"""Sprint Planning Agent with MCP Support.

This example demonstrates building a sprint planning agent that can interact
with project management tools (Notion, Jira, ClickUp) via MCP (Model Context Protocol).

The agent can:
- Fetch tasks from project management tools
- Create new tasks and user stories
- Update task status
- Plan sprints automatically
- Generate reports

Requirements:
    - pip install devorbit mcp
    - Set up MCP servers for Notion/Jira/ClickUp (see config below)
"""

import asyncio
import os
from datetime import datetime

from devorbit import AsyncDevorbit, MCPManager, ToolExecutor, beta_tool

# ============================================================================
# Example MCP Configuration (.mcp.json)
# ============================================================================
"""
Create a file named .mcp.json in your project root:

{
    "mcpServers": {
        "notion": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@notionhq/mcp-server-notion"],
            "env": {
                "NOTION_API_KEY": "your-notion-api-key"
            }
        },
        "jira": {
            "transport": "stdio",
            "command": "python",
            "args": ["path/to/jira_mcp_server.py"],
            "env": {
                "JIRA_URL": "https://your-domain.atlassian.net",
                "JIRA_EMAIL": "your-email@example.com",
                "JIRA_API_TOKEN": "your-jira-api-token"
            }
        },
        "clickup": {
            "transport": "stdio",
            "command": "node",
            "args": ["path/to/clickup-mcp-server.js"],
            "env": {
                "CLICKUP_API_TOKEN": "your-clickup-token"
            }
        }
    }
}
"""


# ============================================================================
# Custom Tools for Sprint Planning
# ============================================================================


@beta_tool
def calculate_velocity(completed_story_points: int, sprint_days: int) -> dict:
    """Calculate team velocity.

    Args:
        completed_story_points: Total story points completed in the sprint
        sprint_days: Number of days in the sprint
    """
    velocity = completed_story_points / sprint_days if sprint_days > 0 else 0
    return {
        "velocity": velocity,
        "completed_points": completed_story_points,
        "sprint_days": sprint_days,
        "recommendation": "high" if velocity > 5 else "medium" if velocity > 2 else "low",
    }


@beta_tool
def prioritize_tasks(tasks: list, criteria: str = "value") -> dict:
    """Prioritize tasks based on criteria.

    Args:
        tasks: List of task descriptions
        criteria: Prioritization criteria (value, urgency, effort)
    """
    # Simple mock prioritization
    prioritized = sorted(tasks, key=lambda x: len(x))  # Mock sorting
    return {"prioritized_tasks": prioritized, "criteria": criteria, "count": len(tasks)}


@beta_tool
def generate_sprint_summary(sprint_name: str, tasks_completed: int, tasks_total: int) -> dict:
    """Generate a sprint summary report.

    Args:
        sprint_name: Name of the sprint
        tasks_completed: Number of tasks completed
        tasks_total: Total number of tasks
    """
    completion_rate = (tasks_completed / tasks_total * 100) if tasks_total > 0 else 0

    summary = {
        "sprint_name": sprint_name,
        "tasks_completed": tasks_completed,
        "tasks_total": tasks_total,
        "completion_rate": round(completion_rate, 2),
        "status": (
            "excellent"
            if completion_rate >= 90
            else "good" if completion_rate >= 70 else "needs_improvement"
        ),
    }

    return summary


# ============================================================================
# Sprint Planning Agent
# ============================================================================


