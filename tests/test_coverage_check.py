#!/usr/bin/env python3
"""Tests de coverage-check.py (puerta criterios↔tests de qa), incl. criterios [GWT].

Ejecuta:  python3 tests/test_coverage_check.py   (sale 0 si todo pasa, 1 si algo falla)
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "agent-kits", "qa", "coverage-check.py")

TASKS_OK = """# Tareas
### T-01 — cosa de UI
- **Cubre (tests)**: E2E-01
### T-02 — cosa sin UI
- **Cubre (tests)**: —
"""
PLAN_OK = """# Test plan
## E2E-01 — flujo feliz
Pasos… (cubre CA-01)
"""
SPEC_GWT = """---
spec: x
---
## Criterios de aceptación
- [ ] criterio libre de proceso
- [ ] [GWT] CA-01 — Dado un usuario logueado, Cuando pulsa guardar, Entonces ve el toast
- [x] [GWT] CA-02 — Dado un carrito vacío, Cuando añade un ítem, Entonces el contador marca 1
- [ ] [GWT] Dado algo sin ID, Cuando pasa, Entonces avisa
"""
# `improvement-plan.md` CON el marcador (forma canónica) y sin él
PLAN_NA = "---\nplan: x\ntest-plan: n/a (sin UI)\n---\n# Plan\n"
PLAN_CON_UI = "---\nplan: x\n---\n# Plan\n"
# `.claude/dev.json` del escenario compuesto de R4a-19 (fuera de los f-strings: lleva llaves)
CONFIG_EXCLUIR = '{"alcance": {"excluir": ["src/components/**"]}}'


def run(tasks, plan, spec=None, improvement_plan=None):
    d = tempfile.mkdtemp()
    tp = os.path.join(d, "tasks.md")
    open(tp, "w", encoding="utf-8").write(tasks)
    if improvement_plan is not None:
        open(os.path.join(d, "improvement-plan.md"), "w", encoding="utf-8").write(improvement_plan)
    args = [sys.executable, SCRIPT, tp]
    pp = os.path.join(d, "test-plan.md")
    if plan is not None:
        open(pp, "w", encoding="utf-8").write(plan)
    args.append(pp)
    if spec is not None:
        sp = os.path.join(d, "spec.md")
        open(sp, "w", encoding="utf-8").write(spec)
        args.append(sp)
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    last = r.stdout.strip().splitlines()[-1]
    return r.returncode, json.loads(last), r.stdout


def eq(got, exp, msg):
    assert got == exp, f"{msg}: esperado {exp!r}, obtenido {got!r}"


def escenario_r4a19():
    """Escenario COMPUESTO del gap R4a-19: `alcance.excluir` esconde la interfaz del ledger.

    Un plan con `test-plan: n/a (sin UI)`, tres ficheros de interfaz en el diff y un
    `alcance.excluir: ["src/components/**"]` en `.claude/dev.json`. ANTES: `scope-check` salía 0
    (los tres quedaban «excluidos», no «fuera de alcance») y `coverage-check` salía 0 con
    `rutas_ui: []`, porque solo miraba los campos `Archivos` — donde esos ficheros NO están. El
    caso que `agents/qa.md` manda cazar era invisible por la COMPOSICIÓN de las dos puertas.
    AHORA el aviso lee también el diff y los tres salen con origen `diff`."""
    if not shutil.which("git"):
        print("· escenario R4a-19 omitido: no hay git en el PATH")
        return
    d = tempfile.mkdtemp()

    def g(*args):
        subprocess.run(["git"] + list(args), cwd=d, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", check=True)

    g("init", "-q", "-b", "master", ".")
    g("config", "user.email", "t@example.test")
    g("config", "user.name", "test")
    ini = os.path.join(d, "docs", "roadmap", "2026-01-01-x")
    os.makedirs(os.path.join(d, "src", "components"))
    os.makedirs(ini)
    os.makedirs(os.path.join(d, ".claude"))
    open(os.path.join(d, "README.md"), "w", encoding="utf-8").write("base\n")
    g("add", "-A")
    g("commit", "-qm", "base")
    g("checkout", "-qb", "feature/x")
    open(os.path.join(d, ".claude", "dev.json"), "w", encoding="utf-8").write(CONFIG_EXCLUIR)
    for f in ("Boton.tsx", "Panel.vue", "estilos.css"):
        open(os.path.join(d, "src", "components", f), "w", encoding="utf-8").write("x\n")
    open(os.path.join(ini, "improvement-plan.md"), "w", encoding="utf-8").write(PLAN_NA)
    tasks = os.path.join(ini, "tasks.md")
    open(tasks, "w", encoding="utf-8").write(
        "# Tareas\n### T-01 — cosa\n"
        "- **Archivos**: `docs/roadmap/2026-01-01-x/improvement-plan.md`\n"
        "- **Cubre (tests)**: —\n")
    g("add", "-A")
    g("commit", "-qm", "wip")

    # la puerta de ALCANCE pasa: los tres ficheros quedan «excluidos», no «fuera de alcance»
    scope = os.path.join(ROOT, "agent-kits", "shared", "scope-check.py")
    r = subprocess.run([sys.executable, scope, "docs/roadmap/2026-01-01-x", "--json"], cwd=d,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    eq(r.returncode, 0, "scope-check pasa: la exclusión los saca del exit code")
    sj = json.loads(r.stdout)
    eq(sj["fuera_de_alcance"], [], "nada fuera de alcance (por eso el hueco era invisible)")
    assert len([f for f in sj["excluidos"] if f.startswith("src/components/")]) == 3, sj

    # …y la puerta de COBERTURA ahora sí ve los tres, diciendo de dónde sale cada uno
    r = subprocess.run([sys.executable, SCRIPT, tasks, os.path.join(ini, "test-plan.md")], cwd=d,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    eq(r.returncode, 0, "el aviso no cambia el exit code")
    js = json.loads(r.stdout.strip().splitlines()[-1])
    eq(sorted(js["rutas_ui"]),
       ["src/components/Boton.tsx", "src/components/Panel.vue", "src/components/estilos.css"],
       "las rutas EXCLUIDAS del alcance salen igual, porque están en el diff")
    eq(js["rutas_ui_degradado"], None, "con git no hay degradación")
    for f in js["rutas_ui"]:
        eq(js["rutas_ui_origen"][f], "diff", f + " viene del diff, no del ledger")
    assert "[diff]" in r.stdout and "pinta de interfaz" in r.stdout, r.stdout
    shutil.rmtree(d, ignore_errors=True)


def _repo(rama="master"):
    """(carpeta, función git) de un repo temporal recién inicializado."""
    d = tempfile.mkdtemp()

    def g(*args):
        subprocess.run(["git"] + list(args), cwd=d, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", check=True)

    g("init", "-q", "-b", rama, ".")
    g("config", "user.email", "t@example.test")
    g("config", "user.name", "test")
    return d, g


def _iniciativa(d, tareas="# Tareas\n### T-01 — cosa\n- **Cubre (tests)**: —\n"):
    ini = os.path.join(d, "docs", "roadmap", "2026-01-01-x")
    os.makedirs(ini, exist_ok=True)
    open(os.path.join(ini, "improvement-plan.md"), "w", encoding="utf-8").write(PLAN_NA)
    tasks = os.path.join(ini, "tasks.md")
    open(tasks, "w", encoding="utf-8").write(tareas)
    return ini, tasks


def _corre(tasks, ini, cwd):
    r = subprocess.run([sys.executable, SCRIPT, tasks, os.path.join(ini, "test-plan.md")], cwd=cwd,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, json.loads(r.stdout.strip().splitlines()[-1]), r.stdout


def _modulo_coverage_check():
    """`coverage-check.py` cargado como módulo (el nombre lleva guion: no vale `import`)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("_coverage_check", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def escenario_r4a30():
    """Gap R4a-30: la TERCERA degradación silenciosa, el mismo hueco que R4a-19 por otra puerta.

    En la rama principal con el árbol limpio, `resolver_base` devuelve `HEAD` y la fuente «diff» no
    aporta NADA (solo se miran los cambios sin comitear) — pero `rutas_ui_degradado` salía `null`,
    que afirma lo contrario, y no se imprimía aviso: `qa` daba por inspeccionado un diff que nadie
    miró. Mismo caso cuando el diff contra la base no aporta ficheros."""
    if not shutil.which("git"):
        print("· escenario R4a-30 omitido: no hay git en el PATH")
        return
    d, g = _repo("master")
    ini, tasks = _iniciativa(d)
    g("add", "-A")
    g("commit", "-qm", "base")                      # rama principal + árbol LIMPIO

    rc, js, out = _corre(tasks, ini, d)
    eq(rc, 0, "el aviso no cambia el exit code")
    assert js["rutas_ui_degradado"], f"la base HEAD se declara: {js['rutas_ui_degradado']!r}"
    assert "HEAD" in js["rutas_ui_degradado"], js["rutas_ui_degradado"]
    assert "no se ha podido mirar el DIFF" in out, out

    # …y en una rama de trabajo cuyo diff contra la base no aporta ficheros, lo mismo
    g("checkout", "-qb", "feature/x")
    open(os.path.join(d, "suelto.txt"), "w", encoding="utf-8").write("x\n")
    rc, js, out = _corre(tasks, ini, d)
    eq(rc, 0, "sigue sin cambiar el exit code")
    assert js["rutas_ui_degradado"] and "no aporta ningún fichero" in js["rutas_ui_degradado"], js
    # y con un commit propio en la rama, el diff SÍ aporta: cero degradación (no-regresión)
    g("add", "-A")
    g("commit", "-qm", "wip")
    rc, js, out = _corre(tasks, ini, d)
    eq(js["rutas_ui_degradado"], None, "con diff real no hay degradación")
    shutil.rmtree(d, ignore_errors=True)


def escenario_b42():
    """Gap B4-2: la TERCERA causa de que no haya raíz de repo. Git está, la carpeta SÍ tiene `.git`
    y `git rev-parse` falla igual (config rota, `safe.directory`, repo corrupto). Antes se afirmaba
    «esto no es un repositorio git» y el remedio -`git init`- era el equivocado; el stderr de git,
    que explicaba el fallo de verdad, se tragaba."""
    if not shutil.which("git"):
        print("· escenario B4-2 omitido: no hay git en el PATH")
        return
    cc = _modulo_coverage_check()
    d = tempfile.mkdtemp()
    _ini, tasks = _iniciativa(d)
    # `.git` como FICHERO que apunta a un gitdir inexistente: repo «presente» y roto
    open(os.path.join(d, ".git"), "w", encoding="utf-8").write("gitdir: no-existe-de-verdad\n")
    _rutas, motivo = cc.rutas_del_diff(tasks)
    assert "hay un `.git`" in motivo, motivo
    assert "esto no es un repositorio git" not in motivo, motivo
    assert "safe.directory" in motivo, motivo
    assert "«" in motivo and "»" in motivo, "el stderr de git viaja en el mensaje: " + motivo
    # la sexta firma del acoplamiento E12, leída con getattr y con respaldo si no esta
    mod = cc._scope_check_mod()
    assert callable(getattr(mod, "motivo_sin_repo", None)), "scope-check.py ya no expone motivo_sin_repo()"
    assert callable(getattr(mod, "hay_git_dir", None)), "scope-check.py ya no expone hay_git_dir()"
    shutil.rmtree(d, ignore_errors=True)


def escenario_b43_b44():
    """Gaps B4-3 (falsos NEGATIVOS) y B4-4 (falsos POSITIVOS) de la misma familia: la pista que
    viene SOLO del nombre de la carpeta.

    B4-3: `src/components` o `frontend` -sin barra- son la forma que `scope-check.casa()` soporta a
    propósito para declarar una carpeta, y exigir la barra las dejaba fuera. Se resuelve como lo
    resuelve `casa()`: preguntando al sistema de ficheros.
    B4-4: con la carpeta como única pista, la extensión tiene que ser de interfaz; si no, un backend
    puro -justo quien declara «sin UI»- tenía que desmontar el falso positivo a mano."""
    cc = _modulo_coverage_check()
    d = tempfile.mkdtemp()
    for carpeta in ("src/components", "frontend", "db/views"):
        os.makedirs(os.path.join(d, *carpeta.split("/")), exist_ok=True)
    open(os.path.join(d, "public"), "w", encoding="utf-8").write("x")   # FICHERO, no carpeta

    # B4-3: la carpeta declarada sin barra cuenta… sí de verdad es una carpeta
    for tok in ("src/components", "frontend"):
        assert cc._parece_ui(tok, d) is True, "B4-3: carpeta declarada sin barra: " + tok
        assert cc._parece_ui(tok, None) is False, "sin raíz no se pregunta al disco: " + tok
    # …y el fichero sin extensión llamado `public` sigue sin contar (el falso positivo de R4a-36)
    assert cc._parece_ui("public", d) is False, "B4-3 no puede reabrir R4a-36"
    assert cc._parece_ui("assets", d) is False, "B4-3 no puede reabrir R4a-36"

    # B4-4: los seis falsos positivos que la lente enumeró
    for tok in ("db/views/v.sql", "templates/mail.json", "static/datos.csv", "assets/fuente.ttf",
                "screens/README.json", "e2e/datos.csv"):
        assert cc._parece_ui(tok, d) is False, "B4-4: la extensión no es de interfaz: " + tok
    # …y lo que SÍ es interfaz por carpeta + extensión sigue contando
    for tok in ("db/views/lista.tsx", "templates/mail.twig", "static/app.js", "assets/estilo.css",
                "screens/Home.swift", "e2e/login.spec.ts", "web/app.js", "public/index.html"):
        assert cc._parece_ui(tok, d) is True, "no se ha aflojado la pista: " + tok
    shutil.rmtree(d, ignore_errors=True)


def escenario_r4a34_r4a35_r4a40():
    """R4a-34 (no hay git ≠ no es un repo), R4a-35 (no reenviar un `--base` que no existe) y
    R4a-40 (el acoplamiento entre kits: las tres firmas de `scope-check.py` que `coverage-check.py`
    necesita). Se ejecuta en proceso: hace falta manipular el PATH."""
    if not shutil.which("git"):
        print("· escenario R4a-34/35/40 omitido: no hay git en el PATH")
        return
    cc = _modulo_coverage_check()

    # R4a-40: la arista E12 de CONTRACTS.md, comprobada — si una firma se renombra, esto cae aquí
    # en vez de degradar a `rutas_ui_degradado` con la puerta en verde y ciega al diff
    mod = cc._scope_check_mod()
    assert mod is not None, "los helpers de scope-check.py tienen que cargarse"
    for firma in ("repo_root", "resolver_base", "ficheros_cambiados", "git", "git_disponible"):
        assert callable(getattr(mod, firma, None)), f"scope-check.py ya no expone {firma}()"

    d, g = _repo("master")
    ini, tasks = _iniciativa(d)
    g("add", "-A")
    g("commit", "-qm", "base")

    # R4a-34 (a): con git, una carpeta que NO es repo sigue diciendo lo de siempre
    fuera = tempfile.mkdtemp()
    _, tasks_fuera = _iniciativa(fuera)
    _rutas, motivo = cc.rutas_del_diff(tasks_fuera)
    eq(motivo, "esto no es un repositorio git", "fuera de un repo, el motivo de siempre")

    # R4a-34 (b): sin `git` en el PATH la causa es OTRA y el remedio también
    vacio = tempfile.mkdtemp()
    previo = os.environ.get("PATH", "")
    os.environ["PATH"] = vacio
    try:
        _rutas, motivo = cc.rutas_del_diff(tasks)
    finally:
        os.environ["PATH"] = previo
    assert "no hay `git` en el PATH" in motivo, motivo
    assert "no es un repositorio" not in motivo.split("(")[0], motivo

    # R4a-35: sin base determinable (ni main ni master), el motivo NO pide un `--base` que
    # `coverage-check.py` no acepta; dice qué hacer de verdad
    d2, g2 = _repo("trabajo")
    ini2, tasks2 = _iniciativa(d2)
    g2("add", "-A")
    g2("commit", "-qm", "base")
    _rutas, motivo = cc.rutas_del_diff(tasks2)
    assert "sin base de diff determinable" in motivo, motivo
    assert "pasa `--base" not in motivo, motivo
    assert "no acepta `--base`" in motivo and "`Archivos`" in motivo, motivo
    for t in (d, d2, fuera, vacio):
        shutil.rmtree(t, ignore_errors=True)


def main():
    # regresión: comportamiento existente sin spec
    rc, js, _ = run(TASKS_OK, PLAN_OK)
    eq(rc, 0, "caso base verde")
    eq(js["broken_refs"], 0, "sin referencias rotas")
    assert "T-02" in js["tasks_sin_cobertura"], "T-02 sin cobertura es aviso"

    rc, js, _ = run(TASKS_OK.replace("E2E-01", "E2E-99"), PLAN_OK)
    eq(rc, 1, "referencia rota → exit 1")

    rc, js, _ = run(TASKS_OK, None)
    eq(rc, 0, "sin test-plan y sin spec GWT → no aplica, exit 0")
    eq(js.get("applies"), False, "no aplica")

    # [GWT] cubierto: CA-01 aparece en el plan; CA-02 no → error
    rc, js, out = run(TASKS_OK, PLAN_OK, SPEC_GWT)
    eq(rc, 1, "GWT sin cubrir → exit 1")
    eq(js["gwt_cubiertos"], ["CA-01"], "CA-01 cubierto (mención en el plan)")
    eq(js["gwt_sin_cubrir"], ["CA-02"], "CA-02 sin cubrir")
    eq(js["gwt_sin_id"], 1, "un GWT sin ID es aviso")
    assert "CA-02" in out and "❌" in out, "el error de CA-02 se imprime"

    # todos los GWT cubiertos → verde
    plan2 = PLAN_OK + "\n## E2E-02 — contador\nCubre CA-02\n"
    rc, js, _ = run(TASKS_OK, plan2, SPEC_GWT)
    eq(rc, 0, "todos los GWT cubiertos → exit 0")
    eq(js["gwt_sin_cubrir"], [], "nada sin cubrir")

    # GWT presentes pero SIN test-plan → los GWT prometen test: exit 1
    rc, js, _ = run(TASKS_OK, None, SPEC_GWT)
    eq(rc, 1, "GWT sin test-plan → exit 1")
    eq(sorted(js["gwt_sin_cubrir"]), ["CA-01", "CA-02"], "ambos sin cubrir")

    # spec sin criterios GWT → idéntico al comportamiento base
    rc, js, _ = run(TASKS_OK, PLAN_OK, "---\nspec: y\n---\n- [ ] criterio libre\n")
    eq(rc, 0, "spec sin GWT no cambia el resultado")
    eq(js["gwt_cubiertos"], [], "sin GWT")

    # --- robustez (revisión lente B) ---
    # ID en negrita, [gwt] minúsculas y viñeta *: los tres deben detectarse CON id
    spec_variantes = """---
spec: v
---
- [ ] [GWT] **CA-01** — Dado a, Cuando b, Entonces c
- [X] [gwt] CA-02 — Dado d, Cuando e, Entonces f
* [ ] [GWT] CA-03 — Dado g, Cuando h, Entonces i
"""
    plan_v = "## E2E-01\ncubre CA-01 y CA-02 y CA-03\n"
    rc, js, _ = run(TASKS_OK, plan_v, spec_variantes)
    eq(rc, 0, "variantes de formato GWT cubiertas → verde")
    eq(sorted(js["gwt_cubiertos"]), ["CA-01", "CA-02", "CA-03"],
       "negrita/minúsculas/asterisco detectados con ID")
    eq(js["gwt_sin_id"], 0, "ninguno cae a sin-id por el formato")

    # un ejemplo [GWT] dentro de un bloque de código NO cuenta como criterio real
    spec_fence = ("---\nspec: f\n---\nFormato:\n\n```markdown\n"
                  "- [ ] [GWT] CA-77 — Dado ejemplo, Cuando doc, Entonces nada\n```\n"
                  "- [ ] criterio libre real\n")
    rc, js, _ = run(TASKS_OK, PLAN_OK, spec_fence)
    eq(rc, 0, "GWT en bloque de código no dispara la puerta")
    eq(js["gwt_cubiertos"] + js["gwt_sin_cubrir"], [], "CA-77 de ejemplo ignorado")

    # todos los GWT sin ID + sin test-plan → exit 0 pero CON aviso visible
    spec_sinid = "---\nspec: s\n---\n- [ ] [GWT] Dado a, Cuando b, Entonces c\n"
    rc, js, out = run(TASKS_OK, None, spec_sinid)
    eq(rc, 0, "GWT sin ID y sin test-plan no rompe")
    assert "no son rastreables" in out, "el aviso de GWT sin ID sin test-plan se imprime"
    eq(js["gwt_sin_id"], 1, "el JSON refleja los sin-id")

    # --- marcador `test-plan: n/a (sin UI)` (C-08, hueco E1, T-13) ---

    # con marcador y sin test-plan: exit 0, es una DECISIÓN y no se pide regenerar nada
    rc, js, out = run(TASKS_OK, None, improvement_plan=PLAN_NA)
    eq(rc, 0, "marcador declarado: sin test-plan no es un olvido")
    eq(js.get("test_plan_na"), True, "el JSON refleja el marcador")
    assert "planner" not in out, f"con marcador no se pide regenerar el test-plan: {out!r}"

    # sin marcador: el aviso es UNO y trae el comando que lo fija
    rc, js, out = run(TASKS_OK, None, improvement_plan=PLAN_CON_UI)
    eq(rc, 0, "sin marcador y sin test-plan sigue siendo exit 0")
    eq(js.get("test_plan_na"), False, "sin marcador el JSON lo dice")
    eq(out.count("sin test-plan.md"), 1, "aviso UNA vez, no en bucle")
    assert "test-plan: n/a (sin UI)" in out and "planner" in out, out

    # criterios [GWT] + marcador: no fuerzan exit 1, pero se LISTAN (no se silencian)
    rc, js, out = run(TASKS_OK, None, SPEC_GWT, improvement_plan=PLAN_NA)
    eq(rc, 0, "GWT con marcador sin UI -> exit 0 (su evidencia es la Verificacion del ledger)")
    eq(js.get("test_plan_na"), True, "marcador reflejado")
    assert "CA-01" in out and "CA-02" in out and "Verificación" in out, out
    assert "❌" not in out, "ningun error con el marcador declarado"
    # R4a-22: los [GWT] SÍ los exigía la puerta, así que aquí «eximir» es la palabra correcta
    eq(js["eximidos_exigidos"], True, "los [GWT] estaban sujetos a la puerta")
    assert "se eximen" in out, out

    # … y sin marcador esos mismos GWT siguen siendo exit 1 (no se ha aflojado la puerta)
    rc, js, _ = run(TASKS_OK, None, SPEC_GWT, improvement_plan=PLAN_CON_UI)
    eq(rc, 1, "GWT sin test-plan y SIN marcador siguen en exit 1")

    # el marcador solo cuenta en el FRONTMATTER: citado en la prosa no decide
    plan_prosa = "---\nplan: x\n---\n# Plan\nAqui se explica `test-plan: n/a (sin UI)` como concepto.\n"
    rc, js, out = run(TASKS_OK, None, SPEC_GWT, improvement_plan=plan_prosa)
    eq(rc, 1, "marcador en la prosa no exime")
    eq(js.get("test_plan_na"), False, "solo el frontmatter cuenta")

    # sin improvement-plan.md no hay marcador y nada peta
    rc, js, out = run(TASKS_OK, None)
    eq(rc, 0, "sin improvement-plan.md sigue el comportamiento clasico")
    eq(js.get("test_plan_na"), False, "sin plan, sin marcador")

    # --- gaps R4a-2, R4a-7, R4a-8, R4a-9 (revisión de dos lentes del tramo R4a, intento 1) ---

    # R4a-2: el marcador emite ℹ️ y NUNCA ✅ (un ✅ se lee como «cobertura comprobada» en el
    # informe de qa, y aquí no se ha comprobado nada: se ha aceptado una declaración)
    rc, js, out = run(TASKS_OK, None, improvement_plan=PLAN_NA)
    assert "✅" not in out, f"el marcador no puede salir en verde: {out!r}"
    assert "ℹ️" in out, out

    # R4a-2: sin criterios [GWT] la exención se lista IGUAL (antes: una línea y nada más).
    # Sin spec, la escalera cae a las tareas del ledger.
    eq(sorted(js["eximidos"]), ["T-01", "T-02"], "sin spec se listan las tareas del ledger")
    assert "T-01" in out and "tarea(s) del ledger" in out, out
    # R4a-22: sin [GWT] la puerta no exigía NADA, así que no se «exime»: se LISTA para la revisión
    eq(js["eximidos_exigidos"], False, "las tareas del ledger no estaban sujetas a la puerta")
    assert "se listan para la revisión" in out and "se eximen" not in out, out

    # …con spec SIN [GWT] se listan sus criterios CA-XX
    spec_ca = "---\nspec: c\n---\n- [ ] CA-01 — algo\n- [x] **CA-02** — otra cosa\n- [ ] libre\n"
    rc, js, out = run(TASKS_OK, None, spec_ca, improvement_plan=PLAN_NA)
    eq(js["eximidos"], ["CA-01", "CA-02"], "criterios de la spec listados sin [GWT]")
    assert "ninguno [GWT]" in out, out

    # …y si no hay NADA que listar, lo dice con esas palabras (nunca una línea sola y muda)
    rc, js, out = run("# Tareas\nsin tareas\n", None, improvement_plan=PLAN_NA)
    eq(js["eximidos"], [], "nada que listar")
    assert "no hay nada que listar" in out, out

    # R4a-2: aviso si el alcance declarado tiene pinta de UI habiendo marcador
    tasks_ui = TASKS_OK + "- **Archivos**: `src/components/Boton.tsx`, `agent-kits/shared/x.py`\n"
    rc, js, out = run(tasks_ui, None, improvement_plan=PLAN_NA)
    eq(rc, 0, "el aviso de UI no cambia el exit code")
    eq(js["rutas_ui"], ["src/components/Boton.tsx"], "solo la ruta con pinta de UI")
    eq(js["rutas_ui_origen"], {"src/components/Boton.tsx": "ledger"}, "sin git, sale del ledger")
    assert "⚠️" in out and "pinta de interfaz" in out, out
    # y sin rutas de UI no hay ruido
    rc, js, out = run(TASKS_OK + "- **Archivos**: `agent-kits/shared/x.py`\n", None,
                      improvement_plan=PLAN_NA)
    eq(js["rutas_ui"], [], "sin rutas de UI, sin aviso")
    assert "pinta de interfaz" not in out, out

    # …y un DOCUMENTO no es una vista por el nombre de su carpeta (falso positivo real de este
    # repo: `agent-kits/planner/templates/improvement-plan.md` es una plantilla de texto)
    tasks_doc = TASKS_OK + "- **Archivos**: `agent-kits/planner/templates/improvement-plan.md`, `docs/views/guia.md`\n"
    rc, js, out = run(tasks_doc, None, improvement_plan=PLAN_NA)
    eq(js["rutas_ui"], [], "los .md no cuentan como interfaz")
    assert "pinta de interfaz" not in out, out

    # R4a-7: el marcador ANIDADO bajo otra clave no exime (en YAML es `plan.test-plan`)
    plan_anidado = "---\nplan:\n  test-plan: n/a (sin UI)\n---\n# Plan\n"
    rc, js, _ = run(TASKS_OK, None, SPEC_GWT, improvement_plan=plan_anidado)
    eq(rc, 1, "clave anidada no exime")
    eq(js.get("test_plan_na"), False, "solo la clave de primer nivel")

    # R4a-7: basura DETRÁS del literal no exime (antes: sin ancla final valía cualquier cosa)
    plan_basura = "---\nplan: x\ntest-plan: n/a (sin UI) pero en realidad sí hay UI\n---\n# Plan\n"
    rc, js, _ = run(TASKS_OK, None, SPEC_GWT, improvement_plan=plan_basura)
    eq(rc, 1, "basura detrás del literal no exime")
    eq(js.get("test_plan_na"), False, "el marcador va anclado al final")

    # R4a-7: la forma CITADA es YAML equivalente y SÍ exime (antes pedía declarar lo declarado)
    for comillas in ('"', "'"):
        plan_citado = f"---\nplan: x\ntest-plan: {comillas}n/a (sin UI){comillas}\n---\n# Plan\n"
        rc, js, out = run(TASKS_OK, None, SPEC_GWT, improvement_plan=plan_citado)
        eq(rc, 0, f"la forma citada con {comillas} exime")
        eq(js.get("test_plan_na"), True, "marcador citado reconocido")

    # R4a-8: un BOM al principio del plan ya no anula el marcador en silencio
    rc, js, _ = run(TASKS_OK, None, SPEC_GWT, improvement_plan="﻿" + PLAN_NA)
    eq(rc, 0, "BOM en improvement-plan.md no anula el marcador")
    eq(js.get("test_plan_na"), True, "utf-8-sig al leer el plan")

    # R4a-9: `test_plan_na` sale en las CUATRO ramas del --json, no solo en las dos sin test-plan
    rc, js, _ = run(TASKS_OK, PLAN_OK)                      # rama normal, con test-plan
    assert "test_plan_na" in js, js
    eq(js["test_plan_na"], False, "sin marcador")
    rc, js, _ = run(TASKS_OK, PLAN_OK, improvement_plan=PLAN_NA)
    eq(js["test_plan_na"], True, "con test-plan Y marcador, la clave lo dice igual")
    rc, js, _ = run("# Ledger sin tareas\n", PLAN_OK, improvement_plan=PLAN_NA)  # rama no_tasks
    eq(rc, 1, "ledger sin tareas sigue en exit 1")
    assert js.get("no_tasks") and js.get("test_plan_na") is True, js

    # --- gaps R4a-19, R4a-23, R4a-24, R4a-26 (revisión de dos lentes, intento 2) ---

    # R4a-23: las formas NO canónicas siguen eximiendo, pero AVISAN (escritas así, el `grep` del
    # literal con el que el resto de la cadena las busca no las encuentra)
    for raro in ("Test-Plan: n/a (sin UI)", "test-plan: N/A (SIN UI)", "test-plan:n/a (sin UI)"):
        plan_raro = "---\nplan: x\n" + raro + "\n---\n# Plan\n"
        rc, js, out = run(TASKS_OK, None, SPEC_GWT, improvement_plan=plan_raro)
        eq(rc, 0, "la forma no canónica se acepta: " + raro)
        eq(js.get("test_plan_na"), True, "exime igual: " + raro)
        eq(js.get("marcador_no_canonico"), raro, "se declara no canónica: " + raro)
        assert "forma canónica" in out, out
    # …y la canónica no avisa de nada
    rc, js, out = run(TASKS_OK, None, SPEC_GWT, improvement_plan=PLAN_NA)
    eq(js.get("marcador_no_canonico"), None, "la forma canónica no avisa")
    assert "forma canónica" not in out, out

    # R4a-24: el frontmatter puede cerrar en el FIN DEL FICHERO, sin salto final (antes: la
    # cabecera salía vacía, el marcador desaparecía y el exit 0 declarado se volvía exit 1)
    rc, js, _ = run(TASKS_OK, None, SPEC_GWT,
                    improvement_plan="---\nplan: x\ntest-plan: n/a (sin UI)\n---")
    eq(rc, 0, "frontmatter sin salto final: el marcador sigue valiendo")
    eq(js.get("test_plan_na"), True, "marcador reconocido al cerrar en EOF")

    # R4a-26: pistas de interfaz que faltaban (.astro, .twig, .svg, assets/, web/ y `components`
    # como NOMBRE de fichero)
    nuevas = ["src/Home.astro", "tpl/lista.twig", "img/logo.svg", "assets/x.js", "web/app.js",
              "src/components.ts"]
    tasks_nuevas = TASKS_OK + "- **Archivos**: " + ", ".join("`" + x + "`" for x in nuevas) + "\n"
    rc, js, out = run(tasks_nuevas, None, improvement_plan=PLAN_NA)
    eq(sorted(js["rutas_ui"]), sorted(nuevas), "las pistas nuevas se detectan")

    # R4a-19: sin git, el aviso se DEGRADA al alcance declarado y lo DICE (nunca en silencio)
    rc, js, out = run(TASKS_OK, None, improvement_plan=PLAN_NA)
    assert js["rutas_ui_degradado"], "sin repo git, la degradación se declara"
    assert "no se ha podido mirar el DIFF" in out, out

    # --- gaps R4a-29…R4a-40 (revisión de dos lentes del tramo R4a, intento 3) ---

    # R4a-31: la regex CANÓNICA solo acepta la forma que encuentra `grep -F` del literal. El
    # tabulador, el doble espacio y las dos formas entrecomilladas eximen —por la laxa— pero AVISAN
    for raro in ("test-plan:\tn/a (sin UI)", "test-plan:  n/a (sin UI)",
                 'test-plan: "n/a (sin UI)"', "test-plan: 'n/a (sin UI)'"):
        plan_raro = "---\nplan: x\n" + raro + "\n---\n# Plan\n"
        rc, js, out = run(TASKS_OK, None, SPEC_GWT, improvement_plan=plan_raro)
        eq(rc, 0, "la forma no canónica sigue eximiendo: " + repr(raro))
        eq(js.get("test_plan_na"), True, "exime igual: " + repr(raro))
        eq(js.get("marcador_no_canonico"), raro, "declarada NO canónica: " + repr(raro))
        assert "forma canónica" in out, out
        # el criterio que las declara no canónicas: `grep -F` del literal no las encuentra
        assert "test-plan: n/a (sin UI)" not in raro, raro
    # …y la única forma que el `grep` SÍ encuentra sigue sin avisar de nada
    rc, js, out = run(TASKS_OK, None, SPEC_GWT, improvement_plan=PLAN_NA)
    eq(js.get("marcador_no_canonico"), None, "la canónica no avisa")
    assert "test-plan: n/a (sin UI)" in PLAN_NA, "la canónica es la que encuentra `grep -F`"

    # R4a-32: `marcador_no_canonico` sale en las CUATRO ramas del --json, no en dos
    plan_raro = "---\nplan: x\ntest-plan:\tn/a (sin UI)\n---\n# Plan\n"
    plan_roto = "---\nplan: x\nTest-Plan: n/a (sin UI)\n---\n# Plan\n"
    rc, js, _ = run(TASKS_OK, PLAN_OK, improvement_plan=plan_raro)            # rama con test-plan
    eq(js.get("marcador_no_canonico"), "test-plan:\tn/a (sin UI)", "rama normal")
    rc, js, _ = run(TASKS_OK, None, SPEC_GWT, improvement_plan=plan_raro)     # rama sin test-plan
    eq(js.get("marcador_no_canonico"), "test-plan:\tn/a (sin UI)", "rama sin UI")
    rc, js, _ = run("# Ledger sin tareas\n", PLAN_OK, improvement_plan=plan_raro)  # rama no_tasks
    eq(rc, 1, "ledger sin tareas sigue en exit 1")
    eq(js.get("marcador_no_canonico"), "test-plan:\tn/a (sin UI)", "rama no_tasks")
    # rama «[GWT] sin test-plan y sin marcador»: la clave está, con valor None (no hay marcador)
    rc, js, _ = run(TASKS_OK, None, SPEC_GWT, improvement_plan=PLAN_CON_UI)
    eq(rc, 1, "sin marcador, los GWT siguen forzando exit 1")
    assert "marcador_no_canonico" in js, js
    eq(js["marcador_no_canonico"], None, "sin marcador, la clave existe y es None")
    # …y con un marcador no canónico en ESA rama, la clave lo dice (antes: la rama no la emitía)
    rc, js, _ = run(TASKS_OK, PLAN_OK.replace("E2E-01", "E2E-77"), SPEC_GWT,
                    improvement_plan=plan_roto)
    assert "marcador_no_canonico" in js and js["marcador_no_canonico"] == "Test-Plan: n/a (sin UI)", js

    # R4a-36: falsos positivos de `UI_PISTAS` que el revisor tenía que desmontar uno a uno
    falsos = ["tests/fixtures/web/a.json", "infra/terraform/web/main.tf", "public", "assets",
              "components.json", "src/ui", "cfg/components.yaml",
              # B4-4: la carpeta como única pista no basta si la extensión no es de interfaz
              "db/views/v.sql", "templates/mail.json", "static/datos.csv", "assets/fuente.ttf",
              "screens/README.json", "e2e/datos.csv"]
    tasks_fp = TASKS_OK + "- **Archivos**: " + ", ".join("`" + x + "`" for x in falsos) + "\n"
    rc, js, out = run(tasks_fp, None, improvement_plan=PLAN_NA)
    eq(js["rutas_ui"], [], "ni carpetas sin barra, ni `web` fuera de la raíz, ni config")
    assert "pinta de interfaz" not in out, out
    # …y lo que SÍ es interfaz se sigue detectando (no se ha aflojado la pista)
    verdaderos = ["web/app.js", "public/index.html", "src/assets/logo.svg", "src/components.ts",
                  "app/components/Boton.tsx", "e2e/login.spec.ts"]
    tasks_ok_ui = TASKS_OK + "- **Archivos**: " + ", ".join("`" + x + "`" for x in verdaderos) + "\n"
    rc, js, out = run(tasks_ok_ui, None, improvement_plan=PLAN_NA)
    eq(sorted(js["rutas_ui"]), sorted(verdaderos), "las pistas reales siguen saltando")

    # R4a-19: el escenario compuesto (exclusión de `dev.json` + interfaz solo en el diff)
    escenario_r4a19()
    # R4a-30: la base `HEAD` (y el diff que no aporta ficheros) se DECLARAN
    escenario_r4a30()
    # R4a-34 / R4a-35 / R4a-40: causa de la degradación, consejo accionable y firmas del acoplamiento
    escenario_r4a34_r4a35_r4a40()
    # B4-2: la tercera causa de «no hay raíz de repo», con el stderr de git a la vista
    escenario_b42()
    # B4-3 / B4-4: la carpeta declarada sin barra cuenta; la extensión que no es de interfaz, no
    escenario_b43_b44()

    print("OK: coverage-check con criterios [GWT] y marcador sin-UI — todo pasa.")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"FALLO: {e}", file=sys.stderr)
        sys.exit(1)
