"""Typed Graphiti tool errors are failures even when MCP isError is false."""
import copy
import importlib.util
import json
from pathlib import Path
import pytest
HERE=Path(__file__).resolve().parent
def load():
    path=HERE.parent/'backends/graphiti.py'
    spec=importlib.util.spec_from_file_location('typed_graphiti_error',path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

@pytest.mark.parametrize('representation',['live','text','structured-flat','empty-error'])
def test_typed_tool_error_never_returns_as_success(monkeypatch,representation):
    mod=load();fixture=json.loads((HERE/'fixtures/graphiti/graphiti-mcp-validation-error.json').read_bytes())
    if representation=='text':fixture.pop('structuredContent')
    elif representation=='structured-flat':fixture['structuredContent']=fixture['structuredContent']['result']
    elif representation=='empty-error':fixture={'isError':False,'structuredContent':{'result':{'error':''}}}
    client=mod.ClienteMCP('http://127.0.0.1:8001/mcp')
    monkeypatch.setattr(client,'_peticion',lambda *a,**k:copy.deepcopy(fixture))
    with pytest.raises(mod.ErrorMCP):client.tools_call('add_memory',{})

def test_error_response_diagnostic_is_sanitized(monkeypatch):
    mod=load();client=mod.ClienteMCP('http://127.0.0.1:8001/mcp')
    fixture={'isError':False,'structuredContent':{'result':{'error':'Owned failure\n\x1b[2J'+'x'*5000}}}
    monkeypatch.setattr(client,'_peticion',lambda *a,**k:copy.deepcopy(fixture))
    with pytest.raises(mod.ErrorMCP) as raised:client.tools_call('add_memory',{})
    assert len(str(raised.value))<300 and '\n' not in str(raised.value) and '\x1b' not in str(raised.value)

def test_queued_success_message_is_preserved(monkeypatch):
    mod=load();client=mod.ClienteMCP('http://127.0.0.1:8001/mcp')
    fixture={'isError':False,'structuredContent':{'result':{'message':'Episode queued; error handling remains server-side'}}}
    monkeypatch.setattr(client,'_peticion',lambda *a,**k:copy.deepcopy(fixture))
    assert client.tools_call('add_memory',{})==fixture
