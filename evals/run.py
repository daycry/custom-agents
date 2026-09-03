#!/usr/bin/env python3
"""
run.py — runner LOCAL de los evals de comportamiento (`evals/cases/*.json`). Lanza cada caso
en una sesión headless de Claude Code con el plugin cargado, en un cwd temporal (copia de
`evals/fixtures/project/`), y evalúa `expect`. Cuesta tokens reales: NO corre en CI (ahí va
`check.py`). Requiere `claude` en PATH (exit 2 si falta, salvo `--dry-run`).

Contrato de la CLI usado (code.claude.com/docs/en/headless + cli-reference, verificado 2026-09-03):
  claude -p "<prompt>" --output-format stream-json --verbose --plugin-dir <raíz del plugin>
         --max-turns N --permission-mode acceptEdits --allowedTools "<--allowed-tools>" [--bare]
  · `--output-format json` devuelve SOLO el resultado final (result, session_id, coste) — sin las
    tool uses; para ver QUÉ se activó hace falta `stream-json` (+ `--verbose`, obligatorio en -p),
    cuyas líneas `{"type":"assistant","message":{"content":[{"type":"tool_use",…}]}}` traen cada
    herramienta invocada. La última línea es `{"type":"result", result, total_cost_usd, num_turns…}`.
  · `--plugin-dir` carga el plugin para esa sesión (sin instalarlo). `--bare` (opt-in aquí) evita
    cargar hooks/skills/CLAUDE.md del host — más reproducible, pero exige ANTHROPIC_API_KEY.
  · No existe `claude plugin eval`: el formato de casos es PROPIO (ver evals/README.md).

Cómo se detecta la ACTIVACIÓN (determinista sobre la transcripción):
  · skill:<n> y command:<n> → una tool use `Skill` (o `SlashCommand`, versiones antiguas) cuyo
    `input.skill` / `input.command` / `input.name`, sin `/` inicial, sin argumentos y sin el
    namespace `custom-agents:`, es exactamente <n>. (Los commands se fusionaron con las skills:
    Claude los invoca por la herramienta Skill.)
  · agent:<n> → una tool use `Agent` (o `Task`) con `input.subagent_type` == <n> (mismo recorte).
  · `--loose` añade una señal débil: un `Read` de `skills/<n>/SKILL.md`, `commands/<n>.md` o
    `agents/<n>.md` también cuenta (útil para depurar, no para el veredicto por defecto).
  Se miran TODAS las tool uses del stream (también las de subagentes: `parent_tool_use_id`).

Veredicto por caso (pasa si TODO se cumple):
  · `expect.activates` == activación detectada del target.
  · `expect.mentions`: cada cadena aparece (sin distinguir mayúsculas) en el texto del asistente
    (bloques `text` + `result`). `expect.must_not`: ninguna aparece.
  · `expect.artifacts`: cada glob (relativo al cwd temporal, `**` recursivo) casa ≥ 1 fichero.
  · `expect.redirect` es INFORMATIVO: se anota si la pieza alternativa se activó, no decide.
  Un `claude` que termina con error o timeout → caso fallido con el motivo.
  · `causa` por caso fallido: `no activó` / `activó sin deber` (activación), `permiso denegado`
    (la pieza SÍ se activó pero una tool use —típicamente Bash— fue denegada: en `-p` nadie
    aprueba y `acceptEdits` no cubre Bash; se detecta en los `tool_result` con `is_error` cuyo
    texto habla de permisos), `expectativa` (mentions/must_not/artifacts) o `timeout`. Por eso
    `--allowed-tools` (default `ALLOWED_TOOLS_DEFAULT`, se pasa tal cual a `--allowedTools`).

Informe: evals/reports/<AAAA-MM-DD>.json (o --report) + resumen en consola.
Exit: 0 todo pasa · 1 algún caso falla · 2 `claude` no está en PATH.

Uso:
  python3 evals/run.py --dry-run                      # imprime los comandos, no ejecuta nada
  python3 evals/run.py --target skill:quick-implement  # un target (repetible: --target A --target B)
  python3 evals/run.py --only quick-implement-literal  # un caso
  python3 evals/run.py --max-turns 6 --timeout 900 --bare
"""
import argparse
import datetime as _dt
import glob
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(HERE, "fixtures", "project")
SKILL_TOOLS = {"Skill", "SlashCommand"}
# Default de --allowed-tools: lo que los scripts del plugin lanzan por Bash (python3, git, find) — sin
# esto, en `-p` una tool use de Bash queda denegada y el caso falla por permisos, no por activación.
ALLOWED_TOOLS_DEFAULT = "Bash(python3:*),Bash(git:*),Bash(find:*)"
AGENT_TOOLS = {"Agent", "Task"}


