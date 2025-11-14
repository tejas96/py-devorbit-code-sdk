"""Tests for file operation tools."""

import tempfile
from pathlib import Path

import pytest

from devorbit import edit_file, multi_edit_file, read_file, write_file


class TestReadFile:
    """Tests for read_file tool."""

    def test_read_simple_file(self, tmp_path: Path) -> None:
        """Test reading a simple text file."""
        # Create test file
        test_file = tmp_path / "test.txt"
        content = "Line 1\nLine 2\nLine 3\n"
        test_file.write_text(content)

        # Read file
        result = read_file(str(test_file))

        # Verify
        assert "error" not in result
        assert result["total_lines"] == 3
        assert result["lines_shown"] == 3
        assert "     1\tLine 1\n" in result["content"]
        assert "     2\tLine 2\n" in result["content"]

    def test_read_with_offset(self, tmp_path: Path) -> None:
        """Test reading file with offset."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("\n".join([f"Line {i}" for i in range(1, 11)]))

        result = read_file(str(test_file), offset=5)

        assert result["start_line"] == 6
        assert "     6\tLine 6" in result["content"]

    def test_read_with_limit(self, tmp_path: Path) -> None:
        """Test reading file with limit."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("\n".join([f"Line {i}" for i in range(1, 101)]))

        result = read_file(str(test_file), limit=10)

        assert result["lines_shown"] == 10
        assert result["total_lines"] == 100
        assert result.get("truncated") is True

    def test_read_nonexistent_file(self) -> None:
        """Test reading file that doesn't exist."""
        result = read_file("/nonexistent/file.txt")

        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_read_directory(self, tmp_path: Path) -> None:
        """Test reading a directory (should fail)."""
        result = read_file(str(tmp_path))

        assert "error" in result
        assert "not a file" in result["error"].lower()


class TestWriteFile:
    """Tests for write_file tool."""

    def test_write_new_file(self, tmp_path: Path) -> None:
        """Test writing a new file."""
        test_file = tmp_path / "new.txt"
        content = "Hello, world!"

        result = write_file(str(test_file), content)

        assert result["success"] is True
        assert result["action"] == "created"
        assert test_file.read_text() == content

    def test_write_overwrite_file(self, tmp_path: Path) -> None:
        """Test overwriting existing file."""
        test_file = tmp_path / "existing.txt"
        test_file.write_text("Old content")

        new_content = "New content"
        result = write_file(str(test_file), new_content)

        assert result["success"] is True
        assert test_file.read_text() == new_content

    def test_write_creates_parent_dirs(self, tmp_path: Path) -> None:
        """Test that parent directories are created."""
        test_file = tmp_path / "subdir" / "nested" / "file.txt"
        content = "Nested file"

        result = write_file(str(test_file), content)

        assert result["success"] is True
        assert test_file.exists()
        assert test_file.read_text() == content


class TestEditFile:
    """Tests for edit_file tool."""

    def test_edit_simple_replacement(self, tmp_path: Path) -> None:
        """Test simple string replacement with unique string."""
        test_file = tmp_path / "edit.txt"
        original = "Hello, world!\nGoodbye, universe!"
        test_file.write_text(original)

        result = edit_file(
            str(test_file),
            old_string="world",
            new_string="Python",
        )

        assert result["success"] is True
        assert result["replacements"] == 1
        assert "Hello, Python!" in test_file.read_text()

    def test_edit_replace_all(self, tmp_path: Path) -> None:
        """Test replacing all occurrences."""
        test_file = tmp_path / "edit.txt"
        original = "foo bar foo baz foo"
        test_file.write_text(original)

        result = edit_file(
            str(test_file),
            old_string="foo",
            new_string="qux",
            replace_all=True,
        )

        assert result["success"] is True
        assert result["replacements"] == 3
        assert test_file.read_text() == "qux bar qux baz qux"

    def test_edit_multiple_without_replace_all(self, tmp_path: Path) -> None:
        """Test error when multiple occurrences without replace_all."""
        test_file = tmp_path / "edit.txt"
        test_file.write_text("foo foo foo")

        result = edit_file(
            str(test_file),
            old_string="foo",
            new_string="bar",
            replace_all=False,
        )

        assert "error" in result
        assert "3 times" in result["error"]

    def test_edit_string_not_found(self, tmp_path: Path) -> None:
        """Test error when old_string not found."""
        test_file = tmp_path / "edit.txt"
        test_file.write_text("Hello, world!")

        result = edit_file(
            str(test_file),
            old_string="missing",
            new_string="replacement",
        )

        assert "error" in result
        assert "not found" in result["error"]

    def test_edit_same_strings(self, tmp_path: Path) -> None:
        """Test error when old_string equals new_string."""
        test_file = tmp_path / "edit.txt"
        test_file.write_text("Hello, world!")

        result = edit_file(
            str(test_file),
            old_string="world",
            new_string="world",
        )

        assert "error" in result
        assert "must be different" in result["error"]


class TestMultiEditFile:
    """Tests for multi_edit_file tool."""

    def test_multi_edit_success(self, tmp_path: Path) -> None:
        """Test multiple successful edits."""
        test_file = tmp_path / "multi.txt"
        test_file.write_text("foo bar baz")

        edits = [
            {"old_string": "foo", "new_string": "FOO"},
            {"old_string": "bar", "new_string": "BAR"},
            {"old_string": "baz", "new_string": "BAZ"},
        ]

        result = multi_edit_file(str(test_file), edits)

        assert result["success"] is True
        assert result["successful_edits"] == 3
        assert result["failed_edits"] == 0
        assert test_file.read_text() == "FOO BAR BAZ"

    def test_multi_edit_partial_failure(self, tmp_path: Path) -> None:
        """Test multi-edit with some failures."""
        test_file = tmp_path / "multi.txt"
        test_file.write_text("foo bar")

        edits = [
            {"old_string": "foo", "new_string": "FOO"},
            {"old_string": "missing", "new_string": "MISSING"},
            {"old_string": "bar", "new_string": "BAR"},
        ]

        result = multi_edit_file(str(test_file), edits)

        assert result["success"] is True
        assert result["successful_edits"] == 2
        assert result["failed_edits"] == 1
        assert test_file.read_text() == "FOO BAR"

    def test_multi_edit_empty_list(self, tmp_path: Path) -> None:
        """Test multi-edit with empty edits list."""
        test_file = tmp_path / "multi.txt"
        test_file.write_text("content")

        result = multi_edit_file(str(test_file), [])

        assert "error" in result
        assert "cannot be empty" in result["error"]

    def test_multi_edit_invalid_edit(self, tmp_path: Path) -> None:
        """Test multi-edit with invalid edit structure."""
        test_file = tmp_path / "multi.txt"
        test_file.write_text("content")

        edits = [{"old_string": "foo"}]  # Missing new_string

        result = multi_edit_file(str(test_file), edits)

        assert "error" in result
        assert "missing" in result["error"].lower()
