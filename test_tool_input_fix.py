#!/usr/bin/env python3
"""Test that tool input accumulation is working correctly."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from devorbit._streaming import MessageStream
from devorbit._models import ToolUseBlock


def test_tool_input_accumulation():
    """Test that input_json_delta events are accumulated correctly."""
    print("=" * 60)
    print("TEST: Tool Input Accumulation Fix")
    print("=" * 60)

    # Simulate streaming events for a tool use
    events = [
        {
            "type": "message_start",
            "message": {
                "id": "msg_test",
                "model": "claude-sonnet-4-5",
                "role": "assistant",
                "content": [],
                "stop_reason": None,
                "usage": {"input_tokens": 10, "output_tokens": 20},
            },
        },
        {
            "type": "content_block_start",
            "index": 0,
            "content_block": {
                "type": "tool_use",
                "id": "toolu_123",
                "name": "bash",
            },
        },
        {
            "type": "content_block_delta",
            "index": 0,
            "delta": {"type": "input_json_delta", "partial_json": '{"command"'},
        },
        {
            "type": "content_block_delta",
            "index": 0,
            "delta": {"type": "input_json_delta", "partial_json": ': "ls -la"'},
        },
        {
            "type": "content_block_delta",
            "index": 0,
            "delta": {"type": "input_json_delta", "partial_json": ', "timeout": 60}'},
        },
        {"type": "content_block_stop", "index": 0},
        {"type": "message_delta", "delta": {"stop_reason": "tool_use"}},
        {"type": "message_stop"},
    ]

    print("\n[1/3] Creating message stream with simulated events...")
    stream = MessageStream(iter(events))

    print("[2/3] Processing stream...")
    # Process stream (text_stream consumes events)
    list(stream.text_stream)

    print("[3/3] Getting final message and checking tool input...")
    message = stream.get_final_message()

    # Check results
    assert len(message.content) == 1, f"Expected 1 content block, got {len(message.content)}"

    block = message.content[0]
    assert isinstance(block, ToolUseBlock), f"Expected ToolUseBlock, got {type(block)}"

    print(f"\n  Tool ID: {block.id}")
    print(f"  Tool Name: {block.name}")
    print(f"  Tool Input: {block.input}")
    print(f"  Input Type: {type(block.input)}")

    # Verify the input was properly accumulated and parsed
    assert block.input != {}, "❌ FAILED: Tool input is still empty!"
    assert "command" in block.input, "❌ FAILED: 'command' not in tool input!"
    assert (
        block.input["command"] == "ls -la"
    ), f"❌ FAILED: Expected 'ls -la', got '{block.input.get('command')}'"
    assert (
        block.input.get("timeout") == 60
    ), f"❌ FAILED: Expected timeout=60, got {block.input.get('timeout')}"

    print("\n✅ SUCCESS: Tool input accumulation is working correctly!")
    print(f"  - Parsed JSON: {block.input}")
    print(f"  - Command: {block.input['command']}")
    print(f"  - Timeout: {block.input['timeout']}")

    return True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TESTING TOOL INPUT FIX (No API calls needed)")
    print("=" * 60 + "\n")

    try:
        success = test_tool_input_accumulation()
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60 + "\n")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
