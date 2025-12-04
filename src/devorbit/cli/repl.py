"""REPL implementation using Component-Based Rendering (Claude Theme)."""

from pathlib import Path
from typing import TYPE_CHECKING, Any, cast


# 1. Low-level UI components
try:
    from prompt_toolkit import Application
    from prompt_toolkit.buffer import Buffer
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.enums import DEFAULT_BUFFER
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
    from prompt_toolkit.layout.containers import FloatContainer, HSplit, VSplit, Window
    from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
    from prompt_toolkit.layout.dimension import Dimension
    from prompt_toolkit.layout.layout import Layout
    from prompt_toolkit.styles import Style

    HAS_PROMPT_TOOLKIT = True
except ImportError:
    HAS_PROMPT_TOOLKIT = False

    # Define dummy Dimension to prevent NameError in class definition if import fails
    def Dimension(**kwargs: Any) -> Any:  # noqa: N802
        return None

    # Dummy for typing if import fails
    if TYPE_CHECKING:
        from prompt_toolkit.key_binding import KeyPressEvent
    else:

        class KeyPressEvent:
            app: Any
            current_buffer: Any


# 2. Updated Imports (Simple Relative Paths)
from .command_handler import CommandHandler
from .input import AutocompleteEngine, FileMentionParser, InputValidator
from .llm import LLMHandler
from .session import CLISession


