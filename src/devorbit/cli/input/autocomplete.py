"""Autocomplete system for Devorbit CLI.

Implements autocomplete for slash commands, file paths, model names, and tools
matching the Claude Code CLI specification.
"""

from pathlib import Path




class CommandCompleter:
    """Autocomplete for slash commands.

    Provides suggestions for built-in commands and custom commands from
    .devorbit/commands/ directories.
    """

    # Built-in commands from the specification
    BUILT_IN_COMMANDS = {
        "help": "Show all commands",
        "model": "Switch model",
        "mode": "Change execution mode",
        "clear": "Clear conversation",
        "compact": "Compact context",
        "rewind": "Rewind conversation",
        "export": "Export session",
        "history": "Show command history",
        "context": "Manage context",
        "attach": "Attach files",
        "mcp": "MCP configuration",
        "hooks": "Manage hooks",
        "skills": "Manage skills",
        "agents": "Manage subagents",
        "settings": "Open settings",
        "doctor": "Run diagnostics",
        "statusline": "Configure status line",
        "bug": "Report bug",
        "quit": "Exit",
        "exit": "Exit",
        "cd": "Change directory",
        "pwd": "Print working directory",
        "planning": "Toggle planning mode",
        "provider": "Show current provider",
        "status": "Show session status",
    }

    def __init__(self, working_dir: Path | None = None) -> None:
        """Initialize command completer.

        Args:
            working_dir: Working directory for finding custom commands
        """
        self.working_dir = working_dir or Path.cwd()
        self.custom_commands: dict[str, str] = {}
        self._load_custom_commands()

    def _load_custom_commands(self) -> None:
        """Load custom commands from .devorbit/commands/ directory."""
        commands_dir = self.working_dir / ".devorbit" / "commands"
        if commands_dir.exists() and commands_dir.is_dir():
            for cmd_file in commands_dir.glob("*.md"):
                cmd_name = cmd_file.stem
                self.custom_commands[cmd_name] = f"Custom: {cmd_name}"

    def get_completions(self, text: str) -> list[tuple[str, str]]:
        """Get command completions for given text.

        Args:
            text: Partial command text (without leading /)

        Returns:
            List of (command, description) tuples
        """
        text_lower = text.lower()
        completions = []

        # Add built-in commands
        for cmd, desc in self.BUILT_IN_COMMANDS.items():
            if cmd.startswith(text_lower):
                completions.append((cmd, desc))

        # Add custom commands
        for cmd, desc in self.custom_commands.items():
            if cmd.startswith(text_lower):
                completions.append((cmd, desc))

        return sorted(completions)


class FileCompleter:
    """Autocomplete for file paths and glob patterns.

    Supports @file mentions and glob pattern completion.
    """

    def __init__(self, working_dir: Path | None = None) -> None:
        """Initialize file completer.

        Args:
            working_dir: Base directory for file completion
        """
        self.working_dir = working_dir or Path.cwd()

    def get_completions(self, text: str) -> list[tuple[str, str]]:
        """Get file path completions.

        Args:
            text: Partial file path

        Returns:
            List of (path, type) tuples where type is "file" or "dir"
        """
        # Remove @ prefix if present
        path_text = text.lstrip("@")

        try:
            # Resolve partial path
            if "/" in path_text:
                parent = self.working_dir / Path(path_text).parent
                prefix = Path(path_text).name
            else:
                parent = self.working_dir
                prefix = path_text

            if not parent.exists():
                return []

            completions = []
            for item in parent.iterdir():
                if item.name.startswith(prefix):
                    item_type = "dir" if item.is_dir() else "file"
                    rel_path = item.relative_to(self.working_dir)
                    completions.append((str(rel_path), item_type))

            return sorted(completions)[:10]  # Limit to 10 suggestions

        except (ValueError, OSError):
            return []

    def expand_glob(self, pattern: str) -> list[Path]:
        """Expand glob pattern to matching files.

        Args:
            pattern: Glob pattern (e.g., "src/**/*.py")

        Returns:
            List of matching file paths
        """
        try:
            return sorted(self.working_dir.glob(pattern))
        except (ValueError, OSError):
            return []


