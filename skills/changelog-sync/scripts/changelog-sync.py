#!/usr/bin/env python3
"""
changelog-sync.py — entradas `[Unreleased]`/`[Sin publicar]` desde los ledgers CERRADOS.

(Iniciativa superiority T-02, lección LES-012: el papeleo mecánico del release lo hace un
script, no el modelo. Aquí: el CHANGELOG se deriva del ledger, que es la fuente única del
progreso — no de la memoria de la conversación.)

Qué hace
  1. Recorre `docs/roadmap/<fecha>-<slug>/tasks.md` y toma los ledgers con `estado: completado`
     en el frontmatter (los legacy sin frontmatter se ignoran con aviso).
  2. Descarta los que YA aparecen en el CHANGELOG (busca `` `<slug>` `` en el texto) → idempotente.
  3. Por cada ledger pendiente escribe, justo bajo la cabecera Unreleased y en orden de fecha,
     una subsección `### <Categoría> — \\`<slug>\\` initiative (<fecha>)` (EN) /
     `### <Categoría> — iniciativa \\`<slug>\\` (<fecha>)` (ES) con UN bullet por tarea `T-XX`:
     título + el resumen de la ESCALERA de `resumen()` + hasta ARCHIVOS_MAX `Archivos` clave.
  4. Categoría por heurística sobre `descripcion:` y títulos (fix/corrige/saldar/bug → Fixed;
     cambia/retira/renombra/migra/sustituye → Changed; resto Added), sobreescribible con
     `changelog: Added|Changed|Fixed` en el frontmatter del ledger.

Uso:  changelog-sync.py [--root <repo>] [--dry-run] [--only <slug>] [--check] [--json]
      changelog-sync.py --medicion [--json]   (las cifras que la doc afirma, medidas)
Exit: 0 ok (o nada pendiente) · 1 con `--check` y entradas pendientes · 2 error de uso
      (no hay CHANGELOG.md/CHANGELOG.es.md, o `--only` sin ledger cerrado que case).

NO hace: no crea la sección de versión (eso es `scripts/release.py`), no inventa alcance, no
traduce con modelo (el bullet ES y EN salen del MISMO texto del ledger, que está en español;
afinar la redacción es trabajo humano posterior — la skill lo explica).
"""
import argparse
import contextlib
import json
import os
import re
import sys

# Consola Windows (cp1252) o tuberías: reconfigurar ANTES de leer o imprimir nada (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

LEDGER_GLOB = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)$")
CHANGELOGS = {  # fichero → (cabecera de la sección abierta, plantilla de subsección)
    "CHANGELOG.md": ("## [Unreleased]", "### {cat} — `{slug}` initiative ({fecha})"),
    "CHANGELOG.es.md": ("## [Sin publicar]", "### {cat} — iniciativa `{slug}` ({fecha})"),
}
CATS = ("Added", "Changed", "Fixed")

# --- Topes del bullet (constantes, no números repartidos por el código) ---
# RESUMEN_MAX = 200: elegido MIDIENDO los 13 ledgers cerrados del repo — 63 tareas (medición en
# `skills/changelog-sync/references/medicion-escalera.md`). Con 160 se pierde la frase útil más
# larga que hay (192 caracteres, `windows-console/T-02`); con 240 entran enumeraciones de tres
# cláusulas (237 y 212 caracteres) que se leen como párrafo, que es justo lo que se quería quitar.
# 200 ≈ dos frases de español técnico, que es el objetivo declarado del bullet.
RESUMEN_MAX = 200
RESUMEN_FRASES_MAX = 2      # el campo `Changelog:` admite una o DOS frases; el resto se recorta
ARCHIVOS_MAX = 3            # ficheros que se listan en el paréntesis
# Con más ficheros tocados que el DOBLE de los que se listan, mostrar 3 no informa (el lector
# creería que son todos): se omite el paréntesis. Medido: 24/63 tareas conservan lista, 39 no.
ARCHIVOS_MAX_TOCADOS = 2 * ARCHIVOS_MAX
CORTE_MIN_PALABRAS = 5      # palabras fuera de `código` para que un corte sea una idea completa
# Cortes de nivel superior y parejas que NO se abren para cortar dentro (código, paréntesis,
# corchetes y comillas latinas): la mayoría de las Descripciones de este repo empiezan por la ruta
# del fichero entre acentos graves, y cortar ahí daría una lista de ficheros en vez de un resumen.
CORTES = ":;—–"
ABRE, CIERRA = "([{«", ")]}»"
RE_FIXED = re.compile(r"\b(fix|corrig\w+|correcci[oó]n|saldar|saldad\w+|bug|regresi[oó]n)\b", re.I)
RE_CHANGED = re.compile(r"\b(cambia\w*|retira\w*|renombra\w*|migra\w*|sustituy\w*|reemplaza\w*)\b", re.I)

# --- Campos del ledger. `[^\S\n]*` (espacio o tab, NUNCA salto de línea) y no `\s*`: con `re.M`,
# `^- \*\*X\*\*\s*:\s*(.*)$` se come el `\n` y captura la LÍNEA SIGUIENTE cuando el campo está
# vacío, así que un `- **Changelog**:` sin texto publicaba `- **Estado**: completado` (o la fila de
# tabla que hubiera debajo) como resumen de la tarea. `re.M` cambia el anclaje de `^`/`$`, no `\s`.
#
# CHANGELOG_FIELD_PATTERN es copia LITERAL del patrón de `agent-kits/shared/ledger-lint.py`
# (`CHANGELOG_FIELD_PATTERN`), para cuando la skill viaja sola en el paquete portable.
# `test_changelog_sync.py` compara las dos cadenas y afirma que los dos parsers reconocen los
# MISMOS casos: antes este exigía `- ` al principio de línea y el del linter aceptaba indentación y
# espaciado libres, así que un `-  **Changelog**: …` (dos espacios, Markdown normal) pasaba el
# linter y este script lo descartaba en silencio, devolviendo el bullet a la `Descripción` cruda.
CHANGELOG_FIELD_PATTERN = \
    r"^[^\S\n]*-[^\S\n]*\*\*Changelog\*\*[^\S\n]*:[^\S\n]*(?P<txt>.*)$"
