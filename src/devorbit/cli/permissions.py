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
from prompt_toolkit.keys import Keys

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.tree import Tree

    HAS_RICH = True
except ImportError:
    HAS_RICH = False

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
    """Interactive prompt for approving tool executions with Rich UI."""

    def __init__(self, session: Session):
        """Initialize the approval prompt.

        Args:
            session: The current CLI session
        """
        self.session = session
        self.console = session.console if session.console else Console()

    def _create_tool_tree(self, tool_name: str, tool_input: dict[str, Any], is_dangerous: bool = False) -> Tree:
        """Create a Rich Tree display for tool details.

        Args:
            tool_name: Name of the tool
            tool_input: Tool input parameters
            is_dangerous: Whether the tool is flagged as dangerous

        Returns:
            Rich Tree object
        """
        # Color based on danger level
        icon = "⚠️ " if is_dangerous else "🔧 "
        color = "red" if is_dangerous else "cyan"

        tree = Tree(f"[bold {color}]{icon}{tool_name}[/bold {color}]")

        # Special formatting for common tools
        if tool_name == "bash":
            command = tool_input.get("command", "")
            timeout = tool_input.get("timeout", 60)

            cmd_node = tree.add(f"[yellow]Command[/yellow]")
            cmd_node.add(f"[white]{command}[/white]")
            tree.add(f"[dim]Timeout: {timeout}s[/dim]")

        elif tool_name == "read_file":
            file_path = tool_input.get("file_path", "")
            tree.add(f"[green]File:[/green] [white]{file_path}[/white]")

        elif tool_name in ("write_file", "edit_file"):
            file_path = tool_input.get("file_path", "")
            tree.add(f"[green]File:[/green] [white]{file_path}[/white]")

            if tool_name == "edit_file":
                old_str = tool_input.get("old_string", "")
                new_str = tool_input.get("new_string", "")

                old_display = old_str[:50] + "..." if len(old_str) > 50 else old_str
                new_display = new_str[:50] + "..." if len(new_str) > 50 else new_str

                tree.add(f"[red]Replace:[/red] [dim]{old_display}[/dim]")
                tree.add(f"[green]With:[/green] [white]{new_display}[/white]")

        elif tool_name == "grep":
            pattern = tool_input.get("pattern", "")
            path = tool_input.get("path", ".")
            tree.add(f"[yellow]Pattern:[/yellow] [white]{pattern}[/white]")
            tree.add(f"[dim]Path: {path}[/dim]")

        elif tool_name == "glob":
            pattern = tool_input.get("pattern", "")
            path = tool_input.get("path", ".")
            tree.add(f"[yellow]Pattern:[/yellow] [white]{pattern}[/white]")
            tree.add(f"[dim]Path: {path}[/dim]")

        else:
            # Generic formatting for other tools
            for key, value in tool_input.items():
                value_str = str(value)
                if len(value_str) > 100:
                    value_str = value_str[:100] + "..."
                tree.add(f"[cyan]{key}:[/cyan] [white]{value_str}[/white]")

        return tree

    def show_approval_prompt(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        is_dangerous: bool = False,
        danger_reason: str | None = None,
    ) -> bool:
        """Show an interactive approval prompt with Rich UI.

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
                self.console.print(f"[dim]⚡ Auto-approved:[/dim] [cyan]{tool_name}[/cyan]")
                return True
            # Always prompt for dangerous commands even in auto-approve mode

        # Create the tool tree
        tool_tree = self._create_tool_tree(tool_name, tool_input, is_dangerous)

        # Build panel content
        panel_content = Text()

        if is_dangerous and danger_reason:
            panel_content.append("\n")
            panel_content.append("⚠️  DANGER WARNING\n", style="bold red blink")
            panel_content.append(f"{danger_reason}\n", style="red")
            panel_content.append("\n")

        # Determine panel style based on danger level
        border_style = "red" if is_dangerous else "cyan"
        title_icon = "⚠️ " if is_dangerous else "🔧 "
        title = f"{title_icon}Tool Execution Request"

        # Show the panel with tool details
        panel = Panel(
            tool_tree,
            title=f"[bold]{title}[/bold]",
            border_style=border_style,
            padding=(1, 2),
        )
        self.console.print()
        self.console.print(panel)

        if is_dangerous:
            self.console.print("[bold yellow]⚠️  This is a potentially dangerous operation![/bold yellow]")

        # Create interactive prompt with key bindings
        self.console.print()
        self.console.print("[dim]Press [bold]y[/bold] to approve, [bold]n[/bold] to deny, [bold]Ctrl+C[/bold] to cancel[/dim]")

        # Simple yes/no prompt
        kb = KeyBindings()
        approved = [False]  # Use list for closure

        @kb.add("y")
        @kb.add("Y")
        def _(event):
            approved[0] = True
            event.app.exit(result=True)

        @kb.add("n")
        @kb.add("N")
        def _(event):
            approved[0] = False
            event.app.exit(result=False)

        @kb.add("c-c")
        def _(event):
            approved[0] = False
            event.app.exit(result=False)

        try:
            # Show prompt with key bindings
            result = prompt(
                HTML("<style fg='cyan' bg=''>Your choice: </style>"),
                key_bindings=kb,
            )

            if approved[0]:
                self.console.print("[bold green]✓ Approved[/bold green]")
            else:
                self.console.print("[bold red]✗ Denied[/bold red]")

            return approved[0]

        except KeyboardInterrupt:
            self.console.print("[bold red]✗ Cancelled[/bold red]")
            return False
        except Exception:
            self.console.print("[bold red]✗ Error - Denied by default[/bold red]")
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
        """Approve a batch of tool calls with Rich UI.

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

        # Multiple tools - create a Rich table to show all tools
        table = Table(title=f"📦 Batch Tool Request ({len(tool_calls)} tools)", show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim", width=4)
        table.add_column("Tool", style="cyan")
        table.add_column("Details", style="white")
        table.add_column("Status", justify="center", width=10)

        # Check for dangerous commands in batch
        has_dangerous = False
        tool_statuses = []

        for idx, (tool_name, tool_input) in enumerate(tool_calls, 1):
            is_dangerous, danger_reason = DangerousCommandDetector.check_tool_call(tool_name, tool_input)
            if is_dangerous:
                has_dangerous = True

            # Format details based on tool type
            if tool_name == "bash":
                details = tool_input.get("command", "")[:50] + ("..." if len(tool_input.get("command", "")) > 50 else "")
            elif tool_name in ("write_file", "edit_file", "read_file"):
                details = tool_input.get("file_path", "")[:50]
            elif tool_name in ("grep", "glob"):
                details = f"pattern: {tool_input.get('pattern', '')[:30]}"
            else:
                details = str(list(tool_input.keys()))[:50]

            status_icon = "⚠️ " if is_dangerous else "✓"
            status_color = "red" if is_dangerous else "green"
            status = f"[{status_color}]{status_icon}[/{status_color}]"

            table.add_row(str(idx), tool_name, details, status)
            tool_statuses.append((is_dangerous, danger_reason))

        # Show the table
        panel = Panel(
            table,
            border_style="red" if has_dangerous else "cyan",
            padding=(1, 2),
        )
        self.console.print()
        self.console.print(panel)

        if has_dangerous:
            self.console.print("[bold yellow]⚠️  Batch contains dangerous operations![/bold yellow]")

        # Show batch options
        self.console.print()
        self.console.print("[dim]Choose an option:[/dim]")
        self.console.print("  [bold]a[/bold] - Approve all (dangerous tools will still prompt)")
        self.console.print("  [bold]e[/bold] - Approve each individually")
        self.console.print("  [bold]d[/bold] - Deny all")
        self.console.print("  [bold]Ctrl+C[/bold] - Cancel")
        self.console.print()

        # Create key bindings
        kb = KeyBindings()
        choice = [""]

        @kb.add("a")
        @kb.add("A")
        def _(event):
            choice[0] = "approve_all"
            event.app.exit(result="approve_all")

        @kb.add("e")
        @kb.add("E")
        def _(event):
            choice[0] = "approve_each"
            event.app.exit(result="approve_each")

        @kb.add("d")
        @kb.add("D")
        def _(event):
            choice[0] = "deny_all"
            event.app.exit(result="deny_all")

        @kb.add("c-c")
        def _(event):
            choice[0] = "deny_all"
            event.app.exit(result="deny_all")

        try:
            result = prompt(
                HTML("<style fg='cyan' bg=''>Your choice: </style>"),
                key_bindings=kb,
            )

            if choice[0] == "approve_all":
                self.console.print("[bold green]✓ Approving all tools...[/bold green]")
                # Approve everything (except dangerous in non-auto mode)
                results = []
                for (tool_name, tool_input), (is_dangerous, _) in zip(tool_calls, tool_statuses):
                    if is_dangerous and not self.session.auto_approve_tools:
                        # Still prompt for dangerous
                        approved = self.approve_tool(tool_name, tool_input)
                        results.append(approved)
                    else:
                        self.console.print(f"[dim]  ✓ {tool_name}[/dim]")
                        results.append(True)
                return results

            elif choice[0] == "approve_each":
                self.console.print("[bold cyan]→ Reviewing each tool individually...[/bold cyan]")
                # Prompt for each tool
                return [self.approve_tool(tool_name, tool_input) for tool_name, tool_input in tool_calls]

            else:  # deny_all
                self.console.print("[bold red]✗ Denied all tools[/bold red]")
                return [False] * len(tool_calls)

        except KeyboardInterrupt:
            self.console.print("[bold red]✗ Cancelled - Denied all tools[/bold red]")
            return [False] * len(tool_calls)
        except Exception as e:
            self.console.print(f"[bold red]✗ Error - Denied all tools: {e}[/bold red]")
            return [False] * len(tool_calls)
