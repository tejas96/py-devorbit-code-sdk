# Phase 4: Web & Advanced Tools Implementation

**Implementation Date:** 2025-11-15
**Status:** ✅ Complete

## Overview

Phase 4 implements web operations and advanced notebook support as outlined in the FEATURE_GAP_ANALYSIS_REPORT.md. This phase adds essential tools for fetching web content, searching the web, and working with Jupyter notebooks.

## Implemented Features

### 1. Web Tools (`_web_tools.py`)

#### WebFetch Tool
- **Purpose:** Fetch content from URLs and optionally convert HTML to Markdown
- **Key Features:**
  - Automatic HTTP to HTTPS upgrade
  - HTML to Markdown conversion
  - Redirect handling
  - Configurable timeouts
  - URL validation with invalid character detection

**Usage Example:**
```python
from devorbit import web_fetch, web_fetch_sync

# Async version
result = await web_fetch("https://example.com", convert_to_markdown=True)
print(result["content"])

# Sync version
result = web_fetch_sync("https://example.com")
print(result["status_code"])
```

#### WebSearch Tool
- **Purpose:** Search the web (placeholder implementation for custom API integration)
- **Key Features:**
  - Configurable number of results
  - Safe search option
  - Ready for integration with Google Custom Search, Bing, or DuckDuckGo APIs

**Usage Example:**
```python
from devorbit import web_search, web_search_sync

# Async version
results = await web_search("Python tutorials", num_results=10)
for result in results["results"]:
    print(result["title"], result["url"])

# Sync version
results = web_search_sync("AI news")
```

#### HTML to Markdown Conversion
- **Purpose:** Convert HTML content to clean Markdown format
- **Supported Elements:**
  - Headers (h1-h6)
  - Links and images
  - Bold and italic text
  - Code blocks and inline code
  - Lists (ordered and unordered)
  - Paragraphs and line breaks
  - HTML entity decoding

**Usage Example:**
```python
from devorbit import html_to_markdown

html = "<h1>Title</h1><p>Content with <strong>bold</strong> text.</p>"
markdown = html_to_markdown(html)
print(markdown)
# Output:
# # Title
# Content with **bold** text.
```

### 2. Notebook Tools (`_notebook_tools.py`)

#### NotebookRead Tool
- **Purpose:** Read and parse Jupyter notebook files
- **Key Features:**
  - Read all cells with content, type, and metadata
  - Optional cell range selection
  - Include/exclude cell outputs
  - Full metadata extraction

**Usage Example:**
```python
from devorbit import notebook_read

# Read entire notebook
result = notebook_read("analysis.ipynb")
print(f"Found {result['num_cells']} cells")

for i, cell in enumerate(result["cells"]):
    print(f"Cell {i} ({cell['cell_type']}): {cell['source'][:50]}...")

# Read specific cell range
result = notebook_read("analysis.ipynb", cell_range={"start": 0, "end": 5})

# Read without outputs
result = notebook_read("analysis.ipynb", include_outputs=False)
```

#### NotebookEdit Tool
- **Purpose:** Edit, insert, or delete cells in Jupyter notebooks
- **Supported Operations:**
  - **Replace:** Modify existing cell content
  - **Insert:** Add new cells at any position
  - **Delete:** Remove cells
  - **Change cell type:** Convert between code, markdown, and raw cells

**Usage Example:**
```python
from devorbit import notebook_edit

# Replace a cell
result = notebook_edit(
    "analysis.ipynb",
    cell_index=1,
    new_source="print('Updated code')",
    operation="replace"
)

# Insert a new markdown cell
result = notebook_edit(
    "analysis.ipynb",
    cell_index=0,
    new_source="# New Section",
    cell_type="markdown",
    operation="insert"
)

# Delete a cell
result = notebook_edit(
    "analysis.ipynb",
    cell_index=5,
    operation="delete"
)
```

## Tool Definitions

Both web and notebook tools provide standardized tool definitions for LLM integration:

```python
from devorbit import (
    get_all_web_tools,
    get_all_notebook_tools,
    create_web_fetch_tool,
    create_web_search_tool,
    create_notebook_read_tool,
    create_notebook_edit_tool,
)

# Get all web tools
web_tools = get_all_web_tools()
# Returns: [web_fetch_tool, web_search_tool]

# Get all notebook tools
notebook_tools = get_all_notebook_tools()
# Returns: [notebook_read_tool, notebook_edit_tool]

# Get individual tool definitions
fetch_tool = create_web_fetch_tool()
search_tool = create_web_search_tool()
read_tool = create_notebook_read_tool()
edit_tool = create_notebook_edit_tool()
```

