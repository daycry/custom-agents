// A project inventory is not proof of ownership. Authenticate the entire inventory
// with a private user key and a destination-bound context before using any claim.
import {createHmac,randomBytes,timingSafeEqual} from 'node:crypto'
import {constants,lstatSync,fstatSync,openSync,closeSync,readFileSync,writeFileSync,mkdirSync,realpathSync} from 'node:fs'
import {homedir} from 'node:os'
import {resolve,join,dirname,relative,isAbsolute,sep,posix} from 'node:path'

const MAX_BYTES=4*1024*1024
const fail=()=>{const error=new Error('unverified installation manifest: no automatic cleanup; back up and reconcile the legacy or modified installation before reinstalling');error.code='UNVERIFIED_MANIFEST';throw error}
export function physicalSystemPath(path,platform=process.platform,resolveLink=realpathSync) {
  if(platform!=='darwin')return resolve(path)
  const absolute=posix.resolve(path)
  for(const alias of ['/tmp','/var','/etc']) {
    if(absolute!==alias && !absolute.startsWith(alias+'/'))continue
    let target
    try {target=resolveLink(alias)} catch {return absolute}
    if(target===alias)return absolute
    if(target!=='/private'+alias)fail()
    return target+absolute.slice(alias.length)
  }
  return absolute
}
const canonical=value=>JSON.stringify(value,(_key,row)=>row && typeof row==='object' && !Array.isArray(row)
  ? Object.fromEntries(Object.keys(row).sort().map(key=>[key,row[key]])) : row)
const normalized=path=>{
  let result=physicalSystemPath(path)
  try {result=realpathSync(result)} catch {/* A fresh manifest does not exist yet. */}
  return process.platform==='win32' ? result.toLowerCase() : result
}
export function manifestContext(provider,scope,dir,path) {
  return {provider,scope,project:scope==='project'?normalized(dir):null,manifest:normalized(path)}
}
export function regularPath(path,{file=false}={}) {
  let current=physicalSystemPath(path),leaf=true
  while(true) {
    let state
    try {state=lstatSync(current)} catch(error) {if(error.code!=='ENOENT')throw error}
    if(state && (state.isSymbolicLink() || (leaf && file ? !state.isFile() || state.nlink!==1 : !state.isDirectory())))fail()
    const parent=dirname(current)
    if(parent===current)break
    current=parent;leaf=false
  }
}
function key(context,create) {
  const path=join(homedir(),'.custom-agents','installer-auth-v1','key')
  if(context.project) {
    const rel=relative(context.project,physicalSystemPath(path))
    if(!isAbsolute(rel) && rel!=='..' && !rel.startsWith('..'+sep))fail()
  }
  regularPath(dirname(path));regularPath(path,{file:true})
  if(create) {
    mkdirSync(dirname(path),{recursive:true,mode:0o700});regularPath(dirname(path))
    try {writeFileSync(path,randomBytes(32),{flag:'wx',mode:0o600})}
    catch(error) {if(error.code!=='EEXIST')throw error}
  }
  regularPath(path,{file:true})
  let fd
  try {
    fd=openSync(path,constants.O_RDONLY|(constants.O_NOFOLLOW||0))
    const info=fstatSync(fd)
    if(!info.isFile() || info.nlink!==1 || info.size!==32 || (process.platform!=='win32' && (info.mode&0o077)))fail()
    const bytes=readFileSync(fd)
    if(bytes.length!==32)fail()
    return bytes
  } finally {if(fd!==undefined)closeSync(fd)}
}
function payload(manifest) {
  const {ownership,...body}=manifest
  return body
}
export function signManifest(manifest,context) {
  const body=payload(manifest),text=canonical({context,manifest:body})
  if(Buffer.byteLength(text)>MAX_BYTES)fail()
  return {...body,ownership:{version:1,mac:createHmac('sha256',key(context,true)).update(text).digest('hex')}}
}
export function readManifest(path,context) {
  regularPath(path,{file:true})
  let info
  try {info=lstatSync(path)} catch(error) {if(error.code==='ENOENT')return null;throw error}
  if(info.size>MAX_BYTES)fail()
  let manifest
  try {manifest=JSON.parse(readFileSync(path,'utf8').replace(/^\uFEFF/,''))} catch {fail()}
  if(!manifest || Array.isArray(manifest) || manifest.plugin!=='custom-agents' || manifest.provider!==context.provider
      || manifest.scope!==context.scope || manifest.ownership?.version!==1 || !/^[a-f0-9]{64}$/.test(manifest.ownership.mac||''))fail()
  try {
    const expected=createHmac('sha256',key(context,false)).update(canonical({context,manifest:payload(manifest)})).digest()
    if(!timingSafeEqual(expected,Buffer.from(manifest.ownership.mac,'hex')))fail()
  } catch {fail()}
  return manifest
}
