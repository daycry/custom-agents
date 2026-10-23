#!/usr/bin/env node
// Pico (spike) de CSP del panel con Chart.js — panel-redesign T-03 (design.md §2.4 I-01).
//
// Abre una página mínima con un gráfico de Chart.js (el fichero incluido en
// skills/plugin-panel/assets/vendor/chart.js/) en los dos modos del panel y en cada motor:
//   - servido: servidor de loopback 127.0.0.1 con CSP por cabecera y nonce en cada <script src>;
//   - file://: carpeta exportada con CSP en <meta>, sin JS inline (datos en type="application/json").
// La red queda bloqueada: toda petición http(s) a un origen distinto del servidor se aborta y se cuenta.
// Cuenta eventos `securitypolicyviolation` (detector inyectado por Playwright) y mensajes de consola de CSP.
// Un caso de CONTROL por motor y modo (script inline prohibido) demuestra que el detector ve las
// violaciones: sin él, «0 violaciones» podría ser un detector roto. Con --fallback prueba además el
// respaldo determinista (Chart.js incrustado + script-src 'sha256-…').
//
// Uso: node tests/e2e/panel-csp-spike.mjs [--engines chromium,firefox] [--playwright-dir <dir>]
//                                          [--chromium-channel msedge] [--fallback]
// Salida 0: los casos pasan · 1: algún caso falla · 2: Playwright o un navegador no está instalado
// (aviso; nunca un verde inventado). No es un test de CI (sin `.test`): CI no tiene navegadores.
import { createRequire } from 'node:module';
import { createServer } from 'node:http';
import { createHash, randomBytes } from 'node:crypto';
import { copyFileSync, existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, extname, join, resolve, sep } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..');
const CHART = join(ROOT, 'skills', 'plugin-panel', 'assets', 'vendor', 'chart.js', 'chart.umd.min.js');

// Políticas CANDIDATAS (lo que decide este pico). Ninguna lleva 'unsafe-eval' ni 'unsafe-inline' en script-src.
const CSP_EXPORTADO = "default-src 'none'; script-src 'self' file:; style-src 'self' 'unsafe-inline'; img-src data:";
// Firefox pide /favicon.ico por su cuenta en http(s) y `default-src 'none'` lo bloquea (img-src): cada página
// declara `<link rel="icon" href="data:,">` y las dos políticas admiten `img-src data:`.
const cspServido = (nonce) => "default-src 'none'; style-src 'self' 'unsafe-inline'; script-src 'nonce-" + nonce
  + "'; img-src data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'";
// Cabecera ACTUAL de serve_panel.py (create_server) — solo diagnóstico: sin 'self' en style-src.
const cspServidoActual = (nonce) => "default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-" + nonce
  + "'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'";

function args(argv) {
  const out = { engines: ['chromium', 'firefox'], playwrightDir: process.env.PLAYWRIGHT_DIR || null,
    chromiumChannel: null, fallback: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--engines') out.engines = String(argv[++i] || '').split(',').map((s) => s.trim()).filter(Boolean);
    else if (a === '--playwright-dir') out.playwrightDir = argv[++i];
    else if (a === '--chromium-channel') out.chromiumChannel = argv[++i];
    else if (a === '--fallback') out.fallback = true;
    else { console.error('argumento desconocido: ' + a); process.exit(2); }
  }
  if (!out.engines.length || out.engines.some((e) => !['chromium', 'firefox'].includes(e))) {
    console.error('--engines solo admite chromium y firefox'); process.exit(2);
  }
  return out;
}

function loadPlaywright(dir) {
  const bases = [dir, join(ROOT, 'agent-kits', 'qa', 'runner'), process.cwd()].filter(Boolean);
  for (const base of bases) {
    const require = createRequire(join(resolve(base), 'package.json'));
    for (const name of ['@playwright/test', 'playwright']) {
      try { return { pw: require(name), from: base }; } catch { /* siguiente */ }
    }
  }
  return null;
}

const sri = (text) => "'sha256-" + createHash('sha256').update(text, 'utf8').digest('base64') + "'";

const DATOS = JSON.stringify({ labels: ['T-01', 'T-02', 'T-03'], serie: 'Horas IA', valores: [0.3, 0.2, 0.4] })
  .replace(/</g, '\\u003c').replace(/>/g, '\\u003e').replace(/&/g, '\\u0026');
