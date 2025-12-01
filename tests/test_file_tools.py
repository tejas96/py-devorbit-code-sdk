"""Tests for file operation tools."""

from pathlib import Path

from devorbit import edit_file, ls_directory, multi_edit_file, read_file, write_file


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

    def test_multi_edit_partial_failure_atomic(self, tmp_path: Path) -> None:
        """Test multi-edit with some failures in atomic mode (default).

        With atomic=True (default), if any edit fails, the file is NOT modified.
        This prevents partial/corrupted state.
        """
        test_file = tmp_path / "multi.txt"
        test_file.write_text("foo bar")

        edits = [
            {"old_string": "foo", "new_string": "FOO"},
            {"old_string": "missing", "new_string": "MISSING"},
            {"old_string": "bar", "new_string": "BAR"},
        ]

        result = multi_edit_file(str(test_file), edits)

        # Atomic mode: operation fails, file unchanged
        assert result["success"] is False
        assert result["file_unchanged"] is True
        assert "validation_errors" in result
        assert result["failed_edits"] == 1
        assert test_file.read_text() == "foo bar"  # Original content preserved!

    def test_multi_edit_partial_failure_non_atomic(self, tmp_path: Path) -> None:
        """Test multi-edit with some failures in non-atomic mode.

        With atomic=False, successful edits are applied even if some fail.
        """
        test_file = tmp_path / "multi.txt"
        test_file.write_text("foo bar")

        edits = [
            {"old_string": "foo", "new_string": "FOO"},
            {"old_string": "missing", "new_string": "MISSING"},
            {"old_string": "bar", "new_string": "BAR"},
        ]

        result = multi_edit_file(str(test_file), edits, atomic=False)

        # Non-atomic mode: partial success, file modified
        assert result["success"] is False  # Overall success is False due to failures
        assert result["successful_edits"] == 2
        assert result["failed_edits"] == 1
        assert test_file.read_text() == "FOO BAR"  # Successful edits applied

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


class TestLsDirectory:
    """Tests for ls_directory tool."""

    def test_ls_simple_directory(self, tmp_path: Path) -> None:
        """Test listing a simple directory."""
        # Create test files
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")
        (tmp_path / "subdir").mkdir()

        result = ls_directory(str(tmp_path))

        assert result["success"] is True
        assert result["total_entries"] == 3
        assert any("file1.txt" in e["name"] for e in result["entries"])
        assert any("file2.txt" in e["name"] for e in result["entries"])
        assert any("subdir/" in e["name"] for e in result["entries"])

    def test_ls_with_hidden_files(self, tmp_path: Path) -> None:
        """Test listing with hidden files."""
        (tmp_path / "visible.txt").write_text("visible")
        (tmp_path / ".hidden").write_text("hidden")

        # Without all_files flag
        result = ls_directory(str(tmp_path), all_files=False)
        assert result["total_entries"] == 1
        assert not any(".hidden" in e["name"] for e in result["entries"])

        # With all_files flag
        result_all = ls_directory(str(tmp_path), all_files=True)
        assert result_all["total_entries"] == 2
        assert any(".hidden" in e["name"] for e in result_all["entries"])

    def test_ls_long_format(self, tmp_path: Path) -> None:
        """Test listing with long format."""
        (tmp_path / "file.txt").write_text("content")

        result = ls_directory(str(tmp_path), long_format=True)

        assert result["success"] is True
        entries = result["entries"]
        assert len(entries) == 1
        assert "size" in entries[0]
        assert "permissions" in entries[0]
        assert "modified" in entries[0]

    def test_ls_recursive(self, tmp_path: Path) -> None:
        """Test recursive directory listing."""
        # Create nested structure
        (tmp_path / "file1.txt").write_text("top")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file2.txt").write_text("nested")

        result = ls_directory(str(tmp_path), recursive=True)

        assert result["success"] is True
        assert result["total_entries"] >= 3  # file1.txt, subdir/, subdir/file2.txt
        assert any("subdir/file2.txt" in e["name"] for e in result["entries"])

    def test_ls_nonexistent_directory(self) -> None:
        """Test listing nonexistent directory."""
        result = ls_directory("/nonexistent/directory")

        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_ls_file_not_directory(self, tmp_path: Path) -> None:
        """Test listing a file (should fail)."""
        test_file = tmp_path / "file.txt"
        test_file.write_text("content")

        result = ls_directory(str(test_file))

        assert "error" in result
        assert "not a directory" in result["error"].lower()

    def test_ls_empty_directory(self, tmp_path: Path) -> None:
        """Test listing an empty directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = ls_directory(str(empty_dir))

        assert result["success"] is True
        assert result["total_entries"] == 0
        assert result["entries"] == []

    def test_ls_output_format(self, tmp_path: Path) -> None:
        """Test output formatting."""
        (tmp_path / "test.txt").write_text("content")

        # Simple format
        result_simple = ls_directory(str(tmp_path))
        assert "output" in result_simple
        assert "test.txt" in result_simple["output"]

        # Long format
        result_long = ls_directory(str(tmp_path), long_format=True)
        assert "output" in result_long
        assert "test.txt" in result_long["output"]
