#!/usr/bin/env python3
"""Tests de la suite de evals: `check.py` (estático) y `run.py` (runner, con el subprocess MOCKEADO —
aquí nunca se lanza `claude`). Ejecutar: python3 -m pytest -q evals  (la CI lo hace así).
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import types

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


check = _load("check")
run = _load("run")


# ------------------------------------------------------------------ fixtures ----

def plugin_min(tmp_path, descripcion_skill='Hace cosas. Úsala cuando el usuario diga "haz la cosa" o "cosifica esto".'):
    """Plugin sintético: 1 skill, 1 command, 1 agent + evals/cases coherentes. Devuelve su raíz."""
    root = tmp_path / "plug"
    (root / "skills" / "cosa").mkdir(parents=True)
    (root / "skills" / "cosa" / "SKILL.md").write_text(f"---\nname: cosa\ndescription: {descripcion_skill}\n---\n# cosa\n", encoding="utf-8")
    (root / "commands").mkdir()
    (root / "commands" / "ciclo.md").write_text("---\ndescription: Orquesta el ciclo entero de una cosa con puertas de control.\nargument-hint: <x>\n---\n# ciclo\n", encoding="utf-8")
    (root / "agents").mkdir()
    (root / "agents" / "obrero.md").write_text("---\nname: obrero\ndescription: Ejecuta el plan de la cosa fase a fase. Úsalo cuando el usuario diga \"ejecuta el plan\".\nmodel: sonnet\ntools: Read\n---\n# obrero\n", encoding="utf-8")
    cases = root / "evals" / "cases"
    cases.mkdir(parents=True)
    escribir(cases, "skill:cosa", [
        pos("cosa-lit", "Por favor haz la cosa con el fichero x.csv", "literal"),
        pos("cosa-par", "Necesito que conviertas x.csv en la cosa", "parafrasis"),
        neg("cosa-neg", "Explícame qué es un csv"),
    ])
    escribir(cases, "command:ciclo", [
        pos("ciclo-lit", "Quiero el ciclo entero de una cosa para el módulo pagos", "literal"),
        pos("ciclo-par", "Llévame de principio a fin la mejora pagos", "parafrasis"),
        neg("ciclo-neg", "Solo la spec de pagos", redirect="skill:cosa"),
    ])
    escribir(cases, "agent:obrero", [
        pos("obrero-lit", "Ejecuta el plan de docs/roadmap/x", "literal"),
        pos("obrero-par", "Escribe el código de cada tarea del plan x", "parafrasis"),
        neg("obrero-neg", "Presupuesta el plan x"),
    ])
    return root


def pos(cid, prompt, trigger, **exp):
    return {"id": cid, "prompt": prompt, "trigger": trigger, "expect": {"activates": True, **exp}}


def neg(cid, prompt, **exp):
    return {"id": cid, "prompt": prompt, "expect": {"activates": False, **exp}}


def escribir(cases_dir, target, casos):
    p = cases_dir / check.nombre_fichero(target)
    p.write_text(json.dumps({"target": target, "cases": casos}, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def leer(p):
    return json.loads(p.read_text(encoding="utf-8"))


# ------------------------------------------------------------------ check.py ----

def test_check_repo_real_exit_0_y_minimo_90_casos():
    errores, stats = check.check(ROOT)
    assert errores == [], errores
    assert stats["casos"] >= 90 and stats["ficheros"] == stats["targets"] >= 31, stats
    r = subprocess.run([sys.executable, os.path.join(HERE, "check.py")], capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0 and "0 errores" in r.stdout, r.stdout + r.stderr


def test_check_plugin_sintetico_valido(tmp_path):
    errores, stats = check.check(str(plugin_min(tmp_path)))
    assert errores == [], errores
    assert stats == {"ficheros": 3, "casos": 9, "positivos": 6, "negativos": 3, "targets": 3}


def test_check_cobertura_pieza_sin_fichero(tmp_path):
    root = plugin_min(tmp_path)
    (root / "skills" / "otra").mkdir()
    (root / "skills" / "otra" / "SKILL.md").write_text("---\nname: otra\ndescription: Otra.\n---\n", encoding="utf-8")
    errores, _ = check.check(str(root))
    assert any("cobertura" in e and "skill-otra.json" in e for e in errores), errores


def test_check_literal_debe_casar_con_la_description(tmp_path):
    root = plugin_min(tmp_path)
    p = root / "evals" / "cases" / "skill-cosa.json"
    d = leer(p)
    d["cases"][0]["prompt"] = "Hola, quiero algo totalmente distinto sin frase gatillo"
    p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    errores, _ = check.check(str(root))
    assert any("trigger: literal" in e for e in errores), errores
    assert any("ningún positivo `trigger: literal`" in e for e in errores), errores


def test_check_cambiar_la_description_rompe_el_caso_literal(tmp_path):
    root = plugin_min(tmp_path, descripcion_skill="Hace cosas. Úsala cuando el usuario diga \"otra frase nueva\".")
    errores, _ = check.check(str(root))
    assert any("cosa-lit" not in e and "skill-cosa.json#0" in e for e in errores), errores


def test_check_literal_acepta_frase_normalizada_sin_acentos_y_mayusculas(tmp_path):
    root = plugin_min(tmp_path, descripcion_skill='Convierte informes. Úsala cuando el usuario diga "genera el informe de evaluación".')
    p = root / "evals" / "cases" / "skill-cosa.json"
    d = leer(p)
    d["cases"][0]["prompt"] = "GENERA EL INFORME DE EVALUACION del trimestre, por favor"
    p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    assert check.check(str(root))[0] == []


def test_check_minimos_positivos_negativos_e_ids_unicos(tmp_path):
    root = plugin_min(tmp_path)
    escribir(root / "evals" / "cases", "skill:cosa", [
        pos("cosa-lit", "haz la cosa ya", "literal"),
        pos("cosa-lit", "haz la cosa ya", "literal"),     # id duplicado + prompt repetido
    ])
    errores, _ = check.check(str(root))
    assert any("id duplicado" in e for e in errores), errores
    assert any("prompt positivo repetido" in e for e in errores), errores
    assert any("0 negativos" in e for e in errores), errores


def test_check_esquema_nombre_fichero_trigger_en_negativo_y_redirect(tmp_path):
    root = plugin_min(tmp_path)
    cases = root / "evals" / "cases"
    (cases / "mal-nombre.json").write_text(json.dumps({"target": "skill:cosa", "cases": [
        pos("x1", "haz la cosa", "literal"), pos("x2", "haz la cosa dos", "parafrasis"),
        {"id": "x3", "prompt": "no", "trigger": "literal", "expect": {"activates": False, "redirect": "skill:inexistente", "rara": 1}},
        {"id": "x4", "prompt": "", "expect": {"activates": "sí"}},
    ]}), encoding="utf-8")
    errores, _ = check.check(str(root))
    texto = "\n".join(errores)
    assert "debe ser `skill-cosa.json`" in texto
    assert "un negativo no lleva `trigger`" in texto
    assert "`skill:inexistente` no es una pieza" in texto
    assert "claves desconocidas" in texto and "rara" in texto
    assert "`prompt` vacío" in texto and "`expect.activates` debe ser bool" in texto


def test_check_datos_corporativos(tmp_path):
    root = plugin_min(tmp_path)
    p = root / "evals" / "cases" / "skill-cosa.json"
    d = leer(p)
    d["cases"][1]["prompt"] = "Sube la cosa a acme.atlassian.net y avisa a ana@acme.com del ticket ACME-1234"
    p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    errores, _ = check.check(str(root))
    etiquetas = {e.split("(")[1].split(")")[0] for e in errores if "dato corporativo" in e}
    assert etiquetas == {"correo", "host atlassian", "clave jira"}, errores
    # lo permitido NO salta: PROJ-, T-XX, E2E-, localhost, example.com
    d["cases"][1]["prompt"] = "Vuelca T-01 y E2E-02 bajo PROJ-59 y prueba http://localhost:3000 con ana@example.com"
    p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    assert check.check(str(root))[0] == []


def test_check_json_invalido_y_cli_exit_1(tmp_path):
    root = plugin_min(tmp_path)
    (root / "evals" / "cases" / "skill-cosa.json").write_text("{ no es json", encoding="utf-8")
    r = subprocess.run([sys.executable, os.path.join(HERE, "check.py"), "--root", str(root), "--json"],
                       capture_output=True, text=True)
    assert r.returncode == 1
    out = json.loads(r.stdout)
    assert out["ok"] is False and any("JSON inválido" in e for e in out["errores"])


# ------------------------------------------------------------------ run.py ----

def stream(*eventos):
    return "\n".join(json.dumps(e, ensure_ascii=False) for e in eventos) + "\n"


def tool_use(name, inp, parent=None):
    return {"type": "assistant", "parent_tool_use_id": parent,
            "message": {"content": [{"type": "tool_use", "name": name, "input": inp}]}}


def texto(t):
    return {"type": "assistant", "parent_tool_use_id": None, "message": {"content": [{"type": "text", "text": t}]}}


def resultado(txt="hecho", cost=0.01, error=False):
    return {"type": "result", "subtype": "error" if error else "success", "is_error": error,
            "result": txt, "total_cost_usd": cost, "num_turns": 3}


def test_run_parsea_stream_y_detecta_skill_command_agent():
    parsed = run.parsear_stream(stream(
        {"type": "system", "subtype": "init"},
        tool_use("Skill", {"skill": "custom-agents:quick-implement", "args": "x"}),
        tool_use("Skill", {"skill": "/pm-cycle objetivo largo"}),
        tool_use("Agent", {"subagent_type": "custom-agents:implementer", "prompt": "…"}, parent="toolu_1"),
        tool_use("Read", {"file_path": "/plug/skills/discovery/SKILL.md"}),
        texto("voy a usar la vía rápida"),
        resultado("listo"),
    ) + "basura no json\n")
    assert len(parsed["tool_uses"]) == 4 and parsed["lineas_invalidas"] == 1
    tus = parsed["tool_uses"]
    assert run.detectar(tus, "skill:quick-implement")
    assert run.detectar(tus, "command:pm-cycle")
    assert run.detectar(tus, "agent:implementer")          # también en subagentes
    assert not run.detectar(tus, "skill:discovery")         # un Read NO cuenta por defecto…
    assert run.detectar(tus, "skill:discovery", loose=True)  # …salvo con --loose
    assert not run.detectar(tus, "agent:qa") and not run.detectar(tus, "skill:pm-cycl")
    assert run.detectar(tus, "skill:pm-cycle")  # skill: y command: comparten herramienta (commands = skills)


def test_run_evaluar_mentions_must_not_artifacts(tmp_path):
    cwd = tmp_path / "cwd"
    (cwd / "docs" / "roadmap" / "2026-02-02-x").mkdir(parents=True)
    (cwd / "docs" / "roadmap" / "2026-02-02-x" / "tasks.md").write_text("x", encoding="utf-8")
    parsed = run.parsear_stream(stream(tool_use("Skill", {"skill": "quick-implement"}), texto("Creo el ledger ligero"), resultado("Hecho en rama")))
    caso = {"id": "c", "prompt": "p", "expect": {"activates": True, "mentions": ["LEDGER"], "must_not": ["main"],
                                                  "artifacts": ["docs/roadmap/*/tasks.md"], "redirect": "command:dev-cycle"}}
    ev = run.evaluar("skill:quick-implement", caso, parsed, str(cwd))
    assert ev["pass"] and ev["activado"] and ev["redirect_observado"] is False, ev
    caso["expect"]["must_not"] = ["ledger"]
    caso["expect"]["artifacts"] = ["docs/roadmap/*/spec.md"]
    ev = run.evaluar("skill:quick-implement", caso, parsed, str(cwd))
    assert not ev["pass"] and ev["checks"]["must_not"] is False and ev["checks"]["artifacts"] is False
    assert ev["detalle"]["artifacts_faltan"] == ["docs/roadmap/*/spec.md"]


def test_run_negativo_pasa_si_no_se_activa_y_falla_si_se_activa():
    caso = {"id": "n", "prompt": "p", "expect": {"activates": False}}
    assert run.evaluar("skill:quick-implement", caso, run.parsear_stream(stream(texto("¿qué alcance?"), resultado())), ".")["pass"]
    assert not run.evaluar("skill:quick-implement", caso, run.parsear_stream(stream(tool_use("Skill", {"skill": "quick-implement"}), resultado())), ".")["pass"]


def test_run_dry_run_imprime_comandos_sin_ejecutar(capsys, tmp_path):
    root = plugin_min(tmp_path)
    llamadas = []

    def runner(*a, **k):  # no debe llamarse
        llamadas.append(a)
    rc = run.main(["--root", str(root), "--cases", str(root / "evals" / "cases"), "--dry-run", "--max-turns", "5", "--bare"], runner=runner)
    out = capsys.readouterr().out
    assert rc == 0 and llamadas == []
    assert "--output-format stream-json --verbose --plugin-dir" in out and "--max-turns 5" in out and "--bare" in out
    assert out.count("claude -p ") == 9 and "9 casos (no ejecutado nada)" in out
    # gap Minor #5: --allowedTools con el default; --allowed-tools "" → no se pasa; valor propio → tal cual
    assert f"--allowedTools '{run.ALLOWED_TOOLS_DEFAULT}'" in out, out
    run.main(["--root", str(root), "--cases", str(root / "evals" / "cases"), "--dry-run", "--allowed-tools", ""], runner=runner)
    assert "--allowedTools" not in capsys.readouterr().out
    run.main(["--root", str(root), "--cases", str(root / "evals" / "cases"), "--dry-run", "--allowed-tools", "Bash,WebFetch"], runner=runner)
    assert "--allowedTools Bash,WebFetch" in capsys.readouterr().out


def test_run_target_repetible(capsys, tmp_path):
    """[plan-and-diet T-03] `--target` se puede repetir: `--dry-run --target A --target B` imprime exactamente
    los casos de esos dos ficheros (ni más ni menos); un solo `--target` sigue funcionando igual."""
    root = plugin_min(tmp_path)
    cases = str(root / "evals" / "cases")
    todos = run.cargar_casos(cases)
    targets = sorted({t for t, _ in todos})
    assert len(targets) >= 3
    a, b = targets[0], targets[1]
    esperados = sum(1 for t, _ in todos if t in (a, b))
    solo_a = sum(1 for t, _ in todos if t == a)
    assert 0 < solo_a < esperados < len(todos)
    rc = run.main(["--root", str(root), "--cases", cases, "--dry-run", "--target", a, "--target", b], runner=None)
    out = capsys.readouterr().out
    assert rc == 0 and out.count("claude -p ") == esperados, out
    assert f"{esperados} casos (no ejecutado nada)" in out
    rc = run.main(["--root", str(root), "--cases", cases, "--dry-run", "--target", a], runner=None)
    assert rc == 0 and capsys.readouterr().out.count("claude -p ") == solo_a
    # cargar_casos acepta str o lista
    assert len(run.cargar_casos(cases, target=a)) == solo_a
    assert len(run.cargar_casos(cases, target=[a, b])) == esperados


def test_run_permiso_denegado_se_distingue_de_no_activo():
    """Gap Minor #5: la pieza se activa pero un tool_result de Bash viene denegado por permisos →
    `causa: permiso denegado` (no «no activó»); sin activación → `no activó`; todo bien → causa None."""
    denegado = {"type": "user", "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": "toolu_9", "is_error": True,
         "content": "Claude requested permissions to use Bash, but you haven't granted it yet."}]}}
    parsed = run.parsear_stream(stream(tool_use("Skill", {"skill": "quick-implement"}),
                                       tool_use("Bash", {"command": "python3 ledger-lint.py"}), denegado, resultado("x")))
    assert parsed["permisos_denegados"] and "haven't granted" in parsed["permisos_denegados"][0]
    caso = {"id": "c", "prompt": "p", "expect": {"activates": True, "artifacts": ["docs/roadmap/*/tasks.md"]}}
    ev = run.evaluar("skill:quick-implement", caso, parsed, "/nonexistent-cwd")
    assert not ev["pass"] and ev["causa"] == "permiso denegado" and ev["detalle"]["permisos_denegados"]
    ev2 = run.evaluar("skill:quick-implement", caso, run.parsear_stream(stream(texto("hola"), resultado())), "/nonexistent-cwd")
    assert ev2["causa"] == "no activó"
    ev3 = run.evaluar("skill:quick-implement", {"id": "c", "prompt": "p", "expect": {"activates": True}}, parsed, ".")
    assert ev3["pass"] and ev3["causa"] is None
    # un tool_result con error que NO habla de permisos no cuenta como permiso denegado
    otro = {"type": "user", "message": {"content": [{"type": "tool_result", "is_error": True, "content": [{"type": "text", "text": "Traceback: KeyError"}]}]}}
    assert run.parsear_stream(stream(otro, resultado()))["permisos_denegados"] == []


def test_run_exit_2_sin_claude(tmp_path, capsys):
    root = plugin_min(tmp_path)
    rc = run.main(["--root", str(root), "--cases", str(root / "evals" / "cases"), "--claude", "claude-que-no-existe-xyz"])
    assert rc == 2 and "no está en PATH" in capsys.readouterr().err


def test_run_con_subprocess_mockeado_informe_y_exit_codes(tmp_path):
    root = plugin_min(tmp_path)
    fixture = tmp_path / "fx"
    fixture.mkdir()
    (fixture / "README.md").write_text("fixture", encoding="utf-8")
    vistos = []

    def runner(cmd, cwd, capture_output, text, timeout):
        vistos.append((cmd, cwd))
        prompt = cmd[cmd.index("-p") + 1]
        assert cmd[0] == "claude" and "--plugin-dir" in cmd and os.path.isfile(os.path.join(cwd, "README.md"))
        if "haz la cosa" in prompt or "conviertas" in prompt:
            out = stream(tool_use("Skill", {"skill": "custom-agents:cosa"}), resultado("cosa hecha"))
        elif "ciclo entero" in prompt or "principio a fin" in prompt:
            out = stream(tool_use("Skill", {"skill": "ciclo"}), resultado())
        elif "Ejecuta el plan" in prompt or "cada tarea" in prompt:
            out = stream(tool_use("Agent", {"subagent_type": "custom-agents:obrero"}), resultado())
        else:
            out = stream(texto("respondo sin activar nada"), resultado())
        return types.SimpleNamespace(returncode=0, stdout=out, stderr="")

    report = tmp_path / "rep.json"
    rc = run.main(["--root", str(root), "--cases", str(root / "evals" / "cases"), "--fixture", str(fixture),
                   "--report", str(report), "--workdir", str(tmp_path)], runner=runner)
    assert rc == 0 and len(vistos) == 9
    inf = json.loads(report.read_text(encoding="utf-8"))
    assert inf["total"] == 9 and inf["pasan"] == 9 and inf["fallan"] == 0 and inf["coste_usd"] == 0.09
    assert {c["id"] for c in inf["casos"]} == {"cosa-lit", "cosa-par", "cosa-neg", "ciclo-lit", "ciclo-par", "ciclo-neg", "obrero-lit", "obrero-par", "obrero-neg"}
    # el cwd temporal se borra sin --keep
    assert all(c["cwd"] is None for c in inf["casos"]) and not any(d.startswith("eval-") for d in os.listdir(tmp_path))

    # un negativo que SÍ se activa → exit 1 y el informe lo señala
    def runner_malo(cmd, **k):
        return types.SimpleNamespace(returncode=0, stdout=stream(tool_use("Skill", {"skill": "cosa"}), resultado()), stderr="")
    rc = run.main(["--root", str(root), "--cases", str(root / "evals" / "cases"), "--fixture", str(fixture),
                   "--only", "cosa-neg", "--report", str(report), "--workdir", str(tmp_path)], runner=runner_malo)
    inf = json.loads(report.read_text(encoding="utf-8"))
    assert rc == 1 and inf["fallan"] == 1 and inf["casos"][0]["checks"]["activates"] is False


def test_run_timeout_y_exit_distinto_de_0_fallan_el_caso(tmp_path):
    root = plugin_min(tmp_path)

    def runner_timeout(cmd, **k):
        raise subprocess.TimeoutExpired(cmd, k.get("timeout", 1))
    report = tmp_path / "r1.json"
    rc = run.main(["--root", str(root), "--cases", str(root / "evals" / "cases"), "--only", "cosa-lit",
                   "--fixture", str(tmp_path / "nada"), "--report", str(report), "--workdir", str(tmp_path), "--timeout", "7"], runner=runner_timeout)
    inf = json.loads(report.read_text(encoding="utf-8"))
    assert rc == 1 and inf["casos"][0]["checks"] == {"timeout": False} and "7s" in inf["casos"][0]["stderr"]

    def runner_error(cmd, **k):
        return types.SimpleNamespace(returncode=1, stdout=stream(tool_use("Skill", {"skill": "cosa"}), resultado("auth", error=True)), stderr="Not logged in")
    rc = run.main(["--root", str(root), "--cases", str(root / "evals" / "cases"), "--only", "cosa-lit",
                   "--fixture", str(tmp_path / "nada"), "--report", str(report), "--workdir", str(tmp_path)], runner=runner_error)
    inf = json.loads(report.read_text(encoding="utf-8"))
    c = inf["casos"][0]
    assert rc == 1 and c["checks"]["exit_0"] is False and c["checks"]["sin_error"] is False and c["checks"]["activates"] is True


def test_run_fixture_real_es_ledger_valido_y_se_copia(tmp_path):
    assert os.path.isfile(os.path.join(run.FIXTURE, "docs", "roadmap", "2026-01-01-demo", "tasks.md"))
    cwd = run.preparar_cwd(run.FIXTURE, str(tmp_path))
    assert os.path.isfile(os.path.join(cwd, "src", "app.py")) and os.path.isfile(os.path.join(cwd, ".claude", "rates.json"))
    ll = os.path.join(ROOT, "agent-kits", "shared", "ledger-lint.py")
    r = subprocess.run([sys.executable, ll, os.path.join(cwd, "docs", "roadmap", "2026-01-01-demo", "tasks.md")], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    shutil.rmtree(cwd)


def test_casos_reales_cada_negativo_con_redirect_apunta_a_pieza_distinta():
    for fn in os.listdir(os.path.join(HERE, "cases")):
        d = json.load(open(os.path.join(HERE, "cases", fn), encoding="utf-8"))
        for c in d["cases"]:
            red = c["expect"].get("redirect")
            if red:
                assert red != d["target"], (fn, c["id"])
                assert not c["expect"]["activates"], (fn, c["id"])


if __name__ == "__main__":
    sys.exit(pytest.main(["-q", __file__]))
