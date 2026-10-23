/* Página Inicio: iniciativas por estado de spec (gráfico + tabla), avance global y coste real frente al estimado.
   Todas las cifras salen de la cartera (`api/cartera` o el JSON incrustado): aquí solo se muestran, no se recalculan.
   Un dato ausente se dice («sin datos»); nunca se pinta como 0. Todo el texto entra por textContent. */
(function (raiz) {
  'use strict';

  var C = function () { return raiz.PanelCartera; };
  var graficoPintado = null;
  var chartjsDisponible = true;

  function el(etiqueta, clase, texto) {
    var nodo = raiz.document.createElement(etiqueta);
    if (clase) { nodo.className = clase; }
    if (texto !== undefined) { nodo.textContent = texto; }
    return nodo;
  }
  function limpiar(id) {
    var nodo = raiz.document.getElementById(id);
    if (nodo) { nodo.replaceChildren(); }
    return nodo;
  }
  function pongo(id, texto) {
    var nodo = raiz.document.getElementById(id);
    if (nodo) { nodo.textContent = texto; }
    return nodo;
  }

  function hayDatos(d) { return d && (d.status === 'ok' || d.status === 'partial'); }

  function estadoGeneral(d, motivo) {
    if (!d && motivo === 'calculando') { return 'Calculando la cartera… (reintento en ' + C().REINTENTO_S + ' s)'; }
    if (!d && motivo === 'sin_cartera') {
      return 'Sin datos: esta copia estática no incluye la cartera (se genera con --project).';
    }
    if (!d) { return 'No se pudo leer la cartera. Sin datos de iniciativas; vuelve a intentarlo.'; }
    if (d.status === 'unavailable') { return 'Cartera no disponible: no se pudo leer el roadmap. Sin datos.'; }
    if (d.status === 'not_found') { return 'No se encontró el roadmap del proyecto (docs/roadmap). Sin datos.'; }
    var fecha = ' Lectura obtenida: ' + d.observed_at + '.';
    if (d.status === 'partial' || !d.complete) {
      return 'Lectura parcial: se muestran las iniciativas leídas; lo omitido no acredita ausencia ni un total completo.' + fecha;
    }
    if (!d.iniciativas.length) { return 'El roadmap no tiene iniciativas.' + fecha; }
    return 'Cartera derivada de docs/roadmap.' + fecha;
  }

  function dibujarEstados(d) {
    var contenedor = raiz.document.getElementById('grafico-estados');
    if (!contenedor || !raiz.PanelCharts) { return; }
    var valores = C().CATEGORIAS.map(function (c) { return hayDatos(d) ? d.totales.por_estado[c[0]] : null; });
    var clave = JSON.stringify(valores);
    if (clave === graficoPintado) { return; }
    graficoPintado = clave;
    contenedor.replaceChildren();
    raiz.PanelCharts.dibujar(contenedor, {
      id: 'grafico-estados-spec',
      titulo: 'Iniciativas por estado de spec',
      descripcion: 'Número de iniciativas en cada estado de su spec; una spec ilegible no cuenta en ningún estado.',
      tipo: 'bar',
      categoria: 'Estado de la spec',
      etiquetas: C().CATEGORIAS.map(function (c) { return c[1]; }),
      origen: 'api/cartera (cifras de build_dashboard.py --json)',
      series: [{ nombre: 'Iniciativas', valores: valores }]
    }, { chartDisponible: chartjsDisponible });
  }

  function dibujarAvance(d) {
    var avance = raiz.document.getElementById('avance-global');
    var fuera = limpiar('avance-fuera-de-tope');
    if (!avance) { return; }
    if (!hayDatos(d)) { avance.textContent = 'Sin datos: no hay lectura de la cartera.'; return; }
    var t = d.totales.tareas;
    avance.textContent = t
      ? t.completadas + ' de ' + t.total + ' tareas completadas (' + t.pct + ' %) · suma de ' + t.ledgers
        + (t.ledgers === 1 ? ' ledger leído' : ' ledgers leídos')
      : 'Sin datos: ningún ledger legible dentro del tope de lectura.';
    if (fuera && d.totales.fuera_de_tope.length) {
      fuera.appendChild(el('p', 'ausencia', 'Ledgers fuera del tope de lectura (256 KiB); no suman en las tareas completadas ni en el total:'));
      var lista = el('ul');
      d.totales.fuera_de_tope.forEach(function (x) { lista.appendChild(el('li', '', x.slug)); });
      fuera.appendChild(lista);
    }
    var sinLeer = d.iniciativas.filter(function (f) { return f.ledger === 'ilegible' || f.ledger === 'sin_lectura'; });
    if (fuera && sinLeer.length) {
      fuera.appendChild(el('p', 'ausencia', 'Ledgers ilegibles o sin leer (tampoco suman): '
        + sinLeer.map(function (f) { return f.slug; }).join(', ')));
    }
  }

  function filaCoste(lista, nombre, total, n, cuantas) {
    lista.appendChild(el('dt', '', nombre));
    lista.appendChild(el('dd', '', n === 0
      ? 'sin datos'
      : C().eur(total) + ' · dato en ' + n + ' de ' + cuantas + (cuantas === 1 ? ' iniciativa' : ' iniciativas')));
  }

  function dibujarCoste(d) {
    var contenedor = limpiar('coste-cartera');
    var procedencia = raiz.document.getElementById('coste-procedencia');
    if (!contenedor || !procedencia) { return; }
    if (!hayDatos(d)) {
      contenedor.appendChild(el('p', 'ausencia', 'Sin datos: no hay lectura de la cartera.'));
      procedencia.textContent = '';
      return;
    }
    var t = d.totales, lista = el('dl');
    filaCoste(lista, 'Coste real', t.coste.real_eur, t.coste.real_n, t.iniciativas);
    filaCoste(lista, 'Coste estimado', t.coste.est_eur, t.coste.est_n, t.iniciativas);
    contenedor.appendChild(lista);
    contenedor.appendChild(el('p', 'filter-note', 'Cada total suma solo las iniciativas con dato; una iniciativa sin estimación no suma 0.'));
    procedencia.textContent = 'procedencia: ' + t.procedencia.medidos + ' medidos · ' + t.procedencia.estimados
      + ' estimados · ' + t.procedencia.desconocidos + ' desconocidos';
  }

  function dibujar(d, motivo) {
    pongo('cartera-estado', estadoGeneral(d, motivo));
    dibujarEstados(d);
    dibujarAvance(d);
    dibujarCoste(d);
  }

  function iniciar() {
    var nodo = raiz.document.getElementById('panel-data');
    var modo = null;
    try {
      var incrustados = JSON.parse(nodo.textContent);
      chartjsDisponible = incrustados.chartjs_disponible !== false;
      modo = incrustados.modo;
    } catch (e) { chartjsDisponible = false; }
    iniciarActividad(modo);
    var previo = null;
    C().iniciar(function (cartera) { previo = cartera; dibujar(cartera); },
      function (hayPrevio, motivo) {
        if (hayPrevio && previo) {
          pongo('cartera-estado', 'No se pudo actualizar. Se conserva la última vista y su fecha ('
            + previo.observed_at + '); no se acredita su vigencia.');
        } else { dibujar(null, motivo); }
      });
  }

  /* Actividad reciente (panel-redesign T-50, CA-04): los últimos eventos de `api/actividad-runs` (solo servido),
     con enlace a Agentes en vivo. En el exportado no hay actividad y se dice. Todo por textContent. */
  var ACTIVAR = 'Para activarla, define "sesion": {"actividad": true} en .claude/dev.json.';
  var RUNTIMES = { claude: 'Claude Code', codex: 'Codex', opencode: 'OpenCode' };
  var ROLES = ['analyst', 'evaluator', 'architect', 'planner', 'implementer', 'reviewer', 'qa', 'documenter',
    'knowledge-curator', 'nemesis', 'other'];
  var CLAVES_RECIENTE = ['key16', 'runtime', 'role', 'scope', 'tool', 'tarea', 'observed_at', 'edad_s'];

  function forma(v, claves) {
    return v !== null && typeof v === 'object' && !Array.isArray(v) && Object.keys(v).length === claves.length
      && claves.every(function (k) { return Object.prototype.hasOwnProperty.call(v, k); });
  }
  function cifra(v) { return typeof v === 'number' && isFinite(v) && v >= 0 && v <= Number.MAX_SAFE_INTEGER; }
  function recienteValido(e) {
    return forma(e, CLAVES_RECIENTE) && typeof e.key16 === 'string' && /^[a-f0-9]{16}$/.test(e.key16)
      && Object.prototype.hasOwnProperty.call(RUNTIMES, e.runtime) && (e.role === null || ROLES.indexOf(e.role) >= 0)
      && (e.scope === null || e.scope === 'subagent' || e.scope === 'session')
      && typeof e.tool === 'string' && e.tool.length <= 64 && (e.tarea === null || (typeof e.tarea === 'string' && e.tarea.length <= 200))
      && cifra(e.observed_at) && (e.edad_s === null || cifra(e.edad_s));
  }
  function actividadValida(d) {
    if (d === null || typeof d !== 'object' || d.schema_version !== 1 || d.collection_complete !== false) { return false; }
    if (d.status === 'unavailable') { return typeof d.reason === 'string' && /^[a-z_]{1,40}$/.test(d.reason); }
    return d.status === 'ok' && d.reason === null && Array.isArray(d.recientes) && d.recientes.length <= 10
      && d.recientes.every(recienteValido);
  }
  function haceCuanto(s) {
    if (s === null) { return 'hace: sin datos'; }
    if (s < 60) { return 'hace ' + Math.round(s) + ' s'; }
    if (s < 3600) { return 'hace ' + Math.floor(s / 60) + ' min'; }
    return 'hace ' + Math.floor(s / 3600) + ' h';
  }

  function seccionActividad() {
    var main = raiz.document.getElementById('main');
    if (!main) { return null; }
    var seccion = el('section'); seccion.id = 'inicio-actividad'; seccion.setAttribute('id', 'inicio-actividad');
    var estado = el('p', 'filter-note', 'Leyendo la actividad…');
    estado.setAttribute('role', 'status'); estado.setAttribute('aria-live', 'polite');
    var lista = el('ul');
    var enlace = el('a', '', 'Ver Agentes en vivo'); enlace.setAttribute('href', 'agentes.html');
    var nota = el('p', 'filter-note', 'Captura informativa: puede tener huecos.');
    seccion.append(el('h2', '', 'Actividad reciente'), estado, lista, nota, enlace);
    main.append(seccion);
    return { estado: estado, lista: lista };
  }

  function pintarActividad(partes, d) {
    if (d.status !== 'ok') {
      partes.lista.replaceChildren();
      partes.estado.textContent = d.reason === 'disabled' || d.reason === 'invalid_config'
        ? 'Actividad desactivada. ' + ACTIVAR
        : d.reason === 'state_missing' ? 'Aún no hay actividad registrada.' : 'Actividad no disponible (' + d.reason + ').';
      return;
    }
    partes.estado.textContent = d.recientes.length ? 'Últimos eventos de herramienta (orden de recepción).'
      : 'Aún sin eventos registrados en las últimas 24 h.';
    partes.lista.replaceChildren.apply(partes.lista, d.recientes.map(function (e) {
      var quien = e.scope === 'session' || e.role === null ? 'sesión' : e.role;
      return el('li', '', quien + ' · ' + RUNTIMES[e.runtime] + ' · ' + e.tool + ' · tarea: '
        + (e.tarea === null ? 'sin atribuir' : e.tarea) + ' · ' + haceCuanto(e.edad_s));
    }));
  }

  function iniciarActividad(modo) {
    var partes = seccionActividad();
    if (!partes) { return; }
    if (modo !== 'servido') {
      partes.estado.textContent = 'La actividad de los agentes solo existe en el panel servido (/plugin-catalog --serve).';
      return;
    }
    var temporizador = null, ocupado = false;
    function leer() {
      if (ocupado || raiz.document.hidden) { return; }
      ocupado = true; clearTimeout(temporizador);
      var control = new AbortController();
      var plazo = setTimeout(function () { control.abort(); }, 4000);
      raiz.fetch('api/actividad-runs', { method: 'GET', credentials: 'omit', cache: 'no-store', signal: control.signal })
        .then(function (r) { if (!r.ok) { throw Error('unavailable'); } return r.json(); })
        .then(function (d) { if (!actividadValida(d)) { throw Error('invalid'); } pintarActividad(partes, d); })
        .catch(function () {
          partes.lista.replaceChildren();
          partes.estado.textContent = 'No se pudo leer la actividad; se reintenta en 5 s.';
        })
        .then(function () {
          clearTimeout(plazo); ocupado = false;
          if (!raiz.document.hidden) { temporizador = setTimeout(leer, 5000); }
        });
    }
    // T-50 fix1 (B1): hidden pauses the polling; visible again resumes it (as page-agentes.js does).
    raiz.document.addEventListener('visibilitychange', function () {
      clearTimeout(temporizador); temporizador = null;
      if (!raiz.document.hidden) { leer(); }
    });
    leer();
  }

  var Inicio = { iniciar: iniciar, dibujar: dibujar };
  raiz.PanelInicio = Inicio;
  if (raiz.document && raiz.document.getElementById && raiz.document.getElementById('cartera-estado')) { iniciar(); }
})(typeof window !== 'undefined' ? window : globalThis);
