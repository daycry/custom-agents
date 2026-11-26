"""plugin-audit-2 T-42 fix1: la prosa del ciclo dice lo que hace la herramienta del roadmap.

Gap 2: el ledger lo cierra la Fase 6 (`roadmap-sync.py <carpeta> --cerrar`), no el veredicto de la Fase 3.
Gap 5: la puerta go/no-go de `/dev-cycle` usa `roadmap-sync.py gate`, igual que `/pm-cycle`.
Gap 12: la marca `· estado:` es la fuente del estado en el índice; la prosa del autor no se reescribe.
Gap 13: la fila del índice tiene un único dueño (`roadmap-sync.py`); evaluator y planner no la mantienen.
Gap 16: la arista `ledger-write.py` ↔ `roadmap-sync.py` está declarada en CONTRACTS con su Puerta.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def plain(rel):
    return " ".join((ROOT / rel).read_text(encoding="utf-8").split())


def test_t42_fix1_gap2_el_ledger_lo_cierra_la_fase_6():
    fase6 = plain("agent-kits/dev-cycle/references/phase6-close.md")
    paso6 = fase6[fase6.index("6. **Estados del plan"):][:900]
    assert "--cerrar" in paso6 and "qa" in paso6, paso6
    assert "ya llamó a `roadmap-sync.py`, que pasa `tasks.md` a `completado`" not in fase6
    for rel in ("docs/CONVENTIONS.md", "docs/en/CONVENTIONS.md"):
        text = plain(rel)
        assert "--cerrar" in text and "reabierta" in text, rel


def test_t42_fix1_gap5_la_puerta_go_de_dev_cycle_usa_la_herramienta():
    fase1 = plain("agent-kits/dev-cycle/references/phase1-evaluation.md")
    assert "roadmap-sync.py\" gate" in fase1 or "roadmap-sync.py gate" in fase1, fase1
    assert "--decision go" in fase1 and "no-go" in fase1
    core = plain("commands/dev-cycle.md")
    transiciones = core[core.index("## Transiciones de estado"):][:1200]
    assert "roadmap-sync.py gate" in transiciones and "--cerrar" in transiciones, transiciones
    evaluator = plain("agents/evaluator.md")
    assert "roadmap-sync.py gate" in evaluator
    assert "Cuando el usuario aprueba (go): spec → `aprobada` y evaluación → `completado`" not in evaluator


def test_t42_fix1_gap12_la_marca_es_la_fuente_del_indice():
    assert "la marca es la fuente" in plain("docs/CONVENTIONS.md").lower()
    assert "the marker is the source" in plain("docs/en/CONVENTIONS.md").lower()


def test_t42_fix1_gap13_un_solo_dueno_de_la_fila_del_indice():
    for rel in ("agents/evaluator.md", "agents/planner.md"):
        text = plain(rel)
        assert not re.search(r"[Mm]ant[eé]n (el índice )?`docs/roadmap/README\.md`", text), rel
        assert not re.search(r"Mantén el índice", text), rel
        assert "roadmap-sync" in text, rel
    for rel in ("docs/CONVENTIONS.md", "docs/en/CONVENTIONS.md"):
        text = plain(rel).replace("**", "")
        assert "roadmap-sync" in text and ("dueña única" in text or "single owner" in text), rel


def test_t42_fix1_gap16_arista_ledger_write_roadmap_sync_en_contracts():
    filas = [l for l in (ROOT / "docs/agents/CONTRACTS.md").read_text(encoding="utf-8").splitlines()
             if l.startswith("| E") and "roadmap-sync.py" in l and "ledger-write.py" in l]
    assert filas, "falta la arista"
    celdas = [c.strip() for c in filas[0].strip("|").split(" | ")]
    assert len(celdas) >= 9 and "test_roadmap_sync.py" in celdas[7], celdas
