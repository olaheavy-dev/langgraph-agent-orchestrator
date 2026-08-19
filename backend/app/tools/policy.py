"""The review rules from contributing.md, checked before a human is asked.

These run against a proposal rather than a pull request, so the agent finds out
that its change would be rejected while it can still be revised -- and so the
human is not asked to approve something CI would reject anyway.

The rules are duplicated from the workspace's own ci.yml on purpose. That file
is the authority and this is a local mirror of it; when they disagree, ci.yml
wins and this needs updating.
"""

import re

from app.schemas import CodeProposal
from app.tools import workspace

# Mirrors the adr-drift job: these modules carry decisions, so changing one
# without touching a record leaves the reasoning behind.
ARCHITECTURAL = re.compile(r'src/taskvault/(rate_limit|storage|auth)\.py$')
ADR = re.compile(r'docs/adr-')

# The same rules stated for a model rather than for a regex. Kept beside the
# checks so the instruction and the enforcement cannot drift apart.
CONVENTIONS = """Follow the review conventions exactly:
- Branch: type/short-description, e.g. fix/rate-limit-boundary.
- Commit subject: a conventional commit -- lowercase, imperative, no trailing period.
- The body must say what changes, why now, and which test fails without it.
- At most three files. More than that is more than one change.
- If you change rate_limit.py, storage.py or auth.py you must also update the
  ADR in docs/ that explains the decision, in the same change."""

# From contributing.md: type prefix, lowercase subject, no trailing period.
COMMIT_SUBJECT = re.compile(r'^(feat|fix|docs|refactor|test|chore)(\([a-z_./-]+\))?: [a-z].*[^.]$')
BRANCH = re.compile(r'^(feat|fix|docs|refactor|test|chore)/[a-z0-9][a-z0-9-]*$')

# "A PR that touches more than about three files is doing more than one thing."
MAX_FILES = 3


def violations(proposal: CodeProposal) -> list[str]:
    """Every rule the proposal breaks, phrased as the reviewer would phrase it."""
    paths = [edit.path for edit in proposal.edits]
    found: list[str] = []

    if not paths:
        found.append('The proposal edits no files.')

    if any(ARCHITECTURAL.search(path) for path in paths) and not any(
        ADR.search(path) for path in paths
    ):
        found.append(
            'adr-drift: architectural code changed with no ADR update. '
            'See contributing.md -- amend the record or add a new one.'
        )

    for path in paths:
        if workspace.is_protected(path):
            found.append(
                f'{path} is protected. The agent may change the service, not the rules '
                'it is judged by.'
            )
        else:
            try:
                workspace.resolve(path)
            except workspace.PathOutsideWorkspace:
                found.append(f'{path} resolves outside the workspace.')

    if len(paths) > MAX_FILES:
        found.append(
            f'{len(paths)} files changed; contributing.md asks for at most {MAX_FILES}. '
            'This is probably more than one change.'
        )

    if not BRANCH.match(proposal.branch):
        found.append(f'Branch {proposal.branch!r} is not type/short-description.')

    if not COMMIT_SUBJECT.match(proposal.commit_message):
        found.append(
            f'Commit subject {proposal.commit_message!r} is not a conventional commit: '
            'lowercase, imperative, no trailing period.'
        )

    for field in ('summary', 'rationale', 'verification'):
        if not getattr(proposal, field).strip():
            found.append(f'The PR body leaves "{field}" blank; contributing.md requires all three.')

    return found
