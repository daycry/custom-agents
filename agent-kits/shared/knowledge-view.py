#!/usr/bin/env python3
"""Bounded canonical memory snapshots and read-only compact projections.

Trusted sibling readers/parsers remain the authority; this module never loads
project code, adapters, native configuration, journals or cache indexes.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
MAX_SCAN = 256
MAX_FILES = 128
MAX_FILE_BYTES = 256 * 1024
MAX_BYTES = 2 * 1024 * 1024
MAX_DEPTH = 8
MAX_OUTPUT_BYTES = 65536
MAX_RESULTS = 20
MAX_ID = 256
MAX_QUERY = 1000
MAX_BODY = 12000
_CONTROLS = re.compile(r'[\x00-\x1f\x7f-\x9f\u2028\u2029\u202a-\u202e\u2066-\u2069]')


def _load(filename):
    spec = importlib.util.spec_from_file_location('knowledge_view_' + filename.replace('-', '_'), HERE / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _unique_object(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError('duplicate_key')
        out[key] = value
    return out


def _valid_id(identifier):
    return isinstance(identifier, str) and 0 < len(identifier) <= MAX_ID


def valid_request(operation='search', text='', id='', area='', tipo='', limit=10):
    """Shared request shape/selector validation; no I/O or Unicode coercion."""
    return (operation in ('search', 'show', 'related')
            and all(isinstance(value, str) for value in (text, id, area, tipo))
            and all(len(value) <= MAX_QUERY for value in (text, area, tipo))
            and type(limit) is int and 1 <= limit <= MAX_RESULTS
            and ((operation == 'search' and not id)
                 or (operation != 'search' and _valid_id(id) and not text and not area and not tipo)))


def snapshot(root):
    """Return bounded source tuples plus explicit completeness and read accounting.

    Approved validation is fail closed for that tree; valid legacy entries remain
    available. Source tuples preserve exact decoded text and relative identity.
    """
    reader = _load('local-read.py')
    budget = {'files': 0, 'bytes': 0, 'entries': 0, 'scans': 0}
    issues = []
    read_status = {}
    def issue(code):
        if code not in issues: issues.append(code)

    def exhausted():
        if budget['files'] >= MAX_FILES:
            issue('file_budget')
            return True
        if MAX_BYTES - budget['bytes'] <= 1:
            issue('byte_budget')
            return True
        return False

    def read(relative, optional=False):
        if budget['files'] >= MAX_FILES:
            issue('file_budget')
            return None
        remaining = MAX_BYTES - budget['bytes']
        if remaining <= 1:
            issue('byte_budget')
            return None
        budget['files'] += 1
        result = reader.read_text(root, relative, max_bytes=min(MAX_FILE_BYTES, remaining - 1))
        budget['bytes'] += result['bytes']
        read_status[relative] = result['status']
        if result['status'] == 'ok': return result['text']
        if not (optional and result['status'] == 'not_found'):
            issue('read_' + result['status'])
        return None

    def scan(relative, optional=False, classify=False):
        empty = {'status': 'budget', 'names': [], 'complete': False}
        if exhausted(): return empty
        if budget['scans'] >= MAX_SCAN:
            issue('scan_call_budget')
            return empty
        remaining = MAX_SCAN - budget['entries']
        if remaining <= 0:
            issue('scan_budget')
            return empty
        budget['scans'] += 1
        result = reader.list_names(root, relative, max_entries=remaining)
        budget['entries'] += len(result['names'])
        if result['status'] == 'incomplete': issue('scan_budget')
        elif (result['status'] != 'ok'
              and not (optional and result['status'] == 'not_found')
              and not (classify and result['status'] == 'not_regular')):
            issue('scan_' + result['status'])
        return result

    def names(relative, optional=False):
        return scan(relative, optional=optional)['names']

    # Presence is checked by safe listing; this also rejects linked corpus roots.
    names('docs/knowledge', optional=True)
    files = []
    text = read('docs/knowledge/README.md', optional=True)
    if text is not None: files.append(('README.md', text.encode('utf-8')))
    for folder in ('adr', 'gotchas', 'lessons'):
        for name in names('docs/knowledge/' + folder, optional=True):
            if name.lower().endswith('.md') and name.lower() != 'readme.md':
                text = read('docs/knowledge/' + folder + '/' + name)
                if text is not None: files.append((folder + '/' + name, text.encode('utf-8')))

    try:
        local = _load('knowledge-local.py')
        taxonomy = local._TAXONOMY
        config = taxonomy._con_id_prefix_por_defecto(
            json.loads(json.dumps(taxonomy._TAXONOMY_FALLBACK)), str(root))
    except Exception:
        issue('approved_helper_unavailable')
        return {'files': files, 'corpus_read': {'complete': False, 'issues': issues, 'budget': budget}}
    taxonomy_text = read('.claude/knowledge-services/taxonomy.json', optional=True)
    taxonomy_failed = False
    if taxonomy_text is not None:
        try:
            config = json.loads(taxonomy_text, object_pairs_hook=_unique_object)
            taxonomy_failed = bool(local._TAXONOMY.validar(config))
        except (ValueError, RecursionError): taxonomy_failed = True
    elif read_status.get('.claude/knowledge-services/taxonomy.json') not in ('not_found',):
        taxonomy_failed = True
        issue('taxonomy_unavailable')
    if taxonomy_failed:
        issue('taxonomy_invalid')
    else:
        sources = []
        visited = set()
        def walk(relative, folder, depth, listed=None):
            if relative in visited: return
            visited.add(relative)
            if depth > MAX_DEPTH:
                issue('depth_budget')
                return
            for name in names(relative, optional=True) if listed is None else listed:
                if exhausted(): break
                target = relative + '/' + name
                if depth >= MAX_DEPTH:
                    if name.lower().endswith('.md') and name.lower() != 'readme.md':
                        text = read(target)
                        if text is not None: sources.append((str(Path(root) / target), folder, text))
                        elif read_status.get(target) == 'not_regular': issue('depth_budget')
                    elif name.lower() != 'readme.md': issue('depth_budget')
                    continue
                result = scan(target, classify=True)
                if result['status'] == 'budget': break
                if result['status'] in ('ok', 'incomplete'):
                    if depth >= MAX_DEPTH: issue('depth_budget')
                    else: walk(target, folder, depth + 1, result['names'])
                elif result['status'] == 'not_regular':
                    if name.lower().endswith('.md') and name.lower() != 'readme.md':
                        text = read(target)
                        if text is not None: sources.append((str(Path(root) / target), folder, text))
                # Other failures were classified by the common scan budget.
        config = local._TAXONOMY._con_id_prefix_por_defecto(config, str(root))
        folders = local._carpetas_declaradas(config)
        for folder in sorted(folders, key=lambda f: (-f.count('/'), f)):
            if exhausted(): break
            if budget['scans'] >= MAX_SCAN:
                issue('scan_call_budget')
                break
            if budget['entries'] >= MAX_SCAN:
                issue('scan_budget')
                break
            walk('docs/knowledge/approved/' + folder, folder, folder.count('/') + 1)
        records, errors = local.index_snapshot(sources, config, include_source=True, root=str(root))
        if errors:
            issue('approved_invalid')
            records = {}
        if sources:
            files.append(('__approved_meta__.json', json.dumps({'config': config, 'entries': records}, ensure_ascii=False, sort_keys=True).encode('utf-8')))
            files.extend((meta['ruta_rel'], meta['texto'].encode('utf-8')) for meta in records.values())
    return {'files': files, 'corpus_read': {'complete': not issues, 'issues': issues, 'budget': budget}}


def query(root, operation='search', text='', id='', area='', tipo='', limit=10):
    """Project safe read-only results. Invalid selectors never touch the corpus."""
    data = {'version': 1, 'source': 'canonical_knowledge',
            'observed_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'operation': operation if operation in ('search', 'show', 'related') else '',
            'status': 'ok', 'complete': True, 'issues': [], 'entries': [],
            'selected': None, 'related': None,
            'budget': {'files': 0, 'bytes': 0, 'entries': 0}}
    def issue(code):
        if code not in data['issues']: data['issues'].append(code)
        data['complete'] = False
        if data['status'] in ('ok', 'not_found'): data['status'] = 'partial'
    if not valid_request(operation, text, id, area, tipo, limit):
        data.update(status='invalid_request', complete=False, issues=['invalid_request'])
        return data
    try:
        find = _load('knowledge-find.py')
        redactor = _load('redact.py')
        snap = snapshot(root)
        entries = find.parsear_corpus(snap['files'])
    except Exception:
        data.update(status='unavailable', complete=False, issues=['helper_unavailable'])
        return data
    data['budget'] = snap['corpus_read']['budget']
    for code in snap['corpus_read']['issues']: issue(code)
    def clean(value, maximum=160, multiline=False):
        value = redactor.redactar('' if value is None else str(value))
        value = (_CONTROLS.sub(' ', value) if not multiline else
                 _CONTROLS.sub(lambda m: m.group() if m.group() in '\n\r\t' else ' ', value))
        if len(value) > maximum: issue('text_budget')
        return value[:maximum]
    eligible = []
    for e in entries:
        if not _valid_id(e.get('id')):
            issue('identity_invalid')
            continue
        if clean(e['id'], MAX_ID) != e['id']:
            issue('identity_redacted')
            continue
        if e.get('_legacy_version_invalid'): issue('version_invalid')
        if e['estado'] not in ('aceptada', 'propuesta', 'obsoleta', 'aprobado'): issue('unknown_state')
        eligible.append(e)
    counts = {}
    for e in eligible: counts[e['id'].casefold()] = counts.get(e['id'].casefold(), 0) + 1
    if any(n > 1 for n in counts.values()): issue('identity_collision')
    def projected_version(e):
        value = e.get('version')
        if value is None: return None
        if type(value) is not int or value <= 0:
            issue('version_invalid')
            return None
        if value <= 9007199254740991: return value
        try: decimal = str(value)
        except ValueError:
            issue('version_budget')
            return None
        if len(decimal) > 4300:
            issue('version_budget')
            return None
        return decimal

    def compact(e):
        return {'id': e['id'], 'tipo': clean(e['tipo']), 'estado': clean(e['estado']),
                'estado_detalle': clean(e['estado_detalle']), 'titular': clean(e['titular']),
                'area': clean(e['area']), 'version': projected_version(e),
                'category': clean(e['category']) if e.get('category') is not None else None,
                'evidencia': clean(e.get('evidencia'), 1000),
                'origen': 'approved' if e['ruta'].startswith('docs/knowledge/approved/') else 'legacy',
                'ruta': clean(e['ruta'], 1000),
                'source_sha256': hashlib.sha256(e['texto'].encode('utf-8')).hexdigest()}
    if operation == 'search':
        hits, total = find.buscar(eligible, texto=text, area=area, tipo=tipo, limit=limit)
        data['entries'] = [compact(e) for e in hits]
        if total > len(hits): issue('result_budget')
        if not hits and data['complete']: data['status'] = 'not_found'
    else:
        matches = [e for e in eligible if e['id'].casefold() == id.casefold()]
        if len(matches) > 1:
            data.update(status='ambiguous', complete=False)
        elif not matches:
            if data['complete']: data['status'] = 'not_found'
        else:
            e = matches[0]
            if operation == 'show': data['selected'] = dict(compact(e), texto=clean(e['texto'], MAX_BODY, multiline=True))
            else:
                # The canonical relation methods use dictionary lookup: remove collided
                # peers before invoking them, preserving unresolved successor identities.
                unique = [x for x in eligible if counts[x['id'].casefold()] == 1]
                relations = find.relaciones(unique, e)
                result = {'sucesion': [], 'iniciativa': [], 'area': [], 'enlaces': []}
                remaining_results = MAX_RESULTS
                for group in result:
                    rows = relations.get(group, [])
                    if len(rows) > remaining_results: issue('result_budget')
                    selected_rows = rows[:remaining_results]
                    remaining_results -= len(selected_rows)
                    for row in selected_rows:
                        if group == 'sucesion':
                            relation, target, identifier = row
                            if not _valid_id(identifier):
                                issue('identity_invalid')
                                continue
                            if clean(identifier, MAX_ID) != identifier:
                                issue('identity_redacted')
                                continue
                            if target is None: issue('unresolved_relation')
                            result[group].append({'relation': clean(relation), 'id': clean(identifier, MAX_ID), 'entry': compact(target) if target else None})
                        else: result[group].append(compact(row))
                data['related'] = result
    def encoded_size(): return len(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    if encoded_size() > MAX_OUTPUT_BYTES:
        issue('output_budget')
        while encoded_size() > MAX_OUTPUT_BYTES:
            if data['entries']: data['entries'].pop()
            elif data['related'] and any(data['related'].values()):
                next(rows for rows in reversed(list(data['related'].values())) if rows).pop()
            elif data['selected'] and data['selected']['texto']:
                data['selected']['texto'] = data['selected']['texto'][:len(data['selected']['texto'])//2]
            else:
                data['selected'] = None
                break
    return data
