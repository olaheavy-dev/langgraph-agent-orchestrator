"""API-key authentication.

Keys identify a tenant, not a person. Everything a key can see is scoped by
owner_key at the query level rather than filtered after the fact -- see
adr-002-auth for why that boundary sits in storage.
"""

import hmac
import os

HEADER = 'X-API-Key'


def known_keys() -> set[str]:
    """Keys are supplied as a comma-separated environment variable.

    Adequate for the current tenant count. adr-002-auth records the threshold at
    which this should become a table.
    """
    raw = os.environ.get('TASKVAULT_API_KEYS', '')
    return {key.strip() for key in raw.split(',') if key.strip()}


def is_valid(candidate: str | None) -> bool:
    """Compare against every known key in constant time.

    hmac.compare_digest rather than ==: key comparison is the one place in this
    service where an attacker controls one side of the comparison and can time it.
    """
    if not candidate:
        return False
    return any(hmac.compare_digest(candidate, key) for key in known_keys())
