#!/usr/bin/env python3
"""jira-flow.py — ciclo de eventos DETERMINISTA de jira-sync (firmado por agente).

(Iniciativa roles-and-jira-flow T-02: «que cuando Jira esté configurado se vaya cambiando de
estado, el implementer añada comentarios de lo que hizo, el reviewer añada comentarios de la
revisión, y si está bien pase a Done, o que el implementer sea notificado». Fix de comportamiento:
antes, el issue pasaba a Done en cuanto la TAREA del ledger llegaba a `completado` — es decir,
justo tras implementar, ANTES de la revisión de dos lentes y de `qa` (orden real de
`commands/dev-cycle.md` Fase 3: 1) implementer, 2) revisión, 3) qa). Aquí se separa la
IMPUTACIÓN de horas (incondicional, al completar cada evento) de la transición a Done (solo con
el evento `aprobado`, que el orquestador dispara cuando revisión Y qa han dado su visto bueno).)

Qué hace (y qué NO hace)
  Dado un evento del ciclo, LEE el ledger (`tasks.md`) y genera el PLAN de operaciones Jira
  — transición · etiqueta · comentario (ya redactado, firmado) · comando de `worklog.py` — que el
  agente/orquestador ejecuta luego vía el conector Atlassian (Rovo MCP). Este script NUNCA llama
  al conector: no hay red aquí, solo lectura del ledger + relleno de plantillas fijas. El MODELO
  no redacta el comentario: los textos vienen de `assets/comment-<evento>.md` con huecos que este
  script rellena SOLO con lo que el ledger ya dice (Descripción/Archivos/Verificación/horas, o la
  fila del intento de revisión) — nunca inventa prosa ni cifras.

  Firma OBLIGATORIA en cada comentario (para saber qué agente comentó cada cosa):
    > 🤖 **[custom-agents · <agente>]** · <rol> · <fecha>
  Etiqueta Jira por actor (para filtrar en Jira): `ca-implementer` · `ca-reviewer` · `ca-qa` ·
  `ca-orquestador` (el cierre del evento `aprobado`).

Eventos (7; el actor que los dispara es fijo — `--actor` debe casar o exit 2):
  arrancar      (implementer)  transición → en curso (lógico `en-curso`).       Sin comentario.
  implementado  (implementer)  comentario (qué se hizo) + worklog `implementacion`. Sin transición
                (regla dura: YA NO pasa a Done aquí — antes lo hacía, era el bug).
  revision      (reviewer)     comentario «sin gaps» + worklog `revision --attempt N`. Sin transición.
  gaps          (reviewer)     transición → en curso (lógico `reabrir`: un intento con gaps REABRE
                el issue) + comentario con la tabla de gaps + worklog `revision --attempt N`. El
                aviso al implementer va por el LADO DEL LEDGER (para que el subagente de la
                corrección lo vea): lo hace `agent-kits/shared/task-brief.py` (inyección de gaps
                pendientes), no este script.
  aprobado      (orquestador)  transición → Done (lógico `done`) + comentario de cierre firmado por
                el orquestador (`ca-orquestador`). NO lo dispara `qa` ni ningún otro agente, y NO se
                emite a ciegas: exige EVIDENCIA en el ledger (última sección de revisión sin gaps
                pendientes para esas tareas) Y `--qa-verde` (el orquestador solo pasa ese flag tras
                leer el exit 0 de `agent-kits/qa/qa-gate.py`). Sin evidencia → exit 2 con la razón y
                `ops: []`.
  qa-verde      (qa)           comentario con el veredicto + evidencias. Sin transición, sin worklog
                (el tiempo de qa no se imputa aparte; el informe local ya lo documenta).
  qa-rojo       (qa)           comentario con el veredicto + evidencias. Sin transición, sin worklog.

Por qué 7 eventos y 6 plantillas: `arrancar` es transición pura (no hay nada nuevo que contar); los
otros 6 llevan comentario+plantilla propia. `revision`/`gaps` son las dos salidas posibles de UN
intento de revisión — el propio script decide cuál aplica mirando si hay filas de gaps para esa
tarea en la sección del intento (exit 2 si el evento pedido no casa con lo que dice el ledger: pide
`--event gaps` con un intento sin gaps, o al revés).

Tres guardarraíles deterministas más (T-fix1), porque un plan que se publica dos veces o con Jira
apagado hace daño real en el Jira del equipo:
  · **Opt-in de verdad.** Lee `.claude/jira.json` (`--root`, o cwd hacia arriba: misma resolución
    que `worklog.py`). Si `enabled` no es exactamente `true` → `ops: []`, `jira: "desactivado"`,
    exit 0 y sin ruido: el ciclo es idéntico, simplemente no publica.
  · **Idempotencia.** Cada plan con `ops` se anota en `jira-state.json` bajo
    `flow["<issue>|<evento>|<tareas>|<intento>"] = {"fecha": …}`. Repetir el MISMO evento →
    `ops: []` + `yaRealizado: true` + exit 0 (no un segundo comentario en Jira); `--force` lo
    repite a propósito. Estado corrupto o de solo lectura → aviso y sigue, nunca bloquea.
  · **`--intento` obligatorio en `revision`/`gaps`.** Antes caía a 1 en silencio: publicaba los gaps
    del intento 1 con el pie «intento 2 de 3». Ahora falta → exit 2, y se usa SIEMPRE la sección de
    ESE intento.
Las validaciones de USO (actor que no casa, `--intento` ausente, tarea inexistente, evidencia de
`aprobado`) se comprueban con Jira encendido o apagado: son errores de la llamada, no publicaciones.

Uso:
  jira-flow.py plan --ledger <tasks.md> --event <evento>
                     --actor <implementer|reviewer|qa|orquestador>
                     --task T-01[,T-02,...] [--batch] [--intento N] [--issue KEY] [--state PATH]
                     [--root DIR] [--force] [--qa-verde] [--resumen TEXTO] [--evidencia RUTA]
                     [--fecha YYYY-MM-DD] [--json]
  Salida por defecto: resumen legible. --json: el plan completo (ops[], avisos[]) para ejecutar.
Exit: 0 plan generado (aunque falte el issueKey — degrada con aviso, nunca bloquea; también con
      Jira apagado o evento ya realizado: `ops: []`) ·
      2 error de uso (ledger inválido, tarea inexistente, actor no casa con el evento, `--intento`
      ausente en `revision`/`gaps`, evento de revisión que no casa con lo que dice el ledger para
      esa tarea/intento, `aprobado` sin evidencia de revisión limpia + `--qa-verde`).

Reutiliza `agent-kits/shared/ledger-lint.py` (`parse_ledger`, `_parse_horas`) como fuente única
del parseo del ledger — el mismo patrón que ya usa `scope-check.py`. Solo stdlib.
"""
import argparse
import datetime
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
ASSETS = os.path.join(SKILL_DIR, "assets")
REPO_ROOT_DESDE_SKILL = os.path.dirname(os.path.dirname(SKILL_DIR))  # skills/jira-sync/scripts → …/skills → raíz

