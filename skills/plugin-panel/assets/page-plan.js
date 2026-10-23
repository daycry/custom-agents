/* Página Plan de UNA iniciativa (`plan-<id16>.html`): kanban de SOLO LECTURA con las cinco columnas del
   vocabulario de estados del ledger y una franja «Estado no reconocido» (con el literal) para lo que no case.
   Una tarjeta por `T-XX`: id, título, fase, horas IA real y estimadas con su procedencia y nº de gaps abiertos.
   Abrir una tarjeta (clic o Enter sobre su botón) muestra el detalle de la tarea: descripción, criterios con su
   casilla, verificación y su salida, dependencias, última revisión con sus gaps abiertos y la marca «archivado».
   Servido: consulta `api/plan-<id16>` y `api/plan-<id16>-<T-XX>` (rutas relativas, sin credenciales). Exportado:
   lee el plan y los detalles incrustados en `panel-data` (claves `plan` y `detalles`).
   Un dato ausente es `null` y se dice («sin datos»); nunca se pinta como 0. Sin arrastre, sin controles que
   escriban y sin HTML insertado: todo el texto entra por textContent.
   Accesibilidad del detalle (patrón del menú de `panel-core.js`): al abrir, el foco pasa al detalle y se anuncia en
   una región `aria-live`; Escape (o el botón «Cerrar detalle») lo cierra, devuelve el foco a la tarjeta que lo abrió
   y lo anuncia. El detalle va ANTES del tablero en el orden de lectura. */
