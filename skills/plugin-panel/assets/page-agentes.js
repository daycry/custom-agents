/* Página Agentes en vivo (panel-redesign T-49): una fila por run y, al abrir uno, su línea de tiempo.
   Solo modo servido: `api/actividad-runs` y `api/actividad-run-<key16>` (GET, mismo origen, sin credenciales),
   refresco cada 5 s como el resto de vistas vivas. Todo el texto entra por textContent; un dato fuera de forma
   no llega al DOM y la página dice «historial no disponible» en lugar de mostrar algo parcial.
   Lo que un runtime no aporta se declara siempre (CA-42); la captura es informativa y puede tener huecos. */
(function (raiz) {
  'use strict';
  var doc = raiz.document;
  var main = doc.getElementById('main');
  if (!main) { return; }

  var ACTIVAR = 'Para activarla, define "sesion": {"actividad": true} en .claude/dev.json.';
  var RUNTIMES = { claude: 'Claude Code', codex: 'Codex', opencode: 'OpenCode' };
  var ESTADOS = { en_curso: 'en curso', sin_senal_reciente: 'sin señal reciente', respuesta_terminada: 'respuesta terminada' };
  var ROLES = ['analyst', 'evaluator', 'architect', 'planner', 'implementer', 'reviewer', 'qa', 'documenter',
    'knowledge-curator', 'nemesis', 'other'];
  var MOTIVOS = ['disabled', 'invalid_config', 'state_missing', 'unowned_state', 'invalid_state', 'unsafe_state',
    'state_busy', 'deadline_exceeded', 'state_budget', 'durability_degraded', 'invalid_input', 'input_budget',
    'project_mismatch', 'unsupported_event', 'invalid_identity', 'role_map_unavailable', 'quota_exceeded',
    'revision_exhausted', 'invalid_clock', 'reader_unavailable', 'invalid_history', 'response_budget'];
  var DECLARACIONES = [
    'Claude Code: un evento por herramienta terminada, con duración y resultado; identifica al subagente.',
    'Codex no identifica el subagente en eventos de herramienta: se agrupan por sesión. Sin duración ni resultado (sin datos); las búsquedas web alojadas no emiten eventos.',
    'OpenCode: un evento por herramienta terminada, sin duración (sin datos); el subagente corre en una sesión hija. Si el adaptador instalado no declara la vinculación de herramientas, este runtime no emite eventos de herramienta.',
    'Captura informativa: puede tener huecos (un evento que no se pudo escribir se pierde y no se reintenta).',
    'Los eventos se listan en orden de recepción, no de ejecución.'
  ];

  function el(etiqueta, texto, id) {
    var nodo = doc.createElement(etiqueta);
    if (id) { nodo.id = id; }
    if (texto !== undefined) { nodo.textContent = texto; }
    return nodo;
  }

  // ---- validación (formas cerradas; nada parcial llega al DOM) ----
  function objeto(v, claves) {
    return v !== null && typeof v === 'object' && !Array.isArray(v) && Object.keys(v).length === claves.length
      && claves.every(function (k) { return Object.prototype.hasOwnProperty.call(v, k); });
  }
  function numero(v) { return typeof v === 'number' && isFinite(v) && v >= 0 && v <= Number.MAX_SAFE_INTEGER; }
  function numeroONulo(v) { return v === null || numero(v); }
  function texto(v, tope) { return typeof v === 'string' && v.length <= tope; }
  function textoONulo(v, tope) { return v === null || texto(v, tope); }
  function key16(v) { return typeof v === 'string' && /^[a-f0-9]{16}$/.test(v); }
  function rol(v) { return v === null || ROLES.indexOf(v) >= 0; }
  function runtime(v) { return Object.prototype.hasOwnProperty.call(RUNTIMES, v); }

  var CLAVES_RUN = ['key16', 'runtime', 'scope', 'role', 'estado', 'iniciado_at', 'ultima_senal_at', 'edad_s',
    'duracion_s', 'ultima_herramienta', 'eventos'];
  function runValido(r) {
    return objeto(r, CLAVES_RUN) && key16(r.key16) && runtime(r.runtime) && (r.scope === 'subagent' || r.scope === 'session')
      && rol(r.role) && Object.prototype.hasOwnProperty.call(ESTADOS, r.estado) && numeroONulo(r.iniciado_at)
      && numero(r.ultima_senal_at) && numeroONulo(r.edad_s) && numeroONulo(r.duracion_s)
      && textoONulo(r.ultima_herramienta, 64) && Number.isSafeInteger(r.eventos) && r.eventos >= 0;
  }
  var CLAVES_EVENTO = ['tool', 'resumen', 'tarea', 'duracion_ms', 'resultado', 'observed_at', 'revision'];
  function eventoValido(e) {
    return objeto(e, CLAVES_EVENTO) && texto(e.tool, 64) && texto(e.resumen, 160) && textoONulo(e.tarea, 200)
      && numeroONulo(e.duracion_ms) && (e.resultado === null || e.resultado === 'ok' || e.resultado === 'error')
      && numero(e.observed_at) && Number.isSafeInteger(e.revision) && e.revision >= 1;
  }
  function contador(v) { return Number.isSafeInteger(v) && v >= 0; }
  function noDisponible(d, claves) {
    return objeto(d, claves) && d.status === 'unavailable' && MOTIVOS.indexOf(d.reason) >= 0 && d.collection_complete === false;
  }
  var CLAVES_RUNS = ['schema_version', 'status', 'reason', 'collection_complete', 'recortado', 'descartados_por_tamano',
    'eventos', 'runs', 'recientes'];
  function listaValida(d) {
    if (noDisponible(d, CLAVES_RUNS) || noDisponible(d, CLAVES_RUNS.concat(['activar']))) {
      return Array.isArray(d.runs) && d.runs.length === 0;
    }
    return objeto(d, CLAVES_RUNS) && d.schema_version === 1 && d.status === 'ok' && d.reason === null
      && d.collection_complete === false && contador(d.recortado) && contador(d.descartados_por_tamano)
      && contador(d.eventos) && Array.isArray(d.runs) && d.runs.length <= 64 && d.runs.every(runValido)
      && Array.isArray(d.recientes);
  }
  var CLAVES_LINEA = ['schema_version', 'status', 'reason', 'collection_complete', 'key16', 'run', 'recortado',
    'recortado_historial', 'descartados_por_tamano', 'eventos'];
  function lineaValida(d, clave) {
    if (noDisponible(d, CLAVES_LINEA) || noDisponible(d, CLAVES_LINEA.concat(['activar']))) {
      return Array.isArray(d.eventos) && d.eventos.length === 0;
    }
    return objeto(d, CLAVES_LINEA) && d.schema_version === 1 && d.status === 'ok' && d.reason === null
      && d.collection_complete === false && d.key16 === clave && runValido(d.run) && d.run.key16 === clave
      && contador(d.recortado) && contador(d.recortado_historial) && contador(d.descartados_por_tamano)
      && Array.isArray(d.eventos) && d.eventos.length <= 150 && d.eventos.every(eventoValido);
  }

  // ---- formato ----
  function fecha(segundos) {
    if (segundos === null) { return 'sin datos'; }
    var f = new Date(segundos * 1000);
    return isNaN(f.getTime()) ? 'sin datos' : f.toISOString();
  }
  function duracion(segundos) {
    if (segundos === null) { return 'sin datos'; }
    var s = Math.round(segundos), h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), r = s % 60;
    return (h ? h + ' h ' : '') + (h || m ? m + ' min ' : '') + r + ' s';
  }
  function rolTexto(r) {
    if (r.scope === 'session') { return r.runtime === 'codex' ? 'sesión (Codex agrupa por sesión)' : 'sesión'; }
    return r.role === null ? 'sin rol' : r.role;
  }
  function motivoTexto(d) {
    if (d.reason === 'disabled' || d.reason === 'invalid_config') { return 'Actividad desactivada. ' + ACTIVAR; }
    if (d.reason === 'state_missing') { return 'Aún no hay actividad registrada.'; }
    return 'Historial no disponible (' + d.reason + ').';
  }

  // ---- estructura ----
  var seccion = el('section', undefined, 'agentes-runs');
  var cabecera = el('div'); cabecera.className = 'section-head';
  var titulo = el('div');
  titulo.append(el('h2', 'Runs de agentes'),
    el('p', 'Una fila por run: runtime, rol, inicio, duración y última herramienta. Ningún estado acredita un proceso vivo ni un agente destruido.'));
  cabecera.append(titulo);
  var estado = el('p', 'Consultando el historial…', 'agentes-estado');
  estado.setAttribute('role', 'status'); estado.setAttribute('aria-live', 'polite');
  var recorte = el('p', '', 'agentes-recorte');
  var avisos = el('ul', undefined, 'agentes-declaraciones');
  DECLARACIONES.forEach(function (t) { avisos.append(el('li', t)); });
  var tabla = el('table', undefined, 'agentes-tabla');
  var cuerpo = el('tbody', undefined, 'agentes-filas');
  var cabezaTabla = el('thead'), filaCabeza = el('tr');
  ['Runtime', 'Rol', 'Inicio', 'Duración', 'Última herramienta', 'Estado', 'Línea de tiempo'].forEach(function (t) {
    var th = el('th', t); th.setAttribute('scope', 'col'); filaCabeza.append(th);
  });
  cabezaTabla.append(filaCabeza);
  tabla.append(el('caption', 'Runs observados (los más recientes primero)'), cabezaTabla, cuerpo);
  seccion.append(cabecera, estado, recorte, avisos, tabla);

  var linea = el('section', undefined, 'agentes-linea');
  var lineaTitulo = el('h2', 'Línea de tiempo', 'agentes-linea-titulo');
  var lineaEstado = el('p', 'Abre un run para ver su línea de tiempo.', 'agentes-linea-estado');
  lineaEstado.setAttribute('role', 'status'); lineaEstado.setAttribute('aria-live', 'polite');
  var lineaRecorte = el('p', '', 'agentes-linea-recorte');
  var eventos = el('ol', undefined, 'agentes-eventos');
  linea.append(lineaTitulo, lineaEstado, lineaRecorte, eventos);
  main.append(seccion, linea);

  // ---- pintado ----
  var abierto = null;
  function pintarRuns(d) {
    if (d.status !== 'ok') {
      estado.textContent = motivoTexto(d);
      recorte.textContent = '';
      cuerpo.replaceChildren();
      return;
    }
    estado.textContent = d.runs.length
      ? d.runs.length + (d.runs.length === 1 ? ' run observado' : ' runs observados') + ' en las últimas 24 h.'
      : 'Aún sin eventos registrados en las últimas 24 h.';
    var partes = [];
    if (d.recortado > 0) { partes.push('Historial recortado a los últimos ' + d.eventos + ' eventos (' + d.recortado + ' descartados por el tope de 500 eventos o 256 KiB).'); }
    if (d.descartados_por_tamano > 0) { partes.push(d.descartados_por_tamano + ' eventos descartados por tamaño de la entrada.'); }
    recorte.textContent = partes.join(' ');
    cuerpo.replaceChildren.apply(cuerpo, d.runs.map(function (r) {
      var fila = el('tr');
      var boton = el('button', abierto === r.key16 ? 'Abierta' : 'Abrir');
      boton.setAttribute('type', 'button');
      boton.setAttribute('aria-pressed', abierto === r.key16 ? 'true' : 'false');
      boton.addEventListener('click', function () { abrir(r.key16, RUNTIMES[r.runtime] + ' · ' + rolTexto(r)); });
      var celdaBoton = el('td'); celdaBoton.append(boton);
      fila.append(el('td', RUNTIMES[r.runtime]), el('td', rolTexto(r)), el('td', fecha(r.iniciado_at)),
        el('td', duracion(r.duracion_s)), el('td', r.ultima_herramienta === null ? 'sin eventos de herramienta' : r.ultima_herramienta),
        el('td', ESTADOS[r.estado]), celdaBoton);
      return fila;
    }));
  }
  function pintarLinea(d) {
    if (d.status !== 'ok') {
      lineaEstado.textContent = motivoTexto(d);
      lineaRecorte.textContent = '';
      eventos.replaceChildren();
      return;
    }
    lineaEstado.textContent = d.eventos.length + (d.eventos.length === 1 ? ' evento' : ' eventos')
      + ' · ' + ESTADOS[d.run.estado] + ' · duración ' + duracion(d.run.duracion_s) + '.';
    lineaRecorte.textContent = d.recortado > 0 ? 'Historial recortado a los últimos ' + d.eventos.length + ' eventos.' : '';
    eventos.replaceChildren.apply(eventos, d.eventos.map(function (e) {
      var item = el('li');
      item.append(el('span', fecha(e.observed_at) + ' · '), el('strong', e.tool), el('span', ' · ' + e.resumen),
        el('span', ' · tarea: ' + (e.tarea === null ? 'sin atribuir' : e.tarea)),
        el('span', ' · duración: ' + (e.duracion_ms === null ? 'sin datos' : e.duracion_ms + ' ms')),
        el('span', ' · resultado: ' + (e.resultado === null ? 'sin datos' : e.resultado)));
      return item;
    }));
  }

  // ---- red (un pedido en vuelo, 4 s de plazo, refresco de 5 s, pausa con la pestaña oculta) ----
  var temporizador = null, ocupado = false, generacion = 0;
  function pedir(ruta) {
    var control = new AbortController();
    var plazo = setTimeout(function () { control.abort(); }, 4000);
    return fetch(ruta, { method: 'GET', credentials: 'omit', cache: 'no-store', signal: control.signal })
      .then(function (r) { if (!r.ok) { throw Error('unavailable'); } return r.json(); })
      .finally(function () { clearTimeout(plazo); });
  }
  function abrir(clave, etiqueta) {
    if (!key16(clave)) { return; }
    abierto = clave;
    lineaTitulo.textContent = 'Línea de tiempo · ' + etiqueta;
    lineaEstado.textContent = 'Leyendo la línea de tiempo…';
    eventos.replaceChildren(); lineaRecorte.textContent = '';
    ++generacion; ocupado = false; clearTimeout(temporizador); temporizador = null;
    refrescar();
  }
  function refrescar() {
    if (ocupado || doc.hidden) { return; }
    clearTimeout(temporizador); temporizador = null; ocupado = true;
    var version = ++generacion, clave = abierto;
    var lista = pedir('api/actividad-runs').then(function (d) {
      if (version !== generacion) { return; }
      if (!listaValida(d)) { throw Error('invalid'); }
      pintarRuns(d);
    }).catch(function () {
      if (version === generacion) { estado.textContent = 'No se pudo actualizar el historial; se conserva la última vista.'; }
    });
    var detalle = clave === null ? Promise.resolve() : pedir('api/actividad-run-' + clave).then(function (d) {
      if (version !== generacion || clave !== abierto) { return; }
      if (!lineaValida(d, clave)) { throw Error('invalid'); }
      pintarLinea(d);
    }).catch(function () {
      if (version === generacion && clave === abierto) { lineaEstado.textContent = 'No se pudo leer la línea de tiempo (el run puede haber caducado).'; }
    });
    Promise.all([lista, detalle]).then(function () {
      if (version !== generacion) { return; }
      ocupado = false;
      if (!doc.hidden) { temporizador = setTimeout(refrescar, 5000); }
    });
  }
  doc.addEventListener('visibilitychange', function () {
    clearTimeout(temporizador); temporizador = null;
    if (doc.hidden) { ++generacion; ocupado = false; } else { refrescar(); }
  });
  refrescar();
})(typeof window !== 'undefined' ? window : globalThis);
