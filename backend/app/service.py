"""The seam between the graph and HTTP.

Routers call this; the graph does not know it exists. Translating a graph result
into a response is real logic -- an interrupted run and a completed one look quite
different -- and it does not belong in a route handler.
"""

import uuid
from typing import Any

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from app.graph import get_graph
from app.schemas import (
    ChatResponse,
    Citation,
    CodeProposal,
    PullRequest,
    TraceEvent,
)


def new_thread_id() -> str:
    return str(uuid.uuid4())


def _config(thread_id: str) -> RunnableConfig:
    return {'configurable': {'thread_id': thread_id}}


def _interrupt_payload(result: dict[str, Any]) -> dict | None:
    """The value passed to interrupt(), if the run stopped at one.

    LangGraph returns pending interrupts under '__interrupt__' rather than
    raising, so a completed run and a suspended one are told apart by this key.
    """
    pending = result.get('__interrupt__')
    if not pending:
        return None
    value = pending[0].value
    return value if isinstance(value, dict) else {'prompt': str(value)}


def _last_reply(result: dict[str, Any]) -> str:
    for message in reversed(result.get('messages', [])):
        if getattr(message, 'type', None) == 'ai':
            return message.text()
    return ''


def _to_response(thread_id: str, result: dict[str, Any]) -> ChatResponse:
    trace = [
        event if isinstance(event, TraceEvent) else TraceEvent(**event)
        for event in result.get('trace', [])
    ]
    citations = [
        c if isinstance(c, Citation) else Citation(**c) for c in result.get('citations') or []
    ]

    proposal = result.get('proposal')
    if proposal is not None and not isinstance(proposal, CodeProposal):
        proposal = CodeProposal(**proposal)

    pull_request = result.get('pull_request')
    if pull_request is not None and not isinstance(pull_request, PullRequest):
        pull_request = PullRequest(**pull_request)

    interrupted = _interrupt_payload(result)

    return ChatResponse(
        thread_id=thread_id,
        status='awaiting_approval' if interrupted else 'complete',
        intent=result.get('intent'),
        reply=interrupted['prompt'] if interrupted else _last_reply(result),
        citations=citations,
        trace=trace,
        proposal=proposal,
        diff=result.get('diff', ''),
        violations=result.get('violations') or [],
        pull_request=pull_request,
    )


def send(message: str, thread_id: str | None = None) -> ChatResponse:
    """Run one turn. May return with the graph suspended at the approval gate."""
    thread_id = thread_id or new_thread_id()
    result = get_graph().invoke({'messages': [HumanMessage(message)]}, config=_config(thread_id))
    return _to_response(thread_id, result)


def resume(thread_id: str, decision: str) -> ChatResponse:
    """Answer a pending approval and let the graph continue from its checkpoint.

    Command(resume=...) rather than a fresh invoke: the graph is mid-run, and
    starting a new one would re-classify the decision text as though it were a
    new request.
    """
    result = get_graph().invoke(Command(resume=decision), config=_config(thread_id))
    return _to_response(thread_id, result)


def history(thread_id: str) -> list[dict[str, Any]]:
    """Every checkpoint on a thread, newest first.

    Exposed because it is the honest way to show that the graph is durable: the
    run really did stop, and really did resume from where it stopped.
    """
    return [
        {
            'checkpoint_id': snapshot.config.get('configurable', {}).get('checkpoint_id'),
            'next': list(snapshot.next),
            'trace': [
                event.node if isinstance(event, TraceEvent) else event.get('node')
                for event in snapshot.values.get('trace', [])
            ],
        }
        for snapshot in get_graph().get_state_history(_config(thread_id))
    ]
