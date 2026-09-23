"""Tests de `case-recorder.py` (training-data-services T-02; el recorder completo llega en T-04).

T-02 fija UNA regla: la redaccion de secretos del recorder es la de `agent-kits/shared/redact.py`
(fuente unica de patrones del plugin, `session-end-durable-capture` T-02, CA-09). El recorder no
define ningun patron propio y, si `redact.py` no esta disponible, se niega a redactar (nunca
escribe un caso sin redactar ni cae a una copia local).
"""
import ast
import importlib.util
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REDACT_PATH = os.path.normpath(os.path.join(HERE, "..", "..", "..", "agent-kits", "shared", "redact.py"))
RECORDER_PATH = os.path.join(HERE, "case-recorder.py")


def _load(ruta, nombre):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = mod
    spec.loader.exec_module(mod)
    return mod


rec = _load(RECORDER_PATH, "case_recorder_bajo_test")


def test_redactar_es_la_de_redact_py():
    """Misma funcion (mismo codigo), no una copia: el recorder la toma de `redact.py`."""
    assert os.path.normcase(rec.redactar.__code__.co_filename) == os.path.normcase(REDACT_PATH)
    assert rec.REDACTADO == "[secreto redactado]"


def test_redacta_secretos_evidentes():
    texto = "usa token=abc123XYZ789 y la clave sk-ant-" + "a" * 24 + " para entrar"
    salida = rec.redactar(texto)
    assert "abc123XYZ789" not in salida
    assert "sk-ant-" + "a" * 24 not in salida
    assert salida.count(rec.REDACTADO) == 2
    # alta precision: lo inocuo no se toca
    assert rec.redactar("tokens por hora (479326)") == "tokens por hora (479326)"


def test_redactar_estructura_recorre_dicts_y_listas_sin_tocar_claves():
    caso = {"request": "password=Sup3rS3creto!", "trajectory": [
        {"role": "user", "content": "Bearer " + "x" * 30}, {"role": "tool", "name": "t", "content": "ok"}],
        "metrics": {"score": 0.9}}
    salida = rec.redactar_estructura(caso)
    assert "Sup3rS3creto" not in salida["request"]
    assert rec.REDACTADO in salida["trajectory"][0]["content"]
    assert salida["trajectory"][1] == {"role": "tool", "name": "t", "content": "ok"}
    assert salida["metrics"] == {"score": 0.9}          # no-texto intacto
    assert caso["request"] == "password=Sup3rS3creto!"  # no muta la entrada


def test_recorder_no_define_patrones_propios():
    """Ni `re.compile`, ni `_SECRETOS_RE`, ni `def redactar` en el recorder: una sola fuente."""
    with open(RECORDER_PATH, encoding="utf-8") as f:
        fuente = f.read()
    arbol = ast.parse(fuente)
    definidas = {n.name for n in ast.walk(arbol) if isinstance(n, ast.FunctionDef)}
    assert "redactar" not in definidas
    assert "_SECRETOS_RE" not in fuente
    assert "re.compile" not in fuente
    assert "import re\n" not in fuente


def test_sin_redact_py_se_niega(tmp_path):
    """Instalacion parcial sin `agent-kits/shared/redact.py`: error explicito, nunca sin redactar."""
    with pytest.raises(rec.RedaccionNoDisponible):
        rec.cargar_redact([str(tmp_path / "no-existe")])
