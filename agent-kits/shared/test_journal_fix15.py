#!/usr/bin/env python3
"""T-23 fix15 (plugin-audit-2, fase 1, intento 15): el plazo de la captura del journal se mide desde el ARRANQUE del proceso. Ejecuta: pytest -q.

Gap 9: el plazo de `begin_budget` (fix14) empezaba en la primera espera, no al arrancar el proceso; el hijo de SessionEnd en frio (50 K + 5 K,
cola configurada fallida) tardaba 551-1.283 ms con carga porque el arranque e imports (192-584 ms) no contaban. Ahora el modulo marca el
arranque al importarse (`_ARRANQUE`, reloj monotonico) y los dos puntos de entrada de un proceso de captura (`journal-capture.py main` y
`journal.py capture-end`) lo pasan como `desde=`. Gap 10: una inicializacion legitima que dura mas de lo que queda de plazo se omite (la recupera
`recover`); aqui se declara desde cuando. Relojes inyectados: no dependen de la maquina.
"""
import io
import json
import os
import sys
import time

import pytest

from test_journal import _reloj_inyectado, journal, proyecto, session_end_payload
from test_journal_fix14 import _con_tmp_vivo


def _espera_en(JIO, reloj, fichero, desde):
    JIO.begin_budget(desde=desde)
    try:
        with pytest.raises(ValueError, match="unsafe_state"):
            JIO.read_settled(str(fichero))
    finally:
        JIO.end_budget()
    return reloj["t"] - 1000.0


def test_el_modulo_marca_el_arranque_del_proceso_al_importarse():
    JIO = journal._capture_mod.JIO
    assert isinstance(JIO._ARRANQUE, float) and JIO._ARRANQUE <= time.monotonic()
    assert isinstance(journal._capture_mod._ARRANQUE, float) and journal._capture_mod._ARRANQUE <= time.monotonic()
    assert isinstance(journal._ARRANQUE, float) and journal._ARRANQUE <= time.monotonic()


def test_el_plazo_se_mide_desde_el_arranque_no_desde_la_primera_espera(tmp_path, monkeypatch):
    JIO = journal._capture_mod.JIO
    f = _con_tmp_vivo(tmp_path / "a", "f")
    reloj = _reloj_inyectado(monkeypatch, JIO)
    espera = _espera_en(JIO, reloj, f, desde=1000.0 - 0.20)         # el proceso lleva 0,20 s arrancado
    assert espera <= JIO._PRESUPUESTO_PROCESO - 0.20 + 0.06, f"{espera:.3f} s simulados: el arranque no cuenta en el plazo"


def test_un_plazo_ya_agotado_por_el_arranque_solo_espera_el_minimo(tmp_path, monkeypatch):
    """El proceso ya agoto su plazo (arranque lento): la espera del estado transitorio recibe el minimo (`_ESPERA_MINIMA`, i10) y ni un ms mas."""
    JIO = journal._capture_mod.JIO
    f = _con_tmp_vivo(tmp_path / "a", "f")
    reloj = _reloj_inyectado(monkeypatch, JIO)
    espera = _espera_en(JIO, reloj, f, desde=1000.0 - 5.0)
    assert 0.0 < espera <= JIO._ESPERA_MINIMA + 0.03, f"{espera:.3f} s: plazo agotado, la espera debe ser el minimo de {JIO._ESPERA_MINIMA} s"


@pytest.mark.parametrize("duracion", [0.02, 0.05, 0.09])
def test_el_arranque_lento_no_omite_una_inicializacion_legitima_corta(tmp_path, monkeypatch, duracion):
    """Interpretacion i10 (regresion medida): con la maquina saturada el arranque del hijo consumia los 0,35 s y la primera espera de un estado
    transitorio (nlink 2 durante unos ms) se daba por agotada: captura omitida. Con el minimo por espera se lee."""
    JIO = journal._capture_mod.JIO
    f, reloj = _inicializador_legitimo(monkeypatch, JIO, tmp_path / "q", duracion)
    JIO.begin_budget(desde=1000.0 - 5.0)                       # el arranque ya gasto todo el plazo del proceso
    try:
        assert JIO.read_settled(str(f)) == b"x"
    finally:
        JIO.end_budget()


