import test from 'node:test';
import assert from 'node:assert/strict';
import { cpSync, mkdtempSync, mkdirSync, writeFileSync, readFileSync, readdirSync, rmSync, existsSync } from 'node:fs';
import { execFileSync, spawn } from 'node:child_process';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
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

test('the cached context is invalidated by its signature, not by events (H-46)', async () => {
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
    // The capture log of an established session already exists when the context is first built.
    writeFileSync(join(dir,'.claude','session-prompts-cache.log'),'turn 0');
    assert.equal(await call(), 'context 1'); assert.equal(await call(), 'context 1');
    // Events that leave the canonical trees untouched never recompute the context.
    await ctx.hooks.get('tool.execute.after')({sessionID:'cache',tool:'read',status:'completed'});
    assert.equal(await call(), 'context 1');
    await ctx.hooks.get('tool.execute.after')({sessionID:'cache',tool:'bash',status:'completed'});
    assert.equal(await call(), 'context 1');
    // A prompt appends to its capture log under .claude/: volatile noise, not part of the signature.
    await ctx.hooks.get('session.prompt')({sessionID:'cache',prompt:{text:'next turn'}});
    writeFileSync(join(dir,'.claude','session-prompts-cache.log'),'turn 1');
    assert.equal(await call(), 'context 1');
    writeFileSync(join(dir,'.claude','session-prompts-cache.log'),'turn 1\nturn 2');
    assert.equal(await call(), 'context 1');
    // No time-to-live either: the same signature is reused however long the session runs.
    const clock = Date.now;
    try { Date.now = () => clock() + 3600000; assert.equal(await call(), 'context 1'); }
    finally { Date.now = clock; }
    // A change in the canonical files does recompute.
    mkdirSync(join(dir,'docs','roadmap','fixture'));
    writeFileSync(join(dir,'docs','roadmap','fixture','tasks.md'),'ledger changed');
    assert.equal(await call(), 'context 2');
    assert.equal(await call(), 'context 2');
    mkdirSync(join(dir,'docs','knowledge'),{recursive:true});
    writeFileSync(join(dir,'docs','knowledge','memory.md'),'memory changed');
    assert.equal(await call(), 'context 3');
    writeFileSync(join(dir,'.claude','dev.json'),'{}');
    assert.equal(await call(), 'context 4');
    assert.equal(await call('other-session'), 'context 5');
    writeFileSync(join(dir,'.claude','dev.json'),'{"sesion":{"journal":{"dir":"own-queue"}}}');
    assert.equal(await call('other-session'), 'context 6');
    assert.equal(await call('other-session'), 'context 7');
    writeFileSync(join(dir,'.claude','dev.json'),'{');
    assert.equal(await call('other-session'), 'context 8');
    assert.equal(await call('other-session'), 'context 9');
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
    // The canonical files change while the context is being built: the signature differs, nothing is saved.
    mkdirSync(join(dir,'docs','knowledge'),{recursive:true});
    writeFileSync(join(dir,'docs','knowledge','late.md'),'changed while computing');
    await pending;
    const second={sessionID:'concurrent',system:[]}; await ctx.hooks.get('session.context')(second);
    assert.equal(second.system[0].text,'context 2');
  } finally { await cleanup?.(); rmSync(dir, { recursive: true, force: true }); }
});

async function isolatedPlugin(dir, launcher, changeCatalog) {
  const folder = join(dir, 'hooks'); mkdirSync(folder, { recursive: true });
  writeFileSync(join(dir, 'package.json'), '{"type":"module"}');
  let source = readFileSync(new URL('../hooks/opencode-plugin.js', import.meta.url), 'utf8');
  if (changeCatalog) {
    const expression = /(\/\/ custom-agents hook-catalog:start\r?\nconst hookCatalog = JSON\.parse\(`)([\s\S]*?)(`\);\r?\n\/\/ custom-agents hook-catalog:end)/;
    const match = source.match(expression);
    assert.ok(match, 'The adapter must carry its own strict JSON registration catalog');
    const catalog = JSON.parse(match[2]); changeCatalog(catalog);
    source = source.replace(expression, (_, before, body, after) => before + JSON.stringify(catalog) + after);
  }
  writeFileSync(join(folder, 'adapter.js'), source);
  writeFileSync(join(folder, 'run-hook.mjs'), launcher);
  return (await import(pathToFileURL(join(folder, 'adapter.js')).href)).default;
}

