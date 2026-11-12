"""Behavioural checks of the offline, allowlisted handbook build boundary."""
import importlib.util
import json
from pathlib import Path
import subprocess
import threading

import pytest

ROOT=Path(__file__).resolve().parents[1]


def api():
    spec=importlib.util.spec_from_file_location('tested_handbook_build',ROOT/'scripts/build-handbook.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def fixture(tmp_path):
    module=api()
    for name in module.source_names():
        path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True)
        text='# '+path.stem+'\n\nPreserved: café and : "quotes".\n'
        if name=='docs/guides/core-workflows.md':
            text+='\n## W-01. Sample\n\n```mermaid\nflowchart LR\n A --> B\n```\n'
        if name.endswith('.json'):text='{"example":true}\n'
        path.write_bytes(text.replace('\n','\r\n').encode('utf-8'))
    return module


def test_build_request_preserves_allowlisted_sources_and_lf_hashes(tmp_path):
    module=fixture(tmp_path);request=module.prepare(tmp_path,'2026-11-06')
    operational=request['editions'][0]
    assert operational['pdf']=='output/pdf/custom-agents-manual-operativo.pdf'
    assert operational['workflows']==1
    body=next(row['text'] for row in operational['sections'] if row['source']=='docs/guides/product.md')
    assert 'café and : "quotes"' in body and '\r' not in body
    assert len(request['editions'])==3
    assert len(operational['diagrams'])==1
    assert operational['diagrams'][0]['code']=='flowchart LR\n A --> B\n'
    assert all(not name.startswith('../') for name in module.source_names())


def test_changed_sources_fail_before_replacing_any_previous_pdf(tmp_path):
    module=fixture(tmp_path);request=module.prepare(tmp_path,'2026-11-06')
    pdf=tmp_path/request['editions'][0]['pdf'];pdf.parent.mkdir(parents=True)
    pdf.write_bytes(b'%PDF-previous')
    (tmp_path/'docs/guides/product.md').write_text('changed',encoding='utf-8')
    with pytest.raises(ValueError,match='source_changed'):
        module.verify_snapshot(tmp_path,request)
    assert pdf.read_bytes()==b'%PDF-previous'


def test_source_traversal_and_unapproved_editions_fail_closed(tmp_path):
    module=fixture(tmp_path)
    with pytest.raises(ValueError,match='unsafe_source'):
        module.read_source(tmp_path,'../private')
    with pytest.raises(ValueError,match='invalid_edition'):
        module.prepare(tmp_path,'../../private')


def test_renderer_result_must_cover_every_diagram_and_pdf(tmp_path):
    module=fixture(tmp_path);request=module.prepare(tmp_path,'2026-11-06')
    stage=tmp_path/'stage';stage.mkdir()
    for edition in request['editions']:
        (stage/Path(edition['pdf']).name).write_bytes(b'%PDF-1.7\nfixture\n%%EOF\n')
    with pytest.raises(ValueError,match='diagram_mismatch'):
        module.receipts(request,stage,{'editions':[]})


def test_publishing_preserves_previous_outputs_when_a_write_fails(tmp_path,monkeypatch):
    module=fixture(tmp_path);names=module.output_names()[:2];paths=[tmp_path/name for name in names]
    paths[0].parent.mkdir(parents=True)
    for path in paths:path.write_bytes(b'previous')
    original=module.os.replace;calls=0
    def fail_second(source,destination):
        nonlocal calls
        calls+=1
        if calls==2:raise OSError('synthetic_replace_failure')
        return original(source,destination)
    monkeypatch.setattr(module.os,'replace',fail_second)
    with pytest.raises(OSError,match='synthetic_replace_failure'):
        module.publish(tmp_path,{name:b'next' for name in names})
    assert [path.read_bytes() for path in paths]==[b'previous',b'previous']


def test_output_paths_cannot_be_selected_by_a_renderer(tmp_path):
    module=fixture(tmp_path)
    with pytest.raises(ValueError,match='unsafe_output'):
        module.publish(tmp_path,{'../outside.pdf':b'%PDF-no'})


def test_failed_rollback_keeps_recoverable_previous_bytes(tmp_path,monkeypatch):
    """A persistent I/O error must not clean up the only previous edition copy."""
    module=fixture(tmp_path);names=module.output_names()[:2]
    for name in names:
        path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'previous')
    original=module.os.replace;calls=0
    def fail_after_first(source,destination):
        nonlocal calls
        calls+=1
        if calls>1:raise OSError('persistent_io_failure')
        return original(source,destination)
    monkeypatch.setattr(module.os,'replace',fail_after_first)
    with pytest.raises(OSError,match='rollback_failed_backup_retained'):
        module.publish(tmp_path,{name:b'next' for name in names})
    retained=list((tmp_path/'output/pdf').glob('.handbook-build-*/*.backup'))
    assert retained and all(path.read_bytes()==b'previous' for path in retained)


