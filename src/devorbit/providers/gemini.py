"""Google Gemini provider implementation.

This provider translates between our unified interface and Google's Gemini API.
"""

import os
import random
from collections.abc import AsyncIterator, Iterator
from typing import Any, cast
from dotenv import load_dotenv
load_dotenv()

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
                    # ✅ FIX: Handle both dict and Pydantic model objects
                    if isinstance(block, dict):
                        block_type = block.get("type")
                        if block_type == "text":
                            parts.append({"text": block["text"]})
                        elif block_type == "image":
                            source = block["source"]
                            if source["type"] == "base64":
                                parts.append(
                                    {
                                        "inline_data": {
                                            "mime_type": source["media_type"],
                                            "data": source["data"],
                                        }
                                    }
                                )
                        elif block_type == "tool_result":
                            parts.append({"text": str(block.get("content", ""))})
                        elif block_type == "tool_use":
                            # Skip tool_use blocks in history (already processed)
                            pass
                    else:
                        # ✅ Handle Pydantic model objects (TextBlock, ToolUseBlock, etc.)
                        from .._models import TextBlock, ToolUseBlock
                        
                        if isinstance(block, TextBlock):
                            parts.append({"text": block.text})
                        elif isinstance(block, ToolUseBlock):
                            # Skip tool_use blocks (Gemini doesn't need them in history)
                            pass
                        # Handle other block types as needed
    
                if parts:
                    gemini_messages.append({"role": role, "parts": parts})
    
        return system, gemini_messages
    

    def _convert_tools_to_gemini(self, tools: list[Tool]) -> list[Any]:
        """Convert our tool format to Gemini Tool objects.

        Args:
            tools: Our tool format (Claude SDK compatible)

        Returns:
            List of Gemini Tool objects
        """
        from google.generativeai.types import Tool as GeminiTool
        from google.generativeai.types import FunctionDeclaration

        function_declarations = []

        for tool in tools:
            input_schema = tool.get("input_schema", {})
            gemini_parameters = self._convert_schema_to_gemini(input_schema)

            function_decl = FunctionDeclaration(
                name=tool["name"],
                description=tool.get("description", ""),
                parameters=gemini_parameters,
            )

            function_declarations.append(function_decl)

        # Wrap in Tool object
        return [GeminiTool(function_declarations=function_declarations)]

    def _convert_schema_to_gemini(self, schema: dict[str, Any]) -> dict[str, Any]:
        """Convert JSON Schema to Gemini Schema format.

        Args:
            schema: JSON Schema format

        Returns:
            Gemini Schema format with uppercase types
        """
        if not schema:
            return {}

        schema_type = schema.get("type", "object").upper()

        gemini_schema: dict[str, Any] = {
            "type": schema_type,
        }

        if "properties" in schema:
            gemini_properties = {}
            for prop_name, prop_schema in schema["properties"].items():
                gemini_properties[prop_name] = self._convert_property_to_gemini(prop_schema)
            gemini_schema["properties"] = gemini_properties

        if "required" in schema:
            gemini_schema["required"] = schema["required"]

        if "description" in schema:
            gemini_schema["description"] = schema["description"]

        if "items" in schema:
            gemini_schema["items"] = self._convert_property_to_gemini(schema["items"])

        return gemini_schema

    def _convert_property_to_gemini(self, prop_schema: dict[str, Any]) -> dict[str, Any]:
        """Convert a single property schema to Gemini format.

        Args:
            prop_schema: Property schema

        Returns:
            Gemini property schema with uppercase type
        """
        if not isinstance(prop_schema, dict):
            return {"type": "STRING"}

        type_map = {
            "string": "STRING",
            "number": "NUMBER",
            "integer": "INTEGER",
            "boolean": "BOOLEAN",
            "array": "ARRAY",
            "object": "OBJECT",
        }

        prop_type = prop_schema.get("type", "string")
        gemini_type = type_map.get(prop_type.lower(), "STRING")

        gemini_prop: dict[str, Any] = {
            "type": gemini_type,
        }

        if "description" in prop_schema:
            gemini_prop["description"] = prop_schema["description"]

        if prop_type == "array" and "items" in prop_schema:
            gemini_prop["items"] = self._convert_property_to_gemini(prop_schema["items"])

        if prop_type == "object":
            if "properties" in prop_schema:
                gemini_prop["properties"] = {
                    name: self._convert_property_to_gemini(sub_schema)
                    for name, sub_schema in prop_schema["properties"].items()
                }
            if "required" in prop_schema:
                gemini_prop["required"] = prop_schema["required"]

        if "enum" in prop_schema:
            gemini_prop["enum"] = prop_schema["enum"]

        return gemini_prop

    def _convert_response(self, response: Any, model: str) -> MessageResponse:
        """Convert Gemini response to our format.

        Args:
            response: Gemini GenerateContentResponse
            model: Model name

        Returns:
            MessageResponse in our format
        """
        content_blocks: list[ResponseContentBlock] = []

        # Process all parts in response
        for part in response.parts:
            # Handle text parts
            if hasattr(part, "text") and part.text:
                content_blocks.append(TextBlock(type="text", text=part.text))
            
            # Handle function calls
            elif hasattr(part, "function_call") and part.function_call:
                func_call = part.function_call
                tool_id = f"toolu_gemini_{random.randint(100000, 999999)}"
                
                content_blocks.append(
                    ToolUseBlock(
                        type="tool_use",
                        id=tool_id,
                        name=func_call.name,
                        input=dict(func_call.args),
                    )
                )

        # If no content blocks, add empty text
        if not content_blocks:
            content_blocks.append(
                TextBlock(type="text", text="[No response content]")
            )

        # Map finish reason
        finish_reason_map = {
            "STOP": "end_turn",
            "MAX_TOKENS": "max_tokens",
            "SAFETY": "content_filter",
            "RECITATION": "content_filter",
            "OTHER": "end_turn",
        }

        try:
            finish_reason = str(response.candidates[0].finish_reason)
            stop_reason = finish_reason_map.get(finish_reason, "end_turn")
        except (AttributeError, IndexError):
            stop_reason = "end_turn"

        # Get token usage
        try:
            usage = Usage(
                input_tokens=response.usage_metadata.prompt_token_count,
                output_tokens=response.usage_metadata.candidates_token_count,
            )
        except AttributeError:
            usage = Usage(input_tokens=0, output_tokens=0)

        # Generate ID
        response_id = f"gemini-{random.randint(100000, 999999)}"

        return MessageResponse(
            id=response_id,
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

        generation_config: dict[str, Any] = {"max_output_tokens": max_tokens}

        if temperature is not None:
            generation_config["temperature"] = temperature
        if top_p is not None:
            generation_config["top_p"] = top_p
        if top_k is not None:
            generation_config["top_k"] = top_k
        if stop_sequences is not None:
            generation_config["stop_sequences"] = stop_sequences

        # Initialize model with tools if provided
        if tools:
            gemini_tools = self._convert_tools_to_gemini(tools)
            gemini_model = genai.GenerativeModel(
                model_name=model,
                system_instruction=system_instruction,
                tools=gemini_tools,
            )
        else:
            gemini_model = genai.GenerativeModel(
                model_name=model,
                system_instruction=system_instruction
            )

        # Generate content
        response = gemini_model.generate_content(
            gemini_messages,
            generation_config=generation_config
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

        generation_config: dict[str, Any] = {"max_output_tokens": max_tokens}

        if temperature is not None:
            generation_config["temperature"] = temperature
        if top_p is not None:
            generation_config["top_p"] = top_p
        if top_k is not None:
            generation_config["top_k"] = top_k
        if stop_sequences is not None:
            generation_config["stop_sequences"] = stop_sequences

        # Initialize model with tools if provided
        if tools:
            gemini_tools = self._convert_tools_to_gemini(tools)
            gemini_model = genai.GenerativeModel(
                model_name=model,
                system_instruction=system_instruction,
                tools=gemini_tools,
            )
        else:
            gemini_model = genai.GenerativeModel(
                model_name=model,
                system_instruction=system_instruction
            )

        # Generate content asynchronously
        response = await gemini_model.generate_content_async(
            gemini_messages,
            generation_config=generation_config
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

        # Initialize model with tools if provided
        if tools:
            gemini_tools = self._convert_tools_to_gemini(tools)
            gemini_model = genai.GenerativeModel(
                model_name=model,
                system_instruction=system_instruction,
                tools=gemini_tools,
            )
        else:
            gemini_model = genai.GenerativeModel(
                model_name=model,
                system_instruction=system_instruction
            )

        response = gemini_model.generate_content(
            gemini_messages,
            generation_config=generation_config,
            stream=True
        )

        # Generate message ID
        message_id = f"msg_gemini_{random.randint(100000, 999999)}"

        # Emit message_start
        yield {
            "type": "message_start",
            "message": {
                "id": message_id,
                "type": "message",
                "role": "assistant",
                "content": [],
                "model": model,
                "stop_reason": None,
                "stop_sequence": None,
                "usage": {"input_tokens": 0, "output_tokens": 0},
            }
        }

        # Track content blocks
        text_block_started = False
        tool_blocks: dict[str, bool] = {}
        block_index = 0

        # Stream chunks
        for chunk in response:
            # ✅ CRITICAL FIX: Check parts directly, don't access .text
            if hasattr(chunk, 'parts'):
                for part in chunk.parts:
                    # Handle text parts
                    if hasattr(part, 'text') and part.text:
                        if not text_block_started:
                            yield {
                                "type": "content_block_start",
                                "index": block_index,
                                "content_block": {"type": "text", "text": ""}
                            }
                            text_block_started = True

                        yield {
                            "type": "content_block_delta",
                            "index": block_index,
                            "delta": {"type": "text_delta", "text": part.text},
                        }
                    
                    # Handle function calls
                    elif hasattr(part, 'function_call') and part.function_call:
                        func_call = part.function_call
                        
                        # Close text block if open
                        if text_block_started:
                            yield {
                                "type": "content_block_stop",
                                "index": block_index,
                            }
                            text_block_started = False
                            block_index += 1

                        # Start tool block if not started
                        if func_call.name not in tool_blocks:
                            tool_id = f"toolu_gemini_{random.randint(100000, 999999)}"
                            yield {
                                "type": "content_block_start",
                                "index": block_index,
                                "content_block": {
                                    "type": "tool_use",
                                    "id": tool_id,
                                    "name": func_call.name,
                                }
                            }
                            tool_blocks[func_call.name] = True

                        # Emit tool input as JSON delta
                        import json
                        tool_input_json = json.dumps(dict(func_call.args))
                        yield {
                            "type": "content_block_delta",
                            "index": block_index,
                            "delta": {
                                "type": "input_json_delta",
                                "partial_json": tool_input_json
                            }
                        }

                        # Close tool block
                        yield {
                            "type": "content_block_stop",
                            "index": block_index,
                        }
                        block_index += 1

        # Close any remaining open blocks
        if text_block_started:
            yield {
                "type": "content_block_stop",
                "index": block_index,
            }

        # Emit message_stop
        yield {
            "type": "message_stop",
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

        # Initialize model with tools if provided
        if tools:
            gemini_tools = self._convert_tools_to_gemini(tools)
            gemini_model = genai.GenerativeModel(
                model_name=model,
                system_instruction=system_instruction,
                tools=gemini_tools,
            )
        else:
            gemini_model = genai.GenerativeModel(
                model_name=model,
                system_instruction=system_instruction
            )

        response = await gemini_model.generate_content_async(
            gemini_messages,
            generation_config=generation_config,
            stream=True
        )

        # Generate message ID
        message_id = f"msg_gemini_{random.randint(100000, 999999)}"

        # Emit message_start
        yield {
            "type": "message_start",
            "message": {
                "id": message_id,
                "type": "message",
                "role": "assistant",
                "content": [],
                "model": model,
                "stop_reason": None,
                "stop_sequence": None,
                "usage": {"input_tokens": 0, "output_tokens": 0},
            }
        }

        # Track content blocks
        text_block_started = False
        tool_blocks: dict[str, bool] = {}
        block_index = 0

        # Stream chunks (async)
        async for chunk in response:
            # ✅ CRITICAL FIX: Check parts directly, don't access .text
            if hasattr(chunk, 'parts'):
                for part in chunk.parts:
                    # Handle text parts
                    if hasattr(part, 'text') and part.text:
                        if not text_block_started:
                            yield {
                                "type": "content_block_start",
                                "index": block_index,
                                "content_block": {"type": "text", "text": ""}
                            }
                            text_block_started = True

                        yield {
                            "type": "content_block_delta",
                            "index": block_index,
                            "delta": {"type": "text_delta", "text": part.text},
                        }
                    
                    # Handle function calls
                    elif hasattr(part, 'function_call') and part.function_call:
                        func_call = part.function_call
                        
                        # Close text block if open
                        if text_block_started:
                            yield {
                                "type": "content_block_stop",
                                "index": block_index,
                            }
                            text_block_started = False
                            block_index += 1

                        # Start tool block if not started
                        if func_call.name not in tool_blocks:
                            tool_id = f"toolu_gemini_{random.randint(100000, 999999)}"
                            yield {
                                "type": "content_block_start",
                                "index": block_index,
                                "content_block": {
                                    "type": "tool_use",
                                    "id": tool_id,
                                    "name": func_call.name,
                                }
                            }
                            tool_blocks[func_call.name] = True

                        # Emit tool input as JSON delta
                        import json
                        tool_input_json = json.dumps(dict(func_call.args))
                        yield {
                            "type": "content_block_delta",
                            "index": block_index,
                            "delta": {
                                "type": "input_json_delta",
                                "partial_json": tool_input_json
                            }
                        }

                        # Close tool block
                        yield {
                            "type": "content_block_stop",
                            "index": block_index,
                        }
                        block_index += 1

        # Close any remaining open blocks
        if text_block_started:
            yield {
                "type": "content_block_stop",
                "index": block_index,
            }

        # Emit message_stop
        yield {
            "type": "message_stop",
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
            model_name=model,
            system_instruction=system_instruction
        )

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
            model_name=model,
            system_instruction=system_instruction
        )

        token_count = await gemini_model.count_tokens_async(gemini_messages)

        return TokenCountResponse(input_tokens=token_count.total_tokens)
