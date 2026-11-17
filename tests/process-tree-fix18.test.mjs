import {test} from 'node:test'
import assert from 'node:assert/strict'
import {mkdtempSync,mkdirSync,writeFileSync,readFileSync,existsSync,rmSync,symlinkSync} from 'node:fs'
import {tmpdir} from 'node:os'
import {join,delimiter,dirname} from 'node:path'
import {spawn,spawnSync} from 'node:child_process'
import {fileURLToPath,pathToFileURL} from 'node:url'

// fix18 (T-23, intento 18): el arbol de procesos de Windows ACTUA en produccion (gap 3), con la raiz viva no se espera al barrido, la identidad se comprueba al matar y las sondas
// `--version` del instalador no arrancan un worker de node (gap 15). Los bloques del arbol son de Windows.
const win=process.platform==='win32'
const AQUI=dirname(fileURLToPath(import.meta.url))
const MODULO=join(AQUI,'..','agent-kits','shared','codex-plugin-state.mjs')
const mod=await import(pathToFileURL(MODULO).href)
const alive=pid=>{try{process.kill(pid,0);return true}catch(error){return error.code==='EPERM'}}
const sleep=ms=>new Promise(r=>setTimeout(r,ms))
const waitFor=async(cond,ms)=>{const limit=Date.now()+ms;while(Date.now()<limit){if(await cond())return true;await sleep(50)}return await cond()}
const quiet=pid=>{try{process.kill(pid,'SIGKILL')}catch{/* ya no esta */}}
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

// --- gap 3: el barrido de respaldo sobrevive al worker
test('Windows (fix18, gap 3): el barrido con la raiz MUERTA sobrevive al worker que sale y mata al descendiente huerfano',{skip:!win && 'el barrido CIM es de Windows'},async()=>{
  const root=mkdtempSync(join(tmpdir(),'ca-sweep18-')),flag=join(root,'n.pid');let nieto,raiz
  try {
    const since=Date.now()-200
    // raiz: lanza un descendiente (que sale del job con `detached`) y muere; es el caso del `codex.cmd` que termina dejando un hijo con stdout abierto.
    const prog=`const {spawn}=require('node:child_process');const n=spawn(process.execPath,['-e','setTimeout(()=>{},300000)'],{stdio:'ignore',detached:true});require('node:fs').writeFileSync(${JSON.stringify(flag)},String(n.pid));n.unref()`
    raiz=spawn(process.execPath,['-e',prog],{stdio:'ignore'})
    const murio=new Promise(r=>raiz.on('exit',r));await murio
    assert.ok(await waitFor(()=>existsSync(flag),20000));nieto=Number(readFileSync(flag,'utf8'))
    assert.ok(alive(nieto),'el descendiente esta vivo con la raiz muerta')
    // el «worker»: llama a terminateProcessTree con un presupuesto MENOR que el barrido (CIM: 1-4 s con carga) y sale, como `queryWorker`/`runBoundedWorker` al agotar su plazo.
    const worker=`const m=await import(${JSON.stringify(pathToFileURL(MODULO).href)});m.terminateProcessTree(${raiz.pid},300,300,{since:${since},until:${Date.now()},rootAlive:false});process.exit(0)`
    const w=spawnSync(process.execPath,['--input-type=module','-e',worker],{stdio:'ignore',timeout:60000})
    assert.equal(w.status,0)
    assert.ok(await waitFor(()=>!alive(nieto),30000),'el descendiente huerfano sigue vivo: el barrido murio con el worker (job de libuv)')
  } finally {if(nieto)quiet(nieto);removeTree(root)}
})

test('Windows (fix18, gap 3): el barrido se lanza FUERA del job del worker (cmd /c start /b, detached) con -EncodedCommand y el pid ajeno no se mata',{skip:!win && 'solo Windows'},()=>{
  const llamadas=[]
  const fake=(file,args,options)=>{
    const h={pid:900000+llamadas.length,on(){return h},unref(){},stdout:null}
    llamadas.push({file:String(file),args,options});return h
  }
  mod.terminateProcessTree(4242,500,500,{since:1000,until:2000,rootAlive:false,deps:{spawn:fake,alive:()=>false}})
  const barrido=llamadas.find(l=>/powershell|cmd/i.test(l.file))
  assert.ok(barrido,'se lanza el barrido')
  assert.equal(barrido.options.detached,true,'el barrido debe salir del job del worker')
  const linea=[barrido.file,...(barrido.args||[])].join(' ')
  assert.match(linea,/start/i,'con DETACHED_PROCESS puro PowerShell sale sin ejecutar nada (medido): se lanza con `cmd /c start /b`')
  assert.match(linea,/-EncodedCommand/i,'sin interpolar texto en una linea de cmd')
  assert.doesNotMatch(linea,/DETACHED_PROCESS/)
})

