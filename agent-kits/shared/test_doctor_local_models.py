"""Local model context is diagnosed without inferring server settings."""
import importlib.util
import json
from pathlib import Path
import socket
import threading
import time
import socketserver
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("doctor_local_test", HERE / "doctor.py")
doctor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(doctor)


def isolate(monkeypatch):
    for name, key in [("bloque_herramientas", "herramientas"), ("bloque_plugin", "plugin"),
                      ("bloque_configs", "configs"), ("bloque_estado", "estado"),
                      ("bloque_capacidades", "capacidades"), ("bloque_memoria", "memoria"),
                      ("bloque_journal", "journal"), ("bloque_version", "version")]:
        monkeypatch.setattr(doctor, name, lambda *a, _key=key, **k: {"clave": _key, "lineas": []})
    monkeypatch.setattr(doctor, "localizar_plugin", lambda *a: None)
    monkeypatch.setattr(doctor, "inventario_automatizaciones", lambda *a: [])


@pytest.mark.parametrize("runtime,context,expected", [
    ("codex", 32768, "aviso"), ("opencode", 65536, "ok"), ("codex", None, "aviso"),
])
def test_explicit_native_context_is_declared_and_default_never_uses_network(tmp_path, monkeypatch, capsys, runtime, context, expected):
    isolate(monkeypatch)
    if runtime == "codex":
        (tmp_path / ".codex").mkdir()
        text = 'model = "qwen3:32b"\nmodel_provider = "ollama"\n'
        if context is not None:
            text += "model_context_window = " + str(context) + "\n"
        (tmp_path / ".codex/config.toml").write_text(text, encoding="utf-8")
    else:
        data = {"model": "ollama/qwen3:32b", "providers": {"ollama": {"models": {"qwen3:32b": {"limit": {"context": context}}}}}}
        (tmp_path / "opencode.json").write_text(json.dumps(data), encoding="utf-8")
    before = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    calls = []
    monkeypatch.setattr(socket, "socket", lambda *a, **k: calls.append(a) or pytest.fail("unexpected network"))
    assert doctor.main(["--root", str(tmp_path), "--runtime", runtime, "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    block = next(row for row in report["bloques"] if row["clave"] == "modelos_locales")
    row = block["lineas"][0]
    assert row["estado"] == expected
    assert row["contexto"] == context
    assert row["fuente_contexto"] == ("declarado" if context else "desconocido")
    assert row["minimo_orientativo"] == 65536
    if expected == "aviso":
        assert row["arreglo"]
    assert calls == []
    assert before == {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}


@pytest.fixture
def local_project(tmp_path):
    (tmp_path / ".codex").mkdir()
    (tmp_path / ".codex/config.toml").write_text('model = "qwen3:32b"\nmodel_provider = "ollama"\nmodel_context_window = 65536\n', encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize("redirect", [False, True])
def test_explicit_probe_observes_loaded_context_and_never_follows_redirects(local_project, monkeypatch, capsys, redirect):
    isolate(monkeypatch)
    calls = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            calls.append((self.path, dict(self.headers)))
            body = json.dumps({"models": [{"name": "qwen3:32b", "context_length": 8192}]}).encode()
            self.send_response(302 if redirect else 200)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Content-Type", "application/json")
            if redirect:
                self.send_header("Location", "http://198.51.100.23/forbidden")
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("HTTP_PROXY", "http://198.51.100.23:9999")
    monkeypatch.setenv("HTTPS_PROXY", "http://198.51.100.23:9999")
    try:
        endpoint = "http://127.0.0.1:" + str(server.server_port)
        assert doctor.main(["--root", str(local_project), "--runtime", "codex", "--probe-ollama", endpoint, "--json"]) == 0
        report = json.loads(capsys.readouterr().out)
        row = next(b for b in report["bloques"] if b["clave"] == "modelos_locales")["lineas"][0]
        assert row["estado"] == "aviso"
        assert row["sondeo"] == ("error" if redirect else "ok")
        if not redirect:
            assert row["contexto"] == 8192 and row["fuente_contexto"] == "observado"
        assert len(calls) == 1 and calls[0][0] == "/api/ps"
        assert not any(key.lower() in ("authorization", "proxy-authorization", "cookie") for key in calls[0][1])
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
        assert not thread.is_alive()


@pytest.mark.parametrize("endpoint", [
    "http://example.com", "http://192.168.1.2", "https://127.0.0.1", "http://user:pass@127.0.0.1",
    "http://127.0.0.1/other", "http://127.0.0.1/?key=fixture", "http://127.0.0.1\r\nInjected: value", "http://127.0.0.1:0",
])
def test_probe_rejects_nonlocal_or_ambiguous_endpoints_before_opening_socket(local_project, monkeypatch, capsys, endpoint):
    isolate(monkeypatch)
    monkeypatch.setattr(socket, "socket", lambda *a, **k: pytest.fail("must reject before network"))
    assert doctor.main(["--root", str(local_project), "--runtime", "codex", "--probe-ollama", endpoint, "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    row = next(b for b in data["bloques"] if b["clave"] == "modelos_locales")["lineas"][0]
    assert row["estado"] == "aviso" and row["sondeo"] == "error"
    assert "sondeo" in row["detalle"].lower() and "loopback" in row["arreglo"].lower()
    assert "user:pass" not in json.dumps(data)


@pytest.mark.parametrize("runtime", ["codex", "opencode"])
def test_own_agent_context_is_checked_even_when_parent_has_a_larger_window(tmp_path, runtime):
    role = "custom-agents-implementer"
    if runtime == "codex":
        folder = tmp_path / ".codex/agents"
        folder.mkdir(parents=True)
        (tmp_path / ".codex/config.toml").write_text('model = "qwen3:8b"\nmodel_provider = "ollama"\nmodel_context_window = 65536\n[agents.' + role + ']\nconfig_file = "agents/' + role + '.toml"\n', encoding="utf-8")
        (folder / (role + ".toml")).write_text('name = "' + role + '"\nmodel = "qwen3:32b"\nmodel_context_window = 8192\n', encoding="utf-8")
    else:
        folder = tmp_path / ".opencode/agents"
        folder.mkdir(parents=True)
        (tmp_path / "opencode.json").write_text(json.dumps({"model": "ollama/qwen3:8b", "providers": {"ollama": {"models": {"qwen3:8b": {"limit": {"context": 65536}}, "qwen3:32b": {"limit": {"context": 8192}}}}}}), encoding="utf-8")
        (folder / (role + ".md")).write_text('---\nmodel: "ollama/qwen3:32b"\n---\nOwn fixture instructions.\n', encoding="utf-8")
    block = doctor.bloque_modelos_locales(str(tmp_path), runtime)
    child = next(row for row in block["lineas"] if row.get("agente") == role)
    # Codex 0.166 does not apply model_context_window from a role TOML.
    assert child["estado"] == "aviso" and child["contexto"] == (None if runtime == "codex" else 8192)


def test_anonymous_server_entry_never_becomes_observed_context_for_an_unselected_model(tmp_path, monkeypatch):
    monkeypatch.setattr(doctor, "_ollama_running", lambda endpoint: [{"context_length": 65536}])
    rows = doctor.bloque_modelos_locales(str(tmp_path), "codex", probe_ollama="http://127.0.0.1")["lineas"]
    assert all(row["contexto"] is None and row["estado"] == "aviso" for row in rows)


@pytest.mark.parametrize("runtime", ["codex", "opencode"])
def test_dev_model_resolution_uses_the_selected_runtime(tmp_path, monkeypatch, runtime):
    calls = []
    monkeypatch.setattr(doctor, "_modelos_localizar_script", lambda root: "owned-model-tier.py")
    monkeypatch.setattr(doctor, "_correr", lambda args: (calls.append(args) or json.dumps({"agentes": [], "avisos": []}), True))
    rows = doctor._modelos({"modelos": {"implementer": {"model": "ollama/qwen3:32b"}}}, None, str(tmp_path), runtime=runtime)
    assert rows and calls
    assert calls[0][calls[0].index("--runtime") + 1] == runtime


def test_shared_native_config_is_not_reported_as_verified(local_project):
    import os
    os.link(local_project / ".codex/config.toml", local_project / "shared.toml")
    row = doctor.bloque_modelos_locales(str(local_project), "codex")["lineas"][0]
    assert row["estado"] == "aviso" and row["contexto"] is None


def test_codex_namespace_is_not_mistaken_for_a_provider_prefix(local_project, monkeypatch):
    (local_project / ".codex/config.toml").write_text('model = "ollama/qwen3:32b"\nmodel_provider = "ollama"\n', encoding="utf-8")
    monkeypatch.setattr(doctor, "_ollama_running", lambda endpoint: [{"name": "qwen3:32b", "context_length": 65536}])
    row = doctor.bloque_modelos_locales(str(local_project), "codex", probe_ollama="http://127.0.0.1")["lineas"][0]
    assert row["contexto"] is None and row["estado"] == "aviso"


def test_opencode_alias_uses_the_explicit_native_model_id(tmp_path, monkeypatch):
    (tmp_path / "opencode.json").write_text(json.dumps({"model": "ollama/coding", "providers": {"ollama": {"models": {"coding": {"modelID": "qwen3:32b", "limit": {"context": 65536}}}}}}), encoding="utf-8")
    monkeypatch.setattr(doctor, "_ollama_running", lambda endpoint: [{"name": "qwen3:32b", "context_length": 8192}])
    row = doctor.bloque_modelos_locales(str(tmp_path), "opencode", probe_ollama="http://127.0.0.1")["lineas"][0]
    assert row["contexto"] == 8192 and row["fuente_contexto"] == "observado"


@contextmanager
def response_fixture(reply, drip=False):
    stop = threading.Event()

    class Handler(socketserver.BaseRequestHandler):
        def handle(self):
            try:
                self.request.recv(4096)
                if drip:
                    for value in reply:
                        if stop.wait(0.15):
                            break
                        self.request.sendall(bytes([value]))
                else:
                    self.request.sendall(reply)
            except OSError:
                pass

    server = socketserver.TCPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
    thread.start()
    try:
        yield "http://127.0.0.1:" + str(server.server_address[1])
    finally:
        stop.set()
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
        assert not thread.is_alive()


@pytest.mark.parametrize("reply", [
    b"HTTP/1.1 200 OK\r\nContent-Length: 262145\r\n\r\n",
    b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nContent-Length: 2\r\n\r\n{}",
    b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n0\r\n\r\n",
    b"HTTP/1.1 200 OK\r\nContent-Length: 100\r\n\r\n{}",
    b"HTTP/1.1 200 OK\r\n\r\n{\"models\":{}}",
])
def test_probe_rejects_oversized_ambiguous_or_incomplete_responses(reply):
    with response_fixture(reply) as endpoint:
        with pytest.raises((OSError, ValueError)):
            doctor._ollama_running(endpoint)


def test_probe_deadline_includes_slow_http_headers():
    with response_fixture(b"HTTP/1.1 200 OK\r\n\r\n{\"models\":[]}", drip=True) as endpoint:
        start = time.monotonic()
        with pytest.raises((OSError, ValueError)):
            doctor._ollama_running(endpoint)
        assert time.monotonic() - start < 5


def test_corrupt_provider_schema_warns_before_probe(tmp_path, monkeypatch):
    (tmp_path / "opencode.json").write_text('{"model":"ollama/qwen3:32b","providers":[]}', encoding="utf-8")
    calls = []
    monkeypatch.setattr(doctor, "_ollama_running", lambda endpoint: calls.append(endpoint) or [])
    rows = doctor.bloque_modelos_locales(str(tmp_path), "opencode", probe_ollama="http://127.0.0.1")["lineas"]
    assert rows[0]["estado"] == "aviso" and calls == []


def test_deep_native_json_degrades_without_a_traceback(tmp_path):
    (tmp_path / "opencode.json").write_text('{"a":' * 10000 + "0" + "}" * 10000, encoding="utf-8")
    rows = doctor.bloque_modelos_locales(str(tmp_path), "opencode")["lineas"]
    assert rows[0]["estado"] == "aviso" and rows[0]["contexto"] is None


def test_deep_probe_json_is_a_controlled_invalid_response():
    body = b'{"models":[' + b"[" * 10000 + b"0" + b"]" * 10000 + b"]}"
    reply = b"HTTP/1.1 200 OK\r\nContent-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body
    with response_fixture(reply) as endpoint:
        with pytest.raises(ValueError):
            doctor._ollama_running(endpoint)


def test_codex_child_does_not_assume_the_parent_context_window(local_project):
    folder = local_project / ".codex/agents"
    folder.mkdir()
    (folder / "custom-agents-implementer.toml").write_text('name = "custom-agents-implementer"\nmodel = "qwen3:32b"\n', encoding="utf-8")
    child = next(row for row in doctor.bloque_modelos_locales(str(local_project), "codex")["lineas"]
                 if row.get("agente") == "custom-agents-implementer")
    assert child["estado"] == "aviso" and child["contexto"] is None


@pytest.mark.parametrize("header", [
    '---invalid\nmodel: "ollama/qwen3:32b"\n---\n',
    '---\nmodel: "ollama/qwen3:32b"\nmissing delimiter\n',
    '---\nmodel:\n"ollama/qwen3:32b"\n---\n',
])
def test_ambiguous_markdown_model_header_is_not_a_valid_context_declaration(tmp_path, header):
    folder = tmp_path / ".opencode/agents"
    folder.mkdir(parents=True)
    (folder / "custom-agents-implementer.md").write_text(header, encoding="utf-8")
    (tmp_path / "opencode.json").write_text(json.dumps({"providers": {"ollama": {"models": {"qwen3:32b": {"limit": {"context": 65536}}}}}}), encoding="utf-8")
    child = next(row for row in doctor.bloque_modelos_locales(str(tmp_path), "opencode")["lineas"]
                 if row.get("agente") == "custom-agents-implementer")
    assert child["estado"] == "aviso" and child["contexto"] is None
