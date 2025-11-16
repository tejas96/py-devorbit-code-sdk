"""Enhanced file tools with diff preview for CLI.

This module provides CLI-enhanced versions of file tools that show diffs
before applying changes, similar to Claude Code CLI's behavior.
"""

from pathlib import Path
from typing import Any

from .diff_engine import DiffEngine, DiffManager
from .diff_workflow import DiffWorkflow


class EnhancedFileTools:
    """Enhanced file tools with interactive diff preview."""

    def __init__(
        self,
        diff_engine: DiffEngine,
        enable_diff_preview: bool = True,
        auto_apply: bool = False,
    ):
        """Initialize enhanced file tools.

        Args:
            diff_engine: DiffEngine for generating diffs
            enable_diff_preview: Show diffs before applying changes
            auto_apply: Automatically apply changes without prompting
        """
        self.diff_engine = diff_engine
        self.enable_diff_preview = enable_diff_preview
        self.auto_apply = auto_apply
        self.diff_manager = DiffManager(diff_engine)
        self.diff_workflow = DiffWorkflow(
            self.diff_manager,
            console=diff_engine.console,
            no_color=diff_engine.no_color,
        )

    def preview_edit(
        self,
        file_path: str,
        old_content: str,
        new_content: str,
    ) -> dict[str, Any]:
        """Preview file edit with diff before applying.

        Args:
            file_path: Path to file
            old_content: Current file content
            new_content: New file content

        Returns:
            Result dictionary with 'applied', 'diff', 'action'
        """
        path = Path(file_path)

        # Generate diff
        file_diff = self.diff_engine.generate_diff(path, old_content, new_content)

        # Check if there are actual changes
        if not file_diff.diff_lines or len(file_diff.diff_lines) <= 2:
            # No changes (only headers)
            return {
                "applied": False,
                "diff": None,
                "action": "no_changes",
                "message": "No changes to apply",
            }

        # If diff preview disabled or auto-apply, just apply
        if not self.enable_diff_preview or self.auto_apply:
            self._apply_diff_directly(path, new_content)
            return {
                "applied": True,
                "diff": file_diff,
                "action": "auto_applied",
                "message": f"Applied changes to {file_path}",
            }

        # Show diff
        self.diff_engine.render_diff(file_diff)

        # Add to pending diffs
        self.diff_manager.clear_pending()
        self.diff_manager.add_diff(path, old_content, new_content)

        # Interactive review
        results = self.diff_workflow.review_and_apply(auto_apply=False)

        if results["applied"]:
            return {
                "applied": True,
                "diff": file_diff,
                "action": "user_applied",
                "message": f"Applied changes to {file_path}",
            }
        if results["rejected"]:
            return {
                "applied": False,
                "diff": file_diff,
                "action": "user_rejected",
                "message": f"Rejected changes to {file_path}",
            }

        return {
            "applied": False,
            "diff": file_diff,
            "action": "unknown",
            "message": "Diff review completed",
        }

    def preview_write(
        self,
        file_path: str,
        content: str,
    ) -> dict[str, Any]:
        """Preview file write with diff before applying.

        Args:
            file_path: Path to file
            content: Content to write

        Returns:
            Result dictionary
        """
        path = Path(file_path)

        # Check if file exists
        if path.exists():
            try:
                old_content = path.read_text(encoding="utf-8")
            except Exception:
                old_content = ""
        else:
            old_content = ""

        # Use preview_edit to handle diff
        return self.preview_edit(str(path), old_content, content)

    def _apply_diff_directly(self, file_path: Path, content: str) -> None:
        """Apply changes directly without confirmation.

        Args:
            file_path: Path to file
            content: New content
        """
        # Create backup if file exists
        if file_path.exists():
            self.diff_workflow._create_backup(file_path)

        # Write new content
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

    def get_pending_diffs_count(self) -> int:
        """Get number of pending diffs.

        Returns:
            Number of pending diffs
        """
        return self.diff_manager.get_pending_count()

    def clear_pending_diffs(self) -> None:
        """Clear all pending diffs."""
        self.diff_manager.clear_pending()

    def render_pending_summary(self) -> None:
        """Render summary of pending diffs."""
        self.diff_manager.render_summary()


__all__ = ["EnhancedFileTools"]