class SprintPlanningAgent:
    """AI-powered sprint planning agent with MCP support."""

    def __init__(
        self,
        provider: str = "anthropic",
        api_key: str = None,
        mcp_config_path: str = ".mcp.json",
    ):
        """Initialize the sprint planning agent.

        Args:
            provider: LLM provider (anthropic, openai, etc.)
            api_key: API key for the provider
            mcp_config_path: Path to MCP configuration file
        """
        self.client = AsyncDevorbit(provider=provider, api_key=api_key)
        self.mcp_config_path = mcp_config_path
        self.mcp_manager = None
        self.executor = None

    async def setup(self):
        """Set up MCP connections and tool executor."""
        # Load MCP configuration
        self.mcp_manager = MCPManager.from_config_file(self.mcp_config_path)

        # Connect to all MCP servers
        await self.mcp_manager.connect_all()

        print(f"✅ Connected to {len(self.mcp_manager.clients)} MCP servers:")
        for server_name in self.mcp_manager.clients.keys():
            print(f"  - {server_name}")

        # Get available tools
        mcp_tools = await self.mcp_manager.get_all_tools()
        for server_name, tools in mcp_tools.items():
            print(f"  {server_name}: {len(tools)} tools available")

        # Create tool executor with both custom and MCP tools
        custom_tools = {
            "calculate_velocity": calculate_velocity,
            "prioritize_tasks": prioritize_tasks,
            "generate_sprint_summary": generate_sprint_summary,
        }

        self.executor = ToolExecutor(tools=custom_tools, mcp_manager=self.mcp_manager)

    async def cleanup(self):
        """Clean up MCP connections."""
        if self.mcp_manager:
            await self.mcp_manager.disconnect_all()

    async def plan_sprint(
        self,
        sprint_name: str,
        backlog_query: str = "all tasks",
        target_story_points: int = 40,
    ) -> dict:
        """Plan a sprint using AI and MCP tools.

        Args:
            sprint_name: Name of the sprint
            backlog_query: Query to fetch backlog items
            target_story_points: Target story points for the sprint

        Returns:
            Sprint plan details
        """
        messages = [
            {
                "role": "user",
                "content": f"""You are a sprint planning assistant. Help me plan a sprint with the following details:

Sprint Name: {sprint_name}
Target Story Points: {target_story_points}
Backlog Query: {backlog_query}

Please:
1. Fetch backlog items from available project management tools (Notion/Jira/ClickUp)
2. Prioritize tasks based on value and dependencies
3. Select tasks that fit within the target story points
4. Create a sprint plan with the selected tasks
5. Generate a summary report

Use the available MCP tools to interact with project management systems.""",
            }
        ]

        print(f"\n🚀 Planning sprint: {sprint_name}")
        print(f"   Target: {target_story_points} story points")
        print(f"   Backlog query: {backlog_query}\n")

        # Execute tool loop
        response = await self.executor.aexecute_tool_loop(
            client=self.client,
            messages=messages,
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            max_iterations=15,
        )

        # Extract final text
        final_text = ""
        for block in response.content:
            if block.type == "text":
                final_text += block.text

        return {"sprint_name": sprint_name, "plan": final_text, "response": response}

    async def create_task(
        self,
        tool: str,
        title: str,
        description: str,
        story_points: int = 0,
        **kwargs,
    ) -> dict:
        """Create a task in a project management tool via MCP.

        Args:
            tool: Tool name (notion, jira, clickup)
            title: Task title
            description: Task description
            story_points: Story points estimate
            **kwargs: Additional tool-specific parameters

        Returns:
            Created task details
        """
        messages = [
            {
                "role": "user",
                "content": f"""Create a new task in {tool}:

Title: {title}
Description: {description}
Story Points: {story_points}
Additional: {kwargs}

Use the appropriate MCP tool to create this task.""",
            }
        ]

        response = await self.executor.aexecute_tool_loop(
            client=self.client,
            messages=messages,
            model="claude-sonnet-4-5-20250929",
            max_tokens=2048,
            max_iterations=5,
        )

        return {"task_created": True, "response": response}

    async def get_sprint_status(self, sprint_name: str) -> dict:
        """Get current sprint status from all tools.

        Args:
            sprint_name: Name of the sprint

        Returns:
            Sprint status details
        """
        messages = [
            {
                "role": "user",
                "content": f"""Get the status of sprint: {sprint_name}

Please:
1. Query all available project management tools
2. Count completed vs in-progress vs pending tasks
3. Calculate completion percentage
4. Generate a status summary

Use MCP tools to fetch data from Notion, Jira, and/or ClickUp.""",
            }
        ]

        response = await self.executor.aexecute_tool_loop(
            client=self.client,
            messages=messages,
            model="claude-sonnet-4-5-20250929",
            max_tokens=3072,
            max_iterations=10,
        )

        # Extract status
        status_text = ""
        for block in response.content:
            if block.type == "text":
                status_text += block.text

        return {"sprint_name": sprint_name, "status": status_text}


# ============================================================================
# Example Usage
# ============================================================================


