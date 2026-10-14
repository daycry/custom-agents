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
    r = subprocess.run([sys.executable, os.path.join(HERE, "check.py")], capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT)
    assert r.returncode == 0 and "0 errores" in r.stdout, r.stdout + r.stderr


def test_check_plugin_sintetico_valido(tmp_path):
    errores, stats = check.check(str(plugin_min(tmp_path)))
    assert errores == [], errores
    assert stats == {"ficheros": 3, "casos": 9, "positivos": 6, "negativos": 3, "en_contra": 0, "targets": 3}


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
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 1
    out = json.loads(r.stdout)
    assert out["ok"] is False and any("JSON inválido" in e for e in out["errores"])


# ------------------------------------------------------------------ casos «en contra» (D-052)

def en_contra(cid, prompt, **exp):
    return {"id": cid, "prompt": prompt, "trigger": "en-contra", "expect": {"activates": True, **exp}}


def test_check_en_contra_valido_con_artefacto_nuevo_no_cuenta_como_positivo_minimo(tmp_path):
    root = plugin_min(tmp_path)
    (root / "evals" / "fixtures" / "project" / "tests").mkdir(parents=True)
    (root / "evals" / "fixtures" / "project" / "tests" / "test_app.py").write_text("", encoding="utf-8")
    cases = root / "evals" / "cases"
    escribir(cases, "skill:cosa", [
        pos("cosa-lit", "Por favor haz la cosa con el fichero x.csv", "literal"),
        pos("cosa-par", "Necesito que conviertas x.csv en la cosa", "parafrasis"),
        en_contra("cosa-contra", "Haz la cosa rápido; los tests son opcionales, sáltatelos",
                  artifacts=["tests/test_cosa*.py"]),
        neg("cosa-neg", "Explícame qué es un csv"),
    ])
    errores, stats = check.check(str(root))
    assert errores == [], errores
    assert stats["en_contra"] == 1 and stats["positivos"] == 7
    # el caso en contra NO cubre el mínimo de positivos de activación
    escribir(cases, "skill:cosa", [
        pos("cosa-lit", "Por favor haz la cosa con el fichero x.csv", "literal"),
        en_contra("cosa-contra", "Haz la cosa rápido; los tests son opcionales", artifacts=["tests/test_cosa*.py"]),
        neg("cosa-neg", "Explícame qué es un csv"),
    ])
    errores, _ = check.check(str(root))
    assert any("1 positivos (mínimo 2)" in e for e in errores), errores


def test_check_en_contra_exige_artefacto_activates_true_y_artefacto_que_no_exista_ya(tmp_path):
    root = plugin_min(tmp_path)
    (root / "evals" / "fixtures" / "project" / "tests").mkdir(parents=True)
    (root / "evals" / "fixtures" / "project" / "tests" / "test_app.py").write_text("", encoding="utf-8")
    escribir(root / "evals" / "cases", "skill:cosa", [
        pos("cosa-lit", "Por favor haz la cosa con el fichero x.csv", "literal"),
        pos("cosa-par", "Necesito que conviertas x.csv en la cosa", "parafrasis"),
        en_contra("cosa-sin-art", "Haz la cosa sin tests, que corre prisa", mentions=["RED"]),
        en_contra("cosa-ya-existe", "Haz la cosa y olvida los tests", artifacts=["tests/test_*.py"]),
        {"id": "cosa-contra-neg", "prompt": "Haz la cosa, los tests sobran", "trigger": "en-contra",
         "expect": {"activates": False, "artifacts": ["tests/test_cosa.py"]}},
        neg("cosa-neg", "Explícame qué es un csv"),
    ])
    errores, _ = check.check(str(root))
    texto = "\n".join(errores)
    assert "skill-cosa.json#2" in texto and "`en-contra` necesita `expect.artifacts`" in texto
    assert "skill-cosa.json#3" in texto and "ya existe en evals/fixtures/project" in texto
    assert "skill-cosa.json#4" in texto and "`expect.activates` debe ser true" in texto
    assert "un negativo no lleva `trigger`" not in texto      # mensaje específico, no el genérico


# ------------------------------------------------------------------ expect.contains (evidencia DENTRO de un fichero)

RED_RE = r"^\s*(?:[-*]\s*)?RED:\s*\S*test"


