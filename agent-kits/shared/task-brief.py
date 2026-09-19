#!/usr/bin/env python3
"""task-brief.py — brief DETERMINISTA de una tarea para el subagente de contexto fresco.

(Iniciativa sdd-hardening, C-08 — mecánica del ciclo de subagentes:
el brief lo extrae un script del plan, no lo redacta el orquestador a mano.)

Extrae de la carpeta de una iniciativa (docs/roadmap/<fecha>-<slug>/) todo lo que un
subagente fresco necesita para implementar UNA tarea `T-XX` — y nada más (brief-only):

  1. La TAREA completa de `tasks.md` (descripción, criterios de aceptación, subtareas, notas).
  2. La cabecera de su FASE (contexto inmediato).
  3. La PERSONA DE DOMINIO (iniciativa subagent-personas; cascada de tres escalones desde
     project-specialization T-01): si la tarea lleva `- **Tipo**: <tipo>`, se antepone el perfil
     corto de `.claude/personas/<tipo>.md` DEL PROYECTO si existe, si no el de
     `personas/<tipo>.md` (catálogo del plugin, o `--personas-dir`). Los tipos son libres: no hay
     lista blanca. Sin etiqueta → subagente genérico; etiqueta sin persona en ningún escalón →
     aviso + genérico (degradación, no bloqueo).
  4. La sección de ARQUITECTURA de `improvement-plan.md` (cómo encaja la pieza).
  5. La CONSTITUCIÓN del proyecto (`docs/CONSTITUTION.md`) si existe.
  6. La VERIFICACIÓN de la tarea (campo `- **Verificación**:` del ledger, plan-and-diet T-02): el
     subagente debe ejecutarla al terminar y pegar la salida real en su informe. Sin el campo, el
     brief lo dice y pide que proponga una (no inventa comandos). Acepta la forma en línea (` · `),
     la sub-lista (`  - cmd → res`) y `(ejecutada <fecha> — salida: …)` — parser único
     `parse_verificacion()` de ledger-lint.py (T-fix1). El brief lleva la verificación UNA vez, en su
     sección (memory-retrieval, revisión intento 1): en el bloque de la tarea el campo se sustituye por
     un puntero a esa sección (antes iba entero en los dos sitios: 2.300-3.200 caracteres duplicados),
     y los ítems que son EVIDENCIA de una ejecución anterior —`RED: <test> falló con … · <fecha>`, el
     rojo del TDD que el ledger conserva para la revisión— se omiten y se cuentan en una línea: un
     subagente necesita «comando → esperado», no el historial; si TDD está activo, produce su propio
     rojo. Y los campos de PRESUPUESTO del bloque (`Tiempo humano` · `Tiempo IA` · `Supervisión` ·
     `Previsión IA`: horas y euros del PM) y el `Changelog` (nota de release de quien CIERRA la tarea,
     ADR-012) tampoco van: no son información para implementar. Con eso
     el brief completo cabe en el tope de la spec (CA-08: ≤ 2.500 tokens ≈ BRIEF_TOPE_CHARS = 10.000
     caracteres; medido sobre las 10 tareas cerradas de memory-retrieval, 2026-09-07: 8.919-12.543
     antes → todas ≤ 10.000 después). El test lo afirma sobre ese ledger real y sobre uno de `tmp_path`.
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
  11. MEMORIA TÉCNICA (memory-retrieval T-05 — la puerta cerrada del hueco 1: con `subagentes: true`
      el brief es el ÚNICO contexto y hasta aquí no llevaba ni un gotcha): los aciertos compactos de
      `knowledge-find.py --json` (mismo kit) ENRUTADOS por el `- **Tipo**:` de la tarea, el título de
      la tarea y el slug de la iniciativa (`--tipo-tarea/--contexto/--iniciativa`: casan por ÁREA, nunca
      por texto libre; sin `Tipo` cae a la iniciativa y al título, no al corpus entero). Tope
      MEMORIA_TOPE_CHARS (≤ 600 tokens, spec CA-08): si no cabe se recorta y se dice. Degradación
      SILENCIOSA: sin `docs/knowledge/`, sin aciertos, sin el script o con el script fallando → no hay
      sección y el brief sale byte a byte como sin memoria (CA-09); un fallo se cuenta solo por stderr.
      El detalle se abre por ID (`--show`), no se pega entero: progressive disclosure.

Antes de extraer, valida el ledger con `ledger-lint.py` (mismo kit): un ledger inválido
detiene el brief con aviso (exit 2) — no se despacha trabajo sobre un ledger roto.

Uso:
  task-brief.py <carpeta-iniciativa> <T-XX> [--constitucion RUTA] [--sin-lint]
                [--personas-dir DIR] [--tdd] [--dev-json RUTA] [--knowledge-find RUTA]
Salida: el brief en Markdown por stdout. Exit: 0 ok · 1 tarea/ficheros no encontrados ·
2 ledger inválido.
"""
import argparse
import json
import os
import re
import subprocess
import sys

# Consola Windows (cp1252) o tuberías: reconfigurar ANTES de leer o imprimir nada (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

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


MEMORIA_TOPE_CHARS = 2400      # ≤ 600 tokens de memoria en el brief (spec CA-08); con test que lo afirma
MEMORIA_LIMIT = 12             # aciertos que se piden; el tope de caracteres es el que manda
MEMORIA_TIMEOUT = 20           # s: knowledge-find.py es local y determinista; si se cuelga, sin sección
BRIEF_TOPE_CHARS = 10000       # brief completo ≤ 2.500 tokens (spec CA-08); lo afirma el test sobre el ledger real
# Persona de dominio (project-specialization T-01, revisión intento 1 gap 2): el fichero de
# `.claude/personas/<tipo>.md` del proyecto se pega ÍNTEGRO, sin la casilla propia que el diseño
# nunca fijó (spec.md: «MEMORIA_TOPE_CHARS no se toca: la persona usa su propia casilla» — pero esa
# casilla no llevaba número). Mismo patrón que la sección de memoria (§11): recorta y lo dice, en
# vez de desbordar en silencio el tope global del brief (BRIEF_TOPE_CHARS, CA-08).
# Revisión intento 2, gap B-3: esta constante NO fija el tope por sí sola — es un CAP de sanidad
# (nunca dejar que una persona sola se coma el brief entero aunque sobre margen). El tope EFECTIVO es
# `min(PERSONA_TOPE_CHARS, margen que quede de verdad tras montar el resto del brief)`, calculado en
# main() una vez conocido ese resto: medido sobre el ledger real, 11/22 tareas ya pasan de
# BRIEF_TOPE_CHARS sin persona (preexistente, `## Diseño` + memoria + tabla de gaps — no se arregla
# aquí), así que un margen fijo de 4.000 es una promesa falsa para esas tareas (T-06: margen real 430).
PERSONA_TOPE_CHARS = 4000      # ≤ 1.000 tokens; CAP de sanidad, no el tope real (ver comentario arriba)
# Revisión intento 3, gap B-3 (opción A, decisión del usuario tras el 3.er intento del bucle acotado):
# el margen real puede quedar por debajo de lo que ocupa una persona ENTERA del catálogo (T-06: margen
# real recortó `docs.md` de 1.107 a 55 caracteres — un muñón ilegible). El problema de fondo (11/22
# tareas ya pasan de BRIEF_TOPE_CHARS SIN persona: `## Diseño` + memoria + tabla de gaps) es de otra
# iniciativa y no se arregla aquí; lo que sí es alcance de esta corrección es que la persona nunca sea
# la víctima de ese exceso preexistente. `PERSONA_SUELO_CHARS` es un SUELO garantizado: por debajo de
# él nunca se recorta el CONTENIDO de una persona, aunque el margen real sea menor o negativo (el
# brief se pasará de BRIEF_TOPE_CHARS, y el aviso de abajo lo dice con la causa medida, sin culpar a
# la persona). Medido: las 6 personas del catálogo (`agent-kits/shared/personas/*.md`, tras `.strip()`)
# — backend.md 1058, frontend.md 1076, docs.md 1107, devops.md 1164, db.md 1162, test.md 1182 (la
# mayor: `test_persona_suelo_por_encima_del_catalogo` lo comprueba contra el catálogo real, no a
# ciegas). Suelo fijado justo por encima de la mayor, con margen para crecer sin tocar la constante.
#
# Tres reglas para esta sección, no cuatro (revisión intento 3, código muerto detectado: la cuarta,
# `PERSONA_TOPE_MINIMO_UTIL`, era inalcanzable — los dos puntos de llamada pasan `BRIEF_TOPE_CHARS` o
# un `tope_cuerpo` que por `max(PERSONA_SUELO_CHARS, …)` nunca baja de 1.300 — y se retira):
#   1. `PERSONA_TOPE_CHARS` — techo cuando sobra margen de verdad (CAP de sanidad).
#   2. `PERSONA_SUELO_CHARS` — mínimo de CONTENIDO que se entrega siempre, sin descontar la nota de
#      recorte (gap B-4: antes el suelo se repartía entre contenido y nota, y una nota con ruta
#      absoluta larga podía dejar menos contenido útil que una persona más pequeña sin recortar).
#   3. El margen real entre ambos manda cuando cae dentro de ese rango.
PERSONA_SUELO_CHARS = 1300     # ≥ la persona más grande del catálogo (1.182); nunca se baja de aquí
# Ítem de Verificación que es evidencia del rojo de una ejecución anterior (skill `tdd`: `RED: <test> falló
# con <error> · <fecha>`), no un comando que ejecutar: se omite del brief y se cuenta.
_ITEM_RED_RE = re.compile(r"^\s*[`*_]*\s*(RED|TDD n/a)\s*:", re.I)
# Campos del ledger que NO son información para implementar y se quitan del bloque de la tarea (≈ 350-800 chars):
# los de PRESUPUESTO (horas y euros, estimado vs real: contabilidad del PM que el brief no pide devolver) y el
# `Changelog` (la nota de release, que escribe quien CIERRA la tarea —ADR-012—: una tarea en despacho no lo tiene,
# y en un redespacho de una cerrada es texto para el usuario del proyecto, no para el subagente).
_CAMPO_NO_BRIEF_RE = re.compile(r"^\s*-\s*\*\*(Tiempo humano|Tiempo IA[^*]*|Supervisi[oó]n|Previsi[oó]n IA|Changelog)\*\*\s*:", re.I)


