"""Activity view exercised with the existing isolated Node DOM approach."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import pytest
from panel_render import pagina
from test_panel_activity_server import DATA, ROOT

@pytest.fixture
def panel():
    spec=importlib.util.spec_from_file_location('activity_builder',ROOT/'skills/plugin-panel/scripts/build_panel.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def test_static_panel_explains_no_service_without_telemetry(panel):
    html=pagina(panel,DATA,'agentes')
    assert 'id="activity"' in html and 'sin servicio' in html.lower()
    assert 'api/activity' not in html and 'id="activity-refresh"' not in html and 'panel-activity.js' not in html

def test_served_activity_is_separate_accessible_and_embedded(panel):
    html=pagina(panel,DATA,'agentes',live=True)
    assert 'src="assets/panel-activity.js"' in html
    for identity in ('activity','activity-status','activity-freshness','activity-cards','activity-refresh','activity-coverage'):
        assert f'id="{identity}"' in html
    assert 'aria-live=' in html and 'collection_complete' in html and '@@' not in html

def activity_script(panel):
    source=(ROOT/'skills/plugin-panel/assets/panel-activity.js').read_text(encoding='utf8')
    assert 'api/activity' in source
    return source

HARNESS=r'''
const assert=require('node:assert/strict');
class Element{
 constructor(tag='div'){this.tagName=tag;this.children=[];this.events={};this.disabled=false;this.hidden=false;this.className='';this.dataset={};this._text='';}
 set textContent(value){this._text=String(value);this.children=[];}
 get textContent(){return this._text+this.children.map(x=>x.textContent).join('');}
 set innerHTML(value){throw Error('Untrusted HTML assignment');}
 append(...nodes){this.children.push(...nodes.map(n=>typeof n==='string'?Object.assign(new Element(),{textContent:n}):n));}
 replaceChildren(...nodes){this.children=[];this._text='';this.append(...nodes);}
 addEventListener(type,callback){this.events[type]=callback;}
 setAttribute(key,value){this[key]=value;}
}
const ids={};for(const id of ['activity','activity-status','activity-freshness','activity-cards','activity-refresh','activity-coverage'])ids[id]=new Element();
const docEvents={};global.document={hidden:false,getElementById:id=>ids[id]||null,createElement:tag=>new Element(tag),addEventListener:(type,callback)=>docEvents[type]=callback};
let clock=0,sequence=0;Object.defineProperty(global,'performance',{value:{now:()=>clock},configurable:true});
const timers=new Map();global.setTimeout=(fn,delay)=>{timers.set(++sequence,{fn,delay,due:clock+delay});return sequence;};global.clearTimeout=id=>timers.delete(id);
const requests=[];global.fetch=(url,options)=>new Promise((resolve,reject)=>requests.push({url,options,resolve,reject}));
const observation=(overrides={})=>({runtime:'codex',scope:'subagent',session_key:'a'.repeat(64),agent_key:'b'.repeat(64),role:'implementer',source:'native_hook',observed_at:100,revision:1,age_seconds:5,state:'recent_start',live_process_proven:false,agent_destroyed_proven:false,...overrides});
const report=(rows=[observation()])=>({schema_version:1,status:'ok',reason:null,complete:true,collection_complete:false,observations:rows});
const settle=async()=>{for(let i=0;i<12;i++)await Promise.resolve();};
const resolve=async(data,index=requests.length-1)=>{requests[index].resolve({ok:true,json:async()=>data});await settle();};
const timer=async(delay)=>{const row=[...timers].find(([,v])=>v.delay===delay);assert.ok(row,'timer '+delay);timers.delete(row[0]);clock=Math.max(clock,row[1].due);row[1].fn();await settle();};
const advance=async(ms)=>{clock+=ms;for(let i=0;i<30;i++){const row=[...timers].find(([,v])=>v.due<=clock);if(!row)break;timers.delete(row[0]);row[1].fn();await settle();}};
const text=()=>ids['activity-cards'].textContent;
const refresh=()=>ids['activity-refresh'].events.click();
'''
SCENARIOS={
 'relative_readonly':"assert.equal(requests[0].url,'api/activity');assert.equal(requests[0].options.credentials,'omit');assert.ok(requests[0].options.signal);assert.ok(!requests[0].options.body);",
 'closed_metadata_no_ids':"await resolve(report());assert.match(text(),/implementer|implementador/i);assert.ok(!text().includes('a'.repeat(64))&&!text().includes('b'.repeat(64)));assert.match(ids['activity-coverage'].textContent,/incompleta/i);assert.ok(!/agente vivo|destruido|todos activos/i.test(text()));",
 'states_do_not_mean_death':"for(const [state,label] of Object.entries({recent_start:'Señal reciente de inicio',recent_response_end:'Fin reciente de respuesta',recent_execution_end:'Fin reciente de ejecución',recent_idle:'Señal reciente de inactividad',unknown:'Estado desconocido'})){const session=['recent_execution_end','recent_idle'].includes(state)?{scope:'session',agent_key:null,role:null}:{};await resolve(report([observation({...session,state})]));assert.ok(text().includes(label));assert.ok(!/agente vivo|destruido/i.test(text()));if(state!=='unknown')refresh();}",
 'exact_sixty':"await resolve(report([observation({age_seconds:59})]));assert.ok(!/desconocido/i.test(text()));await advance(1000);assert.match(text(),/desconocido/i);",
 'http_failure_still_expires':"await resolve(report([observation({age_seconds:55})]));const date=ids['activity-freshness'].textContent;refresh();requests.at(-1).reject(Error('PRIVATE_TRANSCRIPT'));await settle();await advance(5000);assert.match(text(),/desconocido/i);assert.equal(ids['activity-freshness'].textContent,date);assert.ok(!ids['activity-status'].textContent.includes('PRIVATE'));",
 'unavailable_preserves_then_expires':"await resolve(report([observation({age_seconds:55})]));const date=ids['activity-freshness'].textContent;refresh();await resolve({schema_version:1,status:'unavailable',reason:'state_missing',complete:false,collection_complete:false,observations:[]});await advance(5000);assert.match(text(),/desconocido/i);assert.equal(ids['activity-freshness'].textContent,date);",
 'hidden_abort_and_resume_age':"await resolve(report([observation({age_seconds:55})]));refresh();document.hidden=true;docEvents.visibilitychange();assert.ok(requests.at(-1).options.signal.aborted);requests.at(-1).reject(Error('aborted'));await settle();await advance(5000);assert.equal(requests.length,2);document.hidden=false;docEvents.visibilitychange();assert.match(text(),/desconocido/i);assert.equal(requests.length,3);",
 'timeout_four_seconds':"await timer(4000);assert.ok(requests[0].options.signal.aborted);requests[0].reject(Error('aborted'));await settle();assert.equal(ids['activity-refresh'].disabled,false);assert.equal([...timers.values()].filter(x=>x.delay===5000).length,1);",
 'one_inflight':"refresh();refresh();assert.equal(requests.length,1);await resolve(report());refresh();assert.equal(requests.length,2);",
 'poll_five_seconds':"await resolve(report());await timer(5000);assert.equal(requests.length,2);assert.ok(![...timers.values()].some(x=>x.delay===5000));requests.at(-1).reject(Error('offline'));await settle();assert.equal([...timers.values()].filter(x=>x.delay===5000).length,1);",
 'future_unknown':"await resolve(report([observation({age_seconds:null,state:'unknown'})]));assert.match(text(),/desconocido/i);",
 'expiry_is_not_reset_by_same_event':"await resolve(report([observation({age_seconds:55})]));await advance(5000);assert.match(text(),/desconocido/i);await resolve(report([observation({age_seconds:0})]));assert.match(text(),/desconocido/i);",
 'invalid_metadata_is_not_dom':"await resolve(report([observation({role:'<img src=x onerror=alert(1)>'})]));assert.equal(ids['activity-cards'].children.length,0);assert.ok(!text().includes('<img'));assert.match(ids['activity-status'].textContent,/disponible|actualizar/i);",
 'partial_collection_is_always_visible':"await resolve(report([]));assert.match(ids['activity-coverage'].textContent,/incompleta/i);assert.ok(!/todos activos/i.test(text()));",
 'wrong_shape_does_not_claim_empty':"await resolve({...report([]),collection_complete:true});assert.match(ids['activity-status'].textContent,/disponible|actualizar/i);",
 'duplicate_id_rejected':"await resolve(report([observation(),observation()]));assert.equal(ids['activity-cards'].children.length,0);",
 'count_limit':"await resolve(report(Array.from({length:65},(_,i)=>observation({agent_key:i.toString(16).padStart(64,'0')}))));assert.equal(ids['activity-cards'].children.length,0);",
 'disabled_says_opt_in_and_how_to_enable':"await resolve({schema_version:1,status:'unavailable',reason:'disabled',complete:false,collection_complete:false,observations:[]});const t=ids['activity-status'].textContent;assert.match(t,/La actividad de los agentes está desactivada \\(opt-in\\)/);assert.ok(t.includes('sesion')&&t.includes('actividad')&&t.includes('.claude/dev.json'));assert.ok(!/No se pudo actualizar/.test(t));assert.equal(ids['activity-cards'].children.length,0);",
 'other_unavailable_reasons_keep_the_failure_text':"await resolve({schema_version:1,status:'unavailable',reason:'state_missing',complete:false,collection_complete:false,observations:[]});assert.match(ids['activity-status'].textContent,/No se pudo actualizar/);",
 'not_a_writer_or_chat':"await resolve(report());assert.ok(requests.every(x=>!x.options.body&&(!x.options.method||x.options.method==='GET')));assert.ok(!ids['activity-cards'].children.some(x=>x.tagName==='textarea'));"
}

@pytest.mark.parametrize('scenario',SCENARIOS)
def test_activity_dom_contract(panel,tmp_path,scenario):
    node=os.environ.get('OWN_ACTIVITY_NODE') or shutil.which('node');assert node,'existing Node runner required'
    expected=os.environ.get('OWN_ACTIVITY_NODE_SHA256')
    digest=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    if expected:assert digest(node)==expected
    script=activity_script(panel)
    program=HARNESS+'\n'+script+'\n(async()=>{'+SCENARIOS[scenario]+"})().catch(error=>{console.error(error);process.exitCode=1;});"
    path=tmp_path/'activity-controller.cjs';path.write_text(program,encoding='utf-8')
    env={k:os.environ[k] for k in ('SystemRoot','WINDIR') if k in os.environ}
    env.update(HOME=str(tmp_path),USERPROFILE=str(tmp_path),TMP=str(tmp_path),TEMP=str(tmp_path),TMPDIR=str(tmp_path),PATH=str(Path(node).parent))
    argv=[node,str(path)]
    (tmp_path/'prelaunch.json').write_text(json.dumps(dict(argv=argv,env=env,cwd=str(tmp_path),source_sha256=digest(path),asset_sha256=hashlib.sha256(script.encode()).hexdigest(),executable_sha256=digest(node))),encoding='utf-8')
    child=None
    try:
        with (tmp_path/'stdout.raw').open('wb') as stdout,(tmp_path/'stderr.raw').open('wb') as stderr:
            child=subprocess.Popen(argv,cwd=tmp_path,env=env,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr)
            (tmp_path/'pid.json').write_text(json.dumps(dict(pid=child.pid,owned=True)),encoding='utf-8')
            child.wait(timeout=15)
    finally:
        if child is not None:
            if child.poll() is None:child.kill()
            child.wait(timeout=5)
            (tmp_path/'terminal.json').write_text(json.dumps(dict(pid=child.pid,exit_code=child.returncode,terminal=True,stdout_sha256=digest(tmp_path/'stdout.raw'),stderr_sha256=digest(tmp_path/'stderr.raw'))),encoding='utf-8')
    assert child.returncode==0,(tmp_path/'stdout.raw').read_bytes()+(tmp_path/'stderr.raw').read_bytes()

def test_missing_activity_asset_preserves_static_and_existing_served_views(panel,tmp_path,monkeypatch):
    copy=tmp_path/'assets'
    shutil.copytree(ROOT/'skills/plugin-panel/assets',copy)
    (copy/'panel-activity.js').unlink()
    pages=panel._load_pages()
    monkeypatch.setattr(pages,'ASSETS_DIR',copy)
    files,_,_=pages.cargar_assets('servido')
    assert 'assets/panel-activity.js' not in files and 'assets/panel-live.js' in files
    assert 'sin servicio' in pagina(panel,DATA,'agentes').lower()
    html=panel.cuerpos_paginas(DATA,live=True,actividad=False)['agentes']
    assert 'id="activity"' in html and 'no disponibles' in html.lower()
    assert 'api/activity' not in html and 'id="activity-refresh"' not in html
    assert 'id="operations"' in panel.cuerpos_paginas(DATA,live=True,actividad=False)['inicio']


def test_memory_view_preserves_unicode_accessible_labels(panel):
    html=pagina(panel,DATA,'memoria',live=True)
    assert 'placeholder="Área opcional"' in html
    assert 'aria-label="Área de conocimiento"' in html
    assert chr(129) not in html and chr(195) not in html