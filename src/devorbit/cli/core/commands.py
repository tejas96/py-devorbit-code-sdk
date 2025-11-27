"""Command Pattern implementation for Devorbit CLI.

This module provides a robust command system with:
- Command interface (Protocol) for all CLI commands
- CommandContext for passing execution context
- CommandResult for standardized return values
- CommandRegistry for command registration and lookup
- @command decorator for easy command definition
- CommandInvoker for command execution with history support

Usage:
    from devorbit.cli.core.commands import command, CommandContext, CommandResult

    @command(
        name="help",
        description="Show help information",
        aliases=["h", "?"],
        category="system"
    )
    def help_command(ctx: CommandContext, args: list[str]) -> CommandResult:
        return CommandResult.success("Help text here...")
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from pathlib import Path  # noqa: TC003 - Used at runtime in dataclass
import time
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable


if TYPE_CHECKING:
    from devorbit.cli.session import CLISession


class CommandCategory(Enum):
    """Categories for organizing commands."""

    SYSTEM = "system"
    NAVIGATION = "navigation"
    SESSION = "session"
    MODEL = "model"
    DEBUG = "debug"
    HISTORY = "history"
    MODE = "mode"
    FILE = "file"
    CUSTOM = "custom"


@dataclass
class CommandContext:
    """Context object passed to command handlers.

    Provides access to session state and utilities without
    coupling commands directly to CLISession internals.
    """

    session: CLISession
    working_dir: Path
    args: list[str]
    raw_input: str
    flags: dict[str, Any] = field(default_factory=dict)

    @property
    def provider(self) -> str:
        """Get the current provider name."""
        return self.session.provider

    @property
    def model(self) -> str | None:
        """Get the current model name."""
        return self.session.model

    @property
    def debug(self) -> bool:
        """Check if debug mode is enabled."""
        return self.session.debug

    @property
    def message_count(self) -> int:
        """Get the number of messages in history."""
        return len(self.session.messages)

    def print(self, message: str) -> None:
        """Print a message to the console."""
        self.session.print(message)

    def print_error(self, message: str) -> None:
        """Print an error message."""
        self.session.print_error(message)

    def print_success(self, message: str) -> None:
        """Print a success message."""
        self.session.print_success(message)

    def print_info(self, message: str) -> None:
        """Print an info message."""
        self.session.print_info(message)

    def print_warning(self, message: str) -> None:
        """Print a warning message."""
        self.session.print_warning(message)


@dataclass
class CommandResult:
    """Result of a command execution.

    Provides standardized return values for commands with
    support for success/failure states, messages, and metadata.
    """

    success: bool
    message: str = ""
    continue_repl: bool = True
    data: dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0

    @classmethod
    def ok(cls, message: str = "", **data: Any) -> CommandResult:
        """Create a successful result.

        Args:
            message: Success message to display
            **data: Additional data to include

        Returns:
            CommandResult with success=True
        """
        return cls(success=True, message=message, data=data)

    @classmethod
    def error(cls, message: str, **data: Any) -> CommandResult:
        """Create an error result.

        Args:
            message: Error message to display
            **data: Additional data to include

        Returns:
            CommandResult with success=False
        """
        return cls(success=False, message=message, data=data)

    @classmethod
    def exit(cls, message: str = "Goodbye! 👋") -> CommandResult:
        """Create an exit result that stops the REPL.

        Args:
            message: Exit message to display

        Returns:
            CommandResult with continue_repl=False
        """
        return cls(success=True, message=message, continue_repl=False)


@runtime_checkable
class Command(Protocol):
    """Protocol defining the interface for CLI commands.

    All commands must implement the execute method.
    """

    name: str
    description: str
    aliases: list[str]
    category: CommandCategory
    usage: str
    examples: list[str]

    def execute(self, ctx: CommandContext) -> CommandResult:
        """Execute the command.

        Args:
            ctx: Command execution context

        Returns:
            CommandResult indicating success/failure
        """
        ...

    def validate(self, ctx: CommandContext) -> tuple[bool, str]:
        """Validate command arguments before execution.

        Args:
            ctx: Command execution context

        Returns:
            Tuple of (is_valid, error_message)
        """
        ...


# Type alias for command handler functions
CommandHandler = Callable[[CommandContext], CommandResult]
CommandHandlerWithArgs = Callable[[CommandContext, list[str]], CommandResult]


@dataclass
class CommandDefinition:
    """Definition of a registered command."""

    name: str
    description: str
    handler: CommandHandler
    aliases: list[str] = field(default_factory=list)
    category: CommandCategory = CommandCategory.CUSTOM
    usage: str = ""
    examples: list[str] = field(default_factory=list)
    hidden: bool = False

    def execute(self, ctx: CommandContext) -> CommandResult:
        """Execute the command handler.

        Args:
            ctx: Command execution context

        Returns:
            CommandResult from the handler
        """
        start_time = time.perf_counter()
        result = self.handler(ctx)
        result.execution_time_ms = (time.perf_counter() - start_time) * 1000
        return result

    def get_help(self) -> str:
        """Get formatted help text for this command.

        Returns:
            Formatted help string
        """
        lines = [
            f"/{self.name} - {self.description}",
        ]

        if self.aliases:
            lines.append(f"  Aliases: {', '.join('/' + a for a in self.aliases)}")

        if self.usage:
            lines.append(f"  Usage: /{self.name} {self.usage}")

        if self.examples:
            lines.append("  Examples:")
            for example in self.examples:
                lines.append(f"    {example}")

        return "\n".join(lines)


class CommandRegistry:
    """Registry for CLI commands.

    Manages command registration, lookup, and organization.
    Supports aliases and categories for better organization.
    """

    def __init__(self) -> None:
        """Initialize the command registry."""
        self._commands: dict[str, CommandDefinition] = {}
        self._aliases: dict[str, str] = {}

    def register(
        self,
        name: str,
        handler: CommandHandler,
        description: str = "",
        aliases: list[str] | None = None,
        category: CommandCategory = CommandCategory.CUSTOM,
        usage: str = "",
        examples: list[str] | None = None,
        hidden: bool = False,
    ) -> None:
        """Register a command.

        Args:
            name: Command name (without leading /)
            handler: Function to execute the command
            description: Command description for help
            aliases: Alternative names for the command
            category: Command category for organization
            usage: Usage string (e.g., "<path>")
            examples: Example usages
            hidden: Hide from help listings

        Raises:
            ValueError: If command name already registered
        """
        name = name.lower()

        if name in self._commands or name in self._aliases:
            raise ValueError(f"Command '{name}' is already registered")

        cmd_def = CommandDefinition(
            name=name,
            description=description,
            handler=handler,
            aliases=aliases or [],
            category=category,
            usage=usage,
            examples=examples or [],
            hidden=hidden,
        )

        self._commands[name] = cmd_def

        # Register aliases
        for alias in cmd_def.aliases:
            alias_lower = alias.lower()
            if alias_lower in self._commands or alias_lower in self._aliases:
                raise ValueError(f"Alias '{alias}' conflicts with existing command")
            self._aliases[alias_lower] = name

    def get(self, name: str) -> CommandDefinition | None:
        """Get a command by name or alias.

        Args:
            name: Command name or alias

        Returns:
            CommandDefinition or None if not found
        """
        name = name.lower()

        # Check direct command
        if name in self._commands:
            return self._commands[name]

        # Check aliases
        if name in self._aliases:
            return self._commands[self._aliases[name]]

        return None

    def exists(self, name: str) -> bool:
        """Check if a command exists.

        Args:
            name: Command name or alias

        Returns:
            True if command exists
        """
        name = name.lower()
        return name in self._commands or name in self._aliases

    def list_commands(
        self,
        category: CommandCategory | None = None,
        include_hidden: bool = False,
    ) -> list[CommandDefinition]:
        """List all registered commands.

        Args:
            category: Filter by category (optional)
            include_hidden: Include hidden commands

        Returns:
            List of command definitions
        """
        commands = []
        for cmd in self._commands.values():
            if cmd.hidden and not include_hidden:
                continue
            if category is not None and cmd.category != category:
                continue
            commands.append(cmd)

        return sorted(commands, key=lambda c: c.name)

    def list_by_category(
        self, include_hidden: bool = False
    ) -> dict[CommandCategory, list[CommandDefinition]]:
        """List commands grouped by category.

        Args:
            include_hidden: Include hidden commands

        Returns:
            Dict mapping categories to command lists
        """
        result: dict[CommandCategory, list[CommandDefinition]] = {}

        for cmd in self._commands.values():
            if cmd.hidden and not include_hidden:
                continue

            if cmd.category not in result:
                result[cmd.category] = []
            result[cmd.category].append(cmd)

        # Sort commands within each category
        for _category, cmds in result.items():
            cmds.sort(key=lambda c: c.name)

        return result

    def get_completions(self, prefix: str = "") -> list[str]:
        """Get command name completions.

        Args:
            prefix: Prefix to filter by

        Returns:
            List of matching command names
        """
        prefix = prefix.lower()
        completions = []

        for name in self._commands:
            if name.startswith(prefix):
                completions.append(name)

        for alias in self._aliases:
            if alias.startswith(prefix):
                completions.append(alias)

        return sorted(set(completions))

    def unregister(self, name: str) -> bool:
        """Unregister a command.

        Args:
            name: Command name

        Returns:
            True if command was removed
        """
        name = name.lower()

        if name not in self._commands:
            return False

        cmd = self._commands[name]

        # Remove aliases
        for alias in cmd.aliases:
            self._aliases.pop(alias.lower(), None)

        # Remove command
        del self._commands[name]
        return True

    def __len__(self) -> int:
        """Return number of registered commands."""
        return len(self._commands)

    def __contains__(self, name: str) -> bool:
        """Check if command exists."""
        return self.exists(name)


# Singleton holder for global command registry
class _CommandRegistryHolder:
    """Holder class for the global command registry singleton."""

    instance: CommandRegistry | None = None


def get_command_registry() -> CommandRegistry:
    """Get the global command registry instance.

    Returns:
        Global CommandRegistry singleton
    """
    if _CommandRegistryHolder.instance is None:
        _CommandRegistryHolder.instance = CommandRegistry()
    return _CommandRegistryHolder.instance


def reset_command_registry() -> None:
    """Reset the global command registry (for testing)."""
    _CommandRegistryHolder.instance = None


def command(
    name: str,
    description: str = "",
    aliases: list[str] | None = None,
    category: CommandCategory = CommandCategory.CUSTOM,
    usage: str = "",
    examples: list[str] | None = None,
    hidden: bool = False,
    registry: CommandRegistry | None = None,
) -> Callable[[CommandHandler], CommandHandler]:
    """Decorator to register a function as a CLI command.

    Args:
        name: Command name (without leading /)
        description: Command description for help
        aliases: Alternative names for the command
        category: Command category for organization
        usage: Usage string (e.g., "<path>")
        examples: Example usages
        hidden: Hide from help listings
        registry: Registry to use (default: global)

    Returns:
        Decorator function

    Example:
        @command(
            name="help",
            description="Show help information",
            aliases=["h", "?"],
            category=CommandCategory.SYSTEM
        )
        def help_command(ctx: CommandContext) -> CommandResult:
            return CommandResult.ok("Help text...")
    """

    def decorator(func: CommandHandler) -> CommandHandler:
        @wraps(func)
        def wrapper(ctx: CommandContext) -> CommandResult:
            return func(ctx)

        # Register with specified or global registry
        reg = registry or get_command_registry()
        reg.register(
            name=name,
            handler=wrapper,
            description=description,
            aliases=aliases,
            category=category,
            usage=usage,
            examples=examples,
            hidden=hidden,
        )

        return wrapper

    return decorator


@dataclass
class CommandHistoryEntry:
    """Entry in command history."""

    command_name: str
    args: list[str]
    raw_input: str
    result: CommandResult
    timestamp: float = field(default_factory=time.time)


class CommandInvoker:
    """Executes commands and maintains history.

    Provides a single point for command execution with
    support for history tracking and potential undo/redo.
    """

    def __init__(
        self,
        registry: CommandRegistry | None = None,
        max_history: int = 100,
    ) -> None:
        """Initialize the command invoker.

        Args:
            registry: Command registry to use
            max_history: Maximum history entries to keep
        """
        self.registry = registry or get_command_registry()
        self.history: list[CommandHistoryEntry] = []
        self.max_history = max_history

    def execute(
        self,
        command_line: str,
        session: CLISession,
    ) -> CommandResult:
        """Execute a command from a command line string.

        Args:
            command_line: Full command line (with or without leading /)
            session: CLI session for context

        Returns:
            CommandResult from execution
        """
        # Strip leading / if present
        if command_line.startswith("/"):
            command_line = command_line[1:]

        # Parse command and arguments
        parts = command_line.split()
        if not parts:
            return CommandResult.error("Empty command")

        cmd_name = parts[0].lower()
        cmd_args = parts[1:]

        # Look up command
        cmd_def = self.registry.get(cmd_name)
        if cmd_def is None:
            return CommandResult.error(
                f"Unknown command: /{cmd_name}\nType /help to see available commands"
            )

        # Build context
        ctx = CommandContext(
            session=session,
            working_dir=session.working_dir,
            args=cmd_args,
            raw_input=command_line,
        )

        # Execute command
        try:
            result = cmd_def.execute(ctx)
        except Exception as e:
            result = CommandResult.error(f"Command failed: {e}")
            if session.debug:
                raise

        # Record in history
        entry = CommandHistoryEntry(
            command_name=cmd_name,
            args=cmd_args,
            raw_input=command_line,
            result=result,
        )
        self._add_to_history(entry)

        return result

    def _add_to_history(self, entry: CommandHistoryEntry) -> None:
        """Add an entry to command history.

        Args:
            entry: History entry to add
        """
        self.history.append(entry)

        # Trim history if needed
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history :]

    def get_last_result(self) -> CommandResult | None:
        """Get the result of the last executed command.

        Returns:
            Last CommandResult or None if no history
        """
        if self.history:
            return self.history[-1].result
        return None

    def get_history(self, limit: int = 10) -> list[CommandHistoryEntry]:
        """Get recent command history.

        Args:
            limit: Maximum entries to return

        Returns:
            List of recent history entries
        """
        return self.history[-limit:]

    def clear_history(self) -> None:
        """Clear command history."""
        self.history.clear()


__all__ = [
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
]
