"""HTTP budgets of the documentary adapter, using owned loopback fixtures only."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import threading
import time
import urllib.error
from unittest import mock

import pytest
from http.server import BaseHTTPRequestHandler, HTTPServer


@pytest.fixture
def adapter():
    path = Path(__file__).parents[1] / "backends" / "markdown_export.py"
    spec = importlib.util.spec_from_file_location("bounded_documentary_adapter", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@contextlib.contextmanager
def server(responses):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            options = responses[self.path]
            try:
                time.sleep(options.get("delay", 0))
                if "slow_headers" in options:
                    for byte in b"HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r\n":
                        self.connection.sendall(bytes([byte]))
                        time.sleep(options["slow_headers"])
                else:
                    self.send_response(400 if options.get("host") and self.headers.get("Host") != options["host"]
                                       else options.get("code", 200))
                    for key, value in options.get("headers", {}).items():
                        self.send_header(key, value)
                    self.end_headers()
                body = options.get("body", b"")
                step = options.get("step", len(body) or 1)
                for start in range(0, len(body), step):
                    self.wfile.write(body[start:start + step])
                    self.wfile.flush()
                    time.sleep(options.get("interval", 0))
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass

        def log_message(self, *args):
            pass

    httpd = HTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=httpd.serve_forever)
    worker.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_port}"
    finally:
        httpd.shutdown()
        httpd.server_close()
        worker.join(3)
        assert not worker.is_alive()


def config(root, base, timeout=1000):
    return {"_root": str(root), "export_dir": "published",
            "health": {"url": base + "/health", "timeout_ms": timeout}}


def published(adapter, root, base, timeout=1000):
    cfg = config(root, base, timeout)
    entry = {"id": "fixture.pattern.one", "version": 1, "category": "PATTERN",
             "evidencia": "validated_case", "fuentes": [], "tags": [],
             "modo": "completo", "cuerpo": "Synthetic fixture only."}
    adapter.apply(adapter.plan([entry], cfg), cfg)
    return cfg


def snapshot(**extras):
    return json.dumps({"nodes": [{"type": "chunk", "file_name": "fixture.pattern.one.md"}],
                       **extras}).encode()


def test_health_oversize_cannot_be_healthy(adapter, tmp_path):
    body = json.dumps({"status": "ok", "padding": "x" * (64 * 1024)}).encode()
    with server({"/health": {"body": body}}) as base:
        result = adapter.health(config(tmp_path, base))
    assert result["estado"] == "error"
    assert "budget" in result["detalle"]


def test_snapshot_oversize_cannot_verify(adapter, tmp_path):
    with server({"/graph/snapshot": {"body": snapshot(padding="x" * (2 * 1024 * 1024))}}) as base:
        result = adapter.verify(published(adapter, tmp_path, base))
    assert result["ok"] is False
    assert "budget" in result["desfase"][0]["motivo"]


def test_error_body_reads_at_most_budget_and_closes(adapter):
    class Counted(io.BytesIO):
        total = 0

        def read(self, amount=-1):
            result = super().read(amount)
            self.total += len(result)
            return result

        def read1(self, amount=-1):
            return self.read(amount)

    body = Counted(json.dumps({"error": "x" * (64 * 1024)}).encode())
    error = urllib.error.HTTPError("http://127.0.0.1/health", 503, "fixture", {}, body)
    result = adapter._cuerpo_json_o_none(error)
    assert result is None
    assert 0 < body.total <= 64 * 1024 + 1
    assert body.closed


@pytest.mark.parametrize("operation", ["health", "verify"])
def test_excessive_json_depth_is_opaque_failure(adapter, tmp_path, operation):
    nested = "[" * 80 + "0" + "]" * 80
    body = (('{"status":"ok","nested":' if operation == "health" else
             '{"nodes":[{"type":"chunk","file_name":"fixture.pattern.one.md"}],"nested":')
            + nested + '}').encode()
    route = "/health" if operation == "health" else "/graph/snapshot"
    with server({route: {"body": body}}) as base:
        cfg = config(tmp_path, base) if operation == "health" else published(adapter, tmp_path, base)
        result = getattr(adapter, operation)(cfg)
    assert result["estado"] == "error" if operation == "health" else result["ok"] is False


@pytest.mark.parametrize("body", [b'[]', b'{"nodes":{}}', b'{"nodes":"bad"}'])
def test_invalid_snapshot_shape_never_escapes(adapter, tmp_path, body):
    with server({"/graph/snapshot": {"body": body}}) as base:
        result = adapter.verify(published(adapter, tmp_path, base))
    assert result["ok"] is False
    assert "JSON" in result["desfase"][0]["motivo"]


@pytest.mark.parametrize("mode", ["body", "headers", "redirect_body", "error_body"])
def test_total_deadline_resists_dribble(adapter, tmp_path, mode):
    final = {"body": b'{"status":"ok"}', "step": 1, "interval": 0.025}
    responses = {"/health": final}
    if mode == "headers":
        final["slow_headers"] = 0.01
        final["interval"] = 0
    elif mode == "redirect_body":
        responses = {"/health": {"code": 302, "headers": {"Location": "/final"}, "delay": 0.07},
                     "/final": {**final, "delay": 0.03}}
    elif mode == "error_body":
        final["code"] = 503
    with server(responses) as base:
        started = time.monotonic()
        result = adapter.health(config(tmp_path, base, 140))
        elapsed = time.monotonic() - started
    assert elapsed < 0.30, (mode, elapsed, result)
    assert result["estado"] != "sano"


def test_truncated_content_length_never_healthy(adapter, tmp_path):
    with server({"/health": {"body": b'{"status":"ok"}',
                             "headers": {"Content-Length": "100"}}}) as base:
        result = adapter.health(config(tmp_path, base))
    assert result["estado"] == "error"


@pytest.mark.parametrize("mode", ["body", "chunked", "length"])
def test_complete_small_response_preserves_health_and_verification(adapter, tmp_path, mode):
    def response(body):
        if mode == "chunked":
            return {"body": f"{len(body):x}\r\n".encode() + body + b"\r\n0\r\n\r\n",
                    "headers": {"Transfer-Encoding": "chunked"}}
        return {"body": body, "headers": {"Content-Length": str(len(body))} if mode == "length" else {}}

    with server({"/health": response(b'{"status":"ok"}'),
                 "/graph/snapshot": response(snapshot())}) as base:
        cfg = published(adapter, tmp_path, base)
        assert adapter.health(cfg)["estado"] == "sano"
        assert adapter.verify(cfg)["ok"] is True


def test_http_error_keeps_status_and_useful_small_detail(adapter, tmp_path):
    with server({"/health": {"code": 503, "body": b'{"error":"synthetic offline"}'}}) as base:
        result = adapter.health(config(tmp_path, base))
    assert result["estado"] == "degradado"
    assert "synthetic offline" in result["detalle"]


def test_redirect_errors_are_closed_before_next_hop(adapter):
    error_body = io.BytesIO(b"unused")
    error = urllib.error.HTTPError("http://127.0.0.1/start", 302, "redirect",
                                   {"Location": "/next"}, error_body)
    good = io.BytesIO(b'{"status":"ok"}')
    opener = mock.Mock()
    opener.open.side_effect = [error, good]
    with mock.patch.object(adapter.urllib.request, "build_opener", return_value=opener):
        with adapter._urlopen_local("http://127.0.0.1/start", 1):
            pass
    assert error_body.closed


@pytest.mark.parametrize("body", [b'{"nodes":[{"type":"chunk","file_name":["bad"]}]}',
                                  b'{"nodes":[null,{"type":"chunk","file_name":"fixture.pattern.one.md"}]}',
                                  b'{"nodes":[{"type":"chunk","file_name":"fixture.pattern.one.md"}],"bad":NaN}'])
def test_snapshot_invalid_node_or_json_constant_cannot_verify(adapter, tmp_path, body):
    with server({"/graph/snapshot": {"body": body}}) as base:
        result = adapter.verify(published(adapter, tmp_path, base))
    assert result["ok"] is False


def test_https_handler_uses_same_deadline_reader_and_preserves_tls_context(adapter):
    opener = adapter._deadline_opener(time.monotonic() + 1)
    handler = next(h for h in opener.handlers if isinstance(h, adapter.urllib.request.HTTPSHandler))
    captured = {}

    def do_open(factory, req, **kwargs):
        captured["kwargs"] = kwargs
        return factory("fixture.local", timeout=0.5, **kwargs)

    with mock.patch.object(handler, "do_open", side_effect=do_open):
        connection = handler.https_open(object())
    assert captured["kwargs"]["context"] is handler._context
    raw = io.BytesIO(b"HTTP/1.0 200 OK\r\n\r\n{}")
    sock = mock.Mock()
    sock.makefile.return_value = io.BufferedReader(raw)
    response = connection.response_class(sock)
    try:
        response.begin()
        assert adapter._read_http_body(response, 20, time.monotonic() + 1) == b"{}"
        assert sock.settimeout.call_count > 0
    finally:
        response.close()
        connection.close()
    assert raw.closed


def test_json_brackets_in_strings_do_not_consume_depth(adapter, tmp_path):
    with server({"/health": {"body": json.dumps({"status": "ok", "string": '["\\' * 100}).encode()}}) as base:
        assert adapter.health(config(tmp_path, base))["estado"] == "sano"


def test_verify_http_error_body_is_closed(adapter, tmp_path):
    cfg = published(adapter, tmp_path, "http://127.0.0.1")
    body = io.BytesIO(b"error")
    error = urllib.error.HTTPError("http://127.0.0.1/graph/snapshot", 503, "fixture", {}, body)
    with mock.patch.object(adapter, "_urlopen_local", side_effect=error):
        assert adapter.verify(cfg)["ok"] is False
    assert body.closed


def test_dns_validation_uses_remaining_budget(adapter, tmp_path):
    completed = threading.Event()

    def slow_dns(host):
        time.sleep(0.24)
        completed.set()
        return "127.0.0.1"

    with mock.patch.object(adapter.socket, "gethostbyname", side_effect=slow_dns):
        started = time.monotonic()
        result = adapter.health(config(tmp_path, "http://fixture-unique.invalid", 60))
        elapsed = time.monotonic() - started
        assert completed.wait(1)
    assert elapsed < 0.18, elapsed
    assert result["estado"] != "sano"


def test_hostnames_are_pinned_once_without_second_dns_and_keep_host(adapter, tmp_path):
    connections = []
    original = adapter.socket.create_connection

    def connect(address, *args, **kwargs):
        connections.append(address)
        assert address[0] == "127.0.0.1"
        return original(address, *args, **kwargs)

    options = {"body": b'{"status":"ok"}'}
    with server({"/health": options}) as base:
        cfg = config(tmp_path, base.replace("127.0.0.1", "fixture.test"))
        options["host"] = cfg["health"]["url"].split("/")[2]
        with mock.patch.object(adapter.socket, "gethostbyname", return_value="127.0.0.1") as dns:
            with mock.patch.object(adapter.socket, "create_connection", side_effect=connect):
                result = adapter.health(cfg)
    assert result["estado"] == "sano"
    assert dns.call_count == 1
    assert connections


def test_pinned_https_keeps_original_sni_and_certificate_validation(adapter):
    import ssl
    opener = adapter._deadline_opener(time.monotonic() + 1, "127.0.0.1")
    handler = next(h for h in opener.handlers if isinstance(h, adapter.urllib.request.HTTPSHandler))
    with mock.patch.object(handler, "do_open", side_effect=lambda factory, req, **kw:
                           factory("fixture.test", timeout=0.5, **kw)):
        connection = handler.https_open(object())
    assert connection._context.check_hostname
    assert connection._context.verify_mode == ssl.CERT_REQUIRED
    sock = mock.Mock()
    with mock.patch.object(adapter.socket, "create_connection", return_value=sock) as connect:
        with mock.patch.object(connection._context, "wrap_socket", return_value=sock) as wrap:
            connection.connect()
    assert connect.call_args.args[0] == ("127.0.0.1", 443)
    assert wrap.call_args.kwargs["server_hostname"] == "fixture.test"
    connection.close()


def test_proxy_configuration_does_not_change_local_transport(adapter, tmp_path, monkeypatch):
    monkeypatch.setenv("http_proxy", "http://127.0.0.1:1")
    monkeypatch.setenv("https_proxy", "http://127.0.0.1:1")
    monkeypatch.setenv("no_proxy", "")
    with server({"/health": {"body": b'{"status":"ok"}'}}) as base:
        hostname_url = base.replace("127.0.0.1", "fixture.test")
        with mock.patch.object(adapter.socket, "gethostbyname", return_value="127.0.0.1"):
            assert adapter.health(config(tmp_path, hostname_url))["estado"] == "sano"


def test_tls_handshake_uses_budget_remaining_after_tcp(adapter):
    """A real silent TLS peer cannot inherit the timeout from before TCP connect."""
    listener = adapter.socket.socket()
    listener.bind(('127.0.0.1', 0))
    listener.listen()
    listener.settimeout(2)
    accepted_sockets = []

    def hold_tls():
        try:
            accepted, _ = listener.accept()
            accepted_sockets.append(accepted)
            with accepted:
                time.sleep(0.45)
        except OSError:
            pass

    worker = threading.Thread(target=hold_tls)
    worker.start()
    actual_connect = adapter.socket.create_connection
    client_sockets = []

    def slow_tcp(*args, **kwargs):
        sock = actual_connect(*args, **kwargs)
        client_sockets.append(sock)
        time.sleep(0.13)
        return sock

    started = time.monotonic()
    try:
        with mock.patch.object(adapter.socket, 'create_connection', side_effect=slow_tcp):
            with pytest.raises((adapter.urllib.error.URLError, TimeoutError, OSError)):
                adapter._urlopen_local('https://127.0.0.1:' + str(listener.getsockname()[1]) + '/health',
                                       0.2, _deadline=started + 0.2)
        elapsed = time.monotonic() - started
    finally:
        listener.close()
        worker.join(3)
    assert elapsed < 0.28, elapsed
    assert accepted_sockets and client_sockets
    assert all(sock.fileno() == -1 for sock in client_sockets)
    assert not worker.is_alive()
