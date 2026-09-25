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
    # T-04: el recorder carga `case_schema.py` de su MISMA carpeta (viaja siempre con el, en la
    # skill); lo que puede faltar en un paquete parcial es `agent-kits/shared/redact.py`.
    with open(os.path.join(HERE, "case_schema.py"), encoding="utf-8") as f:
        (aislado / "case_schema.py").write_text(f.read(), encoding="utf-8")
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


# ------------------------------------------------------------------ T-04: recorder determinista

import copy
import json
import subprocess
import threading

ASSETS_EJEMPLO = os.path.normpath(os.path.join(HERE, "..", "assets", "case-store-example"))
FICHEROS_VERSION = {"metadata.json", "request.json", "context.json", "constraints.json",
                    "trajectory.jsonl", "metrics.json", "validation.json", "final/artifacts.json"}
SECRETO = "sk-ant-" + "c" * 24

CASO = {
    "case_id": "geo-ramp.steep", "family": "ramp", "variant": "steep",
    "request": "Genera una rampa de 30 grados (año 2026, ñandú)",
    "context": {"text": "escena vacía", "refs": [{"ref": "src/scene/ramp.py:42", "kind": "code"}]},
    "constraints": {"max_angle_deg": 30},
    "trajectory": [
        {"role": "user", "content": "Genera una rampa", "ts": "2026-09-25T10:00:00Z"},
        {"role": "assistant", "content": "", "tool_calls": [{"name": "make_ramp", "arguments": {"angle_deg": 30}}]},
        {"role": "tool", "name": "make_ramp", "content": "ok"},
    ],
    "metrics": {"score": 0.5},
    "validation": {"status": "pending", "approved_by_human": False},
    "outcome": "failure",
    "artifacts": [{"path": "final/ramp.blend", "hash": "sha256:ab12", "kind": "mesh"}],
}


def _caso(**cambios):
    c = copy.deepcopy(CASO)
    c.update(cambios)
    return c


def _proyecto(tmp_path, **ids):
    """Proyecto con su config; el store vive FUERA del proyecto (`../store`, ADR-019)."""
    raiz = tmp_path / "proj"
    raiz.mkdir(exist_ok=True)
    cfg = {"version": 1, "enabled": True, "root": "../store", "id_prefix": "geo"}
    if ids:
        cfg["ids"] = ids
    return str(raiz), cfg, tmp_path / "store"


def _escribir_config(tmp_path, cfg):
    d = tmp_path / "proj" / ".claude" / "knowledge-services"
    d.mkdir(parents=True, exist_ok=True)
    (d / "training.json").write_text(json.dumps(cfg), encoding="utf-8")
    return d / "training.json"


def _ficheros(dir_version):
    out = set()
    for base, _dirs, fs in os.walk(dir_version):
        for f in fs:
            out.add(os.path.relpath(os.path.join(base, f), dir_version).replace(os.sep, "/"))
    return out


def _bytes_del_store(store):
    todo = b""
    for base, _dirs, fs in os.walk(store):
        for f in fs:
            with open(os.path.join(base, f), "rb") as fh:
                todo += fh.read()
    return todo


