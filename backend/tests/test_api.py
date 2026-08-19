"""The HTTP surface, against a graph with no model behind it.

What these check is the translation: that a suspended graph becomes
'awaiting_approval' with a diff attached, and that a resume lands on the same
thread rather than starting a new conversation.
"""

import pytest
from fastapi.testclient import TestClient
from langgraph.checkpoint.memory import InMemorySaver

from app import service
from app.graph import build_graph
from app.graph.nodes.classifier import Classification
from app.main import app
from app.schemas import FileEdit
from tests.test_graph import TwoStepModel


@pytest.fixture
def client(monkeypatch, sandbox):
    compiled = build_graph(InMemorySaver())
    monkeypatch.setattr(service, 'get_graph', lambda: compiled)
    return TestClient(app)


@pytest.fixture
def coding_client(client, monkeypatch, proposal):
    proposal.edits.append(FileEdit(path='docs/adr-003-rate-limiting.md', new_content='# updated\n'))
    from app import llm

    # One instance, not one per call: the queue is shared state between the
    # classifier's turn and the coding agent's.
    model = TwoStepModel(proposal)
    monkeypatch.setattr(llm, 'get_model', lambda: model)
    return client


def test_health_reports_the_corpus_it_can_actually_read(client):
    body = client.get('/health').json()
    assert body['status'] == 'ok'
    assert body['corpus_documents'] == 9


def test_a_chat_turn_returns_a_thread_to_continue_on(client, scripted):
    scripted(reply='hello', structured=Classification(intent='chat'))
    body = client.post('/chat', json={'message': 'hi'}).json()

    assert body['status'] == 'complete'
    assert body['intent'] == 'chat'
    assert body['reply'] == 'hello'
    assert body['thread_id']
    assert [event['node'] for event in body['trace']] == ['classifier', 'chat_agent']


def test_a_knowledge_turn_comes_back_with_citations(client, scripted):
    scripted(reply='because of the March incident', structured=Classification(intent='knowledge'))
    body = client.post('/chat', json={'message': 'why is there a rate limit?'}).json()

    assert body['intent'] == 'knowledge'
    assert len(body['citations']) == 4
    assert all(citation['source'].endswith('.md') for citation in body['citations'])


def test_a_coding_turn_suspends_and_hands_back_the_diff(coding_client):
    body = coding_client.post('/chat', json={'message': 'fix the rate limit boundary'}).json()

    assert body['status'] == 'awaiting_approval'
    assert body['proposal']['branch'] == 'fix/rate-limit-boundary'
    assert 'rate_limit' in body['diff']
    assert body['pull_request'] is None


def test_approving_continues_the_same_thread(coding_client, sandbox):
    started = coding_client.post('/chat', json={'message': 'fix the rate limit'}).json()
    thread_id = started['thread_id']

    body = coding_client.post(
        '/approve', json={'thread_id': thread_id, 'decision': 'approve'}
    ).json()

    assert body['thread_id'] == thread_id
    assert body['status'] == 'complete'
    assert body['pull_request']['branch'] == 'fix/rate-limit-boundary'
    assert (sandbox / 'src/taskvault/rate_limit.py').read_text() == '# replaced\n'


def test_denying_writes_nothing(coding_client, sandbox):
    before = (sandbox / 'src/taskvault/rate_limit.py').read_text()
    started = coding_client.post('/chat', json={'message': 'fix the rate limit'}).json()

    coding_client.post('/approve', json={'thread_id': started['thread_id'], 'decision': 'deny'})
    assert (sandbox / 'src/taskvault/rate_limit.py').read_text() == before


def test_thread_history_shows_the_run_stopped_and_resumed(coding_client):
    started = coding_client.post('/chat', json={'message': 'fix the rate limit'}).json()
    thread_id = started['thread_id']
    coding_client.post('/approve', json={'thread_id': thread_id, 'decision': 'deny'})

    history = coding_client.get(f'/threads/{thread_id}/history').json()
    # More than one checkpoint means the graph really was persisted mid-run.
    assert len(history) > 1
    assert any('approval' in snapshot['next'] for snapshot in history)
