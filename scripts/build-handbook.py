#!/usr/bin/env python3
"""Build the three maintained Spanish handbooks offline from allowlisted sources.

Uses optional, already installed Node/Chromium authoring tools. Never installs
dependencies or downloads a browser. Runtime scripts remain Python stdlib-only.
Run --help for explicit tool locations. Edition receipts use UTF-8/LF hashes.
Mermaid graphs require closed, unindented top-level fences. List/blockquote
containers are rejected before rendering; longer outer code fences stay literal.
"""
import argparse
from datetime import date
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

SCRIPTS=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('handbook_integrity',SCRIPTS/'check-handbook.py')
CHECK=importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(CHECK)
MAX_SOURCE=512*1024
MAX_PDF=32*1024*1024
SHA=re.compile(r'[a-f0-9]{64}')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def source_names():
    return tuple(name for edition in CHECK.editions() for name in edition['sources'])


def output_names():
    pdfs=tuple(edition['pdf'] for edition in CHECK.editions())
    return tuple(item for pdf in pdfs for item in (pdf,pdf[:-4]+'.manifest.json'))


def read_source(root,name):
    root=Path(root).resolve()
    if name not in source_names():raise ValueError('unsafe_source')
    return CHECK.read(root,name,MAX_SOURCE).replace(b'\r\n',b'\n').decode('utf-8')


def prepare(root,edition):
    try:
        if date.fromisoformat(edition).isoformat()!=edition:raise ValueError
    except (ValueError,TypeError):raise ValueError('invalid_edition') from None
    texts={name:read_source(root,name) for name in source_names()}
    editions=[]
    for definition in CHECK.editions():
        pdf,title,names=definition['pdf'],definition['title'],definition['sources']
        sections=[];diagrams=[];workflows=[]
        for name in names:
            text=texts[name]
            sections.append({'source':name,'text':text,'sha256':digest(text.encode('utf-8'))})
            for index,code in enumerate(CHECK.mermaid_blocks(text),1):
                diagrams.append({'source':name,'index':index,'code':code,'sha256':digest(code.encode('utf-8'))})
            if name.startswith('docs/guides/'):
                workflows.extend(int(n) for n in re.findall(r'^## W-(\d+)[.] ',text,re.M))
        if workflows and sorted(workflows)!=list(range(1,len(workflows)+1)):
            raise ValueError('workflow_sequence')
        if len(diagrams)>128:raise ValueError('diagram_budget')
        editions.append({'pdf':pdf,'title':title,'edition':edition,'language':'es',
                         'sections':sections,'diagrams':diagrams,'workflows':len(workflows)})
    return {'schema_version':1,'editions':editions}


def verify_snapshot(root,request):
    expected={name:digest(read_source(root,name).encode('utf-8')) for name in source_names()}
    actual={row['source']:row['sha256'] for edition in request['editions'] for row in edition['sections']}
    if actual!=expected:raise ValueError('source_changed_during_build')


def receipts(request,stage,result):
    """Validate renderer output against the in-memory snapshot, not its paths."""
    rows=result.get('editions') if type(result) is dict else None
    if type(rows) is not list or len(rows)!=len(request['editions']):raise ValueError('diagram_mismatch')
    products={}
    for edition,row in zip(request['editions'],rows):
        if type(row) is not dict or row.get('pdf')!=edition['pdf']:raise ValueError('diagram_mismatch')
        actual=row.get('diagrams')
        expected=[{key:item[key] for key in ('source','index','sha256')} for item in edition['diagrams']]
        if type(actual) is not list or len(actual)!=len(expected):raise ValueError('diagram_mismatch')
        for item,wanted in zip(actual,expected):
            if type(item) is not dict or any(item.get(key)!=value for key,value in wanted.items()) or not SHA.fullmatch(str(item.get('png_sha256',''))):
                raise ValueError('diagram_mismatch')
        pdf=Path(stage)/Path(edition['pdf']).name
        if pdf.is_symlink() or not pdf.is_file():raise ValueError('invalid_pdf')
        with pdf.open('rb') as handle:data=handle.read(MAX_PDF+1)
        if len(data)>MAX_PDF or not data.startswith(b'%PDF-'):raise ValueError('invalid_pdf')
        manifest={'schema_version':1,'edition':edition['edition'],'language':edition['language'],
                  'pdf':edition['pdf'],'pdf_sha256':digest(data),'source_hash_method':'sha256-utf8-lf',
                  'sources':{section['source']:section['sha256'] for section in edition['sections']},
                  'workflows':edition['workflows'],
                  'diagrams':[{key:item[key] for key in ('source','index','sha256','png_sha256')} for item in actual],
                  'renderer':'Chromium; offline resources; pre-rendered Mermaid PNG; final JavaScript disabled'}
        products[edition['pdf']]=data
        products[edition['pdf'][:-4]+'.manifest.json']=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    return products


