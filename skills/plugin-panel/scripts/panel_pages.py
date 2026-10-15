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
import re
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
ASSET_FILES = ('panel.css', 'panel-core.js', 'panel-charts.js', 'page-catalogo.js', 'page-diagnostico.js',
               'page-cartera.js', 'page-inicio.js', 'page-iniciativas.js', 'page-plan.js')
# Solo el modo servido los usa (consultan api/*); el exportado no los copia.
LIVE_ASSET_FILES = ('panel-live.js', 'panel-memory.js', 'panel-activity.js', 'panel-review.js')
# Script propio de cada página (después de panel-core.js y panel-charts.js), y los vivos del modo servido.
PAGE_SCRIPTS = {'catalogo': ('page-catalogo.js',), 'diagnostico': ('page-diagnostico.js',),
                'inicio': ('page-cartera.js', 'page-inicio.js'),
                'iniciativas': ('page-cartera.js', 'page-iniciativas.js')}
# La página Plan de UNA iniciativa (`plan-<id16>.html`): su kanban y su detalle de tarea. No lleva los JS vivos de
# `plan.html` (progreso y revisión), que dependen de secciones que solo tiene el índice.
PLAN_SCRIPTS = ('page-cartera.js', 'page-plan.js')
ID16_RE = re.compile(r'[a-f0-9]{16}')
LIVE_SCRIPTS = {'inicio': ('panel-live.js',), 'plan': ('panel-live.js', 'panel-review.js'),
                'agentes': ('panel-activity.js',), 'memoria': ('panel-memory.js',)}
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
    return (f'<p class="modo" data-modo="exportado">Copia estática del {_esc(generado)} · para verla en vivo, '
            'abre el panel servido con <code>/plugin-catalog --serve</code></p>')


def render_page(slug, *, modo, generado, datos, cuerpo='', chart_ok=True, nonce=None, scripts_omitidos=(),
                plan_id=None):
    """Devuelve el HTML de una página. `cuerpo` es HTML ya escapado por quien lo genera.

    `nonce` (modo servido) va en TODAS las etiquetas `<script …>` que se generan aquí; los scripts
    son siempre ficheros (`src=`) y los datos viajan en un bloque `application/json`.
    `scripts_omitidos` quita scripts por nombre (p. ej. la revisión cuando no está activa).
    `plan_id` (solo con `slug == 'plan'`): es la página Plan de UNA iniciativa, `plan-<id16>.html`; el menú sigue
    marcando «Plan» y sus scripts son `PLAN_SCRIPTS`, no los de la vista viva del índice.
    """
    pagina = next((p for p in PAGES if p[0] == slug), None)
    if pagina is None:
        raise ValueError(f'página desconocida: {slug}')
    if modo not in ('servido', 'exportado'):
        raise ValueError(f'modo desconocido: {modo}')
    _, archivo, titulo = pagina
    csp = (f'<meta http-equiv="Content-Security-Policy" content="{CSP_EXPORTADO}">' if modo == 'exportado' else '')
    atributo = f' nonce="{_esc(nonce)}"' if nonce else ''

    def script(ruta):
        return f'<script{atributo} src="{ruta}"></script>'
    scripts = script(CHART_REL) if chart_ok else ''
    scripts += script('assets/panel-core.js') + script('assets/panel-charts.js')
    if plan_id is not None:
        if slug != 'plan' or not ID16_RE.fullmatch(plan_id):
            raise ValueError('plan_id solo para la página Plan y con la forma de un id16')
        propios = PLAN_SCRIPTS
    else:
        propios = PAGE_SCRIPTS.get(slug, ()) + (LIVE_SCRIPTS.get(slug, ()) if modo == 'servido' else ())
    scripts += ''.join(script('assets/' + nombre) for nombre in propios if nombre not in scripts_omitidos)
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
            + f'<script{atributo} type="application/json" id="panel-data">{json_seguro(datos_pagina)}</script>'
            + scripts + '</body></html>')


# --- Modo exportado -----------------------------------------------------------------------------

def _sha256(contenido):
    return hashlib.sha256(contenido).hexdigest()


