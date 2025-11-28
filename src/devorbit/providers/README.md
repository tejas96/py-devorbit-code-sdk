# 🔌 Devorbit Providers

> Unified interface to multiple LLM providers. One API, many models.

## Supported Providers

| Provider | Models | Streaming | Tools | Vision |
|----------|--------|-----------|-------|--------|
| **Anthropic** | Claude 3.5, Claude 3, etc. | ✅ | ✅ | ✅ |
| **OpenAI** | GPT-4o, GPT-4, GPT-3.5 | ✅ | ✅ | ✅ |
| **Google** | Gemini Pro, Gemini Flash | ✅ | ✅ | ✅ |
| **Mistral** | Mistral Large, Medium, Small | ✅ | ✅ | ❌ |
| **Code Llama** | Code Llama 70B, 34B, 13B | ✅ | ✅ | ❌ |

---

## Quick Start

```python
from devorbit import Devorbit

# Pick your provider
client = Devorbit(
    provider="anthropic",  # or "openai", "gemini", "mistral", "codellama"
    api_key="your-api-key"
)

# Same API for all providers!
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.content[0].text)
```

---

## 🟣 Anthropic (Claude)

### Setup

```python
from devorbit import Devorbit

client = Devorbit(
    provider="anthropic",
    api_key="sk-ant-..."  # or set ANTHROPIC_API_KEY env var
)
```

### Available Models

| Model | Context | Best For |
|-------|---------|----------|
| `claude-sonnet-4-20250514` | 200K | **Recommended** - Best balance |
| `claude-3-5-sonnet-20241022` | 200K | Previous generation |
| `claude-3-opus-20240229` | 200K | Complex reasoning |
| `claude-3-haiku-20240307` | 200K | Fast, cheap |

### Example

```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    system="You are a helpful coding assistant.",
    messages=[
        {"role": "user", "content": "Explain Python decorators"}
    ]
)
```

### Special Features

- **Prompt Caching**: Reduce costs for repeated context
- **Extended Thinking**: Access model's reasoning
- **Computer Use**: Screen interaction tools

```python
# Prompt caching
response = client.beta.messages.create(
    model="claude-sonnet-4-20250514",
    system=[{
        "type": "text",
        "text": "Long context here...",
        "cache_control": {"type": "ephemeral"}
    }],
    messages=[...]
)
```

---

## 🟢 OpenAI (GPT)

### Setup

```python
from devorbit import Devorbit

client = Devorbit(
    provider="openai",
    api_key="sk-..."  # or set OPENAI_API_KEY env var
)
```

### Available Models

| Model | Context | Best For |
|-------|---------|----------|
| `gpt-4o` | 128K | **Recommended** - Multimodal |
| `gpt-4o-mini` | 128K | Fast, cheap |
| `gpt-4-turbo` | 128K | High quality |
| `gpt-3.5-turbo` | 16K | Budget option |

### Example

```python
response = client.messages.create(
    model="gpt-4o",
    max_tokens=4096,
    messages=[
        {"role": "user", "content": "Write a Python function to sort a list"}
    ]
)
```

### Vision Support

```python
response = client.messages.create(
    model="gpt-4o",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "What's in this image?"},
            {"type": "image_url", "image_url": {"url": "https://..."}}
        ]
    }]
)
```

---

## 🔵 Google (Gemini)

### Setup

```python
from devorbit import Devorbit

client = Devorbit(
    provider="gemini",
    api_key="AIza..."  # or set GOOGLE_API_KEY env var
)
```

### Available Models

| Model | Context | Best For |
|-------|---------|----------|
| `gemini-1.5-pro` | 1M | **Recommended** - Long context |
| `gemini-1.5-flash` | 1M | Fast responses |
| `gemini-pro` | 32K | Standard tasks |

### Example

```python
response = client.messages.create(
    model="gemini-1.5-pro",
    max_tokens=4096,
    messages=[
        {"role": "user", "content": "Analyze this codebase..."}
    ]
)
```

### Streaming

```python
with client.messages.stream(
    model="gemini-1.5-flash",
    max_tokens=2048,
    messages=[{"role": "user", "content": "Tell me a story"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

---

## 🟠 Mistral

### Setup

```python
from devorbit import Devorbit

