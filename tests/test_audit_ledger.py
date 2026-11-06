"""R7/R8/R16/R17 regressions against real Git and canonical ledger operations."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(relative, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_R7_git_quoted_unicode_and_literal_arrow_are_real_paths(tmp_path):
    def git(*args):
        result = subprocess.run(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                                 '-c', 'core.quotePath=true', *args], cwd=tmp_path, capture_output=True,
                                text=True, encoding='utf-8', check=True,
                                env=dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1'))
        return result.stdout.strip()
    git('init', '-q')
    (tmp_path / 'base.txt').write_text('base', encoding='utf-8')
    git('add', '.'); git('commit', '-qm', 'base')
    base = git('rev-parse', 'HEAD')
    (tmp_path / 'guía.md').write_text('committed', encoding='utf-8')
    git('add', '.'); git('commit', '-qm', 'accent')
    untracked = 'other -> gu\u00eda.txt' if os.name != 'nt' else 'other gu\u00eda.txt'
    (tmp_path / untracked).write_text('untracked', encoding='utf-8')
    sc = load('agent-kits/shared/scope-check.py', 'audit_scope_paths')
    assert sc.ficheros_cambiados(str(tmp_path), base) == ['gu\u00eda.md', untracked]


def test_R8_old_calibration_cannot_close_a_new_initiative_with_same_slug(tmp_path):
    old = tmp_path / 'docs/roadmap/2026-01-10-auth'; old.mkdir(parents=True)
    new = tmp_path / 'docs/roadmap/2026-06-01-auth'; new.mkdir()
    (new / 'retro.md').write_text('# Retro\n\nCurrent retrospective.\n', encoding='utf-8')
    (new.parent / 'CALIBRATION.md').write_text('| 2026-02-01 | auth | previous work |\n', encoding='utf-8')
    rg = load('agent-kits/shared/retro-gate.py', 'audit_retro_identity')
    assert rg.veredicto(str(tmp_path), str(new))['abierta'] is False


def test_R16_unicode_inside_fence_cannot_shift_state_mutation(tmp_path):
    fixture = load('tests/test_ledger_write.py', 'audit_writer_fixture')
    text = fixture.BASE.replace('### T-01', '```text\nfoo\u2028bar\n```\n\n### T-01', 1)
    text = text.replace('### T-02 — Second\n\n- **Estado**',
                        '### T-02 — Second\n\n- **Descripción**: Original description.\n- **Estado**')
    path = tmp_path / 'tasks.md'; path.write_text(text, encoding='utf-8')
    result = fixture.call(path, 'state', '--task', 'T-02', '--state', 'en-progreso')
    assert result.returncode == 0, result.stderr
    after = path.read_text(encoding='utf-8')
    assert 'Original description.' in after
    lint = load('agent-kits/shared/ledger-lint.py', 'audit_writer_lint')
    assert lint.parse_ledger(after)['tareas'][1]['estado'] == 'en-progreso'
    assert 'foo\u2028bar' in after


def archive_fixture(tmp_path):
    module = load('agent-kits/shared/ledger-archive.py', 'audit_archive')
    fixture = load('agent-kits/shared/test_ledger_archive.py', 'audit_archive_fixture')
    path = tmp_path / 'tasks.md'; path.write_text(fixture.ledger(), encoding='utf-8')
    return module, path


def test_archive_large_history_has_an_explicit_bounded_continuation(tmp_path):
    module, path = archive_fixture(tmp_path)
    history = tmp_path / 'execution-history.md'
    original = b'# Execution history\n' + b'x' * (8 * 1024 * 1024) + b'\n'
    history.write_bytes(original)
    plan = module.planificar(str(tmp_path), 600, '2026-11-05')
    before = path.read_bytes()
    with pytest.raises((ValueError, OSError), match='history-max-bytes'):
        module.aplicar(plan, str(tmp_path), '2026-11-05')
    assert path.read_bytes() == before
    assert history.read_bytes() == original
    module.aplicar(plan, str(tmp_path), '2026-11-05', history_max_bytes=16 * 1024 * 1024)
    after = history.read_bytes()
    assert after.startswith(original) and len(after) > len(original)
    plan = module.planificar(str(tmp_path), 600, '2026-11-05')
    module.aplicar(plan, str(tmp_path), '2026-11-05', history_max_bytes=16 * 1024 * 1024)
    assert history.read_bytes() == after


def test_R17_archive_rejects_a_successful_interleaved_ledger_update(tmp_path):
    module, path = archive_fixture(tmp_path)
    plan = module.planificar(str(tmp_path), 600, '2026-11-05')
    result = subprocess.run([sys.executable, str(ROOT / 'agent-kits/shared/ledger-write.py'),
                             'state', str(path), '--task', 'T-01', '--state', 'en-revision'],
                            capture_output=True, text=True, encoding='utf-8')
    assert result.returncode == 0, result.stderr
    updated = path.read_bytes()
    with pytest.raises((ValueError, OSError)):
        module.aplicar(plan, str(tmp_path), '2026-11-05')
    assert path.read_bytes() == updated
    assert not (tmp_path / 'execution-history.md').exists()


@pytest.mark.skipif(os.name == 'nt', reason='POSIX permissions')
def test_R17_archive_preserves_ledger_mode(tmp_path):
    module, path = archive_fixture(tmp_path)
    path.chmod(0o640)
    plan = module.planificar(str(tmp_path), 600, '2026-11-05')
    module.aplicar(plan, str(tmp_path), '2026-11-05')
    assert path.stat().st_mode & 0o777 == 0o640


def test_R17_archive_rejects_a_redirected_parent(tmp_path):
    source = tmp_path / 'source'; source.mkdir()
    module, path = archive_fixture(source)
    redirected = tmp_path / 'redirected'
    if os.name == 'nt':
        import _winapi
        _winapi.CreateJunction(str(source), str(redirected))
    else:
        redirected.symlink_to(source, target_is_directory=True)
    before = path.read_bytes()
    with pytest.raises((ValueError, OSError)):
        module.planificar(str(redirected), 600, '2026-11-05')
    assert path.read_bytes() == before
def test_calibration_does_not_rescan_roadmap_for_unrelated_rows(tmp_path, monkeypatch):
    mod = load('agent-kits/shared/retro-gate.py', 'audit_retro_scan')
    roadmap = tmp_path / 'docs/roadmap'; folder = roadmap / '2026-11-05-audit'
    folder.mkdir(parents=True)
    rows = [f'| 2026-11-05 | unrelated-{n} | 0 | 0 |' for n in range(500)]
    rows.append('| 2026-11-05 | 2026-11-05-audit | 0 | 0 |')
    (roadmap / 'CALIBRATION.md').write_text('\n'.join(rows), encoding='utf8')
    real = mod.os.listdir; calls = []
    def listing(path):
        calls.append(str(path)); return real(path)
    monkeypatch.setattr(mod.os, 'listdir', listing)
    assert mod.fila_calibracion(str(tmp_path), str(folder))[0]
    assert len(calls) <= 1, 'Unrelated calibration rows trigger repeated full roadmap listings.'


def test_state_io_normalizes_only_verified_system_aliases():
    mod = load('agent-kits/shared/local-state.py', 'audit_system_alias')
    transform = getattr(mod, 'physical_system_path', lambda path, **kwargs: Path(path))
    assert transform('/var/project/untrusted-link/file', platform='darwin', resolve_link=lambda _: '/private/var').as_posix() == '/private/var/project/untrusted-link/file'
    with pytest.raises(ValueError):
        transform('/tmp/project/file', platform='darwin', resolve_link=lambda _: '/unrelated')
