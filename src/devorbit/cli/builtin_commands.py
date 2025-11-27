"""Built-in CLI commands for Devorbit.

This module registers all built-in slash commands using the Command Pattern.
Commands are automatically registered with the global registry when imported.

Usage:
    # Import to register all built-in commands
    import devorbit.cli.builtin_commands  # noqa: F401
"""

from __future__ import annotations

from pathlib import Path

from .core.commands import CommandCategory, CommandContext, CommandResult, command


# =============================================================================
# System Commands
# =============================================================================


@command(
    name="help",
    description="Show help information and available commands",
    aliases=["h", "?"],
    category=CommandCategory.SYSTEM,
    usage="[command]",
    examples=["/help", "/help cd", "/help model"],
)
def cmd_help(ctx: CommandContext) -> CommandResult:
    """Display help information.

    Shows all available commands or detailed help for a specific command.
    """
    from .core.commands import get_command_registry

    registry = get_command_registry()

    # If a specific command is requested
    if ctx.args:
        cmd_name = ctx.args[0].lower().lstrip("/")
        cmd_def = registry.get(cmd_name)
        if cmd_def:
            ctx.print(cmd_def.get_help())
            return CommandResult.ok()
        return CommandResult.error(f"Unknown command: /{cmd_name}")

    # Show all commands grouped by category
    help_text = """
Available Commands:
"""
    commands_by_category = registry.list_by_category()

    category_names = {
        CommandCategory.SYSTEM: "System",
        CommandCategory.NAVIGATION: "Navigation",
        CommandCategory.SESSION: "Session & Permissions",
        CommandCategory.MODEL: "Model",
        CommandCategory.MODE: "Mode",
        CommandCategory.HISTORY: "History",
        CommandCategory.DEBUG: "Debug",
        CommandCategory.FILE: "File",
        CommandCategory.CUSTOM: "Custom",
    }

    for category, commands in sorted(commands_by_category.items(), key=lambda x: x[0].value):
        if commands:
            help_text += f"\n  {category_names.get(category, category.value)}:\n"
            for cmd in commands:
                alias_str = ""
                if cmd.aliases:
                    alias_str = f" ({', '.join('/' + a for a in cmd.aliases)})"
                help_text += f"    /{cmd.name}{alias_str} - {cmd.description}\n"

    help_text += f"""
Input Features:
    - Use @file.py to attach files to your message
    - Use @**/*.py to attach files matching glob patterns
    - Tab for autocomplete (commands, files, models)
    - Ctrl+Enter to submit (multi-line mode)
    - Ctrl+R to search command history

System Information:
    - Provider: {ctx.provider}
    - Model: {ctx.model or "(default)"}
    - Working Dir: {ctx.working_dir}
    - Messages: {ctx.message_count}

Tips:
    - Use Ctrl+D or /exit to quit
    - Use Ctrl+C to cancel current operation
    - Commands starting with / are system commands
    - Everything else is sent to the LLM
"""
    ctx.print(help_text)
    return CommandResult.ok()


@command(
    name="exit",
    description="Exit the REPL",
    aliases=["quit", "q"],
    category=CommandCategory.SYSTEM,
)
def cmd_exit(ctx: CommandContext) -> CommandResult:
    """Exit the REPL."""
    ctx.session.is_running = False
    return CommandResult.exit()


@command(
    name="version",
    description="Show Devorbit version",
    aliases=["v"],
    category=CommandCategory.SYSTEM,
)
def cmd_version(ctx: CommandContext) -> CommandResult:
    """Show the current Devorbit version."""
    try:
        from devorbit import __version__

        ctx.print(f"Devorbit v{__version__}")
    except ImportError:
        ctx.print("Devorbit (version unknown)")
    return CommandResult.ok()


# =============================================================================
# Navigation Commands
# =============================================================================


@command(
    name="cd",
    description="Change working directory",
    category=CommandCategory.NAVIGATION,
    usage="<path>",
    examples=["/cd ..", "/cd ~/projects", "/cd src"],
)
def cmd_cd(ctx: CommandContext) -> CommandResult:
    """Change the working directory."""
    if not ctx.args:
        return CommandResult.error("Usage: /cd <path>")

    new_path = Path(ctx.args[0]).expanduser()

    # Handle relative paths
    if not new_path.is_absolute():
        new_path = ctx.working_dir / new_path

    new_path = new_path.resolve()

    if not new_path.exists():
        return CommandResult.error(f"Directory not found: {new_path}")

    if not new_path.is_dir():
        return CommandResult.error(f"Not a directory: {new_path}")

    ctx.session.working_dir = new_path
    ctx.print_success(f"Changed working directory to: {new_path}")
    return CommandResult.ok()


