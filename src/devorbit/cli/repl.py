"""REPL implementation using Component-Based Rendering (Claude Theme)."""

import math
import shutil
from pathlib import Path
from typing import Any, cast


# 1. Low-level UI components
try:
    from prompt_toolkit import Application
    from prompt_toolkit.buffer import Buffer
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.enums import DEFAULT_BUFFER
    from prompt_toolkit.filters import Condition
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
    def Dimension(**kwargs: Any) -> Any:  # type: ignore[no-redef] # noqa: N802
        return None

    # Fix: Add type: ignore[no-redef] to silence mypy error
    class KeyPressEvent:  # type: ignore[no-redef]
        pass


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

        # STATE: Tracks if we are in paste mode
        self.paste_mode = False

        # --- CLAUDE THEME ---
        self.style = Style.from_dict(
            {
                "frame.border": "#666666",
                "prompt": "#da7756 bold",
                "input": "#f0f0f0",
                "path": "#999999",
                "git": "#555555",
                "status": "#da7756",
                "docs": "#555555",
                "mode": "#da7756 bold",
                "paste-warning": "#ffffff bg:#da7756 bold",
            }
        )

    # ------------------------------------------------------------------
    #      DISPLAY INPUT PREVIEW
    # ------------------------------------------------------------------
    def display_input_preview(self, text: str) -> None:
        clean_text = text.strip()
        lines = clean_text.split("\n")
        total_lines = len(lines)

        if total_lines > 1:
            if total_lines > 10:
                print(
                    f"\n\033[38;2;153;153;153m📝 Input: {total_lines} lines (showing last 10):\033[0m"
                )
                print(f"\033[38;2;153;153;153m... ({total_lines - 10} lines hidden)\033[0m")
                preview_lines = lines[-10:]
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

        kb = KeyBindings()

        @kb.add("c-d")
        def _(event: KeyPressEvent) -> None:
            event.app.exit(result=None)

        # --- CONDITIONS for Modes ---
        @Condition
        def is_paste_mode() -> bool:
            return self.paste_mode

        @Condition
        def is_normal_mode() -> bool:
            return not self.paste_mode

        # --- KEY BINDINGS ---

        # 1. Ctrl+F2: Toggle Paste Mode
        @kb.add("c-f2")
        def _(event: KeyPressEvent) -> None:
            self.paste_mode = not self.paste_mode

        # 2. NORMAL MODE: Enter = Submit
        @kb.add("enter", filter=is_normal_mode)
        def _(event: KeyPressEvent) -> None:
            text = event.current_buffer.text
            if text.strip():
                event.current_buffer.append_to_history()
                event.app.exit(result=text)
            else:
                event.current_buffer.insert_text("\n")

        # 3. PASTE MODE: Enter = New Line (Safe for pasting)
        @kb.add("enter", filter=is_paste_mode)
        def _(event: KeyPressEvent) -> None:
            event.current_buffer.insert_text("\n")

        # 4. Universal Submit: Alt+Enter (Works in both modes)
        @kb.add("escape", "enter")
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
            try:
                data = event.app.clipboard.get_data()
                event.current_buffer.paste_clipboard_data(data)
            except Exception:
                pass

        buf = Buffer(
            name=DEFAULT_BUFFER,
            history=FileHistory(str(self.history_file)),
            completer=WordCompleter(
                list(self.autocomplete.command_completer.BUILT_IN_COMMANDS.keys())
            ),
            complete_while_typing=True,
            multiline=True,
        )

        # -------------------------
        # INPUT AREA (With Width Fix)
        # -------------------------
        def get_input_height() -> int:
            try:
                term_width = shutil.get_terminal_size().columns
            except Exception:
                term_width = 80

            effective_width = max(term_width - 5, 10)
            text = buf.text
            visual_lines = 0

            for line in text.split("\n"):
                line_length = len(line)
                if line_length == 0:
                    visual_lines += 1
                else:
                    visual_lines += math.ceil(line_length / effective_width)

            return min(max(visual_lines, 1), 15)

        input_content = VSplit(
            [
                Window(content=FormattedTextControl(HTML(" <prompt>></prompt> ")), width=3),
                Window(
                    content=BufferControl(buffer=buf),
                    style="class:input",
                    wrap_lines=True,
                    dont_extend_width=False,
                ),
            ],
            height=get_input_height,
        )

        border_char = "-"

        input_box = HSplit(
            [
                Window(
                    height=1, char=border_char, style="class:frame.border", dont_extend_width=False
                ),
                input_content,
                Window(
                    height=1, char=border_char, style="class:frame.border", dont_extend_width=False
                ),
            ]
        )

        # --- DYNAMIC STATUS BAR ---
        def get_status_text() -> HTML:
            if self.paste_mode:
                return HTML("<paste-warning> [PASTE MODE] (Enter=NewLine) </paste-warning>")
            return HTML("<status>no sandbox</status> <docs>(Ctrl+F2 for Paste Mode)</docs>")

        path_str = self.session.working_dir.name
        mode_str = "auto" if self.session.auto_approve_tools else "manual"

        status_bar = VSplit(
            [
                Window(
                    content=FormattedTextControl(HTML(f"<path>{path_str}</path> <git>(main)</git>"))
                ),
                Window(
                    content=FormattedTextControl(get_status_text),
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

        app: Application[Any] = Application(
            layout=layout,
            key_bindings=kb,
            style=self.style,
            mouse_support=True,
            full_screen=False,
        )

        return cast("str | None", app.run())

    # ------------------------------------------------------------------
    # PROCESS INPUT
    # ------------------------------------------------------------------
    def process_input(self, user_input: str) -> bool:
        # Reset paste mode after every submission
        self.paste_mode = False

        if not user_input:
            return True

        is_valid, error = self.input_validator.validate_input(user_input)
        if not is_valid:
            self.session.print_error(f"Invalid input: {error}")
            return True

        user_input = self.input_validator.sanitize_input(user_input)

        if "\n" in user_input.strip():
            self.display_input_preview(user_input)

        if user_input.startswith("/"):
            return self.command_handler.handle_command(user_input)

        mentions = self.mention_parser.parse(user_input)
        if mentions:
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

    def run(self) -> None:
        while self.session.is_running:
            user_input = self.read_input()
            if user_input is None:
                self.session.print("\nGoodbye! 👋")
                break
            if not self.process_input(user_input):
                break


__all__ = ["DevorbitREPL"]
