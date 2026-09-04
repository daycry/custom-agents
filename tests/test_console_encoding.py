#!/usr/bin/env python3
"""Tests de la codificación de la consola en las dos direcciones (windows-console T-01/T-04/T-05).

Bug reportado por el usuario el 2026-09-03: `python scripts/release.py 1.16.0` en PowerShell reventaba
porque `lint_plugin.py`, lanzado por `release.py` con `capture_output=True` (stdout a un PIPE, sin la
API de consola de Windows), caía al ANSI codepage del locale — `cp1252` — y `print(f"⚠️  {w}")` lanzaba
`UnicodeEncodeError`. Reproducible en cualquier SO con `PYTHONIOENCODING=cp1252`.

Las DOS mitades de la regla (docs/CONVENTIONS.md regla 8, GOT-005):
  1. **Lado propio** — todo script del plugin que ESCRIBA símbolos o LEA de `sys.stdin` reconfigura
     `sys.stdin`/`stdout`/`stderr` a UTF-8 con `errors="replace"` **al arrancar**, con el snippet
     replicado LITERAL (son standalone: el paquete portable los copia sueltos y los agentes los
     invocan con `python3 <ruta>`, sin `PYTHONPATH`). `stdin` entra desde T-04: el guardrail del
     implementer leía el payload del hook con el codec del locale y su `except` convertía el
     `UnicodeDecodeError` en un ALLOW silencioso. Y desde T-05 el criterio MIRA quién lee: el lado
     que lee no depende del fuente sino del payload, así que un `.py` ASCII puro entra igual —
     `pick_asset.py` era la 28.ª pieza, hacía `json.load(sys.stdin)` y no la veía nadie.
  2. **Lado padre** — todo `.py` del plugin que capture un subproceso en modo TEXTO fija
     `encoding="utf-8", errors="replace"`: los hijos escriben UTF-8 siempre, así que decodificarlos
     con el codec del locale revienta al padre justo donde antes daba su veredicto.

El criterio de qué ficheros entran (`es_pieza`, `exige_snippet`) y las comprobaciones estructurales
(`snippet_al_arrancar`, `lee_stdin`, `subprocess_sin_encoding`) son el MISMO TEXTO que en
`scripts/lint_plugin.py`, y dos tests lo comprueban: uno compara los bloques byte a byte y otro
compara los VEREDICTOS del linter y de la suite sobre árboles reales. Única diferencia deliberada, y
está dicha en CONVENTIONS 8: el linter mira el DISCO (tiene que funcionar sobre un plugin
desempaquetado, sin git) y esta suite mira `git ls-files`. Por eso la comparación de veredictos solo
mira lo VERSIONADO (T-05): si no, un `.py` sin `git add` en el árbol de trabajo del desarrollador
ponía roja la suite acusando al criterio de haber divergido.

Ejecutar: python3 -m pytest -q tests/test_console_encoding.py
"""
import ast
import os
import re
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --8<-- criterio de consola COMPARTIDO (windows-console T-04/T-05) — REPLICADO LITERAL en
# scripts/lint_plugin.py y en tests/test_console_encoding.py. No lo edites en uno solo:
# `test_linter_y_suite_replican_el_mismo_bloque` compara los dos textos byte a byte, y
# `test_linter_y_suite_dan_el_mismo_veredicto` compara sus veredictos sobre árboles reales.
# Se replica (en vez de importarse) por el mismo contrato que el snippet: los scripts del plugin
# son standalone y el paquete portable los copia sueltos, sin PYTHONPATH ni módulo común.
CONSOLE_MARK = 'reconfigure(encoding="utf-8", errors="replace")'


def es_pieza(rel):
    """¿`rel` es una pieza del plugin a la que aplican las reglas de consola (CONVENTIONS 8)?

    Fuera del criterio, y solo esto:
      - las suites: basename que empieza por `test_` (no imprimen a la consola de nadie);
      - cualquier ruta con un segmento de directorio `fixtures`: es código del proyecto CONSUMIDOR
        simulado (lo que ejecutan los evals), no una pieza nuestra, y su salida no es nuestra.
    """
    partes = rel.replace("\\", "/").split("/")
    return not partes[-1].startswith("test_") and "fixtures" not in partes[:-1]


def _es_reconfigure(nodo):
    """¿`nodo` es la llamada `<stream>.reconfigure(encoding="utf-8", errors="replace")` del snippet?

    Se mira el NODO, no el texto: así una mención en un docstring o en un comentario no cuenta.
    """
    if not (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute)
            and nodo.func.attr == "reconfigure"):
        return False
    kws = {k.arg: k.value for k in nodo.keywords}
    return all(isinstance(kws.get(a), ast.Constant) and kws[a].value == v
               for a, v in (("encoding", "utf-8"), ("errors", "replace")))


def _previo_admitido(nodo):
    """Sentencias de módulo que pueden ir ANTES del snippet: no leen ni escriben en los streams."""
    if isinstance(nodo, (ast.Import, ast.ImportFrom)):     # incluye `from __future__ import …`
        return True
    return (isinstance(nodo, ast.Expr) and isinstance(nodo.value, ast.Constant)
            and isinstance(nodo.value.value, str))        # docstring del módulo


def snippet_al_arrancar(src):
    """¿El snippet de CONVENTIONS 8 protege de verdad a este fichero? (True/False/None)

    ESTRUCTURAL con `ast`, no `grep` de subcadena: medido (T-04) que la marca dentro de `main()` con
    un `print` de símbolos a nivel de módulo antes, o citada solo en un docstring, daba 0 avisos y el
    script reventaba igual bajo cp1252. Exige las dos cosas:
      (a) la llamada a `reconfigure` está en una sentencia de NIVEL DE MÓDULO (no dentro de un `def`
          ni de una `class`: ahí no protege el arranque), y
      (b) esa sentencia va antes de cualquier otra sentencia de módulo que no sea el docstring o un
          `import`/`from … import` — es decir, antes del primer `print` o del primer `stdin.read()`.
    `None` = el fichero no es Python parseable: ni se afirma ni se niega (no se opina a ciegas).
    """
    try:
        arbol = ast.parse(src)
    except (SyntaxError, ValueError):
        return None
    for i, nodo in enumerate(arbol.body):
        if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if any(_es_reconfigure(n) for n in ast.walk(nodo)):
            return all(_previo_admitido(p) for p in arbol.body[:i])
    return False


def _sys_alias(arbol):
    """Nombres con los que este módulo nombra a `sys` y a `sys.stdin` (`import sys as s`,
    `from sys import stdin as entrada`)."""
    alias, directos = {"sys"}, set()
    for n in ast.walk(arbol):
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name == "sys":
                    alias.add(a.asname or "sys")
        elif isinstance(n, ast.ImportFrom) and n.module == "sys":
            for a in n.names:
                if a.name == "stdin":
                    directos.add(a.asname or "stdin")
    return alias, directos


def lee_stdin(src):
    """¿Este fichero USA `sys.stdin`? El lado que LEE no depende de su fuente, sino del PAYLOAD.

    Un `.py` 100 % ASCII revienta igual: `json.load(sys.stdin)` decodifica con el codec del locale, y
    el JSON de una release de GitHub trae emojis en `body` (🐛 = `F0 9F 90 9B`, con el byte `0x90`, y
    👍 con `0x8D`; ninguno existe en cp1252). Medido en `agent-kits/nemesis/tools/pick_asset.py`, que
    era la 28.ª pieza versionada y quedaba invisible para el criterio del lado que ESCRIBE.
    Con `ast`, no con `grep`: una mención en un comentario o dentro de una cadena no cuenta. El propio
    snippet nombra `sys.stdin`, así que queda fuera SOLO el `iter` de su `for` — si no, todo fichero
    con snippet «leería» stdin y el criterio se volvería circular. Excluir la sentencia entera sería
    peor que circular: apagaría la detección en todo el cuerpo de la función que alojase el snippet.
    """
    try:
        arbol = ast.parse(src)
    except (SyntaxError, ValueError):
        return False
    alias, directos = _sys_alias(arbol)
    del_snippet = set()
    for n in ast.walk(arbol):
        # SOLO el `sys.stdin` que el propio snippet nombra en su `iter`: excluir la sentencia entera
        # (o peor, cualquier ancestro que la contenga) apagaba la detección en todo el cuerpo de la
        # función donde estuviera el snippet — justo el anti-patrón «snippet dentro de `main()`» que
        # el linter existe para cazar. Medido en la revisión, intento 3.
        if isinstance(n, ast.For) and any(_es_reconfigure(c) for c in ast.walk(n)):
            del_snippet.update(id(x) for x in ast.walk(n.iter))
    for n in ast.walk(arbol):
        if id(n) in del_snippet:
            continue
        if (isinstance(n, ast.Attribute) and n.attr == "stdin"
                and isinstance(n.value, ast.Name) and n.value.id in alias):
            return True
        if isinstance(n, ast.Name) and n.id in directos:
            return True
        # `input()` y `fileinput.input()` leen del mismo stdin y con el mismo codec del locale.
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name) and f.id == "input":
                return True
            if (isinstance(f, ast.Attribute) and f.attr in ("input", "FileInput")
                    and isinstance(f.value, ast.Name) and f.value.id == "fileinput"):
                return True
    return False


