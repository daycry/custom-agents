"""Tests de las plantillas del case store (training-data-services T-03).

Las plantillas de `assets/` no son prosa suelta: el ejemplo completo (`assets/case-store-example/`)
debe validar con el MISMO `case_schema.py` que usara el recorder, seguir la estructura de
`design.md` (`cases/<family>.<variant>/v<NNN>/...`) y tener un `cases_index.jsonl` coherente con
los `metadata.json`/`validation.json` de cada version.
"""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, "..", "assets"))
EJEMPLO = os.path.join(ASSETS, "case-store-example")

FICHEROS_VERSION = ("metadata.json", "request.json", "context.json", "constraints.json",
                    "trajectory.jsonl", "metrics.json", "validation.json")
CLAVES_INDICE = {"case_id", "version", "family", "variant", "status", "outcome", "updated_at"}


def _load():
    spec = importlib.util.spec_from_file_location("case_schema_assets", os.path.join(HERE, "case_schema.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["case_schema_assets"] = mod
    spec.loader.exec_module(mod)
    return mod


cs = _load()


def _json(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def _jsonl(ruta):
    with open(ruta, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def _versiones():
    base = os.path.join(EJEMPLO, "cases")
    for caso in sorted(os.listdir(base)):
        for v in sorted(os.listdir(os.path.join(base, caso))):
            yield caso, v, os.path.join(base, caso, v)


def _componer(dir_version):
    """Reune los ficheros de una version en el dict que valida `case_schema.validar_caso`."""
    meta = _json(os.path.join(dir_version, "metadata.json"))
    caso = dict(meta)
    caso["request"] = _json(os.path.join(dir_version, "request.json"))["request"]
    caso["context"] = _json(os.path.join(dir_version, "context.json"))
    caso["constraints"] = _json(os.path.join(dir_version, "constraints.json"))
    caso["trajectory"] = _jsonl(os.path.join(dir_version, "trajectory.jsonl"))
    caso["metrics"] = _json(os.path.join(dir_version, "metrics.json"))
    caso["validation"] = _json(os.path.join(dir_version, "validation.json"))
    arts = os.path.join(dir_version, "final", "artifacts.json")
    if os.path.isfile(arts):
        caso["artifacts"] = _json(arts)
    return caso


def test_training_example_valida():
    cfg = _json(os.path.join(ASSETS, "training.example.json"))
    assert cs.validar_config(cfg) == []
    assert cfg["enabled"] is True and cfg["root"] and cfg["id_prefix"]


def test_readme_de_plantillas_documenta_cada_fichero():
    with open(os.path.join(ASSETS, "README.md"), encoding="utf-8") as f:
        texto = f.read()
    for nombre in FICHEROS_VERSION + ("cases_index.jsonl", "final/artifacts.json", "exports/", "training.json"):
        assert nombre in texto, nombre


def test_estructura_sigue_design_md():
    cfg = _json(os.path.join(ASSETS, "training.example.json"))
    width = cfg.get("ids", {}).get("version_width", 3)
    vistos = list(_versiones())
    assert len(vistos) >= 2
    for caso, v, d in vistos:
        meta = _json(os.path.join(d, "metadata.json"))
        esperado = cs.directorio_version(meta["family"], meta["variant"], meta["version"], width)
        assert os.path.normpath(os.path.join("cases", caso, v)) == os.path.normpath(esperado)
        for nombre in FICHEROS_VERSION:
            assert os.path.isfile(os.path.join(d, nombre)), (d, nombre)


def test_cada_version_del_ejemplo_valida_con_el_esquema():
    cfg = _json(os.path.join(ASSETS, "training.example.json"))
    for _caso, _v, d in _versiones():
        assert cs.validar_caso(_componer(d), cfg) == [], d


def test_ejemplo_incluye_par_fallo_correccion_y_gold_humano():
    casos = [_componer(d) for _c, _v, d in _versiones()]
    fallo = next(c for c in casos if c["outcome"] == "failure")
    corregido = next(c for c in casos if c["outcome"] == "corrected")
    assert corregido["supersedes_case"] == cs.referencia_version(fallo["case_id"], fallo["version"])
    assert corregido["validation"] == {**corregido["validation"], "status": "approved", "approved_by_human": True}
    assert fallo["validation"]["status"] == "rejected"   # el rechazado se conserva, no se borra


def test_indice_coherente_con_las_versiones():
    indice = _jsonl(os.path.join(EJEMPLO, "cases_index.jsonl"))
    assert indice
    por_clave = {}
    for fila in indice:
        assert set(fila) == CLAVES_INDICE, fila
        por_clave[(fila["case_id"], fila["version"])] = fila   # append-only: gana la ultima
    for _c, _v, d in _versiones():
        meta = _json(os.path.join(d, "metadata.json"))
        val = _json(os.path.join(d, "validation.json"))
        fila = por_clave[(meta["case_id"], meta["version"])]
        assert (fila["family"], fila["variant"], fila["outcome"]) == (meta["family"], meta["variant"], meta["outcome"])
        assert fila["status"] == val["status"]


def test_ejemplo_sin_binarios_inline():
    for raiz, _dirs, ficheros in os.walk(EJEMPLO):
        for nombre in ficheros:
            assert nombre.endswith((".json", ".jsonl", ".md")), os.path.join(raiz, nombre)


# ------------------------------------------------------------------ fix1 (revision intento 1, Fase 2)

def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


SKILL_MD = os.path.join(HERE, "..", "SKILL.md")


def test_f2fix1_gap47_skill_documenta_las_dos_vias_a_gold_y_config():
    """E3 (gap #47): las dos vias a Gold (misma puerta), `--config`, y consulta/cache en su paso."""
    s = _leer(SKILL_MD)
    assert "record <caso.json> --approved-by-human" in s and "set-status <case_id>" in s
    assert "--config <training.json>" in s
    assert "5. **Consultar**" in s and "4. **Aprobar Gold**" in s


def test_f2fix1_gap48_skill_dice_que_version_es_opcional_en_record():
    s = _leer(SKILL_MD)
    assert "Para `record`, `version`" in s and "siguiente versión libre" in s


def test_f2fix1_gap49_readme_lista_el_bloqueo_y_todos_los_redactados():
    r = _leer(os.path.join(ASSETS, "README.md"))
    assert ".cases_index.lock" in r and ".cases_index.lock" in _leer(SKILL_MD)
    tramo = r[r.index("Todo el texto libre"):]
    for f in ("constraints.json", "metrics.json", "final/artifacts.json", "reviewer_note", "created_at"):
        assert f in tramo, f
