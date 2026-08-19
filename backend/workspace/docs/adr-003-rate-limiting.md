# ADR-003: Per-key token bucket, 100 requests per minute

Status: accepted, 2026-03-20. Written in response to the 2026-03-14 incident.

## Decision

Each API key gets a token bucket holding 100 tokens, refilling continuously at
100 tokens per minute. A request costs one token. A request that finds an empty
bucket is rejected with HTTP 429.

## Why these numbers

100 per minute is roughly four times the busiest observed legitimate tenant, and
roughly one fortieth of what the runaway client in the March incident produced.
The gap between those two figures is wide enough that the limit does not need to
be precise -- it needs to be present.

Continuous refill rather than a fixed window: a fixed window lets a client spend
its whole allowance in the last second of one window and again in the first
second of the next, which is the exact burst shape that took the service down.

## Per key, not per IP

The March incident came from a single tenant behind a NAT shared with three
others. Limiting by IP would have throttled all four. The limit belongs to the
thing that owns the quota, which is the key.

## Ordering

Authentication runs before rate limiting. An unauthenticated request must not be
able to consume another tenant's tokens, and rejecting an unknown key is cheaper
than accounting for it.

## What this constrains

Buckets are held in process memory. With two instances behind a load balancer,
each would enforce its own 100 per minute and the effective limit would be 200.
Before a second instance is deployed, buckets must move to shared storage --
this is a hard prerequisite, not a follow-up.

## The boundary is exact

A key may spend exactly 100 requests from a full bucket. The 101st is rejected.
An implementation that allows 101 has failed the requirement, and the boundary
is the part most likely to be got wrong, so it is the part that must be tested
directly.
