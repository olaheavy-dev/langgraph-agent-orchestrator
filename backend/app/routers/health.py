"""Liveness, and a corpus check that actually touches the corpus.

The postmortem in the knowledge base is about a health check that answered from
the HTTP layer while the thing it was protecting was unusable. It would be a
poor joke to repeat that here, so this one reads the corpus off disk.
"""

from fastapi import APIRouter

from app.knowledge import document_names

router = APIRouter(tags=['health'])


@router.get('/health')
def health() -> dict:
    documents = document_names()
    return {
        'status': 'ok' if documents else 'degraded',
        'corpus_documents': len(documents),
    }