class ModelCompleter:
    """Autocomplete for model names per provider.

    Provides model suggestions based on the current provider.
    """

    # Model lists per provider (from specification)
    MODELS = {
        "anthropic": {
            "claude-opus-4-1": "Most capable",
            "claude-opus-4": "Very capable",
            "claude-sonnet-4-5": "Fastest & smartest",
            "claude-sonnet-4": "Balanced",
            "claude-haiku-4-5": "Ultra fast",
            "claude-haiku-3-5": "Fast",
        },
        "openai": {
            "gpt-5": "Latest & greatest",
            "gpt-5-codex-mini": "Optimized for code",
            "gpt-4-turbo": "Fast GPT-4",
            "gpt-4": "Very capable",
            "gpt-3.5-turbo": "Fast & affordable",
        },
        "gemini": {
            "gemini-pro-2-5": "Latest Gemini",
            "gemini-pro-2": "Very capable",
            "gemini-pro-1-5": "Balanced",
            "gemini-flash-2": "Ultra fast",
            "gemini-flash-1-5": "Fast",
        },
        "mistral": {
            "mistral-large-2": "Most capable",
            "mistral-large": "Very capable",
            "mistral-medium": "Balanced",
            "mistral-small": "Fast",
        },
        "codellama": {
            "codellama-70b": "Most capable",
            "codellama-34b": "Balanced",
            "codellama-13b": "Fast",
        },
    }

    def __init__(self, provider: str = "anthropic") -> None:
        """Initialize model completer.

        Args:
            provider: Current provider name
        """
        self.provider = provider

    def get_completions(self, text: str) -> list[tuple[str, str]]:
        """Get model completions for current provider.

        Args:
            text: Partial model name

        Returns:
            List of (model, description) tuples
        """
        text_lower = text.lower()
        models = self.MODELS.get(self.provider, {})

        completions = []
        for model, desc in models.items():
            if model.startswith(text_lower):
                completions.append((model, desc))

        return completions


class AutocompleteEngine:
    """Main autocomplete engine that coordinates all completers.

    Determines context and delegates to appropriate completer.
    """

    def __init__(
        self,
        provider: str = "anthropic",
        working_dir: Path | None = None,
    ) -> None:
        """Initialize autocomplete engine.

        Args:
            provider: Current provider name
            working_dir: Working directory
        """
        self.provider = provider
        self.working_dir = working_dir or Path.cwd()

        # Initialize completers
        self.command_completer = CommandCompleter(working_dir)
        self.file_completer = FileCompleter(working_dir)
        self.model_completer = ModelCompleter(provider)

    def get_completions(self, text: str, cursor_position: int) -> list[tuple[str, str]]:
        """Get completions based on context.

        Args:
            text: Full input text
            cursor_position: Current cursor position

        Returns:
            List of (completion, description) tuples
        """
        # Get text before cursor
        text_before_cursor = text[:cursor_position]

        # Slash command completion
        if text_before_cursor.startswith("/"):
            cmd_text = text_before_cursor[1:].split()[0] if " " in text_before_cursor else text_before_cursor[1:]
            return self.command_completer.get_completions(cmd_text)

        # File path completion (@ mentions)
        if "@" in text_before_cursor:
            # Find the @ symbol closest to cursor
            at_pos = text_before_cursor.rfind("@")
            file_text = text_before_cursor[at_pos + 1:]
            return self.file_completer.get_completions(file_text)

        # Model completion (after /model command)
        if text_before_cursor.strip().startswith("/model "):
            model_text = text_before_cursor.split("/model ", 1)[1]
            return self.model_completer.get_completions(model_text)

        return []

    def update_provider(self, provider: str) -> None:
        """Update provider for model completion.

        Args:
            provider: New provider name
        """
        self.provider = provider
        self.model_completer = ModelCompleter(provider)


__all__ = ["AutocompleteEngine", "CommandCompleter", "FileCompleter", "ModelCompleter"]
