import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { join, resolve } from 'node:path';
import { tmpdir } from 'node:os';

const launcher = resolve('hooks/run-hook.mjs');
const invoke = (hook, runtime, payload) => spawnSync(process.execPath,
  [launcher, hook, `--runtime=${runtime}`], {
    input: typeof payload === 'string' ? payload : JSON.stringify(payload),
    encoding: 'utf8', timeout: 5000,
    env: { ...process.env, CUSTOM_AGENTS_PYTHON: join(tmpdir(), 'custom-agents-absent-preflight-python'),
      PATH: join(tmpdir(), 'custom-agents-absent-preflight-bin'),
      Path: join(tmpdir(), 'custom-agents-absent-preflight-bin') },
  });
const edit = file_path => ({ tool_input: { file_path } });

for (const runtime of ['claude', 'codex', 'opencode']) {
  for (const [hook, payload] of [
    ['mark-docs-pending.sh', edit('src/app.py')],
    ['mark-docs-pending.sh', edit('docs/security-scan/report.md')],
    ['mark-docs-pending.sh', edit('docs/confluence/page.md')],
    ['ledger-lint-warn.sh', edit('docs/roadmap/first/spec.md')],
    ['progress-line.sh', edit('docs/roadmap/first/design.md')],
    ['ledger-lint-warn.sh', { tool_input: { edits: [{ file_path: 'src/app.py' }, { file_path: 'docs/README.md' }] } }],
    ['progress-line.sh', { tool_name: 'apply_patch', tool_input: { command: '*** Begin Patch\n*** Add File: src/app.py\n+x\n*** End Patch' } }],
  ]) test(`${runtime}: ${hook} skips Python for an inapplicable edit ${JSON.stringify(payload)}`, () => {
    const result = invoke(hook, runtime, payload);
    assert.equal(result.status, 0, result.stderr);
    assert.equal(result.stdout, '');
    assert.equal(result.stderr, '');
  });

  for (const [hook, payload] of [
    ['mark-docs-pending.sh', edit('docs/README.md')],
    ['ledger-lint-warn.sh', edit('docs\\roadmap\\first\\tasks.md')],
    ['progress-line.sh', { tool_input: { edits: [{ file_path: 'src/app.py' }, { file_path: 'docs/roadmap/first/tasks.md' }] } }],
    ['progress-line.sh', { tool_name: 'apply_patch', tool_input: { command: '*** Begin Patch\n*** Update File: docs/roadmap/first/tasks.md\n@@\n-old\n+new\n*** End Patch' } }],
    ['ledger-lint-warn.sh', '{invalid'],
    ['mark-docs-pending.sh', { tool_input: { file_path: null } }],
    ['progress-line.sh', { tool_input: { edits: [{ content: 'unknown shape' }] } }],
    ['ledger-lint-warn.sh', edit('docs/roadmap/first/tasks.md\nsrc/app.py')],
    ['ledger-lint-warn.sh', edit('docs/roadmap/first\u2028/tasks.md')],
    ['progress-line.sh', edit('docs/roadmap/first\u2029/tasks.md')],
  ]) test(`${runtime}: ${hook} keeps execution for an applicable or unknown edit ${JSON.stringify(payload)}`, () => {
    const result = invoke(hook, runtime, payload);
    assert.equal(result.status, 0);
    assert.match(result.stderr, /custom-agents hooks:/);
  });
}
