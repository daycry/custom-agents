"""Integracion T-03 (knowledge-services): estructura de `docs/knowledge/candidates|approved/`,
ownership documentado y export de backends no versionado. Complementa (no repite) los tests
unitarios de `agent-kits/shared/test_knowledge_index.py` (T-02): aqui se valida el ARBOL REAL del
repo, no fixtures en `tmp_path`.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARED = os.path.join(ROOT, "agent-kits", "shared")


def _load_knowledge_index():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "knowledge_index", os.path.join(SHARED, "knowledge-index.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["knowledge_index"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_candidates_y_approved_existen_con_ownership():
    candidatos = os.path.join(ROOT, "docs", "knowledge", "candidates", "README.md")
    aprobados = os.path.join(ROOT, "docs", "knowledge", "approved", "README.md")
    assert os.path.isfile(candidatos)
    assert os.path.isfile(aprobados)
    for ruta in (candidatos, aprobados):
        with open(ruta, "r", encoding="utf-8") as f:
            texto = f.read()
        assert "knowledge-curator" in texto


def test_subcarpetas_de_candidatos_presentes():
    base = os.path.join(ROOT, "docs", "knowledge", "candidates")
    for sub in ("pending", "needs_changes", "rejected"):
        assert os.path.isdir(os.path.join(base, sub)), f"falta docs/knowledge/candidates/{sub}"


def test_sin_arbol_projects_en_docs_knowledge():
    base = os.path.join(ROOT, "docs", "knowledge")
    for nombre in os.listdir(base):
        assert nombre != "projects", "docs/knowledge/projects/ no debe existir (sin control-plane multi-proyecto, ADR-018)"


def test_indice_real_del_repo_sin_derivados_y_sin_errores():
    """El árbol real del repo (sin `taxonomy.json` de proyecto: usa la plantilla por defecto)
    construye un índice sin errores; `approved/` está vacío en el propio plugin (el flujo de
    curación empieza en T-04) y eso es válido, no un fallo."""
    ki = _load_knowledge_index()
    indice, errores = ki.build_index(ROOT)
    assert errores == []
    assert isinstance(indice, dict)


def test_gitignore_declara_export_de_backends_no_versionado():
    with open(os.path.join(ROOT, ".gitignore"), "r", encoding="utf-8") as f:
        texto = f.read()
    assert ".claude/knowledge-services/kwipu-export/" in texto
    assert ".claude/knowledge-services/*-export/" in texto


def test_git_check_ignore_cubre_export_derivado():
    """Un export derivado bajo `.claude/knowledge-services/<algo>-export/` queda ignorado por
    git (fuentes e índice coherentes sin derivados: el derivado nunca compite con la fuente)."""
    resultado = subprocess.run(
        ["git", "check-ignore", "-q", ".claude/knowledge-services/kwipu-export/manifest.json"],
        cwd=ROOT)
    assert resultado.returncode == 0
