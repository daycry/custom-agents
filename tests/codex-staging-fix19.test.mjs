// fix19 (plugin-audit-2, T-23): el home aislado del instalador (scope project) ya no enlaza la cache real con una
// junction: en Windows con KB5135385 el `codex` nativo no puede crear directorios a traves de ella
// (ver mkdir-p-fix19.test.mjs). La entrada instalada se promueve a la cache real solo si el add tiene exito.
import {test} from 'node:test'
import assert from 'node:assert/strict'
import {mkdtempSync,mkdirSync,writeFileSync,readFileSync,existsSync,rmSync,symlinkSync,lstatSync,readdirSync,realpathSync} from 'node:fs'
import {tmpdir} from 'node:os'
import {spawnSync} from 'node:child_process'
import {join} from 'node:path'
import * as installer from '../install/install.mjs'

const tipo=process.platform==='win32'?'junction':'dir'
const conRaiz=fn=>{const raiz=mkdtempSync(join(tmpdir(),'ca-fix19-'));try{return fn(raiz)}finally{rmSync(raiz,{recursive:true,force:true})}}

test('instalarCodexNativo: el home aislado NO enlaza la cache (el codex nativo crea directorios en ella)',()=>conRaiz(raiz=>{
  const home=join(raiz,'codex'),dir=join(raiz,'project'),cache=join(home,'plugins/cache/daycry')
  mkdirSync(dir);mkdirSync(join(cache,'other/1.0.0'),{recursive:true});writeFileSync(join(cache,'other/1.0.0/keep.txt'),'keep')
  let enlaces=null
  const runner=(args,o)=>{
    const staged=o.env.CODEX_HOME,ns=join(staged,'plugins/cache/daycry')
    if(args[1]==='marketplace')return 'ok'
    enlaces=[join(staged,'plugins'),join(staged,'plugins/cache'),ns].map(p=>existsSync(p)&&lstatSync(p).isSymbolicLink())
    const installed=join(ns,'custom-agents/1.22.0')
    mkdirSync(join(installed,'.codex-plugin'),{recursive:true})   // lo que hace el codex nativo: crear directorios
    writeFileSync(join(installed,'.codex-plugin/plugin.json'),JSON.stringify({name:'custom-agents',version:'1.22.0'}))
    return JSON.stringify({pluginId:'custom-agents@daycry',version:'1.22.0',installedPath:installed})
  }
  const r=installer.instalarCodexNativo({home,dir,scope:'project',version:'1.22.0',runner,tempRoot:raiz})
  assert.deepEqual(enlaces,[false,false,false])
  assert.ok(existsSync(join(cache,'custom-agents/1.22.0/.codex-plugin/plugin.json')),'la entrada se promueve a la cache real')
  assert.equal(readFileSync(join(cache,'other/1.0.0/keep.txt'),'utf8'),'keep')
  assert.equal(realpathSync(r.installedPath),realpathSync(join(cache,'custom-agents/1.22.0')))
  assert.deepEqual(readdirSync(raiz).filter(n=>n.startsWith('custom-agents-codex-')),[],'el home aislado se limpia')
}))

test('instalarCodexNativo: si el codex nativo falla, la cache real queda intacta',()=>conRaiz(raiz=>{
  const home=join(raiz,'codex'),dir=join(raiz,'project'),cache=join(home,'plugins/cache/daycry')
  mkdirSync(dir);mkdirSync(join(cache,'custom-agents/1.0.0'),{recursive:true});writeFileSync(join(cache,'custom-agents/1.0.0/a'),'old')
  mkdirSync(join(cache,'custom-agents/1.0.0/.codex-plugin'))
  writeFileSync(join(cache,'custom-agents/1.0.0/.codex-plugin/plugin.json'),JSON.stringify({name:'custom-agents',repository:JSON.parse(readFileSync(new URL('../.codex-plugin/plugin.json',import.meta.url),'utf8')).repository}))
  const runner=args=>{if(args[1]==='marketplace')return 'ok';throw new Error('native add rejected')}
  assert.throws(()=>installer.instalarCodexNativo({home,dir,scope:'project',version:'1.22.0',runner,tempRoot:raiz}),/rejected/)
  assert.deepEqual(readdirSync(join(cache,'custom-agents')),['1.0.0'])
  assert.equal(readFileSync(join(cache,'custom-agents/1.0.0/a'),'utf8'),'old')
}))

test('instalarCodexNativo: un tempRoot que cruza un enlace del usuario no impide el aislamiento',{timeout:60000},()=>conRaiz(raiz=>{
  const real=join(raiz,'tmp-real');mkdirSync(real);const enlace=join(raiz,'tmp-link');symlinkSync(real,enlace,tipo)
  const home=join(raiz,'codex'),dir=join(raiz,'project');mkdirSync(dir)
  // En un proceso hijo con plazo: en Windows+KB5135385 el codigo viejo se queda colgado de forma SINCRONA.
  const guion=`
import {mkdirSync,writeFileSync} from 'node:fs'
import {join} from 'node:path'
import * as installer from ${JSON.stringify(new URL('../install/install.mjs',import.meta.url).href)}
const [home,dir,tempRoot]=process.argv.slice(1)
const runner=(args,o)=>{
  if(args[1]==='marketplace')return 'ok'
  const installed=join(o.env.CODEX_HOME,'plugins/cache/daycry/custom-agents/1.22.0')
  mkdirSync(join(installed,'.codex-plugin'),{recursive:true})
  writeFileSync(join(installed,'.codex-plugin/plugin.json'),JSON.stringify({name:'custom-agents',version:'1.22.0'}))
  return JSON.stringify({pluginId:'custom-agents@daycry',version:'1.22.0',installedPath:installed})
}
installer.instalarCodexNativo({home,dir,scope:'project',version:'1.22.0',runner,tempRoot})
`
  const r=spawnSync(process.execPath,['--input-type=module','-e',guion,home,dir,enlace],{encoding:'utf8',timeout:20000})
  assert.equal(r.status,0,`salida ${r.status} ${r.signal||''}: ${String(r.stderr).slice(0,300)}`)
  assert.ok(existsSync(join(home,'plugins/cache/daycry/custom-agents/1.22.0/.codex-plugin/plugin.json')))
}))
