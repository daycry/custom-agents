"""Publication CLI contracts exercised in process, with isolated project fixtures."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

import pytest

SOURCE = Path(os.environ.get('MEMORY_COVERAGE_SOURCE', Path(__file__).resolve().parents[1]))


@pytest.fixture
def scope():
    path = SOURCE / 'skills/confluence-publish/scripts/confluence-scope.py'
    spec = importlib.util.spec_from_file_location('scope_cli_additional', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tree(root):
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in root.rglob('*') if p.is_file()}


@pytest.fixture
def project(tmp_path):
    root = tmp_path / 'project'
    for relative, content in {
        'docs/README.md': b'# Public\r\nPreserve exact bytes.\r\n',
        'docs/knowledge/approved/gotchas/entry.md': '# Aprobado\nReferencia verificada.\n'.encode(),
        'docs/knowledge/candidates/pending/entry.md': b'PRIVATE-PENDING',
        'docs/knowledge/candidates/needs_changes/entry.md': b'PRIVATE-CHANGES',
        'docs/knowledge/candidates/rejected/entry.md': b'PRIVATE-REJECTED',
        'docs/knowledge/JoUrNaL/session.md': b'PRIVATE-JOURNAL',
        'docs/security-scan/finding.md': b'PRIVATE-SECURITY',
    }.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    config = root / 'publish.json'
    config.write_text(json.dumps({'publish': {
        'include': ['**/*.md'], 'exclude': ['docs/security-scan/**']}}), encoding='utf-8')
    return root, config


def cli(scope, monkeypatch, capsys, *arguments):
    monkeypatch.setattr(sys, 'argv', ['confluence-scope', *map(str, arguments)])
    with pytest.raises(SystemExit) as terminal:
        scope.main()
    output = capsys.readouterr()
    assert 'Traceback' not in output.out + output.err
    return terminal.value.code, output.out, output.err


def test_cli_stage_idempotent_byte_exact_and_private_memory_never_published(scope, project, monkeypatch, capsys):
    root, config = project
    originals = tree(root)
    args = ('--stage', '--root', root, '--config', config, '--out', 'docs/publish-view')
    code, output, _ = cli(scope, monkeypatch, capsys, *args)
    assert code == 0 and '2 fichero(s)' in output
    out = root / 'docs/publish-view'
    expected = {'README.md', 'knowledge/approved/gotchas/entry.md', scope.STAGE_MARKER_NAME}
    first = tree(out)
    assert set(first) == expected
    assert first['README.md'] == originals['docs/README.md']
    assert first['knowledge/approved/gotchas/entry.md'] == originals['docs/knowledge/approved/gotchas/entry.md']
    assert not any(b'PRIVATE-' in value for value in first.values())
    assert cli(scope, monkeypatch, capsys, *args)[0] == 0
    assert tree(out) == first
    assert all((root / name).read_bytes() == value for name, value in originals.items())
    assert not (out / 'publish-view').exists()


@pytest.mark.parametrize('kind', ['project_docs', 'occupied_directory', 'regular_file'])
def test_cli_stage_refuses_unowned_output_without_touching_existing_content(scope, project, monkeypatch, capsys, kind):
    root, config = project
    if kind == 'project_docs':
        out = root / 'docs'
    elif kind == 'occupied_directory':
        out = root / 'artifacts'
        out.mkdir()
        (out / 'human-work.md').write_bytes(b'KEEP-HUMAN-WORK')
    else:
        out = root / 'output-file'
        out.write_bytes(b'KEEP-FILE')
    before = tree(root)
    code, output, _ = cli(scope, monkeypatch, capsys, '--stage', '--root', root, '--config', config, '--out', out)
    assert code == 2 and ('no se toca' in output or 'rehúsa borrarlo' in output)
    assert tree(root) == before


@pytest.mark.parametrize('state_kind', ['valid', 'missing', 'corrupt'])
def test_cli_status_reads_sync_manifest_and_preserves_source_bytes(scope, project, monkeypatch, capsys, state_kind):
    root, config = project
    state = root / 'state.json'
    if state_kind == 'valid':
        state.write_text(json.dumps({
            'docs/README.md': {'hash': hashlib.sha256((root / 'docs/README.md').read_bytes()).hexdigest()},
            'docs/knowledge/approved/gotchas/entry.md': {'hash': '0' * 64}}), encoding='utf-8')
    elif state_kind == 'corrupt':
        state.write_bytes(b'{ partial json')
    before = tree(root)
    code, output, _ = cli(scope, monkeypatch, capsys, '--status', '--root', root, '--config', config, '--state', state)
    assert code == 0
    if state_kind == 'valid':
        assert '[sincronizado] docs/README.md' in output
        assert '[desactualizado] docs/knowledge/approved/gotchas/entry.md' in output
    else:
        assert '[pendiente] docs/README.md' in output
        assert '[pendiente] docs/knowledge/approved/gotchas/entry.md' in output
    for private in ('pending', 'needs_changes', 'rejected', 'JoUrNaL'):
        lines = [line for line in output.splitlines() if '/'+private+'/' in line]
        assert lines and all('[excluido:' in line for line in lines)
    assert tree(root) == before


def test_cli_status_missing_docs_reports_empty_without_creating_it(scope, tmp_path, monkeypatch, capsys):
    before = tree(tmp_path)
    code, output, _ = cli(scope, monkeypatch, capsys, '--status', '--root', tmp_path)
    assert code == 0 and 'nada más que analizar' in output
    assert tree(tmp_path) == before and not (tmp_path / 'docs').exists()


@pytest.mark.parametrize('config_kind', ['missing', 'corrupt', 'no_publish', 'unsafe_policy'])
def test_cli_check_explicit_policy_is_not_silently_replaced(scope, project, monkeypatch, capsys, config_kind):
    root, _ = project
    explicit = root / 'requested-policy.json'
    if config_kind == 'corrupt':
        explicit.write_bytes(b'{ broken')
    elif config_kind == 'no_publish':
        explicit.write_text('{}', encoding='utf-8')
    elif config_kind == 'unsafe_policy':
        explicit.write_text(json.dumps({'publish': {'include': ['**/*.md'], 'exclude': []}}), encoding='utf-8')
    before = tree(root)
    code, output, _ = cli(scope, monkeypatch, capsys, '--check', '--root', root, '--config', explicit)
    assert code == (1 if config_kind == 'unsafe_policy' else 2)
    assert 'docs/security-scan' in output if config_kind == 'unsafe_policy' else 'config inválida' in output
    assert tree(root) == before


def test_cli_check_default_project_policy_and_embedded_fallback_are_observable(scope, tmp_path, monkeypatch, capsys):
    config = tmp_path / '.claude/confluence.json'
    config.parent.mkdir()
    config.write_text(json.dumps({'publish': {'exclude': ['docs/security-scan/**']}}), encoding='utf-8')
    code, output, _ = cli(scope, monkeypatch, capsys, '--check', '--root', tmp_path)
    assert code == 0 and 'config de proyecto' in output
    config.write_bytes(b'{ broken')
    monkeypatch.setattr(scope, 'DEFAULT_ASSET', tmp_path / 'unavailable-default.json')
    before = tree(tmp_path)
    code, output, _ = cli(scope, monkeypatch, capsys, '--check', '--root', tmp_path)
    assert code == 1 and 'defaults embebidos' in output and 'docs/security-scan' in output
    assert tree(tmp_path) == before


@pytest.mark.parametrize('mapping_request,expected', [
    ('README.md', 0), ('docs/publish-view/README.md', 0), ('absolute', 0),
    ('_STAGING-LEEME.md', 1), ('unmapped.md', 1), ('', 2), ('outside', 1),
])
def test_cli_inverse_mapping_requires_existing_canonical_file(scope, project, monkeypatch, capsys, mapping_request, expected):
    root, _ = project
    out = root / 'docs/publish-view'
    if mapping_request == 'absolute':
        mapping_request = out / 'README.md'
    elif mapping_request == 'outside':
        mapping_request = root.parent / 'unrelated.md'
    before = tree(root)
    code, output, _ = cli(scope, monkeypatch, capsys, '--map', mapping_request, '--root', root, '--out', out)
    assert code == expected
    if expected == 0:
        assert output.strip() == 'docs/README.md'
    else:
        assert output.strip() and 'docs/README.md' != output.strip()
    assert tree(root) == before and not out.exists()


def test_cli_status_unreadable_manifest_and_document_do_not_claim_synchronized(scope, project, monkeypatch, capsys):
    root, config = project
    state = root / 'state.json'
    state.write_text(json.dumps({'docs/README.md': {'hash': '0' * 64}}), encoding='utf-8')
    read_text = Path.read_text

    def denied(path, *args, **kwargs):
        if path == state:
            raise PermissionError('fixture denies manifest')
        return read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'read_text', denied)
    code, output, _ = cli(scope, monkeypatch, capsys, '--status', '--root', root, '--config', config, '--state', state)
    assert code == 0 and '[pendiente] docs/README.md' in output
    monkeypatch.setattr(Path, 'read_text', read_text)
    original_hash = scope.sha256_of

    def unavailable(path):
        if path == root / 'docs/README.md':
            raise PermissionError('fixture denies content')
        return original_hash(path)

    monkeypatch.setattr(scope, 'sha256_of', unavailable)
    code, output, _ = cli(scope, monkeypatch, capsys, '--status', '--root', root, '--config', config, '--state', state)
    assert code == 0 and '[pendiente] docs/README.md' in output