RE_CAMPO_CHANGELOG = re.compile(CHANGELOG_FIELD_PATTERN, re.M | re.I)
RE_CAMPO_DESC = re.compile(r"^[^\S\n]*-[^\S\n]*\*\*Descripci[oó]n\*\*[^\S\n]*:[^\S\n]*(.*)$", re.M)
RE_CAMPO_ARCH = re.compile(r"^[^\S\n]*-[^\S\n]*\*\*Archivos\*\*[^\S\n]*:[^\S\n]*(.*)$", re.M)
# Cualquier `## ` cierra el bloque de la tarea — MISMO criterio que `ledger-lint.py` (`close_task()`
# en `^##\s`). Sin esto, todo lo que va tras la última `### T-XX` (`## Notas de cierre`, `## Resumen
# de progreso`, la sección de revisión, apéndices) quedaba DENTRO del bloque de la última tarea, y
# un `- **Changelog**:` citado ahí como ejemplo se publicaba como resumen de esa tarea.
RE_FIN_BLOQUE = re.compile(r"^##\s", re.M)

# --- Criterios REPLICADOS LITERAL de `agent-kits/shared/ledger-lint.py` (paquete portable sin el
# kit). La suite compara las tres cadenas byte a byte y enfrenta los dos PARSERS sobre bloques de
# ledger completos, no dos regex sobre una línea suelta: el test del intento 1 comparaba las regex
# y por eso no cazó que un campo indentado bajo `- **Verificación**:` lo publicaba el generador y
# el linter lo daba por ausente.
#
# (a) Valla de código: `^##` DENTRO de un bloque ``` no cierra nada. Un `## Ejemplo` citado en una
#     valla ```markdown cortaba la tarea y los dos parsers perdían EN SILENCIO un campo real
#     escrito debajo.
VALLA_PATTERN = r"^[^\S\n]*(?:`{3,}|~{3,})"
# (b) Campos del bloque de una tarea. Una línea que es uno de ellos NO es prosa de continuación ni
#     ítem de la sub-lista de `Verificación`, con o sin la viñeta `- ` y con cualquier indentación.
CAMPO_LEDGER_PATTERN = (r"^[^\S\n]*(?:[-*+][^\S\n]*)?\*\*(?:Changelog|Descripci[oó]n|Archivos|"
                        r"Estado|Verificaci[oó]n|Tiempo[^*]*|Supervisi[oó]n|Notas|"
                        r"Criterios[^*]*)\*\*")
# (c) Continuación indentada del campo: una persona parte una frase larga en dos líneas y el
#     Markdown la lee como un solo párrafo. Se absorbe (unida por un espacio) en vez de perderla en
#     silencio — pero SOLO si es prosa: quedan fuera las viñetas, las listas numeradas, las filas
#     de tabla, las citas, los comentarios HTML, el código a 4 espacios y los campos del ledger.
#     Sin esas guardas, `  1. \`pytest -q\`` bajo `- **Archivos**:` convertía comandos en ficheros
#     (`archivos=[…, 'pytest -q', 'ruff']`) y un `  **Estado**: completado` tragado dejaba
#     `estado=None` en el linter.
CONTINUACION_PATTERN = r"^[ \t]{1,3}(?![-*+>|]\s|\d+[.)]\s|<!--|\|)\S"
RE_VALLA = re.compile(VALLA_PATTERN)
RE_CAMPO_LEDGER = re.compile(CAMPO_LEDGER_PATTERN, re.I)
RE_CONTINUACION = re.compile(CONTINUACION_PATTERN)


def sin_vallas(text):
    """`text` con las líneas DENTRO de una valla de código vaciadas (mismo número de líneas, para
    que los números no se muevan). Réplica del criterio de `ledger-lint.py` (`sin_vallas`)."""
    out, cerco = [], None
    for ln in text.split("\n"):
        m = RE_VALLA.match(ln)
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
    return "\n".join(out)


def es_continuacion(ln):
    """¿`ln` es la continuación indentada (prosa) del campo anterior?"""
    return bool(RE_CONTINUACION.match(ln)) and not RE_CAMPO_LEDGER.match(ln)
# Un placeholder de plantilla sin sustituir NO es un resumen escrito: se ignora (la escalera sigue
# bajando) y se avisa. Sin esto, el `{{OPCIONAL, lo rellena quien CIERRA la tarea: …}}` de
# `agent-kits/planner/templates/tasks.md` llegaba LITERAL al CHANGELOG.
#
# PLACEHOLDER_PATTERN es copia LITERAL del patrón de `agent-kits/shared/ledger-lint.py`, y
# `es_placeholder()` replica su criterio; la suite compara las dos cadenas byte a byte y las dos
# funciones sobre la misma tabla de casos. El criterio es «el campo ES el placeholder», NO «lo
# menciona»: en un repo cuyas plantillas van llenas de `{{…}}`, un `{{…}}` CITADO es texto humano
# legítimo, y descartarlo era pérdida silenciosa de lo que escribió una persona — justo lo que la
# escalera declara no hacer. Medido antes del arreglo, los dos casos se descartaban y el aviso
# diagnosticaba «placeholder sin sustituir»:
#   «Ahora la plantilla del planner trae `{{qué cambia para quien USA el proyecto}}` en vez del
#    párrafo largo.»          → descartado (¡y es la frase que T-06 escribiría sobre su cambio!)
#   «El generador acepta {{slug}} y {{fecha}} en el nombre de la sección.»   → descartado
PLACEHOLDER_PATTERN = r"\{\{.*?\}\}"
RE_PLACEHOLDER = re.compile(PLACEHOLDER_PATTERN, re.S)
# Puntuación y decoración que no cuenta como prosa propia al decidir si el campo ES el placeholder.
PLACEHOLDER_RELLENO = " \t\n.,;:!?—–·-*_`\"'()[]{}«»"

# Abreviaturas que NO cierran frase. `FIN_FRASE` reconoce el fin de frase por «punto + espacio +
# apertura de frase», así que el punto de una abreviatura seguida de palabra capitalizada le parecía
# fin de frase: medido, un campo de EXACTAMENTE dos frases («… el orden Sr. Pérez en la firma del
# comentario. Ahora el CHANGELOG sale en dos idiomas.») perdía la segunda y el aviso decía «de más
# de 2 frases». Se comparan contra el texto que PRECEDE al punto, sin distinguir mayúsculas y
# exigiendo que la abreviatura empiece en frontera de palabra (si no, «las cosas.» acabaría en
# «s.»). `ee.` entra para no partir «EE. UU.»; `uu.` NO, porque una frase que termina en «EE. UU.»
# sí termina ahí y ese caso es el frecuente.
#
# `etc.` está FUERA por el mismo motivo que `uu.`, y su presencia era un fallo medido: en español
# técnico «… rutas, globs, etc. Tercera frase.» son DOS frases (el punto de `etc.` cierra la
# primera), así que meterlo en la guarda hacía invisible un fin de frase real — y con el fin de
# frase invisible, `frases()` no encontraba su n-ésimo corte y devolvía el texto ENTERO,
# incumpliendo su tope en silencio. La guarda es para abreviaturas que aparecen EN MEDIO de la
# frase (`Sr. Pérez`, `vs. Claude`, `p. ej. Windows`), no para las que la terminan.
ABREVIATURAS = ("p. ej.", "ej.", "vs.", "sr.", "sra.", "srta.", "dr.", "dra.", "núm.",
                "pág.", "págs.", "cap.", "art.", "fig.", "aprox.", "ee.", "a. m.", "p. m.",
                "cf.", "vid.", "ud.", "uds.", "vol.", "ed.", "op.", "cit.")


