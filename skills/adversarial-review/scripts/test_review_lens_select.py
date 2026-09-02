#!/usr/bin/env python3
"""Tests de review-lens-select.py (repo git temporal + modo --files). Ejecuta: pytest -q."""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "review-lens-select.py")

# Payloads construidos por concatenación para que este fichero no dispare la heurística
# si algún día se escanea (los tests están excluidos del escaneo de contenido, pero por si acaso).
EVAL = "ev" + "al(" + "'1+1')"
FSELECT = 'f"SEL' + 'ECT * FROM u WHERE id={uid}"'


def sh(cwd, *args):
    subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)


def run(cwd, *args, env_extra=None):
    env = dict(os.environ)
    env.update(env_extra or {})
    r = subprocess.run([sys.executable, SCRIPT, "--json", *args], cwd=cwd,
                       capture_output=True, text=True, env=env)
    data = json.loads(r.stdout) if r.stdout.strip() else None
    return r.returncode, data, r.stderr


def repo_git():
    """Repo temporal en master con un commit inicial inocuo y rama feature/x encima."""
    d = tempfile.mkdtemp(prefix="rls-")
    sh(d, "git", "init", "-q", "-b", "master")
    sh(d, "git", "config", "user.email", "t@t")
    sh(d, "git", "config", "user.name", "t")
    os.makedirs(os.path.join(d, "src"))
    open(os.path.join(d, "src", "app.py"), "w").write("def main():\n    return 1\n")
    open(os.path.join(d, "README.md"), "w").write("# demo\n")
    sh(d, "git", "add", "-A")
    sh(d, "git", "commit", "-q", "-m", "init")
    sh(d, "git", "checkout", "-q", "-b", "feature/x")
    return d


def write(d, rel, text):
    p = os.path.join(d, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)


def dev_json(d, text):
    os.makedirs(os.path.join(d, ".claude"), exist_ok=True)
    open(os.path.join(d, ".claude", "dev.json"), "w").write(text)


# ------------------------------------------------------------------ tests ----

def test_ruta_auth_activa_la_lente_c():
    d = repo_git()
    write(d, "auth/login.py", "def login(u, p):\n    return True\n")
    sh(d, "git", "add", "-A"); sh(d, "git", "commit", "-q", "-m", "login")
    code, data, _ = run(d)
    assert code == 0
    assert data["lente_c"] is True
    assert any(m["tipo"] == "ruta" and m["fichero"] == "auth/login.py" for m in data["motivos"])


def test_contenido_eval_en_linea_anadida_activa_la_lente_c():
    d = repo_git()
    write(d, "src/app.py", "def main():\n    return " + EVAL + "\n")
    sh(d, "git", "commit", "-q", "-am", "eval")
    code, data, _ = run(d)
    assert code == 0 and data["lente_c"] is True
    m = [m for m in data["motivos"] if m["tipo"] == "contenido"]
    assert m and m[0]["fichero"] == "src/app.py" and m[0]["linea"] == 2


def test_nada_sensible_da_false_con_motivos_vacios():
    d = repo_git()
    write(d, "src/util.py", "def suma(a, b):\n    return a + b\n")
    write(d, "docs/guia.md", "# Guía\n\nUsa " + EVAL + " nunca.\n")  # prosa: no se escanea
    sh(d, "git", "add", "-A"); sh(d, "git", "commit", "-q", "-m", "util")
    code, data, err = run(d)
    assert code == 0
    assert data["lente_c"] is False and data["motivos"] == []
    assert data["modo"] == "auto"


def test_config_siempre_fuerza_true_aunque_nada_sea_sensible():
    d = repo_git()
    dev_json(d, json.dumps({"revision": {"lenteSeguridad": "siempre"}}))
    write(d, "src/util.py", "x = 1\n")
    sh(d, "git", "add", "-A"); sh(d, "git", "commit", "-q", "-m", "x")
    code, data, _ = run(d)
    assert code == 0 and data["lente_c"] is True and data["modo"] == "siempre"
    assert all(m["tipo"] == "config" for m in data["motivos"])


def test_config_nunca_fuerza_false_aunque_haya_auth():
    d = repo_git()
    dev_json(d, json.dumps({"revision": {"lenteSeguridad": "nunca"}}))
    write(d, "auth/login.py", "x = 1\n")
    sh(d, "git", "add", "-A"); sh(d, "git", "commit", "-q", "-m", "x")
    code, data, _ = run(d)
    assert code == 0 and data["lente_c"] is False and data["modo"] == "nunca"


