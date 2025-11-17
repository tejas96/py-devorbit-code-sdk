"""Display components for streaming responses and tool calls.

Implements the display system from the Claude Code CLI specification for
real-time streaming responses and formatted tool call output.
"""

import time
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from rich.console import Console
    from rich.live import Live
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.syntax import Syntax


class StreamingDisplay:
    """Display system for streaming LLM responses.

    Handles real-time display of streaming responses with support for:
    - Animated streaming indicator (⏺)
    - Markdown rendering
    - Code blocks with syntax highlighting
    - Thinking blocks (collapsible)
    """

    def __init__(self, console: "Console | None" = None, no_color: bool = False) -> None:
        """Initialize streaming display.

        Args:
            console: Rich console instance (optional)
            no_color: Disable colored output
        """
        self.console = console
        self.no_color = no_color
        self.buffer: list[str] = []
        self.is_streaming = False

    def start_streaming(self) -> None:
        """Start streaming mode with animated indicator.

        Example:
            ⏺ Claude is thinking...
        """
        self.is_streaming = True
        self.buffer = []

        if self.console and not self.no_color:
            from .colors import Colors

            color = Colors.rich_brand()
            self.console.print(f"[{color}]⏺[/{color}] Responding...")
        else:
            print("⏺ Responding...")

    def append_chunk(self, chunk: str) -> None:
        """Append a chunk of text to the streaming display.

        Args:
            chunk: Text chunk to append
        """
        self.buffer.append(chunk)

        # Display the chunk in real-time
        if self.console:
            self.console.print(chunk, end="")
        else:
            print(chunk, end="", flush=True)

    def end_streaming(self) -> None:
        """End streaming mode and finalize display."""
        self.is_streaming = False

        if self.console:
            self.console.print()  # New line
        else:
            print()  # New line

        # Clear buffer
        self.buffer = []

    def display_message(self, content: str, role: str = "assistant") -> None:
        """Display a complete message with formatting.

        Args:
            content: Message content (supports markdown)
            role: Message role (user or assistant)
        """
        if role == "user":
            self._display_user_message(content)
        else:
            self._display_assistant_message(content)

    def _display_user_message(self, content: str) -> None:
        """Display user message.

        Args:
            content: User message content

        Example:
            > Your prompt text here
        """
        if self.console and not self.no_color:
            from .colors import Colors

            color = Colors.rich_info()
            self.console.print(f"[{color}]>[/{color}] {content}")
        else:
            print(f"> {content}")

    def _display_assistant_message(self, content: str) -> None:
        """Display assistant message with markdown rendering.

        Args:
            content: Assistant message content
        """
        if self.console and not self.no_color:
            try:
                from rich.markdown import Markdown

                md = Markdown(content)
                self.console.print(md)
            except ImportError:
                self.console.print(content)
        else:
            print(content)

    def display_thinking_block(self, thinking: str, collapsed: bool = False) -> None:
        """Display thinking block (extended thinking).

        Args:
            thinking: Thinking content
            collapsed: If True, show collapsed view

        Example:
            ┌─ Extended Thinking ─────────────────────────────────┐
            │ Let me analyze the requirements...                  │
            │ - First, I need to understand the structure         │
            │ - Then identify the best approach                   │
            └──────────────────────────────────────────────────────┘
        """
        if collapsed:
            if self.console:
                self.console.print("[dim]⟨ Extended Thinking ⟩[/dim]")
            else:
                print("⟨ Extended Thinking ⟩")
            return

        if self.console and not self.no_color:
            try:
                from rich.panel import Panel

                panel = Panel(
                    thinking,
                    title="Extended Thinking",
                    border_style="dim",
                    padding=(1, 2),
                )
                self.console.print(panel)
            except ImportError:
                self.console.print(f"\n[Thinking]\n{thinking}\n[/Thinking]\n")
        else:
            print(f"\n[Thinking]\n{thinking}\n[/Thinking]\n")


