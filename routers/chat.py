from fastapi import APIRouter, HTTPException, BackgroundTasks, Header
from fastapi.responses import StreamingResponse
from typing import Optional
import time
import asyncio

from core.schemas import ChatRequest, ChatResponse, MessageHistory
from core.enums import OperationMode, IntentType
from core.routing.intent import analyze_intent
from core.routing.mode import select_operation_mode
from core.routing.knowledge import fetch_knowledge
from core.routing.execution import execute_pipeline
from core.routing.validator import format_and_validate
from core.constants import DEFAULT_FALLBACK
from services.cache_service import TTLCache
from config import settings
from logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["Chat API (Unified)"],
    responses={404: {"description": "Not found"}},
)

_answer_cache = TTLCache(maxsize=256, ttl=3600)

@router.post("/direct", response_model=ChatResponse)
async def chat_direct(
    request: ChatRequest,
    x_network_mode: Optional[str] = Header(None, alias="X-Network-Mode"),
):
    start_time = time.time()
    query = request.query.strip()
    
    try:
        # 1. Mode Selector
        header_mode = None
        if x_network_mode:
            try:
                header_mode = OperationMode(x_network_mode.lower())
            except ValueError:
                pass
                
        active_mode = await select_operation_mode(mode_override=request.mode_override or header_mode)
        logger.info(f"Active Mode: {active_mode.value}")

        # 2. Intent Analyzer
        intent = await analyze_intent(query)
        logger.info(f"Intent detected: {intent.type.value} | Topic: {intent.topic.value}")

        # Check cache only for INFO or GREETING (skip ROUTE intent caching for fresh real-time route generation)
        cache_key = f"{active_mode.value}:{query.lower()}"
        if intent.type != IntentType.ROUTE:
            cached_resp = _answer_cache.get(cache_key)
            if cached_resp:
                logger.info(f"Cache hit for query: {query}")
                cached_resp.latency_ms = round((time.time() - start_time) * 1000, 2)
                return cached_resp

        # 3. Knowledge Router
        rag_context, route_context = await fetch_knowledge(intent, active_mode)

        # 4. Execution Router
        request.messages.append(MessageHistory(role="user", content=query))
        raw_answer = await execute_pipeline(intent, rag_context, route_context, request.messages, active_mode)

        # 5. Formatter & Validator
        final_answer, suggestions = format_and_validate(raw_answer, intent)

        latency = round((time.time() - start_time) * 1000, 2)
        
        sources = []
        if rag_context: sources.append("local_rag" if active_mode == OperationMode.OFFLINE else "cloud_rag")
        if route_context: sources.append("smart_route")
            
        resp = ChatResponse(
            reply=final_answer,
            mode=active_mode,
            model=settings.llm_model_name,
            intent=intent.type.value,
            latency_ms=latency,
            sources=sources,
            suggestions=suggestions if request.suggest else []
        )
        
        # 6. Set Cache (only for non-ROUTE intents)
        if len(final_answer) > 50 and intent.type != IntentType.ROUTE:
            _answer_cache.set(cache_key, resp)
            
        return resp

    except Exception as e:
        logger.exception(f"Chat execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    x_network_mode: Optional[str] = Header(None, alias="X-Network-Mode"),
):
    start_time = time.time()
    query = request.query.strip()
    cache_key = query.lower()
    
    # 1. Check Cache
    cached_resp = _answer_cache.get(cache_key)
    
    async def event_generator():
        if cached_resp:
            logger.info(f"Stream Cache hit for query: {query}")
            ans = cached_resp.reply
            chunk_size = max(1, len(ans) // 20)
            for i in range(0, len(ans), chunk_size):
                chunk = ans[i:i+chunk_size]
                yield f"data: {chunk.replace(chr(10), chr(10) + 'data: ')}\n\n"
                await asyncio.sleep(0.02)
            return

        try:
            # 1. Mode Selector
            header_mode = None
            if x_network_mode:
                try:
                    header_mode = OperationMode(x_network_mode.lower())
                except ValueError:
                    pass
            active_mode = await select_operation_mode(mode_override=request.mode_override or header_mode)
            
            # 2. Intent Analyzer
            intent = await analyze_intent(query)
            
            # 3. Knowledge Router
            rag_context, route_context = await fetch_knowledge(intent, active_mode)

            # 4. Execution Router
            request.messages.append(MessageHistory(role="user", content=query))
            
            stream_gen = await execute_pipeline(intent, rag_context, route_context, request.messages, active_mode, stream=True)
            
            full_response = ""
            async for chunk in stream_gen:
                if chunk:
                    full_response += chunk
                    yield f"data: {chunk.replace(chr(10), chr(10) + 'data: ')}\n\n"
                    
            # Post-process the full response to cache it
            final_answer, suggestions = format_and_validate(full_response, intent)
            if len(final_answer) > 50:
                resp = ChatResponse(
                    reply=final_answer,
                    mode=active_mode,
                    model=settings.llm_model_name,
                    intent=intent.type.value,
                    latency_ms=round((time.time() - start_time) * 1000, 2),
                    sources=[],
                    suggestions=suggestions if request.suggest else []
                )
                _answer_cache.set(cache_key, resp)
                
        except Exception as e:
            logger.exception(f"Chat stream execution error: {e}")
            fallback = DEFAULT_FALLBACK
            yield f"data: {fallback.replace(chr(10), chr(10) + 'data: ')}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

