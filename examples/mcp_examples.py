"""Model Context Protocol (MCP) Examples.

This file demonstrates how to use MCP (Model Context Protocol) with the Devorbit SDK
to connect AI agents to external data sources and tools.

MCP is like USB-C for AI - a standardized way to connect AI models to different
data sources and tools (Notion, Jira, databases, file systems, etc.).
"""

import asyncio
import os
from pathlib import Path

from devorbit import (
    AsyncDevorbit,
    MCPClient,
    MCPManager,
    MCPServerConfig,
    ToolExecutor,
    load_mcp_config,
)


# ============================================================================
# Example 1: Basic MCP Client Usage
# ============================================================================


async def example_basic_mcp_client():
    """Example: Connect to a single MCP server and use its tools."""
    print("\n=== Example 1: Basic MCP Client ===\n")

    # Configure MCP server (example with a file system server)
    config = MCPServerConfig(
        name="filesystem",
        transport="stdio",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
    )

    # Create and connect to MCP server
    client = MCPClient(config)

    async with client:  # Automatically connects and disconnects
        # List available tools
        tools = await client.list_tools()
        print(f"Available tools: {len(tools)}")
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}")

        # List resources
        resources = await client.list_resources()
        print(f"\nAvailable resources: {len(resources)}")
        for resource in resources:
            print(f"  - {resource['uri']}: {resource['name']}")

        # Call a tool
        if tools:
            print(f"\nCalling tool: {tools[0]['name']}")
            result = await client.call_tool(tools[0]["name"], arguments={})
            print(f"Result: {result}")


# ============================================================================
# Example 2: MCP Manager with Multiple Servers
# ============================================================================


async def example_mcp_manager():
    """Example: Manage multiple MCP servers."""
    print("\n=== Example 2: MCP Manager with Multiple Servers ===\n")

    # Create MCP manager
    manager = MCPManager()

    # Add multiple servers programmatically
    manager.add_server(
        MCPServerConfig(
            name="filesystem",
            transport="stdio",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
        )
    )

    manager.add_server(
        MCPServerConfig(
            name="memory",
            transport="stdio",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-memory"],
        )
    )

    # Connect to all servers
    async with manager:
        # Get tools from all servers
        all_tools = await manager.get_all_tools()

        for server_name, tools in all_tools.items():
            print(f"\n{server_name} server:")
            print(f"  Tools: {len(tools)}")
            for tool in tools:
                print(f"    - {tool['name']}")

        # Get all tools as a flat list (with server prefixes)
        flat_tools = await manager.get_all_tools_flat(prefix_with_server=True)
        print(f"\nTotal tools across all servers: {len(flat_tools)}")


# ============================================================================
# Example 3: Loading MCP Configuration from File
# ============================================================================


async def example_config_file():
    """Example: Load MCP servers from configuration file."""
    print("\n=== Example 3: Loading from Config File ===\n")

    # Create example config file
    config_content = """{
    "mcpServers": {
        "filesystem": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
        },
        "memory": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-memory"]
        }
    }
}"""

    # Write config file
    config_path = Path(".mcp.example.json")
    config_path.write_text(config_content)

    try:
        # Load from config file
        manager = MCPManager.from_config_file(config_path)

        async with manager:
            print(f"Loaded {len(manager.clients)} servers from config:")
            for name in manager.clients.keys():
                print(f"  - {name}")

            # Get all tools
            tools = await manager.get_all_tools()
            for server, server_tools in tools.items():
                print(f"\n{server}: {len(server_tools)} tools")

    finally:
        # Clean up
        if config_path.exists():
            config_path.unlink()


# ============================================================================
# Example 4: Using MCP with ToolExecutor
# ============================================================================


async def example_mcp_with_tool_executor():
    """Example: Integrate MCP tools with ToolExecutor for AI agents."""
    print("\n=== Example 4: MCP with ToolExecutor ===\n")

    # Create MCP manager
    manager = MCPManager()
    manager.add_server(
        MCPServerConfig(
            name="memory",
            transport="stdio",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-memory"],
        )
    )

    # Connect to MCP servers
    await manager.connect_all()

    try:
        # Create tool executor with MCP support
        executor = ToolExecutor(mcp_manager=manager)

        # Create AI client
        client = AsyncDevorbit(
            provider="anthropic",
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
        )

        # Execute agent task using MCP tools
        messages = [
            {
                "role": "user",
                "content": "Store the following information: 'Project deadline is March 15, 2025'. Then retrieve all stored information.",
            }
        ]

        print("Running agent with MCP tools...\n")

        response = await executor.aexecute_tool_loop(
            client=client,
            messages=messages,
            model="claude-sonnet-4-5-20250929",
            max_tokens=2048,
            max_iterations=10,
        )

        # Print agent's final response
        for block in response.content:
            if block.type == "text":
                print(f"Agent: {block.text}")

    finally:
        await manager.disconnect_all()


# ============================================================================
# Example 5: Custom Tools + MCP Tools Together
# ============================================================================


