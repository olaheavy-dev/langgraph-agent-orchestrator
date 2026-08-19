"""The coding agent's turn.

Retrieval happens here rather than inside the strategies, because both of them
need the same passages and the citations belong in state either way -- showing a
reviewer what the change was grounded in is the point of the project.

The node does not know how the proposal was produced. It checks it against the
review rules and renders it for a human, and that is the same work whether one
model call wrote the files or a coding agent explored the sandbox to do it.
"""

from app.agents import get_agent
from app.graph.nodes._timing import traced
from app.graph.state import State
from app.knowledge import store
from app.tools import diffing, policy, workspace


@traced('coding_agent')
def propose(state: State) -> dict:
    request = state['messages'][-1].text()
    citations = store.search(request)
    # The code, plus the full text of any document the retrieval cited: the
    # agent is expected to amend those, and cannot amend what it has only seen
    # an excerpt of.
    source = workspace.snapshot() | store.cited_documents(citations)

    agent = get_agent()
    proposal = agent.propose(request, citations, source)

    broken = policy.violations(proposal)
    before = diffing.baseline(proposal.edits, source)
    diff = diffing.render(proposal.edits, before)

    detail = (
        f'{agent.name}: {diffing.stat(proposal.edits, before)}, '
        f'grounded in {len(citations)} passages'
    )
    if broken:
        detail += f', {len(broken)} rule violation(s) remain'

    return {
        'proposal': proposal,
        'diff': diff,
        'citations': citations,
        'violations': broken,
        '_detail': detail,
    }
