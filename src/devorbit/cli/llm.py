"""LLM interaction handler for Devorbit CLI with streaming support.

This module handles message sending, streaming responses, and tool execution
in a provider-agnostic way.
"""

from typing import TYPE_CHECKING

from prompt_toolkit import prompt
from prompt_toolkit.formatted_text import HTML

from devorbit._models import MessageResponse, TextBlock, ToolUseBlock


if TYPE_CHECKING:
    from .session import CLISession


class LLMHandler:
    """Handles LLM interactions with streaming and tool support.

    This class provides a clean interface for sending messages to the LLM,
    handling streaming responses, and executing tools - all in a provider-
    agnostic way.
    """

    # Default configuration (Claude Code-like behavior)
    DEFAULT_MAX_TOOL_ROUNDS = 25  # Higher limit like Claude Code
    PROMPT_CONTINUE_AT = 10  # Prompt user to continue after this many rounds

    def __init__(self, session: "CLISession") -> None:
        """Initialize LLM handler.

        Args:
            session: CLI session instance
        """
        self.session = session
        self.max_tokens = 4096  # Default max tokens
        self.temperature: float | None = None  # Use provider default
        self.max_tool_rounds = self.DEFAULT_MAX_TOOL_ROUNDS
        self.prompt_continue_at = self.PROMPT_CONTINUE_AT
        self._tool_execution_count = 0  # Track total tool executions in session

    def _should_prompt_continue(self, tool_round: int) -> bool:
        """Check if we should prompt user to continue.

        Args:
            tool_round: Current tool round number

        Returns:
            True if we should prompt user to continue
        """
        return tool_round > 0 and tool_round % self.prompt_continue_at == 0

    def _prompt_user_continue(self, tool_round: int) -> bool:
        """Prompt user to continue execution (Claude Code-style).

        Args:
            tool_round: Current tool round number

        Returns:
            True if user wants to continue, False otherwise
        """
        self.session.print("")
        self.session.print_warning(f"⚡ Executed {tool_round} tool rounds so far.")
        self.session.print_info("The assistant is still working. Continue?")
        self.session.print("")

        try:
            response = (
                prompt(
                    HTML("<style fg='cyan'>Continue? (y/n): </style>"),
                )
                .strip()
                .lower()
            )
            return response in ("y", "yes", "")
        except (KeyboardInterrupt, EOFError):
            return False

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
        user_stopped = False

        # Tool execution loop (Claude Code-style with continue prompt)
        while tool_round < self.max_tool_rounds and not user_stopped:
            tool_round += 1

            # Check if we should prompt user to continue (after every N rounds)
            if self._should_prompt_continue(tool_round):
                if not self._prompt_user_continue(tool_round):
                    user_stopped = True
                    self.session.print_info(
                        f"Stopped after {tool_round} tool rounds. "
                        "You can continue the conversation."
                    )
                    break

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

                # Add assistant message with tool calls to history
                self.session.add_message(
                    "assistant",
                    final_message.content,  # type: ignore[arg-type]
                )

                # Get approval for all tools
                tool_approvals = self.session.tool_approval.approve_batch(
                    [(tool_call.name, tool_call.input or {}) for tool_call in tool_calls]
                )

                # Execute approved tools
                tool_results = []
                for tool_call, approved in zip(tool_calls, tool_approvals, strict=False):
                    self._tool_execution_count += 1

                    if not approved:
                        # Tool was denied, send denial result to Claude
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_call.id,
                                "content": "Tool execution was denied by user.",
                                "is_error": True,
                            }
                        )
                        continue

                    # Start Claude Code-style execution display
                    self.session.live_tool_execution.start_execution(
                        tool_call.name, tool_call.input or {}
                    )

                    # Execute approved tool
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
                        # Show final result with Claude Code-style display
                        is_success = not result.startswith("Error")
                        self.session.live_tool_execution.finish_execution(
                            tool_name=tool_call.name,
                            tool_input=tool_call.input or {},
                            success=is_success,
                            output=result if is_success else None,
                            error=result if not is_success else None,
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
                        # Show error result with Claude Code-style display
                        self.session.live_tool_execution.finish_execution(
                            tool_name=tool_call.name,
                            tool_input=tool_call.input or {},
                            success=False,
                            error=error_msg,
                        )

                # Add tool results as user message
                self.session.add_message("user", tool_results)

                # Continue loop to get next response with tool results

            except Exception as e:
                self.session.streaming.end_streaming()
                self.session.print_error(f"Streaming error: {e}")
                raise

        # Handle reaching max rounds (Claude Code-style)
        if tool_round >= self.max_tool_rounds and not user_stopped:
            self.session.print_warning(
                f"\n⚠ Reached maximum tool execution limit ({self.max_tool_rounds} rounds)"
            )
            self.session.print_info("The assistant was still working. You can ask it to continue.")

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
        user_stopped = False

        # Tool execution loop (Claude Code-style with continue prompt)
        while tool_round < self.max_tool_rounds and not user_stopped:
            tool_round += 1

            # Check if we should prompt user to continue (after every N rounds)
            if self._should_prompt_continue(tool_round):
                if not self._prompt_user_continue(tool_round):
                    user_stopped = True
                    self.session.print_info(
                        f"Stopped after {tool_round} tool rounds. "
                        "You can continue the conversation."
                    )
                    break

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

            # Add assistant message to history
            self.session.add_message("assistant", response.content)  # type: ignore[arg-type]

            # Get approval for all tools
            tool_approvals = self.session.tool_approval.approve_batch(
                [(tool_call.name, tool_call.input or {}) for tool_call in tool_calls]
            )

            # Execute approved tools
            tool_results = []
            for tool_call, approved in zip(tool_calls, tool_approvals, strict=False):
                self._tool_execution_count += 1

                if not approved:
                    # Tool was denied, send denial result to Claude
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_call.id,
                            "content": "Tool execution was denied by user.",
                            "is_error": True,
                        }
                    )
                    continue

                # Start Claude Code-style execution display
                self.session.live_tool_execution.start_execution(
                    tool_call.name, tool_call.input or {}
                )

                # Execute approved tool
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
                    # Show final result with Claude Code-style display
                    is_success = not result.startswith("Error")
                    self.session.live_tool_execution.finish_execution(
                        tool_name=tool_call.name,
                        tool_input=tool_call.input or {},
                        success=is_success,
                        output=result if is_success else None,
                        error=result if not is_success else None,
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
                    # Show error result with Claude Code-style display
                    self.session.live_tool_execution.finish_execution(
                        tool_name=tool_call.name,
                        tool_input=tool_call.input or {},
                        success=False,
                        error=error_msg,
                    )

            # Add tool results to messages
            self.session.add_message("user", tool_results)

            # Update context info in status line
            if hasattr(response, "usage"):
                self.session.status_line.set_context(
                    response.usage.input_tokens + response.usage.output_tokens, 200000
                )

        # Handle reaching max rounds (Claude Code-style)
        if tool_round >= self.max_tool_rounds and not user_stopped:
            self.session.print_warning(
                f"\n⚠ Reached maximum tool execution limit ({self.max_tool_rounds} rounds)"
            )
            self.session.print_info("The assistant was still working. You can ask it to continue.")

        return full_response_text

    def set_model_params(
        self, max_tokens: int | None = None, temperature: float | None = None
    ) -> None:
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
