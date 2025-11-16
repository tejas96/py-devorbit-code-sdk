"""Process management for dev servers and background tasks.

This module provides process management similar to Claude Code CLI,
allowing running and monitoring of dev servers, build watchers, etc.
"""

import os
import subprocess
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


try:
    from rich.console import Console
    from rich.live import Live
    from rich.table import Table

    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    Console = None  # type: ignore[assignment, misc]
    Live = None  # type: ignore[assignment, misc]
    Table = None  # type: ignore[assignment, misc]


@dataclass
class ProcessInfo:
    """Information about a managed process."""

    name: str
    command: str
    pid: int | None = None
    status: str = "stopped"  # stopped, running, crashed, restarting
    started_at: datetime | None = None
    stopped_at: datetime | None = None
    exit_code: int | None = None
    auto_restart: bool = False
    restart_count: int = 0
    max_restarts: int = 3
    log_file: Path | None = None
    output_lines: list[str] = field(default_factory=list)
    error_lines: list[str] = field(default_factory=list)
    cwd: Path | None = None
    env: dict[str, str] = field(default_factory=dict)


class ProcessManager:
    """Manage background processes for dev servers and build tools."""

    def __init__(self, log_dir: Path | None = None, console: Any | None = None):
        """Initialize process manager.

        Args:
            log_dir: Directory for process logs (default: .claude/logs/)
            console: Rich console for output
        """
        self.log_dir = log_dir or Path(".claude/logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.console = console
        if HAS_RICH and console is None:
            self.console = Console()

        self.processes: dict[str, ProcessInfo] = {}
        self.process_handles: dict[str, subprocess.Popen[str]] = {}
        self.monitor_threads: dict[str, threading.Thread] = {}
        self.shutdown_event = threading.Event()

    def start_process(
        self,
        name: str,
        command: str,
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
        auto_restart: bool = False,
        max_restarts: int = 3,
    ) -> ProcessInfo:
        """Start a background process.

        Args:
            name: Process name (identifier)
            command: Command to run
            cwd: Working directory
            env: Environment variables
            auto_restart: Restart on crash
            max_restarts: Max restart attempts

        Returns:
            ProcessInfo for the started process

        Raises:
            ValueError: If process with name already exists
        """
        if name in self.processes:
            raise ValueError(f"Process '{name}' already exists")

        # Create log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"{name}_{timestamp}.log"

        # Create process info
        process_info = ProcessInfo(
            name=name,
            command=command,
            status="starting",
            started_at=datetime.now(),
            auto_restart=auto_restart,
            max_restarts=max_restarts,
            log_file=log_file,
            cwd=cwd,
            env=env or {},
        )

        self.processes[name] = process_info

        # Start process
        try:
            # Merge environment variables
            process_env: dict[str, str] | None = None
            if process_info.env:
                process_env = {**os.environ, **process_info.env}

            # Start subprocess
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(cwd) if cwd else None,
                env=process_env,
                text=True,
                bufsize=1,  # Line buffered
            )

            self.process_handles[name] = process
            process_info.pid = process.pid
            process_info.status = "running"

            # Start monitoring thread
            monitor_thread = threading.Thread(
                target=self._monitor_process,
                args=(name,),
                daemon=True,
            )
            monitor_thread.start()
            self.monitor_threads[name] = monitor_thread

            self._log_message(name, f"Started process: {command} (PID: {process.pid})")

        except Exception as e:
            process_info.status = "crashed"
            process_info.exit_code = -1
            process_info.stopped_at = datetime.now()
            self._log_message(name, f"Failed to start: {e}")
            raise

        return process_info

    def stop_process(self, name: str, timeout: int = 5) -> bool:
        """Stop a running process.

        Args:
            name: Process name
            timeout: Seconds to wait before force kill

        Returns:
            True if stopped successfully

        Raises:
            KeyError: If process doesn't exist
        """
        if name not in self.processes:
            raise KeyError(f"Process '{name}' not found")

        process_info = self.processes[name]
        process = self.process_handles.get(name)

        if not process or process_info.status != "running":
            return False

        try:
            # Send SIGTERM
            process.terminate()

            # Wait for graceful shutdown
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                # Force kill
                process.kill()
                process.wait()

            process_info.status = "stopped"
            process_info.stopped_at = datetime.now()
            process_info.exit_code = process.returncode

            self._log_message(name, f"Stopped process (exit code: {process.returncode})")

            # Remove from handles
            del self.process_handles[name]

            return True

        except Exception as e:
            self._log_message(name, f"Error stopping process: {e}")
            return False

    def restart_process(self, name: str) -> ProcessInfo:
        """Restart a process.

        Args:
            name: Process name

        Returns:
            Updated ProcessInfo

        Raises:
            KeyError: If process doesn't exist
        """
        if name not in self.processes:
            raise KeyError(f"Process '{name}' not found")

        process_info = self.processes[name]

        # Stop if running
        if process_info.status == "running":
            self.stop_process(name)

        # Increment restart count
        process_info.restart_count += 1

        # Start again
        return self.start_process(
            name=name,
            command=process_info.command,
            cwd=process_info.cwd,
            env=process_info.env,
            auto_restart=process_info.auto_restart,
            max_restarts=process_info.max_restarts,
        )

    def get_process_info(self, name: str) -> ProcessInfo:
        """Get process information.

        Args:
            name: Process name

        Returns:
            ProcessInfo

        Raises:
            KeyError: If process doesn't exist
        """
        if name not in self.processes:
            raise KeyError(f"Process '{name}' not found")

        return self.processes[name]

    def list_processes(self) -> list[ProcessInfo]:
        """List all managed processes.

        Returns:
            List of ProcessInfo objects
        """
        return list(self.processes.values())

    def get_process_output(
        self,
        name: str,
        lines: int | None = None,
    ) -> tuple[list[str], list[str]]:
        """Get process output.

        Args:
            name: Process name
            lines: Number of lines to return (None for all)

        Returns:
            Tuple of (stdout_lines, stderr_lines)

        Raises:
            KeyError: If process doesn't exist
        """
        if name not in self.processes:
            raise KeyError(f"Process '{name}' not found")

        process_info = self.processes[name]

        if lines:
            return (
                process_info.output_lines[-lines:],
                process_info.error_lines[-lines:],
            )

        return (process_info.output_lines, process_info.error_lines)

    def stop_all(self, timeout: int = 5) -> None:
        """Stop all running processes.

        Args:
            timeout: Seconds to wait for each process
        """
        # Set shutdown event
        self.shutdown_event.set()

        # Stop all processes
        for name in list(self.processes.keys()):
            if self.processes[name].status == "running":
                try:
                    self.stop_process(name, timeout=timeout)
                except Exception as e:
                    self._log_message(name, f"Error during shutdown: {e}")

    def render_status(self) -> None:
        """Render status table of all processes."""
        if HAS_RICH and self.console:
            self._render_status_rich()
        else:
            self._render_status_plain()

    def _render_status_rich(self) -> None:
        """Render status with Rich table."""
        if not self.console:
            return

        table = Table(title="Managed Processes")
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("PID", style="dim")
        table.add_column("Restarts", style="yellow")
        table.add_column("Uptime", style="green")

        for process_info in self.processes.values():
            # Status color
            status_style = {
                "running": "green",
                "stopped": "dim",
                "crashed": "red",
                "restarting": "yellow",
            }.get(process_info.status, "white")

            # Calculate uptime
            uptime = ""
            if process_info.started_at and process_info.status == "running":
                elapsed = datetime.now() - process_info.started_at
                hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                uptime = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            table.add_row(
                process_info.name,
                f"[{status_style}]{process_info.status}[/{status_style}]",
                str(process_info.pid) if process_info.pid else "-",
                str(process_info.restart_count),
                uptime,
            )

        self.console.print(table)

    def _render_status_plain(self) -> None:
        """Render status with plain text."""
        print("\nManaged Processes:")
        print("─" * 80)
        print(f"{'Name':<20} {'Status':<12} {'PID':<10} {'Restarts':<10} {'Uptime'}")
        print("─" * 80)

        for process_info in self.processes.values():
            # Calculate uptime
            uptime = ""
            if process_info.started_at and process_info.status == "running":
                elapsed = datetime.now() - process_info.started_at
                hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                uptime = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            print(
                f"{process_info.name:<20} "
                f"{process_info.status:<12} "
                f"{str(process_info.pid) if process_info.pid else '-':<10} "
                f"{process_info.restart_count:<10} "
                f"{uptime}"
            )

        print("─" * 80)

    def _monitor_process(self, name: str) -> None:
        """Monitor process output and status.

        Args:
            name: Process name
        """
        process_info = self.processes[name]
        process = self.process_handles[name]

        try:
            # Monitor stdout
            if process.stdout:
                for raw_line in iter(process.stdout.readline, ""):
                    if self.shutdown_event.is_set():
                        break

                    line = raw_line.rstrip()
                    process_info.output_lines.append(line)
                    self._log_message(name, line)

                    # Keep only last 1000 lines
                    if len(process_info.output_lines) > 1000:
                        process_info.output_lines = process_info.output_lines[-1000:]

            # Wait for process to finish
            exit_code = process.wait()
            process_info.exit_code = exit_code
            process_info.stopped_at = datetime.now()

            # Handle crashes and auto-restart
            if exit_code != 0:
                process_info.status = "crashed"
                self._log_message(name, f"Process crashed (exit code: {exit_code})")

                # Auto-restart if enabled
                if (
                    process_info.auto_restart
                    and process_info.restart_count < process_info.max_restarts
                    and not self.shutdown_event.is_set()
                ):
                    self._log_message(name, "Auto-restarting...")
                    time.sleep(2)  # Wait before restart
                    self.restart_process(name)
            else:
                process_info.status = "stopped"
                self._log_message(name, "Process exited normally")

        except Exception as e:
            process_info.status = "crashed"
            process_info.stopped_at = datetime.now()
            self._log_message(name, f"Monitor error: {e}")

    def _log_message(self, name: str, message: str) -> None:
        """Log message to file and memory.

        Args:
            name: Process name
            message: Log message
        """
        process_info = self.processes.get(name)
        if not process_info:
            return

        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}"

        # Write to log file
        if process_info.log_file:
            try:
                with process_info.log_file.open("a", encoding="utf-8") as f:
                    f.write(log_line + "\n")
            except Exception:
                pass  # Ignore log write errors


__all__ = ["ProcessInfo", "ProcessManager"]
