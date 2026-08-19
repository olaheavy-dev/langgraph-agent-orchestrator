from app.schemas import FileEdit
from app.tools import diffing


def test_a_diff_shows_only_what_changed():
    before = {'a.py': 'one\ntwo\nthree\n'}
    edits = [FileEdit(path='a.py', new_content='one\nTWO\nthree\n')]
    diff = diffing.render(edits, before)
    assert '-two' in diff and '+TWO' in diff
    assert '+one' not in diff


def test_an_unchanged_file_produces_no_diff():
    before = {'a.py': 'same\n'}
    assert diffing.render([FileEdit(path='a.py', new_content='same\n')], before) == ''


def test_a_new_file_is_marked_as_created():
    diff = diffing.render([FileEdit(path='new.py', new_content='x\n')], {})
    assert '/dev/null' in diff


def test_stat_counts_lines_both_ways():
    before = {'a.py': 'one\ntwo\n'}
    edits = [FileEdit(path='a.py', new_content='one\ntwo\nthree\n')]
    assert diffing.stat(edits, before) == '1 file changed, +1 -0'


def test_editing_a_file_the_agent_never_saw_diffs_against_disk(sandbox):
    """A rewrite must render as a modification, not a creation.

    The agent is handed src/ and the documents it cited. If it edits anything
    else, diffing against what it was shown would report /dev/null and hide
    every line the rewrite deletes -- which is the one case a reviewer most needs
    to see.
    """
    edits = [FileEdit(path='docs/adr-001-storage.md', new_content='# ADR-001\n\nRewritten.\n')]

    before = diffing.baseline(edits, known={})
    diff = diffing.render(edits, before)

    assert '/dev/null' not in diff
    assert 'SQLite as the primary store' in diff  # the real heading, being removed
    assert diff.count('\n-') > 10


def test_a_genuinely_new_file_still_reads_as_a_creation(sandbox):
    edits = [FileEdit(path='docs/adr-004-caching.md', new_content='# ADR-004\n')]
    diff = diffing.render(edits, diffing.baseline(edits, known={}))
    assert '/dev/null' in diff
