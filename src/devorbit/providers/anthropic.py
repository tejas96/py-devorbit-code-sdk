"""Anthropic (Claude) provider implementation.

This provider wraps the official Anthropic SDK to provide a unified interface.
"""

from collections.abc import AsyncIterator, Iterator
import os
from typing import Any, cast

import anthropic  # type: ignore[import-not-found]

from .._models import (
    MessageResponse,
    ResponseContentBlock,
    TextBlock,
    TokenCountResponse,
    ToolUseBlock,
    Usage,
)
from .._types import Message, StopReason, Tool
from ._base import BaseProvider


class AnthropicProvider(BaseProvider):
    """Provider for Anthropic's Claude models.

    This provider wraps the official Anthropic SDK.
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str | None = None,
        timeout: float | None = None,
        max_retries: int = 2,
        **kwargs: Any,
    ) -> None:
        """Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key
            base_url: Optional base URL override
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            **kwargs: Additional configuration
        """
        super().__init__(api_key, **kwargs)

        # Get API key from environment if not provided
        if not api_key:
            api_key = os.environ.get("ANTHROPIC_API_KEY", "")

        # Initialize sync client
        self._client = anthropic.Anthropic(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )

        # Initialize async client
        self._async_client = anthropic.AsyncAnthropic(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )

    @property
    def name(self) -> str:
        """Provider name."""
        return "anthropic"

    def _convert_response(self, response: Any) -> MessageResponse:
        """Convert Anthropic response to our format.

        Args:
            response: Anthropic Message object

        Returns:
            MessageResponse in our format
        """
        # Convert content blocks
        content_blocks: list[ResponseContentBlock] = []
        for block in response.content:
            if block.type == "text":
                content_blocks.append(TextBlock(type="text", text=block.text))
            elif block.type == "tool_use":
                content_blocks.append(
                    ToolUseBlock(
                        type="tool_use",
                        id=block.id,
                        name=block.name,
                        input=block.input,
                    )
                )

        return MessageResponse(
            id=response.id,
            type="message",
            role="assistant",
            content=content_blocks,
            model=response.model,
            stop_reason=cast("StopReason | None", response.stop_reason),
            stop_sequence=response.stop_sequence,
            usage=Usage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                cache_creation_input_tokens=getattr(
                    response.usage, "cache_creation_input_tokens", None
                ),
                cache_read_input_tokens=getattr(response.usage, "cache_read_input_tokens", None),
            ),
        )

    def create_message(
        self,
        model: str,
        messages: list[Message],
        max_tokens: int,
        *,
        system: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        top_k: int | None = None,
        stop_sequences: list[str] | None = None,
        tools: list[Tool] | None = None,
        tool_choice: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> MessageResponse:
        """Create a message synchronously."""
        # Build request parameters
        params: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
        }

        if system is not None:
            params["system"] = system
        if temperature is not None:
            params["temperature"] = temperature
        if top_p is not None:
            params["top_p"] = top_p
        if top_k is not None:
            params["top_k"] = top_k
        if stop_sequences is not None:
            params["stop_sequences"] = stop_sequences
        if tools is not None:
            params["tools"] = tools
        if tool_choice is not None:
            params["tool_choice"] = tool_choice
        if metadata is not None:
            params["metadata"] = metadata

        params.update(kwargs)

        response = self._client.messages.create(**params)
        return self._convert_response(response)

    async def acreate_message(
        self,
        model: str,
        messages: list[Message],
        max_tokens: int,
        *,
        system: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        top_k: int | None = None,
        stop_sequences: list[str] | None = None,
        tools: list[Tool] | None = None,
        tool_choice: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> MessageResponse:
        """Create a message asynchronously."""
        # Build request parameters
        params: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
        }

        if system is not None:
            params["system"] = system
        if temperature is not None:
            params["temperature"] = temperature
        if top_p is not None:
            params["top_p"] = top_p
        if top_k is not None:
            params["top_k"] = top_k
        if stop_sequences is not None:
            params["stop_sequences"] = stop_sequences
        if tools is not None:
            params["tools"] = tools
        if tool_choice is not None:
            params["tool_choice"] = tool_choice
        if metadata is not None:
            params["metadata"] = metadata

        params.update(kwargs)

        response = await self._async_client.messages.create(**params)
        return self._convert_response(response)

    def stream_message(
        self,
        model: str,
        messages: list[Message],
        max_tokens: int,
        *,
        system: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        top_k: int | None = None,
        stop_sequences: list[str] | None = None,
        tools: list[Tool] | None = None,
        tool_choice: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Iterator[dict[str, Any]]:
        """Stream a message synchronously."""
        # Build request parameters
        params: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
        }

        if system is not None:
            params["system"] = system
        if temperature is not None:
            params["temperature"] = temperature
        if top_p is not None:
            params["top_p"] = top_p
        if top_k is not None:
            params["top_k"] = top_k
        if stop_sequences is not None:
            params["stop_sequences"] = stop_sequences
        if tools is not None:
            params["tools"] = tools
        if tool_choice is not None:
            params["tool_choice"] = tool_choice
        if metadata is not None:
            params["metadata"] = metadata

        params.update(kwargs)

        with self._client.messages.stream(**params) as stream:
            for event in stream:
                # Convert event to dict format
                yield self._convert_stream_event(event)

    async def astream_message(
        self,
        model: str,
        messages: list[Message],
        max_tokens: int,
        *,
        system: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        top_k: int | None = None,
        stop_sequences: list[str] | None = None,
        tools: list[Tool] | None = None,
        tool_choice: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream a message asynchronously."""
        # Build request parameters
        params: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
        }

        if system is not None:
            params["system"] = system
        if temperature is not None:
            params["temperature"] = temperature
        if top_p is not None:
            params["top_p"] = top_p
        if top_k is not None:
            params["top_k"] = top_k
        if stop_sequences is not None:
            params["stop_sequences"] = stop_sequences
        if tools is not None:
            params["tools"] = tools
        if tool_choice is not None:
            params["tool_choice"] = tool_choice
        if metadata is not None:
            params["metadata"] = metadata

        params.update(kwargs)

        async with self._async_client.messages.stream(**params) as stream:
            async for event in stream:
                # Convert event to dict format
                yield self._convert_stream_event(event)

    def _convert_stream_event(self, event: Any) -> dict[str, Any]:
        """Convert Anthropic stream event to dict.

        Args:
            event: Anthropic stream event

        Returns:
            Event as dictionary
        """
        # Anthropic SDK events are already in the correct format
        # We just need to convert to dict
        result: dict[str, Any]
        if hasattr(event, "model_dump"):
            result = dict(event.model_dump())
            return result
        if hasattr(event, "dict"):
            result = dict(event.dict())
            return result
        # Fallback: convert to dict manually
        return {"type": event.type, **vars(event)}

    def count_tokens(
        self,
        model: str,
        messages: list[Message],
        *,
        system: str | None = None,
        tools: list[Tool] | None = None,
        **kwargs: Any,
    ) -> TokenCountResponse:
        """Count tokens synchronously."""
        params: dict[str, Any] = {
            "model": model,
            "messages": messages,
        }

        if system is not None:
            params["system"] = system
        if tools is not None:
            params["tools"] = tools

        params.update(kwargs)

        result = self._client.messages.count_tokens(**params)
        return TokenCountResponse(input_tokens=result.input_tokens)

    async def acount_tokens(
        self,
        model: str,
        messages: list[Message],
        *,
        system: str | None = None,
        tools: list[Tool] | None = None,
        **kwargs: Any,
    ) -> TokenCountResponse:
        """Count tokens asynchronously."""
        params: dict[str, Any] = {
            "model": model,
            "messages": messages,
        }

        if system is not None:
            params["system"] = system
        if tools is not None:
            params["tools"] = tools

        params.update(kwargs)

        result = await self._async_client.messages.count_tokens(**params)
        return TokenCountResponse(input_tokens=result.input_tokens)
