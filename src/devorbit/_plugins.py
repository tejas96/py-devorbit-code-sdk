"""Plugin system for Devorbit SDK.

This module provides an extensible plugin framework:
- Discover plugins via entry points or local directories
- Load and validate plugins
- Install/uninstall plugins via pip
- Enable/disable plugins dynamically
- Plugin contributions: tools, providers, commands, hooks
"""

import importlib
import importlib.metadata
import json
import subprocess
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from ._tool_helpers import beta_tool


# ============================================================================
# Plugin Protocol & Interface
# ============================================================================


class DevorbitPlugin(Protocol):
    """Protocol that all Devorbit plugins must implement."""

    name: str
    version: str
    description: str

    def initialize(self) -> dict[str, Any]:
        """Initialize the plugin.

        Returns:
            Dictionary with initialization status and metadata
        """
        ...

    def get_tools(self) -> list[dict[str, Any]]:
        """Get tool definitions provided by this plugin.

        Returns:
            List of tool definitions
        """
        ...

    def cleanup(self) -> None:
        """Cleanup plugin resources."""
        ...


class BasePlugin(ABC):
    """Base class for Devorbit plugins."""

    def __init__(self) -> None:
        """Initialize base plugin."""
        self.initialized = False

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name."""

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Plugin description."""

    def initialize(self) -> dict[str, Any]:
        """Initialize the plugin.

        Returns:
            Dictionary with initialization status
        """
        self.initialized = True
        return {
            "success": True,
            "plugin": self.name,
            "version": self.version,
        }

    def get_tools(self) -> list[dict[str, Any]]:
        """Get tool definitions provided by this plugin.

        Returns:
            List of tool definitions
        """
        return []

    def cleanup(self) -> None:
        """Cleanup plugin resources."""
        self.initialized = False


# ============================================================================
# Plugin Data Classes
# ============================================================================


@dataclass
class PluginMetadata:
    """Plugin metadata.

    Attributes:
        name: Plugin name
        version: Plugin version
        description: Plugin description
        author: Plugin author
        license: Plugin license
        dependencies: Plugin dependencies
        entry_point: Plugin entry point module
        plugin_type: Type of plugin (pip, local, builtin)
        enabled: Whether plugin is enabled
    """

    name: str
    version: str
    description: str
    author: str = ""
    license: str = ""
    dependencies: list[str] = field(default_factory=list)
    entry_point: str | None = None
    plugin_type: str = "pip"  # pip, local, builtin
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "license": self.license,
            "dependencies": self.dependencies,
            "entry_point": self.entry_point,
            "plugin_type": self.plugin_type,
            "enabled": self.enabled,
        }


@dataclass
class LoadedPlugin:
    """Loaded plugin instance.

    Attributes:
        metadata: Plugin metadata
        instance: Plugin instance
        initialized: Whether plugin is initialized
    """

    metadata: PluginMetadata
    instance: DevorbitPlugin
    initialized: bool = False


# ============================================================================
# Plugin Registry
# ============================================================================


class PluginRegistry:
    """Registry for managing plugins."""

    def __init__(self) -> None:
        """Initialize plugin registry."""
        self._plugins: dict[str, LoadedPlugin] = {}

    def register(self, plugin: LoadedPlugin) -> None:
        """Register a plugin.

        Args:
            plugin: Plugin to register
        """
        self._plugins[plugin.metadata.name] = plugin

    def get(self, name: str) -> LoadedPlugin | None:
        """Get plugin by name.

        Args:
            name: Plugin name

        Returns:
            LoadedPlugin if found, None otherwise
        """
        return self._plugins.get(name)

    def list_plugins(self, enabled_only: bool = False) -> list[LoadedPlugin]:
        """List all registered plugins.

        Args:
            enabled_only: Only return enabled plugins

        Returns:
            List of plugins
        """
        plugins = list(self._plugins.values())

        if enabled_only:
            plugins = [p for p in plugins if p.metadata.enabled]

        return sorted(plugins, key=lambda p: p.metadata.name)

    def remove(self, name: str) -> bool:
        """Remove plugin by name.

        Args:
            name: Plugin name

        Returns:
            True if removed, False if not found
        """
        if name not in self._plugins:
            return False

        plugin = self._plugins.pop(name)
        # Cleanup plugin
        if plugin.initialized:
            plugin.instance.cleanup()

        return True

    def clear(self) -> None:
        """Clear all plugins."""
        # Cleanup all initialized plugins
        for plugin in self._plugins.values():
            if plugin.initialized:
                plugin.instance.cleanup()

        self._plugins.clear()