const SPIKE_JS = `(function () {
  var raiz = document.documentElement;
  var datos = JSON.parse(document.getElementById('panel-data').textContent);
  if (!window.Chart) { raiz.dataset.spike = 'sin-chart'; return; }
  var lienzo = document.getElementById('grafico');
  new window.Chart(lienzo, { type: 'bar', data: { labels: datos.labels,
    datasets: [{ label: datos.serie, data: datos.valores, backgroundColor: '#1d4ed8' }] },
    options: { animation: false, responsive: false } });
  var px = lienzo.getContext('2d').getImageData(0, 0, lienzo.width, lienzo.height).data, n = 0;
  for (var i = 3; i < px.length; i += 4) if (px[i]) n++;
  raiz.dataset.pixels = String(n);
  raiz.dataset.spike = n > 0 ? 'dibujado' : 'vacio';
  if (raiz.dataset.modo === 'servido') {
    fetch('ping').then(function (r) { raiz.dataset.fetch = String(r.status); },
      function () { raiz.dataset.fetch = 'error'; });
  } else { raiz.dataset.fetch = 'n/a'; }
})();
`;
const CSS = 'body{font:14px system-ui,sans-serif;margin:16px}canvas{border:1px solid #475569}\n';

function page({ modo, csp, nonce = null, inline = null }) {
  const n = nonce ? ' nonce="' + nonce + '"' : '';
  const meta = csp ? '<meta http-equiv="Content-Security-Policy" content="' + csp + '">' : '';
  const scripts = inline
    ? '<script>' + inline.chart + '</script><script>' + inline.spike + '</script>'
    : '<script' + n + ' src="vendor/chart.js/chart.umd.min.js"></script><script' + n + ' src="assets/spike.js"></script>';
  return '<!doctype html><html lang="es" data-modo="' + modo + '"><head><meta charset="utf-8">' + meta
    + '<title>Pico CSP</title><link rel="icon" href="data:,"><link rel="stylesheet" href="assets/spike.css"></head><body>'
    + '<main id="main"><h1>Pico CSP</h1><figure><canvas id="grafico" width="320" height="160" aria-label="Horas IA por tarea"></canvas></figure></main>'
    + '<script type="application/json" id="panel-data">' + DATOS + '</script>' + scripts + '</body></html>';
}
const CONTROL = (meta) => '<!doctype html><html lang="es"><head><meta charset="utf-8">' + meta
  + '<title>Control</title><link rel="icon" href="data:,"></head><body><script>window.__inline = 1;</script></body></html>';

function buildSite() {
  const dir = mkdtempSync(join(tmpdir(), 'panel-csp-spike-'));
  mkdirSync(join(dir, 'assets'), { recursive: true });
  mkdirSync(join(dir, 'vendor', 'chart.js'), { recursive: true });
  copyFileSync(CHART, join(dir, 'vendor', 'chart.js', 'chart.umd.min.js'));
  writeFileSync(join(dir, 'assets', 'spike.js'), SPIKE_JS);
  writeFileSync(join(dir, 'assets', 'spike.css'), CSS);
  writeFileSync(join(dir, 'index.html'), page({ modo: 'file', csp: CSP_EXPORTADO }));
  writeFileSync(join(dir, 'control.html'), CONTROL('<meta http-equiv="Content-Security-Policy" content="' + CSP_EXPORTADO + '">'));
  const chartText = readFileSync(CHART, 'utf8');
  const cspHash = "default-src 'none'; script-src " + sri(chartText) + ' ' + sri(SPIKE_JS)
    + "; style-src 'self' 'unsafe-inline'; img-src data:";
  writeFileSync(join(dir, 'hash.html'), page({ modo: 'file', csp: cspHash, inline: { chart: chartText, spike: SPIKE_JS } }));
  return { dir, cspHash };
}

const TYPES = { '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8' };