def test_sin_git_con_files_funciona_por_ruta_y_contenido():
    d = tempfile.mkdtemp(prefix="rls-nogit-")
    write(d, "config/session.py", "TIMEOUT = 30\n")
    write(d, "src/db.py", "q = " + FSELECT + "\n")
    write(d, "src/ok.py", "x = 1\n")
    code, data, err = run(d, "--files", "config/session.py", "src/db.py", "src/ok.py")
    assert code == 0 and data["lente_c"] is True
    tipos = {(m["tipo"], m["fichero"]) for m in data["motivos"]}
    assert ("ruta", "config/session.py") in tipos
    assert ("contenido", "src/db.py") in tipos
    assert not any(m["fichero"] == "src/ok.py" for m in data["motivos"])


def test_sin_git_y_sin_files_avisa_y_devuelve_false_exit_0():
    d = tempfile.mkdtemp(prefix="rls-nogit-")
    code, data, err = run(d)
    assert code == 0 and data["lente_c"] is False
    assert "git" in err.lower()


def test_dev_json_corrupto_degrada_a_auto_con_aviso():
    d = repo_git()
    dev_json(d, "{ esto no es json")
    write(d, "src/util.py", "x = 1\n")
    sh(d, "git", "add", "-A"); sh(d, "git", "commit", "-q", "-m", "x")
    code, data, err = run(d)
    assert code == 0 and data["modo"] == "auto" and data["lente_c"] is False
    assert "dev.json" in err
    # valor desconocido → también auto + aviso
    dev_json(d, json.dumps({"revision": {"lenteSeguridad": "tal-vez"}}))
    code, data, err = run(d)
    assert code == 0 and data["modo"] == "auto" and "lenteSeguridad" in err


def test_patron_solo_en_linea_borrada_no_cuenta():
    d = repo_git()
    # el patrón ya estaba en master; la rama lo BORRA → no es introducido ni reabierto
    sh(d, "git", "checkout", "-q", "master")
    write(d, "src/app.py", "def main():\n    return " + EVAL + "\n")
    sh(d, "git", "commit", "-q", "-am", "eval en master")
    sh(d, "git", "checkout", "-q", "feature/x")
    sh(d, "git", "merge", "-q", "master")
    write(d, "src/app.py", "def main():\n    return 1\n")
    sh(d, "git", "commit", "-q", "-am", "quita eval")
    code, data, _ = run(d)
    assert code == 0 and data["lente_c"] is False and data["motivos"] == []


def test_binario_se_salta_sin_error():
    d = repo_git()
    with open(os.path.join(d, "logo.png"), "wb") as f:
        f.write(b"\x89PNG\x00\x00" + EVAL.encode() + b"\x00PRIVATE KEY\x00")
    # sin comitear (untracked) y también comiteado
    code, data, err = run(d)
    assert code == 0 and data["lente_c"] is False and data["motivos"] == []
    sh(d, "git", "add", "-A"); sh(d, "git", "commit", "-q", "-m", "png")
    code, data, err = run(d)
    assert code == 0 and data["lente_c"] is False and "Traceback" not in err


def test_cambios_sin_comitear_y_untracked_cuentan():
    d = repo_git()
    write(d, "src/app.py", "def main():\n    h = 'Author" + "ization: Bearer x'\n")  # tracked, sin comitear
    write(d, "src/new.py", "import pickle\nobj = pick" + "le.loads(data)\n")          # untracked
    code, data, _ = run(d)
    assert data["lente_c"] is True
    ficheros = {m["fichero"] for m in data["motivos"]}
    assert {"src/app.py", "src/new.py"} <= ficheros


def test_tests_y_fixtures_no_se_escanean_por_contenido_pero_si_por_ruta():
    d = repo_git()
    write(d, "tests/test_app.py", "def test_x():\n    assert " + EVAL + " == 2\n")
    write(d, "tests/fixtures/payload.py", "p = " + FSELECT + "\n")
    sh(d, "git", "add", "-A"); sh(d, "git", "commit", "-q", "-m", "tests")
    code, data, _ = run(d)
    assert data["lente_c"] is False and data["motivos"] == []
    write(d, "tests/test_auth.py", "x = 1\n")
    sh(d, "git", "add", "-A"); sh(d, "git", "commit", "-q", "-m", "auth test")
    code, data, _ = run(d)
    assert data["lente_c"] is True and data["motivos"][0]["tipo"] == "ruta"


