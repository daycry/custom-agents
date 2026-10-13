"""Durable submit/confirm receipts for asynchronous Graphiti episode creation.

The cooperative lock prevents cooperating callers from submitting the same intent
twice. An unknown acknowledgment remains unknown; this is not exactly-once delivery
or authentication of the server/producer.
"""
import contextlib
import contextvars
import hashlib
import importlib.util
import json
import math
import re
import os
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True
MAX_STATE_BYTES = 256 * 1024
MAX_OPERATIONS = 128
OWNER = {'owner': 'custom-agents.graphiti-submissions', 'schema': 1}
MAX_MANIFEST_BYTES = 8 * 1024 * 1024
_active_publication = contextvars.ContextVar('graphiti_publication_io', default=None)
_helper_modules = {}


def _mkdir_private(path, **kwargs):
    """0o700 en POSIX. En Windows se heredan los permisos del padre: Python 3.13 convierte
    0o700 en una ACL explícita que deja fuera al usuario restringido del sandbox de Codex."""
    if os.name == 'nt':
        path.mkdir(**kwargs)
    else:
        path.mkdir(mode=0o700, **kwargs)


class PublicationError(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise PublicationError(reason)


def _guard(deadline):
    _need(time.monotonic() < deadline, 'publication_budget_exhausted')


def _helper(name):
    if name in _helper_modules:
        return _helper_modules[name]
    path = Path(__file__).resolve().parents[3] / 'agent-kits/shared' / (name + '.py')
    spec = importlib.util.spec_from_file_location('graphiti_publication_' + name.replace('-', '_'), path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except (OSError, ImportError) as error:
        raise PublicationError('publication_shared_helper_unavailable') from error
    _helper_modules[name] = module
    return module


def _encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf8')


def _digest(value):
    return hashlib.sha256(_encoded(value)).hexdigest()


def _submission_error(error):
    kind = type(error).__name__
    if re.fullmatch('[A-Za-z_][A-Za-z0-9_]{0,127}', kind) is None:
        kind = 'Exception'
    text = str(error)
    if len(text) > 4096:
        text = 'detalle del error supera el limite de diagnostico'
    text = ''.join(char if char.isprintable() else ' ' for char in text)
    text = _helper('redact').redactar(text)[:500] or 'sin detalle'
    return {'kind': kind, 'detail': text}


def _decode(raw):
    def pairs(values):
        result = {}
        for key, value in values:
            _need(key not in result, 'duplicate_publication_state_key')
            result[key] = value
        return result
    def invalid_constant(_value):
        raise PublicationError('invalid_publication_state_number')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid_constant)


def _access(cfg):
    reader, state = _helper('local-read'), _helper('local-state')
    timeout = cfg.get('timeout_ms', 3000)
    _need(type(timeout) in (int, float) and math.isfinite(timeout) and timeout > 0, 'invalid_publication_budget')
    deadline = time.monotonic() + max(1.0, timeout / 1000.0) * 4
    io = state.StateIO(reader, _need, _guard, maximum=MAX_STATE_BYTES)
    identity = {'endpoint': cfg.get('endpoint'), 'group_id': cfg.get('group_id')}
    _need(all(type(v) is str and v for v in identity.values()), 'invalid_publication_identity')
    root = Path(cfg.get('_root') or '.').absolute()
    return io, deadline, identity, root


def _state_path(base, identity):
    # A changed endpoint must not silently adopt another pending identity for this group.
    return base / (_digest({'group_id': identity['group_id']}) + '.json')


def _validate_owner(raw):
    marker = _decode(raw)
    _need(type(marker) is dict and marker == OWNER
        and type(marker.get('schema')) is int, 'unowned_publication_state')


def _validate_record(raw, identity):
    record = _decode(raw)
    _need(type(record) is dict and set(record) in ({'schema', 'endpoint', 'group_id', 'operations'}, {'schema', 'endpoint', 'group_id', 'operations', 'relations'})
        and type(record.get('schema')) is int and record['schema'] == 1, 'invalid_publication_state')
    _need(all(record.get(k) == v for k, v in identity.items()), 'publication_identity_changed')
    operations = record.get('operations')
    _need(type(operations) is dict and len(operations) <= MAX_OPERATIONS, 'invalid_publication_state')
    for key, value in operations.items():
        _need(type(value) is dict and value.get('phase') in ('submitting', 'submitted', 'confirmed'), 'invalid_publication_operation')
        fields = {'name', 'body_sha256', 'phase'} | ({'uuid'} if value['phase'] == 'confirmed' else set()) | ({'transition'} if 'transition' in value else set()) | ({'error'} if 'error' in value else set())
        _need(set(value) == fields and type(value['name']) is str and 0 < len(value['name']) <= 512
            and type(value['body_sha256']) is str and re.fullmatch('[a-f0-9]{64}', value['body_sha256']), 'invalid_publication_operation')
        _need(key == _digest({'name': value['name'], 'group_id': identity['group_id']}), 'invalid_publication_operation_identity')
        if value['phase'] == 'confirmed':
            _need(type(value['uuid']) is str and 0 < len(value['uuid']) <= 200, 'invalid_publication_remote_identity')
        if 'transition' in value:
            _validate_transition(value['transition'], value['name'])
        if 'error' in value:
            error = value['error']
            _need(type(error) is dict and set(error) == {'kind', 'detail'}
                and type(error['kind']) is str and re.fullmatch('[A-Za-z_][A-Za-z0-9_]{0,127}', error['kind'])
                and type(error['detail']) is str and 0 < len(error['detail']) <= 500
                and error['detail'].isprintable(), 'invalid_submission_error')
    relations = record.get('relations', {})
    _need(type(relations) is dict and len(relations) + len(operations) <= MAX_OPERATIONS, 'invalid_relation_state')
    for key, value in relations.items():
        _need(type(value) is dict and value.get('phase') in ('submitting', 'acknowledged', 'confirmed'), 'invalid_relation_operation')
        request = value.get('request')
        _validate_relation_request(request, identity['group_id'])
        _need(key == _digest(request), 'invalid_relation_identity')
        fields = {'phase', 'request'} | ({'edge_uuid', 'source_uuid', 'target_uuid'} if value['phase'] != 'submitting' else set())
        _need(set(value) == fields, 'invalid_relation_operation')
        if value['phase'] != 'submitting':
            _need(all(type(value[k]) is str and 0 < len(value[k]) <= 200 for k in ('edge_uuid', 'source_uuid', 'target_uuid')), 'invalid_relation_remote_identity')
    return record


def _validate_transition(value, name):
    _need(type(value) is dict, 'invalid_transition_intent')
    fields = {'id', 'target_version', 'action', 'representation', 'source_ref', 'target_ref', 'source_episode_uuid'}
    fields |= {'replacement_episode_uuid'} if value.get('action') == 'superseded' else set()
    fields |= {'retired_episode'} if 'retired_episode' in value else set()
    _need(set(value) == fields and value.get('action') in ('superseded', 'withdrawn')
          and value.get('representation') in ('episode', 'triplet'), 'invalid_transition_intent')
    id_ = value.get('id');version = value.get('target_version')
    _need(type(id_) is str and 0 < len(id_) <= 400 and id_.isprintable() and '@' not in id_
          and type(version) is int and version > 0, 'invalid_transition_target')
    target = f'{id_}@{version}';prefix = 'custom-agents:knowledge:'
    _need(name == target + '@' + value['action'] and value['target_ref'] == prefix + target,
          'invalid_transition_name_binding')
    source = value['source_ref']
    _need(type(source) is str and 0 < len(source) <= 512, 'invalid_transition_source')
    if value['action'] == 'withdrawn':
        _need(source == prefix + name, 'invalid_transition_source')
    else:
        start = prefix + id_ + '@'
        _need(source.startswith(start) and re.fullmatch('[1-9][0-9]*', source[len(start):])
              and int(source[len(start):]) > version, 'invalid_transition_source')
    for key in ('source_episode_uuid', 'replacement_episode_uuid'):
        if key in value:
            _need(type(value[key]) is str and 0 < len(value[key]) <= 200 and value[key].isprintable(), 'invalid_transition_episode_identity')
    if 'retired_episode' in value:
        retired = value['retired_episode']
        _need(type(retired) is dict and set(retired) == {'name', 'uuid', 'episode_body_sha256'}
              and retired.get('name') == target and retired.get('uuid') == value['source_episode_uuid']
              and type(retired.get('episode_body_sha256')) is str
              and re.fullmatch('[a-f0-9]{64}', retired['episode_body_sha256']), 'invalid_transition_retired_binding')


def _read_state(cfg):
    """Read owned state without creating directories or acquiring a write lock."""
    io, _deadline, identity, root = _access(cfg)
    io.dirs(root)
    parent = root
    for part in ('.claude', 'knowledge-services'):
        parent = parent / part
        if not os.path.lexists(parent):
            return io, parent, None, False
        io.dirs(parent)
    for name in ('graphiti-manifest.json', 'graphiti-manifest.pending.json'):
        path = parent / name
        if os.path.lexists(path):
            io.file(path)
    base = parent / 'graphiti-submissions'
    if not os.path.lexists(base):
        return io, parent, None, False
    io.dirs(base)
    marker = base / '_owner.json'
    _need(os.path.lexists(marker), 'unowned_publication_state')
    raw, _ = io.read(marker, MAX_STATE_BYTES)
    _validate_owner(raw)
    path = _state_path(base, identity)
    if not os.path.lexists(path):
        return io, parent, None, True
    raw, _ = io.read(path, MAX_STATE_BYTES)
    record = _validate_record(raw, identity)
    return io, parent, record, True


def submissions(cfg):
    """Return copied owned episode receipts for pure local planning."""
    _io, _parent, record, _available = _read_state(cfg)
    return [json.loads(_encoded(value)) for value in sorted((record or {}).get('operations', {}).values(), key=lambda value: value['name'])]


def _committed_bindings(published):
    """Episode receipts may be committed as active entries or exact retired identities."""
    bindings = {}
    def bind(name, identity):
        _need(name not in bindings or bindings[name] == identity, 'conflicting_published_binding')
        bindings[name] = identity
    for id_, meta in published.get('entradas', {}).items():
        _need(type(meta) is dict, 'invalid_published_binding')
        bind(f"{id_}@{meta.get('version')}", (meta.get('uuid'), meta.get('episode_body_sha256')))
    transitions = published.get('transitions', {})
    _need(type(transitions) is dict, 'invalid_transition_bindings')
    for name, meta in transitions.items():
        _need(type(meta) is dict, 'invalid_transition_bindings')
        bind(name, (meta.get('uuid'), meta.get('episode_body_sha256')))
        if 'retired_episode' in meta:
            retired = meta['retired_episode']
            _need(type(retired) is dict and set(retired) == {'name', 'uuid', 'episode_body_sha256'}
                and all(type(value) is str and value for value in retired.values())
                and name in (retired['name'] + '@withdrawn', retired['name'] + '@superseded')
                and re.fullmatch('[a-f0-9]{64}', retired['episode_body_sha256']), 'invalid_retired_binding')
            bind(retired['name'], (retired['uuid'], retired['episode_body_sha256']))
    return bindings


def observe(cfg):
    """Read-only receipt status; no directories, lock, network or recovery."""
    io, parent, record, available = _read_state(cfg)
    if record is None:
        return {'unconfirmed': 0, 'confirmed': 0, 'available': available}
    identity = {'endpoint': cfg.get('endpoint'), 'group_id': cfg.get('group_id')}
    operations = list(record['operations'].values())
    relations = list(record.get('relations', {}).values())
    confirmed = [value for value in operations if value['phase'] == 'confirmed']
    committed = {}
    committed_edges = set()
    if (confirmed or relations) and os.path.lexists(parent / 'graphiti-manifest.json'):
        raw, _ = io.read(parent / 'graphiti-manifest.json', MAX_MANIFEST_BYTES)
        published = _decode(raw)
        _need(type(published) is dict and published.get('group_id') == identity['group_id']
            and type(published.get('entradas')) is dict, 'invalid_published_binding')
        committed = _committed_bindings(published)
        for meta in published.get('transitions', {}).values():
            if meta.get('edge_uuid'):
                committed_edges.add(meta['edge_uuid'])
    uncommitted = sum(committed.get(value['name']) != (value['uuid'], value['body_sha256']) for value in confirmed)
    uncommitted += sum(value['phase'] == 'confirmed' and value['edge_uuid'] not in committed_edges for value in relations)
    return {'unconfirmed': sum(value['phase'] != 'confirmed' for value in operations) + sum(value['phase'] != 'confirmed' for value in relations),
            'uncommitted': uncommitted, 'confirmed': len(confirmed), 'available': True}


@contextlib.contextmanager
def _journal(cfg):
    io, deadline, identity, root = _access(cfg)
    io.dirs(root)
    parent = root
    for part in ('.claude', 'knowledge-services'):
        path = parent / part
        io.dirs(parent)
        _mkdir_private(path, exist_ok=True)
        io.dirs(path)
        parent = path
    base = parent / 'graphiti-submissions'
    marker = base / '_owner.json'
    created = False
    try:
        _mkdir_private(base)
        created = True
    except FileExistsError:
        pass
    io.dirs(base)
    if created:
        io.write(marker, _encoded(OWNER), deadline)
    else:
        _need(os.path.lexists(marker), 'unowned_publication_state')
        raw, _ = io.read(marker, MAX_STATE_BYTES)
        _validate_owner(raw)
    path = _state_path(base, identity)
    with io.locked(base, deadline, initialize=True):
        if os.path.lexists(path):
            raw, _ = io.read(path, MAX_STATE_BYTES)
            record = _validate_record(raw, identity)
        else:
            record = {'schema': 1, **identity, 'operations': {}}
        def write():
            _guard(deadline)
            expected = io.file(path) if os.path.lexists(path) else None
            io.write(path, _encoded(record), deadline, expected=expected)
        yield record, write, deadline, io


@contextlib.contextmanager
def session(cfg):
    """Validate legacy leaves and serialize publication through its final commit."""
    with _journal(cfg) as context:
        io = context[3]
        parent = Path(cfg.get('_root') or '.').absolute() / '.claude/knowledge-services'
        for name in ('graphiti-manifest.json', 'graphiti-manifest.pending.json'):
            path = parent / name
            if os.path.lexists(path):
                io.file(path)
        token = _active_publication.set((Path(cfg.get('_root') or '.').absolute(), context))
        try:
            yield context
        finally:
            _active_publication.reset(token)


def write_manifest(cfg, path, raw):
    """Use the shared guarded writer, preserving an active publication's deadline."""
    root = Path(cfg.get('_root') or '.').absolute()
    path = Path(path).absolute()
    _need(path.parent == root / '.claude/knowledge-services', 'foreign_manifest_path')
    active = _active_publication.get()
    if active is not None:
        _need(active[0] == root and active[1][0]['group_id'] == cfg.get('group_id')
              and active[1][0]['endpoint'] == cfg.get('endpoint'), 'foreign_publication_context')
        deadline, existing = active[1][2], active[1][3]
        io = type(existing)(existing.reader, _need, _guard, maximum=MAX_MANIFEST_BYTES, sync=existing.sync)
    else:
        reader, state = _helper('local-read'), _helper('local-state')
        timeout = cfg.get('timeout_ms', 3000)
        _need(type(timeout) in (int,float) and math.isfinite(timeout) and timeout > 0, 'invalid_publication_budget')
        deadline = time.monotonic() + max(1.0, timeout / 1000.0) * 4
        io = state.StateIO(reader, _need, _guard, maximum=MAX_MANIFEST_BYTES)
    io.dirs(root)
    parent = root
    for part in ('.claude', 'knowledge-services'):
        parent = parent / part
        if not os.path.lexists(parent):
            io.dirs(parent.parent)
            _mkdir_private(parent)
        io.dirs(parent)
    expected = io.file(path) if os.path.lexists(path) else None
    io.write(path, raw, deadline, expected=expected)


def _find(client, decode, cfg, episode, deadline, expected_uuid=None, expected_hash=None, return_record=False):
    maximum = cfg.get('max_episodes', 5000)
    _need(type(maximum) is int and maximum > 0, 'invalid_publication_window')
    limit = min(50, maximum)
    for _ in range(6):
        _guard(deadline)
        response = decode(client.tools_call('get_episodes', {'group_ids': [episode['group_id']], 'max_episodes': limit}))
        values = response.get('episodes') if type(response) is dict else response
        _need(type(values) is list and len(values) <= limit, 'invalid_episode_window')
        matches = []
        for value in values:
            _need(type(value) is dict and value.get('group_id') == episode['group_id'], 'foreign_or_unbound_episode')
            if value.get('name') != episode['name']:
                continue
            matches.append(value)
        _need(len(matches) <= 1, 'ambiguous_remote_episode')
        if matches:
            value = matches[0]
            uid = value.get('uuid')
            _need(type(uid) is str and 0 < len(uid) <= 200, 'missing_remote_episode_identity')
            _need(expected_uuid is None or uid == expected_uuid, 'changed_remote_episode_identity')
            content = value.get('content', value.get('episode_body'))
            body_hash = expected_hash or hashlib.sha256(episode['episode_body'].encode('utf8')).hexdigest()
            _need(type(content) is str and hashlib.sha256(content.encode('utf8')).hexdigest()
                == body_hash, 'conflicting_remote_episode_content')
            for key in ('source', 'source_description'):
                _need(key not in episode or key not in value or value[key] == episode[key], 'conflicting_remote_episode_source')
            if expected_uuid is not None or len(values) < limit:
                return dict(value) if return_record else uid
        if len(values) < limit:
            return None
        _need(limit < maximum, 'publication_window_incomplete')
        limit = min(limit * 4, maximum)
    raise PublicationError('publication_window_incomplete')


def publish(cfg, episode, client, decode, known_uuid=None, publication_session=None, transition=None):
    """Create without a client UUID; return only a verified actual remote UUID."""
    _need(type(episode) is dict and 'uuid' not in episode, 'new_episode_must_not_supply_uuid')
    for field in ('name', 'episode_body', 'group_id', 'source', 'source_description'):
        _need(type(episode.get(field)) is str and bool(episode[field]), 'invalid_episode_submission')
    _need(episode['group_id'] == cfg.get('group_id'), 'foreign_episode_submission')
    if transition is not None:
        _validate_transition(transition, episode['name'])
    body_hash = hashlib.sha256(episode['episode_body'].encode('utf8')).hexdigest()
    key = _digest({'name': episode['name'], 'group_id': episode['group_id']})
    context = session(cfg) if publication_session is None else contextlib.nullcontext(publication_session)
    with context as (record, write, deadline, _io):
        operations = record['operations']
        previous = operations.get(key)
        if previous is not None:
            _need(type(previous) is dict and previous.get('name') == episode['name']
                and previous.get('body_sha256') == body_hash
                and previous.get('phase') in ('submitting', 'submitted', 'confirmed'), 'invalid_publication_operation')
            _need(previous.get('transition') == transition, 'changed_transition_intent')
        intent = {'transition': json.loads(_encoded(transition))} if transition is not None else {}
        expected_uuid = previous.get('uuid') if previous and previous['phase'] == 'confirmed' else known_uuid
        uid = _find(client, decode, cfg, episode, deadline, expected_uuid)
        if uid:
            _need(previous is not None or len(operations) + len(record.get('relations', {})) < MAX_OPERATIONS, 'publication_operation_budget')
            operations[key] = {'name': episode['name'], 'body_sha256': body_hash, 'phase': 'confirmed', 'uuid': uid, **intent}
            write()
            return uid
        if previous is not None:
            detail = previous.get('error')
            original = ': ' + detail['kind'] + ': ' + detail['detail'] if detail else ''
            raise PublicationError('pending_confirmation: observe the existing submission; no automatic resend' + original)
        _need(known_uuid is None, 'confirmed_episode_missing')
        _need(len(operations) + len(record.get('relations', {})) < MAX_OPERATIONS, 'publication_operation_budget')
        operations[key] = {'name': episode['name'], 'body_sha256': body_hash, 'phase': 'submitting', **intent}
        write()  # Durably record uncertainty before crossing the network boundary.
        try:
            response = decode(client.tools_call('add_memory', episode))
            _need(type(response) is dict and type(response.get('message')) is str and response['message'], 'unknown_submission_acknowledgment')
        except Exception as error:
            operations[key]['error'] = _submission_error(error)
            write()
            raise
        operations[key]['phase'] = 'submitted'
        write()
        uid = _find(client, decode, cfg, episode, deadline)
        if uid is None:
            raise PublicationError('pending_confirmation: episode queued but not yet verified')
        operations[key].update(phase='confirmed', uuid=uid)
        write()
        return uid


def receipt(publication_session, name, remote_uuid):
    record = publication_session[0]
    key = _digest({'name': name, 'group_id': record['group_id']})
    value = record['operations'].get(key)
    _need(type(value) is dict and value.get('phase') == 'confirmed'
        and value.get('uuid') == remote_uuid, 'missing_confirmed_receipt')
    return json.loads(_encoded(value))


def confirm_existing(cfg, name, body_hash, client, decode, publication_session, include_content=False):
    """Resolve only an owned submission receipt; never recreate a missing episode."""
    record, write, deadline, _io = publication_session
    key = _digest({'name': name, 'group_id': record['group_id']})
    previous = record['operations'].get(key)
    _need(type(previous) is dict and previous['name'] == name and previous['body_sha256'] == body_hash,
          'missing_or_changed_owned_submission')
    expected_uuid = previous.get('uuid') if previous['phase'] == 'confirmed' else None
    value = _find(client, decode, cfg, {'name': name, 'group_id': record['group_id']},
                  deadline, expected_uuid=expected_uuid, expected_hash=body_hash, return_record=True)
    _need(value is not None, 'pending_confirmation: withdrawn submission has not been observed; no resend')
    previous.update(phase='confirmed', uuid=value['uuid'])
    write()
    result = json.loads(_encoded(previous))
    if include_content:
        result['remote_content'] = value.get('content', value.get('episode_body'))
    return result


def prune_confirmed(cfg, published, publication_session=None, transitions=None):
    """Only retire receipts already represented by an exact published identity."""
    transitions = transitions or {}
    names = _committed_bindings({'entradas': published, 'transitions': transitions})
    context = session(cfg) if publication_session is None else contextlib.nullcontext(publication_session)
    with context as (record, write, _deadline, _io):
        old = record['operations']
        retained = {key: value for key, value in old.items() if not (type(value) is dict
            and value.get('phase') == 'confirmed' and value.get('uuid')
            and names.get(value.get('name')) == (value['uuid'], value.get('body_sha256')))}
        edges = {meta.get('edge_uuid') for meta in transitions.values() if meta.get('edge_uuid')}
        links = record.get('relations', {})
        retained_links = {key: value for key, value in links.items() if not (value['phase'] == 'confirmed' and value['edge_uuid'] in edges)}
        if retained != old or retained_links != links:
            record['operations'] = retained
            if 'relations' in record:
                record['relations'] = retained_links
            write()


def _validate_relation_request(request, group_id):
    fields = {'source_node_name', 'target_node_name', 'edge_name', 'fact', 'group_id'}
    _need(type(request) is dict and set(request) == fields
        and all(type(value) is str and 0 < len(value) <= 2048 for value in request.values())
        and request['group_id'] == group_id, 'invalid_relation_request')


def _relation_identity(request, nodes, edges, expected=None):
    _need(type(nodes) is list and type(edges) is list, 'invalid_relation_response')
    pair = []
    for field in ('source_node_name', 'target_node_name'):
        matches = [value for value in nodes if type(value) is dict and value.get('name') == request[field]
                   and value.get('group_id') == request['group_id'] and 'Entity' in value.get('labels', [])]
        _need(len(matches) <= 1, 'ambiguous_relation_entity')
        if not matches:
            return None
        _need(type(matches[0].get('uuid')) is str and 0 < len(matches[0]['uuid']) <= 200, 'invalid_relation_entity_uuid')
        pair.append(matches[0]['uuid'])
    matching = [value for value in edges if type(value) is dict and value.get('group_id') == request['group_id']
        and value.get('name') == request['edge_name'] and value.get('fact') == request['fact']
        and value.get('source_node_uuid') == pair[0] and value.get('target_node_uuid') == pair[1]
        and not value.get('invalid_at') and not value.get('expired_at')]
    if expected:
        matching = [value for value in matching if value.get('uuid') == expected['edge_uuid']]
        _need(pair == [expected['source_uuid'], expected['target_uuid']], 'changed_relation_entities')
    _need(len(matching) <= 1, 'ambiguous_relation_edge')
    if not matching:
        return None
    uid = matching[0].get('uuid')
    _need(type(uid) is str and 0 < len(uid) <= 200, 'invalid_relation_edge_uuid')
    return {'edge_uuid': uid, 'source_uuid': pair[0], 'target_uuid': pair[1]}


def _observe_relation(client, decode, request, deadline, expected=None):
    nodes = {}
    for field in ('source_node_name', 'target_node_name'):
        _guard(deadline)
        result = decode(client.tools_call('search_nodes', {'query': request[field], 'group_ids': [request['group_id']], 'max_nodes': 50}))
        values = result.get('nodes') if type(result) is dict else None
        _need(type(values) is list and len(values) < 50, 'relation_entity_window_incomplete')
        for value in values:
            _need(type(value) is dict and value.get('group_id') == request['group_id'], 'foreign_relation_entity')
            if value.get('name') == request[field]:
                uid = value.get('uuid')
                if uid in nodes:
                    _need(nodes[uid] == value, 'changed_relation_entity_observation')
                nodes[uid] = value
    _guard(deadline)
    result = decode(client.tools_call('search_memory_facts', {'query': request['fact'], 'group_ids': [request['group_id']], 'max_facts': 50}))
    edges = result.get('facts') if type(result) is dict else None
    _need(type(edges) is list and len(edges) < 50, 'relation_edge_window_incomplete')
    _need(all(type(value) is dict and value.get('group_id') == request['group_id'] for value in edges), 'foreign_relation_edge')
    return _relation_identity(request, list(nodes.values()), edges, expected)


def link(cfg, request, client, decode, publication_session):
    """Bind a verified Entity-to-Entity edge without assigning episode UUIDs to it."""
    _validate_relation_request(request, cfg.get('group_id'))
    record, write, deadline, _io = publication_session
    relations = record.setdefault('relations', {})
    key = _digest(request)
    previous = relations.get(key)
    expected = previous if previous and previous['phase'] != 'submitting' else None
    identity = _observe_relation(client, decode, request, deadline, expected)
    if identity:
        _need(previous is not None or len(relations) + len(record['operations']) < MAX_OPERATIONS, 'publication_operation_budget')
        relations[key] = {'phase': 'confirmed', 'request': dict(request), **identity}
        write()
        return dict(identity)
    if previous:
        raise PublicationError('relation_confirmation_pending: observe the existing request; no automatic resend')
    _need(len(relations) + len(record['operations']) < MAX_OPERATIONS, 'publication_operation_budget')
    relations[key] = {'phase': 'submitting', 'request': dict(request)}
    write()
    result = decode(client.tools_call('add_triplet', request))
    _need(type(result) is dict, 'invalid_relation_response')
    identity = _relation_identity(request, result.get('nodes'), result.get('edges'))
    _need(identity is not None, 'unbound_relation_acknowledgment')
    relations[key].update(phase='acknowledged', **identity)
    write()
    verified = _observe_relation(client, decode, request, deadline, identity)
    _need(verified is not None, 'relation_confirmation_pending')
    relations[key].update(phase='confirmed', **verified)
    write()
    return dict(verified)
