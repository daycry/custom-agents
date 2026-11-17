#!/usr/bin/env python3
"""Tests de guardrail-check.py: ciclo fix18 de T-06 (plugin-audit-2, fase 1, intento 18). Ejecuta: pytest -q.

Punto 1: rama por lista blanca sin ambiguedad de ruta (`git checkout main` con un directorio `main`; las refs se leen de `.git`, las rutas contra el `cwd` del payload) y los
movimientos de `refs/heads/*` como clase. Punto 2: subcomandos que destruyen y opciones que ejecutan una shell. Punto 3: `commondir` validado. Los efectos se comprueban con git real.
"""
import pytest

from test_guardrail_fix12 import gc
from test_guardrail_fix16 import _git, repo  # noqa: F401  (`repo` es un fixture)
from test_guardrail_fix18_corpus import (CODIGO18, DESTRUYEN18, EN_OTRO_DIRECTORIO18, LIMITE18, MUEVEN_RAMAS18, PERMITIDAS18, RAMA_COMO_RUTA18)


def _id(o):
    return o.encode("unicode_escape").decode("ascii")[:70]


def _sin_git_env(monkeypatch):
    for k in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"):
        monkeypatch.delenv(k, raising=False)


@pytest.fixture
def repo18(repo, monkeypatch):
    """`feature/x` con las ramas `main`, `master`, `docs`, `feature/y`, el tag `v1.0`, la remota `origin/main` y un DIRECTORIO con cada nombre."""
    for r in ("main", "master", "docs", "feature/y"):
        assert _git(repo, "branch", r).returncode == 0
    assert _git(repo, "tag", "v1.0").returncode == 0
    assert _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD").returncode == 0
    for d in ("main", "master", "docs", "origin/main", "feature/y", "v1.0", "src"):
        (repo / d).mkdir(parents=True, exist_ok=True)
        (repo / d / "k.txt").write_text("k")
    monkeypatch.chdir(repo)
    _sin_git_env(monkeypatch)
    return repo


# --------------------------------------------------------------------------- gap 1: rama con nombre de ruta ----
@pytest.mark.parametrize("orden", RAMA_COMO_RUTA18, ids=[_id(o) for o in RAMA_COMO_RUTA18])
def test_una_rama_con_nombre_de_ruta_se_deniega(repo18, orden):
    assert gc.check_git(orden, "feature/x"), orden


def test_git_real_cambia_de_rama_con_un_directorio_homonimo(repo18):
    assert _git(repo18, "checkout", "main").returncode == 0
    assert _git(repo18, "symbolic-ref", "--short", "HEAD").stdout.strip() == "main", "git real SI cambia a la rama, no a la ruta"


@pytest.mark.parametrize("orden", ["git checkout -- main", "git checkout HEAD", "git checkout main -- a.txt", "git checkout src", "git checkout src/k.txt", "git checkout a.txt",
                                    "git checkout feature/x", "git checkout HEAD -- a.txt", "git checkout restore-me.txt"])
def test_una_ruta_que_no_es_ref_o_va_tras_guiones_se_permite(repo18, orden):
    (repo18 / "restore-me.txt").write_text("x")
    assert gc.check_git(orden, "feature/x") is None, orden


def test_las_rutas_se_resuelven_contra_el_cwd_del_payload_y_las_refs_del_repositorio_del_payload(repo18, tmp_path_factory, monkeypatch):
    otro = tmp_path_factory.mktemp("otro-cwd")
    monkeypatch.chdir(otro)
    payload = {"tool_name": "Bash", "cwd": str(repo18), "tool_input": {"command": "git checkout src"}}
    assert gc.decide(payload, str(repo18), branch="feature/x") is None, "`src` existe en el cwd del payload y no es una ref"
    payload["tool_input"]["command"] = "git checkout main"
    assert gc.decide(payload, str(repo18), branch="feature/x"), "`main` es una rama del repositorio del payload"
    payload["tool_input"]["command"] = "git checkout a.txt"
    assert gc.decide(payload, str(repo18), branch="feature/x") is None, "`a.txt` existe en el cwd del payload, no en el del proceso"


