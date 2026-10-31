import {test} from 'node:test'
import assert from 'node:assert/strict'
let selection={}
try {selection=await import('../install/modules.mjs')} catch(error) {
  if(error.code!=='ERR_MODULE_NOT_FOUND') throw error
}
const api=()=>{assert.equal(typeof selection.resolveSelection,'function','module selection API missing');return selection}

test('core omits optional integrations and editorial skills',()=>{
  const result=api().resolveSelection({profile:'core'})
  assert.ok(result.skills.includes('tdd'))
  for(const name of ['jira-sync','confluence-publish','confluence-pull','voice-profile','relationship-planning'])
    assert.ok(!result.skills.includes(name),name)
  assert.ok(!result.commands.includes('confluence-pull'))
})
test('explicit modules close dependencies without modifying the source catalog',()=>{
  const first=api().resolveSelection({profile:'core',include:['content','jira']})
  assert.ok(first.skills.includes('voice-profile') && first.skills.includes('jira-sync'))
  assert.deepEqual(first,api().resolveSelection({profile:'core',include:['jira','content','content']}))
  assert.ok(!api().resolveSelection({profile:'core'}).skills.includes('jira-sync'))
})
test('invalid selections fail instead of falling back to full',()=>{
  const {resolveSelection}=api()
  for(const options of [{profile:'missing'},{profile:'core',include:['../jira']},
    {profile:'core',include:['content'],exclude:['voice']},
    {profile:'core',include:['unknown']}]) assert.throws(()=>resolveSelection(options))
})
test('full catalog partitions all source skills exactly once',()=>{
  const catalog=api().loadCatalog()
  const all=Object.values(catalog.modules).flatMap(module=>module.skills)
  assert.equal(new Set(all).size,all.length)
  assert.deepEqual(api().resolveSelection({profile:'full'}).skills,[...all].sort())
})
test('allowed identifiers do not collide with object prototypes',()=>{
  const catalog={version:1,modules:{constructor:{skills:['one'],commands:[],requires:[]}},profiles:{core:['constructor']}}
  assert.deepEqual(api().resolveSelection({catalog}).selected_by,{constructor:['profile:core']})
})
test('empty selection is not a silent install',()=>{
  assert.throws(()=>api().resolveSelection({profile:'core',exclude:['core']}))
})
