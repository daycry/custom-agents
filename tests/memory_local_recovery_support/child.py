"""OWN child: transparent public CLI with optional frontier barriers; never product CLI."""
from __future__ import annotations

import errno
import importlib.util
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from protocol import (InfrastructureError, atomic_record, backup_drill, digest,
                      pause, within)


def main():
    if len(sys.argv) != 2:
        raise InfrastructureError('child requires one OWN spec')
    spec_path = Path(sys.argv[1]).resolve()
    spec = json.loads(spec_path.read_text(encoding='utf-8'))
    own = Path(spec['own']).resolve()
    within(spec_path, own)
    control = within(spec['control'], own)
    root = within(spec['root'], own)
    if spec['parent_pid'] != os.getppid() or (control / 'started.json').exists():
        raise InfrastructureError('child ownership does not match')
    started = {'schema': 1, 'nonce': spec['nonce'], 'pid': os.getpid(),
               'parent_pid': os.getppid(), 'started_utc_ns': time.time_ns(),
               'mode': spec['mode'], 'root': str(root), 'script_sha256': spec.get('script_sha256')}
    atomic_record(control / 'started.json', started)
    if spec['mode'] == 'backup_drill':
        backup_drill(root, spec['destination'], own=own, barrier=spec)
        atomic_record(control / 'finished.json', {'nonce': spec['nonce'], 'exit': 0})
        return 0
    script = Path(spec['script']).resolve()
    source = Path(spec['source']).resolve()
    if source not in script.parents or digest(script.read_bytes()) != spec['script_sha256']:
        raise InfrastructureError('unregistered CLI source')
    if script.name not in ('journal.py', 'journal-capture.py', 'knowledge-find.py'):
        raise InfrastructureError('unapproved public CLI')

    # Audit is independent of the optional timing barrier. It records/blocks actual
    # attempts; static module presence is never counted as network execution.
    attempted, source_reads, bytecode_probes = [], [], []
    allowed_files = set(spec['allowed_source_files']) | set(spec.get('allowed_source_probes', ()))
    # importlib probes bytecode even under -B. Only the exact cache_from_source
    # path for selected public helpers may behave as absent; never read its bytes.
    absent_bytecode = {Path(importlib.util.cache_from_source(str(source / rel))).resolve(): rel
                       for rel in spec['allowed_source_files']
                       if rel.startswith('agent-kits/shared/') and rel.endswith('.py')}
    if any(path.exists() for path in absent_bytecode):
        raise InfrastructureError('frozen helper bytecode is present before execution')
    def record_audit():
        atomic_record(control / 'audit.json', {'nonce': spec['nonce'], 'attempts': attempted,
                      'source_reads': source_reads, 'bytecode_probes': bytecode_probes})
    record_audit()
    def audit(event, arguments):
        if event.startswith('socket.') or event in ('urllib.Request', 'http.client.connect'):
            attempted.append({'kind': 'network', 'event': event})
            record_audit()
            raise PermissionError('OWN child prohibits all network')
        if event == 'subprocess.Popen':
            audited_executable = arguments[0]
            command = arguments[1]
            owner_git = (["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all"],
                         ["git", "-C", str(root), "status", "--porcelain"])
            if os.name == 'nt':
                expected = tuple(subprocess.list2cmdline(argv) for argv in owner_git)
                closed_git = audited_executable is None and isinstance(command, str) and command in expected
            else:
                closed_git = (audited_executable == 'git' and isinstance(command, (tuple, list))
                              and any(list(command) == argv for argv in owner_git))
            kind = 'git_unavailable' if closed_git else 'process_forbidden'
            attempted.append({'kind': kind, 'event': event,
                              'audit_executable': audited_executable,
                              'audit_arguments': list(command) if isinstance(command, (tuple, list)) else command,
                              'argument_transport': type(command).__name__, 'closed_owner_match': closed_git})
            record_audit()
            raise FileNotFoundError('OWN no-Git/no-model environment')
        if event == 'open':
            name, mode, flags = arguments
            if isinstance(name, (str, bytes, os.PathLike)):
                path = Path(os.fsdecode(name)).resolve()
                writes = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (
                    isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
                if writes:
                    within(path, own)
                if not writes and path in absent_bytecode:
                    rel = path.relative_to(source).as_posix()
                    helper = absent_bytecode[path]
                    if not any(probe['path'] == rel for probe in bytecode_probes):
                        bytecode_probes.append({'kind': 'expected_absent_bytecode_probe', 'path': rel,
                                                'source': helper,
                                                'source_sha256': spec['allowed_source_sha256'][helper],
                                                'pid': os.getpid()})
                        record_audit()
                    raise FileNotFoundError(errno.ENOENT, 'OWN bytecode probe forced absent', str(path))
                if source in path.parents:
                    rel = path.relative_to(source).as_posix()
                    if rel not in allowed_files:
                        attempted.append({'kind': 'unregistered_source_read', 'path': rel})
                        record_audit()
                        raise PermissionError('source dependency not in frozen selection')
                    if rel not in source_reads:
                        source_reads.append(rel)
                        record_audit()
                    if rel.startswith(('.claude/', '.codex/', '.opencode/', 'docs/knowledge/')):
                        raise PermissionError('source consumer files are excluded')
                    if '/backends/' in rel or rel.startswith('skills/'):
                        attempted.append({'kind': 'adapter', 'event': event})
                        record_audit()
                        raise PermissionError('local acceptance never imports adapters')
    sys.addaudithook(audit)

    original_replace = os.replace
    reached = False
    def observed_replace(old, new, *args, **kwargs):
        nonlocal reached
        target = Path(new).resolve()
        inside = root in target.parents
        relative = target.relative_to(root).as_posix() if inside else ''
        frontier = spec.get('frontier')
        before = frontier == 'capture_before_publish' and relative.startswith('.claude/journal/outbox/') and relative.endswith('.json')
        after_claim = frontier == 'claim_after_claiming' and relative.startswith('.claude/journal/processing/') and relative.endswith('.json.claiming')
        after_entry = frontier == 'journal_after_publish' and relative.startswith('docs/knowledge/journal/') and relative.endswith('.md') and target.name != 'README.md'
        before_done = frontier == 'done_before_envelope_move' and relative.startswith('.claude/journal/done/') and relative.endswith('.json') and not relative.endswith('.manifest.json')
        fail_manifest = (frontier == 'fail_manifest_once'
                         and relative == '.claude/journal/done/' + spec['event_id'] + '.json.manifest.json')
        if not reached and (before or before_done or fail_manifest):
            reached = True
            if fail_manifest:
                atomic_record(control / 'fault.json', {**started, 'frontier': frontier,
                             'reached_utc_ns': time.time_ns(), 'injected_errno': errno.ENOSPC})
                raise OSError(errno.ENOSPC, 'OWN synthetic manifest failure')
            pause(spec, frontier, target)
        result = original_replace(old, new, *args, **kwargs)
        if not reached and (after_claim or after_entry):
            reached = True
            pause(spec, frontier, target)
        return result
    if spec.get('frontier'):
        # Runtime timing/fault instrumentation confined to one owned child. Source
        # bytes remain exact. This is not an independent implementation of a writer.
        os.replace = observed_replace
    sys.argv = [str(script), *spec['arguments']]
    exit_code = 0
    try:
        runpy.run_path(str(script), run_name='__main__')
    except SystemExit as exc:
        exit_code = exc.code if isinstance(exc.code, int) else int(bool(exc.code))
    finally:
        os.replace = original_replace
        record_audit()
    atomic_record(control / 'finished.json', {'nonce': spec['nonce'], 'exit': exit_code,
                  'frontier_reached': reached, 'finished_utc_ns': time.time_ns()})
    return exit_code


if __name__ == '__main__':
    try:
        sys.exit(main())
    except InfrastructureError as exc:
        print('OWN_INFRASTRUCTURE: ' + str(exc), file=sys.stderr)
        sys.exit(86)
