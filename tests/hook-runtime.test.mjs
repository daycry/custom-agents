import test from 'node:test';
import assert from 'node:assert/strict';
import { spawn, spawnSync } from 'node:child_process';
import { cpSync, existsSync, mkdtempSync, mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import plugin from '../hooks/opencode-plugin.js';
import { opencodeContext, until } from './helpers/opencode-context.mjs';

const root = resolve('.');
const runner = join(root, 'hooks', 'run-hook.mjs');
function invoke(hook, payload, cwd) {
  return spawnSync(process.execPath, [runner, hook], {
    cwd, input: JSON.stringify(payload), encoding: 'utf8', timeout: ['session-journal.sh', 'user-prompt-capture.sh'].includes(hook) ? 3000 : 25000,
    env: { ...process.env, CLAUDE_PROJECT_DIR: cwd, CUSTOM_AGENTS_PYTHON: process.env.TEST_PYTHON || 'python' },
  });
}

test('SessionStart injects JSON context through Git Bash and native Python', () => {
  const dir = mkdtempSync(join(tmpdir(), 'custom-agents-start-'));
  try {
    const result = spawnSync(process.execPath, [runner, 'session-context.sh'], {
      cwd: dir, input: JSON.stringify({ cwd: dir, source: 'startup', session_id: 'hook-runtime-start' }),
      encoding: 'utf8', timeout: 25000, env: { ...process.env, CLAUDE_PROJECT_DIR: dir },
    });
    assert.equal(result.status, 0, result.stderr);
    assert.equal(result.stderr, '');
    const output = JSON.parse(result.stdout);
    assert.equal(output.hookSpecificOutput.hookEventName, 'SessionStart');
    assert.ok(output.hookSpecificOutput.additionalContext.length > 0);
  } finally { rmSync(dir, { recursive: true, force: true }); }
});

test('OpenCode session.idle uses the shared runner and persists an envelope', async () => {
  const dir = mkdtempSync(join(tmpdir(), 'custom-agents-opencode-'));
  let cleanup;
  try {
    mkdirSync(join(dir, 'docs', 'roadmap'), { recursive: true });
    const ctx = opencodeContext(dir);
    cleanup = await plugin.setup(ctx);
    ctx.emit({ type: 'session.idle', location: ctx.location, data: { sessionID: 'opencode-hook-test' } });
    await until(() => existsSync(join(dir, '.claude', 'journal', 'outbox')) && readdirSync(join(dir, '.claude', 'journal', 'outbox')).some(f => f.endsWith('.json')));
    assert.equal(readdirSync(join(dir, '.claude', 'journal', 'outbox')).filter(f => f.endsWith('.json')).length, 1);
  } finally { await cleanup?.(); rmSync(dir, { recursive: true, force: true }); }
});

test('native capture and SessionEnd persist UTF8 data inside 3s', () => {
  const dir = mkdtempSync(join(tmpdir(), 'custom-agents-hooks-'));
  try {
    mkdirSync(join(dir, 'docs', 'roadmap'), { recursive: true });
    const prompt = { session_id: 'hook-runtime-test', cwd: dir, prompt: 'Decidimos usar Python 🐍' };
    const captured = invoke('user-prompt-capture.sh', prompt, dir);
    assert.equal(captured.status, 0, captured.stderr);
    assert.match(readFileSync(join(dir, '.claude', 'session-prompts-hook-runtime-test.log'), 'utf8'), /Python 🐍/);
    const ended = invoke('session-journal.sh', { ...prompt, reason: 'other' }, dir);
    assert.equal(ended.status, 0, ended.stderr);
    assert.equal(ended.stdout, '');
    assert.equal(readdirSync(join(dir, '.claude', 'journal', 'outbox')).filter(f => f.endsWith('.json')).length, 1);
  } finally { rmSync(dir, { recursive: true, force: true }); }
});

test('SessionEnd capture is independent of slow materialization startup', () => {
  const dir = mkdtempSync(join(tmpdir(), 'custom-agents-teardown-'));
  try {
    const bundle = join(dir, 'plugin');
    cpSync(join(root, 'hooks'), join(bundle, 'hooks'), { recursive: true });
    cpSync(join(root, 'agent-kits', 'shared'), join(bundle, 'agent-kits', 'shared'), { recursive: true });
    const journal = join(bundle, 'agent-kits', 'shared', 'journal.py');
    writeFileSync(journal, 'import time; time.sleep(2)\n' + readFileSync(journal, 'utf8'));
    mkdirSync(join(dir, 'docs', 'roadmap'), { recursive: true });
    const result = spawnSync(process.execPath, [join(bundle, 'hooks', 'run-hook.mjs'), 'session-journal.sh'], {
      cwd: dir, input: JSON.stringify({ cwd: dir, session_id: 'bounded-startup', reason: 'other' }),
      encoding: 'utf8', timeout: 5000,
      env: { ...process.env, CLAUDE_PROJECT_DIR: dir, CUSTOM_AGENTS_PYTHON: process.env.TEST_PYTHON || 'python' },
    });
    assert.equal(result.status, 0, result.stderr);
    assert.ok(existsSync(join(dir, '.claude', 'journal', 'outbox')), 'durable capture must not wait for materialization imports');
    assert.equal(readdirSync(join(dir, '.claude', 'journal', 'outbox')).filter(f => f.endsWith('.json')).length, 1);
  } finally { rmSync(dir, { recursive: true, force: true }); }
});

test('SessionEnd timeout terminates its child tree before returning', () => {
  const dir = mkdtempSync(join(tmpdir(), 'custom-agents-timeout-'));
  try {
    const bundle = join(dir, 'plugin');
    cpSync(join(root, 'hooks'), join(bundle, 'hooks'), { recursive: true });
    mkdirSync(join(bundle, 'agent-kits', 'shared'), { recursive: true });
    const marker = join(dir, 'orphan.txt');
    const program = `import subprocess, sys, time, pathlib\nchild = subprocess.Popen([sys.executable, '-I', '-S', '-c', "import time,pathlib; time.sleep(3); pathlib.Path(" + repr(${JSON.stringify(marker)}) + ").write_text('orphan')"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\npathlib.Path(${JSON.stringify(marker + '.started')}).write_text(str(child.pid))\ntime.sleep(10)\n`;
    writeFileSync(join(bundle, 'agent-kits', 'shared', 'journal-capture.py'), program);
    const result = spawnSync(process.execPath, [join(bundle, 'hooks', 'run-hook.mjs'), 'session-journal.sh'], {
      cwd: dir, input: '{}', encoding: 'utf8', timeout: 8000,
      env: { ...process.env, CUSTOM_AGENTS_PYTHON: process.env.TEST_PYTHON || 'python' },
    });
    assert.equal(result.status, 0, result.stderr);
    assert.ok(existsSync(marker + '.started'), 'fixture must actually spawn a descendant before timeout');
    spawnSync(process.execPath, ['-e', 'setTimeout(()=>{},3500)'], { timeout: 6000 });
    assert.equal(existsSync(marker), false, 'a timed-out hook must leave no live descendants');
  } finally { rmSync(dir, { recursive: true, force: true }); }
});

test('SessionEnd cleans descendants after its direct child has already exited', () => {
  const dir = mkdtempSync(join(tmpdir(), 'custom-agents-exited-parent-'));
  try {
    const bundle = join(dir, 'plugin');
    cpSync(join(root, 'hooks'), join(bundle, 'hooks'), { recursive: true });
    mkdirSync(join(bundle, 'agent-kits', 'shared'), { recursive: true });
    const marker = join(dir, 'orphan.txt');
    const program = `import subprocess, sys, pathlib\nchild = subprocess.Popen([sys.executable, '-I', '-S', '-c', "import time,pathlib; time.sleep(3); pathlib.Path(" + repr(${JSON.stringify(marker)}) + ").write_text('orphan')"])\npathlib.Path(${JSON.stringify(marker + '.started')}).write_text(str(child.pid))\n`;
    writeFileSync(join(bundle, 'agent-kits', 'shared', 'journal-capture.py'), program);
    const result = spawnSync(process.execPath, [join(bundle, 'hooks', 'run-hook.mjs'), 'session-journal.sh'], {
      cwd: dir, input: '{}', encoding: 'utf8', timeout: 8000,
      env: { ...process.env, CUSTOM_AGENTS_PYTHON: process.env.TEST_PYTHON || 'python' },
    });
    assert.equal(result.status, 0, result.stderr);
    assert.ok(existsSync(marker + '.started'), 'fixture must spawn its descendant');
    assert.equal(existsSync(marker), false, 'a completed direct child must not disable descendant cleanup');
  } finally { rmSync(dir, { recursive: true, force: true }); }
});

test('forced termination of the Windows launcher closes its descendant job', { skip: process.platform !== 'win32' }, async () => {
  const dir = mkdtempSync(join(tmpdir(), 'custom-agents-owner-kill-'));
  let launcher, descendant;
  try {
    const bundle = join(dir, 'plugin');
    cpSync(join(root, 'hooks'), join(bundle, 'hooks'), { recursive: true });
    mkdirSync(join(bundle, 'agent-kits', 'shared'), { recursive: true });
    const marker = join(dir, 'orphan.txt');
    writeFileSync(join(bundle, 'agent-kits', 'shared', 'journal-capture.py'),
      `import subprocess,sys,pathlib,time\nchild=subprocess.Popen([sys.executable,'-I','-S','-c',"import time,pathlib; time.sleep(3); pathlib.Path("+repr(${JSON.stringify(marker)})+").write_text('orphan')"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)\npathlib.Path(${JSON.stringify(marker + '.started')}).write_text(str(child.pid))\ntime.sleep(10)\n`);
    launcher = spawn(process.execPath, [join(bundle, 'hooks', 'run-hook.mjs'), 'session-journal.sh', '--runtime=codex'], {
      cwd: dir, stdio: ['pipe', 'ignore', 'ignore'],
      env: { ...process.env, CUSTOM_AGENTS_PYTHON: process.env.TEST_PYTHON || 'python' },
    });
    launcher.stdin.end('{}');
    await until(() => existsSync(marker + '.started'));
    descendant = Number(readFileSync(marker + '.started', 'utf8'));
    const closed = new Promise(resolve => launcher.on('close', resolve));
    launcher.kill('SIGKILL'); // Deliberately kill only Node, without taskkill /T.
    await closed;
    await new Promise(resolve => setTimeout(resolve, 3300));
    assert.equal(existsSync(marker), false, 'closing the owner must close the only Job Object handle');
  } finally {
    launcher?.kill('SIGKILL');
    if (descendant) spawnSync('taskkill', ['/PID', String(descendant), '/T', '/F'], { stdio: 'ignore', windowsHide: true });
    rmSync(dir, { recursive: true, force: true });
  }
});

test('unavailable Windows supervision skips business code without exposing its payload', { skip: process.platform !== 'win32' }, () => {
  const dir = mkdtempSync(join(tmpdir(), 'custom-agents-no-supervisor-'));
  try {
    const bundle = join(dir, 'plugin');
    cpSync(join(root, 'hooks'), join(bundle, 'hooks'), { recursive: true });
    rmSync(join(bundle, 'hooks', 'runtime-supervisor.py'));
    mkdirSync(join(bundle, 'agent-kits', 'shared'), { recursive: true });
    const marker = join(dir, 'business-ran');
    writeFileSync(join(bundle, 'agent-kits', 'shared', 'journal-capture.py'), `import pathlib\npathlib.Path(${JSON.stringify(marker)}).write_text('unsafe')\n`);
    const result = spawnSync(process.execPath, [join(bundle, 'hooks', 'run-hook.mjs'), 'session-journal.sh'], {
      cwd: dir, input: '{"prompt":"PRIVATE_SENTINEL"}', encoding: 'utf8', timeout: 3000,
      env: { ...process.env, CUSTOM_AGENTS_PYTHON: process.env.TEST_PYTHON || 'python' },
    });
    assert.equal(result.status, 0, result.stderr);
    assert.equal(existsSync(marker), false);
    assert.equal(result.stdout, '');
    assert.equal(result.stderr.includes('PRIVATE_SENTINEL'), false);
    assert.match(result.stderr, /supervision unavailable|hook failed/);
  } finally { rmSync(dir, { recursive: true, force: true }); }
});

test('malformed Windows job confirmation is rejected before forwarding diagnostics', { skip: process.platform !== 'win32' }, () => {
  const dir = mkdtempSync(join(tmpdir(), 'custom-agents-bad-confirmation-'));
  try {
    const bundle = join(dir, 'plugin');
    cpSync(join(root, 'hooks'), join(bundle, 'hooks'), { recursive: true });
    writeFileSync(join(bundle, 'hooks', 'runtime-supervisor.py'),
      "import sys,time\nprint('PRIVATE_BAD_CONFIRMATION',file=sys.stderr,flush=True)\ntime.sleep(5)\n");
    const result = spawnSync(process.execPath, [join(bundle, 'hooks', 'run-hook.mjs'), 'session-journal.sh'], {
      cwd: dir, input: '{}', encoding: 'utf8', timeout: 5000,
      env: { ...process.env, CUSTOM_AGENTS_PYTHON: process.env.TEST_PYTHON || 'python' },
    });
    assert.equal(result.status, 0, result.stderr);
    assert.equal(result.stdout, '');
    assert.equal(result.stderr.includes('PRIVATE_BAD_CONFIRMATION'), false);
    assert.match(result.stderr, /supervision unavailable/);
  } finally { rmSync(dir, { recursive: true, force: true }); }
});

test('unknown hook is never executed', () => {
  const result = invoke('../../install/install.mjs', {}, root);
  assert.equal(result.status, 0);
  assert.equal(result.stdout, '');
  assert.match(result.stderr, /unknown hook/);
});

test('Codex apply_patch updates docs flags and emits ledger warnings as JSON', () => {
  const dir = mkdtempSync(join(tmpdir(), 'custom-agents-patch-'));
  try {
    const path = join(dir, 'docs', 'roadmap', 'demo', 'tasks.md');
    mkdirSync(dirname(path), { recursive: true });
    writeFileSync(path, '# Ledger roto\n\n### T-01 — tarea\n- **Estado**: nonsense\n');
    const payload = { tool_name: 'apply_patch', cwd: dir, tool_input: { command: '*** Begin Patch\n*** Update File: docs/roadmap/demo/tasks.md\n@@\n-old\n+new\n*** End Patch' } };
    const result = invoke('mark-docs-pending.sh', payload, dir);
    assert.equal(result.status, 0, result.stderr);
    assert.ok(existsSync(join(dir, '.claude', '.confluence-pending')));
    const warning = spawnSync(process.execPath, [runner, 'ledger-lint-warn.sh'], {
      cwd: dir, input: JSON.stringify(payload), encoding: 'utf8', timeout: 20000,
      env: { ...process.env, CLAUDE_PROJECT_DIR: dir },
    });
    assert.equal(warning.status, 0, warning.stderr);
    assert.match(JSON.parse(warning.stdout).systemMessage, /incoherencias|Estado/i);
  } finally { rmSync(dir, { recursive: true, force: true }); }
});

test('Edit paths escaped by JSON retain progress, lint and sensitive-doc exclusions', () => {
  const dir = mkdtempSync(join(tmpdir(), 'custom-agents-edit-'));
  try {
    const path = join(dir, 'docs', 'roadmap', 'demo', 'tasks.md');
    mkdirSync(dirname(path), { recursive: true });
    cpSync(join(root, 'docs', 'roadmap', '2026-09-02-adversarial-review', 'tasks.md'), path);
    const payload = { tool_name: 'Edit', tool_input: { file_path: path.replaceAll('/', '\\') } };
    const progress = invoke('progress-line.sh', payload, dir);
    assert.equal(progress.status, 0, progress.stderr);
    assert.match(JSON.parse(progress.stdout).systemMessage, /demo/);
    writeFileSync(path, '# Ledger roto\n\n### T-01 — tarea\n- **Estado**: nonsense\n');
    const lint = invoke('ledger-lint-warn.sh', payload, dir);
    assert.equal(lint.status, 0, lint.stderr);
    assert.match(JSON.parse(lint.stdout).systemMessage, /incoherencias|Estado/i);
    const sensitive = { tool_name: 'Edit', tool_input: { file_path: join(dir, 'docs', 'security-scan', 'findings.md').replaceAll('/', '\\') } };
    const excluded = invoke('mark-docs-pending.sh', sensitive, dir);
    assert.equal(excluded.status, 0, excluded.stderr);
    assert.equal(existsSync(join(dir, '.claude', '.confluence-pending')), false);
    const changed = invoke('mark-docs-pending.sh', payload, dir);
    assert.equal(changed.status, 0, changed.stderr);
    assert.equal(existsSync(join(dir, '.claude', '.confluence-pending')), true);
  } finally { rmSync(dir, { recursive: true, force: true }); }
});

for (const mode of ['flat', 'cache', 'precedence']) for (const agent of ['implementer', 'architect']) test(`copied ${agent} retains its guard without CLAUDE_PLUGIN_ROOT (${mode})`, () => {
  const dir = mkdtempSync(join(tmpdir(), 'custom-agents-guard-'));
  try {
    const bundle = mode !== 'flat' ? join(dir, '.claude', 'plugins', 'cache', 'marketplace', 'custom-agents', '1.0.0') : join(dir, '.claude');
    cpSync(join(root, 'hooks'), join(bundle, 'hooks'), { recursive: true });
    mkdirSync(join(bundle, 'agent-kits', 'shared'), { recursive: true });
    cpSync(join(root, 'agent-kits', 'shared', 'guardrail-check.py'), join(bundle, 'agent-kits', 'shared', 'guardrail-check.py'));
    const text = readFileSync(join(root, 'agents', `${agent}.md`), 'utf8');
    const line = text.match(/^\s+command: (.+)$/m)[1];
    assert.ok(line.startsWith('node -e "'), 'copied guards use the portable Node entry');
    const home = mode === 'precedence' ? join(dir, 'user') : dir;
    if (mode === 'precedence') {
      const userHooks = join(home, '.claude', 'hooks');
      cpSync(join(root, 'hooks'), userHooks, { recursive: true });
      writeFileSync(join(userHooks, `${agent}-guardrail.sh`), `#!/usr/bin/env bash\nprintf '%s' '{"hookSpecificOutput":{"permissionDecision":"allow"}}'\n`);
    }
    const env = { ...process.env, CLAUDE_PROJECT_DIR: dir, HOME: home, USERPROFILE: home };
    delete env.CLAUDE_PLUGIN_ROOT;
    const args = line.startsWith('node -e "')
      ? ['-e', line.slice(9, -1)]
      : [join('/', 'hooks', 'run-hook.mjs'), `${agent}-guardrail.sh`];
    const result = spawnSync(process.execPath, args, {
      cwd: dir, env, encoding: 'utf8', timeout: 15000,
      input: JSON.stringify({ tool_name: 'Write', tool_input: { file_path: join(dir, 'docs', 'roadmap', 'review', 'spec.md') } }),
    });
    assert.ok(result.stdout, result.stderr);
    assert.equal(JSON.parse(result.stdout).hookSpecificOutput.permissionDecision, 'deny', result.stderr);
  } finally { rmSync(dir, { recursive: true, force: true }); }
});
