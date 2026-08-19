"""One turn of conversation, and the approval that may follow it."""

from fastapi import APIRouter

from app import service
from app.schemas import ApprovalRequest, ChatRequest, ChatResponse

router = APIRouter(tags=['chat'])


@router.post('/chat', response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Send a message.

    A `status` of 'awaiting_approval' means the graph is suspended at the coding
    gate and the client must call /approve before anything is written.
    """
    return service.send(request.message, request.thread_id)


@router.post('/approve', response_model=ChatResponse)
def approve(request: ApprovalRequest) -> ChatResponse:
    """Answer a pending approval: 'approve', 'deny', or revised instructions."""
    return service.resume(request.thread_id, request.decision)
