/* Cartera del roadmap: carga, validación y formato compartidos por Inicio e Iniciativas.
   Servido: consulta `api/cartera` (ruta relativa, sin credenciales). Exportado: lee el JSON incrustado en
   `panel-data` (clave `cartera`). Los topes de texto son los de `panel_data.TOPES` y `serve_panel._CAPS`.
   Un dato ausente es `null` y se dice; nunca se pinta como 0. Sin red salvo `api/cartera`, sin HTML insertado. */
(function (raiz) {
  'use strict';

  var CATEGORIAS = [['borrador', 'Borrador'], ['aprobada', 'Aprobada'], ['implementada', 'Implementada'],
                    ['obsoleta', 'Obsoleta'], ['ilegible', 'Ilegible'], ['sin_spec', 'Sin spec'],
                    ['no_reconocido', 'Estado no reconocido']];
  var ESTADOS_LEDGER = ['ok', 'fuera_de_tope', 'ilegible', 'sin_lectura', 'sin_ledger'];
  var MOTIVOS = { sin_estado: 'la spec no declara un estado legible', sin_lectura: 'no se pudo leer',
                  fuera_de_tope: 'fuera del tope de lectura' };
  var CODIGOS = ['fuera_de_tope', 'gaps_abiertos', 'completado_sin_marcar', 'sin_estimacion'];
  var ESTADOS_RESPUESTA = ['ok', 'partial', 'not_found', 'unavailable'];
  var REFRESCO_MS = 10000;
  var PLAZO_MS = 4000;

  function largo(texto) { return Array.from(texto).length; }
  function entero(v) { return typeof v === 'number' && isFinite(v) && Math.floor(v) === v && v >= 0; }
  function numero(v) { return v === null || (typeof v === 'number' && isFinite(v) && v >= 0); }
  function texto(v, tope) { return typeof v === 'string' && largo(v) <= tope; }
  function textoONulo(v, tope) { return v === null || texto(v, tope); }
  function objeto(v) { return v !== null && typeof v === 'object' && !Array.isArray(v); }
  function incluye(lista, v) { return lista.indexOf(v) !== -1; }
  function par(v) { return objeto(v) && numero(v.real) && numero(v.est); }

  function validaTareas(t) {
    return t === null || (objeto(t) && entero(t.total) && entero(t.completadas) && t.completadas <= t.total
      && entero(t.pct) && t.pct <= 100);
  }

  function validaFila(f, ids) {
    if (!objeto(f) || typeof f.id !== 'string' || !/^[a-f0-9]{16}$/.test(f.id) || ids[f.id]) { return false; }
    ids[f.id] = true;
    if (!texto(f.slug, 80) || !texto(f.titulo, 160)) { return false; }
    if (f.fecha !== null && !(typeof f.fecha === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(f.fecha))) { return false; }
    if (!CATEGORIAS.some(function (c) { return c[0] === f.categoria; })) { return false; }
    if (f.literal !== undefined && !texto(f.literal, 48)) { return false; }
    if (f.motivo !== undefined && !Object.prototype.hasOwnProperty.call(MOTIVOS, f.motivo)) { return false; }
    if (typeof f.tiene_plan !== 'boolean' || !incluye(ESTADOS_LEDGER, f.ledger) || !validaTareas(f.tareas)) { return false; }
    var h = f.horas, c = f.coste, p = f.procedencia;
    if (!par(h) || !par(h.humanas)) { return false; }
    if (!objeto(c) || !numero(c.real_eur) || !numero(c.est_eur) || typeof c.real_parcial !== 'boolean'
        || !textoONulo(c.est_texto, 120)) { return false; }
    if (!objeto(p) || !entero(p.medidos) || !entero(p.estimados) || !entero(p.desconocidos)) { return false; }
    return Array.isArray(f.alertas) && f.alertas.length <= 8 && f.alertas.every(function (a) {
      return objeto(a) && incluye(CODIGOS, a.codigo) && entero(a.n) && a.n >= 1;
    });
  }

  function validaTotales(t, completa) {
    if (!objeto(t) || !entero(t.iniciativas) || !objeto(t.por_estado)) { return false; }
    if (completa && !CATEGORIAS.every(function (c) { return entero(t.por_estado[c[0]]); })) { return false; }
    if (t.tareas !== null && !(objeto(t.tareas) && validaTareas(t.tareas) && entero(t.tareas.ledgers))) { return false; }
    if (!Array.isArray(t.fuera_de_tope) || t.fuera_de_tope.length > 64 || !t.fuera_de_tope.every(function (x) {
      return objeto(x) && typeof x.id === 'string' && /^[a-f0-9]{16}$/.test(x.id) && texto(x.slug, 80);
    })) { return false; }
    var c = t.coste, p = t.procedencia;
    return objeto(c) && numero(c.real_eur) && entero(c.real_n) && numero(c.est_eur) && entero(c.est_n)
      && objeto(p) && entero(p.medidos) && entero(p.estimados) && entero(p.desconocidos);
  }

  /* Forma y topes de `api/cartera`. Un campo fuera de contrato invalida la respuesta entera. */
  function validar(d) {
    if (!objeto(d) || d.version !== 1 || d.source !== 'roadmap_cartera' || !incluye(ESTADOS_RESPUESTA, d.status)
        || typeof d.complete !== 'boolean') { return false; }
    if (typeof d.observed_at !== 'string' || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$/.test(d.observed_at)
        || !isFinite(Date.parse(d.observed_at))) { return false; }
    if (!Array.isArray(d.issues) || d.issues.length > 16 || !d.issues.every(function (i) {
      return objeto(i) && typeof i.status === 'string' && /^[-a-z_]{1,48}$/.test(i.status);
    })) { return false; }
    if (!Array.isArray(d.iniciativas) || d.iniciativas.length > 64) { return false; }
    var ids = {};
    return d.iniciativas.every(function (f) { return validaFila(f, ids); })
      && validaTotales(d.totales, d.status === 'ok' || d.status === 'partial');
  }

  /* --- formato: sin Intl para que el texto no dependa de la configuración regional del equipo --- */
  function agrupar(entera) { return entera.replace(/\B(?=(\d{3})+(?!\d))/g, '.'); }
  function num(v, decimales) {
    if (v === null || v === undefined || !isFinite(v)) { return 'sin datos'; }
    var partes = Number(v).toFixed(decimales === undefined ? 0 : decimales).split('.');
    return agrupar(partes[0]) + (partes[1] ? ',' + partes[1] : '');
  }
  function eur(v) { return v === null || v === undefined ? 'sin datos' : num(v, v % 1 === 0 ? 0 : 2) + ' €'; }
  function horas(v) { return v === null || v === undefined ? 'sin datos' : num(v, 2) + ' h'; }
  function alertaTexto(a) {
    var n = a.n;
    if (a.codigo === 'fuera_de_tope') { return 'Ledger fuera del tope de lectura (256 KiB): no suma en el avance.'; }
    if (a.codigo === 'gaps_abiertos') { return n === 1 ? '1 gap de revisión abierto' : n + ' gaps de revisión abiertos'; }
    if (a.codigo === 'completado_sin_marcar') {
      return n === 1 ? '1 tarea completada con criterios sin marcar' : n + ' tareas completadas con criterios sin marcar';
    }
    return 'Sin estimación: faltan las horas y el coste estimados';
  }
  function categoriaTexto(f) {
    var base = CATEGORIAS.filter(function (c) { return c[0] === f.categoria; })[0][1];
    if (f.categoria === 'ilegible' && f.motivo) { return base + ' (' + MOTIVOS[f.motivo] + ')'; }
    if (f.categoria === 'no_reconocido' && f.literal) { return base + ': «' + f.literal + '»'; }
    return base;
  }

  function leerDatos() {
    var nodo = raiz.document.getElementById('panel-data');
    try { return JSON.parse(nodo.textContent); } catch (e) { return {}; }
  }

  /* Pide la cartera y llama a `alRecibir(cartera)` con una respuesta válida o a `alFallar(hayPrevio, motivo)` si
     no la hay (`motivo`: `sin_cartera` en una copia exportada sin `--project`, `invalida`, `no_disponible`). Exportado: una sola lectura del JSON incrustado. Servido: lectura inicial y refresco cada 10 s, sin
     solaparse, parado mientras la pestaña está oculta; un fallo conserva la última vista. */
  function iniciar(alRecibir, alFallar) {
    var datos = leerDatos();
    if (datos.modo !== 'servido') {
      if (datos.cartera === undefined) { alFallar(false, 'sin_cartera'); }
      else if (validar(datos.cartera)) { alRecibir(datos.cartera); }
      else { alFallar(false, 'invalida'); }
      return;
    }
    var temporizador = null, enVuelo = false, hayPrevio = false, controlador = null;
    function parar() { if (temporizador !== null) { raiz.clearTimeout(temporizador); temporizador = null; } }
    function programar() {
      parar();
      if (!raiz.document.hidden) { temporizador = raiz.setTimeout(leer, REFRESCO_MS); }
    }
    function leer() {
      parar();
      if (raiz.document.hidden || enVuelo) { return; }
      enVuelo = true;
      controlador = new raiz.AbortController();
      var actual = controlador;
      var plazo = raiz.setTimeout(function () { actual.abort(); }, PLAZO_MS);
      raiz.fetch('api/cartera', { credentials: 'omit', cache: 'no-store', signal: actual.signal })
        .then(function (r) { if (!r.ok) { throw new Error('no disponible'); } return r.json(); })
        .then(function (d) {
          if (!validar(d)) { throw new Error('no disponible'); }
          if (d.status === 'unavailable' && hayPrevio) { throw new Error('no disponible'); }
          hayPrevio = hayPrevio || d.status !== 'unavailable';
          alRecibir(d);
        })
        .catch(function () { alFallar(hayPrevio, 'no_disponible'); })
        .then(function () { raiz.clearTimeout(plazo); controlador = null; enVuelo = false; programar(); });
    }
    raiz.document.addEventListener('visibilitychange', function () {
      if (raiz.document.hidden) { parar(); if (controlador) { controlador.abort(); } } else { leer(); }
    });
    leer();
  }

  var Cartera = { CATEGORIAS: CATEGORIAS, MOTIVOS: MOTIVOS, validar: validar, iniciar: iniciar, num: num, eur: eur,
                  horas: horas, alertaTexto: alertaTexto, categoriaTexto: categoriaTexto };
  raiz.PanelCartera = Cartera;
  if (typeof module === 'object' && module.exports) { module.exports = Cartera; }
})(typeof window !== 'undefined' ? window : globalThis);
