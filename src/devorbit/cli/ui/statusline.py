"""Status line system for Devorbit CLI.

Implements the customizable status line system from the Claude Code CLI specification
with template support and real-time updates.
"""

import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from rich.console import Console


class StatusLine:
    """Customizable status line for the terminal UI.

    Supports template-based status lines with variable substitution.

    Example templates:
        "${model_short} | ${context_percent}% | ${git_info} | ${cost} | ${duration}"
        "[${model}] [${context}] [${git_branch} ${git_status}] [$${cost}] [${time}]"
    """

    # Default template (matches Claude Code spec)
    DEFAULT_TEMPLATE = (
        "[${model_short}] [${context}] [${git_branch} ${git_status}] [$${cost}] [${duration}]"
    )

    def __init__(
        self,
        console: "Console | None" = None,
        template: str | None = None,
        no_color: bool = False,
    ) -> None:
        """Initialize status line.

        Args:
            console: Rich console instance (optional)
            template: Custom status line template (uses default if None)
            no_color: Disable colored output
        """
        self.console = console
        self.template = template or self.DEFAULT_TEMPLATE
        self.no_color = no_color
        self.start_time = datetime.now()

        # Status line state
        self.model: str | None = None
        self.model_short: str | None = None
        self.provider: str | None = None
        self.context_tokens: int = 0
        self.context_max: int = 200000
        self.git_branch: str | None = None
        self.git_status: str = "-"
        self.cost: float = 0.0
        self.message_count: int = 0
        self.project_name: str | None = None
        self.mcp_servers: list[str] = []
        self.hooks_active: int = 0

    def set_model(self, model: str, provider: str) -> None:
        """Set the current model and provider.

        Args:
            model: Full model name
            provider: Provider name
        """
        self.model = model
        self.provider = provider

        # Generate short model name
        if "claude" in model.lower():
            if "opus" in model.lower():
                self.model_short = "Opus"
            elif "sonnet" in model.lower():
                self.model_short = "Sonnet"
            elif "haiku" in model.lower():
                self.model_short = "Haiku"
            else:
                self.model_short = model[:15]
        elif "gpt" in model.lower():
            parts = model.split("-")
            self.model_short = "-".join(parts[:2]) if len(parts) >= 2 else model[:15]
        elif "gemini" in model.lower():
            self.model_short = "Gemini"
        else:
            self.model_short = model[:15]

    def set_context(self, tokens: int, max_tokens: int = 200000) -> None:
        """Set context window usage.

        Args:
            tokens: Current token count
            max_tokens: Maximum context window size
        """
        self.context_tokens = tokens
        self.context_max = max_tokens

    def set_git_info(self, branch: str | None, status: str = "✓") -> None:
        """Set git information.

        Args:
            branch: Git branch name (None if not a git repo)
            status: Git status symbol (✓ clean, ± changes, ✗ conflicts, - no repo)
        """
        self.git_branch = branch
        self.git_status = status if branch else "-"

    def set_cost(self, cost: float) -> None:
        """Set session cost.

        Args:
            cost: Cost in dollars
        """
        self.cost = cost

    def increment_messages(self) -> None:
        """Increment message count."""
        self.message_count += 1

    def set_project(self, path: Path) -> None:
        """Set project directory.

        Args:
            path: Project directory path
        """
        self.project_name = path.name

    def set_mcp_servers(self, servers: list[str]) -> None:
        """Set active MCP servers.

        Args:
            servers: List of server names
        """
        self.mcp_servers = servers

    def set_hooks_count(self, count: int) -> None:
        """Set number of active hooks.

        Args:
            count: Number of active hooks
        """
        self.hooks_active = count

    def render(self) -> str:
        """Render the status line with current values.

        Returns:
            Formatted status line string
        """
        # Calculate derived values
        context_percent = (
            int((self.context_tokens / self.context_max) * 100) if self.context_max > 0 else 0
        )
        context_str = f"{self.context_tokens // 1000}k/{self.context_max // 1000}k"

        duration = datetime.now() - self.start_time
        duration_str = self._format_duration(duration)

        git_info = (
            f"{self.git_branch} {self.git_status}" if self.git_branch else f"- {self.git_status}"
        )

        mcp_servers_str = ", ".join(self.mcp_servers) if self.mcp_servers else "none"

        # Variable substitution map
        variables: dict[str, Any] = {
            "model": self.model or "unknown",
            "model_short": self.model_short or "unknown",
            "provider": self.provider or "unknown",
            "context": context_str,
            "context_percent": context_percent,
            "context_bar": self._make_progress_bar(context_percent),
            "git_branch": self.git_branch or "-",
            "git_status": self.git_status,
            "git_info": git_info,
            "cost": f"{self.cost:.2f}",
            "duration": duration_str,
            "message_count": self.message_count,
            "time": datetime.now().strftime("%H:%M:%S"),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "project_name": self.project_name or "unknown",
            "mcp_servers": mcp_servers_str,
            "hooks_active": self.hooks_active,
        }

        # Substitute variables
        result = self.template
        for key, value in variables.items():
            pattern = r"\$\{" + key + r"\}"
            result = re.sub(pattern, str(value), result)

        return result

    def display(self) -> None:
        """Display the status line."""
        status_text = self.render()

        if self.console and not self.no_color:
            from .colors import Colors

            # Apply colors to different parts
            colored_status = status_text.replace("[", f"[{Colors.rich_muted()}][").replace(
                "]", f"][/{Colors.rich_muted()}]]"
            )

            self.console.print(colored_status)
        else:
            print(status_text)

    @staticmethod
    def _format_duration(delta: timedelta) -> str:
        """Format duration as human-readable string.

        Args:
            delta: Time delta

        Returns:
            Formatted duration string (e.g., "2h 34m", "45s")
        """
        total_seconds = int(delta.total_seconds())

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours}h {minutes}m"
        if minutes > 0:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"

    @staticmethod
    def _make_progress_bar(percentage: int, width: int = 20) -> str:
        """Create ASCII progress bar.

        Args:
            percentage: Progress percentage (0-100)
            width: Bar width in characters

        Returns:
            Progress bar string (e.g., "▓▓▓▓▒▒▒▒▒▒")
        """
        filled = int((percentage / 100) * width)
        return "▓" * filled + "▒" * (width - filled)


__all__ = ["StatusLine"]
