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
