#!/usr/bin/env python3
"""
bench-session-end.py — bench end-to-end de `journal.py capture-end` (session-end-durable-capture T-07).

Mide, sobre un proyecto fixture con rastro del plugin (`docs/roadmap/` + `.claude/`), el tiempo de
PARED de invocar `journal.py capture-end` tal y como lo hace `hooks/session-journal.sh` de verdad:
un subproceso Python con el payload de `SessionEnd` por stdin — el mismo camino que corre en el
teardown de la sesión (sin `bash` de por medio: el arranque de bash es un coste fijo que no depende
del capturador y que ya cubre `tests/test_hooks_shell.py`, no algo que este bench deba medir).

CA-02 de la spec: p95 ≤ 100 ms / p99 ≤ 300 ms en CI de referencia, 30 iteraciones. Este script NO
fija el umbral: lo pasa quien lo invoca (`--assert-p95-ms`/`--assert-p99-ms`), así que la CI puede
usar un margen distinto al de un portátil de desarrollo sin tocar el código.

Uso:
  bench-session-end.py [--iterations N] [--assert-p95-ms MS] [--assert-p99-ms MS] [--json]
Exit:
  0  sin aserciones pedidas, o con ellas y se cumplen
  1  una aserción --assert-p95-ms/--assert-p99-ms no se cumple
  2  uso incorrecto (--iterations < 1)

Lo que este bench NO mide: el arranque de `bash` del hook, el coste de `replay` (materialización,
deliberadamente fuera del teardown), ni el peor caso de un `SIGKILL` a mitad de escritura (eso lo
cubren los tests de corte de `test_outbox.py`/`test_hooks_shell.py`, no un bench de rendimiento).
"""
import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

# Consola Windows (cp1252) o tuberías: reconfigurar ANTES de leer o imprimir nada (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
JOURNAL_PY = os.path.join(ROOT, "agent-kits", "shared", "journal.py")


def _preparar_proyecto(tmp):
    """Rastro mínimo del plugin (`proyecto_con_plugin` de journal.py): sin esto `capture_end` no
    escribe nada y el bench mediría solo el arranque del intérprete, no la escritura atómica."""
    os.makedirs(os.path.join(tmp, "docs", "roadmap"), exist_ok=True)
    os.makedirs(os.path.join(tmp, ".claude"), exist_ok=True)


def _percentil(valores, p):
    """Percentil por interpolación lineal (sin `numpy`: stdlib únicamente, como el resto del plugin)."""
    if not valores:
        return 0.0
    s = sorted(valores)
    k = (len(s) - 1) * (p / 100)
    f, c = int(k), min(int(k) + 1, len(s) - 1)
    if f == c:
        return s[f]
    return s[f] + (s[c] - s[f]) * (k - f)


def medir(iterations, root=None):
    """Lista de duraciones en ms, una por iteración, de `journal.py capture-end` sobre un proyecto
    fixture (uno propio por defecto — `tempfile`, borrado al terminar — o `root` si se da uno)."""
    propio = root is None
    tmp = root or tempfile.mkdtemp(prefix="bench-session-end-")
    try:
        _preparar_proyecto(tmp)
        duraciones = []
        for i in range(iterations):
            payload = json.dumps({"hook_event_name": "SessionEnd", "session_id": f"bench-{i}",
                                  "reason": "other", "cwd": tmp,
                                  "transcript_path": os.path.join(tmp, "no-existe.jsonl")})
            inicio = time.perf_counter()
            subprocess.run([sys.executable, JOURNAL_PY, "capture-end", "--root", tmp],
                           input=payload, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=30)
            duraciones.append((time.perf_counter() - inicio) * 1000)
        return duraciones
    finally:
        if propio:
            shutil.rmtree(tmp, ignore_errors=True)


def resultado_de(duraciones, iterations):
    return {"iterations": iterations,
           "p50_ms": round(_percentil(duraciones, 50), 2),
           "p95_ms": round(_percentil(duraciones, 95), 2),
           "p99_ms": round(_percentil(duraciones, 99), 2),
           "max_ms": round(max(duraciones), 2) if duraciones else 0.0,
           "mean_ms": round(statistics.mean(duraciones), 2) if duraciones else 0.0}


def main(argv=None):
    ap = argparse.ArgumentParser(description="bench end-to-end de journal.py capture-end (CA-02)")
    ap.add_argument("--iterations", type=int, default=30)
    ap.add_argument("--assert-p95-ms", type=float, default=None)
    ap.add_argument("--assert-p99-ms", type=float, default=None)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.iterations < 1:
        print("bench-session-end: --iterations debe ser >= 1", file=sys.stderr)
        return 2
    if not os.path.isfile(JOURNAL_PY):
        print(f"bench-session-end: no encuentro {JOURNAL_PY}", file=sys.stderr)
        return 2

    duraciones = medir(a.iterations)
    r = resultado_de(duraciones, a.iterations)
    fallos = []
    if a.assert_p95_ms is not None and r["p95_ms"] > a.assert_p95_ms:
        fallos.append(f"p95 {r['p95_ms']:.2f} ms > {a.assert_p95_ms} ms")
    if a.assert_p99_ms is not None and r["p99_ms"] > a.assert_p99_ms:
        fallos.append(f"p99 {r['p99_ms']:.2f} ms > {a.assert_p99_ms} ms")
    if fallos:
        r["fallos"] = fallos

    if a.json:
        print(json.dumps(r, ensure_ascii=False))
    else:
        print(f"iterations={r['iterations']} p50={r['p50_ms']}ms p95={r['p95_ms']}ms "
             f"p99={r['p99_ms']}ms max={r['max_ms']}ms mean={r['mean_ms']}ms")
        for f in fallos:
            print(f"FALLO: {f}", file=sys.stderr)
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
