"""One model call, returning complete file contents.

Fast, cheap and fully deterministic to test, because nothing runs outside the
process. It cannot explore: it sees the source it was handed and nothing else,
which is workable only because the sandbox is small.
"""

from typing import cast

from app import llm
from app.knowledge import store
from app.schemas import Citation, CodeProposal
from app.tools import policy

SYSTEM = (
    'You are the coding agent for TaskVault. You propose changes; a human '
    'approves them.\n\n'
    'The documentation passages you are given are binding. They record decisions '
    'that are not visible in the code, and where the code contradicts them the '
    'code is wrong. Ground your change in them and name the ones you used.\n\n'
    'Return complete file contents for every file you edit, not fragments. Match '
    'the surrounding style: single quotes, 100-column lines, comments that say '
    'why rather than what.\n\n'
    f'{policy.CONVENTIONS}'
)

REVISION = (
    '\n\nYour previous proposal was rejected by the review rules for these '
    'reasons. Produce a corrected proposal that fixes them:\n{violations}'
)


class StructuredCodeAgent:
    name = 'structured'

    def _call(self, request: str, context: str, source: dict[str, str], extra: str = ''):
        files = '\n\n'.join(f'--- {path} ---\n{content}' for path, content in source.items())
        model = llm.get_model().with_structured_output(CodeProposal)
        return cast(
            CodeProposal,
            model.invoke(
                [
                    {'role': 'system', 'content': SYSTEM + extra},
                    {
                        'role': 'user',
                        'content': (
                            f'Documentation:\n\n{context}\n\n'
                            f'Source:\n\n{files}\n\n'
                            f'Request: {request}'
                        ),
                    },
                ]
            ),
        )

    def propose(
        self, request: str, citations: list[Citation], source: dict[str, str]
    ) -> CodeProposal:
        context = store.as_context(citations)
        proposal = self._call(request, context, source)

        # One automatic revision, then it goes to the human either way. Looping
        # until the rules pass would hide a model that cannot satisfy them, and
        # the human should see that.
        broken = policy.violations(proposal)
        if broken:
            proposal = self._call(
                request, context, source, REVISION.format(violations='\n'.join(broken))
            )
        return proposal
