"""Tests for skills system."""

from pathlib import Path

import pytest

from devorbit._skills import (
    Skill,
    SkillRegistry,
    execute_skill,
    get_all_skill_tools,
    get_skill_registry,
    list_available_skills,
    load_skills,
    load_skills_from_dir,
    parse_skill_file,
    register_skill,
    run_skill,
    validate_skill,
    validate_skill_dependencies,
)


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    """Create a temporary project directory."""
    return tmp_path


@pytest.fixture
def skills_dir(temp_project: Path) -> Path:
    """Create skills directory."""
    skill_dir = temp_project / ".devorbit" / "skills"
    skill_dir.mkdir(parents=True)
    return skill_dir


class TestSkill:
    """Test Skill class."""

    def test_skill_creation(self) -> None:
        """Test creating a skill."""
        skill = Skill(
            name="code-review",
            description="Review code for issues",
            content="Please review the code carefully",
            tags=["code", "quality"],
            version="1.0.0",
            dependencies=["read_file", "grep_code"],
        )

        assert skill.name == "code-review"
        assert skill.description == "Review code for issues"
        assert skill.content == "Please review the code carefully"
        assert skill.tags == ["code", "quality"]
        assert skill.version == "1.0.0"
        assert skill.dependencies == ["read_file", "grep_code"]
        assert skill.enabled is True

    def test_skill_matches_tag(self) -> None:
        """Test skill tag matching."""
        skill = Skill(
            name="test",
            description="Test",
            content="Content",
            tags=["code", "review", "quality"],
        )

        assert skill.matches_tag("code") is True
        assert skill.matches_tag("CODE") is True
        assert skill.matches_tag("review") is True
        assert skill.matches_tag("testing") is False


class TestSkillRegistry:
    """Test SkillRegistry class."""

    def test_register_skill(self) -> None:
        """Test registering a skill."""
        registry = SkillRegistry()
        skill = Skill(name="test", description="Test", content="Content")

        registry.register(skill)

        assert registry.get("test") == skill

    def test_list_skills(self) -> None:
        """Test listing skills."""
        registry = SkillRegistry()
        skill1 = Skill(name="skill1", description="Skill 1", content="Content 1")
        skill2 = Skill(
            name="skill2",
            description="Skill 2",
            content="Content 2",
            tags=["test"],
        )

        registry.register(skill1)
        registry.register(skill2)

        skills = registry.list_skills()
        assert len(skills) == 2
        assert skills[0].name == "skill1"
        assert skills[1].name == "skill2"

    def test_list_skills_by_tag(self) -> None:
        """Test listing skills filtered by tag."""
        registry = SkillRegistry()
        skill1 = Skill(
            name="skill1",
            description="Skill 1",
            content="Content 1",
            tags=["code"],
        )
        skill2 = Skill(
            name="skill2",
            description="Skill 2",
            content="Content 2",
            tags=["test"],
        )

        registry.register(skill1)
        registry.register(skill2)

        skills = registry.list_skills(tag="code")
        assert len(skills) == 1
        assert skills[0].name == "skill1"

    def test_remove_skill(self) -> None:
        """Test removing a skill."""
        registry = SkillRegistry()
        skill = Skill(name="test", description="Test", content="Content")

        registry.register(skill)
        assert registry.get("test") is not None

        result = registry.remove("test")
        assert result is True
        assert registry.get("test") is None

    def test_remove_nonexistent_skill(self) -> None:
        """Test removing a nonexistent skill."""
        registry = SkillRegistry()

        result = registry.remove("nonexistent")
        assert result is False

    def test_clear_registry(self) -> None:
        """Test clearing the registry."""
        registry = SkillRegistry()
        skill1 = Skill(name="skill1", description="Skill 1", content="Content 1")
        skill2 = Skill(name="skill2", description="Skill 2", content="Content 2")

        registry.register(skill1)
        registry.register(skill2)
        assert len(registry.list_skills()) == 2

        registry.clear()
        assert len(registry.list_skills()) == 0


