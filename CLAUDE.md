# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A LangGraph orchestrator that routes a message to a chat agent, a retrieval agent, or a
coding agent, and suspends mid-run for human approval before any code is written.

The premise, which explains most of the design: the decisions constraining a change live
in ADRs and nowhere else, so a model given only source code writes something reasonable
and wrong. `backend/workspace/` is a small service (TaskVault) whose test suite is green
while the code contradicts its own documentation in four places. That gap is deliberate —
it is what makes retrieval load-bearing rather than decorative. **Do not "fix" those gaps.**

## Three separate projects

Each has its own lockfile, dependencies and test suite. `cd` into the right one first.

| Path | Toolchain |
| --- | --- |
| `backend/` | uv, Python 3.13 — the orchestrator |
| `backend/workspace/` | uv, Python 3.13 — TaskVault, the sandbox the coding agent edits |
| `frontend/` | npm, Next.js 15 — chat, trace rail, approval dialog |

## Commands

```bash
# backend
cd backend
uv sync --extra dev
uv run pytest -q                                     # 58 tests, no API key needed
uv run pytest tests/test_graph.py -q                 # one file
uv run pytest tests/test_policy.py::test_a_conforming_proposal_has_no_violations
uv run ruff check app tests && uv run ruff format app tests
uv run pyright                                       # must stay at 0 errors
uv run uvicorn app.main:app --reload                 # needs backend/.env

# workspace sandbox
cd backend/workspace
uv run pytest -q                                     # 8 tests
uv run ruff check . && uv run ruff format --check .

# frontend
cd frontend
npm install
npx vitest run                                       # 17 tests
npx vitest run -t "sends approve and deny"           # one test by name
npx tsc --noEmit
npx next dev -p 3000                                 # MUST be run from frontend/

# everything
docker compose up --build                            # needs backend/.env
```

`npx next dev` from any other directory silently builds the wrong workspace root and
returns HTTP 500. It also writes stray `.next/`, `AGENTS.md` and `CLAUDE.md` into
whatever directory it was run from — delete those if it happens.

## Architecture

### The graph never imports FastAPI

`app/graph/` takes a `State` and returns dict updates. Nothing in it knows a server
exists. That is what makes it testable without one, loadable in LangGraph Studio, and
reusable elsewhere. `app/service.py` is the only seam: routers call it, and it translates
graph results into API responses. Keep that boundary.

Read `app/graph/build.py` first — it is the whole system in one file with no logic in it.

### The approval interrupt spans two HTTP requests

`approval` calls `interrupt()`, the checkpointer persists everything, and `POST /chat`
returns `status: "awaiting_approval"`. A separate `POST /approve` resumes with
`Command(resume=...)`.

Consequences that are easy to break:

- The checkpointer is **SqliteSaver, not in-memory** — the pause outlives the request, so
  with more than one worker an in-memory checkpoint is invisible to whoever resumes it.
- Resuming **replays the approval node from the top**. It must do nothing before its
  `interrupt()` call, or the side effect happens twice.
- A revision cycles back to `coding_agent`, so a thread can hit `interrupt()` repeatedly.

### Two coding strategies behind one Protocol

`app/agents/` — `structured` (one model call returns whole files) and `claude_code`
(delegates to `claude -p`). Selected by `ORCHESTRATOR_CODE_AGENT`.

`claude_code` runs the CLI against a **throwaway copy** of the workspace, diffs the copy,
then deletes it. `--permission-mode acceptEdits` is safe only because the directory is
disposable. Pointing it at the real workspace would make the approval gate a notification
— the files would already be changed by the time `interrupt()` ran. Never do that.

### Nothing reaches the workspace before approval

- `app/tools/workspace.py` resolves paths **then** checks them against the root, so `../`
  and symlinks out are both refused. `.github/`, `pyproject.toml` and `uv.lock` are not
  writable — the agent may change the service, not the rules it is judged by.
- `apply` validates every path before writing any file. A half-applied change is worse
  than a rejected one, because nothing on disk records that it happened.
- `app/tools/policy.py` mirrors the review rules in `backend/workspace/docs/contributing.md`
  and `.github/workflows/ci.yml` (the `adr-drift` job). Those files are the authority; this
  is a local copy. If they disagree, they win and policy.py needs updating.

### The corpus lives inside the sandbox

`backend/workspace/docs/*.md`, not in the orchestrator. That placement is load-bearing:
the `adr-drift` rule requires a change to `rate_limit.py`/`storage.py`/`auth.py` to also
update an ADR, which is only enforceable if the coding agent can edit both.

The coding agent is handed `src/` and `tests/` plus the **full text** of any document a
retrieval cited. Excerpts are enough to answer a question and not enough to amend a file —
an agent given a 700-character passage rewrites the ADR from scratch. `diffing.baseline()`
reads real file contents from disk for anything edited but not shown, or a destructive
rewrite renders as a `/dev/null` creation and hides what it deletes.

## Conventions that will break things if ignored

**Late-bind the cached factories.** Modules do `from app import config` / `from app import
llm` and call `config.get_settings()`, never `from app.config import get_settings`. A
direct import binds the name at import time and the test fixtures' monkeypatching silently
does nothing — which once caused tests to write into the real checked-in workspace.
`lru_cache` sits on `config.get_settings`, `llm.get_model`, `llm.get_embeddings`,
`knowledge.store.get_store` and `graph.build.get_graph`; the `sandbox` fixture clears the
ones it has to.

**Tests never reach a provider.** An autouse fixture substitutes a scripted model and
deterministic hash-based embeddings, so routing and the approval gate are asserted without
an API key. Use the `sandbox` fixture for anything that touches the filesystem — it works
on a disposable copy. `TwoStepModel` in `tests/test_graph.py` must be a **single shared
instance** across a turn; its queue is state shared between the classifier's call and the
coding agent's.

**Style:** single quotes, 100 columns, `ruff format` (configured for single quotes in all
three projects). Comments explain *why*, never *what* — if the reasoning is architectural
it belongs in an ADR with the comment pointing at it.

## Config

`backend/.env` (see `.env.example`) needs `OPENAI_API_KEY`. Settings are `ORCHESTRATOR_`-
prefixed and all live in `app/config.py`. `frontend/.env.example` holds
`NEXT_PUBLIC_API_URL`, which is inlined at build time and so must be reachable from a
browser, not from inside the container network.

## Running it end to end

A real coding turn writes to `backend/workspace/` and takes ~10–20s of API spend. Snapshot
`workspace/{src,docs,tests}` before, and restore after, or the seeded gaps are lost and the
demo stops reproducing. Verify with: a full bucket should allow **101** requests (the
seeded bug), not 100.

## Git

Commits carry the user's authorship only — do not add a `Co-Authored-By` trailer.
