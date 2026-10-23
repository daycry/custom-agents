#!/usr/bin/env python3
"""Local proposal and curation persistence; semantic judgment belongs to the curator.

The process lock coordinates this service's writers, not arbitrary editors.
Exclusive publication is one filesystem boundary; source retirement and receipt
are separate, explicitly recoverable boundaries. Role labels are declarations.
"""
import argparse
from contextlib import contextmanager, nullcontext
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import sys
import uuid

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

HERE = Path(__file__).absolute().parent
MAX_BYTES = 256 * 1024
MAX_ENTRIES = 4096
MAX_SCAN_BYTES = 8 * 1024 * 1024
MAX_OPERATION_BYTES = 1024 * 1024
BASE = 'docs/knowledge/candidates'
STATES = ('pending', 'needs_changes', 'rejected')
OPERATIONS = BASE + '/.curation/operations'
RECEIPTS = BASE + '/.curation/receipts'
_MODULES = {}


def _mkdir_private(path, **kwargs):
    """0o700 en POSIX. En Windows se heredan los permisos del padre: Python 3.13 convierte
    0o700 en una ACL explícita que deja fuera al usuario restringido del sandbox de Codex."""
    if os.name == 'nt':
        path.mkdir(**kwargs)
    else:
        path.mkdir(mode=0o700, **kwargs)


class _Failure(Exception):
    def __init__(self, status, code=1, errors=None):
        self.status, self.code, self.errors = status, code, errors


def _module(filename):
    if filename not in _MODULES:
        spec = importlib.util.spec_from_file_location(
            'curation_' + filename.replace('-', '_').replace('.', '_'), HERE / filename)
        if spec is None or spec.loader is None:
            raise _Failure('shared_unavailable', 2)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _MODULES[filename] = module
    return _MODULES[filename]


def _hash(raw):
    return hashlib.sha256(raw).hexdigest()


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def _result(status, code=0, errors=None, **fields):
    return dict(status=status, errores=errors or ([] if code == 0 else [
        {'mensaje': status, 'campo': '$'}]), avisos=[], **fields), code


def _caught(exc, **fields):
    if isinstance(exc, _Failure):
        result, code = _result(exc.status, exc.code, exc.errors, **fields)
        try:
            result = json.loads(_module('redact.py').redactar(json.dumps(result, ensure_ascii=False)))
        except (OSError, ValueError, TypeError, ImportError, _Failure):
            # A missing redactor never falls back to consumer diagnostic bytes.
            result, _ = _result(exc.status, exc.code)
        return result, code
    return _result('io_or_shared_unavailable', 2, **fields)


def _name(value, maximum=128):
    if (not isinstance(value, str) or len(value) > maximum
            or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*\.md', value)
            or value.casefold() == 'readme.md'
            or value.split('.')[0].upper() in {'CON', 'PRN', 'AUX', 'NUL'}
            or re.fullmatch(r'(?:COM|LPT)[1-9]', value.split('.')[0].upper())):
        raise _Failure('invalid_filename', 2)
    return value


def _parts(relative):
    if not isinstance(relative, str) or '\\' in relative or ':' in relative:
        raise _Failure('invalid_path', 2)
    parts = relative.split('/')
    if any(not p or p in ('.', '..') or p.endswith((' ', '.')) for p in parts):
        raise _Failure('invalid_path', 2)
    return parts


def _candidate(relative):
    parts = _parts(relative)
    if len(parts) != 5 or '/'.join(parts[:3]) != BASE or parts[3] not in STATES:
        raise _Failure('invalid_candidate', 2)
    _name(parts[4])
    return parts[3]


def _identity(info):
    return [info.st_dev, info.st_ino, stat.S_IFMT(info.st_mode)]


def _parents(root, relative, create=False, *, effects=None):
    target = Path(root).absolute().joinpath(*_parts(relative))
    reader = _module('local-read.py')
    snapshots = []
    for path in list(reversed(target.parent.parents)) + [target.parent]:
        try:
            info = path.lstat()
        except FileNotFoundError:
            if not create:
                raise
            if not reader._unchanged(snapshots):
                raise _Failure('changed_path', 2)
            try:
                # A failed OS call does not prove that creation had no effect.
                if effects is not None and effects['written'] is not True:
                    effects['written'] = None
                _mkdir_private(path)
                if effects is not None:
                    effects['written'] = True
            except FileExistsError:
                pass
            info = path.lstat()
        if reader._redirected(info) or not stat.S_ISDIR(info.st_mode):
            raise _Failure('redirected_path', 2)
        snapshots.append((path, reader._identity(info)))
    if not reader._unchanged(snapshots):
        raise _Failure('changed_path', 2)
    return target, snapshots


def _read(root, relative, maximum=MAX_BYTES, allow_links=False, *, budget=None):
    if budget is not None:
        maximum = min(maximum, budget['remaining'])
        if maximum <= 0:
            raise _Failure('read_budget', 2)
    result = _module('local-read.py').read_bytes(
        root, relative, max_bytes=maximum, include_digest=True, include_identity=True)
    if budget is not None:
        budget['remaining'] -= result['bytes'] if result['status'] == 'ok' else maximum
    if result['status'] != 'ok':
        raise _Failure('read_' + result['status'], 2)
    info = (Path(root) / relative).lstat()
    if _identity(info) != list(result['identity']) or (not allow_links and info.st_nlink != 1):
        raise _Failure('changed_or_hardlinked_file', 2)
    return result


def _text(raw):
    try:
        return raw.decode('utf-8-sig')
    except UnicodeError:
        raise _Failure('invalid_encoding', 2) from None


def _payload(text):
    if not isinstance(text, str) or len(text.encode('utf-8')) > MAX_BYTES:
        raise _Failure('invalid_or_large_payload', 2)
    text = _module('redact.py').redactar(text)
    if len(text.encode('utf-8')) > MAX_BYTES:
        raise _Failure('large_redacted_payload', 2)
    local = _module('knowledge-local.py')
    fm = local._frontmatter(text)
    body = local._FRONTMATTER_RE.sub('', text, count=1)
    if not fm or not body.strip():
        raise _Failure('invalid_candidate_content')
    return text, fm, body


def _walk(root, relative):
    reader = _module('local-read.py')
    todo, found, count = [relative], [], 0
    while todo:
        directory = todo.pop()
        listing = reader.list_names(root, directory, max_entries=MAX_ENTRIES)
        if listing['status'] == 'not_found':
            continue
        if listing['status'] != 'ok' or not listing['complete']:
            raise _Failure('incomplete_inventory', 2)
        for name in listing['names']:
            count += 1
            if count > MAX_ENTRIES:
                raise _Failure('inventory_limit', 2)
            rel = directory + '/' + name
            _parts(rel)
            info = (Path(root) / rel).lstat()
            if reader._redirected(info):
                raise _Failure('redirected_inventory', 2)
            if stat.S_ISDIR(info.st_mode):
                todo.append(rel)
            elif stat.S_ISREG(info.st_mode):
                found.append(rel)
            else:
                raise _Failure('nonregular_inventory', 2)
    return sorted(found)


