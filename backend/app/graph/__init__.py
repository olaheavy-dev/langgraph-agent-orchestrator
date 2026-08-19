"""The orchestrator graph.

Nothing in this package imports FastAPI. The graph is a library that takes a
State and returns updates to it, which is what makes it testable without a
server, runnable in LangGraph Studio, and reusable from a CLI.
"""

from app.graph.build import build_graph, get_graph
from app.graph.state import State

__all__ = ['State', 'build_graph', 'get_graph']
