"""Contracts for native identity selection and mutation normalization."""
import importlib.util
import io
import json
from pathlib import Path
import queue
import subprocess
import sys
import threading

import pytest

SCRIPT = Path(__file__).with_name("native-guardrail.py")
ROLES = {"schema_version": 1, "runtimes": {
    runtime: {role: ("custom-agents:" if runtime == "claude" else "custom-agents-") + role
              for role in ("implementer", "architect", "planner")}
    for runtime in ("claude", "codex", "opencode")}}


def load_module():
    spec = importlib.util.spec_from_file_location("native_guardrail_tests", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def event(runtime, role, tool, inputs):
    key = "agent" if runtime == "opencode" else "agent_type"
    return {key: ROLES["runtimes"][runtime][role], "tool_name": tool, "tool_input": inputs}


def evaluate(payload, runtime="claude", module=None, **kwargs):
    return (module or load_module()).evaluate(payload, runtime, "project", roles=ROLES,
                                             cfg={"alcance": True, "git": True, "ramaPrincipal": True},
                                             branch_fn=lambda _: "feature/test", **kwargs)


@pytest.mark.parametrize("runtime,tool,inputs", [
    ("claude", "Write", {"file_path": "docs/roadmap/x/spec.md", "content": "x"}),
    ("codex", "apply_patch", {"command": "*** Begin Patch\n*** Add File: docs/roadmap/x/spec.md\n+x\n*** End Patch"}),
    ("opencode", "write", {"filePath": "docs/roadmap/x/spec.md", "content": "x"}),
])
def test_native_protected_identity_denies_forbidden_write(runtime, tool, inputs):
    result = evaluate(event(runtime, "implementer", tool, inputs), runtime)
    assert result["decision"] == "deny"
    assert result["role"] == "implementer"


@pytest.mark.parametrize("runtime", ["claude", "codex", "opencode"])
@pytest.mark.parametrize("branch", ["main", "feature/first-task"])
def test_unborn_branch_is_evaluated_without_degradation(runtime, branch, tmp_path):
    subprocess.run(["git", "init", "-q", "-b", branch], cwd=tmp_path, check=True,
                   capture_output=True)
    tool, inputs = {
        "claude": ("Write", {"file_path": "src/app.py", "content": "x"}),
        "codex": ("apply_patch", {"command": "*** Begin Patch\n*** Add File: src/app.py\n+x\n*** End Patch"}),
        "opencode": ("write", {"filePath": "src/app.py", "content": "x"}),
    }[runtime]
    result = load_module().evaluate(event(runtime, "implementer", tool, inputs), runtime,
                                    str(tmp_path), roles=ROLES,
                                    cfg={"alcance": True, "git": True, "ramaPrincipal": True})
    assert result["diagnostic"] is None
    assert result["decision"] == ("deny" if branch == "main" else "continue")


@pytest.mark.parametrize("runtime", ["claude", "codex", "opencode"])
@pytest.mark.parametrize("identity", [None, "implementer", "architect", "consumer-agent", "custom-agents-planner"])
def test_unprotected_identity_does_not_query_config_or_branch(runtime, identity, monkeypatch, tmp_path):
    module = load_module()
    monkeypatch.setattr(module, "read_config", lambda _: pytest.fail("unprotected config read"))
    payload = {"tool_name": "Bash", "tool_input": {"command": "git push --force", "agent_type": "custom-agents-implementer"}}
    payload["agent" if runtime == "opencode" else "agent_type"] = identity
    result = module.evaluate(payload, runtime, str(tmp_path), roles=ROLES,
                             branch_fn=lambda _: pytest.fail("unprotected branch query"))
    assert result["decision"] == "continue"
    assert result["role"] is None


@pytest.mark.parametrize("tool,inputs", [
    ("Edit", {"file_path": "docs/roadmap/x/spec.md", "old_string": "a", "new_string": "b"}),
    ("NotebookEdit", {"notebook_path": "docs/roadmap/x/spec.md", "new_source": "x"}),
    ("MultiEdit", {"file_path": "src/a", "edits": [{"old_string": "a", "new_string": "b"}, {"file_path": "docs/roadmap/x/spec.md", "old_string": "a", "new_string": "b"}]}),
])
def test_all_claude_mutation_targets_checked(tool, inputs):
    assert evaluate(event("claude", "implementer", tool, inputs))["decision"] == "deny"


@pytest.mark.parametrize("runtime,tool,inputs", [
    ("claude", "Edit", {"file_path": "docs/roadmap/x/spec.md", "old_string": "title", "new_string": "design: design.md"}),
    ("opencode", "edit", {"filePath": "docs/roadmap/x/spec.md", "oldString": "title", "newString": "design: design.md"}),
    ("codex", "apply_patch", {"command": "*** Begin Patch\n*** Update File: docs/roadmap/x/spec.md\n@@\n-title\n+design: design.md\n*** End Patch"}),
])
def test_architect_partial_link_edit_allowed(runtime, tool, inputs):
    assert evaluate(event(runtime, "architect", tool, inputs), runtime)["decision"] == "continue"


@pytest.mark.parametrize("runtime,tool,inputs", [
    ("claude", "Write", {"file_path": "docs/roadmap/x/spec.md", "content": "design: design.md"}),
    ("opencode", "write", {"filePath": "docs/roadmap/x/spec.md", "content": "design: design.md"}),
    ("codex", "apply_patch", "*** Begin Patch\n*** Add File: docs/roadmap/x/spec.md\n+design: design.md\n*** End Patch"),
])
def test_architect_whole_write_link_still_denied(runtime, tool, inputs):
    assert evaluate(event(runtime, "architect", tool, inputs), runtime)["decision"] == "deny"


@pytest.mark.parametrize("runtime,key", [("codex", "command"), ("opencode", "patchText")])
@pytest.mark.parametrize("source,dest", [("docs/roadmap/x/spec.md", "src/moved"), ("src/a", "docs/roadmap/x/spec.md")])
def test_patch_move_checks_original_and_destination(runtime, key, source, dest):
    patch = f"*** Begin Patch\n*** Update File: {source}\n*** Move to: {dest}\n@@\n-a\n+b\n*** End Patch"
    tool = "apply_patch" if runtime == "codex" else "patch"
    assert evaluate(event(runtime, "implementer", tool, {key: patch}), runtime)["decision"] == "deny"


def test_architect_move_cannot_use_link_exception():
    patch = "*** Begin Patch\n*** Update File: docs/roadmap/x/spec.md\n*** Move to: docs/roadmap/y/spec.md\n@@\n-title\n+design: design.md\n*** End Patch"
    assert evaluate(event("codex", "architect", "apply_patch", {"command": patch}), "codex")["decision"] == "deny"


@pytest.mark.parametrize("runtime,tool", [("claude", "Bash"), ("claude", "PowerShell"), ("codex", "Bash"), ("opencode", "shell")])
def test_shell_commands_use_central_policy(runtime, tool):
    assert evaluate(event(runtime, "architect", tool, {"command": "git push --force"}), runtime)["decision"] == "deny"


@pytest.mark.parametrize("patch", [
    "*** Begin Patch\n*** Add File: docs/roadmap/x/spec.md\n+x",
    "*** Begin Patch\n*** Add File: x\nbad\n*** End Patch",
    "*** Begin Patch\n*** Update File: x\n@@\n?bad\n*** End Patch",
    "*** Begin Patch\n*** Delete File: x\n+bad\n*** End Patch",
])
def test_incomplete_patch_degrades_visibly_without_partial_decision(patch):
    result = evaluate(event("codex", "implementer", "apply_patch", {"command": patch}), "codex")
    assert result["decision"] == "continue"
    assert result["diagnostic"] == "input-unrecognized"


def test_independent_multi_edit_changes_do_not_share_design_marker():
    inputs = {"edits": [{"file_path": "docs/roadmap/x/spec.md", "old_string": "a", "new_string": "design: design.md"},
                        {"file_path": "docs/roadmap/y/spec.md", "old_string": "a", "new_string": "b"}]}
    assert evaluate(event("claude", "architect", "MultiEdit", inputs))["decision"] == "deny"


def run_cli(tmp_path, payload, output="structured"):
    return subprocess.run([sys.executable, "-I", "-S", str(SCRIPT), "--runtime", "codex", "--project-dir", str(tmp_path), "--output", output],
                          input=payload, capture_output=True, encoding="utf-8", errors="replace", timeout=10)


def test_cli_malformed_payload_sanitized(tmp_path):
    result = run_cli(tmp_path, "private-secret not JSON")
    assert result.returncode == 0
    assert json.loads(result.stdout)["diagnostic"] == "input-invalid-json"
    assert "private-secret" not in result.stdout + result.stderr


def test_cli_bounds_payload_before_parsing(tmp_path):
    result = run_cli(tmp_path, "private-secret" * 6000)
    assert result.returncode == 0
    assert json.loads(result.stdout)["diagnostic"] == "input-too-large"
    assert "private-secret" not in result.stdout + result.stderr


@pytest.mark.parametrize("tool", ["write", "edit"])
def test_opencode_native_path_schema(tool):
    inputs = {"path": "docs/roadmap/x/spec.md", "oldString": "a", "newString": "b", "content": "x"}
    assert evaluate(event("opencode", "implementer", tool, inputs), "opencode")["decision"] == "deny"


def test_multi_file_patch_later_protected_target():
    patch = "*** Begin Patch\n*** Add File: src/a\n+x\n*** Delete File: docs/roadmap/x/spec.md\n*** End Patch"
    assert evaluate(event("codex", "implementer", "apply_patch", {"command": patch}), "codex")["decision"] == "deny"


@pytest.mark.parametrize("patch", [
    "<<'EOF'\n*** Begin Patch\n*** Add File: src/a\n+x\n*** End Patch\nEOF",
    "*** Begin Patch\n*** Environment ID: local\n*** Update File: src/a\n@@\n a\n-x\n+y\n*** End of File\n*** End Patch",
    "*** Begin Patch\n*** Update File: src/a\n*** Move to: src/b\n*** End Patch",
])
def test_complete_patch_variants_preserve_normal_permissions(patch):
    assert evaluate(event("codex", "implementer", "apply_patch", {"command": patch}), "codex")["decision"] == "continue"


@pytest.mark.parametrize("patch", [
    "*** Begin Patch\n*** Invalid File: x\n*** End Patch",
    "*** Begin Patch\n*** Update File: x\n*** Move to: \n*** End Patch",
    "*** Begin Patch\n*** Update File: x\n*** End Patch",
    "*** Begin Patch\n*** Add File: \n+x\n*** End Patch",
])
def test_invalid_complete_patch_degrades_visibly(patch):
    assert evaluate(event("codex", "implementer", "apply_patch", {"command": patch}), "codex")["diagnostic"] == "input-unrecognized"


@pytest.mark.parametrize("tool,inputs", [
    ("Bash", {"command": []}), ("Write", {}), ("Write", []),
    ("Edit", {"file_path": "x", "old_string": 12, "new_string": "x"}),
    ("MultiEdit", {"edits": []}), ("MultiEdit", {"edits": [12]}),
    ("MultiEdit", {"edits": [{"old_string": "x", "new_string": "y"}]}),
    ("MultiEdit", {"file_path": "src/a", "edits": [{"old_string": 12, "new_string": "design: design.md"}]}),
])
def test_incomplete_mutation_schema_degrades_visibly(tool, inputs):
    assert evaluate(event("claude", "implementer", tool, inputs))["diagnostic"] == "input-unrecognized"


def test_unknown_tool_continues_without_loading_evaluator(monkeypatch):
    module = load_module()
    monkeypatch.setattr(module, "_evaluator", lambda: pytest.fail("unknown evaluator loaded"))
    assert evaluate(event("claude", "architect", "Read", {}), module=module)["decision"] == "continue"


def test_unknown_runtime_and_invalid_payload():
    module = load_module()
    assert module.evaluate({}, "claimed", "project", roles=ROLES)["diagnostic"] == "input-unrecognized"
    assert module.evaluate([], "claude", "project", roles=ROLES)["diagnostic"] == "input-unrecognized"


@pytest.mark.parametrize("roles", [{}, {"schema_version": 2, "runtimes": ROLES["runtimes"]},
                                    {"schema_version": 1, "runtimes": {"claude": {"implementer": "same", "architect": "same"}}}])
def test_invalid_role_map_degrades_visibly(roles):
    result = load_module().evaluate(event("claude", "architect", "Write", {"file_path": "src/a"}), "claude", "project", roles=roles)
    assert result["diagnostic"] == "role-map-unavailable"


def test_config_defaults_optout_and_individual_switches(tmp_path):
    module = load_module()
    assert module.read_config(tmp_path)[1] is True
    config = tmp_path / ".claude" / "dev.json"
    config.parent.mkdir()
    config.write_text(json.dumps({"guardrails": False}), encoding="utf-8")
    payload = event("claude", "architect", "Write", {"file_path": "src/a"})
    assert module.evaluate(payload, "claude", str(tmp_path), roles=ROLES)["diagnostic"] == "guardrails-disabled"
    config.write_text(json.dumps({"guardrails": {"alcance": False, "git": False}}), encoding="utf-8")
    assert module.evaluate(payload, "claude", str(tmp_path), roles=ROLES)["decision"] == "continue"
    config.write_text("{}" * 40000, encoding="utf-8")
    assert module.read_config(tmp_path)[0]["alcance"] is True


def test_branch_unknown_visible_and_queried_once():
    calls = []
    def branch(directory):
        calls.append(directory)
        return None
    patch = "*** Begin Patch\n*** Add File: src/a\n+x\n*** Add File: src/b\n+y\n*** End Patch"
    result = load_module().evaluate(event("codex", "implementer", "apply_patch", {"command": patch}), "codex", "project", roles=ROLES, cfg={"alcance": True, "ramaPrincipal": True}, branch_fn=branch)
    assert result["decision"] == "continue"
    assert result["diagnostic"] == "branch-unavailable"
    assert calls == ["project"]


def test_evaluator_failure_does_not_expose_error(monkeypatch):
    module = load_module()
    def fail():
        raise RuntimeError("private-secret")
    monkeypatch.setattr(module, "_evaluator", fail)
    result = evaluate(event("claude", "implementer", "Write", {"file_path": "src/a"}), module=module)
    assert result["diagnostic"] == "evaluator-unavailable"
    assert "private-secret" not in json.dumps(result)


def test_cli_native_denies_and_continue_has_no_forced_permission(tmp_path):
    payload = event("codex", "architect", "apply_patch", {"command": "*** Begin Patch\n*** Add File: src/a\n+x\n*** End Patch"})
    result = run_cli(tmp_path, json.dumps(payload), output="native")
    assert result.returncode == 0
    assert json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"
    result = run_cli(tmp_path, json.dumps({"tool_name": "Bash", "tool_input": {"command": "git push --force"}}), output="native")
    assert result.stdout == ""


@pytest.mark.parametrize("runtime,tool", [("codex", "Write"), ("opencode", "Write"), ("opencode", "Bash")])
def test_non_native_tool_alias_does_not_select_policy(runtime, tool):
    result = evaluate(event(runtime, "architect", tool, {"file_path": "src/a", "command": "git push --force"}), runtime)
    assert result["decision"] == "continue"


@pytest.mark.parametrize("raw,output,decision,diagnostic", [
    (b"private-secret invalid-json", "structured", "continue", "input-invalid-json"),
    (b"x" * 65537, "structured", "continue", "input-too-large"),
    (b"\xff", "native", "continue", "input-invalid-json"),
    (b'{}', "native", "continue", None),
    (json.dumps(event("codex", "architect", "apply_patch", {"command": "*** Begin Patch\n*** Add File: src/a\n+x\n*** End Patch"})).encode(), "native", "deny", None),
], ids=["invalid-json", "oversize", "invalid-utf8", "normal-permissions", "native-deny"])
def test_main_outputs_are_sanitized_and_do_not_grant_permission(raw, output, decision, diagnostic, tmp_path, monkeypatch, capsys):
    module = load_module()
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--runtime", "codex", "--project-dir", str(tmp_path), "--output", output])
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(raw), encoding="utf-8"))
    assert module.main() == 0
    captured = capsys.readouterr()
    assert "private-secret" not in captured.out + captured.err
    if output == "structured":
        result = json.loads(captured.out)
        assert result["decision"] == decision
        assert result["diagnostic"] == diagnostic
    elif decision == "deny":
        assert json.loads(captured.out)["hookSpecificOutput"]["permissionDecision"] == "deny"
    else:
        assert captured.out == ""


