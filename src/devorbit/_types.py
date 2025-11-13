"""Type definitions for the Devorbit SDK.

This module provides TypedDicts and type aliases that mirror the Claude SDK's type system.
"""

from typing import Any, Dict, List, Literal, Optional, TypedDict, Union

from typing_extensions import NotRequired, Required

# ============================================================================
# Prompt Caching Types
# ============================================================================


class CacheControl(TypedDict):
    """Cache control for prompt caching (beta feature)."""

    type: Required[Literal["ephemeral"]]


# ============================================================================
# Content Types
# ============================================================================


class TextContent(TypedDict):
    """Text content block."""

    type: Required[Literal["text"]]
    text: Required[str]
    cache_control: NotRequired[CacheControl]  # For prompt caching


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
    cache_control: NotRequired[CacheControl]  # For prompt caching


class DocumentSource(TypedDict):
    """Document source (PDF, etc.)."""

    type: Required[Literal["base64"]]
    media_type: Required[Literal["application/pdf"]]
    data: Required[str]


class DocumentContent(TypedDict):
    """Document content block (PDF support)."""

    type: Required[Literal["document"]]
    source: Required[DocumentSource]
    cache_control: NotRequired[CacheControl]  # For prompt caching


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
ContentBlock = Union[
    TextContent, ImageContent, DocumentContent, ToolUseContent, ToolResultContent
]

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
    cache_control: NotRequired[CacheControl]  # For prompt caching


# ============================================================================
# Built-in Tool Types (Beta)
# ============================================================================


class ComputerUseTool(TypedDict):
    """Computer use tool for controlling computer interfaces."""

    type: Required[Literal["computer_20241022"]]
    name: Required[Literal["computer"]]
    display_width_px: Required[int]
    display_height_px: Required[int]
    display_number: NotRequired[int]


class BashTool(TypedDict):
    """Bash tool for executing shell commands."""

    type: Required[Literal["bash_20241022"]]
    name: Required[Literal["bash"]]


class TextEditorTool(TypedDict):
    """Text editor tool for file manipulation."""

    type: Required[Literal["text_editor_20241022"]]
    name: Required[Literal["str_replace_editor"]]


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
    # Beta features
    thinking: NotRequired[Dict[str, Any]]  # Extended thinking configuration


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

# ============================================================================
# Message Batch Types
# ============================================================================


class BatchRequest(TypedDict):
    """A single request in a batch."""

    custom_id: Required[str]
    params: Required[MessageCreateParams]


class BatchCreateParams(TypedDict):
    """Parameters for creating a message batch."""

    requests: Required[List[BatchRequest]]


class BatchStatus(TypedDict):
    """Batch processing status."""

    processing_status: Literal["in_progress", "ended", "canceling", "canceled"]
    request_counts: Dict[str, int]
