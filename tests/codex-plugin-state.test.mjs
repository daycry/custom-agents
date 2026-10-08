import {test} from 'node:test'
import assert from 'node:assert/strict'
import {mkdtempSync,mkdirSync,writeFileSync,readFileSync,existsSync,rmSync,chmodSync,copyFileSync} from 'node:fs'
import {tmpdir} from 'node:os'
import {join,resolve,delimiter} from 'node:path'
import {execFileSync} from 'node:child_process'
import {fileURLToPath} from 'node:url'
import {queryCodexPlugin,runCodexQuery,terminateProcessTree} from '../agent-kits/shared/codex-plugin-state.mjs'

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
    if(!existsSync(binary)) copyFileSync(process.execPath,binary)
    if(process.platform!=='win32')chmodSync(binary,0o755)
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
    assert.ok(Date.now()-began<7500,'query waited for non-cooperative process after its deadline')
    assert.ok(existsSync(pidFile),'fixture must start its descendant before the deadline')
    const pid=Number(readFileSync(pidFile,'utf8'))
    assert.throws(()=>process.kill(pid,0),'native descendant survived query timeout cleanup')
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
