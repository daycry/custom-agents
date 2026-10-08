#!/usr/bin/env node
// Read native local plugin state. No config edits, credentials, source paths or raw errors in output.
import {execFileSync,spawn} from 'node:child_process'
import {statSync} from 'node:fs'
import {delimiter, join, resolve} from 'node:path'
import {fileURLToPath} from 'node:url'

export const CODEX_PLUGIN_ID = 'custom-agents@daycry'
export const CODEX_QUERY_TIMEOUT_MS = 3_000
const QUERY_ARGS=['plugin','list','--marketplace','daycry','--available','--json']
const HELPER=fileURLToPath(import.meta.url)
const unknown = reason => ({state:'unknown', enabled:null, version:null, reason})
const validVersion = value => typeof value==='string' && /^[A-Za-z0-9.+-]{1,64}$/.test(value)

export function terminateProcessTree(pid) {
  if (!Number.isInteger(pid) || pid <= 0) return
  if (process.platform !== 'win32') {
    try {process.kill(-pid,'SIGKILL')} catch {/* process group already gone */}
    return
  }
  const system=join(process.env.SystemRoot || 'C:\\Windows','System32')
  try {execFileSync(join(system,'taskkill.exe'),['/T','/F','/PID',String(pid)],{stdio:'ignore',timeout:1000})} catch {/* direct child already gone */}
  // A killed cmd shim can leave children whose recorded parent PID is still the old PID.
  try {
    execFileSync(join(system,'WindowsPowerShell/v1.0/powershell.exe'),['-NoProfile','-NonInteractive','-Command',
      `$all=@(Get-CimInstance Win32_Process); $ids=@(${pid}); for($i=0;$i -lt $ids.Count;$i++){ $ids+=@($all | Where-Object { $_.ParentProcessId -eq $ids[$i] -and $_.ProcessId -notin $ids } | Select-Object -ExpandProperty ProcessId) }; [array]::Reverse($ids); foreach($id in $ids){ Stop-Process -Id $id -Force -ErrorAction SilentlyContinue }`],
    {stdio:'ignore',timeout:2000})
  } catch {/* best effort, bounded even on machines without CIM */}
}

function executable(env) {
  const extensions=process.platform==='win32'
    ? (env.PATHEXT || '.COM;.EXE;.BAT;.CMD').split(';').filter(e=>/^\.(com|exe|bat|cmd)$/i.test(e)) : ['']
  for(const dir of String(env.PATH || env.Path || '').split(delimiter).filter(Boolean)) {
    for(const ext of extensions) {
      const candidate=join(dir,`codex${ext.toLowerCase()}`)
      try {if(statSync(candidate).isFile()) return candidate} catch {/* next candidate */}
    }
  }
  const error=new Error('Codex CLI unavailable');error.code='ENOENT';throw error
}

// The synchronous caller waits only for our Node worker. The worker owns an asynchronous
// watchdog and kills the native tree before exiting, even when SIGTERM is ignored or a
// descendant retains native stdout. Native pipe handles never reach this outer wait.
export function runCodexQuery(args, {cwd,timeout=CODEX_QUERY_TIMEOUT_MS,env=process.env}={}) {
  executable(env) // Preserve the missing-CLI classification without starting a worker.
  if(JSON.stringify(args)!==JSON.stringify(QUERY_ARGS)) throw new Error('unsupported native query arguments')
  const limit=Number.isFinite(timeout) && timeout>0 ? Math.min(timeout,CODEX_QUERY_TIMEOUT_MS) : CODEX_QUERY_TIMEOUT_MS
  try {
    return execFileSync(process.execPath,[HELPER,'--query-worker',String(Date.now()+limit)],
      {cwd,env,timeout:limit+4000,killSignal:'SIGKILL',encoding:'utf8',stdio:['ignore','pipe','pipe'],maxBuffer:4*1024*1024})
  } catch(error) {
    if(error.status===124) error.code='ETIMEDOUT'
    throw error
  }
}

