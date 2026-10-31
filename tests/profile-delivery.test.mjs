import {test} from 'node:test'
import assert from 'node:assert/strict'
import {mkdtempSync,mkdirSync,writeFileSync,readFileSync,existsSync,rmSync} from 'node:fs'
import {tmpdir} from 'node:os'
import {join} from 'node:path'
import * as delivery from '../install/modules.mjs'

test('copy profile plans enumerate only selected skills and commands',()=>{
  assert.equal(typeof delivery.planProfileCopies,'function')
  const temp=mkdtempSync(join(tmpdir(),'ca-profile-'))
  try {
    for(const skill of ['tdd','jira-sync']) {
      mkdirSync(join(temp,'source','skills',skill),{recursive:true})
      writeFileSync(join(temp,'source','skills',skill,'SKILL.md'),skill)
    }
    const result=delivery.planProfileCopies({root:join(temp,'source'),dest:join(temp,'dest'),
      plan:[{type:'copy',from:'skills',to:join(temp,'dest/skills')}],
      selection:{skills:['tdd'],commands:[]},previous:null})
    assert.deepEqual(result.plan.flatMap(step=>step.files || [step]).map(step=>step.from),['skills/tdd/SKILL.md'])
    assert.equal(Object.keys(result.hashes).length,1)
    assert.equal(existsSync(join(temp,'dest')),false)
  } finally {rmSync(temp,{recursive:true,force:true})}
})

test('copy profiles reject user files and modified files before any operation',()=>{
  assert.equal(typeof delivery.planProfileCopies,'function')
  const temp=mkdtempSync(join(tmpdir(),'ca-profile-'))
  try {
    mkdirSync(join(temp,'source/skills/tdd'),{recursive:true})
    mkdirSync(join(temp,'dest/skills/tdd'),{recursive:true})
    writeFileSync(join(temp,'source/skills/tdd/SKILL.md'),'source')
    const target=join(temp,'dest/skills/tdd/SKILL.md')
    writeFileSync(target,'mine')
    assert.throws(()=>delivery.planProfileCopies({root:join(temp,'source'),dest:join(temp,'dest'),
      plan:[{type:'copy',from:'skills',to:join(temp,'dest/skills')}],
      selection:{skills:['tdd'],commands:[]},previous:{files:[target]}}))
    assert.equal(readFileSync(target,'utf8'),'mine')
  } finally {rmSync(temp,{recursive:true,force:true})}
})

test('native partial selection is rejected before the provider plan runs',()=>{
  assert.equal(typeof delivery.validateDelivery,'function')
  assert.throws(()=>delivery.validateDelivery('codex','plugin',{profile:'core'}),/native|nativ/i)
  assert.throws(()=>delivery.validateDelivery('opencode','plugin',{profile:'core'}),/supported|soport/i)
  assert.doesNotThrow(()=>delivery.validateDelivery('claude-code','copy',{profile:'core'}))
})

test('binary file ownership compares exact bytes',()=>{
  const temp=mkdtempSync(join(tmpdir(),'ca-profile-'))
  try {
    mkdirSync(join(temp,'source/assets'),{recursive:true})
    const input=join(temp,'source/assets/image.bin')
    writeFileSync(input,Buffer.from([255]))
    const args={root:join(temp,'source'),dest:join(temp,'dest'),
      plan:[{type:'copy',from:'assets',to:join(temp,'dest/assets')}],
      selection:{skills:[],commands:[]},previous:null}
    const first=delivery.planProfileCopies(args)
    writeFileSync(input,Buffer.from([254]))
    const second=delivery.planProfileCopies(args)
    assert.notDeepEqual(first.hashes,second.hashes)
  } finally {rmSync(temp,{recursive:true,force:true})}
})

test('gap D: profile checkpoints scale with payload groups, not file count',()=>{
  const temp=mkdtempSync(join(tmpdir(),'ca-profile-'))
  try {
    mkdirSync(join(temp,'source/assets'),{recursive:true})
    for(let i=0;i<30;i++)writeFileSync(join(temp,'source/assets',`${i}.txt`),'content')
    const result=delivery.planProfileCopies({root:join(temp,'source'),dest:join(temp,'dest'),
      plan:[{type:'copy',from:'assets',to:join(temp,'dest/assets')}],
      selection:{skills:[],commands:[]},previous:null})
    assert.equal(result.plan.length,1)
    assert.equal(Object.keys(result.hashes).length,30)
  } finally {rmSync(temp,{recursive:true,force:true})}
})

test('gap B: a profile write revalidates ownership after preflight',()=>{
  assert.equal(typeof delivery.verifyProfileTarget,'function')
  const temp=mkdtempSync(join(tmpdir(),'ca-profile-'))
  try {
    mkdirSync(join(temp,'source/assets'),{recursive:true})
    mkdirSync(join(temp,'dest/assets'),{recursive:true})
    writeFileSync(join(temp,'source/assets/file.txt'),'source')
    const args={root:join(temp,'source'),dest:join(temp,'dest'),
      plan:[{type:'copy',from:'assets',to:join(temp,'dest/assets')}],
      selection:{skills:[],commands:[]},previous:null}
    const result=delivery.planProfileCopies(args)
    writeFileSync(join(temp,'dest/assets/file.txt'),'consumer edit during install')
    const step=result.plan.flatMap(step=>step.files || [step])[0]
    assert.throws(()=>delivery.verifyProfileTarget(step,join(temp,'dest')),/changed|modified/i)
  } finally {rmSync(temp,{recursive:true,force:true})}
})
