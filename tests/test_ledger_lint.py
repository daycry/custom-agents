#!/usr/bin/env python3
"""Tests de ledger-lint.py (validación del ledger tasks.md). Ejecuta: python tests/test_ledger_lint.py"""
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "agent-kits", "shared", "ledger-lint.py")

BASE = """# Checklist de Tareas — demo

> **⚠️ Ledger canónico de progreso.** Fuente única de verdad.

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|------|------------|-------|----------|
| Fase 1 — Uno | {f1done} | {f1total} | x% |

## Fase 1 — Uno

### T-01 — Tarea uno

- **Estado**: {t1estado}

**Criterios de aceptación**
- [{t1c1}] criterio uno
- [{t1c2}] criterio dos

### T-02 — Tarea dos

- **Estado**: {t2estado}

**Criterios de aceptación**
- [{t2c1}] criterio uno
"""


def run(text, warn_only=False):
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "tasks.md")
        open(p, "w", encoding="utf-8").write(text)
        cmd = [sys.executable, SCRIPT, p] + (["--warn-only"] if warn_only else [])
        r = subprocess.run(cmd, capture_output=True, text=True)
        return r.returncode, r.stdout


def doc(**kw):
    d = dict(f1done=1, f1total=2, t1estado="completado", t1c1="x", t1c2="x",
             t2estado="en-progreso", t2c1=" ")
    d.update(kw)
    return BASE.format(**d)


def main():
    # 1) coherente → exit 0
    code, out = run(doc())
    assert code == 0, out

    # 2) estado inválido → exit 1
    code, out = run(doc(t2estado="haciendose"))
    assert code == 1 and "estado inválido" in out, out

    # 3) completado con criterios sin marcar → exit 1
    code, out = run(doc(t1c2=" "))
    assert code == 1 and "incoherencia dura" in out, out

    # 4) resumen descuadrado → exit 1
    code, out = run(doc(f1done=2))
    assert code == 1 and "descuadrado" in out, out

    # 5) ID duplicado → exit 1
    dup = doc().replace("### T-02 — Tarea dos", "### T-01 — Tarea dos")
    code, out = run(dup)
    assert code == 1 and "duplicado" in out, out

    # 6) legacy sin resumen ni banner → solo avisos, exit 0
    legacy = "## Fase 1 — Uno\n\n### T-01 — t\n\n- **Estado**: borrador\n\n**Criterios de aceptación**\n- [ ] c\n"
    code, out = run(legacy)
    assert code == 0 and "⚠️" in out, out

    # 7) --warn-only: incoherencia dura NO rompe (modo hook) → exit 0
    code, out = run(doc(t1c2=" "), warn_only=True)
    assert code == 0 and "incoherencia dura" in out, out

    # 8) estados con emoji/decoración se normalizan → exit 0
    code, out = run(doc(t2estado="en-progreso 🚧"))
    assert code == 0, out

    # 9) «Fase 3» y «Fase 3-bis» NO colisionan en el resumen (regresión sdd-hardening)
    bis = """# Tareas

| | |
|---|---|
| **Estado** | en-progreso |

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|------|------------|-------|----------|
| Fase 3 — Nucleo | 2 | 2 | 100% |
| Fase 3-bis — Extra | 1 | 1 | 100% |
| **TOTAL** | **3** | **3** | **100%** |

## Fase 3 — Nucleo

### T-01 — a

- **Estado**: completado

**Criterios de aceptación**
- [x] ok

### T-02 — b

- **Estado**: completado

**Criterios de aceptación**
- [x] ok

## Fase 3-bis — Extra

### T-03 — c

- **Estado**: completado

**Criterios de aceptación**
- [x] ok
"""
    code, out = run(bis)
    assert code == 0 and "descuadrado" not in out, f"colisión Fase 3 / 3-bis: {out}"

    # 10) numeración multinivel: «Fase 3.2» y «Fase 3.2.1» tampoco colisionan
    multi = bis.replace("Fase 3 —", "Fase 3.2 —").replace("Fase 3-bis —", "Fase 3.2.1 —")
    code, out = run(multi)
    assert code == 0 and "descuadrado" not in out, f"colisión Fase 3.2 / 3.2.1: {out}"

    print("test_ledger_lint: 10/10 OK")


if __name__ == "__main__":
    main()
