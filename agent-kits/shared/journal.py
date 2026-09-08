#!/usr/bin/env python3
"""
journal.py — memoria EPISÓDICA de sesión, determinista y sin MCP (agent-kits/shared).

Una entrada por sesión en `docs/knowledge/journal/AAAA-MM-DD-<slug>.md` (bitácora cronológica,
NO curada — a diferencia de `adr/`, `gotchas/` y `lessons/`, que son memoria curada con umbral;
ver `knowledge-write.md`). La escribe el hook `hooks/session-journal.sh` (SessionEnd) y la
reinyecta `hooks/session-context.sh` (SessionStart `startup|resume`, no `compact`). Los turnos del
usuario los acumula el hook `hooks/user-prompt-capture.sh` (UserPromptSubmit) con `capture` en un LOG
CRUDO no versionado, del que `draft`/`write` extraen `decisiones` y `pendientes` (memory-retrieval F4).

Subcomandos (exit 0 SIEMPRE salvo error de uso → 2; la bitácora nunca bloquea):
  capture [--root DIR]                                   ← stdin: payload del hook UserPromptSubmit
      Añade el turno del usuario (`prompt`) como UNA línea JSON `{"ts", "prompt"}` a
      `.claude/session-prompts-<session_id>.log` (no versionado: `*.log` está en .gitignore). Reglas:
      (1) con la etiqueta `<private>` en cualquier parte del turno el log NO se toca (ni se crea, ni
      mtime, ni tamaño); (2) solo en proyectos con rastro del plugin (mismo criterio que `write`) y sin
      `dev.json` → `sesion.journal: false` ni `sesion.captura: false`; (3) topes: CAPTURA_MAX_CHARS por
      turno, LOG_MAX_BYTES por fichero (se conservan los ÚLTIMOS turnos, cortando por línea) y purga de
      logs `session-prompts-*.log` con más de LOG_RETENCION_DIAS días; (4) payload roto, sin
      `session_id`, sin `prompt`, `--root` inexistente o disco no escribible → exit 0 SIN stdout ni
      stderr: en UserPromptSubmit el stdout se inyecta como contexto y un exit 2 borraría el prompt.
      Raíz: `--root` > CLAUDE_PROJECT_DIR > `cwd` del payload > `.`.
  draft  [--root DIR] [--session-id ID] [--transcript FICHERO] [--reason R] [--enrich JSON]
      Borrador de la entrada SIN modelo, en JSON:
        fecha · session_id · reason · iniciativa (primera `en-progreso` del roadmap, vía
        progress-report.py active) · resumen (primer prompt del usuario de la transcripción si
        es legible — formato JSONL NO oficial, best-effort — o «Sesión sobre <iniciativa>») ·
        decisiones/pendientes (vacías salvo --enrich) · ficheros_tocados (top 10 de
        `git status --porcelain` + `git diff --name-only HEAD`) · tareas_cambiadas (tareas
        cuyo `- **Estado**:` difiere entre el tasks.md de trabajo y `git show HEAD:…`) ·
        marcadores_cerrados (usage-state.json con `ultimoCierre` de hoy) · avisos.
      Sin git → listas vacías + aviso. Sin roadmap → iniciativa "n/a".
      `decisiones`/`pendientes`: si `--enrich` las trae, mandan; si no, salen del LOG CRUDO de la sesión
      (`capturas`) con una extracción DETERMINISTA sin modelo — frases del usuario con un marcador
      léxico ES/EN (`decidimos`, `acordamos`, `optamos por`, `we decided`… / `pendiente`, `queda por`,
      `más tarde`, `TODO:`, `remind me`…), deduplicadas, ≤ MAX_ITEMS por lista y ≤ ITEM_MAX_CHARS
      cada una; sin log o sin marcadores → `[]` HONESTO (no se inventa nada). `turnos` = nº de turnos
      capturados. `resumen`: --enrich > primer turno del log > primer prompt de la transcripción >
      «Sesión sobre <iniciativa>».
  write  [--root DIR] --session-id ID [--reason R] [--fuente hook|manual] [--enrich JSON] [--draft JSON]
         [--ia auto|on|off]
      Escribe la entrada SOLO si el proyecto tiene rastro del plugin (existe `docs/roadmap/`,
      `docs/knowledge/` o `.claude/dev.json`); en cualquier otro repo sale en silencio (exit 0, sin
      stdout) para no sembrar carpetas donde nadie usa el plugin (T-fix1). IDEMPOTENTE por
      session_id: si ya hay una entrada con ese id la ACTUALIZA en sitio (mismo fichero); si no,
      crea `AAAA-MM-DD-<slug>.md` — slug = iniciativa activa, o `sesion` si no hay ninguna — (sufijo
      -2, -3 si el nombre ya existe con otra sesión). Regenera el índice `journal/README.md`.
      Imprime la ruta. Las entradas SE VERSIONAN (memoria del proyecto, como ADR/lecciones); quien
      no quiera, añade `docs/knowledge/journal/*.md` (no el README) a su `.gitignore`.
      Resumen por IA (memory-retrieval T-13), OPT-IN: con `--ia on`, o `--ia auto` (default) y
      `dev.json` → `sesion.resumen: true`, PRIMERO se escribe la entrada determinista y DESPUÉS se
      pide a `claude -p --bare --output-format json` (el mismo CLI headless que `evals/run.py`; `--bare`
      salta hooks/plugins/MCP — sin recursión — y exige ANTHROPIC_API_KEY) un JSON con
      resumen/decisiones/pendientes a partir de los turnos capturados, y se re-escribe la MISMA entrada
      (`resumen_por: ia`). Cualquier fallo —opt-in apagado, `claude` fuera del PATH, sin clave, timeout
      IA_TIMEOUT, exit ≠ 0, JSON ilegible, guardia anti-recursión— deja la entrada determinista con el
      motivo en `avisos` y exit 0: el cierre de sesión nunca se entera.
  latest [--root DIR] [--n 2] [--max-lines 25]
      Bloque compacto para el contexto de sesión: la ÚLTIMA entrada o las N últimas si son de
      días distintos; recortado a --max-lines. Sin carpeta/entradas → sin salida.
  index  [--root DIR]
      Regenera `docs/knowledge/journal/README.md` (tabla fecha · iniciativa · resumen · fuente).
  candidatas [--root DIR] [--min N] [--iniciativa SLUG] [--json]
      Promoción journal → CANDIDATA a lección (memory-retrieval T-14; spec CA-19): un mismo patrón
      (raíces con contenido —tokenizador de `knowledge-find.py`— que solapan ≥ CANDIDATA_JACCARD con las
      de la primera formulación vista; agrupación voraz en orden cronológico, determinista) en
      `decisiones` o `pendientes` de ≥ N entradas de SESIONES distintas (N = CANDIDATA_MIN = 2; una entrada
      cuenta una vez aunque lo repita) sale como candidata con `estado: propuesta` y su EVIDENCIA (fecha,
      fichero, session_id de cada entrada). NUNCA nace `aceptada`: la curación sigue siendo la revisión de dos
      lentes o el usuario, por la puerta de `/retro` (que es quien invoca esto). Sin journal, con una
      sola entrada o sin patrón repetido → sin salida, exit 0.

`--enrich JSON` (fichero o `-` para stdin): {"resumen": "...", "decisiones": [...], "pendientes": [...]}
— entrada MANUAL que manda sobre lo extraído del log y sobre la IA. Sobre el contrato: la doc oficial
(hooks.md, 2026-09-03) sigue sin permitir que un hook `prompt`/`agent` en SessionEnd DEVUELVA texto
(solo decisión `ok/reason`, y en SessionEnd la salida se ignora) — eso sigue siendo cierto y por eso el
hook `command` no devuelve nada: ESCRIBE (ADR-010, revisada 2026-09-08 por memory-retrieval T-12/T-13).
"""
import argparse
import datetime as _dt
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time

