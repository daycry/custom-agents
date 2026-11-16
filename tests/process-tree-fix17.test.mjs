import {test} from 'node:test'
import assert from 'node:assert/strict'
import {mkdtempSync,mkdirSync,writeFileSync,readFileSync,existsSync,rmSync,copyFileSync,linkSync,symlinkSync} from 'node:fs'
import {tmpdir} from 'node:os'
import {join,delimiter} from 'node:path'
import {execFileSync,spawn,spawnSync} from 'node:child_process'

// fix17 (T-23, intento 17): arbol de procesos de Windows con identidad (gaps 3, 5, 18 y 19), plazos coherentes de la consulta nativa (gaps 4 y 20) y un ejecutor con
// temporizador propio para la CLI del instalador. Los dos primeros bloques son de Windows (en Linux/macOS el arbol es el grupo de procesos).
const win=process.platform==='win32'
const mod=await import('../agent-kits/shared/codex-plugin-state.mjs')

const alive=pid=>{try{process.kill(pid,0);return true}catch(error){return error.code==='EPERM'}}
const sleep=ms=>new Promise(r=>setTimeout(r,ms))
const waitFor=async(cond,ms)=>{const limit=Date.now()+ms;while(Date.now()<limit){if(await cond())return true;await sleep(50)}return await cond()}
function removeTree(root) {
  const wait=new Int32Array(new SharedArrayBuffer(4))
  for(let attempt=0;;attempt++) {
    try {rmSync(root,{recursive:true,force:true});return}
    catch(error) {
      if(!['EPERM','EBUSY','ENOTEMPTY','EACCES'].includes(error.code) || attempt>=150) throw error
      Atomics.wait(wait,0,0,100)
    }
  }
}
const quiet=pid=>{try{process.kill(pid,'SIGKILL')}catch{/* ya no esta */}}

// Un padre P que lanza una victima V (un nodo dormido) y muere: V queda con `ParentProcessId` = pid de P, ya muerto. Es la forma de un proceso ANTERIOR que cuelga de un pid
// que Windows reasigna a otro proceso: el barrido por `ParentProcessId` lo confunde con un descendiente.
async function victimaHuerfana(root) {
  const flag=join(root,'v.pid')
  const padre=`const {spawn}=require('node:child_process');const v=spawn(process.execPath,['-e','setTimeout(()=>{},300000)'],{stdio:'ignore',detached:true});require('node:fs').writeFileSync(${JSON.stringify(flag)},String(v.pid));v.unref()`
  const p=spawn(process.execPath,['-e',padre],{stdio:'ignore'})
  const pid=p.pid
  await new Promise(r=>p.on('exit',r))
  assert.ok(await waitFor(()=>existsSync(flag),20000),'el padre escribio el pid de la victima')
  const v=Number(readFileSync(flag,'utf8'))
  assert.ok(alive(v),'la victima esta viva con el padre muerto')
  return {padre:pid,victima:v}
}

test('Windows (fix17, gap 3): un proceso ANTERIOR al lanzamiento que cuelga del pid del arbol NO es un descendiente y sobrevive (pid reutilizado)',{skip:!win && 'solo Windows reutiliza pids con padres huerfanos'},async()=>{
  const root=mkdtempSync(join(tmpdir(),'ca-reuse-'));let v
  try {
    const t0=Date.now()-500
    const o=await victimaHuerfana(root);v=o.victima
    await sleep(1500)
    const since=Date.now()      // el «lanzamiento» del arbol es POSTERIOR a la victima: el pid de P lo recibio otro proceso despues
    mod.terminateProcessTree(o.padre,20000,20000,{since,rootAlive:false})
    assert.equal(alive(v),true,'la victima es anterior al lanzamiento y no desciende de el: no se mata')
    // control positivo: con el lanzamiento ANTERIOR a la victima (es un huerfano legitimo del arbol que lanzamos), el mismo barrido la mata
    mod.terminateProcessTree(o.padre,20000,20000,{since:t0,rootAlive:false})
    assert.ok(await waitFor(()=>!alive(v),10000),'un huerfano legitimo (posterior al lanzamiento) si muere')
  } finally {if(v)quiet(v);removeTree(root)}
})