def _es_evidencia_red(item):
    return bool(_ITEM_RED_RE.match(item or ""))


def _raiz_de(carpeta):
    """Raíz del proyecto derivada de la carpeta de la iniciativa (docs/roadmap/<slug> → <raíz>)."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(carpeta))))


def _titulo_de_tarea(chunk):
    m = re.match(r"^###\s+T-\d+\s*[—:-]\s*(.+)$", chunk.splitlines()[0] if chunk else "")
    return m.group(1).strip() if m else ""


def _memoria_tecnica(carpeta, chunk, tipo, script=None):
    """Sección 11 o None. Llama a `knowledge-find.py --json` (subproceso: un fallo suyo, cualquiera, no
    puede tumbar el brief) enrutando por `Tipo`, título de la tarea e iniciativa; sin `docs/knowledge/`,
    sin aciertos o sin script → None en SILENCIO (es el caso normal de un proyecto recién instalado)."""
    raiz = _raiz_de(carpeta)
    if not os.path.isdir(os.path.join(raiz, "docs", "knowledge")):
        return None
    script = script or os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge-find.py")
    if not os.path.isfile(script):
        return None
    slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", os.path.basename(os.path.normpath(os.path.abspath(carpeta))))
    titulo = _titulo_de_tarea(chunk)
    cmd = [sys.executable, script, "--json", "--root", raiz, "--limit", str(MEMORIA_LIMIT),
           "--contexto", titulo, "--iniciativa", slug] + (["--tipo-tarea", tipo] if tipo else [])
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=MEMORIA_TIMEOUT)
        if r.returncode != 0:
            raise RuntimeError(f"exit {r.returncode}: {(r.stderr or r.stdout).strip()[:200]}")
        data = json.loads(r.stdout)
        aciertos = [a["linea"] for a in data["aciertos"] if a.get("linea")]
        total = int(data.get("total", len(aciertos)))
        claves = data.get("consulta", {}).get("claves", [])
    except Exception as e:  # noqa: BLE001 — la memoria nunca bloquea el brief: se omite y se dice por stderr
        print(f"⚠️  knowledge-find.py no respondió ({e.__class__.__name__}: {e}) — brief sin sección de memoria.",
              file=sys.stderr)
        return None
    if not aciertos:
        return None
    ruta = f"`{slug}`"
    cabecera = [f"## Memoria técnica del proyecto (docs/knowledge — {total} acierto(s) de knowledge-find.py)", "",
                f"Entradas cuya ÁREA casa con esta tarea (tipo `{tipo or '—'}`, iniciativa {ruta}"
                + (f", claves: {', '.join(claves[:8])}" if claves else "") + "). El `estado` va delante: "
                "`aceptada` es doctrina (aplícala), `propuesta` indicio (dilo si condiciona una decisión), "
                "`obsoleta` no se aplica (sigue a su sucesor). Abre SOLO la que necesites, por ID:", "",
                f"    python3 \"{script}\" --show <ID>    # o `--related <ID>` para su grafo curado", ""]
    pie_de = lambda n_fuera: [] if not n_fuera else [  # noqa: E731
        "", f"… y {n_fuera} acierto(s) más que no caben en el tope de {MEMORIA_TOPE_CHARS} caracteres: "
        f"`python3 \"{script}\" --contexto \"{titulo}\" --iniciativa {slug}"
        + (f" --tipo-tarea {tipo}" if tipo else "") + "` los lista todos."]
    n = len(aciertos)
    while n >= 0:
        cuerpo = [f"- {l}" for l in aciertos[:n]]
        sec = "\n".join(cabecera + cuerpo + pie_de(total - n))
        if len(sec) <= MEMORIA_TOPE_CHARS:
            return sec + "\n" if n > 0 else None    # UN elemento del brief que acaba en línea en blanco
        n -= 1
    return None


def _tdd_activo(carpeta, dev_json=None):
    """True si dev.json tiene `tdd: true`. Ruta: --dev-json, o <raíz derivada de la carpeta>/.claude/dev.json,
    o .claude/dev.json del cwd. Ausente → False sin ruido; ilegible → False + aviso (nunca bloquea)."""
    raiz = _raiz_de(carpeta)
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


def _estado_estructura_por_linea(text):
    """[(fence_abierto_tras_esta_línea, comentario_abierto_tras_esta_línea), ...] — tras cada línea,
    si un bloque de código (```/~~~) o un comentario HTML (<!-- -->) sigue ABIERTO. Lo usa
    `_recorte_seguro` (gap B-2, revisión intento 2) para no partir ninguna de las dos estructuras al
    truncar contenido INYECTADO (persona de dominio): antes se cortaba a ciegas por índice de
    carácter y lo que seguía se lo comía el bloque abierto."""
    en_fence, en_comentario = False, False
    estados = []
    for ln in text.splitlines():
        if re.match(r"^\s*(```|~~~)", ln):
            en_fence = not en_fence
        else:
            resto = ln
            while resto:
                if en_comentario:
                    idx = resto.find("-->")
                    if idx == -1:
                        break
                    en_comentario = False
                    resto = resto[idx + 3:]
                else:
                    idx = resto.find("<!--")
                    if idx == -1:
                        break
                    en_comentario = True
                    resto = resto[idx + 4:]
        estados.append((en_fence, en_comentario))
    return estados


