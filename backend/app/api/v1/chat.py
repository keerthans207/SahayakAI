"""Chat endpoints — sessions and messages."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1._deps import get_current_user_id, get_db
from app.schemas.chat import (
    ChatMessageRead,
    ChatSessionCreate,
    ChatSessionRead,
    ChatTurnCreate,
    ChatTurnResponse,
)
from app.services.chat_service import ChatService
from app.utils.content_normalizer import normalize_content
from app.services.chat_service import ChatService

router = APIRouter()


@router.post("/sessions", response_model=ChatSessionRead, status_code=201)
async def create_session(
    body: ChatSessionCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    svc = ChatService(db)
    conv = await svc.create_session(user_id, title=body.title, language=body.preferred_language)
    await db.commit()
    return ChatSessionRead(
        id=conv.id, title=conv.title, language=conv.language,
        created_at=conv.created_at, updated_at=conv.updated_at,
    )


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    svc = ChatService(db)
    conv = await svc.get_session(user_id, session_id)
    if conv is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    messages = await svc.list_messages(user_id, session_id)
    return {
        "session": ChatSessionRead(
            id=conv.id, title=conv.title, language=conv.language,
            created_at=conv.created_at, updated_at=conv.updated_at,
        ),
        "messages": [
            ChatMessageRead(
                id=m.id, role=m.role, content=m.content, language=m.language,
                created_at=m.created_at,
            )
            for m in messages
        ],
    }


@router.post("/sessions/{session_id}/messages", response_model=ChatTurnResponse)
async def send_message(
    session_id: str,
    body: ChatTurnCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    svc = ChatService(db)
    try:
        result = await svc.send_message(user_id, session_id, body.content, language=body.language)
    except KeyError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    return ChatTurnResponse(**result)


@router.post("/sessions/{session_id}/stream")
async def stream_message(
    session_id: str,
    body: ChatTurnCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Stream a response with true token-by-token generation from the LLM."""
    from fastapi.responses import StreamingResponse
    import json

    svc = ChatService(db)

    async def event_gen():
        try:
            async for event in svc.stream_message(user_id, session_id, body.content, language=body.language):
                event_type = event.get("type")
                
                if event_type == "token":
                    # Send raw token content (preserves spaces, newlines, markdown)
                    yield f"data: {json.dumps(event)}\n\n"
                
                elif event_type == "timing":
                    yield f"data: {json.dumps(event)}\n\n"
                
                elif event_type == "metadata":
                    yield f"data: {json.dumps(event)}\n\n"
                
                elif event_type == "done":
                    yield f"data: {json.dumps(event)}\n\n"
                    yield "data: [DONE]\n\n"
                    return
                
                elif event_type == "error":
                    yield f"data: {json.dumps(event)}\n\n"
                    return
                    
        except Exception as e:  # noqa: BLE001
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    svc = ChatService(db)
    ok = await svc.delete_session(user_id, session_id)
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    return None
