#!/usr/bin/env python3
"""Tests de guardrail-check.py: ciclo fix16 de T-06 (plugin-audit-2, fase 1, intento 16). Ejecuta: pytest -q.

Punto 1: git en CUALQUIER posicion de la orden simple (regla general por clase) + lo concreto (opciones de senal de env, `eval --`/`builtin --`,
`trap`, clusters `-oc`, asignaciones `1=x`, `coproc NAME {`, flock). Punto 2: punto fijo tambien en palabras decodificadas. Punto 3: regla de rama
(`--`, `-B`/`-C`, formas de commit, `symbolic-ref`/`update-ref HEAD`, rama desconocida). Punto 4: rama barata (`.git/HEAD`). Punto 9: los arneses con bash
real deciden «ejecuta git» por el REGISTRO del shim (no por stdout) y el shim cubre `sudo`/`doas`/`su`.
"""
import json
import os
import subprocess

import pytest

from test_guardrail_differential import BASH, necesita_bash
from test_guardrail_fix12 import decide, gc
from test_guardrail_fix16_corpus import BYPASS16, G1_PROBES16, LIMITE16, PROBES16

AQUI = os.path.dirname(os.path.abspath(__file__))
NOMBRES_SHIM = ("git", "GIT", "Git", "git.exe", "GIT.EXE", "sudo", "doas", "su")


def _id(o):
    return o.encode("unicode_escape").decode("ascii")[:70]


# --------------------------------------------------------------------------- punto 1: la clase, no la forma ----
@pytest.mark.parametrize("orden", BYPASS16, ids=[_id(o) for o in BYPASS16])
def test_las_formas_que_bash_ejecuta_como_git_se_deniegan(orden):
    assert decide(orden), orden


ENV_SENAL = [
    "env --default-signal git push --force", "env --block-signal git reset --hard", "nice env --default-signal git switch main",
    "env --b git reset --hard", "env --bl git reset --hard", "env --def git reset --hard", "env --ignore-s git reset --hard",
    "env --ignore-signal=INT git reset --hard", "env --default-signal=TERM git reset --hard",
]


@pytest.mark.parametrize("orden", ENV_SENAL, ids=[_id(o) for o in ENV_SENAL])
def test_las_opciones_de_senal_de_env_llevan_argumento_solo_con_igual(orden):
    assert decide(orden), orden


def test_env_solo_acepta_como_asignacion_un_argumento_con_igual():
    for orden in ("env 1=x git reset --hard", "env A-B=1 GIT reset --hard", "env =x git reset --hard", "FOO=1 env 9=z git switch main"):
        assert decide(orden), orden
    assert decide("env FOO=1 npm test") is None


def test_coproc_con_nombre_y_llave_y_los_dobles_guiones_de_eval_builtin_y_trap():
    for orden in ("coproc NAME { git reset --hard; }", "eval -- 'git reset --hard'", "builtin -- exec git reset --hard",
                  "builtin -- eval 'git reset --hard'", "eval -- cd .. && git restore a.txt", "trap -- 'git reset --hard' EXIT",
                  "trap 'git checkout -- .' EXIT", "git stash && trap 'git checkout -- .' EXIT && true", "trap 'cd ..; git restore a.txt' EXIT"):
        assert decide(orden), orden
    for orden in ("trap 'rm -f /tmp/x' EXIT; npm test", "trap - EXIT", "trap -p", "coproc NAME { sleep 1; }", "eval -- echo hi"):
        assert decide(orden) is None, orden


def test_los_clusters_de_las_shells_con_o_y_O_consumen_su_valor():
    for orden in ("bash -oc errexit 'git reset --hard'", "bash -Oc extglob 'git reset --hard'", "bash -co errexit 'git reset --hard'",
                  "bash -cO extglob 'git reset --hard'", "sh -oc errexit 'GIT checkout main'", "bash -oc posix -- 'git reset --hard'"):
        assert decide(orden), orden
    assert decide("bash -oc errexit 'make test'") is None
    assert decide("bash -c 'git reset --hard'")


def test_flock_con_una_opcion_fuera_de_la_tabla_sigue_buscando_la_cadena():
    for orden in ("flock --verbose /tmp/l -c 'git reset --hard'", "flock --fcntl /tmp/l -c \"g''it reset --hard\"",
                  "flock --nonblocking /tmp/l -c \"g''it reset --hard\""):
        assert decide(orden), orden
    assert decide("flock --verbose /tmp/l -c 'git status'") is None
    assert decide("flock --verbose /tmp/l -c 'echo hola'") is None