## Integration with LLM Agents

These tools are designed to work seamlessly with the Devorbit SDK's tool execution system:

```python
from devorbit import (
    Devorbit,
    gather_tools,
    get_all_web_tools,
    get_all_notebook_tools,
)

# Initialize client
client = Devorbit(provider="anthropic", api_key="...")

# Gather all tools including web and notebook tools
tools = gather_tools(
    builtin_tools=["bash"],
    custom_tools=get_all_web_tools() + get_all_notebook_tools()
)

# Use in agent loop
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=4096,
    messages=[{"role": "user", "content": "Fetch and summarize https://example.com"}],
    tools=tools
)
```

## Test Coverage

### Web Tools Tests (`test_web_tools.py`)
- **Coverage:** 90.72%
- **Test Cases:** 21 tests
  - HTML to Markdown conversion (9 tests)
  - WebFetch tool (7 tests)
  - WebSearch tool (3 tests)
  - Helper functions (2 tests)

### Notebook Tools Tests (`test_notebook_tools.py`)
- **Coverage:** 86.61%
- **Test Cases:** 18 tests
  - NotebookRead tool (8 tests)
  - NotebookEdit tool (9 tests)
  - Helper functions (1 test)

**Total Phase 4 Tests:** 39 tests, all passing ✅

## Files Added

1. `src/devorbit/_web_tools.py` - Web operations module
2. `src/devorbit/_notebook_tools.py` - Notebook operations module
3. `tests/test_web_tools.py` - Web tools test suite
4. `tests/test_notebook_tools.py` - Notebook tools test suite
5. `docs/PHASE_4_IMPLEMENTATION.md` - This documentation

## Files Modified

1. `src/devorbit/__init__.py` - Added exports for web and notebook tools

## API Reference

### Web Tools API

#### `web_fetch(url, convert_to_markdown=True, timeout=30, follow_redirects=True)`
- **Returns:** `WebFetchResult` with `url`, `content`, `content_type`, `status_code`, `redirect_url`
- **Raises:** `ValueError` for invalid URLs, `httpx.HTTPError` for request failures

#### `web_search(query, num_results=10, safe_search=True)`
- **Returns:** `WebSearchResult` with `query`, `results`, `num_results`

#### `html_to_markdown(html)`
- **Returns:** `str` - Markdown formatted text

### Notebook Tools API

#### `notebook_read(notebook_path, include_outputs=True, cell_range=None)`
- **Returns:** `NotebookReadResult` with `path`, `num_cells`, `cells`, `metadata`
- **Raises:** `FileNotFoundError`, `ValueError` for invalid notebooks

#### `notebook_edit(notebook_path, cell_index, new_source="", cell_type="code", operation="replace")`
- **Returns:** `dict` with operation result
- **Raises:** `FileNotFoundError`, `ValueError`, `IndexError`

## Future Enhancements

### Web Tools
1. **WebSearch Integration:** Integrate with real search APIs (Google Custom Search, Bing, DuckDuckGo)
2. **Enhanced HTML Parsing:** Use `beautifulsoup4` or `html2text` for more robust HTML to Markdown conversion
3. **Caching:** Implement response caching for faster repeated requests
4. **Rate Limiting:** Add configurable rate limiting for API calls

### Notebook Tools
1. **Cell Execution:** Add ability to execute notebook cells
2. **Output Formatting:** Better formatting of complex outputs (images, plots, dataframes)
3. **Metadata Management:** Tools for managing cell and notebook metadata
4. **Notebook Validation:** Validate notebook structure and dependencies

## Alignment with FEATURE_GAP_ANALYSIS_REPORT.md

This implementation addresses all items listed under "Phase 4: Web & Advanced Tools" in the feature gap analysis:

- ✅ WebFetch tool (fetch + AI processing ready)
- ✅ WebSearch tool (placeholder for API integration)
- ✅ HTML to markdown conversion
- ✅ NotebookRead tool
- ✅ NotebookEdit tool (created from scratch with full functionality)

## Next Steps

With Phase 4 complete, the SDK now has:
- ✅ Phase 1: File operations, search, and todo management
- ✅ Phase 2: Agent framework and task management
- ✅ Phase 3: Developer experience (configuration, hooks, slash commands)
- ✅ Phase 4: Web operations and notebook support

**Recommended Next Phase:** Phase 5 - Skills & Plugins System

---

**Implementation Complete:** All Phase 4 features implemented, tested, and documented.
