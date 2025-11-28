"""Devorbit Multi-LLM SDK.

A unified Python SDK for multiple LLM providers with a Claude SDK-like interface.

Uses lazy loading for fast startup - modules are only imported when accessed.
"""

import importlib
from typing import TYPE_CHECKING, Any

# Version
__version__ = "0.1.0"

# Core exports that are always available (lightweight)
__all__ = [
    # Version
    "__version__",
    # Main client classes (lazy loaded)
    "Devorbit",
    "AsyncDevorbit",
    "Beta",
    "AsyncBeta",
    # Core types (lazy loaded)
    "Message",
    "Tool",
    "ToolChoice",
    "ContentBlock",
    "TextContent",
    "ImageContent",
    "ProviderType",
    # Response types (lazy loaded)
    "MessageResponse",
    "TextBlock",
    "ToolUseBlock",
    "Usage",
    # Errors (lazy loaded)
    "DevorbitError",
    "APIError",
    "AuthenticationError",
    "RateLimitError",
    # Tools (lazy loaded)
    "bash",
    "read_file",
    "write_file",
    "edit_file",
    "glob_files",
    "grep_code",
    "beta_tool",
]

# Lazy loading implementation
_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    # Core client
    "Devorbit": ("devorbit.core.client", "Devorbit"),
    "AsyncDevorbit": ("devorbit.core.client", "AsyncDevorbit"),
    "Beta": ("devorbit.core.beta", "Beta"),
    "AsyncBeta": ("devorbit.core.beta", "AsyncBeta"),
    # Types
    "Message": ("devorbit.core.types", "Message"),
    "Tool": ("devorbit.core.types", "Tool"),
    "ToolChoice": ("devorbit.core.types", "ToolChoice"),
    "ContentBlock": ("devorbit.core.types", "ContentBlock"),
    "TextContent": ("devorbit.core.types", "TextContent"),
    "ImageContent": ("devorbit.core.types", "ImageContent"),
    "ProviderType": ("devorbit.core.types", "ProviderType"),
    "StopReason": ("devorbit.core.types", "StopReason"),
    "CacheControl": ("devorbit.core.types", "CacheControl"),
    "DocumentContent": ("devorbit.core.types", "DocumentContent"),
    "DocumentSource": ("devorbit.core.types", "DocumentSource"),
    "ToolResultContent": ("devorbit.core.types", "ToolResultContent"),
    "ToolUseContent": ("devorbit.core.types", "ToolUseContent"),
    "BatchCreateParams": ("devorbit.core.types", "BatchCreateParams"),
    "BatchRequest": ("devorbit.core.types", "BatchRequest"),
    "BatchStatus": ("devorbit.core.types", "BatchStatus"),
    "MessageCreateParams": ("devorbit.core.types", "MessageCreateParams"),
    "BashTool": ("devorbit.core.types", "BashTool"),
    "ComputerUseTool": ("devorbit.core.types", "ComputerUseTool"),
    "TextEditorTool": ("devorbit.core.types", "TextEditorTool"),
    # Models
    "MessageResponse": ("devorbit.core.models", "MessageResponse"),
    "TextBlock": ("devorbit.core.models", "TextBlock"),
    "ToolUseBlock": ("devorbit.core.models", "ToolUseBlock"),
    "ThinkingBlock": ("devorbit.core.models", "ThinkingBlock"),
    "DocumentBlock": ("devorbit.core.models", "DocumentBlock"),
    "Usage": ("devorbit.core.models", "Usage"),
    "TokenCountResponse": ("devorbit.core.models", "TokenCountResponse"),
    "MessageBatchResponse": ("devorbit.core.models", "MessageBatchResponse"),
    "BatchResult": ("devorbit.core.models", "BatchResult"),
    "BatchRequestCounts": ("devorbit.core.models", "BatchRequestCounts"),
    "MessageStartEvent": ("devorbit.core.models", "MessageStartEvent"),
    "MessageStopEvent": ("devorbit.core.models", "MessageStopEvent"),
    "ContentBlockStartEvent": ("devorbit.core.models", "ContentBlockStartEvent"),
    "ContentBlockStopEvent": ("devorbit.core.models", "ContentBlockStopEvent"),
    "ContentBlockDeltaEvent": ("devorbit.core.models", "ContentBlockDeltaEvent"),
    # Errors
    "DevorbitError": ("devorbit.core.errors", "DevorbitError"),
    "APIError": ("devorbit.core.errors", "APIError"),
    "APIConnectionError": ("devorbit.core.errors", "APIConnectionError"),
    "APIStatusError": ("devorbit.core.errors", "APIStatusError"),
    "APITimeoutError": ("devorbit.core.errors", "APITimeoutError"),
    "AuthenticationError": ("devorbit.core.errors", "AuthenticationError"),
    "BadRequestError": ("devorbit.core.errors", "BadRequestError"),
    "InternalServerError": ("devorbit.core.errors", "InternalServerError"),
    "NotFoundError": ("devorbit.core.errors", "NotFoundError"),
    "OverloadedError": ("devorbit.core.errors", "OverloadedError"),
    "PermissionDeniedError": ("devorbit.core.errors", "PermissionDeniedError"),
    "ProviderError": ("devorbit.core.errors", "ProviderError"),
    "RateLimitError": ("devorbit.core.errors", "RateLimitError"),
    "StreamError": ("devorbit.core.errors", "StreamError"),
    "UnprocessableEntityError": ("devorbit.core.errors", "UnprocessableEntityError"),
    "UnsupportedProviderError": ("devorbit.core.errors", "UnsupportedProviderError"),
    # Config
    "DevorbitConfig": ("devorbit.core.config", "DevorbitConfig"),
    "load_config": ("devorbit.core.config", "load_config"),
    "save_config": ("devorbit.core.config", "save_config"),
    "read_config": ("devorbit.core.config", "read_config"),
    "update_config": ("devorbit.core.config", "update_config"),
    "get_all_config_tools": ("devorbit.core.config", "get_all_config_tools"),
    # Hooks
    "Hook": ("devorbit.core.hooks", "Hook"),
    "HookContext": ("devorbit.core.hooks", "HookContext"),
    "HookRegistry": ("devorbit.core.hooks", "HookRegistry"),
    "HookType": ("devorbit.core.hooks", "HookType"),
    "PythonHookHandler": ("devorbit.core.hooks", "PythonHookHandler"),
    "hook": ("devorbit.core.hooks", "hook"),
    "register_hook": ("devorbit.core.hooks", "register_hook"),
    "unregister_hook": ("devorbit.core.hooks", "unregister_hook"),
    "execute_hook": ("devorbit.core.hooks", "execute_hook"),
    "execute_hooks": ("devorbit.core.hooks", "execute_hooks"),
    "get_registry": ("devorbit.core.hooks", "get_registry"),
    "list_hooks": ("devorbit.core.hooks", "list_hooks"),
    "clear_hooks": ("devorbit.core.hooks", "clear_hooks"),
    "enable_hooks": ("devorbit.core.hooks", "enable_hooks"),
    "disable_hooks": ("devorbit.core.hooks", "disable_hooks"),
    "trigger_hook": ("devorbit.core.hooks", "trigger_hook"),
    "load_hooks_from_config": ("devorbit.core.hooks", "load_hooks_from_config"),
    "get_all_hook_tools": ("devorbit.core.hooks", "get_all_hook_tools"),
    # MCP
    "MCPClient": ("devorbit.core.mcp", "MCPClient"),
    "MCPManager": ("devorbit.core.mcp", "MCPManager"),
    "MCPServerConfig": ("devorbit.core.mcp", "MCPServerConfig"),
    "load_mcp_config": ("devorbit.core.mcp", "load_mcp_config"),
    # Planning
    "PlanningState": ("devorbit.core.planning", "PlanningState"),
    "enter_planning_mode": ("devorbit.core.planning", "enter_planning_mode"),
    "exit_plan_mode": ("devorbit.core.planning", "exit_plan_mode"),
    "get_current_plan": ("devorbit.core.planning", "get_current_plan"),
    "get_planning_status": ("devorbit.core.planning", "get_planning_status"),
    "is_planning_active": ("devorbit.core.planning", "is_planning_active"),
    "cancel_plan": ("devorbit.core.planning", "cancel_plan"),
    "get_all_planning_tools": ("devorbit.core.planning", "get_all_planning_tools"),
    # Plugins
    "BasePlugin": ("devorbit.core.plugins", "BasePlugin"),
    "DevorbitPlugin": ("devorbit.core.plugins", "DevorbitPlugin"),
    "LoadedPlugin": ("devorbit.core.plugins", "LoadedPlugin"),
    "PluginMetadata": ("devorbit.core.plugins", "PluginMetadata"),
    "PluginRegistry": ("devorbit.core.plugins", "PluginRegistry"),
    "get_plugin_registry": ("devorbit.core.plugins", "get_plugin_registry"),
    "discover_all_plugins": ("devorbit.core.plugins", "discover_all_plugins"),
    "load_and_initialize_plugin": ("devorbit.core.plugins", "load_and_initialize_plugin"),
    "list_plugins": ("devorbit.core.plugins", "list_plugins"),
    "enable_plugin": ("devorbit.core.plugins", "enable_plugin"),
    "disable_plugin": ("devorbit.core.plugins", "disable_plugin"),
    "get_plugin_tools": ("devorbit.core.plugins", "get_plugin_tools"),
    "get_all_plugin_tools": ("devorbit.core.plugins", "get_all_plugin_tools"),
    # Recovery
    "ErrorCategory": ("devorbit.core.recovery", "ErrorCategory"),
    "ErrorClassifier": ("devorbit.core.recovery", "ErrorClassifier"),
    "ErrorInfo": ("devorbit.core.recovery", "ErrorInfo"),
    "RecoveryManager": ("devorbit.core.recovery", "RecoveryManager"),
    "RecoveryStrategy": ("devorbit.core.recovery", "RecoveryStrategy"),
    "RetryConfig": ("devorbit.core.recovery", "RetryConfig"),
    "RetryHandler": ("devorbit.core.recovery", "RetryHandler"),
    "get_recovery_manager": ("devorbit.core.recovery", "get_recovery_manager"),
    "reset_recovery_manager": ("devorbit.core.recovery", "reset_recovery_manager"),
    "with_retry": ("devorbit.core.recovery", "with_retry"),
    # Skills
    "Skill": ("devorbit.core.skills", "Skill"),
    "SkillRegistry": ("devorbit.core.skills", "SkillRegistry"),
    "get_skill_registry": ("devorbit.core.skills", "get_skill_registry"),
    "register_skill": ("devorbit.core.skills", "register_skill"),
    "execute_skill": ("devorbit.core.skills", "execute_skill"),
    "list_available_skills": ("devorbit.core.skills", "list_available_skills"),
    "load_skills": ("devorbit.core.skills", "load_skills"),
    "run_skill": ("devorbit.core.skills", "run_skill"),
    "validate_skill": ("devorbit.core.skills", "validate_skill"),
    "get_all_skill_tools": ("devorbit.core.skills", "get_all_skill_tools"),
    # Tool helpers
    "beta_tool": ("devorbit.core.tool_helpers", "beta_tool"),
    "gather_tools": ("devorbit.core.tool_helpers", "gather_tools"),
    "ToolExecutor": ("devorbit.core.tool_helpers", "ToolExecutor"),
    # Tool registry
    "ToolRegistry": ("devorbit.core.tool_registry", "ToolRegistry"),
    "get_tool_registry": ("devorbit.core.tool_registry", "get_tool_registry"),
    "reset_tool_registry": ("devorbit.core.tool_registry", "reset_tool_registry"),
    "tool": ("devorbit.core.tool_registry", "tool"),
    # Slash commands
    "Command": ("devorbit.slash_commands.loader", "Command"),
    "CommandRegistry": ("devorbit.slash_commands.loader", "CommandRegistry"),
    "register_command": ("devorbit.slash_commands.loader", "register_command"),
    "execute_command": ("devorbit.slash_commands.loader", "execute_command"),
    "parse_command_invocation": ("devorbit.slash_commands.loader", "parse_command_invocation"),
    "list_slash_commands": ("devorbit.slash_commands.loader", "list_slash_commands"),
    "load_commands": ("devorbit.slash_commands.loader", "load_commands"),
    "run_slash_command": ("devorbit.slash_commands.loader", "run_slash_command"),
    "get_all_command_tools": ("devorbit.slash_commands.loader", "get_all_command_tools"),
    # Agent tools
    "AgentCoordinator": ("devorbit.tools.agent", "AgentCoordinator"),
    "AgentTask": ("devorbit.tools.agent", "AgentTask"),
    "TaskPriority": ("devorbit.tools.agent", "TaskPriority"),
    "TaskResult": ("devorbit.tools.agent", "TaskResult"),
    "TaskStatus": ("devorbit.tools.agent", "TaskStatus"),
    "task": ("devorbit.tools.agent", "task"),
    "task_status": ("devorbit.tools.agent", "task_status"),
    "task_cancel": ("devorbit.tools.agent", "task_cancel"),
    "list_active_tasks": ("devorbit.tools.agent", "list_active_tasks"),
    "list_agent_types": ("devorbit.tools.agent", "list_agent_types"),
    "get_agent_info": ("devorbit.tools.agent", "get_agent_info"),
    "cleanup_tasks": ("devorbit.tools.agent", "cleanup_tasks"),
    "get_all_agent_tools": ("devorbit.tools.agent", "get_all_agent_tools"),
    # Bash tools
    "bash": ("devorbit.tools.bash", "bash"),
    "bash_output": ("devorbit.tools.bash", "bash_output"),
    "kill_shell": ("devorbit.tools.bash", "kill_shell"),
    "list_active_sessions": ("devorbit.tools.bash", "list_active_sessions"),
    "cleanup_sessions": ("devorbit.tools.bash", "cleanup_sessions"),
    "get_all_bash_tools": ("devorbit.tools.bash", "get_all_bash_tools"),
    # File tools
    "read_file": ("devorbit.tools.file", "read_file"),
    "write_file": ("devorbit.tools.file", "write_file"),
    "edit_file": ("devorbit.tools.file", "edit_file"),
    "multi_edit_file": ("devorbit.tools.file", "multi_edit_file"),
    "list_directory": ("devorbit.tools.file", "list_directory"),
    "ls_directory": ("devorbit.tools.file", "ls_directory"),
    "get_file_info": ("devorbit.tools.file", "get_file_info"),
    "create_directory": ("devorbit.tools.file", "create_directory"),
    "delete_file": ("devorbit.tools.file", "delete_file"),
    "copy_file": ("devorbit.tools.file", "copy_file"),
    "move_file": ("devorbit.tools.file", "move_file"),
    "get_all_file_tools": ("devorbit.tools.file", "get_all_file_tools"),
    # Search tools
    "glob_files": ("devorbit.tools.search", "glob_files"),
    "grep_code": ("devorbit.tools.search", "grep_code"),
    "search_codebase": ("devorbit.tools.search", "search_codebase"),
    "find_definition": ("devorbit.tools.search", "find_definition"),
    "get_all_search_tools": ("devorbit.tools.search", "get_all_search_tools"),
    # Todo tools
    "todo_read": ("devorbit.tools.todo", "todo_read"),
    "todo_write": ("devorbit.tools.todo", "todo_write"),
    "get_all_todo_tools": ("devorbit.tools.todo", "get_all_todo_tools"),
    "clear_todo_state": ("devorbit.tools.todo", "clear_todo_state"),
    "get_current_todos": ("devorbit.tools.todo", "get_current_todos"),
    # Web tools
    "web_fetch": ("devorbit.tools.web", "web_fetch"),
    "web_search": ("devorbit.tools.web", "web_search"),
    "web_fetch_sync": ("devorbit.tools.web", "web_fetch_sync"),
    "web_search_sync": ("devorbit.tools.web", "web_search_sync"),
    "get_all_web_tools": ("devorbit.tools.web", "get_all_web_tools"),
    "create_web_fetch_tool": ("devorbit.tools.web", "create_web_fetch_tool"),
    "create_web_search_tool": ("devorbit.tools.web", "create_web_search_tool"),
    "html_to_markdown": ("devorbit.tools.web", "html_to_markdown"),
    # Notebook tools
    "notebook_read": ("devorbit.tools.notebook", "notebook_read"),
    "notebook_edit": ("devorbit.tools.notebook", "notebook_edit"),
    "get_all_notebook_tools": ("devorbit.tools.notebook", "get_all_notebook_tools"),
    "create_notebook_read_tool": ("devorbit.tools.notebook", "create_notebook_read_tool"),
    "create_notebook_edit_tool": ("devorbit.tools.notebook", "create_notebook_edit_tool"),
    # Builtin tools
    "BASH_TOOL": ("devorbit.tools.builtin", "BASH_TOOL"),
    "READ_FILE_TOOL": ("devorbit.tools.builtin", "READ_FILE_TOOL"),
    "WRITE_FILE_TOOL": ("devorbit.tools.builtin", "WRITE_FILE_TOOL"),
    "EDIT_FILE_TOOL": ("devorbit.tools.builtin", "EDIT_FILE_TOOL"),
    "GLOB_TOOL": ("devorbit.tools.builtin", "GLOB_TOOL"),
    "GREP_TOOL": ("devorbit.tools.builtin", "GREP_TOOL"),
    "WEB_FETCH_TOOL": ("devorbit.tools.builtin", "WEB_FETCH_TOOL"),
    "WEB_SEARCH_TOOL": ("devorbit.tools.builtin", "WEB_SEARCH_TOOL"),
    "TODO_READ_TOOL": ("devorbit.tools.builtin", "TODO_READ_TOOL"),
    "TODO_WRITE_TOOL": ("devorbit.tools.builtin", "TODO_WRITE_TOOL"),
    "NOTEBOOK_READ_TOOL": ("devorbit.tools.builtin", "NOTEBOOK_READ_TOOL"),
    "NOTEBOOK_EDIT_TOOL": ("devorbit.tools.builtin", "NOTEBOOK_EDIT_TOOL"),
    "TASK_TOOL": ("devorbit.tools.builtin", "TASK_TOOL"),
    "TASK_STATUS_TOOL": ("devorbit.tools.builtin", "TASK_STATUS_TOOL"),
    "ALL_BUILTIN_TOOLS": ("devorbit.tools.builtin", "ALL_BUILTIN_TOOLS"),
    # Resources
    "Messages": ("devorbit.resources.messages", "Messages"),
    "AsyncMessages": ("devorbit.resources.messages", "AsyncMessages"),
    "MessageStream": ("devorbit.resources.streams", "MessageStream"),
    "AsyncMessageStream": ("devorbit.resources.streams", "AsyncMessageStream"),
}

