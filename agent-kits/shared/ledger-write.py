#!/usr/bin/env python3
"""Write canonical task states, RED evidence and review handoffs.

The canonical parser/linter owns interpretation; local-state owns cooperative
locking and atomic publication. This tool does not judge evidence or approve QA.
Exit 0 success, 1 invalid ledger, 2 input/I/O, 3 conflict, 4 busy/timeout.
"""
import argparse
import datetime
import functools
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — streams may not support reconfigure

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
MAX_BYTES = 256 * 1024
RUNTIMES = frozenset({"claude", "codex", "opencode", "unknown"})
TASK_STATE_FIELD = re.compile(r"^\s*-\s*\*\*Estado\*\*\s*:\s*(.*)$")
ERROR_DETAILS = {
    "review_open": "La tarea tiene una revisión abierta sin veredicto.",
    "review_not_reopened": "La revisión de la tarea requiere un veredicto con gaps para reabrirla.",
    "summary_task_outside_tasks": "--summary solo admite IDs de tarea declarados en --tasks.",
}


def load(name):
    spec = importlib.util.spec_from_file_location("ledger_write_" + name, HERE / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


LINT, READER, STATE, REDACT = (load(name) for name in ("ledger-lint", "local-read", "local-state", "redact"))


class WriteError(Exception):
    def __init__(self, status, code=2):
        self.status, self.code = status, code
        super().__init__(status)


def need(condition, status, code=2):
    if not condition:
        raise WriteError(status, code)


def guard(deadline):
    need(time.monotonic() < deadline, "timeout", 4)


IO = STATE.StateIO(READER, lambda condition, status: need(condition, status,
                   4 if status == "state_busy" else 3 if status == "conflict" else 2),
                   guard, maximum=MAX_BYTES)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def single_line(value, maximum):
    need(isinstance(value, str) and 0 < len(value) <= maximum
         and value.splitlines() == [value]
         and all(ord(char) >= 32 and ord(char) != 127 for char in value), "invalid_text")
    need(REDACT.redactar(value) == value, "unsafe_evidence")
    return value


def _source_lines(text):
    # Markdown and the fence masker use LF, not Python's extra Unicode line separators.
    pieces = text.split("\n")
    return [line + "\n" for line in pieces[:-1]] + ([pieces[-1]] if pieces[-1] else [])


def task_range(text, task, clean=None):
    """Locate editable lines only; task identity/meaning is validated by LINT."""
    if clean is None:
        clean = LINT.sin_vallas(text).split("\n")
    heading = re.compile(r"^###\s+" + re.escape(task) + r"\b")
    starts = [i for i, line in enumerate(clean) if heading.match(line)]
    need(starts, "unknown_task")
    need(len(starts) == 1, "ambiguous_task", 1)
    start = starts[0]
    stop = next((i for i in range(start + 1, len(clean))
                 if re.match(r"^##\s|^###\s+(?:T-\d+\b|Fase\b)", clean[i])), len(clean))
    return start, stop, clean


def summarize(text, previous, changes):
    def phase_counts(document, overrides):
        return {LINT.norm_fase(phase["nombre"]):
                (completed(phase["tareas"], overrides), len(phase["tareas"]))
                for phase in document["fases"]}

    def completed(tasks, overrides):
        return sum(overrides.get(task["id"], task["estado"]) == "completado" for task in tasks)

    counts, prior_counts = phase_counts(previous, changes), phase_counts(previous, {})
    done = completed(previous["tareas"], changes)
    total = len(previous["tareas"])
    prior_total = (completed(previous["tareas"], {}), total)
    lines = _source_lines(text)
    clean = LINT.sin_vallas(text).split("\n")
    has_summary = any(line.strip() == "## Resumen de progreso" for line in clean)
    summary = not has_summary
    for i, line in enumerate(clean):
        if has_summary and line.startswith("## "):
            summary = line.strip() == "## Resumen de progreso"
        if not summary:
            continue
        match = re.match(r"^\|(?P<label>[^|]+)\|(?P<done>[^|]+)\|(?P<total>[^|]+)\|(?P<pct>[^|]+)\|", line)
        if not match:
            continue
        label = match["label"].strip().strip("*").strip()
        pair = (done, total) if label.upper() == "TOTAL" else counts.get(LINT.norm_fase(label))
        prior = prior_total if label.upper() == "TOTAL" else prior_counts.get(LINT.norm_fase(label))
        if pair is None or pair == prior:
            continue
        count, size = pair
        replacements = {"done": str(count), "total": str(size), "pct": f"{100 * count / size if size else 0:.1f}%"}
        for key in ("pct", "total", "done"):
            original = match[key]
            bold = "**" if original.strip().startswith("**") else ""
            start, end = match.span(key)
            lines[i] = lines[i][:start] + f" {bold}{replacements[key]}{bold} " + lines[i][end:]
    return "".join(lines)


def phase_state(tasks):
    states = {task["estado"] or "borrador" for task in tasks}
    if states == {"cancelado"}:
        return "cancelado"
    if states <= {"borrador", "cancelado"}:
        return "borrador"
    open_states = states - {"completado", "cancelado"}
    if not open_states:
        return "completado"
    if open_states == {"en-revision"}:
        return "en-revision"
    return "en-progreso"


def set_states(text, parsed, changes, *, close=False):
    known = {task["id"]: task for task in parsed["tareas"]}
    for task, state in changes.items():
        current = known[task]
        need(state != "completado" or (current["tiene_criterios"]
             and current["checked"] > 0 and current["unchecked"] == 0), "unchecked_criteria", 1)
    actual = {task: state for task, state in changes.items() if known[task]["estado"] != state}
    if not actual:
        return text
    lines = _source_lines(text)
    clean = LINT.sin_vallas(text).split("\n")
    for task, state in actual.items():
        start, stop, _ = task_range(text, task, clean)
        hits = [i for i in range(start, stop) if TASK_STATE_FIELD.match(clean[i])]
        need(len(hits) == 1, "ambiguous_state", 1)
        i = hits[0]
        lines[i] = re.sub(r"(:)[^\n]*", r"\1 " + state, lines[i], count=1)
        if close and state == "completado" and known[task]["cerrada"] is None:
            date = datetime.date.today().isoformat()
            lines[i] = lines[i].rstrip("\n") + f"\n- **Cerrada**: {date}\n"
    phases = {phase["nombre"]: phase_state([dict(t, estado=actual.get(t["id"], t["estado"]))
              for t in phase["tareas"]]) for phase in parsed["fases"]
              if phase["estados"] and any(t["id"] in actual for t in phase["tareas"])}
    phase = None
    for i, line in enumerate(clean):
        if re.match(r"^#{2,3}\s", line):
            phase = phases.get(line[3:].strip()) if line.startswith("## ") else None
        if phase and re.match(r"^\s*\*\*Estado\*\*\s*:", line):
            lines[i] = re.sub(r"(^\s*\*\*Estado\*\*\s*:\s*)[^·\n]*?(?=\s*(?:·|$))",
                              lambda m: m[1] + phase, lines[i], count=1)
            phase = None
    return summarize("".join(lines), parsed, actual)


def verdict(text, parsed, known, tasks, args):
    sections = LINT.secciones_revision(text)
    latest = LINT.latest_reviews(sections)
    selected = [s for s in sections if s["intento"] == args.attempt
                and LINT.ids_de_tarea(s["cabecera"]) == set(tasks)]
    need(len(selected) == 1, "review_not_found_or_ambiguous", 1)
    section = selected[0]
    need(all(latest.get(task) is section for task in tasks), "superseded_review", 1)
    blocked = LINT.blocking_tasks(section, tasks)
    supplied = args.gap_tasks.split(",") if args.gap_tasks else []
    need(len(supplied) == len(set(supplied)) and set(supplied) <= set(tasks), "invalid_gap_tasks")
    if args.result == "gaps":
        gaps = set(supplied) if supplied else blocked
        need(gaps and (not blocked or gaps == blocked), "invalid_gap_tasks", 1)
    else:
        need(not supplied and not blocked, "blocking_gaps", 1)
        gaps = set()
    marker = "**Veredicto del plugin**: " + args.result
    if gaps:
        marker += " (" + ", ".join(sorted(gaps)) + ")"
    body = text[section["inicio"]:section["fin"]]
    existing = LINT._PLUGIN_VERDICT.search(LINT.sin_vallas(body))
    if existing:
        need(existing[0] == marker, "verdict_conflict", 1)
        return text
    clean_lines = LINT.sin_vallas(body).split("\n")
    placeholder = next((i for i, line in enumerate(clean_lines) if line == LINT._OPEN_REVIEW), None)
    if placeholder is None:
        body = body.rstrip("\n") + "\n\n" + marker + "\n\n"
    else:
        body_lines = _source_lines(body)
        body_lines[placeholder] = marker + "\n"
        body = "".join(body_lines)
    changes = {task: "en-progreso" for task in gaps if known[task]["estado"] != "cancelado"}
    if args.result == "limpio":
        changes = {task: "completado" for task in tasks if known[task]["estado"] != "cancelado"}
    text = text[:section["inicio"]] + body + text[section["fin"]:]
    return set_states(text, parsed, changes, close=True)


def reconcile(text, parsed, known, tasks):
    latest = LINT.latest_reviews(LINT.secciones_revision(text))
    changes = {}
    for task in tasks:
        section = latest.get(task)
        status = LINT.review_status(section) if section else None
        if not status or known[task]["estado"] == "cancelado":
            continue
        if LINT.blocking_tasks(section, {task}):
            changes[task] = "en-progreso"
        elif status in ("abierta", "gaps"):
            changes[task] = "en-revision"
        elif status == "historica" and LINT.unverified_fix(section, task):
            continue
        elif known[task]["checked"] and not known[task]["unchecked"]:
            changes[task] = "completado"
        else:
            changes[task] = "en-revision"
    return set_states(text, parsed, changes, close=True)


def handoff_current(text, args):
    """Inspect the target without projecting or validating unrelated tasks."""
    start, stop, clean = task_range(text, args.task)
    matches = [m[1] for line in clean[start + 1:stop] if (m := TASK_STATE_FIELD.match(line))]
    need(len(matches) == 1, "ambiguous_state", 1)
    current = LINT.norm_estado(matches[0])
    need(current in LINT.ESTADOS, "invalid_ledger", 1)
    if current in (args.state, "completado", "cancelado"):
        return None
    if args.state == "en-progreso":
        section = next((section for section in reversed(LINT.secciones_revision(text))
                        if args.task in LINT.menciones(section)), None)
        status = LINT.review_status(section) if section else None
        need(status != "abierta", "review_open", 1)
        if current == "en-revision":
            need(status == "gaps" and LINT.blocking_tasks(section, {args.task}),
                 "review_not_reopened", 1)
        else:
            need(current == "borrador", "invalid_handoff_state", 1)
    return current


def transform(text, parsed, args):
    known = {task["id"]: task for task in parsed["tareas"]}
    if args.operation in ("state", "red"):
        need(args.task in known, "unknown_task", 2)
        if args.operation == "state":
            return set_states(text, parsed, {args.task: args.state})
        start, stop, clean = task_range(text, args.task)
        lines = _source_lines(text)
        single_line(args.test, 512)
        single_line(args.error, 2048)
        need("`" not in args.test, "invalid_test")
        need(bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.date)), "invalid_date")
        try:
            datetime.date.fromisoformat(args.date)
        except ValueError:
            raise WriteError("invalid_date") from None
        entry = f"RED: `{args.test}` falló con {args.error} · {args.date}."
        if entry in [line.strip() for line in clean[start:stop]]:
            return text
        suffix = "".join(lines[stop:])
        prefix = "".join(lines[:stop])
        return prefix + ("\n" if prefix.endswith("\n") else "\n\n") + entry + "\n\n" + suffix
    tasks = args.tasks.split(",")
    need(tasks and len(set(tasks)) == len(tasks) and all(task in known for task in tasks), "unknown_task")
    if args.operation == "verdict":
        return verdict(text, parsed, known, tasks, args)
    if args.operation == "reconcile":
        return reconcile(text, parsed, known, tasks)
    summary = single_line(args.summary, 512)
    need(LINT.ids_de_tarea(summary) <= set(tasks), "summary_task_outside_tasks")
    # H-24: each review CYCLE has three attempts. «Seguir» after the third opens the next cycle
    # (attempts 4-6, then 7-9) only with the user's OK quoted in the header; inside a cycle the
    # sequence goes on without repeating it, and an OK anywhere else is rejected.
    opens_cycle = args.attempt > 3 and args.attempt % 3 == 1
    if args.new_cycle_ok is not None:
        need(opens_cycle, "new_cycle_ok_unexpected")
        quote = single_line(args.new_cycle_ok, 200)
        need(bool(quote.strip()) and not any(c in quote for c in "«»()"), "invalid_new_cycle_ok")
        # B3: un `T-NN` citado no es una tarea de este intento; el guion se cambia por U+2011
        # (se lee igual y `ids_de_tarea` no lo cuenta).
        quote = re.sub(r"\bT-(\d+)", "T\u2011\\1", quote.strip())
        summary += f" — ciclo {(args.attempt - 1) // 3 + 1}, abierto con OK del usuario: «{quote}»"
    else:
        need(not opens_cycle, "new_cycle_ok_required", 1)
    header = f"## Revisión de dos lentes — intento {args.attempt}: {summary} ({', '.join(tasks)})"
    sections = LINT.secciones_revision(text)
    if any(section["cabecera"] == header for section in sections):
        return text
    prior = LINT.ultimo_intento_para(sections, set(tasks))
    need(args.attempt == (prior or 0) + 1, "review_sequence", 1)
    text = set_states(text, parsed, {task: "en-revision" for task in tasks
                                     if known[task]["estado"] != "cancelado"})
    return text + ("\n" if text.endswith("\n") else "\n\n") + header + "\n\n" + LINT._OPEN_REVIEW + "\n"


