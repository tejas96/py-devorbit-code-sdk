"""Input validation and sanitization for CLI tools.

This module provides comprehensive input validation:
- Path validation (prevent traversal attacks)
- Command validation (detect dangerous patterns)
- Input sanitization (encoding, length limits)
- Type validation (ensure correct parameter types)

Security is a top priority - all validation is strict by default.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ============================================================================
# Constants
# ============================================================================

# Maximum input lengths
MAX_COMMAND_LENGTH = 10_000
MAX_FILE_CONTENT_LENGTH = 10_000_000  # 10MB
MAX_PATH_LENGTH = 4096
MAX_PATTERN_LENGTH = 1000

# Dangerous path patterns
PATH_TRAVERSAL_PATTERNS = [
    r"\.\./",  # ../
    r"/\.\.",  # /..
    r"^\.\.$",  # just ..
]

# Dangerous command patterns (for warnings, not blocking)
DANGEROUS_COMMAND_PATTERNS = [
    r"\brm\s+-rf\s+/",  # rm -rf /
    r"\brm\s+-rf\s+~",  # rm -rf ~
    r">\s*/dev/sd",  # > /dev/sd*
    r"mkfs\.",  # mkfs.*
    r"dd\s+if=.*of=/dev",  # dd to device
    r":\(\)\s*\{.*\}",  # fork bomb
    r"chmod\s+-R\s+777\s+/",  # chmod -R 777 /
    r"chown\s+-R.*\s+/",  # chown -R ... /
]


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class ValidationResult:
    """Result of input validation."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    sanitized: dict[str, Any] = field(default_factory=dict)

    def add_error(self, message: str) -> None:
        """Add an error message."""
        self.errors.append(message)
        self.valid = False

    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)

    def to_error_string(self) -> str:
        """Convert errors to a single string."""
        if not self.errors:
            return ""
        return "; ".join(self.errors)


# ============================================================================
# Validation Functions
# ============================================================================


def validate_path(
    path_str: str,
    *,
    base_dir: Path | None = None,
    must_exist: bool = False,
    must_be_file: bool = False,
    must_be_dir: bool = False,
    allow_absolute: bool = True,
) -> ValidationResult:
    """Validate a file path for safety and correctness.

    Args:
        path_str: Path string to validate
        base_dir: Base directory for relative paths (for traversal check)
        must_exist: If True, path must exist
        must_be_file: If True, path must be a file
        must_be_dir: If True, path must be a directory
        allow_absolute: If True, allow absolute paths

    Returns:
        ValidationResult with validation status
    """
    result = ValidationResult(valid=True)

    # Check length
    if len(path_str) > MAX_PATH_LENGTH:
        result.add_error(f"Path too long ({len(path_str)} > {MAX_PATH_LENGTH})")
        return result

    # Check for path traversal patterns
    for pattern in PATH_TRAVERSAL_PATTERNS:
        if re.search(pattern, path_str):
            result.add_error(f"Path traversal detected: {path_str}")
            return result

    # Parse path
    try:
        path = Path(path_str)
    except (ValueError, OSError) as e:
        result.add_error(f"Invalid path: {e}")
        return result

    # Check absolute path
    if path.is_absolute() and not allow_absolute:
        result.add_error("Absolute paths not allowed")
        return result

    # Resolve and check traversal
    if base_dir:
        try:
            resolved = (base_dir / path).resolve()
            resolved.relative_to(base_dir.resolve())
        except ValueError:
            result.add_error(f"Path escapes base directory: {path_str}")
            return result

    # Check existence
    resolved_path = path.resolve() if path.is_absolute() else path
    if base_dir:
        resolved_path = (base_dir / path).resolve()

    if must_exist and not resolved_path.exists():
        result.add_error(f"Path does not exist: {path_str}")
        return result

    if must_be_file and resolved_path.exists() and not resolved_path.is_file():
        result.add_error(f"Path is not a file: {path_str}")
        return result

    if must_be_dir and resolved_path.exists() and not resolved_path.is_dir():
        result.add_error(f"Path is not a directory: {path_str}")
        return result

    # Store sanitized path
    result.sanitized["path"] = str(resolved_path)

    return result


def validate_command(command: str) -> ValidationResult:
    """Validate a bash command for safety.

    Note: This does NOT block dangerous commands, only warns about them.
    The permission system handles actual approval.

    Args:
        command: Command string to validate

    Returns:
        ValidationResult with warnings for dangerous patterns
    """
    result = ValidationResult(valid=True)

    # Check length
    if len(command) > MAX_COMMAND_LENGTH:
        result.add_error(f"Command too long ({len(command)} > {MAX_COMMAND_LENGTH})")
        return result

    # Check for dangerous patterns (warnings only)
    for pattern in DANGEROUS_COMMAND_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            result.add_warning("Potentially dangerous command pattern detected")
            break

    result.sanitized["command"] = command
    return result


