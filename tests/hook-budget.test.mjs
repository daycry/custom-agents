import {test} from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
// The launcher may only import Node builtins (tests/test_graphiti_security.py), so the budget
// function lives inside it between markers and is evaluated here from its source.
const launcher = readFileSync(new URL('../hooks/run-hook.mjs', import.meta.url), 'utf8')
const block = launcher.match(/\/\/ child-budget:start[\s\S]*?\/\/ child-budget:end/)
if (!block) throw new Error('child-budget block not found in hooks/run-hook.mjs')
const childBudgetMs = new Function(`${block[0]}\nreturn childBudgetMs`)()
const cleanupConfirmationMs = new Function(`${block[0]}\nreturn cleanupConfirmationMs`)()

// SessionEnd en Claude Code: 1,5 s globales por defecto. El hijo de la captura tiene 800 ms y el resto
// es margen para arrancar el launcher y cerrar el árbol. Si el usuario eleva el presupuesto con
// CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS, el hook (que declara `timeout: 5`) puede usar hasta 5 s:
// el hijo aprovecha ese margen en vez de cortarse a los 800 ms igualmente.
const journal = (env = {}) => childBudgetMs('session-journal.sh', '--runtime=claude', env)

test('hook budget: SessionEnd capture keeps 800 ms without an explicit budget', () => {
  assert.equal(journal(), 800)
  assert.equal(journal({CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS: ''}), 800)
})

test('hook budget: a raised SessionEnd budget gives the child that budget minus the launcher margin', () => {
  assert.equal(journal({CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS: '3000'}), 2300)
  assert.equal(journal({CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS: '5000'}), 4300)
})

test('hook budget: the declared per-hook timeout (5 s) caps the child even with a larger budget', () => {
  assert.equal(journal({CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS: '60000'}), 4300)
})

test('hook budget: invalid or lower values never shrink the default', () => {
  for (const value of ['abc', '-1', '0', '1200', '1500', '2e9x', ' 3000 ']) {
    assert.equal(journal({CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS: value}), 800, value)
  }
})

test('hook budget: other runtimes and hooks keep their budgets', () => {
  assert.equal(childBudgetMs('session-journal.sh', '--runtime=codex', {CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS: '5000'}), 2200)
  // fix16 (gap 22): OpenCode no impone plazo al hook de captura (el catalogo declara 20 s): el presupuesto del producto sube a 8 s. Los 800 ms de SessionEnd de Claude
  // Code y los 4.500 ms del guard (plazos del anfitrion) y los de Codex no se tocan.
  assert.equal(childBudgetMs('session-journal.sh', '--runtime=opencode', {}), 8000)
  assert.equal(childBudgetMs('native-guardrail', '--runtime=claude', {}), 4500)
  assert.equal(childBudgetMs('agent-activity', '--runtime=claude', {}), 2000)
  assert.equal(childBudgetMs('progress-line.sh', '--runtime=claude', {}), 20000)
})

test('hook budget: the declared SessionEnd timeout in hooks.json is the cap the launcher assumes', () => {
  const hooks = JSON.parse(readFileSync(new URL('../hooks/hooks.json', import.meta.url), 'utf8')).hooks
  assert.equal(hooks.SessionEnd[0].hooks[0].timeout, 5)
})

test('hook budget: run-hook.mjs takes its child budget from the shared function', () => {
  const src = readFileSync(new URL('../hooks/run-hook.mjs', import.meta.url), 'utf8')
  assert.match(src, /childBudgetMs\(hook, runtime, process\.env\)/)
})

// panel-redesign T-46 (design O5): for agent-activity, Node reads .claude/dev.json (≤ 64 KiB) and
// returns before launching Python unless `sesion.actividad === true`. The block is evaluated from
// the launcher source like child-budget, with the real node:fs.
import * as fs from 'node:fs'
import {mkdtempSync, rmSync, writeFileSync, mkdirSync} from 'node:fs'
import {tmpdir} from 'node:os'
import {join} from 'node:path'
const optin = launcher.match(/\/\/ activity-optin:start[\s\S]*?\/\/ activity-optin:end/)
const activityEnabled = optin && new Function('fs', `${optin[0]}\nreturn activityEnabled`)(fs)

function withConfig(content, check) {
  const dir = mkdtempSync(join(tmpdir(), 'custom-agents-optin-'))
  try {
    const path = join(dir, 'dev.json')
    if (content === 'directory') mkdirSync(path)
    else if (content !== undefined) writeFileSync(path, content)
    check(path)
  } finally { rmSync(dir, {recursive: true, force: true}) }
}

