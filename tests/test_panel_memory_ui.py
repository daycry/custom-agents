"""Explicit memory actions reuse the existing isolated DOM/fetch harness."""
import re
import shutil
import subprocess

import pytest
from test_panel_live_ui import HARNESS, inventory, panel


def script(panel, inventory):
    output = panel.render_html(inventory, live=True)
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', output, re.S)
    return next(source for source in scripts if 'api/memory' in source)


def test_memory_only_served_with_accessible_controls(panel, inventory):
    offline = panel.render_html(inventory)
    assert 'api/memory' not in offline and 'id="memory-query"' not in offline
    output = panel.render_html(inventory, live=True)
    for selector in ('memory-query', 'memory-form', 'memory-text', 'memory-area', 'memory-type',
                     'memory-search', 'memory-status', 'memory-freshness', 'memory-results',
                     'memory-selected', 'memory-related'):
        assert f'id="{selector}"' in output
    assert 'href="#memory-query"' in output
    assert 'type="submit"' in output and 'aria-label="Buscar conocimiento"' in output
    assert '@@' not in output


SETUP = r'''
for(const id of ['memory-query','memory-form','memory-text','memory-area','memory-type','memory-search','memory-status','memory-freshness','memory-results-date','memory-results','memory-selected','memory-related'])ids[id]=new Element();
Element.prototype.focus=function(){document.activeElement=this;};
const entry=(overrides={})=>Object.assign({id:'LES-001',tipo:'LES',estado:'aceptada',estado_detalle:'Vigente',titular:'Conocimiento <img src=x>',area:'planning',version:null,category:null,evidencia:'single_case',ruta:'docs/knowledge/lessons/LES-001.md',source_sha256:'b'.repeat(64),origen:'legacy'},overrides);
const memory=(operation='search',overrides={})=>Object.assign({version:1,source:'canonical_knowledge',observed_at:'2026-10-09T10:00:00Z',operation,status:'ok',complete:true,issues:[],entries:operation==='search'?[entry()]:[],selected:operation==='show'?entry({texto:'# Body <script>alert(1)</script>'}):null,related:operation==='related'?{sucesion:[],iniciativa:[],area:[entry({id:'LES-002'})],enlaces:[]}:null,budget:{files:2,bytes:600,entries:3}},overrides);
const submit=()=>ids['memory-form'].events.submit({preventDefault(){}});
const buttons=node=>node.children.flatMap(child=>child.tagName==='button'?[child]:buttons(child));
const show=()=>buttons(ids['memory-results'])[0].events.click();
const related=()=>buttons(ids['memory-results'])[1].events.click();
'''


