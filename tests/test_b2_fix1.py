"""plugin-audit-2, fase 3, tanda B2 — fix1 de la revisión intento 1 (gaps 1, 2, 4, 5-8).

Cada test nombra su gap: `test_b2_fix1_gapN_…`.
"""
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / "agent-kits/shared"


def _lf(rel):
    return (ROOT / rel).read_text(encoding="utf-8").replace("\r\n", "\n")


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, SHARED / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---- gap 1: el gate de cobertura llega también al camino CON brief ----------------------------

def _proyecto(tmp_path, dev):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude/dev.json").write_text(json.dumps(dev), encoding="utf-8")
    folder = tmp_path / "docs/roadmap/fixture"
    folder.mkdir(parents=True)
    (folder / "tasks.md").write_text("""# Tasks
## Fase 1 — Fixture
### T-01 — Implement
- **Estado**: en-progreso
- **Verificación**: python verify.py → exit 0
**Criterios de aceptación**
- [ ] Keep this entire criterion.
""", encoding="utf-8")
    return folder


def _brief(folder):
    r = subprocess.run([sys.executable, str(SHARED / "task-brief.py"), str(folder), "T-01", "--sin-lint",
                        "--constitucion", str(folder / "absent.md"), "--extensions-project-only"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    assert r.returncode == 0, r.stderr
    return r.stdout


@pytest.mark.parametrize("dev", [
    {"subagentes": True, "tests": {"coberturaMinima": 80}},
    {"perfil": "lite", "tests": {"coberturaMinima": 80}},
], ids=["subagentes", "lite"])
def test_b2_fix1_gap1_el_brief_lleva_el_gate_de_cobertura(tmp_path, dev):
    out = _brief(_proyecto(tmp_path, dev))
    assert "## Cobertura" in out
    assert "coverage-gate.py" in out and "--changed-only --min 80" in out
    assert "exit 1" in out and "exit 2" in out
    if dev.get("perfil") == "lite":
        assert len(out) <= 6000


@pytest.mark.parametrize("dev", [{"subagentes": True}, {"subagentes": True, "tests": {"coberturaMinima": "80"}},
                                 {"subagentes": True, "tests": {"coberturaMinima": 130}}],
                         ids=["sin-clave", "texto", "fuera-de-rango"])
def test_b2_fix1_gap1_sin_umbral_valido_no_hay_gate_en_el_brief(tmp_path, dev):
    assert "coverage-gate.py" not in _brief(_proyecto(tmp_path, dev))


def test_b2_fix1_gap1_las_referencias_al_gate_dicen_la_verdad():
    cierre = _lf("agent-kits/dev-cycle/references/phase6-close.md")
    assert "P5 del implementer" not in cierre
    assert "classic-flow.md" in cierre and "«Cobertura» del brief" in cierre
    dc = _lf("commands/dev-cycle.md")
    assert "TDD, QA, cobertura y Knowledge Gate conservan todas sus puertas" not in dc
    assert "tests.coberturaMinima" in dc


# ---- gap 2: la condición del detalle de capability-check se evalúa con el núcleo ---------------

def test_b2_fix1_gap2_el_nucleo_nombra_la_comprobacion_de_piezas_propias(tmp_path):
    nucleo = _lf("agent-kits/shared/capability-check.md")
    m = re.search(r'python3 "\$SHAREDKIT/project-pieces\.py" ([^`\n]+)', nucleo)
    assert m, "el núcleo no nombra project-pieces.py"
    assert "capability-check-detail.md" in nucleo and "- **Extensiones**:" in nucleo
    assert len(nucleo.encode("utf-8")) <= 2048
    # Consumidor con una skill propia: la comprobación que nombra el núcleo la encuentra.
    (tmp_path / ".claude/skills/foo").mkdir(parents=True)
    (tmp_path / ".claude/skills/foo/SKILL.md").write_text(
        "---\nname: foo\ndescription: Skill foo del consumidor.\n---\nCuerpo\n", encoding="utf-8")
    args = m.group(1).replace("<raíz>", str(tmp_path)).replace("<runtime>", "claude-code").split()
    assert "--json" in args
    r = subprocess.run([sys.executable, str(SHARED / "project-pieces.py"), *args, "--project-only"],
                       capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr
    assert [p["name"] for p in json.loads(r.stdout)["pieces"]] == ["foo"]


# ---- gap 4: lista blanca de opciones de commit y la capa propia de --no-verify ------------------

GUARD = _load("b2_fix1_guard", "guardrail-check.py")
# Opciones largas de `git commit` (builtin/commit.c, git 2.53) que NO están en la lista blanca.
_COMMIT_FUERA = ("unified", "inter-hunk-context", "ahead-behind", "no-ahead-behind", "post-rewrite")


@pytest.mark.parametrize("orden", [
    "git commit --no-verify --verify -m x", "git commit --no-veri --veri -m x", "git commit -n --verify -m x",
    "git commit --mess --no-verify", "git commit --c --no-verify", "git commit --no-verify --no-no-veri -m x",
])
def test_b2_fix1_gap4_commit_restaura_hooks_y_abrevia_solo_en_la_lista_blanca(orden):
    assert GUARD.check_git(orden, None) is None, orden


@pytest.mark.parametrize("orden", [
    "git commit --no-verify -m x", "git commit -n -m x", "git commit --no-v -m x", "git commit --unif=3 -m x",
    "git commit --s -m x", "git commit --unknown", "git merge --no-verify main", "git rebase --update-r main",
])
def test_b2_fix1_gap4_lo_que_salta_hooks_o_no_es_unico_sigue_denegado(orden):
    assert GUARD.check_git(orden, "feature/x"), orden


def test_b2_fix1_gap4_ninguna_opcion_real_fuera_de_la_lista_es_prefijo_de_una_permitida():
    _sin, _con, _peg, largas, valor = GUARD._OPCIONES["commit"]
    for fuera in _COMMIT_FUERA:
        assert not any(w != fuera and w.startswith(fuera) for w in largas | valor), fuera


# ---- gaps 5-8: punteros que siguen al detalle y casos «sin brief» -------------------------------

def test_b2_fix1_gap5_work_context_apunta_al_detalle():
    wc = _lf("commands/work-context.md")
    assert "su sección de extensiones" not in wc
    assert "capability-check-detail.md" in wc


def test_b2_fix1_gap6_la_racionalizacion_no_remite_a_p3():
    imp = _lf("agents/implementer.md")
    tabla = imp.split("## Racionalizaciones que NO valen")[1].split("## ANTES DE CERRAR")[0]
    assert "(P3)" not in tabla


def test_b2_fix1_gap7_el_doc_no_cita_constitution_check_como_dependencia():
    doc = _lf("docs/agents/implementer.md")
    deps = doc.split("## Dependencias")[1].split("\n## ")[0]
    assert "constitution-check.md" not in deps


def test_b2_fix1_gap8_sin_brief_incluye_dev_cycle_con_subagentes_false():
    imp = _lf("agents/implementer.md")
    parrafo = next(p for p in imp.split("\n\n") if p.startswith("**Con brief o sin él.**"))
    assert "`subagentes: false`" in parrafo
    clasico = _lf("agent-kits/implementer/references/classic-flow.md").split("\n## ")[0]
    assert "`subagentes: false`" in clasico
    dc = _lf("commands/dev-cycle.md")
    assert "sigue el flujo clásico en el contexto principal" not in dc
    assert "classic-flow.md" in dc
