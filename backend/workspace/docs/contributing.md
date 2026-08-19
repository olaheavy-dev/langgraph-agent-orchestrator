# Contributing

## Branches

Branch from `main`. Name it `type/short-description` using the same type as the
commit: `fix/rate-limit-boundary`, `feat/status-filter`, `docs/adr-004`.

`main` is protected. Nothing merges without a pull request, including changes by
whoever wrote the code originally.

## Commits

Conventional commits, imperative mood, lowercase subject, no trailing period:

```
fix(rate_limit): reject the 101st request in a full window
feat(api): filter GET /tasks by status
docs(adr-003): record the shared-bucket prerequisite
```

The type prefix is what generates the changelog, so `chore` is not a synonym for
"I could not decide".

## Pull requests

One reviewer approval is required. The PR body must answer three things, and a
PR that leaves any of them blank will be sent back:

1. **What changes** -- one or two sentences, not a diff summary.
2. **Why now** -- the issue, incident, or ADR that motivates it.
3. **How it was verified** -- the test that fails without this change. "Ran it
   locally" is not verification.

Keep them small. A PR that touches more than about three files is doing more
than one thing and should be split; large ones get shallow reviews, which is how
the March incident reached production.

## The ADR rule

A pull request that changes `rate_limit.py`, `storage.py`, or `auth.py` must
also change an ADR -- either amending the record it affects or adding a new one.
This is enforced by the `adr-drift` job in CI, and the check is deliberately
blunt: it does not know whether your change was architectural, so if it fires on
a genuinely trivial edit, say so in the PR and the reviewer can override it.

The rule exists because the code and its reasoning drifted apart once already,
and the drift was invisible until an incident made it expensive.

## Agent-authored changes

Changes proposed by an automated agent follow exactly this process -- same
branch naming, same PR body, same review. The PR description must state that it
was agent-authored and name the ADRs the agent retrieved before writing the
code, so a reviewer can check the change against the reasoning it claims to
follow.

An agent may not approve a pull request.
