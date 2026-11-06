"""Content normalization utility for AI message responses.

Azure Foundry LangChain adapters return AIMessage.content as structured objects
(list of dictionaries with type/text keys). This module normalizes all response
formats to plain strings while preserving Markdown formatting.
"""

from typing import Any


def normalize_content(content: Any) -> str:
    """
    Normalize AI message content to a plain string.

    Args:
        content: Any content format from LangChain/AI providers:
                 - str: returned as-is
                 - list[dict]: extracted and concatenated text blocks
                 - dict: single text block extracted
                 - other: converted to string

    Returns:
        Normalized string content with Markdown preserved.

    Examples:
        >>> normalize_content("Hello world")
        'Hello world'
        >>> normalize_content([{"type": "text", "text": "Hello"}])
        'Hello'
        >>> normalize_content([{"type": "text", "text": "A"}, {"type": "text", "text": "B"}])
        'AB'
        >>> normalize_content({"type": "text", "text": "Single block"})
        'Single block'
    """
    # Already a string — return as-is
    if isinstance(content, str):
        return content

    # List of content blocks (Azure Foundry format)
    if isinstance(content, list):
        text_parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                # Extract text from {"type": "text", "text": "..."}
                if block.get("type") == "text" and "text" in block:
                    text_parts.append(str(block["text"]))
                # Ignore unsupported block types (images, etc.) safely
            elif isinstance(block, str):
                # Some providers may mix strings in the list
                text_parts.append(block)
        return "".join(text_parts)

    # Single content block as dict
    if isinstance(content, dict):
        if content.get("type") == "text" and "text" in content:
            return str(content["text"])
        # Fallback for unrecognized dict structure
        return str(content.get("text", ""))

    # Fallback for unexpected types
    return str(content)
