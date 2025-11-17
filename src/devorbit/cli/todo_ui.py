"""Enhanced TODO UI panel with checkboxes and progress tracking."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from rich.live import Live

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
    from rich.table import Table
    from rich.text import Text

    HAS_RICH = True
except ImportError:
    HAS_RICH = False


class TodoUIPanel:
    """Interactive TODO panel with checkboxes and progress tracking."""

    def __init__(self, no_color: bool = False) -> None:
        """Initialize TODO UI panel.

        Args:
            no_color: Disable colored output
        """
        self.no_color = no_color
        self.console = Console(no_color=no_color) if HAS_RICH else None
        self.todos: list[dict[str, Any]] = []
        self.live_display: Live | None = None
        self.show_panel = True

    def set_todos(self, todos: list[dict[str, Any]]) -> None:
        """Set TODO items.

        Args:
            todos: List of TODO items with status
        """
        self.todos = todos

    def render_panel(self) -> Panel | None:
        """Render TODO panel with progress.

        Returns:
            Rich Panel object or None if Rich not available
        """
        if not HAS_RICH or self.console is None or not self.todos:
            return None

        # Create table for todos
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Status", width=3)
        table.add_column("Task", style="white")

        completed = 0
        in_progress = 0

        for todo in self.todos:
            status = todo.get("status", "pending")
            content = todo.get("content", "")

            # Status icon
            if status == "completed":
                icon = Text("☒", style="bold green")
                completed += 1
                text_style = "dim"
            elif status == "in_progress":
                icon = Text("☐", style="bold cyan")
                in_progress += 1
                text_style = "cyan"
            else:
                icon = Text("☐", style="white")
                text_style = "white"

            # Add row
            table.add_row(icon, Text(content, style=text_style))

        # Calculate progress
        total = len(self.todos)

        # Create panel title with progress
        title = f"[bold cyan]Todos[/bold cyan] [dim]({completed}/{total} completed)[/dim]"

        # Create panel
        return Panel(
            table,
            title=title,
            border_style="cyan",
            padding=(0, 1),
        )

    def display(self) -> None:
        """Display TODO panel."""
        if not HAS_RICH or self.console is None:
            # Fallback to plain text
            self._display_plain()
            return

        panel = self.render_panel()
        if panel:
            self.console.print(panel)

    def _display_plain(self) -> None:
        """Display TODO list in plain text."""
        if not self.todos:
            return

        print("\n─── Todos ───")
        for todo in self.todos:
            status = todo.get("status", "pending")
            content = todo.get("content", "")

            if status == "completed":
                print(f"  [✓] {content}")
            elif status == "in_progress":
                print(f"  [>] {content}")
            else:
                print(f"  [ ] {content}")
        print("─────────────\n")

    def display_progress_bar(self) -> None:
        """Display progress bar for current task."""
        if not HAS_RICH or self.console is None:
            return

        # Find in-progress task
        in_progress_task = next(
            (t for t in self.todos if t.get("status") == "in_progress"), None
        )

        if not in_progress_task:
            return

        # Create progress bar
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console,
        )

        # Calculate progress
        total = len(self.todos)
        completed = sum(1 for t in self.todos if t.get("status") == "completed")
        percentage = (completed / total * 100) if total > 0 else 0

        with progress:
            progress.add_task(
                in_progress_task.get("activeForm", "Working..."),
                total=100,
                completed=percentage,
            )

    def update_status(self, index: int, status: str) -> None:
        """Update TODO status.

        Args:
            index: Index of TODO item
            status: New status (pending, in_progress, completed)
        """
        if 0 <= index < len(self.todos):
            self.todos[index]["status"] = status
            if self.show_panel:
                self.display()

    def display_compact(self) -> None:
        """Display compact TODO list inline."""
        if not HAS_RICH or self.console is None or not self.todos:
            return

        # Only show in-progress and pending tasks
        active_todos = [
            t for t in self.todos if t.get("status") in ("in_progress", "pending")
        ]

        if not active_todos:
            return

        # Create compact text
        total = len(self.todos)
        completed = sum(1 for t in self.todos if t.get("status") == "completed")

        text = Text()
        text.append("(", style="dim")
        text.append(f"{completed}/{total}", style="cyan")
        text.append(" · ", style="dim")

        # Show first in-progress or pending task
        first_task = active_todos[0]
        status = first_task.get("status", "pending")

        if status == "in_progress":
            text.append("⚙ ", style="cyan")
            text.append(first_task.get("activeForm", ""), style="cyan")
        else:
            text.append(first_task.get("content", ""), style="white")

        if len(active_todos) > 1:
            text.append(f" +{len(active_todos) - 1} more", style="dim")

        text.append(")", style="dim")

        self.console.print(text)


class TodoProgressTracker:
    """Track and display TODO progress with animations."""

    def __init__(self, console: Console | None = None) -> None:
        """Initialize progress tracker.

        Args:
            console: Rich console instance
        """
        self.console = console or (Console() if HAS_RICH else None)
        self.current_progress: Progress | None = None
        self.current_task_id: Any = None

    def start_task(self, description: str, total: int = 100) -> None:
        """Start tracking a task.

        Args:
            description: Task description
            total: Total steps (default 100 for percentage)
        """
        if not HAS_RICH or self.console is None:
            print(f"⚙ {description}...")
            return

        self.current_progress = Progress(
            SpinnerColumn(),
            TextColumn("[cyan]{task.description}"),
            BarColumn(),
            TextColumn("[cyan]{task.percentage:>3.0f}%"),
            console=self.console,
        )

        self.current_progress.start()
        self.current_task_id = self.current_progress.add_task(description, total=total)

    def update(self, completed: int) -> None:
        """Update progress.

        Args:
            completed: Completed amount
        """
        if self.current_progress and self.current_task_id is not None:
            self.current_progress.update(self.current_task_id, completed=completed)

    def finish(self) -> None:
        """Finish tracking."""
        if self.current_progress:
            self.current_progress.stop()
            self.current_progress = None
            self.current_task_id = None


__all__ = ["TodoProgressTracker", "TodoUIPanel"]