def test_main_stdin_failure_is_visible(tmp_path, monkeypatch, capsys):
    module = load_module()
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--runtime", "codex", "--project-dir", str(tmp_path), "--output", "structured"])
    monkeypatch.setattr(sys, "stdin", None)
    assert module.main() == 0
    assert json.loads(capsys.readouterr().out)["diagnostic"] == "input-unavailable"


def test_branch_default_uses_bounded_central_api(monkeypatch):
    module = load_module()
    evaluator = module._evaluator()
    queries = []
    def branch(project, timeout):
        queries.append((project, timeout))
        return None
    monkeypatch.setattr(evaluator, "current_branch", branch)
    monkeypatch.setattr(module, "_evaluator", lambda: evaluator)
    result = module.evaluate(event("codex", "architect", "Bash", {"command": "git status"}), "codex", "project", roles=ROLES, cfg={"git": True})
    assert result["diagnostic"] == "branch-unavailable"
    assert queries == [("project", 0.5)]


def test_patch_preceding_eof_and_blank_context():
    patch = "*** Begin Patch\n*** Update File: src/a\n*** End of File\n@@\n\n-a\n+b\n*** End Patch"
    assert evaluate(event("codex", "implementer", "apply_patch", {"command": patch}), "codex")["decision"] == "continue"


