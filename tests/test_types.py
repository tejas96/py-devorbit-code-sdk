"""Tests for type definitions."""

from devorbit._types import (
    ImageContent,
    Message,
    MessageCreateParams,
    TextContent,
    Tool,
    ToolChoice,
)


def test_text_content():
    """Test TextContent type."""
    content: TextContent = {
        "type": "text",
        "text": "Hello, world!",
    }
    assert content["type"] == "text"
    assert content["text"] == "Hello, world!"


def test_image_content():
    """Test ImageContent type."""
    content: ImageContent = {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": "image/jpeg",
            "data": "base64data",
        },
    }
    assert content["type"] == "image"
    assert content["source"]["type"] == "base64"


def test_message():
    """Test Message type."""
    message: Message = {
        "role": "user",
        "content": "Hello!",
    }
    assert message["role"] == "user"
    assert message["content"] == "Hello!"


def test_message_with_content_blocks():
    """Test Message with content blocks."""
    message: Message = {
        "role": "user",
        "content": [
            {"type": "text", "text": "Hello!"},
            {
                "type": "image",
                "source": {
                    "type": "url",
                    "media_type": "image/jpeg",
                    "url": "https://example.com/image.jpg",
                },
            },
        ],
    }
    assert message["role"] == "user"
    assert len(message["content"]) == 2


def test_tool():
    """Test Tool type."""
    tool: Tool = {
        "name": "get_weather",
        "description": "Get weather for a location",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string"},
            },
            "required": ["location"],
        },
    }
    assert tool["name"] == "get_weather"
    assert "location" in tool["input_schema"]["properties"]


def test_tool_choice_auto():
    """Test auto tool choice."""
    choice: ToolChoice = {"type": "auto"}
    assert choice["type"] == "auto"


def test_tool_choice_specific():
    """Test specific tool choice."""
    choice: ToolChoice = {
        "type": "tool",
        "name": "get_weather",
    }
    assert choice["type"] == "tool"
    assert choice["name"] == "get_weather"


def test_message_create_params():
    """Test MessageCreateParams type."""
    params: MessageCreateParams = {
        "model": "claude-sonnet-4-5-20250929",
        "messages": [
            {"role": "user", "content": "Hello!"},
        ],
        "max_tokens": 1024,
        "temperature": 0.7,
    }
    assert params["model"] == "claude-sonnet-4-5-20250929"
    assert params["max_tokens"] == 1024
    assert params["temperature"] == 0.7