def test_salida_texto_legible_y_base_explicita():
    d = repo_git()
    write(d, "Dockerfile", "FROM python:3.11\n")
    sh(d, "git", "add", "-A"); sh(d, "git", "commit", "-q", "-m", "docker")
    r = subprocess.run([sys.executable, SCRIPT, "--base", "master"], cwd=d, capture_output=True, text=True)
    assert r.returncode == 0
    assert "lente_c: true" in r.stdout and "Dockerfile" in r.stdout and "--base master" in r.stdout


def test_el_propio_script_no_se_dispara_a_si_mismo():
    """Regresión: la primera versión listaba los patrones literales en el docstring y en las
    etiquetas → cualquier cambio en el script forzaba la Lente C sobre este repo."""
    code, data, _ = run(HERE, "--files", "review-lens-select.py")
    assert code == 0 and data["lente_c"] is False and data["motivos"] == []


# ---------------------------------------------- revisión de dos lentes, intento 1 (T-fix1) ----

def test_fix1_files_conserva_prefijo_punto_solo_quita_dot_slash():
    """Gap I1: `.lstrip("./")` borraba caracteres → `.env` quedaba `env` y `.github/…` `github/…`."""
    d = tempfile.mkdtemp(prefix="rls-nogit-")
    write(d, ".env", "X=1\n")
    write(d, ".github/workflows/ci.yml", "on: push\n")
    write(d, "src/ok.py", "x = 1\n")
    code, data, _ = run(d, "--files", ".env", "./.github/workflows/ci.yml", "././src/ok.py")
    assert code == 0 and data["lente_c"] is True
    ficheros = {m["fichero"] for m in data["motivos"]}
    assert ficheros == {".env", ".github/workflows/ci.yml"}


def test_fix1_ruta_no_ascii_con_quotepath_por_defecto():
    """Gap I2: con core.quotepath por defecto git escribe "app/caf\\303\\251.py" y la cabecera +++ no casaba."""
    d = repo_git()
    write(d, "app/café.py", "x = 1\n")
    sh(d, "git", "add", "-A"); sh(d, "git", "commit", "-q", "-m", "cafe")
    write(d, "app/café.py", "x = 1\ny = " + EVAL + "\n")
    sh(d, "git", "commit", "-q", "-am", "eval")
    code, data, _ = run(d)
    assert code == 0 and data["lente_c"] is True
    m = [m for m in data["motivos"] if m["tipo"] == "contenido"]
    assert m and m[0]["fichero"] == "app/café.py" and m[0]["linea"] == 2


def test_fix1_linea_anadida_que_empieza_por_mas_mas_no_es_cabecera():
    """Gap M3: una línea añadida `++ x` aparece como `+++ x` en el diff y se tomaba por cabecera."""
    d = repo_git()
    write(d, "src/app.py", "def main():\n    return 1\n++ marcador\nz = " + EVAL + "\n")
    sh(d, "git", "commit", "-q", "-am", "plusplus")
    code, data, _ = run(d)
    assert code == 0 and data["lente_c"] is True
    m = [m for m in data["motivos"] if m["tipo"] == "contenido"]
    assert m and m[0]["fichero"] == "src/app.py" and m[0]["linea"] == 4


def test_fix1_revision_no_dict_avisa_y_degrada_a_auto():
    """Gap M4: `"revision": "x"` degradaba a auto SIN aviso."""
    d = repo_git()
    dev_json(d, json.dumps({"revision": "x"}))
    write(d, "src/util.py", "x = 1\n")
    sh(d, "git", "add", "-A"); sh(d, "git", "commit", "-q", "-m", "x")
    code, data, err = run(d)
    assert code == 0 and data["modo"] == "auto" and "revision" in err


