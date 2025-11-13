"""Mistral AI provider implementation.

This provider translates between our unified interface and Mistral's API.
"""

import json
import os
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional

from mistralai import Mistral

from .._models import MessageResponse, TextBlock, TokenCountResponse, ToolUseBlock, Usage
from .._types import Message, Tool
from ._base import BaseProvider


class MistralProvider(BaseProvider):
    """Provider for Mistral AI models.

    This provider translates between our unified interface and Mistral's API.
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: int = 2,
        **kwargs: Any,
    ) -> None:
        """Initialize Mistral provider.

        Args:
            api_key: Mistral API key
            base_url: Optional base URL override
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            **kwargs: Additional configuration
        """
        super().__init__(api_key, **kwargs)

        # Get API key from environment if not provided
        if not api_key:
            api_key = os.environ.get("MISTRAL_API_KEY", "")

        # Initialize client
        self._client = Mistral(api_key=api_key)
        self.timeout = timeout
        self.max_retries = max_retries

    @property
    def name(self) -> str:
        """Provider name."""
        return "mistral"

    def _convert_messages_to_mistral(
        self, messages: List[Message], system: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Convert our message format to Mistral format.

        Args:
            messages: Our message format
            system: System prompt to prepend

        Returns:
            Mistral message format
        """
        mistral_messages = []

        # Add system message if provided
        if system:
            mistral_messages.append({"role": "system", "content": system})

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if isinstance(content, str):
                mistral_messages.append({"role": role, "content": content})
            elif isinstance(content, list):
                # Handle multi-part content
                text_parts = []
                for block in content:
                    if block["type"] == "text":
                        text_parts.append(block["text"])
                    elif block["type"] == "tool_result":
                        # Mistral handles tool results as assistant messages
                        mistral_messages.append(
                            {"role": "tool", "content": str(block.get("content", ""))}
                        )

                if text_parts:
                    mistral_messages.append({"role": role, "content": "\n".join(text_parts)})

        return mistral_messages

    def _convert_tools_to_mistral(self, tools: List[Tool]) -> List[Dict[str, Any]]:
        """Convert our tool format to Mistral format.

        Args:
            tools: Our tool format

        Returns:
            Mistral tool format
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
        """Convert Mistral response to our format.

        Args:
            response: Mistral ChatCompletionResponse
            model: Model name

        Returns:
            MessageResponse in our format
        """
        choice = response.choices[0]
        message = choice.message

        # Convert content blocks
        content_blocks = []

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

        # Map finish reason
        stop_reason_map = {
            "stop": "end_turn",
            "length": "max_tokens",
            "tool_calls": "tool_use",
            "model_length": "max_tokens",
        }
        stop_reason = stop_reason_map.get(choice.finish_reason, "end_turn")

        return MessageResponse(
            id=response.id,
            type="message",
            role="assistant",
            content=content_blocks,
            model=model,
            stop_reason=stop_reason,
            stop_sequence=None,
            usage=Usage(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
            ),
        )

    def create_message(
        self,
        model: str,
        messages: List[Message],
        max_tokens: int,
        *,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
        tools: Optional[List[Tool]] = None,
        tool_choice: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> MessageResponse:
        """Create a message synchronously."""
        mistral_messages = self._convert_messages_to_mistral(messages, system)

        params: Dict[str, Any] = {
            "model": model,
            "messages": mistral_messages,
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
            params["tools"] = self._convert_tools_to_mistral(tools)
            if tool_choice is not None:
                if tool_choice.get("type") == "auto":
                    params["tool_choice"] = "auto"
                elif tool_choice.get("type") == "any":
                    params["tool_choice"] = "any"

        params.update(kwargs)

        response = self._client.chat.complete(**params)
        return self._convert_response(response, model)

    async def acreate_message(
        self,
        model: str,
        messages: List[Message],
        max_tokens: int,
        *,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
        tools: Optional[List[Tool]] = None,
        tool_choice: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> MessageResponse:
        """Create a message asynchronously."""
        mistral_messages = self._convert_messages_to_mistral(messages, system)

        params: Dict[str, Any] = {
            "model": model,
            "messages": mistral_messages,
            "max_tokens": max_tokens,
        }

        if temperature is not None:
            params["temperature"] = temperature
        if top_p is not None:
            params["top_p"] = top_p
        if stop_sequences is not None:
            params["stop"] = stop_sequences

        if tools is not None:
            params["tools"] = self._convert_tools_to_mistral(tools)
            if tool_choice is not None:
                if tool_choice.get("type") == "auto":
                    params["tool_choice"] = "auto"
                elif tool_choice.get("type") == "any":
                    params["tool_choice"] = "any"

        params.update(kwargs)

        response = await self._client.chat.complete_async(**params)
        return self._convert_response(response, model)

    def stream_message(
        self,
        model: str,
        messages: List[Message],
        max_tokens: int,
        *,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
        tools: Optional[List[Tool]] = None,
        tool_choice: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """Stream a message synchronously."""
        mistral_messages = self._convert_messages_to_mistral(messages, system)

        params: Dict[str, Any] = {
            "model": model,
            "messages": mistral_messages,
            "max_tokens": max_tokens,
        }

        if temperature is not None:
            params["temperature"] = temperature
        if top_p is not None:
            params["top_p"] = top_p
        if stop_sequences is not None:
            params["stop"] = stop_sequences

        if tools is not None:
            params["tools"] = self._convert_tools_to_mistral(tools)

        params.update(kwargs)

        stream = self._client.chat.stream(**params)

        for chunk in stream:
            if chunk.data.choices:
                delta = chunk.data.choices[0].delta
                if delta.content:
                    yield {
                        "type": "content_block_delta",
                        "index": 0,
                        "delta": {"type": "text_delta", "text": delta.content},
                    }

    async def astream_message(
        self,
        model: str,
        messages: List[Message],
        max_tokens: int,
        *,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
        tools: Optional[List[Tool]] = None,
        tool_choice: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream a message asynchronously."""
        mistral_messages = self._convert_messages_to_mistral(messages, system)

        params: Dict[str, Any] = {
            "model": model,
            "messages": mistral_messages,
            "max_tokens": max_tokens,
        }

        if temperature is not None:
            params["temperature"] = temperature
        if top_p is not None:
            params["top_p"] = top_p
        if stop_sequences is not None:
            params["stop"] = stop_sequences

        if tools is not None:
            params["tools"] = self._convert_tools_to_mistral(tools)

        params.update(kwargs)

        stream = await self._client.chat.stream_async(**params)

        async for chunk in stream:
            if chunk.data.choices:
                delta = chunk.data.choices[0].delta
                if delta.content:
                    yield {
                        "type": "content_block_delta",
                        "index": 0,
                        "delta": {"type": "text_delta", "text": delta.content},
                    }

    def count_tokens(
        self,
        model: str,
        messages: List[Message],
        *,
        system: Optional[str] = None,
        tools: Optional[List[Tool]] = None,
        **kwargs: Any,
    ) -> TokenCountResponse:
        """Count tokens synchronously.

        Note: Mistral doesn't provide a direct token counting API.
        This is a rough estimation.
        """
        mistral_messages = self._convert_messages_to_mistral(messages, system)

        # Rough estimate: ~4 chars per token
        total_chars = sum(len(str(msg.get("content", ""))) for msg in mistral_messages)
        estimated_tokens = total_chars // 4

        return TokenCountResponse(input_tokens=estimated_tokens)

    async def acount_tokens(
        self,
        model: str,
        messages: List[Message],
        *,
        system: Optional[str] = None,
        tools: Optional[List[Tool]] = None,
        **kwargs: Any,
    ) -> TokenCountResponse:
        """Count tokens asynchronously."""
        return self.count_tokens(model, messages, system=system, tools=tools, **kwargs)