def test_envoltorios_fuera_de_la_tabla_chroot_strace_y_otros():
    for orden in ("chroot / git reset --hard", "strace -f git reset --hard", "ltrace git switch main", "unshare -r git reset --hard",
                  "sg root git reset --hard", "numactl -N 0 git reset --hard", "xyz-desconocido --opcion git reset --hard"):
        assert decide(orden), orden


LEGITIMAS16 = [
    "git log --oneline", "man git", "grep -rn 'git reset --hard' docs", "env FOO=1 npm test", "nice -n 5 pytest -q", "time npm run build",
    "npm exec -- prettier --check .", "strace -f node x.js", "echo hola | xargs echo", "builtin -- cd src && ls", "git commit -m 'git reset --hard'",
    "npm install git-url-parse", "echo gitignore", "cat .gitignore", "ls git-hooks", "chroot / ls", "env --default-signal make test",
    "git status", "git diff --stat HEAD", "git checkout main -- src/a.py", "git switch -c feature/otra", "git checkout -b feature/nueva",
    "git stash", "git log -1 --format=%H", "echo '{\"a\": 1}' | jq .", "python3 -c 'print(1)'",
]


@pytest.mark.parametrize("orden", LEGITIMAS16, ids=[_id(o) for o in LEGITIMAS16])
def test_las_ordenes_sin_git_destructivo_siguen_permitidas(orden):
    assert decide(orden) is None, orden


FALSOS_DENY16 = ["echo git reset --hard is blocked", "printf '%s\n' git checkout main", "echo git push --force", "echo prueba git reset --hard"]


@pytest.mark.parametrize("orden", FALSOS_DENY16, ids=[_id(o) for o in FALSOS_DENY16])
def test_falsos_deny_aceptados_echo_y_printf_con_git_sin_comillas_y_una_forma_destructiva(orden):
    """Coste DECLARADO del criterio por clase (git en cualquier posicion de la orden simple): el texto de un `echo`/`printf` con git sin comillas y
    una forma destructiva detras se deniega. Con comillas (`echo 'git reset --hard'`) el texto es una sola palabra y se permite."""
    assert decide(orden), orden


def test_con_comillas_el_texto_de_echo_sigue_permitido():
    assert decide("echo 'git reset --hard'") is None
    assert decide("printf '%s' 'git checkout main'") is None


@pytest.mark.parametrize("orden,clase", LIMITE16, ids=[_id(o) for o, _ in LIMITE16])
def test_limite16_el_guardarrail_no_ve_estas_formas(orden, clase):
    assert decide(orden) is None, (clase, orden)


# --------------------------------------------------------------------------- punto 2: punto fijo en las palabras ----
G1 = [
    "eval \\$\\'$'" + chr(92) + "x5c'x67it\\' reset --hard",
    "echo \"$(time -p case x in *) eval \\$\\'$'" + chr(92) + "x5c'x67it\\' reset --hard;; esac)\"",
    "echo $(time -p case x in *) eval \\$\\'$'" + chr(92) + "x5c'x67it\\' reset --hard;; esac)",
    "echo \"$(time -p case x in *) bash -c \\$\\'$'" + chr(92) + "x5c'x67it\\' reset --hard;; esac)\"",
]


@pytest.mark.parametrize("orden", G1, ids=[_id(o) for o in G1])
def test_un_escape_partido_por_comillas_en_una_lectura_incompleta_se_deniega(orden):
    assert decide(orden), orden


def test_el_punto_fijo_de_las_palabras_es_opaco_si_no_se_estabiliza():
    orden = "echo $(time -p case x in *) bash -c $'" + chr(92) + "x5c" + "x5c" * 11 + "x67it reset --hard';; esac)"
    razon = decide(orden)
    assert razon and "opaca" in razon, razon


# --------------------------------------------------------------------------- punto 3: regla de rama ----
SALIDAS = [
    "git switch main --", "git switch -- main", "git checkout main --", "git checkout - --", "GIT switch -- main", "git checkout -B main",
    "git checkout -B feature/x origin/main", "git checkout -B main origin/main", "git checkout --force-create=main", "git checkout -Bmain",
    "git switch -C main", "git switch --force-create main", "git switch --force-create=main", "git switch -Cmain", "git checkout HEAD~1",
    "git checkout HEAD^", "git checkout abc1234", "git checkout deadbeef01", "git checkout tags/v1.0", "git checkout @{1}", "git switch HEAD~2",
    "git checkout HEAD", "git symbolic-ref HEAD refs/heads/main", "git update-ref HEAD abc1234", "git switch --detach", "git checkout --detach",
    "git switch main -- ", "git checkout master --", "git checkout -fB main", "git switch -fC main",
    "git checkout --conflict merge main", "git checkout --pathspec-from-file f main", "git checkout --opcion-nueva origin/main",
]


