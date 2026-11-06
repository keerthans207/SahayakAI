"""Integration tests for streaming with real database.

These tests use a temporary SQLite database to verify the full streaming pipeline.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.models.db import Base, User, UserProfile, Conversation, Message
from app.services.chat_service import ChatService


@pytest.fixture
async def test_db():
    """Create a temporary async SQLite database for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Create test user
        user = User(external_id="test-user", display_name="Test User")
        session.add(user)
        await session.flush()

        profile = UserProfile(
            user_id=user.id,
            state="Karnataka",
            disability_percentage=50,
            preferred_language="en",
        )
        session.add(profile)

        conv = Conversation(user_id=user.id, title="Test Session", language="en")
        session.add(conv)
        await session.commit()

        yield session, conv.id

    await engine.dispose()


@pytest.mark.asyncio
async def test_streaming_end_to_end(test_db):
    """Test full streaming pipeline with real database."""
    db, conv_id = test_db

    svc = ChatService(db)

    events = []
    accumulated_content = ""

    async for event in svc.stream_message(
        "test-user",
        conv_id,
        "What scholarships are available in Karnataka?",
        "en"
    ):
        events.append(event)
        if event.get("type") == "token":
            accumulated_content += event.get("content", "")

    # Verify we got events
    assert len(events) > 0

    # Verify timing events
    timing_events = [e for e in events if e.get("type") == "timing"]
    assert len(timing_events) > 0
    assert any(e.get("stage") == "profile_loaded" for e in timing_events)

    # Verify token events
    token_events = [e for e in events if e.get("type") == "token"]
    assert len(token_events) > 0

    # Verify content was generated
    assert len(accumulated_content) > 0

    # Verify done event
    done_events = [e for e in events if e.get("type") == "done"]
    assert len(done_events) == 1

    # Verify message was saved to database
    from sqlalchemy import select
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conv_id, Message.role == "assistant")
        .order_by(Message.created_at.desc())
    )
    messages = result.scalars().all()
    assert len(messages) == 1
    assert messages[0].content == accumulated_content


@pytest.mark.asyncio
async def test_non_streaming_includes_timing(test_db):
    """Test non-streaming response includes timing metadata."""
    db, conv_id = test_db

    svc = ChatService(db)

    result = await svc.send_message(
        "test-user",
        conv_id,
        "Tell me about UDID registration",
        "en"
    )

    assert "timing" in result
    timing = result["timing"]
    assert "profile_load_ms" in timing
    assert "agent_ms" in timing
    assert "persistence_ms" in timing
    assert "total_ms" in timing

    # All timing values should be non-negative integers
    assert all(isinstance(timing[k], int) and timing[k] >= 0 for k in timing)


@pytest.mark.asyncio
async def test_streaming_preserves_text_exactly(test_db):
    """Verify streaming reconstructs exact text without corruption."""
    db, conv_id = test_db

    svc = ChatService(db)

    # Collect all tokens
    accumulated = ""
    final_message_id = None

    async for event in svc.stream_message(
        "test-user",
        conv_id,
        "List available schemes",
        "en"
    ):
        if event.get("type") == "token":
            accumulated += event.get("content", "")
        elif event.get("type") == "done":
            final_message_id = event.get("message_id")

    # Retrieve the persisted message
    from sqlalchemy import select
    result = await db.execute(
        select(Message).where(Message.id == final_message_id)
    )
    db_message = result.scalar_one()

    # Accumulated tokens should exactly match persisted content
    assert accumulated == db_message.content


@pytest.mark.asyncio
async def test_streaming_tokens_arrive_progressively(test_db):
    """Verify tokens arrive during generation, not all at once."""
    db, conv_id = test_db

    svc = ChatService(db)

    token_count = 0
    timing_before_first_token = None

    async for event in svc.stream_message(
        "test-user",
        conv_id,
        "Explain scholarship eligibility",
        "en"
    ):
        if event.get("type") == "timing" and event.get("stage") == "first_token":
            timing_before_first_token = event.get("elapsed_ms")
        elif event.get("type") == "token":
            token_count += 1
            if token_count >= 3:
                # Stop early to prove streaming works progressively
                break

    # Should have received timing before tokens
    assert timing_before_first_token is not None
    # Should have received multiple tokens
    assert token_count >= 3


@pytest.mark.asyncio
async def test_streaming_handles_multiple_messages(test_db):
    """Verify streaming works correctly across multiple messages in a conversation."""
    db, conv_id = test_db

    svc = ChatService(db)

    messages = [
        "What is UDID?",
        "How do I apply for it?",
        "What documents do I need?",
    ]

    for msg in messages:
        events = []
        async for event in svc.stream_message("test-user", conv_id, msg, "en"):
            events.append(event)

        # Each message should complete successfully
        assert any(e.get("type") == "done" for e in events)

    # Verify all messages were saved
    from sqlalchemy import select
    result = await db.execute(
        select(Message).where(Message.conversation_id == conv_id).order_by(Message.created_at)
    )
    all_messages = result.scalars().all()

    # 3 user messages + 3 assistant messages = 6 total
    assert len(all_messages) == 6
    assert sum(1 for m in all_messages if m.role == "user") == 3
    assert sum(1 for m in all_messages if m.role == "assistant") == 3


@pytest.mark.asyncio
async def test_streaming_metadata_event(test_db):
    """Verify metadata event contains expected fields."""
    db, conv_id = test_db

    svc = ChatService(db)

    metadata_event = None

    async for event in svc.stream_message(
        "test-user",
        conv_id,
        "Check eligibility for karnataka_pwd_scholarship",
        "en"
    ):
        if event.get("type") == "metadata":
            metadata_event = event.get("data")

    assert metadata_event is not None
    assert "intent" in metadata_event
    assert "official_sources" in metadata_event
