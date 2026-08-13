#!/usr/bin/env python3
"""task-brief.py — brief DETERMINISTA de una tarea para el subagente de contexto fresco.

(Iniciativa sdd-hardening, C-08 — mecánica del ciclo de subagentes:
el brief lo extrae un script del plan, no lo redacta el orquestador a mano.)

Extrae de la carpeta de una iniciativa (docs/roadmap/<fecha>-<slug>/) todo lo que un
subagente fresco necesita para implementar UNA tarea `T-XX` — y nada más (brief-only):

  1. La TAREA completa de `tasks.md` (descripción, criterios de aceptación, subtareas, notas).
  2. La cabecera de su FASE (contexto inmediato).
  3. La PERSONA DE DOMINIO (iniciativa subagent-personas): si la tarea lleva
     `- **Tipo**: frontend|backend|db|devops|test|docs`, se antepone el perfil corto de
     `personas/<tipo>.md` (mismo kit). Sin etiqueta → subagente genérico; etiqueta sin
     persona en el catálogo → aviso + genérico (degradación, no bloqueo).
  4. La sección de ARQUITECTURA de `improvement-plan.md` (cómo encaja la pieza).
  5. La CONSTITUCIÓN del proyecto (`docs/CONSTITUTION.md`) si existe.
  6. El contrato de retorno: DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED.

Antes de extraer, valida el ledger con `ledger-lint.py` (mismo kit): un ledger inválido
detiene el brief con aviso (exit 2) — no se despacha trabajo sobre un ledger roto.

Uso:
  task-brief.py <carpeta-iniciativa> <T-XX> [--constitucion RUTA] [--sin-lint]
                [--personas-dir DIR]
Salida: el brief en Markdown por stdout. Exit: 0 ok · 1 tarea/ficheros no encontrados ·
2 ledger inválido.
"""
import argparse
import os
import re
import subprocess
import sys

CONTRATO = """## Contrato de retorno (obligatorio)

Trabaja SOLO con este brief y los ficheros que referencia (no explores el repo entero).
Al terminar, tu última línea debe ser exactamente uno de estos estados:

- `DONE` — tarea completa; todos los criterios de aceptación cumplidos (di cómo verificarlo).
- `DONE_WITH_CONCERNS: <duda concreta>` — completa, pero con una duda que la revisión debe mirar.
- `NEEDS_CONTEXT: <qué necesitas exactamente>` — te falta información; PROHIBIDO inventarla.
- `BLOCKED: <bloqueo concreto>` — no puedes avanzar (dependencia, permiso, contradicción).
"""


def _lineas_con_fence(text):
    """[(línea, en_fence)] — marca qué líneas viven dentro de un bloque de código
    cercado (```...```), para que los encabezados de EJEMPLO dentro de fences no
    se confundan con secciones reales (hallazgo de la revisión adversarial)."""
    out, en_fence = [], False
    for ln in text.splitlines():
        if re.match(r"^\s*(```|~~~)", ln):
            out.append((ln, True))  # la línea del fence también cuenta como dentro
            en_fence = not en_fence
        else:
            out.append((ln, en_fence))
    return out


def _seccion_tarea(tasks_text, tid):
    """(chunk de la tarea, cabecera de su fase) o (None, None). Ignora encabezados
    dentro de bloques de código; la fase es el ENCABEZADO ## inmediatamente anterior
    SOLO si es una Fase (una tarea bajo '## Apéndice' no hereda la fase de más arriba)."""
    lineas = _lineas_con_fence(tasks_text)
    task_re = re.compile(rf"^###\s+{re.escape(tid)}\b")
    ini = None
    for i, (ln, fenced) in enumerate(lineas):
        if not fenced and task_re.match(ln):
            ini = i
            break
    if ini is None:
        return None, None
    fin = len(lineas)
    for j in range(ini + 1, len(lineas)):
        ln, fenced = lineas[j]
        if not fenced and re.match(r"^##{1,2}\s", ln):
            fin = j
            break
    chunk = "\n".join(ln for ln, _ in lineas[ini:fin]).rstrip() + "\n"
    # fase: el último "## ..." REAL antes de la tarea, solo si es una Fase
    fase = None
    for j in range(ini - 1, -1, -1):
        ln, fenced = lineas[j]
        if not fenced and re.match(r"^##\s", ln) and not re.match(r"^###", ln):
            fase = ln if re.match(r"^##\s+Fase", ln) else None
            break
    return chunk, fase


def _tipo_de_tarea(chunk):
    """Etiqueta `- **Tipo**: <tipo>` del bloque de la tarea, normalizada a minúsculas,
    o None. Placeholders de plantilla ({{...}}) y valores no-etiqueta se tratan como
    ausentes (el campo es OPCIONAL: sin tipo → subagente genérico)."""
    # solo líneas VISIBLES: un `- **Tipo**:` de ejemplo dentro de un fence no cuenta
    visible = "\n".join(ln for ln, fenced in _lineas_con_fence(chunk) if not fenced)
    m = re.search(r"^\s*-\s*\*\*Tipo\*\*\s*:\s*(.+)$", visible, re.M | re.I)
    if not m:
        return None
    val = m.group(1).strip()
    if "{{" in val:
        return None
    val = val.split()[0].strip("`").lower() if val.split() else ""
    return val if re.fullmatch(r"[a-z][a-z0-9-]*", val) else None


