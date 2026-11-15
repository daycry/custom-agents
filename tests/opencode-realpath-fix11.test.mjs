import test from 'node:test';
import assert from 'node:assert/strict';
import fs, { mkdtempSync, mkdirSync, existsSync, rmSync, rmdirSync, symlinkSync, unlinkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import plugin from '../hooks/opencode-plugin.js';
import { opencodeContext } from './helpers/opencode-context.mjs';

// T-06 fix11 (gap 9): un fallo de `realpath` hace la comparacion de ubicaciones INDETERMINADA y la sesion se guarda (guardar de mas
// solo ejecuta el hook con el cwd de la sesion; descartar de menos pierde la sesion propia). Un fallo `ENOENT`/`ENOTDIR` no es
// indeterminado: una ruta que no existe no puede ser otra forma de un proyecto que si existe.
const WINDOW = 6000;

function project(tag) {
  const dir = mkdtempSync(join(tmpdir(), `custom-agents-fix11-${tag}-`));
  mkdirSync(join(dir, '.claude'), { recursive: true });
  mkdirSync(join(dir, 'docs', 'roadmap'), { recursive: true });
  return dir;
}
const link = (target, path) => symlinkSync(target, path, 'junction');
const unlink = path => { try { unlinkSync(path); } catch { try { rmdirSync(path); } catch { /* ya no existe */ } } };
const saved = (dir, id) => existsSync(join(dir, '.claude', `session-prompts-${id}.log`));
const prompt = (ctx, id) => ctx.hooks.get('session.prompt')({ sessionID: id, prompt: { text: 'turno de prueba' } });
function withClock(fn) {
  const real = Date.now, base = real();
  let offset = 0;
  Date.now = () => base + offset;
  return fn(ms => { offset += ms; }).finally(() => { Date.now = real; });
}
function patchRealpath(impl) {
  const original = fs.realpathSync.native;
  fs.realpathSync.native = (...args) => impl(original, ...args);
  return () => { fs.realpathSync.native = original; };
}
const eio = () => Object.assign(new Error('EIO'), { code: 'EIO' });

test('fix11 gap 9: a failed first realpath and another path form still saves the own session', async () => {
  const p = project('a'), j = `${p}-link`; let cleanup, restore;
  try {
    link(p, j);
    let first = true;
    restore = patchRealpath((original, ...args) => { if (first) { first = false; throw eio(); } return original(...args); });
    const ctx = opencodeContext(j);                       // la ubicacion por el enlace; la sesion llega por la ruta real
    ctx.session.get = async () => ({ data: { location: { directory: p } } });
    await withClock(async advance => {
      cleanup = await plugin.setup(ctx);
      await prompt(ctx, 'during');                        // el primer realpath falla: comparacion indeterminada
      assert.equal(saved(p, 'during'), true, 'indeterminada: la sesion se guarda, no se descarta 5 s');
      advance(WINDOW);
      await prompt(ctx, 'after');
    });
    assert.equal(saved(p, 'after'), true);
  } finally { restore?.(); await cleanup?.(); unlink(j); rmSync(p, { recursive: true, force: true }); }
});

test('fix11 gap 9: a failure on the session side only is also indeterminate', async () => {
  const p = project('b'), j = `${p}-link`; let cleanup, restore;
  try {
    link(p, j);
    restore = patchRealpath((original, path, ...rest) => { if (path === p) throw eio(); return original(path, ...rest); });
    const ctx = opencodeContext(j);
    ctx.session.get = async () => ({ data: { location: { directory: p } } });
    cleanup = await plugin.setup(ctx);
    await prompt(ctx, 'own');
    assert.equal(saved(p, 'own'), true);
  } finally { restore?.(); await cleanup?.(); unlink(j); rmSync(p, { recursive: true, force: true }); }
});

test('fix11 gap 9: a path that does not exist (ENOENT) is a different project, not an indeterminate one', async () => {
  const p = project('c'); let cleanup;
  try {
    const ctx = opencodeContext(p);
    ctx.session.get = async () => ({ data: { location: { directory: resolve(p, '..', `custom-agents-fix11-nada-${process.pid}`) } } });
    cleanup = await plugin.setup(ctx);
    await prompt(ctx, 'foreign');
    assert.equal(saved(p, 'foreign'), false, 'una ruta que no existe no es una forma de este proyecto');
  } finally { await cleanup?.(); rmSync(p, { recursive: true, force: true }); }
});

test('fix11 gap 9: two existing different projects stay different when every realpath works', async () => {
  const p = project('d'), x = project('x'); let cleanup;
  try {
    const ctx = opencodeContext(p);
    ctx.session.get = async () => ({ data: { location: { directory: x } } });
    cleanup = await plugin.setup(ctx);
    await prompt(ctx, 'foreign');
    assert.equal(saved(p, 'foreign'), false);
  } finally { await cleanup?.(); rmSync(p, { recursive: true, force: true }); rmSync(x, { recursive: true, force: true }); }
});