def exige_snippet(data, src):
    """¿Esta pieza TIENE que llevar el snippet? Dos motivos independientes, no uno:

      (a) su FUENTE trae caracteres no ASCII — los imprime, y en cp1252 el primer `print` revienta
          con `UnicodeEncodeError`;
      (b) LEE de `sys.stdin` — el payload puede traerlos aunque el fuente sea ASCII puro, y entonces
          revienta con `UnicodeDecodeError`.
    `data` son los bytes del fichero y `src` su texto. El `or` corta a la izquierda: solo se parsea
    (b) cuando (a) no ha decidido ya.
    """
    return any(b > 127 for b in data) or lee_stdin(src)


def _kw(nodo, nombre):
    for k in nodo.keywords:
        if k.arg == nombre:
            return k
    return None


def _kw_verdadero(k):
    return k is not None and not (isinstance(k.value, ast.Constant) and k.value.value in (False, None))


SUBPROCESS_FUNCS = {"run", "Popen", "check_output", "check_call", "call", "getoutput", "getstatusoutput"}


def subprocess_sin_encoding(src):
    """Líneas con una llamada a `subprocess` en modo TEXTO y SIN `encoding=` (el lado PADRE, T-04).

    Desde T-01 los hijos escriben UTF-8 SIEMPRE; un padre que los decodifique con el codec del
    locale (`text=True` a secas) revienta con `UnicodeDecodeError` en una consola cp1252 — justo
    donde antes daba su veredicto. `capture_output=True` a solas NO entra: devuelve bytes y no
    decodifica nada. Lo que enciende el modo texto es `text=` / `universal_newlines=` / `errors=`.
    Se reconoce la llamada por el nombre (`subprocess.run`, alias de import, `from subprocess import
    run`) y también por llevar `capture_output=`, que solo existe en `subprocess.run` — así entra el
    invocador indirecto (`runner(cmd, capture_output=True, text=True, …)` de `evals/run.py`).
    `[]` si el fichero no es Python parseable.
    """
    try:
        arbol = ast.parse(src)
    except (SyntaxError, ValueError):
        return []
    alias = {"subprocess"}
    directos = set()
    for n in ast.walk(arbol):
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name == "subprocess":
                    alias.add(a.asname or "subprocess")
        elif isinstance(n, ast.ImportFrom) and n.module == "subprocess":
            for a in n.names:
                directos.add(a.asname or a.name)
    fuera = []
    for n in ast.walk(arbol):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        es = ((isinstance(f, ast.Attribute) and f.attr in SUBPROCESS_FUNCS
               and isinstance(f.value, ast.Name) and f.value.id in alias)
              or (isinstance(f, ast.Name) and f.id in directos)
              or _kw(n, "capture_output") is not None)
        if not es:
            continue
        texto = (_kw_verdadero(_kw(n, "text")) or _kw_verdadero(_kw(n, "universal_newlines"))
                 or _kw(n, "errors") is not None
                 or (isinstance(f, ast.Attribute) and f.attr in ("getoutput", "getstatusoutput")))
        if texto and _kw(n, "encoding") is None:
            fuera.append(n.lineno)
    return sorted(set(fuera))
# --8<-- fin del criterio de consola COMPARTIDO


# Codificaciones que reproducen el entorno del bug (cp1252 = Windows español; ascii = el caso extremo).
ENCODINGS = ("cp1252", "ascii")


# --------------------------------------------------------------- descubrimiento (mismo criterio)

def versionados(root):
    """Los `.py` VERSIONADOS que son piezas del plugin (`es_pieza`), o `None` si no hay git.

    `-c core.quotepath=false` + `-z`: con el default (`core.quotepath=true`) git CITA las rutas no
    ASCII (`"scripts/a\\303\\261o.py"`) y nunca escapa los espacios, así que el
    `sorted(salida.split())` de antes perdía ficheros EN SILENCIO — medido (T-04) en un repo de
    prueba con `scripts/año.py` y `scripts/mi script.py`: descubiertos `[]`, suite verde.
    """
    r = subprocess.run(["git", "-c", "core.quotepath=false", "ls-files", "-z", "*.py"],
                       cwd=root, capture_output=True)
    if r.returncode != 0:
        return None
    rels = [x for x in r.stdout.decode("utf-8", "replace").split("\0") if x]
    return sorted(rel for rel in rels if es_pieza(rel))


def _no_ascii(path):
    with open(path, "rb") as f:
        return any(b > 127 for b in f.read())


def descubrir():
    """Las piezas versionadas que TIENEN que llevar el snippet, según `exige_snippet`.

    Dos motivos, no uno (T-05): escribir símbolos **o** leer de `sys.stdin`. El segundo no se ve en el
    fuente —`agent-kits/nemesis/tools/pick_asset.py` es ASCII pura y hacía `json.load(sys.stdin)`—,
    así que con el criterio de T-04 (solo no-ASCII en el fuente) quedaba invisible para el linter y
    para esta suite: 27 de las 28 piezas llevaban el snippet y la que faltaba era justo un lector.
    """
    rels = versionados(ROOT)
    if rels is None:
        pytest.skip("no es un checkout git: no se puede descubrir la lista de scripts")
    out = []
    for rel in rels:
        p = os.path.join(ROOT, rel)
        if not os.path.isfile(p):
            continue
        with open(p, "rb") as f:
            data = f.read()
        if exige_snippet(data, data.decode("utf-8", "replace")):
            out.append(rel)
    return out


SCRIPTS = descubrir()

# Piezas que llevan el snippet por LEER `stdin` y cuyo veredicto es ASCII legítimo. Se NOMBRAN una a
# una, con su motivo, en vez de dejar que un `skip` genérico las tape: la ausencia de símbolos en la
# salida es justo la degradación que `test_la_salida_sigue_siendo_utf8_no_interrogantes` vigila, así
# que la excepción tiene que ser explícita y estar medida (T-05). Ojo: mirar el fuente NO sirve para
# decidir esto — el propio comentario del snippet trae `í` y `—`, así que toda pieza con snippet tiene
# no-ASCII en el fuente. `test_los_exentos_de_simbolos_lo_estan_por_medicion` comprueba que la
# exención sigue siendo cierta ejecutando el modo declarado.
SIN_SIMBOLOS_EN_LA_SALIDA = {
    "agent-kits/nemesis/tools/pick_asset.py":
        "su veredicto es una URL (ASCII) o un exit 2 mudo; entra en SCRIPTS por leer el JSON de stdin",
}
SCRIPTS_CON_SIMBOLOS = [rel for rel in SCRIPTS if rel not in SIN_SIMBOLOS_EN_LA_SALIDA]

# Todas las piezas versionadas (con símbolos o sin ellos): el lado PADRE aplica a todas.
PIEZAS = versionados(ROOT) or []


# --------------------------------------------------------------- modos de arranque (los que SÍ imprimen)

