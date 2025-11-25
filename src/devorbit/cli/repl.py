"""REPL (Read-Eval-Print Loop) implementation for Devorbit CLI with enhanced input."""

import random
from pathlib import Path
from typing import TYPE_CHECKING
import shutil


if TYPE_CHECKING:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import Completer
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.styles import Style
else:
    try:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.completion import Completer, WordCompleter
        from prompt_toolkit.formatted_text import HTML
        from prompt_toolkit.history import FileHistory
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.styles import Style

        HAS_PROMPT_TOOLKIT = True
    except ImportError:
        PromptSession = None  # type: ignore[assignment,misc]
        Completer = None  # type: ignore[assignment,misc]
        WordCompleter = None  # type: ignore[assignment,misc]
        HTML = None  # type: ignore[assignment,misc]
        FileHistory = None  # type: ignore[assignment,misc]
        KeyBindings = None  # type: ignore[assignment,misc]
        Style = None  # type: ignore[assignment,misc]
        HAS_PROMPT_TOOLKIT = False

from .commands import CommandHandler
from .input import AutocompleteEngine, FileMentionParser, InputValidator
from .llm import LLMHandler
from .session import CLISession


class DevorbitREPL:
    """Interactive REPL for Devorbit CLI."""
    
    # Random tips to display in the input placeholder
    TIPS = [
        "Type your message or @path/to/file",
        "Tip: Use @filename to reference files in your project",
        "Tip: Try /help to see all available commands",
        "Tip: Press Ctrl+D to exit anytime",
        "Tip: Use /clear to clear conversation history",
        "Tip: Type /model to switch between different AI models",
        "Tip: Use @ to mention multiple files at once",
        "Tip: Try /history to see your conversation history",
        "Tip: Use /multiline for multi-line input mode",
        "Tip: Reference files with @src/main.py for context",
        "Tip: Press Ctrl+@ for quick file mention",
        "Tip: Use /exit or Ctrl+D to quit gracefully",
    ]

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
        
        # Track attached files for display
        self.attached_files: list[str] = []
        
        # Current tip index
        self.current_tip = random.choice(self.TIPS)

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

            # Setup key bindings
            kb = None
            if HAS_PROMPT_TOOLKIT and KeyBindings is not None:
                kb = KeyBindings()
                
                # Add @ shortcut for file mentions (Ctrl+@)
                @kb.add("c-@")
                def _(event):
                    """Insert @ for file mention."""
                    event.current_buffer.insert_text("@")

            if HAS_PROMPT_TOOLKIT and PromptSession is not None and FileHistory is not None:
                self.prompt_session = PromptSession(
                    history=FileHistory(str(history_file)),
                    completer=self.completer,
                    complete_while_typing=True,
                    key_bindings=kb,
                    placeholder=HTML(f'<placeholder>{self.current_tip}</placeholder>'),
                )

            # Enhanced prompt style with box
            if HAS_PROMPT_TOOLKIT and Style is not None:
                self.prompt_style = Style.from_dict(
                    {
                        # Input prompt
                        "prompt": "#888888",  # Gray arrow
                        "": "#ffffff",  # White text for input
                        "placeholder": "#666666",  # Dark gray placeholder
                        # Bottom toolbar/status bar
                        "bottom-toolbar": "bg:#1a1a1a #888888",
                        "bottom-toolbar.path": "#4a9eff",  # Blue for path
                        "bottom-toolbar.status": "#ff6b6b",  # Red for warnings
                        "bottom-toolbar.mode": "#888888",  # Gray for mode
                        # Input box border
                        "input-border": "#666666",  # Gray border
                    }
                )

    def _get_bottom_toolbar(self) -> "HTML | str":
        """Create the bottom status bar.

        Returns:
            Formatted toolbar HTML or plain string
        """
        if not HAS_PROMPT_TOOLKIT or HTML is None:
            # Fallback plain text
            sandbox_status = "no sandbox"
            mode = "auto" if self.session.auto_approve_tools else "manual"
            return f"{self.session.working_dir} | {sandbox_status} | {mode}"

        # Get directory name
        path_display = self.session.working_dir.name
        
        # Sandbox status (always no sandbox for now)
        sandbox_status = "no sandbox"
        
        # Mode
        mode = "auto" if self.session.auto_approve_tools else "manual"
        
        # File count
        file_info = ""
        if self.attached_files:
            file_info = f" | Using: {len(self.attached_files)} file(s)"

        toolbar_html = (
            f'<path>{path_display}</path> '
            f'<status>{sandbox_status}</status> (see /docs)     '
            f'<mode>{mode}</mode>'
            f'{file_info}'
        )

        return HTML(toolbar_html)

    def get_prompt_message(self) -> "HTML | str":
        """Get the prompt message with current context.

        Returns:
            Formatted prompt string
        """
        if not HAS_PROMPT_TOOLKIT or HTML is None:
            return "> "

        # Simple prompt arrow
        return HTML('<prompt>></prompt> ')

    def read_input(self) -> str | None:
        """Read user input from the prompt with box border.

        Returns:
            User input string or None if EOF/exit
        """
        try:
            if not TYPE_CHECKING and HAS_PROMPT_TOOLKIT and self.prompt_session is not None:
                # Rotate to a new random tip for next prompt
                self.current_tip = random.choice(self.TIPS)
                
                # Update placeholder with new tip
                if HTML is not None:
                    self.prompt_session.placeholder = HTML(f'<placeholder>{self.current_tip}</placeholder>')
                
                # --- FIX STARTS HERE ---
                # Get dynamic terminal width
                cols, _ = shutil.get_terminal_size(fallback=(80, 24))
                # Subtract 2 to account for the corner characters (╭ and ╮)
                width = max(0, cols - 2)

                # Print top border of input box with dynamic width
                print(f"\033[90m╭{'─' * width}╮\033[0m")
                
                prompt_msg = self.get_prompt_message()
                user_input = self.prompt_session.prompt(
                    prompt_msg,
                    style=self.prompt_style,
                    bottom_toolbar=self._get_bottom_toolbar,
                    multiline=False,
                    prompt_continuation=lambda width, line_number, is_soft_wrap: '',
                )
                
                # Print bottom border of input box with dynamic width
                print(f"\033[90m╰{'─' * width}╯\033[0m")
                # --- FIX ENDS HERE ---
                
                return user_input.strip()

            # Fallback to basic input
            user_input = input("> ")
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
            # Track attached files
            self.attached_files = [m.get('path', m.get('file', '')) for m in mentions]
            
            # Display attached files summary
            print(f"\n\033[90mUsing: {len(self.attached_files)} file(s)\033[0m")
            for filepath in self.attached_files:
                print(f"\033[90m  • {filepath}\033[0m")
            print()

            # Remove mentions from the actual prompt
            clean_input = self.mention_parser.remove_mentions(user_input)
        else:
            clean_input = user_input
            self.attached_files = []

        # Regular message - send to LLM
        try:
            # Send message with streaming (provider-agnostic)
            response = self.llm_handler.send_message(
                clean_input,
                stream=True,  # Enable streaming for real-time display
            )

            # Add assistant response to history
            if response:
                self.session.add_message("assistant", response)
            else:
                self.session.print_warning("No response received from LLM")

        except Exception as e:
            self.session.print_error(f"Failed to process message: {e}")
            if self.session.debug:
                raise
        finally:
            # Clear attached files after processing
            self.attached_files = []

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