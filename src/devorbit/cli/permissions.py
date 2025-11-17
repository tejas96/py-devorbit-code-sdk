"""Tool permission and approval system.

This module provides interactive prompts for approving tool executions
before they run, with keyboard navigation and dangerous command detection.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from prompt_toolkit import prompt
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import radiolist_dialog

if TYPE_CHECKING:
    from .session import Session


class DangerousCommandDetector:
    """Detects potentially dangerous commands and file operations."""

    # Dangerous shell commands
    DANGEROUS_PATTERNS = [
        r"\brm\s+-rf\s+/",  # rm -rf /
        r"\brm\s+-rf\s+\*",  # rm -rf *
        r"\bdd\s+if=",  # dd commands
        r"\bmkfs\.",  # format filesystem
        r"\bformat\s+",  # format command
        r">\s*/dev/sd[a-z]",  # write to device
        r"\bfdisk\s+",  # disk partitioning
        r"\bcurl\s+.*\|\s*(bash|sh)",  # curl | bash or curl | sh
        r"\bwget\s+.*\|\s*(bash|sh)",  # wget | bash or wget | sh
        r"\bchmod\s+777",  # overly permissive permissions
        r"\bsudo\s+rm",  # sudo rm
        r":\(\)\{\s*:\|\:&\s*\};:",  # fork bomb
    ]

    # Dangerous file paths
    DANGEROUS_PATHS = [
        "/etc/passwd",
        "/etc/shadow",
        "/etc/sudoers",
        "/etc/hosts",
        "/boot",
        "/sys",
        "/proc",
        "~/.ssh/id_rsa",
        "~/.ssh/authorized_keys",
    ]

    # File operations that should trigger warnings
    WRITE_OPERATIONS = {"write_file", "edit_file"}
    DELETE_OPERATIONS = {"bash"}  # bash can contain rm commands

    @classmethod
    def is_dangerous_command(cls, command: str) -> tuple[bool, str | None]:
        """Check if a bash command is dangerous.

        Args:
            command: The command to check

        Returns:
            Tuple of (is_dangerous, reason)
        """
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return True, f"Potentially destructive pattern detected: {pattern}"

        return False, None

    @classmethod
    def is_dangerous_path(cls, path: str) -> tuple[bool, str | None]:
        """Check if a file path is dangerous to modify.

        Args:
            path: The file path to check

        Returns:
            Tuple of (is_dangerous, reason)
        """
        for dangerous_path in cls.DANGEROUS_PATHS:
            if dangerous_path in path:
                return True, f"System file or sensitive path: {dangerous_path}"

        return False, None

    @classmethod
    def check_tool_call(cls, tool_name: str, tool_input: dict[str, Any]) -> tuple[bool, str | None]:
        """Check if a tool call is dangerous.

        Args:
            tool_name: Name of the tool
            tool_input: Tool input parameters

        Returns:
            Tuple of (is_dangerous, reason)
        """
        # Check bash commands
        if tool_name == "bash":
            command = tool_input.get("command", "")
            return cls.is_dangerous_command(command)

        # Check file operations on dangerous paths
        if tool_name in cls.WRITE_OPERATIONS:
            file_path = tool_input.get("file_path", "")
            return cls.is_dangerous_path(file_path)

        return False, None


class ToolApprovalPrompt:
    """Interactive prompt for approving tool executions."""

    def __init__(self, session: Session):
        """Initialize the approval prompt.

        Args:
            session: The current CLI session
        """
        self.session = session

    def format_tool_details(self, tool_name: str, tool_input: dict[str, Any]) -> str:
        """Format tool details for display.

        Args:
            tool_name: Name of the tool
            tool_input: Tool input parameters

        Returns:
            Formatted string representation
        """
        lines = [f"Tool: {tool_name}"]

        # Special formatting for common tools
        if tool_name == "bash":
            command = tool_input.get("command", "")
            timeout = tool_input.get("timeout", 60)
            lines.append(f"Command: {command}")
            lines.append(f"Timeout: {timeout}s")

        elif tool_name == "read_file":
            file_path = tool_input.get("file_path", "")
            lines.append(f"File: {file_path}")

        elif tool_name in ("write_file", "edit_file"):
            file_path = tool_input.get("file_path", "")
            lines.append(f"File: {file_path}")
            if tool_name == "edit_file":
                old_str = tool_input.get("old_string", "")
                new_str = tool_input.get("new_string", "")
                lines.append(f"Old: {old_str[:50]}..." if len(old_str) > 50 else f"Old: {old_str}")
                lines.append(f"New: {new_str[:50]}..." if len(new_str) > 50 else f"New: {new_str}")

        elif tool_name == "grep":
            pattern = tool_input.get("pattern", "")
            path = tool_input.get("path", ".")
            lines.append(f"Pattern: {pattern}")
            lines.append(f"Path: {path}")

        elif tool_name == "glob":
            pattern = tool_input.get("pattern", "")
            path = tool_input.get("path", ".")
            lines.append(f"Pattern: {pattern}")
            lines.append(f"Path: {path}")

        else:
            # Generic formatting for other tools
            for key, value in tool_input.items():
                value_str = str(value)
                if len(value_str) > 100:
                    value_str = value_str[:100] + "..."
                lines.append(f"{key}: {value_str}")

        return "\n".join(lines)

    def show_approval_prompt(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        is_dangerous: bool = False,
        danger_reason: str | None = None,
    ) -> bool:
        """Show an interactive approval prompt.

        Args:
            tool_name: Name of the tool
            tool_input: Tool input parameters
            is_dangerous: Whether the command is flagged as dangerous
            danger_reason: Reason for danger flag

        Returns:
            True if approved, False if denied
        """
        # Check if auto-approve is enabled
        if self.session.auto_approve_tools:
            if not is_dangerous:
                # Auto-approve non-dangerous commands
                return True
            # Always prompt for dangerous commands even in auto-approve mode

        # Format the tool details
        details = self.format_tool_details(tool_name, tool_input)

        # Build the prompt message
        lines = []
        lines.append("")
        lines.append("┌─────────────────────────────────────────────────────────┐")
        lines.append("│              🔧 TOOL EXECUTION REQUEST                  │")
        lines.append("└─────────────────────────────────────────────────────────┘")
        lines.append("")

        if is_dangerous and danger_reason:
            lines.append("⚠️  DANGER WARNING ⚠️")
            lines.append(f"⚠️  {danger_reason}")
            lines.append("")

        lines.append(details)
        lines.append("")
        lines.append("─" * 60)

        # Print the info
        for line in lines:
            self.session.print_info(line)

        # Show the prompt with keyboard navigation
        try:
            result = radiolist_dialog(
                title="Approve Tool Execution?",
                text="Use arrow keys to select, Enter to confirm:",
                values=[
                    ("approve", "✓ Approve - Execute this tool"),
                    ("deny", "✗ Deny - Skip this tool"),
                ],
                default="approve" if not is_dangerous else "deny",
            ).run()

            return result == "approve"

        except KeyboardInterrupt:
            # Ctrl+C denies
            return False
        except Exception:
            # Any error denies by default
            return False

    def approve_tool(self, tool_name: str, tool_input: dict[str, Any]) -> bool:
        """Check if a tool should be approved for execution.

        Args:
            tool_name: Name of the tool
            tool_input: Tool input parameters

        Returns:
            True if approved, False if denied
        """
        # Check for dangerous operations
        is_dangerous, danger_reason = DangerousCommandDetector.check_tool_call(tool_name, tool_input)

        # Show approval prompt
        approved = self.show_approval_prompt(tool_name, tool_input, is_dangerous, danger_reason)

        if approved:
            self.session.print_success(f"✓ Approved: {tool_name}")
        else:
            self.session.print_warning(f"✗ Denied: {tool_name}")

        return approved

    def approve_batch(self, tool_calls: list[tuple[str, dict[str, Any]]]) -> list[bool]:
        """Approve a batch of tool calls.

        Args:
            tool_calls: List of (tool_name, tool_input) tuples

        Returns:
            List of boolean approvals (same length as tool_calls)
        """
        if not tool_calls:
            return []

        # Check if we should show batch prompt
        if len(tool_calls) == 1:
            # Single tool, use regular prompt
            tool_name, tool_input = tool_calls[0]
            approved = self.approve_tool(tool_name, tool_input)
            return [approved]

        # Multiple tools - show batch summary
        self.session.print_info("")
        self.session.print_info("┌─────────────────────────────────────────────────────────┐")
        self.session.print_info(f"│         📦 BATCH TOOL REQUEST ({len(tool_calls)} tools)          │")
        self.session.print_info("└─────────────────────────────────────────────────────────┘")
        self.session.print_info("")

        # Check for dangerous commands in batch
        has_dangerous = False
        for tool_name, tool_input in tool_calls:
            is_dangerous, _ = DangerousCommandDetector.check_tool_call(tool_name, tool_input)
            if is_dangerous:
                has_dangerous = True
                break

        # Show batch options
        try:
            result = radiolist_dialog(
                title="Approve Tool Batch?",
                text=f"Execute {len(tool_calls)} tools. {'⚠️ CONTAINS DANGEROUS COMMANDS' if has_dangerous else ''}",
                values=[
                    ("approve_all", f"✓ Approve All - Execute all {len(tool_calls)} tools"),
                    ("approve_each", "✓ Approve Each - Review each tool individually"),
                    ("deny_all", "✗ Deny All - Skip all tools"),
                ],
                default="approve_each" if has_dangerous else "approve_all",
            ).run()

            if result == "approve_all":
                # Approve everything (except dangerous in non-auto mode)
                results = []
                for tool_name, tool_input in tool_calls:
                    is_dangerous, _ = DangerousCommandDetector.check_tool_call(tool_name, tool_input)
                    if is_dangerous and not self.session.auto_approve_tools:
                        # Still prompt for dangerous
                        approved = self.approve_tool(tool_name, tool_input)
                        results.append(approved)
                    else:
                        results.append(True)
                return results

            elif result == "approve_each":
                # Prompt for each tool
                return [self.approve_tool(tool_name, tool_input) for tool_name, tool_input in tool_calls]

            else:  # deny_all or None
                return [False] * len(tool_calls)

        except KeyboardInterrupt:
            # Ctrl+C denies all
            return [False] * len(tool_calls)
        except Exception:
            # Error denies all
            return [False] * len(tool_calls)