def test_nonstring_patch_degrades_visibly():
    assert evaluate(event("codex", "architect", "apply_patch", {"command": 3}), "codex")["diagnostic"] == "input-unrecognized"


@pytest.mark.parametrize("runtime,key,tool", [("codex", "command", "apply_patch"), ("opencode", "patchText", "patch")])
@pytest.mark.parametrize("separator", ["\u0085", "\u2028", "\u2029", "\r"], ids=["nel", "line-separator", "paragraph-separator", "embedded-cr"])
def test_patch_unicode_content_protected_add_still_denied(runtime, key, tool, separator):
    patch = f"*** Begin Patch\n*** Add File: docs/roadmap/x/spec.md\n+a{separator}b\n*** End Patch"
    result = evaluate(event(runtime, "implementer", tool, {key: patch}), runtime)
    assert result["decision"] == "deny"
    assert result["diagnostic"] is None


@pytest.mark.parametrize("runtime,key,tool", [("codex", "command", "apply_patch"), ("opencode", "patchText", "patch")])
def test_patch_crlf_structure_keeps_protected_add_denied(runtime, key, tool):
    patch = "*** Begin Patch\r\n*** Add File: docs/roadmap/x/spec.md\r\n+a\r\n*** End Patch\r\n"
    result = evaluate(event(runtime, "implementer", tool, {key: patch}), runtime)
    assert result["decision"] == "deny"
    assert result["diagnostic"] is None