async def example_basic_sprint_planning():
    """Example: Basic sprint planning with MCP."""
    print("=" * 70)
    print("Example 1: Basic Sprint Planning with MCP")
    print("=" * 70)

    # Initialize agent
    agent = SprintPlanningAgent(
        provider="anthropic",
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
        mcp_config_path=".mcp.json",
    )

    try:
        # Setup MCP connections
        await agent.setup()

        # Plan a sprint
        result = await agent.plan_sprint(
            sprint_name="Sprint 42",
            backlog_query="priority:high AND status:todo",
            target_story_points=40,
        )

        print("\n📊 Sprint Plan:")
        print(result["plan"])

    finally:
        await agent.cleanup()


async def example_create_tasks_via_mcp():
    """Example: Create tasks using MCP tools."""
    print("\n" + "=" * 70)
    print("Example 2: Create Tasks via MCP")
    print("=" * 70)

    agent = SprintPlanningAgent(
        provider="anthropic",
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
        mcp_config_path=".mcp.json",
    )

    try:
        await agent.setup()

        # Create tasks in different tools
        tasks = [
            {
                "tool": "notion",
                "title": "Implement user authentication",
                "description": "Add OAuth2 authentication flow",
                "story_points": 8,
            },
            {
                "tool": "jira",
                "title": "Fix database migration bug",
                "description": "Schema migration fails on PostgreSQL 14",
                "story_points": 5,
            },
            {
                "tool": "clickup",
                "title": "Update API documentation",
                "description": "Document new endpoints for v2 API",
                "story_points": 3,
            },
        ]

        for task in tasks:
            print(f"\n📝 Creating task in {task['tool']}: {task['title']}")
            result = await agent.create_task(**task)
            print(f"   ✅ Task created successfully")

    finally:
        await agent.cleanup()


async def example_sprint_status():
    """Example: Get sprint status from all tools."""
    print("\n" + "=" * 70)
    print("Example 3: Get Sprint Status")
    print("=" * 70)

    agent = SprintPlanningAgent(
        provider="anthropic",
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
        mcp_config_path=".mcp.json",
    )

    try:
        await agent.setup()

        # Get sprint status
        status = await agent.get_sprint_status("Sprint 42")

        print("\n📈 Sprint Status:")
        print(status["status"])

    finally:
        await agent.cleanup()


async def example_mcp_only():
    """Example: Direct MCP usage without ToolExecutor."""
    print("\n" + "=" * 70)
    print("Example 4: Direct MCP Usage")
    print("=" * 70)

    # Load MCP servers
    mcp = MCPManager.from_config_file(".mcp.json")

    async with mcp:  # Automatically connects and disconnects
        # Get all available tools
        print("\n📦 Available MCP Tools:")
        tools = await mcp.get_all_tools()

        for server_name, server_tools in tools.items():
            print(f"\n  {server_name}:")
            for tool in server_tools:
                print(f"    - {tool['name']}: {tool['description']}")

        # Call a specific tool
        print("\n\n🔧 Calling Notion tool...")
        try:
            result = await mcp.call_tool(
                server_name="notion",
                tool_name="search_pages",
                arguments={"query": "sprint planning"},
            )
            print(f"   Result: {result}")
        except Exception as e:
            print(f"   Error: {e}")


# ============================================================================
# Main
# ============================================================================


async def main():
    """Run all examples."""
    # Check if MCP config exists
    import os.path

    if not os.path.exists(".mcp.json"):
        print("⚠️  WARNING: .mcp.json not found")
        print("\nTo use MCP features, create a .mcp.json file with your MCP server configurations.")
        print("See the docstring at the top of this file for an example configuration.\n")
        print("For now, showing the structure only...\n")

        # Show example configuration structure
        example_mcp_only = """
        async def demo():
            from devorbit import MCPManager, MCPServerConfig

            # Create MCP manager programmatically
            mcp = MCPManager()

            # Add servers
            mcp.add_server(MCPServerConfig(
                name="notion",
                transport="stdio",
                command="npx",
                args=["-y", "@notionhq/mcp-server-notion"],
                env={"NOTION_API_KEY": "your-key"}
            ))

            async with mcp:
                tools = await mcp.get_all_tools()
                print(f"Available tools: {tools}")
        """
        print(example_mcp_only)
        return

    # Run examples
    await example_mcp_only()
    # await example_basic_sprint_planning()
    # await example_create_tasks_via_mcp()
    # await example_sprint_status()

    print("\n" + "=" * 70)
    print("✅ All examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
