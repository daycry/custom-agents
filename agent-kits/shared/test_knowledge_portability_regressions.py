"""Concrete implementation self-review regressions; real files and owner."""
import json
from pathlib import Path

import pytest

from test_knowledge_portability import (
    PENDING, canonical, import_, interrupt, note, result, roots, service, transfer, tree,
)


def test_boolean_receipt_schema_is_corruption_not_valid_history(service, roots):
    _, raw = transfer(service, roots)
    _, destination = roots
    imported = result(import_(service, destination, raw))
    path = destination / imported['entries'][0]['import_receipt_path']
    record = json.loads(path.read_bytes())
    record['schema_version'] = True
    path.write_bytes(canonical(record))
    before = tree(destination)
    failed, code = import_(service, destination, raw)
    assert code != 0 and failed['complete'] is False, failed
    assert tree(destination) == before


@pytest.mark.parametrize('state', ['approved', 'rejected'])
def test_owned_intent_does_not_exempt_foreign_reservation_in_other_state(service, roots, monkeypatch, state):
    source, destination = roots
    ids, raw = transfer(service, roots)
    seen, original = interrupt(monkeypatch, service, 'import_intent_published', ids[0])
    failed = result(import_(service, destination, raw), 2)
    assert len(seen) == 1
    name = Path(failed['entries'][0]['candidate_path']).name
    directory = destination / ('docs/knowledge/approved/gotchas' if state == 'approved'
                               else 'docs/knowledge/candidates/rejected')
    directory.mkdir(parents=True)
    foreign = directory / name
    content = (source / 'docs/knowledge/approved/gotchas/a.md').read_bytes()
    foreign.write_bytes(content.replace(b'src.gotcha.a', b'dst.gotcha.foreign'))
    before = tree(destination)
    monkeypatch.setattr(service, '_checkpoint', original)
    rejected, code = import_(service, destination, raw)
    assert code != 0 and rejected['status'] == 'reservation_conflict', rejected
    assert tree(destination) == before
    assert not list((destination / PENDING).glob('*.md'))


def test_export_after_link_failure_reports_actual_published_bytes(service, roots, monkeypatch):
    source, _ = roots
    source_id, _ = note(source)
    actual_link = service.os.link
    observed = []

    def fail_after_link(staged, target, **kwargs):
        actual_link(staged, target, **kwargs)
        if Path(target) == source / 'artifacts/export.json':
            observed.append((Path(staged), Path(target)))
            raise OSError('interruption after export link')

    monkeypatch.setattr(service.os, 'link', fail_after_link)
    failed, code = service.export_package(str(source), source_id='source-project',
        ids=[source_id], out='artifacts/export.json')
    assert code == 2 and len(observed) == 1
    staged, published = observed[0]
    assert published.read_bytes() == staged.read_bytes()
    assert failed['written'] is True, failed
    assert failed['ruta'] == 'artifacts/export.json'


def test_policy_change_cannot_bypass_an_unpublished_intent_reservation(service, roots, monkeypatch):
    ids, raw = transfer(service, roots)
    _, destination = roots
    seen, original = interrupt(monkeypatch, service, 'import_intent_published', ids[0])
    result(import_(service, destination, raw), 2)
    assert len(seen) == 1 and not list((destination / PENDING).glob('*.md'))
    config = destination / '.claude/knowledge-services/taxonomy.json'
    policy = json.loads(config.read_bytes())
    policy['denylist'].append('new-local-rule')
    config.write_bytes(canonical(policy))
    before = tree(destination)
    monkeypatch.setattr(service, '_checkpoint', original)
    failed, code = import_(service, destination, raw)
    assert code != 0 and failed['status'] == 'reservation_conflict', failed
    assert tree(destination) == before
