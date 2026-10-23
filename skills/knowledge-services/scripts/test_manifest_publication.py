"""Controlled native Windows reader blocks manifest replacement, then releases it."""
import ctypes
from ctypes import wintypes
import importlib.util
import json
import os
from pathlib import Path
import pytest

HERE=Path(__file__).resolve().parent
def load():
    path=HERE.parent/'backends/markdown_export.py'
    spec=importlib.util.spec_from_file_location('native_manifest_lock',path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def entry(body):
    return {'id':'owned.gotcha.note','version':1,'category':'GOTCHA','evidencia':'validated_case',
            'fuentes':['docs/evidence.md'],'tags':['area:testing'],'modo':'completo','cuerpo':body}

@pytest.mark.skipif(os.name!='nt',reason='Real Windows CreateFile sharing contract')
def test_native_reader_released_after_rejected_replace_can_finalize_without_new_sync(tmp_path):
    mod=load();projection=tmp_path/'projection';cfg={'export_dir':str(projection)}
    old=[entry('Original body.\n')];new=[entry('Updated body.\n')]
    mod.apply(mod.plan(old,cfg),cfg)
    target=projection/'manifest.json';pending=projection/'manifest.pending.json'
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.CreateFileW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE]
    kernel.CreateFileW.restype=wintypes.HANDLE
    kernel.CloseHandle.argtypes=[wintypes.HANDLE];kernel.CloseHandle.restype=wintypes.BOOL
    handle=kernel.CreateFileW(str(target),0x80000000,0x1|0x2,None,3,0x80,None)
    assert handle!=ctypes.c_void_p(-1).value,ctypes.get_last_error()
    real_replace=mod.os.replace;seen=[];closed=False
    def replace(source,destination,*args,**kwargs):
        nonlocal closed
        try:return real_replace(source,destination,*args,**kwargs)
        except OSError as error:
            if Path(destination)==target and not closed:
                seen.append(error.winerror)
                assert kernel.CloseHandle(handle);closed=True
            raise
    mod.os.replace=replace
    try:
        mod.apply(mod.plan(new,cfg),cfg)
    finally:
        mod.os.replace=real_replace
        if not closed:assert kernel.CloseHandle(handle)
    assert seen and seen[0] in (5,32,33)
    assert not pending.exists()
    assert 'Updated body.' in (projection/'owned.gotcha.note.md').read_text(encoding='utf8')
    manifest=json.loads(target.read_bytes())
    assert manifest['entries']['owned.gotcha.note']['hash']==mod.plan(new,cfg)[0]['hash']

def synthetic_windows_error():
    error=PermissionError('Owned injected sharing denial');error.winerror=5;return error

def publication_fixture(tmp_path):
    mod=load();projection=tmp_path/'projection';cfg={'export_dir':str(projection)}
    mod.apply(mod.plan([entry('Original body.\n')],cfg),cfg)
    return mod,projection,cfg

def test_transient_finalization_denial_retries_the_same_unchanged_files(tmp_path,monkeypatch):
    mod,projection,cfg=publication_fixture(tmp_path);target=projection/'manifest.json'
    real=mod.os.replace;attempts=[]
    monkeypatch.setattr(mod,'_retryable_manifest_error',lambda e:getattr(e,'winerror',None)==5,raising=False)
    def replace(source,destination,*args,**kwargs):
        if Path(destination)==target:
            attempts.append((source,destination))
            if len(attempts)==1:raise synthetic_windows_error()
        return real(source,destination,*args,**kwargs)
    monkeypatch.setattr(mod.os,'replace',replace)
    mod.apply(mod.plan([entry('Updated body.\n')],cfg),cfg)
    assert len(attempts)==2 and attempts[0]==attempts[1]
    assert not (projection/'manifest.pending.json').exists()

@pytest.mark.parametrize('changed',['source','target'])
def test_retry_never_overwrites_a_changed_manifest_identity(tmp_path,monkeypatch,changed):
    mod,projection,cfg=publication_fixture(tmp_path);target=projection/'manifest.json';pending=projection/'manifest.pending.json'
    real=mod.os.replace;attempts=[];foreign=b'{"foreign":"preserve these changed bytes"}'
    monkeypatch.setattr(mod,'_retryable_manifest_error',lambda e:getattr(e,'winerror',None)==5,raising=False)
    def replace(source,destination,*args,**kwargs):
        if Path(destination)==target:
            attempts.append((source,destination))
            (Path(source) if changed=='source' else target).write_bytes(foreign)
            raise synthetic_windows_error()
        return real(source,destination,*args,**kwargs)
    monkeypatch.setattr(mod.os,'replace',replace)
    with pytest.raises(mod.ConfigInvalida):mod.apply(mod.plan([entry('Updated body.\n')],cfg),cfg)
    assert len(attempts)==1
    assert (pending if changed=='source' else target).read_bytes()==foreign
    assert pending.exists()

def test_persistent_denial_keeps_pending_and_has_bounded_attempts(tmp_path,monkeypatch):
    mod,projection,cfg=publication_fixture(tmp_path);target=projection/'manifest.json';before=target.read_bytes()
    real=mod.os.replace;attempts=[]
    monkeypatch.setattr(mod,'_retryable_manifest_error',lambda e:getattr(e,'winerror',None)==5,raising=False)
    def replace(source,destination,*args,**kwargs):
        if Path(destination)==target:attempts.append(destination);raise synthetic_windows_error()
        return real(source,destination,*args,**kwargs)
    monkeypatch.setattr(mod.os,'replace',replace)
    with pytest.raises(mod.ConfigInvalida):mod.apply(mod.plan([entry('Updated body.\n')],cfg),cfg)
    assert 1<=len(attempts)<=4 and target.read_bytes()==before
    assert (projection/'manifest.pending.json').exists()

def test_nonsharing_error_is_not_retried(tmp_path,monkeypatch):
    mod,projection,cfg=publication_fixture(tmp_path);target=projection/'manifest.json';real=mod.os.replace;attempts=[]
    def replace(source,destination,*args,**kwargs):
        if Path(destination)==target:attempts.append(destination);raise OSError('Owned nontransient failure')
        return real(source,destination,*args,**kwargs)
    monkeypatch.setattr(mod.os,'replace',replace)
    with pytest.raises(mod.ConfigInvalida):mod.apply(mod.plan([entry('Updated body.\n')],cfg),cfg)
    assert len(attempts)==1 and (projection/'manifest.pending.json').exists()
