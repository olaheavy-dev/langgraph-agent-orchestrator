"""What flows between nodes.

Every field is either accumulated or replaced, and which one it is matters: a
reducer is the difference between a trace that records the whole run and a trace
that only remembers the last node to write to it.
"""

import operator
from typing import Annotated, NotRequired, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

from app.schemas import Citation, CodeProposal, Intent, PullRequest, TraceEvent


class State(TypedDict):
    # add_messages appends and de-duplicates by id, so a node returning one new
    # message does not have to know what came before it.
    messages: Annotated[list[AnyMessage], add_messages]

    # operator.add rather than a replace: every node contributes its own turn and
    # none of them should be able to erase another's. NotRequired because a caller
    # starts a run with a message and nothing else -- the reducer still applies,
    # so the channel accumulates from empty.
    trace: NotRequired[Annotated[list[TraceEvent], operator.add]]

    # Replaced, not accumulated. Each of these describes the current turn only,
    # and carrying the previous turn's proposal forward would let a stale change
    # be applied by a later approval.
    intent: NotRequired[Intent]
    citations: NotRequired[list[Citation]]
    proposal: NotRequired[CodeProposal | None]
    diff: NotRequired[str]
    # What the review rules would still object to, shown to the human rather than
    # silently retried: a model that cannot satisfy them is worth seeing.
    violations: NotRequired[list[str]]
    pull_request: NotRequired[PullRequest | None]

    # Set by the approval node so routing can read the human's decision without
    # re-running the interrupt.
    approval: NotRequired[str]
