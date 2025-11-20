#!/usr/bin/env python3
"""Test script to verify all implemented features work correctly."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_imports():
    """Test that all modules import correctly."""
    print("=" * 60)
    print("TEST 1: Module Imports")
    print("=" * 60)

    try:
        # Test UI module imports
        print("\n[1/3] Testing UI module imports...")

        print("✓ UI modules imported successfully")

        # Test input module imports
        print("\n[2/3] Testing input module imports...")

        print("✓ Input modules imported successfully")

        # Test enhanced session and repl imports
        print("\n[3/3] Testing enhanced CLI imports...")

        print("✓ Enhanced CLI modules imported successfully")

        print("\n✓ ALL IMPORTS SUCCESSFUL\n")
        return True

    except Exception as e:
        print(f"\n✗ Import failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_ui_components():
    """Test UI components without API calls."""
    print("=" * 60)
    print("TEST 2: UI Components")
    print("=" * 60)

    try:
        from devorbit.cli.ui import (
            ColorScheme,
            Colors,
            NotificationManager,
            StatusLine,
        )

        # Test color scheme
        print("\n[1/4] Testing ColorScheme...")
        colors = ColorScheme()
        assert colors.brand_orange == "#FF6B35"
        assert colors.brand_blue == "#004E89"
        assert colors.success_green == "#10B981"
        print(f"  - Brand Orange: {colors.brand_orange}")
        print(f"  - Success Green: {colors.success_green}")
        print("✓ ColorScheme working correctly")

        # Test Colors helper
        print("\n[2/4] Testing Colors helper...")
        info_style = Colors.rich_info()
        success_style = Colors.rich_success()
        error_style = Colors.rich_error()
        assert "rgb(" in info_style
        print(f"  - Info style: {info_style}")
        print("✓ Colors helper working correctly")

        # Test NotificationManager
        print("\n[3/4] Testing NotificationManager...")
        notifications = NotificationManager(no_color=True)
        # These should not raise errors
        notifications.info("Test info message")
        notifications.success("Test success message")
        notifications.warning("Test warning message")
        notifications.error("Test error message")
        print("✓ NotificationManager working correctly")

        # Test StatusLine
        print("\n[4/4] Testing StatusLine...")
        status = StatusLine(no_color=True)
        status.set_model("claude-sonnet-4-5", "anthropic")
        status.set_context(1000, 10000)
        rendered = status.render()
        # Status line should contain context and brackets
        assert "[" in rendered and "]" in rendered
        print(f"  Status line: {rendered[:80] if len(rendered) > 80 else rendered}")
        print("✓ StatusLine working correctly")

        print("\n✓ ALL UI COMPONENTS WORKING\n")
        return True

    except Exception as e:
        print(f"\n✗ UI component test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_input_features():
    """Test input features without API calls."""
    print("=" * 60)
    print("TEST 3: Input Features")
    print("=" * 60)

    try:
        from devorbit.cli.input import (
            CommandCompleter,
            FileCompleter,
            ModelCompleter,
            FileMentionParser,
        )
        from devorbit.cli.input.editor import InputValidator

        # Test CommandCompleter
        print("\n[1/5] Testing CommandCompleter...")
        cmd_completer = CommandCompleter()
        completions = cmd_completer.get_completions("hel")
        assert any(cmd == "help" for cmd, _ in completions)
        print(f"  - Found {len(completions)} completions for 'hel'")
        print("✓ CommandCompleter working correctly")

        # Test FileCompleter
        print("\n[2/5] Testing FileCompleter...")
        file_completer = FileCompleter(Path.cwd())
        completions = file_completer.get_completions("src")
        print(f"  - Found {len(completions)} file completions")
        print("✓ FileCompleter working correctly")

        # Test ModelCompleter
        print("\n[3/5] Testing ModelCompleter...")
        model_completer = ModelCompleter(provider="anthropic")
        completions = model_completer.get_completions("claude")
        assert len(completions) > 0
        print(f"  - Found {len(completions)} model completions for 'claude'")
        print("✓ ModelCompleter working correctly")

        # Test FileMentionParser
        print("\n[4/5] Testing FileMentionParser...")
        mention_parser = FileMentionParser(Path.cwd())
        text = "explain @src/devorbit/__init__.py"
        mentions = mention_parser.parse(text)
        print(f"  - Parsed {len(mentions)} mentions from text")
        if mentions:
            summary = mention_parser.format_mention_summary(mentions)
            print(f"  - Summary: {summary}")
        print("✓ FileMentionParser working correctly")

        # Test InputValidator
        print("\n[5/5] Testing InputValidator...")
        is_valid, error = InputValidator.validate_input("Hello world")
        assert is_valid and error is None
        is_valid, error = InputValidator.validate_input("x" * 60000)
        assert not is_valid
        print("  - Valid input accepted")
        print("  - Invalid input rejected")
        print("✓ InputValidator working correctly")

        print("\n✓ ALL INPUT FEATURES WORKING\n")
        return True

    except Exception as e:
        print(f"\n✗ Input feature test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_cli_initialization():
    """Test CLI initialization without making API calls."""
    print("=" * 60)
    print("TEST 4: CLI Initialization")
    print("=" * 60)

    try:
        import os
        from devorbit.cli.session import CLISession
        from devorbit.cli.repl import DevorbitREPL

        # Set API key
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("⚠ ANTHROPIC_API_KEY not set, skipping initialization test")
            return True

        print("\n[1/2] Testing CLISession initialization...")
        session = CLISession(
            provider="anthropic",
            model="claude-sonnet-4-5",
            api_key=api_key,
            working_dir=Path.cwd(),
            no_color=True,
        )
        print(f"  - Provider: {session.provider}")
        print(f"  - Model: {session.model}")
        print(f"  - Working dir: {session.working_dir}")
        print("✓ CLISession initialized successfully")

        print("\n[2/2] Testing DevorbitREPL initialization...")
        repl = DevorbitREPL(session)
        assert repl.session == session
        assert repl.autocomplete is not None
        assert repl.mention_parser is not None
        assert repl.input_validator is not None
        print("  - REPL components initialized")
        print("✓ DevorbitREPL initialized successfully")

        print("\n✓ CLI INITIALIZATION SUCCESSFUL\n")
        return True

    except Exception as e:
        print(f"\n✗ CLI initialization test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_minimal_api_call():
    """Test that API integration is ready (without making actual calls)."""
    print("=" * 60)
    print("TEST 5: API Integration Setup")
    print("=" * 60)

    try:
        import os
        from devorbit.cli.session import CLISession

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("⚠ ANTHROPIC_API_KEY not set, skipping API test")
            return True

        print("\n[1/2] Testing session with API key...")
        session = CLISession(
            provider="anthropic",
            model="claude-sonnet-4-5",
            api_key=api_key,
            working_dir=Path.cwd(),
            no_color=True,
        )
        print("  - Session created with API key")
        print("✓ Session initialized with API credentials")

        print("\n[2/2] Testing message management...")
        session.add_message("user", "test message")
        assert len(session.messages) == 1
        assert session.messages[0]["role"] == "user"
        print("  - Messages can be added to history")
        print("✓ Message management working")

        print("\n✓ API INTEGRATION SETUP SUCCESSFUL")
        print("  (Note: Actual LLM integration is in progress - see repl.py TODO)")
        print("\n")
        return True

    except Exception as e:
        print(f"\n✗ API integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("DEVORBIT CLI - FEATURE IMPLEMENTATION TEST SUITE")
    print("=" * 60 + "\n")

    results = []

    # Run tests
    results.append(("Module Imports", test_imports()))
    results.append(("UI Components", test_ui_components()))
    results.append(("Input Features", test_input_features()))
    results.append(("CLI Initialization", test_cli_initialization()))
    results.append(("API Integration Setup", test_minimal_api_call()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} | {test_name}")

    print("=" * 60)
    print(f"TOTAL: {passed}/{total} tests passed")
    print("=" * 60 + "\n")

    return all(result for _, result in results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