class TestSkillParsing:
    """Test skill file parsing."""

    def test_parse_skill_with_frontmatter(self, skills_dir: Path) -> None:
        """Test parsing skill file with frontmatter."""
        skill_file = skills_dir / "test.md"
        skill_file.write_text(
            """---
name: code-review
description: Review code for quality
tags: [code, quality, review]
version: 1.0.0
dependencies: [read_file, grep_code]
---

Please review the code carefully for:
- Code quality
- Best practices
- Security issues
"""
        )

        skill = parse_skill_file(skill_file)

        assert skill is not None
        assert skill.name == "code-review"
        assert skill.description == "Review code for quality"
        assert skill.tags == ["code", "quality", "review"]
        assert skill.version == "1.0.0"
        assert skill.dependencies == ["read_file", "grep_code"]
        assert "code carefully" in skill.content

    def test_parse_skill_simple_markdown(self, skills_dir: Path) -> None:
        """Test parsing skill file with simple markdown."""
        skill_file = skills_dir / "simple.md"
        skill_file.write_text(
            """# Code Review

Review code for quality issues.

Please review the code carefully.
"""
        )

        skill = parse_skill_file(skill_file)

        assert skill is not None
        assert skill.name == "Code Review"
        assert skill.description == "Review code for quality issues."
        assert "code carefully" in skill.content

    def test_parse_skill_missing_file(self, skills_dir: Path) -> None:
        """Test parsing nonexistent skill file."""
        skill_file = skills_dir / "missing.md"

        skill = parse_skill_file(skill_file)

        assert skill is None

    def test_load_skills_from_dir(self, skills_dir: Path) -> None:
        """Test loading skills from directory."""
        skill1 = skills_dir / "skill1.md"
        skill1.write_text("# Skill 1\n\nDescription\n\nContent")

        skill2 = skills_dir / "skill2.md"
        skill2.write_text("# Skill 2\n\nDescription\n\nContent")

        skills = load_skills_from_dir(skills_dir)

        assert len(skills) == 2
        assert any(s.name == "Skill 1" for s in skills)
        assert any(s.name == "Skill 2" for s in skills)

    def test_load_skills_from_empty_dir(self, temp_project: Path) -> None:
        """Test loading skills from empty directory."""
        empty_dir = temp_project / "empty"
        empty_dir.mkdir()

        skills = load_skills_from_dir(empty_dir)

        assert len(skills) == 0

    def test_load_skills_from_nonexistent_dir(self, temp_project: Path) -> None:
        """Test loading skills from nonexistent directory."""
        nonexistent = temp_project / "nonexistent"

        skills = load_skills_from_dir(nonexistent)

        assert len(skills) == 0


class TestSkillExecution:
    """Test skill execution."""

    def test_execute_skill(self) -> None:
        """Test executing a skill."""
        registry = SkillRegistry()
        skill = Skill(
            name="greet",
            description="Greet user",
            content="Hello, {name}! Welcome to {app}.",
        )
        registry.register(skill)

        result = execute_skill(
            "greet",
            context={"name": "Alice", "app": "Devorbit"},
            registry=registry,
        )

        assert result["success"] is True
        assert result["skill"] == "greet"
        assert "Hello, Alice!" in result["content"]
        assert "Devorbit" in result["content"]

    def test_execute_nonexistent_skill(self) -> None:
        """Test executing nonexistent skill."""
        registry = SkillRegistry()

        result = execute_skill("nonexistent", registry=registry)

        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_execute_disabled_skill(self) -> None:
        """Test executing disabled skill."""
        registry = SkillRegistry()
        skill = Skill(
            name="test",
            description="Test",
            content="Content",
            enabled=False,
        )
        registry.register(skill)

        result = execute_skill("test", registry=registry)

        assert "error" in result
        assert "disabled" in result["error"].lower()

    def test_execute_skill_without_context(self) -> None:
        """Test executing skill without context."""
        registry = SkillRegistry()
        skill = Skill(name="test", description="Test", content="Simple content")
        registry.register(skill)

        result = execute_skill("test", registry=registry)

        assert result["success"] is True
        assert result["content"] == "Simple content"