def _json(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def _jsonl(ruta):
    with open(ruta, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def test_t04_graba_la_estructura_exacta_de_design(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    r = rec.grabar(_caso(), cfg, raiz)
    assert r["case_id"] == "geo-ramp.steep" and r["version"] == 1 and r["ref"] == "geo-ramp.steep@v001"
    d = store / "cases" / "ramp.steep" / "v001"
    assert os.path.normcase(os.path.realpath(r["path"])) == os.path.normcase(os.path.realpath(str(d)))
    assert _ficheros(str(d)) == FICHEROS_VERSION
    meta = _json(d / "metadata.json")
    assert meta["case_id"] == "geo-ramp.steep" and meta["version"] == 1 and meta["outcome"] == "failure"
    assert set(meta) == {"case_id", "family", "variant", "version", "created_at", "outcome"}
    assert _json(d / "request.json") == {"request": CASO["request"]}
    assert _json(d / "context.json") == CASO["context"]
    assert _json(d / "constraints.json") == CASO["constraints"]
    assert _jsonl(d / "trajectory.jsonl") == CASO["trajectory"]
    assert _json(d / "metrics.json") == CASO["metrics"]
    assert _json(d / "validation.json") == {"status": "pending", "approved_by_human": False,
                                            "approved_at": None, "reviewer_note": None}
    assert _json(d / "final" / "artifacts.json") == CASO["artifacts"]
    # UTF-8 sin escapar (ensure_ascii=False) y LF: ni escapes \uXXXX ni CRLF en disco
    for f in FICHEROS_VERSION:
        crudo = (d / f).read_bytes()
        assert b"\r\n" not in crudo, f
        assert b"\\u00" not in crudo, f
    assert "ñandú".encode("utf-8") in (d / "request.json").read_bytes()
    assert len((d / "trajectory.jsonl").read_bytes().splitlines()) == 3


def _componer_ejemplo(dir_version):
    caso = _json(os.path.join(dir_version, "metadata.json"))
    caso["request"] = _json(os.path.join(dir_version, "request.json"))["request"]
    for f in ("context", "constraints", "metrics", "validation"):
        caso[f] = _json(os.path.join(dir_version, f + ".json"))
    caso["trajectory"] = _jsonl(os.path.join(dir_version, "trajectory.jsonl"))
    caso["artifacts"] = _json(os.path.join(dir_version, "final", "artifacts.json"))
    return caso


def test_t04_reproduce_el_ejemplo_de_assets_fichero_a_fichero(tmp_path):
    """Grabar el ejemplo de `assets/` (v001 failure/rejected + v002 corrected/Gold) produce los
    mismos ficheros con el mismo contenido: la estructura del recorder ES la documentada."""
    raiz, cfg, store = _proyecto(tmp_path)
    for v in ("v001", "v002"):
        origen = os.path.join(ASSETS_EJEMPLO, "cases", "ramp.steep", v)
        caso = _componer_ejemplo(origen)
        rec.grabar(caso, cfg, raiz, approved_by_human=(v == "v002"))
        destino = store / "cases" / "ramp.steep" / v
        assert _ficheros(str(destino)) == _ficheros(origen) == FICHEROS_VERSION
        for f in FICHEROS_VERSION:
            ruta_o, ruta_d = os.path.join(origen, f), str(destino / f)
            leer = _jsonl if f.endswith(".jsonl") else _json
            assert leer(ruta_d) == leer(ruta_o), (v, f)


def test_t04_version_siguiente_libre_y_nunca_sobrescribe(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    c = _caso()
    c.pop("version", None)
    assert rec.grabar(c, cfg, raiz)["version"] == 1
    assert rec.grabar(_caso(request="otra peticion"), cfg, raiz)["version"] == 2
    v1 = store / "cases" / "ramp.steep" / "v001"
    antes = {f: (v1 / f).read_bytes() for f in FICHEROS_VERSION}
    with pytest.raises(rec.Rechazo) as e:
        rec.grabar(_caso(version=1, request="pisar v001"), cfg, raiz)
    assert "geo-ramp.steep@v001" in str(e.value) and "existe" in str(e.value)
    assert {f: (v1 / f).read_bytes() for f in FICHEROS_VERSION} == antes
    assert rec.grabar(_caso(version=7), cfg, raiz)["version"] == 7
    assert rec.grabar(_caso(), cfg, raiz)["version"] == 8        # siguiente a la MAYOR existente
    assert sorted(os.listdir(store / "cases" / "ramp.steep")) == ["v001", "v002", "v007", "v008"]


def test_t04_ancho_de_version_de_la_config(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path, version_width=4)
    r = rec.grabar(_caso(), cfg, raiz)
    assert r["ref"] == "geo-ramp.steep@v0001"
    assert (store / "cases" / "ramp.steep" / "v0001" / "metadata.json").is_file()


def test_t04_id_estable_desde_la_config(tmp_path):
    raiz, cfg, _store = _proyecto(tmp_path)
    c = _caso()
    del c["case_id"]
    assert rec.grabar(c, cfg, raiz)["case_id"] == "geo-ramp.steep"
    with pytest.raises(rec.Rechazo) as e:
        rec.grabar(_caso(case_id="otro-ramp.steep"), cfg, raiz)
    assert "case_id" in {x["campo"] for x in e.value.errores}


def test_t04_redacta_request_context_constraints_y_trayectoria_antes_de_escribir(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    tr = copy.deepcopy(CASO["trajectory"])
    tr[0]["content"] = "usa " + SECRETO
    tr[1]["tool_calls"][0]["arguments"] = {"api_key": "token=abc123XYZ789"}
    c = _caso(request="password=Sup3rS3creto!", context={"text": "Bearer " + "x" * 30},
              constraints={"cred": "token=zzz999QQQ111"}, trajectory=tr)
    rec.grabar(c, cfg, raiz)
    todo = _bytes_del_store(str(store))
    for fuga in (SECRETO, "abc123XYZ789", "Sup3rS3creto", "x" * 30, "zzz999QQQ111"):
        assert fuga.encode() not in todo, fuga
    assert rec.REDACTADO.encode() in todo


def test_t04_valida_el_caso_ya_redactado(tmp_path, monkeypatch):
    """Orden obligatorio: redactar -> validar -> escribir. El validador recibe el caso REDACTADO."""
    raiz, cfg, _store = _proyecto(tmp_path)
    vistos = []
    original = rec.cs.validar_caso

    def espia(caso, config=None):
        vistos.append(json.dumps(caso, ensure_ascii=False))
        return original(caso, config)

    monkeypatch.setattr(rec.cs, "validar_caso", espia)
    r = rec.grabar(_caso(request="password=Sup3rS3creto!"), cfg, raiz)
    # fix1 Fase 2 (gap #32): se valida el ORIGINAL (forma + CoT) y DESPUES el redactado; lo que se
    # escribe es lo redactado (la ultima validacion es la del caso redactado)
    assert len(vistos) == 2 and "Sup3rS3creto" in vistos[0] and "Sup3rS3creto" not in vistos[1]
    assert b"Sup3rS3creto" not in _bytes_del_store(os.path.dirname(os.path.dirname(os.path.dirname(r["path"]))))


def test_t04_caso_invalido_no_toca_disco(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    for malo in (_caso(outcome="meh"), _caso(trajectory=[]),
                 _caso(artifacts=[{"path": "final/a", "hash": "sha256:ab", "content": "AAAA"}]),
                 _caso(family="r/../../x"), _caso(version=0), "no soy un objeto"):
        with pytest.raises(rec.Rechazo) as e:
            rec.grabar(malo, cfg, raiz)
        assert e.value.errores and all({"campo", "mensaje"} <= set(x) for x in e.value.errores)
    assert not store.exists()


def test_t04_sin_redact_py_no_toca_disco(tmp_path, monkeypatch):
    raiz, cfg, store = _proyecto(tmp_path)

    def _falta():
        raise rec.RedaccionNoDisponible("sin redact.py")

    monkeypatch.setattr(rec, "_redact_mod", _falta)
    with pytest.raises(rec.RedaccionNoDisponible):
        rec.grabar(_caso(), cfg, raiz)
    assert not store.exists()


def test_t04_sin_config_desactivada_o_invalida_rechaza_sin_escribir(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    for mala, pista in ((None, "falta .claude/knowledge-services/training.json"), (dict(cfg, enabled=False), "enabled: false"),
                        (dict(cfg, root="docs/knowledge/cases"), "root")):
        with pytest.raises(rec.Rechazo) as e:
            rec.grabar(_caso(), mala, raiz)
        assert pista in str(e.value)
    assert not store.exists()
    assert not (tmp_path / "proj" / "docs").exists()


def test_t04_gold_no_nace_por_record_sin_flag(tmp_path):
    """Un caso no nace `approved` por `record` sin `--approved-by-human` (sin puerta trasera:
    ni con `approved_by_human: true` escrito en el propio caso)."""
    raiz, cfg, store = _proyecto(tmp_path)
    for val in ({"status": "approved", "approved_by_human": False},
                {"status": "approved", "approved_by_human": True, "approved_at": "2026-09-25T10:00:00Z"}):
        with pytest.raises(rec.Rechazo) as e:
            rec.grabar(_caso(validation=val), cfg, raiz)
        assert "--approved-by-human" in str(e.value)
    assert not store.exists()
    r = rec.grabar(_caso(validation={"status": "approved", "approved_by_human": False}), cfg, raiz,
                   approved_by_human=True)
    val = _json(os.path.join(r["path"], "validation.json"))
    assert val["status"] == "approved" and val["approved_by_human"] is True and val["approved_at"]


def test_t04_corrected_exige_que_exista_la_version_que_corrige(tmp_path):
    """CA-12: la version citada en `supersedes_case` debe existir y se conserva junto a la correccion."""
    raiz, cfg, store = _proyecto(tmp_path)
    corr = _caso(version=2, outcome="corrected", supersedes_case="geo-ramp.steep@v001")
    with pytest.raises(rec.Rechazo) as e:
        rec.grabar(corr, cfg, raiz)
    assert "supersedes_case" in {x["campo"] for x in e.value.errores}
    assert not store.exists()
    rec.grabar(_caso(version=1, validation={"status": "rejected", "approved_by_human": False}), cfg, raiz)
    rec.grabar(corr, cfg, raiz)
    base = store / "cases" / "ramp.steep"
    assert sorted(os.listdir(base)) == ["v001", "v002"]
    assert _json(base / "v002" / "metadata.json")["supersedes_case"] == "geo-ramp.steep@v001"
    assert _json(base / "v001" / "validation.json")["status"] == "rejected"


def test_t04_rechazados_y_fallidos_se_conservan_no_hay_borrado(tmp_path):
    """CA-02: no existe operacion de borrado; lo rechazado sigue en disco tras nuevas versiones."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(validation={"status": "rejected", "approved_by_human": False}), cfg, raiz)
    for _ in range(3):
        rec.grabar(_caso(), cfg, raiz)
    v1 = store / "cases" / "ramp.steep" / "v001"
    assert _json(v1 / "validation.json")["status"] == "rejected" and _ficheros(str(v1)) == FICHEROS_VERSION
    # ni API ni CLI de borrado; lo unico que se elimina es el directorio temporal propio
    publicas = {n for n in dir(rec) if not n.startswith("_")}
    assert not {n for n in publicas if any(p in n.lower() for p in ("borrar", "delete", "remove", "purge"))}
    with open(RECORDER_PATH, encoding="utf-8") as f:
        arbol = ast.parse(f.read())
    assert "rmtree" not in ast.dump(arbol) and "unlink" not in ast.dump(arbol)
    for nodo in ast.walk(arbol):
        # fix4 (#82, arbitraje): `_deshacer_si_escapa` retira SOLO el fichero propio recien creado que
        # escapo del store por un enlace (misma identidad que su descriptor); nunca una version
        if isinstance(nodo, ast.FunctionDef) and nodo.name not in ("_limpiar_temporal", "_deshacer_si_escapa"):
            for sub in ast.walk(nodo):
                if isinstance(sub, ast.Attribute) and sub.attr in ("remove", "rmdir", "removedirs"):
                    raise AssertionError(f"{nodo.name} borra ({sub.attr})")


def test_t04_concurrencia_sin_version_cada_hilo_su_version(tmp_path):
    """Dos (o N) recorders a la vez: la reserva de la version es atomica (mkdir del destino)."""
    raiz, cfg, store = _proyecto(tmp_path)
    n = 12
    barrera = threading.Barrier(n)
    res, errores = [], []

    def graba(i):
        barrera.wait()
        try:
            res.append((i, rec.grabar(_caso(request=f"peticion {i}"), cfg, raiz)["version"]))
        except Exception as e:   # noqa: BLE001 — se comprueba abajo
            errores.append(e)

    hilos = [threading.Thread(target=graba, args=(i,)) for i in range(n)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    assert not errores, errores
    assert sorted(v for _i, v in res) == list(range(1, n + 1))
    for i, v in res:
        d = store / "cases" / "ramp.steep" / f"v{v:03d}"
        assert _json(d / "request.json") == {"request": f"peticion {i}"}
        assert _ficheros(str(d)) == FICHEROS_VERSION
    assert sorted(os.listdir(store / "cases" / "ramp.steep")) == [f"v{v:03d}" for v in range(1, n + 1)]


def test_t04_concurrencia_misma_version_explicita_gana_uno(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    n = 8
    barrera = threading.Barrier(n)
    ok, rechazos = [], []

    def graba(i):
        barrera.wait()
        try:
            rec.grabar(_caso(version=5, request=f"peticion {i}"), cfg, raiz)
            ok.append(i)
        except rec.Rechazo:
            rechazos.append(i)

    hilos = [threading.Thread(target=graba, args=(i,)) for i in range(n)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    assert len(ok) == 1 and len(rechazos) == n - 1
    d = store / "cases" / "ramp.steep" / "v005"
    assert _json(d / "request.json") == {"request": f"peticion {ok[0]}"}


def test_t04_reserva_atomica_aunque_la_vista_de_versiones_este_obsoleta(tmp_path, monkeypatch):
    """Deterministico: si dos recorders calculan la MISMA siguiente version, el segundo no pisa al
    primero (mkdir falla si existe) y reintenta con la siguiente; con version explicita, rechaza."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(request="primero"), cfg, raiz)
    monkeypatch.setattr(rec, "_siguiente_version", lambda *_a, **_k: 1)
    assert rec.grabar(_caso(request="segundo"), cfg, raiz)["version"] == 2
    base = store / "cases" / "ramp.steep"
    assert _json(base / "v001" / "request.json") == {"request": "primero"}
    assert _json(base / "v002" / "request.json") == {"request": "segundo"}
    assert sorted(os.listdir(base)) == ["v001", "v002"]     # sin temporales huerfanos


def test_t04_procesos_concurrentes_por_cli(tmp_path):
    """Lo mismo con PROCESOS (CLI `record` lanzado en paralelo): versiones distintas, nada pisado."""
    raiz, cfg, store = _proyecto(tmp_path)
    _escribir_config(tmp_path, cfg)
    procs = []
    for i in range(5):
        f = tmp_path / f"caso{i}.json"
        f.write_text(json.dumps(_caso(request=f"proceso {i}")), encoding="utf-8")
        procs.append(subprocess.Popen([sys.executable, RECORDER_PATH, "record", str(f), "--project-root", raiz],
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE))
    salidas = [p.communicate(timeout=120) for p in procs]
    assert all(p.returncode == 0 for p in procs), [s[1] for s in salidas]
    versiones = sorted(json.loads(s[0])["version"] for s in salidas)
    assert versiones == [1, 2, 3, 4, 5]
    peticiones = {_json(store / "cases" / "ramp.steep" / f"v{v:03d}" / "request.json")["request"] for v in versiones}
    assert peticiones == {f"proceso {i}" for i in range(5)}
    # T-06: el indice recibe las 5 altas sin perder ni mezclar lineas entre procesos
    if hasattr(rec, "comprobar_indice"):
        assert rec.comprobar_indice(str(store)) == []


def _cli(*args, cwd=None):
    return subprocess.run([sys.executable, RECORDER_PATH, *args], capture_output=True, text=True,
                          encoding="utf-8", cwd=cwd)


def test_t04_cli_record_codigos_de_salida(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    caso = tmp_path / "caso.json"
    caso.write_text(json.dumps(_caso()), encoding="utf-8")
    # sin training.json: rechazo explicito, exit 1, nada escrito
    r = _cli("record", str(caso), "--project-root", raiz)
    assert r.returncode == 1 and "training.json" in r.stderr and not store.exists()
    ruta_cfg = _escribir_config(tmp_path, cfg)
    r = _cli("record", str(caso), "--project-root", raiz)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["ref"] == "geo-ramp.steep@v001"
    # --config explicito (raiz deducida de su ruta)
    r = _cli("record", str(caso), "--config", str(ruta_cfg))
    assert r.returncode == 0 and json.loads(r.stdout)["version"] == 2, r.stderr
    # caso invalido: exit 1 con el campo; JSON ilegible: exit 2
    malo = tmp_path / "malo.json"
    malo.write_text(json.dumps(_caso(outcome="meh")), encoding="utf-8")
    r = _cli("record", str(malo), "--project-root", raiz)
    assert r.returncode == 1 and "outcome" in r.stderr
    roto = tmp_path / "roto.json"
    roto.write_text("{no es json", encoding="utf-8")
    assert _cli("record", str(roto), "--project-root", raiz).returncode == 2
    hondo = tmp_path / "hondo.json"
    hondo.write_text("[" * 100000 + "]" * 100000, encoding="utf-8")
    r = _cli("record", str(hondo), "--project-root", raiz)
    assert r.returncode == 2 and "Traceback" not in r.stderr
    # approved sin flag: exit 1; con flag: exit 0
    gold = tmp_path / "gold.json"
    gold.write_text(json.dumps(_caso(validation={"status": "approved", "approved_by_human": False})), encoding="utf-8")
    r = _cli("record", str(gold), "--project-root", raiz)
    assert r.returncode == 1 and "--approved-by-human" in r.stderr
    assert _cli("record", str(gold), "--project-root", raiz, "--approved-by-human").returncode == 0
    # uso incorrecto: exit 2
    assert _cli("record").returncode == 2


def test_t04_sin_red_ni_dominio():
    """CA-04 / sin red: el recorder no importa nada de red ni de dominio; solo stdlib."""
    with open(RECORDER_PATH, encoding="utf-8") as f:
        arbol = ast.parse(f.read())
    importados = set()
    for n in ast.walk(arbol):
        if isinstance(n, ast.Import):
            importados |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            importados.add(n.module.split(".")[0])
    assert not importados & {"socket", "urllib", "http", "requests", "ssl", "bpy"}
    assert importados <= set(sys.stdlib_module_names)


# ------------------------------------------------------------------ T-05: puerta humana para Gold

def _grabado(tmp_path, **cambios):
    raiz, cfg, store = _proyecto(tmp_path)
    r = rec.grabar(_caso(**cambios), cfg, raiz)
    return raiz, cfg, store, r


def test_t05_gold_approved_sin_flag_falla_con_mensaje_explicito(tmp_path):
    raiz, cfg, _store, r = _grabado(tmp_path)
    val = os.path.join(r["path"], "validation.json")
    antes = open(val, "rb").read()
    for sin_flag in ({}, {"approved_by_human": False}, {"approved_by_human": 1}, {"approved_by_human": "si"}):
        with pytest.raises(rec.Rechazo) as e:
            rec.cambiar_estado("geo-ramp.steep", 1, "approved", cfg, raiz, **sin_flag)
        assert "approved exige --approved-by-human: Gold es siempre una accion humana" in str(e.value), sin_flag
    assert open(val, "rb").read() == antes


def test_t05_gold_con_flag_fija_humano_fecha_y_nota(tmp_path):
    raiz, cfg, _store, r = _grabado(tmp_path)
    out = rec.cambiar_estado("geo-ramp.steep", 1, "approved", cfg, raiz, approved_by_human=True,
                             reviewer_note="Revisado a mano: Gold.")
    val = _json(os.path.join(r["path"], "validation.json"))
    assert val["status"] == "approved" and val["approved_by_human"] is True
    assert isinstance(val["approved_at"], str) and val["approved_at"].endswith("Z")
    assert val["reviewer_note"] == "Revisado a mano: Gold."
    assert out["status"] == "approved" and out["ref"] == "geo-ramp.steep@v001"


def test_t05_gold_needs_changes_rejected_y_pending_no_requieren_el_flag(tmp_path):
    raiz, cfg, _store, r = _grabado(tmp_path)
    ruta = os.path.join(r["path"], "validation.json")
    rec.cambiar_estado("geo-ramp.steep", 1, "approved", cfg, raiz, approved_by_human=True, reviewer_note="nota previa")
    for status in ("needs_changes", "rejected", "pending"):
        rec.cambiar_estado("geo-ramp.steep", 1, status, cfg, raiz)
        val = _json(ruta)
        assert val["status"] == status and val["approved_by_human"] is False and val["approved_at"] is None, status
        assert val["reviewer_note"] == "nota previa"      # sin --note se conserva
    # el resultado sigue siendo un caso valido para el esquema
    assert rec.cs._validar_validation is not None
    errores = []
    rec.cs._validar_validation(_json(ruta), errores)
    assert errores == []


def test_t05_gold_solo_reescribe_validation_y_de_forma_atomica(tmp_path, monkeypatch):
    raiz, cfg, _store, r = _grabado(tmp_path)
    d = r["path"]
    otros = {f: open(os.path.join(d, f), "rb").read() for f in FICHEROS_VERSION if f != "validation.json"}
    rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg, raiz, reviewer_note="no vale")
    assert {f: open(os.path.join(d, f), "rb").read() for f in otros} == otros
    assert _ficheros(d) == FICHEROS_VERSION                  # sin temporales
    # si la sustitucion falla, validation.json queda como estaba y no quedan temporales
    antes = open(os.path.join(d, "validation.json"), "rb").read()

    def _falla(*_a, **_k):
        raise OSError("disco lleno")

    monkeypatch.setattr(rec.os, "replace", _falla)
    with pytest.raises(OSError):
        rec.cambiar_estado("geo-ramp.steep", 1, "pending", cfg, raiz)
    assert open(os.path.join(d, "validation.json"), "rb").read() == antes
    assert _ficheros(d) == FICHEROS_VERSION
    assert b"\r\n" not in antes


def test_t05_gold_estado_version_o_case_id_invalidos_se_rechazan(tmp_path):
    raiz, cfg, store, _r = _grabado(tmp_path)
    for args in (("geo-ramp.steep", 1, "gold"), ("geo-ramp.steep", 9, "rejected"),
                 ("otro-ramp.steep", 1, "rejected"), ("geo-ramp", 1, "rejected"),
                 ("geo-ramp.steep.x", 1, "rejected"), ("geo-../x.steep", 1, "rejected"),
                 ("geo-ramp.steep", 0, "rejected"), ("geo-ramp.steep", "uno", "rejected")):
        with pytest.raises(rec.Rechazo):
            rec.cambiar_estado(*args, cfg, raiz)
    # una version fuera de rango se rechaza POR SER version invalida, no por no encontrarse
    for mala in (0, -1, "v000", "uno", True, "v", ""):
        with pytest.raises(rec.Rechazo) as e:
            rec.cambiar_estado("geo-ramp.steep", mala, "rejected", cfg, raiz)
        assert e.value.errores[0]["campo"] == "version", mala
    # una version a medio escribir (sin metadata.json) no admite cambios de estado
    parcial = store / "cases" / "ramp.steep" / "v002"
    parcial.mkdir()
    with pytest.raises(rec.Rechazo):
        rec.cambiar_estado("geo-ramp.steep", 2, "rejected", cfg, raiz)
    # la version admite tambien la forma `v001`
    assert rec.cambiar_estado("geo-ramp.steep", "v001", "rejected", cfg, raiz)["version"] == 1


def test_t05_gold_sin_config_o_desactivada_no_escribe(tmp_path):
    raiz, cfg, _store, r = _grabado(tmp_path)
    antes = open(os.path.join(r["path"], "validation.json"), "rb").read()
    for mala in (None, dict(cfg, enabled=False)):
        with pytest.raises(rec.Rechazo):
            rec.cambiar_estado("geo-ramp.steep", 1, "rejected", mala, raiz)
    assert open(os.path.join(r["path"], "validation.json"), "rb").read() == antes


def test_t05_gold_corrected_se_conserva_junto_al_failure_que_corrige(tmp_path):
    """Criterio 2 de T-05: el `corrected` declara `supersedes_case` y el `failure` sigue en disco,
    aunque se rechace y aunque la correccion llegue a Gold."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(outcome="failure"), cfg, raiz)
    rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg, raiz, reviewer_note="se sale de la rampa")
    sin_sup = _caso(outcome="corrected")
    with pytest.raises(rec.Rechazo) as e:
        rec.grabar(sin_sup, cfg, raiz)
    assert "supersedes_case" in {x["campo"] for x in e.value.errores}
    rec.grabar(_caso(outcome="corrected", supersedes_case="geo-ramp.steep@v001"), cfg, raiz)
    rec.cambiar_estado("geo-ramp.steep", 2, "approved", cfg, raiz, approved_by_human=True)
    base = store / "cases" / "ramp.steep"
    assert _json(base / "v001" / "metadata.json")["outcome"] == "failure"
    assert _json(base / "v001" / "validation.json")["status"] == "rejected"
    assert _json(base / "v002" / "metadata.json")["supersedes_case"] == "geo-ramp.steep@v001"
    assert _json(base / "v002" / "validation.json")["approved_by_human"] is True


def test_t05_gold_cli_set_status(tmp_path):
    raiz, cfg, _store, r = _grabado(tmp_path)
    _escribir_config(tmp_path, cfg)
    val = os.path.join(r["path"], "validation.json")
    s = _cli("set-status", "geo-ramp.steep", "1", "approved", "--project-root", raiz)
    assert s.returncode == 1 and "approved exige --approved-by-human" in s.stderr
    assert _json(val)["status"] == "pending"
    s = _cli("set-status", "geo-ramp.steep", "v001", "approved", "--approved-by-human", "--note", "ok humano",
             "--project-root", raiz)
    assert s.returncode == 0, s.stderr
    assert _json(val)["approved_by_human"] is True and _json(val)["reviewer_note"] == "ok humano"
    assert _cli("set-status", "geo-ramp.steep", "1", "needs_changes", "--project-root", raiz).returncode == 0
    assert _json(val)["status"] == "needs_changes" and _json(val)["approved_by_human"] is False
    assert _cli("set-status", "geo-ramp.steep", "1", "gold", "--project-root", raiz).returncode == 2
    assert _cli("set-status", "geo-ramp.steep", "7", "rejected", "--project-root", raiz).returncode == 1


# ------------------------------------------------------------------ T-06: indice cases_index.jsonl

import shutil

CLAVES_INDICE = ("case_id", "version", "family", "variant", "status", "outcome", "updated_at")


def _indice(store):
    return _jsonl(os.path.join(str(store), "cases_index.jsonl"))


def _ultimas(lineas):
    """Ultima linea por (case_id, version), sin `updated_at` (lo que el indice promete)."""
    out = {}
    for l in lineas:
        out[(l["case_id"], l["version"])] = {k: l[k] for k in CLAVES_INDICE if k != "updated_at"}
    return out


def test_t06_index_una_linea_por_alta_y_por_cambio_de_estado(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(outcome="failure"), cfg, raiz)
    rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg, raiz)
    rec.grabar(_caso(outcome="corrected", supersedes_case="geo-ramp.steep@v001"), cfg, raiz)
    rec.cambiar_estado("geo-ramp.steep", 2, "approved", cfg, raiz, approved_by_human=True)
    lineas = _indice(store)
    assert [tuple(l) for l in lineas] == [CLAVES_INDICE] * 4          # claves EXACTAS y en orden
    assert [(l["version"], l["status"], l["outcome"]) for l in lineas] == [
        (1, "pending", "failure"), (1, "rejected", "failure"), (2, "pending", "corrected"), (2, "approved", "corrected")]
    assert all(l["family"] == "ramp" and l["variant"] == "steep" and l["updated_at"].endswith("Z") for l in lineas)
    # misma forma que el ejemplo documentado de assets/
    ejemplo = _indice(ASSETS_EJEMPLO)
    assert [(l["version"], l["status"]) for l in lineas] == [(l["version"], l["status"]) for l in ejemplo]


def test_t06_index_es_append_only(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    ruta = os.path.join(str(store), "cases_index.jsonl")
    rec.grabar(_caso(), cfg, raiz)
    antes = open(ruta, "rb").read()
    rec.cambiar_estado("geo-ramp.steep", 1, "needs_changes", cfg, raiz)
    rec.grabar(_caso(), cfg, raiz)
    despues = open(ruta, "rb").read()
    assert despues.startswith(antes) and despues.count(b"\n") == 3 and b"\r\n" not in despues


def test_t06_index_se_reconstruye_desde_cases_si_se_pierde_o_corrompe(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg, raiz)
    rec.grabar(_caso(variant="gentle", case_id="geo-ramp.gentle"), cfg, raiz)
    _envejecer(store)       # fix2 (E5): una version recien grabada sin linea estaria «en curso» 60 s
    esperado = _ultimas(_indice(store))
    ruta = os.path.join(str(store), "cases_index.jsonl")
    for estropear in ("perder", "corromper"):
        if estropear == "perder":
            os.remove(ruta)
        else:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write("{basura\n[1,2]\n")
        assert rec.comprobar_indice(str(store))                       # diverge
        n, _avisos = rec.reconstruir_indice(str(store))
        assert n == 2
        assert _ultimas(_indice(store)) == esperado
        assert rec.comprobar_indice(str(store)) == []


def test_t06_index_check_detecta_divergencias_con_detalle(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    rec.grabar(_caso(), cfg, raiz)
    _envejecer(store)       # fix2 (E5): fuera de la gracia «en curso»
    _escribir_config(tmp_path, cfg)
    assert rec.comprobar_indice(str(store)) == []
    ok = _cli("index", "check", "--project-root", raiz)
    assert ok.returncode == 0 and "OK" in ok.stdout, ok.stderr
    ruta = os.path.join(str(store), "cases_index.jsonl")
    lineas = open(ruta, encoding="utf-8").read().splitlines()
    fantasma = dict(json.loads(lineas[0]), version=9)
    alterada = dict(json.loads(lineas[1]), status="approved")
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(fantasma) + "\n" + json.dumps(alterada) + "\n")   # v001 falta, v002 alterada
    difs = rec.comprobar_indice(str(store))
    texto = "\n".join(difs)
    assert "geo-ramp.steep@v001" in texto and "geo-ramp.steep@v009" in texto and "geo-ramp.steep@v002" in texto
    assert "status" in texto
    r = _cli("index", "check", "--project-root", raiz)
    assert r.returncode == 1 and "v009" in (r.stdout + r.stderr) and "v001" in (r.stdout + r.stderr)
    assert _cli("index", "rebuild", "--project-root", raiz).returncode == 0
    assert _cli("index", "check", "--project-root", raiz).returncode == 0


def test_t06_index_lineas_corruptas_se_ignoran_con_aviso_y_check_las_reporta(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    _escribir_config(tmp_path, cfg)
    ruta = os.path.join(str(store), "cases_index.jsonl")
    buena = json.loads(open(ruta, encoding="utf-8").read())
    malas = ["{no es json", "[1, 2]", json.dumps({"case_id": 1}), json.dumps(dict(buena, extra=1)),
             json.dumps(dict(buena, status="gold")), json.dumps(dict(buena, version=True)),
             "[" * 5000 + "]" * 5000]
    with open(ruta, "a", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(malas) + "\n\n")
    entradas, avisos = rec.leer_indice(str(store))
    assert list(entradas) == [("geo-ramp.steep", 1)]
    assert len(avisos) == len(malas) and all("linea" in a for a in avisos)
    difs = rec.comprobar_indice(str(store))
    assert sum("linea" in d for d in difs) == len(malas)
    r = _cli("list", "--project-root", raiz)
    assert r.returncode == 0 and "Traceback" not in r.stderr and "geo-ramp.steep@v001" in r.stdout
    assert "aviso" in r.stderr
    r = _cli("index", "check", "--project-root", raiz)
    assert r.returncode == 1 and "Traceback" not in r.stderr and "linea 2" in (r.stdout + r.stderr)
    rec.reconstruir_indice(str(store))
    assert rec.comprobar_indice(str(store)) == []


def test_t06_index_list_filtra_por_status_family_y_outcome(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(outcome="failure"), cfg, raiz)
    rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg, raiz)
    rec.grabar(_caso(outcome="corrected", supersedes_case="geo-ramp.steep@v001"), cfg, raiz)
    rec.cambiar_estado("geo-ramp.steep", 2, "approved", cfg, raiz, approved_by_human=True)
    rec.grabar(_caso(family="stairs", variant="short", case_id="geo-stairs.short", outcome="success"), cfg, raiz)
    refs = lambda es: [(e["case_id"], e["version"]) for e in es]   # noqa: E731
    assert refs(rec.listar(str(store))) == [("geo-ramp.steep", 1), ("geo-ramp.steep", 2), ("geo-stairs.short", 1)]
    assert refs(rec.listar(str(store), status="approved")) == [("geo-ramp.steep", 2)]
    assert refs(rec.listar(str(store), family="stairs")) == [("geo-stairs.short", 1)]
    assert refs(rec.listar(str(store), outcome="failure")) == [("geo-ramp.steep", 1)]
    assert refs(rec.listar(str(store), status="pending", family="ramp")) == []
    _escribir_config(tmp_path, cfg)
    r = _cli("list", "--status", "approved", "--json", "--project-root", raiz)
    assert r.returncode == 0, r.stderr
    datos = json.loads(r.stdout)
    assert [(d["case_id"], d["version"], d["status"]) for d in datos] == [("geo-ramp.steep", 2, "approved")]
    assert tuple(datos[0]) == CLAVES_INDICE
    r = _cli("list", "--outcome", "corrected", "--project-root", raiz)
    assert r.returncode == 0 and r.stdout.strip().splitlines()[0].startswith("geo-ramp.steep@v002")
    assert _cli("list", "--status", "gold", "--project-root", raiz).returncode == 2
    # store que aun no existe: lista vacia, sin avisos
    assert rec.listar(str(tmp_path / "no-hay-store")) == []
    assert rec.leer_indice(str(tmp_path / "no-hay-store")) == ({}, [])


def test_t06_index_concurrencia_ninguna_linea_se_pierde(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    n = 12
    barrera = threading.Barrier(n)
    errores = []

    def graba(i):
        barrera.wait()
        try:
            rec.grabar(_caso(request=f"peticion {i}"), cfg, raiz)
        except Exception as e:   # noqa: BLE001
            errores.append(e)

    hilos = [threading.Thread(target=graba, args=(i,)) for i in range(n)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    assert not errores
    entradas, avisos = rec.leer_indice(str(store))
    assert avisos == [] and sorted(v for _c, v in entradas) == list(range(1, n + 1))
    assert rec.comprobar_indice(str(store)) == []


def test_t06_index_rebuild_conserva_updated_at_e_ignora_versiones_a_medias(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg, raiz)
    ultima = _indice(store)[-1]
    val = store / "cases" / "ramp.steep" / "v001" / "validation.json"
    os.utime(str(val), (1_000_000_000, 1_000_000_000))                 # mtime (2001) != updated_at
    (store / "cases" / "ramp.steep" / "v002").mkdir()                   # a medio escribir
    _envejecer(store, solo_dirs=True)   # fix2 (E5): interrumpida hace rato, no «en curso»
    n, avisos = rec.reconstruir_indice(str(store))
    assert n == 1 and any("v002" in a for a in avisos)
    assert _indice(store) == [ultima]                                     # updated_at conservado
    # fix1 Fase 2 (gap #37): una version incompleta es una incoherencia que `check` reporta
    difs = rec.comprobar_indice(str(store))
    assert difs and all("v002" in d for d in difs), difs


def test_t06_index_reconstruye_el_ejemplo_de_assets(tmp_path):
    """El ejemplo documentado es coherente (check vacio) y reconstruirlo da las mismas ultimas lineas."""
    assert rec.comprobar_indice(ASSETS_EJEMPLO) == []
    copia = tmp_path / "ejemplo"
    shutil.copytree(ASSETS_EJEMPLO, str(copia))
    esperado = _ultimas(_indice(copia))
    os.remove(os.path.join(str(copia), "cases_index.jsonl"))
    assert rec.reconstruir_indice(str(copia))[0] == 2
    assert _ultimas(_indice(copia)) == esperado
    assert [l["updated_at"] for l in _indice(copia)] and all(l["updated_at"].endswith("Z") for l in _indice(copia))


def test_t06_index_cli_sin_config_rechaza(tmp_path):
    raiz, _cfg, _store = _proyecto(tmp_path)
    for args in (("index", "check"), ("index", "rebuild"), ("list",)):
        r = _cli(*args, "--project-root", raiz)
        assert r.returncode == 1 and "training.json" in r.stderr, args
    assert _cli("index", "borrar", "--project-root", raiz).returncode == 2


def test_t06_index_el_bloqueo_excluye_a_otro_escritor(tmp_path):
    """Deterministico: mientras un escritor tiene el bloqueo del indice, otro `anadir_al_indice`
    espera (el append de Windows no es atomico entre descriptores); al soltarlo, escribe."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    entrada = _indice(store)[0]
    hecho = threading.Event()

    def otro():
        rec.anadir_al_indice(str(store), dict(entrada, status="rejected"))
        hecho.set()

    # fix3 (F2): `anadir_al_indice` valida la entrada contra el disco: la W de un `set-status rejected`
    val = store / "cases" / "ramp.steep" / "v001" / "validation.json"
    val.write_text(json.dumps({"status": "rejected", "approved_by_human": False, "approved_at": None,
                               "reviewer_note": None}), encoding="utf-8")

    with rec._Bloqueo(str(store)) as b:
        assert b.tomado
        h = threading.Thread(target=otro)
        h.start()
        assert not hecho.wait(0.5), "escribio sin esperar al bloqueo"
    h.join(10)
    assert hecho.is_set() and [l["status"] for l in _indice(store)] == ["pending", "rejected"]


def test_t06_index_rebuild_reintenta_replace_ante_bloqueo_transitorio(tmp_path, monkeypatch):
    """Windows: un handle ajeno (antivirus) puede dar `PermissionError` un instante al sustituir
    el indice; se reintenta de forma acotada. Otro `OSError` no se reintenta."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    real, fallos = os.replace, []

    def intermitente(a, b):
        if len(fallos) < 3:
            fallos.append(a)
            raise PermissionError(13, "en uso por otro proceso")
        return real(a, b)

    monkeypatch.setattr(rec.os, "replace", intermitente)
    assert rec.reconstruir_indice(str(store))[0] == 1 and len(fallos) == 3
    monkeypatch.setattr(rec.os, "replace", lambda a, b: (_ for _ in ()).throw(OSError(28, "disco lleno")))
    with pytest.raises(OSError):
        rec.reconstruir_indice(str(store))
    monkeypatch.setattr(rec.os, "replace", real)
    assert rec.comprobar_indice(str(store)) == []


# ------------------------------------------------------------------ fix1 (revision intento 1, Fase 2)

import builtins

FLAGS_NO_HUMANOS = ("false", "no", 1, [0], None, "true", "si")


def _enlazar_dir(objetivo, enlace):
    """Enlace de DIRECTORIO real: junction en Windows (no pide privilegios), symlink en POSIX."""
    os.makedirs(str(objetivo), exist_ok=True)
    try:
        if os.name == "nt":
            import _winapi
            _winapi.CreateJunction(str(objetivo), str(enlace))
        else:
            os.symlink(str(objetivo), str(enlace), target_is_directory=True)
    except (OSError, AttributeError, NotImplementedError) as e:   # pragma: no cover - entorno
        pytest.skip(f"no se puede crear un enlace de directorio: {e}")


def test_f2fix1_gap31_grabar_exige_flag_is_true_no_truthy(tmp_path):
    """gap #31: `grabar` usa la MISMA puerta que `cambiar_estado` (`flag is True`)."""
    raiz, cfg, store = _proyecto(tmp_path)
    gold = _caso(validation={"status": "approved", "approved_by_human": False})
    for flag in FLAGS_NO_HUMANOS:
        with pytest.raises(rec.Rechazo) as e:
            rec.grabar(gold, cfg, raiz, approved_by_human=flag)
        assert rec.MENSAJE_GOLD in str(e.value), flag
    assert not (store / "cases").exists()
    assert rec.grabar(gold, cfg, raiz, approved_by_human=True)["version"] == 1


def test_f2fix1_gap31_cambiar_estado_misma_puerta(tmp_path):
    raiz, cfg, _store, r = _grabado(tmp_path)
    antes = open(os.path.join(r["path"], "validation.json"), "rb").read()
    for flag in FLAGS_NO_HUMANOS:
        with pytest.raises(rec.Rechazo) as e:
            rec.cambiar_estado("geo-ramp.steep", 1, "approved", cfg, raiz, approved_by_human=flag)
        assert rec.MENSAJE_GOLD in str(e.value), flag
    assert open(os.path.join(r["path"], "validation.json"), "rb").read() == antes
    assert rec.es_confirmacion_humana(True) is True
    assert not any(rec.es_confirmacion_humana(f) for f in FLAGS_NO_HUMANOS)


def test_f2fix1_gap32_cot_en_arguments_texto_no_se_cuela_al_redactar(tmp_path):
    """gap #32 (escenario literal): el patron `pwd=` se comia la `\\` de `\\"`, el JSON dejaba de
    parsear y el validador lo trataba como opaco: el `reasoning` llegaba a disco."""
    raiz, cfg, store = _proyecto(tmp_path)
    args = json.dumps({"cmd": 'echo pwd=abcd1234" && ls', "reasoning": "pienso en voz alta"})
    assert rec.cs.validar_caso(_caso(version=1, trajectory=[
        {"role": "assistant", "tool_calls": [{"name": "sh", "arguments": args}]}]), cfg)   # sin redactar: se rechaza
    tr = copy.deepcopy(CASO["trajectory"])
    tr[1]["tool_calls"][0]["arguments"] = args
    with pytest.raises(rec.Rechazo) as e:
        rec.grabar(_caso(trajectory=tr), cfg, raiz)
    assert any("reasoning" in x["campo"] for x in e.value.errores)
    assert not store.exists()


def test_f2fix1_gap32_arguments_texto_json_se_redacta_como_estructura(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    tr = copy.deepcopy(CASO["trajectory"])
    tr[1]["tool_calls"][0]["arguments"] = json.dumps({"cmd": 'echo pwd=abcd1234" && ls', "n": 3})
    r = rec.grabar(_caso(trajectory=tr), cfg, raiz)
    grabada = _jsonl(os.path.join(r["path"], "trajectory.jsonl"))
    args = json.loads(grabada[1]["tool_calls"][0]["arguments"])     # sigue siendo JSON valido
    assert args["n"] == 3 and rec.REDACTADO in args["cmd"] and "abcd1234" not in args["cmd"]
    assert b"abcd1234" not in _bytes_del_store(str(store))
    # un `arguments` de texto que NO es JSON se redacta como texto; uno sin secretos no cambia
    tr[1]["tool_calls"][0]["arguments"] = "no es json token=abc123XYZ789"
    r = rec.grabar(_caso(trajectory=tr), cfg, raiz)
    assert "abc123XYZ789" not in _jsonl(os.path.join(r["path"], "trajectory.jsonl"))[1]["tool_calls"][0]["arguments"]
    limpio = '{"a":  1}'
    tr[1]["tool_calls"][0]["arguments"] = limpio
    r = rec.grabar(_caso(trajectory=tr), cfg, raiz)
    assert _jsonl(os.path.join(r["path"], "trajectory.jsonl"))[1]["tool_calls"][0]["arguments"] == limpio


def test_f2fix1_gap32_se_valida_el_original_y_el_redactado(tmp_path, monkeypatch):
    """Basta que falle UNO de los dos (original o redactado) para rechazar; y el error del original
    no filtra el secreto por stderr."""
    raiz, cfg, store = _proyecto(tmp_path)
    tr = copy.deepcopy(CASO["trajectory"])
    tr[1]["reasoning token=abc123XYZ789"] = "x"
    with pytest.raises(rec.Rechazo) as e:
        rec.grabar(_caso(trajectory=tr), cfg, raiz)
    assert "abc123XYZ789" not in str(e.value) and "abc123XYZ789" not in repr(e.value.errores)
    real = rec._redactar_caso
    monkeypatch.setattr(rec, "_redactar_caso", lambda c: dict(real(c), trajectory=[]))
    with pytest.raises(rec.Rechazo) as e:
        rec.grabar(_caso(), cfg, raiz)
    assert "trajectory" in {x["campo"] for x in e.value.errores}
    # y al reves: una redaccion que ENMASCARA el chain-of-thought (hoy ningun patron de redact.py lo
    # hace; el arbitraje exige no depender de ello) no lo cuela: el ORIGINAL ya se rechaza
    tr = copy.deepcopy(CASO["trajectory"])
    tr[1]["reasoning"] = "pienso en voz alta"
    limpia = copy.deepcopy(CASO["trajectory"])
    monkeypatch.setattr(rec, "_redactar_caso", lambda c: dict(real(c), trajectory=limpia))
    with pytest.raises(rec.Rechazo) as e:
        rec.grabar(_caso(trajectory=tr), cfg, raiz)
    assert "trajectory[1].reasoning" in {x["campo"] for x in e.value.errores}
    assert not store.exists()


def test_f2fix1_gap33_rebuild_lee_y_escribe_bajo_el_mismo_bloqueo(tmp_path, monkeypatch):
    """gap #33a (determinista): un `set-status` que llega mientras `rebuild` ya ha leido `cases/`
    no se pierde: espera al bloqueo y su linea queda DESPUES del indice reconstruido."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    original, hilo = rec.estado_de_cases, {}

    def espia(*a, **k):
        res = original(*a, **k)
        if "t" not in hilo:
            hilo["t"] = threading.Thread(target=rec.cambiar_estado, args=("geo-ramp.steep", 1, "rejected", cfg, raiz))
            hilo["t"].start()
            hilo["t"].join(0.5)
        return res

    monkeypatch.setattr(rec, "estado_de_cases", espia)
    rec.reconstruir_indice(str(store))
    hilo["t"].join(15)
    assert not hilo["t"].is_alive()
    monkeypatch.setattr(rec, "estado_de_cases", original)
    assert rec.comprobar_indice(str(store)) == []
    assert [e["status"] for e in rec.listar(str(store))] == ["rejected"]


_TRABAJADOR = r"""
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("rec_proc", sys.argv[1])
r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
cfg, raiz, papel, n, nv = json.loads(sys.argv[2]), sys.argv[3], sys.argv[4], int(sys.argv[5]), int(sys.argv[6])
store, fallos = r.raiz_store(cfg, raiz), []
for i in range(n):
    try:
        if papel.startswith("w"):
            r.cambiar_estado("geo-ramp.steep", int(papel[1:]), ("rejected", "needs_changes", "pending")[i % 3], cfg, raiz)
        elif papel == "rebuild":
            k, avisos = r.reconstruir_indice(store)
            if avisos or k != nv:
                fallos.append(f"rebuild {k}/{nv} {avisos}")
        else:
            ent, avisos = r.estado_de_cases(store)
            if avisos or len(ent) != nv:
                fallos.append(f"lector {len(ent)}/{nv} {avisos}")
    except Exception as e:
        fallos.append(f"{papel}: {type(e).__name__}: {e}")
print(json.dumps(fallos))
"""


def test_f2fix1_gap33_procesos_reales_set_status_rebuild_y_lectores(tmp_path):
    """gap #33 con PROCESOS reales (acotado: 3 escritores x 24 cambios, 2 `rebuild` x 24, 2 lectores
    x 48). Veredicto determinista sobre el invariante: ningun proceso ve una version completa como
    ilegible o a medio escribir, ningun `set-status` se rechaza, y al final el indice == `cases/`."""
    raiz, cfg, store = _proyecto(tmp_path)
    nv = 3
    for _ in range(nv):
        rec.grabar(_caso(), cfg, raiz)
    papeles = [("w1", 24), ("w2", 24), ("w3", 24), ("rebuild", 24), ("rebuild", 24), ("lector", 48), ("lector", 48)]
    procs = [subprocess.Popen([sys.executable, "-c", _TRABAJADOR, RECORDER_PATH, json.dumps(cfg), raiz, p, str(n), str(nv)],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE) for p, n in papeles]
    salidas = [p.communicate(timeout=300) for p in procs]
    assert all(p.returncode == 0 for p in procs), [s[1][-400:] for s in salidas]
    fallos = [f for s in salidas for f in json.loads(s[0])]
    assert fallos == [], fallos[:5]
    assert rec.comprobar_indice(str(store)) == []
    for e in rec.listar(str(store)):
        val = _json(store / "cases" / "ramp.steep" / f"v{e['version']:03d}" / "validation.json")
        assert e["status"] == val["status"]


def test_f2fix1_gap33_lector_reintenta_ante_permissionerror_transitorio(tmp_path, monkeypatch):
    """gap #33b: un `PermissionError` al abrir (Windows, `os.replace` ajeno) se reintenta de forma
    acotada; una version completa nunca se da por «a medio escribir» por eso."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    real_open, fallos = builtins.open, []

    def intermitente(ruta, *a, **k):
        if str(ruta).endswith("validation.json") and len(fallos) < 3:
            fallos.append(ruta)
            raise PermissionError(13, "en uso por otro proceso")
        return real_open(ruta, *a, **k)

    monkeypatch.setattr(rec, "open", intermitente, raising=False)
    monkeypatch.setattr(rec.time, "sleep", lambda _s: None)
    entradas, avisos = rec.estado_de_cases(str(store))
    assert len(fallos) == 3 and avisos == [] and list(entradas) == [("geo-ramp.steep", 1)]
    fallos.clear()
    assert rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg, raiz)["status"] == "rejected"
    assert len(fallos) == 3


def test_f2fix1_gap33_ilegible_transitorio_no_es_a_medio_escribir(tmp_path, monkeypatch):
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    (store / "cases" / "ramp.steep" / "v002").mkdir()
    _envejecer(store, solo_dirs=True)   # fix2 (E5): interrumpida hace rato, no «en curso»
    real_open = builtins.open

    def bloqueado(ruta, *a, **k):
        if str(ruta).endswith("validation.json"):
            raise PermissionError(13, "en uso por otro proceso")
        return real_open(ruta, *a, **k)

    monkeypatch.setattr(rec, "open", bloqueado, raising=False)
    monkeypatch.setattr(rec.time, "sleep", lambda _s: None)
    _e, avisos = rec.estado_de_cases(str(store))
    v1 = [a for a in avisos if "v001" in a]
    v2 = [a for a in avisos if "v002" in a]
    assert v1 and "bloqueada" in v1[0] and "a medio escribir" not in v1[0]
    assert v2 and "a medio escribir" in v2[0]


class _SinReadCompleto:
    def __init__(self, f):
        self._f = f

    def read(self, n=-1):
        if n is None or n < 0:
            raise AssertionError("read() completo del indice")
        return self._f.read(n)

    def __iter__(self):
        return iter(self._f)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return self._f.__exit__(*exc)

    def __getattr__(self, nombre):
        return getattr(self._f, nombre)


def test_f2fix1_gap34_list_lee_el_indice_una_vez_y_en_streaming(tmp_path, monkeypatch, capsys):
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg, raiz)
    with open(os.path.join(str(store), "cases_index.jsonl"), "a", encoding="utf-8", newline="\n") as f:
        f.write("{roto\n")
    _escribir_config(tmp_path, cfg)
    aperturas = []

    def espia(ruta, modo="r", *a, **k):
        f = builtins.open(ruta, modo, *a, **k)
        if os.path.basename(str(ruta)) == "cases_index.jsonl":
            aperturas.append(modo)
            return _SinReadCompleto(f)
        return f

    monkeypatch.setattr(rec, "open", espia, raising=False)
    assert rec.main(["list", "--project-root", raiz]) == 0
    salida = capsys.readouterr()
    assert len(aperturas) == 1, aperturas
    assert "geo-ramp.steep@v001  rejected" in salida.out and "linea 3 ignorada" in salida.err
    lista, avisos = rec.listar_con_avisos(str(store), status="rejected")
    assert [e["version"] for e in lista] == [1] and len(avisos) == 1


def test_f2fix1_gap35_validation_y_linea_del_indice_bajo_el_mismo_bloqueo(tmp_path, monkeypatch):
    """gap #35 (determinista): B no puede escribir+indexar entre la escritura y el append de A."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    real, hilo = rec._escribir_atomico, {}

    def espia(ruta, datos):
        real(ruta, datos)
        if ruta.endswith("validation.json") and "t" not in hilo:
            hilo["t"] = threading.Thread(target=rec.cambiar_estado, args=("geo-ramp.steep", 1, "rejected", cfg, raiz))
            hilo["t"].start()
            hilo["t"].join(0.5)

    monkeypatch.setattr(rec, "_escribir_atomico", espia)
    rec.cambiar_estado("geo-ramp.steep", 1, "approved", cfg, raiz, approved_by_human=True)
    hilo["t"].join(15)
    assert not hilo["t"].is_alive()
    val = _json(store / "cases" / "ramp.steep" / "v001" / "validation.json")
    assert val["status"] == "rejected"
    assert _indice(store)[-1]["status"] == "rejected"
    assert rec.comprobar_indice(str(store)) == []


def test_f2fix1_gap36_metadata_incompleto_se_rechaza_antes_de_escribir(tmp_path):
    raiz, cfg, store, r = _grabado(tmp_path)
    meta = os.path.join(r["path"], "metadata.json")
    m = _json(meta)
    del m["outcome"]
    with open(meta, "w", encoding="utf-8") as f:
        json.dump(m, f)
    val = os.path.join(r["path"], "validation.json")
    antes, indice = open(val, "rb").read(), open(os.path.join(str(store), "cases_index.jsonl"), "rb").read()
    with pytest.raises(rec.Rechazo) as e:
        rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg, raiz)
    assert "metadata.json" in str(e.value)
    assert open(val, "rb").read() == antes
    assert open(os.path.join(str(store), "cases_index.jsonl"), "rb").read() == indice
    _escribir_config(tmp_path, cfg)
    s = _cli("set-status", "geo-ramp.steep", "1", "rejected", "--project-root", raiz)
    assert s.returncode == 1 and "Traceback" not in s.stderr


def test_f2fix1_gap37_version_incompleta_es_incoherencia_y_se_salta(tmp_path, monkeypatch):
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    real = rec._reemplazar

    def falla_en_metadata(origen, destino):
        if destino.endswith("metadata.json"):
            raise OSError(28, "disco lleno")
        return real(origen, destino)

    monkeypatch.setattr(rec, "_reemplazar", falla_en_metadata)
    with pytest.raises(OSError):
        rec.grabar(_caso(), cfg, raiz)
    monkeypatch.setattr(rec, "_reemplazar", real)
    v2 = store / "cases" / "ramp.steep" / "v002"
    assert v2.is_dir() and not (v2 / "metadata.json").exists()        # se conserva (CA-02)
    _envejecer(store, solo_dirs=True)   # fix2 (E5): interrumpida hace rato, no «en curso»
    difs = rec.comprobar_indice(str(store))
    assert any("v002" in d and "incompleta" in d for d in difs), difs
    _escribir_config(tmp_path, cfg)
    r = _cli("index", "check", "--project-root", raiz)
    assert r.returncode == 1 and "v002" in (r.stdout + r.stderr)
    assert rec.grabar(_caso(), cfg, raiz)["version"] == 3              # la automatica la salta
    with pytest.raises(rec.Rechazo):
        rec.grabar(_caso(version=2), cfg, raiz)
    assert v2.is_dir()


def test_f2fix1_gap38_errores_de_e_s_y_version_enorme_sin_traceback(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    _escribir_config(tmp_path, cfg)
    store.write_text("soy un fichero, no un directorio", encoding="utf-8")
    caso = tmp_path / "caso.json"
    caso.write_text(json.dumps(_caso()), encoding="utf-8")
    for args in (("record", str(caso)), ("index", "rebuild")):
        r = _cli(*args, "--project-root", raiz)
        assert r.returncode == 2 and "Traceback" not in r.stderr and "error" in r.stderr, (args, r.stderr)
    store.unlink()
    rec.grabar(_caso(), cfg, raiz)
    enorme = "v" + "9" * 5000
    with pytest.raises(rec.Rechazo) as e:
        rec.cambiar_estado("geo-ramp.steep", enorme, "rejected", cfg, raiz)
    assert e.value.errores[0]["campo"] == "version"
    r = _cli("set-status", "geo-ramp.steep", enorme, "rejected", "--project-root", raiz)
    assert r.returncode == 1 and "Traceback" not in r.stderr
    for grande in (10 ** 12, 10 ** 5000):
        with pytest.raises(rec.Rechazo) as e:
            rec.grabar(_caso(version=grande), cfg, raiz)
        assert "version" in {x["campo"] for x in e.value.errores}


def test_f2fix1_gap39_supersedes_exige_failure_o_corrected(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(outcome="success"), cfg, raiz)
    with pytest.raises(rec.Rechazo) as e:
        rec.grabar(_caso(outcome="corrected", supersedes_case="geo-ramp.steep@v001"), cfg, raiz)
    assert "supersedes_case" in {x["campo"] for x in e.value.errores} and "success" in str(e.value)
    rec.grabar(_caso(outcome="failure"), cfg, raiz)                                           # v002
    rec.grabar(_caso(outcome="corrected", supersedes_case="geo-ramp.steep@v002"), cfg, raiz)   # v003
    assert rec.grabar(_caso(outcome="corrected", supersedes_case="geo-ramp.steep@v003"), cfg, raiz)["version"] == 4
    assert sorted(os.listdir(store / "cases" / "ramp.steep")) == ["v001", "v002", "v003", "v004"]


def test_f2fix1_gap40_mismo_numero_con_otro_ancho_se_rechaza(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)                                    # v001 (ancho 3)
    cfg4 = dict(cfg, ids={"version_width": 4})
    with pytest.raises(rec.Rechazo) as e:
        rec.grabar(_caso(version=1), cfg4, raiz)
    assert "existe" in str(e.value)
    assert rec.grabar(_caso(), cfg4, raiz)["ref"] == "geo-ramp.steep@v0002"
    assert sorted(os.listdir(store / "cases" / "ramp.steep")) == ["v0002", "v001"]
    shutil.copytree(str(store / "cases" / "ramp.steep" / "v001"), str(store / "cases" / "ramp.steep" / "v01"))
    difs = rec.comprobar_indice(str(store))
    assert any("duplicada" in d for d in difs), difs


def test_f2fix1_gap40_case_id_que_solo_difiere_en_mayusculas_se_rechaza(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path, family_pattern="^[A-Za-z0-9]+$")
    rec.grabar(_caso(), cfg, raiz)
    with pytest.raises(rec.Rechazo) as e:
        rec.grabar(_caso(family="RAMP", case_id="geo-RAMP.steep"), cfg, raiz)
    assert "mayusculas" in str(e.value)
    assert sorted(os.listdir(store / "cases")) == ["ramp.steep"]
    assert sorted(os.listdir(store / "cases" / "ramp.steep")) == ["v001"]


def test_f2fix1_gap41_nan_e_infinity_se_rechazan(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    for cambios, campo in (({"metrics": {"score": float("nan")}}, "metrics.score"),
                           ({"constraints": {"max": float("inf")}}, "constraints.max"),
                           ({"context": {"l": [1, float("-inf")]}}, "context.l[1]")):
        with pytest.raises(rec.Rechazo) as e:
            rec.grabar(_caso(**cambios), cfg, raiz)
        assert campo in {x["campo"] for x in e.value.errores}, e.value.errores
    assert not store.exists()
    with pytest.raises(ValueError):
        rec._json_bytes({"x": float("nan")})


def test_f2fix1_gap42_append_sobre_indice_sin_salto_final(tmp_path):
    raiz, cfg, store, _r = _grabado(tmp_path)
    ruta = os.path.join(str(store), "cases_index.jsonl")
    crudo = open(ruta, "rb").read()
    with open(ruta, "wb") as f:
        f.write(crudo.rstrip(b"\n"))
    rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg, raiz)
    entradas, avisos = rec.leer_indice(str(store))
    assert avisos == [] and len(_indice(store)) == 2 and entradas[("geo-ramp.steep", 1)]["status"] == "rejected"


def test_f2fix1_gap43_junction_dentro_del_store_hacia_docs_knowledge_se_rechaza(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    (store / "cases").mkdir(parents=True)
    aprobado = tmp_path / "proj" / "docs" / "knowledge" / "approved"
    _enlazar_dir(aprobado, store / "cases" / "ramp.steep")
    with pytest.raises(rec.Rechazo) as e:
        rec.grabar(_caso(), cfg, raiz)
    assert "enlace" in str(e.value)
    assert os.listdir(str(aprobado)) == []


def test_f2fix1_gap43_cases_enlazado_fuera_del_store_se_rechaza(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    store.mkdir()
    fuera = tmp_path / "fuera"
    _enlazar_dir(fuera, store / "cases")
    with pytest.raises(rec.Rechazo):
        rec.grabar(_caso(), cfg, raiz)
    assert os.listdir(str(fuera)) == []


def test_f2fix1_gap43_set_status_y_check_con_enlace(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    r = rec.grabar(_caso(), cfg, raiz)
    aprobado = tmp_path / "proj" / "docs" / "knowledge" / "approved"
    shutil.copytree(r["path"], str(aprobado / "v001"))
    m = _json(aprobado / "v001" / "metadata.json")
    m.update(family="stairs", variant="short", case_id="geo-stairs.short")
    (aprobado / "v001" / "metadata.json").write_text(json.dumps(m), encoding="utf-8")
    _enlazar_dir(aprobado, store / "cases" / "stairs.short")
    antes = (aprobado / "v001" / "validation.json").read_bytes()
    with pytest.raises(rec.Rechazo) as e:
        rec.cambiar_estado("geo-stairs.short", 1, "rejected", cfg, raiz)
    assert "enlace" in str(e.value)
    assert (aprobado / "v001" / "validation.json").read_bytes() == antes
    difs = rec.comprobar_indice(str(store), raiz_proyecto=raiz)
    # se omite el directorio del caso ENTERO, sin leer nada a traves del enlace
    # fix2 (E4): el lector detecta el enlace POR ENTRADA (sin resolverlo) y lo omite sea cual sea su destino
    assert [d for d in difs if "stairs.short" in d] == [f"cases/stairs.short omitido: {rec.MOTIVO_ENLACE}"], difs
    rec.reconstruir_indice(str(store), raiz_proyecto=raiz)
    assert [e["case_id"] for e in rec.listar(str(store))] == ["geo-ramp.steep"]


def test_f2fix1_gap43_indice_enlazado_fuera_se_rechaza(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    store.mkdir()
    fuera = tmp_path / "fuera.jsonl"
    fuera.write_text("", encoding="utf-8")
    try:
        os.symlink(str(fuera), str(store / "cases_index.jsonl"))
    except (OSError, NotImplementedError) as e:   # pragma: no cover - Windows sin privilegio
        pytest.skip(f"sin symlink de fichero: {e}")
    with pytest.raises(rec.Rechazo):
        rec.grabar(_caso(), cfg, raiz)
    assert fuera.read_text(encoding="utf-8") == "" and not (store / "cases").exists()


def test_f2fix1_gap44_todo_texto_libre_se_redacta(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    fugas = ["abc123XYZ789", "zzz999QQQ111", "kkk777MMM222", "ppp555NNN333", "qqq444RRR666", "ttt111UUU999"]
    caso = _caso(metrics={"score": 0.5, "nota": "token=" + fugas[0]},
                 artifacts=[{"path": "final/token=" + fugas[1], "hash": "sha256:ab12", "kind": "password=" + fugas[2]}],
                 created_at="2026-09-25 token=" + fugas[3],
                 validation={"status": "approved", "approved_by_human": False, "reviewer_note": "secret=" + fugas[4],
                             "approved_at": "2026-09-25 token=" + fugas[5]})
    r = rec.grabar(caso, cfg, raiz, approved_by_human=True)
    todo = _bytes_del_store(str(store))
    for fuga in fugas:
        assert fuga.encode() not in todo, fuga
    assert _json(os.path.join(r["path"], "final", "artifacts.json"))[0]["hash"] == "sha256:ab12"
    assert _json(os.path.join(r["path"], "metrics.json"))["score"] == 0.5
    rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg, raiz, reviewer_note="pwd=nota1234Secreta")
    _escribir_config(tmp_path, cfg)
    s = _cli("set-status", "geo-ramp.steep", "1", "needs_changes", "--note", "clave=cli9876Secreta", "--project-root", raiz)
    assert s.returncode == 0, s.stderr
    todo = _bytes_del_store(str(store))
    assert b"nota1234Secreta" not in todo and b"cli9876Secreta" not in todo


def test_f2fix1_gap45_validation_incoherente_no_se_indexa_como_gold(tmp_path):
    raiz, cfg, store, r = _grabado(tmp_path)
    with open(os.path.join(r["path"], "validation.json"), "w", encoding="utf-8") as f:
        json.dump({"status": "approved", "approved_by_human": False}, f)
    difs = rec.comprobar_indice(str(store))
    assert any("v001" in d and "validation.json" in d for d in difs), difs
    _escribir_config(tmp_path, cfg)
    assert _cli("index", "check", "--project-root", raiz).returncode == 1
    rec.reconstruir_indice(str(store))
    assert rec.listar(str(store), status="approved") == []


def test_f2fix1_gap46_versiones_con_scandir_sin_isdir_por_entrada(tmp_path, monkeypatch):
    raiz, cfg, store = _proyecto(tmp_path)
    for _ in range(12):
        rec.grabar(_caso(), cfg, raiz)
    llamadas = []
    real = os.path.isdir

    def contar_grabar():
        llamadas.clear()
        monkeypatch.setattr(rec.os.path, "isdir", lambda p: llamadas.append(p) or real(p))
        rec.grabar(_caso(), cfg, raiz)
        monkeypatch.setattr(rec.os.path, "isdir", real)
        return len(llamadas)

    monkeypatch.setattr(rec.os.path, "isdir", lambda p: llamadas.append(p) or real(p))
    assert rec.versiones(str(store / "cases" / "ramp.steep")) == list(range(1, 13))
    assert llamadas == []                                   # ni un isdir por entrada
    monkeypatch.setattr(rec.os.path, "isdir", real)
    con_13 = contar_grabar()                                # 12 versiones existentes
    for _ in range(12):
        rec.grabar(_caso(), cfg, raiz)
    assert contar_grabar() == con_13                        # 25 existentes: mismo coste en isdir


def test_f2fix1_gap48_ayuda_del_cli_dice_que_version_es_opcional():
    r = _cli("record", "--help")
    assert r.returncode == 0 and "sin `version`" in r.stdout


def test_f2fix1_gap50_m01_supersedes_rechaza_version_a_medio_escribir(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    (store / "cases" / "ramp.steep" / "v001").mkdir(parents=True)
    with pytest.raises(rec.Rechazo) as e:
        rec.grabar(_caso(outcome="corrected", supersedes_case="geo-ramp.steep@v001"), cfg, raiz)
    assert "supersedes_case" in {x["campo"] for x in e.value.errores}


def test_f2fix1_gap50_m02_metadata_se_mueve_la_ultima(tmp_path, monkeypatch):
    raiz, cfg, _store = _proyecto(tmp_path)
    real, orden = rec._reemplazar, []
    monkeypatch.setattr(rec, "_reemplazar", lambda o, d: orden.append(os.path.basename(d)) or real(o, d))
    rec.grabar(_caso(), cfg, raiz)
    assert orden[-1] == "metadata.json" and orden.count("metadata.json") == 1 and len(orden) == len(FICHEROS_VERSION)


def test_f2fix1_gap50_m03_version_sin_validation_json_no_admite_cambios(tmp_path):
    raiz, cfg, store, r = _grabado(tmp_path)
    os.remove(os.path.join(r["path"], "validation.json"))
    with pytest.raises(rec.Rechazo) as e:
        rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg, raiz)
    assert "medio escribir" in str(e.value)
    assert not os.path.exists(os.path.join(r["path"], "validation.json"))
    _n, avisos = rec.reconstruir_indice(str(store))
    assert any("v001" in a and "validation.json" in a for a in avisos), avisos


def test_f2fix1_gap50_m05_lineas_en_blanco_se_ignoran_sin_aviso(tmp_path):
    raiz, cfg, store, _r = _grabado(tmp_path)
    with open(os.path.join(str(store), "cases_index.jsonl"), "ab") as f:
        f.write(b"\n   \n\t\n")
    rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg, raiz)
    entradas, avisos = rec.leer_indice(str(store))
    assert avisos == [] and entradas[("geo-ramp.steep", 1)]["status"] == "rejected"
    assert rec.comprobar_indice(str(store)) == []


def test_f2fix1_gap50_m11_indice_no_escribible_da_aviso_no_excepcion(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    (store / "cases_index.jsonl").mkdir(parents=True)          # el indice no se puede abrir
    r = rec.grabar(_caso(), cfg, raiz)
    assert r["version"] == 1 and r["avisos"] and "index rebuild" in r["avisos"][0]
    assert (store / "cases" / "ramp.steep" / "v001" / "metadata.json").is_file()
    out = rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg, raiz)
    assert out["avisos"]


def test_f2fix1_gap50_m14_reintentos_acotados(tmp_path, monkeypatch):
    llamadas = []

    def siempre(*_a, **_k):
        llamadas.append(1)
        raise PermissionError(13, "en uso")

    monkeypatch.setattr(rec.time, "sleep", lambda _s: None)
    monkeypatch.setattr(rec.os, "replace", siempre)
    with pytest.raises(PermissionError):
        rec._reemplazar("a", "b")
    assert len(llamadas) == rec.REINTENTOS
    monkeypatch.undo()
    monkeypatch.setattr(rec.time, "sleep", lambda _s: None)
    llamadas.clear()
    monkeypatch.setattr(rec, "open", siempre, raising=False)
    with pytest.raises(PermissionError):
        rec._leer_json_reintentando(str(tmp_path / "x.json"))
    assert len(llamadas) == rec.REINTENTOS


def test_f2fix1_gap50_m15_rebuild_lee_dentro_del_bloqueo(tmp_path, monkeypatch):
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    estado = {"dentro": False}
    real_bloqueo = rec._Bloqueo

    class Espia(real_bloqueo):
        def __enter__(self):
            r = super().__enter__()
            estado["dentro"] = True
            return r

        def __exit__(self, *exc):
            estado["dentro"] = False
            return super().__exit__(*exc)

    # fix2 (D-fix2 §3/E3): el recorrido de `cases/` (F1) va SIN el bloqueo del indice pero SIEMPRE con
    # `.cases_rebuild.lock` (un rebuild a la vez). fix3 (D-fix3 §2 + F2): la cola se lee en pasadas
    # SIN el bloqueo del indice y el RESIDUAL (`hasta_eof`) con el
    tomados, _orden = _espia_de_bloqueos_por_nombre(monkeypatch)
    vistos = []
    real_estado, real_cola = rec.estado_de_cases, rec._leer_cola
    monkeypatch.setattr(rec, "estado_de_cases", lambda *a, **k: vistos.append(("cases", tuple(tomados))) or real_estado(*a, **k))
    monkeypatch.setattr(rec, "_leer_cola", lambda *a, **k: vistos.append(("residual" if k.get("hasta_eof") else "pasada",
                                                                          tuple(tomados))) or real_cola(*a, **k))
    rec.reconstruir_indice(str(store))
    assert ("cases", (rec.BLOQUEO_REBUILD,)) in vistos, vistos
    assert all(v[1][:1] == (rec.BLOQUEO_REBUILD,) for v in vistos), vistos
    assert ("pasada", (rec.BLOQUEO_REBUILD,)) in vistos, vistos
    assert ("residual", (rec.BLOQUEO_REBUILD, rec.BLOQUEO_INDICE)) in vistos, vistos


def test_f2fix1_gap51_sin_bloqueo_a_tiempo_falla_cerrado(tmp_path, monkeypatch, capsys):
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    _escribir_config(tmp_path, cfg)
    monkeypatch.setattr(rec, "ESPERA_BLOQUEO_S", 0.2)
    indice = open(os.path.join(str(store), "cases_index.jsonl"), "rb").read()
    caso = tmp_path / "caso.json"
    caso.write_text(json.dumps(_caso()), encoding="utf-8")
    with rec._Bloqueo(str(store)):
        with pytest.raises(rec.Rechazo) as e:
            rec.grabar(_caso(), cfg, raiz)
        assert "bloqueo" in str(e.value)
        with pytest.raises(rec.Rechazo):
            rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg, raiz)
        with pytest.raises(rec.Rechazo):
            rec.anadir_al_indice(str(store), _indice(store)[0])
        assert rec.main(["record", str(caso), "--project-root", raiz]) == 3   # fix2 (E2): transitorio, exit 3
    assert "bloqueo" in capsys.readouterr().err
    assert sorted(os.listdir(store / "cases" / "ramp.steep")) == ["v001"]
    assert _json(store / "cases" / "ramp.steep" / "v001" / "validation.json")["status"] == "pending"
    assert open(os.path.join(str(store), "cases_index.jsonl"), "rb").read() == indice


def test_f2fix1_gap40_directorio_de_otro_case_id_se_rechaza(tmp_path):
    """gap #40b: si el directorio del caso existe y su `metadata.case_id` es otro (p. ej. el
    `id_prefix` cambio), no se mezclan versiones de dos case_id."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    otro = dict(cfg, id_prefix="otro")
    with pytest.raises(rec.Rechazo) as e:
        rec.grabar(_caso(case_id="otro-ramp.steep"), otro, raiz)
    assert "pertenece a" in str(e.value)
    assert sorted(os.listdir(store / "cases" / "ramp.steep")) == ["v001"]


def test_f2fix1_gap43_store_en_la_raiz_del_proyecto_y_junction_a_docs_knowledge(tmp_path):
    """gap #43: con `root: "."` el enlace no sale del store, pero cae en `docs/knowledge/`."""
    raiz = str(tmp_path / "proj")
    os.makedirs(raiz)
    cfg = {"version": 1, "enabled": True, "root": ".", "id_prefix": "geo"}
    (tmp_path / "proj" / "cases").mkdir()
    aprobado = tmp_path / "proj" / "docs" / "knowledge" / "approved"
    _enlazar_dir(aprobado, tmp_path / "proj" / "cases" / "ramp.steep")
    with pytest.raises(rec.Rechazo) as e:
        rec.grabar(_caso(), cfg, raiz)
    assert "docs/knowledge" in str(e.value)
    assert os.listdir(str(aprobado)) == []


def test_f2fix1_gap43_se_recomprueba_tras_crear_temporal_y_destino(tmp_path, monkeypatch):
    """TOCTOU (gap #43): el temporal y el destino se comprueban DESPUES de crearlos, por si un
    enlace aparecio entre la primera comprobacion y la escritura."""
    raiz, cfg, _store = _proyecto(tmp_path)
    real, vistos = rec._comprobar_contencion, []

    def espia(store, rutas, raiz_proyecto=None):
        vistos.extend((os.path.basename(r), os.path.isdir(r)) for r in rutas)
        return real(store, rutas, raiz_proyecto)

    monkeypatch.setattr(rec, "_comprobar_contencion", espia)
    rec.grabar(_caso(), cfg, raiz)
    assert any(n.startswith(rec.PREFIJO_TEMPORAL) and existe for n, existe in vistos), vistos
    assert ("v001", True) in vistos, vistos


def test_f2fix1_gap43_version_enlazada_fuera_se_omite_en_check_y_rebuild(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    r = rec.grabar(_caso(), cfg, raiz)
    fuera = tmp_path / "fuera" / "v002"
    shutil.copytree(r["path"], str(fuera))
    m = _json(fuera / "metadata.json")
    m["version"] = 2
    (fuera / "metadata.json").write_text(json.dumps(m), encoding="utf-8")
    _enlazar_dir(fuera, store / "cases" / "ramp.steep" / "v002")
    difs = rec.comprobar_indice(str(store))
    assert any("v002" in d and "enlace" in d for d in difs), difs
    n, avisos = rec.reconstruir_indice(str(store))
    assert n == 1 and any("v002" in a and "enlace" in a for a in avisos)
    with pytest.raises(rec.Rechazo):
        rec.cambiar_estado("geo-ramp.steep", 2, "rejected", cfg, raiz)


def _espia_de_bloqueo(monkeypatch):
    estado = {"dentro": 0}

    class Espia(rec._Bloqueo):
        def __enter__(self):
            r = super().__enter__()
            estado["dentro"] += 1
            return r

        def __exit__(self, *exc):
            estado["dentro"] -= 1
            return super().__exit__(*exc)

    monkeypatch.setattr(rec, "_Bloqueo", Espia)
    return estado


def test_f2fix1_gap35_escritura_y_append_con_el_bloqueo_tomado(tmp_path, monkeypatch):
    """gap #35 (determinista): `validation.json` y su linea del indice se escriben DENTRO del
    bloqueo, en `cambiar_estado` y en `grabar` (la version entera y su alta)."""
    raiz, cfg, _store = _proyecto(tmp_path)
    estado, vistos = _espia_de_bloqueo(monkeypatch), []
    real_ind, real_atom, real_rep = rec._indexar, rec._escribir_atomico, rec._reemplazar
    monkeypatch.setattr(rec, "_indexar", lambda *a: vistos.append(("indice", estado["dentro"])) or real_ind(*a))
    monkeypatch.setattr(rec, "_escribir_atomico", lambda *a: vistos.append(("validation", estado["dentro"])) or real_atom(*a))
    monkeypatch.setattr(rec, "_reemplazar", lambda *a: vistos.append(("version", estado["dentro"])) or real_rep(*a))
    rec.grabar(_caso(), cfg, raiz)
    en_grabar = list(vistos)
    vistos.clear()
    rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg, raiz)
    # fix2 (D-fix2 E1): `grabar` MUEVE la version sin el bloqueo (W) y su linea (S2) va con el;
    # `set-status` sigue escribiendo `validation.json` (con su `os.replace`) y su linea con el bloqueo
    assert {q for q, _d in en_grabar} == {"indice", "version"} and {q for q, _d in vistos} == {"indice", "validation", "version"}
    assert all(d == 0 for q, d in en_grabar if q == "version") and [d for q, d in en_grabar if q == "indice"] == [1], en_grabar
    assert all(d == 1 for _q, d in vistos), vistos


# ------------------------------------------------------------------ fix2 (revision intento 2, Fase 2)
# Diseno D-fix2 con las enmiendas E1-E6 (tasks.md, «Revision de dos lentes — intento 2: Fase 2»).

import stat
import time

SKILL_MD = os.path.normpath(os.path.join(HERE, "..", "SKILL.md"))


def _envejecer(store, solo_dirs=False, segundos=3600):
    """Pone el `mtime` de las versiones (directorios y, si no `solo_dirs`, su `metadata.json`) una
    hora atras: fuera de la gracia «en curso» de `index check` (E5)."""
    viejo = time.time() - segundos
    for base, _dirs, fs in os.walk(os.path.join(str(store), "cases")):
        for f in fs if not solo_dirs else ():
            if f == "metadata.json":
                os.utime(os.path.join(base, f), (viejo, viejo))
        if os.path.basename(base).startswith("v"):
            os.utime(base, (viejo, viejo))


def _esperar(ruta, proc, t=60):
    """Espera ACOTADA a que aparezca `ruta` (o a que `proc` termine): nunca cuelga el test."""
    limite = time.monotonic() + t
    while time.monotonic() < limite:
        if os.path.exists(str(ruta)):
            return True
        if proc is not None and proc.poll() is not None:
            return False
        time.sleep(0.01)
    return False


# Proceso real que graba y se PARA justo despues de W (la version ya en disco, antes de S2).
_PAUSA_TRAS_W = r"""
import importlib.util, os, sys, time
spec = importlib.util.spec_from_file_location("rec_proc", sys.argv[1])
r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
senal, seguir = sys.argv[2], sys.argv[3]
r.ESPERA_BLOQUEO_S = float(sys.argv[4])
real = r._mover_version
def pausa(*a, **k):
    res = real(*a, **k)
    open(senal, "w").close()
    limite = time.monotonic() + 60
    while not os.path.exists(seguir):
        if time.monotonic() > limite:
            os._exit(7)
        time.sleep(0.01)
    return res
r._mover_version = pausa
sys.exit(r.main(sys.argv[5:]))
"""


def _lanzar_pausado(tmp_path, espera, *args):
    senal, seguir = tmp_path / "w_hecho", tmp_path / "seguir"
    p = subprocess.Popen([sys.executable, "-c", _PAUSA_TRAS_W, RECORDER_PATH, str(senal), str(seguir), str(espera), *args],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
    return p, senal, seguir


def test_f2fix2_gap52_e1_set_status_entre_w_y_a_gana_el_disco(tmp_path):
    """E6 (a), PROCESOS reales: `record` Gold se para tras W; un `set-status rejected` (otro proceso)
    entra entre W y A; la A de `record` relee `validation.json` en S2 e indexa ESE estado."""
    raiz, cfg, store = _proyecto(tmp_path)
    _escribir_config(tmp_path, cfg)
    gold = tmp_path / "gold.json"
    gold.write_text(json.dumps(_caso(validation={"status": "approved", "approved_by_human": True})), encoding="utf-8")
    p, senal, seguir = _lanzar_pausado(tmp_path, 10, "record", str(gold), "--project-root", raiz, "--approved-by-human")
    try:
        assert _esperar(senal, p), p.communicate(timeout=30)
        s = _cli("set-status", "geo-ramp.steep", "1", "rejected", "--project-root", raiz)
        assert s.returncode == 0, s.stderr
    finally:
        seguir.write_text("", encoding="utf-8")
    out, err = p.communicate(timeout=120)
    assert p.returncode == 0, err
    assert _json(store / "cases" / "ramp.steep" / "v001" / "validation.json")["status"] == "rejected"
    assert rec.listar(str(store), status="approved") == []
    assert _indice(store)[-1]["status"] == "rejected"
    assert rec.comprobar_indice(str(store)) == []
    ls = _cli("list", "--status", "approved", "--project-root", raiz)
    assert ls.returncode == 0 and ls.stdout.strip() == ""


def test_f2fix2_gap52_e2_timeout_tras_w_es_exit_0_con_aviso_y_el_reintento_no_duplica(tmp_path):
    """E6 (b), PROCESOS reales: el bloqueo no llega en S2 (la version YA esta grabada) -> exit 0 con
    aviso «index rebuild», nunca exit 3; quien reintenta SOLO ante exit 3 no duplica la version."""
    raiz, cfg, store = _proyecto(tmp_path)
    _escribir_config(tmp_path, cfg)
    caso = tmp_path / "caso.json"
    caso.write_text(json.dumps(_caso()), encoding="utf-8")
    p, senal, seguir = _lanzar_pausado(tmp_path, 0.3, "record", str(caso), "--project-root", raiz)
    assert _esperar(senal, p), p.communicate(timeout=30)
    with rec._Bloqueo(str(store)):
        seguir.write_text("", encoding="utf-8")
        out, err = p.communicate(timeout=120)
    intentos = [p.returncode]
    while intentos[-1] == 3 and len(intentos) < 3:        # politica de quien llama: reintentar solo ante 3
        intentos.append(_cli("record", str(caso), "--project-root", raiz).returncode)
    assert intentos == [0], (intentos, err)
    assert "index rebuild" in err and json.loads(out)["version"] == 1
    assert sorted(os.listdir(store / "cases" / "ramp.steep")) == ["v001"]
    difs, en_curso = rec.comprobar_indice_detalle(str(store))
    assert difs == [] and any("v001" in e for e in en_curso), (difs, en_curso)
    rec.reconstruir_indice(str(store))
    assert rec.comprobar_indice(str(store)) == []


_GRABADOR = r"""
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("rec_proc", sys.argv[1])
r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
cfg, raiz, n, etiqueta = json.loads(sys.argv[2]), sys.argv[3], int(sys.argv[4]), sys.argv[5]
caso = json.loads(sys.stdin.read())
fallos = []
for i in range(n):
    try:
        res = r.grabar(dict(caso, request=f"{etiqueta}-{i}"), cfg, raiz)
        if res["avisos"]:
            fallos.append(res["avisos"])
    except Exception as e:
        fallos.append(f"{type(e).__name__}: {e}")
print(json.dumps(fallos))
"""


def test_f2fix2_gap52_procesos_reales_record_sin_rechazos(tmp_path):
    """#52 con PROCESOS reales (acotado: 8 x 6 `record`): ningun rechazo ni aviso, versiones 1..48
    sin huecos, cada peticion en su version, e indice == `cases/` al final."""
    raiz, cfg, store = _proyecto(tmp_path)
    procs = [subprocess.Popen([sys.executable, "-c", _GRABADOR, RECORDER_PATH, json.dumps(cfg), raiz, "6", f"p{k}"],
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                              encoding="utf-8") for k in range(8)]
    salidas = [p.communicate(json.dumps(_caso()), timeout=300) for p in procs]
    assert all(p.returncode == 0 for p in procs), [s[1][-400:] for s in salidas]
    fallos = [f for s in salidas for f in json.loads(s[0])]
    assert fallos == [], fallos[:5]
    base = store / "cases" / "ramp.steep"
    assert sorted(os.listdir(base)) == [f"v{v:03d}" for v in range(1, 49)]
    peticiones = {_json(base / f"v{v:03d}" / "request.json")["request"] for v in range(1, 49)}
    assert peticiones == {f"p{k}-{i}" for k in range(8) for i in range(6)}
    assert rec.comprobar_indice(str(store)) == []


def test_f2fix2_gap52_record_mueve_la_version_sin_el_bloqueo_s1_y_s2_cortas(tmp_path, monkeypatch):
    """E1 (determinista): `record` toma el bloqueo DOS veces — S1 (reserva `mkdir`) y S2 (relee
    `validation.json` + linea) — y mueve los ficheros de la version SIN el."""
    raiz, cfg, _store = _proyecto(tmp_path)
    estado, vistos = _espia_de_bloqueo(monkeypatch), []
    entradas = []
    real_enter = rec._Bloqueo.__enter__

    def contar(self):
        entradas.append(os.path.basename(self.ruta))
        return real_enter(self)

    monkeypatch.setattr(rec._Bloqueo, "__enter__", contar)
    real_rep, real_lin, real_mkdir = rec._reemplazar, rec._anadir_linea, os.mkdir
    real_leer = rec._leer_json_reintentando
    monkeypatch.setattr(rec, "_reemplazar", lambda o, d: vistos.append(("mover", estado["dentro"])) or real_rep(o, d))
    monkeypatch.setattr(rec, "_anadir_linea", lambda *a: vistos.append(("linea", estado["dentro"])) or real_lin(*a))
    monkeypatch.setattr(rec.os, "mkdir", lambda p, *a, **k: vistos.append(("mkdir " + os.path.basename(p), estado["dentro"]))
                        or real_mkdir(p, *a, **k))
    monkeypatch.setattr(rec, "_leer_json_reintentando",
                        lambda ruta, *a: vistos.append(("leer " + os.path.basename(ruta), estado["dentro"])) or real_leer(ruta, *a))
    rec.grabar(_caso(), cfg, raiz)
    assert entradas == [rec.BLOQUEO_INDICE, rec.BLOQUEO_INDICE], entradas
    assert ("mkdir v001", 1) in vistos, vistos
    assert all(d == 0 for q, d in vistos if q == "mover") and any(q == "mover" for q, _d in vistos), vistos
    assert [d for q, d in vistos if q == "linea"] == [1], vistos
    ultimo_mover = max(i for i, (q, _d) in enumerate(vistos) if q == "mover")
    assert ("leer validation.json", 1) in vistos[ultimo_mover:], vistos      # S2 relee el disco


def test_f2fix2_gap52_bloqueo_no_disponible_es_exit_3_y_no_escribe(tmp_path, monkeypatch, capsys):
    """E2: `BloqueoNoDisponible` (S1 de `record`, `set-status`, F0/F2 de `rebuild`) -> exit 3
    «transitorio: reintenta», distinto de 1 (rechazo) y 2 (uso/E/S); no se escribe nada."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    _escribir_config(tmp_path, cfg)
    monkeypatch.setattr(rec, "ESPERA_BLOQUEO_S", 0.2)
    caso = tmp_path / "caso.json"
    caso.write_text(json.dumps(_caso()), encoding="utf-8")
    malo = tmp_path / "malo.json"
    malo.write_text(json.dumps(_caso(outcome="meh")), encoding="utf-8")
    rec.reconstruir_indice(str(store))                  # los dos ficheros de bloqueo ya existen
    antes = sorted(_ficheros(str(store))), _bytes_del_store(str(store))
    capsys.readouterr()
    with rec._Bloqueo(str(store)):
        assert rec.main(["record", str(caso), "--project-root", raiz]) == 3
        assert rec.main(["set-status", "geo-ramp.steep", "1", "rejected", "--project-root", raiz]) == 3
        assert rec.main(["index", "rebuild", "--project-root", raiz]) == 3
        assert rec.main(["record", str(malo), "--project-root", raiz]) == 1      # rechazo: antes del bloqueo
    err = capsys.readouterr().err
    assert err.count("reintenta") >= 3
    assert (sorted(_ficheros(str(store))), _bytes_del_store(str(store))) == antes
    assert issubclass(rec.BloqueoNoDisponible, rec.Transitorio) and issubclass(rec.Transitorio, rec.Rechazo)


def test_f2fix2_gap52_espera_con_retroceso_exponencial_y_jitter(tmp_path, monkeypatch):
    """E2/§4: el sondeo del bloqueo espera 5 ms, dobla hasta 50 ms, con jitter, y nunca pasa del limite."""
    store = tmp_path / "s"
    store.mkdir()
    esperas = []
    base = time.monotonic()
    with rec._Bloqueo(str(store)):
        monkeypatch.setattr(rec, "ESPERA_BLOQUEO_S", 1.0)
        monkeypatch.setattr(rec.time, "sleep", lambda s: esperas.append(s))
        monkeypatch.setattr(rec.time, "monotonic", lambda: base + sum(esperas))
        with pytest.raises(rec.BloqueoNoDisponible):
            rec._Bloqueo(str(store)).__enter__()
        monkeypatch.undo()
    assert esperas and esperas[0] <= rec.ESPERA_INICIAL_S + 1e-9
    assert max(esperas) <= rec.ESPERA_MAX_S + 1e-9 and max(esperas) > 4 * rec.ESPERA_INICIAL_S
    assert sum(esperas) <= 1.0 + 1e-9
    en_el_tope = esperas[5:-1]                         # tras 5 duplicaciones, sin la ultima (recortada al limite)
    assert len(en_el_tope) >= 10 and len({round(s, 6) for s in en_el_tope}) > 1   # jitter: no todas iguales


def _espia_de_bloqueos_por_nombre(monkeypatch):
    """Nombres de los bloqueos tomados AHORA (pila) y orden en que se toman."""
    tomados, orden = [], []

    class Espia(rec._Bloqueo):
        def __enter__(self):
            r = super().__enter__()
            tomados.append(os.path.basename(self.ruta))
            orden.append(os.path.basename(self.ruta))
            return r

        def __exit__(self, *exc):
            tomados.remove(os.path.basename(self.ruta))
            return super().__exit__(*exc)

    monkeypatch.setattr(rec, "_Bloqueo", Espia)
    return tomados, orden


def test_f2fix2_gap53_rebuild_recorre_cases_sin_el_bloqueo_del_indice(tmp_path, monkeypatch):
    """§3/E3: F1 (recorrido de `cases/`) va SIN el bloqueo del indice pero con `.cases_rebuild.lock`,
    que se toma ANTES; F0 y F2 toman el del indice (dos secciones O(1)/O(cola))."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    rec.grabar(_caso(), cfg, raiz)
    tomados, orden = _espia_de_bloqueos_por_nombre(monkeypatch)
    vistos = []
    real = rec.estado_de_cases
    monkeypatch.setattr(rec, "estado_de_cases", lambda *a, **k: vistos.append(tuple(tomados)) or real(*a, **k))
    assert rec.reconstruir_indice(str(store))[0] == 2
    assert vistos == [(rec.BLOQUEO_REBUILD,)], vistos
    assert orden == [rec.BLOQUEO_REBUILD, rec.BLOQUEO_INDICE, rec.BLOQUEO_INDICE], orden


def test_f2fix2_gap53_escritores_durante_f1_no_esperan_al_rebuild(tmp_path, monkeypatch):
    """#53: un `record` y un `set-status` DURANTE F1 no esperan (con el bloqueo retenido por F1
    fallarian a los 0,2 s) y sus lineas entran por la cola: el indice final == `cases/`."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    monkeypatch.setattr(rec, "ESPERA_BLOQUEO_S", 0.2)
    real, res = rec.estado_de_cases, {}

    def f1_con_escritores(*a, **k):
        r = real(*a, **k)
        if not res:
            res["g"] = rec.grabar(_caso(request="durante F1"), cfg, raiz)
            res["s"] = rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg, raiz)
        return r

    monkeypatch.setattr(rec, "estado_de_cases", f1_con_escritores)
    n, avisos = rec.reconstruir_indice(str(store))
    monkeypatch.setattr(rec, "estado_de_cases", real)
    assert res["g"]["version"] == 2 and res["g"]["avisos"] == [] and res["s"]["avisos"] == []
    assert n == 2 and avisos == []
    assert {e["version"]: e["status"] for e in rec.listar(str(store))} == {1: "rejected", 2: "pending"}
    assert rec.comprobar_indice(str(store)) == []


_MUERE_TRAS_W = r"""
import importlib.util, json, os, sys
spec = importlib.util.spec_from_file_location("rec_proc", sys.argv[1])
r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
r.ESPERA_BLOQUEO_S = 1.0
r._indexar = lambda *a, **k: os._exit(9)          # muere entre W (validation.json) y A (su linea)
r.cambiar_estado("geo-ramp.steep", 1, sys.argv[4], json.loads(sys.argv[2]), sys.argv[3])
"""


def test_f2fix2_gap53_e3_set_status_muerto_durante_f1_gana_el_disco(tmp_path, monkeypatch):
    """E6/E3: durante F1, un `set-status rejected` deja su linea en la cola y OTRO proceso muere
    entre W (`needs_changes`) y A: F2 relee del disco lo que toca la cola, no copia sus bytes."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    real, hecho = rec.estado_de_cases, []

    def f1(*a, **k):
        r = real(*a, **k)
        if not hecho:
            rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg, raiz)
            muerto = subprocess.run([sys.executable, "-c", _MUERE_TRAS_W, RECORDER_PATH, json.dumps(cfg), raiz,
                                     "needs_changes"], capture_output=True, text=True, encoding="utf-8", timeout=120)
            hecho.append(muerto.returncode)
        return r

    monkeypatch.setattr(rec, "estado_de_cases", f1)
    rec.reconstruir_indice(str(store))
    monkeypatch.setattr(rec, "estado_de_cases", real)
    assert hecho == [9]
    assert _json(store / "cases" / "ramp.steep" / "v001" / "validation.json")["status"] == "needs_changes"
    assert [e["status"] for e in rec.listar(str(store))] == ["needs_changes"]
    assert rec.comprobar_indice(str(store)) == []


def test_f2fix2_gap53_e3_indice_ausente_en_f0_no_dispara_el_reintento(tmp_path, monkeypatch):
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    os.remove(os.path.join(str(store), rec.INDICE))
    real, llamadas = rec.estado_de_cases, []

    def f1(*a, **k):
        llamadas.append(1)
        r = real(*a, **k)
        if len(llamadas) == 1:
            rec.grabar(_caso(request="crea el indice"), cfg, raiz)
        return r

    monkeypatch.setattr(rec, "estado_de_cases", f1)
    assert rec.reconstruir_indice(str(store))[0] == 2
    monkeypatch.setattr(rec, "estado_de_cases", real)
    assert llamadas == [1]                                   # sin reintento
    assert rec.comprobar_indice(str(store)) == []


def test_f2fix2_gap53_e3_identidad_cambiada_reintenta_acotado_y_luego_exit_3(tmp_path, monkeypatch, capsys):
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    _escribir_config(tmp_path, cfg)
    ruta = os.path.join(str(store), rec.INDICE)
    antes = open(ruta, "rb").read()
    contador = [0]
    real = rec._identidad

    def cambia(r):
        contador[0] += 1
        i = real(r)
        return None if i is None else i[:1] + (contador[0],) + i[2:]

    monkeypatch.setattr(rec, "_identidad", cambia)
    with pytest.raises(rec.Transitorio):
        rec.reconstruir_indice(str(store))
    # fix3 (F2): una identidad por intento (F0); las pasadas la comprueban sobre su propio descriptor
    assert contador[0] == rec.REINTENTOS_REBUILD
    assert rec.main(["index", "rebuild", "--project-root", raiz]) == 3
    assert open(ruta, "rb").read() == antes
    assert not [n for n in os.listdir(str(store)) if n.startswith(rec.PREFIJO_TEMPORAL)]
    # tamano menor que offset0 (alguien trunco el indice durante F1): tambien reintento
    monkeypatch.setattr(rec, "_identidad", real)
    real_f1, veces = rec.estado_de_cases, []

    def trunca(*a, **k):
        veces.append(1)
        if len(veces) == 1:
            with open(ruta, "wb") as f:
                f.write(b"")
        return real_f1(*a, **k)

    monkeypatch.setattr(rec, "estado_de_cases", trunca)
    assert rec.reconstruir_indice(str(store))[0] == 1 and len(veces) == 2


def test_f2fix2_gap53_e3_st_ino_cero_compara_el_hash_del_prefijo(tmp_path, monkeypatch):
    """FAT/SMB (`st_ino == 0`): la identidad incluye un hash de los bytes previos a `offset0`; si
    cambian durante F1 (mismo tamano), se reintenta."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    ruta = os.path.join(str(store), rec.INDICE)
    real_stat = rec._stat_indice

    class SinIno:
        def __init__(self, st):
            self.st_dev, self.st_ino, self.st_size = st.st_dev, 0, st.st_size

    monkeypatch.setattr(rec, "_stat_indice", lambda r: SinIno(real_stat(r)))
    real_f1, veces = rec.estado_de_cases, []

    def reescribe(*a, **k):
        veces.append(1)
        if len(veces) == 1:
            crudo = open(ruta, "rb").read()
            with open(ruta, "wb") as f:
                f.write(crudo.replace(b"pending", b"PENDING"))    # mismo tamano, otros bytes
        return real_f1(*a, **k)

    monkeypatch.setattr(rec, "estado_de_cases", reescribe)
    assert rec.reconstruir_indice(str(store))[0] == 1
    assert len(veces) == 2
    monkeypatch.setattr(rec, "estado_de_cases", real_f1)
    assert rec.comprobar_indice(str(store)) == []


def test_f2fix2_gap53_e3_permissionerror_en_el_replace_de_f2_no_toca_el_indice(tmp_path, monkeypatch):
    """E3 + fix3 (#76): `PermissionError` PERSISTENTE (tras los reintentos) al sustituir el indice ->
    `ErrorPermanente` (exit 2, antes exit 3); nunca toca el indice ni deja temporales."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    _escribir_config(tmp_path, cfg)
    ruta = os.path.join(str(store), rec.INDICE)
    antes = open(ruta, "rb").read()
    real = os.replace

    def en_uso(a, b):
        if os.path.basename(b) == rec.INDICE:
            raise PermissionError(5, "Acceso denegado (un lector tiene el indice abierto)")
        return real(a, b)

    monkeypatch.setattr(rec.time, "sleep", lambda _s: None)
    monkeypatch.setattr(rec.os, "replace", en_uso)
    with pytest.raises(rec.ErrorPermanente):
        rec.reconstruir_indice(str(store))
    assert rec.main(["index", "rebuild", "--project-root", raiz]) == 2
    monkeypatch.setattr(rec.os, "replace", real)
    assert open(ruta, "rb").read() == antes
    assert not [n for n in os.listdir(str(store)) if n.startswith(rec.PREFIJO_TEMPORAL)]


def test_f2fix2_gap53_e3_el_append_abre_el_indice_por_ruta_con_el_bloqueo(tmp_path, monkeypatch):
    """E3 (invariante): cada append abre el indice POR RUTA despues de tomar el bloqueo (nunca un fd
    cacheado): tras el `os.replace` del rebuild, la linea siguiente cae en el fichero NUEVO."""
    raiz, cfg, store = _proyecto(tmp_path)
    estado = _espia_de_bloqueo(monkeypatch)
    aperturas, real_open = [], builtins.open

    def espia(ruta, modo="r", *a, **k):
        if os.path.basename(str(ruta)) == rec.INDICE and ("a" in modo or "w" in modo):
            aperturas.append(estado["dentro"])
        return real_open(ruta, modo, *a, **k)

    monkeypatch.setattr(rec, "open", espia, raising=False)
    rec.grabar(_caso(), cfg, raiz)
    rec.reconstruir_indice(str(store))
    rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg, raiz)
    assert len(aperturas) == 2 and all(d >= 1 for d in aperturas), aperturas
    assert _indice(store)[-1]["status"] == "rejected" and rec.comprobar_indice(str(store)) == []


def test_f2fix2_gap53_e4_recorrido_sin_realpath_por_version(tmp_path, monkeypatch):
    raiz, cfg, store = _proyecto(tmp_path)
    for _ in range(3):
        rec.grabar(_caso(), cfg, raiz)
    real, llamadas = os.path.realpath, []

    def contar():
        llamadas.clear()
        monkeypatch.setattr(rec.os.path, "realpath", lambda p, *a, **k: llamadas.append(p) or real(p, *a, **k))
        rec.estado_de_cases(str(store), raiz)
        monkeypatch.setattr(rec.os.path, "realpath", real)
        return len(llamadas)

    con_3 = contar()
    for _ in range(9):
        rec.grabar(_caso(), cfg, raiz)
    assert contar() == con_3                                 # 12 versiones: mismo numero de realpath


class _St:
    """Resultado de `lstat` sintetico (placeholders de nube y enlaces sin privilegios)."""

    def __init__(self, modo, tag=None, **extra):
        self.st_mode = modo
        if tag is not None:
            self.st_reparse_tag = tag
        self.st_nlink = 1
        self.st_mtime = time.time()
        for k, v in extra.items():
            setattr(self, k, v)


def _nombre(x):
    return getattr(x, "name", None) or os.path.basename(str(x))


def test_f2fix2_gap53_e4_enlace_por_name_surrogate_y_la_nube_no_es_enlace(tmp_path, monkeypatch):
    """E4/E6: enlace = symlink o `st_reparse_tag & 0x20000000` (name surrogate: symlink y junction);
    un placeholder de OneDrive (`0x9000001A`) NO es enlace; sin `st_reparse_tag` en Windows,
    degradacion a `realpath`."""
    assert rec.NAME_SURROGATE == 0x20000000
    assert rec._es_enlace_st(_St(stat.S_IFDIR, 0x9000001A)) is False           # IO_REPARSE_TAG_CLOUD_6
    assert rec._es_enlace_st(_St(stat.S_IFDIR, 0xA0000003)) is True            # junction (mount point)
    assert rec._es_enlace_st(_St(stat.S_IFREG, 0xA000000C)) is True            # symlink
    assert rec._es_enlace_st(_St(stat.S_IFLNK)) is True
    assert rec._es_enlace_st(_St(stat.S_IFDIR, 0)) is False
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    real = rec._stat_sin_seguir

    def con_tag(tag):
        def f(x):
            st = real(x)
            return _St(st.st_mode, tag, st_nlink=st.st_nlink, st_mtime=st.st_mtime) if _nombre(x) == "v001" else st
        return f

    monkeypatch.setattr(rec, "_stat_sin_seguir", con_tag(0x9000001A))
    entradas, avisos = rec.estado_de_cases(str(store))
    assert list(entradas) == [("geo-ramp.steep", 1)] and avisos == []
    monkeypatch.setattr(rec, "_stat_sin_seguir", con_tag(0xA0000003))
    entradas, avisos = rec.estado_de_cases(str(store))
    assert entradas == {} and any("v001" in a and "enlace" in a for a in avisos), avisos
    # degradacion: en Windows sin `st_reparse_tag`, se resuelve con realpath (un enlace real se detecta)
    monkeypatch.setattr(rec, "_stat_sin_seguir", real)
    fuera = tmp_path / "fuera" / "v002"
    shutil.copytree(str(store / "cases" / "ramp.steep" / "v001"), str(fuera))
    _enlazar_dir(fuera, store / "cases" / "ramp.steep" / "v002")
    monkeypatch.setattr(rec, "_WINDOWS", True)
    monkeypatch.setattr(rec, "_stat_sin_seguir", lambda x: _St(stat.S_IFDIR) if _nombre(x) == "v002" else real(x))
    _e, avisos = rec.estado_de_cases(str(store))
    assert any("v002" in a and "enlace" in a for a in avisos), avisos


def test_f2fix2_gap54_skill_y_docstring_documentan_exit_codes_y_check():
    """E3 (gap #54, TDD n/a: prosa): exit 0/1/2/3 del CLI y la lista EXACTA de motivos de exit 1 de
    `index check`, con «en curso» como informativo (exit 0)."""
    with open(SKILL_MD, encoding="utf-8") as f:
        s = f.read()
    for frag in ("exit 3", "reintenta", "en curso", "60 s", "mtime", "futuro", "no es un fichero regular",
                 "bloqueada o sin permisos", "no casa con su ruta", "línea corrupta", ".cases_rebuild.lock",
                 "duplicada", "enlace", "`validation.json` incoherente", "en `cases/` y no en el índice"):
        assert frag in s, frag
    doc = rec.__doc__
    for frag in ("exit 0", "1 rechazo", "2 uso", "3 transitorio", "en curso", "no es un fichero regular"):
        assert frag in doc, frag


def test_f2fix2_gap56_api_sin_raiz_proyecto_usa_el_cwd(tmp_path, monkeypatch):
    """#56: sin `raiz_proyecto`, TODAS las funciones publicas usan el cwd (como `config_activa`) y
    la comprobacion de `docs/knowledge/` no se salta."""
    (tmp_path / "otro").mkdir()
    otro, cfg_otro, _s = _proyecto(tmp_path / "otro")
    r = rec.grabar(_caso(), cfg_otro, otro)
    raiz = tmp_path / "proj"
    raiz.mkdir()
    cfg = {"version": 1, "enabled": True, "root": ".", "id_prefix": "geo"}
    aprobado = raiz / "docs" / "knowledge" / "approved"
    shutil.copytree(r["path"], str(aprobado / "v001"))
    (raiz / "cases").mkdir()
    _enlazar_dir(aprobado, raiz / "cases" / "ramp.steep")
    antes = sorted(_ficheros(str(aprobado))), _bytes_del_store(str(aprobado))
    monkeypatch.chdir(str(raiz))
    with pytest.raises(rec.Rechazo):
        rec.grabar(_caso(), cfg)
    with pytest.raises(rec.Rechazo):
        rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg)
    difs = rec.comprobar_indice(str(raiz))
    assert any("ramp.steep" in d and "enlace" in d for d in difs), difs
    assert rec.reconstruir_indice(str(raiz))[0] == 0
    assert (sorted(_ficheros(str(aprobado))), _bytes_del_store(str(aprobado))) == antes


def _anidado(n):
    v = "hoja token=abc123XYZ789"
    for _ in range(n):
        v = {"a": v}
    return v


def test_f2fix2_gap57_anidamiento_profundo_se_rechaza_por_campo(tmp_path):
    """#57: redactar con tope `cs.PROFUNDIDAD_MAX` -> rechazo `{campo, mensaje}`, nunca `RecursionError`."""
    raiz, cfg, store = _proyecto(tmp_path)
    tope = rec.cs.PROFUNDIDAD_MAX
    for campo in ("metrics", "context", "constraints", "request"):
        for n in (tope + 1, 600):
            with pytest.raises(rec.Rechazo) as e:
                rec.grabar(_caso(**{campo: _anidado(n)}), cfg, raiz)
            assert campo in {x["campo"] for x in e.value.errores}, (campo, n, e.value.errores)
    assert not store.exists()
    r = rec.grabar(_caso(metrics=_anidado(tope)), cfg, raiz)
    assert "abc123XYZ789" not in open(os.path.join(r["path"], "metrics.json"), encoding="utf-8").read()
    _escribir_config(tmp_path, cfg)
    hondo = tmp_path / "hondo.json"
    hondo.write_text(json.dumps(_caso(metrics=_anidado(600))), encoding="utf-8")
    c = _cli("record", str(hondo), "--project-root", raiz)
    assert c.returncode == 1 and "Traceback" not in c.stderr and "metrics" in c.stderr


def test_f2fix2_gap58_version_en_curso_es_informativa_y_caduca(tmp_path, monkeypatch, capsys):
    """§5/E5: una version SIN `metadata.json` con `0 <= ahora - mtime < GRACIA_EN_CURSO_S` es «en
    curso» (informativa, exit 0); pasada la gracia, o con `mtime` futuro, es incoherencia."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    _escribir_config(tmp_path, cfg)
    v2 = store / "cases" / "ramp.steep" / "v002"
    v2.mkdir()
    difs, en_curso = rec.comprobar_indice_detalle(str(store))
    assert difs == [] and len(en_curso) == 1 and "v002" in en_curso[0] and "en curso" in en_curso[0]
    assert rec.comprobar_indice(str(store)) == []
    capsys.readouterr()
    assert rec.main(["index", "check", "--project-root", raiz]) == 0
    assert "en curso" in capsys.readouterr().err
    ahora = time.time()
    monkeypatch.setattr(rec, "_reloj", lambda: ahora + rec.GRACIA_EN_CURSO_S + 1)
    difs, en_curso = rec.comprobar_indice_detalle(str(store))
    assert en_curso == [] and any("v002" in d and "incompleta" in d for d in difs), difs
    assert rec.main(["index", "check", "--project-root", raiz]) == 1
    monkeypatch.setattr(rec, "_reloj", time.time)
    os.utime(str(v2), (ahora + 3600, ahora + 3600))                        # mtime futuro: nunca «en curso»
    difs, en_curso = rec.comprobar_indice_detalle(str(store))
    assert en_curso == [] and any("v002" in d and "futuro" in d for d in difs), difs
    os.utime(str(v2), (ahora, ahora))
    # con metadata.json y sin validation.json nunca esta «en curso»
    v3 = store / "cases" / "ramp.steep" / "v003"
    v3.mkdir()
    m = _json(store / "cases" / "ramp.steep" / "v001" / "metadata.json")
    m["version"] = 3
    (v3 / "metadata.json").write_text(json.dumps(m), encoding="utf-8")
    difs, en_curso = rec.comprobar_indice_detalle(str(store))
    assert any("v003" in d for d in difs) and not any("v003" in e for e in en_curso), (difs, en_curso)


def test_f2fix2_gap58_completa_sin_linea_reciente_es_en_curso(tmp_path, monkeypatch):
    """E5: «esta en cases/ pero no en el indice» con `metadata.json` reciente = grabacion entre W y A."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    open(os.path.join(str(store), rec.INDICE), "wb").close()
    difs, en_curso = rec.comprobar_indice_detalle(str(store))
    assert difs == [] and any("v001" in e and "en curso" in e for e in en_curso), (difs, en_curso)
    monkeypatch.setattr(rec, "_reloj", lambda: time.time() + rec.GRACIA_EN_CURSO_S + 1)
    difs, _en = rec.comprobar_indice_detalle(str(store))
    assert any("v001" in d and "no en el indice" in d for d in difs), difs


def test_f2fix2_gap58_check_lee_la_cola_antes_de_reportar(tmp_path, monkeypatch):
    """E5: `check` toma el tamano del indice (F0), recorre `cases/` y lee la cola ANTES de reportar:
    un `set-status` que entra entre F0 y el recorrido no es una diferencia."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    real, hecho = rec._estado_de_cases, []

    def set_status_antes_del_recorrido(*a, **k):
        if not hecho:
            hecho.append(rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg, raiz)["status"])
        return real(*a, **k)

    monkeypatch.setattr(rec, "_estado_de_cases", set_status_antes_del_recorrido)
    assert rec.comprobar_indice_detalle(str(store)) == ([], [])
    assert hecho == ["rejected"]


_BUCLE = r"""
import importlib.util, json, os, sys, time
spec = importlib.util.spec_from_file_location("rec_proc", sys.argv[1])
r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
cfg, raiz, papel, fin = json.loads(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5]
store, fallos, vueltas = r.raiz_store(cfg, raiz), [], 0
if papel == "record":
    caso = json.loads(sys.stdin.read())
    for i in range(20):
        try:
            r.grabar(dict(caso, request=f"bucle {i}"), cfg, raiz)
        except Exception as e:
            fallos.append(f"{type(e).__name__}: {e}")
else:
    limite = time.monotonic() + 120
    while not os.path.exists(fin) and time.monotonic() < limite and vueltas < 2000:
        vueltas += 1
        try:
            difs = r.comprobar_indice(store)
        except Exception as e:
            difs = [f"{type(e).__name__}: {e}"]
        if difs:
            fallos.append(difs)
print(json.dumps({"fallos": fallos, "vueltas": vueltas}))
"""


def test_f2fix2_gap58_procesos_record_y_check_en_bucle_sin_falsos_positivos(tmp_path):
    """#58 con PROCESOS reales (acotado: 20 `record` frente a un `check` en bucle): ningun `check`
    cuenta como incoherencia la version que `record` esta escribiendo."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    fin = tmp_path / "fin"

    def lanzar(papel):
        return subprocess.Popen([sys.executable, "-c", _BUCLE, RECORDER_PATH, json.dumps(cfg), raiz, papel, str(fin)],
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                encoding="utf-8")

    chk = lanzar("check")
    chk.stdin.close()
    grab = lanzar("record")
    sal_g = grab.communicate(json.dumps(_caso()), timeout=300)
    fin.write_text("", encoding="utf-8")
    sal_c = chk.stdout.read(), chk.stderr.read()
    chk.wait(timeout=300)
    assert grab.returncode == 0 and chk.returncode == 0, (sal_g[1][-400:], sal_c[1][-400:])
    g, c = json.loads(sal_g[0]), json.loads(sal_c[0])
    assert g["fallos"] == [] and c["fallos"] == [], (g["fallos"][:3], c["fallos"][:3])
    assert c["vueltas"] >= 3, c
    assert rec.comprobar_indice(str(store)) == []


def test_f2fix2_gap59_no_es_un_fichero_sin_reintentos_y_no_legible_con_mensaje_exacto(tmp_path, monkeypatch):
    raiz, cfg, store = _proyecto(tmp_path)
    for _ in range(3):
        rec.grabar(_caso(), cfg, raiz)
    for v in (1, 2, 3):
        meta = store / "cases" / "ramp.steep" / f"v{v:03d}" / "metadata.json"
        meta.unlink()
        meta.mkdir()
    esperas = []
    monkeypatch.setattr(rec.time, "sleep", lambda s: esperas.append(s))
    difs = rec.comprobar_indice(str(store))
    assert esperas == [], len(esperas)                                    # sin reintentos
    motivos = [d for d in difs if "metadata.json no es un fichero regular" in d]
    assert len(motivos) == 3 and not any("bloqueada por otro proceso" in d for d in difs), difs
    # un fichero regular que no se puede leer tras los reintentos: «bloqueada o sin permisos»
    (tmp_path / "b").mkdir()
    raiz2, cfg2, store2 = _proyecto(tmp_path / "b")
    rec.grabar(_caso(), cfg2, raiz2)
    real_open = builtins.open

    def denegado(ruta, *a, **k):
        if str(ruta).endswith("validation.json"):
            raise PermissionError(13, "Permiso denegado")
        return real_open(ruta, *a, **k)

    monkeypatch.setattr(rec, "open", denegado, raising=False)
    difs = rec.comprobar_indice(str(store2))
    assert any(f"no legible tras {rec.REINTENTOS} reintentos (bloqueada o sin permisos)" in d for d in difs), difs


def test_f2fix2_gap60_set_status_y_supersedes_localizan_la_version_por_numero(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)                                          # v001 con ancho 3
    cfg4 = dict(cfg, ids={"version_width": 4})
    val = store / "cases" / "ramp.steep" / "v001" / "validation.json"
    for v, st in ((1, "rejected"), ("v001", "needs_changes"), ("v0001", "pending")):
        r = rec.cambiar_estado("geo-ramp.steep", v, st, cfg4, raiz)
        assert r["ref"] == "geo-ramp.steep@v0001" and _json(val)["status"] == st
    r = rec.grabar(_caso(outcome="corrected", supersedes_case="geo-ramp.steep@v0001"), cfg4, raiz)
    assert r["ref"] == "geo-ramp.steep@v0002"
    shutil.copytree(str(store / "cases" / "ramp.steep" / "v001"), str(store / "cases" / "ramp.steep" / "v01"))
    with pytest.raises(rec.Rechazo) as e:
        rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg4, raiz)
    assert "duplicada" in str(e.value)
    with pytest.raises(rec.Rechazo) as e:
        rec.grabar(_caso(outcome="corrected", supersedes_case="geo-ramp.steep@v0001"), cfg4, raiz)
    assert "duplicada" in str(e.value)


def _bloqueo_con_gancho(monkeypatch, gancho):
    """`_Bloqueo` que ejecuta `gancho()` una vez, justo ANTES de tomar el primer bloqueo."""
    hecho = []

    class ConGancho(rec._Bloqueo):
        def __enter__(self):
            if not hecho:
                hecho.append(1)
                gancho()
            return super().__enter__()

    monkeypatch.setattr(rec, "_Bloqueo", ConGancho)
    return hecho


def test_f2fix2_gap61_m2_record_recomprueba_enlaces_con_el_bloqueo(tmp_path, monkeypatch):
    raiz, cfg, store = _proyecto(tmp_path)
    (store / "cases").mkdir(parents=True)
    aprobado = tmp_path / "proj" / "docs" / "knowledge" / "approved"
    aprobado.mkdir(parents=True)
    _bloqueo_con_gancho(monkeypatch, lambda: _enlazar_dir(aprobado, store / "cases" / "ramp.steep"))
    with pytest.raises(rec.Rechazo) as e:
        rec.grabar(_caso(), cfg, raiz)
    assert "enlace" in str(e.value)
    assert os.listdir(str(aprobado)) == []


def test_f2fix2_gap61_m8_set_status_recomprueba_enlaces_con_el_bloqueo(tmp_path, monkeypatch):
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    fuera = tmp_path / "fuera"
    fuera.mkdir()

    def cambiar_por_enlace():
        os.rename(str(store / "cases" / "ramp.steep"), str(fuera / "ramp.steep"))
        _enlazar_dir(fuera / "ramp.steep", store / "cases" / "ramp.steep")

    _bloqueo_con_gancho(monkeypatch, cambiar_por_enlace)
    val = fuera / "ramp.steep" / "v001" / "validation.json"
    with pytest.raises(rec.Rechazo) as e:
        rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg, raiz)
    assert "enlace" in str(e.value)
    assert _json(val)["status"] == "pending"


def test_f2fix2_gap61_m6_mayusculas_se_recomprueban_con_el_bloqueo(tmp_path, monkeypatch):
    """fix4-bis (#81): en NTFS/APFS la variante creada a la vez hace chocar el `mkdir` del caso ->
    rechazo; en un sistema que distingue mayusculas (Linux) son dos directorios: el record pasa y
    `check` reporta la pareja (limite declarado)."""
    raiz, cfg, store = _proyecto(tmp_path, family_pattern="^[A-Za-z0-9]+$")
    (store / "cases").mkdir(parents=True)
    sensible = _distingue_mayusculas(store / "cases")
    _bloqueo_con_gancho(monkeypatch, lambda: os.makedirs(str(store / "cases" / "RAMP.steep")))
    if sensible:
        assert rec.grabar(_caso(), cfg, raiz)["ref"] == "geo-ramp.steep@v001"
        difs = rec.comprobar_indice(str(store))
        assert any("mayusculas" in d and "RAMP.steep" in d and "ramp.steep" in d for d in difs), difs
        return
    with pytest.raises(rec.Rechazo) as e:
        rec.grabar(_caso(), cfg, raiz)
    assert "mayusculas" in str(e.value)
    assert os.listdir(str(store / "cases" / "RAMP.steep")) == []


def test_f2fix2_gap61_m15_dentro_exige_separador(tmp_path):
    """`_dentro` no acepta un hermano con el mismo prefijo (`store-evil` no esta dentro de `store`)."""
    base = os.path.normcase(str(tmp_path / "store"))
    assert not rec._dentro(os.path.normcase(str(tmp_path / "store-evil" / "x")), base)
    assert not rec._dentro(os.path.normcase(str(tmp_path / "store-evil")), base)
    assert rec._dentro(os.path.normcase(str(tmp_path / "store" / "x")), base) and rec._dentro(base, base)
    raiz, cfg, store = _proyecto(tmp_path)
    store.mkdir()
    evil = tmp_path / "store-evil" / "cases"
    _enlazar_dir(evil, store / "cases")
    with pytest.raises(rec.Rechazo):
        rec.grabar(_caso(), cfg, raiz)
    assert os.listdir(str(evil)) == []


def test_f2fix2_gap62_mapping_que_miente_no_abre_gold_sin_flag(tmp_path):
    """#62: el caso se convierte a tipos JSON PLANOS al entrar; un `dict` hijo cuyo `get` miente no
    esquiva la puerta Gold, y un tipo no JSON se rechaza."""
    raiz, cfg, store = _proyecto(tmp_path)

    class Miente(dict):
        def get(self, k, d=None):
            return {"status": "pending", "approved_by_human": False}.get(k, d)

    with pytest.raises(rec.Rechazo) as e:
        rec.grabar(_caso(validation=Miente(status="approved", approved_by_human=True)), cfg, raiz)
    assert rec.MENSAJE_GOLD in str(e.value)
    assert not store.exists()
    for raro in (object(), {1, 2}, (1, 2), b"bytes"):
        with pytest.raises(rec.Rechazo) as e:
            rec.grabar(_caso(metrics={"x": raro}), cfg, raiz)
        assert any("metrics" in x["campo"] for x in e.value.errores), e.value.errores
    with pytest.raises(rec.Rechazo):
        rec.grabar(_caso(metrics={1: "clave no texto"}), cfg, raiz)
    assert not store.exists()
    assert rec.grabar(_caso(validation=Miente(status="approved", approved_by_human=True)), cfg, raiz,
                      approved_by_human=True)["version"] == 1


def _hardlink(origen, destino):
    try:
        os.link(str(origen), str(destino))
    except (OSError, NotImplementedError) as e:   # pragma: no cover - FS sin enlaces duros
        pytest.skip(f"sin enlaces duros: {e}")


def test_f2fix2_gap63_hardlink_en_el_indice_o_el_bloqueo_se_rechaza(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    store.mkdir()
    adr = tmp_path / "proj" / "docs" / "knowledge" / "approved" / "ADR-999.md"
    adr.parent.mkdir(parents=True)
    adr.write_bytes(b"curado\n")
    _hardlink(adr, store / rec.INDICE)
    with pytest.raises(rec.Rechazo) as e:
        rec.grabar(_caso(), cfg, raiz)
    assert "enlace duro" in str(e.value)
    assert adr.read_bytes() == b"curado\n" and not (store / "cases" / "ramp.steep" / "v001").exists()
    os.remove(str(store / rec.INDICE))
    rec.grabar(_caso(), cfg, raiz)
    val = store / "cases" / "ramp.steep" / "v001" / "validation.json"
    os.remove(str(store / rec.INDICE))
    _hardlink(adr, store / rec.INDICE)
    with pytest.raises(rec.Rechazo) as e:
        rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg, raiz)
    assert "enlace duro" in str(e.value) and _json(val)["status"] == "pending"
    os.remove(str(store / rec.INDICE))
    os.remove(str(store / rec.BLOQUEO_INDICE))
    _hardlink(adr, store / rec.BLOQUEO_INDICE)
    for accion in (lambda: rec.grabar(_caso(), cfg, raiz),
                   lambda: rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg, raiz)):
        with pytest.raises(rec.Rechazo) as e:
            accion()
        assert "enlace duro" in str(e.value)
    assert adr.read_bytes() == b"curado\n" and _json(val)["status"] == "pending"
    assert sorted(os.listdir(str(store / "cases" / "ramp.steep"))) == ["v001"]


