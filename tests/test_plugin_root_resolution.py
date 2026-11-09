"""Resolución de la raíz del plugin en las piezas (regla 5 de docs/CONVENTIONS.md).

Bug: `find … "$HOME/.claude" … | head -1` devolvía la primera coincidencia del disco: un temporal de
`~/.claude/jobs/`, la versión más antigua de la caché (`2.0.0` antes que `3.2.2`), un fixture de tests
(`tests/fixtures/…/bundle/agent-kits/shared`), el clon del marketplace o una copia `synced` vieja.
Ahora cada resolución usa primero `${CLAUDE_PLUGIN_ROOT}` (Claude Code lo sustituye en el contenido
de comandos, skills y agentes) y, si no existe, busca el MARCADOR `agent-kits/shared/ledger-lint.py`
—solo existe en un bundle real— raíz a raíz (proyecto, cachés de instalación, usuario), con
`-maxdepth 6` (deja fuera `synced/`, `.staging/` y `plugin-install-*`), la versión más alta dentro
de cada raíz y corte en la primera raíz con resultado.

Las instalaciones simuladas reproducen las de una máquina real con las tres CLIs.
"""
import os
import pathlib
import re
import shutil
import subprocess
import sys

import pytest

ROOT = pathlib.Path(os.environ.get("CA_RESOLUTION_ROOT") or pathlib.Path(__file__).resolve().parent.parent)
BASH = shutil.which("bash")
PWSH = shutil.which("pwsh") or shutil.which("powershell")
PIEZAS = ("commands", "skills", "agents", "agent-kits")
MARCADOR = pathlib.Path("agent-kits", "shared", "ledger-lint.py")
GENERADO = {   # copias del comando que lee cada runtime: (doctor, dev-cycle)
    "claude": (("commands", "doctor.md"), ("commands", "dev-cycle.md")),
    "codex": (("interop", "codex", "command-skills", "custom-agents-doctor", "references", "command.md"),
              ("interop", "codex", "command-skills", "custom-agents-dev-cycle", "references", "command.md")),
    "opencode": (("interop", "opencode", "commands", "doctor.md"), ("interop", "opencode", "commands", "dev-cycle.md")),
}
CACHE = {"claude": (".claude", "plugins", "cache", "daycry", "custom-agents"),
         "codex": (".codex", "plugins", "cache", "daycry", "custom-agents")}


def bundle(d):
    """Un bundle real: marcador + los ficheros que resuelven los tests."""
    for rel in (MARCADOR, pathlib.Path("agent-kits", "shared", "doctor.py"),
                pathlib.Path("agent-kits", "dev-cycle", "references", "phase2-planning.md")):
        (d / rel).parent.mkdir(parents=True, exist_ok=True)
        (d / rel).write_text("#\n", encoding="utf-8")
    return d


def maquina(home, runtimes=("claude",), versiones=("2.0.0", "10.1.0", "3.2.2")):
    """HOME con las instalaciones y los distractores que se ven en una máquina real."""
    bundle(home / ".claude" / "jobs" / "e1" / "mut")                       # mutante de revisión
    if "claude" in runtimes:
        for v in versiones:
            b = bundle(home.joinpath(*CACHE["claude"], v))
            fx = b / "tests" / "fixtures" / "panel-redesign" / "bundle" / "agent-kits" / "shared"
            fx.mkdir(parents=True)
            (fx / "native-roles.json").write_text("{}", encoding="utf-8")   # fixture sin marcador
        bundle(home / ".claude" / "plugins" / "marketplaces" / "daycry")   # clon del marketplace
        sync = home / ".claude" / "plugins" / "synced" / "a1_b2"
        bundle(sync / "custom-agents")                                     # copia sincronizada vieja
        bundle(sync / ".staging" / "1" / "custom-agents" / "unzip-x")
    if "codex" in runtimes:
        for v in versiones:
            bundle(home.joinpath(*CACHE["codex"], v))
        bundle(home / ".codex" / "plugins" / "cache" / "daycry" / "plugin-install-Tz" / "custom-agents" / "99.0.0")
        bundle(home / ".codex" / "plugins" / "custom-agents")              # fuente del instalador
    if "opencode" in runtimes:
        bundle(home / ".config" / "opencode")


def _env(home):
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PLUGIN_ROOT"}
    env.update(HOME=str(home), USERPROFILE=str(home))
    return env


