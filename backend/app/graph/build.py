"""Wiring.

Read top to bottom this is the whole system: classify, then branch to one of
three agents, and on the coding branch pause for a human before anything is
written. Keeping the wiring in one file with no logic in it is what makes that
readable -- the nodes say how, this says what.
"""

from functools import lru_cache
from pathlib import Path

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

from app import config
from app.graph.nodes import apply, approval, chat, classifier, coding, rag
from app.graph.state import State


def build_graph(checkpointer: BaseCheckpointSaver | None = None):
    """Assemble and compile the graph.

    The checkpointer is a parameter rather than a global so tests can compile
    against an in-memory one, and so a deployment can swap SQLite for Postgres
    without touching the graph.
    """
    builder = StateGraph(State)

    builder.add_node('classifier', classifier.classify)
    builder.add_node('chat_agent', chat.chat)
    builder.add_node('rag_agent', rag.answer)
    builder.add_node('coding_agent', coding.propose)
    builder.add_node('approval', approval.request_approval)
    builder.add_node('apply', apply.apply_change)
    builder.add_node('denied', apply.deny)

    builder.add_edge(START, 'classifier')
    builder.add_conditional_edges(
        'classifier',
        classifier.route,
        {'chat': 'chat_agent', 'knowledge': 'rag_agent', 'code': 'coding_agent'},
    )

    builder.add_edge('chat_agent', END)
    builder.add_edge('rag_agent', END)

    # The coding branch is the only cycle: a revision returns to the agent with
    # the human's instructions appended to the conversation.
    builder.add_edge('coding_agent', 'approval')
    builder.add_conditional_edges(
        'approval',
        approval.route,
        {'approve': 'apply', 'deny': 'denied', 'revise': 'coding_agent'},
    )
    builder.add_edge('apply', END)
    builder.add_edge('denied', END)

    return builder.compile(checkpointer=checkpointer)


def _checkpointer(path: Path) -> BaseCheckpointSaver:
    path.parent.mkdir(parents=True, exist_ok=True)
    import sqlite3

    # check_same_thread=False because FastAPI serves sync endpoints from a thread
    # pool, so the connection is used from whichever worker thread took the call.
    connection = sqlite3.connect(str(path), check_same_thread=False)
    return SqliteSaver(connection)


@lru_cache
def get_graph():
    """The application's graph, compiled once against durable storage."""
    return build_graph(_checkpointer(config.get_settings().checkpoint_path))
