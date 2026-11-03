import re
import json
from typing import Tuple, Optional
from core.enums import IntentType, TopicType
from core.schemas import IntentResult
from services.ai_topic import detect_topic, TOPIC_DISPLAY
from services.sanitizer import sanitize_query
from core.exceptions import InvalidQueryError
from logger import get_logger

logger = get_logger(__name__)

# Basic greeting keywords
GREETING_KEYWORDS = ["chào", "hello", "hi", "xin chào", "hey", "chào bạn", "chào bot"]

def _detect_greeting(query_lower: str) -> bool:
    """Check if query is just a simple greeting"""
    words = query_lower.strip().split()
    if len(words) <= 4 and any(gw == query_lower.strip() for gw in GREETING_KEYWORDS):
        return True
    return False

import unicodedata

def _extract_route_regex(query_lower: str) -> Tuple[bool, Optional[str], Optional[str], str]:
    """
    Extract origin and destination using fast regex/string operations.
    Returns: (is_route, origin, destination, rewritten_query)
    """
    # Normalize Unicode NFC to prevent accent split mismatch (e.g., u\u0300 vs \u00f9)
    query_lower = unicodedata.normalize('NFC', query_lower)
    
    map_keywords = [
        "từ", "đến", "tới", "sang", "đi", "đường", "quãng đường", 
        "khoảng cách", "chỉ đường", "bản đồ", "lộ trình", "về"
    ]
    
    # Check if this might be a route query
    if not any(kw in query_lower for kw in map_keywords):
        return False, None, None, query_lower
        
    clean_q = re.sub(r"^(tôi\s+muốn\s+|muốn\s+|hãy\s+|cho\s+tôi\s+|tra\s+cứu\s+cho\s+tôi|cho\s+tôi\s+hỏi|cho\s+tôi\s+biết|quãng\s+đường|lộ\s+trình|chỉ\s+đường|bản\s+đồ)\s+", "", query_lower, flags=re.IGNORECASE).strip()
    clean_q = re.sub(r"^(tra cứu|cho tôi|biết|hỏi|tìm|xem|khoảng cách|quãng đường|đường đi|lộ trình)\s+", "", clean_q, flags=re.IGNORECASE).strip()
    
    origin = ""
    destination = ""
    
    split_words = [" đến ", " tới ", " sang ", " về "]
    split_found = None
    for sw in split_words:
        if sw in clean_q:
            split_found = sw
            break
            
    if split_found:
        parts = clean_q.split(split_found, 1)
        orig_part = parts[0].strip()
        dest_part = parts[1].replace("?", "").strip()
        
        # Clean prefix noise words like "đi từ", "từ", "đi tư", "tư", "đi"
        orig_clean = re.sub(r"^(tôi\s+muốn\s+đi\s+từ|muốn\s+đi\s+từ|đi\s+từ|đi\s+tư|quãng\s+đường\s+từ|đường\s+từ|từ|tư|đi)\s+", "", orig_part, flags=re.IGNORECASE).strip()
        dest_clean = re.sub(r"^(đến|tới|sang|về)\s+", "", dest_part, flags=re.IGNORECASE).strip()
        
        origin = orig_clean if orig_clean else "Vị trí hiện tại"
        destination = dest_clean
    elif "đến " in clean_q or "tới " in clean_q or "về " in clean_q:
        dest_part = re.sub(r"^.*?(đến|tới|về)\s+", "", clean_q, flags=re.IGNORECASE).replace("?", "").strip()
        origin = "Vị trí hiện tại"
        destination = dest_part
        
    if origin and destination:
        rewritten = f"Làm thế nào để đi bằng phương tiện công cộng từ {origin} đến {destination}?"
        return True, origin, destination, rewritten
        
    return False, None, None, query_lower

async def analyze_intent(raw_query: str, llm=None) -> IntentResult:
    """
    Analyze user intent through pipeline: Sanitize -> Regex -> LLM Fallback (optional)
    """
    # 1. Sanitize
    clean_query, is_safe, reason = sanitize_query(raw_query)
    if not is_safe:
        raise InvalidQueryError(reason)
        
    query_lower = clean_query.lower()
    
    # 2. Topic Detection
    topic_str = detect_topic(clean_query)
    try:
        topic = TopicType(topic_str)
    except ValueError:
        topic = TopicType.GTCC_CHUNG

    # 3. Fast Intent Detection (Regex)
    # 3a. Greeting
    if _detect_greeting(query_lower):
        return IntentResult(
            type=IntentType.GREETING,
            topic=topic,
            rewritten_query=clean_query,
            confidence=1.0
        )
        
    # 3b. Route Detection
    is_route, origin, destination, rewritten = _extract_route_regex(query_lower)
    if is_route and destination:
        return IntentResult(
            type=IntentType.ROUTE,
            topic=topic,
            origin=origin,
            destination=destination,
            rewritten_query=rewritten,
            confidence=0.9
        )
        
    # 3c. Info Keywords Detection
    info_keywords = ["giá vé", "lịch trình", "tuyến", "phạt", "đăng ký", "vé tháng", "giờ"]
    if any(kw in query_lower for kw in info_keywords) or topic != TopicType.GTCC_CHUNG:
        # If it contains specific info keywords or topic is recognized clearly
        return IntentResult(
            type=IntentType.INFO,
            topic=topic,
            rewritten_query=clean_query,
            confidence=0.8
        )
        
    # 4. LLM Intent Fallback (if LLM is provided and query is ambiguous)
    if llm:
        try:
            logger.info("Falling back to LLM for intent detection")
            sys_prompt = "Bạn là trợ lý phân tích câu hỏi giao thông công cộng. Hãy trả về JSON: {\"is_route\": bool, \"is_info\": bool, \"origin\": \"\", \"destination\": \"\", \"rewritten_query\": \"\"}."
            # Simulating LLM call here, actual implementation would invoke LLM.
            # For simplicity, returning AMBIGUOUS if we get here.
        except Exception as e:
            logger.error(f"[Intent Analyzer] LLM intent error: {e}")
            
    # Default to ambiguous
    return IntentResult(
        type=IntentType.AMBIGUOUS,
        topic=topic,
        rewritten_query=clean_query,
        confidence=0.5
    )
