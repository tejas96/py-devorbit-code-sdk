"""Enhanced tool execution display with colored panels."""

import json
from typing import Any

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.table import Table
    from rich.text import Text

    HAS_RICH = True
except ImportError:
    HAS_RICH = False


class ToolExecutionDisplay:
    """Display tool execution with rich formatting."""

    def __init__(self, no_color: bool = False) -> None:
        """Initialize tool execution display.

        Args:
            no_color: Disable colored output
        """
        self.no_color = no_color
        self.console = Console(no_color=no_color) if HAS_RICH else None

    def display_tool_call(
        self, tool_name: str, tool_input: dict[str, Any], show_input: bool = True
    ) -> None:
        """Display tool call with formatted input.

        Args:
            tool_name: Name of the tool
            tool_input: Tool input parameters
            show_input: Whether to show input details
        """
        if not HAS_RICH or self.console is None:
            self._display_plain_call(tool_name, tool_input, show_input)
            return

        # Tool icon mapping
        icons = {
            "write_file": "✢",
            "edit_file": "✎",
            "read_file": "👁",
            "ls_directory": "📂",
            "glob_files": "🔍",
            "grep_code": "🔎",
            "bash": "⚡",
            "task": "🤖",
            "web_search": "🌐",
            "web_fetch": "📥",
        }

        icon = icons.get(tool_name, "⚙")

        # Create header text
        header = Text()
        header.append(f"{icon} ", style="bold cyan")
        header.append(tool_name, style="bold white")

        if show_input and tool_input:
            # Format input based on tool type
            if tool_name == "write_file" or tool_name in ("edit_file", "read_file"):
                file_path = tool_input.get("file_path", "")
                header.append(f"({file_path})", style="dim")
            elif tool_name == "bash":
                command = tool_input.get("command", "")[:50]
                header.append(f"({command}...)", style="dim")
            elif tool_name == "grep_code":
                pattern = tool_input.get("pattern", "")
                header.append(f"('{pattern}')", style="dim")

        self.console.print(header)

        # Display detailed input if requested
        if show_input and tool_input and len(str(tool_input)) < 500:
            self._display_input_panel(tool_input)

    def _display_plain_call(
        self, tool_name: str, tool_input: dict[str, Any], show_input: bool
    ) -> None:
        """Display tool call in plain text.

        Args:
            tool_name: Tool name
            tool_input: Tool input
            show_input: Show input flag
        """
        print(f"\n⚙ {tool_name}")
        if show_input and tool_input:
            print(f"   Input: {tool_input}")

    def _display_input_panel(self, tool_input: dict[str, Any]) -> None:
        """Display tool input in a panel.

        Args:
            tool_input: Tool input parameters
        """
        if not HAS_RICH or self.console is None:
            return

        # Format as JSON
        json_str = json.dumps(tool_input, indent=2)
        syntax = Syntax(json_str, "json", theme="monokai")

        panel = Panel(
            syntax,
            title="[dim]Input[/dim]",
            border_style="dim",
            padding=(0, 1),
        )

        self.console.print(panel)

    def display_tool_result(
        self, tool_name: str, result: Any, success: bool = True, compact: bool = True
    ) -> None:
        """Display tool execution result.

        Args:
            tool_name: Name of the tool
            result: Tool result
            success: Whether execution succeeded
            compact: Use compact display
        """
        if not HAS_RICH or self.console is None:
            self._display_plain_result(tool_name, result, success)
            return

        # Result prefix
        prefix = "⎿ " if success else "✗ "
        style = "green" if success else "red"

        # Create result text
        text = Text()
        text.append(prefix, style=f"bold {style}")

        # Format result based on tool
        if tool_name == "write_file":
            if isinstance(result, dict):
                lines = result.get("lines_written", 0)
                path = result.get("file_path", "")
                text.append(f"Wrote {lines} lines to ", style=style)
                text.append(str(path), style="bold cyan")
        elif tool_name == "read_file":
            if isinstance(result, dict):
                lines = result.get("lines", 0)
                text.append(f"Read {lines} lines", style=style)
        elif tool_name == "bash":
            if isinstance(result, dict):
                exit_code = result.get("exit_code", 0)
                if exit_code == 0:
                    text.append("Command completed", style=style)
                else:
                    text.append(f"Command failed (exit {exit_code})", style="red")
        else:
            text.append(f"{tool_name} completed", style=style)

        self.console.print(text)

        # Display detailed result if not compact
        if not compact and result:
            self._display_result_panel(result)

    def _display_plain_result(self, tool_name: str, result: Any, success: bool) -> None:
        """Display result in plain text.

        Args:
            tool_name: Tool name
            result: Result
            success: Success flag
        """
        status = "✓" if success else "✗"
        print(f"{status} {tool_name}: {result}")

    def _display_result_panel(self, result: Any) -> None:
        """Display result in a panel.

        Args:
            result: Result to display
        """
        if not HAS_RICH or self.console is None:
            return

        # Format result
        if isinstance(result, dict):
            json_str = json.dumps(result, indent=2)
            syntax = Syntax(json_str, "json", theme="monokai")
            content = syntax
        elif isinstance(result, str):
            # Limit length
            content = result[:500] + "\n... (truncated)" if len(result) > 500 else result
        else:
            content = str(result)

        panel = Panel(
            content,
            title="[dim]Result[/dim]",
            border_style="green",
            padding=(0, 1),
        )

        self.console.print(panel)

    def display_tool_table(self, tools: list[dict[str, Any]]) -> None:
        """Display table of available tools.

        Args:
            tools: List of tool definitions
        """
        if not HAS_RICH or self.console is None:
            print("\nAvailable Tools:")
            for tool in tools:
                print(f"  • {tool.get('name', 'Unknown')}: {tool.get('description', '')}")
            return

        table = Table(title="Available Tools", show_header=True)
        table.add_column("Tool", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")

        for tool in tools:
            name = tool.get("name", "Unknown")
            description = tool.get("description", "")
            table.add_row(name, description)

        self.console.print()
        self.console.print(table)
        self.console.print()

    def display_execution_summary(
        self, total_tools: int, successful: int, failed: int, duration: float
    ) -> None:
        """Display execution summary.

        Args:
            total_tools: Total tools executed
            successful: Number of successful executions
            failed: Number of failed executions
            duration: Total duration in seconds
        """
        if not HAS_RICH or self.console is None:
            print("\nExecution Summary:")
            print(f"  Total: {total_tools}")
            print(f"  Successful: {successful}")
            print(f"  Failed: {failed}")
            print(f"  Duration: {duration:.2f}s")
            return

        table = Table(show_header=False, box=None)
        table.add_column("Metric", style="dim")
        table.add_column("Value", style="bold white")

        table.add_row("Total Tools", str(total_tools))
        table.add_row("Successful", Text(str(successful), style="green"))

        if failed > 0:
            table.add_row("Failed", Text(str(failed), style="red"))

        table.add_row("Duration", f"{duration:.2f}s")

        panel = Panel(
            table,
            title="[bold cyan]Execution Summary[/bold cyan]",
            border_style="cyan",
        )

        self.console.print()
        self.console.print(panel)


__all__ = ["ToolExecutionDisplay"]
