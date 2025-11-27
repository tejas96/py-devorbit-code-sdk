"""Error recovery system for Devorbit SDK.

This module provides robust error handling and recovery mechanisms:
- Error classification (transient vs permanent)
- Automatic retry with exponential backoff
- Recovery strategies (retry, fallback, abort, ask_user)
- Context-aware error handling

Example:
    from devorbit.core.recovery import RetryHandler, ErrorClassifier, RecoveryManager

    # Simple retry with backoff
    retry = RetryHandler(max_retries=3, backoff_factor=2.0)
    result = await retry.execute(async_function, arg1, arg2)

    # Classify errors
    category = ErrorClassifier.classify(exception)

    # Full recovery management
    manager = RecoveryManager()
    result = await manager.handle_error(error, context_data)
"""

from __future__ import annotations

import asyncio
import contextlib
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar


if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

T = TypeVar("T")


# ============================================================================
# Error Categories
# ============================================================================


class ErrorCategory(Enum):
    """Categories of errors for recovery handling."""

    TRANSIENT = "transient"  # Can be retried (network, timeout, rate limit)
    PERMANENT = "permanent"  # Cannot be retried (auth, not found, validation)
    RESOURCE = "resource"  # Resource issues (disk, memory)
    UNKNOWN = "unknown"  # Unknown error type


class RecoveryStrategy(Enum):
    """Recovery strategies for errors."""

    RETRY = "retry"  # Retry the operation
    RETRY_WITH_BACKOFF = "retry_with_backoff"  # Retry with exponential backoff
    FALLBACK = "fallback"  # Use fallback value/function
    ABORT = "abort"  # Stop execution
    ASK_USER = "ask_user"  # Prompt user for decision
    SKIP = "skip"  # Skip this operation and continue


# ============================================================================
# Error Info
# ============================================================================


@dataclass
class ErrorInfo:
    """Information about an error for recovery decisions.

    Attributes:
        error: The original exception
        category: Classified error category
        strategy: Recommended recovery strategy
        message: Human-readable error message
        retryable: Whether the error is retryable
        retry_after: Suggested wait time before retry (if applicable)
        context: Additional context about the error
    """

    error: Exception
    category: ErrorCategory
    strategy: RecoveryStrategy
    message: str
    retryable: bool = False
    retry_after: float | None = None
    context: dict[str, Any] = field(default_factory=dict)

    @property
    def is_retryable(self) -> bool:
        """Check if the error should be retried."""
        return self.retryable or self.category == ErrorCategory.TRANSIENT


# ============================================================================
# Error Classifier
# ============================================================================


class ErrorClassifier:
    """Classifies errors into categories.

    Uses error type, message patterns, and HTTP status codes
    to determine the appropriate category and recovery strategy.
    """

    TRANSIENT_PATTERNS: ClassVar[list[str]] = [
        "timeout",
        "timed out",
        "connection",
        "network",
        "rate limit",
        "too many requests",
        "temporarily unavailable",
        "service unavailable",
        "503",
        "502",
        "504",
        "overloaded",
        "retry",
        "ECONNRESET",
        "ETIMEDOUT",
    ]

    PERMANENT_PATTERNS: ClassVar[list[str]] = [
        "not found",
        "404",
        "unauthorized",
        "401",
        "forbidden",
        "403",
        "invalid",
        "malformed",
        "bad request",
        "400",
        "authentication",
        "permission denied",
        "access denied",
    ]

    RESOURCE_PATTERNS: ClassVar[list[str]] = [
        "disk",
        "space",
        "memory",
        "quota",
        "limit exceeded",
        "out of memory",
        "no space",
    ]

    @classmethod
    def classify(cls, error: Exception) -> ErrorCategory:
        """Classify an error into a category.

        Args:
            error: Exception to classify

        Returns:
            ErrorCategory for the error
        """
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()

        # Check by error type first
        if any(t in error_type for t in ["timeout", "connection", "network", "ratelimit"]):
            return ErrorCategory.TRANSIENT

        if any(
            t in error_type for t in ["notfound", "unauthorized", "forbidden", "validation", "auth"]
        ):
            return ErrorCategory.PERMANENT

        # Check by message patterns
        for pattern in cls.TRANSIENT_PATTERNS:
            if pattern in error_str:
                return ErrorCategory.TRANSIENT

        for pattern in cls.PERMANENT_PATTERNS:
            if pattern in error_str:
                return ErrorCategory.PERMANENT

        for pattern in cls.RESOURCE_PATTERNS:
            if pattern in error_str:
                return ErrorCategory.RESOURCE

        return ErrorCategory.UNKNOWN

    @classmethod
    def get_strategy(cls, error: Exception) -> RecoveryStrategy:
        """Get recommended recovery strategy for an error.

        Args:
            error: Exception to get strategy for

        Returns:
            Recommended RecoveryStrategy
        """
        category = cls.classify(error)

        if category == ErrorCategory.TRANSIENT:
            return RecoveryStrategy.RETRY_WITH_BACKOFF
        if category == ErrorCategory.PERMANENT:
            return RecoveryStrategy.ABORT
        if category == ErrorCategory.RESOURCE:
            return RecoveryStrategy.ASK_USER

        return RecoveryStrategy.ASK_USER

    @classmethod
    def get_error_info(cls, error: Exception) -> ErrorInfo:
        """Get complete error information.

        Args:
            error: Exception to analyze

        Returns:
            ErrorInfo with classification and recommendations
        """
        category = cls.classify(error)
        strategy = cls.get_strategy(error)

        return ErrorInfo(
            error=error,
            category=category,
            strategy=strategy,
            message=str(error),
            retryable=category == ErrorCategory.TRANSIENT,
        )


