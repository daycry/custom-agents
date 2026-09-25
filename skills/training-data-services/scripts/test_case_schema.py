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



# ------------------------------------------------------------------ fix1 (revision intento 1, Fase 1)

RAROS = ([], ["success"], {}, {"a": 1}, None, 1.5, True, 0)


def _es_lista_de_errores(errores):
    return isinstance(errores, list) and all(set(e) == {"campo", "mensaje"} for e in errores)


def test_f1fix1_gap01_tipos_inesperados_devuelven_campo_y_mensaje():
    """gap #1: un valor de tipo inesperado (list/dict/None/...) nunca lanza: `{campo, mensaje}`."""
    for campo in ("outcome", "case_id", "family", "variant", "version", "supersedes_case", "request",
                  "trajectory", "context", "constraints", "metrics", "artifacts", "created_at"):
        for raro in RAROS:
            errores = cs.validar_caso(_caso(**{campo: raro}))
            assert _es_lista_de_errores(errores), (campo, raro)
    for raro in RAROS:
        val = {"status": raro, "approved_by_human": False}
        errores = cs.validar_caso(_caso(validation=val))
        assert _es_lista_de_errores(errores) and "validation.status" in _campos(errores), raro
        for fuente in (None, "graphify", raro):
            assert cs.mapear_outcome(raro, fuente) is None, (raro, fuente)
    for campo in ("outcome", "case_id"):
        for raro in ([], ["success"], {"a": 1}, None):
            assert campo in _campos(cs.validar_caso(_caso(**{campo: raro}))), (campo, raro)
    for campo in ("version", "enabled", "root", "id_prefix", "ids", "bridge_to_curator", "$comment"):
        for raro in RAROS:
            assert _es_lista_de_errores(cs.validar_config(dict(CONFIG_OK, **{campo: raro}))), (campo, raro)


def test_f1fix1_gap01_cli_tipo_inesperado_es_exit_1_sin_traceback(tmp_path):
    mal = tmp_path / "mal.json"
    mal.write_text(json.dumps(_caso(outcome=["success"])), encoding="utf-8")
    r = _cli("case", str(mal))
    assert r.returncode == 1, r.stderr
    assert "outcome" in r.stdout and "Traceback" not in r.stderr
    roto = tmp_path / "roto.json"
    roto.write_text("[", encoding="utf-8")
    assert _cli("config", str(roto)).returncode == 2


def test_f1fix1_gap02_root_dentro_de_docs_knowledge_absoluto_relativo_o_capitalizado(tmp_path):
    """gap #2 (M19): la regla se resuelve contra la raiz del proyecto, no textualmente."""
    raiz = str(tmp_path)
    absoluto = os.path.join(raiz, "docs", "knowledge", "cases")
    for mal in (absoluto, "docs/knowledge/cases", "Docs/Knowledge/x", "DOCS/knowledge",
                "./x/../docs/knowledge/y", os.path.join(raiz, "Docs", "KNOWLEDGE")):
        assert "root" in _campos(cs.validar_config(dict(CONFIG_OK, root=mal), raiz)), mal
    for bien in (os.path.join(raiz, "data", "cases"), "../case-store", "docs/knowledge-cases"):
        assert cs.validar_config(dict(CONFIG_OK, root=bien), raiz) == [], bien


def test_f1fix1_gap02_cargar_config_pasa_la_raiz_del_proyecto(tmp_path):
    d = tmp_path / ".claude" / "knowledge-services"
    d.mkdir(parents=True)
    absoluto = str(tmp_path / "docs" / "knowledge" / "cases")
    (d / "training.json").write_text(json.dumps(dict(CONFIG_OK, root=absoluto)), encoding="utf-8")
    config, _ruta, errores = cs.cargar_config(str(tmp_path))
    assert config is None and "root" in _campos(errores)


