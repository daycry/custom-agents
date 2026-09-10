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
from datetime import datetime, timedelta, timezone
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


def test_subagente_anidado_se_suma_con_el_principal(entorno):
    # T-03: los subagentes escriben en <sesion>/subagents/agent-*.jsonl (formato real,
    # incl. isSidechain=True), NO en el .jsonl principal. Antes (glob no recursivo) ese
    # fichero se ignoraba por completo: 43,6 % de los tokens facturables sin contar.
    _, tdir, state = entorno
    _write(tdir / "main.jsonl", [_rec("m1", inp=10, out=5)])  # fuera de ventana (antes del start)
    sesion_dir = tdir / "76684689-5475-48bb-b737-8ca949139c64" / "subagents"
    sesion_dir.mkdir(parents=True)
    subagente = sesion_dir / "agent-a014b85dec1ed31e2.jsonl"
    rc, _ = _run(None, ["start", "--artefacto", "a.md", "--state", str(state),
                        "--transcript-dir", str(tdir)])
    assert rc == 0
    with open(tdir / "main.jsonl", "a", encoding="utf-8") as f:
        f.write(_rec("m2", inp=1, out=1) + "\n")
    _write(subagente, [_rec("s1", inp=300, out=80, sidechain=True)])
    rc, res = _run(None, ["close", "--artefacto", "a.md", "--state", str(state),
                          "--transcript-dir", str(tdir)])
    assert rc == 0
    t = res["tokens_reales"]
    # m1 queda fuera de ventana (antes del start); m2 (principal) y s1 (subagente,
    # creado DENTRO de la ventana) sí se suman: la ventana cruza ambos ficheros
    assert (t["entrada"], t["salida"]) == (301, 81)
    assert t["respuestas"] == 2


def test_subagente_creado_despues_del_start_se_cuenta_entero(entorno):
    # Un subagente lanzado DENTRO de la ventana: su fichero no existe en el snapshot del
    # `start` (offset ausente -> 0), así que se cuenta entero, no solo lo posterior a un
    # offset heredado de otro fichero por error.
    _, tdir, state = entorno
    _write(tdir / "main.jsonl", [_rec("m0", inp=1, out=1)])
    rc, _ = _run(None, ["start", "--artefacto", "a.md", "--state", str(state),
                        "--transcript-dir", str(tdir)])
    assert rc == 0
    subagentes_dir = tdir / "sess-x" / "subagents"
    subagentes_dir.mkdir(parents=True)
    _write(subagentes_dir / "agent-nuevo.jsonl",
           [_rec("sub1", inp=500, out=200), _rec("sub2", inp=100, out=50)])
    rc, res = _run(None, ["close", "--artefacto", "a.md", "--state", str(state),
                          "--transcript-dir", str(tdir)])
    assert rc == 0
    t = res["tokens_reales"]
    assert (t["entrada"], t["salida"]) == (600, 250)
    assert t["respuestas"] == 2


def test_message_id_repetido_entre_principal_y_subagente_cuenta_una_vez(entorno):
    # Intersección real medida en esta máquina: 0 ids compartidos entre sesión principal
    # y subagentes; el código no debe ASUMIRLO — un id repetido entre ambos se cuenta UNA
    # vez (mismo dedupe global que ya aplicaba dentro de un solo fichero).
    _, tdir, state = entorno
    subagentes_dir = tdir / "sess-y" / "subagents"
    subagentes_dir.mkdir(parents=True)
    rc, _ = _run(None, ["start", "--artefacto", "a.md", "--state", str(state),
                        "--transcript-dir", str(tdir)])
    assert rc == 0
    _write(tdir / "main.jsonl", [_rec("compartido", inp=100, out=40)])
    _write(subagentes_dir / "agent-z.jsonl", [_rec("compartido", inp=100, out=40)])
    rc, res = _run(None, ["close", "--artefacto", "a.md", "--state", str(state),
                          "--transcript-dir", str(tdir)])
    assert rc == 0
    t = res["tokens_reales"]
    assert (t["entrada"], t["salida"]) == (100, 40)  # no 200/80: mismo id, una sola vez
    assert t["respuestas"] == 1


