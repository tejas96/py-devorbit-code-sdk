"""Skills system for Devorbit SDK.

This module provides a reusable skills framework similar to Claude Code:
- Load skills from .devorbit/skills/ or .claude/skills/
- Parse skill definitions from SKILL.md files
- Execute skills with context injection
- Support for skill dependencies and composition
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ._tool_helpers import beta_tool


# ============================================================================
# Skill Data Classes
# ============================================================================


@dataclass
class Skill:
    """Skill definition.

    Attributes:
        name: Skill name
        description: Skill description
        content: Skill instructions/prompts
        tags: Skill tags for categorization
        version: Skill version
        dependencies: Required tools or other skills
        file_path: Source file path (if loaded from file)
        enabled: Whether skill is enabled
    """

    name: str
    description: str
    content: str
    tags: list[str] = field(default_factory=list)
    version: str = "1.0.0"
    dependencies: list[str] = field(default_factory=list)
    file_path: str | None = None
    enabled: bool = True

    def matches_tag(self, tag: str) -> bool:
        """Check if skill has the given tag.

        Args:
            tag: Tag to check

        Returns:
            True if skill has the tag
        """
        return tag.lower() in [t.lower() for t in self.tags]


# ============================================================================
# Skill Registry
# ============================================================================


class SkillRegistry:
    """Registry for managing skills."""

    def __init__(self) -> None:
        """Initialize skill registry."""
        self._skills: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        """Register a skill.

        Args:
            skill: Skill to register
        """
        self._skills[skill.name] = skill

    def get(self, name: str) -> Skill | None:
        """Get skill by name.

        Args:
            name: Skill name

        Returns:
            Skill if found, None otherwise
        """
        return self._skills.get(name)

    def list_skills(self, tag: str | None = None) -> list[Skill]:
        """List all registered skills, optionally filtered by tag.

        Args:
            tag: Optional tag to filter by

        Returns:
            List of skills
        """
        skills = list(self._skills.values())

        if tag:
            skills = [s for s in skills if s.matches_tag(tag)]

        return sorted(skills, key=lambda s: s.name)

    def remove(self, name: str) -> bool:
        """Remove skill by name.

        Args:
            name: Skill name

        Returns:
            True if removed, False if not found
        """
        if name not in self._skills:
            return False

        self._skills.pop(name)
        return True

    def clear(self) -> None:
        """Clear all registered skills."""
        self._skills.clear()


# Global skill registry
_REGISTRY = SkillRegistry()


# ============================================================================
# Skill Loaders
# ============================================================================


def parse_skill_frontmatter(
    content: str,
) -> tuple[str | None, str, str, list[str], str, list[str]] | None:
    """Extract frontmatter from skill file.

    Args:
        content: File content

    Returns:
        Tuple of (name, description, body, tags, version, dependencies) or None
    """
    pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(pattern, content, re.DOTALL)
    if not match:
        return None

    raw_meta, skill_content = match.groups()
    meta: dict[str, str | list[str]] = {
        "name": "",
        "description": "",
        "tags": [],
        "version": "1.0.0",
        "dependencies": [],
    }

    for line in raw_meta.splitlines():
        if ":" not in line:
            continue
        key, value = [x.strip() for x in line.split(":", 1)]

        if key in ("tags", "dependencies"):
            # Parse list values
            list_str = value.strip("[]")
            meta[key] = [item.strip("'\" ") for item in list_str.split(",") if item.strip()]
        else:
            meta[key] = value

    # Ensure correct types
    name = str(meta["name"]) if meta["name"] else None
    description = str(meta["description"]) if meta["description"] else ""
    tags = list(meta["tags"]) if isinstance(meta["tags"], list) else []
    version = str(meta["version"]) if meta["version"] else "1.0.0"
    dependencies = list(meta["dependencies"]) if isinstance(meta["dependencies"], list) else []

    return (
        name,
        description,
        skill_content.strip(),
        tags,
        version,
        dependencies,
    )


def parse_simple_skill_markdown(content: str, fallback_name: str) -> tuple[str, str, str]:
    """Parse skill markdown without frontmatter.

    Args:
        content: File content
        fallback_name: Name to use if not found in content

    Returns:
        Tuple of (name, description, body)
    """
    lines = content.splitlines()
    name = fallback_name
    description = ""
    skill_body = content

    for i, line in enumerate(lines):
        if line.startswith("# "):
            name = line[2:].strip()
            # Try next non-empty line as description
            for j in range(i + 1, len(lines)):
                if lines[j].strip() and not lines[j].startswith("#"):
                    description = lines[j].strip()
                    break
            skill_body = "\n".join(lines[i + 1 :]).strip()
            break

    return name, description, skill_body


def parse_skill_file(file_path: Path) -> Skill | None:
    """Parse a skill file.

    Args:
        file_path: Path to skill file

    Returns:
        Skill if successfully parsed, None otherwise
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return None

    # 1. Try frontmatter
    fm = parse_skill_frontmatter(content)
    if fm:
        name, description, body, tags, version, dependencies = fm
        return Skill(
            name=name or file_path.stem,
            description=description,
            content=body,
            tags=tags,
            version=version,
            dependencies=dependencies,
            file_path=str(file_path.absolute()),
        )

    # 2. Fallback to simple markdown
    name, description, body = parse_simple_skill_markdown(content, file_path.stem)

    return Skill(
        name=name,
        description=description,
        content=body,
        file_path=str(file_path.absolute()),
    )