function serve(dir, policy) {
  const token = randomBytes(24).toString('base64url');
  const server = createServer((req, res) => {
    const nonce = randomBytes(18).toString('base64url');
    const prefix = '/' + token + '/';
    const url = req.url || '';
    if (req.method !== 'GET' || !url.startsWith(prefix) || /[?%\\#]/.test(url)) { res.writeHead(404); return res.end(); }
    const rel = url.slice(prefix.length);
    const headers = { 'Content-Security-Policy': policy(nonce), 'X-Content-Type-Options': 'nosniff', 'Cache-Control': 'no-store' };
    if (rel === '' || rel === 'control') {
      const body = rel === '' ? page({ modo: 'servido', csp: null, nonce }) : CONTROL('');
      res.writeHead(200, { ...headers, 'Content-Type': 'text/html; charset=utf-8' }); return res.end(body);
    }
    if (rel === 'ping') { res.writeHead(200, { ...headers, 'Content-Type': 'application/json' }); return res.end('{"ok":true}'); }
    if (['assets/spike.js', 'assets/spike.css', 'vendor/chart.js/chart.umd.min.js'].includes(rel)) {
      res.writeHead(200, { ...headers, 'Content-Type': TYPES[extname(rel)] });
      return res.end(readFileSync(join(dir, ...rel.split('/'))));
    }
    res.writeHead(404); res.end();
  });
  return new Promise((ok) => server.listen(0, '127.0.0.1', () => {
    const origin = 'http://127.0.0.1:' + server.address().port;
    ok({ server, origin, base: origin + '/' + token + '/' });
  }));
}

const DETECTOR = () => {
  window.__csp = [];
  document.addEventListener('securitypolicyviolation', (e) => {
    window.__csp.push({ directiva: e.violatedDirective, bloqueado: e.blockedURI });
  }, true);
};

async function runCase(browser, { url, allowedOrigin }) {
  const context = await browser.newContext();
  const foreign = [];
  const consoleCsp = [];
  await context.route(/^https?:\/\//, (route) => {
    const u = new URL(route.request().url());
    if (allowedOrigin && u.origin === allowedOrigin) return route.continue();
    foreign.push(u.origin); return route.abort();
  });
  context.on('request', (r) => {
    const u = r.url();
    if (/^(file|data|about|blob):/.test(u)) return;
    if (allowedOrigin && new URL(u).origin === allowedOrigin) return;
    if (!foreign.includes(new URL(u).origin)) foreign.push(new URL(u).origin);
  });
  await context.addInitScript(DETECTOR);
  const p = await context.newPage();
  p.on('console', (m) => { if (/content[- ]security[- ]policy/i.test(m.text())) consoleCsp.push(m.text().slice(0, 160)); });
  await p.goto(url, { waitUntil: 'load' });
  await p.waitForFunction(() => !!document.documentElement.dataset.spike || window.__inline !== undefined
    || document.title === 'Control', null, { timeout: 5000 }).catch(() => {});
  await p.waitForTimeout(400);
  const estado = await p.evaluate(() => ({ detector: Array.isArray(window.__csp), csp: window.__csp || [],
    spike: document.documentElement.dataset.spike || null, pixels: document.documentElement.dataset.pixels || null,
    fetch: document.documentElement.dataset.fetch || null, inline: window.__inline === 1 }));
  await context.close();
  return { ...estado, foreign, consoleCsp };
}

async function launch(pw, engine, channel) {
  const type = pw[engine];
  try { return { browser: await type.launch({ headless: true }), how: 'bundled' }; } catch (error) {
    if (engine !== 'chromium' || !/Executable doesn't exist|executable/i.test(String(error))) throw error;
    const ch = channel || 'msedge';
    return { browser: await type.launch({ headless: true, channel: ch }), how: 'channel ' + ch };
  }
}

function linea(engine, modo, r, extra = '') {
  const v = Math.max(r.csp.length, r.consoleCsp.length);
  return '[' + engine + ' · ' + modo + '] securitypolicyviolation: ' + v + ' · peticiones a otros orígenes: '
    + r.foreign.length + ' · gráfico: ' + (r.spike || 'sin ejecutar') + (r.pixels ? ' (' + r.pixels + ' píxeles)' : '')
    + (r.fetch && r.fetch !== 'n/a' ? ' · fetch mismo origen: ' + r.fetch : '') + extra
    + (r.csp.length ? ' · directivas: ' + [...new Set(r.csp.map((c) => c.directiva + ' ← ' + bloqueado(c.bloqueado)))].join(', ') : '');
}

// Qué se bloqueó, sin rutas locales ni token: «inline», el último segmento del recurso o su esquema.
function bloqueado(uri) {
  if (!uri || uri === 'inline' || uri === 'eval') return uri || 'inline';
  try { const u = new URL(uri); return (u.protocol === 'file:' ? 'file:…/' : '<origen>/…/') + u.pathname.split('/').pop(); } catch { return 'otro'; }
}

async function main() {
  const opts = args(process.argv.slice(2));
  if (!existsSync(CHART)) { console.error('falta ' + CHART.slice(ROOT.length + 1).split(sep).join('/') + ' (T-02)'); process.exit(2); }
  const loaded = loadPlaywright(opts.playwrightDir);
  if (!loaded) {
    console.error('Playwright no está instalado (ni --playwright-dir/PLAYWRIGHT_DIR ni agent-kits/qa/runner): '
      + 'instálalo con permiso del usuario (npm i @playwright/test) y los navegadores (npx playwright install). '
      + 'Sin Playwright no hay veredicto.');
    process.exit(2);
  }
  for (const p of [CSP_EXPORTADO, cspServido('N')]) {
    const scriptSrc = (p.split(';').find((d) => d.trim().startsWith('script-src')) || '');
    if (/unsafe-(eval|inline)/.test(scriptSrc)) { console.error('política inválida: ' + p); process.exit(1); }
  }
  const { dir, cspHash } = buildSite();
  const fileUrl = (name) => pathToFileURL(join(dir, name)).href;
  console.log('Playwright: cargado de ' + (loaded.from === opts.playwrightDir ? '--playwright-dir' : loaded.from));
  console.log('Política exportada: ' + CSP_EXPORTADO);
  console.log("Política servida:   " + cspServido('<nonce>'));
  let fallos = 0, casos = 0;
  const resumen = [];
  try {
    for (const engine of opts.engines) {
      let launched;
      try { launched = await launch(loaded.pw, engine, opts.chromiumChannel); } catch (error) {
        console.error('[' + engine + '] navegador no disponible: ' + String(error.message || error).split('\n')[0]
          + ' — instálalo con `npx playwright install ' + engine + '` (permiso del usuario).');
        process.exitCode = 2; return;
      }
      const { browser, how } = launched;
      console.log('[' + engine + '] ' + browser.version() + ' (' + how + ')');
      try {
        const srv = await serve(dir, cspServido);
        try {
          const servido = await runCase(browser, { url: srv.base, allowedOrigin: srv.origin });
          const controlS = await runCase(browser, { url: srv.base + 'control', allowedOrigin: srv.origin });
          const okS = servido.detector && servido.csp.length === 0 && servido.consoleCsp.length === 0
            && servido.foreign.length === 0 && servido.spike === 'dibujado' && servido.fetch === '200';
          const ctlS = !controlS.inline && Math.max(controlS.csp.length, controlS.consoleCsp.length) >= 1;
          console.log(linea(engine, 'servido', servido) + ' → ' + (okS ? 'OK' : 'FALLA'));
          console.log(linea(engine, 'servido · control inline', controlS, ' · inline ejecutado: ' + (controlS.inline ? 'sí' : 'no')) + ' → ' + (ctlS ? 'detector OK' : 'DETECTOR ROTO'));
          casos++; if (!okS || !ctlS) fallos++;
          resumen.push([engine, 'servido', okS && ctlS]);
        } finally { srv.server.close(); }
        const actual = await serve(dir, cspServidoActual);
        try {
          const r = await runCase(browser, { url: actual.base, allowedOrigin: actual.origin });
          console.log(linea(engine, 'servido · cabecera ACTUAL de serve_panel.py (diagnóstico)', r));
        } finally { actual.server.close(); }
        const exportado = await runCase(browser, { url: fileUrl('index.html'), allowedOrigin: null });
        const controlF = await runCase(browser, { url: fileUrl('control.html'), allowedOrigin: null });
        const okF = exportado.detector && exportado.csp.length === 0 && exportado.consoleCsp.length === 0
          && exportado.foreign.length === 0 && exportado.spike === 'dibujado';
        const ctlF = !controlF.inline && Math.max(controlF.csp.length, controlF.consoleCsp.length) >= 1;
        console.log(linea(engine, 'file://', exportado) + ' → ' + (okF ? 'OK' : 'FALLA'));
        console.log(linea(engine, 'file:// · control inline', controlF, ' · inline ejecutado: ' + (controlF.inline ? 'sí' : 'no')) + ' → ' + (ctlF ? 'detector OK' : 'DETECTOR ROTO'));
        casos++; if (!okF || !ctlF) fallos++;
        resumen.push([engine, 'file://', okF && ctlF]);
        if (opts.fallback) {
          const hash = await runCase(browser, { url: fileUrl('hash.html'), allowedOrigin: null });
          const okH = hash.csp.length === 0 && hash.consoleCsp.length === 0 && hash.foreign.length === 0 && hash.spike === 'dibujado';
          console.log(linea(engine, "file:// · respaldo 'sha256-…' (informativo)", hash) + ' → ' + (okH ? 'OK' : 'FALLA'));
        }
      } finally { await browser.close(); }
    }
  } finally { rmSync(dir, { recursive: true, force: true }); }
  if (opts.fallback) console.log('Política del respaldo (hash de Chart.js 4.5.1 + spike.js): ' + cspHash.replace(/'sha256-[^']+'/g, (m) => m.slice(0, 20) + "…'"));
  console.log('Casos: ' + casos + ' · fallidos: ' + fallos);
  const fileOk = resumen.filter((r) => r[1] === 'file://').every((r) => r[2]);
  console.log(fallos === 0
    ? "Decisión: `script-src 'self' file:` vale en " + opts.engines.join(' y ') + "; no hace falta el respaldo con 'sha256-…'."
    : (fileOk ? 'Decisión pendiente: falla el modo servido (ver líneas).'
      : "Decisión: `file:` NO vale en todos los motores → respaldo determinista (Chart.js incrustado + 'sha256-…')."));
  process.exitCode = fallos ? 1 : 0;
}

main().catch((error) => { console.error('pico CSP: ' + (error && error.stack || error)); process.exit(1); });
