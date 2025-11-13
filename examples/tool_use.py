"""Tool use (function calling) examples for the Devorbit SDK.

This example demonstrates how to use tools/functions with different providers.
"""

import json
import os

from devorbit import Devorbit


def get_weather(location: str, unit: str = "celsius") -> dict:
    """Mock function to get weather for a location."""
    # In a real application, this would call a weather API
    return {
        "location": location,
        "temperature": 22,
        "unit": unit,
        "conditions": "sunny",
        "humidity": 65,
    }


def calculate(expression: str) -> dict:
    """Mock function to calculate a mathematical expression."""
    try:
        result = eval(expression)
        return {"result": result, "expression": expression}
    except Exception as e:
        return {"error": str(e), "expression": expression}


def example_basic_tool_use():
    """Basic tool use example."""
    print("\n=== Basic Tool Use Example ===")

    client = Devorbit(
        provider="anthropic",
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    # Define tools
    tools = [
        {
            "name": "get_weather",
            "description": "Get the current weather for a location",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and country, e.g., 'San Francisco, CA'",
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "The unit for temperature",
                    },
                },
                "required": ["location"],
            },
        }
    ]

    # Initial message
    messages = [{"role": "user", "content": "What's the weather like in Tokyo?"}]

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        tools=tools,
        messages=messages,
    )

    print(f"Stop reason: {response.stop_reason}")

    # Check if the model wants to use a tool
    if response.stop_reason == "tool_use":
        # Extract tool use from response
        tool_use = None
        for block in response.content:
            if block.type == "tool_use":
                tool_use = block
                break

        if tool_use:
            print(f"Model wants to use tool: {tool_use.name}")
            print(f"Tool input: {tool_use.input}")

            # Execute the tool
            if tool_use.name == "get_weather":
                tool_result = get_weather(**tool_use.input)
                print(f"Tool result: {tool_result}")

                # Send tool result back to the model
                messages.append(
                    {"role": "assistant", "content": response.content[0].text or ""}
                )
                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_use.id,
                                "content": json.dumps(tool_result),
                            }
                        ],
                    }
                )

                # Get final response
                final_response = client.messages.create(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=1024,
                    tools=tools,
                    messages=messages,
                )

                print(f"\nFinal response: {final_response.content[0].text}")


def example_multiple_tools():
    """Example with multiple tools."""
    print("\n=== Multiple Tools Example ===")

    client = Devorbit(
        provider="anthropic",
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    # Define multiple tools
    tools = [
        {
            "name": "get_weather",
            "description": "Get the current weather for a location",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                },
                "required": ["location"],
            },
        },
        {
            "name": "calculate",
            "description": "Calculate a mathematical expression",
            "input_schema": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string"},
                },
                "required": ["expression"],
            },
        },
    ]

    messages = [
        {
            "role": "user",
            "content": "What's 15 * 23? Also, what's the weather in Paris?",
        }
    ]

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        tools=tools,
        messages=messages,
    )

    print(f"Stop reason: {response.stop_reason}")

    # Handle multiple tool uses
    if response.stop_reason == "tool_use":
        tool_results = []

        for block in response.content:
            if block.type == "tool_use":
                print(f"\nTool: {block.name}")
                print(f"Input: {block.input}")

                # Execute the appropriate tool
                if block.name == "get_weather":
                    result = get_weather(**block.input)
                elif block.name == "calculate":
                    result = calculate(**block.input)
                else:
                    result = {"error": "Unknown tool"}

                print(f"Result: {result}")

                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    }
                )

        # Send all tool results back
        messages.append({"role": "assistant", "content": response.content[0].text or ""})
        messages.append({"role": "user", "content": tool_results})

        final_response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1024,
            tools=tools,
            messages=messages,
        )

        print(f"\nFinal response: {final_response.content[0].text}")


def example_tool_choice():
    """Example with tool choice control."""
    print("\n=== Tool Choice Example ===")

    client = Devorbit(
        provider="anthropic",
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    tools = [
        {
            "name": "get_weather",
            "description": "Get the current weather for a location",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                },
                "required": ["location"],
            },
        }
    ]

    # Force the model to use a specific tool
    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        tools=tools,
        tool_choice={"type": "tool", "name": "get_weather"},
        messages=[{"role": "user", "content": "Hello"}],
    )

    print(f"Stop reason: {response.stop_reason}")

    for block in response.content:
        if block.type == "tool_use":
            print(f"Forced tool use: {block.name}")
            print(f"Input: {block.input}")


def example_tool_use_with_openai():
    """Example of tool use with OpenAI provider."""
    print("\n=== Tool Use with OpenAI ===")

    client = Devorbit(
        provider="openai",
        api_key=os.environ.get("OPENAI_API_KEY"),
    )

    tools = [
        {
            "name": "get_weather",
            "description": "Get the current weather for a location",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                },
                "required": ["location"],
            },
        }
    ]

    messages = [{"role": "user", "content": "What's the weather in London?"}]

    response = client.messages.create(
        model="gpt-4",
        max_tokens=1024,
        tools=tools,
        messages=messages,
    )

    print(f"Stop reason: {response.stop_reason}")

    if response.stop_reason == "tool_use":
        for block in response.content:
            if block.type == "tool_use":
                print(f"Tool: {block.name}")
                print(f"Input: {block.input}")

                result = get_weather(**block.input)
                print(f"Result: {result}")


if __name__ == "__main__":
    # Run examples
    example_basic_tool_use()
    example_multiple_tools()
    example_tool_choice()

    # Uncomment to try OpenAI
    # example_tool_use_with_openai()

    print("\n=== All tool use examples completed! ===")
