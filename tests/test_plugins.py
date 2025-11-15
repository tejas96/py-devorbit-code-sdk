"""Tests for plugin system."""

import json
from pathlib import Path
from typing import Any

import pytest

from devorbit._plugins import (
    BasePlugin,
    LoadedPlugin,
    PluginMetadata,
    PluginRegistry,
    disable_plugin,
    discover_all_plugins,
    discover_local_plugins,
    enable_plugin,
    get_all_plugin_tools,
    get_plugin_registry,
    get_plugin_tools,
    initialize_plugin,
    list_plugins,
)


class TestPlugin(BasePlugin):
    """Test plugin implementation."""

    @property
    def name(self) -> str:
        """Plugin name."""
        return "test-plugin"

    @property
    def version(self) -> str:
        """Plugin version."""
        return "1.0.0"

    @property
    def description(self) -> str:
        """Plugin description."""
        return "Test plugin for testing"

    def get_tools(self) -> list[dict[str, Any]]:
        """Get tool definitions."""
        return [
            {
                "name": "test_tool",
                "description": "Test tool",
                "input_schema": {"type": "object"},
            }
        ]


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    """Create a temporary project directory."""
    return tmp_path


@pytest.fixture
def plugins_dir(temp_project: Path) -> Path:
    """Create plugins directory."""
    plugin_dir = temp_project / ".devorbit" / "plugins"
    plugin_dir.mkdir(parents=True)
    return plugin_dir


class TestPluginMetadata:
    """Test PluginMetadata class."""

    def test_metadata_creation(self) -> None:
        """Test creating plugin metadata."""
        metadata = PluginMetadata(
            name="test-plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            license="MIT",
            dependencies=["dep1", "dep2"],
            entry_point="test_plugin:Plugin",
            plugin_type="pip",
        )

        assert metadata.name == "test-plugin"
        assert metadata.version == "1.0.0"
        assert metadata.description == "Test plugin"
        assert metadata.author == "Test Author"
        assert metadata.license == "MIT"
        assert metadata.dependencies == ["dep1", "dep2"]
        assert metadata.entry_point == "test_plugin:Plugin"
        assert metadata.plugin_type == "pip"
        assert metadata.enabled is True

    def test_metadata_to_dict(self) -> None:
        """Test converting metadata to dictionary."""
        metadata = PluginMetadata(
            name="test",
            version="1.0.0",
            description="Test",
        )

        data = metadata.to_dict()

        assert data["name"] == "test"
        assert data["version"] == "1.0.0"
        assert data["description"] == "Test"
        assert data["enabled"] is True


class TestPluginRegistry:
    """Test PluginRegistry class."""

    def test_register_plugin(self) -> None:
        """Test registering a plugin."""
        registry = PluginRegistry()
        metadata = PluginMetadata(
            name="test",
            version="1.0.0",
            description="Test",
        )
        plugin = LoadedPlugin(
            metadata=metadata,
            instance=TestPlugin(),
        )

        registry.register(plugin)

        assert registry.get("test") == plugin

    def test_list_plugins(self) -> None:
        """Test listing plugins."""
        registry = PluginRegistry()

        metadata1 = PluginMetadata(
            name="plugin1",
            version="1.0.0",
            description="Plugin 1",
        )
        plugin1 = LoadedPlugin(
            metadata=metadata1,
            instance=TestPlugin(),
        )

        metadata2 = PluginMetadata(
            name="plugin2",
            version="2.0.0",
            description="Plugin 2",
        )
        plugin2 = LoadedPlugin(
            metadata=metadata2,
            instance=TestPlugin(),
        )

        registry.register(plugin1)
        registry.register(plugin2)

        plugins = registry.list_plugins()
        assert len(plugins) == 2

    def test_list_enabled_plugins_only(self) -> None:
        """Test listing only enabled plugins."""
        registry = PluginRegistry()

        metadata1 = PluginMetadata(
            name="enabled",
            version="1.0.0",
            description="Enabled",
            enabled=True,
        )
        plugin1 = LoadedPlugin(
            metadata=metadata1,
            instance=TestPlugin(),
        )

        metadata2 = PluginMetadata(
            name="disabled",
            version="1.0.0",
            description="Disabled",
            enabled=False,
        )
        plugin2 = LoadedPlugin(
            metadata=metadata2,
            instance=TestPlugin(),
        )

        registry.register(plugin1)
        registry.register(plugin2)

        plugins = registry.list_plugins(enabled_only=True)
        assert len(plugins) == 1
        assert plugins[0].metadata.name == "enabled"

    def test_remove_plugin(self) -> None:
        """Test removing a plugin."""
        registry = PluginRegistry()
        metadata = PluginMetadata(
            name="test",
            version="1.0.0",
            description="Test",
        )
        plugin = LoadedPlugin(
            metadata=metadata,
            instance=TestPlugin(),
        )

        registry.register(plugin)
        assert registry.get("test") is not None

        result = registry.remove("test")
        assert result is True
        assert registry.get("test") is None

    def test_remove_nonexistent_plugin(self) -> None:
        """Test removing a nonexistent plugin."""
        registry = PluginRegistry()

        result = registry.remove("nonexistent")
        assert result is False

    def test_clear_registry(self) -> None:
        """Test clearing the registry."""
        registry = PluginRegistry()
        metadata = PluginMetadata(
            name="test",
            version="1.0.0",
            description="Test",
        )
        plugin = LoadedPlugin(
            metadata=metadata,
            instance=TestPlugin(),
        )

        registry.register(plugin)
        assert len(registry.list_plugins()) == 1

        registry.clear()
        assert len(registry.list_plugins()) == 0


