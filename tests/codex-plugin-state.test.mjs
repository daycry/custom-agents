import {test} from 'node:test'
import assert from 'node:assert/strict'
import {mkdtempSync,mkdirSync,writeFileSync,readFileSync,existsSync,rmSync,chmodSync,copyFileSync,symlinkSync} from 'node:fs'
import {tmpdir} from 'node:os'
import {join,resolve,delimiter} from 'node:path'
import {execFileSync,spawn} from 'node:child_process'
import {fileURLToPath} from 'node:url'
import {queryCodexPlugin,runCodexQuery,terminateProcessTree} from '../agent-kits/shared/codex-plugin-state.mjs'

function nativeProcessIsLive(pid) {
  try {process.kill(pid,0)}
  catch(error) {if(error.code==='ESRCH')return false;throw error}
  if(process.platform!=='linux')return true
  try {
    const raw=readFileSync(`/proc/${pid}/stat`,'utf8')
    const state=raw.slice(raw.lastIndexOf(')')+2).split(' ')[0]
    // A terminal PID can remain visible until its parent reaps it; it cannot run.
    // Keep stopped, sleeping, running and unknown states observable as survivors.
    return state!=='Z' && state!=='X'
  } catch(error) {if(error.code==='ENOENT' || error.code==='ESRCH')return false;throw error}
}

test('Codex state liveness oracle rejects a surviving process, including a stopped one',()=>{
  const child=spawn(process.execPath,['-e','setInterval(()=>{},1000)'],{stdio:'ignore'})
  try {
    assert.ok(Number.isInteger(child.pid),'fixture must own a real child')
    assert.equal(nativeProcessIsLive(child.pid),true)
    if(process.platform==='linux') {
      process.kill(child.pid,'SIGSTOP')
      assert.equal(nativeProcessIsLive(child.pid),true,'a stopped child is not terminated')
    }
  } finally {try {child.kill('SIGKILL')} catch {}}
})

test('Codex state liveness oracle recognizes an exited child before it is reaped',{skip:process.platform!=='linux'},()=>{
  const child=spawn(process.execPath,['-e','setInterval(()=>{},1000)'],{stdio:'ignore'})
  try {
    assert.ok(Number.isInteger(child.pid),'fixture must own a real child')
    process.kill(child.pid,'SIGKILL')
    const until=Date.now()+5000,wait=new Int32Array(new SharedArrayBuffer(4))
    let state
    do {
      const raw=readFileSync(`/proc/${child.pid}/stat`,'utf8')
      state=raw.slice(raw.lastIndexOf(')')+2).split(' ')[0]
      if(state==='Z')break
      Atomics.wait(wait,0,0,5)
    } while(Date.now()<until)
    assert.equal(state,'Z','fixture must create a terminal child while its owner cannot reap yet')
    assert.doesNotThrow(()=>process.kill(child.pid,0),'terminal PID must still exist for this regression')
    assert.equal(nativeProcessIsLive(child.pid),false,'an unreaped terminal child cannot survive cleanup')
  } finally {try {child.kill('SIGKILL')} catch {}}
})

function fixture() {
  const root=mkdtempSync(join(tmpdir(),'ca-state-owned-')),bin=join(root,'bin')
  mkdirSync(bin)
  const env={}
  for(const key of ['SystemRoot','WINDIR','COMSPEC','PATHEXT','NODE_V8_COVERAGE']) if(process.env[key])env[key]=process.env[key]
  Object.assign(env,{HOME:root,USERPROFILE:root,CODEX_HOME:join(root,'.codex'),PATH:[bin,process.platform==='win32' ? join(process.env.SystemRoot,'System32') : '/usr/bin:/bin'].join(delimiter)})
  const script=join(root,'native-owned.mjs')
  const shim=join(bin,process.platform==='win32' ? 'codex.cmd' : 'codex')
  const create=body=>{
    writeFileSync(script,body)
    writeFileSync(shim,process.platform==='win32' ? `@echo off\r\n"${process.execPath}" "${script}" %*\r\n`
      : `#!/bin/sh\nexec '${process.execPath.replace(/'/g,"'\\''")}' '${script.replace(/'/g,"'\\''")}' "$@"\n`)
    if(process.platform!=='win32')chmodSync(shim,0o755)
  }
  const createDirectNode=body=>{
    const binary=join(bin,process.platform==='win32' ? 'codex.exe' : 'codex')
    if(!existsSync(binary)) {
      if(process.platform==='win32') {
        copyFileSync(process.execPath,binary)
        // Prepare the copied fixture before measuring its query deadline.
        assert.equal(execFileSync(binary,['--version'],{cwd:root,env,encoding:'utf8',timeout:10000}).trim(),process.version)
      } else symlinkSync(process.execPath,binary)
    }
    writeFileSync(join(root,'package.json'),'{"type":"module"}')
    writeFileSync(join(root,'plugin'),body)
  }
  return {root,bin,env,create,createDirectNode,close:()=>rmSync(root,{recursive:true,force:true})}
}

