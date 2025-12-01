"""Tests for todo management tools."""

import json
from pathlib import Path

from devorbit import clear_todo_state, get_current_todos, todo_read, todo_write


class TestTodoWrite:
    """Tests for todo_write tool."""

    def setup_method(self) -> None:
        """Clear todo state before each test."""
        clear_todo_state()

    def test_write_valid_todos(self) -> None:
        """Test writing valid todos."""
        todos = [
            {
                "content": "Task 1",
                "activeForm": "Doing task 1",
                "status": "pending",
            },
            {
                "content": "Task 2",
                "activeForm": "Doing task 2",
                "status": "in_progress",
            },
        ]

        result = todo_write(todos)

        assert result["success"] is True
        assert result["total_tasks"] == 2
        assert result["pending"] == 1
        assert result["in_progress"] == 1
        assert result["completed"] == 0

    def test_write_updates_state(self) -> None:
        """Test that writing updates global state."""
        todos = [
            {
                "content": "Task 1",
                "activeForm": "Doing task 1",
                "status": "pending",
            },
        ]

        todo_write(todos)
        current = get_current_todos()

        assert len(current) == 1
        assert current[0]["content"] == "Task 1"

    def test_write_persist_to_file(self, tmp_path: Path) -> None:
        """Test persisting todos to file."""
        todo_file = tmp_path / "todos.json"
        todos = [
            {
                "content": "Task 1",
                "activeForm": "Doing task 1",
                "status": "pending",
            },
        ]

        result = todo_write(todos, persist_to_file=str(todo_file))

        assert result["persisted"] is True
        assert todo_file.exists()

        # Verify file content
        saved_todos = json.loads(todo_file.read_text())
        assert len(saved_todos) == 1
        assert saved_todos[0]["content"] == "Task 1"

    def test_write_empty_todos(self) -> None:
        """Test error when writing empty todos list."""
        result = todo_write([])

        assert "error" in result
        assert "cannot be empty" in result["error"]

    def test_write_missing_activeform_auto_generated(self) -> None:
        """Test that missing activeForm is auto-generated (not an error)."""
        todos = [{"content": "Task 1", "status": "pending"}]  # Missing activeForm

        result = todo_write(todos)

        # Should succeed with auto-generated activeForm
        assert result["success"] is True
        assert result["total_tasks"] == 1

        # Verify activeForm was generated in stored state
        from devorbit.tools.todo import get_current_todos

        stored = get_current_todos()
        assert len(stored) == 1
        assert "activeForm" in stored[0]
        assert stored[0]["activeForm"]  # Not empty

    def test_write_missing_content_error(self) -> None:
        """Test error when todo missing required 'content' field."""
        todos = [{"status": "pending", "activeForm": "Doing something"}]  # Missing content

        result = todo_write(todos)

        assert "error" in result
        assert "missing" in result["error"].lower() and "content" in result["error"].lower()

    def test_write_invalid_status(self) -> None:
        """Test error when todo has invalid status."""
        todos = [
            {
                "content": "Task 1",
                "activeForm": "Doing task 1",
                "status": "invalid_status",
            },
        ]

        result = todo_write(todos)

        assert "error" in result
        assert "invalid status" in result["error"].lower()

    def test_write_empty_content(self) -> None:
        """Test error when todo has empty content."""
        todos = [
            {
                "content": "   ",  # Empty/whitespace only
                "activeForm": "Doing task",
                "status": "pending",
            },
        ]

        result = todo_write(todos)

        assert "error" in result
        assert "empty" in result["error"].lower()


class TestTodoRead:
    """Tests for todo_read tool."""

    def setup_method(self) -> None:
        """Clear todo state before each test."""
        clear_todo_state()

    def test_read_empty_state(self) -> None:
        """Test reading when no todos exist."""
        result = todo_read()

        assert result["total_tasks"] == 0
        assert result["todos"] == []
        assert "No tasks" in result["message"]

    def test_read_after_write(self) -> None:
        """Test reading todos after writing."""
        todos = [
            {
                "content": "Task 1",
                "activeForm": "Doing task 1",
                "status": "pending",
            },
            {
                "content": "Task 2",
                "activeForm": "Doing task 2",
                "status": "completed",
            },
        ]

        todo_write(todos)
        result = todo_read()

        assert result["total_tasks"] == 2
        assert result["pending"] == 1
        assert result["completed"] == 1
        assert len(result["todos"]) == 2

    def test_read_formatted_output(self) -> None:
        """Test that read output is properly formatted."""
        todos = [
            {
                "content": "Task 1",
                "activeForm": "Doing task 1",
                "status": "pending",
            },
        ]

        todo_write(todos)
        result = todo_read()

        formatted = result["todos"][0]
        assert formatted["number"] == 1
        assert formatted["content"] == "Task 1"
        assert formatted["status"] == "pending"
        assert "display" in formatted
        assert "pending" in formatted["display"]

    def test_read_progress_percentage(self) -> None:
        """Test progress percentage calculation."""
        todos = [
            {
                "content": "Task 1",
                "activeForm": "Doing task 1",
                "status": "completed",
            },
            {
                "content": "Task 2",
                "activeForm": "Doing task 2",
                "status": "pending",
            },
        ]

        todo_write(todos)
        result = todo_read()

        assert result["progress_percentage"] == 50.0

    def test_read_from_file(self, tmp_path: Path) -> None:
        """Test loading todos from file."""
        todo_file = tmp_path / "todos.json"
        todos = [
            {
                "content": "File task",
                "activeForm": "Doing file task",
                "status": "pending",
            },
        ]
        todo_file.write_text(json.dumps(todos))

        result = todo_read(load_from_file=str(todo_file))

        assert result["loaded_from_file"] is True
        assert result["total_tasks"] == 1
        assert result["todos"][0]["content"] == "File task"

    def test_read_nonexistent_file(self) -> None:
        """Test reading from nonexistent file."""
        result = todo_read(load_from_file="/nonexistent/todos.json")

        assert "error" in result
        assert "not found" in result["error"].lower()


class TestTodoStateManagement:
    """Tests for todo state management functions."""

    def setup_method(self) -> None:
        """Clear todo state before each test."""
        clear_todo_state()

    def test_clear_state(self) -> None:
        """Test clearing todo state."""
        todos = [
            {
                "content": "Task 1",
                "activeForm": "Doing task 1",
                "status": "pending",
            },
        ]

        todo_write(todos)
        assert len(get_current_todos()) == 1

        clear_todo_state()
        assert len(get_current_todos()) == 0

    def test_get_current_todos(self) -> None:
        """Test getting current todos."""
        todos = [
            {
                "content": "Task 1",
                "activeForm": "Doing task 1",
                "status": "pending",
            },
        ]

        todo_write(todos)
        current = get_current_todos()

        assert len(current) == 1
        assert current[0]["content"] == "Task 1"

    def test_state_isolation(self) -> None:
        """Test that state changes don't affect returned copies."""
        todos = [
            {
                "content": "Task 1",
                "activeForm": "Doing task 1",
                "status": "pending",
            },
        ]

        todo_write(todos)
        current1 = get_current_todos()
        current2 = get_current_todos()

        # Modify one copy
        current1[0]["content"] = "Modified"

        # Other copy should be unchanged
        assert current2[0]["content"] == "Task 1"
