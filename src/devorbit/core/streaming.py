"""Streaming helpers for message streams.

This module provides utilities for handling Server-Sent Events (SSE) streaming,
mirroring the Claude SDK's streaming functionality.
"""

import json
from collections.abc import AsyncIterator, Iterator
from contextlib import contextmanager, suppress
from typing import Any

from .models import (
    MessageResponse,
    ResponseContentBlock,
    TextBlock,
    ToolUseBlock,
)


class MessageStream:
    """Synchronous message stream.

    Provides convenient methods for working with streaming responses,
    similar to Claude SDK's streaming interface.
    """

    def __init__(self, stream_iterator: Iterator[dict[str, Any]]) -> None:
        """Initialize stream.

        Args:
            stream_iterator: Iterator yielding stream events
        """
        self._iterator = stream_iterator
        self._message: MessageResponse | None = None
        self._current_content_blocks: list[ResponseContentBlock] = []
        self._tool_input_buffers: dict[int, str] = {}  # Buffer for accumulating tool input JSON
        self._finished = False

    def __iter__(self) -> Iterator[dict[str, Any]]:
        """Iterate over stream events."""
        return self._iterator

    def __enter__(self) -> "MessageStream":
        """Enter context manager."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit context manager."""
        self._finished = True

    @property
    def text_stream(self) -> Iterator[str]:
        """Iterate over text deltas only.

        Yields:
            Text delta strings
        """
        for event in self._iterator:
            if event.get("type") == "message_start":
                self._message = MessageResponse(**event["message"])
            elif event.get("type") == "content_block_start":
                block = event.get("content_block", {})
                if block.get("type") == "text":
                    self._current_content_blocks.append(TextBlock(type="text", text=""))
                elif block.get("type") == "tool_use":
                    self._current_content_blocks.append(
                        ToolUseBlock(
                            type="tool_use",
                            id=block["id"],
                            name=block["name"],
                            input={},
                        )
                    )
            elif event.get("type") == "content_block_delta":
                delta = event.get("delta", {})
                if delta.get("type") == "text_delta":
                    text = delta.get("text", "")
                    yield text
                    # Accumulate text
                    index = event.get("index", 0)
                    if index < len(self._current_content_blocks):
                        block = self._current_content_blocks[index]
                        if isinstance(block, TextBlock):
                            block.text += text
                elif delta.get("type") == "input_json_delta":
                    # Accumulate tool input JSON
                    partial_json = delta.get("partial_json", "")
                    index = event.get("index", 0)
                    if index not in self._tool_input_buffers:
                        self._tool_input_buffers[index] = ""
                    self._tool_input_buffers[index] += partial_json

    def get_final_message(self) -> MessageResponse:
        """Get the complete message after stream finishes.

        Returns:
            Complete MessageResponse

        Raises:
            RuntimeError: If stream hasn't finished
        """
        # Consume remaining events if not already consumed
        for _ in self._iterator:
            pass

        if self._message is None:
            raise RuntimeError("No message received in stream")

        # Parse accumulated tool input JSON and update tool use blocks
        for index, json_str in self._tool_input_buffers.items():
            if index < len(self._current_content_blocks):
                block = self._current_content_blocks[index]
                if isinstance(block, ToolUseBlock) and json_str:
                    # If JSON is invalid, keep empty dict
                    with suppress(json.JSONDecodeError):
                        block.input = json.loads(json_str)

        # Update message with accumulated content
        if self._current_content_blocks:
            self._message.content = self._current_content_blocks

        return self._message

    def get_final_text(self) -> str:
        """Get the final text content.

        Returns:
            Concatenated text from all text blocks
        """
        message = self.get_final_message()
        text_blocks = [block.text for block in message.content if isinstance(block, TextBlock)]
        return "".join(text_blocks)


