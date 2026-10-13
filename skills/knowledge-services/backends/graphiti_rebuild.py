"""Resumable generation construction with one verified publication switch.

The previous physical group is retained. No clear_graph request is issued. This
cooperative protocol cannot authenticate remote writers or cancel queued jobs.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import re
from types import SimpleNamespace
import uuid


OWNER = 'custom-agents.graphiti-rebuild'
STATE_FIELDS = {'owner', 'schema', 'endpoint', 'logical_group_id', 'group_id',
                'previous_group_id', 'nonce', 'baseline_sha256', 'request_sha256',
                'config_sha256', 'phase', 'original_manifest', 'snapshot',
                'restored', 'transitions', 'seeded', 'candidate', 'candidate_snapshot'}


def _mkdir_private(path, **kwargs):
    """0o700 on POSIX. On Windows the parent permissions are inherited: Python 3.13 turns
    0o700 into an explicit ACL that locks out the restricted Codex sandbox user."""
    if os.name == 'nt':
        path.mkdir(**kwargs)
    else:
        path.mkdir(mode=0o700, **kwargs)


class GenerationError(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise GenerationError(reason)


def _encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':'), allow_nan=False).encode('utf8')


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _request(entries, api):
    _need(type(entries) in (list, tuple), 'rebuild_invalid_corpus')
    result, ids = copy.deepcopy(entries), set()
    for entry in result:
        _need(type(entry) is dict, 'rebuild_invalid_entry')
        api._nombre_episodio(entry.get('id'), entry.get('version'))
        _need(entry['id'] not in ids, 'rebuild_duplicate_entry')
        _need(type(entry.get('cuerpo', '')) is str, 'rebuild_invalid_body')
        entry.setdefault('cuerpo', '')
        ids.add(entry['id'])
    return sorted(result, key=lambda entry: entry['id'])


def _configuration_hash(cfg):
    return _sha(_encoded({key: value for key, value in cfg.items()
                          if key not in ('_root', '_logical_group_id', 'group_id')}))


def _read(io, path, maximum, api):
    if not os.path.lexists(path):
        return {}, b''
    raw, _ = io.read(path, maximum)
    value = api._gpub._decode(raw)
    _need(type(value) is dict, 'rebuild_invalid_state')
    return value, raw


def _write(io, path, value, deadline):
    expected = io.file(path) if os.path.lexists(path) else None
    io.write(path, _encoded(value), deadline, expected=expected)


def _validate_snapshot(rows, manifest, api):
    _need(type(rows) is list and type(manifest) is dict
          and type(manifest.get('entradas', {})) is dict
          and type(manifest.get('transitions', {})) is dict, 'rebuild_invalid_snapshot')
    api._history_bindings(manifest.get('transitions', {}))
    bindings = api._gpub._committed_bindings(manifest)
    marker_names = set(manifest.get('transitions', {}))
    hashes = {}
    for row in rows:
        _need(type(row) is dict and set(row) == {'payload', 'original_uuid', 'body_sha256'},
              'rebuild_invalid_snapshot_episode')
        payload = row['payload']
        _need(type(payload) is dict and set(payload) == {'name', 'episode_body', 'source', 'source_description'}
              and all(type(value) is str and value for value in payload.values()),
              'rebuild_invalid_snapshot_payload')
        name = payload['name']
        _need(name not in hashes and re.fullmatch(r'.+@[1-9][0-9]*', name)
              and type(row['original_uuid']) is str and row['original_uuid']
              and row['body_sha256'] == _sha(payload['episode_body'].encode('utf8')),
              'rebuild_invalid_snapshot_identity')
        expected = bindings.get(name)
        _need(expected is not None and expected[0] == row['original_uuid']
              and expected[1] in (None, row['body_sha256']), 'rebuild_snapshot_binding_changed')
        hashes[name] = row['body_sha256']
    _need(set(hashes) == set(bindings) - marker_names, 'rebuild_snapshot_history_incomplete')
    return hashes, marker_names


def _validate(record, cfg, api):
    _need(set(record) == STATE_FIELDS and record.get('owner') == OWNER
          and type(record.get('schema')) is int and record['schema'] == 1,
          'rebuild_unowned_or_invalid_state')
    logical = cfg['_logical_group_id']
    _need(record['endpoint'] == cfg['endpoint'] and record['logical_group_id'] == logical,
          'rebuild_identity_changed')
    _need(record['group_id'] == api._gscope.generation_group(logical, record['nonce'])
          and api._gscope._owned_group(logical, record['previous_group_id']),
          'rebuild_foreign_generation')
    _need(record['phase'] in ('building', 'ready', 'committed')
          and type(record['seeded']) is bool, 'rebuild_invalid_phase')
    for key in ('baseline_sha256', 'request_sha256', 'config_sha256'):
        _need(type(record[key]) is str and re.fullmatch('[a-f0-9]{64}', record[key]),
              'rebuild_invalid_binding')
    _need(type(record['original_manifest']) is dict and type(record['snapshot']) is list
          and type(record['restored']) is dict and type(record['transitions']) is dict,
          'rebuild_invalid_snapshot')
    hashes, marker_names = _validate_snapshot(record['snapshot'], record['original_manifest'], api)
    names = set(hashes)
    _need(set(record['restored']) <= names, 'rebuild_unbound_restore_progress')
    for name, meta in record['restored'].items():
        _need(type(meta) is dict and set(meta) == {'uuid', 'episode_body_sha256'}
              and type(meta['uuid']) is str and 0 < len(meta['uuid']) <= 200
              and type(meta['episode_body_sha256']) is str
              and re.fullmatch('[a-f0-9]{64}', meta['episode_body_sha256']),
              'rebuild_invalid_restore_progress')
        expected = hashes[name]
        _need(meta['episode_body_sha256'] == expected, 'rebuild_changed_restore_body')
    api._history_bindings(record['transitions'])
    _need(set(record['transitions']) <= marker_names,
          'rebuild_unbound_transition_progress')
    if record['seeded']:
        _need(set(record['restored']) == names and set(record['transitions']) == marker_names,
              'rebuild_seed_progress_incomplete')
    candidate = record['candidate']
    _need(candidate is None or (type(candidate) is dict
          and candidate.get('group_id') == record['group_id']
          and candidate.get('logical_group_id') == logical), 'rebuild_invalid_candidate')
    _need(record['phase'] == 'building' or candidate is not None, 'rebuild_missing_candidate')
    if candidate is not None:
        _retained_history(candidate, record)
        _validate_snapshot(record['candidate_snapshot'], candidate, api)
    else:
        _need(record['candidate_snapshot'] is None, 'rebuild_unbound_candidate_snapshot')


def _retained_history(manifest, record):
    _need(type(manifest.get('transitions', {})) is dict, 'rebuild_invalid_candidate_history')
    _need(all(manifest.get('transitions', {}).get(name) == meta
              for name, meta in record['transitions'].items()), 'rebuild_preserved_history_changed')


def _window(client, cfg, api):
    maximum = api._max_episodios_verify(cfg)
    limit = min(50, maximum)
    for _ in range(6):
        result = api._contenido_tool_call(client.tools_call(
            'get_episodes', {'group_ids': [cfg['group_id']], 'max_episodes': limit}))
        values = result.get('episodes') if type(result) is dict else result
        _need(type(values) is list and len(values) <= limit, 'rebuild_invalid_remote_window')
        _need(all(type(row) is dict and row.get('group_id') == cfg['group_id'] for row in values),
              'rebuild_foreign_remote_scope')
        if len(values) < limit:
            return values
        _need(limit < maximum, 'rebuild_remote_window_incomplete')
        limit = min(limit * 4, maximum)
    raise GenerationError('rebuild_remote_window_incomplete')


def _local_episode(name, meta, entries, cfg, api):
    id_, version = name.rsplit('@', 1)
    entry = next((value for value in entries if value['id'] == id_ and value['version'] == int(version)), None)
    _need(entry is not None and meta.get('hash') == _sha(entry['cuerpo'].encode('utf8')),
          'rebuild_missing_remote_history_or_canonical_source')
    op = next(value for value in api.plan([entry], cfg, force=True) if value['tipo'] == 'upsert')
    episode, _warning = api._episodio_upsert(cfg['group_id'], op, cfg)
    provider_cfg = cfg.get('provider') or {}
    provider = api._gp.resolver_proveedor(provider_cfg.get('llm') or 'none')
    generated = provider(provider_cfg, episode)
    api._validar_episodio_del_proveedor(generated, episode)
    _need(meta.get('episode_body_sha256') == _sha(generated['episode_body'].encode('utf8')),
          'rebuild_canonical_source_does_not_match_published_body')
    return {'name': name, 'uuid': meta['uuid'], 'content': generated['episode_body'],
            'source': generated['source'], 'source_description': generated['source_description']}


def _snapshot(manifest, entries, cfg, client, api, backup=None):
    _need(not manifest or manifest.get('group_id') == cfg['group_id'], 'rebuild_manifest_scope_changed')
    active = manifest.get('entradas', {})
    _need(type(active) is dict, 'rebuild_invalid_published_entries')
    historical = api._history_bindings(manifest.get('transitions', {}))
    expected = {f"{id_}@{meta.get('version')}": meta for id_, meta in active.items()}
    for name, meta in historical.items():
        if name in expected:
            _need((expected[name].get('uuid'), expected[name].get('episode_body_sha256'))
                  == (meta['uuid'], meta['episode_body_sha256']), 'rebuild_conflicting_history')
        expected[name] = meta
    for meta in manifest.get('transitions', {}).values():
        refs = [(meta['target_ref'], meta['source_episode_uuid'])]
        if meta['action'] == 'superseded':
            refs.append((meta['source_ref'], meta['replacement_episode_uuid']))
        for ref, uid in refs:
            name = ref[len('custom-agents:knowledge:'):]
            _need(name in expected and expected[name].get('uuid') == uid,
                  'rebuild_unbound_historical_episode')
    remote = {}
    identities = set()
    for row in _window(client, cfg, api):
        name, uid = row.get('name'), row.get('uuid')
        _need(type(name) is str and name in expected and name not in remote
              and type(uid) is str and uid and uid not in identities,
              'rebuild_untracked_or_ambiguous_remote_episode')
        remote[name] = row
        identities.add(uid)
    data = []
    transitions = manifest.get('transitions', {})
    for name, meta in sorted(expected.items()):
        row = remote.get(name)
        if row is None:
            row = next(({'name': name, 'uuid': meta['uuid'], 'content': saved['payload']['episode_body'],
                         'source': saved['payload']['source'], 'source_description': saved['payload']['source_description']}
                        for saved in (backup or []) if saved['payload']['name'] == name
                        and saved['original_uuid'] == meta.get('uuid')
                        and saved['body_sha256'] == meta.get('episode_body_sha256')), None)
        if row is None and name in transitions:
            row = {'name': name, 'uuid': meta['uuid'], 'content': api._transition_body(transitions[name]),
                   'source': 'text', 'source_description': 'custom-agents:graphiti-memory'}
        if row is None:
            id_ = name.rsplit('@', 1)[0]
            _need(name not in transitions and id_ in active
                  and name == f"{id_}@{active[id_].get('version')}",
                  'rebuild_missing_remote_history')
            row = _local_episode(name, active[id_], entries, cfg, api)
        content = row.get('content', row.get('episode_body'))
        _need(row.get('uuid') == meta.get('uuid') and type(content) is str and content,
              'rebuild_changed_remote_episode')
        body_hash = _sha(content.encode('utf8'))
        _need(meta.get('episode_body_sha256') in (None, body_hash), 'rebuild_changed_remote_content')
        if name in transitions:
            _need(content == api._transition_body(transitions[name]), 'rebuild_changed_remote_marker')
            continue
        payload = {'name': name, 'episode_body': content,
                   'source': row.get('source'), 'source_description': row.get('source_description')}
        _need(all(type(value) is str and value for value in payload.values()), 'rebuild_missing_episode_provenance')
        data.append({'payload': payload, 'original_uuid': row['uuid'], 'body_sha256': body_hash})
    return data


def _stage_root(root, record, io, deadline, api):
    parent = root / '.claude/knowledge-services/graphiti-generations'
    if not os.path.lexists(parent):
        _mkdir_private(parent)
    io.dirs(parent)
    folder = parent / record['nonce']
    marker = folder / '_owner.json'
    identity = {'owner': OWNER, 'schema': 1, 'endpoint': record['endpoint'],
                'logical_group_id': record['logical_group_id'], 'group_id': record['group_id']}
    if not os.path.lexists(folder):
        _mkdir_private(folder)
        io.dirs(folder)
        _write(io, marker, identity, deadline)
    else:
        io.dirs(folder)
        current, _raw = _read(io, marker, api._gpub.MAX_STATE_BYTES, api)
        _need(current == identity and type(current.get('schema')) is int, 'rebuild_unowned_generation_directory')
    return folder


def _archive(record, parent, io, deadline, api):
    target = parent / ('graphiti-rebuild.archivado-' + record['nonce'] + '.json')
    raw = _encoded(record)
    if os.path.lexists(target):
        _value, existing = _read(io, target, api._gpub.MAX_MANIFEST_BYTES, api)
        _need(existing == raw, 'rebuild_archive_collision')
    else:
        _write(io, target, record, deadline)


def _restore(record, cfg, io, state_path, deadline, client, api):
    pub = api._gpub
    with pub.session(cfg) as context:
        for row in record['snapshot']:
            payload = {**row['payload'], 'group_id': cfg['group_id'], 'previous_episode_uuids': []}
            previous = record['restored'].get(payload['name'])
            uid = pub.publish(cfg, payload, client, api._contenido_tool_call,
                              known_uuid=(previous or {}).get('uuid'), publication_session=context)
            record['restored'][payload['name']] = {'uuid': uid, 'episode_body_sha256': row['body_sha256']}
            _write(io, state_path, record, deadline)
            id_, version = payload['name'].rsplit('@', 1)
            pub.prune_confirmed(cfg, {id_: {'version': int(version), 'uuid': uid,
                                           'episode_body_sha256': row['body_sha256']}}, context)
        for name, original in sorted(record['original_manifest'].get('transitions', {}).items()):
            target = original['target_ref'][len('custom-agents:knowledge:'):]
            restored = record['restored'][target]
            intent_context = {'source_episode_uuid': restored['uuid']}
            if original['action'] == 'superseded':
                source = original['source_ref'][len('custom-agents:knowledge:'):]
                intent_context['replacement_episode_uuid'] = record['restored'][source]['uuid']
            if 'retired_episode' in original:
                intent_context['retired_episode'] = {'name': target, **restored}
            intent = {**{key: original[key] for key in ('id', 'target_version', 'action', 'source_ref', 'target_ref')},
                      'representation': api._transition_relation_mode(cfg), **intent_context}
            body = api._transition_body(intent)
            previous = record['transitions'].get(name)
            if previous is not None:
                _need(all(previous.get(key) == value for key, value in intent.items()), 'rebuild_changed_transition_progress')
                found = pub._find(client, api._contenido_tool_call, cfg,
                                  {'name': name, 'episode_body': body, 'group_id': cfg['group_id']},
                                  context[2], expected_uuid=previous['uuid'], expected_hash=previous['episode_body_sha256'])
                _need(found == previous['uuid'], 'rebuild_confirmed_marker_missing')
            else:
                api._transition_marker(client, cfg, context, intent['id'], intent['target_version'], name,
                                       body.split('\nrelation: SUPERSEDES\n', 1)[0], intent['source_ref'],
                                       intent['target_ref'], intent['action'], record['transitions'], intent_context)
                _write(io, state_path, record, deadline)
            pub.prune_confirmed(cfg, {}, context, record['transitions'])
        entries = copy.deepcopy(record['original_manifest'].get('entradas', {}))
        for id_, meta in entries.items():
            meta.update(record['restored'][f"{id_}@{meta['version']}"])
            meta['binding'] = 'verified_readback'
        api._escribir_manifest(cfg, api._manifest_data(cfg['group_id'], entries, record['transitions']))
        record['seeded'] = True
        _write(io, state_path, record, deadline)


def _matches(candidate, entries):
    desired = {entry['id']: (entry['version'], _sha(entry['cuerpo'].encode('utf8'))) for entry in entries}
    active = candidate.get('entradas', {})
    _need(type(active) is dict and set(active) == set(desired), 'rebuild_current_corpus_incomplete')
    _need(all((meta.get('version'), meta.get('hash')) == desired[id_] for id_, meta in active.items()),
          'rebuild_current_corpus_changed')


def rebuild(entries, cfg, namespace):
    """Resume the same request, or retain an obsolete stage before a changed request."""
    api = SimpleNamespace(**namespace)
    pub = api._gpub
    entries = _request(entries, api)
    request_hash, config_hash = _sha(_encoded(entries)), _configuration_hash(cfg)
    root = Path(cfg.get('_root') or '.').absolute()
    parent = root / '.claude/knowledge-services'
    state_path, publication = parent / 'graphiti-rebuild.json', parent / 'graphiti-manifest.json'
    with pub.session(cfg) as context:
        effective = api._gscope.read_config(cfg, pub)
        _need(effective['group_id'] == cfg['group_id'], 'rebuild_active_generation_changed_before_lock')
        deadline, shared = context[2], context[3]
        io = type(shared)(shared.reader, _need, pub._guard, maximum=pub.MAX_MANIFEST_BYTES, sync=shared.sync)
        published, raw = _read(io, publication, pub.MAX_MANIFEST_BYTES, api)
        record, _old_raw = _read(io, state_path, pub.MAX_MANIFEST_BYTES, api)
        backup = []
        if record:
            _validate(record, cfg, api)
            if cfg['group_id'] == record['group_id']:
                backup = record['candidate_snapshot'] or []
            elif cfg['group_id'] == record['previous_group_id']:
                backup = record['snapshot']
            if record['baseline_sha256'] == _sha(raw):
                _need(_encoded(record['original_manifest']) == _encoded(published),
                      'rebuild_original_publication_changed')
            same_request = record['request_sha256'] == request_hash and record['config_sha256'] == config_hash
            candidate = record['candidate']
            if same_request and candidate is not None and _encoded(published) == _encoded(candidate):
                _matches(candidate, entries)
                if api.verify(cfg).get('ok') is True:
                    record['phase'] = 'committed'
                    _write(io, state_path, record, deadline)
                    return {'reconstruido': True, 'group_id': record['group_id'],
                            'grupo_anterior_conservado': record['previous_group_id'], 'reanudado': True}
            if not same_request or record['baseline_sha256'] != _sha(raw) or record['phase'] == 'committed':
                _archive(record, parent, io, deadline, api)
                record = {}
        _need(not os.path.lexists(parent / 'graphiti-manifest.pending.json'), 'rebuild_active_publication_pending: sync first')
        observed = pub.observe(cfg)
        _need(not observed['unconfirmed'] and not observed.get('uncommitted', 0),
              'rebuild_active_submission_uncertain: resolve existing receipts first')
        client = api.ClienteMCP(cfg.get('endpoint'), timeout_s=api._timeout_s(cfg),
                              allow_remote=bool(cfg.get('allow_remote', False)),
                              max_respuesta_bytes=api._max_respuesta_bytes(cfg))
        client.initialize()
        if not record:
            snapshot = _snapshot(published, entries, cfg, client, api, backup)
            nonce = uuid.uuid4().hex
            record = {'owner': OWNER, 'schema': 1, 'endpoint': cfg['endpoint'],
                      'logical_group_id': cfg['_logical_group_id'],
                      'group_id': api._gscope.generation_group(cfg['_logical_group_id'], nonce),
                      'previous_group_id': cfg['group_id'], 'nonce': nonce, 'baseline_sha256': _sha(raw),
                      'request_sha256': request_hash, 'config_sha256': config_hash, 'phase': 'building',
                      'original_manifest': copy.deepcopy(published), 'snapshot': snapshot,
                      'restored': {}, 'transitions': {}, 'seeded': False, 'candidate': None,
                      'candidate_snapshot': None}
            _write(io, state_path, record, deadline)
        folder = _stage_root(root, record, io, deadline, api)
        stage = {**cfg, '_root': str(folder), 'group_id': record['group_id'],
                 '_logical_group_id': record['group_id']}
        if not record['seeded']:
            _restore(record, stage, io, state_path, deadline, client, api)
        stage_manifest, _stage_raw = _read(io, folder / '.claude/knowledge-services/graphiti-manifest.json', pub.MAX_MANIFEST_BYTES, api)
        _need(stage_manifest.get('group_id') == record['group_id'], 'rebuild_seeded_manifest_missing_or_foreign')
        _retained_history(stage_manifest, record)
        if record['phase'] == 'building':
            result = api.apply(api.plan(entries, stage), stage)
            _need(api.verify(stage).get('ok') is True, 'rebuild_new_generation_not_verified')
            candidate, _stage_raw = _read(io, folder / '.claude/knowledge-services/graphiti-manifest.json', pub.MAX_MANIFEST_BYTES, api)
            _matches(candidate, entries)
            _retained_history(candidate, record)
            candidate_snapshot = _snapshot(candidate, entries, stage, client, api)
            candidate['logical_group_id'] = cfg['_logical_group_id']
            record.update(candidate=candidate, candidate_snapshot=candidate_snapshot, phase='ready')
            _write(io, state_path, record, deadline)
        else:
            result = {'aplicados': 0, 'revocados': 0}
            _matches(record['candidate'], entries)
            _need(_encoded({**stage_manifest, 'logical_group_id': cfg['_logical_group_id']})
                  == _encoded(record['candidate']), 'rebuild_ready_candidate_changed')
            _need(api.verify(stage).get('ok') is True, 'rebuild_ready_generation_not_verified')
        _current, current_raw = _read(io, publication, pub.MAX_MANIFEST_BYTES, api)
        _need(_sha(current_raw) == record['baseline_sha256'], 'rebuild_publication_changed_during_build')
        api._escribir_manifest(cfg, record['candidate'])
        api._invalidar_cache_verify(cfg)
        record['phase'] = 'committed'
        _write(io, state_path, record, deadline)
        return {**result, 'reconstruido': True, 'group_id': record['group_id'],
                'grupo_anterior_conservado': record['previous_group_id']}
