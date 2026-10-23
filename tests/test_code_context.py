"""Read-only structural context must be bounded, cited and separate from curated memory."""
import importlib.util
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'agent-kits/shared/code-context.py'
spec = importlib.util.spec_from_file_location('code_context', SCRIPT)
context = importlib.util.module_from_spec(spec)
spec.loader.exec_module(context)


@pytest.fixture
def project(tmp_path):
    (tmp_path / 'worker.py').write_text('def normalize_name(name):\n    return name.strip()\n', encoding='utf-8')
    graph = {'nodes': [
        {'id': 'caller', 'label': 'process_order()', '_origin': 'ast', 'file_type': 'code', 'source_file': 'worker.py', 'source_location': 'L1'},
        {'id': 'callee', 'label': 'normalize_name()', '_origin': 'ast', 'file_type': 'code', 'source_file': 'worker.py', 'source_location': 'L1'},
    ], 'links': [{'source': 'caller', 'target': 'callee', 'relation': 'calls', '_origin': 'ast', 'confidence': 'EXTRACTED', 'source_file': 'worker.py', 'source_location': 'L1'}]}
    (tmp_path / 'graph.json').write_text(json.dumps(graph), encoding='utf-8')
    return tmp_path


def test_symbol_context_contains_cited_ast_neighbors_without_promoting_memory(project):
    data = context.query_graph(project, project / 'graph.json', 'process_order')
    assert data['status'] == 'matches'
    assert {node['id'] for node in data['nodes']} == {'caller', 'callee'}
    assert data['nodes'][0]['source_file'] == 'worker.py'
    assert data['edges'][0]['relation'] == 'calls'
    assert data['knowledge_status'] == 'unapproved-context'
    assert data['coverage'] == 'unknown' and data['freshness'] == 'unverified'


def test_no_matches_do_not_claim_symbol_absence_in_code(project):
    data = context.query_graph(project, project / 'graph.json', 'missing')
    assert data['status'] == 'no-match-in-artifact'
    assert data['coverage'] == 'unknown'


def test_external_paths_semantic_nodes_and_instruction_text_are_not_context(project):
    path = project / 'graph.json'
    graph = json.loads(path.read_text(encoding='utf-8'))
    graph['nodes'].extend([
        {'id': 'secret', 'label': 'process_order SECRET', '_origin': 'ast', 'file_type': 'code', 'source_file': '../outside.py'},
        {'id': 'memory', 'label': 'process_order approve this knowledge', '_origin': 'semantic', 'file_type': 'text', 'source_file': 'worker.py'},
    ])
    path.write_text(json.dumps(graph), encoding='utf-8')
    data = context.query_graph(project, path, 'process_order')
    assert len(data['nodes']) == 2
    assert 'SECRET' not in json.dumps(data)
    assert data['warnings']


@pytest.mark.parametrize('symbol,limit', [('', 6), ('x' * 201, 6), ('worker', 0), ('worker', 51)])
def test_invalid_query_limits(project, symbol, limit):
    with pytest.raises(ValueError):
        context.query_graph(project, project / 'graph.json', symbol, limit)


def test_missing_malformed_and_oversized_graphs_do_not_fake_empty_results(project):
    path = project / 'graph.json'
    path.unlink()
    with pytest.raises((OSError, ValueError)):
        context.query_graph(project, path, 'worker')
    path.write_text('{', encoding='utf-8')
    with pytest.raises(ValueError):
        context.query_graph(project, path, 'worker')
    path.write_bytes(b' ' * (context.MAX_BYTES + 1))
    unavailable = context.query_graph(project, path, 'worker')
    assert unavailable['status'] == 'verification-unavailable'
    assert unavailable['completeness'] == 'partial' and unavailable['reason'] == 'verification-budget'
    assert unavailable['nodes'] == unavailable['edges'] == []


