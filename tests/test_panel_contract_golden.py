"""Goldens de los contratos que el rediseño del panel NO puede cambiar (panel-redesign T-01).

Fija la salida de tres contratos sobre fixtures propias (nunca sobre el repo real):

- ``build_dashboard.py --json``  → ``golden/dashboard.json``  (lo consumen /roadmap-metrics y /pm-backlog)
- ``build_dashboard.py --md``    → ``golden/dashboard.md``    (la página de Confluence de /roadmap-status)
- ``build_panel.py --json``      → ``golden/panel.json``      (CA-28: catálogo, extensiones, hooks, workflow)

La comparación es BYTE A BYTE tras una normalización EXPLÍCITA y cerrada (``NORMALIZACION``). Cada
regla dice qué campo es volátil y por qué; ningún fichero se excluye. Si un cambio legítimo altera un
golden (está previsto UNA vez, en T-51, por los registros de hook nuevos), se regenera con
``PANEL_GOLDEN_UPDATE=1`` y el diff del golden se revisa en la revisión de la fase.

Los generadores corren sobre una COPIA materializada de la fixture (``materializar``), no sobre el
árbol versionado: la iniciativa ilegible necesita bytes no UTF-8, y un ``.md`` así versionado rompe a
los lectores del repo que recorren todo ``.md`` en UTF-8 estricto (p. ej. ``test_review_jira_owner``).
Las fases siguientes que usen esta fixture deben materializarla igual (importando este módulo).
"""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/panel-redesign'
GOLDEN = FIXTURE / 'golden'
# Iniciativa ilegible: spec sin frontmatter y con bytes que no son UTF-8 (solo existen en la copia).
ILEGIBLE = ('roadmap/2026-01-13-delta/spec.md', b'cabecera rota sin frontmatter \x80\x81\n# Delta \xe9 ilegible\n')


def materializar(destino):
    """Copia `roadmap/`, `bundle/`, `project/` y `home/` de la fixture en `destino` y escribe los
    bytes no UTF-8 de la iniciativa ilegible. Devuelve `destino`."""
    destino = Path(destino)
    for parte in ('roadmap', 'bundle', 'project', 'home'):
        shutil.copytree(FIXTURE / parte, destino / parte)
    (destino / ILEGIBLE[0]).write_bytes(ILEGIBLE[1])
    return destino


@pytest.fixture(scope='module')
def copia(tmp_path_factory):
    return materializar(tmp_path_factory.mktemp('panel-redesign'))
DASHBOARD = ROOT / 'skills/roadmap-dashboard/scripts/build_dashboard.py'
PANEL = ROOT / 'skills/plugin-panel/scripts/build_panel.py'

# Normalización declarada. Es la ÚNICA tolerancia del test; añadir una regla exige justificarla aquí.
NORMALIZACION = (
    # 1. Fin de línea de la plataforma: en Windows, stdout y `open(..., "w")` en modo texto
    #    escriben CRLF. El contrato es el contenido, no la traducción de newline del SO.
    ('fin de línea', re.compile(r'\r\n'), '\n'),
    # 2. `dashboard.md` lleva la hora de generación (`datetime.now()`, build_dashboard.py:638).
    ('fecha de generación del dashboard.md',
     re.compile(r'(> Generado automáticamente el \*\*)\d{4}-\d{2}-\d{2} \d{2}:\d{2}(\*\*)'), r'\1<fecha>\2'),
    # 3. `path` de cada iniciativa es `os.path.join(root, slug)`: separador `\` en Windows.
    ('separador del campo path', re.compile(r'("path": "roadmap)\\\\'), r'\1/'),
)


def _normalizar(texto, extra=()):
    for _nombre, patron, sustituto in NORMALIZACION:
        texto = patron.sub(sustituto, texto)
    for viejo, nuevo in extra:
        texto = texto.replace(viejo, nuevo)
    return texto


def _ids_de_usuario(texto):
    """4. Ids derivados de la ruta ABSOLUTA de la raíz de usuario (`project-pieces.py:505`, hash de
    `normcase(base)`): cambian con la máquina y la carpeta del checkout. Se sustituyen por marcadores
    estables en orden de aparición; los ids de proyecto (ruta relativa) se comparan tal cual."""
    datos = json.loads(texto)
    extra, raices, piezas = [], {}, {}
    for pieza in datos.get('extensions', {}).get('pieces', []):
        if pieza.get('scope') != 'user':
            continue
        raiz = pieza['root_id']
        raices.setdefault(raiz, f'user-<raiz-{len(raices) + 1}>')
        piezas.setdefault(pieza['id'], f'ext-<usuario-{len(piezas) + 1}>')
    extra += sorted(raices.items()) + sorted(piezas.items())
    return extra


