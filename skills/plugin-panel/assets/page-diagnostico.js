/* Página Diagnóstico: filtros de la instantánea de doctor y navegación a sus filas.
   El panel no ejecuta doctor ni lee nada más: solo filtra lo que ya está en la página. */
(function (raiz) {
  'use strict';

  function filtrar() {
    var doc = raiz.document;
    var control = doc.getElementById('diagnostic-state');
    var busqueda = doc.getElementById('diagnostic-search');
    var resultado = doc.getElementById('diagnostic-results');
    if (!control || !busqueda || !resultado) { return; }
    var consulta = busqueda.value.toLocaleLowerCase();
    var cuenta = 0;
    Array.prototype.slice.call(doc.querySelectorAll('.diagnostic-block')).forEach(function (bloque) {
      var coincide = 0;
      Array.prototype.slice.call(bloque.querySelectorAll('.diagnostic-row')).forEach(function (fila) {
        var visible = (control.value === 'all' || fila.dataset.state === control.value)
          && fila.textContent.toLocaleLowerCase().indexOf(consulta) !== -1;
        fila.hidden = !visible;
        if (visible) { coincide++; cuenta++; }
      });
      bloque.hidden = coincide === 0;
    });
    resultado.textContent = cuenta + ' comprobaciones coincidentes';
  }

  function sincronizarAncla() {
    var doc = raiz.document;
    if (!raiz.location || !raiz.location.hash) { return; }
    var id;
    try { id = decodeURIComponent(raiz.location.hash.slice(1)); } catch (e) { return; }
    var destino = id ? doc.getElementById(id) : null;
    if (!destino || !destino.classList || !destino.classList.contains('diagnostic-row')) { return; }
    doc.getElementById('diagnostic-state').value = 'all';
    doc.getElementById('diagnostic-search').value = '';
    filtrar();
    var detalles = destino.closest('details');
    if (detalles) { detalles.open = true; }
    destino.setAttribute('tabindex', '-1');
    destino.focus({ preventScroll: true });
  }

  function iniciar() {
    var doc = raiz.document;
    var control = doc.getElementById('diagnostic-state');
    if (!control) { return; }
    control.addEventListener('change', filtrar);
    doc.getElementById('diagnostic-search').addEventListener('input', filtrar);
    filtrar();
    raiz.addEventListener('hashchange', sincronizarAncla);
    sincronizarAncla();
  }

  raiz.PanelDiagnostico = { iniciar: iniciar, filtrar: filtrar };
  if (raiz.document && raiz.document.getElementById && raiz.document.getElementById('panel-data')) { iniciar(); }
})(typeof window !== 'undefined' ? window : globalThis);