test('Windows (fix18, gap 3): con la raiz VIVA se confia en taskkill /T y NO se espera al barrido',{skip:!win && 'solo Windows'},()=>{
  const llamadas=[]
  const t0=Date.now()
  const fake=(file,args,options)=>{
    const h={pid:910000+llamadas.length,on(){return h},unref(){}}
    llamadas.push({file:String(file),args,options,en:Date.now()-t0});return h
  }
  // taskkill «termina» enseguida; el barrido «sigue vivo» (alive devuelve true para el): si se esperase al barrido, se agotaria el presupuesto de 6 s
  const vivo=pid=>pid===777 || (pid>=910000 && pid!==910000)
  mod.terminateProcessTree(777,6000,6000,{since:1,rootAlive:true,deps:{spawn:fake,alive:vivo}})
  assert.ok(llamadas.some(l=>/taskkill/i.test(l.file)),'taskkill /T primero')
  assert.ok(Date.now()-t0<2500,`con la raiz viva se espero al barrido ${Date.now()-t0} ms`)
})

test('el barrido comprueba la identidad (pid + fecha de creacion) en la MISMA orden, justo antes de cada Stop-Process',()=>{
  const script=mod.sweepScript(123,1000,2000,false)
  const idx=script.indexOf('Stop-Process')
  const antes=script.slice(Math.max(0,idx-300),idx)
  assert.match(antes,/Get-Process/,'antes de cada Stop-Process se vuelve a leer el proceso')
  assert.match(antes,/StartTime/,'y se compara su fecha de creacion con la de la foto')
})

test('todos los llamadores de terminateProcessTree pasan since/until y rootAlive por el estado real de la raiz',()=>{
  const fuente=readFileSync(MODULO,'utf8')
  const llamadas=fuente.split(String.fromCharCode(10)).filter(l=>l.includes('terminateProcessTree(') && !l.includes('export function') && !l.trim().startsWith('//'))
  assert.ok(llamadas.length>=2,'queryWorker y runBoundedWorker')
  for(const l of llamadas) {
    assert.match(l,/since/,l);assert.match(l,/until/,l);assert.match(l,/rootAlive/,l)
    assert.doesNotMatch(l,/rootAlive:true\}/,'rootAlive depende de si la raiz ya salio, no es una constante: '+l)
  }
})

// --- gap 15: las sondas del instalador no arrancan un worker
test('Windows (fix18, gap 15): `correr(cmd, ["--version"])` no arranca un worker de node; una orden larga sigue con su worker',{skip:!win && 'solo Windows usa el worker'},async()=>{
  const root=mkdtempSync(join(tmpdir(),'ca-probe18-')),bin=join(root,'bin'),log=join(root,'arranques.txt')
  mkdirSync(bin)
  writeFileSync(join(bin,'sonda-ca18.cmd'),'@echo off\r\necho sonda 1.2.3\r\n')
  const preload=join(root,'registra.cjs')
  writeFileSync(preload,`require('node:fs').appendFileSync(${JSON.stringify(log.split('\\').join('/'))},process.argv.slice(1).join(' ')+'\\n')`)
  const script=join(root,'prueba.mjs')
  writeFileSync(script,`import {correr} from ${JSON.stringify(pathToFileURL(join(AQUI,'..','install','install.mjs')).href)}
process.env.PATH=${JSON.stringify(bin)}+${JSON.stringify(delimiter)}+${JSON.stringify(join(process.env.SystemRoot,'System32'))}
console.log(correr('sonda-ca18',['--version'],${JSON.stringify(root)}).trim())
console.log(correr('sonda-ca18',['otra','cosa'],${JSON.stringify(root)}).trim())`)
  try {
    const r=spawnSync(process.execPath,[script],{encoding:'utf8',timeout:120000,env:{...process.env,NODE_OPTIONS:'--require '+JSON.stringify(preload.split('\\').join('/'))}})
    assert.equal(r.status,0,r.stderr)
    assert.equal(r.stdout.trim().split(/\r?\n/).length,2)
    const arranques=readFileSync(log,'utf8').split(/\r?\n/).filter(l=>/--run-bounded/.test(l))
    assert.equal(arranques.length,1,`la sonda --version no debe arrancar un worker; solo la orden larga (arranques: ${JSON.stringify(arranques.map(l=>l.slice(0,60)))})`)
  } finally {removeTree(root)}
})

