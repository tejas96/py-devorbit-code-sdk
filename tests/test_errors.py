"""Tests for error classes."""

import pytest

from devorbit._errors import (
    APIError,
    AuthenticationError,
    BadRequestError,
    DevorbitError,
    InternalServerError,
    NotFoundError,
    RateLimitError,
    UnsupportedProviderError,
    map_status_code_to_error,
)


def test_devorbit_error():
    """Test base DevorbitError."""
    error = DevorbitError("Test error", provider="anthropic")

    assert str(error) == "Test error"
    assert error.provider == "anthropic"


def test_api_error():
    """Test APIError."""
    error = APIError(
        "API error",
        status_code=500,
        provider="anthropic",
        request_id="req_123",
        body={"error": "Internal error"},
    )

    assert error.status_code == 500
    assert error.provider == "anthropic"
    assert error.request_id == "req_123"
    assert error.body == {"error": "Internal error"}


def test_unsupported_provider_error():
    """Test UnsupportedProviderError."""
    error = UnsupportedProviderError("Provider not supported")

    assert str(error) == "Provider not supported"


@pytest.mark.parametrize(
    "status_code,expected_type",
    [
        (400, BadRequestError),
        (401, AuthenticationError),
        (404, NotFoundError),
        (429, RateLimitError),
        (500, InternalServerError),
    ],
)
def test_map_status_code_to_error(status_code, expected_type):
    """Test status code to error mapping."""
    error = map_status_code_to_error(
        status_code=status_code,
        message="Test error",
        provider="test",
    )

    assert isinstance(error, expected_type)
    assert error.status_code == status_code


def test_error_inheritance():
    """Test error class inheritance."""
    assert issubclass(APIError, DevorbitError)
    assert issubclass(AuthenticationError, APIError)
    assert issubclass(RateLimitError, APIError)