def test_una_ref_empaquetada_cuenta_como_ref(repo18):
    assert _git(repo18, "pack-refs", "--all").returncode == 0
    assert not (repo18 / ".git" / "refs" / "heads" / "docs").exists()
    assert gc.check_git("git checkout docs", "feature/x")
    assert gc.check_git("git checkout v1.0 --", "feature/x")


def test_con_la_ref_ilegible_una_rama_principal_se_deniega_igual(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _sin_git_env(monkeypatch)
    (tmp_path / "main").mkdir()
    (tmp_path / "src").mkdir()
    assert gc.check_git("git checkout main", "feature/x"), "sin repositorio legible no se puede descartar que `main` sea una rama"
    assert gc.check_git("git checkout src", "feature/x") is None, "una ruta que existe y no parece una rama principal se permite"


# --------------------------------------------------------------------------- gaps 2, 7 y 9: destruyen o ejecutan shell ----
@pytest.mark.parametrize("orden", DESTRUYEN18, ids=[_id(o) for o in DESTRUYEN18])
def test_los_subcomandos_que_destruyen_se_deniegan(orden):
    assert gc.check_git(orden, "feature/x"), orden


@pytest.mark.parametrize("orden", CODIGO18, ids=[_id(o) for o in CODIGO18])
def test_las_opciones_cuyo_valor_ejecuta_una_shell_se_analizan_como_codigo(orden):
    assert gc.check_git(orden, "feature/x"), orden


def test_git_real_submodule_update_force_pierde_cambios_y_se_deniega(tmp_path):
    sub, sup = tmp_path / "sub", tmp_path / "sup"
    for d in (sub, sup):
        d.mkdir()
        assert _git(d, "init", "-q", "-b", "feature/x").returncode == 0
        for k, v in (("user.name", "t"), ("user.email", "t@t"), ("protocol.file.allow", "always")):
            _git(d, "config", k, v)
    (sub / "a.txt").write_text("a")
    _git(sub, "add", "a.txt")
    assert _git(sub, "commit", "-q", "-m", "c").returncode == 0
    assert _git(sup, "-c", "protocol.file.allow=always", "submodule", "add", "-q", str(sub), "s").returncode == 0
    (sup / "s" / "a.txt").write_text("TRABAJO SIN COMITEAR")
    assert gc.check_git("git submodule update --init --recursive --force", "feature/x")
    assert _git(sup, "submodule", "update", "--init", "--recursive", "--force").returncode == 0
    assert (sup / "s" / "a.txt").read_text() == "a", "con git real la forma borra el cambio sin comitear del submodulo"


# --------------------------------------------------------------------------- gap 6: movimientos de refs/heads/* ----
@pytest.mark.parametrize("orden", MUEVEN_RAMAS18, ids=[_id(o) for o in MUEVEN_RAMAS18])
def test_los_movimientos_de_refs_heads_se_deniegan(orden):
    assert gc.check_git(orden, "feature/x"), orden


@pytest.fixture
def con_worktrees(tmp_path, monkeypatch):
    """Repositorio principal con HEAD en `main` y un worktree en `feature/x`: la rama de `-C <dir>` se lee de ese directorio."""
    prin = tmp_path / "p"
    prin.mkdir()
    assert _git(prin, "init", "-q", "-b", "main").returncode == 0
    for k, v in (("user.name", "t"), ("user.email", "t@t")):
        _git(prin, "config", k, v)
    (prin / "a.txt").write_text("a")
    _git(prin, "add", "a.txt")
    assert _git(prin, "commit", "-q", "-m", "c").returncode == 0
    wt = tmp_path / "wt-feature"
    assert _git(prin, "worktree", "add", "-q", "-b", "feature/x", str(wt)).returncode == 0
    monkeypatch.chdir(wt)
    _sin_git_env(monkeypatch)
    return str(prin).replace("\\", "/"), str(wt).replace("\\", "/")


@pytest.mark.parametrize("orden", EN_OTRO_DIRECTORIO18, ids=[_id(o) for o in EN_OTRO_DIRECTORIO18])
def test_con_C_el_head_que_cuenta_es_el_del_directorio(con_worktrees, orden):
    prin, wt = con_worktrees
    assert gc.check_git(orden.replace("WT-MAIN", prin), "feature/x"), "un worktree con HEAD en `main`: modificar su historia es integrar"
    assert gc.check_git(orden.replace("WT-MAIN", wt), "feature/x") is None, "el mismo cambio en el worktree de la rama de trabajo es normal"


@pytest.mark.parametrize("orden", PERMITIDAS18, ids=[_id(o) for o in PERMITIDAS18])
def test_lo_cotidiano_del_implementer_sigue_permitido(repo18, orden):
    assert gc.check_git(orden, "feature/x") is None, orden


def test_git_real_fetch_con_mas_mueve_main_y_se_deniega(repo18):
    assert _git(repo18, "commit", "-q", "--allow-empty", "-m", "otro").returncode == 0
    antes = _git(repo18, "rev-parse", "main").stdout.strip()
    assert gc.check_git("git fetch . +feature/x:main", "feature/x")
    assert _git(repo18, "fetch", ".", "+feature/x:main").returncode == 0
    assert _git(repo18, "rev-parse", "main").stdout.strip() != antes, "con git real `fetch . +x:main` mueve main"


@pytest.mark.parametrize("orden,motivo", LIMITE18, ids=[_id(o) for o, _ in LIMITE18])
def test_limite18_el_guardarrail_no_ve_las_cadenas_de_programas_fuera_de_la_tabla(orden, motivo):
    assert gc.check_git(orden, "feature/x") is None, (motivo, orden)


# --------------------------------------------------------------------------- gap 8: commondir validado ----
def test_commondir_que_no_apunta_a_un_repositorio_no_es_un_repositorio(tmp_path, monkeypatch):
    _sin_git_env(monkeypatch)
    falso = tmp_path / "proj"
    (falso / ".git").mkdir(parents=True)
    (falso / ".git" / "HEAD").write_text("ref: refs/heads/feature/x\n")
    for contenido in ("no-existe\n", "..\n"):
        (falso / ".git" / "commondir").write_text(contenido)
        assert gc._es_repositorio(str(falso / ".git")) is False, contenido
    llamadas = []
    monkeypatch.setattr(gc, "current_branch", lambda d, timeout=5: llamadas.append(d) or "main")
    assert gc.rama_barata(str(falso)) == "main" and llamadas


def test_commondir_valido_de_un_worktree_sigue_siendo_repositorio(repo, tmp_path, monkeypatch):
    _sin_git_env(monkeypatch)
    wt = tmp_path / "wt"
    assert _git(repo, "worktree", "add", "-q", "-b", "feature/wt", str(wt)).returncode == 0
    monkeypatch.setattr(gc, "current_branch", lambda d, timeout=5: (_ for _ in ()).throw(AssertionError("no debe lanzar git")))
    assert gc.rama_barata(str(wt)) == "feature/wt"


# --------------------------------------------------------------------------- coste ----
def test_la_lista_blanca_de_rama_no_lanza_git(repo18, monkeypatch):
    def prohibido(*a, **k):
        raise AssertionError("la resolucion de refs no debe lanzar procesos")
    monkeypatch.setattr(gc.subprocess, "run", prohibido)
    assert gc.check_git("git checkout main", "feature/x")
    assert gc.check_git("git checkout src", "feature/x") is None


def test_el_corpus_18_no_esta_vacio_y_sin_duplicados():
    for lista in (DESTRUYEN18, CODIGO18, MUEVEN_RAMAS18, RAMA_COMO_RUTA18, PERMITIDAS18, EN_OTRO_DIRECTORIO18):
        assert len(lista) == len(set(lista)) and len(lista) > 8, len(lista)
    assert all(o.isascii() for lista in (DESTRUYEN18, CODIGO18, MUEVEN_RAMAS18, PERMITIDAS18) for o in lista)