def test_la_segunda_espera_comparte_el_plazo_ya_agotado(tmp_path, monkeypatch):
    """El minimo es solo de la PRIMERA espera del proceso: la segunda comparte el plazo (el contrato de fix14: un solo plazo por proceso)."""
    JIO = journal._capture_mod.JIO
    a, b = _con_tmp_vivo(tmp_path / "a", "f"), _con_tmp_vivo(tmp_path / "b", "f")
    reloj = _reloj_inyectado(monkeypatch, JIO)
    JIO.begin_budget(desde=1000.0 - 5.0)
    try:
        for fichero in (a, b):
            with pytest.raises(ValueError, match="unsafe_state"):
                JIO.read_settled(str(fichero))
    finally:
        JIO.end_budget()
    assert reloj["t"] - 1000.0 <= JIO._ESPERA_MINIMA + 0.03, "dos esperas con el plazo agotado suman un solo minimo, no uno por espera"


@pytest.mark.parametrize("entradas", [3, 100, 255])
def test_queue_recorre_siempre_las_primeras_255_entradas_aunque_el_plazo_este_agotado(tmp_path, monkeypatch, entradas):
    """Una cola normal (outbox, processing, done…) se valida entera aunque el arranque lento haya agotado el plazo del proceso (i10)."""
    JIO = journal._capture_mod.JIO
    cola = tmp_path / "cola"
    cola.mkdir()
    for i in range(entradas):
        (cola / f"e{i}.json").write_bytes(b"")
    _reloj_inyectado(monkeypatch, JIO)
    JIO.begin_budget(desde=1000.0 - 5.0)
    try:
        JIO.queue(str(cola))                                    # no lanza `journal_queue_budget`
    finally:
        JIO.end_budget()


def test_el_minimo_no_amplia_el_recorrido_de_queue(tmp_path, monkeypatch):
    """`queue()` sigue acotada por el plazo del proceso a partir de la entrada 256, sin minimo: un listado largo no puede alargar el cierre."""
    JIO = journal._capture_mod.JIO
    cola = tmp_path / "cola"
    cola.mkdir()
    for i in range(1200):
        (cola / f"e{i}.json").write_bytes(b"")
    reloj = _reloj_inyectado(monkeypatch, JIO)
    real = JIO.IO.file
    monkeypatch.setattr(JIO.IO, "file", lambda p: (reloj.__setitem__("t", reloj["t"] + 0.001), real(p))[1])
    JIO.begin_budget(desde=1000.0 - 5.0)
    try:
        with pytest.raises(ValueError, match="journal_queue_budget"):
            JIO.queue(str(cola))
    finally:
        JIO.end_budget()
    assert reloj["t"] - 1000.0 <= 0.3, "queue() recorrio con el plazo del proceso agotado: el minimo no aplica a los listados"


def test_sin_origen_el_plazo_sigue_empezando_en_la_primera_espera(tmp_path, monkeypatch):
    """Regresion declarada: `begin_budget()` sin `desde` (otros usos, los tests de fix14) se comporta como antes."""
    JIO = journal._capture_mod.JIO
    f = _con_tmp_vivo(tmp_path / "a", "f")
    reloj = _reloj_inyectado(monkeypatch, JIO)
    espera = _espera_en(JIO, reloj, f, desde=None)
    assert JIO._PRESUPUESTO_PROCESO - 0.06 <= espera <= JIO._PRESUPUESTO_PROCESO + 0.06, espera


