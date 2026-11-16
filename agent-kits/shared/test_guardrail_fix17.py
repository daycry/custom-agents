#!/usr/bin/env python3
"""Tests de guardrail-check.py: ciclo fix17 de T-06 (plugin-audit-2, fase 1, intento 17). Ejecuta: pytest -q.

Punto 1: re-anclaje general (git que lanza git, envoltorio o shell tras un programa fuera de la tabla). Punto 2: regla de rama por lista blanca
(`checkout`/`switch`, `-B`, `update-ref refs/heads/*`, `rebase`, `bisect`). Punto 3: `rama_barata` exige un repositorio valido. Punto 6: el arnes de fix15 decide por
el REGISTRO del shim, no por stdout. Los arneses con bash real ponen shims de `git`, `GIT`, `Git`, `git.exe`, `GIT.EXE`, `sudo`, `doas`, `su` y de cada programa
del corpus delante en el PATH (Git Bash ve el `sudo` real de Windows 11): «ejecuta git» se decide por el registro.
"""
import os
import re
import subprocess

import pytest

from test_guardrail_differential import BASH, necesita_bash
from test_guardrail_fix12 import decide, gc
from test_guardrail_fix16 import NOMBRES_SHIM, _git, ejecuta_git, repo  # noqa: F401  (`repo` es un fixture)
from test_guardrail_fix17_corpus import (ENVOLTORIO_DETRAS_DE_DESCONOCIDO17, GIT_LANZA_GIT17, PERMITIDAS_RAMA17, PROGRAMAS17, SALIDAS_RAMA17)

AQUI = os.path.dirname(os.path.abspath(__file__))


def _id(o):
    return o.encode("unicode_escape").decode("ascii")[:70]


# --------------------------------------------------------------------------- punto 1: la clase, no la forma ----
@pytest.mark.parametrize("orden", GIT_LANZA_GIT17, ids=[_id(o) for o in GIT_LANZA_GIT17])
def test_git_que_lanza_otro_git_se_analiza_como_codigo(orden):
    assert decide(orden), orden


@pytest.mark.parametrize("orden", ENVOLTORIO_DETRAS_DE_DESCONOCIDO17, ids=[_id(o) for o in ENVOLTORIO_DETRAS_DE_DESCONOCIDO17])
def test_un_envoltorio_o_una_shell_tras_un_programa_desconocido_se_analiza_entero(orden):
    assert decide(orden), orden


LEGITIMAS17 = [
    "uv run pytest -q", "uv run --no-project python -c 'print(1)'", "chroot / ls", "strace -f node x.js", "strace env FOO=1 make test", "xvfb-run npm test",
    "dotenv -- npm run build", "npx prettier --check .", "poetry run pytest", "direnv exec . make", "strace bash -c 'make test'", "uv run bash -c 'make test'",
    "uv run env -S 'make test'", "uv run xargs echo", "strace xargs echo hola", "chroot / sh -c 'ls /'", "uv run sh -c 'git status'", "strace env GIT_PAGER=cat git log",
    "git submodule foreach 'git status'", "git submodule foreach --recursive git pull", "git submodule foreach 'echo $name'", "git rebase -x 'make test' HEAD~2",
    "git bisect run make test", "git log --oneline", "git submodule update --init --recursive", "git submodule status",
]


@pytest.mark.parametrize("orden", LEGITIMAS17, ids=[_id(o) for o in LEGITIMAS17])
def test_lo_legitimo_tras_programas_desconocidos_sigue_permitido(orden):
    assert decide(orden) is None, orden


def test_el_sufijo_se_analiza_como_segmento_nuevo_sin_heredar_el_estado_de_la_orden_exterior():
    """`env -C ..` y `xargs` aparecen DENTRO del sufijo: su cambio de base y sus rutas por stdin cuentan aunque la orden exterior no los traiga."""
    assert decide("uv run xargs git restore")
    assert decide("strace env -C .. git restore a.txt")
    assert decide("uv run --no-project env GIT_DIR=../o/.git git checkout -- a.txt")
    assert decide("strace sudo -D .. git restore a.txt")
    assert decide("strace sudo git status") is None


def test_mas_de_32_anclas_en_una_orden_se_deniegan_sin_analizarlas_una_a_una():
    orden = "echo " + " ".join(["env"] * 40)
    razon = decide(orden)
    assert razon and "32" in razon, razon


def test_el_coste_del_reanclaje_es_lineal_en_orden_y_acotado():
    import time
    for n in (5, 25, 32):
        orden = "uv run " + " ".join(["bash -c 'echo'"] * n)
        t0 = time.monotonic()
        decide(orden)
        assert time.monotonic() - t0 < 5.0, n


# --------------------------------------------------------------------------- punto 2: rama por lista blanca ----
@pytest.mark.parametrize("orden", SALIDAS_RAMA17, ids=[_id(o) for o in SALIDAS_RAMA17])
def test_la_lista_blanca_de_rama_deniega_lo_que_no_es_la_rama_actual(orden):
    assert gc.check_git(orden, "feature/x"), orden