# ============================================================================
# Retry Configuration
# ============================================================================


@dataclass
class RetryConfig:
    """Configuration for retry behavior.

    Attributes:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Multiplier for exponential backoff
        jitter: Add random jitter to delay (0.0-1.0)
        retryable_exceptions: Exception types that should be retried
    """

    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    jitter: float = 0.1
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,)

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for a specific attempt with jitter.

        Args:
            attempt: Current attempt number (1-based)

        Returns:
            Delay in seconds
        """
        delay = self.initial_delay * (self.backoff_factor ** (attempt - 1))
        delay = min(delay, self.max_delay)

        # Add jitter
        if self.jitter > 0:
            jitter_range = delay * self.jitter
            delay += random.uniform(-jitter_range, jitter_range)

        return max(0, delay)


# ============================================================================
# Retry Handler
# ============================================================================


class RetryHandler:
    """Handles automatic retry with exponential backoff.

    Supports both sync and async functions with configurable retry behavior.
    """

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: float = 0.1,
        retryable_exceptions: tuple[type[Exception], ...] | None = None,
        on_retry: Callable[[int, Exception, float], None] | None = None,
    ) -> None:
        """Initialize retry handler.

        Args:
            max_retries: Maximum retry attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            backoff_factor: Exponential backoff multiplier
            jitter: Random jitter factor (0.0-1.0)
            retryable_exceptions: Exception types to retry
            on_retry: Callback on each retry (attempt, error, delay)
        """
        self.config = RetryConfig(
            max_retries=max_retries,
            initial_delay=initial_delay,
            max_delay=max_delay,
            backoff_factor=backoff_factor,
            jitter=jitter,
            retryable_exceptions=retryable_exceptions or (Exception,),
        )
        self.on_retry = on_retry
        self.attempts = 0
        self.last_error: Exception | None = None

    def should_retry(self, error: Exception) -> bool:
        """Check if an error should be retried.

        Args:
            error: Exception to check

        Returns:
            True if should retry
        """
        # Check if we have retries left
        if self.attempts >= self.config.max_retries:
            return False

        # Check if error is retryable by type
        if isinstance(error, self.config.retryable_exceptions):
            # Also check error category
            category = ErrorClassifier.classify(error)
            return category in (ErrorCategory.TRANSIENT, ErrorCategory.UNKNOWN)

        return False

    async def execute_async(
        self,
        func: Callable[..., Awaitable[T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Execute an async function with retry.

        Args:
            func: Async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            Last exception if all retries fail
        """
        self.attempts = 0
        self.last_error = None

        while True:
            try:
                self.attempts += 1
                return await func(*args, **kwargs)

            except Exception as e:
                self.last_error = e

                if not self.should_retry(e):
                    raise

                delay = self.config.get_delay(self.attempts)

                if self.on_retry:
                    self.on_retry(self.attempts, e, delay)

                await asyncio.sleep(delay)

    def execute_sync(
        self,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Execute a sync function with retry.

        Args:
            func: Sync function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            Last exception if all retries fail
        """
        self.attempts = 0
        self.last_error = None

        while True:
            try:
                self.attempts += 1
                return func(*args, **kwargs)

            except Exception as e:
                self.last_error = e

                if not self.should_retry(e):
                    raise

                delay = self.config.get_delay(self.attempts)

                if self.on_retry:
                    self.on_retry(self.attempts, e, delay)

                time.sleep(delay)


# ============================================================================
# Retry Decorator
# ============================================================================


def with_retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    retryable_exceptions: tuple[type[Exception], ...] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to add retry behavior to a function.

    Args:
        max_retries: Maximum retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Backoff multiplier
        retryable_exceptions: Exception types to retry

    Example:
        @with_retry(max_retries=3, initial_delay=1.0)
        async def fetch_data():
            return await api.get_data()
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        handler = RetryHandler(
            max_retries=max_retries,
            initial_delay=initial_delay,
            backoff_factor=backoff_factor,
            retryable_exceptions=retryable_exceptions,
        )

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            return await handler.execute_async(func, *args, **kwargs)  # type: ignore[arg-type]

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            return handler.execute_sync(func, *args, **kwargs)

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore[return-value]
        return sync_wrapper

    return decorator


# ============================================================================
# Recovery Manager
# ============================================================================


class RecoveryManager:
    """Manages error recovery strategies.

    Provides a unified interface for handling errors with configurable
    recovery strategies and fallback handlers.
    """

    def __init__(
        self,
        default_strategy: RecoveryStrategy = RecoveryStrategy.RETRY_WITH_BACKOFF,
        retry_handler: RetryHandler | None = None,
    ) -> None:
        """Initialize recovery manager.

        Args:
            default_strategy: Default recovery strategy
            retry_handler: Custom retry handler (optional)
        """
        self.default_strategy = default_strategy
        self.retry_handler = retry_handler or RetryHandler()
        self._fallbacks: dict[type[Exception], Callable[..., Any]] = {}
        self._recovery_callbacks: list[Callable[[ErrorInfo], None]] = []

    def register_fallback(
        self,
        exception_type: type[Exception],
        fallback: Callable[..., Any],
    ) -> None:
        """Register a fallback handler for an exception type.

        Args:
            exception_type: Exception type to handle
            fallback: Fallback function to call
        """
        self._fallbacks[exception_type] = fallback

    def on_recovery(self, callback: Callable[[ErrorInfo], None]) -> None:
        """Register a callback for recovery events.

        Args:
            callback: Function to call when recovery occurs
        """
        self._recovery_callbacks.append(callback)

    def handle_error(
        self,
        error: Exception,
        context: dict[str, Any] | None = None,
        strategy: RecoveryStrategy | None = None,
    ) -> ErrorInfo:
        """Handle an error with appropriate recovery.

        Args:
            error: Exception to handle
            context: Additional context about the error
            strategy: Override recovery strategy

        Returns:
            ErrorInfo with classification and strategy
        """
        # Classify error
        error_info = ErrorClassifier.get_error_info(error)
        error_info.context = context or {}

        # Override strategy if provided
        if strategy:
            error_info.strategy = strategy

        # Notify callbacks (suppress errors from callbacks)
        for callback in self._recovery_callbacks:
            with contextlib.suppress(Exception):
                callback(error_info)

        return error_info

    def get_fallback(self, error: Exception) -> Callable[..., Any] | None:
        """Get fallback handler for an exception.

        Args:
            error: Exception to get fallback for

        Returns:
            Fallback function or None
        """
        for exc_type, fallback in self._fallbacks.items():
            if isinstance(error, exc_type):
                return fallback
        return None

    async def execute_with_recovery(
        self,
        func: Callable[..., Awaitable[T]],
        *args: Any,
        fallback_value: T | None = None,
        **kwargs: Any,
    ) -> T | None:
        """Execute a function with automatic recovery.

        Args:
            func: Async function to execute
            *args: Positional arguments
            fallback_value: Value to return on failure
            **kwargs: Keyword arguments

        Returns:
            Function result or fallback value
        """
        try:
            return await self.retry_handler.execute_async(func, *args, **kwargs)
        except Exception as e:
            error_info = self.handle_error(e)

            # Try fallback
            fallback_func = self.get_fallback(e)
            if fallback_func:
                with contextlib.suppress(Exception):
                    fallback_result = fallback_func(*args, **kwargs)
                    if fallback_result is not None:
                        return fallback_result  # type: ignore[no-any-return]

            # Return fallback value if provided
            if fallback_value is not None:
                return fallback_value

            # Re-raise if no fallback
            if error_info.strategy == RecoveryStrategy.ABORT:
                raise

            return None


# ============================================================================
# Global Instance
# ============================================================================


_recovery_manager: RecoveryManager | None = None


def get_recovery_manager() -> RecoveryManager:
    """Get or create the global recovery manager instance."""
    global _recovery_manager  # noqa: PLW0603
    if _recovery_manager is None:
        _recovery_manager = RecoveryManager()
    return _recovery_manager


def reset_recovery_manager() -> None:
    """Reset the global recovery manager (for testing)."""
    global _recovery_manager  # noqa: PLW0603
    _recovery_manager = None


# Export all public classes and functions
__all__ = [
    "ErrorCategory",
    "ErrorClassifier",
    "ErrorInfo",
    "RecoveryManager",
    "RecoveryStrategy",
    "RetryConfig",
    "RetryHandler",
    "get_recovery_manager",
    "reset_recovery_manager",
    "with_retry",
]
