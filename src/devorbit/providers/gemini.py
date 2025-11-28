"""Google Gemini provider implementation.

This provider translates between our unified interface and Google's Gemini API.
"""

import json
import os
import random
from collections.abc import AsyncIterator, Iterator
from typing import Any, cast

import google.generativeai as genai

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
                parts = self._convert_content_blocks(content)
                if parts:
                    gemini_messages.append({"role": role, "parts": parts})

        return system, gemini_messages

    def _convert_content_blocks(self, content: list[Any]) -> list[dict[str, Any]]:
        """Convert content blocks to Gemini parts format.

        Handles both dict blocks and dataclass blocks (TextBlock, ToolUseBlock).
        """
        parts: list[dict[str, Any]] = []
        for block in content:
            part = self._convert_single_block(block)
            if part:
                parts.append(part)
        return parts

    def _convert_single_block(self, block: Any) -> dict[str, Any] | None:
        """Convert a single content block to Gemini part format."""
        # Get block type (works for both dict and dataclass)
        block_type = block.get("type") if isinstance(block, dict) else getattr(block, "type", None)

        if block_type == "text":
            text = block.get("text", "") if isinstance(block, dict) else getattr(block, "text", "")
            return {"text": text}

        if block_type == "image":
            return self._convert_image_block(block)

        if block_type == "tool_use":
            return self._convert_tool_use_block(block)

        if block_type == "tool_result":
            return self._convert_tool_result_block(block)

        return None

    def _convert_image_block(self, block: Any) -> dict[str, Any] | None:
        """Convert image block to Gemini inline_data format."""
        source = (
            block.get("source", {}) if isinstance(block, dict) else getattr(block, "source", {})
        )
        source_type = (
            source.get("type") if isinstance(source, dict) else getattr(source, "type", None)
        )

        if source_type != "base64":
            return None

        media_type = (
            source.get("media_type", "")
            if isinstance(source, dict)
            else getattr(source, "media_type", "")
        )
        data = source.get("data", "") if isinstance(source, dict) else getattr(source, "data", "")
        return {"inline_data": {"mime_type": media_type, "data": data}}

    def _convert_tool_use_block(self, block: Any) -> dict[str, Any]:
        """Convert tool use block to Gemini function_call format."""
        tool_name = block.get("name", "") if isinstance(block, dict) else getattr(block, "name", "")
        tool_input = (
            block.get("input", {}) if isinstance(block, dict) else getattr(block, "input", {})
        )
        return {"function_call": {"name": tool_name, "args": tool_input or {}}}

    def _convert_tool_result_block(self, block: Any) -> dict[str, Any]:
        """Convert tool result block to Gemini function_response format."""
        tool_content = (
            block.get("content", "") if isinstance(block, dict) else getattr(block, "content", "")
        )
        tool_use_id = (
            block.get("tool_use_id", "")
            if isinstance(block, dict)
            else getattr(block, "tool_use_id", "")
        )
        # Extract tool name from ID (format: "tool_name-1234")
        name = tool_use_id.split("-")[0] if "-" in str(tool_use_id) else str(tool_use_id)
        return {"function_response": {"name": name, "response": {"result": str(tool_content)}}}

    def _convert_tools_to_gemini(self, tools: list[Tool]) -> list[dict[str, Any]]:
        """Convert our tool format to Gemini format.

        Args:
            tools: Our tool format

        Returns:
            Gemini tool format (function declarations)
        """
        gemini_tools: list[dict[str, Any]] = []
        for tool in tools:
            # Convert JSON Schema to Gemini Schema format
            input_schema = tool.get("input_schema", {})
            gemini_params = self._convert_schema_to_gemini(input_schema)

            gemini_tools.append(
                {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": gemini_params,
                }
            )
        return gemini_tools

    def _convert_schema_to_gemini(self, schema: dict[str, Any]) -> dict[str, Any]:
        """Convert JSON Schema to Gemini Schema format.

        Gemini uses a different schema format than standard JSON Schema.
        This converts between the two formats.

        Args:
            schema: JSON Schema format

        Returns:
            Gemini-compatible schema
        """
        if not schema:
            return {}

        gemini_schema: dict[str, Any] = {}

        # Map JSON Schema types to Gemini types
        type_mapping = {
            "string": "STRING",
            "number": "NUMBER",
            "integer": "INTEGER",
            "boolean": "BOOLEAN",
            "array": "ARRAY",
            "object": "OBJECT",
        }

        # Handle the type field
        json_type = schema.get("type", "object")
        gemini_schema["type"] = type_mapping.get(json_type, "STRING")

        # Handle description
        if "description" in schema:
            gemini_schema["description"] = schema["description"]

        # Handle properties (for object types)
        if "properties" in schema:
            gemini_schema["properties"] = {}
            for prop_name, prop_schema in schema["properties"].items():
                gemini_schema["properties"][prop_name] = self._convert_schema_to_gemini(prop_schema)

        # Handle required fields
        if "required" in schema:
            gemini_schema["required"] = schema["required"]

        # Handle array items
        if "items" in schema:
            gemini_schema["items"] = self._convert_schema_to_gemini(schema["items"])

        # Handle enum
        if "enum" in schema:
            gemini_schema["enum"] = schema["enum"]

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

        # Extract text content (safely handle blocked responses)
        try:
            if response.text:
                content_blocks.append(TextBlock(type="text", text=response.text))
        except ValueError:
            # Response was blocked by safety filters, add empty text block
            content_blocks.append(
                TextBlock(type="text", text="[Content blocked by safety filters]")
            )

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
        stop_reason = finish_reason_map.get(str(response.candidates[0].finish_reason), "end_turn")

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

        # Emit message_start event (Claude SDK compatible)
        yield {
            "type": "message_start",
            "message": {
                "id": f"gemini-{random.randint(100000, 999999)}",
                "type": "message",
                "role": "assistant",
                "content": [],
                "model": model,
                "stop_reason": None,
                "stop_sequence": None,
                "usage": {"input_tokens": 0, "output_tokens": 0},
            },
        }

        # Emit content_block_start event
        yield {
            "type": "content_block_start",
            "index": 0,
            "content_block": {"type": "text", "text": ""},
        }

        response = gemini_model.generate_content(
            gemini_messages, generation_config=generation_config, stream=True
        )

        accumulated_text = ""
        content_block_index = 0
        has_text_block = True  # We already emitted content_block_start for text

        for chunk in response:
            # Process each part in the chunk
            for part in chunk.parts:
                # Handle text content
                if hasattr(part, "text") and part.text:
                    accumulated_text += part.text
                    yield {
                        "type": "content_block_delta",
                        "index": 0,
                        "delta": {"type": "text_delta", "text": part.text},
                    }

                # Handle function calls (tool use)
                elif hasattr(part, "function_call") and part.function_call:
                    fc = part.function_call
                    tool_id = f"{fc.name}-{random.randint(1000, 9999)}"

                    # Close text block if we had one
                    if has_text_block:
                        yield {"type": "content_block_stop", "index": content_block_index}
                        content_block_index += 1
                        has_text_block = False

                    # Emit tool use block start
                    yield {
                        "type": "content_block_start",
                        "index": content_block_index,
                        "content_block": {
                            "type": "tool_use",
                            "id": tool_id,
                            "name": fc.name,
                            "input": {},
                        },
                    }

                    # Emit tool input as JSON delta
                    input_json = json.dumps(dict(fc.args))
                    yield {
                        "type": "content_block_delta",
                        "index": content_block_index,
                        "delta": {"type": "input_json_delta", "partial_json": input_json},
                    }

                    # Close tool use block
                    yield {"type": "content_block_stop", "index": content_block_index}
                    content_block_index += 1

        # Close text block if still open
        if has_text_block:
            yield {"type": "content_block_stop", "index": 0}

        # Emit message_delta event with stop reason
        yield {
            "type": "message_delta",
            "delta": {"stop_reason": "end_turn", "stop_sequence": None},
            "usage": {"output_tokens": len(accumulated_text.split())},
        }

        # Emit message_stop event
        yield {"type": "message_stop"}

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

        # Emit message_start event (Claude SDK compatible)
        yield {
            "type": "message_start",
            "message": {
                "id": f"gemini-{random.randint(100000, 999999)}",
                "type": "message",
                "role": "assistant",
                "content": [],
                "model": model,
                "stop_reason": None,
                "stop_sequence": None,
                "usage": {"input_tokens": 0, "output_tokens": 0},
            },
        }

        # Emit content_block_start event
        yield {
            "type": "content_block_start",
            "index": 0,
            "content_block": {"type": "text", "text": ""},
        }

        response = await gemini_model.generate_content_async(
            gemini_messages, generation_config=generation_config, stream=True
        )

        accumulated_text = ""
        content_block_index = 0
        has_text_block = True  # We already emitted content_block_start for text

        async for chunk in response:
            # Process each part in the chunk
            for part in chunk.parts:
                # Handle text content
                if hasattr(part, "text") and part.text:
                    accumulated_text += part.text
                    yield {
                        "type": "content_block_delta",
                        "index": 0,
                        "delta": {"type": "text_delta", "text": part.text},
                    }

                # Handle function calls (tool use)
                elif hasattr(part, "function_call") and part.function_call:
                    fc = part.function_call
                    tool_id = f"{fc.name}-{random.randint(1000, 9999)}"

                    # Close text block if we had one
                    if has_text_block:
                        yield {"type": "content_block_stop", "index": content_block_index}
                        content_block_index += 1
                        has_text_block = False

                    # Emit tool use block start
                    yield {
                        "type": "content_block_start",
                        "index": content_block_index,
                        "content_block": {
                            "type": "tool_use",
                            "id": tool_id,
                            "name": fc.name,
                            "input": {},
                        },
                    }

                    # Emit tool input as JSON delta
                    input_json = json.dumps(dict(fc.args))
                    yield {
                        "type": "content_block_delta",
                        "index": content_block_index,
                        "delta": {"type": "input_json_delta", "partial_json": input_json},
                    }

                    # Close tool use block
                    yield {"type": "content_block_stop", "index": content_block_index}
                    content_block_index += 1

        # Close text block if still open
        if has_text_block:
            yield {"type": "content_block_stop", "index": 0}

        # Emit message_delta event with stop reason
        yield {
            "type": "message_delta",
            "delta": {"stop_reason": "end_turn", "stop_sequence": None},
            "usage": {"output_tokens": len(accumulated_text.split())},
        }

        # Emit message_stop event
        yield {"type": "message_stop"}

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
