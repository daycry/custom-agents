#!/usr/bin/env python3
"""Tests de worklog.py (tope diario + banco por issue). Ejecuta: python tests/test_worklog.py"""
import codecs
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
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
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


# --- Auditoría 2026-11-09 (H-1, H-2): sin pérdida de datos ni entradas imposibles ---

def _prep(tmp, state_bytes=None):
    json.dump({"horasJornada": 8, "ratioSupervision": 0.25},
              open(os.path.join(tmp, "rates.json"), "w"))
    json.dump({"alCubrirJornada": "banco"}, open(os.path.join(tmp, "jira.json"), "w"))
    sp = os.path.join(tmp, "jira-state.json")
    if state_bytes is not None:
        with open(sp, "wb") as f:
            f.write(state_bytes)
    return sp


def _raw(tmp, *extra):
    cmd = [sys.executable, SCRIPT, *extra,
           "--state", os.path.join(tmp, "jira-state.json"),
           "--rates", os.path.join(tmp, "rates.json"),
           "--jira", os.path.join(tmp, "jira.json")]
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def test_casos_historicos():
    main()


def test_estado_con_bom_se_lee_y_conserva():
    estado = {"imputadoPorDia": {"2026-07-17": 5},
              "bancoHoras": [{"task": "T-09", "issueKey": "K-9", "horas": 2.0,
                              "origen": "2026-07-16"}],
              "tasks": {"T-09": {"issueKey": "K-9", "worklog": 5}}}
    with tempfile.TemporaryDirectory() as tmp:
        sp = _prep(tmp, codecs.BOM_UTF8 + json.dumps(estado).encode("utf-8"))
        s = run(tmp, "status")
        assert s["bancoPendiente"] == 2.0 and s["imputadoPorDia"] == {"2026-07-17": 5}, s
        run(tmp, "plan", "--task", "T-10", "--issue", "K-10", "--ia-real", "1",
            "--sup-real", "0", "--fecha", "2026-07-17", "--apply")
        st = json.load(open(sp, encoding="utf-8-sig"))
        assert st["imputadoPorDia"]["2026-07-17"] == 6, st
        assert st["bancoHoras"][0]["task"] == "T-09" and "T-09" in st["tasks"], st


def test_estado_corrupto_exit2_sin_escribir():
    corrupto = b'{"imputadoPorDia": {"2026-07-17": 5}, "bancoHoras": ['
    with tempfile.TemporaryDirectory() as tmp:
        sp = _prep(tmp, corrupto)
        for args in (("plan", "--task", "T-01", "--issue", "K-1", "--ia-real", "1",
                      "--fecha", "2026-07-17", "--apply"),
                     ("drain", "--fecha", "2026-07-18", "--apply"),
                     ("status",)):
            r = _raw(tmp, *args)
            assert r.returncode == 2, (args, r.returncode, r.stdout, r.stderr)
            assert "error" in json.loads(r.stdout), r.stdout
            assert open(sp, "rb").read() == corrupto, "el estado ilegible se sobrescribió"


def test_estado_raiz_no_objeto_exit2():
    with tempfile.TemporaryDirectory() as tmp:
        sp = _prep(tmp, b"[]")
        r = _raw(tmp, "plan", "--task", "T-01", "--issue", "K-1", "--ia-real", "1",
                 "--fecha", "2026-07-17", "--apply")
        assert r.returncode == 2, (r.returncode, r.stdout, r.stderr)
        assert open(sp, "rb").read() == b"[]"


def test_estado_ausente_sigue_siendo_vacio():
    with tempfile.TemporaryDirectory() as tmp:
        sp = _prep(tmp)
        o = run(tmp, "plan", "--task", "T-01", "--issue", "K-1", "--ia-real", "1",
                "--sup-real", "0", "--fecha", "2026-07-17", "--apply")
        assert o["aplicado"] and os.path.exists(sp), o


