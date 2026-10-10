"""N01-N09 local recovery acceptance over exclusively synthetic pytest-owned roots.

Only explicit public inputs are copied. No product module enters the pytest process.
Products run through existing public CLIs in registered OWN children.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

import pytest

SUPPORT = Path(__file__).with_name('memory_local_recovery_support')
_spec = importlib.util.spec_from_file_location('memory_local_recovery_protocol', SUPPORT / 'protocol.py')
protocol = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(protocol)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True) + '\n', encoding='utf-8')


def state_bytes(root):
    return {key: value['sha256'] for key, value in protocol.inventory(root).items()}


def final_envelopes(directory):
    # Only publication destinations count as durable final envelopes. Queue
    # producer temporaries and completion/cause sidecars are distinct evidence.
    return [p for p in directory.glob('*.json')
            if not p.name.startswith('.tmp-')
            and not p.name.endswith(('.manifest.json', '.causa.json'))]


def tree_bytes(root):
    # Ignore access time: reading is allowed. Detect content, mode and mtime
    # mutations as well as additions/removals, including locks and caches.
    return {p.relative_to(root).as_posix(): (protocol.digest(p.read_bytes()),
            p.stat().st_size, p.stat().st_mtime_ns, p.stat().st_mode)
            for p in root.rglob('*') if p.is_file()}


@pytest.fixture(scope='session')
def run_budget():
    return {'children': 0, 'maximum': 96,
            'deadline_monotonic': time.monotonic() + 420}


SOURCE_FILES = (
    'agent-kits/shared/journal.py',
    'agent-kits/shared/journal-capture.py',
    'agent-kits/shared/outbox.py',
    'agent-kits/shared/local-read.py',
    'agent-kits/shared/knowledge-find.py',
    'agent-kits/shared/knowledge-view.py',
    'agent-kits/shared/knowledge-local.py',
    'agent-kits/shared/knowledge-taxonomy-local.py',
    'agent-kits/shared/redact.py',
    'agent-kits/shared/progress-report.py',
    'agent-kits/shared/ledger-lint.py',
    'agent-kits/shared/templates/taxonomy.json',
    'package.json',
    '.claude-plugin/plugin.json',
    '.codex-plugin/plugin.json',
)
HARNESS_FILES = (
    'tests/test_memory_local_recovery.py',
    'tests/memory_local_recovery_support/protocol.py',
    'tests/memory_local_recovery_support/child.py',
    'tests/memory_local_recovery_support/fixture-gold.json',
)
EXCLUDED_SOURCE_PREFIXES = (
    '.claude/', '.codex/', '.opencode/', 'docs/knowledge/', 'scratchpad/', '.venv/',
)


def checked_public_inputs(repo, relatives):
    # Validate the entire explicit selection before opening any file. Never scan
    # the checkout or fall back to a consumer memory/configuration directory.
    paths = []
    for relative in relatives:
        parts = relative.split('/')
        if (relative.startswith(EXCLUDED_SOURCE_PREFIXES)
                or relative.startswith('/') or any(part in ('', '.', '..') for part in parts)):
            raise protocol.InfrastructureError('excluded public input: ' + relative)
        path = repo.joinpath(*parts)
        if path.resolve(strict=True) != path:
            raise protocol.InfrastructureError('linked public input: ' + relative)
        protocol.regular(path)
        paths.append((relative, path))
    return paths


def input_bytes(path):
    info = protocol.regular(path)
    if info.st_size > protocol.MAX_FILE_BYTES:
        raise protocol.InfrastructureError('public input exceeds file budget')
    with path.open('rb') as handle:
        raw = handle.read(protocol.MAX_FILE_BYTES + 1)
        after = os.fstat(handle.fileno())
    if (len(raw) > protocol.MAX_FILE_BYTES
            or (info.st_size, info.st_mtime_ns, info.st_ino)
            != (after.st_size, after.st_mtime_ns, after.st_ino)):
        raise protocol.InfrastructureError('public input changed during copy')
    return raw


@pytest.fixture(scope='session')
def recovery_session(tmp_path_factory):
    # mktemp allocates a new child of pytest's own temporary area. This fixture
    # never requests --basetemp or deletes/reuses an existing shared directory.
    own = tmp_path_factory.mktemp('memory-local-recovery').resolve()
    protocol.atomic_record(own / 'ownership.json', {
        'schema': 1, 'synthetic_only': True, 'owner_pid': os.getpid(),
        'own': str(own), 'allocation': 'pytest tmp_path_factory.mktemp; new directory',
    })
    repo = Path(__file__).resolve().parents[1]
    selected = checked_public_inputs(repo, SOURCE_FILES)
    harness = checked_public_inputs(repo, HARNESS_FILES)
    source = own / 'source'; source.mkdir()
    (own / 'cases').mkdir()
    records, seals, byte_count = [], [], 0
    for group, inputs in (('source', selected), ('harness', harness)):
        for relative, original in inputs:
            raw = input_bytes(original)
            byte_count += len(raw)
            if byte_count > protocol.MAX_BYTES:
                raise protocol.InfrastructureError('public input copy exceeds byte budget')
            target_relative = relative if group == 'source' else (
                'test_memory_local_recovery.py' if relative == HARNESS_FILES[0]
                else 'memory_local_recovery_support/' + original.name)
            target = own / group / target_relative
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as handle:
                handle.write(raw)
            record = {'path': relative, 'sha256': protocol.digest(raw), 'bytes': len(raw)}
            if group == 'source':
                records.append(record)
            seals.append((original, target, record))
    selection = {'schema': 1, 'files': records, 'purpose': 'current explicit public source copy'}
    selection_path = own / 'source-selection.json'
    write_json(selection_path, selection)
    selection_sha = protocol.digest(selection_path.read_bytes())

    def check_inputs():
        for original, target, record in seals:
            for path in (original, target):
                raw = input_bytes(path)
                if len(raw) != record['bytes'] or protocol.digest(raw) != record['sha256']:
                    raise protocol.InfrastructureError('public input changed: ' + record['path'])
        if protocol.digest(selection_path.read_bytes()) != selection_sha:
            raise protocol.InfrastructureError('OWN source selection changed')

    check_inputs()
    try:
        yield {'own': own, 'source': source, 'selection': selection, 'check_inputs': check_inputs}
    finally:
        check_inputs()


@pytest.fixture
def lab(recovery_session, run_budget, request):
    own = recovery_session['own']
    label = ''.join(character if character.isalnum() or character in '-_' else '_'
                    for character in request.node.name)
    work = own / 'cases' / (label + '-' + uuid.uuid4().hex[:12])
    work.mkdir()
    protocol.within(work, own)
    recovery_session['check_inputs']()
    result = Lab(work, own, recovery_session['source'], recovery_session['selection'], run_budget)
    try:
        yield result
    finally:
        try:
            result.close()
        finally:
            recovery_session['check_inputs']()

class Lab:
    def __init__(self, work, own, source, selection, run_budget):
        self.work, self.own, self.source = work, own, source
        self.selection, self.run_budget = selection, run_budget
        self.support = own / 'harness/memory_local_recovery_support'
        self.gold = json.loads((self.support / 'fixture-gold.json').read_text(encoding='utf-8'))
        self.calls, self.mutations, self.cleanup_errors = [], [], []
        self.environment = {name: value for name, value in os.environ.items()
                            if name.upper() in ('SYSTEMROOT', 'WINDIR', 'SYSTEMDRIVE', 'COMSPEC',
                                                'PROCESSOR_ARCHITECTURE', 'NUMBER_OF_PROCESSORS')}
        directories = {name: work / name for name in (
            'home', 'appdata', 'localappdata', 'programdata', 'temp', 'empty-bin',
            'xdg-config', 'xdg-data', 'xdg-cache', 'xdg-state', 'xdg-runtime',
        )}
        for path in directories.values():
            path.mkdir()
        home = directories['home']
        self.environment.update(
            HOME=str(home), USERPROFILE=str(home), CODEX_HOME=str(home / 'codex'),
            CLAUDE_CONFIG_DIR=str(home / 'claude'),
            APPDATA=str(directories['appdata']), LOCALAPPDATA=str(directories['localappdata']),
            PROGRAMDATA=str(directories['programdata']), TEMP=str(directories['temp']),
            TMP=str(directories['temp']), PATH=str(directories['empty-bin']),
            XDG_CONFIG_HOME=str(directories['xdg-config']), XDG_DATA_HOME=str(directories['xdg-data']),
            XDG_CACHE_HOME=str(directories['xdg-cache']), XDG_STATE_HOME=str(directories['xdg-state']),
            XDG_RUNTIME_DIR=str(directories['xdg-runtime']),
            XDG_CONFIG_DIRS=str(directories['xdg-config']), XDG_DATA_DIRS=str(directories['xdg-data']),
            PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1', PYTHONIOENCODING='utf-8',
            CUSTOM_AGENTS_JOURNAL_IA='0', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
            GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_SYSTEM=os.devnull, GIT_CONFIG_GLOBAL=os.devnull,
            GIT_CONFIG_COUNT='0', GIT_TERMINAL_PROMPT='0',
        )

    def project(self, name='atlas'):
        root = self.work / name
        root.mkdir()
        meta = self.gold['projects'][name]
        taxonomy = copy.deepcopy(self.gold['taxonomy']); taxonomy['id_prefix'] = meta['prefix']
        write_json(root / '.claude/knowledge-services/taxonomy.json', taxonomy)
        write_json(root / '.claude/dev.json', {'sesion': {'resumen': False, 'journal': True, 'captura': True}})
        def entry(relative, identifier, state, version=1, category=None, links=None, body=''):
            fields = {'id': identifier, 'estado': state, 'version': version,
                      'titulo': meta['word'] if category == 'DECISION' else 'Sintética conservación',
                      'area': 'memoria sintética', 'fuente': 'fixture:synthetic-not-human-approved',
                      'fixture_synthetic': 'true'}
            if category:
                fields.update(category=category, evidencia='synthetic_test_only',
                              fuentes=['fixture:synthetic-source'], tags=['fixture:synthetic'])
            if links: fields['enlaces'] = links
            text = '---\n' + ''.join(k + ': ' + json.dumps(v, ensure_ascii=False) + '\n' for k, v in fields.items())
            text += '---\n\n# Dato sintético; sin aprobación humana real\n' + body + '\n'
            path = root / relative; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'\xef\xbb\xbf' + text.replace('\n', '\r\n').encode('utf-8'))
        entry('docs/knowledge/approved/adr/current.md', meta['current'], 'aprobado', 7, 'DECISION',
              [meta['peer']], meta['word'] + ' vigente 45 segundos')
        entry('docs/knowledge/approved/gotchas/peer.md', meta['peer'], 'aprobado', 2, 'GOTCHA',
              body='Relación declarada sintética, no sucesión')
        entry('docs/knowledge/adr/ADR-101-fixture.md', 'ADR-101',
              'aceptada (fixture sintética; sin aprobación humana real)', 3, body=meta['word'] + ' antecedente')
        entry('docs/knowledge/gotchas/GOT-102-fixture.md', 'GOT-102', 'propuesta', body='Patrón pendiente')
        entry('docs/knowledge/adr/ADR-103-fixture.md', 'ADR-103',
              'obsoleta (sustituida por ADR-101; fixture sintética)', body=meta['word'] + ' anterior 90 segundos')
        for state in ('pending', 'needs_changes', 'rejected'):
            entry('docs/knowledge/candidates/' + state + '/candidate.md', 'CANDIDATE-' + state,
                  'propuesta', body=self.gold['expected']['candidate_word'])
        (root / 'docs/knowledge/README.md').write_text('# Índice sintético\n', encoding='utf-8')
        return root

    def launch(self, root, script, arguments, stdin=None, frontier=None, source=None,
               event_id=None, mode='cli', destination=None):
        if time.monotonic() >= self.run_budget['deadline_monotonic']:
            raise protocol.InfrastructureError('whole-run launch deadline exceeded (420 seconds)')
        if len(self.calls) >= protocol.MAX_PROCESSES:
            raise protocol.InfrastructureError('per-case child budget exceeded')
        if self.run_budget['children'] >= self.run_budget['maximum']:
            raise protocol.InfrastructureError('whole-run child budget exceeded')
        # Windows venv launchers may introduce another process between Popen and
        # the executing child. Run the base interpreter directly; keep all PID,
        # ppid, nonce and frontier guards unchanged. Product children use stdlib.
        interpreter_value = getattr(sys, '_base_executable', None) if os.name == 'nt' else sys.executable
        if (not interpreter_value or not Path(interpreter_value).is_absolute()
                or not Path(interpreter_value).is_file()):
            raise protocol.InfrastructureError('child interpreter must be an existing absolute file')
        interpreter = Path(interpreter_value).resolve()
        interpreter_record = {'path': str(interpreter),
                              'sha256': protocol.digest(interpreter.read_bytes()),
                              'selection': 'windows_base' if os.name == 'nt' else 'posix_current'}
        self.run_budget['children'] += 1
        source = source or self.source
        control = self.work / ('child-' + str(len(self.calls))); control.mkdir()
        nonce = uuid.uuid4().hex
        target = source / 'agent-kits/shared' / script if script else None
        spec = {'schema': 1, 'nonce': nonce, 'own': str(self.own), 'source': str(source), 'control': str(control),
                'root': str(root), 'mode': mode, 'parent_pid': os.getpid(), 'script': str(target) if target else None,
                'script_sha256': protocol.digest(target.read_bytes()) if target else None,
                'arguments': [*arguments, '--root', str(root)] if target else [], 'frontier': frontier,
                'event_id': event_id, 'destination': str(destination) if destination else None}
        spec['interpreter'] = interpreter_record
        spec['allowed_source_files'] = [record['path'] for record in self.selection['files']]
        spec['allowed_source_sha256'] = {record['path']: record['sha256'] for record in self.selection['files']}
        spec['allowed_source_probes'] = ['.claude-plugin/plugin.json', '.codex-plugin/plugin.json']
        write_json(control / 'spec.json', spec)
        with (control / 'stdout.txt').open('wb') as out, (control / 'stderr.txt').open('wb') as err:
            if time.monotonic() >= self.run_budget['deadline_monotonic']:
                raise protocol.InfrastructureError('whole-run launch deadline exceeded (420 seconds)')
            proc = subprocess.Popen([str(interpreter), '-I', '-X', 'utf8', '-B', str(self.support / 'child.py'), str(control / 'spec.json')],
                                    cwd=root, env=self.environment, stdin=subprocess.PIPE, stdout=out, stderr=err)
        row = {'process': proc, 'control': control, 'nonce': nonce, 'spec': spec}
        self.calls.append(row)
        try:
            protocol.atomic_record(control / 'parent-registration.json', {'nonce': nonce, 'pid': proc.pid,
                                   'parent_pid': os.getpid(), 'created_utc_ns': time.time_ns()})
            proc.stdin.write((json.dumps(stdin, ensure_ascii=False) if stdin is not None else '').encode('utf-8'))
            proc.stdin.close()
        except BaseException as exc:
            try:
                proc.stdin.close()
            except Exception:
                pass
            self.safety_stop(row, 'launch_registration_or_stdin_failed')
            raise protocol.InfrastructureError('child setup failed after owned Popen registration') from exc
        return row

    def finish(self, child, expected=(0,)):
        proc, control = child['process'], child['control']
        try: proc.wait(timeout=protocol.CHILD_SECONDS + 5)
        except subprocess.TimeoutExpired as exc:
            self.safety_stop(child, 'safety_timeout')
            raise protocol.InfrastructureError('CLI safety deadline exceeded') from exc
        outputs = []
        for name in ('stdout.txt', 'stderr.txt'):
            path = control / name
            if path.stat().st_size > protocol.MAX_OUTPUT_BYTES:
                raise protocol.InfrastructureError('child output budget exceeded')
            outputs.append(path.read_text(encoding='utf-8'))
        if proc.returncode == 86 or 'OWN_INFRASTRUCTURE:' in outputs[1]:
            raise protocol.InfrastructureError(outputs[1])
        self.check_audit(child)
        if proc.returncode not in expected:
            raise AssertionError(f'public CLI exit {proc.returncode}: {outputs[1]}')
        return outputs

    def check_audit(self, child):
        audit_path = child['control'] / 'audit.json'
        if child['spec']['mode'] == 'cli':
            if not audit_path.exists():
                raise protocol.InfrastructureError('required CLI audit missing')
            try:
                audit = json.loads(audit_path.read_text(encoding='utf-8'))
                if (audit['nonce'] != child['nonce'] or not isinstance(audit['attempts'], list)
                        or not isinstance(audit['source_reads'], list)
                        or not isinstance(audit['bytecode_probes'], list)
                        or not all(isinstance(item, dict) and isinstance(item.get('kind'), str)
                                   for item in audit['attempts'])):
                    raise ValueError('audit identity or schema differs')
            except (OSError, ValueError, KeyError, TypeError) as exc:
                raise protocol.InfrastructureError('CLI audit malformed/unreadable') from exc
            args = child['spec']['arguments']
            git_allowed = (Path(child['spec']['script']).name == 'journal.py'
                           and args and args[0] in ('write', 'replay', 'recover'))
            if any(item['kind'] != 'git_unavailable' or not git_allowed
                   for item in audit['attempts']):
                raise protocol.InfrastructureError('prohibited runtime attempt: ' + str(audit['attempts']))
            source = Path(child['spec']['source'])
            exact_probes = {Path(importlib.util.cache_from_source(str(source / rel))).relative_to(source).as_posix(): rel
                            for rel in child['spec']['allowed_source_files']
                            if rel.startswith('agent-kits/shared/') and rel.endswith('.py')}
            for probe in audit['bytecode_probes']:
                rel = probe.get('path') if isinstance(probe, dict) else None
                helper = exact_probes.get(rel)
                if (not helper or probe.get('kind') != 'expected_absent_bytecode_probe'
                        or probe.get('pid') != child['process'].pid or probe.get('source') != helper
                        or probe.get('source_sha256') != child['spec']['allowed_source_sha256'][helper]
                        or rel in audit['source_reads']):
                    raise protocol.InfrastructureError('bytecode probe outside exact frozen helper selection')

    def stop(self, child, reason='observed_barrier'):
        proc, control = child['process'], child['control']
        try:
            if proc.poll() is not None:
                raise protocol.InfrastructureError('child exited before observed cut')
            started = json.loads((control / 'started.json').read_text(encoding='utf-8'))
            if (started['pid'] != proc.pid or started['nonce'] != child['nonce']
                    or started['parent_pid'] != os.getpid()
                    or started['script_sha256'] != child['spec']['script_sha256']):
                raise protocol.InfrastructureError('child identity mismatch')
            protocol.atomic_record(control / 'termination-intent.json', {'nonce': child['nonce'], 'pid': proc.pid,
                                   'reason': reason, 'identity_kind': 'child_started',
                                   'script_sha256': child['spec']['script_sha256'],
                                   'before_kill_utc_ns': time.time_ns()})
            proc.kill(); proc.wait(timeout=5)
            protocol.atomic_record(control / 'terminated.json', {'nonce': child['nonce'], 'pid': proc.pid,
                                   'returncode': proc.returncode, 'after_wait_utc_ns': time.time_ns()})
            self.check_audit(child)
        except Exception as exc:
            self.safety_stop(child, 'observed_cut_receipt_or_cleanup_failed')
            raise protocol.InfrastructureError('observed cut evidence/cleanup incomplete') from exc

    def safety_stop(self, child, reason):
        # Memory-held exact Popen ownership permits safety cleanup even when all
        # control writes/receipts fail. Best effort evidence is not a durable ACK.
        if not any(row is child for row in self.calls):
            raise protocol.InfrastructureError('cleanup handle not registered in this Lab')
        proc, control = child['process'], child['control']
        issues = []
        before = {'nonce': child['nonce'], 'pid': proc.pid, 'reason': reason,
                  'identity_kind': 'parent_owned_handle_only', 'frontier_proven': False,
                  'before_kill_utc_ns': time.time_ns()}
        try:
            protocol.atomic_record(control / 'safety-termination-intent.json', before)
        except Exception as exc:
            issues.append('intent evidence unavailable: ' + repr(exc))
        try:
            if proc.poll() is None:
                proc.kill()
        except Exception as exc:
            issues.append('owned kill failed: ' + repr(exc))
        try:
            proc.wait(timeout=5)
        except Exception as exc:
            issues.append('owned reap failed: ' + repr(exc))
        try:
            protocol.atomic_record(control / 'safety-terminated.json',
                                  {**before, 'returncode': proc.returncode,
                                   'after_wait_utc_ns': time.time_ns(), 'issues': issues})
        except Exception as exc:
            issues.append('termination evidence unavailable: ' + repr(exc))
        self.cleanup_errors.extend(issues)
        return issues

    def barrier(self, child):
        proc, control = child['process'], child['control']
        deadline = time.monotonic() + protocol.CHILD_SECONDS
        while time.monotonic() < deadline:
            if (control / 'ready.json').exists():
                ready = json.loads((control / 'ready.json').read_text(encoding='utf-8'))
                expected_frontier = (child['spec']['frontier'] if child['spec']['mode'] == 'cli'
                                     else 'backup_before_complete_manifest')
                if (ready['pid'] != proc.pid or ready['nonce'] != child['nonce']
                        or ready['parent_pid'] != os.getpid() or ready['frontier'] != expected_frontier
                        or ready['script_sha256'] != child['spec']['script_sha256']
                        or proc.poll() is not None):
                    raise protocol.InfrastructureError('barrier identity unavailable')
                return ready
            if proc.poll() is not None:
                self.finish(child)
                raise protocol.InfrastructureError('required frontier not reached')
            time.sleep(0.01)
        self.safety_stop(child, 'barrier_timeout')
        raise protocol.InfrastructureError('frontier safety deadline exceeded')

    def cli(self, root, script, *arguments, stdin=None, expected=(0,), **options):
        child = self.launch(root, script, arguments, stdin=stdin, **options)
        output, error = self.finish(child, expected)
        return (json.loads(output) if output.strip().startswith(('{', '[')) else output), child, error

    def query(self, root, *arguments, expected=(0,)):
        return self.cli(root, 'knowledge-find.py', '--view', '--limit', '20', *arguments, expected=expected)[0]

    def prompt(self, root, sid, text=None):
        self.cli(root, 'journal.py', 'capture', stdin={'session_id': sid, 'prompt': text or self.gold['expected']['pending_quote']})

    def capture(self, root, sid):
        before = set((root / '.claude/journal/outbox').glob('*.json'))
        self.cli(root, 'journal-capture.py', stdin={'session_id': sid, 'hook_event_name': 'SessionEnd', 'reason': 'other'})
        paths = set((root / '.claude/journal/outbox').glob('*.json')) - before
        assert len(paths) == 1, 'capture unconfirmed: final envelope absent or multiple'
        path = paths.pop(); raw = path.read_bytes(); env = json.loads(raw)
        assert env['session_id'] == sid and env['schema_version'] == 1 and env['event_id'] == path.stem
        assert raw == path.read_bytes() and not any(k in env for k in ('prompt', 'transcript', 'conversation'))
        protocol.atomic_record(self.work / ('ack-' + env['event_id'] + '.json'), {'synthetic_only': True,
                               'event_id': env['event_id'], 'session_id': sid, 'sha256': protocol.digest(raw),
                               'confirmed_utc_ns': time.time_ns(), 'ack': 'CLI finished; stable final JSON; no power-loss claim'})
        return path

    def replay(self, root, *extra, **options):
        return self.cli(root, 'journal.py', 'replay', '--ia', 'no', '--max', '12', '--budget-ms', '4000', *extra, **options)

    def journals(self, root, sid):
        marker = 'session_id: ' + json.dumps(sid, ensure_ascii=False)
        return [p for p in (root / 'docs/knowledge/journal').glob('*.md') if marker in p.read_text(encoding='utf-8')]

    def previous(self, root):
        self.cli(root, 'journal.py', 'write', '--session-id', 'previous-synthetic', '--enrich', '-', '--ia', 'off',
                 stdin={'resumen': 'Historia sintética conservada', 'pendientes': ['Pendiente previo sintético']})
        docs = self.journals(root, 'previous-synthetic'); assert len(docs) == 1
        return docs[0], docs[0].read_bytes()

    def restore(self, root, label):
        snapshot, target = self.work / (label + '-backup'), self.work / (label + '-restored')
        before = protocol.backup_drill(root, snapshot, own=self.own)
        protocol.restore_drill(snapshot, target, own=self.own)
        assert protocol.inventory(root) == before == protocol.inventory(target)
        return target, snapshot

    def age_claim(self, root):
        epoch = time.time() - 700
        for path in (root / '.claude/journal/processing').glob('*'):
            if path.is_file():
                os.utime(path, (epoch, epoch))
                if path.name.endswith('.claimed_at'): path.write_text(str(epoch), encoding='utf-8')
        self.mutations.append({'kind': 'synthetic TTL elapsed', 'epoch': epoch})
        write_json(self.work / 'fixture-mutations.json', self.mutations)

    def close(self):
        for child in self.calls:
            try:
                if child['process'].poll() is None:
                    self.safety_stop(child, 'fixture_finalizer')
            except Exception as exc:
                self.cleanup_errors.append('finalizer failed: ' + repr(exc))
        try:
            write_json(self.work / 'case-process-ledger.json',
                       {'processes': [{'pid': c['process'].pid, 'nonce': c['nonce'],
                                       'mode': c['spec']['mode'], 'frontier': c['spec']['frontier'],
                                       'returncode': c['process'].returncode} for c in self.calls],
                        'cleanup_errors': self.cleanup_errors})
        except Exception as exc:
            self.cleanup_errors.append('ledger unavailable: ' + repr(exc))
        if self.cleanup_errors:
            raise protocol.InfrastructureError('cleanup/evidence incomplete: ' + str(self.cleanup_errors))


def stable_view(data):
    return {k: v for k, v in data.items() if k != 'observed_at'}


def test_N01_restore_preserves_bytes_authority_queries_and_queue_states(lab):
    root = lab.project(); lab.previous(root)
    lab.prompt(root, 'done'); lab.capture(root, 'done'); lab.replay(root)
    bad = lab.capture(root, 'dead-letter')
    bad_env = json.loads(bad.read_bytes()); bad_env['schema_version'] = 999; write_json(bad, bad_env)
    lab.replay(root)
    lab.prompt(root, 'pending'); pending = lab.capture(root, 'pending')
    write_json(pending.with_name(pending.name + '.intentos'), {'intentos': 1, 'no_antes_de': time.time() + 1200})
    lab.prompt(root, 'processing'); active = lab.capture(root, 'processing')
    processing = root / '.claude/journal/processing' / active.name
    active.rename(processing)
    processing.with_name(processing.name + '.claimed_at').write_text(str(time.time()), encoding='utf-8')
    write_json(lab.work / 'fixture-mutations.json', {'schema': 1, 'synthetic_only': True,
               'actions': ['schema999 rejected event', 'future backoff sidecar', 'quiescent processing state']})
    queries = [('AtlasOwnWord',), ('--show', lab.gold['projects']['atlas']['current']),
               ('--related', lab.gold['projects']['atlas']['current'])]
    before = [stable_view(lab.query(root, *query)) for query in queries]
    assert {e['id'] for e in before[0]['entries']} == set(lab.gold['questions'][0]['expected_ids'])
    assert before[1]['selected']['version'] == 7 and before[1]['selected']['origen'] == 'approved'
    assert lab.gold['projects']['atlas']['peer'] in {e['id'] for e in before[2]['related']['enlaces']}
    original_status = lab.cli(root, 'journal.py', 'status', '--json')[0]
    restored, _ = lab.restore(root, 'N01')
    assert [stable_view(lab.query(restored, *query)) for query in queries] == before
    restored_status = lab.cli(restored, 'journal.py', 'status', '--json')[0]
    for field in ('outbox', 'processing', 'done', 'dead-letter', 'en_backoff'):
        assert original_status[field] == restored_status[field] == 1
    assert state_bytes(root) == state_bytes(restored)


@pytest.mark.parametrize('cache', ['absent', 'corrupt'])
def test_N02_cache_rebuild_and_readonly_view(lab, cache):
    root = lab.project(); restored, _ = lab.restore(root, 'N02')
    canonical = state_bytes(restored)
    index = restored / '.claude/knowledge-index.sqlite'
    if cache == 'corrupt': index.write_bytes(b'OWN invalid SQLite')
    baseline = lab.cli(restored, 'knowledge-find.py', 'AtlasOwnWord', '--no-index', '--json')[0]
    assert baseline['corpus_read']['complete'] is True, baseline
    expected = baseline['aciertos']
    before = tree_bytes(restored); view = lab.query(restored, 'AtlasOwnWord')
    assert view['complete'] is True, view
    assert tree_bytes(restored) == before
    actual = lab.cli(restored, 'knowledge-find.py', 'AtlasOwnWord', '--json')[0]
    assert actual['corpus_read']['complete'] is True, actual
    assert actual['aciertos'] == expected
    if actual['indice'] not in ('construido', 'reconstruido', 'cache'):
        reason = actual.get('indice_motivo', '')
        issues = actual['corpus_read'].get('issues', [])
        if reason == 'sqlite3 sin FTS5':
            raise protocol.InfrastructureError('SQLite/FTS5 unavailable; cause=' + reason + '; issues=' + str(issues))
        raise AssertionError('index rebuild failed: indice=' + str(actual['indice'])
                             + '; motivo=' + reason + '; issues=' + str(issues))
    assert index.read_bytes().startswith(b'SQLite format 3\x00')
    assert state_bytes(restored) == canonical


def test_N03_cut_before_capture_publish_is_unconfirmed_and_log_recoverable(lab):
    root = lab.project(); lab.prompt(root, 'uncaptured')
    log = root / '.claude/session-prompts-uncaptured.log'; before = log.read_bytes()
    child = lab.launch(root, 'journal-capture.py', (), stdin={'session_id': 'uncaptured', 'reason': 'other'},
                       frontier='capture_before_publish')
    assert lab.barrier(child)['frontier'] == 'capture_before_publish'
    outbox = root / '.claude/journal/outbox'
    temporaries = [p for p in outbox.glob('*.json') if p.name.startswith('.tmp-')]
    assert len(temporaries) == 1
    temporary = temporaries[0]; temporary_bytes = temporary.read_bytes()
    assert json.loads(temporary_bytes)['session_id'] == 'uncaptured'
    assert final_envelopes(outbox) == [] and log.read_bytes() == before
    assert not list(lab.work.glob('ack-*.json'))
    write_json(child['control'] / 'N03-before-kill-observation.json',
               {'nonce': child['nonce'], 'phase': 'before_kill', 'temporary': temporary.name,
                'temporary_sha256': protocol.digest(temporary_bytes), 'final_envelopes': [],
                'log_sha256': protocol.digest(before), 'ack_observed': False})
    lab.stop(child)
    assert log.read_bytes() == before and final_envelopes(outbox) == []
    assert temporary.read_bytes() == temporary_bytes
    assert not list(lab.work.glob('ack-*.json'))
    write_json(child['control'] / 'N03-after-kill-observation.json',
               {'nonce': child['nonce'], 'phase': 'after_kill', 'temporary': temporary.name,
                'temporary_sha256': protocol.digest(temporary.read_bytes()), 'final_envelopes': [],
                'log_sha256': protocol.digest(log.read_bytes()), 'ack_observed': False})
    recovered = lab.cli(root, 'journal.py', 'recover', '--session-id', 'uncaptured', '--budget-ms', '4000', '--max', '1')[0]
    assert recovered['recuperadas'] == 1
    docs = lab.journals(root, 'uncaptured'); assert len(docs) == 1
    text = docs[0].read_text(encoding='utf-8')
    assert 'recuperado_sin_cierre' in text and lab.gold['expected']['pending_quote'] in text
    assert not list(lab.work.glob('ack-*.json'))


@pytest.mark.parametrize('frontier', ['claim_after_claiming', 'journal_after_publish', 'done_before_envelope_move'])
def test_N04_confirmed_capture_survives_cut_and_restart_once(lab, frontier):
    root = lab.project(); previous, old = lab.previous(root)
    lab.prompt(root, 'interrupted'); event = lab.capture(root, 'interrupted')
    child = lab.launch(root, 'journal.py', ('replay', '--ia', 'no', '--max', '1', '--budget-ms', '4000'), frontier=frontier)
    assert lab.barrier(child)['frontier'] == frontier
    lab.stop(child); lab.age_claim(root)
    result = lab.replay(root)[0]
    assert not result['errores']
    assert len(lab.journals(root, 'interrupted')) == 1
    text = lab.journals(root, 'interrupted')[0].read_text(encoding='utf-8')
    assert lab.gold['expected']['pending_quote'] in text and 'materializado' in text
    lab.replay(root)
    assert len(lab.journals(root, 'interrupted')) == 1 and previous.read_bytes() == old
    done = root / '.claude/journal/done' / event.name
    assert json.loads(done.read_bytes())['session_id'] == 'interrupted'
    manifest = json.loads(done.with_name(done.name + '.manifest.json').read_bytes())
    assert manifest['hash'] == protocol.digest(done.read_bytes())


def test_N05_manifest_failure_visible_then_restored_replay_idempotent(lab):
    root = lab.project(); previous, old = lab.previous(root)
    lab.prompt(root, 'manifest-failure'); bad = lab.capture(root, 'manifest-failure')
    lab.prompt(root, 'healthy'); good = lab.capture(root, 'healthy')
    result, child, _ = lab.replay(root, frontier='fail_manifest_once', event_id=bad.stem)
    if not (child['control'] / 'fault.json').exists():
        raise protocol.InfrastructureError('required injected manifest fault not reached')
    assert result['materializados'] == 1 and result['reintentados'] == 1 and result['en_backoff'] == 1
    assert any('manifiesto pendiente' in warning for warning in result['avisos'])
    assert len(lab.journals(root, 'manifest-failure')) == len(lab.journals(root, 'healthy')) == 1
    restored, _ = lab.restore(root, 'N05')
    assert lab.gold['expected']['pending_quote'] in lab.journals(restored, 'manifest-failure')[0].read_text(encoding='utf-8')
    second = lab.replay(restored, '--reintentar-ahora')[0]
    assert second['materializados'] == 1 and second['en_backoff'] == 0
    lab.replay(restored)
    assert len(lab.journals(restored, 'manifest-failure')) == len(lab.journals(restored, 'healthy')) == 1
    assert (restored / previous.relative_to(root)).read_bytes() == old
    for event in (bad, good):
        final = restored / '.claude/journal/done' / event.name
        assert final.exists() and final.with_name(final.name + '.manifest.json').exists()


def test_N06_torn_or_tampered_backup_rejected_before_destination_mutation(lab):
    root = lab.project()
    canonical_sentinel = root / 'docs/knowledge/approved/adr/preserve.tmp-2026.md'
    sentinel_bytes = b'Synthetic canonical evidence; no human approval; preserve exact bytes.\n'
    canonical_sentinel.write_bytes(sentinel_bytes)
    before = state_bytes(root)
    torn = lab.work / 'torn-backup'
    child = lab.launch(root, None, (), mode='backup_drill', destination=torn)
    assert lab.barrier(child)['frontier'] == 'backup_before_complete_manifest'
    lab.stop(child)
    for label in ('torn', 'tampered'):
        snapshot = torn
        if label == 'tampered':
            snapshot = lab.work / 'tampered-backup'; protocol.backup_drill(root, snapshot, own=lab.own)
            path = snapshot / 'data/docs/knowledge/approved/adr/current.md'; path.write_bytes(path.read_bytes() + b'altered')
        target = lab.work / (label + '-rejected-target')
        with pytest.raises(protocol.RestoreRejected): protocol.restore_drill(snapshot, target, own=lab.own)
        assert not target.exists() and not target.with_name(target.name + '.restore-staging').exists()
    existing = lab.work / 'unowned-existing-target'; existing.mkdir()
    sentinel = existing / 'preserve.txt'; sentinel.write_bytes(b'OWN sentinel')
    valid = lab.work / 'complete-backup'; protocol.backup_drill(root, valid, own=lab.own)
    with pytest.raises(protocol.RestoreRejected): protocol.restore_drill(valid, existing, own=lab.own)
    assert sentinel.read_bytes() == b'OWN sentinel' and state_bytes(root) == before
    restored = lab.work / 'N06-valid-restored'
    protocol.restore_drill(valid, restored, own=lab.own)
    assert (restored / canonical_sentinel.relative_to(root)).read_bytes() == sentinel_bytes
    assert canonical_sentinel.read_bytes() == sentinel_bytes


def test_N07_candidate_exclusion_legacy_authority_and_collision_after_restore(lab):
    root = lab.project(); restored, _ = lab.restore(root, 'N07')
    for key in ('legacy_accepted', 'legacy_proposal', 'legacy_obsolete'):
        gold = lab.gold['expected'][key]; entry = lab.query(restored, '--show', gold['id'])['selected']
        for field in ('id', 'estado', 'origen', 'version'): assert entry[field] == gold[field]
    assert lab.query(restored, lab.gold['expected']['candidate_word'])['entries'] == []
    current = lab.gold['projects']['atlas']['current']; selected = lab.query(restored, '--show', current)['selected']
    assert selected['origen'] == 'approved' and selected['version'] == 7
    collision = restored / 'docs/knowledge/adr/collision.md'
    collision.write_text('---\nid: ' + current + '\nestado: propuesta\narea: memoria\n---\n# Fixture collision\n', encoding='utf-8')
    ambiguous = lab.query(restored, '--show', current, expected=(1,))
    assert ambiguous['status'] == 'ambiguous' and ambiguous['selected'] is None


def test_N08_view_status_are_readonly_offline_and_missing_outbox_is_degraded(lab):
    root = lab.project(); restored, _ = lab.restore(root, 'N08'); before = tree_bytes(restored)
    view, view_child, _ = lab.cli(restored, 'knowledge-find.py', '--view', 'AtlasOwnWord')
    status, status_child, _ = lab.cli(restored, 'journal.py', 'status', '--json')
    assert view['source'] == 'canonical_knowledge' and isinstance(status['avisos'], list)
    assert tree_bytes(restored) == before
    for child in (view_child, status_child):
        assert json.loads((child['control'] / 'audit.json').read_text(encoding='utf-8'))['attempts'] == []
    partial = lab.work / 'partial-source'
    for relative in ('agent-kits/shared/journal.py', 'agent-kits/shared/journal-capture.py',
                     'agent-kits/shared/redact.py', 'agent-kits/shared/local-read.py', 'package.json'):
        target = partial / relative; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((lab.source / relative).read_bytes())
    assert not (partial / 'agent-kits/shared/outbox.py').exists()
    diagnostic = lab.cli(restored, 'journal.py', 'status', '--json', source=partial)[0]
    assert any('degradado' in warning for warning in diagnostic['avisos'])
    assert tree_bytes(restored) == before


def test_N09_project_scope_private_turn_and_redaction_survive_restore(lab):
    root = lab.project(); other = lab.project('boreal'); secret = 'sk-' + 'A' * 35
    lab.prompt(root, 'private', '<private>' + lab.gold['expected']['private_word'])
    assert not (root / '.claude/session-prompts-private.log').exists()
    lab.prompt(root, 'public', lab.gold['expected']['pending_quote'] + '. token: ' + secret)
    log = root / '.claude/session-prompts-public.log'; assert secret.encode('utf-8') not in log.read_bytes()
    lab.capture(root, 'public'); restored, _ = lab.restore(root, 'N09'); lab.replay(restored)
    text = '\n'.join(p.read_text(encoding='utf-8') for p in lab.journals(restored, 'public'))
    assert lab.gold['expected']['pending_quote'] in text
    assert lab.gold['expected']['private_word'] not in text and secret not in text
    assert lab.query(restored, 'BorealForeignWord')['entries'] == []
    assert {e['id'] for e in lab.query(other, 'BorealForeignWord')['entries']} >= {lab.gold['projects']['boreal']['current']}
    legacy = restored / 'docs/knowledge/adr/ADR-101-fixture.md'
    raw = legacy.read_bytes() + ('\n' + secret).encode('utf-8'); legacy.write_bytes(raw)
    view = lab.query(restored, '--show', 'ADR-101')
    assert secret not in json.dumps(view, ensure_ascii=False) and legacy.read_bytes() == raw
