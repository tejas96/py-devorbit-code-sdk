"""CLI session management with enhanced UI system."""

import json
import random
from pathlib import Path
from typing import TYPE_CHECKING, Any

from devorbit.core.types import ContentBlock


try:
    from rich import box
    from rich.console import Console as RichConsole
    from rich.panel import Panel as RichPanel
    from rich.table import Table as RichTable
    from rich.text import Text as RichText

    HAS_RICH = True
except ImportError:
    RichConsole = None  # type: ignore[assignment,misc]
    RichPanel = None  # type: ignore[assignment,misc]
    RichText = None  # type: ignore[assignment,misc]
    RichTable = None  # type: ignore[assignment,misc]
    box = None  # type: ignore[assignment]
    HAS_RICH = False

from devorbit import Devorbit
from devorbit.core.hooks import get_registry, load_hooks_from_config

from .permissions import ToolApprovalPrompt
from .system_prompt import build_system_prompt
from .tools import ToolExecutor
from .ui import (
    CodeBlockDisplay,
    DiffDisplay,
    NotificationManager,
    ProgressIndicator,
    StatusLine,
    StreamingDisplay,
)


if TYPE_CHECKING:
    from devorbit.core.types import Message


# ANSI escape codes for terminal colors
ORANGE = "\033[38;5;208m"
RESET = "\033[0m"
GRAY = "\033[90m"
WHITE = "\033[97m"


