import {test} from 'node:test'
import assert from 'node:assert/strict'
import {mkdir,writeFile} from 'node:fs/promises'
import {pathToFileURL} from 'node:url'
import {resolve} from 'node:path'

test('shared console: session, chat, task notes, permissions and workspace isolation',
 {skip:!process.env.CONSOLE_TEST_URL || !process.env.CONSOLE_BROWSER_MODULE,timeout:120000},async()=>{
  const {default:puppeteer}=await import(pathToFileURL(resolve(process.env.CONSOLE_BROWSER_MODULE)))
  const browser=await puppeteer.launch({executablePath:process.env.CONSOLE_BROWSER_EXECUTABLE,headless:true})
  const page=await browser.newPage()
  try {
    await page.setViewport({width:1540,height:1050,deviceScaleFactor:1})
    const errors=[]
    page.on('pageerror',error=>errors.push(error.message))
    await page.goto(process.env.CONSOLE_TEST_URL,{waitUntil:'networkidle0'})
    await page.waitForFunction(()=>document.querySelector('#workspace-select')?.options.length===2,{timeout:7000})
    assert.equal(await page.$eval('#breadcrumb-project',e=>e.textContent),'Portal · datos de prueba')
    await page.click('#new-session-button')
    await page.waitForSelector('#session-dialog[open]',{timeout:7000})
    await page.type('#session-name','Portal piloto')
    await page.click('#session-create-submit')
    await page.waitForFunction(()=>document.querySelector('#chat-state')?.textContent.includes('Disponible'))
    const input='Hola <img src=x onerror="window.__consoleXss=1">'
    await page.type('#chat-input',input)
    await page.click('#send-button')
    await page.waitForFunction(()=>document.querySelector('#chat-messages')?.textContent.includes('Respuesta de prueba:'))
    assert.equal(await page.evaluate(()=>window.__consoleXss),undefined)
    assert.equal(await page.$$eval('#chat-messages img',e=>e.length),0)
    await page.type('#chat-input','ask-permission')
    await page.click('#send-button')
    await page.waitForSelector('.request-card')
    const allow=await page.$('.request-card button[data-decision="allow"]')
    assert.ok(allow)
    await allow.click()
    await page.waitForFunction(()=>document.querySelector('#chat-messages')?.textContent.includes('Decisión de prueba recibida.'))
    await page.click('[data-view="plans"]')
    await page.waitForSelector('#plans-content .plan-title-button',{visible:true})
    await page.click('#plans-content .plan-title-button')
    await page.waitForSelector('.kanban .task-card')
    const cards=await page.$$('.kanban .task-card')
    assert.equal(cards.length,4)
    const task=await page.$('.task-card[data-task="T-02"]')
    assert.ok(task);await task.click()
    await page.waitForSelector('#task-dialog[open]')
    await page.type('#comment-input','Nota privada del portal')
    await page.waitForFunction(()=>document.querySelector('#comment-submit')?.disabled===false&&document.querySelector('#task-title')?.textContent==='Aprobar o rechazar con motivo')
    await page.click('#comment-submit')
    await page.waitForFunction(()=>document.querySelector('#task-comments')?.textContent.includes('Nota privada del portal'))
    await page.keyboard.press('Escape')
    const out=process.env.CONSOLE_SCREENSHOTS
    if(out){await mkdir(out,{recursive:true});await page.screenshot({path:resolve(out,'plans-dark.png'),fullPage:true})}
    await page.select('#workspace-select','billing')
    await page.waitForFunction(()=>document.querySelector('#breadcrumb-project')?.textContent==='Facturación · datos de prueba')
    assert.ok(!(await page.$eval('#main',e=>e.textContent)).includes('Nota privada del portal'))
    await page.click('[data-view="sessions"]')
    assert.ok(!(await page.$eval('#chat-messages',e=>e.textContent)).includes('Respuesta de prueba:'))
    await page.select('#workspace-select','portal')
    await page.waitForFunction(()=>document.querySelector('#breadcrumb-project')?.textContent==='Portal · datos de prueba')
    await page.click('[data-view="sessions"]')
    await page.waitForSelector('.session-row')
    await page.click('.session-row')
    await page.waitForFunction(()=>document.querySelector('#chat-title')?.textContent==='Portal piloto')
    if(out)await page.screenshot({path:resolve(out,'session-dark.png'),fullPage:true})
    await page.click('#theme-button')
    assert.equal(await page.$eval('html',e=>e.dataset.theme),'light')
    await new Promise(resolve=>setTimeout(resolve,250))
    if(out)await page.screenshot({path:resolve(out,'session-light.png'),fullPage:true})
    await page.keyboard.down('Control');await page.keyboard.press('k');await page.keyboard.up('Control')
    await page.waitForSelector('#palette-dialog[open]')
    await page.keyboard.press('Escape')
    assert.equal(await page.$eval('#palette-dialog',e=>e.open),false)
    await page.setViewport({width:375,height:844,deviceScaleFactor:1})
    await page.click('#mobile-menu')
    await page.waitForSelector('.mobile-navigation[open]')
    await page.keyboard.press('Escape')
    const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)
    assert.equal(overflow,false)
    if(out)await page.screenshot({path:resolve(out,'session-mobile.png'),fullPage:true})
    assert.deepEqual(errors,[])
  } catch(error) {
    const diagnostic=await page.evaluate(()=>({toast:document.querySelector('#toast')?.textContent,auth:document.querySelector('#auth-message')?.textContent,title:document.title,dialogs:[...document.querySelectorAll('dialog')].map(d=>({id:d.id,open:d.open})),text:document.querySelector('#main')?.textContent.slice(-1200)})).catch(()=>({}))
    if(process.env.CONSOLE_SCREENSHOTS){await mkdir(process.env.CONSOLE_SCREENSHOTS,{recursive:true});await page.screenshot({path:resolve(process.env.CONSOLE_SCREENSHOTS,'failure.png'),fullPage:true});await writeFile(resolve(process.env.CONSOLE_SCREENSHOTS,'failure.json'),JSON.stringify(diagnostic,null,2))}
    console.log(JSON.stringify(diagnostic));throw error
  } finally {await browser.close()}
 })

