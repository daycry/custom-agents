"""Tests de `capabilities.py` (knowledge-services T-13, ADR-018 punto 7 / CA-14).

Contrato de una capacidad: {id, config_path, enabled, health, doctor, setup_step}. `enabled`,
`health` y `doctor` pueden ser valores estáticos o callables `f(root)`; el registro los evalúa
sin que `/doctor`/`/setup` necesiten saber cuál. Una capacidad cuyo `health`/`enabled` lanza
degrada a `error` sin tumbar la evaluación de las demás.
"""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _load():
    spec = importlib.util.spec_from_file_location("capabilities", os.path.join(HERE, "capabilities.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["capabilities"] = mod
    spec.loader.exec_module(mod)
    return mod


cap_mod = _load()


def _taxonomy(root, backends=None):
    cfg = {
        "version": 1,
        "id_prefix": "ca",
        "categories": [{"key": "DECISION", "folder": "adr", "min_evidence": "human_confirmed_rule"}],
        "evidence_levels": ["observation", "single_case", "validated_case",
                             "multiple_validated_cases", "human_confirmed_rule"],
    }
    if backends is not None:
        cfg["backends"] = backends
    d = os.path.join(root, ".claude", "knowledge-services")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "taxonomy.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f)
    return cfg


# ------------------------------------------------------------------ contrato basico

def test_registro_base_declara_knowledge_gate_y_kwipu():
    ids = {c["id"] for c in cap_mod.REGISTRO}
    assert {"knowledge-gate", "kwipu"} <= ids


def test_capacidad_tiene_las_seis_claves_del_contrato():
    for cap in cap_mod.REGISTRO:
        assert set(cap.keys()) >= {"id", "config_path", "enabled", "health", "doctor", "setup_step"}


def test_sin_dependencias_externas():
    with open(os.path.join(HERE, "capabilities.py"), "r", encoding="utf-8") as f:
        texto = f.read()
    for prohibido in ("import requests", "import yaml", "import jsonschema"):
        assert prohibido not in texto


# ------------------------------------------------------------------ evaluacion sobre un proyecto

def test_knowledge_gate_habilitado_sin_taxonomy_de_proyecto(tmp_path):
    root = str(tmp_path)
    resultado = cap_mod.enumerar(root)
    kg = next(c for c in resultado if c["id"] == "knowledge-gate")
    assert kg["enabled"] is True
    assert kg["health"]["estado"] == "ok"


def test_kwipu_deshabilitado_por_defecto(tmp_path):
    root = str(tmp_path)
    _taxonomy(root)  # sin `backends` -> plantilla no se aplica aqui (fichero explicito de proyecto)
    resultado = cap_mod.enumerar(root)
    kwipu = next(c for c in resultado if c["id"] == "kwipu")
    assert kwipu["enabled"] is False


def test_kwipu_habilitado_si_taxonomy_lo_declara(tmp_path):
    root = str(tmp_path)
    _taxonomy(root, backends={"kwipu": {"type": "markdown-export", "enabled": True,
                                          "config": {"export_dir": ".claude/knowledge-services/kwipu-export"}}})
    resultado = cap_mod.enumerar(root)
    kwipu = next(c for c in resultado if c["id"] == "kwipu")
    assert kwipu["enabled"] is True


def test_knowledge_gate_reporta_error_con_taxonomy_invalida(tmp_path):
    root = str(tmp_path)
    d = os.path.join(root, ".claude", "knowledge-services")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "taxonomy.json"), "w", encoding="utf-8") as f:
        json.dump({"categories": []}, f)  # falta version, categories vacia
    resultado = cap_mod.enumerar(root)
    kg = next(c for c in resultado if c["id"] == "knowledge-gate")
    assert kg["health"]["estado"] == "error"
    assert kg["doctor"]  # trae algo legible para /doctor


# ------------------------------------------------------------------ registrar() extensible y degradacion

def test_registrar_anade_una_capacidad_sin_tocar_las_demas(tmp_path):
    registro = list(cap_mod.REGISTRO)
    cap_mod.registrar({
        "id": "fixture-ok",
        "config_path": ".claude/fixture.json",
        "enabled": True,
        "health": lambda root: {"estado": "ok"},
        "doctor": lambda root: "fixture-ok: sano",
        "setup_step": "nada que configurar",
    }, registro=registro)
    assert any(c["id"] == "fixture-ok" for c in registro)
    resultado = cap_mod.enumerar(str(tmp_path), registro=registro)
    assert any(c["id"] == "fixture-ok" and c["health"]["estado"] == "ok" for c in resultado)


