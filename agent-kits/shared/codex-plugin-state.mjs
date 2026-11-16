#!/usr/bin/env node
// Read native local plugin state. No config edits, credentials, source paths or raw errors in output.
import {execFileSync,spawn,spawnSync} from 'node:child_process'
import {statSync} from 'node:fs'
import {delimiter, isAbsolute, join, resolve} from 'node:path'
import {fileURLToPath} from 'node:url'

export const CODEX_PLUGIN_ID = 'custom-agents@daycry'
// fix16 (gap 21): 6 s (eran 3 s). Con la maquina saturada (12 bucles de CPU) el arranque de node del propio shim de codex (`codex.cmd` -> node) tarda una mediana de 3,7 s y el plazo de
// 3 s ni siquiera dejaba arrancar a codex. Ningun anfitrion impone mas de 10 s al ayudante (`doctor.py`): el tope exterior es limite + 3 s (9 s) y la limpieza del arbol cabe dentro.
export const CODEX_QUERY_TIMEOUT_MS = 6_000
// Igual que `CUSTOM_AGENTS_EXEC_TIMEOUT_MS` del instalador: quien tenga una maquina lenta (o un arnes de CI saturado) puede subir el tope con `CUSTOM_AGENTS_CODEX_QUERY_TIMEOUT_MS`
// (de 1.000 a 60.000 ms); un valor ilegible se ignora. El diagnostico sigue imponiendo 10 s al ayudante.
const capMs=env=>{const n=Number(env?.CUSTOM_AGENTS_CODEX_QUERY_TIMEOUT_MS);return Number.isInteger(n) && n>=1000 && n<=60000 ? n : CODEX_QUERY_TIMEOUT_MS}
const QUERY_ARGS=['plugin','list','--marketplace','daycry','--available','--json']
const HELPER=fileURLToPath(import.meta.url)
const unknown = reason => ({state:'unknown', enabled:null, version:null, reason})
const validVersion = value => typeof value==='string' && /^[A-Za-z0-9.+-]{1,64}$/.test(value)

// fix16 (gap 10): en Windows `taskkill /T /F` (p50 1,1-1,2 s) y el barrido de PowerShell (p50 2,5-3,2 s) se agotaban en serie con topes de 1 s y 2 s: con el
// lanzador real de npm (`codex.cmd` -> node -> descendiente) quedaban 3 de 3 arboles huerfanos. Ahora corren EN PARALELO (taskkill en segundo plano, el barrido
// bloqueando), con un tope TOTAL de 8 s, y la muerte se CONFIRMA con un sondeo acotado de los pids (el del arbol y los que el barrido encontro).
// `budgetMs` acota la espera: el worker de la consulta lo ajusta al tope EXTERIOR de `runCodexQuery` (limite + 4 s, y el diagnostico impone 10 s al ayudante):
// si el exterior mata al worker a mitad de la limpieza, los descendientes quedarian huerfanos.
export const TREE_KILL_TOTAL_MS = 8_000
// Tope EXTERIOR de la consulta: limite + 3 s y, como minimo, 7 s (el valor de siempre para plazos pequeños). Con el plazo por defecto son 9 s, dentro de los 10 s del diagnostico.
const outerMs=limit=>Math.max(limit+3000,7000)
export function terminateProcessTree(pid,budgetMs=TREE_KILL_TOTAL_MS,maxMs=TREE_KILL_TOTAL_MS) {
  if (!Number.isInteger(pid) || pid <= 0) return
  if (process.platform !== 'win32') {
    try {process.kill(-pid,'SIGKILL')} catch {/* process group already gone */}
    return
  }
  const deadline=Date.now()+Math.min(maxMs,Math.max(1000,Number.isFinite(budgetMs) ? budgetMs : TREE_KILL_TOTAL_MS))
  const system=join(process.env.SystemRoot || 'C:\\Windows','System32')
  try {
    const killer=spawn(join(system,'taskkill.exe'),['/T','/F','/PID',String(pid)],{stdio:'ignore',windowsHide:true})
    killer.on('error',()=>{});killer.unref()
  } catch {/* direct child already gone */}
  // A killed cmd shim can leave children whose recorded parent PID is still the old PID: the sweep follows ParentProcessId from the recorded PID.
  const ids=new Set([pid])
  try {
    const swept=spawnSync(join(system,'WindowsPowerShell/v1.0/powershell.exe'),['-NoProfile','-NonInteractive','-Command',
      `$all=@(Get-CimInstance Win32_Process); $ids=@(${pid}); for($i=0;$i -lt $ids.Count;$i++){ $ids+=@($all | Where-Object { $_.ParentProcessId -eq $ids[$i] -and $_.ProcessId -notin $ids } | Select-Object -ExpandProperty ProcessId) }; [array]::Reverse($ids); foreach($id in $ids){ Stop-Process -Id $id -Force -ErrorAction SilentlyContinue }; $ids -join ' '`],
    {stdio:['ignore','pipe','ignore'],encoding:'utf8',windowsHide:true,timeout:Math.max(1000,deadline-Date.now()-500)})
    for(const found of String(swept.stdout || '').split(/\s+/)) if(/^\d{1,10}$/.test(found)) ids.add(Number(found))
  } catch {/* best effort, bounded even on machines without CIM */}
  const alive=id=>{try {process.kill(id,0);return true} catch(error) {return error.code==='EPERM'}}
  const wait=new Int32Array(new SharedArrayBuffer(4))
  while([...ids].some(alive) && Date.now()<deadline) Atomics.wait(wait,0,0,50)
}