test('shared console: local knowledge and project extensions are usable without external services',
 {skip:!process.env.CONSOLE_TEST_URL || !process.env.CONSOLE_BROWSER_MODULE,timeout:60000},async()=>{
  const {default:puppeteer}=await import(pathToFileURL(resolve(process.env.CONSOLE_BROWSER_MODULE)))
  const browser=await puppeteer.launch({executablePath:process.env.CONSOLE_BROWSER_EXECUTABLE,headless:true})
  const page=await browser.newPage()
  try{
    await page.goto(process.env.CONSOLE_TEST_URL,{waitUntil:'networkidle0'})
    await page.waitForFunction(()=>document.querySelector('#workspace-select')?.options.length===2)
    await page.click('[data-view="memory"]')
    await page.waitForFunction(()=>document.querySelector('#memory-content')?.textContent.includes('Motivo obligatorio del portal'),{timeout:12000})
    await page.click('.knowledge-item button')
    await page.waitForFunction(()=>document.querySelector('#memory-content')?.textContent.includes('El rechazo conserva un motivo verificable.'))
    await page.click('[data-view="integrations"]')
    await page.waitForFunction(()=>document.querySelector('#integrations-content')?.textContent.includes('portal-wiki'))
    assert.equal(await page.$eval('#view-banner',node=>!node.hidden&&node.textContent.includes('configuración')),false)
    await page.click('[data-view="catalog"]')
    await page.waitForFunction(()=>document.querySelector('#catalog-content')?.textContent.includes('portal-policy'),{timeout:12000})
    assert.equal(await page.$eval('#catalog-content',node=>node.textContent.includes('Private fixture instructions.')),false)
    await page.select('#workspace-select','billing')
    await page.waitForFunction(()=>document.querySelector('#breadcrumb-project')?.textContent==='Facturación · datos de prueba')
    await page.waitForFunction(()=>!document.querySelector('#catalog-content .loading'))
    assert.equal(await page.$eval('#catalog-content',node=>node.textContent.includes('portal-policy')),false)
    await page.click('[data-view="memory"]')
    await page.waitForFunction(()=>!document.querySelector('#memory-content .loading'))
    assert.equal(await page.$eval('#memory-content',node=>node.textContent.includes('Motivo obligatorio del portal')),false)
  }finally{await browser.close()}
 })

