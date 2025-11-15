"""Tests for planning mode tools."""

from devorbit import (
    cancel_plan,
    enter_planning_mode,
    exit_plan_mode,
    get_current_plan,
    get_planning_status,
    is_planning_active,
)


class TestPlanningMode:
    """Tests for planning mode functionality."""

    def test_planning_mode_lifecycle(self) -> None:
        """Test complete planning mode lifecycle."""
        # Initial state - not active
        assert is_planning_active() is False
        assert get_current_plan() is None

        # Enter planning mode
        enter_planning_mode()
        assert is_planning_active() is True

        # Exit with plan
        plan = "Implement feature X with approach Y"
        result = exit_plan_mode(plan)

        assert result["success"] is True
        assert result["status"] == "approved"
        assert result["plan"] == plan
        assert is_planning_active() is False
        assert get_current_plan() == plan

    def test_exit_plan_mode_success(self) -> None:
        """Test successful plan exit."""
        enter_planning_mode()

        plan = "Add new authentication system using OAuth2"
        result = exit_plan_mode(plan)

        assert result["success"] is True
        assert result["status"] == "approved"
        assert result["plan"] == plan
        assert "message" in result

    def test_exit_plan_mode_empty_plan(self) -> None:
        """Test exiting with empty plan."""
        enter_planning_mode()

        result = exit_plan_mode("")

        assert "error" in result
        assert result["status"] == "rejected"
        assert "empty" in result["error"].lower()

    def test_exit_plan_mode_whitespace_only(self) -> None:
        """Test exiting with whitespace-only plan."""
        enter_planning_mode()

        result = exit_plan_mode("   \n  \t  ")

        assert "error" in result
        assert result["status"] == "rejected"

    def test_cancel_plan(self) -> None:
        """Test cancelling a plan."""
        enter_planning_mode()
        exit_plan_mode("Test plan")

        # Cancel the plan
        result = cancel_plan()

        assert result["status"] == "cancelled"
        assert is_planning_active() is False
        assert get_current_plan() is None

    def test_get_planning_status(self) -> None:
        """Test getting planning status."""
        # Initial status
        status = get_planning_status()
        assert status["is_active"] is False
        assert status["has_plan"] is False

        # After entering planning mode
        enter_planning_mode()
        status = get_planning_status()
        assert status["is_active"] is True

        # After exiting with plan
        plan = "Test plan"
        exit_plan_mode(plan)
        status = get_planning_status()
        assert status["is_active"] is False
        assert status["has_plan"] is True
        assert status["plan"] == plan

    def test_multiple_plan_cycles(self) -> None:
        """Test multiple planning cycles."""
        # First cycle
        enter_planning_mode()
        exit_plan_mode("Plan 1")
        assert get_current_plan() == "Plan 1"

        # Second cycle
        enter_planning_mode()
        exit_plan_mode("Plan 2")
        assert get_current_plan() == "Plan 2"

        # Verify old plan was replaced
        assert get_current_plan() != "Plan 1"

    def test_plan_with_markdown(self) -> None:
        """Test plan with markdown formatting."""
        plan = """
        ## Implementation Plan

        1. **Step 1:** Initialize database connection
        2. **Step 2:** Create migration scripts
        3. **Step 3:** Run tests

        *Expected completion: 2 days*
        """

        enter_planning_mode()
        result = exit_plan_mode(plan)

        assert result["success"] is True
        assert result["plan"] == plan

    def test_exit_without_entering(self) -> None:
        """Test exiting planning mode without entering first."""
        # This should still work but not require active mode
        plan = "Emergency plan"
        result = exit_plan_mode(plan)

        assert result["success"] is True
        assert get_current_plan() == plan

    def test_concurrent_planning_operations(self) -> None:
        """Test handling of rapid planning operations."""
        enter_planning_mode()
        assert is_planning_active() is True

        exit_plan_mode("Plan A")
        assert is_planning_active() is False

        enter_planning_mode()
        assert is_planning_active() is True

        cancel_plan()
        assert is_planning_active() is False
        assert get_current_plan() is None


class TestPlanningToolDefinitions:
    """Tests for planning tool definitions."""

    def test_exit_plan_mode_has_tool_definition(self) -> None:
        """Test that exit_plan_mode has tool definition."""
        assert hasattr(exit_plan_mode, "tool_definition")
        tool_def = exit_plan_mode.tool_definition  # type: ignore[attr-defined]

        assert tool_def["name"] == "exit_plan_mode"
        assert "description" in tool_def
        assert "input_schema" in tool_def
        assert tool_def["input_schema"]["type"] == "object"
        assert "plan" in tool_def["input_schema"]["properties"]

    def test_get_all_planning_tools(self) -> None:
        """Test getting all planning tools."""
        from devorbit import get_all_planning_tools

        tools = get_all_planning_tools()

        assert isinstance(tools, list)
        assert len(tools) > 0
        assert any(tool["name"] == "exit_plan_mode" for tool in tools)
