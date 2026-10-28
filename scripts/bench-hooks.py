#!/usr/bin/env python3
"""Measure registered shared hook launchers in disposable projects; estimates use chars/4."""
import argparse
import ctypes
from datetime import datetime, timezone
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
RUNTIMES = ("claude", "codex", "opencode")
LAUNCHER = "${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.mjs"
COMMAND = re.compile(r'^node "\$\{CLAUDE_PLUGIN_ROOT\}/hooks/run-hook\.mjs" ([a-z.-]+)(?: --runtime=claude)?$')


def registered_hooks(root):
    """Retain each event registration, including repeated activity registrations."""
    config = json.loads((root / "hooks/hooks.json").read_text(encoding="utf-8"))
    cases = []
    for event, groups in config["hooks"].items():
        for g, group in enumerate(groups):
            for h, handler in enumerate(group["hooks"]):
                command = handler.get("command", "")
                args = handler.get("args")
                match = COMMAND.fullmatch(command)
                if command == "node" and isinstance(args, list) and len(args) == 2 and args[0] == LAUNCHER:
                    target = args[1]
                elif args is None and match:
                    target = match[1]
                else:
                    raise ValueError(f"unsupported hook registration: {event}:{g}:{h}")
                if not isinstance(target, str) or not re.fullmatch(r"[a-z.-]+", target):
                    raise ValueError("invalid hook target")
                cases.append({"evento": event, "hook": target, "registro": f"{event}:{g}:{h}",
                              "async": handler.get("async", False)})
    if not cases:
        raise ValueError("no hook registrations")
    return cases


def load_payload(root, runtime, event, project):
    path = root / "tests/fixtures/bench-hooks" / (runtime + ".json")
    fixtures = json.loads(path.read_text(encoding="utf-8"))
    payload = fixtures.get(event)
    if not isinstance(payload, dict) or payload.get("hook_event_name") != event:
        raise ValueError(f"missing or invalid fixture: {runtime}/{event}")
    # Replace values, never parse template substitutions as source or shell code.
    def expand(value):
        if isinstance(value, str):
            return value.replace("${PROJECT}", project.as_posix())
        if isinstance(value, dict):
            return {key: expand(item) for key, item in value.items()}
        return value
    payload = expand(payload)
    payload["cwd"] = str(project)
    return payload


def prepare_project(project):
    ledger = project / "docs/roadmap/bench/tasks.md"
    ledger.parent.mkdir(parents=True)
    ledger.write_text("# Benchmark fixture\n\n| **Estado** | en-progreso |\n\n"
                      "## Fase 1\n\n### T-01 — Fixture\n\n- **Estado**: en-progreso\n", encoding="utf-8")
    (project / ".claude").mkdir()
    # Deterministic defaults; do not enable network/AI summaries or optional activity.
    (project / ".claude/dev.json").write_text('{"sesion":{"resumen":false,"actividad":false}}\n', encoding="utf-8")


def invoke(root, case, payload, project, timeout):
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project), "CLAUDE_PLUGIN_ROOT": str(root),
           "CUSTOM_AGENTS_PYTHON": sys.executable, "PYTHONIOENCODING": "utf-8:replace"}
    env.pop("CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS", None)
    command = [shutil.which("node") or "node", str(root / "hooks/run-hook.mjs"), case["hook"],
               "--runtime=" + case["runtime"]]
    started = time.perf_counter()
    error = None
    elapsed = None
    try:
        result = subprocess.run(command, input=json.dumps(payload), cwd=project, env=env,
                                capture_output=True, text=True, encoding="utf-8", errors="replace",
                                timeout=timeout)
        elapsed = round((time.perf_counter() - started) * 1000, 3)
        if result.returncode:
            error = f"process exit {result.returncode}"
        elif result.stderr.strip():
            # Launchers deliberately exit 0 on degradation: never report that as fast success.
            error = "launcher diagnostic: " + result.stderr.strip()[:240]
        elif case["hook"] == "session-context.sh":
            try:
                output = json.loads(result.stdout)
                if not output.get("hookSpecificOutput", {}).get("additionalContext"):
                    error = "missing SessionStart context"
            except ValueError:
                error = "invalid SessionStart output"
    except subprocess.TimeoutExpired:
        error = f"timeout after {timeout}s"
    except OSError as exc:
        error = f"cannot start launcher: {type(exc).__name__} (errno {exc.errno})"
    if error is None and case["hook"] in ("session-journal.sh", "user-prompt-capture.sh"):
        if case["hook"] == "session-journal.sh":
            records = (project / ".claude/journal/outbox").glob("*.json")
            key, expected = "session_id", payload["session_id"]
        else:
            records = [project / ".claude" / ("session-prompts-" + payload["session_id"] + ".log")]
            key, expected = "prompt", payload.get("prompt")
        persisted = False
        for path in records:
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
                persisted = isinstance(value, dict) and value.get(key) == expected
            except (OSError, ValueError):
                continue
            if persisted:
                break
        if not persisted:
            error = "capture did not persist the expected fixture record"
    return {"ms": elapsed if elapsed is not None else round((time.perf_counter() - started) * 1000, 3), "error": error}


