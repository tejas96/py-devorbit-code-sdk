"""Messages resource for message operations.

This module provides the Messages resource class that mirrors the Claude SDK's
messages interface.
"""

from typing import Any, cast

from ..core.models import MessageResponse, TokenCountResponse
from ..core.streaming import AsyncMessageStream, MessageStream
from ..core.types import Message, Tool, ToolChoice
from ..providers._base import BaseProvider


class Messages:
    """Synchronous messages resource.

    Provides methods for creating messages and counting tokens,
    mirroring the Claude SDK's messages resource.
    """

    def __init__(self, provider: BaseProvider) -> None:
        """Initialize messages resource.

        Args:
            provider: Provider implementation to use
        """
        self._provider = provider

    def create(
        self,
        *,
        model: str,
        messages: list[Message],
        max_tokens: int,
        system: str | list[dict[str, str]] | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        top_k: int | None = None,
        stop_sequences: list[str] | None = None,
        stream: bool = False,
        tools: list[Tool] | None = None,
        tool_choice: ToolChoice | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> MessageResponse:
        """Create a message.

        Args:
            model: Model identifier
            messages: List of messages
            max_tokens: Maximum tokens to generate
            system: System prompt (string or list of text content blocks)
            temperature: Sampling temperature (0.0-1.0)
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            stop_sequences: Sequences that stop generation
            stream: Whether to stream the response
            tools: Available tools for the model
            tool_choice: Tool choice strategy
            metadata: Request metadata
            **kwargs: Additional provider-specific parameters

        Returns:
            MessageResponse with the model's response

        Raises:
            ValueError: If stream=True (use stream() method instead)
        """
        if stream:
            raise ValueError(
                "stream=True is not supported in create(). Use stream() method instead."
            )

        # Convert system to string if it's a list
        system_str = None
        if system is not None:
            if isinstance(system, list):
                system_str = "\n".join(block["text"] for block in system)
            else:
                system_str = system

        return self._provider.create_message(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            system=system_str,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            stop_sequences=stop_sequences,
            tools=tools,
            tool_choice=cast("dict[str, Any] | None", tool_choice),
            metadata=metadata,
            **kwargs,
        )

    def stream(
        self,
        *,
        model: str,
        messages: list[Message],
        max_tokens: int,
        system: str | list[dict[str, str]] | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        top_k: int | None = None,
        stop_sequences: list[str] | None = None,
        tools: list[Tool] | None = None,
        tool_choice: ToolChoice | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> MessageStream:
        """Stream a message.

        Args:
            model: Model identifier
            messages: List of messages
            max_tokens: Maximum tokens to generate
            system: System prompt (string or list of text content blocks)
            temperature: Sampling temperature (0.0-1.0)
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            stop_sequences: Sequences that stop generation
            tools: Available tools for the model
            tool_choice: Tool choice strategy
            metadata: Request metadata
            **kwargs: Additional provider-specific parameters

        Returns:
            MessageStream for iterating over events
        """
        # Convert system to string if it's a list
        system_str = None
        if system is not None:
            if isinstance(system, list):
                system_str = "\n".join(block["text"] for block in system)
            else:
                system_str = system

        stream_iterator = self._provider.stream_message(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            system=system_str,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            stop_sequences=stop_sequences,
            tools=tools,
            tool_choice=cast("dict[str, Any] | None", tool_choice),
            metadata=metadata,
            **kwargs,
        )

        return MessageStream(stream_iterator)

    def count_tokens(
        self,
        *,
        model: str,
        messages: list[Message],
        system: str | list[dict[str, str]] | None = None,
        tools: list[Tool] | None = None,
        **kwargs: Any,
    ) -> TokenCountResponse:
        """Count tokens in a message.

        Args:
            model: Model identifier
            messages: List of messages
            system: System prompt (string or list of text content blocks)
            tools: Available tools
            **kwargs: Additional provider-specific parameters

        Returns:
            TokenCountResponse with token count
        """
        # Convert system to string if it's a list
        system_str = None
        if system is not None:
            if isinstance(system, list):
                system_str = "\n".join(block["text"] for block in system)
            else:
                system_str = system

        return self._provider.count_tokens(
            model=model,
            messages=messages,
            system=system_str,
            tools=tools,
            **kwargs,
        )


class AsyncMessages:
    """Asynchronous messages resource.

    Async version of Messages resource.
    """

    def __init__(self, provider: BaseProvider) -> None:
        """Initialize async messages resource.

        Args:
            provider: Provider implementation to use
        """
        self._provider = provider

    async def create(
        self,
        *,
        model: str,
        messages: list[Message],
        max_tokens: int,
        system: str | list[dict[str, str]] | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        top_k: int | None = None,
        stop_sequences: list[str] | None = None,
        stream: bool = False,
        tools: list[Tool] | None = None,
        tool_choice: ToolChoice | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> MessageResponse:
        """Create a message asynchronously.

        Args:
            model: Model identifier
            messages: List of messages
            max_tokens: Maximum tokens to generate
            system: System prompt (string or list of text content blocks)
            temperature: Sampling temperature (0.0-1.0)
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            stop_sequences: Sequences that stop generation
            stream: Whether to stream the response
            tools: Available tools for the model
            tool_choice: Tool choice strategy
            metadata: Request metadata
            **kwargs: Additional provider-specific parameters

        Returns:
            MessageResponse with the model's response

        Raises:
            ValueError: If stream=True (use stream() method instead)
        """
        if stream:
            raise ValueError(
                "stream=True is not supported in create(). Use stream() method instead."
            )

        # Convert system to string if it's a list
        system_str = None
        if system is not None:
            if isinstance(system, list):
                system_str = "\n".join(block["text"] for block in system)
            else:
                system_str = system

        return await self._provider.acreate_message(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            system=system_str,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            stop_sequences=stop_sequences,
            tools=tools,
            tool_choice=cast("dict[str, Any] | None", tool_choice),
            metadata=metadata,
            **kwargs,
        )

    async def stream(
        self,
        *,
        model: str,
        messages: list[Message],
        max_tokens: int,
        system: str | list[dict[str, str]] | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        top_k: int | None = None,
        stop_sequences: list[str] | None = None,
        tools: list[Tool] | None = None,
        tool_choice: ToolChoice | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AsyncMessageStream:
        """Stream a message asynchronously.

        Args:
            model: Model identifier
            messages: List of messages
            max_tokens: Maximum tokens to generate
            system: System prompt (string or list of text content blocks)
            temperature: Sampling temperature (0.0-1.0)
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            stop_sequences: Sequences that stop generation
            tools: Available tools for the model
            tool_choice: Tool choice strategy
            metadata: Request metadata
            **kwargs: Additional provider-specific parameters

        Returns:
            AsyncMessageStream for iterating over events
        """
        # Convert system to string if it's a list
        system_str = None
        if system is not None:
            if isinstance(system, list):
                system_str = "\n".join(block["text"] for block in system)
            else:
                system_str = system

        stream_iterator = self._provider.astream_message(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            system=system_str,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            stop_sequences=stop_sequences,
            tools=tools,
            tool_choice=cast("dict[str, Any] | None", tool_choice),
            metadata=metadata,
            **kwargs,
        )

        return AsyncMessageStream(stream_iterator)

    async def count_tokens(
        self,
        *,
        model: str,
        messages: list[Message],
        system: str | list[dict[str, str]] | None = None,
        tools: list[Tool] | None = None,
        **kwargs: Any,
    ) -> TokenCountResponse:
        """Count tokens in a message asynchronously.

        Args:
            model: Model identifier
            messages: List of messages
            system: System prompt (string or list of text content blocks)
            tools: Available tools
            **kwargs: Additional provider-specific parameters

        Returns:
            TokenCountResponse with token count
        """
        # Convert system to string if it's a list
        system_str = None
        if system is not None:
            if isinstance(system, list):
                system_str = "\n".join(block["text"] for block in system)
            else:
                system_str = system

        return await self._provider.acount_tokens(
            model=model,
            messages=messages,
            system=system_str,
            tools=tools,
            **kwargs,
        )