def test_f1fix1_gap03_regex_que_revienta_al_compilar_es_error_de_campo():
    for patron in ("a{4294967296}", "(" * 2000 + ")" * 2000):
        cfg = copy.deepcopy(CONFIG_OK)
        cfg["ids"]["family_pattern"] = patron
        errores = cs.validar_config(cfg)
        assert "ids.family_pattern" in _campos(errores), patron[:20]


def test_f1fix1_gap04_anclas_y_traversal():
    for campo in ("family", "variant"):
        for mal in ("ramp\n", "r/../../x", "r\\x", "..", "a\x00b"):
            assert campo in _campos(cs.validar_caso(_caso(**{campo: mal}))), (campo, mal)
    assert "id_prefix" in _campos(cs.validar_config(dict(CONFIG_OK, id_prefix="geo\n")))
    sup = _caso(outcome="corrected", version=2, supersedes_case="geo-ramp.steep@v001\n")
    assert "supersedes_case" in _campos(cs.validar_caso(sup))
    # patron del proyecto sin anclas: fullmatch, y separadores/`..` rechazados igualmente
    cfg = copy.deepcopy(CONFIG_OK)
    cfg["ids"]["family_pattern"] = "[a-z]"
    cfg["ids"]["variant_pattern"] = ".*"
    assert cs.validar_config(cfg) == []
    c = _caso(family="r/../../x", case_id="geo-r/../../x.steep")
    assert "family" in _campos(cs.validar_caso(c, cfg))
    assert "family" in _campos(cs.validar_caso(_caso(family="rr", case_id="geo-rr.steep"), cfg))
    assert "variant" in _campos(cs.validar_caso(_caso(variant="a/b", case_id="geo-ramp.a/b"), cfg))
    for mal in (("r/../../x", "steep"), ("ramp", ".."), ("ramp", "a\\b")):
        try:
            cs.directorio_version(mal[0], mal[1], 1)
        except ValueError:
            continue
        raise AssertionError(f"directorio_version acepto {mal!r}")


def test_f1fix1_gap05_supersedes_case_coherente_con_el_caso():
    ok = _caso(outcome="corrected", version=2, supersedes_case="geo-ramp.steep@v001")
    assert cs.validar_caso(ok) == []
    for sup, version in (("geo-ramp.steep@v002", 2),      # se reemplaza a si mismo
                         ("geo-ramp.steep@v003", 2),      # version posterior
                         ("geo-otra.cosa@v001", 2)):      # otro case_id
        c = _caso(outcome="corrected", version=version, supersedes_case=sup)
        assert "supersedes_case" in _campos(cs.validar_caso(c)), sup
    for outcome in ("success", "failure"):
        c = _caso(outcome=outcome, version=2, supersedes_case="geo-ramp.steep@v001")
        assert "supersedes_case" in _campos(cs.validar_caso(c)), outcome


def test_f1fix1_gap06_chain_of_thought_case_insensitive_por_prefijo_y_recursivo():
    for clave in ("Thinking", "reasoning_details", "REASONING", "scratchpad", "Chain_Of_Thought", "thoughts"):
        tr = copy.deepcopy(CASO_OK["trajectory"])
        tr[2][clave] = "pienso que..."
        assert "trajectory[2]." + clave in _campos(cs.validar_caso(_caso(trajectory=tr))), clave
    tr = copy.deepcopy(CASO_OK["trajectory"])
    tr[2]["tool_calls"][0]["arguments"] = {"angle": 30, "reasoning": "porque..."}
    assert "trajectory[2].tool_calls[0].arguments.reasoning" in _campos(cs.validar_caso(_caso(trajectory=tr)))
    tr = copy.deepcopy(CASO_OK["trajectory"])
    tr[2]["tool_calls"][0]["arguments"] = json.dumps({"opts": {"Thinking": "x"}})
    assert "trajectory[2].tool_calls[0].arguments.opts.Thinking" in _campos(cs.validar_caso(_caso(trajectory=tr)))
    tr = copy.deepcopy(CASO_OK["trajectory"])
    tr[1]["meta"] = [{"scratchpad_notes": "x"}]
    assert "trajectory[1].meta[0].scratchpad_notes" in _campos(cs.validar_caso(_caso(trajectory=tr)))
    # lo inocuo no dispara
    assert cs.validar_caso(CASO_OK) == []