def _recorte_seguro(contenido, tope):
    """Recorta `contenido` a como mucho `tope` caracteres sin partir un fence de código ni un
    comentario HTML abiertos (gap B-2): corta por LÍNEAS completas y, si el punto de corte cae
    dentro de una de las dos estructuras, retrocede hasta la última línea donde ambas están
    cerradas — «corta antes», nunca «cierra a ciegas» un bloque que sigue abierto. Si tras ese
    retroceso sobra margen (p.ej. una única línea/párrafo sin saltos, más larga que `tope`), se
    aprovecha con un corte por CARÁCTER de la línea siguiente, pero solo si esa línea no es ella
    misma un marcador de fence/comentario y no venimos de una estructura abierta (si lo fuera,
    un corte a medias podría dejar un `` ` `` o un `<!--` truncado). Devuelve
    (texto_recortado, se_recortó); `tope <= 0` o sin ningún punto seguro → ("", True)."""
    if tope <= 0:
        return "", True
    if len(contenido) <= tope:
        return contenido, False
    lineas = contenido.splitlines(keepends=True)
    estados = _estado_estructura_por_linea(contenido)
    acumulado, n = 0, 0
    for i, ln in enumerate(lineas):
        if acumulado + len(ln) > tope:
            break
        acumulado += len(ln)
        n = i + 1
    while n > 0 and (estados[n - 1][0] or estados[n - 1][1]):
        n -= 1
    texto = "".join(lineas[:n])
    if n < len(lineas):
        texto = _aprovecha_margen_de_linea(texto, lineas[n], estados[n - 1] if n > 0 else (False, False), tope)
    return texto.rstrip(), True


def _aprovecha_margen_de_linea(texto, siguiente, estado_previo, tope):
    """Si tras el corte por líneas sobra margen (una línea/párrafo más largo que `tope`), lo aprovecha
    con un corte por CARÁCTER de `siguiente` — pero solo si esa línea no es ella misma un marcador de
    fence/comentario y no venimos de una estructura abierta (evita dejar un `` ` `` o `<!--` truncado)."""
    es_marcador = bool(re.match(r"^\s*(```|~~~)", siguiente)) or "<!--" in siguiente or "-->" in siguiente
    if es_marcador or estado_previo[0] or estado_previo[1]:
        return texto
    restante = tope - len(texto)
    return texto + siguiente[:restante] if restante > 0 else texto


def _neutraliza_encabezados(texto):
    """Antepone `\\` a cualquier línea que Markdown renderizaría como encabezado (`# ...`) dentro de
    contenido INYECTADO (persona de dominio): así no puede fingir una sección al mismo nivel que
    `## Contrato de retorno` u otra del brief (gap B-1, revisión intento 2) — el texto sigue siendo
    legible, solo deja de ser un heading real."""
    return "\n".join(
        ("\\" + ln if re.match(r"^ {0,3}#{1,6}(\s|$)", ln) else ln)
        for ln in texto.splitlines()
    )


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


def _chunk_sin_verificacion(chunk, n_items):
    """El bloque de la tarea con el campo `- **Verificación**…:` (y su sub-lista) sustituido por UNA línea
    que apunta a la sección «Verificación» del brief. Mismo parser que la sección (`parse_verificacion`,
    fuente única): lo que se quita aquí es exactamente lo que la sección reproduce, así que no se pierde
    nada. Sin campo visible → el chunk intacto."""
    lineas = _lineas_con_fence(chunk)
    raw = [ln for ln, _ in lineas]
    parse = _parse_verificacion_fn()
    for i, (ln, fenced) in enumerate(lineas):
        if fenced:
            continue
        info, j = parse(raw, i)
        if info is None:
            continue
        puntero = (f"- **Verificación**: {n_items} ítem(s) → en la sección «Verificación» de este brief "
                   "(no se repite aquí).")
        return "\n".join(raw[:i] + [puntero] + raw[max(j, i + 1):])
    return chunk


def _chunk_sin_presupuesto(chunk):
    """El bloque de la tarea sin sus campos de presupuesto (`Tiempo humano`, `Tiempo IA`, `Supervisión`,
    `Previsión IA`: horas y euros del PM) ni `Changelog` (nota de release de quien cierra): no son información
    para implementar. Solo líneas visibles; un campo de varias líneas no existe en el ledger (una línea por campo)."""
    return "\n".join(ln for ln, fenced in _lineas_con_fence(chunk) if fenced or not _CAMPO_NO_BRIEF_RE.match(ln))


def _persona_cascada(tipo, personas_dir, carpeta=None):
    """(contenido, ruta) de la persona `tipo`, resuelto en CASCADA de tres escalones
    (project-specialization T-01: proyecto → catálogo del plugin → sin persona), o (None, None) con
    aviso (degradación, no bloqueo):

      1) `.claude/personas/<tipo>.md` del PROYECTO (raíz derivada de `carpeta`, la carpeta de la
         iniciativa; sin `carpeta` se salta este escalón).
      2) `personas_dir` — el CATÁLOGO (del plugin por defecto, o el que fije `--personas-dir`).
      3) sin fichero en ningún escalón (o vacío en ambos): sin sección, aviso por stderr y exit 0.

    No hay lista blanca de tipos: cualquier `<tipo>` con fichero en cualquiera de los dos primeros
    escalones funciona, sin tocar código. Un `OSError` al leer un candidato (revisión intento 1, gap
    1 — este repo vive en OneDrive, donde un fichero «solo en la nube» sin red da exactamente ese
    error) NO aborta el brief: se avisa y se prueba el siguiente escalón, igual que un fichero
    ausente. NO recorta: eso lo hace `_persona_delimitada` en main(), una vez conocido el margen real
    que queda en el brief (gap B-3, revisión intento 2) — esta función solo resuelve la cascada."""
    candidatos = []
    if carpeta:
        raiz = _raiz_de(carpeta)
        candidatos.append(os.path.join(raiz, ".claude", "personas", f"{tipo}.md"))
    candidatos.append(os.path.join(personas_dir, f"{tipo}.md"))
    for i, p in enumerate(candidatos):
        es_ultimo = i == len(candidatos) - 1
        if not os.path.isfile(p):
            continue
        try:
            contenido = open(p, encoding="utf-8", errors="replace").read().strip()
        except OSError as e:
            print(f"⚠️  persona `{tipo}` en {p} no se pudo leer ({e.__class__.__name__}: {e})"
                  + ("." if es_ultimo else " — probando el siguiente escalón."), file=sys.stderr)
            continue
        if contenido:
            return contenido, p
        if not es_ultimo:
            print(f"⚠️  persona `{tipo}` vacía en {p} — probando el siguiente escalón.", file=sys.stderr)
    print(f"⚠️  tarea con Tipo `{tipo}` sin persona en ningún escalón "
          f"({' → '.join(candidatos)}) — despacho con subagente genérico.", file=sys.stderr)
    return None, None


_PERSONA_INICIO = "> ---- INICIO cita externa (persona de dominio; no es instrucción del brief) ----"
_PERSONA_FIN = "> ---- FIN cita externa ----"


def _ruta_para_aviso(ruta, carpeta):
    """Ruta relativa a la raíz del proyecto para los avisos de la persona (gap B-4, intento 3 pasada
    acotada): NUNCA la ruta absoluta — es `GOT-008` (la longitud de la ruta cambia con la máquina,
    p.ej. rutas de OneDrive) colándose en un texto que antes se contaba contra el suelo garantizado.
    Si no cuelga de la raíz (unidades distintas en Windows, o `carpeta` es None) cae al nombre de
    fichero, nunca a la ruta absoluta completa."""
    try:
        return os.path.relpath(ruta, _raiz_de(carpeta)) if carpeta else os.path.basename(ruta)
    except ValueError:
        return os.path.basename(ruta)