SCENARIOS = {
    'bounded_scan_budget': "for(const scans of [257,-1,true,1.5,'1']){submit();await resolve(memory('search',{budget:{files:2,bytes:600,entries:3,scans}}));assert.equal(ids['memory-results'].children.length,0);}submit();await resolve(memory('search',{budget:{files:2,bytes:600,entries:3,scans:256}}));assert.equal(ids['memory-results'].children.length,1);",
    'no_auto_query': "assert.equal(requests.length,0);assert.equal(timers.size,0);ids['memory-text'].value='hi';assert.equal(requests.length,0);",
    'explicit_post': "ids['memory-text'].value='test';submit();assert.equal(requests.length,1);assert.equal(requests[0].url,'api/memory');assert.equal(requests[0].options.method,'POST');assert.equal(requests[0].options.credentials,'omit');assert.equal(requests[0].options.cache,'no-store');assert.equal(requests[0].options.headers['Content-Type'],'application/json');assert.deepEqual(JSON.parse(requests[0].options.body),{operation:'search',text:'test',area:'',tipo:'',limit:20});",
    'no_overlap': "submit();submit();assert.equal(requests.length,1);await resolve(memory());submit();assert.equal(requests.length,2);",
    'text_dom': "submit();await resolve(memory());assert.ok(ids['memory-results'].textContent.includes('<img src=x>'));assert.ok(ids['memory-results'].textContent.includes('LES-001'));assert.ok(!ids['memory-results'].textContent.includes('# Body'));assert.equal(buttons(ids['memory-results']).length,2);assert.equal(requests.length,1);",
    'show_explicit': "submit();await resolve(memory());show();assert.deepEqual(JSON.parse(requests[1].options.body),{operation:'show',id:'LES-001'});await resolve(memory('show'));assert.ok(ids['memory-selected'].textContent.includes('# Body <script>'));assert.ok(ids['memory-selected'].textContent.includes('single_case'));assert.ok(ids['memory-selected'].textContent.includes('b'.repeat(64)));assert.equal(document.activeElement,ids['memory-selected']);",
    'related_explicit': "submit();await resolve(memory());related();assert.deepEqual(JSON.parse(requests[1].options.body),{operation:'related',id:'LES-001'});await resolve(memory('related'));assert.ok(ids['memory-related'].textContent.includes('LES-002'));assert.equal(requests.length,2);",
    'search_clears_selection': "submit();await resolve(memory());show();await resolve(memory('show'));related();await resolve(memory('related'));submit();await resolve(memory({},{operation:'search',entries:[]}));assert.equal(ids['memory-selected'].children.length,0);assert.equal(ids['memory-related'].children.length,0);",
    'failure_preserves': "submit();await resolve(memory());const before=ids['memory-results'].textContent,date=ids['memory-freshness'].textContent;submit();requests[1].reject(Error('PRIVATE_FAILURE'));await settle();assert.equal(ids['memory-results'].textContent,before);assert.equal(ids['memory-freshness'].textContent,date);assert.match(ids['memory-status'].textContent,/anterior|última/i);assert.ok(!ids['memory-status'].textContent.includes('PRIVATE_FAILURE'));",
    'unavailable_preserves': "submit();await resolve(memory());const before=ids['memory-results'].textContent,date=ids['memory-freshness'].textContent;submit();await resolve(memory('search',{status:'unavailable',complete:false,entries:[]}));assert.equal(ids['memory-results'].textContent,before);assert.equal(ids['memory-freshness'].textContent,date);assert.match(ids['memory-status'].textContent,/anterior|última/i);",
    'ambiguous_no_selection': "submit();await resolve(memory());show();await resolve(memory('show'));show();await resolve(memory('show',{status:'ambiguous',complete:false,selected:null}));assert.equal(ids['memory-selected'].children.length,0);assert.match(ids['memory-status'].textContent,/ambigua|colisión/i);",
    'partial': "submit();await resolve(memory('search',{status:'partial',complete:false,issues:['scan_budget']}));assert.match(ids['memory-status'].textContent,/parcial/i);assert.equal(ids['memory-results'].children.length,1);",
    'not_found': "submit();await resolve(memory('search',{status:'not_found',entries:[]}));assert.match(ids['memory-status'].textContent,/encontr|coinciden/i);",
    'deadline': "submit();runTimer(6000);assert.equal(requests[0].options.signal.aborted,true);requests[0].reject(Error('abort'));await settle();assert.equal(ids['memory-search'].disabled,false);assert.match(ids['memory-status'].textContent,/disponible|consultar/i);",
    'request_unicode_budget': "ids['memory-text'].value='🚀'.repeat(1000);submit();assert.equal(requests.length,1);requests[0].reject(Error('stop'));await settle();ids['memory-text'].value='🚀'.repeat(1001);submit();assert.equal(requests.length,1);",
    'request_json_budget': "ids['memory-text'].value='🚀'.repeat(1000);ids['memory-area'].value='x'.repeat(160);submit();assert.equal(requests.length,0);assert.match(ids['memory-status'].textContent,/límite/i);",
    'full_unicode_id': "submit();await resolve(memory('search',{entries:[entry({id:'🚀'.repeat(256),titular:'🚀'.repeat(160)})]}));show();assert.equal(JSON.parse(requests[1].options.body).id,'🚀'.repeat(256));",
    'bad_version': "submit();await resolve(memory('search',{version:2}));assert.equal(ids['memory-results'].children.length,0);",
    'bad_source': "submit();await resolve(memory('search',{source:'other'}));assert.equal(ids['memory-results'].children.length,0);",
    'bad_timestamp': "submit();await resolve(memory('search',{observed_at:'yesterday'}));assert.equal(ids['memory-results'].children.length,0);",
    'bad_complete': "submit();await resolve(memory('search',{complete:'yes'}));assert.equal(ids['memory-results'].children.length,0);",
    'bad_budget': "submit();await resolve(memory('search',{budget:{files:true,bytes:1,entries:1}}));assert.equal(ids['memory-results'].children.length,0);",
    'bounded_entries': "submit();await resolve(memory('search',{entries:Array(21).fill(entry())}));assert.equal(ids['memory-results'].children.length,0);",
    'bounded_id': "submit();await resolve(memory('search',{entries:[entry({id:'x'.repeat(257)})]}));assert.equal(ids['memory-results'].children.length,0);",
    'bad_hash': "submit();await resolve(memory('search',{entries:[entry({source_sha256:'../secret'})]}));assert.equal(ids['memory-results'].children.length,0);",
    'bad_evidence': "submit();await resolve(memory('search',{entries:[entry({evidencia:[]})]}));assert.equal(ids['memory-results'].children.length,0);",
    'no_body_in_search': "submit();await resolve(memory('search',{selected:entry({texto:'secret'})}));assert.equal(ids['memory-results'].children.length,0);",
    'mismatched_operation': "submit();await resolve(memory('show'));assert.equal(ids['memory-results'].children.length,0);",
    'mismatched_show_id': "submit();await resolve(memory());show();await resolve(memory('show',{selected:entry({id:'LES-OTHER',texto:'wrong'})}));assert.equal(ids['memory-selected'].children.length,0);",
    'bounded_body': "submit();await resolve(memory());show();await resolve(memory('show',{selected:entry({texto:'🚀'.repeat(12000)})}));assert.ok(ids['memory-selected'].textContent.includes('🚀'.repeat(12000)));",
    'body_over_budget': "submit();await resolve(memory());show();await resolve(memory('show',{selected:entry({texto:'x'.repeat(12001)})}));assert.equal(ids['memory-selected'].children.length,0);",
    'relations_total_budget': "submit();await resolve(memory());related();await resolve(memory('related',{related:{sucesion:[],iniciativa:Array(11).fill(entry()),area:Array(10).fill(entry()),enlaces:[]}}));assert.equal(ids['memory-related'].children.length,0);",
    'unresolved_successor': "submit();await resolve(memory());related();await resolve(memory('related',{status:'partial',complete:false,related:{sucesion:[{relation:'supersedes',id:'LES-MISSING',entry:null}],iniciativa:[],area:[],enlaces:[]}}));assert.ok(ids['memory-related'].textContent.includes('LES-MISSING'));assert.ok(ids['memory-related'].textContent.includes('sin resolver'));",
    'provenance_per_view': "submit();await resolve(memory());const date=ids['memory-results-date'].textContent;show();await resolve(memory('show',{observed_at:'2026-10-09T10:01:00Z'}));assert.equal(ids['memory-results-date'].textContent,date);assert.ok(ids['memory-selected'].textContent.includes('10:01'));",
    'http_failure_preserves': "submit();await resolve(memory());const before=ids['memory-results'].textContent;submit();requests[1].resolve({ok:false});await settle();assert.equal(ids['memory-results'].textContent,before);",
    'abort_late_success_preserves': "submit();await resolve(memory());const before=ids['memory-results'].textContent,date=ids['memory-freshness'].textContent;submit();runTimer(6000);await resolve(memory('search',{entries:[],observed_at:'2026-10-09T10:01:00Z'}));assert.equal(ids['memory-results'].textContent,before);assert.equal(ids['memory-freshness'].textContent,date);",
    'ambiguous_payload_cannot_choose_entry': "submit();await resolve(memory());const date=ids['memory-freshness'].textContent;show();await resolve(memory('show',{status:'ambiguous',complete:false,selected:entry({texto:'must not render'}),observed_at:'2026-10-09T10:01:00Z'}));assert.equal(ids['memory-selected'].children.length,0);assert.equal(ids['memory-freshness'].textContent,date);assert.match(ids['memory-status'].textContent,/anterior/i);",
    'literal_id_roundtrip': "const id='project:DEC-001/variant';submit();await resolve(memory('search',{entries:[entry({id})]}));show();assert.deepEqual(JSON.parse(requests[1].options.body),{operation:'show',id});await resolve(memory('show',{selected:entry({id,texto:'Literal identity body'})}));related();assert.deepEqual(JSON.parse(requests[2].options.body),{operation:'related',id});await resolve(memory('related'));assert.ok(ids['memory-related'].textContent.includes('LES-002'));",
    'exact_large_knowledge_version': "const version='9007199254740993';submit();await resolve(memory('search',{entries:[entry({version})]}));assert.ok(ids['memory-results'].textContent.includes(version));show();await resolve(memory('show',{selected:entry({version,texto:'Large exact version'})}));assert.ok(ids['memory-selected'].textContent.includes(version));",
    'invalid_knowledge_versions_rejected': "for(const version of [-1,0,true,9007199254740992,'-1','01','0','1e20','x','1'.repeat(4301)]){submit();await resolve(memory('search',{entries:[entry({version})]}));assert.equal(ids['memory-results'].children.length,0);}",
}


@pytest.mark.parametrize('scenario', SCENARIOS)
def test_explicit_memory_controller(panel, inventory, scenario, tmp_path):
    node = shutil.which('node')
    if not node:
        pytest.skip('Node unavailable for isolated UI controller tests')
    source = tmp_path / 'memory-controller.cjs'
    source.write_text(HARNESS + '\n' + SETUP + '\n' + script(panel, inventory) + '\n(async()=>{' +
                      SCENARIOS[scenario] + '})().catch(error=>{console.error(error);process.exitCode=1;});', encoding='utf8')
    result = subprocess.run([node, str(source)], capture_output=True, encoding='utf8', errors='replace', timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
