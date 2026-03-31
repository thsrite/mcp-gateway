import json
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib


class DetectionError(Exception):
    pass


def detect_project_type(repo_path: Path) -> str:
    if (repo_path / "package.json").exists():
        return "node"
    if (repo_path / "pyproject.toml").exists() or (repo_path / "setup.py").exists():
        return "python"
    if list(repo_path.glob("*.py")):
        return "python"
    raise DetectionError(f"Cannot detect project type for {repo_path}")


def detect_start_command(repo_path: Path, project_type: str) -> tuple[str, list[str]]:
    if project_type == "node":
        return _detect_node_command(repo_path)
    elif project_type == "python":
        return _detect_python_command(repo_path)
    raise DetectionError(f"Unsupported project type: {project_type}")


def _detect_node_command(repo_path: Path) -> tuple[str, list[str]]:
    pkg_path = repo_path / "package.json"
    if pkg_path.exists():
        with open(pkg_path, "r") as f:
            pkg = json.load(f)

        # Check bin field
        bin_field = pkg.get("bin")
        if isinstance(bin_field, dict):
            first_bin = next(iter(bin_field.values()))
            return "node", [first_bin]
        elif isinstance(bin_field, str):
            return "node", [bin_field]

        # Check scripts.start
        scripts = pkg.get("scripts", {})
        if "start" in scripts:
            return "npx", scripts["start"].split()

    # Fallback: look for common entry points
    for entry in ["dist/index.js", "build/index.js", "index.js"]:
        if (repo_path / entry).exists():
            return "node", [entry]

    raise DetectionError(f"Cannot detect Node.js start command for {repo_path}")


def _detect_python_command(repo_path: Path) -> tuple[str, list[str]]:
    venv_python = repo_path / ".venv" / "bin" / "python"
    python_cmd = str(venv_python) if venv_python.exists() else "python"

    # Check pyproject.toml for scripts
    pyproject_path = repo_path / "pyproject.toml"
    if pyproject_path.exists():
        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)

        # [project.scripts]
        scripts = pyproject.get("project", {}).get("scripts", {})
        if scripts:
            first_script = next(iter(scripts.keys()))
            # The script entry point should be installed in .venv/bin/
            script_bin = repo_path / ".venv" / "bin" / first_script
            if script_bin.exists():
                return str(script_bin), []
            return python_cmd, ["-m", first_script]

        # Try to get package name
        pkg_name = pyproject.get("project", {}).get("name", "")
        if pkg_name:
            module_name = pkg_name.replace("-", "_")
            return python_cmd, ["-m", module_name]

    # Look for common entry points
    for pattern in ["src/*/server.py", "**/mcp_server.py", "server.py", "main.py"]:
        matches = list(repo_path.glob(pattern))
        if matches:
            return python_cmd, [str(matches[0].relative_to(repo_path))]

    # Check __main__.py
    for pattern in ["src/*/__main__.py", "**/__main__.py"]:
        matches = list(repo_path.glob(pattern))
        if matches:
            parent = matches[0].parent
            module = str(parent.relative_to(repo_path)).replace("/", ".")
            return python_cmd, ["-m", module]

    raise DetectionError(f"Cannot detect Python start command for {repo_path}")


def detect_name_from_repo(repo_path: Path, project_type: str) -> str:
    if project_type == "node":
        pkg_path = repo_path / "package.json"
        if pkg_path.exists():
            with open(pkg_path, "r") as f:
                pkg = json.load(f)
            name = pkg.get("name", "")
            if name:
                return name.split("/")[-1]  # Remove scope

    if project_type == "python":
        pyproject_path = repo_path / "pyproject.toml"
        if pyproject_path.exists():
            with open(pyproject_path, "rb") as f:
                pyproject = tomllib.load(f)
            name = pyproject.get("project", {}).get("name", "")
            if name:
                return name

    # Fallback to directory name
    return repo_path.name
