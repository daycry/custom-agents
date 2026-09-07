#!/usr/bin/env python3
"""Suite de SHELL de los hooks (`hooks/*.sh`) y la statusline (debt-cleanup T-06).

Hasta hoy la evidencia de los hooks era la simulación manual de stdin anotada en los ledgers
(live-visibility, deterministic-guardrails). Aquí pytest lanza cada hook con `bash` sobre un
PROYECTO TEMPORAL (ledger de fixture copiado de docs/roadmap/ del repo, puesto en `en-progreso`) con
un entorno controlado (CLAUDE_PLUGIN_ROOT, CLAUDE_PROJECT_DIR, HOME, PATH) y afirma:
  - el JSON de salida sigue el contrato oficial (`systemMessage` / `hookSpecificOutput`);
  - el debounce de progress-line (2.ª idéntica → vacío) y su ATOMICIDAD con 6 invocaciones
    concurrentes (T-01a): con `flock` exactamente UNA systemMessage; sin `flock` la aserción
    honesta es «≥ 1 y nunca ninguna» (el rename es atómico; dos lectores pueden ver el estado viejo);
  - la degradación sin `python3` (guardrail: aviso una vez, nunca bloqueo);
  - `exit 0` SIEMPRE, también con stdin vacío.
Se salta entera si no hay `bash`. Ejecutar: python3 -m pytest -q tests/test_hooks_shell.py
(el bucle de la CI también la ejecuta como script: `python tests/test_hooks_shell.py`).
"""
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOKS = os.path.join(ROOT, "hooks")
STATUSLINE = os.path.join(ROOT, "statusline", "roadmap-statusline.sh")
LEDGER_FUENTE = os.path.join(ROOT, "docs", "roadmap", "2026-09-02-adversarial-review", "tasks.md")

try:
    import pytest
except ImportError:  # el bucle de la CI ejecuta el fichero como script; sin pytest solo informa
    pytest = None

BASH = shutil.which("bash")
if pytest is not None:
    pytestmark = pytest.mark.skipif(BASH is None, reason="sin bash en PATH: la suite de shell no aplica")


# ------------------------------------------------------------------ helpers ----

def proyecto(tmp_path, activa=True, slug="2026-01-01-demo"):
    """Proyecto temporal con un ledger de fixture (copia real del repo) en-progreso o completado."""
    proj = tmp_path / "proj"
    led = proj / "docs" / "roadmap" / slug / "tasks.md"
    led.parent.mkdir(parents=True)
    text = open(LEDGER_FUENTE, encoding="utf-8").read()
    if activa:
        # frontmatter + tabla de cabecera a en-progreso y una tarea abierta → iniciativa ACTIVA
        text = text.replace("estado: completado", "estado: en-progreso", 1)
        text = text.replace("| **Estado** | completado |", "| **Estado** | en-progreso |", 1)
        text = text.replace("- **Estado**: completado\n- **Tiempo humano**: est. 0,9h", "- **Estado**: en-progreso\n- **Tiempo humano**: est. 0,9h", 1)
    led.write_text(text, encoding="utf-8")
    (proj / ".claude").mkdir()
    return proj, led


def env_de(proj, tmp_path, sin_python=False, plugin_root=ROOT):
    """Entorno mínimo y controlado. `sin_python` → PATH con solo bash/coreutils (sin python3)."""
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    path = os.environ.get("PATH", "/usr/bin:/bin")
    if sin_python:
        bindir = tmp_path / "bin"
        bindir.mkdir(exist_ok=True)
        for tool in ("bash", "cat", "mkdir", "printf", "find", "head", "grep", "sed", "rm", "mv", "mktemp", "flock", "dirname"):
            src = shutil.which(tool)
            if src:
                dst = bindir / tool
                if not dst.exists():
                    os.symlink(src, dst)
        path = str(bindir)
    return {"CLAUDE_PLUGIN_ROOT": str(plugin_root), "CLAUDE_PROJECT_DIR": str(proj),
            "HOME": str(home), "PATH": path, "LC_ALL": "C.UTF-8", "LANG": "C.UTF-8"}


def hook(nombre, payload, env, cwd=None):
    """Lanza hooks/<nombre> con el payload por stdin. Devuelve (rc, stdout, stderr)."""
    script = STATUSLINE if nombre == "statusline" else os.path.join(HOOKS, nombre)
    data = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
    r = subprocess.run([BASH, script], input=data, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env,
                       cwd=cwd or env["CLAUDE_PROJECT_DIR"], timeout=60)
    return r.returncode, r.stdout, r.stderr


def post_tool(path):
    return {"tool_name": "Edit", "tool_input": {"file_path": path, "old_string": "a", "new_string": "b"},
            "tool_response": {"filePath": path}}


def un_json(stdout):
    lineas = [l for l in stdout.splitlines() if l.strip()]
    assert len(lineas) == 1, f"esperaba UN objeto JSON en stdout, hubo {len(lineas)}: {stdout!r}"
    return json.loads(lineas[0])


# --------------------------------------------------------------- progress-line ----

