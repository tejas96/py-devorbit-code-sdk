"""Jupyter notebook operation tools for the Devorbit SDK.

This module provides tools for reading and editing Jupyter notebooks (.ipynb files).
"""

import json
from pathlib import Path
from typing import Any, Literal

from typing_extensions import TypedDict


class NotebookCell(TypedDict):
    """Jupyter notebook cell."""

    cell_type: Literal["code", "markdown", "raw"]
    source: str
    metadata: dict[str, Any]
    execution_count: int | None
    outputs: list[dict[str, Any]] | None
    id: str | None


class NotebookContent(TypedDict):
    """Jupyter notebook content."""

    cells: list[NotebookCell]
    metadata: dict[str, Any]
    nbformat: int
    nbformat_minor: int


class NotebookReadResult(TypedDict):
    """Result from reading a Jupyter notebook."""

    path: str
    num_cells: int
    cells: list[NotebookCell]
    metadata: dict[str, Any]


# NotebookRead tool
def create_notebook_read_tool() -> dict[str, Any]:
    """Create NotebookRead tool definition.

    Returns:
        Tool definition for NotebookRead
    """
    return {
        "name": "notebook_read",
        "description": """Read a Jupyter notebook (.ipynb file) and return its contents.

This tool reads Jupyter notebooks and returns all cells with their content,
type (code/markdown), execution counts, and outputs.

Use this when you need to:
- Analyze notebook structure
- Read code and markdown cells
- View cell outputs
- Understand notebook flow""",
        "input_schema": {
            "type": "object",
            "properties": {
                "notebook_path": {
                    "type": "string",
                    "description": "Absolute path to the Jupyter notebook file",
                },
                "include_outputs": {
                    "type": "boolean",
                    "description": "Include cell outputs in the result (default: true)",
                },
                "cell_range": {
                    "type": "object",
                    "description": "Optional range of cells to read (start and end indices)",
                    "properties": {
                        "start": {"type": "integer"},
                        "end": {"type": "integer"},
                    },
                },
            },
            "required": ["notebook_path"],
        },
    }


def notebook_read(
    notebook_path: str,
    include_outputs: bool = True,
    cell_range: dict[str, int] | None = None,
) -> NotebookReadResult:
    """Read a Jupyter notebook file.

    Args:
        notebook_path: Path to the notebook file
        include_outputs: Include cell outputs
        cell_range: Optional range of cells to read (start, end)

    Returns:
        NotebookReadResult with notebook contents

    Raises:
        FileNotFoundError: If notebook doesn't exist
        ValueError: If file is not a valid notebook
    """
    path = Path(notebook_path)

    if not path.exists():
        raise FileNotFoundError(f"Notebook not found: {notebook_path}")

    if not path.suffix == ".ipynb":
        raise ValueError(f"File is not a Jupyter notebook: {notebook_path}")

    # Read notebook file
    with path.open(encoding="utf-8") as f:
        try:
            notebook_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid notebook file: {e}") from e

    # Validate notebook structure
    if "cells" not in notebook_data:
        raise ValueError("Invalid notebook: missing 'cells' field")

    cells = notebook_data["cells"]

    # Apply cell range if specified
    if cell_range:
        start = cell_range.get("start", 0)
        end = cell_range.get("end", len(cells))
        cells = cells[start:end]

    # Process cells
    processed_cells: list[NotebookCell] = []
    for cell in cells:
        # Join source lines if it's a list
        source = cell.get("source", "")
        if isinstance(source, list):
            source = "".join(source)

        processed_cell = NotebookCell(
            cell_type=cell.get("cell_type", "code"),
            source=source,
            metadata=cell.get("metadata", {}),
            execution_count=cell.get("execution_count"),
            outputs=cell.get("outputs", []) if include_outputs else None,
            id=cell.get("id"),
        )
        processed_cells.append(processed_cell)

    return NotebookReadResult(
        path=str(path.absolute()),
        num_cells=len(processed_cells),
        cells=processed_cells,
        metadata=notebook_data.get("metadata", {}),
    )


