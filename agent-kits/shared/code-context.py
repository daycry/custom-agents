#!/usr/bin/env python3
"""Query cited AST context from an existing local graph; no extraction or knowledge promotion."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
import sys

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001

MAX_BYTES = 8 * 1024 * 1024
MAX_NODES, MAX_EDGES = 20000, 50000
MAX_MANIFEST_BYTES = 512 * 1024
MAX_SOURCE_FILES = 128
MAX_SOURCE_BYTES = 1024 * 1024
MAX_TOTAL_SOURCE_BYTES = 8 * 1024 * 1024


def _module(name, filename):
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _id(value):
    return isinstance(value, str) and bool(re.fullmatch(r'[a-zA-Z0-9_.:-]{1,128}', value))


class _Unavailable(ValueError):
    def __init__(self, reason, bytes_read=0):
        super().__init__(reason)
        self.reason, self.bytes_read = reason, bytes_read


def _signature(info):
    # Windows lstat ctime is creation time; descriptor ctime is not comparable.
    return (info.st_dev, info.st_ino, stat.S_IFMT(info.st_mode), info.st_size, info.st_mtime_ns, None if os.name == 'nt' else info.st_ctime_ns)


def _read_stable(project, path, cap, reader):
    """Use the shared descriptor primitive; this wrapper only maps diagnostics."""
    # Reserve the primitive's overflow sentinel even on a failed/concurrent read.
    if cap <= 1:
        raise _Unavailable('verification-budget')
    result = reader.read_bytes(project, path.relative_to(project).as_posix(), max_bytes=cap - 1, include_digest=True, include_identity=True)
    if result['status'] != 'ok':
        if result['status'] == 'not_found' and result['bytes'] == 0:
            raise FileNotFoundError()
        reason = {'too_large': 'verification-budget', 'invalid_limit': 'verification-budget', 'redirected_path': 'linked-file', 'not_regular': 'nonregular-file', 'changed_path': 'unstable-read'}.get(result['status'], 'read-unavailable')
        raise _Unavailable(reason, result['bytes'])
    identity, generation = result['identity'], result['generation']
    signature = (*identity, generation[0], generation[1], None if os.name == 'nt' else generation[2])
    return result['data'], signature


def _strict_json(raw, route):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    def constant(_value):
        raise ValueError('non-JSON constant')
    return route._bounded(json.loads(raw.decode('utf-8-sig'), object_pairs_hook=pairs, parse_constant=constant))


def _source_path(value):
    if not isinstance(value, str) or not value or len(value) > 300 or any(c in value for c in '\\:*?"<>|') or any(ord(c) < 32 or ord(c) == 127 for c in value) or PurePosixPath(value).is_absolute():
        raise ValueError('invalid canonical input path')
    parts = value.split('/')
    devices = {'con', 'prn', 'aux', 'nul', 'clock$'} | {prefix + suffix for prefix in ('com', 'lpt') for suffix in '123456789¹²³'}
    if any(not part or part in {'.', '..'} or part.endswith(('.', ' ')) or part.split('.')[0].casefold() in devices for part in parts):
        raise ValueError('invalid canonical input path')
    return value


def _hash(value):
    return isinstance(value, str) and bool(re.fullmatch('[0-9a-f]{64}', value))


def _verify_sources(project, graph, graph_signature, artifact_hash, data, edges, sources_manifest, route, reader):
    verification = {'state': 'unavailable', 'scope': 'declared-inputs', 'authenticated': False, 'total_inputs': 0, 'checked_inputs': 0, 'bytes_read': 0, 'complete': False, 'reason': None}
    availability = {}
    def outcome(status, reason, state=None):
        verification['state'] = state or {'verification-invalid': 'invalid', 'verification-unavailable': 'unavailable', 'artifact-stale': 'stale'}.get(status, 'hashes-match')
        verification['reason'] = reason
        return status, verification, availability
    try:
        if sources_manifest is None:
            manifest = Path(str(graph) + '.sources.json')
        elif isinstance(sources_manifest, (str, os.PathLike)) and str(sources_manifest):
            manifest = Path(sources_manifest)
            manifest = manifest if manifest.is_absolute() else project / manifest
            manifest = manifest.absolute()
        else:
            return outcome('verification-invalid', 'manifest-path')
        if '..' in manifest.parts or not manifest.is_relative_to(project):
            return outcome('verification-invalid', 'manifest-scope')
        _source_path(manifest.relative_to(project).as_posix())
    except (ValueError, OSError):
        return outcome('verification-invalid', 'manifest-path')
    try:
        manifest_raw, manifest_signature = _read_stable(project, manifest, MAX_MANIFEST_BYTES, reader)
    except FileNotFoundError:
        if sources_manifest is None:
            return outcome(None, 'automatic-sidecar-absent', 'legacy-unverified')
        return outcome('verification-unavailable', 'explicit-manifest-missing')
    except _Unavailable as exc:
        return outcome('verification-unavailable', exc.reason)
    try:
        receipt = _strict_json(manifest_raw, route)
        verification['manifest_sha256'] = hashlib.sha256(manifest_raw).hexdigest()
        if not isinstance(receipt, dict) or set(receipt) != {'schema_version', 'artifact_sha256', 'scope', 'inputs'} or type(receipt['schema_version']) is not int or receipt['schema_version'] != 1 or receipt['scope'] != 'declared-inputs' or not _hash(receipt['artifact_sha256']) or receipt['artifact_sha256'] != artifact_hash or not isinstance(receipt['inputs'], list):
            raise ValueError('schema or artifact binding')
        inputs, seen = receipt['inputs'], set()
        # Receipt paths have a portable identity, independent of host filesystem case rules.
        reserved = {path.relative_to(project).as_posix().casefold() for path in (graph, manifest)}
        verification['total_inputs'] = len(inputs)
        declared_bytes = 0
        for item in inputs:
            if not isinstance(item, dict) or set(item) != {'path', 'bytes', 'sha256'} or type(item['bytes']) is not int or item['bytes'] < 0 or not _hash(item['sha256']):
                raise ValueError('input schema')
            value = _source_path(item['path'])
            identity = value.casefold()
            if identity in seen or identity in reserved:
                raise ValueError('duplicate or artifact-aliased input')
            seen.add(identity)
            declared_bytes += item['bytes']
        declared = {item['path'] for item in inputs}
        # Citation coverage is checked before availability or duplicate-ID exclusion.
        records = [node for node in data['nodes'] if isinstance(node, dict) and node.get('_origin') == 'ast' and node.get('file_type') == 'code']
        records.extend(edge for edge in edges if isinstance(edge, dict) and edge.get('_origin') == 'ast' and edge.get('confidence') == 'EXTRACTED')
        for record in records:
            if _source_path(record.get('source_file')) not in declared:
                raise ValueError('undeclared AST citation')
            definition = record.get('definition_file')
            if definition is not None and _source_path(definition) not in declared:
                raise ValueError('undeclared AST definition')
    except (ValueError, UnicodeError, RecursionError):
        return outcome('verification-invalid', 'receipt-schema-binding-or-coverage')
    if len(inputs) > MAX_SOURCE_FILES or declared_bytes > MAX_TOTAL_SOURCE_BYTES or any(item['bytes'] > MAX_SOURCE_BYTES for item in inputs):
        return outcome('verification-unavailable', 'verification-budget')
    stale, partial, reason = False, False, None
    physical = {graph_signature[:2], manifest_signature[:2]}
    for item in inputs:
        remaining = MAX_TOTAL_SOURCE_BYTES - verification['bytes_read']
        if remaining <= 0 and item['bytes']:
            partial, reason = True, 'verification-budget'
            break
        path = project / item['path']
        try:
            raw, signature = _read_stable(project, path, min(MAX_SOURCE_BYTES, max(0, remaining)), reader)
            verification['bytes_read'] += len(raw)
            if signature[:2] in physical:
                return outcome('verification-invalid', 'duplicate-physical-input')
            physical.add(signature[:2])
            verification['checked_inputs'] += 1
            availability[path] = True
            if len(raw) != item['bytes'] or hashlib.sha256(raw).hexdigest() != item['sha256']:
                stale = True
        except FileNotFoundError:
            verification['checked_inputs'] += 1
            stale = True
        except _Unavailable as exc:
            verification['bytes_read'] += exc.bytes_read
            partial, reason = True, exc.reason
            if verification['bytes_read'] > MAX_TOTAL_SOURCE_BYTES:
                break
    try:
        if _signature(graph.lstat()) != graph_signature or _signature(manifest.lstat()) != manifest_signature or any(route._linked(p) for p in (graph, *graph.parents, manifest, *manifest.parents)):
            partial, reason = True, 'artifact-or-receipt-changed-during-verification'
    except OSError:
        partial, reason = True, 'artifact-or-receipt-unavailable'
    verification['complete'] = not partial and verification['checked_inputs'] == len(inputs)
    if stale:
        return outcome('artifact-stale', reason if partial else 'declared-input-changed-or-missing')
    if partial:
        return outcome('verification-unavailable', reason)
    return outcome(None, None)


def _citation(project, value, location, route, availability):
    if not isinstance(value, str) or len(value) > 300 or '\\' in value or PureWindowsPath(value).drive or PurePosixPath(value).is_absolute() or '..' in PurePosixPath(value).parts:
        raise ValueError('source outside project or unsupported path')
    if not isinstance(location, str) or not re.fullmatch(r'L[1-9][0-9]{0,7}(?:-L[1-9][0-9]{0,7})?', location):
        raise ValueError('source location unavailable')
    path = project / value
    if path not in availability:
        try:
            availability[path] = not any(route._linked(p) for p in (path, *path.parents)) and path.is_file()
        except OSError:
            availability[path] = False
    if not availability[path]:
        raise ValueError('source unavailable or linked')
    return value, location


def _selector(symbol, node_id, source_file, label):
    paired = source_file is not None or label is not None
    if sum((symbol is not None, node_id is not None, paired)) != 1:
        raise ValueError('exactly one context selector is required')
    if symbol is not None:
        if not isinstance(symbol, str) or not symbol.strip() or len(symbol) > 200:
            raise ValueError('invalid symbol')
        return 'symbol'
    if node_id is not None:
        if not _id(node_id):
            raise ValueError('invalid node ID')
        return 'node-id'
    if not isinstance(label, str) or not label.strip() or len(label) > MAX_BYTES:
        raise ValueError('invalid exact label')
    if not isinstance(source_file, str) or not source_file.strip() or len(source_file) > 300 or '\0' in source_file or '\\' in source_file or PureWindowsPath(source_file).drive or PurePosixPath(source_file).is_absolute() or '..' in PurePosixPath(source_file).parts:
        raise ValueError('invalid exact source path')
    return 'source-label'


def query_graph(project, graph, symbol=None, limit=6, *, node_id=None, source_file=None, label=None, sources_manifest=None):
    selector = _selector(symbol, node_id, source_file, label)
    if type(limit) is not int or not 1 <= limit <= 50:
        raise ValueError('invalid context limit')
    if any(str(path).startswith(('\\\\', '//')) for path in (project, graph)):
        raise ValueError('remote or device project path')
    project, graph = Path(project).absolute(), Path(graph).absolute()
    route = _module('context_capability_route', 'capability-route.py')
    if not project.is_dir() or any(route._linked(p) for p in (project, *project.parents)) or '..' in graph.parts or not graph.is_relative_to(project):
        raise ValueError('project or graph outside allowed scope')
    _source_path(graph.relative_to(project).as_posix())
    reader = _module('context_local_read', 'local-read.py')
    try:
        raw, graph_signature = _read_stable(project, graph, MAX_BYTES, reader)
    except _Unavailable as exc:
        return {'version': 1, 'artifact_sha256': None, 'coverage': 'unknown',
                'freshness': 'unverified', 'knowledge_status': 'unapproved-context',
                'verification': {'state': 'unavailable', 'scope': 'declared-inputs',
                    'authenticated': False, 'total_inputs': 0, 'checked_inputs': 0,
                    'bytes_read': exc.bytes_read, 'complete': False, 'reason': exc.reason},
                'selector': {'kind': selector},
                'selection': 'discovery' if selector == 'symbol' else 'exact',
                'status': 'verification-unavailable', 'completeness': 'partial',
                'reason': exc.reason, 'truncated': False, 'nodes': [], 'edges': [],
                'warnings': ['graph read did not permit context']}
    artifact_hash = hashlib.sha256(raw).hexdigest()
    data = _strict_json(raw, route)
    if not isinstance(data, dict) or not isinstance(data.get('nodes'), list):
        raise ValueError('unsupported graph schema')
    edges = data.get('links', data.get('edges', []))
    if not isinstance(edges, list) or len(data['nodes']) > MAX_NODES or len(edges) > MAX_EDGES:
        raise ValueError('graph exceeds collection limits')
    verification_status, verification, availability = _verify_sources(project, graph, graph_signature, artifact_hash, data, edges, sources_manifest, route, reader)
    freshness = 'verified-declared-inputs' if verification['state'] == 'hashes-match' else ('stale' if verification_status == 'artifact-stale' else 'unverified')
    envelope = {'version': 1, 'artifact_sha256': artifact_hash, 'coverage': 'unknown', 'freshness': freshness, 'knowledge_status': 'unapproved-context', 'directed': data.get('directed') is True, 'verification': verification, 'selector': {'kind': selector}, 'selection': 'discovery' if selector == 'symbol' else 'exact', 'completeness': 'complete', 'reason': None}
    if verification_status:
        return envelope | {'status': verification_status, 'completeness': 'complete' if verification['complete'] else 'partial', 'reason': verification['reason'], 'truncated': False, 'nodes': [], 'edges': [], 'warnings': ['declared-input verification did not permit context']}
    redactor = _module('context_redactor', 'redact.py')
    nodes, identities, warnings = {}, {}, []
    if verification['state'] == 'legacy-unverified':
        warnings.append('automatic sources receipt absent; artifact freshness is unverified')
    counts = Counter(node.get('id') for node in data['nodes'] if isinstance(node, dict) and _id(node.get('id')))
    duplicates = {key for key, count in counts.items() if count > 1}
    for node in data['nodes']:
        try:
            if not isinstance(node, dict) or node.get('_origin') != 'ast' or node.get('file_type') != 'code' or not _id(node.get('id')) or node['id'] in duplicates or not isinstance(node.get('label'), str):
                raise ValueError('unsupported node')
            source, location = _citation(project, node.get('source_file'), node.get('source_location'), route, availability)
            identities[node['id']] = (source, node['label'])
            nodes[node['id']] = {'id': node['id'], 'label': redactor.redactar(node['label'])[:240], 'source_file': redactor.redactar(source), 'source_location': location}
        except (OSError, ValueError):
            warnings.append('unsupported, duplicate or uncited node excluded')
    if selector == 'symbol':
        # Legacy symbol lookup deliberately retains its displayed-label substring contract.
        seeds = sorted(key for key, node in nodes.items() if symbol.casefold() in node['label'].casefold())
    elif selector == 'node-id':
        seeds = [node_id] if node_id in nodes else []
    else:
        seeds = sorted(key for key, identity in identities.items() if identity == (source_file, label))
    ambiguous = selector == 'source-label' and len(seeds) > 1
    if ambiguous:
        warnings.append('ambiguous source/label selector has multiple node IDs')
        seeds = []
    selected, valid_edges = set(seeds), []
    for edge in edges:
        try:
            if not isinstance(edge, dict) or edge.get('_origin') != 'ast' or edge.get('confidence') != 'EXTRACTED' or not _id(edge.get('source')) or not _id(edge.get('target')) or not _id(edge.get('relation')) or edge['source'] not in nodes or edge['target'] not in nodes:
                raise ValueError('unsupported edge')
            source, location = _citation(project, edge.get('source_file'), edge.get('source_location'), route, availability)
            if edge['source'] in seeds or edge['target'] in seeds:
                selected.update((edge['source'], edge['target']))
                valid_edges.append({key: edge[key] for key in ('source', 'target', 'relation')} | {'source_file': redactor.redactar(source), 'source_location': location})
        except (OSError, ValueError):
            warnings.append('unsupported or uncited relation excluded')
    chosen = (seeds + sorted(selected - set(seeds)))[:limit]
    envelope['selection'] = 'ambiguous' if ambiguous else envelope['selection']
    if len(selected) > limit:
        envelope.update(completeness='partial', reason='result_budget')
    return envelope | {'status': 'ambiguous' if ambiguous else ('matches' if seeds else 'no-match-in-artifact'), 'truncated': len(selected) > limit, 'nodes': [nodes[key] for key in chosen], 'edges': sorted((edge for edge in valid_edges if edge['source'] in chosen and edge['target'] in chosen), key=lambda edge: (edge['source'], edge['target'], edge['relation'])), 'warnings': sorted(set(warnings))}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path('.'))
    parser.add_argument('--graph', type=Path, default=Path('graphify-out/graph.json'))
    selectors = parser.add_mutually_exclusive_group(required=True)
    selectors.add_argument('--symbol')
    selectors.add_argument('--node-id')
    selectors.add_argument('--source-file')
    parser.add_argument('--label')
    parser.add_argument('--sources-manifest', type=Path)
    parser.add_argument('--limit', type=int, default=6)
    args = parser.parse_args(argv)
    if (args.source_file is None) != (args.label is None):
        parser.error('--source-file and --label must be used together')
    graph = args.graph if args.graph.is_absolute() else args.project / args.graph
    try:
        result = query_graph(args.project, graph, args.symbol, args.limit, node_id=args.node_id, source_file=args.source_file, label=args.label, sources_manifest=args.sources_manifest)
        redactor = _module('context_cli_redactor', 'redact.py')
        print(redactor.redactar(json.dumps(result, ensure_ascii=False)))
        return 2 if result['status'] in {'artifact-stale', 'verification-invalid', 'verification-unavailable'} else 0
    except (OSError, ValueError, UnicodeError, RecursionError, ImportError, SyntaxError, AttributeError, TypeError):
        print('code context unavailable: check artifact, sources and bundled modules; local knowledge remains available', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
