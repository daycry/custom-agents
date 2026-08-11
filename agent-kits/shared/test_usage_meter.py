#!/usr/bin/env python3
"""Tests de usage-meter.py (iniciativa coste-generacion).

Cubre: suma por ventana, dedupe por message.id (hallazgo T-01: hasta 6 registros por
respuesta), sidechains (fichero nuevo en la ventana), exclusión pre-marcador,
degradación (carpeta ausente, JSON corrupto, usage incompleto), € fiable/no fiable,
caché sin precio → 0 con aviso, ratio CALIBRATION vs default vs explícito,
idempotencia del re-close, marcadores concurrentes y el helper fmt (formato XhYm).

Ejecutar:  python3 -m pytest test_usage_meter.py -q
"""

import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "usage_meter", Path(__file__).parent / "usage-meter.py")
um = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(um)


# ------------------------------------------------------------------ helpers

def _rec(msg_id, inp=0, out=0, cc=0, cr=0, typ="assistant", sidechain=False):
    return json.dumps({
        "type": typ, "isSidechain": sidechain, "uuid": f"u-{msg_id}",
        "requestId": f"req-{msg_id}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": {"id": msg_id, "usage": {
            "input_tokens": inp, "output_tokens": out,
            "cache_creation_input_tokens": cc, "cache_read_input_tokens": cr,
            "service_tier": "standard"}},
    })


def _write(path, lines):
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _run(tmp, argv):
    """Ejecuta el CLI capturando el JSON impreso."""
    import io
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = um.main(argv)
    out = buf.getvalue().strip()
    return rc, json.loads(out) if out.startswith("{") else out


def _rates(tmp, input_p=15.0, output_p=75.0, verificado=None, extra=None):
    pt = {"moneda": "USD", "unidad": "por_millon", "input": input_p, "output": output_p}
    if verificado:
        pt["verificadoEl"] = verificado
    if extra:
        pt.update(extra)
    f = tmp / "rates.json"
    f.write_text(json.dumps({"precioTokens": pt, "tipoCambioUsdEur": 0.92}), encoding="utf-8")
    return str(f)


HOY = datetime.now(timezone.utc).strftime("%Y-%m-%d")


@pytest.fixture()
def entorno(tmp_path):
    tdir = tmp_path / "transcripts"
    tdir.mkdir()
    state = tmp_path / "usage-state.json"
    return tmp_path, tdir, state


def _start_close(tdir, state, antes, despues, close_args=()):
    _write(tdir / "sesion.jsonl", antes)
    rc, _ = _run(None, ["start", "--artefacto", "a.md", "--state", str(state),
                        "--transcript-dir", str(tdir)])
    assert rc == 0
    with open(tdir / "sesion.jsonl", "a", encoding="utf-8") as f:
        for line in despues:
            f.write(line + "\n")
    rc, res = _run(None, ["close", "--artefacto", "a.md", "--state", str(state),
                          "--transcript-dir", str(tdir), *close_args])
    assert rc == 0
    return res


# ------------------------------------------------------------------- ventana

def test_suma_solo_ventana(entorno):
    _, tdir, state = entorno
    res = _start_close(tdir, state,
                       antes=[_rec("m1", inp=1000, out=500)],
                       despues=[_rec("m2", inp=200, out=100, cc=50, cr=30)])
    t = res["tokens_reales"]
    assert res["fuente"] == "medido"
    assert (t["entrada"], t["salida"], t["cache_creacion"], t["cache_lectura"]) == (200, 100, 50, 30)
    assert t["respuestas"] == 1


def test_dedupe_por_message_id(entorno):
    """Hallazgo T-01: una respuesta = hasta 6 registros con usage idéntico → contar UNA vez."""
    _, tdir, state = entorno
    repetidos = [_rec("mX", inp=100, out=50)] * 6
    res = _start_close(tdir, state, antes=[], despues=repetidos)
    t = res["tokens_reales"]
    assert (t["entrada"], t["salida"], t["respuestas"]) == (100, 50, 1)


def test_sidechain_fichero_nuevo_en_ventana(entorno):
    _, tdir, state = entorno
    _write(tdir / "sesion.jsonl", [_rec("m1", inp=10, out=5)])
    rc, _ = _run(None, ["start", "--artefacto", "a.md", "--state", str(state),
                        "--transcript-dir", str(tdir)])
    assert rc == 0
    _write(tdir / "sidechain.jsonl", [_rec("s1", inp=300, out=80, sidechain=True)])
    rc, res = _run(None, ["close", "--artefacto", "a.md", "--state", str(state),
                          "--transcript-dir", str(tdir)])
    assert res["tokens_reales"]["entrada"] == 300
    assert res["tokens_reales"]["salida"] == 80