test('terminateProcessTree mata el arbol con la raiz VIVA (taskkill /T en Windows, grupo en POSIX) y confirma la muerte',async()=>{
  const root=mkdtempSync(join(tmpdir(),'ca-live-')),flag=join(root,'n.pid');let nieto
  try {
    const since=Date.now()-200
    const prog=`const {spawn}=require('node:child_process');const n=spawn(process.execPath,['-e','setTimeout(()=>{},300000)'],{stdio:'ignore'});require('node:fs').writeFileSync(${JSON.stringify(flag)},String(n.pid));setTimeout(()=>{},300000)`
    const raiz=spawn(process.execPath,['-e',prog],{stdio:'ignore',detached:!win})
    assert.ok(await waitFor(()=>existsSync(flag),20000));nieto=Number(readFileSync(flag,'utf8'))
    const t0=Date.now()
    mod.terminateProcessTree(raiz.pid,15000,15000,{since,rootAlive:true})
    assert.ok(Date.now()-t0<15000,'dentro del presupuesto')
    assert.ok(await waitFor(()=>!alive(raiz.pid) && !alive(nieto),8000),'raiz y nieto muertos')
  } finally {if(nieto)quiet(nieto);removeTree(root)}
})

test('terminateProcessTree no pasa de su presupuesto aunque el pid siga vivo (sin suelo de 1 s ni sondeo de 60 s)',async()=>{
  const dormido=spawn(process.execPath,['-e','setInterval(()=>{},1000)'],{stdio:'ignore'})
  try {
    // un «arbol» cuyo pid esta vivo pero es ANTERIOR al lanzamiento (`since` en el futuro): no se actua sobre el y el sondeo no puede esperarlo
    assert.ok(await waitFor(()=>alive(dormido.pid),5000))
    const t0=Date.now()
    mod.terminateProcessTree(dormido.pid,1500,1500,{since:Date.now()+3600_000,rootAlive:false})
    assert.equal(alive(dormido.pid),true,'un proceso anterior al lanzamiento no se mata')
    assert.ok(Date.now()-t0<6000,`espero ${Date.now()-t0} ms con un presupuesto de 1500`)
  } finally {quiet(dormido.pid)}
})

// --- plazos de la consulta nativa (gap 4)
test('queryPlan: el plazo de la consulta se recorta al tope exterior menos 2 s de reserva (sin suelo que pase del SIGKILL)',()=>{
  assert.equal(typeof mod.queryPlan,'function')
  const p=mod.queryPlan({launchedAt:0,readyAt:2000,limit:6000})
  assert.equal(p.outerKill,9000)
  assert.equal(p.deadline,7000,'listo + limite = 8000 pasa del tope menos la reserva (7000)')
  assert.equal(p.cleanupBy,8800)
  assert.equal(mod.queryPlan({launchedAt:0,readyAt:0,limit:6000}).deadline,6000,'sin retraso manda el limite')
  for(const ready of [0,500,1500,2500,4000,8000,9500]) {
    const q=mod.queryPlan({launchedAt:0,readyAt:ready,limit:6000})
    assert.ok(q.deadline<=q.outerKill-2000 && q.cleanupBy<q.outerKill,`ready=${ready}`)
  }
  for(const limit of [1000,3000,6000,20000,60000]) assert.ok(mod.queryPlan({launchedAt:0,readyAt:0,limit}).outerKill<=Math.max(limit+3000,7000))
})

