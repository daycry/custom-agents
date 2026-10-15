/* Página Iniciativas: kanban de SOLO LECTURA con una columna por estado de spec y una tarjeta por iniciativa,
   con sus alertas en texto, más los gráficos de horas y coste por iniciativa (cada uno con su tabla).
   Las cifras salen de la cartera (`api/cartera` o el JSON incrustado) y aquí no se recalculan. Un dato ausente
   se dice («sin datos»); nunca se pinta como 0. Sin arrastre, sin controles que escriban y sin HTML insertado:
   todo el texto entra por textContent. La tarjeta con plan es un enlace nativo a `plan-<id16>.html`. */
(function (raiz) {
  'use strict';

  var C = function () { return raiz.PanelCartera; };
  var ESTADOS_FIJOS = ['borrador', 'aprobada', 'implementada', 'obsoleta'];
  var vistaPintada = null;
  var graficosPintados = {};
  var chartjsDisponible = true;

  function el(etiqueta, clase, texto) {
    var nodo = raiz.document.createElement(etiqueta);
    if (clase) { nodo.className = clase; }
    if (texto !== undefined) { nodo.textContent = texto; }
    return nodo;
  }
  function pongo(id, texto) {
    var nodo = raiz.document.getElementById(id);
    if (nodo) { nodo.textContent = texto; }
    return nodo;
  }
  function hayDatos(d) { return d && (d.status === 'ok' || d.status === 'partial'); }

  function estadoGeneral(d, motivo) {
    if (!d && motivo === 'sin_cartera') {
      return 'Sin datos: esta copia estática no incluye la cartera (se genera con --project).';
    }
    if (!d) { return 'No se pudo leer la cartera. Sin datos de iniciativas; vuelve a intentarlo.'; }
    if (d.status === 'unavailable') { return 'Cartera no disponible: no se pudo leer el roadmap. Sin datos.'; }
    if (d.status === 'not_found') { return 'No se encontró el roadmap del proyecto (docs/roadmap). Sin datos.'; }
    var fecha = ' Lectura obtenida: ' + d.observed_at + '.';
    if (d.status === 'partial' || !d.complete) {
      return 'Lectura parcial: se muestran las iniciativas leídas; lo omitido no acredita ausencia.' + fecha;
    }
    if (!d.iniciativas.length) { return 'El roadmap no tiene iniciativas.' + fecha; }
    return 'Cartera derivada de docs/roadmap.' + fecha;
  }

  function lineaTareas(f) {
    if (f.tareas) { return 'Tareas: ' + f.tareas.completadas + '/' + f.tareas.total + ' tareas (' + f.tareas.pct + ' %)'; }
    if (f.ledger === 'fuera_de_tope') { return 'Tareas: sin datos (ledger fuera del tope de lectura)'; }
    if (f.ledger === 'sin_ledger') { return 'Tareas: sin datos (sin ledger)'; }
    return 'Tareas: sin datos (ledger no legible)';
  }
  function lineaHoras(f) {
    return 'Horas (IA + supervisión): real ' + C().horas(f.horas.real)
      + ' · estimado ' + C().horas(f.horas.est);
  }
  function lineaCoste(f) {
    var est = f.coste.est_eur !== null ? C().eur(f.coste.est_eur) : (f.coste.est_texto || 'sin datos');
    return 'Coste: real ' + C().eur(f.coste.real_eur) + (f.coste.real_parcial ? ' (parcial)' : '') + ' · estimado ' + est;
  }

  function tarjeta(f) {
    var art = el('article', 'card');
    art.dataset.id = f.id;
    var titulo = el('h3');
    if (f.tiene_plan) {
      var enlace = el('a', 'enlace-tarjeta', f.slug);
      enlace.setAttribute('href', 'plan-' + f.id + '.html');
      titulo.appendChild(enlace);
    } else {
      titulo.textContent = f.slug;
    }
    art.appendChild(titulo);
    art.appendChild(el('p', 'tarjeta-titulo', f.titulo));
    art.appendChild(el('p', '', 'Spec: ' + C().categoriaTexto(f)));
    art.appendChild(el('p', '', 'Fecha: ' + (f.fecha || 'sin datos') + (f.tiene_plan ? '' : ' · sin plan')));
    art.appendChild(el('p', '', lineaTareas(f)));
    art.appendChild(el('p', '', lineaHoras(f)));
    art.appendChild(el('p', '', lineaCoste(f)));
    art.appendChild(el('p', '', 'procedencia: ' + f.procedencia.medidos + ' medidos · ' + f.procedencia.estimados
      + ' estimados · ' + f.procedencia.desconocidos + ' desconocidos'));
    if (f.alertas.length) {
      var lista = el('ul', 'alertas');
      f.alertas.forEach(function (a) { lista.appendChild(el('li', '', C().alertaTexto(a))); });
      art.appendChild(lista);
    }
    return art;
  }

  function dibujarKanban(d) {
    var tablero = raiz.document.getElementById('kanban-iniciativas');
    if (!tablero) { return; }
    var clave = hayDatos(d) ? JSON.stringify(d.iniciativas) : 'sin-datos';
    if (clave === vistaPintada) { return; }
    vistaPintada = clave;
    if (!hayDatos(d)) {
      tablero.replaceChildren(el('p', 'ausencia', 'Sin datos: no hay lectura de la cartera.'));
      return;
    }
    var columnas = [];
    C().CATEGORIAS.forEach(function (c) {
      var filas = d.iniciativas.filter(function (f) { return f.categoria === c[0]; });
      if (!filas.length && ESTADOS_FIJOS.indexOf(c[0]) === -1) { return; }
      var seccion = el('section', 'columna');
      seccion.appendChild(el('h2', '', c[1] + ' (' + filas.length + ')'));
      if (!filas.length) { seccion.appendChild(el('p', 'columna-vacia', 'Ninguna iniciativa.')); }
      filas.forEach(function (f) { seccion.appendChild(tarjeta(f)); });
      columnas.push(seccion);
    });
    tablero.replaceChildren.apply(tablero, columnas);
  }

  /* Un gráfico real frente a estimado por iniciativa. `leer(fila)` devuelve [real, est] (null si falta). Las
     iniciativas sin ningún valor van solo a la tabla («sin datos»); un valor ausente nunca se pinta como 0. */
  function dibujarPareja(id, d, def) {
    var contenedor = raiz.document.getElementById(id);
    if (!contenedor || !raiz.PanelCharts) { return; }
    var etiquetas = [], reales = [], estimados = [], sinDatos = [];
    if (hayDatos(d)) {
      d.iniciativas.forEach(function (f) {
        var par = def.leer(f);
        if (par[0] === null && par[1] === null) { sinDatos.push(f.slug); return; }
        etiquetas.push(f.slug); reales.push(par[0]); estimados.push(par[1]);
      });
    }
    var clave = hayDatos(d) ? JSON.stringify([etiquetas, reales, estimados, sinDatos]) : 'sin-datos';
    if (graficosPintados[id] === clave) { return; }
    graficosPintados[id] = clave;
    contenedor.replaceChildren();
    raiz.PanelCharts.dibujar(contenedor, {
      id: def.id, titulo: def.titulo, descripcion: def.descripcion, tipo: 'bar', categoria: 'Iniciativa',
      unidad: def.unidad, origen: 'api/cartera (build_dashboard.py --json y progress-report.py)',
      etiquetas: etiquetas, sinDatos: sinDatos,
      series: [{ nombre: def.real, valores: reales }, { nombre: def.est, valores: estimados }]
    }, { chartDisponible: chartjsDisponible });
  }

  function dibujarGraficos(d) {
    dibujarPareja('grafico-horas', d, {
      id: 'grafico-horas-iniciativa', titulo: 'Horas por iniciativa: real frente a estimado',
      descripcion: 'Horas de IA más supervisión, reales y estimadas, de cada iniciativa que declara alguna.',
      unidad: 'h', real: 'Real (h)', est: 'Estimado (h)',
      leer: function (f) { return [f.horas.real, f.horas.est]; } });
    dibujarPareja('grafico-coste', d, {
      id: 'grafico-coste-iniciativa', titulo: 'Coste por iniciativa: real frente a estimado',
      descripcion: 'Coste real medido y coste estimado en euros de cada iniciativa que declara alguno.',
      unidad: '€', real: 'Real (€)', est: 'Estimado (€)',
      leer: function (f) { return [f.coste.real_eur, f.coste.est_eur]; } });
  }

  function dibujar(d, motivo) {
    pongo('cartera-estado', estadoGeneral(d, motivo));
    dibujarKanban(d);
    dibujarGraficos(d);
  }

  function iniciar() {
    var nodo = raiz.document.getElementById('panel-data');
    try { chartjsDisponible = JSON.parse(nodo.textContent).chartjs_disponible !== false; } catch (e) { chartjsDisponible = false; }
    var previo = null;
    C().iniciar(function (cartera) { previo = cartera; dibujar(cartera); },
      function (hayPrevio, motivo) {
        if (hayPrevio && previo) {
          pongo('cartera-estado', 'No se pudo actualizar. Se conserva la última vista y su fecha ('
            + previo.observed_at + '); no se acredita su vigencia.');
        } else { dibujar(null, motivo); }
      });
  }

  raiz.PanelIniciativas = { iniciar: iniciar, dibujar: dibujar, el: el, hayDatos: hayDatos };
  if (raiz.document && raiz.document.getElementById && raiz.document.getElementById('kanban-iniciativas')) { iniciar(); }
})(typeof window !== 'undefined' ? window : globalThis);