def test_ignora_tipos_no_assistant_y_usage_incompleto(entorno):
    _, tdir, state = entorno
    res = _start_close(tdir, state, antes=[], despues=[
        _rec("m1", inp=100, out=10),
        json.dumps({"type": "user", "message": {"content": "hola"}}),
        json.dumps({"type": "assistant", "message": {"id": "m2", "usage": {"output_tokens": 7}}}),
    ])
    t = res["tokens_reales"]
    assert t["entrada"] == 100 and t["salida"] == 17 and t["respuestas"] == 2


# -------------------------------------------------------------- degradación

def test_degrada_sin_transcripciones(tmp_path):
    state = tmp_path / "s.json"
    rc, _ = _run(None, ["start", "--artefacto", "a.md", "--state", str(state),
                        "--transcript-dir", str(tmp_path / "no-existe")])
    assert rc == 0
    rc, res = _run(None, ["close", "--artefacto", "a.md", "--state", str(state),
                          "--transcript-dir", str(tmp_path / "no-existe")])
    assert rc == 0  # NUNCA bloquea
    assert res["fuente"] == "estimado"
    assert res["tokens_reales"] is None
    assert any("no disponible" in a for a in res["avisos"])


def test_degrada_sin_marcador(entorno):
    _, tdir, state = entorno
    rc, res = _run(None, ["close", "--artefacto", "nunca-abierto.md", "--state", str(state),
                          "--transcript-dir", str(tdir)])
    assert rc == 0 and res["fuente"] == "estimado"


def test_lineas_corruptas_tolerantes(entorno):
    _, tdir, state = entorno
    res = _start_close(tdir, state, antes=[], despues=[
        "{esto no es json", _rec("m1", inp=50, out=20), '{"type": "assistant"}'])
    assert res["fuente"] == "medido"
    assert res["tokens_reales"]["entrada"] == 50


def test_ventana_vacia_degrada_a_estimado(entorno):
    _, tdir, state = entorno
    res = _start_close(tdir, state, antes=[_rec("m1", inp=10, out=5)], despues=[])
    assert res["fuente"] == "estimado"
    assert any("sin respuestas" in a for a in res["avisos"])


# ------------------------------------------------------------------ € y horas

def test_eur_con_precios_fiables(entorno):
    tmp, tdir, state = entorno
    rates = _rates(tmp, verificado=HOY)
    res = _start_close(tdir, state, antes=[],
                       despues=[_rec("m1", inp=1_000_000, out=100_000)],
                       close_args=["--rates", rates])
    # (1M×15 + 0,1M×75) USD/M × 0,92 = (15+7,5)×0,92 = 20,70 €
    assert res["eur"] == pytest.approx(20.70, abs=0.01)


def test_eur_null_sin_verificadoEl(entorno):
    tmp, tdir, state = entorno
    rates = _rates(tmp, verificado=None)
    res = _start_close(tdir, state, antes=[], despues=[_rec("m1", inp=1000, out=100)],
                       close_args=["--rates", rates])
    assert res["eur"] is None
    assert any("rates-verify" in a for a in res["avisos"])


def test_cache_sin_precio_valorada_a_cero_con_aviso(entorno):
    tmp, tdir, state = entorno
    rates = _rates(tmp, verificado=HOY)
    res = _start_close(tdir, state, antes=[],
                       despues=[_rec("m1", inp=1_000_000, out=0, cr=5_000_000)],
                       close_args=["--rates", rates])
    assert res["eur"] == pytest.approx(13.80, abs=0.01)  # solo el input
    assert any("cache_lectura" in a for a in res["avisos"])
    assert res["tokens_reales"]["cache_lectura"] == 5_000_000  # se informa igualmente


def test_horas_excluyen_lectura_de_cache(entorno):
    _, tdir, state = entorno
    res = _start_close(tdir, state, antes=[],
                       despues=[_rec("m1", inp=100_000, cc=140_000, out=60_000, cr=9_000_000)],
                       close_args=["--ratio", "300000"])
    # facturables = 100k+140k+60k = 300k → 1,0 h (la lectura de caché NO computa)
    assert res["horas_ia"] == 1.0
    assert res["duracion"] == "1h"


def test_ratio_de_calibration_mediana(entorno, tmp_path):
    tmp, tdir, state = entorno
    cal = tmp_path / "CALIBRATION.md"
    cal.write_text(
        "| Iniciativa | tokens/hora (medido) |\n|---|---|\n"
        "| a | 200000 |\n| b | 400.000 |\n| c | ~250000 |\n", encoding="utf-8")
    res = _start_close(tdir, state, antes=[],
                       despues=[_rec("m1", inp=250_000)],
                       close_args=["--calibration", str(cal)])
    assert res["ratio_usado"] == 250_000  # mediana de {200k, 250k, 400k}
    assert "CALIBRATION" in res["ratio_origen"]
    assert res["horas_ia"] == 1.0