# rel -> lista de modos. Cada modo: (etiqueta, args(taller) -> lista, exits permitidos, stdin|None).
# `--help` no sirve como modo salvo que imprima no-ASCII: lo que se prueba es la RUTA REAL de impresión.
# Los exits permitidos son los VEREDICTOS legítimos del script; un traceback se caza aparte (stderr).
def _modos():
    L = "docs/roadmap/2026-09-03-windows-console/tasks.md"      # este mismo ledger
    INI = "docs/roadmap/2026-09-03-windows-console"
    # Con emoji EN EL PAYLOAD a propósito: bajo cp1252 el `sys.stdin.read()` reventaba y el
    # `except` del guardrail convertía el UnicodeDecodeError en «se permite» (T-04, CRITICAL 1).
    deny = ('{"tool_name":"Write","tool_input":'
            '{"file_path":"docs/roadmap/2026-09-03-x/spec.md","content":"👍 ok"}}')
    # El JSON REAL de una release de GitHub: `body` trae las notas con emojis (🐛 = `F0 9F 90 9B`,
    # con el byte `0x90`; 👍 lleva `0x8D`) — ninguno existe en cp1252. `pick_asset.py` es ASCII pura
    # en el fuente, así que el criterio de T-04 no lo miraba: entra por LEER stdin (T-05).
    release = ('{"tag_name":"v1.0.0","body":"Arreglos 🐛 y mejoras 👍","assets":'
               '[{"name":"tool_linux_amd64.tar.gz","browser_download_url":"https://x/y"}]}')
    return {
        "agent-kits/nemesis/tools/pick_asset.py":
            [("release con emoji", lambda w: ["linux", "amd64"], (0,), release)],
        "agent-kits/qa/coverage-check.py":
            [("sin test-plan", lambda w: [L, os.path.join(w, "no-hay-test-plan.md")], (0, 1), None)],
        "agent-kits/qa/qa-gate.py":
            [("veredicto", lambda w: [os.path.join(w, "results.json")], (0, 1), None)],
        "agent-kits/shared/doctor.py":
            [("informe", lambda w: ["--root", "."], (0, 1), None),
             ("json", lambda w: ["--root", ".", "--json"], (0, 1), None)],
        "agent-kits/shared/guardrail-check.py":
            [("deny", lambda w: ["pre-tool", "--project-dir", "."], (0,), deny)],
        "agent-kits/shared/journal.py":
            [("draft", lambda w: ["draft", "--root", "."], (0,), None)],
        "agent-kits/shared/ledger-lint.py":
            [("ledger", lambda w: [L], (0, 1), None)],
        "agent-kits/shared/model-tier.py":
            [("--all", lambda w: ["--all"], (0,), None)],
        "agent-kits/shared/progress-report.py":
            [("line", lambda w: ["line", L], (0,), None)],
        "agent-kits/shared/scope-check.py":
            [("alcance", lambda w: [INI, "--base", "HEAD"], (0, 1), None)],
        "agent-kits/shared/skill-index.py":
            [("indice", lambda w: ["--no-cache"], (0,), None)],
        "agent-kits/shared/task-brief.py":
            [("brief", lambda w: [INI, "T-01"], (0,), None)],
        "agent-kits/shared/usage-meter.py":
            [("close", lambda w: ["close", "--artefacto", "x", "--state", os.path.join(w, "u.json")], (0,), None)],
        "evals/check.py":
            [("cobertura", lambda w: [], (0, 1), None)],
        "evals/run.py":
            [("--dry-run", lambda w: ["--dry-run"], (0,), None)],
        "scripts/export-skills.py":
            [("paquete", lambda w: ["--out", os.path.join(w, "pkg")], (0, 1), None),
             ("--check", lambda w: ["--check", os.path.join(w, "pkg")], (0, 1), None)],
        "scripts/lint_plugin.py":
            [("linter", lambda w: [], (0, 1), None)],
        "scripts/release.py":
            [("--check", lambda w: ["--check"], (0, 1), None)],
        "skills/adversarial-review/scripts/review-lens-select.py":
            [("lentes", lambda w: ["--files", "x.py"], (0,), None)],
        "skills/api-contract/scripts/openapi-lint.py":
            [("spec", lambda w: [os.path.join(w, "api.json")], (0, 1), None)],
        "skills/changelog-sync/scripts/changelog-sync.py":
            [("--check", lambda w: ["--check"], (0, 1), None)],
        "skills/code-health/scripts/code-health.py":
            [("informe", lambda w: [w], (0,), None)],
        "skills/confluence-publish/scripts/confluence-scope.py":
            [("--status", lambda w: ["--status", "--root", "."], (0, 1), None)],
        "skills/dependency-upgrade/scripts/deps-inventory.py":
            [("inventario", lambda w: [w, "--no-outdated"], (0,), None)],
        "skills/jira-sync/scripts/jira-flow.py":
            [("plan", lambda w: ["plan", "--task", "T-01", "--ledger", L,
                                 "--event", "implementado", "--actor", "implementer"], (0, 2), None)],
        "skills/jira-sync/scripts/worklog.py":
            [("plan sobre jornada", lambda w: ["plan", "--task", "T-01", "--issue", "CA-1",
                                               "--kind", "implementacion", "--ia-real", "9",
                                               "--state", os.path.join(w, "w.json")], (0,), None)],
        "skills/roadmap-dashboard/scripts/build_dashboard.py":
            [("json", lambda w: ["--root", "docs/roadmap", "--json"], (0,), None)],
        "skills/unit-tests/scripts/coverage-gate.py":
            # exit 2 = "no se detectó ningún stack soportado": es su error de USO, no un traceback, y
            # es la ruta barata (montar un proyecto con pytest real ejecutaría la suite entera).
            [("sin stack", lambda w: [w], (0, 1, 2), None)],
    }


MODOS = _modos()


@pytest.fixture(scope="module")
def taller(tmp_path_factory):
    """Espacio de trabajo con los fixtures mínimos que piden algunos modos. Nada se escribe en el repo."""
    import json
    w = tmp_path_factory.mktemp("consola")
    (w / "src").mkdir()
    (w / "src" / "a.py").write_text("def f():\n    return 1\n" * 3, encoding="utf-8")
    (w / "requirements.txt").write_text("requests==2.0.0\n", encoding="utf-8")
    (w / "api.json").write_text(json.dumps(
        {"openapi": "3.0.3", "info": {"title": "Demo", "version": "1.0.0"}, "paths": {}}), encoding="utf-8")
    (w / "results.json").write_text(json.dumps({"suites": [{"title": "s", "specs": [
        {"title": "E2E-01 algo", "ok": True, "tests": [{"results": [{"status": "passed"}]}]}]}]}),
        encoding="utf-8")
    return str(w)


_EJECUCIONES = {}


def _ejecutar(rel, args, stdin, encoding):
    """Lanza `rel` y MEMOIZA el resultado por `(rel, args, stdin, encoding)` (T-04, lente D).

    Los tests de las secciones 2 y 3 piden repetidamente el MISMO arranque: medido, 114 subprocesos
    de los que 56 eran repeticiones (58 claves distintas), 2,9 s de los 6,1 s del fichero. La
    repetición no aporta señal: comprobado que las 58 claves devuelven lo mismo las dos veces, salvo
    `usage-meter.py close`, que solo cambia el `"fin"` (marca de tiempo) — nada de lo que estos tests
    afirman (exit code, ausencia de traceback, bytes UTF-8 válidos) depende de eso. La caché vive lo
    que dura el módulo, así que cada `pytest` sigue ejecutando de verdad las 28 piezas.
    """
    clave = (rel, tuple(args), stdin, encoding)
    if clave not in _EJECUCIONES:
        env = dict(os.environ, PYTHONIOENCODING=encoding)
        env.pop("PYTHONWARNINGS", None)
        _EJECUCIONES[clave] = subprocess.run(
            [sys.executable, os.path.join(ROOT, rel), *args], cwd=ROOT, env=env,
            input=(stdin or "").encode("utf-8"), capture_output=True, timeout=120)
    return _EJECUCIONES[clave]


# --------------------------------------------------------------- 1. el snippet está en todos

@pytest.mark.parametrize("rel", SCRIPTS)
def test_todo_script_no_ascii_lleva_el_snippet(rel):
    """Regla de CONVENTIONS 8 / GOT-005: si imprimes símbolos, reconfiguras stdout/stderr al arrancar.

    Esta comprobación ESTÁTICA no es redundante con la ejecución: un script puede quedar protegido de
    rebote porque importa por ruta a otro que sí lleva el snippet (medido: `lint_plugin.py` sin snippet
    seguía saliendo 0 bajo cp1252 porque `_cargar_evals_check` ejecuta `evals/check.py`; borrando
    `evals/` —instalación parcial— volvía el `UnicodeEncodeError`). Cada script responde de lo suyo.
    """
    src = open(os.path.join(ROOT, rel), encoding="utf-8").read()
    assert CONSOLE_MARK in src, (
        f"{rel} tiene caracteres no ASCII y NO reconfigura la salida: en una consola cp1252 (o con la "
        f"salida a un pipe en Windows) el primer print revienta con UnicodeEncodeError. Copia el snippet "
        f"de scripts/lint_plugin.py tras el bloque de imports (4 líneas, LITERAL — los scripts son "
        f"standalone, no hay módulo común que importar).")