def test_capacidad_rota_degrada_a_error_sin_tumbar_el_resto(tmp_path):
    registro = list(cap_mod.REGISTRO)

    def _rompe(root):
        raise RuntimeError("boom")

    cap_mod.registrar({
        "id": "fixture-rota",
        "config_path": ".claude/fixture-rota.json",
        "enabled": True,
        "health": _rompe,
        "doctor": _rompe,
        "setup_step": "n/a",
    }, registro=registro)
    resultado = cap_mod.enumerar(str(tmp_path), registro=registro)
    por_id = {c["id"]: c for c in resultado}
    assert por_id["fixture-rota"]["health"]["estado"] == "error"
    assert "boom" in por_id["fixture-rota"]["health"]["detalle"]
    # las demas capacidades del registro base siguen evaluandose con normalidad
    assert por_id["knowledge-gate"]["health"]["estado"] == "ok"


def test_registrar_no_duplica_id(tmp_path):
    registro = list(cap_mod.REGISTRO)
    n_antes = len(registro)
    cap_mod.registrar({
        "id": "knowledge-gate",
        "config_path": ".claude/knowledge-services/taxonomy.json",
        "enabled": True,
        "health": lambda root: {"estado": "ok"},
        "doctor": lambda root: "duplicado",
        "setup_step": "n/a",
    }, registro=registro)
    assert len(registro) == n_antes  # sobrescribe, no duplica


# ------------------------------------------------------------------ CLI

def test_cli_lista_capacidades(capsys, tmp_path):
    assert cap_mod.main(["--root", str(tmp_path)]) == 0
    salida = capsys.readouterr().out
    assert "knowledge-gate" in salida
    assert "kwipu" in salida


# ------------------------------------------------------------------ revisión intento 1 (fix2)

def test_registrar_sin_id_levanta_valueerror():
    """Gap 16: `registrar()` con una capacidad sin `id` (o `id` vacío) falla con un mensaje claro
    en el momento de registrar, no con un `KeyError` a mitad del bucle de comparación."""
    import pytest
    registro = []
    with pytest.raises(ValueError):
        cap_mod.registrar({"config_path": "x"}, registro=registro)
    with pytest.raises(ValueError):
        cap_mod.registrar({"id": ""}, registro=registro)
    assert registro == []


def test_enumerar_memoiza_la_taxonomia_por_llamada(tmp_path, monkeypatch):
    """Gap 22: dentro de una sola `enumerar()`, `taxonomy.json` se lee/valida UNA vez (hoy
    `knowledge-gate` y `kwipu` la leen cada uno por su lado, y `kwipu` la relee en
    enabled/health/doctor: hasta 5 lecturas por `enumerar()`)."""
    root = str(tmp_path)
    _taxonomy(root, backends={"kwipu": {"type": "markdown-export", "enabled": True,
                                          "config": {"export_dir": ".claude/knowledge-services/kwipu-export"}}})

    llamadas = {"n": 0}
    original = cap_mod._cargar_knowledge_schema

    def _contando():
        llamadas["n"] += 1
        return original()

    monkeypatch.setattr(cap_mod, "_cargar_knowledge_schema", _contando)
    cap_mod.enumerar(root)
    assert llamadas["n"] == 1


def test_enumerar_no_sirve_taxonomia_obsoleta_entre_llamadas(tmp_path):
    """La cache de `enumerar()` (gap 22) no debe sobrevivir a la llamada: una taxonomia editada
    entre dos `enumerar()` se refleja en la segunda."""
    root = str(tmp_path)
    _taxonomy(root, backends={"kwipu": {"type": "markdown-export", "enabled": False,
                                          "config": {"export_dir": ".claude/knowledge-services/kwipu-export"}}})
    primero = cap_mod.enumerar(root)
    kwipu1 = next(c for c in primero if c["id"] == "kwipu")
    assert kwipu1["enabled"] is False

    _taxonomy(root, backends={"kwipu": {"type": "markdown-export", "enabled": True,
                                          "config": {"export_dir": ".claude/knowledge-services/kwipu-export"}}})
    segundo = cap_mod.enumerar(root)
    kwipu2 = next(c for c in segundo if c["id"] == "kwipu")
    assert kwipu2["enabled"] is True


def test_evaluar_capacidad_no_sirve_taxonomia_obsoleta_entre_llamadas_directas(tmp_path):
    """Gap 32: `evaluar_capacidad()` es API PUBLICA, usable fuera de `enumerar()`; antes solo
    `enumerar()` vaciaba `_CACHE_TAXONOMIA`, asi que dos llamadas DIRECTAS a
    `evaluar_capacidad()` entre las que se edita `taxonomy.json` servian la taxonomia obsoleta a
    la segunda."""
    root = str(tmp_path)
    kwipu_cap = next(c for c in cap_mod.REGISTRO if c["id"] == "kwipu")

    _taxonomy(root, backends={"kwipu": {"type": "markdown-export", "enabled": False,
                                          "config": {"export_dir": ".claude/knowledge-services/kwipu-export"}}})
    primero = cap_mod.evaluar_capacidad(kwipu_cap, root)
    assert primero["enabled"] is False

    _taxonomy(root, backends={"kwipu": {"type": "markdown-export", "enabled": True,
                                          "config": {"export_dir": ".claude/knowledge-services/kwipu-export"}}})
    segundo = cap_mod.evaluar_capacidad(kwipu_cap, root)
    assert segundo["enabled"] is True


