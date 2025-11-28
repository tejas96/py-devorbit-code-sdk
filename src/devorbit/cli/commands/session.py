"""Session commands: clear, status, history, permissions, autoapprove."""

from __future__ import annotations

from ..core.commands import CommandCategory, CommandContext, CommandResult, command


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
    from ..core.permissions import PermissionLevel, get_permission_manager

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
                f"Invalid level: {level_name}\nValid levels: ALLOW, DENY, ASK, ASK_ONCE"
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
