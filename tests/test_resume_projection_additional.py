import json

import pytest

from test_resume_curation import TEXT, load, snapshot


def block(refs):
    return '```curation-refs-v1\n' + json.dumps(refs) + '\n```\n'


@pytest.fixture
def long_handoff(tmp_path):
    service = load('projection_real_service', 'knowledge-curation.py')
    progress = load('projection_real_progress', 'progress-report.py')
    root = tmp_path / 'project'
    policy = root / '.claude/knowledge-services/taxonomy.json'
    policy.parent.mkdir(parents=True)
    policy.write_text(json.dumps({'version': 1, 'id_prefix': 'ca', 'categories': [
        {'key': 'GOTCHA', 'folder': 'g' * 100, 'min_evidence': 'validated_case'}]}), encoding='utf-8')
    refs = []
    for n in range(8):
        filename = 'n' + str(n) + 'a' * 123 + '.md'
        assert len(filename) == 128
        proposal, code = service.propose(root, filename, TEXT, producer='documenter')
        assert code == 0, proposal
        original = (root / proposal['ruta']).read_bytes()
        applied, code = service.apply_decision(root, proposal['ruta'], 'approve',
            expected_sha256=proposal['sha256'], reason='Reviewed fixture', metadata={
                'id': 'ca.gotcha.test' + str(n), 'category': 'GOTCHA', 'version': 1, 'estado': 'aprobado'})
        assert code == 0, applied
        (root / proposal['ruta']).write_bytes(original)
        refs.append({'candidate': proposal['ruta'], 'sha256': proposal['sha256'],
                     'operation_id': applied['operation_id']})
    initiative = '2026-10-10-' + 'd' * 149
    ledger = root / ('docs/roadmap/' + initiative + '/tasks.md')
    ledger.parent.mkdir(parents=True)
    header = '---\nestado: en-progreso\n---\n## Fase 1 — ' + 'F' * 160 + '\n'
    header += ''.join('### T-0' + str(n) + ' — ' + 'T' * 160 + '\n- **Estado**: en-progreso\n'
                      for n in range(1, 5))
    ledger.write_text(header + block(refs), encoding='utf-8')
    before = snapshot(root)
    view = progress.resume(root, initiative=initiative)
    assert snapshot(root) == before
    return progress, view, refs, root, initiative


@pytest.mark.parametrize('close', ['```suffix', '``` trailing', '    ```', '> ```', '``'])
def test_generic_example_false_close_never_adopts_handoff(tmp_path, close):
    progress = load('false_close_progress', 'progress-report.py')
    ref = {'candidate': 'docs/knowledge/candidates/pending/example.md', 'sha256': 'a' * 64}
    view = progress._resume_curation(tmp_path, '```text\n' + close + '\n' + block([ref]))
    assert view == {'status': 'not_registered', 'references': []}


@pytest.mark.parametrize('opening,closing', [
    ('```text', '```'), ('````text', '`````  '), ('~~~text', '~~~\t'), ('   ```text', '  ```')])
def test_complete_generic_closing_allows_following_top_level_handoff(tmp_path, opening, closing):
    progress = load('correct_close_progress', 'progress-report.py')
    view = progress._resume_curation(tmp_path, opening + '\nexample\n' + closing + '\n' + block([]))
    assert view == {'status': 'ok', 'references': []}


@pytest.mark.parametrize('prefix', ['    ', '> ', '   '])
def test_non_top_level_handoff_does_not_register(tmp_path, prefix):
    progress = load('non_top_level_progress', 'progress-report.py')
    text = '\n'.join(prefix + line for line in block([]).splitlines()) + '\n'
    assert progress._resume_curation(tmp_path, text) == {'status': 'not_registered', 'references': []}


def test_json_budget_counts_whole_prefix_of_real_completed_references(long_handoff, capsys):
    progress, view, refs, root, initiative = long_handoff
    assert len(json.dumps(view, ensure_ascii=False).encode('utf-8')) <= 12000
    visible = view['curation']['references']
    assert 0 < len(visible) < 8
    assert view['curation']['references_omitted'] == 8 - len(visible)
    assert view['output_truncated'] is True
    for actual, original in zip(visible, refs):
        assert actual['candidate'] == original['candidate']
        assert actual['expected_sha256'] == original['sha256']
        assert actual['operation_id'] == original['operation_id']
        assert actual['identity_resolvable'] is True and actual['status'] == 'completed'
        assert actual['receipt_sha256'] == __import__('hashlib').sha256(
            (root / actual['receipt_path']).read_bytes()).hexdigest()
    assert progress.main(['resume', '--root', str(root), '--initiative', initiative, '--json']) == 0
    output = capsys.readouterr().out
    assert len(output.rstrip('\n').encode('utf-8')) <= 12000
    assert json.loads(output) == view


def test_text_budget_counts_every_omitted_reference_without_cutting_identity(long_handoff):
    progress, view, refs, _, _ = long_handoff
    rendered = progress.resume_text(view)
    shown = [ref for ref in refs if ref['operation_id'] in rendered]
    assert 0 < len(shown) < 8
    assert shown == refs[:len(shown)]
    assert f'Curación: {8 - len(shown)} referencias omitidas' in rendered
    assert view['output_truncated'] is True
    assert len(rendered.splitlines()) <= 32 and len(rendered) <= 6000
    for ref in shown:
        assert ref['candidate'] in rendered and ref['sha256'] in rendered
        visible = next(item for item in view['curation']['references'] if item['operation_id'] == ref['operation_id'])
        assert visible['receipt_sha256'] in rendered
    for ref in refs[len(shown):]:
        assert ref['candidate'] not in rendered and ref['operation_id'] not in rendered


def test_text_history_pressure_keeps_entire_reference_groups(long_handoff):
    progress, view, refs, _, _ = long_handoff
    view['history'] = [{'entry': 'history.md', 'fecha': '2026-10-10', 'session_id': 's',
                        'resumen': 'a' * 120, 'decisiones': ['b' * 120] * 4,
                        'pendientes': ['c' * 120] * 4}] * 2
    rendered = progress.resume_text(view)
    assert len(rendered.splitlines()) <= 32 and len(rendered) <= 6000
    shown = [ref for ref in refs if ref['operation_id'] in rendered]
    assert shown == refs[:len(shown)]
    assert f'Curación: {8 - len(shown)} referencias omitidas' in rendered
    for original in shown:
        actual = next(item for item in view['curation']['references'] if item['operation_id'] == original['operation_id'])
        assert original['candidate'] in rendered and original['sha256'] in rendered
        assert actual['receipt_sha256'] in rendered


def test_text_omission_is_reported_even_when_json_fits(long_handoff):
    progress, _, refs, root, initiative = long_handoff
    initiative = '2026-10-10-small'
    ledger = root / ('docs/roadmap/' + initiative + '/tasks.md')
    ledger.parent.mkdir(parents=True)
    ledger.write_text('---\nestado: en-progreso\n---\n## Fase 1 — Work\n### T-01 — Continue\n'
                      '- **Estado**: en-progreso\n' + block(refs), encoding='utf-8')
    before = snapshot(root)
    view = progress.resume(root, initiative=initiative)
    assert len(json.dumps(view, ensure_ascii=False).encode('utf-8')) <= 12000
    assert len(view['curation']['references']) == 8
    rendered = progress.resume_text(view)
    shown = [ref for ref in refs if ref['operation_id'] in rendered]
    assert 0 < len(shown) < 8
    assert view['output_truncated'] is True
    assert f'Curación: {8 - len(shown)} referencias omitidas' in rendered
    assert snapshot(root) == before
