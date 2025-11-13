"""Type definitions for the Devorbit SDK.

This module provides TypedDicts and type aliases that mirror the Claude SDK's type system.
"""

from typing import Any, Dict, List, Literal, Optional, TypedDict, Union

from typing_extensions import NotRequired, Required

# ============================================================================
# Content Types
# ============================================================================


class TextContent(TypedDict):
    """Text content block."""

    type: Required[Literal["text"]]
    text: Required[str]


class ImageSource(TypedDict):
    """Image source with base64 data or URL."""

    type: Required[Literal["base64", "url"]]
    media_type: Required[str]
    data: NotRequired[str]  # For base64
    url: NotRequired[str]  # For URL


class ImageContent(TypedDict):
    """Image content block."""

    type: Required[Literal["image"]]
    source: Required[ImageSource]


class ToolUseContent(TypedDict):
    """Tool use request from the model."""

    type: Required[Literal["tool_use"]]
    id: Required[str]
    name: Required[str]
    input: Required[Dict[str, Any]]


class ToolResultContent(TypedDict):
    """Tool result provided by the client."""

    type: Required[Literal["tool_result"]]
    tool_use_id: Required[str]
    content: NotRequired[Union[str, List[Union[TextContent, ImageContent]]]]
    is_error: NotRequired[bool]


# Union of all content types
ContentBlock = Union[TextContent, ImageContent, ToolUseContent, ToolResultContent]

# ============================================================================
# Message Types
# ============================================================================


class Message(TypedDict):
    """A message in the conversation."""

    role: Required[Literal["user", "assistant"]]
    content: Required[Union[str, List[ContentBlock]]]


# ============================================================================
# Tool Types
# ============================================================================


class ToolInputSchema(TypedDict):
    """JSON Schema for tool input."""

    type: Required[Literal["object"]]
    properties: Required[Dict[str, Any]]
    required: NotRequired[List[str]]


class Tool(TypedDict):
    """Tool definition."""

    name: Required[str]
    description: Required[str]
    input_schema: Required[ToolInputSchema]


class ToolChoiceAuto(TypedDict):
    """Auto tool choice - model decides."""

    type: Required[Literal["auto"]]


class ToolChoiceAny(TypedDict):
    """Any tool choice - model must use a tool."""

    type: Required[Literal["any"]]


class ToolChoiceTool(TypedDict):
    """Specific tool choice."""

    type: Required[Literal["tool"]]
    name: Required[str]


ToolChoice = Union[ToolChoiceAuto, ToolChoiceAny, ToolChoiceTool]

# ============================================================================
# Metadata Types
# ============================================================================


class Metadata(TypedDict):
    """Request metadata."""

    user_id: NotRequired[str]


# ============================================================================
# Request Parameters
# ============================================================================


class MessageCreateParams(TypedDict):
    """Parameters for creating a message.

    This mirrors the Claude SDK's message creation parameters.
    """

    model: Required[str]
    messages: Required[List[Message]]
    max_tokens: Required[int]
    system: NotRequired[Union[str, List[TextContent]]]
    temperature: NotRequired[float]
    top_p: NotRequired[float]
    top_k: NotRequired[int]
    stop_sequences: NotRequired[List[str]]
    stream: NotRequired[bool]
    tools: NotRequired[List[Tool]]
    tool_choice: NotRequired[ToolChoice]
    metadata: NotRequired[Metadata]


class MessageStreamParams(MessageCreateParams):
    """Parameters for streaming a message."""

    stream: Required[Literal[True]]


class MessageCountTokensParams(TypedDict):
    """Parameters for counting tokens."""

    model: Required[str]
    messages: Required[List[Message]]
    system: NotRequired[Union[str, List[TextContent]]]
    tools: NotRequired[List[Tool]]


# ============================================================================
# Provider Types
# ============================================================================

ProviderType = Literal["anthropic", "openai", "gemini", "mistral", "codellama"]

# ============================================================================
# Stop Reasons
# ============================================================================

StopReason = Literal[
    "end_turn",
    "max_tokens",
    "stop_sequence",
    "tool_use",
    "content_filter",
]