class ToolCallDisplay:
    """Display system for tool calls and their results.

    Handles formatted display of tool executions with:
    - Tool name and parameters
    - Status indicators (⏳, ✓, ✗)
    - Execution duration
    - Collapsible output
    """

    def __init__(self, console: "Console | None" = None, no_color: bool = False) -> None:
        """Initialize tool call display.

        Args:
            console: Rich console instance (optional)
            no_color: Disable colored output
        """
        self.console = console
        self.no_color = no_color
        self.start_time: float | None = None

    def show_tool_call(self, tool_name: str, tool_input: dict[str, Any]) -> None:
        """Display tool call initiation.

        Args:
            tool_name: Name of the tool
            tool_input: Tool input parameters

        Example:
            ┌─ Tool: Read ─────────────────────────────────────────┐
            │ File: src/main.py                                    │
            │ Status: ⏳ Executing...                              │
            └──────────────────────────────────────────────────────┘
        """
        self.start_time = time.time()

        # Format input parameters
        params_str = self._format_params(tool_input)

        if self.console and not self.no_color:
            try:
                from rich.panel import Panel

                from .colors import Colors

                color = Colors.rich_info()
                content = f"{params_str}\n[{color}]Status: ⏳ Executing...[/{color}]"

                panel = Panel(
                    content,
                    title=f"Tool: {tool_name}",
                    border_style="cyan",
                    padding=(1, 2),
                )
                self.console.print(panel)
            except ImportError:
                self.console.print(f"\n[Tool: {tool_name}]\n{params_str}\n⏳ Executing...\n")
        else:
            print(f"\n[Tool: {tool_name}]\n{params_str}\n⏳ Executing...\n")

    def show_tool_result(
        self, tool_name: str, success: bool, output: str | None = None, error: str | None = None
    ) -> None:
        """Display tool call result.

        Args:
            tool_name: Name of the tool
            success: Whether the tool succeeded
            output: Tool output (if successful)
            error: Error message (if failed)

        Example:
            ┌─ Tool: Read ─────────────────────────────────────────┐
            │ Status: ✓ Success (0.2s)                             │
            │ [Output Preview - Click to expand]                   │
            │ import os                                            │
            │ ...                                                  │
            └──────────────────────────────────────────────────────┘
        """
        duration = time.time() - self.start_time if self.start_time else 0.0

        status_icon = "✓" if success else "✗"
        status_text = f"{status_icon} {'Success' if success else 'Failed'} ({duration:.2f}s)"

        content = status_text
        if success and output:
            # Show preview of output (first 200 chars)
            preview = output[:200] + "..." if len(output) > 200 else output
            content += f"\n\n{preview}"
        elif error:
            content += f"\n\nError: {error}"

        if self.console and not self.no_color:
            try:
                from rich.panel import Panel

                from .colors import Colors

                color = Colors.rich_success() if success else Colors.rich_error()
                colored_content = f"[{color}]{content}[/{color}]"

                panel = Panel(
                    colored_content,
                    title=f"Tool: {tool_name}",
                    border_style="green" if success else "red",
                    padding=(1, 2),
                )
                self.console.print(panel)
            except ImportError:
                self.console.print(f"\n[Tool: {tool_name}]\n{content}\n")
        else:
            print(f"\n[Tool: {tool_name}]\n{content}\n")

        # Reset timer
        self.start_time = None

    @staticmethod
    def _format_params(params: dict[str, Any]) -> str:
        """Format tool parameters for display.

        Args:
            params: Parameter dictionary

        Returns:
            Formatted parameter string
        """
        lines = []
        for key, value in params.items():
            # Format value (truncate if too long)
            value_str = str(value)
            if len(value_str) > 100:
                value_str = value_str[:97] + "..."

            lines.append(f"{key}: {value_str}")

        return "\n".join(lines)


__all__ = ["StreamingDisplay", "ToolCallDisplay"]
