#!/usr/bin/env python3
"""
progress-report.py — línea de progreso DETERMINISTA del ledger canónico `tasks.md`
(agent-kits/shared: lo invocan los hooks `progress-line.sh` (PostToolUse),
`subagent-progress.sh` (SubagentStop), `session-context.sh` (SessionStart) y el
statusline opt-in `statusline/roadmap-statusline.sh`).

Reutiliza el parser estructural de `ledger-lint.py` (`parse_ledger`), importado como
módulo sin efectos secundarios; no valida, solo resume.

Subcomandos:
  line <tasks.md> [--json]
      UNA línea:
      📋 <slug> · T-04/12 completadas (33%) · fase 2/4 «<nombre>» · en curso: T-05 <título> · IA real 1h12m
      Tramos opcionales: «fase» solo si hay ≥1 fase; «en curso» solo si hay una tarea
      en-progreso; «IA real» solo si alguna tarea tiene horas IA reales MEDIDAS (formato
      XhYm); si todas las reales están marcadas «(estimado)», el tramo se rotula «IA est.».
  active [--root docs/roadmap] [--json]
      Una línea por iniciativa con estado `en-progreso` (frontmatter `estado:` o, si falta,
      tabla `| **Estado** |`). Sin ninguna → `sin iniciativas en progreso`. Ficheros que no
      se pueden parsear se SALTAN con aviso en stderr.
  session [--root .]
      Bloque ≤ 15 líneas para inyectar como contexto de sesión: activas, tareas en curso,
      marcadores huérfanos de `usage-meter.py status` (si está junto a este script) y la
      línea de retoma. Sin nada activo → UNA línea neutra (`LINEA_NEUTRA`).

Exit codes:
  0  OK (active/session: SIEMPRE 0, incluso sin roadmap — la información nunca bloquea)
  1  uso incorrecto / fichero inexistente (solo `line`)
  2  ledger ilegible o sin tareas `### T-XX` (solo `line`; aviso en stderr)
"""
import argparse
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
import time

# Consola Windows (cp1252) o tuberías: reconfigurar ANTES de leer o imprimir nada (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

# Project-local kits must remain read-only even when the caller omits Python -B.
sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
LINEA_NEUTRA = "roadmap: sin iniciativas en progreso"
SIN_ACTIVAS = "sin iniciativas en progreso"


