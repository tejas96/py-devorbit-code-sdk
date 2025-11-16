"""Streaming response handler for Claude Code-style CLI experience."""

import json
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from devorbit._models import MessageResponse

    from .ui import CLIFormatter


class StreamingHandler:
    """Handle streaming responses with Claude Code-style display."""

    def __init__(self, formatter: "CLIFormatter", confirm_tools: bool = True) -> None:
        """Initialize streaming handler.

        Args:
            formatter: UI formatter instance
            confirm_tools: Whether to confirm before executing tools
        """
        self.formatter = formatter
        self.confirm_tools = confirm_tools
        self.current_text = ""
        self.tool_uses: list[dict[str, Any]] = []
        self.thinking_displayed = False

    def handle_stream(self, stream: Any) -> tuple[str, list[dict[str, Any]]]:
        """Handle streaming response from LLM.

        Args:
            stream: Streaming response object

        Returns:
            Tuple of (complete_text, tool_uses)
        """
        self.current_text = ""
        self.tool_uses = []
        self.thinking_displayed = False

        try:
            for event in stream:
                self._handle_event(event)
        except Exception as e:
            self.formatter.print_error("Stream processing failed", str(e))
            raise

        return self.current_text, self.tool_uses

    def _handle_event(self, event: Any) -> None:  # noqa: PLR0912
        """Handle individual stream event.

        Args:
            event: Stream event
        """
        event_type = getattr(event, "type", None)

        if event_type == "message_start":
            # Show thinking indicator at start
            if not self.thinking_displayed:
                self.formatter.print_thinking()
                self.thinking_displayed = True

        elif event_type == "content_block_start":
            block = getattr(event, "content_block", None)
            if block and hasattr(block, "type"):
                if block.type == "text":
                    # Start of text block - print newline
                    print()
                elif block.type == "tool_use":
                    # Tool use starting
                    tool_name = getattr(block, "name", "unknown")
                    tool_id = getattr(block, "id", "")
                    self.tool_uses.append(
                        {
                            "type": "tool_use",
                            "id": tool_id,
                            "name": tool_name,
                            "input": {},
                        }
                    )

        elif event_type == "content_block_delta":
            delta = getattr(event, "delta", None)
            if delta and hasattr(delta, "type"):
                if delta.type == "text_delta":
                    # Stream text token by token
                    text = getattr(delta, "text", "")
                    self.current_text += text
                    self.formatter.print_assistant_message(text, streaming=True)

                elif delta.type == "input_json_delta":
                    # Accumulate tool input
                    if self.tool_uses:
                        partial_json = getattr(delta, "partial_json", "")
                        # Accumulate the JSON (will parse when complete)
                        if "partial_input" not in self.tool_uses[-1]:
                            self.tool_uses[-1]["partial_input"] = ""
                        self.tool_uses[-1]["partial_input"] += partial_json

        elif event_type == "content_block_stop":
            # Block completed
            if self.tool_uses and "partial_input" in self.tool_uses[-1]:
                # Parse complete tool input
                try:
                    input_str = self.tool_uses[-1].pop("partial_input")
                    self.tool_uses[-1]["input"] = json.loads(input_str)

                    # Display tool use
                    tool_name = self.tool_uses[-1]["name"]
                    tool_input = self.tool_uses[-1]["input"]
                    self.formatter.print_tool_use(tool_name, tool_input)

                    # Ask for confirmation if enabled
                    if self.confirm_tools:
                        confirmed = self.formatter.confirm(
                            f"Execute {tool_name}?",
                            default=True,
                        )
                        self.tool_uses[-1]["confirmed"] = confirmed
                    else:
                        self.tool_uses[-1]["confirmed"] = True

                except json.JSONDecodeError as e:
                    self.formatter.print_error(
                        f"Failed to parse tool input for {self.tool_uses[-1]['name']}",
                        str(e),
                    )
                    self.tool_uses[-1]["confirmed"] = False

        elif event_type == "message_stop":
            # Message complete - print newline
            print()

    def handle_non_streaming(self, response: "MessageResponse") -> tuple[str, list[dict[str, Any]]]:
        """Handle non-streaming response.

        Args:
            response: Complete message response

        Returns:
            Tuple of (text_content, tool_uses)
        """
        text_content = ""
        tool_uses = []

        # Show thinking indicator
        self.formatter.print_thinking()

        # Process content blocks
        for block in response.content:
            if hasattr(block, "type"):
                if block.type == "text":
                    text = getattr(block, "text", "")
                    text_content += text
                    print()  # Newline before text
                    self.formatter.print_assistant_message(text, streaming=False)

                elif block.type == "tool_use":
                    tool_id = getattr(block, "id", "")
                    tool_name = getattr(block, "name", "")
                    tool_input = getattr(block, "input", {})

                    # Display tool use
                    self.formatter.print_tool_use(tool_name, tool_input)

                    # Ask for confirmation
                    confirmed = True
                    if self.confirm_tools:
                        confirmed = self.formatter.confirm(
                            f"Execute {tool_name}?",
                            default=True,
                        )

                    tool_uses.append(
                        {
                            "type": "tool_use",
                            "id": tool_id,
                            "name": tool_name,
                            "input": tool_input,
                            "confirmed": confirmed,
                        }
                    )

        return text_content, tool_uses


__all__ = ["StreamingHandler"]
