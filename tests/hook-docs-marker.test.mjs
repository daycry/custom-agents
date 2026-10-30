import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, existsSync, lstatSync, rmSync, symlinkSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { tmpdir } from 'node:os';

const launcher = resolve('hooks/run-hook.mjs');
function fixture(t) {
  const root = mkdtempSync(join(tmpdir(), 'custom-agents-doc-marker-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  return root;
}
function invoke(root, runtime, payload) {
  const absent = join(root, 'absent-bin');
  const result = spawnSync(process.execPath, [launcher, 'mark-docs-pending.sh', `--runtime=${runtime}`], {
    input: typeof payload === 'string' ? payload : JSON.stringify(payload),
    encoding: 'utf8', timeout: 5000, cwd: root,
    env: { ...process.env, CLAUDE_PROJECT_DIR: root, CUSTOM_AGENTS_PYTHON: join(absent, 'python'),
      PATH: absent, Path: absent },
  });
  assert.ifError(result.error);
  assert.equal(result.status, 0, result.stderr);
  assert.equal(result.stdout, '');
  return result;
}

for (const runtime of ['claude', 'codex', 'opencode']) {
  test(`${runtime}: documentation marker works without Python or shell`, t => {
    const root = fixture(t);
    const result = invoke(root, runtime, { tool_name: 'Write', tool_input: { file_path: 'docs/readme.md' } });
    const marker = join(root, '.claude', '.confluence-pending');
    assert.equal(result.stderr, '');
    assert.equal(existsSync(marker), true);
    assert.equal(lstatSync(marker).isFile(), true);
    assert.equal(readFileSync(marker).length, 0);
  });
  for (const [name, payload] of [
    ['native backslashes', { tool_name: 'Edit', tool_input: { file_path: 'C:\\project\\docs\\page.md' } }],
    ['multiple edits', { tool_name: 'MultiEdit', tool_input: { edits: [{ file_path: 'src/app.py' }, { file_path: 'docs/page.md' }] } }],
    ['F2-B01 standard MultiEdit with a top-level path', { tool_name: 'MultiEdit', tool_input: {
      file_path: 'docs/page.md', edits: [{ old_string: 'old', new_string: 'new' }],
    } }],
    ['patch move', { tool_name: 'apply_patch', tool_input: { command: '*** Begin Patch\n*** Update File: src/page.md\n*** Move to: docs/page.md\n@@\n-a\n+b\n*** End Patch' } }],
    ['non-ASCII path', { tool_input: { file_path: 'docs/guía/日本語.md' } }],
  ]) test(`${runtime}: marker accepts ${name}`, t => {
    const root = fixture(t);
    assert.equal(invoke(root, runtime, payload).stderr, '');
    assert.equal(existsSync(join(root, '.claude', '.confluence-pending')), true);
  });
  for (const path of ['src/app.py', 'docs/security-scan/report.md', 'docs/confluence/staged.md', 'docs\\security-scan\\report.md']) {
    test(`${runtime}: marker excludes ${path}`, t => {
      const root = fixture(t);
      assert.equal(invoke(root, runtime, { tool_input: { file_path: path } }).stderr, '');
      assert.equal(existsSync(join(root, '.claude')), false);
    });
  }
  for (const payload of ['{invalid', { tool_input: { file_path: null } }, { tool_input: { edits: [{}] } },
    { tool_input: { file_path: 'docs/page.md', edits: [null] } },
    { tool_input: { file_path: 'docs/page.md', edits: [{ file_path: null }] } },
  ]) {
    test(`${runtime}: marker degrades for unknown input ${JSON.stringify(payload)}`, t => {
      const root = fixture(t);
      const result = invoke(root, runtime, payload);
      assert.match(result.stderr, /custom-agents hooks:/);
      assert.equal(existsSync(join(root, '.claude', '.confluence-pending')), false);
    });
  }
}

test('marker refuses an existing .claude directory junction/symlink', t => {
  const root = fixture(t);
  const outside = fixture(t);
  symlinkSync(outside, join(root, '.claude'), 'junction');
  assert.match(invoke(root, 'codex', { tool_input: { file_path: 'docs/page.md' } }).stderr, /custom-agents hooks:/);
  assert.equal(existsSync(join(outside, '.confluence-pending')), false);
});

test('marker preserves an existing unrelated nonempty file', t => {
  const root = fixture(t);
  mkdirSync(join(root, '.claude'));
  const marker = join(root, '.claude', '.confluence-pending');
  writeFileSync(marker, 'unowned content');
  assert.match(invoke(root, 'claude', { tool_input: { file_path: 'docs/page.md' } }).stderr, /custom-agents hooks:/);
  assert.equal(readFileSync(marker, 'utf8'), 'unowned content');
});

test('marker is idempotent for an existing empty marker', t => {
  const root = fixture(t);
  mkdirSync(join(root, '.claude'));
  const marker = join(root, '.claude', '.confluence-pending');
  writeFileSync(marker, '');
  assert.equal(invoke(root, 'opencode', { tool_input: { file_path: 'docs/page.md' } }).stderr, '');
  assert.equal(readFileSync(marker).length, 0);
});

test('marker handles an unusable state directory without failing the edit', t => {
  const root = fixture(t);
  writeFileSync(join(root, '.claude'), 'not a directory');
  assert.match(invoke(root, 'codex', { tool_input: { file_path: 'docs/page.md' } }).stderr, /custom-agents hooks:/);
  assert.equal(readFileSync(join(root, '.claude'), 'utf8'), 'not a directory');
});

test('marker does not follow an existing file symlink', t => {
  const root = fixture(t);
  mkdirSync(join(root, '.claude'));
  const target = join(root, 'unowned.txt');
  writeFileSync(target, 'unowned content');
  try { symlinkSync(target, join(root, '.claude', '.confluence-pending'), 'file'); }
  catch (error) { if (process.platform === 'win32' && error.code === 'EPERM') return t.skip('file symlink privilege unavailable'); throw error; }
  assert.match(invoke(root, 'codex', { tool_input: { file_path: 'docs/page.md' } }).stderr, /custom-agents hooks:/);
  assert.equal(readFileSync(target, 'utf8'), 'unowned content');
});