class DevorbitREPL:
    """Interactive REPL matching Claude Theme."""

    def __init__(self, session: CLISession) -> None:
        self.session = session
        self.command_handler = CommandHandler(session)
        self.autocomplete = AutocompleteEngine(session.provider, session.working_dir)
        self.mention_parser = FileMentionParser(session.working_dir)
        self.input_validator = InputValidator()
        self.llm_handler = LLMHandler(session)

        self.attached_files: list[str] = []
        self.history_file = Path.home() / ".devorbit_history"

        # --- CLAUDE THEME ---
        self.style = Style.from_dict(
            {
                "frame.border": "#666666",  # Sophisticated Dark Grey
                "prompt": "#da7756 bold",  # Claude Orange for the ">"
                "input": "#f0f0f0",  # Soft Off-White
                "path": "#999999",  # Light Grey
                "git": "#555555",  # Dark Grey
                "status": "#da7756",  # Orange
                "docs": "#555555",
                "mode": "#da7756 bold",
            }
        )

    # ------------------------------------------------------------------
    #      DISPLAY INPUT PREVIEW
    # ------------------------------------------------------------------
    def display_input_preview(self, text: str) -> None:
        """Display preview of multiline input before processing."""
        # Strip whitespace to ensure accurate line count (ignores trailing newlines)
        clean_text = text.strip()
        lines = clean_text.split("\n")
        total_lines = len(lines)

        # Only show preview if we genuinely have multiple lines
        if total_lines > 1:
            if total_lines > 10:
                print(
                    f"\n\033[38;2;153;153;153m📝 Input: {total_lines} lines (showing last 10):\033[0m"
                )
                print(f"\033[38;2;153;153;153m... ({total_lines - 10} lines hidden)\033[0m")
                preview_lines = lines[-10:]
                # Start numbering from the correct line number
                for i, line in enumerate(preview_lines, total_lines - 9):
                    print(f"\033[38;2;240;240;240m{i:2d} | {line}\033[0m")
                print()
            else:
                print(f"\n\033[38;2;153;153;153m📝 Input: {total_lines} lines:\033[0m")
                for i, line in enumerate(lines, 1):
                    print(f"\033[38;2;240;240;240m{i:2d} | {line}\033[0m")
                print()

    # ------------------------------------------------------------------
    #      READ INPUT
    # ------------------------------------------------------------------
    def read_input(self) -> str | None:
        if not HAS_PROMPT_TOOLKIT:
            return input("> ")

        # Keybindings
        kb = KeyBindings()

        @kb.add("c-d")
        def _(event: KeyPressEvent) -> None:
            event.app.exit(result=None)

        @kb.add("enter")
        def _(event: KeyPressEvent) -> None:
            """
            Handle Enter key:
            - If it's a slash command (e.g., /help), submit immediately.
            - Otherwise, insert a newline (safe for pasting).
            """
            text = event.current_buffer.text

            # Immediate submit for slash commands (single line convenience)
            if text.strip().startswith("/"):
                event.current_buffer.append_to_history()
                event.app.exit(result=text)
                return

            # Default: Insert newline (Standard Multiline Editor Behavior)
            event.current_buffer.insert_text("\n")

        @kb.add("escape", "enter")  # Alt+Enter to submit
        def _(event: KeyPressEvent) -> None:
            text = event.current_buffer.text
            if text:
                event.current_buffer.append_to_history()
                event.app.exit(result=text)

        @kb.add("c-j")  # Ctrl+J to submit (alternative)
        def _(event: KeyPressEvent) -> None:
            text = event.current_buffer.text
            if text:
                event.current_buffer.append_to_history()
                event.app.exit(result=text)

        @kb.add("c-@")
        def _(event: KeyPressEvent) -> None:
            event.current_buffer.insert_text("@")

        @kb.add("c-v")
        def _(event: KeyPressEvent) -> None:
            """Allow pasting with Ctrl+V safely."""
            try:
                data = event.app.clipboard.get_data()
                event.current_buffer.paste_clipboard_data(data)
            except Exception:
                pass

        # Autocomplete
        buf = Buffer(
            name=DEFAULT_BUFFER,
            history=FileHistory(str(self.history_file)),
            completer=WordCompleter(
                list(self.autocomplete.command_completer.BUILT_IN_COMMANDS.keys())
            ),
            complete_while_typing=True,
            multiline=True,  # Enable multiline mode
        )

        # -------------------------
        # INPUT AREA
        # -------------------------
        # Note: Casting "center" and "right" to Any to allow string values
        # instead of importing strict WindowAlign enums which might cause version issues.
        input_content = VSplit(
            [
                Window(content=FormattedTextControl(HTML(" <prompt>></prompt> ")), width=3),
                Window(
                    content=BufferControl(buffer=buf),
                    style="class:input",
                    wrap_lines=True,
                    # Force start at 1 line, allow growing up to 15 lines max
                    height=Dimension(min=1, max=15),
                ),
            ]
        )

        # Custom "Dashed" Frame Construction
        border_char = "-"

        input_box = HSplit(
            [
                # Top Border
                Window(height=1, char=border_char, style="class:frame.border"),
                # Middle Section (Content only)
                input_content,
                # Bottom Border
                Window(height=1, char=border_char, style="class:frame.border"),
            ]
        )

        # Status Bar
        path_str = self.session.working_dir.name
        mode_str = "auto" if self.session.auto_approve_tools else "manual"

        status_bar = VSplit(
            [
                Window(
                    content=FormattedTextControl(HTML(f"<path>{path_str}</path> <git>(main)</git>"))
                ),
                Window(
                    content=FormattedTextControl(
                        HTML("<status>no sandbox</status> <docs>(see /docs)</docs>")
                    ),
                    align=cast("Any", "center"),
                ),
                Window(
                    content=FormattedTextControl(HTML(f"<mode>{mode_str}</mode>")),
                    width=6,
                    align=cast("Any", "right"),
                ),
            ],
            height=1,
        )

        layout = Layout(FloatContainer(content=HSplit([input_box, status_bar]), floats=[]))

        # APPLICATION
        app: Application[Any] = Application(
            layout=layout,
            key_bindings=kb,
            style=self.style,
            mouse_support=True,
            full_screen=False,  # Ensures it sits inline at the bottom
        )

        return cast("str | None", app.run())

    # ------------------------------------------------------------------
    # PROCESS INPUT
    # ------------------------------------------------------------------
    def process_input(self, user_input: str) -> bool:
        if not user_input:
            return True

        is_valid, error = self.input_validator.validate_input(user_input)
        if not is_valid:
            self.session.print_error(f"Invalid input: {error}")
            return True

        user_input = self.input_validator.sanitize_input(user_input)

        # Show preview if multiline input (more than 1 line)
        # Using stripped input to avoid counting trailing newlines
        if "\n" in user_input.strip():
            self.display_input_preview(user_input)

        # Note: We do NOT truncate the actual user_input anymore.
        # The full input is now sent to the LLM.

        if user_input.startswith("/"):
            return self.command_handler.handle_command(user_input)

        mentions = self.mention_parser.parse(user_input)
        if mentions:
            # Cast m to Any to access keys/attributes without typeddict issues
            self.attached_files = [
                cast("Any", m).get("path", cast("Any", m).get("file", "")) for m in mentions
            ]
            print(f"\033[38;2;218;119;86m📎 Attached: {', '.join(self.attached_files)}\033[0m")
            clean_input = self.mention_parser.remove_mentions(user_input)
        else:
            clean_input = user_input
            self.attached_files = []

        try:
            response = self.llm_handler.send_message(clean_input, stream=True)
            if response:
                self.session.add_message("assistant", response)
            else:
                self.session.print_warning("No response received")
        except Exception as e:
            self.session.print_error(f"Error: {e}")
            if self.session.debug:
                raise
        finally:
            self.attached_files = []

        return True

    # ------------------------------------------------------------------
    def run(self) -> None:
        while self.session.is_running:
            user_input = self.read_input()
            if user_input is None:
                self.session.print("\nGoodbye! 👋")
                break
            if not self.process_input(user_input):
                break


__all__ = ["DevorbitREPL"]