test('Consulta nativa: codex colgado con un descendiente y un worker lento (+3 s) no deja huerfanos (gap 4)',async()=>{
  const root=mkdtempSync(join(tmpdir(),'ca-slowhang-')),bin=join(root,'bin'),flag=join(root,'nieto.pid');let nieto
  mkdirSync(bin)
  // Windows: el `codex.cmd` real de npm (cmd.exe -> node -> descendiente), la forma en que la lente D vio los huerfanos (con `codex.exe` copia de node no aparecen).
  const executable=join(bin,win?'codex.cmd':'codex')
  if(win) writeFileSync(executable,['@echo off','"'+process.execPath+'" "'+join(root,'plugin.mjs')+'" %*','exit /b %errorlevel%',''].join(String.fromCharCode(13,10))); else symlinkSync(process.execPath,executable)
  writeFileSync(join(root,'package.json'),'{"type":"module"}')
  writeFileSync(join(root,win?'plugin.mjs':'plugin'),`import {spawn} from 'node:child_process';import {writeFileSync} from 'node:fs'
const n=spawn(process.execPath,['-e','setTimeout(()=>{},300000)'],{stdio:'ignore'});writeFileSync(${JSON.stringify(flag)},String(n.pid));writeFileSync(${JSON.stringify(flag+'.codex')},String(process.pid));setInterval(()=>{},1000)`)
  const preload=join(root,'slow-worker.cjs')
  writeFileSync(preload,"if(process.argv.includes('--query-worker'))Atomics.wait(new Int32Array(new SharedArrayBuffer(4)),0,0,3000)")
  const env={}
  for(const key of ['SystemRoot','WINDIR','COMSPEC','PATHEXT','NODE_V8_COVERAGE'])if(process.env[key])env[key]=process.env[key]
  Object.assign(env,{HOME:root,USERPROFILE:root,CODEX_HOME:join(root,'.codex'),NODE_OPTIONS:'--require '+JSON.stringify(preload.split(String.fromCharCode(92)).join('/')),
    PATH:[bin,win?join(process.env.SystemRoot,'System32'):'/usr/bin:/bin'].join(delimiter)})
  try {
    const t0=Date.now()
    const state=mod.queryCodexPlugin({cwd:root,runner:(args,options)=>mod.runCodexQuery(args,{...options,env})})
    assert.equal(state.state,'unknown');assert.equal(state.reason,'cli-timeout')
    assert.ok(Date.now()-t0<10000,'dentro de los 10 s que impone /doctor')
    assert.ok(existsSync(flag),'el fixture lanzo su descendiente');nieto=Number(readFileSync(flag,'utf8'))
    assert.ok(await waitFor(()=>!alive(nieto),3000),'el descendiente de codex sigue vivo: el SIGKILL exterior llego a mitad de la limpieza')
  } finally {if(nieto)quiet(nieto);if(existsSync(flag+'.codex'))quiet(Number(readFileSync(flag+'.codex','utf8')));try{removeTree(root)}catch{/* un resto de la prueba retiene el directorio */}}
})

// --- ejecutor con temporizador propio (gap 5): el dueño del plazo mata el arbol con la raiz viva
test('runBounded: un comando colgado con un descendiente expira, mata el arbol con la raiz viva y deja 0 huerfanos',async()=>{
  assert.equal(typeof mod.runBounded,'function')
  const root=mkdtempSync(join(tmpdir(),'ca-bounded-')),flag=join(root,'nieto.pid');let nieto
  try {
    const prog=`const {spawn}=require('node:child_process');const n=spawn(process.execPath,['-e','setTimeout(()=>{},300000)'],{stdio:'ignore'});require('node:fs').writeFileSync(${JSON.stringify(flag)},String(n.pid));console.log('hola');setTimeout(()=>{},300000)`
    const t0=Date.now()
    const r=mod.runBounded({file:process.execPath,args:['-e',prog],timeoutMs:4000})
    assert.equal(r.expirado,true,'expiro');assert.ok(Date.now()-t0<40000)
    assert.ok(existsSync(flag),'el fixture lanzo su descendiente');nieto=Number(readFileSync(flag,'utf8'))
    assert.ok(await waitFor(()=>!alive(nieto),5000),'el descendiente quedo vivo')
  } finally {if(nieto)quiet(nieto);removeTree(root)}
})

test('runBounded: devuelve stdout, stderr y el codigo de salida de un comando que termina',()=>{
  const ok=mod.runBounded({file:process.execPath,args:['-e',"console.log('salida');console.error('aviso')"],timeoutMs:60000})
  assert.equal(ok.expirado,false);assert.equal(ok.status,0);assert.match(ok.stdout,/salida/);assert.match(ok.stderr,/aviso/)
  const mal=mod.runBounded({file:process.execPath,args:['-e','process.exit(7)'],timeoutMs:60000})
  assert.equal(mal.expirado,false);assert.equal(mal.status,7)
  const noEsta=mod.runBounded({file:join(tmpdir(),'no-existe-ca-fix17'),args:[],timeoutMs:60000})
  assert.equal(noEsta.expirado,false);assert.notEqual(noEsta.status,0)
})
