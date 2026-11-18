// mkdir -p que sobrevive a un enlace del usuario en un ancestro (HOME, dotfile, TEMP enlazados).
// En Windows con KB5135385 crear un DIRECTORIO a traves de una junction falla (mkdir 'link/c' -> EEXIST sin crear
// nada; recursivo 'link/a/b' -> ENOENT), aunque crear o leer FICHEROS a traves de ella funciona. La solucion es
// resolver el ancestro existente mas profundo y crear el resto desde su ruta real. Semantica identica a
// `mkdir -p`: lo que crea es lo mismo que habria creado el SO siguiendo el enlace, asi que no acepta nada que
// el SO no aceptara (ficheros y enlaces colgantes en la ruta siguen siendo un error); los rechazos de enlaces del
// instalador (`regularPath`) corren ANTES y no dependen de esta funcion.
import {mkdirSync,statSync,realpathSync,writeFileSync} from 'node:fs'
import {resolve,dirname,join,basename} from 'node:path'

export function mkdirP(path,options={}) {
  const target=resolve(path)
  try {return mkdirSync(target,{...options,recursive:true})}
  catch(error) {if(error.code!=='ENOENT' && error.code!=='EEXIST')throw error}
  const pending=[]
  let current=target
  while(true) {
    let state=null
    try {state=statSync(current)} catch(error) {if(error.code!=='ENOENT')throw error}
    if(state) {
      if(!state.isDirectory()) {const error=new Error(`EEXIST: ${current} exists and is not a directory`);error.code='EEXIST';error.path=current;throw error}
      break
    }
    const parent=dirname(current)
    if(parent===current)break
    pending.unshift(current.slice(parent.length).replace(/^[\/]+/,''))
    current=parent
  }
  const anchor=realpathSync(current)
  if(!pending.length)return undefined
  const resolved=join(anchor,...pending)
  mkdirSync(resolved,{...options,recursive:true})
  return resolved
}

// Crear un fichero NUEVO con O_EXCL a traves de una junction tambien falla en esa build (EEXIST sin crear nada).
// El directorio padre debe existir; se resuelve a su ruta real y el fichero se crea ahi con `wx`: el componente
// final NO se sigue (si existe, aunque sea un enlace colgante, sigue siendo EEXIST).
export function writeFileExclusive(path,data,options={}) {
  const target=resolve(path)
  writeFileSync(join(realpathSync(dirname(target)),basename(target)),data,{...options,flag:'wx'})
}
