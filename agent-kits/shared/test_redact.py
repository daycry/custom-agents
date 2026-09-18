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