class TestSkillDependencies:
    """Test skill dependency validation."""

    def test_validate_skill_dependencies_satisfied(self) -> None:
        """Test validating skill with satisfied dependencies."""
        skill = Skill(
            name="test",
            description="Test",
            content="Content",
            dependencies=["read_file", "grep_code"],
        )

        result = validate_skill_dependencies(
            skill,
            available_tools=["read_file", "grep_code", "write_file"],
        )

        assert result["valid"] is True
        assert len(result["missing_dependencies"]) == 0

    def test_validate_skill_dependencies_missing(self) -> None:
        """Test validating skill with missing dependencies."""
        skill = Skill(
            name="test",
            description="Test",
            content="Content",
            dependencies=["read_file", "missing_tool"],
        )

        result = validate_skill_dependencies(
            skill,
            available_tools=["read_file", "grep_code"],
        )

        assert result["valid"] is False
        assert "missing_tool" in result["missing_dependencies"]
        assert "error" in result

    def test_validate_skill_no_dependencies(self) -> None:
        """Test validating skill with no dependencies."""
        skill = Skill(
            name="test",
            description="Test",
            content="Content",
        )

        result = validate_skill_dependencies(skill)

        assert result["valid"] is True
        assert len(result["missing_dependencies"]) == 0


class TestSkillTools:
    """Test skill tools for agent use."""

    def test_list_available_skills(self, skills_dir: Path) -> None:
        """Test listing available skills."""
        skill_file = skills_dir / "test.md"
        skill_file.write_text("# Test Skill\n\nDescription\n\nContent")

        result = list_available_skills(project_root=str(skills_dir.parent.parent))

        assert result["success"] is True
        assert result["count"] >= 1
        assert any(s["name"] == "Test Skill" for s in result["skills"])

    def test_run_skill(self, skills_dir: Path) -> None:
        """Test running a skill."""
        skill_file = skills_dir / "greet.md"
        skill_file.write_text("# Greet\n\nGreet user\n\nHello, {name}!")

        result = run_skill(
            "Greet",
            context={"name": "Bob"},
            project_root=str(skills_dir.parent.parent),
        )

        assert result["success"] is True
        assert "Hello, Bob!" in result["content"]

    def test_validate_skill_tool(self, skills_dir: Path) -> None:
        """Test validating a skill."""
        skill_file = skills_dir / "test.md"
        skill_file.write_text(
            """---
name: test-skill
dependencies: [read_file]
---

Content
"""
        )

        result = validate_skill(
            "test-skill",
            available_tools=["read_file", "write_file"],
            project_root=str(skills_dir.parent.parent),
        )

        assert result["success"] is True

    def test_get_all_skill_tools(self) -> None:
        """Test getting all skill tool definitions."""
        tools = get_all_skill_tools()

        assert len(tools) == 3
        assert any(t["name"] == "list_available_skills" for t in tools)
        assert any(t["name"] == "run_skill" for t in tools)
        assert any(t["name"] == "validate_skill" for t in tools)


class TestSkillHelpers:
    """Test skill helper functions."""

    def test_register_skill(self) -> None:
        """Test programmatically registering a skill."""
        registry = get_skill_registry()

        register_skill(
            name="programmatic",
            content="Test content",
            description="Test description",
            tags=["test"],
            version="2.0.0",
            dependencies=["tool1"],
        )

        skill = registry.get("programmatic")
        assert skill is not None
        assert skill.name == "programmatic"
        assert skill.description == "Test description"
        assert skill.tags == ["test"]
        assert skill.version == "2.0.0"
        assert skill.dependencies == ["tool1"]

        # Cleanup
        registry.remove("programmatic")

    def test_get_skill_registry(self) -> None:
        """Test getting the global skill registry."""
        registry = get_skill_registry()

        assert isinstance(registry, SkillRegistry)


class TestSkillIntegration:
    """Integration tests for skills system."""

    def test_complete_skill_workflow(self, skills_dir: Path) -> None:
        """Test complete workflow from file to execution."""
        # Create skill file
        skill_file = skills_dir / "workflow.md"
        skill_file.write_text(
            """---
name: workflow-test
description: Test workflow
tags: [test]
version: 1.0.0
---

Process {input} and produce {output}.
"""
        )

        # Load skills
        skills = load_skills(skills_dir.parent.parent)
        workflow_skill = next((s for s in skills if s.name == "workflow-test"), None)

        assert workflow_skill is not None
        assert workflow_skill.description == "Test workflow"
        assert workflow_skill.tags == ["test"]

        # Register and execute
        registry = SkillRegistry()
        registry.register(workflow_skill)

        result = execute_skill(
            "workflow-test",
            context={"input": "data", "output": "result"},
            registry=registry,
        )

        assert result["success"] is True
        assert "data" in result["content"]
        assert "result" in result["content"]
