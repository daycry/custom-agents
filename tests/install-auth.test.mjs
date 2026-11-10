import {test} from 'node:test'
import assert from 'node:assert/strict'
import * as auth from '../install/manifest-auth.mjs'
import {mkdtempSync,mkdirSync,symlinkSync,rmSync,writeFileSync} from 'node:fs'
import {tmpdir} from 'node:os'
import {join} from 'node:path'

for(const alias of ['/tmp','/var','/etc'])test(`B6 canonical system alias ${alias} remains usable`,()=>{
  const target=alias+'/project/.claude/manifest.json',calls=[]
  const result=auth.physicalSystemPath
    ? auth.physicalSystemPath(target,'darwin',path=>{calls.push(path);return '/private'+alias})
    : target
  assert.equal(result,'/private'+target)
  assert.deepEqual(calls,[alias])
})

test('B6 resolving a system alias never resolves a project-owned link',()=>{
  const calls=[]
  const result=auth.physicalSystemPath
    ? auth.physicalSystemPath('/tmp/project/untrusted-link/file','darwin',path=>{calls.push(path);return '/private/tmp'})
    : '/tmp/project/untrusted-link/file'
  assert.equal(result,'/private/tmp/project/untrusted-link/file')
  assert.deepEqual(calls,['/tmp'])
})

test('B6 unexpected system alias destinations are rejected',()=>{
  assert.throws(()=>auth.physicalSystemPath?.('/tmp/project/file','darwin',()=>'/unrelated'),/unverified/)
})

// Auditoría H-11: los enlaces de la disposición del usuario (HOME, dotfiles, el propio --dir)
// no bloquean; un enlace en un segmento que crea o borra el instalador sí, con error propio.
test('H-11 a linked trust anchor (HOME or dotfile) is resolved, not rejected',()=>{
  const root=mkdtempSync(join(tmpdir(),'ca-auth-link-'))
  try {
    const real=join(root,'real'),link=join(root,'link');mkdirSync(join(real,'.claude'),{recursive:true})
    symlinkSync(real,link,process.platform==='win32'?'junction':'dir')
    writeFileSync(join(real,'.claude','m.json'),'{}')
    assert.equal(typeof auth.setTrustAnchors,'function')
    auth.setTrustAnchors([link])
    assert.doesNotThrow(()=>auth.regularPath(join(link,'.claude','m.json'),{file:true}))
    assert.doesNotThrow(()=>auth.regularPath(join(link,'.claude','nuevo','x.json'),{file:true}))
  } finally {auth.setTrustAnchors?.([]);rmSync(root,{recursive:true,force:true})}
})

test('H-11 a link below the anchor keeps failing with a dedicated error',()=>{
  const root=mkdtempSync(join(tmpdir(),'ca-auth-link-'))
  try {
    const outside=join(root,'outside'),project=join(root,'project');mkdirSync(outside);mkdirSync(project)
    symlinkSync(outside,join(project,'.claude'),process.platform==='win32'?'junction':'dir')
    auth.setTrustAnchors?.([project])
    assert.throws(()=>auth.regularPath(join(project,'.claude','m.json'),{file:true}),error=>{
      assert.equal(error.code,'LINKED_PATH');assert.match(error.message,/\.claude/);return true})
  } finally {auth.setTrustAnchors?.([]);rmSync(root,{recursive:true,force:true})}
})
