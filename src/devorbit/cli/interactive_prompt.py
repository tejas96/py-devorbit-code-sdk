"""Interactive prompts with arrow-key navigation.

This module provides Claude Code CLI-style interactive prompts with arrow key
navigation and Enter to select, replacing text-based input.
"""

try:
    from InquirerPy import inquirer
    from InquirerPy.base.control import Choice

    HAS_INQUIRER = True
except ImportError:
    HAS_INQUIRER = False
    inquirer = None
    Choice = None


class InteractivePrompt:
    """Interactive prompts with arrow key navigation."""

    @staticmethod
    def select(
        message: str,
        choices: list[tuple[str, str]],  # [(display, value), ...]
        default: str | None = None,
    ) -> str:
        """Show interactive selection prompt with arrow keys.

        Args:
            message: Prompt message
            choices: List of (display_text, value) tuples
            default: Default value

        Returns:
            Selected value
        """
        if HAS_INQUIRER and inquirer:
            # Use InquirerPy for beautiful arrow-based selection
            inquirer_choices = [Choice(value=value, name=display) for display, value in choices]

            result: str = inquirer.select(
                message=message,
                choices=inquirer_choices,
                default=default,
                pointer=">",
                style={
                    "pointer": "cyan bold",
                    "highlighted": "cyan bold",
                    "selected": "green",
                },
            ).execute()
            return result

        # Fallback to simple text input
        print(f"\n{message}")
        for i, (display, value) in enumerate(choices, 1):
            marker = "→" if value == default else " "
            print(f"  {marker} {i}. {display}")

        while True:
            try:
                choice_input = input(
                    f"\nSelect option (1-{len(choices)}) [Enter for default]: "
                ).strip()

                if not choice_input and default:
                    # Find default value
                    for _display, value in choices:
                        if value == default:
                            return value

                choice_num = int(choice_input)
                if 1 <= choice_num <= len(choices):
                    return choices[choice_num - 1][1]

                print(f"Please enter a number between 1 and {len(choices)}")
            except (ValueError, KeyboardInterrupt):
                print("\nPlease enter a valid number")

    @staticmethod
    def confirm(message: str, default: bool = True) -> bool:
        """Show yes/no confirmation prompt.

        Args:
            message: Confirmation message
            default: Default value

        Returns:
            True for yes, False for no
        """
        if HAS_INQUIRER and inquirer:
            result: bool = inquirer.confirm(
                message=message,
                default=default,
                style={
                    "question": "cyan bold",
                    "answer": "green",
                },
            ).execute()
            return result

        # Fallback
        default_text = "Y/n" if default else "y/N"
        response = input(f"{message} [{default_text}]: ").strip().lower()

        if not response:
            return default

        return response in {"y", "yes"}


__all__ = ["InteractivePrompt"]
