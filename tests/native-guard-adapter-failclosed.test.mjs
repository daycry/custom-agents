import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import plugin from '../hooks/opencode-plugin.js';
import { opencodeContext } from './helpers/opencode-context.mjs';

// T-06 fix7, gap 10(c): the OpenCode bridge fails closed for the protected roles when the project of the session
// cannot be resolved (no session id, a session without location). A session whose KNOWN location differs from this
// plugin's own is another workspace and keeps its documented skip (tests/native-guard-adapter.test.mjs).
function ownedProject() {
  const directory = mkdtempSync(join(tmpdir(), 'custom-agents-failclosed-'));
  mkdirSync(join(directory, '.claude'));
  writeFileSync(join(directory, '.claude', 'dev.json'), JSON.stringify({guardrails:{ramaPrincipal:false}}));
  return directory;
}

const write = (agent, sessionID) => ({agent, sessionID, id: 'x', tool: 'write', input: {path: 'src/a.txt', content: 'x'}});

test('an unresolvable project denies the protected roles and lets the other identities finish', async () => {
  const directory = ownedProject(); let cleanup;
  const originalWarn = console.warn; console.warn = () => {};
  try {
    const ctx = opencodeContext(directory); cleanup = await plugin.setup(ctx);
    const before = ctx.hooks.get('tool.execute.before');
    for (const agent of ['custom-agents-implementer', 'custom-agents-architect'])
      await assert.rejects(before(write(agent, undefined)), /role guard|denied|protected/i, `${agent} without a session id`);
    ctx.session.get = async () => ({data: {}});
    for (const agent of ['custom-agents-implementer', 'custom-agents-architect'])
      await assert.rejects(before(write(agent, 'own')), /role guard|denied|protected/i, `${agent} with a session without location`);
    for (const agent of ['custom-agents-planner', 'custom-agents-qa', undefined]) {
      await before(write(agent, undefined));
      await before(write(agent, 'own'));
    }
  } finally { console.warn = originalWarn; await cleanup?.(); rmSync(directory, {recursive:true,force:true}); }
});

test('a session in another known location keeps the documented skip', async () => {
  const directory = ownedProject(); let cleanup;
  try {
    const ctx = opencodeContext(directory); cleanup = await plugin.setup(ctx);
    const before = ctx.hooks.get('tool.execute.before');
    ctx.session.get = async () => ({location: {directory: join(directory, 'other')}});
    await before(write('custom-agents-architect', 'foreign'));
  } finally { await cleanup?.(); rmSync(directory, {recursive:true,force:true}); }
});