@pytest.mark.parametrize("orden", SALIDAS, ids=[_id(o) for o in SALIDAS])
def test_salir_de_la_rama_de_trabajo_se_deniega(orden):
    assert decide(orden), orden


PERMITIDAS_RAMA = [
    "git checkout main -- src/a.py", "git checkout HEAD -- src/a.py", "git checkout abc1234 -- a.py", "git switch -c feature/otra",
    "git switch -c feature/otra main", "git checkout -b nueva", "git checkout -B feature/x", "git checkout feature/x", "git switch feature/x",
    "git checkout feature/y", "git switch feature/y --", "git checkout -B feature/otra", "git switch -C feature/otra",
    "git checkout HEAD src/a.py", "git checkout main src/a.py", "git checkout abc1234 a.py b.py", "git checkout -q main src/a.py",
]


@pytest.mark.parametrize("orden", PERMITIDAS_RAMA, ids=[_id(o) for o in PERMITIDAS_RAMA])
def test_cambios_que_no_salen_de_la_rama_siguen_permitidos(orden):
    assert gc.check_git(orden, "feature/x") is None, orden


def test_con_la_rama_desconocida_se_deniegan_las_ordenes_que_sacan_de_ella():
    for orden in ("git switch main", "git checkout master", "git checkout -B main", "git checkout HEAD~1", "git switch --detach", "git checkout -"):
        assert gc.check_git(orden, None), orden
    for orden in ("git status", "git switch -c x", "git checkout -b x", "git checkout main -- a.py", "git log"):
        assert gc.check_git(orden, None) is None, orden


def test_en_main_o_con_head_suelto_no_se_aplica_la_regla_de_salida():
    assert gc.check_git("git switch main", "main") is None
    assert gc.check_git("git checkout HEAD~1", "HEAD") is None


# --------------------------------------------------------------------------- punto 4: rama barata ----
def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)


@pytest.fixture
def repo(tmp_path):
    p = tmp_path / "r"
    p.mkdir()
    assert _git(p, "init", "-q", "-b", "feature/x").returncode == 0
    for k, v in (("user.name", "t"), ("user.email", "t@t")):
        _git(p, "config", k, v)
    (p / "a.txt").write_text("a")
    _git(p, "add", "a.txt")
    assert _git(p, "commit", "-q", "-m", "c").returncode == 0, "commit"
    return p


def test_rama_barata_lee_head_sin_ejecutar_git(repo, monkeypatch):
    def prohibido(*a, **k):
        raise AssertionError("rama_barata no debe lanzar procesos")
    monkeypatch.setattr(gc.subprocess, "run", prohibido)
    monkeypatch.delenv("GIT_DIR", raising=False)
    monkeypatch.delenv("GIT_WORK_TREE", raising=False)
    assert gc.rama_barata(str(repo)) == "feature/x"
    (repo / "sub").mkdir()
    assert gc.rama_barata(str(repo / "sub")) == "feature/x", "desde un subdirectorio"


def test_rama_barata_head_suelto_worktree_y_submodulo(repo, tmp_path, monkeypatch):
    monkeypatch.delenv("GIT_DIR", raising=False)
    monkeypatch.delenv("GIT_WORK_TREE", raising=False)
    sha = _git(repo, "rev-parse", "HEAD").stdout.strip()
    wt = tmp_path / "wt"
    assert _git(repo, "worktree", "add", "-q", "-b", "feature/wt", str(wt)).returncode == 0
    assert gc.rama_barata(str(wt)) == "feature/wt"
    assert gc.rama_barata(str(repo)) == "feature/x"
    # `.git` como fichero `gitdir:` relativo (submodulos): se resuelve contra el directorio del fichero
    sm = tmp_path / "sm"
    sm.mkdir()
    (tmp_path / "gd").mkdir()
    gd = repo / ".git"
    (sm / ".git").write_text("gitdir: " + os.path.relpath(gd, sm) + "\n")
    assert gc.rama_barata(str(sm)) == "feature/x"
    assert _git(repo, "checkout", "-q", "--detach", sha).returncode == 0
    assert gc.rama_barata(str(repo)) == "HEAD"


