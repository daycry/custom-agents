"""Resolución de la raíz del plugin en las piezas (regla 5 de docs/CONVENTIONS.md).

Bug: `find … "$HOME/.claude" … | head -1` devolvía la primera coincidencia del disco —un temporal de
`~/.claude/jobs/` o la versión más antigua de la caché (`2.0.0` antes que `3.2.2`)— en vez del plugin
que está corriendo. Ahora cada resolución usa primero `${CLAUDE_PLUGIN_ROOT}` (Claude Code lo sustituye
en el contenido de comandos, skills y agentes) y, si no existe, un `find` que prefiere la copia del
proyecto y, en las raíces de usuario, ignora `jobs/` y elige la versión más alta.
"""
import os
import pathlib
import re
import shutil
import subprocess

import pytest

ROOT = pathlib.Path(os.environ.get("CA_RESOLUTION_ROOT") or pathlib.Path(__file__).resolve().parent.parent)
BASH = shutil.which("bash")
PIEZAS = ("commands", "skills", "agents", "agent-kits")
PREFIJOS_PLUGIN = ("agent-kits/", "skills/", "statusline/", "hooks/", "commands/")
FIND_RE = re.compile(r"\$\(\{? ?find \"\$PWD/\.claude\"[^\n]*?-path '\*([^']+)'")


def _linea_doctor():
    md = (ROOT / "commands" / "doctor.md").read_text(encoding="utf-8")
    return next(l.strip() for l in md.splitlines() if l.strip().startswith("DOC="))


def _resolver(tmp_path, *, plugin_root=None, copia_proyecto=False):
    home, proj = tmp_path / "home", tmp_path / "proj"
    rel = pathlib.Path("agent-kits", "shared", "doctor.py")
    sitios = [home / ".claude" / "jobs" / "e1" / "tmp" / "lenteB" / "mut",
              home / ".claude" / "plugins" / "cache" / "daycry" / "custom-agents" / "2.0.0",
              home / ".claude" / "plugins" / "cache" / "daycry" / "custom-agents" / "3.2.2"]
    if copia_proyecto:
        sitios.append(proj / ".claude")
    for s in sitios:
        (s / rel).parent.mkdir(parents=True, exist_ok=True)
        (s / rel).write_text("#\n", encoding="utf-8")
    proj.mkdir(exist_ok=True)
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PLUGIN_ROOT"}
    env["HOME"] = str(home)
    linea = _linea_doctor()
    if plugin_root is not None:   # lo que hace Claude Code al cargar el comando
        linea = linea.replace("${CLAUDE_PLUGIN_ROOT}", str(plugin_root).replace("\\", "/"))
    r = subprocess.run([BASH, "-c", linea + '\nprintf "%s" "$DOC"'], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=str(proj), env=env, timeout=60)
    return r.stdout.replace("\\", "/"), home


@pytest.mark.skipif(not BASH, reason="sin bash")
def test_sin_raiz_sustituida_elige_la_version_mas_alta_y_nunca_jobs(tmp_path):
    ruta, _ = _resolver(tmp_path)
    assert "/custom-agents/3.2.2/agent-kits/shared/doctor.py" in ruta, ruta
    assert "/jobs/" not in ruta and "/2.0.0/" not in ruta, ruta


@pytest.mark.skipif(not BASH, reason="sin bash")
def test_raiz_sustituida_gana_a_cualquier_otra_copia(tmp_path):
    raiz = tmp_path / "home" / ".claude" / "plugins" / "cache" / "daycry" / "custom-agents" / "2.0.0"
    ruta, _ = _resolver(tmp_path, plugin_root=raiz, copia_proyecto=True)
    assert ruta.endswith("/custom-agents/2.0.0/agent-kits/shared/doctor.py"), ruta


@pytest.mark.skipif(not BASH, reason="sin bash")
def test_sin_raiz_la_copia_del_proyecto_sigue_ganando(tmp_path):
    ruta, _ = _resolver(tmp_path, copia_proyecto=True)
    assert "/proj/.claude/agent-kits/shared/doctor.py" in ruta, ruta


