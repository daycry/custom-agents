"""Opt-in plan controller renders text and never consumes a receipt."""
import importlib.util
from pathlib import Path
import re
import shutil
import subprocess
import types

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/plugin-panel/scripts/build_panel.py'
DATA = {'counts': dict.fromkeys(('agents', 'skills', 'commands', 'tools', 'hooks'), 0),
        'agents': [], 'skills': [], 'commands': [], 'tools': [], 'hooks': [],
        'runtimes': {}, 'memory': {}, 'warnings': [], 'workflow': {'roles': {}}}

@pytest.fixture
def panel():
    spec = importlib.util.spec_from_file_location('review_builder', SCRIPT)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

def test_review_is_explicit_live_only(panel):
    for kwargs in ({}, {'live': True}, {'review_enabled': True}):
        output = panel.render_html(DATA, **kwargs)
        assert 'id="plan-review"' not in output and 'api/review/' not in output
    output = panel.render_html(DATA, live=True, review_enabled=True)
    for identity in ('plan-review', 'review-status', 'review-sections', 'review-save', 'review-approve',
                     'review-changes', 'review-refresh', 'review-close', 'review-open', 'review-version'):
        assert 'id="'+identity+'"' in output
    assert 'aria-live="polite"' in output and 'href="#plan-review"' in output
    assert '@@' not in output

def test_missing_review_asset_degrades_only_requested_review(panel, tmp_path, monkeypatch):
    reference = SCRIPT.parents[1] / 'references'
    for name in ('panel.html','panel-live.js','panel-memory.js'):
        (tmp_path / name).write_bytes((reference / name).read_bytes())
    monkeypatch.setattr(panel,'TEMPLATE',tmp_path / 'panel.html')
    with pytest.raises(ValueError,match='bundled review panel asset unavailable'):
        panel.render_html(DATA,live=True,review_enabled=True)
    assert 'id="plan-review"' not in panel.render_html(DATA,live=True)
    assert 'api/review/' not in panel.render_html(DATA,review_enabled=True)

@pytest.mark.parametrize('argv', [ ['--review-initiative','docs/roadmap/2026-10-09-example'],
    ['--serve','--project','synthetic','--review-initiative','docs/roadmap/2026-10-09-example'],
    ['--serve','--project','synthetic','--review-state-root','synthetic/.claude/plan-review']])
def test_cli_requires_paired_explicit_review_scope(panel, argv):
    with pytest.raises(SystemExit) as error: panel.main(argv)
    assert error.value.code == 2

@pytest.mark.parametrize('gate', [None, 'requested-review', 'plan-ok'])
def test_cli_explicit_gate_selection(panel, monkeypatch, gate):
    calls = []
    monkeypatch.setattr(panel, 'build_inventory', lambda *args, **kwargs: DATA)
    monkeypatch.setattr(panel, '_load_server', lambda: types.SimpleNamespace(
        run=lambda *args, **kwargs: calls.append(kwargs) or 0))
    argv = ['--serve','--project','synthetic','--review-initiative','docs/roadmap/2026-10-09-example',
            '--review-state-root','synthetic/.claude/plan-review']
    if gate is not None: argv += ['--review-gate-key',gate]
    assert panel.main(argv) == 0
    assert calls[0]['review_selection']['gate_key'] == (gate or 'requested-review')

@pytest.mark.parametrize('argv', [['--review-gate-key','arbitrary'], ['--review-gate-key','plan-ok'],
    ['--serve','--project','synthetic','--review-gate-key','plan-ok']])
def test_cli_gate_rejects_arbitrary_or_unselected_scope(panel, argv):
    with pytest.raises(SystemExit) as error: panel.main(argv)
    assert error.value.code == 2