test('native adapter identifies its runtime independently of consumer payload', async () => {
  const dir = project(); let cleanup;
  try {
    const adapter = await isolatedPlugin(dir, `import fs from 'node:fs';
      if(process.argv[2]==='session-journal.sh') fs.writeFileSync('end-argv.json',JSON.stringify(process.argv.slice(2)));`);
    const ctx = opencodeContext(dir); cleanup = await adapter.setup(ctx);
    ctx.emit({ type: 'session.execution.succeeded', data: { sessionID: 'runtime-test', runtime: 'claude' } });
    await until(() => existsSync(join(dir, 'end-argv.json')));
    assert.deepEqual(JSON.parse(readFileSync(join(dir, 'end-argv.json'), 'utf8')), ['session-journal.sh', '--runtime=opencode']);
  } finally { await cleanup?.(); rmSync(dir, { recursive: true, force: true }); }
});

test('catalog binding and handler edits govern native registration and dispatch', async () => {
  const dir = project(); let cleanup;
  try {
    const adapter = await isolatedPlugin(dir, `process.stdout.write(JSON.stringify({systemMessage:process.argv[2]}));`, catalog => {
      const post = catalog.bindings.find(item => item.id === 'post');
      post.native_event = 'own.after'; post.handlers = ['progress-line.sh'];
      catalog.bindings.find(item => item.id === 'tool-activity').native_event = 'own.after'; // T-47: shares the event
    });
    const ctx = opencodeContext(dir); cleanup = await adapter.setup(ctx);
    assert.ok(ctx.hooks.has('tool.own.after'));
    assert.equal(ctx.hooks.has('tool.execute.after'), false);
    const event = { sessionID:'catalog', tool:'write', status:'completed', input:{filePath:'docs/own.md'}, result:{metadata:{own:true}} };
    await ctx.hooks.get('tool.own.after')(event);
    assert.deepEqual(event.result.metadata.customAgentsMessages, ['progress-line.sh']);
    assert.equal(event.result.metadata.own, true);
  } finally { await cleanup?.(); rmSync(dir, { recursive:true, force:true }); }
});

test('catalog stream events drive capture without changing native payload translation', async () => {
  const dir = project(); let cleanup;
  try {
    // Activity handlers may run independently; the stream fixture observes capture only.
    const adapter = await isolatedPlugin(dir, `import fs from 'node:fs';
      if(process.argv[2]==='session-journal.sh') fs.writeFileSync('stream-args.json',JSON.stringify(process.argv.slice(2)));`, catalog => {
      catalog.bindings.find(item => item.id === 'capture').native_events = ['own.completed'];
    });
    const ctx = opencodeContext(dir); cleanup = await adapter.setup(ctx);
    ctx.emit({type:'session.execution.succeeded', data:{sessionID:'catalog'}});
    await new Promise(resolve => setTimeout(resolve, 100));
    assert.equal(existsSync(join(dir,'stream-args.json')), false);
    ctx.emit({type:'own.completed', data:{sessionID:'catalog'}});
    await until(() => existsSync(join(dir,'stream-args.json')));
    assert.deepEqual(JSON.parse(readFileSync(join(dir,'stream-args.json'),'utf8')), ['session-journal.sh','--runtime=opencode']);
  } finally { await cleanup?.(); rmSync(dir,{recursive:true,force:true}); }
});

test('catalog supervision budget terminates a delayed informational handler', async () => {
  const dir = project(); let cleanup;
  const saved = console.warn; console.warn = () => {};
  try {
    const adapter = await isolatedPlugin(dir, `import fs from 'node:fs';setTimeout(()=>fs.writeFileSync('late-catalog-handler','late'),3000);`, catalog => {
      catalog.bindings.find(item => item.id === 'prompt').timeout_ms = 1;
    });
    const ctx = opencodeContext(dir); cleanup = await adapter.setup(ctx);
    await ctx.hooks.get('session.prompt')({sessionID:'catalog-budget',prompt:{text:'own bounded fixture'}});
    await new Promise(resolve => setTimeout(resolve,400));
    assert.equal(existsSync(join(dir,'late-catalog-handler')), false);
  } finally { console.warn=saved; await cleanup?.(); rmSync(dir,{recursive:true,force:true}); }
});

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

