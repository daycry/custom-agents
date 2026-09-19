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
  - Con `verificacion: obligatoria` en el frontmatter: tarea sin campo `- **Verificación**:` o con
    el campo VACÍO (plan-and-diet T-02 — sin verificación ejecutable la tarea no está bien definida).
    Formas aceptadas (T-fix1): en línea `- **Verificación**: cmd → res · cmd2 → res2`, sub-lista
    (`- **Verificación**:` + ítems `  - cmd → res` indentados debajo) y la variante ya ejecutada
    `- **Verificación** (ejecutada <fecha> — salida: …): cmd → res` (el paréntesis se parsea aparte;
    `parse_verificacion()` es importable — lo reutiliza `task-brief.py`).

AVISOS (no rompen; formato/legacy):
  - Falta el banner de ledger canónico.
  - Falta la tabla «Resumen de progreso».
  - Tarea sin campo Estado o sin bloque de criterios.
  - Tarea sin `Verificación` cuando el ledger NO declara `verificacion: obligatoria` pero ya usa el
    campo en otras tareas (adopción parcial) o declara `verificacion:` con otro valor. Un ledger
    legacy sin la clave y sin ningún `Verificación` no recibe aviso (los ledgers previos validan
    idéntico).
  - Tarea sin `- **Changelog**:` (resumen del cambio para el CHANGELOG, skill `changelog-sync`)
    cuando el ledger ya usa el campo en otra tarea — adopción PARCIAL. El campo es **opcional por
    diseño**: un ledger que no lo usa en ninguna tarea no recibe aviso (los ledgers previos validan
    idéntico) y el empuje para escribirlo lo da `changelog-sync.py --check`, no este linter. Nunca
    es incoherencia dura. El TOPE de longitud vive solo en `changelog-sync.py` (`RESUMEN_MAX`), que
    es quien renderiza: aquí no se duplica la constante.
  - Campo `- **Changelog**:` VACÍO, o que ES todavía el placeholder `{{…}}` de la plantilla: en los
    dos casos `changelog-sync` degrada el bullet al título, así que el campo no está escrito. Un
    `{{…}}` CITADO (entre acentos graves, o dentro de una frase que dice algo más) sí está escrito
    y se publica: el criterio es «el campo ES el placeholder», no «lo menciona».

Uso:
  python3 ledger-lint.py <ruta/a/tasks.md> [--warn-only]
  --warn-only: imprime todo como aviso y SIEMPRE exit 0 (modo hook).

