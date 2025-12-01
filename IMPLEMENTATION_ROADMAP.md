# Devorbit SDK - Production Implementation Roadmap

## Current Status

✅ **PR Ready**: `phase-9-performance` branch pushed
🔗 **Create PR**: https://github.com/tejas96/py-devorbit-code-sdk/pull/new/phase-9-performance

---

## Implementation Phases Overview

| Phase | Focus | Priority | Timeline |
|-------|-------|----------|----------|
| **Phase 0** | Merge PR, Fresh Start | P0 | Today |
| **Phase 1** | Multi-Tenant Foundation | P0 | 2-3 days |
| **Phase 2** | Progressive Tool Loading | P1 | 2-3 days |
| **Phase 3** | Code Execution Environment | P1 | 2 days |
| **Phase 4** | Production Hardening | P2 | 2-3 days |

---

## Phase 0: Merge & Fresh Start (Today)

### Steps
1. ✅ Push `phase-9-performance` branch
2. ⏳ Create PR on GitHub
3. ⏳ Review changes
4. ⏳ Merge to main
5. ⏳ Create new branch: `phase-10-production-ready`

### What's in the PR
- 13 files changed, 1213 insertions(+), 200 deletions(-)
- Bug fixes for permissions, tools, streaming
- 303 tests passing

---

## Phase 1: Multi-Tenant Foundation (P0 - CRITICAL)

### 1.1 Create UserContext Class

**File**: `src/devorbit/core/user_context.py`

```python
"""User-scoped context for multi-tenant support."""

import threading
import uuid
from dataclasses import dataclass, field
from typing import Any

@dataclass
class UserContext:
    """Isolated context for each user/agent session.

    All state that was previously global is now scoped to this context.
    Each user gets their own isolated state.
    """

    user_id: str
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Per-user state (previously global!)
    bash_sessions: dict[str, Any] = field(default_factory=dict)
    todo_state: list[dict] = field(default_factory=list)
    active_tasks: dict[str, Any] = field(default_factory=dict)
    conversation_history: list[dict] = field(default_factory=list)

    # Per-user registries (copies of global with user customizations)
    _tool_overrides: dict[str, bool] = field(default_factory=dict)  # tool enable/disable
    _permission_rules: list[Any] = field(default_factory=list)

    # Thread safety
    _lock: threading.RLock = field(default_factory=threading.RLock)

    def __post_init__(self):
        """Initialize derived state."""
        self._created_at = time.time()
        self._last_activity = time.time()

    def touch(self) -> None:
        """Update last activity timestamp."""
        self._last_activity = time.time()


# Thread-safe context registry
class ContextRegistry:
    """Global registry for user contexts."""

    def __init__(self):
        self._contexts: dict[str, UserContext] = {}
        self._lock = threading.Lock()

    def get(self, user_id: str, session_id: str | None = None) -> UserContext:
        """Get or create user context."""
        key = f"{user_id}:{session_id or 'default'}"
        with self._lock:
            if key not in self._contexts:
                self._contexts[key] = UserContext(
                    user_id=user_id,
                    session_id=session_id or str(uuid.uuid4())
                )
            return self._contexts[key]

    def remove(self, user_id: str, session_id: str | None = None) -> bool:
        """Remove user context."""
        key = f"{user_id}:{session_id or 'default'}"
        with self._lock:
            if key in self._contexts:
                del self._contexts[key]
                return True
            return False

    def cleanup_stale(self, max_age: float = 3600) -> int:
        """Remove stale contexts older than max_age seconds."""
        now = time.time()
        removed = 0
        with self._lock:
            stale_keys = [
                k for k, v in self._contexts.items()
                if now - v._last_activity > max_age
            ]
            for key in stale_keys:
                del self._contexts[key]
                removed += 1
        return removed


# Global context registry (the ONLY global state needed)
_context_registry = ContextRegistry()

def get_context(user_id: str, session_id: str | None = None) -> UserContext:
    """Get user context (convenience function)."""
    return _context_registry.get(user_id, session_id)
```

### 1.2 Refactor Global State Files

| File | Current Global | Change To |
|------|---------------|-----------|
| `tools/bash.py` | `_BASH_SESSIONS` | `context.bash_sessions` |
| `tools/todo.py` | `_TODO_STATE` | `context.todo_state` |
| `tools/agent.py` | `_ACTIVE_TASKS` | `context.active_tasks` |

### 1.3 Add Context Parameter to Tools

```python
# BEFORE
def bash(command: str, cwd: str | None = None) -> dict:
    global _BASH_SESSIONS  # ❌ Global!
    ...

# AFTER
def bash(
    command: str,
    cwd: str | None = None,
    _context: UserContext | None = None,  # ✅ Context injected
) -> dict:
    ctx = _context or get_current_context()
    sessions = ctx.bash_sessions  # ✅ User-scoped!
    ...
```

