"""Turning an approved proposal into a review artifact.

Publishing is behind a protocol because where a pull request goes is a
deployment concern, not a graph concern. The default writes it to disk and
returns it to the caller, which is what a reviewer actually needs to see; a
GitHubPublisher calling `gh pr create` satisfies the same interface and is the
intended swap for a real remote.
"""

from pathlib import Path
from typing import Protocol

from app.schemas import CheckResult, CodeProposal, PullRequest


class PullRequestPublisher(Protocol):
    def publish(self, pull_request: PullRequest) -> str:
        """Put the pull request somewhere a human can review it, and say where."""
        ...


def render_body(proposal: CodeProposal, checks: list[CheckResult]) -> str:
    """The three questions contributing.md requires, plus the agent disclosure."""
    consulted = ', '.join(proposal.adrs_consulted) or 'none'
    check_lines = '\n'.join(
        f'- {"pass" if check.passed else "FAIL"} `{check.name}`' for check in checks
    )
    return (
        f'## What changes\n\n{proposal.summary}\n\n'
        f'## Why now\n\n{proposal.rationale}\n\n'
        f'## How it was verified\n\n{proposal.verification}\n\n'
        f'## Checks\n\n{check_lines or "not run"}\n\n'
        f'---\n\n'
        f'This pull request was authored by an automated agent. '
        f'Knowledge-base documents consulted before writing the code: {consulted}. '
        f'Per contributing.md, an agent may not approve a pull request -- '
        f'a human approved the change before it was applied, and review is still required.\n'
    )


class LocalPublisher:
    """Writes the pull request to a directory as a reviewable artifact.

    No remote and no git: the sandbox is not a repository of its own, and the
    thing worth demonstrating is the *content* of the review -- whether the change
    is grounded, conventional, and passes the checks -- not the plumbing of
    pushing it somewhere.
    """

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir

    def publish(self, pull_request: PullRequest) -> str:
        self._output_dir.mkdir(parents=True, exist_ok=True)
        destination = self._output_dir / f'{pull_request.branch.replace("/", "-")}.md'
        destination.write_text(
            f'# {pull_request.title}\n\n'
            f'Branch: `{pull_request.branch}`\n\n'
            f'{pull_request.body}\n'
            f'## Diff\n\n```diff\n{pull_request.diff}\n```\n'
        )
        return str(destination)
