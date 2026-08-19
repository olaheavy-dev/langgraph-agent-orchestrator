"""The human gate.

interrupt() suspends the graph here and the checkpointer persists everything up
to this point. Resuming replays this node from the top, which is why it does
nothing before the interrupt call -- any side effect above it would happen twice.
"""

from langchain_core.messages import HumanMessage
from langgraph.types import interrupt

from app.graph.nodes._timing import traced
from app.graph.state import State

APPROVE = {'y', 'yes', 'approve', 'approved', 'ok', 'lgtm'}
DENY = {'n', 'no', 'deny', 'denied', 'cancel', 'reject'}


@traced('approval')
def request_approval(state: State) -> dict:
    proposal = state.get('proposal')
    decision = interrupt(
        {
            'summary': proposal.summary if proposal else '',
            'diff': state.get('diff', ''),
            'prompt': 'Approve this change, deny it, or reply with revised instructions.',
        }
    )

    # The raw text is preserved: a revision is instructions to the coding agent,
    # and lowercasing it to compare against the keyword sets would corrupt it.
    raw = str(decision).strip()
    choice = raw.lower()

    if choice in APPROVE:
        return {'approval': 'approve', '_detail': 'approved by human'}
    if choice in DENY:
        return {'approval': 'deny', '_detail': 'denied by human'}
    return {
        'approval': 'revise',
        'messages': [HumanMessage(raw)],
        '_detail': 'revision requested',
    }


def route(state: State) -> str:
    return state.get('approval', 'deny')
