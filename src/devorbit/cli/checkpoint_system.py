"""Checkpoint and recovery system for rollback functionality.

This module provides checkpoint creation and restoration, along with crash recovery,
similar to Claude Code CLI's safety features.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .undo_system import ChangeTracker, Checkpoint, FileChange


class CheckpointManager:
    """Manage checkpoints for rollback."""

    def __init__(self, checkpoint_dir: Path | None = None):
        """Initialize checkpoint manager.

        Args:
            checkpoint_dir: Directory for checkpoints (default: .claude/checkpoints/)
        """
        self.checkpoint_dir = checkpoint_dir or Path(".claude/checkpoints")
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        self.checkpoints_file = self.checkpoint_dir / "checkpoints.json"
        self.checkpoints: list[Checkpoint] = []
        self.max_checkpoints = 50  # Keep last 50 checkpoints

        # Load existing checkpoints
        self._load_checkpoints()

    def create_checkpoint(
        self,
        name: str,
        description: str = "",
        changes: list[FileChange] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Checkpoint:
        """Create a new checkpoint.

        Args:
            name: Checkpoint name
            description: Checkpoint description
            changes: List of changes to include
            metadata: Additional metadata

        Returns:
            Created Checkpoint object
        """
        checkpoint_id = str(uuid4())

        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            name=name,
            timestamp=datetime.now(),
            description=description,
            changes=changes or [],
            metadata=metadata or {},
        )

        # Save checkpoint data to separate file
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"
        with checkpoint_file.open("w", encoding="utf-8") as f:
            json.dump(checkpoint.to_dict(), f, indent=2)

        # Add to list
        self.checkpoints.append(checkpoint)

        # Trim old checkpoints
        if len(self.checkpoints) > self.max_checkpoints:
            removed = self.checkpoints[: len(self.checkpoints) - self.max_checkpoints]
            self.checkpoints = self.checkpoints[-self.max_checkpoints :]

            # Clean up old checkpoint files
            for old_cp in removed:
                cp_file = self.checkpoint_dir / f"{old_cp.checkpoint_id}.json"
                if cp_file.exists():
                    cp_file.unlink()

        # Save checkpoint list
        self._save_checkpoints()

        return checkpoint

    def get_checkpoint(self, checkpoint_id: str) -> Checkpoint | None:
        """Get a checkpoint by ID.

        Args:
            checkpoint_id: Checkpoint ID

        Returns:
            Checkpoint object or None if not found
        """
        for checkpoint in self.checkpoints:
            if checkpoint.checkpoint_id == checkpoint_id:
                return checkpoint
        return None

    def list_checkpoints(self) -> list[Checkpoint]:
        """List all checkpoints.

        Returns:
            List of Checkpoint objects
        """
        return self.checkpoints

    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint.

        Args:
            checkpoint_id: Checkpoint ID

        Returns:
            True if deleted, False if not found
        """
        checkpoint = self.get_checkpoint(checkpoint_id)
        if not checkpoint:
            return False

        # Remove from list
        self.checkpoints.remove(checkpoint)

        # Delete checkpoint file
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"
        if checkpoint_file.exists():
            checkpoint_file.unlink()

        # Save updated list
        self._save_checkpoints()

        return True

    def rollback_to_checkpoint(self, checkpoint_id: str) -> Checkpoint:
        """Rollback to a specific checkpoint.

        Args:
            checkpoint_id: Checkpoint ID to rollback to

        Returns:
            Checkpoint that was restored

        Raises:
            ValueError: If checkpoint not found
            RuntimeError: If rollback fails
        """
        checkpoint = self.get_checkpoint(checkpoint_id)
        if not checkpoint:
            raise ValueError(f"Checkpoint not found: {checkpoint_id}")

        # Restore each change in reverse order
        for change in reversed(checkpoint.changes):
            try:
                self._restore_change(change)
            except Exception as e:
                raise RuntimeError(f"Failed to restore change {change.change_id}: {e}") from e

        return checkpoint

    def _restore_change(self, change: FileChange) -> None:
        """Restore a file change.

        Args:
            change: FileChange to restore

        Raises:
            RuntimeError: If restore fails
        """
        # Restore to the state captured in the change
        if change.backup_path and change.backup_path.exists():
            # Restore from backup
            change.file_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(change.backup_path, change.file_path)
        elif change.old_content is not None:
            # Restore from old content
            change.file_path.parent.mkdir(parents=True, exist_ok=True)
            change.file_path.write_text(change.old_content, encoding="utf-8")

    def _load_checkpoints(self) -> None:
        """Load checkpoints from disk."""
        if not self.checkpoints_file.exists():
            return

        try:
            with self.checkpoints_file.open(encoding="utf-8") as f:
                data = json.load(f)

            # Load checkpoint metadata (changes are in separate files)
            self.checkpoints = []
            for cp_data in data:
                checkpoint_id = cp_data["checkpoint_id"]
                checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"

                if checkpoint_file.exists():
                    with checkpoint_file.open(encoding="utf-8") as cf:
                        full_data = json.load(cf)
                    self.checkpoints.append(Checkpoint.from_dict(full_data))

        except Exception:
            # If loading fails, start fresh
            self.checkpoints = []

    def _save_checkpoints(self) -> None:
        """Save checkpoint list to disk."""
        try:
            # Save lightweight metadata list
            with self.checkpoints_file.open("w", encoding="utf-8") as f:
                data = [
                    {
                        "checkpoint_id": cp.checkpoint_id,
                        "name": cp.name,
                        "timestamp": cp.timestamp.isoformat(),
                        "description": cp.description,
                    }
                    for cp in self.checkpoints
                ]
                json.dump(data, f, indent=2)
        except Exception:
            pass  # Ignore save errors