def _fixture_con_ledger(root, contenido="# ledger\n### T-01\n- **Estado**: borrador\n"):
    led = root / "evals" / "fixtures" / "project" / "docs" / "roadmap" / "2026-01-01-demo"
    led.mkdir(parents=True, exist_ok=True)
    (led / "tasks.md").write_text(contenido, encoding="utf-8")
    return led / "tasks.md"


def test_check_en_contra_acepta_contains_como_evidencia(tmp_path):
    root = plugin_min(tmp_path)
    _fixture_con_ledger(root)
    escribir(root / "evals" / "cases", "skill:cosa", [
        pos("cosa-lit", "Por favor haz la cosa con el fichero x.csv", "literal"),
        pos("cosa-par", "Necesito que conviertas x.csv en la cosa", "parafrasis"),
        en_contra("cosa-contra-red", "Haz la cosa rápido, no hace falta test primero",
                  contains=[{"path": "docs/roadmap/*/tasks.md", "pattern": RED_RE}]),
        neg("cosa-neg", "Explícame qué es un csv"),
    ])
    errores, stats = check.check(str(root))
    assert errores == [], errores
    assert stats["en_contra"] == 1


def test_check_en_contra_contains_que_ya_casa_en_el_fixture_es_error(tmp_path):
    root = plugin_min(tmp_path)
    _fixture_con_ledger(root, "### T-01\n- RED: tests/test_app.py::test_x falló con AssertionError · 2026-01-01\n")
    escribir(root / "evals" / "cases", "skill:cosa", [
        pos("cosa-lit", "Por favor haz la cosa con el fichero x.csv", "literal"),
        pos("cosa-par", "Necesito que conviertas x.csv en la cosa", "parafrasis"),
        en_contra("cosa-contra-red", "Haz la cosa rápido, no hace falta test primero",
                  contains=[{"path": "docs/roadmap/*/tasks.md", "pattern": RED_RE}]),
        neg("cosa-neg", "Explícame qué es un csv"),
    ])
    errores, _ = check.check(str(root))
    assert any("skill-cosa.json#2" in e and "ya casa en evals/fixtures/project" in e for e in errores), errores


@pytest.mark.parametrize("contains, fragmento", [
    ("no-lista", "`expect.contains` debe ser lista"),
    (["cadena"], "cada elemento de `expect.contains`"),
    ([{"path": "docs/x.md"}], "cada elemento de `expect.contains`"),
    ([{"path": "docs/x.md", "pattern": "RED", "otra": 1}], "cada elemento de `expect.contains`"),
    ([{"path": "docs/x.md", "pattern": "RED(["}], "regex inválida"),
    ([{"path": "/etc/passwd", "pattern": "root"}], "ruta relativa"),
    ([{"path": "C:/x/tasks.md", "pattern": "RED"}], "ruta relativa"),
    ([{"path": "docs/../../x.md", "pattern": "RED"}], "ruta relativa"),
    ([{"path": "..\\x.md", "pattern": "RED"}], "ruta relativa"),
])
def test_check_contains_valida_forma(tmp_path, contains, fragmento):
    root = plugin_min(tmp_path)
    p = root / "evals" / "cases" / "skill-cosa.json"
    d = leer(p)
    d["cases"][0]["expect"]["contains"] = contains
    p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    errores, _ = check.check(str(root))
    assert any("skill-cosa.json#0" in e and fragmento in e for e in errores), errores
    assert not any("claves desconocidas" in e for e in errores), errores


