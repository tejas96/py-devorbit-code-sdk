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

from .repl_enhanced import EnhancedREPL
from .session import CLISession


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
def main(
    provider: str,
    model: str | None,
    api_key: str | None,
    working_dir: Path | None,
    no_color: bool,
    debug: bool,
    no_confirm: bool,
    no_stream: bool,
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

    # Create CLI session - provider is already validated by click.Choice
    session = CLISession(
        provider=provider,
        model=model,
        api_key=api_key,
        working_dir=working_dir,
        no_color=no_color,
        debug=debug,
    )

    # Display welcome banner
    if not no_color:
        session.display_welcome()

    # Start Enhanced REPL with Claude Code-style UX
    repl = EnhancedREPL(
        session=session,
        confirm_tools=not no_confirm,
        stream=not no_stream,
    )
    try:
        repl.run()
    except KeyboardInterrupt:
        click.echo("\n\nGoodbye! 👋")
        sys.exit(0)
    except Exception as e:
        if debug:
            raise
        click.echo(f"\nError: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
