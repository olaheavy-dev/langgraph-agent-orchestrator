import pytest

from app.schemas import FileEdit
from app.tools import policy


def test_a_conforming_proposal_has_no_violations(proposal):
    proposal.edits.append(FileEdit(path='docs/adr-003-rate-limiting.md', new_content='# x\n'))
    assert policy.violations(proposal) == []


def test_touching_architecture_without_an_adr_is_caught(proposal):
    # The rule from contributing.md, and the one CI enforces as adr-drift.
    assert any('adr-drift' in problem for problem in policy.violations(proposal))


@pytest.mark.parametrize(
    'branch', ['rate-limit-fix', 'Fix/Rate-Limit', 'feature/rate-limit', 'fix/']
)
def test_branch_names_must_be_type_slash_description(proposal, branch):
    proposal.branch = branch
    assert any('not type/short-description' in problem for problem in policy.violations(proposal))


@pytest.mark.parametrize(
    'subject',
    [
        'Fix the rate limiter',
        'fix: Reject the 101st request',
        'fix(rate_limit): reject the 101st request.',
        'reject the 101st request',
    ],
)
def test_commit_subjects_must_be_conventional(proposal, subject):
    proposal.commit_message = subject
    assert any('conventional commit' in problem for problem in policy.violations(proposal))


def test_an_oversized_change_is_flagged(proposal):
    proposal.edits = [FileEdit(path=f'src/taskvault/m{i}.py', new_content='') for i in range(5)]
    assert any('more than one change' in problem for problem in policy.violations(proposal))


def test_a_blank_pr_body_field_is_flagged(proposal):
    proposal.verification = '   '
    assert any('verification' in problem for problem in policy.violations(proposal))


def test_protected_paths_are_caught_before_a_human_is_asked(proposal, sandbox):
    """The agent may change the service, not the rules it is judged by."""
    proposal.edits.append(FileEdit(path='.github/workflows/ci.yml', new_content='jobs: {}'))
    assert any('protected' in problem for problem in policy.violations(proposal))


def test_a_path_escaping_the_sandbox_is_caught(proposal, sandbox):
    proposal.edits.append(FileEdit(path='../../escape.py', new_content='x'))
    assert any('outside the workspace' in problem for problem in policy.violations(proposal))
