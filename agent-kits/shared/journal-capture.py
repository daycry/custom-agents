#!/usr/bin/env python3
"""Canonical durable SessionEnd capture, separate from deferred materialization.

Only stdlib and the shared atomic outbox are loaded at teardown. journal.py
reuses this policy and writer; replay/recover remain in the materializer.
"""
import argparse
import contextlib
import datetime as _dt
import hashlib
import importlib.util
import json
import ntpath
import os
import re
import sys

# Console streams and native payloads use UTF-8 on every platform (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

HERE = os.path.dirname(os.path.abspath(__file__))
LOG_DIR_REL = ".claude"
LOG_PREFIX = "session-prompts-"
_SID_RE = re.compile(r"[^A-Za-z0-9._-]")
_REASON_RE_SANEA = re.compile(r"[^a-z_]+")
SCHEMA_VERSION = 1
ENVELOPE_STR_MAX = 2000
SESSION_ID_MAX = 200
ENVELOPE_MAX_BYTES = 64 * 1024
PAYLOAD_MAX_CHARS = 64 * 1024
_OB = {"cargado": False, "mod": None}
_DIR_DEFAULT = os.path.join(".claude", "journal")
_QUEUE_MARKER = ".custom-agents-journal"
_CONTENIDO_DE_LA_COLA = frozenset(
    {"outbox", "processing", "done", "dead-letter", ".gitignore", ".replay.lock", ".claim.lock", _QUEUE_MARKER,
     ".durabilidad-degradada", ".permisos-degradados", ".reclamacion-degradada"})

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

def _schema_aceptados(version):
    """{version, version - 1} ∩ ≥ 1: al subir `SCHEMA_VERSION` a 2, la 1 sigue aceptándose durante
    esa versión (gap 17 de la revisión: con `SCHEMA_VERSION == 1` la rama N-1 era código muerto sin
    test que la ejercitara)."""
    return frozenset(v for v in (version, version - 1) if v >= 1)

def _outbox_mod():
    """`agent-kits/shared/outbox.py` cargado una vez (o `None` si no viaja junto a journal.py:
    entonces capture-end/replay degradan en silencio, nunca bloquean SessionEnd/SessionStart)."""
    if not _OB["cargado"]:
        _OB["cargado"], _OB["mod"] = True, _load_module("outbox", "outbox.py")
    return _OB["mod"]

def _dir_es_de_la_cola_o_vacio(dirpath):
    """True si `dirpath` no existe todavía, existe pero está vacío, o YA lleva el marcador de la
    cola Y todo su contenido son piezas conocidas de la cola (`outbox/`, `processing/`, `done/`,
    `dead-letter/`, `.gitignore`, `.replay.lock`, los sentinelas de degradación y el propio
    marcador). Gap 34 de la revisión intento 2: `sesion.journal.dir` con contención solo LÉXICA
    dejaba pasar `"."` o `"docs"` (rutas realmente contenidas en la raíz del proyecto, así que
    ninguna comprobación de escape las rechaza) y `_asegurar_gitignore_local` plantaba
    `.gitignore`/`chmod 0700` en la raíz o en `docs/` del proyecto consumidor. Gap 62 de la revisión
    intento 3: el marcador SOLO no bastaba — un repo con `journal.dir: "docs"` y
    `docs/.custom-agents-journal` VERSIONADO (por el motivo que fuera) hacía que el hook tratara
    `docs/` entero como cola aunque llevara `README.md` y el resto de la documentación del proyecto;
    ahora, con marcador, se exige ADEMÁS que no haya NINGÚN fichero ajeno."""
    if not os.path.isdir(dirpath):
        return True
    try:
        contenido = os.listdir(dirpath)
    except OSError:
        return False
    if not contenido:
        return True
    if _QUEUE_MARKER not in contenido:
        return False        # tiene contenido y ni siquiera lleva el marcador: no es (ni puede ser) nuestro
    return all(nombre in _CONTENIDO_DE_LA_COLA for nombre in contenido)

