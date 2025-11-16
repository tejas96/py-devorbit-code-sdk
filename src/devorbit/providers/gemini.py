"""Google Gemini provider implementation.

This provider translates between our unified interface and Google's Gemini API.
"""

import os
import random
from collections.abc import AsyncIterator, Iterator
from typing import Any, cast

import google.generativeai as genai

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


class GeminiProvider(BaseProvider):
    """Provider for Google's Gemini models.

    This provider translates between our unified interface and Google's Gemini API.
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
        self, messages: list[Message], system: str | None = None
    ) -> tuple[str | None, list[dict[str, Any]]]:
        """Convert our message format to Gemini format.

        Args:
            messages: Our message format
            system: System prompt

        Returns:
            Tuple of (system_instruction, gemini_messages)
        """
        gemini_messages: list[dict[str, Any]] = []

        for msg in messages:
            role = "model" if msg["role"] == "assistant" else "user"
            content = msg["content"]

            if isinstance(content, str):
                gemini_messages.append({"role": role, "parts": [{"text": content}]})
            elif isinstance(content, list):
                parts: list[dict[str, Any]] = []
                for block in content:
                    if block["type"] == "text":
                        parts.append({"text": block["text"]})
                    elif block["type"] == "image":
                        source = block["source"]
                        if source["type"] == "base64":
                            # No need to decode - Gemini accepts base64 directly
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

    def _convert_tools_to_gemini(self, tools: list[Tool]) -> list[dict[str, Any]]:
        """Convert our tool format to Gemini format.

        Args:
            tools: Our tool format

        Returns:
            Gemini tool format
        """
        gemini_tools: list[dict[str, Any]] = []
        for tool in tools:
            # Convert JSON Schema to Gemini's format
            # Gemini uses uppercase type names (STRING, INTEGER, etc.)
            input_schema = self._convert_json_schema_to_gemini(tool["input_schema"])

            gemini_tools.append(
                {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": input_schema,
                }
            )
        return gemini_tools

    def _convert_json_schema_to_gemini(self, schema: dict[str, Any]) -> dict[str, Any]:
        """Convert JSON Schema format to Gemini's schema format.

        Args:
            schema: JSON Schema format

        Returns:
            Gemini schema format
        """
        gemini_schema: dict[str, Any] = {}

        # Map JSON Schema types to Gemini types
        type_map = {
            "string": "STRING",
            "integer": "INTEGER",
            "number": "NUMBER",
            "boolean": "BOOLEAN",
            "array": "ARRAY",
            "object": "OBJECT",
        }

        # Convert properties
        if "properties" in schema:
            gemini_properties = {}
            for prop_name, prop_schema in schema["properties"].items():
                gemini_prop: dict[str, Any] = {}

                # Convert type
                if "type" in prop_schema:
                    gemini_prop["type"] = type_map.get(prop_schema["type"], "STRING")

                # Add description if present
                if "description" in prop_schema:
                    gemini_prop["description"] = prop_schema["description"]

                # Handle nested properties for objects
                if prop_schema.get("type") == "object" and "properties" in prop_schema:
                    nested = self._convert_json_schema_to_gemini(prop_schema)
                    if "properties" in nested:
                        gemini_prop["properties"] = nested["properties"]

                # Handle array items
                if prop_schema.get("type") == "array" and "items" in prop_schema:
                    items_schema = prop_schema["items"]
                    if "type" in items_schema:
                        gemini_prop["items"] = {
                            "type": type_map.get(items_schema["type"], "STRING")
                        }

                gemini_properties[prop_name] = gemini_prop

            gemini_schema["properties"] = gemini_properties

        # Convert required fields
        if "required" in schema:
            gemini_schema["required"] = schema["required"]

        # Set type to OBJECT for root schema
        gemini_schema["type"] = "OBJECT"

        return gemini_schema

    def _convert_response(self, response: Any, model: str) -> MessageResponse:
        """Convert Gemini response to our format.

        Args:
            response: Gemini GenerateContentResponse
            model: Model name

        Returns:
            MessageResponse in our format
        """
        content_blocks: list[ResponseContentBlock] = []
        has_function_call = False

        # First, check for function calls and text in parts
        for part in response.parts:
            # Handle function calls (tool use)
            if hasattr(part, "function_call") and part.function_call:
                has_function_call = True
                func_call = part.function_call
                content_blocks.append(
                    ToolUseBlock(
                        type="tool_use",
                        id=f"{func_call.name}-{random.randint(1000, 9999)}",
                        name=func_call.name,
                        input=dict(func_call.args),
                    )
                )
            # Handle text parts
            elif hasattr(part, "text") and part.text:
                content_blocks.append(TextBlock(type="text", text=part.text))

        # If no content blocks were added, check if response was blocked by safety
        if not content_blocks:
            # Check finish reason for safety blocks
            finish_reason_name = str(response.candidates[0].finish_reason)
            if finish_reason_name in ("SAFETY", "RECITATION"):
                content_blocks.append(
                    TextBlock(type="text", text="[Content blocked by safety filters]")
                )
            else:
                # Empty response
                content_blocks.append(TextBlock(type="text", text=""))

        # Map finish reason
        finish_reason_map = {
            "STOP": "end_turn",
            "MAX_TOKENS": "max_tokens",
            "SAFETY": "content_filter",
            "RECITATION": "content_filter",
        }

        # If we have a function call, set stop_reason to tool_use
        if has_function_call:
            stop_reason = "tool_use"
        else:
            stop_reason = finish_reason_map.get(
                str(response.candidates[0].finish_reason), "end_turn"
            )

        # Estimate token usage (Gemini provides token count)
        usage = Usage(
            input_tokens=(
                response.usage_metadata.prompt_token_count
                if hasattr(response, "usage_metadata")
                else 0
            ),
            output_tokens=(
                response.usage_metadata.candidates_token_count
                if hasattr(response, "usage_metadata")
                else 0
            ),
        )

        # Generate ID safely (handle blocked responses)
        try:
            response_id = f"gemini-{hash(response.text)}"
        except (ValueError, AttributeError):
            response_id = f"gemini-{random.randint(100000, 999999)}"

        return MessageResponse(
            id=response_id,  # Gemini doesn't provide IDs
            type="message",
            role="assistant",
            content=content_blocks,
            model=model,
            stop_reason=cast("StopReason | None", stop_reason),
            stop_sequence=None,
            usage=usage,
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
        system_instruction, gemini_messages = self._convert_messages_to_gemini(messages, system)

        # Create generation config
        generation_config: dict[str, Any] = {"max_output_tokens": max_tokens}

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
        system_instruction, gemini_messages = self._convert_messages_to_gemini(messages, system)

        # Create generation config
        generation_config: dict[str, Any] = {"max_output_tokens": max_tokens}

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
        system_instruction, gemini_messages = self._convert_messages_to_gemini(messages, system)

        generation_config: dict[str, Any] = {"max_output_tokens": max_tokens}

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
        system_instruction, gemini_messages = self._convert_messages_to_gemini(messages, system)

        generation_config: dict[str, Any] = {"max_output_tokens": max_tokens}

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
        messages: list[Message],
        *,
        system: str | None = None,
        tools: list[Tool] | None = None,
        **kwargs: Any,
    ) -> TokenCountResponse:
        """Count tokens synchronously."""
        system_instruction, gemini_messages = self._convert_messages_to_gemini(messages, system)

        gemini_model = genai.GenerativeModel(
            model_name=model, system_instruction=system_instruction
        )

        # Gemini provides token counting
        token_count = gemini_model.count_tokens(gemini_messages)

        return TokenCountResponse(input_tokens=token_count.total_tokens)

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
        system_instruction, gemini_messages = self._convert_messages_to_gemini(messages, system)

        gemini_model = genai.GenerativeModel(
            model_name=model, system_instruction=system_instruction
        )

        # Gemini provides token counting (async version)
        token_count = await gemini_model.count_tokens_async(gemini_messages)

        return TokenCountResponse(input_tokens=token_count.total_tokens)