@command(
    name="pwd",
    description="Print working directory",
    category=CommandCategory.NAVIGATION,
)
def cmd_pwd(ctx: CommandContext) -> CommandResult:
    """Print the current working directory."""
    ctx.print(str(ctx.working_dir))
    return CommandResult.ok()


@command(
    name="ls",
    description="List files in directory",
    aliases=["dir"],
    category=CommandCategory.NAVIGATION,
    usage="[path]",
    examples=["/ls", "/ls src", "/ls -a"],
)
def cmd_ls(ctx: CommandContext) -> CommandResult:
    """List files in the current or specified directory."""
    path = ctx.working_dir
    show_hidden = False

    for arg in ctx.args:
        if arg in ("-a", "--all"):
            show_hidden = True
        elif not arg.startswith("-"):
            path = Path(arg).expanduser()
            if not path.is_absolute():
                path = ctx.working_dir / path
            path = path.resolve()

    if not path.exists():
        return CommandResult.error(f"Directory not found: {path}")

    if not path.is_dir():
        return CommandResult.error(f"Not a directory: {path}")

    try:
        entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        lines = []

        for entry in entries:
            if not show_hidden and entry.name.startswith("."):
                continue

            if entry.is_dir():
                lines.append(f"  📁 {entry.name}/")
            else:
                lines.append(f"  📄 {entry.name}")

        if lines:
            ctx.print("\n".join(lines))
        else:
            ctx.print_info("(empty directory)")

        return CommandResult.ok()
    except PermissionError:
        return CommandResult.error(f"Permission denied: {path}")


# =============================================================================
# Session Commands
# =============================================================================


@command(
    name="clear",
    description="Clear conversation history",
    aliases=["cls"],
    category=CommandCategory.SESSION,
)
def cmd_clear(ctx: CommandContext) -> CommandResult:
    """Clear the conversation history."""
    ctx.session.clear_history()
    ctx.print_success("Conversation history cleared")
    return CommandResult.ok()


@command(
    name="status",
    description="Show current session status",
    aliases=["info"],
    category=CommandCategory.SESSION,
)
def cmd_status(ctx: CommandContext) -> CommandResult:
    """Show the current session status."""
    status = f"""
Session Status:
    Provider: {ctx.provider}
    Model: {ctx.model or "(default)"}
    Working Directory: {ctx.working_dir}
    Messages: {ctx.message_count}
    Planning Mode: {"Enabled" if ctx.session.planning_mode else "Disabled"}
    Debug Mode: {"Enabled" if ctx.debug else "Disabled"}
    """
    ctx.print(status)
    return CommandResult.ok()


@command(
    name="history",
    description="Show conversation history",
    aliases=["hist"],
    category=CommandCategory.HISTORY,
    usage="[count]",
    examples=["/history", "/history 5"],
)
def cmd_history(ctx: CommandContext) -> CommandResult:
    """Show the conversation history."""
    messages = ctx.session.messages

    if not messages:
        ctx.print_info("No conversation history")
        return CommandResult.ok()

    # Parse optional count argument
    count = len(messages)
    if ctx.args:
        try:
            count = min(int(ctx.args[0]), len(messages))
        except ValueError:
            return CommandResult.error("Invalid count argument")

    ctx.print("\nConversation History:\n")
    for i, msg in enumerate(messages[-count:], 1):
        role = msg["role"]
        content = msg["content"]

        if isinstance(content, str):
            preview = content[:100] + "..." if len(content) > 100 else content
        else:
            preview = str(content)[:100]

        ctx.print(f"  {i}. [{role}] {preview}")

    ctx.print(f"\nShowing {min(count, len(messages))} of {len(messages)} messages")
    return CommandResult.ok()


# =============================================================================
# Model Commands
# =============================================================================


@command(
    name="model",
    description="Show or change the current model",
    aliases=["m"],
    category=CommandCategory.MODEL,
    usage="[model_name]",
    examples=["/model", "/model gpt-4o", "/model claude-sonnet-4-5"],
)
def cmd_model(ctx: CommandContext) -> CommandResult:
    """Show or change the current model."""
    if not ctx.args:
        ctx.print(f"Current model: {ctx.model or '(default)'}")
        return CommandResult.ok()

    new_model = ctx.args[0]
    ctx.session.model = new_model
    ctx.print_success(f"Model changed to: {new_model}")
    return CommandResult.ok()


@command(
    name="provider",
    description="Show current provider",
    category=CommandCategory.MODEL,
)
def cmd_provider(ctx: CommandContext) -> CommandResult:
    """Show the current provider."""
    ctx.print(f"Current provider: {ctx.provider}")
    ctx.print_info("Note: Provider cannot be changed during session")
    return CommandResult.ok()