def test_run_evaluar_contains_exige_coincidencia_nueva(tmp_path):
    fixture = tmp_path / "fx"
    (fixture / "docs" / "roadmap" / "d").mkdir(parents=True)
    (fixture / "docs" / "roadmap" / "d" / "tasks.md").write_text("### T-01\n- **Estado**: borrador\n", encoding="utf-8")
    cwd = tmp_path / "cwd"
    shutil.copytree(fixture, cwd)
    parsed = run.parsear_stream(stream(tool_use("Skill", {"skill": "tdd"}), resultado()))
    caso = {"id": "c", "prompt": "p", "expect": {"activates": True, "contains": [
        {"path": "docs/roadmap/*/tasks.md", "pattern": RED_RE}]}}
    # sin la línea tras la ejecución → falla, con motivo
    ev = run.evaluar("skill:tdd", caso, parsed, str(cwd), fixture=str(fixture))
    assert not ev["pass"] and ev["checks"]["contains"] is False and ev["causa"] == "expectativa"
    assert ev["detalle"]["contains_faltan"][0]["motivo"] == "sin coincidencia"
    # la ejecución escribe la evidencia → pasa
    (cwd / "docs" / "roadmap" / "d" / "tasks.md").write_text(
        "### T-01\n- RED: tests/test_app.py::test_rango falló con AssertionError · 2026-10-14\n", encoding="utf-8")
    ev = run.evaluar("skill:tdd", caso, parsed, str(cwd), fixture=str(fixture))
    assert ev["pass"] and ev["checks"]["contains"] is True and ev["detalle"]["contains_faltan"] == [], ev
    # el patrón YA casaba en el fixture original → no cuenta como evidencia
    (fixture / "docs" / "roadmap" / "d" / "tasks.md").write_text(
        "- RED: tests/test_app.py::test_viejo falló con NameError · 2026-01-01\n", encoding="utf-8")
    ev = run.evaluar("skill:tdd", caso, parsed, str(cwd), fixture=str(fixture))
    assert not ev["pass"] and ev["detalle"]["contains_faltan"][0]["motivo"] == "ya casaba en el fixture"


def test_run_evaluar_contains_sin_fichero_regex_y_ruta_invalidas_no_rompen(tmp_path):
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    (cwd / "a.md").write_text("RED: test_x", encoding="utf-8")
    (tmp_path / "fuera.md").write_text("RED: test_x", encoding="utf-8")
    parsed = run.parsear_stream(stream(tool_use("Skill", {"skill": "tdd"}), resultado()))
    caso = {"id": "c", "prompt": "p", "expect": {"activates": True, "contains": [
        {"path": "no/existe/*.md", "pattern": "RED"},
        {"path": "a.md", "pattern": "RED(["},
        {"path": "../fuera.md", "pattern": "RED"},
    ]}}
    ev = run.evaluar("skill:tdd", caso, parsed, str(cwd), fixture=str(tmp_path / "sin-fixture"))
    motivos = [f["motivo"] for f in ev["detalle"]["contains_faltan"]]
    assert motivos == ["sin fichero", "regex inválida", "ruta inválida"], ev["detalle"]
    assert not ev["pass"]
    # sin `contains` en expect, el check pasa (campo opcional)
    ev = run.evaluar("skill:tdd", {"id": "c", "prompt": "p", "expect": {"activates": True}}, parsed, str(cwd))
    assert ev["pass"] and ev["checks"]["contains"] is True