def test_f2fix2_gap64_arguments_con_clave_duplicada_se_rechaza(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    secreto = "sk-ant-" + "a" * 24
    args = '{"token": "%s", "token": "x"}' % secreto
    for tr in ([{"role": "assistant", "tool_calls": [{"name": "sh", "arguments": args}]}],
               [{"role": "assistant", "tool_calls": [{"name": "sh", "arguments": {"sub": {"arguments": args}}}]}]):
        with pytest.raises(rec.Rechazo) as e:
            rec.grabar(_caso(trajectory=tr), cfg, raiz)
        assert any("arguments" in x["campo"] and "duplicada" in x["mensaje"] for x in e.value.errores), e.value.errores
        assert secreto not in str(e.value)
    assert not store.exists()
    # defensa en profundidad: la redaccion de un `arguments` ambiguo nunca devuelve el texto original
    assert secreto not in rec._redactar_arguments_texto(args)


def test_f2fix2_gap65_limpiar_temporal_no_desciende_por_un_enlace(tmp_path):
    fuera = tmp_path / "fuera"
    fuera.mkdir()
    (fuera / "valioso.txt").write_text("no me borres", encoding="utf-8")
    tmp = tmp_path / ".tmp-prueba"
    (tmp / "sub").mkdir(parents=True)
    (tmp / "f.txt").write_text("x", encoding="utf-8")
    _enlazar_dir(fuera, tmp / "sub" / "j")
    rec._limpiar_temporal(str(tmp))
    assert (fuera / "valioso.txt").read_text(encoding="utf-8") == "no me borres"
    assert not os.path.lexists(str(tmp))
    raiz_enlace = tmp_path / ".tmp-enlace"
    _enlazar_dir(fuera, raiz_enlace)                                     # el propio temporal es un enlace
    rec._limpiar_temporal(str(raiz_enlace))
    assert (fuera / "valioso.txt").exists() and not os.path.lexists(str(raiz_enlace))


def test_f2fix2_gap66_validation_o_metadata_enlazados_se_rechazan_antes_de_leer(tmp_path, monkeypatch):
    """#66 en cualquier SO: `lstat` antes de leer (enlace simulado); y con symlink de fichero real
    cuando el SO lo permite (Linux/CI; Windows sin privilegio: solo la simulacion)."""
    raiz, cfg, store = _proyecto(tmp_path)
    r = rec.grabar(_caso(), cfg, raiz)
    real, real_leer, leidos = rec._stat_sin_seguir, rec._leer_json_reintentando, []
    for fichero in ("validation.json", "metadata.json"):
        monkeypatch.setattr(rec, "_stat_sin_seguir", lambda x, f=fichero: _St(stat.S_IFLNK) if _nombre(x) == f else real(x))
        monkeypatch.setattr(rec, "_leer_json_reintentando",
                            lambda ruta, *a: leidos.append(os.path.basename(ruta)) or real_leer(ruta, *a))
        with pytest.raises(rec.Rechazo) as e:
            rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg, raiz)
        assert "enlace" in str(e.value) and fichero not in leidos, leidos
        difs = rec.comprobar_indice(str(store))
        assert any("v001" in d and "enlace" in d for d in difs), difs
        leidos.clear()
    monkeypatch.setattr(rec, "_stat_sin_seguir", real)
    monkeypatch.setattr(rec, "_leer_json_reintentando", real_leer)
    fuera = tmp_path / "fuera.json"
    fuera.write_text(json.dumps({"status": "pending", "approved_by_human": False, "reviewer_note": "FUERA"}),
                     encoding="utf-8")
    val = os.path.join(r["path"], "validation.json")
    os.remove(val)
    try:
        os.symlink(str(fuera), val)
    except (OSError, NotImplementedError) as e:   # pragma: no cover - Windows sin privilegio
        pytest.skip(f"sin symlink de fichero: {e}")
    with pytest.raises(rec.Rechazo) as e:
        rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg, raiz)
    assert "enlace" in str(e.value) and "FUERA" in fuera.read_text(encoding="utf-8")


