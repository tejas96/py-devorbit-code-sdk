"""Pydantic models for API responses.

This module provides Pydantic models that mirror the Claude SDK's response structure.
"""

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field

from ._types import StopReason


# ============================================================================
# Content Block Models
# ============================================================================


class TextBlock(BaseModel):
    """Text content block in response."""

    type: Literal["text"] = "text"
    text: str


class ImageBlock(BaseModel):
    """Image content block in response."""

    type: Literal["image"] = "image"
    source: Dict[str, Any]


class ToolUseBlock(BaseModel):
    """Tool use block in response."""

    type: Literal["tool_use"] = "tool_use"
    id: str
    name: str
    input: Dict[str, Any]


class ThinkingBlock(BaseModel):
    """Thinking block in response (for extended thinking models)."""

    type: Literal["thinking"] = "thinking"
    thinking: str


# Union of all response content blocks
ResponseContentBlock = Union[TextBlock, ImageBlock, ToolUseBlock, ThinkingBlock]


# ============================================================================
# Usage Model
# ============================================================================


class Usage(BaseModel):
    """Token usage information."""

    input_tokens: int
    output_tokens: int
    cache_creation_input_tokens: Optional[int] = None
    cache_read_input_tokens: Optional[int] = None


# ============================================================================
# Message Response Model
# ============================================================================


class MessageResponse(BaseModel):
    """Response from message creation.

    This mirrors the Claude SDK's Message response structure.
    """

    id: str
    type: Literal["message"] = "message"
    role: Literal["assistant"] = "assistant"
    content: List[ResponseContentBlock]
    model: str
    stop_reason: Optional[StopReason] = None
    stop_sequence: Optional[str] = None
    usage: Usage

    def __str__(self) -> str:
        """String representation showing text content."""
        text_blocks = [block.text for block in self.content if isinstance(block, TextBlock)]
        return "\n".join(text_blocks) if text_blocks else ""


# ============================================================================
# Token Count Response Model
# ============================================================================


class TokenCountResponse(BaseModel):
    """Response from token counting."""

    input_tokens: int


# ============================================================================
# Streaming Event Models
# ============================================================================


class MessageStartEvent(BaseModel):
    """Stream event: message start."""

    type: Literal["message_start"] = "message_start"
    message: MessageResponse


class ContentBlockStartEvent(BaseModel):
    """Stream event: content block start."""

    type: Literal["content_block_start"] = "content_block_start"
    index: int
    content_block: ResponseContentBlock


class ContentBlockDeltaText(BaseModel):
    """Text delta in streaming."""

    type: Literal["text_delta"] = "text_delta"
    text: str


class ContentBlockDeltaToolUse(BaseModel):
    """Tool use delta in streaming."""

    type: Literal["input_json_delta"] = "input_json_delta"
    partial_json: str


class ContentBlockDeltaEvent(BaseModel):
    """Stream event: content block delta."""

    type: Literal["content_block_delta"] = "content_block_delta"
    index: int
    delta: Union[ContentBlockDeltaText, ContentBlockDeltaToolUse]


class ContentBlockStopEvent(BaseModel):
    """Stream event: content block stop."""

    type: Literal["content_block_stop"] = "content_block_stop"
    index: int


class MessageDeltaUsage(BaseModel):
    """Usage delta in streaming."""

    output_tokens: int


class MessageDeltaEvent(BaseModel):
    """Stream event: message delta."""

    type: Literal["message_delta"] = "message_delta"
    delta: Dict[str, Any]
    usage: MessageDeltaUsage


class MessageStopEvent(BaseModel):
    """Stream event: message stop."""

    type: Literal["message_stop"] = "message_stop"


class PingEvent(BaseModel):
    """Stream event: ping."""

    type: Literal["ping"] = "ping"


class ErrorEvent(BaseModel):
    """Stream event: error."""

    type: Literal["error"] = "error"
    error: Dict[str, Any]


# Union of all stream events
StreamEvent = Union[
    MessageStartEvent,
    ContentBlockStartEvent,
    ContentBlockDeltaEvent,
    ContentBlockStopEvent,
    MessageDeltaEvent,
    MessageStopEvent,
    PingEvent,
    ErrorEvent,
]
