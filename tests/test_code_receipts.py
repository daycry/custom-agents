"""Producer-declared bytes constrain context; this suite uses wholly owned fixtures."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
from types import SimpleNamespace
import pytest
from test_code_context import context, project

def receipt(project, paths=('worker.py',)):
    graph=project/'graph.json'
    value={'schema_version':1,'artifact_sha256':hashlib.sha256(graph.read_bytes()).hexdigest(),'scope':'declared-inputs','inputs':[{'path':name,'bytes':len((project/name).read_bytes()),'sha256':hashlib.sha256((project/name).read_bytes()).hexdigest()} for name in paths]}
    path=Path(str(graph)+'.sources.json')
    path.write_text(json.dumps(value),encoding='utf8')
    return path,value

def query(project, **kwargs):
    return context.query_graph(project, project/'graph.json', 'process_order', **kwargs)

def test_legacy_auto_absent_is_warned_but_context_remains(project):
    result=query(project)
    assert result['nodes'] and result['freshness']=='unverified'
    assert result['verification']['state']=='legacy-unverified'


@pytest.mark.parametrize('status', ['changed_path', 'unreadable', 'too_large'])
def test_initial_graph_read_failure_is_partial_without_context(project, monkeypatch, status):
    original = context._module
    observed = []
    def read(root, relative, **kwargs):
        observed.append(relative)
        return {'status': status, 'data': None, 'bytes': 0}
    def load(name, filename):
        return SimpleNamespace(read_bytes=read) if filename == 'local-read.py' else original(name, filename)
    monkeypatch.setattr(context, '_module', load)
    result = query(project)
    assert result['status'] == 'verification-unavailable'
    assert result['completeness'] == 'partial' and result['artifact_sha256'] is None
    assert result['freshness'] == 'unverified' and result['verification']['complete'] is False
    assert result['nodes'] == result['edges'] == [] and observed == ['graph.json']
    assert result['warnings']

def test_bound_receipt_rehashes_every_declared_raw_input_each_query(project,monkeypatch):
    (project/'unused.cfg').write_bytes(b'\xef\xbb\xbfraw\r\n')
    receipt(project,('worker.py','unused.cfg'))
    original=os.open
    reads=[]
    def observed(path,*args,**kwargs):
        if Path(path) in {project/'worker.py',project/'unused.cfg'}:reads.append(Path(path).name)
        return original(path,*args,**kwargs)
    monkeypatch.setattr(os,'open',observed)
    result=query(project)
    assert result['freshness']=='verified-declared-inputs'
    assert result['verification']['checked_inputs']==result['verification']['total_inputs']==2
    assert reads==['worker.py','unused.cfg']
    assert result['coverage']=='unknown' and result['knowledge_status']=='unapproved-context'
    reads.clear(); query(project)
    assert reads==['worker.py','unused.cfg']

def test_same_length_same_mtime_input_edit_is_stale(project):
    receipt(project);path=project/'worker.py';old=path.stat();raw=path.read_bytes()
    path.write_bytes(raw.replace(b'name',b'NAME'));os.utime(path,ns=(old.st_atime_ns,old.st_mtime_ns))
    result=query(project)
    assert result['status']=='artifact-stale' and result['freshness']=='stale'
    assert result['nodes']==result['edges']==[]

@pytest.mark.parametrize('missing',[False,True])
def test_unselected_declared_change_or_missing_is_stale(project,missing):
    path=project/'unused.cfg';path.write_bytes(b'one');receipt(project,('worker.py','unused.cfg'))
    if missing:path.unlink()
    else:path.write_bytes(b'two')
    result=query(project)
    assert result['status']=='artifact-stale' and result['nodes']==[]
    assert result['verification']['checked_inputs']==2

def test_exact_artifact_bytes_and_bom_binding_not_normalized(project):
    receipt(project)
    graph=project/'graph.json';graph.write_bytes(b'\xef\xbb\xbf'+graph.read_bytes())
    result=query(project)
    assert result['status']=='verification-invalid' and result['nodes']==[]
    receipt(project)
    assert query(project)['freshness']=='verified-declared-inputs'

@pytest.mark.parametrize('variant',['version','bool-version','scope','extra','bool-bytes','negative-bytes','hash-uppercase','hash-bad','item-extra','duplicate-path','case-collision','omitted-node','omitted-edge','alias-graph'])
def test_strict_schema_and_citation_coverage_fail_closed(project,variant):
    path,data=receipt(project)
    if variant=='version':data['schema_version']=2
    elif variant=='bool-version':data['schema_version']=True
    elif variant=='scope':data['scope']='all-project'
    elif variant=='extra':data['producer']='invented'
    elif variant=='bool-bytes':data['inputs'][0]['bytes']=True
    elif variant=='negative-bytes':data['inputs'][0]['bytes']=-1
    elif variant=='hash-uppercase':data['inputs'][0]['sha256']=data['inputs'][0]['sha256'].upper()
    elif variant=='hash-bad':data['artifact_sha256']='x'*64
    elif variant=='item-extra':data['inputs'][0]['mtime']=123
    elif variant=='duplicate-path':data['inputs'].append(dict(data['inputs'][0]))
    elif variant=='case-collision':data['inputs'].append(dict(data['inputs'][0],path='WORKER.py'))
    elif variant=='omitted-node':data['inputs']=[]
    elif variant=='omitted-edge':
        graph=json.loads((project/'graph.json').read_text());graph['links'][0]['source_file']='uncited.py';(project/'graph.json').write_text(json.dumps(graph));data['artifact_sha256']=hashlib.sha256((project/'graph.json').read_bytes()).hexdigest()
    elif variant=='alias-graph':data['inputs'].append({'path':'graph.json','bytes':0,'sha256':'0'*64})
    path.write_text(json.dumps(data))
    result=query(project)
    assert result['status']=='verification-invalid' and result['nodes']==result['edges']==[]

@pytest.mark.parametrize('raw',['{','{"schema_version":1,"schema_version":1}', '{"schema_version":NaN}'])
def test_malformed_duplicate_keys_and_nonjson_numbers_are_invalid(project,raw):
    path,_=receipt(project);path.write_text(raw)
    result=query(project)
    assert result['status']=='verification-invalid' and result['nodes']==[]

@pytest.mark.parametrize('name', ['WORKER.py', 'GRAPH.json', 'GRAPH.json.sources.json'])
def test_portable_receipt_path_collisions_rejected_before_source_reads(project, monkeypatch, name):
    path, data = receipt(project)
    data['inputs'].append(dict(data['inputs'][0], path=name))
    path.write_text(json.dumps(data), encoding='utf-8')
    original = context._read_stable
    reads = []
    def observed(root, target, cap, reader):
        reads.append(target.relative_to(root).as_posix())
        return original(root, target, cap, reader)
    monkeypatch.setattr(context, '_read_stable', observed)
    result = query(project)
    assert result['status'] == 'verification-invalid'
    assert result['nodes'] == result['edges'] == []
    assert result['verification']['checked_inputs'] == 0
    assert reads == ['graph.json', 'graph.json.sources.json']


def test_missing_cited_source_cannot_hide_coverage_omission(project):
    path,data=receipt(project);data['inputs']=[];path.write_text(json.dumps(data));(project/'worker.py').unlink()
    assert query(project)['status']=='verification-invalid'

@pytest.mark.parametrize('name',['../outside.py','/absolute.py','C:/outside.py','\\\\host\\file','a\\b.py','a/../b.py','./worker.py','a//b.py','worker.py:stream','CON.py','LPT1','a./b.py','a /b.py','bad\0.py'])
def test_noncanonical_or_windows_aliased_input_paths_invalid(project,name):
    path,data=receipt(project);data['inputs'][0]['path']=name;path.write_text(json.dumps(data))
    result=query(project)
    assert result['status']=='verification-invalid' and result['nodes']==[]

def test_explicit_missing_manifest_unavailable_without_legacy_fallback(project,capsys):
    result=query(project,sources_manifest=project/'missing.sources.json')
    assert result['status']=='verification-unavailable' and result['nodes']==[]
    assert context.main(['--project',str(project),'--graph','graph.json','--symbol','process_order','--sources-manifest','missing.sources.json'])==2
    assert json.loads(capsys.readouterr().out)['status']=='verification-unavailable'

def test_explicit_manifest_outside_project_invalid_without_read(project):
    assert query(project,sources_manifest=project.parent/'outside.json')['status']=='verification-invalid'

@pytest.mark.parametrize('cap,value',[('MAX_SOURCE_FILES',0),('MAX_SOURCE_BYTES',1),('MAX_TOTAL_SOURCE_BYTES',1),('MAX_MANIFEST_BYTES',1)])
def test_receipt_budgets_partial_unavailable_not_verified(project,monkeypatch,cap,value):
    receipt(project);monkeypatch.setattr(context,cap,value,raising=False)
    result=query(project)
    assert result['status']=='verification-unavailable' and result['nodes']==[]
    assert result['verification']['complete'] is False

def test_actual_underdeclared_oversized_input_bounded_as_unknown(project,monkeypatch):
    path,data=receipt(project);data['inputs'][0]['bytes']=0;path.write_text(json.dumps(data));monkeypatch.setattr(context,'MAX_SOURCE_BYTES',2,raising=False)
    result=query(project)
    assert result['status']=='verification-unavailable' and result['nodes']==[]

@pytest.mark.parametrize('stale_first',[False,True])
def test_permission_unknown_preserves_any_proved_stale(project,monkeypatch,stale_first):
    (project/'unused.cfg').write_bytes(b'one');receipt(project,('worker.py','unused.cfg'))
    if stale_first:(project/'worker.py').write_bytes(b'changed')
    original=os.open
    def denied(path,*args,**kwargs):
        if Path(path)==project/'unused.cfg':raise PermissionError('own controlled denial')
        return original(path,*args,**kwargs)
    monkeypatch.setattr(os,'open',denied)
    result=query(project)
    assert result['status']==('artifact-stale' if stale_first else 'verification-unavailable')
    assert result['nodes']==[] and result['verification']['complete'] is False

def test_read_instability_does_not_certify_prechange_bytes(project,monkeypatch):
    receipt(project);target=project/'worker.py';original=Path.open
    opened=os.open;fdopen=os.fdopen;targets=set()
    class Changing:
        def __init__(self,handle):self.handle=handle
        def __enter__(self):self.handle.__enter__();return self
        def __exit__(self,*args):return self.handle.__exit__(*args)
        def fileno(self):return self.handle.fileno()
        def read(self,size):
            raw=self.handle.read(size)
            with original(target,'wb') as out:out.write(b'changed')
            return raw
    def observe(path,*args,**kwargs):
        fd=opened(path,*args,**kwargs)
        if Path(path)==target:targets.add(fd)
        return fd
    def unstable(fd,*args,**kwargs):
        handle=fdopen(fd,*args,**kwargs)
        return Changing(handle) if fd in targets else handle
    monkeypatch.setattr(os,'open',observe);monkeypatch.setattr(os,'fdopen',unstable)
    result=query(project)
    assert result['status']=='verification-unavailable' and result['nodes']==[]

def test_empty_receipt_only_valid_for_graph_without_cited_ast_sources(project):
    (project/'graph.json').write_text(json.dumps({'nodes':[],'links':[]}));receipt(project,())
    result=query(project)
    assert result['freshness']=='verified-declared-inputs' and result['status']=='no-match-in-artifact'

def test_ambiguous_pair_still_reports_verified_freshness_without_context(project):
    graph=json.loads((project/'graph.json').read_text());graph['nodes'][1]['label']=graph['nodes'][0]['label'];(project/'graph.json').write_text(json.dumps(graph));receipt(project)
    result=context.query_graph(project,project/'graph.json',source_file='worker.py',label='process_order()',limit=1)
    assert result['status']=='ambiguous' and result['freshness']=='verified-declared-inputs'
    assert result['nodes']==result['edges']==[]

@pytest.mark.parametrize('kind',['missing','syntax','callable'])
def test_partial_helper_bundle_fails_safely(project,tmp_path,capsys,kind):
    bundle=tmp_path/'partial';bundle.mkdir()
    origin=Path(context.__file__).parent
    for name in ('code-context.py','capability-route.py','redact.py','local-read.py'):shutil.copyfile(origin/name,bundle/name)
    helper=bundle/'capability-route.py'
    if kind=='missing':helper.unlink()
    elif kind=='syntax':helper.write_text('invalid python !')
    else:helper.write_text('_linked = None')
    spec=importlib.util.spec_from_file_location('partial_receipt_reader',bundle/'code-context.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    assert module.main(['--project',str(project),'--graph','graph.json','--symbol','process_order'])==2
    output=capsys.readouterr()
    assert output.out=='' and 'Traceback' not in output.err


@pytest.mark.parametrize('parent',[False,True])
def test_linked_source_or_parent_is_unknown_without_read(project,monkeypatch,parent):
    target=project/'worker.py'
    if parent:
        (project/'src').mkdir();target=project/'src/worker.py';target.write_bytes((project/'worker.py').read_bytes())
        graph=json.loads((project/'graph.json').read_text())
        for item in graph['nodes']+graph['links']:item['source_file']='src/worker.py'
        (project/'graph.json').write_text(json.dumps(graph))
    receipt(project,(target.relative_to(project).as_posix(),))
    loader=context._module;original=os.open;reads=[]
    def modules(name,filename):
        module=loader(name,filename)
        if filename=='local-read.py':
            checked=module._checked
            def guard(root,path):
                if (target.parent in path.parents) if parent else path==target:raise module._ReadStatus('redirected_path')
                return checked(root,path)
            module._checked=guard
        return module
    def observed(path,*args,**kwargs):
        if Path(path)==target:reads.append(path)
        return original(path,*args,**kwargs)
    monkeypatch.setattr(context,'_module',modules);monkeypatch.setattr(os,'open',observed)
    result=query(project)
    assert result['status']=='verification-unavailable' and result['nodes']==[] and reads==[]


def test_nonregular_declared_file_rejected_before_open(project,monkeypatch):
    receipt(project);target=project/'worker.py';original=os.lstat
    def nonregular(path,*args,**kwargs):
        info=original(path,*args,**kwargs)
        if Path(path)==target:
            return SimpleNamespace(**{name:stat.S_IFIFO if name=='st_mode' else getattr(info,name) for name in dir(info) if name.startswith('st_')})
        return info
    monkeypatch.setattr(os,'lstat',nonregular)
    result=query(project)
    assert result['status']=='verification-unavailable' and result['nodes']==[]


def test_hardlinked_inputs_invalid_as_duplicate_physical_identity(project):
    os.link(project/'worker.py',project/'alias.py');receipt(project,('worker.py','alias.py'))
    result=query(project)
    assert result['status']=='verification-invalid' and result['nodes']==[]


def test_duplicate_keys_inside_receipt_input_are_invalid(project):
    path,_=receipt(project);raw=path.read_text();path.write_text(raw.replace('"path": "worker.py"','"path": "worker.py", "path": "worker.py"'))
    assert query(project)['status']=='verification-invalid'


def test_graph_duplicate_keys_cannot_select_an_overwritten_identity(project):
    graph=project/'graph.json';graph.write_text('{"nodes":[],"nodes":[]}')
    with pytest.raises(ValueError):query(project)


def test_completion_and_exact_selection_budget_remain_visible(project):
    receipt(project)
    result=context.query_graph(project,project/'graph.json',node_id='caller',limit=1)
    assert result['selector']=={'kind':'node-id'} and result['selection']=='exact'
    assert result['completeness']=='partial' and result['reason']=='result_budget'
    assert result['status']=='matches' and result['truncated'] and len(result['nodes'])==1


def test_verification_unknown_exposes_partial_completion_and_reason(project):
    result=query(project,sources_manifest=project/'missing.json')
    assert result['completeness']=='partial' and result['reason']=='explicit-manifest-missing'


@pytest.mark.parametrize('name',['wild*.py','wild?.py','bad|.py','bad<.py','bad>.py','bad".py'])
def test_receipt_rejects_windows_invalid_filename_characters(name):
    with pytest.raises(ValueError):context._source_path(name)


def test_remote_root_rejected_before_any_filesystem_probe(monkeypatch):
    def no_probe(*args,**kwargs):raise AssertionError('remote path probed')
    monkeypatch.setattr(Path,'is_dir',no_probe)
    with pytest.raises(ValueError):context.query_graph('\\\\server\\share','\\\\server\\share\\graph.json','symbol')


def test_noncanonical_graph_filename_rejected_before_artifact_read(project,monkeypatch):
    def no_read(*args,**kwargs):raise AssertionError('alias graph read')
    monkeypatch.setattr(context,'_read_stable',no_read)
    with pytest.raises(ValueError):context.query_graph(project,project/'graph.json.','symbol')


def test_total_budget_reserves_primitive_guard_bytes(project,monkeypatch):
    (project/'unused.cfg').write_bytes(b'');path,data=receipt(project,('worker.py','unused.cfg'))
    for item in data['inputs']:item['bytes']=0
    path.write_text(json.dumps(data));monkeypatch.setattr(context,'MAX_TOTAL_SOURCE_BYTES',8);monkeypatch.setattr(context,'MAX_SOURCE_BYTES',4)
    loader=context._module;allocations=[]
    def modules(name,filename):
        module=loader(name,filename)
        if filename=='local-read.py':
            read=module.read_bytes
            def cost(root,relative,**kwargs):
                if relative in {'worker.py','unused.cfg'}:
                    allocations.append(kwargs['max_bytes']+1)
                    return {'status':'unreadable','data':None,'bytes':kwargs['max_bytes']+1}
                return read(root,relative,**kwargs)
            module.read_bytes=cost
        return module
    monkeypatch.setattr(context,'_module',modules)
    result=query(project)
    assert result['status']=='verification-unavailable' and result['nodes']==[]
    assert sum(allocations)<=8 and result['verification']['bytes_read']<=8


def test_binary_declared_input_hashes_raw_bytes_without_text_decoding(project):
    (project/'binary.cfg').write_bytes(b'\x00\xff\xfe\r\n');receipt(project,('worker.py','binary.cfg'))
    assert query(project)['freshness']=='verified-declared-inputs'


def test_unknown_before_later_stale_keeps_stale_diagnostics(project,monkeypatch):
    (project/'unused.cfg').write_bytes(b'one');receipt(project,('unused.cfg','worker.py'));(project/'worker.py').write_bytes(b'changed')
    opened=os.open
    def denied(path,*args,**kwargs):
        if Path(path)==project/'unused.cfg':raise PermissionError('own controlled denial')
        return opened(path,*args,**kwargs)
    monkeypatch.setattr(os,'open',denied)
    result=query(project)
    assert result['status']=='artifact-stale' and result['freshness']=='stale'
    assert result['nodes']==result['edges']==[] and result['verification']['complete'] is False


@pytest.mark.parametrize('which',['graph','receipt'])
def test_artifact_or_receipt_change_during_all_input_verification_is_unknown(project,monkeypatch,which):
    sidecar,_=receipt(project);loader=context._module
    target=project/'graph.json' if which=='graph' else sidecar
    def modules(name,filename):
        module=loader(name,filename)
        if filename=='local-read.py':
            read=module.read_bytes
            def changed(root,relative,**kwargs):
                result=read(root,relative,**kwargs)
                if relative=='worker.py':target.write_bytes(target.read_bytes()+b' ')
                return result
            module.read_bytes=changed
        return module
    monkeypatch.setattr(context,'_module',modules)
    result=query(project)
    assert result['status']=='verification-unavailable' and result['nodes']==result['edges']==[]
    assert result['reason']=='artifact-or-receipt-changed-during-verification'


def test_empty_input_disappearance_after_open_is_instability_not_proved_stale(project,monkeypatch):
    target=project/'empty.cfg';target.write_bytes(b'');receipt(project,('worker.py','empty.cfg'))
    opened=os.open;fdopen=os.fdopen;lstat=os.lstat;target_fds=set();disappeared=False
    class Disappearing:
        def __init__(self,handle):self.handle=handle
        def __enter__(self):self.handle.__enter__();return self
        def __exit__(self,*args):return self.handle.__exit__(*args)
        def fileno(self):return self.handle.fileno()
        def read(self,size):
            nonlocal disappeared
            raw=self.handle.read(size);disappeared=True;return raw
    def observe(path,*args,**kwargs):
        fd=opened(path,*args,**kwargs)
        if Path(path)==target:target_fds.add(fd)
        return fd
    def changing(fd,*args,**kwargs):
        handle=fdopen(fd,*args,**kwargs)
        return Disappearing(handle) if fd in target_fds else handle
    def missing_after(path,*args,**kwargs):
        if disappeared and Path(path)==target:raise FileNotFoundError('own simulated disappearance')
        return lstat(path,*args,**kwargs)
    monkeypatch.setattr(os,'open',observe);monkeypatch.setattr(os,'fdopen',changing);monkeypatch.setattr(os,'lstat',missing_after)
    result=query(project)
    assert result['status']=='verification-unavailable' and result['freshness']=='unverified'
    assert result['nodes']==result['edges']==[]


@pytest.mark.parametrize('record_kind',['node','edge'])
@pytest.mark.parametrize('definition',['unlisted.py','','../outside.py'])
def test_definition_file_coverage_required_before_context(project,record_kind,definition):
    graph=json.loads((project/'graph.json').read_text())
    record=graph['nodes'][0] if record_kind=='node' else graph['links'][0]
    record['definition_file']=definition
    (project/'graph.json').write_text(json.dumps(graph));receipt(project)
    result=query(project)
    assert result['status']=='verification-invalid' and result['nodes']==result['edges']==[]


def test_declared_definition_file_or_native_null_preserves_verified_context(project):
    (project/'defs.py').write_bytes(b'def imported(): pass\n')
    graph=json.loads((project/'graph.json').read_text());graph['nodes'][0]['definition_file']='defs.py';graph['nodes'][1]['definition_file']=None
    (project/'graph.json').write_text(json.dumps(graph));receipt(project,('worker.py','defs.py'))
    assert query(project)['freshness']=='verified-declared-inputs'