def test_f1fix1_gap07_root_con_tilde_se_rechaza():
    for mal in ("~/store", "~", "~otro/x"):
        assert "root" in _campos(cs.validar_config(dict(CONFIG_OK, root=mal))), mal


def test_f1fix1_gap14_m2_version_booleana_en_config():
    assert "version" in _campos(cs.validar_config(dict(CONFIG_OK, version=True)))


def test_f1fix1_gap14_m15_version_width_entre_1_y_6():
    for w, valido in ((1, True), (6, True), (0, False), (7, False), (60, False)):
        cfg = copy.deepcopy(CONFIG_OK)
        cfg["ids"]["version_width"] = w
        assert ("ids.version_width" not in _campos(cs.validar_config(cfg))) is valido, w


def test_f1fix1_gap14_m16_tool_calls_solo_en_assistant():
    tr = copy.deepcopy(CASO_OK["trajectory"])
    tr[1]["tool_calls"] = [{"name": "make_ramp", "arguments": {}}]
    assert "trajectory[1].tool_calls" in _campos(cs.validar_caso(_caso(trajectory=tr)))


def test_f1fix1_gap14_m17_refs_kind_debe_ser_texto():
    c = _caso(context={"refs": [{"ref": "src/a.py:1", "kind": 5}]})
    assert "context.refs[0].kind" in _campos(cs.validar_caso(c))


def test_f1fix1_gap14_m18_clave_desconocida_dentro_de_ids():
    cfg = copy.deepcopy(CONFIG_OK)
    cfg["ids"]["family_regex"] = "^x$"
    assert "ids.family_regex" in _campos(cs.validar_config(cfg))


# ------------------------------------------------------------------ fix2 (revision intento 2, Fase 1)

def _cfg_permisiva():
    cfg = copy.deepcopy(CONFIG_OK)
    cfg["ids"]["family_pattern"] = ".+"
    cfg["ids"]["variant_pattern"] = ".+"
    return cfg


def test_f1fix2_gap19_supersedes_case_en_forma_canonica_y_version_minima_1():
    """gap #19: `@v0`/`@v000` (inexistente), `@v1` sin relleno y digitos unicode se rechazan."""
    for sup in ("geo-ramp.steep@v0", "geo-ramp.steep@v000", "geo-ramp.steep@v1", "geo-ramp.steep@v01",
                "geo-ramp.steep@v0001", "geo-ramp.steep@v١", "geo-ramp.steep@v00١"):
        c = _caso(outcome="corrected", version=2, supersedes_case=sup)
        assert "supersedes_case" in _campos(cs.validar_caso(c)), sup
    ok = _caso(outcome="corrected", version=2, supersedes_case="geo-ramp.steep@v001")
    assert cs.validar_caso(ok) == []
    # la forma canonica sigue `version_width` de la config del proyecto
    cfg = copy.deepcopy(CONFIG_OK)
    cfg["ids"]["version_width"] = 1
    assert cs.validar_caso(dict(ok, supersedes_case="geo-ramp.steep@v1"), cfg) == []
    assert "supersedes_case" in _campos(cs.validar_caso(ok, cfg))
    # una version por encima del ancho se escribe con todos sus digitos (v1000 con width 3)
    grande = _caso(outcome="corrected", version=1001, supersedes_case="geo-ramp.steep@v1000")
    assert cs.validar_caso(grande) == []