CACHES = {   # raíz de usuario de cada runtime → carpeta de la instalación con versión
    "claude": (".claude", "plugins", "cache", "daycry", "custom-agents"),
    "codex": (".codex", "plugins", "cache", "daycry", "custom-agents"),
    "opencode": (".config", "opencode", "plugins", "custom-agents"),
}
GENERADO = {   # copia del comando /doctor que cada runtime lee
    "claude": ("commands", "doctor.md"),
    "codex": ("interop", "codex", "command-skills", "custom-agents-doctor", "references", "command.md"),
    "opencode": ("interop", "opencode", "commands", "doctor.md"),
}


def _resolver_en(tmp_path, runtime, versiones):
    """Ejecuta la línea `DOC=` de la copia de `runtime` sin raíz sustituida (Codex/OpenCode no la
    sustituyen) con las instalaciones `versiones` = {runtime: [versión, …]} en un HOME falso."""
    home, proj = tmp_path / "home", tmp_path / "proj"
    proj.mkdir(exist_ok=True)
    rel = pathlib.Path("agent-kits", "shared", "doctor.py")
    for rt, vs in versiones.items():
        for v in vs:
            f = home.joinpath(*CACHES[rt], v) / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text("#\n", encoding="utf-8")
    md = ROOT.joinpath(*GENERADO[runtime]).read_text(encoding="utf-8")
    linea = next(l.strip() for l in md.splitlines() if l.strip().startswith("DOC="))
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PLUGIN_ROOT"}
    env["HOME"] = str(home)
    r = subprocess.run([BASH, "-c", linea + '\nprintf "%s" "$DOC"'], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=str(proj), env=env, timeout=60)
    return r.stdout.replace("\\", "/")


@pytest.mark.skipif(not BASH, reason="sin bash")
def test_las_raices_de_usuario_no_se_mezclan_al_ordenar_versiones(tmp_path):
    """Una copia de OpenCode con versión mayor no gana a la caché de Claude Code en la pieza canónica:
    el orden de las raíces manda y la versión solo decide DENTRO de cada raíz."""
    ruta = _resolver_en(tmp_path, "claude", {"claude": ["2.0.0", "3.2.2"], "opencode": ["9.9.9"]})
    assert "/.claude/plugins/cache/daycry/custom-agents/3.2.2/" in ruta, ruta


@pytest.mark.skipif(not BASH, reason="sin bash")
@pytest.mark.parametrize("runtime", ["codex", "opencode"])
def test_la_copia_generada_de_cada_runtime_prefiere_su_propia_instalacion(tmp_path, runtime):
    """Con los tres runtimes instalados, Codex y OpenCode ejecutan SU copia, en la versión más alta."""
    ruta = _resolver_en(tmp_path, runtime, {"claude": ["9.9.9"], "codex": ["2.0.0", "3.2.2"],
                                            "opencode": ["2.0.0", "3.2.2"]})
    esperado = "/" + "/".join(CACHES[runtime]) + "/3.2.2/agent-kits/shared/doctor.py"
    assert ruta.endswith(esperado), ruta


@pytest.mark.skipif(not BASH, reason="sin bash")
@pytest.mark.parametrize("runtime", ["codex", "opencode"])
def test_runtime_solo_instalado_encuentra_su_version_mas_alta(tmp_path, runtime):
    ruta = _resolver_en(tmp_path, runtime, {runtime: ["2.0.0", "10.1.0", "3.2.2"]})
    assert ruta.endswith("/" + "/".join(CACHES[runtime]) + "/10.1.0/agent-kits/shared/doctor.py"), ruta


def test_toda_resolucion_de_un_fichero_del_plugin_usa_primero_la_raiz_del_plugin():
    malas = []
    for d in PIEZAS:
        for p in sorted((ROOT / d).rglob("*.md")):
            for n, linea in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                for m in FIND_RE.finditer(linea):
                    suf = m.group(1)
                    if not suf.startswith(PREFIJOS_PLUGIN):
                        continue   # configuración del proyecto (rates.json, confluence.json…)
                    if "${CLAUDE_PLUGIN_ROOT}/" + suf not in linea or "! -path '*/.claude/jobs/*'" not in linea:
                        malas.append(f"{p.relative_to(ROOT)}:{n} ({suf})")
    assert not malas, malas