# ------------------------------------------------------------------ fix3 (revision intento 3, Fase 2)
# Diseno D-fix3 con las enmiendas F1-F5 (tasks.md, «Revision de dos lentes — intento 3: Fase 2»).

import errno


def _caso_fv(family, variant="steep", **cambios):
    return _caso(family=family, variant=variant, case_id=f"geo-{family}.{variant}", **cambios)


def _llamadas_con_el_bloqueo(monkeypatch, nombres=("scandir", "listdir", "lstat", "stat", "mkdir")):
    """Cuenta las llamadas a `os.<nombre>` hechas mientras `.cases_index.lock` esta tomado."""
    tomados, _orden = _espia_de_bloqueos_por_nombre(monkeypatch)
    cuenta = dict.fromkeys(nombres, 0)
    for n in nombres:
        def envoltura(*a, _real=getattr(os, n), _n=n, **k):
            if rec.BLOQUEO_INDICE in tomados:
                cuenta[_n] += 1
            return _real(*a, **k)
        monkeypatch.setattr(rec.os, n, envoltura)
    return cuenta


def test_f2fix3_gap67_s1_con_el_bloqueo_no_depende_de_versiones_ni_de_casos(tmp_path, monkeypatch):
    """#67 (D-fix3 §1 + F1): con `.cases_index.lock` tomado, `record` hace el MISMO numero de llamadas
    al sistema de ficheros con 11 que con 61 versiones del caso y con 2 que con 42 casos, y ningun
    `scandir`/`listdir` (el recorrido O(C) de mayusculas y la pista O(V) van fuera del bloqueo)."""
    raiz, cfg, store = _proyecto(tmp_path, family_pattern="^[A-Za-z0-9]+$")
    for _ in range(10):
        rec.grabar(_caso(), cfg, raiz)
    rec.grabar(_caso_fv("otro"), cfg, raiz)

    def medir():
        with monkeypatch.context() as m:
            cuenta = _llamadas_con_el_bloqueo(m)
            rec.grabar(_caso(), cfg, raiz)
        return dict(cuenta)

    base = medir()                                          # v011: dos digitos, igual que v061
    for _ in range(49):
        rec.grabar(_caso(), cfg, raiz)
    for i in range(40):
        rec.grabar(_caso_fv(f"fam{i}"), cfg, raiz)
    grande = medir()
    assert base["scandir"] == 0 and base["listdir"] == 0, base
    assert grande == base, (base, grande)


