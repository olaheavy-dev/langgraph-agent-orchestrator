"""Rendering a proposal as something a human can review.

A diff rather than the new file contents: approval is a judgement about what
changes, and asking someone to spot the change in 200 unchanged lines is asking
them to approve without reading.
"""

import difflib

from app.schemas import FileEdit
from app.tools import workspace


def baseline(edits: list[FileEdit], known: dict[str, str]) -> dict[str, str]:
    """What each edited file looked like before.

    `known` is what the agent was shown. Anything it edited outside that -- an ADR
    it was asked to amend, most often -- is read from disk, because diffing a
    rewrite against nothing renders it as a creation and hides the 40 lines it
    would delete. A reviewer needs the truth precisely there.
    """
    return {edit.path: known.get(edit.path) or workspace.read_or_empty(edit.path) for edit in edits}


def render(edits: list[FileEdit], before: dict[str, str]) -> str:
    """A unified diff across every edited file, in `git diff` shape."""
    blocks: list[str] = []
    for edit in edits:
        original = before.get(edit.path, '')
        if original == edit.new_content:
            continue
        blocks.append(
            '\n'.join(
                difflib.unified_diff(
                    original.splitlines(),
                    edit.new_content.splitlines(),
                    fromfile=f'a/{edit.path}' if original else '/dev/null',
                    tofile=f'b/{edit.path}',
                    lineterm='',
                )
            )
        )
    return '\n\n'.join(block for block in blocks if block)


def stat(edits: list[FileEdit], before: dict[str, str]) -> str:
    """A one-line summary in the shape of `git diff --stat`."""
    added = removed = 0
    for edit in edits:
        original = before.get(edit.path, '').splitlines()
        for line in difflib.ndiff(original, edit.new_content.splitlines()):
            added += line.startswith('+ ')
            removed += line.startswith('- ')
    files = len(edits)
    return f'{files} file{"s" if files != 1 else ""} changed, +{added} -{removed}'
