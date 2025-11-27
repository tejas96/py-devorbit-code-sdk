"""Slash command system for Devorbit SDK.

This module provides a flexible slash command framework similar to Claude Code:
- Load custom commands from .devorbit/commands/ or .claude/commands/
- Parse command definitions from markdown files
- Execute commands with arguments
- Support for command aliases and descriptions
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devorbit.core.tool_helpers import beta_tool


# ============================================================================
# Command Data Classes
# ============================================================================


@dataclass
class Command:
    """Slash command definition.

    Attributes:
        name: Command name (without /)
        description: Command description
        content: Command content/prompt
        aliases: Alternative names for the command
        file_path: Source file path (if loaded from file)
    """

    name: str
    description: str
    content: str
    aliases: list[str] | None = None
    file_path: str | None = None

    def matches(self, name: str) -> bool:
        """Check if command matches given name or alias."""
        if name == self.name:
            return True
        return bool(self.aliases and name in self.aliases)


# ============================================================================
# Command Registry
# ============================================================================


class CommandRegistry:
    """Registry for managing slash commands."""

    def __init__(self) -> None:
        """Initialize command registry."""
        self._commands: dict[str, Command] = {}

    def register(self, command: Command) -> None:
        """Register a command.

        Args:
            command: Command to register
        """
        self._commands[command.name] = command

        # Register aliases
        if command.aliases:
            for alias in command.aliases:
                self._commands[alias] = command

    def get(self, name: str) -> Command | None:
        """Get command by name or alias.

        Args:
            name: Command name or alias

        Returns:
            Command if found, None otherwise
        """
        return self._commands.get(name)

    def list_commands(self) -> list[Command]:
        """List all registered commands (deduplicated).

        Returns:
            List of unique commands
        """
        seen = set()
        commands = []

        for cmd in self._commands.values():
            if cmd.name not in seen:
                seen.add(cmd.name)
                commands.append(cmd)

        return sorted(commands, key=lambda c: c.name)

    def remove(self, name: str) -> bool:
        """Remove command by name.

        Args:
            name: Command name

        Returns:
            True if removed, False if not found
        """
        if name not in self._commands:
            return False

        cmd = self._commands[name]

        # Remove main entry
        self._commands.pop(name, None)

        # Remove aliases
        if cmd.aliases:
            for alias in cmd.aliases:
                self._commands.pop(alias, None)

        return True

    def clear(self) -> None:
        """Clear all registered commands."""
        self._commands.clear()


# Global command registry
_REGISTRY = CommandRegistry()


# ============================================================================
# Command Loaders
# ============================================================================


def parse_frontmatter(content: str) -> tuple[str | None, str, str, list[str] | None] | None:
    """Extract frontmatter and content if present."""
    pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(pattern, content, re.DOTALL)
    if not match:
        return None

    raw_meta, command_content = match.groups()
    meta: dict[str, str | list[str] | None] = {"name": None, "description": "", "aliases": []}
    for line in raw_meta.splitlines():
        if ":" not in line:
            continue
        key, value = [x.strip() for x in line.split(":", 1)]
        if key == "aliases":
            aliases_str: str = value.strip("[]")
            meta["aliases"] = [a.strip("'\" ") for a in aliases_str.split(",") if a.strip()]
        else:
            meta[key] = value

    # Ensure correct types
    name: str | None = None
    if meta["name"] is not None:
        if isinstance(meta["name"], str):
            name = meta["name"]
        elif isinstance(meta["name"], list) and meta["name"]:
            name = str(meta["name"][0])

    description: str = ""
    if meta["description"] is not None:
        if isinstance(meta["description"], str):
            description = meta["description"]
        elif isinstance(meta["description"], list) and meta["description"]:
            description = str(meta["description"][0])

    aliases_list: list[str] | None = None
    if meta["aliases"] and isinstance(meta["aliases"], list):
        aliases_list = meta["aliases"]

    return (
        name,
        description,
        command_content.strip(),
        aliases_list,
    )


def parse_simple_markdown(content: str, fallback_name: str) -> tuple[str, str, str]:
    """Parse markdown without frontmatter."""
    lines = content.splitlines()
    name = fallback_name
    description = ""
    command_body = content

    for i, line in enumerate(lines):
        if line.startswith("# "):
            name = line[2:].strip()
            # Try next non-empty line as description
            for j in range(i + 1, len(lines)):
                if lines[j].strip() and not lines[j].startswith("#"):
                    description = lines[j].strip()
                    break
            command_body = "\n".join(lines[i + 1 :]).strip()
            break

    return name, description, command_body


def parse_command_file(file_path: Path) -> Command | None:
    """Parse a command file using frontmatter or simple markdown formats."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return None

    # 1. Try frontmatter
    fm = parse_frontmatter(content)
    if fm:
        name, description, body, aliases = fm
        return Command(
            name=name or file_path.stem,
            description=description,
            content=body,
            aliases=aliases,
            file_path=str(file_path.absolute()),
        )

    # 2. Fallback to markdown
    name, description, body = parse_simple_markdown(content, file_path.stem)

    return Command(
        name=name,
        description=description,
        content=body,
        aliases=None,
        file_path=str(file_path.absolute()),
    )


