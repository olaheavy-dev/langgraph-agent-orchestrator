"""Writing an approved change, then checking it the way CI would.

This is the only node that mutates anything outside the graph, and it runs only
on the approved branch. The checks run after the write rather than before,
because the workspace's own pipeline is the honest judge of whether the change
holds up -- and if it fails, the pull request says so rather than hiding it.
"""

from langchain_core.messages import AIMessage

from app import config
from app.graph.nodes._timing import traced
from app.graph.state import State
from app.schemas import CheckResult, PullRequest
from app.tools import workspace
from app.tools.publisher import LocalPublisher, render_body


@traced('apply')
def apply_change(state: State) -> dict:
    proposal = state.get('proposal')
    if proposal is None:
        return {'messages': [AIMessage('Nothing to apply.')]}

    # Every path is checked before any file is written. Writing as we go would
    # leave the workspace half-changed when the fourth edit turns out to be
    # inadmissible, and nothing on disk would record that it had happened.
    refused = [edit.path for edit in proposal.edits if not workspace.is_writable(edit.path)]
    if refused:
        return {
            'messages': [
                AIMessage(
                    'Nothing was written. These paths may not be modified: ' + ', '.join(refused)
                )
            ],
            'proposal': None,
            '_detail': f'refused {len(refused)} path(s), no files written',
        }

    for edit in proposal.edits:
        workspace.write_file(edit.path, edit.new_content)

    checks = [
        CheckResult(name=name, passed=passed, output=output)
        for name, passed, output in workspace.run_checks()
    ]

    pull_request = PullRequest(
        branch=proposal.branch,
        title=proposal.commit_message,
        body=render_body(proposal, checks),
        diff=state.get('diff', ''),
        checks=checks,
    )

    settings = config.get_settings()
    location = LocalPublisher(settings.checkpoint_path.parent / 'pull-requests').publish(
        pull_request
    )

    failed = [check.name for check in checks if not check.passed]
    verdict = f'checks failed: {", ".join(failed)}' if failed else 'all checks passed'
    summary = (
        f'Applied to `{proposal.branch}` and opened a pull request -- {verdict}.\n\n'
        f'{proposal.summary}\n\nReview artifact: `{location}`'
    )

    return {
        'messages': [AIMessage(summary)],
        'pull_request': pull_request,
        '_detail': verdict,
    }


@traced('denied')
def deny(state: State) -> dict:
    """The change is dropped and the proposal cleared, so a later approval on this
    thread cannot resurrect it."""
    return {
        'messages': [AIMessage('Change denied. Nothing was written to the workspace.')],
        'proposal': None,
        'diff': '',
        '_detail': 'no files written',
    }