def _reserved(root, filename, aliases=(), *, owned=()):
    paths = []
    for state in STATES:
        paths.extend(_walk(root, BASE + '/' + state))
    paths.extend(_walk(root, 'docs/knowledge/approved'))
    names = {name.casefold() for name in (filename, *aliases)}
    if any(Path(p).name.casefold() in names and p not in owned for p in paths):
        raise _Failure('name_already_reserved')


@contextmanager
def _locked(root):
    path, snapshots = _parents(root, BASE + '/.curation-lock', create=True)
    fd = os.open(path, os.O_RDWR | os.O_CREAT | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                or _identity(path.lstat()) != _identity(info)
                or not _module('local-read.py')._unchanged(snapshots)):
            raise _Failure('unsafe_lock', 2)
        try:
            if os.name == 'nt':
                import msvcrt
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise _Failure('writer_busy', 2) from None
        yield
    finally:
        os.close(fd)


def _sync_dir(path):
    if os.name != 'nt':
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def _stage(root, relative, raw, *, effects=None):
    path, snapshots = _parents(root, relative, create=True, effects=effects)
    if effects is not None and effects['written'] is not True:
        effects['written'] = None
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    if effects is not None:
        effects['written'] = True
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                or _identity(path.lstat()) != _identity(info)
                or not _module('local-read.py')._unchanged(snapshots)):
            raise _Failure('changed_path_before_write', 2)
        if callable(raw):
            raw = raw(_identity(info))
        with os.fdopen(fd, 'wb') as stream:
            fd = None
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        observed = _read(root, relative, max(MAX_OPERATION_BYTES, len(raw)))
        if observed['sha256'] != _hash(raw):
            raise _Failure('changed_staging', 2)
        return list(observed['identity'])
    finally:
        if fd is not None:
            os.close(fd)


def _unlink_owned(root, relative, identity, digest, allow_links=False):
    observed = _read(root, relative, MAX_OPERATION_BYTES, allow_links)
    if list(observed['identity']) != identity or observed['sha256'] != digest:
        raise _Failure('changed_owned_file')
    path, snapshots = _parents(root, relative)
    if not _module('local-read.py')._unchanged(snapshots):
        raise _Failure('changed_path', 2)
    path.unlink()
    _sync_dir(path.parent)


def _publish_stage(root, staged, target, identity, digest):
    source = _read(root, staged, MAX_OPERATION_BYTES)
    if list(source['identity']) != identity or source['sha256'] != digest:
        raise _Failure('changed_staging')
    target_path, snapshots = _parents(root, target, create=True)
    if not _module('local-read.py')._unchanged(snapshots):
        raise _Failure('changed_path', 2)
    try:
        os.link(Path(root) / staged, target_path, follow_symlinks=False)
    except FileExistsError:
        raise _Failure('destination_exists') from None
    target_read = _read(root, target, MAX_OPERATION_BYTES, allow_links=True)
    if list(target_read['identity']) != identity or target_read['sha256'] != digest:
        raise _Failure('changed_publication', 2)
    _sync_dir(target_path.parent)
    _unlink_owned(root, staged, identity, digest, allow_links=True)


def _create(root, relative, raw):
    staged = str(Path(relative).parent).replace('\\', '/') + '/.curation-' + uuid.uuid4().hex + '.tmp'
    identity = _stage(root, staged, raw)
    _publish_stage(root, staged, relative, identity, _hash(raw))
    return identity


def _prepare_record(root, directory, payload, *, operation=False):
    staged = directory + '/.curation-' + uuid.uuid4().hex + '.tmp'
    prepared = {}

    def serialize(identity):
        record = dict(payload, record_publication={'staged': staged, 'identity': identity})
        if operation:
            record['operation_id'] = _hash(_json(record))
        raw = _json(record)
        if len(raw) > MAX_OPERATION_BYTES:
            raise _Failure('operation_limit', 2)
        prepared.update(record=record, raw=raw)
        return raw

    identity = _stage(root, staged, serialize)
    record = prepared['record']
    return staged, directory + '/' + record['operation_id'] + '.json', identity, record, prepared['raw']


def _settle_record(root, relative, snapshot, record, *, readonly=False, read=None):
    read = read or _read
    publication = record.get('record_publication')
    if not isinstance(publication, dict) or set(publication) != {'staged', 'identity'}:
        raise _Failure('invalid_record_publication', 2)
    staged = publication['staged']
    directory = relative.rsplit('/', 1)[0]
    if (not isinstance(staged, str)
            or not re.fullmatch(re.escape(directory) + r'/\.curation-[a-f0-9]{32}\.tmp', staged)
            or publication['identity'] != list(snapshot['identity'])):
        raise _Failure('invalid_record_publication', 2)
    linked = (Path(root) / relative).lstat().st_nlink
    if not os.path.lexists(Path(root) / staged):
        if linked != 1:
            raise _Failure('foreign_record_hardlink', 2)
        return
    if linked != 2:
        raise _Failure('foreign_record_hardlink', 2)
    stage = read(root, staged, MAX_OPERATION_BYTES, allow_links=True)
    if stage['identity'] != snapshot['identity'] or stage['sha256'] != snapshot['sha256']:
        raise _Failure('foreign_record_staging', 2)
    if not readonly:
        _unlink_owned(root, staged, publication['identity'], snapshot['sha256'], allow_links=True)
        _read(root, relative, MAX_OPERATION_BYTES)


def _policy(root):
    relative = '.claude/knowledge-services/taxonomy.json'
    reader = _module('local-read.py')
    before = reader.read_bytes(root, relative, include_digest=True)
    if before['status'] not in ('ok', 'not_found'):
        raise _Failure('unreadable_taxonomy', 2)
    schema = _module('knowledge-schema.py')
    config, _, _, errors = schema.cargar_taxonomia(str(root))
    if errors:
        raise _Failure('invalid_taxonomy', 2, errors)
    after = reader.read_bytes(root, relative, include_digest=True)
    if before['status'] != after['status'] or before.get('sha256') != after.get('sha256'):
        raise _Failure('changed_taxonomy', 2)
    return config, _hash(_json(config))


