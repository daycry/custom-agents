#!/usr/bin/env python3
"""Test de `scripts/bench-session-end.py` (session-end-durable-capture T-07, CA-02).

5 iteraciones (rápido en CI) con umbrales LAXOS: lo que se prueba es el contrato del script
(percentiles calculados, `--json`, exit 1 solo si una aserción falla, exit 2 con uso incorrecto),
no una afirmación de rendimiento — esa la hace `ci.yml.MANUAL-COPY` con 30 iteraciones y los
umbrales reales de CA-02 (p95 ≤ 100 ms / p99 ≤ 300 ms).
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "bench-session-end.py")


def run(*args):
    return subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=60)


def test_bench_5_iteraciones_umbrales_laxos_exit_0():
    r = run("--iterations", "5", "--assert-p95-ms", "5000", "--assert-p99-ms", "10000", "--json")
    assert r.returncode == 0, r.stderr
    d = json.loads(r.stdout)
    assert d["iterations"] == 5
    assert d["p95_ms"] <= 5000 and d["p99_ms"] <= 10000
    assert "fallos" not in d


def test_bench_umbral_imposible_falla_exit_1():
    r = run("--iterations", "5", "--assert-p95-ms", "0", "--json")
    assert r.returncode == 1
    d = json.loads(r.stdout)
    assert d["fallos"] and "p95" in d["fallos"][0]


def test_bench_sin_aserciones_nunca_falla():
    r = run("--iterations", "5", "--json")
    assert r.returncode == 0
    assert "fallos" not in json.loads(r.stdout)


def test_bench_uso_incorrecto_exit_2():
    r = run("--iterations", "0")
    assert r.returncode == 2


def test_bench_texto_por_defecto():
    r = run("--iterations", "5")
    assert r.returncode == 0 and "iterations=5" in r.stdout


def test_bench_mide_in_process_no_solo_subproceso(tmp_path):
    """Gap 71: la medida que se assertea es IN-PROCESS (`journal.capture_end` cronometrado
    directamente), no dominada por el arranque del intérprete — debe quedar muy por debajo de lo
    que tardaría un subproceso Python (decenas de ms)."""
    # MEDIANA, no p99: la cola in-process en un runner de CI cargado supera los 20 ms sin que el bench
    # mida nada distinto (PR #10, run 35443037756). La propiedad es «in-process, no subproceso»: la
    # mediana in-process tiene que quedar muy por debajo de lo que tarda un arranque de Python.
    r = run("--iterations", "10", "--json")
    assert r.returncode == 0, r.stderr
    d = json.loads(r.stdout)
    assert d["p50_ms"] < 20, f"p50_ms={d['p50_ms']} sugiere que se sigue midiendo el subproceso"


def test_bench_reporta_e2e_p50_informativo_sin_assertarlo(tmp_path):
    """Gap 71: `e2e_p50_ms` se reporta aparte (informativo, incluye el arranque de Python) y NUNCA
    entra en las aserciones de `--assert-p95-ms`/`--assert-p99-ms` (que siguen siendo in-process)."""
    # Umbral ADAPTATIVO, no 20 ms fijos: en un runner de CI cargado el p95 in-process superó los 20 ms y
    # el test fallaba por la máquina, no por el bench (PR #9, run 35422462468). Se mide primero sin
    # aserción y se exige después un p95 con holgura x4 (mínimo 20 ms); lo que se prueba aquí es que
    # `e2e_p50_ms` se reporta y NO entra en la aserción, no la velocidad absoluta de la máquina.
    r0 = run("--iterations", "5", "--e2e-iterations", "2", "--json")
    assert r0.returncode == 0, r0.stderr
    d0 = json.loads(r0.stdout)
    umbral_ms = max(20.0, float(d0["p95_ms"]) * 4)
    r = run("--iterations", "5", "--e2e-iterations", "2", "--assert-p95-ms", str(umbral_ms), "--json")
    assert r.returncode == 0, r.stderr
    d = json.loads(r.stdout)
    assert "e2e_p50_ms" in d
    # mediana contra mediana: comparar la cola in-process (p95) con la mediana e2e mezclaba ruido de
    # cola con tendencia central y fallaba en runners cargados (PR #10, rerun del run 35443037756)
    assert d["e2e_p50_ms"] > d["p50_ms"], "e2e (con arranque de Python) debe ser más lento que in-process"
    # discriminante cuando la máquina lo permite: si el e2e queda POR ENCIMA del umbral y aun así el
    # exit fue 0, queda demostrado que la aserción no lo tuvo en cuenta (si no lo supera, no concluye)
    if d["e2e_p50_ms"] > umbral_ms:
        assert d["p95_ms"] <= umbral_ms


def test_bench_sin_e2e_iterations_omite_el_campo():
    r = run("--iterations", "5", "--e2e-iterations", "0", "--json")
    assert r.returncode == 0
    assert "e2e_p50_ms" not in json.loads(r.stdout)


def test_bench_detecta_captura_que_no_escribe_nada(tmp_path, monkeypatch):
    """Gap 71: si `capture_end` no deja envelope, el bench falla con un `FALLO` explícito, no con
    percentiles perfectos de una función que no hizo nada."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("bench_mod", SCRIPT)
    bench = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bench)

    class _Falso:
        @staticmethod
        def capture_end(root, payload):
            return None   # nunca escribe nada

    monkeypatch.setattr(bench, "_cargar_journal", lambda: _Falso)
    import pytest
    with pytest.raises(RuntimeError, match="no escribió nada"):
        bench.medir(3, warmup=0, root=str(tmp_path / "proj"))


def test_bench_warmup_iterations_se_descartan_de_la_medida(tmp_path, monkeypatch):
    """Gap 85 de la revisión tramo 2: el descarte de las `warmup` primeras iteraciones no tenía
    ningún test con dientes — un mutante que las contara igual (o que quitara el `if medida:`)
    habría pasado igual. Aquí el reloj se controla por completo: las iteraciones de warmup "tardan"
    10 s cada una y las medidas ~1 ms; si el warmup se colara en `duraciones`, el máximo lo
    delataría."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("bench_mod3", SCRIPT)
    bench = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bench)

    warmup, iterations = 2, 3
    valores = []
    t = 0.0
    for i in range(warmup + iterations):
        if i < warmup:
            valores += [t, t + 10.0]     # 10 s "de warmup" (perf_counter en segundos)
            t += 10.0
        else:
            valores += [t, t + 0.001]    # 1 ms de una medida real
            t += 0.001
    it = iter(valores)
    monkeypatch.setattr(bench.time, "perf_counter", lambda: next(it))

    duraciones = bench.medir(iterations, warmup=warmup, root=str(tmp_path / "proj"))
    assert len(duraciones) == iterations, "debe haber exactamente `iterations` medidas, ni una de warmup"
    assert max(duraciones) < 100, f"duraciones={duraciones}: una medida de warmup (10000 ms) se coló"


def test_bench_e2e_timeout_expired_es_fallo_estructurado(tmp_path, monkeypatch):
    """Gap 78: un `subprocess.TimeoutExpired` en la medida end-to-end produce un `FALLO`
    ESTRUCTURADO (exit 1, JSON con `fallos`), no un traceback sin capturar."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("bench_mod2", SCRIPT)
    bench = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bench)

    def _run_que_expira(*a, **kw):
        raise subprocess.TimeoutExpired(cmd=a[0] if a else "cmd", timeout=kw.get("timeout", 30))

    monkeypatch.setattr(bench.subprocess, "run", _run_que_expira)
    duraciones, error = bench.medir_e2e(1, root=str(tmp_path))
    assert error is not None and "timeout" in error.lower()
