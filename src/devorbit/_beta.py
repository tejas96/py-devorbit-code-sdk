"""Beta namespace for experimental features.

This module provides the beta namespace similar to Claude SDK's beta features.
"""

from .providers._base import BaseProvider
from .resources.batches import AsyncMessageBatches, MessageBatches
from .resources.messages import AsyncMessages, Messages


class BetaMessages(Messages):
    """Beta messages resource with extended features.

    Extends the standard Messages resource with beta features like:
    - Prompt caching
    - Extended thinking
    - PDF support
    """

    def __init__(self, provider: BaseProvider) -> None:
        """Initialize beta messages resource.

        Args:
            provider: Provider implementation to use
        """
        super().__init__(provider)
        self.batches = MessageBatches(provider)


class AsyncBetaMessages(AsyncMessages):
    """Async beta messages resource with extended features."""

    def __init__(self, provider: BaseProvider) -> None:
        """Initialize async beta messages resource.

        Args:
            provider: Provider implementation to use
        """
        super().__init__(provider)
        self.batches = AsyncMessageBatches(provider)


class Beta:
    """Beta namespace for experimental features.

    Provides access to beta features similar to Claude SDK:
    - client.beta.messages - Beta messages API
    - client.beta.tools - Tool helpers (via _tool_helpers module)

    Example:
        ```python
        from devorbit import Devorbit

        client = Devorbit(provider="anthropic", api_key="...")

        # Use beta messages with caching
        response = client.beta.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1024,
            system=[
                {
                    "type": "text",
                    "text": "You are a helpful assistant.",
                    "cache_control": {"type": "ephemeral"}
                }
            ],
            messages=[{"role": "user", "content": "Hello!"}]
        )

        # Use message batches
        batch = client.beta.messages.batches.create(
            requests=[...]
        )
        ```
    """

    messages: BetaMessages

    def __init__(self, provider: BaseProvider) -> None:
        """Initialize beta namespace.

        Args:
            provider: Provider implementation to use
        """
        self._provider = provider
        self.messages = BetaMessages(provider)


class AsyncBeta:
    """Async beta namespace for experimental features."""

    messages: AsyncBetaMessages

    def __init__(self, provider: BaseProvider) -> None:
        """Initialize async beta namespace.

        Args:
            provider: Provider implementation to use
        """
        self._provider = provider
        self.messages = AsyncBetaMessages(provider)
