# Incident 2026-03-14: TaskVault unavailable for 47 minutes

## What happened

A tenant deployed a retry loop with no backoff. A failing request retried
immediately, and each retry failed the same way, producing roughly 4,000
requests per minute from one API key against a service that had no rate limit at
all.

SQLite's single writer (adr-001-storage) serialised the resulting writes. Request
handlers blocked on the write lock, the worker pool filled, and requests from
every other tenant began timing out. The service was effectively down for 47
minutes for all twenty tenants.

## Detection

A tenant emailed. There was no alert on request rate, and the health check
continued to pass throughout, because `/health` touches neither storage nor the
worker pool and was answered promptly the whole time.

## Resolution

The offending key was removed from `TASKVAULT_API_KEYS` and the service was
redeployed. Recovery was immediate once the load stopped.

## What was wrong beneath the immediate cause

The retry loop was the trigger, not the cause. Three things made a single
misbehaving client sufficient to take down every tenant:

There was no limit on how much of a shared resource one key could consume. That
was addressed by adr-003-rate-limiting.

The health check proved nothing. It answered from the HTTP layer alone, so it
reported healthy while the thing it existed to protect was unusable. This is
still open.

The single-writer constraint was documented but its blast radius was not. The
ADR said writes serialise; nobody had written down that serialised writes under
load take the read path with them.

## Actions

| Action | Status |
| --- | --- |
| Per-key rate limiting | Done -- adr-003-rate-limiting |
| Alert on per-key request rate | Done |
| Health check that exercises a real query | Open |
| Document the write-lock blast radius in adr-001 | Open |

## The rule that came out of it

The PR that introduced the retry loop was 900 lines and approved in four
minutes. Pull requests are now expected to be small enough to actually read, and
that expectation is written into contributing.md rather than left as a lesson
people remember for a quarter.
