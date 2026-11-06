import {test} from 'node:test'
import assert from 'node:assert/strict'
import {mkdtempSync,mkdirSync,writeFileSync,readFileSync,readdirSync,rmSync,copyFileSync,existsSync} from 'node:fs'
import {tmpdir} from 'node:os'
import {join,resolve,dirname} from 'node:path'
import {fileURLToPath} from 'node:url'
import {spawnSync} from 'node:child_process'

const source=resolve(dirname(fileURLToPath(import.meta.url)),'../skills/to-pdf/scripts')
function fixture(args=[]) {
 const dir=mkdtempSync(join(tmpdir(),'ca-pdf-policy-'))
 for(const file of readdirSync(source).filter(name=>name.endsWith('.mjs')))copyFileSync(join(source,file),join(dir,file))
 writeFileSync(join(dir,'package.json'),'{"type":"module"}')
 for(const name of ['markdown-it','mammoth','puppeteer']) {
  const module=join(dir,'node_modules',name);mkdirSync(module,{recursive:true})
  writeFileSync(join(module,'package.json'),'{"type":"module","exports":"./index.mjs"}')
  writeFileSync(join(module,'index.mjs'),name==='puppeteer'
   ? [
     'import {writeFileSync} from "node:fs";',
     'const log={calls:[],decisions:[]};const handlers={};',
     'const page={',
     'setJavaScriptEnabled:async value=>{log.js=value;log.calls.push("js")},',
     'setOfflineMode:async value=>{log.offline=value;log.calls.push("offline")},',
     'setBypassServiceWorker:async()=>{},setRequestInterception:async value=>{log.interception=value},',
     'on:(event,callback)=>{handlers[event]=callback},',
     'setContent:async doc=>{log.doc=doc;log.calls.push("content");for(const url of JSON.parse(process.env.CA_PDF_URLS)){const req={url:()=>url,isInterceptResolutionHandled:()=>false,continue:async()=>log.decisions.push([url,"continued"]),abort:async()=>log.decisions.push([url,"aborted"])};if(handlers.request)await handlers.request(req);else await req.continue();}},',
     'addStyleTag:async data=>{log.style=data.content},',
     'pdf:async data=>writeFileSync(data.path,"%PDF-fixture"),',
     '};',
     'export default {launch:async options=>{log.launch=options;return {newPage:async()=>page,close:async()=>writeFileSync(process.env.CA_PDF_LOG,JSON.stringify(log))}}};',
    ].join('\n')
   : 'export default '+(name==='markdown-it'?'class {render(text){return text}}':'{convertToHtml:async()=>({value:""})}'))
 }
 writeFileSync(join(dir,'input.html'),'<html><body><h1>Document</h1><script>throw new Error("document JS")</script></body></html>')
 const urls=['data:image/png;base64,AA==','https://assets.example.com/p.png','https://assets.example.com/redirect','https://other.example.com/p.png','file:///private-canary','ws://localhost:1/','https://user:secret@assets.example.com/x']
 const result=spawnSync(process.execPath,[join(dir,'to-pdf.mjs'),join(dir,'input.html'),'--out',join(dir,'result.pdf'),...args],{
  encoding:'utf8',env:{...process.env,CA_PDF_LOG:join(dir,'log.json'),CA_PDF_URLS:JSON.stringify(urls)},timeout:20000,windowsHide:true,
 })
 return {dir,result,log:existsSync(join(dir,'log.json'))?JSON.parse(readFileSync(join(dir,'log.json'),'utf8')):null}
}
function cleanup(dir){assert.equal(dirname(resolve(dir)),resolve(tmpdir()));rmSync(dir,{recursive:true,force:true})}

test('PDF default policy keeps sandbox, disables JS and blocks remote resources',()=>{
 const f=fixture()
 try {
  assert.equal(f.result.status,0,f.result.stderr)
  assert.ok(!f.log.launch.args.includes('--no-sandbox'),'sandbox must be enabled by default')
  assert.equal(f.log.js,false)
  assert.equal(f.log.offline,true)
  assert.equal(f.log.interception,true)
  assert.ok(f.log.calls.indexOf('js')<f.log.calls.indexOf('content'))
  assert.equal(f.log.decisions[0][1],'continued')
  assert.ok(f.log.decisions.slice(1).every(row=>row[1]==='aborted'))
 } finally {cleanup(f.dir)}
})
test('PDF explicit JS and exact origin allowlist preserve network boundaries',()=>{
 const f=fixture(['--allow-js','--allow-origin','https://assets.example.com'])
 try {
  assert.equal(f.result.status,0,f.result.stderr);assert.equal(f.log.js,true);assert.equal(f.log.offline,false)
  assert.deepEqual(f.log.decisions.map(row=>row[1]),['continued','continued','continued','aborted','aborted','aborted','aborted'])
 } finally {cleanup(f.dir)}
})
test('PDF sandbox opt-out must be explicit and visible',()=>{
 const f=fixture(['--unsafe-no-sandbox'])
 try {
  assert.equal(f.result.status,0,f.result.stderr);assert.ok(f.log.launch.args.includes('--no-sandbox'));assert.match(f.result.stderr,/sandbox/i)
 } finally {cleanup(f.dir)}
})
test('PDF title remains text, not document markup',()=>{
 const f=fixture(['--title','</title><img src=x>'])
 try {
  assert.equal(f.result.status,0,f.result.stderr);assert.ok(f.log.doc.includes('&lt;/title&gt;&lt;img src=x&gt;'))
 } finally {cleanup(f.dir)}
})
for(const args of [['--allow-origin','http://assets.example.com'],['--allow-origin'],['--typo-policy']])
test('PDF malformed policy rejects before browser launch '+args.join(' '),()=>{
 const f=fixture(args)
 try {assert.notEqual(f.result.status,0);assert.equal(f.log,null);assert.equal(existsSync(join(f.dir,'result.pdf')),false)}
 finally {cleanup(f.dir)}
})
