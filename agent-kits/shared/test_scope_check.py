#!/usr/bin/env python3
"""Tests de scope-check.py con repo git temporal. Ejecuta: pytest -q."""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "scope-check.py")
INI = "docs/roadmap/2026-01-01-demo"

LEDGER = """---
tasks: demo
estado: en-progreso
---
# Checklist — demo

> Ledger canónico de progreso.

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase 1 — Uno | 0 | 2 | 0% |

## Fase 1 — Uno

### T-01 — Código

- **Descripción**: x
- **Estado**: en-progreso
- **Archivos**: `src/app.py`, `src/util/` (carpeta), `tests/test_*.py` (nuevo), `docs/{a,b}.md`, sus tests, `/tmp/fuera.txt`

**Criterios de aceptación**
- [ ] c

### T-02 — Doc

- **Descripción**: y
- **Estado**: borrador
- **Archivos**: `README.md` (nuevo), `notes/**/*.md`, `agents/*.md`

**Criterios de aceptación**
- [ ] c
"""

GIT_ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, env=GIT_ENV)


def touch(root, rel, content="x"):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").write(content)


def repo(tmp, main="main", feature=True):
    git(tmp, "init", "-q", "-b", main)
    touch(tmp, INI + "/tasks.md", LEDGER)
    touch(tmp, "base.txt")
    git(tmp, "add", "-A")
    git(tmp, "commit", "-qm", "init")
    if feature:
        git(tmp, "checkout", "-qb", "feature/demo")
    return tmp


