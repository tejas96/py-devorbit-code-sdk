"""Basic usage examples for the Devorbit SDK.

This example demonstrates basic message creation with different providers.
"""

import os

from devorbit import Devorbit


def example_anthropic():
    """Example using Anthropic (Claude) provider."""
    print("\n=== Anthropic (Claude) Example ===")

    client = Devorbit(
        provider="anthropic",
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Write a haiku about programming."}],
    )

    print(f"Response: {message.content[0].text}")
    print(f"Usage: {message.usage.input_tokens} in, {message.usage.output_tokens} out")


def example_openai():
    """Example using OpenAI (GPT) provider."""
    print("\n=== OpenAI (GPT) Example ===")

    client = Devorbit(
        provider="openai",
        api_key=os.environ.get("OPENAI_API_KEY"),
    )

    message = client.messages.create(
        model="gpt-4",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Write a haiku about programming."}],
    )

    print(f"Response: {message.content[0].text}")
    print(f"Usage: {message.usage.input_tokens} in, {message.usage.output_tokens} out")


def example_gemini():
    """Example using Google Gemini provider."""
    print("\n=== Google Gemini Example ===")

    client = Devorbit(
        provider="gemini",
        api_key=os.environ.get("GOOGLE_API_KEY"),
    )

    message = client.messages.create(
        model="gemini-1.5-flash",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Write a haiku about programming."}],
    )

    print(f"Response: {message.content[0].text}")
    print(f"Usage: {message.usage.input_tokens} in, {message.usage.output_tokens} out")


def example_mistral():
    """Example using Mistral provider."""
    print("\n=== Mistral Example ===")

    client = Devorbit(
        provider="mistral",
        api_key=os.environ.get("MISTRAL_API_KEY"),
    )

    message = client.messages.create(
        model="mistral-large-latest",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Write a haiku about programming."}],
    )

    print(f"Response: {message.content[0].text}")
    print(f"Usage: {message.usage.input_tokens} in, {message.usage.output_tokens} out")


def example_with_system_prompt():
    """Example with system prompt."""
    print("\n=== Example with System Prompt ===")

    client = Devorbit(
        provider="anthropic",
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        system="You are a helpful assistant that speaks like a pirate.",
        messages=[{"role": "user", "content": "Tell me about Python programming."}],
    )

    print(f"Response: {message.content[0].text}")


def example_with_temperature():
    """Example with temperature control."""
    print("\n=== Example with Temperature ===")

    client = Devorbit(
        provider="anthropic",
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    # Low temperature (more deterministic)
    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=100,
        temperature=0.2,
        messages=[{"role": "user", "content": "Count from 1 to 5."}],
    )

    print(f"Low temperature response: {message.content[0].text}")

    # High temperature (more creative)
    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=100,
        temperature=1.0,
        messages=[{"role": "user", "content": "Count from 1 to 5."}],
    )

    print(f"High temperature response: {message.content[0].text}")


def example_multi_turn_conversation():
    """Example of multi-turn conversation."""
    print("\n=== Multi-turn Conversation ===")

    client = Devorbit(
        provider="anthropic",
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    # First turn
    messages = [{"role": "user", "content": "My name is Alice."}]

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=messages,
    )

    print(f"Assistant: {response.content[0].text}")

    # Second turn - add assistant response and new user message
    messages.append({"role": "assistant", "content": response.content[0].text})
    messages.append({"role": "user", "content": "What is my name?"})

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=messages,
    )

    print(f"Assistant: {response.content[0].text}")


if __name__ == "__main__":
    # Run examples (uncomment the ones you want to try)

    # Basic examples with different providers
    example_anthropic()
    # example_openai()
    # example_gemini()
    # example_mistral()

    # Advanced examples
    example_with_system_prompt()
    example_with_temperature()
    example_multi_turn_conversation()

    print("\n=== All examples completed! ===")
