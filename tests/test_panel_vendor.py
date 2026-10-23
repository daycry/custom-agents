"""Chart.js incluido en el panel: un único fichero, sin modificar, con licencia y procedencia (panel-redesign T-02, CA-36).

El fichero se extrajo UNA vez, en desarrollo, del tarball oficial de npm verificando su integridad
`sha512`; ningún script del plugin lo descarga en ejecución ni al generar. Este test es la huella:
recalcula el SHA-256 y falla si el fichero, su procedencia o su licencia no cuadran.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / 'skills/plugin-panel/assets/vendor/chart.js'
FICHERO = VENDOR / 'chart.umd.min.js'
LICENCIA = VENDOR / 'LICENSE.md'
PROCEDENCIA = VENDOR / 'PROVENANCE.json'

# Huella revisada (design.md §2.4 I-01). Cambiar de versión es una decisión, no un refresco: exige
# nueva extracción verificada, PROVENANCE.json nuevo y actualizar estas tres constantes en el mismo cambio.
VERSION = '4.5.1'
SHA256 = '48444a82d4edcb5bec0f1965faacdde18d9c17db3063d042abada2f705c9f54a'
TAMANO = 208522
INTEGRIDAD_NPM = 'sha512-GIjfiT9dbmHRiYi6Nl2yFCq7kkwdkp1W/lp2J99rX0yo9tgJGn3lKQATztIjb5tVtevcBtIdICNWqlq5+E8/Pw=='
TARBALL = 'https://registry.npmjs.org/chart.js/-/chart.js-4.5.1.tgz'

CLAVES = {'name', 'version', 'file', 'source', 'tarball', 'tarball_member', 'npm_integrity', 'sha256',
          'size_bytes', 'license', 'license_file', 'license_sha256', 'extracted_on', 'modified', 'note'}
# Directorios que no forman parte del plugin (entornos, cachés, papelera local, salidas de pruebas).
NO_PLUGIN = {'.git', 'node_modules', '.venv', 'venv', '__pycache__', '.pytest_cache', '_to_delete',
             'scratchpad', 'test-results', 'dist'}
NOMBRE_CHARTJS = re.compile(r'^chart(?:\.umd)?(?:\.min)?\.(?:m|c)?js$', re.I)
CABECERA_CHARTJS = re.compile(rb'^\s*\*\s*Chart\.js v\d', re.M)


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _procedencia():
    return json.loads(PROCEDENCIA.read_text(encoding='utf-8'))


def _ficheros_del_plugin():
    """Ficheros versionables del árbol: con git, los que git ve (seguidos + no ignorados); sin git
    (plugin desempaquetado), un recorrido que salta lo que no es plugin."""
    git = shutil.which('git')
    if git and (ROOT / '.git').exists():
        salida = subprocess.run([git, '-c', 'core.quotepath=false', 'ls-files', '-z', '--cached', '--others',
                                 '--exclude-standard'], cwd=ROOT, capture_output=True, check=True).stdout
        return sorted({ROOT / rel for rel in salida.decode('utf-8').split('\0') if rel and (ROOT / rel).is_file()})
    out = []
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in NO_PLUGIN]
        out += [Path(base, f) for f in files]
    return sorted(out)


def test_fichero_identico_al_publicado_en_npm():
    assert FICHERO.is_file(), 'falta skills/plugin-panel/assets/vendor/chart.js/chart.umd.min.js'
    datos = FICHERO.read_bytes()
    assert len(datos) == TAMANO
    assert hashlib.sha256(datos).hexdigest() == SHA256
    assert datos.startswith(b'/*!\n * Chart.js v' + VERSION.encode() + b'\n'), 'cabecera de versión distinta'
    assert b'\r' not in datos, 'conversión de fin de línea: el fichero ya no es el publicado'


def test_procedencia_completa_y_coherente_con_el_fichero():
    datos = _procedencia()
    assert set(datos) == CLAVES, sorted(set(datos) ^ CLAVES)
    assert datos['name'] == 'chart.js' and datos['version'] == VERSION
    assert datos['file'] == 'chart.umd.min.js' and datos['tarball_member'] == 'package/dist/chart.umd.min.js'
    assert datos['tarball'] == TARBALL and datos['source'] == 'npm'
    assert datos['npm_integrity'] == INTEGRIDAD_NPM
    assert datos['sha256'] == _sha256(FICHERO) == SHA256, 'el SHA-256 recalculado no coincide con PROVENANCE.json'
    assert datos['size_bytes'] == FICHERO.stat().st_size == TAMANO
    assert datos['license'] == 'MIT' and datos['license_file'] == 'LICENSE.md'
    assert datos['license_sha256'] == _sha256(LICENCIA)
    assert re.fullmatch(r'\d{4}-\d{2}-\d{2}', datos['extracted_on'])
    assert datos['modified'] is False


def test_licencia_mit_de_chartjs_junto_al_fichero():
    texto = LICENCIA.read_text(encoding='utf-8')
    assert texto.startswith('The MIT License (MIT)')
    assert 'Copyright (c) 2014-2024 Chart.js Contributors' in texto
    assert 'The above copyright notice and this permission notice shall be included' in texto


def test_un_unico_chartjs_en_todo_el_plugin():
    por_nombre, por_cabecera = [], []
    for ruta in _ficheros_del_plugin():
        rel = ruta.relative_to(ROOT).as_posix()
        if NOMBRE_CHARTJS.match(ruta.name):
            por_nombre.append(rel)
        try:
            with ruta.open('rb') as handle:
                if CABECERA_CHARTJS.search(handle.read(1024)):
                    por_cabecera.append(rel)
        except OSError:
            continue
    esperado = [FICHERO.relative_to(ROOT).as_posix()]
    assert por_nombre == esperado, por_nombre
    assert por_cabecera == esperado, por_cabecera


def test_git_no_lo_ignora_ni_convierte_fines_de_linea():
    git = shutil.which('git')
    if not git or not (ROOT / '.git').exists():
        pytest.skip('sin git: plugin desempaquetado')
    rel = FICHERO.relative_to(ROOT).as_posix()
    ignorado = subprocess.run([git, 'check-ignore', '-q', rel], cwd=ROOT)
    assert ignorado.returncode == 1, '.gitignore ignora el Chart.js incluido (regla **/vendor/)'
    atributos = subprocess.run([git, 'check-attr', 'text', '--', rel], cwd=ROOT, capture_output=True,
                               encoding='utf-8', errors='replace', check=True).stdout
    assert atributos.strip().endswith('text: unset'), atributos


def test_ningun_script_del_panel_descarga_nada():
    """La extracción es un paso de desarrollo único: ni el generador ni el servidor citan un origen remoto."""
    # El servidor local cita su propio origen de loopback (`http://127.0.0.1:<puerto>`): eso no es red.
    # El espacio de nombres SVG del W3C es un identificador XML de `createElementNS`, no una URL que se descargue:
    # se excluye solo esa cadena exacta (cualquier otra ruta de www.w3.org sigue contando como origen remoto).
    remoto = re.compile(r'registry\.npmjs\.org|jsdelivr|unpkg|cdnjs|https?://(?!127\.0\.0\.1[:/]|localhost[:/]|www\.w3\.org/2000/svg\b)[A-Za-z0-9.-]+', re.I)
    panel = ROOT / 'skills/plugin-panel'
    for ruta in sorted(panel.rglob('*')):
        if not ruta.is_file() or ruta.suffix not in ('.py', '.js', '.mjs', '.html', '.css'):
            continue
        if VENDOR in ruta.parents:
            continue
        texto = ruta.read_text(encoding='utf-8', errors='replace')
        coincidencias = sorted({m.group(0) for m in remoto.finditer(texto)})
        assert not coincidencias, f'{ruta.relative_to(ROOT).as_posix()}: {coincidencias}'
