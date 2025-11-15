"""Command handler for slash commands in Devorbit CLI."""

from typing import Callable, Dict

from .session import CLISession


class CommandHandler:
    """Handles slash commands in the REPL."""

    def __init__(self, session: CLISession) -> None:
        """Initialize command handler.

        Args:
            session: CLI session instance
        """
        self.session = session

        # Register built-in commands
        self.commands: Dict[str, Callable[[list[str]], bool]] = {
            "help": self.cmd_help,
            "exit": self.cmd_exit,
            "quit": self.cmd_exit,
            "clear": self.cmd_clear,
            "history": self.cmd_history,
            "status": self.cmd_status,
            "model": self.cmd_model,
            "provider": self.cmd_provider,
            "cd": self.cmd_cd,
            "pwd": self.cmd_pwd,
            "planning": self.cmd_planning,
        }

    def handle_command(self, command_line: str) -> bool:
        """Handle a slash command.

        Args:
            command_line: Full command line starting with /

        Returns:
            True to continue REPL, False to exit
        """
        # Parse command and arguments
        parts = command_line[1:].split()
        if not parts:
            self.session.print_error("Empty command")
            return True

        cmd_name = parts[0].lower()
        cmd_args = parts[1:]

        # Execute command
        if cmd_name in self.commands:
            return self.commands[cmd_name](cmd_args)

        self.session.print_error(f"Unknown command: /{cmd_name}")
        self.session.print("Type /help to see available commands")
        return True

    def cmd_help(self, args: list[str]) -> bool:
        """Display help information.

        Args:
            args: Command arguments

        Returns:
            True to continue REPL
        """
        help_text = """
Available Commands:

    /help              - Show this help message
    /exit, /quit       - Exit the REPL
    /clear             - Clear conversation history
    /history           - Show conversation history
    /status            - Show current session status
    /model [name]      - Show or change the current model
    /provider          - Show current provider
    /cd <path>         - Change working directory
    /pwd               - Print working directory
    /planning          - Toggle planning mode

System Information:
    - Provider: {provider}
    - Model: {model}
    - Working Dir: {working_dir}
    - Messages: {msg_count}

Tips:
    - Use Ctrl+D or /exit to quit
    - Use Ctrl+C to cancel current operation
    - Commands starting with / are system commands
    - Everything else is sent to the LLM
        """.format(
            provider=self.session.provider,
            model=self.session.model or "(default)",
            working_dir=self.session.working_dir,
            msg_count=len(self.session.messages),
        )
        self.session.print(help_text)
        return True

    def cmd_exit(self, args: list[str]) -> bool:
        """Exit the REPL.

        Args:
            args: Command arguments

        Returns:
            False to exit REPL
        """
        self.session.print("Goodbye! 👋")
        self.session.is_running = False
        return False

    def cmd_clear(self, args: list[str]) -> bool:
        """Clear conversation history.

        Args:
            args: Command arguments

        Returns:
            True to continue REPL
        """
        self.session.clear_history()
        self.session.print_success("Conversation history cleared")
        return True

    def cmd_history(self, args: list[str]) -> bool:
        """Show conversation history.

        Args:
            args: Command arguments

        Returns:
            True to continue REPL
        """
        if not self.session.messages:
            self.session.print_info("No conversation history")
            return True

        self.session.print("\nConversation History:\n")
        for i, msg in enumerate(self.session.messages, 1):
            role = msg["role"]
            content = msg["content"]
            if isinstance(content, str):
                preview = content[:100] + "..." if len(content) > 100 else content
            else:
                preview = str(content)[:100]

            self.session.print(f"{i}. [{role}] {preview}")

        self.session.print(f"\nTotal messages: {len(self.session.messages)}")
        return True

    def cmd_status(self, args: list[str]) -> bool:
        """Show current session status.

        Args:
            args: Command arguments

        Returns:
            True to continue REPL
        """
        status = f"""
Session Status:
    Provider: {self.session.provider}
    Model: {self.session.model or "(default)"}
    Working Directory: {self.session.working_dir}
    Messages: {len(self.session.messages)}
    Planning Mode: {"Enabled" if self.session.planning_mode else "Disabled"}
    Debug Mode: {"Enabled" if self.session.debug else "Disabled"}
        """
        self.session.print(status)
        return True

    def cmd_model(self, args: list[str]) -> bool:
        """Show or change the current model.

        Args:
            args: Command arguments

        Returns:
            True to continue REPL
        """
        if not args:
            self.session.print(f"Current model: {self.session.model or '(default)'}")
        else:
            new_model = args[0]
            self.session.model = new_model
            self.session.print_success(f"Model changed to: {new_model}")
        return True

    def cmd_provider(self, args: list[str]) -> bool:
        """Show current provider.

        Args:
            args: Command arguments

        Returns:
            True to continue REPL
        """
        self.session.print(f"Current provider: {self.session.provider}")
        self.session.print_info("Note: Provider cannot be changed during session")
        return True

    def cmd_cd(self, args: list[str]) -> bool:
        """Change working directory.

        Args:
            args: Command arguments

        Returns:
            True to continue REPL
        """
        if not args:
            self.session.print_error("Usage: /cd <path>")
            return True

        from pathlib import Path

        new_dir = Path(args[0]).expanduser().resolve()
        if not new_dir.exists():
            self.session.print_error(f"Directory not found: {new_dir}")
            return True

        if not new_dir.is_dir():
            self.session.print_error(f"Not a directory: {new_dir}")
            return True

        self.session.working_dir = new_dir
        self.session.print_success(f"Changed working directory to: {new_dir}")
        return True

    def cmd_pwd(self, args: list[str]) -> bool:
        """Print working directory.

        Args:
            args: Command arguments

        Returns:
            True to continue REPL
        """
        self.session.print(str(self.session.working_dir))
        return True

    def cmd_planning(self, args: list[str]) -> bool:
        """Toggle planning mode.

        Args:
            args: Command arguments

        Returns:
            True to continue REPL
        """
        self.session.planning_mode = not self.session.planning_mode
        status = "enabled" if self.session.planning_mode else "disabled"
        self.session.print_success(f"Planning mode {status}")

        if self.session.planning_mode:
            self.session.print_info(
                "The agent will present plans for approval before executing changes"
            )
        return True


__all__ = ["CommandHandler"]
