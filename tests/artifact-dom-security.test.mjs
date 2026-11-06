import {test} from 'node:test'
import assert from 'node:assert/strict'
import {mkdtempSync,readFileSync,writeFileSync,existsSync,rmSync} from 'node:fs'
import {tmpdir} from 'node:os'
import {resolve,join,dirname} from 'node:path'
import {pathToFileURL,fileURLToPath} from 'node:url'
import {spawnSync} from 'node:child_process'

const root=resolve(dirname(fileURLToPath(import.meta.url)),'..')
const browser=[
 process.env.CUSTOM_AGENTS_TEST_BROWSER,
 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
 'C:/Program Files/Google/Chrome/Application/chrome.exe',
 '/usr/bin/google-chrome','/usr/bin/google-chrome-stable','/usr/bin/chromium','/usr/bin/chromium-browser',
].find(path=>path && existsSync(path))
const payload='<img src="data:," onerror="document.body.dataset.attack=\'yes\'"> & "á"'
const definitions=[
 {id:'jira-picker',path:'skills/jira-sync/assets/jira-picker.template.html',
  action:'const row=issueRow(window.fixtureIssue);document.body.appendChild(row);window.literalText=row.querySelector(".s").textContent===window.fixturePayload;row.querySelector("button").click();',
  expected:'parentSummary'},
 {id:'jira-live',path:'skills/roadmap-dashboard/assets/jira-live.template.html',
  action:'setTimeout(()=>{window.literalText=document.querySelector("#body").textContent.includes(window.fixturePayload)},60);'},
 {id:'confluence-tree',path:'skills/confluence-publish/assets/tree-browser.template.html',
  action:'setTimeout(()=>{document.querySelector("#tree button.sel").click();window.literalText=document.querySelector(".ask .q").textContent.includes(window.fixturePayload);setTimeout(()=>{document.querySelector("#o1").checked=true;document.querySelector("#ok").click()},30)},40);',
  expected:'parentPath'},
]

for(const entry of [...definitions])definitions.push({...entry,mode:'error',
 action:entry.id==='jira-picker'
  ? 'document.getElementById("pq").value="demo";smart();setTimeout(()=>{window.literalText=document.querySelector("#plist").textContent.includes(window.fixturePayload)},70);'
  : 'setTimeout(()=>{window.literalText=document.querySelector("'+(entry.id==='jira-live'?'#body':'#tree')+'").textContent.includes(window.fixturePayload)},70);',
 expected:undefined})
definitions.push({...definitions[2],mode:'config',
 action:'setTimeout(()=>{document.querySelector("#tree button.sel").click();window.literalText=document.querySelector("#space-heading").textContent.includes(window.fixturePayload)&&document.querySelector("#cname").value===window.fixturePayload;},60);',
 expected:undefined})
definitions.push({...definitions[0],mode:'project',
 action:'document.getElementById("pq").value="demo";smart();setTimeout(()=>{window.literalText=document.querySelector("#plist .s").textContent===window.fixturePayload;document.querySelector("#plist button").click();chooseNoParent()},70);',
 expected:'projectName'})
definitions.push({...definitions[0],mode:'epic',
 action:'pickProject("DEMO",window.fixturePayload);document.querySelector("#epicname").value=window.fixturePayload;chooseNewEpic();window.literalText=document.querySelector("#bhint").textContent.includes(window.fixturePayload);',
 expected:'createEpicName'})

