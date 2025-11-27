"""Tests for configuration system."""

import json
from pathlib import Path

import pytest

from devorbit.core.config import (
    DevorbitConfig,
    load_config,
    load_devorbit_json,
    load_env_config,
    load_project_md,
    read_config,
    save_config,
    update_config,
)


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    """Create a temporary project directory."""
    return tmp_path


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clean environment variables."""
    for key in [
        "DEVORBIT_MODEL",
        "DEVORBIT_PROVIDER",
        "DEVORBIT_MAX_TOKENS",
        "DEVORBIT_TEMPERATURE",
        "DEVORBIT_HOOKS_ENABLED",
    ]:
        monkeypatch.delenv(key, raising=False)


class TestDevorbitConfig:
    """Test DevorbitConfig class."""

    def test_default_config(self) -> None:
        """Test default configuration."""
        config = DevorbitConfig()

        assert config.project_context == ""
        assert config.model is None
        assert config.provider is None
        assert config.max_tokens == 4096
        assert config.temperature == 1.0
        assert config.hooks_enabled is True

    def test_config_merge(self) -> None:
        """Test merging configurations."""
        config1 = DevorbitConfig(model="gpt-4", max_tokens=2000)
        config2 = DevorbitConfig(provider="openai", max_tokens=4096)

        merged = config1.merge(config2)

        assert merged.model == "gpt-4"  # From config1
        assert merged.provider == "openai"  # From config2
        assert merged.max_tokens == 2000  # config1 wins (non-default)

    def test_to_dict(self) -> None:
        """Test converting to dictionary."""
        config = DevorbitConfig(model="claude-3", provider="anthropic")
        data = config.to_dict()

        assert data["model"] == "claude-3"
        assert data["provider"] == "anthropic"
        assert "max_tokens" in data

    def test_from_dict(self) -> None:
        """Test creating from dictionary."""
        data = {
            "model": "gpt-4",
            "provider": "openai",
            "max_tokens": 2000,
            "temperature": 0.7,
        }

        config = DevorbitConfig.from_dict(data)

        assert config.model == "gpt-4"
        assert config.provider == "openai"
        assert config.max_tokens == 2000
        assert config.temperature == 0.7


class TestProjectMdLoader:
    """Test PROJECT.md loading."""

    def test_load_project_md(self, temp_project: Path) -> None:
        """Test loading PROJECT.md."""
        project_md = temp_project / "PROJECT.md"
        project_md.write_text("# My Project\n\nThis is the project context.")

        content = load_project_md(temp_project)

        assert "My Project" in content
        assert "project context" in content

    def test_load_claude_md(self, temp_project: Path) -> None:
        """Test loading CLAUDE.md as fallback."""
        claude_md = temp_project / "CLAUDE.md"
        claude_md.write_text("# Claude Context\n\nContext for Claude.")

        content = load_project_md(temp_project)

        assert "Claude Context" in content

    def test_project_md_priority(self, temp_project: Path) -> None:
        """Test PROJECT.md takes priority over CLAUDE.md."""
        (temp_project / "PROJECT.md").write_text("Project content")
        (temp_project / "CLAUDE.md").write_text("Claude content")

        content = load_project_md(temp_project)

        assert "Project content" in content
        assert "Claude content" not in content

    def test_no_project_file(self, temp_project: Path) -> None:
        """Test when no project file exists."""
        content = load_project_md(temp_project)

        assert content == ""


class TestDevorbitJsonLoader:
    """Test .devorbit.json loading."""

    def test_load_devorbit_json(self, temp_project: Path) -> None:
        """Test loading .devorbit.json."""
        config_data = {
            "model": "gpt-4",
            "provider": "openai",
            "max_tokens": 2000,
        }

        (temp_project / ".devorbit.json").write_text(json.dumps(config_data))

        loaded = load_devorbit_json(temp_project)

        assert loaded["model"] == "gpt-4"
        assert loaded["provider"] == "openai"
        assert loaded["max_tokens"] == 2000

    def test_no_config_file(self, temp_project: Path) -> None:
        """Test when no config file exists."""
        loaded = load_devorbit_json(temp_project)

        assert loaded == {}

    def test_invalid_json(self, temp_project: Path) -> None:
        """Test handling invalid JSON."""
        (temp_project / ".devorbit.json").write_text("invalid json")

        loaded = load_devorbit_json(temp_project)

        assert loaded == {}


class TestEnvLoader:
    """Test environment variable loading."""

    def test_load_env_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test loading from environment."""
        monkeypatch.setenv("DEVORBIT_MODEL", "gpt-4")
        monkeypatch.setenv("DEVORBIT_PROVIDER", "openai")
        monkeypatch.setenv("DEVORBIT_MAX_TOKENS", "2000")
        monkeypatch.setenv("DEVORBIT_TEMPERATURE", "0.7")

        config = load_env_config()

        assert config["model"] == "gpt-4"
        assert config["provider"] == "openai"
        assert config["max_tokens"] == 2000
        assert config["temperature"] == 0.7

    def test_hooks_enabled_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test DEVORBIT_HOOKS_ENABLED."""
        monkeypatch.setenv("DEVORBIT_HOOKS_ENABLED", "false")

        config = load_env_config()

        assert config["hooks_enabled"] is False

    def test_invalid_env_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test handling invalid environment values."""
        monkeypatch.setenv("DEVORBIT_MAX_TOKENS", "invalid")
        monkeypatch.setenv("DEVORBIT_TEMPERATURE", "invalid")

        config = load_env_config()

        assert "max_tokens" not in config
        assert "temperature" not in config


