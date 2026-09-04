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
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
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

    # 11) «Fase única — …» (vía rápida) se reconoce en el resumen: sin aviso legacy, y su descuadre
    #     es ERROR (antes la fila no casaba con `Fase\s+\d+` y disparaba el aviso falso)
    unica = bis.replace("Fase 3 — Nucleo | 2 | 2", "Fase única — Todo | 3 | 3") \
               .replace("| Fase 3-bis — Extra | 1 | 1 | 100% |\n", "") \
               .replace("## Fase 3 — Nucleo", "## Fase única — Todo") \
               .replace("## Fase 3-bis — Extra\n", "")
    code, out = run(unica)
    assert code == 0 and "Resumen de progreso" not in out, f"aviso legacy falso con Fase única: {out}"
    code, out = run(unica.replace("Fase única — Todo | 3 | 3", "Fase única — Todo | 2 | 3"))
    assert code == 1 and "descuadrado" in out, f"descuadre en Fase única debe ser error: {out}"

    # 12) [plan-and-diet T-02] frontmatter `verificacion: obligatoria` + tarea sin `Verificación` → ERROR (exit 1)
    fm_obl = "---\ntasks: demo\nverificacion: obligatoria   # comentario\n---\n"
    con_verif_t1 = doc().replace("- **Estado**: completado\n",
                                 "- **Estado**: completado\n- **Verificación**: `pytest -q` → passed\n", 1)
    code, out = run(fm_obl + con_verif_t1)
    assert code == 1 and "T-02: sin campo **Verificación** (el ledger declara verificacion: obligatoria)" in out, out
    assert "T-01: sin campo" not in out, out
    # la variante `- **Verificación** (ejecutada …): …` también cuenta como campo presente
    ejecutada = con_verif_t1.replace("- **Verificación**: `pytest -q` → passed",
                                     "- **Verificación** (ejecutada 2026-09-03 — passed): `pytest -q` → passed")
    code, out = run(fm_obl + ejecutada)
    assert code == 1 and "T-01: sin campo" not in out and "T-02: sin campo" in out, out

    # 13) mismo ledger SIN la clave → adopción parcial: solo AVISO (exit 0); y sin la clave y sin ningún
    #     `Verificación` (los 20 ledgers previos) → NI aviso: salida idéntica a la versión anterior
    code, out = run(con_verif_t1)
    assert code == 0 and "⚠️  T-02: sin campo **Verificación** (otras tareas lo declaran)" in out, out
    code, out = run(doc())
    assert code == 0 and "Verificación" not in out, out
    code, out = run("---\nverificacion: recomendada\n---\n" + doc())     # clave con otro valor → aviso sin «otras»
    assert code == 0 and "⚠️  T-01: sin campo **Verificación**\n" in out and "otras tareas" not in out, out

    # 14) con la clave y TODAS las tareas con el campo → exit 0 sin aviso de Verificación
    todas = con_verif_t1.replace("- **Estado**: en-progreso\n",
                                 "- **Estado**: en-progreso\n- **Verificación**: lectura: la doc dice X\n", 1)
    code, out = run(fm_obl + todas)
    assert code == 0 and "Verificación" not in out, out

    # 15) [T-fix1, gap Important #1] sub-lista bajo el campo → cuenta como Verificación (los ítems indentados
    #     se consumen y NO se confunden con criterios); campo VACÍO (sin texto ni sub-lista) → error distinto
    #     de «sin campo»; variante `(ejecutada … — salida: …): cmd` → el paréntesis no rompe el parseo
    sublista = doc().replace("- **Estado**: completado\n",
                             "- **Estado**: completado\n- **Verificación**:\n  - `pytest -q` → passed\n  - `lint` → 0 errores\n", 1)
    sublista = sublista.replace("- **Estado**: en-progreso\n",
                                "- **Estado**: en-progreso\n- **Verificación** (ejecutada 2026-09-03 — salida: `ok: 3`): `make check` → `ok: 3`\n", 1)
    code, out = run(fm_obl + sublista)
    assert code == 0 and "Verificación" not in out, out
    vacio = doc().replace("- **Estado**: completado\n", "- **Estado**: completado\n- **Verificación**:\n", 1) \
                 .replace("- **Estado**: en-progreso\n", "- **Estado**: en-progreso\n- **Verificación**: `x` → y\n", 1)
    code, out = run(fm_obl + vacio)
    assert code == 1 and "T-01: campo **Verificación** VACÍO" in out and "T-01: sin campo" not in out, out
    # el parser importable expone ítems y paréntesis por separado
    import importlib.util
    spec = importlib.util.spec_from_file_location("ledger_lint", SCRIPT)
    ll = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ll)
    tareas = {x["id"]: x for x in ll.parse_ledger(fm_obl + sublista)["tareas"]}
    assert tareas["T-01"]["verificacion_items"] == ["`pytest -q` → passed", "`lint` → 0 errores"], tareas["T-01"]
    assert tareas["T-01"]["checked"] == 2, "la sub-lista no se come los criterios"
    assert tareas["T-02"]["verificacion_items"] == ["`make check` → `ok: 3`"], tareas["T-02"]
    assert tareas["T-02"]["verificacion_ejecutada"] == "ejecutada 2026-09-03 — salida: `ok: 3`"
    inline = ll.parse_verificacion(["- **Verificación**: `a` → 1 · `b` → 2"], 0)[0]
    assert inline["items"] == ["`a` → 1", "`b` → 2"] and inline["ejecutada"] is None

    # 16) campo `Changelog:` — OPCIONAL por diseño: nunca es incoherencia, y un ledger que no lo
    #     usa en NINGUNA tarea no recibe aviso (los 13 ledgers cerrados previos —63 tareas—
    #     validan idéntico).
    code, out = run(doc())
    assert code == 0 and "Changelog" not in out, out
    #     adopción PARCIAL (una tarea lo trae y la otra no) → AVISO, exit 0
    parcial = doc().replace("- **Estado**: completado\n",
                            "- **Estado**: completado\n- **Changelog**: Arregla el arranque sin config.\n", 1)
    code, out = run(parcial)
    assert code == 0, out
    assert "⚠️" in out and "T-02: sin campo **Changelog**" in out, out
    assert "T-01" not in out.split("ledger-lint:")[0], out
    #     campo presente pero VACÍO → aviso, nunca error
    vacio_cl = doc().replace("- **Estado**: completado\n",
                             "- **Estado**: completado\n- **Changelog**:\n", 1)
    code, out = run(vacio_cl)
    assert code == 0 and "T-01: campo **Changelog** VACÍO" in out, out
    #     el parser lo expone
    tareas = {x["id"]: x for x in ll.parse_ledger(parcial)["tareas"]}
    assert tareas["T-01"]["changelog"] == "Arregla el arranque sin config."
    assert tareas["T-02"]["changelog"] is None

    # 17) `--warn-only` (modo hook) con el campo: exit 0 y el aviso sigue saliendo. Faltaba el
    #     caso, y el criterio T-03#3 promete «ni con --warn-only ni sin él».
    code, out = run(parcial, warn_only=True)
    assert code == 0 and "T-02: sin campo **Changelog**" in out, out
    assert "❌" not in out, out
    code, out = run(vacio_cl, warn_only=True)
    assert code == 0 and "T-01: campo **Changelog** VACÍO" in out and "❌" not in out, out

    # 18) placeholder `{{…}}` de plantilla sin sustituir: no es un resumen escrito (changelog-sync
    #     lo IGNORA y degrada al título), así que se avisa en vez de darlo por bueno.
    ph = doc().replace(
        "- **Estado**: completado\n",
        "- **Estado**: completado\n- **Changelog**: {{qué cambia para quien USA el proyecto}}\n", 1)
    code, out = run(ph)
    assert code == 0 and "T-01: campo **Changelog** sin sustituir" in out, out
    assert "T-02: sin campo **Changelog**" not in out, "con placeholder no hay adopción parcial"
    code, out = run(ph, warn_only=True)
    assert code == 0 and "placeholder" in out and "❌" not in out, out

    # 18-bis) …pero un `{{…}}` CITADO es texto humano: el criterio es «el campo ES el placeholder»,
    #     no «lo menciona». Antes se descartaban los dos casos de abajo (pérdida silenciosa de
    #     texto escrito a mano) y el aviso diagnosticaba «placeholder sin sustituir».
    for escrito in ("Ahora la plantilla del planner trae `{{qué cambia para quien USA el "
                    "proyecto}}` en vez del párrafo largo.",
                    "El generador acepta {{slug}} y {{fecha}} en el nombre de la sección."):
        cita = doc().replace("- **Estado**: completado\n",
                             f"- **Estado**: completado\n- **Changelog**: {escrito}\n", 1)
        code, out = run(cita)
        assert code == 0 and "sin sustituir" not in out, (escrito, out)
        tareas = {x["id"]: x for x in ll.parse_ledger(cita)["tareas"]}
        assert tareas["T-01"]["changelog"] == escrito, tareas["T-01"]
        assert not ll.es_placeholder(escrito), escrito
    for plantilla in ("{{qué cambia para quien USA el proyecto, en una frase}}",
                      "{{OPCIONAL, lo rellena quien CIERRA la tarea: una frase}}",
                      "  {{sin sustituir}}  "):
        assert ll.es_placeholder(plantilla), plantilla

    # 19) continuación INDENTADA del campo: una persona parte la frase en dos líneas y el Markdown
    #     la lee como un párrafo. Se absorbe (no se pierde en silencio) y no se come los criterios.
    multi = doc().replace(
        "- **Estado**: completado\n",
        "- **Estado**: completado\n- **Changelog**: El script deja de reventar sin config\n"
        "  y aplica los defaults documentados.\n", 1)
    code, out = run(multi)
    assert code == 0, out
    tareas = {x["id"]: x for x in ll.parse_ledger(multi)["tareas"]}
    assert tareas["T-01"]["changelog"] == \
        "El script deja de reventar sin config y aplica los defaults documentados.", tareas["T-01"]
    assert tareas["T-01"]["checked"] == 2, "la continuación no se come los criterios"

    # 20) el patrón del campo es la FUENTE ÚNICA que replica `changelog-sync.py`. `[^\\S\\n]*` y no
    #     `\\s*`: con `re.M` sobre un bloque, `\\s*` se come el salto de línea y un campo VACÍO
    #     captura la línea siguiente entera (se publicaba `- **Estado**: completado` como resumen).
    import importlib.util as _iu
    _spec = _iu.spec_from_file_location(
        "changelog_sync_t", os.path.join(ROOT, "skills", "changelog-sync", "scripts",
                                         "changelog-sync.py"))
    _cs = _iu.module_from_spec(_spec)
    _spec.loader.exec_module(_cs)
    assert ll.CHANGELOG_FIELD_PATTERN == _cs.CHANGELOG_FIELD_PATTERN, "los dos criterios divergen"
    assert "[^\\S\\n]*" in ll.CHANGELOG_FIELD_PATTERN and "\\s*" not in ll.CHANGELOG_FIELD_PATTERN
    _b = "### T-01 — x\n\n- **Changelog**:\n- **Estado**: completado\n"
    assert _cs.RE_CAMPO_CHANGELOG.search(_b).group("txt") == "", "el campo vacío es VACÍO"

    print("test_ledger_lint: 21/21 OK")


if __name__ == "__main__":
    main()
