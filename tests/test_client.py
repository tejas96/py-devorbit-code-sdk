"""Tests for main client classes."""

import pytest

from devorbit import AsyncDevorbit, Devorbit
from devorbit.core.errors import UnsupportedProviderError


def test_devorbit_init():
    """Test Devorbit client initialization."""
    client = Devorbit(provider="anthropic", api_key="test-key")

    assert client.provider_name == "anthropic"
    assert client.api_key == "test-key"
    assert client.messages is not None


def test_async_devorbit_init():
    """Test AsyncDevorbit client initialization."""
    client = AsyncDevorbit(provider="anthropic", api_key="test-key")

    assert client.provider_name == "anthropic"
    assert client.api_key == "test-key"
    assert client.messages is not None


def test_unsupported_provider():
    """Test error on unsupported provider."""
    with pytest.raises(UnsupportedProviderError):
        Devorbit(provider="unsupported", api_key="test-key")


def test_all_supported_providers():
    """Test that all supported providers can be initialized."""
    providers = ["anthropic", "openai", "gemini", "mistral", "codellama"]

    for provider in providers:
        client = Devorbit(provider=provider, api_key="test-key")
        assert client.provider_name == provider
        assert client.messages is not None


@pytest.mark.parametrize("provider", ["anthropic", "openai", "gemini", "mistral"])
def test_provider_initialization(provider):
    """Test individual provider initialization."""
    client = Devorbit(provider=provider, api_key="test-key")
    assert client.provider_name == provider


def test_client_with_config():
    """Test client with additional configuration."""
    client = Devorbit(
        provider="anthropic",
        api_key="test-key",
        timeout=30.0,
        max_retries=3,
    )

    assert client.timeout == 30.0
    assert client.max_retries == 3
