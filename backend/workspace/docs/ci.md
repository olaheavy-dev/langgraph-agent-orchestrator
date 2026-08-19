# Continuous integration

Every pull request runs three jobs in GitHub Actions. All three block merge.
The workflow lives at `.github/workflows/ci.yml` in the TaskVault repository.

## lint

`ruff check` followed by `ruff format --check`. Fails on unformatted code, unused
imports, and unsorted imports.

This job is first because it is the fastest and its failures are the cheapest to
fix. If it is red, fix it before reading the others -- a formatting failure often
means the change was never run locally, and the later failures may be noise from
the same cause.

## test

`uv sync --extra dev` then `pytest -q`. The whole suite runs on every push; there
is no partial or changed-files-only mode, because the suite takes under ten
seconds and deciding what to skip costs more than running it.

A skipped test counts as a failing test in review. If something cannot be tested
yet, the PR says why in the body rather than leaving an unexplained `skipif`.

## adr-drift

Compares the changed file list against the base branch. If the diff touches
`rate_limit.py`, `storage.py`, or `auth.py` without touching any `adr-*` file,
the job fails with a pointer to contributing.md.

It is a text comparison, not an understanding of the change. It cannot tell an
architectural edit from a typo fix in the same file, and it is expected to
produce occasional false positives. A reviewer may override it; nobody may
disable it.

## Concurrency

Runs are grouped per workflow and ref with `cancel-in-progress: true`, so pushing
twice in quick succession cancels the first run rather than queueing both.

## What is deliberately absent

No deploy job. TaskVault is released by tagging, and the tag pipeline is separate
so that a red main branch cannot ship.

No coverage gate. Coverage was measured for a quarter and produced tests written
to raise the number rather than to catch anything, so the gate was removed and
the requirement moved into review: every PR names the test that fails without it.
