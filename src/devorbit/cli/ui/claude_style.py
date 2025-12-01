"""Claude Code-style UI components.

This module implements UI components matching Claude Code CLI:
- Arrow-key selection prompts (↑/↓ + Enter) in unified panel
- Single unified tool execution display
- Status dot color changes (gray → green/red)
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from questionary import Style
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text


if TYPE_CHECKING:
    from collections.abc import Callable


# Custom questionary style matching Claude Code
CLAUDE_STYLE = Style(
    [
        ("qmark", "fg:cyan bold"),
        ("question", "fg:white bold"),
        ("answer", "fg:cyan bold"),
        ("pointer", "fg:cyan bold"),
        ("highlighted", "fg:cyan bold"),
        ("selected", "fg:cyan"),
        ("instruction", "fg:#858585 italic"),
    ]
)


class ToolStatus(Enum):
    """Status indicators for tool execution."""

    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class PermissionChoice:
    """Result of permission prompt selection."""

    value: str
    option_index: int


class ClaudeStylePrompt:
    """Claude Code-style permission prompt with arrow key navigation.

    Uses Rich for panel display + questionary for reliable arrow key selection.
    """

    def __init__(self, console: Console | None = None):
        """Initialize the prompt.

        Args:
            console: Rich console instance
        """
        self.console = console or Console()
        self.prompt_session = PromptSession()

    def show_permission_prompt(
        self,
        tool_name: str,
        command: str,
        description: str,
        working_dir: str,
        is_dangerous: bool = False,
    ) -> PermissionChoice | None:
        """Show Claude Code-style permission prompt with embedded options.

        The panel is shown with transient=True, so it auto-clears when done.

        Args:
            tool_name: Name of the tool (e.g., "Bash")
            command: The command to execute
            description: Description of what the command does
            working_dir: Current working directory
            is_dangerous: Whether this is a dangerous operation

        Returns:
            PermissionChoice if selected, None if cancelled
        """
        tool_display = f"{tool_name} command" if tool_name.lower() == "bash" else tool_name
        color = "red" if is_dangerous else "cyan"

        # Prepare choices
        cmd_short = command[:40] + "..." if len(command) > 40 else command
        dir_short = working_dir if len(working_dir) <= 35 else "..." + working_dir[-32:]

        choices = [
            ("yes", "Yes"),
            ("yes_always", f"Yes, and don't ask again for {cmd_short} in {dir_short}"),
            ("no", "No, and tell Claude what to do differently"),
        ]

        selected_index = [0]
        live_display = [None]

        # Key bindings for arrow navigation
        kb = KeyBindings()

        @kb.add(Keys.Up)
        def move_up(event):
            selected_index[0] = (selected_index[0] - 1) % len(choices)
            if live_display[0]:
                update_display()

        @kb.add(Keys.Down)
        def move_down(event):
            selected_index[0] = (selected_index[0] + 1) % len(choices)
            if live_display[0]:
                update_display()

        @kb.add(Keys.Enter)
        def select(event):
            event.app.exit(result=choices[selected_index[0]][0])

        @kb.add("c-c")
        def cancel(event):
            event.app.exit(result=None)

        def create_panel_content() -> Text:
            """Create panel content with embedded options."""
            content = Text()
            content.append(f"{tool_display}\n", style=f"bold {color}")
            content.append(f"  {command}\n", style="white")
            if description:
                content.append(f"  {description}\n", style="dim")

            content.append("\n")
            content.append("Do you want to proceed?\n", style="bold white")

            # Add choices with pointer
            for i, (value, label) in enumerate(choices):
                if i == selected_index[0]:
                    content.append("  ❯ ", style="cyan bold")
                    content.append(label, style="cyan bold")
                else:
                    content.append("    ", style="dim")
                    content.append(label, style="dim")
                content.append("\n")

            content.append("\n")
            content.append("(↑/↓ to select, Enter to confirm)", style="dim italic")

            return content

        def update_display():
            """Update the live display with new selection."""
            if live_display[0]:
                panel = Panel(
                    create_panel_content(),
                    border_style=color,
                    padding=(0, 1),
                )
                live_display[0].update(panel)

        # Initial panel
        panel = Panel(
            create_panel_content(),
            border_style=color,
            padding=(0, 1),
        )

        # Show panel with transient=True - it will auto-clear when Live context exits
        with Live(panel, console=self.console, refresh_per_second=10, transient=True) as live:
            live_display[0] = live
            try:
                result = self.prompt_session.prompt("", key_bindings=kb)

                if result is None:
                    return None

                # Find the selected index
                for i, (value, _) in enumerate(choices):
                    if value == result:
                        return PermissionChoice(value=result, option_index=i)

                return PermissionChoice(value=result, option_index=0)

            except (KeyboardInterrupt, EOFError):
                return None
            # Panel auto-clears here because transient=True


class ToolExecutionDisplay:
    """Claude Code-style tool execution display.

    Features:
    - Status dot (○ gray running, ● green success, ● red failed)
    - Single line status that shows final result
    - Truncated output with expand hint
    """

    # Status dot characters
    DOT_RUNNING = "●"  # Empty circle (gray)
    DOT_SUCCESS = "●"  # Filled circle (green)
    DOT_FAILED = "●"  # Filled circle (red)

    def __init__(self, console: Console | None = None):
        """Initialize the display.

        Args:
            console: Rich console instance
        """
        self.console = console or Console()
        self._start_time: float | None = None
        self._tool_name: str = ""
        self._command: str = ""
        self._live: Live | None = None

    def show_tool_start(
        self,
        tool_name: str,
        command: str,
        tool_id: str | None = None,
    ) -> str:
        """Show tool execution starting (running status).

        Uses Rich Live for in-place updates.

        Args:
            tool_name: Name of the tool
            command: Command being executed
            tool_id: Unique ID for this execution

        Returns:
            Tool execution ID
        """
        tool_id = tool_id or f"{tool_name}-{time.time()}"
        self._start_time = time.time()
        self._tool_name = tool_name
        self._command = command

        # Create running status display
        display = Text()
        display.append(f"{self.DOT_RUNNING} ", style="dim")
        display.append(f"{tool_name}({command})\n", style="white")
        display.append("  └─ Running...", style="white")
        self.console.print(display)

        return tool_id

    def show_tool_complete(
        self,
        tool_name: str,
        command: str,
        success: bool,
        output: str | None = None,
        error: str | None = None,
        tool_id: str | None = None,
    ) -> None:
        """Show tool execution complete.

        Stops the Live display and prints final state.

        Args:
            tool_name: Name of the tool
            command: Command executed
            success: Whether execution succeeded
            output: Tool output
            error: Error message if failed
            tool_id: Tool execution ID
        """
        status = ToolStatus.SUCCESS if success else ToolStatus.FAILED
        final_output = output or error or ""

        # Stop Live display (clears transient content)
        if self._live:
            self._live.stop()
            self._live = None

        # Print final state
        self._print_final(status, final_output)

        # Reset state
        self._start_time = None
        self._tool_name = ""
        self._command = ""

    def show_tool_denied(self, tool_name: str, command: str) -> None:
        """Show tool was denied by user.

        Args:
            tool_name: Name of the tool
            command: Command that was denied
        """
        if self._live:
            self._live.stop()
            self._live = None

        display_cmd = command[:60] + "..." if len(command) > 60 else command
        self.console.print(f"[red]{self.DOT_FAILED}[/red] [bold]{tool_name}({display_cmd})[/bold]")
        self.console.print("  [red]└─ Denied by user[/red]")

    def _create_display(self, status: ToolStatus, output: str | None = None) -> Text:
        """Create display for given status.

        Args:
            status: Current status
            output: Output text

        Returns:
            Rich Text for display
        """
        tool_display = f"{self._tool_name}({self._command})"
        text = Text()

        if status == ToolStatus.RUNNING:
            text.append(f"{self.DOT_RUNNING} ", style="dim")
            text.append(f"{tool_display}\n", style="bold")
            text.append("  └─ Running...", style="dim cyan")
        elif status == ToolStatus.SUCCESS:
            text.append(f"{self.DOT_SUCCESS} ", style="green")
            text.append(f"{tool_display}", style="bold")
        else:  # FAILED
            text.append(f"{self.DOT_FAILED} ", style="red")
            text.append(f"{tool_display}", style="bold")

        return text

    def _print_final(self, status: ToolStatus, output: str) -> None:
        """Print final status with output.

        Args:
            status: Final status
            output: Output text
        """
        tool_display = f"{self._tool_name}({self._command})"

        if status == ToolStatus.SUCCESS:
            self.console.print(f"[green]{self.DOT_SUCCESS}[/green] [bold]{tool_display}[/bold]")
            if output:
                self._print_output(output, style="white")
            else:
                self.console.print("  [green]└─ Done[/green]")
        else:  # FAILED
            self.console.print(f"[red]{self.DOT_FAILED}[/red] [bold]{tool_display}[/bold]")
            if output:
                self._print_output(output, style="red")
            else:
                self.console.print("  [red]└─ Failed[/red]")

    def _print_output(self, output: str, style: str = "white") -> None:
        """Print output with truncation.

        Args:
            output: Output text
            style: Rich style
        """
        lines = output.strip().split("\n")
        max_lines = 8

        for i, line in enumerate(lines[:max_lines]):
            prefix = "  └─ " if i == 0 else "     "
            self.console.print(f"{prefix}[{style}]{line}[/{style}]")

        if len(lines) > max_lines:
            remaining = len(lines) - max_lines
            self.console.print(f"     [dim]... {remaining} more lines (Ctrl+O to expand)[/dim]")


class ClaudeStyleUI:
    """Main interface combining all Claude Code-style components."""

    def __init__(self, console: Console | None = None):
        """Initialize Claude-style UI.

        Args:
            console: Rich console instance
        """
        self.console = console or Console()
        self.prompt = ClaudeStylePrompt(console)
        self.tool_display = ToolExecutionDisplay(console)

        # NOTE: Permission memory is now handled by PermissionManager in core/permissions.py
        # This class only handles UI display, not permission state

    def request_permission(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        working_dir: str,
        is_dangerous: bool = False,
    ) -> tuple[bool, bool]:
        """Request permission for tool execution (UI only - no memory).

        Permission memory is handled by PermissionManager in core/permissions.py.
        This method ONLY shows the UI prompt and returns the user's choice.

        Args:
            tool_name: Name of the tool
            tool_input: Tool input parameters
            working_dir: Current working directory
            is_dangerous: Whether operation is dangerous

        Returns:
            Tuple of (approved, remember_choice)
        """
        # Get command string for display
        if tool_name.lower() == "bash":
            command = str(tool_input.get("command", str(tool_input)))
        elif tool_name in ("read_file", "write_file", "edit_file"):
            command = str(tool_input.get("file_path", str(tool_input)))
        else:
            command = str(tool_input)

        # Generate description
        description = self._get_tool_description(tool_name, tool_input)

        # Show permission prompt (memory check is done by PermissionManager BEFORE this)
        choice = self.prompt.show_permission_prompt(
            tool_name=tool_name,
            command=command,
            description=description,
            working_dir=working_dir,
            is_dangerous=is_dangerous,
        )

        if choice is None:
            return False, False

        if choice.value == "yes":
            return True, False
        if choice.value == "yes_always":
            # Return True for remember - PermissionManager will store the rule
            return True, True
        return False, False

    def execute_tool_with_display(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        executor: Callable[..., Any],
    ) -> dict[str, Any]:
        """Execute tool with Claude-style display.

        Args:
            tool_name: Name of the tool
            tool_input: Tool input parameters
            executor: Function to execute the tool

        Returns:
            Tool execution result
        """
        # Get command for display
        if tool_name.lower() == "bash":
            command = str(tool_input.get("command", str(tool_input)))
        elif tool_name in ("read_file", "write_file", "edit_file"):
            command = str(tool_input.get("file_path", str(tool_input)))
        else:
            command = str(next(iter(tool_input.values()))) if tool_input else tool_name

        try:
            # Execute tool
            result = executor(**tool_input)

            # Determine success
            success = True
            output = ""
            error: str | None = None

            if isinstance(result, dict):
                if "error" in result:
                    success = False
                    error = str(result.get("error", "Unknown error"))
                else:
                    raw_output = result.get("output", result.get("content", str(result)))
                    output = str(raw_output) if raw_output is not None else str(result)
            else:
                output = str(result)

            # Complete display (gray dot → green/red dot)
            self.tool_display.show_tool_complete(
                tool_name=tool_name,
                command=command,
                success=success,
                output=output if success else None,
                error=error,
            )

            return dict(result) if isinstance(result, dict) else {"result": result}

        except Exception as e:
            # Show failure
            self.tool_display.show_tool_complete(
                tool_name=tool_name,
                command=command,
                success=False,
                error=str(e),
            )
            return {"error": str(e)}

    def _get_tool_description(self, tool_name: str, tool_input: dict[str, Any]) -> str:
        """Generates a one-line description of the specific tool call based on inputs.

        This method replaces the static tool description with a dynamic, context-
        specific summary, ensuring a better user experience without consuming extra
        LLM tokens.
        """

        # --- File I/O Tools ---
        if tool_name == "read_file":
            file_path = tool_input.get("file_path", "a file")
            return f"Read the content of file: '{file_path}'."

        elif tool_name == "write_file":
            file_path = tool_input.get("file_path", "a file")
            return f"Create or overwrite file: '{file_path}'."

        elif tool_name == "edit_file":
            file_path = tool_input.get("file_path", "a file")
            return f"Edit content within file: '{file_path}'."

        # --- File Search Tools ---
        elif tool_name == "glob":
            pattern = tool_input.get("pattern", "a pattern")
            path = tool_input.get("path", ".")
            return f"Search for files matching '{pattern}' in '{path}'."

        elif tool_name == "grep":
            pattern = tool_input.get("pattern", "a pattern")
            path = tool_input.get("path", ".")
            return f"Search for the text pattern '{pattern}' in files in '{path}'."

        # --- Enhanced Shell/Command Tools (bash) ---
        elif tool_name == "bash":
            command = tool_input.get("command", "").strip()

            # Use lower-casing for robust command matching
            cmd_lower = command.lower()

            # 1. Common File/Directory Commands
            if cmd_lower == "pwd":
                return "Display the current working directory."
            if cmd_lower.startswith("ls"):
                return "List files and directories."
            if cmd_lower.startswith("cd"):
                path = command.split(maxsplit=1)[1] if len(command.split()) > 1 else "~"
                return f"Change directory to: {path}"
            if cmd_lower.startswith("cat"):
                path = command.split(maxsplit=1)[1] if len(command.split()) > 1 else ""
                return f"Display the content of file: {path}"
            if cmd_lower.startswith("mkdir"):
                path = command.split(maxsplit=1)[1] if len(command.split()) > 1 else ""
                return f"Create a new directory: {path}"
            if cmd_lower.startswith("touch"):
                path = command.split(maxsplit=1)[1] if len(command.split()) > 1 else ""
                return f"Create a new file: {path}"

            # 2. Common System Status Commands
            if cmd_lower in ("free -h", "free"):
                return "Check current memory usage."
            if cmd_lower.startswith("df -h"):
                return "Check current disk space usage."
            if cmd_lower.startswith("ps aux"):
                return "List all running processes."

            # 3. Dangerous or Generic Commands
            # Note: Requires access to DangerousCommandDetector patterns (see next section)
            try:
                # Assuming access to DangerousCommandDetector.DANGEROUS_PATTERNS via session/tool_approval
                detector = self.session.tool_approval.DangerousCommandDetector
                if any(re.search(p, command, re.IGNORECASE) for p in detector.DANGEROUS_PATTERNS):
                    return f"Execute potentially dangerous shell command: {command[:50]}..."
            except AttributeError:
                # Fallback if detector path is incorrect
                pass

            # 4. Final Fallback for ANY other bash command
            return f"Execute shell command: {command[:50]}..."

        # --- Fallback for uncategorized/new tools ---
        else:
            # Fallback to general tool description defined statically (if available)
            tool_definitions = {
                tool["name"]: tool.get("description")
                for tool in self.session.tool_executor.get_tool_definitions()
            }
            return tool_definitions.get(tool_name)


__all__ = [
    "ClaudeStylePrompt",
    "ClaudeStyleUI",
    "PermissionChoice",
    "ToolExecutionDisplay",
    "ToolStatus",
]
