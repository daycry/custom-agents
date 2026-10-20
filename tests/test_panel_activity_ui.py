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


# ---- panel-redesign T-49: page Agentes en vivo (runs, timeline, per-runtime declarations) ----
AGENTES_JS = ROOT / 'skills/plugin-panel/assets/page-agentes.js'

AGENTES_HARNESS = r'''
const assert=require('node:assert/strict');
const ids={};
class Element{
 constructor(tag='div'){this.tagName=tag;this.children=[];this.events={};this.attrs={};this.className='';this._text='';this._id='';}
 set id(value){this._id=value;ids[value]=this;}
 get id(){return this._id;}
 set textContent(value){this._text=String(value);this.children=[];}
 get textContent(){return this._text+this.children.map(x=>x.textContent).join('');}
 set innerHTML(value){throw Error('Untrusted HTML assignment');}
 set outerHTML(value){throw Error('Untrusted HTML assignment');}
 insertAdjacentHTML(){throw Error('Untrusted HTML assignment');}
 append(...nodes){for(const n of nodes){if(typeof n==='string')throw Error('raw string node');this.children.push(n);}}
 replaceChildren(...nodes){this.children=[];this._text='';this.append(...nodes);}
 addEventListener(type,callback){this.events[type]=callback;}
 setAttribute(key,value){this.attrs[key]=String(value);}
 find(pred){if(pred(this))return this;for(const c of this.children){const f=c.find(pred);if(f)return f;}return null;}
 all(pred,out=[]){if(pred(this))out.push(this);for(const c of this.children)c.all(pred,out);return out;}
}
ids.main=new Element('main');
const docEvents={};
global.window=global;
global.document={hidden:false,getElementById:id=>ids[id]||null,createElement:tag=>new Element(tag),addEventListener:(type,callback)=>docEvents[type]=callback};
const timers=new Map();let sequence=0;
global.setTimeout=(fn,delay)=>{timers.set(++sequence,{fn,delay});return sequence;};global.clearTimeout=id=>timers.delete(id);
const requests=[];global.fetch=(url,options)=>new Promise((resolve,reject)=>requests.push({url,options,resolve,reject}));
const K='a1'.repeat(8),K2='c3'.repeat(8);
const run=(o={})=>({key16:K,runtime:'claude',scope:'subagent',role:'implementer',estado:'en_curso',iniciado_at:1000,ultima_senal_at:1030,edad_s:5,duracion_s:35,ultima_herramienta:'Edit',eventos:3,...o});
const runs=(rows=[run()],o={})=>({schema_version:1,status:'ok',reason:null,collection_complete:false,recortado:0,descartados_por_tamano:0,eventos:3,runs:rows,recientes:[],...o});
const ev=(o={})=>({tool:'Bash',resumen:'git status',tarea:null,duracion_ms:12,resultado:'ok',observed_at:1020,revision:1,...o});
const line=(events=[ev()],o={})=>({schema_version:1,status:'ok',reason:null,collection_complete:false,key16:K,run:run(),recortado:0,recortado_historial:0,descartados_por_tamano:0,eventos:events,...o});
const settle=async()=>{for(let i=0;i<20;i++)await Promise.resolve();};
const reply=async(data,index=requests.length-1)=>{requests[index].resolve({ok:true,json:async()=>data});await settle();};
const text=id=>ids[id].textContent;
const rows=()=>ids['agentes-filas'].children;
const open=async(index=0)=>{rows()[index].find(n=>n.tagName==='button').events.click();await settle();};
const pending=url=>requests.filter(r=>r.url===url);
'''

