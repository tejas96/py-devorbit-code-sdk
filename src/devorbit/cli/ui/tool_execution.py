"""Live tool execution display with animations.

Implements Claude Code-style animated tool execution with:
- Live spinner animations
- Real-time output streaming
- Tree-structured progress display
- Collapsible results
"""

import time
from typing import TYPE_CHECKING, Any


try:
    from rich.console import Console, Group
    from rich.live import Live
    from rich.panel import Panel
    from rich.spinner import Spinner
    from rich.text import Text
    from rich.tree import Tree

    HAS_RICH = True
except ImportError:
    HAS_RICH = False

if TYPE_CHECKING:
    from rich.console import RenderableType


class LiveToolExecution:
    """Live animated display for tool execution matching Claude Code UX."""

    def __init__(self, console: "Console | None" = None, no_color: bool = False) -> None:
        """Initialize live tool execution display.

        Args:
            console: Rich console instance
            no_color: Disable colored output
        """
        self.console = console if console else Console()
        self.no_color = no_color
        self.start_time: float | None = None
        self.live: Live | None = None
        self.output_lines: list[str] = []

    def start_execution(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        is_dangerous: bool = False,
    ) -> None:
        """Start live animated display of tool execution.

        Args:
            tool_name: Name of the tool
            tool_input: Tool input parameters
            is_dangerous: Whether this is a dangerous operation
        """
        if not HAS_RICH:
            print(f"\n[Tool: {tool_name}]")
            print("Status: ⏳ Executing...")
            return

        self.start_time = time.time()
        self.output_lines = []

        # Create initial display
        renderable = self._create_execution_display(
            tool_name, tool_input, is_dangerous, executing=True
        )

        # Start live display with spinner
        self.live = Live(
            renderable,
            console=self.console,
            refresh_per_second=10,
            transient=False,
        )
        self.live.start()

    def update_output(self, output_chunk: str) -> None:
        """Update display with new output chunk (real-time streaming).

        Args:
            output_chunk: New output to append
        """
        if output_chunk:
            self.output_lines.append(output_chunk)

    def finish_execution(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        success: bool,
        output: str | None = None,
        error: str | None = None,
        is_dangerous: bool = False,
    ) -> None:
        """Finish execution and show final result.

        Args:
            tool_name: Name of the tool
            tool_input: Tool input parameters
            success: Whether execution succeeded
            output: Tool output (if successful)
            error: Error message (if failed)
            is_dangerous: Whether this was a dangerous operation
        """
        if not HAS_RICH:
            status = "✓ Success" if success else "✕ Failed"
            print(f"Status: {status}")
            if output:
                print(output)
            elif error:
                print(f"Error: {error}")
            return

        # Stop live display
        if self.live:
            self.live.stop()

        # Show final result
        duration = time.time() - self.start_time if self.start_time else 0.0
        final_output = output or error or ""

        self._display_final_result(
            tool_name, tool_input, success, final_output, duration, is_dangerous
        )

        # Reset
        self.start_time = None
        self.output_lines = []

    def _create_execution_display(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        is_dangerous: bool,
        executing: bool = True,
    ) -> "RenderableType":
        """Create the live execution display.

        Args:
            tool_name: Tool name
            tool_input: Tool parameters
            is_dangerous: Dangerous operation flag
            executing: Whether currently executing

        Returns:
            Rich renderable
        """
        # Icon and color based on status
        if is_dangerous:
            icon = "⚠️ "
            color = "red"
        else:
            icon = "🔧 "
            color = "cyan"

        # Create tree structure
        tree = Tree(f"[bold {color}]{icon}{tool_name}[/bold {color}]")

        # Add parameters to tree
        for key, value in tool_input.items():
            value_str = str(value)
            if len(value_str) > 80:
                value_str = value_str[:77] + "..."

            if key == "command":
                param_node = tree.add(f"[yellow]{key.title()}[/yellow]")
                param_node.add(f"[white]{value_str}[/white]")
            elif key == "file_path":
                tree.add(f"[green]{key.title()}:[/green] [white]{value_str}[/white]")
            else:
                tree.add(f"[cyan]{key}:[/cyan] [dim]{value_str}[/dim]")

        # Add status with spinner if executing
        if executing:
            spinner = Spinner("dots", text="Executing...", style="cyan")
            tree.add(spinner)
        else:
            tree.add("[dim]Preparing...[/dim]")

        # Add live output if any
        if self.output_lines:
            output_text = "".join(self.output_lines[:10])
            if output_text.strip():
                output_node = tree.add("[dim]Output:[/dim]")
                for line in output_text.split("\n")[:8]:
                    if line.strip():
                        output_node.add(f"[dim]{line}[/dim]")

        # Wrap in panel
        return Panel(
            tree,
            title=f"[bold]{icon}Tool Execution[/bold]",
            border_style=color,
            padding=(1, 2),
        )

    def _display_final_result(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        success: bool,
        output: str,
        duration: float,
        is_dangerous: bool,
    ) -> None:
        """Display final execution result.

        Args:
            tool_name: Tool name
            tool_input: Tool parameters
            success: Success flag
            output: Output or error message
            duration: Execution duration
            is_dangerous: Dangerous operation flag
        """
        # Icon and colors
        if is_dangerous:
            icon = "⚠️ "
            base_color = "red" if not success else "yellow"
        else:
            icon = "🔧 "
            base_color = "cyan"

        border_color = "green" if success else "red"
        status_icon = "✓" if success else "✕"
        status_color = "green" if success else "red"

        # Create result tree
        tree = Tree(f"[bold {base_color}]{icon}{tool_name}[/bold {base_color}]")

        # Add status
        status_text = f"{status_icon} {'Success' if success else 'Failed'} ({duration:.2f}s)"
        tree.add(f"[bold {status_color}]{status_text}[/bold {status_color}]")

        # Add output preview (first 500 chars)
        if output:
            preview = output[:500] if len(output) > 500 else output
            if preview.strip():
                output_node = tree.add("[dim]Output:[/dim]")
                for line in preview.split("\n")[:15]:
                    if line.strip():
                        output_node.add(f"[white]{line}[/white]")

                if len(output) > 500:
                    output_node.add("[dim]...(output truncated)[/dim]")

        # Wrap in panel
        panel = Panel(
            tree,
            title=f"[bold]{icon}Tool Result[/bold]",
            border_style=border_color,
            padding=(1, 2),
        )

        self.console.print(panel)


__all__ = ["LiveToolExecution"]