# Consola Windows (cp1252) o tuberías: reconfigurar ANTES de leer o imprimir nada (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

HERE = os.path.dirname(os.path.abspath(__file__))
JOURNAL_REL = os.path.join("docs", "knowledge", "journal")
TOP_FICHEROS = 10
GIT_TIMEOUT = 5
LISTAS = ("decisiones", "pendientes", "ficheros_tocados", "tareas_cambiadas", "marcadores_cerrados")
_SLUG_RE = re.compile(r"[^a-z0-9]+")

# --- log crudo del turno del usuario (hook UserPromptSubmit → `capture`; memory-retrieval T-11) ---
LOG_DIR_REL = ".claude"
LOG_PREFIX = "session-prompts-"
PRIVATE_TAG = "<private>"          # en cualquier parte del turno, sin distinguir mayúsculas → el log NO se toca
CAPTURA_MAX_CHARS = 4000           # tope por turno (un turno gigantesco no llena el disco)
LOG_MAX_BYTES = 256 * 1024         # tope por fichero: al superarlo se conservan los ÚLTIMOS turnos (½ del tope)
LOG_RETENCION_DIAS = 30            # purga de `session-prompts-*.log` más viejos (mtime) al capturar
_SID_RE = re.compile(r"[^A-Za-z0-9._-]")

# --- extracción DETERMINISTA de decisiones/pendientes del log crudo (T-12; sin modelo) ---
# Una FRASE del usuario cuenta si contiene un marcador léxico (ES/EN). Deliberadamente estrecho: mejor
# `[]` honesto que ruido. «luego»/«later» a secas NO son marcadores (secuencian, no aplazan).
MAX_ITEMS = 8                      # por lista
ITEM_MAX_CHARS = 200               # por elemento
_FRASE_RE = re.compile(r"(?<=[.!?])\s+|\n+")
DECISION_RE = re.compile(
    r"(?<!\w)(?:decid(?:o|imos|ido|ida)|decisi[oó]n|acord(?:amos|ado)|opt(?:amos|o) por|vamos a usar|usaremos|"
    r"nos quedamos con|eleg(?:imos|ido)|elijo|descart(?:amos|ado)|se descarta|"
    r"we decided|decided to|decision:|let'?s use|we'?ll (?:use|go with)|go(?:ing)? with|we chose)(?!\w)", re.I)
PENDIENTE_RE = re.compile(
    r"(?<!\w)(?:pendientes?|queda(?:n)? por|falta(?:n)? por|m[aá]s tarde|en otra sesi[oó]n|para (?:la )?pr[oó]xima|"
    r"no (?:te )?olvides|no olvidar|recu[eé]rdame|todo:|dej(?:amos|a|ar) para|aparc(?:amos|ado)|pospon(?:emos|er|go)|"
    r"pending|next session|don'?t forget|remind me|to-?do:)(?!\w)", re.I)

# --- resumen por IA, opt-in (T-13) ---
IA_TIMEOUT = 25                    # s; el hook SessionEnd declara `timeout: 45` en hooks.json (máx. oficial 60)
IA_MAX_CHARS = 6000                # de turnos que viajan en el prompt (los ÚLTIMOS: las decisiones llegan al final)
IA_ENV_GUARD = "CUSTOM_AGENTS_JOURNAL_IA"   # =0 en el hijo: si algo re-entrara aquí, no vuelve a llamar al modelo

# --- promoción journal → candidata a lección (T-14) ---
CANDIDATA_MIN = 2                  # entradas (sesiones distintas) en las que debe repetirse el patrón
CANDIDATA_MIN_RAICES = 2           # un patrón de una sola raíz («ok», «tests») no es un patrón
CANDIDATA_JACCARD = 0.6            # dos formulaciones son el MISMO patrón si sus raíces solapan ≥ 60 % (Jaccard)


def _load_module(name, filename):
    path = os.path.join(HERE, filename)
    if not os.path.isfile(path):
        return None
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:  # noqa: BLE001 — degradación: sin el módulo, sin esa medida
        return None


def hoy():
    return _dt.date.today().isoformat()


def slugify(s):
    """Slug del nombre de fichero: la iniciativa activa; sin iniciativa (`n/a`, vacío) → `sesion`."""
    if not s or s.strip().lower() in ("n/a", "na", "n-a"):
        return "sesion"
    s = _SLUG_RE.sub("-", s.lower()).strip("-")
    return s or "sesion"


