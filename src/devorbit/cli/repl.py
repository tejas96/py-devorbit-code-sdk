"""REPL (Read-Eval-Print Loop) implementation for Devorbit CLI with enhanced input."""

from pathlib import Path
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import Completer
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.styles import Style
else:
    try:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.completion import Completer, WordCompleter
        from prompt_toolkit.formatted_text import HTML
        from prompt_toolkit.history import FileHistory
        from prompt_toolkit.styles import Style

        HAS_PROMPT_TOOLKIT = True
    except ImportError:
        PromptSession = None  # type: ignore[assignment,misc]
        Completer = None  # type: ignore[assignment,misc]
        WordCompleter = None  # type: ignore[assignment,misc]
        HTML = None  # type: ignore[assignment,misc]
        FileHistory = None  # type: ignore[assignment,misc]
        Style = None  # type: ignore[assignment,misc]
        HAS_PROMPT_TOOLKIT = False

from .commands import CommandHandler
from .input import AutocompleteEngine, FileMentionParser, InputValidator
from .llm import LLMHandler
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

        # Initialize enhanced input components
        self.autocomplete = AutocompleteEngine(
            provider=session.provider,
            working_dir=session.working_dir,
        )
        self.mention_parser = FileMentionParser(working_dir=session.working_dir)
        self.input_validator = InputValidator()

        # Initialize LLM handler
        self.llm_handler = LLMHandler(session)

        # Multi-line mode toggle
        self.multiline_mode = False

        # Setup prompt session with history
        history_file = Path.home() / ".devorbit_history"
        self.prompt_session: PromptSession[str] | None = None
        self.prompt_style: Style | None = None
        self.completer: Completer | None = None

        if not TYPE_CHECKING:
            # Setup autocompleter for prompt_toolkit
            if HAS_PROMPT_TOOLKIT and WordCompleter is not None:
                # Create a simple word completer with command names
                command_words = list(self.autocomplete.command_completer.BUILT_IN_COMMANDS.keys())
                self.completer = WordCompleter(command_words, sentence=True)

            if HAS_PROMPT_TOOLKIT and PromptSession is not None and FileHistory is not None:
                self.prompt_session = PromptSession(
                    history=FileHistory(str(history_file)),
                    completer=self.completer,
                    complete_while_typing=True,
                )

            # Prompt style
            if HAS_PROMPT_TOOLKIT and Style is not None:
                self.prompt_style = Style.from_dict(
                    {
                        "prompt": "bold cyan",
                        "path": "yellow",
                    }
                )

    def get_prompt_message(self) -> str:
        """Get the prompt message with current context.

        Returns:
            Formatted prompt string
        """
        if (
            not TYPE_CHECKING
            and HAS_PROMPT_TOOLKIT
            and HTML is not None
            and self.prompt_style is not None
        ):
            return HTML("<prompt>devorbit</prompt> <prompt>></prompt> ")
        return "devorbit> "

    def read_input(self) -> str | None:
        """Read user input from the prompt.

        Returns:
            User input string or None if EOF/exit
        """
        try:
            if not TYPE_CHECKING and HAS_PROMPT_TOOLKIT and self.prompt_session is not None:
                prompt_msg = self.get_prompt_message()
                user_input = self.prompt_session.prompt(
                    prompt_msg,
                    style=self.prompt_style,
                )
                return user_input.strip()

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

        # Validate input
        is_valid, error = self.input_validator.validate_input(user_input)
        if not is_valid:
            self.session.print_error(f"Invalid input: {error}")
            return True

        # Sanitize input
        user_input = self.input_validator.sanitize_input(user_input)

        # Check if it's a slash command
        if user_input.startswith("/"):
            # Handle special commands that affect REPL state
            if user_input.strip() == "/multiline":
                self.multiline_mode = not self.multiline_mode
                status = "enabled" if self.multiline_mode else "disabled"
                self.session.print_success(f"Multi-line mode {status}")
                if self.multiline_mode:
                    self.session.print_info("Press Ctrl+Enter to submit, Shift+Enter for new line")
                return True

            return self.command_handler.handle_command(user_input)

        # Parse @file mentions
        mentions = self.mention_parser.parse(user_input)
        if mentions:
            # Display attached files summary
            summary = self.mention_parser.format_mention_summary(mentions)
            if summary:
                self.session.print_info(summary)

            # Remove mentions from the actual prompt
            clean_input = self.mention_parser.remove_mentions(user_input)
        else:
            clean_input = user_input

        # Regular message - send to LLM
        try:
            response_text, usage = self.llm_handler.send_message(
                clean_input,
                stream=True,  # Enable streaming for real-time display
            )

            if response_text:
                self.session.add_message("assistant", response_text)
                if usage is not None:
                    input_tokens = getattr(usage, "input_tokens", 0)
                    output_tokens = getattr(usage, "output_tokens", 0)
                    total_tokens = input_tokens + output_tokens
                    self.session.print(
                        f"\n[Token Usage] Input: {input_tokens} | Output: {output_tokens} | Total: {total_tokens}\n"
                    )
            else:
                self.session.print_warning("No response received from LLM")

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
