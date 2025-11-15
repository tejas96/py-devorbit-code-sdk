"""Main entry point for Devorbit CLI."""

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

from .repl import DevorbitREPL
from .session import CLISession


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
    envvar="ANTHROPIC_API_KEY",
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
def main(
    provider: str,
    model: str | None,
    api_key: str | None,
    working_dir: Path | None,
    no_color: bool,
    debug: bool,
) -> None:
    """Devorbit - Multi-provider LLM CLI with Claude Code-like experience.

    An interactive command-line interface for autonomous coding with multiple LLM providers.

    \b
    Features:
    - Multi-provider support (Anthropic, OpenAI, Gemini, Mistral, CodeLlama)
    - Interactive REPL with slash commands
    - File operations (Read, Write, Edit, Glob, Grep)
    - Agent orchestration and task delegation
    - Planning mode for safe code analysis
    - Web search and fetching capabilities

    \b
    Examples:
        # Start with Anthropic (default)
        $ devorbit

        # Use OpenAI GPT-4
        $ devorbit --provider openai --model gpt-4-turbo

        # Use Gemini in a specific directory
        $ devorbit --provider gemini --working-dir /path/to/project

    \b
    Environment Variables:
        ANTHROPIC_API_KEY    - API key for Anthropic
        OPENAI_API_KEY       - API key for OpenAI
        GOOGLE_API_KEY       - API key for Google Gemini
        MISTRAL_API_KEY      - API key for Mistral
    """
    # Validate API key
    if not api_key:
        click.echo(
            f"Error: No API key provided for {provider}. "
            f"Set {provider.upper()}_API_KEY environment variable or use --api-key",
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

    # Start REPL
    repl = DevorbitREPL(session)
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
