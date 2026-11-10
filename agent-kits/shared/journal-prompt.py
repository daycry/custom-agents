#!/usr/bin/env python3
"""Captura ligera del turno del usuario (hook UserPromptSubmit) en el log crudo de su sesión.

H-31 (T-14): el hook importaba `journal.py` entero (~3.000 líneas, ~1 s en Windows) para añadir una
línea. Este módulo es la fuente ÚNICA de la captura y de sus cerrojos; `journal.py` reexporta estos
nombres (`capture`, `_rotar`, `_cerrojo`, `_transcript_seguro`…) para replay, recover y sus tests.
Solo carga la biblioteca estándar, `journal-io.py`, `journal-capture.py` (política de la sesión) y
`redact.py`. Nunca stdout ni stderr, nunca exit distinto de 0: en UserPromptSubmit el stdout es
contexto y el exit 2 borra el prompt.
"""
import argparse
import contextlib
import datetime as _dt
import importlib.util
import json
import os
import sys
import time

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001

HERE = os.path.dirname(os.path.abspath(__file__))


def _load_module(name, filename):
    path = os.path.join(HERE, filename)
    if not os.path.isfile(path):
        return None
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:  # noqa: BLE001 — degradación: sin el módulo, sin captura
        return None


JIO = _load_module('journal_prompt_io', 'journal-io.py')
_politica = _load_module('journal_prompt_policy', 'journal-capture.py')
try:
    proyecto_con_plugin = _politica.proyecto_con_plugin
    _dev_sesion = _politica._dev_sesion
    _journal_activo = _politica._journal_activo
    log_path = _politica.log_path
    LOG_DIR_REL = _politica.LOG_DIR_REL
    LOG_PREFIX = _politica.LOG_PREFIX
    ENVELOPE_STR_MAX = _politica.ENVELOPE_STR_MAX
except AttributeError:   # paquete incompleto: sin la política de la sesión no se captura nada
    _politica = None
_redact = _load_module('journal_prompt_redact', 'redact.py')


def redactar(texto):
    """`redact.py` es la fuente única; sin él (paquete parcial) se usa el respaldo de journal.py."""
    if _redact is not None:
        return _redact.redactar(texto)
    return _load_module('journal_prompt_respaldo', 'journal.py').redactar(texto)


# --- log crudo del turno del usuario (hook UserPromptSubmit → `capture`; memory-retrieval T-11) ---
PRIVATE_TAG = "<private>"          # en cualquier parte del turno, sin distinguir mayúsculas → el log NO se toca
CAPTURA_MAX_CHARS = 4000           # tope por turno (un turno gigantesco no llena el disco)
LOG_MAX_BYTES = 256 * 1024         # tope por fichero: al superarlo se conservan los ÚLTIMOS turnos (½ del tope)
LOG_RETENCION_DIAS = 30            # purga de `session-prompts-*.log` más viejos (mtime) al capturar
LOG_GITIGNORE = "session-prompts-*"       # log y su `.lock`; se siembra en `.claude/.gitignore` del consumidor (revisión F4, Lente C gap 2)


def _transcripts_permitidos_root():
    """Directorio bajo el que Claude Code guarda las transcripciones reales: `$CLAUDE_CONFIG_DIR/projects`
    si la variable está definida, si no `~/.claude/projects` (gap 38 de la revisión intento 2: el
    basename-match por sí solo no bastaba)."""
    base = os.environ.get("CLAUDE_CONFIG_DIR")
    if base:
        return os.path.join(base, "projects")
    return os.path.join(os.path.expanduser("~"), ".claude", "projects")


def _transcript_seguro(path, session_id):
    """`transcript_path` solo se usa si es ruta absoluta, NO es un symlink, existe, termina en
    `.jsonl`, su `basename` es `<session_id>.jsonl` (así nombra Claude Code las transcripciones) Y
    cae (tras resolver symlinks) bajo el directorio de transcripciones permitido — gap 15/38 de la
    revisión (C2/K-1 · CWE-59/73/22/200): el basename-match por sí solo compara dos campos del
    MISMO envelope no confiable (un atacante controla ambos) y `os.path.isfile` sigue symlinks, así
    que un envelope plantado podía hacer que `replay` leyera (y volcara en un fichero versionado)
    el transcript de OTRO proyecto con solo nombrar el symlink como `<session_id>.jsonl`."""
    if not path or not session_id or not os.path.isabs(path) or not path.endswith(".jsonl"):
        return None
    if os.path.basename(path) != f"{session_id}.jsonl":
        return None
    try:
        if os.path.islink(path):        # gap 38: un symlink con el nombre correcto no debe colarse
            return None
    except OSError:
        return None
    permitido = _transcripts_permitidos_root()
    try:
        real, real_permitido = os.path.realpath(path), os.path.realpath(permitido)
        if os.path.commonpath([real, real_permitido]) != real_permitido:
            return None
    except (OSError, ValueError):
        return None
    return path if os.path.isfile(path) else None


def _asegurar_gitignore(dirpath):
    path = os.path.join(dirpath, '.gitignore')
    def add_rule(raw):
        actual = raw.decode('utf8', errors='replace')
        if LOG_GITIGNORE in actual.splitlines():return raw
        suffix = ('\n' if actual and not actual.endswith('\n') else '')
        suffix += '# custom-agents: raw session log, never commit\n' + LOG_GITIGNORE + '\n'
        return raw + suffix.encode('utf8')
    JIO.update(path, add_rule)