def test_progress_line_emite_system_message_json(tmp_path):
    proj, led = proyecto(tmp_path)
    rc, out, _ = hook("progress-line.sh", post_tool(str(led)), env_de(proj, tmp_path))
    assert rc == 0
    msg = un_json(out)["systemMessage"]
    assert msg.startswith("📋 demo") and "T-03/4" in msg and "IA est." in msg, msg
    assert (proj / ".claude" / ".progress-last").read_text(encoding="utf-8") == msg


def test_progress_line_debounce_segunda_identica_vacia(tmp_path):
    proj, led = proyecto(tmp_path)
    env = env_de(proj, tmp_path)
    rc1, out1, _ = hook("progress-line.sh", post_tool(str(led)), env)
    rc2, out2, _ = hook("progress-line.sh", post_tool(str(led)), env)
    assert rc1 == 0 and rc2 == 0
    assert out1.strip() and out2 == "", (out1, out2)
    # cambia el estado del ledger → vuelve a emitir
    led.write_text(led.read_text(encoding="utf-8").replace("- **Estado**: en-progreso", "- **Estado**: completado", 1), encoding="utf-8")
    rc3, out3, _ = hook("progress-line.sh", post_tool(str(led)), env)
    assert rc3 == 0 and out3.strip() and out3 != out1


def test_progress_line_ruta_windows_con_backslashes(tmp_path):
    proj, led = proyecto(tmp_path)
    win = str(led).replace("/", "\\")
    rc, out, _ = hook("progress-line.sh", post_tool(win), env_de(proj, tmp_path))
    assert rc == 0 and "systemMessage" in un_json(out)


def test_progress_line_multiedit_edits_lista(tmp_path):
    proj, led = proyecto(tmp_path)
    payload = {"tool_name": "MultiEdit", "tool_input": {"file_path": str(proj / "src" / "a.py"),
                                                        "edits": [{"file_path": str(led), "old_string": "a", "new_string": "b"}]}}
    rc, out, _ = hook("progress-line.sh", payload, env_de(proj, tmp_path))
    assert rc == 0 and "systemMessage" in un_json(out)


def test_progress_line_stdin_vacio_y_fichero_ajeno_exit_0_vacio(tmp_path):
    proj, _ = proyecto(tmp_path)
    env = env_de(proj, tmp_path)
    assert hook("progress-line.sh", "", env) == (0, "", "")
    rc, out, _ = hook("progress-line.sh", post_tool(str(proj / "src" / "app.py")), env)
    assert (rc, out) == (0, "")


def test_progress_line_seis_concurrentes_debounce_atomico(tmp_path):
    """T-01a. Con `flock`: exactamente UNA systemMessage (sección crítica serializada). Sin `flock`
    (macOS sin coreutils): el rename sigue siendo atómico pero dos lectores pueden ver el estado
    viejo a la vez → aserción honesta: al menos una, nunca cero, y el fichero de estado íntegro."""
    proj, led = proyecto(tmp_path)
    env = env_de(proj, tmp_path)
    payload = post_tool(str(led))
    with ThreadPoolExecutor(max_workers=6) as ex:
        res = list(ex.map(lambda _: hook("progress-line.sh", payload, env), range(6)))
    assert all(rc == 0 for rc, _, _ in res)
    emitidas = [un_json(out)["systemMessage"] for _, out, _ in res if out.strip()]
    if shutil.which("flock"):
        assert len(emitidas) == 1, f"con flock debe emitirse exactamente 1, fueron {len(emitidas)}"
    else:
        assert 1 <= len(emitidas) <= 6 and len(set(emitidas)) == 1
    assert (proj / ".claude" / ".progress-last").read_text(encoding="utf-8") == emitidas[0]
    # sin temporales huérfanos del rename
    assert not [f for f in os.listdir(proj / ".claude") if f.startswith(".progress-last.") and f != ".progress-last.lock"]


def test_progress_line_sin_flock_degrada_a_rename_atomico(tmp_path):
    """Sin `flock` en PATH el hook sigue funcionando (1.ª emite, 2.ª idéntica calla) y no crea el lock."""
    proj, led = proyecto(tmp_path)
    env = env_de(proj, tmp_path, sin_python=True)
    os.unlink(tmp_path / "bin" / "flock") if (tmp_path / "bin" / "flock").exists() else None
    os.symlink(sys.executable, tmp_path / "bin" / "python3")   # con python3 pero sin flock
    rc1, out1, _ = hook("progress-line.sh", post_tool(str(led)), env)
    rc2, out2, _ = hook("progress-line.sh", post_tool(str(led)), env)
    assert rc1 == 0 and "systemMessage" in un_json(out1)
    assert (rc2, out2) == (0, "")
    assert not (proj / ".claude" / ".progress-last.lock").exists()


# ----------------------------------------------------------- subagent-progress ----

def test_subagent_progress_con_activa_emite_system_message(tmp_path):
    proj, _ = proyecto(tmp_path)
    rc, out, _ = hook("subagent-progress.sh", {"hook_event_name": "SubagentStop", "agent_type": "implementer"}, env_de(proj, tmp_path))
    assert rc == 0
    assert "demo" in un_json(out)["systemMessage"]


