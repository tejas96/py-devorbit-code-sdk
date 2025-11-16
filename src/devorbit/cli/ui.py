"""UI components for pixel-perfect Claude Code CLI experience."""

import difflib
import re
from pathlib import Path
from typing import Any

from .interactive_prompt import InteractivePrompt


try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.prompt import Confirm, Prompt
    from rich.syntax import Syntax
    from rich.text import Text

    HAS_RICH = True
except ImportError:
    HAS_RICH = False


class CLIFormatter:
    """Pixel-perfect Claude Code-style CLI formatter."""

    def __init__(self, no_color: bool = False, output_format: str = "text") -> None:
        """Initialize CLI formatter.

        Args:
            no_color: Disable colored output
            output_format: Output format (text, json, markdown)
        """
        self.no_color = no_color
        self.output_format = output_format
        self.console = Console(no_color=no_color) if HAS_RICH else None

    def print_user_message(self, message: str) -> None:
        """Display user message in Claude Code style.

        Args:
            message: User's input message
        """
        if not HAS_RICH or self.console is None:
            print(f"\n> {message}\n")
            return

        self.console.print()
        self.console.print(f"> {message}", style="bold white")
        self.console.print()

    def print_assistant_message(self, message: str, streaming: bool = False) -> None:
        """Display assistant message in Claude Code style.

        Args:
            message: Assistant's response
            streaming: Whether this is part of streaming response
        """
        # Handle different output formats
        if self.output_format in ("json", "markdown"):
            # Plain text output for JSON and markdown modes
            if streaming:
                print(message, end="", flush=True)
            else:
                print(message)
            return

        # Rich text output (default)
        if not HAS_RICH or self.console is None:
            if streaming:
                print(message, end="", flush=True)
            else:
                print(message)
            return

        if not streaming:
            # Render markdown for complete messages
            md = Markdown(message)
            self.console.print(md)
        else:
            # Plain text for streaming
            self.console.print(message, end="", markup=False)

    def print_thinking(self) -> None:
        """Display thinking indicator (⏺ symbol)."""
        if not HAS_RICH or self.console is None:
            print("⏺ Thinking...")
            return

        text = Text()
        text.append("⏺ ", style="bold cyan")
        self.console.print()
        self.console.print(text, end="")

    def print_assistant_prefix(self) -> None:
        """Display assistant text prefix (⏺ symbol with newline)."""
        if not HAS_RICH or self.console is None:
            print("\n⏺ ", end="", flush=True)
            return

        text = Text()
        text.append("⏺ ", style="bold cyan")
        self.console.print()
        self.console.print(text, end="")

    def print_tool_use(
        self, tool_name: str, tool_input: dict[str, Any], description: str | None = None
    ) -> None:
        """Display tool usage in Claude Code style.

        Format: ⏺ ToolName(param1, param2...)
                  ⎿  Description

        Args:
            tool_name: Name of the tool being used
            tool_input: Tool input parameters
            description: Optional description of what the tool does
        """
        if not HAS_RICH or self.console is None:
            params = ", ".join(f"{k}={v!r}" for k, v in tool_input.items())
            print(f"⏺ {tool_name}({params})")
            if description:
                print(f"  ⎿  {description}")
            return

        # Convert snake_case tool names to PascalCase for display
        display_name = self._format_tool_name(tool_name)

        # Format parameters
        param_list: list[str] = []
        for key, value in tool_input.items():
            # Truncate long values
            value_str = str(value)
            if len(value_str) > 50:
                value_str = value_str[:47] + "…"
            param_list.append(f"{key}={value_str!r}")

        params_str = ", ".join(param_list) if param_list else ""

        text = Text()
        text.append("⏺ ", style="bold cyan")
        text.append(f"{display_name}(", style="cyan")
        text.append(params_str, style="dim")
        text.append(")", style="cyan")

        self.console.print()
        self.console.print(text)

        # Print description if provided
        if description:
            desc_text = Text()
            desc_text.append("  ⎿  ", style="cyan")
            desc_text.append(description, style="dim")
            self.console.print(desc_text)

    def print_tool_running(self) -> None:
        """Display tool running indicator (⎿ Running…)."""
        if not HAS_RICH or self.console is None:
            print("  ⎿ Running…", flush=True)
            return

        text = Text()
        text.append("  ⎿  ", style="cyan")
        text.append("Running…", style="dim")
        self.console.print(text)

    def print_tool_result(  # noqa: PLR0912
        self,
        tool_name: str,
        success: bool = True,
        result: Any = None,
        truncate: int = 10,
        custom_message: str | None = None,
    ) -> None:
        """Display tool result in Claude Code style.

        Format:   ⎿ Result message
                  Content (indented 2 spaces)
                  … +N lines (ctrl+o to expand)

        Args:
            tool_name: Name of the tool
            success: Whether tool execution succeeded
            result: Tool execution result
            truncate: Number of lines to show before truncating
            custom_message: Custom message to display instead of default
        """
        if not HAS_RICH or self.console is None:
            msg = custom_message or f"{tool_name} completed"
            print(f"  ⎿ {msg}")
            if result:
                print(f"     {result}")
            return

        # Claude Code style: Show content directly on ⎿ line if no custom message
        if result and not custom_message:
            # Show result content directly on the ⎿ line
            result_str = str(result)
            lines = result_str.split("\n")

            if len(lines) <= truncate:
                # Show all lines directly
                for i, line in enumerate(lines):
                    text = Text()
                    if i == 0:
                        text.append("  ⎿  ", style="cyan")
                    else:
                        text.append("     ", style="cyan")
                    text.append(line, style="dim")
                    self.console.print(text)
            else:
                # Show first line on ⎿, rest truncated
                text = Text()
                text.append("  ⎿  ", style="cyan")
                text.append(lines[0], style="dim")
                self.console.print(text)

                # Show remaining lines (truncated)
                for line in lines[1:truncate]:
                    self.console.print(f"     {line}", style="dim")

                remaining = len(lines) - truncate
                truncate_text = Text()
                truncate_text.append(f"     … +{remaining} lines", style="dim cyan")
                truncate_text.append(" (ctrl+o to expand)", style="dim italic")
                self.console.print(truncate_text)
        else:
            # Show custom message or default message
            text = Text()
            text.append("  ⎿  ", style="cyan")

            if success:
                if custom_message:
                    text.append(custom_message, style="dim")
                else:
                    display_name = self._format_tool_name(tool_name)
                    text.append(f"{display_name} completed", style="dim")
            else:
                text.append("Error", style="red")

            self.console.print(text)

            # Display result content if available (on separate lines)
            if result:
                self._print_result_content(result, truncate)

    def _print_result_content(self, content: Any, truncate: int = 10) -> None:
        """Print result content with truncation.

        Args:
            content: Content to print
            truncate: Number of lines before truncating
        """
        if not self.console:
            return

        content_str = str(content)
        lines = content_str.split("\n")

        if len(lines) <= truncate:
            # Show all lines
            for line in lines:
                self.console.print(f"     {line}", style="dim")
        else:
            # Show first few lines then truncate
            for line in lines[:truncate]:
                self.console.print(f"     {line}", style="dim")

            remaining = len(lines) - truncate
            truncate_text = Text()
            truncate_text.append(f"     … +{remaining} lines", style="dim cyan")
            truncate_text.append(" (ctrl+o to expand)", style="dim italic")
            self.console.print(truncate_text)

    def print_tool_confirmation(self, tool_name: str, tool_input: dict[str, Any]) -> None:
        """Display tool that's about to execute (before confirmation).

        This shows the tool in a different format before asking for confirmation.

        Args:
            tool_name: Name of the tool
            tool_input: Tool input parameters
        """
        # Show tool use without confirmation prompt
        self.print_tool_use(tool_name, tool_input)

    def print_token_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        cache_creation_tokens: int = 0,
        cache_read_tokens: int = 0,
    ) -> None:
        """Display token usage in Claude Code style.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cache_creation_tokens: Tokens used for cache creation
            cache_read_tokens: Tokens read from cache
        """
        if not HAS_RICH or self.console is None:
            total = input_tokens + output_tokens
            print(f"\n📊 Tokens: {input_tokens} in + {output_tokens} out = {total} total")
            if cache_creation_tokens or cache_read_tokens:
                print(f"   Cache: {cache_creation_tokens} created, {cache_read_tokens} read")
            return

        # Format token numbers with commas
        total = input_tokens + output_tokens

        # Create compact display
        self.console.print()
        token_text = Text()
        token_text.append("  ", style="")
        token_text.append(f"{input_tokens:,}", style="cyan")
        token_text.append(" in, ", style="dim")
        token_text.append(f"{output_tokens:,}", style="cyan")
        token_text.append(" out", style="dim")

        if cache_read_tokens > 0:
            token_text.append(f" ({cache_read_tokens:,} cached)", style="dim green")

        self.console.print(token_text)

    def print_error(self, message: str, details: str | None = None) -> None:
        """Display error message.

        Args:
            message: Error message
            details: Optional error details
        """
        if not HAS_RICH or self.console is None:
            print(f"\n✗ Error: {message}")
            if details:
                print(f"  Details: {details}")
            return

        text = Text()
        text.append("\n✗ ", style="bold red")
        text.append(message, style="red")

        self.console.print(text)

        if details:
            self.console.print(f"  {details}", style="dim red")

    def print_success(self, message: str) -> None:
        """Display success message.

        Args:
            message: Success message
        """
        if not HAS_RICH or self.console is None:
            print(f"✓ {message}")
            return

        text = Text()
        text.append("✓ ", style="bold green")
        text.append(message, style="green")
        self.console.print(text)

    def print_info(self, message: str) -> None:
        """Display info message.

        Args:
            message: Info message
        """
        if not HAS_RICH or self.console is None:
            print(f"ℹ {message}")  # noqa: RUF001
            return

        text = Text()
        text.append("ℹ ", style="bold blue")  # noqa: RUF001
        text.append(message, style="dim")
        self.console.print(text)

    def print_code_block(self, code: str, language: str = "python") -> None:
        """Display code block with syntax highlighting.

        Args:
            code: Code to display
            language: Programming language
        """
        if not HAS_RICH or self.console is None:
            print(f"\n```{language}")
            print(code)
            print("```")
            return

        syntax = Syntax(code, language, theme="monokai", line_numbers=False)
        self.console.print()
        self.console.print(syntax)

    def confirm(self, question: str, default: bool = True) -> bool:
        """Ask for user confirmation (Claude Code style).

        Args:
            question: Question to ask
            default: Default answer

        Returns:
            User's confirmation
        """
        if not HAS_RICH or self.console is None:
            response = input(f"\n❓ {question} [{'Y/n' if default else 'y/N'}]: ")
            if not response:
                return default
            return response.lower() in ("y", "yes")

        self.console.print()
        result = Confirm.ask(f"❓ {question}", default=default)
        return bool(result)

    def _extract_context_from_tool(self, tool_name: str, tool_input: dict[str, Any]) -> str | None:
        """Extract context (file/directory) from tool parameters.

        Args:
            tool_name: Name of the tool
            tool_input: Tool input parameters

        Returns:
            Context string (e.g., "sessions/", "config files") or None
        """
        # Try to find file/directory references in tool parameters
        for key, value in tool_input.items():
            if not isinstance(value, str):
                continue

            # Look for common path patterns
            # Pattern 1: .devorbit/sessions/
            if ".devorbit" in value:
                match = re.search(r"\.devorbit/([^/\s]+)", value)
                if match:
                    return f"{match.group(1)}/"

            # Pattern 2: Explicit path= or file= parameters
            if key in ("path", "file", "file_path", "directory", "dir"):
                try:
                    p = Path(value)
                    # Get the most specific directory name
                    if p.name:
                        return f"{p.name}/" if p.is_dir() or "/" in value else p.name
                except Exception:
                    pass

            # Pattern 3: Config files
            if any(ext in value for ext in [".json", ".yaml", ".yml", ".toml", ".ini"]):
                return "config files"

        return None

    def confirm_tool_boxed(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        description: str | None = None,
        context_options: list[str] | None = None,
    ) -> int:
        """Ask for tool execution confirmation with boxed dialog (Claude Code style).

        Args:
            tool_name: Name of the tool
            tool_input: Tool input parameters
            description: Optional description of what the tool does
            context_options: Optional context-aware permission options

        Returns:
            User choice (1 = Yes, 2 = Yes + allow context, 3 = No)
        """
        if not HAS_RICH or self.console is None or Panel is None:
            # Fallback to simple confirmation
            print(f"\n{tool_name} - {description or 'Execute tool'}")
            print("1. Yes")
            print("2. Yes, allow all")
            print("3. No")
            response = input("Choice [1-3]: ").strip()
            return int(response) if response.isdigit() else 1

        # Build panel content
        content = Text()

        # Tool name as header (e.g., "Bash command")
        display_name = self._format_tool_name(tool_name)
        content.append(f"{display_name} command\n\n", style="white")

        # Tool parameters (formatted nicely, indented)
        for _key, value in tool_input.items():
            value_str = str(value)
            # Wrap long values
            if len(value_str) > 70:
                lines = [value_str[i : i + 70] for i in range(0, len(value_str), 70)]
                content.append(f"  {value_str[:70]}\n", style="dim")
                for line in lines[1:]:
                    content.append(f"  {line}\n", style="dim")
            else:
                content.append(f"  {value_str}\n", style="dim")

        # Description if provided (on its own line, indented)
        if description:
            content.append(f"  {description}\n", style="dim")

        content.append("\nDo you want to proceed?\n", style="white")

        # Options
        content.append("❯ 1. Yes\n", style="cyan")  # noqa: RUF001

        # Generate context-aware option 2 if possible
        if context_options:
            for i, option in enumerate(context_options, 2):
                content.append(f"  {i}. {option}\n", style="dim")
        else:
            # Try to extract context from tool parameters
            context = self._extract_context_from_tool(tool_name, tool_input)
            if context:
                content.append(
                    f"  2. Yes, and always allow access to {context} from this project\n",
                    style="dim",
                )
            else:
                content.append("  2. Yes, allow all tools this session\n", style="dim")

        content.append("  3. No, and tell Claude what to do differently (esc)\n", style="dim")

        # Create panel (title is lowercase tool name for border)
        panel = Panel(
            content,
            title=f"[bold]{tool_name.lower()}[/bold]",
            border_style="cyan",
            padding=(1, 2),
        )

        self.console.print()
        self.console.print(panel)

        # Get user input with arrow-based selection
        context = self._extract_context_from_tool(tool_name, tool_input)
        option2_text = (
            f"Yes, and always allow access to {context} from this project"
            if context
            else "Yes, allow all tools this session"
        )

        choice = InteractivePrompt.select(
            message="",  # Message already shown in panel
            choices=[
                ("Yes", "1"),
                (option2_text, "2"),
                ("No, and tell Claude what to do differently", "3"),
            ],
            default="1",
        )
        return int(choice)

    def confirm_edit(  # noqa: PLR0911
        self,
        file_path: str,
        old_content: str,
        new_content: str,
        allow_all_session: bool = False,
    ) -> tuple[bool, bool]:
        """Ask for edit confirmation with diff preview (Claude Code style).

        Args:
            file_path: Path to file being edited
            old_content: Original content
            new_content: New content
            allow_all_session: Whether "allow all" option was already chosen

        Returns:
            Tuple of (confirmed, allow_all_edits)
        """
        if allow_all_session:
            return True, True

        if not HAS_RICH or self.console is None:
            print(f"\n📝 Edit: {file_path}")
            print("─" * 50)
            print("Choose an option:")
            print("  1: Yes")
            print("  2: Yes, allow all edits during this session")
            print("  3: No, and tell Claude what to do differently")
            response = input("Enter choice [1-3] (default: 1): ").strip()

            if response == "2":
                return True, True
            if response == "3":
                return False, False
            return True, False

        # Show file being edited
        self.console.print()
        file_text = Text()
        file_text.append("📝 Edit: ", style="bold yellow")
        file_text.append(file_path, style="cyan")
        self.console.print(file_text)

        # Show diff preview
        self._print_diff(old_content, new_content)

        # Show options
        self.console.print()
        self.console.print("Choose an option:", style="bold")
        self.console.print("  1: Yes", style="green")
        self.console.print("  2: Yes, allow all edits during this session", style="green")
        self.console.print("  3: No, and tell Claude what to do differently", style="red")

        # Get user choice
        choice = Prompt.ask(
            "Enter choice",
            choices=["1", "2", "3"],
            default="1",
        )

        if choice == "2":
            return True, True
        if choice == "3":
            return False, False
        return True, False

    def _print_diff(self, old_content: str, new_content: str, max_lines: int = 20) -> None:
        """Print diff between old and new content.

        Args:
            old_content: Original content
            new_content: New content
            max_lines: Maximum lines to show
        """
        if not self.console:
            return

        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)

        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            lineterm="",
            n=3,
        )

        diff_lines = list(diff)
        if not diff_lines:
            self.console.print("  (no changes)", style="dim")
            return

        # Show diff with syntax highlighting
        for idx, diff_line in enumerate(diff_lines[2:]):  # Skip the header lines
            if idx >= max_lines:
                remaining = len(diff_lines) - 2 - idx
                self.console.print(f"  ... +{remaining} more lines", style="dim cyan")
                break

            stripped_line = diff_line.rstrip()
            if stripped_line.startswith("+"):
                self.console.print(f"  {stripped_line}", style="green")
            elif stripped_line.startswith("-"):
                self.console.print(f"  {stripped_line}", style="red")
            elif stripped_line.startswith("@@"):
                self.console.print(f"  {stripped_line}", style="cyan dim")
            else:
                self.console.print(f"  {stripped_line}", style="dim")

    def print_todo_list(self, todos: list[dict[str, str]]) -> None:
        """Display todo list in Claude Code style.

        Args:
            todos: List of todo items with content, status, and activeForm
        """
        if not todos:
            return

        if not HAS_RICH or self.console is None:
            print("\n📋 Tasks:")
            for todo in todos:
                status = todo.get("status", "pending")
                content = todo.get("content", "")
                if status == "completed":
                    print(f"  ✓ {content}")
                elif status == "in_progress":
                    print(f"  ⏺ {content}")
                else:
                    print(f"  ☐ {content}")
            return

        # Display with rich formatting
        self.console.print()
        self.console.print("📋 Tasks:", style="bold cyan")

        for todo in todos:
            status = todo.get("status", "pending")
            content = todo.get("content", "")
            active_form = todo.get("activeForm", content)

            text = Text()
            if status == "completed":
                text.append("  ✓ ", style="green bold")
                text.append(content, style="dim strikethrough")
            elif status == "in_progress":
                text.append("  ⏺ ", style="cyan bold")
                text.append(active_form, style="cyan")
            else:
                text.append("  ☐ ", style="dim")
                text.append(content, style="white")

            self.console.print(text)

    def _format_tool_name(self, tool_name: str) -> str:
        """Convert snake_case tool name to PascalCase for display.

        Args:
            tool_name: Tool name in snake_case

        Returns:
            Tool name in PascalCase
        """
        # Special cases for common tools
        special_names = {
            "read_file": "Read",
            "write_file": "Write",
            "edit_file": "Edit",
            "bash": "Bash",
            "ls_directory": "List",
            "glob": "Glob",
            "grep": "Grep",
            "task": "Task",
        }

        if tool_name in special_names:
            return special_names[tool_name]

        # Convert snake_case to PascalCase
        words = tool_name.split("_")
        return "".join(word.capitalize() for word in words)


__all__ = ["CLIFormatter"]
