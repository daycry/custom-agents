// SessionEnd en Claude Code tiene un presupuesto GLOBAL de 1,5 s por defecto; el `timeout: 5` de
// hooks/hooks.json no lo eleva. Este fichero MIDE la captura real (launcher Node → Python aislado →
// envelope en la outbox) con el log de prompts en su tope y comprueba la otra mitad del contrato:
// si la captura no llega a tiempo, el log se conserva y `journal.py recover` la materializa.
// Repetible a mano: TEST_PYTHON=<python> node --test tests/session-end-budget.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { cpSync, existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';

const root = resolve('.');
const python = process.env.TEST_PYTHON || 'python';
const SESSION_END_BUDGET_MS = 1500;   // presupuesto efectivo por defecto de SessionEnd
const LOG_MAX_BYTES = 256 * 1024;     // journal.py LOG_MAX_BYTES: el peor caso que hashea la captura
const RUNS = 5;

function proyecto(prefix) {
  const dir = mkdtempSync(join(tmpdir(), prefix));
  mkdirSync(join(dir, 'docs', 'roadmap'), { recursive: true });
  mkdirSync(join(dir, '.claude'), { recursive: true });
  return dir;
}

function logLleno(dir, sid) {
  const linea = JSON.stringify({ ts: '2026-10-13T10:00:00Z', prompt: 'Decidimos medir el cierre. '.repeat(20) }) + '\n';
  writeFileSync(join(dir, '.claude', `session-prompts-${sid}.log`), linea.repeat(Math.floor(LOG_MAX_BYTES / Buffer.byteLength(linea))));
}

function cerrar(runner, dir, sid) {
  const inicio = process.hrtime.bigint();
  const r = spawnSync(process.execPath, [runner, 'session-journal.sh'], {
    cwd: dir, encoding: 'utf8', timeout: 10000,
    input: JSON.stringify({ hook_event_name: 'SessionEnd', session_id: sid, reason: 'other', cwd: dir }),
    env: { ...process.env, CLAUDE_PROJECT_DIR: dir, CUSTOM_AGENTS_PYTHON: python },
  });
  return { r, ms: Number(process.hrtime.bigint() - inicio) / 1e6 };
}

const envelopes = dir => {
  const outbox = join(dir, '.claude', 'journal', 'outbox');
  return existsSync(outbox) ? readdirSync(outbox).filter(f => f.endsWith('.json')) : [];
};

// Trabajo de la captura MEDIDO SIN RELOJ. Antes este test exigia una mediana de pared < 1,5 s del launcher Node + Python: con la maquina
// cargada (80-98 %) arrancar `node` cuesta 1,4-2,3 s y la mediana dio 1,6-2,9 s sin ninguna regresion del producto (era un `todo` en Windows).
// La regresion que guardaba es que la captura haga MAS TRABAJO del previsto (imports pesados en el arranque, trabajo por linea del log de
// prompts, algo cuadratico): eso se cuenta en llamadas de funcion Python (`sys.setprofile`), que no dependen de la carga, y se comprueba
// que no crece con el tamano del log. El tiempo de pared del cierre completo se imprime como dato, no se exige.
const HARNESS = `
import sys, importlib.util
path, root, sid = sys.argv[1:4]
n = [0]
def prof(frame, event, arg):
    if event == 'call': n[0] += 1
sys.setprofile(prof)
spec = importlib.util.spec_from_file_location('jc', path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
imp = n[0]
m.capture_end(root, {'hook_event_name': 'SessionEnd', 'session_id': sid, 'reason': 'other', 'cwd': root})
sys.setprofile(None)
print(imp, n[0] - imp)
`;
// Medido (CPython 3.13, Windows): arranque 9.490 llamadas, captura 5.400-8.000. Tope ~2,5x: un import pesado o un bucle por linea lo superan.
const MAX_LLAMADAS_ARRANQUE = 24000;
const MAX_LLAMADAS_CAPTURA = 20000;
const MARGEN_POR_TAMANO = 300;        // lo que puede subir la captura de un log completo respecto de uno de una linea (ruido de primer uso de la cola)

function llamadas(dir, sid) {
  const r = spawnSync(python, ['-I', '-S', '-c', HARNESS, join(root, 'agent-kits', 'shared', 'journal-capture.py'), dir, sid],
    { cwd: dir, encoding: 'utf8', timeout: 60000, env: { ...process.env, CLAUDE_PROJECT_DIR: dir } });
  assert.equal(r.status, 0, r.stderr);
  const [arranque, captura] = r.stdout.trim().split(/\s+/).map(Number);
  assert.ok(Number.isInteger(arranque) && Number.isInteger(captura), `harness output: ${r.stdout}`);
  return { arranque, captura };
}

