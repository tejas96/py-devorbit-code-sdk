"""CLI session management."""

from pathlib import Path
from typing import TYPE_CHECKING, Any

try:
    from rich.console import Console as RichConsole
    from rich.panel import Panel as RichPanel
    from rich.text import Text as RichText

    HAS_RICH = True
except ImportError:
    RichConsole = None  # type: ignore[assignment,misc]
    RichPanel = None  # type: ignore[assignment,misc]
    RichText = None  # type: ignore[assignment,misc]
    HAS_RICH = False

from devorbit import Devorbit

if TYPE_CHECKING:
    from devorbit._types import Message


class CLISession:
    """Manages a Devorbit CLI session."""

    def __init__(
        self,
        provider: str,
        api_key: str,
        model: str | None = None,
        working_dir: Path | None = None,
        no_color: bool = False,
        debug: bool = False,
    ) -> None:
        """Initialize a CLI session.

        Args:
            provider: LLM provider to use
            api_key: API key for the provider
            model: Specific model to use (optional)
            working_dir: Working directory for file operations (default: current directory)
            no_color: Disable colored output
            debug: Enable debug mode
        """
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.working_dir = working_dir or Path.cwd()
        self.no_color = no_color
        self.debug = debug

        # Initialize console
        self.console: RichConsole | None = None
        if HAS_RICH and RichConsole is not None:
            self.console = RichConsole(no_color=no_color)

        # Initialize Devorbit client
        self.client = Devorbit(
            provider=provider,  # type: ignore[arg-type]
            api_key=api_key,
        )

        # Conversation history
        self.messages: list[Message] = []

        # Session state
        self.is_running = True
        self.planning_mode = False

    def display_welcome(self) -> None:
        """Display welcome banner."""
        if not HAS_RICH or self.console is None or RichPanel is None or RichText is None:
            print("Welcome to Devorbit CLI!")
            print(f"Provider: {self.provider}")
            print(f"Working directory: {self.working_dir}")
            return

        welcome_text = RichText()
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

        panel = RichPanel(
            welcome_text,
            title="🤖 Welcome",
            border_style="cyan",
            padding=(1, 2),
        )
        self.console.print(panel)
        self.console.print()

    def add_message(self, role: str, content: str) -> None:
        """Add a message to conversation history.

        Args:
            role: Message role (user or assistant)
            content: Message content
        """
        message: Message = {
            "role": role,  # type: ignore[typeddict-item]
            "content": content,
        }
        self.messages.append(message)

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.messages.clear()

    def print(self, *args: Any, **kwargs: Any) -> None:
        """Print to console with proper formatting.

        Args:
            *args: Positional arguments for print/console.print
            **kwargs: Keyword arguments for print/console.print
        """
        if HAS_RICH and self.console is not None:
            self.console.print(*args, **kwargs)
        else:
            print(*args, **kwargs)

    def print_error(self, message: str) -> None:
        """Print an error message.

        Args:
            message: Error message to display
        """
        if HAS_RICH and self.console is not None:
            self.console.print(f"[bold red]Error:[/bold red] {message}")
        else:
            print(f"Error: {message}")

    def print_success(self, message: str) -> None:
        """Print a success message.

        Args:
            message: Success message to display
        """
        if HAS_RICH and self.console is not None:
            self.console.print(f"[bold green]✓[/bold green] {message}")
        else:
            print(f"✓ {message}")

    def print_info(self, message: str) -> None:
        """Print an info message.

        Args:
            message: Info message to display
        """
        if HAS_RICH and self.console is not None:
            self.console.print(f"[bold cyan]i[/bold cyan] {message}")
        else:
            print(f"i {message}")
