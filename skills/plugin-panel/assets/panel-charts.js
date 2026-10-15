/* Adaptador de gráficos: cada gráfico es un <figure> con su tabla equivalente.
   Sin Chart.js (o con su huella sin verificar) la página sigue entera, solo con la tabla y un aviso.
   Todo el texto entra por textContent. */
(function (raiz) {
  'use strict';

  var FORMAS = ['circle', 'rect', 'triangle', 'rectRot', 'cross', 'star'];
  var N_SERIES = 6;

  function el(etiqueta, clase, texto) {
    var nodo = raiz.document.createElement(etiqueta);
    if (clase) { nodo.className = clase; }
    if (texto !== undefined) { nodo.textContent = texto; }
    return nodo;
  }

  function color(nombre) {
    var raizDoc = raiz.document.documentElement;
    var valor = raiz.getComputedStyle ? raiz.getComputedStyle(raizDoc).getPropertyValue(nombre) : '';
    return String(valor || '').trim() || undefined;
  }

  function nucleo() { return raiz.PanelCore; }

  function hayValores(spec) {
    return spec.series.some(function (s) {
      return s.valores.some(function (v) { return typeof v === 'number' && isFinite(v); });
    });
  }

  function tabla(spec) {
    var region = el('div', 'tabla-equivalente');
    region.setAttribute('role', 'region');
    region.setAttribute('tabindex', '0');
    region.setAttribute('aria-label', 'Tabla equivalente: ' + spec.titulo);
    var t = el('table');
    t.appendChild(el('caption', '', spec.titulo));
    var cabecera = el('tr');
    var primera = el('th', '', spec.categoria || 'Categoría');
    primera.setAttribute('scope', 'col');
    cabecera.appendChild(primera);
    spec.series.forEach(function (s) {
      var th = el('th', '', s.nombre);
      th.setAttribute('scope', 'col');
      cabecera.appendChild(th);
    });
    var thead = el('thead');
    thead.appendChild(cabecera);
    t.appendChild(thead);
    var cuerpo = el('tbody');
    spec.etiquetas.forEach(function (etiqueta, i) {
      var fila = el('tr');
      var th = el('th', '', etiqueta);
      th.setAttribute('scope', 'row');
      fila.appendChild(th);
      spec.series.forEach(function (s) {
        var valor = s.valores[i];
        var ausente = nucleo().celda(valor) === 'sin datos';
        fila.appendChild(el('td', ausente ? 'sin-datos' : '', nucleo().celda(valor) + (!ausente && spec.unidad ? ' ' + spec.unidad : '')));
      });
      cuerpo.appendChild(fila);
    });
    t.appendChild(cuerpo);
    region.appendChild(t);
    return region;
  }

  function configuracion(spec) {
    var linea = spec.tipo === 'line';
    var texto = color('--texto');
    var borde = color('--borde');
    if (raiz.Chart && raiz.Chart.defaults) {
      if (texto) { raiz.Chart.defaults.color = texto; }
      if (borde) { raiz.Chart.defaults.borderColor = borde; }
    }
    return {
      type: linea ? 'line' : 'bar',
      data: {
        labels: spec.etiquetas.slice(),
        datasets: spec.series.map(function (s, i) {
          var c = color('--serie-' + ((i % N_SERIES) + 1));
          return {
            label: s.nombre,
            data: s.valores.map(function (v) { return typeof v === 'number' && isFinite(v) ? v : null; }),
            backgroundColor: c,
            borderColor: linea ? c : texto,
            borderWidth: 2,
            pointStyle: FORMAS[i % FORMAS.length],
            pointRadius: linea ? 5 : undefined,
            spanGaps: false
          };
        })
      },
      options: {
        animation: false,
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: true }, title: { display: false } }
      }
    };
  }

  /* Dibuja `spec` dentro de `contenedor`.
     spec: { id, titulo, descripcion?, tipo: 'bar'|'line', categoria?, unidad?, etiquetas: [], origen?,
             series: [{ nombre, valores: [número|null] }], parcial?: { presentes, total, origen? } }
     opciones: { chartDisponible: false } fuerza el modo solo tabla. */
  function dibujar(contenedor, spec, opciones) {
    var opts = opciones || {};
    var figura = el('figure', 'grafico');
    if (spec.id) { figura.setAttribute('id', spec.id); }
    figura.appendChild(el('figcaption', '', spec.titulo));
    var origen = spec.origen;
    var dibujable = hayValores(spec);

    if (spec.parcial) {
      nucleo().renderAusencia(figura, { estado: 'parcial', presentes: spec.parcial.presentes,
        total: spec.parcial.total, origen: spec.parcial.origen || origen });
    }
    if (!dibujable) {
      nucleo().renderAusencia(figura, { estado: 'sin-datos', origen: origen });
    } else {
      var avisoChart = null;
      var puedeChart = opts.chartDisponible !== false && typeof raiz.Chart === 'function';
      if (puedeChart) {
        var envoltorio = el('div', 'lienzo');
        var canvas = el('canvas');
        canvas.setAttribute('role', 'img');
        canvas.setAttribute('aria-label', spec.titulo + (spec.descripcion ? '. ' + spec.descripcion : '')
          + '. Los mismos datos están en la tabla siguiente.');
        envoltorio.appendChild(canvas);
        try {
          new raiz.Chart(canvas, configuracion(spec));
          figura.appendChild(envoltorio);
        } catch (e) {
          puedeChart = false;
        }
      }
      if (!puedeChart) {
        avisoChart = el('p', 'ausencia', 'Chart.js no está disponible (falta el fichero o su huella no coincide): se muestra solo la tabla.');
        avisoChart.setAttribute('role', 'status');
        figura.appendChild(avisoChart);
      }
    }
    figura.appendChild(tabla(spec));
    contenedor.appendChild(figura);
    return figura;
  }

  var Graficos = { dibujar: dibujar, FORMAS: FORMAS };
  raiz.PanelCharts = Graficos;
  if (typeof module === 'object' && module.exports) { module.exports = Graficos; }
})(typeof window !== 'undefined' ? window : globalThis);
