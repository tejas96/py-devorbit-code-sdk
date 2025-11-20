#!/usr/bin/env python3
"""Quick test to verify LLM integration with minimal token usage."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from devorbit.cli.session import CLISession


def test_minimal_llm_call():
    """Make one minimal LLM call to verify integration."""
    print("=" * 60)
    print("MINIMAL LLM INTEGRATION TEST")
    print("=" * 60)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("✗ ANTHROPIC_API_KEY not set")
        return False

    try:
        print("\n[1/3] Creating session...")
        session = CLISession(
            provider="anthropic",
            model="claude-sonnet-4-5",
            api_key=api_key,
            working_dir=Path.cwd(),
            no_color=True,
        )
        print("✓ Session created")

        print("\n[2/3] Making minimal LLM call (prompt: 'hi')...")
        # Use the client directly for a minimal call
        response = session.client.messages.create(
            model=session.model,
            max_tokens=10,  # Minimal tokens to save cost
            messages=[{"role": "user", "content": "hi"}],
        )
        print("✓ Response received")

        print("\n[3/3] Verifying response...")
        if response.content and len(response.content) > 0:
            text_content = (
                response.content[0].text
                if hasattr(response.content[0], "text")
                else str(response.content[0])
            )
            print(f"  Response: {text_content[:50]}...")
            print(f"  Model: {response.model}")
            print(
                f"  Tokens used: input={response.usage.input_tokens}, output={response.usage.output_tokens}"
            )
            print("✓ Response valid")

            # Estimate cost (very rough)
            # Claude Sonnet 4.5: ~$3/M input, ~$15/M output
            cost = (response.usage.input_tokens / 1_000_000 * 3) + (
                response.usage.output_tokens / 1_000_000 * 15
            )
            print(f"  Estimated cost: ${cost:.6f}")

            return True
        print("✗ No content in response")
        return False

    except Exception as e:
        print(f"\n✗ LLM call failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\nTesting with MINIMAL token usage to preserve balance...\n")
    success = test_minimal_llm_call()

    print("\n" + "=" * 60)
    if success:
        print("✅ LLM INTEGRATION WORKING")
    else:
        print("❌ LLM INTEGRATION FAILED")
    print("=" * 60 + "\n")

    sys.exit(0 if success else 1)
