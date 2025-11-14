"""Devorbit Multi-LLM SDK.

A unified Python SDK for multiple LLM providers with a Claude SDK-like interface.
"""

from ._beta import AsyncBeta, Beta
from ._builtin_tools import (
    BASH_TOOL,
    COMPUTER_USE_TOOL,
    TEXT_EDITOR_TOOL,
    create_bash_tool,
    create_computer_use_tool,
    create_text_editor_tool,
    get_all_builtin_tools,
)
from ._file_tools import (
    edit_file,
    get_all_file_tools,
    multi_edit_file,
    read_file,
    write_file,
)
from ._search_tools import get_all_search_tools, glob_files, grep_code
from ._todo_tools import (
    clear_todo_state,
    get_all_todo_tools,
    get_current_todos,
    todo_read,
    todo_write,
)
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
from ._mcp import MCPClient, MCPManager, MCPServerConfig, load_mcp_config
from ._models import (
    BatchRequestCounts,
    BatchResult,
    ContentBlockDeltaEvent,
    ContentBlockStartEvent,
    ContentBlockStopEvent,
    DocumentBlock,
    MessageBatchResponse,
    MessageDeltaEvent,
    MessageResponse,
    MessageStartEvent,
    MessageStopEvent,
    TextBlock,
    ThinkingBlock,
    TokenCountResponse,
    ToolUseBlock,
    Usage,
)
from ._tool_helpers import ToolExecutor, beta_tool, gather_tools
from ._types import (
    BashTool,
    BatchCreateParams,
    BatchRequest,
    BatchStatus,
    CacheControl,
    ComputerUseTool,
    ContentBlock,
    DocumentContent,
    DocumentSource,
    ImageContent,
    Message,
    MessageCreateParams,
    ProviderType,
    StopReason,
    TextContent,
    TextEditorTool,
    Tool,
    ToolChoice,
    ToolResultContent,
    ToolUseContent,
)


__version__ = "0.1.0"

__all__ = [
    "BASH_TOOL",
    "COMPUTER_USE_TOOL",
    "TEXT_EDITOR_TOOL",
    "APIConnectionError",
    "APIError",
    "APIStatusError",
    "APITimeoutError",
    "AsyncBeta",
    "AsyncDevorbit",
    "AuthenticationError",
    "BadRequestError",
    "BashTool",
    "BatchCreateParams",
    "BatchRequest",
    "BatchRequestCounts",
    "BatchResult",
    "BatchStatus",
    # Beta namespace
    "Beta",
    "CacheControl",
    "ComputerUseTool",
    "ContentBlock",
    "ContentBlockDeltaEvent",
    "ContentBlockStartEvent",
    "ContentBlockStopEvent",
    # Main clients
    "Devorbit",
    # Errors
    "DevorbitError",
    "DocumentBlock",
    "DocumentContent",
    "DocumentSource",
    "ImageContent",
    "InternalServerError",
    # MCP support
    "MCPClient",
    "MCPManager",
    "MCPServerConfig",
    # Types
    "Message",
    "MessageBatchResponse",
    "MessageCreateParams",
    "MessageDeltaEvent",
    # Models
    "MessageResponse",
    "MessageStartEvent",
    "MessageStopEvent",
    "NotFoundError",
    "OverloadedError",
    "PermissionDeniedError",
    "ProviderError",
    "ProviderType",
    "RateLimitError",
    "StopReason",
    "StreamError",
    "TextBlock",
    "TextContent",
    "TextEditorTool",
    "ThinkingBlock",
    "TokenCountResponse",
    "Tool",
    "ToolChoice",
    "ToolExecutor",
    "ToolResultContent",
    "ToolUseBlock",
    "ToolUseContent",
    "UnprocessableEntityError",
    "UnsupportedProviderError",
    "Usage",
    # Tool helpers
    "beta_tool",
    # Built-in tools
    "create_bash_tool",
    "create_computer_use_tool",
    "create_text_editor_tool",
    "gather_tools",
    "get_all_builtin_tools",
    # File operation tools
    "read_file",
    "write_file",
    "edit_file",
    "multi_edit_file",
    "get_all_file_tools",
    # Search tools
    "glob_files",
    "grep_code",
    "get_all_search_tools",
    # Todo management tools
    "todo_write",
    "todo_read",
    "get_all_todo_tools",
    "clear_todo_state",
    "get_current_todos",
    # MCP
    "load_mcp_config",
]
