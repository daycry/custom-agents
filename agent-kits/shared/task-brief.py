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
  6. La VERIFICACIÓN de la tarea (campo `- **Verificación**:` del ledger, plan-and-diet T-02): el
     subagente debe ejecutarla al terminar y pegar la salida real en su informe. Sin el campo, el
     brief lo dice y pide que proponga una (no inventa comandos). Acepta la forma en línea (` · `),
     la sub-lista (`  - cmd → res`) y `(ejecutada <fecha> — salida: …)` — parser único
     `parse_verificacion()` de ledger-lint.py (T-fix1).
  7. TDD (parity-core T-03): si `.claude/dev.json` del proyecto (raíz derivada de la carpeta, o cwd)
     tiene `tdd: true` — o se pasa `--tdd` —, el brief añade la sección «TDD» que manda seguir la
     skill `tdd` (fuente única del método) y devolver la evidencia del rojo (`RED: …`); dev.json
     ausente/corrupto → sin sección, aviso por stderr, nunca bloquea (`--dev-json RUTA` para tests).
  8. DISEÑO (parity-core T-fix1): si la carpeta tiene `design.md` (agente architect) en estado
     `aprobado`, se inyecta SOLO su sección «opción elegida y por qué» (token-diet: ni contexto, ni
     las opciones descartadas, ni el impacto); `borrador`/sin opción → aviso por stderr y nada.
  9. GAPS PENDIENTES (roles-and-jira-flow T-03 — redespacho tras una revisión con gaps): si el
     ÚLTIMO `## Revisión de dos lentes — intento N` de `tasks.md` trae filas de gap para ESTA
     `T-XX`, se inyectan (grado, gap, corrección sugerida, evidencia) con la misma disciplina que
     `agents/implementer.md`: verificar antes de corregir, rebatir con evidencia si el gap está mal.
     Es la vía por la que el `implementer` se entera de los gaps — NO por Jira (ese comentario, si
     Jira está activo, es solo el espejo para el equipo). Intento sin gaps o sin sección → nada.
  10. El contrato de retorno: DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED.

Antes de extraer, valida el ledger con `ledger-lint.py` (mismo kit): un ledger inválido
detiene el brief con aviso (exit 2) — no se despacha trabajo sobre un ledger roto.

Uso:
  task-brief.py <carpeta-iniciativa> <T-XX> [--constitucion RUTA] [--sin-lint]
                [--personas-dir DIR] [--tdd] [--dev-json RUTA]
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

- `DONE` — tarea completa; todos los criterios de aceptación cumplidos y la **Verificación ejecutada
  con su salida real pegada** (no «debería pasar»: el resultado).
- `DONE_WITH_CONCERNS: <duda concreta>` — completa, pero con una duda que la revisión debe mirar.
- `NEEDS_CONTEXT: <qué necesitas exactamente>` — te falta información; PROHIBIDO inventarla.
- `BLOCKED: <bloqueo concreto>` — no puedes avanzar (dependencia, permiso, contradicción).
"""


TDD_BRIEF = """## TDD (activo en `.claude/dev.json`: sigue la skill `tdd`)