# NotebookEdit tool
def create_notebook_edit_tool() -> dict[str, Any]:
    """Create NotebookEdit tool definition.

    Returns:
        Tool definition for NotebookEdit
    """
    return {
        "name": "notebook_edit",
        "description": """Edit a Jupyter notebook cell.

This tool allows you to modify, insert, or delete cells in a Jupyter notebook.

Operations:
- replace: Replace cell content (default)
- insert: Insert a new cell
- delete: Delete a cell

Use this when you need to:
- Modify code or markdown cells
- Add new cells to a notebook
- Remove cells
- Update cell metadata""",
        "input_schema": {
            "type": "object",
            "properties": {
                "notebook_path": {
                    "type": "string",
                    "description": "Absolute path to the Jupyter notebook file",
                },
                "cell_index": {
                    "type": "integer",
                    "description": "Index of the cell to edit (0-based)",
                },
                "new_source": {
                    "type": "string",
                    "description": "New source content for the cell",
                },
                "cell_type": {
                    "type": "string",
                    "enum": ["code", "markdown", "raw"],
                    "description": "Type of cell (required for insert operation)",
                },
                "operation": {
                    "type": "string",
                    "enum": ["replace", "insert", "delete"],
                    "description": "Operation to perform (default: replace)",
                },
            },
            "required": ["notebook_path", "cell_index"],
        },
    }


def notebook_edit(
    notebook_path: str,
    cell_index: int,
    new_source: str = "",
    cell_type: Literal["code", "markdown", "raw"] = "code",
    operation: Literal["replace", "insert", "delete"] = "replace",
) -> dict[str, Any]:
    """Edit a Jupyter notebook cell.

    Args:
        notebook_path: Path to the notebook file
        cell_index: Index of the cell (0-based)
        new_source: New source content
        cell_type: Cell type for insert operation
        operation: Operation to perform

    Returns:
        Dictionary with operation result

    Raises:
        FileNotFoundError: If notebook doesn't exist
        ValueError: If operation is invalid
        IndexError: If cell_index is out of range
    """
    path = Path(notebook_path)

    if not path.exists():
        raise FileNotFoundError(f"Notebook not found: {notebook_path}")

    if not path.suffix == ".ipynb":
        raise ValueError(f"File is not a Jupyter notebook: {notebook_path}")

    # Read notebook
    with path.open(encoding="utf-8") as f:
        notebook_data = json.load(f)

    cells = notebook_data.get("cells", [])

    # Perform operation
    if operation == "delete":
        if cell_index < 0 or cell_index >= len(cells):
            raise IndexError(f"Cell index {cell_index} out of range (0-{len(cells)-1})")
        deleted_cell = cells.pop(cell_index)
        result_msg = f"Deleted cell {cell_index}"
        result_data = {"deleted_cell": deleted_cell}

    elif operation == "insert":
        if cell_index < 0 or cell_index > len(cells):
            raise IndexError(f"Cell index {cell_index} out of range (0-{len(cells)})")

        # Create new cell
        new_cell: dict[str, Any] = {
            "cell_type": cell_type,
            "source": new_source.split("\n") if "\n" in new_source else [new_source],
            "metadata": {},
        }

        if cell_type == "code":
            new_cell["execution_count"] = None
            new_cell["outputs"] = []

        cells.insert(cell_index, new_cell)
        result_msg = f"Inserted {cell_type} cell at index {cell_index}"
        result_data = {"new_cell": new_cell}

    else:  # replace
        if cell_index < 0 or cell_index >= len(cells):
            raise IndexError(f"Cell index {cell_index} out of range (0-{len(cells)-1})")

        old_source = cells[cell_index].get("source", "")
        cells[cell_index]["source"] = new_source.split("\n") if "\n" in new_source else [new_source]

        # Update cell type if specified
        if cell_type != cells[cell_index].get("cell_type"):
            cells[cell_index]["cell_type"] = cell_type
            if cell_type == "code":
                cells[cell_index]["execution_count"] = None
                cells[cell_index]["outputs"] = []
            else:
                cells[cell_index].pop("execution_count", None)
                cells[cell_index].pop("outputs", None)

        result_msg = f"Replaced cell {cell_index}"
        result_data = {"old_source": old_source, "new_source": new_source}

    # Write back to file
    with path.open("w", encoding="utf-8") as f:
        json.dump(notebook_data, f, indent=2, ensure_ascii=False)

    return {
        "success": True,
        "message": result_msg,
        "path": str(path.absolute()),
        "operation": operation,
        "cell_index": cell_index,
        **result_data,
    }


# Helper function to get all notebook tools
def get_all_notebook_tools() -> list[dict[str, Any]]:
    """Get all notebook operation tools.

    Returns:
        List of notebook tool definitions
    """
    return [
        create_notebook_read_tool(),
        create_notebook_edit_tool(),
    ]


__all__ = [
    "NotebookCell",
    "NotebookContent",
    "NotebookReadResult",
    "create_notebook_edit_tool",
    "create_notebook_read_tool",
    "get_all_notebook_tools",
    "notebook_edit",
    "notebook_read",
]
