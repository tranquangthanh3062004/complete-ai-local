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
    origin: str
    destination: str
    rewritten_query: str

import re
from services.smart_route import find_multiple_routes

def extract_locations_and_intent_regex(query: str):
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
        
    return requires_map, requires_bike, origin, destination, query

import json

from tenacity import retry, stop_after_attempt, wait_exponential

from services.cache_service import TTLCache
_INTENT_CACHE = TTLCache(maxsize=128, ttl=3600)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def extract_intent_llm(query: str, llm):
    # Dùng cache nếu câu hỏi đã được hỏi trước đó
    cached_intent = _INTENT_CACHE.get(query)
    if cached_intent:
        logger.info(f"Using cached intent for: {query}")
        return cached_intent
        
    # 1. Thử dùng Fast Regex trước (cực nhanh 0ms, chính xác 100% cho câu hỏi vị trí từ A đến B)
    regex_map, regex_bike, reg_orig, reg_dest, reg_query = extract_locations_and_intent_regex(query)
    if regex_map and reg_dest:
        result = (regex_map, regex_bike, reg_orig, reg_dest, f"Làm thế nào để đi bằng phương tiện công cộng từ {reg_orig or 'Vị trí hiện tại'} đến {reg_dest}?")
        _INTENT_CACHE.set(query, result)
        return result
        
    sys_prompt = """Bạn là trợ lý phân tích câu hỏi giao thông công cộng.
Hãy trả về một chuỗi JSON duy nhất, không có markdown, không giải thích thêm:
{
    "requires_map": bool, 
    "requires_bike": bool,
    "origin": "string",
    "destination": "string",
    "rewritten_query": "string"
}
Lưu ý: "rewritten_query" là câu hỏi được viết lại rõ ràng, đầy đủ ngữ cảnh để tìm kiếm tài liệu (RAG).
Nếu người dùng hỏi "giá vé", hãy viết lại thành "Giá vé xe buýt và metro tại Hà Nội là bao nhiêu?".
"""
    try:
        res = await llm.ainvoke([
            SystemMessage(content=sys_prompt),
            HumanMessage(content=query)
        ])
        content = res.content.strip() if hasattr(res, "content") else str(res).strip()
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
            
        data = json.loads(content)
        result = (
            data.get("requires_map", False),
            data.get("requires_bike", False),
            data.get("origin", ""),
            data.get("destination", ""),
            data.get("rewritten_query", query)
        )
        
        # Lưu vào cache để tối ưu các lần hỏi sau
        _INTENT_CACHE.set(query, result)
        return result
    except Exception as e:
        logger.error(f"[Intent LLM Error] {e}. Falling back to Regex.")
        return extract_locations_and_intent_regex(query)

