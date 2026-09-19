"""
tests/test_graphiti_model.py — `skills/knowledge-services/backends/graphiti_model.py`
(graphiti-memory T-02, ADR-018 enmienda 2026-09-18, CA-13 reformulado;
T-02-fix2: gaps #16/#18/#20/#22/#26 de la revisión de dos lentes, intento 2).

Cubre: mapeo categoría -> tipo de entidad EFECTIVO del servidor (`entity_map`, default
`Document` si la categoría no tiene mapeo válido), el bloque `entity_types` propuesto para
`config.yaml` del servidor (UNA entrada POR CATEGORÍA — nombre `entity_map[key]` si es una
cadena no vacía, si no `TitleCase` Unicode de la propia `key` — más `Knowledge`/`Evidence`;
nunca el genérico `Document` en la propuesta), la propuesta COMPLETA `proponer_config`
(`entity_types` + el `entity_map` que los hace efectivos, gap #16), las relaciones núcleo +
`relations` declaradas, y la sucesión `SUPERSEDES` (conserva historia, marca vigencia).
"""
import importlib.util
import os
import sys

import pytest

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
    # T-01-fix1 gap #2: una entrada POR CATEGORÍA (no por tipo efectivo agrupado); sin mapeo
    # explícito en `entity_map`, el nombre se deriva de la `key` en TitleCase — nunca el
    # genérico `Document` (eso escondería PATTERN/GOTCHA bajo el mismo tipo sin que el usuario
    # lo decidiera).
    config = {"entity_map": {"DECISION": "Organization"}}
    yaml_texto = gm.proponer_entity_types_yaml(TAXONOMIA_A, config)
    assert yaml_texto.startswith("entity_types:\n")
    assert f'name: {gm._yaml_cadena("Organization")}' in yaml_texto
    assert f'name: {gm._yaml_cadena("Pattern")}' in yaml_texto  # sin mapeo -> TitleCase(key)
    assert f'name: {gm._yaml_cadena("Gotcha")}' in yaml_texto  # sin mapeo -> TitleCase(key)
    assert f'name: {gm._yaml_cadena("Knowledge")}' in yaml_texto
    assert f'name: {gm._yaml_cadena("Evidence")}' in yaml_texto
    assert "Document" not in yaml_texto


def test_proponer_entity_types_yaml_es_yaml_valido():
    yaml = pytest.importorskip("yaml")
    config = {"entity_map": {"TOOL": "Project"}}
    yaml_texto = gm.proponer_entity_types_yaml(TAXONOMIA_B, config)
    parsed = yaml.safe_load(yaml_texto)
    assert isinstance(parsed, dict) and "entity_types" in parsed
    nombres = {entrada["name"] for entrada in parsed["entity_types"]}
    assert nombres == {"Project", "Runbook", "Knowledge", "Evidence"}


def test_proponer_entity_types_yaml_taxonomia_vacia_solo_nucleo():
    yaml_texto = gm.proponer_entity_types_yaml({"categories": []}, {})
    assert f'name: {gm._yaml_cadena("Knowledge")}' in yaml_texto
    assert f'name: {gm._yaml_cadena("Evidence")}' in yaml_texto
    assert "Document" not in yaml_texto


def test_proponer_entity_types_yaml_dedupe_por_nombre_explicito():
    # Dos categorías mapeadas al MISMO tipo explícito no duplican la entrada `name:`.
    taxonomy = {
        "categories": [
            {"key": "DECISION", "folder": "adr", "min_evidence": "x"},
            {"key": "RUNBOOK", "folder": "runbooks", "min_evidence": "x"},
        ],
    }
    config = {"entity_map": {"DECISION": "Organization", "RUNBOOK": "Organization"}}
    yaml_texto = gm.proponer_entity_types_yaml(taxonomy, config)
    assert yaml_texto.count(f'name: {gm._yaml_cadena("Organization")}') == 1
    assert "DECISION" in yaml_texto and "RUNBOOK" in yaml_texto


def test_proponer_entity_types_yaml_titlecase_normaliza_separadores():
    taxonomy = {
        "categories": [{"key": "MULTI_WORD-KEY", "folder": "x", "min_evidence": "x"}],
    }
    yaml_texto = gm.proponer_entity_types_yaml(taxonomy, {})
    assert f'name: {gm._yaml_cadena("MultiWordKey")}' in yaml_texto


# --------------------------------------------------------- T-01-fix1 gap #4: `name:` escapado
#
# Nota (T-02-fix2 gap #20): la cadena vacía/blanca ya NO es un "nombre hostil que se escapa" —
# es un valor INVÁLIDO de `entity_map` (igual que en `tipo_entidad`) que degrada con aviso al
# nombre derivado de la `key`; ver `test_proponer_entity_types_yaml_valor_vacio_degrada_...`
# más abajo. Las listas de aquí solo cubren nombres hostiles que SÍ son cadenas no vacías.