def test_ratio_default_marcado_no_calibrado(entorno):
    _, tdir, state = entorno
    res = _start_close(tdir, state, antes=[], despues=[_rec("m1", inp=100)])
    assert res["ratio_usado"] == um.DEFAULT_RATIO
    assert "no calibrado" in res["ratio_origen"]


# --------------------------------------------------------------- idempotencia

def test_reclose_misma_ventana_sustituye(entorno):
    """Re-cerrar el mismo artefacto re-mide la MISMA ventana (sustituye, no acumula)."""
    _, tdir, state = entorno
    res1 = _start_close(tdir, state, antes=[], despues=[_rec("m1", inp=100, out=10)])
    rc, res2 = _run(None, ["close", "--artefacto", "a.md", "--state", str(state),
                           "--transcript-dir", str(tdir)])
    assert res2["tokens_reales"]["entrada"] == res1["tokens_reales"]["entrada"] == 100


def test_marcadores_concurrentes_independientes(entorno):
    _, tdir, state = entorno
    _write(tdir / "sesion.jsonl", [])
    for art in ("spec.md", "evaluation.md"):
        rc, _ = _run(None, ["start", "--artefacto", art, "--state", str(state),
                            "--transcript-dir", str(tdir)])
        assert rc == 0
    with open(tdir / "sesion.jsonl", "a", encoding="utf-8") as f:
        f.write(_rec("m1", inp=100, out=10) + "\n")
    for art in ("spec.md", "evaluation.md"):
        rc, res = _run(None, ["close", "--artefacto", art, "--state", str(state),
                              "--transcript-dir", str(tdir)])
        assert res["tokens_reales"]["entrada"] == 100  # cada marcador, su ventana

    rc, st = _run(None, ["status", "--state", str(state)])
    assert rc == 0 and len(st["marcadores"]) == 2
    assert all(m["cerrado"] for m in st["marcadores"])


# ----------------------------------------------------------------- fmt (C-08)

@pytest.mark.parametrize("horas,esperado", [
    ("0,53", "32m"),      # el caso del usuario
    ("1,53", "1h 32m"),
    ("1.25", "1h 15m"),
    ("18", "18h"),
    ("0", "0m"),
    ("0,005", "0m"),      # <1 min redondea a 0m
    ("0,999", "1h"),      # 59,94 min → 60 → 1h
    ("2", "2h"),
])
def test_fmt(horas, esperado):
    rc, out = _run(None, ["fmt", horas])
    assert rc == 0 and out == esperado


def test_fmt_negativo_error():
    rc, out = _run(None, ["fmt", "-1"])
    assert rc == 2


def test_fmt_infinito_no_crashea():
    rc, out = _run(None, ["fmt", "inf"])
    assert rc == 2  # error limpio, no traceback


# ------------------------------------------------- robustez (revisión lente B)

def test_calibration_notacion_k_y_miles(entorno, tmp_path):
    """'300k' y '300,000' deben leerse como 300000, no 300 (bug alta de la revisión)."""
    tmp, tdir, state = entorno
    cal = tmp_path / "CALIBRATION.md"
    cal.write_text(
        "| slug | tokens/hora |\n|---|---|\n"
        "| a | 300k |\n| b | 300.000 |\n| c | 300,000 |\n", encoding="utf-8")
    res = _start_close(tdir, state, antes=[], despues=[_rec("m1", inp=300_000)],
                       close_args=["--calibration", str(cal)])
    assert res["ratio_usado"] == 300_000
    assert res["horas_ia"] == 1.0


def test_calibration_ignora_tablas_posteriores_y_fuera_de_rango(entorno, tmp_path):
    tmp, tdir, state = entorno
    cal = tmp_path / "CALIBRATION.md"
    cal.write_text(
        "| slug | tokens/hora |\n|---|---|\n| a | 250000 |\n"
        "\n## Otra tabla\n\n| fecha | precio |\n|---|---|\n| 2026-01-01 | 15 |\n",
        encoding="utf-8")
    res = _start_close(tdir, state, antes=[], despues=[_rec("m1", inp=250_000)],
                       close_args=["--calibration", str(cal)])
    assert res["ratio_usado"] == 250_000  # el '15' de la otra tabla NO entra en la mediana