def validate_content(
    content: str,
    *,
    max_length: int = MAX_FILE_CONTENT_LENGTH,
) -> ValidationResult:
    """Validate file content.

    Args:
        content: Content string to validate
        max_length: Maximum allowed length

    Returns:
        ValidationResult with validation status
    """
    result = ValidationResult(valid=True)

    if len(content) > max_length:
        result.add_error(f"Content too long ({len(content)} > {max_length})")
        return result

    result.sanitized["content"] = content
    return result


def validate_pattern(
    pattern: str,
    *,
    pattern_type: str = "regex",
) -> ValidationResult:
    """Validate a search pattern.

    Args:
        pattern: Pattern string to validate
        pattern_type: Type of pattern ("regex" or "glob")

    Returns:
        ValidationResult with validation status
    """
    result = ValidationResult(valid=True)

    # Check length
    if len(pattern) > MAX_PATTERN_LENGTH:
        result.add_error(f"Pattern too long ({len(pattern)} > {MAX_PATTERN_LENGTH})")
        return result

    # Validate regex if applicable
    if pattern_type == "regex":
        try:
            re.compile(pattern)
        except re.error as e:
            result.add_error(f"Invalid regex pattern: {e}")
            return result

    result.sanitized["pattern"] = pattern
    return result


# ============================================================================
# High-Level Validation
# ============================================================================


class InputValidator:
    """High-level input validator for tool inputs.

    Provides a fluent interface for validating tool inputs:

    Example:
        ```python
        validator = InputValidator(base_dir=Path.cwd())

        result = validator.validate(tool_input, {
            "path": {"type": "path", "must_exist": True},
            "content": {"type": "content"},
            "pattern": {"type": "pattern", "pattern_type": "regex"},
        })

        if not result.valid:
            return f"Error: {result.to_error_string()}"
        ```
    """

    def __init__(self, base_dir: Path | None = None) -> None:
        """Initialize validator.

        Args:
            base_dir: Base directory for path validation
        """
        self.base_dir = base_dir

    def validate(
        self,
        tool_input: dict[str, Any],
        schema: dict[str, dict[str, Any]],
    ) -> ValidationResult:
        """Validate tool input against a schema.

        Args:
            tool_input: Input dictionary to validate
            schema: Validation schema

        Returns:
            Combined ValidationResult
        """
        result = ValidationResult(valid=True)

        for param_name, param_schema in schema.items():
            param_type = param_schema.get("type", "string")
            required = param_schema.get("required", False)

            # Check required
            if required and param_name not in tool_input:
                result.add_error(f"Missing required parameter: {param_name}")
                continue

            # Skip if not present and not required
            if param_name not in tool_input:
                continue

            value = tool_input[param_name]

            # Type-specific validation
            if param_type == "path":
                path_result = validate_path(
                    str(value),
                    base_dir=self.base_dir,
                    must_exist=param_schema.get("must_exist", False),
                    must_be_file=param_schema.get("must_be_file", False),
                    must_be_dir=param_schema.get("must_be_dir", False),
                    allow_absolute=param_schema.get("allow_absolute", True),
                )
                if not path_result.valid:
                    result.errors.extend(path_result.errors)
                    result.valid = False
                result.warnings.extend(path_result.warnings)
                result.sanitized[param_name] = path_result.sanitized.get("path", value)

            elif param_type == "command":
                cmd_result = validate_command(str(value))
                if not cmd_result.valid:
                    result.errors.extend(cmd_result.errors)
                    result.valid = False
                result.warnings.extend(cmd_result.warnings)
                result.sanitized[param_name] = cmd_result.sanitized.get("command", value)

            elif param_type == "content":
                content_result = validate_content(
                    str(value),
                    max_length=param_schema.get("max_length", MAX_FILE_CONTENT_LENGTH),
                )
                if not content_result.valid:
                    result.errors.extend(content_result.errors)
                    result.valid = False
                result.sanitized[param_name] = content_result.sanitized.get("content", value)

            elif param_type == "pattern":
                pattern_result = validate_pattern(
                    str(value),
                    pattern_type=param_schema.get("pattern_type", "regex"),
                )
                if not pattern_result.valid:
                    result.errors.extend(pattern_result.errors)
                    result.valid = False
                result.sanitized[param_name] = pattern_result.sanitized.get("pattern", value)

            else:
                # Default: just copy the value
                result.sanitized[param_name] = value

        return result


# ============================================================================
# Convenience Functions
# ============================================================================


def sanitize_path(path_str: str, base_dir: Path | None = None) -> str | None:
    """Sanitize a path string.

    Args:
        path_str: Path to sanitize
        base_dir: Base directory for resolution

    Returns:
        Sanitized path string, or None if invalid
    """
    result = validate_path(path_str, base_dir=base_dir)
    if not result.valid:
        return None
    sanitized = result.sanitized.get("path", path_str)
    return str(sanitized) if sanitized is not None else path_str


def validate_input(
    tool_input: dict[str, Any],
    schema: dict[str, dict[str, Any]],
    base_dir: Path | None = None,
) -> ValidationResult:
    """Validate tool input (convenience function).

    Args:
        tool_input: Input to validate
        schema: Validation schema
        base_dir: Base directory for paths

    Returns:
        ValidationResult
    """
    validator = InputValidator(base_dir=base_dir)
    return validator.validate(tool_input, schema)
