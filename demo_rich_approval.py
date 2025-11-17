#!/usr/bin/env python3
"""Demo of the new Rich approval UI."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

console = Console()


def demo_single_tool_approval():
    """Demo single tool approval UI."""
    console.print("\n[bold cyan]═══ DEMO: Single Tool Approval (Safe Command) ═══[/bold cyan]\n")

    # Create tool tree for bash command
    tree = Tree("[bold cyan]🔧 bash[/bold cyan]")
    cmd_node = tree.add("[yellow]Command[/yellow]")
    cmd_node.add("[white]ls -la[/white]")
    tree.add("[dim]Timeout: 60s[/dim]")

    panel = Panel(
        tree,
        title="[bold]🔧 Tool Execution Request[/bold]",
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(panel)
    console.print("[dim]Press [bold]y[/bold] to approve, [bold]n[/bold] to deny[/dim]\n")


def demo_dangerous_tool_approval():
    """Demo dangerous tool approval UI."""
    console.print("\n[bold red]═══ DEMO: Dangerous Tool Approval ═══[/bold red]\n")

    # Create tool tree for dangerous command
    tree = Tree("[bold red]⚠️  bash[/bold red]")
    cmd_node = tree.add("[yellow]Command[/yellow]")
    cmd_node.add("[white]rm -rf /[/white]")
    tree.add("[dim]Timeout: 60s[/dim]")

    panel = Panel(
        tree,
        title="[bold]⚠️  Tool Execution Request[/bold]",
        border_style="red",
        padding=(1, 2),
    )
    console.print(panel)
    console.print("[bold yellow]⚠️  This is a potentially dangerous operation![/bold yellow]")
    console.print("[dim]Press [bold]y[/bold] to approve, [bold]n[/bold] to deny[/dim]\n")


def demo_batch_approval():
    """Demo batch approval UI."""
    console.print("\n[bold cyan]═══ DEMO: Batch Tool Approval (3 tools) ═══[/bold cyan]\n")

    # Create table for batch
    table = Table(
        title="📦 Batch Tool Request (3 tools)",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Tool", style="cyan")
    table.add_column("Details", style="white")
    table.add_column("Status", justify="center", width=10)

    table.add_row("1", "bash", "ls -la", "[green]✓[/green]")
    table.add_row("2", "read_file", "README.md", "[green]✓[/green]")
    table.add_row("3", "bash", "rm -rf /", "[red]⚠️ [/red]")

    panel = Panel(table, border_style="red", padding=(1, 2))
    console.print(panel)

    console.print("[bold yellow]⚠️  Batch contains dangerous operations![/bold yellow]")
    console.print()
    console.print("[dim]Choose an option:[/dim]")
    console.print("  [bold]a[/bold] - Approve all (dangerous tools will still prompt)")
    console.print("  [bold]e[/bold] - Approve each individually")
    console.print("  [bold]d[/bold] - Deny all")
    console.print()


def demo_file_edit():
    """Demo file edit approval UI."""
    console.print("\n[bold cyan]═══ DEMO: File Edit Tool ═══[/bold cyan]\n")

    # Create tool tree for edit_file
    tree = Tree("[bold cyan]🔧 edit_file[/bold cyan]")
    tree.add("[green]File:[/green] [white]src/main.py[/white]")
    tree.add("[red]Replace:[/red] [dim]def old_function():[/dim]")
    tree.add("[green]With:[/green] [white]def new_function():[/white]")

    panel = Panel(
        tree,
        title="[bold]🔧 Tool Execution Request[/bold]",
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(panel)
    console.print("[dim]Press [bold]y[/bold] to approve, [bold]n[/bold] to deny[/dim]\n")


def demo_auto_approve():
    """Demo auto-approve mode."""
    console.print("\n[bold green]═══ DEMO: Auto-Approve Mode ═══[/bold green]\n")
    console.print("[dim]⚡ Auto-approved:[/dim] [cyan]bash[/cyan]")
    console.print("[dim]⚡ Auto-approved:[/dim] [cyan]read_file[/cyan]")
    console.print("[dim]⚡ Auto-approved:[/dim] [cyan]grep[/cyan]")
    console.print()


if __name__ == "__main__":
    console.print("\n[bold magenta]╔════════════════════════════════════════════════════╗[/bold magenta]")
    console.print("[bold magenta]║  Rich UI Approval System - Visual Demo            ║[/bold magenta]")
    console.print("[bold magenta]╚════════════════════════════════════════════════════╝[/bold magenta]")

    demo_single_tool_approval()
    demo_file_edit()
    demo_dangerous_tool_approval()
    demo_batch_approval()
    demo_auto_approve()

    console.print("\n[bold green]✅ Demo Complete![/bold green]")
    console.print("[dim]This is how the new approval UI will look in Claude Code clone.[/dim]\n")
