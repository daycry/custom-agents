#!/usr/bin/env python3
"""Query cited AST context from an existing local graph; no extraction or knowledge promotion."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import sys

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001

MAX_BYTES = 8 * 1024 * 1024
MAX_NODES, MAX_EDGES = 20000, 50000


def _module(name, filename):
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _id(value):
    return isinstance(value, str) and bool(re.fullmatch(r'[a-zA-Z0-9_.:-]{1,128}', value))


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


def query_graph(project, graph, symbol, limit=6):
    if not isinstance(symbol, str) or not symbol.strip() or len(symbol) > 200 or type(limit) is not int or not 1 <= limit <= 50:
        raise ValueError('invalid symbol or context limit')
    project, graph = Path(project).absolute(), Path(graph).absolute()
    route = _module('context_capability_route', 'capability-route.py')
    if not project.is_dir() or any(route._linked(p) for p in (project, *project.parents)) or '..' in graph.parts or not graph.is_relative_to(project):
        raise ValueError('project or graph outside allowed scope')
    raw = route._read(graph, MAX_BYTES, as_bytes=True)
    data = route._bounded(json.loads(raw.decode('utf-8-sig')))
    if not isinstance(data, dict) or not isinstance(data.get('nodes'), list):
        raise ValueError('unsupported graph schema')
    edges = data.get('links', data.get('edges', []))
    if not isinstance(edges, list) or len(data['nodes']) > MAX_NODES or len(edges) > MAX_EDGES:
        raise ValueError('graph exceeds collection limits')
    redactor = _module('context_redactor', 'redact.py')
    nodes, warnings, availability = {}, [], {}
    for node in data['nodes']:
        try:
            if not isinstance(node, dict) or node.get('_origin') != 'ast' or node.get('file_type') != 'code' or not _id(node.get('id')) or not isinstance(node.get('label'), str):
                raise ValueError('unsupported node')
            source, location = _citation(project, node.get('source_file'), node.get('source_location'), route, availability)
            if node['id'] in nodes:
                raise ValueError('duplicate node')
            nodes[node['id']] = {'id': node['id'], 'label': redactor.redactar(node['label'])[:240], 'source_file': redactor.redactar(source), 'source_location': location}
        except (OSError, ValueError):
            warnings.append('unsupported, duplicate or uncited node excluded')
    seeds = sorted(key for key, node in nodes.items() if symbol.casefold() in node['label'].casefold())
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
    return {'version': 1, 'status': 'matches' if seeds else 'no-match-in-artifact', 'artifact_sha256': hashlib.sha256(raw).hexdigest(), 'coverage': 'unknown', 'freshness': 'unverified', 'knowledge_status': 'unapproved-context', 'directed': data.get('directed') is True, 'truncated': len(selected) > limit, 'nodes': [nodes[key] for key in chosen], 'edges': sorted((edge for edge in valid_edges if edge['source'] in chosen and edge['target'] in chosen), key=lambda edge: (edge['source'], edge['target'], edge['relation'])), 'warnings': sorted(set(warnings))}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path('.'))
    parser.add_argument('--graph', type=Path, default=Path('graphify-out/graph.json'))
    parser.add_argument('--symbol', required=True)
    parser.add_argument('--limit', type=int, default=6)
    args = parser.parse_args(argv)
    graph = args.graph if args.graph.is_absolute() else args.project / args.graph
    try:
        result = query_graph(args.project, graph, args.symbol, args.limit)
        redactor = _module('context_cli_redactor', 'redact.py')
        print(redactor.redactar(json.dumps(result, ensure_ascii=False)))
        return 0
    except (OSError, ValueError, UnicodeError, RecursionError):
        print('code context unavailable: check artifact, sources and bundled modules; local knowledge remains available', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
