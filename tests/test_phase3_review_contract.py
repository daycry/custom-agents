"""Contratos de prosa de la tanda A de plugin-audit-2."""

import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
ROADMAP = "docs/roadmap/2026-11-10-plugin-audit-2"
PROMPTS = "skills/adversarial-review/references/lens-prompts.md"


def _read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def _literal_lente_a():
    return next(line for line in _read(PROMPTS).splitlines() if line.startswith("- **Lente A —"))


def test_intento1_gap1_lente_a_y_reviewer_piden_la_vista_de_fase():
    prompt = _literal_lente_a()
    reviewer = " ".join(_read("agents/reviewer.md").split())
    for texto in (prompt, reviewer):
        assert "`task-brief.py <carpeta> --fase N`" in texto
        assert "y `tasks.md`" not in texto
    assert "Abre `tasks.md` solo para citar una línea concreta." in prompt
    assert "solo abre `tasks.md` para citar una línea concreta." in reviewer


@pytest.mark.parametrize("path,claude,otros", [
    ("docs/FLOWS.md", "cabecera de piezas en Claude Code", "índice completo en Codex y OpenCode"),
    ("docs/en/FLOWS.md", "catalog header in Claude Code", "full index in Codex and OpenCode"),
])
def test_intento1_gap9_flujos_documentan_el_indice_por_runtime(path, claude, otros):
    flecha = next(line for line in _read(path).splitlines() if 'H3 -->|"additionalContext:' in line)
    assert claude in flecha and otros in flecha


@pytest.mark.parametrize("path,inicio", [
    ("agent-kits/shared/README.md", "| `task-brief.py`"),
    ("docs/agents/CONTRACTS.md", "| E8 ·"),
])
def test_intento1_gap9_contratos_documentan_la_vista_de_fase(path, inicio):
    fila = next(line for line in _read(path).splitlines() if line.startswith(inicio))
    assert "--fase N" in fila and "Lente A" in fila


def test_intento1_gap8_m_c_incluye_evals_reales_de_activacion():
    fila = next(line for line in _read(f"{ROADMAP}/improvement-plan.md").splitlines()
                if line.startswith("| M-C |"))
    assert "T-20" in fila and "`python evals/run.py`" in fila and "línea base" in fila


def test_fix2_gap7_modo_sin_plan_sustituye_el_texto_vigente_de_lente_a():
    modo = next(line for line in _read(PROMPTS).splitlines() if "*Modo sin plan:*" in line)
    original, reemplazo = re.findall(r"«([^»]*)»", modo)[:2]
    assert original in _literal_lente_a()
    assert "`task-brief.py <carpeta> --fase N`" in original
    assert "<objetivo>" in reemplazo and "`<base>..HEAD`" in reemplazo
    assert "desde el ledger" not in reemplazo and "--fase" not in reemplazo
    assert "(5) y (5b) no aplican sin ledger" in modo


def test_fix2_gap9_changelogs_bilingues_en_changed_y_trazados_por_tarea():
    en = _read("CHANGELOG.md").split("## [Unreleased]\n", 1)[1].split("\n## ", 1)[0]
    es = _read("CHANGELOG.es.md").split("## [Sin publicar]\n", 1)[1].split("\n## ", 1)[0]
    ledger = _read(f"{ROADMAP}/tasks.md")
    traducciones = {
        "12": "Each task brief includes the essential TDD rule, so the subagent no longer loads the whole skill.",
        "13": "The reviewer reads only the lens table it needs, without loading the full adversarial review skill.",
        "14": "Ledgers warn before they grow too large, can be archived by phase, and reviews read only the current phase.",
        "20": "Claude Code startup no longer repeats the skill listing. Codex and OpenCode keep it.",
        "21": "Codex and OpenCode commands that do not dispatch agents no longer include the orchestration header.",
    }
    for tid, traduccion in traducciones.items():
        tarea = ledger.split(f"### T-{tid} —", 1)[1].split("\n### ", 1)[0]
        fuente = next(line.removeprefix("- **Changelog**: ") for line in tarea.splitlines()
                      if line.startswith("- **Changelog**: "))
        archivos = next(line for line in tarea.splitlines() if line.startswith("- **Archivos**:"))
        assert "`CHANGELOG.md`" in archivos and "`CHANGELOG.es.md`" in archivos
        for bloque, texto in [(en, traduccion), (es, fuente)]:
            changed = bloque.split("### Changed\n", 1)[1].split("\n### ", 1)[0]
            assert changed.splitlines().count(f"- {texto}") == 1
            assert bloque.splitlines().count(f"- {texto}") == 1
    assert "changelog-sync" in ledger.split("### T-14 —", 1)[1].split("\n### ", 1)[0]