def test_f2fix3_gap67_f5_reserva_muerta_en_mayusculas_se_rechaza(tmp_path):
    """F5 (§1 roto en la revision previa): una reserva muerta `cases/RAMP.steep/v001` (vacia) +
    `record` de `ramp.steep` -> rechazo de mayusculas; nada se graba en el directorio de NTFS
    compartido. La existencia del caso sale del nombre EXACTO de `scandir`, no de `isdir`."""
    raiz, cfg, store = _proyecto(tmp_path, family_pattern="^[A-Za-z0-9]+$")
    muerta = store / "cases" / "RAMP.steep" / "v001"
    muerta.mkdir(parents=True)
    with pytest.raises(rec.Rechazo) as e:
        rec.grabar(_caso(), cfg, raiz)
    assert "mayusculas" in str(e.value)
    assert os.listdir(str(store / "cases" / "RAMP.steep")) == ["v001"] and os.listdir(str(muerta)) == []
    assert [n for n in os.listdir(str(store / "cases")) if not n.startswith(".")] == ["RAMP.steep"]
    _escribir_config(tmp_path, cfg)
    caso = tmp_path / "caso.json"
    caso.write_text(json.dumps(_caso()), encoding="utf-8")
    c = _cli("record", str(caso), "--project-root", raiz)
    assert c.returncode == 1 and "mayusculas" in c.stderr and "Traceback" not in c.stderr


_CREADOR = r"""
import importlib.util, json, os, sys, time
spec = importlib.util.spec_from_file_location("rec_proc", sys.argv[1])
r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
cfg, raiz, fam, listo, go = json.loads(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6]
caso = json.loads(sys.stdin.read())
caso.update(family=fam, case_id=f"geo-{fam}.steep")
r._redact_mod()                                   # carga perezosa fuera de la carrera
open(listo, "w").close()
limite = time.monotonic() + 60
while not os.path.exists(go) and time.monotonic() < limite:
    time.sleep(0.001)
try:
    out = {"ok": r.grabar(caso, cfg, raiz)["ref"]}
except r.Rechazo as e:
    out = {"rechazo": e.mensaje}
print(json.dumps(out))
"""


