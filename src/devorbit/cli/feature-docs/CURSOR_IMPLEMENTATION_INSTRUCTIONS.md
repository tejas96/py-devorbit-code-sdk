# CURSOR AI - Implementation Instructions for Devorbit CLI

## 🎯 CRITICAL: Read This First

**DO NOT create duplicate code or tools. ENHANCE existing codebase only.**

---

## 📋 Current System Architecture

### **What Already Exists:**

1. **Multi-Provider Support (CORE FEATURE - DO NOT REMOVE)**
   - ✅ Anthropic (Claude)
   - ✅ OpenAI (GPT)
   - ✅ Google (Gemini)
   - ✅ Mistral
   - ✅ Code Llama (if implemented)

2. **Basic CLI Structure**
   - ✅ Command-line interface foundation
   - ✅ Provider switching mechanism
   - ✅ Basic message handling
   - ✅ Multi-provider abstraction layer

3. **Existing SDK Integration**
   - ✅ Devorbit SDK with multi-provider support
   - ✅ Message API wrappers
   - ✅ Tool execution framework
   - ✅ MCP client integration

### **Current File Structure:**
```
src ->
-> devorbit/
|── providers/         # Multi-provider implementations
├── cli/
│   ├- main.py, session.py, repl.py, commands.py
├──

-> test
-> examples
-> docs
```

---

## 🚨 MANDATORY RULES

### **Rule 1: DO NOT Duplicate**
- ❌ Do NOT create new provider integration if it already exists
- ❌ Do NOT create new SDK layer
- ❌ Do NOT recreate tool execution framework
- ✅ USE existing Devorbit SDK functions
- ✅ ENHANCE existing CLI files
- ✅ EXTEND existing classes/functions

### **Rule 2: Multi-Provider is NON-NEGOTIABLE**
- ✅ PRESERVE all existing provider support
- ✅ MAINTAIN provider switching functionality
- ✅ ENSURE all features work with ALL providers
- ✅ TEST each feature across all providers
- ❌ Do NOT hardcode Anthropic-specific features

### **Rule 3: File Management**
- ✅ MODIFY existing files in place
- ✅ ADD new files only if absolutely necessary
- ✅ IMPORT and USE existing SDK functions
- ❌ Do NOT create parallel implementations

### **Rule 4: Backward Compatibility**
- ✅ MAINTAIN existing API contracts
- ✅ PRESERVE current configuration format
- ✅ KEEP existing command-line flags
- ✅ ENSURE existing code still works

---

## 📖 Implementation Strategy

### **Step 1: Analyze Current Codebase**
```bash
# Before making ANY changes:
1. Read ALL files in devorbit_cli/
2. Identify existing functions and classes
3. Map current architecture
4. List what's already implemented
5. Document what needs enhancement
```

### **Step 2: Plan Enhancement (Don't Code Yet)**
```
For each feature in the specification:
1. Check if similar functionality exists
2. Decide: Enhance existing OR Create new
3. If enhancing: Identify exact file and function
4. If creating: Justify why it's needed
5. Document integration points
```

### **Step 3: Implement Incrementally**
```
Priority Order:
1. Terminal UI enhancements (Rich/Textual)
2. Streaming response display
3. Built-in tools (Read, Write, Edit, Bash, Grep, Glob)
4. Slash command system
5. Permission system
6. Context management
7. Session persistence
8. MCP integration enhancements
9. Hooks system
10. Subagents
11. Advanced features
```

---

## 🔧 Specific Implementation Guidelines

### **Terminal UI (Phase 1)**

**Enhance existing UI files, don't recreate:**

```python
# CORRECT: Import and enhance existing
from devorbit_cli.ui import TerminalUI  # If exists
from rich.console import Console
from rich.live import Live

class EnhancedTerminalUI(TerminalUI):  # Extend existing
    def __init__(self):
        super().__init__()
        self.console = Console()
        # Add new features here
```

**WRONG: Creating from scratch:**
```python
# ❌ DON'T DO THIS if TerminalUI exists
class TerminalUI:  # Creating duplicate
    def __init__(self):
        # Rewriting everything...
```

### **Multi-Provider Integration (CRITICAL)**

**ALWAYS use existing provider layer:**

```python
# CORRECT: Use existing SDK
from devorbit import Devorbit

client = Devorbit(
    provider=user_selected_provider,  # anthropic, openai, gemini, etc.
    api_key=api_keys[user_selected_provider]
)

# Works with ALL providers
response = client.messages.create(
    model=model_name,
    messages=messages,
    tools=tools
)
```