# Global plugin registry
_REGISTRY = PluginRegistry()


# ============================================================================
# Plugin Discovery
# ============================================================================


def discover_pip_plugins() -> list[PluginMetadata]:
    """Discover plugins installed via pip using entry points.

    Returns:
        List of discovered plugin metadata
    """
    plugins = []

    try:
        # Discover plugins via entry point group "devorbit.plugins"
        entry_points = importlib.metadata.entry_points()

        # Handle both old and new entry_points API
        plugin_eps: Any
        if hasattr(entry_points, "select"):
            # Python 3.10+
            plugin_eps = entry_points.select(group="devorbit.plugins")
        else:
            # Python 3.9 - entry_points returns a dict
            plugin_eps = entry_points.get("devorbit.plugins", [])  # type: ignore[attr-defined]

        for ep in plugin_eps:
            try:
                # Get distribution metadata
                dist = importlib.metadata.distribution(ep.name)

                metadata = PluginMetadata(
                    name=ep.name,
                    version=dist.version,
                    description=dist.metadata.get("Summary", ""),
                    author=dist.metadata.get("Author", ""),
                    license=dist.metadata.get("License", ""),
                    entry_point=ep.value,
                    plugin_type="pip",
                )
                plugins.append(metadata)

            except Exception:
                # Skip plugins that can't be loaded
                continue

    except Exception:
        # Entry points not available or error occurred
        pass

    return plugins


def discover_local_plugins(plugins_dir: Path) -> list[PluginMetadata]:
    """Discover plugins from a local directory.

    Each plugin should be in its own subdirectory with a plugin.json file.

    Args:
        plugins_dir: Directory containing plugins

    Returns:
        List of discovered plugin metadata
    """
    if not plugins_dir.exists() or not plugins_dir.is_dir():
        return []

    plugins = []

    for plugin_dir in plugins_dir.iterdir():
        if not plugin_dir.is_dir():
            continue

        # Look for plugin.json
        plugin_json = plugin_dir / "plugin.json"
        if not plugin_json.exists():
            continue

        try:
            with plugin_json.open(encoding="utf-8") as f:
                data = json.load(f)

            metadata = PluginMetadata(
                name=data.get("name", plugin_dir.name),
                version=data.get("version", "0.0.0"),
                description=data.get("description", ""),
                author=data.get("author", ""),
                license=data.get("license", ""),
                dependencies=data.get("dependencies", []),
                entry_point=data.get("entry_point"),
                plugin_type="local",
            )
            plugins.append(metadata)

        except Exception:
            # Skip plugins with invalid metadata
            continue

    return plugins


def discover_all_plugins(project_root: Path | None = None) -> list[PluginMetadata]:
    """Discover all available plugins.

    Searches:
    1. Pip-installed plugins (via entry points)
    2. Local plugins in .devorbit/plugins/
    3. Local plugins in .claude/plugins/
    4. Local plugins in plugins/

    Args:
        project_root: Project root directory (default: current directory)

    Returns:
        List of all discovered plugins
    """
    plugins = []

    # Discover pip plugins
    plugins.extend(discover_pip_plugins())

    # Discover local plugins
    root = project_root or Path.cwd()
    for dir_name in [".devorbit/plugins", ".claude/plugins", "plugins"]:
        plugins_dir = root / dir_name
        plugins.extend(discover_local_plugins(plugins_dir))

    return plugins


# ============================================================================
# Plugin Loading
# ============================================================================


def load_plugin(metadata: PluginMetadata) -> LoadedPlugin | None:
    """Load a plugin from its metadata.

    Args:
        metadata: Plugin metadata

    Returns:
        LoadedPlugin if successful, None otherwise
    """
    if not metadata.entry_point:
        return None

    try:
        # Import the plugin module
        module_path, class_name = metadata.entry_point.rsplit(":", 1)
        module = importlib.import_module(module_path)
        plugin_class = getattr(module, class_name)

        # Instantiate the plugin
        instance = plugin_class()

        # Verify it implements the protocol
        if not all(
            hasattr(instance, attr)
            for attr in ["name", "version", "description", "initialize", "get_tools"]
        ):
            return None

        return LoadedPlugin(
            metadata=metadata,
            instance=instance,
            initialized=False,
        )

    except Exception:
        return None


