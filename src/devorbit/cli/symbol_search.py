"""Symbol search and indexing for code navigation.

This module provides symbol search capabilities similar to Claude Code CLI,
allowing quick navigation to functions, classes, and other code symbols.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

try:
    from rich.console import Console
    from rich.table import Table

    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    Console = None
    Table = None


@dataclass
class Symbol:
    """Represents a code symbol (function, class, method, etc)."""

    name: str
    kind: str  # function, class, method, variable, constant
    file_path: Path
    line_number: int
    context: str  # Surrounding code for context
    language: str  # python, javascript, etc


class SymbolIndex:
    """Index of code symbols for fast searching."""

    def __init__(self):
        """Initialize symbol index."""
        self.symbols: list[Symbol] = []
        self.index_by_name: dict[str, list[Symbol]] = {}
        self.index_by_kind: dict[str, list[Symbol]] = {}
        self.index_by_file: dict[Path, list[Symbol]] = {}

    def add_symbol(self, symbol: Symbol) -> None:
        """Add a symbol to the index.

        Args:
            symbol: Symbol to add
        """
        self.symbols.append(symbol)

        # Index by name
        if symbol.name not in self.index_by_name:
            self.index_by_name[symbol.name] = []
        self.index_by_name[symbol.name].append(symbol)

        # Index by kind
        if symbol.kind not in self.index_by_kind:
            self.index_by_kind[symbol.kind] = []
        self.index_by_kind[symbol.kind].append(symbol)

        # Index by file
        if symbol.file_path not in self.index_by_file:
            self.index_by_file[symbol.file_path] = []
        self.index_by_file[symbol.file_path].append(symbol)

    def search(
        self,
        query: str,
        kind: str | None = None,
        file_path: Path | None = None,
    ) -> list[Symbol]:
        """Search for symbols.

        Args:
            query: Search query (can be partial name or regex)
            kind: Filter by symbol kind
            file_path: Filter by file path

        Returns:
            List of matching symbols
        """
        results: list[Symbol] = []

        # Start with all symbols or filter by kind/file
        candidates = self.symbols

        if kind:
            candidates = self.index_by_kind.get(kind, [])

        if file_path:
            file_symbols = self.index_by_file.get(file_path, [])
            candidates = [s for s in candidates if s in file_symbols] if kind else file_symbols

        # Filter by query
        query_lower = query.lower()
        for symbol in candidates:
            if query_lower in symbol.name.lower():
                results.append(symbol)

        return results

    def get_symbols_by_name(self, name: str) -> list[Symbol]:
        """Get all symbols with exact name.

        Args:
            name: Symbol name

        Returns:
            List of symbols with matching name
        """
        return self.index_by_name.get(name, [])

    def get_symbols_by_kind(self, kind: str) -> list[Symbol]:
        """Get all symbols of a specific kind.

        Args:
            kind: Symbol kind

        Returns:
            List of symbols of that kind
        """
        return self.index_by_kind.get(kind, [])

    def get_symbols_in_file(self, file_path: Path) -> list[Symbol]:
        """Get all symbols in a file.

        Args:
            file_path: File path

        Returns:
            List of symbols in that file
        """
        return self.index_by_file.get(file_path, [])

    def clear(self) -> None:
        """Clear the index."""
        self.symbols.clear()
        self.index_by_name.clear()
        self.index_by_kind.clear()
        self.index_by_file.clear()


class SymbolParser:
    """Parse code files to extract symbols."""

    # Python patterns
    PYTHON_PATTERNS: ClassVar[dict[str, re.Pattern]] = {
        "class": re.compile(r"^class\s+(\w+)", re.MULTILINE),
        "function": re.compile(r"^def\s+(\w+)", re.MULTILINE),
        "method": re.compile(r"^\s+def\s+(\w+)", re.MULTILINE),
    }

    # JavaScript/TypeScript patterns
    JS_PATTERNS: ClassVar[dict[str, re.Pattern]] = {
        "class": re.compile(r"class\s+(\w+)", re.MULTILINE),
        "function": re.compile(r"function\s+(\w+)", re.MULTILINE),
        "const": re.compile(r"const\s+(\w+)\s*=", re.MULTILINE),
        "let": re.compile(r"let\s+(\w+)\s*=", re.MULTILINE),
        "method": re.compile(r"(\w+)\s*\([^)]*\)\s*\{", re.MULTILINE),
    }

    # Go patterns
    GO_PATTERNS: ClassVar[dict[str, re.Pattern]] = {
        "function": re.compile(r"func\s+(\w+)", re.MULTILINE),
        "type": re.compile(r"type\s+(\w+)\s+struct", re.MULTILINE),
        "method": re.compile(r"func\s+\(\w+\s+\*?\w+\)\s+(\w+)", re.MULTILINE),
    }

    # Rust patterns
    RUST_PATTERNS: ClassVar[dict[str, re.Pattern]] = {
        "function": re.compile(r"fn\s+(\w+)", re.MULTILINE),
        "struct": re.compile(r"struct\s+(\w+)", re.MULTILINE),
        "enum": re.compile(r"enum\s+(\w+)", re.MULTILINE),
        "trait": re.compile(r"trait\s+(\w+)", re.MULTILINE),
    }

    def __init__(self):
        """Initialize symbol parser."""
        self.language_patterns = {
            "python": self.PYTHON_PATTERNS,
            "javascript": self.JS_PATTERNS,
            "typescript": self.JS_PATTERNS,
            "go": self.GO_PATTERNS,
            "rust": self.RUST_PATTERNS,
        }

    def parse_file(self, file_path: Path) -> list[Symbol]:
        """Parse a file and extract symbols.

        Args:
            file_path: Path to file

        Returns:
            List of symbols found in file
        """
        # Detect language from extension
        language = self._detect_language(file_path)
        if not language:
            return []

        # Get patterns for language
        patterns = self.language_patterns.get(language)
        if not patterns:
            return []

        # Read file
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            return []

        # Extract symbols
        symbols: list[Symbol] = []
        lines = content.splitlines()

        for kind, pattern in patterns.items():
            for match in pattern.finditer(content):
                name = match.group(1)
                start_pos = match.start()

                # Find line number
                line_number = content[:start_pos].count("\n") + 1

                # Get context (3 lines around the match)
                context_start = max(0, line_number - 2)
                context_end = min(len(lines), line_number + 2)
                context = "\n".join(lines[context_start:context_end])

                symbol = Symbol(
                    name=name,
                    kind=kind,
                    file_path=file_path,
                    line_number=line_number,
                    context=context,
                    language=language,
                )
                symbols.append(symbol)

        return symbols

    def _detect_language(self, file_path: Path) -> str | None:
        """Detect programming language from file extension.

        Args:
            file_path: Path to file

        Returns:
            Language name or None
        """
        extension = file_path.suffix.lower()

        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".go": "go",
            ".rs": "rust",
        }

        return language_map.get(extension)


class SymbolSearchEngine:
    """High-level symbol search engine."""

    def __init__(self, root_path: Path | None = None, console: Any | None = None):
        """Initialize symbol search engine.

        Args:
            root_path: Root directory to search (default: current directory)
            console: Rich console for output
        """
        self.root_path = root_path or Path.cwd()
        self.console = console

        if HAS_RICH and console is None:
            self.console = Console()

        self.index = SymbolIndex()
        self.parser = SymbolParser()

    def index_directory(
        self,
        directory: Path | None = None,
        patterns: list[str] | None = None,
    ) -> int:
        """Index all code files in a directory.

        Args:
            directory: Directory to index (default: root_path)
            patterns: Glob patterns for files to include

        Returns:
            Number of symbols indexed
        """
        if directory is None:
            directory = self.root_path

        if patterns is None:
            patterns = ["**/*.py", "**/*.js", "**/*.ts", "**/*.go", "**/*.rs"]

        # Clear existing index
        self.index.clear()

        # Index files
        for pattern in patterns:
            for file_path in directory.glob(pattern):
                if file_path.is_file():
                    symbols = self.parser.parse_file(file_path)
                    for symbol in symbols:
                        self.index.add_symbol(symbol)

        return len(self.index.symbols)

    def search(
        self,
        query: str,
        kind: str | None = None,
        file_path: Path | None = None,
        limit: int | None = 50,
    ) -> list[Symbol]:
        """Search for symbols.

        Args:
            query: Search query
            kind: Filter by kind
            file_path: Filter by file
            limit: Max results to return

        Returns:
            List of matching symbols
        """
        results = self.index.search(query, kind=kind, file_path=file_path)

        if limit:
            results = results[:limit]

        return results

    def render_results(self, results: list[Symbol]) -> None:
        """Render search results.

        Args:
            results: Search results to render
        """
        if HAS_RICH and self.console:
            self._render_results_rich(results)
        else:
            self._render_results_plain(results)

    def _render_results_rich(self, results: list[Symbol]) -> None:
        """Render results with Rich table.

        Args:
            results: Search results
        """
        if not self.console:
            return

        table = Table(title=f"Found {len(results)} symbols")
        table.add_column("Symbol", style="cyan bold")
        table.add_column("Kind", style="yellow")
        table.add_column("File", style="dim")
        table.add_column("Line", style="green")

        for symbol in results:
            table.add_row(
                symbol.name,
                symbol.kind,
                str(symbol.file_path.relative_to(self.root_path)),
                str(symbol.line_number),
            )

        self.console.print(table)

    def _render_results_plain(self, results: list[Symbol]) -> None:
        """Render results with plain text.

        Args:
            results: Search results
        """
        print(f"\nFound {len(results)} symbols:")
        print("─" * 80)
        print(f"{'Symbol':<30} {'Kind':<15} {'File':<25} {'Line'}")
        print("─" * 80)

        for symbol in results:
            file_rel = str(symbol.file_path.relative_to(self.root_path))
            print(f"{symbol.name:<30} {symbol.kind:<15} {file_rel:<25} {symbol.line_number}")

        print("─" * 80)


__all__ = ["Symbol", "SymbolIndex", "SymbolParser", "SymbolSearchEngine"]