**WRONG: Provider-specific code:**
```python
# ❌ DON'T DO THIS
if provider == "anthropic":
    from anthropic import Anthropic
    client = Anthropic(api_key=key)
elif provider == "openai":
    # Separate implementation
```

### **Tools Implementation**

**Check if tool framework exists first:**

```python
# CORRECT: Extend existing tool system
from devorbit.tools import BaseTool, ToolExecutor  # If exists

class ReadTool(BaseTool):  # Extend existing
    name = "Read"
    description = "Read file contents"

    def execute(self, **kwargs):
        # Implementation
        pass

# Register with existing executor
executor = ToolExecutor()
executor.register_tool(ReadTool())
```

**If tools don't exist, create minimal structure:**
```python
# Only if NO tool system exists
# Create in: devorbit_cli/tools/base.py
class ToolRegistry:
    """Minimal tool system that works with existing SDK"""
    pass
```

### **Configuration System**

**Enhance existing config, don't replace:**

```python
# CORRECT: Extend existing config
from devorbit_cli.config import Config  # If exists

class EnhancedConfig(Config):
    def __init__(self):
        super().__init__()
        # Add new config options
        self.load_project_config()
        self.load_devorbit_md()
```

---

## 📝 Code Integration Checklist

Before implementing ANY feature, check:

- [ ] Does this function/class already exist?
- [ ] Can I enhance existing code instead of creating new?
- [ ] Am I using the existing SDK functions?
- [ ] Does this work with ALL providers (not just Anthropic)?
- [ ] Am I modifying files in place (not creating duplicates)?
- [ ] Have I imported existing utilities?
- [ ] Is this backward compatible?
- [ ] Have I tested with multiple providers?

---

## 🎨 UI Enhancement Guidelines

### **Use Rich/Textual for Terminal UI**

```python
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.progress import Progress

# For interactive UI:
from textual.app import App
from textual.widgets import Input, RichLog

# Enhance existing UI, don't recreate terminal handling
```

### **Color Scheme (from specification)**

```python
COLORS = {
    'brand_orange': '#FF6B35',
    'brand_blue': '#004E89',
    'success': '#10B981',
    'warning': '#F59E0B',
    'error': '#EF4444',
    'primary_text': '#E6EDF3',
    # ... use colors from specification
}
```

---

## 🔌 Provider-Agnostic Implementation

**Every feature MUST work across all providers:**

### **Example: Streaming Response**
```python
def stream_response(self, provider: str, model: str, messages: list):
    """Works with ANY provider"""
    client = Devorbit(provider=provider)

    # SDK handles provider differences
    for chunk in client.messages.stream(model=model, messages=messages):
        self.display_chunk(chunk)  # Provider-agnostic display
```

### **Example: Tool Execution**
```python
def execute_tool(self, tool_name: str, tool_input: dict, provider: str):
    """Provider-agnostic tool execution"""
    tool = self.get_tool(tool_name)
    result = tool.execute(**tool_input)

    # Return in standard format for all providers
    return {
        "tool": tool_name,
        "result": result,
        "provider": provider  # Track but don't limit functionality
    }
```

---

## 📦 Dependencies Management

### **Check existing dependencies first:**
```bash
# Read existing requirements.txt or pyproject.toml
# Only add NEW dependencies if needed

# Likely already have:
- anthropic SDK
- openai SDK
- google-generativeai SDK
- mistralai SDK (maybe)

# May need to add for CLI:
- rich >= 13.0.0
- textual >= 0.50.0
- prompt-toolkit >= 3.0
- click >= 8.1.0 (if not present)
```

---

## 🚀 Implementation Phases (Prioritized)

### **Phase 1: Foundation (Week 1-2)**
1. Enhance terminal UI with Rich
2. Add streaming display
3. Improve input handling
4. Add color scheme from spec

### **Phase 2: Core Tools (Week 3-4)**
1. Implement Read, Write, Edit tools
2. Add Bash tool (persistent session)
3. Add Grep, Glob tools
4. Ensure all work with multiple providers

### **Phase 3: Commands & Config (Week 5-6)**
1. Slash command system
2. Configuration loading (DEVORBIT.md)
3. Custom commands
4. Command history

### **Phase 4: Advanced (Week 7-8)**
1. Permission system
2. Context management
3. Session persistence
4. MCP enhancements

### **Phase 5: Polish (Week 9-10)**
1. Hooks system
2. Subagents
3. Git integration
4. Error handling

---

## 💡 Key Integration Points

### **1. Using Existing SDK**
```python
# Always start with:
from devorbit import Devorbit, AsyncDevorbit
from devorbit.tools import ToolExecutor
from devorbit.mcp import MCPClient, MCPManager

# Build CLI on top of existing SDK
```