test('SessionEnd capture does bounded work (function calls, not wall time) with a full prompt log', () => {
  const dir = proyecto('custom-agents-budget-');
  try {
    // Calentamiento sin medir (crea la cola); despues, log de una linea frente a log en su tope.
    logLleno(dir, 'warm-up');
    llamadas(dir, 'warm-up');
    const chica = proyecto('custom-agents-budget-small-');
    try {
      const linea = JSON.stringify({ ts: '2026-10-13T10:00:00Z', prompt: 'Decidimos medir el cierre. '.repeat(20) }) + '\n';
      writeFileSync(join(chica, '.claude', 'session-prompts-chica.log'), linea);
      llamadas(chica, 'warm-up');
      const pequeno = llamadas(chica, 'chica');
      logLleno(dir, 'grande');
      const grande = llamadas(dir, 'grande');
      console.log(`SessionEnd capture calls: startup ${grande.arranque} · capture small log ${pequeno.captura} · capture full log ${grande.captura}`);
      assert.ok(grande.arranque < MAX_LLAMADAS_ARRANQUE, `startup did ${grande.arranque} calls (max ${MAX_LLAMADAS_ARRANQUE}): heavier imports at teardown?`);
      assert.ok(grande.captura < MAX_LLAMADAS_CAPTURA, `capture did ${grande.captura} calls (max ${MAX_LLAMADAS_CAPTURA})`);
      assert.ok(grande.captura <= pequeno.captura + MARGEN_POR_TAMANO, `capture work grows with the log: ${pequeno.captura} -> ${grande.captura} calls`);
    } finally { rmSync(chica, { recursive: true, force: true }); }
  } finally { rmSync(dir, { recursive: true, force: true }); }
});

test('SessionEnd closes through the launcher never lose a capture it did not cut (wall time is informational)', () => {
  const dir = proyecto('custom-agents-closes-');
  try {
    logLleno(dir, 'warm-up');
    cerrar(join(root, 'hooks', 'run-hook.mjs'), dir, 'warm-up');
    rmSync(join(dir, '.claude', 'journal'), { recursive: true, force: true });
    const tiempos = [], cortados = [];
    for (let i = 0; i < RUNS; i++) {
      const sid = `budget-${i}`;
      logLleno(dir, sid);
      const { r, ms } = cerrar(join(root, 'hooks', 'run-hook.mjs'), dir, sid);
      assert.equal(r.status, 0, r.stderr);
      tiempos.push(ms);
      if (/timed out/.test(r.stderr)) cortados.push(i);
    }
    const sobres = envelopes(dir).length;
    const orden = [...tiempos].sort((a, b) => a - b);
    const mediana = orden[Math.floor(RUNS / 2)];
    console.log(`SessionEnd capture ms (default ${SESSION_END_BUDGET_MS} ms budget): ${tiempos.map(t => t.toFixed(0)).join(', ')} · median ${mediana.toFixed(0)} · `
      + `cut by launcher: ${cortados.length}/${RUNS} · envelopes ${sobres}/${RUNS}`);
    // fix24 (gap 21): la puerta de pared se restaura en POSIX (Linux/macOS, donde `node` arranca en <0,3 s y la mediana de 450-715 ms mide el producto). En Windows con la maquina cargada
    // arrancar `node` cuesta 1,4-2,3 s sin regresion (por eso el trabajo se cuenta en llamadas, test anterior): ahi solo se informa.
    if (process.platform !== 'win32') assert.ok(mediana < SESSION_END_BUDGET_MS, `median ${mediana.toFixed(0)} ms >= ${SESSION_END_BUDGET_MS} ms`);
    // Un cierre cortado por el presupuesto lo cubre `recover` (test siguiente); uno NO cortado sin envelope seria perdida silenciosa.
    assert.ok(sobres >= RUNS - cortados.length, `${sobres} envelopes for ${RUNS - cortados.length} uncut closes`);
  } finally { rmSync(dir, { recursive: true, force: true }); }
});

test('a capture cut by the budget keeps the prompt log and journal recover materializes it', () => {
  const dir = proyecto('custom-agents-recover-');
  try {
    const bundle = join(dir, 'plugin');
    cpSync(join(root, 'hooks'), join(bundle, 'hooks'), { recursive: true });
    mkdirSync(join(bundle, 'agent-kits', 'shared'), { recursive: true });
    // Captura más lenta que cualquier presupuesto: el launcher la corta sin dejar envelope.
    writeFileSync(join(bundle, 'agent-kits', 'shared', 'journal-capture.py'), 'import time\ntime.sleep(10)\n');
    const sid = 'cut-by-budget';
    logLleno(dir, sid);
    const { r, ms } = cerrar(join(bundle, 'hooks', 'run-hook.mjs'), dir, sid);
    assert.equal(r.status, 0, r.stderr);
    assert.match(r.stderr, /capture timed out; journal recover/);
    assert.ok(ms < 8000, `the cut must not wait for the 10 s capture (took ${ms.toFixed(0)} ms)`);
    assert.equal(envelopes(dir).length, 0);
    assert.ok(existsSync(join(dir, '.claude', `session-prompts-${sid}.log`)), 'the prompt log must survive the cut');

    const rec = spawnSync(python, [join(root, 'agent-kits', 'shared', 'journal.py'), 'recover', '--root', dir, '--session-id', sid], {
      cwd: dir, encoding: 'utf8', timeout: 30000, env: { ...process.env, CLAUDE_PROJECT_DIR: dir },
    });
    assert.equal(rec.status, 0, rec.stderr);
    const journal = join(dir, 'docs', 'knowledge', 'journal');
    const entradas = existsSync(journal) ? readdirSync(journal).filter(f => f.endsWith('.md') && f !== 'README.md') : [];
    assert.equal(entradas.length, 1, `recover output: ${rec.stdout}`);
    assert.match(readFileSync(join(journal, entradas[0]), 'utf8'), new RegExp(sid));
  } finally { rmSync(dir, { recursive: true, force: true }); }
});