@pytest.mark.parametrize("runtime,key,tool", [("codex", "command", "apply_patch"), ("opencode", "patchText", "patch")])
@pytest.mark.parametrize("separator", ["\u0085", "\u2028", "\u2029", "\r"], ids=["nel", "line-separator", "paragraph-separator", "embedded-cr"])
def test_patch_unicode_content_independent_update_cannot_share_design_marker(runtime, key, tool, separator):
    patch = ("*** Begin Patch\n*** Update File: docs/roadmap/x/spec.md\n@@\n-title\n+design: design.md\n"
             f"@@ second\n-a{separator}b\n+c{separator}d\n*** End Patch")
    result = evaluate(event(runtime, "architect", tool, {key: patch}), runtime)
    assert result["decision"] == "deny"
    assert result["diagnostic"] is None


@pytest.mark.parametrize("runtime,key,tool", [("codex", "command", "apply_patch"), ("opencode", "patchText", "patch")])
@pytest.mark.parametrize("separator", ["\u0085", "\u2028", "\u2029", "\r"], ids=["nel", "line-separator", "paragraph-separator", "embedded-cr"])
def test_patch_unicode_content_partial_design_edit_preserves_strings(runtime, key, tool, separator):
    patch = ("*** Begin Patch\r\n*** Update File: docs/roadmap/x/spec.md\r\n@@\r\n"
             f"-title{separator}tail\r\n+design: design.md{separator}tail\r\n*** End Patch\r\n")
    payload = event(runtime, "architect", tool, {key: patch})
    operations = load_module().normalize(payload, runtime)
    assert len(operations) == 1
    assert operations[0]["tool_input"]["old_string"] == f"title{separator}tail"
    assert operations[0]["tool_input"]["new_string"] == f"design: design.md{separator}tail"
    result = evaluate(payload, runtime)
    assert result["decision"] == "continue"
    assert result["diagnostic"] is None


