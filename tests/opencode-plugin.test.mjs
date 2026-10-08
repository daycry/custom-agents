import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, readdirSync, rmSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import plugin from '../hooks/opencode-plugin.js';
import { opencodeContext, until } from './helpers/opencode-context.mjs';

function project() {
  const dir = mkdtempSync(join(tmpdir(), 'custom-agents-v2-test-'));
  mkdirSync(join(dir, '.claude'), { recursive: true });
  mkdirSync(join(dir, 'docs', 'roadmap'), { recursive: true });
  return dir;
}

test('V2 default definition registers native domains and cleans up', async () => {
  const dir = project();
  try {
    assert.equal(plugin.id, 'custom-agents');
    const ctx = opencodeContext(dir);
    const cleanup = await plugin.setup(ctx);
    for (const name of ['tool.execute.after', 'session.prompt', 'session.context']) assert.ok(ctx.hooks.has(name));
    await cleanup();
    assert.equal(ctx.stopped, true);
  } finally { rmSync(dir, { recursive: true, force: true }); }
});

test('prompt captures UTF8 without mutating input and honors private turns', async () => {
  const dir = project(); let cleanup;
  try {
    const ctx = opencodeContext(dir); cleanup = await plugin.setup(ctx);
    const event = { sessionID: 'v2-capture', prompt: { text: 'Decidimos usar Python 🐍' }, delivery: 'steer' };
    const original = structuredClone(event);
    await ctx.hooks.get('session.prompt')(event);
    assert.deepEqual(event, original);
    assert.match(readFileSync(join(dir, '.claude', 'session-prompts-v2-capture.log'), 'utf8'), /Python 🐍/);
    await ctx.hooks.get('session.prompt')({ sessionID: 'private-turn', prompt: { text: '<private> petición privada' } });
    assert.equal(existsSync(join(dir, '.claude', 'session-prompts-private-turn.log')), false);
  } finally { await cleanup?.(); rmSync(dir, { recursive: true, force: true }); }
});

test('idle captures envelope and the next context replays and injects bounded local sources', async () => {
  const dir = project(); let cleanup;
  try {
    const ctx = opencodeContext(dir); cleanup = await plugin.setup(ctx);
    await ctx.hooks.get('session.prompt')({ sessionID: 'v2-idle', prompt: { text: 'Decidimos verificar el contexto' } });
    ctx.emit({ type: 'session.execution.succeeded', data: { sessionID: 'v2-idle' } });
    const queue = join(dir, '.claude', 'journal', 'outbox');
    await until(() => existsSync(queue) && readdirSync(queue).some(name => name.endsWith('.json')));
    const event = { sessionID: 'v2-resume', system: [{ type: 'text', text: 'Instrucciones propias' }] };
    await ctx.hooks.get('session.context')(event);
    assert.equal(event.system[0].text, 'Instrucciones propias');
    assert.equal(event.system.length, 2);
    assert.match(event.system[1].text, /custom-agents|Plugin|plugin/);
    assert.ok(event.system[1].text.length <= 10000);
    assert.ok(readdirSync(join(dir, 'docs', 'knowledge', 'journal')).some(name => name.endsWith('.md') && name !== 'README.md'));
  } finally { await cleanup?.(); rmSync(dir, { recursive: true, force: true }); }
});

test('foreign sessions and workspace events never write or inject into this project', async () => {
  const dir = project(); let cleanup;
  try {
    const ctx = opencodeContext(dir);
    ctx.session.get = async () => ({ data: { location: { directory: resolve(dir, '..', 'other-project') } } });
    cleanup = await plugin.setup(ctx);
    await ctx.hooks.get('session.prompt')({ sessionID: 'foreign', prompt: { text: 'texto ajeno' } });
    const event = { sessionID: 'foreign', system: [] };
    await ctx.hooks.get('session.context')(event);
    assert.deepEqual(event.system, []);
    ctx.emit({ type: 'session.status', location: { directory: dir, workspaceID: 'other-workspace' }, data: { sessionID: 'foreign', status: { type: 'idle' } } });
    await cleanup(); cleanup = null;
    assert.equal(existsSync(join(dir, '.claude', 'journal')), false);
    assert.equal(existsSync(join(dir, '.claude', 'session-prompts-foreign.log')), false);
  } finally { await cleanup?.(); rmSync(dir, { recursive: true, force: true }); }
});