(function (raiz) {
  'use strict';

  var C = function () { return raiz.PanelCartera; };
  var COLUMNAS = [['borrador', 'Borrador'], ['en-progreso', 'En progreso'], ['en-revision', 'En revisión'],
                  ['completado', 'Completado'], ['cancelado', 'Cancelado']];
  var ESTADOS_RESPUESTA = ['ok', 'partial', 'fuera_de_tope', 'ilegible', 'sin_ledger', 'sin_tareas', 'sin_lectura',
                           'unavailable'];
  var FUENTES = ['medido', 'estimado'];
  var GRADOS = ['Critical', 'Important', 'Minor', 'otro'];
  var MAX_TAREAS = 400;
  var MAX_CRITERIOS = 40;
  var MAX_GAPS = 20;
  var PLAZO_MS = 4000;
  var SONDEO_MS = 5000;
  var MAX_GRAFICO_TAREAS = 400;
  var pintado = null;
  var ctx = { id: null, servido: false, tareas: [], detalles: {}, abierto: null, boton: null, token: 0, controlador: null,
              nodos: {}, chart: true, ultimo: null, aviso: false, temporizador: null, enVuelo: false, ctrlPlan: null, graficos: null };

  function largo(texto) { return Array.from(texto).length; }
  function entero(v) { return typeof v === 'number' && isFinite(v) && Math.floor(v) === v && v >= 0; }
  function numero(v) { return v === null || (typeof v === 'number' && isFinite(v) && v >= 0); }
  function texto(v, tope) { return typeof v === 'string' && largo(v) <= tope; }
  function textoONulo(v, tope) { return v === null || texto(v, tope); }
  function objeto(v) { return v !== null && typeof v === 'object' && !Array.isArray(v); }
  function incluye(lista, v) { return lista.indexOf(v) !== -1; }
  function claves(v) { return Object.keys(v).sort().join(','); }
  function lista(texto) { return texto.split(',').sort().join(','); }
  function fechaISO(v) { return typeof v === 'string' && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$/.test(v) && isFinite(Date.parse(v)); }
  function issuesValidos(i) {
    return Array.isArray(i) && i.length <= 16 && i.every(function (x) {
      return objeto(x) && claves(x) === 'status' && typeof x.status === 'string' && /^[-a-z_]{1,48}$/.test(x.status);
    });
  }

  /* `avisos` es opcional (solo viaja si la proyección tiene alguno) y de vocabulario cerrado. */
  var AVISOS = ['rangos_sin_expandir'];
  function avisosValidos(d) {
    return d.avisos === undefined || (Array.isArray(d.avisos) && d.avisos.length >= 1 && d.avisos.length <= AVISOS.length
      && d.avisos.every(function (a) { return incluye(AVISOS, a); }));
  }
  function clavesSinAvisos(d) { return Object.keys(d).filter(function (k) { return k !== 'avisos'; }).sort().join(','); }
  function textoAvisos(d) {
    return d && Array.isArray(d.avisos) && incluye(d.avisos, 'rangos_sin_expandir')
      ? 'Aviso: hay rangos de tareas sin expandir; alguna revisión puede no aparecer.' : '';
  }

  var CLAVES_PLAN = 'complete,id,issues,observed_at,omitidas,slug,source,status,tareas,version,vocabulario';
  var CLAVES_FILA = 'cerrada,estado_tarea,fase_nombre,gaps,horas,id,literal,titulo';
  var CLAVES_ENVOLTURA = 'complete,id,issues,observed_at,omitidos,source,status,tarea,tarea_id,version';
  var CLAVES_TAREA = lista('id,titulo,fase_nombre,estado_tarea,literal,descripcion,criterios,verificacion,'
    + 'verificacion_recortada,ejecutada,salida,dependencias,archivado,cerrada,horas,revision,gaps');

  function fechaCierre(v) { return v === null || (typeof v === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(v) && isFinite(Date.parse(v))); }
  function estadoValido(v) { return v === null || COLUMNAS.some(function (c) { return c[0] === v; }); }
  function horasValidas(h) { return objeto(h) && claves(h) === 'est,fuente,real' && numero(h.real) && numero(h.est) && (h.fuente === null || incluye(FUENTES, h.fuente)); }
  function parValido(h) { return objeto(h) && claves(h) === 'est,real' && numero(h.real) && numero(h.est); }

  function validaFila(f, vistos) {
    if (!objeto(f) || claves(f) !== CLAVES_FILA || typeof f.id !== 'string' || !/^T-\d{1,4}$/.test(f.id) || vistos[f.id]) { return false; }
    vistos[f.id] = true;
    return texto(f.titulo, 160) && textoONulo(f.fase_nombre, 160) && textoONulo(f.literal, 48) && entero(f.gaps)
      && estadoValido(f.estado_tarea) && horasValidas(f.horas) && fechaCierre(f.cerrada);
  }

  /* Forma y topes de `api/plan-<id16>`. Un campo fuera de contrato invalida la respuesta entera. */
  function validar(d, id) {
    if (!objeto(d) || clavesSinAvisos(d) !== CLAVES_PLAN || !avisosValidos(d) || d.version !== 1 || d.source !== 'ledger_plan'
        || !incluye(ESTADOS_RESPUESTA, d.status) || typeof d.complete !== 'boolean' || d.id !== id) { return false; }
    if (!fechaISO(d.observed_at) || !textoONulo(d.slug, 80) || !entero(d.omitidas) || !issuesValidos(d.issues)) { return false; }
    if (!Array.isArray(d.vocabulario) || d.vocabulario.join(',') !== COLUMNAS.map(function (c) { return c[0]; }).join(',')) { return false; }
    if (d.tareas === null) { return d.status !== 'ok' && d.status !== 'partial'; }
    if (!Array.isArray(d.tareas) || d.tareas.length > MAX_TAREAS || (d.status !== 'ok' && d.status !== 'partial')) { return false; }
    var vistos = {};
    return d.tareas.every(function (f) { return validaFila(f, vistos); });
  }

  function validaGap(g) {
    return objeto(g) && claves(g) === 'correccion,gap,grado,intento,num' && entero(g.intento) && typeof g.num === 'string'
      && /^\d{1,4}$/.test(g.num) && incluye(GRADOS, g.grado) && texto(g.gap, 400) && texto(g.correccion, 400);
  }
  function validaCriterio(c) { return objeto(c) && claves(c) === 'criterio,marcado' && texto(c.criterio, 400) && typeof c.marcado === 'boolean'; }

  function validaTarea(t, tid) {
    if (!objeto(t) || claves(t) !== CLAVES_TAREA || t.id !== tid || !texto(t.titulo, 160) || !textoONulo(t.fase_nombre, 160)
        || !estadoValido(t.estado_tarea) || !textoONulo(t.literal, 48) || !textoONulo(t.descripcion, 1500)
        || !textoONulo(t.verificacion, 2000) || typeof t.verificacion_recortada !== 'boolean'
        || !textoONulo(t.ejecutada, 1000) || !textoONulo(t.salida, 1000)) { return false; }
    if (!Array.isArray(t.criterios) || t.criterios.length > MAX_CRITERIOS || !t.criterios.every(validaCriterio)) { return false; }
    if (!Array.isArray(t.gaps) || t.gaps.length > MAX_GAPS || !t.gaps.every(validaGap)) { return false; }
    if (!Array.isArray(t.dependencias) || t.dependencias.length > 40
        || !t.dependencias.every(function (x) { return typeof x === 'string' && /^T-\d{1,4}$/.test(x); })) { return false; }
    if (t.archivado !== null && !(objeto(t.archivado) && claves(t.archivado) === 'enlace' && t.archivado.enlace === 'execution-history.md')) { return false; }
    if (t.cerrada !== null && !(typeof t.cerrada === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(t.cerrada))) { return false; }
    var h = t.horas;
    if (!objeto(h) || claves(h) !== 'humano,ia,supervision' || !horasValidas(h.ia) || !parValido(h.supervision) || !parValido(h.humano)) { return false; }
    var r = t.revision;
    return r === null || (objeto(r) && claves(r) === 'abiertos,cabecera,intento' && entero(r.abiertos) && entero(r.intento) && textoONulo(r.cabecera, 160));
  }

  /* Forma y topes de `api/plan-<id16>-<T-XX>`. */
  function validarDetalle(d, id, tid) {
    if (!objeto(d) || clavesSinAvisos(d) !== CLAVES_ENVOLTURA || !avisosValidos(d) || d.version !== 1 || d.source !== 'ledger_tarea'
        || !incluye(ESTADOS_RESPUESTA, d.status) || typeof d.complete !== 'boolean' || d.id !== id || d.tarea_id !== tid) { return false; }
    if (!fechaISO(d.observed_at) || !issuesValidos(d.issues)) { return false; }
    var o = d.omitidos;
    if (!objeto(o) || claves(o) !== 'criterios,gaps' || !entero(o.criterios) || !entero(o.gaps)) { return false; }
    if (d.tarea === null) { return d.status !== 'ok' && d.status !== 'partial'; }
    return (d.status === 'ok' || d.status === 'partial') && validaTarea(d.tarea, tid);
  }

  function el(etiqueta, clase, contenido) {
    var nodo = raiz.document.createElement(etiqueta);
    if (clase) { nodo.className = clase; }
    if (contenido !== undefined) { nodo.textContent = contenido; }
    return nodo;
  }
  function porId(id) { return raiz.document.getElementById(id); }
  function pongo(id, contenido) {
    var nodo = porId(id);
    if (nodo) { nodo.textContent = contenido; }
    return nodo;
  }
  function hayTareas(d) { return d && (d.status === 'ok' || d.status === 'partial') && d.tareas !== null; }
  function plural(n, uno, varios) { return n + ' ' + (n === 1 ? uno : varios); }

  function textoEstado(d, motivo) {
    if (!d && motivo === 'sin_plan') { return 'Sin datos: esta copia estática no incluye este plan (se genera con --project).'; }
    if (!d && motivo === 'invalida') { return 'No se pudo leer el plan: la respuesta no tiene la forma esperada. Sin datos.'; }
    if (!d) { return 'No se pudo leer el plan. Sin datos de tareas; vuelve a intentarlo.'; }
    if (d.status === 'fuera_de_tope') { return 'Ledger fuera del tope de lectura (256 KiB): no se muestran tareas ni cifras.'; }
    if (d.status === 'ilegible') { return 'Ledger no legible (no es UTF-8 válido o no se pudo interpretar): no se muestran tareas ni cifras.'; }
    if (d.status === 'sin_ledger') { return 'Esta iniciativa no tiene ledger (tasks.md): sin tareas que mostrar.'; }
    if (d.status === 'sin_tareas') { return 'El ledger no contiene tareas reconocibles (### T-XX): sin tareas que mostrar.'; }
    if (d.status === 'sin_lectura') { return 'No se pudo leer el ledger. Sin datos de tareas; vuelve a intentarlo.'; }
    if (d.status === 'unavailable') { return 'Plan no disponible: no se pudo leer el ledger. Sin datos.'; }
    var base = 'Plan de «' + (d.slug || 'iniciativa') + '»: ' + plural(d.tareas.length, 'tarea', 'tareas') + '.'
      + (textoAvisos(d) ? ' ' + textoAvisos(d) : '');
    if (d.status === 'partial' || !d.complete) {
      return base + ' Lectura parcial: ' + plural(d.omitidas, 'tarea omitida', 'tareas omitidas')
        + ' por el presupuesto de la respuesta; lo omitido no acredita ausencia.';
    }
    return base;
  }

  function lineaHoras(rotulo, h, conFuente) {
    var real = C().horas(h.real) + (conFuente && h.real !== null && h.fuente ? ' (' + h.fuente + ')' : '');
    return rotulo + ': real ' + real + ' · estimado ' + C().horas(h.est);
  }

  /* --- detalle de tarea -------------------------------------------------------------------------------------- */

  function anunciar(mensaje) { pongo('plan-anuncio', mensaje); }

  function mensajeDetalle(d, tid) {
    if (!d) { return 'No se pudo leer el detalle de ' + tid + '. Sin datos; vuelve a intentarlo.'; }
    if (d.status === 'fuera_de_tope') { return 'Ledger fuera del tope de lectura (256 KiB): no se muestra el detalle de ' + tid + '.'; }
    if (d.status === 'ilegible') { return 'Ledger no legible: no se muestra el detalle de ' + tid + '.'; }
    if (d.status === 'unavailable') { return 'Detalle no disponible: no se pudo leer el ledger.'; }
    if (d.status === 'sin_ledger') { return 'Esta iniciativa no tiene ledger: sin detalle de ' + tid + '.'; }
    return 'No se pudo leer el ledger: sin detalle de ' + tid + '.';
  }

  function bloque(titulo) {
    var b = el('section', 'detalle-bloque');
    b.appendChild(el('h3', '', titulo));
    return b;
  }

  function pintarCriterios(cont, t) {
    var b = bloque('Criterios de aceptación');
    if (!t.criterios.length) { b.appendChild(el('p', '', 'Sin criterios declarados.')); }
    else {
      var ul = el('ul', 'criterios');
      t.criterios.forEach(function (c) { ul.appendChild(el('li', '', (c.marcado ? 'Hecho' : 'Pendiente') + ' · ' + c.criterio)); });
      b.appendChild(ul);
    }
    cont.appendChild(b);
  }

  function pintarVerificacion(cont, t) {
    var b = bloque('Verificación');
    if (t.verificacion === null) { b.appendChild(el('p', '', 'Sin verificación declarada.')); }
    else {
      b.appendChild(el('pre', '', t.verificacion));
      if (t.verificacion_recortada) { b.appendChild(el('p', 'filter-note', 'Verificación recortada a 2.000 caracteres: el ledger guarda el texto completo.')); }
    }
    if (t.ejecutada) { b.appendChild(el('p', '', 'Ejecutada: ' + t.ejecutada)); }
    if (t.salida) {
      b.appendChild(el('p', '', 'Salida registrada:'));
      b.appendChild(el('pre', '', t.salida));
    }
    cont.appendChild(b);
  }

  function pintarRevision(cont, t, d) {
    var b = bloque('Última revisión');
    if (textoAvisos(d)) { b.appendChild(el('p', 'ausencia', textoAvisos(d))); }
    if (t.revision === null) { b.appendChild(el('p', '', 'Sin revisión registrada para esta tarea.')); }
    else {
      b.appendChild(el('p', '', (t.revision.cabecera || ('Revisión de dos lentes — intento ' + t.revision.intento))));
      b.appendChild(el('p', '', plural(t.revision.abiertos, 'gap abierto', 'gaps abiertos') + '.'));
    }
    if (t.gaps.length) {
      var ul = el('ul', 'gaps');
      t.gaps.forEach(function (g) { ul.appendChild(el('li', '', g.grado + ' · ' + g.gap + ' · Corrección: ' + (g.correccion || 'sin datos'))); });
      b.appendChild(ul);
    }
    cont.appendChild(b);
  }

  function pintarDetalle(d, tid) {
    var cont = porId('plan-detalle-contenido');
    if (!cont) { return; }
    var nodos = [];
    if (!d || !d.tarea) { cont.replaceChildren(el('p', 'ausencia', mensajeDetalle(d, tid))); cont.setAttribute('aria-busy', 'false'); return; }
    var t = d.tarea;
    pongo('plan-detalle-titulo', t.id + ' · ' + t.titulo);
    var datos = bloque('Datos');
    datos.appendChild(el('p', '', 'Estado: ' + (t.estado_tarea || (t.literal ? '«' + t.literal + '»' : 'sin estado'))));
    datos.appendChild(el('p', '', 'Fase: ' + (t.fase_nombre || 'sin datos')));
    datos.appendChild(el('p', '', 'Cerrada: ' + (t.cerrada || 'sin datos')));
    datos.appendChild(el('p', '', 'Dependencias: ' + (t.dependencias.length ? t.dependencias.join(', ') : 'ninguna')));
    datos.appendChild(el('p', '', lineaHoras('IA', t.horas.ia, true)));
    datos.appendChild(el('p', '', lineaHoras('Supervisión', t.horas.supervision, false)));
    datos.appendChild(el('p', '', lineaHoras('Humano', t.horas.humano, false)));
    nodos.push(datos);
    var desc = bloque('Descripción');
    desc.appendChild(el('p', '', t.descripcion || 'Sin descripción declarada.'));
    nodos.push(desc);
    var contenedor = el('div', 'detalle-cuerpo');
    pintarCriterios(contenedor, t);
    pintarVerificacion(contenedor, t);
    pintarRevision(contenedor, t, d);
    Array.prototype.push.apply(nodos, contenedor.children);
    if (t.archivado) {
      var a = bloque('Historia archivada');
      a.appendChild(el('p', '', 'Archivado: la historia de esta tarea está en ' + t.archivado.enlace
        + ', junto al ledger; el panel no la mezcla con el ledger.'));
      nodos.push(a);
    }
    if (d.omitidos.criterios || d.omitidos.gaps) {
      var partes = [];
      if (d.omitidos.criterios) { partes.push(plural(d.omitidos.criterios, 'criterio omitido', 'criterios omitidos')); }
      if (d.omitidos.gaps) { partes.push(plural(d.omitidos.gaps, 'gap omitido', 'gaps omitidos')); }
      nodos.push(el('p', 'ausencia', 'Respuesta recortada: ' + partes.join(' y ') + ' por el presupuesto de la respuesta; lo omitido no acredita ausencia.'));
    }
    cont.replaceChildren.apply(cont, nodos);
    cont.setAttribute('aria-busy', 'false');
  }

  function cancelar() {
    ctx.token += 1;
    if (ctx.controlador) { ctx.controlador.abort(); ctx.controlador = null; }
  }

  function pedirDetalle(tid, token) {
    var controlador = new raiz.AbortController();
    ctx.controlador = controlador;
    var plazo = raiz.setTimeout(function () { controlador.abort(); }, PLAZO_MS);
    raiz.fetch('api/plan-' + ctx.id + '-' + tid, { credentials: 'omit', cache: 'no-store', signal: controlador.signal })
      .then(function (r) { if (!r.ok) { throw new Error('no disponible'); } return r.json(); })
      .then(function (d) { if (token === ctx.token && ctx.controlador === controlador) { pintarDetalle(validarDetalle(d, ctx.id, tid) ? d : null, tid); } })
      .catch(function () { if (token === ctx.token && ctx.controlador === controlador) { pintarDetalle(null, tid); } })
      .then(function () { raiz.clearTimeout(plazo); });
  }

  function abrir(tid, boton) {
    var panel = porId('plan-detalle');
    if (!panel) { return; }
    cancelar();
    var token = ctx.token;
    var fila = ctx.tareas.filter(function (t) { return t.id === tid; })[0];
    ctx.abierto = tid;
    ctx.boton = boton;
    pongo('plan-detalle-titulo', tid + (fila ? ' · ' + fila.titulo : ''));
    panel.hidden = false;
    if (ctx.servido) {
      var cont = porId('plan-detalle-contenido');
      if (cont) { cont.setAttribute('aria-busy', 'true'); cont.replaceChildren(el('p', 'filter-note', 'Cargando el detalle de ' + tid + '…')); }
      pedirDetalle(tid, token);
    } else {
      var d = ctx.detalles[tid];
      if (d === undefined) { pintarDetalle({ tarea: null, status: 'sin_lectura' }, tid); }
      else { pintarDetalle(validarDetalle(d, ctx.id, tid) ? d : null, tid); }
    }
    panel.focus();
    anunciar('Detalle de ' + tid + ' abierto');
  }

  function cerrar() {
    var panel = porId('plan-detalle');
    if (!panel || panel.hidden) { return false; }
    var tid = ctx.abierto, boton = ctx.boton;
    cancelar();
    panel.hidden = true;
    ctx.abierto = null;
    if (boton && typeof boton.focus === 'function') { boton.focus(); }
    anunciar('Detalle de ' + tid + ' cerrado');
    return true;
  }

  function alTeclado(evento) {
    if (evento.key === 'Escape') {
      /* Escape dentro de un campo de formulario (p. ej. un comentario de revisión) es del campo: no cierra el detalle. */
      var objetivo = evento.target && typeof evento.target.tagName === 'string' ? evento.target.tagName.toLowerCase() : '';
      if (objetivo === 'textarea' || objetivo === 'input' || objetivo === 'select') { return; }
      var panel = porId('plan-detalle');
      if (panel && !panel.hidden) { evento.preventDefault(); cerrar(); }
    }
  }

  /* --- kanban ------------------------------------------------------------------------------------------------ */

  function tarjeta(t) {
    var art = el('article', 'card');
    art.dataset.id = t.id;
    var titulo = el('h3');
    var abre = el('button', 'abrir-tarea', t.id + ' · ' + t.titulo);
    abre.setAttribute('type', 'button');
    abre.dataset.tarea = t.id;
    abre.addEventListener('click', function () { abrir(t.id, abre); });
    titulo.appendChild(abre);
    art.appendChild(titulo);
    if (t.estado_tarea === null) { art.appendChild(el('p', '', 'Estado: ' + (t.literal ? '«' + t.literal + '»' : 'sin estado'))); }
    art.appendChild(el('p', '', 'Fase: ' + (t.fase_nombre || 'sin datos')));
    art.appendChild(el('p', '', lineaHoras('Horas IA', t.horas, true)));
    art.appendChild(el('p', '', 'Gaps de revisión abiertos: ' + t.gaps));
    return { clave: JSON.stringify(t), art: art, boton: abre };
  }

  /* Una tarjeta cuya fila no cambió conserva su nodo entre refrescos (conservación de DOM, como panel-live.js). */
  function nodoDe(t) {
    var previo = ctx.nodos[t.id];
    return previo && previo.clave === JSON.stringify(t) ? previo : tarjeta(t);
  }

  function columna(titulo, filas, clase, nuevos) {
    var seccion = el('section', 'columna' + (clase ? ' ' + clase : ''));
    seccion.appendChild(el('h2', '', titulo + ' (' + filas.length + ')'));
    if (!filas.length) { seccion.appendChild(el('p', 'columna-vacia', 'Ninguna tarea.')); }
    filas.forEach(function (t) { var n = nodoDe(t); nuevos[t.id] = n; seccion.appendChild(n.art); });
    return seccion;
  }

  function tareaConFoco() {
    var activo = raiz.document.activeElement;
    var id = activo && activo.dataset ? activo.dataset.tarea : null;
    return id && ctx.nodos[id] && ctx.nodos[id].boton === activo ? id : null;
  }

  function dibujarKanban(d) {
    var tablero = porId('kanban-plan');
    if (!tablero) { return; }
    var clave = hayTareas(d) ? JSON.stringify(d.tareas) : 'sin-datos';
    if (clave === pintado) { return; }
    pintado = clave;
    ctx.tareas = hayTareas(d) ? d.tareas : [];
    if (!hayTareas(d)) {
      ctx.nodos = {};
      tablero.replaceChildren(el('p', 'ausencia', 'Sin datos: no hay tareas que mostrar.'));
      return;
    }
    var foco = tareaConFoco();
    var nuevos = {};
    var columnas = COLUMNAS.map(function (c) {
      return columna(c[1], d.tareas.filter(function (t) { return t.estado_tarea === c[0]; }), '', nuevos);
    });
    var raras = d.tareas.filter(function (t) { return t.estado_tarea === null; });
    if (raras.length) { columnas.push(columna('Estado no reconocido', raras, 'desconocidos', nuevos)); }
    ctx.nodos = nuevos;
    tablero.replaceChildren.apply(tablero, columnas);
    if (ctx.abierto && nuevos[ctx.abierto]) { ctx.boton = nuevos[ctx.abierto].boton; }
    if (foco && nuevos[foco]) { nuevos[foco].boton.focus(); }
  }

  /* --- gráficos (T-25, T-26): derivan de las filas del plan con el adaptador panel-charts.js ------------------- */

  function suma(valores) {
    var presentes = valores.filter(function (v) { return v !== null; });
    if (!presentes.length) { return null; }
    return Math.round(presentes.reduce(function (a, b) { return a + b; }, 0) * 100) / 100;
  }
  function sufijoFuente(fuentes) {
    var f = FUENTES.filter(function (x) { return fuentes.indexOf(x) !== -1; });
    return f.length ? ' (' + f.join(' y ') + ')' : '';
  }

  function fases(tareas) {
    var orden = [], por = {};
    tareas.forEach(function (t) {
      var n = t.fase_nombre || 'Sin fase';
      if (!por[n]) { por[n] = []; orden.push(n); }
      por[n].push(t);
    });
    return orden.map(function (n) { return { nombre: n, tareas: por[n] }; });
  }

  function especificaciones(tareas) {
    var fs = fases(tareas);
    var avance = { id: 'grafico-avance-fase-spec', titulo: 'Avance por fase', tipo: 'bar', categoria: 'Fase',
      descripcion: 'Tareas completadas y tareas totales de cada fase, como en el resumen de progreso del ledger.',
      origen: 'ledger (api/plan)', etiquetas: fs.map(function (f) { return f.nombre; }),
      series: [{ nombre: 'Completadas', valores: fs.map(function (f) { return f.tareas.filter(function (t) { return t.estado_tarea === 'completado'; }).length; }) },
               { nombre: 'Total', valores: fs.map(function (f) { return f.tareas.length; }) }] };
    var horasFase = { id: 'grafico-horas-fase-spec', titulo: 'Horas IA reales frente a estimadas, por fase', tipo: 'bar',
      categoria: 'Fase', unidad: 'h', origen: 'ledger (api/plan); real solo con medición o estimación declarada',
      descripcion: 'Suma de las horas IA reales y estimadas de cada fase; sin dato se dice «sin datos», nunca 0.',
      etiquetas: [], series: [{ nombre: 'IA real', valores: [] }, { nombre: 'IA estimada', valores: [] }], sinDatos: [] };
    fs.forEach(function (f) {
      var real = suma(f.tareas.map(function (t) { return t.horas.real; }));
      var est = suma(f.tareas.map(function (t) { return t.horas.est; }));
      var fuentes = f.tareas.filter(function (t) { return t.horas.real !== null; }).map(function (t) { return t.horas.fuente; });
      if (real === null && est === null) { horasFase.sinDatos.push(f.nombre); return; }
      horasFase.etiquetas.push(f.nombre + sufijoFuente(fuentes));
      horasFase.series[0].valores.push(real);
      horasFase.series[1].valores.push(est);
    });
    var horasTarea = { id: 'grafico-horas-tarea-spec', titulo: 'Horas IA reales frente a estimadas, por tarea', tipo: 'bar',
      categoria: 'Tarea', unidad: 'h', origen: 'ledger (api/plan); «(medido)» o «(estimado)» según la procedencia del real',
      descripcion: 'Horas IA reales y estimadas de cada tarea; la procedencia del real va entre paréntesis.',
      etiquetas: [], series: [{ nombre: 'IA real', valores: [] }, { nombre: 'IA estimada', valores: [] }], sinDatos: [] };
    tareas.slice(0, MAX_GRAFICO_TAREAS).forEach(function (t) {
      if (t.horas.real === null && t.horas.est === null) { horasTarea.sinDatos.push(t.id); return; }
      horasTarea.etiquetas.push(t.id + (t.horas.real !== null && t.horas.fuente ? ' (' + t.horas.fuente + ')' : ''));
      horasTarea.series[0].valores.push(t.horas.real);
      horasTarea.series[1].valores.push(t.horas.est);
    });
    return { avance: avance, horasFase: horasFase, horasTarea: horasTarea, burndown: burndown(tareas) };
  }

  /* Burndown (design.md §2.4 I-02): solo si TODAS las tareas completadas llevan Cerrada; si no, el mensaje y nada más.
     Los puntos son únicamente las fechas de cierre reales: no se interpola ningún día intermedio. */
  function burndown(tareas) {
    var hechas = tareas.filter(function (t) { return t.estado_tarea === 'completado'; });
    if (!hechas.length) { return { mensaje: 'Sin datos: ninguna tarea completada todavía; el burndown necesita fechas de cierre.' }; }
    var sin = hechas.filter(function (t) { return t.cerrada === null; }).length;
    if (sin) { return { mensaje: 'burndown no disponible: ' + sin + ' de ' + hechas.length + ' tareas completadas sin fecha de cierre' }; }
    var base = tareas.filter(function (t) { return t.estado_tarea !== 'cancelado'; }).length;
    var fechas = [];
    hechas.forEach(function (t) { if (fechas.indexOf(t.cerrada) === -1) { fechas.push(t.cerrada); } });
    fechas.sort();
    return { spec: { id: 'grafico-burndown-spec', titulo: 'Burndown: tareas pendientes por fecha de cierre', tipo: 'line',
      categoria: 'Fecha de cierre', unidad: 'tareas', origen: 'campo Cerrada del ledger',
      descripcion: 'Tareas pendientes (sin cancelar) tras cada fecha en la que se cerró alguna; no hay puntos interpolados.',
      etiquetas: fechas, series: [{ nombre: 'Tareas pendientes', valores: fechas.map(function (f) {
        return base - hechas.filter(function (t) { return t.cerrada <= f; }).length; }) }] } };
  }

  function vaciar(id) { var n = porId(id); if (n) { n.replaceChildren(); } return n; }

  function dibujarGraficos(tareas) {
    if (!porId('grafico-avance-fase') || !raiz.PanelCharts) { return; }
    var esp = tareas ? especificaciones(tareas) : null;
    var clave = JSON.stringify([esp, ctx.chart]);
    if (clave === ctx.graficos) { return; }
    ctx.graficos = clave;
    ['grafico-avance-fase', 'grafico-horas-fase', 'grafico-horas-tarea', 'grafico-burndown'].forEach(vaciar);
    if (!esp) {
      porId('grafico-avance-fase').appendChild(el('p', 'ausencia', 'Sin datos: no hay tareas con las que dibujar los gráficos.'));
      return;
    }
    var opciones = { chartDisponible: ctx.chart };
    raiz.PanelCharts.dibujar(porId('grafico-avance-fase'), esp.avance, opciones);
    raiz.PanelCharts.dibujar(porId('grafico-horas-fase'), esp.horasFase, opciones);
    raiz.PanelCharts.dibujar(porId('grafico-horas-tarea'), esp.horasTarea, opciones);
    var b = porId('grafico-burndown');
    if (esp.burndown.spec) { raiz.PanelCharts.dibujar(b, esp.burndown.spec, opciones); }
    else {
      var m = el('p', 'ausencia', esp.burndown.mensaje);
      m.setAttribute('role', 'status');
      b.appendChild(m);
    }
  }

  /* --- estado, sondeo y arranque ----------------------------------------------------------------------------- */

  function dibujar(d, motivo) {
    ctx.aviso = false;
    pongo('plan-estado', textoEstado(d, motivo));
    pongo('plan-frescura', d ? 'Lectura obtenida: ' + d.observed_at + '.' : '');
    if (d && d.slug) { pongo('plan-titulo', 'Tareas del plan «' + d.slug + '»'); }
    dibujarKanban(hayTareas(d) ? d : null);
    dibujarGraficos(hayTareas(d) ? d.tareas : null);
  }

  function parar() {
    if (ctx.temporizador !== null) { raiz.clearTimeout(ctx.temporizador); ctx.temporizador = null; }
  }
  function programar() {
    parar();
    if (!ctx.servido || raiz.document.hidden) { return; }
    ctx.temporizador = raiz.setTimeout(refrescar, SONDEO_MS);
  }

  function filaDe(id) { return ctx.nodos[id] ? ctx.nodos[id].clave : null; }

  function aplicar(d) {
    var tid = ctx.abierto;
    var antes = tid ? filaDe(tid) : null;
    dibujar(d);
    ctx.ultimo = d;
    /* Si la tarea abierta cambió de fila, su detalle se vuelve a pedir en silencio: sin cerrar ni mover el foco. */
    if (tid && ctx.abierto === tid && ctx.nodos[tid] && ctx.nodos[tid].clave !== antes) {
      if (ctx.controlador) { ctx.controlador.abort(); }
      pedirDetalle(tid, ctx.token);
    }
  }

  function refrescar() {
    parar();
    if (raiz.document.hidden || ctx.enVuelo) { return; }
    ctx.enVuelo = true;
    var controlador = new raiz.AbortController();
    ctx.ctrlPlan = controlador;
    var plazo = raiz.setTimeout(function () { controlador.abort(); }, PLAZO_MS);
    raiz.fetch('api/plan-' + ctx.id, { credentials: 'omit', cache: 'no-store', signal: controlador.signal })
      .then(function (r) { if (!r.ok) { throw new Error('no disponible'); } return r.json(); })
      .then(function (d) {
        ctx.invalida = !validar(d, ctx.id);
        if (ctx.invalida) { throw new Error('invalida'); }
        aplicar(d);
      })
      .catch(function () {
        if (controlador.signal.aborted && raiz.document.hidden) { return; }
        if (ctx.ultimo) {
          ctx.aviso = true;
          pongo('plan-estado', 'No se pudo actualizar. Se conserva la última vista y su fecha anterior; no se acredita su vigencia.');
        } else { dibujar(null, ctx.invalida ? 'invalida' : 'no_disponible'); }
      })
      .then(function () {
        raiz.clearTimeout(plazo);
        ctx.ctrlPlan = null;
        ctx.enVuelo = false;
        programar();
      });
  }

  function alVisibilidad() {
    if (raiz.document.hidden) {
      parar();
      if (ctx.ctrlPlan) { ctx.ctrlPlan.abort(); }
    } else { refrescar(); }
  }

  function leerDatos() {
    var nodo = porId('panel-data');
    try { return JSON.parse(nodo.textContent); } catch (e) { return {}; }
  }

  function iniciar() {
    var datos = leerDatos();
    var id = datos.plan_id;
    if (typeof id !== 'string' || !/^[a-f0-9]{16}$/.test(id)) { dibujar(null, 'invalida'); return; }
    ctx.id = id;
    ctx.servido = datos.modo === 'servido';
    ctx.chart = datos.chartjs_disponible !== false;
    ctx.detalles = objeto(datos.detalles) ? datos.detalles : {};
    raiz.document.addEventListener('keydown', alTeclado);
    var cierre = porId('plan-detalle-cerrar');
    if (cierre) { cierre.addEventListener('click', cerrar); }
    if (!ctx.servido) {
      if (datos.plan === undefined) { dibujar(null, 'sin_plan'); }
      else if (validar(datos.plan, id)) { dibujar(datos.plan); }
      else { dibujar(null, 'invalida'); }
      return;
    }
    var boton = porId('plan-refrescar');
    if (boton) { boton.hidden = false; boton.addEventListener('click', refrescar); }
    raiz.document.addEventListener('visibilitychange', alVisibilidad);
    refrescar();
  }

  raiz.PanelPlan = { iniciar: iniciar, dibujar: dibujar, validar: validar, validarDetalle: validarDetalle, COLUMNAS: COLUMNAS };
  if (typeof module === 'object' && module.exports) { module.exports = raiz.PanelPlan; }
  if (raiz.document && raiz.document.getElementById && raiz.document.getElementById('kanban-plan')) { iniciar(); }
})(typeof window !== 'undefined' ? window : globalThis);
