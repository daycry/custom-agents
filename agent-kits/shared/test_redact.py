#!/usr/bin/env python3
"""Tests de redact.py (session-end-durable-capture T-02, CA-11). Ejecutar:
python3 -m pytest -q agent-kits/shared/test_redact.py

Extraído de `journal.py:redactar` (única fuente): mismos casos de redacción que ya cubría
`test_journal.py` — claves de API con prefijo conocido, JWT, bloques PEM, `Bearer`, `clave|token|
password… = valor`, sin falsos positivos evidentes."""
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "redact.py")

spec = importlib.util.spec_from_file_location("redact", SCRIPT)
redact = importlib.util.module_from_spec(spec)
spec.loader.exec_module(redact)


def test_redacta_api_key_con_prefijo_conocido():
    assert redact.redactar("api_key=AKIAIOSFODNN7EXAMPLE1") == f"api_key={redact.REDACTADO}"


def test_redacta_bearer():
    assert redact.redactar("Bearer AbCdEfGhIjKlMnOpQrStUvWxYz0123456789") == f"Bearer {redact.REDACTADO}"


def test_redacta_jwt():
    jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dQw4w9WgXcQ_abcdefghij"
    assert redact.REDACTADO in redact.redactar(f"token: {jwt}")


def test_redacta_bloque_pem():
    pem = "-----BEGIN PRIVATE KEY-----\nMIIBVQ==\n-----END PRIVATE KEY-----"
    assert redact.redactar(pem) == redact.REDACTADO


def test_sin_falsos_positivos():
    for limpio in ("tokens por hora (479326)", "password reset flow", "hola mundo"):
        assert redact.redactar(limpio) == limpio


def test_solo_stdlib():
    src = open(SCRIPT, encoding="utf-8").read()
    for prohibido in ("import requests", "import urllib.request"):
        assert prohibido not in src


def test_139_redacta_el_par_json_de_una_clave_sensible():
    """#139 (training-data-services fix2, CWE-312): la forma JSON `"password": "…"` no casaba con
    `password=`/`password:` (la comilla de cierre de la clave va antes de los dos puntos)."""
    import json
    for clave in ("password", "api_key", "token", "secret", "Password", "API-KEY", "contraseña", "pwd"):
        texto = json.dumps({clave: "hunter2", "otro": "valor"}, ensure_ascii=False)
        salida = redact.redactar(texto)
        assert "hunter2" not in salida, clave
        assert json.loads(salida) == {clave: redact.REDACTADO, "otro": "valor"}, clave
    assert redact.redactar('{"token" :  "a\\"b c"}') == '{"token" :  "' + redact.REDACTADO + '"}'
    assert redact.redactar("{'password': 'hunter2'}") == "{'password': '" + redact.REDACTADO + "'}"


def test_139_par_json_de_una_clave_no_sensible_no_se_toca():
    for limpio in ('{"tokens": "479326"}', '{"passwordless": "si"}', '{"nota": "password"}',
                   '{"password_hint": "el perro"}', '{"password": ""}', '{"token": 5}'):
        assert redact.redactar(limpio) == limpio, limpio


def test_139_es_clave_sensible():
    for k in ("password", "PASSWD", "api_key", "api-key", "apikey", "secret_key", "access_key", "token", "clave"):
        assert redact.es_clave_sensible(k), k
    for k in ("tokens", "my_password", "passwordless", "clave_foranea", "", "nota"):
        assert not redact.es_clave_sensible(k), k
