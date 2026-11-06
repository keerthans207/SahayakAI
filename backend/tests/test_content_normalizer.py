"""Unit tests for content normalization."""



import pytest



from app.utils.content_normalizer import normalize_content





class TestNormalizeContent:

    """Test suite for normalize_content function."""



    def test_string_input_unchanged(self):

        """String input should be returned as-is."""

        assert normalize_content("Hello world") == "Hello world"

        assert normalize_content("") == ""

        assert normalize_content("Line 1\nLine 2") == "Line 1\nLine 2"



    def test_markdown_preserved(self):

        """Markdown formatting should be preserved."""

        markdown = "# Title\n\n**Bold** and *italic*\n\n- Item 1\n- Item 2"

        assert normalize_content(markdown) == markdown



    def test_single_text_block(self):

        """Single text block should extract the text field."""

        content = [{"type": "text", "text": "Hello from Azure"}]

        assert normalize_content(content) == "Hello from Azure"



    def test_multiple_text_blocks(self):

        """Multiple text blocks should be concatenated."""

        content = [

            {"type": "text", "text": "First part "},

            {"type": "text", "text": "second part "},

            {"type": "text", "text": "third part"},

        ]

        assert normalize_content(content) == "First part second part third part"



    def test_mixed_block_types(self):

        """Non-text blocks should be ignored safely."""

        content = [

            {"type": "text", "text": "Text before "},

            {"type": "image", "url": "http://example.com/img.png"},

            {"type": "text", "text": "text after"},

        ]

        assert normalize_content(content) == "Text before text after"



    def test_single_dict_block(self):

        """Single dict with type=text should extract text."""

        content = {"type": "text", "text": "Single block content"}

        assert normalize_content(content) == "Single block content"



    def test_dict_missing_text_field(self):

        """Dict without text field should return empty string."""

        content = {"type": "text"}

        assert normalize_content(content) == ""



    def test_unrecognized_dict_structure(self):

        """Unrecognized dict structure should attempt text extraction."""

        content = {"other_field": "value", "text": "fallback"}

        assert normalize_content(content) == "fallback"



    def test_empty_list(self):

        """Empty list should return empty string."""

        assert normalize_content([]) == ""



    def test_list_with_strings(self):

        """List containing strings should concatenate them."""

        content = ["Hello ", "world"]

        assert normalize_content(content) == "Hello world"



    def test_mixed_list_strings_and_dicts(self):

        """List with mixed strings and dicts should handle both."""

        content = [

            "Plain string ",

            {"type": "text", "text": "and dict text"},

        ]

        assert normalize_content(content) == "Plain string and dict text"



    def test_azure_foundry_response_format(self):

        """Test actual Azure Foundry response format."""

        # Simulates what Azure Foundry LangChain adapter returns

        content = [

            {

                "type": "text",

                "text": "Here are the main scholarships available:\n\n"

                        "1. **Post Matric Scholarship**\n"

                        "2. **Pre Matric Scholarship**\n\n"

                        "These schemes support students with disabilities.",

            }

        ]

        result = normalize_content(content)

        assert "Here are the main scholarships available:" in result

        assert "**Post Matric Scholarship**" in result

        assert "**Pre Matric Scholarship**" in result

        assert "[{" not in result  # Should not contain Python dict representation



    def test_fallback_conversion(self):

        """Unexpected types should convert to string as fallback."""

        assert normalize_content(123) == "123"

        assert normalize_content(None) == "None"

        assert normalize_content(True) == "True"



    def test_nested_structures(self):

        """Nested structures should be handled gracefully."""

        content = [{"type": "text", "text": "Valid"}, {"nested": {"deep": "value"}}]

        # Should extract "Valid" and ignore the nested dict

        assert normalize_content(content) == "Valid"
