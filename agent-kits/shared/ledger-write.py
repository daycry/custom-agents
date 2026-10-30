#!/usr/bin/env python3
"""Write selected canonical ledger fields, RED evidence or a review header.

The canonical parser/linter owns interpretation; local-state owns cooperative
locking and atomic publication. This tool does not judge evidence or approve QA.
Exit 0 success, 1 invalid ledger, 2 input/I/O, 3 conflict, 4 busy/timeout.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — streams may not support reconfigure

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
MAX_BYTES = 256 * 1024


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


def task_range(text, task):
    """Locate editable lines only; task identity/meaning is validated by LINT."""
    clean = LINT.sin_vallas(text).splitlines()
    starts = [i for i, line in enumerate(clean) if re.match(r"^###\s+" + re.escape(task) + r"\b", line)]
    need(len(starts) == 1, "ambiguous_task", 1)
    start = starts[0]
    stop = next((i for i in range(start + 1, len(clean))
                 if re.match(r"^##\s|^###\s+(?:T-\d+\b|Fase\b)", clean[i])), len(clean))
    return start, stop, clean


def summarize(text, previous):
    parsed = LINT.parse_ledger(text)
    def phase_counts(document):
        return {LINT.norm_fase(phase["nombre"]):
                (sum(task["estado"] == "completado" for task in phase["tareas"]), len(phase["tareas"]))
                for phase in document["fases"]}
    counts, prior_counts = phase_counts(parsed), phase_counts(previous)
    done = sum(task["estado"] == "completado" for task in parsed["tareas"])
    total = len(parsed["tareas"])
    prior_total = (sum(task["estado"] == "completado" for task in previous["tareas"]), len(previous["tareas"]))
    lines = text.splitlines(keepends=True)
    clean = LINT.sin_vallas(text).splitlines()
    for i, line in enumerate(clean):
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


def transform(text, args):
    parsed = LINT.parse_ledger(text)
    errors, _ = LINT.lint(args.path, text=text, parsed=parsed)
    need(not errors, "invalid_ledger", 1)
    known = {task["id"]: task for task in parsed["tareas"]}
    if args.operation in ("state", "red"):
        need(args.task in known, "unknown_task", 2)
        start, stop, clean = task_range(text, args.task)
        lines = text.splitlines(keepends=True)
        if args.operation == "state":
            need(args.state != "completado" or (known[args.task]["tiene_criterios"]
                 and known[args.task]["checked"] > 0 and known[args.task]["unchecked"] == 0), "unchecked_criteria", 1)
            hits = [i for i in range(start, stop) if re.match(r"^\s*-\s*\*\*Estado\*\*\s*:", clean[i])]
            need(len(hits) == 1, "ambiguous_state", 1)
            if known[args.task]["estado"] == args.state:
                return text
            i = hits[0]
            lines[i] = re.sub(r"(:)[^\n]*", r"\1 " + args.state, lines[i], count=1)
            return summarize("".join(lines), parsed)
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
    summary = single_line(args.summary, 512)
    header = f"## Revisión de dos lentes — intento {args.attempt}: {summary} ({', '.join(tasks)})"
    sections = LINT.secciones_revision(text)
    if any(section["cabecera"] == header for section in sections):
        return text
    prior = LINT.ultimo_intento_para(sections, set(tasks))
    need(args.attempt == (prior or 0) + 1, "review_sequence", 1)
    return text + ("\n" if text.endswith("\n") else "\n\n") + header + "\n\nPendiente de revisión; sin veredicto.\n"


def prepare(raw, args):
    need(len(raw) <= MAX_BYTES, "ledger_budget")
    bom = b"\xef\xbb\xbf" if raw.startswith(b"\xef\xbb\xbf") else b""
    decoded = raw.decode("utf-8-sig")
    newline = "\r\n" if "\r\n" in decoded else "\n"
    text = decoded.replace("\r\n", "\n")
    need("\r" not in text and not (newline == "\r\n" and "\n" in decoded.replace("\r\n", "")), "mixed_newlines")
    updated = transform(text, args)
    errors, warnings = LINT.lint(args.path, text=updated)
    need(not errors, "invalid_result", 1)
    output = bom + updated.replace("\n", newline).encode("utf-8")
    need(len(output) <= MAX_BYTES, "ledger_budget")
    return output, warnings


def write(args):
    path = Path(args.path).absolute()
    need(path.name == "tasks.md" and ".." not in Path(args.path).parts, "invalid_path")
    raw, identity = IO.read(path, MAX_BYTES, changed_status="conflict")
    if args.expected_sha256:
        need(digest(raw) == args.expected_sha256, "conflict", 3)
    output, warnings = prepare(raw, args)
    if not args.dry_run and output != raw:
        state = path.parent / ".ledger-write"
        state.mkdir(exist_ok=True)
        deadline = time.monotonic() + 5
        with IO.locked(state, deadline, True, wait=2):
            try:
                with (state / ".gitignore").open("xb") as handle:
                    handle.write(b"*\n")
            except FileExistsError:
                pass  # An existing consumer policy is never overwritten.
            raw, identity = IO.read(path, MAX_BYTES, changed_status="conflict")
            if args.expected_sha256:
                need(digest(raw) == args.expected_sha256, "conflict", 3)
            output, warnings = prepare(raw, args)
            if output != raw:
                mode = path.lstat().st_mode & 0o777 if os.name != "nt" else None
                IO.write(path, output, deadline, expected=identity, mode=mode)
    return {"schema_version": 1, "status": "ok", "operation": args.operation,
            "changed": output != raw, "dry_run": args.dry_run,
            "input_sha256": digest(raw), "output_sha256": digest(output), "warnings": warnings}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="operation", required=True)
    for name in ("state", "red", "review"):
        sub = subs.add_parser(name)
        sub.add_argument("path", help="existing canonical tasks.md")
        sub.add_argument("--expected-sha256")
        sub.add_argument("--dry-run", action="store_true")
        sub.add_argument("--json", action="store_true")
        if name == "review":
            sub.add_argument("--attempt", type=int, choices=(1, 2, 3), required=True)
            sub.add_argument("--tasks", required=True, help="comma-separated task ids")
            sub.add_argument("--summary", required=True)
        else:
            sub.add_argument("--task", required=True)
        if name == "state":
            sub.add_argument("--state", choices=sorted(LINT.ESTADOS), required=True)
        elif name == "red":
            for flag in ("--test", "--error", "--date"):
                sub.add_argument(flag, required=True)
    args = parser.parse_args(argv)
    try:
        row, code = write(args), 0
    except WriteError as error:
        row, code = {"schema_version": 1, "status": error.status}, error.code
    except (OSError, UnicodeError, ValueError):
        row, code = {"schema_version": 1, "status": "unavailable"}, 2
    if args.json:
        print(json.dumps(row, ensure_ascii=False, sort_keys=True))
    else:
        print(row["status"] + (": changed" if row.get("changed") else ""), file=sys.stdout if not code else sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