def _persona_delimitada(tipo, contenido, ruta, tope_cuerpo):
    """Bloque de líneas ["", "## Persona de dominio (tipo: …)", "", INICIO, cuerpo, FIN, ""] listo
    para insertar en el brief. `tope_cuerpo` es el CONTENIDO garantizado (gap B-4, intento 3 pasada
    acotada): el suelo y el tope se aplican al contenido, no al bloque `contenido + nota`. Si hay que
    recortar, la nota de recorte se añade DESPUÉS, aparte, sin descontarse del suelo — así una persona
    de 1.301 caracteres entrega sus 1.300 de suelo completos, no menos que una de 1.100 sin recortar
    (antes: reservar el hueco de la nota DENTRO de `tope_cuerpo` hacía que el contenido útil dependiera
    de la longitud de la ruta del fichero en la nota — acantilado no monótono, `GOT-008`). La nota ya
    no lleva la ruta absoluta: solo el `tipo` (`_ruta_para_aviso` la usa en los avisos por stderr, que
    no cuentan contra ningún tope). El recorte usa `_recorte_seguro` (por líneas, sin partir fences ni
    comentarios HTML: gap B-2). El cuerpo se delimita con marcas VISIBLES de apertura Y cierre (antes
    era un comentario HTML de apertura sola, invisible en cualquier render: gap B-1) y sus encabezados
    se neutralizan para que no pueda fingir una sección del brief (`_neutraliza_encabezados`)."""
    if len(contenido) <= tope_cuerpo:
        cuerpo_final = contenido
    else:
        recortado, _ = _recorte_seguro(contenido, tope_cuerpo)
        if not recortado:
            print(f"⚠️  la persona `{tipo}` de {ruta} no cabe en el margen real ({tope_cuerpo} caracteres) "
                  "sin partir un bloque de código o un comentario HTML — se omite.", file=sys.stderr)
            return []
        nota = (f"\n\n… recortado a {len(recortado)} de {len(contenido)} caracteres (margen real del "
                f"brief, CA-08): resume la persona de tipo `{tipo}` si necesitas que quepa entera.")
        print(f"⚠️  persona `{tipo}` en {ruta} recortada de {len(contenido)} a {len(recortado)} "
              "caracteres (margen real del brief, CA-08; corte alineado a línea para no partir un "
              "bloque de código ni un comentario HTML).", file=sys.stderr)
        cuerpo_final = recortado + nota
    cuerpo = _neutraliza_encabezados(cuerpo_final)
    return ["", f"## Persona de dominio (tipo: {tipo})", "", _PERSONA_INICIO, cuerpo, _PERSONA_FIN, ""]


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
# DECLARADA en `agent-kits/shared/copias.json` (bloque `revision_hdr_pattern`, ADR-016): el registro
# es la lista única de copias del repo y `scripts/lint_plugin.py` da error si aparece una `_*_FALLBACK`
# sin fila.
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


VALLA_PATTERN = r"^[^\S\n]*(?:`{3,}|~{3,})"

_VALLA_RE = re.compile(VALLA_PATTERN)


def sin_vallas(text):
    """`text` con las líneas DENTRO de una valla de código vaciadas (mismo número de líneas)."""
    # --8<-- sin_vallas (cuerpo) — REPLICADO LITERAL en agent-kits/shared/ledger-lint.py y en
    # skills/changelog-sync/scripts/changelog-sync.py (dos copias independientes: la skill viaja sin
    # este kit). DECLARADO en agent-kits/shared/copias.json (ADR-016), que lista la ÚNICA diferencia
    # tolerada (el nombre de la regex de valla); tests/test_copias_declaradas.py compara el resto
    # byte a byte — antes solo había un test CONDUCTUAL y una divergencia sin efecto pasaba.
    out, cerco = [], None
    for ln in text.split("\n"):
        m = _VALLA_RE.match(ln)
        if cerco is None:
            if m:
                cerco = m.group(0).strip()[0] * len(m.group(0).strip())
                out.append("")
                continue
        else:
            out.append("")
            if m and m.group(0).strip()[0] == cerco[0] and len(m.group(0).strip()) >= len(cerco):
                cerco = None
            continue
        out.append(ln)
    # --8<-- fin sin_vallas (cuerpo)
    return "\n".join(out)


# --8<-- secciones_revision (parser de secciones + seleccion) -- REPLICADO LITERAL en
# agent-kits/shared/ledger-lint.py (canonico) y como respaldo local en
# skills/jira-sync/scripts/jira-flow.py y agent-kits/shared/task-brief.py (sin este kit,
# ADR-016, jira-review-comments T-03-fix1). Declarado en agent-kits/shared/copias.json.
# ---------------------------------------------------------------------------------------------
# Parser UNICO de SECCIONES de revision + seleccion entre varias del mismo intento
# [jira-review-comments T-03-fix1, gaps #1/#2/#5]. Antes `jira-flow.py` y `task-brief.py` tenian
# CADA UNO su propio criterio de "que seccion es esta": `jira-flow` cortaba el cuerpo de una
# seccion en la siguiente cabecera de REVISION (no en el siguiente `## ` cualquiera), asi que el
# parrafo de contexto se tragaba fases enteras (bloques `### T-XX` de la fase siguiente) y una
# "mencion" casaba con celdas `Correccion`/`Evidencia` que citan otras tareas de contexto; ademas
# elegia la PRIMERA candidata que mencionaba la tarea, no la mas reciente. `task-brief.py` ni
# siquiera filtraba por fase: usaba el intento MAXIMO GLOBAL del ledger. Fuente unica: parsea
# TODAS las secciones de una vez (`secciones_revision`), calcula la mencion con el mismo criterio
# (`menciones`: solo cabecera+resumen y columna `Tarea`, nunca `Correccion`/`Evidencia`) y elige
# con el mismo criterio (`seleccionar_seccion`, `ultimo_intento_para`). `jira-flow.py` y
# `task-brief.py` importan este modulo y, si el kit no viaja con el paquete, replican estas
# funciones LITERALMENTE como respaldo local - DECLARADO en `agent-kits/shared/copias.json`
# (bloque `secciones_revision`, ADR-016): hay test que compara las cadenas.
_HDR_CUALQUIERA_RE = re.compile(r"^##[ \t]+.*$", re.M)


def split_fila_md(ln):
    """Divide una fila de tabla Markdown por `|`, ignorando los `|` dentro de un tramo
    `` `codigo` `` (una celda de gap puede citar una regex con alternancia `a|b|c`; un split
    ingenuo la trocearia). No es un parser Markdown completo: basta para code spans de una linea."""
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


