"""Code Llama provider implementation.

This provider supports Code Llama models via OpenAI-compatible APIs
(like Together AI, Replicate, or Anyscale) or direct Meta API.
"""

import contextlib
import json
import os
from collections.abc import AsyncIterator, Iterator
from typing import Any, cast

import httpx

from ..core.models import (
    MessageResponse,
    ResponseContentBlock,
    TextBlock,
    TokenCountResponse,
    ToolUseBlock,
    Usage,
)
from ..core.types import Message, StopReason, Tool
from ._base import BaseProvider


class CodeLlamaProvider(BaseProvider):
    """Provider for Code Llama models.

    This provider supports Code Llama via OpenAI-compatible endpoints
    (Together AI, Replicate, Anyscale, etc.) or can be configured
    with a custom endpoint.

    Common endpoints:
    - Together AI: https://api.together.xyz/v1
    - Anyscale: https://api.endpoints.anyscale.com/v1
    - Replicate: Custom implementation
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
        """Initialize Code Llama provider.

        Args:
            api_key: API key for the service
            base_url: Base URL for the API (e.g., "https://api.together.xyz/v1")
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            **kwargs: Additional configuration
        """
        super().__init__(api_key, **kwargs)

        # Get API key from environment if not provided
        if not api_key:
            api_key = os.environ.get("CODELLAMA_API_KEY", "")

        # Default to Together AI if no base URL provided
        if not base_url:
            base_url = os.environ.get("CODELLAMA_BASE_URL", "https://api.together.xyz/v1")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout or 120.0
        self.max_retries = max_retries

        # Initialize HTTP clients
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=self.timeout,
        )

        self._async_client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=self.timeout,
        )

    @property
    def name(self) -> str:
        """Provider name."""
        return "codellama"

    def _convert_messages_to_openai_format(
        self, messages: list[Message], system: str | None = None
    ) -> list[dict[str, Any]]:
        """Convert our message format to OpenAI-compatible format.

        Args:
            messages: Our message format
            system: System prompt to prepend

        Returns:
            OpenAI-compatible message format
        """
        openai_messages = []

        # Add system message if provided
        if system:
            openai_messages.append({"role": "system", "content": system})

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if isinstance(content, str):
                openai_messages.append({"role": role, "content": content})
            elif isinstance(content, list):
                # For Code Llama, we primarily handle text
                text_parts = []
                for block in content:
                    if block["type"] == "text":
                        text_parts.append(block["text"])
                    elif block["type"] == "tool_result":
                        text_parts.append(f"Tool result: {block.get('content', '')}")

                if text_parts:
                    openai_messages.append({"role": role, "content": "\n".join(text_parts)})

        return openai_messages

    def _convert_response(self, response_data: dict[str, Any], model: str) -> MessageResponse:
        """Convert API response to our format.

        Args:
            response_data: API response data
            model: Model name

        Returns:
            MessageResponse in our format
        """
        choice = response_data["choices"][0]
        message = choice["message"]

        # Convert content blocks
        content_blocks: list[ResponseContentBlock] = []

        if message.get("content"):
            content_blocks.append(TextBlock(type="text", text=message["content"]))

        # Handle tool calls if present
        if message.get("tool_calls"):
            for tool_call in message["tool_calls"]:
                content_blocks.append(
                    ToolUseBlock(
                        type="tool_use",
                        id=tool_call["id"],
                        name=tool_call["function"]["name"],
                        input=json.loads(tool_call["function"]["arguments"]),
                    )
                )

        # Map finish reason
        stop_reason_map = {
            "stop": "end_turn",
            "length": "max_tokens",
            "tool_calls": "tool_use",
            "eos": "end_turn",
        }
        stop_reason = stop_reason_map.get(choice.get("finish_reason"), "end_turn")

        usage = response_data.get("usage", {})

        return MessageResponse(
            id=response_data.get("id", f"codellama-{hash(str(response_data))}"),
            type="message",
            role="assistant",
            content=content_blocks,
            model=model,
            stop_reason=cast("StopReason | None", stop_reason),
            stop_sequence=None,
            usage=Usage(
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
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
        openai_messages = self._convert_messages_to_openai_format(messages, system)

        payload: dict[str, Any] = {
            "model": model,
            "messages": openai_messages,
            "max_tokens": max_tokens,
        }

        if temperature is not None:
            payload["temperature"] = temperature
        if top_p is not None:
            payload["top_p"] = top_p
        if top_k is not None:
            payload["top_k"] = top_k
        if stop_sequences is not None:
            payload["stop"] = stop_sequences

        payload.update(kwargs)

        response = self._client.post("/chat/completions", json=payload)
        response.raise_for_status()

        return self._convert_response(response.json(), model)

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
        openai_messages = self._convert_messages_to_openai_format(messages, system)

        payload: dict[str, Any] = {
            "model": model,
            "messages": openai_messages,
            "max_tokens": max_tokens,
        }

        if temperature is not None:
            payload["temperature"] = temperature
        if top_p is not None:
            payload["top_p"] = top_p
        if top_k is not None:
            payload["top_k"] = top_k
        if stop_sequences is not None:
            payload["stop"] = stop_sequences

        payload.update(kwargs)

        response = await self._async_client.post("/chat/completions", json=payload)
        response.raise_for_status()

        return self._convert_response(response.json(), model)

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
        openai_messages = self._convert_messages_to_openai_format(messages, system)

        payload: dict[str, Any] = {
            "model": model,
            "messages": openai_messages,
            "max_tokens": max_tokens,
            "stream": True,
        }

        if temperature is not None:
            payload["temperature"] = temperature
        if top_p is not None:
            payload["top_p"] = top_p
        if top_k is not None:
            payload["top_k"] = top_k
        if stop_sequences is not None:
            payload["stop"] = stop_sequences

        payload.update(kwargs)

        with self._client.stream("POST", "/chat/completions", json=payload) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        if chunk["choices"] and chunk["choices"][0].get("delta"):
                            delta = chunk["choices"][0]["delta"]
                            if delta.get("content"):
                                yield {
                                    "type": "content_block_delta",
                                    "index": 0,
                                    "delta": {"type": "text_delta", "text": delta["content"]},
                                }
                    except json.JSONDecodeError:
                        continue

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
        openai_messages = self._convert_messages_to_openai_format(messages, system)

        payload: dict[str, Any] = {
            "model": model,
            "messages": openai_messages,
            "max_tokens": max_tokens,
            "stream": True,
        }

        if temperature is not None:
            payload["temperature"] = temperature
        if top_p is not None:
            payload["top_p"] = top_p
        if top_k is not None:
            payload["top_k"] = top_k
        if stop_sequences is not None:
            payload["stop"] = stop_sequences

        payload.update(kwargs)

        async with self._async_client.stream("POST", "/chat/completions", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        if chunk["choices"] and chunk["choices"][0].get("delta"):
                            delta = chunk["choices"][0]["delta"]
                            if delta.get("content"):
                                yield {
                                    "type": "content_block_delta",
                                    "index": 0,
                                    "delta": {"type": "text_delta", "text": delta["content"]},
                                }
                    except json.JSONDecodeError:
                        continue

    def count_tokens(
        self,
        model: str,
        messages: list[Message],
        *,
        system: str | None = None,
        tools: list[Tool] | None = None,
        **kwargs: Any,
    ) -> TokenCountResponse:
        """Count tokens synchronously.

        Note: Most Code Llama endpoints don't provide token counting.
        This is a rough estimation.
        """
        openai_messages = self._convert_messages_to_openai_format(messages, system)

        # Rough estimate: ~4 chars per token
        total_chars = sum(len(str(msg.get("content", ""))) for msg in openai_messages)
        estimated_tokens = total_chars // 4

        return TokenCountResponse(input_tokens=estimated_tokens)

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
        return self.count_tokens(model, messages, system=system, tools=tools, **kwargs)

    def __del__(self) -> None:
        """Cleanup HTTP clients."""
        with contextlib.suppress(Exception):
            self._client.close()