for(const view of definitions)test('F001 '+view.id+' '+(view.mode||'metadata')+': remote metadata stays literal and cannot run handlers',{skip:!browser},()=>{
 const temp=mkdtempSync(join(tmpdir(),'ca-artifact-dom-'))
 try {
  let html=readFileSync(join(root,view.path),'utf8')
  const config={SERVER_PROJECTS:'projects',SERVER_SEARCH:'search',SERVER:'descendants',CLOUD_ID:'cloud',HOME_ID:'home',SPACE_KEY:'DEMO',SPACE_NAME:'Demo',SPACE_INITIALS:'D',DEFAULT_NAME:'Demo',LABEL:'demo',TITULO:'Demo'}
  if(view.mode==='config'){config.SPACE_NAME=payload;config.DEFAULT_NAME=payload}
  const fields={'jira-picker':['SERVER_PROJECTS','SERVER_SEARCH','CLOUD_ID'],'jira-live':['SERVER_SEARCH','CLOUD_ID','LABEL','TITULO'],'confluence-tree':['SERVER','CLOUD_ID','HOME_ID','SPACE_KEY','SPACE_NAME','SPACE_INITIALS','DEFAULT_NAME']}[view.id]
  const selected=Object.fromEntries(fields.map(key=>[key,config[key]]))
  const renderer=join(root,'agent-kits/shared/render-artifact.py')
  if(existsSync(renderer)) {
   const result=spawnSync(process.env.TEST_PYTHON || 'python',[renderer,'--template',view.id,'--config','-'],{cwd:root,input:JSON.stringify(selected),encoding:'utf8',env:{...process.env,PYTHONDONTWRITEBYTECODE:'1',PYTHONIOENCODING:'utf-8'}})
   assert.equal(result.status,0,result.stderr);html=result.stdout
  } else {
   // Baseline is the previous documented literal-substitution workflow.
   for(const [key,value] of Object.entries(config))html=html.split('{{'+key+'}}').join(value)
  }
  const issue={key:'DEMO-1',fields:{summary:payload,project:{key:'DEMO',name:payload},issuetype:{name:payload,hierarchyLevel:1},status:{name:payload,statusCategory:{key:'done'}}}}
  const bootstrap='window.fixturePayload='+JSON.stringify(payload)+';window.fixtureIssue='+JSON.stringify(issue)+';window.fixtureError='+JSON.stringify(view.mode==='error')+';window.cowork={callMcpTool:async()=>{if(window.fixtureError)throw new Error(window.fixturePayload);return {structuredContent:{issues:[window.fixtureIssue],results:[{id:"100",title:window.fixturePayload}],values:[{key:"DEMO",name:window.fixturePayload}]}}}};'
  html=html.replace('<script>','<script>'+bootstrap+'</script><script>')
  const resultScript='<script>'+view.action+';setTimeout(()=>{const p=document.createElement("pre");p.id="fixture-result";p.textContent=JSON.stringify({injected:document.body.dataset.attack==="yes",literal:window.literalText,dest:window.__dest});document.body.appendChild(p)},240);</script>'
  html=html.replace('</body>',resultScript+'</body>')
  const path=join(temp,'fixture.html');writeFileSync(path,html)
  const run=spawnSync(browser,['--headless=new','--disable-gpu','--disable-extensions','--disable-background-networking','--disable-component-update','--disable-sync','--no-first-run','--no-proxy-server','--host-resolver-rules=MAP * ~NOTFOUND','--user-data-dir='+join(temp,'profile'),'--dump-dom','--virtual-time-budget=1500',pathToFileURL(path).href],{encoding:'utf8',timeout:30000,windowsHide:true})
  assert.equal(run.status,0,run.stderr)
  const match=run.stdout.match(/<pre id="fixture-result">([\s\S]*?)<\/pre>/)
  assert.ok(match,'browser must finish the fixture')
  const result=JSON.parse(match[1].replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&'))
  assert.equal(result.injected,false,'remote metadata executed an HTML handler')
  assert.equal(result.literal,true,'remote markup must remain literal text')
  if(view.expected==='parentSummary')assert.equal(result.dest.parentSummary,payload)
  if(view.expected==='parentPath')assert.equal(result.dest.parentPath[0],payload)
  if(view.expected==='projectName')assert.equal(result.dest.projectName,payload)
  if(view.expected==='createEpicName')assert.equal(result.dest.createEpicName,payload)
 } finally {
  assert.equal(dirname(resolve(temp)),resolve(tmpdir()))
  rmSync(temp,{recursive:true,force:true})
 }
})
