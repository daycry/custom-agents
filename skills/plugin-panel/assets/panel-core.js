/* Núcleo del panel: menú accesible y utilidades comunes. Sin red y sin inserción de HTML. */
(function (raiz) {
  'use strict';

  /* Menú plegable en pantallas estrechas. Sin JavaScript el menú queda siempre visible. */
  function iniciarMenu() {
    var boton = raiz.document.getElementById('menu-toggle');
    var nav = raiz.document.getElementById('panel-nav');
    if (!boton || !nav) { return; }
    var consulta = raiz.matchMedia ? raiz.matchMedia('(max-width: 760px)') : { matches: false };

    function abrir(abierto) {
      nav.hidden = !abierto;
      boton.setAttribute('aria-expanded', abierto ? 'true' : 'false');
    }
    function ajustar() {
      if (consulta.matches) {
        boton.hidden = false;
        abrir(false);
      } else {
        boton.hidden = true;
        nav.hidden = false;
        boton.setAttribute('aria-expanded', 'false');
      }
    }
    boton.addEventListener('click', function () { abrir(nav.hidden); });
    raiz.document.addEventListener('keydown', function (evento) {
      if (evento.key === 'Escape' && !nav.hidden && !boton.hidden) {
        evento.preventDefault();
        abrir(false);
        boton.focus();
      }
    });
    if (consulta.addEventListener) { consulta.addEventListener('change', ajustar); }
    ajustar();
  }

  /* Ausencias: un dato que falta se dice, con su origen; nunca se pinta como 0 ni se promedia. */
  function celda(valor) {
    if (valor === null || valor === undefined) { return 'sin datos'; }
    if (typeof valor === 'number' && !isFinite(valor)) { return 'sin datos'; }
    return String(valor);
  }
  function textoAusencia(info) {
    var origen = info && info.origen ? ' (origen: ' + info.origen + ')' : '';
    if (info && info.estado === 'parcial') {
      return 'Parcial: ' + info.presentes + ' de ' + info.total + origen;
    }
    return 'Sin datos' + origen;
  }
  function renderAusencia(padre, info) {
    var nodo = raiz.document.createElement('p');
    nodo.className = 'ausencia';
    nodo.setAttribute('role', 'status');
    nodo.textContent = textoAusencia(info);
    padre.appendChild(nodo);
    return nodo;
  }

  var Nucleo = { iniciarMenu: iniciarMenu, celda: celda, textoAusencia: textoAusencia, renderAusencia: renderAusencia };
  raiz.PanelCore = Nucleo;
  if (typeof module === 'object' && module.exports) { module.exports = Nucleo; }

  if (raiz.document && raiz.document.readyState === 'loading') {
    raiz.document.addEventListener('DOMContentLoaded', iniciarMenu);
  } else if (raiz.document && !(typeof module === 'object' && module.exports)) {
    iniciarMenu();
  }
})(typeof window !== 'undefined' ? window : globalThis);
