"""A decorator that records what each node did and how long it took.

Cross-cutting and dull, so it lives here rather than being repeated at the top
and bottom of six node functions. The trace it produces is what the client
renders to show how an answer arrived.
"""

import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from app.schemas import TraceEvent


def traced(name: str) -> Callable:
    """Wrap a node so its turn appears in state['trace'].

    The node may set a human-readable detail by returning a '_detail' key, which
    is stripped before the update reaches the graph -- it is a channel to this
    decorator, not a field of State.
    """

    def decorate(node: Callable[..., dict[str, Any]]) -> Callable[..., dict[str, Any]]:
        @wraps(node)
        def run(*args: Any, **kwargs: Any) -> dict[str, Any]:
            started = time.perf_counter()
            update = node(*args, **kwargs)
            detail = update.pop('_detail', '') if isinstance(update, dict) else ''
            elapsed = int((time.perf_counter() - started) * 1000)
            event = TraceEvent(node=name, detail=detail, elapsed_ms=elapsed)
            return {**update, 'trace': [event]}

        return run

    return decorate
