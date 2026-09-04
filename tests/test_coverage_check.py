#!/usr/bin/env python3
"""Tests de coverage-check.py (puerta criterios↔tests de qa), incl. criterios [GWT].

Ejecuta:  python3 tests/test_coverage_check.py   (sale 0 si todo pasa, 1 si algo falla)
"""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "agent-kits", "qa", "coverage-check.py")

TASKS_OK = """# Tareas
### T-01 — cosa de UI
- **Cubre (tests)**: E2E-01
### T-02 — cosa sin UI
- **Cubre (tests)**: —
"""
PLAN_OK = """# Test plan
## E2E-01 — flujo feliz
Pasos… (cubre CA-01)
"""
SPEC_GWT = """---
spec: x
---
## Criterios de aceptación
- [ ] criterio libre de proceso
- [ ] [GWT] CA-01 — Dado un usuario logueado, Cuando pulsa guardar, Entonces ve el toast
- [x] [GWT] CA-02 — Dado un carrito vacío, Cuando añade un ítem, Entonces el contador marca 1
- [ ] [GWT] Dado algo sin ID, Cuando pasa, Entonces avisa
"""


def run(tasks, plan, spec=None):
    d = tempfile.mkdtemp()
    tp = os.path.join(d, "tasks.md")
    open(tp, "w", encoding="utf-8").write(tasks)
    args = [sys.executable, SCRIPT, tp]
    pp = os.path.join(d, "test-plan.md")
    if plan is not None:
        open(pp, "w", encoding="utf-8").write(plan)
    args.append(pp)
    if spec is not None:
        sp = os.path.join(d, "spec.md")
        open(sp, "w", encoding="utf-8").write(spec)
        args.append(sp)
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    last = r.stdout.strip().splitlines()[-1]
    return r.returncode, json.loads(last), r.stdout


def eq(got, exp, msg):
    assert got == exp, f"{msg}: esperado {exp!r}, obtenido {got!r}"


def main():
    # regresión: comportamiento existente sin spec
    rc, js, _ = run(TASKS_OK, PLAN_OK)
    eq(rc, 0, "caso base verde")
    eq(js["broken_refs"], 0, "sin referencias rotas")
    assert "T-02" in js["tasks_sin_cobertura"], "T-02 sin cobertura es aviso"

    rc, js, _ = run(TASKS_OK.replace("E2E-01", "E2E-99"), PLAN_OK)
    eq(rc, 1, "referencia rota → exit 1")

    rc, js, _ = run(TASKS_OK, None)
    eq(rc, 0, "sin test-plan y sin spec GWT → no aplica, exit 0")
    eq(js.get("applies"), False, "no aplica")

    # [GWT] cubierto: CA-01 aparece en el plan; CA-02 no → error
    rc, js, out = run(TASKS_OK, PLAN_OK, SPEC_GWT)
    eq(rc, 1, "GWT sin cubrir → exit 1")
    eq(js["gwt_cubiertos"], ["CA-01"], "CA-01 cubierto (mención en el plan)")
    eq(js["gwt_sin_cubrir"], ["CA-02"], "CA-02 sin cubrir")
    eq(js["gwt_sin_id"], 1, "un GWT sin ID es aviso")
    assert "CA-02" in out and "❌" in out, "el error de CA-02 se imprime"

    # todos los GWT cubiertos → verde
    plan2 = PLAN_OK + "\n## E2E-02 — contador\nCubre CA-02\n"
    rc, js, _ = run(TASKS_OK, plan2, SPEC_GWT)
    eq(rc, 0, "todos los GWT cubiertos → exit 0")
    eq(js["gwt_sin_cubrir"], [], "nada sin cubrir")

    # GWT presentes pero SIN test-plan → los GWT prometen test: exit 1
    rc, js, _ = run(TASKS_OK, None, SPEC_GWT)
    eq(rc, 1, "GWT sin test-plan → exit 1")
    eq(sorted(js["gwt_sin_cubrir"]), ["CA-01", "CA-02"], "ambos sin cubrir")

    # spec sin criterios GWT → idéntico al comportamiento base
    rc, js, _ = run(TASKS_OK, PLAN_OK, "---\nspec: y\n---\n- [ ] criterio libre\n")
    eq(rc, 0, "spec sin GWT no cambia el resultado")
    eq(js["gwt_cubiertos"], [], "sin GWT")

    # --- robustez (revisión lente B) ---
    # ID en negrita, [gwt] minúsculas y viñeta *: los tres deben detectarse CON id
    spec_variantes = """---
spec: v
---
- [ ] [GWT] **CA-01** — Dado a, Cuando b, Entonces c
- [X] [gwt] CA-02 — Dado d, Cuando e, Entonces f
* [ ] [GWT] CA-03 — Dado g, Cuando h, Entonces i
"""
    plan_v = "## E2E-01\ncubre CA-01 y CA-02 y CA-03\n"
    rc, js, _ = run(TASKS_OK, plan_v, spec_variantes)
    eq(rc, 0, "variantes de formato GWT cubiertas → verde")
    eq(sorted(js["gwt_cubiertos"]), ["CA-01", "CA-02", "CA-03"],
       "negrita/minúsculas/asterisco detectados con ID")
    eq(js["gwt_sin_id"], 0, "ninguno cae a sin-id por el formato")

    # un ejemplo [GWT] dentro de un bloque de código NO cuenta como criterio real
    spec_fence = ("---\nspec: f\n---\nFormato:\n\n```markdown\n"
                  "- [ ] [GWT] CA-77 — Dado ejemplo, Cuando doc, Entonces nada\n```\n"
                  "- [ ] criterio libre real\n")
    rc, js, _ = run(TASKS_OK, PLAN_OK, spec_fence)
    eq(rc, 0, "GWT en bloque de código no dispara la puerta")
    eq(js["gwt_cubiertos"] + js["gwt_sin_cubrir"], [], "CA-77 de ejemplo ignorado")

    # todos los GWT sin ID + sin test-plan → exit 0 pero CON aviso visible
    spec_sinid = "---\nspec: s\n---\n- [ ] [GWT] Dado a, Cuando b, Entonces c\n"
    rc, js, out = run(TASKS_OK, None, spec_sinid)
    eq(rc, 0, "GWT sin ID y sin test-plan no rompe")
    assert "no son rastreables" in out, "el aviso de GWT sin ID sin test-plan se imprime"
    eq(js["gwt_sin_id"], 1, "el JSON refleja los sin-id")

    print("OK: coverage-check con criterios [GWT] — todo pasa.")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"FALLO: {e}", file=sys.stderr)
        sys.exit(1)
