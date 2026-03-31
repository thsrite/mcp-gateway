import asyncio
import logging
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from app.utils.detector import (
    detect_name_from_repo,
    detect_project_type,
    detect_start_command,
)
from app.utils.namespace import sanitize_namespace

logger = logging.getLogger(__name__)


@dataclass
class CloneResult:
    local_path: Path
    project_type: str
    command: str
    args: list[str]
    detected_name: str
    commit_hash: str


@dataclass
class PullResult:
    has_updates: bool
    commit_before: str
    commit_after: str


class GitHubManager:
    def __init__(self, repos_dir: Path):
        self.repos_dir = repos_dir
        self.repos_dir.mkdir(parents=True, exist_ok=True)

    def _parse_repo_name(self, github_url: str) -> str:
        match = re.search(r"github\.com/([^/]+)/([^/.]+)", github_url)
        if not match:
            raise ValueError(f"Invalid GitHub URL: {github_url}")
        return match.group(2)

    async def _run_command(
        self, cmd: list[str], cwd: Path | None = None
    ) -> tuple[str, str, int]:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        stdout, stderr = await proc.communicate()
        return (
            stdout.decode("utf-8", errors="replace").strip(),
            stderr.decode("utf-8", errors="replace").strip(),
            proc.returncode,
        )

    async def _get_commit_hash(self, repo_path: Path) -> str:
        stdout, _, _ = await self._run_command(
            ["git", "rev-parse", "HEAD"], cwd=repo_path
        )
        return stdout

    async def clone(self, github_url: str, branch: str | None = None) -> CloneResult:
        repo_name = self._parse_repo_name(github_url)
        local_path = self.repos_dir / repo_name

        if local_path.exists():
            logger.info(f"Repository already exists at {local_path}, pulling latest")
            await self._run_command(["git", "pull", "--ff-only"], cwd=local_path)
        else:
            cmd = ["git", "clone", "--depth", "1"]
            if branch:
                cmd += ["-b", branch]
            cmd += [github_url, str(local_path)]
            logger.info(f"Cloning {github_url} (branch={branch or 'default'}) to {local_path}")
            stdout, stderr, code = await self._run_command(cmd)
            if code != 0:
                raise RuntimeError(f"git clone failed: {stderr}")

        project_type = detect_project_type(local_path)
        logger.info(f"Detected project type: {project_type}")

        await self._install_dependencies(local_path, project_type)

        command, args = detect_start_command(local_path, project_type)
        detected_name = sanitize_namespace(
            detect_name_from_repo(local_path, project_type)
        )
        commit_hash = await self._get_commit_hash(local_path)

        logger.info(
            f"Clone complete: name={detected_name}, type={project_type}, "
            f"cmd={command} {args}"
        )

        return CloneResult(
            local_path=local_path,
            project_type=project_type,
            command=command,
            args=args,
            detected_name=detected_name,
            commit_hash=commit_hash,
        )

    async def pull(self, local_path: Path) -> PullResult:
        commit_before = await self._get_commit_hash(local_path)

        stdout, stderr, code = await self._run_command(
            ["git", "pull", "--ff-only"], cwd=local_path
        )
        if code != 0:
            logger.warning(f"git pull failed for {local_path}: {stderr}")
            return PullResult(
                has_updates=False,
                commit_before=commit_before,
                commit_after=commit_before,
            )

        commit_after = await self._get_commit_hash(local_path)
        has_updates = commit_before != commit_after

        if has_updates:
            logger.info(
                f"Updates found for {local_path}: {commit_before[:8]} -> {commit_after[:8]}"
            )
            project_type = detect_project_type(local_path)
            await self._install_dependencies(local_path, project_type)

        return PullResult(
            has_updates=has_updates,
            commit_before=commit_before,
            commit_after=commit_after,
        )

    async def _install_dependencies(self, local_path: Path, project_type: str):
        if project_type == "python":
            await self._install_python_deps(local_path)
        elif project_type == "node":
            await self._install_node_deps(local_path)

    async def _install_python_deps(self, repo_path: Path):
        venv_path = repo_path / ".venv"

        _, _, uv_code = await self._run_command(["which", "uv"])
        use_uv = uv_code == 0

        if not venv_path.exists():
            if use_uv:
                logger.info(f"Creating venv with uv at {venv_path}")
                await self._run_command(["uv", "venv", str(venv_path)])
            else:
                logger.info(f"Creating venv at {venv_path}")
                await self._run_command(["python3", "-m", "venv", str(venv_path)])

        if use_uv:
            logger.info(f"Installing Python deps with uv for {repo_path}")
            stdout, stderr, code = await self._run_command(
                [
                    "uv",
                    "pip",
                    "install",
                    "-e",
                    str(repo_path),
                    "--python",
                    str(venv_path / "bin" / "python"),
                ]
            )
        else:
            pip_path = venv_path / "bin" / "pip"
            logger.info(f"Installing Python deps with pip for {repo_path}")
            stdout, stderr, code = await self._run_command(
                [str(pip_path), "install", "-e", str(repo_path)]
            )

        if code != 0:
            logger.warning(f"Dependency install warning: {stderr}")

    async def _install_node_deps(self, repo_path: Path):
        logger.info(f"Installing Node.js deps for {repo_path}")
        stdout, stderr, code = await self._run_command(
            ["npm", "install"], cwd=repo_path
        )
        if code != 0:
            logger.warning(f"npm install warning: {stderr}")

        if (repo_path / "tsconfig.json").exists():
            logger.info(f"Building TypeScript project at {repo_path}")
            await self._run_command(["npm", "run", "build"], cwd=repo_path)

    async def delete_repo(self, local_path: Path):
        if local_path.exists() and local_path.is_dir():
            shutil.rmtree(local_path)
            logger.info(f"Deleted repository: {local_path}")
