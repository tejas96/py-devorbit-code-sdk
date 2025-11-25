"""Arrow-based menu navigation component for tool approval.

This module provides an interactive menu with arrow key navigation,
replacing the traditional y/n keyboard shortcuts with a more intuitive
visual selection system.
"""

import sys
from typing import TYPE_CHECKING, Any

from prompt_toolkit import prompt
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings


try:
    from rich.console import Console
    from rich.live import Live
    from rich.text import Text

    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    Console = None  # type: ignore[assignment,misc]
    Live = None  # type: ignore[assignment,misc]
    Text = None  # type: ignore[assignment,misc]

if TYPE_CHECKING:
    from prompt_toolkit.key_binding.key_bindings import KeyPressEvent


class ArrowMenu:
    """Interactive arrow-based menu selector.

    Features:
    - Arrow key navigation (up/down)
    - Visual current selection indicator (>)
    - Bold highlighting of selected option
    - Enter to confirm
    - Number keys for direct selection
    - Vim-style navigation (j/k)
    """

    def __init__(
        self,
        options: list[str],
        console: "Console | None" = None,
        no_color: bool = False,
        default_index: int = 0,
    ):
        """Initialize arrow menu.

        Args:
            options: List of menu options to display
            console: Rich console instance
            no_color: Disable colored output
            default_index: Initially selected option (default: 0)
        """
        if not HAS_RICH or Console is None:
            raise ImportError(
                "Rich library required for ArrowMenu. Install with: pip install rich"
            )

        self.options = options
        self.console = console or Console()
        self.no_color = no_color
        self.current_index = default_index
        self.live_display: "Live | None" = None

        # Validate default index
        if not 0 <= self.current_index < len(self.options):
            self.current_index = 0

    def _render_menu(self) -> "Text":
        """Render the menu with current selection highlighted.

        Returns:
            Rich Text object with formatted menu
        """
        if Text is None:
            raise ImportError("Rich library required")

        text = Text()

        for i, option in enumerate(self.options):
            if i == self.current_index:
                # Current selection: arrow + bold + color
                if not self.no_color:
                    text.append("> ", style="bold cyan")
                    text.append(f"{i+1}. {option}", style="bold cyan")
                else:
                    text.append(f"> {i+1}. {option}", style="bold")
            else:
                # Other options: dimmed
                if not self.no_color:
                    text.append(f"  {i+1}. {option}", style="dim")
                else:
                    text.append(f"  {i+1}. {option}")

            # Add newline except for last option
            if i < len(self.options) - 1:
                text.append("\n")

        return text

    def _create_key_bindings(self) -> KeyBindings:
        """Create key bindings for arrow navigation.

        Returns:
            KeyBindings object with all navigation handlers
        """
        kb = KeyBindings()

        # Arrow key navigation
        @kb.add("up")  # type: ignore[misc]
        def move_up(event: "KeyPressEvent") -> None:
            """Move selection up."""
            if self.current_index > 0:
                self.current_index -= 1
            else:
                # Wrap around to bottom
                self.current_index = len(self.options) - 1
            # Update live display
            if self.live_display:
                self.live_display.update(self._render_menu())

        @kb.add("down")  # type: ignore[misc]
        def move_down(event: "KeyPressEvent") -> None:
            """Move selection down."""
            if self.current_index < len(self.options) - 1:
                self.current_index += 1
            else:
                # Wrap around to top
                self.current_index = 0
            # Update live display
            if self.live_display:
                self.live_display.update(self._render_menu())

        # Vim-style navigation
        @kb.add("j")  # type: ignore[misc]
        def move_down_vim(event: "KeyPressEvent") -> None:
            """Move selection down (Vim style)."""
            move_down(event)

        @kb.add("k")  # type: ignore[misc]
        def move_up_vim(event: "KeyPressEvent") -> None:
            """Move selection up (Vim style)."""
            move_up(event)

        # Enter to confirm
        @kb.add("enter")  # type: ignore[misc]
        def select_option(event: "KeyPressEvent") -> None:
            """Confirm selection."""
            event.app.exit(result=self.current_index)

        # Number keys for direct selection
        for i in range(1, min(10, len(self.options) + 1)):

            @kb.add(str(i))  # type: ignore[misc]
            def select_by_number(event: "KeyPressEvent", num: int = i) -> None:
                """Select option by number."""
                index = num - 1
                if 0 <= index < len(self.options):
                    self.current_index = index
                    event.app.exit(result=self.current_index)

        # Ctrl+C to cancel (select last option, typically "Cancel")
        @kb.add("c-c")  # type: ignore[misc]
        def cancel(event: "KeyPressEvent") -> None:
            """Cancel selection."""
            event.app.exit(result=len(self.options) - 1)

        return kb

    def show(self, instruction: str | None = None) -> int:
        """Display menu and get user selection.

        Args:
            instruction: Optional custom instruction text

        Returns:
            Index of selected option (0-based)
        """
        if Live is None:
            raise ImportError("Rich library required")

        # Default instruction
        if instruction is None:
            instruction = "Use ↑/↓ (or j/k) to navigate, Enter to select, 1-9 for direct selection"

        # Print instruction BEFORE starting Live display
        self.console.print()
        if not self.no_color:
            self.console.print(f"[dim]{instruction}[/dim]")
        else:
            self.console.print(instruction)

        # Create key bindings
        kb = self._create_key_bindings()

        # Start Live display for the menu only
        self.live_display = Live(
            self._render_menu(),
            console=self.console,
            refresh_per_second=10,
            transient=False,
        )

        try:
            with self.live_display:
                # Wait for user input with Live updating menu
                result = prompt(
                    HTML(""),  # Empty prompt
                    key_bindings=kb,
                    mouse_support=False,
                )

                return result if result is not None else len(self.options) - 1

        except KeyboardInterrupt:
            # Ctrl+C pressed - return last option (Cancel)
            return len(self.options) - 1
        except Exception:
            # Error - return cancel option
            return len(self.options) - 1
        finally:
            self.live_display = None


__all__ = ["ArrowMenu"]