"""Tests for agent and task management tools."""

from devorbit import (
    cleanup_tasks,
    get_agent_info,
    list_active_tasks,
    list_agent_types,
    task,
    task_cancel,
    task_status,
)


class TestTask:
    """Tests for task tool."""

    def setup_method(self) -> None:
        """Clean up tasks before each test."""
        cleanup_tasks(all_tasks=True)

    def teardown_method(self) -> None:
        """Clean up tasks after each test."""
        cleanup_tasks(all_tasks=True)

    def test_task_launch_general_purpose(self) -> None:
        """Test launching a general-purpose agent."""
        result = task(
            prompt="Analyze the codebase structure",
            subagent_type="general-purpose",
            description="Analyze codebase",
        )

        assert "error" not in result
        assert result["status"] == "running"
        assert result["agent_type"] == "general-purpose"
        assert "task_id" in result
        assert "agent_info" in result

    def test_task_launch_explore_agent(self) -> None:
        """Test launching explore agent."""
        result = task(
            prompt="Find all Python files in src directory",
            subagent_type="explore",
        )

        assert "error" not in result
        assert result["status"] == "running"
        assert result["agent_type"] == "explore"

    def test_task_launch_code_reviewer(self) -> None:
        """Test launching code review agent."""
        result = task(
            prompt="Review the file operations code",
            subagent_type="code-reviewer",
            description="Code review",
        )

        assert "error" not in result
        assert result["agent_type"] == "code-reviewer"

    def test_task_launch_with_model(self) -> None:
        """Test launching task with specific model."""
        result = task(
            prompt="Quick task",
            subagent_type="explore",
            model="haiku",
        )

        assert "error" not in result
        assert "task_id" in result

    def test_task_invalid_agent_type(self) -> None:
        """Test error with invalid agent type."""
        result = task(
            prompt="Test task",
            subagent_type="invalid-agent-type",
        )

        assert "error" in result
        assert "invalid" in result["error"].lower()
        assert "available_types" in result

    def test_task_multiple_agents(self) -> None:
        """Test launching multiple agents."""
        result1 = task("Task 1", subagent_type="explore")
        result2 = task("Task 2", subagent_type="plan")

        assert result1["task_id"] != result2["task_id"]
        assert result1["agent_type"] == "explore"
        assert result2["agent_type"] == "plan"


class TestTaskStatus:
    """Tests for task_status tool."""

    def setup_method(self) -> None:
        """Clean up tasks before each test."""
        cleanup_tasks(all_tasks=True)

    def teardown_method(self) -> None:
        """Clean up tasks after each test."""
        cleanup_tasks(all_tasks=True)

    def test_task_status_basic(self) -> None:
        """Test getting task status."""
        # Launch task
        launch_result = task("Test task", subagent_type="explore")
        task_id = launch_result["task_id"]

        # Get status
        status_result = task_status(task_id)

        assert "error" not in status_result
        assert status_result["task_id"] == task_id
        assert status_result["agent_type"] == "explore"
        assert status_result["status"] in ["pending", "running", "completed", "failed"]

    def test_task_status_nonexistent(self) -> None:
        """Test getting status of nonexistent task."""
        result = task_status("nonexistent-task-id")

        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_task_status_fields(self) -> None:
        """Test that status includes expected fields."""
        launch_result = task("Test", subagent_type="plan")
        task_id = launch_result["task_id"]

        status_result = task_status(task_id)

        assert "task_id" in status_result
        assert "agent_type" in status_result
        assert "status" in status_result
        assert "message_count" in status_result


