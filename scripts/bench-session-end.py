#!/usr/bin/env python3
"""
bench-session-end.py — bench de `journal.py capture_end` (session-end-durable-capture T-07).

Gap 71 de la revisión tramo 2: la versión anterior medía SOLO por subproceso (`python3 journal.py
capture-end`), una ventana dominada por el arranque del intérprete + el `import` de `journal.py`
(~87% de los ~55 ms medidos entonces) — el número no reflejaba lo que CA-02 quiere acotar (el
COSTE de la captura en sí), y en un runner 2× más lento el coste FIJO podía tirar la CI del repo
entero por ruido ajeno a este cambio. Ahora:

  - la medida que se ASSERTEA (`p50_ms`/`p95_ms`/`p99_ms`/`max_ms`/`mean_ms`) es IN-PROCESS:
    `journal.py` se importa UNA vez y `capture_end(...)` se cronometra N veces sobre el MISMO
    payload fixture, con `--warmup` iteraciones (3 por defecto) descartadas ANTES de medir (primera
    ejecución paga el `import`/JIT de caché de disco; no es lo que se quiere acotar);
  - cada iteración medida COMPRUEBA que la captura escribió/reconoció un envelope de verdad (gap
    71: antes el bench no comprobaba que `capture_end` hiciera nada) — si no, `FALLO: la captura
    no escribió nada` estructurado, no una aserción de percentil que pasaría igual con una función
    que no hace nada;
  - `e2e_p50_ms` se reporta APARTE, informativo, un puñado de subprocesos reales end-to-end (con el
    arranque de Python incluido, el camino real del hook) — nunca se assertea, solo se informa junto
    a los percentiles in-process (ver `docs/observability.md`/`docs/en/observability.md` para qué
    mide cada número exactamente);
  - un `subprocess.TimeoutExpired` en la medida end-to-end produce un `FALLO` ESTRUCTURADO (JSON con
    `fallos`, exit 1), no un traceback sin capturar (gap 78).

CA-02 de la spec: p95 ≤ 100 ms / p99 ≤ 300 ms en CI de referencia, 30 iteraciones. Este script NO
fija el umbral: lo pasa quien lo invoca (`--assert-p95-ms`/`--assert-p99-ms`), así que la CI puede
usar un margen distinto al de un portátil de desarrollo sin tocar el código.

Uso:
  bench-session-end.py [--iterations N] [--warmup N] [--e2e-iterations N]
                       [--assert-p95-ms MS] [--assert-p99-ms MS] [--json]
Exit:
  0  sin aserciones pedidas, o con ellas y se cumplen
  1  una aserción --assert-p95-ms/--assert-p99-ms no se cumple, la captura no escribió nada, o el
     subproceso end-to-end informativo superó su timeout
  2  uso incorrecto (--iterations < 1)

Lo que este bench NO mide: el arranque de `bash` del hook (lo cubre `tests/test_hooks_shell.py`),
el coste de `replay`/`recover` (materialización, deliberadamente fuera del teardown), ni el peor
caso de un `SIGKILL` a mitad de escritura (eso lo cubren los tests de corte de
`test_outbox.py`/`test_hooks_shell.py`, no un bench de rendimiento).
"""
import argparse
import importlib.util
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


def _cargar_journal():
    """Importa `journal.py` UNA vez (coste de import fuera de la medida in-process)."""
    spec = importlib.util.spec_from_file_location("journal_bench_session_end", JOURNAL_PY)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _preparar_proyecto(tmp):
    """Rastro mínimo del plugin (`proyecto_con_plugin` de journal.py): sin esto `capture_end` no
    escribe nada y el bench mediría solo el coste de la función, no la escritura atómica real."""
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


def _payload(tmp, sid):
    return {"hook_event_name": "SessionEnd", "session_id": sid, "reason": "other", "cwd": tmp,
           "transcript_path": os.path.join(tmp, "no-existe.jsonl")}


def _hay_envelope_para(tmp, sid):
    """¿`capture_end` dejó de verdad un envelope reconocible para `sid`? (gap 71: antes el bench no
    comprobaba que la captura escribiera nada — un `capture_end` que no hiciera nada habría pasado
    igual, con percentiles perfectos)."""
    d = os.path.join(tmp, ".claude", "journal", "outbox")
    try:
        nombres = os.listdir(d)
    except OSError:
        return False
    for fn in nombres:
        if not fn.endswith(".json") or fn.startswith(".tmp-"):
            continue
        try:
            with open(os.path.join(d, fn), encoding="utf-8") as fh:
                payload = json.load(fh)
        except (OSError, ValueError):
            continue
        if isinstance(payload, dict) and payload.get("session_id") == sid:
            return True
    return False