def test_rama_barata_recurre_a_current_branch_si_no_es_concluyente(repo, tmp_path, monkeypatch):
    llamadas = []
    monkeypatch.setattr(gc, "current_branch", lambda d, timeout=5: llamadas.append(d) or "desde-git")
    monkeypatch.delenv("GIT_DIR", raising=False)
    monkeypatch.delenv("GIT_WORK_TREE", raising=False)
    assert gc.rama_barata(str(repo)) == "feature/x" and not llamadas
    monkeypatch.setenv("GIT_DIR", str(repo / ".git"))
    assert gc.rama_barata(str(repo)) == "desde-git" and llamadas, "con GIT_DIR en el entorno no es concluyente"
    monkeypatch.delenv("GIT_DIR")
    monkeypatch.setenv("GIT_WORK_TREE", str(repo))
    assert gc.rama_barata(str(repo)) == "desde-git"
    monkeypatch.delenv("GIT_WORK_TREE")
    (repo / ".git" / "HEAD").write_text("ref: refs/heads/.invalid\n")                  # reftable
    assert gc.rama_barata(str(repo)) == "desde-git"
    (repo / ".git" / "HEAD").write_bytes(b"\xff\xfe basura")
    assert gc.rama_barata(str(repo)) == "desde-git"
    sin_git = tmp_path / "sin-git"
    sin_git.mkdir()
    assert gc.rama_barata(str(sin_git)) == "desde-git", "sin .git en ningun ancestro"


def test_current_branch_conserva_su_contrato(repo, monkeypatch):
    monkeypatch.delenv("GIT_DIR", raising=False)
    assert gc.current_branch(str(repo)) == "feature/x"


def test_el_hook_usa_la_rama_barata_y_no_lanza_git(repo, tmp_path):
    """`main()` consulta la rama con `rama_barata`: un `git` falso delante en el PATH no se ejecuta, y la salida de rama se deniega igual."""
    shim = tmp_path / "shim"
    shim.mkdir()
    reg = tmp_path / "git.reg"
    (shim / "git").write_bytes(b"#!/bin/sh\necho ran >> \"" + str(reg).replace("\\", "/").encode() + b"\"\nexit 1\n")
    os.chmod(shim / "git", 0o755)
    env = {**os.environ, "PATH": str(shim) + os.pathsep + os.environ["PATH"]}
    for k in ("GIT_DIR", "GIT_WORK_TREE", "CLAUDE_AGENT_NAME"):
        env.pop(k, None)
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "echo hola; git switch main"}})
    r = subprocess.run([os.sys.executable, os.path.join(AQUI, "guardrail-check.py"), "pre-tool", "--project-dir", str(repo)], input=payload, env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    assert "rama de trabajo" in r.stdout, (r.stdout, r.stderr)
    assert not reg.exists(), "el guardarrail lanzo git para consultar la rama"


# --------------------------------------------------------------------------- punto 9: arnes con bash real ----
_TROZO16 = 80      # ordenes por lanzador de bash: con la maquina saturada (12 bucles de CPU) 331 formas pasaban de los 900 s de UN solo lanzador (fix16)


def _ejecutar16(tmp_path, ordenes, nombre):
    """`_ejecutar16_trozo` por trozos de `_TROZO16` ordenes, cada uno con su lanzador y su plazo; devuelve el registro de todas, en orden."""
    registro = {}
    for k, ini in enumerate(range(0, len(ordenes), _TROZO16)):
        trozo = ordenes[ini:ini + _TROZO16]
        for j, texto in _ejecutar16_trozo(tmp_path, trozo, f"{nombre}_{k}").items():
            registro[ini + j] = texto
    return registro


def _ejecutar16_trozo(tmp_path, ordenes, nombre):
    """Cada orden en su `.sh`, con `git`, `GIT`, `Git`, `git.exe`, `GIT.EXE` FALSOS y tambien `sudo`, `doas` y `su` (Git Bash ve el `sudo` de Windows 11 y NO se puede ejecutar).
    Los shims y las funciones exportadas anotan en un REGISTRO (un fichero por orden): «ejecuta git» se decide por el registro, no por stdout.
    Devuelve {indice: texto del registro}: `ejecuta_git` mira solo las lineas de los shims de git y `ejecuta_priv` las de `sudo`/`doas`/`su`."""
    base = tmp_path / nombre
    base.mkdir()
    shim = base / "shim"
    shim.mkdir()
    for n in NOMBRES_SHIM:
        (shim / n).write_bytes(b"#!/bin/sh\necho \"" + n.encode() + b" $*\" >> \"$REG\"\n")
        os.chmod(shim / n, 0o755)
    cabecera = "".join(f"{n}() {{ echo \"{n} $*\" >> \"$REG\"; }}\nexport -f {n}\n" for n in NOMBRES_SHIM if "." not in n)
    for k, orden in enumerate(ordenes):
        (base / f"s_{k}.sh").write_bytes((cabecera + orden + "\n").encode("utf-8"))
    comprobar = "for n in " + " ".join(NOMBRES_SHIM) + "; do case \"$(type -P $n)\" in \"$PWD\"/shim/*) ;; *) echo \"SHIM-NO-$n\"; exit 3;; esac; done\n"
    lanzador = base / "l.sh"
    lanzador.write_bytes(("export PATH=\"$PWD/shim:$PATH\"\nexport GIT_DIR=/inexistente-fix16\n" + comprobar +
                          f"for k in $(seq 0 {len(ordenes) - 1}); do export REG=\"$PWD/reg_$k\"; timeout 20 bash \"s_$k.sh\" >/dev/null 2>&1 </dev/null; done\n").encode())
    env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull}
    r = subprocess.run([BASH, str(lanzador)], cwd=str(base), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900,
                       stdin=subprocess.DEVNULL)
    assert "SHIM-NO-" not in r.stdout, f"el shim no es el primero del PATH: {r.stdout[:80]!r}"
    return {k: ((base / f"reg_{k}").read_text(encoding="utf-8", errors="replace") if (base / f"reg_{k}").exists() else "") for k in range(len(ordenes))}