# =============================================================================
# Mode Commands
# =============================================================================


@command(
    name="planning",
    description="Toggle planning mode",
    aliases=["plan"],
    category=CommandCategory.MODE,
)
def cmd_planning(ctx: CommandContext) -> CommandResult:
    """Toggle planning mode."""
    ctx.session.planning_mode = not ctx.session.planning_mode
    status = "enabled" if ctx.session.planning_mode else "disabled"
    ctx.print_success(f"Planning mode {status}")

    if ctx.session.planning_mode:
        ctx.print_info("The agent will present plans for approval before executing changes")

    return CommandResult.ok()


@command(
    name="multiline",
    description="Toggle multi-line input mode",
    aliases=["ml"],
    category=CommandCategory.MODE,
)
def cmd_multiline(ctx: CommandContext) -> CommandResult:
    """Toggle multi-line input mode.

    Note: This returns a special result that the REPL handles.
    """
    # This is handled specially by the REPL
    return CommandResult.ok(
        message="toggle_multiline",
        data={"action": "toggle_multiline"},
    )


# =============================================================================
# Debug Commands
# =============================================================================


@command(
    name="debug",
    description="Toggle debug mode",
    category=CommandCategory.DEBUG,
)
def cmd_debug(ctx: CommandContext) -> CommandResult:
    """Toggle debug mode."""
    ctx.session.debug = not ctx.session.debug
    status = "enabled" if ctx.session.debug else "disabled"
    ctx.print_success(f"Debug mode {status}")
    return CommandResult.ok()


@command(
    name="tokens",
    description="Show token usage statistics",
    category=CommandCategory.DEBUG,
)
def cmd_tokens(ctx: CommandContext) -> CommandResult:
    """Show token usage statistics."""
    # This would require tracking token usage in the session
    ctx.print_info("Token usage tracking not yet implemented")
    return CommandResult.ok()


# =============================================================================
# File Commands
# =============================================================================


@command(
    name="cat",
    description="Display file contents",
    category=CommandCategory.FILE,
    usage="<file>",
    examples=["/cat README.md", "/cat src/main.py"],
)
def cmd_cat(ctx: CommandContext) -> CommandResult:
    """Display the contents of a file."""
    if not ctx.args:
        return CommandResult.error("Usage: /cat <file>")

    file_path = Path(ctx.args[0]).expanduser()
    if not file_path.is_absolute():
        file_path = ctx.working_dir / file_path
    file_path = file_path.resolve()

    if not file_path.exists():
        return CommandResult.error(f"File not found: {file_path}")

    if not file_path.is_file():
        return CommandResult.error(f"Not a file: {file_path}")

    try:
        content = file_path.read_text(encoding="utf-8")
        ctx.print(content)
        return CommandResult.ok()
    except PermissionError:
        return CommandResult.error(f"Permission denied: {file_path}")
    except UnicodeDecodeError:
        return CommandResult.error(f"Cannot read binary file: {file_path}")


@command(
    name="init",
    description="Initialize DEVORBIT.md project file",
    category=CommandCategory.FILE,
)
def cmd_init(ctx: CommandContext) -> CommandResult:
    """Initialize a DEVORBIT.md project file."""
    devorbit_file = ctx.working_dir / "DEVORBIT.md"

    if devorbit_file.exists():
        ctx.print_warning("DEVORBIT.md already exists in this directory")
        return CommandResult.ok()

    template = """# Project Instructions for Devorbit

## Project Overview
<!-- Describe your project here -->

## Key Files
<!-- List important files and their purposes -->

## Conventions
<!-- Describe coding conventions and patterns to follow -->

## Common Tasks
<!-- Describe common tasks and how to accomplish them -->

## Notes
<!-- Any additional notes for the AI assistant -->
"""

    try:
        devorbit_file.write_text(template, encoding="utf-8")
        ctx.print_success(f"Created {devorbit_file}")
        ctx.print_info("Edit this file to provide project-specific instructions")
        return CommandResult.ok()
    except PermissionError:
        return CommandResult.error(f"Permission denied: {devorbit_file}")


# =============================================================================
# Permission Commands
# =============================================================================


