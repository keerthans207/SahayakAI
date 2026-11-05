#!/usr/bin/env python
"""Verify LLM provider connectivity and the full agent pipeline.

Usage:
    # Test the mock provider (no credentials needed):
    LLM_PROVIDER=mock python scripts/test_llm.py

    # Test Azure Foundry:
    LLM_PROVIDER=azure_foundry \\
    FOUNDRY_PROJECT_ENDPOINT=https://... \\
    AZURE_AI_MODEL=gpt-4.1 \\
    python scripts/test_llm.py

    # Test an OpenAI-compatible endpoint:
    LLM_PROVIDER=openai_compatible \\
    OPENAI_BASE_URL=https://... \\
    OPENAI_API_KEY=... \\
    OPENAI_MODEL=llama-3.1 \\
    python scripts/test_llm.py
"""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


async def main() -> None:
    from app.agents.factory import SahayakAgent
    from app.agents.model_factory import get_chat_model
    from app.config import get_settings

    settings = get_settings()
    print(f"Provider: {settings.llm_provider}")
    print(f"Database: {settings.database_url}")

    # 1. Direct model call.
    try:
        model = get_chat_model()
        from langchain_core.messages import HumanMessage

        response = await model.ainvoke([HumanMessage(content="Say 'Hello from Sahayak AI' briefly.")])
        print(f"\nModel response: {response.content[:200]}")
    except Exception as exc:
        print(f"\nModel error: {exc}")
        sys.exit(1)

    # 2. Full agent pipeline.
    agent = SahayakAgent()
    test_cases = [
        ("B.Tech student, 60% disability, Karnataka. Find scholarships.", {"state": "Karnataka", "disability_percentage": 60, "education_level": "undergraduate"}),
        ("I have UDID but no NSP OTR. What next?", {"udid_status": "has_udid", "otr_status": "no_otr"}),
        ("Which assistive device schemes are available?", {}),
    ]
    for msg, profile in test_cases:
        print(f"\n--- Query: {msg[:60]}... ---")
        result = await agent.run(user_message=msg, user_profile=profile)
        print(f"Intent: {result.get('current_intent')}")
        print(f"Scheme: {result.get('selected_scheme')}")
        print(f"Eligibility: {(result.get('eligibility_result') or {}).get('outcome', 'n/a')}")
        print(f"Sources: {len(result.get('official_sources', []))}")
        print(f"Response: {result.get('response', '')[:120]}...")

    print("\n=== All checks passed. ===")


if __name__ == "__main__":
    asyncio.run(main())