def ejecuta_git(registro):
    return any(linea.split(" ", 1)[0].lower().removesuffix(".exe") == "git" for linea in registro.splitlines())


def ejecuta_priv(registro):
    return any(linea.split(" ", 1)[0] in ("sudo", "doas", "su") for linea in registro.splitlines())


@necesita_bash
def test_diferencial16_si_bash_ejecuta_git_el_guardarrail_deniega(tmp_path):
    corre = {k: ejecuta_git(v) for k, v in _ejecutar16(tmp_path, BYPASS16, "d16").items()}
    ejecutadas = [o for k, o in enumerate(BYPASS16) if corre[k]]
    divergencias = [o for o in ejecutadas if decide(o) is None]
    assert not divergencias, f"bash ejecuta git y el guardarrail PERMITE ({len(divergencias)}): {divergencias[:6]!r}"
    assert len(ejecutadas) >= len(BYPASS16) * 0.9, f"el arnes apenas ejecuta el corpus ({len(ejecutadas)} de {len(BYPASS16)})"


@necesita_bash
def test_el_registro_del_shim_ve_lo_que_stdout_no_ve(tmp_path):
    """Una orden que ejecuta git con stdout y stderr redirigidos a /dev/null SI se registra (el arnes de fix15 la daba por no ejecutada)."""
    ordenes = ["git status >/dev/null 2>&1", "echo hola", "sudo git status >/dev/null 2>&1", "doas git status", "su -c 'git status'"]
    reg = _ejecutar16(tmp_path, ordenes, "r16")
    assert ejecuta_git(reg[0]) and not reg[1] and ejecuta_priv(reg[2]) and ejecuta_priv(reg[3]) and ejecuta_priv(reg[4]) and not ejecuta_git(reg[2]), reg


@necesita_bash
def test_el_shim_cubre_las_cinco_grafias_de_git_y_sudo_doas_su(tmp_path):
    ordenes = [n + " status" for n in NOMBRES_SHIM]
    reg = _ejecutar16(tmp_path, ordenes, "s16")
    assert all(ejecuta_git(reg[k]) if k < 5 else ejecuta_priv(reg[k]) for k in range(len(ordenes))), reg


@necesita_bash
def test_diferencial16_las_sondas_de_las_lentes_a_y_b_con_bash_real(tmp_path):
    """Las 97 sondas de la lente B y las 4 de la lente A: lo que bash ejecuta (registro del shim) el guardarrail lo deniega."""
    ordenes = PROBES16 + G1_PROBES16
    corre = {k: ejecuta_git(v) for k, v in _ejecutar16(tmp_path, ordenes, "p16").items()}
    ejecutadas = [o for k, o in enumerate(ordenes) if corre[k]]
    divergencias = [o for o in ejecutadas if decide(o) is None]
    assert not divergencias, f"bash ejecuta git y el guardarrail PERMITE ({len(divergencias)}): {divergencias[:6]!r}"
    assert len(ejecutadas) >= 30, f"el arnes apenas ejecuta las sondas ({len(ejecutadas)} de {len(ordenes)})"
    # lo que el guardarrail permite, bash tampoco lo ejecuta como git destructivo: todas las sondas son destructivas, asi que ninguna se permite salvo las que bash no ejecuta
    permitidas = [o for o in ordenes if decide(o) is None]
    assert all(not corre[ordenes.index(o)] for o in permitidas), permitidas