def _approved_snapshot(root, config):
    paths = _walk(root, 'docs/knowledge/approved')
    folders = sorted({c['folder'] for c in config['categories']}, key=lambda p: (-p.count('/'), p))
    sources, total = [], 0
    for relative in paths:
        if not relative.lower().endswith('.md') or Path(relative).name.casefold() == 'readme.md':
            continue
        folder = next((f for f in folders if relative.startswith('docs/knowledge/approved/' + f + '/')), None)
        if folder is None:
            continue
        snapshot = _read(root, relative)
        total += snapshot['bytes']
        if total > MAX_SCAN_BYTES:
            raise _Failure('approved_read_limit', 2)
        sources.append((str(Path(root) / relative), folder, _text(snapshot['data'])))
    return sources


def _render(fm, body):
    lines = ['---']
    normalized = {}
    if any(not isinstance(key, str) for key in fm):
        raise _Failure('unrepresentable_metadata')
    for key in sorted(fm):
        value = fm[key]
        if not isinstance(key, str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', key):
            raise _Failure('unrepresentable_metadata')
        if isinstance(value, list):
            if not value or len(value) > 128 or any(not isinstance(v, str) or not v.strip() or '\n' in v or '\r' in v for v in value):
                raise _Failure('unrepresentable_metadata')
            lines.append(key + ':')
            lines.extend('  - ' + v for v in value)
            normalized[key] = value
        else:
            if type(value) is int:
                value = str(value)
            if not isinstance(value, str) or '\n' in value or '\r' in value:
                raise _Failure('unrepresentable_metadata')
            lines.append(key + ': ' + value)
            normalized[key] = value
    rendered = '\n'.join(lines) + '\n---\n' + body
    if _module('knowledge-local.py')._frontmatter(rendered) != normalized:
        raise _Failure('metadata_roundtrip_failed')
    return rendered


def _final(root, candidate, original, config, metadata, replacement):
    text, fm, body = _payload(replacement if replacement is not None else _text(original))
    if not isinstance(metadata, dict):
        raise _Failure('invalid_metadata', 2)
    if metadata.get('estado', 'aprobado') != 'aprobado':
        raise _Failure('invalid_final_state')
    final_version = metadata.get('version', fm.get('version', 1))
    if (type(final_version) is not int and final_version != '1') or str(final_version) != '1':
        raise _Failure('invalid_initial_version')
    original_id = _module('knowledge-local.py')._frontmatter(_text(original)).get('id')
    fm.update(metadata)
    if original_id and fm.get('id') != original_id:
        raise _Failure('changed_declared_id')
    fm.update(version=1, estado='aprobado')
    identifier = fm.get('id')
    if not isinstance(identifier, str) or not identifier.strip():
        raise _Failure('missing_final_id')
    rules = _module('knowledge-curation-rules.py')
    category, errors = rules.validar_categoria(config, fm.get('category'), candidate)
    if errors:
        raise _Failure('invalid_category', 1, errors)
    _, errors, usage = rules.validar_id_override(identifier, fm, config, candidate)
    if usage or errors:
        raise _Failure('invalid_final_id', 1, errors or [usage])
    rendered, fm, body = _payload(_render(fm, body))
    errors = rules.validar_aprobacion(fm, body, category, config, candidate,
                                    _module('knowledge-schema.py').default_taxonomy()['evidence_levels'], 'taxonomy.json')
    target = 'docs/knowledge/approved/' + category['folder'] + '/' + Path(candidate).name
    _parts(target)
    sources = _approved_snapshot(root, config)
    local = _module('knowledge-local.py')
    index, index_errors = local.index_snapshot(sources, config)
    if index_errors:
        raise _Failure('invalid_existing_index', 1, index_errors)
    if identifier in index:
        raise _Failure('id_collision')
    _, final_errors = local.index_snapshot(sources + [(str(Path(root) / target), category['folder'], rendered)], config)
    if errors or final_errors:
        raise _Failure('approval_validation_failed', 1, errors + final_errors)
    return target, rendered.encode('utf-8')


def _checkpoint(stage, operation):
    """No-op boundary used by interruption drills; never a model/tool callback."""


def propose(root, filename, text, *, producer, reserved_aliases=()):
    try:
        _name(filename)
        if not isinstance(reserved_aliases, (list, tuple)) or len(reserved_aliases) > 8:
            raise _Failure('invalid_reserved_aliases', 2)
        for alias in reserved_aliases:
            _name(alias, maximum=255)
        if not isinstance(producer, str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,63}', producer):
            raise _Failure('invalid_producer', 2)
        text, fm, _ = _payload(text)
        if 'estado' in fm:
            raise _Failure('proposal_cannot_declare_estado')
        if 'proposed_by' in fm and fm['proposed_by'] != producer:
            raise _Failure('conflicting_producer_label')
        if 'proposed_by' not in fm:
            text = text.replace('---', '---\nproposed_by: ' + producer, 1)
        _policy(root)
        _reserved(root, filename, reserved_aliases)
        relative = BASE + '/pending/' + filename
        with _locked(root):
            _reserved(root, filename, reserved_aliases)
            _create(root, relative, text.encode('utf-8'))
        return _result('proposed', ruta=relative, sha256=_hash(text.encode('utf-8')))
    except (OSError, ValueError, TypeError, ImportError, _Failure) as exc:
        return _caught(exc)


def _operation_directory(candidate):
    return OPERATIONS + '/' + _hash(candidate.encode('utf-8'))


def _load_operation(root, operation_id, *, relative=None, readonly=False, read=None):
    read = read or _read
    if not isinstance(operation_id, str) or not re.fullmatch(r'[a-f0-9]{64}', operation_id):
        raise _Failure('invalid_operation_id', 2)
    if relative is None:
        matches = [path for path in _walk(root, OPERATIONS)
                   if Path(path).name == operation_id + '.json']
        if len(matches) != 1:
            raise _Failure('operation_not_found' if not matches else 'ambiguous_operation', 2)
        relative = matches[0]
    record = read(root, relative, MAX_OPERATION_BYTES, allow_links=True)
    operation = json.loads(_text(record['data']))
    core = {key: value for key, value in operation.items() if key != 'operation_id'}
    if operation.get('operation_id') != operation_id or _hash(_json(core)) != operation_id:
        raise _Failure('invalid_operation_record', 2)
    _candidate(operation['source'])
    if relative != _operation_directory(operation['source']) + '/' + operation_id + '.json':
        raise _Failure('invalid_operation_location', 2)
    _parts(operation['target'])
    if operation['decision'] not in ('approve', 'reject', 'needs_changes'):
        raise _Failure('invalid_operation_record', 2)
    if operation['decision'] == 'approve':
        if not operation['target'].startswith('docs/knowledge/approved/'):
            raise _Failure('invalid_operation_target', 2)
    elif operation['target'] != BASE + '/' + ('rejected' if operation['decision'] == 'reject' else 'needs_changes') + '/' + Path(operation['source']).name:
        raise _Failure('invalid_operation_target', 2)
    _settle_record(root, relative, record, operation, readonly=readonly, read=read)
    return operation


def _complete(root, operation):
    op_id = operation['operation_id']
    source, target = operation['source'], operation['target']
    source_exists = os.path.lexists(Path(root) / source)
    if source_exists:
        observed = _read(root, source)
        if observed['sha256'] != operation['source_sha256'] or list(observed['identity']) != operation['source_identity']:
            raise _Failure('changed_source')
    target_exists = os.path.lexists(Path(root) / target)
    if not target_exists:
        if not source_exists:
            raise _Failure('source_and_target_unavailable', 2)
        config, policy_hash = _policy(root)
        if policy_hash != operation['policy_sha256']:
            raise _Failure('changed_policy')
        if operation['decision'] == 'approve':
            # Reuse final validation, including the latest complete index, under
            # the cooperative lock. No independent read rederives the candidate.
            final_target, final_raw = _final(root, source, observed['data'], config,
                                             operation['metadata'], operation['replacement'])
            if final_target != target or _hash(final_raw) != operation['target_sha256']:
                raise _Failure('changed_final_representation')
        _publish_stage(root, operation['staged'], target,
                       operation['target_identity'], operation['target_sha256'])
    else:
        existing = _read(root, target, MAX_BYTES, allow_links=True)
        if list(existing['identity']) != operation['target_identity'] or existing['sha256'] != operation['target_sha256']:
            raise _Failure('foreign_or_changed_destination')
        if operation['staged'] and os.path.lexists(Path(root) / operation['staged']):
            _unlink_owned(root, operation['staged'], operation['target_identity'], operation['target_sha256'], allow_links=True)
        elif (Path(root) / target).lstat().st_nlink != 1:
            raise _Failure('hardlinked_destination', 2)
    _checkpoint('published', operation)
    if source != target and source_exists:
        _unlink_owned(root, source, operation['source_identity'], operation['source_sha256'])
    _checkpoint('source_removed', operation)
    receipt_path = RECEIPTS + '/' + op_id + '.json'
    receipt = _json({'operation_id': op_id, 'source': source, 'target': target,
                     'source_sha256': operation['source_sha256'], 'target_sha256': operation['target_sha256'],
                     'status': 'complete'})
    if os.path.lexists(Path(root) / receipt_path):
        snapshot = _read(root, receipt_path, MAX_OPERATION_BYTES, allow_links=True)
        record = json.loads(_text(snapshot['data']))
        if not isinstance(record, dict) or _json({k: v for k, v in record.items() if k != 'record_publication'}) != receipt:
            raise _Failure('changed_receipt', 2)
        _settle_record(root, receipt_path, snapshot, record)
    else:
        staged, relative, identity, _, raw = _prepare_record(root, RECEIPTS, json.loads(receipt))
        _publish_stage(root, staged, relative, identity, _hash(raw))
    return _result('complete', operation_id=op_id, ruta=target, sha256=operation['target_sha256'])


def apply_decision(root, candidate, decision, *, expected_sha256, metadata=None,
                   replacement_text=None, reason, decider='knowledge-curator'):
    operation_id = None
    try:
        state = _candidate(candidate)
        if decider != 'knowledge-curator':
            raise _Failure('invalid_declared_decider', 2)
        if decision not in ('approve', 'reject', 'needs_changes') or (state == 'rejected' and decision != 'reject'):
            raise _Failure('invalid_or_terminal_decision', 2)
        if not isinstance(expected_sha256, str) or not re.fullmatch(r'[a-f0-9]{64}', expected_sha256):
            raise _Failure('invalid_expected_sha256', 2)
        if not isinstance(reason, str) or not reason.strip() or len(reason.encode('utf-8')) > 8192:
            raise _Failure('invalid_reason', 2)
        if replacement_text is not None and decision != 'approve':
            raise _Failure('replacement_only_for_approve', 2)
        reason = _module('redact.py').redactar(reason)
        with _locked(root):
            observed = _read(root, candidate)
            if observed['sha256'] != expected_sha256:
                raise _Failure('changed_source')
            config, policy_hash = _policy(root)
            if decision == 'approve':
                target, raw = _final(root, candidate, observed['data'], config, metadata or {}, replacement_text)
            else:
                target = BASE + '/' + ('rejected' if decision == 'reject' else 'needs_changes') + '/' + Path(candidate).name
                raw = _module('redact.py').redactar(_text(observed['data'])).encode('utf-8')
                if raw != observed['data']:
                    raise _Failure('unredacted_candidate_requires_review')
            operation_directory = _operation_directory(candidate)
            for pending in _walk(root, operation_directory):
                if not pending.endswith('.json'):
                    continue
                prior = _load_operation(root, Path(pending).stem, relative=pending)
                if prior['source'] == candidate and not os.path.lexists(Path(root) / RECEIPTS / (prior['operation_id'] + '.json')):
                    raise _Failure('recover_existing_operation')
            staged = None
            if candidate == target:
                identity = list(observed['identity'])
            else:
                if os.path.lexists(Path(root) / target):
                    raise _Failure('destination_exists')
                staged = str(Path(target).parent).replace('\\', '/') + '/.curation-' + uuid.uuid4().hex + '.tmp'
                identity = _stage(root, staged, raw)
            core = dict(version=1, source=candidate, source_sha256=expected_sha256,
                        source_identity=list(observed['identity']), target=target, target_sha256=_hash(raw),
                        target_identity=identity, staged=staged, decision=decision, reason=reason,
                        decider=decider, policy_sha256=policy_hash,
                        original_redacted=_module('redact.py').redactar(_text(observed['data'])),
                        metadata=_module('redact.py').redactar(json.dumps(metadata or {}, ensure_ascii=False)),
                        replacement=_module('redact.py').redactar(replacement_text) if replacement_text is not None else None)
            # Store only redacted metadata, then bind its exact representation.
            core['metadata'] = json.loads(core['metadata'])
            record_staged, relative, record_identity, operation, record = _prepare_record(root, operation_directory, core, operation=True)
            operation_id = operation['operation_id']
            _publish_stage(root, record_staged, relative, record_identity, _hash(record))
            _checkpoint('prepared', operation)
            return _complete(root, operation)
    except (OSError, ValueError, TypeError, KeyError, ImportError, _Failure) as exc:
        return _caught(exc, **({'operation_id': operation_id} if operation_id else {}))


def recover(root, operation_id, *, decider='knowledge-curator'):
    try:
        if decider != 'knowledge-curator':
            raise _Failure('invalid_declared_decider', 2)
        with _locked(root):
            return _complete(root, _load_operation(root, operation_id))
    except (OSError, ValueError, TypeError, KeyError, ImportError, _Failure) as exc:
        return _caught(exc, operation_id=operation_id)


def inspect_reference(root, candidate, expected_sha256, *, operation_id=None, _budget=None):
    """Observe a ledger-bound candidate; never persist or decide curation."""
    result = {'candidate': candidate, 'expected_sha256': expected_sha256,
              'target_content_verified': False}
    budget = _budget if _budget is not None else {'remaining': MAX_OPERATION_BYTES}
    def read(root, relative, maximum=MAX_BYTES, allow_links=False):
        return _read(root, relative, min(maximum, MAX_BYTES), allow_links, budget=budget)
    def outcome(status, reason):
        return dict(result, status=status, reason=reason)
    try:
        _candidate(candidate)
        if not isinstance(expected_sha256, str) or not re.fullmatch(r'[a-f0-9]{64}', expected_sha256):
            raise _Failure('invalid_expected_sha256', 2)
        if operation_id is not None and (not isinstance(operation_id, str) or not re.fullmatch(r'[a-f0-9]{64}', operation_id)):
            return outcome('corrupt', 'invalid_operation_id')
        try:
            observed = read(root, candidate)
        except _Failure as exc:
            if exc.status != 'read_not_found':
                raise
            observed = None
        if observed is not None and observed['sha256'] != expected_sha256:
            return outcome('changed', 'candidate_changed')
        directory = _operation_directory(candidate)
        if operation_id is not None:
            names = [operation_id + '.json']
        else:
            listing = _module('local-read.py').list_names(root, directory, max_entries=16)
            if listing['status'] == 'not_found':
                names = []
            elif listing['status'] != 'ok' or not listing['complete']:
                return outcome('unknown', listing['status'])
            else:
                names = listing['names']
        matches = []
        for name in names:
            if re.fullmatch(r'\.curation-[a-f0-9]{32}\.tmp', name):
                continue
            if not re.fullmatch(r'[a-f0-9]{64}\.json', name):
                return outcome('unknown', 'corrupt_operation')
            relative = directory + '/' + name
            try:
                operation = _load_operation(root, name[:-5], relative=relative, readonly=True, read=read)
            except _Failure as exc:
                if operation_id is not None and exc.status == 'read_not_found':
                    return outcome('missing', 'operation_missing')
                raise
            if operation['source'] != candidate or operation['source_sha256'] != expected_sha256:
                return outcome('changed', 'association_conflict')
            matches.append((relative, operation))
        if len(matches) > 1:
            return outcome('unknown', 'ambiguous')
        if not matches:
            return outcome('pending' if observed is not None else 'missing',
                           'candidate_observed' if observed is not None else 'candidate_missing')
        relative, operation = matches[0]
        result.update(operation_id=operation['operation_id'], operation_path=relative,
                      target=operation['target'], target_sha256=operation['target_sha256'])
        receipt_relative = RECEIPTS + '/' + operation['operation_id'] + '.json'
        try:
            receipt = read(root, receipt_relative, MAX_OPERATION_BYTES, allow_links=True)
        except _Failure as exc:
            if exc.status == 'read_not_found':
                result['recovery_pending'] = True
                return outcome('pending', 'operation_without_receipt')
            raise
        record = json.loads(_text(receipt['data']))
        expected = dict(operation_id=operation['operation_id'], source=candidate, target=operation['target'],
            source_sha256=expected_sha256, target_sha256=operation['target_sha256'], status='complete')
        if not isinstance(record, dict) or _json({k: v for k, v in record.items() if k != 'record_publication'}) != _json(expected):
            return outcome('corrupt', 'invalid_receipt')
        _settle_record(root, receipt_relative, receipt, record, readonly=True, read=read)
        result.update(receipt_path=receipt_relative, receipt_sha256=receipt['sha256'], recovery_pending=False)
        return outcome('completed', 'completed_receipt_observed')
    except _Failure as exc:
        return outcome('unknown', exc.status if exc.status.startswith('read_') else 'unverifiable_record')
    except (OSError, ValueError, TypeError, KeyError, AttributeError, ImportError, RecursionError):
        return outcome('unknown', 'unverifiable_record')


IMPORT_BASE = BASE + '/.curation/import-v1'
IMPORT_RECEIPTS = IMPORT_BASE + '/receipts'
_IMPORT_INTENT_KEYS = {'schema_version', 'kind', 'request_sha256', 'source_project_id',
    'source_id', 'source_version', 'source_sha256', 'package_sha256', 'destination_project_id',
    'root_identity', 'destination_policy_sha256', 'producer', 'candidate_path',
    'candidate_sha256', 'staged', 'staged_identity', 'operation_id', 'record_publication'}


def _port_index(root, config, budget):
    """Complete bounded snapshot, retaining original bytes for portable integrity."""
    folders = sorted({c['folder'] for c in config['categories']}, key=lambda p: (-p.count('/'), p))
    snapshots, sources = {}, []
    for relative in _walk(root, 'docs/knowledge/approved'):
        if not relative.lower().endswith('.md') or Path(relative).name.casefold() == 'readme.md':
            continue
        folder = next((f for f in folders if relative.startswith('docs/knowledge/approved/' + f + '/')), None)
        if folder is not None:
            snapshot = _read(root, relative, budget=budget)
            absolute = str(Path(root) / relative)
            snapshots[absolute] = (relative, snapshot)
            sources.append((absolute, folder, _text(snapshot['data'])))
    index, errors = _module('knowledge-local.py').index_snapshot(sources, config, include_source=True, root=str(root))
    if errors:
        raise _Failure('invalid_existing_index', 1, errors)
    return index, snapshots


def export_package(root, *, source_id, ids, out, scope_category=None, scope_area=None):
    staged, created_identity, io_started = None, {}, False
    try:
        codec = _module('knowledge-portability.py')
        codec.label(source_id)
        if (not isinstance(ids, (list, tuple)) or not 1 <= len(ids) <= MAX_SCAN_BYTES // MAX_BYTES
                or any(not isinstance(v, str) for v in ids) or len(set(ids)) != len(ids)):
            raise _Failure('invalid_selection')
        if any(v is not None and (not isinstance(v, str) or not v) for v in (scope_category, scope_area)):
            raise _Failure('scope_mismatch')
        parts = _parts(out)
        if (parts[0].casefold() in ('.git', '.claude', '.codex', '.opencode')
                or out.casefold().startswith('docs/knowledge/') or Path(out).name.casefold() == 'tasks.md'):
            raise _Failure('protected_output', 2)
        if os.path.lexists(Path(root) / out):
            raise _Failure('destination_exists')
        config, policy_sha = _policy(root)
        budget = {'remaining': MAX_SCAN_BYTES}
        index, snapshots = _port_index(root, config, budget)
        local = _module('knowledge-local.py')
        rules = _module('knowledge-curation-rules.py')
        entries, selected = [], []
        for identifier in sorted(ids):
            if identifier not in index:
                raise _Failure('invalid_selection')
            record = index[identifier]
            fm = record['frontmatter']
            if any(value is not None and fm.get(key) != value for key, value in
                   (('category', scope_category), ('area', scope_area))):
                raise _Failure('scope_mismatch')
            relative, observed = snapshots[record['ruta']]
            text = _text(observed['data'])
            if _module('redact.py').redactar(text) != text:
                raise _Failure('source_redaction_required')
            category, errors = rules.validar_categoria(config, fm.get('category'), relative)
            if not errors:
                errors = rules.validar_aprobacion(fm, record['cuerpo'], category, config, relative,
                    _module('knowledge-schema.py').default_taxonomy()['evidence_levels'], 'taxonomy.json')
            if errors:
                raise _Failure('source_approval_invalid', 1, errors)
            import base64
            entries.append(dict(id=identifier, version=record['version'], category=fm['category'],
                relative_path=record['ruta_rel'], bytes=len(observed['data']), raw_sha256=observed['sha256'],
                content_base64=base64.b64encode(observed['data']).decode('ascii')))
            selected.append((relative, observed))
        value = dict(schema_version=1, kind='approved_knowledge_export',
            source=dict(project_id=source_id, identity_basis='declared', id_prefix=config['id_prefix'], policy_sha256=policy_sha),
            selection=dict(ids=sorted(ids), scope=dict(category=scope_category, area=scope_area)), entries=entries)
        codec.validate(value, max_bytes=MAX_BYTES, max_entries=MAX_SCAN_BYTES // MAX_BYTES, parse=local._frontmatter)
        raw = codec.canonical(value)
        if len(raw) > MAX_OPERATION_BYTES:
            raise _Failure('package_limit')
        if _policy(root)[1] != policy_sha:
            raise _Failure('changed_taxonomy', 2)
        for relative, previous in selected:
            current = _read(root, relative, budget=budget)
            if current['sha256'] != previous['sha256'] or current['identity'] != previous['identity']:
                raise _Failure('changed_export_source')
        staged = str(Path(out).parent).replace('\\', '/') + '/.curation-' + uuid.uuid4().hex + '.tmp'
        if staged.startswith('./'):
            staged = staged[2:]
        def capture(identity):
            created_identity['value'] = identity
            return raw
        io_started = True
        identity = _stage(root, staged, capture)
        _publish_stage(root, staged, out, identity, _hash(raw))
        return _result('exported', ruta=out, sha256=_hash(raw), written=True)
    except (OSError, ValueError, TypeError, KeyError, ImportError, _Failure) as exc:
        fields = dict(written=True if created_identity else (None if io_started else False), ruta=out)
        if io_started:
            fields.update(staging_path=staged, staging_identity=created_identity.get('value'),
                          sha256=None, output_current='unverified')
            try:
                actual = _read(root, out, MAX_OPERATION_BYTES, allow_links=True)
                if created_identity and list(actual['identity']) == created_identity['value'] and actual['sha256'] == _hash(raw):
                    fields.update(sha256=actual['sha256'], output_current='published_verified')
            except (OSError, ValueError, TypeError, _Failure):
                pass
        return _caught(exc, **fields)


def _import_row(plan):
    return dict(source_id=plan['source_id'], candidate_path=plan['candidate_path'],
        candidate_sha256=plan['candidate_sha256'], destination_id=None, status='not_started',
        candidate_current=None, import_operation_id=None, import_receipt_path=None, import_receipt_sha256=None)


def _import_read_record(root, relative, budget):
    snapshot = _read(root, relative, MAX_OPERATION_BYTES, allow_links=True, budget=budget)
    try:
        record = _module('knowledge-portability.py').json_value(snapshot['data'])
        _module('knowledge-portability.py').record_types(record)
    except ValueError:
        raise _Failure('invalid_import_record', 2) from None
    _settle_record(root, relative, snapshot, record, readonly=True)
    return record, snapshot


def _import_observation(root, relative, identity, digest, other, budget):
    try:
        observed = _read(root, relative, MAX_BYTES, allow_links=True, budget=budget)
    except _Failure as exc:
        if exc.status == 'read_not_found':
            return None
        raise
    if list(observed['identity']) != identity or observed['sha256'] != digest:
        raise _Failure('reservation_conflict')
    linked = (Path(root) / relative).lstat().st_nlink
    if os.path.lexists(Path(root) / other):
        peer = _read(root, other, MAX_BYTES, allow_links=True, budget=budget)
        if linked != 2 or peer['identity'] != observed['identity'] or peer['sha256'] != digest:
            raise _Failure('foreign_import_hardlink', 2)
    elif linked != 1:
        raise _Failure('foreign_import_hardlink', 2)
    return observed


def _import_load(root, plan, budget):
    paths = _walk(root, plan['directory'])
    records = [p for p in paths if p.endswith('.json')]
    if not records:
        if paths:
            raise _Failure('unrecoverable_import', 2)
        return None
    if len(records) != 1:
        raise _Failure('ambiguous_import_intent', 2)
    relative = records[0]
    operation, snapshot = _import_read_record(root, relative, budget)
    if (set(operation) != _IMPORT_INTENT_KEYS
            or _hash(_json({k: v for k, v in operation.items() if k != 'operation_id'})) != operation.get('operation_id')
            or relative != plan['directory'] + '/' + operation['operation_id'] + '.json'
            or any(operation.get(k) != v for k, v in plan['core'].items())
            or not isinstance(operation['staged'], str)
            or not re.fullmatch(re.escape(plan['directory']) + r'/\.proposal-[a-f0-9]{32}\.tmp', operation['staged'])
            or not isinstance(operation['staged_identity'], list) or len(operation['staged_identity']) != 3
            or any(type(v) is not int for v in operation['staged_identity'])):
        raise _Failure('invalid_import_intent', 2)
    receipt_path = IMPORT_RECEIPTS + '/' + operation['operation_id'] + '.json'
    receipt_record = receipt_snapshot = None
    if os.path.lexists(Path(root) / receipt_path):
        receipt_record, receipt_snapshot = _import_read_record(root, receipt_path, budget)
        expected = _import_receipt(operation)
        if {k: v for k, v in receipt_record.items() if k != 'record_publication'} != expected:
            raise _Failure('invalid_import_receipt', 2)
    candidate = _import_observation(root, operation['candidate_path'], operation['staged_identity'],
                                   operation['candidate_sha256'], operation['staged'], budget)
    staged = None
    if candidate is None and receipt_record is None:
        staged = _import_observation(root, operation['staged'], operation['staged_identity'],
                                    operation['candidate_sha256'], operation['candidate_path'], budget)
        if staged is None:
            raise _Failure('unrecoverable_import', 2)
    return dict(operation=operation, operation_path=relative, operation_snapshot=snapshot,
        receipt=receipt_record, receipt_path=receipt_path, receipt_snapshot=receipt_snapshot,
        candidate=candidate, staged=staged)


def _import_receipt(operation):
    return dict(schema_version=1, kind='import_proposal_receipt', status='proposed',
        operation_id=operation['operation_id'], request_sha256=operation['request_sha256'],
        source_id=operation['source_id'], candidate_path=operation['candidate_path'],
        candidate_sha256=operation['candidate_sha256'], candidate_identity=operation['staged_identity'])


def _import_preflight(root, plans, budget):
    states = []
    by_key = {_hash(p['source_id'].encode('utf-8')): p for p in plans}
    # A different policy/label changes the request hash, not the reservation
    # represented by its durable intent. Never bypass an unfinished operation.
    for relative in _walk(root, IMPORT_BASE + '/operations'):
        if not relative.endswith('.json'):
            continue
        key = relative.rsplit('/', 2)[-2]
        plan = by_key.get(key)
        if plan is None or relative.startswith(plan['directory'] + '/'):
            continue
        operation, _ = _import_read_record(root, relative, budget)
        if set(operation) != _IMPORT_INTENT_KEYS:
            raise _Failure('invalid_import_intent', 2)
        binding = {k: operation[k] for k in ('package_sha256', 'destination_project_id',
                                           'root_identity', 'destination_policy_sha256', 'producer')}
        directory = IMPORT_BASE + '/operations/' + operation['request_sha256'] + '/' + _hash(operation['source_id'].encode('utf-8'))
        if (operation['kind'] != 'import_proposal_intent' or operation['producer'] != 'import'
                or _hash(_json(binding)) != operation['request_sha256']
                or _hash(_json({k: v for k, v in operation.items() if k != 'operation_id'})) != operation['operation_id']
                or relative != directory + '/' + operation['operation_id'] + '.json'
                or operation['root_identity'] != _identity(Path(root).lstat())):
            raise _Failure('invalid_import_intent', 2)
        if operation['candidate_path'].casefold() == plan['candidate_path'].casefold():
            raise _Failure('reservation_conflict')
    # Validate owned request records BEFORE generic basename reservations.
    for plan in plans:
        state = _import_load(root, plan, budget)
        if state is None or state['receipt'] is None:
            try:
                owned = (plan['candidate_path'],) if state and state['candidate'] else ()
                _reserved(root, Path(plan['candidate_path']).name, owned=owned)
            except _Failure as exc:
                if exc.status == 'name_already_reserved':
                    raise _Failure('reservation_conflict') from None
                raise
        states.append(state)
    return states


def _import_finish(root, plan, state, row, *, effects):
    if state is None:
        staged = plan['directory'] + '/.proposal-' + uuid.uuid4().hex + '.tmp'
        row['staging_path'] = staged
        identity = _stage(root, staged, plan['raw'], effects=effects)
        row.update(staging_sha256=plan['candidate_sha256'], staging_identity=identity)
        operation = dict(plan['core'], staged=staged, staged_identity=identity)
        _checkpoint('import_stage_prepared', operation)
        record_stage, relative, record_identity, operation, record_raw = _prepare_record(
            root, plan['directory'], operation, operation=True)
        _publish_stage(root, record_stage, relative, record_identity, _hash(record_raw))
        # A durable record is not announced until actually read/verified.
        state = _import_load(root, plan, {'remaining': MAX_OPERATION_BYTES * 4})
        row['import_operation_id'] = operation['operation_id']
        _checkpoint('import_intent_published', dict(operation, import_operation_id=operation['operation_id']))
    operation = state['operation']
    row['import_operation_id'] = operation['operation_id']
    _settle_record(root, state['operation_path'], state['operation_snapshot'], operation)
    if state['receipt'] is not None:
        _settle_record(root, state['receipt_path'], state['receipt_snapshot'], state['receipt'])
        row.update(status='proposed', candidate_current='pending' if state['candidate'] else 'missing_or_moved',
            import_receipt_path=state['receipt_path'], import_receipt_sha256=state['receipt_snapshot']['sha256'])
        return False
    if state['candidate'] is None:
        _publish_stage(root, operation['staged'], operation['candidate_path'], operation['staged_identity'],
                       operation['candidate_sha256'])
    elif os.path.lexists(Path(root) / operation['staged']):
        _unlink_owned(root, operation['staged'], operation['staged_identity'], operation['candidate_sha256'], allow_links=True)
    row['candidate_current'] = 'pending'
    _checkpoint('import_candidate_published', dict(operation, import_operation_id=operation['operation_id']))
    record_stage, relative, identity, _, raw = _prepare_record(root, IMPORT_RECEIPTS, _import_receipt(operation))
    _publish_stage(root, record_stage, relative, identity, _hash(raw))
    record, snapshot = _import_read_record(root, relative, {'remaining': MAX_OPERATION_BYTES * 2})
    if {k: v for k, v in record.items() if k != 'record_publication'} != _import_receipt(operation):
        raise _Failure('invalid_import_receipt', 2)
    row.update(status='proposed', import_receipt_path=relative, import_receipt_sha256=snapshot['sha256'])
    _checkpoint('import_receipt_published', dict(operation, import_operation_id=operation['operation_id']))
    return True


def import_package(root, *, destination_id, package, expected_sha256, check=False):
    rows, written = [], False
    effects = {'written': False}
    try:
        codec = _module('knowledge-portability.py')
        codec.label(destination_id)
        if type(check) is not bool or not isinstance(expected_sha256, str) or not re.fullmatch(r'[a-f0-9]{64}', expected_sha256):
            raise _Failure('invalid_import_arguments', 2)
        _parts(package)
        observed = _read(root, package, MAX_OPERATION_BYTES)
        if observed['sha256'] != expected_sha256:
            raise _Failure('package_integrity')
        local = _module('knowledge-local.py')
        try:
            value = codec.json_value(observed['data'])
            decoded = codec.validate(value, max_bytes=MAX_BYTES, max_entries=MAX_SCAN_BYTES // MAX_BYTES,
                                     parse=local._frontmatter)
        except ValueError:
            raise _Failure('invalid_package') from None
        config, policy_sha = _policy(root)
        budget = {'remaining': MAX_SCAN_BYTES}
        root_identity = _identity(Path(root).lstat())
        binding = dict(package_sha256=expected_sha256, destination_project_id=destination_id,
                       root_identity=root_identity, destination_policy_sha256=policy_sha, producer='import')
        request = _hash(_json(binding))
        plans, warnings = [], []
        rules = _module('knowledge-curation-rules.py')
        for entry, text, fm in decoded:
            category, errors = rules.validar_categoria(config, entry['category'], entry['relative_path'])
            if errors:
                raise _Failure('invalid_destination_category', 1, errors)
            body = local._FRONTMATTER_RE.sub('', text, count=1)
            proposed = codec.proposal(value['source'], entry, fm, body, expected_sha256, _render)
            proposed, proposed_fm, proposed_body = _payload(proposed)
            if any(proposed_fm.get(k) != v for k, v in local._frontmatter(
                    codec.proposal(value['source'], entry, fm, body, expected_sha256, _render)).items()
                    if k.startswith('import_')):
                raise _Failure('redacted_import_provenance')
            filename = 'import-' + _hash(_json([value['source']['project_id'], entry['id']])) + '.md'
            _name(filename)
            candidate = BASE + '/pending/' + filename
            raw = proposed.encode('utf-8')
            core = dict(schema_version=1, kind='import_proposal_intent', request_sha256=request,
                source_project_id=value['source']['project_id'], source_id=entry['id'], source_version=entry['version'],
                source_sha256=entry['raw_sha256'], candidate_path=candidate, candidate_sha256=_hash(raw), **binding)
            plan = dict(core=core, source_id=entry['id'], candidate_path=candidate, candidate_sha256=_hash(raw), raw=raw,
                directory=IMPORT_BASE + '/operations/' + request + '/' + _hash(entry['id'].encode('utf-8')))
            plans.append(plan)
            warnings.extend(rules.validar_aprobacion(proposed_fm, proposed_body, category, config, candidate,
                _module('knowledge-schema.py').default_taxonomy()['evidence_levels'], 'taxonomy.json'))
        rows = [_import_row(p) for p in plans]
        if len(_json(dict(entries=rows, avisos=warnings))) + len(rows) * 1024 > MAX_OPERATION_BYTES:
            raise _Failure('import_response_limit')
        already_locked = os.path.lexists(Path(root) / (BASE + '/.curation-lock'))
        # Existing cooperative writers protect store reads as well as writes.
        # A cold malformed batch still fails before creating lock infrastructure.
        with (_locked(root) if already_locked else nullcontext()):
            _port_index(root, config, budget)
            states = _import_preflight(root, plans, budget)
            if check:
                response, code = _result('checked', entries=rows, complete=True, written=False)
                response['avisos'] = warnings
                return response, code
            with (nullcontext() if already_locked else _locked(root)):
                current = _read(root, package, MAX_OPERATION_BYTES)
                if (current['identity'] != observed['identity'] or current['sha256'] != expected_sha256
                        or _identity(Path(root).lstat()) != root_identity or _policy(root)[1] != policy_sha):
                    raise _Failure('changed_import_inputs', 2)
                _port_index(root, config, budget)
                states = _import_preflight(root, plans, budget)
                for plan, state, row in zip(plans, states, rows):
                    try:
                        written = _import_finish(root, plan, state, row, effects=effects) or written
                    except (OSError, ValueError, TypeError, KeyError, ImportError, _Failure):
                        # Determine actual durable ownership, not success from a hash match.
                        try:
                            proven = _import_load(root, plan, {'remaining': MAX_OPERATION_BYTES * 4})
                        except _Failure as load_error:
                            if load_error.status != 'unrecoverable_import' or row['import_operation_id'] is not None:
                                raise
                            proven = None
                        if proven:
                            row['import_operation_id'] = proven['operation']['operation_id']
                            row['candidate_current'] = 'pending' if proven['candidate'] else None
                            row['status'] = 'persistence_pending'
                            raise _Failure('persistence_pending', 2) from None
                        staged = row.get('staging_path')
                        if staged and os.path.lexists(Path(root) / staged):
                            actual = _read(root, staged, MAX_BYTES)
                            row.update(staging_sha256=actual['sha256'], staging_identity=list(actual['identity']), status='orphan_unrecoverable')
                            raise _Failure('orphan_unrecoverable', 2) from None
                        raise
        response, code = _result('proposed', entries=rows, complete=True, written=written)
        response['avisos'] = warnings
        return response, code
    except (OSError, ValueError, TypeError, KeyError, ImportError, _Failure) as exc:
        observed_write = written or any(row.get('import_operation_id') for row in rows)
        return _caught(exc, entries=rows, complete=False,
                       written=True if observed_write else effects['written'])


def _stdin_text():
    raw = sys.stdin.buffer.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise _Failure('payload_limit', 2)
    return _text(raw)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest='command', required=True)
    proposal = commands.add_parser('propose')
    proposal.add_argument('--filename', required=True)
    proposal.add_argument('--producer', required=True)
    proposal.add_argument('--reserved-alias', action='append', default=[])
    apply = commands.add_parser('apply')
    apply.add_argument('candidate')
    apply.add_argument('--decision', required=True, choices=('approve', 'reject', 'needs_changes'))
    apply.add_argument('--expected-sha256', required=True)
    apply.add_argument('--reason', required=True)
    apply.add_argument('--metadata-json', default='{}')
    apply.add_argument('--replacement-stdin', action='store_true')
    recovery = commands.add_parser('recover')
    recovery.add_argument('operation_id')
    export = commands.add_parser('export')
    export.add_argument('--source-id', required=True)
    export.add_argument('--id', action='append', required=True)
    export.add_argument('--scope-category')
    export.add_argument('--scope-area')
    export.add_argument('--out', required=True)
    import_command = commands.add_parser('import')
    import_command.add_argument('--destination-id', required=True)
    import_command.add_argument('--package', required=True)
    import_command.add_argument('--expected-sha256', required=True)
    import_command.add_argument('--check', action='store_true')
    for subparser in (proposal, apply, recovery, export, import_command):
        subparser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    try:
        if args.command == 'propose':
            result, code = propose(args.root, args.filename, _stdin_text(), producer=args.producer,
                                   reserved_aliases=args.reserved_alias)
        elif args.command == 'apply':
            result, code = apply_decision(args.root, args.candidate, args.decision,
                expected_sha256=args.expected_sha256, metadata=json.loads(args.metadata_json), reason=args.reason,
                replacement_text=_stdin_text() if args.replacement_stdin else None)
        elif args.command == 'export':
            result, code = export_package(args.root, source_id=args.source_id, ids=args.id, out=args.out,
                                         scope_category=args.scope_category, scope_area=args.scope_area)
        elif args.command == 'import':
            result, code = import_package(args.root, destination_id=args.destination_id, package=args.package,
                                         expected_sha256=args.expected_sha256, check=args.check)
        else:
            result, code = recover(args.root, args.operation_id)
    except (OSError, ValueError, TypeError, _Failure) as exc:
        result, code = _caught(exc)
    print(json.dumps(result, ensure_ascii=False))
    return code


if __name__ == '__main__':
    sys.exit(main())