def test_f1fix2_gap20_punto_final_dos_puntos_y_nombres_reservados():
    """gap #20: con patrones del proyecto permisivos, `.` (separador reservado family.variant),
    punto/espacio final, `:` (flujo NTFS) y nombres reservados de Windows se rechazan."""
    cfg = _cfg_permisiva()
    for campo, mal in (("family", "ramp.x"), ("variant", "x.y"), ("variant", "steep."), ("variant", "steep "),
                       ("family", "a:b"), ("family", "con"), ("variant", "NUL"), ("family", "Com1"),
                       ("variant", "lpt9"), ("family", "aux")):
        c = _caso(**{campo: mal})
        c["case_id"] = cs.construir_case_id("geo", c["family"], c["variant"])
        assert campo in _campos(cs.validar_caso(c, cfg)), (campo, mal)
        try:
            cs.directorio_version(c["family"], c["variant"], 1)
        except ValueError:
            continue
        raise AssertionError(f"directorio_version acepto {mal!r}")
    # lo legitimo con patron permisivo sigue pasando (`console`, `con_x`, `com10` no son reservados)
    for fam in ("console", "con_x", "com10", "ramp"):
        c = _caso(family=fam, case_id=f"geo-{fam}.steep")
        assert cs.validar_caso(c, cfg) == [], fam


def test_f1fix2_gap20_root_con_prefijo_extendido_no_esquiva_adr019(tmp_path):
    """gap #20: `\\\\?\\<proyecto>\\docs\\knowledge\\...` (y `//?/`) es la misma carpeta."""
    raiz = str(tmp_path)
    dentro = os.path.join(raiz, "docs", "knowledge", "cases")
    for mal in ("\\\\?\\" + dentro, "//?/" + dentro.replace("\\", "/")):
        assert "root" in _campos(cs.validar_config(dict(CONFIG_OK, root=mal), raiz)), mal
    fuera = os.path.join(raiz, "data", "cases")
    assert cs.validar_config(dict(CONFIG_OK, root="\\\\?\\" + fuera), raiz) == []


def test_f1fix2_gap21_anidamiento_excesivo_se_rechaza_no_se_deja_de_mirar():
    """gap #21: pasado el limite de profundidad, error (fail closed), no silencio."""
    profundo = {"reasoning": "pienso..."}
    for _ in range(60):
        profundo = {"n": profundo}
    tr = copy.deepcopy(CASO_OK["trajectory"])
    tr[1]["meta"] = profundo
    errores = cs.validar_caso(_caso(trajectory=tr))
    assert any(e["campo"].startswith("trajectory[1]") and "anidamiento" in e["mensaje"] for e in errores), errores
    # un anidamiento razonable sin CoT no dispara nada
    llano = {"a": 1}
    for _ in range(10):
        llano = {"n": llano}
    tr = copy.deepcopy(CASO_OK["trajectory"])
    tr[1]["meta"] = llano
    assert cs.validar_caso(_caso(trajectory=tr)) == []


def test_f1fix2_gap22_parametros_de_proveedor_exentos_solo_en_arguments():
    """gap #22: `reasoning_effort`/`thinking_budget`/`reasoning_level` son parametros legitimos de
    herramienta DENTRO de `tool_calls[].arguments`; fuera de ahi siguen siendo CoT."""
    for clave in ("reasoning_effort", "thinking_budget", "reasoning_level", "Reasoning-Effort"):
        tr = copy.deepcopy(CASO_OK["trajectory"])
        tr[2]["tool_calls"][0]["arguments"] = {"angle": 30, clave: "high"}
        assert cs.validar_caso(_caso(trajectory=tr)) == [], clave
        tr = copy.deepcopy(CASO_OK["trajectory"])
        tr[2]["tool_calls"][0]["arguments"] = json.dumps({"opts": {clave: 1024}})
        assert cs.validar_caso(_caso(trajectory=tr)) == [], clave
        tr = copy.deepcopy(CASO_OK["trajectory"])
        tr[2][clave] = "high"                           # fuera de arguments: CoT
        assert "trajectory[2]." + clave in _campos(cs.validar_caso(_caso(trajectory=tr))), clave
    # la exencion es de la CLAVE, no de su contenido: CoT anidado bajo ella se sigue viendo
    tr = copy.deepcopy(CASO_OK["trajectory"])
    tr[2]["tool_calls"][0]["arguments"] = {"reasoning_effort": {"reasoning": "pienso..."}}
    assert "trajectory[2].tool_calls[0].arguments.reasoning_effort.reasoning" in _campos(
        cs.validar_caso(_caso(trajectory=tr)))
    # cualquier otra clave de CoT dentro de arguments sigue prohibida
    tr = copy.deepcopy(CASO_OK["trajectory"])
    tr[2]["tool_calls"][0]["arguments"] = {"reasoning_trace": "x"}
    assert "trajectory[2].tool_calls[0].arguments.reasoning_trace" in _campos(cs.validar_caso(_caso(trajectory=tr)))
    # una clave del turno que IMITA la ruta de arguments no hereda la exencion
    tr = copy.deepcopy(CASO_OK["trajectory"])
    tr[2]["x.tool_calls[0].arguments"] = {"reasoning_effort": "high"}
    assert any(e["campo"].endswith("reasoning_effort") for e in cs.validar_caso(_caso(trajectory=tr)))