# ------------------------------------------------------------------ casos

def cargar_casos(cases_dir, target=None, only=None):
    """[(target, caso)] ordenados por fichero; filtra por --target (uno o varios: str o lista —
    `--target` es repetible, plan-and-diet T-03) / --only."""
    targets = None
    if target:
        targets = {target} if isinstance(target, str) else set(target)
    out = []
    for fn in sorted(os.listdir(cases_dir)):
        if not fn.endswith(".json"):
            continue
        data = json.load(open(os.path.join(cases_dir, fn), encoding="utf-8"))
        t = data.get("target", "")
        if targets and t not in targets:
            continue
        for c in data.get("cases", []):
            if only and c.get("id") != only:
                continue
            out.append((t, c))
    return out


# ------------------------------------------------------------------ comando

def construir_comando(prompt, root, opts):
    cmd = [opts.claude, "-p", prompt, "--output-format", "stream-json", "--verbose",
           "--plugin-dir", root, "--max-turns", str(opts.max_turns),
           "--permission-mode", opts.permission_mode]
    if getattr(opts, "allowed_tools", None):
        cmd += ["--allowedTools", opts.allowed_tools]
    if opts.bare:
        cmd.append("--bare")
    return cmd


def preparar_cwd(fixture, base):
    """Copia del fixture en un directorio temporal (+ `git init` silencioso si hay git)."""
    cwd = tempfile.mkdtemp(prefix="eval-", dir=base)
    if os.path.isdir(fixture):
        shutil.copytree(fixture, cwd, dirs_exist_ok=True)
    if shutil.which("git"):
        try:
            for args in (["git", "init", "-q"], ["git", "add", "-A"],
                         ["git", "-c", "user.email=evals@example.com", "-c", "user.name=evals",
                          "commit", "-q", "-m", "fixture", "--allow-empty"]):
                subprocess.run(args, cwd=cwd, capture_output=True, timeout=30, check=False)
        except (OSError, subprocess.SubprocessError):
            pass
    return cwd


# ------------------------------------------------------------------ transcripción

def parsear_stream(texto):
    """stream-json (una línea = un evento) → {tool_uses:[{name,input,parent}], textos:[…], result:{…}}."""
    out = {"tool_uses": [], "textos": [], "result": None, "lineas_invalidas": 0, "permisos_denegados": []}
    for linea in texto.splitlines():
        linea = linea.strip()
        if not linea:
            continue
        try:
            ev = json.loads(linea)
        except ValueError:
            out["lineas_invalidas"] += 1
            continue
        if not isinstance(ev, dict):
            continue
        tipo = ev.get("type")
        if tipo == "assistant":
            msg = ev.get("message") or {}
            for bloque in msg.get("content", []) or []:
                if not isinstance(bloque, dict):
                    continue
                if bloque.get("type") == "tool_use":
                    out["tool_uses"].append({"name": bloque.get("name", ""),
                                             "input": bloque.get("input") or {},
                                             "parent": ev.get("parent_tool_use_id")})
                elif bloque.get("type") == "text" and bloque.get("text"):
                    out["textos"].append(bloque["text"])
        elif tipo == "user":
            # tool_result con error de PERMISO (en `-p` nadie aprueba; acceptEdits no cubre Bash):
            # causa distinta de «no activó» — se marca aparte en el informe.
            msg = ev.get("message") or {}
            for bloque in msg.get("content", []) or []:
                if isinstance(bloque, dict) and bloque.get("type") == "tool_result" and bloque.get("is_error"):
                    texto = _texto_de(bloque.get("content"))
                    if PERMISO_RE.search(texto):
                        out["permisos_denegados"].append(texto[:200])
        elif tipo == "result":
            out["result"] = ev
    return out


PERMISO_RE = re.compile(r"(permission|permiso|haven't granted|hasn't granted|not allowed|denied|requires approval)", re.I)