def test_docstring_no_afirma_isSidechain_como_mecanismo_de_localizacion():
    # Gap B-6: el docstring viejo decía "isSidechain marca subagentes ... se suman TODOS
    # los .jsonl de la carpeta" (describía un mecanismo que ya no existe: 0 registros
    # isSidechain en el .jsonl PRINCIPAL de una sesión real, y los subagentes viven en
    # ficheros aparte, no intercalados).
    doc = um.__doc__
    assert "isSidechain marca registros de subagentes" not in doc
    assert "se suman TODOS los .jsonl de la carpeta" not in doc


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


# --------------------------------------------------- T-04: filtro por timestamp

def _rec_ts(msg_id, timestamp, inp=0, out=0):
    """Como `_rec`, pero con timestamp EXPLÍCITO (para probar el filtro de ventana)."""
    return json.dumps({
        "type": "assistant", "isSidechain": False, "uuid": f"u-{msg_id}",
        "requestId": f"req-{msg_id}", "timestamp": timestamp,
        "message": {"id": msg_id, "usage": {
            "input_tokens": inp, "output_tokens": out,
            "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}},
    })


def _hermetico(tmp_path):
    """B-7 (revisión R1): `--calibration`/`--rates` a ficheros INEXISTENTES bajo `tmp_path`,
    para que el test no dependa de `docs/roadmap/CALIBRATION.md` ni `.claude/rates.json`
    reales del repo/máquina (ratio y € deterministas, sin fiarse del entorno)."""
    return ["--calibration", str(tmp_path / "no-existe-CALIBRATION.md"),
            "--rates", str(tmp_path / "no-existe-rates.json")]


def test_registro_anterior_al_inicio_en_fichero_nuevo_se_descarta(entorno):
    """Hallazgo T-04: un fichero NO visto en `start` (offset 0, p. ej. un subagente
    reaparecido) ya no cuenta enteros los registros anteriores a la ventana."""
    tmp_path, tdir, state = entorno
    rc, res_start = _run(None, ["start", "--artefacto", "a.md", "--state", str(state),
                                "--transcript-dir", str(tdir)])
    assert rc == 0
    inicio = res_start["inicio"]
    inicio_dt = datetime.strptime(inicio, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    antes = (inicio_dt - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    dentro = (inicio_dt + timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    # fichero nuevo, jamás visto en el snapshot de `start` → offset 0
    _write(tdir / "nuevo.jsonl", [
        _rec_ts("viejo", antes, inp=1000, out=1000),
        _rec_ts("nuevo", dentro, inp=7, out=3),
    ])
    rc, res = _run(None, ["close", "--artefacto", "a.md", "--state", str(state),
                          "--transcript-dir", str(tdir), *_hermetico(tmp_path)])
    assert rc == 0
    t = res["tokens_reales"]
    assert (t["entrada"], t["salida"]) == (7, 3)
    assert any("descartad" in a for a in res["avisos"])


def test_tolerancia_60s_del_filtro_de_ventana(entorno):
    """El filtro admite hasta 60s antes de `inicio` (relojes de fichero vs. `start`)."""
    tmp_path, tdir, state = entorno
    rc, res_start = _run(None, ["start", "--artefacto", "a.md", "--state", str(state),
                                "--transcript-dir", str(tdir)])
    assert rc == 0
    inicio_dt = datetime.strptime(res_start["inicio"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    dentro_tolerancia = (inicio_dt - timedelta(seconds=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    fuera_tolerancia = (inicio_dt - timedelta(seconds=90)).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write(tdir / "nuevo.jsonl", [
        _rec_ts("fuera", fuera_tolerancia, inp=500, out=0),
        _rec_ts("dentro", dentro_tolerancia, inp=9, out=1),
    ])
    rc, res = _run(None, ["close", "--artefacto", "a.md", "--state", str(state),
                          "--transcript-dir", str(tdir), *_hermetico(tmp_path)])
    assert rc == 0
    assert res["tokens_reales"]["entrada"] == 9


def test_marcador_sin_version_degrada_a_estimado(entorno):
    """Un marcador escrito por el código ANTERIOR a T-04 (sin `version`) degrada, no mide."""
    tmp_path, tdir, state = entorno
    _write(tdir / "sesion.jsonl", [])
    state.write_text(json.dumps({
        "a.md": {"inicio": _now_marker(), "transcriptDir": str(tdir), "offsets": {}}
    }), encoding="utf-8")
    with open(tdir / "sesion.jsonl", "a", encoding="utf-8") as f:
        f.write(_rec("m1", inp=100, out=10) + "\n")
    rc, res = _run(None, ["close", "--artefacto", "a.md", "--state", str(state),
                          "--transcript-dir", str(tdir), *_hermetico(tmp_path)])
    assert rc == 0
    assert res["fuente"] == "estimado"
    assert any("anterior al arreglo" in a for a in res["avisos"])


def _now_marker(delta=None):
    dt = datetime.now(timezone.utc)
    if delta is not None:
        dt -= delta
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def test_duracion_reloj_aditiva_no_cambia_duracion(entorno):
    """`duracion_reloj` es NUEVA y aditiva; `duracion` (tokens ÷ ratio) no cambia de semántica."""
    tmp_path, tdir, state = entorno
    res = _start_close(tdir, state, antes=[], despues=[_rec("m1", inp=300_000, out=0)],
                       close_args=["--ratio", "300000", *_hermetico(tmp_path)])
    assert res["fuente"] == "medido"
    assert "duracion_reloj" in res
    assert res["duracion"] == "1h"  # 300k / 300k (ratio explícito) = 1h, como antes de T-04


def test_duracion_reloj_valor_exacto_37_minutos(entorno):
    """B-3 (revisión R1): `duracion_reloj` no tenía oráculo de VALOR, solo de clave (el test
    original solo comprobaba `"duracion_reloj" in res`) — un mutante que devolviera `None` o
    `fmt_horas(0.0)` pasaba la suite entera. `inicio` fijado a 37 minutos antes del cierre →
    "37m" exacto."""
    tmp_path, tdir, state = entorno
    state.write_text(json.dumps({
        "a.md": {"version": 2, "inicio": _now_marker(delta=timedelta(minutes=37)),
                 "transcriptDir": str(tdir), "offsets": {}}
    }), encoding="utf-8")
    rc, res = _run(None, ["close", "--artefacto", "a.md", "--state", str(state),
                          "--transcript-dir", str(tdir), *_hermetico(tmp_path)])
    assert rc == 0
    assert res["duracion_reloj"] == "37m"


def test_marcador_version2_sin_inicio_degrada_con_aviso(entorno):
    """B-5 (revisión R1): un marcador `version: 2` sin `inicio` desactivaba en silencio el
    filtro por timestamp (`inicio=None` → `_sum_usage_window` no filtra nada) y volvía al bug
    exacto que T-04 arregla, reportando `fuente: medido`. `offsets` ya tenía esta defensa
    (rama "marcador sin offsets"); `inicio` no."""
    tmp_path, tdir, state = entorno
    hace_30_dias = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write(tdir / "viejo.jsonl", [_rec_ts("viejo", hace_30_dias, inp=777777, out=1)])
    state.write_text(json.dumps({
        "a.md": {"version": 2, "transcriptDir": str(tdir), "offsets": {}}   # sin "inicio"
    }), encoding="utf-8")
    rc, res = _run(None, ["close", "--artefacto", "a.md", "--state", str(state),
                          "--transcript-dir", str(tdir), *_hermetico(tmp_path)])
    assert rc == 0
    assert res["fuente"] == "estimado"
    assert res["tokens_reales"] is None
    assert any("inicio" in a for a in res["avisos"])


def test_marcador_con_inicio_naive_close_no_revienta_y_mide(entorno):
    """B-1 (revisión R1): un `inicio` ISO SIN zona (ni `Z` ni offset — p. ej. un marcador
    editado a mano) hacía morir `close` (`TypeError` sin capturar al restar un datetime
    *naive* de uno *aware* para `duracion_reloj`, en `:491`). `_parse_iso` ahora asume UTC
    cuando falta la zona: `close` sigue midiendo con normalidad, sin reventar."""
    tmp_path, tdir, state = entorno
    inicio_naive = (datetime.now(timezone.utc) - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%S")
    assert "Z" not in inicio_naive and "+" not in inicio_naive
    state.write_text(json.dumps({
        "a.md": {"version": 2, "inicio": inicio_naive, "transcriptDir": str(tdir), "offsets": {}}
    }), encoding="utf-8")
    _write(tdir / "nuevo.jsonl", [_rec("m1", inp=100, out=10)])
    rc, res = _run(None, ["close", "--artefacto", "a.md", "--state", str(state),
                          "--transcript-dir", str(tdir), *_hermetico(tmp_path)])
    assert rc == 0
    assert res["fuente"] == "medido"
    assert res["duracion_reloj"] is not None


def test_registro_con_timestamp_naive_entre_correctos_se_cuenta(entorno):
    """B-1 (revisión R1): un registro con `timestamp` sin zona, mezclado entre 100 correctos,
    ya NO pierde la ventana entera — antes `_sum_usage_window` lanzaba `TypeError` al comparar
    ese timestamp *naive* con `inicio` *aware*, lo capturaba el `except Exception` de
    `cmd_close` (`:260`/`:491`) y degradaba TODOS los tokens a estimado por un solo registro."""
    tmp_path, tdir, state = entorno
    rc, res_start = _run(None, ["start", "--artefacto", "a.md", "--state", str(state),
                                "--transcript-dir", str(tdir)])
    assert rc == 0
    naive_ahora = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")  # sin 'Z': naive
    lineas = [_rec(f"m{i}", inp=1, out=1) for i in range(100)]
    lineas.append(_rec_ts("naive", naive_ahora, inp=1, out=1))
    _write(tdir / "nuevo.jsonl", lineas)
    rc, res = _run(None, ["close", "--artefacto", "a.md", "--state", str(state),
                          "--transcript-dir", str(tdir), *_hermetico(tmp_path)])
    assert rc == 0
    assert res["fuente"] == "medido"
    assert res["tokens_reales"]["respuestas"] == 101


def test_b4_marcadores_encadenados_dentro_de_60s_duplican_solape(entorno):
    """B-4 (revisión R1, documentado — NO corregido, fuera de alcance declarado): un fichero de
    transcript ya EXISTENTE al hacer `start` queda correctamente baselineado (su contenido previo
    no cuenta) — el hueco está en un fichero NUEVO que aparece DESPUÉS del `start` del siguiente
    marcador (p. ej. un subagente que reescribe/duplica registros en un fichero propio, ver el
    docstring de `_sum_usage_window` sobre 0 intersecciones «medidas, pero no asumidas»): al ser
    la primera vez que ese marcador lo ve, arranca en offset 0, y si sus timestamps caen dentro de
    la tolerancia de 60 s del `inicio` de este marcador, se cuentan otra vez aunque YA los hubiera
    medido el marcador anterior. A mide 100, B mide 105 (100 «reaparecidos» + 5 nuevos) en vez de
    5. No es una regresión (antes de esta iniciativa se recontaba el transcript ENTERO en este
    caso), pero es la grieta que documenta `docs/observability.md` (+EN). Este test fija el
    comportamiento ACTUAL a propósito (no lo arregla) para que no cambie en silencio."""
    tmp_path, tdir, state = entorno
    rc, res_a = _run(None, ["start", "--artefacto", "a.md", "--state", str(state),
                            "--transcript-dir", str(tdir)])
    assert rc == 0
    inicio_a_dt = datetime.strptime(res_a["inicio"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    ts_viejos = (inicio_a_dt + timedelta(seconds=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write(tdir / "principal.jsonl", [_rec_ts(f"m{i}", ts_viejos, inp=10, out=0) for i in range(10)])
    rc, res_close_a = _run(None, ["close", "--artefacto", "a.md", "--state", str(state),
                          "--transcript-dir", str(tdir), *_hermetico(tmp_path)])
    assert rc == 0
    assert res_close_a["tokens_reales"]["entrada"] == 100

    # B arranca casi inmediatamente (< 60 s) tras el close de A; "principal.jsonl" YA existía al
    # arrancar B, así que su `start` lo baselinea correctamente (offset = tamaño actual)
    rc, res_b = _run(None, ["start", "--artefacto", "b.md", "--state", str(state),
                            "--transcript-dir", str(tdir)])
    assert rc == 0
    inicio_b_dt = datetime.strptime(res_b["inicio"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    ts_nuevo = (inicio_b_dt + timedelta(seconds=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    # Un fichero NUEVO aparece DESPUÉS del `start` de B (nunca visto bajo el artefacto "b.md" →
    # offset 0) y "reaparecen" en él los mismos registros que A ya midió, junto a uno genuinamente
    # nuevo — simula un subagente que reescribe contexto ya contado en su propio transcript
    (tdir / "subagents").mkdir(exist_ok=True)
    registros_rotados = [_rec_ts(f"m{i}", ts_viejos, inp=10, out=0) for i in range(10)]
    registros_rotados.append(_rec_ts("mNuevo", ts_nuevo, inp=5, out=0))
    _write(tdir / "subagents" / "rotado.jsonl", registros_rotados)
    rc, res_close_b = _run(None, ["close", "--artefacto", "b.md", "--state", str(state),
                          "--transcript-dir", str(tdir), *_hermetico(tmp_path)])
    assert rc == 0
    # Límite conocido: 105 (100 «reaparecidos» + 5 nuevos), no 5 — ver nota en observability.md
    assert res_close_b["tokens_reales"]["entrada"] == 105


def test_b4_con_90s_de_separacion_no_hay_solape(entorno):
    """Contraste del mismo B-4: si B arranca fuera de la tolerancia de 60 s respecto a los
    timestamps ya medidos por A, no hay doble conteo (5, el valor correcto)."""
    tmp_path, tdir, state = entorno
    rc, res_a = _run(None, ["start", "--artefacto", "a.md", "--state", str(state),
                            "--transcript-dir", str(tdir)])
    assert rc == 0
    inicio_a_dt = datetime.strptime(res_a["inicio"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    ts_viejos = (inicio_a_dt + timedelta(seconds=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write(tdir / "nuevo.jsonl", [_rec_ts(f"m{i}", ts_viejos, inp=10, out=0) for i in range(10)])
    rc, res_close_a = _run(None, ["close", "--artefacto", "a.md", "--state", str(state),
                          "--transcript-dir", str(tdir), *_hermetico(tmp_path)])
    assert rc == 0
    assert res_close_a["tokens_reales"]["entrada"] == 100

    # Marcador B se escribe a mano con `inicio` 90 s después de los timestamps viejos
    inicio_b_forzado = (inicio_a_dt + timedelta(seconds=95)).strftime("%Y-%m-%dT%H:%M:%SZ")
    estado = json.loads(state.read_text(encoding="utf-8"))
    estado["b.md"] = {"version": 2, "inicio": inicio_b_forzado, "transcriptDir": str(tdir),
                       "offsets": {}}
    state.write_text(json.dumps(estado), encoding="utf-8")
    ts_nuevo = (datetime.strptime(inicio_b_forzado, "%Y-%m-%dT%H:%M:%SZ")
                .replace(tzinfo=timezone.utc) + timedelta(seconds=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(tdir / "nuevo.jsonl", "a", encoding="utf-8") as f:
        f.write(_rec_ts("mNuevo", ts_nuevo, inp=5, out=0) + "\n")
    rc, res_close_b = _run(None, ["close", "--artefacto", "b.md", "--state", str(state),
                          "--transcript-dir", str(tdir), *_hermetico(tmp_path)])
    assert rc == 0
    assert res_close_b["tokens_reales"]["entrada"] == 5


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


def test_ratio_default_marcado_no_calibrado(entorno, tmp_path):
    """Sin CALIBRATION.md se usa el default y se marca como no calibrado.
    El test apunta --calibration a una ruta INEXISTENTE a propósito: si no, leería
    el CALIBRATION.md real del repo (que ya está calibrado) y el resultado dependería
    del cwd — así fallaba al crear el fichero de calibración de verdad."""
    _, tdir, state = entorno
    inexistente = tmp_path / "no-hay" / "CALIBRATION.md"
    res = _start_close(tdir, state, antes=[], despues=[_rec("m1", inp=100)],
                       close_args=["--calibration", str(inexistente)])
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


# --------------------------------------------- localizacion de transcripciones (sin --transcript-dir)
#
# GOT-010: los 28 tests de arriba inyectan --transcript-dir, así que
# _project_transcript_dir() tenía cobertura cero. Estos ejercitan la codificación del
# cwd (HOME/cwd redirigidos a tmp_path) SIN ese flag. Oráculo: nombres de carpeta REALES
# de ~/.claude/projects/ en esta máquina (T-01 de usage-meter-transcripts, 2026-09-10).

def test_encoding_ruta_windows_con_espacios_y_puntos():
    # Carpeta real observada en esta máquina para este mismo repo (con espacios y puntos).
    cwd = r"C:\Users\46066917X\OneDrive - Imagina Media Audiovisual S.L\claude-cowork\custom-agents"
    esperado = "C--Users-46066917X-OneDrive---Imagina-Media-Audiovisual-S-L-claude-cowork-custom-agents"
    assert um._encode_cwd(cwd) == esperado


def test_encoding_ruta_windows_con_segmento_oculto():
    # Variante de la segunda carpeta real de esta máquina (`.claude-mem-observer`), con un
    # segmento extra CON ESPACIO para que discrimine de la regex vieja `[/\\.:]` (que no
    # toca espacios ni barras): con ambas regexes el segmento oculto sale igual, así que
    # sin el espacio este test no distinguía el fix del bug (gap B-7 de la revisión).
    # Ninguna carpeta real de esta máquina contiene '_'; ese supuesto queda en el
    # docstring de `_encode_cwd`, no en un test (criterio de aceptación de T-01).
    cwd = r"C:\Users\46066917X\.claude-mem-observer\my sessions"
    esperado = "C--Users-46066917X--claude-mem-observer-my-sessions"
    assert um._encode_cwd(cwd) == esperado


def test_encoding_ruta_posix_sin_caracteres_especiales():
    # Sin regresión en Linux/CI: una ruta POSIX simple sigue codificando solo las '/'.
    assert um._encode_cwd("/home/u/proj") == "-home-u-proj"


def test_project_transcript_dir_localiza_sin_transcript_dir(monkeypatch, tmp_path):
    # HOME (y USERPROFILE en Windows, que Path.home() consulta) redirigidos a tmp_path;
    # cwd redirigido a un `cwd` LITERAL (no bajo tmp_path: no hace falta que exista en
    # disco, solo que os.getcwd() lo devuelva). El nombre de carpeta esperado es el
    # LITERAL real de esta máquina (oráculo), no una llamada a `_encode_cwd` (gap B-3 de
    # la revisión: usar la función bajo prueba para fabricar su propio oráculo es una
    # tautología que no detectaría una regresión en la propia función).
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    cwd_literal = r"C:\Users\46066917X\OneDrive - Imagina Media Audiovisual S.L\claude-cowork\custom-agents"
    encoded_literal = "C--Users-46066917X-OneDrive---Imagina-Media-Audiovisual-S-L-claude-cowork-custom-agents"
    (home / ".claude" / "projects" / encoded_literal).mkdir(parents=True)
    monkeypatch.setattr(um.os, "getcwd", lambda: cwd_literal)
    monkeypatch.setattr(um.Path, "home", classmethod(lambda cls: home))
    resultado = um._project_transcript_dir()
    assert resultado is not None
    assert resultado.name == encoded_literal


def test_project_transcript_dir_ausente_devuelve_none(monkeypatch, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setattr(um.os, "getcwd", lambda: str(tmp_path / "no-tiene-carpeta"))
    monkeypatch.setattr(um.Path, "home", classmethod(lambda cls: home))
    assert um._project_transcript_dir() is None


def test_project_transcript_dir_respaldo_root(monkeypatch, tmp_path):
    # Gap B-8: el respaldo `Path("/root/.claude/projects")` estaba sin cobertura. `Path.home()`
    # (Windows y POSIX) apunta a un tmp_path SIN carpeta de proyecto; se ejercita el respaldo
    # sustituyendo directamente `um.Path` por un patch que redirige "/root" a otro tmp_path
    # con la carpeta ya creada.
    home_vacio = tmp_path / "home-sin-proyecto"
    home_vacio.mkdir()
    root_falso = tmp_path / "root-falso"
    cwd_literal = r"C:\Users\46066917X\OneDrive - Imagina Media Audiovisual S.L\claude-cowork\custom-agents"
    encoded_literal = "C--Users-46066917X-OneDrive---Imagina-Media-Audiovisual-S-L-claude-cowork-custom-agents"
    (root_falso / ".claude" / "projects" / encoded_literal).mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home_vacio))
    monkeypatch.setenv("USERPROFILE", str(home_vacio))
    monkeypatch.setattr(um.os, "getcwd", lambda: cwd_literal)

    real_path_cls = um.Path

    class _PathConRootRedirigido(real_path_cls):
        # pathlib (3.12+) resuelve los args reales en __init__, no en __new__
        # (__new__ solo decide la subclase concreta): hay que redirigir aquí.
        def __init__(self, *args, **kwargs):
            if len(args) == 1 and str(args[0]) == "/root/.claude/projects":
                args = (root_falso, ".claude", "projects")
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(_PathConRootRedirigido, "home", classmethod(lambda cls: home_vacio))
    monkeypatch.setattr(um, "Path", _PathConRootRedirigido)

    resultado = um._project_transcript_dir()
    assert resultado is not None
    assert resultado.name == encoded_literal


def test_close_sin_transcript_dir_usa_localizacion_real(monkeypatch, tmp_path):
    # Extremo a extremo: close SIN --transcript-dir encuentra la carpeta creada con el
    # nombre codificado y devuelve fuente="medido" (el criterio de aceptación de T-01).
    # El `cwd` y su nombre de carpeta esperado son LITERALES (segunda carpeta real de
    # esta máquina), no el resultado de llamar a `_encode_cwd` (gap B-3): así, si la
    # codificación se rompiera, el fixture seguiría teniendo el nombre CORRECTO y el
    # test detectaría el fallo en vez de "seguir la corrupción" del código bajo prueba.
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    cwd_literal = r"C:\Users\46066917X\.claude-mem-observer\sessions"
    encoded_literal = "C--Users-46066917X--claude-mem-observer-sessions"
    tdir = home / ".claude" / "projects" / encoded_literal
    tdir.mkdir(parents=True)
    _write(tdir / "sesion.jsonl", [_rec("m1", inp=1000, out=500)])
    monkeypatch.setattr(um.os, "getcwd", lambda: cwd_literal)
    monkeypatch.setattr(um.Path, "home", classmethod(lambda cls: home))
    state = tmp_path / "usage-state.json"
    rc, _ = _run(None, ["start", "--artefacto", "b.md", "--state", str(state)])
    assert rc == 0
    with open(tdir / "sesion.jsonl", "a", encoding="utf-8") as f:
        f.write(_rec("m2", inp=200, out=100) + "\n")
    rc, res = _run(None, ["close", "--artefacto", "b.md", "--state", str(state),
                          "--calibration", str(tmp_path / "no-existe-CALIBRATION.md")])
    assert rc == 0
    assert res["fuente"] == "medido"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
