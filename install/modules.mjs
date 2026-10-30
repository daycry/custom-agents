// Pure module selection over a bundled, versioned catalog. No provider/tool allowlist.
import {readFileSync,readdirSync,lstatSync} from 'node:fs'
import {resolve,relative,join,dirname,sep,isAbsolute} from 'node:path'
import {createHash} from 'node:crypto'

const CATALOG=new URL('../agent-kits/shared/modules.json',import.meta.url)
const name=value=>typeof value==='string' && /^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/.test(value) && value.length<=100
const object=value=>value!==null && typeof value==='object' && !Array.isArray(value)
const fail=message=>{throw new Error(`module selection: ${message}`)}
const unique=values=>[...new Set(values)].sort()
function names(values,label) {
  if(!Array.isArray(values) || values.length>512 || values.some(value=>!name(value))) fail(`invalid ${label}`)
  return unique(values)
}
export function loadCatalog() {
  const raw=readFileSync(CATALOG)
  if(raw.length>65536) fail('catalog exceeds limit')
  return JSON.parse(raw.toString('utf8'))
}
export function validateCatalog(catalog) {
  if(!object(catalog) || Object.keys(catalog).sort().join()!=='modules,profiles,version' || catalog.version!==1
      || !object(catalog.modules) || !object(catalog.profiles)) fail('invalid catalog schema/version')
  const ids=Object.keys(catalog.modules), profiles=Object.keys(catalog.profiles)
  if(!ids.length || ids.length>64 || !profiles.length || profiles.length>32 || [...ids,...profiles].some(id=>!name(id))) fail('invalid catalog identifiers')
  const owned={skills:new Set(),commands:new Set()}
  for(const module of Object.values(catalog.modules)) {
    if(!object(module) || Object.keys(module).sort().join()!=='commands,requires,skills') fail('invalid module fields')
    for(const field of ['skills','commands','requires']) {
      const values=names(module[field],field)
      if(values.length!==module[field].length) fail(`duplicate ${field}`)
      for(const value of values) {
        if(field==='requires') {if(!Object.hasOwn(catalog.modules,value)) fail('unknown dependency')}
        else {if(owned[field].has(value)) fail(`duplicate owner: ${value}`);owned[field].add(value)}
      }
    }
  }
  for(const values of Object.values(catalog.profiles))
    for(const id of names(values,'profile modules')) if(!Object.hasOwn(catalog.modules,id)) fail('unknown profile module')
  const done=new Set(), active=new Set()
  function visit(id) {
    if(active.has(id)) fail('dependency cycle')
    if(done.has(id)) return
    active.add(id)
    for(const dependency of catalog.modules[id].requires) visit(dependency)
    active.delete(id);done.add(id)
  }
  for(const id of ids) visit(id)
  return catalog
}
export function resolveSelection(options={}) {
  if(!object(options) || Object.keys(options).some(key=>!['profile','include','exclude','catalog'].includes(key))) fail('invalid options')
  const {profile='core',include=[],exclude=[],catalog=loadCatalog()}=options
  validateCatalog(catalog)
  if(typeof profile!=='string' || !Object.hasOwn(catalog.profiles,profile)) fail('unknown profile')
  const added=names(include,'include'), removed=names(exclude,'exclude')
  for(const id of [...added,...removed]) if(!Object.hasOwn(catalog.modules,id)) fail('unknown module')
  if(added.some(id=>removed.includes(id))) fail('included module is excluded')
  const initial=unique([...catalog.profiles[profile],...added]).filter(id=>!removed.includes(id))
  if(!initial.length) fail('empty selection')
  const selected=new Set(), reasons=Object.create(null)
  function add(id,reason) {
    if(removed.includes(id)) fail(`excluded dependency: ${id}`)
    ;(reasons[id]??=new Set()).add(reason)
    if(selected.has(id)) return
    selected.add(id)
    for(const dependency of [...catalog.modules[id].requires].sort()) add(dependency,`required:${id}`)
  }
  for(const id of initial) add(id,added.includes(id)?'explicit':`profile:${profile}`)
  const modules=[...selected].sort()
  return {version:1,profile,modules,
    skills:unique(modules.flatMap(id=>catalog.modules[id].skills)),
    commands:unique(modules.flatMap(id=>catalog.modules[id].commands)),
    selected_by:Object.fromEntries(modules.map(id=>[id,[...reasons[id]].sort()]))}
}

