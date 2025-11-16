"""Interactive diff engine with colored output.

This module provides diff generation and rendering similar to Claude Code CLI,
with apply/reject workflow for code changes.
"""

import difflib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.text import Text

    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    Console = None  # type: ignore[assignment, misc]
    Panel = None  # type: ignore[assignment, misc]
    Syntax = None  # type: ignore[assignment, misc]
    Text = None  # type: ignore[assignment, misc]


@dataclass
class DiffLine:
    """Represents a single line in a diff."""

    line_type: str  # 'add', 'remove', 'context', 'header'
    content: str
    old_line_num: int | None = None
    new_line_num: int | None = None


@dataclass
class FileDiff:
    """Represents a diff for a single file."""

    file_path: Path
    old_content: str
    new_content: str
    diff_lines: list[DiffLine]
    is_new_file: bool = False
    is_deleted: bool = False


class DiffEngine:
    """Generate and render diffs with colored output."""

    def __init__(self, console: Any | None = None, no_color: bool = False):
        """Initialize diff engine.

        Args:
            console: Rich console for output (optional)
            no_color: Disable colored output
        """
        self.console = console
        self.no_color = no_color

        # Initialize Rich console if available and not disabled
        if HAS_RICH and console is None and not no_color:
            self.console = Console()

    def generate_diff(
        self,
        file_path: Path,
        old_content: str,
        new_content: str,
    ) -> FileDiff:
        """Generate diff between old and new file content.

        Args:
            file_path: Path to the file
            old_content: Original file content
            new_content: New file content

        Returns:
            FileDiff object with diff information
        """
        # Check if file is new or deleted
        is_new_file = not old_content
        is_deleted = not new_content

        # Split into lines
        old_lines = old_content.splitlines(keepends=True) if old_content else []
        new_lines = new_content.splitlines(keepends=True) if new_content else []

        # Generate unified diff
        diff_lines: list[DiffLine] = []
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=str(file_path),
            tofile=str(file_path),
            lineterm="",
        )

        old_line_num = 0
        new_line_num = 0

        for line in diff:
            if line.startswith("---") or line.startswith("+++"):
                # File header
                diff_lines.append(
                    DiffLine(
                        line_type="header",
                        content=line,
                        old_line_num=None,
                        new_line_num=None,
                    )
                )
            elif line.startswith("@@"):
                # Hunk header
                diff_lines.append(
                    DiffLine(
                        line_type="header",
                        content=line,
                        old_line_num=None,
                        new_line_num=None,
                    )
                )
                # Parse line numbers from hunk header
                # Format: @@ -old_start,old_count +new_start,new_count @@
                parts = line.split()
                if len(parts) >= 2:
                    old_part = parts[1].lstrip("-")
                    new_part = parts[2].lstrip("+")
                    old_line_num = int(old_part.split(",")[0]) - 1
                    new_line_num = int(new_part.split(",")[0]) - 1
            elif line.startswith("-"):
                # Removed line
                old_line_num += 1
                diff_lines.append(
                    DiffLine(
                        line_type="remove",
                        content=line[1:],
                        old_line_num=old_line_num,
                        new_line_num=None,
                    )
                )
            elif line.startswith("+"):
                # Added line
                new_line_num += 1
                diff_lines.append(
                    DiffLine(
                        line_type="add",
                        content=line[1:],
                        old_line_num=None,
                        new_line_num=new_line_num,
                    )
                )
            else:
                # Context line
                old_line_num += 1
                new_line_num += 1
                content = line[1:] if line.startswith(" ") else line
                diff_lines.append(
                    DiffLine(
                        line_type="context",
                        content=content,
                        old_line_num=old_line_num,
                        new_line_num=new_line_num,
                    )
                )

        return FileDiff(
            file_path=file_path,
            old_content=old_content,
            new_content=new_content,
            diff_lines=diff_lines,
            is_new_file=is_new_file,
            is_deleted=is_deleted,
        )

    def render_diff(self, file_diff: FileDiff) -> None:
        """Render diff with colored output.

        Args:
            file_diff: FileDiff object to render
        """
        if HAS_RICH and self.console and not self.no_color:
            self._render_diff_rich(file_diff)
        else:
            self._render_diff_plain(file_diff)

    def _render_diff_rich(self, file_diff: FileDiff) -> None:
        """Render diff with Rich library (colored).

        Args:
            file_diff: FileDiff object to render
        """
        if not self.console:
            return

        # File header
        if file_diff.is_new_file:
            header = f"📄 New file: {file_diff.file_path}"
            style = "green bold"
        elif file_diff.is_deleted:
            header = f"🗑️  Deleted file: {file_diff.file_path}"
            style = "red bold"
        else:
            header = f"📝 Modified: {file_diff.file_path}"
            style = "yellow bold"

        self.console.print(f"\n{header}", style=style)
        self.console.print("─" * 80, style="dim")

        # Render diff lines
        for diff_line in file_diff.diff_lines:
            if diff_line.line_type == "header":
                # Hunk headers in cyan
                self.console.print(diff_line.content, style="cyan dim")
            elif diff_line.line_type == "add":
                # Added lines in green with + prefix
                text = Text()
                text.append("+", style="green bold")
                text.append(diff_line.content.rstrip(), style="green")
                self.console.print(text)
            elif diff_line.line_type == "remove":
                # Removed lines in red with - prefix
                text = Text()
                text.append("-", style="red bold")
                text.append(diff_line.content.rstrip(), style="red")
                self.console.print(text)
            else:
                # Context lines in dim white
                self.console.print(f" {diff_line.content.rstrip()}", style="dim")

        self.console.print("─" * 80, style="dim")

    def _render_diff_plain(self, file_diff: FileDiff) -> None:
        """Render diff without colors (plain text).

        Args:
            file_diff: FileDiff object to render
        """
        # File header
        if file_diff.is_new_file:
            print(f"\nNew file: {file_diff.file_path}")
        elif file_diff.is_deleted:
            print(f"\nDeleted file: {file_diff.file_path}")
        else:
            print(f"\nModified: {file_diff.file_path}")

        print("─" * 80)

        # Render diff lines
        for diff_line in file_diff.diff_lines:
            if diff_line.line_type == "add":
                print(f"+{diff_line.content.rstrip()}")
            elif diff_line.line_type == "remove":
                print(f"-{diff_line.content.rstrip()}")
            else:
                print(f" {diff_line.content.rstrip()}")

        print("─" * 80)

    def get_diff_stats(self, file_diff: FileDiff) -> dict[str, int]:
        """Get statistics about the diff.

        Args:
            file_diff: FileDiff object

        Returns:
            Dictionary with 'additions', 'deletions', 'changes' counts
        """
        additions = sum(1 for line in file_diff.diff_lines if line.line_type == "add")
        deletions = sum(1 for line in file_diff.diff_lines if line.line_type == "remove")

        return {
            "additions": additions,
            "deletions": deletions,
            "changes": additions + deletions,
        }

    def render_diff_summary(self, file_diff: FileDiff) -> None:
        """Render a summary of changes.

        Args:
            file_diff: FileDiff object
        """
        stats = self.get_diff_stats(file_diff)

        if HAS_RICH and self.console and not self.no_color:
            text = Text()
            text.append(f"{file_diff.file_path.name}: ", style="bold")
            text.append(f"+{stats['additions']}", style="green")
            text.append(" / ", style="dim")
            text.append(f"-{stats['deletions']}", style="red")
            self.console.print(text)
        else:
            print(f"{file_diff.file_path.name}: +{stats['additions']} / -{stats['deletions']}")