@pytest.mark.parametrize("runtime,key,tool", [("codex", "command", "apply_patch"), ("opencode", "patchText", "patch")])
@pytest.mark.parametrize("context", ["*** Add File: d\u00e9mo\u2028.md", "*** Delete File: d\u00e9mo\u2028.md", "*** Update File: d\u00e9mo\u2028.md"])
def test_patch_header_like_context_keeps_protected_update_denied(runtime, key, tool, context):
    patch = f"*** Begin Patch\n*** Update File: src/a\n@@\n {context}\n-old\n+new\n*** End Patch"
    payload = event(runtime, "architect", tool, {key: patch})
    result = evaluate(payload, runtime)
    assert result["decision"] == "deny"
    assert result["diagnostic"] is None
    operations = load_module().normalize(payload, runtime)
    assert len(operations) == 1
    assert operations[0]["tool_input"]["file_path"] == "src/a"
    assert operations[0]["tool_input"]["old_string"] == context + "\nold"
    assert operations[0]["tool_input"]["new_string"] == context + "\nnew"


@pytest.mark.parametrize("runtime,key,tool", [("codex", "command", "apply_patch"), ("opencode", "patchText", "patch")])
@pytest.mark.parametrize("context", ["@@", "@@ hint", "*** End of File", "*** Move to: d\u00e9mo.md"])
def test_patch_hunk_like_context_keeps_partial_edit_content(runtime, key, tool, context):
    patch = f"*** Begin Patch\n*** Update File: docs/roadmap/x/spec.md\n@@\n {context}\n-title\n+design: design.md\n*** End Patch"
    payload = event(runtime, "architect", tool, {key: patch})
    operations = load_module().normalize(payload, runtime)
    assert len(operations) == 1
    assert operations[0]["tool_input"]["old_string"] == context + "\ntitle"
    assert operations[0]["tool_input"]["new_string"] == context + "\ndesign: design.md"
    result = evaluate(payload, runtime)
    assert result["decision"] == "continue"
    assert result["diagnostic"] is None


@pytest.mark.parametrize("wrapper", [
    "*** Begin Patch\n*** Environment ID:own\n{body}\n*** End Patch",
    "<<PATCH\n{patch}\nPATCH",
    "<<'PATCH'\n{patch}\nPATCH",
    '<<"PATCH_12"\n{patch}\nPATCH_12',
    "cat <<'PATCH'\n{patch}\nPATCH",
    "cat\t<<123\n{patch}\n123",
    "cat\u00a0<<_PATCH\n{patch}\n_PATCH",
    "cat\ufeff<<'PATCH'\r\n{patch}\r\nPATCH",
    "<<'PATCH'\n\n{patch}\nPATCH",
], ids=["environment-no-space", "bare-label", "single-quote", "double-quote-word", "cat", "cat-tab-numeric", "cat-nbsp", "cat-bom-crlf", "opening-whitespace"])
@pytest.mark.parametrize("path,decision", [("docs/roadmap/x/spec.md", "deny"), ("docs/roadmap/x/tasks.md", "continue")])
def test_native_opencode_patch_wrappers_keep_scope_decisions(wrapper, path, decision):
    body = f"*** Add File: {path}\n+a\u2028b\u0085c\rd"
    patch = "*** Begin Patch\n" + body + "\n*** End Patch"
    wrapped = wrapper.format(body=body, patch=patch)
    result = evaluate(event("opencode", "implementer", "patch", {"patchText": wrapped}), "opencode")
    assert result["decision"] == decision
    assert result["diagnostic"] is None
    assert load_module().normalize(event("opencode", "implementer", "patch", {"patchText": wrapped}), "opencode") == [
        {"tool_name": "Write", "tool_input": {"file_path": path}}]


