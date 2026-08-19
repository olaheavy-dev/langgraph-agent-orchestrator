"""The knowledge base: TaskVault's engineering documentation.

The corpus is the documentation of the service in backend/workspace -- a
different codebase from the one running it. That separation is what makes retrieval
load-bearing rather than decorative: the decisions in these documents are not
derivable from reading the code, and in four places the code contradicts them.

Chunks split on headings first, because a heading marks a change of subject and
a chunk spanning two subjects retrieves well for neither. Long sections split
again on paragraphs, since an embedding of a thousand words is an average of
everything in them and matches nothing sharply.
"""

import re
from dataclasses import dataclass
from pathlib import Path

from app import config

MAX_CHUNK_CHARS = 700


def docs_dir() -> Path:
    """The corpus lives beside the code it documents, inside the sandbox.

    That placement is deliberate: the ADR rule in contributing.md requires a
    change to the architecture to update the record explaining it, which is only
    enforceable if the agent can edit both.
    """
    return config.get_settings().workspace_root / 'docs'


@dataclass(frozen=True)
class Chunk:
    # What gets embedded: the heading travels with the prose, because a section
    # is largely about what its own title says it is about.
    text: str
    source: str
    heading: str
    # The prose alone, for display under a citation that already shows the
    # heading above it.
    body: str


def _split_long(body: str) -> list[str]:
    """Break an oversized section on paragraph boundaries rather than mid-idea."""
    paragraphs = [part.strip() for part in body.split('\n\n') if part.strip()]
    chunks: list[str] = []
    current = ''
    for paragraph in paragraphs:
        candidate = f'{current}\n\n{paragraph}'.strip()
        if current and len(candidate) > MAX_CHUNK_CHARS:
            chunks.append(current)
            current = paragraph
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def load_chunks(directory: Path | None = None) -> list[Chunk]:
    """Read the corpus, one chunk per section."""
    directory = directory or docs_dir()
    chunks: list[Chunk] = []

    for path in sorted(directory.glob('*.md')):
        title = ''
        for block in re.split(r'\n(?=#)', path.read_text()):
            block = block.strip()
            if not block:
                continue

            lines = block.splitlines()
            heading = lines[0].lstrip('#').strip() if lines[0].startswith('#') else ''
            body = '\n'.join(lines[1:] if heading else lines).strip()

            # A document's own title prefixes its sections, so a chunk about
            # "Ordering" still carries the fact that it is about rate limiting.
            if heading and not title:
                title = heading
            label = heading if heading == title else f'{title} -- {heading}' if heading else title

            if not body:
                continue

            for part in _split_long(body):
                chunks.append(
                    Chunk(
                        text=f'{label}\n\n{part}' if label else part,
                        source=path.name,
                        heading=label,
                        body=part,
                    )
                )

    return chunks


def document_names(directory: Path | None = None) -> list[str]:
    """The corpus filenames, for prompting a model about what it may cite."""
    directory = directory or docs_dir()
    return sorted(path.name for path in directory.glob('*.md'))
