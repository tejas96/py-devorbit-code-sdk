"""Workspace management for .claude directory system.

This module provides workspace context management similar to Claude Code CLI,
including project metadata, preferences, and session history.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar

from pydantic import BaseModel, Field


class WorkspaceContext(BaseModel):
    """Workspace context stored in .claude/context.json."""

    project_type: str = "unknown"  # python, javascript, typescript, react, etc
    language: str = "unknown"
    frameworks: list[str] = Field(default_factory=list)
    dependencies: dict[str, str] = Field(default_factory=dict)
    config: dict[str, Any] = Field(default_factory=dict)
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat())
    working_directory: str = ""

    class Config:
        """Pydantic config."""

        json_encoders: ClassVar[dict[type, Any]] = {datetime: lambda v: v.isoformat()}


class WorkspacePreferences(BaseModel):
    """User preferences stored in .claude/preferences.json."""

    auto_confirm_tools: bool = False
    session_allow_all: bool = False
    default_model: str | None = None
    default_provider: str | None = None
    custom_tool_permissions: dict[str, bool] = Field(default_factory=dict)


class WorkspaceManager:
    """Manage .claude workspace directory and context.

    The .claude directory structure:
    .claude/
      ├── context.json          # Project metadata
      ├── preferences.json      # User preferences
      ├── history/             # Command history
      │   └── sessions/        # Session snapshots
      └── cache/               # Model cache, indexes
    """

    def __init__(self, base_path: Path | None = None):
        """Initialize workspace manager.

        Args:
            base_path: Base directory for workspace (default: current working directory)
        """
        self.base_path = base_path or Path.cwd()
        self.claude_dir = self.base_path / ".claude"
        self.context_file = self.claude_dir / "context.json"
        self.preferences_file = self.claude_dir / "preferences.json"
        self.history_dir = self.claude_dir / "history"
        self.sessions_dir = self.history_dir / "sessions"
        self.cache_dir = self.claude_dir / "cache"

    def create_workspace(self) -> None:
        """Create .claude directory structure if it doesn't exist."""
        # Create main directory
        self.claude_dir.mkdir(exist_ok=True)

        # Create subdirectories
        self.history_dir.mkdir(exist_ok=True)
        self.sessions_dir.mkdir(exist_ok=True)
        self.cache_dir.mkdir(exist_ok=True)

        # Create context.json if it doesn't exist
        if not self.context_file.exists():
            context = WorkspaceContext(working_directory=str(self.base_path))
            self.save_context(context)

        # Create preferences.json if it doesn't exist
        if not self.preferences_file.exists():
            preferences = WorkspacePreferences()
            self.save_preferences(preferences)

    def workspace_exists(self) -> bool:
        """Check if workspace directory exists.

        Returns:
            True if .claude directory exists
        """
        return self.claude_dir.exists() and self.claude_dir.is_dir()

    def load_context(self) -> WorkspaceContext:
        """Load workspace context from .claude/context.json.

        Returns:
            Workspace context

        Raises:
            FileNotFoundError: If context file doesn't exist
        """
        if not self.context_file.exists():
            raise FileNotFoundError(f"Context file not found: {self.context_file}")

        with self.context_file.open(encoding="utf-8") as f:
            data = json.load(f)

        return WorkspaceContext(**data)

    def save_context(self, context: WorkspaceContext) -> None:
        """Save workspace context to .claude/context.json.

        Args:
            context: Workspace context to save
        """
        # Ensure directory exists
        self.claude_dir.mkdir(exist_ok=True)

        # Update last_updated timestamp
        context.last_updated = datetime.now().isoformat()

        # Write context
        with self.context_file.open("w", encoding="utf-8") as f:
            json.dump(context.model_dump(), f, indent=2)

    def load_preferences(self) -> WorkspacePreferences:
        """Load user preferences from .claude/preferences.json.

        Returns:
            Workspace preferences

        Raises:
            FileNotFoundError: If preferences file doesn't exist
        """
        if not self.preferences_file.exists():
            raise FileNotFoundError(f"Preferences file not found: {self.preferences_file}")

        with self.preferences_file.open(encoding="utf-8") as f:
            data = json.load(f)

        return WorkspacePreferences(**data)

    def save_preferences(self, preferences: WorkspacePreferences) -> None:
        """Save user preferences to .claude/preferences.json.

        Args:
            preferences: Preferences to save
        """
        # Ensure directory exists
        self.claude_dir.mkdir(exist_ok=True)

        # Write preferences
        with self.preferences_file.open("w", encoding="utf-8") as f:
            json.dump(preferences.model_dump(), f, indent=2)

    def reset_workspace(self) -> None:
        """Reset workspace to default state (clear cache, reset preferences)."""
        # Clear cache directory
        if self.cache_dir.exists():
            for file in self.cache_dir.iterdir():
                if file.is_file():
                    file.unlink()

        # Reset preferences
        preferences = WorkspacePreferences()
        self.save_preferences(preferences)

    def clear_workspace(self) -> None:
        """Delete entire .claude directory and all contents."""
        if self.claude_dir.exists():
            shutil.rmtree(self.claude_dir)

    def get_workspace_info(self) -> dict[str, Any]:
        """Get workspace information summary.

        Returns:
            Dictionary with workspace info
        """
        if not self.workspace_exists():
            return {
                "exists": False,
                "path": str(self.claude_dir),
            }

        info: dict[str, Any] = {
            "exists": True,
            "path": str(self.claude_dir),
        }

        try:
            context = self.load_context()
            info["project_type"] = context.project_type
            info["language"] = context.language
            info["frameworks"] = context.frameworks
            info["last_updated"] = context.last_updated
        except FileNotFoundError:
            info["context"] = "missing"

        try:
            preferences = self.load_preferences()
            info["auto_confirm_tools"] = preferences.auto_confirm_tools
            info["session_allow_all"] = preferences.session_allow_all
        except FileNotFoundError:
            info["preferences"] = "missing"

        return info