def decode(raw):
    need(len(raw) <= MAX_BYTES, "ledger_budget")
    bom = b"\xef\xbb\xbf" if raw.startswith(b"\xef\xbb\xbf") else b""
    decoded = raw.decode("utf-8-sig")
    newline = "\r\n" if "\r\n" in decoded else "\n"
    text = decoded.replace("\r\n", "\n")
    need("\r" not in text and not (newline == "\r\n" and "\n" in decoded.replace("\r\n", "")), "mixed_newlines")
    return text, bom, newline


def prepare(raw, args):
    text, bom, newline = decode(raw)
    handoff = args.operation == "handoff"
    current = handoff_current(text, args) if handoff else None
    if handoff and current is None:
        return raw, [], None, None
    closed = functools.cache(lambda: LINT._closed_measurements(args.path))
    parsed = LINT.parse_ledger(text)
    errors, warnings = LINT.lint(args.path, text=text, parsed=parsed, closed_measurements=closed)
    need(not errors, "invalid_ledger", 1)
    if handoff:
        need(states_from(parsed).get(args.task) == current, "ambiguous_state", 1)
        updated = set_states(text, parsed, {args.task: args.state})
    else:
        updated = transform(text, parsed, args)
    updated_parsed = parsed
    if updated != text:
        updated_parsed = LINT.parse_ledger(updated)
        if handoff:
            # Handoffs only change nonterminal states. Their closing dates,
            # criteria and completed counts cannot change.
            need(states_from(updated_parsed).get(args.task) == args.state, "invalid_result", 1)
        else:
            errors, warnings = LINT.lint(args.path, text=updated, parsed=updated_parsed, closed_measurements=closed)
            need(not errors, "invalid_result", 1)
    output = bom + updated.replace("\n", newline).encode("utf-8")
    need(len(output) <= MAX_BYTES, "ledger_budget")
    return output, warnings, parsed, updated_parsed


