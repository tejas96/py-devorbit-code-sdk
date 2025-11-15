"""Tests for CLI session management."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from devorbit.cli.session import CLISession


class TestCLISession:
    """Test suite for CLISession class."""

    def test_session_initialization(self):
        """Test basic session initialization."""
        session = CLISession(
            provider="anthropic",
            api_key="test-key",
            model="claude-sonnet-4-5-20250929",
        )

        assert session.provider == "anthropic"
        assert session.api_key == "test-key"
        assert session.model == "claude-sonnet-4-5-20250929"
        assert session.is_running is True
        assert session.planning_mode is False
        assert len(session.messages) == 0

    def test_session_with_working_dir(self):
        """Test session with custom working directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session = CLISession(
                provider="anthropic",
                api_key="test-key",
                working_dir=Path(tmpdir),
            )

            assert session.working_dir == Path(tmpdir)

    def test_session_default_working_dir(self):
        """Test session uses current directory by default."""
        session = CLISession(
            provider="anthropic",
            api_key="test-key",
        )

        assert session.working_dir == Path.cwd()

    def test_add_message(self):
        """Test adding messages to conversation history."""
        session = CLISession(
            provider="anthropic",
            api_key="test-key",
        )

        session.add_message("user", "Hello!")
        assert len(session.messages) == 1
        assert session.messages[0]["role"] == "user"
        assert session.messages[0]["content"] == "Hello!"

        session.add_message("assistant", "Hi there!")
        assert len(session.messages) == 2
        assert session.messages[1]["role"] == "assistant"
        assert session.messages[1]["content"] == "Hi there!"

    def test_clear_history(self):
        """Test clearing conversation history."""
        session = CLISession(
            provider="anthropic",
            api_key="test-key",
        )

        session.add_message("user", "Hello!")
        session.add_message("assistant", "Hi!")
        assert len(session.messages) == 2

        session.clear_history()
        assert len(session.messages) == 0

    def test_client_initialization(self):
        """Test that Devorbit client is properly initialized."""
        session = CLISession(
            provider="anthropic",
            api_key="test-key",
        )

        assert session.client is not None
        assert hasattr(session.client, "messages")
        assert hasattr(session.client, "beta")

    def test_session_state_flags(self):
        """Test session state management."""
        session = CLISession(
            provider="anthropic",
            api_key="test-key",
        )

        # Default state
        assert session.is_running is True
        assert session.planning_mode is False

        # Modify state
        session.is_running = False
        assert session.is_running is False

        session.planning_mode = True
        assert session.planning_mode is True

    def test_no_color_mode(self):
        """Test session with no_color flag."""
        session = CLISession(
            provider="anthropic",
            api_key="test-key",
            no_color=True,
        )

        assert session.no_color is True

    def test_debug_mode(self):
        """Test session with debug flag."""
        session = CLISession(
            provider="anthropic",
            api_key="test-key",
            debug=True,
        )

        assert session.debug is True

    @patch("devorbit.cli.session.HAS_RICH", False)
    def test_print_without_rich(self):
        """Test print methods without rich library."""
        session = CLISession(
            provider="anthropic",
            api_key="test-key",
        )

        # Should not raise any errors
        session.print("Test message")
        session.print_error("Test error")
        session.print_success("Test success")
        session.print_info("Test info")

    @patch("devorbit.cli.session.HAS_RICH", True)
    def test_print_with_rich(self):
        """Test print methods with rich library."""
        session = CLISession(
            provider="anthropic",
            api_key="test-key",
        )

        # Mock console
        session.console = Mock()

        session.print("Test message")
        session.console.print.assert_called_with("Test message")

        session.print_error("Test error")
        session.console.print.assert_called_with("[bold red]Error:[/bold red] Test error")

        session.print_success("Test success")
        session.console.print.assert_called_with("[bold green]✓[/bold green] Test success")

        session.print_info("Test info")
        session.console.print.assert_called_with("[bold cyan]i[/bold cyan] Test info")

    def test_display_welcome_without_rich(self):
        """Test welcome banner without rich library."""
        with patch("devorbit.cli.session.HAS_RICH", False):
            session = CLISession(
                provider="anthropic",
                api_key="test-key",
                model="claude-sonnet-4-5-20250929",
            )

            # Should not raise any errors
            session.display_welcome()

    @patch("devorbit.cli.session.HAS_RICH", True)
    def test_display_welcome_with_rich(self):
        """Test welcome banner with rich library."""
        session = CLISession(
            provider="anthropic",
            api_key="test-key",
            model="claude-sonnet-4-5-20250929",
        )

        # Mock console
        session.console = Mock()

        session.display_welcome()
        assert session.console.print.called

    def test_session_with_different_providers(self):
        """Test session initialization with different providers."""
        providers = ["anthropic", "openai", "gemini", "mistral", "codellama"]

        for provider in providers:
            session = CLISession(
                provider=provider,
                api_key="test-key",
            )

            assert session.provider == provider
            assert session.client is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
