# API reference

All endpoints except `/health` require an `X-API-Key` header. A key sees only
the tasks it created.

This document is the contract. Where it and the implementation disagree, the
implementation is wrong.

## GET /health

No authentication. Returns `{"status": "ok"}`.

## POST /tasks

Creates a task. Body: `{"title": "..."}`.

The title is trimmed of surrounding whitespace. A title that is empty after
trimming is rejected with 400. A title longer than 200 characters is rejected
with 400 -- titles are shown untruncated in the tenant UI, and a long one breaks
the layout rather than degrading it.

Returns 201 with the created task.

## GET /tasks

Lists the calling key's tasks, oldest first.

Accepts an optional `status` query parameter, either `open` or `done`, which
filters the result to tasks in that state. Omitting it returns all tasks. A
value that is neither is rejected with 422.

## POST /tasks/{id}/complete

Marks a task done and returns it. Completing an already-done task is not an
error and returns the task unchanged.

A task belonging to another key returns 404, never 403. The distinction matters:
403 would confirm the task exists, which tells one tenant something about
another. See adr-001-storage on scoping.

## Errors

| Status | Meaning |
| --- | --- |
| 400 | The body failed validation |
| 401 | The API key was missing or unknown |
| 404 | No such task for this key |
| 422 | A query parameter was the wrong shape |
| 429 | The key's rate limit is exhausted -- see adr-003-rate-limiting |
