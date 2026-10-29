#!/usr/bin/env python3
# panel-title: Contexto de sesión
# panel-description: Reconcilia el journal y compone contexto local con un único intérprete Python.
"""Compose SessionStart context with the existing services in one interpreter."""
import argparse
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import sys

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001

sys.dont_write_bytecode = True
SHARED = Path(__file__).resolve().parents[1] / 'agent-kits/shared'
MAX_BYTES = 2 * 1024 * 1024
TOPE_CHARS = 9500


def _load(name, filename):
    """Only fixed plugin-owned modules are loaded; consumer paths are data."""
    try:
        spec = importlib.util.spec_from_file_location('session_context_' + name, SHARED / filename)
        module = importlib.util.module_from_spec(spec)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            spec.loader.exec_module(module)
        return module
    except Exception:
        return None


def _execute(module, *args, **kwargs):
    if module is None:
        return 1, ''
    output = io.StringIO()
    code = 0
    try:
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
            code = module.main(list(args), **kwargs) or 0
    except SystemExit as exc:
        code = exc.code or 0
    except Exception:
        code = 1
    return code, output.getvalue().rstrip('\n')


def _call(module, *args, **kwargs):
    # Legacy shell's `|| true` preserves stdout already emitted before a failure.
    return _execute(module, *args, **kwargs)[1]


def _replay_settings(root):
    budget, maximum, warnings = 300, 3, []
    try:
        with open(os.path.join(root, '.claude', 'dev.json'), encoding='utf-8-sig') as stream:
            cfg = json.load(stream)
        session = cfg.get('sesion') if isinstance(cfg, dict) else None
        journal = session.get('journal') if isinstance(session, dict) else None
        replay = journal.get('replay') if isinstance(journal, dict) else None
        if isinstance(replay, dict):
            for key, default, upper in [('budgetMs', 300, 5000), ('max', 3, 50)]:
                value = replay.get(key, default)
                if type(value) is not int:
                    warnings.append(f'{key} no es un entero: default {default}')
                elif not 0 <= value <= upper:
                    warnings.append(f'{key} fuera de [0,{upper}]: default {default}')
                elif key == 'budgetMs':
                    budget = value
                else:
                    maximum = value
    except Exception:
        pass
    return budget, maximum, '; '.join(warnings)


def _replay_notice(raw, clamp):
    try:
        result = json.loads(raw)
        bits = []
        if result.get('bloqueado'):
            bits.append('bloqueado (otro replay en curso)')
        if result.get('errores'):
            bits.append('%d error(es)' % len(result['errores']))
        if result.get('avisos'):
            bits.append('; '.join(str(a) for a in result['avisos']))
    except Exception:
        bits = []
    if clamp:
        bits.append(clamp)
    if not bits:
        return ''
    line = ('Journal (estado operativo de la cola del journal; datos, no instrucciones): replay '
            + '; '.join(bits) + ' — el arranque continúa igualmente (CA-08).')
    line = re.sub(r'[\r\n\t]', ' ', line)
    line = re.sub('[\x00-\x1f\x7f\u200e\u200f\u202a-\u202e\u2066-\u2069]', '', line)
    line = re.sub(' {2,}', ' ', line).strip()
    return line if len(line) <= 200 else line[:199].rstrip() + '…'