test('shared console: deep links, delayed responses and project selection remain scoped',
 {skip:!process.env.CONSOLE_TEST_URL || !process.env.CONSOLE_BROWSER_MODULE,timeout:60000},async()=>{
  const {default:puppeteer}=await import(pathToFileURL(resolve(process.env.CONSOLE_BROWSER_MODULE)))
  const browser=await puppeteer.launch({executablePath:process.env.CONSOLE_BROWSER_EXECUTABLE,headless:true})
  const page=await browser.newPage()
  try{
    await page.setViewport({width:1540,height:1050})
    await page.goto(process.env.CONSOLE_TEST_URL,{waitUntil:'networkidle0'})
    await page.waitForFunction(()=>document.querySelector('#workspace-select')?.options.length===2)
    assert.equal(await page.$eval('.mobile-navigation-close',node=>node.hidden),true)
    await page.click('[data-view="plans"]')
    await page.waitForSelector('#plans-content .plan-title-button',{visible:true})
    await page.click('#plans-content .plan-title-button')
    await page.waitForSelector('.kanban .task-card')
    const deepLink=page.url()
    await page.reload({waitUntil:'networkidle0'})
    await page.waitForSelector('.kanban .task-card',{visible:true,timeout:7000})
    assert.equal(page.url(),deepLink)
    await page.evaluate(()=>{
      const original=window.fetch.bind(window)
      window.fetch=async(input,options)=>{
        if(String(input).endsWith('/portal/plans')){
          const response=await original(input,{...options,signal:undefined})
          const data=await response.json()
          for(const row of data.iniciativas||[])row.titulo='PRIVATE LATE PORTAL RESPONSE'
          window.__latePortalStarted=true
          await new Promise(resolve=>setTimeout(resolve,1200))
          window.__latePortalReturned=true
          return new Response(JSON.stringify(data),{status:200})
        }
        return original(input,options)
      }
    })
    await page.click('[data-view="plans"]')
    await page.waitForFunction(()=>window.__latePortalStarted===true)
    await page.select('#workspace-select','billing')
    await page.waitForFunction(()=>document.querySelector('#breadcrumb-project')?.textContent==='Facturación · datos de prueba')
    await page.waitForFunction(()=>window.__latePortalReturned===true)
    assert.equal(await page.$eval('#main',node=>node.textContent.includes('PRIVATE LATE PORTAL RESPONSE')),false)
    assert.ok(page.url().includes('workspace=billing'))
    await page.select('#workspace-select','portal')
    await page.waitForFunction(()=>document.querySelector('#workspace-select')?.value==='portal')
    await page.click('#new-plan-button')
    await page.type('#idea-name','PRIVATE PORTAL IDEA')
    await page.keyboard.press('Escape')
    await page.select('#workspace-select','billing')
    await page.waitForFunction(()=>document.querySelector('#breadcrumb-project')?.textContent==='Facturación · datos de prueba')
    await page.click('#new-plan-button')
    assert.equal(await page.$eval('#idea-name',node=>node.value),'')
    await page.keyboard.press('Escape')
    await page.select('#workspace-select','portal')
    await page.waitForFunction(()=>document.querySelector('#breadcrumb-project')?.textContent==='Portal · datos de prueba')
    await page.click('#new-plan-button')
    assert.equal(await page.$eval('#idea-name',node=>node.value),'PRIVATE PORTAL IDEA')
  }finally{await browser.close()}
 })