def load_commands_from_dir(commands_dir: Path) -> list[Command]:
    """Load all commands from a directory.

    Args:
        commands_dir: Directory containing command files

    Returns:
        List of loaded commands
    """
    if not commands_dir.exists() or not commands_dir.is_dir():
        return []

    commands = []

    # Load all .md files
    for file_path in commands_dir.glob("*.md"):
        if cmd := parse_command_file(file_path):
            commands.append(cmd)

    return commands


def load_commands(project_root: Path | None = None) -> list[Command]:
    """Load commands from standard locations.

    Searches for commands in:
    1. .devorbit/commands/
    2. .claude/commands/
    3. commands/

    Args:
        project_root: Project root directory (default: current directory)

    Returns:
        List of loaded commands
    """
    root = project_root or Path.cwd()
    commands = []

    # Check standard directories
    for dir_name in [".devorbit/commands", ".claude/commands", "commands"]:
        commands_dir = root / dir_name
        commands.extend(load_commands_from_dir(commands_dir))

    return commands


# ============================================================================
# Command Execution
# ============================================================================


def parse_command_invocation(text: str) -> tuple[str, str] | None:
    """Parse a command invocation.

    Args:
        text: Text to parse (e.g., "/review src/main.py")

    Returns:
        Tuple of (command_name, arguments) or None if not a command
    """
    text = text.strip()

    if not text.startswith("/"):
        return None

    # Remove leading /
    text = text[1:]

    # Split into command and args
    parts = text.split(None, 1)
    command_name = parts[0]
    args = parts[1] if len(parts) > 1 else ""

    return command_name, args


def execute_command(
    command_name: str,
    args: str = "",
    registry: CommandRegistry | None = None,
) -> dict[str, Any]:
    """Execute a registered command.

    Args:
        command_name: Name of command to execute
        args: Command arguments
        registry: Command registry (default: global registry)

    Returns:
        Execution result dictionary
    """
    reg = registry or _REGISTRY

    # Get command
    cmd = reg.get(command_name)

    if not cmd:
        return {
            "error": f"Command not found: {command_name}",
            "command": command_name,
        }

    # Build final content with args substituted
    content = cmd.content

    # Simple variable substitution: {args} -> actual args
    if "{args}" in content:
        content = content.replace("{args}", args)
    elif args:
        # If no {args} placeholder, append args to content
        content = f"{content}\n\n{args}"

    return {
        "success": True,
        "command": cmd.name,
        "description": cmd.description,
        "content": content,
        "args": args,
    }


# ============================================================================
# Command Tools (for agent use)
# ============================================================================


@beta_tool
def list_slash_commands(project_root: str | None = None) -> dict[str, Any]:
    """List all available slash commands.

    Args:
        project_root: Project root directory (default: current directory)

    Returns:
        Dictionary with list of available commands
    """
    try:
        root = Path(project_root) if project_root else None

        # Load commands
        commands = load_commands(root)

        # Also include registered commands
        registered_commands = _REGISTRY.list_commands()

        # Combine and deduplicate
        all_commands = {}
        for cmd in commands + registered_commands:
            if cmd.name not in all_commands:
                all_commands[cmd.name] = {
                    "name": cmd.name,
                    "description": cmd.description,
                    "aliases": cmd.aliases or [],
                    "source": cmd.file_path or "programmatic",
                }

        return {
            "success": True,
            "commands": list(all_commands.values()),
            "count": len(all_commands),
        }
    except Exception as e:
        return {
            "error": f"Failed to list commands: {e!s}",
        }


@beta_tool
def run_slash_command(
    command: str,
    args: str = "",
    project_root: str | None = None,
) -> dict[str, Any]:
    """Execute a slash command.

    Args:
        command: Command name (with or without leading /)
        args: Command arguments
        project_root: Project root directory (default: current directory)

    Returns:
        Command execution result
    """
    try:
        root = Path(project_root) if project_root else None

        # Remove leading / if present
        command_name = command.lstrip("/")

        # Load commands from files
        commands = load_commands(root)
        for cmd in commands:
            _REGISTRY.register(cmd)

        # Execute command
        return execute_command(command_name, args, _REGISTRY)

    except Exception as e:
        return {
            "error": f"Failed to execute command: {e!s}",
            "command": command,
        }


# ============================================================================
# Helper Functions
# ============================================================================


def get_all_command_tools() -> list[dict[str, Any]]:
    """Get all command tool definitions.

    Returns:
        List of command tool definitions for use with Devorbit client
    """
    return [
        list_slash_commands.tool_definition,  # type: ignore[attr-defined]
        run_slash_command.tool_definition,  # type: ignore[attr-defined]
    ]


def register_command(
    name: str,
    content: str,
    description: str = "",
    aliases: list[str] | None = None,
) -> None:
    """Register a command programmatically.

    Args:
        name: Command name
        content: Command content/prompt
        description: Command description
        aliases: Alternative names
    """
    cmd = Command(
        name=name,
        description=description,
        content=content,
        aliases=aliases,
    )
    _REGISTRY.register(cmd)


# Export command classes and functions
__all__ = [
    "Command",
    "CommandRegistry",
    "execute_command",
    "get_all_command_tools",
    "list_slash_commands",
    "load_commands",
    "load_commands_from_dir",
    "parse_command_file",
    "parse_command_invocation",
    "register_command",
    "run_slash_command",
]
