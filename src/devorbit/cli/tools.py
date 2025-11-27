"""Tool execution system for Devorbit CLI.

This module handles tool execution for the CLI, coordinating between
LLM tool requests and actual tool implementations.

ARCHITECTURE PRINCIPLE:
This module acts as a thin coordination layer, delegating actual tool
execution to the SDK's built-in tools. This eliminates code duplication
and ensures consistency across the platform.

DESIGN PATTERNS:
- Delegation: CLI delegates to SDK for actual tool execution
- Adapter: CLI adapts LLM parameter names to SDK parameter names
- Validation: All inputs validated before execution
- Hooks: Pre/post hooks triggered during tool execution (Phase 5)
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any

from devorbit.core.hooks import HookType, execute_hooks, get_registry
from devorbit.core.types import Tool
from devorbit.tools.bash import bash
from devorbit.tools.file import edit_file, get_all_file_tools, read_file, write_file
from devorbit.tools.search import get_all_search_tools, glob_files, grep_code

from .core.validation import InputValidator, validate_command, validate_path


if TYPE_CHECKING:
    from collections.abc import Callable

    from .session import CLISession


class ToolExecutor:
    """Executes tools requested by the LLM.

    This class bridges between LLM tool requests (in the form of ToolUseBlocks)
    and actual tool implementations in the Devorbit SDK.

    ZERO DUPLICATION PRINCIPLE:
    All tool execution is delegated to SDK implementations. This class only
    handles:
    1. Tool name -> SDK function mapping
    2. Input parameter transformation (CLI conventions -> SDK format)
    3. Output formatting for CLI display
    4. Working directory context injection
    """

    def __init__(self, session: "CLISession") -> None:
        """Initialize tool executor.

        Args:
            session: CLI session instance
        """
        self.session = session

        # Get or create bash session for persistent state
        self._bash_session_id = f"cli_{id(session)}"

        # Input validator with working directory context
        self._validator = InputValidator(base_dir=session.working_dir)

        # Map tool names to execution functions
        # All handlers delegate to SDK implementations
        self.tool_handlers: dict[str, Callable[[dict[str, Any]], str]] = {
            "bash": self._execute_bash,
            "read_file": self._execute_read,
            "write_file": self._execute_write,
            "edit_file": self._execute_edit,
            "grep": self._execute_grep,
            "glob": self._execute_glob,
        }

    def get_tool_definitions(self) -> list[Tool]:
        """Get all available tool definitions for the LLM.

        Imports tool definitions directly from SDK modules to avoid duplication.
        SDK tools are decorated with @beta_tool which auto-generates definitions.

        Returns:
            List of tool definitions in Claude SDK format
        """
        # ✅ Import tool definitions from SDK - zero duplication!
        tools: list[dict[str, Any]] = []

        # Get bash tool (only the main bash tool, not bash_output/kill_shell)
        bash_def: dict[str, Any] = bash.tool_definition  # type: ignore[attr-defined]
        tools.append(bash_def)

        # Get file tools (read, write, edit - skip multi_edit and ls for now)
        file_tools = get_all_file_tools()
        for tool in file_tools:
            if tool["name"] in ["read_file", "write_file", "edit_file"]:
                tools.append(tool)

        # Get search tools (grep, glob)
        search_tools = get_all_search_tools()
        # Map SDK tool names to CLI expected names
        for tool in search_tools:
            if tool["name"] == "grep_code":
                # Create a copy and rename to 'grep' for CLI compatibility
                grep_tool = tool.copy()
                grep_tool["name"] = "grep"
                # Update description to CLI format
                grep_tool["description"] = (
                    "Search for patterns in files using regex. "
                    "Returns matching lines with line numbers."
                )
                # Map input_schema parameters (SDK uses different names)
                tools.append(grep_tool)
            elif tool["name"] == "glob_files":
                # Create a copy and rename to 'glob' for CLI compatibility
                glob_tool = tool.copy()
                glob_tool["name"] = "glob"
                glob_tool["description"] = (
                    "Find files matching a glob pattern. Returns list of matching file paths."
                )
                tools.append(glob_tool)

        return tools  # type: ignore[return-value]

    def execute_tool(self, tool_name: str, tool_input: dict[str, Any]) -> str:
        """Execute a tool and return the result.

        Triggers pre/post hooks if registered (Phase 5 integration).

        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool

        Returns:
            Tool execution result as a string

        Raises:
            ValueError: If tool is not found
        """
        handler = self.tool_handlers.get(tool_name)
        if not handler:
            raise ValueError(f"Unknown tool: {tool_name}")

        # Execute PRE_TOOL_CALL hooks (Phase 5)
        pre_results = self._execute_pre_hooks(tool_name, tool_input)

        # Check if any pre-hook stopped execution
        for result in pre_results:
            if result.get("stopped_chain") or not result.get("should_continue", True):
                return f"Tool execution stopped by hook: {result.get('hook', 'unknown')}"

        try:
            tool_result = handler(tool_input)

            # Execute POST_TOOL_CALL hooks (Phase 5)
            self._execute_post_hooks(tool_name, tool_input, tool_result)

            return tool_result
        except Exception as e:
            # Execute error hooks (Phase 5)
            self._execute_error_hooks(tool_name, tool_input, e)
            # Return error as string for LLM to see
            return f"Error executing {tool_name}: {e}"

    def _execute_pre_hooks(
        self, tool_name: str, tool_input: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Execute pre-tool-call hooks.

        Args:
            tool_name: Name of tool being executed
            tool_input: Tool parameters

        Returns:
            List of hook execution results
        """
        if not get_registry().is_enabled():
            return []

        results = execute_hooks(
            HookType.PRE_TOOL_CALL,
            context_data={
                "tool_name": tool_name,
                "tool_input": str(tool_input),
                **tool_input,
            },
            metadata={
                "working_dir": str(self.session.working_dir),
            },
        )

        # Print shell hook output so it's visible to the user
        self._display_hook_output(results)
        return results

    def _display_hook_output(self, results: list[dict[str, Any]]) -> None:
        """Display output from shell hooks.

        Args:
            results: List of hook execution results
        """
        for result in results:
            if result.get("skipped"):
                continue

            # Print stdout from shell hooks
            stdout = result.get("stdout", "").strip()
            if stdout:
                self.session.print_info(f"[hook:{result.get('hook', 'unknown')}] {stdout}")

            # Print stderr as warnings
            stderr = result.get("stderr", "").strip()
            if stderr:
                self.session.print_warning(f"[hook:{result.get('hook', 'unknown')}] {stderr}")

    def _execute_post_hooks(
        self, tool_name: str, tool_input: dict[str, Any], result: str
    ) -> list[dict[str, Any]]:
        """Execute post-tool-call hooks.

        Args:
            tool_name: Name of tool that was executed
            tool_input: Tool parameters
            result: Tool execution result

        Returns:
            List of hook execution results
        """
        if not get_registry().is_enabled():
            return []

        # Determine specific hook type based on tool
        hook_type = HookType.POST_TOOL_CALL

        # Map tool names to specific file hook types
        if tool_name == "write_file":
            hook_type = HookType.POST_FILE_WRITE
        elif tool_name == "read_file":
            hook_type = HookType.POST_FILE_READ
        elif tool_name == "edit_file":
            hook_type = HookType.POST_FILE_EDIT

        # Execute both specific and generic hooks
        results = execute_hooks(
            hook_type,
            context_data={
                "tool_name": tool_name,
                "result": result[:500],  # Truncate for env var size limits
                "file_path": tool_input.get("file_path", tool_input.get("path", "")),
                **{k: str(v)[:200] for k, v in tool_input.items()},
            },
            metadata={
                "working_dir": str(self.session.working_dir),
            },
        )

        # Also execute generic POST_TOOL_CALL if we used a specific type
        if hook_type != HookType.POST_TOOL_CALL:
            generic_results = execute_hooks(
                HookType.POST_TOOL_CALL,
                context_data={
                    "tool_name": tool_name,
                    "result": result[:500],
                    **{k: str(v)[:200] for k, v in tool_input.items()},
                },
            )
            results.extend(generic_results)

        # Display output from shell hooks
        self._display_hook_output(results)
        return results

    def _execute_error_hooks(
        self, tool_name: str, tool_input: dict[str, Any], error: Exception
    ) -> list[dict[str, Any]]:
        """Execute error hooks when tool execution fails.

        Args:
            tool_name: Name of tool that failed
            tool_input: Tool parameters
            error: The exception that occurred

        Returns:
            List of hook execution results
        """
        if not get_registry().is_enabled():
            return []

        return execute_hooks(
            HookType.TOOL_ERROR,
            context_data={
                "tool_name": tool_name,
                "error": str(error),
                "error_type": type(error).__name__,
            },
            metadata={
                "working_dir": str(self.session.working_dir),
            },
        )

    def _execute_bash(self, tool_input: dict[str, Any]) -> str:
        """Execute bash command using SDK's bash tool.

        Delegates to SDK's bash implementation which provides:
        - Persistent bash sessions with state retention
        - Environment variable tracking
        - Working directory persistence
        - Background process support
        - Output streaming

        Args:
            tool_input: Tool parameters (command, timeout, run_in_background)

        Returns:
            Command output formatted for CLI display
        """
        # Debug: print what we received
        if self.session.debug:
            self.session.print_info(f"DEBUG: tool_input = {tool_input}")

        # Validate command parameter
        if "command" not in tool_input:
            available_keys = list(tool_input.keys())
            return (
                f"Error: 'command' parameter not found. "
                f"Available keys: {available_keys}. "
                f"Please provide a 'command' parameter with the bash command to execute."
            )

        command = tool_input["command"]

        # Validate command (warnings for dangerous patterns)
        cmd_validation = validate_command(command)
        if not cmd_validation.valid:
            return f"Error: {cmd_validation.to_error_string()}"

        # Log warnings but don't block
        for warning in cmd_validation.warnings:
            self.session.print_warning(f"⚠️  {warning}")

        self.session.print_info(f"Executing: {command}")

        # Delegate to SDK bash tool
        result = bash(
            command=command,
            session_id=self._bash_session_id,
            cwd=str(self.session.working_dir),
            timeout=tool_input.get("timeout", 60.0),
            run_in_background=tool_input.get("run_in_background", False),
        )

        # Format result for CLI display
        return self._format_bash_result(result)

    def _execute_read(self, tool_input: dict[str, Any]) -> str:
        """Read file using SDK's read_file tool.

        Delegates to SDK's read_file which provides:
        - Line-numbered output (cat -n format)
        - Offset/limit support for large files
        - Safety checks and validation
        - Syntax highlighting support

        Args:
            tool_input: Tool parameters (file_path/path, offset, limit)

        Returns:
            File content with line numbers
        """
        # Accept both 'file_path' (SDK format) and 'path' (CLI format)
        path_str = tool_input.get("file_path") or tool_input.get("path")
        if not path_str:
            return "Error: Missing 'file_path' or 'path' parameter"

        # Validate path
        path_validation = validate_path(
            path_str,
            base_dir=self.session.working_dir,
        )
        if not path_validation.valid:
            return f"Error: {path_validation.to_error_string()}"

        # Resolve relative paths against working directory
        file_path = self._resolve_path(path_str)

        self.session.print_info(f"Reading: {file_path}")

        # Delegate to SDK read_file tool
        result = read_file(
            file_path=str(file_path),
            offset=tool_input.get("offset"),
            limit=tool_input.get("limit"),
        )

        # Format result for CLI display
        return self._format_tool_result(result)

    def _execute_write(self, tool_input: dict[str, Any]) -> str:
        """Write file using SDK's write_file tool.

        Delegates to SDK's write_file which provides:
        - Automatic directory creation
        - Overwrite confirmation (when enabled)
        - File size reporting
        - Safety checks

        Args:
            tool_input: Tool parameters (file_path/path, content)

        Returns:
            Success message with file details
        """
        # Accept both 'file_path' (SDK format) and 'path' (CLI format)
        path_str = tool_input.get("file_path") or tool_input.get("path")
        if not path_str:
            return "Error: Missing 'file_path' or 'path' parameter"
        content = tool_input.get("content", "")

        # Validate path
        path_validation = validate_path(
            path_str,
            base_dir=self.session.working_dir,
        )
        if not path_validation.valid:
            return f"Error: {path_validation.to_error_string()}"

        # Resolve relative paths against working directory
        file_path = self._resolve_path(path_str)

        self.session.print_info(f"Writing: {file_path}")

        # Delegate to SDK write_file tool
        result = write_file(
            file_path=str(file_path),
            content=content,
        )

        # Format result for CLI display
        return self._format_tool_result(result)

    def _execute_edit(self, tool_input: dict[str, Any]) -> str:
        """Edit file using SDK's edit_file tool.

        Delegates to SDK's edit_file which provides:
        - Exact string replacement
        - Multiple occurrence detection
        - Diff generation
        - Backup creation
        - Atomic operations

        Args:
            tool_input: Tool parameters (file_path/path, old_string/old_text, new_string/new_text)

        Returns:
            Success message with edit details and diff
        """
        # Accept both 'file_path' (SDK format) and 'path' (CLI format)
        path_str = tool_input.get("file_path") or tool_input.get("path")
        if not path_str:
            return "Error: Missing 'file_path' or 'path' parameter"
        # Accept both SDK and CLI parameter names
        old_text = tool_input.get("old_string") or tool_input.get("old_text", "")
        new_text = tool_input.get("new_string") or tool_input.get("new_text", "")

        # Validate path
        path_validation = validate_path(
            path_str,
            base_dir=self.session.working_dir,
            must_exist=True,
        )
        if not path_validation.valid:
            return f"Error: {path_validation.to_error_string()}"

        # Resolve relative paths against working directory
        file_path = self._resolve_path(path_str)

        self.session.print_info(f"Editing: {file_path}")

        # Delegate to SDK edit_file tool
        # NOTE: SDK uses 'old_string'/'new_string', LLM provides 'old_text'/'new_text'
        result = edit_file(
            file_path=str(file_path),
            old_string=old_text,  # Map old_text -> old_string
            new_string=new_text,  # Map new_text -> new_string
        )

        # Format result for CLI display
        return self._format_tool_result(result)

    def _execute_grep(self, tool_input: dict[str, Any]) -> str:
        """Search code using SDK's grep_code tool.

        Delegates to SDK's grep_code which provides:
        - Powerful regex search
        - File type filtering
        - Context lines (before/after)
        - Case-insensitive search
        - Multiline mode
        - Output format options

        Args:
            tool_input: Tool parameters (pattern, path, file_pattern, etc.)

        Returns:
            Search results with matches
        """
        pattern = tool_input["pattern"]
        path_str = tool_input.get("path", ".")

        # Validate path
        path_validation = validate_path(
            path_str,
            base_dir=self.session.working_dir,
        )
        if not path_validation.valid:
            return f"Error: {path_validation.to_error_string()}"

        # Resolve relative paths against working directory
        search_path = self._resolve_path(path_str)

        self.session.print_info(f"Searching for '{pattern}' in {search_path}")

        # Map CLI parameters to SDK parameters
        # CLI uses 'file_pattern', SDK uses 'glob'
        glob_pattern = tool_input.get("file_pattern")

        # Delegate to SDK grep_code tool
        result = grep_code(
            pattern=pattern,
            path=str(search_path),
            glob=glob_pattern,
            output_mode="content",  # CLI wants full content, not just file names
        )

        # Format result for CLI display
        return self._format_tool_result(result)

    def _execute_glob(self, tool_input: dict[str, Any]) -> str:
        """Find files using SDK's glob_files tool.

        Delegates to SDK's glob_files which provides:
        - Fast file pattern matching
        - Recursive patterns (e.g., "**/*.py")
        - Sorted by modification time
        - File count reporting

        Args:
            tool_input: Tool parameters (pattern, path)

        Returns:
            List of matching files with count
        """
        pattern = tool_input["pattern"]
        path_str = tool_input.get("path", ".")

        # Validate path
        path_validation = validate_path(
            path_str,
            base_dir=self.session.working_dir,
        )
        if not path_validation.valid:
            return f"Error: {path_validation.to_error_string()}"

        # Resolve relative paths against working directory
        search_path = self._resolve_path(path_str)

        self.session.print_info(f"Finding files matching: {pattern}")

        # Delegate to SDK glob_files tool
        result = glob_files(
            pattern=pattern,
            path=str(search_path),
        )

        # Format result for CLI display
        return self._format_tool_result(result)

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _resolve_path(self, path_str: str) -> Path:
        """Resolve a path string relative to working directory.

        Args:
            path_str: Path string (absolute or relative)

        Returns:
            Resolved absolute path
        """
        path = Path(path_str)
        if not path.is_absolute():
            path = self.session.working_dir / path
        return path.resolve()

    def _format_tool_result(self, result: dict[str, Any]) -> str:
        """Format SDK tool result for CLI display.

        SDK tools return structured dicts with either:
        - Success: {content, file_path, line_count, etc.}
        - Error: {error, file_path, etc.}

        Args:
            result: Tool result dict from SDK

        Returns:
            Formatted string for CLI display
        """
        # Check for errors
        if "error" in result:
            return f"Error: {result['error']}"

        # For read_file: return content
        if "content" in result:
            content = result["content"]
            return str(content) if content is not None else ""

        # For write_file: return success message
        if "message" in result:
            message = result["message"]
            return str(message) if message is not None else "Success"

        # For edit_file: return diff and message
        if "diff" in result:
            message = result.get("message", "File edited successfully")
            diff = result["diff"]
            return f"{message}\n\nDiff:\n{diff}"

        # For grep_code: format search results (check before glob since both have "matches")
        if "total_matches" in result:
            matches = result.get("matches", [])
            total = result.get("total_matches", 0)
            if total == 0:
                return "No matches found"
            # Format grep results
            output_lines = [f"Found {total} match(es):"]
            for match in matches:
                if isinstance(match, dict):
                    file_path = match.get("file", "")
                    content = match.get("content", "")
                    try:
                        rel_path = Path(file_path).relative_to(self.session.working_dir)
                        output_lines.append(f"{rel_path}: {content}")
                    except (ValueError, TypeError):
                        output_lines.append(f"{file_path}: {content}")
                else:
                    output_lines.append(str(match))
            return "\n".join(output_lines)

        # For glob_files: format matches
        if "matches" in result and "count" in result:
            matches = result["matches"]
            count = result["count"]
            if count == 0:
                return "No files found matching pattern"
            # Convert absolute paths to relative for CLI display
            rel_matches = []
            for match in matches:
                try:
                    rel_path = Path(match).relative_to(self.session.working_dir)
                    rel_matches.append(str(rel_path))
                except (ValueError, TypeError):
                    # If path is outside working_dir, show absolute
                    rel_matches.append(str(match))
            return f"Found {count} file(s):\n" + "\n".join(rel_matches)

        # Fallback: convert dict to string
        return str(result)

    def _format_bash_result(self, result: dict[str, Any]) -> str:
        """Format bash execution result for CLI display.

        Args:
            result: Bash execution result from SDK

        Returns:
            Formatted output for CLI
        """
        # Check for errors
        if "error" in result:
            return f"Error: {result['error']}"

        # Check for background task
        if result.get("is_background"):
            task_id = result.get("task_id", "unknown")
            return f"Background task started: {task_id}\n{result.get('output', '')}"

        # Regular output
        output = result.get("output", "")
        exit_code = result.get("exit_code", 0)

        if exit_code != 0:
            output += f"\nExit code: {exit_code}"

        return output or "(no output)"


__all__ = ["ToolExecutor"]
