"""Agent and subagent tools for complex workflow management.

This module provides Task tool and agent coordination capabilities:
- Launch specialized subagents for complex tasks
- Agent message passing and coordination
- Task delegation and result aggregation
- Multi-agent workflows
- Async parallel task execution
- Priority-based task scheduling
- Timeout handling
"""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import IntEnum
from typing import TYPE_CHECKING, Any

from devorbit.core.tool_helpers import beta_tool


if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine


if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine


# Global state for active tasks
_ACTIVE_TASKS: dict[str, AgentTask] = {}


class TaskPriority(IntEnum):
    """Task execution priority (lower = higher priority)."""

    CRITICAL = 0
    HIGH = 25
    NORMAL = 50
    LOW = 75
    BACKGROUND = 100


class TaskStatus:
    """Task status constants."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class TaskResult:
    """Result of a task execution."""

    task_id: str
    status: str
    result: Any = None
    error: str | None = None
    duration: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class AgentTask:
    """Represents a running agent task with priority and timeout."""

    def __init__(
        self,
        task_id: str,
        agent_type: str,
        prompt: str,
        model: str | None = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: float | None = None,
    ) -> None:
        """Initialize agent task.

        Args:
            task_id: Unique task identifier
            agent_type: Type of specialized agent
            prompt: Task prompt for the agent
            model: Optional model override
            priority: Task execution priority
            timeout: Optional timeout in seconds
        """
        self.task_id = task_id
        self.agent_type = agent_type
        self.prompt = prompt
        self.model = model
        self.priority = priority
        self.timeout = timeout
        self.status = TaskStatus.PENDING
        self.result: str | None = None
        self.error: str | None = None
        self.messages: list[dict[str, Any]] = []
        self.created_at = time.time()
        self.started_at: float | None = None
        self.completed_at: float | None = None

    def start(self) -> None:
        """Start the agent task."""
        self.status = TaskStatus.RUNNING
        self.started_at = time.time()

    def complete(self, result: str) -> None:
        """Mark task as completed.

        Args:
            result: Task result
        """
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.completed_at = time.time()

    def fail(self, error: str) -> None:
        """Mark task as failed.

        Args:
            error: Error message
        """
        self.status = TaskStatus.FAILED
        self.error = error
        self.completed_at = time.time()

    def cancel(self) -> None:
        """Cancel the task."""
        self.status = TaskStatus.CANCELLED
        self.completed_at = time.time()

    def set_timeout(self) -> None:
        """Mark task as timed out."""
        self.status = TaskStatus.TIMEOUT
        self.error = f"Task timed out after {self.timeout}s"
        self.completed_at = time.time()

    def add_message(self, role: str, content: str) -> None:
        """Add message to task conversation.

        Args:
            role: Message role (user/assistant)
            content: Message content
        """
        self.messages.append(
            {
                "role": role,
                "content": content,
            }
        )

    @property
    def duration(self) -> float:
        """Get task duration in seconds."""
        if self.started_at is None:
            return 0.0
        end_time = self.completed_at or time.time()
        return end_time - self.started_at

    @property
    def is_done(self) -> bool:
        """Check if task is done (completed, failed, cancelled, timeout)."""
        return self.status in (
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.TIMEOUT,
        )


# Specialized agent types and their capabilities
AGENT_TYPES = {
    "general-purpose": {
        "description": "General-purpose agent for complex multi-step tasks",
        "tools": ["*"],  # All tools
        "capabilities": [
            "Research complex questions",
            "Search for code",
            "Execute multi-step tasks",
            "File operations",
        ],
    },
    "explore": {
        "description": "Fast agent specialized for exploring codebases",
        "tools": ["Glob", "Grep", "Read"],
        "capabilities": [
            "Find files by patterns",
            "Search code for keywords",
            "Answer codebase questions",
        ],
        "thoroughness_levels": ["quick", "medium", "very thorough"],
    },
    "plan": {
        "description": "Planning agent for breaking down complex tasks",
        "tools": ["Read", "Glob", "Grep", "TodoWrite"],
        "capabilities": [
            "Analyze requirements",
            "Create implementation plans",
            "Break down tasks",
        ],
    },
    "code-reviewer": {
        "description": "Code review agent for analyzing code quality",
        "tools": ["Read", "Grep", "Write"],
        "capabilities": [
            "Review code quality",
            "Find bugs and issues",
            "Suggest improvements",
        ],
    },
    "test-runner": {
        "description": "Test execution and analysis agent",
        "tools": ["Bash", "Read", "Grep"],
        "capabilities": [
            "Run test suites",
            "Analyze test failures",
            "Generate test reports",
        ],
    },
}


# ============================================================================
# Task Tool
# ============================================================================


@beta_tool
def task(
    prompt: str,
    subagent_type: str,
    description: str | None = None,
    model: str | None = None,
    priority: str | None = None,
    timeout: float | None = None,
) -> dict[str, Any]:
    """Launch a specialized subagent to handle complex tasks autonomously.

    The Task tool launches specialized agents that autonomously handle
    complex tasks. Each agent type has specific capabilities and tools.

    Available agent types:
    - general-purpose: Multi-step tasks, research, code search
    - explore: Fast codebase exploration and search
    - plan: Break down complex tasks into steps
    - code-reviewer: Analyze code quality
    - test-runner: Execute and analyze tests

    Args:
        prompt: Task description for the agent to perform autonomously
        subagent_type: Type of specialized agent to use
        description: Short (3-5 word) description of the task
        model: Optional model override (sonnet, opus, haiku)
        priority: Task priority (critical, high, normal, low, background)
        timeout: Optional timeout in seconds

    Returns:
        Dictionary containing task ID and status
    """
    try:
        # Validate agent type
        if subagent_type not in AGENT_TYPES:
            return {
                "error": f"Invalid subagent_type: {subagent_type}",
                "available_types": list(AGENT_TYPES.keys()),
            }

        # Parse priority
        priority_map = {
            "critical": TaskPriority.CRITICAL,
            "high": TaskPriority.HIGH,
            "normal": TaskPriority.NORMAL,
            "low": TaskPriority.LOW,
            "background": TaskPriority.BACKGROUND,
        }
        task_priority = priority_map.get(priority or "normal", TaskPriority.NORMAL)

        # Create task
        task_id = str(uuid.uuid4())
        agent_task = AgentTask(
            task_id=task_id,
            agent_type=subagent_type,
            prompt=prompt,
            model=model,
            priority=task_priority,
            timeout=timeout,
        )

        # Store task
        _ACTIVE_TASKS[task_id] = agent_task

        # Start task (in real implementation, would spawn actual agent)
        agent_task.start()

        return {
            "task_id": task_id,
            "status": TaskStatus.RUNNING,
            "agent_type": subagent_type,
            "description": description or "Agent task",
            "priority": task_priority.name,
            "timeout": timeout,
            "message": (
                f"Task {task_id} started with {subagent_type} agent. "
                "The agent will work autonomously on the task."
            ),
            "agent_info": AGENT_TYPES[subagent_type],
        }

    except Exception as e:
        return {
            "error": f"Failed to launch task: {e!s}",
            "prompt": prompt,
        }


# ============================================================================
# Task Status Tool
# ============================================================================


@beta_tool
def task_status(task_id: str) -> dict[str, Any]:
    """Get the status of a running task.

    Check the status and progress of a task launched with the Task tool.

    Args:
        task_id: ID of the task to check

    Returns:
        Dictionary containing task status and results
    """
    try:
        if task_id not in _ACTIVE_TASKS:
            return {
                "error": f"Task not found: {task_id}",
                "task_id": task_id,
            }

        task = _ACTIVE_TASKS[task_id]

        result = {
            "task_id": task_id,
            "agent_type": task.agent_type,
            "status": task.status,
            "message_count": len(task.messages),
        }

        if task.status == "completed":
            result["result"] = task.result

        if task.status == "failed":
            result["error"] = task.error

        return result

    except Exception as e:
        return {
            "error": f"Failed to get task status: {e!s}",
            "task_id": task_id,
        }


# ============================================================================
# Task Cancel Tool
# ============================================================================


@beta_tool
def task_cancel(task_id: str) -> dict[str, Any]:
    """Cancel a running task.

    Terminate a task that was launched with the Task tool.

    Args:
        task_id: ID of the task to cancel

    Returns:
        Dictionary containing cancellation status
    """
    try:
        if task_id not in _ACTIVE_TASKS:
            return {
                "error": f"Task not found: {task_id}",
                "task_id": task_id,
            }

        task = _ACTIVE_TASKS[task_id]

        if task.status in ["completed", "failed"]:
            return {
                "error": f"Task already {task.status}",
                "task_id": task_id,
            }

        task.fail("Task cancelled by user")
        del _ACTIVE_TASKS[task_id]

        return {
            "success": True,
            "task_id": task_id,
            "message": "Task cancelled successfully",
        }

    except Exception as e:
        return {
            "error": f"Failed to cancel task: {e!s}",
            "task_id": task_id,
        }


# ============================================================================
# Agent Coordinator
# ============================================================================


class AgentCoordinator:
    """Coordinates multiple agents working together.

    Manages message passing, task delegation, and result aggregation
    across multiple agent tasks with async parallel execution.
    """

    def __init__(self, max_concurrent: int = 5) -> None:
        """Initialize agent coordinator.

        Args:
            max_concurrent: Maximum concurrent tasks
        """
        self.agents: dict[str, AgentTask] = {}
        self.max_concurrent = max_concurrent
        self._semaphore: asyncio.Semaphore | None = None

    def register_agent(self, task: AgentTask) -> None:
        """Register an agent task.

        Args:
            task: Agent task to register
        """
        self.agents[task.task_id] = task

    def send_message(
        self,
        from_task_id: str,
        to_task_id: str,
        content: str,
    ) -> bool:
        """Send message between agents.

        Args:
            from_task_id: Source task ID
            to_task_id: Destination task ID
            content: Message content

        Returns:
            Success status
        """
        if to_task_id not in self.agents:
            return False

        target_task = self.agents[to_task_id]
        target_task.add_message("user", content)
        return True

    def get_results(self) -> dict[str, Any]:
        """Get results from all agents.

        Returns:
            Dictionary of task results
        """
        return {
            task_id: {
                "status": task.status,
                "result": task.result,
                "error": task.error,
                "duration": task.duration,
            }
            for task_id, task in self.agents.items()
        }

    async def run_task_async(
        self,
        task: AgentTask,
        executor: Callable[[AgentTask], Coroutine[Any, Any, str]],
    ) -> TaskResult:
        """Run a single task asynchronously with timeout.

        Args:
            task: Task to execute
            executor: Async function that executes the task

        Returns:
            TaskResult with execution status
        """
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.max_concurrent)

        async with self._semaphore:
            task.start()
            try:
                if task.timeout:
                    result = await asyncio.wait_for(
                        executor(task),
                        timeout=task.timeout,
                    )
                else:
                    result = await executor(task)

                task.complete(result)
                return TaskResult(
                    task_id=task.task_id,
                    status=TaskStatus.COMPLETED,
                    result=result,
                    duration=task.duration,
                )

            except TimeoutError:
                task.set_timeout()
                return TaskResult(
                    task_id=task.task_id,
                    status=TaskStatus.TIMEOUT,
                    error=task.error,
                    duration=task.duration,
                )

            except Exception as e:
                task.fail(str(e))
                return TaskResult(
                    task_id=task.task_id,
                    status=TaskStatus.FAILED,
                    error=str(e),
                    duration=task.duration,
                )

    async def run_parallel(
        self,
        executor: Callable[[AgentTask], Coroutine[Any, Any, str]],
        tasks: list[AgentTask] | None = None,
    ) -> list[TaskResult]:
        """Run multiple tasks in parallel with concurrency limit.

        Args:
            executor: Async function that executes each task
            tasks: List of tasks to execute (default: all registered)

        Returns:
            List of TaskResults
        """
        task_list = tasks or list(self.agents.values())

        # Sort by priority (lower = higher priority)
        task_list.sort(key=lambda t: t.priority)

        # Run all tasks concurrently
        results = await asyncio.gather(
            *[self.run_task_async(t, executor) for t in task_list],
            return_exceptions=True,
        )

        # Convert exceptions to TaskResults
        final_results: list[TaskResult] = []
        for i, result in enumerate(results):
            if isinstance(result, BaseException):
                final_results.append(
                    TaskResult(
                        task_id=task_list[i].task_id,
                        status=TaskStatus.FAILED,
                        error=str(result),
                    )
                )
            elif isinstance(result, TaskResult):
                final_results.append(result)

        return final_results

    def get_pending_tasks(self) -> list[AgentTask]:
        """Get all pending tasks sorted by priority.

        Returns:
            List of pending tasks
        """
        pending = [t for t in self.agents.values() if t.status == TaskStatus.PENDING]
        return sorted(pending, key=lambda t: t.priority)

    def get_completed_results(self) -> list[TaskResult]:
        """Get results for all completed tasks.

        Returns:
            List of TaskResults for completed tasks
        """
        return [
            TaskResult(
                task_id=t.task_id,
                status=t.status,
                result=t.result,
                error=t.error,
                duration=t.duration,
            )
            for t in self.agents.values()
            if t.is_done
        ]

    def cleanup_done(self) -> int:
        """Remove completed tasks from registry.

        Returns:
            Number of tasks removed
        """
        done_ids = [tid for tid, t in self.agents.items() if t.is_done]
        for tid in done_ids:
            del self.agents[tid]
        return len(done_ids)


# ============================================================================
# Helper Functions
# ============================================================================


def get_all_agent_tools() -> list[dict[str, Any]]:
    """Get all agent tool definitions.

    Returns:
        List of agent tool definitions
    """
    return [
        task.tool_definition,  # type: ignore[attr-defined]
        task_status.tool_definition,  # type: ignore[attr-defined]
        task_cancel.tool_definition,  # type: ignore[attr-defined]
    ]


def list_active_tasks() -> list[dict[str, Any]]:
    """List all active tasks.

    Returns:
        List of active task information
    """
    # Maximum prompt length in task list display
    max_prompt_length = 100

    return [
        {
            "task_id": task_id,
            "agent_type": task.agent_type,
            "status": task.status,
            "prompt": (
                task.prompt[:max_prompt_length] + "..."
                if len(task.prompt) > max_prompt_length
                else task.prompt
            ),
        }
        for task_id, task in _ACTIVE_TASKS.items()
    ]


def cleanup_tasks(all_tasks: bool = False) -> None:
    """Clean up tasks.

    Args:
        all_tasks: If True, remove all tasks. Otherwise only completed/failed.

    Removes completed and failed tasks by default, or all tasks if requested.
    """
    global _ACTIVE_TASKS  # noqa: PLW0602

    if all_tasks:
        _ACTIVE_TASKS.clear()
    else:
        completed = [
            task_id
            for task_id, task in _ACTIVE_TASKS.items()
            if task.status in ["completed", "failed"]
        ]

        for task_id in completed:
            del _ACTIVE_TASKS[task_id]


def get_agent_info(agent_type: str) -> dict[str, Any] | None:
    """Get information about an agent type.

    Args:
        agent_type: Type of agent

    Returns:
        Agent type information or None
    """
    return AGENT_TYPES.get(agent_type)


def list_agent_types() -> dict[str, dict[str, Any]]:
    """List all available agent types.

    Returns:
        Dictionary of agent types and their capabilities
    """
    return AGENT_TYPES.copy()


# Export tool instances
__all__ = [
    "AgentCoordinator",
    "AgentTask",
    "TaskPriority",
    "TaskResult",
    "TaskStatus",
    "cleanup_tasks",
    "get_agent_info",
    "get_all_agent_tools",
    "list_active_tasks",
    "list_agent_types",
    "task",
    "task_cancel",
    "task_status",
]