# --------------------------------------------------------------- lectura del ledger ----
def frontmatter(text):
    """dict del frontmatter YAML plano (clave: valor) o {} si no hay."""
    lines = text.lstrip("﻿").split("\n")
    if not lines or lines[0].strip() != "---":
        return {}
    out = {}
    for l in lines[1:]:
        if l.strip() == "---":
            break
        m = re.match(r"([A-Za-z_][\w-]*)\s*:\s*(.*)$", l)
        if m:
            out[m.group(1)] = m.group(2).split("#")[0].strip().strip('"\'')
    return out


# Fin de frase: punto seguido de espacio + apertura de frase nueva (evita cortar las versiones).
# El `*` cubre `. **(1) …`, muy común en las Descripciones de este repo. El lookahead SOLO propone
# candidatos: `ABREVIATURAS` descarta los que cierran una abreviatura, no una frase.
FIN_FRASE = re.compile(r"\.(?=\s+[A-ZÁÉÍÓÚÑ¿«`*])")


def _es_abreviatura(s, fin):
    """¿El punto en `s[fin - 1]` cierra una abreviatura conocida en vez de una frase?"""
    antes = s[:fin].lower()
    for ab in ABREVIATURAS:
        if antes.endswith(ab):
            k = len(antes) - len(ab)
            if k == 0 or not antes[k - 1].isalpha():   # frontera: «las cosas.» no es «…s.»
                return True
    return False


def fin_de_frase(s, desde=0):
    """Primer punto de `s[desde:]` que cierra frase DE VERDAD (match de `FIN_FRASE`), o None.
    Descarta los candidatos que solo terminan una abreviatura de `ABREVIATURAS`."""
    for m in FIN_FRASE.finditer(s, desde):
        if not _es_abreviatura(s, m.start() + 1):
            return m
    return None


def primera_frase(s):
    s = re.sub(r"\s+", " ", s).strip()
    m = fin_de_frase(s)
    return (s[: m.start()] if m else s).rstrip(" .") + "."


def separa_frases(s):
    """`s` partido en frases por el criterio de `fin_de_frase()` (una lista, nunca vacía si hay
    texto). Es la fuente única de «cuántas frases hay»: `frases()` la recorta y el aviso de
    `resumen()` cuenta sobre ella, así que el tope y el mensaje no pueden volver a discrepar."""
    s = re.sub(r"\s+", " ", s).strip()
    if not s:
        return []
    out, desde = [], 0
    while True:
        m = fin_de_frase(s, desde)
        if not m:
            out.append(s[desde:].strip())
            return [f for f in out if f]
        out.append(s[desde:m.start() + 1].strip())
        desde = m.start() + 1


def frases(s, n):
    """Las `n` primeras frases de `s`, y NUNCA más de `n` (sin punto añadido; si el texto tiene
    `n` frases o menos se devuelve tal cual).

    El tope es sobre las frases que el criterio de `fin_de_frase()` VE. Antes esta función
    agotaba su bucle y caía en `return s` —el texto entero— cuando no encontraba el n-ésimo fin de
    frase, que es justo lo que pasa cuando una guarda de abreviatura tapa un corte real: publicaba
    tres frases con `RESUMEN_FRASES_MAX = 2` y el aviso decía «recortado a las 2 primeras»."""
    fs = separa_frases(s)
    return " ".join(f.strip() for f in fs[:max(0, n)]).strip()


def corte_principal(s):
    """Lo anterior al primer corte de NIVEL SUPERIOR (`:`, `;`, `—`, `–`, `(`), o None si no hay.

    «Nivel superior» = fuera de los tramos de código y fuera de cualquier pareja abierta
    (paréntesis, corchetes, «comillas»): un `:` dentro de `` `a:b` `` o de «Coste (por qué)» no es
    el final de la oración principal. Dos detalles que parecen menores y no lo son:
    los delimitadores de código se cuentan por RUNS de acentos graves (regla CommonMark), porque
    con el toggle de uno en uno un tramo ``` ``a:b`` ``` quedaba «abierto y cerrado» y el corte
    entraba dentro; y el `(` de un enlace Markdown `[texto](destino)` NO es una apertura de nivel
    superior, porque cortar ahí deja el `[texto]` colgando sin referencia."""
    s = re.sub(r"\s+", " ", s).strip()
    depth, cerco, i, n = 0, 0, 0, len(s)
    while i < n:
        ch = s[i]
        if ch == "`":
            run = len(s[i:]) - len(s[i:].lstrip("`"))
            if cerco == 0:
                cerco = run                       # abre un tramo de código de `run` acentos
            elif cerco == run:
                cerco = 0                         # solo lo cierra un delimitador del MISMO tamaño
            i += run
            continue
        if cerco:
            i += 1
            continue
        if ch in ABRE:
            if depth == 0 and ch == "(" and not (i and s[i - 1] == "]"):
                return s[:i].strip() or None
            depth += 1
        elif ch in CIERRA:
            depth = max(0, depth - 1)
        elif depth == 0 and ch in CORTES:
            return s[:i].strip() or None
        i += 1
    return None


RE_RUN_CODIGO = re.compile(r"`+")