class TestBasePlugin:
    """Test BasePlugin class."""

    def test_plugin_initialization(self) -> None:
        """Test plugin initialization."""
        plugin = TestPlugin()

        assert plugin.name == "test-plugin"
        assert plugin.version == "1.0.0"
        assert plugin.description == "Test plugin for testing"
        assert plugin.initialized is False

        result = plugin.initialize()

        assert result["success"] is True
        assert plugin.initialized is True

    def test_plugin_get_tools(self) -> None:
        """Test getting plugin tools."""
        plugin = TestPlugin()

        tools = plugin.get_tools()

        assert len(tools) == 1
        assert tools[0]["name"] == "test_tool"

    def test_plugin_cleanup(self) -> None:
        """Test plugin cleanup."""
        plugin = TestPlugin()
        plugin.initialize()

        assert plugin.initialized is True

        plugin.cleanup()

        assert plugin.initialized is False


class TestPluginDiscovery:
    """Test plugin discovery."""

    def test_discover_local_plugins(self, plugins_dir: Path) -> None:
        """Test discovering local plugins."""
        # Create plugin directory with metadata
        plugin1_dir = plugins_dir / "plugin1"
        plugin1_dir.mkdir()

        plugin1_json = plugin1_dir / "plugin.json"
        plugin1_json.write_text(
            json.dumps(
                {
                    "name": "plugin1",
                    "version": "1.0.0",
                    "description": "Plugin 1",
                    "author": "Test Author",
                    "entry_point": "plugin1:Plugin",
                }
            )
        )

        plugins = discover_local_plugins(plugins_dir)

        assert len(plugins) == 1
        assert plugins[0].name == "plugin1"
        assert plugins[0].version == "1.0.0"
        assert plugins[0].plugin_type == "local"

    def test_discover_local_plugins_empty_dir(self, temp_project: Path) -> None:
        """Test discovering plugins from empty directory."""
        empty_dir = temp_project / "empty"
        empty_dir.mkdir()

        plugins = discover_local_plugins(empty_dir)

        assert len(plugins) == 0

    def test_discover_local_plugins_nonexistent_dir(self, temp_project: Path) -> None:
        """Test discovering plugins from nonexistent directory."""
        nonexistent = temp_project / "nonexistent"

        plugins = discover_local_plugins(nonexistent)

        assert len(plugins) == 0

    def test_discover_local_plugins_invalid_json(self, plugins_dir: Path) -> None:
        """Test discovering plugins with invalid JSON."""
        plugin_dir = plugins_dir / "invalid"
        plugin_dir.mkdir()

        plugin_json = plugin_dir / "plugin.json"
        plugin_json.write_text("invalid json")

        plugins = discover_local_plugins(plugins_dir)

        assert len(plugins) == 0

    def test_discover_all_plugins(self, plugins_dir: Path) -> None:
        """Test discovering all plugins."""
        # Create local plugin
        plugin_dir = plugins_dir / "local-plugin"
        plugin_dir.mkdir()

        plugin_json = plugin_dir / "plugin.json"
        plugin_json.write_text(
            json.dumps(
                {
                    "name": "local-plugin",
                    "version": "1.0.0",
                    "description": "Local plugin",
                }
            )
        )

        plugins = discover_all_plugins(plugins_dir.parent.parent)

        # Should find at least the local plugin
        local_plugin = next((p for p in plugins if p.name == "local-plugin"), None)
        assert local_plugin is not None
        assert local_plugin.plugin_type == "local"


class TestPluginLoading:
    """Test plugin loading."""

    def test_initialize_plugin(self) -> None:
        """Test initializing a plugin."""
        metadata = PluginMetadata(
            name="test",
            version="1.0.0",
            description="Test",
        )
        plugin = LoadedPlugin(
            metadata=metadata,
            instance=TestPlugin(),
        )

        assert plugin.initialized is False

        result = initialize_plugin(plugin)

        assert result["success"] is True
        assert plugin.initialized is True

    def test_initialize_already_initialized_plugin(self) -> None:
        """Test initializing an already initialized plugin."""
        metadata = PluginMetadata(
            name="test",
            version="1.0.0",
            description="Test",
        )
        plugin = LoadedPlugin(
            metadata=metadata,
            instance=TestPlugin(),
            initialized=True,
        )

        result = initialize_plugin(plugin)

        assert result["success"] is True
        assert "already initialized" in result["message"].lower()