def test_subagent_progress_sin_activas_vacio(tmp_path):
    proj, _ = proyecto(tmp_path, activa=False)
    assert hook("subagent-progress.sh", {"hook_event_name": "SubagentStop"}, env_de(proj, tmp_path)) == (0, "", "")


# ------------------------------------------------------------- session-context ----

def test_session_context_con_activa_additional_context_anidado(tmp_path):
    proj, _ = proyecto(tmp_path)
    rc, out, _ = hook("session-context.sh", {"hook_event_name": "SessionStart", "source": "resume"}, env_de(proj, tmp_path))
    assert rc == 0
    d = un_json(out)
    assert set(d) == {"hookSpecificOutput"}                     # additionalContext SOLO anidado
    hso = d["hookSpecificOutput"]
    assert hso["hookEventName"] == "SessionStart" and "demo" in hso["additionalContext"]


def test_session_context_startup_indice_mas_roadmap_bajo_el_tope(tmp_path):
    """T-02 activation-reliability: en `startup` el contexto lleva el ÍNDICE de piezas (3 bloques) y,
    detrás, el bloque del roadmap; total < 10.000 caracteres; se escribe la caché del índice."""
    proj, _ = proyecto(tmp_path)
    rc, out, _ = hook("session-context.sh", {"hook_event_name": "SessionStart", "source": "startup"}, env_de(proj, tmp_path))
    assert rc == 0
    ctx = un_json(out)["hookSpecificOutput"]["additionalContext"]
    assert ctx.startswith("Plugin custom-agents") and "Comandos:" in ctx and "Skills:" in ctx and "Agentes:" in ctx
    assert "/dev-cycle" in ctx and "quick-implement" in ctx and "implementer" in ctx
    assert ctx.index("Agentes:") < ctx.index("demo")            # índice primero, roadmap después
    assert len(ctx) < 10_000
    assert (proj / ".claude" / ".skill-index.cache").read_text(encoding="utf-8").startswith("# skill-index ")
    # `compact` también reinyecta el índice (la compactación resume la conversación; guía oficial)
    rc, out, _ = hook("session-context.sh", {"hook_event_name": "SessionStart", "source": "compact"}, env_de(proj, tmp_path))
    assert rc == 0 and "Comandos:" in un_json(out)["hookSpecificOutput"]["additionalContext"]


def test_session_context_indice_false_solo_roadmap(tmp_path):
    proj, _ = proyecto(tmp_path)
    (proj / ".claude" / "dev.json").write_text('{"sesion": {"indice": false}}', encoding="utf-8")
    rc, out, _ = hook("session-context.sh", {"hook_event_name": "SessionStart", "source": "startup"}, env_de(proj, tmp_path))
    assert rc == 0
    ctx = un_json(out)["hookSpecificOutput"]["additionalContext"]
    assert "Comandos:" not in ctx and "demo" in ctx
    assert not (proj / ".claude" / ".skill-index.cache").exists()


def test_session_context_sin_activas_solo_indice(tmp_path):
    proj, _ = proyecto(tmp_path, activa=False)
    rc, out, _ = hook("session-context.sh", {"hook_event_name": "SessionStart", "source": "startup"}, env_de(proj, tmp_path))
    assert rc == 0
    ctx = un_json(out)["hookSpecificOutput"]["additionalContext"]
    assert "Comandos:" in ctx and "demo" not in ctx and "Ledger canónico" not in ctx


def test_session_context_sin_activas_e_indice_off_vacio(tmp_path):
    proj, _ = proyecto(tmp_path, activa=False)
    (proj / ".claude" / "dev.json").write_text('{"sesion": {"indice": false}}', encoding="utf-8")
    assert hook("session-context.sh", {"hook_event_name": "SessionStart", "source": "startup"}, env_de(proj, tmp_path)) == (0, "", "")


def test_session_context_sin_python3_silencio(tmp_path):
    proj, _ = proyecto(tmp_path)
    assert hook("session-context.sh", {"hook_event_name": "SessionStart", "source": "startup"}, env_de(proj, tmp_path, sin_python=True)) == (0, "", "")


# ------------------------------------------------------------- session-journal ----

def session_end(proj, sid="s1", reason="other"):
    return {"hook_event_name": "SessionEnd", "session_id": sid, "reason": reason, "cwd": str(proj),
            "transcript_path": str(proj / "no-existe.jsonl")}


def entradas_journal(proj):
    d = proj / "docs" / "knowledge" / "journal"
    return sorted(f for f in os.listdir(d) if f != "README.md") if d.is_dir() else []


def test_session_journal_escribe_entrada_y_es_idempotente_por_session_id(tmp_path):
    """memory-health T-01: SessionEnd (contrato oficial 2026-09-03: session_id/reason/cwd; salida
    ignorada) → UNA entrada en docs/knowledge/journal/; el mismo session_id ACTUALIZA, otro añade."""
    proj, _ = proyecto(tmp_path)
    env = env_de(proj, tmp_path)
    assert hook("session-journal.sh", session_end(proj), env) == (0, "", "")      # stdout se ignora: vacío
    assert len(entradas_journal(proj)) == 1
    texto = (proj / "docs" / "knowledge" / "journal" / entradas_journal(proj)[0]).read_text(encoding="utf-8")
    assert 'session_id: "s1"' in texto and "iniciativa: demo" in texto and "reason: other" in texto
    assert hook("session-journal.sh", session_end(proj), env)[0] == 0
    assert len(entradas_journal(proj)) == 1                                         # actualizada, no duplicada
    assert hook("session-journal.sh", session_end(proj, sid="s2", reason="clear"), env)[0] == 0
    assert len(entradas_journal(proj)) == 2
    assert (proj / "docs" / "knowledge" / "journal" / "README.md").read_text(encoding="utf-8").count("| demo |") == 2


