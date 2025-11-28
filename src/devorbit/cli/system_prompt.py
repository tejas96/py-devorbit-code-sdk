"""System prompt configuration for Devorbit CLI.

Optimized system prompt with:
- Dynamic system detection (OS, shell, architecture)
- Concise but powerful guidelines
- Token-efficient design
"""

import platform
import subprocess
from functools import lru_cache
from pathlib import Path


def _detect_system_info() -> dict[str, str]:
    """Detect system information once at startup.

    Returns:
        Dictionary with os, arch, shell, and version info
    """
    info: dict[str, str] = {
        "os": platform.system(),  # Darwin, Linux, Windows
        "os_version": platform.release(),
        "arch": platform.machine(),  # arm64, x86_64
        "shell": "bash",
    }

    # Detect shell
    try:
        shell_path = subprocess.run(
            ["echo", "$SHELL"],
            capture_output=True,
            text=True,
            shell=True,
            timeout=2,
            check=False,
        )
        if shell_path.stdout.strip():
            info["shell"] = Path(shell_path.stdout.strip()).name
    except Exception:
        pass

    # macOS specific
    if info["os"] == "Darwin":
        info["os_name"] = "macOS"
        try:
            result = subprocess.run(
                ["sw_vers", "-productVersion"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            if result.returncode == 0:
                info["os_version"] = result.stdout.strip()
        except Exception:
            pass
    elif info["os"] == "Linux":
        info["os_name"] = "Linux"
        # Try to get distro
        try:
            with Path("/etc/os-release").open() as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        info["os_name"] = line.split("=")[1].strip().strip('"')
                        break
        except Exception:
            pass
    else:
        info["os_name"] = info["os"]

    return info


@lru_cache(maxsize=1)
def get_system_info() -> dict[str, str]:
    """Get cached system information (detected once, cached forever)."""
    return _detect_system_info()


def build_system_prompt(
    working_dir: Path,
    provider: str,
    model: str,
    tools_available: list[str] | None = None,
) -> str:
    """Build optimized system prompt with dynamic system info.

    Args:
        working_dir: Current working directory
        provider: LLM provider name
        model: Model name/identifier
        tools_available: List of available tool names

    Returns:
        Concise but powerful system prompt
    """
    sys_info = get_system_info()
    tools_str = ", ".join(
        tools_available or ["bash", "read_file", "write_file", "edit_file", "glob", "grep"]
    )

    return f"""You are Devorbit, an AI coding assistant in the user's terminal.

## SYSTEM
- OS: {sys_info["os_name"]} {sys_info["os_version"]} ({sys_info["arch"]})
- Shell: {sys_info["shell"]}
- CWD: {working_dir}
- Provider: {provider} | Model: {model}

## TOOLS
{tools_str}

**bash**: Run ANY shell command (git, npm, pip, docker, system queries, etc.)
**read_file**: View file contents
**write_file**: Create/overwrite files
**edit_file**: Precise edits via search/replace (PREFER over write_file)
**glob**: Find files by pattern
**grep**: Search file contents

## CORE RULES
1. You have FULL system access - never say "I cannot access"
2. Use tools proactively - don't ask what you can detect (OS, files, etc.)
3. Read files before editing
4. Be concise, explain actions, warn before destructive ops

## WHEN TO USE TOOLS
✓ System queries → bash (df, ps, top -l 1, etc.)
✓ File ops → read first, then edit/write
✓ Code search → grep/glob
✗ Greetings → respond directly
✗ Concepts → explain without tools

## DESTRUCTIVE OPERATIONS (rm, clean, delete)
ALWAYS follow this pattern:
1. **INSPECT**: Show what exists with sizes (du -sh, ls -la)
2. **PRESENT**: List items, categorize by safety
3. **RECOMMEND**: Safe vs caution vs don't-delete
4. **CONFIRM**: Get user approval before executing
5. **EXECUTE**: Only after confirmation

Example - "clean cache":
→ Run: du -sh ~/Library/Caches/* | sort -hr | head -10
→ Show breakdown with sizes
→ Categorize: safe/caution/skip
→ Ask which to delete
→ Execute only confirmed items

NEVER run rm -rf without showing what will be deleted first!

## RESPONSE STYLE
- Concise, actionable
- Code in markdown blocks
- Suggest next steps
- Ask if ambiguous"""


# Lightweight default for quick access
DEFAULT_SYSTEM_PROMPT = """You are Devorbit, an AI coding assistant in the user's terminal.

Tools: bash (ANY command), read_file, write_file, edit_file, glob, grep

Rules:
- Full system access - use tools proactively
- Read before edit, inspect before delete
- Concise responses, warn before destructive ops
- Greetings → respond directly, no tools needed"""


__all__ = ["DEFAULT_SYSTEM_PROMPT", "build_system_prompt", "get_system_info"]
