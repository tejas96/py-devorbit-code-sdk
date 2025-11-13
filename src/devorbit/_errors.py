"""Error classes for the Devorbit SDK.

This module provides exception classes that mirror the Claude SDK's error hierarchy.
"""

from typing import Any, Dict, Optional


class DevorbitError(Exception):
    """Base exception for all Devorbit SDK errors."""

    def __init__(self, message: str, *, provider: Optional[str] = None) -> None:
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
        status_code: Optional[int] = None,
        provider: Optional[str] = None,
        request_id: Optional[str] = None,
        body: Optional[Dict[str, Any]] = None,
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
    provider: Optional[str] = None,
    request_id: Optional[str] = None,
    body: Optional[Dict[str, Any]] = None,
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
    error_kwargs = {
        "message": message,
        "status_code": status_code,
        "provider": provider,
        "request_id": request_id,
        "body": body,
    }

    if status_code == 400:
        return BadRequestError(**error_kwargs)
    elif status_code == 401:
        return AuthenticationError(**error_kwargs)
    elif status_code == 403:
        return PermissionDeniedError(**error_kwargs)
    elif status_code == 404:
        return NotFoundError(**error_kwargs)
    elif status_code == 422:
        return UnprocessableEntityError(**error_kwargs)
    elif status_code == 429:
        return RateLimitError(**error_kwargs)
    elif status_code == 500:
        return InternalServerError(**error_kwargs)
    elif status_code == 529:
        return OverloadedError(**error_kwargs)
    else:
        return APIStatusError(**error_kwargs)
