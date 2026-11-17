#!/usr/bin/env node
// Read native local plugin state. No config edits, credentials, source paths or raw errors in output.
import {execFileSync,spawn,spawnSync} from 'node:child_process'
import {statSync,writeSync} from 'node:fs'
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

// fix17 (gaps 3, 5, 18 y 19) y fix18 (gap 3): arbol de procesos de Windows con IDENTIDAD. Windows reutiliza los pid y el `ParentProcessId` de un proceso conserva el pid de un padre muerto: matar
// «todo lo que cuelga del pid X» alcanza a procesos AJENOS y ANTERIORES (se vio con 25 padres huerfanos en una sesion: `explorer.exe`, `OneDrive.exe`…). Reglas:
//  - `since` (ms, reloj de pared: el instante del lanzamiento menos 100 ms): un proceso solo cuenta si su `CreationDate` >= `since` y >= la de su padre; si la raiz esta MUERTA
//    (`rootAlive:false`), los hijos directos ademas deben ser anteriores a `until` (el instante en que SALIO: el evento `exit` del llamador; un hijo de un proceso que reutilizo el pid nace despues).
//    Los llamadores deciden `rootAlive` por el estado real de su handle (`exitCode`/`exit`), no por `alive(pid)`: con el handle abierto el pid no se reutiliza.
//  - Con la raiz VIVA el dueño del temporizador mata con `taskkill /T /F` (0,6-1,1 s con carga; ya filtra por fecha de creacion) y SOLO espera a taskkill: no al barrido.
//  - El barrido CIM (una proyeccion `ProcessId,ParentProcessId,CreationDate` y busqueda en anchura en el cliente) es el respaldo para los huerfanos fuera del arbol y el UNICO mecanismo con la
//    raiz muerta. Se lanza FUERA del job del worker (fix18): un PowerShell hijo normal muere cuando el worker sale (job de libuv con KILL_ON_JOB_CLOSE) y la foto CIM tarda 1-4 s con carga, mas
//    que el presupuesto; con `detached` puro (DETACHED_PROCESS) PowerShell no tiene consola y sale SIN ejecutar nada (medido), asi que va con `cmd /c start /b` (detached) y `-EncodedCommand`
//    (sin interpolar texto en una linea de cmd). Comprueba pid + fecha de creacion JUSTO antes de cada `Stop-Process`, en la misma orden: el pid que `taskkill` libera no mata a un ajeno.
export const TREE_KILL_TOTAL_MS=8_000
const CLEANUP_RESERVE_MS=2_000       // limpieza del arbol (taskkill con la raiz viva) dentro del tope exterior de la consulta
const alive=id=>{try {process.kill(id,0);return true} catch(error) {return error.code==='EPERM'}}
export const sweepScript=(pid,since,until,rootAlive)=>[
  "$ErrorActionPreference='SilentlyContinue'",
  `$root=${pid};$since=${since};$until=${until};$rootAlive=${rootAlive ? '$true' : '$false'}`,
  'function T($d){([DateTimeOffset]::new($d)).ToUnixTimeMilliseconds()}',
  '$all=@(Get-CimInstance Win32_Process -Property ProcessId,ParentProcessId,CreationDate)',
  '$by=@{};foreach($p in $all){$k=[int]$p.ParentProcessId;if(-not $by.ContainsKey($k)){$by[$k]=New-Object System.Collections.ArrayList};[void]$by[$k].Add($p)}',
  '$kill=New-Object System.Collections.ArrayList;$q=New-Object System.Collections.Queue;$seen=@{};$low=@{}',
  '$r=$all|Where-Object{$_.ProcessId -eq $root}|Select-Object -First 1',
  '$low[$root]=$since',
  'if($rootAlive -and $r){$rt=T $r.CreationDate;if($rt -ge $since){[void]$kill.Add(@($root,$rt));$low[$root]=$rt}}',
  '$q.Enqueue($root);$seen[$root]=1',
  'while($q.Count -gt 0 -and $kill.Count -lt 512){$par=$q.Dequeue();if(-not $by.ContainsKey($par)){continue}',
  'foreach($c in $by[$par]){$cid=[int]$c.ProcessId;if($seen.ContainsKey($cid)){continue};$ct=T $c.CreationDate',
  'if($ct -ge $low[$par] -and ($par -ne $root -or $until -eq 0 -or $ct -le $until)){$seen[$cid]=1;$low[$cid]=$ct;[void]$kill.Add(@($cid,$ct));$q.Enqueue($cid)}}}',
  'for($i=$kill.Count-1;$i -ge 0;$i--){$id=$kill[$i][0];$p=Get-Process -Id $id;if($p -and [math]::Abs((T $p.StartTime)-$kill[$i][1]) -le 2000){Stop-Process -Id $id -Force}}',
].join(';')
const encodedCommand=script=>Buffer.from(script,'utf16le').toString('base64')
export function terminateProcessTree(pid,budgetMs=TREE_KILL_TOTAL_MS,maxMs=TREE_KILL_TOTAL_MS,{since=0,until=0,rootAlive=true,deps}={}) {
  if (!Number.isInteger(pid) || pid <= 0) return
  if (process.platform !== 'win32') {
    try {process.kill(-pid,'SIGKILL')} catch {/* process group already gone */}
    return
  }
  const launch=deps?.spawn || spawn,isAlive=deps?.alive || alive
  const deadline=Date.now()+Math.min(maxMs,Math.max(0,Number.isFinite(budgetMs) ? budgetMs : TREE_KILL_TOTAL_MS))
  const system=join(process.env.SystemRoot || 'C:\\Windows','System32')
  const live=rootAlive && isAlive(pid)
  let killer
  // 1) con la raiz VIVA, `taskkill /T /F`. NO se lanza `detached`: la limpieza cabe antes del SIGKILL exterior gracias a `queryPlan` (reserva de 2 s) y al presupuesto sin suelo.
  if(live) {
    try {killer=launch(join(system,'taskkill.exe'),['/T','/F','/PID',String(pid)],{stdio:'ignore',windowsHide:true});killer.on('error',()=>{});killer.unref()} catch {killer=undefined}
  }
  // 2) respaldo: barrido por identidad, FUERA del job del worker (sobrevive a su salida) y sin esperarlo.
  try {
    const powershell=join(system,'WindowsPowerShell/v1.0/powershell.exe')
    const script=sweepScript(pid,Math.max(0,Math.floor(since)),Math.max(0,Math.floor(until)),live)
    const sweeper=launch(process.env.COMSPEC || join(system,'cmd.exe'),['/d','/c',`start "" /b "${powershell}" -NoProfile -NonInteractive -WindowStyle Hidden -EncodedCommand ${encodedCommand(script)}`],
      {stdio:'ignore',windowsHide:true,detached:true,windowsVerbatimArguments:true})
    sweeper.on('error',()=>{});sweeper.unref()
  } catch {/* sin barrido: queda taskkill */}
  if(!killer) return
  const wait=new Int32Array(new SharedArrayBuffer(4))
  while(Date.now()<deadline && killer.pid && isAlive(killer.pid)) Atomics.wait(wait,0,0,50)
}

