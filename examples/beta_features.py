"""Beta features examples.

This example demonstrates:
- Prompt caching
- Extended thinking
- PDF support
- Built-in tools (computer use, bash, text editor)
- Beta namespace usage
"""

import base64
import os

from devorbit import (
    BASH_TOOL,
    COMPUTER_USE_TOOL,
    TEXT_EDITOR_TOOL,
    Devorbit,
    create_bash_tool,
    create_computer_use_tool,
    create_text_editor_tool,
    get_all_builtin_tools,
)


# ============================================================================
# Example 1: Prompt Caching
# ============================================================================


def example_prompt_caching():
    """Example using prompt caching to reduce costs."""
    print("\n=== Example: Prompt Caching ===\n")

    client = Devorbit(provider="anthropic", api_key=os.environ.get("ANTHROPIC_API_KEY"))

    # Long system prompt with caching
    long_system_prompt = """You are an expert Python developer with deep knowledge of:
    - Python 3.12+ features
    - Type hints and mypy
    - Async programming
    - FastAPI and web frameworks
    - SQLAlchemy and databases
    - pytest and testing
    - Docker and deployment

    [... imagine this is a very long prompt with company context, coding standards, etc ...]

    Always provide detailed, well-documented code with type hints.
    """

    # Use beta.messages.create with cache control
    response = client.beta.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": long_system_prompt,
                "cache_control": {"type": "ephemeral"},  # Cache this prompt!
            }
        ],
        messages=[{"role": "user", "content": "Write a function to validate an email address."}],
    )

    print("First request (creates cache):")
    print(f"  Input tokens: {response.usage.input_tokens}")
    print(f"  Cache creation tokens: {response.usage.cache_creation_input_tokens}")
    print(f"  Output tokens: {response.usage.output_tokens}")

    # Second request will use cached prompt
    response2 = client.beta.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": long_system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": "Write a function to parse a URL."}],
    )

    print("\nSecond request (uses cache):")
    print(f"  Input tokens: {response2.usage.input_tokens}")
    print(f"  Cache read tokens: {response2.usage.cache_read_input_tokens}")
    print(f"  Output tokens: {response2.usage.output_tokens}")


# ============================================================================
# Example 2: Extended Thinking
# ============================================================================


def example_extended_thinking():
    """Example using extended thinking for complex reasoning."""
    print("\n=== Example: Extended Thinking ===\n")

    client = Devorbit(provider="anthropic", api_key=os.environ.get("ANTHROPIC_API_KEY"))

    # Extended thinking is automatically enabled for compatible models
    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": "Design a distributed caching system that handles 1 million requests per second. Consider scalability, consistency, and failure modes.",
            }
        ],
    )

    # Check for thinking blocks in response
    for block in response.content:
        if block.type == "thinking":
            print(f"Model's thinking process:\n{block.thinking}\n")
        elif block.type == "text":
            print(f"Final answer:\n{block.text}\n")


# ============================================================================
# Example 3: PDF Support
# ============================================================================


def example_pdf_support():
    """Example using PDF document inputs."""
    print("\n=== Example: PDF Support ===\n")

    # NOTE: You need to provide an actual PDF file
    # pdf_path = "example.pdf"

    # Mock example - replace with actual PDF
    # with open(pdf_path, "rb") as f:
    #     pdf_data = base64.b64encode(f.read()).decode("utf-8")

    pdf_data = "..."  # Your base64 PDF data here

    client = Devorbit(provider="anthropic", api_key=os.environ.get("ANTHROPIC_API_KEY"))

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Summarize this PDF document."},
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_data,
                        },
                    },
                ],
            }
        ],
    )

    print(f"PDF summary: {response.content[0].text}")


# ============================================================================
# Example 4: Built-in Tools - Computer Use
# ============================================================================


def example_computer_use_tool():
    """Example using computer use tool (requires beta access)."""
    print("\n=== Example: Computer Use Tool ===\n")

    # Create computer use tool
    computer_tool = create_computer_use_tool(
        display_width_px=1920, display_height_px=1080, display_number=1
    )

    # Or use the constant
    # computer_tool = COMPUTER_USE_TOOL

    print(f"Computer use tool: {computer_tool}")

    client = Devorbit(provider="anthropic", api_key=os.environ.get("ANTHROPIC_API_KEY"))

    # Note: Computer use requires special setup and beta access
    # This is just a structural example
    response = client.beta.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        tools=[computer_tool],
        messages=[
            {"role": "user", "content": "Open a web browser and navigate to example.com"}
        ],
    )

    print(f"Response: {response}")


