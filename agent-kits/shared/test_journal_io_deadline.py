#!/usr/bin/env python3
"""Plazo de pared de la E/S del journal inyectable en tests (T-23 fix8, gap 13 del intento 8). Ejecuta: pytest -q.

La E/S acotada del journal tiene un plazo fijo de 5 s (`journal-io.py`). Un fsync lento (disco ocupado) lo agotaba y
la captura se perdía en `test_journal.py`. Como `agent-activity-store.py` con su escala de plazos, el plazo se puede
alargar SOLO bajo `PYTEST_CURRENT_TEST` (la producción no cambia) y el test no depende del reloj de la máquina: el
fsync «lento» avanza un reloj simulado, no espera.
"""
import importlib.util
import os
import time

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("journal_io_fix8", os.path.join(HERE, "journal-io.py"))
jio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jio)

ESCALA = "CUSTOM_AGENTS_JOURNAL_IO_DEADLINE_SCALE"


@pytest.fixture
def fsync_lento(monkeypatch):
    """`os.fsync` tarda 6 s de reloj simulado (más que el plazo por defecto de 5 s) sin esperar de verdad."""
    avance = [0.0]
    real = time.monotonic
    monkeypatch.setattr(time, "monotonic", lambda: real() + avance[0])
    fsync = os.fsync

    def lento(fd):
        avance[0] += 6.0
        return fsync(fd)
    monkeypatch.setattr(os, "fsync", lento)


def _escribir(tmp_path, nombre="a.bin"):
    jio.write(tmp_path / nombre, b"hola")
    return (tmp_path / nombre).read_bytes()


def test_sin_escala_un_fsync_de_6_s_agota_el_plazo_por_defecto(tmp_path, fsync_lento, monkeypatch):
    monkeypatch.delenv(ESCALA, raising=False)
    with pytest.raises(ValueError, match="journal_io_deadline"):
        _escribir(tmp_path)


def test_con_escala_inyectada_el_fsync_lento_cabe_en_el_plazo(tmp_path, fsync_lento, monkeypatch):
    monkeypatch.setenv(ESCALA, "12")
    assert _escribir(tmp_path) == b"hola"


def test_update_tambien_usa_el_plazo_inyectado(tmp_path, fsync_lento, monkeypatch):
    monkeypatch.setenv(ESCALA, "12")
    jio.update(tmp_path / "u.bin", lambda raw: raw + b"x")
    assert (tmp_path / "u.bin").read_bytes() == b"x"


@pytest.mark.parametrize("valor", ["0.5", "abc", "-3", "nan", "inf"])
def test_una_escala_invalida_o_menor_que_1_vale_el_plazo_por_defecto(valor, monkeypatch):
    monkeypatch.setenv(ESCALA, valor)
    assert jio.deadline_seconds() == 5.0


def test_la_escala_se_acota_a_60(monkeypatch):
    monkeypatch.setenv(ESCALA, "1000")
    assert jio.deadline_seconds() == 300.0


def test_fuera_de_pytest_la_escala_no_actua(monkeypatch):
    """Producción: sin `PYTEST_CURRENT_TEST` el plazo sigue siendo 5 s aunque la variable esté puesta."""
    monkeypatch.setenv(ESCALA, "12")
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    assert jio.deadline_seconds() == 5.0
