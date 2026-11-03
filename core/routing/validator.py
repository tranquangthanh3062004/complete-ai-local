import re
from typing import List, Tuple
from core.schemas import IntentResult, IntentType
from services.ai_topic import _get_gtcc_suggestions

def format_and_validate(raw_answer: str, intent: IntentResult) -> Tuple[str, List[str]]:
    """
    Format the response, clean up XML tags, and generate suggestions.
    Returns: (cleaned_answer, suggestions)
    """
    # 1. Clean XML tags and markdown blocks
    cleaned = re.sub(r"</?(?:system_context|rag_docs|maps_data|smart_routes|bike_data|instructions)>", "", raw_answer, flags=re.IGNORECASE)
    
    # Sometimes LLM wraps response in ```markdown
    cleaned = re.sub(r"^```(?:markdown|md)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"```$", "", cleaned)
    
    # 2. Cleanup whitespace
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = cleaned.strip()
    
    # 3. Anti-hallucination sanity check
    # Check for known impossible claims e.g., Metro 2A going to Mỹ Đình or Giáp Bát
    c_lower = cleaned.lower()
    if "metro 2a" in c_lower or "metro tuyến 2a" in c_lower:
        if "mỹ đình" in c_lower or "giáp bát" in c_lower or "kim mã" in c_lower:
            # Fix hallucinated Metro 2A station claims
            cleaned = re.sub(r"(?:tiếp tục đi|bắt|đi)\s+metro\s+(?:tuyến\s+)?2a\s+từ\s+[^.\n]+?(?:mỹ đình|giáp bát|kim mã)[^.\n]*", "đón xe buýt liên tuyến để di chuyển", cleaned, flags=re.IGNORECASE)

    # Check for false walking claims between distant districts (e.g. Hà Đông to Hoàng Mai/Sân Bay)
    if "đi bộ" in c_lower and ("hà đông" in c_lower or "ha dong" in c_lower):
        if "hoàng mai" in c_lower or "hoan mai" in c_lower or "sân bay" in c_lower or "noi bai" in c_lower:
            cleaned = re.sub(r"chỉ cần đi bộ[^.\n]*", "nên đón xe buýt tuyến 21A hoặc xe buýt liên tuyến để di chuyển", cleaned, flags=re.IGNORECASE)

    # If the answer is suspiciously short but isn't a greeting
    if len(cleaned) < 10 and intent.type != IntentType.GREETING:
        cleaned += "\n\nXin lỗi, tôi chưa hiểu rõ ý của bạn. Bạn có thể hỏi chi tiết hơn về tuyến xe buýt hoặc lộ trình được không?"

    # 4. Generate Suggestions
    suggestions = _get_gtcc_suggestions(intent.topic.value)
    
    return cleaned, suggestions
