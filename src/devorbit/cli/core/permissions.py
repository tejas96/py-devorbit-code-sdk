"""Permission system for Devorbit CLI.

This module provides:
- PermissionLevel: Risk levels for operations
- PermissionPolicy: Configurable policies (allow, deny, ask)
- PermissionRule: Path and pattern-based rules
- PermissionManager: Central permission management
- PermissionStore: Persistence for permission decisions

Usage:
    from devorbit.cli.core.permissions import PermissionManager, PermissionLevel

    manager = PermissionManager()

    # Check permission
    if manager.check_permission("write_file", {"file_path": "test.py"}):
        execute_tool()

    # Add rule
    manager.add_rule("*.py", PermissionLevel.ASK, tool="write_file")
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar


if TYPE_CHECKING:
    from collections.abc import Callable


class PermissionLevel(Enum):
    """Permission levels for operations."""

    ALLOW = auto()  # Always allow without prompt
    ASK = auto()  # Always ask user
    DENY = auto()  # Always deny
    ASK_ONCE = auto()  # Ask once, remember for session
    ALLOW_SESSION = auto()  # Allow for this session only


class ToolCategory(Enum):
    """Categories of tools by risk level."""

    READ = "read"  # File reading, inspection
    WRITE = "write"  # File creation/modification
    EXECUTE = "execute"  # Command execution
    NETWORK = "network"  # Network operations
    SYSTEM = "system"  # System-level operations
    SEARCH = "search"  # Search operations (grep, glob)


# Tool category mappings
TOOL_CATEGORIES: dict[str, ToolCategory] = {
    "read_file": ToolCategory.READ,
    "write_file": ToolCategory.WRITE,
    "edit_file": ToolCategory.WRITE,
    "multi_edit_file": ToolCategory.WRITE,
    "bash": ToolCategory.EXECUTE,
    "grep": ToolCategory.SEARCH,
    "glob": ToolCategory.SEARCH,
    "ls_directory": ToolCategory.READ,
    "web_fetch": ToolCategory.NETWORK,
    "web_search": ToolCategory.NETWORK,
}


@dataclass
class PermissionRule:
    """A rule for permission matching.

    Attributes:
        pattern: Glob pattern for matching (file paths, commands, etc.)
        level: Permission level for this rule
        tool: Optional specific tool this rule applies to
        category: Optional category this rule applies to
        expires_at: Optional expiration timestamp
        reason: Optional reason for this rule
    """

    pattern: str
    level: PermissionLevel
    tool: str | None = None
    category: ToolCategory | None = None
    expires_at: float | None = None
    reason: str | None = None
    created_at: float = field(default_factory=time.time)

    def matches(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        category: ToolCategory | None = None,
    ) -> bool:
        """Check if this rule matches the given operation.

        Args:
            tool_name: Name of the tool
            tool_input: Tool input parameters
            category: Tool category

        Returns:
            True if rule matches
        """
        # Check expiration
        if self.expires_at and time.time() > self.expires_at:
            return False

        # Check tool-specific match
        if self.tool and self.tool != tool_name:
            return False

        # Check category match
        if self.category and category and self.category != category:
            return False

        # Match pattern against relevant input
        match_value = self._get_match_value(tool_name, tool_input)
        if match_value:
            return fnmatch.fnmatch(match_value, self.pattern)

        # If no specific match value, pattern matches tool name
        return fnmatch.fnmatch(tool_name, self.pattern)

    def _get_match_value(self, tool_name: str, tool_input: dict[str, Any]) -> str | None:
        """Get the value to match against the pattern.

        Args:
            tool_name: Name of the tool
            tool_input: Tool input parameters

        Returns:
            Value to match against pattern, or None
        """
        # File-based tools: match against file path
        if tool_name in ("read_file", "write_file", "edit_file", "multi_edit_file"):
            file_path: str | None = tool_input.get("file_path") or tool_input.get("path")
            return file_path

        # Bash: match against command
        if tool_name == "bash":
            command: str | None = tool_input.get("command")
            return command

        # Search tools: match against pattern
        if tool_name in ("grep", "glob"):
            path: str = str(tool_input.get("path", "."))
            return path

        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "pattern": self.pattern,
            "level": self.level.name,
            "tool": self.tool,
            "category": self.category.value if self.category else None,
            "expires_at": self.expires_at,
            "reason": self.reason,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PermissionRule:
        """Create from dictionary."""
        return cls(
            pattern=data["pattern"],
            level=PermissionLevel[data["level"]],
            tool=data.get("tool"),
            category=ToolCategory(data["category"]) if data.get("category") else None,
            expires_at=data.get("expires_at"),
            reason=data.get("reason"),
            created_at=data.get("created_at", time.time()),
        )


@dataclass
class PermissionDecision:
    """Record of a permission decision.

    Attributes:
        tool_name: Name of the tool
        tool_input_hash: Hash of tool input for matching
        level: Decision level
        timestamp: When decision was made
        expires_at: When decision expires (session-based)
    """

    tool_name: str
    tool_input_hash: str
    level: PermissionLevel
    timestamp: float = field(default_factory=time.time)
    expires_at: float | None = None

    @staticmethod
    def hash_input(tool_input: dict[str, Any]) -> str:
        """Create hash of tool input for matching."""
        # Sort keys for consistent hashing
        sorted_input = json.dumps(tool_input, sort_keys=True)
        return hashlib.sha256(sorted_input.encode()).hexdigest()[:16]


@dataclass
class AuditLogEntry:
    """Audit log entry for permission decisions.

    Attributes:
        timestamp: When the decision was made
        tool_name: Name of the tool
        tool_input: Tool input parameters (sanitized)
        decision: The permission decision
        rule_matched: The rule that matched (if any)
        user_response: User's response (if prompted)
    """

    timestamp: float
    tool_name: str
    tool_input: dict[str, Any]
    decision: PermissionLevel
    rule_matched: str | None = None
    user_response: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp,
            "datetime": datetime.fromtimestamp(self.timestamp).isoformat(),
            "tool_name": self.tool_name,
            "tool_input": self._sanitize_input(self.tool_input),
            "decision": self.decision.name,
            "rule_matched": self.rule_matched,
            "user_response": self.user_response,
        }

    def _sanitize_input(self, tool_input: dict[str, Any]) -> dict[str, Any]:
        """Sanitize tool input for logging (truncate large values)."""
        sanitized = {}
        for key, value in tool_input.items():
            if isinstance(value, str) and len(value) > 200:
                sanitized[key] = value[:200] + "...[truncated]"
            else:
                sanitized[key] = value
        return sanitized


class PermissionStore:
    """Persistent storage for permission rules and decisions."""

    def __init__(self, storage_dir: Path | None = None):
        """Initialize permission store.

        Args:
            storage_dir: Directory for storing permission data
        """
        self.storage_dir = storage_dir or Path.home() / ".devorbit" / "permissions"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.rules_file = self.storage_dir / "rules.json"
        self.audit_file = self.storage_dir / "audit.jsonl"

        self._rules: list[PermissionRule] = []
        self._load_rules()

    def _load_rules(self) -> None:
        """Load rules from disk."""
        if self.rules_file.exists():
            try:
                with self.rules_file.open(encoding="utf-8") as f:
                    data = json.load(f)
                    self._rules = [PermissionRule.from_dict(r) for r in data.get("rules", [])]
            except (json.JSONDecodeError, KeyError):
                self._rules = []

    def save_rules(self) -> None:
        """Save rules to disk."""
        with self.rules_file.open("w", encoding="utf-8") as f:
            json.dump({"rules": [r.to_dict() for r in self._rules]}, f, indent=2)

    def add_rule(self, rule: PermissionRule) -> None:
        """Add a permission rule."""
        self._rules.append(rule)
        self.save_rules()

    def remove_rule(self, pattern: str, tool: str | None = None) -> bool:
        """Remove a rule by pattern and optional tool.

        Returns:
            True if rule was removed
        """
        initial_count = len(self._rules)
        self._rules = [r for r in self._rules if not (r.pattern == pattern and r.tool == tool)]
        if len(self._rules) < initial_count:
            self.save_rules()
            return True
        return False

    def get_rules(self) -> list[PermissionRule]:
        """Get all rules (filtering expired ones)."""
        now = time.time()
        self._rules = [r for r in self._rules if not r.expires_at or r.expires_at > now]
        return self._rules.copy()

    def clear_rules(self) -> None:
        """Clear all rules."""
        self._rules = []
        self.save_rules()

    def log_audit(self, entry: AuditLogEntry) -> None:
        """Log an audit entry."""
        with self.audit_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict()) + "\n")

    def get_audit_log(self, limit: int = 100) -> list[AuditLogEntry]:
        """Get recent audit log entries.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of audit log entries (most recent first)
        """
        entries: list[AuditLogEntry] = []
        if not self.audit_file.exists():
            return entries

        # Read file in reverse (most recent first)
        with self.audit_file.open(encoding="utf-8") as f:
            lines = f.readlines()

        for line in reversed(lines[-limit:]):
            try:
                data = json.loads(line.strip())
                entries.append(
                    AuditLogEntry(
                        timestamp=data["timestamp"],
                        tool_name=data["tool_name"],
                        tool_input=data["tool_input"],
                        decision=PermissionLevel[data["decision"]],
                        rule_matched=data.get("rule_matched"),
                        user_response=data.get("user_response"),
                    )
                )
            except (json.JSONDecodeError, KeyError):
                continue

        return entries


class PermissionManager:
    """Central permission management system.

    Manages permission rules, session decisions, and audit logging.
    """

    # Default dangerous patterns (from DangerousCommandDetector)
    DANGEROUS_PATTERNS: ClassVar[list[str]] = [
        r"\brm\s+-rf\s+/",
        r"\brm\s+-rf\s+\*",
        r"\bdd\s+if=",
        r"\bmkfs\.",
        r"\bformat\s+",
        r">\s*/dev/sd[a-z]",
        r"\bfdisk\s+",
        r"\bcurl\s+.*\|\s*(bash|sh)",
        r"\bwget\s+.*\|\s*(bash|sh)",
        r"\bchmod\s+777",
        r"\bsudo\s+rm",
        r":\(\)\{\s*:\|\:&\s*\};:",
    ]

    DANGEROUS_PATHS: ClassVar[list[str]] = [
        "/etc/passwd",
        "/etc/shadow",
        "/etc/sudoers",
        "/etc/hosts",
        "/boot",
        "/sys",
        "/proc",
        "~/.ssh/id_rsa",
        "~/.ssh/authorized_keys",
    ]

    def __init__(
        self,
        store: PermissionStore | None = None,
        prompt_callback: Callable[[str, dict[str, Any], bool, str | None], bool] | None = None,
    ):
        """Initialize permission manager.

        Args:
            store: Permission store for persistence
            prompt_callback: Callback for prompting user (tool_name, tool_input, is_dangerous, reason) -> bool
        """
        self.store = store or PermissionStore()
        self.prompt_callback = prompt_callback

        # Session-level decisions (cleared on restart)
        self._session_decisions: dict[str, PermissionDecision] = {}

        # Default category permissions
        self._category_defaults: dict[ToolCategory, PermissionLevel] = {
            ToolCategory.READ: PermissionLevel.ASK_ONCE,
            ToolCategory.WRITE: PermissionLevel.ASK,
            ToolCategory.EXECUTE: PermissionLevel.ASK,
            ToolCategory.NETWORK: PermissionLevel.ASK,
            ToolCategory.SYSTEM: PermissionLevel.ASK,
            ToolCategory.SEARCH: PermissionLevel.ASK_ONCE,
        }

    def check_permission(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        auto_approve: bool = False,
    ) -> tuple[bool, PermissionLevel, str | None]:
        """Check if an operation is permitted.

        Args:
            tool_name: Name of the tool
            tool_input: Tool input parameters
            auto_approve: Whether auto-approve mode is enabled

        Returns:
            Tuple of (is_allowed, decision_level, reason)
        """
        # Get tool category
        category = TOOL_CATEGORIES.get(tool_name)

        # Check for dangerous operations first
        is_dangerous, danger_reason = self._check_dangerous(tool_name, tool_input)
        if is_dangerous:
            # Dangerous operations always require explicit approval
            decision = self._prompt_user(tool_name, tool_input, True, danger_reason)
            level = PermissionLevel.ALLOW if decision else PermissionLevel.DENY
            self._log_decision(tool_name, tool_input, level, danger_reason, decision)
            return decision, level, danger_reason

        # Check persistent rules
        for rule in self.store.get_rules():
            if rule.matches(tool_name, tool_input, category):
                if rule.level == PermissionLevel.ALLOW:
                    self._log_decision(tool_name, tool_input, rule.level, rule.pattern)
                    return True, rule.level, f"Matched rule: {rule.pattern}"
                if rule.level == PermissionLevel.DENY:
                    self._log_decision(tool_name, tool_input, rule.level, rule.pattern)
                    return False, rule.level, f"Denied by rule: {rule.pattern}"
                # ASK or ASK_ONCE - continue to prompting

        # Check session decisions
        session_key = self._get_session_key(tool_name, tool_input)
        if session_key in self._session_decisions:
            session_decision = self._session_decisions[session_key]
            if not session_decision.expires_at or time.time() < session_decision.expires_at:
                allowed = session_decision.level in (
                    PermissionLevel.ALLOW,
                    PermissionLevel.ALLOW_SESSION,
                )
                return allowed, session_decision.level, "Session decision"

        # Check auto-approve mode
        if auto_approve and category in (ToolCategory.READ, ToolCategory.SEARCH):
            self._log_decision(tool_name, tool_input, PermissionLevel.ALLOW, "auto_approve")
            return True, PermissionLevel.ALLOW, "Auto-approved (safe operation)"

        # Get default permission for category
        default_level = (
            self._category_defaults.get(category, PermissionLevel.ASK)
            if category
            else PermissionLevel.ASK
        )

        # Prompt user if needed
        if default_level in (PermissionLevel.ASK, PermissionLevel.ASK_ONCE):
            decision = self._prompt_user(tool_name, tool_input, False, None)
            level = PermissionLevel.ALLOW if decision else PermissionLevel.DENY

            # Remember for session if ASK_ONCE
            if default_level == PermissionLevel.ASK_ONCE and decision:
                self._session_decisions[session_key] = PermissionDecision(
                    tool_name=tool_name,
                    tool_input_hash=PermissionDecision.hash_input(tool_input),
                    level=PermissionLevel.ALLOW_SESSION,
                )

            self._log_decision(tool_name, tool_input, level, None, decision)
            return decision, level, None

        # Default allow/deny
        allowed = default_level == PermissionLevel.ALLOW
        self._log_decision(tool_name, tool_input, default_level)
        return allowed, default_level, None

    def _check_dangerous(
        self, tool_name: str, tool_input: dict[str, Any]
    ) -> tuple[bool, str | None]:
        """Check if operation is dangerous.

        Args:
            tool_name: Name of the tool
            tool_input: Tool input parameters

        Returns:
            Tuple of (is_dangerous, reason)
        """
        # Check bash commands
        if tool_name == "bash":
            command = tool_input.get("command", "")
            for pattern in self.DANGEROUS_PATTERNS:
                if re.search(pattern, command, re.IGNORECASE):
                    return True, f"Dangerous command pattern: {pattern}"

        # Check file paths
        if tool_name in ("write_file", "edit_file"):
            file_path = tool_input.get("file_path", "") or tool_input.get("path", "")
            for dangerous_path in self.DANGEROUS_PATHS:
                if dangerous_path in file_path:
                    return True, f"Sensitive path: {dangerous_path}"

        return False, None

    def _prompt_user(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        is_dangerous: bool,
        reason: str | None,
    ) -> bool:
        """Prompt user for permission.

        Args:
            tool_name: Name of the tool
            tool_input: Tool input parameters
            is_dangerous: Whether operation is dangerous
            reason: Reason for prompt

        Returns:
            True if approved, False if denied
        """
        if self.prompt_callback:
            return self.prompt_callback(tool_name, tool_input, is_dangerous, reason)
        # Default: deny if no callback
        return False

    def _get_session_key(self, tool_name: str, tool_input: dict[str, Any]) -> str:
        """Generate session key for a tool call."""
        # For some tools, use specific input for key
        if tool_name in ("read_file", "write_file", "edit_file"):
            path = tool_input.get("file_path") or tool_input.get("path", "")
            return f"{tool_name}:{path}"
        if tool_name == "bash":
            # For bash, just use tool name (too variable for caching)
            return "bash:*"
        return f"{tool_name}:*"

    def _log_decision(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        level: PermissionLevel,
        rule_matched: str | None = None,
        user_response: bool | None = None,
    ) -> None:
        """Log a permission decision."""
        entry = AuditLogEntry(
            timestamp=time.time(),
            tool_name=tool_name,
            tool_input=tool_input,
            decision=level,
            rule_matched=rule_matched,
            user_response=(
                "approved" if user_response else "denied" if user_response is False else None
            ),
        )
        self.store.log_audit(entry)

    # Rule management methods

    def add_rule(
        self,
        pattern: str,
        level: PermissionLevel,
        tool: str | None = None,
        category: ToolCategory | None = None,
        expires_in: float | None = None,
        reason: str | None = None,
    ) -> PermissionRule:
        """Add a permission rule.

        Args:
            pattern: Glob pattern to match
            level: Permission level
            tool: Specific tool (optional)
            category: Tool category (optional)
            expires_in: Seconds until expiration (optional)
            reason: Reason for rule (optional)

        Returns:
            The created rule
        """
        expires_at = time.time() + expires_in if expires_in else None
        rule = PermissionRule(
            pattern=pattern,
            level=level,
            tool=tool,
            category=category,
            expires_at=expires_at,
            reason=reason,
        )
        self.store.add_rule(rule)
        return rule

    def remove_rule(self, pattern: str, tool: str | None = None) -> bool:
        """Remove a rule."""
        return self.store.remove_rule(pattern, tool)

    def list_rules(self) -> list[PermissionRule]:
        """List all active rules."""
        return self.store.get_rules()

    def clear_session(self) -> None:
        """Clear session-level decisions."""
        self._session_decisions.clear()

    def set_category_default(self, category: ToolCategory, level: PermissionLevel) -> None:
        """Set default permission level for a category."""
        self._category_defaults[category] = level

    def get_audit_log(self, limit: int = 100) -> list[AuditLogEntry]:
        """Get recent audit log entries."""
        return self.store.get_audit_log(limit)


# Singleton instance
_permission_manager: PermissionManager | None = None


def get_permission_manager() -> PermissionManager:
    """Get or create the global permission manager instance."""
    global _permission_manager  # noqa: PLW0603
    if _permission_manager is None:
        _permission_manager = PermissionManager()
    return _permission_manager


def reset_permission_manager() -> None:
    """Reset the global permission manager (for testing)."""
    global _permission_manager  # noqa: PLW0603
    _permission_manager = None


__all__ = [
    "TOOL_CATEGORIES",
    "AuditLogEntry",
    "PermissionDecision",
    "PermissionLevel",
    "PermissionManager",
    "PermissionRule",
    "PermissionStore",
    "ToolCategory",
    "get_permission_manager",
    "reset_permission_manager",
]
