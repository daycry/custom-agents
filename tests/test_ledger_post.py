"""A single business process shares the ledger parse and serializes progress debounce."""
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / 'agent-kits/shared'
HOOK = ROOT / 'hooks/ledger-post.py'
TEXT = '''---
estado: en-progreso
verificacion: obligatoria
---
# Demo

> Ledger canónico de progreso.

| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase 1 — Fixture | 1 | 2 | 50% |

## Fase 1 — Fixture

### T-01 — First
- **Estado**: completado
- **Verificación**: lectura: fixture
- **Changelog**: First fixture.
**Criterios de aceptación**
- [x] First done.

### T-02 — Second
- **Estado**: en-progreso
- **Verificación**: lectura: fixture
- **Changelog**: Second fixture.
**Criterios de aceptación**
- [ ] Second pending.
'''


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def service():
    assert HOOK.is_file(), 'combined ledger hook is not implemented'
    return load('combined_ledger_post_test', HOOK)


def project(tmp_path):
    root = tmp_path / 'project'
    ledger = root / 'docs/roadmap/demo/tasks.md'
    ledger.parent.mkdir(parents=True)
    ledger.write_text(TEXT, encoding='utf-8')
    return root, ledger


def payload(path):
    return {'tool_name': 'Edit', 'tool_input': {'file_path': str(path)}}


def test_lint_accepts_a_shared_parse_without_reopening_or_reparsing(tmp_path):
    _, ledger = project(tmp_path)
    lint = load('post_lint_api_test', SHARED / 'ledger-lint.py')
    parsed = lint.parse_ledger(TEXT)
    expected = lint.lint(str(ledger))
    with patch.object(lint, 'parse_ledger', side_effect=AssertionError('duplicate parse')):
        with patch('builtins.open', side_effect=AssertionError('duplicate read')):
            assert lint.lint(str(ledger), text=TEXT, parsed=parsed) == expected


def test_progress_accepts_a_shared_parse_without_reopening_or_reparsing(tmp_path):
    _, ledger = project(tmp_path)
    report = load('post_report_api_test', SHARED / 'progress-report.py')
    parsed = report.parse_ledger(TEXT)
    expected = report.resumir(str(ledger), text=TEXT)
    with patch.object(report, 'parse_ledger', side_effect=AssertionError('duplicate parse')):
        with patch('builtins.open', side_effect=AssertionError('duplicate read')):
            assert report.resumir(str(ledger), text=TEXT, parsed=parsed) == expected


def test_combined_hook_shares_one_parse_and_preserves_both_cli_messages(tmp_path):
    root, ledger = project(tmp_path)
    hook = service()
    cli = lambda script, args: subprocess.run(
        [sys.executable, str(SHARED / script), *args], cwd=root,
        capture_output=True, text=True, encoding='utf-8', check=True).stdout.strip()
    lint_text = cli('ledger-lint.py', [str(ledger), '--warn-only'])
    progress_text = cli('progress-report.py', ['line', str(ledger)])
    calls = []
    lint_parse, report_parse = hook.lint_module.parse_ledger, hook.progress_module.parse_ledger
    with patch.object(hook.lint_module, 'parse_ledger', side_effect=lambda text: (calls.append('lint'), lint_parse(text))[1]):
        with patch.object(hook.progress_module, 'parse_ledger', side_effect=lambda text: (calls.append('progress'), report_parse(text))[1]):
            actual = hook.process_payload(payload(ledger), root)
    assert actual == lint_text + '\n' + progress_text
    assert len(calls) == 1, calls
    assert (root / '.claude/.progress-last').read_text(encoding='utf-8') == progress_text
    assert hook.process_payload(payload(ledger), root) == lint_text