HARNESS = r'''
const assert=require('node:assert/strict');
class Element {
 constructor(tag='div'){this.tagName=tag;this.children=[];this.events={};this.value='';this.hidden=false;this.disabled=false;this.dataset={};this._text='';}
 set textContent(value){this._text=String(value);this.children=[];}
 get textContent(){return this._text+this.children.map(x=>x.textContent).join('');}
 set innerHTML(value){throw Error('Untrusted HTML assignment');}
 append(...nodes){this.children.push(...nodes);}
 replaceChildren(...nodes){this.children=[];this._text='';this.append(...nodes);}
 addEventListener(type,callback){this.events[type]=callback;}
 setAttribute(key,value){this[key]=value;}
 focus(){this.focused=true;}
}
const ids={};for(const id of ['plan-review','review-status','review-sections','review-save','review-approve','review-changes','review-refresh','review-close','review-open','review-version','review-metadata'])ids[id]=new Element();
ids['plan-review'].dataset.reviewId='a'.repeat(64);
const docEvents={};global.document={hidden:false,getElementById:id=>ids[id],createElement:tag=>new Element(tag),addEventListener:(type,callback)=>docEvents[type]=callback};
let seq=0;const timers=new Map();global.setTimeout=(callback,delay)=>{timers.set(++seq,{callback,delay});return seq;};global.clearTimeout=id=>timers.delete(id);
const requests=[];global.fetch=(url,options)=>new Promise((resolve,reject)=>requests.push({url,options,resolve,reject}));
const version={raw_sha256:'b'.repeat(64),view_sha256:'c'.repeat(64),view_version:'plan-text-v1'};
const section={section_id:'d'.repeat(64),title:'<script>alert(1)</script>',level:1,text:'[click](https://evil.test) ![img](x) <img src=x onerror=alert(1)> 🚀'};
const review=(overrides={})=>Object.assign({review_id:'a'.repeat(64),initiative:'docs/roadmap/2026-10-09-example',artifact:'improvement-plan.md',gate_key:'plan-ok',version,current_version:version,revision:0,state:'pendiente',created_at:'2026-10-09T10:00:00Z',observed_at:'2026-10-09T10:00:01Z',consumer_registration:null,draft_comments:[],decision:null,delivery:null,ack:null,validity:'current',complete:true,redacted:false,controls_sanitized:false,sections:[section]},overrides);
const envelope=(overrides={},status='ok')=>({schema_version:1,status,reason:null,review:review(overrides)});
const settle=async()=>{for(let i=0;i<12;i++)await Promise.resolve();};
const resolve=async(data,index=requests.length-1)=>{requests[index].resolve({ok:true,json:async()=>data});await settle();};
const timer=delay=>{const found=[...timers].find(([,v])=>v.delay===delay);assert.ok(found,'timer '+delay);timers.delete(found[0]);found[1].callback();};
const textarea=()=>ids['review-sections'].children[0].children.find(x=>x.tagName==='textarea');
'''

