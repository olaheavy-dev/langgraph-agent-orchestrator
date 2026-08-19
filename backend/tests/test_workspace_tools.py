import pytest

from app.tools import workspace
from app.tools.workspace import PathOutsideWorkspace


@pytest.mark.parametrize(
    'escape',
    ['../secrets.txt', '../../etc/passwd', 'src/../../outside.py', '/etc/passwd'],
)
def test_paths_cannot_escape_the_sandbox(sandbox, escape):
    with pytest.raises(PathOutsideWorkspace):
        workspace.resolve(escape)


def test_a_symlink_out_of_the_sandbox_is_refused(sandbox, tmp_path):
    outside = tmp_path / 'outside.py'
    outside.write_text('secret')
    (sandbox / 'link.py').symlink_to(outside)
    # The check is on the resolved path, which is the only reason this fails.
    with pytest.raises(PathOutsideWorkspace):
        workspace.resolve('link.py')


def test_ci_configuration_may_not_be_written(sandbox):
    with pytest.raises(PathOutsideWorkspace):
        workspace.write_file('.github/workflows/ci.yml', 'jobs: {}')


def test_snapshot_offers_source_but_not_the_corpus(sandbox):
    snapshot = workspace.snapshot()
    assert 'src/taskvault/rate_limit.py' in snapshot
    assert not any(path.startswith('docs/') for path in snapshot)


def test_write_then_read_round_trips(sandbox):
    workspace.write_file('src/taskvault/new.py', 'x = 1\n')
    assert workspace.read_file('src/taskvault/new.py') == 'x = 1\n'
