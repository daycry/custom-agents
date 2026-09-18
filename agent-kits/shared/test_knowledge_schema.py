import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _load():
    spec = importlib.util.spec_from_file_location("knowledge_schema", os.path.join(HERE, "knowledge-schema.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["knowledge_schema"] = mod
    spec.loader.exec_module(mod)
    return mod


ks = _load()


def _valida(**over):
    cfg = json.loads(json.dumps(ks.DEFAULT_TAXONOMY_FALLBACK))
    cfg.update(over)
    return cfg


# ------------------------------------------------------------------ estructura básica

def test_default_template_es_valido():
    assert ks.validar(ks.default_taxonomy(), "template") == []


def test_default_fallback_es_valido():
    assert ks.validar(json.loads(json.dumps(ks.DEFAULT_TAXONOMY_FALLBACK)), "fallback") == []


def test_falta_version():
    cfg = _valida()
    del cfg["version"]
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "version" for e in errores)


def test_version_no_soportada():
    cfg = _valida(version=99)
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "version" for e in errores)


def test_categories_vacio_es_invalido():
    cfg = _valida(categories=[])
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "categories" for e in errores)


def test_key_duplicada():
    cfg = _valida(categories=[
        {"key": "DECISION", "folder": "adr", "min_evidence": "observation", "routing": {}},
        {"key": "DECISION", "folder": "adr2", "min_evidence": "observation", "routing": {}},
    ])
    errores = ks.validar(cfg, "t.json")
    assert any("key" in e["campo"] and "duplicada" in e["mensaje"] for e in errores)


def test_min_evidence_fuera_de_evidence_levels():
    cfg = _valida(categories=[
        {"key": "X", "folder": "x", "min_evidence": "nivel-inventado", "routing": {}},
    ])
    errores = ks.validar(cfg, "t.json")
    assert any("min_evidence" in e["campo"] for e in errores)


# ------------------------------------------------------------------ routing fail-closed (CA-11)

def test_routing_a_backend_no_declarado_falla():
    cfg = _valida(
        backends={"kwipu": {"type": "markdown-export"}},
        categories=[{"key": "PATTERN", "folder": "patterns", "min_evidence": "observation",
                     "routing": {"graphiti": True}}],
    )
    errores = ks.validar(cfg, "t.json")
    assert any("graphiti" in e["mensaje"] and "no declarado" in e["mensaje"] for e in errores)
    assert any(e["campo"] == "categories[0].routing.graphiti" for e in errores)


def test_routing_a_backend_declarado_es_valido():
    cfg = _valida(
        backends={"kwipu": {"type": "markdown-export"}},
        categories=[{"key": "PATTERN", "folder": "patterns", "min_evidence": "observation",
                     "routing": {"kwipu": True}}],
    )
    assert ks.validar(cfg, "t.json") == []


def test_routing_valor_invalido():
    cfg = _valida(
        backends={"kwipu": {"type": "markdown-export"}},
        categories=[{"key": "PATTERN", "folder": "patterns", "min_evidence": "observation",
                     "routing": {"kwipu": "todo"}}],
    )
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "categories[0].routing.kwipu" for e in errores)


def test_categoria_sin_routing_no_es_error_pero_no_exporta():
    cfg = _valida(
        backends={"kwipu": {"type": "markdown-export"}},
        categories=[{"key": "PATTERN", "folder": "patterns", "min_evidence": "observation"}],
    )
    assert ks.validar(cfg, "t.json") == []
    assert ks.categorias_por_backend(cfg, "kwipu") == []


# ------------------------------------------------------------------ backends

def test_backend_sin_type_falla():
    cfg = _valida(backends={"kwipu": {}})
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "backends.kwipu.type" for e in errores)


def test_backend_enabled_no_booleano():
    cfg = _valida(backends={"kwipu": {"type": "markdown-export", "enabled": "si"}})
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "backends.kwipu.enabled" for e in errores)


# ------------------------------------------------------------------ estado/tag inválidos (CA-01, CA-13)

def test_utility_scoring_no_booleano():
    cfg = _valida(utility_scoring="si")
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "utility_scoring" for e in errores)


def test_denylist_no_lista_de_cadenas():
    cfg = _valida(denylist=[1, 2, 3])
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "denylist" for e in errores)


def test_contenido_no_es_objeto():
    errores = ks.validar([1, 2, 3], "t.json")
    assert errores and errores[0]["fichero"] == "t.json"


# ------------------------------------------------------------------ cargar_taxonomia (CA-01/CA-09)

def test_cargar_taxonomia_sin_fichero_usa_default(tmp_path):
    config, origen, ruta, errores = ks.cargar_taxonomia(root=str(tmp_path))
    assert origen == "default"
    assert ruta is None
    assert errores == []
    assert config["categories"]


def test_cargar_taxonomia_con_fichero_de_proyecto(tmp_path):
    proyecto = tmp_path / ".claude" / "knowledge-services"
    proyecto.mkdir(parents=True)
    cfg = _valida(id_prefix="mr")
    (proyecto / "taxonomy.json").write_text(json.dumps(cfg), encoding="utf-8")
    config, origen, ruta, errores = ks.cargar_taxonomia(root=str(tmp_path))
    assert origen == "proyecto"
    assert ruta is not None
    assert errores == []
    assert config["id_prefix"] == "mr"


def test_cargar_taxonomia_json_invalido(tmp_path):
    proyecto = tmp_path / ".claude" / "knowledge-services"
    proyecto.mkdir(parents=True)
    (proyecto / "taxonomy.json").write_text("{ esto no es json", encoding="utf-8")
    config, origen, ruta, errores = ks.cargar_taxonomia(root=str(tmp_path))
    assert origen == "proyecto"
    assert errores and "JSON ilegible" in errores[0]["mensaje"]


# ------------------------------------------------------------------ CLI

def test_cli_default_exit_0():
    assert ks.main(["--default"]) == 0


def test_cli_fichero_invalido_exit_1(tmp_path):
    p = tmp_path / "taxonomy.json"
    p.write_text(json.dumps({"version": 1, "categories": []}), encoding="utf-8")
    assert ks.main([str(p)]) == 1


def test_cli_fichero_inexistente_exit_2(tmp_path):
    assert ks.main([str(tmp_path / "no-existe.json")]) == 2


def test_cli_sin_argumentos_exit_2():
    assert ks.main([]) == 2
