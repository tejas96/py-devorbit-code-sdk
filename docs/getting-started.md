# Getting Started with Devorbit SDK

A complete guide to get started with the Devorbit Multi-LLM SDK.

## Installation

### From PyPI (when published)

```bash
pip install devorbit-multi-llm-sdk
```

### From Source

```bash
git clone https://github.com/devorbit/devorbit-multi-llm-sdk.git
cd devorbit-multi-llm-sdk
pip install -e .
```

### Development Installation

```bash
git clone https://github.com/devorbit/devorbit-multi-llm-sdk.git
cd devorbit-multi-llm-sdk
pip install -e ".[dev]"
```

## Requirements

- Python 3.12 or higher
- API keys for the providers you want to use

## Quick Start

### 1. Get API Keys

You'll need API keys for the providers you want to use:

- **Anthropic**: [Get key](https://console.anthropic.com/)
- **OpenAI**: [Get key](https://platform.openai.com/api-keys)
- **Google Gemini**: [Get key](https://makersuite.google.com/app/apikey)
- **Mistral**: [Get key](https://console.mistral.ai/)
- **Code Llama**: Get key from [Together AI](https://together.ai) or [Anyscale](https://anyscale.com)

### 2. Set Environment Variables

```bash
export ANTHROPIC_API_KEY="your-anthropic-key"
export OPENAI_API_KEY="your-openai-key"
export GOOGLE_API_KEY="your-google-key"
export MISTRAL_API_KEY="your-mistral-key"
export CODELLAMA_API_KEY="your-codellama-key"
```

### 3. Your First Message

```python
from devorbit import Devorbit

# Create client
client = Devorbit(
    provider="anthropic",
    api_key="your-api-key"  # Or omit to use env variable
)

# Create a message
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Hello! Introduce yourself."}
    ]
)

# Print response
print(message.content[0].text)
```

## Core Concepts

### 1. Providers

The SDK supports multiple LLM providers through a unified interface:

```python
# Anthropic
client = Devorbit(provider="anthropic", api_key="...")

# OpenAI
client = Devorbit(provider="openai", api_key="...")

# Google Gemini
client = Devorbit(provider="gemini", api_key="...")

# Mistral
client = Devorbit(provider="mistral", api_key="...")

# Code Llama
client = Devorbit(provider="codellama", api_key="...")
```

### 2. Messages

Messages are the primary way to interact with LLMs:

```python
messages = [
    {"role": "user", "content": "What is Python?"},
    {"role": "assistant", "content": "Python is a programming language..."},
    {"role": "user", "content": "What are its key features?"}
]

response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=messages
)
```

### 3. System Prompts

Control the assistant's behavior with system prompts:

```python
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    system="You are a helpful coding assistant specialized in Python.",
    messages=[
        {"role": "user", "content": "How do I create a list?"}
    ]
)
```

### 4. Streaming

Stream responses as they're generated:

```python
with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Write a story"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)

# Get complete message
final_message = stream.get_final_message()
```

### 5. Tool Use

Enable the model to call functions:

```python
tools = [
    {
        "name": "get_weather",
        "description": "Get current weather for a location",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            },
            "required": ["location"]
        }
    }
]

response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=tools,
    messages=[
        {"role": "user", "content": "What's the weather in Paris?"}
    ]
)
```

### 6. Vision

Send images to vision-capable models:

```python
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What's in this image?"},
                {
                    "type": "image",
                    "source": {
                        "type": "url",
                        "url": "https://example.com/image.jpg",
                        "media_type": "image/jpeg"
                    }
                }
            ]
        }
    ]
)
```

### 7. Async Support

Use async operations for better performance:

```python
import asyncio
from devorbit import AsyncDevorbit

async def main():
    client = AsyncDevorbit(
        provider="anthropic",
        api_key="your-key"
    )

    response = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Hello!"}]
    )

    print(response.content[0].text)

asyncio.run(main())
```

## Common Patterns

### Multi-turn Conversations

```python
conversation = []

# First turn
conversation.append(
    {"role": "user", "content": "My name is Alice"}
)

response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=conversation
)

# Add assistant response
conversation.append(
    {"role": "assistant", "content": response.content[0].text}
)

# Second turn
conversation.append(
    {"role": "user", "content": "What's my name?"}
)

response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=conversation
)
```

### Error Handling

```python
from devorbit import Devorbit
from devorbit._errors import (
    APIError,
    RateLimitError,
    AuthenticationError
)

client = Devorbit(provider="anthropic", api_key="your-key")

try:
    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Hello"}]
    )
except RateLimitError:
    print("Rate limit exceeded, waiting...")
    # Implement retry logic
except AuthenticationError:
    print("Invalid API key")
except APIError as e:
    print(f"API error: {e.message}")
```

### Switching Providers

```python
providers = ["anthropic", "openai", "gemini"]
prompt = "Explain quantum computing in one sentence"

for provider_name in providers:
    client = Devorbit(provider=provider_name)

    response = client.messages.create(
        model=get_model_for_provider(provider_name),
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}]
    )

    print(f"{provider_name}: {response.content[0].text}")
```

### Token Counting

```python
messages = [
    {"role": "user", "content": "Long conversation..."}
]

# Count tokens before sending
token_count = client.messages.count_tokens(
    model="claude-sonnet-4-5-20250929",
    messages=messages
)

print(f"Estimated tokens: {token_count.input_tokens}")

# Check if within limits
if token_count.input_tokens < 100000:
    response = client.messages.create(...)
```

## Next Steps

- **[API Reference](./api-reference.md)**: Complete API documentation
- **[Provider Guide](./providers.md)**: Provider-specific information
- **[Examples](../examples/)**: Comprehensive example code
- **[GitHub](https://github.com/devorbit/devorbit-multi-llm-sdk)**: Source code and issues

## Tips

### Choose the Right Model

- **General tasks**: Claude Sonnet, GPT-4
- **Code generation**: Code Llama, Claude
- **Cost optimization**: Gemini Flash, GPT-3.5
- **Vision tasks**: Claude Sonnet, GPT-4 Vision

### Optimize Performance

1. **Use async** for concurrent requests
2. **Stream** for long responses
3. **Count tokens** to stay within limits
4. **Cache system prompts** when possible

### Best Practices

1. **Handle errors** gracefully
2. **Implement retries** for rate limits
3. **Validate inputs** before API calls
4. **Use type hints** for better IDE support
5. **Set appropriate timeouts**

## Troubleshooting

### "Unsupported provider" error

Make sure you're using one of the supported providers:
`"anthropic"`, `"openai"`, `"gemini"`, `"mistral"`, `"codellama"`

### "Authentication failed" error

- Check your API key is correct
- Verify the environment variable is set
- Ensure the key has necessary permissions

### Import errors

```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### Type checking issues

```bash
# Install type stubs
pip install types-requests
```

## Support

- **Issues**: [GitHub Issues](https://github.com/devorbit/devorbit-multi-llm-sdk/issues)
- **Discussions**: [GitHub Discussions](https://github.com/devorbit/devorbit-multi-llm-sdk/discussions)
- **Documentation**: [Full Docs](https://github.com/devorbit/devorbit-multi-llm-sdk/tree/main/docs)
