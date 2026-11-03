import os
from typing import Tuple
from core.schemas import IntentResult, IntentType
from core.enums import OperationMode
from services.ai_rag import get_vector_store, format_docs
from services.smart_route import find_multiple_routes
from services.maps import gmaps_service
from logger import get_logger

logger = get_logger(__name__)

async def fetch_knowledge(intent: IntentResult, mode: OperationMode) -> Tuple[str, str]:
    """
    Fetch knowledge based on the intent and mode.
    Returns: (rag_context, route_context)
    """
    rag_context = ""
    route_context = ""
    
    # 1. RAG Docs for INFO and ROUTE
    if intent.type in [IntentType.INFO, IntentType.ROUTE]:
        try:
            vectordb = get_vector_store()
            query = intent.rewritten_query
            
            logger.info(f"RAG searching for: '{query}'")
            
            # Simple RAG search
            # We skip multiple calls and just do one robust search using rewritten query
            docs = await vectordb.asimilarity_search(query, k=6)
            
            # Prioritize bus/route data
            docs.sort(key=lambda d: 0 if any(k in d.metadata.get("source", "").lower() for k in ["buyt", "bus", "lich_trinh", "danh_sach"]) else 1)
            
            # Deduplicate
            unique_docs = []
            seen_contents = set()
            for d in docs:
                snippet = d.page_content[:150]
                if snippet not in seen_contents:
                    seen_contents.add(snippet)
                    unique_docs.append(d)
                    if len(unique_docs) >= 6:
                        break
                        
            if unique_docs:
                rag_context = "<rag_docs>\n" + format_docs(unique_docs) + "\n</rag_docs>\n"
        except Exception as e:
            logger.error(f"[Knowledge Router] RAG Error: {e}")

    # 2. Map Routes for ROUTE intent
    if intent.type == IntentType.ROUTE and intent.destination:
        try:
            orig = intent.origin if intent.origin else "Vị trí hiện tại"
            
            # Call Smart Route (Local Graph)
            multi_options = find_multiple_routes(orig, intent.destination, city="HN")
            if multi_options:
                route_details = []
                for opt in multi_options:
                    t_mins = opt.get('total_time', opt.get('total_time_mins', 0))
                    cost_val = opt.get('total_cost', opt.get('total_cost_vnd', 0))
                    detail = f"### Phương án ({opt['option_name']}):\n"
                    detail += f"- Tổng thời gian: ~{t_mins} phút | Chi phí: {cost_val:,}đ | Chuyển tuyến: {opt.get('transfers', 0)} lần\n"
                    steps = opt.get("steps", [])
                    if steps:
                        detail += "- Các bước chi tiết:\n"
                        for idx, step in enumerate(steps, 1):
                            m_type = step.get("type", step.get("mode", "bus"))
                            emoji = "🚌" if m_type == "bus" else ("🚇" if m_type == "metro" else ("🚲" if m_type == "bike" else "🚶"))
                            line_name = step.get("line", "Tuyến")
                            from_st = step.get("from", "Điểm đi")
                            to_st = step.get("to", "Điểm đến")
                            dur = step.get("duration", 0)
                            c_str = f"{step.get('cost', 0):,}đ" if step.get('cost', 0) > 0 else "Miễn phí"
                            detail += f"  {idx}. {emoji} [{line_name}] Từ **{from_st}** đến **{to_st}** (~{dur} phút | {c_str})\n"
                    route_details.append(detail)
                route_context += f"\n<smart_routes>\n" + "\n".join(route_details) + "\n</smart_routes>\n"

            # If online, optionally fetch Google Maps Directions
            if mode != OperationMode.OFFLINE:
                gmaps_info = gmaps_service.get_directions(orig, intent.destination)
                if gmaps_info:
                    route_context += f"\n<maps_data>\n{gmaps_info}\n</maps_data>\n"

        except Exception as e:
            logger.error(f"[Knowledge Router] Map Route Error: {e}")

    return rag_context, route_context