class CLISession:
    """Manages a Devorbit CLI session."""

    # ------------------------------
    #      TIPS FEATURE
    # ------------------------------
    TIPS = [
        "Type your message or @path/to/file",
        "Use @filename to reference files",
        "Enter submits single line messages",
        "Alt+Enter or Ctrl+J to submit multiline",
        "Press Ctrl+D to exit anytime",
        "Use /clear to clear history",
        "Try /model to switch AI models",
        "Reference files with @src/main.py",
        "Use /history to see recent messages",
        "Press Ctrl+@ for quick file mention",
        "Paste code, then Alt+Enter to send",
    ]

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
            working_dir: Working directory for file operations (default: current directory)
            no_color: Disable colored output
            debug: Enable debug mode
            auto_approve_tools: Automatically approve non-dangerous tool executions
        """
        self.provider = provider
        self.api_key = api_key

        # Set model with provider-specific defaults if not specified
        if model is None:
            default_models = {
                "anthropic": "claude-sonnet-4-5",
                "openai": "gpt-4o",
                "gemini": "gemini-2.5-flash",
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
            provider=provider,  # type: ignore[arg-type]
            api_key=api_key,
        )

        # Conversation history
        self.messages: list[Message] = []

        # Session state
        self.is_running = True
        self.planning_mode = False

        # Initialize enhanced UI components
        self.notifications = NotificationManager(self.console, no_color)
        self.progress = ProgressIndicator(self.console, no_color)
        self.status_line = StatusLine(self.console, no_color=no_color)
        self.streaming = StreamingDisplay(self.console, no_color)
        self.code_display = CodeBlockDisplay(self.console, no_color)
        self.diff_display = DiffDisplay(self.console, no_color)

        # Initialize tool executor and approval system
        self.tool_executor = ToolExecutor(self)
        self.tool_approval = ToolApprovalPrompt(self)

        # System prompt for the LLM (after tool executor for dynamic tool list)
        self.system_prompt = self._build_system_prompt()

        # Set initial status line values
        self.status_line.set_model(self.model, provider)
        self.status_line.set_project(working_dir or Path.cwd())

        # Load hooks from .devorbit.json config
        self._load_hooks_config()

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the LLM.

        Returns:
            Complete system prompt string with context
        """
        # Get list of available tools from tool executor
        tools_available = None
        if hasattr(self, "tool_executor"):
            tool_defs = self.tool_executor.get_tool_definitions()
            tools_available = [t.get("name", "") for t in tool_defs if t.get("name")]

        return build_system_prompt(
            working_dir=self.working_dir,
            provider=self.provider,
            model=self.model,
            tools_available=tools_available,
        )

    def _load_hooks_config(self) -> None:
        """Load hooks from .devorbit.json config file."""
        config_paths = [
            self.working_dir / ".devorbit.json",
            Path.home() / ".devorbit.json",
        ]

        for config_path in config_paths:
            if config_path.exists():
                try:
                    with config_path.open() as f:
                        config = json.load(f)

                    hooks = load_hooks_from_config(config)
                    registry = get_registry()

                    for hook in hooks:
                        registry.register(hook)

                    if hooks and self.debug:
                        self.print_info(f"Loaded {len(hooks)} hooks from {config_path}")

                except (json.JSONDecodeError, OSError) as e:
                    if self.debug:
                        self.print_warning(f"Failed to load hooks from {config_path}: {e}")

    def get_hooks_info(self) -> list[dict[str, Any]]:
        """Get information about all registered hooks.

        Returns:
            List of hook info dictionaries
        """
        return get_registry().list_all()

    def display_welcome(self) -> None:
        """Display welcome banner with tips in a split horizontal layout."""
        # Check if Rich is available for the advanced layout
        if not (HAS_RICH and self.console):
            print(f"Devorbit CLI - {self.provider}/{self.model}")
            print(f"Working Dir: {self.working_dir}")
            return

        # 1. Setup Data
        model_display = self.model if self.model else "default"
        provider_display = self.provider.capitalize()
        random_tip = random.choice(self.TIPS)

        # 2. Create the Main Layout Table (2 Columns)
        # Using a full Table instead of grid allows us to control borders (box)
        # show_edge=False removes the outer border, leaving only the internal divider
        # padding settings: (top/bottom, left/right)
        grid = RichTable(
            show_header=False,
            box=box.ROUNDED,
            show_edge=False,
            expand=True,
            padding=(1, 2),
            border_style="grey30",  # Subtle color for the divider line
        )
        grid.add_column(justify="center", ratio=1)  # Left Column: Logo
        grid.add_column(justify="left", ratio=1)  # Right Column: Info

        # 3. Left Side: Compact Logo & Version
        # New "Tech/Modern" style ASCII logo
        logo_text = (
            "[orange3]"
            r"     ____                        __    _ __ " + "\n"
            r"    / __ \___ _   ______  ____  / /_  (_) /_" + "\n"
            r"   / / / / _ \ | / / __ \/ __ \/ __ \/ / __/" + "\n"
            r" / /_/ /  __/ |/ / /_/ / / / / /_/ / / /_  " + "\n"
            r"/_____/\___/|___/\____/_/ /_/_.___/_/\__/  " + "\n"
            "[/]"
        )

        logo_panel = RichText.from_markup(
            f"{logo_text}\n[white]v1.0.0[/]\n[grey50]The AI Software Engineer[/]"
        )

        # 4. Right Side: Info, Tips, & Commands
        # We use a nested grid for perfect alignment of labels and values
        info_grid = RichTable.grid(padding=(0, 2))
        info_grid.add_column(style="bold white")
        info_grid.add_column(style="orange3")  # Use 'orange3' style, NOT the ANSI 'ORANGE' constant

        # Helper for grey labels
        def label(text: str) -> RichText:
            return RichText(text, style="grey50")

        # Session Details
        info_grid.add_row(label("Provider:"), f"{provider_display}")
        info_grid.add_row(label("Model:"), f"{model_display}")
        info_grid.add_row(label("Path:"), f"{self.working_dir.name}/")
        info_grid.add_row("", "")  # Spacer

        # Random Tip
        info_grid.add_row(label("💡 Tip:"), f"{random_tip}")
        info_grid.add_row("", "")  # Spacer

        # Quick Commands
        info_grid.add_row(label("Start:"), "/init to setup project")
        info_grid.add_row(label("Help:"), "/help to list commands")
        info_grid.add_row(label("Ref:"), "@filename to mention code")

        # 5. Add Content to Main Grid and Print
        grid.add_row(logo_panel, info_grid)

        # Wrap in a panel for the border
        self.console.print(
            RichPanel(
                grid,
                border_style="orange3",
                subtitle="[grey50]Press [white]Ctrl+D[/] to exit[/]",
                subtitle_align="right",
            )
        )

    def add_message(
        self, role: str, content: str | list[ContentBlock] | list[dict[str, Any]]
    ) -> None:
        """Add a message to conversation history.

        Args:
            role: Message role (user or assistant)
            content: Message content
        """
        message: Message = {
            "role": role,  # type: ignore[typeddict-item]
            "content": content,  # type: ignore[typeddict-item]
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
        self.notifications.error(message)

    def print_success(self, message: str) -> None:
        """Print a success message.

        Args:
            message: Success message to display
        """
        self.notifications.success(message)

    def print_info(self, message: str) -> None:
        """Print an info message.

        Args:
            message: Info message to display
        """
        self.notifications.info(message)

    def print_warning(self, message: str) -> None:
        """Print a warning message.

        Args:
            message: Warning message to display
        """
        self.notifications.warning(message)
