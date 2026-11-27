"""plugin-audit-2 T-42 fix2 (revisión intento 2): la prosa y el panel dicen lo que hace la herramienta.

Gap 2 (d): en la Fase 6 el ledger se cierra ANTES del merge/PR y el paso 9 dice la verdad.
Gap 2 (e): el criterio 2 de T-42 cita los tipos reales que cubre su test.
Gap 6: ninguna pieza instruye a escribir el índice `docs/roadmap/README.md` salvo `roadmap-sync.py`.
Gap 7: FLOWS (ES/EN) muestra `gate` en `/dev-cycle` y el cierre del ledger antes de `changelog-sync`.
Gap 9: el panel cuenta las tareas con el parser canónico ligero (mismos estados que `parse_ledger`).
Gap 10: una tarea nueva en `borrador` o reabierta reabre el ledger, y la doc lo dice.
"""
import importlib.util
from pathlib import Path
import re

import pytest

ROOT = Path(__file__).resolve().parents[1]


def plain(rel):
    return " ".join((ROOT / rel).read_text(encoding="utf-8").split())


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_t42_fix2_gap2_el_ledger_se_cierra_antes_del_merge_y_el_paso_9_dice_la_verdad():
    fase6 = plain("agent-kits/dev-cycle/references/phase6-close.md")
    cierre = fase6.index("**Estados del plan")
    assert cierre < fase6.index("**Resumen de merge/PR") < fase6.index("**Integración según el flujo del repo**")
    assert fase6.index("--cerrar") < fase6.index("**Integración según el flujo del repo**")
    paso9 = fase6[fase6.index("9. **Cierre declarado**"):][:700]
    assert "retro-gate.py --sync" in paso9 and "ledger" in paso9, paso9
    paso8 = fase6[fase6.index("8. **Retro"):fase6.index("9. **Cierre declarado**")]
    assert "tareas abiertas" in paso8, paso8


def test_t42_fix2_gap2_criterio_2_cita_los_tipos_que_cubre_el_test():
    ledger = (ROOT / "docs/roadmap/2026-11-10-plugin-audit-2/tasks.md").read_text(encoding="utf-8")
    bloque = ledger[ledger.index("### T-42 "):]
    bloque = bloque[:bloque.index("\n## ")]
    criterio = next(l for l in bloque.splitlines() if l.startswith("- [") and "`--check`" in l)
    for tipo in ("rancio", "reabiert", "cierre olvidado", "plan", "spec", "índice"):
        assert tipo in criterio, (tipo, criterio)
    # scope-check: un criterio aprobado no se reescribe, se amplía detrás; la enmienda dice los tipos reales.
    assert "Enmendado en fix2 por la revisión intento 2: los tipos reales son" in criterio
    test = (ROOT / "agent-kits/shared/test_roadmap_sync.py").read_text(encoding="utf-8")
    assert "def test_t42_fix2_gap2_check_cubre_los_tipos_del_criterio_2" in test


ESCRIBE_INDICE = re.compile(r"(?i)\b(registr\w*|actualiz\w*|añad\w*|escrib\w*|mant[eé]n\w*|edit\w*|crea\w*|"
                            r"rellen\w*)\b")
PIEZAS = ("agents/evaluator.md", "agents/planner.md", "agents/analyst.md", "skills/dependency-upgrade/SKILL.md",
          "docs/agents/evaluator.md", "docs/agents/planner.md", "docs/agents/analyst.md")


@pytest.mark.parametrize("rel", PIEZAS)
def test_t42_fix2_gap6_ninguna_pieza_escribe_el_indice_salvo_roadmap_sync(rel):
    """Cualquier frase que hable del índice del roadmap con un verbo de escritura nombra a `roadmap-sync.py`
    como quien la escribe (no solo «Mantén»: «regístrala en», «actualiza», «escribes … su fila»)."""
    malas = _frases_que_escriben_el_indice((ROOT / rel).read_text(encoding="utf-8"))
    assert not malas, malas


def test_t42_fix2_gap6_puerta_de_tokens_del_evaluator():
    assert len((ROOT / "agents/evaluator.md").read_bytes().replace(b"\r\n", b"\n")) <= 15513


@pytest.mark.parametrize("rel", ("docs/FLOWS.md", "docs/en/FLOWS.md"))
def test_t42_fix2_gap7_flows_muestra_gate_y_el_cierre_del_ledger(rel):
    text = (ROOT / rel).read_text(encoding="utf-8")
    bloque = text[text.index('A["/dev-cycle'):]
    bloque = bloque[:bloque.index("```")]
    assert "roadmap-sync.py gate" in bloque, rel
    assert "--cerrar" in bloque and bloque.index("--cerrar") < bloque.index("changelog-sync"), rel
    assert "retro-gate.py --sync" in bloque, rel


