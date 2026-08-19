# Runbook

## 429s from a tenant who says they are not being noisy

Check whether a second instance is running. Buckets are per process
(adr-003-rate-limiting), so two instances enforce two independent limits and a
client bouncing between them sees inconsistent behaviour rather than a clean
limit. If a second instance exists, that is the bug; the limit is working.

Otherwise, confirm the tenant is not sharing a key across several of their own
services. The limit belongs to the key, and a key used by three cron jobs is one
noisy client as far as TaskVault is concerned.

## Writes timing out under load

Expected behaviour at the SQLite ceiling described in adr-001-storage, not a
transient fault. Do not restart the service -- it will absorb the backlog and time
out again. Confirm the sustained write rate; if it is above roughly one per
second, the decision to revisit is the storage engine.

## A tenant reports seeing another tenant's task

Treat as an incident, not a bug report. Every query filters on `owner_key` in
SQL; a leak means a query was written without the filter. Find it by grepping
`storage.py` for a `SELECT` or `UPDATE` with no `owner_key` clause. This has
happened once and is the reason the rule in adr-001-storage is stated as a
prohibition rather than a preference.

## CI is red on adr-drift for a change that is genuinely trivial

The check cannot tell. Say so in the PR body and ask the reviewer to override.
Do not edit an ADR to add a no-op line to make the job pass -- that defeats the
one thing the check protects.

## Rotating a compromised key

Remove it from `TASKVAULT_API_KEYS` and redeploy. There is no revocation list;
adr-002-auth records why. Tasks created by the old key remain in the database
under that `owner_key` and become unreachable, which is intentional -- deleting
them on rotation would make a leaked key into a destructive one.