def _load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, filename))
    if spec is None or spec.loader is None:
        raise ImportError(filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_ll = _load_module("ledger_lint", "ledger-lint.py")
parse_ledger = _ll.parse_ledger
norm_estado = _ll.norm_estado
sin_vallas = _ll.sin_vallas


def fmt_horas(horas):
    """Formato puro de horas; resumir un ledger no carga el meter ni su estado."""
    total_min = round(float(horas) * 60)
    h, m = divmod(total_min, 60)
    if h and m:
        return f"{h}h {m}m"
    if h:
        return f"{h}h"
    return f"{m}m"


# ------------------------------------------------------------------ núcleo

def slug_de(path, frontmatter):
    d = os.path.basename(os.path.dirname(os.path.abspath(path)))
    slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", d)
    if not slug or slug in (".", "") or d in (".", ""):
        slug = frontmatter.get("tasks") or "ledger"
    return slug


def nombre_fase(nombre):
    """'Fase 2 — Núcleo' → 'Núcleo'; 'Fase única — visibilidad' → 'visibilidad'; sin separador → tal cual."""
    m = re.match(r"^\s*Fase\b[^—–:-]*[—–:-]\s*(.+)$", nombre)
    return (m.group(1) if m else nombre).strip()


def resumir(path, *, text=None, parsed=None):
    """Resume un ledger; con texto suministrado no accede al sistema de archivos."""
    if text is None:
        try:
            with open(path, encoding="utf-8-sig", errors="replace") as source:
                text = source.read()   # tolera BOM para los consumidores históricos
        except OSError as e:
            raise ValueError(f"no se puede leer: {e}") from e
    if parsed is None:
        parsed = parse_ledger(text)
    tareas = parsed["tareas"]
    if not tareas:
        raise ValueError("sin tareas `### T-XX` reconocibles")

    total = len(tareas)
    completadas = sum(1 for t in tareas if t["estado"] == "completado")
    pct = round(100 * completadas / total) if total else 0

    en_curso = next((t for t in tareas if t["estado"] == "en-progreso"), None)

    fases = parsed["fases"]
    fase = None
    if fases:
        idx = None
        if en_curso is not None:
            idx = next((i for i, f in enumerate(fases) if en_curso in f["tareas"]), None)
        if idx is None:
            idx = next((i for i, f in enumerate(fases)
                        if any(t["estado"] != "completado" for t in f["tareas"])), len(fases) - 1)
        fase = {"indice": idx + 1, "total": len(fases), "nombre": nombre_fase(fases[idx]["nombre"])}

    # Horas IA: solo cuentan como «real» las NO marcadas «(estimado)»; si todas las que hay
    # son estimadas, se suman igual pero se rotulan «IA est.» (no se vende estimado como medido).
    medidas = [t["ia_real_h"] for t in tareas if t["ia_real_h"] is not None
               and t["ia_real_fuente"] != "estimado"]
    estimadas = [t["ia_real_h"] for t in tareas if t["ia_real_h"] is not None
                 and t["ia_real_fuente"] == "estimado"]
    if medidas:
        ia_real_h, ia_fuente = round(sum(medidas), 4), "medido"
    elif estimadas:
        ia_real_h, ia_fuente = round(sum(estimadas), 4), "estimado"
    else:
        ia_real_h, ia_fuente = None, None

    estado = norm_estado(parsed["frontmatter"]["estado"]) if parsed["frontmatter"].get("estado") \
        else parsed["estado_tabla"]

    return {
        "slug": slug_de(path, parsed["frontmatter"]),
        "path": path,
        "estado": estado,
        "completadas": completadas,
        "total": total,
        "pct": pct,
        "fase": fase,
        "en_curso": {"id": en_curso["id"], "titulo": en_curso["titulo"]} if en_curso else None,
        "en_progreso": [{"id": t["id"], "titulo": t["titulo"]}
                        for t in tareas if t["estado"] == "en-progreso"],
        "ia_real_h": ia_real_h,
        "ia_fuente": ia_fuente,
        "ia_real_fmt": fmt_horas(ia_real_h) if ia_real_h is not None else None,
    }


def linea(r):
    partes = [f"📋 {r['slug']}",
              f"T-{r['completadas']:02d}/{r['total']} completadas ({r['pct']}%)"]
    if r["fase"]:
        partes.append(f"fase {r['fase']['indice']}/{r['fase']['total']} «{r['fase']['nombre']}»")
    if r["en_curso"]:
        t = r["en_curso"]
        partes.append(f"en curso: {t['id']} {t['titulo']}".rstrip())
    if r["ia_real_fmt"]:
        rotulo = "IA real" if r.get("ia_fuente") == "medido" else "IA est."
        partes.append(f"{rotulo} {r['ia_real_fmt']}")
    return " · ".join(partes)


def activas(root):
    """[(resumen)] de las iniciativas en-progreso bajo root/*/tasks.md; avisa por stderr y sigue."""
    out = []
    if not os.path.isdir(root):
        return out
    for d in sorted(os.listdir(root)):
        p = os.path.join(root, d, "tasks.md")
        if not os.path.isfile(p):
            continue
        try:
            r = resumir(p)
        except ValueError as e:
            print(f"⚠️  progress-report: {p}: {e} (saltado)", file=sys.stderr)
            continue
        if r["estado"] == "en-progreso":
            out.append(r)
    return out


def _slug_de_clave(clave):
    """Slug de la iniciativa de una clave del usage-meter: `<slug>/<artefacto>` o
    `docs/roadmap/<fecha>-<slug>/<artefacto>`. None si no se reconoce."""
    partes = [x for x in str(clave).replace("\\", "/").split("/") if x]
    if partes[:2] == ["docs", "roadmap"]:
        partes = partes[2:]
    if len(partes) < 2:   # sin artefacto no es una clave del meter
        return None
    return re.sub(r"^\d{4}-\d{2}-\d{2}-", "", partes[0]) or None


def iniciativa_en_curso(rs, estado, mtime=os.path.getmtime):
    """Slug de la iniciativa en la que se trabaja entre las activas `rs` (función pura salvo `mtime`).

    1) marcador ABIERTO (sin `ultimoCierre`) del usage-meter cuya clave apunta a una activa con
       ledger (uno de spec/evaluación sin ledger no cuenta); si hay varios, el de inicio más reciente;
    2) si no hay, la activa cuyo `tasks.md` se modificó más recientemente. None si `rs` está vacía."""
    if not rs:
        return None
    por_slug = {r["slug"]: r for r in rs}
    abiertos = []
    if isinstance(estado, dict):
        for clave, m in estado.items():
            if not isinstance(m, dict) or "ultimoCierre" in m:
                continue
            slug = _slug_de_clave(clave)
            if slug in por_slug:
                abiertos.append((str(m.get("inicio") or ""), slug))
    if abiertos:
        return max(abiertos)[1]

    def _t(r):
        try:
            return mtime(r["path"])
        except OSError:
            return 0
    return max(rs, key=_t)["slug"]


_USAGE_STATE_MEMO = {}


def _leer_usage_state(root):
    """`<proyecto>/.claude/usage-state.json` (root = <proyecto>/docs/roadmap), lectura directa:
    sin lanzar usage-meter. Ausente o corrupto -> {}. Memo por proceso mientras no cambie su
    firma (mtime, tamaño): el arranque lo consulta varias veces y no lo relee (D1)."""
    proyecto = os.path.dirname(os.path.dirname(os.path.abspath(root)))
    ruta = os.path.join(proyecto, ".claude", "usage-state.json")
    try:
        info = os.stat(ruta)
        firma = (info.st_mtime_ns, info.st_size)
    except OSError:
        return {}
    memo = _USAGE_STATE_MEMO.get(ruta)
    if memo is not None and memo[0] == firma:
        return memo[1]
    try:
        with open(ruta, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}
    data = data if isinstance(data, dict) else {}
    _USAGE_STATE_MEMO.clear()
    _USAGE_STATE_MEMO[ruta] = (firma, data)
    return data


_CABECERA_BYTES = 16 * 1024


def _celdas(linea):
    """Celdas de una fila de tabla Markdown, sin regex con cuantificadores que compitan (C1)."""
    s = linea.strip()
    if not s.startswith("|"):
        return None
    return [c.strip() for c in s.strip("|").split("|")]


def resumir_cabecera(path, text):
    """Progreso de un ledger desde su frontmatter y su tabla «Resumen de progreso» (prefijo acotado).

    Para ledgers que no se leen enteros (> tope): `completadas`/`total` del TOTAL o de la suma de
    fases, la fase pendiente y `en_progreso` vacío (no se conoce desde la cabecera). Las líneas de
    dentro de un bloque de código no cuentan. `None` si el prefijo no trae una tabla usable."""
    lineas = sin_vallas(text.lstrip("\ufeff")).splitlines()
    frontmatter = {}
    if lineas and lineas[0].strip() == "---":
        for ln in lineas[1:]:
            if ln.strip() == "---":
                break
            m = re.match(r"^([A-Za-z_][\w-]*)[ \t]*:(.*)$", ln)
            if m:
                frontmatter[m.group(1)] = m.group(2).split("#", 1)[0].strip()
    inicio = next((i for i, ln in enumerate(lineas) if re.match(r"^##[ \t]+Resumen de progreso", ln)), None)
    if inicio is None:
        return None
    fases, total_fila = [], None
    for ln in lineas[inicio + 1:]:
        if ln.startswith("## "):
            break
        celdas = _celdas(ln)
        if not celdas or len(celdas) < 3:
            continue
        nombre = celdas[0].strip("*").strip()
        hechas, total = celdas[1].strip("*").strip(), celdas[2].strip("*").strip()
        if not (hechas.isdigit() and total.isdigit()):
            continue
        fila = (nombre, int(hechas), int(total))
        if nombre.upper() == "TOTAL":
            total_fila = fila
        elif nombre.lower().startswith("fase"):
            fases.append(fila)
    if not fases and total_fila is None:
        return None
    hechas = total_fila[1] if total_fila else sum(f[1] for f in fases)
    total = total_fila[2] if total_fila else sum(f[2] for f in fases)
    if total <= 0 or hechas > total:
        return None
    fase = None
    if fases:
        i = next((n for n, f in enumerate(fases) if f[1] < f[2]), len(fases) - 1)
        fase = {"indice": i + 1, "total": len(fases), "nombre": nombre_fase(fases[i][0])}
    estado = norm_estado(frontmatter["estado"]) if frontmatter.get("estado") else None
    return {"slug": slug_de(path, frontmatter), "path": path, "estado": estado,
            "completadas": hechas, "total": total, "pct": round(100 * hechas / total), "fase": fase,
            "en_curso": None, "en_progreso": [], "ia_real_h": None, "ia_fuente": None, "ia_real_fmt": None}


_LEDGER_MAX = 256 * 1024
_ACTIVA_MAX = 16 * 1024 * 1024   # fix3 (B3): las ACTIVAS (pocas) se leen enteras hasta este tope, como la consola
_SNAPSHOT_MEMO = {}


def _estado_de(text):
    """Estado del ledger en un prefijo: frontmatter o, si no lo trae, la fila `| **Estado** |` de la
    tabla de cabecera (plantilla del planner, fix2 B-I1). None si el prefijo no lo trae."""
    parsed = parse_ledger(text)
    fm = parsed["frontmatter"].get("estado")
    return norm_estado(fm) if fm else parsed["estado_tabla"]


def _resumen_acotado(reader, root, relative, absoluta, avisos=None):
    """Resumen de UN ledger con el lector acotado: 16 KiB para saber si está activo y, solo si lo
    está (o el estado no cabe en ese prefijo), hasta 256 KiB para el resumen exacto (tareas en curso
    incluidas). Por encima de 256 KiB, la cabecera. None si no se puede leer o no se sabe su estado."""
    carpeta = os.path.basename(os.path.dirname(absoluta))

    def ilegible(status):
        # fix3 (B5): un ledger que el lector rechaza no desaparece en silencio
        if status not in ("not_found", "not_regular") and avisos is not None:
            avisos.append(f"{carpeta}: tasks.md ilegible ({status})")
        return None
    read = reader.read_text(root, relative, max_bytes=_CABECERA_BYTES, prefix=True)
    if read["status"] != "ok":
        return ilegible(read["status"])
    try:
        if not read.get("truncated"):
            return resumir(absoluta, text=read["text"])
        estado = _estado_de(read["text"])
        if estado not in (None, "en-progreso"):
            return {"slug": slug_de(absoluta, {}), "path": absoluta, "estado": estado}
        read = reader.read_text(root, relative, max_bytes=_LEDGER_MAX, prefix=True)
        if read["status"] != "ok":
            return ilegible(read["status"])
        if not read.get("truncated"):
            return resumir(absoluta, text=read["text"])
        estado = _estado_de(read["text"])
        if estado is None:
            return None
        if estado == "en-progreso":
            entero = reader.read_text(root, relative, max_bytes=_ACTIVA_MAX)
            if entero["status"] == "ok":
                return resumir(absoluta, text=entero["text"])
            if entero["status"] != "too_large":
                return ilegible(entero["status"])
        r = resumir_cabecera(absoluta, read["text"]) or {
            "slug": slug_de(absoluta, {}), "path": absoluta, "completadas": 0, "total": None, "pct": 0,
            "fase": None, "en_curso": None, "en_progreso": [], "ia_real_h": None, "ia_fuente": None,
            "ia_real_fmt": None}
        r["estado"] = estado
        return r
    except ValueError as e:
        print(f"⚠️  progress-report: {absoluta}: {e} (saltado)", file=sys.stderr)   # como `activas()`
        return None
    except (TypeError, KeyError, OverflowError, RecursionError):
        return None


def instantanea(root):
    """INSTANTÁNEA única del roadmap (fix2 B-M3 + fix3): `{"activas": [...], "avisos": [...]}`. La
    usan el escritor del journal, el historial del arranque, el bloque `session`, `active --json`
    (memoria, statusline, `/doctor`).

    Lector acotado: la raíz del proyecto es el ancla (resuelta una vez); por debajo no se siguen
    enlaces, y una carpeta enlazada no se mira por dentro ni para la firma (fix3, C1). 16 KiB por
    ledger para saber su estado (frontmatter o tabla de cabecera), hasta 256 KiB si no aparece y, para
    las activas, hasta 16 MiB. Mira las 128 carpetas más recientes por nombre; las más antiguas se
    avisan («Roadmap recortado: …», fix3 B4) y los ledgers ilegibles también (fix3 B5). Memo por
    proceso mientras no cambie la firma (mtime, tamaño) de ningún ledger."""
    reader = _load_module("vigente_local_read", "local-read.py")
    listing = reader.list_names(root, "docs/roadmap", max_entries=4096, newest_first=True)
    if listing["status"] not in ("ok", "incomplete"):
        return {"activas": [], "avisos": []}
    validas = [f for f in listing["names"] if _initiative_name(f)]
    avisos = []
    if len(validas) > _RESUME_SCAN or not listing["complete"]:
        resto = len(validas) - _RESUME_SCAN
        avisos.append(f"Roadmap recortado: {max(resto, 0)}{'' if listing['complete'] else ' o más'} "
                      "carpetas más antiguas sin revisar")
    carpetas = sorted(validas[:_RESUME_SCAN])
    base = os.path.join(str(root), "docs", "roadmap")
    firma = []
    for folder in carpetas:
        try:
            dir_info = os.lstat(os.path.join(base, folder))
            if reader._redirected(dir_info) or not stat.S_ISDIR(dir_info.st_mode):
                firma.append((folder, "redirected", None))
                continue
            info = os.lstat(os.path.join(base, folder, "tasks.md"))
            firma.append((folder, info.st_mtime_ns, info.st_size))
        except OSError:
            firma.append((folder, None, None))
    clave = (os.path.abspath(str(root)), tuple(firma))
    memo = _SNAPSHOT_MEMO.get(clave[0])
    if memo is not None and memo[0] == clave[1]:
        return {"activas": [dict(r) for r in memo[1]], "avisos": list(memo[2])}
    out = []
    for folder, mtime_ns, _size in firma:
        if mtime_ns == "redirected":
            avisos.append(f"{folder}: tasks.md ilegible (redirected_path)")
            continue
        if mtime_ns is None:
            continue
        absoluta = os.path.join(base, folder, "tasks.md")
        r = _resumen_acotado(reader, root, "docs/roadmap/" + folder + "/tasks.md", absoluta, avisos)
        if r and r.get("estado") == "en-progreso":
            out.append(r)
    _SNAPSHOT_MEMO.clear()
    _SNAPSHOT_MEMO[clave[0]] = (clave[1], out, avisos)
    return {"activas": [dict(r) for r in out], "avisos": list(avisos)}


def activas_acotadas(root):
    """Iniciativas `en-progreso` de la instantánea única (`instantanea`), en orden de carpeta."""
    return instantanea(root)["activas"]


def _lstat_mtime(path):
    return os.lstat(path).st_mtime


def vigente_entre(rs, estado, mtime=os.path.getmtime):
    """Regla ÚNICA de «la iniciativa en curso» (escritor y lector del journal, bloque de sesión,
    memoria y statusline), fix2 B-I2: (a) la del marcador abierto del usage-meter más reciente, aunque
    esté al 100 % (su retro o su QA); (b) si no hay, la pendiente con el ledger más reciente; (c) si
    todas están al 100 %, la más reciente. Empates por nombre (determinista)."""
    if not rs:
        return None
    por_slug = {r["slug"]: r for r in rs}
    abiertos = []
    if isinstance(estado, dict):
        for clave, m in estado.items():
            if isinstance(m, dict) and "ultimoCierre" not in m:
                slug = _slug_de_clave(clave)
                if slug in por_slug:
                    abiertos.append((str(m.get("inicio") or ""), slug))
    if abiertos:
        return max(abiertos)[1]

    def _t(r):
        try:
            return mtime(r["path"])
        except OSError:
            return 0
    pendientes = [r for r in rs if r.get("total") is None or r["completadas"] < r["total"]] or rs
    return max(pendientes, key=lambda r: (_t(r), r["slug"]))["slug"]


def _proyecto_de(roadmap):
    absoluto = os.path.abspath(str(roadmap))
    if os.path.basename(absoluto) == "roadmap" and os.path.basename(os.path.dirname(absoluto)) == "docs":
        return os.path.dirname(os.path.dirname(absoluto))
    return None


def iniciativa_vigente(root):
    """Slug de la iniciativa en curso del proyecto `root` (B1: misma función para el escritor del
    journal y para el historial del arranque). None sin activas."""
    roadmap = os.path.join(str(root), "docs", "roadmap")
    return vigente_entre(activas_acotadas(root), _leer_usage_state(roadmap), mtime=_lstat_mtime)


def marcadores_huerfanos(root=".", *, in_process=False):
    """Marcadores abiertos (sin cierre) de usage-meter.py status sobre el estado del PROYECTO
    (`<root>/.claude/usage-state.json`, no el cwd); None si el meter no está o falla."""
    meter = os.path.join(HERE, "usage-meter.py")
    if not os.path.isfile(meter):
        return None
    try:
        state = os.path.join(root, ".claude", "usage-state.json")
        if in_process:
            meter_module = _load_module('progress_usage_meter', 'usage-meter.py')
            data = meter_module.status(state)
        else:
            res = subprocess.run([sys.executable, meter, "status", "--state", state],
                                 capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10, check=False)
            data = json.loads(res.stdout or "{}")
        return [m.get("artefacto", "?") for m in data.get("marcadores", []) if not m.get("cerrado")]
    except Exception:  # noqa: BLE001 — cualquier fallo del meter = no disponible
        return None


# ------------------------------------------------------------------ retoma dirigida, solo lectura

_RESUME_SCAN = 128
_RESUME_BYTES = 1024 * 1024
_HISTORY_FIELDS = ("entry", "fecha", "session_id", "runtime", "iniciativa", "resumen",
                   "fuente", "cierre", "resumen_por", "decisiones", "pendientes",
                   "ficheros_tocados", "tareas_cambiadas", "marcadores_cerrados",
                   "materializado_en", "derivados_en", "continuidad", "output_truncated", "identity_resolvable")
# Continuidad del journal (D-085): clave AUSENTE = omitida; ""/[] = vaciado explícito en esa sesión.
_CONTINUITY_FIELDS = (("objetivo", "Objetivo", str), ("punto_actual", "Dónde quedó", str),
                      ("siguientes_pasos", "Siguientes", list), ("bloqueos", "Bloqueos", list),
                      ("descartados", "Descartados", list))   # «enfoque — motivo»: no repetir lo que ya falló


def _history_continuity(value):
    """Solo las claves conocidas con su tipo; sin ninguna, la entrada no añade nada."""
    if not isinstance(value, dict):
        return {}
    return {key: value[key] for key, _, kind in _CONTINUITY_FIELDS
            if isinstance(value.get(key), kind)
            and (kind is str or all(isinstance(item, str) for item in value[key]))}


def _initiative_name(value):
    return (isinstance(value, str) and bool(value) and value not in (".", "..")
            and not any(c in value for c in "/\\:\x00"))


def _resume_result(status, *, ledger=None, history=None, candidates=None, issues=None, curation=None, reviews=None):
    return {"status": status, "ledger": ledger, "history": history or [],
            "candidates": candidates or [], "issues": issues or [], "output_truncated": False,
            "curation": curation if curation is not None else {'status': 'unselected', 'references': []},
            "reviews": reviews if reviews is not None else {'status': 'unselected', 'reviews': [], 'reviews_omitted': 0}}


def _public_resume(result, journal):
    """Proyección pública con vocabulario fijo y presupuesto independiente de la entrada."""
    truncated = False
    def clean(value, limit=160):
        nonlocal truncated
        if isinstance(value, str):
            projected = journal.public_text(value, limit=limit)
            truncated |= projected != value
            return projected
        if isinstance(value, list):
            if len(value) > 4:
                truncated = True
            return [clean(item, limit) for item in value[:4]]
        if isinstance(value, dict):
            return {key: clean(item, limit) for key, item in value.items()}
        return value
    ledger = result.get("ledger")
    if ledger:
        ledger = dict(ledger)
        truncated |= len(ledger["en_progreso"]) > 4
        ledger["en_progreso"] = ledger["en_progreso"][:4]
        result["ledger"] = clean(ledger)
    entries = result["history"]
    truncated |= len(entries) > 2 or any(entry.get("output_truncated") for entry in entries)
    result["history"] = []
    for entry in entries[:2]:
        visible = {k: entry[k] for k in _HISTORY_FIELDS if k in entry and k != "continuidad"}
        continuity = _history_continuity(entry.get("continuidad"))
        if continuity:
            visible["continuidad"] = continuity
        projected = clean(visible, 120)
        projected['output_truncated'] = bool(entry.get('output_truncated') or projected != visible)
        projected['identity_resolvable'] = bool(entry.get('identity_resolvable') and
            all(projected.get(k) == entry.get(k) for k in ('entry', 'session_id', 'iniciativa')))
        truncated |= projected['output_truncated']
        result['history'].append(projected)
    for field in ("candidates", "issues"):
        values = result[field]
        truncated |= len(values) > 16
        result[field] = [clean(value, 100) for value in values[:16]]
    curation = result.get('curation', {'status': 'unselected', 'references': []})
    projected_refs = []
    identity_keys = ('candidate', 'expected_sha256', 'operation_id', 'operation_path',
                     'receipt_path', 'receipt_sha256', 'target', 'target_sha256')
    for reference in curation['references'][:8]:
        projected = clean(reference, 256)
        identity_ok = all(projected.get(key) == reference.get(key) for key in identity_keys)
        projected['identity_resolvable'] = identity_ok
        if not identity_ok:
            for key in identity_keys:
                projected.pop(key, None)
            projected['reason'] = 'identity_projection_changed'
        projected_refs.append(projected)
    result['curation'] = dict(curation, references=projected_refs)
    omitted = len(curation['references']) - len(projected_refs)
    if omitted:
        result['curation']['references_omitted'] = omitted
        truncated = True
    result["output_truncated"] = truncated
    # Escaped strings and multibyte text consume more JSON bytes than characters.
    # If the projection still exceeds its budget, retain the current ledger and
    # report that historical detail and candidate labels were omitted.
    if len(json.dumps(result, ensure_ascii=False).encode("utf-8")) > 12000:
        result["history"] = []
        result["candidates"] = result["candidates"][:4]
        result["issues"] = [{"status": "output_budget"}]
        result["output_truncated"] = True
    # A whole prefix retains each visible reference's exact executable identity.
    # Recheck the final serialization, including the omission counter itself.
    while len(json.dumps(result, ensure_ascii=False).encode("utf-8")) > 12000 and projected_refs:
        projected_refs.pop()
        omitted += 1
        result['curation']['references_omitted'] = omitted
        result['output_truncated'] = True
    review_rows = result['reviews']['reviews']
    result['output_truncated'] |= bool(result['reviews']['reviews_omitted'])
    while len(json.dumps(result, ensure_ascii=False).encode("utf-8")) > 12000 and review_rows:
        review_rows.pop()
        result['reviews']['reviews_omitted'] += 1
        result['output_truncated'] = True
    _, text_truncated = _resume_text_lines(result)
    result['output_truncated'] |= text_truncated
    return result


def _resume_curation(root, text):
    """Read only explicit ledger associations; operation validation belongs to its owner."""
    blocks, capture, fence, comment = [], None, None, False
    for line in text.splitlines():
        if comment:
            comment = '-->' not in line
            continue
        if fence is None and '<!--' in line:
            comment = '-->' not in line.split('<!--', 1)[1]
            continue
        match = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
        if fence is not None:
            close = re.fullmatch(r' {0,3}(`{3,}|~{3,})[ \t]*', line)
            if close and close.group(1)[0] == fence[0] and len(close.group(1)) >= len(fence):
                if capture is not None:
                    if line != '```':
                        return {'status': 'corrupt', 'references': []}
                    blocks.append('\n'.join(capture))
                fence, capture = None, None
            elif capture is not None:
                capture.append(line)
            continue
        if match:
            fence = match.group(1)
            if line == '```curation-refs-v1':
                capture = []
    if capture is not None or len(blocks) > 1:
        return {'status': 'corrupt', 'references': []}
    if not blocks:
        return {'status': 'not_registered', 'references': []}
    if len(blocks[0].encode('utf-8')) > 8192:
        return {'status': 'corrupt', 'references': []}
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate key')
            result[key] = value
        return result
    try:
        refs = json.loads(blocks[0], object_pairs_hook=pairs)
        if not isinstance(refs, list) or len(refs) > 8:
            raise ValueError('invalid references')
        seen = set()
        for ref in refs:
            if (not isinstance(ref, dict) or not {'candidate', 'sha256'} <= set(ref)
                    or not set(ref) <= {'candidate', 'sha256', 'operation_id'}
                    or not isinstance(ref['candidate'], str) or len(ref['candidate']) > 256
                    or ref['candidate'] in seen
                    or not isinstance(ref['sha256'], str) or not re.fullmatch(r'[a-f0-9]{64}', ref['sha256'])
                    or ('operation_id' in ref and (not isinstance(ref['operation_id'], str)
                        or not re.fullmatch(r'[a-f0-9]{64}', ref['operation_id'])))):
                raise ValueError('invalid reference')
            seen.add(ref['candidate'])
    except (ValueError, TypeError, KeyError, RecursionError):
        return {'status': 'corrupt', 'references': []}
    try:
        service = _load_module('resume_curation', 'knowledge-curation.py')
    except (ImportError, OSError, SyntaxError):
        return {'status': 'unknown', 'reason': 'service_unavailable', 'references': []}
    try:
        for ref in refs:
            service._candidate(ref['candidate'])
    except (service._Failure, ValueError, TypeError, AttributeError):
        return {'status': 'corrupt', 'references': []}
    budget = {'remaining': 1024 * 1024}
    results = [service.inspect_reference(root, ref['candidate'], ref['sha256'],
        operation_id=ref.get('operation_id'), _budget=budget) for ref in refs]
    return {'status': 'ok', 'references': results}


def _resume_ledger(root, initiative, reader):
    """Resuelve carpeta exacta o slug único sin elegir dentro de un scan incompleto."""
    def read(folder, *, max_bytes=256 * 1024):
        relative = "docs/roadmap/" + folder + "/tasks.md"
        result = reader.read_text(root, relative, max_bytes=max_bytes)
        if result["status"] != "ok":
            return result["status"], None, result.get("bytes", 0)
        try:
            summary = resumir(relative, text=result["text"])
        except (ValueError, TypeError, KeyError, OverflowError):
            return "malformed", None, result["bytes"]
        summary['_curation_text'] = result['text']
        return "ok", summary, result["bytes"]

    # An exact dated folder is independent of unrelated ledger failures.
    if initiative is not None and re.match(r"^\d{4}-\d{2}-\d{2}-.+", initiative):
        status, summary, _ = read(initiative)
        return status, summary, [], [] if status == "ok" else [{"entry": initiative, "status": status}]
    listing = reader.list_names(root, "docs/roadmap", max_entries=_RESUME_SCAN)
    if listing["status"] != "ok" or not listing["complete"]:
        status = "incomplete" if listing["status"] == "incomplete" else listing["status"]
        return status, None, [], [{"status": status, "scope": "roadmap"}]
    matches, issues = [], []
    remaining = _RESUME_BYTES
    for folder in listing["names"]:
        if not _initiative_name(folder):
            issues.append({"entry": folder, "status": "invalid_path"})
            continue
        if remaining <= 0:
            issues.append({"status": "scan_budget"})
            break
        status, summary, size = read(folder, max_bytes=min(256 * 1024, remaining))
        remaining -= size
        if status in ("not_found", "not_regular"):
            continue  # This roadmap entry has no ledger.
        if status != "ok":
            issues.append({"entry": folder, "status": status})
            continue
        matches_selection = (summary["slug"] == initiative if initiative is not None
                             else summary["estado"] == "en-progreso")
        if matches_selection:
            matches.append((folder, summary))
    candidates = [folder for folder, _ in matches]
    if issues:
        return "incomplete", None, candidates, issues
    if len(matches) > 1:
        return "ambiguous", None, candidates, []
    if not matches:
        return "not_found", None, [], [{"scope": "roadmap", "status": "no_matching_ledger"}]
    return "ok", matches[0][1], [], []


def _history_initiative(root):
    """Slug de la iniciativa en curso entre las activas, para el historial del arranque (H-14).

    Lee los ledgers como `session` (el mismo arranque ya los lee) y desempata con
    `iniciativa_en_curso`: marcador abierto del meter o el ledger más reciente.
    Sin activas → None: nunca se cita el historial de una iniciativa no activa."""
    return iniciativa_vigente(root)


def _resume_reviews(root, ledger_path, *, deadline=None):
    """Only the exact ledger-selected initiative; no global or historical fallback."""
    try:
        owner = _load_module('resume_plan_review', 'plan-review.py')
        return owner.list_reminders(root, ledger_path.rsplit('/', 1)[0],
                                    state_root=os.path.join(root, '.claude', 'plan-review'), deadline=deadline)
    except (ImportError, OSError, SyntaxError, AttributeError):
        return {'status': 'unavailable', 'reason': 'helper_unavailable', 'complete': False,
                'reviews': [], 'reviews_omitted': 0, 'approval_granted': False}


def _review_text_lines(result):
    if result['status'] in ('unselected', 'not_registered'):
        return []
    lines = ['Revisiones observadas (no acredita aprobación): ' + result['status']]
    if result.get('reason'):
        lines.append('Revisiones: ' + result['reason'])
    for row in result['reviews']:
        lines.append('Revisión ' + row['review_id'] + ' · ' + row['gate_key'] + ' · ' + row['state']
                     + ' · ' + row['version_status'] + ' · decisión registrada: '
                     + ('sí' if row['decision_recorded'] else 'no')
                     + f" · comentarios/respuestas: {row['comments_recorded']}/{row['comments_with_result']}")
    if result['reviews_omitted']:
        lines.append(f"Revisiones: {result['reviews_omitted']} referencias omitidas por presupuesto de presentación.")
    return lines


def resume(root, *, initiative=None, session_id=None, runtime=None, entry=None, _history_only=False):
    """Compose current ledger and quoted history without usage state or subprocesses.

    Explicit selections never fall back to a different initiative or journal entry.
    Historical claims remain evidence from their recorded session, not current QA.
    """
    try:
        journal = _load_module("resume_journal", "journal.py")
        reader = _load_module("resume_local_read", "local-read.py")
    except (ImportError, OSError, SyntaxError):
        return _resume_result('reader_unavailable', issues=[{'status': 'incomplete_bundle'}])
    def finish(status, **kwargs):
        return _public_resume(_resume_result(status, **kwargs), journal)
    if initiative is not None and (not _initiative_name(initiative)
                                  or journal.public_text(initiative, limit=4096) != initiative):
        return finish("invalid_selection", issues=[{"status": "invalid_initiative"}])
    selected_history = None
    if initiative is None and (session_id is not None or entry is not None):
        selected_history = journal.select_entries(root, initiative=initiative, session_id=session_id,
                                                  runtime=runtime, entry=entry)
        if selected_history["status"] != "ok" or not selected_history["complete"]:
            return finish(selected_history["status"], candidates=selected_history["candidates"],
                          issues=selected_history["issues"])
        if initiative is None:
            if any(e.get("identity_resolvable") is False
                   or ("identity_resolvable" not in e and e.get("output_truncated"))
                   for e in selected_history["entries"]):
                return finish("initiative_unknown", history=selected_history["entries"],
                              issues=[{"status": "historical_identity_truncated"}])
            names = {e.get("iniciativa") for e in selected_history["entries"] if e.get("iniciativa")}
            if len(names) != 1:
                return finish("initiative_unknown" if not names else "ambiguous",
                              history=selected_history["entries"], candidates=sorted(names),
                              issues=[{"status": "history_does_not_identify_one_initiative"}])
            initiative = next(iter(names))
            if not _initiative_name(initiative):
                return finish("invalid_selection", issues=[{"status": "invalid_historical_initiative"}])
    status, summary, candidates, issues = _resume_ledger(root, initiative, reader)
    if summary is None and _history_only and initiative is None and session_id is None and entry is None:
        # H-14: the startup history must not depend on the bounded global ledger
        # selection (1 MiB budget, single active initiative). Take the initiative
        # in progress among the active ones and quote only its own entries.
        slug = _history_initiative(root)
        if slug is None:
            return finish(status, candidates=candidates, issues=issues)
        selected_history = journal.select_entries(root, initiative=slug, runtime=runtime, require_rule=True)
        return finish(selected_history["status"] if selected_history["complete"] else "incomplete",
                      history=selected_history["entries"], issues=selected_history["issues"])
    if summary is None:
        return finish(status, candidates=candidates, issues=issues,
                      history=selected_history["entries"] if selected_history else None)
    ledger_text = summary.pop('_curation_text')
    curation = ({'status': 'unselected', 'references': []} if _history_only
                else _resume_curation(root, ledger_text))
    reviews = None if _history_only else _resume_reviews(root, summary['path'])
    # fix2 B-M4: el arranque (`--history-only`) solo atribuye entradas etiquetadas con la regla vigente
    selected_history = selected_history or journal.select_entries(root, initiative=summary["slug"],
                                                                  session_id=session_id, runtime=runtime, entry=entry,
                                                                  **({"require_rule": True} if _history_only else {}))
    history_status = selected_history["status"]
    issues.extend(selected_history["issues"])
    history_absent = history_status in ("empty", "not_found")
    if history_absent:
        issues.append({"scope": "history", "status": history_status})
        if session_id is None and entry is None:
            # A ledger remains useful without history. An explicitly requested
            # session or file that is missing retains its failure status.
            history_status = "ok"
    if not selected_history["complete"] and history_status == "ok" and not history_absent:
        history_status = "incomplete"
    return finish(history_status, ledger=summary, history=selected_history["entries"],
                   candidates=selected_history["candidates"], issues=issues, curation=curation, reviews=reviews)


def _resume_text_lines(result):
    """Bound whole lines/groups, reserving space for truthful omission notices."""
    out = ["Retoma dirigida · estado: " + result["status"]]
    truncated = bool(result['output_truncated'])
    def append(lines):
        nonlocal truncated
        if len(out) + len(lines) > 30 or len('\n'.join(out + lines)) > 5800:
            truncated = True
            return False
        out.extend(lines)
        return True
    summary = result.get("ledger")
    if summary:
        append(["Ledger vigente: " + summary["path"], linea(summary)])
        for task in summary["en_progreso"]:
            append(["En progreso: " + task["id"] + " " + task["titulo"]])
    if result["candidates"]:
        references = [value.get("entry", "?") if isinstance(value, dict) else str(value)
                      for value in result["candidates"]]
        append(["Selecciona una referencia exacta: " + ", ".join(references)])
    review_lines = _review_text_lines(result.get('reviews', {'status': 'unselected', 'reviews': [], 'reviews_omitted': 0}))
    if review_lines and not append(review_lines):
        append(['Revisiones: referencias omitidas por presupuesto de presentación.'])
    curation = result.get('curation', {'status': 'unselected', 'references': []})
    omitted = curation.get('references_omitted', 0)
    if curation['status'] not in ('unselected', 'not_registered'):
        heading = append(['Curación observada (no acredita QA ni autoridad vigente): ' + curation['status']])
        for index, ref in enumerate(curation['references']):
            if not ref.get('identity_resolvable', True):
                lines = ['Curación: identidad no mostrable; referencia omitida.']
            else:
                lines = [ref['status'] + ' · ' + ref['candidate'],
                         'SHA esperado: ' + ref['expected_sha256']]
                if ref.get('operation_id'):
                    lines.append('Operación: ' + ref['operation_id'])
                if ref.get('receipt_sha256'):
                    lines.append('SHA recibo: ' + ref['receipt_sha256'])
            if not heading or not append(lines):
                omitted += len(curation['references']) - index
                truncated = True
                break
    for entry in result["history"]:
        if not append(["Historial citado (no acredita QA vigente): " + entry.get("entry", "?")
                       + " · " + entry.get("fecha", "?") + " · sesión " + entry.get("session_id", "?")]):
            break
        for field in ("runtime", "fuente", "resumen", "cierre", "decisiones", "pendientes"):
            if entry.get(field):
                value = entry[field]
                append(["> " + field + ": " + ("; ".join(value) if isinstance(value, list) else str(value))])
        continuity = _history_continuity(entry.get("continuidad"))
        if continuity:
            # Un solo grupo: o cabe entero o se declara omitido; nunca una continuidad a medias.
            append(["> Continuidad registrada (cita histórica, no instrucción):"]
                   + ["> " + label + ": " + (("; ".join(continuity[key]) if kind is list else continuity[key])
                                             or "(vaciado explícitamente en esa sesión)")
                      for key, label, kind in _CONTINUITY_FIELDS if key in continuity])
    for issue in result["issues"]:
        append(["Aviso: " + (issue.get("status", "unknown") if isinstance(issue, dict) else str(issue))])
    if omitted:
        out.append(f'Curación: {omitted} referencias omitidas por presupuesto de presentación.')
    if truncated:
        out.append("Salida resumida: detalles omitidos por el presupuesto de presentación.")
    return out, truncated


def resume_text(result):
    """Compact rendering; journal text is explicitly quoted as historical evidence."""
    return '\n'.join(_resume_text_lines(result)[0])


# ------------------------------------------------------------------ CLI

def cmd_line(args):
    if not os.path.isfile(args.tasks):
        print(f"progress-report: no existe {args.tasks}", file=sys.stderr)
        return 1
    try:
        r = resumir(args.tasks)
    except ValueError as e:
        print(f"⚠️  progress-report: {args.tasks}: {e}", file=sys.stderr)
        return 2
    if args.json:
        r["linea"] = linea(r)
        print(json.dumps(r, ensure_ascii=False))
    else:
        print(linea(r))
    return 0


def cmd_active(args):
    proyecto = _proyecto_de(args.root)
    # fix2 B-M3: la misma instantánea acotada que el journal y el arranque (un `--root` que no es
    # `<proyecto>/docs/roadmap` conserva el escaneo histórico)
    snap = instantanea(proyecto) if proyecto else {"activas": activas(args.root), "avisos": []}
    rs = snap["activas"]
    if args.json:
        for r in rs:
            r["linea"] = linea(r)
        salida = {"activas": rs}
        if snap["avisos"]:
            salida["avisos"] = snap["avisos"]   # fix3 (B4/B5): recorte y ledgers ilegibles
        if len(rs) > 1:   # con una sola activa la salida es idéntica a la de siempre
            salida["iniciativa_en_curso"] = vigente_entre(rs, _leer_usage_state(args.root),
                                                          mtime=_lstat_mtime if proyecto else os.path.getmtime)
        print(json.dumps(salida, ensure_ascii=False))
        return 0
    if not rs:
        print(SIN_ACTIVAS)
        return 0
    for r in rs:
        print(linea(r))
    return 0


def cmd_session(args):
    snap = instantanea(args.root)   # fix2 B-M3: misma instantánea acotada que el journal
    rs = snap["activas"]
    if not rs:
        print("\n".join([LINEA_NEUTRA] + snap["avisos"][:3]))
        return 0
    out = ["Roadmap en progreso (ledger canónico = tasks.md):"]
    # H-48: las iniciativas al 100 % solo esperan su cierre; se compactan en una línea.
    cerrables = [r for r in rs if r["total"] and r["completadas"] == r["total"]]
    pendientes = [r for r in rs if r not in cerrables]
    for r in pendientes:
        out.append("- " + linea(r))
        for t in r["en_progreso"]:
            out.append(f"  · en-progreso: {t['id']} {t['titulo']}".rstrip())
    if cerrables:
        out.append(f"{len(cerrables)} al 100 % pendientes de cierre: "
                   + ", ".join("/retro " + r["slug"] for r in cerrables))
    huerf = marcadores_huerfanos(args.root, in_process=getattr(args, 'in_process', False))
    if huerf is None:
        out.append("usage-meter: no disponible")
    elif huerf:
        out.append("usage-meter: marcadores abiertos → " + ", ".join(huerf[:5])
                   + (" …" if len(huerf) > 5 else ""))
    for aviso in snap["avisos"][:3]:
        out.append(aviso)
    # fix3 (A): la MISMA regla que el journal, la memoria y la statusline
    vigente = vigente_entre(rs, _leer_usage_state(os.path.join(args.root, "docs", "roadmap")), mtime=_lstat_mtime)
    unica = next(r for r in rs if r["slug"] == vigente)
    rel = os.path.relpath(unica["path"], args.root).replace("\\", "/")
    if unica["en_progreso"]:
        cola = "retoma desde la tarea en-progreso"
    elif unica.get("total") and unica["completadas"] == unica["total"]:
        cola = "al 100 %: /retro " + unica["slug"]
    else:
        cola = "sin tarea en-progreso"
    out.append(f"Ledger canónico: {rel} — {cola}")
    # Resolve with the bounded reader on the exact folder of the single pending
    # initiative. The legacy progress scan never supplies review identities, and
    # several pending initiatives cannot select a receipt: that is not news for
    # the session block, so no opaque status line is added (H-48).
    review_lines = []
    if unica:
        try:
            reader = _load_module('session_review_reader', 'local-read.py')
            folder = os.path.basename(os.path.dirname(os.path.abspath(unica["path"])))
            status, summary, _, _ = _resume_ledger(args.root, folder, reader)
            if status == "too_large":
                # B5: sin la lectura acotada no hay revisiones que mostrar; se dice y se da el camino.
                review_lines = ["Revisiones omitidas: ledger > 256 KiB; /work-resume --initiative " + folder]
            if summary:
                review_lines = _review_text_lines(_resume_reviews(args.root, summary['path'],
                                                                  deadline=time.monotonic() + 0.75))
        except (ImportError, OSError, SyntaxError):
            review_lines = ['Revisiones: lector no disponible']
    if review_lines:
        # Keep complete IDs. Reserve one line for omissions, rather than cutting
        # a reference in half or silently hiding an open review.
        visible = review_lines[:3]
        if len(review_lines) > 3:
            visible = review_lines[:2] + ['Revisiones: detalles omitidos; consulta /work-resume.']
        out = out[:15-len(visible)] + visible
    print("\n".join(out[:15]))
    return 0


def cmd_resume(args):
    result = resume(args.root, initiative=args.initiative, session_id=args.session_id,
                    runtime=args.runtime, entry=args.entry, _history_only=args.history_only)
    if args.history_only:
        # H-48: the session block gets history or nothing; a failed selection is
        # reported by /work-resume, not as an opaque «Journal: <status>» line.
        if result["status"] != "ok" or not result["history"]:
            return 0
        journal = _load_module("resume_render_journal", "journal.py")
        print(journal.selected_text({"status": result["status"], "entries": result["history"]}))
    else:
        print(json.dumps(result, ensure_ascii=False) if args.json else resume_text(result))
    return 0


def main(argv=None, *, in_process=False):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1].strip())
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("line", help="una línea de progreso de un tasks.md")
    sp.add_argument("tasks")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_line)

    sp = sub.add_parser("active", help="iniciativas en-progreso bajo --root")
    sp.add_argument("--root", default=os.path.join("docs", "roadmap"))
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_active)

    sp = sub.add_parser("session", help="bloque de contexto de sesión (≤15 líneas)")
    sp.add_argument("--root", default=".")
    sp.set_defaults(fn=cmd_session)

    sp = sub.add_parser("resume", help="retoma dirigida, de solo lectura, desde ledger e historial")
    sp.add_argument("--root", default=".")
    sp.add_argument("--initiative")
    sp.add_argument("--session-id")
    sp.add_argument("--runtime")
    sp.add_argument("--entry")
    output = sp.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true")
    output.add_argument("--history-only", action="store_true", help="solo contexto histórico acotado")
    sp.set_defaults(fn=cmd_resume)

    args = p.parse_args(argv)
    args.in_process = in_process
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