def test_session_journal_stdin_vacio_sin_session_id_opt_out_y_sin_python3(tmp_path):
    proj, _ = proyecto(tmp_path)
    env = env_de(proj, tmp_path)
    assert hook("session-journal.sh", "", env) == (0, "", "")
    assert hook("session-journal.sh", {"hook_event_name": "SessionEnd", "reason": "other"}, env) == (0, "", "")
    (proj / ".claude" / "dev.json").write_text('{"sesion": {"journal": false}}', encoding="utf-8")
    assert hook("session-journal.sh", session_end(proj), env) == (0, "", "")
    assert entradas_journal(proj) == []                                             # nada escrito en los 3 casos
    (proj / ".claude" / "dev.json").unlink()
    assert hook("session-journal.sh", session_end(proj), env_de(proj, tmp_path, sin_python=True)) == (0, "", "")
    assert entradas_journal(proj) == []


def test_session_journal_repo_ajeno_sin_rastro_del_plugin_no_siembra_nada(tmp_path):
    """T-fix1 (I1): repo temporal con solo a.txt (sin docs/roadmap, docs/knowledge ni .claude/dev.json)
    → el hook sale en silencio y NO aparece docs/knowledge/journal/."""
    ajeno = tmp_path / "ajeno"
    ajeno.mkdir()
    (ajeno / "a.txt").write_text("x", encoding="utf-8")
    env = env_de(ajeno, tmp_path)
    assert hook("session-journal.sh", session_end(ajeno), env) == (0, "", "")
    assert sorted(os.listdir(ajeno)) == ["a.txt"]
    # con .claude/dev.json (rastro del plugin) sí escribe, con slug `sesion` al no haber iniciativa
    (ajeno / ".claude").mkdir()
    (ajeno / ".claude" / "dev.json").write_text("{}", encoding="utf-8")
    assert hook("session-journal.sh", session_end(ajeno), env) == (0, "", "")
    assert entradas_journal(ajeno) and entradas_journal(ajeno)[0].endswith("-sesion.md")


def test_session_context_reinyecta_journal_en_resume_no_en_compact(tmp_path):
    proj, _ = proyecto(tmp_path)
    env = env_de(proj, tmp_path)
    hook("session-journal.sh", session_end(proj), env)
    for src in ("startup", "resume"):
        rc, out, _ = hook("session-context.sh", {"hook_event_name": "SessionStart", "source": src}, env)
        assert rc == 0
        ctx = un_json(out)["hookSpecificOutput"]["additionalContext"]
        assert "Journal de sesión" in ctx and "· demo ·" in ctx, src
        bloque = ctx[ctx.index("Journal de sesión"):]
        assert len(bloque.splitlines()) <= 25 and len(ctx) < 10_000
        assert ctx.index("Ledger canónico") < ctx.index("Journal de sesión")        # roadmap antes, journal después
    rc, out, _ = hook("session-context.sh", {"hook_event_name": "SessionStart", "source": "compact"}, env)
    assert rc == 0 and "Journal de sesión" not in un_json(out)["hookSpecificOutput"]["additionalContext"]


# ------------------------------------------- session-context · memoria del área activa (T-06) ----

def _knowledge(proj, n_extra=0):
    """`docs/knowledge/` mínimo con DOS áreas: una que casa con la iniciativa activa del fixture
    («adversarial-review» → área «Revisión adversarial / lentes») y otra que no (estimación)."""
    kn = proj / "docs" / "knowledge"
    (kn / "adr").mkdir(parents=True)
    (kn / "lessons").mkdir()
    filas = []
    (kn / "adr" / "ADR-001-lentes-en-paralelo.md").write_text(
        "---\nid: ADR-001\ntitulo: Las lentes se despachan en paralelo\nestado: aceptada (validada: usuario, 2026-01-02)\n"
        "fecha: 2026-01-02\n---\n\n# ADR-001\n\nx\n", encoding="utf-8")
    filas.append("| [`adr/ADR-001-lentes-en-paralelo.md`](adr/ADR-001-lentes-en-paralelo.md) — las lentes se despachan en paralelo "
                 "| ADR-001 | ADR | Revisión adversarial / lentes | aceptada (validada: usuario, 2026-01-02) | `2026-01-02-otra/tasks.md` |")
    (kn / "lessons" / "LES-001-evaluator-revision-cara.md").write_text(
        "---\nid: LES-001\ntipo: leccion\narea: Estimación / calibración\nestado: aceptada (validada: usuario, 2026-01-03)\n"
        "fuente: 2026-01-01-estimacion/retro.md\n---\n\n## evaluator\n\n- El coste está en la revisión.\n", encoding="utf-8")
    filas.append("| [`lessons/LES-001-evaluator-revision-cara.md`](lessons/LES-001-evaluator-revision-cara.md) — el coste está en la revisión "
                 "| LES-001 | Lección | Estimación / calibración | aceptada (validada: usuario, 2026-01-03) | `2026-01-01-estimacion/retro.md` |")
    for n in range(2, 2 + n_extra):
        fn = f"ADR-{n:03d}-lente-numero-{n}-con-un-nombre-de-fichero-deliberadamente-largo.md"
        (kn / "adr" / fn).write_text(f"---\nid: ADR-{n:03d}\ntitulo: Lente número {n} con un titular largo para llenar la línea\n"
                                     f"estado: aceptada (validada: usuario, 2026-01-02)\nfecha: 2026-01-02\n---\n\n# ADR-{n:03d}\n\nx\n",
                                     encoding="utf-8")
        filas.append(f"| [`adr/{fn}`](adr/{fn}) — lente número {n} con un titular largo para llenar la línea "
                     f"| ADR-{n:03d} | ADR | Revisión adversarial / lentes | aceptada (validada: usuario, 2026-01-02) | `x/tasks.md` |")
    (kn / "README.md").write_text("# índice\n\n| Entrada | ID | Tipo | Área | Estado | Fuente |\n|---|---|---|---|---|---|\n"
                                  + "\n".join(filas) + "\n", encoding="utf-8")
    return kn


