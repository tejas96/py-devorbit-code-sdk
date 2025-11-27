"""File commands: cat, init."""

from __future__ import annotations

from pathlib import Path

from ..core.commands import CommandCategory, CommandContext, CommandResult, command


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

