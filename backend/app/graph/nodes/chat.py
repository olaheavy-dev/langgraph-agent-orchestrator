"""The fallback agent: no retrieval, no tools, just the conversation."""

from app import llm
from app.graph.nodes._timing import traced
from app.graph.state import State

SYSTEM = (
    'You are the conversational agent of an orchestrator that also has a '
    'retrieval agent and a coding agent working on a service called TaskVault. '
    'Answer briefly and plainly. If the user seems to want something about '
    'TaskVault itself, say which agent would handle it rather than guessing at '
    'the answer yourself.'
)


@traced('chat_agent')
def chat(state: State) -> dict:
    response = llm.get_model().invoke([{'role': 'system', 'content': SYSTEM}, *state['messages']])
    return {'messages': [response], '_detail': 'answered without retrieval'}
