"""Pytest configuration and fixtures."""

import os

import pytest


@pytest.fixture
def anthropic_api_key():
    """Anthropic API key from environment."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        pytest.skip("ANTHROPIC_API_KEY not set")
    return key


@pytest.fixture
def openai_api_key():
    """OpenAI API key from environment."""
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        pytest.skip("OPENAI_API_KEY not set")
    return key


@pytest.fixture
def gemini_api_key():
    """Gemini API key from environment."""
    key = os.environ.get("GOOGLE_API_KEY")
    if not key:
        pytest.skip("GOOGLE_API_KEY not set")
    return key


@pytest.fixture
def mistral_api_key():
    """Mistral API key from environment."""
    key = os.environ.get("MISTRAL_API_KEY")
    if not key:
        pytest.skip("MISTRAL_API_KEY not set")
    return key
