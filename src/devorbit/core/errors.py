"""Error classes for the Devorbit SDK.

This module provides exception classes that mirror the Claude SDK's error hierarchy.
"""

from typing import Any


class DevorbitError(Exception):
    """Base exception for all Devorbit SDK errors."""

    def __init__(self, message: str, *, provider: str | None = None) -> None:
        """Initialize error.

        Args:
            message: Error message
            provider: Provider where error occurred
        """
        super().__init__(message)
        self.message = message
        self.provider = provider


class APIError(DevorbitError):
    """Base class for API-related errors."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        provider: str | None = None,
        request_id: str | None = None,
        body: dict[str, Any] | None = None,
    ) -> None:
        """Initialize API error.

        Args:
            message: Error message
            status_code: HTTP status code
            provider: Provider where error occurred
            request_id: Request ID if available
            body: Response body
        """
        super().__init__(message, provider=provider)
        self.status_code = status_code
        self.request_id = request_id
        self.body = body


class APIConnectionError(APIError):
    """Error connecting to API."""

    pass


class APITimeoutError(APIError):
    """API request timed out."""

    pass


class APIStatusError(APIError):
    """API returned an error status code."""

    pass


class RateLimitError(APIStatusError):
    """API rate limit exceeded."""

    pass


class AuthenticationError(APIStatusError):
    """Authentication failed."""

    pass


class PermissionDeniedError(APIStatusError):
    """Permission denied."""

    pass


class NotFoundError(APIStatusError):
    """Resource not found."""

    pass


class BadRequestError(APIStatusError):
    """Bad request."""

    pass


class UnprocessableEntityError(APIStatusError):
    """Unprocessable entity (validation error)."""

    pass


class InternalServerError(APIStatusError):
    """Internal server error."""

    pass


class OverloadedError(APIStatusError):
    """API is overloaded."""

    pass


class ProviderError(DevorbitError):
    """Error specific to a provider implementation."""

    pass


class UnsupportedProviderError(DevorbitError):
    """Unsupported provider specified."""

    pass


class StreamError(DevorbitError):
    """Error during streaming."""

    pass


def map_status_code_to_error(
    status_code: int,
    message: str,
    provider: str | None = None,
    request_id: str | None = None,
    body: dict[str, Any] | None = None,
) -> APIStatusError:
    """Map HTTP status code to appropriate error class.

    Args:
        status_code: HTTP status code
        message: Error message
        provider: Provider where error occurred
        request_id: Request ID if available
        body: Response body

    Returns:
        Appropriate APIStatusError subclass
    """
    # Map status codes to error classes
    error_map: dict[int, type[APIStatusError]] = {
        400: BadRequestError,
        401: AuthenticationError,
        403: PermissionDeniedError,
        404: NotFoundError,
        422: UnprocessableEntityError,
        429: RateLimitError,
        500: InternalServerError,
        529: OverloadedError,
    }

    error_class = error_map.get(status_code, APIStatusError)
    return error_class(
        message, status_code=status_code, provider=provider, request_id=request_id, body=body
    )
