"""Enhanced Bash tools with persistent sessions and background task management.

This module provides enhanced bash capabilities matching Claude Code's behavior:
- Persistent bash sessions with state retention
- Background process execution
- Output streaming and capture
- Environment variable tracking
- Working directory persistence
"""

import os
import queue
import re
import subprocess
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from devorbit.core.tool_helpers import beta_tool


# Global state for bash sessions
_BASH_SESSIONS: dict[str, "BashSession"] = {}


class BashSession:
    """Persistent bash session with state tracking."""

    def __init__(self, session_id: str, cwd: str | None = None) -> None:
        """Initialize bash session.

        Args:
            session_id: Unique session identifier
            cwd: Working directory (default: current directory)
        """
        self.session_id = session_id
        self.cwd = Path(cwd) if cwd else Path.cwd()
        self.env = os.environ.copy()
        self.process: subprocess.Popen[bytes] | None = None
        self.output_queue: queue.Queue[str] = queue.Queue()
        self.is_running = False
        self.exit_code: int | None = None
        self._output_thread: threading.Thread | None = None

    def start(self) -> None:
        """Start the bash session."""
        if self.is_running:
            return

        # Start bash process
        self.process = subprocess.Popen(
            ["/bin/bash"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=str(self.cwd),
            env=self.env,
            bufsize=0,
        )

        self.is_running = True

        # Start output reader thread
        self._output_thread = threading.Thread(
            target=self._read_output,
            daemon=True,
        )
        self._output_thread.start()

    def _read_output(self) -> None:
        """Read output from process in background thread."""
        if not self.process or not self.process.stdout:
            return

        try:
            while self.is_running:
                line = self.process.stdout.readline()
                if not line:
                    break
                self.output_queue.put(line.decode("utf-8", errors="replace"))
        except Exception:
            pass

    def execute(  # noqa: PLR0912 - Complex state management for persistent bash sessions
        self,
        command: str,
        timeout: float | None = None,
        run_in_background: bool = False,
    ) -> dict[str, Any]:
        """Execute command in session.

        Args:
            command: Command to execute
            timeout: Timeout in seconds (default: 120)
            run_in_background: Run command in background

        Returns:
            Command execution result
        """
        if not self.is_running:
            self.start()

        if not self.process or not self.process.stdin:
            return {"error": "Session not started"}

        # Use default timeout if not specified
        if timeout is None:
            timeout = 120.0

        try:
            # Add marker to detect command completion
            marker = f"__CMD_DONE_{uuid.uuid4().hex}__"
            full_command = f"{command}\necho {marker}\n"

            # Send command
            self.process.stdin.write(full_command.encode("utf-8"))
            self.process.stdin.flush()

            if run_in_background:
                return {
                    "session_id": self.session_id,
                    "status": "running",
                    "message": "Command started in background. Use BashOutput to read output.",
                }

            # Collect output until marker
            output_lines: list[str] = []
            start_time = time.time()

            while True:
                # Check timeout
                if time.time() - start_time > timeout:
                    return {
                        "error": "Command timed out",
                        "output": "".join(output_lines),
                        "session_id": self.session_id,
                    }

                try:
                    line = self.output_queue.get(timeout=0.1)
                    if marker in line:
                        break
                    output_lines.append(line)
                except queue.Empty:
                    # Check if process is still alive
                    if self.process.poll() is not None:
                        self.is_running = False
                        self.exit_code = self.process.poll()
                        break

            output = "".join(output_lines)

            # Update working directory (try to get from pwd)
            pwd_marker = f"__PWD_{uuid.uuid4().hex}__"
            pwd_command = f"pwd\necho {pwd_marker}\n"
            self.process.stdin.write(pwd_command.encode("utf-8"))
            self.process.stdin.flush()

            pwd_lines = []
            start_time = time.time()
            while time.time() - start_time < 1.0:
                try:
                    line = self.output_queue.get(timeout=0.1)
                    if pwd_marker in line:
                        break
                    pwd_lines.append(line)
                except queue.Empty:
                    break

            if pwd_lines:
                new_cwd = pwd_lines[0].strip()
                if new_cwd and Path(new_cwd).exists():
                    self.cwd = Path(new_cwd)

            return {
                "output": output,
                "session_id": self.session_id,
                "cwd": str(self.cwd),
                "exit_code": 0,
            }

        except Exception as e:
            return {
                "error": f"Command execution failed: {e!s}",
                "session_id": self.session_id,
            }

    def get_output(self, filter_regex: str | None = None) -> str:
        """Get accumulated output from session.

        Args:
            filter_regex: Optional regex pattern to filter lines

        Returns:
            Accumulated output
        """
        lines = []
        while not self.output_queue.empty():
            try:
                line = self.output_queue.get_nowait()
                lines.append(line)
            except queue.Empty:
                break

        output = "".join(lines)

        if filter_regex:
            pattern = re.compile(filter_regex)
            filtered_lines = [line for line in lines if pattern.search(line)]
            output = "".join(filtered_lines)

        return output

    def kill(self) -> None:
        """Terminate the bash session."""
        self.is_running = False
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.exit_code = self.process.poll()


# ============================================================================
# Enhanced Bash Tool
# ============================================================================


@beta_tool
def bash(
    command: str,
    session_id: str | None = None,
    cwd: str | None = None,
    timeout: float | None = None,
    run_in_background: bool = False,
) -> dict[str, Any]:
    """Execute shell commands with persistent session support.

    Enhanced bash tool with persistent sessions, environment tracking,
    and background execution support. Sessions maintain state across
    multiple command executions.

    Args:
        command: Shell command to execute
        session_id: Session ID for persistent sessions (creates new if not provided)
        cwd: Working directory (only used for new sessions)
        timeout: Command timeout in seconds (default: 120)
        run_in_background: Run command in background

    Returns:
        Dictionary containing command output and session information
    """
    try:
        # Get or create session
        if session_id and session_id in _BASH_SESSIONS:
            session = _BASH_SESSIONS[session_id]
        else:
            # Create new session
            new_session_id = session_id or str(uuid.uuid4())
            session = BashSession(new_session_id, cwd)
            _BASH_SESSIONS[new_session_id] = session

        # Execute command
        return session.execute(command, timeout, run_in_background)

    except Exception as e:
        return {
            "error": f"Bash execution failed: {e!s}",
            "command": command,
        }


# ============================================================================
# BashOutput Tool
# ============================================================================


@beta_tool
def bash_output(
    bash_id: str,
    filter: str | None = None,
) -> dict[str, Any]:
    """Retrieve output from a running or completed background bash shell.

    Read accumulated output from a bash session. Always returns only new
    output since the last check. Supports optional regex filtering.

    Args:
        bash_id: Session ID of the bash shell
        filter: Optional regex pattern to filter output lines

    Returns:
        Dictionary containing output and session status
    """
    try:
        if bash_id not in _BASH_SESSIONS:
            return {
                "error": f"Bash session not found: {bash_id}",
                "bash_id": bash_id,
            }

        session = _BASH_SESSIONS[bash_id]
        output = session.get_output(filter)

        return {
            "bash_id": bash_id,
            "output": output,
            "is_running": session.is_running,
            "exit_code": session.exit_code,
            "cwd": str(session.cwd),
        }

    except Exception as e:
        return {
            "error": f"Failed to read bash output: {e!s}",
            "bash_id": bash_id,
        }


# ============================================================================
# KillShell Tool
# ============================================================================


@beta_tool
def kill_shell(shell_id: str) -> dict[str, Any]:
    """Kill a running background bash shell.

    Terminate a background bash session by its ID. The session will be
    removed from active sessions.

    Args:
        shell_id: Session ID of the bash shell to kill

    Returns:
        Dictionary containing termination status
    """
    try:
        if shell_id not in _BASH_SESSIONS:
            return {
                "error": f"Bash session not found: {shell_id}",
                "shell_id": shell_id,
            }

        session = _BASH_SESSIONS[shell_id]
        session.kill()

        # Remove from active sessions
        del _BASH_SESSIONS[shell_id]

        return {
            "success": True,
            "shell_id": shell_id,
            "message": "Bash session terminated",
            "exit_code": session.exit_code,
        }

    except Exception as e:
        return {
            "error": f"Failed to kill bash session: {e!s}",
            "shell_id": shell_id,
        }


# ============================================================================
# Helper Functions
# ============================================================================


def get_all_bash_tools() -> list[dict[str, Any]]:
    """Get all enhanced bash tool definitions.

    Returns:
        List of bash tool definitions
    """
    return [
        bash.tool_definition,  # type: ignore[attr-defined]
        bash_output.tool_definition,  # type: ignore[attr-defined]
        kill_shell.tool_definition,  # type: ignore[attr-defined]
    ]


def list_active_sessions() -> list[dict[str, Any]]:
    """List all active bash sessions.

    Returns:
        List of active session information
    """
    return [
        {
            "session_id": sid,
            "is_running": session.is_running,
            "cwd": str(session.cwd),
            "exit_code": session.exit_code,
        }
        for sid, session in _BASH_SESSIONS.items()
    ]


def cleanup_sessions() -> None:
    """Clean up all bash sessions.

    Terminates all active bash sessions. Useful for cleanup.
    """
    for session in _BASH_SESSIONS.values():
        if session.is_running:
            session.kill()

    _BASH_SESSIONS.clear()


# Export tool instances
__all__ = [
    "BashSession",
    "bash",
    "bash_output",
    "cleanup_sessions",
    "get_all_bash_tools",
    "kill_shell",
    "list_active_sessions",
]
