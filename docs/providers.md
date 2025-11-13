# Provider Guide

Detailed information about each LLM provider supported by the Devorbit SDK.

## Table of Contents

- [Anthropic (Claude)](#anthropic-claude)
- [OpenAI (GPT)](#openai-gpt)
- [Google Gemini](#google-gemini)
- [Mistral AI](#mistral-ai)
- [Code Llama](#code-llama)
- [Provider Comparison](#provider-comparison)

---

## Anthropic (Claude)

### Setup

```python
from devorbit import Devorbit

client = Devorbit(
    provider="anthropic",
    api_key="your-anthropic-api-key"
)
```

Or set environment variable:
```bash
export ANTHROPIC_API_KEY="your-api-key"
```

### Supported Models

- `claude-sonnet-4-5-20250929` - Latest Sonnet 4.5
- `claude-opus-4-20250514` - Claude Opus 4
- `claude-3-5-sonnet-20241022` - Claude 3.5 Sonnet
- `claude-3-opus-20240229` - Claude 3 Opus
- `claude-3-sonnet-20240229` - Claude 3 Sonnet
- `claude-3-haiku-20240307` - Claude 3 Haiku

### Features

✅ Messages API
✅ Streaming
✅ Tool use
✅ Vision (image inputs)
✅ System prompts
✅ Token counting
✅ Temperature, top_p, top_k
✅ Stop sequences

### Notes

- Most comprehensive feature support
- Native SDK wrapper
- Excellent tool use support
- Best vision capabilities

---

## OpenAI (GPT)

### Setup

```python
from devorbit import Devorbit

client = Devorbit(
    provider="openai",
    api_key="your-openai-api-key"
)
```

Or set environment variable:
```bash
export OPENAI_API_KEY="your-api-key"
```

### Supported Models

- `gpt-4` - GPT-4
- `gpt-4-turbo` - GPT-4 Turbo
- `gpt-4-vision-preview` - GPT-4 with vision
- `gpt-3.5-turbo` - GPT-3.5 Turbo
- `gpt-3.5-turbo-16k` - GPT-3.5 with 16k context

### Features

✅ Messages API
✅ Streaming
✅ Tool use (function calling)
✅ Vision (with vision models)
✅ System prompts
✅ Token counting (with tiktoken)
✅ Temperature, top_p
❌ top_k (not supported by OpenAI)
✅ Stop sequences

### Notes

- Uses OpenAI's chat completions API
- Function calling translated to our tool format
- Token counting requires `tiktoken` library (optional)
- Vision requires specific vision-enabled models

---

## Google Gemini

### Setup

```python
from devorbit import Devorbit

client = Devorbit(
    provider="gemini",
    api_key="your-google-api-key"
)
```

Or set environment variable:
```bash
export GOOGLE_API_KEY="your-api-key"
```

### Supported Models

- `gemini-1.5-pro` - Gemini 1.5 Pro
- `gemini-1.5-flash` - Gemini 1.5 Flash
- `gemini-pro` - Gemini Pro
- `gemini-pro-vision` - Gemini Pro with vision

### Features

✅ Messages API
✅ Streaming
✅ Tool use (function calling)
✅ Vision (image inputs)
✅ System prompts (via system_instruction)
✅ Token counting (native)
✅ Temperature, top_p, top_k
✅ Stop sequences

### Notes

- Uses Google's Generative AI SDK
- Excellent native token counting
- Good vision support
- Role mapping: "assistant" → "model"

---

## Mistral AI

### Setup

```python
from devorbit import Devorbit

client = Devorbit(
    provider="mistral",
    api_key="your-mistral-api-key"
)
```

Or set environment variable:
```bash
export MISTRAL_API_KEY="your-api-key"
```

### Supported Models

- `mistral-large-latest` - Mistral Large
- `mistral-medium-latest` - Mistral Medium
- `mistral-small-latest` - Mistral Small
- `open-mistral-7b` - Open Mistral 7B
- `open-mixtral-8x7b` - Open Mixtral 8x7B

### Features

✅ Messages API
✅ Streaming
✅ Tool use (function calling)
❌ Vision (not yet supported)
✅ System prompts
⚠️ Token counting (estimated)
✅ Temperature, top_p
❌ top_k (not supported)
✅ Stop sequences

### Notes

- Uses Mistral's official SDK
- Token counting is estimated (no native API)
- Good tool use support
- Fast inference

---

## Code Llama

### Setup

Code Llama requires an OpenAI-compatible endpoint (Together AI, Anyscale, etc.)

```python
from devorbit import Devorbit

client = Devorbit(
    provider="codellama",
    api_key="your-api-key",
    base_url="https://api.together.xyz/v1"  # Or your endpoint
)
```

Or set environment variables:
```bash
export CODELLAMA_API_KEY="your-api-key"
export CODELLAMA_BASE_URL="https://api.together.xyz/v1"
```

### Supported Models

Depends on your provider, common options:

- `meta-llama/CodeLlama-34b-Instruct-hf`
- `meta-llama/CodeLlama-13b-Instruct-hf`
- `meta-llama/CodeLlama-7b-Instruct-hf`

### Recommended Providers

**Together AI:**
- Base URL: `https://api.together.xyz/v1`
- Models: Various Code Llama models
- Website: [together.ai](https://together.ai)

**Anyscale:**
- Base URL: `https://api.endpoints.anyscale.com/v1`
- Models: Code Llama variants
- Website: [anyscale.com](https://anyscale.com)

### Features

✅ Messages API
✅ Streaming
⚠️ Tool use (depends on provider)
❌ Vision (not supported)
✅ System prompts
⚠️ Token counting (estimated)
✅ Temperature, top_p, top_k
✅ Stop sequences

### Notes

- Requires OpenAI-compatible endpoint
- Specialized for code generation
- Token counting is estimated
- Provider-dependent features

---

## Provider Comparison

| Feature | Anthropic | OpenAI | Gemini | Mistral | Code Llama |
|---------|-----------|--------|--------|---------|------------|
| **Streaming** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Tools** | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| **Vision** | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Token Count** | ✅ | ✅* | ✅ | ⚠️ | ⚠️ |
| **top_k** | ✅ | ❌ | ✅ | ❌ | ✅ |
| **System** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Code** | Good | Good | Good | Good | Excellent |

*Requires tiktoken library
⚠️ = Partial/estimated support

---

## Environment Variables

The SDK looks for these environment variables:

```bash
# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# OpenAI
export OPENAI_API_KEY="sk-..."

# Google Gemini
export GOOGLE_API_KEY="..."

# Mistral
export MISTRAL_API_KEY="..."

# Code Llama
export CODELLAMA_API_KEY="..."
export CODELLAMA_BASE_URL="https://api.together.xyz/v1"
```

---

## Choosing a Provider

### For General Use
- **Anthropic Claude**: Most balanced, excellent for most tasks
- **OpenAI GPT-4**: Strong reasoning, widely documented

### For Code Generation
- **Code Llama**: Specialized for code
- **Anthropic Claude**: Also excellent for code

### For Vision Tasks
- **Anthropic Claude**: Best vision capabilities
- **OpenAI GPT-4**: Good vision with specific models
- **Gemini**: Good multimodal support

### For Cost Optimization
- **Gemini Flash**: Fast and economical
- **GPT-3.5**: Lower cost option
- **Mistral Small**: Budget-friendly

### For Streaming
All providers support streaming well.

### For Tool Use
- **Anthropic Claude**: Most mature tool use
- **OpenAI**: Well-documented function calling
- **Gemini**: Good tool support

---

## Provider-Specific Tips

### Anthropic
```python
# Use extended thinking for complex tasks
client.messages.create(
    model="claude-sonnet-4-5-20250929",
    messages=[...],
    # Claude automatically uses thinking when needed
)
```

### OpenAI
```python
# Specify temperature for creative vs deterministic
client.messages.create(
    model="gpt-4",
    messages=[...],
    temperature=0.7  # Higher for creative, lower for deterministic
)
```

### Gemini
```python
# Leverage top_k for code generation
client.messages.create(
    model="gemini-1.5-pro",
    messages=[...],
    top_k=40  # Helps with code quality
)
```

### Mistral
```python
# Use appropriate model size for task
client.messages.create(
    model="mistral-large-latest",  # For complex tasks
    messages=[...]
)
```

### Code Llama
```python
# Provide clear code context
client.messages.create(
    model="meta-llama/CodeLlama-34b-Instruct-hf",
    system="You are an expert Python programmer.",
    messages=[...]
)
```