def test_escritura_atomica_con_os_replace(monkeypatch):
    import importlib.util
    spec = importlib.util.spec_from_file_location("worklog_mod", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    llamadas = []
    real = os.replace

    def espia(src, dst):
        llamadas.append((str(src), str(dst)))
        return real(src, dst)

    monkeypatch.setattr(mod.os, "replace", espia)
    with tempfile.TemporaryDirectory() as tmp:
        destino = os.path.join(tmp, "jira-state.json")
        mod.save_json(destino, {"a": 1})
        assert llamadas and llamadas[0][1] == destino, llamadas
        assert llamadas[0][0] != destino and os.path.dirname(llamadas[0][0]) == tmp
        assert json.load(open(destino, encoding="utf-8")) == {"a": 1}
        assert os.listdir(tmp) == ["jira-state.json"], os.listdir(tmp)


def test_fecha_futura_exit2():
    import datetime
    manana = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    with tempfile.TemporaryDirectory() as tmp:
        sp = _prep(tmp)
        for args in (("plan", "--task", "T-01", "--issue", "K-1", "--ia-real", "1",
                      "--fecha", manana, "--apply"),
                     ("drain", "--fecha", manana, "--apply")):
            r = _raw(tmp, *args)
            assert r.returncode == 2, (args, r.returncode, r.stdout, r.stderr)
            assert "error" in json.loads(r.stdout), r.stdout
        assert not os.path.exists(sp)
        r = _raw(tmp, "plan", "--task", "T-01", "--issue", "K-1", "--ia-real", "1",
                 "--fecha", "2026-13-40")
        assert r.returncode == 2, (r.returncode, r.stdout)


def test_horas_negativas_exit2():
    with tempfile.TemporaryDirectory() as tmp:
        sp = _prep(tmp)
        for flag in ("--ia-real", "--ia-est", "--sup-real", "--sup-est",
                     "--human-real", "--human-est"):
            r = _raw(tmp, "plan", "--task", "T-01", "--issue", "K-1", flag, "-1",
                     "--fecha", "2026-07-17", "--apply")
            assert r.returncode == 2, (flag, r.returncode, r.stdout, r.stderr)
            assert "error" in json.loads(r.stdout), r.stdout
        assert not os.path.exists(sp)


# --- Revisión de dos lentes, intento 1 (gap 8) ---

def test_fix1_horas_no_finitas_exit2():
    with tempfile.TemporaryDirectory() as tmp:
        sp = _prep(tmp)
        for valor in ("nan", "inf", "-inf", "Infinity"):
            r = _raw(tmp, "plan", "--task", "T-01", "--issue", "K-1", f"--ia-real={valor}",
                     "--fecha", "2026-07-17", "--apply")
            assert r.returncode == 2, (valor, r.returncode, r.stdout, r.stderr)
            assert "error" in json.loads(r.stdout), r.stdout
        assert not os.path.exists(sp)


def test_fix1_campos_de_tipo_equivocado_exit2_sin_traceback():
    casos = [{"imputadoPorDia": None}, {"imputadoPorDia": []}, {"bancoHoras": {}},
             {"bancoHoras": [{"task": "T-1", "issueKey": "K"}]}, {"bancoHoras": ["x"]},
             {"tasks": []}, {"imputadoPorDia": {"2026-07-18": "mucho"}}]
    for estado in casos:
        with tempfile.TemporaryDirectory() as tmp:
            raw = json.dumps(estado).encode("utf-8")
            sp = _prep(tmp, raw)
            for args in (("plan", "--task", "T-01", "--issue", "K-1", "--ia-real", "1",
                          "--fecha", "2026-07-18", "--apply"),
                         ("drain", "--fecha", "2026-07-18", "--apply"), ("status",)):
                r = _raw(tmp, *args)
                assert r.returncode == 2 and "Traceback" not in r.stderr, (estado, args, r.stderr)
                assert "error" in json.loads(r.stdout), r.stdout
                assert open(sp, "rb").read() == raw


def test_fix1_replace_con_permission_error_reintenta_y_sale_limpio(monkeypatch):
    import importlib.util
    spec = importlib.util.spec_from_file_location("worklog_mod_fix1", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    llamadas = []
    real = os.replace

    def bloqueado_dos_veces(src, dst):
        llamadas.append(dst)
        if len(llamadas) <= 2:
            raise PermissionError(13, "acceso denegado")
        return real(src, dst)

    monkeypatch.setattr(mod.os, "replace", bloqueado_dos_veces)
    monkeypatch.setattr(mod.time, "sleep", lambda _s: None)
    with tempfile.TemporaryDirectory() as tmp:
        destino = os.path.join(tmp, "jira-state.json")
        mod.save_json(destino, {"a": 1})
        assert len(llamadas) == 3 and json.load(open(destino)) == {"a": 1}

    def siempre_bloqueado(src, dst):
        raise PermissionError(13, "acceso denegado")

    monkeypatch.setattr(mod.os, "replace", siempre_bloqueado)
    with tempfile.TemporaryDirectory() as tmp:
        destino = os.path.join(tmp, "jira-state.json")
        try:
            mod.save_json(destino, {"a": 1})
        except mod.EntradaInvalida as e:
            assert "jira-state.json" in str(e)
        else:
            raise AssertionError("un replace bloqueado debe acabar en EntradaInvalida (exit 2)")
        assert os.listdir(tmp) == [], os.listdir(tmp)


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"FALLO: {e}", file=sys.stderr)
        sys.exit(1)