@pytest.mark.parametrize("rel", SCRIPTS)
def test_el_snippet_esta_a_nivel_de_modulo_y_antes_de_imprimir(rel):
    """No vale dentro de `main()`: hay scripts que imprimen desde funciones sueltas o al importarse.

    Con la MISMA comprobación estructural que el linter (`snippet_al_arrancar`), no con un `grep` de
    subcadena: medido (T-04) que la marca dentro de `main()`, o citada solo en un docstring, dejaba
    el aviso del linter en 0 mientras el script reventaba igual bajo cp1252.
    """
    src = open(os.path.join(ROOT, rel), encoding="utf-8").read()
    assert snippet_al_arrancar(src) is True, (
        f"{rel}: el snippet no protege el arranque — o está dentro de una función/clase, o hay una "
        f"sentencia de módulo antes que no es el docstring ni un import (el primer `print` o el "
        f"primer `stdin.read()` ya habrían reventado). CONVENTIONS regla 8, GOT-005.")


@pytest.mark.parametrize("rel", SCRIPTS)
def test_el_snippet_conserva_su_forma_literal(rel):
    """Se replica LITERAL en las 28: la misma forma en todas, sin variantes que se desincronicen."""
    lineas = open(os.path.join(ROOT, rel), encoding="utf-8").read().split("\n")
    i = next((n for n, l in enumerate(lineas) if CONSOLE_MARK in l), -1)
    assert i >= 0, f"{rel}: sin snippet (lo dice también test_todo_script_no_ascii_lleva_el_snippet)"
    assert lineas[i].startswith("    try:"), f"{rel}: el snippet no conserva su forma ({lineas[i]!r})"
    assert lineas[i - 1] == "for _s in (sys.stdin, sys.stdout, sys.stderr):", (
        f"{rel}: falta el bucle del snippet, o no cubre los tres streams (stdin entra en T-04)")


# --------------------------------------------------------------- 2. ejecución real bajo cp1252 / ascii

@pytest.mark.parametrize("encoding", ENCODINGS)
@pytest.mark.parametrize("rel", SCRIPTS)
def test_arranca_sin_reventar_en_consola_no_utf8(rel, encoding, taller):
    modos = MODOS.get(rel)
    assert modos, (
        f"{rel} imprime símbolos no ASCII pero no declara su modo de arranque en MODOS de "
        f"tests/test_console_encoding.py. Añade el modo MÁS BARATO que de verdad imprima (no `--help` si "
        f"su ayuda es ASCII) con los exit codes que son veredicto legítimo.")
    for etiqueta, args, exits, stdin in modos:
        r = _ejecutar(rel, args(taller), stdin, encoding)
        err = r.stderr.decode("utf-8", "replace")
        ctx = f"{rel} [{etiqueta}] con PYTHONIOENCODING={encoding}"
        assert "UnicodeEncodeError" not in err, f"{ctx}: reventó al imprimir\n{err[-1500:]}"
        assert "Traceback" not in err, f"{ctx}: traceback\n{err[-1500:]}"
        assert r.returncode in exits, f"{ctx}: exit {r.returncode} fuera de {exits}\n{err[-1500:]}"


@pytest.mark.parametrize("encoding", ENCODINGS)
@pytest.mark.parametrize("rel", SCRIPTS_CON_SIMBOLOS)
def test_la_salida_sigue_siendo_utf8_no_interrogantes(rel, encoding, taller):
    """`errors="replace"` es la red de seguridad, no el modo normal: al reconfigurar a UTF-8 los símbolos
    salen ÍNTEGROS (no como `?`). Se comprueba sobre los bytes reales del pipe.

    La ausencia de no-ASCII es un FALLO, no un motivo para saltarse el caso (T-05): es exactamente la
    degradación que este test dice detectar. Antes había un `pytest.skip` ahí, o sea que el único caso
    interesante era el único que no se comprobaba. Medido: los 27 modos de `SCRIPTS_CON_SIMBOLOS`
    (× 2 codificaciones = 54 combinaciones) emiten no-ASCII de verdad, así que el skip nunca se
    disparaba y solo podía taparlo. Los scripts que entran en `SCRIPTS` por LEER stdin y cuyo
    veredicto es ASCII legítimo (`pick_asset.py` imprime una URL) no están en esta lista.
    """
    etiqueta, args, _exits, stdin = MODOS[rel][0]
    r = _ejecutar(rel, args(taller), stdin, encoding)
    salida = r.stdout + r.stderr
    assert any(b > 127 for b in salida), (
        f"{rel} [{etiqueta}] con PYTHONIOENCODING={encoding}: la salida no trae NINGÚN byte no ASCII. "
        f"Este script tiene símbolos en el fuente y su modo declarado los imprime — que hayan "
        f"desaparecido significa o que la salida degradó a `?`/ASCII (justo lo que este test vigila), "
        f"o que el modo declarado en MODOS ya no pasa por la ruta que imprime. Arregla lo primero, o "
        f"cambia el modo por uno que sí imprima.\nstdout={r.stdout[:300]!r}\nstderr={r.stderr[:300]!r}")
    salida.decode("utf-8")   # UTF-8 válido: si hubiera degradado a `?` o a cp1252, esto no cuadraría


@pytest.mark.parametrize("encoding", ENCODINGS)
@pytest.mark.parametrize("rel", sorted(SIN_SIMBOLOS_EN_LA_SALIDA))
def test_los_exentos_de_simbolos_lo_estan_por_medicion(rel, encoding, taller):
    """La exención de `SIN_SIMBOLOS_EN_LA_SALIDA` se comprueba, no se cree.

    Si el script empieza a imprimir símbolos, este test se pone rojo y hay que sacarlo de la lista
    para que vuelva a vigilarlo el test de arriba. Así la excepción no puede pudrirse en silencio,
    que es justo lo que hacía el `pytest.skip` que sustituye.
    """
    assert rel in SCRIPTS, f"{rel} está exento pero ya no es una pieza que exija el snippet"
    _etiqueta, args, _exits, stdin = MODOS[rel][0]
    r = _ejecutar(rel, args(taller), stdin, encoding)
    salida = r.stdout + r.stderr
    assert not any(b > 127 for b in salida), (
        f"{rel} SÍ imprime no-ASCII con PYTHONIOENCODING={encoding}: sácalo de "
        f"SIN_SIMBOLOS_EN_LA_SALIDA para que se le exija salida UTF-8 íntegra\n{salida[:300]!r}")


# --------------------------------------------------------------- 3. el lado STDIN del mismo bug

@pytest.mark.parametrize("encoding", ENCODINGS)
def test_el_payload_con_emoji_por_stdin_no_apaga_el_guardrail(encoding, taller):
    """CRITICAL 1 (T-04): el hook leía el payload con `sys.stdin.read()`, que usa el codec del locale.

    Bajo `cp1252` un payload con un emoji (o un `\u2014`) lanzaba `UnicodeDecodeError`, y el
    `except Exception` del guardrail —que existe para «un guardrail roto nunca bloquea»— lo
    convertía en un **allow silencioso**: exit 0, stdout vacío. Es decir, en el Windows español
    del bug original bastaba con que el contenido llevara un emoji para que el guardrail de
    alcance y el de rama dejaran de denegar. El snippet cubre `sys.stdin` por eso.
    """
    rel = "agent-kits/shared/guardrail-check.py"
    _etiqueta, args, _exits, stdin = MODOS[rel][0]
    assert "\U0001F44D" in stdin, "el payload del modo `deny` debe llevar el emoji del bug"
    r = _ejecutar(rel, tuple(args(taller)), stdin, encoding)
    out = r.stdout.decode("utf-8", "replace")
    err = r.stderr.decode("utf-8", "replace")
    assert "UnicodeDecodeError" not in err, f"stdin sin reconfigurar bajo {encoding}:\n{err[-800:]}"
    assert '"permissionDecision": "deny"' in out, (
        f"el guardrail NO denegó con PYTHONIOENCODING={encoding} y un payload con emoji "
        f"(allow silencioso — CRITICAL 1)\nstdout={out!r}\nstderr={err[-800:]}")