AGENTES_SCENARIOS = {
 'relative_get_only': "assert.equal(requests[0].url,'api/actividad-runs');assert.equal(requests[0].options.method,'GET');assert.equal(requests[0].options.credentials,'omit');assert.ok(!requests[0].options.body);",
 'row_per_run_ca15': "await reply(runs());assert.equal(rows().length,1);const t=rows()[0].textContent;for(const s of ['Claude Code','implementer','1970-01-01T00:16:40.000Z','35 s','Edit','en curso'])assert.ok(t.includes(s),s);",
 'stale_run_ca19': "await reply(runs([run({estado:'sin_senal_reciente',duracion_s:480,edad_s:120})]));const t=rows()[0].textContent;assert.ok(t.includes('sin señal reciente')&&t.includes('8 min 0 s'));assert.ok(!/terminad|muert/i.test(t.replace('respuesta terminada','')));",
 'finished_needs_stop': "await reply(runs([run({estado:'respuesta_terminada'})]));assert.ok(rows()[0].textContent.includes('respuesta terminada'));",
 'timeline_ca16_ca18': "await reply(runs());await open();assert.equal(pending('api/actividad-run-'+K).length,1);await reply(line([ev(),ev({tool:'Edit',resumen:'docs/a.md',tarea:'panel/T-07',revision:2,resultado:'error',duracion_ms:null})]),requests.findIndex(r=>r.url==='api/actividad-run-'+K));const t=text('agentes-eventos');for(const s of ['Bash','git status','tarea: sin atribuir','duración: 12 ms','resultado: ok','tarea: panel/T-07','resultado: error','duración: sin datos','1970-01-01T00:17:00.000Z'])assert.ok(t.includes(s),s);",
 'timeline_trimmed_ca21': "await reply(runs());await open();await reply(line(Array.from({length:150},(_,i)=>ev({revision:i+51})),{recortado:50}),requests.findIndex(r=>r.url==='api/actividad-run-'+K));assert.equal(text('agentes-linea-recorte'),'Historial recortado a los últimos 150 eventos.');assert.equal(ids['agentes-eventos'].children.length,150);",
 'history_trimmed_ca21': "await reply(runs([run()],{recortado:1,eventos:500}));assert.ok(text('agentes-recorte').includes('Historial recortado a los últimos 500 eventos'));",
 'disabled_ca20': "await reply({schema_version:1,status:'unavailable',reason:'disabled',collection_complete:false,recortado:0,descartados_por_tamano:0,eventos:0,runs:[],recientes:[],activar:'IGNORED SERVER TEXT'});const t=text('agentes-estado');assert.ok(t.startsWith('Actividad desactivada.'));assert.ok(t.includes('\"sesion\": {\"actividad\": true}')&&t.includes('.claude/dev.json'));assert.ok(!t.includes('IGNORED'));assert.equal(rows().length,0);",
 'state_missing_is_not_coverage': "await reply({schema_version:1,status:'unavailable',reason:'state_missing',collection_complete:false,recortado:0,descartados_por_tamano:0,eventos:0,runs:[],recientes:[]});assert.equal(text('agentes-estado'),'Aún no hay actividad registrada.');",
 'informative_capture_always_declared': "assert.ok(text('agentes-declaraciones').includes('Captura informativa: puede tener huecos'));assert.ok(text('agentes-declaraciones').includes('orden de recepción, no de ejecución'));",
 'runtimes_declare_what_they_lack_ca42': "const t=text('agentes-declaraciones');assert.ok(t.includes('Codex no identifica el subagente en eventos de herramienta: se agrupan por sesión'));assert.ok(t.includes('este runtime no emite eventos de herramienta'));for(const r of ['Claude Code','Codex','OpenCode'])assert.ok(t.includes(r),r);",
 'codex_session_row': "await reply(runs([run({runtime:'codex',scope:'session',role:null,ultima_herramienta:null,eventos:0})]));const t=rows()[0].textContent;assert.ok(t.includes('Codex')&&t.includes('Codex agrupa por sesión')&&t.includes('sin eventos de herramienta'));",
 'invalid_rows_never_reach_dom': "await reply(runs([run({role:'<img src=x onerror=alert(1)>'})]));assert.equal(rows().length,0);assert.match(text('agentes-estado'),/No se pudo actualizar/);",
 'invalid_event_never_reaches_dom': "await reply(runs());await open();await reply(line([ev({resumen:'x'.repeat(161)})]),requests.findIndex(r=>r.url==='api/actividad-run-'+K));assert.equal(ids['agentes-eventos'].children.length,0);assert.match(text('agentes-linea-estado'),/No se pudo leer/);",
 'foreign_key_in_timeline_rejected': "await reply(runs());await open();await reply(line([ev()],{key16:K2}),requests.findIndex(r=>r.url==='api/actividad-run-'+K));assert.equal(ids['agentes-eventos'].children.length,0);",
 'refresh_every_5s_one_inflight': "await reply(runs());const t=[...timers.values()].filter(x=>x.delay===5000);assert.equal(t.length,1);t[0].fn();await settle();assert.equal(pending('api/actividad-runs').length,2);",
 'request_timeout_4s': "assert.equal([...timers.values()].filter(x=>x.delay===4000).length,1);",
 'hidden_pauses': "await reply(runs());document.hidden=true;docEvents.visibilitychange();assert.equal([...timers.values()].filter(x=>x.delay===5000).length,0);document.hidden=false;docEvents.visibilitychange();assert.equal(pending('api/actividad-runs').length,2);",
 # T-49 fix1 (A-1, TDD debt accepted by the user and verified by mutation): one scenario per surviving mutant
 'null_run_duration_is_sin_datos_ca40': "await reply(runs([run({duracion_s:null})]));assert.equal(rows()[0].children[3].textContent,'sin datos');",
 'null_result_is_sin_datos_ca40': "await reply(runs());await open();await reply(line([ev({resultado:null})]),requests.findIndex(r=>r.url==='api/actividad-run-'+K));const t=text('agentes-eventos');assert.ok(t.includes('resultado: sin datos'));assert.ok(!t.includes('resultado: ok'));",
 'over_64_runs_rejected': "await reply(runs(Array.from({length:65},()=>run())));assert.equal(rows().length,0);assert.match(text('agentes-estado'),/No se pudo actualizar/);",
 'over_150_events_rejected': "await reply(runs());await open();await reply(line(Array.from({length:151},(_,i)=>ev({revision:i+1}))),requests.findIndex(r=>r.url==='api/actividad-run-'+K));assert.equal(ids['agentes-eventos'].children.length,0);assert.match(text('agentes-linea-estado'),/No se pudo leer/);",
 'visible_again_while_inflight_keeps_one_request': "assert.equal(pending('api/actividad-runs').length,1);docEvents.visibilitychange();await settle();assert.equal(pending('api/actividad-runs').length,1);",
 'requests_bypass_the_cache': "assert.equal(requests[0].options.cache,'no-store');",
 'non_ok_response_is_not_painted': "requests[0].resolve({ok:false,status:503,json:async()=>runs()});await settle();assert.equal(rows().length,0);assert.match(text('agentes-estado'),/No se pudo actualizar/);",
 'late_response_of_an_older_generation_is_ignored': "document.hidden=true;docEvents.visibilitychange();await reply(runs(),0);assert.equal(rows().length,0);assert.equal(text('agentes-estado'),'Consultando el historial…');",
}