def test_f2fix3_gap67_f5_carrera_de_creacion_mayusculas_con_procesos_reales(tmp_path):
    """F5, PROCESOS reales: cuatro procesos graban A LA VEZ (barrera) `ramp.steep` y `RAMP.steep`
    (caso nuevo), en 6 rondas. Invariante: queda UN solo directorio, todas sus versiones son del
    `case_id` de su nombre exacto, los ganadores son de ese caso y el resto recibe el rechazo de
    mayusculas; el indice cuadra."""
    for ronda in range(6):
        base = tmp_path / f"r{ronda}"
        base.mkdir()
        raiz, cfg, store = _proyecto(base, family_pattern="^[A-Za-z0-9]+$")
        go = base / "go"
        familias = ("ramp", "RAMP", "ramp", "RAMP")
        procs = [subprocess.Popen([sys.executable, "-c", _CREADOR, RECORDER_PATH, json.dumps(cfg), raiz, fam,
                                   str(base / f"listo{i}"), str(go)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True, encoding="utf-8") for i, fam in enumerate(familias)]
        for p in procs:
            p.stdin.write(json.dumps(_caso()))
            p.stdin.close()
        for i, p in enumerate(procs):
            assert _esperar(base / f"listo{i}", p), p.communicate(timeout=30)
        go.write_text("", encoding="utf-8")
        salidas = []
        for p in procs:
            out = p.stdout.read()
            err = p.stderr.read()
            p.wait(timeout=120)
            assert p.returncode == 0, err[-400:]
            salidas.append(json.loads(out))
        dirs = sorted(n for n in os.listdir(str(store / "cases")) if not n.startswith("."))
        # fix4 (#81): en un sistema que distingue mayusculas (Linux) dos creaciones A LA VEZ son dos
        # directorios distintos (no chocan en disco): limite declarado, `check` reporta la pareja
        sensible = _distingue_mayusculas(store / "cases")
        assert len(dirs) == 1 or (sensible and len(dirs) == 2), (ronda, dirs, salidas)
        versiones_ = []
        for d in dirs:
            dueno = f"geo-{d.split('.')[0]}.steep"
            vs = os.listdir(str(store / "cases" / d))
            assert {_json(store / "cases" / d / v / "metadata.json")["case_id"] for v in vs} == {dueno}, ronda
            versiones_ += [f"{dueno}@{v}" for v in vs]
        ganadores = [s["ok"] for s in salidas if "ok" in s]
        assert sorted(ganadores) == sorted(versiones_), (ronda, salidas)
        assert all("mayusculas" in s["rechazo"] for s in salidas if "rechazo" in s), (ronda, salidas)
        difs = rec.comprobar_indice(str(store))
        if len(dirs) == 2:
            assert any("mayusculas" in x and "RAMP.steep" in x and "ramp.steep" in x for x in difs), difs
        else:
            assert difs == [], difs


def test_f2fix3_gap67_f1_mas_de_64_saltos_suelta_el_bloqueo_recalcula_y_acota(tmp_path, monkeypatch):
    """F1: con una pista obsoleta, S1 salta como mucho `SALTOS_MAX_S1` numeros ocupados con el
    bloqueo; despues lo suelta, recalcula la pista FUERA y reintenta (acotado): la version sale
    bien. Si la pista nunca mejora, tras `REINTENTOS_S1` -> `Transitorio` (exit 3) sin escribir."""
    raiz, cfg, store = _proyecto(tmp_path)
    dir_caso = store / "cases" / "ramp.steep"
    for v in range(1, 101):
        (dir_caso / f"v{v:03d}").mkdir(parents=True)                  # 100 numeros ocupados
    real, pistas = rec._siguiente_version, []

    def obsoleta_la_primera(d):
        pistas.append(1)
        return 1 if len(pistas) == 1 else real(d)

    monkeypatch.setattr(rec, "_siguiente_version", obsoleta_la_primera)
    with monkeypatch.context() as m:
        _tomados, orden = _espia_de_bloqueos_por_nombre(m)
        r = rec.grabar(_caso(), cfg, raiz)
    assert r["version"] == 101 and orden == [rec.BLOQUEO_INDICE] * 3, (r["version"], orden)    # S1, S1, S2
    monkeypatch.setattr(rec, "_siguiente_version", lambda d: 1)
    antes = sorted(os.listdir(str(dir_caso)))
    with pytest.raises(rec.Transitorio) as e:
        rec.grabar(_caso(), cfg, raiz)
    assert "reintenta" in str(e.value) and sorted(os.listdir(str(dir_caso))) == antes
    _escribir_config(tmp_path, cfg)
    caso = tmp_path / "caso.json"
    caso.write_text(json.dumps(_caso()), encoding="utf-8")
    assert rec.main(["record", str(caso), "--project-root", raiz]) == 3
    assert sorted(os.listdir(str(dir_caso))) == antes


def test_f2fix3_gap68_check_no_toma_nunca_el_bloqueo_del_indice(tmp_path, monkeypatch):
    """(4) / F3: `index check` no toma NUNCA `.cases_index.lock` (ni lo abre) aunque haya cola, y
    termina sin esperar mientras otro lo retiene (antes, bloqueo de solo lectura: exit 3)."""
    raiz, cfg, store = _proyecto(tmp_path)
    for _ in range(3):
        rec.grabar(_caso(), cfg, raiz)
    rec.cambiar_estado("geo-ramp.steep", 2, "rejected", cfg, raiz)
    linea = _indice(store)[-1]
    monkeypatch.setattr(rec, "ESPERA_BLOQUEO_S", 0.2)
    real_f1 = rec._estado_de_cases

    def f1_con_cola(*a, **k):
        r = real_f1(*a, **k)
        rec._anadir_linea(str(store), linea)                              # cola (un escritor simulado)
        return r

    with rec._Bloqueo(str(store)):                                        # otro lo retiene todo el rato
        with monkeypatch.context() as m:
            _tomados, orden = _espia_de_bloqueos_por_nombre(m)
            aperturas, real_open = [], builtins.open

            def espia(ruta, *a, **k):
                if os.path.basename(str(ruta)) in (rec.BLOQUEO_INDICE, rec.BLOQUEO_REBUILD):
                    aperturas.append(str(ruta))
                return real_open(ruta, *a, **k)

            m.setattr(rec, "open", espia, raising=False)
            m.setattr(rec, "_estado_de_cases", f1_con_cola)
            t0 = time.monotonic()
            assert rec.comprobar_indice_detalle(str(store)) == ([], [])
            assert time.monotonic() - t0 < 5
        assert orden == [] and aperturas == [], (orden, aperturas)


def test_f2fix3_gap68_f2_residual_tal_cual_con_el_bloqueo_y_relecturas_sin_el(tmp_path, monkeypatch):
    """#68 (F2, alternativa hibrida): las lineas de la cola se RELEEN del disco en pasadas SIN el
    bloqueo del indice; el residual (lo llegado tras la ultima pasada) se copia TAL CUAL con el
    bloqueo, sin ninguna relectura dentro."""
    raiz, cfg, store = _proyecto(tmp_path)
    for _ in range(3):
        rec.grabar(_caso(), cfg, raiz)
    ruta = os.path.join(str(store), rec.INDICE)
    tomados, _orden = _espia_de_bloqueos_por_nombre(monkeypatch)
    relecturas, real_rel = [], rec._releer_version
    monkeypatch.setattr(rec, "_releer_version",
                        lambda *a, **k: relecturas.append(rec.BLOQUEO_INDICE in tomados) or real_rel(*a, **k))
    real_f1, real_pad, residual = rec.estado_de_cases, rec._poner_al_dia, []

    def f1(*a, **k):
        r = real_f1(*a, **k)
        rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg, raiz)   # cola: se relee sin bloqueo
        return r

    def tras_pasadas(*a, **k):
        c = real_pad(*a, **k)
        rec.cambiar_estado("geo-ramp.steep", 2, "needs_changes", cfg, raiz)   # tras la ultima: residual
        with open(ruta, "rb") as f:
            residual.append(f.read().splitlines(keepends=True)[-1])
        return c

    monkeypatch.setattr(rec, "estado_de_cases", f1)
    monkeypatch.setattr(rec, "_poner_al_dia", tras_pasadas)
    n, avisos = rec.reconstruir_indice(str(store))
    assert n == 3 and avisos == [], avisos
    assert relecturas and not any(relecturas), relecturas               # releidas, y nunca con el bloqueo
    with open(ruta, "rb") as f:
        assert f.read().splitlines(keepends=True)[-1] == residual[0]      # copiada TAL CUAL
    assert {e["version"]: e["status"] for e in rec.listar(str(store))} == {1: "rejected", 2: "needs_changes", 3: "pending"}
    monkeypatch.setattr(rec, "estado_de_cases", real_f1)
    monkeypatch.setattr(rec, "_poner_al_dia", real_pad)
    assert rec.comprobar_indice(str(store)) == []


def test_f2fix3_gap68_trafico_sostenido_no_da_exit_3_y_el_bloqueo_se_toma_dos_veces(tmp_path, monkeypatch):
    """F2: con trafico que nunca baja del tope (> 64 lineas nuevas antes de cada pasada), el rebuild
    hace `MAX_PASADAS` pasadas y copia el residual: sin exit 3 por trafico, y el bloqueo del indice
    solo en F0 y F2."""
    raiz, cfg, store = _proyecto(tmp_path)
    for _ in range(2):
        rec.grabar(_caso(), cfg, raiz)
    linea = _indice(store)[0]
    real_cola, pasadas = rec._leer_cola, []

    def con_trafico(r, cursor, hasta_eof=False):
        if not hasta_eof:
            pasadas.append(1)
            for _ in range(rec.COLA_MAX_BLOQUEO + 10):
                rec._anadir_linea(str(store), linea)
        return real_cola(r, cursor, hasta_eof)

    monkeypatch.setattr(rec, "_leer_cola", con_trafico)
    _tomados, orden = _espia_de_bloqueos_por_nombre(monkeypatch)
    n, avisos = rec.reconstruir_indice(str(store))
    assert n == 2 and avisos == [] and len(pasadas) == rec.MAX_PASADAS, (n, avisos, len(pasadas))
    assert orden == [rec.BLOQUEO_REBUILD, rec.BLOQUEO_INDICE, rec.BLOQUEO_INDICE], orden
    monkeypatch.setattr(rec, "_leer_cola", real_cola)
    assert rec.comprobar_indice(str(store)) == []


def test_f2fix3_gap68_f5_fragmento_a_medio_escribir_en_una_pasada_sin_bloqueo(tmp_path, monkeypatch):
    """F5: una pasada sin bloqueo solo consume hasta el ULTIMO `\\n`: la linea que un escritor esta a
    medio escribir se queda para despues y, completa, entra por el residual (sin avisos)."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    ruta = os.path.join(str(store), rec.INDICE)
    linea = rec._linea(_indice(store)[0])
    mitad = len(linea) // 2
    real_f1, real_pad, vistas = rec.estado_de_cases, rec._poner_al_dia, []

    def f1(*a, **k):
        r = real_f1(*a, **k)
        with open(ruta, "ab") as f:
            f.write(linea[:mitad])                                        # a medio escribir...
        return r

    def pad(ruta_, cursor, avisos, al_releer):
        c = real_pad(ruta_, cursor, avisos, lambda clave, l: vistas.append(clave) or al_releer(clave, l))
        with open(ruta, "ab") as f:
            f.write(linea[mitad:])                                        # ... y terminada tras la pasada
        return c

    monkeypatch.setattr(rec, "estado_de_cases", f1)
    monkeypatch.setattr(rec, "_poner_al_dia", pad)
    n, avisos = rec.reconstruir_indice(str(store))
    assert n == 1 and avisos == [] and vistas == [], (avisos, vistas)
    with open(ruta, "rb") as f:
        assert f.read().splitlines(keepends=True)[-1] == linea
    monkeypatch.setattr(rec, "estado_de_cases", real_f1)
    monkeypatch.setattr(rec, "_poner_al_dia", real_pad)
    assert rec.comprobar_indice(str(store)) == []


def test_f2fix3_gap68_f5_sustitucion_del_indice_entre_pasadas(tmp_path, monkeypatch):
    """F5/F2: si otro indice ocupa el nombre ENTRE dos pasadas, la pasada siguiente lo detecta sobre
    su propio descriptor (identidad) y vuelve a F0 sin releer nada del fichero nuevo; el segundo
    intento termina coherente."""
    raiz, cfg, store = _proyecto(tmp_path)
    for _ in range(2):
        rec.grabar(_caso(), cfg, raiz)
    ruta = os.path.join(str(store), rec.INDICE)
    linea = _indice(store)[0]
    real_ident, f0s = rec._identidad, []
    monkeypatch.setattr(rec, "_identidad", lambda r: f0s.append(1) or real_ident(r))
    real_f1, real_cola, real_rel = rec.estado_de_cases, rec._leer_cola, rec._releer_version
    releidas, cambiado = [], []

    def f1(*a, **k):
        r = real_f1(*a, **k)
        if len(f0s) == 1:
            for _ in range(rec.COLA_MAX_BLOQUEO + 1):                     # > 64: habra una 2.a pasada
                rec._anadir_linea(str(store), linea)
        return r

    def cola(r, cursor, hasta_eof=False):
        res = real_cola(r, cursor, hasta_eof)
        if not hasta_eof and len(f0s) == 1 and not cambiado:
            with open(ruta, "rb") as f:
                crudo = f.read()
            with open(ruta + ".nuevo", "wb") as f:
                f.write(crudo + rec._linea(dict(linea, version=99)))     # marcada, tras el offset
            os.replace(ruta + ".nuevo", ruta)
            cambiado.append(1)
        return res

    monkeypatch.setattr(rec, "estado_de_cases", f1)
    monkeypatch.setattr(rec, "_leer_cola", cola)
    monkeypatch.setattr(rec, "_releer_version", lambda s, f, v, numero, *a, **k: releidas.append(numero) or
                        real_rel(s, f, v, numero, *a, **k))
    n, avisos = rec.reconstruir_indice(str(store))
    assert cambiado and len(f0s) == 2 and 99 not in releidas, (len(f0s), releidas)
    assert n == 2 and avisos == [], avisos
    monkeypatch.setattr(rec, "estado_de_cases", real_f1)
    monkeypatch.setattr(rec, "_leer_cola", real_cola)
    assert rec.comprobar_indice(str(store)) == []


def test_f2fix3_gap68_f3_check_confirma_releyendo_la_cola_y_el_disco(tmp_path, monkeypatch):
    """F3: `check` sin bloqueo confirma antes de reportar: relee la cola nueva (una linea que llega
    tras la ultima pasada) y, del disco, las claves que difieren (un `set-status` completo entre la
    ultima pasada y el final). Ninguno de los dos es una diferencia."""
    raiz, cfg, store = _proyecto(tmp_path)
    for _ in range(2):
        rec.grabar(_caso(), cfg, raiz)
    val = store / "cases" / "ramp.steep" / "v001" / "validation.json"
    real_f1, real_pad = rec._estado_de_cases, rec._poner_al_dia

    def w_antes_del_recorrido(*a, **k):                                   # W de v001 visto por F1...
        val.write_text(json.dumps({"status": "rejected", "approved_by_human": False, "approved_at": None,
                                   "reviewer_note": None}), encoding="utf-8")
        return real_f1(*a, **k)

    def a_y_set_status_tras_las_pasadas(*a, **k):
        c = real_pad(*a, **k)
        with rec._Bloqueo(str(store)):                                    # ... su A, tras la ultima pasada
            rec._anadir_linea(str(store), dict(_indice(store)[0], status="rejected"))
        rec.cambiar_estado("geo-ramp.steep", 2, "needs_changes", cfg, raiz)
        return c

    monkeypatch.setattr(rec, "_estado_de_cases", w_antes_del_recorrido)
    monkeypatch.setattr(rec, "_poner_al_dia", a_y_set_status_tras_las_pasadas)
    assert rec.comprobar_indice_detalle(str(store)) == ([], [])


def test_f2fix3_gap68_f3_check_confirma_del_disco_una_relectura_fallida_de_la_cola(tmp_path, monkeypatch):
    """F3: si releer del disco la version de una linea de la cola falla de forma pasajera (p. ej.
    `validation.json` retenido un instante por un `os.replace` ajeno), la confirmacion vuelve a
    leerla del disco antes de reportar: ni el aviso ni la diferencia quedan como falso positivo."""
    raiz, cfg, store = _proyecto(tmp_path)
    for _ in range(2):
        rec.grabar(_caso(), cfg, raiz)
    real_f1, real_rel, fallos = rec._estado_de_cases, rec._releer_version, []

    def f1(*a, **k):
        r = real_f1(*a, **k)
        rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg, raiz)   # cola
        return r

    def con_un_fallo(store_, fam, var, numero, case_id=None):
        if numero == 1 and not fallos:
            fallos.append(1)
            return None, ("cases/ramp.steep/v001 ilegible: validation.json no legible tras 40 reintentos "
                          "(bloqueada o sin permisos)"), False, None
        return real_rel(store_, fam, var, numero, case_id)

    monkeypatch.setattr(rec, "_estado_de_cases", f1)
    monkeypatch.setattr(rec, "_releer_version", con_un_fallo)
    assert rec.comprobar_indice_detalle(str(store)) == ([], []) and fallos == [1]


def test_f2fix3_gap68_anadir_al_indice_valida_contra_el_disco(tmp_path):
    """F2: `anadir_al_indice` (via publica) relee la version del disco: una linea que no la refleja
    no entra en el indice (ni, por tanto, en un residual que se copia tal cual)."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    e = _indice(store)[0]
    for mala in (dict(e, status="approved"), dict(e, version=7), dict(e, outcome="success"), dict(e, status="nada")):
        with pytest.raises(rec.Rechazo):
            rec.anadir_al_indice(str(store), mala)
    assert len(_indice(store)) == 1
    rec.anadir_al_indice(str(store), dict(e, updated_at="2030-01-01T00:00:00Z"))
    assert len(_indice(store)) == 2 and _indice(store)[-1]["updated_at"] == "2030-01-01T00:00:00Z"


class _DictContado(dict):
    """dict que cuenta cuantas veces se RECORRE (el bucle por linea de la cola de #69)."""
    recorridos = 0

    def __iter__(self):
        type(self).recorridos += 1
        return super().__iter__()

    def keys(self):
        type(self).recorridos += 1
        return super().keys()


def test_f2fix3_gap69_check_retira_los_avisos_por_clave_sin_recorrerlos(tmp_path, monkeypatch):
    """#69: por cada linea de la cola, `check` retira los avisos de ESA version por clave (O(1)); no
    recorre `avisos`/`en_curso` enteros (antes O(cola x avisos))."""
    raiz, cfg, store = _proyecto(tmp_path)
    for _ in range(3):
        rec.grabar(_caso(), cfg, raiz)
    for v in range(4, 14):
        (store / "cases" / "ramp.steep" / f"v{v:03d}").mkdir()           # 10 incompletas (avisos)
    _envejecer(store, solo_dirs=True)
    real_f1 = rec._estado_de_cases
    _DictContado.recorridos = 0

    def f1(*a, **k):
        entradas, avisos, en_curso, mtimes, rels = real_f1(*a, **k)
        for _ in range(20):
            rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg, raiz)   # 20 lineas de cola
        return entradas, _DictContado(avisos), _DictContado(en_curso), mtimes, rels

    monkeypatch.setattr(rec, "_estado_de_cases", f1)
    difs, _en = rec.comprobar_indice_detalle(str(store))
    assert len([d for d in difs if "incompleta" in d]) == 10, difs
    assert _DictContado.recorridos == 0, _DictContado.recorridos


