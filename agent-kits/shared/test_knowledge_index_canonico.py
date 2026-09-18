"""Tests de `knowledge-index.py` (knowledge-services T-02).

El índice opera SOLO sobre `docs/knowledge/approved/<folder>/` (y nunca sobre
`docs/knowledge/candidates/**`) para no tocar el corpus heredado de `docs/knowledge/{adr,gotchas,
lessons}` — ese árbol lo sigue gobernando el índice manual + `knowledge-lint.py` diferido de
ADR-006 (D4). `knowledge-index.py` es un validador NUEVO y distinto, dirigido por la taxonomía
configurada (`.claude/knowledge-services/taxonomy.json`), para el flujo de candidatos/aprobados de
`knowledge-services`. Decisión sin respaldo literal en spec/design más allá de "índice canónico
determinista sobre la taxonomía configurada" — señalada para revisión.
"""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _load():
    spec = importlib.util.spec_from_file_location("knowledge_index", os.path.join(HERE, "knowledge-index.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["knowledge_index"] = mod
    spec.loader.exec_module(mod)
    return mod


ki = _load()


def _taxonomy(root, categories):
    cfg = {
        "version": 1,
        "id_prefix": "ca",
        "categories": categories,
        "evidence_levels": ["observation", "single_case", "validated_case",
                             "multiple_validated_cases", "human_confirmed_rule"],
    }
    d = os.path.join(root, ".claude", "knowledge-services")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "taxonomy.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f)
    return cfg


def _entry(root, folder, filename, id_, version=1, enlaces=None, extra=""):
    d = os.path.join(root, "docs", "knowledge", "approved", folder)
    os.makedirs(d, exist_ok=True)
    fm = [f"id: {id_}"]
    if version is not None:
        fm.append(f"version: {version}")
    if enlaces:
        fm.append("enlaces: [" + ", ".join(enlaces) + "]")
    contenido = "---\n" + "\n".join(fm) + "\n---\n\n# " + id_ + "\n\n" + extra + "\n"
    with open(os.path.join(d, filename), "w", encoding="utf-8") as f:
        f.write(contenido)


def _cat(key="DECISION", folder="adr", min_evidence="human_confirmed_rule"):
    return [{"key": key, "folder": folder, "min_evidence": min_evidence}]


# ------------------------------------------------------------------ básico

def test_indice_vacio_sin_entradas(tmp_path):
    root = str(tmp_path)
    _taxonomy(root, _cat())
    indice, errores = ki.build_index(root)
    assert indice == {}
    assert errores == []


def test_una_entrada_valida(tmp_path):
    root = str(tmp_path)
    _taxonomy(root, _cat())
    _entry(root, "adr", "ADR-001.md", "ADR-001")
    indice, errores = ki.build_index(root)
    assert errores == []
    assert "ADR-001" in indice
    assert indice["ADR-001"]["folder"] == "adr"


def test_id_duplicado_falla_con_ruta_y_campo(tmp_path):
    root = str(tmp_path)
    _taxonomy(root, _cat())
    _entry(root, "adr", "ADR-001.md", "ADR-001")
    _entry(root, "adr", "ADR-001-bis.md", "ADR-001")
    indice, errores = ki.build_index(root)
    assert any(e["campo"] == "id" and "duplicad" in e["mensaje"] for e in errores)
    assert all(e.get("fichero") for e in errores)


def test_version_faltante_falla(tmp_path):
    root = str(tmp_path)
    _taxonomy(root, _cat())
    _entry(root, "adr", "ADR-002.md", "ADR-002", version=None)
    indice, errores = ki.build_index(root)
    assert any(e["campo"] == "version" for e in errores)


def test_enlace_roto_falla(tmp_path):
    root = str(tmp_path)
    _taxonomy(root, _cat())
    _entry(root, "adr", "ADR-003.md", "ADR-003", enlaces=["GOT-999"])
    indice, errores = ki.build_index(root)
    assert any(e["campo"] == "enlaces" and "GOT-999" in e["mensaje"] for e in errores)


def test_enlace_valido_no_falla(tmp_path):
    root = str(tmp_path)
    cats = _cat() + [{"key": "GOTCHA", "folder": "gotchas", "min_evidence": "validated_case"}]
    _taxonomy(root, cats)
    _entry(root, "gotchas", "GOT-001.md", "GOT-001")
    _entry(root, "adr", "ADR-004.md", "ADR-004", enlaces=["GOT-001"])
    indice, errores = ki.build_index(root)
    assert errores == []


def test_candidatos_no_aparecen_en_el_indice(tmp_path):
    root = str(tmp_path)
    _taxonomy(root, _cat())
    _entry(root, "adr", "ADR-005.md", "ADR-005")
    d = os.path.join(root, "docs", "knowledge", "candidates", "pending")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "CAND-001.md"), "w", encoding="utf-8") as f:
        f.write("---\nid: CAND-001\nversion: 1\n---\n\n# candidato\n")
    indice, errores = ki.build_index(root)
    assert "CAND-001" not in indice
    assert "ADR-005" in indice


def test_readme_de_carpeta_se_ignora(tmp_path):
    root = str(tmp_path)
    _taxonomy(root, _cat())
    d = os.path.join(root, "docs", "knowledge", "approved", "adr")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "README.md"), "w", encoding="utf-8") as f:
        f.write("# no es una entrada\n")
    indice, errores = ki.build_index(root)
    assert indice == {}
    assert errores == []


def test_taxonomia_invalida_no_construye_indice(tmp_path):
    root = str(tmp_path)
    d = os.path.join(root, ".claude", "knowledge-services")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "taxonomy.json"), "w", encoding="utf-8") as f:
        json.dump({"categories": []}, f)  # falta version, categories vacía
    indice, errores = ki.build_index(root)
    assert indice == {}
    assert errores


# ------------------------------------------------------------------ dos proyectos, dos taxonomías

def test_dos_taxonomias_distintas_dan_carpetas_distintas_a(tmp_path):
    root_a = os.path.join(str(tmp_path), "proyecto_a")
    os.makedirs(root_a, exist_ok=True)
    _taxonomy(root_a, [{"key": "DECISION", "folder": "adr", "min_evidence": "human_confirmed_rule"}])
    _entry(root_a, "adr", "ADR-010.md", "ADR-010")
    indice_a, errores_a = ki.build_index(root_a)
    assert errores_a == []
    assert set(e["folder"] for e in indice_a.values()) == {"adr"}


def test_dos_taxonomias_distintas_dan_carpetas_distintas_b(tmp_path):
    root_b = os.path.join(str(tmp_path), "proyecto_b")
    os.makedirs(root_b, exist_ok=True)
    _taxonomy(root_b, [{"key": "RUNBOOK", "folder": "runbooks", "min_evidence": "observation"}])
    _entry(root_b, "runbooks", "RUN-001.md", "RUN-001")
    indice_b, errores_b = ki.build_index(root_b)
    assert errores_b == []
    assert set(e["folder"] for e in indice_b.values()) == {"runbooks"}


# ------------------------------------------------------------------ CLI

def test_cli_exit_0_sin_errores(tmp_path, capsys):
    root = str(tmp_path)
    _taxonomy(root, _cat())
    _entry(root, "adr", "ADR-020.md", "ADR-020")
    assert ki.main(["--root", root]) == 0


def test_cli_exit_1_con_errores(tmp_path, capsys):
    root = str(tmp_path)
    _taxonomy(root, _cat())
    _entry(root, "adr", "ADR-021.md", "ADR-021", enlaces=["NOPE-1"])
    assert ki.main(["--root", root]) == 1
