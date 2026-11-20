// fix24 (plugin-audit-2, T-23, intento 19, gaps 14 y 17): `promoverEntradaCodex` (la entrada instalada en el home aislado se intercambia con la de la cache real).
// Gap 14: si fallan `rename(nueva -> hasta)` Y la vuelta atras, la entrada anterior (`vieja`) es la unica copia: NO se borra. Gap 17: con staging y cache en el mismo volumen se MUEVE por rename (sin
// copiar los 62 MB de la entrada); la copia queda como respaldo.
import {test} from 'node:test'
import assert from 'node:assert/strict'
import {mkdtempSync,mkdirSync,writeFileSync,readFileSync,existsSync,rmSync,readdirSync,renameSync,cpSync} from 'node:fs'
import {tmpdir} from 'node:os'
import {join} from 'node:path'
import * as installer from '../install/install.mjs'

const conRaiz=fn=>{const raiz=mkdtempSync(join(tmpdir(),'ca-prom24-'));try{return fn(raiz)}finally{rmSync(raiz,{recursive:true,force:true})}}
function entradas(raiz) {
  const desde=join(raiz,'staging','1.0.0'),hasta=join(raiz,'cache','custom-agents','1.0.0')
  mkdirSync(desde,{recursive:true});writeFileSync(join(desde,'nuevo.txt'),'nuevo')
  mkdirSync(hasta,{recursive:true});writeFileSync(join(hasta,'viejo.txt'),'viejo')
  return {desde,hasta}
}

test('gap 14: si fallan el rename a destino Y la vuelta atras, la entrada anterior se conserva',()=>conRaiz(raiz=>{
  const {desde,hasta}=entradas(raiz)
  const ops={renameSync:(a,b)=>{
    if(String(a).includes('.old-') && b===hasta) throw Object.assign(new Error('EPERM vuelta atras'),{code:'EPERM'})
    if(String(a).includes('.new-') && b===hasta) throw Object.assign(new Error('EPERM al instalar'),{code:'EPERM'})
    return renameSync(a,b)
  }}
  assert.throws(()=>installer.promoverEntradaCodex(desde,hasta,ops),/EPERM/)
  const dir=join(raiz,'cache','custom-agents')
  const vieja=readdirSync(dir).find(n=>n.includes('.old-'))
  assert.ok(vieja,'la copia anterior sigue en disco')
  assert.equal(readFileSync(join(dir,vieja,'viejo.txt'),'utf8'),'viejo')
}))

test('gap 17: en el mismo volumen se mueve por rename, sin copiar',()=>conRaiz(raiz=>{
  const {desde,hasta}=entradas(raiz)
  let copias=0
  installer.promoverEntradaCodex(desde,hasta,{cpSync:(...a)=>{copias++;return cpSync(...a)}})
  assert.equal(copias,0,'sin cpSync de la entrada entera')
  assert.equal(readFileSync(join(hasta,'nuevo.txt'),'utf8'),'nuevo')
  assert.equal(existsSync(join(hasta,'viejo.txt')),false)
  assert.deepEqual(readdirSync(join(raiz,'cache','custom-agents')),['1.0.0'],'sin restos .new-/.old-')
}))

test('gap 17: si el rename no es posible (otro volumen), se copia como respaldo',()=>conRaiz(raiz=>{
  const {desde,hasta}=entradas(raiz)
  let copias=0
  const ops={cpSync:(...a)=>{copias++;return cpSync(...a)},renameSync:(a,b)=>{
    if(a===desde) throw Object.assign(new Error('EXDEV'),{code:'EXDEV'})
    return renameSync(a,b)
  }}
  installer.promoverEntradaCodex(desde,hasta,ops)
  assert.equal(copias,1)
  assert.equal(readFileSync(join(hasta,'nuevo.txt'),'utf8'),'nuevo')
}))