def initialize_plugin(plugin: LoadedPlugin) -> dict[str, Any]:
    """Initialize a loaded plugin.

    Args:
        plugin: Plugin to initialize

    Returns:
        Initialization result
    """
    if plugin.initialized:
        return {
            "success": True,
            "plugin": plugin.metadata.name,
            "message": "Plugin already initialized",
        }

    try:
        result = plugin.instance.initialize()
        if result.get("success"):
            plugin.initialized = True

        return result

    except Exception as e:
        return {
            "error": f"Failed to initialize plugin: {e!s}",
            "plugin": plugin.metadata.name,
        }


# ============================================================================
# Plugin Installation
# ============================================================================


def install_plugin(package_name: str) -> dict[str, Any]:
    """Install a plugin via pip.

    Args:
        package_name: Package name to install

    Returns:
        Installation result
    """
    try:
        # Install using pip
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package_name],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            return {
                "success": True,
                "package": package_name,
                "message": f"Successfully installed {package_name}",
                "stdout": result.stdout,
            }
        return {
            "error": "Installation failed",
            "package": package_name,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }

    except Exception as e:
        return {
            "error": f"Failed to install plugin: {e!s}",
            "package": package_name,
        }


def uninstall_plugin(package_name: str) -> dict[str, Any]:
    """Uninstall a plugin via pip.

    Args:
        package_name: Package name to uninstall

    Returns:
        Uninstallation result
    """
    try:
        # Uninstall using pip
        result = subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", "-y", package_name],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            return {
                "success": True,
                "package": package_name,
                "message": f"Successfully uninstalled {package_name}",
                "stdout": result.stdout,
            }
        return {
            "error": "Uninstallation failed",
            "package": package_name,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }

    except Exception as e:
        return {
            "error": f"Failed to uninstall plugin: {e!s}",
            "package": package_name,
        }


# ============================================================================
# Plugin Tools (for agent use)
# ============================================================================


@beta_tool
def list_plugins(
    enabled_only: bool = False,
    project_root: str | None = None,
) -> dict[str, Any]:
    """List all available plugins.

    Args:
        enabled_only: Only return enabled plugins
        project_root: Project root directory (default: current directory)

    Returns:
        Dictionary with list of plugins
    """
    try:
        root = Path(project_root) if project_root else None

        # Discover all plugins
        discovered = discover_all_plugins(root)

        # Also include registered plugins
        registered = _REGISTRY.list_plugins(enabled_only)

        # Combine and deduplicate
        all_plugins = {}

        for metadata in discovered:
            if enabled_only and not metadata.enabled:
                continue

            if metadata.name not in all_plugins:
                all_plugins[metadata.name] = metadata.to_dict()

        for plugin in registered:
            if plugin.metadata.name not in all_plugins:
                all_plugins[plugin.metadata.name] = {
                    **plugin.metadata.to_dict(),
                    "initialized": plugin.initialized,
                }

        return {
            "success": True,
            "plugins": list(all_plugins.values()),
            "count": len(all_plugins),
        }

    except Exception as e:
        return {
            "error": f"Failed to list plugins: {e!s}",
        }


@beta_tool
def load_and_initialize_plugin(
    plugin_name: str,
    project_root: str | None = None,
) -> dict[str, Any]:
    """Load and initialize a plugin.

    Args:
        plugin_name: Name of plugin to load
        project_root: Project root directory (default: current directory)

    Returns:
        Load and initialization result
    """
    try:
        root = Path(project_root) if project_root else None

        # Check if already loaded
        if existing := _REGISTRY.get(plugin_name):
            if existing.initialized:
                return {
                    "success": True,
                    "plugin": plugin_name,
                    "message": "Plugin already loaded and initialized",
                    "metadata": existing.metadata.to_dict(),
                }

            # Initialize existing plugin
            result = initialize_plugin(existing)
            return {**result, "metadata": existing.metadata.to_dict()}

        # Discover plugins
        discovered = discover_all_plugins(root)

        # Find the plugin
        metadata = None
        for meta in discovered:
            if meta.name == plugin_name:
                metadata = meta
                break

        if not metadata:
            return {
                "error": f"Plugin not found: {plugin_name}",
                "plugin": plugin_name,
            }

        # Load plugin
        plugin = load_plugin(metadata)

        if not plugin:
            return {
                "error": f"Failed to load plugin: {plugin_name}",
                "plugin": plugin_name,
            }

        # Initialize plugin
        init_result = initialize_plugin(plugin)

        if init_result.get("success"):
            # Register plugin
            _REGISTRY.register(plugin)

        return {
            **init_result,
            "metadata": metadata.to_dict(),
        }

    except Exception as e:
        return {
            "error": f"Failed to load and initialize plugin: {e!s}",
            "plugin": plugin_name,
        }