def cargar_assets(modo='exportado', review=False):
    """Lee los ficheros propios del panel. Devuelve (ficheros, chart_ok, avisos).

    Falta de un asset propio: ValueError opaco. Chart.js ausente o con huella distinta de la de
    PROVENANCE.json: se omite entero y las páginas degradan a tablas (chart_ok=False).
    Con `modo='servido'` suma los JS vivos: progreso y memoria son obligatorios (ValueError opaco), la
    revisión solo si `review` y la actividad degrada (la página lo dice) si falta.
    """
    ficheros, avisos = {}, []
    try:
        for rel in ASSET_FILES:
            ficheros['assets/' + rel] = (ASSETS_DIR / rel).read_bytes()
    except OSError:
        raise ValueError('bundled panel asset unavailable') from None
    if modo == 'servido':
        for rel in LIVE_ASSET_FILES:
            try:
                ficheros['assets/' + rel] = (ASSETS_DIR / rel).read_bytes()
            except OSError:
                if rel in ('panel-live.js', 'panel-memory.js'):
                    raise ValueError('bundled live panel asset unavailable') from None
                if rel == 'panel-review.js' and review:
                    raise ValueError('bundled review panel asset unavailable') from None
        if not review:
            ficheros.pop('assets/panel-review.js', None)
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


CARTERA_PAGES = ('inicio', 'iniciativas')


def datos_de_pagina(slug, datos, modo='exportado', cartera=None, plan_id=None):
    """Bloque `panel-data` de una página. El inventario completo y la cartera (ya anonimizados) solo viajan en
    la copia exportada; el modo servido lleva los contadores y consulta el resto por `api/*`. `modo` viaja
    en el bloque para que el JS de la página sepa si debe preguntar al servidor o leer lo incrustado; sin
    `cartera` (exportado sin `--project`) la clave no existe y la página dice que no hay datos. `plan_id` (página
    Plan de una iniciativa) viaja en el bloque para que el JS sepa qué plan pide a `api/plan-<id16>` o lee de lo
    incrustado (`plan`, `detalles`: los añade quien exporta)."""
    base = {'pagina': slug, 'modo': modo, 'contadores': datos.get('counts', {})}
    if plan_id is not None:
        base['plan_id'] = plan_id
    if slug == 'catalogo' and modo == 'exportado':
        base['inventario'] = datos
    if slug in CARTERA_PAGES and modo == 'exportado' and cartera is not None:
        base['cartera'] = cartera
    return base


PLACEHOLDER = '<section><p>Esta página todavía no muestra contenido.</p></section>'


def construir_paginas(datos, *, generado, chart_ok, cuerpos=None, cartera=None):
    """HTML (bytes UTF-8) de las 7 páginas del modo exportado. `cuerpos`: {slug: HTML} ya escapado."""
    cuerpos = cuerpos or {}
    return {archivo: render_page(slug, modo='exportado', generado=generado, chart_ok=chart_ok,
                                 datos=datos_de_pagina(slug, datos, cartera=cartera),
                                 cuerpo=cuerpos.get(slug, PLACEHOLDER),
                                 scripts_omitidos=('panel-review.js',)).encode('utf8')
            for slug, archivo, _ in PAGES}


_SHA256_RE = re.compile(r'[0-9a-f]{64}')
_UNIDAD_RE = re.compile(r'^[A-Za-z]:')
_PROHIBIDOS_EN_RUTA = ('\\', ':', '\x00')
# Patron de nombre corto 8.3 de Windows (`CHARTU~1.JS`): el sistema lo trata como alias del fichero largo.
_NOMBRE_CORTO_RE = re.compile(r'~[0-9]')


def _ruta_manifiesto_valida(rel):
    """Ruta relativa POSIX y sin trucos: sin barra invertida, unidad, raíz, `:`, NUL ni componentes `.`, `..` o vacíos."""
    if not isinstance(rel, str) or not rel or rel.startswith('/') or any(c in rel for c in _PROHIBIDOS_EN_RUTA):
        return False
    partes = rel.split('/')
    # Win32 recorta el punto y el espacio finales de un componente: `chart.umd.min.js.` ES `chart.umd.min.js`.
    return not _UNIDAD_RE.match(rel) and all(
        parte not in ('', '.', '..') and parte == parte.rstrip(' .') and not _NOMBRE_CORTO_RE.search(parte)
        for parte in partes)


def _clave_fs(rel):
    """Nombre tal como lo compara el sistema de ficheros (sin distinguir mayúsculas, sin punto/espacio final)."""
    return '/'.join(parte.casefold().rstrip(' .') for parte in rel.split('/'))


def _borrar_si_es_nuestro(destino, raiz, rel, sha, unsafe_link, escritos_resueltos=frozenset()):
    """Borra `destino/rel` solo si, AHORA, ningún componente es enlace, la ruta resuelta sigue dentro del
    destino y el contenido es el que escribimos. Se repite justo antes del `unlink` porque la validación
    del manifiesto es anterior a la escritura (CWE-367): un padre cambiado por un enlace entre medias no
    puede sacar el borrado del destino."""
    ruta = destino / rel
    try:
        for padre in ruta.parents:
            if padre == destino:
                break
            if unsafe_link(padre):
                return False
        if unsafe_link(ruta) or not ruta.is_file():
            return False
        resuelta = ruta.resolve()  # en Windows expande un alias 8.3 al nombre largo
        resuelta.relative_to(raiz)
        if resuelta in escritos_resueltos:
            return False  # es un fichero que acabamos de escribir con otro nombre: no se toca
        if _sha256(ruta.read_bytes()) != sha:
            return False
        ruta.unlink()
    except (OSError, ValueError):
        return False
    return True