def test_el_main_de_la_captura_ancla_el_plazo_al_arranque_del_proceso(tmp_path, monkeypatch):
    cm = journal._capture_mod
    proj, _ = proyecto(tmp_path, con_git=False)
    vistos = {}
    monkeypatch.setattr(cm, "capture_end", lambda root, payload, desde=None: vistos.update(desde=desde))
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(session_end_payload(proj))))
    cm.main(["--root", str(proj)])
    assert vistos.get("desde") == cm._ARRANQUE, vistos


def test_el_capture_end_de_journal_py_ancla_el_plazo_al_arranque_del_proceso(tmp_path, monkeypatch):
    proj, _ = proyecto(tmp_path, con_git=False)
    vistos = {}
    monkeypatch.setattr(journal, "capture_end", lambda root, payload, desde=None: vistos.update(desde=desde))
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(session_end_payload(proj))))
    import argparse
    assert journal.cmd_capture_end(argparse.Namespace(root=str(proj))) == 0
    assert vistos.get("desde") == journal._ARRANQUE, vistos


def test_capture_end_pasa_el_origen_al_presupuesto(tmp_path, monkeypatch):
    JIO = journal._capture_mod.JIO
    proj, _ = proyecto(tmp_path, con_git=False)
    visto = {}
    real = JIO.begin_budget
    monkeypatch.setattr(JIO, "begin_budget", lambda desde=None: (visto.update(desde=desde), real(desde=desde))[1])
    journal._capture_mod.capture_end(str(proj), session_end_payload(proj), desde=123.5)
    assert visto == {"desde": 123.5}


# ---------------------------------------------------------------- gap 10: carrera legitima con el presupuesto REAL ----
def _inicializador_legitimo(monkeypatch, JIO, carpeta, duracion):
    """`carpeta/.custom-agents-journal` con un `.tmp-` hermano y reciente (inicializacion en curso) que el «otro proceso» termina `duracion`
    s de reloj simulado despues de que el lector empiece: cada `sleep` avanza el reloj y, pasada la duracion, borra el temporal."""
    f = _con_tmp_vivo(carpeta, ".custom-agents-journal")
    tmp = carpeta / ".tmp-vivo"
    reloj = _reloj_inyectado(monkeypatch, JIO)
    dormir = JIO.time.sleep

    def dormir_y_acabar(s):
        dormir(s)
        if reloj["t"] - 1000.0 >= duracion and tmp.exists():
            tmp.unlink()

    JIO.time.sleep = dormir_y_acabar
    return f, reloj


@pytest.mark.parametrize("duracion", [0.05, 0.10, 0.15])
def test_una_inicializacion_legitima_corta_se_espera_y_se_lee_con_el_presupuesto_real(tmp_path, monkeypatch, duracion):
    JIO = journal._capture_mod.JIO
    f, reloj = _inicializador_legitimo(monkeypatch, JIO, tmp_path / "q", duracion)
    JIO.begin_budget(desde=1000.0 - 0.05)                    # 50 ms de arranque ya gastados
    try:
        assert JIO.read_settled(str(f)) == b"x"
    finally:
        JIO.end_budget()


@pytest.mark.parametrize("extra", [0.0, 0.05, 0.40])
def test_una_inicializacion_que_dura_mas_que_el_plazo_restante_se_omite_y_la_recupera_recover(tmp_path, monkeypatch, extra):
    """Declarado en el ledger (gap 10): desde `_PRESUPUESTO_PROCESO` - arranque, la captura se OMITE con `unsafe_state`; `recover` la recupera."""
    JIO = journal._capture_mod.JIO
    arranque = 0.05
    f, reloj = _inicializador_legitimo(monkeypatch, JIO, tmp_path / "q", JIO._PRESUPUESTO_PROCESO - arranque + extra + 0.02)
    JIO.begin_budget(desde=1000.0 - arranque)
    try:
        with pytest.raises(ValueError, match="unsafe_state"):
            JIO.read_settled(str(f))
    finally:
        JIO.end_budget()
