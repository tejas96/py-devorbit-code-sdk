"""Tests for CLI main entry point."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from devorbit.cli.main import main


class TestCLIMain:
    """Test suite for CLI main entry point."""

    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def mock_repl(self):
        """Mock REPL class."""
        with patch("devorbit.cli.main.EnhancedREPL") as mock:
            yield mock

    @pytest.fixture
    def mock_session(self):
        """Mock CLISession class."""
        with patch("devorbit.cli.main.CLISession") as mock:
            yield mock

    def test_cli_requires_api_key(self, runner):
        """Test CLI exits when no API key is provided."""
        result = runner.invoke(main, [])
        assert result.exit_code == 1
        assert "No API key provided" in result.output

    def test_cli_with_api_key_env_var(self, runner, mock_repl, mock_session):
        """Test CLI with API key from environment variable."""
        mock_repl_instance = Mock()
        mock_repl.return_value = mock_repl_instance

        result = runner.invoke(main, [], env={"ANTHROPIC_API_KEY": "test-key"})

        assert result.exit_code == 0
        mock_session.assert_called_once()
        mock_repl.assert_called_once()
        mock_repl_instance.run.assert_called_once()

    def test_cli_with_api_key_option(self, runner, mock_repl, mock_session):
        """Test CLI with API key from command line option."""
        mock_repl_instance = Mock()
        mock_repl.return_value = mock_repl_instance

        result = runner.invoke(main, ["--api-key", "test-key"])

        assert result.exit_code == 0
        mock_session.assert_called_once()
        mock_repl_instance.run.assert_called_once()

    def test_cli_provider_option(self, runner, mock_repl, mock_session):
        """Test CLI with different provider options."""
        providers = ["anthropic", "openai", "gemini", "mistral", "codellama"]

        mock_repl_instance = Mock()
        mock_repl.return_value = mock_repl_instance

        for provider in providers:
            result = runner.invoke(main, ["--provider", provider, "--api-key", "test-key"])

            assert result.exit_code == 0
            # Check that session was called with correct provider
            call_kwargs = mock_session.call_args[1]
            assert call_kwargs["provider"] == provider

    def test_cli_invalid_provider(self, runner):
        """Test CLI with invalid provider option."""
        result = runner.invoke(main, ["--provider", "invalid", "--api-key", "test-key"])
        assert result.exit_code != 0
        assert "Invalid value" in result.output

    def test_cli_model_option(self, runner, mock_repl, mock_session):
        """Test CLI with model option."""
        mock_repl_instance = Mock()
        mock_repl.return_value = mock_repl_instance

        result = runner.invoke(
            main,
            ["--api-key", "test-key", "--model", "gpt-4"],
        )

        assert result.exit_code == 0
        call_kwargs = mock_session.call_args[1]
        assert call_kwargs["model"] == "gpt-4"

    def test_cli_working_dir_option(self, runner, mock_repl, mock_session):
        """Test CLI with working directory option."""
        mock_repl_instance = Mock()
        mock_repl.return_value = mock_repl_instance

        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(
                main,
                ["--api-key", "test-key", "--working-dir", tmpdir],
            )

            assert result.exit_code == 0
            call_kwargs = mock_session.call_args[1]
            assert call_kwargs["working_dir"] == Path(tmpdir)

    def test_cli_invalid_working_dir(self, runner):
        """Test CLI with invalid working directory."""
        result = runner.invoke(
            main,
            ["--api-key", "test-key", "--working-dir", "/nonexistent/path"],
        )

        assert result.exit_code != 0
        assert "does not exist" in result.output or "Invalid value" in result.output

    def test_cli_no_color_option(self, runner, mock_repl, mock_session):
        """Test CLI with no-color option."""
        mock_repl_instance = Mock()
        mock_repl.return_value = mock_repl_instance

        result = runner.invoke(main, ["--api-key", "test-key", "--no-color"])

        assert result.exit_code == 0
        call_kwargs = mock_session.call_args[1]
        assert call_kwargs["no_color"] is True

    def test_cli_debug_option(self, runner, mock_repl, mock_session):
        """Test CLI with debug option."""
        mock_repl_instance = Mock()
        mock_repl.return_value = mock_repl_instance

        result = runner.invoke(main, ["--api-key", "test-key", "--debug"])

        assert result.exit_code == 0
        call_kwargs = mock_session.call_args[1]
        assert call_kwargs["debug"] is True

    def test_cli_short_options(self, runner, mock_repl, mock_session):
        """Test CLI with short option flags."""
        mock_repl_instance = Mock()
        mock_repl.return_value = mock_repl_instance

        result = runner.invoke(
            main,
            ["-p", "openai", "-m", "gpt-4", "-k", "test-key"],
        )

        assert result.exit_code == 0
        call_kwargs = mock_session.call_args[1]
        assert call_kwargs["provider"] == "openai"
        assert call_kwargs["model"] == "gpt-4"

    def test_cli_version_option(self, runner):
        """Test CLI --version option."""
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "devorbit" in result.output.lower()

    def test_cli_help_option(self, runner):
        """Test CLI --help option."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Devorbit" in result.output
        assert "--provider" in result.output
        assert "--model" in result.output

    def test_cli_keyboard_interrupt(self, runner, mock_repl, mock_session):
        """Test CLI handles keyboard interrupt gracefully."""
        mock_repl_instance = Mock()
        mock_repl_instance.run.side_effect = KeyboardInterrupt()
        mock_repl.return_value = mock_repl_instance

        result = runner.invoke(main, ["--api-key", "test-key"])

        assert result.exit_code == 0
        assert "Goodbye" in result.output

    def test_cli_exception_in_debug_mode(self, runner, mock_repl, mock_session):
        """Test CLI raises exceptions in debug mode."""
        mock_repl_instance = Mock()
        mock_repl_instance.run.side_effect = RuntimeError("Test error")
        mock_repl.return_value = mock_repl_instance

        result = runner.invoke(main, ["--api-key", "test-key", "--debug"])

        assert result.exit_code == 1
        assert isinstance(result.exception, RuntimeError)

    def test_cli_exception_without_debug(self, runner, mock_repl, mock_session):
        """Test CLI handles exceptions gracefully without debug mode."""
        mock_repl_instance = Mock()
        mock_repl_instance.run.side_effect = RuntimeError("Test error")
        mock_repl.return_value = mock_repl_instance

        result = runner.invoke(main, ["--api-key", "test-key"])

        assert result.exit_code == 1
        assert "Error:" in result.output
        assert "Test error" in result.output

    def test_cli_displays_welcome_banner(self, runner, mock_repl, mock_session):
        """Test CLI displays welcome banner by default."""
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        mock_repl_instance = Mock()
        mock_repl.return_value = mock_repl_instance

        result = runner.invoke(main, ["--api-key", "test-key"])

        assert result.exit_code == 0
        mock_session_instance.display_welcome.assert_called_once()

    def test_cli_no_welcome_with_no_color(self, runner, mock_repl, mock_session):
        """Test CLI skips welcome banner with --no-color."""
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        mock_repl_instance = Mock()
        mock_repl.return_value = mock_repl_instance

        result = runner.invoke(main, ["--api-key", "test-key", "--no-color"])

        assert result.exit_code == 0
        mock_session_instance.display_welcome.assert_not_called()

    def test_cli_combined_options(self, runner, mock_repl, mock_session):
        """Test CLI with multiple combined options."""
        mock_repl_instance = Mock()
        mock_repl.return_value = mock_repl_instance

        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(
                main,
                [
                    "--provider",
                    "openai",
                    "--model",
                    "gpt-4",
                    "--api-key",
                    "test-key",
                    "--working-dir",
                    tmpdir,
                    "--no-color",
                    "--debug",
                ],
            )

            assert result.exit_code == 0
            call_kwargs = mock_session.call_args[1]
            assert call_kwargs["provider"] == "openai"
            assert call_kwargs["model"] == "gpt-4"
            assert call_kwargs["api_key"] == "test-key"
            assert call_kwargs["working_dir"] == Path(tmpdir)
            assert call_kwargs["no_color"] is True
            assert call_kwargs["debug"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
