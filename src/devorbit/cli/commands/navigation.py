"""Navigation commands: cd, pwd, ls."""

from __future__ import annotations

from pathlib import Path

from ..core.commands import CommandCategory, CommandContext, CommandResult, command


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