def _output(root,name):
    if name not in output_names():raise ValueError('unsafe_output')
    path=root/name
    if any(part.is_symlink() for part in (path,path.parent,path.parent.parent)):
        raise ValueError('unsafe_output')
    if not path.resolve().is_relative_to(root):raise ValueError('unsafe_output')
    if path.exists() and (not path.is_file() or path.stat().st_nlink!=1):raise ValueError('unsafe_output')
    return path


def _file_generation(path):
    """Optimistic identity/content snapshot; absence is a distinct generation."""
    if not path.exists():return None
    before=path.stat()
    if path.is_symlink() or not path.is_file() or before.st_nlink!=1:raise ValueError('unsafe_output_generation')
    with path.open('rb') as handle:data=handle.read(MAX_PDF+1)
    after=path.stat()
    identity=lambda item:(item.st_dev,item.st_ino,item.st_size,item.st_mtime_ns)
    if len(data)>MAX_PDF or identity(before)!=identity(after):raise ValueError('output_changed_during_publish')
    return identity(after)+(digest(data),)


def publish(root,products):
    """Replace a complete prepared edition set; roll back on a rename error.

    Render failures never reach this function. No claim of cross-file atomicity
    for OS/power failure: the checker rejects mismatched PDF/source receipts.
    """
    root=Path(root).resolve()
    targets={name:_output(root,name) for name in products}
    directory=root/'output/pdf'
    directory.mkdir(parents=True,exist_ok=True)
    attempted=[];cleanup=True
    stage=Path(tempfile.mkdtemp(prefix='.handbook-build-',dir=directory))
    stage_root=stage.resolve();stage_identity=(stage.stat().st_dev,stage.stat().st_ino)
    try:
        backups={};previous={};generations={};backup_generations={}
        for index,(name,path) in enumerate(targets.items()):
            _output(root,name)
            previous[name]=_file_generation(path)
            if path.exists():
                backup=stage/(str(index)+'.backup');shutil.copyfile(path,backup)
                if _file_generation(path)!=previous[name]:raise ValueError('output_changed_during_publish')
                backups[name]=backup;backup_generations[name]=_file_generation(backup)
            next_file=stage/(str(index)+'.next');next_file.write_bytes(products[name])
            generations[name]=_file_generation(next_file)
        try:
            for index,(name,path) in enumerate(targets.items()):
                _output(root,name)
                if _file_generation(path)!=previous[name]:raise ValueError('output_changed_during_publish')
                attempted.append(name)
                os.replace(stage/(str(index)+'.next'),path)
        except BaseException:
            failed=[]
            for name in reversed(attempted):
                try:
                    _output(root,name)
                    current=_file_generation(targets[name])
                    if current==previous[name]:continue
                    # Only undo this publisher's still-intact generation. A new
                    # inode or an in-place foreign edit must never be overwritten.
                    if current!=generations[name]:raise ValueError('foreign_output_generation')
                    if name in backups:
                        if _file_generation(backups[name])!=backup_generations[name]:raise ValueError('foreign_backup_generation')
                        os.replace(backups[name],targets[name])
                    else:targets[name].unlink(missing_ok=True)
                except BaseException as error:failed.append((name,'unsafe' if isinstance(error,ValueError) else 'failed'))
            if failed:
                cleanup=False
                try:
                    (stage/'recovery.json').write_text(json.dumps({'schema_version':1,'unrestored':failed,
                        'backups':{name:path.name for name,path in backups.items() if path.exists()}},indent=2)+'\n',encoding='utf-8')
                except OSError:pass
                code='unsafe' if any(reason=='unsafe' for _,reason in failed) else 'failed'
                raise OSError('rollback_'+code+'_backup_retained') from None
            raise
    finally:
        if cleanup:
            if (stage.is_symlink() or stage.resolve()!=stage_root or
                    (stage.stat().st_dev,stage.stat().st_ino)!=stage_identity or
                    not stage_root.is_relative_to(root/'output/pdf')):
                raise ValueError('unsafe_build_cleanup_backup_retained')
            shutil.rmtree(stage)