def _ctx(out):
    return un_json(out)["hookSpecificOutput"]["additionalContext"]


def _bloque_memoria(ctx):
    if "Memoria técnica" not in ctx:
        return ""
    i = ctx.index("Memoria técnica")
    i = ctx.rfind("\n", 0, i) + 1
    return ctx[i:]


def test_session_context_inyecta_la_memoria_del_area_activa_bajo_su_tope(tmp_path):
    """memory-retrieval T-06 (spec CA-10): con iniciativa activa y `docs/knowledge/`, el contexto trae los
    aciertos del ÁREA de la iniciativa (≤ 1.200 caracteres), detrás del índice y del roadmap; total ≤ 9.500."""
    proj, _ = proyecto(tmp_path)
    _knowledge(proj)
    env = env_de(proj, tmp_path)
    for src in ("startup", "resume", "compact"):
        rc, out, err = hook("session-context.sh", {"hook_event_name": "SessionStart", "source": src}, env)
        assert rc == 0, err
        ctx = _ctx(out)
        bloque = _bloque_memoria(ctx)
        assert bloque, f"[{src}] falta el bloque de memoria del área activa"
        assert "ADR-001" in bloque and "adversarial" in bloque.lower(), bloque
        assert "LES-001" not in bloque, "la lección de estimación NO es del área de la iniciativa activa"
        assert "aceptada" in bloque and "knowledge-find.py" in bloque and "--show" in bloque
        assert len(bloque) <= 1200 and len(ctx) <= 9500
        assert ctx.index("Agentes:") < ctx.index("Ledger canónico") < ctx.index("Memoria técnica"), src


def test_session_context_sin_knowledge_sin_aciertos_o_sin_activa_no_emite_el_bloque(tmp_path):
    proj, _ = proyecto(tmp_path)
    env = env_de(proj, tmp_path)
    payload = {"hook_event_name": "SessionStart", "source": "startup"}
    rc, out_sin, _ = hook("session-context.sh", payload, env)
    assert rc == 0 and "Memoria técnica" not in _ctx(out_sin) and "knowledge" not in _ctx(out_sin).lower()
    # corpus SIN entradas del área activa → mismo contexto que sin carpeta
    kn = _knowledge(proj)
    (kn / "adr" / "ADR-001-lentes-en-paralelo.md").unlink()
    readme = kn / "README.md"
    readme.write_text("\n".join(l for l in readme.read_text(encoding="utf-8").splitlines() if "ADR-001" not in l) + "\n",
                      encoding="utf-8")
    rc, out_vacio, _ = hook("session-context.sh", payload, env)
    assert rc == 0 and _ctx(out_vacio) == _ctx(out_sin), "sin aciertos el resto sale idéntico"
    # sin iniciativa activa → nada de memoria aunque haya corpus
    proj2, _ = proyecto(tmp_path / "b", activa=False)
    _knowledge(proj2)
    rc, out, _ = hook("session-context.sh", payload, env_de(proj2, tmp_path / "b"))
    assert rc == 0 and "Memoria técnica" not in _ctx(out)


def test_session_context_sesion_memoria_false_apaga_el_bloque(tmp_path):
    proj, _ = proyecto(tmp_path)
    _knowledge(proj)
    (proj / ".claude" / "dev.json").write_text('{"sesion": {"memoria": false}}', encoding="utf-8")
    rc, out, _ = hook("session-context.sh", {"hook_event_name": "SessionStart", "source": "startup"}, env_de(proj, tmp_path))
    assert rc == 0
    ctx = _ctx(out)
    assert "Memoria técnica" not in ctx and "Comandos:" in ctx and "demo" in ctx


