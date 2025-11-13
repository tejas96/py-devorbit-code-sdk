"""Main client classes for the Devorbit SDK.

This module provides the main entry point classes that mirror the Claude SDK's
Anthropic and AsyncAnthropic clients.
"""

from typing import Any, Optional

from ._beta import AsyncBeta, Beta
from ._errors import UnsupportedProviderError
from ._types import ProviderType
from .providers._base import BaseProvider
from .resources import AsyncMessages, Messages


class Devorbit:
    """Main synchronous client for the Devorbit SDK.

    This class mirrors the Claude SDK's Anthropic client, providing a unified
    interface for multiple LLM providers.

    Example:
        ```python
        from devorbit import Devorbit

        client = Devorbit(provider="anthropic", api_key="your-api-key")
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1024,
            messages=[{"role": "user", "content": "Hello!"}]
        )
        ```
    """

    messages: Messages
    beta: Beta

    def __init__(
        self,
        *,
        provider: ProviderType,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: int = 2,
        **kwargs: Any,
    ) -> None:
        """Initialize the Devorbit client.

        Args:
            provider: LLM provider to use ("anthropic", "openai", "gemini", "mistral", "codellama")
            api_key: API key for the provider. If not provided, will look for environment variable.
            base_url: Base URL for the provider's API (optional)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            **kwargs: Additional provider-specific configuration

        Raises:
            UnsupportedProviderError: If the provider is not supported
        """
        self.provider_name = provider
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries

        # Initialize provider
        self._provider = self._create_provider(provider, api_key, **kwargs)

        # Initialize resources
        self.messages = Messages(self._provider)
        self.beta = Beta(self._provider)

    def _create_provider(
        self, provider: ProviderType, api_key: Optional[str], **kwargs: Any
    ) -> BaseProvider:
        """Create provider instance.

        Args:
            provider: Provider type
            api_key: API key
            **kwargs: Additional configuration

        Returns:
            Provider instance

        Raises:
            UnsupportedProviderError: If provider is not supported
        """
        if provider == "anthropic":
            from .providers.anthropic import AnthropicProvider

            return AnthropicProvider(
                api_key=api_key or "",
                base_url=self.base_url,
                timeout=self.timeout,
                max_retries=self.max_retries,
                **kwargs,
            )
        elif provider == "openai":
            from .providers.openai import OpenAIProvider

            return OpenAIProvider(
                api_key=api_key or "",
                base_url=self.base_url,
                timeout=self.timeout,
                max_retries=self.max_retries,
                **kwargs,
            )
        elif provider == "gemini":
            from .providers.gemini import GeminiProvider

            return GeminiProvider(
                api_key=api_key or "",
                base_url=self.base_url,
                timeout=self.timeout,
                max_retries=self.max_retries,
                **kwargs,
            )
        elif provider == "mistral":
            from .providers.mistral import MistralProvider

            return MistralProvider(
                api_key=api_key or "",
                base_url=self.base_url,
                timeout=self.timeout,
                max_retries=self.max_retries,
                **kwargs,
            )
        elif provider == "codellama":
            from .providers.codellama import CodeLlamaProvider

            return CodeLlamaProvider(
                api_key=api_key or "",
                base_url=self.base_url,
                timeout=self.timeout,
                max_retries=self.max_retries,
                **kwargs,
            )
        else:
            raise UnsupportedProviderError(
                f"Unsupported provider: {provider}. "
                f"Supported providers: anthropic, openai, gemini, mistral, codellama"
            )


class AsyncDevorbit:
    """Main asynchronous client for the Devorbit SDK.

    This class mirrors the Claude SDK's AsyncAnthropic client, providing async
    support for all operations.

    Example:
        ```python
        from devorbit import AsyncDevorbit
        import asyncio

        async def main():
            client = AsyncDevorbit(provider="anthropic", api_key="your-api-key")
            message = await client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=1024,
                messages=[{"role": "user", "content": "Hello!"}]
            )

        asyncio.run(main())
        ```
    """

    messages: AsyncMessages
    beta: AsyncBeta

    def __init__(
        self,
        *,
        provider: ProviderType,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: int = 2,
        **kwargs: Any,
    ) -> None:
        """Initialize the async Devorbit client.

        Args:
            provider: LLM provider to use ("anthropic", "openai", "gemini", "mistral", "codellama")
            api_key: API key for the provider. If not provided, will look for environment variable.
            base_url: Base URL for the provider's API (optional)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            **kwargs: Additional provider-specific configuration

        Raises:
            UnsupportedProviderError: If the provider is not supported
        """
        self.provider_name = provider
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries

        # Initialize provider
        self._provider = self._create_provider(provider, api_key, **kwargs)

        # Initialize resources
        self.messages = AsyncMessages(self._provider)
        self.beta = AsyncBeta(self._provider)

    def _create_provider(
        self, provider: ProviderType, api_key: Optional[str], **kwargs: Any
    ) -> BaseProvider:
        """Create provider instance.

        Args:
            provider: Provider type
            api_key: API key
            **kwargs: Additional configuration

        Returns:
            Provider instance

        Raises:
            UnsupportedProviderError: If provider is not supported
        """
        if provider == "anthropic":
            from .providers.anthropic import AnthropicProvider

            return AnthropicProvider(
                api_key=api_key or "",
                base_url=self.base_url,
                timeout=self.timeout,
                max_retries=self.max_retries,
                **kwargs,
            )
        elif provider == "openai":
            from .providers.openai import OpenAIProvider

            return OpenAIProvider(
                api_key=api_key or "",
                base_url=self.base_url,
                timeout=self.timeout,
                max_retries=self.max_retries,
                **kwargs,
            )
        elif provider == "gemini":
            from .providers.gemini import GeminiProvider

            return GeminiProvider(
                api_key=api_key or "",
                base_url=self.base_url,
                timeout=self.timeout,
                max_retries=self.max_retries,
                **kwargs,
            )
        elif provider == "mistral":
            from .providers.mistral import MistralProvider

            return MistralProvider(
                api_key=api_key or "",
                base_url=self.base_url,
                timeout=self.timeout,
                max_retries=self.max_retries,
                **kwargs,
            )
        elif provider == "codellama":
            from .providers.codellama import CodeLlamaProvider

            return CodeLlamaProvider(
                api_key=api_key or "",
                base_url=self.base_url,
                timeout=self.timeout,
                max_retries=self.max_retries,
                **kwargs,
            )
        else:
            raise UnsupportedProviderError(
                f"Unsupported provider: {provider}. "
                f"Supported providers: anthropic, openai, gemini, mistral, codellama"
            )
