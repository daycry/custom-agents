import {test} from 'node:test'
import assert from 'node:assert/strict'
import {observedSessionCount,externalSessions} from '../skills/plugin-panel/assets/console-dom.js'

test('unknown provider plus empty known provider is not a confirmed zero',()=>{
 assert.equal(observedSessionCount({status:'partial',complete:false,sessions:[],providers:[{runtime:'codex',status:'ok'},{runtime:'claude-code',status:'unavailable'}]},[]),null)
})
test('complete empty inventory is zero and observed metadata is a lower bound',()=>{
 assert.equal(observedSessionCount({status:'ok',complete:true,sessions:[]},[]),0)
 assert.equal(observedSessionCount({status:'partial',complete:false,sessions:[{id:'one',runtime:'claude-code'}]},[]),1)
})
test('managed and external entries deduplicate by runtime and native identity',()=>{
 const managed=[{runtime:'codex',native_id:'one'}]
 const inventory={status:'ok',complete:true,sessions:[{runtime:'codex',id:'one'},{runtime:'claude-code',id:'one'}]}
 assert.equal(externalSessions(inventory,managed).length,1)
 assert.equal(observedSessionCount(inventory,managed),2)
})

test('a failed refresh cannot turn a stale empty inventory into confirmed zero',()=>{
 assert.equal(observedSessionCount({status:'ok',complete:true,sessions:[],freshness:{state:'refresh_failed'}},[]),null)
})