def test_session_context_el_tope_de_memoria_va_antes_del_recorte_global(tmp_path):
    """41 entradas del área activa: el bloque se recorta a ≤ 1.200 caracteres y lo dice, y el índice de
    piezas y el roadmap siguen enteros (el tope propio se aplica ANTES del recorte a TOPE_CHARS)."""
    proj, _ = proyecto(tmp_path)
    _knowledge(proj, n_extra=40)
    rc, out, _ = hook("session-context.sh", {"hook_event_name": "SessionStart", "source": "startup"}, env_de(proj, tmp_path))
    assert rc == 0
    ctx = _ctx(out)
    bloque = _bloque_memoria(ctx)
    assert 0 < len(bloque) <= 1200, len(bloque)
    assert "más" in bloque, "recortado Y dicho"
    assert "Comandos:" in ctx and "Agentes:" in ctx and "Ledger canónico" in ctx and len(ctx) <= 9500
    assert not ctx.endswith("…"), "no hizo falta el recorte global"


def _segunda_activa(proj, led, slug, titulo=None):
    """Otra iniciativa ACTIVA (copia del ledger de fixture), opcionalmente con otro título H1 (→ otra área)."""
    d = proj / "docs" / "roadmap" / slug
    d.mkdir()
    text = led.read_text(encoding="utf-8")
    if titulo:
        text = re.sub(r"(?m)^# .*$", f"# Checklist de Tareas — {titulo}", text, count=1)
    (d / "tasks.md").write_text(text, encoding="utf-8")
    return d


def _total_cabecera(bloque):
    m = re.search(r"· (\d+) acierto\(s\) de knowledge-find\.py", bloque)
    return int(m.group(1)) if m else None


def test_session_context_dos_activas_del_mismo_area_deduplican_antes_de_contar(tmp_path):
    """Revisión intento 1 (IMPORTANT 3): con dos ledgers `en-progreso` de la misma área, la cabecera decía
    «4 acierto(s)», mostraba 2 y añadía «… y 2 más» que no existían (total sumaba por iniciativa y las
    líneas deduplicaban por ID). Ahora: únicos reales, sin «y N más» falso."""
    proj, led = proyecto(tmp_path)
    _knowledge(proj, n_extra=2)                                     # 3 entradas del área activa
    _segunda_activa(proj, led, "2026-01-02-demo-b")                 # mismo título → misma área
    rc, out, _ = hook("session-context.sh", {"hook_event_name": "SessionStart", "source": "startup"}, env_de(proj, tmp_path))
    assert rc == 0
    bloque = _bloque_memoria(_ctx(out))
    assert _total_cabecera(bloque) == 3, bloque
    assert bloque.count("- ADR-") == 3 and "más:" not in bloque, "3 únicos, los 3 mostrados: no hay «y N más»"
    for id_ in ("ADR-001", "ADR-002", "ADR-003"):
        assert bloque.count(f"- {id_} · ") == 1, f"{id_} repetido"
    assert "iniciativas activas" not in bloque, "con 2 activas no hay nada que avisar"


def test_session_context_dos_activas_de_areas_distintas_suman_sin_solape(tmp_path):
    proj, led = proyecto(tmp_path)
    _knowledge(proj)                                                # ADR-001 (adversarial) + LES-001 (estimación)
    _segunda_activa(proj, led, "2026-01-02-presupuesto", titulo="Estimación y calibración del presupuesto")
    rc, out, _ = hook("session-context.sh", {"hook_event_name": "SessionStart", "source": "startup"}, env_de(proj, tmp_path))
    assert rc == 0
    bloque = _bloque_memoria(_ctx(out))
    assert _total_cabecera(bloque) == 2 and "ADR-001" in bloque and "LES-001" in bloque, bloque
    assert "más:" not in bloque
    assert "--iniciativa demo" in bloque or "--show" in bloque


def test_session_context_tres_activas_lo_dice_en_la_cabecera_y_nombra_la_que_queda_fuera(tmp_path):
    """`activas[:2]` descartaba la tercera en silencio: ahora la cabecera lo declara."""
    proj, led = proyecto(tmp_path)
    _knowledge(proj, n_extra=1)
    _segunda_activa(proj, led, "2026-01-02-demo-b")
    _segunda_activa(proj, led, "2026-01-03-demo-c")
    rc, out, _ = hook("session-context.sh", {"hook_event_name": "SessionStart", "source": "startup"}, env_de(proj, tmp_path))
    assert rc == 0
    bloque = _bloque_memoria(_ctx(out))
    assert "3 iniciativas activas, consultadas las 2 primeras; fuera: demo-c" in bloque, bloque
    assert _total_cabecera(bloque) == 2 and bloque.count("- ADR-") == 2
    assert len(bloque) <= 1200