def _journal_queue_dir(root):
    """Carpeta de la cola de outbox: `.claude/journal` por defecto; `dev.json` →
    `{"sesion": {"journal": {"dir": "..."}}}` la puede mover (el booleano `sesion.journal` sigue
    valiendo para el opt-out, ver `_journal_activo`). Se rechaza (con aviso, usando el default) si
    `dir`:
      - es absoluto, o relativo a una UNIDAD de Windows (`"C:evil"` — `ntpath.splitdrive` detecta
        esto en cualquier SO, gap 34: la contención léxica anterior solo miraba `..`/absolutos
        POSIX);
      - sale de la raíz del proyecto tras resolver symlinks (`os.path.realpath` +
        `os.path.commonpath`: un symlink versionado `esc -> /fuera` pasaba la comprobación léxica
        de antes);
      - ya existe con CONTENIDO ajeno a la cola (gap 34: `"."`/`"docs"` están léxicamente
        contenidos y no son symlinks, pero mutar la raíz del proyecto o `docs/` con `chmod 0700` y
        un `.gitignore` con `*` es peligroso — se usa el default en vez de tocar un directorio que
        no es nuestro)."""
    jr = _dev_sesion(root).get("journal")
    d = jr.get("dir") if isinstance(jr, dict) else None
    if not (isinstance(d, str) and d.strip()):
        return os.path.join(root, _DIR_DEFAULT)
    d = d.strip()
    if os.path.isabs(d) or ntpath.splitdrive(d)[0]:
        print(f"journal: sesion.journal.dir {d!r} es absoluto o relativo a una unidad; se usa el "
              f"default {_DIR_DEFAULT}", file=sys.stderr)
        return os.path.join(root, _DIR_DEFAULT)
    candidato = os.path.join(root, d)
    real_root, real_cand = os.path.realpath(root), os.path.realpath(candidato)
    try:
        contenido = os.path.commonpath([real_root, real_cand]) == real_root
    except ValueError:              # unidades distintas en Windows: nunca contenido
        contenido = False
    if not contenido:
        print(f"journal: sesion.journal.dir {d!r} sale de la raíz del proyecto (symlink u otra "
              f"ruta); se usa el default {_DIR_DEFAULT}", file=sys.stderr)
        return os.path.join(root, _DIR_DEFAULT)
    if not _dir_es_de_la_cola_o_vacio(candidato):
        print(f"journal: sesion.journal.dir {d!r} ya existe con contenido ajeno a la cola; se usa "
              f"el default {_DIR_DEFAULT} (gap 34)", file=sys.stderr)
        return os.path.join(root, _DIR_DEFAULT)
    return candidato

def _journal_activo(root):
    """`dev.json` → `{"sesion": {"journal": false}}` (o el objeto `{"activo": false}`) apaga
    captura y replay; cualquier otra cosa (ausente, `true`, objeto sin `activo: false`) los deja
    activos — el booleano sigue valiendo (compatibilidad; gap 12 de la revisión: el objeto también
    tiene que poder apagar la captura)."""
    v = _dev_sesion(root).get("journal")
    if isinstance(v, dict):
        return v.get("activo") is not False
    return v is not False

def _plugin_version():
    """Version from this bundle's manifest, independent of the consumer project."""
    root = os.path.dirname(os.path.dirname(HERE))
    for relative in ((".claude-plugin", "plugin.json"), (".codex-plugin", "plugin.json"), ("package.json",)):
        try:
            with open(os.path.join(root, *relative), encoding="utf-8") as fh:
                manifest = json.load(fh)
            version = manifest.get("version") if isinstance(manifest, dict) else None
            if isinstance(version, str) and version.strip():
                return version
        except (OSError, ValueError):
            pass
    return "0.0.0"

def _hash_log_prompts(root, session_id):
    """sha256 del CONTENIDO ÍNTEGRO del log crudo de la sesión (`sha256("")` si no existe): la base
    de `event_id` (gap 28 de la revisión intento 2, reemplaza a `sequence`). `sequence` (nº de
    líneas) NO es monótono cuando el log rota (`_rotar`, `LOG_MAX_BYTES`): puede volver a un valor
    YA USADO tras rotar, y entonces `event_id` colisionaba con uno ya en `done/` — el cierre
    legítimo nunca se encolaba. El HASH del contenido cambia con cualquier turno nuevo o rotación,
    y es estable si nada cambió (CA-03 se mantiene: repetir la captura sin turnos nuevos entre
    medias no cambia el hash)."""
    return _log_snapshot(root, session_id)[0]


def _log_snapshot(root, session_id):
    """One physical read supplies both identity and sequence for the same snapshot.

    JSONL records use LF; Unicode separators inside a prompt are not records.
    """
    try:
        with open(log_path(root, session_id), "rb") as fh:
            data = fh.read()
    except OSError:
        data = b""
    sequence = data.count(b"\n") + int(bool(data) and not data.endswith(b"\n"))
    return hashlib.sha256(data).hexdigest(), sequence

def _event_id(session_id, reason, schema_version, log_hash):
    """`sha256(session_id·reason·schema_version·hash_del_log)[:16]`: determinista, sin texto de
    conversación — la clave de idempotencia de `outbox.escribir` (CA-03: el mismo evento capturado
    varias veces produce un único envelope lógico). `log_hash` (gap 28 de la revisión intento 2)
    sustituye a `sequence` (nº de líneas, NO monótono si el log rota) como lo que distingue dos
    cierres legítimos de la misma sesión: un turno nuevo, o una rotación, cambian el contenido del
    log y por tanto el hash, aunque el nº de líneas coincida con uno ya usado."""
    clave = "|".join(str(x) for x in (session_id, reason, schema_version, log_hash))
    return hashlib.sha256(clave.encode("utf-8")).hexdigest()[:16]

def _contar_lineas_log(root, session_id):
    """Nº de turnos ya capturados de la sesión (líneas del log crudo `.claude/session-prompts-<sid>.log`)
    en el momento del cierre; 0 si el log no existe. Puramente INFORMATIVO en el envelope
    (`sequence`) desde el gap 28 de la revisión intento 2: la idempotencia (`event_id`) ya no
    depende de este número (ver `_hash_log_prompts`), porque no es monótono cuando el log rota."""
    return _log_snapshot(root, session_id)[1]