@pytest.mark.parametrize("encoding", ENCODINGS)
def test_el_json_de_release_con_emoji_no_se_lee_como_falta_de_binario(encoding, taller):
    """T-05: la 28.ª pieza era ASCII pura y leía `stdin` — invisible para el criterio de T-04.

    `pick_asset.py` hace `json.load(sys.stdin)` sobre el JSON de una release de GitHub, cuyo `body`
    trae las notas con emojis. Sin el snippet, bajo cp1252 salía `bad json: 'charmap' codec can't
    decode byte 0x81 …` con exit 1 — y el síntoma es EL MISMO del bug original, un crash disfrazado
    de veredicto: `install-tools.sh` manda ese stderr al log, ve la URL vacía y anuncia
    `[!!] <tool>: no release asset for <os>/<arch>` con `record … failed no-asset`. O sea, un fallo
    de codificación presentado como «este proyecto no publica binario para tu plataforma».
    """
    rel = "agent-kits/nemesis/tools/pick_asset.py"
    _etiqueta, args, _exits, stdin = MODOS[rel][0]
    assert "\U0001F41B" in stdin, "el payload debe traer el emoji de las notas de release"
    r = _ejecutar(rel, tuple(args(taller)), stdin, encoding)
    out = r.stdout.decode("utf-8", "replace")
    err = r.stderr.decode("utf-8", "replace")
    assert "bad json" not in err, f"stdin sin reconfigurar bajo {encoding}:\n{err[-500:]}"
    assert r.returncode == 0, f"exit {r.returncode} (2 = «no hay asset», el falso veredicto)\n{err[-500:]}"
    assert out.strip() == "https://x/y", f"no eligió el asset: {out!r}"


def test_la_memoizacion_no_relanza_el_mismo_arranque(taller):
    """Lente D (T-04): las secciones 2 y 3 repetían 56 de 114 subprocesos, 2,9 s de los 6,1 s.

    Se afirma la identidad del objeto, no solo la igualdad: si vuelve el MISMO `CompletedProcess`,
    no ha habido segundo `subprocess.run`. Una clave distinta sí lanza de nuevo.
    """
    rel = "agent-kits/shared/ledger-lint.py"
    _e, args, _x, stdin = MODOS[rel][0]
    a = _ejecutar(rel, tuple(args(taller)), stdin, "cp1252")
    b = _ejecutar(rel, tuple(args(taller)), stdin, "cp1252")
    c = _ejecutar(rel, tuple(args(taller)), stdin, "ascii")
    assert a is b, "misma clave: debería servirse de la caché, no relanzar"
    assert a is not c, "otra codificación es otra clave: tiene que ejecutarse de verdad"


# El `-c` que envuelve a un script REAL para reproducir los tres `sys.stdin` que no admiten
# `reconfigure`. Es lo que hace un embebedor de verdad: `pythonw` deja `sys.stdin` en `None`, un
# arranque que ya ha consumido parte del stream lo deja «ya leído», y quien lo sustituye por un
# objeto propio (pytest con `capsys`, un runner) lo deja sin el método.
_ENVOLTORIO = """
import sys, runpy
caso = sys.argv[1]
if caso == "leido":
    sys.stdin.readline()          # lectura PARCIAL: `reconfigure` lanza UnsupportedOperation
elif caso == "none":
    sys.stdin = None              # pythonw
elif caso == "sin_metodo":
    class SinReconfigure:
        def read(self, *a): return ""
        def readline(self, *a): return ""
    sys.stdin = SinReconfigure()
sys.argv = sys.argv[2:]
runpy.run_path(sys.argv[0], run_name="__main__")
"""
_CASOS_STREAM = ("leido", "none", "sin_metodo")
# El snippet tal cual viaja a las 28 piezas, y el mismo sin su `except` (el mutante).
_SNIPPET_CON_EXCEPT = ('for _s in (sys.stdin, sys.stdout, sys.stderr):\n'
                       '    try: _s.reconfigure(encoding="utf-8", errors="replace")\n'
                       '    except Exception: pass')
_SNIPPET_SIN_EXCEPT = ('for _s in (sys.stdin, sys.stdout, sys.stderr):\n'
                       '    _s.reconfigure(encoding="utf-8", errors="replace")  #')


def _arranque_envuelto(script, caso):
    """Arranca `script` con `sys.stdin` en el estado `caso`, con datos de verdad en el pipe."""
    return subprocess.run(
        [sys.executable, "-c", _ENVOLTORIO, caso, script,
         "docs/roadmap/2026-09-03-windows-console/tasks.md"],
        cwd=ROOT, input=b"x\ny\n", capture_output=True, timeout=120,
        env=dict(os.environ, PYTHONIOENCODING="cp1252"))


@pytest.mark.parametrize("caso", _CASOS_STREAM)
def test_el_except_del_snippet_aguanta_los_tres_streams_imposibles(caso):
    """El `except` del snippet, MEDIDO sobre un script REAL del repo — no sobre objetos de mentira.

    Antes este test no tenía una sola aserción: hacía `try: stream.reconfigure(...) except: pass`
    sobre tres dobles y no tocaba ningún script, así que pasaba igual si el snippet no tuviera
    `except` o directamente no existiera. Ahora arranca `ledger-lint.py` (standalone, solo stdlib)
    con `sys.stdin` en cada uno de los tres estados que NO admiten `reconfigure` y exige su veredicto
    de siempre: exit 0 y ni un traceback. `test_el_mismo_arranque_sin_except_revienta` es su mutación.
    """
    r = _arranque_envuelto(os.path.join(ROOT, "agent-kits/shared/ledger-lint.py"), caso)
    err = r.stderr.decode("utf-8", "replace")
    assert "Traceback" not in err, f"[{caso}] el arranque reventó:\n{err[-800:]}"
    assert r.returncode == 0, f"[{caso}] exit {r.returncode}, esperaba 0\n{err[-800:]}"
    assert "ledger-lint:" in r.stdout.decode("utf-8", "replace"), (
        f"[{caso}] el script no llegó a dar su veredicto\nstdout={r.stdout[:300]!r}")


@pytest.mark.parametrize("caso", _CASOS_STREAM)
def test_el_mismo_arranque_sin_except_revienta(caso, tmp_path):
    """La mutación que demuestra que el test de arriba PUEDE fallar: sin el `except`, los tres caen.

    Se muta una COPIA en `tmp_path`, nunca el repo. Si algún día el snippet dejara de necesitar el
    `except`, este test se pondría rojo y habría que volver a medir en vez de creerlo.
    """
    src = open(os.path.join(ROOT, "agent-kits/shared/ledger-lint.py"), encoding="utf-8").read()
    assert _SNIPPET_CON_EXCEPT in src, "el snippet ha cambiado de forma: re-mide antes de tocar esto"
    mutante = tmp_path / "ledger-lint-sin-except.py"
    mutante.write_text(src.replace(_SNIPPET_CON_EXCEPT, _SNIPPET_SIN_EXCEPT, 1), encoding="utf-8")

    r = _arranque_envuelto(str(mutante), caso)
    err = r.stderr.decode("utf-8", "replace")
    assert r.returncode != 0 and "Traceback" in err, (
        f"[{caso}] el mutante SIN except debería reventar y no lo hizo (exit {r.returncode}) — "
        f"si es así, el `except` ya no cubre este caso y el test de arriba no mide nada\n{err[-800:]}")
    esperado = {"leido": "UnsupportedOperation", "none": "AttributeError",
                "sin_metodo": "AttributeError"}[caso]
    assert esperado in err, f"[{caso}] esperaba {esperado} en el traceback\n{err[-800:]}"


# --------------------------------------------------------------- 3. el descubridor protege a futuro

def test_el_descubridor_encuentra_los_scripts_conocidos():
    assert len(SCRIPTS) >= 28, f"esperaba ≥ 28 piezas que exijan snippet, encontré {len(SCRIPTS)}: {SCRIPTS}"
    for esperado in ("scripts/lint_plugin.py", "scripts/release.py", "agent-kits/shared/doctor.py",
                     "skills/changelog-sync/scripts/changelog-sync.py",
                     # ASCII pura en el fuente: entra por LEER stdin, no por escribir símbolos (T-05).
                     "agent-kits/nemesis/tools/pick_asset.py"):
        assert esperado in SCRIPTS, f"{esperado} debería estar en la lista descubierta"
    # `pick_asset.py` entra por el SEGUNDO motivo: lee `stdin`. Su cuerpo es ASCII pura (los únicos
    # no-ASCII del fichero son los del comentario del propio snippet), así que con el criterio de
    # T-04 —solo no-ASCII en el fuente— era invisible: era la 28.ª pieza y la única sin snippet.
    lector = os.path.join(ROOT, "agent-kits/nemesis/tools/pick_asset.py")
    src = open(lector, encoding="utf-8").read()
    assert lee_stdin(src), "pick_asset.py debe seguir entrando por leer sys.stdin"
    cuerpo = "\n".join(l for l in src.split("\n") if CONSOLE_MARK not in l and "GOT-005" not in l
                       and not l.startswith("    except Exception: pass"))
    assert not any(ord(c) > 127 for c in cuerpo), (
        "el cuerpo de pick_asset.py debe seguir siendo ASCII puro: es lo que hace de este caso la "
        "prueba de que el criterio no puede depender del fuente")
    # El criterio no tiene lista de excluidos: `es_pieza` saca por FORMA (basename `test_*`, o
    # cualquier segmento `fixtures`), así que un fixture nuevo bajo otro `…/fixtures/` también queda
    # fuera — antes solo estaba fuera la ruta hardcodeada `evals/fixtures/project/src/app.py` (T-04).
    assert "evals/fixtures/project/src/app.py" not in SCRIPTS, "el fixture del proyecto ajeno queda fuera"
    assert not [s for s in SCRIPTS if not es_pieza(s)], "el descubridor y `es_pieza` no coinciden"
    assert not es_pieza("skills/x/fixtures/consumidor/app.py"), "cualquier `fixtures/` queda fuera"
    assert not es_pieza("tests/test_algo.py") and es_pieza("scripts/algo.py")