function executable(env) {
  const extensions=process.platform==='win32'
    ? (env.PATHEXT || '.COM;.EXE;.BAT;.CMD').split(';').filter(e=>/^\.(com|exe|bat|cmd)$/i.test(e)) : ['']
  // Only absolute PATH entries: empty or relative ones (`.`, `bin`, `C:bin`) depend on the
  // current directory, where an untrusted repository could plant a launcher.
  const absolute=dir=>process.platform==='win32' ? /^(?:[A-Za-z]:[\\/]|[\\/]{2})/.test(dir) : isAbsolute(dir)
  for(const raw of String(env.PATH || env.Path || '').split(delimiter)) {
    const dir=raw.trim().replace(/^"(.*)"$/,'$1')
    if(!dir || !absolute(dir))continue
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
export function runCodexQuery(args, {cwd,timeout,env=process.env}={}) {
  executable(env) // Preserve the missing-CLI classification without starting a worker.
  if(JSON.stringify(args)!==JSON.stringify(QUERY_ARGS)) throw new Error('unsupported native query arguments')
  const cap=capMs(env)
  const limit=Number.isFinite(timeout) && timeout>0 ? Math.min(timeout,cap) : cap
  try {
    // NoDefaultCurrentDirectoryInExePath: the worker and the npm shim it starts never resolve
    // `node` (or any command) from the project directory, where it could be planted.
    return execFileSync(process.execPath,[HELPER,'--query-worker',String(Date.now()+limit),String(limit)],
      {cwd,env:{...env,NoDefaultCurrentDirectoryInExePath:'1'},timeout:outerMs(limit),killSignal:'SIGKILL',encoding:'utf8',stdio:['ignore','pipe','pipe'],maxBuffer:4*1024*1024})
  } catch(error) {
    if(error.status===124) error.code='ETIMEDOUT'
    throw error
  }
}

// fix16 (gap 21): con `limit` (relativo) el plazo corre desde que el worker esta LISTO (aqui): el arranque lento de node bajo carga no lo consume. Sin
// `limit` (sondas antiguas) `deadline` es absoluto, como antes. El tope exterior de `runCodexQuery` (`limit+4000`) sigue acotando el arranque.
function queryWorker(deadline,limit) {
  const outerKill=limit!==undefined ? deadline-limit+outerMs(limit) : deadline+4000   // `runCodexQuery` mata al worker a `outerMs(limite)` del lanzamiento: la limpieza del arbol debe caber antes
  if(limit!==undefined) deadline=Date.now()+limit
  deadline=Math.min(deadline,Date.now()+capMs(process.env))
  const timeout=deadline-Date.now()
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
  let chunks=[],size=0,finished=false,timer
  const finish=(status,kill=false)=>{
    if(finished) return
    if(status===0 && Date.now()>=deadline) {status=124;kill=true}
    finished=true;clearTimeout(timer)
    if(kill) terminateProcessTree(child.pid,outerKill-Date.now()-500)
    child.stdout.destroy()
    if(status===0) process.stdout.write(Buffer.concat(chunks),()=>process.exit(0))
    else process.exit(status)
  }
  child.stdout.on('data',chunk=>{
    size+=chunk.length
    if(size>4*1024*1024) finish(125,true)
    else chunks.push(chunk)
  })
  child.on('error',()=>finish(126,true))
  child.on('close',status=>finish(status===0 ? 0 : 126))
  // Native spawn can block synchronously; it must consume the original budget.
  const remaining=deadline-Date.now()
  if(remaining<=0) {finish(124,true);return}
  timer=setTimeout(()=>finish(124,true),remaining)
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

export function queryCodexPlugin({cwd,runner=runCodexQuery,timeout}={}) {
  try {
    // Explicit local marketplace avoids the native CLI's default remote-catalog listing.
    return parseCodexPluginState(runner([...QUERY_ARGS],{cwd,timeout}))
  } catch(error) {
    return unknown(error?.code==='ENOENT' ? 'cli-unavailable' : error?.code==='ETIMEDOUT' || error?.expirado ? 'cli-timeout' : 'cli-failed')
  }
}

if(process.argv[1] && resolve(process.argv[1])===HELPER) {
  const args=process.argv.slice(2)
  if((args.length===2 || args.length===3 && /^\d{1,16}$/.test(args[2])) && args[0]==='--query-worker' && /^\d{1,16}$/.test(args[1])) queryWorker(Number(args[1]),args.length===3 ? Number(args[2]) : undefined)
  else {
    const valid=args.length===0 || args.length===2 && args[0]==='--project' && Boolean(args[1])
    console.log(JSON.stringify(valid ? queryCodexPlugin({cwd:args.length ? resolve(args[1]) : process.cwd()}) : unknown('invalid-arguments')))
  }
}
