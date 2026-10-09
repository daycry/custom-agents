"""Exact selectors must preserve raw identities and fail closed on collisions."""
import json
import pytest
from test_code_context import context, project


def change(project, nodes, links=None):
    data = json.loads((project/'graph.json').read_text())
    data['nodes'] = nodes
    if links is not None: data['links'] = links
    (project/'graph.json').write_text(json.dumps(data), encoding='utf8')


def node(ident, label='same()', source='worker.py', **extra):
    return dict(id=ident, label=label, source_file=source, source_location='L1', _origin='ast', file_type='code', **extra)


def test_node_id_selects_exact_case_sensitive_identity_and_one_hop(project):
    change(project, [node('ns:caller'), node('NS:caller'), node('target', 'neighbor()')], [dict(source='ns:caller', target='target', relation='calls', _origin='ast', confidence='EXTRACTED', source_file='worker.py', source_location='L1')])
    data=context.query_graph(project, project/'graph.json', node_id='ns:caller')
    assert [x['id'] for x in data['nodes']] == ['ns:caller', 'target']
    assert data['edges'][0]['source']=='ns:caller'
    assert context.query_graph(project, project/'graph.json', node_id='ns:CALLER')['status']=='no-match-in-artifact'


def test_pair_uses_full_raw_label_before_truncation_and_exact_source(project):
    prefix='shared_'+('x'*260)
    change(project, [node('first', prefix+'first'), node('second', prefix+'second')], [])
    data=context.query_graph(project, project/'graph.json', source_file='worker.py', label=prefix+'second')
    assert [x['id'] for x in data['nodes']]==['second']
    assert len(data['nodes'][0]['label'])==240
    assert context.query_graph(project, project/'graph.json', source_file='./worker.py', label=prefix+'second')['nodes']==[]
    assert context.query_graph(project, project/'graph.json', source_file='worker.py', label=(prefix+'second').upper())['nodes']==[]


def test_pair_uses_raw_identity_before_redaction_without_leaking_it(project):
    label='token = Abc123456789XYZ1'
    change(project, [node('secretlabel', label)], [])
    result=context.query_graph(project, project/'graph.json', source_file='worker.py', label=label)
    assert [x['id'] for x in result['nodes']]==['secretlabel']
    assert 'Abc123456789XYZ1' not in json.dumps(result)


def test_pair_ambiguity_has_empty_context_even_with_limit_one(project):
    change(project, [node('first'), node('second'), node('neighbor', 'different()')], [dict(source='first', target='neighbor', relation='calls', _origin='ast', confidence='EXTRACTED', source_file='worker.py', source_location='L1')])
    result=context.query_graph(project, project/'graph.json', source_file='worker.py', label='same()', limit=1)
    assert result['status']=='ambiguous'
    assert result['nodes']==[] and result['edges']==[]
    assert result['truncated'] is False


@pytest.mark.parametrize('unsupported_first', [False, True])
def test_duplicate_id_invalidates_all_occurrences_and_incident_edges(project, unsupported_first):
    good=node('collision', 'same()')
    bad=dict(good, _origin='semantic', file_type='text')
    duplicates=[bad,good] if unsupported_first else [good,bad]
    edge=dict(source='anchor', target='collision', relation='calls', _origin='ast', confidence='EXTRACTED', source_file='worker.py', source_location='L1')
    change(project, duplicates+[node('anchor','anchor()')], [edge])
    result=context.query_graph(project, project/'graph.json', 'anchor')
    assert [x['id'] for x in result['nodes']]==['anchor']
    assert result['edges']==[]
    assert context.query_graph(project, project/'graph.json', node_id='collision')['nodes']==[]


@pytest.mark.parametrize('kwargs', [{}, {'symbol':'x','node_id':'caller'}, {'node_id':''}, {'node_id':12}, {'node_id':'../caller'}, {'source_file':'worker.py'}, {'label':'same()'}, {'source_file':'worker.py','label':' '}, {'source_file':'../worker.py','label':'same()'}, {'source_file':'C:/worker.py','label':'same()'}, {'source_file':'worker\\x.py','label':'same()'}, {'source_file':12,'label':'same()'}, {'symbol':'x','source_file':'worker.py','label':'same()'}])
def test_selector_validation_rejects_incomplete_conflicting_or_unsafe_inputs(project, kwargs):
    with pytest.raises(ValueError): context.query_graph(project, project/'graph.json', **kwargs)


def test_cli_exact_modes_dispatch_to_node_and_pair(project, capsys):
    args=['--project',str(project),'--graph','graph.json']
    assert context.main(args+['--node-id','caller'])==0
    assert json.loads(capsys.readouterr().out)['nodes'][0]['id']=='caller'
    assert context.main(args+['--source-file','worker.py','--label','normalize_name()'])==0
    assert json.loads(capsys.readouterr().out)['nodes'][0]['id']=='callee'


@pytest.mark.parametrize('args', [[], ['--source-file','worker.py'], ['--label','x'], ['--symbol','x','--node-id','caller'], ['--node-id','caller','--label','x']])
def test_cli_requires_exactly_one_complete_selector_mode(project, args):
    with pytest.raises(SystemExit) as error:
        context.main(['--project',str(project),'--graph','graph.json']+args)
    assert error.value.code==2


def test_legacy_symbol_keeps_casefold_substring_and_positional_limit(project):
    change(project,[node('first','Namespace.SAME()'),node('second','same_extra()')],[])
    result=context.query_graph(project,project/'graph.json','sAmE',1)
    assert result['nodes'][0]['id']=='first' and result['truncated'] is True
    assert context.query_graph(project,project/'graph.json','first')['status']=='no-match-in-artifact'


def test_exact_source_with_nul_is_rejected_before_artifact_matching(project):
    with pytest.raises(ValueError):
        context.query_graph(project, project/'graph.json', source_file='worker.py\0', label='process_order()')
