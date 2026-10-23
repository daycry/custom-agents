#!/usr/bin/env python3
"""Route exact native role identities into the shared guardrail evaluator.

This adapter recognizes the supported mutation schemas; it is not a sandbox
for arbitrary shells, custom tools, or incomplete payloads. Such inputs retain
normal runtime permissions and receive a stable diagnostic where appropriate.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

MAX_INPUT = 65536
RUNTIMES = ("claude", "codex", "opencode")
PROTECTED = ("implementer", "architect")
SHARED = Path(__file__).resolve().parent
# ECMAScript whitespace for the native heredoc grammar: Python's \s also
# accepts NEL, while the native parser accepts BOM and ASCII-word delimiters.
_PATCH_WHITESPACE = (" \t\n\v\f\r\u00a0\u1680\u2000\u2001\u2002\u2003\u2004\u2005"
                     "\u2006\u2007\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000\ufeff")
_ASCII_WORD = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_")


def _json_file(path):
    with open(path, "rb") as handle:
        raw = handle.read(MAX_INPUT + 1)
    if len(raw) > MAX_INPUT:
        raise ValueError("size")
    return json.loads(raw.decode("utf-8"))


def read_config(project_dir):
    """Delegate defaults, project opt-out, and bounded reads to the evaluator."""
    return _evaluator().load_config(project_dir, max_bytes=MAX_INPUT)


def _result(role=None, reason=None, diagnostic=None):
    return {"decision": "deny" if reason else "continue", "role": role,
            "reason": reason, "diagnostic": diagnostic}


def _evaluator():
    spec = importlib.util.spec_from_file_location("custom_agents_guardrail", SHARED / "guardrail-check.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _operation(tool, path, **fields):
    if not isinstance(path, str) or not path.strip(_PATCH_WHITESPACE):
        raise ValueError("path")
    return {"tool_name": tool, "tool_input": {"file_path": path, **fields}}


def _strip_heredoc(text):
    """Unwrap an already trimmed native heredoc with one bounded linear scan.

    The closing ASCII delimiter must follow a literal LF at the end. Greedy
    opening whitespace selects the last preceding LF; body bytes stay intact.
    """
    cursor, size = 0, len(text)
    if text.startswith("cat") and size > 3 and text[3] in _PATCH_WHITESPACE:
        cursor = 3
        while cursor < size and text[cursor] in _PATCH_WHITESPACE:
            cursor += 1
    if not text.startswith("<<", cursor):
        return text
    cursor += 2
    quote = text[cursor] if cursor < size and text[cursor] in ("'", '"') else ""
    if quote:
        cursor += 1
    start = cursor
    while cursor < size and text[cursor] in _ASCII_WORD:
        cursor += 1
    if start == cursor:
        return text
    delimiter = text[start:cursor]
    if quote:
        if cursor >= size or text[cursor] != quote:
            return text
        cursor += 1
    if not text.endswith(delimiter):
        return text
    closing_lf = size - len(delimiter) - 1
    if closing_lf < cursor or text[closing_lf] != "\n":
        return text
    opening_lf = -1
    while cursor < closing_lf and text[cursor] in _PATCH_WHITESPACE:
        if text[cursor] == "\n":
            opening_lf = cursor
        cursor += 1
    if opening_lf < 0:
        return text
    return text[opening_lf + 1:closing_lf]


def parse_patch(text):
    """Extract mutations from complete native Add/Delete/Update/Move patches.

    No files are read or written. Each update chunk is evaluated independently;
    rename and delete count as whole mutations, without the design-link exception.
    """
    if not isinstance(text, str):
        raise ValueError("patch")
    # Preserve the captured body, including an invalid final blank patch line.
    text = _strip_heredoc(text.strip(_PATCH_WHITESPACE))
    # Native patch grammar separates structural lines with LF. Unicode line
    # separators and embedded CR belong to file content; only CRLF's final CR
    # is removed so those characters cannot turn a valid mutation into a gap.
    lines = [line.removesuffix("\r") for line in text.split("\n")]
    if len(lines) < 2 or lines[0].strip(_PATCH_WHITESPACE) != "*** Begin Patch" or lines[-1].strip(_PATCH_WHITESPACE) != "*** End Patch":
        raise ValueError("boundaries")
    headers = ("*** Add File: ", "*** Delete File: ", "*** Update File: ")
    operations, index, end = [], 1, len(lines) - 1
    if index < end:
        environment = lines[index].strip(_PATCH_WHITESPACE)
        prefix = "*** Environment ID:"
        if environment.startswith(prefix) and environment[len(prefix):].strip(_PATCH_WHITESPACE):
            index += 1
    while index < end:
        header = lines[index].strip(_PATCH_WHITESPACE)
        kind = next((prefix for prefix in headers if header.startswith(prefix)), None)
        if kind is None:
            raise ValueError("header")
        path, index = header[len(kind):].strip(_PATCH_WHITESPACE), index + 1
        # Collect exactly one file body. A malformed later body invalidates the
        # entire payload rather than returning a decision from a parsed prefix.
        body = []
        # Add/Delete boundaries trim indentation. Update's leading space is
        # context content, so only its trailing structural whitespace is trimmed.
        while index < end:
            boundary = (lines[index].rstrip(_PATCH_WHITESPACE) if kind == headers[2]
                        else lines[index].strip(_PATCH_WHITESPACE))
            if any(boundary.startswith(prefix) for prefix in headers):
                break
            body.append(lines[index])
            index += 1
        if kind == headers[0]:
            if any(not line.startswith("+") for line in body):
                raise ValueError("add")
            operations.append(_operation("Write", path))
        elif kind == headers[1]:
            if body:
                raise ValueError("delete")
            operations.append(_operation("Write", path))
        else:
            while body and body[0].rstrip(_PATCH_WHITESPACE) == "*** End of File":
                body.pop(0)
            moved = None
            move = body[0].rstrip(_PATCH_WHITESPACE) if body else ""
            if move == "*** Move to:" or move.startswith("*** Move to: "):
                moved = body.pop(0)[len("*** Move to:"):].strip(_PATCH_WHITESPACE)
                if not moved:
                    raise ValueError("move")
            chunks, old, new, after_eof = [], [], [], False
            for line in body:
                marker = line.rstrip(_PATCH_WHITESPACE)
                is_hunk = marker == "@@" or marker.startswith("@@ ")
                if after_eof:
                    if marker == "":
                        continue
                    if not is_hunk:
                        raise ValueError("after-eof")
                    after_eof = False
                if marker == "*** End of File":
                    if old or new:
                        chunks.append((old, new))
                        old, new, after_eof = [], [], True
                    continue
                if is_hunk:
                    if old or new:
                        chunks.append((old, new))
                        old, new = [], []
                    continue
                if line == "" or line.startswith(" "):
                    old.append(line[1:] if line else "")
                    new.append(line[1:] if line else "")
                elif line.startswith("-"):
                    old.append(line[1:])
                elif line.startswith("+"):
                    new.append(line[1:])
                else:
                    raise ValueError("update")
            if old or new:
                chunks.append((old, new))
            if moved is not None:
                operations.extend((_operation("Write", path), _operation("Write", moved)))
            elif chunks:
                operations.extend(_operation("Edit", path, old_string="\n".join(a), new_string="\n".join(b))
                                  for a, b in chunks)
            else:
                raise ValueError("empty-update")
    return operations


def normalize(payload, runtime):
    """Return canonical operations or raise for incomplete recognized inputs."""
    tool, inputs = payload.get("tool_name"), payload.get("tool_input", {})
    supported = {
        "claude": {"Write", "Edit", "MultiEdit", "NotebookEdit", "Bash", "PowerShell"},
        "codex": {"Bash", "apply_patch"},
        "opencode": {"write", "edit", "patch", "shell"},
    }
    if not isinstance(tool, str) or tool not in supported[runtime]:
        return []
    if runtime == "opencode":
        tool = {"write": "Write", "edit": "Edit", "patch": "apply_patch", "shell": "Bash"}.get(tool, tool)
    if runtime == "claude" and tool == "PowerShell":
        tool = "Bash"
    if tool == "apply_patch" and runtime in ("codex", "opencode"):
        patch = inputs if isinstance(inputs, str) else inputs.get("patchText" if runtime == "opencode" else "command") if isinstance(inputs, dict) else None
        return parse_patch(patch)
    if tool not in ("Write", "Edit", "MultiEdit", "NotebookEdit", "Bash"):
        return []
    if not isinstance(inputs, dict):
        raise ValueError("input")
    if tool == "Bash":
        command = inputs.get("command")
        if not isinstance(command, str):
            raise ValueError("command")
        return [{"tool_name": "Bash", "tool_input": {"command": command}}]
    paths = [inputs[key] for key in ("file_path", "notebook_path", "path", "filePath") if key in inputs]
    if tool == "MultiEdit":
        edits = inputs.get("edits")
        if not isinstance(edits, list) or not edits:
            raise ValueError("edits")
        operations = []
        for edit in edits:
            if not isinstance(edit, dict):
                raise ValueError("edit")
            old, new = edit.get("old_string"), edit.get("new_string")
            if not isinstance(old, str) or not isinstance(new, str):
                raise ValueError("edit")
            targets = paths + ([edit["file_path"]] if "file_path" in edit else [])
            if not targets:
                raise ValueError("targets")
            operations.extend(_operation("Edit", path, old_string=old, new_string=new) for path in targets)
        return operations
    if not paths:
        raise ValueError("targets")
    fields = {}
    if tool == "Edit":
        old = inputs.get("oldString" if runtime == "opencode" else "old_string")
        new = inputs.get("newString" if runtime == "opencode" else "new_string")
        if not isinstance(old, str) or not isinstance(new, str):
            raise ValueError("edit")
        fields = {"old_string": old, "new_string": new}
    return [_operation("Edit" if tool == "Edit" else "Write", path, **fields) for path in paths]


def evaluate(payload, runtime, project_dir, *, roles=None, cfg=None, branch_fn=None):
    """Select only exact native protected IDs; never select from tool input."""
    if runtime not in RUNTIMES or not isinstance(payload, dict):
        return _result(diagnostic="input-unrecognized")
    try:
        mapping = roles if roles is not None else _json_file(SHARED / "native-roles.json")
        candidates = mapping["runtimes"][runtime]
        if mapping.get("schema_version") != 1 or not all(isinstance(candidates.get(key), str) and candidates[key] for key in PROTECTED) or candidates[PROTECTED[0]] == candidates[PROTECTED[1]]:
            raise ValueError("map")
    except (OSError, ValueError, UnicodeError, KeyError, TypeError, AttributeError):
        return _result(diagnostic="role-map-unavailable")
    identity = payload.get("agent" if runtime == "opencode" else "agent_type")
    role = next((key for key in PROTECTED if identity == candidates[key]), None)
    if role is None:
        return _result()
    try:
        if cfg is None:
            cfg, active = read_config(project_dir)
            if not active:
                return _result(role, diagnostic="guardrails-disabled")
        operations = normalize(payload, runtime)
        if not operations:
            return _result(role)
        evaluator = _evaluator()
        branch_unavailable, queried, branch = False, False, None

        def query(directory):
            nonlocal branch_unavailable, queried, branch
            if not queried:
                branch = branch_fn(directory) if branch_fn is not None else evaluator.current_branch(directory, timeout=0.5)
                queried = True
                branch_unavailable = branch is None
            return branch

        for operation in operations:
            reason = evaluator.decide(operation, project_dir, cfg=cfg, branch_fn=query, agent=role)
            if reason:
                reason = "".join(char if char.isprintable() else " " for char in reason)[:2048]
                return _result(role, reason, "branch-unavailable" if branch_unavailable else None)
        return _result(role, diagnostic="branch-unavailable" if branch_unavailable else None)
    except (ValueError, TypeError, KeyError):
        return _result(role, diagnostic="input-unrecognized")
    except Exception:
        return _result(role, diagnostic="evaluator-unavailable")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", required=True, choices=RUNTIMES)
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--output", choices=("native", "structured"), default="native")
    args = parser.parse_args()
    try:
        raw = sys.stdin.buffer.read(MAX_INPUT + 1)
        if len(raw) > MAX_INPUT:
            result = _result(diagnostic="input-too-large")
        else:
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (ValueError, UnicodeError):
                result = _result(diagnostic="input-invalid-json")
            else:
                result = evaluate(payload, args.runtime, args.project_dir)
    except Exception:
        result = _result(diagnostic="input-unavailable")
    if result["diagnostic"]:
        print("native-guardrail: " + result["diagnostic"], file=sys.stderr)
    if args.output == "structured":
        print(json.dumps(result, ensure_ascii=False))
    elif result["decision"] == "deny":
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": result["reason"]}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