def states_from(parsed):
    return {task["id"]: task["estado"] for task in parsed["tareas"]}


def _emit(path, before, after, args):
    project = LINT.ledger_project(path)
    if project is None or args.operation == "red":
        return
    old, new = states_from(before), states_from(after)
    changed = [(task, old[task], state) for task, state in new.items() if old[task] != state]
    if not changed:
        return
    runtime = args.runtime or os.environ.get("CUSTOM_AGENTS_RUNTIME")
    if runtime not in RUNTIMES:
        runtime = "unknown"
    role = "reviewer" if args.operation in ("review", "verdict") else (
        "implementer" if args.operation == "handoff" else "orchestrator")
    activity = load("agent-activity-store")
    return activity.record_task_transitions(project, path.parent.name, changed, runtime=runtime,
                                            role=role, source=args.source)


def write(args):
    path = Path(args.path).absolute()
    need(path.name == "tasks.md" and ".." not in Path(args.path).parts, "invalid_path")
    raw, identity = IO.read(path, MAX_BYTES, changed_status="conflict")
    if args.expected_sha256:
        need(digest(raw) == args.expected_sha256, "conflict", 3)
    if args.operation == "handoff" and not args.dry_run:
        # A no-op never takes the writer lock. A changing handoff validates
        # only the snapshot under that lock, even if another writer raced us.
        plan = None if handoff_current(decode(raw)[0], args) is not None else (raw, [], None, None)
    else:
        plan = prepare(raw, args)
    if not args.dry_run and (plan is None or plan[0] != raw):
        state = path.parent / ".ledger-write"
        state.mkdir(exist_ok=True)
        deadline = time.monotonic() + 5
        with IO.locked(state, deadline, True, wait=2):
            try:
                with (state / ".gitignore").open("xb") as handle:
                    handle.write(b"*\n")
            except FileExistsError:
                pass  # An existing consumer policy is never overwritten.
            locked_raw, identity = IO.read(path, MAX_BYTES, changed_status="conflict")
            if args.expected_sha256:
                need(digest(locked_raw) == args.expected_sha256, "conflict", 3)
            if locked_raw != raw or plan is None:
                raw = locked_raw
                plan = prepare(raw, args)
            output, warnings, before, after = plan
            if output != raw:
                mode = path.lstat().st_mode & 0o777 if os.name != "nt" else None
                IO.write(path, output, deadline, expected=identity, mode=mode)
                try:
                    if _emit(path, before, after, args) is False:
                        warnings.append("ledger: actividad de transición no disponible")
                except (OSError, ValueError, ImportError, RuntimeError):
                    warnings.append("ledger: actividad de transición no disponible")
    output, warnings, _, after = plan
    receipt = {"schema_version": 1, "status": "ok", "operation": args.operation,
               "changed": output != raw, "dry_run": args.dry_run,
               "input_sha256": digest(raw), "output_sha256": digest(output), "warnings": warnings}
    if args.operation == "reconcile":
        states = states_from(after)
        receipt["states"] = {task: states[task] for task in args.tasks.split(",")}
    return receipt


