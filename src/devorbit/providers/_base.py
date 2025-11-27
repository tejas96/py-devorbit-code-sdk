"""Base provider interface.

This module defines the abstract base class that all provider implementations must follow.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Iterator
from typing import Any

from ..core.models import MessageResponse, TokenCountResponse
from ..core.types import Message, Tool


class BaseProvider(ABC):
    """Abstract base class for LLM providers.

    All provider implementations must inherit from this class and implement
    the required methods for both sync and async operations.
    """

    def __init__(self, api_key: str, **kwargs: Any) -> None:
        """Initialize provider.

        Args:
            api_key: API key for the provider
            **kwargs: Additional provider-specific configuration
        """
        self.api_key = api_key
        self.config = kwargs

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass

    @abstractmethod
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
        """Create a message synchronously.

        Args:
            model: Model identifier
            messages: List of messages
            max_tokens: Maximum tokens to generate
            system: System prompt
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            stop_sequences: Sequences that stop generation
            tools: Available tools
            tool_choice: Tool choice strategy
            metadata: Request metadata
            **kwargs: Additional provider-specific parameters

        Returns:
            MessageResponse object
        """
        pass

    @abstractmethod
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
        """Create a message asynchronously.

        Args:
            model: Model identifier
            messages: List of messages
            max_tokens: Maximum tokens to generate
            system: System prompt
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            stop_sequences: Sequences that stop generation
            tools: Available tools
            tool_choice: Tool choice strategy
            metadata: Request metadata
            **kwargs: Additional provider-specific parameters

        Returns:
            MessageResponse object
        """
        pass

    @abstractmethod
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
        """Stream a message synchronously.

        Args:
            model: Model identifier
            messages: List of messages
            max_tokens: Maximum tokens to generate
            system: System prompt
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            stop_sequences: Sequences that stop generation
            tools: Available tools
            tool_choice: Tool choice strategy
            metadata: Request metadata
            **kwargs: Additional provider-specific parameters

        Yields:
            Stream event dictionaries
        """
        pass

    @abstractmethod
    def astream_message(
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
        """Stream a message asynchronously.

        Args:
            model: Model identifier
            messages: List of messages
            max_tokens: Maximum tokens to generate
            system: System prompt
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            stop_sequences: Sequences that stop generation
            tools: Available tools
            tool_choice: Tool choice strategy
            metadata: Request metadata
            **kwargs: Additional provider-specific parameters

        Yields:
            Stream event dictionaries

        Note:
            Implementations should use 'async def' with 'yield' to create
            an async generator.
        """
        pass

    @abstractmethod
    def count_tokens(
        self,
        model: str,
        messages: list[Message],
        *,
        system: str | None = None,
        tools: list[Tool] | None = None,
        **kwargs: Any,
    ) -> TokenCountResponse:
        """Count tokens synchronously.

        Args:
            model: Model identifier
            messages: List of messages
            system: System prompt
            tools: Available tools
            **kwargs: Additional provider-specific parameters

        Returns:
            TokenCountResponse with token count
        """
        pass

    @abstractmethod
    async def acount_tokens(
        self,
        model: str,
        messages: list[Message],
        *,
        system: str | None = None,
        tools: list[Tool] | None = None,
        **kwargs: Any,
    ) -> TokenCountResponse:
        """Count tokens asynchronously.

        Args:
            model: Model identifier
            messages: List of messages
            system: System prompt
            tools: Available tools
            **kwargs: Additional provider-specific parameters

        Returns:
            TokenCountResponse with token count
        """
        pass

    def validate_model(self, model: str) -> None:
        """Validate model identifier for this provider.

        Args:
            model: Model identifier to validate

        Raises:
            ValueError: If model is not supported by this provider
        """
        # Default implementation - providers can override
        # Most providers don't need strict validation
        return