def capture_end(root, payload):
    """Lo que corre en el teardown de SessionEnd (CA-01 de la spec): escribe un envelope atómico en
    la outbox y NADA MÁS — no abre `transcript_path` (referencia no confiable), no ejecuta git, no
    llama a IA, no usa red. Devuelve la ruta escrita, o `None` si no se escribe (payload sin
    `session_id`, `sesion.journal: false`/`{"activo": false}`, sin rastro del plugin, o
    `outbox.py` no disponible): nunca lanza, nunca bloquea el cierre de la sesión."""
    if not isinstance(payload, dict):
        return None
    sid = payload.get("session_id")
    if not isinstance(sid, str) or not sid.strip():
        return None
    sid = sid[:SESSION_ID_MAX]
    if not proyecto_con_plugin(root) or not _journal_activo(root):
        return None
    ob = _outbox_mod()
    if ob is None:
        return None
    reason_crudo = str(payload.get("reason") or "manual")
    reason = _REASON_RE_SANEA.sub("_", reason_crudo.lower())[:40] or "other"
    log_hash, sequence = _log_snapshot(root, sid)
    envelope = {
        "schema_version": SCHEMA_VERSION,
        "event_id": _event_id(sid, reason, SCHEMA_VERSION, log_hash),
        "session_id": sid,
        "hook_event_name": str(payload.get("hook_event_name") or "SessionEnd")[:64],
        "reason": reason,
        "cwd": str(payload.get("cwd") or "")[:ENVELOPE_STR_MAX],
        "transcript_path": str(payload.get("transcript_path") or "")[:ENVELOPE_STR_MAX],
        "captured_at": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "plugin_version": _plugin_version(),
        "sequence": sequence,
    }
    dir_ = _journal_queue_dir(root)
    _asegurar_gitignore_local(dir_)         # gap 9: nunca se cuela en `git status` del consumidor
    return ob.escribir(dir_, envelope["event_id"], envelope)

def _asegurar_gitignore_local(dirpath):
    """`.gitignore` + marcador de la cola (`_QUEUE_MARKER`, gap 34) DENTRO de la propia carpeta:
    funciona aunque `sesion.journal.dir` mueva la cola fuera de `.claude/` (gap 9 de la revisión:
    sin esto, los envelopes se cuelan en `git status` y en `ficheros_tocados`, y se pueden
    commitear). `_journal_queue_dir` ya garantiza que `dirpath` es seguro (contenido en la raíz,
    sin symlinks de escape, y de la cola o vacío) antes de llegar aquí, así que esta función no
    vuelve a comprobarlo: solo crea/marca. La llama también `replay()` (gap 41: creaba la carpeta y
    el cerrojo sin sembrar `.gitignore`)."""
    try:
        os.makedirs(dirpath, exist_ok=True)
        with contextlib.suppress(OSError):
            os.chmod(dirpath, 0o700)
        marker = os.path.join(dirpath, _QUEUE_MARKER)
        if not os.path.isfile(marker):
            open(marker, "w", encoding="utf-8").close()
        gi = os.path.join(dirpath, ".gitignore")
        if not os.path.isfile(gi):
            # Gap 61 de la revisión intento 3 (B-55): `!.gitignore` deshacía la ignorancia del PROPIO
            # `.gitignore`, así que `git status -uall` seguía viéndolo como `??` — el único fichero de
            # la cola que se colaba. Con solo `*` (sin excepción), la cola entera —incluido su propio
            # `.gitignore`— queda ignorada; no hace falta versionarlo para que git lo respete, porque
            # `_asegurar_gitignore_local` se encarga de recrearlo si faltara.
            with open(gi, "w", encoding="utf-8") as fh:
                fh.write("# custom-agents: outbox del journal, nunca versionar (session-end-durable-capture)\n*\n")
    except OSError:
        pass

def _sid_seguro(session_id):
    """`session_id` como trozo de nombre de fichero: nunca sale de `.claude/` (sin separadores)."""
    return _SID_RE.sub("_", str(session_id))[:80]

def log_path(root, session_id):
    return os.path.join(root, LOG_DIR_REL, f"{LOG_PREFIX}{_sid_seguro(session_id)}.log")

SCHEMA_ACEPTADOS = _schema_aceptados(SCHEMA_VERSION)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root")
    args = parser.parse_args(argv)
    try:
        raw = sys.stdin.read(PAYLOAD_MAX_CHARS + 1)
        if len(raw) > PAYLOAD_MAX_CHARS:
            print("journal: payload exceeds capture limit; use journal recover", file=sys.stderr)
            return 0
        payload = json.loads(raw)
        root = args.root or os.environ.get("CLAUDE_PROJECT_DIR") or (payload.get("cwd") if isinstance(payload, dict) else None) or "."
        if os.path.isdir(str(root)):
            capture_end(str(root), payload)
    except Exception:
        pass  # Informational: durable capture never blocks termination.
    return 0


if __name__ == "__main__":
    sys.exit(main())