def test_f1fix2_gap23_realpath_que_falla_rechaza_root(tmp_path, monkeypatch):
    """gap #23: si la ruta no se puede resolver, `root` se rechaza (fail closed)."""
    def _revienta(*_a, **_k):
        raise OSError("no resoluble")
    monkeypatch.setattr(cs.os.path, "realpath", _revienta)
    assert cs._root_en_docs_knowledge("data/cases", str(tmp_path)) is True


def test_f1fix2_gap24_n1_realpath_resuelve_enlaces_a_docs_knowledge(tmp_path):
    """N1 (`realpath` -> `abspath`): un enlace/junction hacia docs/knowledge se resuelve."""
    destino = tmp_path / "docs" / "knowledge"
    destino.mkdir(parents=True)
    alias = tmp_path / "alias"
    try:
        os.symlink(str(destino), str(alias), target_is_directory=True)
    except (OSError, NotImplementedError, AttributeError):
        if os.name != "nt":
            import pytest
            pytest.skip("sin enlaces simbolicos")
        import _winapi
        _winapi.CreateJunction(str(destino), str(alias))
    assert "root" in _campos(cs.validar_config(dict(CONFIG_OK, root="alias/cases"), str(tmp_path)))


def test_f1fix2_gap24_n3_error_al_resolver_desde_validar_config(tmp_path, monkeypatch):
    """N3 (`except` -> False): ValueError al resolver llega a `validar_config` como error de root."""
    def _revienta(*_a, **_k):
        raise ValueError("ruta ilegal")
    monkeypatch.setattr(cs.os.path, "realpath", _revienta)
    assert "root" in _campos(cs.validar_config(dict(CONFIG_OK, root="data/cases"), str(tmp_path)))


def test_f1fix2_gap24_n4_guion_equivale_a_guion_bajo_en_cot():
    """N4 (sin `-`->`_`): `chain-of-thought` es la misma clave que `chain_of_thought`."""
    for clave in ("chain-of-thought", "Chain-Of-Thought"):
        tr = copy.deepcopy(CASO_OK["trajectory"])
        tr[2][clave] = "x"
        assert "trajectory[2]." + clave in _campos(cs.validar_caso(_caso(trajectory=tr))), clave


def test_f1fix2_gap24_n9_controles_en_componentes_con_patron_del_proyecto():
    """N9: con patron permisivo, un caracter de control en family/variant se rechaza igual."""
    cfg = _cfg_permisiva()
    for campo, mal in (("family", "a\tb"), ("variant", "x\x01"), ("family", "a\x7fb")):
        c = _caso(**{campo: mal})
        c["case_id"] = cs.construir_case_id("geo", c["family"], c["variant"])
        errores = cs.validar_caso(c, cfg)
        assert any(e["campo"] == campo and "control" in e["mensaje"] for e in errores), (campo, mal)