# ------------------------------------------------------------------ capacidad `training` (training-data-services T-02)

def _training(proyecto, **cfg):
    d = os.path.join(proyecto, ".claude", "knowledge-services")
    os.makedirs(d, exist_ok=True)
    datos = {"version": 1}
    datos.update(cfg)
    with open(os.path.join(d, "training.json"), "w", encoding="utf-8") as f:
        json.dump(datos, f)
    return os.path.join(d, "training.json")


def _cap_training(root):
    return next(c for c in cap_mod.enumerar(root) if c["id"] == "training")


def test_training_registrada_con_el_contrato_de_seis_claves():
    cap = next(c for c in cap_mod.REGISTRO if c["id"] == "training")
    assert set(cap.keys()) >= {"id", "config_path", "enabled", "health", "doctor", "setup_step"}
    assert cap["config_path"].replace("\\", "/") == ".claude/knowledge-services/training.json"
    assert "training.json" in cap["setup_step"]


def test_training_sin_fichero_deshabilitada_y_sin_efectos(tmp_path):
    """CA-01: sin `training.json` la capacidad no existe para el ciclo y no crea nada en disco."""
    root = str(tmp_path)
    t = _cap_training(root)
    assert t["enabled"] is False
    assert t["health"]["estado"] == "deshabilitado"
    assert "deshabilitad" in t["doctor"]
    assert list(tmp_path.iterdir()) == []


def test_training_enabled_false_deshabilitada(tmp_path):
    root = str(tmp_path)
    _training(root, enabled=False)
    t = _cap_training(root)
    assert t["enabled"] is False and t["health"]["estado"] == "deshabilitado"


def test_training_activa_con_root_existente(tmp_path):
    root = str(tmp_path)
    (tmp_path / "store").mkdir()
    _training(root, enabled=True, root="store", id_prefix="geo")
    t = _cap_training(root)
    assert t["enabled"] is True
    assert t["health"]["estado"] == "ok"
    assert os.path.normcase(t["health"]["root"]) == os.path.normcase(str(tmp_path / "store"))
    assert t["doctor"].startswith("training:")


def test_training_activa_con_root_aun_inexistente_es_declarada(tmp_path):
    root = str(tmp_path)
    _training(root, enabled=True, root="store", id_prefix="geo")
    t = _cap_training(root)
    assert t["enabled"] is True
    assert t["health"]["estado"] == "declarado"
    assert not (tmp_path / "store").exists()  # informar nunca crea el case store


def test_training_config_invalida_es_error_con_fichero_y_campo(tmp_path):
    root = str(tmp_path)
    ruta = _training(root, enabled=True)  # sin root ni id_prefix
    t = _cap_training(root)
    assert t["enabled"] is False
    assert t["health"]["estado"] == "error"
    assert t["health"]["fichero"] == ruta
    assert "root" in t["health"]["detalle"]


def test_training_json_ilegible_es_error_sin_tumbar_el_resto(tmp_path):
    root = str(tmp_path)
    d = tmp_path / ".claude" / "knowledge-services"
    d.mkdir(parents=True)
    (d / "training.json").write_text("{roto", encoding="utf-8")
    resultado = {c["id"]: c for c in cap_mod.enumerar(root)}
    assert resultado["training"]["health"]["estado"] == "error"
    assert resultado["knowledge-gate"]["health"]["estado"] == "ok"


def test_training_sin_red():
    """La capacidad solo lee un JSON local: ni sockets ni HTTP en `capabilities.py`."""
    with open(os.path.join(HERE, "capabilities.py"), "r", encoding="utf-8") as f:
        texto = f.read()
    for prohibido in ("import socket", "urllib.request", "http.client"):
        assert prohibido not in texto


def test_training_valida_con_el_esquema_de_la_skill(tmp_path, monkeypatch):
    """Una sola fuente del esquema: `capabilities.py` valida con `case_schema.py` de la skill; si
    la skill no viaja (paquete parcial), degrada a `declarado` sin inventar validacion propia."""
    root = str(tmp_path)
    _training(root, enabled=True, root="store", id_prefix="geo", bridge_to_curator="si")
    assert _cap_training(root)["health"]["estado"] == "error"
    monkeypatch.setattr(cap_mod, "_cargar_case_schema", lambda: None)
    t = _cap_training(root)
    assert t["enabled"] is True
    assert t["health"]["estado"] == "declarado"
    assert "case_schema.py" in t["health"]["detalle"]