test('completed writes use native input and preserve result content and existing metadata', async () => {
  const dir = project(); let cleanup;
  try {
    const ctx = opencodeContext(dir); cleanup = await plugin.setup(ctx);
    const path = join(dir, 'docs', 'plan.md'); writeFileSync(path, '# Plan\n', 'utf8');
    const event = { sessionID: 'v2-write', tool: 'edit', status: 'completed', input: { path }, result: { content: 'edited', metadata: { own: true } } };
    await ctx.hooks.get('tool.execute.after')(event);
    assert.equal(event.result.content, 'edited'); assert.equal(event.result.metadata.own, true);
    assert.equal(existsSync(join(dir, '.claude', '.confluence-pending')), true);
  } finally { await cleanup?.(); rmSync(dir, { recursive: true, force: true }); }
});

test('native applied targets dispatch indented patches and normalized write paths', async () => {
  const dir = project(); let cleanup;
  try {
    const ctx = opencodeContext(dir); cleanup = await plugin.setup(ctx);
    const target = join(dir, 'docs', 'native.md'); writeFileSync(target, '# Native\n');
    for (const event of [
      { tool: 'patch', input: { patchText: '  *** Add File: docs/native.md' }, output: { applied: [{ type: 'add', target, resource: 'docs/native.md' }] } },
      { tool: 'write', input: { path: '~/not-the-project.md' }, output: { target, resource: 'docs/native.md' } },
    ]) {
      rmSync(join(dir, '.claude', '.confluence-pending'), { force: true });
      await ctx.hooks.get('tool.execute.after')({ sessionID: 'native-target', status: 'completed', tool: event.tool, input: event.input, result: { output: event.output } });
      assert.equal(existsSync(join(dir, '.claude', '.confluence-pending')), true, event.tool);
    }
  } finally { await cleanup?.(); rmSync(dir, { recursive: true, force: true }); }
});

test('a native move out of docs preserves the deleted source notification', async () => {
  const dir = project(); let cleanup;
  try {
    const ctx=opencodeContext(dir); cleanup=await plugin.setup(ctx);
    const source=join(dir,'docs','source.md'), target=join(dir,'moved.md');
    const event={sessionID:'native-move',tool:'patch',status:'completed',
      input:{patchText:'*** Update File: docs/source.md\n*** Move to: moved.md'},
      result:{output:{applied:[{type:'update',target,resource:'moved.md'}],
        files:[{file:'moved.md',patch:`Index: ${source}\n===\n--- ${source}\n+++ ${source}\n@@ -1 +1 @@\n-old\n+new\n`,additions:1,deletions:1,status:'modified'}]}}};
    await ctx.hooks.get('tool.execute.after')(event);
    assert.equal(existsSync(join(dir,'.claude','.confluence-pending')),true);
  } finally { await cleanup?.(); rmSync(dir,{recursive:true,force:true}); }
});