def test_served_agentes_page_loads_its_script_and_exported_does_not(panel):
    served = pagina(panel, DATA, 'agentes', live=True)
    assert 'src="assets/page-agentes.js"' in served and 'src="assets/panel-activity.js"' in served
    assert 'page-agentes.js' not in pagina(panel, DATA, 'agentes')
    pages = panel._load_pages()
    assert 'page-agentes.js' in pages.LIVE_ASSET_FILES and 'page-agentes.js' not in pages.ASSET_FILES
    files, _, _ = pages.cargar_assets('servido')
    assert 'assets/page-agentes.js' in files and 'assets/page-agentes.js' not in pages.cargar_assets('exportado')[0]


def test_agentes_script_never_writes_html_and_reads_only_its_routes():
    source = AGENTES_JS.read_text(encoding='utf-8')
    assert 'innerHTML' not in source and 'insertAdjacentHTML' not in source and 'eval(' not in source
    assert set(re.findall(r"'(api/[^']*)'", source)) == {'api/actividad-runs', 'api/actividad-run-'}


@pytest.mark.parametrize('scenario', AGENTES_SCENARIOS)
def test_agentes_dom_contract(tmp_path, scenario):
    node = os.environ.get('OWN_ACTIVITY_NODE') or shutil.which('node'); assert node, 'existing Node runner required'
    program = AGENTES_HARNESS + '\n' + AGENTES_JS.read_text(encoding='utf-8') + '\n(async()=>{await settle();' + AGENTES_SCENARIOS[scenario] \
        + '})().catch(error=>{console.error(error);process.exitCode=1;});'
    path = tmp_path / 'agentes-controller.cjs'; path.write_text(program, encoding='utf-8')
    env = {k: os.environ[k] for k in ('SystemRoot', 'WINDIR') if k in os.environ}
    env.update(HOME=str(tmp_path), USERPROFILE=str(tmp_path), TMP=str(tmp_path), TEMP=str(tmp_path), PATH=str(Path(node).parent))
    result = subprocess.run([node, str(path)], cwd=tmp_path, env=env, stdin=subprocess.DEVNULL, capture_output=True, timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