def test_cli_lista_training(capsys, tmp_path):
    assert cap_mod.main(["--root", str(tmp_path)]) == 0
    assert "training" in capsys.readouterr().out


def test_f1fix1_gap02_training_root_en_docs_knowledge_absoluto_o_capitalizado_es_error(tmp_path):
    """gap #2: `capabilities` valida con la raiz del PROYECTO (via `cargar_config(root)`), asi que
    un `root` absoluto o con otra capitalizacion dentro de `<proyecto>/docs/knowledge/` es error."""
    root = str(tmp_path)
    for mal in (str(tmp_path / "docs" / "knowledge" / "cases"), "Docs/Knowledge/cases"):
        _training(root, enabled=True, root=mal, id_prefix="geo")
        t = _cap_training(root)
        assert t["enabled"] is False, mal
        assert t["health"]["estado"] == "error" and "root" in t["health"]["detalle"], mal


def test_f1fix1_gap07_training_root_con_tilde_es_error(tmp_path):
    """gap #7: `~` ni se expande ni se toma literal (`<proyecto>/~/store`): error de config."""
    root = str(tmp_path)
    _training(root, enabled=True, root="~/store", id_prefix="geo")
    t = _cap_training(root)
    assert t["health"]["estado"] == "error" and "root" in t["health"]["detalle"]
    assert not (tmp_path / "~").exists()


# ------------------------------------------------------------------ T-10: `/doctor` informa el estado del case store

import copy  # noqa: E402

_CASO = {
    "family": "ramp", "variant": "steep", "request": "Genera una rampa", "context": {"text": "vacia"},
    "constraints": {}, "metrics": {"score": 1}, "outcome": "success", "artifacts": [],
    "trajectory": [{"role": "user", "content": "Genera una rampa"}, {"role": "assistant", "content": "Hecho."}],
}


def _tds():
    tds = cap_mod._cargar_tds()
    assert tds is not None, "la skill training-data-services viaja con el repo"
    return tds


def _proyecto_training(tmp_path, estados=("pending", "approved", "approved", "needs_changes", "rejected")):
    """Proyecto con `training.json` activo (`root: ../store`) y un caso por estado (familias distintas)."""
    proj = tmp_path / "proj"
    proj.mkdir()
    cfg = {"version": 1, "enabled": True, "root": "../store", "id_prefix": "geo"}
    _training(str(proj), **{k: v for k, v in cfg.items() if k != "version"})
    rec = _tds()["rec"]
    for i, estado in enumerate(estados):
        caso = copy.deepcopy(_CASO)
        caso["family"] = f"f{i}"
        r = rec.grabar(caso, cfg, str(proj))
        if estado != "pending":
            rec.cambiar_estado(r["case_id"], r["version"], estado, cfg, str(proj),
                               approved_by_human=estado == "approved")
    return str(proj), cfg, tmp_path / "store"


def _arbol(d):
    out = {}
    for base, dirs, fs in os.walk(str(d)):
        for n in dirs + fs:
            p = os.path.join(base, n)
            st = os.lstat(p)
            out[os.path.relpath(p, str(d))] = (st.st_size, st.st_mtime_ns)
    return out


def test_t10_training_doctor_informa_root_recuento_por_estado_y_dataset(tmp_path):
    proj, _cfg, store = _proyecto_training(tmp_path)
    t = _cap_training(proj)
    assert t["enabled"] is True and t["health"]["estado"] == "ok"
    txt = t["doctor"]
    assert str(store) in txt or os.path.normcase(str(store)) in os.path.normcase(txt)
    assert "pending 1 · approved 2 · needs_changes 1 · rejected 1 (5 versiones)" in txt
    assert "incompletas 0" in txt and "temporales huerfanos 0" in txt
    assert "dataset: desactualizado" in txt and "ningun export" in txt
    assert "PARCIAL" not in txt


def test_t10_training_doctor_dataset_al_dia_tras_exportar(tmp_path):
    proj, cfg, store = _proyecto_training(tmp_path, estados=("approved",))
    r = _tds()["asm"].ensamblar(cfg, proj, {"f0"}, fecha="20260928")          # D-f4: escribe la marca
    txt = _cap_training(proj)["doctor"]
    assert "dataset: al dia" in txt and os.path.basename(r["ruta"]) in txt and "20260928-" in txt


def test_t10_training_doctor_sin_gold_no_hay_dataset_que_exportar(tmp_path):
    proj, _cfg, _store = _proyecto_training(tmp_path, estados=("pending", "rejected"))
    txt = _cap_training(proj)["doctor"]
    assert "dataset: sin Gold" in txt