class AsyncMessageStream:
    """Asynchronous message stream.

    Async version of MessageStream.
    """

    def __init__(self, stream_iterator: AsyncIterator[dict[str, Any]]) -> None:
        """Initialize async stream.

        Args:
            stream_iterator: Async iterator yielding stream events
        """
        self._iterator = stream_iterator
        self._message: MessageResponse | None = None
        self._current_content_blocks: list[ResponseContentBlock] = []
        self._tool_input_buffers: dict[int, str] = {}  # Buffer for accumulating tool input JSON
        self._finished = False

    def __aiter__(self) -> AsyncIterator[dict[str, Any]]:
        """Async iterate over stream events."""
        return self._iterator

    async def __aenter__(self) -> "AsyncMessageStream":
        """Enter async context manager."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context manager."""
        self._finished = True

    async def text_stream(self) -> AsyncIterator[str]:
        """Async iterate over text deltas only.

        Yields:
            Text delta strings
        """
        async for event in self._iterator:
            if event.get("type") == "message_start":
                self._message = MessageResponse(**event["message"])
            elif event.get("type") == "content_block_start":
                block = event.get("content_block", {})
                if block.get("type") == "text":
                    self._current_content_blocks.append(TextBlock(type="text", text=""))
                elif block.get("type") == "tool_use":
                    self._current_content_blocks.append(
                        ToolUseBlock(
                            type="tool_use",
                            id=block["id"],
                            name=block["name"],
                            input={},
                        )
                    )
            elif event.get("type") == "content_block_delta":
                delta = event.get("delta", {})
                if delta.get("type") == "text_delta":
                    text = delta.get("text", "")
                    yield text
                    # Accumulate text
                    index = event.get("index", 0)
                    if index < len(self._current_content_blocks):
                        block = self._current_content_blocks[index]
                        if isinstance(block, TextBlock):
                            block.text += text
                elif delta.get("type") == "input_json_delta":
                    # Accumulate tool input JSON
                    partial_json = delta.get("partial_json", "")
                    index = event.get("index", 0)
                    if index not in self._tool_input_buffers:
                        self._tool_input_buffers[index] = ""
                    self._tool_input_buffers[index] += partial_json

    async def get_final_message(self) -> MessageResponse:
        """Get the complete message after stream finishes.

        Returns:
            Complete MessageResponse

        Raises:
            RuntimeError: If stream hasn't finished
        """
        # Consume remaining events if not already consumed
        async for _ in self._iterator:
            pass

        if self._message is None:
            raise RuntimeError("No message received in stream")

        # Parse accumulated tool input JSON and update tool use blocks
        for index, json_str in self._tool_input_buffers.items():
            if index < len(self._current_content_blocks):
                block = self._current_content_blocks[index]
                if isinstance(block, ToolUseBlock) and json_str:
                    # If JSON is invalid, keep empty dict
                    with suppress(json.JSONDecodeError):
                        block.input = json.loads(json_str)

        # Update message with accumulated content
        if self._current_content_blocks:
            self._message.content = self._current_content_blocks

        return self._message

    async def get_final_text(self) -> str:
        """Get the final text content.

        Returns:
            Concatenated text from all text blocks
        """
        message = await self.get_final_message()
        text_blocks = [block.text for block in message.content if isinstance(block, TextBlock)]
        return "".join(text_blocks)


@contextmanager
def sync_stream(stream_iterator: Iterator[dict[str, Any]]) -> Iterator[MessageStream]:
    """Create a synchronous message stream context.

    Args:
        stream_iterator: Iterator yielding stream events

    Yields:
        MessageStream instance
    """
    stream = MessageStream(stream_iterator)
    try:
        yield stream
    finally:
        stream._finished = True


async def async_stream(
    stream_iterator: AsyncIterator[dict[str, Any]],
) -> AsyncIterator[AsyncMessageStream]:
    """Create an asynchronous message stream context.

    Args:
        stream_iterator: Async iterator yielding stream events

    Yields:
        AsyncMessageStream instance
    """
    stream = AsyncMessageStream(stream_iterator)
    try:
        yield stream
    finally:
        stream._finished = True
