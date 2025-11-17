"""LLM interaction handler for Devorbit CLI with streaming support.

This module handles message sending, streaming responses, and tool execution
in a provider-agnostic way.
"""

from typing import TYPE_CHECKING, Any

from devorbit._models import MessageResponse, TextBlock, ToolUseBlock


if TYPE_CHECKING:
    from .session import CLISession


class LLMHandler:
    """Handles LLM interactions with streaming and tool support.

    This class provides a clean interface for sending messages to the LLM,
    handling streaming responses, and executing tools - all in a provider-
    agnostic way.
    """

    def __init__(self, session: "CLISession") -> None:
        """Initialize LLM handler.

        Args:
            session: CLI session instance
        """
        self.session = session
        self.max_tokens = 4096  # Default max tokens
        self.temperature = None  # Use provider default

    def send_message(
        self,
        user_message: str,
        stream: bool = True,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """Send a message to the LLM and get response.

        Args:
            user_message: User's message
            stream: Whether to stream the response
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Assistant's response text

        Raises:
            Exception: If message sending fails
        """
        # Add user message to history (already done in REPL, but ensure it's there)
        if not self.session.messages or self.session.messages[-1]["content"] != user_message:
            self.session.add_message("user", user_message)

        # Prepare parameters
        tokens = max_tokens or self.max_tokens
        temp = temperature if temperature is not None else self.temperature

        try:
            if stream:
                return self._send_streaming(tokens, temp)
            return self._send_non_streaming(tokens, temp)
        except Exception as e:
            self.session.print_error(f"Failed to send message: {e}")
            if self.session.debug:
                raise
            return f"Error: {e}"

    def _send_streaming(self, max_tokens: int, temperature: float | None) -> str:
        """Send message with streaming response.

        Args:
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Complete response text
        """
        self.session.streaming.start_streaming()

        try:
            # Get stream from provider
            stream = self.session.client.messages.stream(
                model=self.session.model,
                messages=self.session.messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            # Process stream
            full_text = ""
            with stream:
                for text_chunk in stream.text_stream:
                    full_text += text_chunk
                    self.session.streaming.append_chunk(text_chunk)

                # Get final message
                final_message = stream.get_final_message()

            self.session.streaming.finish_streaming()

            # Handle tool calls if present
            if final_message.content:
                tool_calls = [
                    block for block in final_message.content if isinstance(block, ToolUseBlock)
                ]
                if tool_calls:
                    self.session.print_info(f"\n{len(tool_calls)} tool call(s) detected")
                    # TODO: Implement tool execution in next iteration
                    for tool_call in tool_calls:
                        self.session.tool_display.show_tool_call(
                            tool_call.name, tool_call.input or {}
                        )

            return full_text

        except Exception as e:
            self.session.streaming.show_error(str(e))
            raise

    def _send_non_streaming(self, max_tokens: int, temperature: float | None) -> str:
        """Send message without streaming.

        Args:
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Complete response text
        """
        self.session.print_info("Processing your request...")

        # Send message
        response: MessageResponse = self.session.client.messages.create(
            model=self.session.model,
            messages=self.session.messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        # Extract text content
        text_blocks = [block for block in response.content if isinstance(block, TextBlock)]
        full_text = "".join(block.text for block in text_blocks)

        # Handle tool calls if present
        tool_calls = [block for block in response.content if isinstance(block, ToolUseBlock)]
        if tool_calls:
            self.session.print_info(f"{len(tool_calls)} tool call(s) detected")
            # TODO: Implement tool execution in next iteration
            for tool_call in tool_calls:
                self.session.tool_display.show_tool_call(tool_call.name, tool_call.input or {})

        # Update context info in status line
        if hasattr(response, "usage"):
            self.session.status_line.set_context(
                response.usage.input_tokens + response.usage.output_tokens, 200000
            )

        return full_text

    def set_model_params(self, max_tokens: int | None = None, temperature: float | None = None) -> None:
        """Update model parameters.

        Args:
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
        """
        if max_tokens is not None:
            self.max_tokens = max_tokens
        if temperature is not None:
            self.temperature = temperature


__all__ = ["LLMHandler"]
