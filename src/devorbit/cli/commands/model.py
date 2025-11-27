"""Model and mode commands: model, provider, planning, multiline."""

from __future__ import annotations

from ..core.commands import CommandCategory, CommandContext, CommandResult, command


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