def test_el_descubridor_no_pierde_rutas_con_espacios_ni_no_ascii(tmp_path):
    """T-04: `git ls-files` CITA las rutas no ASCII y no escapa los espacios.

    Con el `sorted(salida.split())` de antes, `scripts/año.py` salía como
    `"scripts/a\\303\\261o.py"` (entre comillas y con los bytes escapados) y `scripts/mi script.py`
    se troceaba en `scripts/mi` + `script.py`: ninguno existía en disco, así que se caían del
    descubrimiento EN SILENCIO. El umbral `len(SCRIPTS) >= 27` no lo detectaba porque se seguía
    cumpliendo. El remedio es el que ya usaba `review-lens-select.py`: `-c core.quotepath=false`,
    más `-z` y partir por `\\0`.
    """
    if subprocess.run(["git", "--version"], capture_output=True).returncode != 0:
        pytest.skip("sin git")
    (tmp_path / "scripts").mkdir()
    for nombre in ("año.py", "mi script.py", "normal.py"):
        (tmp_path / "scripts" / nombre).write_text('print("✅")\n', encoding="utf-8")
    entorno = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    for args in (["init", "-q"], ["add", "-A"], ["commit", "-qm", "x"]):
        subprocess.run(["git", *args], cwd=tmp_path, capture_output=True, env=entorno, check=True)

    hallados = versionados(str(tmp_path))
    assert hallados == ["scripts/año.py", "scripts/mi script.py", "scripts/normal.py"], hallados


# --------------------------------------------------------------- 5. el lado PADRE (T-04)

@pytest.mark.parametrize("rel", PIEZAS)
def test_ninguna_pieza_captura_un_subproceso_sin_encoding(rel):
    """La otra mitad de GOT-005: quien LEE a un hijo tiene que decodificarlo como UTF-8.

    Desde T-01 los hijos escriben UTF-8 siempre. Un padre con `text=True` a secas usa el codec del
    locale y revienta con `UnicodeDecodeError` en consola cp1252 — así reventó `task-brief.py` al
    leer a `ledger-lint.py`, justo en el despacho de tarea de `/dev-cycle` (T-04 CRITICAL 2).
    """
    src = open(os.path.join(ROOT, rel), encoding="utf-8").read()
    lineas = subprocess_sin_encoding(src)
    assert not lineas, (
        f"{rel}: captura un subproceso en modo texto SIN `encoding=` en la(s) línea(s) "
        f"{', '.join(str(n) for n in lineas)}. Añade `encoding=\"utf-8\", errors=\"replace\"` — los "
        f"scripts del plugin escriben UTF-8 siempre (CONVENTIONS regla 8, GOT-005 lado padre).")


def test_las_suites_tambien_decodifican_a_sus_hijos_como_utf8():
    """Las suites quedan FUERA de `es_pieza` (no imprimen a la consola de nadie), pero sí lanzan los
    scripts y leen su salida: un desarrollador en Windows que ejecute la suite se comería el mismo
    `UnicodeDecodeError`. El linter no las mira —no son piezas del plugin— así que las vigila este
    test, que solo vive en el repo y no viaja en el paquete portable."""
    rels = versionados(ROOT)
    if rels is None:
        pytest.skip("no es un checkout git")
    r = subprocess.run(["git", "-c", "core.quotepath=false", "ls-files", "-z", "*.py"],
                       cwd=ROOT, capture_output=True)
    suites = [x for x in r.stdout.decode("utf-8", "replace").split("\0")
              if x and not es_pieza(x) and os.path.basename(x).startswith("test_")]
    assert suites, "esperaba encontrar suites versionadas"
    malas = {rel: subprocess_sin_encoding(open(os.path.join(ROOT, rel), encoding="utf-8").read())
             for rel in suites}
    malas = {k: v for k, v in malas.items() if v}
    assert not malas, ("suites que capturan un subproceso en modo texto sin `encoding=`: "
                       + "; ".join(f"{k}:{v}" for k, v in sorted(malas.items())))


# --------------------------------------------------------------- 6. linter y suite, un solo criterio

def _linter():
    """`scripts/lint_plugin.py` importado POR RUTA (módulo sin efectos secundarios al importar)."""
    import importlib.util
    ruta = os.path.join(ROOT, "scripts", "lint_plugin.py")
    spec = importlib.util.spec_from_file_location("lint_plugin_para_tests", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _bloque_compartido(ruta):
    """El texto entre los dos marcadores `--8<--` del fichero."""
    src = open(ruta, encoding="utf-8").read()
    ini = src.index("# --8<-- criterio de consola COMPARTIDO")
    fin = src.index("# --8<-- fin del criterio de consola COMPARTIDO")
    return src[ini:fin]


def test_linter_y_suite_replican_el_mismo_bloque():
    """`docs/CONVENTIONS.md` regla 8 dice que el criterio es el MISMO: aquí se comprueba, no se cree.

    Se replica en vez de importarse por el mismo contrato que el snippet (los scripts son standalone
    y el paquete portable los copia sueltos), así que lo que garantiza la identidad es este test.
    """
    a = _bloque_compartido(os.path.join(ROOT, "scripts", "lint_plugin.py"))
    b = _bloque_compartido(os.path.abspath(__file__))
    assert a == b, ("el bloque compartido ha divergido entre scripts/lint_plugin.py y "
                    "tests/test_console_encoding.py — cópialo LITERAL de uno al otro")


def _veredicto_del_linter(lp, root):
    """Los ficheros que el linter señala en `root` (mira el DISCO, con `os.walk`)."""
    lineas = lp.lint_console_encoding(root) + lp.lint_subprocess_encoding(root)
    return {ln.split("`")[1] for ln in lineas}


def _veredicto_de_la_suite(root, rels):
    """Los ficheros que la suite señala de entre `rels` (los VERSIONADOS, con `git ls-files`)."""
    señalados = set()
    for rel in rels:
        with open(os.path.join(root, rel), "rb") as f:
            data = f.read()
        src = data.decode("utf-8", "replace")
        if exige_snippet(data, src) and snippet_al_arrancar(src) is not True:
            señalados.add(rel)
        if subprocess_sin_encoding(src):
            señalados.add(rel)
    return señalados


def test_linter_y_suite_dan_el_mismo_veredicto_sobre_el_arbol_actual():
    """Mismo criterio ⇒ mismos ficheros señalados. Sobre el repo de verdad: los dos, ninguno.

    Se compara SOLO sobre lo versionado (T-05). Las dos mitades no miran el mismo sitio a propósito
    —el linter el disco, la suite `git ls-files`—, así que sin este filtro cualquier `.py` que un
    desarrollador tuviera sin añadir en su árbol de trabajo rompía la igualdad y el mensaje («el
    criterio ha divergido») lo mandaba a buscar donde no había nada. Medido: un
    `scripts/borrador_local.py` con símbolos y sin `git add` daba
    `AssertionError: linter: ['scripts/borrador_local.py'] · suite: []`. En CI nunca se veía —el
    checkout es limpio—: se lo comía solo quien trabaja en local.
    """
    lp = _linter()
    del_linter = _veredicto_del_linter(lp, ROOT)
    sin_versionar = del_linter - set(PIEZAS)     # borradores del árbol de trabajo: no son del commit
    del_linter -= sin_versionar
    de_la_suite = _veredicto_de_la_suite(ROOT, PIEZAS)
    aviso = (f" · (fuera de la comparación por no estar versionados: {sorted(sin_versionar)})"
             if sin_versionar else "")
    assert del_linter == de_la_suite == set(), (
        f"linter: {sorted(del_linter)} · suite: {sorted(de_la_suite)}{aviso}")


def test_el_veredicto_compartido_ignora_lo_no_versionado_pero_no_una_divergencia(tmp_path):
    """Las dos mitades del arreglo de T-05, sobre un repo git de verdad montado aquí.

    (a) un `.py` SIN versionar con símbolos ya NO pone rojo la comparación —es lo que rompía el
        árbol de trabajo del desarrollador—, y (b) una divergencia REAL sí la pone: ni un infractor
        versionado ni un criterio que deje de coincidir pasan desapercibidos.
    """
    if subprocess.run(["git", "--version"], capture_output=True).returncode != 0:
        pytest.skip("sin git")
    lp = _linter()
    (tmp_path / "scripts").mkdir()
    bueno = ('import sys\nfor _s in (sys.stdin, sys.stdout, sys.stderr):\n'
             '    try: _s.reconfigure(encoding="utf-8", errors="replace")\n'
             '    except Exception: pass\nprint("✅")\n')
    (tmp_path / "scripts" / "bien.py").write_text(bueno, encoding="utf-8")
    entorno = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    for args in (["init", "-q"], ["add", "-A"], ["commit", "-qm", "x"]):
        subprocess.run(["git", *args], cwd=tmp_path, capture_output=True, env=entorno, check=True)

    # (a) borrador SIN versionar, con símbolos y sin snippet: el linter lo ve en disco, la suite no.
    (tmp_path / "scripts" / "borrador_local.py").write_text('print("⚠️ borrador")\n', encoding="utf-8")
    versionadas = versionados(str(tmp_path))
    assert "scripts/borrador_local.py" not in versionadas, "el borrador no debe estar versionado"
    del_linter = _veredicto_del_linter(lp, str(tmp_path))
    assert del_linter == {"scripts/borrador_local.py"}, del_linter
    sin_versionar = del_linter - set(versionadas)
    assert del_linter - sin_versionar == _veredicto_de_la_suite(str(tmp_path), versionadas) == set(), (
        "un .py sin versionar no puede romper la igualdad: el linter mira el disco y la suite git")

    # (b) divergencia REAL: el mismo infractor, esta vez VERSIONADO. No se puede filtrar como
    # «no está en el commit», así que las dos mitades lo señalan y la igualdad con set() se rompe.
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, capture_output=True, env=entorno, check=True)
    subprocess.run(["git", "commit", "-qm", "y"], cwd=tmp_path, capture_output=True, env=entorno, check=True)
    versionadas = versionados(str(tmp_path))
    del_linter = _veredicto_del_linter(lp, str(tmp_path))
    de_la_suite = _veredicto_de_la_suite(str(tmp_path), versionadas)
    assert del_linter - (del_linter - set(versionadas)) == {"scripts/borrador_local.py"}
    assert de_la_suite == {"scripts/borrador_local.py"}, de_la_suite

    # (c) divergencia de CRITERIO: si una de las mitades dejara de mirar un fichero que la otra sí
    # mira, los conjuntos difieren — que es exactamente lo que este par de tests existe para cazar.
    assert _veredicto_de_la_suite(str(tmp_path), []) != del_linter