def medir(iterations, warmup=3, root=None):
    """Duraciones IN-PROCESS (ms) de `journal.capture_end(...)`, una por iteración MEDIDA (las
    `warmup` primeras se descartan). Lanza `RuntimeError` si alguna iteración medida no deja
    envelope (gap 71: sin esto, una captura rota pasaría el bench con percentiles perfectos)."""
    journal = _cargar_journal()
    propio = root is None
    tmp = root or tempfile.mkdtemp(prefix="bench-session-end-")
    try:
        _preparar_proyecto(tmp)
        duraciones = []
        for i in range(warmup + iterations):
            medida = i >= warmup
            sid = f"bench-{i - warmup}" if medida else f"bench-warmup-{i}"
            payload = _payload(tmp, sid)
            inicio = time.perf_counter()
            journal.capture_end(tmp, payload)
            dur_ms = (time.perf_counter() - inicio) * 1000
            if medida:
                if not _hay_envelope_para(tmp, sid):
                    raise RuntimeError(f"la captura no escribió nada (session_id={sid})")
                duraciones.append(dur_ms)
        return duraciones
    finally:
        if propio:
            shutil.rmtree(tmp, ignore_errors=True)


def medir_e2e(n, root=None, timeout=30):
    """Un puñado de subprocesos reales `python3 journal.py capture-end` (informativo, el camino que
    corre de verdad en el teardown del hook, arranque del intérprete incluido). Devuelve
    `(duraciones, error)`: `error` no-None con un `subprocess.TimeoutExpired` (gap 78: antes esto
    escapaba como traceback sin capturar en vez de un `FALLO` estructurado)."""
    if n <= 0:
        return [], None
    propio = root is None
    tmp = root or tempfile.mkdtemp(prefix="bench-session-end-e2e-")
    duraciones = []
    try:
        _preparar_proyecto(tmp)
        for i in range(n):
            payload = json.dumps(_payload(tmp, f"bench-e2e-{i}"))
            inicio = time.perf_counter()
            try:
                subprocess.run([sys.executable, JOURNAL_PY, "capture-end", "--root", tmp],
                               input=payload, capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=timeout)
            except subprocess.TimeoutExpired:
                return duraciones, f"subproceso end-to-end superó el timeout ({timeout}s) en la iteración {i}"
            duraciones.append((time.perf_counter() - inicio) * 1000)
        return duraciones, None
    finally:
        if propio:
            shutil.rmtree(tmp, ignore_errors=True)


def resultado_de(duraciones, iterations, e2e_duraciones=None):
    r = {"iterations": iterations,
        "p50_ms": round(_percentil(duraciones, 50), 2),
        "p95_ms": round(_percentil(duraciones, 95), 2),
        "p99_ms": round(_percentil(duraciones, 99), 2),
        "max_ms": round(max(duraciones), 2) if duraciones else 0.0,
        "mean_ms": round(statistics.mean(duraciones), 2) if duraciones else 0.0}
    if e2e_duraciones:
        r["e2e_p50_ms"] = round(_percentil(e2e_duraciones, 50), 2)   # informativo; NUNCA se assertea
    return r


def main(argv=None):
    ap = argparse.ArgumentParser(description="bench de journal.py capture_end, in-process (CA-02)")
    ap.add_argument("--iterations", type=int, default=30)
    ap.add_argument("--warmup", type=int, default=3, help="iteraciones descartadas antes de medir")
    ap.add_argument("--e2e-iterations", type=int, default=3,
                    help="subprocesos end-to-end informativos (e2e_p50_ms); 0 para omitirlos")
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

    fallos = []
    try:
        duraciones = medir(a.iterations, warmup=max(0, a.warmup))
    except RuntimeError as e:
        fallos.append(f"FALLO: {e}")
        duraciones = []

    e2e_duraciones, e2e_error = medir_e2e(max(0, a.e2e_iterations))
    if e2e_error:
        fallos.append(f"FALLO: {e2e_error}")

    r = resultado_de(duraciones, a.iterations, e2e_duraciones)
    if a.assert_p95_ms is not None and r["p95_ms"] > a.assert_p95_ms:
        fallos.append(f"p95 {r['p95_ms']:.2f} ms > {a.assert_p95_ms} ms")
    if a.assert_p99_ms is not None and r["p99_ms"] > a.assert_p99_ms:
        fallos.append(f"p99 {r['p99_ms']:.2f} ms > {a.assert_p99_ms} ms")
    if fallos:
        r["fallos"] = fallos

    if a.json:
        print(json.dumps(r, ensure_ascii=False))
    else:
        extra = f" e2e_p50={r['e2e_p50_ms']}ms" if "e2e_p50_ms" in r else ""
        print(f"iterations={r['iterations']} p50={r['p50_ms']}ms p95={r['p95_ms']}ms "
             f"p99={r['p99_ms']}ms max={r['max_ms']}ms mean={r['mean_ms']}ms{extra}")
        for f in fallos:
            print(f, file=sys.stderr)
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
