"""Tests for slash command system."""

from pathlib import Path

import pytest

from devorbit._commands import (
    Command,
    CommandRegistry,
    execute_command,
    list_slash_commands,
    load_commands,
    load_commands_from_dir,
    parse_command_file,
    parse_command_invocation,
    register_command,
    run_slash_command,
)


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    """Create a temporary project directory."""
    return tmp_path


@pytest.fixture
def commands_dir(temp_project: Path) -> Path:
    """Create commands directory."""
    cmd_dir = temp_project / ".devorbit" / "commands"
    cmd_dir.mkdir(parents=True)
    return cmd_dir


class TestCommand:
    """Test Command class."""

    def test_command_creation(self) -> None:
        """Test creating a command."""
        cmd = Command(
            name="review",
            description="Review code",
            content="Please review the code",
            aliases=["check"],
        )

        assert cmd.name == "review"
        assert cmd.description == "Review code"
        assert cmd.content == "Please review the code"
        assert cmd.aliases == ["check"]

    def test_command_matches(self) -> None:
        """Test command matching."""
        cmd = Command(
            name="review",
            description="Review code",
            content="Content",
            aliases=["check", "validate"],
        )

        assert cmd.matches("review") is True
        assert cmd.matches("check") is True
        assert cmd.matches("validate") is True
        assert cmd.matches("other") is False


class TestCommandRegistry:
    """Test CommandRegistry class."""

    def test_register_command(self) -> None:
        """Test registering a command."""
        registry = CommandRegistry()
        cmd = Command(name="test", description="Test", content="Content")

        registry.register(cmd)

        assert registry.get("test") == cmd

    def test_register_with_aliases(self) -> None:
        """Test registering command with aliases."""
        registry = CommandRegistry()
        cmd = Command(
            name="review",
            description="Review",
            content="Content",
            aliases=["check"],
        )

        registry.register(cmd)

        assert registry.get("review") == cmd
        assert registry.get("check") == cmd

    def test_list_commands(self) -> None:
        """Test listing commands."""
        registry = CommandRegistry()
        cmd1 = Command(name="cmd1", description="Cmd 1", content="Content 1")
        cmd2 = Command(
            name="cmd2",
            description="Cmd 2",
            content="Content 2",
            aliases=["c2"],
        )

        registry.register(cmd1)
        registry.register(cmd2)

        commands = registry.list_commands()

        assert len(commands) == 2
        assert any(c.name == "cmd1" for c in commands)
        assert any(c.name == "cmd2" for c in commands)

    def test_remove_command(self) -> None:
        """Test removing a command."""
        registry = CommandRegistry()
        cmd = Command(
            name="test",
            description="Test",
            content="Content",
            aliases=["t"],
        )

        registry.register(cmd)
        assert registry.get("test") is not None

        removed = registry.remove("test")

        assert removed is True
        assert registry.get("test") is None
        assert registry.get("t") is None  # Alias should also be removed

    def test_clear_registry(self) -> None:
        """Test clearing registry."""
        registry = CommandRegistry()
        cmd = Command(name="test", description="Test", content="Content")

        registry.register(cmd)
        assert len(registry.list_commands()) == 1

        registry.clear()

        assert len(registry.list_commands()) == 0


class TestCommandParsing:
    """Test command file parsing."""

    def test_parse_frontmatter_format(self, temp_project: Path) -> None:
        """Test parsing command with frontmatter."""
        cmd_file = temp_project / "review.md"
        cmd_file.write_text(
            """---
name: review
description: Review code changes
aliases: [check, validate]
---
Please review the following code changes and provide feedback.
"""
        )

        cmd = parse_command_file(cmd_file)

        assert cmd is not None
        assert cmd.name == "review"
        assert cmd.description == "Review code changes"
        assert cmd.aliases == ["check", "validate"]
        assert "review the following code" in cmd.content

    def test_parse_simple_markdown(self, temp_project: Path) -> None:
        """Test parsing simple markdown command."""
        cmd_file = temp_project / "test.md"
        cmd_file.write_text(
            """# Test Command
Run tests for the project

Execute all unit tests and report results.
"""
        )

        cmd = parse_command_file(cmd_file)

        assert cmd is not None
        assert cmd.name == "Test Command"
        assert cmd.description == "Run tests for the project"
        assert "Execute all unit tests" in cmd.content

    def test_parse_filename_as_name(self, temp_project: Path) -> None:
        """Test using filename as command name."""
        cmd_file = temp_project / "mycommand.md"
        cmd_file.write_text("This is the command content")

        cmd = parse_command_file(cmd_file)

        assert cmd is not None
        assert cmd.name == "mycommand"
        assert cmd.content == "This is the command content"


