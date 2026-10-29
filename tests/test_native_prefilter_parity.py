"""Exact native identity parity; uncertain inputs always retain Python evaluation."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which("node")
spec = importlib.util.spec_from_file_location("prefilter_native", ROOT / "agent-kits/shared/native-guardrail.py")
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)
ROLES = json.loads((ROOT / "agent-kits/shared/native-roles.json").read_text(encoding="utf-8"))
PROGRAM = r"""
const fs = require('node:fs');
const req = JSON.parse(fs.readFileSync(0, 'utf8'));
const source = fs.readFileSync(req.source, 'utf8');
const block = source.match(/\/\/ native-prefilter:start[\s\S]*?\/\/ native-prefilter:end/);
const api = block ? new Function('fs', `${block[0]}\nreturn {guardNeedsPython, roles: PROTECTED_GUARD_ROLES, maxInput: GUARD_INPUT_MAX}`)(fs)
  : {guardNeedsPython: () => true, roles: [], maxInput: 0};
console.log(JSON.stringify({roles: api.roles, maxInput: api.maxInput, decisions: req.cases.map(row => api.guardNeedsPython(row.payload, row.runtime, req.map))}));
"""


def decisions(tmp_path, cases, mapping=ROLES, raw=None):
    if not NODE:
        pytest.skip("Node unavailable")
    path = tmp_path / "roles.json"
    path.write_bytes(raw if raw is not None else json.dumps(mapping).encode("utf-8"))
    request = {"source": str(ROOT / "hooks/run-hook.mjs"), "map": str(path), "cases": cases}
    result = subprocess.run([NODE, "-e", PROGRAM], input=json.dumps(request), capture_output=True,
                            encoding="utf-8", errors="replace", timeout=15)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


@pytest.mark.parametrize("runtime", native.RUNTIMES)
def test_prefilter_matches_exact_python_identities(tmp_path, runtime):
    key = "agent" if runtime == "opencode" else "agent_type"
    ids = ROLES["runtimes"][runtime]
    identities = ["", "main", "implementer", "architect", "custom-agents:unknown",
                  *[ids[role] for role in native.PROTECTED],
                  *[ids[role].upper() for role in native.PROTECTED],
                  *[" " + ids[role] for role in native.PROTECTED],
                  *[ids[role] + ":suffix" for role in native.PROTECTED],
                  *[ids[role] + " " for role in native.PROTECTED], "other-\u00f1-\U0001f40d"]
    payloads = [{"tool_name": "Read", "tool_input": {}, key: value} for value in identities]
    payloads += [{"tool_name": "Read", "tool_input": {"agent_type": ids["implementer"]}},
                 {"tool_name": "Read", "tool_input": {}, "agent" if key == "agent_type" else "agent_type": ids["implementer"]}]
    foreign = "agent" if key == "agent_type" else "agent_type"
    payloads += [{"tool_name": "Read", "tool_input": {}, key: ids["implementer"], foreign: "main"},
                 {"tool_name": "Read", "tool_input": {}, key: "main", foreign: ids["architect"]}]
    cases = [{"runtime": runtime, "payload": payload} for payload in payloads]
    output = decisions(tmp_path, cases)
    assert tuple(output["roles"]) == native.PROTECTED
    assert output["maxInput"] == native.MAX_INPUT
    for payload, needs_python in zip(payloads, output["decisions"]):
        evaluated = native.evaluate(payload, runtime, str(tmp_path), roles=ROLES, cfg={})
        assert needs_python is (evaluated["role"] in native.PROTECTED), payload
        if not needs_python:
            assert evaluated["decision"] == "continue" and evaluated["diagnostic"] is None


def test_uncertain_payloads_and_runtimes_never_skip_python(tmp_path):
    cases = [{"runtime": runtime, "payload": payload} for runtime in ("claude", "codex", "opencode")
             for payload in (None, [], 1, "main", {"agent_type": None, "agent": None},
                             {"agent_type": 1, "agent": {}}, {"agent_type": [], "agent": False})]
    cases += [{"runtime": runtime, "payload": {}} for runtime in ("unknown", "__proto__", None, 1)]
    assert all(decisions(tmp_path, cases)["decisions"])


@pytest.mark.parametrize("mapping", [None, [], {}, {"schema_version": 2, "runtimes": ROLES["runtimes"]},
    {"schema_version": 1, "runtimes": {"codex": {"implementer": "same", "architect": "same"}}},
    {"schema_version": 1, "runtimes": {"codex": {"implementer": "", "architect": "a"}}},
    {"schema_version": 1, "runtimes": {"codex": {"implementer": 1, "architect": "a"}}}])
def test_uncertain_map_never_skips_python(tmp_path, mapping):
    assert decisions(tmp_path, [{"runtime": "codex", "payload": {}}], mapping=mapping)["decisions"] == [True]


@pytest.mark.parametrize("raw", [b"{", b'{"schema_version":1,"runtimes":{"codex":{"implementer":"bad\xff","architect":"a"}}}', b"\xef\xbb\xbf" + json.dumps(ROLES).encode(), b" " * 65537], ids=["invalid-json", "invalid-utf8", "bom", "oversized"])
def test_invalid_map_encoding_and_size_never_skip_python(tmp_path, raw):
    assert decisions(tmp_path, [{"runtime": "codex", "payload": {}}], raw=raw)["decisions"] == [True]


def test_adapter_and_dispatcher_share_protected_role_selection(tmp_path):
    source = (ROOT / "hooks/opencode-plugin.js").read_text(encoding="utf-8")
    import re
    found = re.search(r"const PROTECTED_GUARD_ROLES = (\[[^;]+\]);", source)
    assert found, "OpenCode must expose the same protected role list for parity"
    values = json.loads(found[1].replace("'", '\"'))
    assert tuple(values) == native.PROTECTED