def test_f2fix3_gap70_st_ino_cero_ventana_de_64_kib_previa_al_offset_consumido(tmp_path, monkeypatch):
    """#70/F4: con `st_ino == 0` la identidad hashea SOLO los 64 KiB previos al offset consumido
    (O(1), nunca el prefijo entero): un cambio dentro de la ventana se detecta (vuelta a F0); uno al
    principio de un indice de > 192 KiB, no (probabilistico, documentado)."""
    real_stat = rec._stat_indice

    class SinIno:
        def __init__(self, st):
            self.st_dev, self.st_ino, self.st_size = st.st_dev, 0, st.st_size

    def ensayo(sub, donde):
        raiz, cfg, store = _proyecto(sub)
        rec.grabar(_caso(), cfg, raiz)
        ruta = os.path.join(str(store), rec.INDICE)
        cruda = rec._linea(_indice(store)[0])
        with open(ruta, "ab") as f:
            f.write(cruda * (3 * rec.VENTANA_IDENTIDAD // len(cruda) + 1))
        tam = os.path.getsize(ruta)
        f0s, ventanas = [], []
        real_ident, real_ventana, real_f1 = rec._identidad, rec._ventana, rec.estado_de_cases
        with monkeypatch.context() as m:
            m.setattr(rec, "_stat_indice", lambda x: SinIno(real_stat(x)))
            m.setattr(rec, "_identidad", lambda r: f0s.append(1) or real_ident(r))
            m.setattr(rec, "_ventana", lambda f, off: ventanas.append(off - max(0, off - rec.VENTANA_IDENTIDAD))
                      or real_ventana(f, off))

            def f1(*a, **k):
                if len(f0s) == 1:
                    pos = cruda.index(b"pending") + (0 if donde == "inicio" else tam - len(cruda))
                    with open(ruta, "r+b") as f:                        # mismo tamano, otros bytes
                        f.seek(pos)
                        f.write(b"PENDING")
                return real_f1(*a, **k)

            m.setattr(rec, "estado_de_cases", f1)
            rec.reconstruir_indice(str(store))
        assert ventanas and max(ventanas) <= rec.VENTANA_IDENTIDAD, ventanas
        return len(f0s)

    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    assert ensayo(tmp_path / "a", "ventana") == 2                       # detectado: vuelta a F0
    assert ensayo(tmp_path / "b", "inicio") == 1                        # fuera de la ventana: no


def test_f2fix3_gap71_72_skill_y_docstring_exit_por_subcomando_y_tabla_de_check():
    """#71/#72 (TDD n/a: prosa): exit 0/1/2/3 exactos POR SUBCOMANDO (con los exit 3 de `index check`
    por identidad y el 2 permanente de #76) y la tabla `motivo · exit · qué hacer` de `index check`;
    el limite ampliado de E3 y el falso positivo transitorio de `check` bajo carga."""
    with open(SKILL_MD, encoding="utf-8") as f:
        s = f.read()
    assert "| Motivo | Exit | Qué hacer |" in s
    for frag in ("`record`", "`set-status`", "`index rebuild`", "`index check`", "`list`", "exit 2", "permanente",
                 "identidad", "más de 64", "temporal huérfano", "no es un directorio de versión", "enlace duro",
                 "falso positivo", "residual", "tal cual", "ENOLCK", "solo lectura"):
        assert frag in s, frag
    doc = rec.__doc__
    for frag in ("exit 0", "1 rechazo", "2 uso", "3 transitorio", "permanente", "residual", "identidad",
                 "nunca toma `.cases_index.lock`"):
        assert frag in doc, frag


def test_f2fix3_gap73_surrogate_suelto_se_rechaza_con_campo_y_sin_traceback(tmp_path):
    """#73: texto no codificable en UTF-8 (surrogate suelto) -> rechazo `{campo, mensaje}` en la
    validacion del original (valor, clave, `arguments` en texto y su JSON escapado), nunca
    `UnicodeEncodeError`; tambien `set-status --note`. No se escribe nada."""
    raiz, cfg, store = _proyecto(tmp_path)
    suelto = "a\ud800b"
    casos = [
        ("request", _caso(request=suelto)),
        ("context", _caso(context={suelto: "x"})),
        ("trajectory[1].tool_calls[0].arguments", _caso(trajectory=[
            {"role": "user", "content": "hola"},
            {"role": "assistant", "tool_calls": [{"name": "sh", "arguments": suelto}]}])),
        ("trajectory[1].tool_calls[0].arguments", _caso(trajectory=[
            {"role": "user", "content": "hola"},
            {"role": "assistant", "tool_calls": [{"name": "sh", "arguments": '{"cmd": "\\ud800"}'}]}])),
    ]
    for campo, caso in casos:
        with pytest.raises(rec.Rechazo) as e:
            rec.grabar(caso, cfg, raiz)
        assert any(x["campo"].startswith(campo) and "UTF-8" in x["mensaje"] for x in e.value.errores), (campo, e.value.errores)
    assert not store.exists()
    _escribir_config(tmp_path, cfg)
    fichero = tmp_path / "suelto.json"
    fichero.write_text(json.dumps(_caso(request=suelto)), encoding="utf-8")      # `\ud800` escapado en el JSON
    c = _cli("record", str(fichero), "--project-root", raiz)
    assert c.returncode == 1 and "UTF-8" in c.stderr and "Traceback" not in c.stderr
    rec.grabar(_caso(), cfg, raiz)
    antes = _bytes_del_store(str(store))
    with pytest.raises(rec.Rechazo) as e:
        rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg, raiz, reviewer_note=suelto)
    assert "UTF-8" in str(e.value) and _bytes_del_store(str(store)) == antes


def test_f2fix3_gap74_entrada_de_version_que_no_es_directorio_no_es_duplicado(tmp_path):
    """#74: UN criterio de «entrada de version» para `set-status`/`supersedes` y el recorrido: un
    fichero suelto `v01` o una junction rota `v0001` junto a `v001` no son duplicados (`set-status 1`
    funciona) y `index check`/`rebuild` los reportan con su motivo."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    dir_caso = store / "cases" / "ramp.steep"
    (dir_caso / "v01").write_text("suelto", encoding="utf-8")
    roto = tmp_path / "roto"
    _enlazar_dir(roto, dir_caso / "v0001")
    shutil.rmtree(str(roto))                                             # junction/symlink ROTA
    r = rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg, raiz)
    assert os.path.basename(r["path"]) == "v001" and _json(dir_caso / "v001" / "validation.json")["status"] == "rejected"
    difs = rec.comprobar_indice(str(store))
    assert any("v01:" in d and "no es un directorio de version" in d for d in difs), difs
    assert any("v0001" in d and "enlace" in d for d in difs), difs
    assert not any("duplicada" in d for d in difs), difs
    n, avisos = rec.reconstruir_indice(str(store))
    assert n == 1 and any("v01:" in a for a in avisos) and any("v0001" in a for a in avisos), avisos
    g = rec.grabar(_caso(outcome="corrected", supersedes_case="geo-ramp.steep@v001"), cfg, raiz)
    assert g["version"] == 2                                             # la pista salta lo ocupado


def test_f2fix3_gap75_m4_metadata_con_mtime_futuro_sin_linea_no_esta_en_curso(tmp_path):
    """#75 M4: una version completa sin linea en el indice con `metadata.json` de `mtime` FUTURO es
    una diferencia, nunca «en curso» (`0 <= edad` de la gracia)."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    open(os.path.join(str(store), rec.INDICE), "wb").close()
    futuro = time.time() + 3600
    os.utime(str(store / "cases" / "ramp.steep" / "v001" / "metadata.json"), (futuro, futuro))
    difs, en_curso = rec.comprobar_indice_detalle(str(store))
    assert any("v001" in d and "no en el indice" in d for d in difs), difs
    assert not any("v001" in e for e in en_curso), en_curso


def test_f2fix3_gap75_m7_set_status_recomprueba_enlaces_de_fichero_con_el_bloqueo(tmp_path, monkeypatch):
    """#75 M7: `validation.json` que pasa a ser un enlace justo antes de tomar el bloqueo (tras la
    comprobacion de fuera) se rechaza CON el bloqueo, sin leerlo ni escribir."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    val = store / "cases" / "ramp.steep" / "v001" / "validation.json"
    real, real_leer, enlazado, leidos = rec._stat_sin_seguir, rec._leer_json_reintentando, [], []
    monkeypatch.setattr(rec, "_stat_sin_seguir",
                        lambda x: _St(stat.S_IFLNK) if enlazado and _nombre(x) == "validation.json" else real(x))
    monkeypatch.setattr(rec, "_leer_json_reintentando", lambda ruta, *a: leidos.append(os.path.basename(ruta)) or real_leer(ruta, *a))
    _bloqueo_con_gancho(monkeypatch, lambda: enlazado.append(1))
    with pytest.raises(rec.Rechazo) as e:
        rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg, raiz)
    assert "enlace" in str(e.value) and "validation.json" not in leidos, leidos
    assert _json(val)["status"] == "pending"


def test_f2fix3_gap75_m15_w_recomprueba_enlaces_tras_s1(tmp_path, monkeypatch):
    """#75 M15: una junction que ocupa la version reservada DESPUES de S1 (hacia `docs/knowledge/`)
    se detecta en W: rechazo y nada escrito a traves de ella."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    aprobado = tmp_path / "proj" / "docs" / "knowledge" / "approved"
    aprobado.mkdir(parents=True)
    real = rec._reservar

    def reservar_y_enlazar(*a, **k):
        destino = real(*a, **k)
        os.rmdir(destino)
        _enlazar_dir(aprobado, destino)
        return destino

    monkeypatch.setattr(rec, "_reservar", reservar_y_enlazar)
    with pytest.raises(rec.Rechazo) as e:
        rec.grabar(_caso(), cfg, raiz)
    assert "enlace" in str(e.value) or "docs/knowledge" in str(e.value), str(e.value)
    assert os.listdir(str(aprobado)) == []


def test_f2fix3_gap76_fallo_de_bloqueo_que_no_es_contencion_es_permanente_exit_2(tmp_path, monkeypatch, capsys):
    """#76: `ENOLCK` (o cualquier fallo del bloqueo que no sea contencion) es PERMANENTE: exit 2 al
    instante, sin esperar ni decir «reintenta»; la contencion (`EACCES`/`EWOULDBLOCK`) sigue siendo
    exit 3. No se escribe nada."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    _escribir_config(tmp_path, cfg)
    caso = tmp_path / "caso.json"
    caso.write_text(json.dumps(_caso()), encoding="utf-8")
    rec.reconstruir_indice(str(store))
    antes = sorted(_ficheros(str(store))), _bytes_del_store(str(store))
    monkeypatch.setattr(rec, "ESPERA_BLOQUEO_S", 5.0)

    def sin_bloqueos(_f):
        raise OSError(errno.ENOLCK, "No locks available")

    monkeypatch.setattr(rec, "_intentar_bloqueo", sin_bloqueos)
    capsys.readouterr()
    t0 = time.monotonic()
    assert rec.main(["record", str(caso), "--project-root", raiz]) == 2
    assert rec.main(["set-status", "geo-ramp.steep", "1", "rejected", "--project-root", raiz]) == 2
    assert rec.main(["index", "rebuild", "--project-root", raiz]) == 2
    assert time.monotonic() - t0 < 3                                     # sin agotar los 5 s de espera
    err = capsys.readouterr().err
    assert err.count("error permanente") == 3 and "reintenta" not in err, err
    for codigo in (errno.EACCES, errno.EWOULDBLOCK):
        monkeypatch.setattr(rec, "ESPERA_BLOQUEO_S", 0.2)
        monkeypatch.setattr(rec, "_intentar_bloqueo", lambda _f, c=codigo: (_ for _ in ()).throw(OSError(c, "tomado")))
        assert rec.main(["set-status", "geo-ramp.steep", "1", "rejected", "--project-root", raiz]) == 3
    assert (sorted(_ficheros(str(store))), _bytes_del_store(str(store))) == antes


def test_f2fix3_gap76_indice_de_solo_lectura_es_permanente_y_el_consejo_no_entra_en_bucle(tmp_path, monkeypatch, capsys):
    """#76: indice de solo lectura -> `record` graba (exit 0) con un aviso PERMANENTE que manda
    arreglar los permisos (no «reponlo con rebuild» a secas) y `index rebuild` sale con exit 2 (no
    3/3 exit 3 «reintenta»). Simulado (cualquier SO) y con el atributo real cuando surte efecto."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    _escribir_config(tmp_path, cfg)
    caso = tmp_path / "caso.json"
    caso.write_text(json.dumps(_caso()), encoding="utf-8")
    ruta = os.path.join(str(store), rec.INDICE)

    def comprobar():
        capsys.readouterr()
        assert rec.main(["record", str(caso), "--project-root", raiz]) == 0
        err = capsys.readouterr().err
        assert "PERMANENTE" in err and "arregla los permisos" in err, err
        assert rec.main(["index", "rebuild", "--project-root", raiz]) == 2
        err = capsys.readouterr().err
        assert "error permanente" in err and "solo lectura" in err and "reintenta" not in err, err

    with monkeypatch.context() as m:
        real_access, real_open = os.access, builtins.open
        m.setattr(rec.os, "access", lambda p, modo, *a, **k: False if os.path.basename(str(p)) == rec.INDICE
                  and modo == os.W_OK else real_access(p, modo, *a, **k))

        def solo_lectura(p, modo="r", *a, **k):
            if os.path.basename(str(p)) == rec.INDICE and ("a" in modo or "w" in modo):
                raise PermissionError(errno.EACCES, "Permiso denegado (solo lectura)")
            return real_open(p, modo, *a, **k)

        m.setattr(rec, "open", solo_lectura, raising=False)
        comprobar()
    if os.name == "nt" or os.geteuid() != 0:                               # root ignora el modo
        os.chmod(ruta, stat.S_IREAD)
        try:
            comprobar()
        finally:
            os.chmod(ruta, stat.S_IREAD | stat.S_IWRITE)


def test_f2fix3_gap77_enlace_duro_plantado_en_el_temporal_no_se_sigue(tmp_path, monkeypatch):
    """#77 (escenario literal): alguien planta en `cases/.tmp-*/metadata.json` un enlace duro a un ADR
    curado (fix4, #82: el temporal ya no existe durante la espera de S1; se planta justo despues de
    crearlo, la unica ventana que queda): el fichero se crea con `O_EXCL` -> rechazo, el ADR intacto y
    nada grabado (la reserva queda vacia: no hay borrado)."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    adr = tmp_path / "proj" / "docs" / "knowledge" / "approved" / "ADR-001.md"
    adr.parent.mkdir(parents=True)
    adr.write_bytes(b"curado\n")
    real_mk = rec.tempfile.mkdtemp

    def mk_y_plantar(*a, **k):
        t = real_mk(*a, **k)
        _hardlink(adr, os.path.join(t, "metadata.json"))
        return t

    monkeypatch.setattr(rec.tempfile, "mkdtemp", mk_y_plantar)
    with pytest.raises(rec.Rechazo) as e:
        rec.grabar(_caso(), cfg, raiz)
    assert "ya existia en el temporal" in str(e.value)
    assert adr.read_bytes() == b"curado\n"
    assert not (store / "cases" / "ramp.steep" / "v002" / "metadata.json").exists()
    assert not [n for n in os.listdir(str(store / "cases")) if n.startswith(rec.PREFIJO_TEMPORAL)]
    assert [e["version"] for e in rec.listar(str(store))] == [1]


def test_f2fix3_gap78_temporal_del_rebuild_no_se_reabre_por_ruta_y_se_comprueba(tmp_path, monkeypatch):
    """#78: el temporal del rebuild se escribe por el descriptor de `mkstemp` hasta la sustitucion
    (nunca se reabre por ruta) y, antes del `os.replace`, se comprueba que sigue siendo nuestro: con
    un enlace duro plantado (`st_nlink > 1`) o el nombre sustituido -> rechazo, indice intacto."""
    raiz, cfg, store = _proyecto(tmp_path)
    for _ in range(2):
        rec.grabar(_caso(), cfg, raiz)
    ruta = os.path.join(str(store), rec.INDICE)
    with open(ruta, "rb") as f:
        antes = f.read()
    otro = tmp_path / "otro-nombre"

    def al_tomar_f2(gancho):
        vistos = []

        class EnF2(rec._Bloqueo):
            def __enter__(self):
                vistos.append(os.path.basename(self.ruta))
                if vistos == [rec.BLOQUEO_REBUILD, rec.BLOQUEO_INDICE, rec.BLOQUEO_INDICE]:
                    gancho([str(store / n) for n in os.listdir(str(store)) if n.startswith(rec.PREFIJO_TEMPORAL)])
                return super().__enter__()
        return EnF2

    def enlace_duro(tmps):
        assert len(tmps) == 1, tmps
        _hardlink(tmps[0], otro)

    with monkeypatch.context() as m:
        m.setattr(rec, "_Bloqueo", al_tomar_f2(enlace_duro))
        with pytest.raises(rec.Rechazo) as e:
            rec.reconstruir_indice(str(store))
    assert "enlaces duros" in str(e.value)
    with open(ruta, "rb") as f:
        assert f.read() == antes
    assert not [n for n in os.listdir(str(store)) if n.startswith(rec.PREFIJO_TEMPORAL)]

    def sustituir(tmps):
        try:
            os.remove(tmps[0])
        except PermissionError:                                          # Windows: abierto, no se puede
            return
        with open(tmps[0], "wb") as f:
            f.write(b"ajeno\n")

    with monkeypatch.context() as m:
        m.setattr(rec, "_Bloqueo", al_tomar_f2(sustituir))
        if os.name == "nt":
            assert rec.reconstruir_indice(str(store))[0] == 2
        else:
            with pytest.raises(rec.Rechazo) as e:
                rec.reconstruir_indice(str(store))
            assert "sustituido" in str(e.value)
    assert rec.comprobar_indice(str(store)) == []


def test_f2fix3_gap79_metadata_o_validation_con_enlace_duro_se_rechazan_y_se_omiten(tmp_path):
    """#79: `validation.json`/`metadata.json` que son un ENLACE DURO a un fichero de fuera: `set-status`
    rechaza antes de leer (no copia su `reviewer_note`) y `check`/`rebuild` omiten la version."""
    raiz, cfg, store = _proyecto(tmp_path)
    r = rec.grabar(_caso(), cfg, raiz)
    for fichero in ("validation.json", "metadata.json"):
        ruta = os.path.join(r["path"], fichero)
        fuera = tmp_path / f"fuera-{fichero}"
        with open(ruta, "rb") as f:
            original = f.read()
        datos = json.loads(original)
        if fichero == "validation.json":
            datos["reviewer_note"] = "FUERA"
        fuera.write_text(json.dumps(datos), encoding="utf-8")
        os.remove(ruta)
        _hardlink(fuera, ruta)
        with pytest.raises(rec.Rechazo) as e:
            rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg, raiz)
        assert "enlace duro" in str(e.value), fichero
        assert json.loads(fuera.read_text(encoding="utf-8")) == datos
        difs = rec.comprobar_indice(str(store))
        assert any("v001" in d and "enlace duro" in d for d in difs), difs
        n, avisos = rec.reconstruir_indice(str(store))
        assert n == 0 and any("enlace duro" in a for a in avisos), avisos
        assert "FUERA" not in open(os.path.join(str(store), rec.INDICE), encoding="utf-8").read()
        os.remove(ruta)
        with open(ruta, "wb") as f:
            f.write(original)
        rec.reconstruir_indice(str(store))


def test_f2fix3_gap80_temporales_huerfanos_se_reportan_sin_borrarlos(tmp_path, monkeypatch, capsys):
    """#80: `check` reporta los `.tmp-*` de `cases/`, de un caso y de la raiz del store: recientes,
    «en curso» (informativo); pasada la gracia o con `mtime` futuro, «temporal huerfano» (exit 1, con
    la ruta). Nunca los borra."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    _escribir_config(tmp_path, cfg)
    t1 = store / "cases" / ".tmp-muerto"
    t1.mkdir()
    (t1 / "request.json").write_text("{}", encoding="utf-8")
    t2 = store / "cases" / "ramp.steep" / ".tmp-viejo"
    t2.write_text("x", encoding="utf-8")
    t3 = store / ".tmp-rebuild"
    t3.write_bytes(b"")
    rels = ("cases/.tmp-muerto", "cases/ramp.steep/.tmp-viejo", ".tmp-rebuild")
    difs, en_curso = rec.comprobar_indice_detalle(str(store))
    assert difs == [] and all(any(r in e and "en curso" in e for e in en_curso) for r in rels), (difs, en_curso)
    for cuando in (time.time() - 3600, time.time() + 3600):
        for t in (t1, t2, t3):
            os.utime(str(t), (cuando, cuando))
        difs, en_curso = rec.comprobar_indice_detalle(str(store))
        assert all(any(r in d and "temporal huerfano" in d for d in difs) for r in rels), difs
        capsys.readouterr()
        assert rec.main(["index", "check", "--project-root", raiz]) == 1
    assert t1.exists() and t2.exists() and t3.exists() and (t1 / "request.json").exists()


# ------------------------------------------------------------------ fix4 (verificacion dirigida fix3, Fase 2)
# Gaps #81-#92 con el arbitraje del orquestador (tasks.md, «Verificacion dirigida — fix3: Fase 2»).


def _distingue_mayusculas(d):
    """True si el directorio `d` (que existe) distingue mayusculas en sus nombres."""
    a, b = os.path.join(str(d), ".sonda-a"), os.path.join(str(d), ".SONDA-A")
    os.mkdir(a)
    try:
        os.mkdir(b)
    except FileExistsError:
        return False
    finally:
        for x in (a, b):
            try:
                os.rmdir(x)
            except OSError:
                pass
    return True


def _cases_que_distingue_mayusculas(store):
    """`<store>/cases` VACIO que distingue mayusculas: natural en Linux; en Windows, por directorio
    con `fsutil file setCaseSensitiveInfo` (la semantica de un sistema POSIX). False si no se puede."""
    cases = store / "cases"
    cases.mkdir(parents=True)
    if os.name == "nt":
        subprocess.run(["fsutil.exe", "file", "setCaseSensitiveInfo", str(cases), "enable"], capture_output=True)
    return _distingue_mayusculas(cases)


def test_f2fix4_gap81_caso_nuevo_sin_scandir_de_cases_con_el_bloqueo(tmp_path, monkeypatch):
    """#81: un caso NUEVO se crea con el bloqueo por `os.mkdir(cases/<family>.<variant>)` (O(1)): con
    `.cases_index.lock` tomado no hay NINGUN `scandir`/`listdir` y el numero de llamadas es el mismo
    con 2 que con 42 casos en el store (antes, el recorrido O(C) de mayusculas en cada caso nuevo)."""
    raiz, cfg, store = _proyecto(tmp_path, family_pattern="^[A-Za-z0-9]+$")
    rec.grabar(_caso_fv("uno"), cfg, raiz)
    rec.grabar(_caso_fv("dos"), cfg, raiz)

    def medir(fam):
        with monkeypatch.context() as m:
            cuenta = _llamadas_con_el_bloqueo(m)
            rec.grabar(_caso_fv(fam), cfg, raiz)
        return dict(cuenta)

    base = medir("nuevoa")
    for i in range(40):
        rec.grabar(_caso_fv(f"fam{i}"), cfg, raiz)
    grande = medir("nuevob")
    assert base["scandir"] == 0 and base["listdir"] == 0, base
    assert grande == base, (base, grande)


def test_f2fix4_gap81_variante_creada_a_la_vez_ntfs_rechaza_y_posix_check_reporta_la_pareja(tmp_path, monkeypatch):
    """#81 (arbitraje): mientras `record` de `ramp.steep` (caso nuevo) espera S1, otro crea
    `cases/RAMP.steep`. En un `cases/` que NO distingue mayusculas (NTFS/APFS) el `mkdir` del caso
    choca -> recorrido O(C) -> rechazo de mayusculas, nada grabado. En uno que SI las distingue
    (POSIX; en Windows, `setCaseSensitiveInfo`) son directorios distintos: se graba, `index check`
    reporta la PAREJA como incoherencia (exit 1) y el siguiente `record` lo rechaza el recorrido de
    fuera (limite declarado)."""
    vistos = set()
    for nombre in ("nativo", "sensible"):
        sub = tmp_path / nombre
        sub.mkdir()
        raiz, cfg, store = _proyecto(sub, family_pattern="^[A-Za-z0-9]+$")
        if nombre == "sensible":
            if not _cases_que_distingue_mayusculas(store):
                continue
        else:
            (store / "cases").mkdir(parents=True)
        sensible = _distingue_mayusculas(store / "cases")
        vistos.add(sensible)
        with monkeypatch.context() as m:
            _bloqueo_con_gancho(m, lambda s=store: os.mkdir(str(s / "cases" / "RAMP.steep")))
            if sensible:
                r = rec.grabar(_caso(), cfg, raiz)
                assert r["ref"] == "geo-ramp.steep@v001", r
            else:
                with pytest.raises(rec.Rechazo) as e:
                    rec.grabar(_caso(), cfg, raiz)
                assert "mayusculas" in str(e.value)
                assert [n for n in os.listdir(str(store / "cases")) if not n.startswith(".")] == ["RAMP.steep"]
                assert os.listdir(str(store / "cases" / "RAMP.steep")) == []
                continue
        difs = rec.comprobar_indice(str(store))
        assert any("ramp.steep" in d and "RAMP.steep" in d and "mayusculas" in d for d in difs), difs
        _escribir_config(sub, cfg)
        assert rec.main(["index", "check", "--project-root", raiz]) == 1
        with pytest.raises(rec.Rechazo) as e:
            rec.grabar(_caso(), cfg, raiz)
        assert "mayusculas" in str(e.value)
    assert vistos, "ningun escenario ejecutado"


def test_f2fix4_gap81_carrera_de_creacion_con_procesos_en_cases_que_distingue_mayusculas(tmp_path):
    """#81, PROCESOS reales en un `cases/` que distingue mayusculas (la semantica POSIX): cuatro
    procesos graban A LA VEZ `ramp.steep` y `RAMP.steep`. Invariante: todos terminan sin error, cada
    directorio solo tiene versiones del `case_id` de su nombre exacto, los rechazados lo son por
    mayusculas y, si quedan DOS directorios, `index check` reporta la pareja."""
    for ronda in range(4):
        base = tmp_path / f"r{ronda}"
        base.mkdir()
        raiz, cfg, store = _proyecto(base, family_pattern="^[A-Za-z0-9]+$")
        if not _cases_que_distingue_mayusculas(store):
            pytest.skip("este sistema no permite un directorio que distinga mayusculas")
        go = base / "go"
        familias = ("ramp", "RAMP", "ramp", "RAMP")
        procs = [subprocess.Popen([sys.executable, "-c", _CREADOR, RECORDER_PATH, json.dumps(cfg), raiz, fam,
                                   str(base / f"listo{i}"), str(go)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True, encoding="utf-8") for i, fam in enumerate(familias)]
        for p in procs:
            p.stdin.write(json.dumps(_caso()))
            p.stdin.close()
        for i, p in enumerate(procs):
            assert _esperar(base / f"listo{i}", p), p.communicate(timeout=30)
        go.write_text("", encoding="utf-8")
        salidas = []
        for p in procs:
            out, err = p.stdout.read(), p.stderr.read()
            p.wait(timeout=120)
            assert p.returncode == 0, err[-400:]
            salidas.append(json.loads(out))
        dirs = sorted(n for n in os.listdir(str(store / "cases")) if not n.startswith("."))
        assert 1 <= len(dirs) <= 2, (ronda, dirs)
        for d in dirs:
            dueno = f"geo-{d.split('.')[0]}.steep"
            assert {_json(store / "cases" / d / v / "metadata.json")["case_id"]
                    for v in os.listdir(str(store / "cases" / d))} == {dueno}, (ronda, d)
        assert all("mayusculas" in s["rechazo"] for s in salidas if "rechazo" in s), (ronda, salidas)
        difs = rec.comprobar_indice(str(store))
        if len(dirs) == 2:
            assert any("mayusculas" in d and "RAMP.steep" in d and "ramp.steep" in d for d in difs), difs
        else:
            assert difs == [], difs


def test_f2fix4_gap82_el_temporal_se_crea_despues_de_s1_y_sin_bloqueo(tmp_path, monkeypatch):
    """#82: el temporal `cases/.tmp-*` de `record` se crea DESPUES de S1 (tras soltar el bloqueo): la
    espera del bloqueo, que un tercero controla, deja de ser una ventana para plantar nada en el."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    tomados, orden = _espia_de_bloqueos_por_nombre(monkeypatch)
    eventos, real_mk = [], rec.tempfile.mkdtemp
    monkeypatch.setattr(rec.tempfile, "mkdtemp",
                        lambda *a, **k: eventos.append((len(orden), tuple(tomados))) or real_mk(*a, **k))
    rec.grabar(_caso(), cfg, raiz)
    assert eventos == [(1, ())], eventos                      # 1 bloqueo (S1) ya tomado y soltado


def _ficheros_bajo(d):
    return [os.path.join(b, f) for b, _ds, fs in os.walk(str(d)) for f in fs]


def test_f2fix4_gap82_junction_plantada_en_el_temporal_no_escribe_fuera(tmp_path, monkeypatch):
    """#82, escenario literal 1: una junction `cases/.tmp-X` -> `docs/knowledge/approved/` (a) plantada
    durante la espera de S1 sobre todo temporal que exista y (b) que sustituye al temporal recien
    creado: `record` no escribe NADA en `approved/` (antes, `metadata.json` ya existia alli)."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    aprobado = tmp_path / "proj" / "docs" / "knowledge" / "approved"
    aprobado.mkdir(parents=True)
    cases = store / "cases"

    def plantar():                                              # (a) durante la espera de S1
        for n in os.listdir(str(cases)):
            if n.startswith(rec.PREFIJO_TEMPORAL):
                shutil.rmtree(str(cases / n))
                _enlazar_dir(aprobado, cases / n)

    with monkeypatch.context() as m:
        _bloqueo_con_gancho(m, plantar)
        try:
            rec.grabar(_caso(), cfg, raiz)
        except rec.Rechazo:
            pass
    assert _ficheros_bajo(aprobado) == [], _ficheros_bajo(aprobado)
    real_mk = rec.tempfile.mkdtemp

    def mk(*a, **k):                                            # (b) el temporal recien creado
        t = real_mk(*a, **k)
        os.rmdir(t)
        _enlazar_dir(aprobado, t)
        return t

    monkeypatch.setattr(rec.tempfile, "mkdtemp", mk)
    with pytest.raises(rec.Rechazo) as e:
        rec.grabar(_caso(), cfg, raiz)
    assert "enlace" in str(e.value) or "docs/knowledge" in str(e.value), str(e.value)
    assert _ficheros_bajo(aprobado) == [], _ficheros_bajo(aprobado)
    assert not [n for n in os.listdir(str(cases)) if n.startswith(rec.PREFIJO_TEMPORAL)]


@pytest.mark.parametrize("donde", ["temporal", "version"])
def test_f2fix4_gap82_junction_en_final_entre_mkdir_y_la_escritura_no_escribe_fuera(tmp_path, monkeypatch, donde):
    """#82, escenario literal 2: `final/` (del temporal o de la version reservada) sustituido por una
    junction hacia `docs/knowledge/approved/` justo despues de su `os.mkdir`: el `realpath` del padre
    se recomprueba antes de crear (o mover) cada fichero -> rechazo, nada en `approved/`."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    aprobado = tmp_path / "proj" / "docs" / "knowledge" / "approved"
    aprobado.mkdir(parents=True)
    real_mkdir, hecho = os.mkdir, []

    def mkdir(p, *a, **k):
        real_mkdir(p, *a, **k)
        padre = os.path.basename(os.path.dirname(str(p)))
        es = padre.startswith(rec.PREFIJO_TEMPORAL) if donde == "temporal" else rec._es_version(padre)
        if os.path.basename(str(p)) == "final" and es and not hecho:
            hecho.append(1)
            os.rmdir(p)
            _enlazar_dir(aprobado, p)

    monkeypatch.setattr(rec.os, "mkdir", mkdir)
    fuera, canon = [], os.path.normcase(os.path.realpath(str(aprobado)))
    real_ab, real_rep = rec._abrir_exclusivo, rec._reemplazar

    def espiar(ruta):                                           # ¿se llego a crear/mover algo AHI?
        if os.path.normcase(os.path.realpath(os.path.dirname(ruta))) == canon:
            fuera.append(ruta)

    monkeypatch.setattr(rec, "_abrir_exclusivo", lambda ruta: espiar(ruta) or real_ab(ruta))
    monkeypatch.setattr(rec, "_reemplazar", lambda o, d: espiar(d) or real_rep(o, d))
    with pytest.raises(rec.Rechazo) as e:
        rec.grabar(_caso(), cfg, raiz)
    assert hecho and ("enlace" in str(e.value) or "docs/knowledge" in str(e.value)), str(e.value)
    assert _ficheros_bajo(aprobado) == [], _ficheros_bajo(aprobado)
    assert fuera == [], fuera                                   # ni siquiera un instante (padre ANTES)


@pytest.mark.parametrize("paso", ["creacion", "movimiento"])
def test_f2fix4_gap82_padre_cambiado_entre_la_comprobacion_y_la_creacion_se_detecta_despues(tmp_path, monkeypatch, paso):
    """#82: la ventana residual (microsegundos, sin `openat` portable) entre recomprobar el padre y
    crear (o mover) el fichero: si el padre se sustituye justo ahi, el `realpath` del fichero YA
    creado lo delata -> se elimina SOLO ese fichero (el nuestro: misma identidad) y se rechaza."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    aprobado = tmp_path / "proj" / "docs" / "knowledge" / "approved"
    aprobado.mkdir(parents=True)
    (aprobado / "ADR-001.md").write_bytes(b"curado\n")
    real_ab, real_rep, hecho = rec._abrir_exclusivo, rec._reemplazar, []

    def cambiar_padre(ruta):
        padre = os.path.dirname(ruta)
        if os.path.basename(padre) == "final" and not hecho:
            hecho.append(1)
            os.rmdir(padre)
            _enlazar_dir(aprobado, padre)

    if paso == "creacion":
        monkeypatch.setattr(rec, "_abrir_exclusivo", lambda ruta: cambiar_padre(ruta) or real_ab(ruta))
    else:
        monkeypatch.setattr(rec, "_reemplazar", lambda o, d: cambiar_padre(d) or real_rep(o, d))
    with pytest.raises(rec.Rechazo) as e:
        rec.grabar(_caso(), cfg, raiz)
    assert hecho and ("enlace" in str(e.value) or "docs/knowledge" in str(e.value)), str(e.value)
    assert sorted(os.listdir(str(aprobado))) == ["ADR-001.md"]
    assert (aprobado / "ADR-001.md").read_bytes() == b"curado\n"


def _fuera_json(tmp_path, nombre, datos):
    p = tmp_path / nombre
    p.write_text(json.dumps(datos), encoding="utf-8")
    return p


def _sustituir_al_primer_open(monkeypatch, fichero, sustituir):
    """`open` del recorder que, la PRIMERA vez que se abre `fichero`, ejecuta `sustituir()` y falla con
    `PermissionError` (un handle ajeno): la sustitucion ocurre DURANTE los reintentos."""
    real_open, hecho = builtins.open, []

    def open_(ruta, *a, **k):
        if os.path.basename(str(ruta)) == fichero and not hecho:
            hecho.append(1)
            sustituir()
            raise PermissionError(13, "en uso")
        return real_open(ruta, *a, **k)

    monkeypatch.setattr(rec, "open", open_, raising=False)
    monkeypatch.setattr(rec.time, "sleep", lambda _s: None)
    return hecho


@pytest.mark.parametrize("como", ["enlace_duro", "otro_fichero"])
def test_f2fix4_gap83_set_status_lee_por_descriptor_la_sustitucion_durante_los_reintentos(tmp_path, monkeypatch, como):
    """#83 (escenario literal): `validation.json` sustituido por un enlace DURO a un JSON de fuera (o
    por otro fichero) mientras `set-status` reintenta la apertura: la comprobacion va sobre el
    DESCRIPTOR (`fstat`: regular, `st_nlink == 1`, misma identidad que el `lstat` previo) -> rechazo;
    su `reviewer_note` no se copia al store y el indice no cambia."""
    raiz, cfg, store = _proyecto(tmp_path)
    r = rec.grabar(_caso(), cfg, raiz)
    val = os.path.join(r["path"], "validation.json")
    datos = {"status": "pending", "approved_by_human": False, "approved_at": None, "reviewer_note": "FUERA"}
    fuera = _fuera_json(tmp_path, "fuera.json", datos)

    def sustituir():
        os.remove(val)
        if como == "enlace_duro":
            _hardlink(fuera, val)
        else:
            with builtins.open(val, "w", encoding="utf-8") as f:
                json.dump(datos, f)

    hecho = _sustituir_al_primer_open(monkeypatch, "validation.json", sustituir)
    if como == "enlace_duro":                                   # la amenaza real: rechazo por `st_nlink`
        with pytest.raises(rec.Rechazo) as e:
            rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg, raiz)
        assert hecho and "enlace duro" in str(e.value), str(e.value)
        assert [x["status"] for x in _indice(store)] == ["pending"]
    else:
        # fix4-bis (orquestador + Lente B): «otro fichero» DENTRO del store. Invariante en ambos SO: nada
        # de fuera del store se copia. O se rechaza por identidad distinta (NTFS; en POSIX, `ctime`),
        # o —si el SO reutilizo el inodo y la identidad casara— lo leido es un fichero regular del
        # store con un solo nombre (`st_nlink == 1`): no hay fuga
        try:
            rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg, raiz)
            st = os.lstat(val)
            assert stat.S_ISREG(st.st_mode) and st.st_nlink == 1
        except rec.Rechazo as rechazo:
            assert "sustituido" in str(rechazo), str(rechazo)
            assert [x["status"] for x in _indice(store)] == ["pending"]
        assert hecho
    assert json.loads(fuera.read_text(encoding="utf-8")) == datos


