"""
tests/test_graphiti_model.py — `skills/knowledge-services/backends/graphiti_model.py`
(graphiti-memory T-02, ADR-018 enmienda 2026-09-18, CA-13 reformulado).

Cubre: mapeo categoría -> tipo de entidad EFECTIVO del servidor (`entity_map`, default
`Document`), el bloque `entity_types` propuesto para `config.yaml` del servidor (uno por tipo
efectivo + `Knowledge`/`Evidence`), las relaciones núcleo + `relations` declaradas, y la
sucesión `SUPERSEDES` (conserva historia, marca vigencia).
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE_PATH = os.path.normpath(os.path.join(
    HERE, "..", "skills", "knowledge-services", "backends", "graphiti_model.py"))


def _load():
    spec = importlib.util.spec_from_file_location("graphiti_model", MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["graphiti_model"] = mod
    spec.loader.exec_module(mod)
    return mod


gm = _load()

TAXONOMIA_A = {
    "version": 1,
    "categories": [
        {"key": "DECISION", "folder": "adr", "min_evidence": "human_confirmed_rule"},
        {"key": "PATTERN", "folder": "gotchas", "min_evidence": "multiple_validated_cases"},
        {"key": "GOTCHA", "folder": "gotchas", "min_evidence": "validated_case"},
    ],
}

TAXONOMIA_B = {
    "version": 1,
    "categories": [
        {"key": "TOOL", "folder": "tools", "min_evidence": "observation"},
        {"key": "RUNBOOK", "folder": "runbooks", "min_evidence": "single_case"},
    ],
}


# ------------------------------------------------------------------ tipo_entidad / tipos_por_categoria

def test_tipo_entidad_usa_entity_map():
    config = {"entity_map": {"DECISION": "Organization"}}
    assert gm.tipo_entidad("DECISION", config) == "Organization"


def test_tipo_entidad_sin_mapeo_cae_al_default_document():
    config = {"entity_map": {"DECISION": "Organization"}}
    assert gm.tipo_entidad("PATTERN", config) == "Document"


def test_tipo_entidad_sin_entity_map_cae_al_default():
    assert gm.tipo_entidad("PATTERN", {}) == "Document"
    assert gm.tipo_entidad("PATTERN", None) == "Document"


def test_tipos_por_categoria_dos_taxonomias_distintas():
    config_a = {"entity_map": {"DECISION": "Organization", "PATTERN": "Topic"}}
    mapa_a = gm.tipos_por_categoria(TAXONOMIA_A, config_a)
    assert mapa_a == {"DECISION": "Organization", "PATTERN": "Topic", "GOTCHA": "Document"}

    config_b = {"entity_map": {"TOOL": "Project"}}
    mapa_b = gm.tipos_por_categoria(TAXONOMIA_B, config_b)
    assert mapa_b == {"TOOL": "Project", "RUNBOOK": "Document"}


def test_tipos_por_categoria_sin_categories_es_vacio():
    assert gm.tipos_por_categoria({}, {}) == {}


# ------------------------------------------------------------------ relaciones (núcleo + declaradas)

def test_relaciones_efectivas_incluye_nucleo_sin_config():
    assert gm.relaciones_efectivas({}) == gm.RELACIONES_NUCLEO


def test_relaciones_efectivas_anade_las_declaradas_sin_duplicar_nucleo():
    config = {"relations": ["MITIGATES", "APPLIES_TO", "SUPERSEDES"]}
    out = gm.relaciones_efectivas(config)
    assert out == gm.RELACIONES_NUCLEO + ("MITIGATES", "APPLIES_TO")
    # SUPERSEDES ya está en el núcleo: no aparece dos veces.
    assert out.count("SUPERSEDES") == 1


def test_relaciones_efectivas_relations_no_lista_se_ignora():
    assert gm.relaciones_efectivas({"relations": "no-es-una-lista"}) == gm.RELACIONES_NUCLEO


# ------------------------------------------------------------------ propuesta de entity_types (YAML)

def test_proponer_entity_types_yaml_incluye_nucleo_y_categorias():
    config = {"entity_map": {"DECISION": "Organization"}}
    yaml_texto = gm.proponer_entity_types_yaml(TAXONOMIA_A, config)
    assert yaml_texto.startswith("entity_types:\n")
    assert "name: Organization" in yaml_texto
    assert "name: Document" in yaml_texto  # PATTERN y GOTCHA, sin mapeo -> default
    assert "name: Knowledge" in yaml_texto
    assert "name: Evidence" in yaml_texto
    # Un mismo tipo efectivo compartido por 2 categorías no se duplica como entrada.
    assert yaml_texto.count("name: Document") == 1


def test_proponer_entity_types_yaml_es_yaml_valido():
    import pytest
    yaml = pytest.importorskip("yaml")
    config = {"entity_map": {"TOOL": "Project"}}
    yaml_texto = gm.proponer_entity_types_yaml(TAXONOMIA_B, config)
    parsed = yaml.safe_load(yaml_texto)
    assert isinstance(parsed, dict) and "entity_types" in parsed
    nombres = {entrada["name"] for entrada in parsed["entity_types"]}
    assert nombres == {"Project", "Document", "Knowledge", "Evidence"}


def test_proponer_entity_types_yaml_taxonomia_vacia_solo_nucleo():
    yaml_texto = gm.proponer_entity_types_yaml({"categories": []}, {})
    assert "name: Knowledge" in yaml_texto
    assert "name: Evidence" in yaml_texto
    assert "name: Document" not in yaml_texto


# ------------------------------------------------------------------ sucesión SUPERSEDES (CA-11)

def test_cadena_supersedes_conserva_historia_y_marca_vigencia():
    versiones = [
        {"knowledge_id": "mr.pattern.fast-curve.v1"},
        {"knowledge_id": "mr.pattern.fast-curve.v2"},
        {"knowledge_id": "mr.pattern.fast-curve.v3"},
    ]
    resultado = gm.cadena_supersedes(versiones)
    assert len(resultado["relaciones"]) == 2
    assert resultado["relaciones"][0] == {
        "relacion": "SUPERSEDES",
        "origen": "mr.pattern.fast-curve.v2",
        "destino": "mr.pattern.fast-curve.v1",
    }
    assert resultado["relaciones"][1] == {
        "relacion": "SUPERSEDES",
        "origen": "mr.pattern.fast-curve.v3",
        "destino": "mr.pattern.fast-curve.v2",
    }
    # Vigencia: solo la última versión vive; ninguna se borra (unión = todas las versiones).
    assert resultado["vigentes"] == {"mr.pattern.fast-curve.v3"}
    assert resultado["invalidados"] == {"mr.pattern.fast-curve.v1", "mr.pattern.fast-curve.v2"}
    assert resultado["vigentes"] | resultado["invalidados"] == {e["knowledge_id"] for e in versiones}


def test_cadena_supersedes_una_sola_version_no_genera_relaciones():
    resultado = gm.cadena_supersedes([{"knowledge_id": "mr.pattern.solo.v1"}])
    assert resultado["relaciones"] == []
    assert resultado["vigentes"] == {"mr.pattern.solo.v1"}
    assert resultado["invalidados"] == set()


def test_cadena_supersedes_vacia():
    resultado = gm.cadena_supersedes([])
    assert resultado == {"relaciones": [], "vigentes": set(), "invalidados": set()}


if __name__ == "__main__":
    import unittest
    unittest.main()
