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
    r = run("--iterations", "10", "--json")
    assert r.returncode == 0, r.stderr
    d = json.loads(r.stdout)
    assert d["p99_ms"] < 20, f"p99_ms={d['p99_ms']} sugiere que se sigue midiendo el subproceso"


def test_bench_reporta_e2e_p50_informativo_sin_assertarlo(tmp_path):
    """Gap 71: `e2e_p50_ms` se reporta aparte (informativo, incluye el arranque de Python) y NUNCA
    entra en las aserciones de `--assert-p95-ms`/`--assert-p99-ms` (que siguen siendo in-process)."""
    r = run("--iterations", "5", "--e2e-iterations", "2", "--assert-p95-ms", "20", "--json")
    assert r.returncode == 0, r.stderr
    d = json.loads(r.stdout)
    assert "e2e_p50_ms" in d
    assert d["e2e_p50_ms"] > d["p95_ms"], "e2e (con arranque de Python) debe ser más lento que in-process"


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
