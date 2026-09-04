#!/usr/bin/env python3
"""
coverage-check.py — puerta de COBERTURA criterios↔tests del agente qa.

Cruza el ledger `tasks.md` (campo «Cubre (tests)» de cada tarea) con el
`test-plan.md` (bloques E2E-xx / M-xx / API-xx / A11Y-xx) y detecta:

ERRORES (exit 1):
  - Referencias rotas: una tarea declara «Cubre (tests): E2E-03» pero ese
    bloque no existe en el test-plan.
  - Criterios [GWT] sin cubrir (con <spec.md>): un criterio Given/When/Then
    `- [ ] [GWT] CA-XX — …` de la spec promete comportamiento testeable; si su
    ID CA-XX no aparece en el test-plan, es cobertura que FALTA (no opcional).
AVISOS (informativos; qa los triagea — las tareas sin UI no necesitan cobertura):
  - Tareas sin cobertura declarada (campo vacío o «—»).
  - Bloques del test-plan que ninguna tarea referencia (posible test huérfano).
  - Criterios [GWT] sin ID CA-XX (sin ID no hay trazabilidad; añádelo).

Salida: informe por stdout (para el report.md de qa) + resumen JSON final.
Uso:
  python3 coverage-check.py <tasks.md> <test-plan.md> [spec.md]
Si el test-plan no existe: exit 0 con aviso (iniciativa sin UI; la puerta no
aplica) — SALVO que la spec traiga criterios [GWT]: esos prometen test, así
que sin test-plan cuentan como sin cubrir (exit 1).
"""
import json
import os
import re
import sys

# Consola Windows (cp1252) o tuberías: reconfigurar ANTES de leer o imprimir nada (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

TEST_ID = re.compile(r"\b((?:E2E|M|API|A11Y)-\d+)\b", re.I)
# criterio G/W/T de la spec: "- [ ] [GWT] CA-01 — Dado…" — tolerante: viñeta -/*,
# checkbox marcado o no, [GWT] en cualquier caja, ID opcionalmente en **negrita**
GWT_RE = re.compile(
    r"^\s*[-*]\s*\[[ xX]\]\s*\[GWT\]\s*(?:\*\*)?(CA-\d+)?(?:\*\*)?", re.M | re.I)


def _sin_fences(text):
    """Quita bloques de código cercados (```/~~~): un ejemplo de criterio [GWT]
    dentro de documentación no debe contar como criterio real."""
    out, en_fence = [], False
    for ln in text.splitlines():
        if re.match(r"^\s*(```|~~~)", ln):
            en_fence = not en_fence
            continue
        if not en_fence:
            out.append(ln)
    return "\n".join(out)


def gwt_criteria(spec_path):
    """(ids CA-XX de criterios [GWT], nº de [GWT] sin ID) de la spec; ([], 0) si no hay."""
    if not spec_path or not os.path.isfile(spec_path):
        return [], 0
    text = _sin_fences(open(spec_path, encoding="utf-8", errors="replace").read())
    ids, sin_id = [], 0
    for m in GWT_RE.finditer(text):
        if m.group(1):
            ids.append(m.group(1).upper())
        else:
            sin_id += 1
    return ids, sin_id


def main():
    if len(sys.argv) not in (3, 4):
        print("uso: coverage-check.py <tasks.md> <test-plan.md> [spec.md]")
        sys.exit(1)
    tasks_path, plan_path = sys.argv[1], sys.argv[2]
    spec_path = sys.argv[3] if len(sys.argv) == 4 else None
    gwt_ids, gwt_sin_id = gwt_criteria(spec_path)

    if not os.path.isfile(tasks_path):
        print(f"❌ no existe {tasks_path}")
        sys.exit(1)
    if not os.path.isfile(plan_path):
        if gwt_ids:
            # los [GWT] prometen test: sin test-plan, son cobertura que falta
            for cid in gwt_ids:
                print(f"❌ {cid}: criterio [GWT] de la spec sin test-plan que lo cubra")
            print(json.dumps({"applies": True, "broken_refs": 0,
                              "tasks_sin_cobertura": [], "tests_sin_referencia": [],
                              "gwt_cubiertos": [], "gwt_sin_cubrir": gwt_ids,
                              "gwt_sin_id": gwt_sin_id}, ensure_ascii=False))
            sys.exit(1)
        if gwt_sin_id:
            # prometen test pero sin ID no se pueden rastrear: avisar, no silenciar
            print(f"⚠️  {gwt_sin_id} criterio(s) [GWT] sin ID CA-XX en la spec y sin "
                  "test-plan: prometen test pero no son rastreables (añade IDs y test-plan)")
        print("⚠️  sin test-plan.md: la puerta de cobertura no aplica (iniciativa sin UI)")
        print(json.dumps({"applies": False, "gwt_sin_id": gwt_sin_id}))
        sys.exit(0)

    plan = open(plan_path, encoding="utf-8", errors="replace").read()
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

    tasks = open(tasks_path, encoding="utf-8", errors="replace").read()
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

    # criterios [GWT] de la spec: su CA-XX debe aparecer en el test-plan (cualquier forma:
    # encabezado, **CA-01**, celda de tabla, lista o mención plana — prometen test 1:1)
    gwt_sin_cubrir = [cid for cid in gwt_ids
                      if not re.search(rf"\b{cid}\b", plan, re.I)]
    gwt_cubiertos = [cid for cid in gwt_ids if cid not in gwt_sin_cubrir]

    for tid in sin_cobertura:
        print(f"⚠️  {tid}: sin cobertura declarada (si es tarea de UI, es un criterio huérfano → NO verde)")
    for t in unreferenced:
        print(f"⚠️  {t}: ningún «Cubre (tests)» lo referencia (¿test huérfano?)")
    if gwt_sin_id:
        print(f"⚠️  {gwt_sin_id} criterio(s) [GWT] sin ID CA-XX en la spec (sin ID no hay trazabilidad)")
    for cid in gwt_sin_cubrir:
        print(f"❌ {cid}: criterio [GWT] de la spec sin aparición en el test-plan (cobertura que falta)")
    for e in errors:
        print(f"❌ {e}")

    print(json.dumps({
        "applies": True,
        "defined": sorted(defined),
        "referenced": sorted(referenced),
        "broken_refs": len(errors),
        "tasks_sin_cobertura": sin_cobertura,
        "tests_sin_referencia": unreferenced,
        "gwt_cubiertos": gwt_cubiertos,
        "gwt_sin_cubrir": gwt_sin_cubrir,
        "gwt_sin_id": gwt_sin_id,
    }, ensure_ascii=False))
    sys.exit(1 if (errors or gwt_sin_cubrir) else 0)


if __name__ == "__main__":
    main()
