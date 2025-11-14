"""Async usage examples for the Devorbit SDK.

This example demonstrates asynchronous operations with the AsyncDevorbit client.
"""

import asyncio
import os

from devorbit import AsyncDevorbit


async def example_basic_async():
    """Basic async example."""
    print("\n=== Basic Async Example ===")

    client = AsyncDevorbit(
        provider="anthropic",
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    message = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Write a haiku about async programming."}],
    )

    print(f"Response: {message.content[0].text}")
    print(f"Usage: {message.usage.input_tokens} in, {message.usage.output_tokens} out")


async def example_parallel_requests():
    """Example of parallel requests to the same provider."""
    print("\n=== Parallel Requests Example ===")

    client = AsyncDevorbit(
        provider="anthropic",
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    prompts = [
        "What is Python?",
        "What is JavaScript?",
        "What is Rust?",
    ]

    # Create tasks for all prompts
    tasks = [
        client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        for prompt in prompts
    ]

    # Execute all tasks in parallel
    responses = await asyncio.gather(*tasks)

    # Print results
    for prompt, response in zip(prompts, responses):
        print(f"\nPrompt: {prompt}")
        print(f"Response: {response.content[0].text[:100]}...")


async def example_multiple_providers_parallel():
    """Example of querying multiple providers in parallel."""
    print("\n=== Multiple Providers Parallel Example ===")

    # Create clients for different providers
    clients = {
        "anthropic": AsyncDevorbit(
            provider="anthropic",
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
        ),
        "openai": AsyncDevorbit(
            provider="openai",
            api_key=os.environ.get("OPENAI_API_KEY"),
        ),
    }

    prompt = "Explain what a REST API is in one sentence."

    # Create tasks for each provider
    tasks = {
        name: client.messages.create(
            model="claude-sonnet-4-5-20250929" if name == "anthropic" else "gpt-4",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        for name, client in clients.items()
    }

    # Execute all tasks and wait for completion
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)

    # Print results
    for (name, _), result in zip(tasks.items(), results):
        if isinstance(result, Exception):
            print(f"\n{name}: Error - {result}")
        else:
            print(f"\n{name}: {result.content[0].text}")


async def example_async_with_timeout():
    """Example of async request with timeout handling."""
    print("\n=== Async with Timeout Example ===")

    client = AsyncDevorbit(
        provider="anthropic",
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
        timeout=30.0,  # 30 second timeout
    )

    try:
        message = await asyncio.wait_for(
            client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=1024,
                messages=[{"role": "user", "content": "Explain quantum computing."}],
            ),
            timeout=10.0,  # Additional 10 second timeout
        )

        print(f"Response: {message.content[0].text[:200]}...")

    except TimeoutError:
        print("Request timed out!")


async def example_async_streaming():
    """Example of async streaming."""
    print("\n=== Async Streaming Example ===")

    client = AsyncDevorbit(
        provider="anthropic",
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    print("Streaming: ", end="", flush=True)

    async with await client.messages.stream(
        model="claude-sonnet-4-5-20250929",
        max_tokens=512,
        messages=[{"role": "user", "content": "Write a short poem about async/await."}],
    ) as stream:
        async for text in stream.text_stream():
            print(text, end="", flush=True)

    print("\n")

    final_message = await stream.get_final_message()
    print(f"Tokens used: {final_message.usage.output_tokens}")


async def example_async_token_counting():
    """Example of async token counting."""
    print("\n=== Async Token Counting Example ===")

    client = AsyncDevorbit(
        provider="anthropic",
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    messages = [
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing well, thank you! How can I help you today?"},
        {"role": "user", "content": "Can you explain what machine learning is?"},
    ]

    token_count = await client.messages.count_tokens(
        model="claude-sonnet-4-5-20250929",
        messages=messages,
    )

    print(f"Estimated input tokens: {token_count.input_tokens}")


async def example_error_handling():
    """Example of error handling in async operations."""
    print("\n=== Async Error Handling Example ===")

    client = AsyncDevorbit(
        provider="anthropic",
        api_key="invalid-key",  # Intentionally invalid
    )

    try:
        await client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=100,
            messages=[{"role": "user", "content": "Hello"}],
        )
    except Exception as e:
        print(f"Caught error: {type(e).__name__}")
        print(f"Error message: {e!s}")


async def example_with_semaphore():
    """Example of rate limiting with semaphore."""
    print("\n=== Rate Limiting with Semaphore Example ===")

    client = AsyncDevorbit(
        provider="anthropic",
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    # Limit to 3 concurrent requests
    semaphore = asyncio.Semaphore(3)

    async def make_request(prompt: str) -> str:
        async with semaphore:
            print(f"Processing: {prompt[:30]}...")
            message = await client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text

    # Create many prompts
    prompts = [f"What is the number {i}?" for i in range(10)]

    # Execute with rate limiting
    results = await asyncio.gather(*[make_request(p) for p in prompts])

    print(f"\nCompleted {len(results)} requests with rate limiting")


async def main():
    """Run all async examples."""
    await example_basic_async()
    await example_parallel_requests()

    # Uncomment if you have multiple provider API keys
    # await example_multiple_providers_parallel()

    await example_async_with_timeout()
    await example_async_streaming()
    await example_async_token_counting()
    await example_error_handling()
    await example_with_semaphore()


if __name__ == "__main__":
    print("=== Running Async Examples ===")
    asyncio.run(main())
    print("\n=== All async examples completed! ===")