# Cache for lazy imports
_IMPORT_CACHE: dict[str, Any] = {}


def __getattr__(name: str) -> Any:
    """Lazy import implementation."""
    if name in _IMPORT_CACHE:
        return _IMPORT_CACHE[name]

    if name in _LAZY_IMPORTS:
        module_path, attr_name = _LAZY_IMPORTS[name]
        module = importlib.import_module(module_path)
        value = getattr(module, attr_name)
        _IMPORT_CACHE[name] = value
        return value

    raise AttributeError(f"module 'devorbit' has no attribute '{name}'")


def __dir__() -> list[str]:
    """List available attributes."""
    return list(__all__) + list(_LAZY_IMPORTS.keys())


# Type hints for IDE support (only loaded during type checking)
if TYPE_CHECKING:
    from .core.beta import AsyncBeta, Beta
    from .core.client import AsyncDevorbit, Devorbit
    from .core.config import DevorbitConfig, load_config, read_config, save_config, update_config
    from .core.errors import (
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
    from .core.hooks import (
        Hook,
        HookContext,
        HookRegistry,
        HookType,
        PythonHookHandler,
        execute_hook,
        execute_hooks,
        get_registry,
        hook,
        register_hook,
        unregister_hook,
    )
    from .core.models import (
        MessageResponse,
        TextBlock,
        ThinkingBlock,
        ToolUseBlock,
        Usage,
    )
    from .core.tool_helpers import beta_tool
    from .core.types import (
        ContentBlock,
        ImageContent,
        Message,
        ProviderType,
        TextContent,
        Tool,
        ToolChoice,
    )
    from .tools.bash import bash
    from .tools.file import edit_file, read_file, write_file
    from .tools.search import glob_files, grep_code