def test_linter_y_suite_dan_el_mismo_veredicto_sobre_un_arbol_con_infractores(tmp_path):
    """El acuerdo con el árbol limpio es trivial: aquí se comprueba con infractores de cada clase."""
    lp = _linter()
    casos = {
        # (ruta, contenido, ¿debería señalarse?)
        "scripts/dentro_de_main.py": ('import sys\nprint("⚠️  módulo")\n\n\ndef main():\n'
                                      '    for _s in (sys.stdin, sys.stdout, sys.stderr):\n'
                                      '        try: _s.reconfigure(encoding="utf-8", errors="replace")\n'
                                      '        except Exception: pass\n', True),
        "scripts/solo_docstring.py": ('"""Debería llamar a reconfigure(encoding="utf-8", '
                                      'errors="replace") y no lo hace."""\nprint("⚠️ ")\n', True),
        "scripts/padre_sin_encoding.py": ('import subprocess\nprint(subprocess.run(["ls"], '
                                          'capture_output=True, text=True).stdout)\n', True),
        # ASCII pura, pero LEE stdin: entra por el segundo motivo del criterio (T-05).
        "scripts/lector_ascii.py": ('import json, sys\nprint(json.load(sys.stdin)["x"])\n', True),
        "scripts/lector_ascii_bien.py": ('import json, sys\n'
                                         'for _s in (sys.stdin, sys.stdout, sys.stderr):\n'
                                         '    try: _s.reconfigure(encoding="utf-8", errors="replace")\n'
                                         '    except Exception: pass\n'
                                         'print(json.load(sys.stdin)["x"])\n', False),
        "scripts/bien.py": ('import sys\nfor _s in (sys.stdin, sys.stdout, sys.stderr):\n'
                            '    try: _s.reconfigure(encoding="utf-8", errors="replace")\n'
                            '    except Exception: pass\nprint("✅")\n', False),
        # ASCII pura y sin stdin: fuera del criterio — no se le avisa de nada.
        "scripts/solo_ascii.py": ('print("plain")\n', False),
        # `sys.stdin` solo citado en un comentario y en una cadena (fichero ASCII puro): `ast` no lo
        # cuenta como lectura, que es la diferencia entre el criterio de T-05 y un `grep`.
        "scripts/menciona_stdin.py": ('# algun dia leera de sys.stdin\nprint("sys.stdin")\n', False),
        "scripts/padre_bien.py": ('import subprocess\nprint(subprocess.run(["ls"], '
                                  'capture_output=True, text=True, encoding="utf-8", '
                                  'errors="replace").stdout)\n', False),
        # fuera del criterio: suite y fixture del consumidor, con las dos infracciones a la vez
        "scripts/test_infractor.py": ('import subprocess\nprint("⚠️ ", subprocess.run(["ls"], '
                                      'capture_output=True, text=True).stdout)\n', False),
        "evals/fixtures/proj/app.py": ('import subprocess\nprint("⚠️ ", subprocess.run(["ls"], '
                                       'capture_output=True, text=True).stdout)\n', False),
    }
    for rel, (contenido, _esperado) in casos.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(contenido, encoding="utf-8")

    esperado = {rel for rel, (_c, malo) in casos.items() if malo}
    del_linter = _veredicto_del_linter(lp, str(tmp_path))
    de_la_suite = _veredicto_de_la_suite(str(tmp_path), [r for r in casos if es_pieza(r)])
    assert del_linter == esperado, f"linter: {sorted(del_linter)} ≠ esperado {sorted(esperado)}"
    assert de_la_suite == esperado, f"suite: {sorted(de_la_suite)} ≠ esperado {sorted(esperado)}"


def test_un_script_nuevo_con_simbolos_y_sin_snippet_seria_cazado(tmp_path):
    """La regla en sí, sin depender de git: fichero con símbolos y sin la marca → no pasa el filtro."""
    nuevo = tmp_path / "nuevo.py"
    nuevo.write_text('print("✅ hola")\n', encoding="utf-8")
    assert _no_ascii(str(nuevo)) and CONSOLE_MARK not in nuevo.read_text(encoding="utf-8")
    nuevo.write_text('import sys\nfor _s in (sys.stdin, sys.stdout, sys.stderr):\n'
                     '    try: _s.reconfigure(encoding="utf-8", errors="replace")\n'
                     '    except Exception: pass\nprint("✅ hola")\n', encoding="utf-8")
    assert CONSOLE_MARK in nuevo.read_text(encoding="utf-8")
    r = subprocess.run([sys.executable, str(nuevo)], capture_output=True,
                       env=dict(os.environ, PYTHONIOENCODING="cp1252"))
    assert r.returncode == 0 and "✅" in r.stdout.decode("utf-8")


def test_pytest_capsys_no_rompe_el_snippet(capsys):
    """El `except` cubre los streams que pytest sustituye (o cualquiera sin `reconfigure`)."""
    class SinReconfigure:
        def write(self, s):
            return len(s)

    for stream in (sys.stdin, sys.stdout, sys.stderr, SinReconfigure(), None):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:   # noqa: BLE001 — exactamente lo que hace el snippet
            pass
    print("✅ el snippet no rompe bajo captura")
    assert "✅" in capsys.readouterr().out


# --------------------------------------------------------------- 7. los `python3 -c` de los .sh (T-05)

