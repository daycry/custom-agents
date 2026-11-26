"""Panel del roadmap con datos vivos (plugin-audit-2 T-42).

`_scan_fase` deriva la fase de los ESTADOS y del progreso del ledger, no de los ficheros presentes, y
`_scan_leer_eval` lee coste y esfuerzo con las etiquetas reales que escribe el `evaluator`.
Ejecutar: python -m pytest -q tests/test_dashboard_estado.py
"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "skills", "roadmap-dashboard", "scripts"))

import build_dashboard as bd  # noqa: E402


def _ledger(estado, estados):
    tareas = "".join(f"### T-0{i} — t{i}\n\n- **Estado**: {e}\n\n" for i, e in enumerate(estados, 1))
    return f"---\nestado: {estado}\n---\n\n# Ledger\n\n## Fase 1 — Única\n\n{tareas}"


def _iniciativa(tmp_path, nombre="2026-01-01-demo", **ficheros):
    carpeta = tmp_path / nombre
    carpeta.mkdir()
    nombres = {"spec": "spec.md", "evaluation": "evaluation.md", "plan": "improvement-plan.md", "tasks": "tasks.md"}
    for clave, texto in ficheros.items():
        (carpeta / nombres[clave]).write_text(texto, encoding="utf-8")
    (carpeta / "testing").mkdir()   # su presencia ya no decide la fase («en pruebas» era falso)
    return bd.scan(str(tmp_path))[0]


SPEC = "---\nspec: demo\nestado: aprobada\n---\n\n# Demo\n"
EVAL = "---\nevaluacion: demo\nestado: completado\n---\n\n# Eval\n"
PLAN = "---\nplan: demo\nestado: borrador\n---\n\n# Plan\n"


@pytest.mark.parametrize("ficheros, fase", [
    ({"spec": SPEC, "evaluation": EVAL, "plan": PLAN,
      "tasks": _ledger("completado", ("completado", "cancelado"))}, "completada"),
    ({"spec": SPEC, "evaluation": EVAL, "plan": PLAN,
      "tasks": _ledger("en-progreso", ("completado", "en-progreso", "cancelado"))}, "en curso 1/2"),
    ({"spec": SPEC, "evaluation": EVAL, "plan": PLAN, "tasks": _ledger("borrador", ("borrador",))}, "planificada"),
    ({"spec": SPEC, "evaluation": EVAL, "plan": PLAN}, "planificada"),
    ({"spec": SPEC, "evaluation": EVAL}, "evaluada"),
    ({"spec": SPEC}, "solo spec"),
    ({"tasks": _ledger("borrador", ("borrador",))}, "vía rápida"),
    ({"tasks": _ledger("en-progreso", ("completado", "en-progreso"))}, "en curso 1/2"),
    ({"spec": SPEC, "evaluation": EVAL.replace("completado", "cancelado")}, "cancelada"),
])
def test_fase_derivada_de_estados_y_progreso(tmp_path, ficheros, fase):
    assert _iniciativa(tmp_path, **ficheros)["fase"] == fase


def test_ledger_al_100_es_completada_aunque_su_estado_vaya_rancio(tmp_path):
    rec = _iniciativa(tmp_path, spec=SPEC, tasks=_ledger("en-progreso", ("completado", "completado")))
    assert rec["fase"] == "completada"


EVAL_TABLA = """---
evaluacion: demo
estado: completado
---

# Evaluación

| Métrica | Total estimado | Confianza |
|---|---|---|
| {esfuerzo} | **134,4 h** (112 h base +20 %) | Baja |
| Tiempo IA (ejecución) | **50,7 h** | Baja |
| {coste} | **7.075 €** | Media |
"""


@pytest.mark.parametrize("esfuerzo, coste", [
    ("Esfuerzo humano (referencia)", "Coste"),                                   # panel-redesign
    ("Esfuerzo humano", "Coste (presupuesto humano + tokens)"),                  # plugin-optimization
    ("Esfuerzo humano equivalente", "Coste de referencia (humano equivalente + tokens + proceso)"),  # kairos
])
def test_etiquetas_reales_del_evaluator(tmp_path, esfuerzo, coste):
    rec = _iniciativa(tmp_path, spec=SPEC, evaluation=EVAL_TABLA.format(esfuerzo=esfuerzo, coste=coste))
    assert "134,4 h" in rec["esfuerzo"] and "7.075 €" in rec["coste"]
    assert not [w for w in bd.warnings_for([rec]) if "no se leyeron" in w]


def test_estimacion_en_prosa(tmp_path):
    ev = ("---\nevaluation: demo\nestado: completado\n---\n\n# Evaluacion\n\n**Go.** Estimacion: "
          "**50h humanas (42h base +20%)**, 15h IA; coste humano de referencia: **2,500 EUR** a 50 EUR/h.\n")
    rec = _iniciativa(tmp_path, spec=SPEC, evaluation=ev)
    assert rec["esfuerzo"] == "50h humanas" and rec["coste"] == "2,500 EUR"


def test_presupuesto_no_solicitado_se_declara_y_no_avisa(tmp_path):
    ev = ("---\nevaluacion: demo\nestado: completado\n---\n\n# Evaluación técnica\n\n"
          "Go por autorización. No se solicitó presupuesto; no se estima un coste sin deltas.\n")
    rec = _iniciativa(tmp_path, spec=SPEC, evaluation=ev)
    assert rec["coste"] == "no estimado" and rec["esfuerzo"] == "no estimado"
    assert not [w for w in bd.warnings_for([rec]) if "no se leyeron" in w]


def test_roadmap_real_sin_avisos_de_etiquetas():
    inits = bd.scan(os.path.join(ROOT, "docs", "roadmap"))
    assert not [w for w in bd.warnings_for(inits) if "no se leyeron" in w]