class TestCommandLoading:
    """Test loading commands from directories."""

    def test_load_commands_from_dir(self, commands_dir: Path) -> None:
        """Test loading commands from directory."""
        (commands_dir / "cmd1.md").write_text("# Command 1\nContent 1")
        (commands_dir / "cmd2.md").write_text("# Command 2\nContent 2")

        commands = load_commands_from_dir(commands_dir)

        assert len(commands) == 2
        assert any(c.name == "Command 1" for c in commands)
        assert any(c.name == "Command 2" for c in commands)

    def test_load_commands_empty_dir(self, commands_dir: Path) -> None:
        """Test loading from empty directory."""
        commands = load_commands_from_dir(commands_dir)

        assert len(commands) == 0

    def test_load_commands_nonexistent_dir(self, temp_project: Path) -> None:
        """Test loading from non-existent directory."""
        commands = load_commands_from_dir(temp_project / "nonexistent")

        assert len(commands) == 0

    def test_load_commands_multiple_locations(
        self, temp_project: Path
    ) -> None:
        """Test loading from multiple standard locations."""
        # Create commands in different locations
        devorbit_dir = temp_project / ".devorbit" / "commands"
        claude_dir = temp_project / ".claude" / "commands"

        devorbit_dir.mkdir(parents=True)
        claude_dir.mkdir(parents=True)

        (devorbit_dir / "cmd1.md").write_text("# Command 1\nContent")
        (claude_dir / "cmd2.md").write_text("# Command 2\nContent")

        commands = load_commands(temp_project)

        assert len(commands) >= 2


class TestCommandInvocation:
    """Test command invocation parsing."""

    def test_parse_command_invocation(self) -> None:
        """Test parsing command invocation."""
        result = parse_command_invocation("/review src/main.py")

        assert result is not None
        command, args = result
        assert command == "review"
        assert args == "src/main.py"

    def test_parse_command_no_args(self) -> None:
        """Test parsing command without arguments."""
        result = parse_command_invocation("/test")

        assert result is not None
        command, args = result
        assert command == "test"
        assert args == ""

    def test_parse_non_command(self) -> None:
        """Test parsing non-command text."""
        result = parse_command_invocation("not a command")

        assert result is None


class TestCommandExecution:
    """Test command execution."""

    def test_execute_command(self) -> None:
        """Test executing a command."""
        registry = CommandRegistry()
        cmd = Command(
            name="greet",
            description="Greet user",
            content="Hello, {args}!",
        )
        registry.register(cmd)

        result = execute_command("greet", "World", registry)

        assert result["success"] is True
        assert result["command"] == "greet"
        assert "Hello, World!" in result["content"]

    def test_execute_command_not_found(self) -> None:
        """Test executing non-existent command."""
        registry = CommandRegistry()

        result = execute_command("nonexistent", "", registry)

        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_execute_command_no_placeholder(self) -> None:
        """Test executing command without args placeholder."""
        registry = CommandRegistry()
        cmd = Command(
            name="test",
            description="Test",
            content="Run tests",
        )
        registry.register(cmd)

        result = execute_command("test", "extra args", registry)

        assert result["success"] is True
        # Args should be appended
        assert "Run tests" in result["content"]
        assert "extra args" in result["content"]


class TestCommandTools:
    """Test command tools for agent use."""

    def test_list_slash_commands_tool(self, commands_dir: Path) -> None:
        """Test list_slash_commands tool."""
        (commands_dir / "cmd1.md").write_text("# Cmd1\nDescription\nContent")

        result = list_slash_commands(str(commands_dir.parent.parent))

        assert result["success"] is True
        assert result["count"] > 0

    def test_run_slash_command_tool(self, commands_dir: Path) -> None:
        """Test run_slash_command tool."""
        (commands_dir / "test.md").write_text(
            """---
name: test
description: Run tests
---
Execute all tests
"""
        )

        result = run_slash_command(
            "test",
            "src/",
            str(commands_dir.parent.parent),
        )

        assert result["success"] is True
        assert result["command"] == "test"

    def test_register_command_function(self) -> None:
        """Test programmatic command registration."""
        register_command(
            name="custom",
            content="Custom command content",
            description="A custom command",
            aliases=["c"],
        )

        # Command should be registered in global registry
        result = run_slash_command("custom", "")

        assert result["success"] is True
        assert result["command"] == "custom"
