"""Code block display with syntax highlighting.

Implements code block rendering with syntax highlighting using Pygments,
matching the Claude Code CLI specification.
"""

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from rich.console import Console


class CodeBlockDisplay:
    """Display code blocks with syntax highlighting.

    Supports various programming languages with Pygments syntax highlighting
    and optional line numbers.
    """

    def __init__(
        self,
        console: "Console | None" = None,
        no_color: bool = False,
        show_line_numbers: bool = True,
    ) -> None:
        """Initialize code block display.

        Args:
            console: Rich console instance (optional)
            no_color: Disable colored output
            show_line_numbers: Show line numbers in code blocks
        """
        self.console = console
        self.no_color = no_color
        self.show_line_numbers = show_line_numbers

    def display_code(
        self,
        code: str,
        language: str = "python",
        theme: str = "monokai",
        title: str | None = None,
    ) -> None:
        """Display a code block with syntax highlighting.

        Args:
            code: Code content
            language: Programming language for syntax highlighting
            theme: Color theme (default: monokai)
            title: Optional title for the code block

        Example:
            ```python  [Copy] [Apply]
            def hello_world():
                print("Hello, World!")
            ```
        """
        if self.console and not self.no_color:
            try:
                from rich.syntax import Syntax

                syntax = Syntax(
                    code,
                    language,
                    theme=theme,
                    line_numbers=self.show_line_numbers,
                    word_wrap=False,
                )

                if title:
                    from rich.panel import Panel

                    panel = Panel(
                        syntax,
                        title=title,
                        border_style="dim",
                        padding=(1, 2),
                    )
                    self.console.print(panel)
                else:
                    self.console.print(syntax)
            except ImportError:
                # Fallback without syntax highlighting
                self._display_plain_code(code, language, title)
        else:
            self._display_plain_code(code, language, title)

    def _display_plain_code(
        self, code: str, language: str, title: str | None = None
    ) -> None:
        """Display code without syntax highlighting.

        Args:
            code: Code content
            language: Programming language identifier
            title: Optional title
        """
        header = f"```{language}"
        if title:
            header += f"  {title}"

        if self.console:
            self.console.print(header)
            if self.show_line_numbers:
                for i, line in enumerate(code.splitlines(), 1):
                    self.console.print(f"{i:4d}  {line}")
            else:
                self.console.print(code)
            self.console.print("```")
        else:
            print(header)
            if self.show_line_numbers:
                for i, line in enumerate(code.splitlines(), 1):
                    print(f"{i:4d}  {line}")
            else:
                print(code)
            print("```")

    def display_inline_code(self, code: str) -> None:
        """Display inline code.

        Args:
            code: Code content
        """
        if self.console and not self.no_color:
            self.console.print(f"[cyan]`{code}`[/cyan]", end="")
        else:
            print(f"`{code}`", end="")