def _renderer_job():
    if os.name!='nt':return None
    path=SCRIPTS.parent/'skills/plugin-panel/scripts/console_transport.py'
    spec=importlib.util.spec_from_file_location('handbook_owned_transport',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module._WindowsJob()


def _drain_owned_job(job):
    """Only terminate the already assigned private tree; verify it is empty."""
    import ctypes
    from ctypes import wintypes as W
    class Accounting(ctypes.Structure):
        _fields_=[('user',ctypes.c_longlong),('kernel',ctypes.c_longlong),
                  ('period_user',ctypes.c_longlong),('period_kernel',ctypes.c_longlong),
                  ('page_faults',W.DWORD),('total',W.DWORD),('active',W.DWORD),('terminated',W.DWORD)]
    api=job.api
    api.TerminateJobObject.argtypes=[W.HANDLE,W.UINT];api.TerminateJobObject.restype=W.BOOL
    api.QueryInformationJobObject.argtypes=[W.HANDLE,ctypes.c_int,ctypes.c_void_p,W.DWORD,ctypes.c_void_p]
    api.QueryInformationJobObject.restype=W.BOOL
    try:
        if not api.TerminateJobObject(job.handle,1):raise ValueError('owned_renderer_terminate_failed')
        for _ in range(100):
            accounting=Accounting()
            if not api.QueryInformationJobObject(job.handle,1,ctypes.byref(accounting),ctypes.sizeof(accounting),None):
                raise ValueError('owned_renderer_accounting_failed')
            if accounting.active==0:return
            time.sleep(.05)
        raise ValueError('owned_renderer_not_drained')
    finally:job.close()


def run_renderer(request,timeout=600):
    """Assign Windows ownership before stdin can authorize browser launch.

    Wait for the controller independently of pipe EOF: Chromium descendants may
    inherit those handles. Terminate/query the owned tree before joining readers.
    """
    job=_renderer_job();process=None;reader=None;capture=[];errors=[]
    env=dict(os.environ);env.pop('CA_HANDBOOK_OWNED_JOB',None)
    if job:env['CA_HANDBOOK_OWNED_JOB']='1'
    try:
        process=subprocess.Popen(['node',str(SCRIPTS/'handbook-render.mjs')],stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='replace',
            env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),start_new_session=os.name!='nt')
        if job:job.assign(process)
        def communicate():
            try:capture.append(process.communicate(input=json.dumps(request,ensure_ascii=False)))
            except Exception as error:errors.append(error)
        reader=threading.Thread(target=communicate,daemon=True);reader.start()
        try:process.wait(timeout=timeout)
        finally:
            if job:
                owned=job;job=None
                _drain_owned_job(owned)
            elif os.name!='nt':
                import signal
                try:os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:pass
        reader.join(5)
        if reader.is_alive() or errors or len(capture)!=1:raise ValueError('owned_renderer_output_not_drained')
        out,err=capture[0]
        return process.returncode,out,err
    finally:
        if job:_drain_owned_job(job)
        if process and process.poll() is None:
            process.kill();process.wait(timeout=5)
        if reader and reader.is_alive():reader.join(5)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=SCRIPTS.parent)
    parser.add_argument('--edition',default=date.today().isoformat())
    parser.add_argument('--node-modules',type=Path,default=Path.home()/'.claude/tool-cache/to-pdf/node_modules',
                        help='Existing trusted directory containing puppeteer and markdown-it; never auto-installs')
    parser.add_argument('--mermaid',type=Path,default=Path.home()/'.claude/tool-cache/emailing-manual/node_modules/mermaid/dist/mermaid.min.js',
                        help='Existing trusted Mermaid browser bundle')
    parser.add_argument('--browser',type=Path,help='Installed Chromium/Edge executable; otherwise use the existing Puppeteer browser')
    args=parser.parse_args(argv)
    try:
        request=prepare(args.root,args.edition)
        for library in ('puppeteer','markdown-it'):
            if not (args.node_modules/library/'package.json').is_file():raise ValueError('missing_authoring_dependency:'+library)
        if not args.mermaid.is_file():raise ValueError('missing_authoring_dependency:mermaid')
        with tempfile.TemporaryDirectory(prefix='custom-agents-handbook-') as temporary:
            request['tools']={'node_modules':str(args.node_modules.resolve()),'mermaid':str(args.mermaid.resolve()),
                              'browser':str(args.browser.resolve()) if args.browser else None,'stage':temporary}
            code,out,err=run_renderer(request)
            if code:
                # Renderer emits bounded public error codes, never source content/tool paths.
                error=err.strip()
                if not re.fullmatch(r'handbook-render: [a-z0-9_:-]{1,160}',error):error='handbook-render: conversion_failed'
                raise ValueError(error)
            if len(out)>256*1024:raise ValueError('renderer_result_budget')
            result=json.loads(out,object_pairs_hook=CHECK.unique)
            products=receipts(request,temporary,result)
            verify_snapshot(args.root,request)
            publish(args.root,products)
        for edition in request['editions']:print('build-handbook: '+edition['pdf'])
        return 0
    except (OSError,ValueError,subprocess.TimeoutExpired) as error:
        code=str(error)
        if not re.fullmatch(r'[a-zA-Z0-9_:. -]{1,200}',code):code='build_failed'
        print('build-handbook: '+code+'; existing editions were not certified as current',file=sys.stderr)
        return 1


if __name__=='__main__':raise SystemExit(main())