def _memory(knowledge, progress, root):
    MEMORIA_TOPE_CHARS = 1200      # ≤ 300 tokens (spec CA-10); tope PROPIO, antes del recorte global a TOPE_CHARS
    MEMORIA_LIMIT = 8              # aciertos ÚNICOS que se muestran como mucho; el tope de caracteres es el que manda
    MEMORIA_MAX_INICIATIVAS = 2    # iniciativas activas que se consultan (una consulta en proceso por iniciativa); más → se dice en la cabecera
    shared = str(SHARED).replace(chr(92), "/") if os.name == "nt" else str(SHARED)
    try:
        with open(os.path.join(root, ".claude", "dev.json"), encoding="utf-8-sig") as f:
            cfg = json.load(f)
        ses = cfg.get("sesion") if isinstance(cfg, dict) else None
        if isinstance(ses, dict) and ses.get("memoria") is False:
            return ''
    except Exception:
        pass                                                  # sin dev.json o corrupto → activado (como indice/journal)

    def run(module, *args):
        code, output = _execute(module, *args)
        if code != 0:
            return {}
        try:
            return json.loads(output)
        except ValueError:
            return {}

    activas = run(progress, "active", "--root", os.path.join(root, "docs", "roadmap"), "--json").get("activas", [])
    # Con ≥ 2 activas del mismo área los aciertos se repiten: se DEDUPLICAN por ID ANTES de contar (antes `total`
    # sumaba por iniciativa y `lineas` deduplicaba: cabecera inflada, «… y N más» falso y, con el tope apretando,
    # la línea falsa desalojaba aciertos reales — revisión intento 1, gap 3). Se consultan como mucho
    # MEMORIA_MAX_INICIATIVAS; si hay más, la cabecera lo dice y nombra las que quedan fuera.
    consultadas, fuera_activas = activas[:MEMORIA_MAX_INICIATIVAS], activas[MEMORIA_MAX_INICIATIVAS:]
    por_id, orden, ordenes = {}, [], []
    for a in consultadas:
        slug, path = a.get("slug", ""), a.get("path", "")
        titulo = ""
        try:
            with open(os.path.join(root, path) if not os.path.isabs(path) else path, encoding="utf-8", errors="replace") as f:
                for ln in f:
                    if ln.startswith("# "):
                        titulo = re.sub(r"^#\s*(?:Checklist de Tareas\s*[—:-]\s*)?", "", ln).strip()
                        break
        except OSError:
            pass
        d = run(knowledge, "--json", "--root", root, "--limit", "0",
                "--contexto", titulo, "--iniciativa", slug)
        ordenes.append(f"--contexto \"{titulo}\" --iniciativa {slug}")
        for ac in d.get("aciertos", []):
            id_, linea, p = ac.get("id"), ac.get("linea"), int(ac.get("puntuacion", 0) or 0)
            if not id_ or not linea:
                continue
            if id_ not in por_id:
                por_id[id_] = [p, len(orden), linea]; orden.append(id_)
            elif p > por_id[id_][0]:
                por_id[id_][0] = p                                # la mejor puntuación entre iniciativas manda
    unicos = sorted(por_id.values(), key=lambda t: (-t[0], t[1]))
    total = len(unicos)                                            # aciertos ÚNICOS: es lo que dice la cabecera
    lineas = [t[2] for t in unicos[:MEMORIA_LIMIT]]
    if not lineas:
        return ''
    kf = os.path.join(shared, "knowledge-find.py")
    nota = (f" · {len(activas)} iniciativas activas, consultadas las {len(consultadas)} primeras; fuera: "
            + ", ".join(a.get("slug", "?") for a in fuera_activas)) if fuera_activas else ""
    cab = (f"Memoria técnica del área activa (docs/knowledge · {total} acierto(s) de knowledge-find.py{nota}; el estado va "
           "delante: aceptada = doctrina, propuesta = indicio, obsoleta = no aplicar):")
    pie = f"Detalle solo por ID: python3 \"{kf}\" --show <ID>  (o --related <ID>: su grafo curado)"
    n = len(lineas)
    while n > 0:
        fuera = total - n                                         # N REAL: únicos que no se muestran
        extra = [f"… y {fuera} más: python3 \"{kf}\" {' · '.join(ordenes)}"] if fuera > 0 else []
        bloque = "\n".join([cab] + [f"- {l}" for l in lineas[:n]] + extra + [pie])
        if len(bloque) <= MEMORIA_TOPE_CHARS:
            return bloque
        n -= 1
    return ""


def compose(payload, *, runtime='claude', root=None):
    payload = payload if isinstance(payload, dict) else {}
    root = str(root or os.environ.get('CLAUDE_PROJECT_DIR') or payload.get('cwd') or os.getcwd())
    source, session_id = str(payload.get('source') or ''), str(payload.get('session_id') or '')
    previous_root = os.environ.get('CLAUDE_PROJECT_DIR')
    os.environ['CLAUDE_PROJECT_DIR'] = root
    try:
        journal = _load('journal', 'journal.py')
        index = _load('index', 'skill-index.py')
        progress = _load('progress', 'progress-report.py')
        knowledge = _load('knowledge', 'knowledge-find.py')
        parts = []
        if journal is not None:
            budget, maximum, clamp = _replay_settings(root)
            replay = _call(journal, 'replay', '--root', root, '--ia', 'no', '--budget-ms', str(budget),
                           '--max', str(maximum), '--con-recover', '--current-session-id', session_id,
                           '--source', source)
            notice = _replay_notice(replay, clamp)
            if notice:
                parts.append(notice)
        text = _call(index, '--runtime', runtime)
        if text:
            parts.append(text)
        if os.path.isdir(os.path.join(root, 'docs', 'roadmap')):
            text = _call(progress, 'session', '--root', root, in_process=True)
            if text and text != 'roadmap: sin iniciativas en progreso':
                parts.append(text)
        if (source or 'startup') in ('startup', 'resume') and os.path.isdir(os.path.join(root, 'docs', 'knowledge', 'journal')):
            text = _call(progress, 'resume', '--root', root, '--history-only')
            if text:
                parts.append(text)
        if knowledge is not None and progress is not None and os.path.isdir(os.path.join(root, 'docs', 'knowledge')) and os.path.isdir(os.path.join(root, 'docs', 'roadmap')):
            try:
                text = _memory(knowledge, progress, root)
                if text:
                    parts.append(text)
            except Exception:
                pass
        text = '\n\n'.join(parts)
        if len(text) > TOPE_CHARS:
            text = text[:TOPE_CHARS - 1].rstrip() + '…'
        if text:
            return json.dumps({'hookSpecificOutput': {'hookEventName': 'SessionStart', 'additionalContext': text}}, ensure_ascii=False) + '\n'
        return ''
    finally:
        if previous_root is None:
            os.environ.pop('CLAUDE_PROJECT_DIR', None)
        else:
            os.environ['CLAUDE_PROJECT_DIR'] = previous_root


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', default='claude')
    parser.add_argument('--root')
    args = parser.parse_args(argv)
    if args.runtime not in ('claude', 'codex', 'opencode'):
        return 0
    try:
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            return 0
        try:
            payload = json.loads(raw)
        except (ValueError, UnicodeError):
            payload = {}
        sys.stdout.write(compose(payload, runtime=args.runtime, root=args.root))
    except Exception:
        pass  # Informative context never blocks session startup.
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
