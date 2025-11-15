"""Tests for Jupyter notebook operation tools."""

import json
import tempfile
from pathlib import Path

import pytest

from devorbit import (
    create_notebook_edit_tool,
    create_notebook_read_tool,
    get_all_notebook_tools,
    notebook_edit,
    notebook_read,
)


@pytest.fixture
def sample_notebook() -> dict:
    """Create a sample notebook for testing."""
    return {
        "cells": [
            {
                "cell_type": "markdown",
                "source": ["# Test Notebook\n", "This is a test."],
                "metadata": {},
            },
            {
                "cell_type": "code",
                "source": ["print('Hello, World!')"],
                "metadata": {},
                "execution_count": 1,
                "outputs": [
                    {
                        "output_type": "stream",
                        "name": "stdout",
                        "text": ["Hello, World!\n"],
                    }
                ],
            },
            {
                "cell_type": "code",
                "source": ["x = 42\n", "print(x)"],
                "metadata": {},
                "execution_count": 2,
                "outputs": [],
            },
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


@pytest.fixture
def temp_notebook(sample_notebook: dict) -> Path:
    """Create a temporary notebook file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".ipynb", delete=False) as f:
        json.dump(sample_notebook, f)
        path = Path(f.name)
    yield path
    # Cleanup
    if path.exists():
        path.unlink()


class TestNotebookReadTool:
    """Tests for NotebookRead tool."""

    def test_create_notebook_read_tool(self) -> None:
        """Test notebook read tool creation."""
        tool = create_notebook_read_tool()
        assert tool["name"] == "notebook_read"
        assert "description" in tool
        assert "input_schema" in tool
        assert "notebook_path" in tool["input_schema"]["properties"]

    def test_notebook_read_success(self, temp_notebook: Path) -> None:
        """Test successful notebook reading."""
        result = notebook_read(str(temp_notebook))

        assert result["path"] == str(temp_notebook.absolute())
        assert result["num_cells"] == 3
        assert len(result["cells"]) == 3

        # Check first cell (markdown)
        assert result["cells"][0]["cell_type"] == "markdown"
        assert "# Test Notebook" in result["cells"][0]["source"]

        # Check second cell (code with output)
        assert result["cells"][1]["cell_type"] == "code"
        assert "print('Hello, World!')" in result["cells"][1]["source"]
        assert result["cells"][1]["execution_count"] == 1
        assert result["cells"][1]["outputs"] is not None

    def test_notebook_read_without_outputs(self, temp_notebook: Path) -> None:
        """Test reading notebook without outputs."""
        result = notebook_read(str(temp_notebook), include_outputs=False)

        assert result["num_cells"] == 3
        for cell in result["cells"]:
            assert cell["outputs"] is None

    def test_notebook_read_with_cell_range(self, temp_notebook: Path) -> None:
        """Test reading notebook with cell range."""
        result = notebook_read(str(temp_notebook), cell_range={"start": 1, "end": 2})

        assert result["num_cells"] == 1
        assert result["cells"][0]["cell_type"] == "code"
        assert "print('Hello, World!')" in result["cells"][0]["source"]

    def test_notebook_read_not_found(self) -> None:
        """Test reading non-existent notebook."""
        with pytest.raises(FileNotFoundError):
            notebook_read("/nonexistent/notebook.ipynb")

    def test_notebook_read_invalid_extension(self, tmp_path: Path) -> None:
        """Test reading file with wrong extension."""
        invalid_file = tmp_path / "test.txt"
        invalid_file.write_text("not a notebook")

        with pytest.raises(ValueError, match="not a Jupyter notebook"):
            notebook_read(str(invalid_file))

    def test_notebook_read_invalid_json(self, tmp_path: Path) -> None:
        """Test reading invalid JSON."""
        invalid_nb = tmp_path / "invalid.ipynb"
        invalid_nb.write_text("{ invalid json }")

        with pytest.raises(ValueError, match="Invalid notebook"):
            notebook_read(str(invalid_nb))

    def test_notebook_read_missing_cells(self, tmp_path: Path) -> None:
        """Test reading notebook without cells field."""
        invalid_nb = tmp_path / "nocells.ipynb"
        invalid_nb.write_text('{"metadata": {}}')

        with pytest.raises(ValueError, match="missing 'cells' field"):
            notebook_read(str(invalid_nb))


class TestNotebookEditTool:
    """Tests for NotebookEdit tool."""

    def test_create_notebook_edit_tool(self) -> None:
        """Test notebook edit tool creation."""
        tool = create_notebook_edit_tool()
        assert tool["name"] == "notebook_edit"
        assert "description" in tool
        assert "input_schema" in tool
        assert "notebook_path" in tool["input_schema"]["properties"]
        assert "cell_index" in tool["input_schema"]["properties"]

    def test_notebook_edit_replace_cell(self, temp_notebook: Path) -> None:
        """Test replacing a cell."""
        new_source = "print('Modified!')"
        result = notebook_edit(
            str(temp_notebook), cell_index=1, new_source=new_source, operation="replace"
        )

        assert result["success"] is True
        assert result["operation"] == "replace"
        assert result["cell_index"] == 1

        # Verify the change
        read_result = notebook_read(str(temp_notebook))
        assert new_source in read_result["cells"][1]["source"]

    def test_notebook_edit_insert_cell(self, temp_notebook: Path) -> None:
        """Test inserting a new cell."""
        new_source = "# New cell"
        result = notebook_edit(
            str(temp_notebook),
            cell_index=1,
            new_source=new_source,
            cell_type="markdown",
            operation="insert",
        )

        assert result["success"] is True
        assert result["operation"] == "insert"
        assert result["cell_index"] == 1

        # Verify the insertion
        read_result = notebook_read(str(temp_notebook))
        assert read_result["num_cells"] == 4
        assert read_result["cells"][1]["cell_type"] == "markdown"
        assert new_source in read_result["cells"][1]["source"]

    def test_notebook_edit_delete_cell(self, temp_notebook: Path) -> None:
        """Test deleting a cell."""
        result = notebook_edit(str(temp_notebook), cell_index=0, operation="delete")

        assert result["success"] is True
        assert result["operation"] == "delete"
        assert result["cell_index"] == 0

        # Verify the deletion
        read_result = notebook_read(str(temp_notebook))
        assert read_result["num_cells"] == 2

    def test_notebook_edit_change_cell_type(self, temp_notebook: Path) -> None:
        """Test changing cell type."""
        result = notebook_edit(
            str(temp_notebook),
            cell_index=1,
            new_source="print('test')",
            cell_type="code",
            operation="replace",
        )

        assert result["success"] is True

        # Verify the change
        read_result = notebook_read(str(temp_notebook))
        assert read_result["cells"][1]["cell_type"] == "code"

    def test_notebook_edit_invalid_index(self, temp_notebook: Path) -> None:
        """Test editing with invalid cell index."""
        with pytest.raises(IndexError):
            notebook_edit(str(temp_notebook), cell_index=100, operation="delete")

    def test_notebook_edit_not_found(self) -> None:
        """Test editing non-existent notebook."""
        with pytest.raises(FileNotFoundError):
            notebook_edit("/nonexistent/notebook.ipynb", cell_index=0)

    def test_notebook_edit_invalid_extension(self, tmp_path: Path) -> None:
        """Test editing file with wrong extension."""
        invalid_file = tmp_path / "test.txt"
        invalid_file.write_text("not a notebook")

        with pytest.raises(ValueError, match="not a Jupyter notebook"):
            notebook_edit(str(invalid_file), cell_index=0)

    def test_notebook_edit_multiline_source(self, temp_notebook: Path) -> None:
        """Test editing with multiline source."""
        new_source = "line1\nline2\nline3"
        result = notebook_edit(
            str(temp_notebook), cell_index=1, new_source=new_source, operation="replace"
        )

        assert result["success"] is True

        # Verify the change
        read_result = notebook_read(str(temp_notebook))
        cell_source = read_result["cells"][1]["source"]
        assert "line1" in cell_source
        assert "line2" in cell_source
        assert "line3" in cell_source


class TestNotebookToolsHelpers:
    """Tests for notebook tools helper functions."""

    def test_get_all_notebook_tools(self) -> None:
        """Test getting all notebook tools."""
        tools = get_all_notebook_tools()

        assert len(tools) == 2
        tool_names = {tool["name"] for tool in tools}
        assert "notebook_read" in tool_names
        assert "notebook_edit" in tool_names

        # Verify each tool has required fields
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool
            assert "properties" in tool["input_schema"]
