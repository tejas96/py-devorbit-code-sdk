"""Session management for saving and resuming conversations."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast


if TYPE_CHECKING:
    from devorbit._types import Message


class SessionManager:
    """Manage session saving, loading, and resuming."""

    def __init__(self, sessions_dir: Path | None = None) -> None:
        """Initialize session manager.

        Args:
            sessions_dir: Directory to store session files (default: ~/.devorbit/sessions)
        """
        if sessions_dir is None:
            sessions_dir = Path.home() / ".devorbit" / "sessions"

        self.sessions_dir = sessions_dir
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def save_session(
        self,
        session_id: str,
        provider: str,
        model: str | None,
        messages: list["Message"],
        working_dir: Path,
        metadata: dict[str, Any] | None = None,
    ) -> Path:
        """Save a session to disk.

        Args:
            session_id: Unique session identifier
            provider: LLM provider name
            model: Model name
            messages: Conversation messages
            working_dir: Working directory
            metadata: Additional metadata

        Returns:
            Path to saved session file
        """
        session_data = {
            "session_id": session_id,
            "provider": provider,
            "model": model,
            "messages": messages,
            "working_dir": str(working_dir),
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }

        session_file = self.sessions_dir / f"{session_id}.json"
        with session_file.open("w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2)

        # Update latest session pointer
        latest_file = self.sessions_dir / "latest.txt"
        latest_file.write_text(session_id, encoding="utf-8")

        return session_file

    def load_session(self, session_id: str) -> dict[str, Any] | None:
        """Load a session from disk.

        Args:
            session_id: Session identifier to load

        Returns:
            Session data dictionary or None if not found
        """
        session_file = self.sessions_dir / f"{session_id}.json"

        if not session_file.exists():
            return None

        with session_file.open(encoding="utf-8") as f:
            return cast("dict[str, Any]", json.load(f))

    def get_latest_session_id(self) -> str | None:
        """Get the ID of the most recent session.

        Returns:
            Session ID or None if no sessions exist
        """
        latest_file = self.sessions_dir / "latest.txt"

        if not latest_file.exists():
            return None

        return latest_file.read_text(encoding="utf-8").strip()

    def list_sessions(self, limit: int = 10) -> list[dict[str, Any]]:
        """List recent sessions.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of session summaries sorted by timestamp (newest first)
        """
        sessions = []

        for session_file in self.sessions_dir.glob("*.json"):
            try:
                with session_file.open(encoding="utf-8") as f:
                    data = json.load(f)
                    sessions.append(
                        {
                            "session_id": data["session_id"],
                            "provider": data["provider"],
                            "model": data.get("model", "default"),
                            "timestamp": data["timestamp"],
                            "message_count": len(data.get("messages", [])),
                        }
                    )
            except Exception:
                # Skip invalid session files
                continue

        # Sort by timestamp (newest first)
        sessions.sort(key=lambda x: x["timestamp"], reverse=True)

        return sessions[:limit]

    def delete_session(self, session_id: str) -> bool:
        """Delete a session file.

        Args:
            session_id: Session identifier to delete

        Returns:
            True if deleted, False if not found
        """
        session_file = self.sessions_dir / f"{session_id}.json"

        if not session_file.exists():
            return False

        session_file.unlink()
        return True

    def generate_session_id(self) -> str:
        """Generate a unique session ID.

        Returns:
            New session ID
        """
        return str(uuid.uuid4())[:8]


__all__ = ["SessionManager"]