def test_state_corrupto_degrada_sin_crashear(entorno):
    """State con formas inesperadas → exit 0 y degradación con aviso (contrato 'nunca bloquea')."""
    _, tdir, state = entorno
    _write(tdir / "sesion.jsonl", [_rec("m1", inp=10)])
    for corrupto in ('{"a.md": 5}', '["x"]', "{esto no es json"):
        state.write_text(corrupto, encoding="utf-8")
        rc, res = _run(None, ["close", "--artefacto", "a.md", "--state", str(state),
                              "--transcript-dir", str(tdir)])
        assert rc == 0 and res["fuente"] == "estimado", corrupto
        rc, _ = _run(None, ["status", "--state", str(state)])
        assert rc == 0
        state.write_text(corrupto, encoding="utf-8")
        rc, _ = _run(None, ["start", "--artefacto", "b.md", "--state", str(state),
                            "--transcript-dir", str(tdir)])
        assert rc == 0


def test_marcador_sin_offsets_degrada_con_aviso(entorno):
    """Marcador viejo/a mano sin offsets: NO contar todo el histórico como ventana."""
    _, tdir, state = entorno
    _write(tdir / "sesion.jsonl", [_rec("m1", inp=999_999)])
    state.write_text(json.dumps({"a.md": {"inicio": "2026-08-11T00:00:00Z"}}), encoding="utf-8")
    rc, res = _run(None, ["close", "--artefacto", "a.md", "--state", str(state),
                          "--transcript-dir", str(tdir)])
    assert rc == 0 and res["fuente"] == "estimado"
    assert any("sin offsets" in a for a in res["avisos"])


def test_fichero_truncado_tras_marcador_avisa_y_relee(entorno):
    _, tdir, state = entorno
    _write(tdir / "sesion.jsonl", [_rec("viejo", inp=5000, out=5000)] * 3)
    rc, _ = _run(None, ["start", "--artefacto", "a.md", "--state", str(state),
                        "--transcript-dir", str(tdir)])
    _write(tdir / "sesion.jsonl", [_rec("nuevo", inp=777, out=111)])  # truncado+reescrito
    rc, res = _run(None, ["close", "--artefacto", "a.md", "--state", str(state),
                          "--transcript-dir", str(tdir)])
    assert rc == 0 and res["fuente"] == "medido"
    assert res["tokens_reales"]["entrada"] == 777  # releído completo, no perdido
    assert any("truncado" in a for a in res["avisos"])


def test_usage_no_numerico_no_revienta_la_ventana(entorno):
    _, tdir, state = entorno
    malo = json.dumps({"type": "assistant", "message": {"id": "mx", "usage": {
        "input_tokens": "N/A", "output_tokens": 7}}})
    res = _start_close(tdir, state, antes=[], despues=[_rec("m1", inp=500), malo])
    assert res["fuente"] == "medido"
    assert res["tokens_reales"]["entrada"] == 500  # el válido no se pierde
    assert res["tokens_reales"]["salida"] == 7     # el campo bueno del malo se suma
    assert any("no numéricos" in a for a in res["avisos"])


def test_registros_sin_id_no_colapsan(entorno):
    _, tdir, state = entorno
    sin_id = [json.dumps({"type": "assistant", "message": {"usage": {
        "input_tokens": n, "output_tokens": 0}}}) for n in (100, 900)]
    res = _start_close(tdir, state, antes=[], despues=sin_id)
    assert res["tokens_reales"]["entrada"] == 1000  # 100+900, no solo el último
    assert res["tokens_reales"]["respuestas"] == 2


def test_ratio_cero_rechazado_y_precios_a_cero_no_fiables(entorno):
    tmp, tdir, state = entorno
    # --ratio 0 debe rechazarse como error de uso (no caer al default en silencio)
    _write(tdir / "s.jsonl", [])
    with pytest.raises(SystemExit):
        _run(None, ["close", "--artefacto", "a.md", "--state", str(state),
                    "--transcript-dir", str(tdir), "--ratio", "0"])
    # precios input/output a 0 → no fiables aunque verificadoEl sea reciente (C-01/T-02)
    rates = _rates(tmp, input_p=0, output_p=0, verificado=HOY)
    res = _start_close(tdir, state, antes=[], despues=[_rec("m1", inp=1000)],
                       close_args=["--rates", rates])
    assert res["eur"] is None


def test_usd_sin_tipo_de_cambio_no_asume_paridad(entorno, tmp_path):
    tmp, tdir, state = entorno
    f = tmp_path / "rates-sin-fx.json"
    f.write_text(json.dumps({"precioTokens": {
        "moneda": "USD", "input": 15.0, "output": 75.0, "verificadoEl": HOY}}),
        encoding="utf-8")
    res = _start_close(tdir, state, antes=[], despues=[_rec("m1", inp=1_000_000)],
                       close_args=["--rates", str(f)])
    assert res["eur"] is None  # sin fx no se inventa 1:1
    assert any("tipoCambio" in a for a in res["avisos"])


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
