"""
Windows Console Lock - Clean Version
Place this at: src/devorbit/core/terminal_lock.py
"""

import atexit
import ctypes
import sys
from ctypes import wintypes  # Explicit import for resizing logic


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
_CONSOLE_STATE: dict[str, int | None] = {"original_style": None, "hwnd": None}


def lock_windows_console(cols: int = 120, rows: int = 30) -> bool:
    """
    Lock Windows CMD/PowerShell console to prevent resizing.
    Returns True if locked, False otherwise.
    """
    if sys.platform != "win32":
        return False

    # Fix: Add ignore[unreachable] so mypy passes on Linux/Mac
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

        # Get Standard Handle
        h_console = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)

        # --- RESIZING LOGIC ---
        # 1. Define target size
        target_rect = wintypes.SMALL_RECT(0, 0, cols - 1, rows - 1)

        # 2. Shrink window to minimal size first (1x1)
        # This fixes the bug where the window wouldn't lock if it started large.
        tiny_rect = wintypes.SMALL_RECT(0, 0, 0, 0)
        kernel32.SetConsoleWindowInfo(h_console, True, ctypes.byref(tiny_rect))

        # 3. Set the Buffer Size
        coord = wintypes._COORD(cols, rows)
        success_buf = kernel32.SetConsoleScreenBufferSize(h_console, coord)

        # 4. Expand Window to match Buffer
        success_win = kernel32.SetConsoleWindowInfo(h_console, True, ctypes.byref(target_rect))

        if not success_buf or not success_win:
            return False

        # --- LOCKING STYLE ---
        # Remove resize capability
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

    if original_style is None or hwnd is None:
        return False

    if sys.platform != "win32":
        return False

    # Fix: Add ignore[unreachable] so mypy passes on Linux/Mac
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
