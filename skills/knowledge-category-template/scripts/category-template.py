#!/usr/bin/env python3
"""Project category templates, bounded inbox checks and explicit candidate proposals.

Only stdlib. No template execution, approval, publication, reindexing or network.
Configuration and proposal operations share the curation service's cooperative
writer lock; external editors must cooperate. Partial configuration is explicit.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import sys
import uuid

for _stream in (sys.stdin, sys.stdout, sys.stderr):
    try: _stream.reconfigure(encoding='utf-8', errors='replace')
    except Exception: pass

SHARED = Path(__file__).resolve().parents[3] / 'agent-kits/shared'
BUNDLE_ROOT = SHARED.parent.parent
TAXONOMY = '.claude/knowledge-services/taxonomy.json'
MAX_TEMPLATE = 65536
MAX_FILES = 128
MAX_TOTAL = 2 * 1024 * 1024
MAX_DOCUMENT = 256 * 1024
MAX_DEPTH = 4
_MODULES = {}
_CATEGORY_KEYS = {'key', 'folder', 'min_evidence', 'routing', 'template', 'inbox',
                  'allowed_producers', 'required_metadata', 'required_sections'}


def _load(name):
    if name not in _MODULES:
        spec = importlib.util.spec_from_file_location('category_' + name.replace('-', '_'), SHARED / name)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _MODULES[name] = mod
    return _MODULES[name]


class _Rejected(Exception):
    def __init__(self, status, errors=None):
        self.status, self.errors = status, errors or []


def _result(status, **values):
    return {'status': status, 'complete': status in ('preview', 'configured', 'ok', 'checked', 'proposed', 'empty'), **values}


def _reject(status, errors=None):
    raise _Rejected(status, errors)


def _json(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':')).encode('utf-8')


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _read(root, relative, maximum=MAX_DOCUMENT):
    return _load('local-read.py').read_bytes(root, relative, max_bytes=maximum, include_digest=True, include_identity=True)


def _policy(root):
    observed = _read(root, TAXONOMY)
    if observed['status'] not in ('ok', 'not_found'):
        _reject('unsafe_taxonomy')
    schema = _load('knowledge-schema.py')
    if observed['status'] == 'ok':
        data = json.loads(observed['data'].decode('utf-8-sig'), object_pairs_hook=_unique)
    else:
        data = _load('knowledge-taxonomy-local.py')._con_id_prefix_por_defecto(schema.default_taxonomy(), str(root))
    errors = schema.validar(data)
    if errors:
        _reject('invalid_taxonomy', errors)
    return data, observed


def _unique(pairs):
    data = {}
    for key, value in pairs:
        if key in data:
            _reject('duplicate_json_key')
        data[key] = value
    return data


def _category(config, key):
    found = next((c for c in config['categories'] if c['key'] == key), None)
    if found is None:
        _reject('category_not_found')
    return found


def _outside_bundle(root, relative):
    installed = ((BUNDLE_ROOT / '.claude-plugin/plugin.json').is_file()
                 or (BUNDLE_ROOT / '.codex-plugin/plugin.json').is_file()) and not (BUNDLE_ROOT / '.git').exists()
    if installed:
        try:
            (Path(root) / relative).absolute().relative_to(BUNDLE_ROOT.absolute())
        except ValueError:
            return
        _reject('template_in_plugin')


def _plan(root, request):
    if (not isinstance(request, dict) or set(request) != {'category', 'template_text'}
            or not isinstance(request['category'], dict) or set(request['category']) - _CATEGORY_KEYS):
        _reject('invalid_request')
    patch, template = request['category'], request['template_text']
    if not isinstance(patch.get('key'), str) or not patch['key']:
        _reject('invalid_request')
    if not isinstance(template, str) or not template.strip() or '\x00' in template or len(template.encode('utf-8')) > MAX_TEMPLATE:
        _reject('invalid_template')
    redactor = _load('redact.py')
    if redactor.redactar(template) != template or redactor.redactar(json.dumps(patch, ensure_ascii=False)) != json.dumps(patch, ensure_ascii=False):
        _reject('sensitive_template_or_configuration')
    config, observed = _policy(root)
    updated = copy.deepcopy(config)
    cat = next((c for c in updated['categories'] if c['key'] == patch['key']), None)
    if cat is None:
        cat = {'routing': {}}
        updated['categories'].append(cat)
    cat.update(copy.deepcopy(patch))
    errors = _load('knowledge-schema.py').validar(updated)
    if errors or 'template' not in cat:
        _reject('invalid_taxonomy', errors)
    _outside_bundle(root, cat['template'])
    local = _load('knowledge-local.py')
    fm = local._frontmatter(template)
    headings = _load('knowledge-curation-rules.py')._section_content(local._FRONTMATTER_RE.sub('', template, count=1))
    if (any(k not in fm for k in cat.get('required_metadata', []))
            or any(s.casefold() not in headings for s in cat.get('required_sections', []))
            or fm.get('category') != cat['key']):
        _reject('template_contract_mismatch')
    previous = _read(root, cat['template'], MAX_TEMPLATE)
    if previous['status'] not in ('ok', 'not_found'):
        _reject('unsafe_template')
    if previous['status'] == 'ok' and previous['data'] != template.encode('utf-8'):
        _reject('template_exists')
    raw = (json.dumps(updated, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    if len(raw) > MAX_DOCUMENT:
        _reject('taxonomy_budget')
    identity = _load('local-read.py')._identity(Path(root).lstat())
    token = _sha(_json({'root': str(Path(root).absolute()), 'identity': identity,
                        'taxonomy': observed.get('sha256'), 'template': previous.get('sha256'),
                        'taxonomy_after': _sha(raw), 'template_after': _sha(template.encode('utf-8'))}))
    return updated, cat, raw, template.encode('utf-8'), observed, previous, token


def _replace_taxonomy(root, raw, observed):
    service = _load('knowledge-curation.py')
    if observed['status'] == 'not_found':
        service._create(root, TAXONOMY, raw)
        return
    backup_dir = '.claude/knowledge-services/.category-backups'
    ignore = backup_dir + '/.gitignore'
    ignored = _read(root, ignore)
    if ignored['status'] == 'not_found':
        service._create(root, ignore, b'*\n')
    elif ignored['status'] != 'ok' or ignored['data'] != b'*\n':
        _reject('backup_ignore_conflict')
    backup = backup_dir + '/' + observed['sha256'] + '.json'
    old_backup = _read(root, backup)
    if old_backup['status'] == 'not_found':
        service._create(root, backup, observed['data'])
    elif old_backup['status'] != 'ok' or old_backup['data'] != observed['data']:
        _reject('backup_conflict')
    staged = '.claude/knowledge-services/.category-' + uuid.uuid4().hex + '.tmp'
    identity = service._stage(root, staged, raw)
    current = _read(root, TAXONOMY)
    if current['status'] != 'ok' or current.get('sha256') != observed['sha256']:
        _reject('changed_inputs')
    target, parents = service._parents(root, TAXONOMY)
    reader = _load('local-read.py')
    stage = _read(root, staged)
    if (not reader._unchanged(parents) or list(stage.get('identity', [])) != identity
            or stage.get('sha256') != _sha(raw) or current['identity'] != _read(root, TAXONOMY).get('identity')):
        _reject('changed_inputs')
    os.replace(Path(root) / staged, target)
    service._sync_dir(target.parent)


def configure(root, request, *, apply=False, expected_sha256=None):
    created = False
    try:
        root = Path(root).absolute()
        if apply and not expected_sha256:
            _reject('expected_sha256_required')
        plan = _plan(root, request)
        _, cat, raw, template, observed, previous, token = plan
        if not apply:
            return _result('preview', category=cat, template_text=template.decode('utf-8'), expected_sha256=token)
        if expected_sha256 != token:
            _reject('changed_inputs')
        service = _load('knowledge-curation.py')
        with service._locked(root):
            if _plan(root, request)[-1] != token:
                _reject('changed_inputs')
            if previous['status'] == 'not_found':
                service._create(root, cat['template'], template)
                created = True
            if observed.get('data') != raw:
                _replace_taxonomy(root, raw, observed)
            actual = _read(root, TAXONOMY)
            if actual['status'] != 'ok' or actual.get('sha256') != _sha(raw):
                _reject('configuration_not_verified')
        return _result('configured', category=cat['key'], template=cat['template'], template_created=created)
    except _Rejected as exc:
        return _result('partial' if created else exc.status, complete=False, issue=exc.status, errors=exc.errors,
                       template_created=created)
    except (OSError, ValueError, TypeError, KeyError, ImportError, AttributeError, RuntimeError):
        return _result('partial' if created else 'configuration_unavailable', complete=False, template_created=created)
    except Exception as exc:
        service = _MODULES.get('knowledge-curation.py')
        if service is None or not isinstance(exc, service._Failure):
            raise
        return _result('partial' if created else exc.status, complete=False, issue=exc.status,
                       errors=exc.errors or [], template_created=created)


def read_template(root, category):
    try:
        config, _ = _policy(root)
        cat = _category(config, category)
        if 'template' not in cat:
            _reject('template_not_configured')
        _outside_bundle(root, cat['template'])
        observed = _read(root, cat['template'], MAX_TEMPLATE)
        if observed['status'] != 'ok':
            _reject('template_' + observed['status'])
        return _result('ok', path=cat['template'], text=observed['data'].decode('utf-8-sig'), sha256=observed['sha256'])
    except _Rejected as exc:
        return _result(exc.status, errors=exc.errors)
    except (OSError, ValueError, TypeError, KeyError, ImportError):
        return _result('template_unavailable')


def _inventory(root, cat):
    if 'inbox' not in cat:
        _reject('inbox_not_configured')
    reader = _load('local-read.py')
    documents, issues, cost = [], [], [0, 0]

    def walk(relative, depth):
        listing = reader.list_names(root, relative, max_entries=MAX_FILES + 1)
        if not listing['complete']:
            issues.append('inventory_' + listing['status'])
        if listing['status'] not in ('ok', 'incomplete'):
            return
        for name in listing['names']:
            cost[0] += 1
            if cost[0] > MAX_FILES:
                issues.append('file_budget')
                return
            path = relative + '/' + name
            if name.startswith('.') or name.casefold() == 'readme.md':
                continue
            if path.casefold() in ('docs/knowledge/approved', 'docs/knowledge/candidates'):
                continue
            info = (Path(root) / path).lstat()
            if reader._redirected(info):
                issues.append('redirected_input')
            elif stat.S_ISDIR(info.st_mode):
                if depth >= MAX_DEPTH:
                    issues.append('depth_budget')
                else:
                    walk(path, depth + 1)
            elif name.lower().endswith('.md'):
                remaining = min(MAX_DOCUMENT, MAX_TOTAL - cost[1] - 1)
                if remaining <= 0:
                    issues.append('byte_budget')
                    return
                observed = _read(root, path, remaining)
                cost[1] += observed['bytes']
                if observed['status'] != 'ok':
                    issues.append('document_' + observed['status'])
                else:
                    documents.append((path, observed))
    walk(cat['inbox'], 0)
    return sorted(documents), sorted(set(issues))


def _document(root, category, path, observed, origin, config):
    local = _load('knowledge-local.py')
    text = observed['data'].decode('utf-8-sig').replace('\r\n', '\n').replace('\r', '\n')
    fm = local._frontmatter(text)
    body = local._FRONTMATTER_RE.sub('', text, count=1)
    errors = []
    if 'estado' in fm or fm.get('category', category['key']) != category['key']:
        errors.append({'campo': 'category', 'mensaje': 'categoria incompatible o aprobacion declarada en la entrada', 'fichero': path})
    if fm.get('content_origin', origin) != origin:
        errors.append({'campo': 'content_origin', 'mensaje': 'origen incompatible con el flujo declarado', 'fichero': path})
    fm.update(category=category['key'], content_origin=origin)
    rules = _load('knowledge-curation-rules.py')
    errors.extend(rules.validar_aprobacion(fm, body, category, config, path,
                 _load('knowledge-schema.py').default_taxonomy()['evidence_levels'], TAXONOMY))
    fm.update(source_path=path, source_sha256=observed['sha256'])
    row = {'path': path, 'sha256': observed['sha256'], 'state': 'invalid' if errors else 'valid', 'errors': errors}
    return row, fm, body


def check_category(root, category, *, origin='human', propose=False, expected_sha256=None):
    rows, written = [], False
    try:
        root = Path(root).absolute()
        if origin not in ('human', 'agent'):
            _reject('invalid_origin')
        if propose and not expected_sha256:
            _reject('expected_sha256_required')
        config, policy = _policy(root)
        cat = _category(config, category)
        documents, issues = _inventory(root, cat)
        payloads = []
        for path, observed in documents:
            row, fm, body = _document(root, cat, path, observed, origin, config)
            rows.append(row)
            payloads.append((fm, body))
        token = _sha(_json({'root': str(root), 'policy': policy.get('sha256'), 'config': config,
                           'category': category, 'origin': origin, 'files': [(p, d['sha256']) for p, d in documents],
                           'issues': issues}))
        if propose:
            if not issues and token != expected_sha256:
                _reject('changed_inputs')
            if issues:
                _reject('incomplete_inventory')
            service = _load('knowledge-curation.py')
            for row, (fm, body) in zip(rows, payloads):
                if row['state'] != 'valid':
                    continue
                filename = 'category-' + _sha(_json([category, row['path'], row['sha256']]))[:32] + '.md'
                text = service._render(fm, body)
                producer = 'human' if origin == 'human' else 'documenter'
                prepared = service._payload(text)[0]
                if 'proposed_by' not in service._module('knowledge-local.py')._frontmatter(prepared):
                    prepared = prepared.replace('---', '---\nproposed_by: ' + producer, 1)
                existing_path = service.BASE + '/pending/' + filename
                existing = _read(root, existing_path)
                if existing['status'] == 'ok' and existing['data'] == prepared.encode('utf-8'):
                    row.update(state='already_proposed', candidate=existing_path, candidate_sha256=existing['sha256'])
                    continue
                if existing['status'] != 'not_found':
                    row.update(state='proposal_failed', issue='existing_candidate_conflict')
                    continue
                result, code = service.propose(str(root), filename, text,
                    producer=producer, origin=origin,
                    expected_policy_sha256=policy.get('sha256'),
                    expected_source=(row['path'], row['sha256']))
                if code:
                    row.update(state='proposal_failed', issue=result['status'])
                else:
                    written = True
                    row.update(state='proposed', candidate=result['ruta'], candidate_sha256=result['sha256'])
        failed = any(r['state'] in ('invalid', 'proposal_failed') for r in rows)
        return _result('proposed' if propose and not failed else 'checked' if rows else 'empty',
                       complete=not issues, valid=not failed, files=rows, origin=origin, issues=issues,
                       expected_sha256=token, written=written)
    except _Rejected as exc:
        return _result(exc.status, complete=False, files=rows, errors=exc.errors, written=written)
    except (OSError, ValueError, TypeError, KeyError, ImportError, AttributeError, RuntimeError):
        return _result('check_unavailable', complete=False, files=rows, written=written)
    except Exception as exc:
        service = _MODULES.get('knowledge-curation.py')
        if service is None or not isinstance(exc, service._Failure):
            raise
        return _result(exc.status, complete=False, files=rows, errors=exc.errors or [], written=written)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('operation', choices=('configure', 'template', 'check'))
    parser.add_argument('--root', default='.')
    parser.add_argument('--category')
    parser.add_argument('--origin', choices=('human', 'agent'), default='human')
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--propose', action='store_true')
    parser.add_argument('--expected-sha256')
    args = parser.parse_args(argv)
    if ((args.operation != 'configure' and args.apply) or (args.operation != 'check' and args.propose)
            or (args.operation != 'configure' and not args.category)):
        parser.error('operation and options are incompatible or category is missing')
    if args.operation == 'configure':
        try:
            raw = sys.stdin.buffer.read(MAX_DOCUMENT + 1)
            request = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=_unique) if len(raw) <= MAX_DOCUMENT else None
        except (ValueError, _Rejected):
            request = None
        result = configure(args.root, request, apply=args.apply, expected_sha256=args.expected_sha256)
    elif args.operation == 'template':
        result = read_template(args.root, args.category)
    else:
        result = check_category(args.root, args.category, origin=args.origin,
                                propose=args.propose, expected_sha256=args.expected_sha256)
    output = json.dumps(result, ensure_ascii=False)
    try:
        output = _load('redact.py').redactar(output)
    except (OSError, ImportError, AttributeError):
        print(json.dumps(_result('helper_unavailable', complete=False)))
        return 2
    print(output)
    return 0 if result['complete'] and result.get('valid', True) else 1


if __name__ == '__main__':
    sys.exit(main())
