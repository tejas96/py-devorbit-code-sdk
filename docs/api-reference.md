# API Reference

Complete API reference for the Devorbit Multi-LLM SDK.

## Client Classes

### `Devorbit`

Main synchronous client for the SDK.

```python
from devorbit import Devorbit

client = Devorbit(
    provider="anthropic",
    api_key="your-api-key",
    base_url=None,  # Optional
    timeout=None,   # Optional, in seconds
    max_retries=2   # Optional
)
```

**Parameters:**

- `provider` (ProviderType): LLM provider to use. Options: `"anthropic"`, `"openai"`, `"gemini"`, `"mistral"`, `"codellama"`
- `api_key` (str, optional): API key for the provider. If not provided, looks for environment variable
- `base_url` (str, optional): Base URL for the provider's API
- `timeout` (float, optional): Request timeout in seconds
- `max_retries` (int): Maximum number of retries for failed requests

**Attributes:**

- `messages`: Messages resource for message operations

---

### `AsyncDevorbit`

Asynchronous client for the SDK.

```python
from devorbit import AsyncDevorbit

client = AsyncDevorbit(
    provider="anthropic",
    api_key="your-api-key"
)
```

Parameters and attributes are the same as `Devorbit`.

---

## Messages Resource

### `messages.create()`

Create a message with the LLM.

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
    max_tokens=1024,
    system="You are a helpful assistant",  # Optional
    temperature=0.7,                        # Optional
    top_p=0.9,                              # Optional
    top_k=40,                               # Optional
    stop_sequences=["###"],                 # Optional
    tools=[...],                            # Optional
    tool_choice={"type": "auto"},          # Optional
    metadata={},                            # Optional
)
```

**Parameters:**

- `model` (str): Model identifier
- `messages` (List[Message]): List of conversation messages
- `max_tokens` (int): Maximum tokens to generate
- `system` (str | List[Dict], optional): System prompt
- `temperature` (float, optional): Sampling temperature (0.0-1.0)
- `top_p` (float, optional): Nucleus sampling parameter
- `top_k` (int, optional): Top-k sampling parameter
- `stop_sequences` (List[str], optional): Sequences that stop generation
- `tools` (List[Tool], optional): Available tools
- `tool_choice` (ToolChoice, optional): Tool choice strategy
- `metadata` (Dict, optional): Request metadata

**Returns:** `MessageResponse`

---

### `messages.stream()`

Stream a message with the LLM.

```python
with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    messages=[{"role": "user", "content": "Hello!"}],
    max_tokens=1024
) as stream:
    for text in stream.text_stream:
        print(text, end="")

    final_message = stream.get_final_message()
