"""Built-in tool definitions for agent capabilities.

This module provides pre-configured tools similar to Claude's beta tools:
- Computer use tool
- Bash tool
- Text editor tool
"""

from typing import Any


# ============================================================================
# Computer Use Tool
# ============================================================================


def create_computer_use_tool(
    display_width_px: int = 1024,
    display_height_px: int = 768,
    display_number: int = 1,
) -> dict[str, Any]:
    """Create a computer use tool for controlling computer interfaces.

    Args:
        display_width_px: Display width in pixels
        display_height_px: Display height in pixels
        display_number: Display number

    Returns:
        Computer use tool definition
    """
    return {
        "type": "computer_20241022",
        "name": "computer",
        "display_width_px": display_width_px,
        "display_height_px": display_height_px,
        "display_number": display_number,
    }


# ============================================================================
# Bash Tool
# ============================================================================


def create_bash_tool() -> dict[str, Any]:
    """Create a bash tool for executing shell commands.

    Returns:
        Bash tool definition
    """
    return {
        "type": "bash_20241022",
        "name": "bash",
    }


# ============================================================================
# Text Editor Tool
# ============================================================================


def create_text_editor_tool() -> dict[str, Any]:
    """Create a text editor tool for file manipulation.

    Returns:
        Text editor tool definition
    """
    return {
        "type": "text_editor_20241022",
        "name": "str_replace_editor",
    }


# ============================================================================
# Helper Functions
# ============================================================================


def get_all_builtin_tools(
    include_computer: bool = False,
    include_bash: bool = True,
    include_editor: bool = True,
    display_width_px: int = 1024,
    display_height_px: int = 768,
) -> list[dict[str, Any]]:
    """Get all built-in tools.

    Args:
        include_computer: Include computer use tool
        include_bash: Include bash tool
        include_editor: Include text editor tool
        display_width_px: Display width for computer use
        display_height_px: Display height for computer use

    Returns:
        List of built-in tool definitions
    """
    tools = []

    if include_computer:
        tools.append(
            create_computer_use_tool(
                display_width_px=display_width_px,
                display_height_px=display_height_px,
            )
        )

    if include_bash:
        tools.append(create_bash_tool())

    if include_editor:
        tools.append(create_text_editor_tool())

    return tools


# ============================================================================
# Tool Constants
# ============================================================================

COMPUTER_USE_TOOL = create_computer_use_tool()
BASH_TOOL = create_bash_tool()
TEXT_EDITOR_TOOL = create_text_editor_tool()