Como módulo: `parse_ledger(text)` expone el parser estructural (fases, tareas, estados,
horas IA) sin efectos secundarios — lo reutiliza `progress-report.py` (live-visibility).
"""
import argparse
import os
import re
import sys

# Consola Windows (cp1252) o tuberías: reconfigurar ANTES de leer o imprimir nada (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

ESTADOS = {"borrador", "en-progreso", "en-revision", "completado", "cancelado"}
# quita emojis/decoración al comparar estados: "completado ✅" → "completado"
def norm_estado(s):
    s = re.sub(r"[\s_]+", "-", s.strip().lower())   # "En Progreso" → "en-progreso"
    return re.sub(r"[^a-z\-]", "", s).strip("-")    # "en-progreso 🚧" → "en-progreso"


# `- **Verificación**: …` · `- **Verificación** (ejecutada … — salida: …): …` (paréntesis con un nivel de
# anidamiento, consumido ANTES de los dos puntos: la salida grabada no se confunde con el comando)
VERIF_RE = re.compile(
    r"^\s*-\s*\*\*Verificaci[oó]n\*\*\s*(?P<paren>\((?:[^()]|\([^()]*\))*\))?\s*:\s*(?P<inline>.*)$", re.I)
_SUBITEM_RE = re.compile(r"^\s+[-*]\s+(.*\S)\s*$")
# `- **Changelog**: …` — resumen del cambio que consume la skill `changelog-sync` (opcional).
# FUENTE ÚNICA del criterio de este campo: `skills/changelog-sync/scripts/changelog-sync.py` guarda
# una copia LITERAL de esta cadena (su paquete portable viaja sin este kit) y su suite compara las
# dos byte a byte. Antes cada uno tenía su criterio —aquí `^\s*-\s*` (indentación y espaciado
# libres), allí `^- ` exacto—, así que un `-  **Changelog**: …` con dos espacios pasaba este linter
# y el generador lo descartaba en silencio, devolviendo el bullet a la `Descripción` cruda.
# `[^\S\n]*` y no `\s*`: usado con `re.M` sobre un bloque de varias líneas, `\s*` se come el salto
# de línea y un campo VACÍO captura la línea siguiente entera.
CHANGELOG_FIELD_PATTERN = \
    r"^[^\S\n]*-[^\S\n]*\*\*Changelog\*\*[^\S\n]*:[^\S\n]*(?P<txt>.*)$"
CHANGELOG_RE = re.compile(CHANGELOG_FIELD_PATTERN, re.I)
# --- Criterios que `changelog-sync.py` REPLICA LITERAL (su paquete portable viaja sin este kit).
# La suite compara las tres cadenas byte a byte y enfrenta los dos PARSERS sobre bloques de ledger
# COMPLETOS (con `Verificación` + sub-lista, `### Fase`, valla de código y cola tras la última
# tarea), no dos regex sobre una línea suelta: el test del intento 1 comparaba las regex, y por eso
# no cazó que un `- **Changelog**:` indentado bajo `- **Verificación**:` lo publicaba el generador
# y este linter lo daba por ausente (el bug del intento 1 con los papeles invertidos).
#
# (a) Valla de código: un `## Ejemplo` citado dentro de una valla ```markdown NO cierra la tarea.
VALLA_PATTERN = r"^[^\S\n]*(?:`{3,}|~{3,})"
# (b) Campos del bloque de una tarea: una línea que es uno de ellos no es prosa de continuación ni
#     ítem de la sub-lista de `Verificación`.
CAMPO_LEDGER_PATTERN = (r"^[^\S\n]*(?:[-*+][^\S\n]*)?\*\*(?:Changelog|Descripci[oó]n|Archivos|"
                        r"Estado|Verificaci[oó]n|Tiempo[^*]*|Supervisi[oó]n|Notas|"
                        r"Criterios[^*]*)\*\*")
# (c) Continuación indentada del campo (una persona parte una frase larga en dos líneas): se
#     absorbe, no se pierde en silencio — pero SOLO si es prosa.
CONTINUACION_PATTERN = r"^[ \t]{1,3}(?![-*+>|]\s|\d+[.)]\s|<!--|\|)\S"
_VALLA_RE = re.compile(VALLA_PATTERN)
_CAMPO_LEDGER_RE = re.compile(CAMPO_LEDGER_PATTERN, re.I)
_CONTINUACION_RE = re.compile(CONTINUACION_PATTERN)


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


def es_continuacion(ln):
    """¿`ln` es la continuación indentada (prosa) del campo anterior?"""
    return bool(_CONTINUACION_RE.match(ln)) and not _CAMPO_LEDGER_RE.match(ln)
# Placeholder de plantilla sin sustituir: `{{OPCIONAL, lo rellena quien CIERRA la tarea: …}}` no es
# un resumen escrito. `changelog-sync.py` lo ignora y degrada al título; aquí se avisa.
#
# FUENTE ÚNICA del criterio, igual que `CHANGELOG_FIELD_PATTERN`: `changelog-sync.py` guarda una
# copia LITERAL de `PLACEHOLDER_PATTERN` y replica `es_placeholder()`, y su suite compara las dos
# cadenas byte a byte y las dos FUNCIONES sobre la misma tabla de casos. El criterio es «el campo
# ES el placeholder» (quitando los tramos de código y los bloques `{{…}}` no queda prosa propia),
# NO «el campo menciona un `{{…}}`»: en un repo cuyas plantillas van llenas de `{{…}}`, una CITA
# entre acentos graves es texto humano legítimo y descartarla era pérdida silenciosa.
PLACEHOLDER_PATTERN = r"\{\{.*?\}\}"
_PLACEHOLDER_RE = re.compile(PLACEHOLDER_PATTERN, re.S)
PLACEHOLDER_RELLENO = " \t\n.,;:!?—–·-*_`\"'()[]{}«»"
_RUN_CODIGO_RE = re.compile(r"`+")


def sin_codigo(s):
    """`s` con los tramos entre acentos graves sustituidos por un espacio, emparejando los
    delimitadores por RUNS (regla CommonMark). Réplica del criterio de `changelog-sync.py`
    (`sin_codigo`), comparado por la suite sobre la misma tabla de casos."""
    runs = [(m.start(), m.end()) for m in _RUN_CODIGO_RE.finditer(s)]
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


def es_placeholder(t):
    """¿El campo NO está escrito porque ES (todavía) el placeholder de la plantilla?"""
    s = (t or "").strip()
    if not s:
        return False
    resto = _PLACEHOLDER_RE.sub(" ", sin_codigo(s))
    return not resto.strip(PLACEHOLDER_RELLENO)

# ---------------------------------------------------------------------------------------------
# Cabecera de una sección de revisión adversarial: FUENTE ÚNICA del criterio de parseo
# [roles-and-jira-flow T-fix1]. La usan `task-brief.py` (inyección de gaps al implementer) y
# `skills/jira-sync/scripts/jira-flow.py` (eventos `revision`/`gaps`). Antes cada uno tenía su
# copia y NO coincidían: jira-flow exigía `:` tras el número de intento y task-brief no, así que
# una cabecera sin `:` daba brief CON gaps y Jira exit 2 sobre el MISMO ledger. Criterio único (el
# laxo): los dos puntos y el resumen son OPCIONALES; grupo 1 = número de intento, grupo 2 = resumen
# (None si no hay). Quien necesite una copia local (paquete portable sin este kit) debe replicar
# este patrón LITERALMENTE — hay test que compara las dos cadenas. Las copias vivas están DECLARADAS
# en `agent-kits/shared/copias.json` (bloque `revision_hdr_pattern`, ADR-016).
REVISION_HDR_PATTERN = \
    r"^##\s+Revisi[oó]n de dos lentes\s*[\u2014\u2013-]\s*intento\s+(\d+)\s*(?::\s*(.*))?$"
REVISION_HDR_RE = re.compile(REVISION_HDR_PATTERN, re.M)

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
    for m in REVISION_HDR_RE.finditer(limpio):
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


# --8<-- fin secciones_revision

def parse_verificacion(lines, i):
    """Parsea el campo Verificación que EMPIEZA en lines[i]. Devuelve (info, siguiente_i) o (None, i)
    si la línea no es el campo. info = {"items": [str], "ejecutada": str|None, "inline": str}.
    Formas: en línea (ítems separados por ` · `), sub-lista (`  - ítem` indentados justo debajo; termina
    en la primera línea que no sea un ítem indentado) o mezcla de ambas."""
    m = VERIF_RE.match(lines[i])
    if not m:
        return None, i
    paren = m.group("paren")
    inline = m.group("inline").strip()
    items = [s.strip() for s in re.split(r"\s+·\s+", inline) if s.strip()] if inline else []
    j = i + 1
    while j < len(lines):
        ms = _SUBITEM_RE.match(lines[j])
        if not ms or _CAMPO_LEDGER_RE.match(lines[j]):
            # un `  - **Changelog**: …` indentado bajo `- **Verificación**:` es EL CAMPO, no un
            # ítem de la verificación: si esta sub-lista se lo comía, el generador lo publicaba y
            # este linter avisaba de «sin campo Changelog» sobre el MISMO ledger.
            break
        items.append(ms.group(1).strip())
        j += 1
    ejecutada = paren[1:-1].strip() if paren else None
    return {"items": items, "ejecutada": ejecutada, "inline": inline}, j


def parse_ledger(text):
    """Parser ESTRUCTURAL del ledger (sin efectos secundarios, importable).

    Devuelve un dict:
      frontmatter: {clave: valor} del bloque YAML inicial (solo `clave: valor` planos)
      estado_tabla: valor de la fila `| **Estado** | … |` de la tabla de cabecera (o None)
      fases: [{"nombre": str, "tareas": [tarea, …]}, …]  (cabeceras `## Fase …`)
      huerfanas: [tarea, …]  (tareas `### T-XX` fuera de toda fase)
      tareas: todas las tareas en orden de aparición
    Cada tarea: {"id", "titulo", "estado" (normalizado o None), "checked", "unchecked",
                 "tiene_criterios", "ia_real_h" (float o None), "ia_est_h" (float o None),
                 "ia_real_fuente" ("medido" | "estimado" | None: cómo se obtuvo el real),
                 "verificacion" (texto plano del campo `- **Verificación**:`: ítems unidos por ` · `,
                 "" si el campo existe pero está vacío, None si no existe),
                 "verificacion_items" ([str]: un ítem por comando → resultado),
                 "verificacion_ejecutada" (texto del paréntesis `(ejecutada …)` o None),
                 "changelog" (texto del campo `- **Changelog**:`, "" si existe vacío, None si no)}.
    Lo consumen `lint()` (aquí) y `progress-report.py` (línea de progreso).
    """
    text = text.lstrip("\ufeff")          # BOM UTF-8: sin esto el frontmatter no se reconoce
    # Las líneas DENTRO de una valla de código se vacían antes de parsear: un `## Ejemplo` o un
    # `- **Changelog**:` citados en una valla ```markdown no son estructura del ledger.
    lines = sin_vallas(text).splitlines()

    # ---- frontmatter (claves planas) y tabla de cabecera ----
    frontmatter = {}
    if lines and lines[0].strip() == "---":
        for ln in lines[1:]:
            if ln.strip() == "---":
                break
            m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", ln)
            if m:
                val = m.group(2).split("#", 1)[0].strip()
                frontmatter[m.group(1)] = val
    m = re.search(r"^\|\s*\*\*Estado\*\*\s*\|\s*([^|]+)\|", text, re.M)
    estado_tabla = norm_estado(m.group(1)) if m else None

    # ---- estructura: fases y tareas ----
    fase_re = re.compile(r"^##\s+(Fase\b[^\n]*)")
    task_re = re.compile(r"^###\s+(T-\d+)\b\s*(?:[—–:-]\s*)?(.*)$")
    estado_re = re.compile(r"^\s*-\s*\*\*Estado\*\*\s*:\s*(.+)$")
    # Estado de la FASE: va como párrafo en negrita (`**Estado**: completado · **Estimado**: …`),
    # no como viñeta de tarea. Se recoge para detectar la fase que declara DOS estados a la vez
    # (gap A-4 de la revisión de R4b): el ledger se contradecía —«completado, 9/9» y
    # «en-progreso … sin empezar» en la misma fase— y `ledger-lint` salía 0 sin verlo.
    fase_estado_re = re.compile(r"^\s*\*\*Estado\*\*\s*:\s*(.+)$")
    ia_re = re.compile(r"^\s*-\s*\*\*Tiempo IA[^*]*\*\*\s*:\s*(.+)$")
    check_re = re.compile(r"^\s*[-*]\s*\[( |x|X)\]")

    fases = []
    huerfanas = []
    cur_fase = None
    cur_task = None
    in_criterios = False

    def close_task():
        nonlocal cur_task
        if cur_task is not None:
            (cur_fase["tareas"] if cur_fase else huerfanas).append(cur_task)
            cur_task = None

    idx = 0
    while idx < len(lines):
        ln = lines[idx]
        idx += 1
        m = fase_re.match(ln)
        if m:
            close_task()
            cur_fase = {"nombre": m.group(1).strip(), "tareas": [], "estados": []}
            fases.append(cur_fase)
            continue
        if re.match(r"^##\s", ln) and not fase_re.match(ln):
            # sección de nivel 2 que no es una fase (Apéndice, Notas...) → cierra la fase
            close_task()
            cur_fase = None
            continue
        if re.match(r"^###\s+Fase\b", ln):
            # MINOR 8: `### Fase …` cierra el bloque de la tarea en `changelog-sync` (parte ahí) y
            # aquí no lo cerraba, así que un campo escrito bajo `### Fase 2` se atribuía distinto en
            # cada parser. Mismo criterio en los dos.
            close_task()
            continue
        if cur_task is None and cur_fase is not None:
            m = fase_estado_re.match(ln)
            if m:
                cur_fase["estados"].append((idx, m.group(1).strip()))
        m = task_re.match(ln)
        if m:
            close_task()
            # Título sin énfasis: `**Bold** resto` → `Bold resto` (la negrita interior salía con
            # los `**` en la línea de progreso — deuda de live-visibility, saldada en debt-cleanup)
            titulo = re.sub(r"\*\*(.+?)\*\*", r"\1", m.group(2)).strip().strip("*").strip()
            cur_task = {"id": m.group(1), "titulo": titulo,
                        "estado": None, "unchecked": 0, "checked": 0,
                        "tiene_criterios": False, "ia_real_h": None, "ia_est_h": None,
                        "ia_real_fuente": None, "verificacion": None,
                        "verificacion_items": [], "verificacion_ejecutada": None,
                        "changelog": None}
            in_criterios = False
            continue
        if cur_task is not None:
            m = estado_re.match(ln)
            if m and cur_task["estado"] is None:
                cur_task["estado"] = norm_estado(m.group(1))
                continue
            if cur_task["verificacion"] is None and VERIF_RE.match(ln):
                info, nxt = parse_verificacion(lines, idx - 1)
                cur_task["verificacion"] = " · ".join(info["items"])
                cur_task["verificacion_items"] = info["items"]
                cur_task["verificacion_ejecutada"] = info["ejecutada"]
                idx = nxt          # los ítems de la sub-lista ya están consumidos
                continue
            m = CHANGELOG_RE.match(ln)
            if m and cur_task["changelog"] is None:
                partes = [m.group("txt").strip()]
                while idx < len(lines) and es_continuacion(lines[idx]):
                    partes.append(lines[idx].strip())
                    idx += 1               # continuación indentada: absorbida, no perdida
                cur_task["changelog"] = " ".join(p for p in partes if p).strip()
                continue
            m = ia_re.match(ln)
            if m and cur_task["ia_real_h"] is None and cur_task["ia_est_h"] is None:
                cur_task["ia_est_h"], cur_task["ia_real_h"] = _parse_horas(m.group(1))
                if cur_task["ia_real_h"] is not None:
                    cur_task["ia_real_fuente"] = "estimado" if re.search(
                        r"\(\s*estimad[oa]\s*\)", m.group(1), re.I) else "medido"
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
                    # párrafo/encabezado de nivel superior → fin del bloque de criterios. Vuelto al
                    # comportamiento de `bcf564c` (gap 70 de la revisión tramo 2): la variante
                    # anterior (`^[-*]\s`, exigiendo espacio tras el marcador) excluía del bloque
                    # cualquier línea en **negrita** a columna 0 (`**Subtareas**`, `**Checklist
                    # manual…**`) porque no hay espacio tras el segundo `*` — eso cambiaba el
                    # conteo de criterios en 177 tareas de 24 ledgers del repo (verificado:
                    # `parse_ledger` de los 41 `tasks.md` contra `bcf564c` da 0 con ESTE check).
                    # Una línea en negrita a columna 0 (`**Algo**` o `**Algo**:`) sigue sin contar
                    # como criterio (no matchea `check_re`, que exige `[ ]`/`[x]`) — CONTINÚA el
                    # bloque, no lo cierra; lo que sí sigue bloqueando `completado` es un `- [ ]`
                    # REAL bajo esa negrita (ver `tests/test_ledger_lint.py`, casos `con_checklist`
                    # y `con_checklist_pendiente_real`).
                    in_criterios = False
    close_task()

    tareas = [t for f in fases for t in f["tareas"]] + huerfanas
    return {"frontmatter": frontmatter, "estado_tabla": estado_tabla,
            "fases": fases, "huerfanas": huerfanas, "tareas": tareas}


_HORAS_RE = r"[.:]?\s*(\d+(?:[.,]\d+)?)\s*h(?:\s*(\d{1,2})\s*m(?:in)?)?"


def _parse_horas(campo):
    """'est. 0,3h · real 1,2h (medido)' → (0.3, 1.2); 'real 1h30m' → 1.5; 'real: 2h' → 2.0;
    'real —' → None. Tolerante."""
    def num(m):
        if not m:
            return None
        try:
            h = float(m.group(1).replace(",", "."))
            return h + (int(m.group(2)) / 60 if m.group(2) else 0)
        except ValueError:
            return None
    est = num(re.search(r"\best" + _HORAS_RE, campo, re.I))
    real = num(re.search(r"\breal" + _HORAS_RE, campo, re.I))
    return est, real


def lint(path):
    errors, warnings = [], []
    try:
        text = open(path, encoding="utf-8").read()
    except UnicodeDecodeError:
        text = open(path, encoding="utf-8", errors="replace").read()
        warnings.append("el fichero no es UTF-8 limpio (leído con reemplazos)")

    if "edger canónico" not in text and "edger can" not in text:
        warnings.append("falta el banner de «ledger canónico» (formato legacy)")

    parsed = parse_ledger(text)
    fases = [(f["nombre"], f["tareas"]) for f in parsed["fases"]]
    all_tasks = parsed["tareas"]

    # Una fase con DOS líneas `**Estado**:` es una contradicción, no un descuido de formato: la
    # nueva dice «completado» y la vieja se queda diciendo «sin empezar», y quien lee el ledger (o
    # el orquestador que decide si el tramo sigue) cree la que encuentra primero.
    for f in parsed["fases"]:
        ests = f.get("estados") or []
        if len(ests) > 1:
            detalle = " · ".join(f"línea {n}: «{v[:60]}»" for n, v in ests)
            errors.append(f"fase «{f['nombre'][:40]}»: {len(ests)} líneas `**Estado**:` — "
                          f"el ledger se contradice ({detalle})")

    seen_ids = set()
    for t in all_tasks:
        if t["id"] in seen_ids:
            errors.append(f"ID de tarea duplicado: {t['id']}")
        seen_ids.add(t["id"])

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

    # ---- Verificación por tarea (plan-and-diet T-02) ----
    verif_fm = norm_estado(parsed["frontmatter"].get("verificacion", "")) if parsed["frontmatter"].get("verificacion") else ""
    usa_verif = any(t["verificacion"] for t in all_tasks)
    for t in all_tasks:
        if t["verificacion"]:
            continue
        que = ("campo **Verificación** VACÍO (ni texto en línea ni sub-lista `  - cmd → resultado` debajo)"
               if t["verificacion"] == "" else "sin campo **Verificación**")
        if verif_fm == "obligatoria":
            errors.append(f"{t['id']}: {que} (el ledger declara "
                          f"verificacion: obligatoria) — sin verificación ejecutable la tarea no está bien definida")
        elif verif_fm or usa_verif:
            warnings.append(f"{t['id']}: {que}"
                            + (" (otras tareas lo declaran)" if usa_verif else ""))

    # ---- Changelog por tarea (changelog-brief): AVISO, nunca incoherencia ----
    # Opcional por diseño. Solo se avisa en ADOPCIÓN PARCIAL (alguna tarea lo trae y otra no) o
    # con el campo presente y vacío: un ledger que no lo usa en ninguna tarea valida idéntico a
    # antes. El recordatorio a escribirlo lo da `changelog-sync.py --check`.
    # Un campo con placeholder `{{…}}` NO cuenta como escrito, igual que para `changelog-sync`:
    # si contara, un ledger recién copiado de la plantilla acusaría de «adopción parcial» a las
    # tareas honestas que todavía no lo traen.
    usa_changelog = any(t["changelog"] and not es_placeholder(t["changelog"])
                        for t in all_tasks)
    for t in all_tasks:
        if es_placeholder(t["changelog"]):
            warnings.append(f"{t['id']}: campo **Changelog** sin sustituir (ES el placeholder "
                            f"`{{{{…}}}}` de la plantilla) — `changelog-sync` lo IGNORA y el "
                            f"bullet degrada al título; escribe la frase de verdad o quita el "
                            f"campo")
            continue
        if t["changelog"]:
            continue
        if t["changelog"] == "":
            warnings.append(f"{t['id']}: campo **Changelog** VACÍO — escribe una frase (qué cambia "
                            f"para quien USA el proyecto) o quita el campo")
        elif usa_changelog:
            warnings.append(f"{t['id']}: sin campo **Changelog** (otras tareas lo declaran) — su "
                            f"bullet del CHANGELOG degradará al título")

    # ---- cabeceras de revisión que no casan con REVISION_HDR_PATTERN (T-04, jira-review-comments) ----
    # `jira-flow.py` (evento `revision`/`gaps`) y `task-brief.py` solo VEN las secciones que casan con
    # este patrón — una cabecera con paréntesis tras el número («intento 1 (Fase 2: T-04): …») no
    # casa (el patrón exige `:` o fin de línea justo tras el número) y esa sección queda invisible
    # para los dos, sin aviso alguno hasta ahora: el implementer creía que el mecanismo fallaba
    # cuando en realidad la sección nunca se veía. Respeta `sin_vallas()` [gap #12]: una cabecera
    # citada dentro de una valla de código (ejemplo en la propia doc del ledger) no es una sección
    # de revisión real y no debe avisar. Acepta `##` Y `###` [gap #13]: `secciones_revision()` solo
    # reconoce `##` exacto, así que un `### Revisión…` tampoco se ve — y el aviso original, con
    # `startswith("## Revisi")`, no lo detectaba (ni con dos ni con tres almohadillas si además
    # llevaba paréntesis).
    limpio_para_aviso = sin_vallas(text)
    for i, (ln, ln_limpia) in enumerate(zip(text.splitlines(), limpio_para_aviso.splitlines()), 1):
        s = ln_limpia.strip()
        if re.match(r"^#{2,3}\s+Revisi", s) and "dos lentes" in s and not REVISION_HDR_RE.match(s):
            warnings.append(
                f"línea {i}: cabecera de revisión no casa con REVISION_HDR_PATTERN: "
                f"jira-flow/task-brief no la verán — usa `## Revisión de dos lentes — "
                f"intento N: <resumen>` (`##` exacto, sin paréntesis tras N)")

    # ---- tabla de resumen (completadas/total por fase) ----
    resumen_rows = re.findall(
        r"^\|\s*\*{0,2}\s*(Fase\s+(?:\d+|única|unica)\b[^|*]*)\*{0,2}\s*\|\s*\*{0,2}(\d+)\*{0,2}\*?\s*\|\s*\*{0,2}(\d+)\*{0,2}\s*\|",
        text, re.M | re.I)
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
    # captura sufijos ("Fase 3-bis") para que no colisionen con "Fase 3"; «Fase única» (vía
    # rápida: una sola fase sin número) también es una clave válida
    m = re.match(r"\s*Fase\s+(\d+(?:[.-]\w+)*|única|unica)\b", s, re.I)
    return f"fase-{m.group(1).lower().replace('ú', 'u')}" if m else s.strip().lower()


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
