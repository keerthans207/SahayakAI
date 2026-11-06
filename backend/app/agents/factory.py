"""Agent factory — wraps the LangGraph workflow for the chat layer.

``SahayakAgent.run`` builds the initial state, executes the graph, and returns
the resolved state (intent, selected scheme, eligibility, sources, response).
It keeps the LLM provider behind the model factory so it works with the MOCK
model offline.
"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage

from app.agents.graph import get_graph
from app.agents.state import SahayakState


class SahayakAgent:
    def __init__(self) -> None:
        self._graph = get_graph()

    def _build_initial_state(
        self,
        *,
        user_message: str,
        user_id: str,
        session_id: str,
        preferred_language: str | None,
        user_profile: dict[str, Any] | None,
        history: list[dict[str, Any]] | None,
    ) -> SahayakState:
        """Build initial state from request parameters."""
        messages: list = []
        for h in history or []:
            role = h.get("role")
            content = h.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
        messages.append(HumanMessage(content=user_message))

        return {
            "messages": messages,
            "user_id": user_id,
            "session_id": session_id,
            "preferred_language": preferred_language,
            "user_profile": user_profile or {},
            "retrieved_documents": [],
            "official_sources": [],
            "missing_requirements": [],
            "tool_calls": [],
            "validation_flags": [],
        }

    async def run(
        self,
        *,
        user_message: str,
        user_id: str = "dev-user",
        session_id: str = "",
        preferred_language: str | None = None,
        user_profile: dict[str, Any] | None = None,
        history: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Execute the full graph and return the final state (non-streaming)."""
        initial = self._build_initial_state(
            user_message=user_message,
            user_id=user_id,
            session_id=session_id,
            preferred_language=preferred_language,
            user_profile=user_profile,
            history=history,
        )
        result = await self._graph.ainvoke(initial)
        # Ensure an assistant AIMessage is present in the returned messages.
        result_messages = result.get("messages", [])
        if not any(isinstance(m, AIMessage) for m in result_messages):
            result_messages = result_messages + [AIMessage(content=result.get("response", ""))]
        result["messages"] = result_messages
        return result

    async def stream(
        self,
        *,
        user_message: str,
        user_id: str = "dev-user",
        session_id: str = "",
        preferred_language: str | None = None,
        user_profile: dict[str, Any] | None = None,
        history: list[dict[str, Any]] | None = None,
    ):
        """Stream graph execution with real-time token generation.

        Yields events:
        - {"type": "retrieval_complete"} when scheme/document retrieval finishes
        - {"type": "token", "content": str} for each LLM token
        - {"type": "final_state", "state": dict} with the complete final state
        """
        initial = self._build_initial_state(
            user_message=user_message,
            user_id=user_id,
            session_id=session_id,
            preferred_language=preferred_language,
            user_profile=user_profile,
            history=history,
        )

        # Track state through pipeline
        current_state = initial
        retrieval_complete = False

        from app.utils.content_normalizer import normalize_content

        async for event in self._graph.astream_events(initial, version="v2"):
            event_type = event.get("event")
            name = event.get("name", "")

            # Track state updates from nodes
            if event_type == "on_chain_end" and event.get("data", {}).get("output"):
                output = event["data"]["output"]
                if isinstance(output, dict):
                    current_state = {**current_state, **output}

            # Signal when retrieval completes (before LLM generation)
            if event_type == "on_chain_end" and name in (
                "retrieve_evidence", "discover", "evaluate", "documents",
                "application", "udid_otr", "general"
            ):
                if not retrieval_complete:
                    retrieval_complete = True
                    yield {"type": "retrieval_complete"}

            # Stream LLM tokens from the generate_response node
            if event_type == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk is not None and hasattr(chunk, "content"):
                    token_text = normalize_content(chunk.content)
                    if token_text:
                        yield {"type": "token", "content": token_text}

        # Emit final complete state
        yield {"type": "final_state", "state": current_state}


_agent: SahayakAgent | None = None


def get_agent() -> SahayakAgent:
    global _agent
    if _agent is None:
        _agent = SahayakAgent()
    return _agent


def reset_agent() -> None:
    global _agent
    _agent = None
