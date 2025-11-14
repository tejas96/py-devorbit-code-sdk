"""Tool helpers examples using @beta_tool decorator.

This example demonstrates the new tool helpers for easy tool definition and
automatic tool execution loops.
"""

import os

from devorbit import Devorbit, ToolExecutor, beta_tool, gather_tools


# ============================================================================
# Example 1: Using @beta_tool decorator
# ============================================================================


@beta_tool
def get_weather(location: str, unit: str = "celsius") -> dict:
    """Get the weather for a location.

    Args:
        location: The city name
        unit: Temperature unit (celsius or fahrenheit)
    """
    # Mock implementation
    return {"location": location, "temperature": 22, "unit": unit, "conditions": "sunny"}


@beta_tool
def calculate(expression: str) -> dict:
    """Calculate a mathematical expression.

    Args:
        expression: The mathematical expression to evaluate
    """
    try:
        result = eval(expression)
        return {"result": result, "expression": expression}
    except Exception as e:
        return {"error": str(e)}


@beta_tool
def search_database(query: str, limit: int = 10) -> dict:
    """Search the database for records.

    Args:
        query: Search query string
        limit: Maximum number of results to return
    """
    # Mock implementation
    return {"query": query, "results": [f"Result {i}" for i in range(limit)], "count": limit}


def example_basic_beta_tool():
    """Example using @beta_tool decorator."""
    print("\n=== Example: @beta_tool decorator ===\n")

    # The decorator automatically creates tool definitions
    print("get_weather tool definition:")
    print(f"  Name: {get_weather.tool_definition['name']}")
    print(f"  Description: {get_weather.tool_definition['description']}")
    print(f"  Schema: {get_weather.tool_definition['input_schema']}")

    # Gather all tools
    tools = [get_weather.tool_definition, calculate.tool_definition]

    client = Devorbit(provider="anthropic", api_key=os.environ.get("ANTHROPIC_API_KEY"))

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        tools=tools,
        messages=[{"role": "user", "content": "What's 15 * 23 and what's the weather in Tokyo?"}],
    )

    print(f"\nModel response stop reason: {response.stop_reason}")

    for block in response.content:
        if block.type == "tool_use":
            print(f"\nTool call: {block.name}")
            print(f"Arguments: {block.input}")

            # Execute the tool
            if block.name == "get_weather":
                result = get_weather(**block.input)
            elif block.name == "calculate":
                result = calculate(**block.input)
            else:
                result = {"error": "Unknown tool"}

            print(f"Result: {result}")


# ============================================================================
# Example 2: Using gather_tools from a class
# ============================================================================


class MyAgentTools:
    """A class containing multiple tools."""

    @beta_tool
    def read_file(self, path: str) -> dict:
        """Read a file from the filesystem.

        Args:
            path: Path to the file
        """
        return {"path": path, "content": "File content here..."}

    @beta_tool
    def write_file(self, path: str, content: str) -> dict:
        """Write content to a file.

        Args:
            path: Path to the file
            content: Content to write
        """
        return {"path": path, "bytes_written": len(content)}

    @beta_tool
    def list_files(self, directory: str = ".") -> dict:
        """List files in a directory.

        Args:
            directory: Directory path
        """
        return {"directory": directory, "files": ["file1.txt", "file2.txt", "file3.txt"]}


def example_gather_tools():
    """Example using gather_tools to collect tools from a class."""
    print("\n=== Example: gather_tools from class ===\n")

    # Create instance and gather tools
    agent_tools = MyAgentTools()
    tools = gather_tools(agent_tools)

    print(f"Found {len(tools)} tools:")
    for tool in tools:
        print(f"  - {tool['name']}: {tool['description']}")


# ============================================================================
# Example 3: Using ToolExecutor for automatic tool loops
# ============================================================================


def example_tool_executor():
    """Example using ToolExecutor for automatic tool execution loops."""
    print("\n=== Example: ToolExecutor automatic tool loop ===\n")

    # Create tools dict
    tools_dict = {
        "get_weather": get_weather,
        "calculate": calculate,
        "search_database": search_database,
    }

    # Create executor
    executor = ToolExecutor(tools_dict)

    client = Devorbit(provider="anthropic", api_key=os.environ.get("ANTHROPIC_API_KEY"))

    # Execute with automatic tool loop
    initial_messages = [
        {
            "role": "user",
            "content": "What's the weather in London? Then calculate 42 * 13. Finally, search for 'python tutorials' and show me 5 results.",
        }
    ]

    print("Starting automatic tool execution loop...\n")

    final_response = executor.execute_tool_loop(
        client=client,
        messages=initial_messages,
        model="claude-sonnet-4-5-20250929",
        max_tokens=2048,
        max_iterations=5,
    )

    print("\nFinal response:")
    for block in final_response.content:
        if block.type == "text":
            print(block.text)

    print(f"\nStop reason: {final_response.stop_reason}")
    print(f"Total tokens: {final_response.usage.input_tokens + final_response.usage.output_tokens}")


# ============================================================================
# Example 4: Complex tool with validation
# ============================================================================


@beta_tool
def create_user(username: str, email: str, age: int) -> dict:
    """Create a new user account.

    Args:
        username: Username for the account
        email: Email address
        age: User's age
    """
    # Validation
    if age < 18:
        return {"error": "User must be at least 18 years old"}

    if "@" not in email:
        return {"error": "Invalid email address"}

    # Mock user creation
    user_id = hash(username) % 10000
    return {"success": True, "user_id": user_id, "username": username, "email": email}


def example_complex_tool():
    """Example with complex tool including validation."""
    print("\n=== Example: Complex tool with validation ===\n")

    tools = [create_user.tool_definition]

    client = Devorbit(provider="anthropic", api_key=os.environ.get("ANTHROPIC_API_KEY"))

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        tools=tools,
        messages=[
            {
                "role": "user",
                "content": "Create a user account with username 'alice123', email 'alice@example.com', and age 25",
            }
        ],
    )

    for block in response.content:
        if block.type == "tool_use":
            print(f"Tool: {block.name}")
            print(f"Input: {block.input}")

            result = create_user(**block.input)
            print(f"Result: {result}")


# ============================================================================
# Example 5: Async tool executor
# ============================================================================


async def example_async_tool_executor():
    """Example using async ToolExecutor."""

    from devorbit import AsyncDevorbit

    print("\n=== Example: Async ToolExecutor ===\n")

    tools_dict = {
        "get_weather": get_weather,
        "calculate": calculate,
    }

    executor = ToolExecutor(tools_dict)

    client = AsyncDevorbit(provider="anthropic", api_key=os.environ.get("ANTHROPIC_API_KEY"))

    initial_messages = [
        {"role": "user", "content": "What's 100 / 5 and what's the weather in Paris?"}
    ]

    final_response = await executor.aexecute_tool_loop(
        client=client,
        messages=initial_messages,
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
    )

    print("Async tool loop completed!")
    for block in final_response.content:
        if block.type == "text":
            print(block.text)


if __name__ == "__main__":
    # Run examples
    example_basic_beta_tool()
    example_gather_tools()
    example_tool_executor()
    example_complex_tool()

    # Uncomment to run async example
    # import asyncio
    # asyncio.run(example_async_tool_executor())

    print("\n=== All tool helper examples completed! ===")
