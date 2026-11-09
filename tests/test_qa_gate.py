#!/usr/bin/env python3
"""Tests de qa-gate.py (veredicto determinista). Ejecuta: python tests/test_qa_gate.py"""
import codecs
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "agent-kits", "qa", "qa-gate.py")


def results(specs):
    """specs: lista de (titulo, [status_de_cada_intento], expectedStatus)."""
    return {
        "suites": [{
            "title": "suite",
            "specs": [{
                "title": t,
                "tests": [{
                    "expectedStatus": exp,
                    "results": [{"status": s} for s in statuses],
                }],
            } for t, statuses, exp in specs],
        }],
    }


def run(res_obj, justify=None, no_file=False):
    with tempfile.TemporaryDirectory() as tmp:
        rp = os.path.join(tmp, "results.json")
        if not no_file:
            if isinstance(res_obj, str):
                open(rp, "w").write(res_obj)          # contenido crudo (malformado)
            else:
                json.dump(res_obj, open(rp, "w"))
        cmd = [sys.executable, SCRIPT, rp]
        if justify is not None:
            jp = os.path.join(tmp, "justify.json")
            json.dump(justify, open(jp, "w"))
            cmd += ["--justify", jp]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        return r.returncode, r.stdout


def main():
    # 1) todo verde → exit 0
    code, out = run(results([("login ok", ["passed"], "passed")]))
    assert code == 0 and '"VERDE"' in out, out

    # 2) un failed → exit 1
    code, out = run(results([("login ok", ["passed"], "passed"),
                             ("form roto", ["failed"], "passed")]))
    assert code == 1 and '"NO-VERDE"' in out, out

    # 3) flaky SIN justificar → exit 1
    code, out = run(results([("inestable", ["failed", "passed"], "passed")]))
    assert code == 1 and "inestable" in out, out

    # 4) flaky JUSTIFICADO (texto real) → exit 0
    code, out = run(results([("inestable", ["failed", "passed"], "passed")]),
                    justify={"inestable": "animación de carga; timing conocido, ticket QA-12"})
    assert code == 0, out

    # 5) justificación vacía NO cuenta → exit 1
    code, out = run(results([("inestable", ["failed", "passed"], "passed")]),
                    justify={"inestable": "   "})
    assert code == 1, out

    # 6) results.json ausente → exit 1 (la ausencia de evidencia es rojo)
    code, out = run(None, no_file=True)
    assert code == 1 and "no existe" in out, out

    # 7) malformado → exit 1
    code, out = run("{esto no es json")
    assert code == 1 and "malformado" in out, out

    # 8) esquema con stats (formato del reporter real) → cuenta desde stats
    code, out = run({"stats": {"expected": 3, "unexpected": 0, "flaky": 0, "skipped": 1},
                     "suites": []})
    assert code == 0 and '"passed": 3' in out, out

    # --- regresiones de la revisión adversarial de dos lentes (2026-08-10) ---

    # 9) stats declara flaky pero suites no permiten localizarlos → NO verde
    code, out = run({"stats": {"expected": 5, "unexpected": 0, "flaky": 2, "skipped": 0},
                     "suites": []})
    assert code == 1 and "sin título localizable" in out, out

    # 10) errores top-level del runner (forbidOnly, webserver caído) → NO verde
    code, out = run({"stats": {"expected": 0, "unexpected": 0, "flaky": 0, "skipped": 0},
                     "suites": [], "errors": [{"message": "focused item found"}]})
    assert code == 1 and "errores de ejecución" in out, out

    # 11) ejecución interrumpida (o test que nunca corrió) → NO verde
    code, out = run(results([("ok", ["passed"], "passed"),
                             ("cortado", ["interrupted"], "passed")]))
    assert code == 1 and '"interrupted": 1' in out, out

    # 12) 0 tests ejecutados (todo skipped) → NO verde
    code, out = run(results([("saltado", ["skipped"], "passed")]))
    assert code == 1, out

    # 13) dos flaky con el MISMO título: una justificación por título no vale para ambos
    dup = {"suites": [{"title": "s", "specs": [
        {"title": "guarda cambios", "file": "a.spec.mjs",
         "tests": [{"expectedStatus": "passed", "results": [{"status": "failed"}, {"status": "passed"}]}]},
        {"title": "guarda cambios", "file": "b.spec.mjs",
         "tests": [{"expectedStatus": "passed", "results": [{"status": "failed"}, {"status": "passed"}]}]},
    ]}]}
    code, out = run(dup, justify={"guarda cambios": "timing conocido"})
    assert code == 1, out
    #     …pero justificados por fichero::título sí
    code, out = run(dup, justify={"a.spec.mjs::guarda cambios": "timing conocido QA-1",
                                  "b.spec.mjs::guarda cambios": "timing conocido QA-2"})
    assert code == 0, out

    print("test_qa_gate: 13/13 OK")


# --- Auditoría 2026-11-09 (H-3, C4): sin falso verde y sin traceback ---

def _run_bytes(raw):
    with tempfile.TemporaryDirectory() as tmp:
        rp = os.path.join(tmp, "results.json")
        with open(rp, "wb") as f:
            f.write(raw)
        r = subprocess.run([sys.executable, SCRIPT, rp], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        return r.returncode, r.stdout, r.stderr


def test_casos_historicos():
    main()


def test_saltado_sin_stats_no_cuenta_como_pasado():
    code, out = run(results([("pendiente", ["skipped"], "skipped")]))
    data = json.loads(out)
    assert data["counts"]["passed"] == 0 and data["counts"]["skipped"] == 1, data
    assert code == 1 and data["verdict"] == "NO-VERDE", data


def test_saltado_junto_a_pasado_sigue_verde_y_cuenta_bien():
    code, out = run(results([("ok", ["passed"], "passed"),
                             ("pendiente", ["skipped"], "skipped")]))
    data = json.loads(out)
    assert data["counts"]["passed"] == 1 and data["counts"]["skipped"] == 1, data
    assert code == 0, data


def test_results_con_bom_se_lee():
    raw = codecs.BOM_UTF8 + json.dumps(results([("ok", ["passed"], "passed")])).encode()
    code, out, err = _run_bytes(raw)
    assert code == 0 and json.loads(out)["verdict"] == "VERDE", (out, err)


def test_raiz_lista_es_rojo_con_motivo():
    code, out, err = _run_bytes(b"[]")
    assert code == 1 and "Traceback" not in err, err
    data = json.loads(out)
    assert data["verdict"] == "NO-VERDE" and "objeto" in data["reason"], data


def test_estructura_inesperada_es_rojo_sin_traceback():
    for raw in (b'{"suites": {"no": "lista"}}', b'{"suites": ["texto"]}',
                b'{"errors": ["texto plano"]}', b'{"stats": [], "suites": []}'):
        code, out, err = _run_bytes(raw)
        assert code == 1 and "Traceback" not in err, (raw, err)
        assert json.loads(out)["verdict"] == "NO-VERDE", (raw, out)


if __name__ == "__main__":
    main()


def test_fallo_seguido_de_saltado_no_desaparece():
    """Revisión intento 1 (gap 2): `[failed, skipped]` (test.skip(testInfo.retry > 0)) no es saltado."""
    for exp in ("skipped", "passed"):
        code, out = run(results([("reintento saltado", ["failed", "skipped"], exp)]))
        data = json.loads(out)
        assert code == 1 and data["verdict"] == "NO-VERDE", (exp, data)
        assert data["counts"]["skipped"] == 0, (exp, data)