def test_t10_training_doctor_recuento_parcial_declara_el_tope(tmp_path, monkeypatch):
    proj, _cfg, _store = _proyecto_training(tmp_path)
    monkeypatch.setattr(cap_mod, "TRAINING_PLAZO_S", 0.0)
    txt = _cap_training(proj)["doctor"]
    assert "recuento PARCIAL: 0 de 5 casos" in txt and "tope" in txt
    assert "dataset: no verificado (PARCIAL)" in txt


def test_t10_training_doctor_sin_la_skill_degrada_sin_recuento(tmp_path, monkeypatch):
    proj, _cfg, _store = _proyecto_training(tmp_path)
    monkeypatch.setattr(cap_mod, "_cargar_tds", lambda: None)
    t = _cap_training(proj)
    assert t["health"]["estado"] == "ok" and "recuento no disponible" in t["doctor"]


def test_t10_training_doctor_un_fallo_del_recuento_no_tumba_nada(tmp_path, monkeypatch):
    proj, _cfg, _store = _proyecto_training(tmp_path)
    tds = _tds()

    def _roto(*_a, **_k):
        raise OSError("disco raro")
    monkeypatch.setattr(tds["rec"], "resumen_store", _roto)
    monkeypatch.setattr(cap_mod, "_cargar_tds", lambda: tds)
    resultado = {c["id"]: c for c in cap_mod.enumerar(proj)}
    assert "recuento no disponible (OSError)" in resultado["training"]["doctor"]
    assert resultado["knowledge-gate"]["health"]["estado"] == "ok"


def test_t10_training_doctor_no_escribe_nada(tmp_path):
    proj, _cfg, _store = _proyecto_training(tmp_path)
    antes = _arbol(tmp_path)
    _cap_training(proj)
    assert _arbol(tmp_path) == antes


