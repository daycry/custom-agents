import test from 'node:test';
import assert from 'node:assert/strict';
import fs, { mkdtempSync, mkdirSync, existsSync, rmSync, rmdirSync, symlinkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import plugin from '../hooks/opencode-plugin.js';
import { opencodeContext } from './helpers/opencode-context.mjs';

// T-06 fix10 (gaps 2, 3 y 4): la comparacion de ubicaciones no tiene fallo abierto. Dos rutas son la misma ubicacion si
// coinciden tras `resolve()` O tras `realpath`; la ruta real de la ubicacion del plugin no se fija en `setup` y pasa por la
// misma cache que el resto; la cache guarda exitos y fallos con caducidad corta y no repite una resolucion por ruta y ventana.
const WINDOW = 6000;           // por encima de la caducidad (unos 5 s)

function project(tag) {
  const dir = mkdtempSync(join(tmpdir(), `custom-agents-fix10-${tag}-`));
  mkdirSync(join(dir, '.claude'), { recursive: true });
  mkdirSync(join(dir, 'docs', 'roadmap'), { recursive: true });
  return dir;
}
const link = (target, path) => symlinkSync(target, path, 'junction');
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

test('fix10 gap 2: a failed first realpath never leaves the project foreign for good', async () => {
  const p = project('a'), j = `${p}-link`; let cleanup, restore;
  try {
    link(p, j);
    let first = true;
    restore = patchRealpath((original, ...args) => { if (first) { first = false; throw eio(); } return original(...args); });
    const ctx = opencodeContext(j);                       // la sesion llega por la ruta real, la ubicacion por el enlace
    ctx.session.get = async () => ({ data: { location: { directory: p } } });
    await withClock(async advance => {
      cleanup = await plugin.setup(ctx);
      await prompt(ctx, 'during');                        // el primer realpath falla: la ventana de fallo (unos 5 s) la deja fuera
      advance(WINDOW);
      await prompt(ctx, 'own');
    });
    assert.equal(saved(p, 'own'), true, 'la sesion del propio proyecto debe guardarse tras caducar el fallo (antes: para siempre foreign)');
  } finally { restore?.(); await cleanup?.(); try { rmdirSync(j); } catch {} rmSync(p, { recursive: true, force: true }); }
});

test('fix10 gap 2: equal paths still match when every realpath fails (union with resolve())', async () => {
  const p = project('b'); let cleanup, restore;
  try {
    restore = patchRealpath(() => { throw eio(); });
    const ctx = opencodeContext(p);
    ctx.session.get = async () => ({ data: { location: { directory: p } } });
    cleanup = await plugin.setup(ctx);
    await prompt(ctx, 'own');
    assert.equal(saved(p, 'own'), true);
  } finally { restore?.(); await cleanup?.(); rmSync(p, { recursive: true, force: true }); }
});

test('fix10 gap 3: a re-pointed link is followed once the cached entry expires', async () => {
  const p = project('c'), x = project('x'), j = `${p}-link`; let cleanup;
  try {
    link(x, j);
    const ctx = opencodeContext(j);                       // la ubicacion del plugin es el enlace; la sesion llega por la ruta real
    ctx.session.get = async () => ({ data: { location: { directory: p } } });
    await withClock(async advance => {
      cleanup = await plugin.setup(ctx);
      await prompt(ctx, 'before');
      assert.equal(saved(p, 'before'), false, 'el enlace apunta a otro proyecto: sesion ajena');
      rmdirSync(j); link(p, j);
      advance(WINDOW);
      await prompt(ctx, 'after');
    });
    assert.equal(saved(p, 'after'), true, 'tras re-apuntar el enlace y caducar la entrada, la sesion es propia');
  } finally { await cleanup?.(); try { rmdirSync(j); } catch {} rmSync(p, { recursive: true, force: true }); rmSync(x, { recursive: true, force: true }); }
});

test('fix10 gap 4: a path that cannot be resolved costs one realpath per window', async () => {
  const p = project('d'); let cleanup, restore;
  const gone = join(tmpdir(), `custom-agents-fix10-gone-${process.pid}`);
  try {
    let calls = 0;
    restore = patchRealpath((original, path, ...rest) => { if (path === gone) calls++; return original(path, ...rest); });
    const ctx = opencodeContext(p);
    ctx.session.get = async () => ({ data: { location: { directory: gone } } });
    await withClock(async advance => {
      cleanup = await plugin.setup(ctx);
      for (let i = 0; i < 8; i++) await prompt(ctx, `gone-${i}`);
      assert.equal(calls, 1, 'una sola resolucion en la ventana');
      advance(WINDOW);
      for (let i = 0; i < 8; i++) await prompt(ctx, `gone-b${i}`);
      assert.equal(calls, 2, 'una mas al caducar la entrada');
    });
    assert.equal(saved(p, 'gone-0'), false);
  } finally { restore?.(); await cleanup?.(); rmSync(p, { recursive: true, force: true }); }
});