def sin_codigo(s):
    """`s` con los tramos de código sustituidos por un espacio. FUENTE ÚNICA de «esto es código, no
    prosa» — la usan `palabras_de_prosa()`, `normaliza_resumen()` y la guarda de placeholder.

    Los delimitadores se emparejan por RUNS de acentos graves (regla CommonMark: un tramo abierto
    con N acentos solo lo cierra un run de N), no de uno en uno; un run sin pareja se deja TAL CUAL,
    porque es texto y no debe tragarse lo que venga detrás. Existe porque `normaliza_resumen()`
    contaba los `**` sobre el texto CRUDO: un `**` literal dentro de un glob (`` `evals/**` ``)
    desequilibraba la cuenta y la función añadía un `**` huérfano al final, que abre una negrita sin
    cerrar y se come el resto del párrafo al renderizar. El test del equilibrio de los bullets
    reales ya usaba este criterio; era la función la que le faltaba."""
    runs = [(m.start(), m.end()) for m in RE_RUN_CODIGO.finditer(s)]
    tramos, k = [], 0
    while k < len(runs):
        largo = runs[k][1] - runs[k][0]
        cierre = next((j for j in range(k + 1, len(runs))
                       if runs[j][1] - runs[j][0] == largo), None)
        if cierre is None:
            k += 1
            continue
        tramos.append((runs[k][0], runs[cierre][1]))
        k = cierre + 1
    out, pos = [], 0
    for a, b in tramos:
        out.append(s[pos:a])
        out.append(" ")
        pos = b
    out.append(s[pos:])
    return "".join(out)


def palabras_de_prosa(s):
    """Palabras FUERA de los tramos entre acentos graves (las que hacen que algo se lea como una
    idea y no como una lista de rutas). `üÜçÇïÏ` van en la clase por completitud del español y del
    catalán; en la práctica no mueven ninguna cuenta de este repo (medido), porque basta una racha
    de dos letras para que la palabra cuente y «lingüística» ya la tiene en `ling`."""
    return len([w for w in sin_codigo(s).split()
                if re.search(r"[A-Za-zÁÉÍÓÚÑáéíóúñüÜçÇïÏàèòÀÈÒ]{2,}", w)])


def es_placeholder(t):
    """¿El campo NO está escrito porque es (todavía) el placeholder de la plantilla?

    Criterio: quitando los tramos de código y los bloques `{{…}}`, no queda prosa propia. O sea
    «el campo ES el placeholder» (o empieza por él y no añade nada), no «el campo menciona un
    `{{…}}`». Los `{{…}}` dentro de acentos graves NO cuentan: ahí son una cita, no una plantilla.
    Ver el comentario de `PLACEHOLDER_PATTERN` para los dos casos medidos que el criterio anterior
    descartaba."""
    s = (t or "").strip()
    if not s:
        return False
    resto = RE_PLACEHOLDER.sub(" ", sin_codigo(s))
    return not resto.strip(PLACEHOLDER_RELLENO)


def campo_escrito(t):
    """¿El campo `Changelog:` de la tarea está ESCRITO? (ni vacío, ni el placeholder sin sustituir)

    Fuente única de «cuánta deuda hay». Antes los tres sitios que la miden usaban
    `not t["changelog"].strip()`, y un `{{…}}` no está vacío: con un ledger cerrado y ya publicado
    cuya única tarea traía el placeholder de la plantilla, `--check` decía «sin entradas pendientes
    ✅» y nada más, y `--json` daba `sin_campo: 0` / `ledgers_sin_campo: 0` — o sea, el bloque que
    existe para hacer VISIBLE la deuda reportaba cero justo en el caso que la plantilla crea."""
    return bool((t or "").strip()) and not es_placeholder(t)


def normaliza_resumen(t):
    """Deja el texto presentable: quita la puntuación colgante, CIERRA la negrita que el corte haya
    dejado abierta (`los **27 scripts` → `Los **27 scripts**.`), pone mayúscula inicial y termina en
    punto. NUNCA añade `…` y nunca BORRA el énfasis que escribió el autor.

    Un `**` que queda AL FINAL sin nada detrás no abría nada: es puntuación colgante y se quita.
    Los `**` se cuentan FUERA de los tramos de código (`sin_codigo()`): dentro son literales — un
    glob `` `evals/**` `` no abre negrita — y contarlos añadía un `**` huérfano que abre una
    negrita sin cerrar y se come el resto del párrafo al renderizar. Es el mismo criterio que ya
    usaba `test_los_bullets_reales_del_repo_estan_equilibrados_en_markdown`. Solo se cierra `**`. Un `*` o un `_` en medio del texto se deja tal cual a propósito: en este
    repo son casi siempre literales (`evals/**`, `docs/*`, nombres con guion bajo) y cerrarlos
    corrompería el texto. Medido sobre los 69 bullets reales del repo: 0 desbalanceados, con test."""
    t = (t or "").strip().rstrip(" \t.,;:—–·-*")
    if not t:
        return ""
    if sin_codigo(t).count("**") % 2 == 1:
        t += "**"                            # negrita abierta por el corte: se CIERRA, no se borra
    t = re.sub(r"^([a-záéíóúñüç])", lambda m: m.group(1).upper(), t, count=1)
    return t + "."


def resumen(desc, changelog):
    """(texto, camino, avisos) — la ESCALERA determinista del bullet (fuente única del criterio).

    camino ∈ `changelog` (campo explícito de la tarea) · `frase` (1.ª frase de la Descripción) ·
    `corte` (oración principal) · `titulo` (nada cabía: solo título + puntero al ledger)."""
    avisos = []
    campo = (changelog or "").strip()
    if es_placeholder(campo):
        avisos.append("campo `Changelog:` sin sustituir (ES el placeholder `{{…}}` de la "
                      "plantilla) — se IGNORA (el bullet degrada) hasta que se escriba la frase "
                      "de verdad")
        campo = ""
    if campo:
        n_frases = len(separa_frases(campo))
        corto = frases(campo, RESUMEN_FRASES_MAX).strip()
        if n_frases > RESUMEN_FRASES_MAX:
            # El aviso sale cuando de VERDAD se recortó, y dice CUÁNTAS frases había: antes se
            # deducía de «texto distinto», que mentía en los dos sentidos (una abreviatura sobre un
            # campo de dos frases lo disparaba, y un campo de cuatro con un fin de frase invisible
            # publicaba tres diciendo «recortado a las 2 primeras»).
            avisos.append(f"campo `Changelog:` recortado a las {RESUMEN_FRASES_MAX} primeras "
                          f"frases (traía {n_frases})")
        if len(corto) > RESUMEN_MAX:
            avisos.append(f"campo `Changelog:` de {len(corto)} caracteres (tope {RESUMEN_MAX}) — "
                          f"se respeta tal cual (no se trunca lo que escribió una persona), "
                          f"pero acórtalo a una o dos frases")
        return corto, "changelog", avisos
    d = (desc or "").strip()
    if es_placeholder(d):
        # MINOR 11: la guarda cubría SOLO `Changelog:`, así que
        # `resumen("{{Qué hay que hacer y por qué, en 1-3 frases.}}", None)` publicaba el
        # placeholder de la plantilla literal, sin aviso y por el camino `frase`.
        avisos.append("campo `Descripción:` sin sustituir (ES el placeholder `{{…}}` de la "
                      "plantilla) — se IGNORA (el bullet degrada al título)")
        d = ""
    if not d:
        return "", "titulo", avisos
    pf = normaliza_resumen(primera_frase(d))
    if len(pf) <= RESUMEN_MAX:
        return pf, "frase", avisos
    corte = corte_principal(d)
    if corte:
        n = normaliza_resumen(corte)
        if n and len(n) <= RESUMEN_MAX and palabras_de_prosa(n) >= CORTE_MIN_PALABRAS:
            return n, "corte", avisos
    return "", "titulo", avisos


