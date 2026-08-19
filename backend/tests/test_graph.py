"""The graph end to end, with no model and no network.

These are the tests that would catch a rewiring mistake: which node ran, in what
order, and what the human's decision did to the path taken.
"""

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from app.graph import build_graph
from app.graph.nodes.classifier import Classification
from app.schemas import CodeProposal, FileEdit


@pytest.fixture
def graph():
    return build_graph(InMemorySaver())


def config(thread: str = 't1'):
    return {'configurable': {'thread_id': thread}}


def nodes(result) -> list[str]:
    return [event.node for event in result['trace']]


def send(graph, text: str, thread: str = 't1'):
    return graph.invoke({'messages': [{'role': 'user', 'content': text}]}, config(thread))


@pytest.mark.parametrize(
    ('intent', 'expected'), [('chat', 'chat_agent'), ('knowledge', 'rag_agent')]
)
def test_the_classifier_routes_to_the_named_agent(graph, scripted, sandbox, intent, expected):
    scripted(structured=Classification(intent=intent))
    assert expected in nodes(send(graph, 'anything'))


def test_chat_answers_without_touching_the_corpus(graph, scripted, sandbox):
    scripted(reply='hello', structured=Classification(intent='chat'))
    result = send(graph, 'hi')
    assert nodes(result) == ['classifier', 'chat_agent']
    assert not result.get('citations')


def test_knowledge_retrieves_before_answering(graph, scripted, sandbox):
    scripted(reply='answered', structured=Classification(intent='knowledge'))
    result = send(graph, 'why is there a rate limit?')
    assert nodes(result) == ['classifier', 'rag_agent']
    assert len(result['citations']) == 4
    assert all(citation.source.endswith('.md') for citation in result['citations'])


class TwoStepModel:
    """Classifies once, then proposes, and keeps proposing on every later call.

    The coding branch asks for two different shapes, and a revision asks for the
    second one again -- so the queue drains and then repeats its tail.
    """

    def __init__(self, proposal: CodeProposal) -> None:
        self.proposal = proposal
        self._queue = [Classification(intent='code'), proposal]
        self.structured_calls = 0

    def invoke(self, messages, *a, **kw):
        raise AssertionError('the coding branch should only use structured output')

    def with_structured_output(self, schema, *a, **kw):
        outer = self

        class _Structured:
            def invoke(self, messages, *a, **kw):
                outer.structured_calls += 1
                return outer._queue.pop(0) if outer._queue else outer.proposal

        return _Structured()


@pytest.fixture
def coding_graph(graph, monkeypatch, sandbox, proposal):
    """A graph whose coding branch produces one conforming proposal."""
    proposal.edits.append(FileEdit(path='docs/adr-003-rate-limiting.md', new_content='# updated\n'))
    from app import llm

    model = TwoStepModel(proposal)
    monkeypatch.setattr(llm, 'get_model', lambda: model)
    return graph


def test_the_coding_branch_stops_for_approval(coding_graph):
    result = send(coding_graph, 'fix the rate limit boundary')

    assert result['__interrupt__'], 'the graph should suspend rather than write'
    assert nodes(result) == ['classifier', 'coding_agent']
    payload = result['__interrupt__'][0].value
    assert 'rate_limit' in payload['diff']


def test_nothing_is_written_while_approval_is_pending(coding_graph, sandbox):
    before = (sandbox / 'src/taskvault/rate_limit.py').read_text()
    send(coding_graph, 'fix the rate limit boundary')
    assert (sandbox / 'src/taskvault/rate_limit.py').read_text() == before


def test_denying_leaves_the_workspace_alone(coding_graph, sandbox):
    before = (sandbox / 'src/taskvault/rate_limit.py').read_text()
    send(coding_graph, 'fix the rate limit boundary')

    result = coding_graph.invoke(Command(resume='no'), config())
    assert 'denied' in nodes(result)
    assert (sandbox / 'src/taskvault/rate_limit.py').read_text() == before
    assert result['proposal'] is None


def test_approving_writes_the_files_and_opens_a_pull_request(coding_graph, sandbox):
    send(coding_graph, 'fix the rate limit boundary')
    result = coding_graph.invoke(Command(resume='approve'), config())

    assert 'apply' in nodes(result)
    assert (sandbox / 'src/taskvault/rate_limit.py').read_text() == '# replaced\n'

    pull_request = result['pull_request']
    assert pull_request.branch == 'fix/rate-limit-boundary'
    assert 'authored by an automated agent' in pull_request.body
    assert 'adr-003-rate-limiting.md' in pull_request.body
    assert {check.name for check in pull_request.checks} == {'lint', 'format', 'test'}


def test_a_revision_returns_to_the_coding_agent(coding_graph):
    send(coding_graph, 'fix the rate limit boundary')
    result = coding_graph.invoke(Command(resume='Use a leaky bucket instead'), config())

    # Back to the agent, and the instructions kept their original casing.
    assert nodes(result).count('coding_agent') == 2
    assert any('Use a leaky bucket instead' in message.text() for message in result['messages'])


def test_the_run_resumes_from_its_checkpoint_not_from_the_start(coding_graph):
    send(coding_graph, 'fix the rate limit boundary')
    result = coding_graph.invoke(Command(resume='no'), config())
    # One classification for the whole exchange: the decision was not re-routed.
    assert nodes(result).count('classifier') == 1


def test_an_inadmissible_path_writes_nothing_at_all(graph, monkeypatch, sandbox, proposal):
    """A proposal is applied whole or not at all.

    Writing edit by edit would leave the good file changed and the workspace in a
    state no diff describes -- the worst outcome available, because it is neither
    the old code nor the reviewed change.
    """
    from app import llm
    from app.schemas import FileEdit

    proposal.edits = [
        FileEdit(path='src/taskvault/models.py', new_content='# would be written first\n'),
        FileEdit(path='.github/workflows/ci.yml', new_content='jobs: {}'),
    ]
    before = (sandbox / 'src/taskvault/models.py').read_text()

    model = TwoStepModel(proposal)
    monkeypatch.setattr(llm, 'get_model', lambda: model)

    send(graph, 'change everything')
    result = graph.invoke(Command(resume='approve'), config())

    assert (sandbox / 'src/taskvault/models.py').read_text() == before
    assert not (sandbox / '.github/workflows/ci.yml').read_text().startswith('jobs')
    assert 'Nothing was written' in result['messages'][-1].text()
