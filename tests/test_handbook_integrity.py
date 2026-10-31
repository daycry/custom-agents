"""A shipped PDF must match the maintained sources, including Windows line endings."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def api():
    path=ROOT/'scripts/check-handbook.py'
    assert path.is_file(),'handbook artifact verification is not implemented'
    spec=importlib.util.spec_from_file_location('tested_handbook_integrity',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def fixture(tmp_path):
    module=api();sources={}
    for name in module.SOURCES:
        path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True)
        text='# Example\n'
        if name=='docs/guides/core-workflows.md':text+='\n## W-01. Example\n\n```mermaid\nflowchart TD\n    A[Start] --> B[Done]\n```\n'
        path.write_bytes(text.replace('\n','\r\n').encode())
        sources[name]=hashlib.sha256(text.encode()).hexdigest()
    pdf=tmp_path/module.PDF;pdf.parent.mkdir(parents=True,exist_ok=True);pdf.write_bytes(b'%PDF-1.7\nfixture artifact\n%%EOF\n')
    manifest={'schema_version':1,'pdf':module.PDF,'pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),
              'source_hash_method':'sha256-utf8-lf','sources':sources,'workflows':1,'diagrams':[{
                  'source':'docs/guides/core-workflows.md','index':1,'sha256':hashlib.sha256(b'flowchart TD\n    A[Start] --> B[Done]\n').hexdigest(),
                  'png_sha256':'1'*64}]}
    path=tmp_path/module.MANIFEST;path.write_text(json.dumps(manifest),encoding='utf-8')
    return module,path,manifest

def test_lf_source_hashes_accept_equivalent_windows_worktrees(tmp_path):
    module,_,_=fixture(tmp_path)
    assert module.check(tmp_path)==[]

def test_changed_source_or_pdf_cannot_reuse_the_previous_receipt(tmp_path):
    module,_,_=fixture(tmp_path)
    (tmp_path/'docs/guides/product.md').write_text('Changed',encoding='utf-8')
    assert 'source_changed:docs/guides/product.md' in module.check(tmp_path)
    (tmp_path/module.PDF).write_bytes(b'%PDF-1.7\nchanged\n%%EOF\n')
    assert 'pdf_changed' in module.check(tmp_path)

def test_omitted_sources_and_stale_diagram_receipts_fail_closed(tmp_path):
    module,path,manifest=fixture(tmp_path)
    manifest['sources'].pop('docs/guides/product.md')
    manifest['diagrams'][0]['sha256']='0'*64
    path.write_text(json.dumps(manifest),encoding='utf-8')
    issues=module.check(tmp_path)
    assert 'source_set_mismatch' in issues and 'diagram_mismatch' in issues

def test_manifest_cannot_select_files_outside_the_handbook_source_allowlist(tmp_path):
    module,path,manifest=fixture(tmp_path)
    manifest['sources']['../private']='0'*64
    path.write_text(json.dumps(manifest),encoding='utf-8')
    assert 'source_set_mismatch' in module.check(tmp_path)

def test_handbook_gate_reports_invalid_receipts_and_missing_sources(tmp_path,capsys):
    module,path,manifest=fixture(tmp_path)
    assert module.main(['--root',str(tmp_path)])==0
    assert 'sources, workflows and diagrams match' in capsys.readouterr().out
    (tmp_path/'docs/guides/product.md').unlink()
    assert 'source_unavailable:docs/guides/product.md' in module.check(tmp_path)
    assert module.main(['--root',str(tmp_path)])==1
    assert 'source_unavailable' in capsys.readouterr().out
    manifest['workflows']=2;manifest['diagrams']=[{'source':'x','index':'wrong'}]
    path.write_text(json.dumps(manifest),encoding='utf-8')
    assert {'workflow_mismatch','diagram_mismatch'}<=set(module.check(tmp_path))
    path.write_text('{"schema_version":1,"schema_version":1}',encoding='utf-8')
    assert module.check(tmp_path)==['handbook_unavailable']
    path.write_text('{}',encoding='utf-8')
    assert module.check(tmp_path)==['invalid_manifest']