EVENTOS = ("arrancar", "implementado", "revision", "gaps", "aprobado", "qa-verde", "qa-rojo")
# Quién dispara cada evento (fuente única: la tabla «Ciclo Jira de la Fase 3» de
# `commands/dev-cycle.md`). `aprobado` es del ORQUESTADOR, no de `qa`: es la única puerta que mira
# DOS veredictos a la vez (revisión sin gaps + qa verde) y ningún agente ve los dos (T-fix1).
ACTOR_DE_EVENTO = {
    "arrancar": "implementer", "implementado": "implementer",
    "revision": "reviewer", "gaps": "reviewer",
    "aprobado": "orquestador", "qa-verde": "qa", "qa-rojo": "qa",
}
ROL = {"implementer": "implementador", "reviewer": "revisor", "qa": "verificación (qa)",
       "orquestador": "orquestación del ciclo (/dev-cycle)"}
PLANTILLA_DE_EVENTO = {  # evento -> fichero de assets/ (None = evento de transición pura, sin comentario)
    "arrancar": None,
    "implementado": "comment-implementado.md",
    "revision": "comment-revision-aprobada.md",
    "gaps": "comment-revision-gaps.md",
    "aprobado": "comment-aprobado.md",
    "qa-verde": "comment-qa-verde.md",
    "qa-rojo": "comment-qa-rojo.md",
}
EVENTOS_CON_INTENTO = ("revision", "gaps", "qa-verde", "qa-rojo")
# En `revision`/`gaps` el intento NO puede caer a 1 en silencio: el número elige la SECCIÓN del
# ledger que se publica y el pie «intento N+1 de 3» del comentario. Sin él → exit 2 (T-fix1).
EVENTOS_INTENTO_OBLIGATORIO = ("revision", "gaps")
# Marcadores de una fila de gap SIN corregir (celda «Corrección» vacía o con un placeholder):
# bloquean `aprobado`. Una fila `descartado (rebatido)` NO bloquea: es una decisión tomada.
_GAP_PENDIENTE_RE = re.compile(r"^(?:|-+|—|–|n/?a|todo|pendiente\b.*|sin corregir\b.*|\?+)$", re.I)
_GAP_REBATIDO_RE = re.compile(r"rebatid|descartad", re.I)