def archivos_clave(s, maximo=None):
    """Tokens entre acentos graves del campo Archivos, sin las anotaciones entre paréntesis.
    Sin `maximo` devuelve TODOS: el recorte a `ARCHIVOS_MAX` y la decisión de omitir el paréntesis
    se toman al renderizar, que es donde hace falta saber cuántos toca la tarea de verdad."""
    out = []
    for tok in re.findall(r"`([^`]+)`", s or ""):
        tok = re.sub(r"\s*\([^)]*\)", "", tok).strip()
        if tok and tok not in out:
            out.append(tok)
        if maximo is not None and len(out) >= maximo:
            break
    return out


def campo_con_continuacion(b, rx, grupo=1):
    """Texto del campo que casa `rx` en el bloque `b`, con la CONTINUACIÓN indentada absorbida
    (unida por un espacio), o **None** si el campo NO ESTÁ. Una persona parte una frase larga en
    dos líneas y el Markdown la lee como un solo párrafo: sin esto, la continuación se perdía en
    silencio y el bullet se quedaba sin punto final.

    `None` (ausente) y `""` (presente y vacío) se distinguen a propósito, igual que en
    `ledger-lint.parse_ledger()`: los dos degradan el bullet, pero el desglose de la deuda
    (`degradacion.sin_campo_por_motivo`) dice cuál de los dos es, y eso es la diferencia entre
    «nadie lo ha escrito todavía» y «se quedó a medias»."""
    m = rx.search(b)
    if not m:
        return None
    partes = [m.group(grupo).strip()]
    for ln in b[m.end():].split("\n")[1:]:
        if not es_continuacion(ln):
            break
        partes.append(ln.strip())
    return re.sub(r"\s+", " ", " ".join(p for p in partes if p)).strip()


def tareas(text):
    """[{id, titulo, desc, changelog, archivos}] en orden de aparición. `desc` va CRUDA (la
    escalera de `resumen()` decide qué trozo se usa), `archivos` completo (sin recortar) y
    `changelog` es `None` si el campo NO está y `""` si está y está VACÍO — igual que
    `ledger-lint.parse_ledger()`, para que los dos parsers se puedan comparar sin traducir.

    El bloque de una tarea termina en la siguiente `### T-XX`/`### Fase` O en cualquier `## ` —
    mismo criterio que `ledger-lint.py`. Sin el segundo, la cola del ledger (`## Notas de cierre`,
    `## Resumen de progreso`, apéndices) contaba como parte de la ÚLTIMA tarea. Las líneas dentro
    de una valla de código se vacían ANTES de parsear (`sin_vallas`): un `## Ejemplo` citado en una
    valla ```markdown cortaba la tarea y el campo real de debajo se perdía en silencio."""
    out = []
    bloques = re.split(r"\n(?=### (?:T-\d+|Fase)\b)", sin_vallas(text))
    for b in bloques:
        m = re.match(r"### (T-\d+)\s*[—-]\s*(.+)", b)
        if not m:
            continue
        fin = RE_FIN_BLOQUE.search(b)
        if fin:
            b = b[:fin.start()]
        out.append({"id": m.group(1), "titulo": m.group(2).strip(),
                    "desc": campo_con_continuacion(b, RE_CAMPO_DESC) or "",
                    "changelog": campo_con_continuacion(b, RE_CAMPO_CHANGELOG, "txt"),
                    "archivos": archivos_clave(campo_con_continuacion(b, RE_CAMPO_ARCH) or "")})
    return out


def categoria(fm, tits):
    c = (fm.get("changelog") or "").strip().capitalize()
    if c in CATS:
        return c
    texto = " ".join([fm.get("descripcion", "")] + tits)
    if RE_FIXED.search(texto):
        return "Fixed"
    if RE_CHANGED.search(texto):
        return "Changed"
    return "Added"


def ledgers(root):
    """[(fecha, slug, ruta_relativa, frontmatter, tareas)] de los COMPLETADOS, por fecha+slug."""
    base = os.path.join(root, "docs", "roadmap")
    out, avisos = [], []
    if not os.path.isdir(base):
        return out, ["docs/roadmap/ no existe: nada que sincronizar"]
    for d in sorted(os.listdir(base)):
        m = LEDGER_GLOB.match(d)
        p = os.path.join(base, d, "tasks.md")
        if not m or not os.path.isfile(p):
            continue
        try:
            text = open(p, encoding="utf-8-sig").read()
        except OSError as e:
            avisos.append(f"{d}: no se puede leer ({e})")
            continue
        fm = frontmatter(text)
        if not fm:
            avisos.append(f"{d}: ledger sin frontmatter (legacy) — se ignora")
            continue
        if fm.get("estado") != "completado":
            continue
        ts = tareas(text)
        if not ts:
            avisos.append(f"{d}: completado pero sin tareas T-XX reconocibles — se ignora")
            continue
        out.append((m.group(1), m.group(2), os.path.relpath(p, root).replace(os.sep, "/"),
                    fm, ts))
    return out, avisos


# ------------------------------------------------------------------ render / escritura ----
def bullets(ts, ledger):
    """(líneas, caminos, avisos). Un bullet por tarea: título + resumen de la escalera + hasta
    ARCHIVOS_MAX ficheros; sin resumen, título + puntero al ledger (nunca `…`)."""
    lineas, caminos, avisos = [], {}, []
    for t in ts:
        texto, camino, av = resumen(t["desc"], t["changelog"])
        caminos[camino] = caminos.get(camino, 0) + 1
        avisos += [f"{t['id']}: {a}" for a in av]
        linea = f"- **{t['id']} — {t['titulo']}**"
        if texto:
            linea += f" {texto}"
            arch = t["archivos"]
            if arch and len(arch) <= ARCHIVOS_MAX_TOCADOS:
                linea += " (" + ", ".join(f"`{a}`" for a in arch[:ARCHIVOS_MAX]) + ")"
        else:
            linea += f" ([ledger]({ledger}))"
        lineas.append(linea)
    return lineas, caminos, avisos


