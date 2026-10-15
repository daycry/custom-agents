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

  var Inicio = { iniciar: iniciar, dibujar: dibujar };
  raiz.PanelInicio = Inicio;
  if (raiz.document && raiz.document.getElementById && raiz.document.getElementById('cartera-estado')) { iniciar(); }
})(typeof window !== 'undefined' ? window : globalThis);