// --- gap 14 (anadido tras el RED, k11): la ruta REAL de `/doctor` (`node codex-plugin-state.mjs --project <dir>` con el plazo de 10 s de doctor.py) con un worker +2 s lento (el diseno de fix17 pedia +2 s
// y solo se midio a mano con +1 s): `codex.cmd` colgado con un descendiente, 0 huerfanos y dentro de los 10 s.
test('/doctor (fix18, gap 14): el helper de la consulta nativa con un worker +2 s lento termina en 10 s y no deja huerfanos',async()=>{
  const root=mkdtempSync(join(tmpdir(),'ca-doctor18-')),bin=join(root,'bin'),flag=join(root,'nieto.pid');let nieto
  mkdirSync(bin)
  const executable=join(bin,win?'codex.cmd':'codex')
  if(win) writeFileSync(executable,['@echo off','"'+process.execPath+'" "'+join(root,'plugin.mjs')+'" %*','exit /b %errorlevel%',''].join(String.fromCharCode(13,10))); else symlinkSync(process.execPath,executable)
  writeFileSync(join(root,'package.json'),'{"type":"module"}')
  writeFileSync(join(root,win?'plugin.mjs':'plugin'),`import {spawn} from 'node:child_process';import {writeFileSync} from 'node:fs'
const n=spawn(process.execPath,['-e','setTimeout(()=>{},300000)'],{stdio:'ignore'});writeFileSync(${JSON.stringify(flag)},String(n.pid));writeFileSync(${JSON.stringify(flag+'.codex')},String(process.pid));setInterval(()=>{},1000)`)
  const preload=join(root,'slow-worker.cjs')
  writeFileSync(preload,"if(process.argv.includes('--query-worker'))Atomics.wait(new Int32Array(new SharedArrayBuffer(4)),0,0,2000)")
  const env={}
  for(const key of ['SystemRoot','WINDIR','COMSPEC','PATHEXT','NODE_V8_COVERAGE'])if(process.env[key])env[key]=process.env[key]
  Object.assign(env,{HOME:root,USERPROFILE:root,CODEX_HOME:join(root,'.codex'),NODE_OPTIONS:'--require '+JSON.stringify(preload.split(String.fromCharCode(92)).join('/')),
    PATH:[bin,win?join(process.env.SystemRoot,'System32'):'/usr/bin:/bin'].join(delimiter)})
  try {
    const t0=Date.now()
    const r=spawnSync(process.execPath,[MODULO,'--project',root],{cwd:root,env,encoding:'utf8',timeout:10000,killSignal:'SIGKILL'})
    assert.equal(r.error,undefined,'doctor.py corta a los 10 s: el helper no puede pasar de ahi')
    assert.ok(Date.now()-t0<10000,`${Date.now()-t0} ms`)
    assert.match(r.stdout,/cli-timeout/)
    assert.ok(existsSync(flag),'el fixture lanzo su descendiente');nieto=Number(readFileSync(flag,'utf8'))
    assert.ok(await waitFor(()=>!alive(nieto),8000),'el descendiente de codex sigue vivo')
  } finally {if(nieto)quiet(nieto);if(existsSync(flag+'.codex'))quiet(Number(readFileSync(flag+'.codex','utf8')));try{removeTree(root)}catch{/* un resto retiene el directorio */}}
})

