const {test,expect}=require('@playwright/test');
const fs=require('node:fs');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const url=process.env.PANEL_LIVE_URL,origin=new URL(url).origin;
const fullId=process.env.PANEL_MEMORY_FULL_ID;
let external=[],memoryRequests=[];

function memoryEndpoint(request){return request.url().endsWith('/api/memory');}
async function search(page,text='cache'){
 await page.locator('#memory-text').fill(text);
 const response=page.waitForResponse(value=>value.url().endsWith('/api/memory'));
 await page.locator('#memory-search').click();const result=await response;
 await expect(page.locator('#memory-search')).toBeEnabled();return result.ok()?result.json():null;
}
function result(page,id){return page.locator('#memory-results .memory-card').filter({has:page.getByText(id,{exact:true})});}
async function action(page,card,label){
 const response=page.waitForResponse(value=>value.url().endsWith('/api/memory'));
 await card.getByRole('button',{name:label,exact:true}).click();const data=await response;
 await expect(page.locator('#memory-search')).toBeEnabled();return data.json();
}

test.beforeAll(async({browser})=>{
 fs.writeFileSync(process.env.PANEL_BROWSER_METADATA,JSON.stringify({browser_version:browser.version()}),'utf8');
});
test.beforeEach(async({page,context})=>{
 external=[];memoryRequests=[];
 fs.writeFileSync(process.env.PANEL_MEMORY_OMITTED,process.env.PANEL_MEMORY_OMITTED_INITIAL,'utf8');
 if(fs.existsSync(process.env.PANEL_MEMORY_COLLISION))fs.unlinkSync(process.env.PANEL_MEMORY_COLLISION);
 await context.route('**/*',async route=>{
  if(/^https?:/.test(route.request().url())&&new URL(route.request().url()).origin!==origin){external.push('forbidden origin');await route.abort();return;}
  await route.continue();
 });
 await context.addCookies([{name:'owned_memory_fixture_cookie',value:'synthetic',url:origin}]);
 page.on('request',request=>{if(memoryEndpoint(request))memoryRequests.push(request);});
 await page.goto(url);await expect(page.locator('#progress-refresh')).toBeEnabled();
});
test.afterEach(()=>{expect(external).toEqual([]);});

test('M-01 loading and progress polling never query memory automatically',async({page})=>{
 await expect(page.locator('#memory-status')).toContainText('Sin consultas realizadas');
 expect(memoryRequests).toHaveLength(0);
 const poll=page.waitForRequest(request=>request.url().endsWith('/api/progress'));
 await poll;
 await page.locator('#memory-text').fill('edited without submit');
 expect(memoryRequests).toHaveLength(0);
 await expect(page.locator('#memory-results .memory-card')).toHaveCount(0);
});

test('M-02 desktop search/show preserve full identity and provenance under real CSP',async({page})=>{
 const errors=[];page.on('pageerror',error=>errors.push(error.message));
 const response=await page.reload();expect(response.headers()['content-security-policy']).toMatch(/script-src 'nonce-/);
 expect(await page.locator('script').evaluateAll(nodes=>nodes.every(node=>Boolean(node.nonce)))).toBe(true);
 await page.locator('.sidebar nav a[href="#memory-query"]').click();
 await expect(page.locator('#memory-query')).toBeFocused();
 await expect(page.locator('.sidebar nav a[href="#memory-query"]')).toHaveAttribute('aria-current','location');
 const data=await search(page);expect(data.source).toBe('canonical_knowledge');
 expect(data.entries.some(entry=>entry.id===fullId&&entry.origen==='approved'&&entry.version===2)).toBe(true);
 expect(JSON.stringify(data)).not.toContain('OWNED_BODY_ONLY');
 await expect(page.locator('#memory-selected')).toBeEmpty();
 const shown=await action(page,result(page,fullId),'Ver entrada');
 expect(shown.selected.id).toBe(fullId);expect(shown.selected.category).toBe('DECISION');
 expect(shown.selected.evidencia).toBe('human_confirmed_rule');
 await expect(page.locator('#memory-selected')).toContainText(fullId);
 await expect(page.locator('#memory-selected')).toContainText('Versión: 2');
 await expect(page.locator('#memory-selected')).toContainText('OWNED_BODY_ONLY');
 await expect(page.locator('#memory-selected')).toContainText(shown.selected.source_sha256);
 await expect(page.locator('#memory-selected')).toBeFocused();
 expect(memoryRequests.every(request=>request.method()==='POST'&&!request.headers().cookie)).toBe(true);
 expect(errors).toEqual([]);
 await page.screenshot({path:path.join(process.env.PANEL_SCREENSHOTS,'memory-desktop.png'),fullPage:true});
});

test('M-03 relations are requested explicitly and a fresh search clears old details',async({page})=>{
 await search(page,'ADR-001');
 const before=memoryRequests.length;const relation=await action(page,result(page,'ADR-001'),'Ver relaciones');
 expect(memoryRequests).toHaveLength(before+1);expect(relation.operation).toBe('related');
 expect(relation.related.sucesion.some(row=>row.id==='ADR-002')).toBe(true);
 await expect(page.locator('#memory-related')).toContainText('ADR-002');
 await expect(page.locator('#memory-related')).toBeFocused();
 await action(page,result(page,'ADR-001'),'Ver entrada');
 await expect(page.locator('#memory-selected')).not.toBeEmpty();
 await search(page,'unmatched-owned-query');
 await expect(page.locator('#memory-selected')).toBeEmpty();
 await expect(page.locator('#memory-related')).toBeEmpty();
});

test('M-04 HTTP invalid and unavailable replies preserve prior view and date',async({page})=>{
 await search(page);const before=await page.locator('#memory-results').textContent(),date=await page.locator('#memory-freshness').textContent();
 for(const mode of ['http','invalid','unavailable']){
  await page.route('**/api/memory',async route=>{
   if(mode==='http'){await route.fulfill({status:503,body:'owned failure'});return;}
   const data=mode==='invalid'?{version:99}:{version:1,source:'canonical_knowledge',observed_at:'2026-10-09T10:00:00Z',operation:'search',status:'unavailable',complete:false,issues:['helper_unavailable'],entries:[],selected:null,related:null,budget:{files:0,bytes:0,entries:0}};
   await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(data)});
  });
  await search(page);await expect(page.locator('#memory-status')).toContainText('fecha anterior');
  expect(await page.locator('#memory-results').textContent()).toBe(before);
  expect(await page.locator('#memory-freshness').textContent()).toBe(date);
  await page.unroute('**/api/memory');
 }
});

