"""Interactive diff workflow with apply/reject options.

This module provides an interactive workflow for reviewing and applying diffs,
similar to Claude Code CLI's change review system.
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from .diff_engine import DiffManager, FileDiff
from .interactive_prompt import InteractivePrompt


try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Confirm, Prompt
    from rich.text import Text

    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    Console = None  # type: ignore[assignment, misc]
    Panel = None  # type: ignore[assignment, misc]
    Confirm = None  # type: ignore[assignment, misc]
    Prompt = None  # type: ignore[assignment, misc]
    Text = None  # type: ignore[assignment, misc]


class DiffWorkflow:
    """Interactive workflow for reviewing and applying diffs."""

    def __init__(
        self,
        diff_manager: DiffManager,
        console: Any | None = None,
        no_color: bool = False,
        backup_dir: Path | None = None,
    ):
        """Initialize diff workflow.

        Args:
            diff_manager: DiffManager instance
            console: Rich console for output
            no_color: Disable colored output
            backup_dir: Directory for file backups (default: .claude/backups/)
        """
        self.diff_manager = diff_manager
        self.console = console
        self.no_color = no_color
        self.backup_dir = backup_dir or Path(".claude/backups")

        # Initialize Rich console if available
        if HAS_RICH and console is None and not no_color:
            self.console = Console()

        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def review_and_apply(self, auto_apply: bool = False) -> dict[str, Any]:
        """Review all pending diffs and apply/reject them.

        Args:
            auto_apply: If True, automatically apply all changes without prompting

        Returns:
            Dictionary with results: applied, rejected, errors
        """
        results: dict[str, Any] = {
            "applied": [],
            "rejected": [],
            "errors": [],
        }

        if not self.diff_manager.pending_diffs:
            self._print("No pending changes to review")
            return results

        # Show summary
        self._print_header(f"Reviewing {len(self.diff_manager.pending_diffs)} file(s)")
        self.diff_manager.render_summary()
        print()

        if auto_apply:
            # Apply all without prompting
            for file_diff in self.diff_manager.pending_diffs:
                try:
                    self._apply_diff(file_diff)
                    results["applied"].append(str(file_diff.file_path))
                except Exception as e:
                    results["errors"].append({"file": str(file_diff.file_path), "error": str(e)})
        else:
            # Interactive review
            for i, file_diff in enumerate(self.diff_manager.pending_diffs, 1):
                self._print(
                    f"\n{'=' * 80}\n[{i}/{len(self.diff_manager.pending_diffs)}] Reviewing changes\n{'=' * 80}"
                )

                # Render diff
                self.diff_manager.diff_engine.render_diff(file_diff)

                # Prompt for action
                action = self._prompt_action(file_diff)

                if action == "apply":
                    try:
                        self._apply_diff(file_diff)
                        results["applied"].append(str(file_diff.file_path))
                        self._print_success(f"✅ Applied changes to {file_diff.file_path}")
                    except Exception as e:
                        results["errors"].append(
                            {"file": str(file_diff.file_path), "error": str(e)}
                        )
                        self._print_error(f"❌ Error applying changes: {e}")
                elif action == "reject":
                    results["rejected"].append(str(file_diff.file_path))
                    self._print("⏭️  Skipped {file_diff.file_path}")
                elif action == "skip":
                    # Skip for now, keep in pending
                    pass

        # Clear applied/rejected diffs
        self.diff_manager.clear_pending()

        return results

    def _prompt_action(self, file_diff: FileDiff) -> str:
        """Prompt user for action on a diff with arrow-key selection.

        Args:
            file_diff: FileDiff to review

        Returns:
            Action: 'apply', 'reject', or 'skip'
        """
        while True:
            # Show interactive selection with arrow keys
            choice = InteractivePrompt.select(
                message="What would you like to do?",
                choices=[
                    ("✓ Apply changes", "apply"),
                    ("✗ Reject changes", "reject"),
                    ("⏭  Skip (review later)", "skip"),
                    ("👁  View diff again", "view"),
                ],
                default="apply",
            )

            # Handle view option
            if choice == "view":
                self.diff_manager.diff_engine.render_diff(file_diff)
                continue

            return choice

    def _apply_diff(self, file_diff: FileDiff) -> None:
        """Apply a file diff.

        Args:
            file_diff: FileDiff to apply

        Raises:
            Exception: If file operation fails
        """
        # Create backup before modifying
        if file_diff.file_path.exists() and not file_diff.is_new_file:
            self._create_backup(file_diff.file_path)

        # Handle deleted files
        if file_diff.is_deleted:
            if file_diff.file_path.exists():
                file_diff.file_path.unlink()
            return

        # Write new content
        file_diff.file_path.parent.mkdir(parents=True, exist_ok=True)
        file_diff.file_path.write_text(file_diff.new_content, encoding="utf-8")

    def _create_backup(self, file_path: Path) -> Path:
        """Create backup of a file before modification.

        Args:
            file_path: Path to file to backup

        Returns:
            Path to backup file
        """
        # Create timestamp-based backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.name}.{timestamp}.backup"
        backup_path = self.backup_dir / backup_name

        # Copy file to backup
        shutil.copy2(file_path, backup_path)

        return backup_path

    def _print(self, message: str) -> None:
        """Print a message.

        Args:
            message: Message to print
        """
        if HAS_RICH and self.console and not self.no_color:
            self.console.print(message)
        else:
            print(message)

    def _print_header(self, message: str) -> None:
        """Print a header message.

        Args:
            message: Header message
        """
        if HAS_RICH and self.console and not self.no_color:
            self.console.print(f"\n{message}", style="bold cyan")
            self.console.print("═" * len(message), style="cyan")
        else:
            print(f"\n{message}")
            print("=" * len(message))

    def _print_success(self, message: str) -> None:
        """Print a success message.

        Args:
            message: Success message
        """
        if HAS_RICH and self.console and not self.no_color:
            self.console.print(message, style="green")
        else:
            print(message)

    def _print_error(self, message: str) -> None:
        """Print an error message.

        Args:
            message: Error message
        """
        if HAS_RICH and self.console and not self.no_color:
            self.console.print(message, style="red bold")
        else:
            print(f"ERROR: {message}")


class SafeFileWriter:
    """Safe file writing with atomic operations and backups."""

    def __init__(self, backup_dir: Path | None = None):
        """Initialize safe file writer.

        Args:
            backup_dir: Directory for backups
        """
        self.backup_dir = backup_dir or Path(".claude/backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def write_file(
        self,
        file_path: Path,
        content: str,
        create_backup: bool = True,
    ) -> Path | None:
        """Write file safely with optional backup.

        Args:
            file_path: Path to file
            content: Content to write
            create_backup: Create backup before writing

        Returns:
            Path to backup file if created, None otherwise

        Raises:
            Exception: If write operation fails
        """
        backup_path = None

        # Create backup if file exists
        if create_backup and file_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.name}.{timestamp}.backup"
            backup_path = self.backup_dir / backup_name
            shutil.copy2(file_path, backup_path)

        try:
            # Write to temporary file first
            temp_path = file_path.parent / f".{file_path.name}.tmp"
            temp_path.write_text(content, encoding="utf-8")

            # Atomic move (on same filesystem)
            temp_path.replace(file_path)

            return backup_path

        except Exception as e:
            # Restore from backup if write failed
            if backup_path and backup_path.exists():
                shutil.copy2(backup_path, file_path)
            raise e


__all__ = ["DiffWorkflow", "SafeFileWriter"]
