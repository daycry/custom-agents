import {test} from 'node:test'
import assert from 'node:assert/strict'
import {mkdtempSync, mkdirSync, writeFileSync, readFileSync, existsSync, readdirSync, rmSync} from 'node:fs'
import {tmpdir} from 'node:os'
import {join} from 'node:path'
import * as installer from '../install/install.mjs'
import {buildPlan, getProvider} from '../install/providers.mjs'

test('Codex native: project registration is isolated and activation depends on native cache success', () => {
  const plan=buildPlan(getProvider('codex'),{dir:join(tmpdir(),'owned-project'),scope:'project',version:'1.22.0'})
  const native=plan.find(p=>p.type==='codex-native-add')
  assert.ok(native,'missing native cache installation step')
  assert.equal(plan.find(p=>p.type==='exec' && p.args[1]==='marketplace'),undefined,'project must not register a global marketplace')
  assert.equal(native.marketplaceRoot,join(tmpdir(),'owned-project'))
  assert.equal(native.minVersion,'0.161.0')
  const activation=plan.filter(p=>p.type==='toml-set')
  assert.ok(activation.every(p=>p.requires===native.id))
  assert.ok(plan.indexOf(native)<plan.indexOf(activation[0]))
})

for(const flag of ['absent','false','true']) test(`Codex native: project cache install preserves global ${flag} and unrelated content`,()=>{
  const temp=mkdtempSync(join(tmpdir(),'ca-native-owned-'))
  try {
    const home=join(temp,'codex'), dir=join(temp,'project'), cache=join(home,'plugins/cache/daycry')
    mkdirSync(home,{recursive:true});mkdirSync(dir,{recursive:true});mkdirSync(join(cache,'other/1.0.0'),{recursive:true})
    const config=join(home,'config.toml'), unrelated=join(cache,'other/1.0.0/keep.txt')
    const before=`# preserve\n[features]\nplugins = true\n${flag==='absent'?'':`[plugins."custom-agents@daycry"]\nenabled = ${flag}\n`}`
    writeFileSync(config,before);writeFileSync(unrelated,'keep')
    let staged=null
    const runner=(args,options)=>{
      staged=options.env.CODEX_HOME
      assert.equal(options.cwd,args[1]==='marketplace' ? join(staged,'registry-cwd') : dir)
      assert.notEqual(staged,home)
      assert.equal(readFileSync(join(staged,'config.toml'),'utf8'),before)
      assert.equal(readFileSync(config,'utf8'),before)
      if(args[1]==='marketplace') {assert.deepEqual(args.slice(0,4),['plugin','marketplace','add',dir]);return 'marketplace added'}
      assert.deepEqual(args.slice(0,4),['plugin','add','custom-agents@daycry','--json'])
      assert.deepEqual(args.slice(4),['-c','marketplaces.daycry.source_type="local"','-c',`marketplaces.daycry.source=${JSON.stringify(dir)}`])
      writeFileSync(join(staged,'config.toml'),'# native setter writes only here\n[plugins."custom-agents@daycry"]\nenabled = true\n')
      const installed=join(staged,'plugins/cache/daycry/custom-agents/1.22.0')
      mkdirSync(join(installed,'.codex-plugin'),{recursive:true})
      writeFileSync(join(installed,'.codex-plugin/plugin.json'),JSON.stringify({name:'custom-agents',version:'1.22.0'}))
      return JSON.stringify({pluginId:'custom-agents@daycry',version:'1.22.0',installedPath:installed})
    }
    const result=installer.instalarCodexNativo({home,dir,scope:'project',version:'1.22.0',runner,tempRoot:temp})
    assert.equal(result.version,'1.22.0')
    assert.equal(readFileSync(config,'utf8'),before)
    assert.equal(readFileSync(unrelated,'utf8'),'keep')
    assert.ok(existsSync(join(cache,'custom-agents/1.22.0/.codex-plugin/plugin.json')))
    assert.ok(!existsSync(staged),'own isolated home cleaned without removing real cache')
  } finally {rmSync(temp,{recursive:true,force:true})}
})

