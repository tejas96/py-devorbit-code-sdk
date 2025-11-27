"""Core infrastructure for Devorbit CLI.

This module provides the foundational patterns for the CLI:
- Registry Pattern: Central registration for tools, commands
- Decorator Pattern: Easy registration via decorators
- Command Pattern: Structured command handling with history
- Validation: Input validation and sanitization
- Context Management: Execution context and scoping
- Persistence: Session save/restore and file backup
- Concurrency: Parallel execution and rate limiting
- Permissions: Permission rules, policies, and audit logging

NOTE: Hooks, Recovery, and Subagents are now in the SDK for better reusability.
Import from `devorbit` directly for:
- Hooks: `from devorbit import HookType, HookContext, hook, register_hook`
- Recovery: `from devorbit import RetryHandler, RecoveryManager, with_retry`
- Subagents: `from devorbit import AgentTask, AgentCoordinator, TaskPriority`
"""

# Re-export SDK modules for backwards compatibility
from devorbit._agent_tools import (
    AgentCoordinator,
    AgentTask,
    TaskPriority,
)
from devorbit._agent_tools import TaskResult as AgentTaskResult
from devorbit._agent_tools import (
    TaskStatus,
)
from devorbit._hooks import (
    Hook,
    HookContext,
    HookRegistry,
    HookType,
    execute_hooks,
    hook,
    register_hook,
)
from devorbit._recovery import (
    ErrorCategory,
    ErrorClassifier,
    ErrorInfo,
    RecoveryManager,
    RecoveryStrategy,
    RetryConfig,
    RetryHandler,
    get_recovery_manager,
    reset_recovery_manager,
    with_retry,
)

from .commands import (
    Command,
    CommandCategory,
    CommandContext,
    CommandDefinition,
    CommandHandler,
    CommandHistoryEntry,
    CommandInvoker,
    CommandRegistry,
    CommandResult,
    command,
    get_command_registry,
    reset_command_registry,
)
from .concurrency import (
    RateLimiter,
    ResourceLock,
    TaskExecutor,
    TaskResult,
    get_resource_lock,
    get_task_executor,
)
from .context import (
    ContextManager,
    ExecutionContext,
    context_scope,
    current_context,
    get_context_manager,
)
from .decorators import cli_tool, register_tool
from .permissions import (
    TOOL_CATEGORIES,
    AuditLogEntry,
    PermissionDecision,
    PermissionLevel,
    PermissionManager,
    PermissionRule,
    PermissionStore,
    ToolCategory,
    get_permission_manager,
    reset_permission_manager,
)
from .persistence import BackupManager, FileCheckpoint, SessionPersistence, SessionState
from .registry import Registry, ToolRegistry
from .validation import InputValidator, sanitize_path, validate_input


__all__ = [
    # Agents/Tasks (from SDK)
    "AgentCoordinator",
    "AgentTask",
    "AgentTaskResult",
    "TaskPriority",
    "TaskStatus",
    # Commands
    "Command",
    "CommandCategory",
    "CommandContext",
    "CommandDefinition",
    "CommandHandler",
    "CommandHistoryEntry",
    "CommandInvoker",
    "CommandRegistry",
    "CommandResult",
    "command",
    "get_command_registry",
    "reset_command_registry",
    # Context
    "ContextManager",
    "ExecutionContext",
    "context_scope",
    "current_context",
    "get_context_manager",
    # Decorators
    "cli_tool",
    "register_tool",
    # Recovery (from SDK)
    "ErrorCategory",
    "ErrorClassifier",
    "ErrorInfo",
    "RecoveryManager",
    "RecoveryStrategy",
    "RetryConfig",
    "RetryHandler",
    "get_recovery_manager",
    "reset_recovery_manager",
    "with_retry",
    # Hooks (from SDK)
    "Hook",
    "HookContext",
    "HookRegistry",
    "HookType",
    "execute_hooks",
    "hook",
    "register_hook",
    # Validation
    "InputValidator",
    "sanitize_path",
    "validate_input",
    # Persistence
    "BackupManager",
    "FileCheckpoint",
    "SessionPersistence",
    "SessionState",
    # Permissions
    "AuditLogEntry",
    "PermissionDecision",
    "PermissionLevel",
    "PermissionManager",
    "PermissionRule",
    "PermissionStore",
    "ToolCategory",
    "TOOL_CATEGORIES",
    "get_permission_manager",
    "reset_permission_manager",
    # Concurrency
    "RateLimiter",
    "ResourceLock",
    "TaskExecutor",
    "TaskResult",
    "get_resource_lock",
    "get_task_executor",
    # Registry
    "Registry",
    "ToolRegistry",
]
