"""Enhanced terminal UI components for Devorbit CLI.

This module provides a comprehensive terminal UI system that implements
the Claude Code CLI specification with multi-provider support.
"""

from .claude_style import (
    ClaudeStylePrompt,
    ClaudeStyleUI,
    PermissionChoice,
    ToolExecutionDisplay,
    ToolStatus,
)
from .codeblocks import CodeBlockDisplay, DiffDisplay
from .colors import Colors, ColorScheme
from .display import StreamingDisplay
from .notifications import NotificationManager, NotificationType
from .progress import ProgressIndicator
from .statusline import StatusLine


__all__ = [
    # Claude Code-style components
    "ClaudeStylePrompt",
    "ClaudeStyleUI",
    "PermissionChoice",
    "ToolExecutionDisplay",
    "ToolStatus",
    # Original components
    "CodeBlockDisplay",
    "ColorScheme",
    "Colors",
    "DiffDisplay",
    "NotificationManager",
    "NotificationType",
    "ProgressIndicator",
    "StatusLine",
    "StreamingDisplay",
]