def _persona(tipo, personas_dir):
    """Contenido de personas/<tipo>.md, o None con aviso (degradación, no bloqueo)."""
    p = os.path.join(personas_dir, f"{tipo}.md")
    if not os.path.isfile(p):
        print(f"⚠️  tarea con Tipo `{tipo}` pero sin persona en el catálogo "
              f"({p} no existe) — despacho con subagente genérico.", file=sys.stderr)
        return None
    contenido = open(p, encoding="utf-8", errors="replace").read().strip()
    if not contenido:
        print(f"⚠️  persona `{tipo}` vacía — despacho con subagente genérico.",
              file=sys.stderr)
        return None
    return contenido


def _seccion_plan(plan_text, titulo_re):
    lineas = _lineas_con_fence(plan_text)
    ini = None
    patron = re.compile(rf"^##\s+{titulo_re}", re.I)
    for i, (ln, fenced) in enumerate(lineas):
        if not fenced and patron.match(ln):
            ini = i
            break
    if ini is None:
        return None
    fin = len(lineas)
    for j in range(ini + 1, len(lineas)):
        ln, fenced = lineas[j]
        if not fenced and re.match(r"^##\s", ln) and not re.match(r"^###", ln):
            fin = j
            break
    return "\n".join(ln for ln, _ in lineas[ini:fin]).rstrip() + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("carpeta", help="carpeta de la iniciativa (docs/roadmap/<fecha>-<slug>)")
    ap.add_argument("tarea", help="ID de la tarea (T-XX)")
    ap.add_argument("--constitucion", default=None,
                    help="ruta de la constitución (default: se busca en <raíz del repo>/docs/"
                         "CONSTITUTION.md derivada de la carpeta, y luego docs/CONSTITUTION.md del cwd)")
    ap.add_argument("--sin-lint", action="store_true",
                    help="saltar la validación del ledger (solo para tests)")
    ap.add_argument("--personas-dir", default=None,
                    help="carpeta del catálogo de personas (default: personas/ junto al script)")
    args = ap.parse_args(argv)

    tid = args.tarea.upper()
    if not re.fullmatch(r"T-\d+", tid):
        print(f"❌ id de tarea inválido: {args.tarea} (esperado T-XX)", file=sys.stderr)
        return 1
    tasks_p = os.path.join(args.carpeta, "tasks.md")
    plan_p = os.path.join(args.carpeta, "improvement-plan.md")
    if not os.path.isfile(tasks_p):
        print(f"❌ no existe {tasks_p}", file=sys.stderr)
        return 1

    if not args.sin_lint:
        lint = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ledger-lint.py")
        if os.path.isfile(lint):
            r = subprocess.run([sys.executable, lint, tasks_p],
                               capture_output=True, text=True)
            if r.returncode != 0:
                print("❌ ledger inválido — arregla tasks.md antes de despachar "
                      f"(ledger-lint exit {r.returncode}):\n{r.stdout}{r.stderr}",
                      file=sys.stderr)
                return 2

    tasks_text = open(tasks_p, encoding="utf-8", errors="replace").read()
    chunk, fase = _seccion_tarea(tasks_text, tid)
    if not chunk:
        print(f"❌ tarea {tid} no encontrada en {tasks_p}", file=sys.stderr)
        return 1

    out = [f"# Brief de implementación — {tid}", ""]
    out.append(f"Iniciativa: `{args.carpeta}` · Ledger canónico: `{tasks_p}`. "
               "**NO toques el ledger**: lo actualiza el orquestador; tú limítate a "
               "reportar tu estado final (contrato de abajo).")
    if fase:
        out += ["", f"## Contexto de fase", "", f"> {fase.lstrip('# ').strip()}"]

    # persona de dominio (iniciativa subagent-personas): opcional por etiqueta Tipo
    tipo = _tipo_de_tarea(chunk)
    if tipo:
        personas_dir = args.personas_dir or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "personas")
        persona = _persona(tipo, personas_dir)
        if persona:
            out += ["", f"## Persona de dominio (tipo: {tipo})", "", persona, ""]

    out += ["", "## La tarea (de tasks.md — tus criterios de aceptación son EL contrato)",
            "", chunk]

    if os.path.isfile(plan_p):
        plan_text = open(plan_p, encoding="utf-8", errors="replace").read()
        arq = _seccion_plan(plan_text, r"Arquitectura")
        if arq:
            out += ["## Arquitectura de la solución (de improvement-plan.md)", "", arq]
    else:
        out += ["> (Sin improvement-plan.md — iniciativa de vía rápida: el ledger es todo el plan.)", ""]

    # constitución: ruta explícita, o derivada de la carpeta de la iniciativa
    # (docs/roadmap/<slug> → <raíz>/docs/CONSTITUTION.md), o el cwd como último recurso
    candidatas = ([args.constitucion] if args.constitucion else [
        os.path.join(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(args.carpeta)))), "docs", "CONSTITUTION.md"),
        os.path.join("docs", "CONSTITUTION.md"),
    ])
    const_p = next((c for c in candidatas if c and os.path.isfile(c)), None)
    if const_p:
        const = open(const_p, encoding="utf-8", errors="replace").read()
        out += ["## Constitución del proyecto (principios OBLIGATORIOS)", "", const.rstrip(), ""]

    out += ["", CONTRATO]
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