client = Devorbit(
    provider="mistral",
    api_key="..."  # or set MISTRAL_API_KEY env var
)
```

### Available Models

| Model | Context | Best For |
|-------|---------|----------|
| `mistral-large-latest` | 128K | **Recommended** - Best quality |
| `mistral-medium-latest` | 32K | Balanced |
| `mistral-small-latest` | 32K | Fast, efficient |
| `codestral-latest` | 32K | Code generation |

### Example

```python
response = client.messages.create(
    model="mistral-large-latest",
    max_tokens=4096,
    messages=[
        {"role": "user", "content": "Write a REST API in FastAPI"}
    ]
)
```

---

## 🦙 Code Llama

### Setup

```python
from devorbit import Devorbit

client = Devorbit(
    provider="codellama",
    api_key="...",  # Your inference endpoint key
    base_url="https://your-endpoint.com"  # Required
)
```

### Available Models

| Model | Parameters | Best For |
|-------|------------|----------|
| `codellama-70b` | 70B | **Recommended** - Best quality |
| `codellama-34b` | 34B | Balanced |
| `codellama-13b` | 13B | Fast inference |
| `codellama-7b` | 7B | Edge deployment |

### Example

```python
response = client.messages.create(
    model="codellama-70b",
    max_tokens=2048,
    messages=[
        {"role": "user", "content": "Implement binary search in Rust"}
    ]
)
```

---

## 🔀 Switching Providers

The magic of Devorbit - same code, different providers:

```python
from devorbit import Devorbit

def chat(provider: str, api_key: str, model: str, prompt: str) -> str:
    """Works with ANY provider!"""
    client = Devorbit(provider=provider, api_key=api_key)
    
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text

# Use with any provider
result = chat("anthropic", "sk-ant-...", "claude-sonnet-4-20250514", "Hi!")
result = chat("openai", "sk-...", "gpt-4o", "Hi!")
result = chat("gemini", "AIza...", "gemini-1.5-pro", "Hi!")
```

---

## 🛠️ Tool Use (Function Calling)

All providers support tool use with the same interface:

```python
tools = [{
    "name": "get_weather",
    "description": "Get current weather for a location",
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "City name"},
            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
        },
        "required": ["location"]
    }
}]

response = client.messages.create(
    model="claude-sonnet-4-20250514",  # or gpt-4o, gemini-1.5-pro, etc.
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "What's the weather in Tokyo?"}]
)

# Check if model wants to use a tool
if response.stop_reason == "tool_use":
    tool_use = response.content[0]
    print(f"Tool: {tool_use.name}")
    print(f"Input: {tool_use.input}")
```

---

## 🌊 Streaming

All providers support streaming:

```python
# Context manager style
with client.messages.stream(
    model="gpt-4o",
    max_tokens=2048,
    messages=[{"role": "user", "content": "Write a poem"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
    
    # Get final message
    message = stream.get_final_message()
    print(f"\n\nTokens used: {message.usage.output_tokens}")
```

---

## ⚡ Async Support

```python
from devorbit import AsyncDevorbit
import asyncio

async def main():
    client = AsyncDevorbit(
        provider="anthropic",
        api_key="sk-ant-..."
    )
    
    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Hello!"}]
    )
    
    print(response.content[0].text)

asyncio.run(main())
```

---

## 🔧 Environment Variables

Set API keys via environment variables (recommended):

```bash
# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# OpenAI
export OPENAI_API_KEY="sk-..."

# Google
export GOOGLE_API_KEY="AIza..."

# Mistral
export MISTRAL_API_KEY="..."
```

Then initialize without explicit key:

```python
client = Devorbit(provider="anthropic")  # Uses ANTHROPIC_API_KEY
```

---

## 📊 Provider Comparison

| Feature | Anthropic | OpenAI | Gemini | Mistral |
|---------|-----------|--------|--------|---------|
| Max Context | 200K | 128K | 1M | 128K |
| Streaming | ✅ | ✅ | ✅ | ✅ |
| Tool Use | ✅ | ✅ | ✅ | ✅ |
| Vision | ✅ | ✅ | ✅ | ❌ |
| Prompt Caching | ✅ | ❌ | ❌ | ❌ |
| Extended Thinking | ✅ | ❌ | ❌ | ❌ |

---

## 💡 Best Practices

1. **Use environment variables** for API keys
2. **Set reasonable max_tokens** to control costs
3. **Use streaming** for better UX on long responses
4. **Handle rate limits** with retries
5. **Pick the right model** for your use case:
   - Complex reasoning → Claude Opus, GPT-4
   - Fast responses → Claude Haiku, GPT-4o-mini, Gemini Flash
   - Long context → Gemini 1.5 Pro (1M tokens!)
   - Code → Codestral, Code Llama

---

## 🔗 See Also

- [Tools README](../tools/README.md)
- [CLI Commands README](../cli/commands/README.md)
- [Main README](../../../README.md)