// Plazos de la consulta nativa (fix17, gap 4). El `SIGKILL` exterior de `runCodexQuery` llega a `outerMs(limit)` del lanzamiento; el plazo de la consulta (listo + limite) se recorta a
// ese tope MENOS la reserva de la limpieza, sin suelo que pase del SIGKILL: con un worker lento (carga) la consulta expira antes, el arbol se mata con la raiz viva y no quedan huerfanos.
// Tope exterior: limite + 3 s y, como minimo, 7 s (el valor de siempre para plazos pequeños). Con el plazo por defecto son 9 s, dentro de los 10 s del diagnostico.
const outerMs=limit=>Math.max(limit+3000,7000)
export function queryPlan({launchedAt,readyAt,limit}) {
  const outerKill=launchedAt+outerMs(limit)
  return {outerKill,deadline:Math.min(readyAt+limit,outerKill-CLEANUP_RESERVE_MS),cleanupBy:outerKill-200}
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

// fix16 (gap 21): con `limit` (relativo) el plazo corre desde que el worker esta LISTO (aqui): el arranque lento de node bajo carga no lo consume. fix17 (gap 4): y se recorta al tope
// exterior menos la reserva de la limpieza (`queryPlan`). Sin `limit` (sondas antiguas) `deadline` es absoluto, como antes.
function queryWorker(deadline,limit) {
  let cleanupBy
  if(limit!==undefined) {
    const plan=queryPlan({launchedAt:deadline-limit,readyAt:Date.now(),limit})
    deadline=plan.deadline;cleanupBy=plan.cleanupBy
  } else cleanupBy=deadline+4000
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
  const spawnedAt=Date.now()
  const child=spawn(command,args,options)
  let chunks=[],size=0,finished=false,timer,rootExitedAt=0
  child.on('exit',()=>{rootExitedAt=Date.now()})       // con el handle abierto el pid no se reutiliza: `exit` dice si la raiz sigue viva y desde cuando esta muerta
  const finish=(status,kill=false)=>{
    if(finished) return
    if(status===0 && Date.now()>=deadline) {status=124;kill=true}
    finished=true;clearTimeout(timer)
    if(kill) terminateProcessTree(child.pid,cleanupBy-Date.now(),TREE_KILL_TOTAL_MS,{since:spawnedAt-100,until:rootExitedAt,rootAlive:!rootExitedAt})
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

// fix17 (gap 5): ejecutor con TEMPORIZADOR PROPIO. `execFileSync` con `timeout` mata PRIMERO la raiz y el arbol solo se recupera con el barrido CIM (3,3-4,8 s; mas de 20 s con la CPU saturada);
// el dueño del plazo mata con la raiz VIVA (`taskkill /T`: ~1 s). Mismo patron que `--query-worker`: el llamador espera de forma sincrona a un worker que lanza el comando, lo vigila y,
// al expirar, mata el arbol. El resultado (`status`, `signal`, `expirado`, `error`) viaja por el descriptor 3; stdout/stderr del comando pasan tal cual.
const RUN_BOUNDED_GRACE_MS=TREE_KILL_TOTAL_MS+6_000
export function runBounded({file,args=[],cwd,env=process.env,timeoutMs,verbatim=false,maxBuffer=8*1024*1024}) {
  const spec=JSON.stringify({file,args,cwd,verbatim,timeoutMs})
  const r=spawnSync(process.execPath,[HELPER,'--run-bounded',spec],{cwd,env,encoding:'utf8',stdio:['ignore','pipe','pipe','pipe'],timeout:timeoutMs+RUN_BOUNDED_GRACE_MS,killSignal:'SIGKILL',maxBuffer,windowsHide:true})
  let control
  try {control=JSON.parse(String(r.output?.[3] || ''))} catch {control=null}
  if(!control) return {status:null,signal:r.signal ?? null,expirado:true,error:r.error?.code ?? 'ETIMEDOUT',stdout:String(r.stdout || ''),stderr:String(r.stderr || '')}
  return {status:control.status ?? null,signal:control.signal ?? null,expirado:Boolean(control.expirado),error:control.error ?? null,stdout:String(r.stdout || ''),stderr:String(r.stderr || '')}
}

function runBoundedWorker(specJson) {
  let spec
  try {spec=JSON.parse(specJson)} catch {process.exit(2)}
  const report=result=>{try {writeSync(3,JSON.stringify(result))} catch {/* sin descriptor de control */}}
  const startedAt=Date.now()
  let child
  try {
    child=spawn(spec.file,spec.args || [],{cwd:spec.cwd,stdio:['ignore','pipe','pipe'],windowsHide:true,windowsVerbatimArguments:Boolean(spec.verbatim),detached:process.platform!=='win32'})
  } catch(error) {report({error:error?.code ?? 'EFAIL'});process.exit(0)}
  let finished=false,timer,rootExitedAt=0
  child.on('exit',()=>{rootExitedAt=Date.now()})
  const done=(result,code=0)=>{if(finished)return;finished=true;clearTimeout(timer);report(result);process.exit(code)}
  child.stdout.on('data',chunk=>process.stdout.write(chunk))
  child.stderr.on('data',chunk=>process.stderr.write(chunk))
  child.on('error',error=>done({error:error?.code ?? 'EFAIL'}))
  child.on('close',(status,signal)=>done({status,signal}))
  timer=setTimeout(()=>{
    if(finished) return
    finished=true
    terminateProcessTree(child.pid,TREE_KILL_TOTAL_MS,TREE_KILL_TOTAL_MS,{since:startedAt-100,until:rootExitedAt,rootAlive:!rootExitedAt})
    report({expirado:true});process.exit(0)
  },spec.timeoutMs)
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
  else if(args.length===2 && args[0]==='--run-bounded') runBoundedWorker(args[1])
  else {
    const valid=args.length===0 || args.length===2 && args[0]==='--project' && Boolean(args[1])
    console.log(JSON.stringify(valid ? queryCodexPlugin({cwd:args.length ? resolve(args[1]) : process.cwd()}) : unknown('invalid-arguments')))
  }
}