def load_skills_from_dir(skills_dir: Path) -> list[Skill]:
    """Load all skills from a directory.

    Args:
        skills_dir: Directory containing skill files

    Returns:
        List of loaded skills
    """
    if not skills_dir.exists() or not skills_dir.is_dir():
        return []

    skills = []

    # Load all .md files
    for file_path in skills_dir.glob("*.md"):
        if skill := parse_skill_file(file_path):
            skills.append(skill)

    return skills


def load_skills(project_root: Path | None = None) -> list[Skill]:
    """Load skills from standard locations.

    Searches for skills in:
    1. .devorbit/skills/
    2. .claude/skills/
    3. skills/

    Args:
        project_root: Project root directory (default: current directory)

    Returns:
        List of loaded skills
    """
    root = project_root or Path.cwd()
    skills = []

    # Check standard directories
    for dir_name in [".devorbit/skills", ".claude/skills", "skills"]:
        skills_dir = root / dir_name
        skills.extend(load_skills_from_dir(skills_dir))

    return skills


# ============================================================================
# Skill Execution
# ============================================================================


def validate_skill_dependencies(
    skill: Skill,
    available_tools: list[str] | None = None,
    available_skills: list[str] | None = None,
) -> dict[str, Any]:
    """Validate that skill dependencies are satisfied.

    Args:
        skill: Skill to validate
        available_tools: List of available tool names
        available_skills: List of available skill names

    Returns:
        Validation result dictionary
    """
    missing_deps = []

    for dep in skill.dependencies:
        # Check if dependency is a tool or skill
        is_available = False

        if (available_tools and dep in available_tools) or (
            available_skills and dep in available_skills
        ):
            is_available = True

        if not is_available:
            missing_deps.append(dep)

    if missing_deps:
        return {
            "valid": False,
            "missing_dependencies": missing_deps,
            "error": f"Missing dependencies: {', '.join(missing_deps)}",
        }

    return {"valid": True, "missing_dependencies": []}


def execute_skill(
    skill_name: str,
    context: dict[str, Any] | None = None,
    registry: SkillRegistry | None = None,
) -> dict[str, Any]:
    """Execute a skill.

    Args:
        skill_name: Name of skill to execute
        context: Context variables for skill
        registry: Skill registry (default: global registry)

    Returns:
        Execution result dictionary
    """
    reg = registry or _REGISTRY

    # Get skill
    skill = reg.get(skill_name)

    if not skill:
        return {
            "error": f"Skill not found: {skill_name}",
            "skill": skill_name,
        }

    if not skill.enabled:
        return {
            "error": f"Skill is disabled: {skill_name}",
            "skill": skill_name,
        }

    # Build final content with context substituted
    content = skill.content
    ctx = context or {}

    # Simple variable substitution: {var} -> value
    for key, value in ctx.items():
        placeholder = f"{{{key}}}"
        if placeholder in content:
            content = content.replace(placeholder, str(value))

    return {
        "success": True,
        "skill": skill.name,
        "description": skill.description,
        "content": content,
        "tags": skill.tags,
        "version": skill.version,
        "dependencies": skill.dependencies,
    }


# ============================================================================
# Skill Tools (for agent use)
# ============================================================================