### 1.4 Thread Safety Checklist

- [ ] Add `threading.RLock` to UserContext
- [ ] Add `threading.Lock` to ContextRegistry
- [ ] Add locks to ToolRegistry operations
- [ ] Add locks to SkillRegistry operations
- [ ] Add locks to PermissionManager operations

---

## Phase 2: Progressive Tool Loading (P1)

### 2.1 Create Tool Manifest Generator

**File**: `src/devorbit/core/tool_manifest.py`

```python
"""Generate tool definitions as files for progressive discovery."""

class ToolManifestGenerator:
    def generate(self, output_dir: Path) -> Path:
        """Generate .devorbit/tools/ structure."""
        # Creates index.json + per-tool JSON files
```

### 2.2 Create search_tools Meta-Tool

**File**: `src/devorbit/tools/discovery.py`

```python
@tool(category="meta")
def search_tools(
    query: str = "",
    category: str | None = None,
    detail_level: str = "summary",
) -> dict[str, Any]:
    """Search available tools by name/description."""
```

### 2.3 Modify LLM Handler

**File**: `src/devorbit/cli/llm.py`

```python
# Change from:
tools=self.session.tool_executor.get_tool_definitions()

# To:
tools=self.session.tool_executor.get_core_tools()
```

### 2.4 Core Tools List

```python
CORE_TOOLS = [
    "bash",           # Execute commands
    "read_file",      # Read files (including tool definitions)
    "search_tools",   # Discover available tools
    "glob",           # Find files
]
```

---

## Phase 3: Code Execution Environment (P1)

### 3.1 Create Code Execution Tool

**File**: `src/devorbit/tools/code_exec.py`

```python
@tool(category="meta")
def execute_code(
    code: str,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Execute Python code with access to devorbit tools.

    Data stays in execution environment - doesn't flow through model!
    """
```

### 3.2 MCP Tool File Generation

**File**: `src/devorbit/core/mcp.py` (enhance MCPManager)

```python
async def generate_tool_files(self, output_dir: Path) -> None:
    """Generate tool files for all connected MCP servers."""
```

---

## Phase 4: Production Hardening (P2)

### 4.1 Rate Limiting

```python
class RateLimiter:
    """Per-user rate limiting."""

    def __init__(self, requests_per_minute: int = 60):
        self.rpm = requests_per_minute
        self._user_requests: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def check(self, user_id: str) -> bool:
        """Check if user can make a request."""
        ...
```

### 4.2 Resource Quotas

```python
@dataclass
class ResourceQuota:
    """Per-user resource limits."""

    max_sessions: int = 10
    max_concurrent_tasks: int = 5
    max_file_size_mb: int = 100
    max_execution_time: float = 300  # 5 minutes
```

### 4.3 Audit Logging

```python
class AuditLogger:
    """Log all tool executions for compliance."""

    def log_tool_execution(
        self,
        user_id: str,
        tool_name: str,
        params: dict,
        result: Any,
        duration: float,
    ) -> None:
        """Log tool execution with full context."""
```

---

## File Changes Summary

### New Files to Create

| File | Purpose |
|------|---------|
| `src/devorbit/core/user_context.py` | Multi-tenant context |
| `src/devorbit/core/tool_manifest.py` | Manifest generation |
| `src/devorbit/tools/discovery.py` | search_tools meta-tool |
| `src/devorbit/tools/code_exec.py` | Code execution |
| `src/devorbit/core/rate_limiter.py` | Rate limiting |
| `src/devorbit/core/audit.py` | Audit logging |

### Files to Modify

| File | Changes |
|------|---------|
| `tools/bash.py` | Use UserContext instead of global |
| `tools/todo.py` | Use UserContext instead of global |
| `tools/agent.py` | Use UserContext instead of global |
| `cli/llm.py` | Use progressive tool loading |
| `cli/tools.py` | Add get_core_tools() |
| `core/mcp.py` | Add generate_tool_files() |

---

## Testing Strategy

### Unit Tests
- Test UserContext isolation
- Test thread safety with concurrent access
- Test rate limiting
- Test tool manifest generation

### Integration Tests
- Multi-user simulation
- Concurrent tool execution
- MCP integration with progressive loading

### Load Tests
- 100 concurrent users
- 1000 requests/minute
- Memory usage under load

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Concurrent users | 1 | 100+ |
| Token usage per call | ~15K | ~2K |
| Thread safety | Partial | Full |
| Session isolation | None | Complete |
| Test coverage | ~80% | >90% |

---

## Next Steps

1. **Create PR** for current changes
2. **Merge to main**
3. **Create `phase-10-production-ready` branch**
4. **Start Phase 1 implementation**