def _leer_manifiesto(ruta, destino, unsafe_link):
    """{ruta: sha256} del manifiesto previo; ValueError si existe y no es nuestro o si una entrada no es
    segura (CWE-22: el manifiesto guía un `unlink`, así que no es de fiar). Una entrada inválida ABORTA
    antes de escribir o borrar nada: o el manifiesto está corrupto o es hostil, y en ambos casos no se
    limpia a ciegas; el mensaje no lleva rutas."""
    if not ruta.exists():
        return {}
    try:
        texto = json.loads(ruta.read_text(encoding='utf8'))
        if texto.get('generador') != GENERADOR:
            raise ValueError
        previo = {f['ruta']: f['sha256'] for f in texto['ficheros']}
    except (OSError, ValueError, UnicodeError, KeyError, TypeError, AttributeError):
        raise ValueError(f'output was not created by plugin-panel: {MANIFEST}') from None
    raiz = destino.resolve()
    for rel, sha in previo.items():
        if not _ruta_manifiesto_valida(rel) or not isinstance(sha, str) or not _SHA256_RE.fullmatch(sha):
            raise ValueError(f'output manifest has an unsafe entry: {MANIFEST}')
        completa = destino / rel
        try:
            completa.resolve().relative_to(raiz)
        except (OSError, ValueError):
            raise ValueError(f'output manifest has an unsafe entry: {MANIFEST}') from None
        for padre in completa.parents:
            if padre == destino:
                break
            if unsafe_link(padre):
                raise ValueError('output is a symbolic link')
    return previo


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


def exportar_sitio(destino, datos, *, generado=None, unsafe_link=lambda ruta: ruta.is_symlink(), cuerpos=None,
                   cartera=None, planes=None):
    """Escribe las 7 páginas, una `plan-<id16>.html` por cada plan de `planes` (`[{'id', 'cuerpo', 'datos'}]`),
    `assets/`, `vendor/chart.js/` y `export-manifest.json` en `destino`.

    Solo sobrescribe HTML con MARKER o ficheros del manifiesto previo cuyo hash sea el que se escribió;
    cualquier otro choque aborta ANTES de escribir nada. Devuelve (rutas escritas, avisos).
    """
    destino = Path(destino).absolute()
    if generado is None:
        generado = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    ficheros, chart_ok, avisos = cargar_assets()
    ficheros.update(construir_paginas(datos, generado=generado, chart_ok=chart_ok, cuerpos=cuerpos, cartera=cartera))
    for plan in planes or ():
        if not isinstance(plan.get('id'), str) or not ID16_RE.fullmatch(plan['id']):
            raise ValueError('plan id is not an id16')
        ficheros[f"plan-{plan['id']}.html"] = render_page(
            'plan', modo='exportado', generado=generado, chart_ok=chart_ok, plan_id=plan['id'], cuerpo=plan['cuerpo'],
            datos={**datos_de_pagina('plan', datos, plan_id=plan['id']), **plan['datos']}).encode('utf8')

    if unsafe_link(destino) or any(unsafe_link(p) for p in destino.absolute().parents):
        raise ValueError('output is a symbolic link')
    if destino.exists() and not destino.is_dir():
        raise ValueError('output is not a directory')
    if not destino.exists() and not destino.parent.is_dir():
        raise ValueError('output parent directory does not exist')
    previo = _leer_manifiesto(destino / MANIFEST, destino, unsafe_link)

    for rel, contenido in sorted(ficheros.items()):
        ruta = destino / rel
        padre = ruta.parent
        while padre != destino and destino in padre.parents:
            if unsafe_link(padre):
                raise ValueError('output is a symbolic link')
            if padre.exists() and not padre.is_dir():
                raise ValueError(f'output was not created by plugin-panel: {rel}')
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
    escritos = {_clave_fs(rel) for rel in ficheros}
    raiz = destino.resolve()
    resueltos = {(destino / rel).resolve() for rel in ficheros}
    for rel, sha in previo.items():
        if rel not in ficheros and _clave_fs(rel) not in escritos:
            _borrar_si_es_nuestro(destino, raiz, rel, sha, unsafe_link, resueltos)
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
