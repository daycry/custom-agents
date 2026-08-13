#!/usr/bin/env python3
"""
ledger-lint.py — validación MECÁNICA del ledger canónico `tasks.md`
(agent-kits/shared: lo invocan implementer (DoD), qa (P1), /dev-cycle (puertas)
y el hook PostToolUse en modo aviso).

ERRORES (exit 1, incoherencias duras):
  - Estado inválido (vocabulario: borrador · en-progreso · en-revision ·
    completado · cancelado).
  - IDs de tarea `T-XX` duplicados.
  - Tarea `completado` con criterios de aceptación sin marcar (`- [ ]`).
  - Tabla de resumen que no cuadra con las tareas (completadas/total por fase).

AVISOS (no rompen; formato/legacy):
  - Falta el banner de ledger canónico.
  - Falta la tabla «Resumen de progreso».
  - Tarea sin campo Estado o sin bloque de criterios.

Uso:
  python3 ledger-lint.py <ruta/a/tasks.md> [--warn-only]
  --warn-only: imprime todo como aviso y SIEMPRE exit 0 (modo hook).
"""
import argparse
import os
import re
import sys

ESTADOS = {"borrador", "en-progreso", "en-revision", "completado", "cancelado"}
# quita emojis/decoración al comparar estados: "completado ✅" → "completado"
def norm_estado(s):
    s = re.sub(r"[\s_]+", "-", s.strip().lower())   # "En Progreso" → "en-progreso"
    return re.sub(r"[^a-z\-]", "", s).strip("-")    # "en-progreso 🚧" → "en-progreso"


def lint(path):
    errors, warnings = [], []
    try:
        text = open(path, encoding="utf-8").read()
    except UnicodeDecodeError:
        text = open(path, encoding="utf-8", errors="replace").read()
        warnings.append("el fichero no es UTF-8 limpio (leído con reemplazos)")
    lines = text.splitlines()

    if "edger canónico" not in text and "edger can" not in text:
        warnings.append("falta el banner de «ledger canónico» (formato legacy)")

    # ---- estructura: fases y tareas ----
    fase_re = re.compile(r"^##\s+(Fase\s+\d+[^\n]*)")
    task_re = re.compile(r"^###\s+(T-\d+)\b")
    estado_re = re.compile(r"^\s*-\s*\*\*Estado\*\*\s*:\s*(.+)$")
    check_re = re.compile(r"^\s*[-*]\s*\[( |x|X)\]")

    fases = []          # [(nombre, [tareas])]
    cur_fase = None
    cur_task = None
    seen_ids = set()

    def close_task():
        nonlocal cur_task
        if cur_task is not None:
            (cur_fase[1] if cur_fase else orphan_tasks).append(cur_task)
            cur_task = None

    orphan_tasks = []
    in_criterios = False
    for ln in lines:
        m = fase_re.match(ln)
        if m:
            close_task()
            cur_fase = (m.group(1).strip(), [])
            fases.append(cur_fase)
            continue
        if re.match(r"^##\s", ln) and not fase_re.match(ln):
            # sección de nivel 2 que no es una fase (Apéndice, Notas...) → cierra la fase
            close_task()
            cur_fase = None
            continue
        m = task_re.match(ln)
        if m:
            close_task()
            tid = m.group(1)
            if tid in seen_ids:
                errors.append(f"ID de tarea duplicado: {tid}")
            seen_ids.add(tid)
            cur_task = {"id": tid, "estado": None, "unchecked": 0, "checked": 0,
                        "tiene_criterios": False}
            in_criterios = False
            continue
        if cur_task is not None:
            m = estado_re.match(ln)
            if m and cur_task["estado"] is None:
                cur_task["estado"] = norm_estado(m.group(1))
                continue
            if re.match(r"^(\*\*|#{3,5}\s*)Criterios de aceptación", ln.strip()):
                in_criterios = True
                cur_task["tiene_criterios"] = True
                continue
            if in_criterios:
                mc = check_re.match(ln)
                if mc:
                    if mc.group(1) in ("x", "X"):
                        cur_task["checked"] += 1
                    else:
                        cur_task["unchecked"] += 1
                elif ln.strip() and not ln.startswith((" ", "\t")) \
                        and not ln.strip().startswith(("-", "*")):
                    # párrafo/encabezado de nivel superior → fin del bloque de criterios
                    in_criterios = False
    close_task()

    all_tasks = [t for _, ts in fases for t in ts] + orphan_tasks
    if not all_tasks:
        warnings.append("no se han detectado tareas `### T-XX` (¿formato distinto?)")

    for t in all_tasks:
        if t["estado"] is None:
            warnings.append(f"{t['id']}: sin campo **Estado** (legacy)")
        elif t["estado"] not in ESTADOS:
            errors.append(f"{t['id']}: estado inválido «{t['estado']}» "
                          f"(vocabulario: {' · '.join(sorted(ESTADOS))})")
        if not t["tiene_criterios"]:
            warnings.append(f"{t['id']}: sin bloque de criterios de aceptación")
        if t["estado"] == "completado" and t["unchecked"] > 0:
            errors.append(f"{t['id']}: marcado `completado` con {t['unchecked']} "
                          f"criterio(s) sin marcar `- [ ]` — incoherencia dura")

    # ---- tabla de resumen (completadas/total por fase) ----
    resumen_rows = re.findall(
        r"^\|\s*\*{0,2}\s*(Fase\s+\d+[^|*]*)\*{0,2}\s*\|\s*\*{0,2}(\d+)\*{0,2}\*?\s*\|\s*\*{0,2}(\d+)\*{0,2}\s*\|", text, re.M)
    if not resumen_rows:
        warnings.append("sin tabla «Resumen de progreso» reconocible (legacy)")
    else:
        real = {}
        for nombre, ts in fases:
            key = norm_fase(nombre)
            done = sum(1 for t in ts if t["estado"] == "completado")
            real[key] = (done, len(ts))
        for nombre, comp, total in resumen_rows:
            key = norm_fase(nombre)
            if key not in real:
                warnings.append(f"resumen: fila «{nombre.strip()}» sin sección de fase que le corresponda")
                continue
            rdone, rtotal = real[key]
            if int(total) != rtotal or int(comp) != rdone:
                errors.append(
                    f"resumen descuadrado en «{nombre.strip()}»: tabla dice "
                    f"{comp}/{total}, las tareas dicen {rdone}/{rtotal}")
    return errors, warnings


def norm_fase(s):
    # captura sufijos ("Fase 3-bis") para que no colisionen con "Fase 3"
    m = re.match(r"\s*Fase\s+(\d+(?:[.-]\w+)*)", s)
    return f"fase-{m.group(1).lower()}" if m else s.strip().lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tasks", help="ruta a tasks.md")
    ap.add_argument("--warn-only", action="store_true",
                    help="modo hook: todo como aviso, siempre exit 0")
    args = ap.parse_args()

    if not os.path.isfile(args.tasks):
        print(f"⚠️  ledger-lint: no existe {args.tasks}")
        sys.exit(0 if args.warn_only else 1)

    errors, warnings = lint(args.tasks)
    for w in warnings:
        print(f"⚠️  {w}")
    prefix = "⚠️ " if args.warn_only else "❌"
    for e in errors:
        print(f"{prefix} {e}")
    print(f"ledger-lint: {len(errors)} incoherencias · {len(warnings)} avisos "
          f"({os.path.basename(args.tasks)})")
    sys.exit(0 if (args.warn_only or not errors) else 1)


if __name__ == "__main__":
    main()
