"""Notification system for Devorbit CLI.

Implements the notification system from the Claude Code CLI specification
with support for info, warning, error, and success notifications.
"""

from enum import Enum
from typing import TYPE_CHECKING

from .colors import Colors


if TYPE_CHECKING:
    from rich.console import Console


class NotificationType(Enum):
    """Types of notifications."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class NotificationManager:
    """Manages notifications in the terminal UI.

    Displays notifications with appropriate icons, colors, and durations
    according to the Claude Code CLI specification.
    """

    def __init__(self, console: "Console | None" = None, no_color: bool = False) -> None:
        """Initialize notification manager.

        Args:
            console: Rich console instance (optional)
            no_color: Disable colored output
        """
        self.console = console
        self.no_color = no_color
        self.icons = {
            NotificationType.INFO: "ℹ",
            NotificationType.WARNING: "⚠",
            NotificationType.ERROR: "✗",
            NotificationType.SUCCESS: "✓",
        }

    def info(self, message: str) -> None:
        """Display an info notification.

        Args:
            message: Info message to display

        Example:
            ℹ Session saved to ~/.devorbit/sessions/abc123
        """
        self._display(NotificationType.INFO, message)

    def warning(self, message: str) -> None:
        """Display a warning notification.

        Args:
            message: Warning message to display

        Example:
            ⚠ Context window is 80% full. Consider using /clear
        """
        self._display(NotificationType.WARNING, message)

    def error(self, message: str) -> None:
        """Display an error notification.

        Args:
            message: Error message to display

        Example:
            ✗ Failed to read file: Permission denied
        """
        self._display(NotificationType.ERROR, message)

    def success(self, message: str) -> None:
        """Display a success notification.

        Args:
            message: Success message to display

        Example:
            ✓ 5 files modified successfully
        """
        self._display(NotificationType.SUCCESS, message)

    def _display(self, notification_type: NotificationType, message: str) -> None:
        """Display a notification with appropriate formatting.

        Args:
            notification_type: Type of notification
            message: Message to display
        """
        icon = self.icons[notification_type]

        if self.console and not self.no_color:
            # Use Rich console with colors
            color_map = {
                NotificationType.INFO: Colors.rich_info(),
                NotificationType.WARNING: Colors.rich_warning(),
                NotificationType.ERROR: Colors.rich_error(),
                NotificationType.SUCCESS: Colors.rich_success(),
            }
            color = color_map[notification_type]
            self.console.print(f"[{color}]{icon}[/{color}] {message}")
        else:
            # Use plain text output
            print(f"{icon} {message}")

    def display_with_actions(
        self,
        notification_type: NotificationType,
        message: str,
        actions: list[str] | None = None,
    ) -> None:
        """Display a notification with action buttons.

        Args:
            notification_type: Type of notification
            message: Message to display
            actions: List of action labels (e.g., ["Retry", "Dismiss"])

        Example:
            ✗ Failed to read file: Permission denied
            [View Permissions] [Try Different Path] [Cancel]
        """
        self._display(notification_type, message)

        if actions:
            action_str = " ".join(f"[{action}]" for action in actions)
            if self.console and not self.no_color:
                self.console.print(f"[dim]{action_str}[/dim]")
            else:
                print(action_str)


__all__ = ["NotificationManager", "NotificationType"]