class RecoveryManager:
    """Manage crash recovery and session restoration."""

    def __init__(self, recovery_dir: Path | None = None):
        """Initialize recovery manager.

        Args:
            recovery_dir: Directory for recovery data (default: .claude/recovery/)
        """
        self.recovery_dir = recovery_dir or Path(".claude/recovery")
        self.recovery_dir.mkdir(parents=True, exist_ok=True)

        self.session_file = self.recovery_dir / "session.json"
        self.auto_checkpoint_file = self.recovery_dir / "auto_checkpoint.json"

    def save_session_state(self, state: dict[str, Any]) -> None:
        """Save current session state for recovery.

        Args:
            state: Session state dictionary
        """
        state_with_timestamp = {
            **state,
            "saved_at": datetime.now().isoformat(),
        }

        try:
            with self.session_file.open("w", encoding="utf-8") as f:
                json.dump(state_with_timestamp, f, indent=2)
        except Exception:
            pass  # Ignore save errors

    def load_session_state(self) -> dict[str, Any] | None:
        """Load saved session state.

        Returns:
            Session state dictionary or None if not found
        """
        if not self.session_file.exists():
            return None

        try:
            with self.session_file.open(encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def clear_session_state(self) -> None:
        """Clear saved session state."""
        if self.session_file.exists():
            self.session_file.unlink()

    def create_auto_checkpoint(
        self,
        checkpoint_manager: CheckpointManager,
        change_tracker: ChangeTracker,
    ) -> Checkpoint:
        """Create automatic checkpoint before risky operations.

        Args:
            checkpoint_manager: CheckpointManager instance
            change_tracker: ChangeTracker instance

        Returns:
            Created Checkpoint
        """
        # Get recent changes
        recent_changes = change_tracker.get_recent_changes(count=20)

        # Create auto checkpoint
        checkpoint = checkpoint_manager.create_checkpoint(
            name=f"auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            description="Automatic checkpoint before operation",
            changes=recent_changes,
            metadata={"auto": True},
        )

        # Save auto checkpoint reference
        try:
            with self.auto_checkpoint_file.open("w", encoding="utf-8") as f:
                json.dump({"checkpoint_id": checkpoint.checkpoint_id}, f)
        except Exception:
            pass

        return checkpoint

    def get_last_auto_checkpoint(
        self,
        checkpoint_manager: CheckpointManager,
    ) -> Checkpoint | None:
        """Get last automatic checkpoint.

        Args:
            checkpoint_manager: CheckpointManager instance

        Returns:
            Last auto checkpoint or None
        """
        if not self.auto_checkpoint_file.exists():
            return None

        try:
            with self.auto_checkpoint_file.open(encoding="utf-8") as f:
                data = json.load(f)
            checkpoint_id = data.get("checkpoint_id")
            if checkpoint_id:
                return checkpoint_manager.get_checkpoint(checkpoint_id)
        except Exception:
            pass

        return None

    def has_pending_recovery(self) -> bool:
        """Check if there's a pending recovery state.

        Returns:
            True if recovery data exists
        """
        return self.session_file.exists()


__all__ = ["CheckpointManager", "RecoveryManager"]
