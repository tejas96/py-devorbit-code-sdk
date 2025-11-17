"""File write preview and confirmation system."""

from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.syntax import Syntax
    from rich.table import Table
    from rich.text import Text

    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    Progress = None  # type: ignore[assignment, misc]
    SpinnerColumn = None  # type: ignore[assignment, misc]
    TextColumn = None  # type: ignore[assignment, misc]


class FilePreviewConfirmation:
    """Interactive file write confirmation with preview."""

    def __init__(self, no_color: bool = False, auto_confirm: bool = False) -> None:
        """Initialize file preview confirmation.

        Args:
            no_color: Disable colored output
            auto_confirm: Auto-confirm all writes
        """
        self.no_color = no_color
        self.auto_confirm = auto_confirm
        self.console = Console(no_color=no_color) if HAS_RICH else None
        self.session_allow_all = False

    def confirm_write(
        self, file_path: Path, content: str, is_new: bool = True
    ) -> tuple[bool, str]:
        """Confirm file write with preview.

        Args:
            file_path: Path to file
            content: Content to write
            is_new: Whether this is a new file

        Returns:
            Tuple of (confirmed, action) where action is one of:
            'yes', 'yes_all', 'no', 'skip'
        """
        # Auto-confirm if enabled
        if self.auto_confirm or self.session_allow_all:
            return True, "yes_all"

        # Display preview
        self.display_preview(file_path, content, is_new)

        # Ask for confirmation
        return self.prompt_confirmation(file_path, is_new)

    def display_preview(self, file_path: Path, content: str, is_new: bool) -> None:
        """Display file write preview.

        Args:
            file_path: Path to file
            content: Content to write
            is_new: Whether this is a new file
        """
        if not HAS_RICH or self.console is None:
            self._display_plain_preview(file_path, content, is_new)
            return

        # Count lines
        lines = content.splitlines()
        line_count = len(lines)

        # Truncate content if too long
        max_preview_lines = 50
        if line_count > max_preview_lines:
            preview_content = "\n".join(lines[:max_preview_lines])
            preview_content += f"\n\n... ({line_count - max_preview_lines} more lines)"
        else:
            preview_content = content

        # Determine language for syntax highlighting
        ext = file_path.suffix.lower()
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "jsx",
            ".tsx": "tsx",
            ".html": "html",
            ".css": "css",
            ".scss": "scss",
            ".json": "json",
            ".md": "markdown",
            ".yml": "yaml",
            ".yaml": "yaml",
            ".toml": "toml",
            ".sh": "bash",
            ".sql": "sql",
            ".xml": "xml",
        }
        language = language_map.get(ext, "text")

        # Create syntax-highlighted preview
        syntax = Syntax(
            preview_content,
            language,
            theme="monokai",
            line_numbers=True,
            word_wrap=False,
        )

        # File status
        status = "Create file" if is_new else "Modify file"
        status_style = "green" if is_new else "yellow"

        # Create panel
        panel = Panel(
            syntax,
            title=f"[{status_style}]{status}[/{status_style}]",
            subtitle=f"[bold cyan]{file_path}[/bold cyan]",
            border_style=status_style,
            padding=(0, 1),
        )

        self.console.print()
        self.console.print(panel)

    def _display_plain_preview(self, file_path: Path, content: str, is_new: bool) -> None:
        """Display preview in plain text.

        Args:
            file_path: Path to file
            content: Content to write
            is_new: Whether this is a new file
        """
        status = "CREATE" if is_new else "MODIFY"
        print(f"\n─── {status}: {file_path} ───")

        lines = content.splitlines()
        max_lines = 20

        for i, line in enumerate(lines[:max_lines]):
            print(f"{i + 1:4d} │ {line}")

        if len(lines) > max_lines:
            print(f"     │ ... ({len(lines) - max_lines} more lines)")

        print("─" * 80)

    def prompt_confirmation(self, file_path: Path, is_new: bool) -> tuple[bool, str]:
        """Prompt user for confirmation.

        Args:
            file_path: Path to file
            is_new: Whether this is a new file

        Returns:
            Tuple of (confirmed, action)
        """
        if not HAS_RICH or self.console is None:
            return self._prompt_plain(file_path, is_new)

        # Create options panel
        question = f"Do you want to {'create' if is_new else 'modify'} {file_path.name}?"

        options_table = Table(show_header=False, box=None, padding=(0, 1))
        options_table.add_column("Option", style="cyan")
        options_table.add_column("Description", style="white")

        options_table.add_row("> 1.", "Yes")
        options_table.add_row("  2.", "Yes, allow all edits during this session (shift+tab)")
        options_table.add_row("  3.", "No, and tell Claude what to do differently (esc)")

        self.console.print(
            Panel(
                options_table,
                title=question,
                border_style="cyan",
                padding=(0, 1),
            )
        )

        # Get choice
        try:
            choice = self.console.input("[cyan]Choose [1/2/3]:[/cyan] ").strip()

            if choice in ("1", ""):
                return True, "yes"
            if choice == "2":
                self.session_allow_all = True
                return True, "yes_all"
            return False, "no"

        except (KeyboardInterrupt, EOFError):
            return False, "no"

    def _prompt_plain(self, file_path: Path, is_new: bool) -> tuple[bool, str]:
        """Plain text confirmation prompt.

        Args:
            file_path: Path to file
            is_new: Whether this is a new file

        Returns:
            Tuple of (confirmed, action)
        """
        action = "create" if is_new else "modify"
        print(f"\nDo you want to {action} {file_path.name}?")
        print("  1. Yes")
        print("  2. Yes, allow all")
        print("  3. No")

        try:
            choice = input("Choose [1/2/3]: ").strip()

            if choice in ("1", ""):
                return True, "yes"
            if choice == "2":
                self.session_allow_all = True
                return True, "yes_all"
            return False, "no"

        except (KeyboardInterrupt, EOFError):
            return False, "no"

    def display_write_result(
        self, file_path: Path, success: bool, line_count: int = 0
    ) -> None:
        """Display write result.

        Args:
            file_path: Path to file
            success: Whether write succeeded
            line_count: Number of lines written
        """
        if not HAS_RICH or self.console is None:
            if success:
                print(f"✓ Wrote {line_count} lines to {file_path}")
            else:
                print(f"✗ Failed to write {file_path}")
            return

        if success:
            text = Text()
            text.append("⎿ ", style="dim")
            text.append("Wrote ", style="green")
            text.append(f"{line_count} lines", style="bold green")
            text.append(" to ", style="green")
            text.append(str(file_path), style="bold cyan")
            self.console.print(text)
        else:
            text = Text()
            text.append("✗ ", style="bold red")
            text.append(f"Failed to write {file_path}", style="red")
            self.console.print(text)


class StreamingFileWriter:
    """Write files with streaming progress animation."""

    def __init__(self, console: Console | None = None) -> None:
        """Initialize streaming file writer.

        Args:
            console: Rich console instance
        """
        self.console = console or (Console() if HAS_RICH else None)

    def write_with_animation(
        self, file_path: Path, content: str, show_progress: bool = True
    ) -> bool:
        """Write file with progress animation.

        Args:
            file_path: Path to file
            content: Content to write
            show_progress: Show progress animation

        Returns:
            True if successful
        """
        if not HAS_RICH or self.console is None or not show_progress:
            # Plain write
            try:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content)
                return True
            except Exception:
                return False

        try:
            # Show writing animation
            if not Progress or not SpinnerColumn or not TextColumn:
                raise ImportError("Rich progress components not available")

            with Progress(
                SpinnerColumn(),
                TextColumn("[cyan]Writing {task.description}..."),
                console=self.console,
            ) as progress:
                task = progress.add_task(file_path.name, total=1)

                # Create directory
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # Write file
                file_path.write_text(content)

                progress.update(task, completed=1)

            return True

        except Exception:
            return False


__all__ = ["FilePreviewConfirmation", "StreamingFileWriter"]