def _texto_de(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(str(b.get("text", "")) if isinstance(b, dict) else str(b) for b in content)
    return str(content or "")


def _nombre_pieza(valor):
    """'/custom-agents:pm-cycle mi objetivo' → 'pm-cycle'."""
    if not isinstance(valor, str):
        return ""
    v = valor.strip().lstrip("/").split()[0] if valor.strip() else ""
    return v.rsplit(":", 1)[-1]


def detectar(tool_uses, target, loose=False):
    """True si alguna tool use invoca la pieza `kind:name`."""
    kind, name = target.split(":", 1)
    for tu in tool_uses:
        n, inp = tu.get("name", ""), tu.get("input") or {}
        if kind in ("skill", "command") and n in SKILL_TOOLS:
            valor = inp.get("skill") or inp.get("command") or inp.get("name")
            if _nombre_pieza(valor) == name:
                return True
        if kind == "agent" and n in AGENT_TOOLS:
            if _nombre_pieza(inp.get("subagent_type")) == name:
                return True
        if loose and n == "Read":
            ruta = str(inp.get("file_path", "")).replace("\\", "/")
            sufijo = {"skill": f"skills/{name}/SKILL.md", "command": f"commands/{name}.md",
                      "agent": f"agents/{name}.md"}[kind]
            if ruta.endswith(sufijo):
                return True
    return False


def evaluar(target, caso, parsed, cwd, loose=False):
    """→ {pass, checks:{…}, activado, redirect_observado}."""
    exp = caso.get("expect", {})
    checks = {}
    activado = detectar(parsed["tool_uses"], target, loose)
    checks["activates"] = (activado == bool(exp.get("activates")))
    texto = "\n".join(parsed["textos"] + [str((parsed["result"] or {}).get("result", ""))]).lower()
    faltan = [m for m in exp.get("mentions", []) if m.lower() not in texto]
    checks["mentions"] = not faltan
    sobran = [m for m in exp.get("must_not", []) if m.lower() in texto]
    checks["must_not"] = not sobran
    sin_artefacto = [g for g in exp.get("artifacts", [])
                     if not glob.glob(os.path.join(cwd, g), recursive=True)]
    checks["artifacts"] = not sin_artefacto
    res = parsed["result"] or {}
    checks["sin_error"] = not res.get("is_error", False) and res.get("subtype", "success") == "success"
    permisos = parsed.get("permisos_denegados", [])
    detalle = {"mentions_faltan": faltan, "must_not_presentes": sobran, "artifacts_faltan": sin_artefacto,
               "permisos_denegados": permisos}
    ok = all(checks.values())
    if ok:
        causa = None
    elif not checks["activates"]:
        causa = "no activó" if exp.get("activates") else "activó sin deber"
    elif permisos:
        causa = "permiso denegado"          # la pieza se activó; falló una herramienta por permisos, no la activación
    else:
        causa = "expectativa"
    redirect = exp.get("redirect")
    return {
        "pass": ok,
        "causa": causa,
        "checks": checks,
        "detalle": detalle,
        "activado": activado,
        "redirect_observado": detectar(parsed["tool_uses"], redirect, loose) if redirect else None,
        "tool_uses": [f"{t['name']}({_resumen_input(t['input'])})" for t in parsed["tool_uses"]][:40],
        "coste_usd": res.get("total_cost_usd"),
        "turnos": res.get("num_turns"),
    }


def _resumen_input(inp):
    for k in ("skill", "command", "subagent_type", "file_path", "pattern"):
        if k in inp:
            return f"{k}={str(inp[k])[:60]}"
    return ""


# ------------------------------------------------------------------ ejecución

def ejecutar_caso(target, caso, root, opts, runner):
    cmd = construir_comando(caso["prompt"], root, opts)
    cwd = preparar_cwd(opts.fixture, opts.workdir)
    t0 = time.time()
    try:
        r = runner(cmd, cwd=cwd, capture_output=True, text=True, timeout=opts.timeout)
        parsed = parsear_stream(r.stdout or "")
        ev = evaluar(target, caso, parsed, cwd, opts.loose)
        if r.returncode != 0:
            ev["checks"]["exit_0"] = False
            ev["pass"] = False
        ev["exit_code"] = r.returncode
        ev["stderr"] = (r.stderr or "")[-2000:]
    except subprocess.TimeoutExpired:
        ev = {"pass": False, "causa": "timeout", "checks": {"timeout": False}, "detalle": {}, "activado": None,
              "redirect_observado": None, "tool_uses": [], "coste_usd": None, "turnos": None,
              "exit_code": None, "stderr": f"timeout tras {opts.timeout}s"}
    ev.update({"id": caso["id"], "target": target, "segundos": round(time.time() - t0, 1),
               "cwd": cwd if opts.keep else None})
    if not opts.keep:
        shutil.rmtree(cwd, ignore_errors=True)
    return ev


def main(argv=None, runner=None):
    ap = argparse.ArgumentParser(description="runner local de evals de comportamiento")
    ap.add_argument("--root", default=os.path.dirname(HERE), help="raíz del plugin (--plugin-dir)")
    ap.add_argument("--cases", default=os.path.join(HERE, "cases"))
    ap.add_argument("--fixture", default=FIXTURE)
    ap.add_argument("--target", action="append",
                    help="solo este target (p. ej. skill:quick-implement); repetible: --target A --target B")
    ap.add_argument("--only", help="solo este id de caso")
    ap.add_argument("--dry-run", action="store_true", help="imprime los comandos y sale (exit 0)")
    ap.add_argument("--max-turns", type=int, default=8)
    ap.add_argument("--permission-mode", default="acceptEdits")
    ap.add_argument("--allowed-tools", default=ALLOWED_TOOLS_DEFAULT,
                    help="se pasa tal cual a `claude -p --allowedTools` (en -p nadie aprueba; acceptEdits no cubre Bash). "
                         "Cadena vacía → no se pasa")
    ap.add_argument("--bare", action="store_true", help="añade --bare (sin hooks/skills del host; exige ANTHROPIC_API_KEY)")
    ap.add_argument("--timeout", type=int, default=600, help="segundos por caso")
    ap.add_argument("--loose", action="store_true", help="un Read del fichero de la pieza también cuenta como activación")
    ap.add_argument("--claude", default="claude", help="binario de Claude Code")
    ap.add_argument("--report", help="ruta del informe JSON (default evals/reports/<fecha>.json)")
    ap.add_argument("--workdir", default=None, help="dónde crear los cwd temporales")
    ap.add_argument("--keep", action="store_true", help="no borrar los cwd temporales")
    opts = ap.parse_args(argv)

    root = os.path.abspath(opts.root)
    casos = cargar_casos(opts.cases, opts.target, opts.only)
    if not casos:
        print("evals/run: ningún caso seleccionado", file=sys.stderr)
        return 1

    if opts.dry_run:
        for target, c in casos:
            print(f"# {target} · {c['id']} · activates={c['expect'].get('activates')}")
            print("  " + " ".join(shlex.quote(x) for x in construir_comando(c["prompt"], root, opts)))
        print(f"evals/run --dry-run: {len(casos)} casos (no ejecutado nada)")
        return 0

    if runner is None:
        if shutil.which(opts.claude) is None:
            print(f"evals/run: `{opts.claude}` no está en PATH — instala Claude Code "
                  f"(https://code.claude.com) o pasa --claude <ruta>. Nada ejecutado.", file=sys.stderr)
            return 2
        runner = subprocess.run

    resultados = []
    for target, c in casos:
        ev = ejecutar_caso(target, c, root, opts, runner)
        resultados.append(ev)
        marca = "✅" if ev["pass"] else "❌"
        fallos = [k for k, v in ev["checks"].items() if not v]
        print(f"{marca} {target:32s} {ev['id']:40s} {ev['segundos']:6.1f}s"
              + (f"  falla: {', '.join(fallos)} [{ev.get('causa')}]" if fallos else ""))

    ok = sum(1 for r in resultados if r["pass"])
    informe = {
        "fecha": _dt.datetime.now().isoformat(timespec="seconds"),
        "plugin_root": root, "max_turns": opts.max_turns, "permission_mode": opts.permission_mode,
        "allowed_tools": opts.allowed_tools or None,
        "permisos_denegados": sum(1 for r in resultados if r.get("causa") == "permiso denegado"),
        "bare": opts.bare, "loose": opts.loose,
        "total": len(resultados), "pasan": ok, "fallan": len(resultados) - ok,
        "coste_usd": round(sum(r["coste_usd"] or 0 for r in resultados), 4),
        "casos": resultados,
    }
    report = opts.report or os.path.join(HERE, "reports", _dt.date.today().isoformat() + ".json")
    os.makedirs(os.path.dirname(os.path.abspath(report)), exist_ok=True)
    with open(report, "w", encoding="utf-8") as f:
        json.dump(informe, f, ensure_ascii=False, indent=2)
    print(f"\nevals/run: {ok}/{len(resultados)} pasan · coste ≈ ${informe['coste_usd']} · informe: {report}")
    return 0 if ok == len(resultados) else 1


if __name__ == "__main__":
    sys.exit(main())
