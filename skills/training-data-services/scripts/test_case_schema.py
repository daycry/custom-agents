"""Tests de `case_schema.py` (training-data-services T-01).

Cubre el esquema de `.claude/knowledge-services/training.json` (opt-in: sin fichero no hay
config, CA-01) y el del caso (campos obligatorios, vocabularios cerrados de `validation.status` y
`outcome`, `approved` solo con `approved_by_human`, trayectoria sin chain-of-thought, metricas
opacas, artefactos solo por referencia, `context.refs` opcional con procedencia) y el mapeo
DECLARADO del vocabulario externo `useful|dead_end|corrected` (graphify save-result).
"""
import copy
import importlib.util
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _load():
    spec = importlib.util.spec_from_file_location("case_schema", os.path.join(HERE, "case_schema.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["case_schema"] = mod
    spec.loader.exec_module(mod)
    return mod


cs = _load()


def _campos(errores):
    return {e["campo"] for e in errores}


# ------------------------------------------------------------------ training.json

CONFIG_OK = {
    "version": 1,
    "enabled": True,
    "root": "../case-store",
    "id_prefix": "geo",
    "ids": {"family_pattern": "^[a-z0-9][a-z0-9_-]*$", "variant_pattern": "^[a-z0-9][a-z0-9_-]*$",
            "version_width": 3},
    "bridge_to_curator": False,
}


def test_config_valida():
    assert cs.validar_config(CONFIG_OK) == []


def test_config_minima_desactivada_no_exige_root():
    assert cs.validar_config({"version": 1, "enabled": False}) == []


def test_config_activa_exige_root_e_id_prefix():
    cfg = {"version": 1, "enabled": True}
    assert {"root", "id_prefix"} <= _campos(cs.validar_config(cfg))


def test_config_bridge_debe_ser_booleano():
    cfg = dict(CONFIG_OK, bridge_to_curator="si")
    assert "bridge_to_curator" in _campos(cs.validar_config(cfg))


def test_config_enabled_debe_ser_booleano_y_version_soportada():
    cfg = dict(CONFIG_OK, enabled="true", version=9)
    assert {"enabled", "version"} <= _campos(cs.validar_config(cfg))


def test_config_id_prefix_con_formato_slug():
    cfg = dict(CONFIG_OK, id_prefix="Geo Prefix!")
    assert "id_prefix" in _campos(cs.validar_config(cfg))


def test_config_patron_de_ids_invalido():
    cfg = copy.deepcopy(CONFIG_OK)
    cfg["ids"]["family_pattern"] = "([unclosed"
    assert "ids.family_pattern" in _campos(cs.validar_config(cfg))


def test_config_clave_desconocida_se_rechaza():
    cfg = dict(CONFIG_OK, bridge_to_kwipu=True)
    assert "bridge_to_kwipu" in _campos(cs.validar_config(cfg))


def test_config_root_nunca_dentro_de_docs_knowledge():
    for mal in ("docs/knowledge/cases", "./docs/knowledge", r"docs\knowledge\x"):
        assert "root" in _campos(cs.validar_config(dict(CONFIG_OK, root=mal))), mal
    for bien in ("../docs/knowledge", "data/cases", "docs/knowledge-cases"):
        assert cs.validar_config(dict(CONFIG_OK, root=bien)) == [], bien


def test_config_no_objeto():
    assert cs.validar_config([1, 2]) != []


def test_cargar_config_sin_fichero_es_opt_in(tmp_path):
    config, ruta, errores = cs.cargar_config(str(tmp_path))
    assert config is None and ruta is None and errores == []


def test_cargar_config_json_ilegible(tmp_path):
    d = tmp_path / ".claude" / "knowledge-services"
    d.mkdir(parents=True)
    (d / "training.json").write_text("{no es json", encoding="utf-8")
    config, ruta, errores = cs.cargar_config(str(tmp_path))
    assert config is None and ruta.endswith("training.json") and errores


def test_cargar_config_valida(tmp_path):
    d = tmp_path / ".claude" / "knowledge-services"
    d.mkdir(parents=True)
    (d / "training.json").write_text(json.dumps(CONFIG_OK), encoding="utf-8")
    config, ruta, errores = cs.cargar_config(str(tmp_path))
    assert errores == [] and config["id_prefix"] == "geo"


# ------------------------------------------------------------------ ids

def test_case_id_se_construye_con_prefijo_familia_y_variante():
    assert cs.construir_case_id("geo", "ramp", "steep") == "geo-ramp.steep"
    assert cs.construir_case_id(None, "ramp", "steep") == "ramp.steep"
    assert cs.referencia_version("geo-ramp.steep", 7) == "geo-ramp.steep@v007"
    assert cs.directorio_version("ramp", "steep", 7) == os.path.join("cases", "ramp.steep", "v007")


# ------------------------------------------------------------------ caso

CASO_OK = {
    "case_id": "geo-ramp.steep",
    "version": 1,
    "family": "ramp",
    "variant": "steep",
    "created_at": "2026-09-23T10:00:00Z",
    "request": "Genera una rampa de 30 grados",
    "context": {"text": "escena vacia", "refs": [{"ref": "src/scene.py:42", "kind": "code"}]},
    "constraints": {"max_angle": 30},
    "trajectory": [
        {"role": "system", "content": "Eres un generador"},
        {"role": "user", "content": "Genera una rampa de 30 grados"},
        {"role": "assistant", "content": "", "tool_calls": [{"name": "make_ramp", "arguments": {"angle": 30}}]},
        {"role": "tool", "name": "make_ramp", "content": "ok"},
    ],
    "metrics": {"slope_error": 0.2, "anything": {"nested": [1, 2]}},
    "validation": {"status": "pending", "approved_by_human": False},
    "outcome": "success",
    "artifacts": [{"path": "final/ramp.blend", "hash": "sha256:" + "a" * 64, "kind": "mesh"}],
}


def _caso(**cambios):
    c = copy.deepcopy(CASO_OK)
    c.update(cambios)
    return c


def test_caso_valido():
    assert cs.validar_caso(CASO_OK) == []


def test_caso_valido_con_config_comprueba_prefijo():
    assert cs.validar_caso(CASO_OK, CONFIG_OK) == []
    otro = _caso(case_id="xyz-ramp.steep")
    assert "case_id" in _campos(cs.validar_caso(otro, CONFIG_OK))


def test_caso_exige_campos_obligatorios():
    for campo in ("case_id", "version", "outcome", "validation", "trajectory", "request",
                  "family", "variant"):
        c = copy.deepcopy(CASO_OK)
        del c[campo]
        assert campo in _campos(cs.validar_caso(c)), campo


def test_case_id_debe_casar_con_familia_y_variante():
    assert "case_id" in _campos(cs.validar_caso(_caso(case_id="geo-otra.cosa")))


def test_version_entero_positivo():
    for v in (0, -1, "1", 1.5, True):
        assert "version" in _campos(cs.validar_caso(_caso(version=v))), v


def test_validation_status_vocabulario_cerrado():
    for st in cs.VALIDATION_STATUS:
        aprobado = st == "approved"
        c = _caso(validation={"status": st, "approved_by_human": aprobado})
        assert cs.validar_caso(c) == [], st
    c = _caso(validation={"status": "gold", "approved_by_human": True})
    assert "validation.status" in _campos(cs.validar_caso(c))
    assert set(cs.VALIDATION_STATUS) == {"pending", "approved", "needs_changes", "rejected"}


def test_approved_exige_approved_by_human():
    c = _caso(validation={"status": "approved", "approved_by_human": False})
    assert "validation.approved_by_human" in _campos(cs.validar_caso(c))
    c = _caso(validation={"status": "approved"})
    assert "validation.approved_by_human" in _campos(cs.validar_caso(c))
    c = _caso(validation={"status": "approved", "approved_by_human": "yes"})
    assert "validation.approved_by_human" in _campos(cs.validar_caso(c))


def test_approved_by_human_true_sin_approved_se_rechaza():
    c = _caso(validation={"status": "pending", "approved_by_human": True})
    assert "validation.approved_by_human" in _campos(cs.validar_caso(c))


def test_outcome_vocabulario_cerrado():
    assert set(cs.OUTCOMES) == {"success", "failure", "corrected"}
    assert "outcome" in _campos(cs.validar_caso(_caso(outcome="useful")))
    assert "outcome" in _campos(cs.validar_caso(_caso(outcome="meh")))


def test_corrected_exige_supersedes_case_bien_formado():
    assert "supersedes_case" in _campos(cs.validar_caso(_caso(outcome="corrected")))
    mal = _caso(outcome="corrected", supersedes_case="geo-ramp.steep")
    assert "supersedes_case" in _campos(cs.validar_caso(mal))
    bien = _caso(outcome="corrected", version=2, supersedes_case="geo-ramp.steep@v001")
    assert cs.validar_caso(bien) == []


def test_trayectoria_rechaza_chain_of_thought():
    for clave in ("reasoning", "thinking", "chain_of_thought"):
        tr = copy.deepcopy(CASO_OK["trajectory"])
        tr[2][clave] = "pienso que..."
        assert "trajectory[2]." + clave in _campos(cs.validar_caso(_caso(trajectory=tr))), clave


def test_trayectoria_rol_invalido_y_tool_calls_mal_formados():
    tr = copy.deepcopy(CASO_OK["trajectory"])
    tr[0]["role"] = "narrator"
    tr[2]["tool_calls"] = [{"arguments": {}}]
    campos = _campos(cs.validar_caso(_caso(trajectory=tr)))
    assert "trajectory[0].role" in campos
    assert "trajectory[2].tool_calls[0].name" in campos


def test_trayectoria_vacia_se_rechaza():
    assert "trajectory" in _campos(cs.validar_caso(_caso(trajectory=[])))


def test_metrics_opacas_pero_objeto():
    assert cs.validar_caso(_caso(metrics={"lo_que_sea": "del proyecto"})) == []
    assert "metrics" in _campos(cs.validar_caso(_caso(metrics=[1, 2, 3])))


def test_context_texto_objeto_o_ausente():
    assert cs.validar_caso(_caso(context="solo texto")) == []
    c = copy.deepcopy(CASO_OK)
    del c["context"]
    assert cs.validar_caso(c) == []
    assert "context" in _campos(cs.validar_caso(_caso(context=42)))


def test_context_refs_con_procedencia():
    ok = _caso(context={"refs": [{"ref": "n:ramp-node", "kind": "graph-node"}]})
    assert cs.validar_caso(ok) == []
    mal = _caso(context={"refs": [{"ref": "", "kind": "code"}, {"kind": "code"}, "src/a.py:1"]})
    campos = _campos(cs.validar_caso(mal))
    assert {"context.refs[0].ref", "context.refs[1].ref", "context.refs[2]"} <= campos
    assert "context.refs" in _campos(cs.validar_caso(_caso(context={"refs": "src/a.py"})))


def test_artifacts_solo_referencias_sin_binario_inline():
    mal = _caso(artifacts=[{"path": "final/x.png", "hash": "sha256:" + "b" * 64, "kind": "image",
                            "content": "iVBORw0KGgo..."}])
    assert "artifacts[0].content" in _campos(cs.validar_caso(mal))
    sin_hash = _caso(artifacts=[{"path": "final/x.png", "kind": "image"}])
    assert "artifacts[0].hash" in _campos(cs.validar_caso(sin_hash))


def test_caso_no_objeto():
    assert cs.validar_caso("no") != []


# ------------------------------------------------------------------ mapeo de outcome externo

def test_mapeo_graphify_declarado():
    assert cs.OUTCOME_MAPEO["graphify"] == {"useful": "success", "dead_end": "failure", "corrected": "corrected"}
    assert cs.mapear_outcome("useful", "graphify") == "success"
    assert cs.mapear_outcome("dead_end", "graphify") == "failure"
    assert cs.mapear_outcome("corrected", "graphify") == "corrected"
    # el vocabulario propio pasa tal cual; lo desconocido no se inventa
    assert cs.mapear_outcome("failure") == "failure"
    assert cs.mapear_outcome("maybe", "graphify") is None
    assert cs.mapear_outcome("useful", "desconocida") is None
    assert cs.mapear_outcome("useful") is None


def test_mapeo_solo_apunta_al_vocabulario_cerrado():
    for fuente, tabla in cs.OUTCOME_MAPEO.items():
        assert set(tabla.values()) <= set(cs.OUTCOMES), fuente


# ------------------------------------------------------------------ CLI

def _cli(*args):
    return subprocess.run([sys.executable, os.path.join(HERE, "case_schema.py"), *args],
                          capture_output=True, text=True, encoding="utf-8")


def test_cli_exit_codes(tmp_path):
    ok = tmp_path / "caso.json"
    ok.write_text(json.dumps(CASO_OK), encoding="utf-8")
    mal = tmp_path / "mal.json"
    mal.write_text(json.dumps(_caso(outcome="meh")), encoding="utf-8")
    roto = tmp_path / "roto.json"
    roto.write_text("{", encoding="utf-8")
    cfg = tmp_path / "training.json"
    cfg.write_text(json.dumps(CONFIG_OK), encoding="utf-8")
    assert _cli("case", str(ok)).returncode == 0
    r = _cli("case", str(mal))
    assert r.returncode == 1 and "outcome" in r.stdout
    assert _cli("case", str(roto)).returncode == 2
    assert _cli("config", str(cfg)).returncode == 0
    assert _cli("case", str(ok), "--config", str(cfg)).returncode == 0
    assert _cli().returncode == 2


def test_sin_dependencias_externas():
    with open(os.path.join(HERE, "case_schema.py"), encoding="utf-8") as f:
        texto = f.read()
    for prohibido in ("import jsonschema", "import yaml", "import requests"):
        assert prohibido not in texto
