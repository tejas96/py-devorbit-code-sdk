"""Command handler for slash commands in Devorbit CLI."""

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Callable

from devorbit import get_current_todos

from .session import CLISession
from .session_manager import SessionManager
from .workspace import WorkspaceManager


class CommandHandler:
    """Handles slash commands in the REPL."""

    def __init__(self, session: CLISession, repl: Any = None) -> None:
        """Initialize command handler.

        Args:
            session: CLI session instance
            repl: REPL instance (for accessing runtime state)
        """
        self.session = session
        self.repl = repl

        # Register built-in commands
        self.commands: dict[str, Callable[[list[str]], bool]] = {
            "help": self.cmd_help,
            "exit": self.cmd_exit,
            "quit": self.cmd_exit,
            "clear": self.cmd_clear,
            "compact": self.cmd_compact,
            "history": self.cmd_history,
            "status": self.cmd_status,
            "model": self.cmd_model,
            "provider": self.cmd_provider,
            "cd": self.cmd_cd,
            "pwd": self.cmd_pwd,
            "planning": self.cmd_planning,
            "permissions": self.cmd_permissions,
            "config": self.cmd_config,
            "todos": self.cmd_todos,
            "sessions": self.cmd_sessions,
            "workspace": self.cmd_workspace,
        }

    def handle_command(self, command_line: str) -> bool:
        """Handle a slash command.

        Args:
            command_line: Full command line starting with /

        Returns:
            True to continue REPL, False to exit
        """
        # Parse command and arguments
        parts = command_line[1:].split()
        if not parts:
            self.session.print_error("Empty command")
            return True

        cmd_name = parts[0].lower()
        cmd_args = parts[1:]

        # Execute command
        if cmd_name in self.commands:
            return self.commands[cmd_name](cmd_args)

        self.session.print_error(f"Unknown command: /{cmd_name}")
        self.session.print("Type /help to see available commands")
        return True

    def cmd_help(self, args: list[str]) -> bool:
        """Display help information.

        Args:
            args: Command arguments

        Returns:
            True to continue REPL
        """
        help_text = """
Available Commands:

    /help              - Show this help message
    /exit, /quit       - Exit the REPL
    /clear             - Clear conversation history
    /compact           - Compact conversation to reduce tokens
    /history           - Show conversation history
    /status            - Show current session status
    /model [name]      - Show or change the current model
    /provider          - Show current provider
    /cd <path>         - Change working directory
    /pwd               - Print working directory
    /planning          - Toggle planning mode
    /permissions       - Manage tool permissions
    /config            - Show current configuration
    /todos             - Show current todo list
    /sessions          - List and manage sessions
    /workspace         - Show workspace information

System Information:
    - Provider: {provider}
    - Model: {model}
    - Working Dir: {working_dir}
    - Messages: {msg_count}

Tips:
    - Use Ctrl+D or /exit to quit
    - Use Ctrl+C to cancel current operation
    - Commands starting with / are system commands
    - Everything else is sent to the LLM
        """.format(
            provider=self.session.provider,
            model=self.session.model or "(default)",
            working_dir=self.session.working_dir,
            msg_count=len(self.session.messages),
        )
        self.session.print(help_text)
        return True

    def cmd_exit(self, args: list[str]) -> bool:
        """Exit the REPL.

        Args:
            args: Command arguments

        Returns:
            False to exit REPL
        """
        self.session.print("Goodbye! 👋")
        self.session.is_running = False
        return False

    def cmd_clear(self, args: list[str]) -> bool:
        """Clear conversation history.

        Args:
            args: Command arguments

        Returns:
            True to continue REPL
        """
        self.session.clear_history()
        self.session.print_success("Conversation history cleared")
        return True

    def cmd_history(self, args: list[str]) -> bool:
        """Show conversation history.

        Args:
            args: Command arguments

        Returns:
            True to continue REPL
        """
        if not self.session.messages:
            self.session.print_info("No conversation history")
            return True

        self.session.print("\nConversation History:\n")
        for i, msg in enumerate(self.session.messages, 1):
            role = msg["role"]
            content = msg["content"]
            if isinstance(content, str):
                preview = content[:100] + "..." if len(content) > 100 else content
            else:
                preview = str(content)[:100]

            self.session.print(f"{i}. [{role}] {preview}")

        self.session.print(f"\nTotal messages: {len(self.session.messages)}")
        return True

    def cmd_status(self, args: list[str]) -> bool:
        """Show current session status.

        Args:
            args: Command arguments

        Returns:
            True to continue REPL
        """
        status = f"""
Session Status:
    Provider: {self.session.provider}
    Model: {self.session.model or "(default)"}
    Working Directory: {self.session.working_dir}
    Messages: {len(self.session.messages)}
    Planning Mode: {"Enabled" if self.session.planning_mode else "Disabled"}
    Debug Mode: {"Enabled" if self.session.debug else "Disabled"}
        """
        self.session.print(status)
        return True

    def cmd_model(self, args: list[str]) -> bool:
        """Show or change the current model.

        Args:
            args: Command arguments

        Returns:
            True to continue REPL
        """
        if not args:
            self.session.print(f"Current model: {self.session.model or '(default)'}")
        else:
            new_model = args[0]
            self.session.model = new_model
            self.session.print_success(f"Model changed to: {new_model}")
        return True

    def cmd_provider(self, args: list[str]) -> bool:
        """Show current provider.

        Args:
            args: Command arguments

        Returns:
            True to continue REPL
        """
        self.session.print(f"Current provider: {self.session.provider}")
        self.session.print_info("Note: Provider cannot be changed during session")
        return True

    def cmd_cd(self, args: list[str]) -> bool:
        """Change working directory.

        Args:
            args: Command arguments

        Returns:
            True to continue REPL
        """
        if not args:
            self.session.print_error("Usage: /cd <path>")
            return True

        new_dir = Path(args[0]).expanduser().resolve()
        if not new_dir.exists():
            self.session.print_error(f"Directory not found: {new_dir}")
            return True

        if not new_dir.is_dir():
            self.session.print_error(f"Not a directory: {new_dir}")
            return True

        self.session.working_dir = new_dir
        self.session.print_success(f"Changed working directory to: {new_dir}")
        return True

    def cmd_pwd(self, args: list[str]) -> bool:
        """Print working directory.

        Args:
            args: Command arguments

        Returns:
            True to continue REPL
        """
        self.session.print(str(self.session.working_dir))
        return True

    def cmd_planning(self, args: list[str]) -> bool:
        """Toggle planning mode.

        Args:
            args: Command arguments

        Returns:
            True to continue REPL
        """
        self.session.planning_mode = not self.session.planning_mode
        status = "enabled" if self.session.planning_mode else "disabled"
        self.session.print_success(f"Planning mode {status}")

        if self.session.planning_mode:
            self.session.print_info(
                "The agent will present plans for approval before executing changes"
            )
        return True

    def cmd_compact(self, args: list[str]) -> bool:
        """Compact conversation to reduce tokens.

        Args:
            args: Command arguments

        Returns:
            True to continue REPL
        """
        original_count = len(self.session.messages)
        if original_count <= 2:
            self.session.print_info("Conversation is already compact")
            return True

        # Keep only last 10 messages
        self.session.messages = self.session.messages[-10:]
        removed = original_count - len(self.session.messages)

        self.session.print_success(f"Compacted conversation: removed {removed} messages")
        self.session.print_info(f"Kept {len(self.session.messages)} recent messages")
        return True

    def cmd_permissions(self, args: list[str]) -> bool:
        """Manage tool permissions.

        Args:
            args: Command arguments

        Returns:
            True to continue REPL
        """
        if not args:
            # Show current permissions
            confirm_enabled = (
                self.repl and hasattr(self.repl, "confirm_tools") and self.repl.confirm_tools
            )
            session_allow = (
                self.repl
                and hasattr(self.repl, "session_allow_all")
                and self.repl.session_allow_all
            )

            permissions_text = f"""
Tool Permissions:

Current Settings:
    Confirmation Required: {confirm_enabled}
    Session Allow All: {session_allow}

Available Tools:
    • read_file, write_file, edit_file
    • bash, bash_output
    • glob_files, grep_code
    • web_fetch, web_search
    • todo_write, todo_read
    • task (agent delegation)

Usage:
    /permissions allow-all      - Disable all confirmations
    /permissions ask            - Enable confirmations (default)
    /permissions session-allow  - Auto-approve all tools this session

Note: Individual tool allowlists will be added in future updates
            """
            self.session.print(permissions_text)
            return True

        action = args[0].lower()
        if action == "allow-all":
            if self.repl and hasattr(self.repl, "confirm_tools"):
                self.repl.confirm_tools = False
            self.session.print_success("All tools will be executed without confirmation")
        elif action == "ask":
            if self.repl and hasattr(self.repl, "confirm_tools"):
                self.repl.confirm_tools = True
            self.session.print_success("Tool execution will require confirmation")
        elif action == "session-allow":
            if self.repl and hasattr(self.repl, "session_allow_all"):
                self.repl.session_allow_all = True
            self.session.print_success("Tools will auto-approve for this session (no prompts)")
        else:
            self.session.print_error(f"Unknown action: {action}")
            self.session.print("Usage: /permissions [allow-all|ask|session-allow]")

        return True

    def cmd_config(self, args: list[str]) -> bool:
        """Show current configuration.

        Args:
            args: Command arguments

        Returns:
            True to continue REPL
        """
        config_text = f"""
Current Configuration:

Connection:
    Provider: {self.session.provider}
    Model: {self.session.model or "(default)"}
    API Key: {"Set" if self.session.client else "Not set"}

Session:
    Working Directory: {self.session.working_dir}
    Messages: {len(self.session.messages)}
    Planning Mode: {"Enabled" if self.session.planning_mode else "Disabled"}
    Debug Mode: {"Enabled" if self.session.debug else "Disabled"}
    No Color: {"Enabled" if self.session.no_color else "Disabled"}

Modes:
    Streaming: Enabled
    Tool Confirmation: {("Disabled" if not hasattr(self.session, "confirm_tools") else ("Enabled" if self.session.confirm_tools else "Disabled"))}
        """
        self.session.print(config_text)
        return True

    def cmd_todos(self, args: list[str]) -> bool:
        """Show current todo list.

        Args:
            args: Command arguments

        Returns:
            True to continue REPL
        """
        todos = get_current_todos()

        if not todos:
            self.session.print_info("No active todos")
            return True

        # Calculate statistics
        total = len(todos)
        pending = sum(1 for t in todos if t["status"] == "pending")
        in_progress = sum(1 for t in todos if t["status"] == "in_progress")
        completed = sum(1 for t in todos if t["status"] == "completed")

        self.session.print("\n📋 Current Todo List:\n")

        for todo in todos:
            status = todo.get("status", "pending")
            content = todo.get("content", "")

            if status == "completed":
                symbol = "✓"
                style = "[completed]"
            elif status == "in_progress":
                symbol = "⏺"
                style = "[in progress]"
            else:
                symbol = "☐"
                style = "[pending]"

            self.session.print(f"  {symbol} {style} {content}")

        progress = (completed / total * 100) if total > 0 else 0
        self.session.print(f"\nProgress: {completed}/{total} tasks completed ({progress:.0f}%)")
        self.session.print(
            f"Pending: {pending} | In Progress: {in_progress} | Completed: {completed}"
        )

        return True

    def cmd_sessions(self, args: list[str]) -> bool:
        """List and manage sessions.

        Args:
            args: Command arguments

        Returns:
            True to continue REPL
        """
        session_mgr = SessionManager()

        if not args:
            # List recent sessions
            sessions = session_mgr.list_sessions(limit=10)

            if not sessions:
                self.session.print_info("No saved sessions found")
                return True

            self.session.print("\n📂 Recent Sessions:\n")

            for i, sess in enumerate(sessions, 1):
                session_id = sess["session_id"]
                provider = sess["provider"]
                model = sess.get("model", "default")
                timestamp = sess["timestamp"]
                msg_count = sess["message_count"]

                # Format timestamp
                try:
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    time_str = timestamp[:16]

                self.session.print(
                    f"  {i}. {session_id} - {provider}/{model} - {time_str} ({msg_count} messages)"
                )

            self.session.print("\nUse: devorbit -c  (continue last session)")
            self.session.print("     devorbit -r <id>  (resume specific session)")

        else:
            action = args[0].lower()

            if action == "delete" and len(args) > 1:
                session_id = args[1]
                if session_mgr.delete_session(session_id):
                    self.session.print_success(f"Deleted session: {session_id}")
                else:
                    self.session.print_error(f"Session not found: {session_id}")
            else:
                self.session.print_error(f"Unknown action: {action}")
                self.session.print("Usage: /sessions [delete <id>]")

        return True

    def cmd_workspace(self, args: list[str]) -> bool:
        """Show workspace information (.claude directory).

        Args:
            args: Command arguments

        Returns:
            True to continue REPL
        """
        workspace_mgr = WorkspaceManager(base_path=self.session.working_dir)

        if not workspace_mgr.workspace_exists():
            self.session.print_error("No workspace found in this directory")
            self.session.print("Workspace will be created automatically on startup")
            return True

        info = workspace_mgr.get_workspace_info()

        self.session.print("\n📂 Workspace Information:\n")
        self.session.print(f"  Path: {info['path']}")

        if "project_type" in info:
            self.session.print(f"  Project Type: {info['project_type']}")
            self.session.print(f"  Language: {info['language']}")

            if info.get("frameworks"):
                frameworks = ", ".join(info["frameworks"])
                self.session.print(f"  Frameworks: {frameworks}")

            self.session.print(f"  Last Updated: {info.get('last_updated', 'N/A')}")

        if "auto_confirm_tools" in info:
            self.session.print("\n⚙️  Preferences:")
            self.session.print(f"  Auto-confirm tools: {info['auto_confirm_tools']}")
            self.session.print(f"  Session allow-all: {info['session_allow_all']}")

        self.session.print("\n💡 Tip: The .claude directory stores project context and preferences")

        return True


__all__ = ["CommandHandler"]