def _bash(runtime, tmp_path, *, plugin_root=None, proyecto=None):
    home, proj = tmp_path / "home", tmp_path / "proj"
    proj.mkdir(exist_ok=True)
    if proyecto:
        bundle(proj / proyecto)
    md = ROOT.joinpath(*GENERADO[runtime][0]).read_text(encoding="utf-8")
    linea = next(l.strip() for l in md.splitlines() if 'DOC="$R/' in l or l.strip().startswith("DOC="))
    if plugin_root is not None:   # lo que hace Claude Code al cargar el comando
        linea = linea.replace("${CLAUDE_PLUGIN_ROOT}", str(plugin_root).replace("\\", "/"))
    r = subprocess.run([BASH, "-c", linea + '\nprintf "%s" "$DOC"'], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=str(proj), env=_env(home), timeout=120)
    return r.stdout.replace("\\", "/"), r.stderr


def _esperado(runtime, v="10.1.0"):
    return "/" + "/".join(CACHE[runtime]) + f"/{v}/agent-kits/shared/doctor.py"


@pytest.mark.skipif(not BASH, reason="sin bash")
def test_sin_raiz_sustituida_elige_la_cache_de_version_mas_alta(tmp_path):
    maquina(tmp_path / "home")
    ruta, err = _bash("claude", tmp_path)
    assert ruta.endswith(_esperado("claude")), ruta
    assert err == "", err   # sin `tail: write error` ni otros restos en stderr


@pytest.mark.skipif(not BASH, reason="sin bash")
def test_raiz_sustituida_gana_a_cualquier_otra_copia(tmp_path):
    maquina(tmp_path / "home")
    raiz = tmp_path / "home" / ".claude" / "plugins" / "cache" / "daycry" / "custom-agents" / "2.0.0"
    ruta, _ = _bash("claude", tmp_path, plugin_root=raiz, proyecto=".claude")
    assert ruta.endswith("/custom-agents/2.0.0/agent-kits/shared/doctor.py"), ruta


@pytest.mark.skipif(not BASH, reason="sin bash")
def test_sin_raiz_la_copia_del_proyecto_sigue_ganando(tmp_path):
    maquina(tmp_path / "home")
    ruta, _ = _bash("claude", tmp_path, proyecto=".claude")
    assert ruta.endswith("/proj/.claude/agent-kits/shared/doctor.py"), ruta


@pytest.mark.skipif(not BASH, reason="sin bash")
def test_sin_cache_no_gana_un_fixture_ni_una_copia_synced(tmp_path):
    """Solo marketplace + synced + fixture: gana el clon del marketplace (bundle real a profundidad ≤ 6)."""
    home = tmp_path / "home"
    bundle(home / ".claude" / "plugins" / "marketplaces" / "daycry")
    bundle(home / ".claude" / "plugins" / "synced" / "a1_b2" / "custom-agents")
    fx = home / ".claude" / "tests" / "fixtures" / "x" / "bundle" / "agent-kits" / "shared"
    fx.mkdir(parents=True)
    ruta, _ = _bash("claude", tmp_path)
    assert ruta.endswith("/plugins/marketplaces/daycry/agent-kits/shared/doctor.py"), ruta


@pytest.mark.skipif(not BASH, reason="sin bash")
def test_las_raices_no_se_mezclan_al_ordenar_versiones(tmp_path):
    """Con OpenCode y Codex instalados, la pieza canónica (Claude Code) usa la caché de Claude."""
    maquina(tmp_path / "home", runtimes=("claude", "codex", "opencode"))
    ruta, _ = _bash("claude", tmp_path)
    assert ruta.endswith(_esperado("claude")), ruta


@pytest.mark.skipif(not BASH, reason="sin bash")
def test_codex_usa_su_cache_y_nunca_plugin_install(tmp_path):
    maquina(tmp_path / "home", runtimes=("claude", "codex", "opencode"))
    ruta, _ = _bash("codex", tmp_path)
    assert ruta.endswith(_esperado("codex")), ruta


@pytest.mark.skipif(not BASH, reason="sin bash")
def test_opencode_usa_su_instalacion_global(tmp_path):
    maquina(tmp_path / "home", runtimes=("claude", "codex", "opencode"))
    ruta, _ = _bash("opencode", tmp_path)
    assert ruta.endswith("/home/.config/opencode/agent-kits/shared/doctor.py"), ruta


