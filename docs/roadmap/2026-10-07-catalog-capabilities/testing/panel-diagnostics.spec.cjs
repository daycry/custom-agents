const {test,expect}=require('@playwright/test');
const {pathToFileURL}=require('node:url');
const fs=require('node:fs');
const data=JSON.parse(fs.readFileSync(process.env.PANEL_JSON,'utf8'));
const url=pathToFileURL(process.env.PANEL_HTML).href;
test.beforeEach(async({page})=>{await page.goto(url);});

test('D-01 imported diagnostics keeps historical scope and hook status separate',async({page})=>{
 await page.locator('.sidebar nav a[href="#diagnostics"]').click();
 await expect(page.locator('#diagnostics')).toBeFocused();
 await expect(page.locator('.sidebar nav a[href="#diagnostics"]')).toHaveAttribute('aria-current','location');
 await expect(page.locator('#diagnostics')).toContainText(data.diagnostics.report.checked_at);
 await expect(page.locator('#diagnostics')).toContainText('no acredita carga ni ejecución');
 await expect(page.locator('.diagnostic-row')).toHaveCount(data.diagnostics.report.blocks.reduce((n,b)=>n+b.rows.length,0));
 await expect(page.locator('.diagnostic-source')).toContainText(data.diagnostics.source_sha256);
 await page.locator('#kind').selectOption('hooks');
 for(const card of await page.locator('#catalog .card:visible').all())await expect(card).toContainText('Carga sin verificar');
});

test('D-02 severity and search filter diagnoses independently of catalog',async({page})=>{
 await page.locator('#kind').selectOption('agents');
 const before=await page.locator('#catalog .card:visible').count();
 await page.locator('#diagnostic-state').selectOption('error');
 await expect(page.locator('#diagnostic-results')).toHaveText(data.diagnostics.report.summary.error+' comprobaciones coincidentes');
 await page.locator('.diagnostic-block').first().locator('summary').click();
 for(const row of await page.locator('.diagnostic-row:visible').all())await expect(row).toHaveAttribute('data-state','error');
 await page.locator('#diagnostic-search').fill('not-present-in-this-report');
 await expect(page.locator('#diagnostic-results')).toHaveText('0 comprobaciones coincidentes');
 await expect(page.locator('.diagnostic-block:visible')).toHaveCount(0);
 await expect(page.locator('#catalog .card:visible')).toHaveCount(before);
});

test('D-03 priority link restores hidden check, focus and history',async({page})=>{
 const action=data.diagnostics.report.priorities[0];
 const id='diagnostic-'+action.block+'-'+action.row;
 await page.locator('#diagnostic-state').selectOption('info');
 await page.locator('#diagnostic-search').fill('not-present');
 await page.locator('.diagnostic-priorities a[href="#'+id+'"]').click();
 await expect(page.locator('#diagnostic-state')).toHaveValue('all');
 await expect(page.locator('#diagnostic-search')).toHaveValue('');
 await expect(page.locator('#'+id)).toBeFocused();
 await expect(page.locator('#'+id)).toBeVisible();
 await page.locator('.sidebar nav a[href="#workflow"]').click();
 await page.goBack();
 await expect(page.locator('#'+id)).toBeFocused();
});

test('D-04 keyboard can reach diagnostics and use its controls',async({page})=>{
 const nav=page.locator('.sidebar nav a[href="#diagnostics"]');
 await nav.focus();await page.keyboard.press('Enter');
 await expect(page.locator('#diagnostics')).toBeFocused();
 await page.locator('#diagnostic-state').focus();await page.keyboard.press('ArrowDown');
 await page.keyboard.press('Enter');
 await expect(page.locator('#diagnostic-state')).toHaveValue('error');
});

test('D-05 mobile, reduced motion and no external resources',async({page})=>{
 await page.setViewportSize({width:390,height:844});await page.emulateMedia({reducedMotion:'reduce'});
 const errors=[],network=[];
 page.on('pageerror',e=>errors.push(e.message));
 page.on('request',r=>{if(/^https?:/.test(r.url()))network.push(r.url());});
 await page.reload();
 await expect(page.locator('.sidebar nav a[href="#diagnostics"]')).toBeVisible();
 await page.locator('.sidebar nav a[href="#diagnostics"]').click();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 expect(errors).toEqual([]);expect(network).toEqual([]);
 await page.screenshot({path:process.env.PANEL_MOBILE_SCREENSHOT,fullPage:true});
});

test('D-06 generated HTML omits private report fields',async({page})=>{
 const body=await page.locator('body').innerText();
 for(const text of ['PRIVATE_DIAGNOSTIC_TITLE','PRIVATE_DIAGNOSTIC_DETAIL','PRIVATE_DIAGNOSTIC_COMMAND','Secret1234'])expect(body).not.toContain(text);
 await page.locator('#diagnostics').screenshot({path:process.env.PANEL_DIAGNOSTICS_SCREENSHOT});
});

test('D-07 revisiting the same priority fragment restores a filtered-out row',async({page})=>{
 const action=data.diagnostics.report.priorities[0],id='diagnostic-'+action.block+'-'+action.row;
 const link=page.locator('.diagnostic-priorities a[href="#'+id+'"]');
 await link.click();await page.locator('#diagnostic-search').fill('not-present');
 await link.click();
 await expect(page.locator('#diagnostic-search')).toHaveValue('');
 await expect(page.locator('#'+id)).toBeFocused();await expect(page.locator('#'+id)).toBeVisible();
});
