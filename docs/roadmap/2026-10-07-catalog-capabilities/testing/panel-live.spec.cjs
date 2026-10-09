const {test,expect}=require('@playwright/test');
const fs=require('node:fs');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const url=process.env.PANEL_LIVE_URL;
const origin=new URL(url).origin;
const ledger=process.env.PANEL_LEDGER;
const initial=fs.readFileSync(process.env.PANEL_LEDGER_INITIAL,'utf8');
const updated=fs.readFileSync(process.env.PANEL_LEDGER_UPDATED,'utf8');
let external=[];

test.beforeAll(async({browser})=>{
 fs.writeFileSync(process.env.PANEL_BROWSER_METADATA,JSON.stringify({browser_version:browser.version()}),'utf8');
});

test.beforeEach(async({page,context})=>{
 external=[];
 fs.writeFileSync(ledger,initial,'utf8');
 await context.route('**/*',async route=>{
  const request=route.request();
  if(/^https?:/.test(request.url())&&new URL(request.url()).origin!==origin){external.push('forbidden origin');await route.abort();return;}
  await route.continue();
 });
 await context.addCookies([{name:'owned_fixture_cookie',value:'fixture_value',url:origin}]);
 await page.goto(url);
 await expect(page.locator('#progress-cards .progress-card')).toHaveCount(2,{timeout:12000});
 await expect(page.locator('#progress-cards')).toContainText('1 de 2 tareas completadas',{timeout:12000});
});
test.afterEach(()=>{expect(external).toEqual([]);});

test('E-01 real served scripts respect nonce CSP and progress navigation',async({page})=>{
 const errors=[];const apiCookies=[];
 page.on('pageerror',error=>errors.push(error.message));
 page.on('console',message=>{if(message.type()==='error')errors.push(message.text());});
 page.on('request',request=>{if(request.url().endsWith('/api/progress'))apiCookies.push(request.headers().cookie||'');});
 const response=await page.reload();
 const csp=response.headers()['content-security-policy'];
 expect(csp).toContain("connect-src 'self'");expect(csp).toMatch(/script-src 'nonce-/);
 await expect(page.locator('#progress-cards .progress-card')).toHaveCount(2);
 expect(await page.locator('script').evaluateAll(nodes=>nodes.every(node=>Boolean(node.nonce)))).toBe(true);
 await page.locator('.sidebar nav a[href="#operations"]').click();
 await expect(page.locator('#operations')).toBeFocused();
 await expect(page.locator('.sidebar nav a[href="#operations"]')).toHaveAttribute('aria-current','location');
 await expect(page.locator('#operations')).toContainText('no demuestran agentes vivos');
 await page.locator('#progress-state').selectOption('en-progreso');
 await expect(page.locator('#progress-cards .progress-card:visible')).toHaveCount(1);
 await page.locator('#progress-search').fill('unmatched-fixture');
 await expect(page.locator('#progress-cards .progress-card:visible')).toHaveCount(0);
 await page.locator('#progress-search').fill('');await page.locator('#progress-state').selectOption('all');
 await expect(page.locator('#progress-cards .progress-card:visible')).toHaveCount(2);
 const manual=page.waitForRequest(request=>request.url().endsWith('/api/progress'));
 await page.locator('#progress-refresh').click();await manual;
 await expect(page.locator('#progress-refresh')).toBeEnabled();
 expect(apiCookies.length).toBeGreaterThan(0);expect(apiCookies.every(value=>value==='')).toBe(true);
 expect(errors).toEqual([]);
 await page.screenshot({path:path.join(process.env.PANEL_SCREENSHOTS,'desktop.png'),fullPage:true});
});

test('E-02 changing owned ledger refreshes hash and counts through polling',async({page})=>{
 const before=await page.locator('#progress-cards').textContent();
 const main=page.locator('.progress-card').filter({has:page.getByRole('heading',{name:'live-fixture',exact:true})});
 const hash=await main.locator('code').textContent();
 const date=await page.locator('#progress-freshness').textContent();
 fs.writeFileSync(ledger,updated,'utf8');
 await expect(page.locator('#progress-cards')).toContainText('2 de 2 tareas completadas',{timeout:10000});
 expect(await page.locator('#progress-cards').textContent()).not.toBe(before);
 expect(await main.locator('code').textContent()).not.toBe(hash);
 expect(await page.locator('#progress-freshness').textContent()).not.toBe(date);
 await expect(page.locator('#progress-cards')).not.toContainText('T-02 · Construir beta');
});

test('E-03 HTTP failure and incompatible reply retain prior view and date',async({page})=>{
 const content=await page.locator('#progress-cards').textContent();
 const date=await page.locator('#progress-freshness').textContent();
 for(const mode of ['http','schema']){
  await page.route('**/api/progress',route=>route.fulfill({status:mode==='http'?503:200,contentType:'application/json',body:JSON.stringify({version:99})}));
  const response=page.waitForResponse(value=>value.url().endsWith('/api/progress'));
  await page.locator('#progress-refresh').click();
  await response;await expect(page.locator('#progress-refresh')).toBeEnabled();
  await expect(page.locator('#progress-status')).toContainText('Se conserva la última vista');
  expect(await page.locator('#progress-cards').textContent()).toBe(content);
  expect(await page.locator('#progress-freshness').textContent()).toBe(date);
  await page.unroute('**/api/progress');
 }
});

test('E-04 keyboard and mobile layout preserve usable progress controls',async({page})=>{
 await page.setViewportSize({width:390,height:844});
 await page.locator('.sidebar nav a[href="#operations"]').click();
 await expect(page.locator('.sidebar nav a[href="#operations"]')).toBeVisible();
 await page.locator('#progress-search').focus();await page.keyboard.press('Tab');
 await expect(page.locator('#progress-state')).toBeFocused();await page.keyboard.press('Tab');
 await expect(page.locator('#progress-refresh')).toBeFocused();
 const request=page.waitForRequest(value=>value.url().endsWith('/api/progress'));
 await page.keyboard.press('Enter');await request;await expect(page.locator('#progress-refresh')).toBeEnabled();
 expect(await page.evaluate(()=>Math.max(document.documentElement.scrollWidth,document.body.scrollWidth)<=innerWidth+1)).toBe(true);
 await page.screenshot({path:path.join(process.env.PANEL_SCREENSHOTS,'mobile.png'),fullPage:true});
});

test('E-05 offline output retains no live progress or HTTP fetch',async({page})=>{
 const network=[];page.on('request',request=>{if(/^https?:/.test(request.url()))network.push('http request');});
 await page.goto(pathToFileURL(process.env.PANEL_OFFLINE_HTML).href);
 await expect(page.locator('#operations')).toHaveCount(0);
 await expect(page.locator('.sidebar nav a[href="#operations"]')).toHaveCount(0);
 await expect(page.locator('.snapshot')).toContainText('Instantánea local');
 expect(network).toEqual([]);
});

test('E-06 malformed owned ledger shows partial replacement explicitly',async({page})=>{
 const before=await page.locator('#progress-freshness').textContent();
 fs.writeFileSync(ledger,'# Malformed owned ledger\nNo canonical task entries.\n','utf8');
 await expect(page.locator('#progress-status')).toContainText('Lectura parcial',{timeout:10000});
 await expect(page.locator('#progress-cards .progress-card')).toHaveCount(1);
 expect(await page.locator('#progress-freshness').textContent()).not.toBe(before);
 await expect(page.locator('#progress-results')).toContainText('lectura incompleta');
});
