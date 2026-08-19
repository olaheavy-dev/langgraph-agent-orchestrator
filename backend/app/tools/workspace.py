"""Filesystem access, confined to the sandbox.

Every path the coding agent supplies is resolved and then checked against the
workspace root. The check is on the *resolved* path rather than the string,
because '../../etc/passwd' and a symlink pointing outside both look harmless
until you resolve them.
"""

import subprocess
from pathlib import Path

from app import config

# Read but never written, and never shown to the model as editable: the agent's
# job is to change the service, not the rules it is judged by.
PROTECTED = {'.github', 'pyproject.toml', 'uv.lock'}

SOURCE_SUFFIXES = {'.py', '.toml', '.md', '.yml', '.yaml'}


class PathOutsideWorkspace(ValueError):
    """Raised when a path escapes the sandbox. Never caught -- it means the agent
    tried something it must not be allowed to do, and that should be loud."""


def workspace_root() -> Path:
    return config.get_settings().workspace_root.resolve()


def resolve(relative: str) -> Path:
    """Turn an agent-supplied path into an absolute one inside the sandbox."""
    root = workspace_root()
    candidate = (root / relative).resolve()
    if candidate != root and root not in candidate.parents:
        raise PathOutsideWorkspace(f'{relative!r} resolves outside the workspace')
    return candidate


def is_protected(relative: str) -> bool:
    head = Path(relative).parts[0] if Path(relative).parts else ''
    return head in PROTECTED


def list_files() -> list[str]:
    """Every source file in the sandbox, as workspace-relative paths."""
    root = workspace_root()
    return sorted(
        str(path.relative_to(root))
        for path in root.rglob('*')
        if path.is_file()
        and path.suffix in SOURCE_SUFFIXES
        and not any(part.startswith('.') for part in path.relative_to(root).parts)
    )


def read_file(relative: str) -> str:
    path = resolve(relative)
    if not path.is_file():
        raise FileNotFoundError(relative)
    return path.read_text()


def is_writable(relative: str) -> bool:
    """Whether write_file would accept this path, without writing anything.

    Used to check a whole proposal before applying any of it.
    """
    if is_protected(relative):
        return False
    try:
        resolve(relative)
    except PathOutsideWorkspace:
        return False
    return True


def read_or_empty(relative: str) -> str:
    """The file's current contents, or empty if it does not exist yet.

    Used to build a diff baseline: a file the agent edited but was never handed
    still has to be compared against what is actually on disk.
    """
    try:
        return read_file(relative)
    except (FileNotFoundError, OSError, UnicodeDecodeError):
        return ''


def write_file(relative: str, content: str) -> None:
    """Only ever called after a human has approved the change."""
    if is_protected(relative):
        raise PathOutsideWorkspace(f'{relative!r} is protected and may not be written')
    path = resolve(relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def snapshot() -> dict[str, str]:
    """The whole editable source tree.

    The sandbox is about 230 lines, so the coding agent is given all of it rather
    than retrieving over it. That is a property of this sandbox, not a design
    position: past a few thousand lines this becomes a retrieval problem and
    belongs behind the same store the corpus uses.
    """
    return {
        relative: read_file(relative)
        for relative in list_files()
        if relative.startswith(('src/', 'tests/'))
    }


def run_checks() -> list[tuple[str, bool, str]]:
    """Run the workspace's own CI jobs locally.

    The names match the jobs in its ci.yml, so a failure here reads the same way
    as a failure on a pull request.
    """
    jobs = [
        ('lint', ['uv', 'run', 'ruff', 'check', '.']),
        ('format', ['uv', 'run', 'ruff', 'format', '--check', '.']),
        ('test', ['uv', 'run', 'pytest', '-q']),
    ]
    results: list[tuple[str, bool, str]] = []
    for name, command in jobs:
        try:
            completed = subprocess.run(
                command, cwd=workspace_root(), capture_output=True, text=True, timeout=180
            )
            output = (completed.stdout + completed.stderr).strip()
            results.append((name, completed.returncode == 0, output[-2000:]))
        except (OSError, subprocess.TimeoutExpired) as error:
            results.append((name, False, f'could not run {name}: {error}'))
    return results