### **2. Provider Configuration**
```python
# Enhance existing provider config
PROVIDERS = {
    'anthropic': {
        'models': ['claude-sonnet-4-5', 'claude-opus-4-1', ...],
        'api_key_env': 'ANTHROPIC_API_KEY'
    },
    'openai': {
        'models': ['gpt-5', 'gpt-4-turbo', ...],
        'api_key_env': 'OPENAI_API_KEY'
    },
    'gemini': {
        'models': ['gemini-pro-2-5', 'gemini-flash-2', ...],
        'api_key_env': 'GOOGLE_API_KEY'
    },
    # Add more providers
}
```

### **3. Tool Registration**
```python
# Use existing tool framework if present
# Otherwise create minimal system
class ToolRegistry:
    def __init__(self):
        self.tools = {}
        self._register_builtin_tools()

    def register(self, tool):
        self.tools[tool.name] = tool
```

---

## ⚠️ Common Pitfalls to Avoid

### **❌ DON'T:**
1. Create new SDK when one exists
2. Hardcode Anthropic-specific features
3. Duplicate existing provider logic
4. Create parallel file structures
5. Ignore existing configuration
6. Break backward compatibility
7. Create provider-specific UI

### **✅ DO:**
1. Import and use existing SDK
2. Make features provider-agnostic
3. Enhance existing files
4. Respect current architecture
5. Maintain multi-provider support
6. Test with ALL providers
7. Keep consistent API

---

## 🧪 Testing Requirements

**Test EVERY feature with ALL providers:**

```python
def test_feature_with_all_providers():
    for provider in ['anthropic', 'openai', 'gemini', 'mistral']:
        client = Devorbit(provider=provider)
        result = client.some_feature()
        assert result.works()
```

---

## 📄 File Modification Guidelines

### **Priority: Modify > Extend > Create**

1. **Modify existing file** (if simple enhancement)
   ```python
   # In existing file: devorbit_cli/main.py
   # Add new functions/methods
   ```

2. **Extend existing class** (if major enhancement)
   ```python
   # Import existing
   from devorbit_cli.core import CLI

   # Extend it
   class EnhancedCLI(CLI):
       # Add features
   ```

3. **Create new file** (only if truly needed)
   ```python
   # Only create if:
   # - Feature is completely new
   # - Doesn't fit existing structure
   # - Can't extend existing files
   ```

---

## 🎯 Success Criteria

Your implementation is correct if:

✅ All existing functionality still works
✅ ALL providers (Anthropic, OpenAI, Gemini, Mistral) work
✅ No duplicate code/files created
✅ New features enhance existing files
✅ Configuration is backward compatible
✅ All features are provider-agnostic
✅ Multi-provider switching works seamlessly
✅ Tests pass for all providers

---

## 📚 Reference Priority

When implementing, reference in this order:

1. **Existing codebase** (highest priority)
2. **Devorbit SDK documentation** (if exists)
3. **Claude Code specification** (provided separately)
4. **Provider-specific docs** (only for SDK calls)

---

## 🤝 Collaboration with Existing Code

**Example workflow:**

```python
# Step 1: Import existing
from devorbit_cli.main import DevorbitCLI
from devorbit import Devorbit

# Step 2: Check what exists
cli = DevorbitCLI()
# What methods does it have?
# What attributes?
# What's the flow?

# Step 3: Enhance it
class EnhancedCLI(DevorbitCLI):
    def __init__(self):
        super().__init__()
        self.add_new_features()

    def add_streaming_ui(self):
        """New feature built on existing"""
        # Use existing provider selection
        provider = self.current_provider
        # Add new UI layer
        ...
```

---

## 🎓 Summary: Your Core Mission

**Build a pixel-perfect Claude Code CLI clone that:**
1. ✅ Works with MULTIPLE providers (not just Anthropic)
2. ✅ Enhances EXISTING Devorbit codebase
3. ✅ Does NOT duplicate existing code
4. ✅ Maintains backward compatibility
5. ✅ Follows the specification exactly
6. ✅ Is provider-agnostic in all features

**Remember:**
- The specification describes WHAT to build
- This document describes HOW to integrate
- Multi-provider support is your UNIQUE advantage
- Don't reinvent what exists, enhance it

---

## 🚦 Start Here

1. **First:** Read ALL existing code in `devorbit_cli/`
2. **Second:** List what already exists
3. **Third:** Map specification features to existing code
4. **Fourth:** Identify enhancement opportunities
5. **Fifth:** Begin implementation with Phase 1
6. **Always:** Test with all providers

Good luck! Build something amazing that works across ALL LLM providers! 🚀
