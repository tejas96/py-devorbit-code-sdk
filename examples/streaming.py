"""Streaming examples for the Devorbit SDK.

This example demonstrates streaming responses from different providers.
"""

import asyncio
import os

from devorbit import AsyncDevorbit, Devorbit


def example_sync_streaming():
    """Example of synchronous streaming."""
    print("\n=== Synchronous Streaming Example ===")

    client = Devorbit(
        provider="anthropic",
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    print("Streaming response: ", end="", flush=True)

    with client.messages.stream(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": "Write a short story about a robot learning to code."}
        ],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)

    print("\n")

    # Get the final complete message
    final_message = stream.get_final_message()
    print(f"\nTotal tokens used: {final_message.usage.output_tokens}")


def example_sync_streaming_with_context():
    """Example of streaming with context manager."""
    print("\n=== Streaming with Context Manager ===")

    client = Devorbit(
        provider="anthropic",
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    with client.messages.stream(
        model="claude-sonnet-4-5-20250929",
        max_tokens=512,
        messages=[{"role": "user", "content": "Explain async/await in Python in 3 sentences."}],
    ) as stream:
        # Stream text as it arrives
        print("Response: ", end="", flush=True)
        for text in stream.text_stream:
            print(text, end="", flush=True)
        print("\n")

        # Access the complete message
        message = stream.get_final_message()
        print(f"Stop reason: {message.stop_reason}")
        print(f"Model: {message.model}")


async def example_async_streaming():
    """Example of asynchronous streaming."""
    print("\n=== Asynchronous Streaming Example ===")

    client = AsyncDevorbit(
        provider="anthropic",
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    print("Streaming response: ", end="", flush=True)

    async with await client.messages.stream(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Write a haiku about streaming data."}],
    ) as stream:
        async for text in stream.text_stream():
            print(text, end="", flush=True)

    print("\n")

    # Get the final message
    final_message = await stream.get_final_message()
    print(f"Tokens: {final_message.usage.output_tokens}")


async def example_parallel_streaming():
    """Example of streaming from multiple providers in parallel."""
    print("\n=== Parallel Streaming Example ===")

    # Create clients for different providers
    anthropic_client = AsyncDevorbit(
        provider="anthropic",
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    openai_client = AsyncDevorbit(
        provider="openai",
        api_key=os.environ.get("OPENAI_API_KEY"),
    )

    prompt = "Write a one-sentence description of machine learning."

    # Stream from both providers in parallel
    async def stream_anthropic():
        print("\nAnthropic: ", end="", flush=True)
        async with await anthropic_client.messages.stream(
            model="claude-sonnet-4-5-20250929",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            async for text in stream.text_stream():
                print(text, end="", flush=True)
        print()

    async def stream_openai():
        print("\nOpenAI: ", end="", flush=True)
        async with await openai_client.messages.stream(
            model="gpt-4",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            async for text in stream.text_stream():
                print(text, end="", flush=True)
        print()

    # Run both streams concurrently
    await asyncio.gather(stream_anthropic(), stream_openai())


def example_streaming_with_stop_sequences():
    """Example of streaming with stop sequences."""
    print("\n=== Streaming with Stop Sequences ===")

    client = Devorbit(
        provider="anthropic",
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    print("Streaming until '###': ", end="", flush=True)

    with client.messages.stream(
        model="claude-sonnet-4-5-20250929",
        max_tokens=512,
        stop_sequences=["###"],
        messages=[
            {
                "role": "user",
                "content": "List 5 programming languages. Put ### after the list.",
            }
        ],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)

    print("\n")

    message = stream.get_final_message()
    print(f"Stop reason: {message.stop_reason}")
    if message.stop_sequence:
        print(f"Stopped at sequence: {message.stop_sequence}")


def example_streaming_different_providers():
    """Example of streaming with different providers."""
    print("\n=== Streaming with Different Providers ===")

    providers = [
        ("anthropic", "claude-sonnet-4-5-20250929"),
        ("openai", "gpt-4"),
    ]

    prompt = "Count from 1 to 5."

    for provider_name, model in providers:
        print(f"\n{provider_name.capitalize()}: ", end="", flush=True)

        client = Devorbit(
            provider=provider_name,
            api_key=os.environ.get(f"{provider_name.upper()}_API_KEY"),
        )

        with client.messages.stream(
            model=model,
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)

        print()


if __name__ == "__main__":
    # Run synchronous examples
    example_sync_streaming()
    example_sync_streaming_with_context()
    example_streaming_with_stop_sequences()
    example_streaming_different_providers()

    # Run asynchronous examples
    print("\n=== Running Async Examples ===")
    asyncio.run(example_async_streaming())
    # asyncio.run(example_parallel_streaming())  # Uncomment if you have multiple API keys

    print("\n=== All streaming examples completed! ===")