def test_fix1_ruta_anclada_a_inicio_de_token_y_sin_prosa_ni_docs():
    """Gap M6: `author.md ~ auth`, `token-diet/tasks.md ~ token`, `oracle.py ~ acl` eran falsos positivos."""
    d = tempfile.mkdtemp(prefix="rls-nogit-")
    positivos = ["src/authentication.py", "src/authz.py", "sessions/store.py", "hooks/session-context.sh",
                 "lib/jwt_utils.py", "deploy/Dockerfile.prod", ".env.local", ".github/workflows/ci.yml",
                 "tests/test_auth.py", "app/crypto/keys.py"]
    negativos = ["docs/author.md", "docs/roadmap/2026-08-10-token-diet/tasks.md", "src/oracle.py",
                 "docs/auth/README.md", "notes/session.txt", "src/encrypt.py", "lib/myacl.py",
                 # debt-cleanup T-03a: stems con límite final — ya no cuentan como prefijo
                 "src/tokenizer.py", "src/helmet.py"]
    for f in positivos + negativos:
        write(d, f, "x = 1\n")
    code, data, _ = run(d, "--files", *positivos, *negativos)
    assert code == 0
    disparan = {m["fichero"] for m in data["motivos"] if m["tipo"] == "ruta"}
    assert disparan == set(positivos), disparan ^ set(positivos)


def test_fix1_repo_sin_commits_no_rompe():
    d = tempfile.mkdtemp(prefix="rls-empty-")
    sh(d, "git", "init", "-q", "-b", "master")
    write(d, "auth/login.py", "x = 1\n")
    code, data, err = run(d)
    assert code == 0 and data["lente_c"] is True and "Traceback" not in err


def test_cleanup_stems_con_limite_final():
    """Debt-cleanup T-03a: `token(s)`, `helm`, `acl` con límite final; `auth(?!or)`; `session(s)` amplio."""
    d = tempfile.mkdtemp(prefix="rls-stems-")
    positivos = ["src/tokens.py", "src/token_store.py", "src/auth_middleware.py", "sessions/x.py",
                 "hooks/session-context.sh", "deploy/helm/values.yaml", "src/acl.py", "src/cors-config.js",
                 "auth/oauth2.py", "src/secrets_loader.py"]
    negativos = ["src/tokenizer.py", "src/helmet.py", "src/author.md", "src/authors.py", "src/aclimate.py",
                 "src/corsair.py", "src/helmets.py"]
    for f in positivos + negativos:
        write(d, f, "x = 1\n")
    code, data, _ = run(d, "--files", *positivos, *negativos)
    assert code == 0
    disparan = {m["fichero"] for m in data["motivos"] if m["tipo"] == "ruta"}
    assert disparan == set(positivos), disparan ^ set(positivos)


def test_cleanup_revision_excluir_aplica_a_ruta_no_a_contenido():
    """Debt-cleanup T-03b: `revision.excluir` (globs `**`-aware) saca ficheros de la heurística de RUTA;
    el CONTENIDO añadido sigue contando (una línea con ejecución dinámica en un fichero excluido dispara)."""
    d = repo_git()
    dev_json(d, json.dumps({"revision": {"lenteSeguridad": "auto", "excluir": ["hooks/**", "deploy/*.yaml"]}}))
    write(d, "hooks/session-context.sh", "echo hi\n")
    write(d, "deploy/helm.yaml", "a: 1\n")
    write(d, "deploy/sub/helm.yaml", "a: 1\n")          # `*` es un nivel: NO excluido
    code, data, err = run(d)
    assert code == 0 and "excluir" not in err
    rutas = {m["fichero"] for m in data["motivos"] if m["tipo"] == "ruta"}
    assert rutas == {"deploy/sub/helm.yaml"}, data["motivos"]
    # contenido añadido en un fichero excluido por ruta → sí dispara (la exclusión es solo de ruta)
    write(d, "hooks/session-context.sh", "echo hi\nx = " + EVAL + "\n")
    code, data, _ = run(d)
    assert code == 0 and data["lente_c"] is True
    assert {"tipo": "contenido", "fichero": "hooks/session-context.sh", "patron": "eval", "linea": 2} in data["motivos"]
    # `excluir` que no es lista de cadenas → se ignora con aviso; `hooks/**` deja de excluir
    dev_json(d, json.dumps({"revision": {"excluir": "hooks/**"}}))
    code, data, err = run(d)
    assert code == 0 and "excluir" in err
    assert "hooks/session-context.sh" in {m["fichero"] for m in data["motivos"] if m["tipo"] == "ruta"}