def test_session_context_con_el_tope_apretando_el_y_n_mas_es_real_y_no_desaloja_aciertos(tmp_path):
    """41 entradas del área y DOS activas que las comparten: antes `total` era 82 (41 × 2) y el «… y N más»
    inflado; el N tiene que ser exactamente únicos − mostrados, y mostrar tantas líneas como con UNA activa."""
    proj, led = proyecto(tmp_path)
    _knowledge(proj, n_extra=40)
    payload = {"hook_event_name": "SessionStart", "source": "startup"}
    rc, out_una, _ = hook("session-context.sh", payload, env_de(proj, tmp_path))
    una = _bloque_memoria(_ctx(out_una))
    _segunda_activa(proj, led, "2026-01-02-demo-b")
    rc, out_dos, _ = hook("session-context.sh", payload, env_de(proj, tmp_path))
    assert rc == 0
    dos = _bloque_memoria(_ctx(out_dos))
    assert 0 < len(dos) <= 1200
    assert _total_cabecera(dos) == _total_cabecera(una) == 41, (una, dos)
    mostradas = dos.count("\n- ")
    m = re.search(r"… y (\d+) más", dos)
    assert m and int(m.group(1)) == 41 - mostradas, dos
    # la línea «… y N más» nombra una orden por iniciativa consultada (más larga con dos): cuesta a lo sumo UNA
    # línea de acierto frente a una sola activa; antes, con total 82, el N inflado no era ni siquiera verdad
    assert una.count("\n- ") - 1 <= mostradas <= una.count("\n- ") and mostradas >= 1, (una, dos)


def test_session_context_resuelve_el_kit_del_repo_del_plugin_antes_que_una_copia_instalada(tmp_path):
    """Revisión intento 1 (MINOR 9): sin CLAUDE_PLUGIN_ROOT, dentro del repo del plugin, el `find` sobre
    ~/.claude caía a una copia INSTALADA (anterior a la rama). `<proyecto>/agent-kits/shared` va primero."""
    proj, _ = proyecto(tmp_path)
    home = tmp_path / "home"
    instalado = home / ".claude" / "plugins" / "cache" / "mk" / "custom-agents" / "agent-kits" / "shared"
    instalado.mkdir(parents=True)
    (instalado / "skill-index.py").write_text("print('INDICE-DE-LA-COPIA-INSTALADA')\n", encoding="utf-8")
    del_repo = proj / "agent-kits" / "shared"
    del_repo.mkdir(parents=True)
    (del_repo / "skill-index.py").write_text("print('INDICE-DEL-REPO-DEL-PLUGIN')\n", encoding="utf-8")
    env = env_de(proj, tmp_path)
    del env["CLAUDE_PLUGIN_ROOT"]
    payload = {"hook_event_name": "SessionStart", "source": "startup"}
    rc, out, err = hook("session-context.sh", payload, env, cwd=str(proj))
    assert rc == 0, err
    assert "INDICE-DEL-REPO-DEL-PLUGIN" in _ctx(out) and "INSTALADA" not in _ctx(out), _ctx(out)
    # sin el kit en el proyecto, el find sobre ~/.claude sigue siendo el respaldo
    shutil.rmtree(proj / "agent-kits")
    rc, out, _ = hook("session-context.sh", payload, env, cwd=str(proj))
    assert rc == 0 and "INDICE-DE-LA-COPIA-INSTALADA" in _ctx(out)
    # y CLAUDE_PLUGIN_ROOT sigue mandando sobre los dos
    (del_repo).mkdir(parents=True)
    (del_repo / "skill-index.py").write_text("print('INDICE-DEL-REPO-DEL-PLUGIN')\n", encoding="utf-8")
    rc, out, _ = hook("session-context.sh", payload, env_de(proj, tmp_path), cwd=str(proj))
    assert rc == 0 and "Comandos:" in _ctx(out) and "INDICE-DEL-REPO" not in _ctx(out)


# -------------------------------------------------------- implementer-guardrail ----

def test_guardrail_deny_spec_md_contrato_oficial(tmp_path):
    proj, _ = proyecto(tmp_path)
    payload = {"tool_name": "Write", "tool_input": {"file_path": str(proj / "docs" / "roadmap" / "2026-01-01-demo" / "spec.md"), "content": "x"}}
    rc, out, _ = hook("implementer-guardrail.sh", payload, env_de(proj, tmp_path))
    assert rc == 0
    hso = un_json(out)["hookSpecificOutput"]
    assert hso["hookEventName"] == "PreToolUse" and hso["permissionDecision"] == "deny"
    assert "tasks.md" in hso["permissionDecisionReason"]


def test_guardrail_allow_tasks_md_sin_stdout(tmp_path):
    proj, led = proyecto(tmp_path)
    payload = {"tool_name": "Edit", "tool_input": {"file_path": str(led), "old_string": "a", "new_string": "b"}}
    assert hook("implementer-guardrail.sh", payload, env_de(proj, tmp_path)) == (0, "", "")


def test_guardrail_deny_git_push_force(tmp_path):
    proj, _ = proyecto(tmp_path)
    payload = {"tool_name": "Bash", "tool_input": {"command": "git push --force origin feature/x"}}
    rc, out, _ = hook("implementer-guardrail.sh", payload, env_de(proj, tmp_path))
    assert rc == 0
    hso = un_json(out)["hookSpecificOutput"]
    assert hso["permissionDecision"] == "deny" and "forzado" in hso["permissionDecisionReason"]


