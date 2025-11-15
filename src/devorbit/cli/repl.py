"""REPL (Read-Eval-Print Loop) implementation for Devorbit CLI."""

import sys
from typing import Optional


try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.styles import Style
except ImportError:
    PromptSession = None  # type: ignore[assignment,misc]
    HTML = None  # type: ignore[assignment,misc]
    FileHistory = None  # type: ignore[assignment,misc]
    Style = None  # type: ignore[assignment,misc]

from pathlib import Path

from .commands import CommandHandler
from .session import CLISession


class DevorbitREPL:
    """Interactive REPL for Devorbit CLI."""

    def __init__(self, session: CLISession) -> None:
        """Initialize the REPL.

        Args:
            session: CLI session instance
        """
        self.session = session
        self.command_handler = CommandHandler(session)

        # Setup prompt session with history
        history_file = Path.home() / ".devorbit_history"
        if PromptSession is not None and FileHistory is not None:
            self.prompt_session: Optional[PromptSession[str]] = PromptSession(
                history=FileHistory(str(history_file))
            )
        else:
            self.prompt_session = None

        # Prompt style
        if Style is not None:
            self.prompt_style = Style.from_dict(
                {
                    "prompt": "bold cyan",
                    "path": "yellow",
                }
            )
        else:
            self.prompt_style = None

    def get_prompt_message(self) -> str:
        """Get the prompt message with current context.

        Returns:
            Formatted prompt string
        """
        if HTML is not None and self.prompt_style is not None:
            cwd = self.session.working_dir.name
            return HTML(f"<prompt>devorbit</prompt> <path>{cwd}</path><prompt>></prompt> ").value
        return "devorbit> "

    def read_input(self) -> Optional[str]:
        """Read user input from the prompt.

        Returns:
            User input string or None if EOF/exit
        """
        try:
            if self.prompt_session is not None:
                prompt_msg = self.get_prompt_message()
                user_input = self.prompt_session.prompt(
                    prompt_msg,
                    style=self.prompt_style,
                )
            else:
                # Fallback to basic input
                user_input = input(self.get_prompt_message())

            return user_input.strip()
        except EOFError:
            return None
        except KeyboardInterrupt:
            self.session.print("\nUse /exit or Ctrl+D to quit")
            return ""

    def process_input(self, user_input: str) -> bool:
        """Process user input and execute commands.

        Args:
            user_input: User input string

        Returns:
            True to continue REPL, False to exit
        """
        if not user_input:
            return True

        # Check if it's a slash command
        if user_input.startswith("/"):
            return self.command_handler.handle_command(user_input)

        # Regular message - send to LLM
        try:
            self.session.add_message("user", user_input)
            self.session.print_info("Processing your request...")

            # TODO: Implement LLM message sending and tool execution
            # For now, just echo back
            response = f"[Echo] You said: {user_input}"
            self.session.print(f"\n{response}\n")

            self.session.add_message("assistant", response)
        except Exception as e:
            self.session.print_error(f"Failed to process message: {e}")
            if self.session.debug:
                raise

        return True

    def run(self) -> None:
        """Start the REPL loop."""
        while self.session.is_running:
            user_input = self.read_input()

            # Handle EOF (Ctrl+D)
            if user_input is None:
                self.session.print("\nGoodbye! 👋")
                break

            # Process the input
            continue_running = self.process_input(user_input)
            if not continue_running:
                break


__all__ = ["DevorbitREPL"]
__all__ = ["DevorbitREPL"]