@beta_tool
def list_available_skills(
    project_root: str | None = None,
    tag: str | None = None,
) -> dict[str, Any]:
    """List all available skills.

    Args:
        project_root: Project root directory (default: current directory)
        tag: Optional tag to filter skills

    Returns:
        Dictionary with list of available skills
    """
    try:
        root = Path(project_root) if project_root else None

        # Load skills from files
        skills = load_skills(root)

        # Also include registered skills
        registered_skills = _REGISTRY.list_skills(tag)

        # Combine and deduplicate
        all_skills = {}
        for skill in skills + registered_skills:
            if skill.name not in all_skills:
                all_skills[skill.name] = {
                    "name": skill.name,
                    "description": skill.description,
                    "tags": skill.tags,
                    "version": skill.version,
                    "dependencies": skill.dependencies,
                    "source": skill.file_path or "programmatic",
                    "enabled": skill.enabled,
                }

        return {
            "success": True,
            "skills": list(all_skills.values()),
            "count": len(all_skills),
            "filter": {"tag": tag} if tag else {},
        }
    except Exception as e:
        return {
            "error": f"Failed to list skills: {e!s}",
        }


@beta_tool
def run_skill(
    skill_name: str,
    context: dict[str, Any] | None = None,
    project_root: str | None = None,
) -> dict[str, Any]:
    """Execute a skill with optional context.

    Args:
        skill_name: Name of skill to execute
        context: Context variables for skill (for variable substitution)
        project_root: Project root directory (default: current directory)

    Returns:
        Skill execution result
    """
    try:
        root = Path(project_root) if project_root else None

        # Load skills from files
        skills = load_skills(root)
        for skill in skills:
            _REGISTRY.register(skill)

        # Execute skill
        return execute_skill(skill_name, context or {}, _REGISTRY)

    except Exception as e:
        return {
            "error": f"Failed to execute skill: {e!s}",
            "skill": skill_name,
        }


@beta_tool
def validate_skill(
    skill_name: str,
    available_tools: list[str] | None = None,
    available_skills: list[str] | None = None,
    project_root: str | None = None,
) -> dict[str, Any]:
    """Validate a skill's dependencies.

    Args:
        skill_name: Name of skill to validate
        available_tools: List of available tool names
        available_skills: List of available skill names
        project_root: Project root directory (default: current directory)

    Returns:
        Validation result
    """
    try:
        root = Path(project_root) if project_root else None

        # Load skills from files
        skills = load_skills(root)
        for skill in skills:
            _REGISTRY.register(skill)

        # Get skill
        maybe_skill = _REGISTRY.get(skill_name)

        if not maybe_skill:
            return {
                "error": f"Skill not found: {skill_name}",
                "skill": skill_name,
            }

        skill = maybe_skill

        # Validate dependencies
        result = validate_skill_dependencies(skill, available_tools, available_skills)

        return {
            "success": result["valid"],
            "skill": skill_name,
            **result,
        }

    except Exception as e:
        return {
            "error": f"Failed to validate skill: {e!s}",
            "skill": skill_name,
        }


# ============================================================================
# Helper Functions
# ============================================================================


def get_all_skill_tools() -> list[dict[str, Any]]:
    """Get all skill tool definitions.

    Returns:
        List of skill tool definitions for use with Devorbit client
    """
    return [
        list_available_skills.tool_definition,  # type: ignore[attr-defined]
        run_skill.tool_definition,  # type: ignore[attr-defined]
        validate_skill.tool_definition,  # type: ignore[attr-defined]
    ]


def register_skill(
    name: str,
    content: str,
    description: str = "",
    tags: list[str] | None = None,
    version: str = "1.0.0",
    dependencies: list[str] | None = None,
) -> None:
    """Register a skill programmatically.

    Args:
        name: Skill name
        content: Skill instructions/prompts
        description: Skill description
        tags: Skill tags
        version: Skill version
        dependencies: Required tools or skills
    """
    skill = Skill(
        name=name,
        description=description,
        content=content,
        tags=tags or [],
        version=version,
        dependencies=dependencies or [],
    )
    _REGISTRY.register(skill)


def get_skill_registry() -> SkillRegistry:
    """Get the global skill registry.

    Returns:
        Global skill registry
    """
    return _REGISTRY


# Export skill classes and functions
__all__ = [
    "Skill",
    "SkillRegistry",
    "execute_skill",
    "get_all_skill_tools",
    "get_skill_registry",
    "list_available_skills",
    "load_skills",
    "load_skills_from_dir",
    "parse_skill_file",
    "register_skill",
    "run_skill",
    "validate_skill",
    "validate_skill_dependencies",
]
