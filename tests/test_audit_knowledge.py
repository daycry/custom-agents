"""Publication authorization is checked at the send boundary, with no real services."""
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
    item = {'payload': {'backend': 'graph', 'type': 'externo', 'ops': [{'tipo': 'upsert', 'id': 'withdrawn', 'cuerpo': 'Withdrawn private body'}]}}
    pending = [item, None]
    sent = []
    box = SimpleNamespace(reclamar=lambda _: pending.pop(0), completar=lambda *a, **k: None,
                          ceder_paso=lambda *a, **k: None, reencolar_o_dead_letter=lambda *a, **k: pytest.fail('unexpected retry'))
    adapter = SimpleNamespace(plan=lambda entries, cfg: [], apply=lambda ops, cfg: sent.extend(ops) or {})
    # The public invocation supplies a current authorization snapshot to replay.
    parameters = inspect.signature(sync._drenar_outbox_propia).parameters
    authorization = {'current_entries': [], 'backend_type': 'externo'} if 'current_entries' in parameters else {}
    sync._drenar_outbox_propia(box, adapter, {}, 'unused', 'graph', **authorization)
    assert sent == [], 'A withdrawn queued body crossed the adapter send boundary.'


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
