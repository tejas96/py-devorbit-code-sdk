"""Configuration management for Devorbit SDK.

This module provides a comprehensive configuration system supporting:
- PROJECT.md / CLAUDE.md - Project context and instructions
- .devorbit.json - JSON configuration for settings
- Environment variables - Runtime configuration
- Programmatic configuration - Python API

Priority order: env vars > programmatic > .devorbit.json > PROJECT.md > defaults
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ._tool_helpers import beta_tool
import contextlib


# ============================================================================
# Configuration Data Classes
# ============================================================================


@dataclass
class DevorbitConfig:
    """Devorbit SDK configuration.

    Attributes:
        project_context: Project-level context from PROJECT.md
        model: Default model to use
        provider: Default provider to use
        max_tokens: Default max tokens
        temperature: Default temperature
        system_prompt: Custom system prompt
        hooks_enabled: Whether hooks are enabled
        hooks: Hook configurations
        commands_dir: Directory for slash commands
        custom_settings: Additional custom settings
    """

    project_context: str = ""
    model: str | None = None
    provider: str | None = None
    max_tokens: int = 4096
    temperature: float = 1.0
    system_prompt: str = ""
    hooks_enabled: bool = True
    hooks: dict[str, Any] = field(default_factory=dict)
    commands_dir: str = ".devorbit/commands"
    custom_settings: dict[str, Any] = field(default_factory=dict)

    def merge(self, other: "DevorbitConfig") -> "DevorbitConfig":
        """Merge with another config (other takes priority)."""
        return DevorbitConfig(
            project_context=other.project_context or self.project_context,
            model=other.model or self.model,
            provider=other.provider or self.provider,
            max_tokens=other.max_tokens if other.max_tokens != 4096 else self.max_tokens,
            temperature=other.temperature if other.temperature != 1.0 else self.temperature,
            system_prompt=other.system_prompt or self.system_prompt,
            hooks_enabled=other.hooks_enabled,
            hooks={**self.hooks, **other.hooks},
            commands_dir=other.commands_dir
            if other.commands_dir != ".devorbit/commands"
            else self.commands_dir,
            custom_settings={**self.custom_settings, **other.custom_settings},
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "project_context": self.project_context,
            "model": self.model,
            "provider": self.provider,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "system_prompt": self.system_prompt,
            "hooks_enabled": self.hooks_enabled,
            "hooks": self.hooks,
            "commands_dir": self.commands_dir,
            "custom_settings": self.custom_settings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DevorbitConfig":
        """Create from dictionary."""
        return cls(
            project_context=data.get("project_context", ""),
            model=data.get("model"),
            provider=data.get("provider"),
            max_tokens=data.get("max_tokens", 4096),
            temperature=data.get("temperature", 1.0),
            system_prompt=data.get("system_prompt", ""),
            hooks_enabled=data.get("hooks_enabled", True),
            hooks=data.get("hooks", {}),
            commands_dir=data.get("commands_dir", ".devorbit/commands"),
            custom_settings=data.get("custom_settings", {}),
        )


# ============================================================================
# Configuration Loaders
# ============================================================================


def load_project_md(project_root: Path | None = None) -> str:
    """Load PROJECT.md or CLAUDE.md file.

    Args:
        project_root: Root directory to search (default: current directory)

    Returns:
        Content of PROJECT.md or CLAUDE.md, empty string if not found
    """
    root = project_root or Path.cwd()

    # Check for PROJECT.md first, then CLAUDE.md
    for filename in ["PROJECT.md", "CLAUDE.md"]:
        file_path = root / filename
        if file_path.exists():
            try:
                return file_path.read_text(encoding="utf-8")
            except Exception:
                continue

    return ""


def load_devorbit_json(project_root: Path | None = None) -> dict[str, Any]:
    """Load .devorbit.json configuration.

    Args:
        project_root: Root directory to search (default: current directory)

    Returns:
        Configuration dictionary, empty dict if not found
    """
    root = project_root or Path.cwd()
    config_path = root / ".devorbit.json"

    if not config_path.exists():
        return {}

    try:
        with config_path.open(encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def load_env_config() -> dict[str, Any]:
    """Load configuration from environment variables.

    Environment variables:
        DEVORBIT_MODEL: Default model
        DEVORBIT_PROVIDER: Default provider
        DEVORBIT_MAX_TOKENS: Default max tokens
        DEVORBIT_TEMPERATURE: Default temperature
        DEVORBIT_HOOKS_ENABLED: Enable/disable hooks

    Returns:
        Configuration dictionary from environment
    """
    config: dict[str, Any] = {}

    if model := os.getenv("DEVORBIT_MODEL"):
        config["model"] = model

    if provider := os.getenv("DEVORBIT_PROVIDER"):
        config["provider"] = provider

    if max_tokens := os.getenv("DEVORBIT_MAX_TOKENS"):
        with contextlib.suppress(ValueError):
            config["max_tokens"] = int(max_tokens)

    if temperature := os.getenv("DEVORBIT_TEMPERATURE"):
        with contextlib.suppress(ValueError):
            config["temperature"] = float(temperature)

    if hooks_enabled := os.getenv("DEVORBIT_HOOKS_ENABLED"):
        config["hooks_enabled"] = hooks_enabled.lower() in ("true", "1", "yes")

    return config


def load_config(project_root: Path | None = None) -> DevorbitConfig:
    """Load complete configuration from all sources.

    Priority order:
    1. Environment variables (highest)
    2. .devorbit.json
    3. PROJECT.md / CLAUDE.md
    4. Defaults (lowest)

    Args:
        project_root: Root directory to search (default: current directory)

    Returns:
        Complete merged configuration
    """
    # Start with defaults
    config = DevorbitConfig()

    # Load PROJECT.md
    project_context = load_project_md(project_root)
    if project_context:
        config = config.merge(DevorbitConfig(project_context=project_context))

    # Load .devorbit.json
    json_config = load_devorbit_json(project_root)
    if json_config:
        config = config.merge(DevorbitConfig.from_dict(json_config))

    # Load environment variables
    env_config = load_env_config()
    if env_config:
        config = config.merge(DevorbitConfig.from_dict(env_config))

    return config


def save_config(config: DevorbitConfig, project_root: Path | None = None) -> dict[str, Any]:
    """Save configuration to .devorbit.json.

    Args:
        config: Configuration to save
        project_root: Root directory (default: current directory)

    Returns:
        Result dictionary with success status
    """
    root = project_root or Path.cwd()
    config_path = root / ".devorbit.json"

    try:
        # Don't save project_context to JSON (it comes from PROJECT.md)
        config_dict = config.to_dict()
        config_dict.pop("project_context", None)

        with config_path.open("w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=2)

        return {
            "success": True,
            "config_path": str(config_path.absolute()),
            "message": "Configuration saved successfully",
        }
    except Exception as e:
        return {
            "error": f"Failed to save configuration: {e!s}",
            "config_path": str(config_path.absolute()),
        }


# ============================================================================
# Configuration Tools (for agent use)
# ============================================================================


@beta_tool
def read_config(project_root: str | None = None) -> dict[str, Any]:
    """Read Devorbit configuration from all sources.

    Loads configuration from PROJECT.md/CLAUDE.md, .devorbit.json,
    and environment variables, merging them in priority order.

    Args:
        project_root: Project root directory (default: current directory)

    Returns:
        Complete configuration dictionary
    """
    try:
        root = Path(project_root) if project_root else None
        config = load_config(root)
        return {
            "success": True,
            "config": config.to_dict(),
            "sources": {
                "project_md": bool(config.project_context),
                "devorbit_json": (root or Path.cwd()) / ".devorbit.json",
                "environment": bool(load_env_config()),
            },
        }
    except Exception as e:
        return {
            "error": f"Failed to read configuration: {e!s}",
        }


@beta_tool
def update_config(
    project_root: str | None = None,
    model: str | None = None,
    provider: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
    system_prompt: str | None = None,
    hooks_enabled: bool | None = None,
) -> dict[str, Any]:
    """Update Devorbit configuration and save to .devorbit.json.

    Args:
        project_root: Project root directory (default: current directory)
        model: Default model to use
        provider: Default provider to use
        max_tokens: Default max tokens
        temperature: Default temperature
        system_prompt: Custom system prompt
        hooks_enabled: Enable/disable hooks

    Returns:
        Result dictionary with updated configuration
    """
    try:
        root = Path(project_root) if project_root else None

        # Load current config
        config = load_config(root)

        # Update only specified fields
        if model is not None:
            config.model = model
        if provider is not None:
            config.provider = provider
        if max_tokens is not None:
            config.max_tokens = max_tokens
        if temperature is not None:
            config.temperature = temperature
        if system_prompt is not None:
            config.system_prompt = system_prompt
        if hooks_enabled is not None:
            config.hooks_enabled = hooks_enabled

        # Save to .devorbit.json
        result = save_config(config, root)

        if "error" in result:
            return result

        return {
            "success": True,
            "config": config.to_dict(),
            **result,
        }
    except Exception as e:
        return {
            "error": f"Failed to update configuration: {e!s}",
        }


# ============================================================================
# Helper Functions
# ============================================================================


def get_all_config_tools() -> list[dict[str, Any]]:
    """Get all configuration tool definitions.

    Returns:
        List of configuration tool definitions for use with Devorbit client
    """
    return [
        read_config.tool_definition,  # type: ignore[attr-defined]
        update_config.tool_definition,  # type: ignore[attr-defined]
    ]


# Export configuration classes and functions
__all__ = [
    "DevorbitConfig",
    "get_all_config_tools",
    "load_config",
    "load_devorbit_json",
    "load_env_config",
    "load_project_md",
    "read_config",
    "save_config",
    "update_config",
]
