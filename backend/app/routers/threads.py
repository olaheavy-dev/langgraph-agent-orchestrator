"""Thread inspection.

Not needed by the UI, and kept because the checkpoint history is the evidence
that the durability claim is true rather than asserted.
"""

from fastapi import APIRouter

from app import service

router = APIRouter(prefix='/threads', tags=['threads'])


@router.get('/{thread_id}/history')
def history(thread_id: str) -> list[dict]:
    return service.history(thread_id)
