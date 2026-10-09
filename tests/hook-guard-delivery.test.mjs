import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { cpSync, mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';

const root = resolve('.');
const unavailable = 'custom-agents: role guard unavailable; normal permissions continue';
function invoke(runtime, program, options = {}) {
  const dir = mkdtempSync(join(tmpdir(), 'custom-agents-guard-delivery-'));
  try {
    cpSync(join(root, 'hooks'), join(dir, 'hooks'), { recursive: true });
    mkdirSync(join(dir, 'agent-kits', 'shared'), { recursive: true });
    writeFileSync(join(dir, 'agent-kits', 'shared', 'native-guardrail.py'), program);
    if (options.supervisor) writeFileSync(join(dir, 'hooks', 'runtime-supervisor.py'), options.supervisor);
    const env = { ...process.env, PYTHONDONTWRITEBYTECODE: '1',
      CUSTOM_AGENTS_PYTHON: options.missing ? join(dir, 'absent-python') : process.env.TEST_PYTHON || 'python' };
    if (options.noPython) { env.PATH = dir; env.Path = dir; delete env.CUSTOM_AGENTS_PYTHON; }
    return spawnSync(process.execPath, [join(dir, 'hooks', 'run-hook.mjs'), 'native-guardrail', `--runtime=${runtime}`], {
      cwd: dir, input: '{"prompt":"PRIVATE_PAYLOAD_SENTINEL"}', encoding: 'utf8', timeout: 8500,
      env,
    });
  } finally { rmSync(dir, { recursive: true, force: true }); }
}
function checkUnavailable(result, runtime) {
  assert.equal(result.status, 0, result.stderr);
  assert.equal((result.stdout + result.stderr).includes('PRIVATE_PAYLOAD_SENTINEL'), false);
  const output = JSON.parse(result.stdout);
  if (runtime === 'opencode') {
    assert.deepEqual(output, { decision: 'continue', role: null, reason: null, diagnostic: 'guard-unavailable' });
  } else {
    assert.deepEqual(output, { systemMessage: unavailable });
  }
}
const decision = (kind, diagnostic = null) => ({ decision: kind, role: 'architect',
  reason: kind === 'deny' ? 'Protected mutation' : null, diagnostic });
const print = value => `print(${JSON.stringify(JSON.stringify(value))},flush=True)\n`;

for (const runtime of ['claude', 'codex', 'opencode']) {
  for (const [name, program, options] of [
    ['spawn failure', '', { missing: true }],
    ['Python absent', '', { noPython: true }],
    ['empty failed evaluator', 'raise SystemExit(1)\n', {}],
    ['empty successful evaluator', '', {}],
    ['partial result', "print('{\\\"decision\\\":',flush=True)\n", {}],
    ['invalid decision', print({ decision: 'allow', reason: null, role: null, diagnostic: null }), {}],
    ['invalid denial', print({ decision: 'deny', reason: '', role: 'architect', diagnostic: null }), {}],
    ['invalid role', print({ ...decision('deny'), role: 'foreign-agent' }), {}],
    ['unknown diagnostic', print(decision('continue', 'PRIVATE_PAYLOAD_SENTINEL')), {}],
    ['multiple results', print(decision('continue')) + print(decision('deny')), {}],
    ['failed continuation', print(decision('continue')) + 'raise SystemExit(1)\n', {}],
    ['excessive result', "print('x'*70000,flush=True)\n", {}],
    ['startup budget expires', 'import time\ntime.sleep(10)\n', {}],
  ]) test(`${runtime}: ${name} visibly degrades without granting permission`, () => {
    checkUnavailable(invoke(runtime, program, options), runtime);
  });

  test(`${runtime}: evaluated continue retains normal permissions`, () => {
    const result = invoke(runtime, print(decision('continue')));
    assert.equal(result.status, 0, result.stderr);
    assert.equal(result.stderr, '');
    assert.equal(result.stdout, runtime === 'opencode' ? JSON.stringify(decision('continue')) + '\n' : '');
  });
  test(`${runtime}: evaluated denial retains native blocking output`, () => {
    const result = invoke(runtime, print(decision('deny')));
    assert.equal(result.status, 0, result.stderr);
    const output = JSON.parse(result.stdout);
    if (runtime === 'opencode') assert.deepEqual(output, decision('deny'));
    else assert.deepEqual(output, { hookSpecificOutput: { hookEventName: 'PreToolUse',
      permissionDecision: 'deny', permissionDecisionReason: 'Protected mutation' } });
  });
  test(`${runtime}: supplementary Unicode keeps the evaluator code-point limit`, () => {
    const value = { ...decision('deny'), reason: '🐍'.repeat(2048) };
    const result = invoke(runtime, print(value));
    assert.equal(result.status, 0, result.stderr);
    const output = JSON.parse(result.stdout);
    if (runtime === 'opencode') assert.deepEqual(output, value);
    else assert.equal(output.hookSpecificOutput.permissionDecisionReason, value.reason);
  });
  test(`${runtime}: a reason above the evaluator limit is rejected`, () => {
    checkUnavailable(invoke(runtime, print({ ...decision('deny'), reason: '🐍'.repeat(2049) })), runtime);
  });
  test(`${runtime}: a complete denial survives later timeout`, () => {
    const result = invoke(runtime, print(decision('deny')) + 'import time\ntime.sleep(10)\n');
    assert.equal(result.status, 0, result.stderr);
    const output = JSON.parse(result.stdout);
    if (runtime === 'opencode') assert.equal(output.decision, 'deny');
    else assert.equal(output.hookSpecificOutput.permissionDecision, 'deny');
  });
  test(`${runtime}: complete denial survives failed evaluator termination`, () => {
    const result = invoke(runtime, print(decision('deny')) + 'raise SystemExit(1)\n');
    assert.equal(result.status, 0, result.stderr);
    const output = JSON.parse(result.stdout);
    if (runtime === 'opencode') assert.equal(output.decision, 'deny');
    else assert.equal(output.hookSpecificOutput.permissionDecision, 'deny');
  });
  test(`${runtime}: evaluator diagnostic reaches its native consumer`, () => {
    const result = invoke(runtime, print(decision('continue', 'input-unrecognized')));
    assert.equal(result.status, 0, result.stderr);
    if (runtime === 'opencode') assert.equal(JSON.parse(result.stdout).diagnostic, 'input-unrecognized');
    else assert.equal(JSON.parse(result.stdout).systemMessage, unavailable);
  });
  test(`${runtime}: failed containment visibly degrades`, { skip: process.platform !== 'win32' }, () => {
    checkUnavailable(invoke(runtime, '', { supervisor: "import sys\nprint('PRIVATE_PAYLOAD_SENTINEL',file=sys.stderr,flush=True)\nraise SystemExit(1)\n" }), runtime);
  });
  test(`${runtime}: unconfirmed supervisor cannot supply a denial`, { skip: process.platform !== 'win32' }, () => {
    checkUnavailable(invoke(runtime, '', { supervisor: print(decision('deny')) + "import sys\nprint('{}',file=sys.stderr,flush=True)\n" }), runtime);
  });
  test(`${runtime}: denial is retained when cleanup confirmation expires`, { skip: process.platform !== 'win32' }, () => {
    const supervisor = readFileSync(join(root, 'hooks', 'runtime-supervisor.py'), 'utf8')
      .replace('close_job(owner, int(args[2]))', 'close_job(owner, int(args[2]))\n            time.sleep(2)');
    const result = invoke(runtime, print(decision('deny')), { supervisor });
    assert.equal(result.status, 0, result.stderr);
    assert.match(result.stderr, /cleanup confirmation timed out/);
    const output = JSON.parse(result.stdout);
    if (runtime === 'opencode') assert.equal(output.decision, 'deny');
    else assert.equal(output.hookSpecificOutput.permissionDecision, 'deny');
  });
  for (const diagnostic of ['branch-unavailable', 'guardrails-disabled']) test(`${runtime}: ${diagnostic} is explicit without losing a denial`, () => {
    const result = invoke(runtime, print(decision('deny', diagnostic)));
    assert.equal(result.status, 0, result.stderr);
    const output = JSON.parse(result.stdout);
    if (runtime === 'opencode') assert.deepEqual(output, decision('deny', diagnostic));
    else {
      assert.equal(output.hookSpecificOutput.permissionDecision, 'deny');
      assert.equal(output.systemMessage, diagnostic === 'guardrails-disabled'
        ? 'custom-agents: role guards disabled by project configuration' : unavailable);
    }
  });
}
