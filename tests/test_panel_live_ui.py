"""Served progress UI preserves provenance, bounded DOM and offline behavior."""
import importlib.util
from pathlib import Path
import re
import shutil
import subprocess

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / 'skills/plugin-panel/scripts/build_panel.py'


@pytest.fixture
def panel(tmp_path, monkeypatch):
    own = tmp_path / 'home'
    own.mkdir()
    for key in ('HOME', 'USERPROFILE', 'CODEX_HOME', 'CLAUDE_CONFIG_DIR',
                'APPDATA', 'LOCALAPPDATA', 'XDG_CONFIG_HOME'):
        monkeypatch.setenv(key, str(own))
    spec = importlib.util.spec_from_file_location('panel_live_ui', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def inventory():
    return {'counts': dict.fromkeys(('agents', 'skills', 'commands', 'tools', 'hooks'), 0),
            'agents': [], 'skills': [], 'commands': [], 'tools': [], 'hooks': [],
            'runtimes': {}, 'memory': {}, 'warnings': [], 'workflow': {'roles': {}}}


def test_default_offline_has_no_operational_fetch(panel, inventory):
    output = panel.render_html(inventory)
    assert 'id="operations"' not in output
    assert 'api/progress' not in output
    assert "connect-src 'self'" not in output
    assert 'Instantánea local' in output
    assert '@@' not in output


def test_live_render_has_progress_controls_and_same_origin_csp(panel, inventory):
    output = panel.render_html(inventory, live=True)
    assert 'id="operations"' in output and 'href="#operations"' in output
    for field in ('progress-refresh', 'progress-search', 'progress-state',
                  'progress-status', 'progress-freshness', 'progress-cards'):
        assert 'id="' + field + '"' in output
    assert "connect-src 'self'" in output
    assert 'api/progress' in output and 'agentes vivos' in output
    assert 'Catálogo y diagnóstico' in output
    assert '@@' not in output


def test_live_asset_absent_is_opaque_and_offline_remains_available(panel, inventory, tmp_path, monkeypatch):
    template = tmp_path / 'panel.html'
    template.write_text(panel.TEMPLATE.read_text(encoding='utf8'), encoding='utf8')
    monkeypatch.setattr(panel, 'TEMPLATE', template)
    with pytest.raises(ValueError, match='bundled live panel asset unavailable'):
        panel.render_html(inventory, live=True)
    assert panel.render_html(inventory)


def _live_script(panel, inventory):
    output = panel.render_html(inventory, live=True)
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', output, re.S)
    return next(script for script in scripts if 'api/progress' in script)


HARNESS = r'''
const assert=require('node:assert/strict');
class Element {
 constructor(tag='div'){this.tagName=tag;this.children=[];this.events={};this.value='';this.hidden=false;this.disabled=false;this.className='';this.dataset={};this._text='';}
 set textContent(value){this._text=String(value);this.children=[];}
 get textContent(){return this._text+this.children.map(x=>x.textContent).join('');}
 set innerHTML(value){throw Error('Untrusted HTML assignment');}
 append(...nodes){this.children.push(...nodes.map(n=>typeof n==='string'?Object.assign(new Element(),{textContent:n}):n));}
 appendChild(node){this.append(node);return node;}
 replaceChildren(...nodes){this.children=[];this._text='';this.append(...nodes);}
 addEventListener(type,callback){this.events[type]=callback;}
 setAttribute(key,value){this[key]=value;}
}
const ids={};for(const id of ['operations','progress-refresh','progress-search','progress-state','progress-status','progress-freshness','progress-cards','progress-results'])ids[id]=new Element();
ids['progress-state'].value='all';
const documentEvents={};
global.document={hidden:false,getElementById(id){return ids[id]||null;},createElement(tag){return new Element(tag);},addEventListener(type,callback){documentEvents[type]=callback;}};
let sequence=0;const timers=new Map();
global.setTimeout=(callback,delay)=>{timers.set(++sequence,{callback,delay});return sequence;};
global.clearTimeout=id=>timers.delete(id);
const requests=[];global.fetch=(url,options)=>new Promise((resolve,reject)=>requests.push({url,options,resolve,reject}));
const report=(overrides={})=>Object.assign({version:1,source:'canonical_ledger',observed_at:'2026-10-09T10:00:00Z',status:'ok',complete:true,initiatives:[{id:'a'.repeat(16),title:'Proyecto <img src=x onerror=alert(1)>',estado:'en-progreso',total:3,completadas:1,pct:33,fase:{indice:1,total:2,nombre:'Implementar'},en_progreso:[{id:'T-02',titulo:'Construir'}],source_sha256:'b'.repeat(64)}],issues:[]},overrides);
const settle=async()=>{for(let i=0;i<8;i++)await Promise.resolve();};
const resolve=async(data,index=requests.length-1)=>{requests[index].resolve({ok:true,json:async()=>data});await settle();};
const runTimer=delay=>{const found=[...timers].find(([,value])=>value.delay===delay);assert.ok(found,'timer '+delay+' exists');timers.delete(found[0]);found[1].callback();};
'''


SCENARIOS = {
    'relative_endpoint': "assert.equal(requests[0].url,'api/progress');assert.equal(requests[0].options.credentials,'omit');assert.ok(requests[0].options.signal);",
    'text_dom': "await resolve(report());assert.ok(ids['progress-cards'].textContent.includes('<img src=x'));assert.ok(ids['progress-cards'].textContent.includes('T-02'));assert.equal(ids['progress-cards'].children.length,1);",
    'filters': "await resolve(report());ids['progress-search'].value='no matches';ids['progress-search'].events.input();assert.equal(ids['progress-cards'].children[0].hidden,true);ids['progress-search'].value='';ids['progress-state'].value='completado';ids['progress-state'].events.change();assert.equal(ids['progress-cards'].children[0].hidden,true);ids['progress-state'].value='all';ids['progress-state'].events.change();assert.equal(ids['progress-cards'].children[0].hidden,false);",
    'polling': "await resolve(report());runTimer(5000);assert.equal(requests.length,2);assert.equal([...timers.values()].filter(t=>t.delay===5000).length,0);requests[1].reject(Error('network'));await settle();assert.equal([...timers.values()].filter(t=>t.delay===5000).length,1);",
    'no_overlap': "ids['progress-refresh'].events.click();ids['progress-refresh'].events.click();assert.equal(requests.length,1);await resolve(report());ids['progress-refresh'].events.click();assert.equal(requests.length,2);",
    'preserve_after_failure': "await resolve(report());const content=ids['progress-cards'].textContent;const date=ids['progress-freshness'].textContent;ids['progress-refresh'].events.click();requests[1].reject(Error('PRIVATE_FAILURE'));await settle();assert.equal(ids['progress-cards'].textContent,content);assert.equal(ids['progress-freshness'].textContent,date);assert.match(ids['progress-status'].textContent,/anterior|última/i);assert.ok(!ids['progress-status'].textContent.includes('PRIVATE_FAILURE'));",
    'partial_replaces': "await resolve(report());ids['progress-refresh'].events.click();await resolve(report({status:'partial',complete:false,observed_at:'2026-10-09T10:01:00Z',initiatives:[],issues:[{status:'too_large'}]}));assert.equal(ids['progress-cards'].children.length,0);assert.match(ids['progress-status'].textContent,/parcial/i);assert.ok(ids['progress-freshness'].textContent.includes('10:01'));",
    'hidden_suspend': "await resolve(report());document.hidden=true;documentEvents.visibilitychange();assert.equal([...timers.values()].filter(t=>t.delay===5000).length,0);ids['progress-refresh'].events.click();assert.equal(requests.length,1);document.hidden=false;documentEvents.visibilitychange();assert.equal(requests.length,2);",
    'timeout': "runTimer(4000);assert.equal(requests[0].options.signal.aborted,true);requests[0].reject(Error('aborted'));await settle();assert.match(ids['progress-status'].textContent,/actualizar|disponible/i);assert.equal(ids['progress-refresh'].disabled,false);",
    'bad_version': "await resolve(report({version:2}));assert.match(ids['progress-status'].textContent,/actualizar|disponible/i);assert.equal(ids['progress-cards'].children.length,0);",
    'bad_count': "const data=report();data.initiatives[0].completadas=99;await resolve(data);assert.equal(ids['progress-cards'].children.length,0);assert.match(ids['progress-status'].textContent,/actualizar|disponible/i);",
    'empty_not_found': "await resolve(report({status:'not_found',initiatives:[]}));assert.match(ids['progress-status'].textContent,/ledger|iniciativa/i);assert.equal(ids['progress-cards'].children.length,0);",
    'unavailable_preserves': "await resolve(report());const before=ids['progress-cards'].textContent;ids['progress-refresh'].events.click();await resolve(report({status:'unavailable',complete:false,initiatives:[]}));assert.equal(ids['progress-cards'].textContent,before);assert.match(ids['progress-status'].textContent,/anterior|última/i);",
    'manual_clears_poll': "await resolve(report());ids['progress-refresh'].events.click();assert.equal([...timers.values()].filter(t=>t.delay===5000).length,0);assert.equal(requests.length,2);",
    'schema_provenance': "await resolve(report({source:'other'}));assert.equal(ids['progress-cards'].children.length,0);assert.match(ids['progress-status'].textContent,/actualizar|disponible/i);",
    'preserve_dom_unchanged': "await resolve(report());const first=ids['progress-cards'].children[0];ids['progress-refresh'].events.click();await resolve(report({observed_at:'2026-10-09T10:01:00Z'}));assert.equal(ids['progress-cards'].children[0],first,'unchanged ledger must preserve expanded detail and focus DOM');assert.ok(ids['progress-freshness'].textContent.includes('10:01'));",
    'unknown_state': "const data=report({status:'partial',complete:false});data.initiatives[0].estado='unknown';await resolve(data);assert.ok(ids['progress-cards'].textContent.includes('Sin estado reconocido'));assert.match(ids['progress-status'].textContent,/parcial/i);",
    'bad_hash': "const data=report();data.initiatives[0].source_sha256='../private';await resolve(data);assert.equal(ids['progress-cards'].children.length,0);",
    'bad_timestamp': "await resolve(report({observed_at:'not a UTC time'}));assert.equal(ids['progress-cards'].children.length,0);",
    'boolean_count': "const data=report();data.initiatives[0].total=true;await resolve(data);assert.equal(ids['progress-cards'].children.length,0);",
    'bounded_tasks': "const data=report();data.initiatives[0].en_progreso=Array(9).fill({id:'T-02',titulo:'oversized'});await resolve(data);assert.equal(ids['progress-cards'].children.length,0);",
    'unicode_title_limit': "const data=report();data.initiatives[0].title='🚀'.repeat(160);await resolve(data);assert.equal(ids['progress-cards'].children.length,1,'160 Unicode characters are within producer contract');",
    'initiative_limit_accept': "const data=report();data.initiatives=Array.from({length:64},(_,i)=>Object.assign({},data.initiatives[0],{id:i.toString(16).padStart(16,'0')}));await resolve(data);assert.equal(ids['progress-cards'].children.length,64);",
    'initiative_limit_reject': "const data=report();data.initiatives=Array.from({length:65},(_,i)=>Object.assign({},data.initiatives[0],{id:i.toString(16).padStart(16,'0')}));await resolve(data);assert.equal(ids['progress-cards'].children.length,0);",
    'task_id_producer_limit': "const data=report();data.initiatives[0].en_progreso[0].id='T-'+ '1'.repeat(18);await resolve(data);assert.equal(ids['progress-cards'].children.length,1,'producer allows20character task references');",
    'task_id_over_limit': "const data=report();data.initiatives[0].en_progreso[0].id='T-'+ '1'.repeat(19);await resolve(data);assert.equal(ids['progress-cards'].children.length,0);",
}


@pytest.mark.parametrize('scenario', SCENARIOS)
def test_live_progress_controller(panel, inventory, scenario, tmp_path):
    node = shutil.which('node')
    if not node:
        pytest.skip('Node unavailable for isolated live UI controller tests')
    script = _live_script(panel, inventory)
    program = HARNESS + '\n' + script + '\n(async()=>{' + SCENARIOS[scenario] + '})().catch(error=>{console.error(error);process.exitCode=1;});'
    source = tmp_path / 'controller.cjs'
    source.write_text(program, encoding='utf8')
    result = subprocess.run([node, str(source)], capture_output=True, text=True,
                            encoding='utf8', errors='replace', timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
