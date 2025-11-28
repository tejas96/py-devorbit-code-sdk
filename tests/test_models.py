"""Tests for Pydantic models."""

from devorbit.core.models import MessageResponse, TextBlock, TokenCountResponse, ToolUseBlock, Usage


def test_text_block():
    """Test TextBlock model."""
    block = TextBlock(type="text", text="Hello, world!")

    assert block.type == "text"
    assert block.text == "Hello, world!"


def test_tool_use_block():
    """Test ToolUseBlock model."""
    block = ToolUseBlock(
        type="tool_use",
        id="tool_123",
        name="get_weather",
        input={"location": "Tokyo"},
    )

    assert block.type == "tool_use"
    assert block.id == "tool_123"
    assert block.name == "get_weather"
    assert block.input["location"] == "Tokyo"


def test_usage():
    """Test Usage model."""
    usage = Usage(
        input_tokens=100,
        output_tokens=50,
        cache_creation_input_tokens=10,
        cache_read_input_tokens=5,
    )

    assert usage.input_tokens == 100
    assert usage.output_tokens == 50
    assert usage.cache_creation_input_tokens == 10
    assert usage.cache_read_input_tokens == 5


def test_message_response():
    """Test MessageResponse model."""
    response = MessageResponse(
        id="msg_123",
        type="message",
        role="assistant",
        content=[TextBlock(type="text", text="Hello!")],
        model="claude-sonnet-4-5-20250929",
        stop_reason="end_turn",
        stop_sequence=None,
        usage=Usage(input_tokens=10, output_tokens=5),
    )

    assert response.id == "msg_123"
    assert response.role == "assistant"
    assert len(response.content) == 1
    assert response.content[0].text == "Hello!"
    assert response.stop_reason == "end_turn"


def test_message_response_str():
    """Test MessageResponse string representation."""
    response = MessageResponse(
        id="msg_123",
        type="message",
        role="assistant",
        content=[
            TextBlock(type="text", text="Hello!"),
            TextBlock(type="text", text=" How are you?"),
        ],
        model="claude-sonnet-4-5-20250929",
        stop_reason="end_turn",
        stop_sequence=None,
        usage=Usage(input_tokens=10, output_tokens=5),
    )

    assert str(response) == "Hello!\n How are you?"


def test_token_count_response():
    """Test TokenCountResponse model."""
    response = TokenCountResponse(input_tokens=42)

    assert response.input_tokens == 42


def test_message_response_with_tool_use():
    """Test MessageResponse with tool use."""
    response = MessageResponse(
        id="msg_123",
        type="message",
        role="assistant",
        content=[
            TextBlock(type="text", text="Let me check the weather."),
            ToolUseBlock(
                type="tool_use",
                id="tool_1",
                name="get_weather",
                input={"location": "Tokyo"},
            ),
        ],
        model="claude-sonnet-4-5-20250929",
        stop_reason="tool_use",
        stop_sequence=None,
        usage=Usage(input_tokens=50, output_tokens=30),
    )

    assert len(response.content) == 2
    assert response.content[1].type == "tool_use"
    assert response.content[1].name == "get_weather"
    assert response.stop_reason == "tool_use"
