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
    """Stream a response as Server-Sent Events where the model supports it."""
    from fastapi.responses import StreamingResponse

    svc = ChatService(db)
    try:
        result = await svc.send_message(user_id, session_id, body.content, language=body.language)
    except KeyError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")

    content = result["content"]

    async def event_gen():
        # Token-by-token streaming for the final text. With the MOCK provider this
        # yields word chunks; with a streaming model this could use model.astream.
        for token in content.split():
            yield f"data: {token} \n\n"
        yield "data: [DONE]\n\n"

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
