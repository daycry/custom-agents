"""Own collaboration notes are versioned metadata, never ledger verdicts."""
import importlib.util
from pathlib import Path
import json

import pytest

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/'skills/plugin-panel/scripts/console_state.py'

def api():
    assert PATH.is_file(), 'console metadata owner is not implemented'
    spec=importlib.util.spec_from_file_location('tested_console_state',PATH)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def test_comment_has_receipt_redaction_and_retry_identity_without_changing_ledger(tmp_path):
    ledger=tmp_path/'tasks.md';ledger.write_text('pending')
    notes=api().Notes(tmp_path)
    secret='ghp_'+'A'*36
    first=notes.add('a'*16,'T-01','Please review '+secret,0,'b'*32)
    again=notes.add('a'*16,'T-01','Please review '+secret,0,'b'*32)
    assert first==again and first['revision']==1
    got=notes.list('a'*16,'T-01')
    assert len(got['comments'])==1 and secret not in json.dumps(got)
    assert got['comments'][0]['actor']=='usuario del dashboard'
    assert ledger.read_text()=='pending'
    assert len(notes.list('c'*16,'T-01')['comments'])==0

def test_stale_revision_and_reused_request_cannot_overwrite_notes(tmp_path):
    notes=api().Notes(tmp_path)
    notes.add('a'*16,'T-01','first',0,'b'*32)
    with pytest.raises(ValueError):notes.add('a'*16,'T-01','second',0,'c'*32)
    with pytest.raises(ValueError):notes.add('a'*16,'T-01','changed',1,'b'*32)
    assert [x['text'] for x in notes.list('a'*16,'T-01')['comments']]==['first']

def test_read_does_not_initialize_state_and_foreign_file_is_preserved(tmp_path):
    notes=api().Notes(tmp_path)
    assert notes.list('a'*16,'T-01')=={'revision':0,'comments':[]}
    assert not (tmp_path/'.claude').exists()
    state=tmp_path/'.claude/control-center';state.mkdir(parents=True)
    foreign=state/'comments.json';foreign.write_text('{"private":"keep"}')
    with pytest.raises(ValueError):notes.add('a'*16,'T-01','text',0,'b'*32)
    assert foreign.read_text()=='{"private":"keep"}'

@pytest.mark.parametrize('plan,task,text,revision,key',[
 ('../','T-01','text',0,'b'*32),('a'*16,'../tasks','text',0,'b'*32),
 ('a'*16,'T-01','',0,'b'*32),('a'*16,'T-01','x'*2001,0,'b'*32),
 ('a'*16,'T-01','text',True,'b'*32),('a'*16,'T-01','text',0,'bad')])
def test_invalid_note_cannot_create_state(tmp_path,plan,task,text,revision,key):
    with pytest.raises(ValueError):api().Notes(tmp_path).add(plan,task,text,revision,key)
    assert not (tmp_path/'.claude').exists()
