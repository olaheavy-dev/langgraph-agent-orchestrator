"""Deciding which agent should answer.

A separate node rather than a router function, because the decision costs a
model call and belongs in the trace where a reader can see it was made.
"""

from typing import cast

from pydantic import BaseModel, Field

from app import llm
from app.graph.nodes._timing import traced
from app.graph.state import State
from app.schemas import Intent

SYSTEM = (
    'Classify what the user wants from a system that has three agents.\n\n'
    '"code" -- they want a change made to the TaskVault codebase: a fix, a new '
    'behaviour, a test. Anything that would end in an edit.\n'
    '"knowledge" -- they are asking about TaskVault: how it works, why a decision '
    'was made, what the API contract says, what happened in an incident.\n'
    '"chat" -- anything else: greetings, questions about the assistant itself, '
    'small talk.\n\n'
    'When a request is about TaskVault but asks only to explain rather than to '
    'change, it is "knowledge", not "code".'
)


class Classification(BaseModel):
    intent: Intent = Field(description='One of: chat, knowledge, code.')


@traced('classifier')
def classify(state: State) -> dict:
    model = llm.get_model().with_structured_output(Classification)
    result = cast(
        Classification,
        model.invoke(
            [
                {'role': 'system', 'content': SYSTEM},
                {'role': 'user', 'content': state['messages'][-1].text()},
            ]
        ),
    )
    return {'intent': result.intent, '_detail': f'routed to {result.intent}'}


def route(state: State) -> str:
    """Read the classifier's decision. Kept separate so the edge stays declarative."""
    return state.get('intent', 'chat')
