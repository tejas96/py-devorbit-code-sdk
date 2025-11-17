"""File mention parser for @file syntax.

Implements the @file mention system from the Claude Code CLI specification
for attaching files to the conversation context.
"""

import re
from enum import Enum
from pathlib import Path
from typing import NamedTuple


class MentionType(Enum):
    """Types of mentions in input."""

    FILE = "file"  # @path/to/file.py
    GLOB = "glob"  # @src/**/*.py
    DIRECTORY = "directory"  # @src/


class Mention(NamedTuple):
    """Represents a parsed mention."""

    type: MentionType
    pattern: str
    resolved_paths: list[Path]


class FileMentionParser:
    """Parser for @file mentions in user input.

    Supports:
    - Single files: @src/main.py
    - Glob patterns: @src/**/*.py
    - Directories: @src/
    - Multiple mentions: @file1.py @file2.js

    Example:
        >>> parser = FileMentionParser(Path("/project"))
        >>> mentions = parser.parse("explain @src/main.py and @tests/**/*.py")
        >>> len(mentions)
        2
    """

    # Regex pattern for @mentions
    MENTION_PATTERN = re.compile(r"@([\w\-./\*]+)")

    def __init__(self, working_dir: Path | None = None) -> None:
        """Initialize mention parser.

        Args:
            working_dir: Base directory for resolving paths
        """
        self.working_dir = working_dir or Path.cwd()

    def parse(self, text: str) -> list[Mention]:
        """Parse all @mentions from text.

        Args:
            text: Input text containing @mentions

        Returns:
            List of parsed Mention objects
        """
        mentions = []
        matches = self.MENTION_PATTERN.finditer(text)

        for match in matches:
            pattern = match.group(1)
            mention = self._resolve_mention(pattern)
            if mention:
                mentions.append(mention)

        return mentions

    def _resolve_mention(self, pattern: str) -> Mention | None:
        """Resolve a single mention pattern.

        Args:
            pattern: File pattern (without @ prefix)

        Returns:
            Mention object if pattern resolves to files, None otherwise
        """
        # Check if it's a glob pattern
        if "*" in pattern or "**" in pattern:
            return self._resolve_glob(pattern)

        # Check if it's a directory
        path = self.working_dir / pattern
        if path.exists() and path.is_dir():
            return Mention(
                type=MentionType.DIRECTORY,
                pattern=pattern,
                resolved_paths=[path],
            )

        # Check if it's a file
        if path.exists() and path.is_file():
            return Mention(
                type=MentionType.FILE,
                pattern=pattern,
                resolved_paths=[path],
            )

        return None

    def _resolve_glob(self, pattern: str) -> Mention | None:
        """Resolve a glob pattern.

        Args:
            pattern: Glob pattern

        Returns:
            Mention with resolved paths, or None if no matches
        """
        try:
            matches = list(self.working_dir.glob(pattern))
            # Filter to only files
            file_matches = [p for p in matches if p.is_file()]

            if file_matches:
                return Mention(
                    type=MentionType.GLOB,
                    pattern=pattern,
                    resolved_paths=sorted(file_matches),
                )
        except (ValueError, OSError):
            pass

        return None

    def remove_mentions(self, text: str) -> str:
        """Remove all @mentions from text.

        Args:
            text: Input text

        Returns:
            Text with @mentions removed
        """
        return self.MENTION_PATTERN.sub("", text).strip()

    def format_mention_summary(self, mentions: list[Mention]) -> str:
        """Format a summary of attached files.

        Args:
            mentions: List of mentions

        Returns:
            Formatted summary string

        Example:
            "📎 Attached 3 files: main.py, utils.py, test.py"
        """
        if not mentions:
            return ""

        total_files = sum(len(m.resolved_paths) for m in mentions)

        if total_files == 0:
            return ""

        # Get first few file names
        all_paths = []
        for mention in mentions:
            all_paths.extend(mention.resolved_paths)

        file_names = [p.name for p in all_paths[:3]]
        names_str = ", ".join(file_names)

        if total_files > 3:
            names_str += f", and {total_files - 3} more"

        return f"📎 Attached {total_files} file{'s' if total_files != 1 else ''}: {names_str}"


__all__ = ["FileMentionParser", "Mention", "MentionType"]
