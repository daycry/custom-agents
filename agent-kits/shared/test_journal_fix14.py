#!/usr/bin/env python3
"""T-23 fix14 (plugin-audit-2, fase 1, intento 14): presupuesto POR PROCESO de la captura del journal. Ejecuta: pytest -q.

Gaps 9 y 10: el tope de 0,5 s era por llamada a `settled`, asi que con el directorio configurado fallando y la reserva fallando
tambien se esperaba dos veces (1,2 s de proceso), y `queue()` recorria sin cota (2,9 a 10,5 s con 50 K + 5 K entradas ajenas).
Ahora hay UN plazo monotonico para todo el proceso de captura (`begin_budget`, que abre `capture_end`) compartido por `settled`,
`update`, el directorio de reserva y `queue()` (que lo mira cada 256 entradas). Relojes inyectados: no dependen de la maquina.
El plazo del proceso es de 0,35 s (`_PRESUPUESTO_PROCESO`): con 0,5 s el hijo en frio midio 624-855 ms con 50 K + 5 K y la cola
configurada fallida (2 de 10 por encima de los 800 ms del hook); en fix15 se mide desde el ARRANQUE del proceso (test_journal_fix15.py);
cada llamada suelta de `read_settled` conserva su tope de 0,5 s.
"""
import json
import os
import time

import pytest

from test_journal import _directorio_grande, _reloj_inyectado, journal, proyecto, session_end_payload

TOPE = 0.35                                            # `_PRESUPUESTO_PROCESO`; el tope de cada llamada suelta sigue siendo 0,5 s (`_ESPERA_MAX`)


def test_el_presupuesto_del_proceso_es_de_0_35_s_y_el_tope_de_una_llamada_suelta_sigue_en_0_5_s():
    JIO = journal._capture_mod.JIO
    assert JIO._PRESUPUESTO_PROCESO == TOPE and JIO._ESPERA_MAX == 0.5


def _con_tmp_vivo(carpeta, nombre):
    """`carpeta/nombre` con un `.tmp-vivo` que comparte inodo (inicializacion en curso que no acaba nunca)."""
    carpeta.mkdir(parents=True, exist_ok=True)
    f = carpeta / nombre
    f.write_bytes(b"x")
    os.link(f, carpeta / ".tmp-vivo")
    return f


def test_el_presupuesto_del_proceso_se_comparte_entre_dos_esperas(tmp_path, monkeypatch):
    JIO = journal._capture_mod.JIO
    a, b = _con_tmp_vivo(tmp_path / "a", "f"), _con_tmp_vivo(tmp_path / "b", "f")
    reloj = _reloj_inyectado(monkeypatch, JIO)
    JIO.begin_budget()
    try:
        for fichero in (a, b):
            with pytest.raises(ValueError, match="unsafe_state"):
                JIO.read_settled(str(fichero))
    finally:
        JIO.end_budget()
    espera = reloj["t"] - 1000.0
    assert espera <= TOPE + 0.05, f"{espera:.3f} s simulados: cada espera tiene su propio tope, no hay presupuesto por proceso"


def test_sin_presupuesto_cada_llamada_conserva_su_propio_tope(tmp_path, monkeypatch):
    """Regresion declarada (pasa antes y despues): fuera de la captura, `read_settled` sigue acotando cada llamada por separado."""
    JIO = journal._capture_mod.JIO
    a, b = _con_tmp_vivo(tmp_path / "a", "f"), _con_tmp_vivo(tmp_path / "b", "f")
    reloj = _reloj_inyectado(monkeypatch, JIO)
    for fichero in (a, b):
        with pytest.raises(ValueError, match="unsafe_state"):
            JIO.read_settled(str(fichero))
    assert reloj["t"] - 1000.0 > 0.9, "sin begin_budget cada llamada espera su tope propio de 0,5 s"


def test_end_budget_reinicia_el_plazo_para_la_siguiente_captura(tmp_path, monkeypatch):
    JIO = journal._capture_mod.JIO
    a, b = _con_tmp_vivo(tmp_path / "a", "f"), _con_tmp_vivo(tmp_path / "b", "f")
    reloj = _reloj_inyectado(monkeypatch, JIO)
    for fichero in (a, b):
        JIO.begin_budget()
        try:
            with pytest.raises(ValueError, match="unsafe_state"):
                JIO.read_settled(str(fichero))
        finally:
            JIO.end_budget()
    assert reloj["t"] - 1000.0 > 2 * TOPE - 0.05, "el segundo proceso de captura recibe un plazo NUEVO, no el agotado del primero"


