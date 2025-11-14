"""OpenAI provider implementation.

This provider translates between our unified interface and OpenAI's API.
"""

import json
import os
from collections.abc import AsyncIterator, Iterator
from typing import Any, cast

import openai


try:
    import tiktoken

    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    tiktoken = None

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


class OpenAIProvider(BaseProvider):
    """Provider for OpenAI's GPT models.

    This provider translates between our unified interface and OpenAI's chat completions API.
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
        """Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            base_url: Optional base URL override
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            **kwargs: Additional configuration
        """
        super().__init__(api_key, **kwargs)

        # Get API key from environment if not provided
        if not api_key:
            api_key = os.environ.get("OPENAI_API_KEY", "")

        # Initialize sync client
        self._client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )

        # Initialize async client
        self._async_client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )

    @property
    def name(self) -> str:
        """Provider name."""
        return "openai"

    def _convert_messages_to_openai(
        self, messages: list[Message], system: str | None = None
    ) -> list[dict[str, Any]]:
        """Convert our message format to OpenAI format.

        Args:
            messages: Our message format
            system: System prompt to prepend

        Returns:
            OpenAI message format
        """
        openai_messages: list[dict[str, Any]] = []

        # Add system message if provided
        if system:
            openai_messages.append({"role": "system", "content": system})

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if isinstance(content, str):
                openai_messages.append({"role": role, "content": content})
            elif isinstance(content, list):
                # Handle multi-part content (images, tool results, etc.)
                openai_content: list[dict[str, Any]] = []
                for block in content:
                    if block["type"] == "text":
                        openai_content.append({"type": "text", "text": block["text"]})
                    elif block["type"] == "image":
                        source = block["source"]
                        if source["type"] == "base64":
                            image_url = f"data:{source['media_type']};base64,{source['data']}"
                        else:
                            image_url = source["url"]
                        openai_content.append(
                            {"type": "image_url", "image_url": {"url": image_url}}
                        )
                    elif block["type"] == "tool_use":
                        # OpenAI uses function calls in assistant messages
                        openai_messages.append(
                            {
                                "role": "assistant",
                                "content": None,
                                "tool_calls": [
                                    {
                                        "id": block["id"],
                                        "type": "function",
                                        "function": {
                                            "name": block["name"],
                                            "arguments": json.dumps(block["input"]),
                                        },
                                    }
                                ],
                            }
                        )
                        continue
                    elif block["type"] == "tool_result":
                        # OpenAI uses tool messages for results
                        openai_messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": block["tool_use_id"],
                                "content": (
                                    block["content"]
                                    if isinstance(block.get("content"), str)
                                    else json.dumps(block.get("content"))
                                ),
                            }
                        )
                        continue

                if openai_content:
                    openai_messages.append({"role": role, "content": openai_content})

        return openai_messages

    def _convert_tools_to_openai(self, tools: list[Tool]) -> list[dict[str, Any]]:
        """Convert our tool format to OpenAI format.

        Args:
            tools: Our tool format

        Returns:
            OpenAI tool format
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"],
                },
            }
            for tool in tools
        ]

    def _convert_response(self, response: Any, model: str) -> MessageResponse:
        """Convert OpenAI response to our format.

        Args:
            response: OpenAI ChatCompletion object
            model: Model name

        Returns:
            MessageResponse in our format
        """
        choice = response.choices[0]
        message = choice.message

        # Convert content blocks
        content_blocks: list[ResponseContentBlock] = []

        # Handle text content
        if message.content:
            content_blocks.append(TextBlock(type="text", text=message.content))

        # Handle tool calls
        if hasattr(message, "tool_calls") and message.tool_calls:
            for tool_call in message.tool_calls:
                content_blocks.append(
                    ToolUseBlock(
                        type="tool_use",
                        id=tool_call.id,
                        name=tool_call.function.name,
                        input=json.loads(tool_call.function.arguments),
                    )
                )

        # Map finish reason to stop reason
        stop_reason_map = {
            "stop": "end_turn",
            "length": "max_tokens",
            "tool_calls": "tool_use",
            "content_filter": "content_filter",
        }
        stop_reason = stop_reason_map.get(choice.finish_reason, "end_turn")

        return MessageResponse(
            id=response.id,
            type="message",
            role="assistant",
            content=content_blocks,
            model=model,
            stop_reason=cast("StopReason | None", stop_reason),
            stop_sequence=None,
            usage=Usage(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
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
        # Convert messages
        openai_messages = self._convert_messages_to_openai(messages, system)

        # Build request parameters
        params: dict[str, Any] = {
            "model": model,
            "messages": openai_messages,
            "max_tokens": max_tokens,
        }

        if temperature is not None:
            params["temperature"] = temperature
        if top_p is not None:
            params["top_p"] = top_p
        # OpenAI doesn't support top_k
        if stop_sequences is not None:
            params["stop"] = stop_sequences

        # Handle tools
        if tools is not None:
            params["tools"] = self._convert_tools_to_openai(tools)
            if tool_choice is not None:
                # Convert tool choice
                if tool_choice.get("type") == "auto":
                    params["tool_choice"] = "auto"
                elif tool_choice.get("type") == "any":
                    params["tool_choice"] = "required"
                elif tool_choice.get("type") == "tool":
                    params["tool_choice"] = {
                        "type": "function",
                        "function": {"name": tool_choice["name"]},
                    }

        params.update(kwargs)

        response = self._client.chat.completions.create(**params)
        return self._convert_response(response, model)

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
        # Convert messages
        openai_messages = self._convert_messages_to_openai(messages, system)

        # Build request parameters
        params: dict[str, Any] = {
            "model": model,
            "messages": openai_messages,
            "max_tokens": max_tokens,
        }

        if temperature is not None:
            params["temperature"] = temperature
        if top_p is not None:
            params["top_p"] = top_p
        if stop_sequences is not None:
            params["stop"] = stop_sequences

        # Handle tools
        if tools is not None:
            params["tools"] = self._convert_tools_to_openai(tools)
            if tool_choice is not None:
                if tool_choice.get("type") == "auto":
                    params["tool_choice"] = "auto"
                elif tool_choice.get("type") == "any":
                    params["tool_choice"] = "required"
                elif tool_choice.get("type") == "tool":
                    params["tool_choice"] = {
                        "type": "function",
                        "function": {"name": tool_choice["name"]},
                    }

        params.update(kwargs)

        response = await self._async_client.chat.completions.create(**params)
        return self._convert_response(response, model)

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
        openai_messages = self._convert_messages_to_openai(messages, system)

        params: dict[str, Any] = {
            "model": model,
            "messages": openai_messages,
            "max_tokens": max_tokens,
            "stream": True,
        }

        if temperature is not None:
            params["temperature"] = temperature
        if top_p is not None:
            params["top_p"] = top_p
        if stop_sequences is not None:
            params["stop"] = stop_sequences

        if tools is not None:
            params["tools"] = self._convert_tools_to_openai(tools)
            if tool_choice is not None:
                if tool_choice.get("type") == "auto":
                    params["tool_choice"] = "auto"
                elif tool_choice.get("type") == "any":
                    params["tool_choice"] = "required"

        params.update(kwargs)

        stream = self._client.chat.completions.create(**params)

        # Convert OpenAI stream events to our format
        for chunk in stream:
            yield from self._convert_stream_chunk(chunk)

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
        openai_messages = self._convert_messages_to_openai(messages, system)

        params: dict[str, Any] = {
            "model": model,
            "messages": openai_messages,
            "max_tokens": max_tokens,
            "stream": True,
        }

        if temperature is not None:
            params["temperature"] = temperature
        if top_p is not None:
            params["top_p"] = top_p
        if stop_sequences is not None:
            params["stop"] = stop_sequences

        if tools is not None:
            params["tools"] = self._convert_tools_to_openai(tools)
            if tool_choice is not None:
                if tool_choice.get("type") == "auto":
                    params["tool_choice"] = "auto"
                elif tool_choice.get("type") == "any":
                    params["tool_choice"] = "required"

        params.update(kwargs)

        stream = await self._async_client.chat.completions.create(**params)

        # Convert OpenAI stream events to our format
        async for chunk in stream:
            for event in self._convert_stream_chunk(chunk):
                yield event

    def _convert_stream_chunk(self, chunk: Any) -> Iterator[dict[str, Any]]:
        """Convert OpenAI stream chunk to our event format.

        Args:
            chunk: OpenAI chunk

        Yields:
            Events in our format
        """
        if not chunk.choices:
            return

        choice = chunk.choices[0]
        delta = choice.delta

        # Handle text delta
        if delta.content:
            yield {
                "type": "content_block_delta",
                "index": 0,
                "delta": {"type": "text_delta", "text": delta.content},
            }

        # Handle tool calls
        if hasattr(delta, "tool_calls") and delta.tool_calls:
            for tool_call in delta.tool_calls:
                if tool_call.function.arguments:
                    yield {
                        "type": "content_block_delta",
                        "index": tool_call.index or 0,
                        "delta": {
                            "type": "input_json_delta",
                            "partial_json": tool_call.function.arguments,
                        },
                    }

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

        Note: OpenAI doesn't provide a direct token counting API.
        This is an estimation using tiktoken library if available.
        """
        if not TIKTOKEN_AVAILABLE or tiktoken is None:
            # If tiktoken not available, return estimate
            # Rough estimate: ~4 chars per token
            openai_messages = self._convert_messages_to_openai(messages, system)
            total_chars = sum(len(str(msg.get("content", ""))) for msg in openai_messages)
            estimated_tokens = total_chars // 4
            return TokenCountResponse(input_tokens=estimated_tokens)

        # Use tiktoken for accurate counting
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")

        openai_messages = self._convert_messages_to_openai(messages, system)
        num_tokens = 0

        for message in openai_messages:
            num_tokens += 4  # Every message has overhead
            for _key, value in message.items():
                if isinstance(value, str):
                    num_tokens += len(encoding.encode(value))

        num_tokens += 2  # Reply priming

        return TokenCountResponse(input_tokens=num_tokens)

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
        # Token counting is synchronous, so we just call the sync version
        return self.count_tokens(model, messages, system=system, tools=tools, **kwargs)
