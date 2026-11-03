from typing import List, Optional
from core.enums import OperationMode, IntentType, TopicType
from core.schemas import IntentResult, MessageHistory
from llm_factory import get_llm
from core.constants import (
    GTCC_BASE_PROMPT,
    GTCC_INFO_SYSTEM_PROMPT,
    GTCC_ROUTE_SYSTEM_PROMPT,
    GTCC_OFFLINE_SYSTEM_PROMPT,
    QUICK_FALLBACK,
    DEFAULT_FALLBACK
)
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from logger import get_logger

logger = get_logger(__name__)

async def execute_pipeline(
    intent: IntentResult, 
    rag_context: str, 
    route_context: str, 
    messages: List[MessageHistory], 
    mode: OperationMode,
    stream: bool = False
):
    """
    Execute the core logic by deciding whether to use LLM or template engine.
    """
    
    # 1. Hybrid/Online Pipeline (Cloud LLM)
    if mode in [OperationMode.ONLINE, OperationMode.HYBRID]:
        # Build prompt based on intent
        if intent.type == IntentType.ROUTE:
            sys_prompt = GTCC_ROUTE_SYSTEM_PROMPT
        elif intent.type == IntentType.INFO:
            sys_prompt = GTCC_INFO_SYSTEM_PROMPT
        else:
            sys_prompt = GTCC_BASE_PROMPT
            
        context = rag_context + route_context
        if context:
            sys_prompt += f"\n\n<system_context>\n{context}\n</system_context>\n"
            sys_prompt += "<instructions>\n1. Chỉ sử dụng thông tin trong <system_context> nếu liên quan trực tiếp.\n"
            sys_prompt += "2. Không tự bịa đặt thông tin. Trả lời súc tích.\n</instructions>"
            
        return await _invoke_llm(sys_prompt, messages, temperature=0.05 if intent.type == IntentType.ROUTE else 0.2, stream=stream)
        
    # 2. Offline Pipeline
    if mode == OperationMode.OFFLINE:
        # Check if Ollama is available
        from llm_factory import check_health
        health = check_health()
        
        # If Ollama is available, use Local LLM
        if health.get("online"):
            context = rag_context + route_context
            sys_prompt = GTCC_OFFLINE_SYSTEM_PROMPT
            if context:
                sys_prompt += f"\n\nKIẾN THỨC OFFLINE:\n{context}\n"
            return await _invoke_llm(sys_prompt, messages, temperature=0.1, stream=stream)
        
        # If Ollama is NOT available, use Template Engine
        logger.info("Local LLM unavailable. Using Template Engine for Offline Mode.")
        fallback = _template_fallback(intent, rag_context, route_context)
        if stream:
            async def _yield_fallback():
                yield fallback
            return _yield_fallback()
        return fallback

    fallback = DEFAULT_FALLBACK
    if stream:
        async def _yield_default():
            yield fallback
        return _yield_default()
    return fallback

async def _invoke_llm(system_prompt: str, messages: List[MessageHistory], temperature: float, stream: bool = False):
    llm = get_llm(temperature=temperature)
    langchain_messages = [SystemMessage(content=system_prompt)]
    
    # Limit conversation history to sliding window of max 4 recent messages to avoid context bleed
    recent_messages = messages[-4:] if len(messages) > 4 else messages
    for msg in recent_messages:
        if msg.role == "user":
            langchain_messages.append(HumanMessage(content=msg.content))
        else:
            langchain_messages.append(AIMessage(content=msg.content))
            
    try:
        if stream:
            async def _stream_generator():
                async for chunk in llm.astream(langchain_messages):
                    content = getattr(chunk, "content", str(chunk))
                    if content:
                        yield content
            return _stream_generator()
        else:
            response = await llm.ainvoke(langchain_messages)
            if hasattr(response, "content"):
                return str(response.content).strip()
            return str(response).strip()
    except Exception as e:
        logger.error(f"[Execution Router] LLM generation error: {e}")
        if stream:
            async def _err_stream():
                yield DEFAULT_FALLBACK
            return _err_stream()
        return DEFAULT_FALLBACK

def _template_fallback(intent: IntentResult, rag_context: str, route_context: str) -> str:
    """Fallback logic when no LLM is available (Ollama down). Uses raw context if available."""
    fallback_msg = "⚠️ **Chế độ Ngoại Tuyến (Không có AI)**\n\n"
    
    has_data = False
    
    if route_context:
        fallback_msg += "📍 **Lộ trình tìm được:**\n"
        # Clean up XML tags from route context
        clean_route = route_context.replace("<smart_routes>", "").replace("</smart_routes>", "").replace("<maps_data>", "").replace("</maps_data>", "").strip()
        fallback_msg += clean_route + "\n\n"
        has_data = True
        
    if rag_context:
        fallback_msg += "📚 **Thông tin tra cứu:**\n"
        # Clean up XML tags from rag context
        clean_rag = rag_context.replace("<rag_docs>", "").replace("</rag_docs>", "").strip()
        # Limit the output length so it's readable
        if len(clean_rag) > 800:
            clean_rag = clean_rag[:800] + "...\n(Dữ liệu quá dài, vui lòng hỏi chi tiết hơn)"
        fallback_msg += clean_rag + "\n\n"
        has_data = True
        
    if has_data:
        return fallback_msg.strip()
        
    # If no dynamic data, fall back to static topic answers
    topic = intent.topic.value
    if topic in QUICK_FALLBACK:
        return fallback_msg + QUICK_FALLBACK[topic]
        
    return fallback_msg + DEFAULT_FALLBACK