@beta_tool
def enable_plugin(plugin_name: str) -> dict[str, Any]:
    """Enable a plugin.

    Args:
        plugin_name: Name of plugin to enable

    Returns:
        Result dictionary
    """
    try:
        plugin = _REGISTRY.get(plugin_name)

        if not plugin:
            return {
                "error": f"Plugin not found in registry: {plugin_name}",
                "plugin": plugin_name,
            }

        plugin.metadata.enabled = True

        return {
            "success": True,
            "plugin": plugin_name,
            "message": f"Plugin {plugin_name} enabled",
        }

    except Exception as e:
        return {
            "error": f"Failed to enable plugin: {e!s}",
            "plugin": plugin_name,
        }


@beta_tool
def disable_plugin(plugin_name: str) -> dict[str, Any]:
    """Disable a plugin.

    Args:
        plugin_name: Name of plugin to disable

    Returns:
        Result dictionary
    """
    try:
        plugin = _REGISTRY.get(plugin_name)

        if not plugin:
            return {
                "error": f"Plugin not found in registry: {plugin_name}",
                "plugin": plugin_name,
            }

        plugin.metadata.enabled = False

        return {
            "success": True,
            "plugin": plugin_name,
            "message": f"Plugin {plugin_name} disabled",
        }

    except Exception as e:
        return {
            "error": f"Failed to disable plugin: {e!s}",
            "plugin": plugin_name,
        }


@beta_tool
def get_plugin_tools(plugin_name: str) -> dict[str, Any]:
    """Get tools provided by a plugin.

    Args:
        plugin_name: Name of plugin

    Returns:
        Dictionary with plugin tools
    """
    try:
        plugin = _REGISTRY.get(plugin_name)

        if not plugin:
            return {
                "error": f"Plugin not found in registry: {plugin_name}",
                "plugin": plugin_name,
            }

        if not plugin.initialized:
            return {
                "error": f"Plugin not initialized: {plugin_name}",
                "plugin": plugin_name,
            }

        tools = plugin.instance.get_tools()

        return {
            "success": True,
            "plugin": plugin_name,
            "tools": tools,
            "count": len(tools),
        }

    except Exception as e:
        return {
            "error": f"Failed to get plugin tools: {e!s}",
            "plugin": plugin_name,
        }


# ============================================================================
# Helper Functions
# ============================================================================


def get_all_plugin_tools() -> list[dict[str, Any]]:
    """Get all plugin tool definitions.

    Returns:
        List of plugin tool definitions for use with Devorbit client
    """
    return [
        list_plugins.tool_definition,  # type: ignore[attr-defined]
        load_and_initialize_plugin.tool_definition,  # type: ignore[attr-defined]
        enable_plugin.tool_definition,  # type: ignore[attr-defined]
        disable_plugin.tool_definition,  # type: ignore[attr-defined]
        get_plugin_tools.tool_definition,  # type: ignore[attr-defined]
    ]


def get_plugin_registry() -> PluginRegistry:
    """Get the global plugin registry.

    Returns:
        Global plugin registry
    """
    return _REGISTRY


# Export plugin classes and functions
__all__ = [
    "BasePlugin",
    "DevorbitPlugin",
    "LoadedPlugin",
    "PluginMetadata",
    "PluginRegistry",
    "disable_plugin",
    "discover_all_plugins",
    "discover_local_plugins",
    "discover_pip_plugins",
    "enable_plugin",
    "get_all_plugin_tools",
    "get_plugin_registry",
    "get_plugin_tools",
    "initialize_plugin",
    "install_plugin",
    "list_plugins",
    "load_and_initialize_plugin",
    "load_plugin",
    "uninstall_plugin",
]