test('unchanged context is reused while prompts, tools and canonical files invalidate it', async () => {
  const dir = project(); let cleanup;
  try {
    const adapter = await isolatedPlugin(dir, `import fs from 'node:fs';
      if(process.argv[2]==='session-context.sh') {
        const n=fs.existsSync('runs') ? Number(fs.readFileSync('runs','utf8'))+1 : 1;
        fs.writeFileSync('runs',String(n));
        process.stdout.write(JSON.stringify({hookSpecificOutput:{additionalContext:'context '+n}}));
      }`);
    const ctx = opencodeContext(dir); cleanup = await adapter.setup(ctx);
    const call = async (sessionID='cache') => {
      const event={sessionID,system:[]}; await ctx.hooks.get('session.context')(event); return event.system[0].text;
    };
    assert.equal(await call(), 'context 1'); assert.equal(await call(), 'context 1');
    await ctx.hooks.get('tool.execute.after')({sessionID:'cache',tool:'read',status:'completed'});
    assert.equal(await call(), 'context 1');
    await ctx.hooks.get('session.prompt')({sessionID:'cache',prompt:{text:'next turn'}});
    assert.equal(await call(), 'context 2');
    await ctx.hooks.get('tool.execute.after')({sessionID:'cache',tool:'bash',status:'completed'});
    assert.equal(await call(), 'context 3');
    mkdirSync(join(dir,'docs','roadmap','fixture'));
    writeFileSync(join(dir,'docs','roadmap','fixture','tasks.md'),'ledger changed');
    assert.equal(await call(), 'context 4');
    mkdirSync(join(dir,'docs','knowledge'),{recursive:true});
    writeFileSync(join(dir,'docs','knowledge','memory.md'),'memory changed');
    assert.equal(await call(), 'context 5');
    writeFileSync(join(dir,'.claude','dev.json'),'{}');
    assert.equal(await call(), 'context 6');
    assert.equal(await call('other-session'), 'context 7');
    const clock = Date.now;
    try { Date.now = () => clock() + 31000; assert.equal(await call('other-session'), 'context 8'); }
    finally { Date.now = clock; }
    writeFileSync(join(dir,'.claude','dev.json'),'{"sesion":{"journal":{"dir":"own-queue"}}}');
    assert.equal(await call('other-session'), 'context 9');
    assert.equal(await call('other-session'), 'context 10');
    writeFileSync(join(dir,'.claude','dev.json'),'{');
    assert.equal(await call('other-session'), 'context 11');
    assert.equal(await call('other-session'), 'context 12');
    ctx.session.get = async () => ({location:{directory:resolve(dir,'..','foreign')}});
    const foreign={sessionID:'other-session',system:[]}; await ctx.hooks.get('session.context')(foreign);
    assert.deepEqual(foreign.system,[]);
  } finally { await cleanup?.(); rmSync(dir, { recursive: true, force: true }); }
});

test('a concurrent mutation prevents saving an in-flight context', async () => {
  const dir = project(); let cleanup;
  try {
    const adapter = await isolatedPlugin(dir, `import fs from 'node:fs';
      if(process.argv[2]==='session-context.sh') {
        const n=fs.existsSync('runs') ? Number(fs.readFileSync('runs','utf8'))+1 : 1;
        fs.writeFileSync('runs',String(n));
        setTimeout(()=>process.stdout.write(JSON.stringify({hookSpecificOutput:{additionalContext:'context '+n}})),250);
      }`);
    const ctx = opencodeContext(dir); cleanup = await adapter.setup(ctx);
    const event={sessionID:'concurrent',system:[]};
    const pending=ctx.hooks.get('session.context')(event);
    await until(()=>existsSync(join(dir,'runs')));
    await ctx.hooks.get('tool.execute.after')({sessionID:'concurrent',tool:'unknown-tool',status:'completed'});
    await pending;
    const second={sessionID:'concurrent',system:[]}; await ctx.hooks.get('session.context')(second);
    assert.equal(second.system[0].text,'context 2');
  } finally { await cleanup?.(); rmSync(dir, { recursive: true, force: true }); }
});

async function isolatedPlugin(dir, launcher) {
  const folder = join(dir, 'hooks'); mkdirSync(folder, { recursive: true });
  writeFileSync(join(dir, 'package.json'), '{"type":"module"}');
  writeFileSync(join(folder, 'adapter.js'), readFileSync(new URL('../hooks/opencode-plugin.js', import.meta.url)));
  writeFileSync(join(folder, 'run-hook.mjs'), launcher);
  return (await import(pathToFileURL(join(folder, 'adapter.js')).href)).default;
}