@pytest.mark.parametrize("wrapper", [
    "<<'PATCH\"\n{patch}\nPATCH",
    "<<'PATCH'\n{patch}\nOTHER",
    "<<'PATCH-DIFF'\n{patch}\nPATCH-DIFF",
    "<<'\u00e9PATCH'\n{patch}\n\u00e9PATCH",
    "<<''\n{patch}\n",
    "<< 'PATCH'\n{patch}\nPATCH",
    "sh <<'PATCH'\n{patch}\nPATCH",
    "cat<<'PATCH'\n{patch}\nPATCH",
    "cat\u0085<<'PATCH'\n{patch}\nPATCH",
    "<<'PATCH'\n{patch}\nPATCH; echo extra",
    "\u0085<<'PATCH'\n{patch}\nPATCH",
    "<<'PATCH'\n{patch}\n\nPATCH",
], ids=["mismatched-quotes", "mismatched-label", "hyphen-label", "non-ascii-label", "empty-label", "space-after-shift", "other-command", "cat-no-space", "cat-nel", "trailing-command", "leading-nel", "empty-last-body-line"])
def test_invalid_native_opencode_heredoc_remains_unrecognized(wrapper):
    patch = "*** Begin Patch\n*** Add File: docs/roadmap/x/spec.md\n+x\n*** End Patch"
    result = evaluate(event("opencode", "implementer", "patch", {"patchText": wrapper.format(patch=patch)}), "opencode")
    assert result["decision"] == "continue"
    assert result["diagnostic"] == "input-unrecognized"


@pytest.mark.parametrize("environment", ["*** Environment ID:", "*** Environment ID: \t", "*** Environment ID-own"])
def test_empty_or_invalid_native_environment_remains_unrecognized(environment):
    patch = f"*** Begin Patch\n{environment}\n*** Add File: docs/roadmap/x/spec.md\n+x\n*** End Patch"
    result = evaluate(event("opencode", "implementer", "patch", {"patchText": patch}), "opencode")
    assert result["decision"] == "continue"
    assert result["diagnostic"] == "input-unrecognized"


def test_native_wrapped_context_edit_preserves_partial_design_strings():
    context = "*** Add File: d\u00e9mo\u2028.md"
    patch = ("cat <<'PATCH'\r\n*** Begin Patch\r\n*** Environment ID:own\r\n"
             f"*** Update File: docs/roadmap/x/spec.md\r\n@@\r\n {context}\r\n"
             "-title\rinside\r\n+design: design.md\rinside\r\n*** End Patch\r\nPATCH")
    payload = event("opencode", "architect", "patch", {"patchText": patch})
    operations = load_module().normalize(payload, "opencode")
    assert len(operations) == 1
    assert operations[0]["tool_input"]["old_string"] == context + "\ntitle\rinside"
    assert operations[0]["tool_input"]["new_string"] == context + "\ndesign: design.md\rinside"
    result = evaluate(payload, "opencode")
    assert result["decision"] == "continue"
    assert result["diagnostic"] is None


@pytest.mark.parametrize("first", ["add", "delete"])
@pytest.mark.parametrize("following", ["add", "delete", "update"])
@pytest.mark.parametrize("indent", ["  ", "\ufeff"], ids=["spaces", "bom"])
@pytest.mark.parametrize("path,decision", [("docs/roadmap/x/spec.md", "deny"), ("docs/roadmap/x/tasks.md", "continue")])
def test_opencode_add_delete_boundaries_check_indented_later_targets(first, following, indent, path, decision):
    opening = "*** Add File: src/a\n+x" if first == "add" else "*** Delete File: src/a"
    next_header = {"add": f"*** Add File: {path}\n+y", "delete": f"*** Delete File: {path}",
                   "update": f"*** Update File: {path}\n@@\n-old\n+new"}[following]
    patch = f"*** Begin Patch\n{opening}\n{indent}{next_header}\n*** End Patch"
    payload = event("opencode", "implementer", "patch", {"patchText": patch})
    result = evaluate(payload, "opencode")
    assert result["decision"] == decision
    assert result["diagnostic"] is None
    operations = load_module().normalize(payload, "opencode")
    assert [item["tool_input"]["file_path"] for item in operations] == ["src/a", path]
    assert [item["tool_name"] for item in operations] == ["Write", "Edit" if following == "update" else "Write"]


