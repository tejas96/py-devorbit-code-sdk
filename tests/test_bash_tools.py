"""Tests for enhanced bash tools."""

import time

from devorbit import bash, bash_output, cleanup_sessions, kill_shell, list_active_sessions


class TestBash:
    """Tests for bash tool with persistent sessions."""

    def setup_method(self) -> None:
        """Clean up sessions before each test."""
        cleanup_sessions()

    def teardown_method(self) -> None:
        """Clean up sessions after each test."""
        cleanup_sessions()

    def test_bash_simple_command(self) -> None:
        """Test executing a simple command (uses bash_simple by default)."""
        result = bash("echo 'Hello, World!'")

        assert "error" not in result
        assert "Hello, World!" in result["output"]
        assert result["exit_code"] == 0
        # Note: bash_simple doesn't return session_id (no persistent session)

    def test_bash_simple_command_with_session(self) -> None:
        """Test executing a simple command with persistent session."""
        result = bash("echo 'Hello, World!'", session_id="test-simple")

        assert "error" not in result
        assert "Hello, World!" in result["output"]
        assert result["exit_code"] == 0
        assert "session_id" in result

    def test_bash_with_session_id(self) -> None:
        """Test using a specific session ID."""
        session_id = "test-session-1"

        # First command
        result1 = bash("cd /tmp", session_id=session_id)
        assert "error" not in result1
        assert result1["session_id"] == session_id

        # Second command in same session should remember state
        result2 = bash("pwd", session_id=session_id)
        assert "error" not in result2
        assert "/tmp" in result2["output"]
        assert result2["session_id"] == session_id

    def test_bash_persistent_state(self) -> None:
        """Test that session state persists across commands."""
        session_id = "test-persistent"

        # Set environment variable
        bash("export TEST_VAR=hello", session_id=session_id)

        # Check if variable persists
        result = bash("echo $TEST_VAR", session_id=session_id)
        assert "hello" in result["output"]

    def test_bash_working_directory_persistence(self) -> None:
        """Test that working directory persists."""
        session_id = "test-cwd"

        # Create temp directory and cd into it
        bash("mkdir -p /tmp/test_bash_cwd", session_id=session_id)
        bash("cd /tmp/test_bash_cwd", session_id=session_id)

        # Check current directory
        result = bash("pwd", session_id=session_id)
        assert "/tmp/test_bash_cwd" in result["output"]

        # Cleanup
        bash("cd /tmp && rm -rf /tmp/test_bash_cwd", session_id=session_id)

    def test_bash_background_execution(self) -> None:
        """Test running command in background."""
        result = bash(
            "sleep 1 && echo 'Background task complete'",
            run_in_background=True,
        )

        assert "error" not in result
        assert result["status"] == "running"
        assert "session_id" in result

    def test_bash_timeout(self) -> None:
        """Test command timeout."""
        result = bash("sleep 10", timeout=1.0)

        assert "error" in result
        assert "timed out" in result["error"].lower()

    def test_bash_command_error(self) -> None:
        """Test handling command errors (uses bash_simple by default)."""
        result = bash("nonexistent_command_xyz")

        # Should complete even if command fails
        # Note: bash_simple returns exit_code, not session_id
        assert result["exit_code"] != 0

    def test_bash_command_error_with_session(self) -> None:
        """Test handling command errors with persistent session."""
        result = bash("nonexistent_command_xyz", session_id="test-error")

        # Should complete even if command fails
        assert "session_id" in result


class TestBashOutput:
    """Tests for bash_output tool."""

    def setup_method(self) -> None:
        """Clean up sessions before each test."""
        cleanup_sessions()

    def teardown_method(self) -> None:
        """Clean up sessions after each test."""
        cleanup_sessions()

    def test_bash_output_basic(self) -> None:
        """Test reading output from a session."""
        # Start background task
        result = bash(
            "echo 'Line 1' && sleep 0.1 && echo 'Line 2'",
            run_in_background=True,
        )
        session_id = result["session_id"]

        # Wait a bit for output
        time.sleep(0.3)

        # Read output
        output_result = bash_output(session_id)

        assert "error" not in output_result
        assert output_result["bash_id"] == session_id
        assert "Line 1" in output_result["output"] or "Line 2" in output_result["output"]

    def test_bash_output_nonexistent_session(self) -> None:
        """Test reading from nonexistent session."""
        result = bash_output("nonexistent-session-id")

        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_bash_output_session_status(self) -> None:
        """Test session status in output."""
        # Create session with explicit session_id (required for persistent session)
        result = bash("echo 'test'", session_id="test-status-session")
        session_id = result["session_id"]

        # Get output
        output_result = bash_output(session_id)

        assert "is_running" in output_result
        assert "cwd" in output_result


class TestKillShell:
    """Tests for kill_shell tool."""

    def setup_method(self) -> None:
        """Clean up sessions before each test."""
        cleanup_sessions()

    def teardown_method(self) -> None:
        """Clean up sessions after each test."""
        cleanup_sessions()

    def test_kill_shell_basic(self) -> None:
        """Test killing a bash session."""
        # Create session
        result = bash("sleep 5", run_in_background=True)
        session_id = result["session_id"]

        # Kill session
        kill_result = kill_shell(session_id)

        assert kill_result["success"] is True
        assert kill_result["shell_id"] == session_id

        # Verify session is gone
        sessions = list_active_sessions()
        assert not any(s["session_id"] == session_id for s in sessions)

    def test_kill_shell_nonexistent(self) -> None:
        """Test killing nonexistent session."""
        result = kill_shell("nonexistent-session")

        assert "error" in result
        assert "not found" in result["error"].lower()


class TestSessionManagement:
    """Tests for session management functions."""

    def setup_method(self) -> None:
        """Clean up sessions before each test."""
        cleanup_sessions()

    def teardown_method(self) -> None:
        """Clean up sessions after each test."""
        cleanup_sessions()

    def test_list_active_sessions(self) -> None:
        """Test listing active sessions."""
        # Create multiple sessions
        bash("echo 'test1'", session_id="session-1")
        bash("echo 'test2'", session_id="session-2")

        # List sessions
        sessions = list_active_sessions()

        assert len(sessions) >= 2
        session_ids = [s["session_id"] for s in sessions]
        assert "session-1" in session_ids
        assert "session-2" in session_ids

    def test_cleanup_sessions(self) -> None:
        """Test cleaning up all sessions."""
        # Create sessions
        bash("echo 'test1'", session_id="cleanup-1")
        bash("echo 'test2'", session_id="cleanup-2")

        # Verify sessions exist
        sessions_before = list_active_sessions()
        assert len(sessions_before) >= 2

        # Cleanup
        cleanup_sessions()

        # Verify all sessions are gone
        sessions_after = list_active_sessions()
        assert len(sessions_after) == 0

    def test_session_info(self) -> None:
        """Test session information."""
        # Create session
        bash("echo 'test'", session_id="info-session")

        # Get session info
        sessions = list_active_sessions()
        session_info = next(s for s in sessions if s["session_id"] == "info-session")

        assert "is_running" in session_info
        assert "cwd" in session_info
