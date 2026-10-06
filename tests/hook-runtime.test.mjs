import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { cpSync, existsSync, mkdtempSync, mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { CustomAgentsHooks } from '../hooks/opencode-plugin.js';

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
  try {
    mkdirSync(join(dir, 'docs', 'roadmap'), { recursive: true });
    const hooks = await CustomAgentsHooks({ directory: dir, worktree: dir });
    await hooks.event({ event: { type: 'session.idle', properties: { sessionID: 'opencode-hook-test' } } });
    assert.equal(readdirSync(join(dir, '.claude', 'journal', 'outbox')).filter(f => f.endsWith('.json')).length, 1);
  } finally { rmSync(dir, { recursive: true, force: true }); }
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