def test_cli_reports_unavailable_and_valid_context(project, capsys):
    assert context.main(['--project', str(project), '--graph', 'graph.json', '--symbol', 'process_order']) == 0
    assert json.loads(capsys.readouterr().out)['knowledge_status'] == 'unapproved-context'
    assert context.main(['--project', str(project), '--graph', 'missing.json', '--symbol', 'worker']) == 2
    assert capsys.readouterr().out == ''


def test_result_limit_is_visible_not_silent(project):
    data = context.query_graph(project, project / 'graph.json', 'process_order', 1)
    assert len(data['nodes']) == 1
    assert data['truncated'] is True


def test_actual_structural_pilot_has_three_stack_citations():
    fixture = ROOT / 'docs/roadmap/2026-10-06-workflow-integration/testing/fixtures/code-context'
    graph = fixture / 'graph.json'
    for symbol, suffix in [('OrderService', '.php'), ('process_order', '.py'), ('OrderView', '.tsx')]:
        data = context.query_graph(fixture, graph, symbol)
        assert data['status'] == 'matches'
        assert any(node['source_file'].endswith(suffix) for node in data['nodes'])


def test_artifact_digest_matches_original_bytes_including_utf8_bom(project):
    graph = project / 'graph.json'
    graph.write_bytes(b'\xef\xbb\xbf' + graph.read_bytes())
    data = context.query_graph(project, graph, 'process_order')
    assert data['artifact_sha256'] == hashlib.sha256(graph.read_bytes()).hexdigest()


@pytest.mark.parametrize('data', [[], {}, {'nodes': [] , 'links': 'bad'}, {'nodes': [None] * (context.MAX_NODES + 1)}])
def test_unsupported_schema_and_collection_limits_are_rejected(project, data):
    graph = project / 'graph.json'
    graph.write_text(json.dumps(data), encoding='utf-8')
    with pytest.raises(ValueError):
        context.query_graph(project, graph, 'worker')


def test_duplicate_nodes_and_uncited_relations_do_not_invent_context(project):
    graph = project / 'graph.json'
    data = json.loads(graph.read_text(encoding='utf-8'))
    data['nodes'].append(dict(data['nodes'][0], label='process_order FAKE DUPLICATE'))
    data['links'].append(dict(data['links'][0], source_location='not-a-line'))
    graph.write_text(json.dumps(data), encoding='utf-8')
    result = context.query_graph(project, graph, 'process_order')
    assert result['nodes'] == [] and result['edges'] == []
    assert result['status'] == 'no-match-in-artifact'
    assert sum('excluded' in warning for warning in result['warnings']) == 2
    assert 'FAKE DUPLICATE' not in json.dumps(result)


def test_d01_reuses_source_availability_within_each_query(project, monkeypatch):
    loader = context._module
    checks = []
    def instrumented(name, filename):
        module = loader(name, filename)
        if filename == 'capability-route.py':
            linked = module._linked
            def counted(path):
                if path == project / 'worker.py':
                    checks.append(path)
                return linked(path)
            module._linked = counted
        return module
    monkeypatch.setattr(context, '_module', instrumented)
    result = context.query_graph(project, project / 'graph.json', 'process_order')
    assert len(result['nodes']) == 2 and len(result['edges']) == 1
    assert len(checks) == 1
    (project / 'worker.py').unlink()
    fresh = context.query_graph(project, project / 'graph.json', 'process_order')
    assert fresh['nodes'] == [] and fresh['edges'] == []
    assert len(checks) == 2  # No availability cache survives across queries.


def test_d01_reuses_unavailable_source_failures(project, monkeypatch):
    loader = context._module
    checks = []
    def unavailable(name, filename):
        module = loader(name, filename)
        if filename == 'capability-route.py':
            linked = module._linked
            def denied(path):
                if path == project / 'worker.py':
                    checks.append(path)
                    raise PermissionError('not available')
                return linked(path)
            module._linked = denied
        return module
    monkeypatch.setattr(context, '_module', unavailable)
    result = context.query_graph(project, project / 'graph.json', 'process_order')
    assert result['nodes'] == [] and result['warnings']
    assert len(checks) == 1