def seccion(plantilla, cat, slug, fecha, ts, ledger):
    """(texto de la subsección, caminos, avisos)."""
    lineas, caminos, avisos = bullets(ts, ledger)
    cuerpo = "\n".join([plantilla.format(cat=cat, slug=slug, fecha=fecha), ""] + lineas + [""])
    return cuerpo, caminos, avisos


def aviso_sin_changelog(slug, ts):
    """Empuje para que el campo se escriba: qué tareas SIN `Changelog:` de una iniciativa que
    todavía se puede arreglar. Es un AVISO — el campo es opcional por diseño y no cambia ningún
    exit code. La forma de la línea evita el `SLUG_PENDIENTE` de `scripts/release.py`
    (`<viñeta> <slug> (AAAA-MM-DD)`): aquí el slug lleva `:` detrás, no una fecha entre paréntesis."""
    sin = [t["id"] for t in ts if not campo_escrito(t["changelog"])]
    if not sin:
        return None
    return (f"{slug}: {len(sin)}/{len(ts)} tarea(s) sin `- **Changelog**:` "
            f"[{', '.join(sin)}] — su bullet degrada al título; escribe el campo al cerrar la tarea "
            f"(una frase: qué cambia para quien USA el proyecto)")


def degradacion(regs):
    """Cuánto degrada el CHANGELOG hoy, sobre TODO ledger cerrado: el dato que antes se afirmaba
    visible en `pendientes[].caminos` y no lo era (`pendientes[]` solo lista lo que FALTA en el
    CHANGELOG, así que las iniciativas ya publicadas no aparecen ahí nunca).

    Un campo VACÍO o que ES el placeholder de la plantilla cuenta como NO escrito (`campo_escrito`):
    en los dos casos el bullet degrada, así que contarlos como escritos dejaba la deuda invisible.

    {ledgers, tareas, caminos, sin_campo, sin_campo_por_motivo, ledgers_sin_campo}. El desglose
    por motivo dice POR QUÉ falta (`ausente`, `vacio`, `placeholder`), que es la diferencia entre
    «nadie lo ha escrito todavía» y «lo dejó a medias quien copió la plantilla»."""
    caminos, motivos, sin_campo, ledgers_sin = {}, {"ausente": 0, "vacio": 0, "placeholder": 0}, 0, 0
    for _f, _s, _l, _fm, ts in regs:
        falta = 0
        for t in ts:
            _tx, camino, _av = resumen(t["desc"], t["changelog"])
            caminos[camino] = caminos.get(camino, 0) + 1
            if not campo_escrito(t["changelog"]):
                falta += 1
                clave = ("placeholder" if es_placeholder(t["changelog"])
                         else "ausente" if t["changelog"] is None else "vacio")
                motivos[clave] += 1
        sin_campo += falta
        ledgers_sin += 1 if falta else 0
    return {"ledgers": len(regs), "tareas": sum(caminos.values()), "caminos": caminos,
            "sin_campo": sin_campo, "sin_campo_por_motivo": motivos,
            "ledgers_sin_campo": ledgers_sin}


def linea_degradacion(d):
    """Una línea con el total, en vez de una por iniciativa ya publicada (que nadie puede cambiar
    de sitio: `pendientes()` las salta para siempre). También evita `SLUG_PENDIENTE`."""
    if not d["tareas"]:
        return None
    deg = d["caminos"].get("titulo", 0)
    mot = d["sin_campo_por_motivo"]
    extra = ", ".join(f"{n} {k}" for k, n in mot.items() if n and k != "ausente")
    return (f"resumen del campo `Changelog:`: {d['sin_campo']}/{d['tareas']} tarea(s) de "
            f"{d['ledgers_sin_campo']}/{d['ledgers']} ledger(s) cerrados no lo traen"
            + (f" ({extra})" if extra else "")
            + f" y {deg} bullet(s) degradan al título — detalle por camino en `--check --json` "
              f"(`degradacion.caminos`)")


# --------------------------------------------------------------- medición viva ----
# Nueve cifras escritas A MANO en la prosa de la doc no reproducían (mediana 354 donde eran 350,
# «13 ledgers (63 tareas)» sobre una tabla que suma 69, «de 274 a 66» donde son 55, «12 de los 14»
# donde son 13, «24 tests nuevos» donde son 27, «28 formas» donde `ABREVIATURAS` tiene 26…). La
# causa no era el descuido: era que la ÚNICA fuente de cada cifra era la prosa. `medicion()` las
# CALCULA desde el árbol de trabajo, `--medicion` las imprime y `tests/test_cifras_medidas.py`
# compara cada número marcado en la doc (`<!--m:clave-->`) con lo que sale de aquí.
#
# Corpus BASE = los ledgers cerrados ANTES de la iniciativa `changelog-brief` (13 ledgers, 63
# tareas). Es el corpus con el que se eligieron los topes y con el que se midió el antes/después,
# así que se fija por fecha para que siga siendo el mismo cuando cierren más iniciativas. El
# corpus de HOY (`ledgers_cerrados`/`tareas`) crece, y donde importa la diferencia la doc dice cuál
# de los dos mide.
CORPUS_BASE_HASTA = "2026-09-04"


def _mediana(xs):
    """Mediana ENTERA (con N par se trunca el promedio de los dos centrales): las cifras de la doc
    son enteros y un `128,5` en la prosa no aportaría nada."""
    s = sorted(xs)
    n = len(s)
    if not n:
        return 0
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) // 2


def _media(xs):
    return int(sum(xs) / len(xs)) if xs else 0


@contextlib.contextmanager
def _con_topes(**topes):
    """Barrido: cambia SOLO las constantes indicadas y las restaura al salir."""
    previos = {k: globals()[k] for k in topes}
    globals().update(topes)
    try:
        yield
    finally:
        globals().update(previos)


def _caminos_de(regs):
    out = {}
    for _f, _s, _l, _fm, ts in regs:
        for t in ts:
            _tx, camino, _av = resumen(t["desc"], t["changelog"])
            out[camino] = out.get(camino, 0) + 1
    return out


def _largos_de(regs):
    """{camino: [longitud del bullet completo]} — el bullet tal y como se escribe."""
    out = {}
    for _f, _s, _l, _fm, ts in regs:
        lineas, _c, _av = bullets(ts, _l)
        for t, ln in zip(ts, lineas):
            _tx, camino, _av2 = resumen(t["desc"], t["changelog"])
            out.setdefault(camino, []).append(len(ln))
    return out