def test_proponer_entity_types_yaml_escapa_nombres_hostiles():
    nombres_hostiles = [
        "Doc: interno",
        "Doc\n  - name: Injected",
        "yes",
        "no",
        "{a: 1}",
        "null",
    ]
    for nombre in nombres_hostiles:
        taxonomy = {"categories": [{"key": "X", "folder": "x", "min_evidence": "x"}]}
        config = {"entity_map": {"X": nombre}}
        yaml_texto = gm.proponer_entity_types_yaml(taxonomy, config)
        # El nombre hostil SIEMPRE va entre comillas dobles (mismo criterio que `description`);
        # nunca aparece como escalar YAML sin comillas ni inyecta líneas nuevas de mapeo (se
        # cuentan solo las líneas REALES `  - name:`, no la subcadena dentro del valor escapado).
        assert f"name: {gm._yaml_cadena(nombre)}" in yaml_texto
        lineas_name = [l for l in yaml_texto.splitlines() if l.startswith("  - name:")]
        assert len(lineas_name) == 3  # X + Knowledge + Evidence, ninguna inyectada


def test_proponer_entity_types_yaml_nombres_hostiles_son_yaml_valido():
    yaml = pytest.importorskip("yaml")
    taxonomy = {"categories": [{"key": "X", "folder": "x", "min_evidence": "x"}]}
    for nombre in ("Doc: interno", "Doc\n  - name: Injected", "yes", "{a: 1}"):
        config = {"entity_map": {"X": nombre}}
        yaml_texto = gm.proponer_entity_types_yaml(taxonomy, config)
        parsed = yaml.safe_load(yaml_texto)
        entradas = parsed["entity_types"]
        assert len(entradas) == 3
        nombres = [e["name"] for e in entradas]
        assert nombre in nombres


# ------------------------------------------------ T-02-fix2 gap #20: valores invalidos de entity_map

def test_tipo_entidad_valor_vacio_en_entity_map_degrada_con_aviso():
    for valor_invalido in ("", "   ", 123, [], None):
        config = {"entity_map": {"DECISION": valor_invalido}}
        with pytest.warns(RuntimeWarning):
            assert gm.tipo_entidad("DECISION", config) == "Document"


def test_proponer_entity_types_yaml_valor_vacio_degrada_al_nombre_derivado():
    taxonomy = {"categories": [{"key": "X", "folder": "x", "min_evidence": "x"}]}
    for valor_invalido in ("", "   ", 123, []):
        config = {"entity_map": {"X": valor_invalido}}
        with pytest.warns(RuntimeWarning):
            yaml_texto = gm.proponer_entity_types_yaml(taxonomy, config)
        # Sin valor valido en entity_map, cae al nombre derivado de la key (TitleCase("X") = "X"),
        # NUNCA emite `name: ""` ni omite la categoria en silencio.
        assert 'name: "X"' in yaml_texto


# ------------------------------------------------------ T-02-fix2 gap #18: TitleCase Unicode

def test_titlecase_clave_normaliza_unicode():
    assert gm._titlecase_clave("decisión") == "Decisión"
    assert gm._titlecase_clave("日本") == "日本"


def test_titlecase_clave_nfkc_normaliza_forma_de_composicion():
    # 'e' + combining acute accent (forma NFD) debe normalizar a la misma TitleCase que 'é' (NFC).
    nfd = "café"  # café en forma descompuesta
    assert gm._titlecase_clave(nfd) == gm._titlecase_clave("café")


def test_proponer_entity_types_yaml_key_sin_alfanumericos_falla_explicito():
    taxonomy = {"categories": [{"key": "___", "folder": "x", "min_evidence": "x"}]}
    with pytest.raises(ValueError, match="entity_map"):
        gm.proponer_entity_types_yaml(taxonomy, {})


def test_proponer_entity_types_yaml_colision_implicita_falla_explicito():
    # Dos keys distintas que, SIN mapeo explicito, derivan al mismo TitleCase ("MultiWord").
    taxonomy = {
        "categories": [
            {"key": "MULTI WORD", "folder": "x", "min_evidence": "x"},
            {"key": "MULTI-WORD", "folder": "x", "min_evidence": "x"},
        ],
    }
    with pytest.raises(ValueError, match="entity_map"):
        gm.proponer_entity_types_yaml(taxonomy, {})


# ------------------------------------------------------- T-02-fix2 gap #22: tolerancia de entrada

def test_proponer_entity_types_yaml_config_no_dict_degrada_con_aviso():
    taxonomy = {"categories": [{"key": "X", "folder": "x", "min_evidence": "x"}]}
    with pytest.warns(RuntimeWarning):
        yaml_texto = gm.proponer_entity_types_yaml(taxonomy, ["entity_map"])
    assert 'name: "X"' in yaml_texto


