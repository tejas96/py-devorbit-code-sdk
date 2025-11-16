"""Main entry point for Devorbit CLI."""

import os
import sys
from pathlib import Path


try:
    import click
except ImportError:
    print(
        "Error: CLI dependencies not installed. "
        "Install with: pip install devorbit-multi-llm-sdk[cli]",
        file=sys.stderr,
    )
    sys.exit(1)

from devorbit import __version__

from .project_context import ProjectDetector
from .repl import DevorbitREPL
from .session import CLISession
from .session_manager import SessionManager
from .workspace import WorkspaceContext, WorkspaceManager


# Map providers to their environment variable names
PROVIDER_ENV_VARS = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GOOGLE_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "codellama": "CODELLAMA_API_KEY",
}


@click.command()
@click.version_option(version=__version__, prog_name="devorbit")
@click.option(
    "--provider",
    "-p",
    type=click.Choice(["anthropic", "openai", "gemini", "mistral", "codellama"]),
    default="anthropic",
    help="LLM provider to use (default: anthropic)",
)
@click.option(
    "--model",
    "-m",
    type=str,
    default=None,
    help="Specific model to use (e.g., claude-3-5-sonnet-20241022)",
)
@click.option(
    "--api-key",
    "-k",
    type=str,
    default=None,
    help="API key for the provider (can also use env vars)",
)
@click.option(
    "--working-dir",
    "-w",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Working directory for file operations (default: current directory)",
)
@click.option(
    "--no-color",
    is_flag=True,
    default=False,
    help="Disable colored output",
)
@click.option(
    "--debug",
    is_flag=True,
    default=False,
    help="Enable debug mode with verbose logging",
)
@click.option(
    "--no-confirm",
    is_flag=True,
    default=False,
    help="Disable tool execution confirmation prompts",
)
@click.option(
    "--no-stream",
    is_flag=True,
    default=False,
    help="Disable streaming responses",
)
@click.option(
    "-c",
    "--continue-session",
    is_flag=True,
    default=False,
    help="Continue the most recent session",
)
@click.option(
    "-r",
    "--resume",
    type=str,
    default=None,
    help="Resume a specific session by ID",
)
@click.option(
    "--output-format",
    "-o",
    type=click.Choice(["text", "json", "markdown"]),
    default="text",
    help="Output format for responses (default: text)",
)
def main(  # noqa: PLR0912, PLR0915
    provider: str,
    model: str | None,
    api_key: str | None,
    working_dir: Path | None,
    no_color: bool,
    debug: bool,
    no_confirm: bool,
    no_stream: bool,
    continue_session: bool,
    resume: str | None,
    output_format: str,
) -> None:
    """Devorbit - Multi-provider LLM CLI with Claude Code-like experience.

    An interactive command-line interface for autonomous coding with multiple LLM providers.

    \b
    Features:
    - Claude Code-style streaming responses
    - Interactive tool confirmation prompts
    - Rich UI with token usage display
    - Multi-provider support (Anthropic, OpenAI, Gemini, Mistral, CodeLlama)
    - File operations (Read, Write, Edit, Glob, Grep)
    - Agent orchestration and task delegation
    - Web search and fetching capabilities

    \b
    Examples:
        # Start with Anthropic (default, streaming enabled)
        $ devorbit

        # Use OpenAI GPT-4 without streaming
        $ devorbit --provider openai --model gpt-4-turbo --no-stream

        # Disable tool confirmation prompts
        $ devorbit --no-confirm

        # Output in plain markdown format
        $ devorbit --output-format markdown

    \b
    Environment Variables:
        ANTHROPIC_API_KEY    - API key for Anthropic
        OPENAI_API_KEY       - API key for OpenAI
        GOOGLE_API_KEY       - API key for Google Gemini
        MISTRAL_API_KEY      - API key for Mistral
    """
    # Get API key from environment if not provided via command line
    if not api_key:
        env_var = PROVIDER_ENV_VARS.get(provider)
        if env_var:
            api_key = os.environ.get(env_var)

    # Validate API key
    if not api_key:
        env_var = PROVIDER_ENV_VARS.get(provider, f"{provider.upper()}_API_KEY")
        click.echo(
            f"Error: No API key provided for {provider}. "
            f"Set {env_var} environment variable or use --api-key",
            err=True,
        )
        sys.exit(1)

    # Initialize workspace (Claude Code style .claude directory)
    workspace_path = working_dir or Path.cwd()
    workspace_mgr = WorkspaceManager(base_path=workspace_path)

    # Create workspace if it doesn't exist
    if not workspace_mgr.workspace_exists():
        workspace_mgr.create_workspace()

        # Detect project type and save context
        detector = ProjectDetector(path=workspace_path)
        project_info = detector.detect_project_type()

        context = WorkspaceContext(
            project_type=project_info.project_type,
            language=project_info.language,
            frameworks=project_info.frameworks,
            dependencies=project_info.dependencies,
            working_directory=str(workspace_path),
        )
        workspace_mgr.save_context(context)

        if debug:
            click.echo(f"✨ Created workspace: {workspace_mgr.claude_dir}")
            click.echo(f"📁 Detected project type: {project_info.project_type}")
    else:
        # Load existing context
        try:
            context = workspace_mgr.load_context()
            if debug:
                click.echo(f"📂 Loaded workspace: {context.project_type}")
        except FileNotFoundError:
            # Context file missing, recreate it
            detector = ProjectDetector(path=workspace_path)
            project_info = detector.detect_project_type()
            context = WorkspaceContext(
                project_type=project_info.project_type,
                language=project_info.language,
                frameworks=project_info.frameworks,
                dependencies=project_info.dependencies,
                working_directory=str(workspace_path),
            )
            workspace_mgr.save_context(context)

    # Load workspace preferences
    try:
        preferences = workspace_mgr.load_preferences()
        # Override no_confirm if workspace has auto_confirm_tools enabled
        if preferences.auto_confirm_tools and not no_confirm:
            no_confirm = True
            if debug:
                click.echo("🔧 Auto-confirm enabled from workspace preferences")
    except FileNotFoundError:
        preferences = None

    # Initialize session manager
    session_mgr = SessionManager()
    session_id = None
    loaded_session = None

    # Handle session continuation/resumption
    if continue_session:
        session_id = session_mgr.get_latest_session_id()
        if session_id:
            loaded_session = session_mgr.load_session(session_id)
            if loaded_session:
                click.echo(f"📂 Continuing session: {session_id}")
            else:
                click.echo("⚠️  No previous session found, starting new session")
                session_id = None
        else:
            click.echo("⚠️  No previous session found, starting new session")

    elif resume:
        loaded_session = session_mgr.load_session(resume)
        if loaded_session:
            session_id = resume
            click.echo(f"📂 Resumed session: {session_id}")
        else:
            click.echo(f"❌ Session not found: {resume}", err=True)
            sys.exit(1)

    # Create or restore CLI session
    if loaded_session:
        # Restore from loaded session
        session = CLISession(
            provider=loaded_session["provider"],
            model=loaded_session.get("model"),
            api_key=api_key,  # Use current API key
            working_dir=Path(loaded_session["working_dir"]),
            no_color=no_color,
            debug=debug,
            output_format=output_format,
        )
        # Restore message history
        session.messages = loaded_session.get("messages", [])
    else:
        # Create new session
        session_id = session_mgr.generate_session_id()
        session = CLISession(
            provider=provider,
            model=model,
            api_key=api_key,
            working_dir=working_dir,
            no_color=no_color,
            debug=debug,
            output_format=output_format,
        )

    # Display welcome banner
    if not no_color and not loaded_session:
        session.display_welcome()

    # Start REPL with Claude Code-style UX
    repl = DevorbitREPL(
        session=session,
        confirm_tools=not no_confirm,
        stream=not no_stream,
    )
    try:
        repl.run()
    except KeyboardInterrupt:
        click.echo("\n\nGoodbye! 👋")
    except Exception as e:
        if debug:
            raise
        click.echo(f"\nError: {e}", err=True)
        sys.exit(1)
    finally:
        # Save session on exit
        if session_id:
            try:
                session_mgr.save_session(
                    session_id=session_id,
                    provider=session.provider,
                    model=session.model,
                    messages=session.messages,
                    working_dir=session.working_dir,
                    metadata={
                        "total_tokens": getattr(repl, "total_tokens_used", 0),
                    },
                )
                if not no_color:
                    click.echo(f"💾 Session saved: {session_id}")
            except Exception as e:
                if debug:
                    click.echo(f"⚠️  Failed to save session: {e}", err=True)


if __name__ == "__main__":
    main()
