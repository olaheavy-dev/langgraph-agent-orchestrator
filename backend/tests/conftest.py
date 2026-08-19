"""Test doubles for the two things that would otherwise need an API key.

Both are deterministic. A test that asserts on routing should fail when routing
breaks, not when a model has an off day, so nothing here is probabilistic.
"""

import hashlib
import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest
from langchain_core.embeddings import Embeddings
from langchain_core.messages import AIMessage

from app import llm
from app.schemas import CodeProposal, FileEdit


class DeterministicEmbeddings(Embeddings):
    """Hash-based vectors.

    Not semantic, but stable and real enough to exercise the actual vector store
    and the actual chunking, which is where the bugs would be. Retrieval quality
    is a question for evals, not for unit tests.
    """

    dimensions = 64

    def _vector(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode()).digest()
        return [digest[i % len(digest)] / 255 for i in range(self.dimensions)]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)


class ScriptedModel:
    """Returns whatever the test told it to return.

    Only the two methods the nodes actually use are implemented -- invoke and
    with_structured_output. Subclassing BaseChatModel would mean satisfying an
    interface the graph never touches.
    """

    def __init__(self, reply: str = 'scripted reply', structured: object | None = None) -> None:
        self.reply = reply
        self.structured = structured
        self.calls: list[list] = []

    def invoke(self, messages, *args, **kwargs):
        self.calls.append(messages)
        return AIMessage(self.reply)

    def with_structured_output(self, schema, *args, **kwargs):
        outer = self

        class _Structured:
            def invoke(self, messages, *a, **kw):
                outer.calls.append(messages)
                if outer.structured is None:
                    raise AssertionError(f'no scripted structured output for {schema.__name__}')
                return outer.structured

        return _Structured()


@pytest.fixture(autouse=True)
def _no_real_models(monkeypatch):
    """Nothing in the suite may reach a provider."""
    monkeypatch.setattr(llm, 'get_embeddings', DeterministicEmbeddings)
    monkeypatch.setattr(llm, 'get_model', lambda: ScriptedModel())


@pytest.fixture
def scripted(monkeypatch):
    """Install a model with a scripted answer, and hand it back for assertions."""

    def install(reply: str = 'scripted reply', structured: object | None = None) -> ScriptedModel:
        model = ScriptedModel(reply, structured)
        monkeypatch.setattr(llm, 'get_model', lambda: model)
        return model

    return install


@pytest.fixture
def sandbox(tmp_path, monkeypatch) -> Iterator[Path]:
    """A throwaway copy of the workspace.

    Tests that apply a change write real files, so they write them somewhere
    disposable rather than into the checked-in sandbox.
    """
    from app.config import Settings, get_settings

    source = Path(__file__).resolve().parent.parent / 'workspace'
    destination = tmp_path / 'workspace'
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns('.venv', '.pytest_cache', '.ruff_cache', 'uv.lock'),
    )

    get_settings.cache_clear()
    monkeypatch.setattr(
        'app.config.get_settings',
        lambda: Settings(workspace_root=destination, checkpoint_path=tmp_path / 'cp.sqlite'),
    )
    # The retrieval store caches its index against the old corpus path.
    from app.knowledge import store

    store.get_store.cache_clear()
    yield destination
    get_settings.cache_clear()
    store.get_store.cache_clear()


@pytest.fixture
def proposal() -> CodeProposal:
    return CodeProposal(
        summary='Reject the 101st request in a full window.',
        rationale='adr-003-rate-limiting states the 101st must be rejected.',
        verification='test_a_full_bucket_allows_exactly_capacity fails without it.',
        adrs_consulted=['adr-003-rate-limiting.md'],
        branch='fix/rate-limit-boundary',
        commit_message='fix(rate_limit): reject the 101st request in a full window',
        edits=[FileEdit(path='src/taskvault/rate_limit.py', new_content='# replaced\n')],
    )
