"""How a code change gets produced.

Two strategies, one interface. The graph does not care which is in use: it
receives a CodeProposal, checks it against the review rules, and holds it at the
approval gate either way.

That indifference is deliberate. Delegating to a real coding agent is more
capable than asking a model for file contents in one shot, but it must not be
allowed to change what the human is approving -- so the seam is drawn at "produce
a proposal", and applying it stays the graph's job.
"""

from typing import Protocol

from app import config
from app.schemas import Citation, CodeProposal


class CodeAgent(Protocol):
    """Produces a change without applying it."""

    name: str

    def propose(
        self, request: str, citations: list[Citation], source: dict[str, str]
    ) -> CodeProposal: ...


def get_agent() -> CodeAgent:
    """The configured strategy. Imported lazily so the unused one's dependencies
    -- a CLI on PATH, in the delegating case -- are never a hard requirement."""
    if config.get_settings().code_agent == 'claude_code':
        from app.agents.claude_code import ClaudeCodeAgent

        return ClaudeCodeAgent()

    from app.agents.structured import StructuredCodeAgent

    return StructuredCodeAgent()
