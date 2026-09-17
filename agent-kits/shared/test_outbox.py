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
import stat
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

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
    assert st["durabilidad"] == "ok"


def test_estado_sin_cola_todo_cero(tmp_path):
    d = tmp_path / "no-existe"
    st = outbox.estado(str(d))
    assert st == {"outbox": 0, "processing": 0, "done": 0, "dead-letter": 0, "durabilidad": "ok"}


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


# ------------------------------------------------------------------ revisión intento 1 (gaps 1, 3, 9, 21, 22, 23)

def test_escribir_valida_clave_y_rechaza_escape(tmp_path):
    """Gap 23 (C4 · CWE-22): sin validar `clave`, `../../ESCAPE` crea fuera de la cola."""
    d = tmp_path / "cola"
    with pytest.raises(ValueError):
        outbox.escribir(str(d), "../../ESCAPE", {"a": 1})
    with pytest.raises(ValueError):
        outbox.escribir(str(d), "con espacios", {"a": 1})
    assert not os.path.exists(str(tmp_path / "ESCAPE.json"))


def test_reclamar_reencola_processing_huerfano_por_ttl(tmp_path):
    """Gap 1 (Critical): un item reclamado y nunca completado (corte, excepción) queda en
    `processing/` para siempre hoy; `reclamar` debe barrerlo tras `processing_ttl_s`."""
    d = tmp_path / "cola"
    outbox.escribir(str(d), "ev1", {"a": 1})
    item = outbox.reclamar(str(d))
    assert item is not None
    # simula que el item lleva más de la TTL en processing/ (proceso interrumpido)
    viejo = time.time() - 700
    os.utime(item["path"], (viejo, viejo))
    item2 = outbox.reclamar(str(d), processing_ttl_s=600)
    assert item2 is not None and item2["clave"] == "ev1"
    assert os.path.isfile(os.path.join(str(d), "processing", "ev1.json.intentos"))


def test_reclamar_huerfano_agota_intentos_y_va_a_dead_letter(tmp_path):
    """Gap 1/22: tras MAX_INTENTOS reencolados sin completar, el item va a dead-letter (no se
    pierde silenciosamente, y libera al resto de la cola)."""
    d = tmp_path / "cola"
    outbox.escribir(str(d), "ev1", {"a": 1})
    for _ in range(outbox.MAX_INTENTOS):
        item = outbox.reclamar(str(d), processing_ttl_s=0)
        assert item is not None
        viejo = time.time() - 1
        os.utime(item["path"], (viejo, viejo))
    # una reclamación más: ya alcanzó MAX_INTENTOS → dead-letter, no vuelve a outbox/processing
    assert outbox.reclamar(str(d), processing_ttl_s=0) is None
    st = outbox.estado(str(d))
    assert st["dead-letter"] == 1 and st["outbox"] == 0 and st["processing"] == 0
    causa = json.load(open(os.path.join(str(d), "dead-letter", "ev1.json.causa.json"), encoding="utf-8"))
    assert "reintentos agotados" in causa["causa"]


def test_escribir_no_deja_tmp_a_medias_tras_fallo_a_mitad(tmp_path, monkeypatch):
    """Gap 3 (CA-04): un corte a mitad de la escritura no debe dejar el destino a medias ni un
    `.tmp-*` que nadie limpie."""
    d = tmp_path / "cola"

    real_replace = os.replace

    def replace_que_falla(a, b):
        raise OSError("disco lleno simulado")

    monkeypatch.setattr(os, "replace", replace_que_falla)
    with pytest.raises(OSError):
        outbox.escribir(str(d), "ev1", {"a": 1})
    monkeypatch.setattr(os, "replace", real_replace)
    assert not os.path.exists(os.path.join(str(d), "outbox", "ev1.json"))
    restantes = [f for f in os.listdir(os.path.join(str(d), "outbox")) if ".tmp-" in f]
    assert restantes == []                              # el tmp se limpia aunque `os.replace` falle


def test_limpiar_tmp_huerfanos_borra_planted_y_respeta_ttl(tmp_path):
    """Gap 3/13/21: un `.tmp-<pid>` plantado en outbox/ (o dejado por un corte real) se ignora en
    listados y `replay`/`limpiar_tmp_huerfanos` lo borra al superar la TTL."""
    d = tmp_path / "cola"
    outbox_dir = d / "outbox"
    outbox_dir.mkdir(parents=True)
    plantado = outbox_dir / "ev1.json.tmp-999"
    plantado.write_text("{incompleto", encoding="utf-8")
    viejo = time.time() - 700
    os.utime(str(plantado), (viejo, viejo))
    assert outbox.reclamar(str(d)) is None              # el .tmp-* no es un candidato válido
    assert outbox.estado(str(d))["outbox"] == 0
    borrados = outbox.limpiar_tmp_huerfanos(str(d), ttl_s=600)
    assert borrados == 1 and not plantado.exists()


def test_purgar_antiguos_borra_done_pero_no_dead_letter(tmp_path):
    """Gap 22: `done/`/`dead-letter/` crecían para siempre; `purgar_antiguos` los acota (lo invoca
    `journal.py replay` sobre `done/`, nunca sobre `dead-letter/`)."""
    d = tmp_path / "cola"
    outbox.escribir(str(d), "viejo", {"a": 1})
    item = outbox.reclamar(str(d))
    dst = outbox.completar(item, {})
    viejo = time.time() - 40 * 86400
    os.utime(dst, (viejo, viejo))
    os.utime(dst + ".manifest.json", (viejo, viejo))
    borrados = outbox.purgar_antiguos(str(d), "done", dias=30)
    assert borrados == 1
    assert outbox.estado(str(d))["done"] == 0
    assert not os.path.exists(dst) and not os.path.exists(dst + ".manifest.json")


def test_directorios_y_ficheros_de_la_cola_son_privados(tmp_path):
    """Gap 9 (B5/C1 · CWE-538/732): la cola no debe ser world-readable ni sembrarse en git status
    sin control."""
    d = tmp_path / "cola"
    p = outbox.escribir(str(d), "ev1", {"a": 1})
    assert stat.S_IMODE(os.stat(os.path.dirname(p)).st_mode) == 0o700
    assert stat.S_IMODE(os.stat(p).st_mode) & 0o077 == 0


def test_dead_letter_no_fuga_el_handle_de_causa_json(tmp_path):
    """Gap 23 (B15): `dead_letter` abría `causa.json` sin cerrarlo (fuga de fd en Windows, donde un
    handle abierto bloquea el `os.replace` siguiente). Aquí se fuerza un segundo `dead_letter` de
    la MISMA clave (reencolando a mano) para que la lectura+reescritura de `causa.json` ocurra dos
    veces seguidas sin excepción ni fichero bloqueado."""
    d = tmp_path / "cola"
    outbox.escribir(str(d), "ev1", {"a": 1})
    item = outbox.reclamar(str(d))
    dst = outbox.dead_letter(item, "primer intento")
    # reencola a mano la misma clave (simula un replay que recapturó y volvió a fallar)
    os.replace(dst, os.path.join(str(d), "outbox", "ev1.json"))
    item2 = outbox.reclamar(str(d))
    dst2 = outbox.dead_letter(item2, "segundo intento")
    with open(dst2 + ".causa.json", encoding="utf-8") as fh:
        assert json.load(fh)["intentos"] == 2
