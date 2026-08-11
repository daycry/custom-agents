#!/usr/bin/env python3
"""Tests de worklog.py (tope diario + banco por issue). Ejecuta: python tests/test_worklog.py"""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "skills", "jira-sync", "scripts", "worklog.py")


def run(tmp, *extra, allow_fail=False):
    cmd = [sys.executable, SCRIPT, *extra,
           "--state", os.path.join(tmp, "jira-state.json"),
           "--rates", os.path.join(tmp, "rates.json"),
           "--jira", os.path.join(tmp, "jira.json")]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if not allow_fail:
        assert r.returncode == 0, f"exit {r.returncode}: {r.stderr}"
    return json.loads(r.stdout)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        json.dump({"horasJornada": 8, "ratioSupervision": 0.25},
                  open(os.path.join(tmp, "rates.json"), "w"))
        json.dump({"alCubrirJornada": "banco"}, open(os.path.join(tmp, "jira.json"), "w"))

        # 1) cabe entera: IA 4h + sup 1h = 5h
        o = run(tmp, "plan", "--task", "T-01", "--issue", "K-1",
                "--ia-real", "4", "--sup-real", "1", "--fecha", "2026-07-17", "--apply")
        assert o["imputarHoy"] == 5 and o["banco"] == 0, o

        # 2) no cabe: llevo 5h, tarea de 3h (IA 2.4 + sup derivada 0.6) → 3h; caben 3... ajusto a 4h
        o = run(tmp, "plan", "--task", "T-02", "--issue", "K-2",
                "--ia-real", "3.2", "--fecha", "2026-07-17", "--apply")   # sup=0.8 → 4h, restante 3
        assert o["imputarHoy"] == 3.0 and o["banco"] == 1.0 and not o["parar"], o

        # 3) día cubierto: todo al banco
        o = run(tmp, "plan", "--task", "T-03", "--issue", "K-3",
                "--ia-real", "2", "--sup-real", "0.5", "--fecha", "2026-07-17", "--apply")
        assert o["imputarHoy"] == 0 and o["banco"] == 2.5, o

        # 4) status: banco = 3.5
        s = run(tmp, "status")
        assert s["bancoPendiente"] == 3.5, s

        # 5) drain al día siguiente: caben las 3.5 (cada pago a SU issue)
        d = run(tmp, "drain", "--fecha", "2026-07-18", "--apply")
        pagos = {p["issue"]: p["horas"] for p in d["pagos"]}
        assert pagos == {"K-2": 1.0, "K-3": 2.5} and d["quedaEnBanco"] == 0, d

        # 6) política seguir: supera jornada sin bancar
        json.dump({"alCubrirJornada": "seguir"}, open(os.path.join(tmp, "jira.json"), "w"))
        o = run(tmp, "plan", "--task", "T-04", "--issue", "K-4",
                "--ia-real", "6", "--sup-real", "0", "--fecha", "2026-07-18")
        assert o["imputarHoy"] == 6 and o["banco"] == 0, o

        # 7) política preguntar: pide decisión, no aplica
        json.dump({"alCubrirJornada": "preguntar"}, open(os.path.join(tmp, "jira.json"), "w"))
        o = run(tmp, "plan", "--task", "T-05", "--issue", "K-5",
                "--ia-real", "6", "--sup-real", "0", "--fecha", "2026-07-18")
        assert o["requiereDecision"] and "opciones" in o, o

        # 8) fallback humano (sin IA)
        o = run(tmp, "plan", "--task", "T-06", "--issue", "K-6",
                "--human-real", "2", "--fecha", "2026-07-19")
        assert o["base"] == "humano" and o["horas"] == 2, o

    # --- C-07 jira-granularity: entrada [revisión] y desglose ---
    def state(tmp):
        return json.load(open(os.path.join(tmp, "jira-state.json")))

    with tempfile.TemporaryDirectory() as tmp:
        json.dump({"horasJornada": 8, "ratioSupervision": 0.25},
                  open(os.path.join(tmp, "rates.json"), "w"))
        json.dump({"alCubrirJornada": "banco"}, open(os.path.join(tmp, "jira.json"), "w"))

        # 9) implementación (kind por defecto) → worklogImpl, no worklogRevision
        o = run(tmp, "plan", "--task", "T-01", "--issue", "K-1",
                "--ia-real", "3", "--sup-real", "0", "--fecha", "2026-08-01", "--apply")
        assert o["kind"] == "implementacion" and o["imputarHoy"] == 3, o
        t = state(tmp)["tasks"]["T-01"]
        assert t["worklogImpl"] == 3 and "worklogRevision" not in t, t

        # 10) revisión sobre el MISMO issue → suma al total y al desglose de revisión
        o = run(tmp, "plan", "--task", "T-01", "--issue", "K-1", "--kind", "revision",
                "--ia-real", "0.5", "--sup-real", "0", "--fecha", "2026-08-01", "--apply")
        assert o["kind"] == "revision" and o["imputarHoy"] == 0.5, o
        t = state(tmp)["tasks"]["T-01"]
        assert t["worklog"] == 3.5 and t["worklogImpl"] == 3 and t["worklogRevision"] == 0.5, t

        # 11) segunda pasada de revisión (bucle) → acumula en worklogRevision
        o = run(tmp, "plan", "--task", "T-01", "--issue", "K-1", "--kind", "revision",
                "--ia-real", "0.4", "--sup-real", "0", "--fecha", "2026-08-01", "--apply")
        t = state(tmp)["tasks"]["T-01"]
        assert t["worklogRevision"] == 0.9 and t["worklog"] == 3.9, t
        # el tope diario ve el total (impl+revisión), no cada parte por separado
        assert state(tmp)["imputadoPorDia"]["2026-08-01"] == 3.9, state(tmp)

        # 12) kind inválido → error
        o = run(tmp, "plan", "--task", "T-02", "--issue", "K-2", "--kind", "otro",
                "--ia-real", "1", allow_fail=True)
        assert "error" in o, o

        # 13) traza por intento: una entrada de revisión POR PASADA del bucle
        run(tmp, "plan", "--task", "T-03", "--issue", "K-3", "--kind", "revision",
            "--attempt", "1", "--ia-real", "0.5", "--sup-real", "0",
            "--fecha", "2026-08-02", "--apply")
        run(tmp, "plan", "--task", "T-03", "--issue", "K-3", "--kind", "revision",
            "--attempt", "2", "--ia-real", "0.3", "--sup-real", "0",
            "--fecha", "2026-08-02", "--apply")
        t = state(tmp)["tasks"]["T-03"]
        assert t["worklogRevision"] == 0.8, t                      # el total suma los intentos
        assert [a["intento"] for a in t["reviewAttempts"]] == [1, 2], t
        assert [a["horas"] for a in t["reviewAttempts"]] == [0.5, 0.3], t
        assert all(a["fecha"] == "2026-08-02" for a in t["reviewAttempts"]), t
        # sin --attempt no se registra traza (retrocompatible)
        run(tmp, "plan", "--task", "T-03", "--issue", "K-3", "--kind", "revision",
            "--ia-real", "0.1", "--sup-real", "0", "--fecha", "2026-08-02", "--apply")
        t = state(tmp)["tasks"]["T-03"]
        assert len(t["reviewAttempts"]) == 2 and t["worklogRevision"] == 0.9, t

    print("OK: worklog.py — 13 casos en verde.")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"FALLO: {e}", file=sys.stderr)
        sys.exit(1)