Esta tarea se implementa con RED-GREEN-REFACTOR según la skill **`tdd`** (invócala con la herramienta
Skill; es la fuente única del método — no lo reinterpretes). Resumen del contrato: por cada criterio de
aceptación, escribe primero el test, córrelo SOLO y míralo fallar por la razón correcta; implementa el
mínimo; refactoriza en verde. El código escrito antes de su test se borra y se reescribe tras el rojo.
En tu informe devuelve una línea por criterio `RED: <fichero::test> falló con <error> · <fecha>` (el
orquestador la copia al ledger); si la tarea no tiene código testeable, devuelve `TDD n/a: <motivo>`.
"""


def _tdd_activo(carpeta, dev_json=None):
    """True si dev.json tiene `tdd: true`. Ruta: --dev-json, o <raíz derivada de la carpeta>/.claude/dev.json,
    o .claude/dev.json del cwd. Ausente → False sin ruido; ilegible → False + aviso (nunca bloquea)."""
    import json
    raiz = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(carpeta))))
    candidatas = [dev_json] if dev_json else [os.path.join(raiz, ".claude", "dev.json"),
                                              os.path.join(".claude", "dev.json")]
    for c in candidatas:
        if not c or not os.path.isfile(c):
            continue
        try:
            with open(c, encoding="utf-8-sig") as fh:
                data = json.load(fh)
        except (OSError, ValueError) as e:
            print(f"⚠️  dev.json ilegible ({c}: {e.__class__.__name__}) — brief sin sección TDD.", file=sys.stderr)
            return False
        return bool(isinstance(data, dict) and data.get("tdd") is True)
    return False


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


_LEDGER_LINT_CACHE = []


def _ledger_lint_mod():
    """`ledger-lint.py` del mismo kit, importado por ruta y memorizado (o None si no está).
    Fuente única del parseo compartido del ledger; nunca bloquea si falta el fichero."""
    if _LEDGER_LINT_CACHE:
        return _LEDGER_LINT_CACHE[0]
    lint = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ledger-lint.py")
    mod = None
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("ledger_lint", lint)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception:  # noqa: BLE001 — degradación: sin el kit completo se usan fallbacks locales
        mod = None
    _LEDGER_LINT_CACHE.append(mod)
    return mod


def _parse_verificacion_fn():
    """`parse_verificacion` de ledger-lint.py (mismo kit, importado por ruta) — fuente única del parser
    del campo; sin el fichero (instalación parcial), un fallback local que acepta la forma en línea."""
    mod = _ledger_lint_mod()
    if mod is not None and hasattr(mod, "parse_verificacion"):
        return mod.parse_verificacion

    # degradación: parser mínimo local (kit incompleto)
    rx = re.compile(r"^\s*-\s*\*\*Verificaci[oó]n\*\*\s*(\((?:[^()]|\([^()]*\))*\))?\s*:\s*(.*)$", re.I)

    def _fallback(lines, i):
        m = rx.match(lines[i])
        if not m:
            return None, i
        inline = m.group(2).strip()
        items = [s.strip() for s in re.split(r"\s+·\s+", inline) if s.strip()]
        return {"items": items, "ejecutada": (m.group(1) or "()")[1:-1].strip() or None,
                "inline": inline}, i + 1
    return _fallback


def _verificacion_de_tarea(chunk):
    """{"items": [...], "ejecutada": str|None} del campo `- **Verificación**` del bloque de la tarea, o None
    si no existe o está vacío. Acepta la forma en línea (ítems con ` · `), la sub-lista (`  - cmd → res`
    debajo) y la variante `(ejecutada <fecha> — salida: …)` — el paréntesis se parsea aparte, así el
    comando inyectado es el comando y no la salida grabada (T-fix1). Solo líneas VISIBLES (un ejemplo
    dentro de un fence no cuenta); placeholders `{{…}}` de plantilla = ausente."""
    visible = [ln for ln, fenced in _lineas_con_fence(chunk) if not fenced]
    parse = _parse_verificacion_fn()
    for i, ln in enumerate(visible):
        info, _ = parse(visible, i)
        if info is None:
            continue
        items = [x for x in info["items"] if "{{" not in x]
        if not items:
            return None
        return {"items": items, "ejecutada": info["ejecutada"]}
    return None


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


def _design_elegida(carpeta):
    """(opcion, texto de la sección «opción elegida») de design.md aprobado, o None (con aviso si existe
    pero está en borrador / sin opción). Solo esa sección: token-diet."""
    p = os.path.join(carpeta, "design.md")
    if not os.path.isfile(p):
        return None
    text = open(p, encoding="utf-8", errors="replace").read()
    fm = {}
    if text.startswith("---"):
        end = text.find("\n---", 3)
        for raw in text[3:end].splitlines() if end != -1 else []:
            if raw and raw[0] not in " \t#" and ":" in raw:
                k, v = raw.split(":", 1)
                fm[k.strip()] = v.split("#", 1)[0].strip()
    estado, opcion = fm.get("estado", ""), fm.get("opcion_elegida", "")
    if estado != "aprobado" or not opcion or opcion == "pendiente":
        print(f"⚠️  design.md en estado `{estado or '?'}` (opción `{opcion or '?'}`): no se inyecta en el brief — "
              f"cierra la validación del diseño (architect, pasada 2) antes de despachar.", file=sys.stderr)
        return None
    sec = _seccion_plan(text, r"\d+\.\s*(?:Recomendación\s*·\s*)?[Oo]pci[oó]n elegida")
    if not sec:
        return None
    cuerpo = "\n".join(sec.splitlines()[1:]).strip()
    return opcion, cuerpo


# Copia LITERAL de `REVISION_HDR_PATTERN` de ledger-lint.py, solo para cuando el kit no viaja
# completo. `tests/` compara las dos cadenas: si divergen, el test falla (T-fix1).
_REVISION_HDR_FALLBACK = \
    r"^##\s+Revisi[oó]n de dos lentes\s*[\u2014\u2013-]\s*intento\s+(\d+)\s*(?::\s*(.*))?$"


def _revision_hdr_re():
    """Regex de `## Revisión de dos lentes — intento N`: la CANÓNICA de `ledger-lint.py`
    (`REVISION_HDR_PATTERN`), para que este brief y `skills/jira-sync/scripts/jira-flow.py` lean
    exactamente las mismas cabeceras. Antes cada uno tenía su criterio (aquí `:` opcional, allí
    obligatorio) y una cabecera sin `:` daba brief CON gaps y Jira exit 2 (T-fix1)."""
    mod = _ledger_lint_mod()
    pat = getattr(mod, "REVISION_HDR_PATTERN", None) if mod is not None else None
    return re.compile(pat or _REVISION_HDR_FALLBACK, re.M)


_REVISION_HDR_RE = _revision_hdr_re()


def _split_fila_md(ln):
    """Divide una fila de tabla Markdown por `|`, ignorando los `|` dentro de un tramo `` `código` ``
    (una celda de gap puede citar una regex con alternancia `a|b|c`; un split ingenuo la trocearía).
    Mismo criterio que `skills/jira-sync/scripts/jira-flow.py` — no se importa por no cruzar shared→skill,
    pero es la misma regla, no una reinterpretación."""
    celdas, actual, en_codigo = [], [], False
    for ch in ln.strip().strip("|"):
        if ch == "`":
            en_codigo = not en_codigo
            actual.append(ch)
        elif ch == "|" and not en_codigo:
            celdas.append("".join(actual).strip())
            actual = []
        else:
            actual.append(ch)
    celdas.append("".join(actual).strip())
    return celdas


def _gaps_pendientes_de_tarea(tasks_text, tid):
    """{"intento": N, "filas": [...]} con los gaps de `tid` en el ÚLTIMO `## Revisión de dos
    lentes — intento N` de TODO `tasks.md` (la sección vive al final del ledger, no dentro del
    bloque `### T-XX`) — o None si no hay ninguna sección de revisión, o si el último intento no
    tiene gaps para esta tarea (revisión limpia: nada que inyectar). Cada intento es una foto
    nueva de la revisión (los gaps de un intento anterior ya resuelto no reaparecen en el
    siguiente) — por eso solo el ÚLTIMO intento importa para un redespacho."""
    matches = list(_REVISION_HDR_RE.finditer(tasks_text))
    if not matches:
        return None
    ultimo = max(matches, key=lambda m: int(m.group(1)))
    idx = matches.index(ultimo)
    inicio = ultimo.end()
    fin = matches[idx + 1].start() if idx + 1 < len(matches) else len(tasks_text)
    filas = []
    for ln in tasks_text[inicio:fin].splitlines():
        ln = ln.strip()
        if not ln.startswith("|") or set(ln.replace("|", "").strip()) <= {"-", " "}:
            continue
        celdas = _split_fila_md(ln)
        if len(celdas) < 6 or not re.match(r"^\d+$", celdas[0]) or celdas[3] != tid:
            continue
        filas.append({"grado": celdas[1], "gap": celdas[2], "correccion": celdas[4], "evidencia": celdas[5]})
    return {"intento": int(ultimo.group(1)), "filas": filas} if filas else None


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
    ap.add_argument("--tdd", action="store_true", help="fuerza la sección TDD (como si dev.json tuviera tdd: true)")
    ap.add_argument("--dev-json", default=None, help="ruta explícita de .claude/dev.json (default: derivada de la carpeta)")
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

    # gaps pendientes (roles-and-jira-flow T-03): redespacho tras una revisión con gaps para ESTA tarea
    gaps = _gaps_pendientes_de_tarea(tasks_text, tid)
    if gaps:
        out += ["## Gaps pendientes de revisión (intento "
                f"{gaps['intento']} — corrige ANTES de re-verificar)", ""]
        for f_ in gaps["filas"]:
            out += [f"- **[{f_['grado']}]** {f_['gap']}",
                    f"  - Corrección sugerida: {f_['correccion']}",
                    f"  - Evidencia/escenario: {f_['evidencia']}"]
        out += ["",
                "**Verifica antes de corregir** (disciplina de `agents/implementer.md`): comprueba cada "
                "señalamiento contra el código y la spec. Si es correcto, corrígelo. Si es INCORRECTO, "
                "**rebátelo con evidencia** (`fichero:línea` + por qué está bien como está) en tu informe "
                "— no lo apliques a ciegas ni lo descartes sin evidencia.", ""]

    # verificación declarada (plan-and-diet T-02): el subagente la ejecuta al terminar y pega la salida
    verif = _verificacion_de_tarea(chunk)
    if verif:
        out += ["## Verificación (ejecútala al terminar y pega la salida)", ""]
        out += [f"- {item}" for item in verif["items"]]
        out += ["",
                "Ejecuta EXACTAMENTE esa verificación (todos los ítems) cuando creas haber terminado y pega su "
                "salida real en tu informe (no «debería pasar»: el resultado). Si no pasa, la tarea NO está `DONE`."]
        if verif["ejecutada"]:
            out += ["", f"> Verificación ya ejecutada antes ({verif['ejecutada'].split(' — ')[0]}): "
                        "**re-ejecútala** — la salida grabada en el ledger es de otra sesión, no vale como evidencia tuya."]
        out += [""]
    else:
        out += ["## Verificación", "",
                "> (la tarea no declara `Verificación`: propón una en tu informe — un comando y su resultado "
                "esperado — y ejecútala antes de reportar `DONE`.)", ""]

    diseno = _design_elegida(args.carpeta)
    if diseno:
        out += [f"## Diseño (design.md · opción elegida {diseno[0]})", "", diseno[1],
                "", "Respeta esta opción: no rediseñes; una duda de arquitectura es `DONE_WITH_CONCERNS`, no un cambio.", ""]

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

    if args.tdd or _tdd_activo(args.carpeta, args.dev_json):
        out += ["", TDD_BRIEF]

    out += ["", CONTRATO]
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