def test_f1fix2_gap24_n10_directorio_version_rechaza_texto_vacio():
    """N10: `directorio_version` con family/variant vacio o en blanco levanta ValueError."""
    for fam, var in (("", "steep"), ("ramp", ""), ("   ", "steep"), (None, "steep")):
        try:
            cs.directorio_version(fam, var, 1)
        except ValueError:
            continue
        raise AssertionError(f"directorio_version acepto {(fam, var)!r}")


def test_f1fix2_gap24_n12_comment_debe_ser_texto():
    """N12: `$comment` no texto es error de ese campo."""
    for raro in (5, ["x"], {"a": 1}, True):
        assert "$comment" in _campos(cs.validar_config(dict(CONFIG_OK, **{"$comment": raro}))), raro
    assert cs.validar_config(dict(CONFIG_OK, **{"$comment": "nota"})) == []


def test_f1fix2_gap24_n13_root_con_caracteres_de_control():
    """N13: `root` con caracteres de control se rechaza con ese motivo."""
    for mal in ("data\x01cases", "data/\ncases", "\tstore"):
        errores = cs.validar_config(dict(CONFIG_OK, root=mal))
        assert any(e["campo"] == "root" and "control" in e["mensaje"] for e in errores), repr(mal)


def test_f1fix2_gap24_n14_cli_resuelve_root_contra_la_raiz_del_proyecto(tmp_path):
    """N14 (`_raiz_de`): la raiz se deduce de `<proyecto>/.claude/knowledge-services/training.json`
    o se toma de `--project-root`, nunca del cwd cuando hay una mejor."""
    proyecto = tmp_path / "proyecto"
    d = proyecto / ".claude" / "knowledge-services"
    d.mkdir(parents=True)
    cfg = d / "training.json"
    # absoluto: dentro de docs/knowledge SOLO si la raiz es `proyecto` (con cwd `otro`, no)
    cfg.write_text(json.dumps(dict(CONFIG_OK, root=str(proyecto / "docs" / "knowledge" / "cases"))),
                   encoding="utf-8")
    otro = tmp_path / "otro"
    otro.mkdir()
    script = os.path.join(HERE, "case_schema.py")

    def run(*args):
        return subprocess.run([sys.executable, script, *args], capture_output=True, text=True,
                              encoding="utf-8", cwd=str(otro))

    r = run("config", str(cfg))
    assert r.returncode == 1 and "root" in r.stdout, (r.stdout, r.stderr)
    suelto = tmp_path / "training.json"
    suelto.write_text(cfg.read_text(encoding="utf-8"), encoding="utf-8")
    assert run("config", str(suelto)).returncode == 0          # cwd `otro`: no cae en docs/knowledge
    r = run("config", str(suelto), "--project-root", str(proyecto))
    assert r.returncode == 1 and "root" in r.stdout, (r.stdout, r.stderr)


def test_f1fix2_gap24_n15_hash_debe_casar_entero():
    """N15 (`PATRON_HASH.match`): un hash con basura detras se rechaza."""
    arts = [{"path": "final/a.json", "hash": "sha256:abc123XYZ", "kind": "json"}]
    assert "artifacts[0].hash" in _campos(cs.validar_caso(_caso(artifacts=arts)))
    arts = [{"path": "final/a.json", "hash": "sha256:abc123 ", "kind": "json"}]
    assert "artifacts[0].hash" in _campos(cs.validar_caso(_caso(artifacts=arts)))


def test_f1fix2_gap24_n16_id_prefix_debe_casar_entero():
    """N16 (`PATRON_PREFIJO.match`): un id_prefix con basura detras se rechaza (config y case_id)."""
    for mal in ("geo!", "geo_x", "geo prefijo"):
        assert "id_prefix" in _campos(cs.validar_config(dict(CONFIG_OK, id_prefix=mal))), mal
    assert "case_id" in _campos(cs.validar_caso(_caso(case_id="geo!-ramp.steep")))


