"""Observe the plugin's state changes over the authenticated console API."""
import hashlib
import json
import subprocess
import sys
import time

import pytest

from test_control_center_http import ROOT, login, request, server


@pytest.mark.parametrize("runtime", ["claude", "codex", "opencode"])
def test_task_transition_on_board_and_activity_within_seven_seconds(server, runtime):
    assert server.server_port != 8769
    root = server.workspaces["one"].root
    slug = "2026-10-31-pilot"
    plan = hashlib.sha256(slug.encode()).hexdigest()[:16]
    prefix = "/api/workspaces/one/"
    cookie = login(server)

    def get(route):
        status, _, raw = request(server, prefix + route, cookie=cookie)
        assert status == 200
        return json.loads(raw)

    assert "borrador" in json.dumps(get("plans/" + plan))
    assert get("activity").get("task_transitions", []) == []
    first = time.monotonic()
    result = subprocess.run([sys.executable, str(ROOT / "agent-kits/shared/usage-meter.py"),
        "start", "--artefacto", slug + "/T-01", "--runtime", runtime, "--state", "usage.json"],
        cwd=root, capture_output=True, encoding="utf-8", timeout=7)
    assert result.returncode == 0, result.stderr
    board_at = activity_at = None
    while time.monotonic() - first < 7 and (board_at is None or activity_at is None):
        if board_at is None and "en-progreso" in json.dumps(get("plans/" + plan)):
            board_at = time.monotonic() - first
        if activity_at is None:
            view = get("activity")
            for event in view.get("task_transitions", []):
                if event["task"] == "T-01" and event["to"] == "en-progreso":
                    assert event["runtime"] == runtime and event["from"] == "borrador"
                    assert first and view["runs"] == []
                    activity_at = time.monotonic() - first
        if board_at is None or activity_at is None:
            time.sleep(min(2, max(0, 7 - (time.monotonic() - first))))
    assert board_at is not None and board_at <= 7
    assert activity_at is not None and activity_at <= 7
    print(f"{runtime}: tablero {board_at:.3f} s, actividad {activity_at:.3f} s")