function queryWorker(timeout) {
  if(timeout<=0) {process.exitCode=124;return}
  let command
  try {command=executable(process.env)} catch {process.exitCode=127;return}
  let args=QUERY_ARGS
  const options={stdio:['ignore','pipe','ignore'],detached:process.platform!=='win32'}
  if(process.platform==='win32' && /\.(cmd|bat)$/i.test(command)) {
    // Do not expand a literal '%' in a shim path into environment data.
    const quoted=String(command).split('%').map(s=>`"${s.replace(/"/g,'""')}"`).join('^%')
    args=['/d','/s','/c',`"${quoted} ${QUERY_ARGS.map(a=>`"${a}"`).join(' ')}"`]
    command=process.env.COMSPEC || 'cmd.exe'
    options.windowsVerbatimArguments=true
  }
  const child=spawn(command,args,options)
  let chunks=[],size=0,finished=false
  const finish=(status,kill=false)=>{
    if(finished) return
    finished=true;clearTimeout(timer)
    if(kill) terminateProcessTree(child.pid)
    child.stdout.destroy()
    if(status===0) process.stdout.write(Buffer.concat(chunks),()=>process.exit(0))
    else process.exit(status)
  }
  const timer=setTimeout(()=>finish(124,true),timeout)
  child.stdout.on('data',chunk=>{
    size+=chunk.length
    if(size>4*1024*1024) finish(125,true)
    else chunks.push(chunk)
  })
  child.on('error',()=>finish(126,true))
  child.on('close',status=>finish(status===0 ? 0 : 126))
}

export function parseCodexPluginState(raw) {
  let value
  try {value=JSON.parse(String(raw))} catch {return unknown('invalid-json')}
  if(!value || typeof value!=='object' || !Array.isArray(value.installed) || !Array.isArray(value.available)) return unknown('unsupported-schema')
  for(const entry of value.installed) {
    if(!entry || typeof entry.pluginId!=='string' || entry.installed!==true || typeof entry.enabled!=='boolean'
      || !validVersion(entry.version)) return unknown('unsupported-schema')
  }
  for(const entry of value.available) {
    if(!entry || typeof entry.pluginId!=='string' || entry.installed!==false || typeof entry.enabled!=='boolean'
      || (entry.version!==null && !validVersion(entry.version))) return unknown('unsupported-schema')
  }
  const matches=value.installed.filter(entry=>entry.pluginId===CODEX_PLUGIN_ID)
  if(matches.length>1) return unknown('unsupported-schema')
  if(!matches.length) return {state:'absent',enabled:null,version:null,reason:'not-installed'}
  return {state:'installed',enabled:matches[0].enabled,version:matches[0].version,reason:null}
}

export function queryCodexPlugin({cwd,runner=runCodexQuery,timeout=CODEX_QUERY_TIMEOUT_MS}={}) {
  try {
    // Explicit local marketplace avoids the native CLI's default remote-catalog listing.
    return parseCodexPluginState(runner([...QUERY_ARGS],{cwd,timeout}))
  } catch(error) {
    return unknown(error?.code==='ENOENT' ? 'cli-unavailable' : error?.code==='ETIMEDOUT' || error?.expirado ? 'cli-timeout' : 'cli-failed')
  }
}

if(process.argv[1] && resolve(process.argv[1])===HELPER) {
  const args=process.argv.slice(2)
  if(args.length===2 && args[0]==='--query-worker' && /^\d{1,16}$/.test(args[1])) queryWorker(Math.min(CODEX_QUERY_TIMEOUT_MS,Number(args[1])-Date.now()))
  else {
    const valid=args.length===0 || args.length===2 && args[0]==='--project' && Boolean(args[1])
    console.log(JSON.stringify(valid ? queryCodexPlugin({cwd:args.length ? resolve(args[1]) : process.cwd()}) : unknown('invalid-arguments')))
  }
}
