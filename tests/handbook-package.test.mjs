import test from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {fileURLToPath} from 'node:url'

test('advanced handbook links are included in the published documentation tree',()=>{
 const pkg=JSON.parse(readFileSync(fileURLToPath(new URL('../package.json',import.meta.url)),'utf8'))
 for(const directory of ['docs/*.md','docs/en/*.md','docs/agents/','docs/en/agents/'])
  assert.ok(pkg.files.includes(directory),`Missing maintained documentation: ${directory}`)
 assert.ok(!pkg.files.includes('docs/'),'private journal and roadmap trees must not be implicitly included')
})
