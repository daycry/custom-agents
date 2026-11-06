import {test} from 'node:test'
import assert from 'node:assert/strict'
import * as auth from '../install/manifest-auth.mjs'

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
