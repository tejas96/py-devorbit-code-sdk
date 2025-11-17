"""Progress indicators for Devorbit CLI.

Implements progress indicators and spinners for long-running operations
according to the Claude Code CLI specification.
"""

import itertools
import time
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from rich.console import Console


class ProgressIndicator:
    """Progress indicator for long-running operations.

    Supports both determinate (with percentage) and indeterminate (spinner) modes.
    """

    # Spinner animation frames (from Claude Code spec)
    SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, console: "Console | None" = None, no_color: bool = False) -> None:
        """Initialize progress indicator.

        Args:
            console: Rich console instance (optional)
            no_color: Disable colored output
        """
        self.console = console
        self.no_color = no_color
        self._spinner = itertools.cycle(self.SPINNER_FRAMES)
        self._current_frame = 0

    def show_spinner(self, message: str = "Processing...") -> None:
        """Show an animated spinner for indeterminate progress.

        Args:
            message: Message to display next to spinner

        Example:
            ⠋ Analyzing codebase...
        """
        frame = next(self._spinner)

        if self.console and not self.no_color:
            from .colors import Colors

            color = Colors.rich_info()
            self.console.print(f"[{color}]{frame}[/{color}] {message}", end="\r")
        else:
            print(f"{frame} {message}", end="\r", flush=True)

    def show_progress_bar(
        self, current: int, total: int, message: str = "", width: int = 20
    ) -> None:
        """Show a progress bar for determinate progress.

        Args:
            current: Current progress value
            total: Total value
            message: Optional message to display
            width: Width of the progress bar in characters

        Example:
            [●●●●○○○○○○] Reading files... 40% (2/5)
        """
        percentage = int((current / total) * 100) if total > 0 else 0
        filled = int((current / total) * width) if total > 0 else 0
        bar = "●" * filled + "○" * (width - filled)

        progress_text = f"[{bar}] {message} {percentage}% ({current}/{total})"

        if self.console and not self.no_color:
            from .colors import Colors

            color = Colors.rich_success()
            self.console.print(f"[{color}]{progress_text}[/{color}]", end="\r")
        else:
            print(progress_text, end="\r", flush=True)

    def show_file_processing(
        self,
        files: list[str],
        current_index: int,
        status: dict[str, str] | None = None,
    ) -> None:
        """Show file processing progress.

        Args:
            files: List of file paths
            current_index: Index of currently processing file
            status: Dict mapping file paths to status (✓, ⏳, ○, ✗)

        Example:
            📁 Processing files...
              ✓ file1.py (0.2s)
              ✓ file2.js (0.3s)
              ⏳ file3.ts (processing...)
              ○ file4.css (pending)
        """
        if status is None:
            status = {}

        if self.console:
            self.console.print("📁 Processing files...")
            for i, file in enumerate(files):
                file_status = status.get(file, "○")
                suffix = ""
                if i < current_index:
                    suffix = " ✓"
                elif i == current_index:
                    suffix = " ⏳ (processing...)"
                else:
                    suffix = " ○ (pending)"

                self.console.print(f"  {file_status} {file}{suffix}")
        else:
            print("Processing files...")
            for i, file in enumerate(files):
                file_status = status.get(file, "○")
                print(f"  {file_status} {file}")

    def clear_line(self) -> None:
        """Clear the current line."""
        if self.console:
            self.console.print(" " * 100, end="\r")
        else:
            print(" " * 100, end="\r", flush=True)


class CompactionProgress:
    """Progress indicator for context compaction operations.

    Example:
        ⏳ Compacting conversation...
          • Analyzing 45 messages
          • Identifying key information
          • Preserving recent context
          • Summarizing tool outputs

        ✓ Compacted: 160,000 → 45,000 tokens (71% reduction)
    """

    def __init__(self, console: "Console | None" = None) -> None:
        """Initialize compaction progress indicator.

        Args:
            console: Rich console instance (optional)
        """
        self.console = console
        self.start_time = time.time()

    def show_step(self, step: str) -> None:
        """Show current compaction step.

        Args:
            step: Description of current step
        """
        if self.console:
            self.console.print(f"  • {step}")
        else:
            print(f"  • {step}")

    def show_result(
        self, original_tokens: int, compacted_tokens: int, preserved: list[str]
    ) -> None:
        """Show compaction result.

        Args:
            original_tokens: Original token count
            compacted_tokens: Compacted token count
            preserved: List of preserved items
        """
        reduction = int(((original_tokens - compacted_tokens) / original_tokens) * 100)
        duration = time.time() - self.start_time

        if self.console:
            from .colors import Colors

            color = Colors.rich_success()
            self.console.print(
                f"\n[{color}]✓[/{color}] Compacted: {original_tokens:,} → "
                f"{compacted_tokens:,} tokens ({reduction}% reduction)"
            )
            self.console.print(f"\nDuration: {duration:.1f}s")

            if preserved:
                self.console.print("\nPreserved:")
                for item in preserved:
                    self.console.print(f"  • {item}")
        else:
            print(
                f"\n✓ Compacted: {original_tokens:,} → "
                f"{compacted_tokens:,} tokens ({reduction}% reduction)"
            )
            print(f"\nDuration: {duration:.1f}s")

            if preserved:
                print("\nPreserved:")
                for item in preserved:
                    print(f"  • {item}")


__all__ = ["CompactionProgress", "ProgressIndicator"]