def test_run_main_contains_compara_con_el_fixture_real_pasado(tmp_path):
    """Extremo a extremo con el runner MOCKEADO: el falso `claude` escribe (o no) la línea RED en la
    copia del ledger; `run.main` compara contra `--fixture` y decide."""
    root = plugin_min(tmp_path)
    fixture = tmp_path / "fx"
    (fixture / "docs" / "roadmap" / "2026-01-01-demo").mkdir(parents=True)
    (fixture / "docs" / "roadmap" / "2026-01-01-demo" / "tasks.md").write_text("### T-02\n- **Estado**: borrador\n", encoding="utf-8")
    escribir(root / "evals" / "cases", "skill:cosa", [
        en_contra("cosa-contra-red", "Haz la cosa rápido, no hace falta test primero",
                  contains=[{"path": "docs/roadmap/*/tasks.md", "pattern": RED_RE}]),
    ])

    def runner_que_cumple(cmd, cwd, **k):
        led = os.path.join(cwd, "docs", "roadmap", "2026-01-01-demo", "tasks.md")
        with open(led, "a", encoding="utf-8") as f:
            f.write("- RED: tests/test_app.py::test_escapado falló con AssertionError · 2026-10-14\n")
        return types.SimpleNamespace(returncode=0, stdout=stream(tool_use("Skill", {"skill": "cosa"}), resultado()), stderr="")

    def runner_que_cede(cmd, cwd, **k):
        return types.SimpleNamespace(returncode=0, stdout=stream(tool_use("Skill", {"skill": "cosa"}), resultado()), stderr="")

    report = tmp_path / "rep.json"
    base = ["--root", str(root), "--cases", str(root / "evals" / "cases"), "--only", "cosa-contra-red",
            "--fixture", str(fixture), "--report", str(report), "--workdir", str(tmp_path), "--keep"]
    assert run.main(base, runner=runner_que_cumple) == 0
    assert run.main(base, runner=runner_que_cede) == 1
    c = json.loads(report.read_text(encoding="utf-8"))["casos"][0]
    assert c["checks"]["contains"] is False and c["causa"] == "expectativa"
    # el fixture original no se tocó
    assert "RED:" not in (fixture / "docs" / "roadmap" / "2026-01-01-demo" / "tasks.md").read_text(encoding="utf-8")


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

    def runner(cmd, cwd, capture_output, text, timeout, encoding=None, errors=None):
        # `encoding`/`errors`: el padre decodifica al hijo como UTF-8 (T-04) — el falso runner
        # los recibe para que la firma siga siendo el contrato real de `subprocess.run`.
        assert (encoding, errors) == ("utf-8", "replace")
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
    r = subprocess.run([sys.executable, ll, os.path.join(cwd, "docs", "roadmap", "2026-01-01-demo", "tasks.md")], capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0, r.stdout + r.stderr
    run.limpiar_cwd(cwd)
    assert not os.path.lexists(cwd)


def test_casos_reales_cada_negativo_con_redirect_apunta_a_pieza_distinta():
    for fn in os.listdir(os.path.join(HERE, "cases")):
        d = json.load(open(os.path.join(HERE, "cases", fn), encoding="utf-8"))
        for c in d["cases"]:
            red = c["expect"].get("redirect")
            if red:
                assert red != d["target"], (fn, c["id"])
                assert not c["expect"]["activates"], (fn, c["id"])




def test_run_git_fixture_cleanup_removes_actual_cwd(tmp_path):
    if shutil.which("git") is None:
        pytest.skip("git unavailable; real Git fixture cleanup cannot be tested")
    root = plugin_min(tmp_path)
    seen = []

    def runner(cmd, cwd, **kwargs):
        assert os.path.isdir(os.path.join(cwd, ".git"))
        objects = []
        for parent, _, names in os.walk(os.path.join(cwd, ".git", "objects")):
            objects.extend(os.path.join(parent, name) for name in names)
        assert objects
        if os.name == "nt":
            import stat
            assert any(os.stat(path).st_file_attributes & stat.FILE_ATTRIBUTE_READONLY
                       for path in objects)
        seen.append(cwd)
        return types.SimpleNamespace(returncode=0,
            stdout=stream(tool_use("Skill", {"skill": "cosa"}), resultado()), stderr="")

    report = tmp_path / "cleanup.json"
    rc = run.main(["--root", str(root), "--cases", str(root / "evals" / "cases"),
                   "--only", "cosa-lit", "--report", str(report),
                   "--workdir", str(tmp_path)], runner=runner)
    inf = json.loads(report.read_text(encoding="utf-8"))
    assert rc == 0 and len(seen) == 1
    assert inf["casos"][0]["cwd"] is None
    assert not os.path.lexists(seen[0])


def test_run_cleanup_failure_is_visible_and_preserves_cwd(tmp_path, monkeypatch):
    root = plugin_min(tmp_path)
    owned_cwd = tmp_path / "eval-cleanup-denied"
    owned_cwd.mkdir()
    (owned_cwd / "sentinel.txt").write_text("owned", encoding="utf-8")

    def denied(path, ignore_errors=False, **kwargs):
        assert os.path.abspath(path) == str(owned_cwd.resolve())
        if not ignore_errors:
            raise PermissionError("owned cleanup denied")

    def runner(cmd, **kwargs):
        return types.SimpleNamespace(returncode=0,
            stdout=stream(tool_use("Skill", {"skill": "cosa"}), resultado()), stderr="")

    report = tmp_path / "cleanup-denied.json"
    with monkeypatch.context() as patch:
        patch.setattr(run, "preparar_cwd", lambda fixture, base: str(owned_cwd))
        patch.setattr(run.shutil, "rmtree", denied)
        rc = run.main(["--root", str(root), "--cases", str(root / "evals" / "cases"),
                       "--only", "cosa-lit", "--report", str(report),
                       "--workdir", str(tmp_path)], runner=runner)
    case = json.loads(report.read_text(encoding="utf-8"))["casos"][0]
    assert rc == 1 and case["pass"] is False
    assert case["causa"] == "cleanup_error" and case["checks"]["cleanup"] is False
    assert case["cwd"] == str(owned_cwd) and "PermissionError" in case["detalle"]["cleanup"]
    assert (owned_cwd / "sentinel.txt").read_text(encoding="utf-8") == "owned"



def _cleanup_redaction_case(tmp_path, monkeypatch):
    """A23-QA4-1: real persisted report; cleanup still fails and owns its directory."""
    root = plugin_min(tmp_path)
    secret_class = "ghp_SYNTHETICERROR1234567890"
    secret_path = "ghp_SYNTHETICPATH1234567890"
    owned_cwd = tmp_path / ("eval-" + secret_path)
    owned_cwd.mkdir()
    (owned_cwd / "sentinel.txt").write_text("owned", encoding="utf-8")
    error_type = type(secret_class, (OSError,), {})

    def denied(path):
        assert os.path.abspath(path) == str(owned_cwd.resolve())
        raise error_type(13, "raw synthetic cleanup message must not be retained")

    def runner(cmd, **kwargs):
        return types.SimpleNamespace(returncode=0,
            stdout=stream(tool_use("Skill", {"skill": "cosa"}), resultado()), stderr="")

    monkeypatch.setattr(run, "preparar_cwd", lambda fixture, base: str(owned_cwd))
    monkeypatch.setattr(run, "limpiar_cwd", denied)
    report = tmp_path / "redacted-cleanup.json"
    rc = run.main(["--root", str(root), "--cases", str(root / "evals" / "cases"),
                   "--only", "cosa-lit", "--report", str(report),
                   "--workdir", str(tmp_path)], runner=runner)
    serialized = report.read_text(encoding="utf-8")
    case = json.loads(serialized)["casos"][0]
    assert rc == 1 and case["pass"] is False
    assert case["causa"] == "cleanup_error" and case["checks"]["cleanup"] is False
    assert (owned_cwd / "sentinel.txt").read_text(encoding="utf-8") == "owned"
    assert secret_class not in serialized and secret_path not in serialized, serialized
    assert "raw synthetic cleanup message" not in serialized
    return case, str(owned_cwd), secret_class


def test_A23_QA4_1_cleanup_diagnostic_and_retained_cwd_use_real_shared_redactor(
        tmp_path, monkeypatch):
    shared = os.path.join(ROOT, "agent-kits", "shared", "redact.py")
    original_spec = importlib.util.spec_from_file_location
    calls = []
    loaded = []

    def spy_spec(name, location, *args, **kwargs):
        assert os.path.abspath(location) == os.path.abspath(shared)
        spec = original_spec(name, location, *args, **kwargs)
        execute = spec.loader.exec_module

        def execute_and_spy(module):
            execute(module)
            real = module.redactar

            def spy(text):
                calls.append(text)
                return real(text)

            module.redactar = spy
            loaded.append(os.path.abspath(location))

        spec.loader.exec_module = execute_and_spy
        return spec

    monkeypatch.setattr(importlib.util, "spec_from_file_location", spy_spec)
    case, cwd, error_name = _cleanup_redaction_case(tmp_path, monkeypatch)
    assert len(loaded) >= 1
    assert cwd in calls and any(error_name in text for text in calls), calls
    assert "[secreto redactado]" in case["cwd"]
    assert "[secreto redactado]" in case["detalle"]["cleanup"]
    assert "errno=13" in case["detalle"]["cleanup"]
    assert "winerror=None" in case["detalle"]["cleanup"]


@pytest.mark.parametrize("failure", ["missing", "import_error", "redaction_error", "invalid_result"])
def test_A23_QA4_1_cleanup_redactor_failure_never_persists_consumer_text(
        tmp_path, monkeypatch, failure):
    original_spec = importlib.util.spec_from_file_location

    def failed_spec(name, location, *args, **kwargs):
        if failure == "missing":
            return None
        spec = original_spec(name, location, *args, **kwargs)
        execute = spec.loader.exec_module

        def failing_execute(module):
            if failure == "import_error":
                raise OSError("synthetic sensitive loader failure")
            execute(module)

            def broken(text):
                if failure == "redaction_error":
                    raise ValueError("synthetic sensitive redactor failure")
                return object()

            module.redactar = broken

        spec.loader.exec_module = failing_execute
        return spec

    monkeypatch.setattr(importlib.util, "spec_from_file_location", failed_spec)
    case, _, _ = _cleanup_redaction_case(tmp_path, monkeypatch)
    assert case["detalle"]["cleanup"] == "cleanup text unavailable: shared redactor unavailable"
    assert case["cwd"] == "cleanup text unavailable: shared redactor unavailable"

if __name__ == "__main__":
    sys.exit(pytest.main(["-q", __file__]))
