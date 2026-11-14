// T-06 fix9, gap 7: el puente de OpenCode canoniza `location.directory` UNA vez, al cargar, y las demas rutas con una cache
// por cadena (acotada): `realpathSync.native` bloquea el bucle de eventos (en SMB o VPN, en cada herramienta y cada evento).
import test from 'node:test';
import assert from 'node:assert/strict';
import fs, { mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import plugin from '../hooks/opencode-plugin.js';
import { opencodeContext } from './helpers/opencode-context.mjs';

function ownedProject() {
  const directory = mkdtempSync(join(tmpdir(), 'custom-agents-guard9-'));
  mkdirSync(join(directory, '.claude'));
  mkdirSync(join(directory, 'docs', 'roadmap', 'fixture'), {recursive:true});
  writeFileSync(join(directory, '.claude', 'dev.json'), JSON.stringify({guardrails:{ramaPrincipal:false}}));
  return directory;
}
const event = {agent:'custom-agents-implementer', sessionID:'s', id:'x', tool:'write',
  input:{path:'docs/roadmap/fixture/spec.md', content:'x'}};

function contarRealpath() {
  const original = fs.realpathSync.native, llamadas = [];
  fs.realpathSync.native = (...args) => { llamadas.push(String(args[0])); return original(...args); };
  return { llamadas, restaurar: () => { fs.realpathSync.native = original; } };
}

test('la ubicacion del plugin se canoniza una vez, al cargar', async () => {
  const directory = ownedProject();
  const medida = contarRealpath();
  const ctx = opencodeContext(directory);
  try {
    const cleanup = await plugin.setup(ctx);
    try { assert.ok(medida.llamadas.includes(directory), `setup no canonizo ${directory}: ${medida.llamadas}`); }
    finally { await cleanup?.(); }
  } finally { medida.restaurar(); rmSync(directory, {recursive:true, force:true}); }
});

test('ocho eventos de la misma sesion no vuelven a resolver la ruta real', async () => {
  const directory = ownedProject();
  const ctx = opencodeContext(directory);
  const cleanup = await plugin.setup(ctx);
  const medida = contarRealpath();
  try {
    for (let n = 0; n < 8; n++) {
      await assert.rejects(ctx.hooks.get('tool.execute.before')(event), /implementer/);   // el guard sigue actuando
    }
    assert.ok(medida.llamadas.length <= 1, `realpathSync.native se llamo ${medida.llamadas.length} veces en 8 eventos`);
  } finally { medida.restaurar(); await cleanup?.(); rmSync(directory, {recursive:true, force:true}); }
});