def _cola_de_ficheros(tmp_path, n):
    d = tmp_path / "cola"
    d.mkdir()
    for i in range(n):
        (d / f"e{i}.json").write_bytes(b"")
    return d


def test_queue_con_muchas_entradas_esta_acotada_por_el_presupuesto(tmp_path, monkeypatch):
    JIO = journal._capture_mod.JIO
    cola = _cola_de_ficheros(tmp_path, 4000)
    reloj = _reloj_inyectado(monkeypatch, JIO)
    real = JIO.IO.file

    def lento(path):
        reloj["t"] += 0.0002                           # cada comprobacion de una entrada «cuesta» 0,2 ms de reloj monotonico
        return real(path)

    monkeypatch.setattr(JIO.IO, "file", lento)
    JIO.begin_budget()
    try:
        with pytest.raises(ValueError, match="journal_queue_budget"):
            JIO.queue(cola)
    finally:
        JIO.end_budget()
    espera = reloj["t"] - 1000.0
    assert espera <= TOPE + 0.06, f"{espera:.3f} s simulados: queue() no se acota por el presupuesto (se comprueba cada 256 entradas)"


def test_queue_sin_presupuesto_recorre_entera_como_antes(tmp_path, monkeypatch):
    """Regresion declarada: fuera de la captura (otros usos de `queue`) no hay tope nuevo."""
    JIO = journal._capture_mod.JIO
    cola = _cola_de_ficheros(tmp_path, 1500)
    reloj = _reloj_inyectado(monkeypatch, JIO)
    real = JIO.IO.file
    monkeypatch.setattr(JIO.IO, "file", lambda p: (reloj.__setitem__("t", reloj["t"] + 0.001), real(p))[1])
    JIO.queue(cola)                                     # 1,5 s simulados > 0,5 s: no lanza
    assert reloj["t"] - 1000.0 > 1.0


def test_capture_end_con_cola_configurada_y_reserva_en_estado_transitorio_espera_un_solo_plazo(tmp_path, monkeypatch):
    """Gap 9: antes, directorio configurado -> `unsafe_state` tras 0,5 s -> reserva por defecto -> otros 0,5 s (1,2 s de proceso)."""
    JIO = journal._capture_mod.JIO
    proj, _ = proyecto(tmp_path, con_git=False)
    (proj / ".claude" / "dev.json").write_text(json.dumps({"sesion": {"journal": {"dir": "q2"}}}), encoding="utf-8")
    _con_tmp_vivo(proj / "q2", ".custom-agents-journal")
    _con_tmp_vivo(proj / ".claude" / "journal", ".custom-agents-journal")
    reloj = _reloj_inyectado(monkeypatch, JIO)
    assert journal.capture_end(str(proj), session_end_payload(proj)) is None        # captura omitida con error limpio
    espera = reloj["t"] - 1000.0
    assert espera <= TOPE + 0.06, f"{espera:.3f} s simulados de espera en un proceso de captura: debe ser un solo plazo de {TOPE} s"


def test_una_captura_normal_despues_de_una_omitida_recibe_un_plazo_nuevo(tmp_path, monkeypatch):
    JIO = journal._capture_mod.JIO
    mal, _ = proyecto(tmp_path / "mal", con_git=False)
    (mal / ".claude" / "dev.json").write_text(json.dumps({"sesion": {"journal": {"dir": "q2"}}}), encoding="utf-8")
    _con_tmp_vivo(mal / "q2", ".custom-agents-journal")
    _con_tmp_vivo(mal / ".claude" / "journal", ".custom-agents-journal")
    reloj = _reloj_inyectado(monkeypatch, JIO)
    assert journal.capture_end(str(mal), session_end_payload(mal)) is None
    bien, _ = proyecto(tmp_path / "bien", con_git=False)
    ruta = journal.capture_end(str(bien), session_end_payload(bien))
    assert ruta and os.path.exists(ruta), "el plazo agotado por la captura anterior no puede arrastrarse a la siguiente"