export function validateDelivery(provider,mode,options) {
  const selection=resolveSelection(options)
  if(provider==='claude-code' && mode==='copy') return selection
  const full=resolveSelection({profile:'full'})
  if(selection.modules.join()===full.modules.join()) return selection
  if(provider==='opencode') fail('selective delivery is not supported by the OpenCode installer; use the portable exporter or a complete installation')
  fail('native plugins deliver the complete bundle; use --profile full or the portable exporter')
}

const digest=bytes=>createHash('sha256').update(bytes).digest('hex')
const key=path=>resolve(path).split(sep).join('/')
function info(path) {try{return lstatSync(path)}catch(error){if(error.code==='ENOENT')return null;throw error}}
function confined(root,path) {
  const rel=relative(resolve(root),resolve(path))
  if(!rel || rel==='..' || rel.startsWith(`..${sep}`) || isAbsolute(rel)) fail('path outside delivery root')
  let current=resolve(path)
  while(true) {
    const state=info(current)
    if(state && (state.isSymbolicLink() || current===resolve(path) && (!state.isFile() || state.nlink>1))) fail('linked or nonregular delivery target')
    const parent=dirname(current)
    if(parent===current) break
    current=parent
  }
}

/** Preflight every target before a copy starts; legacy name-only inventories cannot claim files. */
export function planProfileCopies({root,dest,plan,selection,previous}) {
  const output=[], groups=[], hashes=Object.create(null), beforeHashes=Object.create(null), old=previous?.profileHashes || {}
  const accepted=path=>[old[path],...(previous?.estado==='incompleto' ? [previous.profileBeforeHashes?.[path]] : [])]
    .filter(value=>typeof value==='string' && /^[0-9a-f]{64}$/.test(value))
  function append(step) {
    confined(dest,step.to)
    const before=info(step.to), path=key(step.to)
    const beforeHash=before ? digest(readFileSync(step.to)) : null
    if(before && (!Object.hasOwn(old,path) || !accepted(path).includes(beforeHash))) fail('existing or modified file: choose a clean destination or reconcile local changes')
    const content=step.type==='write'?Buffer.from(step.content):readFileSync(join(root,step.from))
    hashes[path]=digest(content)
    beforeHashes[path]=beforeHash
    output.push({...step,beforeHash,contentHash:hashes[path]})
  }
  function walk(from,to) {
    const path=join(root,from), state=lstatSync(path)
    if(state.isSymbolicLink()) fail('linked delivery source')
    const parts=from.replace(/\\/g,'/').split('/')
    if(parts[0]==='skills' && parts.length>1 && !selection.skills.includes(parts[1]))return
    if(parts[0]==='commands' && parts.length>1 && !selection.commands.includes(parts[1].replace(/\.md$/,'')))return
    if(from.replace(/\\/g,'/')==='agents/nemesis.md' && !selection.skills.includes('cybersecurity'))return
    if(parts.includes('__pycache__') || from.endsWith('.pyc'))return
    if(state.isDirectory()) {for(const child of readdirSync(path).sort()) walk(join(from,child),join(to,child));return}
    if(!state.isFile())fail('nonregular delivery source')
    if(from.replace(/\\/g,'/')==='agent-kits/shared/capability-catalog.json') {
      const data=JSON.parse(readFileSync(path,'utf8'))
      data.capabilities=data.capabilities.filter(item=>selection.skills.includes(item.id))
      append({type:'write',to,content:JSON.stringify(data,null,2)+'\n'})
    } else append({type:'copy',from:from.split(sep).join('/'),to})
  }
  for(const step of plan) {
    if(step.type!=='copy') fail('profile copy accepts file copies only')
    const start=output.length
    walk(step.from,step.to)
    const files=output.slice(start)
    if(files.length)groups.push({type:'profile-copy',to:step.to,files})
  }
  const retire=[]
  for(const [path,hash] of Object.entries(old)) {
    confined(dest,path)
    if(Object.hasOwn(hashes,path))continue
    const valid=accepted(path)
    if(info(path) && !valid.includes(digest(readFileSync(path))))fail('removed module has modified files; reconcile local changes first')
    retire.push({type:'retire',to:path,sha256:valid,hashBytes:true})
  }
  return {plan:[...retire,...groups],hashes,beforeHashes}
}

export function verifyProfileTarget(step,dest) {
  confined(dest,step.to)
  const state=info(step.to)
  const actual=state ? digest(readFileSync(step.to)) : null
  if(actual!==step.beforeHash)fail('profile target changed or was modified after preflight')
}