def test_f2fix4_gap83_lectores_leen_por_descriptor(tmp_path, monkeypatch):
    """#83 en los lectores (S2, rebuild, check, dueño, `supersedes`): un fichero de version sustituido
    por un enlace DURO durante los reintentos se omite (o se rechaza) sin leer su contenido; uno
    sustituido por OTRO fichero regular (un `os.replace` legitimo) se vuelve a comprobar y se lee."""
    raiz, cfg, store = _proyecto(tmp_path)
    r = rec.grabar(_caso(), cfg, raiz)
    dir_v = r["path"]
    for fichero in ("validation.json", "metadata.json"):
        ruta = os.path.join(dir_v, fichero)
        with open(ruta, "rb") as f:
            original = f.read()
        fuera = tmp_path / f"fuera-{fichero}"
        fuera.write_bytes(original.replace(b"pending", b"rejected"))

        def enlazar(ruta=ruta, fuera=fuera):
            os.remove(ruta)
            _hardlink(fuera, ruta)

        with monkeypatch.context() as m:
            _sustituir_al_primer_open(m, fichero, enlazar)
            obj, _mt, aviso = rec._leer_de_version(dir_v, fichero, "cases/ramp.steep/v001")
        assert obj is None and aviso and "enlace duro" in aviso, (obj, aviso)
        with pytest.raises(rec.Rechazo) as e:                   # sin `lstat` previo: el descriptor manda
            rec._leer_json_reintentando(ruta)
        assert "enlace duro" in str(e.value)
        if fichero == "metadata.json":
            os.remove(ruta)
            with open(ruta, "wb") as f:
                f.write(original)
            with monkeypatch.context() as m:
                _sustituir_al_primer_open(m, fichero, enlazar)
                with pytest.raises(rec.Rechazo) as e:
                    rec._leer_metadata_sin_enlace(dir_v)
            assert "enlace duro" in str(e.value)
        os.remove(ruta)
        with open(ruta, "wb") as f:
            f.write(original)

    def otro_regular():                                         # sustitucion legitima: se relee
        tmp = os.path.join(dir_v, "nuevo.tmp")
        with builtins.open(tmp, "wb") as f:
            f.write(json.dumps({"status": "rejected", "approved_by_human": False, "approved_at": None,
                                "reviewer_note": None}).encode("utf-8"))
        os.replace(tmp, os.path.join(dir_v, "validation.json"))

    with monkeypatch.context() as m:
        _sustituir_al_primer_open(m, "validation.json", otro_regular)
        obj, _mt, aviso = rec._leer_de_version(dir_v, "validation.json", "cases/ramp.steep/v001")
    assert aviso is None and obj["status"] == "rejected", (obj, aviso)


def test_f2fix4_gap84_check_reporta_un_fragmento_final_persistente(tmp_path):
    """#84: un escritor muerto a mitad de linea deja un fragmento final sin `\\n`; `check` lo reporta
    si PERSISTE en la confirmacion final (mismos bytes al releer), como `list` avisa de la linea
    ignorada; `rebuild` lo descarta y `check` vuelve a estar limpio."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    ruta = os.path.join(str(store), rec.INDICE)
    linea = rec._linea(_indice(store)[0])
    with open(ruta, "ab") as f:
        f.write(linea[:len(linea) // 2])
    difs = rec.comprobar_indice(str(store))
    assert any("fragmento" in d and "sin salto" in d for d in difs), difs
    assert rec.listar_con_avisos(str(store))[1], "list avisa de la linea ignorada"
    rec.reconstruir_indice(str(store))
    assert rec.comprobar_indice(str(store)) == []


def test_f2fix4_gap84_un_fragmento_que_se_completa_durante_el_check_no_se_reporta(tmp_path, monkeypatch):
    """#84: sin falso positivo con un append EN CURSO: si el fragmento se completa entre la primera
    lectura y la confirmacion, no se reporta."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    ruta = os.path.join(str(store), rec.INDICE)
    linea = rec._linea(_indice(store)[0])
    mitad = len(linea) // 2
    with open(ruta, "ab") as f:
        f.write(linea[:mitad])
    real, hecho = rec._claves_con_diferencia, []

    def completar(*a, **k):
        if not hecho:
            hecho.append(1)
            with open(ruta, "ab") as f:
                f.write(linea[mitad:])
        return real(*a, **k)

    monkeypatch.setattr(rec, "_claves_con_diferencia", completar)
    assert rec.comprobar_indice_detalle(str(store)) == ([], []) and hecho


def test_f2fix4_gap85_check_reporta_los_temporales_de_cada_version(tmp_path):
    """#85: el temporal de `_escribir_atomico` vive en el directorio de la VERSION; `check` lo reporta
    con la misma regla de gracia que #80 (reciente: «en curso»; viejo o futuro: «temporal huerfano»,
    exit 1) y nunca lo borra; `rebuild` avisa del huerfano."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    t = store / "cases" / "ramp.steep" / "v001" / ".tmp-muerto"
    t.write_text("{}", encoding="utf-8")
    rel = "cases/ramp.steep/v001/.tmp-muerto"
    difs, en_curso = rec.comprobar_indice_detalle(str(store))
    assert difs == [] and any(rel in e and "en curso" in e for e in en_curso), (difs, en_curso)
    for cuando in (time.time() - 3600, time.time() + 3600):
        os.utime(str(t), (cuando, cuando))
        difs = rec.comprobar_indice(str(store))
        assert any(rel in d and "temporal huerfano" in d for d in difs), difs
    assert any(rel in a for a in rec.reconstruir_indice(str(store))[1])
    assert t.exists()


def _primera_linea(crudo):
    return json.loads(crudo.splitlines()[0])


def test_f2fix4_gap86_truncado_in_situ_y_regrabado_durante_el_rebuild_vuelve_a_f0(tmp_path, monkeypatch):
    """#86: con `st_ino != 0` la identidad tambien lleva la ventana de 64 KiB previa al offset: un
    indice truncado IN SITU (mismo inodo) y regrabado por encima del offset durante el rebuild se
    detecta (vuelta a F0) en vez de dar exit 0 con un indice obsoleto."""
    raiz, cfg, store = _proyecto(tmp_path)
    for _ in range(2):
        rec.grabar(_caso(), cfg, raiz)
    ruta = os.path.join(str(store), rec.INDICE)
    assert os.stat(ruta).st_ino != 0
    real_ident, real_f1, f0s = rec._identidad, rec.estado_de_cases, []
    monkeypatch.setattr(rec, "_identidad", lambda r: f0s.append(1) or real_ident(r))

    def f1(*a, **k):
        if len(f0s) == 1:
            with open(ruta, "r+b") as f:
                crudo = f.read()
                f.seek(0)
                f.truncate()
                f.write(crudo.replace(b'"pending"', b'"PENDING"') + rec._linea(_primera_linea(crudo)))
        return real_f1(*a, **k)

    monkeypatch.setattr(rec, "estado_de_cases", f1)
    n, _avisos = rec.reconstruir_indice(str(store))
    assert len(f0s) == 2 and n == 2, (len(f0s), n)
    monkeypatch.setattr(rec, "estado_de_cases", real_f1)
    assert rec.comprobar_indice(str(store)) == []


def test_f2fix4_gap87_la_pista_solo_cuenta_directorios_de_version_en_rango(tmp_path):
    """#87: un fichero suelto `v999999999` (o `v` + 200 digitos) o un directorio fuera de rango no
    bloquean el `record` automatico del caso: la pista usa el criterio de #74 (directorio real con
    nombre de version en rango); lo demas lo reporta `check`."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    d = store / "cases" / "ramp.steep"
    (d / "v999999999").write_text("x", encoding="utf-8")
    assert rec.grabar(_caso(), cfg, raiz)["version"] == 2
    (d / ("v" + "9" * 200)).write_text("x", encoding="utf-8")
    assert rec.grabar(_caso(), cfg, raiz)["version"] == 3
    (d / ("v" + "9" * 12)).mkdir()
    assert rec.grabar(_caso(), cfg, raiz)["version"] == 4
    difs = rec.comprobar_indice(str(store))
    assert any("v999999999" in x for x in difs) and any("9" * 200 in x for x in difs), difs
    assert any("9" * 12 in x and "fuera de rango" in x for x in difs), difs


def test_f2fix4_gap88_directorio_con_versiones_de_dos_case_id_se_reporta_y_no_se_indexa_el_intruso(tmp_path, monkeypatch):
    """#88 (la carrera del limite declarado del dueño): mientras `record` de `geo-ramp.steep` espera
    S1, otro `id_prefix` (`xyz`) graba el mismo `family.variant`. Quedan `v001` de `xyz-…` y `v002` de
    `geo-…` en el MISMO directorio: `check` lo reporta (exit 1) y `rebuild` no indexa la del intruso."""
    raiz, cfg, store = _proyecto(tmp_path)
    cfg_x = dict(cfg, id_prefix="xyz")
    with monkeypatch.context() as m:
        _bloqueo_con_gancho(m, lambda: rec.grabar(_caso(case_id="xyz-ramp.steep"), cfg_x, raiz))
        r = rec.grabar(_caso(), cfg, raiz)
    assert r["ref"] == "geo-ramp.steep@v002", r
    difs = rec.comprobar_indice(str(store))
    assert any("geo-ramp.steep" in d and "xyz-ramp.steep" in d for d in difs), difs
    _escribir_config(tmp_path, cfg)
    assert rec.main(["index", "check", "--project-root", raiz]) == 1
    n, avisos = rec.reconstruir_indice(str(store))
    assert n == 1 and any("geo-ramp.steep" in a for a in avisos), (n, avisos)
    assert [(e["case_id"], e["version"]) for e in rec.listar(str(store))] == [("xyz-ramp.steep", 1)]


def test_f2fix4_gap89_la_confirmacion_solo_relee_lo_que_toco_la_cola_o_cambio(tmp_path, monkeypatch):
    """#89: con el indice AUSENTE y N versiones, la confirmacion final de `check` no relee ninguna
    del disco (la lectura de F1 ya es consistente); solo relee una clave con diferencia si la toco
    la cola o su `validation.json` cambio desde F1."""
    raiz, cfg, store = _proyecto(tmp_path)
    for _ in range(12):
        rec.grabar(_caso(), cfg, raiz)
    os.remove(os.path.join(str(store), rec.INDICE))
    _envejecer(store)
    real_rel, releidas = rec._releer_version, []
    monkeypatch.setattr(rec, "_releer_version", lambda s, f, v, numero, *a, **k: releidas.append(numero) or
                        real_rel(s, f, v, numero, *a, **k))
    difs = rec.comprobar_indice(str(store))
    assert len([d for d in difs if "no en el indice" in d]) == 12 and releidas == [], (difs, releidas)
    val = store / "cases" / "ramp.steep" / "v005" / "validation.json"
    real_f1 = rec._estado_de_cases

    def f1_y_un_set_status_muerto(*a, **k):                     # W tras F1, sin su linea (A)
        r = real_f1(*a, **k)
        tmp = str(val) + ".nuevo"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"status": "rejected", "approved_by_human": False, "approved_at": None,
                       "reviewer_note": None}, f)
        os.replace(tmp, str(val))
        return r

    monkeypatch.setattr(rec, "_estado_de_cases", f1_y_un_set_status_muerto)
    difs = rec.comprobar_indice(str(store))
    assert releidas == [5], releidas
    assert len([d for d in difs if "no en el indice" in d]) == 12, difs


def test_f2fix4_gap91_m6_linea_corrupta_en_el_residual_se_descarta_con_aviso(tmp_path, monkeypatch):
    """#91 M6: una linea corrupta en el residual del rebuild (copiado tal cual con el bloqueo) se
    DESCARTA con aviso, sin excepcion, tambien si validarla lanzara un error inesperado; el indice
    reconstruido queda limpio."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    ruta = os.path.join(str(store), rec.INDICE)
    real_cola = rec._leer_cola
    corruptas = (b"no json\n", b"[1, 2]\n", b'{"a": 1}\n', b"\xff\xfe\n", b'{"x": 1}')

    def cola(r, cursor, hasta_eof=False):
        if hasta_eof:
            with open(ruta, "ab") as f:
                f.write(b"".join(corruptas))
        return real_cola(r, cursor, hasta_eof)

    monkeypatch.setattr(rec, "_leer_cola", cola)
    n, avisos = rec.reconstruir_indice(str(store))
    assert n == 1 and len([a for a in avisos if "residual ignorada" in a]) == len(corruptas), avisos
    monkeypatch.setattr(rec, "_leer_cola", real_cola)
    assert len(_indice(store)) == 1 and rec.comprobar_indice(str(store)) == []
    real_valida = rec._entrada_valida

    def valida(e):
        if isinstance(e, dict) and e.get("family") == "rota":
            raise TypeError("inesperado")
        return real_valida(e)

    monkeypatch.setattr(rec, "_entrada_valida", valida)
    e, motivo = rec._parsear_linea(rec._linea(dict(_indice(store)[0], family="rota")))
    assert e is None and motivo, (e, motivo)


def test_f2fix4_gap91_m10_confirmacion_relee_una_clave_de_la_cola_sin_diferencia(tmp_path, monkeypatch):
    """#91 M10: una linea de la cola IGUAL a lo que ya dice F1 cuya relectura falla de forma pasajera
    deja un aviso que ninguna diferencia volveria a mirar: la confirmacion la relee (`cola_fallidas`)
    y no hay falso positivo."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    linea = _indice(store)[0]
    real_f1, real_rel, fallos = rec._estado_de_cases, rec._releer_version, []

    def f1(*a, **k):
        r = real_f1(*a, **k)
        with rec._Bloqueo(str(store)):
            rec._anadir_linea(str(store), linea)                        # cola, mismo estado que F1
        return r

    def con_un_fallo(store_, fam, var, numero, case_id=None):
        if not fallos:
            fallos.append(1)
            return None, ("cases/ramp.steep/v001 ilegible: validation.json no legible tras 40 reintentos "
                          "(bloqueada o sin permisos)"), False, None
        return real_rel(store_, fam, var, numero, case_id)

    monkeypatch.setattr(rec, "_estado_de_cases", f1)
    monkeypatch.setattr(rec, "_releer_version", con_un_fallo)
    assert rec.comprobar_indice_detalle(str(store)) == ([], []) and fallos == [1]


def test_f2fix4_gap91_m14_el_dueno_no_lee_un_metadata_con_enlace_duro(tmp_path):
    """#91 M14: la comprobacion del dueño del directorio no lee un `metadata.json` con enlace duro (a
    un JSON de fuera que dice otro `case_id`): lo salta y usa la siguiente version completa."""
    raiz, cfg, store = _proyecto(tmp_path)
    r1 = rec.grabar(_caso(), cfg, raiz)
    rec.grabar(_caso(), cfg, raiz)
    meta = os.path.join(r1["path"], "metadata.json")
    datos = _json(meta)
    fuera = _fuera_json(tmp_path, "fuera-meta.json", dict(datos, case_id="xyz-ramp.steep"))
    os.remove(meta)
    _hardlink(fuera, meta)
    assert rec.grabar(_caso(), cfg, raiz)["version"] == 3


def test_f2fix4_gap91_m18_confirmacion_relee_un_fallo_pasajero_de_f1(tmp_path, monkeypatch):
    """#91 M18: si F1 no pudo leer una version por un fallo pasajero (`PermissionError` persistente
    solo durante el recorrido), la confirmacion la relee del disco: ni aviso ni diferencia."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    rec.grabar(_caso(), cfg, raiz)
    en_f1 = []
    real_f1, real_leer = rec._estado_de_cases, rec._leer_json_reintentando

    def f1(*a, **k):
        en_f1.append(1)
        try:
            return real_f1(*a, **k)
        finally:
            en_f1.clear()

    def leer(ruta, *a, **k):
        if en_f1 and os.path.basename(os.path.dirname(ruta)) == "v001" and os.path.basename(ruta) == "validation.json":
            raise PermissionError(13, "en uso")
        return real_leer(ruta, *a, **k)

    monkeypatch.setattr(rec, "_estado_de_cases", f1)
    monkeypatch.setattr(rec, "_leer_json_reintentando", leer)
    assert rec.comprobar_indice_detalle(str(store)) == ([], [])


def test_f2fix4_gap91_m24_la_ventana_avanza_con_el_offset(tmp_path, monkeypatch):
    """#91 M24: la ventana de identidad avanza con el offset consumido: con `st_ino == 0` y trafico
    que obliga a varias pasadas, el rebuild termina en el PRIMER intento (una sola F0), sin
    reintentos ni exit 3."""
    raiz, cfg, store = _proyecto(tmp_path)
    for _ in range(2):
        rec.grabar(_caso(), cfg, raiz)
    linea = _indice(store)[0]
    real_stat, real_cola, real_ident = rec._stat_indice, rec._leer_cola, rec._identidad

    class SinIno:
        def __init__(self, st):
            self.st_dev, self.st_ino, self.st_size = st.st_dev, 0, st.st_size

    pasadas, f0s = [], []

    def con_trafico(r, cursor, hasta_eof=False):
        if not hasta_eof and len(pasadas) < 3:
            pasadas.append(1)
            for _ in range(rec.COLA_MAX_BLOQUEO + 5):
                rec._anadir_linea(str(store), linea)
        return real_cola(r, cursor, hasta_eof)

    monkeypatch.setattr(rec, "_stat_indice", lambda x: SinIno(real_stat(x)))
    monkeypatch.setattr(rec, "_leer_cola", con_trafico)
    monkeypatch.setattr(rec, "_identidad", lambda r: f0s.append(1) or real_ident(r))
    n, avisos = rec.reconstruir_indice(str(store))
    assert len(pasadas) == 3 and len(f0s) == 1 and n == 2, (len(pasadas), len(f0s), n, avisos)


def test_f2fix4_gap92_temporal_que_es_un_enlace_se_reporta_como_enlace(tmp_path):
    """#92: un `.tmp-*` que es un enlace (junction/symlink) se reporta como «enlace en el store»
    (incoherencia, exit 1) aunque sea reciente; nunca se sigue ni se borra (ni el enlace ni el destino)."""
    raiz, cfg, store = _proyecto(tmp_path)
    rec.grabar(_caso(), cfg, raiz)
    aprobado = tmp_path / "proj" / "docs" / "knowledge" / "approved"
    aprobado.mkdir(parents=True)
    (aprobado / "ADR-001.md").write_bytes(b"curado\n")
    enlaces = (store / ".tmp-r", store / "cases" / ".tmp-c", store / "cases" / "ramp.steep" / ".tmp-k")
    for e in enlaces:
        _enlazar_dir(aprobado, e)
    difs, en_curso = rec.comprobar_indice_detalle(str(store))
    for rel in (".tmp-r", "cases/.tmp-c", "cases/ramp.steep/.tmp-k"):
        assert any(rel in d and "enlace" in d for d in difs), (rel, difs)
        assert not any(rel in c for c in en_curso), en_curso
    rec.reconstruir_indice(str(store))
    assert all(os.path.lexists(str(e)) for e in enlaces)
    assert (aprobado / "ADR-001.md").read_bytes() == b"curado\n"


def test_f2fix4_gap81_skill_describe_lo_que_queda_bajo_el_bloqueo():
    """#81/#90 (TDD n/a: prosa): SKILL.md describe EXACTAMENTE lo que queda bajo el bloqueo (la
    reserva, el `mkdir` del directorio de un caso nuevo y, solo si otro lo creo a la vez, el
    recorrido de `cases/`) y el limite declarado de POSIX (parejas que solo difieren en mayusculas)."""
    with open(SKILL_MD, encoding="utf-8") as f:
        texto = f.read()
    assert "independientes del tamaño del store" not in texto
    assert "`mkdir` del directorio del caso" in texto
    assert "otro lo creó a la vez" in texto
    assert "solo difieren en mayúsculas" in texto


# ------------------------------------------------------------------ fix4-bis (Linux, python:3.11-slim)

import types


def _fstat_trucado(monkeypatch, fichero, **cambios):
    """`os.fstat` del recorder que, para el descriptor abierto de `fichero` (la PRIMERA vez), devuelve
    el `stat` real con `cambios` (p. ej. `st_nlink=0`: inodo desenlazado por un `os.replace` en POSIX)."""
    real_fstat, real_open, abiertos, hechos = os.fstat, builtins.open, {}, []

    def open_(ruta, *a, **k):
        f = real_open(ruta, *a, **k)
        if os.path.basename(str(ruta)) == fichero:
            abiertos[f.fileno()] = True
        return f

    def fstat(fd):
        st = real_fstat(fd)
        if abiertos.pop(fd, False) and not hechos:
            hechos.append(1)
            campos = {k: getattr(st, k) for k in dir(st) if k.startswith("st_")}
            campos.update(cambios)
            return types.SimpleNamespace(**campos)
        return st

    monkeypatch.setattr(rec, "open", open_, raising=False)
    monkeypatch.setattr(rec.os, "fstat", fstat)
    return hechos


def test_f2fix4bis_gap83_st_nlink_cero_es_reemplazado_no_enlace_duro(tmp_path, monkeypatch):
    """fix4-bis (#83, Linux): tras un `os.replace` legitimo, el descriptor abierto apunta a un inodo
    DESENLAZADO (`st_nlink == 0`): es «reemplazado durante la lectura» -> se vuelve a comprobar desde el
    `lstat` y se lee el fichero nuevo; nunca «enlace duro» (solo `st_nlink > 1` lo es)."""
    raiz, cfg, store = _proyecto(tmp_path)
    r = rec.grabar(_caso(), cfg, raiz)
    motivo, sustituido = rec._motivo_descriptor(types.SimpleNamespace(st_mode=stat.S_IFREG, st_nlink=0), None)
    assert sustituido and "enlace duro" not in motivo, motivo
    hechos = _fstat_trucado(monkeypatch, "validation.json", st_nlink=0)
    obj, _mt, aviso = rec._leer_de_version(r["path"], "validation.json", "cases/ramp.steep/v001")
    assert hechos and aviso is None and obj["status"] == "pending", (obj, aviso)


def test_f2fix4bis_gap83_set_status_rechaza_misma_ruta_con_inodo_reutilizado(tmp_path, monkeypatch):
    """fix4-bis (#83, Linux): en POSIX el fichero que sustituye a `validation.json` puede reutilizar el
    MISMO numero de inodo (`samestat` verdadero); la identidad incluye tamaño, `mtime` y `ctime`: con el
    bloqueo tomado, cualquier discrepancia con el `lstat` previo -> rechazo, sin copiar nada."""
    raiz, cfg, store = _proyecto(tmp_path)
    r = rec.grabar(_caso(), cfg, raiz)
    st = os.lstat(os.path.join(r["path"], "validation.json"))
    hechos = _fstat_trucado(monkeypatch, "validation.json", st_ctime_ns=st.st_ctime_ns + 1,
                            st_mtime_ns=st.st_mtime_ns + 1)
    with pytest.raises(rec.Rechazo) as e:
        rec.cambiar_estado("geo-ramp.steep", 1, "rejected", cfg, raiz)
    assert hechos and "sustituido" in str(e.value), str(e.value)
    assert [x["status"] for x in _indice(store)] == ["pending"]


LINEAS_RARAS = (b"[1]", b"1", b"null", b'"x"', b"true", b'{"a": 1}', b"[]", b"{}",
                b'{"case_id": 1, "version": "1", "family": [], "variant": {}, "status": null, "outcome": 2, "updated_at": 3}')


def test_f2fix4bis_mb19_ningun_tipo_de_linea_hace_lanzar_a_check_ni_a_rebuild(tmp_path):
    """fix4-bis (Lente B, MB19): ningun tipo de linea JSON valida pero que no es una entrada (lista,
    numero, null, texto, booleano, objeto ajeno, claves con tipos erroneos) hace lanzar a `check` ni
    a `rebuild`, ni como fragmento final sin `\n` ni como linea del cuerpo: se ignora con aviso.
    `_parsear_linea` devuelve siempre `(None, motivo)` para ellas."""
    for cruda in LINEAS_RARAS:
        e, motivo = rec._parsear_linea(cruda)
        assert e is None and motivo, (cruda, e, motivo)
    for i, cruda in enumerate(LINEAS_RARAS):
        for como in ("fragmento", "cuerpo"):
            sub = tmp_path / f"{como}{i}"
            sub.mkdir()
            raiz, cfg, store = _proyecto(sub)
            rec.grabar(_caso(), cfg, raiz)
            with open(os.path.join(str(store), rec.INDICE), "ab") as f:
                f.write(cruda + (b"\n" if como == "cuerpo" else b""))
            difs = rec.comprobar_indice(str(store))
            assert difs, (cruda, como)
            n, _avisos = rec.reconstruir_indice(str(store))
            assert n == 1 and rec.comprobar_indice(str(store)) == [], (cruda, como)


def test_f2fix4bis_wb2_la_firma_de_f1_sale_del_descriptor_leido(tmp_path, monkeypatch):
    """fix4-bis (Lente B, W-B2): la firma de #89 es la del DESCRIPTOR del que se leyo `validation.json`
    en F1, no la de un `lstat` por ruta posterior: un `set-status` muerto justo despues de la lectura
    de F1 (antes de ese `lstat`) cambia la firma y la confirmacion relee esa version."""
    raiz, cfg, store = _proyecto(tmp_path)
    for _ in range(6):
        rec.grabar(_caso(), cfg, raiz)
    os.remove(os.path.join(str(store), rec.INDICE))
    _envejecer(store)
    val = store / "cases" / "ramp.steep" / "v005" / "validation.json"
    real_leer, hecho = rec._leer_json_reintentando, []

    def leer(ruta, *a, **k):
        r = real_leer(ruta, *a, **k)
        if os.path.normcase(ruta) == os.path.normcase(str(val)) and not hecho:
            hecho.append(1)                                     # W muerto justo tras la lectura de F1
            tmp = str(val) + ".nuevo"
            with builtins.open(tmp, "w", encoding="utf-8") as f:
                json.dump({"status": "rejected", "approved_by_human": False, "approved_at": None,
                           "reviewer_note": None}, f)
            os.replace(tmp, str(val))
        return r

    real_rel, releidas = rec._releer_version, []
    monkeypatch.setattr(rec, "_leer_json_reintentando", leer)
    monkeypatch.setattr(rec, "_releer_version", lambda s, f, v, numero, *a, **k: releidas.append(numero) or
                        real_rel(s, f, v, numero, *a, **k))
    rec.comprobar_indice(str(store))
    assert hecho and releidas == [5], releidas
