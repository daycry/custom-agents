"""Resolve native graph results through committed episode identities.

Entity summaries and extracted facts are derivative text. Confirmed source linkage
is not claim-level validation or authority for automatically approving that text.
"""
import os
from pathlib import Path
import re
import time

MAX_REFERENCES = 128
MAX_MEMBERSHIP_EPISODES = 20
MAX_MEMBERSHIP_NODES = 500


def _need(condition, reason):
    if not condition:
        raise ValueError(reason)


def _identity(value):
    return type(value) is str and 0 < len(value) <= 200 and value.isprintable()


def build(cfg, by_name, publication):
    """Read committed local bindings without mutation or acquiring a lock."""
    root = Path(cfg.get('_root') or '.').absolute()
    path = root / '.claude/knowledge-services/graphiti-manifest.json'
    reader, state = publication._helper('local-read'), publication._helper('local-state')
    io = state.StateIO(reader, _need, publication._guard, maximum=publication.MAX_MANIFEST_BYTES)
    _need(os.path.lexists(path), 'native_provenance_requires_published_bindings')
    raw, _ = io.read(path, publication.MAX_MANIFEST_BYTES)
    manifest = publication._decode(raw)
    _need(type(manifest) is dict and manifest.get('group_id') == cfg['group_id']
          and type(manifest.get('entradas')) is dict, 'native_provenance_scope_invalid')
    bindings = publication._committed_bindings(manifest)
    owned, current, expected_current = {}, {}, {}
    for name, (uid, body_hash) in bindings.items():
        if not re.fullmatch(r'.+@[1-9][0-9]*', name):
            continue  # Control markers are not domain source documents.
        _need(_identity(uid) and uid not in owned, 'ambiguous_native_episode_identity')
        owned[uid] = name
    for id_, meta in manifest['entradas'].items():
        _need(type(meta) is dict, 'invalid_current_provenance_binding')
        name = f"{id_}@{meta.get('version')}"
        uid = meta.get('uuid')
        if meta.get('binding') == 'verified_readback' and _identity(uid) and owned.get(uid) == name:
            expected_current[uid] = name
        record = by_name.get(name)
        if record is None:
            continue
        if (meta.get('binding') != 'verified_readback' or not _identity(uid)
                or record.get('uuid') != uid or record.get('_group_id') != cfg['group_id']
                or record.get('_body_sha256') != meta.get('episode_body_sha256')
                or record.get('knowledge_id') != id_ or record.get('version') != str(meta.get('version'))
                or record.get('hash') != meta.get('hash') or record.get('status') != 'aprobado'):
            continue
        _need(uid in owned and owned[uid] == name, 'unbound_current_episode_identity')
        current[uid] = name
    modern = 'transitions' in manifest or any(meta.get('binding') == 'verified_readback'
                                             for meta in manifest['entradas'].values())
    return {'owned': owned, 'current': current, 'expected_current': expected_current, 'modern': modern,
            'nodes': {}, 'warnings': []}


def episode_name(hit, context, by_name):
    """An exact published episode identity is distinct from an Entity's name."""
    if context is None or not _identity(hit.get('uuid')):
        return None
    name = context['current'].get(hit['uuid'])
    if name is None or hit.get('name') != name:
        return None
    record = by_name.get(name)
    return name if record is not None and record.get('uuid') == hit['uuid'] else None


def _select(references, context, by_name):
    if type(references) is not list or not references or len(references) > MAX_REFERENCES:
        return None
    if any(not _identity(uid) or uid not in context['owned'] for uid in references):
        return None
    if any(uid in context['expected_current'] and uid not in context['current'] for uid in references):
        return None
    names = {context['current'][uid] for uid in references if uid in context['current']}
    if len(names) != 1:
        return None
    name = next(iter(names))
    return name if name in by_name else None


def fact_name(hit, context, by_name):
    """An explicit malformed reference never falls back to an Entity's name."""
    return _select(hit.get('episodes'), context, by_name) if context is not None else None


def populate_nodes(context, hits, client, decode, cfg):
    """Bounded, single-episode membership reads; their union cannot imply provenance."""
    if context is None or not hits:
        return
    wanted = {hit.get('uuid') for hit in hits if _identity(hit.get('uuid'))}
    if not wanted:
        return
    context['membership_complete'] = False
    if set(context['current']) != set(context['expected_current']):
        context['warnings'].append('ventana incompleta para verificar procedencia de entidades')
        return
    deadline = time.monotonic() + max(1.0, cfg.get('timeout_ms', 3000) / 1000) * 4
    ordered = sorted(context['current'], key=lambda uid: context['current'][uid])
    if len(ordered) > MAX_MEMBERSHIP_EPISODES:
        context['warnings'].append('limite de episodios para verificar procedencia de entidades')
        return
    complete = True
    for uid in ordered[:MAX_MEMBERSHIP_EPISODES]:
        if time.monotonic() >= deadline:
            context['warnings'].append('presupuesto agotado al verificar procedencia de entidades')
            complete = False
            break
        try:
            value = decode(client.tools_call('get_episode_entities',
                {'episode_uuids': [uid], 'group_id': cfg['group_id']}))
            nodes = value.get('nodes') if type(value) is dict else None
            _need(type(nodes) is list and len(nodes) <= MAX_MEMBERSHIP_NODES,
                  'invalid_episode_membership_response')
            _need(all(type(node) is dict and node.get('group_id') == cfg['group_id']
                      and _identity(node.get('uuid')) for node in nodes), 'foreign_or_unbound_entity_membership')
            _need(len({node['uuid'] for node in nodes}) == len(nodes), 'ambiguous_entity_membership')
        except Exception:
            context['warnings'].append('procedencia de entidades no disponible o no verificable')
            complete = False
            continue
        for node in nodes:
            if node['uuid'] in wanted:
                context['nodes'].setdefault(node['uuid'], set()).add(uid)
    context['membership_complete'] = complete


def node_name(hit, context, by_name):
    if context is None or not context.get('membership_complete') or not _identity(hit.get('uuid')):
        return None
    references = sorted(context['nodes'].get(hit['uuid'], set()))
    return _select(references, context, by_name)
