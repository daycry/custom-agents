#!/usr/bin/env python3
"""Tests de outbox.py (session-end-durable-capture T-01). Ejecutar:
python3 -m pytest -q agent-kits/shared/test_outbox.py

Cola atómica compartida (`agent-kits/shared/outbox.py`, ADR de la spec `session-end-durable-capture`):
`escribir` (idempotente por clave, tmp+rename), `reclamar` (outbox -> processing, exclusivo con dos
procesos), `completar` (-> done/ con manifiesto+hash), `dead_letter` (-> dead-letter/ con causa y
contador de intentos), `estado` (contadores por carpeta) y `purgar` (borrado explícito)."""
import importlib.util
import json
import os
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "outbox.py")

spec = importlib.util.spec_from_file_location("outbox", SCRIPT)
outbox = importlib.util.module_from_spec(spec)
spec.loader.exec_module(outbox)


# ------------------------------------------------------------------ escribir

def test_escribir_es_idempotente_por_clave(tmp_path):
    d = tmp_path / "cola"
    p1 = outbox.escribir(str(d), "ev1", {"a": 1})
    p2 = outbox.escribir(str(d), "ev1", {"a": 999})     # payload distinto, MISMA clave
    assert p1 == p2
    with open(p1, encoding="utf-8") as fh:
        assert json.load(fh) == {"a": 1}                # el primero manda; no se reescribe
    assert len([f for f in os.listdir(os.path.join(str(d), "outbox")) if f.endswith(".json")]) == 1


def test_escribir_no_deja_temporal_a_medias(tmp_path):
    d = tmp_path / "cola"
    outbox.escribir(str(d), "ev1", {"a": 1})
    nombres = os.listdir(os.path.join(str(d), "outbox"))
    assert nombres == ["ev1.json"]                      # ningún .tmp-* residual tras un write normal


def test_escribir_solo_stdlib_sin_red():
    src = open(SCRIPT, encoding="utf-8").read()
    for prohibido in ("import requests", "import urllib.request", "socket.connect", "import httpx"):
        assert prohibido not in src


# ------------------------------------------------------------------ reclamar

def test_reclamar_mueve_a_processing_y_devuelve_el_item(tmp_path):
    d = tmp_path / "cola"
    outbox.escribir(str(d), "ev1", {"a": 1})
    item = outbox.reclamar(str(d))
    assert item is not None
    assert item["clave"] == "ev1" and item["payload"] == {"a": 1}
    assert os.path.isfile(item["path"])
    assert "processing" in item["path"].replace("\\", "/")
    assert not os.path.exists(os.path.join(str(d), "outbox", "ev1.json"))


def test_reclamar_sin_pendientes_devuelve_none(tmp_path):
    d = tmp_path / "cola"
    assert outbox.reclamar(str(d)) is None


def test_dos_reclamar_concurrentes_uno_gana_otro_none(tmp_path):
    d = tmp_path / "cola"
    outbox.escribir(str(d), "ev1", {"a": 1})
    with ThreadPoolExecutor(max_workers=2) as ex:
        futuros = [ex.submit(outbox.reclamar, str(d)) for _ in range(2)]
        resultados = [f.result() for f in futuros]
    ganadores = [r for r in resultados if r is not None]
    perdedores = [r for r in resultados if r is None]
    assert len(ganadores) == 1 and len(perdedores) == 1
    assert ganadores[0]["clave"] == "ev1"


# ------------------------------------------------------------------ completar / dead_letter

def test_completar_mueve_a_done_con_manifiesto_y_hash(tmp_path):
    d = tmp_path / "cola"
    outbox.escribir(str(d), "ev1", {"a": 1})
    item = outbox.reclamar(str(d))
    dst = outbox.completar(item, {"cierre": "materializado"})
    assert os.path.isfile(dst) and "done" in dst.replace("\\", "/")
    manifiesto = json.load(open(dst + ".manifest.json", encoding="utf-8"))
    assert manifiesto["cierre"] == "materializado"
    assert len(manifiesto["hash"]) == 64                # sha256 hexdigest


def test_dead_letter_mueve_con_causa_y_cuenta_intentos(tmp_path):
    d = tmp_path / "cola"
    outbox.escribir(str(d), "ev1", {"a": 1})
    item = outbox.reclamar(str(d))
    dst = outbox.dead_letter(item, "envelope venenoso: JSON inválido")
    assert os.path.isfile(dst) and "dead-letter" in dst.replace("\\", "/")
    causa = json.load(open(dst + ".causa.json", encoding="utf-8"))
    assert causa["causa"] == "envelope venenoso: JSON inválido"
    assert causa["intentos"] == 1


def test_dead_letter_no_bloquea_al_resto_de_la_cola(tmp_path):
    d = tmp_path / "cola"
    outbox.escribir(str(d), "malo", {"x": 1})
    outbox.escribir(str(d), "bueno", {"x": 2})
    item1 = outbox.reclamar(str(d))
    outbox.dead_letter(item1, "corrupto")
    item2 = outbox.reclamar(str(d))
    assert item2 is not None
    assert outbox.completar(item2, {}) is not None


# ------------------------------------------------------------------ estado / purgar

def test_estado_cuenta_por_carpeta(tmp_path):
    d = tmp_path / "cola"
    outbox.escribir(str(d), "ev1", {"a": 1})
    outbox.escribir(str(d), "ev2", {"a": 2})
    item = outbox.reclamar(str(d))
    outbox.completar(item, {})
    st = outbox.estado(str(d))
    assert st["outbox"] == 1 and st["processing"] == 0 and st["done"] == 1 and st["dead-letter"] == 0


def test_estado_sin_cola_todo_cero(tmp_path):
    d = tmp_path / "no-existe"
    st = outbox.estado(str(d))
    assert st == {"outbox": 0, "processing": 0, "done": 0, "dead-letter": 0}


def test_purgar_sin_confirmar_no_borra(tmp_path):
    d = tmp_path / "cola"
    outbox.escribir(str(d), "ev1", {"a": 1})
    assert outbox.purgar(str(d), confirmar=False) is False
    assert os.path.isdir(str(d))


def test_purgar_confirmado_borra_todo(tmp_path):
    d = tmp_path / "cola"
    outbox.escribir(str(d), "ev1", {"a": 1})
    assert outbox.purgar(str(d), confirmar=True) is True
    assert not os.path.exists(str(d))