def percentile(values, percent):
    ordered = sorted(values)
    index = (len(ordered) - 1) * percent / 100
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    return round(ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower), 3)


def measure_case(root, case, runtime, runs, warmup, timeout):
    row = {**case, "runtime": runtime, "estado": "OK", "muestras_ms": [],
           "mediana_ms": None, "p95_ms": None, "max_ms": None}
    with tempfile.TemporaryDirectory(prefix="bench-hooks-") as temporary:
        sandbox = Path(temporary)
        for iteration in range(runs + warmup):
            project = sandbox / str(iteration)
            project.mkdir()
            prepare_project(project)
            payload = load_payload(root, runtime, case["evento"], project)
            result = invoke(root, row, payload, project, timeout)
            if result["error"]:
                row.update(estado="FALLO", fallo=result["error"], iteracion=iteration,
                           calentamiento=iteration < warmup)
                return row
            if iteration >= warmup:
                row["muestras_ms"].append(result["ms"])
    values = row["muestras_ms"]
    row.update(mediana_ms=round(statistics.median(values), 3), p95_ms=percentile(values, 95), max_ms=max(values))
    return row


def estimate(text):
    return {"caracteres": len(text), "tokens_estimados": math.ceil(len(text) / 4)}


def token_report(root):
    path = root / "agent-kits/shared/skill-index.py"
    spec = importlib.util.spec_from_file_location("bench_skill_index", path)
    index = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(index)
    pieces = index.piezas(str(root))
    descriptions = estimate("".join(piece[2] for piece in pieces))
    descriptions["piezas"] = len(pieces)
    descriptions["por_tipo"] = {kind: estimate("".join(p[2] for p in pieces if p[0] == kind))
                                for kind in ("command", "skill", "agent")}
    indices = {runtime: estimate(index.generar(str(root), usar_cache=False, runtime=runtime)["texto"])
               for runtime in RUNTIMES}
    return {"tokens_fijos": {"metodo": "estimación caracteres/4, redondeo superior; no es un tokenizador ni consumo real",
                             "descriptions": descriptions, "indice_por_runtime": indices,
                             "por_runtime": {r: descriptions["tokens_estimados"] + indices[r]["tokens_estimados"] for r in RUNTIMES}},
            "tokens_bajo_demanda": {name: estimate((root / name).read_text(encoding="utf-8"))
                                    for name in ("commands/dev-cycle.md", "agent-kits/shared/knowledge-check.md")}}


def machine_info():
    free = None
    if os.name == "nt":
        class Memory(ctypes.Structure):
            _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [(name, ctypes.c_ulonglong) for name in
                        ("total", "available", "total_page", "available_page", "total_virtual", "available_virtual", "extended")]
        memory = Memory()
        memory.length = ctypes.sizeof(memory)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):
            free = memory.available
    else:
        try:
            free = os.sysconf("SC_AVPHYS_PAGES") * os.sysconf("SC_PAGE_SIZE")
        except (ValueError, OSError, AttributeError):
            pass
    return {"sistema": platform.system(), "version": platform.release(), "python": platform.python_version(),
            "ram_libre_bytes": free, "repositorio_en_onedrive": any("onedrive" in p.lower() for p in ROOT.parts)}


