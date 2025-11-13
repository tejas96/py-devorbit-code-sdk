"""Google Gemini provider implementation.

This provider translates between our unified interface and Google's Gemini API.
"""

import json
import os
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional

import google.generativeai as genai

from .._models import MessageResponse, TextBlock, TokenCountResponse, ToolUseBlock, Usage
from .._types import Message, Tool
from ._base import BaseProvider


class GeminiProvider(BaseProvider):
    """Provider for Google's Gemini models.

    This provider translates between our unified interface and Google's Gemini API.
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
        """Initialize Gemini provider.

        Args:
            api_key: Google AI API key
            base_url: Optional base URL override (not used for Gemini)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            **kwargs: Additional configuration
        """
        super().__init__(api_key, **kwargs)

        # Get API key from environment if not provided
        if not api_key:
            api_key = os.environ.get("GOOGLE_API_KEY", "")

        # Configure the SDK
        genai.configure(api_key=api_key)

        self.timeout = timeout
        self.max_retries = max_retries

    @property
    def name(self) -> str:
        """Provider name."""
        return "gemini"

    def _convert_messages_to_gemini(
        self, messages: List[Message], system: Optional[str] = None
    ) -> tuple[Optional[str], List[Dict[str, Any]]]:
        """Convert our message format to Gemini format.

        Args:
            messages: Our message format
            system: System prompt

        Returns:
            Tuple of (system_instruction, gemini_messages)
        """
        gemini_messages = []

        for msg in messages:
            role = "model" if msg["role"] == "assistant" else "user"
            content = msg["content"]

            if isinstance(content, str):
                gemini_messages.append({"role": role, "parts": [{"text": content}]})
            elif isinstance(content, list):
                parts = []
                for block in content:
                    if block["type"] == "text":
                        parts.append({"text": block["text"]})
                    elif block["type"] == "image":
                        source = block["source"]
                        if source["type"] == "base64":
                            import base64

                            image_data = base64.b64decode(source["data"])
                            parts.append(
                                {
                                    "inline_data": {
                                        "mime_type": source["media_type"],
                                        "data": source["data"],
                                    }
                                }
                            )
                    elif block["type"] == "tool_result":
                        # Gemini handles tool results differently
                        parts.append({"text": str(block.get("content", ""))})

                if parts:
                    gemini_messages.append({"role": role, "parts": parts})

        return system, gemini_messages

    def _convert_tools_to_gemini(self, tools: List[Tool]) -> List[Dict[str, Any]]:
        """Convert our tool format to Gemini format.

        Args:
            tools: Our tool format

        Returns:
            Gemini tool format
        """
        gemini_tools = []
        for tool in tools:
            gemini_tools.append(
                {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"],
                }
            )
        return gemini_tools

    def _convert_response(self, response: Any, model: str) -> MessageResponse:
        """Convert Gemini response to our format.

        Args:
            response: Gemini GenerateContentResponse
            model: Model name

        Returns:
            MessageResponse in our format
        """
        content_blocks = []

        # Extract text content
        if response.text:
            content_blocks.append(TextBlock(type="text", text=response.text))

        # Handle function calls (tool use)
        for part in response.parts:
            if hasattr(part, "function_call") and part.function_call:
                func_call = part.function_call
                content_blocks.append(
                    ToolUseBlock(
                        type="tool_use",
                        id=func_call.name,  # Gemini doesn't have separate IDs
                        name=func_call.name,
                        input=dict(func_call.args),
                    )
                )

        # Map finish reason
        finish_reason_map = {
            "STOP": "end_turn",
            "MAX_TOKENS": "max_tokens",
            "SAFETY": "content_filter",
            "RECITATION": "content_filter",
        }
        stop_reason = finish_reason_map.get(
            str(response.candidates[0].finish_reason), "end_turn"
        )

        # Estimate token usage (Gemini provides token count)
        usage = Usage(
            input_tokens=response.usage_metadata.prompt_token_count
            if hasattr(response, "usage_metadata")
            else 0,
            output_tokens=response.usage_metadata.candidates_token_count
            if hasattr(response, "usage_metadata")
            else 0,
        )

        return MessageResponse(
            id=f"gemini-{hash(response.text)}",  # Gemini doesn't provide IDs
            type="message",
            role="assistant",
            content=content_blocks,
            model=model,
            stop_reason=stop_reason,
            stop_sequence=None,
            usage=usage,
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
        system_instruction, gemini_messages = self._convert_messages_to_gemini(
            messages, system
        )

        # Create generation config
        generation_config = {"max_output_tokens": max_tokens}

        if temperature is not None:
            generation_config["temperature"] = temperature
        if top_p is not None:
            generation_config["top_p"] = top_p
        if top_k is not None:
            generation_config["top_k"] = top_k
        if stop_sequences is not None:
            generation_config["stop_sequences"] = stop_sequences

        # Initialize model
        gemini_model = genai.GenerativeModel(
            model_name=model, system_instruction=system_instruction
        )

        # Handle tools
        if tools:
            gemini_tools = self._convert_tools_to_gemini(tools)
            gemini_model = genai.GenerativeModel(
                model_name=model,
                system_instruction=system_instruction,
                tools=gemini_tools,
            )

        # Generate content
        response = gemini_model.generate_content(
            gemini_messages, generation_config=generation_config
        )

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
        system_instruction, gemini_messages = self._convert_messages_to_gemini(
            messages, system
        )

        # Create generation config
        generation_config = {"max_output_tokens": max_tokens}

        if temperature is not None:
            generation_config["temperature"] = temperature
        if top_p is not None:
            generation_config["top_p"] = top_p
        if top_k is not None:
            generation_config["top_k"] = top_k
        if stop_sequences is not None:
            generation_config["stop_sequences"] = stop_sequences

        # Initialize model
        gemini_model = genai.GenerativeModel(
            model_name=model, system_instruction=system_instruction
        )

        # Handle tools
        if tools:
            gemini_tools = self._convert_tools_to_gemini(tools)
            gemini_model = genai.GenerativeModel(
                model_name=model,
                system_instruction=system_instruction,
                tools=gemini_tools,
            )

        # Generate content asynchronously
        response = await gemini_model.generate_content_async(
            gemini_messages, generation_config=generation_config
        )

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
        system_instruction, gemini_messages = self._convert_messages_to_gemini(
            messages, system
        )

        generation_config = {"max_output_tokens": max_tokens}

        if temperature is not None:
            generation_config["temperature"] = temperature
        if top_p is not None:
            generation_config["top_p"] = top_p
        if top_k is not None:
            generation_config["top_k"] = top_k
        if stop_sequences is not None:
            generation_config["stop_sequences"] = stop_sequences

        gemini_model = genai.GenerativeModel(
            model_name=model, system_instruction=system_instruction
        )

        if tools:
            gemini_tools = self._convert_tools_to_gemini(tools)
            gemini_model = genai.GenerativeModel(
                model_name=model,
                system_instruction=system_instruction,
                tools=gemini_tools,
            )

        response = gemini_model.generate_content(
            gemini_messages, generation_config=generation_config, stream=True
        )

        for chunk in response:
            if chunk.text:
                yield {
                    "type": "content_block_delta",
                    "index": 0,
                    "delta": {"type": "text_delta", "text": chunk.text},
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
        system_instruction, gemini_messages = self._convert_messages_to_gemini(
            messages, system
        )

        generation_config = {"max_output_tokens": max_tokens}

        if temperature is not None:
            generation_config["temperature"] = temperature
        if top_p is not None:
            generation_config["top_p"] = top_p
        if top_k is not None:
            generation_config["top_k"] = top_k
        if stop_sequences is not None:
            generation_config["stop_sequences"] = stop_sequences

        gemini_model = genai.GenerativeModel(
            model_name=model, system_instruction=system_instruction
        )

        if tools:
            gemini_tools = self._convert_tools_to_gemini(tools)
            gemini_model = genai.GenerativeModel(
                model_name=model,
                system_instruction=system_instruction,
                tools=gemini_tools,
            )

        response = await gemini_model.generate_content_async(
            gemini_messages, generation_config=generation_config, stream=True
        )

        async for chunk in response:
            if chunk.text:
                yield {
                    "type": "content_block_delta",
                    "index": 0,
                    "delta": {"type": "text_delta", "text": chunk.text},
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
        """Count tokens synchronously."""
        system_instruction, gemini_messages = self._convert_messages_to_gemini(
            messages, system
        )

        gemini_model = genai.GenerativeModel(
            model_name=model, system_instruction=system_instruction
        )

        # Gemini provides token counting
        token_count = gemini_model.count_tokens(gemini_messages)

        return TokenCountResponse(input_tokens=token_count.total_tokens)

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
        system_instruction, gemini_messages = self._convert_messages_to_gemini(
            messages, system
        )

        gemini_model = genai.GenerativeModel(
            model_name=model, system_instruction=system_instruction
        )

        # Gemini provides token counting (async version)
        token_count = await gemini_model.count_tokens_async(gemini_messages)

        return TokenCountResponse(input_tokens=token_count.total_tokens)
