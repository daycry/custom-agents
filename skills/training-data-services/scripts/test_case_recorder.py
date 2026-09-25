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
    rec.grabar(_caso(request="password=Sup3rS3creto!"), cfg, raiz)
    assert vistos and all("Sup3rS3creto" not in v for v in vistos)


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
        if isinstance(nodo, ast.FunctionDef) and nodo.name != "_limpiar_temporal":
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