class DiffManager:
    """Manage multiple file diffs and apply/reject workflow."""

    def __init__(self, diff_engine: DiffEngine):
        """Initialize diff manager.

        Args:
            diff_engine: DiffEngine instance for rendering
        """
        self.diff_engine = diff_engine
        self.pending_diffs: list[FileDiff] = []

    def add_diff(
        self,
        file_path: Path,
        old_content: str,
        new_content: str,
    ) -> FileDiff:
        """Add a file diff to pending changes.

        Args:
            file_path: Path to the file
            old_content: Original content
            new_content: New content

        Returns:
            Generated FileDiff object
        """
        file_diff = self.diff_engine.generate_diff(file_path, old_content, new_content)
        self.pending_diffs.append(file_diff)
        return file_diff

    def get_pending_count(self) -> int:
        """Get number of pending diffs.

        Returns:
            Number of pending file diffs
        """
        return len(self.pending_diffs)

    def clear_pending(self) -> None:
        """Clear all pending diffs."""
        self.pending_diffs.clear()

    def render_all_diffs(self) -> None:
        """Render all pending diffs."""
        for file_diff in self.pending_diffs:
            self.diff_engine.render_diff(file_diff)

    def render_summary(self) -> None:
        """Render summary of all pending changes."""
        if not self.pending_diffs:
            print("No pending changes")
            return

        print(f"\n📊 Summary of {len(self.pending_diffs)} file(s) changed:\n")

        for file_diff in self.pending_diffs:
            self.diff_engine.render_diff_summary(file_diff)

        # Total stats
        total_additions = sum(
            self.diff_engine.get_diff_stats(fd)["additions"] for fd in self.pending_diffs
        )
        total_deletions = sum(
            self.diff_engine.get_diff_stats(fd)["deletions"] for fd in self.pending_diffs
        )

        print(f"\nTotal: +{total_additions} / -{total_deletions}")


__all__ = ["DiffEngine", "DiffLine", "DiffManager", "FileDiff"]
