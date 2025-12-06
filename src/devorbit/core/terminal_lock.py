"""
Windows Console Lock - Clean Version
Place this at: src/devorbit/core/terminal_lock.py
"""

import atexit
import ctypes
import sys


# --- Constants ---
GWL_STYLE = -16
STD_OUTPUT_HANDLE = -11

# Window Style Constants
WS_SIZEBOX = 0x00040000
WS_MAXIMIZEBOX = 0x00010000

# SetWindowPos Flags
SWP_FRAMECHANGED = 0x0020
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOZORDER = 0x0004


# --- State Management ---
# Explicitly type the dictionary so mypy knows values can be int OR None
_CONSOLE_STATE: dict[str, int | None] = {"original_style": None, "hwnd": None}


def lock_windows_console(cols: int = 120, rows: int = 30) -> bool:
    """
    Lock Windows CMD/PowerShell console to prevent resizing.
    Returns True if locked, False otherwise.
    """
    if sys.platform != "win32":
        return False

    # Fix: Add ignore[unreachable] for non-Windows type checking environments
    try:  # type: ignore[unreachable]
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32

        # Get console window handle
        hwnd = kernel32.GetConsoleWindow()
        _CONSOLE_STATE["hwnd"] = hwnd

        # If hwnd is 0, it's an embedded terminal (can't lock)
        if hwnd == 0:
            return False

        # Save original style
        original_style = user32.GetWindowLongW(hwnd, GWL_STYLE)
        _CONSOLE_STATE["original_style"] = original_style

        # Set console size
        h_console = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)

        coord = ctypes.wintypes._COORD(cols, rows)
        kernel32.SetConsoleScreenBufferSize(h_console, coord)

        rect = ctypes.wintypes.SMALL_RECT(0, 0, cols - 1, rows - 1)
        kernel32.SetConsoleWindowInfo(h_console, True, ctypes.byref(rect))

        # Remove resize capability
        # Ensure original_style is treated as int for bitwise operations
        style_int = original_style if isinstance(original_style, int) else 0
        new_style = style_int & ~WS_SIZEBOX & ~WS_MAXIMIZEBOX
        user32.SetWindowLongW(hwnd, GWL_STYLE, new_style)

        # Force refresh
        flags = SWP_FRAMECHANGED | SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER
        user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, flags)

        # Register unlock on exit
        atexit.register(unlock_windows_console)

        return True

    except Exception:
        return False


def unlock_windows_console() -> bool:
    """Restore original console window style on exit."""
    hwnd = _CONSOLE_STATE["hwnd"]
    original_style = _CONSOLE_STATE["original_style"]

    # Check if we have state to restore
    if original_style is None or hwnd is None:
        return False

    if sys.platform != "win32":
        return False

    # Fix: Add ignore[unreachable] for non-Windows type checking environments
    try:  # type: ignore[unreachable]
        user32 = ctypes.windll.user32

        # Restore original style
        user32.SetWindowLongW(hwnd, GWL_STYLE, original_style)

        # Force refresh
        flags = SWP_FRAMECHANGED | SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER
        user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, flags)

        return True

    except Exception:
        return False