def _colas(root):
    """(ledgers con tasks.md, cuántos tienen cola tras su última `### T-XX`, ídem solo cerrados)."""
    base = os.path.join(root, "docs", "roadmap")
    tot = con = cerr_con = 0
    if not os.path.isdir(base):
        return 0, 0, 0
    for d in sorted(os.listdir(base)):
        p = os.path.join(base, d, "tasks.md")
        if not LEDGER_GLOB.match(d) or not os.path.isfile(p):
            continue
        text = open(p, encoding="utf-8-sig").read()
        tot += 1
        ults = [b for b in re.split(r"\n(?=### (?:T-\d+|Fase)\b)", text)
                if re.match(r"### T-\d+", b)]
        cola = bool(ults and RE_FIN_BLOQUE.search(ults[-1]))
        con += 1 if cola else 0
        if cola and frontmatter(text).get("estado") == "completado":
            cerr_con += 1
    return tot, con, cerr_con


def _placeholder_de_la_plantilla(root):
    """Longitud del `{{…}}` del campo `Changelog:` en la plantilla de tarea del `planner`, 0 si no
    está (paquete portable sin el kit)."""
    p = os.path.join(root, "agent-kits", "planner", "templates", "tasks.md")
    if not os.path.isfile(p):
        return 0
    m = RE_CAMPO_CHANGELOG.search(open(p, encoding="utf-8").read())
    return len(m.group("txt").strip()) if m else 0


def medicion(root):
    """{clave: entero} con TODA cifra de la doc que se pueda medir hoy desde el árbol de trabajo.

    No lee la red, no lee git y no depende del orden del sistema de ficheros (`sorted`). Las cifras
    que NO son medibles así (un RED histórico, el «antes» medido con el script de `a7a11b0`) NO
    salen de aquí: la doc las marca `<!--m?:motivo-->` y el test exige el motivo en vez de fingir
    que reproducen."""
    regs = ledgers(root)[0]
    base = [r for r in regs if r[0] < CORPUS_BASE_HASTA]
    m = {"ledgers_cerrados": len(regs), "tareas": sum(len(ts) for *_x, ts in regs),
         "base_ledgers": len(base), "base_tareas": sum(len(ts) for *_x, ts in base),
         "resumen_max": RESUMEN_MAX, "resumen_frases_max": RESUMEN_FRASES_MAX,
         "archivos_max": ARCHIVOS_MAX, "archivos_max_tocados": ARCHIVOS_MAX_TOCADOS,
         "corte_min_palabras": CORTE_MIN_PALABRAS, "abreviaturas": len(ABREVIATURAS),
         "placeholder_plantilla": _placeholder_de_la_plantilla(root)}
    tot, con, cerr_con = _colas(root)
    m.update(ledgers_totales=tot, ledgers_con_cola=con, cerrados_con_cola=cerr_con)

    for pref, rs in (("", regs), ("base_", base)):
        largos = _largos_de(rs)
        todos = [x for v in largos.values() for x in v]
        m[f"{pref}bullet_mediana"] = _mediana(todos)
        m[f"{pref}bullet_max"] = max(todos) if todos else 0
        m[f"{pref}bullet_media"] = _media(todos)
        m[f"{pref}bullet_mayores_400"] = sum(1 for x in todos if x > 400)
        for camino in ("changelog", "frase", "corte", "titulo"):
            v = largos.get(camino, [])
            m[f"{pref}camino_{camino}"] = len(v)
            m[f"{pref}{camino}_mediana"] = _mediana(v)
            m[f"{pref}{camino}_max"] = max(v) if v else 0
            m[f"{pref}{camino}_media"] = _media(v)
        n = len(todos) or 1
        m[f"{pref}degradan_titulo_pct"] = round(100 * len(largos.get("titulo", [])) / n)

    deg = degradacion(regs)
    m.update(sin_campo=deg["sin_campo"], ledgers_sin_campo=deg["ledgers_sin_campo"])
    m["ledgers_legacy"] = sum(1 for v in ledgers(root)[1] if "legacy" in v)

    # Descomposición del bullet MÁS LARGO del corpus base: una versión de la doc daba las tres
    # componentes mal (el total era correcto), así que se miden en vez de escribirlas.
    peor = None
    for _f, _s, _l, _fm, ts in base:
        lineas, _c, _av = bullets(ts, _l)
        for t, ln in zip(ts, lineas):
            if peor is None or len(ln) > len(peor[1]):
                peor = (t, ln, _l)
    if peor:
        t, ln, _l = peor
        texto, _cam, _av = resumen(t["desc"], t["changelog"])
        cabecera = f"- **{t['id']} — {t['titulo']}**"
        m.update(base_peor_cabecera=len(cabecera), base_peor_resumen=len(texto),
                 base_peor_titulo=len(t["titulo"]),
                 base_peor_ficheros=len(ln) - len(cabecera) - 1 - len(texto))

    # Caminos por iniciativa del corpus base: la tabla que la doc pegaba a mano.
    for _f, slug, _l, _fm, ts in base:
        c = _caminos_de([(_f, slug, _l, _fm, ts)])
        k = slug.replace("-", "_")
        m[f"base_tareas_{k}"] = len(ts)
        for camino in ("changelog", "frase", "corte", "titulo"):
            m[f"base_caminos_{k}_{camino}"] = c.get(camino, 0)

    # ficheros por tarea (corpus BASE: es el que eligió `ARCHIVOS_MAX_TOCADOS`)
    na = [len(t["archivos"]) for *_x, ts in base for t in ts]
    nb = len(na) or 1
    m.update(base_archivos_mediana=_mediana(na), base_archivos_max=max(na) if na else 0,
             base_archivos_mas_de_3=sum(1 for x in na if x > 3))
    for u in (3, 4, 5, 6, 8, 10):
        c = sum(1 for x in na if x and x <= u)
        m[f"base_umbral_{u}"] = c
        m[f"base_umbral_{u}_pct"] = round(100 * c / nb)
        m[f"base_umbral_{u}_sin"] = len(na) - c

    # barridos: SOLO se mueve la constante que se estudia (corpus BASE)
    for tope in (160, 200, 240):
        with _con_topes(RESUMEN_MAX=tope):
            c = _caminos_de(base)
        for k in ("frase", "corte", "titulo"):
            m[f"base_tope{tope}_{k}"] = c.get(k, 0)
    for v in range(8):
        with _con_topes(CORTE_MIN_PALABRAS=v):
            c = _caminos_de(base)
        m[f"base_barrido{v}_corte"] = c.get("corte", 0)
        m[f"base_barrido{v}_titulo"] = c.get("titulo", 0)
    # trasvase que produce la puerta al valor elegido (`corte` sin puerta → `corte` con puerta)
    m["base_trasvase_corte"] = m["base_barrido0_corte"] - m[f"base_barrido{CORTE_MIN_PALABRAS}_corte"]
    return m


