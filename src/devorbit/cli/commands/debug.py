"""Debug commands: debug, tokens, hooks, recovery."""

from __future__ import annotations

from ..core.commands import CommandCategory, CommandContext, CommandResult, command


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


@command(
    name="hooks",
    description="Show registered hooks and their status",
    category=CommandCategory.DEBUG,
    usage="[list|enable|disable]",
    examples=["/hooks", "/hooks list", "/hooks disable", "/hooks enable"],
)
def cmd_hooks(ctx: CommandContext) -> CommandResult:
    """Display and manage registered hooks.

    Hooks are triggered automatically during operations like file writes,
    tool calls, and git operations.

    Subcommands:
        list    - Show all registered hooks (default)
        enable  - Enable all hooks
        disable - Disable all hooks
    """
    from devorbit.core.hooks import get_registry

    registry = get_registry()
    subcommand = ctx.args[0].lower() if ctx.args else "list"

    if subcommand == "list":
        hooks = registry.list_all()

        if not hooks:
            ctx.print_info("No hooks registered")
            ctx.print("")
            ctx.print("To add hooks, create a .devorbit.json file:")
            ctx.print(
                """
{
  "hooks": {
    "post_file_write": [
      {"name": "format", "command": "black {file_path}", "enabled": true}
    ]
  }
}
"""
            )
            return CommandResult.ok()

        ctx.print(f"\nRegistered Hooks ({len(hooks)}):\n")
        ctx.print(f"  Registry Status: {'ENABLED' if registry.is_enabled() else 'DISABLED'}\n")

        for hook in hooks:
            status_icon = "✓" if hook["enabled"] else "✗"
            hook_type = f"[{hook['type']}]"
            priority = f"p={hook['priority']}"
            kind = "🐍 Python" if hook["is_python"] else "🐚 Shell"

            ctx.print(f"  {status_icon} {hook['name']} {hook_type} ({priority}) - {kind}")
            if hook.get("command"):
                ctx.print(f"      Command: {hook['command']}")

        return CommandResult.ok()

    if subcommand == "enable":
        registry.enable()
        ctx.print_success("Hooks enabled")
        return CommandResult.ok()

    if subcommand == "disable":
        registry.disable()
        ctx.print_warning("Hooks disabled")
        return CommandResult.ok()

    return CommandResult.error(f"Unknown subcommand: {subcommand}")


@command(
    name="recovery",
    description="Show error recovery settings",
    category=CommandCategory.DEBUG,
)
def cmd_recovery(ctx: CommandContext) -> CommandResult:
    """Display error recovery settings.

    The SDK automatically retries transient errors (timeouts, rate limits)
    with exponential backoff.
    """
    from devorbit.core.recovery import RecoveryStrategy

    ctx.print("\nError Recovery System (Phase 5):\n")
    ctx.print("  The SDK automatically handles transient errors:\n")
    ctx.print("  Error Classifications:")
    ctx.print(f"    • TRANSIENT  → {RecoveryStrategy.RETRY_WITH_BACKOFF.value}")
    ctx.print(f"    • PERMANENT  → {RecoveryStrategy.ABORT.value}")
    ctx.print(f"    • RESOURCE   → {RecoveryStrategy.ASK_USER.value}")
    ctx.print(f"    • UNKNOWN    → {RecoveryStrategy.ASK_USER.value}")
    ctx.print("")
    ctx.print("  Transient Error Patterns (auto-retry):")
    ctx.print("    • Connection timeout, network errors")
    ctx.print("    • Rate limits (429, 503)")
    ctx.print("    • Service temporarily unavailable")
    ctx.print("")
    ctx.print("  Retry Settings:")
    ctx.print("    • Max retries: 3")
    ctx.print("    • Initial delay: 1.0s")
    ctx.print("    • Backoff factor: 2.0x")
    ctx.print("")

    return CommandResult.ok()
