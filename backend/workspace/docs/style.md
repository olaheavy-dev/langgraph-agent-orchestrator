# Conventions

## Comments explain why, never what

The code says what it does. A comment repeating that in prose is noise that goes
stale. Comment the decision, the constraint, or the thing that will surprise the
next reader -- and if the reasoning is architectural, it belongs in an ADR with
the comment pointing at it.

## Validate at the boundary

Request validation happens in `api.py`. Storage assumes it was handed something
already valid. Two layers of checking means two places to change and one of them
will be forgotten.

## Errors are HTTPException with a plain-language detail

No error codes, no nested error objects. The detail string is written for a
developer reading a log line, so `'title is required'`, not `'ERR_VALIDATION'`.

## Tests name the behaviour, not the function

`test_completing_another_keys_task_is_a_404` rather than `test_complete_2`. The
test name is what shows up when CI fails, and it should say what broke without
requiring anyone to open the file.

Every test builds a real `TaskStore` against `:memory:`. Mocking storage is not
permitted here -- see adr-001-storage on why the tests exercise real queries.

## Formatting

`ruff format`, 100-column lines, single quotes. Not negotiable in review because
it is checked in CI and arguing about it costs more than complying.
