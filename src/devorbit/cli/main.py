"""Main entry point for Devorbit CLI."""

import sys
from pathlib import Path
from typing import TYPE_CHECKING


try:
    import click
except ImportError:
    print(
        "Error: CLI dependencies not installed. "
        "Install with: pip install devorbit-multi-llm-sdk[cli]",
        file=sys.stderr,
    )
    sys.exit(1)

if TYPE_CHECKING:
    from questionary import Choice

    import questionary as questionary_module

    HAS_QUESTIONARY = True
else:
    try:
        import questionary as questionary_module
        from questionary import Choice

        HAS_QUESTIONARY = True
    except ImportError:
        questionary_module = None  # type: ignore[assignment]
        Choice = None  # type: ignore[assignment,misc]
        HAS_QUESTIONARY = False

from devorbit import __version__

from .repl import DevorbitREPL
from .session import CLISession


def select_provider_interactive() -> str | None:
    """Show interactive provider selection menu.

    Returns:
        Selected provider name or None if cancelled
    """
    if not TYPE_CHECKING and (not HAS_QUESTIONARY or questionary_module is None or Choice is None):
        return None

    providers = [
        Choice(
            title="🤖 Anthropic - Claude models (claude-3-5-sonnet, etc.)",
            value="anthropic",
        ),
        Choice(title="🟢 OpenAI - GPT models (gpt-4, gpt-3.5-turbo, etc.)", value="openai"),
        Choice(title="🔷 Google Gemini - Gemini models (gemini-pro, etc.)", value="gemini"),
        Choice(title="🌟 Mistral - Mistral models (mistral-large, etc.)", value="mistral"),
        Choice(title="🦙 CodeLlama - Code-specific models", value="codellama"),
    ]

    try:
        result = questionary_module.select(
            "Select LLM Provider:",
            choices=providers,
            style=questionary_module.Style(
                [
                    ("qmark", "fg:cyan bold"),
                    ("question", "bold"),
                    ("pointer", "fg:cyan bold"),
                    ("highlighted", "fg:cyan bold"),
                    ("selected", "fg:green"),
                ]
            ),
        ).ask()
        # Cast to str since questionary.select can return Any
        return str(result) if result else None
    except (KeyboardInterrupt, EOFError):
        click.echo("\nCancelled provider selection")
        return None


@click.command()
@click.version_option(version=__version__, prog_name="devorbit")
@click.option(
    "--provider",
    "-p",
    type=click.Choice(["anthropic", "openai", "gemini", "mistral", "codellama"]),
    default=None,
    help="LLM provider to use (if not specified, interactive selection will be shown)",
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
    provider: str | None,
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
        # Start with interactive provider selection
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
    # Interactive provider selection if not specified
    if provider is None:
        selected = select_provider_interactive()
        if selected is None:
            click.echo("Error: No provider selected", err=True)
            sys.exit(1)
        provider = selected

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
