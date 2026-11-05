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
        messages: list = []
        for h in history or []:
            role = h.get("role")
            content = h.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
        messages.append(HumanMessage(content=user_message))

        initial: SahayakState = {
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
        result = await self._graph.ainvoke(initial)
        # Ensure an assistant AIMessage is present in the returned messages.
        result_messages = result.get("messages", [])
        if not any(isinstance(m, AIMessage) for m in result_messages):
            result_messages = result_messages + [AIMessage(content=result.get("response", ""))]
        result["messages"] = result_messages
        return result


_agent: SahayakAgent | None = None


def get_agent() -> SahayakAgent:
    global _agent
    if _agent is None:
        _agent = SahayakAgent()
    return _agent


def reset_agent() -> None:
    global _agent
    _agent = None
