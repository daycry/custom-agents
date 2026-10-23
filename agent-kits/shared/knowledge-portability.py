"""Pure versioned local knowledge package codec; no IO/configuration/CLI."""
import base64
import binascii
import hashlib
import json
import re


class InvalidPackage(ValueError):
    pass


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def label(value):
    if not isinstance(value, str) or len(value) > 128 or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', value):
        raise InvalidPackage('invalid_project_label')
    return value


def exact(value, keys):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise InvalidPackage('invalid_fields')


def hexadecimal(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-f0-9]{64}', value):
        raise InvalidPackage('invalid_digest')


def relative(value):
    if not isinstance(value, str) or '\\' in value or ':' in value or '\x00' in value:
        raise InvalidPackage('invalid_origin_path')
    parts = value.split('/')
    if any(not part or part in ('.', '..') or part.endswith((' ', '.')) for part in parts):
        raise InvalidPackage('invalid_origin_path')
    if parts[0] != 'approved' or len(parts) < 3 or not parts[-1].lower().endswith('.md'):
        raise InvalidPackage('invalid_origin_path')


def pairs(items):
    value = {}
    for key, item in items:
        if key in value:
            raise InvalidPackage('duplicate_key')
        value[key] = item
    return value


def json_value(raw):
    try:
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                           parse_constant=lambda _: (_ for _ in ()).throw(InvalidPackage('invalid_number')))
        if canonical(value) != raw:
            raise InvalidPackage('noncanonical_json')
        return value
    except (UnicodeError, ValueError, TypeError, RecursionError) as exc:
        raise InvalidPackage('invalid_json') from exc


def validate(value, *, max_bytes, max_entries, parse):
    exact(value, ('schema_version', 'kind', 'source', 'selection', 'entries'))
    if type(value['schema_version']) is not int or value['schema_version'] != 1 or value['kind'] != 'approved_knowledge_export':
        raise InvalidPackage('unsupported_package')
    source = value['source']
    exact(source, ('project_id', 'identity_basis', 'id_prefix', 'policy_sha256'))
    label(source['project_id'])
    if source['identity_basis'] != 'declared' or not isinstance(source['id_prefix'], str) or not source['id_prefix']:
        raise InvalidPackage('invalid_source')
    hexadecimal(source['policy_sha256'])
    selection = value['selection']
    exact(selection, ('ids', 'scope'))
    exact(selection['scope'], ('category', 'area'))
    if any(v is not None and (not isinstance(v, str) or not v) for v in selection['scope'].values()):
        raise InvalidPackage('invalid_scope')
    entries, ids = value['entries'], selection['ids']
    if not isinstance(entries, list) or not 1 <= len(entries) <= max_entries or not isinstance(ids, list):
        raise InvalidPackage('invalid_count')
    decoded = []
    for entry in entries:
        exact(entry, ('id', 'version', 'category', 'relative_path', 'bytes', 'raw_sha256', 'content_base64'))
        if not isinstance(entry['id'], str) or not re.fullmatch(r'[A-Za-z0-9._-]+', entry['id']):
            raise InvalidPackage('invalid_id')
        if type(entry['version']) is not int or entry['version'] < 1:
            raise InvalidPackage('invalid_version')
        if not isinstance(entry['category'], str) or not entry['category']:
            raise InvalidPackage('invalid_category')
        relative(entry['relative_path'])
        if type(entry['bytes']) is not int or not 0 < entry['bytes'] <= max_bytes:
            raise InvalidPackage('invalid_entry_size')
        hexadecimal(entry['raw_sha256'])
        if not isinstance(entry['content_base64'], str):
            raise InvalidPackage('invalid_base64')
        try:
            raw = base64.b64decode(entry['content_base64'], validate=True)
            text = raw.decode('utf-8-sig')
        except (UnicodeError, binascii.Error, ValueError) as exc:
            raise InvalidPackage('invalid_entry_encoding') from exc
        if (base64.b64encode(raw).decode('ascii') != entry['content_base64']
                or len(raw) != entry['bytes'] or digest(raw) != entry['raw_sha256']):
            raise InvalidPackage('entry_integrity')
        fm = parse(text)
        try:
            version = int(fm.get('version', ''))
        except (ValueError, TypeError):
            raise InvalidPackage('entry_metadata') from None
        if (fm.get('id') != entry['id'] or version != entry['version']
                or fm.get('category') != entry['category'] or fm.get('estado') != 'aprobado'):
            raise InvalidPackage('entry_metadata')
        scope = selection['scope']
        if any(scope[k] is not None and fm.get(k) != scope[k] for k in ('category', 'area')):
            raise InvalidPackage('scope_mismatch')
        decoded.append((entry, text, fm))
    actual_ids = [entry['id'] for entry in entries]
    if ids != actual_ids or actual_ids != sorted(set(actual_ids)):
        raise InvalidPackage('invalid_selection')
    return decoded


def proposal(source, entry, fm, body, package_sha, render):
    metadata = {k: v for k, v in fm.items()
                if k not in ('id', 'version', 'estado', 'proposed_by') and not k.startswith('import_')}
    metadata.update(proposed_by='import', import_source_project=source['project_id'],
                    import_source_id=entry['id'], import_source_version=str(entry['version']),
                    import_source_path=entry['relative_path'], import_source_sha256=entry['raw_sha256'],
                    import_package_sha256=package_sha, import_source_policy_sha256=source['policy_sha256'])
    if 'proposed_by' in fm:
        metadata['import_source_proposed_by'] = fm['proposed_by']
    return render(metadata, body)


def record_types(record):
    """Typed primitives before equality comparisons or the owner's settlement."""
    if (not isinstance(record, dict) or type(record.get('schema_version')) is not int
            or record['schema_version'] != 1
            or record.get('kind') not in ('import_proposal_intent', 'import_proposal_receipt')):
        raise InvalidPackage('invalid_record_schema')
    for key in ('operation_id', 'request_sha256', 'candidate_sha256'):
        hexadecimal(record.get(key))
    for key in ('source_id', 'candidate_path'):
        if not isinstance(record.get(key), str) or not record[key]:
            raise InvalidPackage('invalid_record_string')
    for key in ('source_project_id', 'destination_project_id'):
        if key in record:
            label(record[key])
    for key in ('source_sha256', 'package_sha256', 'destination_policy_sha256'):
        if key in record:
            hexadecimal(record[key])
    for key in ('staged_identity', 'root_identity', 'candidate_identity'):
        if key in record and (not isinstance(record[key], list) or len(record[key]) != 3
                              or any(type(v) is not int for v in record[key])):
            raise InvalidPackage('invalid_record_identity')
    publication = record.get('record_publication')
    exact(publication, ('staged', 'identity'))
    if (not isinstance(publication['staged'], str) or not isinstance(publication['identity'], list)
            or len(publication['identity']) != 3 or any(type(v) is not int for v in publication['identity'])):
        raise InvalidPackage('invalid_record_publication')
    if 'source_version' in record and (type(record['source_version']) is not int or record['source_version'] < 1):
        raise InvalidPackage('invalid_record_version')