def test_t10_training_cli_exit_0_con_config_invalida(tmp_path, capsys):
    _training(str(tmp_path), enabled=True)                               # sin root ni id_prefix
    assert cap_mod.main(["--root", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "training: enabled=False health=error" in out and "root" in out


def test_t10_training_doctor_pasa_su_tope_de_tiempo_al_recuento(tmp_path, monkeypatch):
    """El recuento va acotado: `capabilities` le pasa `TRAINING_PLAZO_S` (<= 2 s) al recorder."""
    proj, _cfg, _store = _proyecto_training(tmp_path, estados=("approved",))
    tds = _tds()
    vistos = []
    original = tds["rec"].resumen_store

    def _espia(store, raiz=None, plazo_s=None, id_prefix=None):          # fix3 (#181/N2): id_prefix explicito
        vistos.append(plazo_s)
        return original(store, raiz, plazo_s=plazo_s, id_prefix=id_prefix)
    monkeypatch.setattr(tds["rec"], "resumen_store", _espia)
    monkeypatch.setattr(cap_mod, "_cargar_tds", lambda: tds)
    _cap_training(proj)
    assert vistos == [cap_mod.TRAINING_PLAZO_S] and 0 < cap_mod.TRAINING_PLAZO_S <= 2.0


def test_t10_cargar_tds_no_escribe_bytecode_y_restaura_el_flag(monkeypatch):
    """`/doctor` solo lee: cargar los scripts de la skill no deja `__pycache__` en el plugin."""
    vistos = []
    original = cap_mod.importlib.util.spec_from_file_location

    def _spec(nombre, ruta):
        spec = original(nombre, ruta)
        exec_original = spec.loader.exec_module

        def _exec(mod):
            vistos.append(sys.dont_write_bytecode)
            return exec_original(mod)
        spec.loader.exec_module = _exec
        return spec
    monkeypatch.setattr(cap_mod.importlib.util, "spec_from_file_location", _spec)
    monkeypatch.setattr(cap_mod, "_TDS", {})
    monkeypatch.setattr(sys, "dont_write_bytecode", False)
    tds = cap_mod._cargar_tds()
    assert tds is not None and vistos and all(vistos) and sys.dont_write_bytecode is False


def test_t10_cargar_tds_skill_ausente_o_rota_es_none(tmp_path, monkeypatch):
    monkeypatch.setattr(cap_mod, "_TDS", {})
    monkeypatch.setattr(cap_mod, "HERE", str(tmp_path / "agent-kits" / "shared"))
    assert cap_mod._cargar_tds() is None
    d = tmp_path / "skills" / "training-data-services" / "scripts"
    d.mkdir(parents=True)
    (d / "dataset-assembler.py").write_text("raise RuntimeError('rota')\n", encoding="utf-8")
    monkeypatch.setattr(cap_mod, "_TDS", {})
    assert cap_mod._cargar_tds() is None


def test_t10_setup_ofrece_training_desde_la_plantilla_sin_activar_el_puente():
    """`/setup` 5-sexies ofrece `training` como las demas: desde `assets/training.example.json`, con
    `root` fuera de `docs/knowledge/` e `id_prefix`, y `bridge_to_curator` nunca activado sin preguntar."""
    repo = os.path.dirname(os.path.dirname(HERE))
    with open(os.path.join(repo, "commands", "setup.md"), encoding="utf-8") as f:
        paso = f.read().split("5-sexies.", 1)[1].split("\n6. ", 1)[0]
    for literal in ("training.example.json", "training.json", "`root`", "`id_prefix`", "docs/knowledge/",
                    "**`bridge_to_curator` queda en `false`**", "nunca lo actives sin preguntar",
                    "case_schema.py config", "-type d -path '*skills/training-data-services'",
                    "<skill>/assets/training.example.json"):
        assert literal in paso, literal
    ejemplo = os.path.join(repo, "skills", "training-data-services", "assets", "training.example.json")
    with open(ejemplo, encoding="utf-8") as f:
        cfg = json.load(f)
    assert cfg["bridge_to_curator"] is False and "docs/knowledge" not in cfg["root"] and cfg["id_prefix"]
    cap = next(c for c in cap_mod.REGISTRO if c["id"] == "training")
    assert "`root`" in cap["setup_step"] and "`id_prefix`" in cap["setup_step"]


# ------------------------------------------------------------------ T-10 fix1 (revision intento 1, Fase 4)

def test_t10fix1_153_root_del_store_sale_escapado_en_doctor(tmp_path):
    """#153 (CWE-150): la ruta del case store (y todo nombre del store) sale por `_texto_ruta` en la
    salida de la capacidad: un nombre no ASCII o no imprimible nunca llega tal cual a la terminal."""
    proj = tmp_path / "proj"
    proj.mkdir()
    _training(str(proj), enabled=True, root="../almacén", id_prefix="geo")
    t = _cap_training(str(proj))
    assert t["health"]["estado"] == "declarado" and "almacén" not in t["doctor"], t["doctor"]
    assert ascii("almacén")[1:-1] in t["doctor"]
    (tmp_path / "almacén").mkdir()
    t = _cap_training(str(proj))
    assert t["health"]["estado"] == "ok" and "almacén" not in t["doctor"], t["doctor"]
    assert ascii("almacén")[1:-1] in t["doctor"]


def test_t10fix1_159_doctor_con_training_activo_no_deja_pycache_en_el_plugin(tmp_path):
    """#159: TODA carga por ruta de la capacidad (tambien `case_schema.py`, que corre antes) va con
    `dont_write_bytecode`: `/doctor` sobre una COPIA del plugin con `training` activo no deja ni un
    `__pycache__` nuevo."""
    import shutil
    import subprocess
    repo = os.path.dirname(os.path.dirname(HERE))
    copia = tmp_path / "plugin"
    for rel in (os.path.join("agent-kits", "shared"), os.path.join("skills", "training-data-services", "scripts")):
        shutil.copytree(os.path.join(repo, rel), str(copia / rel),
                        ignore=shutil.ignore_patterns("__pycache__", "test_*"))
    proj, _cfg, _store = _proyecto_training(tmp_path, estados=("approved",))
    entorno = {k: v for k, v in os.environ.items() if k != "PYTHONDONTWRITEBYTECODE"}
    for script, args in (("capabilities.py", ["--root", proj]), ("doctor.py", ["--root", proj, "--json"])):
        r = subprocess.run([sys.executable, str(copia / "agent-kits" / "shared" / script), *args],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", env=entorno,
                           cwd=proj, timeout=120)
        assert r.returncode in (0, 1), (script, r.stderr[-2000:])
        assert "training" in r.stdout, (script, r.stdout[-2000:])
    caches = [os.path.relpath(b, str(copia)) for b, ds, _fs in os.walk(str(copia)) if b.endswith("__pycache__")]
    assert caches == [], caches


def test_t10fix1_164_enumerar_pasa_el_plazo_que_queda_a_las_capacidades(tmp_path, monkeypatch):
    """#164: `enumerar(plazo_s=…)` (el presupuesto que le queda a `/doctor`) acota el recuento: la
    capacidad recibe el MENOR entre su tope propio y lo que queda del bloque."""
    proj, _cfg, _store = _proyecto_training(tmp_path, estados=("approved",))
    tds = _tds()
    vistos = []
    original = tds["rec"].resumen_store

    def _espia(store, raiz=None, plazo_s=None, id_prefix=None):          # fix3 (#181/N2): id_prefix explicito
        vistos.append(plazo_s)
        return original(store, raiz, plazo_s=plazo_s, id_prefix=id_prefix)
    monkeypatch.setattr(tds["rec"], "resumen_store", _espia)
    monkeypatch.setattr(cap_mod, "_cargar_tds", lambda: tds)
    next(c for c in cap_mod.enumerar(proj, plazo_s=0.4) if c["id"] == "training")
    assert len(vistos) == 1 and 0 <= vistos[0] <= 0.4
    next(c for c in cap_mod.enumerar(proj, plazo_s=0) if c["id"] == "training")
    assert vistos[1] == 0
    next(c for c in cap_mod.enumerar(proj) if c["id"] == "training")
    assert vistos[2] == cap_mod.TRAINING_PLAZO_S


# ------------------------------------------------------------------ T-10 fix2 (revision intento 2, Fase 4)

def test_t10fix2_172_claves_y_regex_de_training_json_salen_escapadas_en_doctor(tmp_path, capsys):
    """#172 (CWE-150): una clave hostil de `training.json`, una de `ids` y el texto de un `re.error` no
    llegan en crudo (U+202E, CSI U+009B) a la salida de la capacidad —texto de `/doctor` y de la CLI—:
    se escapan en el ORIGEN (`case_schema.validar_config`)."""
    crudos = ("\u202e", "\x9b")
    for extra in ({"\u202egnp.exe\x9b2J x": 1}, {"ids": {"\u202eX\x9b31m": 1}},
                  {"ids": {"family_pattern": "(?<\u202e>a)"}}):
        root = tmp_path / str(len(os.listdir(str(tmp_path))))
        root.mkdir()
        _training(str(root), enabled=True, root="../store", id_prefix="geo", **extra)
        t = _cap_training(str(root))
        assert t["health"]["estado"] == "error", t
        for texto in (t["doctor"], t["health"]["detalle"], json.dumps(t["health"], ensure_ascii=False)):
            assert not any(c in texto for c in crudos), texto
        assert cap_mod.main(["--root", str(root)]) == 0
        salida = capsys.readouterr().out
        assert "training: enabled=False health=error" in salida and not any(c in salida for c in crudos), salida


def test_t10fix2_frescura_y_texto_vienen_del_ensamblador(tmp_path, monkeypatch):
    """F4: el texto del recuento y de la frescura es el del ensamblador (`texto_estado`, el mismo de
    `dataset-assembler.py --estado`); la capacidad le pasa el resumen y un plazo que, con el margen
    propio de `estado_dataset` (M10), no pasa de su tope."""
    proj, cfg, store = _proyecto_training(tmp_path, estados=("approved",))
    tds = _tds()
    tds["asm"].ensamblar(cfg, proj, {"f0"}, fecha="20260928")
    vistos = []
    original = tds["rec"].resumen_store

    def _espia(store_, raiz=None, plazo_s=None, id_prefix=None):         # fix3 (#181/N2): id_prefix explicito
        vistos.append(plazo_s)
        return original(store_, raiz, plazo_s=plazo_s, id_prefix=id_prefix)
    monkeypatch.setattr(tds["rec"], "resumen_store", _espia)
    monkeypatch.setattr(cap_mod, "_cargar_tds", lambda: tds)
    txt = next(c for c in cap_mod.enumerar(proj, plazo_s=1.0) if c["id"] == "training")["doctor"]
    assert 0 <= vistos[0] <= 1.0 - tds["asm"].MARGEN_ESTADO_S + 1e-6, vistos
    res = original(str(store), proj, plazo_s=None)
    assert tds["asm"].texto_estado(res, tds["asm"].estado_dataset(str(store), res)) in txt
    assert cap_mod._texto_recuento(res, tds["asm"].estado_dataset(str(store), res)) in txt


# ------------------------------------------------------------------ T-10 fix3 (#180, #181/N2)

def test_t10fix3_181_doctor_pasa_el_id_prefix_de_training_json_y_un_store_normal_esta_al_dia(tmp_path, monkeypatch):
    """#181/N2 (I4): `/doctor` (la capacidad) pasa a `resumen_store` el `id_prefix` de training.json;
    con un store normal con prefijo, la frescura sale `al_dia` (nunca `n_gold=0`)."""
    proj, cfg, store = _proyecto_training(tmp_path, estados=("approved", "approved"))
    tds = _tds()
    tds["asm"].ensamblar(cfg, proj, {"f1"}, fecha="20260928")
    vistos = []
    original = tds["rec"].resumen_store

    def _espia(store_, raiz=None, plazo_s=None, id_prefix=None):
        vistos.append(id_prefix)
        return original(store_, raiz, plazo_s=plazo_s, id_prefix=id_prefix)
    monkeypatch.setattr(tds["rec"], "resumen_store", _espia)
    monkeypatch.setattr(cap_mod, "_cargar_tds", lambda: tds)
    txt = _cap_training(proj)["doctor"]
    assert vistos == ["geo"] and "dataset: al dia" in txt, (vistos, txt)
    assert "approved 2" in txt, txt


def test_t10fix3_180_parametros_forjados_no_salen_crudos_en_doctor_json(tmp_path):
    """#180 (CWE-150): una marca con firma valida y `parametros.umbral` forjado (OSC + bidi; borrado de
    pantalla + salto de linea) no llega cruda a `/doctor --json` (que escribe con `ensure_ascii=False`):
    la fila de `training` no lleva ESC, U+202E, U+009B, U+2028 ni `\\n`."""
    import subprocess
    proj, cfg, store = _proyecto_training(tmp_path, estados=("approved",))
    tds = _tds()
    tds["asm"].ensamblar(cfg, proj, {"f0"}, fecha="20260928")
    ruta = store / "exports" / ".ultimo.json"
    buena = json.loads(ruta.read_text(encoding="utf-8"))
    for lit in ("\x1b]0;pwn\x07‮", "\x1b[2J‮FALSO\n linea"):
        marca = dict(buena, parametros=dict(buena["parametros"], umbral=lit))
        ruta.write_text(json.dumps(marca, ensure_ascii=False), encoding="utf-8")
        r = subprocess.run([sys.executable, os.path.join(HERE, "doctor.py"), "--root", proj, "--json"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=proj, timeout=120)
        assert r.returncode in (0, 1), r.stderr[-2000:]
        filas = [json.dumps(l, ensure_ascii=False) for b in json.loads(r.stdout)["bloques"] for l in b["lineas"]
                 if l.get("que") == "training"]
        assert filas, r.stdout[-2000:]
        for fila in filas:
            texto = json.loads(fila)["detalle"]
            assert not any(c in texto for c in ("\x1b", "‮", "\u009b", " ", "\n")), texto
            assert "no verificable" in texto, texto


# ------------------------------------------------------------------ T-10 fix4 (#190, #195)

def test_t10fix4_195_training_json_se_lee_una_vez_por_enumerar_antes_del_plazo(tmp_path, monkeypatch):
    """#195: la capacidad `training` lee y valida `training.json` UNA vez por `enumerar()` (espia sobre
    `_estado_training`) y reutiliza el resultado en `enabled`, `health`, `doctor` y el recuento: ninguna
    lectura despues de calcular el plazo (`plazo_restante`). Tambien con `evaluar_capacidad`, y la
    cache no sobrevive a la llamada (una config editada se ve en la siguiente)."""
    proj, _cfg, _store = _proyecto_training(tmp_path, estados=("approved",))
    llamadas = []
    original = cap_mod._estado_training

    def _espia(root):
        llamadas.append("leer")
        return original(root)
    real_plazo = cap_mod.plazo_restante

    def _plazo(defecto):
        llamadas.append("plazo")
        return real_plazo(defecto)
    monkeypatch.setattr(cap_mod, "_estado_training", _espia)
    monkeypatch.setattr(cap_mod, "plazo_restante", _plazo)
    t = next(c for c in cap_mod.enumerar(proj, plazo_s=5.0) if c["id"] == "training")
    assert t["enabled"] is True and "approved 1" in t["doctor"], t
    assert llamadas == ["leer", "plazo"], llamadas
    llamadas.clear()
    cap = next(c for c in cap_mod.REGISTRO if c["id"] == "training")
    assert cap_mod.evaluar_capacidad(cap, proj)["enabled"] is True
    assert llamadas == ["leer", "plazo"], llamadas
    _training(proj, enabled=False, root="../store", id_prefix="geo")
    llamadas.clear()
    assert _cap_training(proj)["enabled"] is False and llamadas == ["leer"], llamadas
    _training(proj, enabled=True, root="../store", id_prefix="geo")      # fuera de enumerar: sin cache
    assert cap_mod._training_enabled(proj) is True and cap_mod._CACHE_TRAINING == {}


def test_t10fix4_190_doctor_pone_primero_la_causa_otro_id_prefix(tmp_path):
    """#190: con un store existente y el `id_prefix` de training.json cambiado, la fila de `/doctor`
    dice PRIMERO «N versiones con otro `id_prefix`…: restauralo o usa otro `root`» (no el mensaje de
    #183 ni «sin Gold»)."""
    proj, cfg, _store = _proyecto_training(tmp_path, estados=("approved", "approved"))
    tds = _tds()
    tds["asm"].ensamblar(cfg, proj, {"f1"}, fecha="20260928")
    _training(proj, enabled=True, root="../store", id_prefix="nuevo")
    txt = _cap_training(proj)["doctor"]
    causa = "2 versiones con otro `id_prefix` que el de training.json: restauralo o usa otro `root`"
    assert f"dataset: {tds['asm'].TEXTO_DATASET['con_omisiones']} ({causa}" in txt, txt
    assert "0 Gold vigentes" not in txt, txt
