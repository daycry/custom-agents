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
// fix21: los barridos de respaldo (fix18) salen del job y nadie los espera; en Windows 11 26300 un barrido tarda 3-13 s (arranque de PowerShell + foto CIM), mas que el `sleep(5000)` de fix18, y su
// PowerShell compite con los tests de plazo de pared de despues («worker lento», /doctor). Para poder ESPERARLOS el test inyecta `deps.spawn` (el producto ya lo admite): recibe la orden `cmd /c start /b
// powershell -EncodedCommand <script>` y lanza ese mismo PowerShell con el mismo script como hijo directo, cuyo `exit` se espera. El sujeto de estos tests es el script de identidad (quien muere y quien
// no), no la forma de lanzarlo (la cubren los tests de fix18).
function barridoEsperable() {
  const salidas=[]
  const spawnObservable=(file,args,options)=>{
    const m=/-EncodedCommand (\S+)/.exec(String(args[args.length-1]))
    const hijo=spawn(join(process.env.SystemRoot,'System32','WindowsPowerShell','v1.0','powershell.exe'),['-NoProfile','-NonInteractive','-EncodedCommand',m[1]],{stdio:'ignore',windowsHide:true})
    hijo.unref=()=>hijo   // el producto lo desreferencia; aqui se le ESPERA y el bucle de eventos no puede cerrarse antes
    salidas.push(new Promise(r=>{hijo.on('exit',r);hijo.on('error',r)}))
    return hijo
  }
  return {deps:{spawn:spawnObservable},acabado:()=>Promise.all(salidas)}
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

test('Windows (fix17, gap 3): un proceso ANTERIOR al lanzamiento que cuelga del pid del arbol NO es un descendiente y sobrevive (pid reutilizado)',{skip:!win && 'solo Windows reutiliza pids con padres huerfanos'},async t=>{
  const root=mkdtempSync(join(tmpdir(),'ca-reuse-'));let v
  try {
    const t0=Date.now()-500
    const o=await victimaHuerfana(root);v=o.victima
    await sleep(1500)
    const since=Date.now()      // el «lanzamiento» del arbol es POSTERIOR a la victima: el pid de P lo recibio otro proceso despues
    const b1=barridoEsperable()
    mod.terminateProcessTree(o.padre,20000,20000,{since,rootAlive:false,deps:b1.deps})
    // fix21: el barrido es asincrono (fix18): comprobar `alive` al instante pasaria aunque el barrido matase a la victima un segundo despues (mutante: la comparacion de fechas invertida seguia en verde).
    // Se espera a que ACABE el barrido y solo entonces se afirma que la victima anterior sigue viva.
    await b1.acabado()
    assert.equal(alive(v),true,'la victima es anterior al lanzamiento y no desciende de el: no se mata')
    // control positivo: con el lanzamiento ANTERIOR a la victima (es un huerfano legitimo del arbol que lanzamos), el mismo barrido la mata
    // fix21: con la raiz muerta el barrido NO se espera (fix18: sale del job del worker y se lanza con `cmd /c start /b`), asi que la muerte llega cuando acaba SU PowerShell: arranque (~1 s) + foto CIM
    // (1-3 s; 4-11 s medidos con la maquina ocupada y dos barridos a la vez, como aqui) y, en Windows 11 26300, hasta ~7 s con la maquina «en reposo». La latencia del barrido no es el sujeto de este
    // test (el sujeto es la IDENTIDAD: quien muere y quien no): el plazo es holgado y se anota lo medido.
    const lanzado=Date.now(),b2=barridoEsperable()
    mod.terminateProcessTree(o.padre,20000,20000,{since:t0,rootAlive:false,deps:b2.deps})
    const murio=await waitFor(()=>!alive(v),60000)
    t.diagnostic(`el huerfano legitimo murio a los ${Date.now()-lanzado} ms del lanzamiento del barrido`)
    assert.ok(murio,'un huerfano legitimo (posterior al lanzamiento) si muere')
    await b2.acabado()
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
    const b3=barridoEsperable()
    mod.terminateProcessTree(dormido.pid,1500,1500,{since:Date.now()+3600_000,rootAlive:false,deps:b3.deps})
    assert.equal(alive(dormido.pid),true,'un proceso anterior al lanzamiento no se mata')
    assert.ok(Date.now()-t0<6000,`espero ${Date.now()-t0} ms con un presupuesto de 1500`)
    // fix18: el barrido de respaldo sale del job del worker y NO se espera: este test lo lanza con la raiz «muerta» y, si acabase aqui, su PowerShell CIM (1-4 s de CPU) competiria con el fixture
    // del test siguiente (el de «worker lento», que tiene un margen de ~3 s para arrancar `codex.cmd`). Se le da tiempo de terminar.
    await b3.acabado()
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

// fix18 (T-23, intento 18): la prueba de /doctor vive AQUI, en el mismo fichero que las de «worker lento» de fix16/fix17: node ejecuta los ficheros de test en paralelo y estas miden el plazo de pared de la consulta nativa; en ficheros distintos competian entre si (y con la maquina) y daban rojo intermitente.
import {fileURLToPath} from 'node:url'
import {dirname} from 'node:path'
const MODULO=join(dirname(fileURLToPath(import.meta.url)),'..','agent-kits','shared','codex-plugin-state.mjs')

// --- gap 14 (anadido tras el RED, k11): el arranque lento de node del PROPIO helper no se suma al tope exterior. doctor.py corta a los 10 s desde que lanza al helper; el tope de la consulta
// (limite + 3 s = 9 s) cuenta desde que el helper arranca el worker: con 1,5 s de arranque el total pasaba de 10 s (10,5 s sin el descuento; con el descuento, 9 s).
test('/doctor (fix18, gap 14): el arranque lento del helper se descuenta del plazo de la consulta y el total cabe en 10 s',async t=>{
  const root=mkdtempSync(join(tmpdir(),'ca-doctor18b-')),bin=join(root,'bin'),flag=join(root,'nieto.pid');let nieto
  mkdirSync(bin)
  const executable=join(bin,win?'codex.cmd':'codex')
  if(win) writeFileSync(executable,['@echo off','"'+process.execPath+'" "'+join(root,'plugin.mjs')+'" %*','exit /b %errorlevel%',''].join(String.fromCharCode(13,10))); else symlinkSync(process.execPath,executable)
  writeFileSync(join(root,'package.json'),'{"type":"module"}')
  writeFileSync(join(root,win?'plugin.mjs':'plugin'),`import {spawn} from 'node:child_process';import {writeFileSync} from 'node:fs'
const n=spawn(process.execPath,['-e','setTimeout(()=>{},300000)'],{stdio:'ignore'});writeFileSync(${JSON.stringify(flag)},String(n.pid));setInterval(()=>{},1000)`)
  const preload=join(root,'slow-helper.cjs')
  // el helper (no el CLI falso) tarda 2,5 s en arrancar Y su worker otros 2 s: el caso de la maquina saturada. T-06 (2026-11-19): con 1,5 s el mutante «sin descuento» (tope 9 s)
  // acababa en 9,8 s y solo fallaba 1 de 3; con 2,5 s pasa de 10 s, y con el descuento el total no depende del arranque (tope 8 s menos el arranque: ~7,5-8,7 s medidos).
  writeFileSync(preload,"if(String(process.argv[1]).endsWith('codex-plugin-state.mjs'))Atomics.wait(new Int32Array(new SharedArrayBuffer(4)),0,0,process.argv.includes('--query-worker') ? 2000 : 2500)")
  const env={}
  for(const key of ['SystemRoot','WINDIR','COMSPEC','PATHEXT','NODE_V8_COVERAGE'])if(process.env[key])env[key]=process.env[key]
  Object.assign(env,{HOME:root,USERPROFILE:root,CODEX_HOME:join(root,'.codex'),NODE_OPTIONS:'--require '+JSON.stringify(preload.split(String.fromCharCode(92)).join('/')),
    PATH:[bin,win?join(process.env.SystemRoot,'System32'):'/usr/bin:/bin'].join(delimiter)})
  try {
    const t0=Date.now()
    const r=spawnSync(process.execPath,[MODULO,'--project',root],{cwd:root,env,encoding:'utf8',timeout:10000,killSignal:'SIGKILL'})
    assert.equal(r.error,undefined,`el helper paso de los 10 s de doctor.py (${Date.now()-t0} ms)`)
    assert.match(r.stdout,/cli-timeout/)
    t.diagnostic(`total ${Date.now()-t0} ms; flag ${existsSync(flag)?'si':'NO'}; stdout ${String(r.stdout).slice(0,120)}`)
    // T-06 (2026-11-19, medido: 2 de 12 en reposo): con 1,5 s + 2 s de arranque simulado a la consulta le quedan ~2,1 s por diseno (el tope de 10 s es fijo) y a veces el codex falso ni
    // llega a arrancar: el sujeto (el total cabe en 10 s) se cumple igual. Sin marca no se da por bueno en vacio: si codex arrancara DESPUES habria sobrevivido a la limpieza (huerfano).
    if(!existsSync(flag)) {
      await new Promise(done=>setTimeout(done,3000))
      assert.ok(!existsSync(flag),'codex arranco despues de la consulta: sobrevivio a la limpieza del arbol')
      t.diagnostic('codex no llego a arrancar dentro del plazo (maquina lenta): sin descendiente que comprobar')
      return
    }
    nieto=Number(readFileSync(flag,'utf8'))
    assert.ok(await waitFor(()=>!alive(nieto),8000),'el descendiente de codex sigue vivo')
  } finally {if(nieto)quiet(nieto);try{removeTree(root)}catch{/* un resto retiene el directorio */}}
})

