# TaskVault

A small task-tracking API: create a task, list your tasks, mark one done. Access
is by API key, and a key sees only its own tasks.

This service is the codebase the orchestrator's coding agent works on. It is
deliberately small enough to read in one sitting and deliberately imperfect --
the gaps between what `docs/` documents and what `src/` implements are the
work the agent is asked to do.

## Running it

```bash
uv sync --extra dev
TASKVAULT_API_KEYS=local-dev-key uv run uvicorn taskvault.api:app --reload
```

```bash
curl -X POST localhost:8000/tasks \
  -H 'X-API-Key: local-dev-key' \
  -H 'content-type: application/json' \
  -d '{"title": "read the ADRs"}'
```

## Tests

```bash
uv run pytest -q
```

## Where the reasoning lives

The code says what it does; `docs/` says why. Decision records, the API
contract, the review conventions and the incident history live there, and that
directory is the corpus the orchestrator's retrieval agent searches.

A change that satisfies the tests but contradicts an ADR is still wrong, which
is why the coding agent reads `docs/` before it writes `src/` -- and why a change
to the architecture is expected to update the record that explains it.
