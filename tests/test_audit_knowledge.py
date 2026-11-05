"""Publication authorization is checked at the send boundary, with no real services."""
import hashlib
import inspect
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(relative):
    spec = importlib.util.spec_from_file_location('audit_' + Path(relative).stem.replace('-', '_'), ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_r9_replay_revalidates_before_sending(monkeypatch):
    sync = load('skills/knowledge-services/scripts/knowledge-sync.py')
    item = {'payload': {'backend': 'graph', 'type': 'graphiti', 'ops': [{'tipo': 'upsert', 'id': 'withdrawn', 'cuerpo': 'Withdrawn private body'}]}}
    pending = [item, None]
    sent = []
    box = SimpleNamespace(reclamar=lambda _: pending.pop(0), completar=lambda *a, **k: None,
                          ceder_paso=lambda *a, **k: None, reencolar_o_dead_letter=lambda *a, **k: pytest.fail('unexpected retry'))
    adapter = SimpleNamespace(plan=lambda entries, cfg: [], apply=lambda ops, cfg: sent.extend(ops) or {})
    # The public invocation supplies a current authorization snapshot to replay.
    parameters = inspect.signature(sync._drenar_outbox_propia).parameters
    authorization = {'current_entries': [], 'backend_type': 'graphiti'} if 'current_entries' in parameters else {}
    sync._drenar_outbox_propia(box, adapter, {}, 'unused', 'graph', **authorization)
    assert sent == [], 'A withdrawn queued body crossed the adapter send boundary.'


def graph():
    return load('skills/knowledge-services/backends/graphiti.py')


def entry(**values):
    return dict(id='ks.gotcha.one', version=1, cuerpo='Public introduction.\n\nPRIVATE SECOND PARAGRAPH.', category='GOTCHA', **values)


def test_r10_summary_without_explicit_summary_never_falls_back_to_full_body(tmp_path):
    mod = graph()
    cfg = {'group_id': 'audit', '_root': str(tmp_path), 'mode': 'shadow', 'endpoint': 'http://127.0.0.1:8001/mcp'}
    op = mod.plan([entry(modo='resumen')], cfg)[0]
    episode, _ = mod._episodio_upsert('audit', op, cfg)
    assert 'Public introduction.' in episode['episode_body']
    assert 'PRIVATE SECOND PARAGRAPH' not in episode['episode_body']


def test_r10_changed_projection_same_identity_requires_explicit_version(tmp_path, monkeypatch):
    mod = graph()
    cfg = {'group_id': 'audit', '_root': str(tmp_path), 'mode': 'shadow', 'endpoint': 'http://127.0.0.1:8001/mcp'}
    full = entry()
    op = mod.plan([full], cfg)[0]
    episode, _ = mod._episodio_upsert('audit', op, cfg)
    prior = {'version': 1, 'hash': op['hash'], 'hash_enviado': episode['hash_enviado']}
    monkeypatch.setattr(mod, '_leer_manifest', lambda _: ({'group_id': 'audit', 'entradas': {full['id']: prior}}, False))
    with pytest.raises(mod.ErrorMCP, match='version'):
        mod.plan([entry(modo='resumen', resumen='Authorized short summary.')], cfg)


def test_legacy_graphiti_summary_with_matching_published_body_is_a_noop(tmp_path, monkeypatch):
    mod = graph()
    cfg = {'group_id': 'audit', '_root': str(tmp_path), 'mode': 'shadow', 'endpoint': 'http://127.0.0.1:8001/mcp'}
    approved = entry(modo='resumen', resumen='Unchanged approved summary.')
    op = mod.plan([approved], cfg)[0]
    episode, _ = mod._episodio_upsert('audit', op, cfg)
    prior = {'version': 1, 'hash': op['hash'], 'episode_body_sha256': hashlib.sha256(episode['episode_body'].encode()).hexdigest()}
    monkeypatch.setattr(mod, '_leer_manifest', lambda _: ({'group_id': 'audit', 'entradas': {approved['id']: prior}}, False))
    assert mod.plan([approved], cfg) == []


def test_r11_staging_excludes_security_reports_without_user_excludes(tmp_path):
    mod = load('skills/confluence-publish/scripts/confluence-scope.py')
    report = tmp_path / 'docs/security-scan/private.md'
    report.parent.mkdir(parents=True)
    report.write_text('Sensitive security report.', encoding='utf8')
    policy = tmp_path / 'policy.json'
    policy.write_text(json.dumps({'publish': {'include': ['**/*.md'], 'exclude': []}}), encoding='utf8')
    assert mod.cmd_stage(SimpleNamespace(root=str(tmp_path), config=str(policy), docs='docs', out=None)) == 0
    assert not (tmp_path / 'docs/confluence/security-scan/private.md').exists()
    assert report.read_text(encoding='utf8') == 'Sensitive security report.'


def test_r12_categoryless_agent_proposal_has_immutable_origin(tmp_path):
    mod = load('agent-kits/shared/knowledge-curation.py')
    root = tmp_path / 'project'
    (root / 'docs/roadmap').mkdir(parents=True)
    result, code = mod.propose(str(root), 'entry.md', '---\ntitle: Audit entry\n---\n\nSupported body.', producer='documenter')
    assert code == 0, result
    assert b'content_origin: agent' in (root / result['ruta']).read_bytes()
    final, code = mod.apply_decision(str(root), result['ruta'], 'approve', expected_sha256=result['sha256'],
        reason='Reviewed evidence.', decider='knowledge-curator', metadata={'id': 'ks.gotcha.one', 'content_origin': 'human'})
    assert code != 0 and final['status'] == 'changed_content_origin', final


def test_r21_rebuilt_group_is_recognized_as_owned(tmp_path):
    mod = graph()
    physical = mod._gscope.generation_group('audit', 'a' * 32)
    folder = tmp_path / '.claude/knowledge-services'
    folder.mkdir(parents=True)
    descriptor = {'group_id': physical, 'logical_group_id': 'audit', 'transitions': {},
                  'entradas': {'ks.gotcha.one': {'version': 1, 'hash': hashlib.sha256(b'body').hexdigest(), 'group_id': physical}}}
    (folder / 'graphiti-manifest.json').write_text(json.dumps(descriptor), encoding='utf8')
    assert mod.estado_grupo({'group_id': 'audit', '_root': str(tmp_path), 'mode': 'shadow', 'endpoint': 'http://127.0.0.1:8001/mcp'})['estado'] == 'propio'