async def analyze_intent(state: AgentState):
    query = state["messages"][-1].content
    # Dùng LLM với temperature=0.0 để dự đoán intent (nhanh, chuẩn)
    intent_llm = get_llm(state.get("model_name"), temperature=0.0)
    requires_map, requires_bike, origin, destination, rewritten_query = await extract_intent_llm(query, intent_llm)
    
    context = ""
    try:
        vectordb = get_vector_store()
        logger.info(f"RAG searching for origin: '{origin}', destination: '{destination}'")
        
        all_docs = []
        if destination:
            docs_dest = await vectordb.asimilarity_search(f"Tuyến xe buýt {destination}", k=4)
            all_docs.extend(docs_dest)
        if origin:
            docs_orig = await vectordb.asimilarity_search(f"Tuyến xe buýt {origin}", k=4)
            all_docs.extend(docs_orig)
            
        docs_main = await vectordb.asimilarity_search(rewritten_query, k=4)
        all_docs.extend(docs_main)
        
        # Ưu tiên các file dữ liệu xe buýt nội bộ trong thư mục data/ (lich_trinh_buyt, danh_sach_tuyen_buyt)
        unique_docs = []
        seen_contents = set()
        
        all_docs.sort(key=lambda d: 0 if any(k in d.metadata.get("source", "").lower() for k in ["buyt", "bus", "lich_trinh", "danh_sach"]) else 1)
        
        for d in all_docs:
            snippet = d.page_content[:100]
            if snippet not in seen_contents:
                seen_contents.add(snippet)
                unique_docs.append(d)
                if len(unique_docs) >= 6:
                    break
                    
        if unique_docs:
            context = "<rag_docs>\n" + format_docs(unique_docs) + "\n</rag_docs>\n"
    except Exception as e:
        logger.error(f"[LangGraph] RAG Error: {e}")
        
    return {
        "requires_map": requires_map, 
        "requires_bike": requires_bike, 
        "context": context,
        "origin": origin,
        "destination": destination,
        "rewritten_query": rewritten_query
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
            context += f"\n<maps_data>\n{route_info}\n</maps_data>\n"
            
            # Thử tìm các tùy chọn nâng cao qua Smart Route Graph
            multi_options = find_multiple_routes(orig, destination, city="HN")
            if multi_options:
                route_details = []
                for opt in multi_options:
                    t_mins = opt.get('total_time', opt.get('total_time_mins', 0))
                    cost_val = opt.get('total_cost', opt.get('total_cost_vnd', 0))
                    detail = f"### Phương án ({opt['option_name']}):\n"
                    detail += f"- Tổng thời gian: ~{t_mins} phút | Chi phí: {cost_val:,}đ | Chuyển tuyến: {opt['transfers']} lần | CO2: {opt['co2_kg']}kg\n"
                    steps = opt.get("steps", [])
                    if steps:
                        detail += "- Các bước di chuyển chi tiết:\n"
                        for idx, step in enumerate(steps, 1):
                            m_type = step.get("type", step.get("mode", "bus"))
                            emoji = "🚌" if m_type == "bus" else ("🚇" if m_type == "metro" else ("🚲" if m_type == "bike" else "🚶"))
                            line_name = step.get("line", "Tuyến xe buýt")
                            from_st = step.get("from", "Điểm đi")
                            to_st = step.get("to", "Điểm đến")
                            dur = step.get("duration", 0)
                            c_str = f"{step.get('cost', 0):,}đ" if step.get('cost', 0) > 0 else "Miễn phí/Vé tháng"
                            detail += f"  {idx}. {emoji} [{line_name}] Từ **{from_st}** đến **{to_st}** (~{dur} phút | {c_str})\n"
                    route_details.append(detail)
                context += f"\n<smart_routes>\n" + "\n".join(route_details) + "\n</smart_routes>\n"
        except Exception as e:
            logger.error(f"[LangGraph] Maps Error: {e}")
            
    if state.get("requires_bike"):
        try:
            bike_info = bike_service.get_pricing_info()
            context += f"\n<bike_data>\n{bike_info}\n</bike_data>\n"
        except Exception as e:
            logger.error(f"[LangGraph] Bike Error: {e}")
            
    return {"context": context}

def clean_xml_tags(text: str) -> str:
    if not text:
        return ""
    import re
    cleaned = re.sub(r"</?(?:system_context|rag_docs|maps_data|smart_routes|bike_data|instructions)>", "", text, flags=re.IGNORECASE)
    return cleaned.strip()

async def generate_response(state: AgentState):
    context = state.get("context", "")
    llm = get_llm(state.get("model_name"), state.get("temperature", 0.1))
    
    # Xây dựng hệ thống prompt
    sys_prompt = GTCC_SYSTEM_PROMPT
    if context:
        sys_prompt += f"""\n\n<system_context>\n{context}\n</system_context>
<instructions>
1. Chỉ sử dụng thông tin trong <system_context> nếu liên quan trực tiếp đến câu hỏi.
2. Tuyệt đối không tự bịa đặt thông tin (no hallucination). Nếu thiếu dữ liệu, hãy yêu cầu người dùng làm rõ.
3. Cung cấp câu trả lời súc tích, rõ ràng, không lặp lại các thẻ XML.
</instructions>"""
        
    # Chuẩn bị messages (bao gồm SystemMessage)
    messages = [SystemMessage(content=sys_prompt)] + state["messages"]
    
    # Tạo node để stream với tag
    response = await llm.ainvoke(messages, config={"tags": ["generate_node"]})
    if hasattr(response, "content") and isinstance(response.content, str):
        response.content = clean_xml_tags(response.content)
    elif isinstance(response, str):
        response = AIMessage(content=clean_xml_tags(response))
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
