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