// --- gap 3 (identidad de la raiz, anadido tras el RED, k12): un pid REUTILIZADO. La raiz salio en `until`; un proceso AJENO que recibio su pid despues (con su propio hijo) NO es la raiz ni desciende
// de ella: con `rootAlive:false` (lo que los llamadores deciden por el evento `exit` de su handle) ni el ni su hijo mueren.
test('Windows (fix18, gap 3): el proceso ajeno que reutiliza el pid de la raiz y su hijo sobreviven al barrido',{skip:!win && 'solo Windows reutiliza pids'},async()=>{
  const root=mkdtempSync(join(tmpdir(),'ca-reuse18-')),flag=join(root,'h.pid');let ajeno,hijo
  try {
    const since=Date.now()-3000,until=Date.now()-1000      // la raiz «salio» hace 1 s; el ajeno nace despues
    const prog=`const {spawn}=require('node:child_process');const h=spawn(process.execPath,['-e','setTimeout(()=>{},300000)'],{stdio:'ignore'});require('node:fs').writeFileSync(${JSON.stringify(flag)},String(h.pid));setTimeout(()=>{},300000)`
    ajeno=spawn(process.execPath,['-e',prog],{stdio:'ignore',detached:true})
    assert.ok(await waitFor(()=>existsSync(flag),20000));hijo=Number(readFileSync(flag,'utf8'))
    mod.terminateProcessTree(ajeno.pid,15000,15000,{since,until,rootAlive:false})
    await sleep(8000)       // el barrido corre fuera del job y sin que nadie lo espere: se le da tiempo de sobra (1-4 s con carga)
    assert.equal(alive(ajeno.pid),true,'el proceso ajeno que reutilizo el pid murio')
    assert.equal(alive(hijo),true,'el hijo del ajeno murio')
  } finally {if(hijo)quiet(hijo);if(ajeno?.pid)quiet(ajeno.pid);removeTree(root)}
})

// --- gap 14 (anadido tras el RED, k11): el arranque lento de node del PROPIO helper no se suma al tope exterior. doctor.py corta a los 10 s desde que lanza al helper; el tope de la consulta
// (limite + 3 s = 9 s) cuenta desde que el helper arranca el worker: con 1,5 s de arranque el total pasaba de 10 s (10,5 s sin el descuento; con el descuento, 9 s).
test('/doctor (fix18, gap 14): el arranque lento del helper se descuenta del plazo de la consulta y el total cabe en 10 s',async()=>{
  const root=mkdtempSync(join(tmpdir(),'ca-doctor18b-')),bin=join(root,'bin'),flag=join(root,'nieto.pid');let nieto
  mkdirSync(bin)
  const executable=join(bin,win?'codex.cmd':'codex')
  if(win) writeFileSync(executable,['@echo off','"'+process.execPath+'" "'+join(root,'plugin.mjs')+'" %*','exit /b %errorlevel%',''].join(String.fromCharCode(13,10))); else symlinkSync(process.execPath,executable)
  writeFileSync(join(root,'package.json'),'{"type":"module"}')
  writeFileSync(join(root,win?'plugin.mjs':'plugin'),`import {spawn} from 'node:child_process';import {writeFileSync} from 'node:fs'
const n=spawn(process.execPath,['-e','setTimeout(()=>{},300000)'],{stdio:'ignore'});writeFileSync(${JSON.stringify(flag)},String(n.pid));setInterval(()=>{},1000)`)
  const preload=join(root,'slow-helper.cjs')
  // el helper (no el CLI falso) tarda 1,5 s en arrancar Y su worker otros 2 s: el caso de la maquina saturada (sin el descuento el total pasaba de 10 s: 10,5 s)
  writeFileSync(preload,"if(String(process.argv[1]).endsWith('codex-plugin-state.mjs'))Atomics.wait(new Int32Array(new SharedArrayBuffer(4)),0,0,process.argv.includes('--query-worker') ? 2000 : 1500)")
  const env={}
  for(const key of ['SystemRoot','WINDIR','COMSPEC','PATHEXT','NODE_V8_COVERAGE'])if(process.env[key])env[key]=process.env[key]
  Object.assign(env,{HOME:root,USERPROFILE:root,CODEX_HOME:join(root,'.codex'),NODE_OPTIONS:'--require '+JSON.stringify(preload.split(String.fromCharCode(92)).join('/')),
    PATH:[bin,win?join(process.env.SystemRoot,'System32'):'/usr/bin:/bin'].join(delimiter)})
  try {
    const t0=Date.now()
    const r=spawnSync(process.execPath,[MODULO,'--project',root],{cwd:root,env,encoding:'utf8',timeout:10000,killSignal:'SIGKILL'})
    assert.equal(r.error,undefined,`el helper paso de los 10 s de doctor.py (${Date.now()-t0} ms)`)
    assert.match(r.stdout,/cli-timeout/)
    assert.ok(existsSync(flag));nieto=Number(readFileSync(flag,'utf8'))
    assert.ok(await waitFor(()=>!alive(nieto),8000),'el descendiente de codex sigue vivo')
  } finally {if(nieto)quiet(nieto);try{removeTree(root)}catch{/* un resto retiene el directorio */}}
})