test('Codex native: TOML keys normalize equivalent quoting and decode escapes safely',()=>{
  assert.equal(installer.normalizarTabla('marketplaces."daycry"'),'marketplaces.daycry')
  assert.equal(installer.normalizarTabla('marketplaces."day\\u0063ry"'),'marketplaces.daycry')
  assert.equal(installer.normalizarTabla('"sqlite_home"'),'sqlite_home')
  assert.equal(installer.normalizarTabla('plugins."a\\\"b"'),'plugins."a\\\"b"')
  assert.throws(()=>installer.normalizarTabla('marketplaces."day\\qcry"'),/TOML/)
  const original='[marketplaces."daycry"]\nsource_type="local"\nsource="C:/foreign"\n'
  const changed=installer.ponerToml(original,'marketplaces.daycry','source','C:/ours')
  assert.equal((changed.match(/\[marketplaces\./g)||[]).length,1)
  assert.match(changed,/source = "C:\/ours"/)
  const commented='[marketplaces."daycry"] # keep header comment\nsource_type="local"\nsource="C:/foreign"\n'
  assert.equal((installer.ponerToml(commented,'marketplaces.daycry','source','C:/ours').match(/\[marketplaces\./g)||[]).length,1)
  assert.throws(()=>installer.ponerToml('[marketplaces."daycry"\nsource="C:/foreign"\n','marketplaces.daycry','source','C:/ours'),/TOML/)
})

test('Codex native: snapshot validates typed paths and preserves unrelated env keys',()=>{
  assert.throws(()=>installer.validarSnapshotCodex('"sqlite_home" = "relative"\n'),/relative|ambiguous/)
  assert.doesNotThrow(()=>installer.validarSnapshotCodex('[mcp_servers.test.env]\nconfig_file="relative"\nwritable_roots="plain env"\n'))
  assert.throws(()=>installer.validarSnapshotCodex('[otel.exporter.otlp-http.tls]\nca-certificate="relative"\n'),/relative|ambiguous/)
  assert.throws(()=>installer.validarSnapshotCodex('[[skills.config]]\npath="./review/SKILL.md"\nenabled=false\n'),/relative|ambiguous/)
  assert.throws(()=>installer.validarSnapshotCodex('[skills]\nconfig=[{path="./review/SKILL.md",enabled=false}]\n'),/relative|ambiguous/)
  assert.doesNotThrow(()=>installer.validarSnapshotCodex('[skills]\nconfig=[{name="review",enabled=false}]\n'))
  assert.throws(()=>installer.validarSnapshotCodex('[mcp_servers.test]\ncwd="relative"\n'),/relative|ambiguous/)
})

test('Codex native: CLI rejection leaves global preferences intact and never falls back to real home',()=>{
  const temp=mkdtempSync(join(tmpdir(),'ca-native-owned-'))
  try {
    const home=join(temp,'codex'),dir=join(temp,'project');mkdirSync(home);mkdirSync(dir)
    writeFileSync(join(home,'config.toml'),'[features]\nplugins = false\n')
    let calls=0,stage
    assert.throws(()=>installer.instalarCodexNativo({home,dir,scope:'project',version:'1.22.0',tempRoot:temp,runner:(args,o)=>{
      calls++;stage=o.env.CODEX_HOME;assert.notEqual(stage,home);throw new Error('native rejection')
    }}),/native rejection/)
    assert.equal(calls,1)
    assert.equal(readFileSync(join(home,'config.toml'),'utf8'),'[features]\nplugins = false\n')
    assert.ok(!existsSync(stage))
    assert.ok(!existsSync(join(dir,'.codex/config.toml')))
  } finally {rmSync(temp,{recursive:true,force:true})}
})

test('Codex native: ambiguous relative user config paths fail closed before invoking native add',()=>{
  const temp=mkdtempSync(join(tmpdir(),'ca-native-owned-'))
  try {
    const home=join(temp,'codex'),dir=join(temp,'project');mkdirSync(home);mkdirSync(dir)
    for(const config of ['model_catalog_json = "./models.json"\n','[agents.reviewer]\nconfig_file = "agents/reviewer.toml"\n',
      'js_repl_node_module_dirs = [\n  "./modules"\n]\n']) {
      writeFileSync(join(home,'config.toml'),config)
      assert.throws(()=>installer.instalarCodexNativo({home,dir,scope:'project',version:'1.22.0',tempRoot:temp,runner:()=>assert.fail('must not invoke native CLI')}),/relative|ambiguous/)
      assert.equal(readFileSync(join(home,'config.toml'),'utf8'),config)
    }
  } finally {rmSync(temp,{recursive:true,force:true})}
})

test('Codex native: preexisting different marketplace source is detected before an upserting CLI',()=>{
  const temp=mkdtempSync(join(tmpdir(),'ca-native-owned-'))
  try {
    const config=join(temp,'config.toml'), expected=join(temp,'our-source'), foreign=join(temp,'user-source')
    mkdirSync(expected);mkdirSync(foreign)
    writeFileSync(config,`[marketplaces.daycry]\nsource_type = "local"\nsource = ${JSON.stringify(foreign)}\n`)
    assert.equal(installer.comprobarFuenteCodex(config,expected),'conflict')
    writeFileSync(config,`[marketplaces.daycry]\nsource_type = "local"\nsource = ${JSON.stringify(expected)}\n`)
    assert.equal(installer.comprobarFuenteCodex(config,expected),'same')
    writeFileSync(config,'[marketplaces.daycry]\nsource_type = "git"\nsource = "user/repo"\n')
    assert.equal(installer.comprobarFuenteCodex(config,expected),'conflict')
    writeFileSync(config,'[marketplaces.daycry]\nsource = "./ambiguous"\n')
    assert.equal(installer.comprobarFuenteCodex(config,expected),'unknown')
  } finally {rmSync(temp,{recursive:true,force:true})}
})

test('Codex native: a same-ID cache with a foreign manifest is preserved and blocks replacement',()=>{
  const temp=mkdtempSync(join(tmpdir(),'ca-native-owned-'))
  try {
    const home=join(temp,'codex'),dir=join(temp,'project'),manifest=join(home,'plugins/cache/daycry/custom-agents/1.22.0/.codex-plugin/plugin.json')
    mkdirSync(dirnameFor(manifest),{recursive:true});mkdirSync(dir)
    const contents=JSON.stringify({name:'custom-agents',version:'1.22.0',repository:'https://example.invalid/user-plugin.git'})
    writeFileSync(manifest,contents)
    let called=false
    assert.throws(()=>installer.instalarCodexNativo({home,dir,scope:'project',version:'1.22.0',tempRoot:temp,runner:()=>{called=true;throw new Error('unexpected invocation')}}),/foreign|ownership/)
    assert.equal(called,false)
    assert.equal(readFileSync(manifest,'utf8'),contents)
  } finally {rmSync(temp,{recursive:true,force:true})}
})
function dirnameFor(p){return join(p,'..')}

test('Codex native: owned marketplace keys undo precisely without removing user fields or edits',()=>{
  const own={escrito:'"local"',previo:null,tablaCreada:true}
  assert.equal(installer.restaurarClaveToml('[marketplaces.daycry]\nsource_type = "local"\nother = 42\n','marketplaces.daycry','source_type',own),
    '[marketplaces.daycry]\nother = 42\n')
  assert.equal(installer.restaurarClaveToml('[marketplaces.daycry]\nsource_type = "git"\n','marketplaces.daycry','source_type',own),
    '[marketplaces.daycry]\nsource_type = "git"\n')
  assert.equal(installer.restaurarClaveToml('[marketplaces.daycry]\nsource_type = "local"\n','marketplaces.daycry','source_type',own),'')
  assert.equal(installer.restaurarClaveToml('[marketplaces]\ndaycry = { source_type = "local", other = 42 }\n','marketplaces.daycry','source_type',own),
    '[marketplaces]\ndaycry = { other = 42 }\n')
})