def proyecto_con_plugin(root):
    """¿Hay rastro del plugin en el proyecto? Solo entonces se escribe la bitácora (T-fix1)."""
    return any(os.path.exists(os.path.join(root, *p)) for p in
               (("docs", "roadmap"), ("docs", "knowledge"), (".claude", "dev.json")))


def _dev_sesion(root):
    """Bloque `sesion` de `.claude/dev.json` ({} si no hay fichero, está corrupto o no es un objeto)."""
    try:
        d = json.load(open(os.path.join(root, ".claude", "dev.json"), encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    s = d.get("sesion") if isinstance(d, dict) else None
    return s if isinstance(s, dict) else {}


# ------------------------------------------------------------------ log crudo (capture / capturas)

def _sid_seguro(session_id):
    """`session_id` como trozo de nombre de fichero: nunca sale de `.claude/` (sin separadores)."""
    return _SID_RE.sub("_", str(session_id))[:80]


def log_path(root, session_id):
    return os.path.join(root, LOG_DIR_REL, f"{LOG_PREFIX}{_sid_seguro(session_id)}.log")


def _rotar(path):
    """Si el log supera LOG_MAX_BYTES, conserva los ÚLTIMOS ~½ LOG_MAX_BYTES cortando por línea."""
    try:
        if os.path.getsize(path) <= LOG_MAX_BYTES:
            return
        with open(path, "rb") as fh:
            data = fh.read()
        cola = data[-(LOG_MAX_BYTES // 2):]
        salto = cola.find(b"\n")
        cola = cola[salto + 1:] if salto != -1 else cola
        with open(path, "wb") as fh:
            fh.write(cola)
    except OSError:
        pass


def _purgar_logs(dirpath, excepto=None, ahora=None):
    ahora = ahora or time.time()
    try:
        nombres = os.listdir(dirpath)
    except OSError:
        return
    for fn in nombres:
        if not (fn.startswith(LOG_PREFIX) and fn.endswith(".log")):
            continue
        p = os.path.join(dirpath, fn)
        if excepto and os.path.abspath(p) == os.path.abspath(excepto):
            continue
        try:
            if ahora - os.stat(p).st_mtime > LOG_RETENCION_DIAS * 86400:
                os.remove(p)
        except OSError:
            pass


def capture(root, payload):
    """Añade el turno del payload de UserPromptSubmit al log crudo de su sesión. Devuelve la ruta
    escrita o None si no se escribió (payload inválido, `<private>`, sin rastro del plugin, opt-out).
    Nunca lanza más allá de errores de disco que el CLI traga en silencio."""
    if not isinstance(payload, dict):
        return None
    sid, prompt = payload.get("session_id"), payload.get("prompt")
    if not isinstance(sid, str) or not sid.strip() or not isinstance(prompt, str) or not prompt.strip():
        return None
    if PRIVATE_TAG in prompt.lower():
        return None                                     # opt-out por turno: ni se crea, ni mtime, ni tamaño
    if not proyecto_con_plugin(root):
        return None
    ses = _dev_sesion(root)
    if ses.get("journal") is False or ses.get("captura") is False:
        return None
    texto = prompt.strip()
    if len(texto) > CAPTURA_MAX_CHARS:
        texto = texto[:CAPTURA_MAX_CHARS].rstrip() + " …[recortado]"
    d = os.path.join(root, LOG_DIR_REL)
    os.makedirs(d, exist_ok=True)
    path = log_path(root, sid)
    rec = {"ts": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "prompt": texto}
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    _rotar(path)
    _purgar_logs(d, excepto=path)
    return path


def capturas(root, session_id):
    """Turnos capturados de la sesión, en orden ([] sin log, sin session_id o ilegible; las líneas
    rotas se saltan)."""
    if not session_id:
        return []
    out = []
    try:
        with open(log_path(root, session_id), encoding="utf-8", errors="replace") as fh:
            for raw in fh:
                try:
                    rec = json.loads(raw)
                except ValueError:
                    continue
                if isinstance(rec, dict) and isinstance(rec.get("prompt"), str) and rec["prompt"].strip():
                    out.append(rec["prompt"])
    except OSError:
        return []
    return out


# ------------------------------------------------------------------ extracción determinista (T-12)

def _frases(turnos):
    for t in turnos:
        if not isinstance(t, str):
            continue
        for f in _FRASE_RE.split(t):
            f = " ".join(f.split())
            f = re.sub(r"^[-*•]\s+", "", f)
            if f and not f.startswith("<"):
                yield f


def _acotar(items):
    """Deduplica (sin distinguir mayúsculas/espacios/puntuación final), recorta cada elemento a
    ITEM_MAX_CHARS y la lista a MAX_ITEMS, conservando el orden de aparición."""
    vistos, out = set(), []
    for x in items:
        x = " ".join(str(x).split())
        if not x:
            continue
        k = x.lower().rstrip(".!?;:, ")
        if k in vistos:
            continue
        vistos.add(k)
        if len(x) > ITEM_MAX_CHARS:
            x = x[:ITEM_MAX_CHARS - 1].rstrip() + "…"
        out.append(x)
        if len(out) >= MAX_ITEMS:
            break
    return out


def _extraer(turnos, patron):
    return _acotar(f for f in _frases(turnos) if patron.search(f))


def decisiones_de(turnos):
    """Frases del usuario con marcador de DECISIÓN (DECISION_RE); [] si no hay ninguna."""
    return _extraer(turnos, DECISION_RE)


def pendientes_de(turnos):
    """Frases del usuario con marcador de PENDIENTE (PENDIENTE_RE); [] si no hay ninguna."""
    return _extraer(turnos, PENDIENTE_RE)


# ------------------------------------------------------------------ git

def _git(root, *args):
    """stdout de git o None si git no está / no es repo / falla (nunca lanza)."""
    try:
        r = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=GIT_TIMEOUT, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    return r.stdout


def _es_journal(path):
    return path.replace("\\", "/").lstrip("./").startswith(JOURNAL_REL.replace(os.sep, "/") + "/")


def ficheros_tocados(root, avisos):
    """Top N de ficheros con cambios (sin comitear: status; + diff vs HEAD), con su marca."""
    status = _git(root, "status", "--porcelain", "--untracked-files=all")
    if status is None:
        avisos.append("git no disponible o no es un repositorio: sin ficheros tocados")
        return []
    vistos, out = set(), []
    for line in status.splitlines():
        if len(line) < 4:
            continue
        marca, path = line[:2].strip() or "M", line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if _es_journal(path):            # la propia bitácora no cuenta como trabajo de la sesión
            continue
        if path and path not in vistos:
            vistos.add(path)
            out.append({"path": path, "cambio": marca})
    diff = _git(root, "diff", "--name-only", "HEAD") or ""
    for path in diff.splitlines():
        path = path.strip()
        if path and path not in vistos and not _es_journal(path):
            vistos.add(path)
            out.append({"path": path, "cambio": "M"})
    return out[:TOP_FICHEROS]


def tareas_cambiadas(root, avisos):
    """Tareas cuyo estado difiere entre el tasks.md de trabajo y HEAD, para cada ledger
    modificado del roadmap (`T-01: borrador → en-progreso`). Reutiliza parse_ledger."""
    ll = _load_module("ledger_lint", "ledger-lint.py")
    if ll is None:
        avisos.append("ledger-lint.py no está junto a journal.py: sin tareas cambiadas")
        return []
    status = _git(root, "status", "--porcelain")
    if status is None:
        return []
    out = []
    for line in status.splitlines():
        path = line[3:].strip()
        if not re.search(r"docs/roadmap/[^/]+/tasks\.md$", path.replace("\\", "/")):
            continue
        marca = line[:2].strip()
        antes = _git(root, "show", f"HEAD:{path}") if "?" not in marca else ""
        try:
            ahora = open(os.path.join(root, path), encoding="utf-8-sig", errors="replace").read()
        except OSError:
            continue
        try:
            t_antes = {t["id"]: t["estado"] for t in ll.parse_ledger(antes or "")["tareas"]}
            t_ahora = ll.parse_ledger(ahora)["tareas"]
        except Exception:  # noqa: BLE001 — ledger ilegible: no es motivo para fallar
            continue
        slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", path.replace("\\", "/").split("/")[-2])
        for t in t_ahora:
            prev = t_antes.get(t["id"])
            if t["estado"] and prev != t["estado"]:
                out.append({"iniciativa": slug, "id": t["id"], "titulo": t["titulo"],
                            "antes": prev or "—", "ahora": t["estado"]})
    return out


# ------------------------------------------------------------------ roadmap / meter / transcripción

def iniciativa_activa(root):
    pr = _load_module("progress_report", "progress-report.py")
    roadmap = os.path.join(root, "docs", "roadmap")
    if pr is None or not os.path.isdir(roadmap):
        return None
    try:
        import contextlib
        import io
        with contextlib.redirect_stderr(io.StringIO()):
            rs = pr.activas(roadmap)
    except Exception:  # noqa: BLE001
        return None
    return rs[0]["slug"] if rs else None


def marcadores_cerrados(root, fecha):
    state = os.path.join(root, ".claude", "usage-state.json")
    try:
        data = json.load(open(state, encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(data, dict):
        return []
    return sorted(k for k, m in data.items()
                  if isinstance(m, dict) and str(m.get("ultimoCierre", "")).startswith(fecha))


def primer_prompt(transcript, max_chars=160):
    """Primer mensaje de usuario de la transcripción JSONL (formato no oficial: best-effort).
    Ignora mensajes de sistema/meta y los que empiezan por '<' (recordatorios, comandos)."""
    if not transcript or not os.path.isfile(transcript):
        return None
    try:
        with open(transcript, encoding="utf-8", errors="replace") as fh:
            for raw in fh:
                try:
                    rec = json.loads(raw)
                except ValueError:
                    continue
                if not isinstance(rec, dict) or rec.get("type") != "user" or rec.get("isMeta"):
                    continue
                msg = rec.get("message") or {}
                content = msg.get("content") if isinstance(msg, dict) else None
                if isinstance(content, list):
                    content = " ".join(b.get("text", "") for b in content
                                       if isinstance(b, dict) and b.get("type") == "text")
                if not isinstance(content, str):
                    continue
                texto = " ".join(content.split())
                if not texto or texto.startswith("<"):
                    continue
                return texto if len(texto) <= max_chars else texto[:max_chars - 1].rstrip() + "…"
    except OSError:
        return None
    return None


def cargar_enrich(spec, avisos):
    if not spec:
        return {}
    try:
        data = json.load(sys.stdin) if spec == "-" else json.load(open(spec, encoding="utf-8"))
    except (OSError, ValueError) as e:
        avisos.append(f"--enrich ilegible ({e}); se ignora")
        return {}
    return data if isinstance(data, dict) else {}


def _lista(v):
    if isinstance(v, str):
        return [v] if v.strip() else []
    return [str(x) for x in v] if isinstance(v, list) else []


def _recorta(texto, max_chars=160):
    texto = " ".join(str(texto).split())
    return texto if len(texto) <= max_chars else texto[:max_chars - 1].rstrip() + "…"


def draft(root, session_id=None, transcript=None, reason=None, enrich=None):
    avisos = []
    fecha = hoy()
    iniciativa = iniciativa_activa(root) or "n/a"
    enr = cargar_enrich(enrich, avisos)
    turnos = capturas(root, session_id)
    if enr.get("resumen"):
        resumen, resumen_por = enr["resumen"], "manual"
    else:
        resumen = (_recorta(turnos[0]) if turnos else None) or primer_prompt(transcript) or f"Sesión sobre {iniciativa}"
        resumen_por = "determinista"
    return {
        "fecha": fecha,
        "session_id": session_id or "manual",
        "reason": reason or "manual",
        "iniciativa": iniciativa,
        "resumen": str(resumen),
        "resumen_por": resumen_por,
        "turnos": len(turnos),
        "decisiones": _lista(enr.get("decisiones")) or decisiones_de(turnos),   # el --enrich manda solo si trae algo
        "pendientes": _lista(enr.get("pendientes")) or pendientes_de(turnos),
        "ficheros_tocados": ficheros_tocados(root, avisos),
        "tareas_cambiadas": tareas_cambiadas(root, avisos),
        "marcadores_cerrados": marcadores_cerrados(root, fecha),
        "avisos": avisos,
    }


# ------------------------------------------------------------------ fichero de entrada

def _yaml_str(s):
    return json.dumps(str(s), ensure_ascii=False)


def render(e, fuente):
    fm = [f"fecha: {e['fecha']}", f"session_id: {_yaml_str(e['session_id'])}",
          f"reason: {e.get('reason') or 'manual'}", f"iniciativa: {e['iniciativa']}",
          f"resumen: {_yaml_str(e['resumen'])}", f"fuente: {fuente}",
          f"resumen_por: {e.get('resumen_por') or 'determinista'}", f"turnos: {int(e.get('turnos') or 0)}"]
    for k in ("decisiones", "pendientes"):
        fm.append(f"{k}:" + ("" if e[k] else " []"))
        fm += [f"  - {_yaml_str(x)}" for x in e[k]]
    fm.append("ficheros_tocados:" + ("" if e["ficheros_tocados"] else " []"))
    fm += [f"  - {_yaml_str(f['path'] + ' (' + f['cambio'] + ')')}" for f in e["ficheros_tocados"]]
    fm.append("tareas_cambiadas:" + ("" if e["tareas_cambiadas"] else " []"))
    fm += [f"  - {_yaml_str(t['iniciativa'] + ' ' + t['id'] + ': ' + t['antes'] + ' → ' + t['ahora'])}"
           for t in e["tareas_cambiadas"]]
    fm.append("marcadores_cerrados:" + ("" if e["marcadores_cerrados"] else " []"))
    fm += [f"  - {_yaml_str(m)}" for m in e["marcadores_cerrados"]]

    body = [f"# Journal — {e['fecha']} — {e['iniciativa']}", "",
            "> Entrada de **bitácora de sesión** (memoria episódica, cronológica, no curada; "
            "`agent-kits/shared/journal.py`). Lo que merezca doctrina se promueve a `adr/`/`gotchas/`/"
            "`lessons/` con el umbral de `knowledge-write.md`; esto NO se publica en Confluence.", "",
            "## Resumen", "", e["resumen"], ""]

    def seccion(titulo, items, vacio):
        body.extend([f"## {titulo}", ""])
        body.extend([f"- {x}" for x in items] if items else [f"_{vacio}_"])
        body.append("")

    seccion("Decisiones", e["decisiones"], "sin decisiones registradas (borrador determinista)")
    seccion("Pendientes", e["pendientes"], "sin pendientes registrados")
    seccion(f"Ficheros tocados (top {TOP_FICHEROS})",
            [f"`{f['path']}` ({f['cambio']})" for f in e["ficheros_tocados"]], "sin cambios detectados")
    seccion("Tareas que cambiaron de estado",
            [f"`{t['iniciativa']}` {t['id']} {t['titulo']}: {t['antes']} → {t['ahora']}".replace("  ", " ")
             for t in e["tareas_cambiadas"]], "ninguna")
    seccion("Marcadores de coste cerrados (usage-meter)",
            [f"`{m}`" for m in e["marcadores_cerrados"]], "ninguno")
    if e.get("avisos"):
        seccion("Avisos", e["avisos"], "")
    return "---\n" + "\n".join(fm) + "\n---\n\n" + "\n".join(body).rstrip() + "\n"


def parse_entry(path):
    """Frontmatter mínimo de una entrada → dict (escalares + listas). None si no es entrada."""
    try:
        text = open(path, encoding="utf-8-sig", errors="replace").read()
    except OSError:
        return None
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    out, cur = {"_path": path}, None
    for raw in text[3:end].splitlines():
        if not raw.strip():
            continue
        if raw.startswith("  - ") and cur:
            out.setdefault(cur, []).append(_unquote(raw[4:].strip()))
            continue
        if ":" not in raw or raw.startswith(" "):
            continue
        k, v = raw.split(":", 1)
        k, v = k.strip(), v.strip()
        if v == "" or v == "[]":
            out[k], cur = [], k
        else:
            out[k], cur = _unquote(v), None
    if "fecha" not in out or "session_id" not in out:
        return None
    return out


def _unquote(v):
    if len(v) >= 2 and v[0] == '"' and v[-1] == '"':
        try:
            return json.loads(v)
        except ValueError:
            return v[1:-1]
    return v


def journal_dir(root):
    return os.path.join(root, JOURNAL_REL)


def entradas(root):
    """Entradas ordenadas por (fecha, mtime): la última es la más reciente."""
    d = journal_dir(root)
    if not os.path.isdir(d):
        return []
    out = []
    for fn in os.listdir(d):
        if not fn.endswith(".md") or fn == "README.md":
            continue
        p = os.path.join(d, fn)
        e = parse_entry(p)
        if e:
            try:
                e["_mtime"] = os.stat(p).st_mtime
            except OSError:
                e["_mtime"] = 0
            out.append(e)
    out.sort(key=lambda e: (str(e.get("fecha")), e["_mtime"], e["_path"]))
    return out


def write(root, e, fuente="hook"):
    """Escribe/actualiza la entrada; None (sin tocar disco) si el proyecto no tiene rastro del plugin."""
    if not proyecto_con_plugin(root):
        return None
    d = journal_dir(root)
    os.makedirs(d, exist_ok=True)
    destino = None
    for prev in entradas(root):
        if prev.get("session_id") == e["session_id"]:
            destino = prev["_path"]
            break
    if destino is None:
        base = f"{e['fecha']}-{slugify(e['iniciativa'])}"
        destino = os.path.join(d, base + ".md")
        n = 2
        while os.path.exists(destino):
            destino = os.path.join(d, f"{base}-{n}.md")
            n += 1
    with open(destino, "w", encoding="utf-8") as fh:
        fh.write(render(e, fuente))
    index(root)
    return destino


# ------------------------------------------------------------------ índice y latest

def index(root):
    d = journal_dir(root)
    if not os.path.isdir(d):
        return None
    es = entradas(root)
    lines = ["# `docs/knowledge/journal/` — bitácora de sesión (memoria episódica)", "",
             "Una entrada por sesión, **generada** por `agent-kits/shared/journal.py` (hook `SessionEnd`; la",
             "última se reinyecta al arrancar/retomar). Cronológica y **no curada**: lo que merezca doctrina",
             "se promueve a `adr/`, `gotchas/` o `lessons/` con el umbral de `knowledge-write.md`. **Excluida de",
             "Confluence** (`docs/knowledge/journal/**`). Nombre: `AAAA-MM-DD-<iniciativa activa | sesion>.md` (sufijo `-2`",
             "si otra sesión del día ya lo usó). **Las entradas se versionan** (memoria del proyecto, como ADR y lecciones);",
             "quien no quiera versionarlas añade `docs/knowledge/journal/*.md` (no este README) a su `.gitignore`.",
             "Este índice lo regenera `journal.py index`; no lo edites.", "",
             "| Fecha | Iniciativa | Resumen | Fuente |", "|---|---|---|---|"]
    for e in reversed(es):
        fn = os.path.basename(e["_path"])
        resumen = str(e.get("resumen", "")).replace("|", "\\|")
        if len(resumen) > 100:
            resumen = resumen[:99].rstrip() + "…"
        lines.append(f"| [{e['fecha']}]({fn}) | {e.get('iniciativa', 'n/a')} | {resumen} | {e.get('fuente', '?')} |")
    if not es:
        lines.append("| — | — | _sin entradas todavía_ | — |")
    p = os.path.join(d, "README.md")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return p


def _corta(items, n=3):
    items = [str(x) for x in items]
    if len(items) <= n:
        return "; ".join(items)
    return "; ".join(items[:n]) + f" (+{len(items) - n})"


def latest(root, n=2, max_lines=25):
    es = entradas(root)
    if not es:
        return ""
    sel = [es[-1]]
    for prev in reversed(es[:-1]):
        if len(sel) >= n:
            break
        if prev.get("fecha") != sel[-1].get("fecha"):
            sel.append(prev)
    out = [f"Journal de sesión (docs/knowledge/journal/ — memoria episódica; {len(sel)} última(s) entrada(s)):"]
    for e in sel:
        out.append(f"- {e['fecha']} · {e.get('iniciativa', 'n/a')} · {e.get('resumen', '')} · fuente: {e.get('fuente', '?')}")
        if e.get("decisiones"):
            out.append(f"  decisiones: {_corta(e['decisiones'])}")
        if e.get("pendientes"):
            out.append(f"  pendientes: {_corta(e['pendientes'])}")
        if e.get("tareas_cambiadas"):
            out.append(f"  tareas: {_corta(e['tareas_cambiadas'], 4)}")
        if e.get("ficheros_tocados"):
            out.append(f"  tocados: {_corta([f.split(' (')[0] for f in e['ficheros_tocados']], 5)}")
    if len(out) > max_lines:
        out = out[:max_lines - 1] + ["  …"]
    return "\n".join(out)


# ------------------------------------------------------------------ resumen por IA, opt-in (T-13)

def ia_activa(root):
    """`dev.json` → {"sesion": {"resumen": true}}. Cualquier otra cosa (ausente, corrupto, no bool) → False."""
    return _dev_sesion(root).get("resumen") is True


def _prompt_ia(turnos, borrador):
    cuerpo = "\n".join(f"- {t}" for t in turnos)
    if len(cuerpo) > IA_MAX_CHARS:
        cuerpo = "…\n" + cuerpo[-IA_MAX_CHARS:]
    return (f"Eres el redactor de la bitácora de una sesión de trabajo sobre la iniciativa «{borrador.get('iniciativa', 'n/a')}». "
            "A partir de los TURNOS DEL USUARIO de abajo devuelve SOLO un objeto JSON, sin texto alrededor ni bloque de "
            'código, con estas claves: {"resumen": "<una frase de hasta 160 caracteres>", "decisiones": ["<frase corta>"], '
            '"pendientes": ["<frase corta>"]}. En español. Máximo 8 elementos por lista. Solo lo que los turnos digan de '
            "forma explícita: si no hay decisiones o pendientes, lista vacía; no inventes.\n\n"
            f"--- turnos del usuario ({len(turnos)}) ---\n{cuerpo}\n")


def _parsear_ia(stdout):
    """`--output-format json` → {"result": "<texto>", "is_error": bool, …}; el texto debe ser (o contener) el
    objeto JSON pedido. None si cualquier capa no parsea o `is_error`."""
    try:
        outer = json.loads(stdout)
    except ValueError:
        return None
    if not isinstance(outer, dict) or outer.get("is_error"):
        return None
    result = outer.get("result")
    if not isinstance(result, str):
        return None
    m = re.search(r"\{.*\}", result, re.S)
    if not m:
        return None
    try:
        inner = json.loads(m.group(0))
    except ValueError:
        return None
    if not isinstance(inner, dict):
        return None
    out = {"decisiones": _acotar(_lista(inner.get("decisiones"))), "pendientes": _acotar(_lista(inner.get("pendientes")))}
    if isinstance(inner.get("resumen"), str) and inner["resumen"].strip():
        out["resumen"] = _recorta(inner["resumen"])
    return out


def resumen_ia(turnos, borrador, runner=None, which=None, environ=None):
    """(datos, aviso): datos = {"resumen"?, "decisiones", "pendientes"} o None; aviso = por qué se degrada
    (o None). Lanza `claude -p <prompt> --bare --output-format json --max-turns 1` — el CLI headless que
    ya usa evals/run.py; `--bare` salta hooks, plugins, MCP y CLAUDE.md (así el SessionEnd de la sesión
    hija no vuelve a entrar aquí) y exige ANTHROPIC_API_KEY. `runner`/`which`/`environ` se inyectan en
    los tests: aquí nunca se lanza `claude` de verdad."""
    runner = runner or subprocess.run
    which = which or shutil.which
    environ = os.environ if environ is None else environ
    if environ.get(IA_ENV_GUARD) == "0":
        return None, "resumen IA: desactivado en este proceso (guardia anti-recursión) — entrada determinista"
    if not turnos:
        return None, "resumen IA: sin turnos capturados que resumir — entrada determinista"
    exe = which("claude")
    if not exe:
        return None, "resumen IA: `claude` no está en PATH — entrada determinista"
    if not environ.get("ANTHROPIC_API_KEY"):
        return None, "resumen IA: sin ANTHROPIC_API_KEY (`claude -p --bare` la exige) — entrada determinista"
    cmd = [exe, "-p", _prompt_ia(turnos, borrador), "--bare", "--output-format", "json", "--max-turns", "1"]
    env = dict(environ)
    env[IA_ENV_GUARD] = "0"
    try:
        r = runner(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=IA_TIMEOUT, env=env)
    except subprocess.TimeoutExpired:
        return None, f"resumen IA: timeout tras {IA_TIMEOUT}s — entrada determinista"
    except (OSError, subprocess.SubprocessError) as e:
        return None, f"resumen IA: no se pudo lanzar `claude` ({e.__class__.__name__}) — entrada determinista"
    if getattr(r, "returncode", 1) != 0:
        return None, f"resumen IA: `claude` salió con {getattr(r, 'returncode', '?')} — entrada determinista"
    datos = _parsear_ia(getattr(r, "stdout", "") or "")
    if datos is None:
        return None, "resumen IA: la respuesta no es el JSON esperado — entrada determinista"
    return datos, None


def escribir_sesion(root, session_id, reason=None, transcript=None, fuente="hook", enrich=None, ia="auto",
                    runner=None, which=None, environ=None):
    """Lo que hace el hook SessionEnd: entrada DETERMINISTA primero (ya está en disco aunque lo que sigue
    muera por timeout) y, si toca IA (`on`, o `auto` + dev.json `sesion.resumen: true`), la MISMA entrada
    re-escrita con el resumen (`resumen_por: ia`) o con el motivo de la degradación en `avisos`.
    Devuelve (ruta | None, entrada)."""
    e = draft(root, session_id, transcript, reason, enrich)
    p = write(root, e, fuente)
    if p is None:
        return None, e
    if ia == "on" or (ia == "auto" and ia_activa(root)):
        datos, aviso = resumen_ia(capturas(root, session_id), e, runner, which, environ)
        if datos:
            if datos.get("resumen") and e.get("resumen_por") != "manual":    # el --enrich manual manda sobre la IA
                e["resumen"], e["resumen_por"] = datos["resumen"], "ia"
            e["decisiones"] = datos["decisiones"] or e["decisiones"]
            e["pendientes"] = datos["pendientes"] or e["pendientes"]
        else:
            e["avisos"].append(aviso)
            print(f"journal: {aviso}", file=sys.stderr)
        write(root, e, fuente)
    return p, e


# ------------------------------------------------------------------ candidatas a lección (T-14)

_KF = {"cargado": False, "mod": None}
_STOP_MINI = frozenset("a al de del el la las lo los un una unos unas y o u e en con por para que se su sus es son "
                       "the a an of to in on for and or is are be it this that".split())


def _raices(texto):
    """Raíces con contenido de un elemento de decisiones/pendientes (tokenizador de `knowledge-find.py` si
    está junto a este fichero: stopwords ES/EN + raíz ligera; si no, tokens sin una mini lista de
    stopwords). frozenset vacío si quedan < CANDIDATA_MIN_RAICES raíces: no es un patrón."""
    if not _KF["cargado"]:
        _KF["cargado"], _KF["mod"] = True, _load_module("knowledge_find", "knowledge-find.py")
    kf = _KF["mod"]
    if kf is not None and hasattr(kf, "tokens_consulta"):
        raices = kf.tokens_consulta(str(texto))
    else:
        import unicodedata
        plano = "".join(c for c in unicodedata.normalize("NFKD", str(texto)) if not unicodedata.combining(c)).lower()
        raices = [t for t in re.findall(r"[0-9a-z]+", plano) if len(t) > 1 and t not in _STOP_MINI]
    r = frozenset(raices)
    return r if len(r) >= CANDIDATA_MIN_RAICES else frozenset()


def _clave_patron(texto):
    """Clave legible del patrón (raíces ordenadas) o None si el texto no forma patrón."""
    r = _raices(texto)
    return " ".join(sorted(r)) if r else None


def _jaccard(a, b):
    return len(a & b) / len(a | b) if (a or b) else 0.0


def candidatas(root, minimo=CANDIDATA_MIN, iniciativa=None):
    """Patrones de `decisiones`/`pendientes` repetidos en ≥ `minimo` entradas de sesiones distintas →
    [{"estado": "propuesta", "tipo": "lección", "campo", "texto", "clave", "entradas": n, "evidencia": [...]}],
    ordenados por nº de entradas desc. `texto` es la primera formulación vista (la más antigua)."""
    grupos = {"decisiones": [], "pendientes": []}     # agrupación voraz: el primer grupo que solape ≥ CANDIDATA_JACCARD
    for e in entradas(root):                             # orden cronológico (fecha, mtime): determinista
        if iniciativa and str(e.get("iniciativa")) != iniciativa:
            continue
        sid = str(e.get("session_id"))
        for campo in ("decisiones", "pendientes"):
            items = e.get(campo)
            if not isinstance(items, list):
                continue
            for item in items:
                r = _raices(item)
                if not r:
                    continue
                g = next((g for g in grupos[campo] if _jaccard(g["_raices"], r) >= CANDIDATA_JACCARD), None)
                if g is None:
                    g = {"estado": "propuesta", "tipo": "lección", "campo": campo, "texto": " ".join(str(item).split()),
                         "clave": " ".join(sorted(r)), "_raices": r, "evidencia": []}
                    grupos[campo].append(g)
                if any(ev["session_id"] == sid for ev in g["evidencia"]):
                    continue                                   # una entrada cuenta UNA vez
                g["evidencia"].append({"fecha": str(e.get("fecha")), "fichero": os.path.basename(e["_path"]),
                                       "session_id": sid, "iniciativa": str(e.get("iniciativa") or "n/a")})
    out = [g for gs in grupos.values() for g in gs if len(g["evidencia"]) >= max(1, int(minimo))]
    for g in out:
        g.pop("_raices", None)
    for g in out:
        g["entradas"] = len(g["evidencia"])
    out.sort(key=lambda g: (-g["entradas"], g["campo"], g["texto"].lower()))
    return out


def render_candidatas(lista, minimo=CANDIDATA_MIN):
    if not lista:
        return ""
    out = [f"Candidatas a lección desde el journal (patrón repetido en ≥ {minimo} entradas de sesiones distintas; "
           f"nacen `propuesta` — la curación sigue siendo la revisión de dos lentes o el usuario, por /retro):"]
    for g in lista:
        ev = " · ".join(f"{x['fecha']} {x['fichero']}" for x in g["evidencia"])
        out.append(f"- [{g['estado']}] «{g['texto']}» · {g['campo']} · {g['entradas']} entradas: {ev}")
    return "\n".join(out)


# ------------------------------------------------------------------ CLI

def cmd_capture(a):
    """Nunca stdout ni stderr, nunca exit ≠ 0: en UserPromptSubmit el stdout es contexto y el exit 2 borra el prompt."""
    try:
        payload = json.load(sys.stdin)
        root = a.root or os.environ.get("CLAUDE_PROJECT_DIR") or (payload.get("cwd") if isinstance(payload, dict) else None) or "."
        if os.path.isdir(str(root)):
            capture(str(root), payload)
    except Exception:  # noqa: BLE001 — el turno del usuario no se toca por nada de lo que pase aquí
        pass
    return 0


def cmd_candidatas(a):
    lista = candidatas(a.root, a.min, a.iniciativa)
    if not lista:
        return 0
    if a.json:
        print(json.dumps(lista, ensure_ascii=False, indent=2))
    else:
        print(render_candidatas(lista, a.min))
    return 0


def cmd_draft(a):
    print(json.dumps(draft(a.root, a.session_id, a.transcript, a.reason, a.enrich), ensure_ascii=False, indent=2))
    return 0


def cmd_write(a):
    if a.draft:
        try:
            e = json.load(sys.stdin) if a.draft == "-" else json.load(open(a.draft, encoding="utf-8"))
        except (OSError, ValueError) as err:
            print(f"journal: --draft ilegible: {err}", file=sys.stderr)
            return 2
        for k in LISTAS:
            e.setdefault(k, [])
        e.setdefault("avisos", [])
        e.setdefault("turnos", 0)
        e["session_id"] = a.session_id or e.get("session_id") or "manual"
        if a.reason:
            e["reason"] = a.reason
        p = write(a.root, e, a.fuente)
    else:
        p, _ = escribir_sesion(a.root, a.session_id, a.reason, a.transcript, a.fuente, a.enrich, a.ia)
    if p is None:                       # sin rastro del plugin: silencio (exit 0, sin stdout)
        return 0
    print(os.path.relpath(p, a.root))
    return 0


def cmd_latest(a):
    t = latest(a.root, a.n, a.max_lines)
    if t:
        print(t)
    return 0


def cmd_index(a):
    p = index(a.root)
    if p:
        print(os.path.relpath(p, a.root))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1].strip())
    sub = p.add_subparsers(dest="cmd", required=True)

    def comunes(sp):
        sp.add_argument("--root", default=os.environ.get("CLAUDE_PROJECT_DIR") or ".")

    sp = sub.add_parser("capture", help="añade el turno del usuario (payload UserPromptSubmit por stdin) al log crudo")
    sp.add_argument("--root", default=None, help="raíz del proyecto (default: CLAUDE_PROJECT_DIR, `cwd` del payload, .)")
    sp.set_defaults(fn=cmd_capture)

    sp = sub.add_parser("draft", help="borrador determinista (JSON)")
    comunes(sp)
    sp.add_argument("--session-id")
    sp.add_argument("--transcript")
    sp.add_argument("--reason")
    sp.add_argument("--enrich", help="JSON con resumen/decisiones/pendientes (fichero o -)")
    sp.set_defaults(fn=cmd_draft)

    sp = sub.add_parser("write", help="escribe/actualiza la entrada de la sesión")
    comunes(sp)
    sp.add_argument("--session-id", required=True)
    sp.add_argument("--transcript")
    sp.add_argument("--reason")
    sp.add_argument("--fuente", choices=("hook", "manual"), default="hook")
    sp.add_argument("--enrich")
    sp.add_argument("--draft", help="usar este JSON (de `draft`) en vez de recalcular")
    sp.add_argument("--ia", choices=("auto", "on", "off"), default="auto",
                    help="resumen por IA tras la entrada determinista: auto = solo con dev.json sesion.resumen: true")
    sp.set_defaults(fn=cmd_write)

    sp = sub.add_parser("latest", help="bloque compacto de la(s) última(s) entrada(s)")
    comunes(sp)
    sp.add_argument("--n", type=int, default=2)
    sp.add_argument("--max-lines", type=int, default=25)
    sp.set_defaults(fn=cmd_latest)

    sp = sub.add_parser("index", help="regenera journal/README.md")
    comunes(sp)
    sp.set_defaults(fn=cmd_index)

    sp = sub.add_parser("candidatas", help="patrones repetidos del journal → candidatas a lección (estado: propuesta)")
    comunes(sp)
    sp.add_argument("--min", type=int, default=CANDIDATA_MIN, help=f"entradas mínimas (sesiones distintas); default {CANDIDATA_MIN}")
    sp.add_argument("--iniciativa", help="solo entradas de esta iniciativa (slug)")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_candidatas)

    a = p.parse_args(argv)
    try:
        return a.fn(a)
    except Exception as e:  # noqa: BLE001 — la bitácora nunca bloquea una sesión
        print(f"journal: {e}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
