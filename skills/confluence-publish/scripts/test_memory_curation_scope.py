"""Uncurated knowledge must never enter the documentation publication view."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


def load_scope():
    spec = importlib.util.spec_from_file_location(
        'memory_curation_scope', Path(__file__).with_name('confluence-scope.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('private', [
    'candidates/pending', 'candidates/needs_changes', 'candidates/rejected',
    'journal', 'CaNdIdAtEs/PENDING', 'JoUrNaL',
])
def test_uncurated_memory_excluded_even_with_explicit_include(tmp_path, private):
    scope = load_scope()
    private_path = tmp_path / 'docs/knowledge' / private / 'entry.md'
    private_path.parent.mkdir(parents=True)
    private_path.write_text('unapproved fixture', encoding='utf-8')
    approved = tmp_path / 'docs/knowledge/approved/gotchas/entry.md'
    approved.parent.mkdir(parents=True)
    approved.write_text('approved fixture', encoding='utf-8')
    before = private_path.read_bytes()
    policy = {'include': ['**/*.md'], 'exclude': ['docs/security-scan/**']}
    included, excluded = scope.resolve_scope(tmp_path, policy)
    relative = private_path.relative_to(tmp_path).as_posix()
    assert relative not in included
    assert relative in {path for path, _ in excluded}
    assert approved.relative_to(tmp_path).as_posix() in included
    assert private_path.read_bytes() == before


def test_staging_preserves_approved_and_omits_candidates_journal(tmp_path):
    scope = load_scope()
    originals = {}
    for name in ('candidates/pending', 'candidates/rejected', 'journal', 'approved/gotchas'):
        path = tmp_path / 'docs/knowledge' / name / 'entry.md'
        path.parent.mkdir(parents=True)
        path.write_text(name, encoding='utf-8')
        originals[path] = path.read_bytes()
    config = tmp_path / 'policy.json'
    config.write_text(json.dumps({'publish': {
        'include': ['**/*.md'], 'exclude': ['docs/security-scan/**'],
    }}), encoding='utf-8')
    args = SimpleNamespace(root=str(tmp_path), config=str(config), docs='docs', out=None)
    assert scope.cmd_stage(args) == 0
    staged = tmp_path / 'docs/confluence/knowledge'
    assert (staged / 'approved/gotchas/entry.md').read_bytes() == b'approved/gotchas'
    assert not (staged / 'candidates').exists()
    assert not (staged / 'journal').exists()
    assert all(path.read_bytes() == raw for path, raw in originals.items())
