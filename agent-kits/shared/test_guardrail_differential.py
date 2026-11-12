#!/usr/bin/env python3
"""Test DIFERENCIAL del guardarraíl del implementer contra bash real (T-06 fix5, plugin-audit-2, fase 1).

El guardarraíl lee la orden con un tokenizador propio; bash la lee con el suyo. Cada hueco de las
revisiones de los intentos 4 y 5 fue un desacuerdo entre los dos. Este corpus junta TODAS las sondas
de las lentes y las ejecuta en un repo temporal con centinela:

* BAD: órdenes que bash ejecuta y que llegan a `git restore`/`reset --hard`/`push --force`. El guardarraíl
  debe denegarlas. Una prueba de paridad confirma, contra bash real, que cada una cambia de verdad el
  centinela (si no, el corpus no probaría nada).
* LEGIT: órdenes del flujo normal (commit con heredoc de comilla impar, `git -C <dir> status`, `cd <propio
  dir>`…). El guardarraíl debe permitirlas.
* Propiedad general: si el guardarraíl PERMITE una orden, bash no debe haber tocado el centinela.

Sin bash real (Windows sin Git Bash, p. ej.) las pruebas que lo ejecutan se saltan con motivo; en Windows
se usa SIEMPRE el bash de Git, nunca el de WSL.
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
spec = importlib.util.spec_from_file_location("guardrail_check_dif", os.path.join(HERE, "guardrail-check.py"))
gc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gc)


def _bash():
    if os.name == "nt":
        for base in (os.environ.get("ProgramFiles"), os.environ.get("ProgramW6432"), r"C:\Program Files"):
            if base:
                ruta = os.path.join(base, "Git", "usr", "bin", "bash.exe")
                if os.path.isfile(ruta):
                    return ruta
        return None
    return shutil.which("bash")


BASH = _bash()
GIT = shutil.which("git")
necesita_bash = pytest.mark.skipif(not (BASH and GIT), reason="sin bash real (o sin git): el corpus no puede ejecutarse")

D_RESTORE = "git restore ."
D_PUSH = "git push --force origin master"

# --------------------------------------------------------------------------- corpus ----
# `{D}` = la orden destructiva; `{proj}` = el directorio de trabajo (para `cd`/`git -C` propios).
BAD = [
    # --- sondas de la lente B/C del intento 5 (scratchpad/lc5/probe.py)
    "{D}",
    "cat <<EOF; {D}\nbody\nEOF",
    "echo '<<EOF'\n{D}",
    "x=$(cat <<EOF\nhola\nEOF\n)\n{D}",
    "cat <<-EOF\n\tbody\n\tEOF\n{D}",
    "cat <<A <<B\na\nA\nb\nB\n{D}",
    "echo $((1<<2))\n{D}",
    "x=$(( 1 << 3 ))\n{D}",
    "(( y = 1<<2 ))\n{D}",
    "cat <<\\EOF\nhola\nEOF\n{D}",
    'cat <<E"OF"\nhola\nEOF\n{D}',
    "cat <<EOF | bash; true\n{D}\nEOF",
    "bash <<EOF; true\n{D}\nEOF",
    "bash <<EOF\n{D}\nEOF",
    "eval \"$(cat <<'EOF'\n{D}\nEOF\n)\"",
    "bash -c \"$(cat <<'EOF'\n{D}\nEOF\n)\"",
    ". /dev/stdin <<EOF\n{D}\nEOF",
    "echo $((2<<1))\n{D}",
    "cd .. && {D}",
    "env -C .. {D}",
    "command cd .. ; {D}",
    "{ cd ..; }; {D}",
    # --- sondas de la lente A/B del intento 5 (scratchpad/vf5/p.py)
    'cat <<<"hola"\n{D}',
    "cat <<< hola\n{D}",
    'x=$(( 1 << 2 ))\n{D}',
    "bash <<EOF | tee log\n{D}\nEOF",
    "bash <<EOF && echo ok\n{D}\nEOF",
    "env bash <<EOF\n{D}\nEOF",
    "bash -s <<EOF\n{D}\nEOF",
    "cat <<EOF | bash\n{D}\nEOF",
    "bash <<A; cat <<B\n{D}\nA\nx\nB",
    "cat <<'EOF' > f\nit's\nEOF\n{D}",
    'echo "<<EOF"\n{D}',
    "cat <<EOF\nx\nEOF\n{D}",
    "cat <<EOF\nhi\nEOF\n{D}",
    # --- sondas de las lentes (scratchpad/probe_gc.py, probe_hook.py)
    "cat <<EOF\nit's\nEOF\n{D}",
    "A=1 bash <<EOF\n{D}\nEOF",
    "command bash <<EOF\n{D}\nEOF",
    "exec bash <<EOF\n{D}\nEOF",
    "time bash <<EOF\n{D}\nEOF",
    "/bin/bash <<EOF\n{D}\nEOF",
    "cat <<EOF | env bash\n{D}\nEOF",
    "bash < /dev/stdin <<EOF\n{D}\nEOF",
    "xargs -0 <<EOF\nx\nEOF\n{D}",
    "bash <<'EOF'\ncd ..\n{D}\nEOF",
    "cd .. && bash <<EOF\n{D}\nEOF",
    "cat <<EOF\n$({D})\nEOF",
    "cat <<EOF\n`{D}`\nEOF",
    "cat <<EOF >f\nit's\nEOF\necho ok; {D}",
    "bash <<EOF 2>&1\n{D}\nEOF",
    "cat <<EOF; {D}\nit's",
    "cat <<EOF; {D}\nsin cierre",
    # --- gap 6: comilla doble impar dentro de `git commit -m "$(cat <<'EOF' …)"`
    "git commit -m \"$(cat <<'EOF'\nodd \" quote\nrest\nEOF\n)\"\n{D}",
    "git commit -m \"$(cat <<'EOF'\nmensaje\nEOF\n)\"\n{D}",
    # --- sustituciones de órdenes que bash ejecuta
    'echo "$({D})"',
    'echo "`{D}`"',
    "echo `{D}`",
    "echo $({D})",
    "echo $((1<<2)) && {D}",
    "x=$((1<<2)); {D}",
    "cat <<EOF >f\n$(echo hi)\nEOF\n{D}",
    # --- cambio de base en cualquier punto
    "cd ..; {D}",
    "pushd ..; {D}",
    "(cd .. && {D})",
    "cd ..\n{D}",
    "builtin cd .. && {D}",
    "time cd .. ; {D}",
    "! cd ..; {D}",
    "A=1 env -C .. {D}",
    "cd .. && bash -c '{D}'",
    "let \"x<<=2\"\n{D}",
]

# En esta lista el efecto no se reproduce en un bash de Git for Windows (sin `sudo`/`zsh`); no se piden
# paridad, pero siguen siendo BAD para el guardarraíl.
SIN_PARIDAD = {"sudo bash <<EOF\n{D}\nEOF", "zsh <<EOF\n{D}\nEOF"}
BAD += sorted(SIN_PARIDAD)

LEGIT = [
    "git commit -F - <<'EOF'\ndon't \"x\nEOF\ngit status",
    "git add . && git commit -F - <<'EOF'\nmensaje con 'apóstrofos' y \"comillas impares\nEOF",
    "git commit -m \"$(cat <<'EOF'\nmensaje don't\nEOF\n)\"",
    "git commit -m \"$(cat <<'EOF'\nmensaje con \" comilla impar\nsegunda línea\nEOF\n)\"",
    "git commit -F - <<EOF\ndon't\nEOF\ngit status",
    "git -C {proj} status",
    "git -C {proj} log --oneline -3",
    "cd {proj} && git status",
    "cd {proj} && git restore src/a.py",
    "cd . && git restore src/a.py",
    "echo $((1<<2))\ngit status",
    "echo $((1<<2)); git restore src/a.py",
    "echo cd; git restore src/a.py",
    "git commit -m 'cd' && git restore src/a.py",
    "git restore src/cd",
    "type cd && git restore src/a.py",
    "cat <<EOF\nx\nEOF",
    "cat <<'EOF'\n$(git restore .)\nEOF",
    "cat <<'EOF'\ngit restore .\nEOF\ngit status",
    "git log <<< 'git restore .'",
    "cat > f.py <<'EOF'\nprint('x')\nEOF\ngit add f.py && git commit -m x",
    "python3 - <<'EOF'\nprint(1)\nEOF",
    "echo env; git status",
    "echo git; echo hecho",
    "ls -la && git diff --stat",
]


def _expandir(plantilla, d, proj):
    return plantilla.replace("{D}", d).replace("{proj}", proj)


def _git(cwd, *args, env=None):
    base = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@t", "GIT_TERMINAL_PROMPT": "0"}
    base.update(env or {})
    return subprocess.run(["git", "-c", "core.autocrlf=false", *args], cwd=cwd, env=base, capture_output=True,
                          text=True, timeout=60)


@pytest.fixture(scope="module")
def plantilla_repo(tmp_path_factory):
    """outer/ (repo con b.txt sucio) ⊃ outer/proj/ (repo con a.txt y src/a.py sucios, remoto divergente)."""
    if not (BASH and GIT):
        pytest.skip("sin bash real o sin git")
    base = tmp_path_factory.mktemp("dif")
    outer = base / "outer"
    proj = outer / "proj"
    remoto = base / "remoto.git"
    proj.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "--bare", "-b", "master", str(remoto)], check=True, capture_output=True)
    for repo, nombre in ((outer, "b.txt"), (proj, "a.txt")):
        _git(repo, "init", "-q", "-b", "master")
        (repo / nombre).write_text("orig\n")
    (proj / "src").mkdir()
    (proj / "src" / "a.py").write_text("orig\n")
    _git(proj, "add", "-A")
    _git(proj, "commit", "-q", "-m", "c1")
    _git(proj, "remote", "add", "origin", str(remoto))
    assert _git(proj, "push", "-q", "origin", "master").returncode == 0
    _git(proj, "commit", "-q", "--amend", "-m", "c2")          # local divergente: solo `--force` entra
    _git(outer, "add", "b.txt")
    _git(outer, "commit", "-q", "-m", "o1")
    (outer / "b.txt").write_text("sucio\n")
    (proj / "a.txt").write_text("sucio\n")
    (proj / "src" / "a.py").write_text("sucio\n")
    return base


def _estado(base):
    outer, proj, remoto = base / "outer", base / "outer" / "proj", base / "remoto.git"
    return (
        (outer / "b.txt").read_text(), (proj / "a.txt").read_text(), (proj / "src" / "a.py").read_text(),
        _git(proj, "rev-parse", "HEAD").stdout.strip(),
        subprocess.run(["git", "--git-dir", str(remoto), "rev-parse", "master"], capture_output=True,
                       text=True).stdout.strip(),
    )


def _ejecutar_en_bash(plantilla_repo, tmp_path, orden):
    """Copia el repo, ejecuta `orden` con bash real dentro de proj y devuelve (estado_antes, estado_despues)."""
    copia = tmp_path / "w"
    shutil.copytree(plantilla_repo, copia)
    # el `remote` apunta a la copia original: se rehace para que `push` actúe sobre la copia
    proj = copia / "outer" / "proj"
    _git(proj, "remote", "set-url", "origin", str(copia / "remoto.git"))
    antes = _estado(copia)
    script = copia / "orden.sh"
    script.write_bytes(orden.encode("utf-8"))
    env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull,
           "GIT_CEILING_DIRECTORIES": str(copia), "GIT_TERMINAL_PROMPT": "0",
           "GIT_EDITOR": "true", "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
    subprocess.run([BASH, str(script)], cwd=str(proj), env=env, capture_output=True, text=True, timeout=60,
                   stdin=subprocess.DEVNULL)
    return antes, _estado(copia), copia


@pytest.fixture
def en_proj(plantilla_repo, monkeypatch):
    proj = plantilla_repo / "outer" / "proj"
    monkeypatch.chdir(proj)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(proj))
    return proj


def _decide(orden):
    return gc.check_git(orden, "feat/x")


def _id(plantilla):
    return plantilla.replace("\n", "⏎")[:60]


# --------------------------------------------------------------------------- pruebas ----
@pytest.mark.parametrize("d", [D_RESTORE, D_PUSH], ids=["restore", "push-force"])
@pytest.mark.parametrize("plantilla", BAD, ids=[_id(p) for p in BAD])
def test_bad_el_guardarrail_deniega_lo_que_bash_ejecuta(plantilla, d, en_proj):
    orden = _expandir(plantilla, d, en_proj.as_posix())
    assert _decide(orden), f"DENY esperado: {orden!r}"


@pytest.mark.parametrize("plantilla", LEGIT, ids=[_id(p) for p in LEGIT])
def test_legit_el_flujo_normal_sigue_permitido(plantilla, en_proj):
    orden = _expandir(plantilla, D_RESTORE, en_proj.as_posix())
    razon = _decide(orden)
    assert razon is None, f"ALLOW esperado: {orden!r} -> {razon}"


@necesita_bash
def test_el_centinela_detecta_lo_que_bash_ejecuta(plantilla_repo, tmp_path):
    """Control del arnés: una `git restore .` real cambia el centinela; una orden inocua, no."""
    antes, despues, _ = _ejecutar_en_bash(plantilla_repo, tmp_path / "a", D_RESTORE)
    assert antes != despues
    antes, despues, _ = _ejecutar_en_bash(plantilla_repo, tmp_path / "b", "git status")
    assert antes == despues
    antes, despues, _ = _ejecutar_en_bash(plantilla_repo, tmp_path / "c", D_PUSH)
    assert antes != despues


@necesita_bash
@pytest.mark.parametrize("plantilla", [p for p in BAD if p not in SIN_PARIDAD],
                         ids=[_id(p) for p in BAD if p not in SIN_PARIDAD])
def test_paridad_cada_bad_cambia_el_centinela_en_bash_real(plantilla, plantilla_repo, tmp_path):
    """Si bash NO ejecuta el efecto, la entrada del corpus no prueba nada: se exige que lo ejecute."""
    orden = _expandir(plantilla, D_RESTORE, "/nada")
    antes, despues, _ = _ejecutar_en_bash(plantilla_repo, tmp_path, orden)
    assert antes != despues, f"bash NO ejecutó el efecto de {orden!r}"


@necesita_bash
def test_propiedad_si_el_guardarrail_permite_bash_no_toca_el_centinela(plantilla_repo, tmp_path, monkeypatch):
    proj = plantilla_repo / "outer" / "proj"
    monkeypatch.chdir(proj)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(proj))
    fallos = []
    n = 0
    for plantilla in BAD:
        for d in (D_RESTORE, D_PUSH, "git reset --hard", "git checkout -- ."):
            orden = _expandir(plantilla, d, proj.as_posix())
            if _decide(orden):
                continue
            n += 1
            antes, despues, _ = _ejecutar_en_bash(plantilla_repo, tmp_path / f"q{n}", orden)
            if antes != despues:
                fallos.append(orden)
    assert not fallos, f"el guardarraíl PERMITIÓ órdenes que bash ejecutó: {fallos}"


# --------------------------------------------------------------------------- de punta a punta ----
NODE = shutil.which("node")


def _payload_30kb(proj):
    orden = "echo " + " ".join(["cd ."] * 6000) + "; git push --force origin master"
    assert len(orden) > 30000
    return json.dumps({"session_id": "x", "hook_event_name": "PreToolUse", "tool_name": "Bash",
                       "tool_input": {"command": orden}, "agent_type": "custom-agents:implementer",
                       "cwd": str(proj)})


@pytest.mark.serie
@pytest.mark.skipif(not NODE, reason="sin Node")
def test_payload_de_30kb_por_el_lanzador_se_deniega_en_menos_de_1_5_s(tmp_path):
    """Lente D: con `echo cd .`×6000 + `git push --force` el guard agotaba el plazo y el lanzador seguía
    SIN deny. Ahora el guard acota la entrada y deniega dentro del plazo (T-06 fix5, gap 4)."""
    proj = tmp_path / "proj"
    proj.mkdir()
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(proj), "CUSTOM_AGENTS_PYTHON": sys.executable}
    ritmo = []
    for _ in range(3):
        t = time.perf_counter()
        r = subprocess.run([NODE, os.path.join(ROOT, "hooks", "run-hook.mjs"), "native-guardrail",
                            "--runtime=claude"], input=_payload_30kb(proj), cwd=str(proj), env=env,
                           capture_output=True, text=True, encoding="utf-8", timeout=30)
        ritmo.append(time.perf_counter() - t)
        assert r.returncode == 0, r.stderr
        out = json.loads(r.stdout)
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny", (r.stdout, r.stderr)
    assert min(ritmo) < 1.5, ritmo