def test_combined_cli_concurrent_progress_is_emitted_exactly_once(tmp_path):
    root, ledger = project(tmp_path)
    service()  # Explicit missing-feature error before launching subprocesses.
    def invoke(_):
        return subprocess.run([sys.executable, str(HOOK), '--root', str(root)],
            input=json.dumps(payload(ledger)), capture_output=True, text=True,
            encoding='utf-8', timeout=20)
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(invoke, range(6)))
    assert all(r.returncode == 0 and not r.stderr for r in results), [(r.returncode, r.stderr) for r in results]
    messages = [json.loads(r.stdout)['systemMessage'] for r in results]
    assert all('ledger-lint:' in message for message in messages)
    assert sum('📋' in message for message in messages) == 1
    assert (root / '.claude/.progress-last').read_text(encoding='utf-8').startswith('📋 demo')
    assert not list((root / '.claude').glob('.tmp-*'))


def test_edit_list_deduplicates_paths_but_checks_each_ledger_once(tmp_path):
    root, first = project(tmp_path)
    second = root / 'docs/roadmap/other/tasks.md'
    second.parent.mkdir(parents=True)
    second.write_text(TEXT, encoding='utf-8')
    hook = service()
    value = {'tool_input': {'file_path': str(first), 'edits': [
        {'file_path': str(first)}, {'file_path': str(second)}, {'file_path': 'src/app.py'}]}}
    with patch.object(hook.lint_module, 'parse_ledger', wraps=hook.lint_module.parse_ledger) as parse:
        message = hook.process_payload(value, root)
    assert parse.call_count == 2
    assert message.count('ledger-lint:') == 2
    assert message.count('📋') == 1


@pytest.mark.parametrize('value', [None, [], {}, {'tool_input': {'file_path': None}}, {'tool_input': {'edits': [{}]}}])
def test_unrecognized_payload_is_informative_and_never_creates_state(tmp_path, value):
    root, _ = project(tmp_path)
    assert service().process_payload(value, root) == ''
    assert not (root / '.claude').exists()


def test_outside_ledger_is_not_read(tmp_path):
    root, _ = project(tmp_path)
    outside = tmp_path / 'docs/roadmap/foreign/tasks.md'
    outside.parent.mkdir(parents=True)
    outside.write_text(TEXT, encoding='utf-8')
    hook = service()
    with patch.object(hook.lint_module, 'parse_ledger', side_effect=AssertionError('foreign read')):
        assert hook.process_payload(payload(outside), root) == ''
    assert not (root / '.claude').exists()


def test_progress_state_failure_does_not_lose_the_informative_message(tmp_path):
    root, ledger = project(tmp_path)
    (root / '.claude').write_text('unowned', encoding='utf-8')
    message = service().process_payload(payload(ledger), root)
    assert 'ledger-lint:' in message and '📋 demo' in message
    assert (root / '.claude').read_text(encoding='utf-8') == 'unowned'


def test_messages_and_persisted_progress_use_the_canonical_redactor(tmp_path):
    root, ledger = project(tmp_path)
    secret = 'Password123456'  # Synthetic credential fixture.
    ledger.write_text(TEXT.replace('### T-02 — Second', '### T-02 — Second token=' + secret), encoding='utf-8')
    message = service().process_payload(payload(ledger), root)
    assert secret not in message
    assert secret not in (root / '.claude/.progress-last').read_text(encoding='utf-8')
    assert '📋 demo' in message and 'ledger-lint:' in message


def test_symlink_ledger_is_not_followed(tmp_path):
    root, ledger = project(tmp_path)
    original = ledger.with_name('unowned.md')
    ledger.rename(original)
    try:
        ledger.symlink_to(original)
    except OSError as error:
        if os.name == 'nt' and error.winerror == 1314:
            pytest.skip('file symlink privilege unavailable')
        raise
    hook = service()
    with patch.object(hook.lint_module, 'parse_ledger', side_effect=AssertionError('followed symlink')):
        assert hook.process_payload(payload(ledger), root) == ''


def test_native_registration_uses_one_combined_ledger_handler():
    config = json.loads((ROOT / 'hooks/hooks.json').read_text(encoding='utf-8'))
    commands = [h['command'] for group in config['hooks']['PostToolUse'] for h in group['hooks']]
    assert sum('ledger-post.py' in command for command in commands) == 1
    assert not any('ledger-lint-warn.sh' in command or 'progress-line.sh' in command for command in commands)
