"""Streaming response handler for Claude Code-style CLI experience."""

import json
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from devorbit._models import MessageResponse

    from .ui import CLIFormatter


class StreamingHandler:
    """Handle streaming responses with Claude Code-style display."""

    def __init__(
        self,
        formatter: "CLIFormatter",
        confirm_tools: bool = True,
        session_allow_all_callback: Any = None,
    ) -> None:
        """Initialize streaming handler.

        Args:
            formatter: UI formatter instance
            confirm_tools: Whether to confirm before executing tools
            session_allow_all_callback: Callback to check if session allows all tools
        """
        self.formatter = formatter
        self.confirm_tools = confirm_tools
        self.session_allow_all_callback = session_allow_all_callback
        self.current_text = ""
        self.tool_uses: list[dict[str, Any]] = []
        self.thinking_displayed = False
        self.usage_data: dict[str, int] | None = None
        self.text_started = False

    def handle_stream(self, stream: Any) -> tuple[str, list[dict[str, Any]], dict[str, int] | None]:
        """Handle streaming response from LLM.

        Args:
            stream: Streaming response object

        Returns:
            Tuple of (complete_text, tool_uses, usage_data)
        """
        self.current_text = ""
        self.tool_uses = []
        self.thinking_displayed = False
        self.usage_data = None
        self.text_started = False

        try:
            for event in stream:
                self._handle_event(event)
        except Exception:
            self.formatter.print_error("Stream processing failed")
            raise

        return self.current_text, self.tool_uses, self.usage_data

    def _handle_event(self, event: Any) -> None:  # noqa: PLR0912, PLR0915
        """Handle individual stream event.

        Args:
            event: Stream event (dictionary format)
        """
        # Events are dictionaries, not objects
        event_type = event.get("type") if isinstance(event, dict) else getattr(event, "type", None)

        if event_type == "message_start":
            # Message starting - no action here, wait for content blocks
            pass

        elif event_type == "content_block_start":
            block = (
                event.get("content_block")
                if isinstance(event, dict)
                else getattr(event, "content_block", None)
            )
            if block:
                block_type = (
                    block.get("type") if isinstance(block, dict) else getattr(block, "type", None)
                )
                if block_type == "text":
                    # Start of text block - print ⏺ symbol (only once)
                    if not self.text_started:
                        self.formatter.print_assistant_prefix()
                        self.text_started = True
                elif block_type == "tool_use":
                    # Tool use starting
                    tool_name = (
                        block.get("name", "unknown")
                        if isinstance(block, dict)
                        else getattr(block, "name", "unknown")
                    )
                    tool_id = (
                        block.get("id", "") if isinstance(block, dict) else getattr(block, "id", "")
                    )
                    self.tool_uses.append(
                        {
                            "type": "tool_use",
                            "id": tool_id,
                            "name": tool_name,
                            "input": {},
                        }
                    )

        elif event_type == "content_block_delta":
            delta = event.get("delta") if isinstance(event, dict) else getattr(event, "delta", None)
            if delta:
                delta_type = (
                    delta.get("type") if isinstance(delta, dict) else getattr(delta, "type", None)
                )
                if delta_type == "text_delta":
                    # Stream text token by token
                    text = (
                        delta.get("text", "")
                        if isinstance(delta, dict)
                        else getattr(delta, "text", "")
                    )
                    self.current_text += text
                    self.formatter.print_assistant_message(text, streaming=True)

                elif delta_type == "input_json_delta":
                    # Accumulate tool input
                    if self.tool_uses:
                        partial_json = (
                            delta.get("partial_json", "")
                            if isinstance(delta, dict)
                            else getattr(delta, "partial_json", "")
                        )
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

                    # Check if session allows all tools
                    session_allows_all = (
                        self.session_allow_all_callback and self.session_allow_all_callback()
                    )

                    # Ask for confirmation if enabled and not session-allowed
                    if self.confirm_tools and not session_allows_all:
                        confirmed = self.formatter.confirm(
                            f"Execute {tool_name}?",
                            default=True,
                        )
                        self.tool_uses[-1]["confirmed"] = confirmed
                    else:
                        self.tool_uses[-1]["confirmed"] = True

                except json.JSONDecodeError:
                    self.formatter.print_error(
                        f"Failed to parse tool input for {self.tool_uses[-1]['name']}"
                    )
                    self.tool_uses[-1]["confirmed"] = False

        elif event_type == "message_delta":
            # Capture usage data if available
            usage = event.get("usage") if isinstance(event, dict) else getattr(event, "usage", None)
            if usage:
                if isinstance(usage, dict):
                    self.usage_data = {
                        "input_tokens": usage.get("input_tokens", 0),
                        "output_tokens": usage.get("output_tokens", 0),
                        "cache_creation_input_tokens": usage.get("cache_creation_input_tokens", 0),
                        "cache_read_input_tokens": usage.get("cache_read_input_tokens", 0),
                    }
                else:
                    self.usage_data = {
                        "input_tokens": getattr(usage, "input_tokens", 0),
                        "output_tokens": getattr(usage, "output_tokens", 0),
                        "cache_creation_input_tokens": getattr(
                            usage, "cache_creation_input_tokens", 0
                        ),
                        "cache_read_input_tokens": getattr(usage, "cache_read_input_tokens", 0),
                    }

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