def test_proponer_entity_types_yaml_key_no_string_lanza_valueerror():
    taxonomy = {"categories": [{"key": 123, "folder": "x", "min_evidence": "x"}]}
    with pytest.raises(ValueError):
        gm.proponer_entity_types_yaml(taxonomy, {})


def test_proponer_config_config_no_dict_degrada_con_aviso():
    taxonomy = {"categories": [{"key": "X", "folder": "x", "min_evidence": "x"}]}
    with pytest.warns(RuntimeWarning):
        resultado = gm.proponer_config(taxonomy, ["entity_map"])
    assert resultado["entity_map"] == {"X": "X"}


# ------------------------------------------------------------- T-02-fix2 gap #16: proponer_config

def test_proponer_config_devuelve_yaml_y_entity_map_completos():
    resultado = gm.proponer_config(TAXONOMIA_A, {"entity_map": {"DECISION": "Organization"}})
    assert set(resultado.keys()) == {"entity_types_yaml", "entity_map", "nota"}
    assert resultado["entity_types_yaml"].startswith("entity_types:\n")
    assert resultado["entity_map"] == {
        "DECISION": "Organization",
        "PATTERN": "Pattern",
        "GOTCHA": "Gotcha",
    }
    assert "Document" in resultado["nota"]


def test_proponer_config_aplicar_entity_map_hace_tipos_por_categoria_igual_a_lo_propuesto():
    resultado = gm.proponer_config(TAXONOMIA_A, {})
    config_aplicada = {"entity_map": resultado["entity_map"]}
    assert gm.tipos_por_categoria(TAXONOMIA_A, config_aplicada) == resultado["entity_map"]


def test_proponer_config_sin_taxonomia_solo_nucleo():
    resultado = gm.proponer_config({"categories": []}, {})
    assert resultado["entity_map"] == {}
    assert "Knowledge" in resultado["entity_types_yaml"]
    assert "Evidence" in resultado["entity_types_yaml"]


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


# ------------------------------------------------------------ T-01-fix1 gap #5: invariantes

def test_cadena_supersedes_ids_repetidos_lanza_valueerror():
    versiones = [
        {"knowledge_id": "mr.pattern.x.v1"},
        {"knowledge_id": "mr.pattern.x.v2"},
        {"knowledge_id": "mr.pattern.x.v1"},  # repetido: [A, B, A]
    ]
    with pytest.raises(ValueError):
        gm.cadena_supersedes(versiones)


def test_cadena_supersedes_ids_repetidos_consecutivos_lanza_valueerror():
    versiones = [{"knowledge_id": "a"}, {"knowledge_id": "a"}, {"knowledge_id": "b"}]
    with pytest.raises(ValueError):
        gm.cadena_supersedes(versiones)  # evitaría SUPERSEDES a→a (auto-sucesión)


def test_cadena_supersedes_vigentes_e_invalidados_son_disjuntos():
    resultado = gm.cadena_supersedes([{"knowledge_id": "x"}, {"knowledge_id": "y"}])
    assert resultado["vigentes"] & resultado["invalidados"] == set()


def test_cadena_supersedes_ninguna_relacion_es_auto_sucesion():
    resultado = gm.cadena_supersedes(
        [{"knowledge_id": "a"}, {"knowledge_id": "b"}, {"knowledge_id": "c"}]
    )
    for relacion in resultado["relaciones"]:
        assert relacion["origen"] != relacion["destino"]


# ------------------------------------------------------------- T-01-fix1 gap #12: validacion

def test_cadena_supersedes_elemento_sin_knowledge_id_lanza_valueerror():
    with pytest.raises(ValueError):
        gm.cadena_supersedes([{"id": "B"}])


def test_cadena_supersedes_no_lista_lanza_typeerror():
    with pytest.raises(TypeError):
        gm.cadena_supersedes({"knowledge_id": "a"})


def test_cadena_supersedes_elemento_no_dict_lanza_typeerror():
    with pytest.raises(TypeError):
        gm.cadena_supersedes(["a", "b"])


def test_cadena_supersedes_knowledge_id_vacio_lanza_valueerror():
    with pytest.raises(ValueError):
        gm.cadena_supersedes([{"knowledge_id": ""}])


def test_cadena_supersedes_knowledge_id_no_string_lanza_valueerror():
    with pytest.raises(ValueError):
        gm.cadena_supersedes([{"knowledge_id": 123}])


def test_tipo_entidad_config_no_dict_cae_al_default_con_warning():
    with pytest.warns(RuntimeWarning):
        assert gm.tipo_entidad("adr", ["entity_map"]) == "Document"


if __name__ == "__main__":
    import unittest
    unittest.main()
