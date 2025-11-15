"""REPL (Read-Eval-Print Loop) implementation for Devorbit CLI."""

import traceback
from pathlib import Path
from typing import TYPE_CHECKING, Any

from devorbit import (
    ToolExecutor,
    bash,
    bash_output,
    edit_file,
    glob_files,
    grep_code,
    kill_shell,
    ls_directory,
    multi_edit_file,
    read_file,
    task,
    task_cancel,
    task_status,
    todo_read,
    todo_write,
    web_fetch_sync,
    web_search_sync,
    write_file,
)


if TYPE_CHECKING:
    from collections.abc import Callable

    from prompt_toolkit import PromptSession
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.styles import Style
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

        # Setup tool executor with all available tools
        self.tools: dict[str, Callable[..., Any]] = {
            # File tools
            "read_file": read_file,
            "write_file": write_file,
            "edit_file": edit_file,
            "multi_edit_file": multi_edit_file,
            "ls_directory": ls_directory,
            # Search tools
            "glob_files": glob_files,
            "grep_code": grep_code,
            # Bash tools
            "bash": bash,
            "bash_output": bash_output,
            "kill_shell": kill_shell,
            # Web tools
            "web_fetch": web_fetch_sync,
            "web_search": web_search_sync,
            # Todo tools
            "todo_read": todo_read,
            "todo_write": todo_write,
            # Agent/Task tools
            "task": task,
            "task_status": task_status,
            "task_cancel": task_cancel,
        }
        self.executor = ToolExecutor(tools=self.tools)

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

        # Regular message - send to LLM with tool execution
        try:
            self.session.add_message("user", user_input)
            self.session.print_info("Processing your request...")

            # Get model to use (use session model or default)
            model = self.session.model or self._get_default_model()

            # Execute tool loop with LLM
            response = self.executor.execute_tool_loop(
                client=self.session.client,
                messages=self.session.messages,
                model=model,
                max_tokens=4096,
                max_iterations=15,
            )

            # Extract and display text response
            response_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    response_text += block.text

            if response_text:
                self.session.print(f"\n{response_text}\n")
                self.session.add_message("assistant", response_text)
            else:
                self.session.print_info("Request completed (no text response)")

            # Display usage statistics if available
            if hasattr(response, "usage") and response.usage:
                usage = response.usage
                self.session.print(
                    f"[dim]Tokens: {usage.input_tokens} in, {usage.output_tokens} out[/dim]"
                )

        except Exception as e:
            self.session.print_error(f"Failed to process message: {e}")
            if self.session.debug:
                traceback.print_exc()

        return True

    def _get_default_model(self) -> str:
        """Get the default model for the current provider.

        Returns:
            Default model name
        """
        provider = self.session.provider
        defaults = {
            "anthropic": "claude-sonnet-4-5-20250929",
            "openai": "gpt-4-turbo-preview",
            "gemini": "gemini-pro",
            "mistral": "mistral-medium",
            "codellama": "codellama-34b",
        }
        return defaults.get(provider, "claude-sonnet-4-5-20250929")

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