def secciones_revision(texto):
    """Lista de TODAS las secciones `## Revision de dos lentes - intento N` del ledger, en orden
    de aparicion: [{"intento", "cabecera", "resumen", "filas", "inicio", "fin"}, ...]. `fin` es el
    siguiente encabezado `## ` de CUALQUIER tipo (o fin de fichero) - no el siguiente `##
    Revision`, que dejaba fases enteras dentro del cuerpo de una seccion (gap #1). Respeta
    `sin_vallas()`: una cabecera citada dentro de una valla de codigo no cuenta como seccion."""
    limpio = sin_vallas(texto)
    cabeceras = [m.start() for m in _HDR_CUALQUIERA_RE.finditer(limpio)]
    out = []
    for m in _REVISION_HDR_RE.finditer(limpio):
        intento = int(m.group(1))
        resumen = (m.group(2) or "").strip()
        fin = next((p for p in cabeceras if p > m.start()), len(limpio))
        cuerpo = limpio[m.end():fin]
        parrafo = []
        for ln in cuerpo.splitlines():
            s = ln.strip()
            if s.startswith("|"):
                break
            if s:
                parrafo.append(s)
        if parrafo:
            resumen = (resumen + " " + " ".join(parrafo)).strip()
        filas = []
        for ln in cuerpo.splitlines():
            s = ln.strip()
            if not s.startswith("|") or set(s.replace("|", "").strip()) <= {"-", " "}:
                continue
            celdas = split_fila_md(s)
            if len(celdas) < 6 or celdas[0] in ("#", "") or not re.match(r"^\d+$", celdas[0]):
                continue
            filas.append({"num": celdas[0], "grado": celdas[1], "gap": celdas[2],
                          "tarea": celdas[3], "correccion": celdas[4], "evidencia": celdas[5]})
        out.append({"intento": intento, "cabecera": m.group(0).strip(), "resumen": resumen,
                     "filas": filas, "inicio": m.start(), "fin": fin})
    return out


def ids_de_tarea(texto):
    """IDs `T-NN` citados en `texto` (regex `\\bT-\\d{2}\\b`), fuente UNICA de "que tareas cita
    una celda o una cabecera" (jira-review-comments T-03-fix2, gaps #14/#15/#17). Antes cada sitio
    -`menciones()` aqui, el filtro de filas de `revision`/`gaps` y de `aprobado` en `jira-flow.py`,
    `_gaps_pendientes_de_tarea` en `task-brief.py`- comparaba la celda `Tarea` con `==`/`in` sobre
    el texto ENTERO, asi que una celda combinada `T-02/T-04` (una fila de gap que afecta a dos
    tareas a la vez) no contaba para NINGUNA de las dos: `--task T-04` no encontraba su propia
    fila. Con esta funcion, `T-02/T-04` cuenta para T-02 Y para T-04 en TODOS los sitios por
    igual - nunca cuenta si el id aparece dentro de otra palabra mas larga (limite `\\b`) ni si
    solo aparece en `Correccion`/`Evidencia` (esta funcion no las mira; ver `menciones()`)."""
    return set(re.findall(r"\bT-\d{2}\b", texto))


def menciones(seccion):
    """IDs `T-NN` que una seccion MENCIONA, para elegir entre varias del mismo intento: SOLO la
    LINEA de cabecera (`seccion["cabecera"]`, una sola linea: nunca el parrafo de contexto que le
    sigue, que `secciones_revision` pega a `resumen` solo para renderizar el comentario) y la
    columna `Tarea` de sus filas - NUNCA `Correccion`/`Evidencia`, que citan tests y otras tareas
    de contexto y dan falsos positivos en un ledger real con fases que se referencian entre si
    (gap #1: una fila de la Fase 1 cita "T-04" en su celda `Correccion`; el parrafo de contexto de
    otra fase tambien puede citar "T-04" sin ser SU tarea)."""
    ids = ids_de_tarea(seccion["cabecera"])
    for f in seccion["filas"]:
        ids |= ids_de_tarea(f["tarea"])
    return ids


def seleccionar_seccion(secciones, intento, tareas):
    """(seccion, aviso) - entre las secciones de `secciones` con ese `intento`, prioriza en TRES
    niveles (jira-review-comments T-03-fix2, gap #14, con el ledger REAL de knowledge-services
    como caso de aceptacion: `T-04 --intento 2` tiene DOS candidatas con filas de T-04 - la Fase 2,
    su seccion PROPIA -cabecera "Fase 2 (T-04, T-05, T-06)"-, con 13 filas; y la Fase 3, que solo
    la cita en dos filas `T-02/T-04` como gap CRUZADO descubierto durante la revision de OTRA
    fase-):
      1) seccion PROPIA: alguna de `tareas` esta en la CABECERA -> entre esas, la ULTIMA (si mas
         de una fase, insolito, declarase la misma tarea en su cabecera). Gana SIEMPRE sobre una
         seccion ajena que solo la cite en una fila, tenga o no gaps propios (si no tiene filas es
         el caso legitimo "sin gaps para T-XX": una fase que cerro limpia esa tarea).
      2) sin seccion propia: seccion AJENA con FILAS que citan alguna de `tareas` (celda combinada
         `T-02/T-04` u otra) -> la ULTIMA de esas, sin aviso (gaps cruzados reales: FX2 de la ronda
         fix2, una fila `T-02/T-04` Critical sin secccion propia para ninguna de las dos).
      3) ninguna la menciona de ningun modo -> la ULTIMA de ese intento, con aviso.
    Sin candidatas para ese `intento` -> (None, None). Sin `tareas`, o con UNA SOLA candidata para
    ese intento (ledger de una sola fase: no hay ambiguedad que resolver) -> esa candidata, sin
    aviso."""
    candidatas = [s for s in secciones if s["intento"] == intento]
    if not candidatas:
        return None, None
    if not tareas or len(candidatas) == 1:
        return candidatas[-1], None
    tareas_set = set(tareas)
    propias = [s for s in candidatas if ids_de_tarea(s["cabecera"]) & tareas_set]
    if propias:
        return propias[-1], None
    ajenas = [s for s in candidatas
              if any(ids_de_tarea(f["tarea"]) & tareas_set for f in s["filas"])]
    if ajenas:
        return ajenas[-1], None
    aviso = (f"el intento {intento} tiene {len(candidatas)} secciones «## Revisión de dos "
             f"lentes — intento {intento}» (probablemente una por fase) y ninguna menciona "
             f"{', '.join(tareas)} en la cabecera o en la columna Tarea: se usa la última "
             f"(más reciente) — revisa si es la sección correcta")
    return candidatas[-1], aviso


def _menciones_efectivas(secciones):
    """`menciones()` de cada seccion, EN ORDEN, con herencia para las rondas de cierre ANONIMAS
    (`## Revision de dos lentes - intento N: sin gaps`, sin ningun T-NN en la cabecera NI filas):
    heredan las menciones de la seccion INMEDIATAMENTE anterior, porque un "sin gaps" de cierre no
    tiene por que repetir el nombre de la tarea que ya cerro limpia (ledger de una sola fase:
    intento 1 cita T-01 en sus filas, intento 2 "sin gaps" no cita nada y aun asi es SU cierre).
    Una seccion que si declara tareas en la cabecera (aunque sean DE OTRA fase, p.ej. "Fase 2
    (T-04)") NO es anonima y NUNCA hereda - es la fase de otra tarea, no un cierre generico (gap
    #16 de jira-review-comments fix2: numeracion CONTINUA entre fases, Fase 1 intento 1 (T-01) /
    Fase 2 intento 2 (T-04), sin repetir numero; el intento 2 de Fase 2 no puede "servir" de cierre
    para T-01). Tampoco hereda si hay una FRONTERA estructural con la seccion anterior - otro
    encabezado `## ` (una `## Fase N`, un `### T-XX` nuevo...) entre el `fin` de la seccion previa
    y el `inicio` de esta (`secciones_revision` ya calcula `fin` como el siguiente `## ` de
    CUALQUIER tipo): sin esa frontera, "sin gaps" tras "sin gaps" en cabeceras igual de anonimas
    (p.ej. "Fase 2 - sin gaps" dos veces, sin ningun T-NN en ninguna) haria que la Fase 2 heredara
    las menciones de la Fase 1 anterior solo por venir despues en el fichero."""
    out = []
    previa = set()
    fin_previa = None
    for s in secciones:
        m = menciones(s)
        anonima = not ids_de_tarea(s["cabecera"]) and not s["filas"]
        sin_frontera = fin_previa is not None and fin_previa == s["inicio"]
        eff = previa if (not m and anonima and sin_frontera) else m
        out.append(eff)
        previa = eff
        fin_previa = s["fin"]
    return out


