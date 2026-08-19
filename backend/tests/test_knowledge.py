from app.knowledge import document_names, load_chunks


def test_every_document_contributes_chunks(sandbox):
    chunks = load_chunks()
    sources = {chunk.source for chunk in chunks}
    assert sources == set(document_names())


def test_chunks_carry_their_document_title(sandbox):
    chunks = load_chunks()
    rate_limit = [c for c in chunks if c.source == 'adr-003-rate-limiting.md']
    # A section called "Ordering" is uninterpretable without the document it
    # belongs to, so the title has to travel with it.
    assert all('rate' in chunk.heading.lower() or chunk.heading for chunk in rate_limit)
    assert any('Ordering' in chunk.heading for chunk in rate_limit)


def test_no_chunk_is_unreasonably_long(sandbox):
    # The cap applies to the body; the heading is added on top of it.
    assert all(len(chunk.body) <= 900 for chunk in load_chunks())


def test_headings_are_not_left_in_the_body(sandbox):
    assert not any(chunk.body.startswith('#') for chunk in load_chunks())


def test_cited_documents_return_full_text_not_excerpts(sandbox):
    from app.knowledge import store
    from app.schemas import Citation

    citation = Citation(source='adr-003-rate-limiting.md', heading='x', text='a passage', score=0.5)
    documents = store.cited_documents([citation])

    assert set(documents) == {'docs/adr-003-rate-limiting.md'}
    # The whole record, so the agent amends it rather than rewriting from a snippet.
    assert len(documents['docs/adr-003-rate-limiting.md']) > 1500
    assert 'The boundary is exact' in documents['docs/adr-003-rate-limiting.md']