class TestTaskCancel:
    """Tests for task_cancel tool."""

    def setup_method(self) -> None:
        """Clean up tasks before each test."""
        cleanup_tasks(all_tasks=True)

    def teardown_method(self) -> None:
        """Clean up tasks after each test."""
        cleanup_tasks(all_tasks=True)

    def test_task_cancel_basic(self) -> None:
        """Test cancelling a task."""
        # Launch task
        launch_result = task("Long task", subagent_type="general-purpose")
        task_id = launch_result["task_id"]

        # Cancel task
        cancel_result = task_cancel(task_id)

        assert cancel_result["success"] is True
        assert cancel_result["task_id"] == task_id

        # Verify task is not in active tasks
        active = list_active_tasks()
        assert not any(t["task_id"] == task_id for t in active)

    def test_task_cancel_nonexistent(self) -> None:
        """Test cancelling nonexistent task."""
        result = task_cancel("nonexistent-task-id")

        assert "error" in result
        assert "not found" in result["error"].lower()


class TestAgentInfo:
    """Tests for agent information functions."""

    def test_get_agent_info_valid(self) -> None:
        """Test getting info for valid agent type."""
        info = get_agent_info("explore")

        assert info is not None
        assert "description" in info
        assert "tools" in info
        assert "capabilities" in info

    def test_get_agent_info_invalid(self) -> None:
        """Test getting info for invalid agent type."""
        info = get_agent_info("invalid-type")

        assert info is None

    def test_list_agent_types(self) -> None:
        """Test listing all agent types."""
        types = list_agent_types()

        assert len(types) > 0
        assert "general-purpose" in types
        assert "explore" in types
        assert "plan" in types
        assert "code-reviewer" in types
        assert "test-runner" in types

        # Check structure
        for _agent_type, info in types.items():
            assert "description" in info
            assert "tools" in info
            assert "capabilities" in info


class TestTaskManagement:
    """Tests for task management functions."""

    def setup_method(self) -> None:
        """Clean up tasks before each test."""
        cleanup_tasks(all_tasks=True)

    def teardown_method(self) -> None:
        """Clean up tasks after each test."""
        cleanup_tasks(all_tasks=True)

    def test_list_active_tasks(self) -> None:
        """Test listing active tasks."""
        # Launch tasks
        task("Task 1", subagent_type="explore")
        task("Task 2", subagent_type="plan")

        # List tasks
        active = list_active_tasks()

        assert len(active) == 2
        assert all("task_id" in t for t in active)
        assert all("agent_type" in t for t in active)
        assert all("status" in t for t in active)
        assert all("prompt" in t for t in active)

    def test_cleanup_tasks(self) -> None:
        """Test cleanup function."""
        # Launch and cancel tasks to create completed tasks
        task1 = task("Task 1", subagent_type="explore")
        task2 = task("Task 2", subagent_type="plan")

        task_cancel(task1["task_id"])
        task_cancel(task2["task_id"])

        # Active tasks should be removed by cancel
        active = list_active_tasks()
        assert len(active) == 0

    def test_task_info_structure(self) -> None:
        """Test structure of task info."""
        result = task("Test task with long prompt" * 10, subagent_type="explore")
        task_id = result["task_id"]

        # Get from list
        active = list_active_tasks()
        task_info = next(t for t in active if t["task_id"] == task_id)

        assert "task_id" in task_info
        assert "agent_type" in task_info
        assert "status" in task_info
        assert "prompt" in task_info

        # Prompt should be truncated in list view
        if len("Test task with long prompt" * 10) > 100:
            assert "..." in task_info["prompt"]


class TestAgentTypes:
    """Tests for agent type definitions."""

    def test_all_agent_types_have_required_fields(self) -> None:
        """Test that all agent types have required fields."""
        types = list_agent_types()

        for agent_type, info in types.items():
            assert "description" in info, f"{agent_type} missing description"
            assert "tools" in info, f"{agent_type} missing tools"
            assert "capabilities" in info, f"{agent_type} missing capabilities"

            assert isinstance(info["description"], str)
            assert isinstance(info["tools"], list)
            assert isinstance(info["capabilities"], list)

    def test_explore_agent_has_thoroughness_levels(self) -> None:
        """Test that explore agent has thoroughness levels."""
        info = get_agent_info("explore")

        assert info is not None
        assert "thoroughness_levels" in info
        assert "quick" in info["thoroughness_levels"]
        assert "medium" in info["thoroughness_levels"]
        assert "very thorough" in info["thoroughness_levels"]
