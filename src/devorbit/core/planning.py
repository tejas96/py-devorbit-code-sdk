"""Planning mode tools for autonomous coding agents.

This module provides planning mode support matching Claude Code's behavior:
- ExitPlanMode: Present plans to user for approval before execution
- Planning state management
"""

from typing import Any

from .tool_helpers import beta_tool


# ============================================================================
# Planning Mode State
# ============================================================================


class PlanningState:
    """Global planning mode state manager."""

    def __init__(self) -> None:
        """Initialize planning state."""
        self.is_active: bool = False
        self.current_plan: str | None = None

    def enter_planning_mode(self) -> None:
        """Enter planning mode for reviewing plans before execution."""
        self.is_active = True
        self.current_plan = None

    def exit_planning_mode(self, plan: str) -> dict[str, Any]:
        """Exit planning mode with approved plan.

        Args:
            plan: The approved plan

        Returns:
            Status dictionary with approval confirmation
        """
        self.current_plan = plan
        self.is_active = False
        return {
            "status": "approved",
            "plan": plan,
            "message": "Plan approved and ready for execution",
        }

    def cancel_plan(self) -> dict[str, Any]:
        """Cancel the current plan without executing.

        Returns:
            Status dictionary with cancellation confirmation
        """
        self.current_plan = None
        self.is_active = False
        return {
            "status": "cancelled",
            "message": "Plan cancelled",
        }

    def get_status(self) -> dict[str, Any]:
        """Get current planning mode status.

        Returns:
            Status dictionary with current state
        """
        return {
            "is_active": self.is_active,
            "has_plan": self.current_plan is not None,
            "plan": self.current_plan,
        }


# Global planning state instance
_planning_state = PlanningState()


# ============================================================================
# ExitPlanMode Tool
# ============================================================================


@beta_tool
def exit_plan_mode(plan: str) -> dict[str, Any]:
    """Exit planning mode after presenting a plan to the user for approval.

    This tool is used when the agent is in planning mode and has finished
    creating a plan. It presents the plan to the user and exits planning mode,
    allowing the agent to proceed with implementation.

    The plan should be concise (1-2 sentences) and clearly describe what
    will be implemented. It should focus on the "why" rather than the "what".

    Args:
        plan: The plan to present to the user (supports markdown formatting)

    Returns:
        Dictionary containing approval status and plan details
    """
    try:
        if not plan or not plan.strip():
            return {
                "error": "Plan cannot be empty",
                "status": "rejected",
            }

        # Exit planning mode with the plan
        result = _planning_state.exit_planning_mode(plan)

        return {
            "success": True,
            "status": result["status"],
            "plan": result["plan"],
            "message": result["message"],
        }

    except Exception as e:
        return {
            "error": f"Failed to exit planning mode: {e!s}",
            "status": "error",
        }


# ============================================================================
# Helper Functions
# ============================================================================


def enter_planning_mode() -> None:
    """Enter planning mode for reviewing plans before execution.

    When in planning mode, the agent should:
    1. Analyze the task and gather context
    2. Create a detailed plan
    3. Use exit_plan_mode to present the plan to the user
    4. Wait for approval before proceeding
    """
    _planning_state.enter_planning_mode()


def cancel_plan() -> dict[str, Any]:
    """Cancel the current plan without executing.

    Returns:
        Status dictionary with cancellation confirmation
    """
    return _planning_state.cancel_plan()


def get_planning_status() -> dict[str, Any]:
    """Get current planning mode status.

    Returns:
        Status dictionary with current state
    """
    return _planning_state.get_status()


def is_planning_active() -> bool:
    """Check if planning mode is currently active.

    Returns:
        True if planning mode is active, False otherwise
    """
    return _planning_state.is_active


def get_current_plan() -> str | None:
    """Get the current approved plan.

    Returns:
        Current plan string or None if no plan exists
    """
    return _planning_state.current_plan


def get_all_planning_tools() -> list[dict[str, Any]]:
    """Get all planning mode tool definitions.

    Returns:
        List of planning tool definitions for use with Devorbit client
    """
    return [
        exit_plan_mode.tool_definition,  # type: ignore[attr-defined]
    ]


# Export tool instances and helpers for direct use
__all__ = [
    "PlanningState",
    "cancel_plan",
    "enter_planning_mode",
    "exit_plan_mode",
    "get_all_planning_tools",
    "get_current_plan",
    "get_planning_status",
    "is_planning_active",
]
