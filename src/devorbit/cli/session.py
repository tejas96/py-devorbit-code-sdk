"""CLI session management with Claude Code UI system."""

from pathlib import Path
from typing import TYPE_CHECKING, Any

from devorbit._types import ContentBlock


try:
    from rich.console import Console as RichConsole

    HAS_RICH = True
except ImportError:
    RichConsole = None
    HAS_RICH = False

from devorbit import Devorbit

from .permissions import ToolApprovalPrompt
from .tools import ToolExecutor


if TYPE_CHECKING:
    from devorbit._types import Message


class CLISession:
    """Manages a Devorbit CLI session with Claude Code UI."""

    def __init__(
        self,
        provider: str,
        api_key: str,
        model: str | None = None,
        working_dir: Path | None = None,
        no_color: bool = False,
        debug: bool = False,
        auto_approve_tools: bool = False,
    ) -> None:
        """Initialize a CLI session.

        Args:
            provider: LLM provider to use
            api_key: API key for the provider
            model: Specific model to use (optional)
            working_dir: Working directory for file operations
            no_color: Disable colored output
            debug: Enable debug mode
            auto_approve_tools: Automatically approve non-dangerous tool executions
        """
        self.provider = provider
        self.api_key = api_key

        # Set model with provider-specific defaults
        if model is None:
            default_models = {
                "anthropic": "claude-sonnet-4-5",
                "openai": "gpt-4o",
                "gemini": "gemini-pro-2-5",
                "mistral": "mistral-large-latest",
                "codellama": "codellama-70b-instruct",
            }
            self.model = default_models.get(provider, "claude-sonnet-4-5")
        else:
            self.model = model

        self.working_dir = working_dir or Path.cwd()
        self.no_color = no_color
        self.debug = debug
        self.auto_approve_tools = auto_approve_tools

        # Initialize console
        self.console: RichConsole | None = None
        if HAS_RICH and RichConsole is not None:
            self.console = RichConsole(no_color=no_color)

        # Initialize Devorbit client
        self.client = Devorbit(
            provider=provider,  # type: ignore
            api_key=api_key,
        )

        # Conversation history
        self.messages: list[Message] = []

        # Session state
        self.is_running = True
        self.planning_mode = False

        # Initialize Claude Code style displays
        # Import here to avoid circular imports
        from .ui.streaming_display_enhanced import (
            ClaudeStyleStreamingDisplay,
            ClaudeStyleToolDisplay,
        )
        
        self.claude_streaming = ClaudeStyleStreamingDisplay(self.console, no_color)
        self.claude_tool_display = ClaudeStyleToolDisplay(self.console, no_color)

        # Initialize tool executor and approval system
        self.tool_executor = ToolExecutor(self)
        self.tool_approval = ToolApprovalPrompt(self)

    def display_welcome(self) -> None:
        """Display welcome banner - KEEPING ORIGINAL AS REQUESTED."""
        if not HAS_RICH or self.console is None:
            print("Welcome to Devorbit CLI!")
            print(f"Provider: {self.provider}")
            print(f"Working directory: {self.working_dir}")
            return

        try:
            from rich.panel import Panel
            from rich.text import Text

            welcome_text = Text()
            welcome_text.append("Devorbit CLI\n", style="bold cyan")
            welcome_text.append("Provider: ", style="dim")
            welcome_text.append(f"{self.provider}\n", style="green")
            if self.model:
                welcome_text.append("Model: ", style="dim")
                welcome_text.append(f"{self.model}\n", style="green")
            welcome_text.append("Working directory: ", style="dim")
            welcome_text.append(f"{self.working_dir}\n", style="yellow")
            welcome_text.append("\nType ", style="dim")
            welcome_text.append("/help", style="bold")
            welcome_text.append(" for available commands or ", style="dim")
            welcome_text.append("/exit", style="bold")
            welcome_text.append(" to quit", style="dim")

            panel = Panel(
                welcome_text,
                title="🤖 Welcome",
                border_style="cyan",
                padding=(1, 2),
            )
            self.console.print(panel)
            self.console.print()
        except ImportError:
            print("Welcome to Devorbit CLI!")
            print(f"Provider: {self.provider}")

    def add_message(
        self, role: str, content: str | list[ContentBlock] | list[dict[str, Any]]
    ) -> None:
        """Add a message to conversation history.

        Args:
            role: Message role (user or assistant)
            content: Message content
        """
        message: Message = {
            "role": role,  # type: ignore
            "content": content,  # type: ignore
        }
        self.messages.append(message)

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.messages.clear()

    def print(self, *args: Any, **kwargs: Any) -> None:
        """Print to console with proper formatting.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
        """
        if HAS_RICH and self.console is not None:
            self.console.print(*args, **kwargs)
        else:
            print(*args, **kwargs)

    def print_error(self, message: str) -> None:
        """Print an error message in Claude Code style.

        Args:
            message: Error message
        """
        if self.console and not self.no_color:
            self.console.print(f"[rgb(239,68,68)]✗[/rgb(239,68,68)] {message}")
        else:
            print(f"✗ {message}")

    def print_success(self, message: str) -> None:
        """Print a success message in Claude Code style.

        Args:
            message: Success message
        """
        if self.console and not self.no_color:
            self.console.print(f"[rgb(16,185,129)]✓[/rgb(16,185,129)] {message}")
        else:
            print(f"✓ {message}")

    def print_info(self, message: str) -> None:
        """Print an info message in Claude Code style.

        Args:
            message: Info message
        """
        if self.console and not self.no_color:
            self.console.print(f"[dim]{message}[/dim]")
        else:
            print(message)

    def print_warning(self, message: str) -> None:
        """Print a warning message in Claude Code style.

        Args:
            message: Warning message
        """
        if self.console and not self.no_color:
            self.console.print(f"[rgb(245,158,11)]⚠[/rgb(245,158,11)] {message}")
        else:
            print(f"⚠ {message}")


__all__ = ["CLISession"]