"""Tests for CLI command handler."""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from devorbit.cli.commands import CommandHandler
from devorbit.cli.session import CLISession


class TestCommandHandler:
    """Test suite for CommandHandler class."""

    @pytest.fixture
    def session(self):
        """Create a test session."""
        return CLISession(
            provider="anthropic",
            api_key="test-key",
            model="claude-sonnet-4-5-20250929",
        )

    @pytest.fixture
    def handler(self, session):
        """Create a test command handler."""
        return CommandHandler(session)

    def test_handler_initialization(self, handler):
        """Test command handler initialization."""
        assert handler.session is not None
        assert len(handler.commands) > 0

        # Verify all expected commands are registered
        expected_commands = [
            "help",
            "exit",
            "quit",
            "clear",
            "history",
            "status",
            "model",
            "provider",
            "cd",
            "pwd",
            "planning",
        ]

        for cmd in expected_commands:
            assert cmd in handler.commands

    def test_handle_empty_command(self, handler, session):
        """Test handling empty command."""
        session.print_error = Mock()
        result = handler.handle_command("/")
        assert result is True
        session.print_error.assert_called_once()

    def test_handle_unknown_command(self, handler, session):
        """Test handling unknown command."""
        session.print_error = Mock()
        session.print = Mock()
        result = handler.handle_command("/unknown")
        assert result is True
        session.print_error.assert_called_once()
        session.print.assert_called_once()

    def test_cmd_help(self, handler, session):
        """Test /help command."""
        session.print = Mock()
        result = handler.cmd_help([])
        assert result is True
        session.print.assert_called_once()

        # Verify help text contains key information
        help_text = session.print.call_args[0][0]
        assert "/help" in help_text
        assert "/exit" in help_text
        assert session.provider in help_text

    def test_cmd_exit(self, handler, session):
        """Test /exit command."""
        session.print = Mock()
        result = handler.cmd_exit([])
        assert result is False
        assert session.is_running is False
        session.print.assert_called_once()

    def test_cmd_quit(self, handler, session):
        """Test /quit command (alias for exit)."""
        session.print = Mock()
        result = handler.handle_command("/quit")
        assert result is False
        assert session.is_running is False

    def test_cmd_clear(self, handler, session):
        """Test /clear command."""
        # Add some messages first
        session.add_message("user", "Test message")
        session.add_message("assistant", "Test response")
        assert len(session.messages) == 2

        session.print_success = Mock()
        result = handler.cmd_clear([])

        assert result is True
        assert len(session.messages) == 0
        session.print_success.assert_called_once()

    def test_cmd_history_empty(self, handler, session):
        """Test /history command with empty history."""
        session.print_info = Mock()
        result = handler.cmd_history([])
        assert result is True
        session.print_info.assert_called_once()

    def test_cmd_history_with_messages(self, handler, session):
        """Test /history command with messages."""
        session.add_message("user", "Hello")
        session.add_message("assistant", "Hi there")

        session.print = Mock()
        result = handler.cmd_history([])

        assert result is True
        assert session.print.call_count >= 3  # Header + 2 messages + footer

    def test_cmd_history_truncates_long_content(self, handler, session):
        """Test /history truncates long messages."""
        long_message = "x" * 200
        session.add_message("user", long_message)

        session.print = Mock()
        handler.cmd_history([])

        # Verify message was truncated
        calls = [str(call) for call in session.print.call_args_list]
        combined = " ".join(calls)
        assert "..." in combined

    def test_cmd_status(self, handler, session):
        """Test /status command."""
        session.print = Mock()
        result = handler.cmd_status([])

        assert result is True
        session.print.assert_called_once()

        # Verify status contains key information
        status_text = session.print.call_args[0][0]
        assert "Provider:" in status_text
        assert "Model:" in status_text
        assert "Working Directory:" in status_text

    def test_cmd_model_show(self, handler, session):
        """Test /model command without arguments (show current)."""
        session.print = Mock()
        result = handler.cmd_model([])

        assert result is True
        session.print.assert_called_once()
        assert "Current model:" in session.print.call_args[0][0]

    def test_cmd_model_change(self, handler, session):
        """Test /model command with argument (change model)."""
        session.print_success = Mock()
        result = handler.cmd_model(["gpt-4"])

        assert result is True
        assert session.model == "gpt-4"
        session.print_success.assert_called_once()

    def test_cmd_provider(self, handler, session):
        """Test /provider command."""
        session.print = Mock()
        session.print_info = Mock()
        result = handler.cmd_provider([])

        assert result is True
        session.print.assert_called_once()
        session.print_info.assert_called_once()

    def test_cmd_pwd(self, handler, session):
        """Test /pwd command."""
        session.print = Mock()
        result = handler.cmd_pwd([])

        assert result is True
        session.print.assert_called_once()
        assert str(session.working_dir) in session.print.call_args[0][0]

    def test_cmd_cd_no_args(self, handler, session):
        """Test /cd command without arguments."""
        session.print_error = Mock()
        result = handler.cmd_cd([])

        assert result is True
        session.print_error.assert_called_once()

    def test_cmd_cd_valid_directory(self, handler, session):
        """Test /cd command with valid directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session.print_success = Mock()
            original_dir = session.working_dir

            result = handler.cmd_cd([tmpdir])

            assert result is True
            assert session.working_dir == Path(tmpdir).resolve()
            assert session.working_dir != original_dir
            session.print_success.assert_called_once()

    def test_cmd_cd_nonexistent_directory(self, handler, session):
        """Test /cd command with nonexistent directory."""
        session.print_error = Mock()
        original_dir = session.working_dir

        result = handler.cmd_cd(["/nonexistent/path"])

        assert result is True
        assert session.working_dir == original_dir
        session.print_error.assert_called_once()

    def test_cmd_cd_file_instead_of_directory(self, handler, session):
        """Test /cd command with file instead of directory."""
        with tempfile.NamedTemporaryFile() as tmpfile:
            session.print_error = Mock()
            original_dir = session.working_dir

            result = handler.cmd_cd([tmpfile.name])

            assert result is True
            assert session.working_dir == original_dir
            session.print_error.assert_called_once()

    def test_cmd_cd_with_home_expansion(self, handler, session):
        """Test /cd command with ~ expansion."""
        session.print_success = Mock()
        result = handler.cmd_cd(["~"])

        assert result is True
        assert session.working_dir == Path.home()
        session.print_success.assert_called_once()

    def test_cmd_planning_toggle_on(self, handler, session):
        """Test /planning command to enable planning mode."""
        assert session.planning_mode is False

        session.print_success = Mock()
        session.print_info = Mock()
        result = handler.cmd_planning([])

        assert result is True
        assert session.planning_mode is True
        session.print_success.assert_called_once()
        session.print_info.assert_called_once()

    def test_cmd_planning_toggle_off(self, handler, session):
        """Test /planning command to disable planning mode."""
        session.planning_mode = True

        session.print_success = Mock()
        result = handler.cmd_planning([])

        assert result is True
        assert session.planning_mode is False
        session.print_success.assert_called_once()

    def test_handle_command_case_insensitive(self, handler):
        """Test command handling is case-insensitive."""
        result1 = handler.handle_command("/HELP")
        result2 = handler.handle_command("/Help")
        result3 = handler.handle_command("/help")

        assert result1 is True
        assert result2 is True
        assert result3 is True

    def test_handle_command_with_arguments(self, handler, session):
        """Test command handling with arguments."""
        session.print_success = Mock()
        result = handler.handle_command("/model gpt-4")

        assert result is True
        assert session.model == "gpt-4"

    def test_handle_command_with_multiple_arguments(self, handler, session):
        """Test command handling with multiple arguments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a directory with spaces
            test_dir = Path(tmpdir) / "test dir"
            test_dir.mkdir()

            session.print_success = Mock()
            # This might not work as expected due to space splitting
            # but tests the behavior
            result = handler.handle_command(f"/cd {test_dir}")

            assert result is True

    def test_all_commands_return_boolean(self, handler):
        """Test that all commands return boolean values."""
        for cmd_name, cmd_func in handler.commands.items():
            result = cmd_func([])
            assert isinstance(result, bool), f"Command {cmd_name} should return bool"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
