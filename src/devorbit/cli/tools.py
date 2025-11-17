"""Tool execution system for Devorbit CLI.

This module handles tool execution for the CLI, coordinating between
LLM tool requests and actual tool implementations.
"""

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any

from devorbit._bash_tools import bash_execute
from devorbit._file_tools import edit_file, read_file, write_file
from devorbit._search_tools import glob_files, grep_search
from devorbit._types import Tool


if TYPE_CHECKING:
    from .session import CLISession


class ToolExecutor:
    """Executes tools requested by the LLM.

    This class bridges between LLM tool requests (in the form of ToolUseBlocks)
    and actual tool implementations in the Devorbit SDK.
    """

    def __init__(self, session: "CLISession") -> None:
        """Initialize tool executor.

        Args:
            session: CLI session instance
        """
        self.session = session

        # Map tool names to execution functions
        self.tool_handlers = {
            "bash": self._execute_bash,
            "read_file": self._execute_read,
            "write_file": self._execute_write,
            "edit_file": self._execute_edit,
            "grep": self._execute_grep,
            "glob": self._execute_glob,
        }

    def get_tool_definitions(self) -> list[Tool]:
        """Get all available tool definitions for the LLM.

        Returns:
            List of tool definitions in Claude SDK format
        """
        return [
            # Bash tool - execute shell commands
            {
                "name": "bash",
                "description": "Execute bash commands. Returns stdout and stderr. Use for system operations, running scripts, and checking system information.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The bash command to execute",
                        },
                        "timeout": {
                            "type": "number",
                            "description": "Timeout in seconds (default: 60)",
                        },
                    },
                    "required": ["command"],
                },
            },
            # Read file tool
            {
                "name": "read_file",
                "description": "Read the contents of a file. Returns file content as text.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the file to read (absolute or relative to working directory)",
                        },
                    },
                    "required": ["path"],
                },
            },
            # Write file tool
            {
                "name": "write_file",
                "description": "Write content to a file. Creates the file if it doesn't exist, overwrites if it does.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the file to write",
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write to the file",
                        },
                    },
                    "required": ["path", "content"],
                },
            },
            # Edit file tool
            {
                "name": "edit_file",
                "description": "Edit a file by replacing old text with new text. Performs exact string replacement.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the file to edit",
                        },
                        "old_text": {
                            "type": "string",
                            "description": "Exact text to replace (must match exactly)",
                        },
                        "new_text": {
                            "type": "string",
                            "description": "New text to insert",
                        },
                    },
                    "required": ["path", "old_text", "new_text"],
                },
            },
            # Grep tool
            {
                "name": "grep",
                "description": "Search for patterns in files using regex. Returns matching lines with line numbers.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "Regex pattern to search for",
                        },
                        "path": {
                            "type": "string",
                            "description": "File or directory to search in (default: current directory)",
                        },
                        "file_pattern": {
                            "type": "string",
                            "description": "File pattern to filter (e.g., '*.py', '*.js')",
                        },
                    },
                    "required": ["pattern"],
                },
            },
            # Glob tool
            {
                "name": "glob",
                "description": "Find files matching a glob pattern. Returns list of matching file paths.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "Glob pattern (e.g., '**/*.py', 'src/**/*.ts')",
                        },
                        "path": {
                            "type": "string",
                            "description": "Base directory to search from (default: current directory)",
                        },
                    },
                    "required": ["pattern"],
                },
            },
        ]

    def execute_tool(self, tool_name: str, tool_input: dict[str, Any]) -> str:
        """Execute a tool and return the result.

        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool

        Returns:
            Tool execution result as a string

        Raises:
            ValueError: If tool is not found
            Exception: If tool execution fails
        """
        handler = self.tool_handlers.get(tool_name)
        if not handler:
            raise ValueError(f"Unknown tool: {tool_name}")

        try:
            return handler(tool_input)
        except Exception as e:
            return f"Error executing {tool_name}: {e}"

    def _execute_bash(self, tool_input: dict[str, Any]) -> str:
        """Execute bash command.

        Args:
            tool_input: Tool parameters

        Returns:
            Command output
        """
        command = tool_input["command"]
        timeout = tool_input.get("timeout", 60)

        self.session.print_info(f"Executing: {command}")

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.session.working_dir),
            )

            output = result.stdout if result.stdout else ""
            if result.stderr:
                output += f"\nstderr: {result.stderr}"
            if result.returncode != 0:
                output += f"\nExit code: {result.returncode}"

            return output or "(no output)"

        except subprocess.TimeoutExpired:
            return f"Command timed out after {timeout} seconds"
        except Exception as e:
            return f"Error: {e}"

    def _execute_read(self, tool_input: dict[str, Any]) -> str:
        """Read file content.

        Args:
            tool_input: Tool parameters

        Returns:
            File content
        """
        path_str = tool_input["path"]
        path = Path(self.session.working_dir) / path_str

        self.session.print_info(f"Reading: {path}")

        try:
            if not path.exists():
                return f"Error: File not found: {path}"

            if not path.is_file():
                return f"Error: Not a file: {path}"

            content = path.read_text()
            return content if content else "(empty file)"

        except Exception as e:
            return f"Error reading file: {e}"

    def _execute_write(self, tool_input: dict[str, Any]) -> str:
        """Write content to file.

        Args:
            tool_input: Tool parameters

        Returns:
            Success message
        """
        path_str = tool_input["path"]
        content = tool_input["content"]
        path = Path(self.session.working_dir) / path_str

        self.session.print_info(f"Writing: {path}")

        try:
            # Create parent directories if needed
            path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            path.write_text(content)

            return f"Successfully wrote {len(content)} characters to {path}"

        except Exception as e:
            return f"Error writing file: {e}"

    def _execute_edit(self, tool_input: dict[str, Any]) -> str:
        """Edit file by replacing text.

        Args:
            tool_input: Tool parameters

        Returns:
            Success message
        """
        path_str = tool_input["path"]
        old_text = tool_input["old_text"]
        new_text = tool_input["new_text"]
        path = Path(self.session.working_dir) / path_str

        self.session.print_info(f"Editing: {path}")

        try:
            if not path.exists():
                return f"Error: File not found: {path}"

            content = path.read_text()

            if old_text not in content:
                return f"Error: Text to replace not found in file"

            # Count occurrences
            count = content.count(old_text)
            if count > 1:
                return f"Error: Found {count} occurrences of text. Please be more specific."

            # Replace
            new_content = content.replace(old_text, new_text)
            path.write_text(new_content)

            return f"Successfully edited {path} (replaced {len(old_text)} characters with {len(new_text)})"

        except Exception as e:
            return f"Error editing file: {e}"

    def _execute_grep(self, tool_input: dict[str, Any]) -> str:
        """Search for pattern in files.

        Args:
            tool_input: Tool parameters

        Returns:
            Search results
        """
        pattern = tool_input["pattern"]
        path = tool_input.get("path", ".")
        file_pattern = tool_input.get("file_pattern", "*")

        search_path = Path(self.session.working_dir) / path

        self.session.print_info(f"Searching for '{pattern}' in {search_path}")

        try:
            # Use system grep for performance
            result = subprocess.run(
                ["grep", "-rn", "-E", pattern, "--include", file_pattern, str(search_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                return result.stdout if result.stdout else "No matches found"
            elif result.returncode == 1:
                return "No matches found"
            else:
                return f"Search failed: {result.stderr}"

        except Exception as e:
            return f"Error searching: {e}"

    def _execute_glob(self, tool_input: dict[str, Any]) -> str:
        """Find files matching glob pattern.

        Args:
            tool_input: Tool parameters

        Returns:
            List of matching files
        """
        pattern = tool_input["pattern"]
        path_str = tool_input.get("path", ".")

        search_path = Path(self.session.working_dir) / path_str

        self.session.print_info(f"Finding files matching: {pattern}")

        try:
            matches = list(search_path.glob(pattern))

            if not matches:
                return "No files found matching pattern"

            # Return relative paths
            result = []
            for match in sorted(matches):
                rel_path = match.relative_to(self.session.working_dir)
                result.append(str(rel_path))

            return "\n".join(result)

        except Exception as e:
            return f"Error finding files: {e}"


__all__ = ["ToolExecutor"]