def test_f1fix2_gap24_n18_patron_roto_en_config_no_valida_no_lanza():
    """N18 (`_casa` sin `try`): una config sin validar con regex rota no hace reventar el caso."""
    cfg = copy.deepcopy(CONFIG_OK)
    cfg["ids"]["family_pattern"] = "("
    cfg["ids"]["variant_pattern"] = "a{4294967296}"
    errores = cs.validar_caso(CASO_OK, cfg)
    assert {"family", "variant"} <= _campos(errores)


# ------------------------------------------------------------------ fix3 (revision intento 3, Fase 1)

BS = "\\"
EN_WINDOWS = os.name == "nt"


def _prefijos_de_volumen(ruta_absoluta):
    r"""`\\?\Volume{guid}\...` y `\\?\GLOBALROOT\Device\HarddiskVolumeN\...` de una ruta
    absoluta con letra de unidad (solo Windows; sin red: consultas locales del kernel)."""
    import ctypes
    unidad, resto = ruta_absoluta[:2], ruta_absoluta[3:]
    vol = ctypes.create_unicode_buffer(260)
    dev = ctypes.create_unicode_buffer(260)
    formas = []
    if ctypes.windll.kernel32.GetVolumeNameForVolumeMountPointW(unidad + BS, vol, 260):
        formas.append(vol.value + resto)
    if ctypes.windll.kernel32.QueryDosDeviceW(unidad, dev, 260):
        formas.append(BS * 2 + "?" + BS + "GLOBALROOT" + dev.value + BS + resto)
        formas.append(BS * 2 + "." + BS + "GLOBALROOT" + dev.value + BS + resto)
    return formas


def test_f1fix3_gap26_root_por_volumen_o_globalroot_no_esquiva_adr019(tmp_path):
    r"""gap #26: `\\?\Volume{...}\<proyecto>\docs\knowledge\cases` y la forma GLOBALROOT son
    la misma carpeta: se resuelven con realpath sobre la ruta TAL CUAL (prefijo fuera DESPUES)."""
    if not EN_WINDOWS:
        import pytest
        pytest.skip("rutas de volumen/dispositivo: solo Windows")
    raiz = os.path.realpath(str(tmp_path))
    for existe in (False, True):
        if existe:
            os.makedirs(os.path.join(raiz, "docs", "knowledge", "cases"))
        dentro = os.path.join(raiz, "docs", "knowledge", "cases")
        formas = _prefijos_de_volumen(dentro)
        assert formas, "sin nombre de volumen para la unidad del tmp"
        for mal in formas:
            assert "root" in _campos(cs.validar_config(dict(CONFIG_OK, root=mal), raiz)), (existe, mal)
    # fuera de docs/knowledge, la misma forma de volumen se admite (se canoniza a letra de unidad)
    for bien in _prefijos_de_volumen(os.path.join(raiz, "data", "cases")):
        assert cs.validar_config(dict(CONFIG_OK, root=bien), raiz) == [], bien


def test_f1fix3_gap26_prefijo_de_volumen_que_no_se_canoniza_se_rechaza(tmp_path):
    """gap #26: un `root` con prefijo de volumen/dispositivo que realpath no lleva a letra de unidad
    o UNC (volumen inexistente, GLOBALROOT inventado) se rechaza: fail closed."""
    raiz = str(tmp_path)
    for mal in (BS * 2 + "?" + BS + "Volume{00000000-0000-0000-0000-000000000000}" + BS + "data",
                BS * 2 + "?" + BS + "GLOBALROOT" + BS + "Device" + BS + "NoExiste999" + BS + "data",
                "//?/Volume{00000000-0000-0000-0000-000000000000}/data"):
        errores = cs.validar_config(dict(CONFIG_OK, root=mal), raiz)
        assert "root" in _campos(errores), mal