def _run(cwd, script, *args):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8')
    result = subprocess.run([sys.executable, str(script), *args], capture_output=True, env=env, cwd=cwd)
    assert result.returncode == 0, result.stderr.decode('utf-8', 'replace')
    return result.stdout.decode('utf-8')


def _comparar(nombre, actual):
    golden = GOLDEN / nombre
    if os.environ.get('PANEL_GOLDEN_UPDATE') == '1':
        GOLDEN.mkdir(exist_ok=True)
        golden.write_bytes(actual.encode('utf-8'))
    assert golden.is_file(), f'golden ausente: {golden.relative_to(ROOT).as_posix()} (PANEL_GOLDEN_UPDATE=1 lo crea)'
    esperado = golden.read_bytes()
    assert actual.encode('utf-8') == esperado, (
        f'{nombre} cambió respecto a su golden: el contrato no puede cambiar en el rediseño (CA-28)')


def test_dashboard_json_igual_a_su_golden(copia):
    _comparar('dashboard.json', _normalizar(_run(copia, DASHBOARD, '--root', 'roadmap', '--json')))


def test_dashboard_md_igual_a_su_golden(copia, tmp_path):
    destino = tmp_path / 'dashboard.md'
    _run(copia, DASHBOARD, '--root', 'roadmap', '--md', str(destino))
    _comparar('dashboard.md', _normalizar(destino.read_bytes().decode('utf-8')))


def test_panel_json_igual_a_su_golden(copia):
    salida = _run(copia, PANEL, '--root', 'bundle', '--project', 'project', '--home', 'home', '--json')
    _comparar('panel.json', _normalizar(salida, _ids_de_usuario(salida)))


def test_la_fixture_cubre_los_casos_que_la_spec_exige_despues(copia):
    """La red solo vale si la fixture tiene los casos que las fases siguientes van a leer."""
    roadmap = copia / 'roadmap'
    datos = json.loads(_normalizar(_run(copia, DASHBOARD, '--root', 'roadmap', '--json')))
    por_slug = {r['slug']: r for r in datos}
    estados = {r['spec_estado'] for r in datos}
    assert {'borrador', 'aprobada', 'implementada', 'obsoleta', None} <= estados, estados
    ilegible = roadmap / '2026-01-13-delta/spec.md'
    with pytest.raises(UnicodeDecodeError):
        ilegible.read_bytes().decode('utf-8')
    grande = roadmap / '2026-01-14-epsilon/tasks.md'
    assert grande.stat().st_size > 256 * 1024
    assert any(r['generacion'] is None for r in datos), 'falta una iniciativa sin generacion:'
    gamma = por_slug['2026-01-12-gamma']['progreso']
    assert gamma['ia'][0] is None and gamma['humanas'][0] is None, 'falta un ledger sin real («—»)'
    assert '| Important |' in (roadmap / '2026-01-10-alfa/tasks.md').read_text(encoding='utf-8')
    assert (roadmap / '2026-01-12-gamma/execution-history.md').is_file()
    assert por_slug['2026-01-14-epsilon']['via_rapida'] is True
    assert 'notas' not in por_slug, 'una carpeta sin artefactos no es iniciativa'


def test_la_fixture_no_lleva_datos_personales():
    """CA-41: ni rutas del home, ni usuario del sistema, ni correos reales en fixtures ni goldens."""
    prohibidos = [str(Path.home()), Path.home().as_posix(), str(ROOT), ROOT.as_posix()]
    usuario = os.environ.get('USERNAME') or os.environ.get('USER') or ''
    # Cuentas genéricas de CI/contenedor: no identifican a nadie y casarían con palabras corrientes.
    usuario_re = (re.compile(r'(?<!\w)' + re.escape(usuario) + r'(?!\w)', re.I)
                  if usuario and usuario.lower() not in ('root', 'runner', 'user') else None)
    correo = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')
    for ruta in sorted(p for p in FIXTURE.rglob('*') if p.is_file()):
        texto = ruta.read_bytes().decode('utf-8', 'replace')
        rel = ruta.relative_to(ROOT).as_posix()
        for valor in prohibidos:
            assert valor.lower() not in texto.lower(), f'{rel}: ruta local'
        if usuario_re:
            assert not usuario_re.search(texto), f'{rel}: usuario del sistema'
        assert not correo.search(texto), f'{rel}: correo'


def test_el_arbol_versionado_solo_lleva_utf8_valido():
    """Los bytes no UTF-8 viven solo en la copia materializada: versionados en un `.md`, romperían
    a los lectores que recorren todo el repo en UTF-8 estricto."""
    for ruta in sorted(p for p in FIXTURE.rglob('*') if p.is_file()):
        ruta.read_bytes().decode('utf-8')
