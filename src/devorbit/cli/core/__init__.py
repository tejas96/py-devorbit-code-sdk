"""Core infrastructure for Devorbit CLI.

This module provides the foundational patterns for the CLI:
- Registry Pattern: Central registration for tools, commands, hooks
- Decorator Pattern: Easy registration via decorators
- Command Pattern: Structured command handling with history
- Validation: Input validation and sanitization
- Context Management: Execution context and scoping
- Persistence: Session save/restore and file backup
- Concurrency: Parallel execution and rate limiting
- Permissions: Permission rules, policies, and audit logging
"""

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
    # Registry
    "Registry",
    "ToolRegistry",
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
    # Persistence
    "BackupManager",
    "FileCheckpoint",
    "SessionPersistence",
    "SessionState",
    # Concurrency
    "RateLimiter",
    "ResourceLock",
    "TaskExecutor",
    "TaskResult",
    "get_resource_lock",
    "get_task_executor",
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
    # Decorators
    "cli_tool",
    "register_tool",
    # Validation
    "InputValidator",
    "sanitize_path",
    "validate_input",
]
