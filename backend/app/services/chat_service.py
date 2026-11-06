"""Chat session & message persistence with user isolation.

Owns the lifecycle: ensure user exists, create/fetch sessions, persist user and
assistant messages, run the LangGraph agent, and return the resolved turn state.
All queries are scoped by ``user_id`` so one applicant never sees another's data.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.factory import get_agent
from app.models.db import Conversation, Message, User, UserProfile
from app.services.language_service import detect_language


class ChatService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.agent = get_agent()

    async def _ensure_user(self, user_id: str) -> User:
        result = await self.db.execute(select(User).where(User.external_id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(external_id=user_id, display_name=user_id)
            self.db.add(user)
            await self.db.flush()
            profile = UserProfile(user_id=user.id)
            self.db.add(profile)
            await self.db.flush()
        return user

    async def _profile_dict(self, user_id: str) -> dict[str, Any]:
        user = await self._ensure_user(user_id)
        result = await self.db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
        p = result.scalar_one_or_none()
        if not p:
            return {}
        return {
            "preferred_language": p.preferred_language,
            "state": p.state,
            "district": p.district,
            "education_level": p.education_level,
            "course": p.course,
            "institution_type": p.institution_type,
            "employment_status": p.employment_status,
            "disability_category": p.disability_category,
            "disability_percentage": p.disability_percentage,
            "udid_status": p.udid_status,
            "otr_status": p.otr_status,
            "income_range": p.income_range,
            "income_amount": p.income_amount,
            "has_aadhaar": p.has_aadhaar,
        }

    async def create_session(self, user_id: str, title: str | None = None, language: str | None = None) -> Conversation:
        user = await self._ensure_user(user_id)
        conv = Conversation(user_id=user.id, title=title or "New conversation", language=language)
        self.db.add(conv)
        await self.db.flush()
        return conv

    async def get_session(self, user_id: str, session_id: str) -> Conversation | None:
        user = await self._ensure_user(user_id)
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == session_id, Conversation.user_id == user.id)
        )
        return result.scalar_one_or_none()

    async def list_messages(self, user_id: str, session_id: str) -> list[Message]:
        conv = await self.get_session(user_id, session_id)
        if conv is None:
            return []
        result = await self.db.execute(
            select(Message).where(Message.conversation_id == session_id).order_by(Message.created_at)
        )
        return list(result.scalars().all())

    async def send_message(self, user_id: str, session_id: str, content: str, language: str | None = None) -> dict[str, Any]:
        """Send a message and return the complete assistant response (non-streaming).

        For streaming responses, use stream_message instead.
        """
        conv = await self.get_session(user_id, session_id)
        if conv is None:
            raise KeyError("session not found")

        t_start = time.time()

        # Persist the user's message.
        detected = detect_language(content, conv.language)
        user_msg = Message(
            conversation_id=session_id,
            role="user",
            content=content,
            language=language or detected.language,
        )
        self.db.add(user_msg)
        await self.db.flush()

        # Load history (last 10 turns) for context.
        history = [
            {"role": m.role, "content": m.content}
            for m in await self.list_messages(user_id, session_id)
            if m.role in ("user", "assistant")
        ][:-1]  # exclude the message we just added (it's passed explicitly)
        profile = await self._profile_dict(user_id)

        t_profile_loaded = time.time()

        result = await self.agent.run(
            user_message=content,
            user_id=user_id,
            session_id=session_id,
            preferred_language=conv.language,
            user_profile=profile,
            history=history,
        )

        t_agent_complete = time.time()

        assistant_content = result.get("response", "")
        assistant_msg = Message(
            conversation_id=session_id,
            role="assistant",
            content=assistant_content,
            language=result.get("response_language") or conv.language,
            metadata_={
                "intent": result.get("current_intent"),
                "selected_scheme": result.get("selected_scheme"),
                "eligibility_outcome": (result.get("eligibility_result") or {}).get("outcome"),
                "tool_calls": result.get("tool_calls", []),
                "validation_flags": result.get("validation_flags", []),
                "timing": {
                    "profile_load_ms": int((t_profile_loaded - t_start) * 1000),
                    "agent_ms": int((t_agent_complete - t_profile_loaded) * 1000),
                    "total_ms": int((time.time() - t_start) * 1000),
                },
            },
        )
        self.db.add(assistant_msg)
        await self.db.flush()
        await self.db.commit()

        t_persisted = time.time()

        return {
            "message_id": assistant_msg.id,
            "role": "assistant",
            "content": assistant_content,
            "language": assistant_msg.language,
            "detected_language": detected.language,
            "intent": result.get("current_intent"),
            "selected_scheme": result.get("selected_scheme"),
            "eligibility_outcome": (result.get("eligibility_result") or {}).get("outcome"),
            "missing_requirements": result.get("missing_requirements", []),
            "official_sources": result.get("official_sources", []),
            "timing": {
                "profile_load_ms": int((t_profile_loaded - t_start) * 1000),
                "agent_ms": int((t_agent_complete - t_profile_loaded) * 1000),
                "persistence_ms": int((t_persisted - t_agent_complete) * 1000),
                "total_ms": int((t_persisted - t_start) * 1000),
            },
        }

    async def stream_message(
        self, user_id: str, session_id: str, content: str, language: str | None = None
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream a response with true token-by-token generation from the LLM.

        Yields SSE-compatible events:
        - {"type": "timing", "stage": str, "elapsed_ms": int}
        - {"type": "token", "content": str}
        - {"type": "metadata", "data": {...}}
        - {"type": "done", "message_id": str}
        - {"type": "error", "error": str}

        The assistant message is persisted exactly once after streaming completes.
        """
        conv = await self.get_session(user_id, session_id)
        if conv is None:
            yield {"type": "error", "error": "session not found"}
            return

        t_start = time.time()

        try:
            # Persist the user's message
            detected = detect_language(content, conv.language)
            user_msg = Message(
                conversation_id=session_id,
                role="user",
                content=content,
                language=language or detected.language,
            )
            self.db.add(user_msg)
            await self.db.flush()

            # Load history
            history = [
                {"role": m.role, "content": m.content}
                for m in await self.list_messages(user_id, session_id)
                if m.role in ("user", "assistant")
            ][:-1]
            profile = await self._profile_dict(user_id)

            t_profile_loaded = time.time()
            yield {
                "type": "timing",
                "stage": "profile_loaded",
                "elapsed_ms": int((t_profile_loaded - t_start) * 1000),
            }

            # Stream from agent
            accumulated_content = ""
            final_result = None
            t_first_token = None
            t_retrieval_complete = None

            async for event in self.agent.stream(
                user_message=content,
                user_id=user_id,
                session_id=session_id,
                preferred_language=conv.language,
                user_profile=profile,
                history=history,
            ):
                event_type = event.get("type")

                if event_type == "retrieval_complete":
                    t_retrieval_complete = time.time()
                    yield {
                        "type": "timing",
                        "stage": "retrieval_complete",
                        "elapsed_ms": int((t_retrieval_complete - t_start) * 1000),
                    }

                elif event_type == "token":
                    if t_first_token is None:
                        t_first_token = time.time()
                        yield {
                            "type": "timing",
                            "stage": "first_token",
                            "elapsed_ms": int((t_first_token - t_start) * 1000),
                        }
                    token = event.get("content", "")
                    accumulated_content += token
                    yield {"type": "token", "content": token}

                elif event_type == "final_state":
                    final_result = event.get("state")

            t_generation_complete = time.time()
            yield {
                "type": "timing",
                "stage": "generation_complete",
                "elapsed_ms": int((t_generation_complete - t_start) * 1000),
            }

            # Persist assistant message exactly once
            if final_result:
                assistant_msg = Message(
                    conversation_id=session_id,
                    role="assistant",
                    content=accumulated_content,
                    language=final_result.get("response_language") or conv.language,
                    metadata_={
                        "intent": final_result.get("current_intent"),
                        "selected_scheme": final_result.get("selected_scheme"),
                        "eligibility_outcome": (final_result.get("eligibility_result") or {}).get("outcome"),
                        "tool_calls": final_result.get("tool_calls", []),
                        "validation_flags": final_result.get("validation_flags", []),
                        "timing": {
                            "profile_load_ms": int((t_profile_loaded - t_start) * 1000) if t_profile_loaded else 0,
                            "retrieval_ms": int((t_retrieval_complete - t_profile_loaded) * 1000) if t_retrieval_complete and t_profile_loaded else 0,
                            "time_to_first_token_ms": int((t_first_token - t_start) * 1000) if t_first_token else 0,
                            "generation_ms": int((t_generation_complete - (t_first_token or t_start)) * 1000),
                            "total_ms": int((t_generation_complete - t_start) * 1000),
                        },
                    },
                )
                self.db.add(assistant_msg)
                await self.db.flush()
                await self.db.commit()

                t_persisted = time.time()

                # Send metadata
                yield {
                    "type": "metadata",
                    "data": {
                        "intent": final_result.get("current_intent"),
                        "selected_scheme": final_result.get("selected_scheme"),
                        "eligibility_outcome": (final_result.get("eligibility_result") or {}).get("outcome"),
                        "missing_requirements": final_result.get("missing_requirements", []),
                        "official_sources": final_result.get("official_sources", []),
                    },
                }

                yield {
                    "type": "timing",
                    "stage": "persistence_complete",
                    "elapsed_ms": int((t_persisted - t_start) * 1000),
                }

                yield {"type": "done", "message_id": str(assistant_msg.id)}

        except Exception as e:  # noqa: BLE001
            yield {"type": "error", "error": str(e)}

    async def delete_session(self, user_id: str, session_id: str) -> bool:
        conv = await self.get_session(user_id, session_id)
        if conv is None:
            return False
        await self.db.delete(conv)
        await self.db.commit()
        return True