def _cargar_ledger_lint():
    """`agent-kits/shared/ledger-lint.py` por ruta (mismo patrón que `scope-check.py`). Ya viaja con
    el paquete portable: `references/create-and-writeback.md` lo cita (`fragmentos_shared`, T-01
    de esta iniciativa/`export-skills.py`)."""
    path = os.path.join(REPO_ROOT_DESDE_SKILL, "agent-kits", "shared", "ledger-lint.py")
    if not os.path.isfile(path):
        return None
    spec = importlib.util.spec_from_file_location("ledger_lint_jf", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ------------------------------------------------------------------ ledger: bloque de UNA tarea

_TASK_BLOCK_RE = r"\n(?=###\s+T-\d+\b)"


def _bloque_de_tarea(texto, tid):
    """Texto crudo de `### T-XX … ` hasta la siguiente `### T-YY` o `## `, o None si no existe."""
    partes = re.split(_TASK_BLOCK_RE, texto)
    for p in partes:
        m = re.match(r"###\s+(T-\d+)\b", p.strip())
        if m and m.group(1) == tid:
            # corta en el siguiente encabezado `## ` (fin de la fase / sección de apéndice)
            corte = re.search(r"\n##\s", p)
            return p[:corte.start()] if corte else p
    return None


def _campo(bloque, nombre):
    """Valor de `- **Nombre**: valor` (tolera un paréntesis entre el `**` y los dos puntos, como
    en `- **Verificación** (ejecutada 2026-…: salida …): python3 -m pytest … → …`)."""
    m = re.search(rf"^-\s*\*\*{re.escape(nombre)}\*\*(?:\s*\([^\n]*?\))?\s*:\s*(.+)$", bloque, re.M)
    return m.group(1).strip() if m else None


def _acortar(texto, n=160):
    texto = (texto or "").strip()
    return texto if len(texto) <= n else texto[:n].rstrip() + "…"


def _primera_frase(s):
    """Corta en el primer punto seguido de espacio+mayúscula (evita «p. ej.», versiones, horas)."""
    s = re.sub(r"\s+", " ", (s or "")).strip()
    m = re.search(r"\.(?=\s+[A-ZÁÉÍÓÚÑ¿«`])", s)
    return (s[: m.start()] if m else s).rstrip(" .") + ("." if s else "")


def _archivos_clave(campo_archivos, maximo=5):
    out = []
    for tok in re.findall(r"`([^`]+)`", campo_archivos or ""):
        tok = re.sub(r"\s*\([^)]*\)", "", tok).strip()
        if tok and tok not in out:
            out.append(tok)
        if len(out) >= maximo:
            break
    return out


def detalle_tarea(texto, tid, ledger_lint):
    """dict con lo que hace falta para el comentario `implementado` de UNA tarea, TODO leído del
    ledger (nunca inventado). None si la tarea no existe en el ledger."""
    bloque = _bloque_de_tarea(texto, tid)
    if bloque is None:
        return None
    titulo_m = re.match(r"###\s+T-\d+\s*(?:[—–:-]\s*)?(.*)", bloque.strip().splitlines()[0])
    titulo = re.sub(r"\*\*(.+?)\*\*", r"\1", (titulo_m.group(1) if titulo_m else "")).strip()
    desc = _primera_frase(_campo(bloque, "Descripción") or "")
    archivos = _archivos_clave(_campo(bloque, "Archivos") or "")
    verif = _acortar(_campo(bloque, "Verificación"))
    ia_est, ia_real = (None, None)
    hum_est, hum_real = (None, None)
    sup_est, sup_real = (None, None)
    if ledger_lint:
        ia_campo = _campo(bloque, "Tiempo IA (ejec.)")
        if ia_campo:
            ia_est, ia_real = ledger_lint._parse_horas(ia_campo)
        hum_campo = _campo(bloque, "Tiempo humano")
        if hum_campo:
            hum_est, hum_real = ledger_lint._parse_horas(hum_campo)
        sup_campo = _campo(bloque, "Supervisión")
        if sup_campo:
            sup_est, sup_real = ledger_lint._parse_horas(sup_campo)
    return {
        "id": tid, "titulo": titulo or tid, "descripcion": desc,
        "archivos": archivos, "verificacion": verif or "—",
        "ia_est": ia_est, "ia_real": ia_real,
        "hum_est": hum_est, "hum_real": hum_real,
        "sup_est": sup_est, "sup_real": sup_real,
    }


# ------------------------------------------------------------------ ledger: sección de revisión

# Copia LITERAL de `REVISION_HDR_PATTERN` de `agent-kits/shared/ledger-lint.py`, solo para cuando
# el kit no viaja con el paquete portable. `test_jira_flow.py` compara las dos cadenas: si divergen,
# el test falla. Antes esta regex EXIGÍA `:` tras el número y la de `task-brief.py` no, así que una
# cabecera sin `:` daba brief CON gaps y este script exit 2 sobre el MISMO ledger (T-fix1).
_REVISION_HDR_FALLBACK = \
    r"^##\s+Revisi[oó]n de dos lentes\s*[\u2014\u2013-]\s*intento\s+(\d+)\s*(?::\s*(.*))?$"


def _revision_hdr_re(ledger_lint=None):
    """Regex canónica de `## Revisión de dos lentes — intento N` (de `ledger-lint.py`), o la copia
    literal de arriba si el kit no está: UN solo criterio para el brief y para Jira."""
    pat = getattr(ledger_lint, "REVISION_HDR_PATTERN", None) if ledger_lint is not None else None
    return re.compile(pat or _REVISION_HDR_FALLBACK, re.M)


_REVISION_HDR_RE = _revision_hdr_re(_cargar_ledger_lint())


def _split_fila_md(ln):
    """Divide una fila de tabla Markdown por `|`, IGNORANDO los `|` dentro de un tramo `` `código` ``
    (gaps reales del ledger citan regex con alternancia `a|b|c` en un code span — un split ingenuo
    trocea la celda). No es un parser Markdown completo: basta para code spans de una línea."""
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


def seccion_revision(texto, intento):
    """(resumen_cabecera, [filas de gap]) de la sección `## Revisión de dos lentes — intento N`.
    Cada fila: {"grado","gap","tarea","correccion","evidencia"}. (None, []) si no existe esa N."""
    matches = list(_REVISION_HDR_RE.finditer(texto))
    objetivo = next((m for m in matches if int(m.group(1)) == intento), None)
    if not objetivo:
        return None, []
    resumen = (objetivo.group(2) or "").strip()   # cabecera sin `: resumen` → cadena vacía
    inicio = objetivo.end()
    fin = matches[matches.index(objetivo) + 1].start() if matches.index(objetivo) + 1 < len(matches) \
        else len(texto)
    cuerpo = texto[inicio:fin]
    # párrafo de contexto ANTES de la tabla (si lo hay) — se une al resumen de la cabecera; se para
    # en la primera fila `|` para no arrastrar notas/callouts posteriores a la tabla (pueden ser largos)
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
        ln = ln.strip()
        if not ln.startswith("|") or set(ln.replace("|", "").strip()) <= {"-", " "}:
            continue
        celdas = _split_fila_md(ln)
        if len(celdas) < 6 or celdas[0] in ("#", ""):
            continue
        if not re.match(r"^\d+$", celdas[0]):
            continue
        filas.append({"num": celdas[0], "grado": celdas[1], "gap": celdas[2],
                      "tarea": celdas[3], "correccion": celdas[4], "evidencia": celdas[5]})
    return resumen, filas


# ------------------------------------------------------------------ plantillas + firma

def _firma(actor, fecha):
    return f"> 🤖 **[custom-agents · {actor}]** · {ROL[actor]} · {fecha}"


def _plantilla(nombre):
    path = os.path.join(ASSETS, nombre)
    with open(path, encoding="utf-8") as f:
        return f.read()


def _rellenar(plantilla, valores):
    out = plantilla
    for k, v in valores.items():
        out = out.replace("{{" + k + "}}", str(v))
    faltan = re.findall(r"\{\{(\w+)\}\}", out)
    if faltan:
        raise ValueError(f"placeholders sin rellenar: {sorted(set(faltan))}")
    return out.strip() + "\n"


def _fmt_horas(d):
    partes = []
    if d.get("ia_real") is not None or d.get("ia_est") is not None:
        h = d["ia_real"] if d["ia_real"] is not None else d["ia_est"]
        partes.append(f"IA {h:g}h" + ("" if d["ia_real"] is not None else " (est.)"))
    if d.get("sup_real") is not None or d.get("sup_est") is not None:
        h = d["sup_real"] if d["sup_real"] is not None else d["sup_est"]
        partes.append(f"supervisión {h:g}h" + ("" if d["sup_real"] is not None else " (est.)"))
    if not partes and (d.get("hum_real") is not None or d.get("hum_est") is not None):
        h = d["hum_real"] if d["hum_real"] is not None else d["hum_est"]
        partes.append(f"humano {h:g}h" + ("" if d["hum_real"] is not None else " (est.)"))
    return " · ".join(partes) if partes else "—"


def render_implementado(tareas_det, actor, fecha):
    bloques = []
    for d in tareas_det:
        bloques.append(
            f"**{d['id']}** — {d['titulo']}\n{d['descripcion']}\n"
            f"Archivos: {', '.join('`' + a + '`' for a in d['archivos']) or '—'} · "
            f"Verificación: {d['verificacion']} · Horas: {_fmt_horas(d)}")
    valores = {"firma": _firma(actor, fecha), "tareas": ", ".join(d["id"] for d in tareas_det),
              "tareas_detalle": "\n\n".join(bloques)}
    return _rellenar(_plantilla(PLANTILLA_DE_EVENTO["implementado"]), valores)


def render_revision(actor, fecha, intento, tareas, resumen):
    valores = {"firma": _firma(actor, fecha), "intento": intento, "tareas": ", ".join(tareas),
              "resumen": _acortar(resumen, 400) or "sin gaps para estas tareas."}
    return _rellenar(_plantilla(PLANTILLA_DE_EVENTO["revision"]), valores)


def render_gaps(actor, fecha, intento, tareas, filas):
    cab = "| # | Grado | Gap | Tarea | Corrección | Evidencia |\n|---|---|---|---|---|---|\n"
    filas_txt = "\n".join(
        f"| {f['num']} | {f['grado']} | {f['gap']} | {f['tarea']} | {f['correccion']} | {f['evidencia']} |"
        for f in filas)
    valores = {"firma": _firma(actor, fecha), "intento": intento, "n_gaps": len(filas),
              "tareas": ", ".join(tareas), "tabla_gaps": cab + filas_txt,
              "siguiente": intento + 1}
    return _rellenar(_plantilla(PLANTILLA_DE_EVENTO["gaps"]), valores)


def render_aprobado(actor, fecha, tareas, intento, resumen):
    """Comentario de CIERRE del evento `aprobado`, firmado por el ORQUESTADOR (`ca-orquestador`).
    Antes `aprobado` no comentaba nada: el issue pasaba a Done sin dejar en Jira quién lo cerró ni
    con qué evidencia — justo lo que pedía la decisión del usuario («que se sepa quién comentó»), y
    lo que la tabla de la Fase 3 de `/dev-cycle` ya prometía en su columna «Comentario» (T-fix1)."""
    valores = {"firma": _firma(actor, fecha), "tareas": ", ".join(tareas), "intento": intento,
              "resumen": _acortar(resumen, 180) or "sin gaps."}
    return _rellenar(_plantilla(PLANTILLA_DE_EVENTO["aprobado"]), valores)


def render_qa(evento, actor, fecha, intento, tareas, resumen, evidencia):
    valores = {"firma": _firma(actor, fecha), "intento": intento, "tareas": ", ".join(tareas),
              "resumen": resumen or "ver informe.", "evidencia": evidencia}
    return _rellenar(_plantilla(PLANTILLA_DE_EVENTO[evento]), valores)


# ------------------------------------------------------------------ estado: resolver issueKey

def _resolver_issue(state_path, tid):
    if not state_path or not os.path.isfile(state_path):
        return None
    try:
        with open(state_path, encoding="utf-8") as f:
            st = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
    return (st.get("tasks", {}).get(tid, {}) or {}).get("issueKey")


def _find_up(name, start="."):
    d = os.path.abspath(start)
    while True:
        p = os.path.join(d, ".claude", name)
        if os.path.isfile(p):
            return p
        nd = os.path.dirname(d)
        if nd == d:
            return None
        d = nd


# ------------------------------------------------------- opt-in: `.claude/jira.json` (T-fix1 #4)

def _jira_activo(root):
    """(activo, ruta, motivo) leyendo `.claude/jira.json` hacia arriba desde `root` (misma
    resolución que `worklog.py`: `find_up` desde cwd, o desde `--root` si se pasa).

    **`enabled: true` o no se publica NADA.** Antes este script no miraba la config: con
    `{"enabled": false}` seguía devolviendo 3 ops y el agente las ejecutaba en el Jira del equipo.
    Falla CERRADO a propósito (config ausente = no activado): la skill dice que el volcado es
    opt-in y quien llama ya ha pasado por el Paso 0."""
    path = _find_up("jira.json", root)
    if not path:
        return False, None, "sin `.claude/jira.json` (Jira no activado para este proyecto)"
    try:
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        return False, path, f"`{path}` ilegible ({type(e).__name__}) — se trata como no activado"
    if cfg.get("enabled") is not True:
        return False, path, f"`enabled` no es `true` en {path}"
    return True, path, ""


# ------------------------------------------------------- idempotencia: `flow` en el estado (#3)

def _clave_flujo(issue, evento, tareas, intento):
    """Clave del evento ya publicado: `<issue>|<evento>|<tareas>|<intento>`. Con `--batch` las
    tareas van en la clave tal cual (una pasada = una clave), y sin issue resuelto va `-`."""
    return "|".join([issue or "-", evento, ",".join(tareas),
                     str(intento) if intento is not None else "-"])


def _leer_estado(state_path):
    """(dict del estado, aviso|None). Estado ausente → {} sin aviso; corrupto o ilegible → {} CON
    aviso (degrada, nunca bloquea: perder la idempotencia es peor que parar el ciclo)."""
    if not state_path or not os.path.isfile(state_path):
        return {}, None
    try:
        with open(state_path, encoding="utf-8") as f:
            st = json.load(f)
        if not isinstance(st, dict):
            raise ValueError("la raíz no es un objeto")
        return st, None
    except (json.JSONDecodeError, OSError, ValueError) as e:
        return {}, (f"estado `{state_path}` ilegible o corrupto ({type(e).__name__}): sigo sin "
                    f"comprobar idempotencia — revisa si este evento ya se publicó en Jira")


def _anotar_flujo(state_path, clave, fecha):
    """Anota `flow[clave] = {"fecha": …}` en el estado. Devuelve aviso|None: un estado de SOLO
    LECTURA (o un disco lleno) degrada con aviso — el plan sigue siendo válido."""
    if not state_path:
        return "sin `jira-state.json` resoluble: no se anota la idempotencia de este evento"
    st, _ = _leer_estado(state_path)
    st.setdefault("flow", {})[clave] = {"fecha": fecha}
    try:
        os.makedirs(os.path.dirname(os.path.abspath(state_path)), exist_ok=True)
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(st, f, ensure_ascii=False, indent=2)
        return None
    except OSError as e:
        return (f"no se pudo anotar la idempotencia en `{state_path}` ({type(e).__name__}): si "
                f"repites este evento, revisa antes en Jira que el comentario no esté ya puesto")


# ------------------------------------- evidencia para `aprobado` (la puerta de Done, T-fix1 #1)

def _gap_pendiente(fila):
    """True si la fila de gap NO tiene corrección registrada (celda vacía o placeholder) y no está
    `descartado (rebatido)`: una tarea con gaps así NO puede pasar a Done."""
    correccion = re.sub(r"[`*_]", "", (fila.get("correccion") or "")).strip()
    evidencia = (fila.get("evidencia") or "").strip()
    if _GAP_REBATIDO_RE.search(correccion) or _GAP_REBATIDO_RE.search(evidencia):
        return False
    return bool(_GAP_PENDIENTE_RE.match(correccion))


def evidencia_aprobado(texto, tareas, qa_verde):
    """(info, razon): qué evidencia respalda un `aprobado`, o por qué NO se puede emitir.

    `aprobado` es el ÚNICO evento que marca Done, así que no se emite a ciegas (antes se emitía
    siempre, sin comprobar nada). Exige las DOS cosas que la tabla de la Fase 3 promete:
      1) **revisión limpia**: existe una sección `## Revisión de dos lentes — intento N` y la
         ÚLTIMA (la N más alta) no deja filas de gap PENDIENTES para esas tareas (sin filas, o
         todas con corrección registrada / `descartado (rebatido)`);
      2) **rastro de qa verde**: `--qa-verde`. El ledger no tiene una marca canónica de «qa verde»
         (el veredicto vive en `docs/roadmap/<slug>/testing/report.md`), así que el flag es la
         declaración explícita del orquestador, que SOLO lo pasa tras leer el **exit 0 de
         `agent-kits/qa/qa-gate.py`** (documentado en `references/progress-sync.md`).
    """
    if not qa_verde:
        return None, ("`aprobado` sin `--qa-verde`: Done exige el verde de qa. Ejecuta "
                      "`agent-kits/qa/qa-gate.py` y, SOLO si su exit es 0, repite con `--qa-verde`")
    matches = list(_REVISION_HDR_RE.finditer(texto))
    if not matches:
        return None, ("`aprobado` sin evidencia: el ledger no tiene ninguna sección `## Revisión de "
                      "dos lentes — intento N`. Sin revisión de dos lentes no hay Done")
    ultimo = max(matches, key=lambda m: int(m.group(1)))
    intento = int(ultimo.group(1))
    # para el cierre basta el resumen de la CABECERA («sin gaps», «12 gaps corregidos (…)»); el
    # párrafo de contexto que `seccion_revision` le pega para el comentario de `revision` aquí solo
    # alargaría el comentario de Done.
    resumen = (ultimo.group(2) or "").strip()
    _, filas = seccion_revision(texto, intento)
    pendientes = [f for f in filas if f["tarea"] in tareas and _gap_pendiente(f)]
    if pendientes:
        detalle = "; ".join(f"#{f['num']} {f['grado']}: {_acortar(f['gap'], 60)}" for f in pendientes)
        return None, (f"`aprobado` bloqueado: el último intento de revisión ({intento}) deja "
                      f"{len(pendientes)} gap(s) sin corrección registrada para "
                      f"{', '.join(tareas)} → {detalle}. Corrígelos (o anótalos como `descartado "
                      f"(rebatido)` con evidencia) y vuelve a intentarlo")
    return {"intento": intento, "resumen": resumen or "", "gaps": len(filas)}, None


# ------------------------------------------------------------------ plan principal

def construir_plan(args):
    ledger_lint = _cargar_ledger_lint()
    with open(args.ledger, encoding="utf-8", errors="replace") as f:
        texto = f.read()

    tareas = [t.strip() for t in args.task.split(",") if t.strip()] if args.batch else [args.task.strip()]
    if not args.batch and "," in args.task:
        return None, ["`--task` con varias tareas requiere `--batch`"], 2
    if not tareas:
        return None, ["`--task` vacío"], 2

    actor_esperado = ACTOR_DE_EVENTO[args.event]
    if args.actor != actor_esperado:
        return None, [f"el evento `{args.event}` lo dispara `{actor_esperado}`, no `{args.actor}` "
                      f"(actor esperado para `{args.event}`: `{actor_esperado}`)"], 2
    if args.event in EVENTOS_INTENTO_OBLIGATORIO and args.intento is None:
        return None, [f"el evento `{args.event}` exige `--intento N`: el número elige la sección "
                      f"`## Revisión de dos lentes — intento N` que se publica y el pie del "
                      f"comentario — no se adivina"], 2

    fecha = args.fecha or datetime.date.today().isoformat()
    avisos = []
    issue_por_tarea = {}
    for tid in tareas:
        if _bloque_de_tarea(texto, tid) is None:
            return None, [f"la tarea `{tid}` no existe en {args.ledger}"], 2

    # --- evidencia de `aprobado`: se comprueba ANTES de resolver issues/estado (es un error de uso)
    evidencia_ok = None
    if args.event == "aprobado":
        evidencia_ok, razon = evidencia_aprobado(texto, tareas, args.qa_verde)
        if evidencia_ok is None:
            return None, [razon], 2

    # --- opt-in: con Jira apagado el ciclo es idéntico, simplemente no publica nada
    root = args.root or os.getcwd()
    activo, cfg_path, motivo = _jira_activo(root)
    if not activo:
        plan = {"evento": args.event, "actor": args.actor, "rol": ROL[args.actor], "fecha": fecha,
               "tareas": tareas, "issueKey": None, "jira": "desactivado", "ops": [],
               "avisos": [f"Jira desactivado: {motivo} — nada que publicar (el ciclo del ledger "
                          f"sigue igual)"]}
        return plan, plan["avisos"], 0

    state_path = args.state or _find_up("jira-state.json", os.path.dirname(os.path.abspath(args.ledger)))
    if not state_path and cfg_path:   # por defecto, hermano de jira.json (donde vive el manifiesto)
        state_path = os.path.join(os.path.dirname(cfg_path), "jira-state.json")
    for tid in tareas:
        key = args.issue if (args.issue and not args.batch) else _resolver_issue(state_path, tid)
        issue_por_tarea[tid] = key
        if not key:
            avisos.append(f"{tid}: sin issueKey en el manifiesto — vuelca el plan a Jira "
                          f"(jira-sync Paso 5) antes de ejecutar este plan")
    issue_principal = args.issue or next((k for k in issue_por_tarea.values() if k), None)

    # --- idempotencia: ¿este mismo evento ya se publicó?
    estado, aviso_estado = _leer_estado(state_path)
    if aviso_estado:
        avisos.append(aviso_estado)
    clave = _clave_flujo(issue_principal, args.event, tareas, args.intento)
    ya = (estado.get("flow") or {}).get(clave) if isinstance(estado.get("flow"), dict) else None
    if ya and not args.force:
        plan = {"evento": args.event, "actor": args.actor, "rol": ROL[args.actor], "fecha": fecha,
               "tareas": tareas, "issueKey": issue_principal, "jira": "activado",
               "yaRealizado": True, "ops": [],
               "avisos": avisos + [f"evento ya publicado el {ya.get('fecha', '?')} "
                                   f"(clave `{clave}`): no se repite — usa `--force` si de verdad "
                                   f"quieres publicarlo otra vez"]}
        return plan, plan["avisos"], 0

    ops = []
    comentario = None

    if args.event == "arrancar":
        ops.append({"tipo": "etiqueta", "issueKey": issue_principal, "add": [f"ca-{args.actor}"]})
        ops.append(_transicion_op(issue_principal, "en-curso"))

    elif args.event == "implementado":
        detalles = [detalle_tarea(texto, t, ledger_lint) for t in tareas]
        comentario = render_implementado(detalles, args.actor, fecha)
        ops.append({"tipo": "etiqueta", "issueKey": issue_principal, "add": [f"ca-{args.actor}"]})
        ops.append({"tipo": "comentario", "issueKey": issue_principal, "cuerpo": comentario})
        for d in detalles:
            ops.append(_worklog_op(issue_por_tarea[d["id"]], d["id"], "implementacion", None, d))

    elif args.event in ("revision", "gaps"):
        intento = args.intento          # obligatorio para estos dos eventos (validado arriba)
        resumen_hdr, filas = seccion_revision(texto, intento)
        if resumen_hdr is None:
            return None, [f"no hay sección `## Revisión de dos lentes — intento {intento}` en el ledger"], 2
        filas_tarea = [f for f in filas if f["tarea"] in tareas]
        if args.event == "gaps" and not filas_tarea:
            return None, [f"el intento {intento} no tiene gaps para {', '.join(tareas)} — usa `--event revision`"], 2
        if args.event == "revision" and filas_tarea:
            return None, [f"el intento {intento} SÍ tiene gaps para {', '.join(tareas)} — usa `--event gaps`"], 2
        if args.event == "revision":
            comentario = render_revision(args.actor, fecha, intento, tareas, resumen_hdr)
        else:
            comentario = render_gaps(args.actor, fecha, intento, tareas, filas_tarea)
        ops.append({"tipo": "etiqueta", "issueKey": issue_principal, "add": [f"ca-{args.actor}"]})
        if args.event == "gaps":
            # Un intento CON gaps devuelve la tarea a `en-progreso` en el ledger; el issue tiene que
            # contarlo igual o Jira miente (la tabla de la Fase 3 ya prometía «→ En curso (reabre)»
            # y el script no la emitía: quedaba en la columna Done de un tablero mientras el
            # implementer corregía). Mismo GOT-004 que las demás transiciones (T-fix1).
            ops.append(_transicion_op(issue_principal, "reabrir"))
        ops.append({"tipo": "comentario", "issueKey": issue_principal, "cuerpo": comentario})
        if args.ia_real is not None or args.ia_est is not None:
            horas = {"ia_real": args.ia_real, "ia_est": args.ia_est,
                    "sup_real": args.sup_real, "sup_est": args.sup_est,
                    "hum_real": None, "hum_est": None}
            if len(tareas) == 1:
                ops.append(_worklog_op(issue_por_tarea[tareas[0]], tareas[0], "revision", intento, horas))
            else:
                # UNA pasada de revisión cubre varias tareas a la vez (--batch): una única entrada
                # sintética — NUNCA se duplican las mismas horas por tarea (doblaría/triplicaría el
                # tiempo real de esa pasada si el llamador ejecutase los N comandos generados).
                # OJO: nombre propio, no `clave` — esa es la de idempotencia del evento y
                # pisarla anotaría el `flow` bajo «rev-T-01-T-02» (T-fix1).
                clave_worklog = "rev-" + "-".join(tareas)
                ops.append(_worklog_op(issue_principal, clave_worklog, "revision", intento, horas))
                avisos.append(f"horas de revisión agrupadas bajo la clave sintética `{clave_worklog}` "
                              f"(una pasada cubre {len(tareas)} tareas — no se duplican por tarea)")
        else:
            avisos.append("sin --ia-real/--ia-est: no se imputan horas de esta revisión, solo el comentario")

    elif args.event == "aprobado":
        comentario = render_aprobado(args.actor, fecha, tareas,
                                     evidencia_ok["intento"], evidencia_ok["resumen"])
        ops.append({"tipo": "etiqueta", "issueKey": issue_principal, "add": [f"ca-{args.actor}"]})
        ops.append(_transicion_op(issue_principal, "done"))
        ops.append({"tipo": "comentario", "issueKey": issue_principal, "cuerpo": comentario})

    else:  # qa-verde | qa-rojo
        intento = args.intento or 1
        slug = os.path.basename(os.path.dirname(os.path.abspath(args.ledger)))
        evidencia = args.evidencia or f"docs/roadmap/{slug}/testing/"
        comentario = render_qa(args.event, args.actor, fecha, intento, tareas, args.resumen, evidencia)
        ops.append({"tipo": "etiqueta", "issueKey": issue_principal, "add": [f"ca-{args.actor}"]})
        ops.append({"tipo": "comentario", "issueKey": issue_principal, "cuerpo": comentario})

    if ops:   # el plan se anota AL GENERARSE: si no llegas a ejecutarlo, repite con `--force`
        aviso_anotar = _anotar_flujo(state_path, clave, fecha)
        if aviso_anotar:
            avisos.append(aviso_anotar)

    plan = {"evento": args.event, "actor": args.actor, "rol": ROL[args.actor], "fecha": fecha,
           "tareas": tareas, "issueKey": issue_principal, "jira": "activado",
           "yaRealizado": False, "claveIdempotencia": clave, "ops": ops, "avisos": avisos}
    return plan, avisos, 0


def _transicion_op(issue_key, logico):
    """Op de transición con el destino LÓGICO (`en-curso` · `reabrir` · `done`) y la regla GOT-004
    para resolverlo: la categoría se descubre con `getTransitionsForJiraIssue`, nunca por el nombre
    de la transición ni por un id fijo (un "Done" puede apuntar a un estado localizado)."""
    cat = "done" if logico == "done" else "indeterminate"
    extra = ("; sáltala si el issue ya está en curso" if logico == "en-curso" else
             "; el issue vuelve a En curso mientras el implementer corrige" if logico == "reabrir"
             else "")
    return {"tipo": "transicion", "issueKey": issue_key, "objetivo_logico": logico,
           "objetivo_statuscategory": cat,
           "regla": f'GOT-004: descubre la transición por to.statusCategory.key == "{cat}", nunca '
                    f'por nombre ni id fijo{extra}'}


def _worklog_op(issue_key, tid, kind, intento, horas):
    """Op de worklog: el COMANDO de `worklog.py` ya compuesto… solo si hay issueKey.

    Sin issue resuelto NO se emite comando: `worklog.py` acepta `--issue "<issueKey>"` como si fuera
    una clave real y devuelve exit 0, así que un comando con el placeholder parecía listo para
    ejecutar y grababa estado bajo una clave inventada. Ahora la op sale marcada
    `pendiente: "issueKey"` / `requiereIssue: true`, con la instrucción de qué hacer (T-fix1)."""
    if not issue_key:
        return {"tipo": "worklog", "issueKey": None, "pendiente": "issueKey", "requiereIssue": True,
               "task": tid, "kind": kind, "intento": intento,
               "horas": {k: v for k, v in horas.items() if v is not None},
               "instruccion": f"NO ejecutable todavía: {tid} no está mapeada a ningún issue. Vuelca "
                              f"el plan a Jira (jira-sync Paso 5) y repite este evento; entonces la "
                              f"op traerá el comando de `worklog.py` con `--issue <KEY>` ya puesto."}
    wl = os.path.join(HERE, "worklog.py")
    cmd = [sys.executable, wl, "plan", "--task", tid, "--issue", issue_key, "--kind", kind]
    tiene_ia = horas.get("ia_real") is not None or horas.get("ia_est") is not None
    campos = [("--ia-real", horas.get("ia_real")), ("--ia-est", horas.get("ia_est")),
             ("--sup-real", horas.get("sup_real")), ("--sup-est", horas.get("sup_est"))]
    if not tiene_ia:   # worklog.py solo mira humano cuando NO hay IA (tarea puramente humana)
        campos += [("--human-real", horas.get("hum_real")), ("--human-est", horas.get("hum_est"))]
    for flag, val in campos:
        if val is not None:
            cmd += [flag, str(val)]
    if intento is not None:
        cmd += ["--attempt", str(intento)]
    return {"tipo": "worklog", "issueKey": issue_key,
           "comando": cmd,
           "nota": "sin --apply: previsualiza (revisa requiereDecision); repite con --apply al confirmar"}


# ------------------------------------------------------------------ CLI

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", choices=["plan"])
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--event", required=True, choices=EVENTOS)
    ap.add_argument("--actor", required=True, choices=sorted(ROL))
    ap.add_argument("--task", required=True)
    ap.add_argument("--batch", action="store_true")
    ap.add_argument("--intento", type=int)
    ap.add_argument("--issue")
    ap.add_argument("--state")
    ap.add_argument("--root", help="desde dónde resolver `.claude/jira.json` (defecto: cwd, hacia "
                                   "arriba — misma resolución que worklog.py)")
    ap.add_argument("--force", action="store_true",
                    help="repite un evento ya publicado (salta la idempotencia)")
    ap.add_argument("--qa-verde", action="store_true", dest="qa_verde",
                    help="obligatorio en `aprobado`: declara que `qa-gate.py` dio exit 0. El "
                         "orquestador solo lo pasa tras LEER ese exit 0, nunca por impresión")
    ap.add_argument("--resumen")
    ap.add_argument("--evidencia")
    ap.add_argument("--fecha")
    ap.add_argument("--ia-real", type=float, dest="ia_real")
    ap.add_argument("--ia-est", type=float, dest="ia_est")
    ap.add_argument("--sup-real", type=float, dest="sup_real")
    ap.add_argument("--sup-est", type=float, dest="sup_est")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not os.path.isfile(args.ledger):
        print(json.dumps({"error": f"no existe el ledger {args.ledger}", "ops": []}), file=sys.stderr)
        return 2
    # `revision`/`gaps` exigen `--intento` (lo valida construir_plan, con la razón); en los eventos
    # de qa el intento es solo el rótulo del comentario, así que ahí sí cae a 1.
    if args.event in EVENTOS_CON_INTENTO and args.intento is None \
            and args.event not in EVENTOS_INTENTO_OBLIGATORIO:
        args.intento = 1

    plan, avisos, code = construir_plan(args)
    if code != 0:
        if args.json:
            print(json.dumps({"error": avisos, "ops": []}, ensure_ascii=False))
        else:
            for a in avisos:
                print(f"jira-flow: {a}", file=sys.stderr)
        return code

    if args.json:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
    else:
        estado = ("jira desactivado" if plan.get("jira") == "desactivado"
                  else "ya realizado" if plan.get("yaRealizado") else f"{len(plan['ops'])} op(s)")
        print(f"jira-flow: evento «{plan['evento']}» · actor {plan['actor']} ({plan['rol']}) · "
             f"{', '.join(plan['tareas'])} · issue {plan['issueKey'] or '(sin resolver)'} · "
             f"{estado}")
        for op in plan["ops"]:
            print(f"  - {op['tipo']}" + (f" → {op.get('objetivo_logico')} "
                                         f"({op.get('objetivo_statuscategory')})"
                                         if op["tipo"] == "transicion" else "")
                  + (" · PENDIENTE de issueKey" if op.get("requiereIssue") else ""))
        for a in plan["avisos"]:
            print(f"  ⚠️  {a}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