@pytest.mark.skipif(not PWSH, reason="sin PowerShell")
@pytest.mark.parametrize("runtime", ["claude", "codex", "opencode"])
def test_receta_powershell_de_dev_cycle_usa_la_instalacion_de_su_runtime(tmp_path, runtime):
    """La receta PowerShell de `/dev-cycle` (Codex en Windows) tenía el mismo `Select-Object -First 1`."""
    home, proj = tmp_path / "home", tmp_path / "proj"
    proj.mkdir()
    maquina(home, runtimes=("claude", "codex", "opencode"))
    md = ROOT.joinpath(*GENERADO[runtime][1]).read_text(encoding="utf-8")
    receta = re.search(r"```powershell\n(.*?)\n```", md, re.S)[1]
    r = subprocess.run([PWSH, "-NoProfile", "-NonInteractive", "-Command", receta + "\nWrite-Output $DevCycleKit"],
                       cwd=str(proj), capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=180, env=_env(home))
    assert r.returncode == 0 and r.stderr == "", r.stderr
    ruta = r.stdout.strip().replace("\\", "/")
    esperado = ("/home/.config/opencode" if runtime == "opencode"
                else "/" + "/".join(CACHE[runtime]) + "/10.1.0") + "/agent-kits/dev-cycle"
    assert ruta.endswith(esperado), ruta


# Una resolución con `find` sobre las raíces del proyecto/usuario: la forma vieja (`$(find "$PWD/.claude" …`)
# o el bucle actual (`for r in "$PWD"/.{claude,…} …; do find "$r" …`).
VIEJA_RE = re.compile(r"\$\(find \"\$PWD/\.claude\"[^\n]*?-path '\*((?:agent-kits|skills|statusline|hooks|commands)/[^']+)'")
BUCLE = 'for r in "$PWD"/.{claude,'
CONTRATO = ('R="${CLAUDE_PLUGIN_ROOT}"; M=agent-kits/shared/ledger-lint.py; [ -f "$R/$M" ] ||',
            '-maxdepth 6 -path "*/$M"', "! -path '*/.claude/jobs/*'", "| sort -V | tail -1 | grep . && break",
            'R="${R%/$M}"')


def test_toda_resolucion_del_plugin_usa_la_raiz_por_marcador():
    malas, vistas = [], 0
    for d in PIEZAS:
        for p in sorted((ROOT / d).rglob("*.md")):
            for n, linea in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if VIEJA_RE.search(linea):
                    malas.append(f"{p.relative_to(ROOT)}:{n} (forma vieja)")
                for _ in range(linea.count(BUCLE)):
                    vistas += 1
                    if not all(c in linea for c in CONTRATO):
                        malas.append(f"{p.relative_to(ROOT)}:{n} (bucle sin el contrato completo)")
    assert vistas >= 60, f"solo {vistas} resoluciones reconocidas: ¿cambió la forma y el test mira en vacío?"
    assert not malas, malas


@pytest.mark.skipif(not BASH, reason="sin bash")
def test_paquete_portable_resuelve_sus_propios_kits(tmp_path):
    """`export-skills.py` reescribe el bucle de raíces a `${PORTABLE_ROOT:-.}`: la resolución de una
    skill exportada encuentra el kit DEL PAQUETE y el `--check` no deja raíces colgando."""
    out = tmp_path / "pkg"
    script = str(ROOT / "scripts" / "export-skills.py")
    r = subprocess.run([sys.executable, script, "--out", str(out), "--format", "claude", "--quiet"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    assert r.returncode == 0, r.stderr
    chk = subprocess.run([sys.executable, script, "--check", str(out)], capture_output=True, text=True,
                         encoding="utf-8", errors="replace", timeout=300)
    assert chk.returncode == 0, chk.stdout + chk.stderr
    md = (out / "skills" / "adversarial-review" / "SKILL.md").read_text(encoding="utf-8")
    linea = next(l.strip() for l in md.splitlines() if 'SHAREDKIT="$R/' in l)
    assert 'for r in "${PORTABLE_ROOT:-.}"; do' in linea, linea
    env = _env(tmp_path / "home")
    env["PORTABLE_ROOT"] = str(out)
    res = subprocess.run([BASH, "-c", linea + '\nprintf "%s" "$SHAREDKIT"'], capture_output=True, text=True,
                         encoding="utf-8", errors="replace", cwd=str(tmp_path), env=env, timeout=60)
    assert res.stdout.replace("\\", "/").endswith("/pkg/agent-kits/shared"), (res.stdout, res.stderr)