class TestConfigLoading:
    """Test complete configuration loading."""

    def test_load_complete_config(self, temp_project: Path, clean_env: None) -> None:
        """Test loading from all sources."""
        # Create PROJECT.md
        (temp_project / "PROJECT.md").write_text("Project context")

        # Create .devorbit.json
        (temp_project / ".devorbit.json").write_text(
            json.dumps({"model": "gpt-4", "max_tokens": 2000})
        )

        config = load_config(temp_project)

        assert config.project_context == "Project context"
        assert config.model == "gpt-4"
        assert config.max_tokens == 2000

    def test_env_priority(self, temp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test environment variables override config file."""
        (temp_project / ".devorbit.json").write_text(json.dumps({"model": "gpt-4"}))

        monkeypatch.setenv("DEVORBIT_MODEL", "claude-3")

        config = load_config(temp_project)

        assert config.model == "claude-3"  # env wins


class TestConfigSaving:
    """Test saving configuration."""

    def test_save_config(self, temp_project: Path) -> None:
        """Test saving configuration."""
        config = DevorbitConfig(model="gpt-4", provider="openai", max_tokens=2000)

        result = save_config(config, temp_project)

        assert result["success"] is True

        # Verify file was created
        config_file = temp_project / ".devorbit.json"
        assert config_file.exists()

        # Verify content
        with config_file.open() as f:
            data = json.load(f)

        assert data["model"] == "gpt-4"
        assert data["provider"] == "openai"
        assert "project_context" not in data  # Should not save this


class TestConfigTools:
    """Test configuration tools for agent use."""

    def test_read_config_tool(self, temp_project: Path) -> None:
        """Test read_config tool."""
        (temp_project / ".devorbit.json").write_text(json.dumps({"model": "gpt-4"}))

        result = read_config(str(temp_project))

        assert result["success"] is True
        assert result["config"]["model"] == "gpt-4"

    def test_update_config_tool(self, temp_project: Path) -> None:
        """Test update_config tool."""
        result = update_config(
            project_root=str(temp_project),
            model="gpt-4",
            provider="openai",
            max_tokens=2000,
        )

        assert result["success"] is True
        assert result["config"]["model"] == "gpt-4"
        assert result["config"]["provider"] == "openai"

        # Verify file was created
        assert (temp_project / ".devorbit.json").exists()