def ultimo_intento_para(secciones, tareas):
    """Intento MAS ALTO relevante para `tareas`, restringido a las secciones cuyas menciones
    EFECTIVAS (`_menciones_efectivas()`: `menciones()` con herencia solo para cierres anonimos, ver
    arriba) casan con `tareas` - SIN el atajo anterior de usar el maximo GLOBAL cuando los numeros
    de intento no se repiten (gap #16 de jira-review-comments fix2: con numeracion CONTINUA entre
    fases, el atajo cogia la ultima fase aunque no mencionara la tarea pedida y dejaba inalcanzable
    el aviso de "ninguna seccion menciona"). El maximo GLOBAL podia venir de otra fase sin que la
    tarea pedida tenga nada que ver (gap #2: `aprobado` concedia Done con un Critical pendiente de
    OTRA fase). `None` si ninguna seccion menciona esas tareas, ni directa ni por herencia (sin
    evidencia: rechazo, no adivinar)."""
    if not secciones:
        return None
    tareas_set = set(tareas)
    efectivas = _menciones_efectivas(secciones)
    candidatas = [s["intento"] for s, eff in zip(secciones, efectivas) if eff & tareas_set]
    if not candidatas:
        return None
    return max(candidatas)


# jira-review-comments T-03-fix3, gap #20 — criterio de "gap pendiente" de una fila (misma lista
# que ya usaba `evidencia_aprobado`: sin corrección registrada, o placeholder de que sigue
# abierta; `descartado (rebatido)` cierra la fila aunque no haya código). Antes vivía SOLO en
# `jira-flow.py` (privado, `_gap_pendiente`); ahora es canónico aquí porque `filas_pendientes_de_
# tarea` (abajo) lo necesita y la usan los dos llamadores por igual.
GAP_PENDIENTE_RE = re.compile(r"^(?:|-+|—|–|n/?a|todo|pendiente\b.*|sin corregir\b.*|\?+)$", re.I)
GAP_REBATIDO_RE = re.compile(r"rebatid|descartad", re.I)


def gap_pendiente(fila):
    """True si la fila de gap NO tiene corrección registrada (celda vacía o placeholder) y no está
    `descartado (rebatido)`: una tarea con gaps así NO puede pasar a Done."""
    correccion = re.sub(r"[`*_]", "", (fila.get("correccion") or "")).strip()
    evidencia = (fila.get("evidencia") or "").strip()
    if GAP_REBATIDO_RE.search(correccion) or GAP_REBATIDO_RE.search(evidencia):
        return False
    return bool(GAP_PENDIENTE_RE.match(correccion))


def filas_pendientes_de_tarea(secciones, tarea):
    """(intento, [filas]) — evidencia para DECIDIR sobre `tarea` (evento `aprobado`; gaps
    pendientes del brief de `task-brief.py`; jira-review-comments T-03-fix3, gap #20).

    Dos usos, dos reglas (arbitraje fix3, sustituye a (2) del fix2 para DECIDIR — PUBLICAR un
    comentario de un intento concreto sigue siendo `seleccionar_seccion()`/`seccion_revision()`,
    cabecera-primero, sin cambios):
      - **Publicar un intento** (`revision`/`gaps`): UNA sección por intento, la dueña de la fase
        (`seleccionar_seccion`).
      - **Decidir sobre una tarea** (esta función): UNIÓN de TODAS las filas de TODAS las secciones
        de revisión que MENCIONAN `tarea` EFECTIVAMENTE (`_menciones_efectivas()`: `menciones()` —
        cabecera o columna `Tarea` — con herencia solo para cierres anónimos, igual que
        `ultimo_intento_para`), en
        CUALQUIER intento y CUALQUIER fase — no solo la sección "dueña". Antes `evidencia_aprobado`
        miraba UNA sola sección por intento (cabecera-primero, vía `seccion_revision`): con la
        sección propia de la fase limpia («Fase 2 (T-04, T-05) — sin gaps») y un Critical cruzado
        `T-04/T-07` descubierto en la revisión de OTRA fase del MISMO intento, la regla
        cabecera-primero elegía la limpia y `aprobado T-04` concedía Done sin ver el Critical.

    Devuelve `(intento_reportado, filas)`: `intento_reportado` es el intento MÁS ALTO entre las
    secciones que MENCIONAN `tarea`; `filas` son SOLO las PENDIENTES (`gap_pendiente()`) de esas
    secciones, cada una anotada con `seccion` (su cabecera) e `intento` de origen, para que el
    llamador cite fichero+sección al rechazar. `(None, [])` si NINGUNA sección menciona `tarea` —
    sin evidencia, no se adivina."""
    if not secciones:
        return None, []
    efectivas = _menciones_efectivas(secciones)
    citantes = [s for s, eff in zip(secciones, efectivas) if tarea in eff]
    if not citantes:
        return None, []
    intento = max(s["intento"] for s in citantes)
    pendientes = []
    for s in citantes:
        for f in s["filas"]:
            if tarea in ids_de_tarea(f["tarea"]) and gap_pendiente(f):
                pendientes.append(dict(f, seccion=s["cabecera"], intento=s["intento"]))
    return intento, pendientes


# --8<-- fin secciones_revision


def _gaps_pendientes_de_tarea(tasks_text, tid):
    """{"intento": N, "filas": [...]} con los gaps PENDIENTES de `tid`, UNIÓN de TODAS las
    secciones `## Revision de dos lentes - intento N` que MENCIONAN `tid` EFECTIVAMENTE, en
    CUALQUIER intento y CUALQUIER fase (no solo la sección "dueña") - o None si no hay ninguna
    sección de revisión, si ninguna sección menciona `tid`, o si esa unión no deja ninguna fila
    PENDIENTE (revisión limpia: nada que inyectar). Delega en `agent-kits/shared/ledger-lint.py`
    (fuente única del parser + criterio de selección, gaps #1/#2/#5/#20 de jira-review-comments:
    antes este brief usaba el intento MÁXIMO GLOBAL y una coincidencia EXACTA de columna (gaps
    #1/#2/#5); luego, UNA sola sección por intento cabecera-primero (gap #20) - con una sección
    propia limpia y un gap cruzado en OTRA sección del MISMO intento, el brief no lo mostraba). Si
    el kit no viaja con el paquete portable, usa la réplica local sentinelada más arriba."""
    ledger_lint = _ledger_lint_mod()
    if ledger_lint is not None:
        secciones = ledger_lint.secciones_revision(tasks_text)
        intento, filas = ledger_lint.filas_pendientes_de_tarea(secciones, tid)
    else:
        secciones = secciones_revision(tasks_text)
        intento, filas = filas_pendientes_de_tarea(secciones, tid)
    if intento is None or not filas:
        return None
    filas = [{"grado": f["grado"], "gap": f["gap"], "correccion": f["correccion"],
              "evidencia": f["evidencia"]} for f in filas]
    return {"intento": intento, "filas": filas}


def _secciones_por_encabezado(texto):
    """Particiona `texto` en secciones de nivel `## ` (gap B-6, intento 3 pasada acotada): cada
    sección es su línea de cabecera hasta la siguiente `## ` (excluida) o el final del texto. Es la
    misma partición que mediría el orquestador desde FUERA de este script (por eso el aviso de
    `main()` la usa en vez de re-estimar cada sección con el fragmento de origen: `len(diseno[1])`
    omite la cabecera y el pie que `main()` añade al montar el brief, y una tabla de gaps
    reconstruida a mano no es el formato real que se imprime)."""
    lineas = texto.split("\n")
    idxs = [i for i, ln in enumerate(lineas) if ln.startswith("## ")]
    secciones = []
    for j, i in enumerate(idxs):
        fin = idxs[j + 1] if j + 1 < len(idxs) else len(lineas)
        secciones.append((lineas[i], "\n".join(lineas[i:fin])))
    return secciones


