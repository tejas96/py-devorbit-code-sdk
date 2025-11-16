"""REPL (Read-Eval-Print Loop) implementation for Devorbit CLI."""

from pathlib import Path
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.styles import Style
    from questionary import Choice

    import questionary as questionary_module

    HAS_QUESTIONARY = True
    HAS_PROMPT_TOOLKIT = True
else:
    try:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.formatted_text import HTML
        from prompt_toolkit.history import FileHistory
        from prompt_toolkit.styles import Style

        HAS_PROMPT_TOOLKIT = True
    except ImportError:
        PromptSession = None  # type: ignore[assignment,misc]
        HTML = None  # type: ignore[assignment,misc]
        FileHistory = None  # type: ignore[assignment,misc]
        Style = None  # type: ignore[assignment,misc]
        HAS_PROMPT_TOOLKIT = False

    try:
        import questionary as questionary_module
        from questionary import Choice

        HAS_QUESTIONARY = True
    except ImportError:
        questionary_module = None  # type: ignore[assignment]
        Choice = None  # type: ignore[assignment,misc]
        HAS_QUESTIONARY = False

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
        self.prompt_session: PromptSession[str] | None = None
        self.prompt_style: Style | None = None

        if not TYPE_CHECKING:
            if HAS_PROMPT_TOOLKIT and PromptSession is not None and FileHistory is not None:
                self.prompt_session = PromptSession(history=FileHistory(str(history_file)))

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
            cwd = self.session.working_dir.name
            return HTML(f"<prompt>devorbit</prompt> <path>{cwd}</path><prompt>></prompt> ").value
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

    def show_command_menu(self) -> str | None:
        """Show interactive command menu using questionary.

        Returns:
            Selected command or None if cancelled
        """
        if not TYPE_CHECKING and (
            not HAS_QUESTIONARY or questionary_module is None or Choice is None
        ):
            self.session.print_info("Interactive menu requires questionary. Install with:")
            self.session.print("  pip install devorbit-multi-llm-sdk[cli]")
            return None

        commands = [
            Choice(title="📖 /help - Show help message", value="/help"),
            Choice(title="📊 /status - Show session status", value="/status"),
            Choice(title="📜 /history - Show conversation history", value="/history"),
            Choice(title="🧹 /clear - Clear conversation history", value="/clear"),
            Choice(title="🤖 /model - Show or change model", value="/model"),
            Choice(title="🔧 /provider - Show current provider", value="/provider"),
            Choice(title="📁 /pwd - Print working directory", value="/pwd"),
            Choice(title="📂 /cd - Change working directory", value="/cd"),
            Choice(title="📝 /planning - Toggle planning mode", value="/planning"),
            Choice(title="🚪 /exit - Exit REPL", value="/exit"),
            Choice(title="❌ Cancel", value="cancel"),
        ]

        try:
            result = questionary_module.select(
                "Select a command:",
                choices=commands,
                style=questionary_module.Style(
                    [
                        ("qmark", "fg:cyan bold"),
                        ("question", "bold"),
                        ("pointer", "fg:cyan bold"),
                        ("highlighted", "fg:cyan bold"),
                        ("selected", "fg:green"),
                    ]
                ),
            ).ask()

            if result == "cancel" or result is None:
                return None
            return str(result)
        except (KeyboardInterrupt, EOFError):
            return None

    def process_input(self, user_input: str) -> bool:
        """Process user input and execute commands.

        Args:
            user_input: User input string

        Returns:
            True to continue REPL, False to exit
        """
        if not user_input:
            return True

        # Check if user typed just "/" - show interactive menu
        if user_input == "/":
            selected_cmd = self.show_command_menu()
            if selected_cmd:
                return self.command_handler.handle_command(selected_cmd)
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
