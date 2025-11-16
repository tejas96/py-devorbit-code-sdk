"""REPL (Read-Eval-Print Loop) with Claude Code-style UX."""

import traceback
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

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
    from prompt_toolkit import PromptSession
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.styles import Style

    from .session import CLISession

from .commands import CommandHandler
from .streaming import StreamingHandler
from .ui import CLIFormatter


try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.styles import Style

    HAS_PROMPT_TOOLKIT = True
except ImportError:
    PromptSession = None
    HTML = None
    FileHistory = None
    Style = None
    HAS_PROMPT_TOOLKIT = False


class DevorbitREPL:
    """Devorbit REPL with Claude Code-style user experience."""

    def __init__(
        self,
        session: "CLISession",
        confirm_tools: bool = True,
        stream: bool = True,
    ) -> None:
        """Initialize enhanced REPL.

        Args:
            session: CLI session instance
            confirm_tools: Ask for confirmation before executing tools
            stream: Enable streaming responses
        """
        self.session = session
        self.command_handler = CommandHandler(session)
        self.confirm_tools = confirm_tools
        self.stream = stream

        # Initialize UI formatter
        self.formatter = CLIFormatter(no_color=session.no_color)

        # Initialize streaming handler
        self.streaming_handler = StreamingHandler(
            formatter=self.formatter,
            confirm_tools=confirm_tools,
        )

        # Setup tools (same as before but cleaner)
        self.tools: dict[str, Callable[..., Any]] = self._setup_tools()
        self.executor = ToolExecutor(tools=self.tools)

        # Setup prompt session
        self.prompt_session: PromptSession[str] | None = None
        self.prompt_style: Style | None = None
        self._setup_prompt()

    def _setup_tools(self) -> dict[str, Callable[..., Any]]:
        """Set up all available tools.

        Returns:
            Dictionary of tool name to function
        """
        return {
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

    def _setup_prompt(self) -> None:
        """Set up prompt toolkit session."""
        if not HAS_PROMPT_TOOLKIT:
            return

        history_file = Path.home() / ".devorbit_history"

        if PromptSession is not None and FileHistory is not None:
            self.prompt_session = PromptSession(history=FileHistory(str(history_file)))

        if Style is not None:
            self.prompt_style = Style.from_dict(
                {
                    "prompt": "bold cyan",
                    "path": "yellow",
                }
            )

    def get_prompt_message(self) -> str:
        """Get prompt message with current context.

        Returns:
            Formatted prompt string
        """
        if HAS_PROMPT_TOOLKIT and HTML is not None and self.prompt_style is not None:
            cwd = self.session.working_dir.name
            return cast(
                "str",
                HTML(f"<prompt>devorbit</prompt> <path>{cwd}</path><prompt>></prompt> ").value,
            )
        return "devorbit> "

    def read_input(self) -> str | None:
        """Read user input from prompt.

        Returns:
            User input or None if EOF
        """
        try:
            if HAS_PROMPT_TOOLKIT and self.prompt_session is not None:
                prompt_msg = self.get_prompt_message()
                user_input = self.prompt_session.prompt(
                    prompt_msg,
                    style=self.prompt_style,
                )
                return cast("str", user_input.strip())

            # Fallback to basic input
            user_input = input(self.get_prompt_message())
            return user_input.strip()
        except EOFError:
            return None
        except KeyboardInterrupt:
            self.formatter.print_info("\nUse /exit or Ctrl+D to quit")
            return ""

    def process_input(self, user_input: str) -> bool:
        """Process user input with Claude Code-style interaction.

        Args:
            user_input: User's input string

        Returns:
            True to continue, False to exit
        """
        if not user_input:
            return True

        # Handle slash commands
        if user_input.startswith("/"):
            return self.command_handler.handle_command(user_input)

        # Display user message in Claude Code style
        self.formatter.print_user_message(user_input)

        # Add to message history
        self.session.add_message("user", user_input)

        try:
            # Get model
            model = self.session.model or self._get_default_model()

            # Process with streaming or non-streaming
            if self.stream:
                self._process_with_streaming(model)
            else:
                self._process_without_streaming(model)

        except Exception as e:
            if self.session.debug:
                self.formatter.print_error(f"Request failed: {e!s}")
                traceback.print_exc()
            else:
                self.formatter.print_error("Request failed")

        return True

    def _process_with_streaming(self, model: str) -> None:
        """Process request with streaming response.

        Args:
            model: Model to use
        """
        # Get tool definitions
        tool_definitions = [
            func.tool_definition for func in self.tools.values() if hasattr(func, "tool_definition")
        ]

        # Call API with streaming
        response_stream = self.session.client.messages.stream(
            model=model,
            max_tokens=4096,
            messages=self.session.messages,
            tools=tool_definitions,
        )

        # Handle stream
        with response_stream as stream:
            text_content, tool_uses, usage_data = self.streaming_handler.handle_stream(stream)

            # Execute confirmed tools
            if tool_uses:
                self._execute_tools(tool_uses, model, tool_definitions)

            # Add assistant message to history
            if text_content:
                self.session.add_message("assistant", text_content)

            # Display token usage
            if usage_data:
                self.formatter.print_token_usage(
                    input_tokens=usage_data.get("input_tokens", 0),
                    output_tokens=usage_data.get("output_tokens", 0),
                    cache_creation_tokens=usage_data.get("cache_creation_input_tokens", 0),
                    cache_read_tokens=usage_data.get("cache_read_input_tokens", 0),
                )

    def _process_without_streaming(self, model: str) -> None:
        """Process request without streaming.

        Args:
            model: Model to use
        """
        # Get tool definitions
        tool_definitions = [
            func.tool_definition for func in self.tools.values() if hasattr(func, "tool_definition")
        ]

        # Call API
        response = self.session.client.messages.create(
            model=model,
            max_tokens=4096,
            messages=self.session.messages,
            tools=tool_definitions,
        )

        # Handle response
        text_content, tool_uses = self.streaming_handler.handle_non_streaming(response)

        # Execute confirmed tools
        if tool_uses:
            self._execute_tools(tool_uses, model, tool_definitions)

        # Add assistant message to history
        if text_content:
            self.session.add_message("assistant", text_content)

        # Display token usage
        if hasattr(response, "usage") and response.usage:
            usage = response.usage
            self.formatter.print_token_usage(
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                cache_creation_tokens=getattr(usage, "cache_creation_input_tokens", 0),
                cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0),
            )

    def _execute_tools(
        self,
        tool_uses: list[dict[str, Any]],
        model: str,
        tool_definitions: list[dict[str, Any]],
    ) -> None:
        """Execute confirmed tools and handle responses.

        Args:
            tool_uses: List of tool use dictionaries
            model: Model being used
            tool_definitions: Available tool definitions
        """
        tool_results = []
        assistant_content = []

        for tool_use in tool_uses:
            if not tool_use.get("confirmed", False):
                # Tool execution declined
                self.formatter.print_info(f"Skipped {tool_use['name']}")
                continue

            # Execute tool
            tool_func = self.tools.get(tool_use["name"])
            if not tool_func:
                self.formatter.print_error(f"Tool not found: {tool_use['name']}")
                continue

            try:
                result = tool_func(**tool_use["input"])

                # Extract meaningful content from result
                display_result = self._extract_result_content(tool_use["name"], result)

                # Generate Claude Code-style result message
                result_message = self._generate_result_message(tool_use["name"], result)

                # Display result with custom message
                self.formatter.print_tool_result(
                    tool_use["name"],
                    True,
                    display_result,
                    custom_message=result_message,
                )

                # Add to results
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use["id"],
                        "content": str(result),
                    }
                )

                assistant_content.append(
                    {
                        "type": "tool_use",
                        "id": tool_use["id"],
                        "name": tool_use["name"],
                        "input": tool_use["input"],
                    }
                )

            except Exception as e:
                self.formatter.print_tool_result(tool_use["name"], False)
                if self.session.debug:
                    self.formatter.print_error("Tool execution failed", str(e))
                    traceback.print_exc()
                else:
                    self.formatter.print_error("Tool execution failed")

        # If we have tool results, continue the conversation
        if tool_results:
            # Add assistant message with tool uses
            self.session.messages.append({"role": "assistant", "content": assistant_content})  # type: ignore[typeddict-item]

            # Add tool results
            self.session.messages.append({"role": "user", "content": tool_results})  # type: ignore[typeddict-item]

            # Get follow-up response
            if self.stream:
                self._process_with_streaming(model)
            else:
                self._process_without_streaming(model)

    def _extract_result_content(self, tool_name: str, result: Any) -> str:  # noqa: PLR0911
        """Extract meaningful content from tool result for display.

        Args:
            tool_name: Name of the tool
            result: Tool result

        Returns:
            Meaningful content to display (empty string if no content to show)
        """
        # If result is a string, return it
        if isinstance(result, str):
            return result

        # If result is a dict, extract relevant content based on tool
        if isinstance(result, dict):
            # Write/Edit operations: don't show content, message is enough
            if tool_name in ("write_file", "edit_file", "multi_edit_file"):
                return ""

            # Read file: show content
            if tool_name == "read_file" and "content" in result:
                return str(result["content"])

            # Bash tools: show stdout
            if "stdout" in result:
                stdout = str(result["stdout"])
                # Only show if there's actual output
                return stdout if stdout.strip() else ""

            # List/glob/grep tools: show matches
            if "matches" in result:
                matches = result["matches"]
                if isinstance(matches, list):
                    return "\n".join(str(m) for m in matches) if matches else ""
                return str(matches)

            # For other tools, don't show raw dict
            return ""

        # Fallback: don't show raw objects
        return ""

    def _generate_result_message(self, tool_name: str, result: Any) -> str:  # noqa: PLR0911
        """Generate Claude Code-style result message.

        Args:
            tool_name: Name of the tool that was executed
            result: Result from tool execution

        Returns:
            Descriptive result message (e.g., "Wrote 170 lines to file.py")
        """
        if isinstance(result, dict):
            # Write/Edit file tools
            if tool_name in ("write_file", "edit_file") and "file_path" in result:
                file_path = result["file_path"]
                if "lines_written" in result:
                    lines = result["lines_written"]
                    return f"Wrote {lines} lines to {file_path}"
                if "content" in result:
                    lines = len(result["content"].splitlines())
                    return f"Wrote {lines} lines to {file_path}"
                return f"Updated {file_path}"

            # Read file tools
            if tool_name == "read_file" and "file_path" in result:
                file_path = result["file_path"]
                total_lines = result.get("total_lines", result.get("lines_shown", 0))
                if total_lines:
                    return f"Read {total_lines} lines from {file_path}"
                return f"Read {file_path}"

            # Bash tools
            if tool_name == "bash" and "stdout" in result:
                stdout = result["stdout"].strip()
                lines = len(stdout.splitlines()) if stdout else 0
                if lines > 0:
                    return f"Executed command ({lines} lines output)"
                return "Executed command"

            # List/glob tools
            if "matches" in result:
                matches = result["matches"]
                count = len(matches) if isinstance(matches, list) else 1
                return f"Found {count} matches"

        # Default message
        display_name = self._format_tool_name(tool_name)
        return f"{display_name} completed"

    def _format_tool_name(self, tool_name: str) -> str:
        """Convert snake_case tool name to PascalCase for display.

        Args:
            tool_name: Tool name in snake_case

        Returns:
            Tool name in PascalCase
        """
        special_names = {
            "read_file": "Read",
            "write_file": "Write",
            "edit_file": "Edit",
            "bash": "Bash",
            "ls_directory": "List",
            "glob_files": "Glob",
            "grep_code": "Grep",
            "task": "Task",
        }

        if tool_name in special_names:
            return special_names[tool_name]

        # Convert snake_case to PascalCase
        words = tool_name.split("_")
        return "".join(word.capitalize() for word in words)

    def _get_default_model(self) -> str:
        """Get default model for current provider.

        Returns:
            Default model name
        """
        defaults = {
            "anthropic": "claude-sonnet-4-5-20250929",
            "openai": "gpt-4-turbo-preview",
            "gemini": "gemini-2.5-flash",
            "mistral": "mistral-medium",
            "codellama": "codellama-34b",
        }
        return defaults.get(self.session.provider, "claude-sonnet-4-5-20250929")

    def run(self) -> None:
        """Start the enhanced REPL loop."""
        while self.session.is_running:
            user_input = self.read_input()

            # Handle EOF
            if user_input is None:
                self.formatter.print_info("\nGoodbye! 👋")
                break

            # Process input
            continue_running = self.process_input(user_input)
            if not continue_running:
                break


__all__ = ["DevorbitREPL"]
