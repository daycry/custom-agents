import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.fixture
def api():
    path = Path(__file__).with_name('context-footprint.py')
    spec = importlib.util.spec_from_file_location('context_footprint_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_reports_source_size_separately_from_runtime_cost(api, tmp_path):
    (tmp_path / 'agents').mkdir()
    text = '# Agent\nRequirements and checks.\n'
    (tmp_path / 'agents/worker.md').write_bytes(text.encode('utf-8'))
    result = api.report(tmp_path, ['agents/worker.md'])
    assert result['status'] == 'ok', result
    row = result['files'][0]
    assert row['characters'] == len(text)
    assert row['bytes'] == len(text.encode('utf-8'))
    assert row['estimated_tokens'] == len(text) / 4
    assert result['billed_tokens'] is None and result['native_observation'] is None
    assert result['method'] == 'characters/4'


def test_comparison_requires_the_same_complete_path_set(api, tmp_path):
    (tmp_path / 'a.md').write_text('a' * 100)
    before = api.report(tmp_path, ['a.md'])
    (tmp_path / 'a.md').write_text('a' * 60)
    after = api.report(tmp_path, ['a.md'], before)
    assert after['comparison']['comparable']
    assert after['comparison']['delta_characters'] == -40
    assert after['comparison']['reduction_percent'] == 40
    (tmp_path / 'b.md').write_text('b')
    different = api.report(tmp_path, ['a.md', 'b.md'], before)
    assert not different['comparison']['comparable']
    assert different['comparison']['reduction_percent'] is None
    (tmp_path / 'a.md').unlink()
    missing = api.report(tmp_path, ['a.md'], before)
    assert not missing['complete'] and not missing['comparison']['comparable']


def test_reference_size_is_not_counted_as_eager_content(api, tmp_path):
    reference = tmp_path / 'agent-kits/worker/references/details.md'
    reference.parent.mkdir(parents=True)
    reference.write_text('a' * 100)
    (tmp_path / 'agent.md').write_text('b' * 40)
    result = api.report(tmp_path, ['agent.md', reference.relative_to(tmp_path).as_posix()])
    assert result['totals']['entry_characters'] == 40
    assert result['totals']['reference_characters'] == 100


def test_invalid_baseline_is_not_treated_as_zero(api, tmp_path):
    (tmp_path / 'a.md').write_text('text')
    bad = api.report(tmp_path, ['a.md'], {'files': []})
    assert not bad['comparison']['comparable']
    assert bad['comparison']['reduction_percent'] is None


def test_newlines_do_not_create_artificial_character_savings(api, tmp_path):
    source = tmp_path / 'a.md'
    source.write_bytes(b'first\r\nsecond\r\n')
    before = api.report(tmp_path, ['a.md'])
    source.write_bytes(b'first\nsecond\n')
    after = api.report(tmp_path, ['a.md'], before)
    assert after['comparison']['reduction_percent'] == 0
    assert before['files'][0]['bytes'] > after['files'][0]['bytes']


def test_discovery_ignores_top_level_skill_files_but_reports_missing_skill(api, tmp_path):
    for folder in ['agents', 'commands', 'skills']:
        (tmp_path / folder).mkdir()
    (tmp_path / 'skills/README.md').write_text('catalogue')
    (tmp_path / 'skills/example').mkdir()
    (tmp_path / 'skills/example/SKILL.md').write_text('instructions')
    value = api.report(tmp_path)
    assert value['complete'], value
    assert [r['path'] for r in value['files']] == ['skills/example/SKILL.md']
    (tmp_path / 'skills/example/SKILL.md').unlink()
    assert not api.report(tmp_path)['complete']


def test_root_reference_and_invalid_utf8(api, tmp_path):
    (tmp_path / 'references').mkdir()
    (tmp_path / 'references/a.md').write_bytes(b'abcd')
    assert api.report(tmp_path, ['references/a.md'])['totals']['reference_characters'] == 4
    (tmp_path / 'references/a.md').write_bytes(b'\xff')
    bad = api.report(tmp_path, ['references/a.md'])
    assert not bad['complete'] and bad['issues'][0]['status'] == 'invalid_utf8'


@pytest.mark.parametrize('change', ['version', 'negative', 'duplicate', 'path', 'incomplete', 'empty'])
def test_untrusted_baselines_cannot_make_a_comparison(api, tmp_path, change):
    (tmp_path / 'a.md').write_text('data')
    baseline = api.report(tmp_path, ['a.md'])
    if change == 'version': baseline['schema_version'] = True
    if change == 'negative': baseline['files'][0]['characters'] = -1
    if change == 'duplicate': baseline['files'] *= 2
    if change == 'path': baseline['files'][0]['path'] = '../a.md'
    if change == 'incomplete': baseline['complete'] = False
    if change == 'empty': baseline['files'] = []
    value = api.report(tmp_path, ['a.md'], baseline)
    assert not value['comparison']['comparable']
    assert value['comparison']['reduction_percent'] is None


def test_cli_rejects_null_or_duplicate_baseline(tmp_path):
    script = str(Path(__file__).with_name('context-footprint.py'))
    (tmp_path / 'a.md').write_text('abcd')
    base = tmp_path / 'before.json'
    def run(*args):
        return subprocess.run([sys.executable, script, '--project', str(tmp_path),
            '--file', 'a.md', *args], capture_output=True, encoding='utf-8')
    before = run()
    assert before.returncode == 0
    base.write_text(before.stdout, encoding='utf-8')
    assert run('--baseline', base.name).returncode == 0
    for invalid in ['null', '{"x":1,"x":2}', '[' * 5000 + '0' + ']' * 5000,
                    'x' * (512 * 1024 + 1)]:
        base.write_text(invalid, encoding='utf-8')
        value = run('--baseline', base.name)
        assert value.returncode != 0
        assert not json.loads(value.stdout)['complete']


def test_unavailable_sources_or_helper_are_not_success(api, tmp_path, monkeypatch):
    assert not api.report(tmp_path, ['missing'])['complete']
    monkeypatch.setattr(api, 'HERE', tmp_path / 'absent')
    assert not api.report(tmp_path, ['a.md'])['complete']
