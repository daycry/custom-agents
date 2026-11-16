import {test} from 'node:test'
import assert from 'node:assert/strict'
import {mkdtempSync,mkdirSync,writeFileSync,readFileSync,rmSync,copyFileSync,symlinkSync} from 'node:fs'
import {tmpdir} from 'node:os'
import {join,delimiter} from 'node:path'
import {spawnSync} from 'node:child_process'
import {fileURLToPath} from 'node:url'

test('Codex state: synchronous native spawn cannot renew an expired query deadline',()=>{
  const root=mkdtempSync(join(tmpdir(),'ca-deadline-owned-')),bin=join(root,'bin')
  mkdirSync(bin)
  const executable=join(bin,process.platform==='win32'?'codex.exe':'codex')
  if(process.platform==='win32')copyFileSync(process.execPath,executable)
  else symlinkSync(process.execPath,executable)
  writeFileSync(join(root,'package.json'),'{"type":"module"}')
  writeFileSync(join(root,'plugin'),'console.log(JSON.stringify({installed:[],available:[]}))')
  const marker=join(root,'spawn.json'),preload=join(root,'spawn-delay.cjs')
  writeFileSync(preload,`const cp=require('node:child_process'),fs=require('node:fs');
const original=cp.spawn;
process.argv[3]=String(Date.now()+500);
cp.spawn=(...args)=>{const child=original(...args);const before=Date.now();Atomics.wait(new Int32Array(new SharedArrayBuffer(4)),0,0,1000);fs.writeFileSync(${JSON.stringify(marker)},JSON.stringify({before,after:Date.now(),child:child.pid,deadline:Number(process.argv[3])}));return child};
require('node:module').syncBuiltinESMExports();`)
  const env={}
  for(const key of ['SystemRoot','WINDIR','COMSPEC','PATHEXT','NODE_V8_COVERAGE'])if(process.env[key])env[key]=process.env[key]
  Object.assign(env,{HOME:root,USERPROFILE:root,CODEX_HOME:join(root,'.codex'),PATH:[bin,process.platform==='win32'?join(process.env.SystemRoot,'System32'):'/usr/bin:/bin'].join(delimiter)})
  const helper=fileURLToPath(new URL('../agent-kits/shared/codex-plugin-state.mjs',import.meta.url))
  try{
    const result=spawnSync(process.execPath,['--require',preload,helper,'--query-worker',String(Date.now()+20000)],{cwd:root,env,encoding:'utf8',timeout:12000})
    const observed=JSON.parse(readFileSync(marker,'utf8'))
    assert.ok(Number.isInteger(observed.child) && observed.child>0,'fixture must launch an actual native process')
    assert.ok(observed.after>observed.deadline,'fixture must return from native spawn after the original deadline')
    assert.equal(result.error,undefined)
    assert.equal(result.status,124,'late native output must remain a timeout, without granting a new timer budget')
    assert.equal(result.stdout,'','expired native output must not reach the consumer')
    assert.throws(()=>process.kill(observed.child,0),'expired native process must be gone before worker exit')
  }finally{rmSync(root,{recursive:true,force:true,maxRetries:50,retryDelay:100})}
})

// fix16 (gap 21): el plazo del producto (3 s) corre desde que el WORKER esta listo, no desde antes de lanzarlo: un arranque lento del worker (carga de CPU)
// ya no consume el plazo de codex. El worker arranca 2,5 s tarde (preload solo para `--query-worker`) y codex tarda 0,6 s: con el plazo fijado antes
// del lanzamiento (3 s desde el padre) le quedan 0,5 s a codex y da `cli-timeout`.
test('Codex state: a slow worker start does not consume the native query budget (fix16, gap 21)',async()=>{
  const {queryCodexPlugin,runCodexQuery}=await import('../agent-kits/shared/codex-plugin-state.mjs')
  const root=mkdtempSync(join(tmpdir(),'ca-deadline-ready-')),bin=join(root,'bin')
  mkdirSync(bin)
  const executable=join(bin,process.platform==='win32'?'codex.exe':'codex')
  if(process.platform==='win32')copyFileSync(process.execPath,executable)
  else symlinkSync(process.execPath,executable)
  writeFileSync(join(root,'package.json'),'{"type":"module"}')
  writeFileSync(join(root,'plugin'),'await new Promise(r=>setTimeout(r,600));console.log(JSON.stringify({installed:[{pluginId:"custom-agents@daycry",installed:true,enabled:true,version:"1.22.0"}],available:[]}))')
  const preload=join(root,'slow-worker.cjs')
  writeFileSync(preload,"if(process.argv.includes('--query-worker'))Atomics.wait(new Int32Array(new SharedArrayBuffer(4)),0,0,2500)")
  const env={}
  for(const key of ['SystemRoot','WINDIR','COMSPEC','PATHEXT','NODE_V8_COVERAGE'])if(process.env[key])env[key]=process.env[key]
  Object.assign(env,{HOME:root,USERPROFILE:root,CODEX_HOME:join(root,'.codex'),NODE_OPTIONS:'--require '+JSON.stringify(preload.split(String.fromCharCode(92)).join('/')),
    PATH:[bin,process.platform==='win32'?join(process.env.SystemRoot,'System32'):'/usr/bin:/bin'].join(delimiter)})
  try{
    const state=queryCodexPlugin({cwd:root,timeout:3000,runner:(args,options)=>runCodexQuery(args,{...options,env})})
    assert.equal(state.reason,null,'the worker start must not consume the budget of the native query')
    assert.equal(state.state,'installed')
  }finally{rmSync(root,{recursive:true,force:true,maxRetries:50,retryDelay:100})}
})