test('M-05 keyboard and mobile permit explicit search and selection without overflow',async({page})=>{
 await page.setViewportSize({width:390,height:844});
 await page.locator('.sidebar nav a[href="#memory-query"]').click();
 await page.locator('#memory-text').fill('cache');
 await page.locator('#memory-text').focus();await page.keyboard.press('Tab');
 await expect(page.locator('#memory-area')).toBeFocused();await page.keyboard.press('Tab');
 await expect(page.locator('#memory-type')).toBeFocused();await page.keyboard.press('Tab');
 await expect(page.locator('#memory-search')).toBeFocused();
 const requested=page.waitForResponse(response=>response.url().endsWith('/api/memory'));
 await page.keyboard.press('Enter');await requested;await expect(page.locator('#memory-search')).toBeEnabled();
 await result(page,fullId).getByRole('button',{name:'Ver entrada',exact:true}).focus();
 const selected=page.waitForResponse(response=>response.url().endsWith('/api/memory'));
 await page.keyboard.press('Enter');await selected;await expect(page.locator('#memory-selected')).toBeFocused();
 expect(await page.evaluate(()=>Math.max(document.documentElement.scrollWidth,document.body.scrollWidth)<=innerWidth+1)).toBe(true);
 await page.screenshot({path:path.join(process.env.PANEL_SCREENSHOTS,'memory-mobile.png'),fullPage:true});
});

test('M-06 canonical partial collision and untrusted text remain explicit and safe',async({page})=>{
 fs.writeFileSync(process.env.PANEL_MEMORY_OMITTED,'x'.repeat(256*1024+1),'utf8');
 const partial=await search(page);expect(partial.status).toBe('partial');expect(partial.complete).toBe(false);
 await expect(page.locator('#memory-status')).toContainText('Lectura parcial');
 const shown=await action(page,result(page,fullId),'Ver entrada');
 expect(JSON.stringify(shown)).not.toContain(process.env.PANEL_MEMORY_SYNTHETIC_SECRET);
 await expect(page.locator('#memory-selected')).toContainText('<img src=x');
 expect(await page.evaluate(()=>globalThis.__memory_injected)).toBeUndefined();
 fs.mkdirSync(path.dirname(process.env.PANEL_MEMORY_COLLISION),{recursive:true});
 fs.writeFileSync(process.env.PANEL_MEMORY_COLLISION,process.env.PANEL_MEMORY_COLLISION_BODY,'utf8');
 await search(page,'ADR-001');
 const collision=page.locator('#memory-results .memory-card').filter({has:page.getByText('ADR-001',{exact:true})});
 const ambiguous=await action(page,collision.first(),'Ver entrada');
 expect(ambiguous.status).toBe('ambiguous');expect(ambiguous.selected).toBeNull();
 await expect(page.locator('#memory-status')).toContainText('Identidad ambigua');
 await expect(page.locator('#memory-selected')).toBeEmpty();
});

test('M-07 offline export has no memory section script or requests',async({page})=>{
 const network=[];page.on('request',request=>{if(/^https?:/.test(request.url()))network.push('HTTP request');});
 await page.goto(pathToFileURL(process.env.PANEL_OFFLINE_HTML).href);
 await expect(page.locator('#memory-query')).toHaveCount(0);
 await expect(page.locator('.sidebar nav a[href="#memory-query"]')).toHaveCount(0);
 expect(await page.locator('script').evaluateAll(nodes=>nodes.some(node=>node.textContent.includes('api/memory')))).toBe(false);
 expect(network).toEqual([]);
});