```

Parameters are the same as `create()`.

**Returns:** `MessageStream` (or `AsyncMessageStream` for async)

---

### `messages.count_tokens()`

Count tokens in a message.

```python
token_count = client.messages.count_tokens(
    model="claude-sonnet-4-5-20250929",
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
    system="You are a helpful assistant",  # Optional
    tools=[...]                             # Optional
)
```

**Parameters:**

- `model` (str): Model identifier
- `messages` (List[Message]): List of messages
- `system` (str | List[Dict], optional): System prompt
- `tools` (List[Tool], optional): Available tools

**Returns:** `TokenCountResponse`

---

## Response Models

### `MessageResponse`

Response from message creation.

**Attributes:**

- `id` (str): Unique message identifier
- `type` (Literal["message"]): Always "message"
- `role` (Literal["assistant"]): Always "assistant"
- `content` (List[ResponseContentBlock]): List of content blocks
- `model` (str): Model that processed the request
- `stop_reason` (StopReason): Why generation stopped
- `stop_sequence` (str | None): Stop sequence that triggered, if any
- `usage` (Usage): Token usage information

**Methods:**

- `__str__()`: Returns concatenated text from all text blocks

---

### `TextBlock`

Text content block.

**Attributes:**

- `type` (Literal["text"]): Always "text"
- `text` (str): Text content

---

### `ToolUseBlock`

Tool use block.

**Attributes:**

- `type` (Literal["tool_use"]): Always "tool_use"
- `id` (str): Tool use identifier
- `name` (str): Tool name
- `input` (Dict[str, Any]): Tool input parameters

---

### `Usage`

Token usage information.

**Attributes:**

- `input_tokens` (int): Input tokens used
- `output_tokens` (int): Output tokens generated
- `cache_creation_input_tokens` (int | None): Cache creation tokens
- `cache_read_input_tokens` (int | None): Cache read tokens

---

### `TokenCountResponse`

Token count response.

**Attributes:**

- `input_tokens` (int): Estimated input tokens

---

## Type Definitions

### `Message`

Message in conversation.

```python
{
    "role": "user" | "assistant",
    "content": str | List[ContentBlock]
}
```

---

### `ContentBlock`

Content block types:

**TextContent:**
```python
{
    "type": "text",
    "text": str
}
```

**ImageContent:**
```python
{
    "type": "image",
    "source": {
        "type": "base64" | "url",
        "media_type": str,
        "data": str,      # For base64
        "url": str        # For URL
    }
}
```

**ToolUseContent:**
```python
{
    "type": "tool_use",
    "id": str,
    "name": str,
    "input": Dict[str, Any]
}
```

**ToolResultContent:**
```python
{
    "type": "tool_result",
    "tool_use_id": str,
    "content": str | List[ContentBlock],
    "is_error": bool  # Optional
}
```

---

### `Tool`

Tool definition.

```python
{
    "name": str,
    "description": str,
    "input_schema": {
        "type": "object",
        "properties": Dict[str, Any],
        "required": List[str]  # Optional
    }
}
```

---

### `ToolChoice`

Tool choice strategy.

**Auto:**
```python
{"type": "auto"}  # Model decides
```

**Any:**
```python
{"type": "any"}  # Model must use a tool
```

**Specific Tool:**
```python
{
    "type": "tool",
    "name": "tool_name"
}
```

---

## Stream Classes

### `MessageStream`

Synchronous message stream.

**Methods:**

- `__iter__()`: Iterate over stream events
- `text_stream`: Property that yields text deltas
- `get_final_message()`: Get complete message after stream finishes
- `get_final_text()`: Get final text content

**Usage:**
```python
with client.messages.stream(...) as stream:
    for text in stream.text_stream:
        print(text, end="")

    message = stream.get_final_message()
```

---

### `AsyncMessageStream`

Asynchronous message stream.

Methods are the same as `MessageStream` but async.

**Usage:**
```python
async with await client.messages.stream(...) as stream:
    async for text in stream.text_stream():
        print(text, end="")

    message = await stream.get_final_message()
```

---

## Error Classes

All errors inherit from `DevorbitError`.

### `APIError`

Base class for API-related errors.

**Attributes:**

- `message` (str): Error message
- `status_code` (int | None): HTTP status code
- `provider` (str | None): Provider where error occurred
- `request_id` (str | None): Request ID
- `body` (Dict | None): Response body

---

### Error Hierarchy

```
DevorbitError
├── APIError
│   ├── APIConnectionError
│   ├── APITimeoutError
│   └── APIStatusError
│       ├── RateLimitError (429)
│       ├── AuthenticationError (401)
│       ├── PermissionDeniedError (403)
│       ├── NotFoundError (404)
│       ├── BadRequestError (400)
│       ├── UnprocessableEntityError (422)
│       ├── InternalServerError (500)
│       └── OverloadedError (529)
├── ProviderError
├── UnsupportedProviderError
└── StreamError
```

---

## Constants

### `StopReason`

Possible stop reasons:

- `"end_turn"`: Natural completion
- `"max_tokens"`: Hit token limit
- `"stop_sequence"`: Hit stop sequence
- `"tool_use"`: Model wants to use a tool
- `"content_filter"`: Content filtered

### `ProviderType`

Supported providers:

- `"anthropic"`: Anthropic (Claude)
- `"openai"`: OpenAI (GPT)
- `"gemini"`: Google Gemini
- `"mistral"`: Mistral AI
- `"codellama"`: Code Llama