test('cleanup terminates its launcher tree and settles the pending hook', async () => {
  const dir = project(); let cleanup, pending, pid;
  try {
    const adapter = await isolatedPlugin(dir, `import {spawn} from 'node:child_process'; import fs from 'node:fs';
      const child=spawn(process.execPath,['-e','setInterval(()=>{},1000)'],{stdio:'ignore'});
      fs.writeFileSync('child.pid',String(child.pid));setInterval(()=>{},1000);`);
    const ctx = opencodeContext(dir); cleanup = await adapter.setup(ctx);
    pending = ctx.hooks.get('session.prompt')({ sessionID: 'cancelled', prompt: { text: 'own cancellation fixture' } });
    await until(() => existsSync(join(dir, 'child.pid')));
    pid = Number(readFileSync(join(dir, 'child.pid'), 'utf8'));
    await cleanup(); cleanup = null;
    await until(() => { try { process.kill(pid, 0); return false; } catch { return true; } });
    await pending; pending = null;
  } finally {
    if (pid) {
      if (process.platform === 'win32') { try { execFileSync('taskkill', ['/PID', String(pid), '/T', '/F'], { stdio: 'ignore', windowsHide: true }); } catch {} }
      else { try { process.kill(pid, 'SIGKILL'); } catch {} }
    }
    await cleanup?.(); await pending;
    rmSync(dir, { recursive: true, force: true });
  }
});

test('stderr failures warn without exposing consumer payloads and context is capped', async () => {
  const dir = project(); let cleanup;
  const oldWarn = console.warn, messages = []; console.warn = text => messages.push(text);
  try {
    const adapter = await isolatedPlugin(dir, `process.stderr.write('PRIVATE_SENTINEL');
      process.stdout.write(JSON.stringify({hookSpecificOutput:{additionalContext:'x'.repeat(12000)}}));`);
    const ctx = opencodeContext(dir); cleanup = await adapter.setup(ctx);
    const event = { sessionID: 'bounded', system: [] };
    await ctx.hooks.get('session.context')(event);
    assert.equal(event.system[0].text.length, 10000);
    assert.ok(messages.length > 0);
    assert.equal(messages.join('').includes('PRIVATE_SENTINEL'), false);
  } finally { console.warn = oldWarn; await cleanup?.(); rmSync(dir, { recursive: true, force: true }); }
});

test('patch metadata carries diagnostics while malformed and oversized context stays empty', async () => {
  const dir = project(); let cleanup;
  try {
    const adapter = await isolatedPlugin(dir, `process.stdout.write(JSON.stringify({systemMessage:'Own diagnostic'}));`);
    const ctx = opencodeContext(dir); cleanup = await adapter.setup(ctx);
    const event = { sessionID: 'patch', tool: 'patch', status: 'completed', input: { patchText: '*** Add File: docs/x.md' }, result: { content: [{ type: 'text', text: 'own result' }], metadata: { own: true } } };
    await ctx.hooks.get('tool.execute.after')(event);
    assert.equal(event.result.content[0].text, 'own result');
    assert.equal(event.result.metadata.own, true);
    assert.deepEqual(event.result.metadata.customAgentsMessages, ['Own diagnostic', 'Own diagnostic', 'Own diagnostic']);
    await cleanup(); cleanup = null;
    for (const source of ["process.stdout.write('invalid JSON');", "process.stdout.write('x'.repeat(70000));"]) {
      writeFileSync(join(dir, 'hooks', 'run-hook.mjs'), source);
      cleanup = await adapter.setup(ctx);
      const context = { sessionID: 'broken', system: [] };
      await ctx.hooks.get('session.context')(context);
      assert.deepEqual(context.system, []);
      await cleanup(); cleanup = null;
    }
  } finally { await cleanup?.(); rmSync(dir, { recursive: true, force: true }); }
});

test('failed writes, reads and broken payloads degrade without claiming edits', async () => {
  const dir = project(); let cleanup;
  try {
    const ctx = opencodeContext(dir); cleanup = await plugin.setup(ctx);
    for (const event of [null, {}, { tool: 'edit', status: 'error', input: { filePath: join(dir, 'docs', 'x.md') } }, { tool: 'read', status: 'completed', input: { filePath: join(dir, 'docs', 'x.md') } }]) await ctx.hooks.get('tool.execute.after')(event);
    ctx.session.get = async () => { throw new Error('unavailable'); };
    await ctx.hooks.get('session.prompt')({ sessionID: 'unavailable', prompt: { text: 'texto' } });
    assert.equal(existsSync(join(dir, '.claude', '.confluence-pending')), false);
    assert.equal(existsSync(join(dir, '.claude', 'session-prompts-unavailable.log')), false);
  } finally { await cleanup?.(); rmSync(dir, { recursive: true, force: true }); }
});
