import {test} from 'node:test'
import assert from 'node:assert/strict'
import {dirname,join} from 'node:path'
import {fileURLToPath,pathToFileURL} from 'node:url'

// fix24 (T-23, intento 19, gap 15): si `taskkill` falla o expira con la raiz «viva», el barrido diferido no puede seguir tratando el pid como raiz viva ni sin tope de fecha: si la raiz muere y su pid se
// reutiliza antes de la foto CIM (1-4 s), mataria a un ajeno. Tras el fallo se vuelve a mirar si la raiz sigue viva; si ya no lo esta, el barrido va con `rootAlive=false` y `until` = ahora.
const win=process.platform==='win32'
const MODULO=join(dirname(fileURLToPath(import.meta.url)),'..','agent-kits','shared','codex-plugin-state.mjs')
const mod=await import(pathToFileURL(MODULO).href)

function barrido(deps,opciones) {
  const llamadas=[]
  const fake=(file,args,options)=>{const h={pid:900000+llamadas.length,on(){return h},unref(){},stdout:null};llamadas.push({file:String(file),args});return h}
  mod.terminateProcessTree(4242,500,500,{since:1000,...opciones,deps:{spawn:fake,...deps}})
  const l=llamadas.find(c=>/cmd/i.test(c.file))
  assert.ok(l,'se lanza el barrido')
  const b64=/-EncodedCommand (\S+)"?$/.exec(l.args.join(' '))[1]
  return Buffer.from(b64,'base64').toString('utf16le')
}

test('Windows (fix24, gap 15): taskkill falla y la raiz ya murio -> el barrido va con rootAlive=false y un tope de fecha',{skip:!win && 'el barrido CIM es de Windows'},()=>{
  let mirada=0
  const script=barrido({spawnSync:()=>({status:1}),alive:()=>++mirada===1},{until:0,rootAlive:true})
  assert.match(script,/\$rootAlive=\$false/,'la raiz que ya no esta viva no se trata como raiz viva (su pid puede ser de un ajeno)')
  const until=Number(/\$until=(\d+)/.exec(script)[1])
  assert.ok(until>Date.now()-60000,'tope de fecha = el instante del fallo (nada creado despues pertenece a la raiz)')
})

test('Windows (fix24, gap 15): taskkill falla y la raiz sigue viva -> el barrido conserva rootAlive=true',{skip:!win && 'el barrido CIM es de Windows'},()=>{
  const script=barrido({spawnSync:()=>({status:1}),alive:()=>true},{until:0,rootAlive:true})
  assert.match(script,/\$rootAlive=\$true/)
})
