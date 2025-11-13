# Devorbit Multi-LLM SDK

A unified Python SDK for multiple LLM providers with a Claude SDK-like interface.

## Features

- **Unified API**: Single, consistent interface across multiple LLM providers
- **Claude SDK Compatible**: Familiar API design for Claude SDK users
- **Async Support**: Full async/await support with `AsyncDevorbit` client
- **Type Safe**: TypedDicts for requests, Pydantic models for responses
- **Streaming**: Server-sent events (SSE) streaming for all providers
- **Tool Use**: Function calling support across providers
- **Vision**: Image input support where available
- **Extensible**: Easy to add new providers

## Supported Providers

- **Anthropic** (Claude models)
- **OpenAI** (GPT models)
- **Google** (Gemini models)
- **Mistral** (Mistral models)
- **Code Llama** (Meta's Code Llama models)

## Installation

```bash
pip install devorbit-multi-llm-sdk
```

## Quick Start

```python
from devorbit import Devorbit

# Initialize client with provider
client = Devorbit(
    provider="anthropic",
    api_key="your-api-key"
)

# Create a message (just like Claude SDK)
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Hello, Claude!"}
    ]
)

print(message.content[0].text)
```

### Switching Providers

```python
# Use OpenAI instead
client = Devorbit(
    provider="openai",
    api_key="your-openai-key"
)

message = client.messages.create(
    model="gpt-4",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Hello, GPT!"}
    ]
)
```

### Async Usage

```python
from devorbit import AsyncDevorbit

async def main():
    client = AsyncDevorbit(
        provider="anthropic",
        api_key="your-api-key"
    )

    message = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": "Hello!"}
        ]
    )

    print(message.content[0].text)

import asyncio
asyncio.run(main())
```

### Streaming

```python
# Streaming with context manager
with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Write a haiku"}
    ]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)

# Or get the final message
message = stream.get_final_message()
```

### Tool Use

```python
tools = [
    {
        "name": "get_weather",
        "description": "Get weather for a location",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            },
            "required": ["location"]
        }
    }
]

message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=tools,
    messages=[
        {"role": "user", "content": "What's the weather in SF?"}
    ]
)
```

## Documentation

- [API Reference](./docs/api-reference.md)
- [Provider Guide](./docs/providers.md)
- [Examples](./examples/)

## Requirements

- Python 3.12+
- See `pyproject.toml` for dependency details

## License

MIT
