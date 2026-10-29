import test from 'node:test';
import assert from 'node:assert/strict';
import {spawn, spawnSync} from 'node:child_process';
import {cpSync, existsSync, mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join, resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {opencodeContext} from './helpers/opencode-context.mjs';
const root = resolve('.');
const roles = JSON.parse(readFileSync(join(root, 'agent-kits/shared/native-roles.json'), 'utf8'));
function fixture() {
  const dir = mkdtempSync(join(tmpdir(), 'custom-agents-prefilter-'));
  const shared = join(dir, 'agent-kits/shared');
  mkdirSync(shared, {recursive: true});
  cpSync(join(root, 'hooks'), join(dir, 'hooks'), {recursive: true});
  writeFileSync(join(shared, 'native-roles.json'), JSON.stringify(roles));
  return {dir, shared, launcher: join(dir, 'hooks/run-hook.mjs'), marker: join(dir, 'python-called')};
}
function invoke(f, runtime, payload, missing = false) {
  return spawnSync(process.execPath, [f.launcher, 'native-guardrail', `--runtime=${runtime}`], {
    cwd: f.dir, input: typeof payload === 'string' || Buffer.isBuffer(payload) ? payload : JSON.stringify(payload),
    encoding: 'utf8', timeout: 12000,
    env: {...process.env, CLAUDE_PROJECT_DIR: f.dir,
      CUSTOM_AGENTS_PYTHON: missing ? join(f.dir, 'missing-python') : process.env.TEST_PYTHON || 'python'},
  });
}
for (const runtime of ['claude', 'codex', 'opencode']) {
  test(`${runtime}: unprotected native identity skips Python even when unavailable`, () => {
    const f = fixture();
    try {
      const result = invoke(f, runtime, {tool_name: 'Bash', tool_input: {command: 'PRIVATE_PREFILTER_PAYLOAD'}}, true);
      assert.equal(result.status, 0, result.stderr);
      assert.equal(result.stderr, '', 'a valid unprotected identity must not attempt Python');
      if (runtime === 'opencode') assert.deepEqual(JSON.parse(result.stdout), {decision: 'continue', role: null, reason: null, diagnostic: null});
      else assert.equal(result.stdout, '');
      assert.equal(existsSync(f.marker), false);
    } finally {rmSync(f.dir, {recursive: true, force: true});}
  });
  for (const role of ['implementer', 'architect']) test(`${runtime}: exact ${role} identity still launches the contained evaluator`, () => {
    const f = fixture();
    try {
      // Build the result as data, never Python source from a consumer payload.
      writeFileSync(join(f.shared, 'native-guardrail.py'), `import pathlib\npathlib.Path(${JSON.stringify(f.marker)}).write_text('called')\nprint(${JSON.stringify(JSON.stringify({decision: 'deny', role, reason: 'Protected mutation', diagnostic: null}))})\n`);
      const result = invoke(f, runtime, {[runtime === 'opencode' ? 'agent' : 'agent_type']: roles.runtimes[runtime][role]});
      assert.equal(result.status, 0, result.stderr);
      assert.equal(readFileSync(f.marker, 'utf8'), 'called');
      const output = JSON.parse(result.stdout);
      if (runtime === 'opencode') assert.equal(output.decision, 'deny');
      else assert.equal(output.hookSpecificOutput.permissionDecision, 'deny');
    } finally {rmSync(f.dir, {recursive: true, force: true});}
  });
}
for (const [name, bytes] of [['missing', undefined], ['invalid', '{'], ['unsupported', JSON.stringify({...roles, schema_version: 999})], ['oversized', ' '.repeat(65537)], ['invalid-utf8', Buffer.from([0xff])], ['bom', '\ufeff' + JSON.stringify(roles)]]) {
  test(`uncertain role map ${name} falls back to Python and its existing diagnostic`, () => {
    const f = fixture();
    try {
      if (bytes === undefined) rmSync(join(f.shared, 'native-roles.json'));
      else writeFileSync(join(f.shared, 'native-roles.json'), bytes);
      const native = readFileSync(join(root, 'agent-kits/shared/native-guardrail.py'), 'utf8');
      writeFileSync(join(f.shared, 'native-guardrail.py'), `import pathlib\npathlib.Path(${JSON.stringify(f.marker)}).write_text('called')\n` + native);
      const result = invoke(f, 'opencode', {});
      assert.equal(result.status, 0, result.stderr);
      assert.equal(readFileSync(f.marker, 'utf8'), 'called');
      assert.equal(JSON.parse(result.stdout).diagnostic, 'role-map-unavailable');
    } finally {rmSync(f.dir, {recursive: true, force: true});}
  });
}

for (const when of ['before-setup', 'after-setup']) test(`OpenCode uncertain map ${when} delegates to the Python diagnostic`, async () => {
  const f = fixture();
  let cleanup;
  const originalWarn = console.warn, warnings = [];
  try {
    const native = readFileSync(join(root, 'agent-kits/shared/native-guardrail.py'), 'utf8');
    writeFileSync(join(f.shared, 'native-guardrail.py'), `import pathlib\npathlib.Path(${JSON.stringify(f.marker)}).write_text('called')\n` + native);
    const entry = join(f.dir, 'hooks/prefilter-adapter.mjs');
    writeFileSync(entry, readFileSync(join(root, 'hooks/opencode-plugin.js')));
    const {default: plugin} = await import(pathToFileURL(entry));
    console.warn = message => warnings.push(String(message));
    if (when === 'before-setup') writeFileSync(join(f.shared, 'native-roles.json'), '{');
    const ctx = opencodeContext(f.dir);
    cleanup = await plugin.setup(ctx);
    if (when === 'after-setup') writeFileSync(join(f.shared, 'native-roles.json'), '{');
    await ctx.hooks.get('tool.execute.before')({sessionID: 'owned', agent: 'main', tool: 'read', input: {}});
    assert.equal(existsSync(f.marker), true, 'a map failure must reach the contained Python diagnostic');
    assert.ok(warnings.some(value => value.includes('role guard unavailable')));
  } finally {await cleanup?.(); console.warn = originalWarn; rmSync(f.dir, {recursive: true, force: true});}
});

for (const [name, input, diagnostic] of [
  ['invalid-json', Buffer.from('{'), 'input-invalid-json'],
  ['invalid-utf8', Buffer.concat([Buffer.from('{"value":"'), Buffer.from([0xff]), Buffer.from('"}')]), 'input-invalid-json'],
  ['bom', Buffer.from('\ufeff{}'), 'input-invalid-json'],
  ['over-limit', Buffer.alloc(65537, 32), 'input-too-large'],
]) test(`uncertain input ${name} retains the native Python diagnostic`, () => {
  const f = fixture();
  try {
    const native = readFileSync(join(root, 'agent-kits/shared/native-guardrail.py'), 'utf8');
    writeFileSync(join(f.shared, 'native-guardrail.py'), `import pathlib\npathlib.Path(${JSON.stringify(f.marker)}).write_text('called')\n` + native);
    const result = invoke(f, 'opencode', input);
    assert.equal(result.status, 0, result.stderr);
    assert.equal(readFileSync(f.marker, 'utf8'), 'called');
    assert.equal(JSON.parse(result.stdout).diagnostic, diagnostic);
  } finally {rmSync(f.dir, {recursive: true, force: true});}
});

for (const shiftClock of [false, true]) test(`unclosed input has a deadline (backward clock: ${shiftClock})`, {timeout: 12000}, async () => {
  const f = fixture();
  let child, watchdog;
  try {
    const preload = shiftClock ? ['--import', 'data:text/javascript,let t=Date.now();Date.now=()=>t-=60000;'] : [];
    child = spawn(process.execPath, [...preload, f.launcher, 'native-guardrail', '--runtime=opencode'], {
      cwd: f.dir, env: {...process.env, CUSTOM_AGENTS_PYTHON: join(f.dir, 'missing-python')}, stdio: ['pipe', 'pipe', 'pipe'],
    });
    let output = '';
    child.stdout.setEncoding('utf8'); child.stdout.on('data', chunk => output += chunk);
    child.stderr.resume(); child.stdin.on('error', () => {});
    watchdog = setTimeout(() => child.kill('SIGKILL'), 10000);
    child.stdin.write('{"agent":"PRIVATE_UNFINISHED_PAYLOAD"');
    const code = await new Promise(resolve => child.on('close', resolve));
    assert.equal(code, 0);
    assert.equal(JSON.parse(output).diagnostic, 'guard-unavailable');
    assert.equal(output.includes('PRIVATE_UNFINISHED_PAYLOAD'), false);
  } finally {clearTimeout(watchdog); child?.stdin.destroy(); child?.kill('SIGKILL'); rmSync(f.dir, {recursive: true, force: true});}
});
