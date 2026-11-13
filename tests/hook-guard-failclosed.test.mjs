// T-06 fix6 (ADR-023): the OpenCode bridge fails closed for the protected roles, like the shared launcher.
import test from 'node:test';
import assert from 'node:assert/strict';
import {cpSync, mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join, resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {opencodeContext} from './helpers/opencode-context.mjs';

const root = resolve('.');
const roles = JSON.parse(readFileSync(join(root, 'agent-kits/shared/native-roles.json'), 'utf8')).runtimes.opencode;

async function withGuard(source, body) {
  const dir = mkdtempSync(join(tmpdir(), 'custom-agents-failclosed-'));
  let cleanup;
  const originalWarn = console.warn;
  try {
    const shared = join(dir, 'agent-kits/shared');
    mkdirSync(shared, {recursive: true});
    cpSync(join(root, 'hooks'), join(dir, 'hooks'), {recursive: true});
    writeFileSync(join(shared, 'native-roles.json'), JSON.stringify({schema_version: 1, runtimes: {opencode: roles, claude: {}, codex: {}}}));
    writeFileSync(join(shared, 'native-guardrail.py'), source);
    const entry = join(dir, 'hooks/failclosed-adapter.mjs');
    writeFileSync(entry, readFileSync(join(root, 'hooks/opencode-plugin.js')));
    const {default: plugin} = await import(pathToFileURL(entry));
    console.warn = () => {};
    const ctx = opencodeContext(dir);
    cleanup = await plugin.setup(ctx);
    await body(ctx.hooks.get('tool.execute.before'), dir);
  } finally {await cleanup?.(); console.warn = originalWarn; rmSync(dir, {recursive: true, force: true});}
}

const broken = 'import sys\nsys.stdin.read()\nsys.exit(3)\n';

for (const role of ['implementer', 'architect']) test(`OpenCode ${role}: a guard that cannot decide denies the tool call`, async () => {
  await withGuard(broken, async before => {
    await assert.rejects(before({sessionID: 'owned', agent: roles[role], tool: 'shell', input: {command: 'git status'}}),
      /could not decide/);
  });
});

test('OpenCode: a non-protected identity keeps normal permissions when the guard is broken', async () => {
  await withGuard(broken, async before => {
    await before({sessionID: 'owned', agent: roles.qa, tool: 'shell', input: {command: 'git status'}});
    await before({sessionID: 'owned', agent: 'main', tool: 'shell', input: {command: 'git status'}});
  });
});