test('activity opt-in: the shortcut block exists in the launcher', () => {
  assert.ok(optin, 'activity-optin block not found in hooks/run-hook.mjs')
})

test('activity opt-in: only sesion.actividad === true enables the capture', () => {
  withConfig('{"sesion": {"actividad": true}}', path => assert.equal(activityEnabled(path), true))
  withConfig('﻿{"sesion": {"actividad": true}}', path => assert.equal(activityEnabled(path), true))
  for (const value of ['false', '"true"', '1', 'null', '{}', '[]']) {
    withConfig(`{"sesion": {"actividad": ${value}}}`, path => assert.equal(activityEnabled(path), false, value))
  }
  for (const value of ['{}', '[]', '{"sesion": []}', '{"sesion": true}', '{"actividad": true}']) {
    withConfig(value, path => assert.equal(activityEnabled(path), false, value))
  }
})

test('activity opt-in: absent, unreadable, invalid or oversized dev.json means disabled', () => {
  withConfig(undefined, path => assert.equal(activityEnabled(path), false))
  withConfig('directory', path => assert.equal(activityEnabled(path), false))
  withConfig('{"sesion": {"actividad": true', path => assert.equal(activityEnabled(path), false))
  withConfig(Buffer.from([0xff, 0xfe, 0x00]), path => assert.equal(activityEnabled(path), false))
  const head = '{"sesion": {"actividad": true}, "pad": "'
  const exact = head + 'x'.repeat(65536 - head.length - 2) + '"}'
  assert.equal(Buffer.byteLength(exact), 65536)
  withConfig(exact, path => assert.equal(activityEnabled(path), true))
  const over = head + 'x'.repeat(65537 - head.length - 2) + '"}'
  withConfig(over, path => assert.equal(activityEnabled(path), false))
})

test('activity opt-in: the launcher checks it before discovering or spawning Python', () => {
  const src = launcher.replaceAll('\r\n', '\n')
  const main = src.slice(src.indexOf('async function main()'))
  const check = main.indexOf('activityEnabled(')
  assert.ok(check > 0, 'main must call activityEnabled')
  assert.ok(check < main.indexOf('const py = python();'), 'opt-in check must precede Python discovery')
  assert.ok(check < main.indexOf('spawn('), 'opt-in check must precede any spawn')
})

test('hook budget: the cleanup confirmation is 10 s only for OpenCode informational hooks (fix16, gap 22); guard and the other runtimes keep 500 ms', () => {
  const src = readFileSync(new URL('../hooks/run-hook.mjs', import.meta.url), 'utf8')
  assert.match(src, /warn\('child cleanup confirmation timed out'\); abandon\(\);\s*\}, confirmMs\)/)
  assert.match(src, /const confirmMs = cleanupConfirmationMs\(runtime, guard, performance\.now\(\)\);/)
})

// fix17 (gap 20): OpenCode no impone plazo a sus hooks informativos, pero su catalogo declara 20 s desde que el adaptador lanza el launcher. Arranque del launcher + captura (8 s) +
// confirmacion de la limpieza debe caber en 20 s POR CONSTRUCCION: la confirmacion toma lo que queda (con un tope de 10 s), no un valor fijo.
test('hook budget: OpenCode launcher start + capture + cleanup confirmation fits the 20 s catalog window by construction', () => {
  for (const startup of [0, 800, 3700, 6000, 9000, 11000]) {
    const capture = childBudgetMs('session-journal.sh', '--runtime=opencode', {})
    const uptimeAtStop = startup + capture
    const confirm = cleanupConfirmationMs('--runtime=opencode', false, uptimeAtStop)
    assert.ok(uptimeAtStop + confirm <= 20000, `startup ${startup}: ${uptimeAtStop} + ${confirm} > 20000`)
    assert.ok(confirm >= 250, `startup ${startup}: the confirmation keeps a minimum`)
  }
  assert.equal(cleanupConfirmationMs('--runtime=opencode', false, 3000), 10000, 'with room, the confirmation keeps its 10 s cap')
})

test('hook budget: the guard and the other runtimes keep the 500 ms confirmation (their window is imposed by the host)', () => {
  for (const runtime of ['--runtime=claude', '--runtime=codex']) assert.equal(cleanupConfirmationMs(runtime, false, 12000), 500)
  assert.equal(cleanupConfirmationMs('--runtime=opencode', true, 12000), 500)
})
