"""Multi-line input editor for Devorbit CLI.

Implements enhanced input editing with multi-line support, keybindings,
and visual feedback matching the Claude Code CLI specification.
"""

from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from prompt_toolkit import PromptSession


class MultiLineEditor:
    """Multi-line input editor with enhanced keybindings.

    Supports:
    - Enter: New line in multi-line mode
    - Ctrl+Enter: Submit message
    - Shift+Enter: New line (always)
    - Ctrl+C: Cancel/Interrupt
    - Ctrl+K: Delete from cursor to end
    - Ctrl+U: Delete from cursor to beginning
    - Ctrl+W: Delete previous word
    - Ctrl+L: Clear screen (keep conversation)

    Example:
        >>> editor = MultiLineEditor()
        >>> text = editor.get_input(multiline=True)
    """

    def __init__(
        self,
        prompt_session: "PromptSession[str] | None" = None,
        multiline: bool = False,
    ) -> None:
        """Initialize multi-line editor.

        Args:
            prompt_session: Existing prompt_toolkit session (optional)
            multiline: Enable multi-line mode by default
        """
        self.prompt_session = prompt_session
        self.multiline = multiline
        self._setup_keybindings()

    def _setup_keybindings(self) -> None:
        """Setup custom keybindings for the editor."""
        try:
            from prompt_toolkit.key_binding import KeyBindings

            self.kb: KeyBindings | None = KeyBindings()

            if self.kb:
                # Ctrl+Enter to submit (in multi-line mode)
                @self.kb.add("c-enter")  # type: ignore[misc]
                def _submit(event: Any) -> None:
                    """Submit input on Ctrl+Enter."""
                    event.current_buffer.validate_and_handle()

                # Ctrl+C to cancel
                @self.kb.add("c-c")  # type: ignore[misc]
                def _cancel(event: Any) -> None:
                    """Cancel input on Ctrl+C."""
                    event.current_buffer.text = ""
                    event.app.exit(exception=KeyboardInterrupt)

                # Ctrl+K to delete to end of line
                @self.kb.add("c-k")  # type: ignore[misc]
                def _kill_to_end(event: Any) -> None:
                    """Delete from cursor to end of line."""
                    buffer = event.current_buffer
                    buffer.delete(count=len(buffer.document.current_line_after_cursor))

                # Ctrl+U to delete to beginning of line
                @self.kb.add("c-u")  # type: ignore[misc]
                def _kill_to_beginning(event: Any) -> None:
                    """Delete from cursor to beginning of line."""
                    buffer = event.current_buffer
                    buffer.delete_before_cursor(
                        count=len(buffer.document.current_line_before_cursor)
                    )

                # Ctrl+W to delete previous word
                @self.kb.add("c-w")  # type: ignore[misc]
                def _delete_word(event: Any) -> None:
                    """Delete previous word."""
                    buffer = event.current_buffer
                    buffer.delete_before_cursor(count=buffer.document.find_start_of_previous_word())

        except ImportError:
            self.kb = None

    def get_input(
        self,
        prompt: str = "> ",
        multiline: bool | None = None,
        default: str = "",
    ) -> str | None:
        """Get user input with enhanced editing.

        Args:
            prompt: Prompt string to display
            multiline: Enable multi-line mode (uses instance default if None)
            default: Default text

        Returns:
            User input string, or None on EOF/cancel
        """
        use_multiline = multiline if multiline is not None else self.multiline

        try:
            if self.prompt_session and self.kb:
                # Use prompt_toolkit with keybindings
                text = self.prompt_session.prompt(
                    prompt,
                    multiline=use_multiline,
                    default=default,
                    key_bindings=self.kb,
                )
                return text.strip()  # type: ignore[no-any-return]

            # Fallback to basic input
            if use_multiline:
                return self._get_multiline_basic(prompt, default)

            user_input = input(prompt)
            return user_input.strip()

        except (EOFError, KeyboardInterrupt):
            return None

    def _get_multiline_basic(self, prompt: str, default: str) -> str:
        """Get multi-line input without prompt_toolkit.

        Args:
            prompt: Prompt string
            default: Default text

        Returns:
            Multi-line input string
        """
        print(f"{prompt}(Press Ctrl+D or type 'END' on empty line to submit)")
        lines = []

        if default:
            lines.append(default)

        while True:
            try:
                line = input()
                if line == "END" and not lines:
                    break
                if line == "END":
                    break
                lines.append(line)
            except EOFError:
                break

        return "\n".join(lines).strip()

    def set_multiline(self, enabled: bool) -> None:
        """Enable or disable multi-line mode.

        Args:
            enabled: True to enable multi-line mode
        """
        self.multiline = enabled


class InputValidator:
    """Validates and sanitizes user input.

    Provides input validation, sanitization, and safety checks.
    """

    MAX_INPUT_LENGTH = 50000  # Maximum input length in characters

    @staticmethod
    def validate_input(text: str) -> tuple[bool, str | None]:
        """Validate user input.

        Args:
            text: Input text to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check length
        if len(text) > InputValidator.MAX_INPUT_LENGTH:
            return (
                False,
                f"Input too long ({len(text)} chars, max {InputValidator.MAX_INPUT_LENGTH})",
            )

        # Check for null bytes
        if "\x00" in text:
            return False, "Input contains null bytes"

        # Input is valid
        return True, None

    @staticmethod
    def sanitize_input(text: str) -> str:
        """Sanitize user input.

        Args:
            text: Input text

        Returns:
            Sanitized text
        """
        # Remove null bytes
        text = text.replace("\x00", "")

        # Normalize whitespace (but preserve intentional newlines)
        lines = text.splitlines()
        sanitized_lines = [line.rstrip() for line in lines]

        return "\n".join(sanitized_lines)


__all__ = ["InputValidator", "MultiLineEditor"]
