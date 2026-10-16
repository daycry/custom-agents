/* Grafo pequeño de UNA entrada de memoria: SVG propio, sin librerías ni red.
   Dibuja el nodo central y los vecinos a UN salto (nunca el grafo completo), con una arista por relación. Los grupos
   se distinguen por la forma del nodo y el trazo de la arista (no solo por color) y cada nodo lleva su etiqueta de
   texto. El SVG es una ayuda visual con nombre accesible: la lista textual equivalente (que arma la página) es la
   alternativa navegable por teclado. Todo texto entra por textContent/setAttribute; nada de HTML insertado. */
(function (raiz) {
  'use strict';

  var SVG = 'http://www.w3.org/2000/svg';
  var ANCHO = 640, ALTO = 440, RX = 230, RY = 150;
  /* Trazo de la arista y forma del nodo por grupo. */
  var TRAZOS = { sucesion: '', iniciativa: '8 4', area: '2 4', enlaces: '12 3 2 3' };
  var FORMAS = { sucesion: 'rombo', iniciativa: 'cuadrado', area: 'circulo', enlaces: 'triangulo' };

  function svg(etiqueta, atributos, texto) {
    var nodo = raiz.document.createElementNS(SVG, etiqueta);
    Object.keys(atributos || {}).forEach(function (k) { nodo.setAttribute(k, String(atributos[k])); });
    if (texto !== undefined) { nodo.textContent = texto; }
    return nodo;
  }
  function numero(v) { return Math.round(v * 10) / 10; }

  function forma(grupo, x, y, esCentro) {
    var r = esCentro ? 14 : 10;
    var tipo = esCentro ? 'circulo' : FORMAS[grupo] || 'circulo';
    if (tipo === 'rombo') {
      return svg('polygon', { points: [x, y - r - 2, x + r + 2, y, x, y + r + 2, x - r - 2, y].join(',') });
    }
    if (tipo === 'cuadrado') { return svg('rect', { x: numero(x - r), y: numero(y - r), width: 2 * r, height: 2 * r }); }
    if (tipo === 'triangulo') {
      return svg('polygon', { points: [x, y - r - 2, x + r + 2, y + r, x - r - 2, y + r].join(',') });
    }
    return svg('circle', { cx: numero(x), cy: numero(y), r: r });
  }

  /* spec: { titulo, centro: { id }, nodos: [{ id, grupo }] (vecinos únicos, el grupo es el de su primera relación),
             aristas: [{ id, grupo, relacion }] (id del vecino) }
     Devuelve el <svg>; no lo inserta. */
  function dibujar(contenedor, spec) {
    var cx = ANCHO / 2, cy = ALTO / 2;
    var figura = svg('svg', { viewBox: '0 0 ' + ANCHO + ' ' + ALTO, role: 'img', 'class': 'grafo-memoria',
      'aria-label': spec.titulo, width: '100%', height: ALTO, focusable: 'false' });
    figura.appendChild(svg('title', {}, spec.titulo));
    figura.appendChild(svg('desc', {}, 'Nodo central ' + spec.centro.id + ' y ' + spec.nodos.length
      + (spec.nodos.length === 1 ? ' entrada relacionada' : ' entradas relacionadas')
      + '. Las mismas relaciones están en la lista de texto siguiente.'));
    var n = spec.nodos.length;
    var posicion = {};
    spec.nodos.forEach(function (nodo, i) {
      var angulo = -Math.PI / 2 + (2 * Math.PI * i) / Math.max(n, 1);
      posicion[nodo.id] = { x: cx + RX * Math.cos(angulo), y: cy + RY * Math.sin(angulo) };
    });
    /* Aristas entre el mismo par: se separan un poco en perpendicular para que no se tapen. */
    var porPar = {};
    spec.aristas.forEach(function (a) { (porPar[a.id] = porPar[a.id] || []).push(a); });
    spec.aristas.forEach(function (a) {
      var p = posicion[a.id];
      if (!p) { return; }
      var grupo = porPar[a.id], k = grupo.indexOf(a), m = grupo.length;
      var dx = p.x - cx, dy = p.y - cy, largo = Math.sqrt(dx * dx + dy * dy) || 1;
      var desplazamiento = (k - (m - 1) / 2) * 7;
      var ox = (-dy / largo) * desplazamiento, oy = (dx / largo) * desplazamiento;
      var linea = svg('line', { x1: numero(cx + ox), y1: numero(cy + oy), x2: numero(p.x + ox), y2: numero(p.y + oy),
        'class': 'arista arista-' + a.grupo, 'data-grupo': a.grupo, 'data-id': a.id, 'data-relacion': a.relacion || a.grupo });
      if (TRAZOS[a.grupo]) { linea.setAttribute('stroke-dasharray', TRAZOS[a.grupo]); }
      linea.appendChild(svg('title', {}, (a.relacion || a.grupo) + ': ' + spec.centro.id + ' → ' + a.id));
      figura.appendChild(linea);
    });
    function nodoSvg(id, grupo, x, y, esCentro) {
      var g = svg('g', { 'class': 'nodo' + (esCentro ? ' nodo-centro' : ' nodo-' + grupo), 'data-id': id });
      g.appendChild(forma(grupo, x, y, esCentro));
      g.appendChild(svg('text', { x: numero(x), y: numero(y + (y >= cy ? 28 : -20)), 'text-anchor': 'middle' }, id));
      return g;
    }
    figura.appendChild(nodoSvg(spec.centro.id, 'centro', cx, cy, true));
    spec.nodos.forEach(function (nodo) { figura.appendChild(nodoSvg(nodo.id, nodo.grupo, posicion[nodo.id].x, posicion[nodo.id].y, false)); });
    contenedor.replaceChildren(figura);
    return figura;
  }

  var Grafo = { dibujar: dibujar, TRAZOS: TRAZOS, FORMAS: FORMAS };
  raiz.PanelGraph = Grafo;
  if (typeof module === 'object' && module.exports) { module.exports = Grafo; }
})(typeof window !== 'undefined' ? window : globalThis);
