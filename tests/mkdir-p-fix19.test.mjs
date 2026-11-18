// fix19 (plugin-audit-2, T-23): en Windows con KB5135385 crear un DIRECTORIO a traves de una junction falla
// (mkdir 'link/c' -> EEXIST sin crear nada; 'link/a/b' recursivo -> ENOENT). Crear/leer FICHEROS a traves de ella
// funciona. Contrato del producto: (1) `mkdirP` crea la ruta aunque un ancestro sea un enlace del usuario (HOME,
// dotfile, TEMP) resolviendo el ancestro existente mas profundo; (2) el instalador ya no hace pasar al `codex`
// nativo por una junction para crear directorios.
import {test} from 'node:test'
import assert from 'node:assert/strict'
import {mkdtempSync,mkdirSync,writeFileSync,readFileSync,existsSync,rmSync,symlinkSync,lstatSync,readdirSync,realpathSync} from 'node:fs'
import {tmpdir} from 'node:os'
import {join} from 'node:path'
import {mkdirP} from '../install/mkdir-p.mjs'

const tipo=process.platform==='win32'?'junction':'dir'
const conRaiz=fn=>{const raiz=mkdtempSync(join(tmpdir(),'ca-fix19-'));try{return fn(raiz)}finally{rmSync(raiz,{recursive:true,force:true})}}

test('mkdirP: crea una ruta anidada normal e idempotente',()=>conRaiz(raiz=>{
  const destino=join(raiz,'a','b','c')
  mkdirP(destino);mkdirP(destino)
  assert.ok(lstatSync(destino).isDirectory())
}))

test('mkdirP: crea directorios a traves de un enlace (HOME enlazado)',()=>conRaiz(raiz=>{
  const real=join(raiz,'real');mkdirSync(real)
  const enlace=join(raiz,'link');symlinkSync(real,enlace,tipo)
  mkdirP(join(enlace,'c'))
  mkdirP(join(enlace,'a','b'))
  assert.ok(lstatSync(join(real,'c')).isDirectory())
  assert.ok(lstatSync(join(real,'a','b')).isDirectory())
  writeFileSync(join(enlace,'a','b','f.txt'),'x')
  assert.equal(readFileSync(join(real,'a','b','f.txt'),'utf8'),'x')
}))

test('mkdirP: un enlace colgante o un fichero en la ruta siguen siendo un error (no se acepta nada nuevo)',()=>conRaiz(raiz=>{
  writeFileSync(join(raiz,'fichero'),'x')
  assert.throws(()=>mkdirP(join(raiz,'fichero','sub')),e=>['EEXIST','ENOTDIR'].includes(e.code))
  assert.throws(()=>mkdirP(join(raiz,'fichero')),e=>e.code==='EEXIST')
  const colgante=join(raiz,'colgante');symlinkSync(join(raiz,'no-existe'),colgante,tipo)
  assert.throws(()=>mkdirP(join(colgante,'x')))
  assert.equal(existsSync(join(raiz,'no-existe')),false,'no se crea nada tras un enlace colgante')
}))

test('mkdirP: devuelve la mascara de modo pedida en los directorios nuevos (POSIX)',{skip:process.platform==='win32'},()=>conRaiz(raiz=>{
  const destino=join(raiz,'p','q');mkdirP(destino,{mode:0o700})
  assert.equal(lstatSync(destino).mode&0o777,0o700)
}))

