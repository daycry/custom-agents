"""T-08: modo exportado `--export <dir>` con manifiesto propio (retira `--html`)."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SCRIPT = RAIZ / 'skills/plugin-panel/scripts/build_panel.py'
ASSETS = RAIZ / 'skills/plugin-panel/assets'
PAGINAS = ['index.html', 'iniciativas.html', 'plan.html', 'agentes.html', 'memoria.html', 'catalogo.html', 'diagnostico.html']
USUARIO = 'jdoeuser'
CORREO = 'jdoe@example.org'


@pytest.fixture
def panel():
    spec = importlib.util.spec_from_file_location('panel_export_under_test', SCRIPT)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _escribir(raiz, ruta, texto):
    destino = raiz / ruta
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(texto, encoding='utf8')


@pytest.fixture
def entorno(tmp_path, monkeypatch):
    home = tmp_path / 'hogar'
    home.mkdir()
    for variable in ('HOME', 'USERPROFILE'):
        monkeypatch.setenv(variable, str(home))
    for variable in ('USERNAME', 'USER', 'LOGNAME', 'LNAME'):
        monkeypatch.setenv(variable, USUARIO)
    return home


@pytest.fixture
def bundle(tmp_path, entorno):
    raiz = tmp_path / 'bundle'
    ruta_home = str(entorno).replace('\\', '/')
    _escribir(raiz, 'agents/demo.md', '---\nname: demo\ndescription: >\n  Revisa en ' + ruta_home + '/proyectos/x y avisa a '
              + CORREO + ' (cuenta ' + USUARIO + ').\nmodel: sonnet\ntools: Read\n---\ncuerpo privado')
    _escribir(raiz, 'skills/example/SKILL.md', '---\nname: example\ndescription: Consulta de ejemplo.\n---\nx')
    _escribir(raiz, 'commands/demo.md', '---\ndescription: Consulta del catálogo.\n---\n$ARGUMENTS')
    return raiz


def _exportar(panel, bundle, destino, *extra):
    return panel.main(['--root', str(bundle), '--export', str(destino), *extra])


def _sha(ruta):
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


def test_la_exportacion_escribe_siete_paginas_assets_vendor_y_manifiesto(panel, bundle, tmp_path):
    destino = tmp_path / 'salida'
    assert _exportar(panel, bundle, destino) == 0
    for pagina in PAGINAS:
        assert (destino / pagina).read_text(encoding='utf8').startswith(panel.MARKER)
    for ruta in ('assets/panel.css', 'assets/panel-core.js', 'assets/panel-charts.js',
                 'assets/page-catalogo.js', 'assets/page-diagnostico.js', 'vendor/chart.js/chart.umd.min.js', 'vendor/chart.js/LICENSE.md', 'vendor/chart.js/PROVENANCE.json'):
        assert (destino / ruta).is_file(), ruta
    manifiesto = json.loads((destino / 'export-manifest.json').read_text(encoding='utf8'))
    assert manifiesto['generador'] == 'custom-agents plugin-panel' and manifiesto['generado']
    rutas = {f['ruta']: f for f in manifiesto['ficheros']}
    assert set(rutas) == set(PAGINAS) | {'assets/panel.css', 'assets/panel-core.js', 'assets/panel-charts.js',
                                          'assets/page-catalogo.js', 'assets/page-diagnostico.js',
                                          'assets/page-cartera.js', 'assets/page-inicio.js', 'assets/page-iniciativas.js',
                                          'assets/page-plan.js', 'vendor/chart.js/chart.umd.min.js', 'vendor/chart.js/LICENSE.md',
                                          'vendor/chart.js/PROVENANCE.json'}
    for ruta, ficha in rutas.items():
        assert ficha['sha256'] == _sha(destino / ruta) and ficha['bytes'] == (destino / ruta).stat().st_size
    assert rutas['vendor/chart.js/chart.umd.min.js']['sha256'] == '48444a82d4edcb5bec0f1965faacdde18d9c17db3063d042abada2f705c9f54a'


def test_ningun_html_pide_recursos_externos(panel, bundle, tmp_path):
    destino = tmp_path / 'salida'
    assert _exportar(panel, bundle, destino) == 0
    for pagina in PAGINAS:
        html = (destino / pagina).read_text(encoding='utf8')
        assert not re.search(r'(?:src|href|action)\s*=\s*["\']\s*(?:https?:)?//', html, re.I), pagina
        assert 'unsafe-eval' not in html


def test_sin_datos_personales_en_ningun_fichero_exportado(panel, bundle, tmp_path, entorno):
    destino = tmp_path / 'salida'
    assert _exportar(panel, bundle, destino, '--project', str(bundle), '--home', str(entorno)) == 0
    sensibles = [USUARIO, CORREO, str(entorno), str(entorno).replace('\\', '/'), str(bundle), str(bundle).replace('\\', '/')]
    for ruta in destino.rglob('*'):
        if not ruta.is_file() or 'vendor' in ruta.parts:
            continue
        texto = ruta.read_text(encoding='utf8', errors='replace')
        for sensible in sensibles:
            assert sensible.lower() not in texto.lower(), f'{sensible!r} en {ruta.name}'
    catalogo = (destino / 'catalogo.html').read_text(encoding='utf8')
    assert '&lt;correo&gt;' in catalogo or '\\u003ccorreo\\u003e' in catalogo


def test_reexportar_es_idempotente_y_conserva_lo_ajeno(panel, bundle, tmp_path):
    destino = tmp_path / 'salida'
    assert _exportar(panel, bundle, destino) == 0
    (destino / 'notas.txt').write_text('mías', encoding='utf8')
    assert _exportar(panel, bundle, destino) == 0
    assert (destino / 'notas.txt').read_text(encoding='utf8') == 'mías'
    manifiesto = json.loads((destino / 'export-manifest.json').read_text(encoding='utf8'))
    assert 'notas.txt' not in {f['ruta'] for f in manifiesto['ficheros']}


@pytest.mark.parametrize('ajeno', ['index.html', 'catalogo.html', 'assets/panel.css', 'export-manifest.json'])
def test_un_fichero_ajeno_no_se_sobrescribe_y_no_se_escribe_nada(panel, bundle, tmp_path, capsys, ajeno):
    destino = tmp_path / 'salida'
    _escribir(destino, ajeno, 'CONTENIDO DEL USUARIO')
    assert _exportar(panel, bundle, destino) == 2
    assert (destino / ajeno).read_text(encoding='utf8') == 'CONTENIDO DEL USUARIO'
    assert 'not created by plugin-panel' in capsys.readouterr().err
    escritos = {p.relative_to(destino).as_posix() for p in destino.rglob('*') if p.is_file()}
    assert escritos == {ajeno}, 'una exportación rechazada no deja ficheros a medias'


def test_un_asset_propio_modificado_por_el_usuario_no_se_pisa(panel, bundle, tmp_path):
    destino = tmp_path / 'salida'
    assert _exportar(panel, bundle, destino) == 0
    (destino / 'assets/panel.css').write_text('/* mi tema */', encoding='utf8')
    assert _exportar(panel, bundle, destino) == 2
    assert (destino / 'assets/panel.css').read_text(encoding='utf8') == '/* mi tema */'


def test_un_asset_propio_intacto_se_actualiza(panel, bundle, tmp_path):
    destino = tmp_path / 'salida'
    assert _exportar(panel, bundle, destino) == 0
    (destino / 'assets/panel.css').write_bytes((ASSETS / 'panel.css').read_bytes())
    assert _exportar(panel, bundle, destino) == 0


def test_un_fichero_listado_que_ya_no_se_genera_se_retira_si_sigue_igual(panel, bundle, tmp_path):
    destino = tmp_path / 'salida'
    assert _exportar(panel, bundle, destino) == 0
    viejo = destino / 'plan-0123456789abcdef.html'
    viejo.write_bytes((panel.MARKER + '<html></html>').encode('utf8'))
    editado = destino / 'plan-aaaaaaaaaaaaaaaa.html'
    editado.write_bytes(b'editado por el usuario')
    ruta_manifiesto = destino / 'export-manifest.json'
    manifiesto = json.loads(ruta_manifiesto.read_text(encoding='utf8'))
    manifiesto['ficheros'] += [{'ruta': 'plan-0123456789abcdef.html', 'sha256': _sha(viejo), 'bytes': viejo.stat().st_size},
                               {'ruta': 'plan-aaaaaaaaaaaaaaaa.html', 'sha256': '0' * 64, 'bytes': 1}]
    ruta_manifiesto.write_text(json.dumps(manifiesto), encoding='utf8')
    assert _exportar(panel, bundle, destino) == 0
    assert not viejo.exists()
    assert editado.read_bytes() == b'editado por el usuario'
    nuevo = json.loads(ruta_manifiesto.read_text(encoding='utf8'))
    assert 'plan-0123456789abcdef.html' not in {f['ruta'] for f in nuevo['ficheros']}


def test_el_destino_no_puede_ser_un_fichero(panel, bundle, tmp_path, capsys):
    destino = tmp_path / 'fichero'
    destino.write_text('x', encoding='utf8')
    assert _exportar(panel, bundle, destino) == 2
    assert destino.read_text(encoding='utf8') == 'x'


def test_el_destino_no_puede_ser_un_enlace_simbolico(panel, bundle, tmp_path):
    real = tmp_path / 'real'
    real.mkdir()
    enlace = tmp_path / 'enlace'
    try:
        enlace.symlink_to(real, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip('sin permiso para crear enlaces simbólicos')
    assert _exportar(panel, bundle, enlace) == 2
    assert list(real.iterdir()) == []


def test_json_con_export_imprime_y_exporta_y_json_solo_no_escribe(panel, bundle, tmp_path, capsys):
    destino = tmp_path / 'salida'
    assert _exportar(panel, bundle, destino, '--json') == 0
    assert json.loads(capsys.readouterr().out)['counts']['agents'] == 1
    assert (destino / 'index.html').is_file()
    assert panel.main(['--root', str(bundle), '--json']) == 0
    assert json.loads(capsys.readouterr().out)['counts']['agents'] == 1


def test_export_solo_imprime_un_resumen_sin_rutas(panel, bundle, tmp_path, capsys):
    assert _exportar(panel, bundle, tmp_path / 'salida') == 0
    salida = capsys.readouterr().out
    assert '7' in salida and str(tmp_path) not in salida


def test_html_ya_no_existe_y_serve_excluye_export(panel, bundle, tmp_path):
    with pytest.raises(SystemExit) as error:
        panel.main(['--root', str(bundle), '--html', str(tmp_path / 'p.html')])
    assert error.value.code == 2
    with pytest.raises(SystemExit) as error:
        panel.main(['--serve', '--project', str(bundle), '--export', str(tmp_path / 'salida')])
    assert error.value.code == 2


def test_falta_un_asset_propio_es_un_diagnostico_opaco(panel, bundle, tmp_path, monkeypatch, capsys):
    copia = tmp_path / 'assets'
    shutil.copytree(ASSETS, copia)
    (copia / 'panel.css').unlink()
    monkeypatch.setattr(panel._load_pages(), 'ASSETS_DIR', copia)
    assert _exportar(panel, bundle, tmp_path / 'salida') == 2
    assert 'bundled panel asset unavailable' in capsys.readouterr().err
    assert not (tmp_path / 'salida').exists()
    assert panel.main(['--root', str(bundle), '--json']) == 0


def test_chartjs_con_huella_distinta_se_omite_y_las_paginas_degradan(panel, bundle, tmp_path, monkeypatch, capsys):
    copia = tmp_path / 'assets'
    shutil.copytree(ASSETS, copia)
    (copia / 'vendor/chart.js/chart.umd.min.js').write_bytes(b'// manipulado')
    monkeypatch.setattr(panel._load_pages(), 'ASSETS_DIR', copia)
    destino = tmp_path / 'salida'
    assert _exportar(panel, bundle, destino) == 0
    assert not (destino / 'vendor').exists()
    html = (destino / 'index.html').read_text(encoding='utf8')
    assert 'chart.umd.min.js' not in html
    assert json.loads(re.search(r'id="panel-data">(.*?)</script>', html, re.S).group(1))['chartjs_disponible'] is False
    assert 'Chart.js' in capsys.readouterr().err


def test_los_datos_de_la_instantanea_van_en_json_incrustado_y_escapado(panel, bundle, tmp_path):
    _escribir(bundle, 'skills/example/SKILL.md', '---\nname: example\ndescription: "</script><b>x</b> & más"\n---\nx')
    destino = tmp_path / 'salida'
    assert _exportar(panel, bundle, destino) == 0
    html = (destino / 'catalogo.html').read_text(encoding='utf8')
    bruto = re.search(r'id="panel-data">(.*?)</script>', html, re.S).group(1)
    assert '<' not in bruto and '>' not in bruto
    datos = json.loads(bruto)
    assert datos['inventario']['counts']['skills'] == 1
    assert datos['contadores']['agents'] == 1
    assert '</script><b>' not in html.replace(bruto, '')
