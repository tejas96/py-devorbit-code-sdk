"""Project bootstrapper for auto-generating folder structures."""

from pathlib import Path
from typing import Any, ClassVar

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.tree import Tree

    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    Table = None  # type: ignore[assignment, misc]


class ProjectBootstrapper:
    """Auto-generate project folder structures from templates."""

    # Project templates
    TEMPLATES: ClassVar[dict[str, Any]] = {
        "python": {
            "name": "Python Project",
            "description": "Modern Python project with Poetry",
            "structure": {
                "src": {
                    "{{project_name}}": {
                        "__init__.py": "# {{project_name}} package",
                        "main.py": "def main():\n    print('Hello from {{project_name}}')",
                    }
                },
                "tests": {"__init__.py": "", "test_main.py": "def test_example():\n    assert True"},
                "pyproject.toml": """[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"

[tool.poetry]
name = "{{project_name}}"
version = "0.1.0"
description = "{{description}}"
authors = ["Your Name <you@example.com>"]

[tool.poetry.dependencies]
python = "^3.12"
""",
                "README.md": "# {{project_name}}\n\n{{description}}",
                ".gitignore": """__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
dist/
build/
*.egg-info/
""",
            },
        },
        "web": {
            "name": "Web App (HTML/CSS/JS)",
            "description": "Static web application",
            "structure": {
                "src": {
                    "index.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{project_name}}</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <h1>{{project_name}}</h1>
    <script src="app.js"></script>
</body>
</html>""",
                    "styles.css": """* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: system-ui, -apple-system, sans-serif;
    padding: 2rem;
}""",
                    "app.js": "console.log('{{project_name}} loaded');",
                },
                "README.md": "# {{project_name}}\n\n{{description}}",
            },
        },
        "pwa": {
            "name": "Progressive Web App",
            "description": "PWA with service worker",
            "structure": {
                "index.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="theme-color" content="#6366f1">
    <title>{{project_name}}</title>
    <link rel="manifest" href="manifest.json">
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <h1>{{project_name}}</h1>
    <script src="app.js"></script>
    <script>
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/service-worker.js');
        }
    </script>
</body>
</html>""",
                "manifest.json": """{
  "name": "{{project_name}}",
  "short_name": "{{project_name}}",
  "description": "{{description}}",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#6366f1",
  "icons": []
}""",
                "service-worker.js": """const CACHE_NAME = '{{project_name}}-v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/styles.css',
  '/app.js'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});""",
                "styles.css": """* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: system-ui, -apple-system, sans-serif;
    padding: 2rem;
}""",
                "app.js": "console.log('{{project_name}} PWA loaded');",
                "README.md": "# {{project_name}}\n\n{{description}}\n\n## PWA Features\n- Offline support\n- Install to home screen",
            },
        },
        "react": {
            "name": "React App",
            "description": "React application with Vite",
            "structure": {
                "src": {
                    "App.jsx": """import { useState } from 'react'
import './App.css'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="App">
      <h1>{{project_name}}</h1>
      <button onClick={() => setCount(count + 1)}>
        Count: {count}
      </button>
    </div>
  )
}

export default App""",
                    "main.jsx": """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)""",
                    "App.css": ".App { text-align: center; padding: 2rem; }",
                    "index.css": "* { margin: 0; padding: 0; box-sizing: border-box; }",
                },
                "index.html": """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{{project_name}}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>""",
                "package.json": """{
  "name": "{{project_name}}",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.0.0",
    "vite": "^4.3.0"
  }
}""",
                "vite.config.js": """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})""",
                "README.md": "# {{project_name}}\n\n{{description}}",
            },
        },
    }

    def __init__(self, console: Console | None = None) -> None:
        """Initialize project bootstrapper.

        Args:
            console: Rich console instance
        """
        self.console = console or (Console() if HAS_RICH else None)

    def list_templates(self) -> None:
        """List available project templates."""
        if not HAS_RICH or self.console is None or Table is None:
            print("\nAvailable Templates:")
            for key, template in self.TEMPLATES.items():
                print(f"  {key}: {template['name']} - {template['description']}")
            return

        table = Table(title="Project Templates", show_header=True)
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="bold white")
        table.add_column("Description", style="dim")

        for key, template in self.TEMPLATES.items():
            table.add_row(key, template["name"], template["description"])

        self.console.print(table)

    def bootstrap(
        self,
        template_id: str,
        project_name: str,
        target_dir: Path,
        description: str = "",
    ) -> bool:
        """Bootstrap a new project from template.

        Args:
            template_id: Template identifier
            project_name: Name of the project
            target_dir: Target directory
            description: Project description

        Returns:
            True if successful
        """
        if template_id not in self.TEMPLATES:
            if self.console:
                self.console.print(f"[red]Error: Template '{template_id}' not found[/red]")
            return False

        template = self.TEMPLATES[template_id]
        structure = template["structure"]

        # Prepare variables for substitution
        variables = {
            "project_name": project_name,
            "description": description or template["description"],
        }

        try:
            # Create directory structure
            self._create_structure(target_dir, structure, variables)

            # Display success
            if HAS_RICH and self.console:
                self._display_success(target_dir, template["name"])
            else:
                print(f"\n✓ Created {template['name']} at {target_dir}")

            return True

        except Exception as e:
            if self.console:
                self.console.print(f"[red]Error bootstrapping project: {e}[/red]")
            return False

    def _create_structure(
        self, base_path: Path, structure: dict[str, Any], variables: dict[str, str]
    ) -> None:
        """Create directory structure recursively.

        Args:
            base_path: Base directory path
            structure: Structure dictionary
            variables: Variables for substitution
        """
        base_path.mkdir(parents=True, exist_ok=True)

        for item_name, content in structure.items():
            # Substitute variables in name
            resolved_name = self._substitute_vars(item_name, variables)
            path = base_path / resolved_name

            if isinstance(content, dict):
                # Directory
                self._create_structure(path, content, variables)
            else:
                # File
                file_content = self._substitute_vars(content, variables)
                path.write_text(file_content)

    def _substitute_vars(self, text: str, variables: dict[str, str]) -> str:
        """Substitute variables in text.

        Args:
            text: Text with {{variable}} placeholders
            variables: Variable values

        Returns:
            Text with substituted values
        """
        for key, value in variables.items():
            text = text.replace(f"{{{{{key}}}}}", value)
        return text

    def _display_success(self, target_dir: Path, template_name: str) -> None:
        """Display success message with tree.

        Args:
            target_dir: Created directory
            template_name: Template name
        """
        if not HAS_RICH or self.console is None:
            return

        # Create tree
        tree = Tree(f"[bold green]✓ Created {template_name}[/bold green]")
        self._build_tree(target_dir, tree, max_depth=2)

        panel = Panel(
            tree,
            title=f"[bold cyan]{target_dir.name}[/bold cyan]",
            subtitle=f"[dim]{target_dir}[/dim]",
            border_style="green",
        )

        self.console.print()
        self.console.print(panel)

    def _build_tree(self, path: Path, tree: Tree, max_depth: int, depth: int = 0) -> None:
        """Build file tree.

        Args:
            path: Current path
            tree: Tree node
            max_depth: Maximum depth
            depth: Current depth
        """
        if depth >= max_depth:
            return

        try:
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
        except PermissionError:
            return

        for item in items:
            if item.name.startswith("."):
                continue

            if item.is_dir():
                branch = tree.add(f"[blue]📁 {item.name}[/blue]")
                self._build_tree(item, branch, max_depth, depth + 1)
            else:
                tree.add(f"[white]📄 {item.name}[/white]")


__all__ = ["ProjectBootstrapper"]