def test_f1fix3_gap27_cli_json_anidado_en_exceso_es_exit_2_sin_traceback(tmp_path):
    """gap #27: `json.load` lanza RecursionError (no ValueError) con un JSON muy anidado: el CLI
    responde exit 2 «JSON ilegible (anidamiento excesivo)», sin traceback, en caso y en --config."""
    hondo = tmp_path / "hondo.json"
    hondo.write_text("[" * 100000 + "]" * 100000, encoding="utf-8")
    bueno = tmp_path / "caso.json"
    bueno.write_text(json.dumps(CASO_OK), encoding="utf-8")
    script = os.path.join(HERE, "case_schema.py")
    for args in (("case", str(hondo)), ("config", str(hondo)), ("case", str(bueno), "--config", str(hondo))):
        r = subprocess.run([sys.executable, script, *args], capture_output=True, text=True, encoding="utf-8")
        assert r.returncode == 2, (args, r.returncode, r.stderr[-300:])
        assert "Traceback" not in r.stderr, r.stderr[-300:]
        assert "anidamiento" in r.stderr, r.stderr[-300:]


def test_f1fix3_gap27_cargar_config_con_json_anidado_es_error_de_fichero(tmp_path):
    """gap #27 (misma clase, via `cargar_config`, que usan capabilities y el recorder): error
    `(fichero)`, nunca RecursionError."""
    d = tmp_path / ".claude" / "knowledge-services"
    d.mkdir(parents=True)
    (d / "training.json").write_text("{\"a\":" * 100000 + "1" + "}" * 100000, encoding="utf-8")
    cfg, ruta, errores = cs.cargar_config(str(tmp_path))
    assert cfg is None and ruta and "(fichero)" in _campos(errores)
    assert any("anidamiento" in e["mensaje"] for e in errores), errores


def test_f1fix3_gap29a_arguments_texto_anidado_en_exceso_no_revienta():
    """gap #29 (a): `arguments` en texto JSON con 5000 niveles -> RecursionError al parsear ->
    error de anidamiento (fail closed), nunca una excepcion."""
    tr = copy.deepcopy(CASO_OK["trajectory"])
    tr[2]["tool_calls"][0]["arguments"] = "[" * 5000 + "]" * 5000
    errores = cs.validar_caso(_caso(trajectory=tr))
    assert any(e["campo"] == "trajectory[2].tool_calls[0].arguments" and "anidamiento" in e["mensaje"]
               for e in errores), errores


def test_f1fix3_gap29b_prefijo_unc_se_reconstruye_con_doble_barra():
    r"""gap #29 (b): `\\?\UNC\srv\sh\x` (y `//?/UNC/`) es `\\srv\sh\x`, no `srv\sh\x`."""
    assert cs._sin_prefijo_extendido(BS * 2 + "?" + BS + "UNC" + BS + "srv" + BS + "sh" + BS + "x") == \
        BS * 2 + "srv" + BS + "sh" + BS + "x"
    assert cs._sin_prefijo_extendido("//?/UNC/srv/sh/x") == BS * 2 + "srv/sh/x"
    assert cs._sin_prefijo_extendido(BS * 2 + "?" + BS + "C:" + BS + "x") == "C:" + BS + "x"
    assert cs._sin_prefijo_extendido("C:" + BS + "x") == "C:" + BS + "x"


def test_f1fix3_gap29b_root_unc_extendido_con_proyecto_unc(monkeypatch):
    r"""gap #29 (b): con proyecto UNC, `\\?\UNC\<srv>\<sh>\...\docs\knowledge\cases` se
    rechaza y el mismo prefijo fuera de docs/knowledge se admite (realpath neutro: sin red)."""
    if not EN_WINDOWS:
        import pytest
        pytest.skip("rutas UNC: solo Windows")
    monkeypatch.setattr(cs.os.path, "realpath", lambda p, *a, **k: p)
    raiz = BS * 2 + "srv" + BS + "sh" + BS + "proj"
    ext = BS * 2 + "?" + BS + "UNC" + BS + "srv" + BS + "sh" + BS + "proj"
    assert cs._root_en_docs_knowledge(ext + BS + "docs" + BS + "knowledge" + BS + "cases", raiz) is True
    assert cs._root_en_docs_knowledge(ext + BS + "data" + BS + "cases", raiz) is False
