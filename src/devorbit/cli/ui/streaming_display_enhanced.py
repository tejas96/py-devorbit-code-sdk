"""Enhanced streaming display matching Claude Code CLI exactly.

This module provides the exact streaming response display from Claude Code,
with the orange circle indicator and clean text output.
"""

import time
from typing import TYPE_CHECKING


try:
    from rich.console import Console
    from rich.live import Live
    from rich.markdown import Markdown
    from rich.text import Text

    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    Console = None
    Live = None
    Markdown = None
    Text = None

if TYPE_CHECKING:
    from rich.console import Console as ConsoleType


class ClaudeStyleStreamingDisplay:
    """Exact replica of Claude Code's streaming display.
    
    Features:
    - Orange circle (⏺) indicator during streaming
    - Clean text output without boxes
    - Real-time character-by-character streaming
    - Smooth animations
    """

    def __init__(self, console: "ConsoleType | None" = None, no_color: bool = False):
        """Initialize Claude-style streaming display.
        
        Args:
            console: Rich console instance
            no_color: Disable colored output
        """
        self.console = console if console and HAS_RICH else None
        self.no_color = no_color
        self.is_streaming = False
        self.buffer: list[str] = []
        self.live_display: Live | None = None
        
    def start_streaming(self) -> None:
        """Start streaming with orange circle indicator."""
        self.is_streaming = True
        self.buffer = []
        
        if self.console and not self.no_color:
            # Show the iconic orange circle
            self.console.print("\n[rgb(255,107,53)]⏺[/rgb(255,107,53)]", end=" ")
        else:
            print("\n⏺", end=" ", flush=True)
    
    def append_chunk(self, chunk: str) -> None:
        """Append a chunk of streaming text.
        
        Args:
            chunk: Text chunk to display
        """
        if not chunk:
            return
            
        self.buffer.append(chunk)
        
        # Display immediately for real-time streaming feel
        if self.console and not self.no_color:
            # Clean, simple text output - no boxes or panels
            self.console.print(chunk, end="", highlight=False)
        else:
            print(chunk, end="", flush=True)
    
    def end_streaming(self) -> None:
        """End streaming and finalize display."""
        self.is_streaming = False
        
        # Add final newline
        if self.console:
            self.console.print("\n")
        else:
            print("\n")
        
        self.buffer = []
    


class ClaudeStyleToolDisplay:
    """Exact replica of Claude Code's tool execution display.
    
    Features:
    - Simple [Tool: Name] format
    - Status icons (⏳, ✓, ✗)
    - Clean output without heavy boxes
    - Collapsible sections
    """
    
    def __init__(self, console: "ConsoleType | None" = None, no_color: bool = False):
        """Initialize Claude-style tool display.
        
        Args:
            console: Rich console instance
            no_color: Disable colored output
        """
        self.console = console if console and HAS_RICH else None
        self.no_color = no_color
        self.start_time: float | None = None
        self.live_display: Live | None = None
    
    def show_tool_start(self, tool_name: str, tool_input: dict) -> None:
        """Show tool execution start - Claude Code style.
        
        Args:
            tool_name: Name of the tool
            tool_input: Tool parameters
        """
        self.start_time = time.time()
        
        if self.console and not self.no_color:
            # Simple format: [Tool: Name]
            self.console.print(f"\n[dim]╭─[/dim] [cyan]Tool: {tool_name}[/cyan] [dim]─────────────────────╮[/dim]")
            
            # Show key parameters
            for key, value in tool_input.items():
                value_str = str(value)
                if len(value_str) > 60:
                    value_str = value_str[:57] + "..."
                
                if key == "command":
                    self.console.print(f"[dim]│[/dim] [yellow]$[/yellow] [white]{value_str}[/white]")
                elif key in ("path", "file_path"):
                    self.console.print(f"[dim]│[/dim] [green]File:[/green] [white]{value_str}[/white]")
                else:
                    self.console.print(f"[dim]│[/dim] [cyan]{key}:[/cyan] [dim]{value_str}[/dim]")
            
            # Status line with spinner
            self.console.print(f"[dim]│[/dim] [rgb(88,166,255)]⏳ Executing...[/rgb(88,166,255)]")
            self.console.print(f"[dim]╰{'─' * 50}╯[/dim]")
        else:
            print(f"\n[Tool: {tool_name}]")
            for key, value in tool_input.items():
                value_str = str(value)[:60]
                print(f"  {key}: {value_str}")
            print("⏳ Executing...")
    
    def show_tool_result(
        self,
        tool_name: str,
        success: bool,
        output: str | None = None,
        error: str | None = None
    ) -> None:
        """Show tool execution result - Claude Code style.
        
        Args:
            tool_name: Tool name
            success: Success status
            output: Output text
            error: Error message
        """
        duration = time.time() - self.start_time if self.start_time else 0.0
        status_icon = "✓" if success else "✗"
        status_text = "Success" if success else "Failed"
        
        if self.console and not self.no_color:
            # Status color
            status_color = "rgb(16,185,129)" if success else "rgb(239,68,68)"
            
            self.console.print(f"[dim]╭─[/dim] [cyan]Tool: {tool_name}[/cyan] [dim]─────────────────────╮[/dim]")
            self.console.print(f"[dim]│[/dim] [{status_color}]{status_icon} {status_text}[/{status_color}] [dim]({duration:.2f}s)[/dim]")
            
            # Show output preview if available
            if success and output:
                lines = output.split('\n')[:10]  # First 10 lines
                if lines:
                    self.console.print(f"[dim]│[/dim]")
                    for line in lines:
                        if line.strip():
                            display_line = line[:70] + "..." if len(line) > 70 else line
                            self.console.print(f"[dim]│[/dim] [white]{display_line}[/white]")
                    
                    if len(output.split('\n')) > 10:
                        self.console.print(f"[dim]│[/dim] [dim]... (output truncated)[/dim]")
            
            elif error:
                self.console.print(f"[dim]│[/dim] [rgb(239,68,68)]{error}[/rgb(239,68,68)]")
            
            self.console.print(f"[dim]╰{'─' * 50}╯[/dim]")
        else:
            print(f"\n[Tool: {tool_name}]")
            print(f"{status_icon} {status_text} ({duration:.2f}s)")
            if output:
                print(output[:500])
            elif error:
                print(f"Error: {error}")
        
        self.start_time = None


__all__ = ["ClaudeStyleStreamingDisplay", "ClaudeStyleToolDisplay"]