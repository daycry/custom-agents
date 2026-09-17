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