@command(
    name="permissions",
    description="Show or manage permission rules",
    aliases=["perms", "perm"],
    category=CommandCategory.SESSION,
    usage="[list|add|remove|clear|audit]",
    examples=[
        "/permissions",
        "/permissions list",
        "/permissions add *.py allow write_file",
        "/permissions remove *.py",
        "/permissions audit",
    ],
)
def cmd_permissions(ctx: CommandContext) -> CommandResult:
    """Manage permission rules for tool execution.

    Subcommands:
        list - Show all active permission rules
        add <pattern> <level> [tool] - Add a permission rule
        remove <pattern> [tool] - Remove a permission rule
        clear - Clear all permission rules
        audit [count] - Show permission audit log
    """
    from .core.permissions import PermissionLevel, get_permission_manager

    manager = get_permission_manager()

    if not ctx.args:
        ctx.args = ["list"]

    subcommand = ctx.args[0].lower()

    if subcommand == "list":
        rules = manager.list_rules()
        if not rules:
            ctx.print_info("No permission rules configured")
            ctx.print_info("Use /permissions add <pattern> <level> [tool] to add rules")
            return CommandResult.ok()

        ctx.print("\nActive Permission Rules:\n")
        for i, rule in enumerate(rules, 1):
            tool_str = f" (tool: {rule.tool})" if rule.tool else ""
            category_str = f" [category: {rule.category.value}]" if rule.category else ""
            ctx.print(f"  {i}. {rule.pattern} → {rule.level.name}{tool_str}{category_str}")
            if rule.reason:
                ctx.print(f"      Reason: {rule.reason}")

        return CommandResult.ok()

    if subcommand == "add":
        if len(ctx.args) < 3:
            return CommandResult.error(
                "Usage: /permissions add <pattern> <level> [tool]\n"
                "Levels: ALLOW, DENY, ASK, ASK_ONCE"
            )

        pattern = ctx.args[1]
        level_name = ctx.args[2].upper()
        tool = ctx.args[3] if len(ctx.args) > 3 else None

        try:
            level = PermissionLevel[level_name]
        except KeyError:
            return CommandResult.error(
                f"Invalid level: {level_name}\n" "Valid levels: ALLOW, DENY, ASK, ASK_ONCE"
            )

        manager.add_rule(pattern=pattern, level=level, tool=tool)
        ctx.print_success(f"Added rule: {pattern} → {level.name}")
        return CommandResult.ok()

    if subcommand == "remove":
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: /permissions remove <pattern> [tool]")

        pattern = ctx.args[1]
        tool = ctx.args[2] if len(ctx.args) > 2 else None

        if manager.remove_rule(pattern, tool):
            ctx.print_success(f"Removed rule: {pattern}")
        else:
            ctx.print_warning(f"No matching rule found: {pattern}")

        return CommandResult.ok()

    if subcommand == "clear":
        manager.store.clear_rules()
        manager.clear_session()
        ctx.print_success("Cleared all permission rules and session decisions")
        return CommandResult.ok()

    if subcommand == "audit":
        limit = 20
        if len(ctx.args) > 1:
            try:
                limit = int(ctx.args[1])
            except ValueError:
                return CommandResult.error("Invalid count argument")

        entries = manager.get_audit_log(limit)
        if not entries:
            ctx.print_info("No permission audit entries")
            return CommandResult.ok()

        ctx.print(f"\nPermission Audit Log (last {len(entries)} entries):\n")
        for entry in entries:
            from datetime import datetime

            dt = datetime.fromtimestamp(entry.timestamp).strftime("%H:%M:%S")
            decision_icon = "✓" if entry.decision == PermissionLevel.ALLOW else "✗"
            ctx.print(f"  [{dt}] {decision_icon} {entry.tool_name} ({entry.decision.name})")
            if entry.rule_matched:
                ctx.print(f"           Rule: {entry.rule_matched}")

        return CommandResult.ok()

    return CommandResult.error(f"Unknown subcommand: {subcommand}")


@command(
    name="autoapprove",
    description="Toggle auto-approve for safe operations",
    aliases=["auto"],
    category=CommandCategory.MODE,
)
def cmd_autoapprove(ctx: CommandContext) -> CommandResult:
    """Toggle auto-approve mode for safe operations.

    When enabled, read and search operations are automatically approved.
    Dangerous operations always require explicit approval.
    """
    ctx.session.auto_approve_tools = not ctx.session.auto_approve_tools
    status = "enabled" if ctx.session.auto_approve_tools else "disabled"
    ctx.print_success(f"Auto-approve mode {status}")

    if ctx.session.auto_approve_tools:
        ctx.print_info("Safe operations (read, search) will be auto-approved")
        ctx.print_info("Dangerous operations still require explicit approval")

    return CommandResult.ok()


# Function to ensure all commands are registered
def register_builtin_commands() -> None:
    """Register all built-in commands.

    This function is called automatically when the module is imported,
    but can also be called explicitly to ensure registration.
    """
    # All commands are registered via decorators when this module loads
    pass


__all__ = ["register_builtin_commands"]
