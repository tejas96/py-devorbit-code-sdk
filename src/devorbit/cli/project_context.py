"""Project type detection and context analysis.

This module provides intelligent project type detection for various languages
and frameworks, similar to Claude Code CLI's workspace intelligence.
"""

import json
import tomllib
from pathlib import Path

from pydantic import BaseModel, Field


class ProjectInfo(BaseModel):
    """Base class for project information."""

    project_type: str
    language: str
    frameworks: list[str] = Field(default_factory=list)
    dependencies: dict[str, str] = Field(default_factory=dict)
    root_path: Path
    config_files: list[str] = Field(default_factory=list)

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


class PythonProject(ProjectInfo):
    """Python project information."""

    project_type: str = "python"
    language: str = "python"
    package_name: str | None = None
    python_version: str | None = None
    build_system: str | None = None  # poetry, setuptools, flit, etc


class JavaScriptProject(ProjectInfo):
    """JavaScript/Node.js project information."""

    project_type: str = "javascript"
    language: str = "javascript"
    package_name: str | None = None
    node_version: str | None = None
    package_manager: str | None = None  # npm, yarn, pnpm


class TypeScriptProject(ProjectInfo):
    """TypeScript project information."""

    project_type: str = "typescript"
    language: str = "typescript"
    package_name: str | None = None
    ts_version: str | None = None


class ReactProject(ProjectInfo):
    """React project information."""

    project_type: str = "react"
    language: str = "javascript"
    frameworks: list[str] = Field(default_factory=lambda: ["react"])
    package_name: str | None = None
    react_version: str | None = None


class NextJsProject(ProjectInfo):
    """Next.js project information."""

    project_type: str = "nextjs"
    language: str = "javascript"
    frameworks: list[str] = Field(default_factory=lambda: ["react", "nextjs"])
    package_name: str | None = None
    next_version: str | None = None


class GoProject(ProjectInfo):
    """Go project information."""

    project_type: str = "go"
    language: str = "go"
    module_name: str | None = None
    go_version: str | None = None


class RustProject(ProjectInfo):
    """Rust project information."""

    project_type: str = "rust"
    language: str = "rust"
    package_name: str | None = None
    rust_version: str | None = None


