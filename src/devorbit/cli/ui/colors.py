"""Color scheme and theming system for Devorbit CLI.

Implements the exact color palette from the Claude Code CLI specification
with support for both Rich markup and ANSI escape codes.
"""

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class ColorScheme:
    """Claude Code CLI color scheme.

    All colors are specified as RGB values matching the official specification.
    """

    # Primary Colors
    brand_orange: str = "#FF6B35"  # RGB: 255, 107, 53
    brand_blue: str = "#004E89"  # RGB: 0, 78, 137
    success_green: str = "#10B981"  # RGB: 16, 185, 129
    warning_yellow: str = "#F59E0B"  # RGB: 245, 158, 11
    error_red: str = "#EF4444"  # RGB: 239, 68, 68

    # Background Colors
    primary_bg: str = "#0D1117"  # RGB: 13, 17, 23
    secondary_bg: str = "#161B22"  # RGB: 22, 27, 34
    tertiary_bg: str = "#1C2128"  # RGB: 28, 33, 40
    border: str = "#30363D"  # RGB: 48, 54, 61

    # Text Colors
    primary_text: str = "#E6EDF3"  # RGB: 230, 237, 243
    secondary_text: str = "#8B949E"  # RGB: 139, 148, 158
    muted_text: str = "#6E7681"  # RGB: 110, 118, 129
    link: str = "#58A6FF"  # RGB: 88, 166, 255

    # Syntax Highlighting
    keyword: str = "#FF7B72"  # RGB: 255, 123, 114
    string: str = "#A5D6FF"  # RGB: 165, 214, 255
    number: str = "#79C0FF"  # RGB: 121, 192, 255
    comment: str = "#8B949E"  # RGB: 139, 148, 158
    function: str = "#D2A8FF"  # RGB: 210, 168, 255
    variable: str = "#FFA657"  # RGB: 255, 166, 87

    def to_rich_style(self, color: str) -> str:
        """Convert hex color to Rich markup style.

        Args:
            color: Hex color code (e.g., "#FF6B35")

        Returns:
            Rich style string (e.g., "rgb(255,107,53)")
        """
        # Remove # and convert to RGB
        hex_color = color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"rgb({r},{g},{b})"

    def to_ansi(self, color: str, foreground: bool = True) -> str:
        """Convert hex color to ANSI escape code.

        Args:
            color: Hex color code (e.g., "#FF6B35")
            foreground: If True, use foreground color (38); else background (48)

        Returns:
            ANSI escape code string
        """
        hex_color = color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        prefix = "38" if foreground else "48"
        return f"\033[{prefix};2;{r};{g};{b}m"


class Colors:
    """Terminal color constants and utilities.

    Provides both Rich markup strings and ANSI escape codes for consistent
    coloring across different output methods.
    """

    # Singleton color scheme
    scheme: Final[ColorScheme] = ColorScheme()

    # ANSI Reset
    RESET: Final[str] = "\033[0m"
    BOLD: Final[str] = "\033[1m"
    DIM: Final[str] = "\033[2m"
    ITALIC: Final[str] = "\033[3m"
    UNDERLINE: Final[str] = "\033[4m"

    # Rich markup styles for common uses
    @classmethod
    def rich_brand(cls) -> str:
        """Get Rich markup for brand orange."""
        return cls.scheme.to_rich_style(cls.scheme.brand_orange)

    @classmethod
    def rich_success(cls) -> str:
        """Get Rich markup for success green."""
        return cls.scheme.to_rich_style(cls.scheme.success_green)

    @classmethod
    def rich_error(cls) -> str:
        """Get Rich markup for error red."""
        return cls.scheme.to_rich_style(cls.scheme.error_red)

    @classmethod
    def rich_warning(cls) -> str:
        """Get Rich markup for warning yellow."""
        return cls.scheme.to_rich_style(cls.scheme.warning_yellow)

    @classmethod
    def rich_info(cls) -> str:
        """Get Rich markup for info blue."""
        return cls.scheme.to_rich_style(cls.scheme.brand_blue)

    @classmethod
    def rich_muted(cls) -> str:
        """Get Rich markup for muted text."""
        return cls.scheme.to_rich_style(cls.scheme.muted_text)

    # ANSI colors for non-Rich output
    @classmethod
    def ansi_brand(cls) -> str:
        """Get ANSI code for brand orange."""
        return cls.scheme.to_ansi(cls.scheme.brand_orange)

    @classmethod
    def ansi_success(cls) -> str:
        """Get ANSI code for success green."""
        return cls.scheme.to_ansi(cls.scheme.success_green)

    @classmethod
    def ansi_error(cls) -> str:
        """Get ANSI code for error red."""
        return cls.scheme.to_ansi(cls.scheme.error_red)

    @classmethod
    def ansi_warning(cls) -> str:
        """Get ANSI code for warning yellow."""
        return cls.scheme.to_ansi(cls.scheme.warning_yellow)


__all__ = ["ColorScheme", "Colors"]
