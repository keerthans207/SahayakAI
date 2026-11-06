#!/usr/bin/env python3
"""Performance benchmark for streaming vs non-streaming responses.

Measures:
- Time to first token (streaming only)
- Total response time
- Token throughput
- Database persistence time

Usage:
    python benchmark_streaming.py [--count N]
"""

import asyncio
import argparse
import time
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import get_settings
from app.services.chat_service import ChatService
from app.database.session import async_session_maker
from app.models.db import User, UserProfile, Conversation


async def benchmark_non_streaming():
    """Benchmark the original non-streaming approach."""
    print("\n=== NON-STREAMING BENCHMARK ===")
    
    async with async_session_maker() as db:
        svc = ChatService(db)
        
        # Ensure test user exists
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.external_id == "benchmark-user"))
        user = result.scalar_one_or_none()
        if not user:
            user = User(external_id="benchmark-user", display_name="Benchmark User")
            db.add(user)
            await db.flush()
            profile = UserProfile(user_id=user.id, state="Karnataka", disability_percentage=50)
            db.add(profile)
            await db.commit()
        
        # Create test session
        conv = await svc.create_session("benchmark-user", title="Benchmark Non-Streaming")
        await db.commit()
        
        test_queries = [
            "What scholarships are available for PwD students in Karnataka?",
            "Check my eligibility for karnataka_pwd_scholarship",
            "What documents do I need for NSP scholarship?",
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\nQuery {i}: {query[:60]}...")
            
            t_start = time.time()
            result = await svc.send_message("benchmark-user", conv.id, query)
            t_end = time.time()
            
            duration_ms = int((t_end - t_start) * 1000)
            content_len = len(result.get("content", ""))
            timing = result.get("timing", {})
            
            print(f"  Total time: {duration_ms}ms")
            print(f"  Content length: {content_len} chars")
            print(f"  Profile load: {timing.get('profile_load_ms', 0)}ms")
            print(f"  Agent execution: {timing.get('agent_ms', 0)}ms")
            print(f"  Persistence: {timing.get('persistence_ms', 0)}ms")
        
        await db.delete(conv)
        await db.commit()


async def benchmark_streaming():
    """Benchmark the new streaming approach."""
    print("\n=== STREAMING BENCHMARK ===")
    
    async with async_session_maker() as db:
        svc = ChatService(db)
        
        # Ensure test user exists
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.external_id == "benchmark-user"))
        user = result.scalar_one_or_none()
        if not user:
            user = User(external_id="benchmark-user", display_name="Benchmark User")
            db.add(user)
            await db.flush()
            profile = UserProfile(user_id=user.id, state="Karnataka", disability_percentage=50)
            db.add(profile)
            await db.commit()
        
        # Create test session
        conv = await svc.create_session("benchmark-user", title="Benchmark Streaming")
        await db.commit()
        
        test_queries = [
            "What scholarships are available for PwD students in Karnataka?",
            "Check my eligibility for karnataka_pwd_scholarship",
            "What documents do I need for NSP scholarship?",
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\nQuery {i}: {query[:60]}...")
            
            t_start = time.time()
            t_first_token = None
            t_retrieval = None
            token_count = 0
            content_len = 0
            
            async for event in svc.stream_message("benchmark-user", conv.id, query):
                event_type = event.get("type")
                
                if event_type == "timing":
                    stage = event.get("stage")
                    if stage == "first_token" and t_first_token is None:
                        t_first_token = time.time()
                    elif stage == "retrieval_complete" and t_retrieval is None:
                        t_retrieval = time.time()
                
                elif event_type == "token":
                    token_count += 1
                    content_len += len(event.get("content", ""))
                
                elif event_type == "done":
                    break
            
            t_end = time.time()
            
            duration_ms = int((t_end - t_start) * 1000)
            ttft_ms = int((t_first_token - t_start) * 1000) if t_first_token else 0
            retrieval_ms = int((t_retrieval - t_start) * 1000) if t_retrieval else 0
            
            print(f"  Total time: {duration_ms}ms")
            print(f"  Time to first token: {ttft_ms}ms")
            print(f"  Retrieval time: {retrieval_ms}ms")
            print(f"  Content length: {content_len} chars")
            print(f"  Token count: {token_count}")
            if token_count > 0 and t_first_token:
                generation_time = t_end - t_first_token
                tokens_per_sec = token_count / generation_time if generation_time > 0 else 0
                print(f"  Tokens/sec: {tokens_per_sec:.1f}")
        
        await db.delete(conv)
        await db.commit()


async def main():
    parser = argparse.ArgumentParser(description="Benchmark streaming performance")
    parser.add_argument("--non-streaming", action="store_true", help="Run non-streaming benchmark")
    parser.add_argument("--streaming", action="store_true", help="Run streaming benchmark")
    args = parser.parse_args()
    
    settings = get_settings()
    print(f"LLM Provider: {settings.llm_provider}")
    print(f"Model: {settings.azure_ai_model or settings.openai_model or settings.ollama_model or 'MOCK'}")
    
    if args.non_streaming or not (args.streaming):
        await benchmark_non_streaming()
    
    if args.streaming or not (args.non_streaming):
        await benchmark_streaming()
    
    print("\n=== BENCHMARK COMPLETE ===")


if __name__ == "__main__":
    asyncio.run(main())
