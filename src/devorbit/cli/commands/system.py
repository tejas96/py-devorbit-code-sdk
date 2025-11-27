"""System commands: help, exit, version."""

from __future__ import annotations

from ..core.commands import CommandCategory, CommandContext, CommandResult, command


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
    from ..core.commands import get_command_registry

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