@pytest.mark.parametrize("location", ["header", "path", "hunk", "eof"])
@pytest.mark.parametrize("path,decision", [("docs/roadmap/x/spec.md", "deny"), ("docs/roadmap/x/tasks.md", "continue")])
def test_opencode_bom_structural_whitespace_keeps_scope(location, path, decision):
    if location == "header":
        body = f"\ufeff*** Add File: {path}\n+x"
    elif location == "path":
        body = f"*** Add File: \ufeff{path}\ufeff\n+x"
    else:
        marker = "@@\ufeff" if location == "hunk" else "@@"
        suffix = "\n*** End of File\ufeff" if location == "eof" else ""
        body = f"*** Update File: {path}\n{marker}\n-old\n+new{suffix}"
    payload = event("opencode", "implementer", "patch", {"patchText": f"*** Begin Patch\n{body}\n*** End Patch"})
    result = evaluate(payload, "opencode")
    assert result["decision"] == decision
    assert result["diagnostic"] is None
    assert load_module().normalize(payload, "opencode")[0]["tool_input"]["file_path"] == path


@pytest.mark.parametrize("whitespace", ["", "  ", "\t", "\u00a0", "\ufeff"])
def test_opencode_after_eof_whitespace_does_not_hide_protected_next_file(whitespace):
    patch = ("*** Begin Patch\n*** Update File: src/a\n@@\n-old\n+new\n*** End of File\n"
             f"{whitespace}\n*** Add File: docs/roadmap/x/spec.md\n+x\n*** End Patch")
    result = evaluate(event("opencode", "implementer", "patch", {"patchText": patch}), "opencode")
    assert result["decision"] == "deny"
    assert result["diagnostic"] is None


def test_opencode_after_eof_whitespace_does_not_create_spurious_edit():
    patch = ("*** Begin Patch\n*** Update File: docs/roadmap/x/spec.md\n@@\n-title\n+design: design.md\n"
             "*** End of File\n \ufeff\n@@\n-old\n+design: other/design.md\n*** End Patch")
    payload = event("opencode", "architect", "patch", {"patchText": patch})
    result = evaluate(payload, "opencode")
    assert result["decision"] == "continue"
    assert result["diagnostic"] is None
    operations = load_module().normalize(payload, "opencode")
    assert len(operations) == 2
    assert operations[1]["tool_input"]["old_string"] == "old"


@pytest.mark.parametrize("body", [
    "\u0085*** Add File: docs/roadmap/x/spec.md\n+x",
    "*** Update File: docs/roadmap/x/spec.md\n@@\u0085\n-old\n+new",
    "*** Update File: src/a\n*** Move to:docs/roadmap/x/spec.md\n@@\n-old\n+new",
    "*** Update File: docs/roadmap/x/spec.md\n@@\n-old\n+new\n*** End of File\n+extra",
    "*** Update File: docs/roadmap/x/spec.md\n@@\n-old\n+new\n*** End of File\n\u0085",
])
def test_invalid_opencode_marker_grammar_keeps_native_permissions(body):
    patch = f"*** Begin Patch\n{body}\n*** End Patch"
    result = evaluate(event("opencode", "implementer", "patch", {"patchText": patch}), "opencode")
    assert result["decision"] == "continue"
    assert result["diagnostic"] == "input-unrecognized"


@pytest.mark.parametrize("runtime,key,tool", [("codex", "command", "apply_patch"), ("opencode", "patchText", "patch")])
@pytest.mark.parametrize("following", ["add", "delete", "update"])
@pytest.mark.parametrize("path,decision", [("docs/roadmap/x/spec.md", "deny"), ("docs/roadmap/x/tasks.md", "continue")])
def test_r5_nel_filename_does_not_hide_later_patch_target(runtime, key, tool, following, path, decision):
    next_hunk = {"add": f"*** Add File: {path}\n+second\u2028tail", "delete": f"*** Delete File: {path}",
                 "update": f"*** Update File: {path}\n@@\n-old\u0085value\n+new\u0085value"}[following]
    patch = f"*** Begin Patch\n*** Add File: \u0085\n+first\u2029tail\n{next_hunk}\n*** End Patch"
    payload = event(runtime, "implementer", tool, {key: patch})
    result = evaluate(payload, runtime)
    assert result["decision"] == decision
    assert result["diagnostic"] is None
    operations = load_module().normalize(payload, runtime)
    assert [item["tool_input"]["file_path"] for item in operations] == ["\u0085", path]
    assert operations[0]["tool_input"]["file_path"].encode("utf-8") == b"\xc2\x85"
    if following == "update":
        assert operations[1]["tool_input"]["old_string"] == "old\u0085value"
        assert operations[1]["tool_input"]["new_string"] == "new\u0085value"
    assert payload["tool_input"][key].encode("utf-8") == patch.encode("utf-8")