test('shared console: delayed saved notes cannot replace another task comments',
 {skip:!process.env.CONSOLE_TEST_URL || !process.env.CONSOLE_BROWSER_MODULE,timeout:60000},async()=>{
  const {default:puppeteer}=await import(pathToFileURL(resolve(process.env.CONSOLE_BROWSER_MODULE)))
  const browser=await puppeteer.launch({executablePath:process.env.CONSOLE_BROWSER_EXECUTABLE,headless:true})
  const page=await browser.newPage()
  try{
    await page.goto(process.env.CONSOLE_TEST_URL,{waitUntil:'networkidle0'})
    await page.waitForFunction(()=>document.querySelector('#workspace-select')?.options.length===2)
    await page.click('[data-view="plans"]')
    await page.waitForSelector('#plans-content .plan-title-button',{visible:true})
    await page.click('#plans-content .plan-title-button')
    await page.waitForSelector('.task-card[data-task="T-02"]');await page.click('.task-card[data-task="T-02"]')
    await page.waitForFunction(()=>document.querySelector('#task-title')?.textContent==='Aprobar o rechazar con motivo')
    await page.evaluate(()=>{
      const original=window.fetch.bind(window);let written=false
      window.fetch=async(input,options)=>{
        const response=await original(input,options)
        if(String(input).endsWith('/tasks/T-02/comments')){
          if(options?.method==='POST')written=true
          else if(written){window.__notesRefreshStarted=true;await new Promise(resolve=>setTimeout(resolve,2200));window.__notesRefreshReturned=true}
        }
        return response
      }
    })
    await page.type('#comment-input','NOTE ONLY FOR T-02')
    await page.click('#comment-submit')
    await page.waitForFunction(()=>window.__notesRefreshStarted)
    await page.keyboard.press('Escape');await page.click('.task-card[data-task="T-03"]')
    await page.waitForFunction(()=>document.querySelector('#task-title')?.textContent==='Revisar la experiencia del equipo')
    await page.waitForFunction(()=>window.__notesRefreshReturned)
    assert.equal(await page.$eval('#task-comments',node=>node.textContent.includes('NOTE ONLY FOR T-02')),false)
  }finally{await browser.close()}
 })

test('shared console: a permission response lost before consumption can be recovered',
 {skip:!process.env.CONSOLE_TEST_URL || !process.env.CONSOLE_BROWSER_MODULE,timeout:60000},async()=>{
  const {default:puppeteer}=await import(pathToFileURL(resolve(process.env.CONSOLE_BROWSER_MODULE)))
  const browser=await puppeteer.launch({executablePath:process.env.CONSOLE_BROWSER_EXECUTABLE,headless:true})
  const page=await browser.newPage()
  try{
    await page.goto(process.env.CONSOLE_TEST_URL,{waitUntil:'networkidle0'})
    await page.waitForFunction(()=>document.querySelector('#workspace-select')?.options.length===2)
    await page.click('#new-session-button');await page.waitForSelector('#session-dialog[open]')
    await page.type('#session-name','Recover permission');await page.click('#session-create-submit')
    await page.waitForFunction(()=>document.querySelector('#chat-state')?.textContent.includes('Disponible'))
    await page.type('#chat-input','ask-permission');await page.click('#send-button')
    await page.waitForSelector('.request-card button[data-decision="allow"]')
    await page.evaluate(()=>{
      const original=window.fetch.bind(window)
      window.fetch=async(input,options)=>{
        if(String(input).endsWith('/answer')&&!window.__permissionLost){window.__permissionLost=true;return new Response(JSON.stringify({error:'service_unavailable'}),{status:503})}
        return original(input,options)
      }
    })
    await page.click('.request-card button[data-decision="allow"]')
    await page.waitForFunction(()=>window.__permissionLost)
    await page.click('#refresh-button')
    await page.waitForFunction(()=>[...document.querySelectorAll('.request-card button')].some(node=>!node.disabled),{timeout:8000})
    await page.click('.request-card button[data-decision="allow"]')
    await page.waitForFunction(()=>document.querySelector('#chat-messages')?.textContent.includes('Decisión de prueba recibida.'))
  }finally{await browser.close()}
 })

