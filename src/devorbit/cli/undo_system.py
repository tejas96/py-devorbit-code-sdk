"""Change tracking and undo/rollback system.

This module provides comprehensive change tracking with undo/rollback capabilities,
similar to Claude Code CLI's safety features.
"""

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class ChangeType(Enum):
    """Type of file change."""

    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    RENAME = "rename"


@dataclass
class FileChange:
    """Represents a single file change."""

    change_id: str
    change_type: ChangeType
    file_path: Path
    timestamp: datetime
    old_content: str | None = None
    new_content: str | None = None
    old_path: Path | None = None  # For renames
    backup_path: Path | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation
        """
        return {
            "change_id": self.change_id,
            "change_type": self.change_type.value,
            "file_path": str(self.file_path),
            "timestamp": self.timestamp.isoformat(),
            "old_content": self.old_content,
            "new_content": self.new_content,
            "old_path": str(self.old_path) if self.old_path else None,
            "backup_path": str(self.backup_path) if self.backup_path else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FileChange":
        """Create from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            FileChange instance
        """
        return cls(
            change_id=data["change_id"],
            change_type=ChangeType(data["change_type"]),
            file_path=Path(data["file_path"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            old_content=data.get("old_content"),
            new_content=data.get("new_content"),
            old_path=Path(data["old_path"]) if data.get("old_path") else None,
            backup_path=Path(data["backup_path"]) if data.get("backup_path") else None,
            metadata=data.get("metadata", {}),
        )


@dataclass
class Checkpoint:
    """Represents a checkpoint in change history."""

    checkpoint_id: str
    name: str
    timestamp: datetime
    description: str
    changes: list[FileChange] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "checkpoint_id": self.checkpoint_id,
            "name": self.name,
            "timestamp": self.timestamp.isoformat(),
            "description": self.description,
            "changes": [change.to_dict() for change in self.changes],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Checkpoint":
        """Create from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            Checkpoint instance
        """
        return cls(
            checkpoint_id=data["checkpoint_id"],
            name=data["name"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            description=data["description"],
            changes=[FileChange.from_dict(c) for c in data.get("changes", [])],
            metadata=data.get("metadata", {}),
        )


class ChangeTracker:
    """Track all file changes for undo/rollback."""

    def __init__(self, history_dir: Path | None = None):
        """Initialize change tracker.

        Args:
            history_dir: Directory for change history (default: .claude/history/)
        """
        self.history_dir = history_dir or Path(".claude/history")
        self.history_dir.mkdir(parents=True, exist_ok=True)

        self.changes_file = self.history_dir / "changes.json"
        self.changes: list[FileChange] = []
        self.max_history = 100  # Keep last 100 changes

        # Load existing changes
        self._load_changes()

    def track_change(
        self,
        change_type: ChangeType,
        file_path: Path,
        old_content: str | None = None,
        new_content: str | None = None,
        old_path: Path | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> FileChange:
        """Track a file change.

        Args:
            change_type: Type of change
            file_path: Path to file
            old_content: Original content (for modify/delete)
            new_content: New content (for create/modify)
            old_path: Original path (for rename)
            metadata: Additional metadata

        Returns:
            FileChange object
        """
        # Generate change ID
        change_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        # Create backup for old content
        backup_path = None
        if old_content is not None:
            backup_path = self.history_dir / f"backup_{change_id}_{file_path.name}"
            backup_path.write_text(old_content, encoding="utf-8")

        # Create change record
        change = FileChange(
            change_id=change_id,
            change_type=change_type,
            file_path=file_path,
            timestamp=datetime.now(),
            old_content=old_content,
            new_content=new_content,
            old_path=old_path,
            backup_path=backup_path,
            metadata=metadata or {},
        )

        # Add to history
        self.changes.append(change)

        # Trim history if needed
        if len(self.changes) > self.max_history:
            removed = self.changes[: len(self.changes) - self.max_history]
            self.changes = self.changes[-self.max_history :]

            # Clean up old backups
            for old_change in removed:
                if old_change.backup_path and old_change.backup_path.exists():
                    old_change.backup_path.unlink()

        # Save changes
        self._save_changes()

        return change

    def get_recent_changes(self, count: int = 10) -> list[FileChange]:
        """Get recent changes.

        Args:
            count: Number of recent changes to return

        Returns:
            List of recent FileChange objects
        """
        return self.changes[-count:]

    def get_changes_for_file(self, file_path: Path) -> list[FileChange]:
        """Get all changes for a specific file.

        Args:
            file_path: Path to file

        Returns:
            List of FileChange objects for the file
        """
        return [c for c in self.changes if c.file_path == file_path]

    def clear_history(self) -> None:
        """Clear all change history."""
        # Remove backup files
        for change in self.changes:
            if change.backup_path and change.backup_path.exists():
                change.backup_path.unlink()

        # Clear changes
        self.changes.clear()
        self._save_changes()

    def _load_changes(self) -> None:
        """Load changes from disk."""
        if not self.changes_file.exists():
            return

        try:
            with self.changes_file.open(encoding="utf-8") as f:
                data = json.load(f)

            self.changes = [FileChange.from_dict(c) for c in data]
        except Exception:
            # If loading fails, start fresh
            self.changes = []

    def _save_changes(self) -> None:
        """Save changes to disk."""
        try:
            with self.changes_file.open("w", encoding="utf-8") as f:
                data = [change.to_dict() for change in self.changes]
                json.dump(data, f, indent=2)
        except Exception:
            pass  # Ignore save errors


class UndoManager:
    """Manage undo operations for file changes."""

    def __init__(self, change_tracker: ChangeTracker):
        """Initialize undo manager.

        Args:
            change_tracker: ChangeTracker instance
        """
        self.change_tracker = change_tracker

    def undo_last(self, count: int = 1) -> list[FileChange]:
        """Undo the last N changes.

        Args:
            count: Number of changes to undo

        Returns:
            List of undone FileChange objects

        Raises:
            ValueError: If not enough changes to undo
        """
        if len(self.change_tracker.changes) < count:
            raise ValueError(
                f"Not enough changes to undo. Have {len(self.change_tracker.changes)}, need {count}"
            )

        # Get changes to undo (in reverse order)
        changes_to_undo = self.change_tracker.changes[-count:][::-1]
        undone: list[FileChange] = []

        for change in changes_to_undo:
            try:
                self._undo_change(change)
                undone.append(change)
            except Exception as e:
                # Stop on first error
                raise RuntimeError(f"Failed to undo change {change.change_id}: {e}") from e

        # Remove undone changes from history
        self.change_tracker.changes = self.change_tracker.changes[:-count]
        self.change_tracker._save_changes()

        return undone

    def undo_file(self, file_path: Path, count: int = 1) -> list[FileChange]:
        """Undo last N changes for a specific file.

        Args:
            file_path: Path to file
            count: Number of changes to undo for this file

        Returns:
            List of undone FileChange objects

        Raises:
            ValueError: If not enough changes for file
        """
        file_changes = self.change_tracker.get_changes_for_file(file_path)

        if len(file_changes) < count:
            raise ValueError(
                f"Not enough changes for {file_path}. Have {len(file_changes)}, need {count}"
            )

        # Get last N changes for file
        changes_to_undo = file_changes[-count:][::-1]
        undone: list[FileChange] = []

        for change in changes_to_undo:
            try:
                self._undo_change(change)
                undone.append(change)

                # Remove from tracker
                self.change_tracker.changes.remove(change)
            except Exception as e:
                raise RuntimeError(f"Failed to undo change {change.change_id}: {e}") from e

        self.change_tracker._save_changes()

        return undone

    def _undo_change(self, change: FileChange) -> None:
        """Undo a single change.

        Args:
            change: FileChange to undo

        Raises:
            RuntimeError: If undo operation fails
        """
        if change.change_type == ChangeType.CREATE:
            # Undo create: delete the file
            if change.file_path.exists():
                change.file_path.unlink()

        elif change.change_type == ChangeType.MODIFY:
            # Undo modify: restore old content
            if change.old_content is not None:
                change.file_path.write_text(change.old_content, encoding="utf-8")
            elif change.backup_path and change.backup_path.exists():
                # Restore from backup
                shutil.copy2(change.backup_path, change.file_path)

        elif change.change_type == ChangeType.DELETE:
            # Undo delete: restore old content
            if change.old_content is not None:
                change.file_path.parent.mkdir(parents=True, exist_ok=True)
                change.file_path.write_text(change.old_content, encoding="utf-8")
            elif change.backup_path and change.backup_path.exists():
                # Restore from backup
                change.file_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(change.backup_path, change.file_path)

        elif (
            change.change_type == ChangeType.RENAME
            and change.old_path
            and change.file_path.exists()
        ):
            # Undo rename: restore original path
            change.file_path.rename(change.old_path)


__all__ = ["ChangeTracker", "ChangeType", "Checkpoint", "FileChange", "UndoManager"]
