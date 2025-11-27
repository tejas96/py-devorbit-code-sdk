"""Session persistence and backup system for Devorbit CLI.

This module provides:
- SessionState: Serializable session state
- SessionPersistence: Save/load session state
- BackupManager: Auto-backup before file changes
- FileCheckpoint: Snapshot files before modification

Usage:
    from devorbit.cli.core.persistence import SessionPersistence, BackupManager

    # Session persistence
    persistence = SessionPersistence()
    persistence.save_session(session_state)
    restored = persistence.load_session()

    # Backup manager
    backup = BackupManager(working_dir)
    checkpoint = backup.create_checkpoint("edit_file.py")
    try:
        modify_file()
    except Exception:
        backup.restore_checkpoint(checkpoint)
"""

from __future__ import annotations

import contextlib
from dataclasses import asdict, dataclass, field
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
import time
from typing import Any


@dataclass
class SessionState:
    """Serializable session state.

    Contains all information needed to restore a CLI session.
    """

    # Session metadata
    session_id: str
    created_at: float
    updated_at: float

    # Provider configuration
    provider: str
    model: str | None

    # Working directory
    working_dir: str

    # Conversation history (serializable format)
    messages: list[dict[str, Any]]

    # Session flags
    planning_mode: bool = False
    debug: bool = False

    # Custom session data
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        """Serialize to JSON string.

        Returns:
            JSON string representation
        """
        return json.dumps(asdict(self), indent=2, default=str)

    @classmethod
    def from_json(cls, json_str: str) -> SessionState:
        """Deserialize from JSON string.

        Args:
            json_str: JSON string

        Returns:
            SessionState instance
        """
        data = json.loads(json_str)
        return cls(**data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionState:
        """Create from dictionary.

        Args:
            data: Dictionary data

        Returns:
            SessionState instance
        """
        return cls(**data)


@dataclass
class FileCheckpoint:
    """Checkpoint for a single file."""

    file_path: Path
    content: bytes | None
    existed: bool
    checksum: str
    created_at: float = field(default_factory=time.time)

    def matches_current(self) -> bool:
        """Check if file still matches checkpoint.

        Returns:
            True if file matches checkpoint
        """
        if not self.file_path.exists():
            return not self.existed

        if not self.existed:
            return False

        current_content = self.file_path.read_bytes()
        current_checksum = hashlib.sha256(current_content).hexdigest()
        return current_checksum == self.checksum


class SessionPersistence:
    """Handles session save/load operations.

    Sessions are stored in ~/.devorbit/sessions/
    """

    def __init__(self, base_dir: Path | None = None) -> None:
        """Initialize session persistence.

        Args:
            base_dir: Base directory for session storage
        """
        self.base_dir = base_dir or (Path.home() / ".devorbit" / "sessions")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _session_file(self, session_id: str) -> Path:
        """Get path to session file.

        Args:
            session_id: Session identifier

        Returns:
            Path to session file
        """
        # Sanitize session_id to prevent path traversal
        safe_id = "".join(c for c in session_id if c.isalnum() or c in "-_")
        return self.base_dir / f"{safe_id}.json"

    def save_session(self, state: SessionState) -> Path:
        """Save session state to disk.

        Args:
            state: Session state to save

        Returns:
            Path to saved session file
        """
        state.updated_at = time.time()
        session_file = self._session_file(state.session_id)
        session_file.write_text(state.to_json(), encoding="utf-8")
        return session_file

    def load_session(self, session_id: str) -> SessionState | None:
        """Load session state from disk.

        Args:
            session_id: Session identifier

        Returns:
            SessionState or None if not found
        """
        session_file = self._session_file(session_id)
        if not session_file.exists():
            return None

        try:
            content = session_file.read_text(encoding="utf-8")
            return SessionState.from_json(content)
        except (json.JSONDecodeError, TypeError, KeyError):
            return None

    def delete_session(self, session_id: str) -> bool:
        """Delete a saved session.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted
        """
        session_file = self._session_file(session_id)
        if session_file.exists():
            session_file.unlink()
            return True
        return False

    def list_sessions(self) -> list[tuple[str, float]]:
        """List all saved sessions.

        Returns:
            List of (session_id, updated_at) tuples
        """
        sessions = []
        for session_file in self.base_dir.glob("*.json"):
            try:
                content = session_file.read_text(encoding="utf-8")
                data = json.loads(content)
                sessions.append((data["session_id"], data.get("updated_at", 0)))
            except (json.JSONDecodeError, KeyError):
                continue

        # Sort by most recent first
        return sorted(sessions, key=lambda x: x[1], reverse=True)

    def get_latest_session(self) -> SessionState | None:
        """Get the most recently updated session.

        Returns:
            SessionState or None if no sessions
        """
        sessions = self.list_sessions()
        if sessions:
            return self.load_session(sessions[0][0])
        return None

    def cleanup_old_sessions(self, max_age_days: int = 30) -> int:
        """Remove sessions older than max_age_days.

        Args:
            max_age_days: Maximum age in days

        Returns:
            Number of sessions removed
        """
        cutoff = time.time() - (max_age_days * 24 * 60 * 60)
        removed = 0

        for session_file in self.base_dir.glob("*.json"):
            try:
                content = session_file.read_text(encoding="utf-8")
                data = json.loads(content)
                if data.get("updated_at", 0) < cutoff:
                    session_file.unlink()
                    removed += 1
            except (json.JSONDecodeError, KeyError):
                continue

        return removed


class BackupManager:
    """Manages file backups before modifications.

    Backups are stored in ~/.devorbit/backups/
    """

    def __init__(
        self,
        working_dir: Path,
        backup_dir: Path | None = None,
        max_backups: int = 100,
    ) -> None:
        """Initialize backup manager.

        Args:
            working_dir: Working directory to backup files from
            backup_dir: Directory for backups
            max_backups: Maximum number of backups to keep
        """
        self.working_dir = working_dir
        self.backup_dir = backup_dir or (Path.home() / ".devorbit" / "backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.max_backups = max_backups

        # Active checkpoints
        self._checkpoints: dict[str, FileCheckpoint] = {}

    def _backup_path(self, file_path: Path, timestamp: float | None = None) -> Path:
        """Get backup path for a file.

        Args:
            file_path: Original file path
            timestamp: Optional timestamp for naming

        Returns:
            Path for backup file
        """
        ts = timestamp or time.time()
        ts_str = datetime.fromtimestamp(ts).strftime("%Y%m%d_%H%M%S")

        # Create a unique backup name
        relative = (
            file_path.relative_to(self.working_dir)
            if file_path.is_relative_to(self.working_dir)
            else file_path
        )

        safe_name = str(relative).replace("/", "_").replace("\\", "_")
        return self.backup_dir / f"{ts_str}_{safe_name}"

    def create_checkpoint(self, file_path: str | Path) -> FileCheckpoint:
        """Create a checkpoint for a file before modification.

        Args:
            file_path: Path to file (relative or absolute)

        Returns:
            FileCheckpoint for restoration
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = self.working_dir / path
        path = path.resolve()

        # Read current content
        content: bytes | None = None
        checksum = ""
        existed = path.exists()

        if existed:
            content = path.read_bytes()
            checksum = hashlib.sha256(content).hexdigest()

        checkpoint = FileCheckpoint(
            file_path=path,
            content=content,
            existed=existed,
            checksum=checksum,
        )

        # Store in active checkpoints
        self._checkpoints[str(path)] = checkpoint

        return checkpoint

    def restore_checkpoint(self, checkpoint: FileCheckpoint) -> bool:
        """Restore a file from checkpoint.

        Args:
            checkpoint: Checkpoint to restore

        Returns:
            True if restored successfully
        """
        try:
            if checkpoint.existed and checkpoint.content is not None:
                # Restore original content
                checkpoint.file_path.parent.mkdir(parents=True, exist_ok=True)
                checkpoint.file_path.write_bytes(checkpoint.content)
            elif not checkpoint.existed and checkpoint.file_path.exists():
                # File was created, remove it
                checkpoint.file_path.unlink()
            return True
        except OSError:
            return False

    def backup_file(self, file_path: str | Path) -> Path | None:
        """Create a backup copy of a file.

        Args:
            file_path: Path to file to backup

        Returns:
            Path to backup file or None if file doesn't exist
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = self.working_dir / path
        path = path.resolve()

        if not path.exists():
            return None

        backup_path = self._backup_path(path)
        shutil.copy2(path, backup_path)

        # Cleanup old backups
        self._cleanup_old_backups()

        return backup_path

    def restore_backup(self, backup_path: Path, target_path: Path | None = None) -> bool:
        """Restore a file from backup.

        Args:
            backup_path: Path to backup file
            target_path: Target path (inferred from backup name if None)

        Returns:
            True if restored successfully
        """
        if not backup_path.exists():
            return False

        try:
            if target_path is None:
                # Infer target from backup name (format: YYYYMMDD_HHMMSS_filename)
                name = backup_path.name
                parts = name.split("_", 2)
                if len(parts) >= 3:
                    original_name = parts[2]
                    target_path = self.working_dir / original_name
                else:
                    return False

            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup_path, target_path)
            return True
        except OSError:
            return False

    def list_backups(self, file_pattern: str = "*") -> list[tuple[Path, float]]:
        """List all backups.

        Args:
            file_pattern: Glob pattern to filter

        Returns:
            List of (backup_path, timestamp) tuples
        """
        backups = []
        for backup_file in self.backup_dir.glob(file_pattern):
            if backup_file.is_file():
                backups.append((backup_file, backup_file.stat().st_mtime))

        return sorted(backups, key=lambda x: x[1], reverse=True)

    def _cleanup_old_backups(self) -> None:
        """Remove excess backups beyond max_backups."""
        backups = self.list_backups()
        if len(backups) > self.max_backups:
            for backup_path, _ in backups[self.max_backups :]:
                with contextlib.suppress(OSError):
                    backup_path.unlink()

    def clear_checkpoints(self) -> None:
        """Clear all active checkpoints."""
        self._checkpoints.clear()

    def get_checkpoint(self, file_path: str | Path) -> FileCheckpoint | None:
        """Get active checkpoint for a file.

        Args:
            file_path: Path to file

        Returns:
            FileCheckpoint or None
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = self.working_dir / path
        return self._checkpoints.get(str(path.resolve()))


__all__ = [
    "BackupManager",
    "FileCheckpoint",
    "SessionPersistence",
    "SessionState",
]