def _longitud_seccion(secciones, prefijo):
    """Suma la longitud de las secciones (de `_secciones_por_encabezado`) cuya cabecera empieza por
    `prefijo` — permite sumar dos cabeceras distintas (p.ej. «## La tarea» + «## Gaps pendientes»
    para «tarea+gaps», gap B-6) o medir una sola («## Diseño»)."""
    return sum(len(txt) for cab, txt in secciones if cab.startswith(prefijo))


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


def _parse_args(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("carpeta", help="carpeta de la iniciativa (docs/roadmap/<fecha>-<slug>)")
    ap.add_argument("tarea", help="ID de la tarea (T-XX)")
    ap.add_argument("--constitucion", default=None,
                    help="ruta de la constitución (default: se busca en <raíz del repo>/docs/"
                         "CONSTITUTION.md derivada de la carpeta, y luego docs/CONSTITUTION.md del cwd)")
    ap.add_argument("--sin-lint", action="store_true",
                    help="saltar la validación del ledger (solo para tests)")
    ap.add_argument("--personas-dir", default=None,
                    help="carpeta del CATÁLOGO de personas, segundo escalón de la cascada "
                         "(default: personas/ junto al script). El primer escalón, "
                         "`.claude/personas/<tipo>.md` del proyecto, no se configura: se deriva "
                         "siempre de la carpeta de la iniciativa")
    ap.add_argument("--tdd", action="store_true", help="fuerza la sección TDD (como si dev.json tuviera tdd: true)")
    ap.add_argument("--dev-json", default=None, help="ruta explícita de .claude/dev.json (default: derivada de la carpeta)")
    ap.add_argument("--knowledge-find", default=None,
                    help="ruta de knowledge-find.py (default: el del mismo kit; solo para tests)")
    return ap.parse_args(argv)


def _validar_ledger(tasks_p, sin_lint):
    """`None` si es válido para seguir; en caso contrario, el exit code a devolver."""
    if not os.path.isfile(tasks_p):
        print(f"❌ no existe {tasks_p}", file=sys.stderr)
        return 1
    if sin_lint:
        return None
    lint = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ledger-lint.py")
    if not os.path.isfile(lint):
        return None
    r = subprocess.run([sys.executable, lint, tasks_p],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print("❌ ledger inválido — arregla tasks.md antes de despachar "
              f"(ledger-lint exit {r.returncode}):\n{r.stdout}{r.stderr}",
              file=sys.stderr)
        return 2
    return None


def _seccion_cabecera(tid, carpeta, tasks_p, fase):
    out = [f"# Brief de implementación — {tid}", ""]
    out.append(f"Iniciativa: `{carpeta}` · Ledger canónico: `{tasks_p}`. "
               "**NO toques el ledger**: lo actualiza el orquestador; tú limítate a "
               "reportar tu estado final (contrato de abajo).")
    if fase:
        out += ["", "## Contexto de fase", "", f"> {fase.lstrip('# ').strip()}"]
    return out


def _preparar_persona(chunk, args, out_len_tras_cabecera):
    """Resuelve la cascada de persona (opcional, por `- **Tipo**:`) SIN insertarla todavía (gap B-3,
    revisión intento 2): el tope efectivo depende del margen que de verdad quede tras montar el RESTO
    del brief, así que `presupuesto_persona()` la inserta al final en el índice que aquí se calcula."""
    tipo = _tipo_de_tarea(chunk)
    if not tipo:
        return tipo, None, None, None
    personas_dir = args.personas_dir or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "personas")
    persona_contenido, persona_ruta = _persona_cascada(tipo, personas_dir, carpeta=args.carpeta)
    insert_idx = out_len_tras_cabecera if persona_contenido else None
    return tipo, persona_contenido, persona_ruta, insert_idx


def _resolver_verificacion(chunk):
    """Lee la `Verificación` declarada ANTES de emitir la tarea, porque el bloque de la tarea la
    sustituye por un puntero a la sección (una vez en el brief, no dos). Devuelve `(verif, chunk_brief)`."""
    verif = _verificacion_de_tarea(chunk)
    if verif:
        items_red = [x for x in verif["items"] if _es_evidencia_red(x)]
        verif["items"] = [x for x in verif["items"] if not _es_evidencia_red(x)]
        verif["omitidos_red"] = len(items_red)
        if not verif["items"]:
            # solo evidencia RED: no hay comando que ejecutar; la sección lo dice como «no declara»
            verif = None
    chunk_brief = _chunk_sin_presupuesto(_chunk_sin_verificacion(chunk, len(verif["items"])) if verif else chunk)
    return verif, chunk_brief


def _seccion_tarea_y_gaps(chunk_brief, tasks_text, tid):
    out = ["", "## La tarea (de tasks.md — tus criterios de aceptación son EL contrato)",
           "", chunk_brief]
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
    return out


def _seccion_verificacion(verif):
    if not verif:
        return ["## Verificación", "",
                "> (la tarea no declara `Verificación`: propón una en tu informe — un comando y su resultado "
                "esperado — y ejecútala antes de reportar `DONE`.)", ""]
    out = ["## Verificación (ejecútala al terminar y pega la salida)", ""]
    out += [f"- {item}" for item in verif["items"]]
    out += ["",
            "Ejecuta EXACTAMENTE esa verificación (todos los ítems) cuando creas haber terminado y pega su "
            "salida real en tu informe (no «debería pasar»: el resultado). Si no pasa, la tarea NO está `DONE`."]
    if verif["ejecutada"]:
        out += ["", f"> Verificación ya ejecutada antes ({verif['ejecutada'].split(' — ')[0]}): "
                    "**re-ejecútala** — la salida grabada en el ledger es de otra sesión, no vale como evidencia tuya."]
    if verif.get("omitidos_red"):
        out += ["", f"> {verif['omitidos_red']} ítem(s) `RED: …` de la ejecución anterior omitido(s): son evidencia "
                    "del rojo de otra sesión, no comandos; si TDD está activo, produce tu propio rojo."]
    out += [""]
    return out


def _seccion_memoria(carpeta, chunk, tipo, knowledge_find):
    # memoria técnica (memory-retrieval T-05): aciertos enrutados por Tipo/título/iniciativa, con tope y en silencio
    memoria = _memoria_tecnica(carpeta, chunk, tipo, knowledge_find)
    return [memoria] if memoria else []      # un solo elemento: quitarlo deja el brief byte a byte como sin memoria (CA-09)


def _seccion_diseno_y_arquitectura(carpeta, plan_p):
    out = []
    diseno = _design_elegida(carpeta)
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
    return out


def _seccion_constitucion(args):
    # ruta explícita, o derivada de la carpeta de la iniciativa (docs/roadmap/<slug> →
    # <raíz>/docs/CONSTITUTION.md), o el cwd como último recurso
    candidatas = ([args.constitucion] if args.constitucion else [
        os.path.join(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(args.carpeta)))), "docs", "CONSTITUTION.md"),
        os.path.join("docs", "CONSTITUTION.md"),
    ])
    const_p = next((c for c in candidatas if c and os.path.isfile(c)), None)
    if not const_p:
        return []
    const = open(const_p, encoding="utf-8", errors="replace").read()
    return ["## Constitución del proyecto (principios OBLIGATORIOS)", "", const.rstrip(), ""]


def _seccion_tdd(args):
    if args.tdd or _tdd_activo(args.carpeta, args.dev_json):
        return ["", TDD_BRIEF]
    return []