def run(tmp, *extra):
    r = subprocess.run([sys.executable, SCRIPT, INI, *extra], cwd=tmp, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout, r.stderr


def _mod():
    """El módulo `scope-check.py` cargado en proceso (para probar helpers sueltos)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("scope_check_helpers", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def commit_all(tmp, msg="wip"):
    git(tmp, "add", "-A")
    git(tmp, "commit", "-qm", msg)


def run_con_default_vacio(tmp, *extra):
    """MUTANTE de T-11: el mismo `main()` con `EXCLUIR_DEFAULT` vacía, en proceso (sin copiar el
    script al árbol: una copia sin centinela registrado tumbaría a `lint_plugin.py`)."""
    import contextlib
    import importlib.util
    import io
    spec = importlib.util.spec_from_file_location("scope_check_mut", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.EXCLUIR_DEFAULT = ()
    cwd, argv = os.getcwd(), sys.argv
    buf = io.StringIO()
    try:
        os.chdir(tmp)
        sys.argv = ["scope-check.py", INI, *extra]
        with contextlib.redirect_stdout(buf):
            code = mod.main()
    finally:
        os.chdir(cwd)
        sys.argv = argv
    return code, buf.getvalue()


def test_en_alcance_exit_0_y_declarados_sin_tocar():
    with tempfile.TemporaryDirectory() as tmp:
        repo(tmp)
        touch(tmp, "src/app.py")
        commit_all(tmp)
        code, out, _ = run(tmp)
        assert code == 0, out
        assert "fuera de alcance (0)" in out
        assert "declarados sin tocar" in out and "README.md (T-02)" in out


def test_fuera_de_alcance_exit_1_y_warn_only_0():
    with tempfile.TemporaryDirectory() as tmp:
        repo(tmp)
        touch(tmp, "src/app.py")
        touch(tmp, "otro/colado.py")
        commit_all(tmp)
        code, out, _ = run(tmp)
        assert code == 1 and "otro/colado.py" in out and "fuera de alcance (1)" in out
        code, out, _ = run(tmp, "--warn-only")
        assert code == 0 and "otro/colado.py" in out


def test_glob_carpeta_nuevo_y_llaves():
    with tempfile.TemporaryDirectory() as tmp:
        repo(tmp)
        touch(tmp, "tests/test_app.py")          # glob tests/test_*.py + «(nuevo)»
        touch(tmp, "src/util/deep/x.py")         # carpeta src/util/
        touch(tmp, "docs/b.md")                  # llaves {a,b}
        touch(tmp, "README.md")                  # (nuevo) sin glob
        commit_all(tmp)
        code, out, _ = run(tmp, "--json")
        d = json.loads(out)
        assert code == 0, out
        assert sorted(d["en_alcance"]) == ["README.md", "docs/b.md", "src/util/deep/x.py", "tests/test_app.py"]
        assert "/tmp/fuera.txt" not in d["patrones"] and "sus tests" not in d["patrones"]


def test_sin_comitear_y_sin_seguimiento_cuentan():
    with tempfile.TemporaryDirectory() as tmp:
        repo(tmp)
        touch(tmp, "base.txt", "modificado")     # modificado sin comitear → fuera
        touch(tmp, "nuevo-sin-add.py")           # untracked → fuera
        code, out, _ = run(tmp)
        assert code == 1 and "base.txt" in out and "nuevo-sin-add.py" in out


def test_tasks_md_propio_y_knowledge_siempre_en_alcance():
    with tempfile.TemporaryDirectory() as tmp:
        repo(tmp)
        touch(tmp, INI + "/tasks.md", LEDGER + "\nnota\n")
        touch(tmp, "docs/knowledge/adr/ADR-001-x.md")
        commit_all(tmp)
        code, out, _ = run(tmp)
        assert code == 0, out
        assert INI + "/tasks.md" in out and "ADR-001-x.md" in out
        # pero OTRO fichero del roadmap (spec.md) sí está fuera
        touch(tmp, INI + "/spec.md")
        code, out, _ = run(tmp)
        assert code == 1 and "spec.md" in out


def test_sin_base_clara_exit_2_y_con_base_explicita():
    with tempfile.TemporaryDirectory() as tmp:
        repo(tmp, main="trunk")                  # ni main ni master; estamos en feature/demo
        touch(tmp, "src/app.py")
        commit_all(tmp)
        code, out, err = run(tmp)
        assert code == 2 and "--base" in err and "trunk" not in out
        code, out, _ = run(tmp, "--base", "trunk")
        assert code == 0 and "src/app.py" in out


def test_en_rama_principal_base_es_head():
    with tempfile.TemporaryDirectory() as tmp:
        repo(tmp, feature=False)                 # seguimos en main
        touch(tmp, "src/app.py")                 # sin comitear
        code, out, _ = run(tmp)
        assert code == 0 and "rama principal" in out and "src/app.py" in out


def test_master_como_principal_y_ledger_inexistente():
    with tempfile.TemporaryDirectory() as tmp:
        repo(tmp, main="master")
        touch(tmp, "src/app.py")
        commit_all(tmp)
        code, out, _ = run(tmp)
        assert code == 0 and "merge-base master" in out
        r = subprocess.run([sys.executable, SCRIPT, "docs/roadmap/no-existe"], cwd=tmp,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        assert r.returncode == 2 and "no existe" in r.stderr


def test_fix1_doble_asterisco_cero_o_mas_directorios_y_asterisco_un_nivel():
    # (4) `notes/**/*.md` casa notes/x.md (cero directorios) y notes/a/b/c.md; `agents/*.md` NO cruza `/`
    with tempfile.TemporaryDirectory() as tmp:
        repo(tmp)
        touch(tmp, "notes/knowledge_x.md")
        touch(tmp, "notes/a/b/c.md")
        touch(tmp, "agents/x.md")
        touch(tmp, "agents/sub/y.md")             # fuera: `*` es un solo nivel
        commit_all(tmp)
        code, out, _ = run(tmp, "--json")
        d = json.loads(out)
        assert code == 1, out
        assert "notes/knowledge_x.md" in d["en_alcance"] and "notes/a/b/c.md" in d["en_alcance"]
        assert "agents/x.md" in d["en_alcance"] and d["fuera_de_alcance"] == ["agents/sub/y.md"]


def test_fuera_de_git_exit_2():
    with tempfile.TemporaryDirectory() as tmp:
        touch(tmp, INI + "/tasks.md", LEDGER)
        r = subprocess.run([sys.executable, SCRIPT, INI], cwd=tmp, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env=dict(os.environ, GIT_CEILING_DIRECTORIES=os.path.dirname(tmp)))
        assert r.returncode == 2 and "git" in r.stderr


# --------------------------------------------------- T-11: exclusiones (E6) ----

def test_exclusiones_por_defecto_no_salen_fuera_de_alcance():
    """`CONTINUE-HERE*.md`, `.claude/**` y el journal no son de ninguna tarea: ni en alcance ni
    fuera (exit 0), pero se listan en `excluidos`. Mutante: con `EXCLUIR_DEFAULT` vacía, exit 1."""
    with tempfile.TemporaryDirectory() as tmp:
        repo(tmp)
        touch(tmp, "CONTINUE-HERE.md")
        touch(tmp, "CONTINUE-HERE.local.md")
        touch(tmp, ".claude/usage-state.json", "{}")
        touch(tmp, "docs/knowledge/journal/2026-01-01-sesion.md")
        touch(tmp, "src/app.py")                  # declarado: sigue en alcance
        commit_all(tmp)
        code, out, _ = run(tmp, "--json")
        d = json.loads(out)
        assert code == 0, out
        assert d["fuera_de_alcance"] == [], d["fuera_de_alcance"]
        assert sorted(d["excluidos"]) == [
            ".claude/usage-state.json", "CONTINUE-HERE.local.md", "CONTINUE-HERE.md",
            "docs/knowledge/journal/2026-01-01-sesion.md"], d["excluidos"]
        assert d["en_alcance"] == ["src/app.py"], d["en_alcance"]
        # claves del contrato: las 8 de siempre + las 5 aditivas de T-11 (`excluidos` y, desde el
        # gap R4a-9, `excluir_vigente`/`excluir_usuario`/`excluidos_patron`/`avisos`) + las 2 del
        # gap B4-1 (`excluidos_usuario`/`info`: la visibilidad sin veredicto)
        assert sorted(d) == ["avisos", "base", "base_desc", "cambiados", "declarados_sin_tocar",
                             "en_alcance", "excluidos", "excluidos_patron", "excluidos_usuario",
                             "excluir_usuario", "excluir_vigente", "fuera_de_alcance", "info",
                             "patrones", "slug"]
        # el patrón que casó cada excluido se publica, y el default es el vigente sin dev.json
        assert d["excluidos_patron"]["CONTINUE-HERE.md"] == "CONTINUE-HERE*.md"
        assert d["excluidos_patron"][".claude/usage-state.json"] == ".claude/**"
        assert d["excluir_vigente"] == ["CONTINUE-HERE*.md", ".claude/**", "docs/knowledge/journal/**"]
        assert d["excluir_usuario"] == [] and d["avisos"] == []
        # mutante: sin lista por defecto los cuatro vuelven a «fuera de alcance» y la puerta salta
        code, out = run_con_default_vacio(tmp)
        assert code == 1, out
        assert "CONTINUE-HERE.md" in out and ".claude/usage-state.json" in out


def test_dev_json_alcance_excluir_amplia_de_forma_aditiva():
    with tempfile.TemporaryDirectory() as tmp:
        repo(tmp)
        touch(tmp, "ruido/local/nota.txt")
        touch(tmp, "CONTINUE-HERE.md")
        commit_all(tmp)
        code, out, _ = run(tmp, "--json")
        assert code == 1 and json.loads(out)["fuera_de_alcance"] == ["ruido/local/nota.txt"]
        touch(tmp, ".claude/dev.json", json.dumps({"alcance": {"excluir": ["ruido/**"]}}))
        code, out, err = run(tmp, "--json")
        d = json.loads(out)
        assert code == 0, out + err
        assert d["fuera_de_alcance"] == []
        # aditiva: el default NO se pierde al declarar `alcance.excluir`
        assert "ruido/local/nota.txt" in d["excluidos"] and "CONTINUE-HERE.md" in d["excluidos"]


def test_alcance_excluir_mal_formado_avisa_y_usa_el_default():
    with tempfile.TemporaryDirectory() as tmp:
        repo(tmp)
        touch(tmp, "CONTINUE-HERE.md")
        touch(tmp, "ruido/local/nota.txt")
        touch(tmp, ".claude/dev.json", json.dumps({"alcance": {"excluir": "ruido/**"}}))
        commit_all(tmp)
        code, out, err = run(tmp, "--json")
        d = json.loads(out)
        assert code == 1, out                      # el glob mal formado no excluye nada
        assert "alcance.excluir" in err and "no es una lista de globs" in err
        assert d["fuera_de_alcance"] == ["ruido/local/nota.txt"]
        assert sorted(d["excluidos"]) == [".claude/dev.json", "CONTINUE-HERE.md"]  # default vivo
        # y un dev.json ilegible tampoco rompe la puerta
        touch(tmp, ".claude/dev.json", "{no es json")
        code, out, err = run(tmp, "--json")
        assert code == 1 and "ilegible" in err
        assert sorted(json.loads(out)["excluidos"]) == [".claude/dev.json", "CONTINUE-HERE.md"]


def test_fichero_declarado_en_archivos_gana_a_la_exclusion():
    """`.claude/**` está excluido por defecto, pero si una tarea lo declara es alcance legítimo."""
    with tempfile.TemporaryDirectory() as tmp:
        repo(tmp)
        ledger = LEDGER.replace("`README.md` (nuevo)", "`README.md` (nuevo), `.claude/dev.json`")
        touch(tmp, INI + "/tasks.md", ledger)
        touch(tmp, ".claude/dev.json", "{}")
        touch(tmp, ".claude/otro.json", "{}")
        commit_all(tmp)
        code, out, _ = run(tmp, "--json")
        d = json.loads(out)
        assert code == 0, out
        assert ".claude/dev.json" in d["en_alcance"]      # declarado → en alcance
        assert d["excluidos"] == [".claude/otro.json"]    # no declarado → excluido


# ---- gap R4a-1: la exclusión de usuario no puede apagar la puerta EN SILENCIO ----

def test_excluir_de_usuario_que_deja_cero_fuera_de_alcance_avisa():
    """`{"alcance": {"excluir": ["**"]}}` sigue dando exit 0 (la exclusión puede ser deliberada),
    pero ya NO en silencio: aviso en stderr y en la clave `avisos` del --json."""
    with tempfile.TemporaryDirectory() as tmp:
        repo(tmp)
        for f in ("ruido/a.txt", "ruido/b.txt", "ruido/c.txt", "otro/d.txt"):
            touch(tmp, f)
        commit_all(tmp)
        code, out, err = run(tmp, "--json")
        assert code == 1 and len(json.loads(out)["fuera_de_alcance"]) == 4
        touch(tmp, ".claude/dev.json", json.dumps({"alcance": {"excluir": ["**"]}}))
        code, out, err = run(tmp, "--json")
        d = json.loads(out)
        assert code == 0, out                       # la puerta pasa…
        assert d["fuera_de_alcance"] == []
        assert d["excluir_usuario"] == ["**"]
        # …pero lo dice, en stderr y en el JSON
        assert any("fuera de alcance» VACÍA" in a for a in d["avisos"]), d["avisos"]
        assert any("decorativa" in a for a in d["avisos"]), d["avisos"]
        assert "VACÍA" in err and "decorativa" in err
        assert d["excluidos_patron"]["ruido/a.txt"] == "**"


def test_glob_de_usuario_desproporcionado_avisa_aunque_quede_algo_fuera():
    """El segundo disparo del aviso: un glob de usuario que se come ≥ la mitad del diff, aunque la
    puerta siga en exit 1 por otros ficheros."""
    with tempfile.TemporaryDirectory() as tmp:
        repo(tmp)
        for f in ("ruido/a.txt", "ruido/b.txt", "ruido/c.txt", "ruido/d.txt", "otro/e.txt"):
            touch(tmp, f)
        touch(tmp, ".claude/dev.json", json.dumps({"alcance": {"excluir": ["ruido/**"]}}))
        commit_all(tmp)
        code, out, err = run(tmp, "--json")
        d = json.loads(out)
        assert code == 1 and d["fuera_de_alcance"] == ["otro/e.txt"]
        assert any("«ruido/**» excluye 4 de los" in a for a in d["avisos"]), d["avisos"]
        # el default NUNCA dispara el aviso: solo lo hace la exclusión que escribe el usuario
        assert not any("CONTINUE-HERE" in a or ".claude/**" in a for a in d["avisos"])


# ---- gap R4a-29: una exclusión LEGÍTIMA no puede dejar un aviso perpetuo ----

def test_glob_de_usuario_legitimo_no_deja_ningun_aviso():
    """El caso que convertía el aviso en un Important imposible de cerrar: un proyecto con
    `alcance.excluir` legítimo, una pasada verde y UN fichero de su ruido tocado. Antes: ⚠️ «fuera
    de alcance VACÍA» en CADA pasada (el DoD manda tratarlo como gap Important, y la única forma de
    quitarlo era borrar la configuración). Ahora: cero avisos, porque el glob no esconde el grueso
    del trabajo — solo quita ruido ya previsto."""
    with tempfile.TemporaryDirectory() as tmp:
        repo(tmp)
        touch(tmp, "src/app.py")                 # declarado en el ledger → en alcance
        touch(tmp, "build/salida.log")           # ruido del proyecto → excluido por su glob
        touch(tmp, ".claude/dev.json", json.dumps({"alcance": {"excluir": ["build/**"]}}))
        commit_all(tmp)
        code, out, err = run(tmp, "--json")
        d = json.loads(out)
        assert code == 0, out
        assert d["fuera_de_alcance"] == [], d
        assert sorted(d["excluidos"]) == [".claude/dev.json", "build/salida.log"], d
        assert d["avisos"] == [], d["avisos"]        # ← lo que exige el gap R4a-29
        assert "⚠️" not in err, err
        # …y el aviso NO se ha desactivado: en cuanto el glob esconde el grueso del trabajo, vuelve
        for f in ("build/a.log", "build/b.log"):
            touch(tmp, f)
        commit_all(tmp)
        code, out, err = run(tmp, "--json")
        d = json.loads(out)
        assert code == 0 and any("fuera de alcance» VACÍA" in a for a in d["avisos"]), d["avisos"]


# ---- gap R4a-39: el denominador no cuenta el ruido que el propio script excluye por defecto ----

def test_la_fraccion_no_se_diluye_con_los_excluidos_por_defecto():
    """Antes, añadir `CONTINUE-HERE.md` y tres ficheros de `.claude/` bajaba un 3 de 6 (50 %) a un
    3 de 10 (30 %) y APAGABA el aviso escondiendo exactamente lo mismo."""
    with tempfile.TemporaryDirectory() as tmp:
        repo(tmp)
        for f in ("ruido/a.txt", "ruido/b.txt", "ruido/c.txt",
                  "otro/d.txt", "otro/e.txt", "otro/f.txt"):
            touch(tmp, f)
        touch(tmp, ".claude/dev.json", json.dumps({"alcance": {"excluir": ["ruido/**"]}}))
        commit_all(tmp)
        code, out, _ = run(tmp, "--json")
        d = json.loads(out)
        assert code == 1 and len(d["fuera_de_alcance"]) == 3, d
        assert any("«ruido/**» excluye 3 de los 6" in a for a in d["avisos"]), d["avisos"]
        # el ruido del orquestador NO diluye la fracción: sigue siendo 3 de 6, no 3 de 10
        touch(tmp, "CONTINUE-HERE.md")
        for f in (".claude/x.json", ".claude/y.json", ".claude/z.json"):
            touch(tmp, f)
        commit_all(tmp)
        code, out, _ = run(tmp, "--json")
        d = json.loads(out)
        assert d["cambiados"] == 11, d["cambiados"]      # 6 relevantes + 5 excluidos por defecto
        assert any("«ruido/**» excluye 3 de los 6" in a for a in d["avisos"]), d["avisos"]


# ---- gap R4a-34: «no hay git» y «no es un repo» son cosas distintas ----

def test_sin_git_en_el_path_el_mensaje_no_dice_que_falte_el_repositorio():
    """Mismo exit 2, causa distinta: sin `git` en el PATH el remedio no es `git init`."""
    with tempfile.TemporaryDirectory() as tmp:
        repo(tmp)
        vacio = os.path.join(tmp, "sin-git")
        os.makedirs(vacio, exist_ok=True)
        entorno = dict(os.environ, PATH=vacio)
        r = subprocess.run([sys.executable, SCRIPT, INI], cwd=tmp, env=entorno,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        assert r.returncode == 2, r.stdout + r.stderr
        assert "no hay `git` en el PATH" in r.stderr, r.stderr
        assert "esto no es un repositorio git" not in r.stderr, r.stderr
    # …y fuera de un repo, con git disponible, se sigue diciendo lo de siempre
    with tempfile.TemporaryDirectory() as tmp:
        touch(tmp, INI + "/tasks.md", LEDGER)
        code, _, err = run(tmp)
        assert code == 2 and "esto no es un repositorio git" in err, err


def test_docs_knowledge_no_se_puede_excluir_desde_dev_json():
    """`SIEMPRE_EN_ALCANCE` se evalúa ANTES que la exclusión: un `docs/**` en `alcance.excluir` no
    saca un ADR nuevo del alcance (antes pasaba de `en_alcance` a `excluidos`)."""
    with tempfile.TemporaryDirectory() as tmp:
        repo(tmp)
        touch(tmp, "docs/knowledge/adr/ADR-001-x.md")
        touch(tmp, "docs/knowledge/journal/2026-01-01-sesion.md")
        touch(tmp, ".claude/dev.json", json.dumps({"alcance": {"excluir": ["docs/**"]}}))
        commit_all(tmp)
        code, out, _ = run(tmp, "--json")
        d = json.loads(out)
        assert code == 0, out
        assert d["en_alcance"] == ["docs/knowledge/adr/ADR-001-x.md"], d["en_alcance"]
        # el journal SÍ se excluye: lo escribe un hook y está fuera de `SIEMPRE_EN_ALCANCE`
        assert "docs/knowledge/journal/2026-01-01-sesion.md" in d["excluidos"]
# ---- gap B4-1: visibilidad SIEMPRE de lo que esconden los globs de usuario ----

def test_info_lista_siempre_lo_que_esconde_un_glob_de_usuario():
    """La otra mitad de R4a-29. El umbral calla el ⚠️ cuando la exclusión solo quita ruido, pero
    callar del todo dejaba sin rastro un glob que esconde uno o dos ficheros. Ahora: cero avisos y
    UNA línea ℹ️ con fichero y patrón, en stderr (también con --json) y en las claves
    `info`/`excluidos_usuario`. Los excluidos por DEFECTO no salen ahí: esos no los ha escrito
    nadie del proyecto."""
    with tempfile.TemporaryDirectory() as tmp:
        repo(tmp)
        touch(tmp, "src/app.py")                 # declarado en el ledger
        touch(tmp, "build/salida.log")           # lo esconde el glob de usuario
        touch(tmp, "CONTINUE-HERE.md")           # lo esconde el DEFECTO: no es cosa del usuario
        touch(tmp, ".claude/dev.json", json.dumps({"alcance": {"excluir": ["build/**"]}}))
        commit_all(tmp)
        code, out, err = run(tmp, "--json")
        d = json.loads(out)
        assert code == 0, out
        assert d["avisos"] == [], d["avisos"]                 # por debajo del umbral: sin ⚠️
        assert "⚠️" not in err, err
        # …pero la línea ℹ️ está, con el fichero y el glob que lo escondió
        assert len(d["info"]) == 1, d["info"]
        assert "build/salida.log (build/**)" in d["info"][0], d["info"]
        assert "ℹ️" in err and "build/salida.log (build/**)" in err, err
        assert "No es un gap" in d["info"][0], d["info"]
        # el default no entra ni en la línea ni en la clave nueva
        assert d["excluidos_usuario"] == {"build/salida.log": "build/**"}, d["excluidos_usuario"]
        assert "CONTINUE-HERE.md" not in d["info"][0], d["info"]
        assert "CONTINUE-HERE.md" in d["excluidos_patron"], d["excluidos_patron"]
        # …y con --json la ℹ️ sigue saliendo por stderr (el stdout es JSON puro)
        json.loads(out)


def test_sin_globs_de_usuario_no_hay_linea_info():
    """La ℹ️ es SOLO de la exclusión que escribe el proyecto: el default curado no la dispara."""
    with tempfile.TemporaryDirectory() as tmp:
        repo(tmp)
        touch(tmp, "src/app.py")
        touch(tmp, "CONTINUE-HERE.md")
        commit_all(tmp)
        code, out, err = run(tmp, "--json")
        d = json.loads(out)
        assert code == 0 and d["info"] == [], d["info"]
        assert d["excluidos_usuario"] == {}, d["excluidos_usuario"]
        assert "ℹ️  `alcance.excluir`" not in err, err


# ---- gap B4-2: tres causas para «no hay raíz de repo», no dos ----

def test_repo_presente_con_rev_parse_roto_es_la_tercera_causa_y_cita_a_git():
    """Git está, la carpeta SÍ tiene `.git` y aun así `git rev-parse` falla (config rota,
    `safe.directory`, repo corrupto). Antes las dos piezas afirmaban «no es un repositorio» y
    mandaban a hacer un `git init` sobre un repo que ya existe, tragándose el stderr de git —que
    es justo el diagnóstico."""
    with tempfile.TemporaryDirectory() as tmp:
        touch(tmp, INI + "/tasks.md", LEDGER)
        # `.git` como FICHERO que apunta a un gitdir inexistente: repo «presente» y roto
        open(os.path.join(tmp, ".git"), "w").write("gitdir: no-existe-de-verdad\n")
        code, _, err = run(tmp)
        assert code == 2, err
        assert "hay un `.git`" in err, err
        assert "esto no es un repositorio git" not in err, err
        assert "git rev-parse" in err and "safe.directory" in err, err
        # el stderr de git viaja dentro del mensaje, entrecomillado
        assert "«" in err and "»" in err, err
    # …y las otras dos causas siguen dando SU mensaje (la tercera no se las come)
    with tempfile.TemporaryDirectory() as tmp:
        touch(tmp, INI + "/tasks.md", LEDGER)
        code, _, err = run(tmp)
        assert code == 2 and "esto no es un repositorio git" in err, err
        assert "hay un `.git`" not in err, err


def test_hay_git_dir_mira_los_padres():
    """`hay_git_dir` es lo que distingue la tercera causa: pregunta al sistema de ficheros, no a
    git, y sube por los padres como hace el propio git."""
    mod = _mod()
    with tempfile.TemporaryDirectory() as tmp:
        hondo = os.path.join(tmp, "a", "b", "c")
        os.makedirs(hondo, exist_ok=True)
        assert mod.hay_git_dir(hondo) is False
        os.makedirs(os.path.join(tmp, ".git"), exist_ok=True)
        assert mod.hay_git_dir(hondo) is True
        assert mod.hay_git_dir(tmp) is True