def test_duplicate_or_missing_diagram_receipts_cannot_be_accepted(tmp_path):
    module=fixture(tmp_path);request=module.prepare(tmp_path,'2026-11-06')
    stage=tmp_path/'stage';stage.mkdir()
    result={'editions':[]}
    for edition in request['editions']:
        (stage/Path(edition['pdf']).name).write_bytes(b'%PDF-1.7\nfixture\n%%EOF\n')
        rows=[dict(row,png_sha256='a'*64) for row in edition['diagrams']]
        result['editions'].append({'pdf':edition['pdf'],'diagrams':rows})
    valid=module.receipts(request,stage,result)
    assert len(valid)==6
    manifest=json.loads(valid['output/pdf/custom-agents-manual-operativo.manifest.json'])
    assert manifest['source_hash_method']=='sha256-utf8-lf'
    result['editions'][0]['diagrams']*=2
    with pytest.raises(ValueError,match='diagram_mismatch'):
        module.receipts(request,stage,result)


def test_renderer_decodes_split_utf8_and_bounds_only_its_own_browser():
    """No npm/browser dependencies: exercise the actual stream and lifecycle helpers."""
    code=r'''
import {readInput,closeOwnedBrowser} from './scripts/handbook-runtime.mjs';
import {Readable} from 'node:stream';
import {EventEmitter} from 'node:events';
import assert from 'node:assert/strict';
const expected='café · revisión 🚀';
const bytes=Buffer.from(expected);
assert.equal(await readInput(Readable.from(Array.from(bytes,byte=>Buffer.from([byte])))),expected);
const child=new EventEmitter();child.exitCode=null;let kills=0;
child.kill=()=>{kills++;child.exitCode=1;queueMicrotask(()=>child.emit('exit',1));return true};
const owned={close:()=>new Promise(()=>{}),process:()=>child};
await assert.rejects(closeOwnedBrowser(owned,5),/browser_close_timeout/);
assert.equal(kills,0);
const shared={close:()=>new Promise(()=>{}),process:()=>null};
await assert.rejects(closeOwnedBrowser(shared,5),/browser_close_timeout/);
assert.equal(kills,0);
assert.deepEqual(await closeOwnedBrowser({close:async()=>{},process:()=>child},5),{forced:false});
'''
    completed=subprocess.run(['node','--input-type=module','-e',code],cwd=ROOT,capture_output=True,
                             text=True,encoding='utf-8',errors='replace',timeout=10)
    assert completed.returncode==0,completed.stderr


def test_windows_renderer_assigns_before_payload_and_drains_before_pipe_eof(tmp_path,monkeypatch):
    """An inherited browser pipe cannot make the controller wait for EOF first."""
    module=fixture(tmp_path);events=[];drained=threading.Event()
    class Job:
        def assign(self,process):events.append('assigned')
    class Process:
        returncode=0
        def communicate(self,input):
            assert 'assigned' in events
            events.append('payload')
            assert drained.wait(2),'parent waited for EOF instead of terminating its Job'
            events.append('eof');return '{}',''
        def wait(self,timeout):events.append('controller_exited');return 0
        def poll(self):return 0
    monkeypatch.setattr(module,'_renderer_job',lambda:Job())
    monkeypatch.setattr(module.subprocess,'Popen',lambda *args,**kwargs:Process())
    def drain(job):events.append('drained');drained.set()
    monkeypatch.setattr(module,'_drain_owned_job',drain)
    assert module.run_renderer({'editions':[]})==(0,'{}','')
    assert events.index('assigned')<events.index('payload')
    assert events.index('controller_exited')<events.index('drained')<events.index('eof')


def test_CLAUDE_TOOL_1_validation_failure_rolls_back_partial_publication(tmp_path,monkeypatch):
    module=fixture(tmp_path);names=module.output_names()[:2]
    for name in names:
        path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'previous')
    original=module._output;rejected=False
    def validate(root,name):
        nonlocal rejected
        if not rejected and name==names[1] and (tmp_path/names[0]).read_bytes()==b'next':
            rejected=True
            raise ValueError('synthetic_validation_failure')
        return original(root,name)
    monkeypatch.setattr(module,'_output',validate)
    with pytest.raises(ValueError,match='synthetic_validation_failure'):
        module.publish(tmp_path,{name:b'next' for name in names})
    assert [(tmp_path/name).read_bytes() for name in names]==[b'previous',b'previous']


