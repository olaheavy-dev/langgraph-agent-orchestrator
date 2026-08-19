"""Retrieval over the corpus.

Kept apart from the graph so that both the retrieval agent and the coding agent
can search the same index without either importing the other. The coding agent
consulting the ADRs before it writes code is the point of the whole project, and
it works because retrieval is a shared service rather than one node's private
detail.
"""

from functools import lru_cache

from langchain_core.vectorstores import InMemoryVectorStore

from app import config, llm
from app.knowledge import load_chunks
from app.schemas import Citation


@lru_cache
def get_store() -> InMemoryVectorStore:
    """Embedded on first use rather than at import, so this module can be
    imported without an API key.

    InMemoryVectorStore rather than a real index: for forty short chunks the
    index structure buys nothing and costs a dependency. The interface is the
    same, so swapping in pgvector later is a change to this function alone.
    """
    chunks = load_chunks()
    return InMemoryVectorStore.from_texts(
        [chunk.text for chunk in chunks],
        embedding=llm.get_embeddings(),
        metadatas=[
            {'source': chunk.source, 'heading': chunk.heading, 'body': chunk.body}
            for chunk in chunks
        ],
    )


def search(query: str, k: int | None = None) -> list[Citation]:
    """Return the passages closest to the query, ready to show to a reader."""
    k = k or config.get_settings().retrieve_count
    hits = get_store().similarity_search_with_score(query, k=k)
    return [
        Citation(
            source=document.metadata.get('source', ''),
            heading=document.metadata.get('heading', ''),
            text=document.metadata.get('body') or document.page_content,
            score=round(float(score), 4),
        )
        for document, score in hits
    ]


def cited_documents(citations: list[Citation]) -> dict[str, str]:
    """Full text of every document a retrieval touched, keyed by workspace path.

    An excerpt is enough to answer a question and not enough to edit a file. An
    agent asked to amend an ADR from a 700-character passage rewrites it from
    scratch, silently dropping everything it was not shown.
    """
    from app.tools import workspace

    names = dict.fromkeys(citation.source for citation in citations)
    return {f'docs/{name}': workspace.read_or_empty(f'docs/{name}') for name in names}


def as_context(citations: list[Citation]) -> str:
    """Format retrieved passages for a prompt, labelled so the model can cite them."""
    return '\n\n'.join(
        f'[{citation.source} :: {citation.heading}]\n{citation.text}' for citation in citations
    )
