import {test} from 'node:test'
import assert from 'node:assert/strict'
import {mkdtempSync,mkdirSync,writeFileSync,readFileSync,rmSync,copyFileSync,linkSync,symlinkSync} from 'node:fs'
import {tmpdir} from 'node:os'
import {join,delimiter} from 'node:path'
import {execFileSync,spawnSync} from 'node:child_process'
import {fileURLToPath} from 'node:url'

// fix16 (gap 20): en Windows el `codex.exe` copiado tarda de 4,1 a 15,7 s en arrancar la primera vez (Defender); un enlace duro, 0,9-1,0 s (copia solo de reserva). El
// primer arranque se hace ANTES de medir plazos. El borrado reintenta EPERM/EBUSY (node 23.8 no reintenta EPERM con `maxRetries`).
function nativeFixture(root,executable,env) {
  if(process.platform==='win32') {
    try {linkSync(process.execPath,executable)} catch {copyFileSync(process.execPath,executable)}
    execFileSync(executable,['--version'],{cwd:root,env,encoding:'utf8',timeout:60000})
  } else symlinkSync(process.execPath,executable)
}

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

test('Codex state: synchronous native spawn cannot renew an expired query deadline',()=>{
  const root=mkdtempSync(join(tmpdir(),'ca-deadline-owned-')),bin=join(root,'bin')
  mkdirSync(bin)
  const executable=join(bin,process.platform==='win32'?'codex.exe':'codex')
  const env={}
  for(const key of ['SystemRoot','WINDIR','COMSPEC','PATHEXT','NODE_V8_COVERAGE'])if(process.env[key])env[key]=process.env[key]
  Object.assign(env,{HOME:root,USERPROFILE:root,CODEX_HOME:join(root,'.codex'),PATH:[bin,process.platform==='win32'?join(process.env.SystemRoot,'System32'):'/usr/bin:/bin'].join(delimiter)})
  nativeFixture(root,executable,env)
  writeFileSync(join(root,'package.json'),'{"type":"module"}')
  writeFileSync(join(root,'plugin'),'console.log(JSON.stringify({installed:[],available:[]}))')
  const marker=join(root,'spawn.json'),preload=join(root,'spawn-delay.cjs')
  writeFileSync(preload,`const cp=require('node:child_process'),fs=require('node:fs');
const original=cp.spawn;
process.argv[3]=String(Date.now()+500);
cp.spawn=(...args)=>{const child=original(...args);const before=Date.now();Atomics.wait(new Int32Array(new SharedArrayBuffer(4)),0,0,1000);fs.writeFileSync(${JSON.stringify(marker)},JSON.stringify({before,after:Date.now(),child:child.pid,deadline:Number(process.argv[3])}));return child};
require('node:module').syncBuiltinESMExports();`)
  const helper=fileURLToPath(new URL('../agent-kits/shared/codex-plugin-state.mjs',import.meta.url))
  try{
    const result=spawnSync(process.execPath,['--require',preload,helper,'--query-worker',String(Date.now()+20000)],{cwd:root,env,encoding:'utf8',timeout:40000})   // fix16: el arbol se mata y se CONFIRMA (hasta 8 s) antes de salir
    const observed=JSON.parse(readFileSync(marker,'utf8'))
    assert.ok(Number.isInteger(observed.child) && observed.child>0,'fixture must launch an actual native process')
    assert.ok(observed.after>observed.deadline,'fixture must return from native spawn after the original deadline')
    assert.equal(result.error,undefined)
    assert.equal(result.status,124,'late native output must remain a timeout, without granting a new timer budget')
    assert.equal(result.stdout,'','expired native output must not reach the consumer')
    assert.throws(()=>process.kill(observed.child,0),'expired native process must be gone before worker exit')
  }finally{removeTree(root)}
})

// fix16 (gap 21): el plazo del producto (3 s) corre desde que el WORKER esta listo, no desde antes de lanzarlo: un arranque lento del worker (carga de CPU)
// ya no consume el plazo de codex. El worker arranca 2,5 s tarde (preload solo para `--query-worker`) y codex tarda 0,6 s: con el plazo fijado antes
// del lanzamiento (3 s desde el padre) le quedan 0,5 s a codex y da `cli-timeout`.
test('Codex state: a slow worker start does not consume the native query budget (fix16, gap 21)',async()=>{
  const {queryCodexPlugin,runCodexQuery}=await import('../agent-kits/shared/codex-plugin-state.mjs')
  const root=mkdtempSync(join(tmpdir(),'ca-deadline-ready-')),bin=join(root,'bin')
  mkdirSync(bin)
  const executable=join(bin,process.platform==='win32'?'codex.exe':'codex')
  writeFileSync(join(root,'package.json'),'{"type":"module"}')
  writeFileSync(join(root,'plugin'),'await new Promise(r=>setTimeout(r,600));console.log(JSON.stringify({installed:[{pluginId:"custom-agents@daycry",installed:true,enabled:true,version:"1.22.0"}],available:[]}))')
  const preload=join(root,'slow-worker.cjs')
  writeFileSync(preload,"if(process.argv.includes('--query-worker'))Atomics.wait(new Int32Array(new SharedArrayBuffer(4)),0,0,2500)")
  const env={}
  for(const key of ['SystemRoot','WINDIR','COMSPEC','PATHEXT','NODE_V8_COVERAGE'])if(process.env[key])env[key]=process.env[key]
  Object.assign(env,{HOME:root,USERPROFILE:root,CODEX_HOME:join(root,'.codex'),NODE_OPTIONS:'--require '+JSON.stringify(preload.split(String.fromCharCode(92)).join('/')),
    PATH:[bin,process.platform==='win32'?join(process.env.SystemRoot,'System32'):'/usr/bin:/bin'].join(delimiter)})
  nativeFixture(root,executable,(({NODE_OPTIONS,...rest})=>rest)(env))
  try{
    // fix17 (gap 4): el plazo se recorta al tope exterior menos 2 s de reserva (`queryPlan`): con limite 3 s el tope exterior es de 7 s y quedan 2,5 s tras el worker lento, que con la
    // maquina saturada no alcanzan para arrancar el node de codex (mediana 3,7 s). Con el plazo por defecto (6 s) la consulta llega hasta los 7 s desde el lanzamiento.
    const state=queryCodexPlugin({cwd:root,timeout:6000,runner:(args,options)=>runCodexQuery(args,{...options,env})})
    assert.equal(state.reason,null,'the worker start must not consume the budget of the native query')
    assert.equal(state.state,'installed')
  }finally{removeTree(root)}
})
