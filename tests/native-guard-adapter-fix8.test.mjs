// T-06 fix8, gap 6: el puente de OpenCode compara las ubicaciones por su ruta REAL y un workspaceID presente solo en
// un lado no hace la sesión ajena (el mismo proyecto con otra forma de ruta no se salta el guard).
import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, existsSync, rmSync, symlinkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import plugin from '../hooks/opencode-plugin.js';
import { opencodeContext } from './helpers/opencode-context.mjs';

function ownedProject() {
  const directory = mkdtempSync(join(tmpdir(), 'custom-agents-guard8-'));
  mkdirSync(join(directory, '.claude'));
  mkdirSync(join(directory, 'docs', 'roadmap', 'fixture'), {recursive:true});
  writeFileSync(join(directory, '.claude', 'dev.json'), JSON.stringify({guardrails:{ramaPrincipal:false}}));
  return directory;
}
const event = {agent:'custom-agents-implementer', sessionID:'s', id:'x', tool:'write',
  input:{path:'docs/roadmap/fixture/spec.md', content:'x'}};

async function guardado(directory, ubicacionSesion, ubicacionPlugin) {
  const ctx = opencodeContext(directory);
  if (ubicacionPlugin) Object.assign(ctx.location, ubicacionPlugin);
  const cleanup = await plugin.setup(ctx);
  try {
    ctx.session.get = async () => ({ location: ubicacionSesion, data: { location: ubicacionSesion } });
    await ctx.hooks.get('tool.execute.before')(event);
    return false;                      // no lanzó: la sesión se tuvo por ajena (o el guard dejó pasar)
  } catch (error) {
    return /implementer/.test(String(error.message));
  } finally { await cleanup?.(); }
}

test('un workspaceID presente solo en la sesion no la hace ajena', async () => {
  const directory = ownedProject();
  try { assert.equal(await guardado(directory, { directory, workspaceID: 'w1' }), true); }
  finally { rmSync(directory, {recursive:true, force:true}); }
});

test('un workspaceID presente solo en el plugin no la hace ajena', async () => {
  const directory = ownedProject();
  try { assert.equal(await guardado(directory, { directory }, { workspaceID: 'w1' }), true); }
  finally { rmSync(directory, {recursive:true, force:true}); }
});

test('dos workspaceID distintos siguen siendo ubicaciones distintas', async () => {
  const directory = ownedProject();
  try { assert.equal(await guardado(directory, { directory, workspaceID: 'a' }, { workspaceID: 'b' }), false); }
  finally { rmSync(directory, {recursive:true, force:true}); }
});

test('el mismo proyecto por un enlace (otra forma de ruta) se guarda', async () => {
  const directory = ownedProject();
  const enlace = directory + '-enlace';
  let hecho = true;
  try { symlinkSync(directory, enlace, 'junction'); } catch { hecho = false; }
  try {
    if (!hecho) return;               // sin permiso para enlaces: no verificable aquí
    assert.equal(await guardado(directory, { directory: enlace }), true);
  } finally { rmSync(enlace, {recursive:true, force:true}); rmSync(directory, {recursive:true, force:true}); }
});

test('otra ubicacion real sigue sin guardarse', async () => {
  const directory = ownedProject();
  try { assert.equal(await guardado(directory, { directory: join(directory, 'other') }), false); }
  finally { rmSync(directory, {recursive:true, force:true}); }
});