SCENARIOS = {
 'close_blocked_during_submit': "await resolve(envelope());ids['review-approve'].events.click();assert.equal(ids['review-close'].disabled,true);ids['review-close'].events.click();assert.equal(ids['review-sections'].hidden,false,'guard must reject close during submitted POST');assert.ok(!/cerrada sin decidir/i.test(ids['review-status'].textContent));assert.equal(requests.length,2);assert.equal(requests[1].options.signal.aborted,false);await resolve(envelope({revision:1,decision:{decision_id:'e'.repeat(64),choice:'approve',comments:[],submitted_at:'2026-10-09T10:00:02Z'}}));assert.equal(ids['review-close'].disabled,false);ids['review-close'].events.click();assert.match(ids['review-status'].textContent,/decisión.*registrada.*aprobación/i);assert.match(ids['review-status'].textContent,/pendiente|pendiente de consumo/i);assert.ok(!/sin decidir/i.test(ids['review-status'].textContent));",
 'close_blocked_during_comments': "await resolve(envelope());textarea().value='Draft';ids['review-save'].events.click();assert.equal(ids['review-close'].disabled,true);ids['review-close'].events.click();assert.equal(ids['review-sections'].hidden,false);assert.equal(requests[1].options.signal.aborted,false);await resolve(envelope({revision:1,draft_comments:[{comment_id:'comment-0',section_id:'d'.repeat(64),text:'Draft'}]}));assert.equal(ids['review-close'].disabled,false);ids['review-close'].events.click();assert.equal(ids['review-sections'].hidden,true);assert.match(ids['review-status'].textContent,/cerrar no crea.*decisión/i);assert.equal(requests.length,2);",
 'close_blocked_during_refresh_post': "await resolve(envelope());ids['review-refresh'].events.click();assert.equal(ids['review-close'].disabled,true);ids['review-close'].events.click();assert.equal(ids['review-sections'].hidden,false);assert.equal(requests.length,2);assert.equal(requests[1].options.signal.aborted,false);",
 'close_preserves_sealed_changes_consumed': "await resolve(envelope({state:'consumida',decision:{decision_id:'e'.repeat(64),choice:'request_changes',comments:[],submitted_at:'2026-10-09T10:00:02Z'}}));ids['review-close'].events.click();assert.match(ids['review-status'].textContent,/decisión.*registrada.*cambios/i);assert.match(ids['review-status'].textContent,/consumida/i);assert.ok(!/sin decidir/i.test(ids['review-status'].textContent));assert.equal(ids['review-close'].textContent,'Cerrar panel');assert.equal(requests.length,1);",
 'close_during_get_preserves_later_known_decision': "await resolve(envelope());timer(5000);assert.equal(ids['review-close'].disabled,false);ids['review-close'].events.click();assert.equal(ids['review-sections'].hidden,true);assert.equal(requests[1].options.signal.aborted,false);await resolve(envelope({sections:undefined,state:'entregada',decision:{decision_id:'e'.repeat(64),choice:'approve',comments:[],submitted_at:'2026-10-09T10:00:02Z'}}));assert.match(ids['review-status'].textContent,/decisión.*registrada.*aprobación/i);assert.match(ids['review-status'].textContent,/entregada/i);assert.equal([...timers.values()].filter(x=>x.delay===5000).length,0);assert.equal(requests.length,2);",
 'unavailable_cannot_enable_current_view': "await resolve(envelope({},'unavailable'));assert.equal(ids['review-approve'].disabled,true);assert.equal(ids['review-sections'].children.length,0);",
 'poll_keeps_comment_editing': "await resolve(envelope());textarea().value='Draft';textarea().focus();timer(5000);assert.equal(textarea().disabled,false,'poll must not blur the active comment every 5s');assert.equal(ids['review-approve'].disabled,true);await resolve(envelope({sections:undefined}));assert.equal(textarea().value,'Draft');",
 'multiple_comments_same_section_preserved': "const comments=[{comment_id:'existing-one',section_id:'d'.repeat(64),text:'Primero'},{comment_id:'existing-two',section_id:'d'.repeat(64),text:'Segundo'}];await resolve(envelope({draft_comments:comments}));ids['review-save'].events.click();assert.deepEqual(JSON.parse(requests[1].options.body).comments,comments);",
 'missing_canonical_history': "await resolve(envelope({validity:'unavailable',complete:false,redacted:null,controls_sanitized:null,current_version:null,sections:[],state:'consumida',decision:{decision_id:'e'.repeat(64),choice:'approve',comments:[],submitted_at:'2026-10-09T10:00:02Z'}},'unavailable'));assert.match(ids['review-status'].textContent,/canónico.*no disponible/i);assert.match(ids['review-status'].textContent,/histórico.*consumida/i);assert.equal(ids['review-approve'].disabled,true);assert.ok(ids['review-version'].textContent.includes('b'.repeat(64)));",
 'relative': "assert.equal(requests[0].url,'api/review/'+ 'a'.repeat(64)+'/view');assert.equal(requests[0].options.credentials,'omit');assert.ok(requests[0].options.signal);",
 'xss_text': "await resolve(envelope());assert.ok(ids['review-sections'].textContent.includes('<img src=x'));assert.ok(ids['review-sections'].textContent.includes('https://evil.test'));assert.equal(requests.length,1);assert.equal(textarea().dataset.sectionId,'d'.repeat(64));",
 'comments_version_cas': "await resolve(envelope());textarea().value='Revisar 🚀';ids['review-save'].events.click();assert.equal(requests[1].url,'api/review/'+ 'a'.repeat(64)+'/comments');const body=JSON.parse(requests[1].options.body);assert.deepEqual(body.version,version);assert.equal(body.expected_revision,0);assert.equal(body.comments[0].section_id,'d'.repeat(64));assert.equal(body.comments[0].text,'Revisar 🚀');",
 'approve': "await resolve(envelope());ids['review-approve'].events.click();assert.equal(JSON.parse(requests[1].options.body).choice,'approve');assert.ok(requests[1].url.endsWith('/submit'));",
 'changes_need_comment': "await resolve(envelope());ids['review-changes'].events.click();assert.equal(requests.length,1);assert.match(ids['review-status'].textContent,/comentario/i);textarea().value='Cambio';ids['review-changes'].events.click();assert.equal(JSON.parse(requests[1].options.body).choice,'request_changes');",
 'close_no_decision': "await resolve(envelope());textarea().value='Draft';ids['review-close'].events.click();assert.equal(requests.length,1);assert.equal(ids['review-sections'].hidden,true);assert.equal([...timers.values()].filter(x=>x.delay===5000).length,0);assert.match(ids['review-status'].textContent,/cerrar no crea.*decisión/i);ids['review-open'].events.click();assert.equal(textarea().value,'Draft');assert.ok(requests[1].url.endsWith('/status'));",
 'poll_no_overlap': "await resolve(envelope());timer(5000);assert.ok(requests[1].url.endsWith('/status'));ids['review-save'].events.click();assert.equal(requests.length,2);assert.equal([...timers.values()].filter(x=>x.delay===5000).length,0);await resolve(envelope({sections:undefined}));assert.equal([...timers.values()].filter(x=>x.delay===5000).length,1);",
 'hidden_pause': "await resolve(envelope());document.hidden=true;docEvents.visibilitychange();assert.equal([...timers.values()].filter(x=>x.delay===5000).length,0);document.hidden=false;docEvents.visibilitychange();assert.equal(requests.length,2);",
 'abort': "timer(4000);assert.equal(requests[0].options.signal.aborted,true);requests[0].reject(Error('private'));await settle();assert.match(ids['review-status'].textContent,/disponible|actualizar/i);assert.equal(ids['review-approve'].disabled,true);",
 'changed_invalidates': "await resolve(envelope());textarea().value='Old';timer(5000);await resolve(envelope({validity:'version_changed',current_version:{...version,raw_sha256:'e'.repeat(64)},sections:undefined},'version_changed'));assert.equal(ids['review-approve'].disabled,true);assert.equal(textarea().disabled,true);assert.equal(textarea().value,'');assert.match(ids['review-status'].textContent,/versión.*cambi/i);ids['review-refresh'].events.click();assert.deepEqual(JSON.parse(requests[2].options.body),{review_id:'a'.repeat(64)});await resolve(envelope({review_id:'f'.repeat(64),version:{...version,raw_sha256:'e'.repeat(64)},current_version:{...version,raw_sha256:'e'.repeat(64)}}));assert.equal(textarea().value,'');",
 'cas_conflict': "await resolve(envelope());textarea().value='Draft';ids['review-save'].events.click();await resolve({schema_version:1,status:'conflict',reason:'revision_conflict',review:null});assert.equal(ids['review-approve'].disabled,true);assert.match(ids['review-status'].textContent,/conflicto/i);",
 'history_consumed': "await resolve(envelope({state:'consumida',decision:{decision_id:'e'.repeat(64),choice:'approve',comments:[],submitted_at:'2026-10-09T10:00:02Z'},consumer_registration:{caller_id:'dev-cycle',runtime:'codex',registered_at:'2026-10-09T10:00:00Z'}}));assert.match(ids['review-status'].textContent,/consumida/i);assert.match(ids['review-metadata'].textContent,/actividad desconocida/i);assert.equal(ids['review-approve'].disabled,true);assert.equal(requests.length,1);",
 'redaction': "await resolve(envelope({redacted:true,controls_sanitized:true}));assert.match(ids['review-metadata'].textContent,/redactad/i);assert.match(ids['review-metadata'].textContent,/no.*secretos/i);",
 'unicode_comment_limit': "await resolve(envelope());textarea().value='🚀'.repeat(2000);ids['review-save'].events.click();assert.equal(requests.length,2);assert.equal(JSON.parse(requests[1].options.body).comments[0].text.length,4000);",
 'unicode_over_limit': "await resolve(envelope());textarea().value='🚀'.repeat(2001);ids['review-save'].events.click();assert.equal(requests.length,1);assert.match(ids['review-status'].textContent,/límite/i);",
 'bad_projection': "await resolve(envelope({version:{...version,raw_sha256:'../private'}}));assert.equal(ids['review-approve'].disabled,true);assert.equal(ids['review-sections'].children.length,0);",
 'absent_consumer': "await resolve(envelope());assert.match(ids['review-metadata'].textContent,/sin consumidor registrado/i);assert.match(ids['review-metadata'].textContent,/no.*autentic/i);",
 'status_preserves_dom_draft': "await resolve(envelope());textarea().value='Draft';const node=textarea();timer(5000);await resolve(envelope({sections:undefined}));assert.equal(textarea(),node);assert.equal(textarea().value,'Draft');",
 'status_other_tab_decision': "await resolve(envelope());textarea().value='Draft';timer(5000);await resolve(envelope({sections:undefined,revision:1,decision:{decision_id:'e'.repeat(64),choice:'request_changes',comments:[],submitted_at:'2026-10-09T10:00:02Z'}}));assert.equal(ids['review-approve'].disabled,true);assert.match(ids['review-status'].textContent,/cambios/i);",
 'closed_pending_response': "ids['review-close'].events.click();await resolve(envelope());assert.equal(ids['review-sections'].hidden,true);assert.equal(ids['review-approve'].disabled,true);assert.equal([...timers.values()].filter(x=>x.delay===5000).length,0);",
}

@pytest.mark.parametrize('scenario', SCENARIOS)
def test_review_controller(panel, scenario, tmp_path):
    node = shutil.which('node')
    if not node: pytest.skip('Node unavailable for isolated controller test')
    output = panel.render_html(DATA, live=True, review_enabled=True)
    script = next(script for script in re.findall(r'<script[^>]*>(.*?)</script>', output, re.S) if 'api/review/' in script)
    source = tmp_path / 'review.cjs'
    source.write_text(HARNESS+'\n'+script+'\n(async()=>{'+SCENARIOS[scenario]+'})().catch(error=>{console.error(error);process.exitCode=1;});', encoding='utf8')
    result = subprocess.run([node, str(source)], capture_output=True, text=True, encoding='utf8', errors='replace', timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
