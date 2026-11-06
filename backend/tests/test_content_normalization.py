from app.agents.graph import _normalize_ai_content


def test_normalizes_plain_string():
    assert _normalize_ai_content("Hello Sahayak") == "Hello Sahayak"


def test_extracts_azure_text_block():
    result = _normalize_ai_content([
        {
            "type": "text",
            "text": "Scholarship information",
            "annotations": [],
            "id": "msg_test_123",
        }
    ])

    assert result == "Scholarship information"
    assert "annotations" not in result
    assert "msg_test_123" not in result


def test_extracts_multiple_text_blocks():
    result = _normalize_ai_content([
        {"type": "text", "text": "First paragraph"},
        {"type": "text", "text": "Second paragraph"},
    ])

    assert result == "First paragraph\nSecond paragraph"


def test_ignores_non_text_blocks():
    result = _normalize_ai_content([
        {"type": "image", "data": "ignored"},
        {"type": "text", "text": "Readable answer"},
    ])

    assert result == "Readable answer"
