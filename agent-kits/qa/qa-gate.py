#!/usr/bin/env python3
"""
qa-gate.py — veredicto DETERMINISTA del agente qa (patrón lib-guardrail: el
umbral lo decide un exit code, no el juicio del LLM).

Umbral verde (exit 0):
  - 0 tests `unexpected` (failed), y
  - 0 tests `flaky` SIN justificación (las justificaciones se pasan con
    --justify <fichero.json>: { "<título del test>": "<motivo no vacío>" }).
La ausencia de evidencia es rojo: results.json inexistente o malformado → exit 1.

Uso:
  python3 qa-gate.py <ruta/a/results.json> [--justify justificaciones.json]
Salida: resumen JSON por stdout (para pegar como evidencia en el informe)
        + exit 0 (verde) / 1 (no verde).

Esquema soportado: reporter `json` de Playwright (stats.expected/unexpected/
flaky/skipped). Si no hay bloque `stats`, se recorren las suites y se calcula
el outcome por test (expected / unexpected / flaky / skipped).
"""
import argparse
import json
import os
import sys


def walk_tests(suite, out):
    for spec in suite.get("specs", []):
        for test in spec.get("tests", []):
            results = test.get("results", [])
            statuses = [r.get("status") for r in results]
            expected = test.get("expectedStatus", "passed")
            title = spec.get("title", "(sin título)")
            fid = f"{spec.get('file', '')}::{title}" if spec.get("file") else title
            if not results:
                out.append((title, fid, "interrupted"))   # nunca corrió: NO es verde
                continue
            final = statuses[-1]
            if "interrupted" in statuses or final == "interrupted":
                out.append((title, fid, "interrupted"))   # ejecución abortada: NO es verde
            elif all(s == expected for s in statuses):
                out.append((title, fid, "expected"))
            elif final == expected and len(statuses) > 1:
                out.append((title, fid, "flaky"))          # falló y pasó al reintento
            elif final == "skipped":
                out.append((title, fid, "skipped"))
            else:
                out.append((title, fid, "unexpected"))
    for child in suite.get("suites", []):
        walk_tests(child, out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results", help="ruta a results.json del reporter json de Playwright")
    ap.add_argument("--justify", help="JSON {titulo_test: motivo} para flaky justificados")
    args = ap.parse_args()

    def rojo(motivo, extra=None):
        print(json.dumps({"verdict": "NO-VERDE", "reason": motivo, **(extra or {})},
                         ensure_ascii=False, indent=2))
        sys.exit(1)

    if not os.path.isfile(args.results):
        rojo("sin resultados: results.json no existe (la ausencia de evidencia es rojo)")
    try:
        data = json.load(open(args.results, encoding="utf-8"))
    except Exception as e:
        rojo(f"results.json malformado: {e}")

    justif = {}
    if args.justify:
        try:
            justif = json.load(open(args.justify, encoding="utf-8"))
        except Exception as e:
            rojo(f"fichero de justificaciones ilegible: {e}")
        if not isinstance(justif, dict):
            rojo("las justificaciones deben ser un objeto {test: motivo}")

    # Errores top-level del runner (forbidOnly violado, webserver caído...) → rojo.
    run_errors = data.get("errors") or []
    if run_errors:
        rojo("el runner reportó errores de ejecución", {
            "errors": [str(e.get("message", e))[:200] for e in run_errors[:5]]})

    tests = []
    for suite in data.get("suites", []):
        walk_tests(suite, tests)

    stats = data.get("stats") or {}
    if {"expected", "unexpected", "flaky"} <= set(stats.keys()):
        counts = {
            "passed": stats.get("expected", 0),
            "failed": stats.get("unexpected", 0),
            "flaky": stats.get("flaky", 0),
            "skipped": stats.get("skipped", 0),
            "interrupted": sum(1 for _, _, s in tests if s == "interrupted"),
        }
    else:
        if not tests:
            rojo("results.json sin tests (¿ejecución vacía?)")
        counts = {
            "passed": sum(1 for _, _, s in tests if s == "expected"),
            "failed": sum(1 for _, _, s in tests if s == "unexpected"),
            "flaky": sum(1 for _, _, s in tests if s == "flaky"),
            "skipped": sum(1 for _, _, s in tests if s == "skipped"),
            "interrupted": sum(1 for _, _, s in tests if s == "interrupted"),
        }

    flaky_items = [(t, fid) for t, fid, s in tests if s == "flaky"]
    flaky_titles = [t for t, _ in flaky_items]

    # Justificación: por id "fichero::título" o por título — pero si el título está
    # repetido entre los flaky, exige el id con fichero (evita justificar dos de golpe).
    dup_titles = {t for t in flaky_titles if flaky_titles.count(t) > 1}
    def justified(title, fid):
        if str(justif.get(fid, "")).strip():
            return True
        return title not in dup_titles and bool(str(justif.get(title, "")).strip())

    sin_justificar = [fid for t, fid in flaky_items if not justified(t, fid)]

    # Flaky que stats declara pero no se pudo localizar en suites → imposible
    # justificarlos: cuentan como sin justificar (nunca un falso verde).
    ilocalizables = counts["flaky"] - len(flaky_items)
    if ilocalizables > 0:
        sin_justificar += [f"(flaky sin título localizable ×{ilocalizables})"]

    ejecutados = counts["passed"] + counts["failed"] + counts["flaky"]
    verde = (counts["failed"] == 0 and len(sin_justificar) == 0
             and counts.get("interrupted", 0) == 0 and ejecutados > 0)
    resumen = {
        "verdict": "VERDE" if verde else "NO-VERDE",
        "counts": counts,
        "flaky_sin_justificar": sin_justificar,
        "flaky_justificados": {fid: (justif.get(fid) or justif.get(t))
                               for t, fid in flaky_items if justified(t, fid)},
        "threshold": "verde ⟺ 0 failed, 0 flaky sin justificar, 0 interrumpidos y ≥1 test ejecutado",
    }
    print(json.dumps(resumen, ensure_ascii=False, indent=2))
    sys.exit(0 if verde else 1)


if __name__ == "__main__":
    main()
