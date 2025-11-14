"""Tests for search and discovery tools."""

from pathlib import Path

from devorbit import glob_files, grep_code


class TestGlobFiles:
    """Tests for glob_files tool."""

    def test_glob_simple_pattern(self, tmp_path: Path) -> None:
        """Test simple glob pattern."""
        # Create test files
        (tmp_path / "test1.py").write_text("# Python 1")
        (tmp_path / "test2.py").write_text("# Python 2")
        (tmp_path / "test.txt").write_text("Text file")

        result = glob_files("*.py", str(tmp_path))

        assert "error" not in result
        assert result["count"] == 2
        assert any("test1.py" in p for p in result["matches"])
        assert any("test2.py" in p for p in result["matches"])

    def test_glob_recursive_pattern(self, tmp_path: Path) -> None:
        """Test recursive glob pattern."""
        # Create nested structure
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("# Main")
        (tmp_path / "src" / "utils").mkdir()
        (tmp_path / "src" / "utils" / "helper.py").write_text("# Helper")

        result = glob_files("**/*.py", str(tmp_path))

        assert result["count"] == 2
        assert any("main.py" in p for p in result["matches"])
        assert any("helper.py" in p for p in result["matches"])

    def test_glob_no_matches(self, tmp_path: Path) -> None:
        """Test glob with no matches."""
        (tmp_path / "test.txt").write_text("Text")

        result = glob_files("*.py", str(tmp_path))

        assert result["count"] == 0
        assert result["matches"] == []

    def test_glob_nonexistent_path(self) -> None:
        """Test glob with nonexistent path."""
        result = glob_files("*.py", "/nonexistent/path")

        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_glob_file_path(self, tmp_path: Path) -> None:
        """Test glob with file path instead of directory."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        result = glob_files("*.py", str(test_file))

        assert "error" in result
        assert "not a directory" in result["error"].lower()


class TestGrepCode:
    """Tests for grep_code tool."""

    def test_grep_files_with_matches(self, tmp_path: Path) -> None:
        """Test grep with files_with_matches output mode."""
        # Create test files
        (tmp_path / "file1.txt").write_text("hello world\ngoodbye world")
        (tmp_path / "file2.txt").write_text("hello python\ngoodbye java")
        (tmp_path / "file3.txt").write_text("no match here")

        result = grep_code(
            pattern="hello",
            path=str(tmp_path),
            output_mode="files_with_matches",
        )

        assert result["total_matches"] == 2
        assert any("file1.txt" in f for f in result["matching_files"])
        assert any("file2.txt" in f for f in result["matching_files"])

    def test_grep_count(self, tmp_path: Path) -> None:
        """Test grep with count output mode."""
        (tmp_path / "file1.txt").write_text("foo foo foo")
        (tmp_path / "file2.txt").write_text("foo bar")

        result = grep_code(
            pattern="foo",
            path=str(tmp_path),
            output_mode="count",
        )

        assert result["total_files"] == 2
        # file1.txt should have 3 matches
        counts = {c["file"]: c["count"] for c in result["match_counts"]}
        assert any(c == 3 for c in counts.values())

    def test_grep_content_mode(self, tmp_path: Path) -> None:
        """Test grep with content output mode."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("line 1\nline 2 match\nline 3")

        result = grep_code(
            pattern="match",
            path=str(tmp_path),
            output_mode="content",
        )

        assert result["total_matches"] >= 1
        assert any("match" in m["content"] for m in result["matches"])

    def test_grep_case_insensitive(self, tmp_path: Path) -> None:
        """Test case insensitive search."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello WORLD hello world")

        result = grep_code(
            pattern="hello",
            path=str(tmp_path),
            case_insensitive=True,
            output_mode="count",
        )

        # Should match both "Hello" and "hello"
        assert result["match_counts"][0]["count"] == 2

    def test_grep_with_file_type(self, tmp_path: Path) -> None:
        """Test grep with file type filter."""
        (tmp_path / "test.py").write_text("def hello(): pass")
        (tmp_path / "test.txt").write_text("hello world")

        result = grep_code(
            pattern="hello",
            path=str(tmp_path),
            type="py",
            output_mode="files_with_matches",
        )

        # Should only match .py file
        assert result["total_matches"] == 1
        assert "test.py" in result["matching_files"][0]

    def test_grep_with_glob_filter(self, tmp_path: Path) -> None:
        """Test grep with glob filter."""
        (tmp_path / "test.js").write_text("const hello = 1;")
        (tmp_path / "test.jsx").write_text("const hello = <div/>;")
        (tmp_path / "test.py").write_text("hello = 1")

        result = grep_code(
            pattern="hello",
            path=str(tmp_path),
            glob="*.{js,jsx}",
            output_mode="files_with_matches",
        )

        # Should match .js and .jsx but not .py
        assert result["total_matches"] == 2

    def test_grep_context_lines(self, tmp_path: Path) -> None:
        """Test grep with context lines."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("line 1\nline 2\nMATCH\nline 4\nline 5")

        result = grep_code(
            pattern="MATCH",
            path=str(test_file),
            context_before=1,
            context_after=1,
            output_mode="content",
        )

        # Should include context lines
        content = result["matches"][0]["content"]
        assert "line 2" in content
        assert "MATCH" in content
        assert "line 4" in content

    def test_grep_head_limit(self, tmp_path: Path) -> None:
        """Test grep with head limit."""
        for i in range(10):
            (tmp_path / f"file{i}.txt").write_text("match")

        result = grep_code(
            pattern="match",
            path=str(tmp_path),
            head_limit=5,
            output_mode="files_with_matches",
        )

        assert result["shown_matches"] == 5
        assert result["total_matches"] == 10

    def test_grep_offset(self, tmp_path: Path) -> None:
        """Test grep with offset."""
        for i in range(10):
            (tmp_path / f"file{i}.txt").write_text("match")

        result = grep_code(
            pattern="match",
            path=str(tmp_path),
            offset=5,
            output_mode="files_with_matches",
        )

        assert result["shown_matches"] == 5
        assert result["total_matches"] == 10

    def test_grep_invalid_regex(self, tmp_path: Path) -> None:
        """Test grep with invalid regex pattern."""
        result = grep_code(
            pattern="[invalid",
            path=str(tmp_path),
        )

        assert "error" in result
        assert "regex" in result["error"].lower()

    def test_grep_multiline(self, tmp_path: Path) -> None:
        """Test multiline grep."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("start\nmiddle\nend")

        result = grep_code(
            pattern="start.*end",
            path=str(test_file),
            multiline=True,
            output_mode="files_with_matches",
        )

        assert result["total_matches"] >= 1