def task_handoff(path, task, state, source, runtime=None):
    """Optional CLI bridge for callers: bounded, no raw errors or personal paths in warnings."""
    args = [sys.executable, str(HERE / "ledger-write.py"), "handoff", str(path),
            "--task", task, "--state", state, "--source", source, "--json"]
    if runtime in RUNTIMES:
        args += ["--runtime", runtime]
    try:
        result = subprocess.run(args, capture_output=True, encoding="utf-8", errors="replace", timeout=5)
        row = json.loads(result.stdout)
        if result.returncode:
            return False, f"ledger: transición pendiente ({row['status']})"
        warning = next((message for message in row["warnings"] if message.startswith("ledger:")), None)
        return True, warning
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired):
        return False, "ledger: transición pendiente (writer no disponible)"


def measurement_target(artifact):
    match = LINT.TASK_ARTIFACT.fullmatch(artifact)
    need(match, "invalid_artifact")
    slug, task = match.groups()
    root = Path.cwd()
    folder = slug
    if not LINT.INITIATIVE_FOLDER.fullmatch(slug):
        listing = READER.list_names(root, "docs/roadmap", max_entries=512)
        need(listing["status"] != "not_found", "roadmap_unavailable")
        names = [name for name in listing["names"] if LINT.INITIATIVE_FOLDER.fullmatch(name)
                 and name[11:] == slug]
        need(listing["complete"] and len(names) == 1, "initiative_missing_or_ambiguous")
        folder = names[0]
    return str(root / "docs" / "roadmap" / folder / "tasks.md"), task


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="operation", required=True)
    for name in ("state", "handoff", "red", "review", "verdict", "reconcile"):
        sub = subs.add_parser(name)
        sub.add_argument("path", nargs="?" if name == "handoff" else None,
                         help="existing canonical tasks.md")
        sub.add_argument("--expected-sha256")
        sub.add_argument("--dry-run", action="store_true")
        sub.add_argument("--json", action="store_true")
        sub.add_argument("--runtime", choices=sorted(RUNTIMES))
        sub.set_defaults(source="ledger-write")
        if name in ("review", "verdict", "reconcile"):
            sub.add_argument("--tasks", required=True, help="comma-separated task ids")
        else:
            sub.add_argument("--task", required=name != "handoff")
        if name in ("review", "verdict"):
            sub.add_argument("--attempt", type=int, choices=range(1, 10), metavar="1-9", required=True)
        if name == "review":
            sub.add_argument("--new-cycle-ok", help="user's OK quoted when attempt 4 or 7 opens a new cycle")
            sub.add_argument("--summary", required=True)
        if name == "state":
            sub.add_argument("--state", choices=sorted(LINT.ESTADOS), required=True)
        elif name == "handoff":
            sub.add_argument("--artifact", help="usage-meter artifact key in the current project")
            sub.add_argument("--state", choices=("en-progreso", "en-revision"), required=True)
            sub.add_argument("--source", choices=("usage-meter", "task-brief"), required=True)
        elif name == "verdict":
            sub.add_argument("--result", choices=("gaps", "limpio"), required=True)
            sub.add_argument("--gap-tasks", help="comma-separated affected task ids")
        elif name == "red":
            for flag in ("--test", "--error", "--date"):
                sub.add_argument(flag, required=True)
    args = parser.parse_args(argv)
    try:
        if args.operation == "handoff":
            if args.artifact is not None:
                need(not args.path and not args.task and args.source == "usage-meter", "invalid_handoff_target")
                args.path, args.task = measurement_target(args.artifact)
            else:
                need(args.path and args.task, "invalid_handoff_target")
        row, code = write(args), 0
    except WriteError as error:
        row, code = {"schema_version": 1, "status": error.status}, error.code
        if error.status in ERROR_DETAILS:
            row["message"] = ERROR_DETAILS[error.status]
    except (OSError, UnicodeError, ValueError):
        row, code = {"schema_version": 1, "status": "unavailable"}, 2
    if args.json:
        print(json.dumps(row, ensure_ascii=False, sort_keys=True))
    else:
        detail = row.get("message") or ("changed" if row.get("changed") else "")
        print(row["status"] + (f": {detail}" if detail else ""), file=sys.stdout if not code else sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
