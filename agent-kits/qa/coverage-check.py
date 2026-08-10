#!/usr/bin/env python3
"""
coverage-check.py — puerta de COBERTURA criterios↔tests del agente qa.

Cruza el ledger `tasks.md` (campo «Cubre (tests)» de cada tarea) con el
`test-plan.md` (bloques E2E-xx / M-xx / API-xx / A11Y-xx) y detecta:

ERRORES (exit 1):
  - Referencias rotas: una tarea declara «Cubre (tests): E2E-03» pero ese
    bloque no existe en el test-plan.
AVISOS (informativos; qa los triagea — las tareas sin UI no necesitan cobertura):
  - Tareas sin cobertura declarada (campo vacío o «—»).
  - Bloques del test-plan que ninguna tarea referencia (posible test huérfano).

Salida: informe por stdout (para el report.md de qa) + resumen JSON final.
Uso:
  python3 coverage-check.py <tasks.md> <test-plan.md>
Si el test-plan no existe: exit 0 con aviso (iniciativa sin UI; la puerta no aplica).
"""
import json
import os
import re
import sys

TEST_ID = re.compile(r"\b((?:E2E|M|API|A11Y)-\d+)\b", re.I)


def main():
    if len(sys.argv) != 3:
        print("uso: coverage-check.py <tasks.md> <test-plan.md>")
        sys.exit(1)
    tasks_path, plan_path = sys.argv[1], sys.argv[2]

    if not os.path.isfile(tasks_path):
        print(f"❌ no existe {tasks_path}")
        sys.exit(1)
    if not os.path.isfile(plan_path):
        print("⚠️  sin test-plan.md: la puerta de cobertura no aplica (iniciativa sin UI)")
        print(json.dumps({"applies": False}))
        sys.exit(0)

    plan = open(plan_path, encoding="utf-8").read()
    defined = set()
    for m in re.finditer(r"^#{2,4}\s*.*?\b((?:E2E|M|API|A11Y)-\d+)\b", plan, re.M | re.I):
        defined.add(m.group(1).upper())
    # también acepta "**E2E-01**", primera celda de tabla "| E2E-01 |" y listas "- E2E-01"
    for m in re.finditer(r"\*\*((?:E2E|M|API|A11Y)-\d+)\*\*", plan, re.I):
        defined.add(m.group(1).upper())
    for m in re.finditer(r"^\|\s*((?:E2E|M|API|A11Y)-\d+)\s*\|", plan, re.M | re.I):
        defined.add(m.group(1).upper())
    for m in re.finditer(r"^\s*[-*]\s*((?:E2E|M|API|A11Y)-\d+)\b", plan, re.M | re.I):
        defined.add(m.group(1).upper())

    tasks = open(tasks_path, encoding="utf-8").read()
    task_re = re.compile(r"^###\s+(T-\d+)[^\n]*", re.M)
    cubre_re = re.compile(r"^\s*-\s*\*\*Cubre \(tests\)\*\*\s*:\s*(.*)$", re.M)

    # trocear por tarea
    positions = [(m.start(), m.group(1)) for m in task_re.finditer(tasks)]
    errors, sin_cobertura, referenced = [], [], set()
    if not positions:
        print("❌ no se han detectado tareas `### T-XX` en tasks.md — la puerta no puede validar cobertura")
        print(json.dumps({"applies": True, "broken_refs": 0, "no_tasks": True}))
        sys.exit(1)
    for i, (pos, tid) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else len(tasks)
        chunk = tasks[pos:end]
        m = cubre_re.search(chunk)
        if not m:
            sin_cobertura.append(tid)
            continue
        val = m.group(1).strip()
        ids = [i.upper() for i in TEST_ID.findall(val)]
        if not ids:
            sin_cobertura.append(tid)
            continue
        for t in ids:
            referenced.add(t)
            if t not in defined:
                errors.append(f"{tid}: referencia rota — «{t}» no existe en el test-plan")

    unreferenced = sorted(defined - referenced)

    for tid in sin_cobertura:
        print(f"⚠️  {tid}: sin cobertura declarada (si es tarea de UI, es un criterio huérfano → NO verde)")
    for t in unreferenced:
        print(f"⚠️  {t}: ningún «Cubre (tests)» lo referencia (¿test huérfano?)")
    for e in errors:
        print(f"❌ {e}")

    print(json.dumps({
        "applies": True,
        "defined": sorted(defined),
        "referenced": sorted(referenced),
        "broken_refs": len(errors),
        "tasks_sin_cobertura": sin_cobertura,
        "tests_sin_referencia": unreferenced,
    }, ensure_ascii=False))
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
