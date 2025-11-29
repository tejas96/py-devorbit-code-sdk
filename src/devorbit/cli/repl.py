"""REPL implementation using Component-Based Rendering (Claude Theme) + Tips."""

import sys
import random
from pathlib import Path
from typing import TYPE_CHECKING

# 1. Low-level UI components
try:
    from prompt_toolkit import Application
    from prompt_toolkit.buffer import Buffer
    from prompt_toolkit.layout.containers import Window, FloatContainer, HSplit, VSplit
    from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
    from prompt_toolkit.layout.layout import Layout
    from prompt_toolkit.layout.dimension import Dimension
    from prompt_toolkit.widgets import Frame
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.styles import Style
    from prompt_toolkit.enums import DEFAULT_BUFFER
    HAS_PROMPT_TOOLKIT = True
except ImportError:
    HAS_PROMPT_TOOLKIT = False

# 2. Robust Import Strategy
try:
    from .commands import CommandHandler
    from .input import AutocompleteEngine, FileMentionParser, InputValidator
    from .llm import LLMHandler
    from .session import CLISession
except (ImportError, ValueError):
    try:
        from ..commands import CommandHandler
        from ..input import AutocompleteEngine, FileMentionParser, InputValidator
        from ..llm import LLMHandler
        from ..session import CLISession
    except (ImportError, ValueError):
        current_path = Path(__file__).resolve().parent
        parent_path = current_path.parent
        if str(parent_path) not in sys.path:
            sys.path.insert(0, str(parent_path))

        from devorbit.commands import CommandHandler
        from devorbit.input import AutocompleteEngine, FileMentionParser, InputValidator
        from devorbit.llm import LLMHandler
        from devorbit.session import CLISession


class DevorbitREPL:
    """Interactive REPL matching Claude Theme + rotating tips."""

    # ------------------------------
    #     RANDOM TIPS FEATURE
    # ------------------------------
    TIPS = [
        "Type your message or @path/to/file",
        "Tip: Use @filename to reference files",
        "Tip: Try /help to see available commands",
        "Tip: Press Ctrl+D to exit anytime",
        "Tip: Use /clear to clear history",
        "Tip: Try /model to switch AI models",
        "Tip: Reference files with @src/main.py",
        "Tip: Use /history to see recent messages",
        "Tip: Press Ctrl+@ for quick file mention",
        "Tip: Use /exit or Ctrl+D to quit gracefully",
    ]

    def __init__(self, session: CLISession) -> None:
        self.session = session
        self.command_handler = CommandHandler(session)
        self.autocomplete = AutocompleteEngine(session.provider, session.working_dir)
        self.mention_parser = FileMentionParser(session.working_dir)
        self.input_validator = InputValidator()
        self.llm_handler = LLMHandler(session)

        self.attached_files: list[str] = []
        self.history_file = Path.home() / ".devorbit_history"

        # Pick a random tip
        self.current_tip = random.choice(self.TIPS)

        # --- CLAUDE THEME ---
        self.style = Style.from_dict({
            "frame.border": "#666666",
            "prompt": "#da7756 bold",
            "input": "#f0f0f0",
            "path": "#999999",
            "git": "#555555",
            "status": "#da7756",
            "docs": "#555555",
            "mode": "#da7756 bold",
            "tip": "#777777 italic",
        })

    # ------------------------------------------------------------------
    #     READ INPUT WITH TIP DISPLAY INSIDE THE INPUT BOX
    # ------------------------------------------------------------------
    def read_input(self) -> str | None:
        if not HAS_PROMPT_TOOLKIT:
            return input("> ")

        # Keybindings
        kb = KeyBindings()

        @kb.add("c-d")
        def _(event):
            event.app.exit(result=None)

        @kb.add("enter")
        def _(event):
            text = event.current_buffer.text
            event.current_buffer.append_to_history()
            event.app.exit(result=text)

        @kb.add("c-@")
        def _(event):
            event.current_buffer.insert_text("@")

        # Autocomplete
        buf = Buffer(
            name=DEFAULT_BUFFER,
            history=FileHistory(str(self.history_file)),
            completer=WordCompleter(
                list(self.autocomplete.command_completer.BUILT_IN_COMMANDS.keys())
            ),
            complete_while_typing=True,
        )

        # -------------------------
        # TIP DISPLAY (NEW!)
        # -------------------------
        tip_html = HTML(f"<tip>{self.current_tip}</tip>")

        tip_window = Window(
            content=FormattedTextControl(text=tip_html),
            height=1,
            style="class:tip",
        )

        # -------------------------
        # INPUT AREA
        # -------------------------
        input_content = VSplit([
            Window(content=FormattedTextControl(HTML(" <prompt>></prompt> ")), width=3),
            Window(content=BufferControl(buffer=buf), style="class:input", wrap_lines=True),
        ])

        # Frame containing tip + input box
        input_box = Frame(
            #title=HTML("<title>devorbit</title>"),
            body=HSplit([
                tip_window,        # <<<<< TIP ADDED HERE
                input_content,
            ]),
            style="class:frame",
        )

        # Status Bar
        path_str = self.session.working_dir.name
        mode_str = "auto" if self.session.auto_approve_tools else "manual"

        status_bar = VSplit([
            Window(content=FormattedTextControl(HTML(f"<path>{path_str}</path> <git>(main)</git>"))),
            Window(content=FormattedTextControl(HTML("<status>no sandbox</status> <docs>(see /docs)</docs>")), align="center"),
            Window(content=FormattedTextControl(HTML(f"<mode>{mode_str}</mode>")), width=6, align="right"),
        ], height=1)

        layout = Layout(FloatContainer(
            content=HSplit([input_box, status_bar]),
            floats=[]
        ))

        # APPLICATION
        app = Application(
            layout=layout,
            key_bindings=kb,
            style=self.style,
            mouse_support=True,
            full_screen=False,
        )

        # ROTATE TIP FOR NEXT INPUT
        self.current_tip = random.choice(self.TIPS)

        result = app.run()
        return result

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

        if user_input.startswith("/"):
            return self.command_handler.handle_command(user_input)

        mentions = self.mention_parser.parse(user_input)
        if mentions:
            self.attached_files = [m.get("path", m.get("file", "")) for m in mentions]
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
