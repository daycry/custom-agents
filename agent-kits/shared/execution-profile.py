#!/usr/bin/env python3
"""Resolve an explicit project execution profile. Read-only, stdlib only.

Exit 0 usable, 2 blocked profile/writer. JSON uses ASCII escaping; no stdin.
This script never dispatches roles, changes config or grants a quality verdict.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import stat
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent


def read_config(project, dev_json=None):
    path = Path(dev_json).absolute() if dev_json else Path(project).absolute() / ".claude/dev.json"
    spec = importlib.util.spec_from_file_location("profile_local_read", HERE / "local-read.py")
    reader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reader)
    row = reader.read_bytes(path.parent if dev_json else Path(project).absolute(),
                            path.name if dev_json else ".claude/dev.json", max_bytes=256 * 1024)
    if row["status"] == "not_found":
        return {}, []
    try:
        if row["status"] != "ok" or path.lstat().st_nlink != 1:
            raise ValueError("unavailable config")
        data = json.loads(row["data"].decode("utf-8-sig"))
        if not isinstance(data, dict):
            raise ValueError("non-object config")
        return data, []
    except (OSError, ValueError, UnicodeError, RecursionError):
        return {}, ["dev.json unavailable or invalid; normal defaults, lite not verified"]


def writer_available(shared_dir):
    directory = Path(shared_dir)
    for name in ("ledger-write.py", "ledger-lint.py", "local-read.py", "local-state.py", "redact.py"):
        try:
            info = (directory / name).lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                return False
        except OSError:
            return False
    try:
        result = subprocess.run([sys.executable, "-I", "-S", str(directory / "ledger-write.py"), "--help"],
                                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=2)
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def resolve(project, *, dev_json=None, shared_dir=None):
    data, warnings = read_config(project, dev_json)
    selected = data.get("perfil", "normal")
    valid = isinstance(selected, str) and selected in ("normal", "lite")
    if not valid:
        warnings.append("invalid perfil: choose normal or lite; dispatch blocked")
    lite = valid and selected == "lite"
    writer = writer_available(HERE if shared_dir is None else shared_dir)
    if not writer:
        warnings.append("ledger writer unavailable; restore this bundle" if lite else
                        "ledger writer unavailable; ordinary manual fallback with ledger-lint")
    return {"schema_version": 1, "perfil": selected if valid else "unknown",
            "brief_max_chars": 6000 if lite else 10000,
            "subagentes": False if lite else data.get("subagentes") is True,
            "paralelismo": False if lite else data.get("paralelismo", True) is True,
            "tdd": data.get("tdd") is True, "worktree": data.get("worktree") is True,
            "reviewers": "fresh_sequential" if lite or data.get("paralelismo") is False else "fresh_parallel",
            "review_required": True, "qa_gate": True,
            "writer_required": lite, "writer_available": writer,
            "blocked": not valid or (lite and not writer), "warnings": warnings}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default=".")
    parser.add_argument("--dev-json")
    parser.add_argument("--json", action="store_true", help="stable JSON (also the default)")
    args = parser.parse_args(argv)
    try:
        row = resolve(args.project, dev_json=args.dev_json)
    except (OSError, ImportError, ValueError):
        row = {"schema_version": 1, "blocked": True,
               "warnings": ["profile resolver dependencies unavailable; profile not verified"]}
    print(json.dumps(row, ensure_ascii=True, sort_keys=True))
    return 2 if row["blocked"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
