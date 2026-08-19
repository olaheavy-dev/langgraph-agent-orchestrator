# ADR-001: SQLite as the primary store

Status: accepted, 2025-11-04. Supersedes nothing.

## Decision

TaskVault stores tasks in a single SQLite file, accessed through one connection
held for the process lifetime.

## Why

The service serves fewer than twenty tenants and writes are rare -- a task is
created, then read many times. Postgres was the obvious alternative and was
rejected on operational cost rather than capability: it doubles what has to be
running for a service whose entire dataset fits comfortably in memory.

SQLite also makes the test suite honest. Every test constructs a real store
against `:memory:` rather than a mock, so the queries under test are the queries
that run in production.

## What this constrains

One writer. Concurrent writes serialise, and under sustained write load they
will time out rather than queue gracefully. This is acceptable at current volume
and is the first thing that breaks if volume changes.

Do not add a connection pool. A pool over SQLite multiplies readers without
helping the writer, and it hides the single-writer ceiling that makes this
decision reviewable.

## When to revisit

Revisit when any of these is true: sustained writes exceed roughly one per
second, a second service instance is deployed, or tenant count passes fifty. The
migration path is Postgres with the same schema; the storage interface exists to
make that a single-module change.

## Scoping rule

Tenant isolation is enforced in the query, not after it. Every read and write
filters on `owner_key` in SQL. Filtering in Python after a broad select is
forbidden -- it has failed in this codebase before, and a missed filter there is
a data leak rather than a bug.