test('Windows teardown completes when PATH omits system tools', {skip:process.platform !== 'win32'}, async () => {
  // The assertions read TAP lines; Node >= 23 defaults to the spec reporter even when piped.
  const args = ['--test', '--test-reporter=tap', '--test-name-pattern=^cleanup terminates its launcher tree and settles the pending hook$',
    fileURLToPath(import.meta.url)];
  const environment = {...process.env, PATH:dirname(process.execPath)};
  delete environment.NODE_TEST_CONTEXT; // Start an independent native test runner.
  const child = spawn(process.execPath, args, {
    env:environment, windowsHide:true,
    stdio:['ignore','pipe','pipe'],
  });
  let output = '', errors = '', expired = false;
  child.stdout.on('data', data => {output += data.toString('utf8');});
  child.stderr.on('data', data => {errors += data.toString('utf8');});
  const code = await new Promise((resolveDone, reject) => {
    const timer = setTimeout(() => {
      expired = true;
      if(child.exitCode === null && child.pid) {
        const taskkill = join(process.env.SystemRoot || process.env.WINDIR || 'C:\\Windows', 'System32', 'taskkill.exe');
        try {execFileSync(taskkill, ['/PID',String(child.pid),'/T','/F'], {windowsHide:true,stdio:'ignore'});} catch {}
      }
    }, 15000);
    child.once('error', error => {clearTimeout(timer);reject(error);});
    child.once('close', status => {clearTimeout(timer);resolveDone(status);});
  });
  assert.equal(expired, false, 'Teardown must settle with a restricted PATH');
  assert.equal(code, 0, errors || output);
  assert.match(output, /^# pass 1\s*$/m, 'The child must execute the real teardown case');
  assert.match(output, /^# fail 0\s*$/m);
});

test('cleanup of the real launcher reaches its Python process', async () => {
  const dir = project(); let cleanup, pid;
  try {
    const adapter = await isolatedPlugin(dir, readFileSync(new URL('../hooks/run-hook.mjs', import.meta.url), 'utf8'));
    cpSync(new URL('../hooks/runtime-supervisor.py', import.meta.url), join(dir, 'hooks', 'runtime-supervisor.py'));
    mkdirSync(join(dir, 'agent-kits', 'shared'), { recursive: true });
    const marker = join(dir, 'after-cleanup');
    const pidfile = join(dir, 'python.pid');
    writeFileSync(join(dir, 'agent-kits', 'shared', 'journal-capture.py'),
      `import os,time,pathlib\npathlib.Path(${JSON.stringify(pidfile)}).write_text(str(os.getpid()))\ntime.sleep(3)\npathlib.Path(${JSON.stringify(marker)}).write_text('late')\n`);
    const ctx = opencodeContext(dir); cleanup = await adapter.setup(ctx);
    ctx.emit({ type: 'session.execution.succeeded', data: { sessionID: 'own-real-cleanup' } });
    await until(() => existsSync(pidfile));
    pid = Number(readFileSync(pidfile, 'utf8'));
    await cleanup(); cleanup = null;
    await new Promise(resolve => setTimeout(resolve, 3300));
    assert.equal(existsSync(marker), false, 'Python must not continue after adapter cleanup');
  } finally {
    if (pid) {
      if (process.platform === 'win32') { try { execFileSync('taskkill', ['/PID', String(pid), '/T', '/F'], { stdio: 'ignore', windowsHide: true }); } catch {} }
      else { try { process.kill(pid, 'SIGKILL'); } catch {} }
    }
    await cleanup?.(); rmSync(dir, { recursive: true, force: true });
  }
});

test('real adapter teardown cleans background descendants after the capture parent exits', async () => {
  const dir = project(); let cleanup, pid;
  try {
    const adapter = await isolatedPlugin(dir, readFileSync(new URL('../hooks/run-hook.mjs', import.meta.url), 'utf8'));
    cpSync(new URL('../hooks/runtime-supervisor.py', import.meta.url), join(dir, 'hooks', 'runtime-supervisor.py'));
    mkdirSync(join(dir, 'agent-kits', 'shared'), { recursive: true });
    const marker = join(dir, 'late-background');
    const pidfile = join(dir, 'background.pid');
    writeFileSync(join(dir, 'agent-kits', 'shared', 'journal-capture.py'),
      `import subprocess,sys,pathlib\nchild=subprocess.Popen([sys.executable,'-I','-S','-c',"import time,pathlib; time.sleep(3); pathlib.Path("+repr(${JSON.stringify(marker)})+").write_text('late')"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)\npathlib.Path(${JSON.stringify(pidfile)}).write_text(str(child.pid))\n`);
    const ctx = opencodeContext(dir); cleanup = await adapter.setup(ctx);
    ctx.emit({ type: 'session.execution.succeeded', data: { sessionID: 'own-background' } });
    await until(() => existsSync(pidfile));
    pid = Number(readFileSync(pidfile, 'utf8'));
    await new Promise(resolve => setTimeout(resolve, 3300));
    assert.equal(existsSync(marker), false, 'normal completion must clean descendants with redirected pipes');
  } finally {
    if (pid) {
      if (process.platform === 'win32') { try { execFileSync('taskkill', ['/PID', String(pid), '/T', '/F'], { stdio: 'ignore', windowsHide: true }); } catch {} }
      else { try { process.kill(pid, 'SIGKILL'); } catch {} }
    }
    await cleanup?.(); rmSync(dir, { recursive: true, force: true });
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
    assert.deepEqual(event.result.metadata.customAgentsMessages, ['Own diagnostic', 'Own diagnostic']);
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


test('native execution start informs activity without premature session capture', async () => {
  const dir = project(); let cleanup;
  try {
    const adapter = await isolatedPlugin(dir, `import fs from 'node:fs';
      let input=''; process.stdin.setEncoding('utf8'); process.stdin.on('data',chunk=>input+=chunk);
      process.stdin.on('end',()=>{
        if(process.argv[2]==='agent-activity') fs.appendFileSync('activity-start.jsonl',JSON.stringify({argv:process.argv.slice(2),payload:JSON.parse(input)})+'\\n');
        if(process.argv[2]==='session-journal.sh') fs.appendFileSync('premature-capture.jsonl',input+'\\n');
      });`);
    const ctx = opencodeContext(dir); cleanup = await adapter.setup(ctx);
    for(let n=0;n<2;n++)ctx.emit({type:'session.execution.started',data:{sessionID:'started',prompt:'RAW-START-PROMPT'},error:'RAW-START-ERROR'});
    const trace=join(dir,'activity-start.jsonl');
    await until(()=>existsSync(trace)&&readFileSync(trace,'utf8').trim().split('\n').length===2);
    const rows=readFileSync(trace,'utf8').trim().split('\n').map(line=>JSON.parse(line));
    assert.equal(existsSync(join(dir,'premature-capture.jsonl')),false);
    for(const row of rows){
      assert.deepEqual(row.argv,['agent-activity','--runtime=opencode']);
      assert.deepEqual(row.payload,{type:'session.execution.started',data:{sessionID:'started'},cwd:dir});
    }
  }finally{await cleanup?.();rmSync(dir,{recursive:true,force:true});}
});

// panel-redesign T-47 (design O5, I-05, CA-42): OpenCode tool activity is a catalog binding of its own on
// tool.execute.after. The event promise resolves before the child ends (no await of the launcher) and the
// child is tracked for cleanup. Only the keys the store's summary whitelist reads cross the boundary.
test('catalog declares tool activity apart from the post and session activity bindings', async () => {
  const source = readFileSync(new URL('../hooks/opencode-plugin.js', import.meta.url), 'utf8');
  const catalog = JSON.parse(source.match(/hook-catalog:start\r?\nconst hookCatalog = JSON\.parse\(`([\s\S]*?)`\);/)[1]);
  const tool = catalog.bindings.find(item => item.id === 'tool-activity');
  assert.deepEqual([tool.domain, tool.native_event, tool.event, tool.behavior, tool.handlers, tool.timeout_ms],
    ['tool', 'execute.after', 'PostToolUse', 'informative', ['agent-activity'], 2500]);
  assert.deepEqual(catalog.bindings.find(item => item.id === 'post').handlers,
    ['mark-docs-pending.sh', 'ledger-post.py']);
  assert.equal(catalog.bindings.find(item => item.id === 'activity').domain, 'event');
});

test('tool activity resolves before its child ends and sends only summary arguments', async () => {
  const dir = project(); let cleanup;
  const heldLookups = [];
  const releaseLookups = () => { for (const release of heldLookups.splice(0)) release(); };
  try {
    const adapter = await isolatedPlugin(dir, `import fs from 'node:fs';
      let input=''; process.stdin.setEncoding('utf8'); process.stdin.on('data',chunk=>input+=chunk);
      process.stdin.on('end',()=>{ if(process.argv[2]!=='agent-activity') return;
        fs.appendFileSync('tool-activity.jsonl',JSON.stringify({argv:process.argv.slice(2),payload:JSON.parse(input)})+'\\n'); });`);
    const ctx = opencodeContext(dir); cleanup = await adapter.setup(ctx);
    // Hold the background lookup, so no child can start until the events return.
    // This proves non-awaiting causally instead of charging synchronous OS spawn
    // startup to a test of awaiting child completion. The 1s event bound remains.
    const ownLookup = ctx.session.get;
    let holdNext = false;
    ctx.session.get = (...args) => {
      if (!holdNext) return ownLookup(...args);
      holdNext = false;
      return new Promise(resolve => heldLookups.push(() => resolve(ownLookup(...args))));
    };
    const events = [
      { sessionID: 'tool-s', tool: 'read', status: 'completed', agent: 'build', input: { filePath: 'docs/x.md', content: 'RAW-CONTENT-FORBIDDEN' },
        result: { output: 'RAW-OUTPUT-FORBIDDEN' } },
      { sessionID: 'tool-s', tool: 'patch', status: 'error', input: { patchText: '  *** Update File: docs/a.md\n+RAW-PATCH-LINE' } },
    ];
    const started = Date.now();
    for (const event of events) {
      holdNext = true;
      let timer;
      try {
        await Promise.race([
          ctx.hooks.get('tool.execute.after')(event),
          new Promise((_, reject) => { timer = setTimeout(() => reject(new Error('event awaited background activity lookup')), 1000); }),
        ]);
      } finally { clearTimeout(timer); }
    }
    const elapsed = Date.now() - started;
    assert.ok(elapsed < 1000, `the event must not wait for the activity child (observed ${elapsed} ms)`);
    assert.equal(heldLookups.length, events.length, 'every activity lookup must remain pending after event completion');
    assert.equal(existsSync(join(dir, 'tool-activity.jsonl')), false);
    releaseLookups();
    const trace = join(dir, 'tool-activity.jsonl');
    await until(() => existsSync(trace) && readFileSync(trace, 'utf8').trim().split('\n').length === 2);
    const text = readFileSync(trace, 'utf8');
    assert.doesNotMatch(text, /RAW-(CONTENT|OUTPUT|PATCH)/);
    const rows = text.trim().split('\n').map(line => JSON.parse(line)).sort((a, b) => a.payload.data.tool.localeCompare(b.payload.data.tool));
    assert.deepEqual(rows.map(row => row.argv), [['agent-activity', '--runtime=opencode'], ['agent-activity', '--runtime=opencode']]);
    assert.deepEqual(rows[0].payload, { type: 'tool.execute.after', cwd: dir,
      data: { sessionID: 'tool-s', tool: 'patch', status: 'error', args: { command: '*** Update File: docs/a.md' } } });
    assert.deepEqual(rows[1].payload, { type: 'tool.execute.after', cwd: dir,
      data: { sessionID: 'tool-s', tool: 'read', status: 'completed', agent: 'build', args: { filePath: 'docs/x.md' } } });
  } finally { releaseLookups(); await cleanup?.(); rmSync(dir, { recursive: true, force: true }); }
});

test('tool activity child is tracked and cleanup terminates it', async () => {
  const dir = project(); let cleanup, pid;
  try {
    const adapter = await isolatedPlugin(dir, `import {spawn} from 'node:child_process'; import fs from 'node:fs';
      if(process.argv[2]==='agent-activity'){const child=spawn(process.execPath,['-e','setInterval(()=>{},1000)'],{stdio:'ignore'});
      fs.writeFileSync('tool-child.pid',String(child.pid));setInterval(()=>{},1000);}`);
    const ctx = opencodeContext(dir); cleanup = await adapter.setup(ctx);
    await ctx.hooks.get('tool.execute.after')({ sessionID: 'tool-cleanup', tool: 'bash', status: 'completed', input: { command: 'ls' } });
    await until(() => existsSync(join(dir, 'tool-child.pid')));
    pid = Number(readFileSync(join(dir, 'tool-child.pid'), 'utf8'));
    await cleanup(); cleanup = null;
    await until(() => { try { process.kill(pid, 0); return false; } catch { return true; } });
  } finally {
    if (pid) {
      if (process.platform === 'win32') { try { execFileSync('taskkill', ['/PID', String(pid), '/T', '/F'], { stdio: 'ignore', windowsHide: true }); } catch {} }
      else { try { process.kill(pid, 'SIGKILL'); } catch {} }
    }
    await cleanup?.(); rmSync(dir, { recursive: true, force: true });
  }
});

test('tool activity ignores foreign sessions and keeps the post notifications', async () => {
  const dir = project(); let cleanup;
  try {
    const adapter = await isolatedPlugin(dir, `import fs from 'node:fs';
      let input=''; process.stdin.setEncoding('utf8'); process.stdin.on('data',chunk=>input+=chunk);
      process.stdin.on('end',()=>{ if(process.argv[2]==='agent-activity') fs.appendFileSync('tool-activity.jsonl',input+'\\n');
        else process.stdout.write(JSON.stringify({systemMessage:process.argv[2]})); });`);
    const ctx = opencodeContext(dir); cleanup = await adapter.setup(ctx);
    const own = ctx.session.get;
    ctx.session.get = async () => ({ location: { directory: join(dir, 'elsewhere') } });
    await ctx.hooks.get('tool.execute.after')({ sessionID: 'foreign', tool: 'bash', status: 'completed', input: { command: 'ls' } });
    await new Promise(resolve => setTimeout(resolve, 300));
    assert.equal(existsSync(join(dir, 'tool-activity.jsonl')), false);
    ctx.session.get = own;
    const event = { sessionID: 'own', tool: 'write', status: 'completed', input: { filePath: 'docs/own.md' }, result: { metadata: {} } };
    await ctx.hooks.get('tool.execute.after')(event);
    assert.deepEqual(event.result.metadata.customAgentsMessages, ['mark-docs-pending.sh', 'ledger-post.py']);
    await until(() => existsSync(join(dir, 'tool-activity.jsonl')));
  } finally { await cleanup?.(); rmSync(dir, { recursive: true, force: true }); }
});

// panel-redesign T-47 fix1 (B2): the unawaited activity binding is dispatched BEFORE the awaited post
// handlers share execute.after, so its observed_at is not delayed by the serial notifications.
test('tool activity is dispatched before the awaited post handlers of the same event', async () => {
  const dir = project(); let cleanup;
  try {
    const adapter = await isolatedPlugin(dir, `import fs from 'node:fs';
      fs.appendFileSync('starts.jsonl', JSON.stringify({ handler: process.argv[2], at: Date.now() }) + '\\n');
      let input=''; process.stdin.setEncoding('utf8'); process.stdin.on('data',chunk=>input+=chunk);
      process.stdin.on('end',()=>{ if(process.argv[2]!=='agent-activity') setTimeout(()=>{},400); });`);
    const ctx = opencodeContext(dir); cleanup = await adapter.setup(ctx);
    await ctx.hooks.get('tool.execute.after')({ sessionID: 'order', tool: 'write', status: 'completed',
      input: { filePath: 'docs/order.md' }, result: { metadata: {} } });
    const trace = join(dir, 'starts.jsonl');
    await until(() => existsSync(trace) && readFileSync(trace, 'utf8').trim().split('\n').length === 3);
    const rows = readFileSync(trace, 'utf8').trim().split('\n').map(line => JSON.parse(line));
    assert.deepEqual(rows.map(row => row.handler).sort(), ['agent-activity', 'ledger-post.py', 'mark-docs-pending.sh']);
    const activity = rows.find(row => row.handler === 'agent-activity');
    const firstPost = rows.filter(row => row.handler !== 'agent-activity').sort((a, b) => a.at - b.at)[0];
    assert.ok(activity.at < firstPost.at + 300,
      'activity started ' + (activity.at - firstPost.at) + ' ms after the first post handler: it waited for the serial posts');
  } finally { await cleanup?.(); rmSync(dir, { recursive: true, force: true }); }
});

// f4fix1 gap 3, 10 and 11 (Phase 4, review attempt 1).
const flowLauncher = `import fs from 'node:fs';
  const script = process.argv[2];
  if (script === 'session-context.sh') {
    const n = fs.existsSync('runs') ? Number(fs.readFileSync('runs','utf8')) + 1 : 1;
    fs.writeFileSync('runs', String(n));
    fs.rmSync('.claude/journal/outbox', {recursive: true, force: true});   // the replay consumes the queue
    process.stdout.write(JSON.stringify({hookSpecificOutput:{additionalContext:'context ' + n}}));
  }
  if (script === 'session-journal.sh') {
    // What the real capture leaves behind on every turn: a queued envelope and a rewritten journal entry
    // whose volatile lines (materializado_en, turnos) change while what the session block quotes does not.
    const stamp = String(Date.now()) + Math.random();
    fs.mkdirSync('.claude/journal/outbox', {recursive: true});
    fs.writeFileSync('.claude/journal/outbox/' + stamp + '.json', '{}');
    fs.mkdirSync('docs/knowledge/journal', {recursive: true});
    const resumen = fs.existsSync('resumen.txt') ? fs.readFileSync('resumen.txt', 'utf8') : 'primer prompt';
    fs.writeFileSync('docs/knowledge/journal/2026-01-01-demo.md', ['---', 'fecha: "2026-01-01"', 'session_id: "flow"',
      'reason: "other"', 'iniciativa: "demo"', 'resumen: "' + resumen + '"', 'turnos: ' + stamp.length,
      'materializado_en: "' + stamp + '"', 'decisiones: []', 'marcadores_cerrados:', '  - "m-' + stamp + '"', '---', '', '# Journal'].join('\\n'));
    fs.writeFileSync('docs/knowledge/journal/README.md', 'index ' + stamp);
    fs.appendFileSync('captures.log', 'x\\n');
  }`;

async function runFlowTurn(ctx, dir, sessionID, captured) {
  // started -> succeeded -> idle, the way the runtime emits a turn; both end events capture.
  ctx.emit({ type: 'session.execution.started', data: { sessionID } });
  ctx.emit({ type: 'session.execution.succeeded', data: { sessionID } });
  ctx.emit({ type: 'session.status', data: { sessionID, status: { type: 'idle' } } });
  await until(() => existsSync(join(dir, 'captures.log')) && readFileSync(join(dir, 'captures.log'), 'utf8').split('\n').filter(Boolean).length >= captured);
  await new Promise(resolve => setTimeout(resolve, 150));
}

test('f4fix1 gap 3: the context survives real turn events when what it quotes did not change', async () => {
  const dir = project(); let cleanup;
  try {
    const adapter = await isolatedPlugin(dir, flowLauncher);
    const ctx = opencodeContext(dir); cleanup = await adapter.setup(ctx);
    const call = async (sessionID = 'flow') => {
      const event = { sessionID, system: [] }; await ctx.hooks.get('session.context')(event); return event.system[0].text;
    };
    const first = await call();
    assert.match(first, /^context \d+$/);
    await runFlowTurn(ctx, dir, 'flow', 2);                 // the capture wrote envelope + journal entry
    const second = await call();
    assert.notEqual(second, first);                         // first sight of the entry: it is new content
    await runFlowTurn(ctx, dir, 'flow', 4);                 // second turn: only volatile lines and the queue changed
    assert.equal(await call(), second);                     // reused across the turn
    await runFlowTurn(ctx, dir, 'flow', 6);
    assert.equal(await call(), second);
    writeFileSync(join(dir, 'resumen.txt'), 'otro encargo');   // what the session block quotes does change
    await runFlowTurn(ctx, dir, 'flow', 8);
    const third = await call();
    assert.notEqual(third, second);
    assert.equal(await call(), third);
  } finally { await cleanup?.(); rmSync(dir, { recursive: true, force: true }); }
});

test('f4fix1 gap 11: a delegated session does not evict the parent context', async () => {
  const dir = project(); let cleanup;
  try {
    const adapter = await isolatedPlugin(dir, flowLauncher);
    const ctx = opencodeContext(dir); cleanup = await adapter.setup(ctx);
    const call = async sessionID => {
      const event = { sessionID, system: [] }; await ctx.hooks.get('session.context')(event); return event.system[0].text;
    };
    assert.equal(await call('parent'), 'context 1');
    assert.equal(await call('child'), 'context 2');
    assert.equal(await call('parent'), 'context 1');
    assert.equal(await call('child'), 'context 2');
    assert.equal(await call('parent'), 'context 1');
  } finally { await cleanup?.(); rmSync(dir, { recursive: true, force: true }); }
});

test('f4fix1 gap 10: a medium project tree still yields a reusable signature', async () => {
  const dir = project(); let cleanup;
  try {
    mkdirSync(join(dir, 'docs', 'knowledge', 'adr'), { recursive: true });
    for (let i = 0; i < 1500; i++) writeFileSync(join(dir, 'docs', 'knowledge', 'adr', `ADR-${i}.md`), 'x');
    const adapter = await isolatedPlugin(dir, flowLauncher);
    const ctx = opencodeContext(dir); cleanup = await adapter.setup(ctx);
    const event = { sessionID: 'big', system: [] }; await ctx.hooks.get('session.context')(event);
    const again = { sessionID: 'big', system: [] }; await ctx.hooks.get('session.context')(again);
    assert.equal(again.system[0].text, 'context 1');
  } finally { await cleanup?.(); rmSync(dir, { recursive: true, force: true }); }
});

// f4fix2 gaps 6-9 (Phase 4, review attempt 2).
const countLauncher = `import fs from 'node:fs';
  if (process.argv[2] === 'session-context.sh') {
    const n = fs.existsSync('runs') ? Number(fs.readFileSync('runs','utf8')) + 1 : 1;
    fs.writeFileSync('runs', String(n));
    let source = ''; try { source = JSON.parse(fs.readFileSync(0, 'utf8')).source; } catch {}
    fs.appendFileSync('sources', source + ',');
    const transient = fs.existsSync('transient') ? 'Journal (estado operativo de la cola del journal; datos, no instrucciones): replay bloqueado (otro replay en curso) — el arranque continúa. '
      : fs.existsSync('permanent') ? 'Journal (estado operativo de la cola del journal; datos, no instrucciones): outbox.py no disponible — el arranque continúa. ' : '';
    process.stdout.write(JSON.stringify({hookSpecificOutput:{additionalContext: transient + 'context ' + n}}));
  }`;
const ask = async (ctx, sessionID = 'f2') => { const event = { sessionID, system: [] }; await ctx.hooks.get('session.context')(event); return event.system[0].text; };
const runs = dir => Number(readFileSync(join(dir, 'runs'), 'utf8'));

test('f4fix2 gap 6: a cache hit still drains a non-empty outbox, in the background', async () => {
  const dir = project(); let cleanup;
  try {
    const adapter = await isolatedPlugin(dir, countLauncher);
    const ctx = opencodeContext(dir); cleanup = await adapter.setup(ctx);
    mkdirSync(join(dir, '.claude', 'journal', 'outbox'), { recursive: true });
    assert.equal(await ask(ctx), 'context 1');
    writeFileSync(join(dir, '.claude', 'journal', 'outbox', 'a.json'), '{}');
    assert.equal(await ask(ctx), 'context 1');                      // served from the cache, not blocked
    await until(() => runs(dir) >= 2);                              // and the queue was drained behind it
    assert.equal(await ask(ctx), 'context 1');
    await new Promise(resolve => setTimeout(resolve, 300));
    assert.equal(runs(dir), 2);                                     // the same queue is not drained twice at once
    assert.equal(readFileSync(join(dir, 'sources'), 'utf8').split(',').filter(Boolean).pop(), 'drain');   // gap 5: replay only
    const clock = Date.now;                                         // gap 3: a queue that did not move is retried later
    try { Date.now = () => clock() + 31000; assert.equal(await ask(ctx), 'context 1'); await until(() => runs(dir) >= 3); }
    finally { Date.now = clock; }
  } finally { await cleanup?.(); rmSync(dir, { recursive: true, force: true }); }
});

test('f4fix2 gap 7: the transient replay notice is not cached and the cost markers sign as present or absent', async () => {
  const dir = project(); let cleanup;
  try {
    const adapter = await isolatedPlugin(dir, countLauncher);
    const ctx = opencodeContext(dir); cleanup = await adapter.setup(ctx);
    writeFileSync(join(dir, 'transient'), '1');
    assert.match(await ask(ctx), /context 1/); assert.match(await ask(ctx), /context 2/);   // blocked replay: never cached
    rmSync(join(dir, 'transient'));
    assert.equal(await ask(ctx), 'context 3'); assert.equal(await ask(ctx), 'context 3');
    writeFileSync(join(dir, 'permanent'), '1');                      // gap 4: a permanent notice is cached like any text
    const permanent = await ask(ctx, 'other'); assert.match(permanent, /outbox.py no disponible.*context 4/);
    assert.equal(await ask(ctx, 'other'), permanent);
    rmSync(join(dir, 'permanent'));
    const journal = join(dir, 'docs', 'knowledge', 'journal'); mkdirSync(journal, { recursive: true });
    const entry = markers => ['---', 'fecha: "2026-01-01"', 'session_id: "m"', 'iniciativa: "demo"', 'resumen: "Sesión de trabajo"',
      'decisiones: []', ...markers, '---', ''].join(String.fromCharCode(10));
    writeFileSync(join(journal, '2026-01-01-demo.md'), entry(['marcadores_cerrados: []']));
    assert.equal(await ask(ctx), 'context 5');
    writeFileSync(join(journal, '2026-01-01-demo.md'), entry(['marcadores_cerrados: []']));
    assert.equal(await ask(ctx), 'context 5');
    writeFileSync(join(journal, '2026-01-01-demo.md'), entry(['marcadores_cerrados:', '  - "x/y"']));
    assert.equal(await ask(ctx), 'context 6');                      // present markers: the entry is no longer a placeholder
  } finally { await cleanup?.(); rmSync(dir, { recursive: true, force: true }); }
});

test('f4fix2 gaps 8 and 9: deep testing/ evidence and the confluence marker do not disable or invalidate the cache', async () => {
  const dir = project(); let cleanup;
  try {
    const deep = join(dir, 'docs', 'roadmap', 'x', 'testing', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i');
    mkdirSync(deep, { recursive: true }); writeFileSync(join(deep, 'fixture.md'), 'x');
    const adapter = await isolatedPlugin(dir, countLauncher);
    const ctx = opencodeContext(dir); cleanup = await adapter.setup(ctx);
    assert.equal(await ask(ctx), 'context 1'); assert.equal(await ask(ctx), 'context 1');
    writeFileSync(join(dir, '.claude', '.confluence-pending'), 'docs/a.md');
    assert.equal(await ask(ctx), 'context 1');
    writeFileSync(join(dir, '.claude', '.confluence-pending'), 'docs/a.md\ndocs/b.md');
    assert.equal(await ask(ctx), 'context 1');
  } finally { await cleanup?.(); rmSync(dir, { recursive: true, force: true }); }
});