test('shared console: optional source failures and preserved stale figures are visible',
 {skip:!process.env.CONSOLE_TEST_URL || !process.env.CONSOLE_BROWSER_MODULE,timeout:60000},async()=>{
  const {default:puppeteer}=await import(pathToFileURL(resolve(process.env.CONSOLE_BROWSER_MODULE)))
  const browser=await puppeteer.launch({executablePath:process.env.CONSOLE_BROWSER_EXECUTABLE,headless:true})
  const page=await browser.newPage()
  try{
    await page.goto(process.env.CONSOLE_TEST_URL,{waitUntil:'networkidle0'})
    await page.waitForFunction(()=>document.querySelector('#overview-content .metric-value')?.textContent==='2')
    await page.evaluate(()=>{
      const original=window.fetch.bind(window)
      window.fetch=async(input,options)=>{
        const response=await original(input,options),path=String(input)
        if(!response.ok)return response
        if(path.endsWith('/portal/plans')){
          const value=await response.json();value.status='partial';value.complete=false;value.freshness={state:'refresh_failed',age_seconds:30}
          return new Response(JSON.stringify(value),{status:200})
        }
        if(path.endsWith('/portal/integrations')){
          const value=await response.json();value.integrations={status:'invalid',bindings:[],diagnostics:['invalid_configuration']};value.memory_services=[{status:'invalid_configuration'}]
          return new Response(JSON.stringify(value),{status:200})
        }
        if(path.endsWith('/portal/activity')){
          const value=await response.json();value.status='unavailable';value.reason='invalid_history';return new Response(JSON.stringify(value),{status:200})
        }
        return response
      }
    })
    await page.click('#refresh-button')
    await page.waitForFunction(()=>document.querySelector('#view-banner')?.hidden===false&&document.querySelector('#view-banner')?.textContent.includes('anterior'),{timeout:7000})
    assert.ok((await page.$eval('#overview-content .metric-value',node=>node.textContent)).includes('≥'))
    await page.click('[data-view="integrations"]')
    await page.waitForFunction(()=>document.querySelector('#view-banner')?.hidden===false&&document.querySelector('#view-banner')?.textContent.includes('configuración'),{timeout:7000})
    await page.click('[data-view="activity"]')
    await page.waitForFunction(()=>document.querySelector('#view-banner')?.hidden===false&&document.querySelector('#view-banner')?.textContent.includes('historial'),{timeout:7000})
    await page.click('[data-view="integrations"]')
    await page.waitForFunction(()=>document.querySelector('#view-banner')?.hidden===false&&document.querySelector('#view-banner')?.textContent.includes('configuración'),{timeout:7000})
    await page.click('[data-view="overview"]')
    await page.waitForFunction(()=>document.querySelector('#view-banner')?.hidden===false&&document.querySelector('#view-banner')?.textContent.includes('anterior'),{timeout:7000})
    await page.click('[data-view="activity"]')
    await page.waitForFunction(()=>document.querySelector('#view-banner')?.hidden===false&&document.querySelector('#view-banner')?.textContent.includes('historial'),{timeout:7000})
  }finally{await browser.close()}
 })

test('shared console: invalid optional configuration and activity are distinguished from empty data',
 {skip:!process.env.CONSOLE_TEST_URL || !process.env.CONSOLE_BROWSER_MODULE,timeout:60000},async()=>{
  const {default:puppeteer}=await import(pathToFileURL(resolve(process.env.CONSOLE_BROWSER_MODULE)))
  const browser=await puppeteer.launch({executablePath:process.env.CONSOLE_BROWSER_EXECUTABLE,headless:true})
  const page=await browser.newPage()
  try{
    await page.goto(process.env.CONSOLE_TEST_URL,{waitUntil:'networkidle0'})
    await page.waitForFunction(()=>document.querySelector('#workspace-select')?.options.length===2)
    await page.evaluate(()=>{
      const original=window.fetch.bind(window)
      window.fetch=async(input,options)=>{
        const response=await original(input,options),path=String(input)
        if(path.endsWith('/portal/integrations')){
          const value=await response.json();value.integrations={status:'invalid',bindings:[]};value.memory_services=[{status:'invalid_configuration'}]
          return new Response(JSON.stringify(value),{status:200})
        }
        if(path.endsWith('/portal/activity')){
          const value=await response.json();value.status='unavailable';value.reason='invalid_history';return new Response(JSON.stringify(value),{status:200})
        }
        return response
      }
    })
    await page.click('[data-view="integrations"]')
    await page.waitForFunction(()=>document.querySelector('#view-banner')?.hidden===false&&document.querySelector('#view-banner')?.textContent.includes('configuración'),{timeout:7000})
    await page.click('[data-view="activity"]')
    await page.waitForFunction(()=>document.querySelector('#view-banner')?.hidden===false&&document.querySelector('#view-banner')?.textContent.includes('historial'),{timeout:7000})
  }finally{await browser.close()}
 })