@pytest.mark.parametrize("path,decision", [("docs/roadmap/x/spec.md", "deny"), ("docs/roadmap/x/tasks.md", "continue")])
def test_r5_claude_nel_filename_does_not_hide_later_multiedit_target(path, decision):
    inputs = {"edits": [{"file_path": "\u0085", "old_string": "first\u2028old", "new_string": "first\u2028new"},
                        {"file_path": path, "old_string": "second\u0085old", "new_string": "second\u0085new"}]}
    payload = event("claude", "implementer", "MultiEdit", inputs)
    result = evaluate(payload)
    assert result["decision"] == decision
    assert result["diagnostic"] is None
    operations = load_module().normalize(payload, "claude")
    assert [item["tool_input"]["file_path"] for item in operations] == ["\u0085", path]
    assert operations[0]["tool_input"]["old_string"].encode("utf-8") == "first\u2028old".encode("utf-8")
    assert operations[1]["tool_input"]["new_string"].encode("utf-8") == "second\u0085new".encode("utf-8")


@pytest.mark.parametrize("runtime,tool,inputs", [
    ("claude", "Write", {"file_path": "\u0085", "content": "content"}),
    ("codex", "apply_patch", {"command": "*** Begin Patch\n*** Add File: \u0085\n+content\n*** End Patch"}),
    ("opencode", "write", {"path": "\u0085", "content": "content"}),
])
def test_r5_nel_filename_preserved_in_supported_path_schema(runtime, tool, inputs):
    payload = event(runtime, "implementer", tool, inputs)
    result = evaluate(payload, runtime)
    assert result["decision"] == "continue"
    assert result["diagnostic"] is None
    operations = load_module().normalize(payload, runtime)
    assert operations[0]["tool_input"]["file_path"].encode("utf-8") == b"\xc2\x85"


@pytest.mark.parametrize("case,decision,diagnostic", [
    ("missing-close", "continue", "input-unrecognized"),
    ("mixed-close", "continue", "input-unrecognized"),
    ("protected", "deny", None),
    ("allowed", "continue", None),
])
def test_r6_large_native_heredoc_returns_bounded_decision_after_ready(case, decision, diagnostic):
    prefix = "cat <<'PATCH'\n" + "\n" * 16000
    if case == "missing-close":
        patch = prefix + "x"
    elif case == "mixed-close":
        patch = prefix + "x\nOTHER"
    else:
        path = "docs/roadmap/x/spec.md" if case == "protected" else "docs/roadmap/x/tasks.md"
        patch = prefix + f"*** Begin Patch\n*** Add File: {path}\n+x\u2028y\u0085z\rw\n*** End Patch\nPATCH"
    raw = json.dumps(event("opencode", "implementer", "patch", {"patchText": patch}))
    assert len(raw.encode("utf-8")) <= 65536
    worker = """import importlib.util, json, sys
spec = importlib.util.spec_from_file_location('native_guardrail_ready', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
print('READY', flush=True)
payload = json.loads(sys.stdin.read())
result = module.evaluate(payload, 'opencode', 'project', cfg={'alcance': True, 'git': False, 'ramaPrincipal': False}, branch_fn=lambda _: 'feature/owned')
print(json.dumps(result), flush=True)
"""
    process = subprocess.Popen([sys.executable, "-I", "-S", "-u", "-c", worker, str(SCRIPT)],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, encoding="utf-8")
    ready = queue.Queue()
    reader = threading.Thread(target=lambda: ready.put(process.stdout.readline()), daemon=True)
    reader.start()
    try:
        assert ready.get(timeout=20) == "READY\n"
        reader.join(timeout=1)
        try:
            output, stderr = process.communicate(raw, timeout=4)
        except subprocess.TimeoutExpired:
            pytest.fail("native heredoc evaluation exceeded 4s after READY")
        assert process.returncode == 0, stderr
        assert len(output.encode("utf-8")) <= 65536
        result = json.loads(output)
        assert result["decision"] == decision
        assert result["diagnostic"] == diagnostic
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=5)


def test_r6_native_heredoc_keeps_last_literal_closer_and_body_exact():
    context = "PATCH\u2028opaque\u0085context\rinside"
    patch = ("cat\t<<\"PATCH\"\r\n\r\n*** Begin Patch\r\n"
             f"*** Update File: docs/roadmap/x/spec.md\r\n@@\r\n {context}\r\n"
             "-title\r\n+design: design.md\r\n*** End Patch\r\nPATCH\ufeff\r\n")
    payload = event("opencode", "architect", "patch", {"patchText": patch})
    operations = load_module().normalize(payload, "opencode")
    assert len(operations) == 1
    assert operations[0]["tool_input"]["old_string"] == context + "\ntitle"
    assert operations[0]["tool_input"]["new_string"] == context + "\ndesign: design.md"
    result = evaluate(payload, "opencode")
    assert result["decision"] == "continue"
    assert result["diagnostic"] is None