# Un python en línea dentro de un `.sh` (`-c` o heredoc) es un script del plugin sin fichero donde
# pegar el snippet, así que la regla se cumple con la variable de entorno equivalente, delante del
# comando. La regla es UNIFORME —todo python en línea la lleva—, no «el que lee stdin o imprime
# símbolos»: para decidir eso habría que parsear el programa, y el programa se escapa de cuatro
# formas triviales (comillas dobles, heredoc, `python` sin el `3`, e interpolación de shell que parte
# la cadena). Medido en la revisión, intento 3: las cuatro pasaban verdes sin señal. Poner la
# variable donde no hace falta cuesta cero; no ponerla donde hace falta es el bug de este gotcha.
PY_EN_LINEA = re.compile(
    r"(?P<env>(?:[A-Za-z_][A-Za-z0-9_]*=\S*[ \t]+)*)"      # asignaciones pegadas al comando
    r"(?P<py>python3|python|\"\$\{?\w*PY\w*\}?\"|\$\{?\w*PY\w*\}?)"   # python3 · python · "$PY"
    r"[ \t]+(?:-\S*[ \t]+)*(?P<modo>-c\b|<<)")           # -c '…' · -c "…" · <<'EOF'
ENV_ESPERADA = "PYTHONIOENCODING=utf-8:replace"


def _shell_versionados():
    r = subprocess.run(["git", "-c", "core.quotepath=false", "ls-files", "-z", "*.sh"],
                       cwd=ROOT, capture_output=True)
    if r.returncode != 0:
        return None
    return sorted(x for x in r.stdout.decode("utf-8", "replace").split("\0") if x)


def test_los_python_en_linea_de_los_hooks_tambien_reconfiguran():
    """La MISMA clase de bug, en shell: un `python3 -c` que lee stdin o imprime símbolos (T-05).

    `hooks/` y `statusline/` extraen el payload del hook y componen su JSON con `python3 -c` en
    línea. Ahí no hay fichero donde pegar el snippet, así que la regla se cumple con la variable
    equivalente delante del comando. Sin ella, bajo cp1252, el programa revienta con
    `UnicodeDecodeError` en cuanto el texto trae un byte que ese codec no define —`❌` (`E2 9D 8C`,
    `0x9D`), `⚠️` (con el selector de variación `EF B8 8F`, `0x8F`), `👍` (`0x8D`)— y el
    `2>/dev/null || true` con el que el hook degrada se lo traga: el usuario deja de ver la línea de
    progreso y nadie se entera. Medido antes/después en `progress-line.sh`: stdout vacío → el JSON
    con la línea íntegra. Ojo, NO es mojibake: los bytes que cp1252 sí define (`📋`, `·`) hacen
    ida y vuelta idénticos; el fallo es el crash silencioso, no una salida sucia.

    Este es un criterio de la SUITE, no del linter: el bloque compartido juzga `.py`, y meter un
    parser de shell en `lint_plugin.py` le haría opinar sobre los hooks de cualquier plugin
    consumidor. Aquí se vigilan los del repo, que son los que tienen síntoma medido.
    """
    shells = _shell_versionados()
    if shells is None:
        pytest.skip("no es un checkout git")
    assert shells, "esperaba encontrar .sh versionados"
    malos = []
    for rel in shells:
        texto = open(os.path.join(ROOT, rel), encoding="utf-8").read()
        for m in PY_EN_LINEA.finditer(texto):
            if ENV_ESPERADA not in (m.group("env") or ""):
                linea = texto[:m.start()].count("\n") + 1
                malos.append(f"{rel}:{linea}")
    assert not malos, (
        f"python en línea SIN `{ENV_ESPERADA}` delante: "
        f"{', '.join(malos)}. En cp1252 revienta con UnicodeDecodeError y el `2>/dev/null || true` "
        f"del hook lo tira en silencio (CONVENTIONS regla 8, GOT-005).")


# Las cuatro formas con las que un python en línea se escapaba del criterio anterior, más las que
# ya se vigilaban. Cada entrada es (fragmento de shell, ¿es una invocación de python en línea?).
FORMAS_DE_PYTHON_EN_LINEA = [
    ("""printf '%s' "$X" | python3 -c 'import sys; print(sys.stdin.read())'""", True),
    ("""printf '%s' "$X" | python3 -c "import sys; print(sys.stdin.read())" """, True),
    ("python3 <<'PYEOF'\nimport sys\nprint(sys.stdin.read())\nPYEOF", True),
    ("""printf '%s' "$X" | python -c 'import sys; print(sys.stdin.read())'""", True),
    ("""printf '%s' "$X" | "$PY" -c 'import sys; print(sys.stdin.read())'""", True),
    ("python3 - <<'PYEOF'\nimport sys\nPYEOF", True),
    ("command -v python3 >/dev/null 2>&1 || exit 0", False),
    ("for c in python3 python; do :; done", False),
    ("""out="$(python3 "$SHARED/progress-report.py" session)" """, False),
]


@pytest.mark.parametrize("fragmento,es_invocacion", FORMAS_DE_PYTHON_EN_LINEA)
def test_el_detector_de_python_en_linea_no_se_escapa_por_la_forma_de_citar(fragmento, es_invocacion):
    """Un criterio que solo reconoce `python3 -c '…'` deja pasar cuatro formas triviales (T-05).

    Medido en la revisión (intento 3): con comillas dobles, con heredoc, con `python` sin el `3` y a
    través de una variable (`"$PY"`, que es como elige intérprete `install-tools.sh`), el
    guardarraíl anterior daba verde sin señal alguna — el hook nuevo simplemente no se vigilaba.
    Este test fija la FORMA de la invocación, no el programa: por eso la regla pasó a ser uniforme.
    """
    hallazgos = list(PY_EN_LINEA.finditer(fragmento))
    assert bool(hallazgos) is es_invocacion, (
        f"{'esperaba detectar' if es_invocacion else 'NO esperaba detectar'} "
        f"un python en línea en: {fragmento!r}")
    if es_invocacion:      # y sin la variable delante, la regla lo marca
        assert ENV_ESPERADA not in (hallazgos[0].group("env") or "")


def test_todo_python_en_linea_del_repo_lleva_la_variable_incluido_el_que_no_la_necesitaba():
    """La regla es uniforme: el de `session-journal.sh` lee un FICHERO con su `encoding=` e imprime
    `0`/`1`, así que ahí la variable no arregla nada — pero cuesta cero y evita tener que decidir,
    por cada python en línea nuevo, si su programa lee stdin. Decidirlo exige parsear el programa, y
    el programa se escapa por la forma de citar (ver el test de arriba)."""
    sitios = []
    for rel in _shell_versionados() or []:
        texto = open(os.path.join(ROOT, rel), encoding="utf-8").read()
        sitios += [(rel, ENV_ESPERADA in (m.group("env") or ""))
                   for m in PY_EN_LINEA.finditer(texto)]
    assert len(sitios) == 8, f"esperaba 8 python en línea versionados, hay {len(sitios)}"
    assert all(ok for _, ok in sitios), f"sin la variable: {[r for r, ok in sitios if not ok]}"


# El snippet nombra `sys.stdin` en su `iter`, así que hay que excluirlo para que el criterio no sea
# circular. Excluir de MÁS es peor: la revisión (intento 3) midió que excluir la sentencia entera
# —o cualquier ancestro— apagaba la detección en todo el cuerpo de la función que alojase el
# snippet, justo el anti-patrón «snippet dentro de `main()`» que el linter existe para cazar.
CASOS_LEE_STDIN = [
    ("solo el snippet, sin leer nada", False, '''import sys
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
print("hola")
'''),
    ("snippet MAL colocado dentro de main(), y lee stdin ahí mismo", True, '''import json, sys
def main():
    d = json.load(sys.stdin)
    for _s in (sys.stdin, sys.stdout, sys.stderr):
        try: _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception: pass
    print(d["url"])
main()
'''),
    ("snippet bien, y ademas lee stdin", True, '''import sys
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
print(sys.stdin.read())
'''),
    ("import sys as s", True, "import sys as s\nprint(s.stdin.read())\n"),
    ("from sys import stdin", True, "from sys import stdin\nprint(stdin.read())\n"),
    ("input()", True, "print(input('dime: '))\n"),
    ("fileinput.input()", True, "import fileinput\nfor l in fileinput.input(): print(l)\n"),
    ("solo mencionado en un docstring", False, '"""usa sys.stdin algun dia"""\nprint(1)\n'),
    ("solo mencionado en un comentario", False, "# lee de sys.stdin\nprint(1)\n"),
    ("no lo usa", False, "import sys\nprint(sys.argv)\n"),
]


@pytest.mark.parametrize("nombre,esperado,src",
                         CASOS_LEE_STDIN, ids=[c[0] for c in CASOS_LEE_STDIN])
def test_lee_stdin_no_se_apaga_por_donde_este_el_snippet(nombre, esperado, src):
    assert lee_stdin(src) is esperado, nombre
