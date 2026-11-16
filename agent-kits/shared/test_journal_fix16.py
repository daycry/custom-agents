#!/usr/bin/env python3
"""Tests de journal-io.py: ciclo fix16 de T-23 (plugin-audit-2, fase 1, intento 16, gap 17). Ejecuta: pytest -q.

El minimo de `_ESPERA_MINIMA` se mide desde la PRIMERA ESPERA REAL (la primera vez que un estado transitorio obliga a dormir), no desde la primera
LLAMADA a `settled`/`update` ni desde el marcador de `queue()`. Una sola formula coherente: `max(_ARRANQUE + 0,35 s, primera espera + 0,10 s)`.
"""
import os
import re

import pytest

from test_journal import _reloj_inyectado, journal
from test_journal_fix14 import _con_tmp_vivo

AQUI = os.path.dirname(os.path.abspath(__file__))


def test_una_llamada_que_no_espera_no_gasta_el_minimo(tmp_path, monkeypatch):
    """Con el plazo agotado por el arranque, una lectura que NO tiene que esperar no consume el minimo: la primera espera real, mas tarde, lo recibe."""
    JIO = journal._capture_mod.JIO
    sano = tmp_path / "sano"
    sano.write_bytes(b"ok")
    f = _con_tmp_vivo(tmp_path / "a", "f")
    reloj = _reloj_inyectado(monkeypatch, JIO)
    JIO.begin_budget(desde=1000.0 - 5.0)
    try:
        assert JIO.read_settled(str(sano)) == b"ok"
        reloj["t"] += 0.5                                           # pasa tiempo antes de la primera espera real
        antes = reloj["t"]
        with pytest.raises(ValueError, match="unsafe_state"):
            JIO.read_settled(str(f))
        espera = reloj["t"] - antes
    finally:
        JIO.end_budget()
    assert 0.05 <= espera <= JIO._ESPERA_MINIMA + 0.03, f"{espera:.3f} s: la primera espera REAL debe recibir el minimo de {JIO._ESPERA_MINIMA} s"


def test_queue_no_gasta_el_minimo_en_el_marcador(tmp_path, monkeypatch):
    JIO = journal._capture_mod.JIO
    cola = tmp_path / "cola"
    cola.mkdir()
    (cola / ".custom-agents-journal").write_bytes(b"m")
    f = _con_tmp_vivo(tmp_path / "a", "f")
    reloj = _reloj_inyectado(monkeypatch, JIO)
    JIO.begin_budget(desde=1000.0 - 5.0)
    try:
        JIO.queue(str(cola))
        reloj["t"] += 0.5
        antes = reloj["t"]
        with pytest.raises(ValueError, match="unsafe_state"):
            JIO.read_settled(str(f))
        espera = reloj["t"] - antes
    finally:
        JIO.end_budget()
    assert 0.05 <= espera <= JIO._ESPERA_MINIMA + 0.03, f"{espera:.3f} s"


def test_el_minimo_tambien_vale_para_update_en_su_primera_espera_real(tmp_path, monkeypatch):
    JIO = journal._capture_mod.JIO
    f = _con_tmp_vivo(tmp_path / "a", "f")
    sano = tmp_path / "sano"
    reloj = _reloj_inyectado(monkeypatch, JIO)
    JIO.begin_budget(desde=1000.0 - 5.0)
    try:
        JIO.update(str(sano), lambda raw: b"nuevo")                 # no espera: no gasta el minimo
        reloj["t"] += 0.5
        antes = reloj["t"]
        with pytest.raises(ValueError):
            JIO.update(str(f), lambda raw: b"otro")
        espera = reloj["t"] - antes
    finally:
        JIO.end_budget()
    assert 0.05 <= espera <= JIO._ESPERA_MINIMA + 0.03, f"{espera:.3f} s"


def test_una_sola_cifra_coherente_en_el_codigo_y_la_documentacion():
    fuente = open(os.path.join(AQUI, "journal-io.py"), encoding="utf-8").read()
    JIO = journal._capture_mod.JIO
    assert JIO._PRESUPUESTO_PROCESO == 0.35 and JIO._ESPERA_MINIMA == 0.10
    for cifra in ("0,55", "0,30 s o mas", "0,30 s o más"):
        assert cifra not in fuente, f"cifra del umbral que no coincide con la formula: {cifra}"
    assert "max(_ARRANQUE + 0,35 s, primera espera + 0,10 s)" in fuente
    doc = open(os.path.join(AQUI, "..", "..", "docs", "agents", "implementer.md"), encoding="utf-8").read()
    assert "max(_ARRANQUE + 0,35 s, primera espera + 0,10 s)" in doc
    assert re.search(r"800 ms[^.\n]*en reposo|en reposo[^.\n]*800 ms", doc), "la cota de 800 ms del hijo en frio es en reposo: debe declararse"