class DiffDisplay:
    """Display file diffs with highlighting.

    Supports unified and side-by-side diff formats matching the
    Claude Code CLI specification.
    """

    def __init__(
        self, console: "Console | None" = None, no_color: bool = False, format: str = "unified"
    ) -> None:
        """Initialize diff display.

        Args:
            console: Rich console instance (optional)
            no_color: Disable colored output
            format: Diff format ("unified" or "side-by-side")
        """
        self.console = console
        self.no_color = no_color
        self.format = format

    def display_diff(
        self, file_path: str, old_content: str, new_content: str, context_lines: int = 3
    ) -> None:
        """Display a file diff.

        Args:
            file_path: Path to the file
            old_content: Original content
            new_content: New content
            context_lines: Number of context lines to show

        Example:
            ╭─ src/main.py ──────────────────────────────────────╮
            │ @@ -10,3 +10,4 @@                                  │
            │ def main():                                        │
            │ -    print("Hello")                      [Old]    │
            │ +    print("Hello, World!")              [New]    │
            │ +    return 0                            [New]    │
            ╰────────────────────────────────────────────────────╯
        """
        if self.format == "unified":
            self._display_unified_diff(file_path, old_content, new_content, context_lines)
        else:
            self._display_side_by_side_diff(file_path, old_content, new_content)

    def _display_unified_diff(
        self, file_path: str, old_content: str, new_content: str, context_lines: int
    ) -> None:
        """Display unified diff format.

        Args:
            file_path: Path to the file
            old_content: Original content
            new_content: New content
            context_lines: Number of context lines
        """
        import difflib

        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)

        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm="",
            n=context_lines,
        )

        if self.console and not self.no_color:
            from .colors import Colors

            self.console.print(f"\n[bold]╭─ {file_path} {'─' * (60 - len(file_path))}╮[/bold]")

            for line in diff:
                if line.startswith("+++") or line.startswith("---"):
                    continue
                if line.startswith("@@"):
                    self.console.print(f"[dim]│ {line}[/dim]")
                elif line.startswith("+"):
                    color = Colors.rich_success()
                    self.console.print(f"[{color}]│ {line}[/{color}]")
                elif line.startswith("-"):
                    color = Colors.rich_error()
                    self.console.print(f"[{color}]│ {line}[/{color}]")
                else:
                    self.console.print(f"│ {line}")

            self.console.print(f"[bold]╰{'─' * 60}╯[/bold]\n")
        else:
            print(f"\n╭─ {file_path} {'─' * (60 - len(file_path))}╮")

            for line in diff:
                if line.startswith("+++") or line.startswith("---"):
                    continue
                if line.startswith("+"):
                    print(f"│ + {line[1:]}")
                elif line.startswith("-"):
                    print(f"│ - {line[1:]}")
                else:
                    print(f"│ {line}")

            print(f"╰{'─' * 60}╯\n")

    def _display_side_by_side_diff(
        self, file_path: str, old_content: str, new_content: str
    ) -> None:
        """Display side-by-side diff format.

        Args:
            file_path: Path to the file
            old_content: Original content
            new_content: New content
        """
        # Simple side-by-side implementation
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()

        max_len = max(len(old_lines), len(new_lines))

        if self.console and not self.no_color:
            from .colors import Colors

            self.console.print(
                f"\n[bold]╭─ {file_path} (Side-by-Side) {'─' * (50 - len(file_path))}╮[/bold]"
            )
            self.console.print("│ [bold]Old[/bold]                   │ [bold]New[/bold]")
            self.console.print(f"├{'─' * 30}┼{'─' * 30}┤")

            for i in range(max_len):
                old_line = old_lines[i] if i < len(old_lines) else ""
                new_line = new_lines[i] if i < len(new_lines) else ""

                old_display = old_line[:27] + "..." if len(old_line) > 30 else old_line
                new_display = new_line[:27] + "..." if len(new_line) > 30 else new_line

                color_old = Colors.rich_error() if old_line != new_line else ""
                color_new = Colors.rich_success() if old_line != new_line else ""

                if color_old:
                    self.console.print(
                        f"│ [{color_old}]{old_display:30}[/{color_old}] │ "
                        f"[{color_new}]{new_display:30}[/{color_new}]"
                    )
                else:
                    self.console.print(f"│ {old_display:30} │ {new_display:30}")

            self.console.print(f"[bold]╰{'─' * 62}╯[/bold]\n")
        else:
            print(f"\n╭─ {file_path} (Side-by-Side) {'─' * (50 - len(file_path))}╮")
            print("│ Old                       │ New")
            print(f"├{'─' * 30}┼{'─' * 30}┤")

            for i in range(max_len):
                old_line = old_lines[i] if i < len(old_lines) else ""
                new_line = new_lines[i] if i < len(new_lines) else ""

                old_display = old_line[:27] + "..." if len(old_line) > 30 else old_line
                new_display = new_line[:27] + "..." if len(new_line) > 30 else new_line

                marker = "≠" if old_line != new_line else " "
                print(f"│ {marker} {old_display:28} │ {new_display:28}")

            print(f"╰{'─' * 62}╯\n")


__all__ = ["CodeBlockDisplay", "DiffDisplay"]
