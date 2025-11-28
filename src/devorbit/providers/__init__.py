"""Provider implementations for different LLM APIs.

Uses lazy loading - providers are only imported when accessed.
"""

import importlib
from typing import TYPE_CHECKING, Any

# Only BaseProvider is always available (lightweight)
from ._base import BaseProvider

__all__ = [
    "AnthropicProvider",
    "BaseProvider",
    "CodeLlamaProvider",
    "GeminiProvider",
    "MistralProvider",
    "OpenAIProvider",
]

# Lazy loading for providers (each loads its own SDK)
_LAZY_PROVIDERS: dict[str, str] = {
    "AnthropicProvider": "anthropic",
    "CodeLlamaProvider": "codellama",
    "GeminiProvider": "gemini",
    "MistralProvider": "mistral",
    "OpenAIProvider": "openai",
}

_PROVIDER_CACHE: dict[str, Any] = {}


def __getattr__(name: str) -> Any:
    """Lazy import providers."""
    if name in _PROVIDER_CACHE:
        return _PROVIDER_CACHE[name]

    if name in _LAZY_PROVIDERS:
        module_name = _LAZY_PROVIDERS[name]
        module = importlib.import_module(f".{module_name}", package="devorbit.providers")
        value = getattr(module, name)
        _PROVIDER_CACHE[name] = value
        return value

    raise AttributeError(f"module 'devorbit.providers' has no attribute '{name}'")


def __dir__() -> list[str]:
    """List available attributes."""
    return list(__all__)


# Type hints for IDE support
if TYPE_CHECKING:
    from .anthropic import AnthropicProvider
    from .codellama import CodeLlamaProvider
    from .gemini import GeminiProvider
    from .mistral import MistralProvider
    from .openai import OpenAIProvider