def test_t42_fix2_gap9_el_panel_cuenta_con_el_parser_canonico_ligero(monkeypatch):
    lint = _load("t42_fix2_lint", "agent-kits/shared/ledger-lint.py")
    ledgers = sorted((ROOT / "docs/roadmap").glob("*/tasks.md"))
    assert ledgers
    for path in ledgers:
        text = path.read_text(encoding="utf-8", errors="replace")
        assert lint.estados_tareas(text) == [t["estado"] for t in lint.parse_ledger(text)["tareas"]], path.name
    bd = _load("t42_fix2_dashboard", "skills/roadmap-dashboard/scripts/build_dashboard.py")

    def prohibido(*a, **k):
        raise AssertionError("contar_tareas no debe usar el parse_ledger completo")

    assert bd._ESTADOS_TAREAS is not None
    monkeypatch.setitem(bd._ESTADOS_TAREAS.__globals__, "parse_ledger", prohibido)
    texto = "## Fase 1\n\n### T-01 — a\n\n- **Estado**: completado\n\n### T-02 — b\n\n- **Estado**: en-progreso\n"
    assert bd.contar_tareas(texto) == {"completadas": 1, "total": 2, "abiertas": 1, "iniciadas": 2}
    rs = (ROOT / "agent-kits/shared/roadmap-sync.py").read_text(encoding="utf-8")
    assert "estados_tareas" in rs


def test_t42_fix2_gap10_la_doc_dice_que_una_tarea_nueva_reabre_el_ledger():
    assert "tarea nueva" in plain("agent-kits/dev-cycle/references/phase6-close.md")
    assert "tarea nueva" in plain("docs/CONVENTIONS.md") and "borrador" in plain("docs/CONVENTIONS.md")
    assert "new task" in plain("docs/en/CONVENTIONS.md")


# ---------------------------------------------------------------- fix3 (revisión intento 3, ciclo 2)

def _frases_que_escriben_el_indice(texto):
    """Frases que mandan escribir el índice del roadmap sin nombrar a `roadmap-sync.py` (detector del gap 6)."""
    malas = []
    for linea in texto.splitlines():
        for frase in re.split(r"(?<=[.;])\s+", linea):
            indice = "docs/roadmap/README.md" in frase or re.search(r"(?i)índice|README\.md", frase)
            if indice and "roadmap/" in linea + frase and ESCRIBE_INDICE.search(frase) \
                    and "roadmap-sync" not in frase:
                malas.append(frase.strip())
    return malas


MUTANTES_GAP9 = {
    "skills/dependency-upgrade/SKILL.md": ("su fila en el índice del roadmap la escribe `roadmap-sync.py`",
                                           ["regístrala en el índice del roadmap", "mantén su fila en el índice del roadmap",
                                            "edita su fila en el índice del roadmap",
                                            "su fila en el índice del roadmap la mantiene el evaluator"]),
    "docs/agents/evaluator.md": ("Su fila del índice `docs/roadmap/README.md` la escribe `roadmap-sync.py` (dueño único).",
                                 ["Mantén su fila en el índice del roadmap.", "Registra la iniciativa en el índice del roadmap.",
                                  "Edita su fila de `docs/roadmap/README.md`.",
                                  "Su fila del índice `docs/roadmap/README.md` la mantiene el evaluator (dueño único)."]),
}


@pytest.mark.parametrize("rel", sorted(MUTANTES_GAP9))
def test_t42_fix3_gap9_el_detector_del_duenyo_unico_cubre_estas_lineas(rel):
    """Gap 9: `skills/dependency-upgrade/SKILL.md:70` y `docs/agents/evaluator.md:12` hoy pasan; cualquier frase
    que mande mantener/editar/registrar el índice (o el «índice del roadmap») sin nombrar a `roadmap-sync.py` falla."""
    original, mutantes = MUTANTES_GAP9[rel]
    texto = (ROOT / rel).read_text(encoding="utf-8")
    assert original in texto, rel
    assert not _frases_que_escriben_el_indice(texto), rel
    for mutante in mutantes:
        assert _frases_que_escriben_el_indice(texto.replace(original, mutante)), (rel, mutante)


@pytest.mark.parametrize("rel,texto", (("docs/FLOWS.md", "ledger no verificable"), ("docs/en/FLOWS.md", "unverifiable ledger")))
def test_t42_fix3_gap10_flows_exit_1_de_retro_gate_sync(rel, texto):
    """Gap 10: el exit 1 de `retro-gate --sync` también son tareas abiertas o un ledger no verificable: no cierra."""
    bloque = (ROOT / rel).read_text(encoding="utf-8")
    linea = next(l for l in bloque.splitlines() if 'RG -.->|"exit 1"|' in l)
    assert texto in linea and ("no cierra" in linea or "no closeout" in linea), linea
    assert "ledger completado" not in linea, linea
