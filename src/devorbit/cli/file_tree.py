"""Interactive file tree browser with previews."""

from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.table import Table
    from rich.tree import Tree

    HAS_RICH = True
except ImportError:
    HAS_RICH = False


class FileTreeBrowser:
    """Interactive file tree browser with previews."""

    def __init__(self, root_path: Path, no_color: bool = False) -> None:
        """Initialize file tree browser.

        Args:
            root_path: Root directory path
            no_color: Disable colored output
        """
        self.root_path = root_path
        self.no_color = no_color
        self.console = Console(no_color=no_color) if HAS_RICH else None
        self.max_depth = 3
        self.show_hidden = False

    def render_tree(self, path: Path | None = None, max_depth: int = 3) -> Tree | None:
        """Render file tree.

        Args:
            path: Starting path (default: root_path)
            max_depth: Maximum depth to display

        Returns:
            Rich Tree object or None
        """
        if not HAS_RICH:
            return None

        path = path or self.root_path
        self.max_depth = max_depth

        # Create root tree node
        tree = Tree(
            f"[bold cyan]{path.name or str(path)}[/bold cyan]",
            guide_style="dim",
        )

        # Build tree recursively
        self._build_tree(path, tree, 0)

        return tree

    def _build_tree(self, path: Path, tree: Tree, depth: int) -> None:
        """Build tree recursively.

        Args:
            path: Current path
            tree: Tree node
            depth: Current depth
        """
        if depth >= self.max_depth:
            return

        try:
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
        except PermissionError:
            return

        for item in items:
            # Skip hidden files unless enabled
            if not self.show_hidden and item.name.startswith("."):
                continue

            # Skip common ignore patterns
            if item.name in ("__pycache__", "node_modules", ".git", ".venv", "venv"):
                continue

            if item.is_dir():
                # Directory node
                branch = tree.add(f"[bold blue]📁 {item.name}[/bold blue]")
                self._build_tree(item, branch, depth + 1)
            else:
                # File node with icon
                icon = self._get_file_icon(item)
                color = self._get_file_color(item)
                tree.add(f"[{color}]{icon} {item.name}[/{color}]")

    def _get_file_icon(self, path: Path) -> str:
        """Get icon for file type.

        Args:
            path: File path

        Returns:
            Icon string
        """
        ext = path.suffix.lower()

        icons = {
            ".py": "🐍",
            ".js": "📜",
            ".ts": "📘",
            ".jsx": "⚛️",
            ".tsx": "⚛️",
            ".html": "🌐",
            ".css": "🎨",
            ".json": "📋",
            ".md": "📝",
            ".yml": "⚙️",
            ".yaml": "⚙️",
            ".toml": "⚙️",
            ".txt": "📄",
            ".pdf": "📕",
            ".png": "🖼️",
            ".jpg": "🖼️",
            ".jpeg": "🖼️",
            ".gif": "🖼️",
            ".svg": "🖼️",
        }

        return icons.get(ext, "📄")

    def _get_file_color(self, path: Path) -> str:
        """Get color for file type.

        Args:
            path: File path

        Returns:
            Color name
        """
        ext = path.suffix.lower()

        colors = {
            ".py": "green",
            ".js": "yellow",
            ".ts": "blue",
            ".jsx": "cyan",
            ".tsx": "cyan",
            ".html": "magenta",
            ".css": "magenta",
            ".json": "yellow",
            ".md": "white",
            ".yml": "yellow",
            ".yaml": "yellow",
            ".toml": "yellow",
        }

        return colors.get(ext, "white")

    def display_tree(self, path: Path | None = None, max_depth: int = 3) -> None:
        """Display file tree.

        Args:
            path: Starting path
            max_depth: Maximum depth
        """
        if not HAS_RICH or self.console is None:
            self._display_plain_tree(path or self.root_path, 0, max_depth)
            return

        tree = self.render_tree(path, max_depth)
        if tree:
            self.console.print(tree)

    def _display_plain_tree(self, path: Path, depth: int, max_depth: int) -> None:
        """Display tree in plain text.

        Args:
            path: Current path
            depth: Current depth
            max_depth: Maximum depth
        """
        if depth >= max_depth:
            return

        indent = "  " * depth

        try:
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
        except PermissionError:
            return

        for item in items:
            if not self.show_hidden and item.name.startswith("."):
                continue

            if item.name in ("__pycache__", "node_modules", ".git", ".venv"):
                continue

            if item.is_dir():
                print(f"{indent}📁 {item.name}/")
                self._display_plain_tree(item, depth + 1, max_depth)
            else:
                icon = self._get_file_icon(item)
                print(f"{indent}{icon} {item.name}")

    def preview_file(self, file_path: Path, max_lines: int = 20) -> Panel | None:
        """Preview file contents.

        Args:
            file_path: File to preview
            max_lines: Maximum lines to show

        Returns:
            Rich Panel or None
        """
        if not HAS_RICH or self.console is None:
            return None

        if not file_path.exists() or not file_path.is_file():
            return None

        try:
            # Read file
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            lines = content.splitlines()

            # Truncate if needed
            if len(lines) > max_lines:
                display_content = "\n".join(lines[:max_lines])
                display_content += f"\n... ({len(lines) - max_lines} more lines)"
            else:
                display_content = content

            # Determine language for syntax highlighting
            ext = file_path.suffix.lower()
            language_map = {
                ".py": "python",
                ".js": "javascript",
                ".ts": "typescript",
                ".jsx": "jsx",
                ".tsx": "tsx",
                ".html": "html",
                ".css": "css",
                ".json": "json",
                ".md": "markdown",
                ".yml": "yaml",
                ".yaml": "yaml",
                ".toml": "toml",
                ".sh": "bash",
            }
            language = language_map.get(ext, "text")

            # Create syntax-highlighted content
            syntax = Syntax(display_content, language, theme="monokai", line_numbers=True)

            # Create panel
            return Panel(
                syntax,
                title=f"[bold cyan]{file_path.name}[/bold cyan]",
                subtitle=f"[dim]{file_path.relative_to(self.root_path)}[/dim]",
                border_style="cyan",
            )

        except Exception:
            return None

    def display_file_list(self, files: list[Path]) -> None:
        """Display list of files with details.

        Args:
            files: List of file paths
        """
        if not HAS_RICH or self.console is None:
            # Plain text fallback
            for file in files:
                print(f"  {file}")
            return

        # Create table
        table = Table(
            show_header=True,
            header_style="bold cyan",
            box=None,
            padding=(0, 1),
        )

        table.add_column("File", style="white")
        table.add_column("Size", justify="right", style="yellow")
        table.add_column("Type", style="blue")

        for file in files:
            if not file.exists():
                continue

            # Get file info
            size = file.stat().st_size
            size_str = self._format_size(size)
            file_type = file.suffix.upper()[1:] if file.suffix else "File"

            # Get icon and color
            icon = self._get_file_icon(file)
            color = self._get_file_color(file)

            # Add row
            table.add_row(
                f"[{color}]{icon} {file.name}[/{color}]",
                size_str,
                file_type,
            )

        panel = Panel(
            table,
            title="[bold cyan]Files[/bold cyan]",
            border_style="cyan",
        )

        self.console.print(panel)

    def _format_size(self, size: int) -> str:
        """Format file size.

        Args:
            size: Size in bytes

        Returns:
            Formatted size string
        """
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


__all__ = ["FileTreeBrowser"]