async def example_mixed_tools():
    """Example: Use custom tools and MCP tools together."""
    print("\n=== Example 5: Custom Tools + MCP Tools ===\n")

    from devorbit import beta_tool

    # Define custom tools
    @beta_tool
    def calculate_days_until(date_str: str) -> dict:
        """Calculate days until a date.

        Args:
            date_str: Date in YYYY-MM-DD format
        """
        from datetime import datetime

        target = datetime.strptime(date_str, "%Y-%m-%d")
        today = datetime.now()
        days = (target - today).days

        return {"days_until": days, "date": date_str, "is_past": days < 0}

    # Create MCP manager
    manager = MCPManager()
    manager.add_server(
        MCPServerConfig(
            name="memory",
            transport="stdio",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-memory"],
        )
    )

    await manager.connect_all()

    try:
        # Create executor with both custom and MCP tools
        custom_tools = {"calculate_days_until": calculate_days_until}

        executor = ToolExecutor(tools=custom_tools, mcp_manager=manager)

        # Create AI client
        client = AsyncDevorbit(
            provider="anthropic",
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
        )

        # Agent can now use both custom tools and MCP tools
        messages = [
            {
                "role": "user",
                "content": """Store this information: 'Product launch date: 2025-06-15'
                Then calculate how many days until that date.""",
            }
        ]

        print("Running agent with mixed tools...\n")

        response = await executor.aexecute_tool_loop(
            client=client,
            messages=messages,
            model="claude-sonnet-4-5-20250929",
            max_tokens=2048,
        )

        for block in response.content:
            if block.type == "text":
                print(f"Agent: {block.text}")

    finally:
        await manager.disconnect_all()


# ============================================================================
# Example 6: Auto-loading MCP Config
# ============================================================================


async def example_auto_load_config():
    """Example: Automatically load MCP config from standard locations."""
    print("\n=== Example 6: Auto-loading MCP Config ===\n")

    # This searches for config in:
    # 1. .mcp.json (project-scoped)
    # 2. .claude/settings.local.json (project-specific)
    # 3. ~/.claude/settings.local.json (user-specific)

    manager = load_mcp_config(project_dir=".")

    if manager:
        print("✅ MCP configuration found and loaded")

        async with manager:
            servers = list(manager.clients.keys())
            print(f"Servers: {', '.join(servers)}")

            tools = await manager.get_all_tools()
            total_tools = sum(len(t) for t in tools.values())
            print(f"Total tools available: {total_tools}")
    else:
        print("⚠️  No MCP configuration found")
        print("Create .mcp.json in your project directory to use MCP")


# ============================================================================
# Example 7: Working with Notion MCP Server
# ============================================================================


async def example_notion_mcp():
    """Example: Using Notion via MCP (requires Notion API key)."""
    print("\n=== Example 7: Notion MCP Integration ===\n")

    notion_api_key = os.environ.get("NOTION_API_KEY")
    if not notion_api_key:
        print("⚠️  Set NOTION_API_KEY environment variable to run this example")
        return

    # Configure Notion MCP server
    config = MCPServerConfig(
        name="notion",
        transport="stdio",
        command="npx",
        args=["-y", "@notionhq/mcp-server-notion"],
        env={"NOTION_API_KEY": notion_api_key},
    )

    client = MCPClient(config)

    async with client:
        # List available Notion tools
        tools = await client.list_tools()
        print(f"Notion MCP tools ({len(tools)}):")
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}")

        # Example: Search Notion pages
        # (Exact tool names depend on the Notion MCP server implementation)
        # result = await client.call_tool("search_pages", {"query": "project"})
        # print(f"\nSearch results: {result}")


# ============================================================================
# Example 8: Error Handling with MCP
# ============================================================================


async def example_mcp_error_handling():
    """Example: Proper error handling with MCP."""
    print("\n=== Example 8: MCP Error Handling ===\n")

    manager = MCPManager()

    # Add a server that might fail
    manager.add_server(
        MCPServerConfig(
            name="test_server",
            transport="stdio",
            command="nonexistent_command",  # This will fail
            args=[],
        )
    )

    try:
        await manager.connect_all()
    except Exception as e:
        print(f"❌ Connection failed (expected): {type(e).__name__}")
        print(f"   Message: {e!s}")

    # Clean approach: try connecting to each server individually
    print("\n✅ Better approach - individual server connection:")

    manager2 = MCPManager()
    manager2.add_server(
        MCPServerConfig(
            name="memory",
            transport="stdio",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-memory"],
        )
    )

    # Connect with error handling
    for name, client in manager2.clients.items():
        try:
            await client.connect()
            print(f"   ✓ Connected to {name}")
        except Exception as e:
            print(f"   ✗ Failed to connect to {name}: {e}")

    # Disconnect from successfully connected servers
    for name, client in manager2.clients.items():
        if client.session:
            await client.disconnect()


# ============================================================================
# Main
# ============================================================================


async def main():
    """Run MCP examples."""
    print("=" * 70)
    print("Model Context Protocol (MCP) Examples")
    print("=" * 70)

    # Check requirements
    try:
        import mcp

        print("✅ MCP package is installed")
    except ImportError:
        print("❌ MCP package not installed")
        print("   Install with: pip install mcp")
        return

    # Run examples
    examples = [
        ("Basic MCP Client", example_basic_mcp_client),
        ("MCP Manager", example_mcp_manager),
        ("Config File Loading", example_config_file),
        ("Auto-load Config", example_auto_load_config),
        ("Error Handling", example_mcp_error_handling),
        # ("MCP with ToolExecutor", example_mcp_with_tool_executor),  # Requires API key
        # ("Mixed Tools", example_mixed_tools),  # Requires API key
        # ("Notion MCP", example_notion_mcp),  # Requires Notion API key
    ]

    for name, example_func in examples:
        try:
            await example_func()
        except Exception as e:
            print(f"\n❌ Example '{name}' failed: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 70)
    print("✅ MCP Examples Completed")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
