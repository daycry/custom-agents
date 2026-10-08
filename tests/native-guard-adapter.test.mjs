import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, existsSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import plugin from '../hooks/opencode-plugin.js';
import { opencodeContext } from './helpers/opencode-context.mjs';

function ownedProject() {
  const directory = mkdtempSync(join(tmpdir(), 'custom-agents-native-guard-'));
  mkdirSync(join(directory, '.claude'));
  mkdirSync(join(directory, 'docs', 'roadmap', 'fixture'), {recursive:true});
  writeFileSync(join(directory, '.claude', 'dev.json'), JSON.stringify({guardrails:{ramaPrincipal:false}}));
  return directory;
}

test('before guard prevents protected writes and lets other native roles finish', async () => {
  const directory = ownedProject(); let cleanup;
  try {
    const ctx = opencodeContext(directory); cleanup = await plugin.setup(ctx);
    const before = ctx.hooks.get('tool.execute.before');
    const apply = async (agent, path, claimed='custom-agents-planner') => {
      const event = {agent, sessionID:'same-native-session', id:'same-outer-codemode-id',
        tool:'write', input:{path, content:'own content', agent:claimed}};
      await before(event);
      writeFileSync(join(directory, path), 'own content');
    };
    const denied = 'docs/roadmap/fixture/spec.md';
    await assert.rejects(apply('custom-agents-implementer', denied), /implementer/);
    assert.equal(existsSync(join(directory, denied)), false);
    await apply('custom-agents-implementer', 'docs/roadmap/fixture/tasks.md');
    await apply('custom-agents-architect', 'docs/roadmap/fixture/design.md');
    await assert.rejects(apply('custom-agents-architect', 'source.txt'), /architect/);
    assert.equal(existsSync(join(directory, 'source.txt')), false);
    // Same tool/session/call ID cannot carry a deny into another role.
    for (const agent of ['custom-agents-planner', 'implementer', 'consumer-agent', undefined]) {
      await apply(agent, denied, 'custom-agents-implementer');
      assert.equal(readFileSync(join(directory, denied), 'utf8'), 'own content');
    }
  } finally { await cleanup?.(); rmSync(directory, {recursive:true,force:true}); }
});

test('before guard checks original and destination of native patch moves', async () => {
  const directory = ownedProject(); let cleanup;
  try {
    const ctx = opencodeContext(directory); cleanup = await plugin.setup(ctx);
    const before = ctx.hooks.get('tool.execute.before');
    await assert.rejects(before({agent:'custom-agents-implementer',sessionID:'move',id:'nested',tool:'patch',
      input:{patchText:'*** Begin Patch\n*** Update File: docs/roadmap/fixture/spec.md\n*** Move to: source.txt\n@@\n-old\n+new\n*** End Patch'}}), /implementer/);
    await assert.rejects(before({agent:'custom-agents-implementer',sessionID:'move',id:'nested',tool:'patch',
      input:{patchText:'*** Begin Patch\n*** Update File: source.txt\n*** Move to: docs/roadmap/fixture/spec.md\n@@\n-old\n+new\n*** End Patch'}}), /implementer/);
  } finally { await cleanup?.(); rmSync(directory, {recursive:true,force:true}); }
});

test('before guard honors opt-out and skips foreign sessions', async () => {
  const directory = ownedProject(); let cleanup;
  const messages = [], originalWarn = console.warn;
  console.warn = message => messages.push(String(message));
  try {
    const ctx = opencodeContext(directory); cleanup = await plugin.setup(ctx);
    const before = ctx.hooks.get('tool.execute.before');
    const event = {agent:'custom-agents-architect',sessionID:'own',id:'x',tool:'write',input:{path:'source.txt'}};
    writeFileSync(join(directory,'.claude','dev.json'), '{"guardrails":false}');
    await before(event);
    assert.ok(messages.some(message => /disabled/.test(message)), messages.join('\n'));
    writeFileSync(join(directory,'.claude','dev.json'), '{}');
    ctx.session.get = async () => ({location:{directory:join(directory,'other')}});
    await before(event);
  } finally { console.warn = originalWarn; await cleanup?.(); rmSync(directory, {recursive:true,force:true}); }
});