class TestPluginTools:
    """Test plugin tools for agent use."""

    def test_list_plugins_tool(self, plugins_dir: Path) -> None:
        """Test listing plugins."""
        # Create a local plugin
        plugin_dir = plugins_dir / "test-plugin"
        plugin_dir.mkdir()

        plugin_json = plugin_dir / "plugin.json"
        plugin_json.write_text(
            json.dumps(
                {
                    "name": "test-plugin",
                    "version": "1.0.0",
                    "description": "Test plugin",
                }
            )
        )

        result = list_plugins(project_root=str(plugins_dir.parent.parent))

        assert result["success"] is True
        assert result["count"] >= 1

    def test_enable_plugin(self) -> None:
        """Test enabling a plugin."""
        registry = get_plugin_registry()
        metadata = PluginMetadata(
            name="test-enable",
            version="1.0.0",
            description="Test",
            enabled=False,
        )
        plugin = LoadedPlugin(
            metadata=metadata,
            instance=TestPlugin(),
        )

        registry.register(plugin)

        result = enable_plugin("test-enable")

        assert result["success"] is True
        assert plugin.metadata.enabled is True

        # Cleanup
        registry.remove("test-enable")

    def test_disable_plugin(self) -> None:
        """Test disabling a plugin."""
        registry = get_plugin_registry()
        metadata = PluginMetadata(
            name="test-disable",
            version="1.0.0",
            description="Test",
            enabled=True,
        )
        plugin = LoadedPlugin(
            metadata=metadata,
            instance=TestPlugin(),
        )

        registry.register(plugin)

        result = disable_plugin("test-disable")

        assert result["success"] is True
        assert plugin.metadata.enabled is False

        # Cleanup
        registry.remove("test-disable")

    def test_get_plugin_tools_tool(self) -> None:
        """Test getting plugin tools."""
        registry = get_plugin_registry()
        metadata = PluginMetadata(
            name="test-tools",
            version="1.0.0",
            description="Test",
        )
        plugin_instance = TestPlugin()
        plugin_instance.initialize()

        plugin = LoadedPlugin(
            metadata=metadata,
            instance=plugin_instance,
            initialized=True,
        )

        registry.register(plugin)

        result = get_plugin_tools("test-tools")

        assert result["success"] is True
        assert result["count"] == 1
        assert result["tools"][0]["name"] == "test_tool"

        # Cleanup
        registry.remove("test-tools")

    def test_get_plugin_tools_not_found(self) -> None:
        """Test getting tools from nonexistent plugin."""
        result = get_plugin_tools("nonexistent")

        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_get_plugin_tools_not_initialized(self) -> None:
        """Test getting tools from uninitialized plugin."""
        registry = get_plugin_registry()
        metadata = PluginMetadata(
            name="test-uninit",
            version="1.0.0",
            description="Test",
        )
        plugin = LoadedPlugin(
            metadata=metadata,
            instance=TestPlugin(),
            initialized=False,
        )

        registry.register(plugin)

        result = get_plugin_tools("test-uninit")

        assert "error" in result
        assert "not initialized" in result["error"].lower()

        # Cleanup
        registry.remove("test-uninit")

    def test_get_all_plugin_tools(self) -> None:
        """Test getting all plugin tool definitions."""
        tools = get_all_plugin_tools()

        assert len(tools) == 5
        assert any(t["name"] == "list_plugins" for t in tools)
        assert any(t["name"] == "load_and_initialize_plugin" for t in tools)
        assert any(t["name"] == "enable_plugin" for t in tools)
        assert any(t["name"] == "disable_plugin" for t in tools)
        assert any(t["name"] == "get_plugin_tools" for t in tools)


class TestPluginHelpers:
    """Test plugin helper functions."""

    def test_get_plugin_registry(self) -> None:
        """Test getting the global plugin registry."""
        registry = get_plugin_registry()

        assert isinstance(registry, PluginRegistry)


class TestPluginIntegration:
    """Integration tests for plugin system."""

    def test_complete_plugin_workflow(self, plugins_dir: Path) -> None:
        """Test complete workflow from discovery to tool usage."""
        # Create plugin metadata
        plugin_dir = plugins_dir / "workflow-plugin"
        plugin_dir.mkdir()

        plugin_json = plugin_dir / "plugin.json"
        plugin_json.write_text(
            json.dumps(
                {
                    "name": "workflow-plugin",
                    "version": "1.0.0",
                    "description": "Workflow test plugin",
                    "author": "Test",
                }
            )
        )

        # Discover plugins
        plugins = discover_all_plugins(plugins_dir.parent.parent)

        workflow_plugin_meta = next((p for p in plugins if p.name == "workflow-plugin"), None)

        assert workflow_plugin_meta is not None
        assert workflow_plugin_meta.description == "Workflow test plugin"
        assert workflow_plugin_meta.plugin_type == "local"