def test_CLAUDE_TOOL_1_rollback_preserves_foreign_edits_and_retains_old_bytes(tmp_path,monkeypatch):
    module=fixture(tmp_path);names=module.output_names()[:2]
    for name in names:
        path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'previous')
    original=module.os.replace;calls=0
    def concurrent_edit(source,destination):
        nonlocal calls
        calls+=1
        if calls==2:
            (tmp_path/names[0]).write_bytes(b'foreign-edit')
            raise OSError('synthetic_replace_failure')
        return original(source,destination)
    monkeypatch.setattr(module.os,'replace',concurrent_edit)
    with pytest.raises(OSError):module.publish(tmp_path,{name:b'next' for name in names})
    assert (tmp_path/names[0]).read_bytes()==b'foreign-edit'
    retained=list((tmp_path/'output/pdf').glob('.handbook-build-*/*.backup'))
    assert retained and any(path.read_bytes()==b'previous' for path in retained)


def test_CLAUDE_TOOL_4_outer_code_sample_does_not_create_a_mermaid_image(tmp_path):
    module=fixture(tmp_path)
    path=tmp_path/'docs/guides/product.md'
    path.write_text('# Example\n\n````markdown\n```mermaid\nflowchart LR\n A --> B\n```\n````\n',encoding='utf-8')
    request=module.prepare(tmp_path,'2026-11-06')
    assert [row for row in request['editions'][0]['diagrams'] if row['source']=='docs/guides/product.md']==[]


@pytest.mark.parametrize('text,reason',[
    ('- ```mermaid\n  flowchart LR\n  A --> B\n  ```\n','unsupported_mermaid_container'),
    ('> ```mermaid\n> flowchart LR\n> A --> B\n> ```\n','unsupported_mermaid_container'),
    ('  ```mermaid\n  flowchart LR\n  A --> B\n  ```\n','unsupported_mermaid_container'),
    ('```mermaid\nflowchart LR\n A --> B\n','unclosed_mermaid_fence'),
])
def test_CLAUDE_TOOL_4_unsupported_graph_fences_fail_before_rendering(tmp_path,text,reason):
    module=fixture(tmp_path)
    (tmp_path/'docs/guides/product.md').write_text(text,encoding='utf-8')
    with pytest.raises(ValueError,match=reason):module.prepare(tmp_path,'2026-11-06')


def test_CLAUDE_TOOL_4_tilde_graph_fences_match_standard_fence_content(tmp_path):
    module=fixture(tmp_path)
    (tmp_path/'docs/guides/product.md').write_text('~~~mermaid\nflowchart LR\n A --> B\n~~~~\n',encoding='utf-8')
    rows=[row for row in module.prepare(tmp_path,'2026-11-06')['editions'][0]['diagrams'] if row['source']=='docs/guides/product.md']
    assert len(rows)==1 and rows[0]['code']=='flowchart LR\n A --> B\n'


def test_CLAUDE_TOOL_1_forward_publication_does_not_overwrite_a_foreign_generation(tmp_path,monkeypatch):
    module=fixture(tmp_path);names=module.output_names()[:2]
    for name in names:
        path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'previous')
    original=module._output;edited=False
    def foreign_edit(root,name):
        nonlocal edited
        if not edited and name==names[1] and (tmp_path/names[0]).read_bytes()==b'next':
            (tmp_path/name).write_bytes(b'foreign-edit');edited=True
        return original(root,name)
    monkeypatch.setattr(module,'_output',foreign_edit)
    with pytest.raises(ValueError,match='output_changed_during_publish'):
        module.publish(tmp_path,{name:b'next' for name in names})
    assert [(tmp_path/name).read_bytes() for name in names]==[b'previous',b'foreign-edit']


def test_CLAUDE_TOOL_1_interrupt_rolls_back_only_the_publisher_generation(tmp_path,monkeypatch):
    module=fixture(tmp_path);names=module.output_names()[:2]
    for name in names:
        path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'previous')
    original=module.os.replace;calls=0
    def interrupt(source,destination):
        nonlocal calls
        calls+=1
        if calls==2:raise KeyboardInterrupt
        return original(source,destination)
    monkeypatch.setattr(module.os,'replace',interrupt)
    with pytest.raises(KeyboardInterrupt):module.publish(tmp_path,{name:b'next' for name in names})
    assert [(tmp_path/name).read_bytes() for name in names]==[b'previous',b'previous']


def test_full_edition_publication_replaces_all_six_owned_outputs(tmp_path):
    module=fixture(tmp_path);names=module.output_names()
    for name in names:
        path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'previous')
    products={name:('edition:'+name).encode() for name in names}
    module.publish(tmp_path,products)
    assert {(name,(tmp_path/name).read_bytes()) for name in names}==set(products.items())
    assert not list((tmp_path/'output/pdf').glob('.handbook-build-*'))
