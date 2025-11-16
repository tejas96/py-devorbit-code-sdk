"""UI components for Claude Code-style CLI experience."""

from typing import Any


try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
    from rich.syntax import Syntax
    from rich.table import Table
    from rich.text import Text

    HAS_RICH = True
except ImportError:
    HAS_RICH = False


class CLIFormatter:
    """Claude Code-style CLI formatter with rich UI elements."""

    def __init__(self, no_color: bool = False) -> None:
        """Initialize CLI formatter.

        Args:
            no_color: Disable colored output
        """
        self.no_color = no_color
        self.console = Console(no_color=no_color) if HAS_RICH else None

    def print_user_message(self, message: str) -> None:
        """Display user message in Claude Code style.

        Args:
            message: User's input message
        """
        if not HAS_RICH or self.console is None:
            print(f"\n> {message}\n")
            return

        user_text = Text()
        user_text.append("❯ ", style="bold cyan")  # noqa: RUF001
        user_text.append(message, style="white")

        self.console.print()
        self.console.print(user_text)
        self.console.print()

    def print_assistant_message(self, message: str, streaming: bool = False) -> None:
        """Display assistant message in Claude Code style.

        Args:
            message: Assistant's response
            streaming: Whether this is part of streaming response
        """
        if not HAS_RICH or self.console is None:
            if streaming:
                print(message, end="", flush=True)
            else:
                print(message)
            return

        if not streaming:
            # Render markdown for complete messages
            md = Markdown(message)
            self.console.print(md)
        else:
            # Plain text for streaming
            self.console.print(message, end="", markup=False)

    def print_thinking(self) -> None:
        """Display thinking indicator."""
        if not HAS_RICH or self.console is None:
            print("🤔 Thinking...")
            return

        text = Text()
        text.append("🤔 ", style="bold yellow")
        text.append("Thinking...", style="dim")
        self.console.print(text)

    def print_tool_use(self, tool_name: str, tool_input: dict[str, Any]) -> None:
        """Display tool usage in Claude Code style.

        Args:
            tool_name: Name of the tool being used
            tool_input: Tool input parameters
        """
        if not HAS_RICH or self.console is None:
            print(f"\n⚡ Using tool: {tool_name}")
            print(f"   Input: {tool_input}")
            return

        # Create tool panel
        tool_text = Text()
        tool_text.append("⚡ ", style="bold yellow")
        tool_text.append("Tool: ", style="dim")
        tool_text.append(tool_name, style="bold cyan")

        # Format input
        input_lines = []
        for key, value in tool_input.items():
            input_lines.append(f"{key}: {value!r}")

        panel = Panel(
            "\n".join(input_lines) if input_lines else "(no parameters)",
            title=tool_text,
            border_style="yellow",
            padding=(0, 1),
        )

        self.console.print()
        self.console.print(panel)

    def print_tool_result(self, tool_name: str, success: bool, result: Any = None) -> None:
        """Display tool result in Claude Code style.

        Args:
            tool_name: Name of the tool
            success: Whether tool execution succeeded
            result: Tool execution result
        """
        if not HAS_RICH or self.console is None:
            status = "✓" if success else "✗"
            print(f"{status} Tool completed: {tool_name}")
            if result:
                print(f"   Result: {result}")
            return

        status_icon = "✓" if success else "✗"
        status_color = "green" if success else "red"

        text = Text()
        text.append(f"{status_icon} ", style=f"bold {status_color}")
        text.append(tool_name, style="cyan")
        text.append(" completed", style="dim")

        self.console.print(text)

    def print_token_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        cache_creation_tokens: int = 0,
        cache_read_tokens: int = 0,
    ) -> None:
        """Display token usage in Claude Code style.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cache_creation_tokens: Cache creation tokens
            cache_read_tokens: Cache read tokens
        """
        if not HAS_RICH or self.console is None:
            total = input_tokens + output_tokens
            print(f"\n📊 Tokens: {input_tokens} in + {output_tokens} out = {total} total")
            if cache_creation_tokens or cache_read_tokens:
                print(f"   Cache: {cache_creation_tokens} created, {cache_read_tokens} read")
            return

        # Create token usage table
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Label", style="dim")
        table.add_column("Value", style="bold cyan")

        table.add_row("Input tokens:", f"{input_tokens:,}")
        table.add_row("Output tokens:", f"{output_tokens:,}")

        if cache_creation_tokens:
            table.add_row("Cache created:", f"{cache_creation_tokens:,}")
        if cache_read_tokens:
            table.add_row("Cache read:", f"{cache_read_tokens:,}")

        total = input_tokens + output_tokens
        table.add_row("Total:", f"{total:,}", style="bold green")

        panel = Panel(
            table,
            title="📊 Token Usage",
            border_style="blue",
            padding=(0, 1),
        )

        self.console.print()
        self.console.print(panel)

    def print_error(self, message: str, details: str | None = None) -> None:
        """Display error message in Claude Code style.

        Args:
            message: Error message
            details: Optional error details
        """
        if not HAS_RICH or self.console is None:
            print(f"\n✗ Error: {message}")
            if details:
                print(f"  Details: {details}")
            return

        error_text = Text()
        error_text.append("✗ ", style="bold red")
        error_text.append("Error: ", style="bold red")
        error_text.append(message, style="red")

        self.console.print()
        self.console.print(error_text)

        if details:
            panel = Panel(
                details,
                title="Details",
                border_style="red",
                padding=(0, 1),
            )
            self.console.print(panel)

    def print_success(self, message: str) -> None:
        """Display success message.

        Args:
            message: Success message
        """
        if not HAS_RICH or self.console is None:
            print(f"✓ {message}")
            return

        text = Text()
        text.append("✓ ", style="bold green")
        text.append(message, style="green")
        self.console.print(text)

    def print_info(self, message: str) -> None:
        """Display info message.

        Args:
            message: Info message
        """
        if not HAS_RICH or self.console is None:
            print(f"ℹ {message}")  # noqa: RUF001
            return

        text = Text()
        text.append("ℹ ", style="bold blue")  # noqa: RUF001
        text.append(message, style="blue")
        self.console.print(text)

    def print_code_block(self, code: str, language: str = "python") -> None:
        """Display code block with syntax highlighting.

        Args:
            code: Code to display
            language: Programming language for syntax highlighting
        """
        if not HAS_RICH or self.console is None:
            print(f"\n```{language}")
            print(code)
            print("```")
            return

        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        self.console.print()
        self.console.print(syntax)

    def create_progress(self, description: str = "Processing...") -> Any:
        """Create progress indicator for long operations.

        Args:
            description: Progress description

        Returns:
            Progress object (or None if rich not available)
        """
        if not HAS_RICH:
            return None

        return Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console,
        )

    def confirm(self, question: str, default: bool = True) -> bool:
        """Ask for user confirmation (Claude Code style).

        Args:
            question: Question to ask
            default: Default answer

        Returns:
            User's response
        """
        if not HAS_RICH or self.console is None:
            default_text = "Y/n" if default else "y/N"
            response = input(f"\n{question} [{default_text}]: ").strip().lower()
            if not response:
                return default
            return response in ("y", "yes")

        # Rich formatted confirmation
        text = Text()
        text.append("❓ ", style="bold yellow")
        text.append(question, style="bold")

        default_text = "Y/n" if default else "y/N"
        text.append(f" [{default_text}]: ", style="dim")

        self.console.print()
        self.console.print(text, end="")

        response = input().strip().lower()
        if not response:
            return default
        return response in ("y", "yes")


__all__ = ["CLIFormatter"]
