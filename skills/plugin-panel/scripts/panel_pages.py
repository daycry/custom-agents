#!/usr/bin/env python3
"""Plantilla común del panel multi-página: menú, cabecera de modo y escritura exportada.

Una sola plantilla sirve a las 7 páginas, en modo servido y exportado. Aquí no se lee el
inventario: las páginas reciben ya el contenido y los datos que deben mostrar.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001

MARKER = '<!doctype html><!-- custom-agents plugin-panel v1 -->'
ASSETS_DIR = Path(__file__).resolve().parents[1] / 'assets'
CHART_REL = 'vendor/chart.js/chart.umd.min.js'
MANIFEST = 'export-manifest.json'
GENERADOR = 'custom-agents plugin-panel'

# (slug, archivo, título): el orden es el del menú y no cambia entre páginas.
PAGES = (
    ('inicio', 'index.html', 'Inicio'),
    ('iniciativas', 'iniciativas.html', 'Iniciativas'),
    ('plan', 'plan.html', 'Plan'),
    ('agentes', 'agentes.html', 'Agentes en vivo'),
    ('memoria', 'memoria.html', 'Memoria'),
    ('catalogo', 'catalogo.html', 'Catálogo'),
    ('diagnostico', 'diagnostico.html', 'Diagnóstico'),
)

# Política decidida en el pico T-03: exportado = <meta>; servido = cabecera (la pone el servidor).
CSP_EXPORTADO = "default-src 'none'; script-src 'self' file:; style-src 'self' 'unsafe-inline'; img-src data:"
CSP_SERVIDO = ("default-src 'none'; style-src 'self' 'unsafe-inline'; script-src 'nonce-{nonce}'; img-src data:; "
               "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")

# Ficheros propios del panel que se copian a la carpeta exportada (ruta relativa a assets/).
ASSET_FILES = ('panel.css', 'panel-core.js', 'panel-charts.js')
VENDOR_FILES = ('vendor/chart.js/chart.umd.min.js', 'vendor/chart.js/LICENSE.md', 'vendor/chart.js/PROVENANCE.json')

_ESCAPES_JSON = {'<': '\\u003c', '>': '\\u003e', '&': '\\u0026', ' ': '\\u2028', ' ': '\\u2029'}


def _esc(texto):
    return (str(texto).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;'))


def json_seguro(valor):
    """JSON para incrustar en un <script type="application/json">: sin `<`, `>`, `&` ni separadores de línea."""
    texto = json.dumps(valor, ensure_ascii=False, sort_keys=True)
    for caracter, escape in _ESCAPES_JSON.items():
        texto = texto.replace(caracter, escape)
    return texto


def _nav(archivo_actual):
    items = []
    for _, archivo, titulo in PAGES:
        actual = ' aria-current="page"' if archivo == archivo_actual else ''
        items.append(f'<li><a href="{archivo}"{actual}>{_esc(titulo)}</a></li>')
    return '<nav id="panel-nav" aria-label="Secciones del panel"><ul>' + ''.join(items) + '</ul></nav>'


def _cabecera_modo(modo, generado):
    if modo == 'servido':
        return '<p class="modo" data-modo="servido">Servido en este equipo · los datos se actualizan mientras el servidor está activo</p>'
    return f'<p class="modo" data-modo="exportado">Instantánea del {_esc(generado)} · no se actualiza sola</p>'


def render_page(slug, *, modo, generado, datos, cuerpo='', chart_ok=True):
    """Devuelve el HTML de una página. `cuerpo` es HTML ya escapado por quien lo genera."""
    pagina = next((p for p in PAGES if p[0] == slug), None)
    if pagina is None:
        raise ValueError(f'página desconocida: {slug}')
    if modo not in ('servido', 'exportado'):
        raise ValueError(f'modo desconocido: {modo}')
    _, archivo, titulo = pagina
    csp = (f'<meta http-equiv="Content-Security-Policy" content="{CSP_EXPORTADO}">' if modo == 'exportado' else '')
    scripts = ''
    if chart_ok:
        scripts += f'<script src="{CHART_REL}"></script>'
    scripts += '<script src="assets/panel-core.js"></script><script src="assets/panel-charts.js"></script>'
    datos_pagina = {**datos, 'chartjs_disponible': bool(chart_ok)}
    return (MARKER + '<html lang="es"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">' + csp
            + f'<title>{_esc(titulo)} · Panel de custom-agents</title>'
            '<link rel="icon" href="data:,"><link rel="stylesheet" href="assets/panel.css"></head><body>'
            '<a class="skip-link" href="#main">Saltar al contenido</a>'
            '<header class="cabecera"><span class="marca">custom-agents</span>'
            '<button id="menu-toggle" type="button" aria-controls="panel-nav" aria-expanded="false" hidden>Menú</button>'
            + _cabecera_modo(modo, generado) + '</header>'
            + _nav(archivo)
            + f'<main id="main" tabindex="-1"><h1>{_esc(titulo)}</h1>{cuerpo}</main>'
            + f'<script type="application/json" id="panel-data">{json_seguro(datos_pagina)}</script>'
            + scripts + '</body></html>')


# --- Modo exportado -----------------------------------------------------------------------------

def _sha256(contenido):
    return hashlib.sha256(contenido).hexdigest()


def cargar_assets():
    """Lee los ficheros propios del panel. Devuelve (ficheros, chart_ok, avisos).

    Falta de un asset propio: ValueError opaco. Chart.js ausente o con huella distinta de la de
    PROVENANCE.json: se omite entero y las páginas degradan a tablas (chart_ok=False).
    """
    ficheros, avisos = {}, []
    try:
        for rel in ASSET_FILES:
            ficheros['assets/' + rel] = (ASSETS_DIR / rel).read_bytes()
    except OSError:
        raise ValueError('bundled panel asset unavailable') from None
    chart_ok = False
    try:
        vendor = {rel: (ASSETS_DIR / rel).read_bytes() for rel in VENDOR_FILES}
        esperado = json.loads(vendor['vendor/chart.js/PROVENANCE.json'].decode('utf8')).get('sha256')
        chart_ok = bool(esperado) and _sha256(vendor[CHART_REL]) == esperado
        if chart_ok:
            ficheros.update(vendor)
        else:
            avisos.append('Chart.js no coincide con la huella de PROVENANCE.json: las páginas muestran solo las tablas.')
    except (OSError, ValueError, UnicodeError):
        avisos.append('Falta el fichero de Chart.js o su procedencia: las páginas muestran solo las tablas.')
    return ficheros, chart_ok, avisos


def _datos_de_pagina(slug, datos):
    base = {'pagina': slug, 'contadores': datos.get('counts', {})}
    if slug == 'catalogo':
        base['inventario'] = datos
    return base


def construir_paginas(datos, *, generado, chart_ok):
    """HTML (bytes UTF-8) de las 7 páginas del modo exportado."""
    cuerpo = '<section><p>Esta página todavía no muestra contenido.</p></section>'
    return {archivo: render_page(slug, modo='exportado', generado=generado, chart_ok=chart_ok,
                                 datos=_datos_de_pagina(slug, datos), cuerpo=cuerpo).encode('utf8')
            for slug, archivo, _ in PAGES}


def _leer_manifiesto(ruta):
    """{ruta: sha256} del manifiesto previo; ValueError si existe y no es nuestro."""
    if not ruta.exists():
        return {}
    try:
        texto = json.loads(ruta.read_text(encoding='utf8'))
        if texto.get('generador') != GENERADOR:
            raise ValueError
        return {f['ruta']: f['sha256'] for f in texto['ficheros']}
    except (OSError, ValueError, UnicodeError, KeyError, TypeError, AttributeError):
        raise ValueError(f'output was not created by plugin-panel: {MANIFEST}') from None


def _escribir_atomico(ruta, contenido):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporal = tempfile.mkstemp(prefix='.plugin-panel-', dir=ruta.parent)
    try:
        with os.fdopen(descriptor, 'wb') as asa:
            asa.write(contenido)
        os.replace(temporal, ruta)
    finally:
        if os.path.exists(temporal):
            os.unlink(temporal)


def exportar_sitio(destino, datos, *, generado=None, unsafe_link=lambda ruta: ruta.is_symlink()):
    """Escribe las 7 páginas, `assets/`, `vendor/chart.js/` y `export-manifest.json` en `destino`.

    Solo sobrescribe HTML con MARKER o ficheros del manifiesto previo cuyo hash sea el que se escribió;
    cualquier otro choque aborta ANTES de escribir nada. Devuelve (rutas escritas, avisos).
    """
    destino = Path(destino).absolute()
    if generado is None:
        generado = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    ficheros, chart_ok, avisos = cargar_assets()
    ficheros.update(construir_paginas(datos, generado=generado, chart_ok=chart_ok))

    if unsafe_link(destino) or any(unsafe_link(p) for p in destino.absolute().parents):
        raise ValueError('output is a symbolic link')
    if destino.exists() and not destino.is_dir():
        raise ValueError('output is not a directory')
    previo = _leer_manifiesto(destino / MANIFEST)

    for rel, contenido in sorted(ficheros.items()):
        ruta = destino / rel
        padre = ruta.parent
        while padre != destino and destino in padre.parents:
            if unsafe_link(padre):
                raise ValueError('output is a symbolic link')
            padre = padre.parent
        if unsafe_link(ruta) or ruta.is_dir():
            raise ValueError(f'output was not created by plugin-panel: {rel}')
        if ruta.exists():
            actual = ruta.read_bytes()
            propio = (rel.endswith('.html') and actual.startswith(MARKER.encode('utf8'))) or previo.get(rel) == _sha256(actual)
            if not propio:
                raise ValueError(f'output was not created by plugin-panel: {rel}')

    for rel, contenido in sorted(ficheros.items()):
        _escribir_atomico(destino / rel, contenido)
    for rel, sha in previo.items():
        ruta = destino / rel
        if rel not in ficheros and ruta.is_file() and not unsafe_link(ruta) and _sha256(ruta.read_bytes()) == sha:
            ruta.unlink()
    manifiesto = {'generador': GENERADOR, 'version': 1, 'generado': generado,
                  'ficheros': [{'ruta': rel, 'sha256': _sha256(c), 'bytes': len(c)} for rel, c in sorted(ficheros.items())]}
    _escribir_atomico(destino / MANIFEST, (json.dumps(manifiesto, ensure_ascii=False, indent=2) + '\n').encode('utf8'))
    return sorted(ficheros), avisos


def main(argv=None):
    """`--list`: imprime las páginas del menú (slug, archivo y título) como JSON."""
    if list(sys.argv[1:] if argv is None else argv) != ['--list']:
        print('uso: panel_pages.py --list', file=sys.stderr)
        return 2
    print(json.dumps([{'slug': s, 'archivo': a, 'titulo': t} for s, a, t in PAGES], ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
