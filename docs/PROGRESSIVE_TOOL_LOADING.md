# Progressive Tool Loading Implementation Plan

Based on [Anthropic's Code Execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp) approach.

## Executive Summary

**Goal**: Reduce token usage by 98%+ through progressive tool discovery and code execution.

| Metric | Current State | Target State |
|--------|---------------|--------------|
| Tool definitions per call | ~15 (150K tokens) | 3-5 core (2K tokens) |
| Data flow | All through model | Stay in execution env |
| Tool discovery | None (all upfront) | Filesystem-based |
| Token savings | N/A | **98.7%** |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         CURRENT STATE                           │
├─────────────────────────────────────────────────────────────────┤
│  User → LLM Handler → [ALL 15 TOOL DEFINITIONS] → Claude API   │
│                              ↓                                  │
│                    Tool Call → Result → Model → Next Call       │
│                    (All data flows through model context)       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         TARGET STATE                            │
├─────────────────────────────────────────────────────────────────┤
│  User → LLM Handler → [3 CORE TOOLS] → Claude API              │
│                              ↓                                  │
│  Agent discovers tools via: search_tools → read_file → glob    │
│                              ↓                                  │
│  Agent writes code that calls tools directly:                   │
│    result = read_file("data.json")  # Data stays in exec env   │
│    write_file("output.json", processed_result)                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## What We Keep (100% Reuse)

| Component | Location | Reuse Strategy |
|-----------|----------|----------------|
| `ToolRegistry` | `core/tool_registry.py` | Extend with manifest generation |
| `MCPClient/Manager` | `core/mcp.py` | Add tool file generation |
| `SkillRegistry` | `core/skills.py` | Connect with tool discovery |
| `bash` tool | `tools/bash.py` | Enhance for code execution |
| File tools | `tools/file.py` | Keep as-is, add to manifest |
| Permission system | `cli/permissions.py` | Keep for security |

---

## Phase 1: Tool Manifest System

### 1.1 Create Tool Manifest Generator

**New File**: `src/devorbit/core/tool_manifest.py`

```python
"""Tool manifest generation for filesystem-based discovery."""

from pathlib import Path
from typing import Any
import json

from .tool_registry import get_tool_registry, ToolCategory


class ToolManifestGenerator:
    """Generates tool files for filesystem-based discovery.

    Creates a .devorbit/tools/ directory structure:

    .devorbit/tools/
    ├── index.json          <- Tool summary (name + one-line desc)
    ├── file/
    │   ├── read_file.json
    │   ├── write_file.json
    │   └── edit_file.json
    ├── bash/
    │   └── bash.json
    └── search/
        ├── grep.json
        └── glob.json
    """

    def __init__(self) -> None:
        self.registry = get_tool_registry()

    def generate(self, output_dir: Path | None = None) -> Path:
        """Generate tool manifest files.

        Args:
            output_dir: Output directory (default: .devorbit/tools)

        Returns:
            Path to generated manifest directory
        """
        output_dir = output_dir or Path.cwd() / ".devorbit" / "tools"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate index.json with summary of all tools
        index = self._generate_index()
        (output_dir / "index.json").write_text(
            json.dumps(index, indent=2)
        )

        # Generate per-category directories and tool files
        for tool in self.registry.get_all_tools():
            category_dir = output_dir / tool.category.value
            category_dir.mkdir(exist_ok=True)

            tool_file = category_dir / f"{tool.name}.json"
            tool_file.write_text(
                json.dumps(tool.definition, indent=2)
            )

        return output_dir

    def _generate_index(self) -> dict[str, Any]:
        """Generate tool index with minimal info."""
        tools_by_category: dict[str, list[dict]] = {}

        for tool in self.registry.get_all_tools():
            category = tool.category.value
            if category not in tools_by_category:
                tools_by_category[category] = []

            tools_by_category[category].append({
                "name": tool.name,
                "description": tool.description[:100],  # First 100 chars
                "path": f"{category}/{tool.name}.json",
            })

        return {
            "version": "1.0.0",
            "total_tools": self.registry.count(),
            "categories": list(tools_by_category.keys()),
            "tools": tools_by_category,
        }
```

### 1.2 Index File Format

The `index.json` provides a lightweight overview:

```json
{
  "version": "1.0.0",
  "total_tools": 15,
  "categories": ["file", "bash", "search", "network", "agent"],
  "tools": {
    "file": [
      {"name": "read_file", "description": "Read contents of a file", "path": "file/read_file.json"},
      {"name": "write_file", "description": "Write content to a file", "path": "file/write_file.json"},
      {"name": "edit_file", "description": "Edit a file with search/replace", "path": "file/edit_file.json"}
    ],
    "bash": [
      {"name": "bash", "description": "Execute shell commands", "path": "bash/bash.json"}
    ],
    "search": [
      {"name": "grep", "description": "Search for patterns in files", "path": "search/grep.json"},
      {"name": "glob", "description": "Find files matching patterns", "path": "search/glob.json"}
    ]
  }
}
```

---

## Phase 2: Progressive Tool Loading

### 2.1 Core Tools (Always Sent)

Only these tools are sent with every API call:

```python
CORE_TOOLS = [
    "bash",           # Execute commands
    "read_file",      # Read files (including tool definitions)
    "search_tools",   # NEW: Discover available tools
    "glob",           # Find files
]
```

### 2.2 Create `search_tools` Meta-Tool

**New File**: `src/devorbit/tools/discovery.py`

```python
"""Tool discovery for progressive loading."""

from typing import Any
from devorbit.core.tool_registry import get_tool_registry, tool, ToolCategory


@tool(category="meta")
def search_tools(
    query: str = "",
    category: str | None = None,
    detail_level: str = "summary",
) -> dict[str, Any]:
    """Search available tools by name, description, or category.

    Use this to discover tools you need for a task. After finding a tool,
    read its definition file at .devorbit/tools/{category}/{name}.json
    to understand the full interface.

    Args:
        query: Search query (searches name and description). Empty = list all.
        category: Filter by category: file, bash, search, network, agent, mcp
        detail_level: How much detail to return:
            - "name": Just tool names (minimal tokens)
            - "summary": Name + one-line description (default)
            - "full": Complete definition with parameters

    Returns:
        Dictionary with matching tools at requested detail level

    Example:
        # Find tools for reading files
        search_tools(query="read")

        # List all file tools with just names
        search_tools(category="file", detail_level="name")

        # Get full definition for a specific tool
        search_tools(query="edit_file", detail_level="full")
    """
    registry = get_tool_registry()

    # Get tools, optionally filtered by category
    cat = ToolCategory(category) if category else None
    all_tools = registry.get_all_tools(category=cat)

    # Filter by query if provided
    if query:
        query_lower = query.lower()
        all_tools = [
            t for t in all_tools
            if query_lower in t.name.lower() or query_lower in t.description.lower()
        ]

    # Format based on detail level
    results = []
    for tool in all_tools:
        if detail_level == "name":
            results.append(tool.name)
        elif detail_level == "summary":
            results.append({
                "name": tool.name,
                "description": tool.description[:100],
                "category": tool.category.value,
            })
        else:  # full
            results.append({
                "name": tool.name,
                "description": tool.description,
                "category": tool.category.value,
                "definition": tool.definition,
            })

    return {
        "count": len(results),
        "detail_level": detail_level,
        "tools": results,
        "hint": "Use read_file('.devorbit/tools/{category}/{name}.json') for full definition"
                if detail_level != "full" else None,
    }
```

### 2.3 Modify LLM Handler

**File**: `src/devorbit/cli/llm.py` (line ~183 and ~318)

```python
# Before:
tools=self.session.tool_executor.get_tool_definitions()

# After:
tools=self.session.tool_executor.get_core_tools()
```

### 2.4 Add Core Tools Method to ToolExecutor

**File**: `src/devorbit/cli/tools.py`

```python
CORE_TOOL_NAMES = ["bash", "read_file", "search_tools", "glob"]

def get_core_tools(self) -> list[dict[str, Any]]:
    """Get only core tools for progressive loading.

    Returns minimal tool set. Agent discovers others via search_tools.
    """
    all_tools = self.get_tool_definitions()
    return [t for t in all_tools if t.get("name") in CORE_TOOL_NAMES]
```

---

## Phase 3: Code Execution Environment

### 3.1 Execute Code Tool

**New File**: `src/devorbit/tools/code_exec.py`

```python
"""Code execution environment for efficient tool composition."""

import sys
import io
import traceback
from typing import Any
from contextlib import redirect_stdout, redirect_stderr

from devorbit.core.tool_registry import tool


@tool(category="meta")
def execute_code(
    code: str,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Execute Python code with access to devorbit tools.

    Use this to compose multiple tool calls efficiently. Data stays in the
    execution environment and doesn't flow through the model context.

    Available imports:
        from devorbit.tools.file import read_file, write_file, edit_file
        from devorbit.tools.search import grep_code, glob_files
        from devorbit.tools.bash import bash

    Args:
        code: Python code to execute
        timeout: Maximum execution time in seconds

    Returns:
        Dictionary with:
        - success: Whether execution succeeded
        - stdout: Captured stdout
        - stderr: Captured stderr
        - result: Last expression value (if any)
        - error: Error message (if failed)

    Example:
        execute_code('''
from devorbit.tools.file import read_file, write_file
import json

# Read config, modify, write back - data never enters model context!
config = json.loads(read_file(file_path="config.json")["content"])
config["version"] = "2.0.0"
write_file(file_path="config.json", content=json.dumps(config, indent=2))
print(f"Updated config to version {config['version']}")
        ''')
    """
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    result = None
    error = None

    # Prepare execution namespace with devorbit tools
    namespace = {
        "__builtins__": __builtins__,
        "devorbit": __import__("devorbit"),
    }

    try:
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            # Execute code
            exec(code, namespace)

            # Try to get last expression value
            if "_" in namespace:
                result = namespace["_"]

    except Exception as e:
        error = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"

    return {
        "success": error is None,
        "stdout": stdout_capture.getvalue(),
        "stderr": stderr_capture.getvalue(),
        "result": str(result) if result is not None else None,
        "error": error,
    }
```

### 3.2 Benefits of Code Execution

| Scenario | Direct Tool Calls | Code Execution |
|----------|------------------|----------------|
| Read file + update DB | 2 API rounds, full data through model | 1 round, data stays local |
| Process 100 files | 100+ API rounds, 500K+ tokens | 1 round with loop, ~5K tokens |
| Filter large dataset | All 10K rows through model | Filter in code, return summary |
| Chain 5 operations | 5 API rounds | 1 round with sequential code |

---

## Phase 4: MCP Integration

### 4.1 Auto-Generate Tool Files from MCP Servers

**File**: `src/devorbit/core/mcp.py` (add to `MCPManager`)

```python
async def generate_tool_files(self, output_dir: Path | None = None) -> None:
    """Generate tool files for all connected MCP servers.

    Creates .devorbit/tools/mcp/{server_name}/ structure with
    tool definition files for filesystem-based discovery.

    Args:
        output_dir: Output directory (default: .devorbit/tools/mcp)
    """
    output_dir = output_dir or Path.cwd() / ".devorbit" / "tools" / "mcp"

    for name, client in self.clients.items():
        server_dir = output_dir / name
        server_dir.mkdir(parents=True, exist_ok=True)

        tools = await client.list_tools()

        for tool in tools:
            tool_file = server_dir / f"{tool['name']}.json"
            tool_file.write_text(json.dumps(tool, indent=2))

        # Create server index
        index = {
            "server": name,
            "tool_count": len(tools),
            "tools": [{"name": t["name"], "description": t.get("description", "")[:100]}
                      for t in tools],
        }
        (server_dir / "index.json").write_text(json.dumps(index, indent=2))
```

### 4.2 Final Directory Structure

```
.devorbit/
├── tools/
│   ├── index.json           <- Master index
│   ├── file/
│   │   ├── read_file.json
│   │   ├── write_file.json
│   │   └── edit_file.json
│   ├── bash/
│   │   └── bash.json
│   ├── search/
│   │   ├── grep.json
│   │   └── glob.json
│   └── mcp/
│       ├── notion/
│       │   ├── index.json
│       │   ├── search.json
│       │   └── create_page.json
│       ├── github/
│       │   ├── index.json
│       │   └── list_repos.json
│       └── slack/
│           ├── index.json
│           └── send_message.json
└── skills/
    ├── analyze_codebase.md
    └── generate_tests.md
```

---

## Phase 5: Integration & Cleanup

### 5.1 Files to Create

| File | Purpose |
|------|---------|
| `src/devorbit/core/tool_manifest.py` | Manifest generation |
| `src/devorbit/tools/discovery.py` | `search_tools` meta-tool |
| `src/devorbit/tools/code_exec.py` | Code execution environment |

### 5.2 Files to Modify

| File | Changes |
|------|---------|
| `src/devorbit/core/tool_registry.py` | Add `generate_manifest()` method |
| `src/devorbit/core/mcp.py` | Add `generate_tool_files()` to MCPManager |
| `src/devorbit/cli/llm.py` | Use `get_core_tools()` instead of all tools |
| `src/devorbit/cli/tools.py` | Add `get_core_tools()` and `CORE_TOOL_NAMES` |
| `src/devorbit/tools/__init__.py` | Register new tools, consolidate registration |

### 5.3 Code Cleanup

1. Remove duplicate tool definitions
2. Consolidate tool registration into registry
3. Remove old non-registry patterns
4. Add feature flag for progressive loading

---

## Configuration

Add to `.devorbit.json`:

```json
{
  "progressive_loading": {
    "enabled": true,
    "core_tools": ["bash", "read_file", "search_tools", "glob"],
    "fallback_to_full": true,
    "fallback_after_failures": 3
  },
  "code_execution": {
    "enabled": true,
    "timeout": 30,
    "max_memory_mb": 256
  }
}
```

---

## Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Tool definition tokens | ~15K | ~2K | API usage |
| API rounds per task | 5-10 | 1-3 | Log analysis |
| Average response time | 3-5s | 1-2s | Latency monitoring |
| Test coverage | N/A | >80% | pytest-cov |

---

## Migration Path

### Phase 1: Opt-in (Feature Flag)

```python
# In .devorbit.json
{"progressive_loading": {"enabled": true}}
```

### Phase 2: Default with Opt-out

```python
# In .devorbit.json
{"progressive_loading": {"enabled": false}}  # Explicit disable
```

### Phase 3: Full Migration

Remove fallback to full tool list, progressive loading is the only mode.

---

## References

- [Anthropic: Code Execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp)
- [Cloudflare: Code Mode](https://developers.cloudflare.com/workers-ai/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