# ============================================================================
# Example 5: Built-in Tools - Bash
# ============================================================================


def example_bash_tool():
    """Example using bash tool."""
    print("\n=== Example: Bash Tool ===\n")

    bash_tool = create_bash_tool()
    # Or: bash_tool = BASH_TOOL

    print(f"Bash tool: {bash_tool}")

    client = Devorbit(provider="anthropic", api_key=os.environ.get("ANTHROPIC_API_KEY"))

    response = client.beta.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        tools=[bash_tool],
        messages=[{"role": "user", "content": "List all files in the current directory"}],
    )

    print("Bash tool example (structure):")
    for block in response.content:
        print(f"  {block.type}: {block}")


# ============================================================================
# Example 6: Built-in Tools - Text Editor
# ============================================================================


def example_text_editor_tool():
    """Example using text editor tool."""
    print("\n=== Example: Text Editor Tool ===\n")

    editor_tool = create_text_editor_tool()
    # Or: editor_tool = TEXT_EDITOR_TOOL

    print(f"Text editor tool: {editor_tool}")

    client = Devorbit(provider="anthropic", api_key=os.environ.get("ANTHROPIC_API_KEY"))

    response = client.beta.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        tools=[editor_tool],
        messages=[
            {
                "role": "user",
                "content": "Create a new file called hello.py with a simple print statement",
            }
        ],
    )

    print("Text editor tool example:")
    for block in response.content:
        if block.type == "tool_use":
            print(f"  Tool: {block.name}")
            print(f"  Input: {block.input}")


# ============================================================================
# Example 7: All Built-in Tools Together
# ============================================================================


def example_all_builtin_tools():
    """Example using all built-in tools together."""
    print("\n=== Example: All Built-in Tools ===\n")

    # Get all built-in tools at once
    tools = get_all_builtin_tools(
        include_computer=False,  # Computer use requires special setup
        include_bash=True,
        include_editor=True,
    )

    print(f"Loaded {len(tools)} built-in tools:")
    for tool in tools:
        print(f"  - {tool['name']} ({tool['type']})")

    client = Devorbit(provider="anthropic", api_key=os.environ.get("ANTHROPIC_API_KEY"))

    response = client.beta.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2048,
        tools=tools,
        messages=[
            {
                "role": "user",
                "content": "Create a Python script that prints 'Hello World' and then execute it",
            }
        ],
    )

    print("\nAgent response:")
    for block in response.content:
        print(f"  {block.type}: {getattr(block, 'text', getattr(block, 'name', ''))}")


# ============================================================================
# Example 8: Combining Features
# ============================================================================


def example_combining_features():
    """Example combining multiple beta features."""
    print("\n=== Example: Combining Beta Features ===\n")

    client = Devorbit(provider="anthropic", api_key=os.environ.get("ANTHROPIC_API_KEY"))

    # Combine:
    # - Prompt caching
    # - Built-in tools
    # - Extended thinking

    cached_context = """You are an AI assistant helping with software development.
    You have access to bash and text editor tools.

    Company coding standards:
    - Use Python 3.12+
    - Always include type hints
    - Write tests for all functions
    - Use meaningful variable names

    [... long company context ...]
    """

    tools = get_all_builtin_tools(include_computer=False, include_bash=True, include_editor=True)

    response = client.beta.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2048,
        system=[
            {
                "type": "text",
                "text": cached_context,
                "cache_control": {"type": "ephemeral"},  # Cache the context
            }
        ],
        tools=tools,  # Provide built-in tools
        messages=[
            {
                "role": "user",
                "content": "Create a Python function to calculate Fibonacci numbers, write it to fib.py, and test it",
            }
        ],
    )

    print("Combined features response:")
    print(f"  Stop reason: {response.stop_reason}")
    print(f"  Cache tokens: {response.usage.cache_creation_input_tokens or 0}")
    print(f"  Total tokens: {response.usage.input_tokens + response.usage.output_tokens}")


if __name__ == "__main__":
    print("=== Beta Features Examples ===\n")
    print("Note: Some features require beta access from the provider")
    print("=" * 60)

    # Run examples (uncomment to execute)
    # example_prompt_caching()
    # example_extended_thinking()
    # example_pdf_support()
    # example_bash_tool()
    # example_text_editor_tool()
    # example_all_builtin_tools()
    # example_combining_features()

    print("\n=== Examples defined! ===")
    print("Uncomment the examples you want to run.")
    print("Some features may require beta access from your provider.")