@pytest.mark.parametrize("orden", PERMITIDAS_RAMA17, ids=[_id(o) for o in PERMITIDAS_RAMA17])
def test_lo_que_no_sale_de_la_rama_sigue_permitido(orden):
    assert gc.check_git(orden, "feature/x") is None, orden


def test_checkout_de_una_ruta_existente_se_permite(tmp_path, monkeypatch):
    (tmp_path / "main.py").write_text("x")
    monkeypatch.chdir(tmp_path)
    assert gc.check_git("git checkout main.py", "feature/x") is None
    assert gc.check_git("git checkout nada-de-esto.py", "feature/x"), "una ref que no es la rama actual ni una ruta existente se deniega"
    assert gc.check_git("git switch main.py", "feature/x"), "`switch` no restaura ficheros"


def test_con_la_rama_desconocida_solo_pasan_las_formas_sin_destino():
    for orden in ("git switch feature/x", "git checkout feature/x", "git checkout -B feature/x", "git checkout HEAD~1", "git rebase main feature/x"):
        assert gc.check_git(orden, None), orden
    for orden in ("git status", "git switch -c x", "git checkout -b x", "git checkout main -- a.py", "git checkout HEAD", "git rebase main"):
        assert gc.check_git(orden, None) is None, orden


def test_en_main_o_con_head_suelto_no_se_aplica_la_regla_de_salida():
    assert gc.check_git("git switch main", "main") is None
    assert gc.check_git("git checkout v1.0", "HEAD") is None


def test_checkout_head_a_secas_conserva_la_rama_con_git_real(repo):
    assert _git(repo, "checkout", "HEAD").returncode == 0
    assert _git(repo, "symbolic-ref", "--short", "HEAD").stdout.strip() == "feature/x", "con git real `checkout HEAD` NO suelta la rama"
    assert gc.check_git("git checkout HEAD", "feature/x") is None


def test_b_mayuscula_sobre_otra_rama_cambia_de_rama_con_git_real(repo):
    """`checkout -B <otra>` reinicia esa rama y cambia a ella con git real: no es un falso deny."""
    assert _git(repo, "branch", "feature/y").returncode == 0
    assert gc.check_git("git checkout -B feature/y", "feature/x")
    r = _git(repo, "checkout", "-B", "feature/y")
    assert r.returncode == 0 and _git(repo, "symbolic-ref", "--short", "HEAD").stdout.strip() == "feature/y"


def test_submodule_foreach_pierde_cambios_con_git_real_y_se_deniega(tmp_path):
    sub, sup = tmp_path / "sub", tmp_path / "sup"
    for d in (sub, sup):
        d.mkdir()
        assert _git(d, "init", "-q", "-b", "feature/x").returncode == 0
        _git(d, "config", "user.name", "t")
        _git(d, "config", "user.email", "t@t")
        _git(d, "config", "protocol.file.allow", "always")
    (sub / "a.txt").write_text("a")
    _git(sub, "add", "a.txt")
    assert _git(sub, "commit", "-q", "-m", "c").returncode == 0
    r = _git(sup, "-c", "protocol.file.allow=always", "submodule", "add", "-q", str(sub), "s")
    assert r.returncode == 0, r.stderr
    (sup / "s" / "a.txt").write_text("TRABAJO SIN COMITEAR")
    orden = "git submodule foreach --recursive 'git reset --hard'"
    assert gc.check_git(orden, "feature/x"), "el guardarrail debe denegar la forma"
    r = _git(sup, "submodule", "foreach", "--recursive", "git reset --hard")
    assert r.returncode == 0 and (sup / "s" / "a.txt").read_text() == "a", "con git real la forma borra el cambio sin comitear del submodulo"


# --------------------------------------------------------------------------- punto 3: rama_barata exige un repositorio valido ----
def test_rama_barata_rechaza_un_git_sin_objetos_ni_refs_y_recurre_a_git(repo, tmp_path, monkeypatch):
    monkeypatch.delenv("GIT_DIR", raising=False)
    monkeypatch.delenv("GIT_WORK_TREE", raising=False)
    falso = repo / "proj"
    (falso / ".git").mkdir(parents=True)
    (falso / ".git" / "HEAD").write_text("ref: refs/heads/feature/falsa\n")
    llamadas = []
    monkeypatch.setattr(gc, "current_branch", lambda d, timeout=5: llamadas.append(d) or "main")
    assert gc.rama_barata(str(falso)) == "main" and llamadas, "un `.git` con solo HEAD no es un repositorio para git: se recurre a `current_branch`"
    llamadas.clear()
    assert gc.rama_barata(str(repo)) == "feature/x" and not llamadas, "un repositorio valido sigue leyendose sin lanzar git"


def test_rama_barata_acepta_un_worktree_con_commondir(repo, tmp_path, monkeypatch):
    monkeypatch.delenv("GIT_DIR", raising=False)
    monkeypatch.delenv("GIT_WORK_TREE", raising=False)
    wt = tmp_path / "wt"
    assert _git(repo, "worktree", "add", "-q", "-b", "feature/wt", str(wt)).returncode == 0
    monkeypatch.setattr(gc, "current_branch", lambda d, timeout=5: (_ for _ in ()).throw(AssertionError("no debe lanzar git")))
    assert gc.rama_barata(str(wt)) == "feature/wt"