def _bloquear(fd):
    """Cerrojo exclusivo sobre el fd: `fcntl.flock` (POSIX) o `msvcrt.locking` no bloqueante en bucle corto
    (Windows). False si no se consigue: entonces se escribe sin cerrojo (degradación, no bloqueo)."""
    try:
        if os.name == "nt":
            import msvcrt
            for _ in range(150):                                # ≤ 3 s; el hook tiene 5
                try:
                    msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                    return True
                except OSError:
                    time.sleep(0.02)
            return False
        import fcntl
        fcntl.flock(fd, fcntl.LOCK_EX)
        return True
    except (OSError, ImportError):
        return False


def _desbloquear(fd):
    try:
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_UN)
    except (OSError, ImportError):
        pass


@contextlib.contextmanager
def _cerrojo(path):
    """Serializa los `capture` de una misma sesión (dos turnos encolados solapan sus hooks; el append sin cerrojo
    y la rotación leer-reescribir perdían un turno en silencio — Lente B gap 5) con `<log>.lock`. Nunca lanza."""
    fd = None
    try:
        lockpath = path + '.lock'
        JIO.directory(os.path.dirname(os.path.abspath(lockpath)))
        if os.path.lexists(lockpath):JIO.IO.file(lockpath)
        fd = os.open(lockpath, os.O_RDWR | os.O_CREAT | getattr(os, 'O_NOFOLLOW', 0), 0o600)
        info = os.fstat(fd)
        JIO.need(info.st_nlink == 1 and JIO.IO.file(lockpath)[:2] == (info.st_dev, info.st_ino), 'unsafe_journal_lock')
        _bloquear(fd)
    except OSError:
        pass
    try:
        yield
    finally:
        if fd is not None:
            _desbloquear(fd)
            try:
                os.close(fd)
            except OSError:
                pass


def _abrir_log(path):
    return JIO.append(path)


def _rotar(path):
    """Rotate only a guarded regular snapshot; preserve concurrent modifications."""
    try:
        JIO.IO.dirs(os.path.dirname(os.path.abspath(path)))
        if JIO.IO.file(path)[2] <= LOG_MAX_BYTES:return
        tail, identity = JIO.tail(path, LOG_MAX_BYTES // 2)
        newline = tail.find(b'\n')
        if newline == -1:return
        JIO.IO.write(path, tail[newline+1:], time.monotonic()+5, expected=identity,
                     mode=__import__('stat').S_IMODE(os.stat(path).st_mode))
    except (OSError, ValueError):
        pass


def _purgar_logs(dirpath, excepto=None, ahora=None):
    ahora = ahora or time.time()
    try:
        if not JIO.directory(dirpath):return
        nombres = os.listdir(dirpath)
    except (OSError, ValueError):
        return
    for fn in nombres:
        if not (fn.startswith(LOG_PREFIX) and fn.endswith((".log", ".lock"))):
            continue
        p = os.path.join(dirpath, fn)
        if excepto and os.path.abspath(p) in (os.path.abspath(excepto), os.path.abspath(excepto) + ".lock"):
            continue
        try:
            JIO.IO.dirs(os.path.dirname(os.path.abspath(p)))
            JIO.IO.file(p)
            if ahora - os.stat(p).st_mtime > LOG_RETENCION_DIAS * 86400:
                os.remove(p)
        except (OSError, ValueError):
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
    if not _journal_activo(root) or ses.get("captura") is False:
        return None
    texto = redactar(prompt.strip())
    if len(texto) > CAPTURA_MAX_CHARS:
        texto = texto[:CAPTURA_MAX_CHARS].rstrip() + " …[recortado]"
    d = os.path.join(root, LOG_DIR_REL)
    JIO.directory(d, create=True)
    _asegurar_gitignore(d)
    path = log_path(root, sid)
    rec = {"ts": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "prompt": texto}
    # Señal de inactividad para `recover` (huérfanas de Windows antes de 24 h): la ruta del transcript
    # SOLO si pasa `_transcript_seguro`. Vive en este log local no versionado; nunca llega a la entrada.
    tp = payload.get("transcript_path")
    if isinstance(tp, str) and len(tp) <= ENVELOPE_STR_MAX and _transcript_seguro(tp, sid):
        rec["transcript"] = tp
    with _cerrojo(path):
        with _abrir_log(path) as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        _rotar(path)
    _purgar_logs(d, excepto=path)
    return path


def main(argv=None):
    """Nunca stdout ni stderr, nunca exit ≠ 0 (mismo contrato que `journal.py capture`)."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root")
    try:
        args = parser.parse_args(argv)
        if _politica is None or JIO is None:
            return 0
        # Como `journal.py capture`: todo el payload, UTF-8 con reemplazo; `capture` recorta el turno a
        # CAPTURA_MAX_CHARS (revisión intento 1, B4: un tope de bytes descartaba el turno entero).
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace"))
        root = args.root or os.environ.get("CLAUDE_PROJECT_DIR") or (payload.get("cwd") if isinstance(payload, dict) else None) or "."
        if os.path.isdir(str(root)):
            capture(str(root), payload)
    except BaseException:  # noqa: BLE001 — el turno del usuario no se toca por nada de lo que pase aquí
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
