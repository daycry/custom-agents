/* Página Memoria: entradas por tipo y estado (gráfico + tabla, filtro de área), bandeja del curador (solo lectura), línea
   de tiempo con sucesión y «vigente», relaciones de UNA entrada (SVG + lista), backends y sesiones del journal.
   Servido: `api/memoria` (GET) y, para las relaciones, la operación `related` de `api/memory` (POST, existente).
   Exportado: lee el JSON incrustado en `panel-data` (clave `memoria`, con las relaciones de cada entrada).
   Lo que una fuente no trae se dice («sin datos»), nunca se pinta como 0. Sin HTML insertado: solo textContent. */
(function (raiz) {
  'use strict';

  var TIPOS = [['adr', 'ADR'], ['gotcha', 'Gotcha'], ['leccion', 'Lección']];
  var ESTADOS = ['aceptada', 'propuesta', 'obsoleta'];
  var GRUPOS = [['sucesion', 'Sucesión'], ['iniciativa', 'Misma iniciativa'], ['area', 'Misma área'], ['enlaces', 'Enlace declarado']];
  /* Clave de cada grupo en las relaciones incrustadas (`area` es clave de texto mostrado del saneador y no lleva ids). */
  var CLAVE_EMBEBIDA = { sucesion: 'sucesion', iniciativa: 'por_iniciativa', area: 'por_area', enlaces: 'enlaces' };
  var SIN_AREA = '\u0001sin-area';
  var ESTADOS_RESPUESTA = ['ok', 'partial', 'not_found', 'unavailable'];
  var SITUACIONES_BANDEJA = ['ok', 'incompleto', 'ausente', 'no_disponible'];
  var SITUACIONES_BACKEND = ['configurado', 'deshabilitado', 'no_configurado'];
  var ESTADOS_JOURNAL = ['ok', 'empty', 'not_found', 'incomplete', 'unavailable'];
  var BANDEJA = [['pending', 'Pendientes'], ['needs_changes', 'Cambios pedidos'], ['rejected', 'Rechazados']];
  var ETIQUETA_BACKEND = { kwipu: 'Kwipu', graphiti: 'Graphiti' };
  var PLAZO_MS = 8000;
  var REINTENTO_MS = 3000;   // el servidor aun calcula la memoria (`calculando`): reintenta pronto, no a mano
  var CONTROLES = /[\u0000-\u001f\u007f-\u009f\u2028\u2029\u202a-\u202e\u2066-\u2069]/;

  /* ---- validación: un campo fuera de contrato invalida la respuesta entera ------------------------------------ */
  function largo(t) { return Array.from(t).length; }
  function entero(v) { return typeof v === 'number' && isFinite(v) && Math.floor(v) === v && v >= 0; }
  function texto(v, tope) { return typeof v === 'string' && largo(v) <= tope; }
  function textoONulo(v, tope) { return v === null || texto(v, tope); }
  function identidad(v) { return texto(v, 256) && v.length > 0 && !CONTROLES.test(v); }
  function objeto(v) { return v !== null && typeof v === 'object' && !Array.isArray(v); }
  function incluye(l, v) { return l.indexOf(v) !== -1; }
  function enteroONulo(v) { return v === null || entero(v); }
  function iso(v) { return typeof v === 'string' && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$/.test(v) && isFinite(Date.parse(v)); }
  function ids(v, max) { return Array.isArray(v) && v.length <= max && v.every(identidad); }
  function lista(v, tope, max) { return Array.isArray(v) && v.length <= max && v.every(function (t) { return texto(t, tope); }); }

  function validaEntrada(e) {
    return objeto(e) && identidad(e.id) && texto(e.tipo, 160) && texto(e.estado, 160) && texto(e.area, 160)
      && texto(e.titular, 160) && (e.fecha === null || /^\d{4}-\d{2}-\d{2}$/.test(e.fecha)) && texto(e.iniciativa, 80)
      && incluye(['proyecto', 'approved'], e.origen) && typeof e.vigente === 'boolean'
      && ids(e.sustituida_por, 16) && ids(e.sustituye_a, 16);
  }
  function validaRelacionesDe(r) {
    return objeto(r) && Array.isArray(r.sucesion) && r.sucesion.length <= 20 && r.sucesion.every(function (s) {
      return objeto(s) && texto(s.relacion, 160) && identidad(s.id) && typeof s.ausente === 'boolean';
    }) && ids(r.por_iniciativa, 20) && ids(r.por_area, 20) && ids(r.enlaces, 20) && typeof r.recortado === 'boolean'
      && (r.total === undefined || entero(r.total));
  }
  function validaBandeja(b) {
    if (!objeto(b) || !objeto(b.estados) || !objeto(b.aprobadas)) { return false; }
    var bien = BANDEJA.every(function (par) {
      var e = b.estados[par[0]];
      return objeto(e) && incluye(SITUACIONES_BANDEJA, e.situacion) && enteroONulo(e.n) && Array.isArray(e.items) && e.items.length <= 20
        && e.items.every(function (i) { return objeto(i) && texto(i.candidato, 160) && textoONulo(i.titular, 160) && textoONulo(i.category, 40); });
    });
    var a = b.aprobadas;
    return bien && enteroONulo(a.n) && Array.isArray(a.items) && a.items.length <= 20
      && a.items.every(function (i) { return objeto(i) && identidad(i.id) && texto(i.titular, 160) && texto(i.area, 160); });
  }
  /* Mismo criterio que el guardrail de nemesis (`lib-guardrail.sh`): loopback o red privada. Compara redes, no prefijos de texto. */
  function hostLocal(v) {
    var m = /^https?:\/\/(\[[0-9a-f:.]+\]|[^\/:?#]+)/i.exec(v);
    if (!m) { return false; }
    var h = m[1].toLowerCase().replace(/^\[|\]$/g, '').replace(/\.$/, '');
    if (h === 'localhost' || h === 'host.docker.internal' || /\.(test|local|localhost|internal)$/.test(h)) { return true; }
    if (h === '::1' || /^f[cd][0-9a-f]{2}:/.test(h) || /^fe[89ab][0-9a-f]:/.test(h)) { return true; }
    var o = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/.exec(h);
    if (!o) { return false; }
    var a = +o[1], b = +o[2];
    if (+o[3] > 255 || +o[4] > 255 || a > 255 || b > 255) { return false; }
    return a === 127 || a === 10 || (a === 172 && b >= 16 && b <= 31) || (a === 192 && b === 168) || (a === 169 && b === 254);
  }
  function urlUi(v) { return typeof v === 'string' && /^https?:\/\/[^\s?#@\\]{1,190}$/.test(v); }
  function validaBackend(b) {
    return objeto(b) && typeof b.backend === 'string' && /^[a-z][a-z0-9_-]{0,31}$/.test(b.backend) && texto(b.tipo, 40)
      && incluye(SITUACIONES_BACKEND, b.situacion) && enteroONulo(b.entradas) && (b.ultima === null || iso(b.ultima))
      && typeof b.interrumpida === 'boolean' && (b.ultima === null || /Z$/.test(b.ultima)) && (b.ui_url === null || urlUi(b.ui_url))
      && (b.ultima_parcial === undefined || typeof b.ultima_parcial === 'boolean')
      && (b.ui_url_no_local === undefined || typeof b.ui_url_no_local === 'boolean');
  }
  function validaSesion(s) {
    return objeto(s) && (s.fecha === null || /^\d{4}-\d{2}-\d{2}$/.test(s.fecha)) && texto(s.iniciativa, 80) && texto(s.resumen, 240)
      && textoONulo(s.objetivo, 240) && textoONulo(s.punto_actual, 240)
      && ['siguientes_pasos', 'bloqueos', 'descartados', 'decisiones', 'pendientes'].every(function (k) { return lista(s[k], 240, 3); });
  }
  function validar(d) {
    if (!objeto(d) || d.version !== 1 || d.source !== 'memoria_panel' || !incluye(ESTADOS_RESPUESTA, d.status)
        || typeof d.complete !== 'boolean' || !iso(d.observed_at)) { return false; }
    if (!Array.isArray(d.issues) || d.issues.length > 16 || !d.issues.every(function (i) {
      return objeto(i) && typeof i.status === 'string' && /^[-a-z_]{1,48}$/.test(i.status);
    })) { return false; }
    if (!entero(d.total) || !entero(d.recortado) || !objeto(d.conteos) || !Array.isArray(d.entradas) || d.entradas.length > 400) { return false; }
    var porId = {};
    if (!d.entradas.every(function (e) {
      if (!validaEntrada(e) || porId[e.id]) { return false; }
      porId[e.id] = true;
      return true;
    })) { return false; }
    var conteosBien = Object.keys(d.conteos).every(function (t) {
      return texto(t, 160) && objeto(d.conteos[t]) && Object.keys(d.conteos[t]).every(function (e) { return texto(e, 160) && entero(d.conteos[t][e]); });
    });
    if (!conteosBien || !validaBandeja(d.bandeja) || !Array.isArray(d.backends) || d.backends.length > 10
        || !d.backends.every(validaBackend)) { return false; }
    var j = d.journal;
    if (!objeto(j) || !incluye(ESTADOS_JOURNAL, j.status) || !Array.isArray(j.sesiones) || j.sesiones.length > 2
        || !j.sesiones.every(validaSesion)) { return false; }
    if (d.relaciones !== undefined) {
      if (!objeto(d.relaciones)) { return false; }
      return Object.keys(d.relaciones).length <= 400 && Object.keys(d.relaciones).every(function (k) { return identidad(k) && validaRelacionesDe(d.relaciones[k]); });
    }
    return true;
  }

  /* `api/memory` (operación `related`, ya existente): misma validación estricta que `panel-memory.js` aplica a lo que muestra. */
  function compacta(e) {
    return objeto(e) && identidad(e.id) && texto(e.titular, 160) && texto(e.area, 160) && texto(e.estado, 160) && texto(e.tipo, 160);
  }
  function validaRelated(d, id) {
    if (!objeto(d) || d.version !== 1 || d.source !== 'canonical_knowledge' || d.operation !== 'related'
        || !incluye(['ok', 'partial'], d.status) || typeof d.complete !== 'boolean' || !iso(d.observed_at)
        || d.selected !== null || !objeto(d.related) || !Array.isArray(d.entries) || d.entries.length) { return false; }
    var n = 0;
    var bien = GRUPOS.every(function (par) {
      var filas = d.related[par[0]];
      if (!Array.isArray(filas)) { return false; }
      n += filas.length;
      return filas.every(function (f) {
        if (par[0] === 'sucesion') { return objeto(f) && texto(f.relation, 160) && identidad(f.id) && (f.entry === null || compacta(f.entry)); }
        return compacta(f);
      });
    });
    return bien && n <= 20 && identidad(id);
  }

  /* ---- DOM ---------------------------------------------------------------------------------------------------- */
  function el(etiqueta, clase, t) {
    var nodo = raiz.document.createElement(etiqueta);
    if (clase) { nodo.className = clase; }
    if (t !== undefined) { nodo.textContent = t; }
    return nodo;
  }
  function porId(id) { return raiz.document.getElementById(id); }
  function vaciar(id) { var n = porId(id); if (n) { n.replaceChildren(); } return n; }
  function pongo(id, t) { var n = porId(id); if (n) { n.textContent = t; } return n; }
  function dato(v) { return v === null || v === undefined || v === '' ? 'sin datos' : String(v); }

  var estado = { d: null, modo: 'exportado', area: '', chart: true, relacionado: null, enVuelo: false, ocupado: false };

  function etiquetaTipo(t) {
    var par = TIPOS.filter(function (p) { return p[0] === t; })[0];
    return par ? par[1] : t;
  }
  function tiposOrdenados(claves) {
    var fijos = TIPOS.map(function (p) { return p[0]; }).filter(function (t) { return claves.indexOf(t) !== -1; });
    return fijos.concat(claves.filter(function (t) { return fijos.indexOf(t) === -1; }).sort());
  }

  function estadoGeneral(d, motivo) {
    if (!d && motivo === 'sin_memoria') { return 'Sin datos: esta copia estática no incluye la memoria (se genera con --project).'; }
    if (!d && motivo === 'calculando') { return 'Calculando la memoria… (reintento en ' + (REINTENTO_MS / 1000) + ' s).'; }
    if (!d) { return 'No se pudo leer la memoria. Sin datos; vuelve a intentarlo.'; }
    if (d.status === 'unavailable') { return 'Memoria no disponible: no se pudo leer docs/knowledge. Sin datos.'; }
    if (d.status === 'not_found') { return 'No se encontraron entradas en docs/knowledge. Lectura obtenida: ' + d.observed_at + '.'; }
    var fecha = ' Lectura obtenida: ' + d.observed_at + '.';
    if (d.status === 'partial' || !d.complete) {
      var recorte = d.recortado ? ' Se muestran ' + d.entradas.length + ' de ' + d.total + ' entradas (la respuesta se recortó a 64 KiB); los conteos son los del corpus leído.' : '';
      return 'Lectura parcial: lo omitido no acredita ausencia ni un total completo.' + recorte + fecha;
    }
    return 'Memoria derivada de docs/knowledge.' + fecha;
  }

  /* ---- resumen: gráfico y tabla ------------------------------------------------------------------------------- */
  function conteosFiltrados(d, area) {
    if (area === '') { return d.conteos; }
    var salida = {};
    d.entradas.forEach(function (e) {
      if ((area === SIN_AREA ? e.area !== '' : e.area !== area)) { return; }
      salida[e.tipo] = salida[e.tipo] || {};
      salida[e.tipo][e.estado] = (salida[e.tipo][e.estado] || 0) + 1;
    });
    return salida;
  }

  function dibujarGrafico(d) {
    var contenedor = vaciar('grafico-memoria');
    if (!contenedor || !raiz.PanelCharts) { return; }
    var c = conteosFiltrados(d, estado.area);
    var tipos = tiposOrdenados(Object.keys(c));
    if (!tipos.length) { contenedor.appendChild(el('p', 'ausencia', 'Sin entradas para este filtro.')); return; }
    var extras = [];
    tipos.forEach(function (t) { Object.keys(c[t]).forEach(function (e) { if (ESTADOS.indexOf(e) === -1 && extras.indexOf(e) === -1) { extras.push(e); } }); });
    var estados = ESTADOS.concat(extras.sort());
    raiz.PanelCharts.dibujar(contenedor, {
      id: 'grafico-memoria-spec', titulo: 'Entradas de memoria por tipo y estado',
      descripcion: 'Número de entradas por tipo (ADR, gotcha, lección) y estado.' + (estado.area === '' ? '' : ' Filtrado por área.'),
      tipo: 'bar', categoria: 'Tipo', origen: 'api/memoria (corpus de knowledge-view.snapshot)',
      etiquetas: tipos.map(etiquetaTipo),
      series: estados.map(function (e) { return { nombre: e, valores: tipos.map(function (t) { return c[t][e] || 0; }) }; })
    }, { chartDisponible: estado.chart });
  }

  function opcionesArea(d) {
    var sel = porId('memoria-area');
    if (!sel) { return; }
    var cuentas = {};
    d.entradas.forEach(function (e) { var k = e.area === '' ? SIN_AREA : e.area; cuentas[k] = (cuentas[k] || 0) + 1; });
    var claves = Object.keys(cuentas).sort(function (a, b) { return a === SIN_AREA ? 1 : b === SIN_AREA ? -1 : a < b ? -1 : a > b ? 1 : 0; });
    if (claves.indexOf(estado.area) === -1) { estado.area = ''; }
    var todas = el('option', '', 'Todas las áreas');
    todas.value = '';
    var opciones = [todas].concat(claves.map(function (k) {
      var o = el('option', '', (k === SIN_AREA ? 'Sin área' : k) + ' (' + cuentas[k] + ')');
      o.value = k;
      return o;
    }));
    sel.replaceChildren.apply(sel, opciones);
    sel.value = estado.area;
  }

  function botonRelaciones(id) {
    var b = el('button', '', 'Ver relaciones');
    b.type = 'button';
    b.setAttribute('aria-label', 'Ver relaciones de ' + id);
    b.addEventListener('click', function () { verRelaciones(id); });
    return b;
  }

  function dibujarTabla(d) {
    var contenedor = vaciar('memoria-tabla');
    if (!contenedor) { return; }
    var filas = d.entradas.filter(function (e) { return estado.area === '' || (estado.area === SIN_AREA ? e.area === '' : e.area === estado.area); });
    if (!filas.length) { contenedor.appendChild(el('p', 'ausencia', 'Sin entradas para este filtro.')); return; }
    var tabla = el('table');
    tabla.appendChild(el('caption', '', 'Entradas de memoria' + (estado.area === '' ? '' : ' del área seleccionada') + ' (' + filas.length + ')'));
    var cab = el('tr');
    ['ID', 'Tipo', 'Estado', 'Área', 'Título', 'Fecha', 'Vigente', 'Relaciones'].forEach(function (t) {
      var th = el('th', '', t);
      th.setAttribute('scope', 'col');
      cab.appendChild(th);
    });
    var thead = el('thead');
    thead.appendChild(cab);
    tabla.appendChild(thead);
    var cuerpo = el('tbody');
    filas.forEach(function (e) {
      var tr = el('tr');
      var id = el('th', '', e.id);
      id.setAttribute('scope', 'row');
      tr.appendChild(id);
      [etiquetaTipo(e.tipo), e.estado, e.area === '' ? 'sin datos' : e.area, e.titular, dato(e.fecha), e.vigente ? 'vigente' : '—']
        .forEach(function (t) { tr.appendChild(el('td', '', t)); });
      var accion = el('td');
      accion.appendChild(botonRelaciones(e.id));
      tr.appendChild(accion);
      cuerpo.appendChild(tr);
    });
    tabla.appendChild(cuerpo);
    contenedor.appendChild(tabla);
  }

  function dibujarResumen(d) {
    dibujarGrafico(d);
    dibujarTabla(d);
  }

  /* ---- bandeja del curador: solo lectura ---------------------------------------------------------------------- */
  function dibujarBandeja(d) {
    var contenedor = vaciar('memoria-bandeja');
    if (!contenedor) { return; }
    contenedor.appendChild(el('p', 'filter-note', 'Solo lectura: las decisiones sobre los candidatos son de knowledge-curator.'));
    function bloque(titulo, n, items, situacion, fila) {
      var h = el('h3', '', titulo + ' (' + (n === null ? 'sin datos' : n) + ')');
      contenedor.appendChild(h);
      if (situacion === 'ausente') { contenedor.appendChild(el('p', 'ausencia', 'Carpeta ausente: ningún candidato.')); return; }
      if (situacion === 'no_disponible') { contenedor.appendChild(el('p', 'ausencia', 'Sin datos: no se pudo leer.')); return; }
      if (!items.length) { contenedor.appendChild(el('p', 'filter-note', 'Ninguno.')); return; }
      var ul = el('ul');
      items.forEach(function (i) { ul.appendChild(el('li', '', fila(i))); });
      contenedor.appendChild(ul);
      if (typeof n === 'number' && n > items.length) { contenedor.appendChild(el('p', 'filter-note', 'Se listan ' + items.length + ' de ' + n + '.')); }
      if (situacion === 'incompleto') { contenedor.appendChild(el('p', 'ausencia', 'Lectura incompleta: la carpeta tiene más ficheros de los que se leen.')); }
    }
    BANDEJA.forEach(function (par) {
      var e = d.bandeja.estados[par[0]];
      bloque(par[1], e.n, e.items, e.situacion, function (i) {
        return i.candidato + (i.titular ? ' — ' + i.titular : '') + (i.category ? ' [' + i.category + ']' : '');
      });
    });
    var a = d.bandeja.aprobadas;
    bloque('Aprobadas', a.n, a.items, 'ok', function (i) { return i.id + ' — ' + i.titular + (i.area ? ' · ' + i.area : ''); });
  }

  /* ---- línea de tiempo ---------------------------------------------------------------------------------------- */
  function cadena(id, mapa) {
    var vistos = {}, raizId = id;
    while (mapa[raizId] && mapa[raizId].sustituye_a.length && !vistos[raizId]) {
      vistos[raizId] = true;
      var previo = mapa[raizId].sustituye_a[0];
      if (!mapa[previo] || vistos[previo]) { raizId = previo; break; }
      raizId = previo;
    }
    var ruta = [raizId], actual = raizId, visto = {};
    visto[raizId] = true;
    while (mapa[actual] && mapa[actual].sustituida_por.length) {
      var siguiente = mapa[actual].sustituida_por[0];
      if (visto[siguiente]) { break; }
      visto[siguiente] = true;
      ruta.push(siguiente);
      actual = siguiente;
    }
    return ruta;
  }

  function dibujarLinea(d) {
    var ol = vaciar('memoria-linea');
    if (!ol) { return; }
    if (!d.entradas.length) { ol.appendChild(el('li', 'ausencia', 'Sin entradas.')); return; }
    var mapa = {};
    d.entradas.forEach(function (e) { mapa[e.id] = e; });
    var ordenadas = d.entradas.slice().sort(function (a, b) {
      if (a.fecha === b.fecha) { return a.id < b.id ? -1 : a.id > b.id ? 1 : 0; }
      if (a.fecha === null) { return 1; }
      if (b.fecha === null) { return -1; }
      return a.fecha < b.fecha ? -1 : 1;
    });
    ordenadas.forEach(function (e) {
      var li = el('li', 'entrada-tiempo');
      li.setAttribute('data-id', e.id);
      var partes = [dato(e.fecha), e.id, e.titular, e.estado];
      if (e.vigente) { partes.push('vigente'); }
      if (e.sustituye_a.length) { partes.push('sustituye a ' + e.sustituye_a.join(', ')); }
      if (e.sustituida_por.length) { partes.push('sustituida por ' + e.sustituida_por.join(', ')); }
      li.appendChild(el('span', '', partes.join(' · ')));
      var ruta = cadena(e.id, mapa);
      if (ruta.length > 1) { li.appendChild(el('span', 'filter-note', ' Cadena: ' + ruta.join(' → '))); }
      li.appendChild(raiz.document.createTextNode ? raiz.document.createTextNode(' ') : el('span', '', ' '));
      li.appendChild(botonRelaciones(e.id));
      ol.appendChild(li);
    });
  }

  /* ---- relaciones de UNA entrada: SVG + lista equivalente ------------------------------------------------------ */
  function titularDe(id, extra) {
    var e = estado.d && estado.d.entradas.filter(function (x) { return x.id === id; })[0];
    return e ? e.titular : (extra || '');
  }

  /* Normaliza las dos fuentes (relaciones incrustadas o respuesta de `api/memory`) a [{ grupo, id, relacion, ausente, titular }]. */
  function aristasDe(rel, desdeServidor) {
    var salida = [];
    GRUPOS.forEach(function (par) {
      var filas = rel[desdeServidor ? par[0] : CLAVE_EMBEBIDA[par[0]]] || [];
      filas.forEach(function (f) {
        if (par[0] === 'sucesion') {
          var id = desdeServidor ? f.id : f.id;
          salida.push({ grupo: 'sucesion', id: id, relacion: desdeServidor ? f.relation : f.relacion,
            ausente: desdeServidor ? f.entry === null : f.ausente, titular: desdeServidor && f.entry ? f.entry.titular : titularDe(id) });
        } else {
          var ident = desdeServidor ? f.id : f;
          salida.push({ grupo: par[0], id: ident, relacion: par[1], ausente: false, titular: desdeServidor ? f.titular : titularDe(ident) });
        }
      });
    });
    return salida;
  }

  /* `aviso`: texto cuando la lista no es todo lo que hay (recortada al presupuesto de 20, o lectura incompleta). */
  function pintarRelaciones(id, aristas, aviso) {
    var cuenta = aristas.length;
    pongo('memoria-relaciones-estado', 'Relaciones de ' + id + ': ' + cuenta + (cuenta === 1 ? ' relación' : ' relaciones')
      + ' a un salto (sucesión, misma iniciativa, misma área y enlaces declarados).' + (aviso ? ' ' + aviso : ''));
    var grafo = vaciar('memoria-grafo');
    var vecinos = [], vistos = {};
    aristas.forEach(function (a) { if (!vistos[a.id]) { vistos[a.id] = true; vecinos.push({ id: a.id, grupo: a.grupo }); } });
    if (grafo && raiz.PanelGraph && cuenta) {
      raiz.PanelGraph.dibujar(grafo, { titulo: 'Relaciones de ' + id + ': ' + cuenta + ' a un salto', centro: { id: id }, nodos: vecinos,
        aristas: aristas.map(function (a) { return { id: a.id, grupo: a.grupo, relacion: a.relacion }; }) });
    } else if (grafo) { grafo.appendChild(el('p', 'ausencia', 'Esta entrada no tiene relaciones declaradas.')); }
    var ul = vaciar('memoria-lista-relaciones');
    aristas.forEach(function (a) {
      var li = el('li');
      li.setAttribute('data-grupo', a.grupo);
      li.setAttribute('data-id', a.id);
      var grupo = GRUPOS.filter(function (p) { return p[0] === a.grupo; })[0][1];
      li.appendChild(el('span', '', grupo + ': ' + (a.grupo === 'sucesion' ? a.relacion + ' ' : '') + a.id
        + (a.ausente ? ' (no está en el corpus)' : a.titular ? ' — ' + a.titular : '') + ' '));
      if (!a.ausente && estado.d && estado.d.entradas.some(function (x) { return x.id === a.id; })) { li.appendChild(botonRelaciones(a.id)); }
      ul.appendChild(li);
    });
    var seccion = porId('memoria-relaciones');
    if (seccion && seccion.focus) { seccion.focus(); }
  }

  function verRelaciones(id) {
    var d = estado.d;
    if (!d) { return; }
    if (estado.modo !== 'servido') {
      var rel = d.relaciones && d.relaciones[id];
      if (!rel) { pongo('memoria-relaciones-estado', 'Sin datos de relaciones para ' + id + ' en esta copia estática.'); return; }
      var aviso = '';
      if (rel.recortado) {
        aviso = typeof rel.total === 'number' ? 'Aviso: se muestran ' + (rel.sucesion.length + rel.por_iniciativa.length + rel.por_area.length + rel.enlaces.length) + ' de ' + rel.total + ' relaciones (límite de lectura de 20); el resto no se lista.'
          : 'Aviso: la lista está recortada a 20 relaciones y hay más.';
      }
      pintarRelaciones(id, aristasDe(rel, false), aviso);
      return;
    }
    if (estado.ocupado) { return; }
    estado.ocupado = true;
    pongo('memoria-relaciones-estado', 'Leyendo las relaciones de ' + id + '…');
    var control = new raiz.AbortController();
    var plazo = raiz.setTimeout(function () { control.abort(); }, PLAZO_MS);
    var cuerpo = JSON.stringify({ operation: 'related', id: id });
    raiz.fetch('api/memory', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: cuerpo, credentials: 'omit',
      cache: 'no-store', signal: control.signal })
      .then(function (r) { if (!r.ok) { throw new Error('no disponible'); } return r.json(); })
      .then(function (resp) {
        if (control.signal.aborted || !validaRelated(resp, id)) { throw new Error('no disponible'); }
        var lista = aristasDe(resp.related, true);
        var avisoRelated = !resp.complete ? 'Aviso: lectura incompleta; puede haber más relaciones de las que se muestran.'
          : (lista.length >= 20 ? 'Aviso: se alcanzó el límite de 20 relaciones; puede haber más.' : '');
        pintarRelaciones(id, lista, avisoRelated);
      })
      .catch(function () { pongo('memoria-relaciones-estado', 'No se pudieron leer las relaciones de ' + id + '. Vuelve a intentarlo.'); })
      .then(function () { raiz.clearTimeout(plazo); estado.ocupado = false; });
  }

  /* ---- backends y journal ------------------------------------------------------------------------------------- */
  function etiquetaBackend(b) { return ETIQUETA_BACKEND[b.backend] || b.backend; }

  function dibujarBackends(d) {
    var contenedor = vaciar('memoria-backends');
    if (!contenedor) { return; }
    if (!d.backends.length) { contenedor.appendChild(el('p', 'ausencia', 'Sin datos de backends.')); return; }
    d.backends.forEach(function (b) {
      var tarjeta = el('article', 'card');
      if (b.situacion === 'no_configurado') {
        tarjeta.appendChild(el('h3', '', etiquetaBackend(b) + ': no configurado'));
        contenedor.appendChild(tarjeta);
        return;
      }
      tarjeta.appendChild(el('h3', '', etiquetaBackend(b) + ' · ' + (b.tipo || 'tipo sin datos') + (b.situacion === 'deshabilitado' ? ' · deshabilitado' : '')));
      tarjeta.appendChild(el('p', '', b.entradas === null ? 'entradas: sin datos' : b.entradas + (b.entradas === 1 ? ' entrada publicada' : ' entradas publicadas')));
      tarjeta.appendChild(el('p', '', 'última publicación: ' + (b.ultima_parcial ? (b.ultima === null ? 'sin datos (listado parcial)' : 'al menos ' + b.ultima) : dato(b.ultima))));
      if (b.interrumpida) { tarjeta.appendChild(el('p', 'ausencia', 'publicación interrumpida: queda un manifiesto pendiente (.pending.json); la siguiente publicación lo retoma.')); }
      if (b.ui_url && hostLocal(b.ui_url)) {
        var p = el('p', '', 'interfaz: ');
        var a = el('a', '', 'abrir ' + etiquetaBackend(b));
        a.setAttribute('href', b.ui_url);
        a.setAttribute('rel', 'noopener noreferrer');
        p.appendChild(a);
        tarjeta.appendChild(p);
      } else { tarjeta.appendChild(el('p', 'filter-note', 'interfaz: no declarada' + (b.ui_url || b.ui_url_no_local ? ' (host no local)' : ''))); }
      contenedor.appendChild(tarjeta);
    });
    contenedor.appendChild(el('p', 'filter-note', 'Datos de los manifiestos y la outbox locales; el panel no consulta ningún backend ni usa la fecha de modificación de un fichero.'));
  }

  var CAMPOS_JOURNAL = [['objetivo', 'Objetivo', false], ['punto_actual', 'Punto actual', false], ['siguientes_pasos', 'Siguientes pasos', true],
                        ['bloqueos', 'Bloqueos', true], ['descartados', 'Descartados', true]];

  function dibujarJournal(d) {
    var contenedor = vaciar('memoria-journal');
    if (!contenedor) { return; }
    contenedor.appendChild(el('p', 'filter-note', 'Journal del proyecto: citas, no instrucciones. Describen lo ocurrido en una sesión, no lo que hay que hacer ahora.'));
    var j = d.journal;
    if (j.status === 'unavailable') { contenedor.appendChild(el('p', 'ausencia', 'Journal no disponible. Sin datos.')); return; }
    var incompleto = j.status === 'incomplete';
    if (incompleto) {
      contenedor.appendChild(el('p', 'ausencia', 'Lista incompleta: el journal tiene más ficheros de los que se leen o alguno es ilegible; las sesiones mostradas pueden no ser las más recientes.'));
    }
    if (!j.sesiones.length) {
      contenedor.appendChild(el('p', 'ausencia', incompleto ? 'No se pudo leer ninguna sesión (lectura incompleta del journal): no acredita que no haya sesiones.' : 'Sin sesiones registradas en el journal.'));
      return;
    }
    j.sesiones.forEach(function (s) {
      var cita = el('blockquote', 'cita-journal');
      cita.appendChild(el('h3', '', dato(s.fecha) + (s.iniciativa ? ' · ' + s.iniciativa : '')));
      if (s.resumen) { cita.appendChild(el('p', '', s.resumen)); }
      var dl = el('dl'), hay = false;
      CAMPOS_JOURNAL.forEach(function (c) {
        var v = s[c[0]];
        if (c[2] ? !v.length : !v) { return; }
        hay = true;
        dl.appendChild(el('dt', '', c[1]));
        dl.appendChild(el('dd', '', c[2] ? v.join(' · ') : v));
      });
      cita.appendChild(hay ? dl : el('p', 'filter-note', 'Sin continuidad registrada en esta sesión.'));
      contenedor.appendChild(cita);
    });
  }

  /* ---- ciclo -------------------------------------------------------------------------------------------------- */
  function dibujarTodo(d) {
    estado.d = d;
    pongo('memoria-estado', estadoGeneral(d));
    pongo('memoria-area-nota', d.recortado > 0 ? 'Con la respuesta recortada, el filtro de área y sus recuentos solo cuentan las ' + d.entradas.length + ' entradas mostradas de ' + d.total + '.' : '');
    opcionesArea(d);
    dibujarResumen(d);
    dibujarBandeja(d);
    dibujarLinea(d);
    dibujarBackends(d);
    dibujarJournal(d);
  }

  function sinDatos(motivo) {
    estado.d = null;
    pongo('memoria-estado', estadoGeneral(null, motivo));
    ['grafico-memoria', 'memoria-tabla', 'memoria-bandeja', 'memoria-linea', 'memoria-backends', 'memoria-journal'].forEach(function (id) {
      var n = vaciar(id);
      if (n) { n.appendChild(el('p', 'ausencia', 'Sin datos.')); }
    });
  }

  function leer() {
    if (estado.enVuelo) { return; }
    estado.enVuelo = true;
    var control = new raiz.AbortController();
    var plazo = raiz.setTimeout(function () { control.abort(); }, PLAZO_MS);
    raiz.fetch('api/memoria', { credentials: 'omit', cache: 'no-store', signal: control.signal })
      .then(function (r) { if (!r.ok) { throw new Error('no disponible'); } return r.json(); })
      .then(function (d) {
        if (control.signal.aborted || !validar(d)) { throw new Error('no disponible'); }
        if (d.status === 'unavailable' && !estado.d && d.issues.some(function (i) { return i.status === 'calculando'; })) {
          sinDatos('calculando');
          raiz.setTimeout(leer, REINTENTO_MS);
          return;
        }
        if (d.status === 'unavailable' && estado.d) { throw new Error('no disponible'); }
        if (d.status === 'unavailable') { dibujarTodo(d); return; }
        dibujarTodo(d);
      })
      .catch(function () {
        if (estado.d) {
          pongo('memoria-estado', 'No se pudo actualizar. Se conserva la última vista y su fecha (' + estado.d.observed_at + '); no se acredita su vigencia.');
        } else { sinDatos('no_disponible'); }
      })
      .then(function () { raiz.clearTimeout(plazo); estado.enVuelo = false; });
  }

  function iniciar() {
    var nodo = porId('panel-data');
    var datos = {};
    try { datos = JSON.parse(nodo.textContent); } catch (e) { datos = {}; }
    estado.chart = datos.chartjs_disponible !== false;
    estado.modo = datos.modo === 'servido' ? 'servido' : 'exportado';
    var sel = porId('memoria-area');
    if (sel) { sel.addEventListener('change', function () { estado.area = sel.value; if (estado.d) { dibujarResumen(estado.d); } }); }
    if (estado.modo === 'servido') {
      var boton = porId('memoria-actualizar');
      if (boton) { boton.hidden = false; boton.addEventListener('click', leer); }
      leer();
      return;
    }
    if (datos.memoria === undefined) { sinDatos('sin_memoria'); }
    else if (validar(datos.memoria)) { dibujarTodo(datos.memoria); }
    else { sinDatos('invalida'); }
  }

  var Memoria = { iniciar: iniciar, validar: validar };
  raiz.PanelMemoria = Memoria;
  if (raiz.document && raiz.document.getElementById && raiz.document.getElementById('memoria-estado')) { iniciar(); }
})(typeof window !== 'undefined' ? window : globalThis);