test('Codex state: real standalone native query is bounded and emits only sanitized local state',()=>{
  const owned=fixture()
  try {
    const marker=join(owned.root,'argv.json')
    owned.createDirectNode(`import fs from 'node:fs';fs.writeFileSync(${JSON.stringify(marker)},JSON.stringify(['plugin',...process.argv.slice(2)]));console.log(JSON.stringify({installed:[{pluginId:'custom-agents@daycry',installed:true,enabled:true,version:'1.22.0',source:'PRIVATE_SOURCE'}],available:[]}));`)
    const helper=resolve(fileURLToPath(new URL('../agent-kits/shared/codex-plugin-state.mjs',import.meta.url)))
    const state=JSON.parse(execFileSync(process.execPath,[helper,'--project',owned.root],{cwd:owned.root,env:owned.env,encoding:'utf8',timeout:10000}))
    assert.deepEqual(state,{state:'installed',enabled:true,version:'1.22.0',reason:null})
    assert.deepEqual(JSON.parse(readFileSync(marker,'utf8')),['plugin','list','--marketplace','daycry','--available','--json'])
    assert.equal(JSON.parse(execFileSync(process.execPath,[helper,'--invalid'],{cwd:owned.root,env:owned.env,encoding:'utf8'})).reason,'invalid-arguments')
    owned.createDirectNode('setInterval(()=>{},1000)')
    const began=Date.now()
    const timeout=queryCodexPlugin({cwd:owned.root,timeout:1000,runner:(args,options)=>runCodexQuery(args,{...options,env:owned.env})})
    assert.equal(timeout.reason,'cli-timeout')
    assert.ok(Date.now()-began<9000,'native query timeout and cleanup must remain bounded')
  } finally {owned.close()}
})

test('Codex state: real runner missing binary and schema variants do not invent state',()=>{
  const owned=fixture()
  try {
    assert.throws(()=>runCodexQuery([],{cwd:owned.root,env:{...owned.env,PATH:owned.bin}}),{code:'ENOENT'})
    const query=value=>queryCodexPlugin({runner:()=>JSON.stringify(value)})
    assert.equal(query({installed:[],available:[{pluginId:'custom-agents@daycry',installed:false,enabled:false,version:null}]}).state,'absent')
    assert.equal(query({installed:[],available:[{pluginId:'custom-agents@daycry',installed:false,enabled:false,version:123}]}).state,'unknown')
    const target={pluginId:'custom-agents@daycry',installed:true,enabled:true,version:'1.22.0'}
    assert.equal(query({installed:[target,target],available:[]}).state,'unknown')
    terminateProcessTree(null)
    terminateProcessTree(-1)
  } finally {owned.close()}
})

test('Codex state: timeout kills non-cooperative native process and descendants before returning',()=>{
  const owned=fixture(),pidFile=join(owned.root,'descendant.pid'),parentFile=join(owned.root,'parent.pid')
  try {
    const child=`import fs from 'node:fs';fs.writeFileSync(${JSON.stringify(pidFile)},String(process.pid));process.on('SIGTERM',()=>{});setTimeout(()=>process.exit(0),12000)`
    owned.createDirectNode(`import fs from 'node:fs';import {spawn} from 'node:child_process';fs.writeFileSync(${JSON.stringify(parentFile)},String(process.pid));process.on('SIGTERM',()=>{});const child=spawn(process.execPath,['--input-type=module','-e',${JSON.stringify(child)}],{stdio:'inherit'});child.on('exit',()=>process.exit(0));`)
    const began=Date.now()
    const state=queryCodexPlugin({cwd:owned.root,timeout:3000,runner:(args,options)=>runCodexQuery(args,{...options,env:owned.env})})
    assert.equal(state.reason,'cli-timeout')
    // Ceiling = 3 s deadline + runCodexQuery's 4 s outer SIGKILL, plus spawn/teardown margin
    // (Windows taskkill + CIM sweep under a loaded runner). Still far below the 12 s the
    // non-cooperative descendant would live if the query waited for it.
    assert.ok(Date.now()-began<9500,'query waited for non-cooperative process after its deadline')
    assert.ok(existsSync(pidFile),'fixture must start its descendant before the deadline')
    const pid=Number(readFileSync(pidFile,'utf8'))
    assert.equal(nativeProcessIsLive(pid),false,'native descendant survived query timeout cleanup')
  } finally {
    for(const file of [pidFile,parentFile]) if(existsSync(file)) {
      try {process.kill(Number(readFileSync(file,'utf8')),'SIGKILL')} catch {}
    }
    // Windows may retain a copied executable/CWD handle briefly after termination.
    rmSync(owned.root,{recursive:true,force:true,maxRetries:50,retryDelay:100})
  }
})

test('Codex state: native installed schema accepts only the exact plugin and boolean enablement',async()=>{
  const {queryCodexPlugin}=await import('../agent-kits/shared/codex-plugin-state.mjs')
  const query=payload=>queryCodexPlugin({cwd:process.cwd(),runner:()=>JSON.stringify(payload)})
  assert.deepEqual(query({installed:[{pluginId:'other@daycry',installed:true,enabled:true,version:'1.0.0'}],available:[]}),{state:'absent',enabled:null,version:null,reason:'not-installed'})
  assert.deepEqual(query({installed:[{pluginId:'custom-agents@daycry',installed:true,enabled:false,version:'1.22.0'}],available:[]}),{state:'installed',enabled:false,version:'1.22.0',reason:null})
  assert.equal(query({installed:[{pluginId:'custom-agents@daycry',installed:true,enabled:'true',version:'1.22.0'}],available:[]}).state,'unknown')
  assert.equal(query({installed:[{pluginId:'custom-agents@daycry',installed:true,enabled:true,version:'private\nraw text'}],available:[]}).state,'unknown')
})

test('Codex state: missing CLI, failure, malformed and unsupported JSON remain unknown',async()=>{
  const {queryCodexPlugin}=await import('../agent-kits/shared/codex-plugin-state.mjs')
  for(const payload of ['not JSON','{}','[]','{"installed":[],"available":{}}']) assert.equal(queryCodexPlugin({runner:()=>payload}).state,'unknown')
  assert.deepEqual(queryCodexPlugin({runner:()=>{const e=new Error('private raw failure');e.code='ENOENT';throw e}}),{state:'unknown',enabled:null,version:null,reason:'cli-unavailable'})
  assert.equal(queryCodexPlugin({runner:()=>{throw new Error('private raw failure')}}).reason,'cli-failed')
})