# --------------------------------------------------------------------------- arnes con bash real y shims ----
_TROZO17 = 60
_SHIM_PROGRAMAS = sorted({p.split()[0] for p in PROGRAMAS17})
_SALTA = ('while [ $# -gt 0 ]; do case "$1" in -*|run|exec|/|.|--) shift;; *) break;; esac; done\n'
          'exec "$@"\n')


def _ejecutar17(tmp_path, ordenes, nombre):
    """Como `_ejecutar16` con un shim por cada programa de `PROGRAMAS17` (quita sus opciones y ejecuta lo que sigue) y `git` falso que solo registra."""
    registro = {}
    for k, ini in enumerate(range(0, len(ordenes), _TROZO17)):
        trozo = ordenes[ini:ini + _TROZO17]
        base = tmp_path / f"{nombre}_{k}"
        base.mkdir()
        shim = base / "shim"
        shim.mkdir()
        for n in NOMBRES_SHIM:
            (shim / n).write_bytes(b"#!/bin/sh\necho \"" + n.encode() + b" $*\" >> \"$REG\"\n")
            os.chmod(shim / n, 0o755)
        for n in _SHIM_PROGRAMAS:
            if n in ("chroot", "unshare", "xvfb-run", "dotenv", "npx", "direnv", "poetry", "uv", "strace", "ltrace"):
                (shim / n).write_bytes(("#!/bin/sh\n" + _SALTA).encode())
                os.chmod(shim / n, 0o755)
        cabecera = "".join(f"{n}() {{ echo \"{n} $*\" >> \"$REG\"; }}\nexport -f {n}\n" for n in NOMBRES_SHIM if "." not in n)
        for j, orden in enumerate(trozo):
            (base / f"s_{j}.sh").write_bytes((cabecera + orden + "\n").encode("utf-8"))
        comprobar = "for n in " + " ".join(NOMBRES_SHIM) + "; do case \"$(type -P $n)\" in \"$PWD\"/shim/*) ;; *) echo \"SHIM-NO-$n\"; exit 3;; esac; done\n"
        lanzador = base / "l.sh"
        lanzador.write_bytes(("export PATH=\"$PWD/shim:$PATH\"\nexport GIT_DIR=/inexistente-fix17\n" + comprobar +
                              f"for k in $(seq 0 {len(trozo) - 1}); do export REG=\"$PWD/reg_$k\"; timeout 20 bash \"s_$k.sh\" >/dev/null 2>&1 </dev/null; done\n").encode())
        env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull}
        r = subprocess.run([BASH, str(lanzador)], cwd=str(base), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900,
                           stdin=subprocess.DEVNULL)
        assert "SHIM-NO-" not in r.stdout, f"el shim no es el primero del PATH: {r.stdout[:80]!r}"
        for j in range(len(trozo)):
            f = base / f"reg_{j}"
            registro[ini + j] = f.read_text(encoding="utf-8", errors="replace") if f.exists() else ""
    return registro


@necesita_bash
def test_diferencial17_si_bash_ejecuta_git_el_guardarrail_deniega(tmp_path):
    ordenes = ENVOLTORIO_DETRAS_DE_DESCONOCIDO17
    reg = _ejecutar17(tmp_path, ordenes, "d17")
    ejecutadas = [o for k, o in enumerate(ordenes) if ejecuta_git(reg[k])]
    divergencias = [o for o in ejecutadas if decide(o) is None]
    assert not divergencias, f"bash ejecuta git y el guardarrail PERMITE ({len(divergencias)}): {divergencias[:6]!r}"
    assert len(ejecutadas) >= len(ordenes) * 0.7, f"el arnes apenas ejecuta el corpus ({len(ejecutadas)} de {len(ordenes)})"


@necesita_bash
def test_el_shim_de_los_programas_del_corpus_ejecuta_lo_que_sigue(tmp_path):
    ordenes = [f"{p} git status" for p in PROGRAMAS17] + ["uv run bash -c 'git status'", "chroot / sh -c 'git status'", "echo hola"]
    reg = _ejecutar17(tmp_path, ordenes, "s17")
    assert all(ejecuta_git(reg[k]) for k in range(len(ordenes) - 1)), reg
    assert not ejecuta_git(reg[len(ordenes) - 1])


def test_el_corpus_17_no_esta_vacio_y_sin_duplicados():
    for lista in (GIT_LANZA_GIT17, ENVOLTORIO_DETRAS_DE_DESCONOCIDO17, SALIDAS_RAMA17, PERMITIDAS_RAMA17):
        assert len(lista) == len(set(lista)) and len(lista) > 30, len(lista)
    assert all(re.fullmatch(r"[\x20-\x7e]+", o) for lista in (GIT_LANZA_GIT17, ENVOLTORIO_DETRAS_DE_DESCONOCIDO17, SALIDAS_RAMA17) for o in lista)
