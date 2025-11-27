"""LLM interaction handler with Claude Code UI.

This module handles message sending with Claude Code's exact streaming display.
"""

from typing import TYPE_CHECKING

from devorbit._models import MessageResponse, TextBlock, ToolUseBlock


if TYPE_CHECKING:
    from .session import CLISession


class LLMHandler:
    """Handles LLM interactions with Claude Code streaming display."""

    def __init__(self, session: "CLISession") -> None:
        """Initialize LLM handler.

        Args:
            session: CLI session instance
        """
        self.session = session
        self.max_tokens = 4096
        self.temperature: float | None = None
        self.max_tool_rounds = 5

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
        """
        # Add user message to history
        if not self.session.messages or self.session.messages[-1]["content"] != user_message:
            self.session.add_message("user", user_message)

        

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
        """Send message with Claude Code streaming display.

        Args:
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Complete response text
        """
        full_response_text = ""
        tool_round = 0

        while tool_round < self.max_tool_rounds:
            tool_round += 1

            # Start Claude-style streaming
            self.session.claude_streaming.start_streaming()

            try:
                # Get stream from provider
                stream = self.session.client.messages.stream(
                    model=self.session.model,
                    messages=self.session.messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    tools=self.session.tool_executor.get_tool_definitions(),
                )

                # Process stream - character by character for smooth display
                text_chunk_buffer = ""
                with stream:
                    for text_chunk in stream.text_stream:
                        text_chunk_buffer += text_chunk
                        # Display immediately for real-time feel
                        self.session.claude_streaming.append_chunk(text_chunk)

                    final_message = stream.get_final_message()

                # End streaming
                self.session.claude_streaming.end_streaming()

                if text_chunk_buffer:
                    full_response_text += text_chunk_buffer

                # Handle tool calls
                tool_calls = [
                    block for block in final_message.content if isinstance(block, ToolUseBlock)
                ]

                if not tool_calls:
                    break

                # Add assistant message to history
                self.session.add_message("assistant", final_message.content)  # type: ignore

                # Get tool approvals
                tool_approvals = self.session.tool_approval.approve_batch(
                    [(tool_call.name, tool_call.input or {}) for tool_call in tool_calls]
                )

                # Execute tools with Claude-style display
                tool_results = []
                for tool_call, approved in zip(tool_calls, tool_approvals, strict=False):
                    if not approved:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_call.id,
                            "content": "Tool execution was denied by user.",
                            "is_error": True,
                        })
                        continue

                    # Show tool start in Claude style
                    self.session.claude_tool_display.show_tool_start(
                        tool_call.name,
                        tool_call.input or {}
                    )

                    try:
                        # Execute tool
                        result = self.session.tool_executor.execute_tool(
                            tool_call.name,
                            tool_call.input or {}
                        )
                        
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_call.id,
                            "content": result,
                        })
                        
                        # Show success result
                        is_success = not result.startswith("Error")
                        self.session.claude_tool_display.show_tool_result(
                            tool_call.name,
                            success=is_success,
                            output=result if is_success else None,
                            error=result if not is_success else None
                        )
                        
                    except Exception as e:
                        error_msg = f"Tool execution failed: {e}"
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_call.id,
                            "content": error_msg,
                            "is_error": True,
                        })
                        
                        # Show error result
                        self.session.claude_tool_display.show_tool_result(
                            tool_call.name,
                            success=False,
                            error=error_msg
                        )

                # Add tool results to messages
                self.session.add_message("user", tool_results)

            except Exception as e:
                self.session.claude_streaming.end_streaming()
                self.session.print_error(f"Streaming error: {e}")
                raise

        if tool_round >= self.max_tool_rounds:
            if self.session.console:
                self.session.console.print("\n[dim]⚠ Reached maximum tool execution rounds[/dim]")
            else:
                print("\n⚠ Reached maximum tool execution rounds")

        return full_response_text

    def _send_non_streaming(self, max_tokens: int, temperature: float | None) -> str:
        """Send message without streaming.

        Args:
            max_tokens: Maximum tokens
            temperature: Temperature

        Returns:
            Response text
        """
        full_response_text = ""
        tool_round = 0

        while tool_round < self.max_tool_rounds:
            tool_round += 1

            # Send message
            response: MessageResponse = self.session.client.messages.create(
                model=self.session.model,
                messages=self.session.messages,
                max_tokens=max_tokens,
                temperature=temperature,
                tools=self.session.tool_executor.get_tool_definitions(),
            )

            # Extract text
            text_blocks = [block for block in response.content if isinstance(block, TextBlock)]
            text = "".join(block.text for block in text_blocks)

            if text:
                full_response_text += text
                # Display with orange circle prefix
                if self.session.console:
                    self.session.console.print(f"\n[rgb(255,107,53)]⏺[/rgb(255,107,53)] {text}")
                else:
                    print(f"\n⏺ {text}")

            # Handle tool calls
            tool_calls = [block for block in response.content if isinstance(block, ToolUseBlock)]

            if not tool_calls:
                break

            self.session.add_message("assistant", response.content)  # type: ignore

            tool_approvals = self.session.tool_approval.approve_batch(
                [(tool_call.name, tool_call.input or {}) for tool_call in tool_calls]
            )

            tool_results = []
            for tool_call, approved in zip(tool_calls, tool_approvals, strict=False):
                if not approved:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call.id,
                        "content": "Tool execution was denied by user.",
                        "is_error": True,
                    })
                    continue

                self.session.claude_tool_display.show_tool_start(
                    tool_call.name,
                    tool_call.input or {}
                )

                try:
                    result = self.session.tool_executor.execute_tool(
                        tool_call.name,
                        tool_call.input or {}
                    )
                    
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call.id,
                        "content": result,
                    })
                    
                    is_success = not result.startswith("Error")
                    self.session.claude_tool_display.show_tool_result(
                        tool_call.name,
                        success=is_success,
                        output=result if is_success else None,
                        error=result if not is_success else None
                    )
                    
                except Exception as e:
                    error_msg = f"Tool execution failed: {e}"
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call.id,
                        "content": error_msg,
                        "is_error": True,
                    })
                    
                    self.session.claude_tool_display.show_tool_result(
                        tool_call.name,
                        success=False,
                        error=error_msg
                    )

            self.session.add_message("user", tool_results)

        return full_response_text


__all__ = ["LLMHandler"]