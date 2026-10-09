#!/usr/bin/env python3
"""Canonical authorization for explicit documental reads, without service imports.

Snapshots remain bounded observations. Their matching fingerprints establish
observed stability, without promising a transaction or detection of ABA changes.
"""
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import time

HERE = Path(__file__).resolve().parent
_FILTER_KEYS = {'tipo', 'area', 'iniciativa', 'claves'}


def _load(name):
    spec = importlib.util.spec_from_file_location('knowledge_read_' + name.replace('-', '_'), HERE / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _copy(value):
    return json.loads(json.dumps(value, ensure_ascii=False, allow_nan=False))


def _filters(value):
    if value is None:
        value = {}
    if not isinstance(value, dict) or set(value) - _FILTER_KEYS:
        raise ValueError('filters_invalid')
    result = {key: value.get(key, [] if key == 'claves' else '') for key in sorted(_FILTER_KEYS)}
    for key, item in result.items():
        texts = item if key == 'claves' else [item]
        if key == 'claves' and (not isinstance(item, list) or len(item) > 128):
            raise ValueError('filters_invalid')
        if any(not isinstance(text, str) or len(text) > 512 or
               any(ord(char) < 32 or 127 <= ord(char) <= 159 for char in text) for text in texts):
            raise ValueError('filters_invalid')
    return _copy(result)


def prepare(root, backend_id, intent, *, expected_config, filters=None, accept_entry=None, deadline=None):
    """Authorize from current project policy; refresh keeps the same absolute deadline.

    The trusted router supplies the predicate implementing its existing filters.
    As the documental query cannot restrict sources, every routed entry must pass.
    JSON configuration never supplies the internal context or its callback.
    """
    def unavailable(reason):
        return {'status': 'unavailable', 'reason': reason, 'context': None}
    started = time.monotonic()
    if deadline is not None:
        if type(deadline) not in (int, float) or not math.isfinite(deadline):
            return unavailable('read_deadline')
        if deadline <= started:
            return unavailable('read_deadline')
    try:
        root_string = os.fspath(root)
        if not isinstance(root_string, str) or root_string.replace('\\', '/').startswith('//'):
            return unavailable('root_unavailable')
        root_string = os.path.abspath(root_string)
        if not isinstance(backend_id, str) or not backend_id or not isinstance(intent, str):
            return unavailable('policy_invalid')
        if re.fullmatch(r'[a-z][a-z0-9_-]*', intent) is None:
            return unavailable('policy_invalid')
        expected = _copy(expected_config)
        requested = _filters(filters)
        taxonomy = _load('knowledge-taxonomy-local.py')
        options, errors = taxonomy.documental_read_options(expected)
        if errors or any(key.startswith('_') for key in expected):
            return unavailable('policy_invalid')
        if options['enabled'] is not True:
            return unavailable('read_disabled')
        budget_deadline = started + options['timeout_ms'] / 1000
        if deadline is None:
            deadline = budget_deadline
        elif deadline > budget_deadline:
            return unavailable('read_deadline')
        view = _load('knowledge-view.py')
        snap = view.snapshot(root_string, include_digests=True, deadline=deadline)
        if time.monotonic() >= deadline:
            return unavailable('read_deadline')
        if snap['corpus_read']['complete'] is not True:
            return unavailable('canonical_incomplete')
        metadata = [data for name, data in snap['files'] if name == '__approved_meta__.json']
        if len(metadata) != 1:
            return unavailable('canonical_empty')
        approved = json.loads(metadata[0].decode('utf-8'))
        config = approved['config']
        declaration = config.get('backends', {}).get(backend_id)
        if (not isinstance(declaration, dict) or declaration.get('type') != 'markdown-export'
                or declaration.get('enabled') is not True):
            return unavailable('policy_changed')
        actual = declaration.get('config')
        _, actual_errors = taxonomy.documental_read_options(actual)
        if (actual_errors or json.dumps(actual, sort_keys=True, allow_nan=False)
                != json.dumps(expected, sort_keys=True, allow_nan=False)):
            return unavailable('policy_changed')
        if expected.get('router', {}).get('intents', {}).get(intent) is not True:
            return unavailable('intent_not_authorized')
        records = approved['entries']
        entries, errors, _ = taxonomy.entradas_enrutadas(config, backend_id, records)
        if errors or not entries:
            return unavailable('routing_not_authorized')
        filtered = any(requested.values())
        if filtered and not callable(accept_entry):
            return unavailable('filters_not_supported')
        for entry in entries:
            meta = records[entry['id']]
            if type(entry.get('version')) is not int or entry['version'] < 1:
                return unavailable('canonical_incomplete')
            if callable(accept_entry) and accept_entry(_copy(meta), _copy(requested)) is not True:
                return unavailable('filters_not_supported')
            relative = 'docs/knowledge/' + meta['ruta_rel']
            digest = snap['source_digests'].get(relative)
            if not isinstance(digest, str) or re.fullmatch(r'[a-f0-9]{64}', digest) is None:
                return unavailable('canonical_incomplete')
            entry.update({'ruta': relative, 'canonical_path': relative, 'canonical_sha256': digest,
                          'canonical_text': meta['texto'], 'estado': 'aprobado'})
        fingerprint = hashlib.sha256(json.dumps({
            'policy': config, 'digests': snap['source_digests'], 'filters': requested,
            'backend_id': backend_id, 'intent': intent}, ensure_ascii=False,
            sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()
        if time.monotonic() >= deadline:
            return unavailable('read_deadline')
        def refresh():
            observed = prepare(root_string, backend_id, intent, expected_config=expected,
                               filters=requested, accept_entry=accept_entry, deadline=deadline)
            return observed['context'] if observed['status'] == 'ok' else {'error': observed['reason']}
        context = {'root': root_string, 'backend_id': backend_id, 'backend_enabled': True,
                   'intent': intent, 'entries': entries, 'fingerprint': fingerprint,
                   'deadline': deadline, 'refresh': refresh, 'filters': requested,
                   'filters_authorized': True}
        return {'status': 'ok', 'reason': '', 'context': context}
    except Exception:  # Partial bundles or a failed trusted predicate never open a service read.
        return unavailable('canonical_unavailable')