class ProjectDetector:
    """Detect project type and extract context information."""

    def __init__(self, path: Path | None = None):
        """Initialize project detector.

        Args:
            path: Project root path (default: current working directory)
        """
        self.path = path or Path.cwd()

    def detect_project_type(self) -> ProjectInfo:  # noqa: PLR0911
        """Detect project type and return project information.

        Returns:
            ProjectInfo subclass with detected project details
        """
        # Python detection
        if (self.path / "pyproject.toml").exists():
            return self._parse_python_project()
        if (self.path / "setup.py").exists() or (self.path / "requirements.txt").exists():
            return self._parse_python_legacy_project()

        # JavaScript/Node detection
        if (self.path / "package.json").exists():
            return self._parse_javascript_project()

        # TypeScript detection (after package.json check)
        if (self.path / "tsconfig.json").exists():
            return self._parse_typescript_project()

        # Go detection
        if (self.path / "go.mod").exists():
            return self._parse_go_project()

        # Rust detection
        if (self.path / "Cargo.toml").exists():
            return self._parse_rust_project()

        # Java detection
        if (self.path / "pom.xml").exists() or (self.path / "build.gradle").exists():
            return self._parse_java_project()

        # Default: Unknown project
        return ProjectInfo(
            project_type="unknown",
            language="unknown",
            root_path=self.path,
            config_files=[],
        )

    def _parse_python_project(self) -> PythonProject:  # noqa: PLR0912
        """Parse Python project with pyproject.toml."""
        config_files = ["pyproject.toml"]
        dependencies: dict[str, str] = {}
        frameworks: list[str] = []
        package_name: str | None = None
        python_version: str | None = None
        build_system: str | None = None

        pyproject_path = self.path / "pyproject.toml"
        try:
            with pyproject_path.open("rb") as f:
                data = tomllib.load(f)

            # Extract project name
            if "project" in data and "name" in data["project"]:
                package_name = data["project"]["name"]
            elif "tool" in data and "poetry" in data["tool"] and "name" in data["tool"]["poetry"]:
                package_name = data["tool"]["poetry"]["name"]

            # Extract Python version
            if "project" in data and "requires-python" in data["project"]:
                python_version = data["project"]["requires-python"]
            elif (
                "tool" in data
                and "poetry" in data["tool"]
                and "dependencies" in data["tool"]["poetry"]
                and "python" in data["tool"]["poetry"]["dependencies"]
            ):
                python_version = str(data["tool"]["poetry"]["dependencies"]["python"])

            # Detect build system
            if "build-system" in data:
                build_backend = data["build-system"].get("build-backend", "")
                if "poetry" in build_backend:
                    build_system = "poetry"
                elif "flit" in build_backend:
                    build_system = "flit"
                elif "setuptools" in build_backend:
                    build_system = "setuptools"
                elif "hatch" in build_backend:
                    build_system = "hatchling"

            # Extract dependencies
            if "project" in data and "dependencies" in data["project"]:
                for dep in data["project"]["dependencies"]:
                    if isinstance(dep, str):
                        parts = dep.split(">=")
                        if len(parts) == 2:
                            dependencies[parts[0].strip()] = parts[1].strip()
                        else:
                            dependencies[dep.strip()] = "*"

            # Poetry dependencies
            if (
                "tool" in data
                and "poetry" in data["tool"]
                and "dependencies" in data["tool"]["poetry"]
            ):
                for name, version in data["tool"]["poetry"]["dependencies"].items():
                    if name != "python":
                        dependencies[name] = str(version)

            # Detect frameworks
            if "django" in dependencies:
                frameworks.append("django")
            if "flask" in dependencies:
                frameworks.append("flask")
            if "fastapi" in dependencies:
                frameworks.append("fastapi")

        except Exception:
            pass

        return PythonProject(
            root_path=self.path,
            config_files=config_files,
            package_name=package_name,
            python_version=python_version,
            build_system=build_system,
            frameworks=frameworks,
            dependencies=dependencies,
        )

    def _parse_python_legacy_project(self) -> PythonProject:
        """Parse Python project with setup.py or requirements.txt."""
        config_files = []
        dependencies: dict[str, str] = {}
        frameworks: list[str] = []

        if (self.path / "setup.py").exists():
            config_files.append("setup.py")

        if (self.path / "requirements.txt").exists():
            config_files.append("requirements.txt")
            req_file = self.path / "requirements.txt"
            try:
                with req_file.open(encoding="utf-8") as f:
                    for raw_line in f:
                        line = raw_line.strip()
                        if line and not line.startswith("#"):
                            if ">=" in line:
                                parts = line.split(">=")
                                dependencies[parts[0].strip()] = parts[1].strip()
                            elif "==" in line:
                                parts = line.split("==")
                                dependencies[parts[0].strip()] = parts[1].strip()
                            else:
                                dependencies[line] = "*"

                # Detect frameworks
                if "django" in dependencies:
                    frameworks.append("django")
                if "flask" in dependencies:
                    frameworks.append("flask")
                if "fastapi" in dependencies:
                    frameworks.append("fastapi")
            except Exception:
                pass

        return PythonProject(
            root_path=self.path,
            config_files=config_files,
            frameworks=frameworks,
            dependencies=dependencies,
            build_system="setuptools",
        )

    def _parse_javascript_project(self) -> JavaScriptProject | ReactProject | NextJsProject:
        """Parse JavaScript/Node.js project with package.json."""
        config_files = ["package.json"]
        dependencies: dict[str, str] = {}
        package_name: str | None = None
        frameworks: list[str] = []

        package_json_path = self.path / "package.json"
        try:
            with package_json_path.open(encoding="utf-8") as f:
                data = json.load(f)

            package_name = data.get("name")

            # Merge dependencies and devDependencies
            all_deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            dependencies = all_deps

            # Detect specific frameworks
            if "next" in all_deps:
                return NextJsProject(
                    root_path=self.path,
                    config_files=config_files,
                    package_name=package_name,
                    dependencies=dependencies,
                    next_version=all_deps.get("next"),
                )

            if "react" in all_deps:
                return ReactProject(
                    root_path=self.path,
                    config_files=config_files,
                    package_name=package_name,
                    dependencies=dependencies,
                    react_version=all_deps.get("react"),
                )

            # Detect other frameworks
            if "vue" in all_deps:
                frameworks.append("vue")
            if "angular" in all_deps or "@angular/core" in all_deps:
                frameworks.append("angular")
            if "express" in all_deps:
                frameworks.append("express")
            if "nestjs" in all_deps or "@nestjs/core" in all_deps:
                frameworks.append("nestjs")

        except Exception:
            pass

        return JavaScriptProject(
            root_path=self.path,
            config_files=config_files,
            package_name=package_name,
            dependencies=dependencies,
            frameworks=frameworks,
        )

    def _parse_typescript_project(self) -> TypeScriptProject:
        """Parse TypeScript project with tsconfig.json."""
        config_files = ["tsconfig.json"]
        dependencies: dict[str, str] = {}

        # Also check package.json if it exists
        if (self.path / "package.json").exists():
            config_files.append("package.json")
            pkg_json = self.path / "package.json"
            try:
                with pkg_json.open(encoding="utf-8") as f:
                    data = json.load(f)
                dependencies = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            except Exception:
                pass

        return TypeScriptProject(
            root_path=self.path,
            config_files=config_files,
            dependencies=dependencies,
        )

    def _parse_go_project(self) -> GoProject:
        """Parse Go project with go.mod."""
        config_files = ["go.mod"]
        module_name: str | None = None
        go_version: str | None = None
        dependencies: dict[str, str] = {}

        go_mod_path = self.path / "go.mod"
        try:
            with go_mod_path.open(encoding="utf-8") as f:
                for raw_line in f:
                    line = raw_line.strip()
                    if line.startswith("module "):
                        module_name = line.split("module ")[1]
                    elif line.startswith("go "):
                        go_version = line.split("go ")[1]
                    elif line.startswith("require "):
                        # Simple require line
                        parts = line.split()
                        if len(parts) >= 3:
                            dependencies[parts[1]] = parts[2]
        except Exception:
            pass

        return GoProject(
            root_path=self.path,
            config_files=config_files,
            module_name=module_name,
            go_version=go_version,
            dependencies=dependencies,
        )

    def _parse_rust_project(self) -> RustProject:
        """Parse Rust project with Cargo.toml."""
        config_files = ["Cargo.toml"]
        package_name: str | None = None
        rust_version: str | None = None
        dependencies: dict[str, str] = {}

        cargo_toml_path = self.path / "Cargo.toml"
        try:
            with cargo_toml_path.open("rb") as f:
                data = tomllib.load(f)

            if "package" in data:
                package_name = data["package"].get("name")
                rust_version = data["package"].get("rust-version")

            if "dependencies" in data:
                for name, version in data["dependencies"].items():
                    if isinstance(version, str):
                        dependencies[name] = version
                    elif isinstance(version, dict) and "version" in version:
                        dependencies[name] = version["version"]
        except Exception:
            pass

        return RustProject(
            root_path=self.path,
            config_files=config_files,
            package_name=package_name,
            rust_version=rust_version,
            dependencies=dependencies,
        )

    def _parse_java_project(self) -> ProjectInfo:
        """Parse Java project with Maven or Gradle."""
        config_files = []
        if (self.path / "pom.xml").exists():
            config_files.append("pom.xml")
        if (self.path / "build.gradle").exists():
            config_files.append("build.gradle")

        return ProjectInfo(
            project_type="java",
            language="java",
            root_path=self.path,
            config_files=config_files,
        )
