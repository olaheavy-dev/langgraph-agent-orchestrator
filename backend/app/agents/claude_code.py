"""Delegating the edit to Claude Code, without giving it the workspace.

`claude -p` is a far more capable coding agent than a single structured call: it
explores, reads what it needs, edits several files and re-runs the tests. The
difficulty is that letting it edit is the whole of its value, and this project's
premise is that nothing reaches the workspace before a human agrees to it.

So it edits a throwaway copy. `--permission-mode acceptEdits` is safe there
precisely because the directory is disposable -- the copy is diffed against the
real workspace, and the diff is what the human approves. If the run is rejected,
the copy is deleted and the workspace was never touched.

Claude Code does the engineering; a structured model call afterwards does the
paperwork, so the proposal still carries a branch, a conventional commit subject
and a reviewable body for the policy checks to judge.
"""

import json
import logging
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import cast

from app import config, llm
from app.knowledge import store
from app.schemas import Citation, CodeProposal, FileEdit
from app.tools import policy, workspace

logger = logging.getLogger(__name__)

# Copied into the sandbox but not worth handing to the agent, and expensive to
# duplicate.
SKIP = shutil.ignore_patterns('.venv', '.pytest_cache', '.ruff_cache', '__pycache__', '.git')

PROMPT = """You are working on TaskVault, in the current directory.

{request}

The following passages from the project's own documentation are binding. They
record decisions that are not visible in the code, and where the code
contradicts them the code is wrong. Read the files in docs/ if you need more.

{context}

{conventions}

Make the change. Run the tests before you finish. Do not create a branch or a
commit -- the change is reviewed by a human before it is applied anywhere.
"""

PAPERWORK = (
    'A coding agent has made the change shown in this diff. Write the pull '
    'request paperwork for it. Do not invent edits: the edits are already '
    'decided, and your output is used only for the branch name, the commit '
    'subject and the review body.\n\n'
    f'{policy.CONVENTIONS}'
)


def _run_claude(prompt: str, cwd: Path, timeout: int) -> str:
    """Invoke the CLI in the disposable copy and return its final message."""
    completed = subprocess.run(
        [
            'claude',
            '-p',
            prompt,
            # Safe only because cwd is a throwaway copy of the workspace.
            '--permission-mode',
            'acceptEdits',
            '--output-format',
            'json',
        ],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if completed.returncode != 0:
        raise RuntimeError(f'claude exited {completed.returncode}: {completed.stderr[-500:]}')

    try:
        return json.loads(completed.stdout).get('result', '')
    except json.JSONDecodeError:
        # Still useful as a transcript even when the envelope is not what we
        # expected; the edits on disk are what actually matter.
        return completed.stdout


class ClaudeCodeAgent:
    name = 'claude_code'

    def __init__(self, runner: Callable[[str, Path, int], str] = _run_claude) -> None:
        # Injected so the suite can exercise the copy-diff-discard cycle without
        # a CLI on PATH or a second billed model.
        self._runner = runner

    def propose(
        self, request: str, citations: list[Citation], source: dict[str, str]
    ) -> CodeProposal:
        settings = config.get_settings()
        prompt = PROMPT.format(
            request=request,
            context=store.as_context(citations),
            conventions=policy.CONVENTIONS,
        )

        with tempfile.TemporaryDirectory(prefix='taskvault-') as scratch:
            copy = Path(scratch) / 'workspace'
            shutil.copytree(settings.workspace_root, copy, ignore=SKIP)

            transcript = self._runner(prompt, copy, settings.code_agent_timeout)
            edits = _changed_files(copy, source)

        # The copy is gone by here. Everything the change consists of is in
        # `edits`, and nothing has touched the real workspace.
        if not edits:
            return _empty_proposal(transcript)
        return _paperwork(request, edits, source, transcript)


def _changed_files(copy: Path, before: dict[str, str]) -> list[FileEdit]:
    """Every source file whose contents differ from the real workspace."""
    edits: list[FileEdit] = []
    for path in sorted(copy.rglob('*')):
        if not path.is_file() or path.suffix not in workspace.SOURCE_SUFFIXES:
            continue
        relative = str(path.relative_to(copy))
        if any(part.startswith('.') for part in Path(relative).parts):
            continue
        try:
            content = path.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        original = before[relative] if relative in before else _read_original(relative)
        if content != original:
            edits.append(FileEdit(path=relative, new_content=content))
    return edits


def _read_original(relative: str) -> str:
    """Files outside the snapshot -- docs, mainly -- still need a baseline to
    compare against, since an ADR update is a legitimate part of a change."""
    try:
        return workspace.read_file(relative)
    except (FileNotFoundError, OSError):
        return ''


def _paperwork(
    request: str, edits: list[FileEdit], before: dict[str, str], transcript: str
) -> CodeProposal:
    from app.tools import diffing

    model = llm.get_model().with_structured_output(CodeProposal)
    proposal = cast(
        CodeProposal,
        model.invoke(
            [
                {'role': 'system', 'content': PAPERWORK},
                {
                    'role': 'user',
                    'content': (
                        f'Request: {request}\n\n'
                        f'What the agent reported:\n{transcript[:4000]}\n\n'
                        f'Diff:\n{diffing.render(edits, diffing.baseline(edits, before))}'
                    ),
                },
            ]
        ),
    )
    # The model writes the description; the edits are the ones actually made.
    proposal.edits = edits
    return proposal


def _empty_proposal(transcript: str) -> CodeProposal:
    """The agent changed nothing. Said plainly rather than dressed up as a
    proposal with no diff, which reads to a reviewer as a bug."""
    return CodeProposal(
        summary='No change was made.',
        rationale=transcript[:500] or 'The coding agent finished without editing any file.',
        verification='Nothing to verify.',
        branch='chore/no-change',
        commit_message='chore: no change proposed',
        edits=[],
    )