def test_guardrail_sin_python3_avisa_una_vez_y_no_bloquea(tmp_path):
    proj, _ = proyecto(tmp_path)
    env = env_de(proj, tmp_path, sin_python=True)
    payload = {"tool_name": "Write", "tool_input": {"file_path": str(proj / "docs" / "roadmap" / "x" / "spec.md")}}
    rc1, out1, _ = hook("implementer-guardrail.sh", payload, env)
    assert rc1 == 0
    d = un_json(out1)
    assert set(d) == {"systemMessage"} and "python3" in d["systemMessage"]   # aviso, NO deny
    assert (proj / ".claude" / ".guardrail-nopython").exists()
    assert hook("implementer-guardrail.sh", payload, env) == (0, "", "")        # 2.ª vez: silencio


# ---------------------------------------------------------- architect-guardrail ----

def test_architect_guardrail_deny_codigo_allow_design(tmp_path):
    proj, _ = proyecto(tmp_path)
    payload = {"tool_name": "Write", "tool_input": {"file_path": str(proj / "src" / "app.py"), "content": "x"}}
    rc, out, _ = hook("architect-guardrail.sh", payload, env_de(proj, tmp_path))
    assert rc == 0
    hso = un_json(out)["hookSpecificOutput"]
    assert hso["permissionDecision"] == "deny" and "architect" in hso["permissionDecisionReason"]
    payload = {"tool_name": "Write", "tool_input": {"file_path": str(proj / "docs" / "roadmap" / "2026-01-01-demo" / "design.md"), "content": "x"}}
    assert hook("architect-guardrail.sh", payload, env_de(proj, tmp_path)) == (0, "", "")


def test_architect_guardrail_sin_python3_avisa_como_architect(tmp_path):
    proj, _ = proyecto(tmp_path)
    env = env_de(proj, tmp_path, sin_python=True)
    payload = {"tool_name": "Write", "tool_input": {"file_path": str(proj / "src" / "app.py")}}
    rc, out, _ = hook("architect-guardrail.sh", payload, env)
    assert rc == 0 and "architect" in un_json(out)["systemMessage"]


# -------------------------------------------- mark-docs-pending · ledger-lint-warn ----

def test_mark_docs_pending_marca_con_docs_y_no_con_security_scan(tmp_path):
    proj, led = proyecto(tmp_path)
    env = env_de(proj, tmp_path)
    assert hook("mark-docs-pending.sh", post_tool(str(proj / "docs" / "security-scan" / "STATE.md")), env) == (0, "", "")
    assert not (proj / ".claude" / ".confluence-pending").exists()
    assert hook("mark-docs-pending.sh", post_tool(str(led)), env) == (0, "", "")
    assert (proj / ".claude" / ".confluence-pending").exists()


def test_ledger_lint_warn_exit_0_con_ledger_coherente_e_incoherente(tmp_path):
    proj, led = proyecto(tmp_path)
    env = env_de(proj, tmp_path)
    rc, out, _ = hook("ledger-lint-warn.sh", post_tool(str(led)), env)
    assert rc == 0 and "Traceback" not in out
    # ledger roto (tarea completada con criterio sin marcar) → sigue exit 0, informa por stdout
    led.write_text(led.read_text(encoding="utf-8").replace("- [x] `skills/adversarial-review/SKILL.md` con frontmatter", "- [ ] `skills/adversarial-review/SKILL.md` con frontmatter", 1), encoding="utf-8")
    rc, out, _ = hook("ledger-lint-warn.sh", post_tool(str(led)), env)
    assert rc == 0 and "T-01" in out, out


# ------------------------------------------------------------------ statusline ----

def test_statusline_json_oficial_una_linea_con_modelo_coste_y_roadmap(tmp_path):
    proj, _ = proyecto(tmp_path)
    payload = {"model": {"display_name": "Opus"}, "cost": {"total_cost_usd": 0.01234}, "context_window": {"used_percentage": 8}}
    rc, out, _ = hook("statusline", payload, env_de(proj, tmp_path))
    assert rc == 0
    lineas = out.splitlines()
    assert len(lineas) == 1 and lineas[0].startswith("[Opus] $0.01 ctx 8%"), out
    assert "📋 demo T-03/4" in lineas[0], out


def test_statusline_stdin_vacio_exit_0(tmp_path):
    proj, _ = proyecto(tmp_path, activa=False)
    rc, out, _ = hook("statusline", "", env_de(proj, tmp_path))
    assert rc == 0 and out.strip() == ""


def test_todos_los_hooks_son_bash_valido_y_ejecutables():
    for fn in sorted(os.listdir(HOOKS)):
        p = os.path.join(HOOKS, fn)
        if fn.endswith(".sh"):
            assert subprocess.run([BASH, "-n", p], capture_output=True).returncode == 0, fn
            assert os.stat(p).st_mode & stat.S_IXUSR, f"{fn} sin bit ejecutable"
        elif fn.endswith(".json"):
            assert not os.stat(p).st_mode & stat.S_IXUSR, f"{fn} no debería ser ejecutable (T-01c)"


def main():
    if pytest is None:
        print("test_hooks_shell: pytest no instalado — suite omitida (pip install pytest)")
        return 0
    if BASH is None:
        print("test_hooks_shell: sin bash — suite omitida")
        return 0
    return pytest.main(["-q", __file__])


if __name__ == "__main__":
    sys.exit(main())
