"""Pydantic models for API responses.

This module provides Pydantic models that mirror the Claude SDK's response structure.
"""

from typing import Any, Literal

from pydantic import BaseModel

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
    source: dict[str, Any]


class ToolUseBlock(BaseModel):
    """Tool use block in response."""

    type: Literal["tool_use"] = "tool_use"
    id: str
    name: str
    input: dict[str, Any]


class ThinkingBlock(BaseModel):
    """Thinking block in response (for extended thinking models)."""

    type: Literal["thinking"] = "thinking"
    thinking: str


class DocumentBlock(BaseModel):
    """Document block in response (PDF support)."""

    type: Literal["document"] = "document"
    source: dict[str, Any]


# Union of all response content blocks
ResponseContentBlock = TextBlock | ImageBlock | ToolUseBlock | ThinkingBlock | DocumentBlock


# ============================================================================
# Usage Model
# ============================================================================


class Usage(BaseModel):
    """Token usage information."""

    input_tokens: int
    output_tokens: int
    cache_creation_input_tokens: int | None = None
    cache_read_input_tokens: int | None = None


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
    content: list[ResponseContentBlock]
    model: str
    stop_reason: StopReason | None = None
    stop_sequence: str | None = None
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
    delta: ContentBlockDeltaText | ContentBlockDeltaToolUse


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
    delta: dict[str, Any]
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
    error: dict[str, Any]


# Union of all stream events
StreamEvent = (
    MessageStartEvent
    | ContentBlockStartEvent
    | ContentBlockDeltaEvent
    | ContentBlockStopEvent
    | MessageDeltaEvent
    | MessageStopEvent
    | PingEvent
    | ErrorEvent
)


# ============================================================================
# Message Batch Models
# ============================================================================


class BatchRequestCounts(BaseModel):
    """Request counts for a batch."""

    processing: int = 0
    succeeded: int = 0
    errored: int = 0
    canceled: int = 0
    expired: int = 0


class MessageBatchResponse(BaseModel):
    """Response from batch creation."""

    id: str
    type: Literal["message_batch"] = "message_batch"
    processing_status: Literal["in_progress", "canceling", "ended"]
    request_counts: BatchRequestCounts
    ended_at: str | None = None
    created_at: str
    expires_at: str
    cancel_initiated_at: str | None = None
    results_url: str | None = None


class BatchResult(BaseModel):
    """Individual result from a batch."""

    custom_id: str
    result: MessageResponse | None = None
    error: dict[str, Any] | None = None
