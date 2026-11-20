"""La verificacion de solo lectura distingue contenido publicado de nombres de fichero o salud.

plugin-audit-2 T-10: corre contra el adaptador de PRUEBA (`fixtures/adaptador_prueba.py`, cargado
por `directorios`/`--backends-dir`, nunca desde `backends/`) y comprueba el contrato de
`verify` y como `knowledge-sync.py --check` traduce los veredictos `ok`/`desfase`/`incompleto`.
"""
import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / 'fixtures'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def publicado(tmp_path):
    adapter = load(FIXTURES / 'adaptador_prueba.py', 'verify_adaptador_prueba')
    cfg = {'dir': 'proyeccion', '_root': str(tmp_path / 'proyecto')}
    entry = {'id': 'owned.rule', 'version': 1, 'cuerpo': 'Approved.'}
    adapter.apply(adapter.plan([entry], cfg), cfg)
    return adapter, cfg, tmp_path / 'proyecto' / 'proyeccion'


def test_publicacion_intacta_es_ok(publicado):
    adapter, cfg, _ = publicado
    resultado = adapter.verify(cfg)
    assert resultado['ok'] is True and resultado['desfase'] == []


def test_un_fichero_alterado_no_pasa_por_existir(publicado):
    adapter, cfg, carpeta = publicado
    (carpeta / 'owned.rule.md').write_text('contenido ajeno', encoding='utf-8')
    resultado = adapter.verify(cfg)
    assert resultado['ok'] is False
    assert resultado['desfase'][0]['knowledge_id'] == 'owned.rule'
    assert resultado['remedio']  # nombra el remedio sin ejecutarlo


def test_un_fichero_ausente_es_desfase(publicado):
    adapter, cfg, carpeta = publicado
    (carpeta / 'owned.rule.md').unlink()
    resultado = adapter.verify(cfg)
    assert resultado['ok'] is False and resultado['estado'] == 'desfase'


def test_sin_publicacion_es_incompleto_no_verde(tmp_path):
    adapter = load(FIXTURES / 'adaptador_prueba.py', 'verify_vacio')
    resultado = adapter.verify({'dir': 'nunca', '_root': str(tmp_path)})
    assert resultado['ok'] is False and resultado['estado'] == 'incompleto'
    assert resultado['aviso']
    assert not (tmp_path / 'nunca').exists()  # verificar no crea nada


def test_verify_no_modifica_la_publicacion(publicado):
    adapter, cfg, carpeta = publicado
    antes = {p.name: p.read_bytes() for p in carpeta.iterdir()}
    adapter.verify(cfg)
    assert {p.name: p.read_bytes() for p in carpeta.iterdir()} == antes


def _taxonomia(root, carpeta):
    d = Path(root) / '.claude/knowledge-services'
    d.mkdir(parents=True)
    cfg = {'version': 1, 'id_prefix': 'ks',
           'categories': [{'key': 'GOTCHA', 'folder': 'gotchas', 'min_evidence': 'validated_case',
                           'routing': {'docs': True}}],
           'backends': {'docs': {'type': 'adaptador-prueba', 'enabled': True,
                                 'config': {'dir': str(carpeta.relative_to(root))}}}}
    (d / 'taxonomy.json').write_text(json.dumps(cfg), encoding='utf-8')


def test_check_del_nucleo_traduce_ok_y_desfase_a_exit_codes(publicado, tmp_path, capsys):
    adapter, cfg, carpeta = publicado
    sync = load(HERE / 'knowledge-sync.py', 'verify_sync')
    root = tmp_path / 'proyecto'
    _taxonomia(root, carpeta)
    argv = ['--root', str(root), '--backend', 'docs', '--check', '--json', '--backends-dir', str(FIXTURES)]
    assert sync.main(argv) == 0
    assert json.loads(capsys.readouterr().out)['verify']['ok'] is True
    (carpeta / 'owned.rule.md').write_text('alterado', encoding='utf-8')
    assert sync.main(argv) == 1
    assert json.loads(capsys.readouterr().out)['verify']['estado'] == 'desfase'


def test_flujo_completo_plan_apply_verify_por_directorios(tmp_path, capsys):
    """T-10: un `taxonomy.json` que declara el adaptador de prueba y `--backends-dir` recorren
    `--dry-run`, publicacion y `--check` en verde, con el nucleo intacto."""
    sync = load(HERE / 'knowledge-sync.py', 'flujo_sync')
    root = tmp_path / 'proyecto'
    carpeta = root / 'salida'
    _taxonomia(root, carpeta)
    aprobada = root / 'docs/knowledge/approved/gotchas'
    aprobada.mkdir(parents=True)
    (aprobada / 'a.md').write_text(
        '---\nid: ks.gotcha.a\nversion: 1\nestado: aprobado\ncategory: GOTCHA\n'
        'evidencia: validated_case\nfuentes: [docs/e.md]\ntags: [area:x]\n---\n\nCuerpo A.\n',
        encoding='utf-8')
    base = ['--root', str(root), '--backend', 'docs', '--backends-dir', str(FIXTURES)]
    assert sync.main(base + ['--dry-run', '--json']) == 0
    assert json.loads(capsys.readouterr().out)['ops'][0]['accion'] == 'upsert'
    assert not carpeta.exists()  # dry-run no publica
    assert sync.main(base + ['--json']) == 0
    capsys.readouterr()
    assert (carpeta / 'ks.gotcha.a.md').is_file()
    assert sync.main(base + ['--check']) == 0
