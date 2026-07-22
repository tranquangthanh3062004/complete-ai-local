from typing import Annotated, TypedDict, List
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from llm_factory import get_llm, GTCC_SYSTEM_PROMPT
from services.google_maps import gmaps_service
from services.bike_service import bike_service
from services.ai_rag import get_vector_store, format_docs
from logger import get_logger
logger = get_logger(__name__)

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], "The messages in the conversation"]
    context: str
    requires_map: bool
    requires_bike: bool
    model_name: str
    temperature: float

import re
from services.smart_route import find_multiple_routes

def extract_locations_and_intent(query: str):
    query_lower = query.lower()
    
    map_keywords = [
        "từ", "đến", "tới", "sang", "đi", "đường", "quãng đường", 
        "khoảng cách", "chỉ đường", "bản đồ", "lộ trình", "vé", "tuyến"
    ]
    
    requires_map = any(kw in query_lower for kw in map_keywords)
    requires_bike = any(kw in query_lower for kw in ["xe đạp", "tngo", "trí nam", "thuê xe", "xe máy điện"])
    
    clean_q = re.sub(r"^(tra cứu cho tôi|cho tôi hỏi|cho tôi biết|quãng đường|lộ trình|chỉ đường|bản đồ)\s+", "", query_lower).strip()
    clean_q = re.sub(r"^(tra cứu|cho tôi|biết|hỏi|tìm|xem|khoảng cách|quãng đường|đường đi|lộ trình)\s+", "", clean_q).strip()
    
    origin = ""
    destination = ""
    
    split_words = [" đến ", " tới ", " sang "]
    split_found = None
    for sw in split_words:
        if sw in clean_q:
            split_found = sw
            break
            
    if split_found:
        parts = clean_q.split(split_found, 1)
        orig_part = parts[0].strip()
        dest_part = parts[1].replace("?", "").strip()
        
        orig_clean = re.sub(r"^(đi từ|từ|thử|quãng đường từ|quãng đường thử|đường từ|đường thử)\s+", "", orig_part).strip()
        origin = orig_clean if orig_clean else "Vị trí hiện tại"
        destination = dest_part
    elif "đến " in clean_q or "tới " in clean_q:
        dest_part = re.sub(r"^.*?(đến|tới)\s+", "", clean_q).replace("?", "").strip()
        origin = "Vị trí hiện tại"
        destination = dest_part
        
    return requires_map, requires_bike, origin, destination

async def analyze_intent(state: AgentState):
    query = state["messages"][-1].content
    requires_map, requires_bike, origin, destination = extract_locations_and_intent(query)
    
    context = ""
    try:
        vectordb = get_vector_store()
        docs = await vectordb.asimilarity_search(query, k=4)
        if docs:
            context = "Tài liệu GTCC (Tham khảo):\n" + format_docs(docs) + "\n\n"
    except Exception as e:
        logger.error(f"[LangGraph] RAG Error: {e}")
        
    return {
        "requires_map": requires_map, 
        "requires_bike": requires_bike, 
        "context": context,
        "origin": origin,
        "destination": destination
    }

async def call_tools(state: AgentState):
    query = state["messages"][-1].content
    context = state.get("context", "")
    origin = state.get("origin")
    destination = state.get("destination")
    
    if state.get("requires_map") and destination:
        try:
            orig = origin if origin else "Vị trí hiện tại"
            route_info = gmaps_service.get_directions(orig, destination)
            context += f"\n[Dữ liệu Định tuyến Đường thực tế (Google Maps / OpenStreetMap)]\n{route_info}\n"
            
            # Thử tìm các tùy chọn nâng cao qua Smart Route Graph
            multi_options = find_multiple_routes(orig, destination, city="HN")
            if multi_options:
                opts_str = "\n".join([
                    f"- **Tùy chọn ({opt['option_name']}):** Thời gian ~{opt['total_time_mins']} phút | Chi phí: {opt['total_cost_vnd']:,}đ | Chuyển tuyến: {opt['transfers']} | CO2: {opt['co2_kg']}kg"
                    for opt in multi_options
                ])
                context += f"\n[Các Phương Án So Sánh Đa Tiêu Chí (Đồ Thị Giao Thông)]:\n{opts_str}\n"
        except Exception as e:
            logger.error(f"[LangGraph] Maps Error: {e}")
            
    if state.get("requires_bike"):
        try:
            bike_info = bike_service.get_pricing_info()
            context += f"\n[Dữ liệu Xe Đạp Công Cộng TNGO]\n{bike_info}\n"
        except Exception as e:
            logger.error(f"[LangGraph] Bike Error: {e}")
            
    return {"context": context}

async def generate_response(state: AgentState):
    context = state.get("context", "")
    llm = get_llm(state.get("model_name"), state.get("temperature", 0.1))
    
    # Xây dựng hệ thống prompt
    sys_prompt = GTCC_SYSTEM_PROMPT
    if context:
        sys_prompt += f"\n\nNGỮ CẢNH HỆ THỐNG CUNG CẤP THÊM:\n{context}\n(LƯU Ý: Chỉ trích xuất và sử dụng phần thông tin nào trong ngữ cảnh thực sự cần thiết để trả lời ĐÚNG TRỌNG TÂM câu hỏi của người dùng. Tuyệt đối bỏ qua các thông tin không liên quan)."
        
    # Chuẩn bị messages (bao gồm SystemMessage)
    messages = [SystemMessage(content=sys_prompt)] + state["messages"]
    
    # Tạo node để stream
    response = await llm.ainvoke(messages)
    return {"messages": [response]}

workflow = StateGraph(AgentState)

workflow.add_node("analyze", analyze_intent)
workflow.add_node("tools", call_tools)
workflow.add_node("generate", generate_response)

workflow.add_edge(START, "analyze")
workflow.add_edge("analyze", "tools")
workflow.add_edge("tools", "generate")
workflow.add_edge("generate", END)

graph_app = workflow.compile()
