# ADR-002: API keys, compared in constant time

Status: accepted, 2025-11-18.

## Decision

Clients authenticate with a static API key in the `X-API-Key` header. Valid keys
come from the `TASKVAULT_API_KEYS` environment variable, comma-separated.

## Why

A key identifies a tenant, not a person. TaskVault has no concept of a user, no
login, and no session -- adding OAuth would introduce all three to serve a
machine-to-machine integration that only needs to prove which tenant it is.

Keys live in the environment rather than the database because the set changes
roughly twice a year and is managed by whoever operates the deployment. A table
would need an admin surface to be useful, and that surface would need its own
authentication.

## Constant-time comparison is required

Key comparison must use `hmac.compare_digest`, never `==`. This is the only
comparison in the service where an attacker supplies one side and can measure
how long it takes. Ordinary string equality returns early on the first differing
byte, which leaks the length of the matching prefix.

## What this constrains

There is no per-key revocation without a redeploy, and no expiry. Both are
accepted; a compromised key is handled by rotating the environment variable.

Keys are not hashed at rest because they are not stored at rest -- they exist
only in the deployment's secret store.

## When to revisit

Revisit when tenants need to rotate their own keys without operator
involvement, or when the key count passes about fifty and editing one
environment variable stops being reasonable. At that point keys become a table
with a hashed column, and this ADR is superseded rather than amended.
