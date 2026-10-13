import {test} from 'node:test'
import assert from 'node:assert/strict'
import {mkdtempSync, writeFileSync, readFileSync, readdirSync, rmSync} from 'node:fs'
import {tmpdir} from 'node:os'
import {join} from 'node:path'
import {writeAtomically} from '../skills/to-pdf/scripts/atomic-out.mjs'

function workdir() {
  return mkdtempSync(join(tmpdir(), 'to-pdf-atomic-'))
}

test('to-pdf: a successful render replaces the output and leaves no temporary file', async () => {
  const dir = workdir()
  try {
    const out = join(dir, 'informe.pdf')
    writeFileSync(out, 'viejo')
    await writeAtomically(out, async tmp => writeFileSync(tmp, 'nuevo'))
    assert.equal(readFileSync(out, 'utf8'), 'nuevo')
    assert.deepEqual(readdirSync(dir), ['informe.pdf'])
  } finally { rmSync(dir, {recursive: true, force: true}) }
})

test('to-pdf: a failed render leaves no partial copy and flags the previous output as stale', async () => {
  const dir = workdir()
  try {
    const out = join(dir, 'informe.pdf')
    writeFileSync(out, 'viejo')
    await assert.rejects(
      writeAtomically(out, async tmp => { writeFileSync(tmp, 'a medias'); throw new Error('chromium cayó') }),
      err => err.message.includes('chromium cayó') && err.message.includes('salida ANTERIOR'))
    assert.equal(readFileSync(out, 'utf8'), 'viejo', 'the previous output is not overwritten with a partial file')
    assert.deepEqual(readdirSync(dir), ['informe.pdf'])
  } finally { rmSync(dir, {recursive: true, force: true}) }
})

test('to-pdf: a failed first render creates nothing and does not mention a previous output', async () => {
  const dir = workdir()
  try {
    const out = join(dir, 'informe.pdf')
    await assert.rejects(writeAtomically(out, async () => { throw new Error('sin fuente') }),
      err => err.message === 'sin fuente')
    assert.deepEqual(readdirSync(dir), [])
  } finally { rmSync(dir, {recursive: true, force: true}) }
})

test('to-pdf: a render that writes nothing is a failure, not an empty success', async () => {
  const dir = workdir()
  try {
    await assert.rejects(writeAtomically(join(dir, 'informe.pdf'), async () => {}),
      err => err.message.includes('sin escribir'))
  } finally { rmSync(dir, {recursive: true, force: true}) }
})

test('to-pdf: the converter writes through the atomic helper, never straight to --out', () => {
  const src = readFileSync(new URL('../skills/to-pdf/scripts/to-pdf.mjs', import.meta.url), 'utf8')
  assert.match(src, /writeAtomically\(out,/)
  assert.doesNotMatch(src, /path:\s*out\b/)
})
