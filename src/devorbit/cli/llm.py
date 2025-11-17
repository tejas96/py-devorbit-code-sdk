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
        self.max_tool_rounds = 5  # Max tool execution rounds to prevent loops

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
        """Send message with streaming response and tool execution.

        Args:
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Complete response text
        """
        full_response_text = ""
        tool_round = 0

        # Tool execution loop
        while tool_round < self.max_tool_rounds:
            tool_round += 1

            self.session.streaming.start_streaming()

            try:
                # Get stream from provider with tool definitions
                stream = self.session.client.messages.stream(
                    model=self.session.model,
                    messages=self.session.messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    tools=self.session.tool_executor.get_tool_definitions(),
                )

                # Process stream
                text_chunk_buffer = ""
                with stream:
                    for text_chunk in stream.text_stream:
                        text_chunk_buffer += text_chunk
                        self.session.streaming.append_chunk(text_chunk)

                    # Get final message
                    final_message = stream.get_final_message()

                self.session.streaming.end_streaming()

                # Add text to full response
                if text_chunk_buffer:
                    full_response_text += text_chunk_buffer

                # Handle tool calls if present
                tool_calls = [
                    block for block in final_message.content if isinstance(block, ToolUseBlock)
                ]

                if not tool_calls:
                    # No more tools to execute, we're done
                    break

                # Execute tools
                self.session.print_info(f"\n🔧 Executing {len(tool_calls)} tool(s)...")

                # Add assistant message with tool calls to history
                self.session.add_message("assistant", final_message.content)

                # Execute each tool and collect results
                tool_results = []
                for tool_call in tool_calls:
                    # Display tool call
                    self.session.tool_display.show_tool_call(
                        tool_call.name, tool_call.input or {}
                    )

                    # Execute tool
                    try:
                        result = self.session.tool_executor.execute_tool(
                            tool_call.name, tool_call.input or {}
                        )
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_call.id,
                                "content": result,
                            }
                        )
                        # Show result
                        self.session.tool_display.show_tool_result(
                            tool_call.name,
                            result,
                            success=not result.startswith("Error"),
                        )
                    except Exception as e:
                        error_msg = f"Tool execution failed: {e}"
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_call.id,
                                "content": error_msg,
                                "is_error": True,
                            }
                        )
                        self.session.print_error(error_msg)

                # Add tool results as user message
                self.session.add_message("user", tool_results)

                # Continue loop to get next response with tool results

            except Exception as e:
                self.session.streaming.end_streaming()
                self.session.print_error(f"Streaming error: {e}")
                raise

        if tool_round >= self.max_tool_rounds:
            self.session.print_warning("\n⚠ Reached maximum tool execution rounds")

        return full_response_text

    def _send_non_streaming(self, max_tokens: int, temperature: float | None) -> str:
        """Send message without streaming (with tool execution support).

        Args:
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Complete response text
        """
        full_response_text = ""
        tool_round = 0

        # Tool execution loop
        while tool_round < self.max_tool_rounds:
            tool_round += 1

            self.session.print_info("Processing your request...")

            # Send message with tool definitions
            response: MessageResponse = self.session.client.messages.create(
                model=self.session.model,
                messages=self.session.messages,
                max_tokens=max_tokens,
                temperature=temperature,
                tools=self.session.tool_executor.get_tool_definitions(),
            )

            # Extract text content
            text_blocks = [block for block in response.content if isinstance(block, TextBlock)]
            text = "".join(block.text for block in text_blocks)

            if text:
                full_response_text += text
                self.session.print(text)

            # Handle tool calls if present
            tool_calls = [block for block in response.content if isinstance(block, ToolUseBlock)]

            if not tool_calls:
                # No more tools, we're done
                break

            # Execute tools
            self.session.print_info(f"\n🔧 Executing {len(tool_calls)} tool(s)...")

            # Add assistant message to history
            self.session.add_message("assistant", response.content)

            # Execute each tool
            tool_results = []
            for tool_call in tool_calls:
                self.session.tool_display.show_tool_call(tool_call.name, tool_call.input or {})

                try:
                    result = self.session.tool_executor.execute_tool(
                        tool_call.name, tool_call.input or {}
                    )
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_call.id,
                            "content": result,
                        }
                    )
                    self.session.tool_display.show_tool_result(
                        tool_call.name, result, success=not result.startswith("Error")
                    )
                except Exception as e:
                    error_msg = f"Tool execution failed: {e}"
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_call.id,
                            "content": error_msg,
                            "is_error": True,
                        }
                    )
                    self.session.print_error(error_msg)

            # Add tool results to messages
            self.session.add_message("user", tool_results)

            # Update context info in status line
            if hasattr(response, "usage"):
                self.session.status_line.set_context(
                    response.usage.input_tokens + response.usage.output_tokens, 200000
                )

        if tool_round >= self.max_tool_rounds:
            self.session.print_warning("\n⚠ Reached maximum tool execution rounds")

        return full_response_text

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