def presupuesto_persona(out, persona_insert_idx, tipo, persona_ruta, persona_contenido, carpeta):
    """Función única para las TRES reglas del presupuesto de la persona de dominio (revisión intento 3:
    una cuarta constante, `PERSONA_TOPE_MINIMO_UTIL`, resultó código muerto y se retiró):
    `PERSONA_TOPE_CHARS` (techo de sanidad), `PERSONA_SUELO_CHARS` (mínimo de contenido garantizado) y
    el margen dinámico que de verdad queda tras montar el RESTO del brief (`out` ya completo salvo la
    persona). El overhead del envoltorio se MIDE con una sonda de un carácter, no se estima a mano: una
    fórmula manual desajustada fue justo lo que hizo que el gap B-1 tumbase este mismo tope en dos
    tareas de `2026-09-04-memory-retrieval`. Devuelve `(out, resto_sin_persona)`: si no hay persona que
    insertar, `resto_sin_persona` es `None` (el llamador usa `len(texto)` como causa del exceso)."""
    if persona_insert_idx is None:
        return out, None
    resto = len("\n".join(out))
    ruta_aviso = _ruta_para_aviso(persona_ruta, carpeta)
    sonda = _persona_delimitada(tipo, "P", ruta_aviso, BRIEF_TOPE_CHARS)
    out_con_sonda = out[:persona_insert_idx] + sonda + out[persona_insert_idx:]
    overhead = len("\n".join(out_con_sonda)) - resto - 1  # -1: el carácter "P" de la sonda
    margen_real = BRIEF_TOPE_CHARS - resto - overhead
    # opción A (gap B-3, intento 3): el suelo manda sobre el margen cuando el margen se queda corto —
    # nunca al revés. Si sobra margen de verdad (por encima del suelo), se usa ese margen (capado por
    # PERSONA_TOPE_CHARS); si no, la persona conserva como mínimo PERSONA_SUELO_CHARS de CONTENIDO
    # aunque eso empuje el brief por encima de BRIEF_TOPE_CHARS (gap B-4: el suelo es del contenido, la
    # nota de recorte va aparte).
    tope_cuerpo = max(PERSONA_SUELO_CHARS, min(PERSONA_TOPE_CHARS, margen_real))
    bloque = _persona_delimitada(tipo, persona_contenido, ruta_aviso, tope_cuerpo)
    if bloque:
        out[persona_insert_idx:persona_insert_idx] = bloque
    return out, resto


def _avisa_si_excede_tope(tid, texto, resto_sin_persona):
    # aviso con causa MEDIDA sobre el brief YA MONTADO (gap B-6): particiona `texto` por sus líneas
    # `## ` — es lo que mediría el orquestador desde fuera — en vez de re-estimar cada sección con su
    # fragmento de origen (`len(diseno[1])` omite cabecera y cierre; una reconstrucción a mano del
    # formato de la tabla de gaps no es el formato real).
    if len(texto) <= BRIEF_TOPE_CHARS:
        return
    secciones = _secciones_por_encabezado(texto)
    len_diseno = _longitud_seccion(secciones, "## Diseño")
    len_memoria = _longitud_seccion(secciones, "## Memoria")
    len_tarea_gaps = (_longitud_seccion(secciones, "## La tarea")
                       + _longitud_seccion(secciones, "## Gaps pendientes"))
    len_persona = _longitud_seccion(secciones, "## Persona de dominio")
    # gap B-5: la causa se bifurca sobre el RESTO sin persona, no se afirma a ciegas ni el suelo ni un
    # exceso preexistente. Si el resto YA cabía en el tope, el suelo de la persona es la ÚNICA causa del
    # exceso — decirlo, no exonerar a la persona con una frase falsa. Si el resto YA se pasaba del tope
    # sin persona, el exceso es preexistente (diseño/memoria/tarea+gaps) y la persona no es la causa.
    resto = resto_sin_persona if resto_sin_persona is not None else len(texto)
    if resto <= BRIEF_TOPE_CHARS:
        print(f"⚠️  brief de {tid}: {len(texto)} caracteres, por encima de BRIEF_TOPE_CHARS="
              f"{BRIEF_TOPE_CHARS} (CA-08). Causa: la persona en su suelo ({len_persona}) empuja "
              f"el brief a {len(texto)} > {BRIEF_TOPE_CHARS}; decisión opción A (2026-09-09): la "
              "persona no se recorta por debajo del suelo.", file=sys.stderr)
    else:
        exceso = resto - BRIEF_TOPE_CHARS
        print(f"⚠️  brief de {tid}: {len(texto)} caracteres, por encima de BRIEF_TOPE_CHARS="
              f"{BRIEF_TOPE_CHARS} (CA-08). Causa: exceso preexistente de {exceso} caracteres SIN "
              f"persona (diseño={len_diseno} memoria={len_memoria} tarea+gaps={len_tarea_gaps}); "
              f"la persona ({len_persona}) no es la causa. No lo arregla este script; el "
              "subagente recibe el brief igual.", file=sys.stderr)


def _resolver_rutas(args):
    """Deriva las rutas del ledger/plan de la iniciativa y valida el ledger. Devuelve `(tasks_p,
    plan_p, exit_code)`; `exit_code` no `None` cuando hay que abortar (el llamador solo comprueba eso)."""
    tasks_p = os.path.join(args.carpeta, "tasks.md")
    plan_p = os.path.join(args.carpeta, "improvement-plan.md")
    return tasks_p, plan_p, _validar_ledger(tasks_p, args.sin_lint)


def _tarea_no_encontrada(tid, tasks_p):
    print(f"❌ tarea {tid} no encontrada en {tasks_p}", file=sys.stderr)
    return 1


def _cargar_chunk(tasks_p, tid):
    """Lee `tasks.md` (ya validado por `_resolver_rutas`) y extrae el chunk de la tarea. Devuelve
    `(tasks_text, chunk, fase, exit_code)`; `exit_code` no `None` cuando hay que abortar."""
    tasks_text = open(tasks_p, encoding="utf-8", errors="replace").read()
    chunk, fase = _seccion_tarea(tasks_text, tid)
    if not chunk:
        return tasks_text, None, None, _tarea_no_encontrada(tid, tasks_p)
    return tasks_text, chunk, fase, None


def main(argv=None):
    args = _parse_args(argv)
    tid = args.tarea.upper()
    if not re.fullmatch(r"T-\d+", tid):
        print(f"❌ id de tarea inválido: {args.tarea} (esperado T-XX)", file=sys.stderr)
        return 1
    tasks_p, plan_p, exit_code = _resolver_rutas(args)
    if exit_code is not None:
        return exit_code
    tasks_text, chunk, fase, exit_code = _cargar_chunk(tasks_p, tid)
    if exit_code is not None:
        return exit_code

    out = _seccion_cabecera(tid, args.carpeta, tasks_p, fase)
    tipo, persona_contenido, persona_ruta, persona_insert_idx = _preparar_persona(chunk, args, len(out))
    verif, chunk_brief = _resolver_verificacion(chunk)

    out += _seccion_tarea_y_gaps(chunk_brief, tasks_text, tid)
    out += _seccion_verificacion(verif)
    out += _seccion_memoria(args.carpeta, chunk, tipo, args.knowledge_find)
    out += _seccion_diseno_y_arquitectura(args.carpeta, plan_p)
    out += _seccion_constitucion(args)
    out += _seccion_tdd(args)
    out += ["", CONTRATO]

    out, resto_sin_persona = presupuesto_persona(
        out, persona_insert_idx, tipo, persona_ruta, persona_contenido, args.carpeta)

    texto = "\n".join(out)
    _avisa_si_excede_tope(tid, texto, resto_sin_persona)
    print(texto)
    return 0


if __name__ == "__main__":
    sys.exit(main())
