"""Tool execution system for Devorbit CLI.

This module handles tool execution for the CLI using the ToolRegistry.

ARCHITECTURE (Phase 7 - Clean):
- Uses ToolRegistry for auto-discovery of tools
- Generic execution via registry.execute()
- No manual tool handlers - tools register themselves
- Hooks integration for pre/post execution
- Claude Code-style execution display

DESIGN PATTERNS:
- Registry Pattern: Central tool registry for auto-discovery
- Facade Pattern: Simple interface to complex tool system
- Observer Pattern: Hooks for pre/post tool execution
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any

# Import tools module to trigger auto-registration
import devorbit.tools  # noqa: F401
from devorbit.core.hooks import HookType, execute_hooks
from devorbit.core.tool_registry import get_tool_registry
from devorbit.core.types import Tool

from .core.validation import InputValidator, validate_command
from .ui.claude_style import ToolExecutionDisplay

if TYPE_CHECKING:
    from .session import CLISession


class ToolExecutor:
    """Executes tools requested by the LLM using the ToolRegistry.

    This class provides a clean interface for tool execution:
    - get_tool_definitions(): Returns all tools for LLM
    - execute_tool(): Executes any registered tool by name

    Features:
    - Auto-discovery from registry - no manual handlers needed!
    - Claude Code-style execution display with status dots
    - Pre/post hooks integration
    """

    def __init__(self, session: "CLISession") -> None:
        """Initialize tool executor.

        Args:
            session: CLI session instance
        """
        self.session = session
        self._validator = InputValidator(base_dir=session.working_dir)
        self._registry = get_tool_registry()

        # Claude-style execution display
        self._tool_display = ToolExecutionDisplay(
            console=session.console if hasattr(session, "console") else None
        )

        # Use Claude-style display
        self.use_claude_style = True

    def get_tool_definitions(self) -> list[Tool]:
        """Get all available tool definitions for the LLM.

        Returns definitions from the ToolRegistry - tools auto-register themselves.

        Returns:
            List of tool definitions in Claude SDK format
        """
        return self._registry.get_all_definitions()

    def execute_tool(self, tool_name: str, tool_input: dict[str, Any]) -> str:
        """Execute a tool and return the result.

        Uses the ToolRegistry for generic execution.
        Triggers pre/post hooks if registered.
        Shows Claude Code-style execution display.

        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool

        Returns:
            Tool execution result as a string

        Raises:
            ValueError: If tool is not found
        """
        # Check if tool exists
        tool = self._registry.get(tool_name)
        if not tool:
            raise ValueError(f"Unknown tool: {tool_name}")

        # Execute PRE_TOOL_CALL hooks
        pre_results = self._execute_pre_hooks(tool_name, tool_input)

        # Check if any pre-hook stopped execution
        for result in pre_results:
            if result.get("stopped_chain") or not result.get("should_continue", True):
                return f"Tool execution stopped by hook: {result.get('hook', 'unknown')}"

        # Get command string for display
        command = self._get_display_command(tool_name, tool_input)

        self._tool_display._tool_name = tool_name
        self._tool_display._command = command

        try:
            # Prepare parameters (adapt CLI conventions to SDK)
            params = self._prepare_params(tool_name, tool_input)

            # Legacy log (only if not using Claude style)
            if not self.use_claude_style:
                self._log_execution(tool_name, params)

            # Execute via registry
            result = self._registry.execute(tool_name, params)

            # Format result for CLI display
            output = self._format_result(tool_name, result)

            # Complete Claude-style display
            if self.use_claude_style:
                self._tool_display.show_tool_complete(
                    tool_name=tool_name,
                    command=command,
                    success=True,
                    output=output,
                )

            # Execute POST_TOOL_CALL hooks
            self._execute_post_hooks(tool_name, tool_input, output)

            return output

        except Exception as e:
            error_msg = f"Error executing {tool_name}: {e!s}"

            # Complete Claude-style display with error
            if self.use_claude_style:
                self._tool_display.show_tool_complete(
                    tool_name=tool_name,
                    command=command,
                    success=False,
                    error=error_msg,
                )

            # Execute error hooks
            self._execute_error_hooks(tool_name, tool_input, e)

            if self.session.debug:
                import traceback

                error_msg += f"\n{traceback.format_exc()}"

            return error_msg

    def _get_display_command(self, tool_name: str, tool_input: dict[str, Any]) -> str:
        """Get command string for display.

        Args:
            tool_name: Tool name
            tool_input: Tool input parameters

        Returns:
            Command string for display
        """
        if tool_name.lower() == "bash":
            return str(tool_input.get("command", str(tool_input)))
        if tool_name in ("read_file", "write_file", "edit_file"):
            path_val = tool_input.get("file_path", tool_input.get("path", str(tool_input)))
            return str(path_val)
        if tool_name in ("grep", "glob"):
            return str(tool_input.get("pattern", str(tool_input)))
        # Return first value or tool name
        if tool_input:
            return str(next(iter(tool_input.values())))[:60]
        return tool_name

    def _prepare_params(self, tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
        """Prepare parameters for tool execution.

        Handles:
        - Working directory injection
        - Path resolution
        - Parameter validation

        Args:
            tool_name: Tool name
            tool_input: Raw input from LLM

        Returns:
            Prepared parameters for SDK tool
        """
        params = tool_input.copy()

        # Handle bash tool
        if tool_name == "bash":
            # Validate command
            if "command" in params:
                cmd_validation = validate_command(params["command"])
                if not cmd_validation.valid:
                    raise ValueError(cmd_validation.to_error_string())
                for warning in cmd_validation.warnings:
                    self.session.print_warning(f"⚠️  {warning}")

            # Set working directory
            if "cwd" not in params:
                params["cwd"] = str(self.session.working_dir)

            # Set default timeout
            if "timeout" not in params:
                params["timeout"] = 60.0

        # Handle file tools - resolve paths
        elif tool_name in ("read_file", "write_file", "edit_file"):
            # Handle path parameter (LLM might use 'path' or 'file_path')
            file_path = params.get("file_path") or params.get("path")
            if file_path:
                resolved = self._resolve_path(file_path)
                params["file_path"] = resolved
                # Remove 'path' if it was used
                params.pop("path", None)

            # Handle content parameter for write_file
            if tool_name == "write_file":
                if "contents" in params and "content" not in params:
                    params["content"] = params.pop("contents")

        # Handle search tools
        elif tool_name in ("grep", "glob"):
            # Set default path to working directory
            if "path" not in params:
                params["path"] = str(self.session.working_dir)
            else:
                params["path"] = self._resolve_path(params["path"])

        return params

    def _resolve_path(self, path: str) -> str:
        """Resolve a path relative to working directory.

        Args:
            path: Path to resolve

        Returns:
            Absolute path string
        """
        p = Path(path)
        if not p.is_absolute():
            p = self.session.working_dir / p
        return str(p.resolve())

    def _log_execution(self, tool_name: str, params: dict[str, Any]) -> None:
        """Log tool execution for user visibility.

        Args:
            tool_name: Tool being executed
            params: Parameters being used
        """
        if tool_name == "bash":
            self.session.print_info(f"Executing: {params.get('command', '')}")
        elif tool_name == "read_file":
            self.session.print_info(f"Reading: {params.get('file_path', '')}")
        elif tool_name == "write_file":
            self.session.print_info(f"Writing: {params.get('file_path', '')}")
        elif tool_name == "edit_file":
            self.session.print_info(f"Editing: {params.get('file_path', '')}")
        elif tool_name == "grep":
            self.session.print_info(f"Searching: {params.get('pattern', '')}")
        elif tool_name == "glob":
            self.session.print_info(f"Finding: {params.get('pattern', '')}")

    def _format_result(self, tool_name: str, result: Any) -> str:
        """Format tool result for CLI display.

        Args:
            tool_name: Tool that was executed
            result: Raw result from tool

        Returns:
            Formatted string for display
        """
        # Handle dict results (common for SDK tools)
        if isinstance(result, dict):
            if "error" in result:
                return f"Error: {result['error']}"
            if "output" in result:
                return str(result["output"])
            if "content" in result:
                return self._format_file_content(result)
            if "matches" in result:
                return self._format_search_results(result)
            # Default: return as string
            return str(result)

        # Handle string results
        if isinstance(result, str):
            return result

        # Handle list results (e.g., glob)
        if isinstance(result, list):
            return "\n".join(str(item) for item in result)

        return str(result)

    def _format_file_content(self, result: dict[str, Any]) -> str:
        """Format file content with line numbers.

        Args:
            result: Result dict with content

        Returns:
            Formatted content string
        """
        content = result.get("content", "")
        if not content:
            return "(empty file)"

        lines = content.split("\n")
        start_line = result.get("start_line", 1)

        formatted_lines = []
        for i, line in enumerate(lines, start=start_line):
            formatted_lines.append(f"{i:6}\t{line}")

        return "\n".join(formatted_lines)

    def _format_search_results(self, result: dict[str, Any]) -> str:
        """Format search results.

        Args:
            result: Result dict with matches

        Returns:
            Formatted results string
        """
        matches = result.get("matches", [])
        if not matches:
            return "No matches found"

        output_lines = []
        for match in matches:
            if isinstance(match, dict):
                file_path = match.get("file", "")
                line_num = match.get("line", 0)
                content = match.get("content", "")
                output_lines.append(f"{file_path}:{line_num}: {content}")
            else:
                output_lines.append(str(match))

        return "\n".join(output_lines)

    # ========================================================================
    # Hooks Integration
    # ========================================================================

    def _execute_pre_hooks(
        self, tool_name: str, tool_input: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Execute pre-tool-call hooks.

        Args:
            tool_name: Tool being called
            tool_input: Tool input parameters

        Returns:
            List of hook results
        """
        results: list[dict[str, Any]] = []

        try:
            hook_results = execute_hooks(
                HookType.PRE_TOOL_CALL,
                context_data={
                    "tool_name": tool_name,
                    "tool_input": tool_input,
                },
                metadata={
                    "working_dir": str(self.session.working_dir),
                },
            )

            for hr in hook_results:
                results.append(hr)
                self._display_hook_output(hr)

        except Exception as e:
            if self.session.debug:
                self.session.print_warning(f"Pre-hook error: {e}")

        return results

    def _execute_post_hooks(
        self, tool_name: str, tool_input: dict[str, Any], result: str
    ) -> list[dict[str, Any]]:
        """Execute post-tool-call hooks.

        Args:
            tool_name: Tool that was called
            tool_input: Tool input parameters
            result: Tool execution result

        Returns:
            List of hook results
        """
        results: list[dict[str, Any]] = []

        try:
            hook_results = execute_hooks(
                HookType.POST_TOOL_CALL,
                context_data={
                    "tool_name": tool_name,
                    "tool_input": tool_input,
                    "result": result[:1000],  # Truncate large results
                },
                metadata={
                    "working_dir": str(self.session.working_dir),
                },
            )

            for hr in hook_results:
                results.append(hr)
                self._display_hook_output(hr)

            # Special hooks for specific tools
            if tool_name == "write_file":
                file_path = tool_input.get("file_path") or tool_input.get("path", "")
                write_results = execute_hooks(
                    HookType.POST_FILE_WRITE,
                    context_data={"file_path": file_path},
                    metadata={"working_dir": str(self.session.working_dir)},
                )
                for wr in write_results:
                    results.append(wr)
                    self._display_hook_output(wr)

        except Exception as e:
            if self.session.debug:
                self.session.print_warning(f"Post-hook error: {e}")

        return results

    def _execute_error_hooks(
        self, tool_name: str, tool_input: dict[str, Any], error: Exception
    ) -> list[dict[str, Any]]:
        """Execute error hooks when tool fails.

        Args:
            tool_name: Tool that failed
            tool_input: Tool input parameters
            error: The exception that occurred

        Returns:
            List of hook results
        """
        results: list[dict[str, Any]] = []

        try:
            hook_results = execute_hooks(
                HookType.TOOL_ERROR,
                context_data={
                    "tool_name": tool_name,
                    "tool_input": tool_input,
                    "error": str(error),
                    "error_type": type(error).__name__,
                },
                metadata={
                    "working_dir": str(self.session.working_dir),
                },
            )

            for hr in hook_results:
                results.append(hr)
                self._display_hook_output(hr)

        except Exception as e:
            if self.session.debug:
                self.session.print_warning(f"Error-hook error: {e}")

        return results

    def _display_hook_output(self, hook_result: dict[str, Any]) -> None:
        """Display hook output to CLI console.

        Args:
            hook_result: Result from hook execution
        """
        stdout = hook_result.get("stdout", "")
        stderr = hook_result.get("stderr", "")

        if stdout and self.session.console:
            self.session.print_info(stdout.strip())

        if stderr and self.session.console:
            self.session.print_warning(stderr.strip())
