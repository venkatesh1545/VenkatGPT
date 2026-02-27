"""
app/api/chat.py
────────────────
Main chat endpoint with full security pipeline + streaming.

POST /api/v1/chat        → streaming SSE response
POST /api/v1/chat/sync   → non-streaming JSON response (for testing)
"""

import json
import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from app.models.chat import ChatRequest, ChatResponse
from app.core.rag_engine import RAGEngine
from app.core.claude_client import stream_claude, complete_claude
from app.core.persona_guard import PersonaGuard
from app.security.sanitizer import InputSanitizer
from app.security.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)
router = APIRouter()

# Singletons
_guard = PersonaGuard()
_sanitizer = InputSanitizer()
_limiter = RateLimiter()


async def _run_pipeline(request: Request, body: ChatRequest):
    """
    Shared pipeline logic:
    1. Rate limit
    2. Sanitize input
    3. Off-topic check
    4. RAG retrieval
    5. Build system prompt
    Returns (system_prompt, clean_query, context_chunks) or raises/returns early message.
    """
    # 1. Rate limit
    client_ip = request.client.host if request.client else "unknown"
    await _limiter.check(client_ip)

    # 2. Sanitize
    clean_query, error = _sanitizer.sanitize(body.query)
    if error:
        return None, None, None, error

    # 3. Off-topic check
    if _guard.is_off_topic(clean_query):
        return None, None, None, _guard.get_redirect_message(clean_query)

    # 4. RAG retrieval
    rag: RAGEngine = request.app.state.rag_engine
    context_chunks = await rag.retrieve(clean_query, mode=body.mode.value)

    # 5. System prompt
    system_prompt = _guard.build_system_prompt(body.mode.value)

    return system_prompt, clean_query, context_chunks, None


@router.post("/chat")
async def chat_stream(request: Request, body: ChatRequest):
    """
    Streaming chat endpoint.
    Returns Server-Sent Events (SSE).

    Client reads events like:
        data: {"type": "token", "data": "Hello"}
        data: {"type": "done", "data": ""}
    """
    system_prompt, clean_query, context_chunks, early_msg = await _run_pipeline(request, body)

    if early_msg:
        # Return early message as a single SSE stream
        async def early_stream():
            yield f"data: {json.dumps({'type': 'token', 'data': early_msg})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'data': ''})}\n\n"
        return StreamingResponse(early_stream(), media_type="text/event-stream")

    async def token_generator():
        try:
            async for token in stream_claude(system_prompt, clean_query, context_chunks):
                payload = json.dumps({"type": "token", "data": token})
                yield f"data: {payload}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'data': ''})}\n\n"
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'data': 'Stream interrupted. Please retry.'})}\n\n"

    return StreamingResponse(
        token_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.post("/chat/sync", response_model=ChatResponse)
async def chat_sync(request: Request, body: ChatRequest):
    """
    Non-streaming chat endpoint.
    Useful for testing, integrations that don't support SSE.
    """
    system_prompt, clean_query, context_chunks, early_msg = await _run_pipeline(request, body)

    if early_msg:
        return ChatResponse(response=early_msg, mode=body.mode.value)

    response_text = await complete_claude(system_prompt, clean_query, context_chunks)
    sources = list({c.split("]")[0].lstrip("[") for c in context_chunks if "]" in c})

    return ChatResponse(
        response=response_text,
        mode=body.mode.value,
        session_id=body.session_id,
        context_sources=sources[:5],
    )
