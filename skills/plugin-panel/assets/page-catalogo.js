/* Página Catálogo: filtros, navegación a anclas, etapas del flujo y el gráfico de piezas por tipo.
   Sin red y sin inserción de HTML: todo el texto entra por textContent. */
(function (raiz) {
  'use strict';

  var ETIQUETAS = [['agents', 'Agentes'], ['skills', 'Skills'], ['commands', 'Comandos'],
                   ['tools', 'Herramientas'], ['hooks', 'Acciones de hook']];

  /* Filtro por texto y por selectores sobre las tarjetas de una sección. */
  function connectFilters(sectionId, searchId, resultId, filters, label) {
    var doc = raiz.document;
    var section = doc.getElementById(sectionId);
    var search = doc.getElementById(searchId);
    var result = doc.getElementById(resultId);
    var cards = Array.prototype.slice.call(section.querySelectorAll('.card'));
    var controls = filters.map(function (f) { return [doc.getElementById(f[0]), f[1]]; });
    function filter() {
      var count = 0;
      var query = search.value.toLocaleLowerCase();
      cards.forEach(function (card) {
        var visible = controls.every(function (c) {
          var control = c[0], attribute = c[1];
          return control.value === 'all'
            || (sectionId === 'catalog' && attribute === 'runtime' && card.dataset.kind !== 'hooks')
            || card.dataset[attribute] === control.value;
        }) && card.textContent.toLocaleLowerCase().indexOf(query) !== -1;
        card.hidden = !visible;
        if (visible) { count++; }
      });
      result.textContent = count + ' ' + label + ' visibles';
    }
    search.addEventListener('input', filter);
    controls.forEach(function (c) { c[0].addEventListener('change', filter); });
    filter();
  }

  /* Gráfico de piezas por tipo con los `counts` de build_panel.py --json; un conteo ausente va como null. */
  function dibujarPiezas(datos) {
    var contenedor = raiz.document.getElementById('grafico-piezas');
    if (!contenedor || !raiz.PanelCharts) { return; }
    var cuentas = (datos && datos.contadores) || {};
    raiz.PanelCharts.dibujar(contenedor, {
      id: 'grafico-piezas-tipo',
      titulo: 'Piezas por tipo',
      descripcion: 'Número de piezas declaradas de cada tipo en el bundle.',
      tipo: 'bar',
      categoria: 'Tipo de pieza',
      etiquetas: ETIQUETAS.map(function (e) { return e[1]; }),
      origen: 'build_panel.py --json (counts)',
      series: [{ nombre: 'Piezas', valores: ETIQUETAS.map(function (e) {
        var v = cuentas[e[0]];
        return typeof v === 'number' && isFinite(v) ? v : null;
      }) }]
    }, { chartDisponible: !(datos && datos.chartjs_disponible === false) });
  }

  function sincronizarAncla() {
    var doc = raiz.document;
    var estado = doc.getElementById('navigation-status');
    var id;
    try { id = decodeURIComponent(raiz.location.hash.slice(1)); } catch (e) { id = null; }
    var destino = id ? doc.getElementById(id) : null;
    if (estado) {
      estado.textContent = (id === null || (id && !destino)) ? 'Destino no disponible en esta instantánea.' : '';
    }
    var hook = id && id.indexOf('hook-') === 0 && destino ? destino.closest('[data-kind="hooks"]') : null;
    if (hook) {
      doc.getElementById('search').value = '';
      doc.getElementById('kind').value = 'hooks';
      doc.getElementById('hook-runtime').value = hook.dataset.runtime;
      doc.getElementById('kind').dispatchEvent(new raiz.Event('change'));
    }
    if (destino) {
      var detalles = destino.matches('details') ? destino : destino.querySelector('details');
      if (detalles) { detalles.open = true; }
      destino.setAttribute('tabindex', '-1');
      destino.focus({ preventScroll: true });
    }
  }

  function etapas() {
    var doc = raiz.document;
    var botones = Array.prototype.slice.call(doc.querySelectorAll('.flow-steps button'));
    var paneles = Array.prototype.slice.call(doc.querySelectorAll('.flow-detail'));
    botones.forEach(function (boton) {
      boton.addEventListener('click', function () {
        botones.forEach(function (b) { b.setAttribute('aria-pressed', String(b === boton)); });
        paneles.forEach(function (p) { p.hidden = p.id !== boton.getAttribute('aria-controls'); });
      });
    });
  }

  function leerDatos() {
    var nodo = raiz.document.getElementById('panel-data');
    try { return JSON.parse(nodo.textContent); } catch (e) { return {}; }
  }

  function iniciar() {
    var doc = raiz.document;
    dibujarPiezas(leerDatos());
    connectFilters('catalog', 'search', 'results', [['kind', 'kind'], ['hook-runtime', 'runtime']], 'capacidades');
    connectFilters('extensions', 'extension-search', 'extension-results',
      [['extension-kind', 'kind'], ['extension-scope', 'scope'], ['extension-runtime', 'runtime']], 'declaraciones');
    etapas();
    raiz.addEventListener('hashchange', sincronizarAncla);
    doc.addEventListener('click', function (evento) {
      var enlace = evento.target.closest ? evento.target.closest('a[href^="#"]') : null;
      if (enlace && !evento.defaultPrevented && evento.button === 0 && !evento.altKey && !evento.ctrlKey
          && !evento.metaKey && !evento.shiftKey && !enlace.hasAttribute('download')
          && (!enlace.target || enlace.target === '_self') && enlace.hash === raiz.location.hash) {
        sincronizarAncla();
      }
    });
    sincronizarAncla();
  }

  var Catalogo = { connectFilters: connectFilters, dibujarPiezas: dibujarPiezas, iniciar: iniciar };
  raiz.PanelCatalogo = Catalogo;
  if (raiz.document && raiz.document.getElementById && raiz.document.getElementById('panel-data')) { iniciar(); }
})(typeof window !== 'undefined' ? window : globalThis);
