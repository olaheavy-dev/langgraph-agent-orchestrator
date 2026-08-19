"""The delegating strategy, without a CLI on PATH.

What matters is not that Claude Code works -- that is its own project's problem --
but that this code never lets it near the real workspace, and that whatever it
did comes back as a proposal the graph can hold at the gate.
"""

import pytest

from app import llm
from app.agents.claude_code import ClaudeCodeAgent
from app.agents.structured import StructuredCodeAgent
from app.tools import workspace


@pytest.fixture
def runner_that_edits():
    """Stands in for `claude -p`: edits the copy it is given, and records where."""
    seen: dict[str, object] = {}

    def run(prompt, cwd, timeout):
        seen['prompt'] = prompt
        seen['cwd'] = cwd
        (cwd / 'src/taskvault/rate_limit.py').write_text('# edited by the agent\n')
        (cwd / 'docs/adr-003-rate-limiting.md').write_text('# updated record\n')
        return 'Edited the rate limiter and its ADR.'

    run.seen = seen  # type: ignore[attr-defined]
    return run


def test_the_agent_never_receives_the_real_workspace(
    sandbox, scripted, proposal, runner_that_edits
):
    scripted(structured=proposal)
    before = (sandbox / 'src/taskvault/rate_limit.py').read_text()

    ClaudeCodeAgent(runner_that_edits).propose('fix it', [], workspace.snapshot())

    assert runner_that_edits.seen['cwd'] != sandbox
    # The edit landed in the copy; the workspace is untouched until approval.
    assert (sandbox / 'src/taskvault/rate_limit.py').read_text() == before


def test_edits_made_in_the_copy_come_back_as_the_proposal(
    sandbox, scripted, proposal, runner_that_edits
):
    scripted(structured=proposal)

    result = ClaudeCodeAgent(runner_that_edits).propose('fix it', [], workspace.snapshot())

    paths = {edit.path for edit in result.edits}
    assert paths == {'src/taskvault/rate_limit.py', 'docs/adr-003-rate-limiting.md'}
    assert result.edits[1].new_content == '# edited by the agent\n'


def test_the_copy_is_discarded_afterwards(sandbox, scripted, proposal, runner_that_edits):
    scripted(structured=proposal)
    ClaudeCodeAgent(runner_that_edits).propose('fix it', [], workspace.snapshot())
    assert not runner_that_edits.seen['cwd'].exists()  # type: ignore[union-attr]


def test_the_conventions_are_given_to_the_agent(sandbox, scripted, proposal, runner_that_edits):
    scripted(structured=proposal)
    ClaudeCodeAgent(runner_that_edits).propose('fix it', [], workspace.snapshot())
    prompt = runner_that_edits.seen['prompt']
    assert 'conventional commit' in prompt
    assert 'ADR' in prompt


def test_a_run_that_changed_nothing_says_so(sandbox, scripted):
    scripted()

    def run(prompt, cwd, timeout):
        return 'I could not find anything to change.'

    result = ClaudeCodeAgent(run).propose('fix it', [], workspace.snapshot())
    assert result.edits == []
    assert result.summary == 'No change was made.'


def test_a_failing_cli_surfaces_rather_than_producing_an_empty_change(sandbox, scripted):
    scripted()

    def run(prompt, cwd, timeout):
        raise RuntimeError('claude exited 1: not authenticated')

    with pytest.raises(RuntimeError, match='not authenticated'):
        ClaudeCodeAgent(run).propose('fix it', [], workspace.snapshot())


def test_the_structured_strategy_retries_once_when_rules_are_broken(sandbox, monkeypatch, proposal):
    """The seeded proposal touches rate_limit.py with no ADR, so adr-drift fires."""
    calls: list[str] = []

    class Recording:
        def with_structured_output(self, schema, *a, **kw):
            class _S:
                def invoke(self, messages, *a, **kw):
                    calls.append(messages[0]['content'])
                    return proposal

            return _S()

    monkeypatch.setattr(llm, 'get_model', lambda: Recording())
    StructuredCodeAgent().propose('fix it', [], workspace.snapshot())

    assert len(calls) == 2
    assert 'rejected by the review rules' in calls[1]