def markdown(report):
    lines = ["# Benchmark de hooks y tokens", "", f"Fecha UTC: {report['fecha']}", "",
             f"Máquina: {report['maquina']['sistema']}; RAM libre: {report['maquina']['ram_libre_bytes']} bytes.",
             "Medición local end-to-end del launcher compartido (no aceptación nativa de los runtimes).",
             f"Muestras: {report['runs']}; calentamiento descartado: {report['warmup']}; estado: {report['estado']}.",
             f"Casos ejecutados: {report.get('casos_ejecutados', len(report['hooks']))}/{report.get('casos_previstos', len(report['hooks']))}.", "",
             "| Runtime | Evento | Hook | Estado | Mediana ms | p95 ms | Máximo ms |",
             "|---|---|---|---|---:|---:|---:|"]
    for row in report["hooks"]:
        lines.append("| " + " | ".join(str(row[key]) for key in
                     ("runtime", "evento", "hook", "estado", "mediana_ms", "p95_ms", "max_ms")) + " |")
        if row.get("fallo"):
            lines.append("\nFALLO: " + row["fallo"].replace("\n", " ").replace("\r", " ") + "\n")
    if report.get("fallo"):
        lines.extend(["", "FALLO: " + report["fallo"]])
    if "tokens_fijos" in report:
        fixed = report["tokens_fijos"]
        lines.extend(["", fixed["metodo"], "", "| Runtime | Tokens fijos estimados |", "|---|---:|"])
        lines.extend(f"| {runtime} | {count} |" for runtime, count in fixed["por_runtime"].items())
        lines.extend(["", "| Bajo demanda | Caracteres | Tokens estimados |", "|---|---:|---:|"])
        lines.extend(f"| {name} | {value['caracteres']} | {value['tokens_estimados']} |" for name, value in report["tokens_bajo_demanda"].items())
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--runtime", choices=RUNTIMES)
    parser.add_argument("--hook", help="Measure only this registered shared hook target")
    parser.add_argument("--tokens-only", action="store_true")
    parser.add_argument("--fail-fast", action="store_true", help="Stop after the first failed case; retain its samples and diagnostic")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true")
    output.add_argument("--md", action="store_true")
    args = parser.parse_args(argv)
    if args.runs < 1:
        parser.error("--runs must be at least 1")
    if args.warmup < 0 or not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--warmup must be nonnegative and --timeout finite and positive")
    report = {"schema_version": 1, "fecha": datetime.now(timezone.utc).isoformat(), "runs": args.runs, "warmup": args.warmup,
              "maquina": machine_info(), "estado": "OK", "hooks": [],
              "linea_base": False, "casos_previstos": 0, "casos_ejecutados": 0}
    try:
        report.update(token_report(ROOT))
        cases = registered_hooks(ROOT)
        if args.hook:
            cases = [case for case in cases if case["hook"] == args.hook]
            if not cases:
                raise ValueError("hook target is not registered")
        if not args.tokens_only:
            runtimes = (args.runtime,) if args.runtime else RUNTIMES
            report["casos_previstos"] = len(cases) * len(runtimes)
            for runtime in runtimes:
                for case in cases:
                    row = measure_case(ROOT, case, runtime, args.runs, args.warmup, args.timeout)
                    report["hooks"].append(row)
                    if args.fail_fast and row["estado"] == "FALLO":
                        break
                if args.fail_fast and report["hooks"][-1]["estado"] == "FALLO":
                    break
        if any(row["estado"] == "FALLO" for row in report["hooks"]):
            report["estado"] = "FALLO"
    except (OSError, ValueError, KeyError) as exc:
        report.update(estado="FALLO", fallo=f"{type(exc).__name__}: {exc}")
    report["casos_ejecutados"] = len(report["hooks"])
    report["linea_base"] = (report["estado"] == "OK" and args.runs >= 10 and args.warmup > 0 and not args.tokens_only
                            and not args.runtime and not args.hook)
    print(json.dumps(report, ensure_ascii=False) if args.json else markdown(report), end="\n" if args.json else "")
    return int(report["estado"] != "OK")


if __name__ == "__main__":
    sys.exit(main())
