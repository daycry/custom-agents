"""T-58: Plan review UI (open, comment, decide, state text, agent replies) in an isolated Node harness."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ASSETS = Path(__file__).resolve().parents[1] / 'skills/plugin-panel/assets'
RID = 'a' * 64

HARNESS = r'''
const assert=require('node:assert/strict');
class Element {
 constructor(tag='div'){this.tagName=tag;this.children=[];this.events={};this.value='';this.hidden=false;this.disabled=false;this.dataset={};this._text='';this.attrs={};}
 set textContent(v){this._text=String(v);this.children=[];}
 get textContent(){return this._text+this.children.map(x=>x.textContent).join('');}
 set innerHTML(v){throw Error('Untrusted HTML assignment');}
 append(...n){this.children.push(...n);}
 appendChild(n){this.children.push(n);return n;}
 replaceChildren(...n){this.children=[];this._text='';this.append(...n);}
 replaceWith(){}
 addEventListener(t,c){this.events[t]=c;}
 setAttribute(k,v){this.attrs[k]=v;this[k]=v;}
 getAttribute(k){return this.attrs[k];}
 focus(){this.focused=true;document.activeElement=this;}
 walk(){return [this,...this.children.flatMap(c=>c.walk?c.walk():[])];}
}
const ids={};
for (const id of ['plan-revision','plan-revision-estado','plan-revisar','panel-data']) ids[id]=new Element(id==='plan-revisar'?'button':'p');
ids['plan-revision'].dataset.revision='activa'; ids['plan-revision'].dataset.initiativeId='ab12cd34ef56ab12';
ids['plan-revisar'].hidden=true;
ids['panel-data'].textContent=JSON.stringify({plan_id:'ab12cd34ef56ab12'});
const docEvents={};
global.document={hidden:false,activeElement:null,getElementById:id=>ids[id],createElement:t=>new Element(t),addEventListener:(t,c)=>docEvents[t]=c};
let seq=0;const timers=new Map();
global.setTimeout=(cb,d)=>{timers.set(++seq,{cb,d});return seq;};global.clearTimeout=i=>timers.delete(i);
const requests=[];let routes=()=>({});
global.fetch=(url,options={})=>{requests.push({url,options});const r=routes(url,options);return Promise.resolve({ok:true,json:async()=>r});};
const settle=async()=>{for(let i=0;i<40;i++)await Promise.resolve();};
const fire=async d=>{const f=[...timers].filter(([,v])=>v.d===d);assert.ok(f.length,'timer '+d);for(const [k,v] of f){timers.delete(k);v.cb();}await settle();};
const version={raw_sha256:'b'.repeat(64),view_sha256:'c'.repeat(64),view_version:'plan-text-v1'};
const section={section_id:'d'.repeat(64),title:'Alcance <b>x</b>',level:1,text:'Texto <img src=x onerror=alert(1)>'};
const review=(o={})=>Object.assign({review_id:'a'.repeat(64),initiative:'docs/roadmap/2026-10-15-x',artifact:'improvement-plan.md',gate_key:'requested-review',version,current_version:version,revision:0,state:'pendiente',created_at:'2026-10-16T10:00:00Z',observed_at:'2026-10-16T10:00:01Z',consumer_registration:null,draft_comments:[],decision:null,delivery:null,ack:null,validity:'current',complete:true,redacted:false,controls_sanitized:false,sections:[section]},o);
const envelope=(o={},st='ok')=>({schema_version:1,status:st,reason:null,review:review(o)});
const current=(o={})=>Object.assign({schema_version:1,status:'ok',reason:null,initiative_id:'ab12cd34ef56ab12',review_id:null,estado:'sin_revision',version_ordinal:1,gate_key:'requested-review',escritura:false},o);
const all=()=>ids['plan-revision'].children.flatMap(c=>c.walk());
const find=(tag,text)=>all().find(n=>n.tagName===tag&&n.textContent===text);
const body=()=>ids['plan-revision'].textContent;
'''

SCENARIOS = {
 'load_is_read_only_and_states_text': """
  routes=u=>current();await boot();await settle();
  assert.equal(ids['plan-revision-estado'].textContent,'Estado de la revisión: sin revisión');
  assert.equal(ids['plan-revisar'].hidden,false);
  assert.ok(requests.every(r=>!r.options.method||r.options.method==='GET'));assert.equal(requests.length,1);
  assert.equal(requests[0].url,'api/review-current/ab12cd34ef56ab12');""",
 'open_sends_only_id16_and_announces': """
  let opened=false;routes=(u,o)=>{if(u.startsWith('api/review-open/')){opened=true;return {schema_version:1,status:'ok',reason:null,initiative_id:'ab12cd34ef56ab12',review_id:'a'.repeat(64),escritura:true};}
   if(u.startsWith('api/review-current/'))return opened?current({review_id:RID,estado:'pendiente',escritura:true}):current();
   if(u.endsWith('/view'))return envelope();return {};};
  await boot();await settle();ids['plan-revisar'].events.click();await settle();await settle();
  const post=requests.find(r=>r.options.method==='POST');assert.equal(post.url,'api/review-open/ab12cd34ef56ab12');
  assert.equal(post.options.body,'{"initiative_id":"ab12cd34ef56ab12"}');
  assert.match(ids['plan-revision-estado'].textContent,/pendiente.*revisión abierta/);assert.equal(ids['plan-revisar'].hidden,true);
  assert.ok(requests.some(r=>r.url==='api/review/'+RID+'/view'));assert.ok(body().includes('Texto <img src=x'));""",
 'comment_then_changes_use_submit_with_limits': """
  routes=u=>u.startsWith('api/review-current/')?current({review_id:RID,estado:'pendiente',escritura:true}):envelope();
  await boot();await settle();const ta=all().find(n=>n.tagName==='textarea');assert.ok(ta);
  const approve=find('button','Aprobar'),changes=find('button','Pedir correcciones');assert.ok(approve&&changes);
  ta.value='x'.repeat(2001);find('button','Guardar comentarios').events.click();assert.match(body(),/límite/);
  assert.equal(requests.filter(r=>r.options.method==='POST').length,0);
  ta.value='Revisar alcance';changes.events.click();await settle();
  const p=requests.find(r=>r.options.method==='POST');assert.equal(p.url,'api/review/'+RID+'/submit');
  assert.equal(JSON.parse(p.options.body).choice,'request_changes');assert.equal(JSON.parse(p.options.body).comments[0].section_id,'d'.repeat(64));""",
 'readonly_plan_ok_has_no_write_controls': """
  routes=u=>u.startsWith('api/review-current/')?current({review_id:RID,estado:'pendiente',gate_key:'plan-ok',escritura:false}):envelope({gate_key:'plan-ok'});
  await boot();await settle();
  for(const l of ['Guardar comentarios','Aprobar','Pedir correcciones','Cargar versión actual'])assert.equal(find('button',l).hidden,true,l);
  assert.equal(all().filter(n=>n.tagName==='textarea').every(n=>n.disabled),true);assert.equal(ids['plan-revisar'].hidden,true);
  assert.match(body(),/solo lectura/);assert.ok(requests.every(r=>!r.options.method||r.options.method==='GET'));""",
 'agent_reply_and_no_reply_text': """
  const fb={schema_version:1,results:[{result_id:'1'.repeat(64),comment_id:'one',section_id:'d'.repeat(64),supersedes_result_id:null,disposition:'addressed',response_text:'Hecho <script>x</script>',text_flags:{redacted:false,controls_sanitized:false},producer:{caller_id:'owned',runtime:'codex',actor_id:null,identity_basis:'declared'},recorded_at:'2026-10-16T10:00:03Z',artifact_observation:{status:'available',version,observed_at:'2026-10-16T10:00:03Z'}}],
   verifications:[{verification_id:'4'.repeat(64),result_id:'1'.repeat(64),comment_id:'one',section_id:'d'.repeat(64),assessment:'confirmed',note:'ok',text_flags:{redacted:false,controls_sanitized:false},basis:'human_instruction_declared',producer:{caller_id:'h',runtime:'codex',actor_id:null,identity_basis:'declared'},recorded_at:'2026-10-16T10:00:04Z'}]};
  const dec={decision_id:'e'.repeat(64),choice:'request_changes',comments:[{comment_id:'one',section_id:'d'.repeat(64),text:'Uno'},{comment_id:'two',section_id:'d'.repeat(64),text:'Dos'}],submitted_at:'2026-10-16T10:00:02Z'};
  routes=u=>u.startsWith('api/review-current/')?current({review_id:RID,estado:'cambios_pedidos',escritura:true}):envelope({state:'consumida',decision:dec,delivery:{delivery_id:'c'.repeat(64),delivered_at:'2026-10-16T10:00:02Z'},ack:{decision_id:'e'.repeat(64),delivery_id:'c'.repeat(64),consumed_at:'2026-10-16T10:00:02Z'},feedback:fb});
  await boot();await settle();const t=body();
  assert.match(t,/Respuesta del agente/);assert.ok(t.includes('Hecho <script>x</script>'));assert.match(t,/Atendido/);assert.match(t,/verify-result.*confirmada/);
  assert.match(t,/Comentario two · sin respuesta del agente/);assert.ok(!t.includes('Sin respuesta declarada'));""",
 'live_refresh_keeps_form_and_typed_text': """
  routes=u=>u.startsWith('api/review-current/')?current({review_id:RID,estado:'pendiente',escritura:true}):envelope(u.endsWith('/status')?{sections:undefined}:{});
  await boot();await settle();const ta=all().find(n=>n.tagName==='textarea');ta.value='Borrador';ta.focus();
  await fire(0);await fire(5000);assert.ok(requests.some(r=>r.url.endsWith('/status')));await fire(0);await fire(5000);const again=all().find(n=>n.tagName==='textarea');
  assert.equal(again,ta);assert.equal(again.value,'Borrador');""",
 'bad_projection_is_not_trusted': """
  routes=u=>current({estado:'<img>',review_id:'../x'});await boot();await settle();
  assert.match(ids['plan-revision-estado'].textContent,/no se pudo leer/);assert.equal(all().filter(n=>n.tagName==='textarea').length,0);""",
}

STATES = [('sin_revision', 'sin revisión', 1), ('pendiente', 'pendiente', 1), ('cambios_pedidos', 'cambios pedidos', 1),
          ('aprobada', 'aprobada v3', 3), ('obsoleta', 'obsoleta por cambio de versión', 1)]

CARD = r'''
const assert=require('node:assert/strict');
class E{constructor(t){this.tagName=t;this.children=[];this.dataset={};this.attrs={};this._t='';}
 set textContent(v){this._t=String(v);this.children=[];}get textContent(){return this._t+this.children.map(c=>c.textContent).join('');}
 set innerHTML(v){throw Error('html');}appendChild(n){this.children.push(n);return n;}append(...n){this.children.push(...n);}
 replaceChildren(...n){this.children=[];this._t='';this.children.push(...n);}setAttribute(k,v){this.attrs[k]=v;}getAttribute(k){return this.attrs[k];}
 find(c){return [this,...this.children.flatMap(x=>x.find?x.find(c):[])].filter(n=>n.className===c);}}
const els={'panel-data':new E('s'),'kanban-iniciativas':new E('div'),'cartera-estado':new E('p'),'iniciativas-revision':new E('p')};
els['panel-data'].textContent='{}';els['iniciativas-revision'].setAttribute('data-revision','activa');
const fila={id:'ab12cd34ef56ab12',slug:'x',titulo:'T',fecha:'2026-10-16',tiene_plan:true,categoria:'aprobada',alertas:[],tareas:null,ledger:'sin_ledger',horas:{real:null,est:null},coste:{real_eur:null,est_eur:null,real_parcial:false},procedencia:{medidos:0,estimados:0,desconocidos:0}};
const reqs=[];
const w={document:{hidden:false,getElementById:id=>els[id],createElement:t=>new E(t)},setTimeout,clearTimeout,
 fetch:u=>{reqs.push(u);return Promise.resolve({ok:true,json:async()=>({initiatives:[{initiative_id:'ab12cd34ef56ab12',estado:'__ESTADO__',version_ordinal:__ORD__}]})});},
 AbortController};
globalThis.window=w;
new Function('window','globalThis',__CARTERA__)(w,w);
Object.assign(w.PanelCartera,{iniciar(cb){cb({status:'ok',complete:true,observed_at:'x',iniciativas:[fila]});}});
globalThis.fetch=w.fetch;globalThis.document=w.document;
new Function(__REVIEW__)();w.PanelReview=globalThis.PanelReview;
new Function('window','globalThis',__PAGE__)(w,w);
setTimeout(()=>{const l=els['kanban-iniciativas'].find('revision-estado');assert.equal(l.length,1);
 assert.equal(l[0].textContent,'Revisión: __TEXTO__');assert.deepEqual(reqs,['api/review-summary']);},5);
'''


def _node():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node unavailable for isolated controller test')
    return node


def _run(tmp_path, name, source):
    path = tmp_path / name
    path.write_text(source, encoding='utf8')
    return subprocess.run([_node(), str(path)], capture_output=True, text=True, encoding='utf8', errors='replace', timeout=20)


def _plan(tmp_path, scenario_js):
    script = (ASSETS / 'panel-review.js').read_text(encoding='utf8')
    boot = "const RID='" + RID + "';const boot=async()=>{(0,eval)(" + json.dumps(script) + ");};"
    return _run(tmp_path, 'case.cjs', HARNESS + boot + '\n(async()=>{' + scenario_js +
                '})().catch(e=>{console.error(e);process.exitCode=1;});')


@pytest.mark.parametrize('scenario', SCENARIOS)
def test_review_panel_controller(scenario, tmp_path):
    result = _plan(tmp_path, SCENARIOS[scenario])
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize('estado,texto,ordinal', STATES)
def test_header_and_card_show_the_same_state_text(estado, texto, ordinal, tmp_path):
    header = _plan(tmp_path, """
      routes=u=>current({estado:'%s',version_ordinal:%d});await boot();await settle();
      assert.equal(ids['plan-revision-estado'].textContent,'Estado de la revisión: %s');""" % (estado, ordinal, texto))
    assert header.returncode == 0, header.stdout + header.stderr
    page = (ASSETS / 'page-iniciativas.js').read_text(encoding='utf8')
    cartera = (ASSETS / 'page-cartera.js').read_text(encoding='utf8')
    source = (CARD.replace('__ESTADO__', estado).replace('__ORD__', str(ordinal)).replace('__TEXTO__', texto)
              .replace('__PAGE__', json.dumps(page)).replace('__CARTERA__', json.dumps(cartera))
              .replace('__REVIEW__', json.dumps((ASSETS / 'panel-review.js').read_text(encoding='utf8'))))
    out = _run(tmp_path, 'card.cjs', source)
    assert out.returncode == 0, out.stdout + out.stderr


def test_no_inner_html_and_no_old_literal():
    for name in ('panel-review.js', 'page-iniciativas.js'):
        text = (ASSETS / name).read_text(encoding='utf8')
        assert 'innerHTML' not in text and 'insertAdjacentHTML' not in text
    assert 'Sin respuesta declarada' not in (ASSETS / 'panel-review.js').read_text(encoding='utf8')
