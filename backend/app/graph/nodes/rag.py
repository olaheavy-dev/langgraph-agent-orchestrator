"""The retrieval agent.

Retrieve then answer, rather than exposing search as a tool the model may skip.
For a corpus this small the search is cheap and the failure mode of not
searching -- answering about TaskVault from general knowledge of similar services
-- is exactly what this project exists to avoid.
"""

from app import llm
from app.graph.nodes._timing import traced
from app.graph.state import State
from app.knowledge import store

SYSTEM = (
    'You answer questions about TaskVault using its own documentation.\n\n'
    'Answer only from the passages provided. Cite the document you drew each '
    'claim from, by filename. If the passages do not answer the question, say '
    'so plainly rather than filling the gap from what you know about similar '
    'services -- an invented answer about this codebase is worse than no answer.'
)


@traced('rag_agent')
def answer(state: State) -> dict:
    question = state['messages'][-1].text()
    citations = store.search(question)

    response = llm.get_model().invoke(
        [
            {'role': 'system', 'content': SYSTEM},
            {
                'role': 'user',
                'content': f'Passages:\n\n{store.as_context(citations)}\n\nQuestion: {question}',
            },
        ]
    )
    sources = ', '.join(sorted({citation.source for citation in citations}))
    return {
        'messages': [response],
        'citations': citations,
        '_detail': f'retrieved {len(citations)} passages from {sources}',
    }