def pendientes(root, only=None):
    """[(fecha, slug, cat, ts)] pendientes en AL MENOS un CHANGELOG + avisos."""
    regs, avisos = ledgers(root)
    textos = {}
    for fn in CHANGELOGS:
        p = os.path.join(root, fn)
        if not os.path.isfile(p):
            return None, avisos + [f"falta {fn}"], None
        textos[fn] = open(p, encoding="utf-8").read()
    out = []
    for fecha, slug, ledger, fm, ts in regs:
        if only and slug != only:
            continue
        falta = [fn for fn, t in textos.items() if f"`{slug}`" not in t]
        if falta:
            out.append((fecha, slug, categoria(fm, [t["titulo"] for t in ts]), ts, falta, ledger))
    return out, avisos, textos


def insertar(text, cabecera, bloque):
    """Inserta el bloque justo debajo de la cabecera Unreleased (y su línea en blanco)."""
    i = text.index(cabecera) + len(cabecera)
    resto = text[i:]
    j = len(resto) - len(resto.lstrip("\n"))
    return text[:i] + "\n" * max(j, 2) + bloque + resto[j:]


def main(argv=None):
    ap = argparse.ArgumentParser(description="Entradas [Unreleased] desde los ledgers cerrados.")
    ap.add_argument("--root", default=".")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--json", action="store_true", dest="as_json")
    ap.add_argument("--medicion", action="store_true",
                    help="imprime las cifras medibles de la doc (clave = valor) y termina")
    a = ap.parse_args(argv)
    root = os.path.abspath(a.root)
    if a.medicion:
        m = medicion(root)
        if a.as_json:
            print(json.dumps(m, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            for k in sorted(m):
                print(f"{k} = {m[k]}")
            print(f"changelog-sync --medicion: {len(m)} cifra(s) medidas "
                  f"(corpus de hoy {m['ledgers_cerrados']} ledger(s) / {m['tareas']} tarea(s); "
                  f"corpus base < {CORPUS_BASE_HASTA}: {m['base_ledgers']} / {m['base_tareas']})")
        return 0
    pend, avisos, textos = pendientes(root, a.only)
    if pend is None:
        for v in avisos:
            print(f"changelog-sync: {v}", file=sys.stderr)
        return 2
    if a.only and not pend and not any(True for _ in ()):
        # --only con un slug que no existe entre los cerrados (o ya sincronizado): distíngelo
        regs, _ = ledgers(root)
        if a.only not in [s for _f, s, *_ in regs]:
            print(f"changelog-sync: no hay ledger CERRADO con slug «{a.only}»", file=sys.stderr)
            return 2
    # Empuje del campo `Changelog:`: SOLO las iniciativas que están pendientes de entrada. Antes
    # `--check` avisaba de todo ledger cerrado «porque es el recordatorio que ve el release», y era
    # falso por los dos lados: `release.py` no ve ninguna de esas líneas (su `SLUG_PENDIENTE` no
    # casa el `⚠️`), y las iniciativas YA publicadas las salta `pendientes()` para siempre, así que
    # escribir el campo en ellas no cambiaría un byte de la salida. El total de la deuda va en UNA
    # línea (`linea_degradacion`) y el detalle por camino en `--check --json`.
    fuente = [(s, ts) for _f, s, _c, ts, _fl, _l in pend]
    avisos = avisos + [v for v in (aviso_sin_changelog(s, ts) for s, ts in fuente) if v]
    deg = degradacion([r for r in ledgers(root)[0] if not a.only or r[1] == a.only])
    # (fecha, slug) como clave: dos iniciativas pueden compartir slug con fechas distintas
    render = {}          # (fecha, slug) → (caminos, avisos del resumen)
    for f, s, c, ts, fl, ledger in pend:
        _l, caminos, av = bullets(ts, ledger)
        render[(f, s)] = (caminos, [f"{s} {x}" for x in av])
        avisos += render[(f, s)][1]
    res = {"root": root, "pendientes": [{"slug": s, "fecha": f, "categoria": c,
                                         "tareas": len(ts), "ficheros": fl,
                                         "caminos": render[(f, s)][0]}
                                        for f, s, c, ts, fl, _l in pend],
           "degradacion": deg, "avisos": avisos, "escrito": []}
    if a.check:
        if a.as_json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            for v in avisos:
                print(f"⚠️  {v}")
            ld = linea_degradacion(deg)
            if ld and deg["sin_campo"]:
                print(f"⚠️  {ld}")
            if pend:
                print("changelog-sync --check: entradas PENDIENTES en el CHANGELOG:")
                for f, s, c, ts, fl, _l in pend:
                    print(f"  · {s} ({f}) — {c}, {len(ts)} tarea(s) → falta en {', '.join(fl)}")
                print("Ejecuta `changelog-sync.py` (sin --check) para generarlas.")
            else:
                print("changelog-sync --check: sin entradas pendientes ✅")
        return 1 if pend else 0
    for fn, (cabecera, plantilla) in CHANGELOGS.items():
        bloques = [seccion(plantilla, c, s, f, ts, ledger)[0]
                   for f, s, c, ts, fl, ledger in pend if fn in fl]
        if not bloques:
            continue
        nuevo = textos[fn]
        # se insertan en orden de fecha ASCENDENTE justo bajo la cabecera: cada inserción
        # empuja a la anterior hacia abajo, así la iniciativa MÁS RECIENTE acaba arriba.
        for b in bloques:
            nuevo = insertar(nuevo, cabecera, b + "\n")
        if a.dry_run:
            res["escrito"].append({"fichero": fn, "secciones": len(bloques), "dry_run": True})
            if not a.as_json:
                print(f"── {fn} (--dry-run, NO escrito):")
                print("\n".join(b.rstrip() for b in bloques))
        else:
            with open(os.path.join(root, fn), "w", encoding="utf-8", newline="") as fh:
                fh.write(nuevo)
            res["escrito"].append({"fichero": fn, "secciones": len(bloques)})
    if a.as_json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        for v in avisos:
            print(f"⚠️  {v}")
        if not pend:
            print("changelog-sync: sin entradas pendientes ✅ (idempotente)")
        elif not a.dry_run:
            print(f"changelog-sync: {len(pend)} iniciativa(s) añadidas a "
                  f"{', '.join(sorted(CHANGELOGS))} — revisa y afina el texto antes del release.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
