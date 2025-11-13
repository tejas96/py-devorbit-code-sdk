"""Devorbit Multi-LLM SDK.

A unified Python SDK for multiple LLM providers with a Claude SDK-like interface.
"""

from ._client import AsyncDevorbit, Devorbit
from ._errors import (
    APIConnectionError,
    APIError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    DevorbitError,
    InternalServerError,
    NotFoundError,
    OverloadedError,
    PermissionDeniedError,
    ProviderError,
    RateLimitError,
    StreamError,
    UnprocessableEntityError,
    UnsupportedProviderError,
)
from ._models import (
    ContentBlockDeltaEvent,
    ContentBlockStartEvent,
    ContentBlockStopEvent,
    MessageDeltaEvent,
    MessageResponse,
    MessageStartEvent,
    MessageStopEvent,
    TextBlock,
    TokenCountResponse,
    ToolUseBlock,
    Usage,
)
from ._types import (
    ContentBlock,
    ImageContent,
    Message,
    MessageCreateParams,
    ProviderType,
    StopReason,
    TextContent,
    Tool,
    ToolChoice,
    ToolResultContent,
    ToolUseContent,
)

__version__ = "0.1.0"

__all__ = [
    # Main clients
    "Devorbit",
    "AsyncDevorbit",
    # Errors
    "DevorbitError",
    "APIError",
    "APIConnectionError",
    "APITimeoutError",
    "APIStatusError",
    "RateLimitError",
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
    "BadRequestError",
    "UnprocessableEntityError",
    "InternalServerError",
    "OverloadedError",
    "ProviderError",
    "UnsupportedProviderError",
    "StreamError",
    # Models
    "MessageResponse",
    "TextBlock",
    "ToolUseBlock",
    "Usage",
    "TokenCountResponse",
    "MessageStartEvent",
    "ContentBlockStartEvent",
    "ContentBlockDeltaEvent",
    "ContentBlockStopEvent",
    "MessageDeltaEvent",
    "MessageStopEvent",
    # Types
    "Message",
    "MessageCreateParams",
    "ContentBlock",
    "TextContent",
    "ImageContent",
    "ToolUseContent",
    "ToolResultContent",
    "Tool",
    "ToolChoice",
    "ProviderType",
    "StopReason",
]
