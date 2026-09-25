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


# ------------------------------------------------------------------ fix1 (revision intento 1, Fase 1)

def test_f1fix1_gap08_redactar_estructura_recorre_tuplas_sets_y_claves():
    """gap #8: un secreto en una tupla, un set o una CLAVE de dict tambien se redacta."""
    secreto = "sk-ant-" + "b" * 24
    entrada = {"t": ("ok", "token=abc123XYZ789"), "s": {"password=Sup3rS3creto!"},
               "f": frozenset({secreto}), secreto: "valor", 7: "no-texto"}
    salida = rec.redactar_estructura(entrada)
    plano = repr(salida)
    for fuga in ("abc123XYZ789", "Sup3rS3creto", secreto):
        assert fuga not in plano, fuga
    assert isinstance(salida["t"], tuple) and salida["t"][0] == "ok"
    assert isinstance(salida["s"], set) and isinstance(salida["f"], frozenset)
    assert 7 in salida                        # claves no textuales intactas
    assert secreto in entrada                 # la entrada no muta


def test_f1fix1_gap08_import_sin_redact_py_no_falla_pero_redactar_si(tmp_path, monkeypatch):
    """gap #8: `redact.py` se carga al REDACTAR (perezoso), no al importar: sin el, importar el
    modulo funciona y es la redaccion la que levanta `RedaccionNoDisponible` (fail closed)."""
    monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
    aislado = tmp_path / "scripts"
    aislado.mkdir()
    copia = aislado / "case-recorder.py"
    with open(RECORDER_PATH, encoding="utf-8") as f:
        copia.write_text(f.read(), encoding="utf-8")
    mod = _load(str(copia), "case_recorder_sin_redact")
    try:
        with pytest.raises(mod.RedaccionNoDisponible):
            mod.redactar_estructura({"request": "token=abc123XYZ789"})
        with pytest.raises(mod.RedaccionNoDisponible):
            mod.redactar("token=abc123XYZ789")
    finally:
        sys.modules.pop("case_recorder_sin_redact", None)


# ------------------------------------------------------------------ fix2 (revision intento 2, Fase 1)

def test_f1fix2_gap18_claves_que_redactan_igual_no_colisionan():
    """gap #18: dos claves distintas que se redactan al mismo literal conservan ambos valores,
    con sufijo estable por orden de aparicion; una clave literal igual a la redactada no se pisa."""
    k1 = "token=abc123XYZ789"
    k2 = "token=zzz999QQQ111"
    salida = rec.redactar_estructura({k1: "uno", k2: "dos", "ok": "tres"})
    assert sorted(salida.values()) == ["dos", "tres", "uno"]
    assert all("abc123XYZ789" not in k and "zzz999QQQ111" not in k for k in salida)
    redactada = rec.redactar(k1)
    assert salida[redactada] == "uno" and salida[redactada + " #2"] == "dos"
    # determinista: misma entrada, mismas claves
    assert list(rec.redactar_estructura({k1: "uno", k2: "dos", "ok": "tres"})) == list(salida)
    # una clave NO redactada que coincide con el literal redactado se conserva tal cual
    salida = rec.redactar_estructura({k1: "secreta", redactada: "literal"})
    assert salida[redactada] == "literal" and sorted(salida.values()) == ["literal", "secreta"]


def test_f1fix2_gap18_namedtuple_se_reconstruye():
    """gap #18: una namedtuple no revienta y conserva su tipo y campos."""
    import collections
    Par = collections.namedtuple("Par", "clave valor")
    salida = rec.redactar_estructura({"p": Par("api", "token=abc123XYZ789")})
    assert isinstance(salida["p"], Par) and salida["p"].clave == "api"
    assert "abc123XYZ789" not in salida["p"].valor
