#!/usr/bin/env python3
"""Suite de `skills/project-extensions/` (plugin-audit-2 T-11).

La skill sustituye a la antigua de desarrollo del plugin (que explicaba como se construye ESTE repo) y crea agentes,
skills, comandos, hooks, tools y MCP en el proyecto del usuario, en la carpeta y el formato de cada
runtime (Claude Code, Codex, OpenCode). Estas pruebas demuestran, sin red y sin tocar el repo:

  1. la skill existe, la antigua no, y su SKILL.md es un mapa corto y generico (sin rutas ni
     herramientas propias de este repo: eso vive en `references/custom-agents-repo.md`);
  2. las plantillas, rellenadas en un proyecto temporal y colocadas donde la tabla de la skill dice,
     las inventaria `agent-kits/shared/project-pieces.py` (lo que ven `/work-context` y el panel)
     sin ningun aviso, para cada runtime;
  3. la tabla de rutas de la skill coincide con la de `docs/PROJECT-EXTENSIONS.md`;
  4. ninguna pieza del repo sigue citando la skill antigua y `CONTRIBUTING.md`/`CLAUDE.md` apuntan a la
     referencia propia de custom-agents.

Ejecutar: python tests/test_project_extensions_skill.py   (o python -m pytest -q tests/test_project_extensions_skill.py)
"""
import json
import os
import re
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, "skills", "project-extensions")
SKILL_MD = os.path.join(SKILL, "SKILL.md")
TEMPLATES = os.path.join(SKILL, "templates")
PIECES = os.path.join(ROOT, "agent-kits", "shared", "project-pieces.py")
DOC_TABLA = os.path.join(ROOT, "docs", "PROJECT-EXTENSIONS.md")
ANTIGUA = "plugin-" + "dev"        # nombre de la skill retirada (partido para que este fichero no la cite)


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def _plantilla(archivo, **valores):
    texto = _leer(os.path.join(TEMPLATES, archivo))
    for clave, valor in valores.items():
        texto = texto.replace("{{" + clave + "}}", valor)
    assert "{{" not in texto, f"{archivo}: placeholder sin rellenar"
    return texto


def _escribir(proyecto, ruta, texto):
    destino = os.path.join(proyecto, *ruta.split("/"))
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, "w", encoding="utf-8", newline="") as f:
        f.write(texto)


def _inventario(proyecto):
    r = subprocess.run([sys.executable, PIECES, "--project", proyecto, "--project-only", "--json"],
                       capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


# ------------------------------------------------------------------ 1. forma de la skill

def test_la_skill_existe_y_plugin_dev_no():
    assert os.path.isfile(SKILL_MD)
    assert not os.path.exists(os.path.join(ROOT, "skills", ANTIGUA))
    texto = _leer(SKILL_MD)
    assert re.search(r"^name: project-extensions$", texto, re.M)
    descripcion = re.search(r"^description: >\n((?:  .*\n)+)", texto, re.M).group(1)
    assert len(" ".join(descripcion.split())) <= 1024
    for disparador in ("crea un agente", "añade un MCP"):
        assert disparador in descripcion, disparador
    assert not re.search(r"lint_plugin|export-interop|release\.py|agent-kits/|CHANGELOG|skills/plugin", descripcion)


def test_skill_md_es_un_mapa_corto_y_sin_herramientas_propias_de_este_repo():
    texto = _leer(SKILL_MD)
    assert len(texto.splitlines()) <= 200
    assert len(re.findall(r"lint_plugin|export-interop|release\.py|agent-kits/", texto)) == 0
    assert "references/custom-agents-repo.md" in texto            # lo propio del repo se lee solo allí
    assert "caché" in texto.lower() and "project-pieces.py" in texto
    for referencia in ("piece-boundaries", "claude-code-contracts", "tool-observation-contracts",
                       "persistent-workflows", "architecture-diagnostics", "custom-agents-repo"):
        assert os.path.isfile(os.path.join(SKILL, "references", referencia + ".md")), referencia


def test_la_referencia_del_repo_conserva_lo_propio_de_custom_agents():
    texto = _leer(os.path.join(SKILL, "references", "custom-agents-repo.md"))
    for propio in ("lint_plugin.py", "export-interop.py", "release.py", "CHANGELOG.es.md", "CONTRIBUTING.md",
                   "docs/agents/", "agent-kits/shared/"):
        assert propio in texto, propio
    assert "solo al trabajar en este repositorio" in texto.lower() or "solo dentro de custom-agents" in texto.lower()


# ------------------------------------------------------------------ 2. plantillas -> project-pieces.py

CASOS = {
    "claude-code": [
        ("agent.claude.template.md", ".claude/agents/revisor-sql.md", "agent"),
        ("skill.template.md", ".claude/skills/revisor-sql/SKILL.md", "skill"),
        ("command.claude.template.md", ".claude/commands/revisar-sql.md", "command"),
        ("mcp.claude.template.json", ".mcp.json", "mcp"),
    ],
    "codex": [
        ("agent.codex.template.toml", ".codex/agents/revisor-sql.toml", "agent"),
        ("skill.template.md", ".agents/skills/revisor-sql/SKILL.md", "skill"),
        ("mcp.codex.template.toml", ".codex/config.toml", "mcp"),
    ],
    "opencode": [
        ("agent.opencode.template.md", ".opencode/agents/revisor-sql.md", "agent"),
        ("skill.template.md", ".opencode/skills/revisor-sql/SKILL.md", "skill"),
        ("command.opencode.template.md", ".opencode/commands/revisar-sql.md", "command"),
        ("tool.opencode.template.ts", ".opencode/tools/sqlcheck.ts", "tool-source"),
        ("mcp.opencode.template.jsonc", "opencode.jsonc", "mcp"),
    ],
}
VALORES = {"nombre": "revisor-sql", "descripcion": "Revisa consultas SQL del proyecto. Úsalo cuando el usuario diga «revisa este SQL».",
           "servidor": "sqlite-local", "comando_mcp": "npx"}


@pytest.mark.parametrize("runtime", sorted(CASOS))
def test_las_plantillas_de_cada_runtime_las_inventaria_project_pieces_sin_avisos(tmp_path, runtime):
    proyecto = str(tmp_path / "proyecto")
    os.makedirs(proyecto)
    for plantilla, ruta, _tipo in CASOS[runtime]:
        valores = dict(VALORES)
        if plantilla.startswith("command"):
            valores["nombre"] = "revisar-sql"
        if plantilla.startswith("tool"):
            valores["nombre"] = "sqlcheck"
        _escribir(proyecto, ruta, _plantilla(plantilla, **valores))
    inv = _inventario(proyecto)
    assert inv["warnings"] == [] and inv["partial"] is False, inv["warnings"]
    vistas = {(p["kind"]) for p in inv["pieces"] if p["runtime"] == runtime}
    esperadas = {tipo for _p, _r, tipo in CASOS[runtime]}
    assert esperadas <= vistas, (runtime, esperadas - vistas)
    nombres = {p["name"] for p in inv["pieces"] if p["runtime"] == runtime and p["kind"] == "agent"}
    assert "revisor-sql" in nombres


def test_codex_no_tiene_carpeta_de_comandos_y_la_skill_lo_dice():
    texto = _leer(SKILL_MD)
    assert re.search(r"Codex[^\n]*coman", texto, re.I | re.S)
    assert not os.path.exists(os.path.join(TEMPLATES, "command.codex.template.md"))


def test_hook_y_tool_de_claude_se_documentan_sin_inventar_un_ejecutor():
    texto = _leer(SKILL_MD)
    assert "hook" in texto.lower()
    assert re.search(r"Claude[^\n]*tool[^\n]*(sin|no hay)[^\n]*ejecutor", texto, re.I)
    assert os.path.isfile(os.path.join(TEMPLATES, "hook.claude.settings.template.json"))
    assert os.path.isfile(os.path.join(TEMPLATES, "hook-informativo.template.py"))


# ------------------------------------------------------------------ 3. la tabla coincide con la doc

def test_las_rutas_de_la_skill_son_las_de_docs_project_extensions():
    skill = _leer(SKILL_MD)
    doc = _leer(DOC_TABLA)
    rutas = set(re.findall(r"`((?:\.claude|\.codex|\.agents|\.opencode)/[A-Za-z{}<>*./-]+|\.mcp\.json|opencode\.json)`", skill))
    # Los hooks no los inventaria `project-pieces.py`: su ruta no esta en la tabla de la doc.
    rutas -= {".claude/settings.json", ".opencode/plugins/"}
    assert len(rutas) >= 10, rutas
    for ruta in sorted(rutas):
        base = ruta.split("<")[0].split("{")[0].split("*")[0].rstrip("/")
        assert base in doc, f"{ruta}: la skill cita una carpeta que docs/PROJECT-EXTENSIONS.md no tiene"


# ------------------------------------------------------------------ 4. nada sigue citando la skill antigua

def test_ninguna_pieza_cita_ya_plugin_dev():
    r = subprocess.run(["git", "grep", "-l", ANTIGUA, "--", ".", ":!docs/roadmap", ":!docs/knowledge", ":!CHANGELOG*"],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    assert r.stdout.strip() == "", r.stdout


def test_contributing_y_claude_md_apuntan_a_la_referencia_del_repo():
    for fichero in ("CONTRIBUTING.md", "CLAUDE.md"):
        assert "skills/project-extensions/references/custom-agents-repo.md" in _leer(os.path.join(ROOT, fichero)), fichero
    assert "project-extensions" in _leer(os.path.join(ROOT, "agent-kits", "shared", "modules.json"))


if __name__ == "__main__":
    sys.exit(pytest.main([os.path.abspath(__file__), "-q"]))


# ------------------------------------------------------------------ 5. fix1 de la Fase 2 (gaps 9-13)

_YAML = [("agent.claude.template.md", ".claude/agents/{n}.md", "claude-code"),
         ("skill.template.md", ".claude/skills/{n}/SKILL.md", "claude-code"),
         ("command.claude.template.md", ".claude/commands/{n}.md", "claude-code"),
         ("agent.opencode.template.md", ".opencode/agents/{n}.md", "opencode"),
         ("command.opencode.template.md", ".opencode/commands/{n}.md", "opencode")]


@pytest.mark.parametrize("plantilla,ruta,runtime", _YAML)
def test_gap9_una_descripcion_con_comillas_dobles_no_invalida_el_frontmatter(tmp_path, plantilla, ruta, runtime):
    """La skill pide terminar la description con «Úsalo cuando el usuario diga "…", "…"»: la plantilla YAML
    tiene que aceptar esas comillas (y un `:`), o la pieza desaparece del inventario."""
    proyecto = str(tmp_path / "p")
    os.makedirs(proyecto)
    descripcion = 'Revisa SQL: criterio propio. Úsalo cuando el usuario diga "revisa la consulta", "optimiza el SQL".'
    _escribir(proyecto, ruta.format(n="revisor-sql"), _plantilla(plantilla, nombre="revisor-sql", descripcion=descripcion))
    inv = _inventario(proyecto)
    assert inv["warnings"] == [] and inv["partial"] is False, inv["warnings"]
    assert [p for p in inv["pieces"] if p["runtime"] == runtime], inv["pieces"]


def _correr_hook(stdin_texto):
    ruta = os.path.join(TEMPLATES, "hook-informativo.template.py")
    codigo = _leer(ruta).replace("{{nombre}}", "mi-hook")
    return subprocess.run([sys.executable, "-c", codigo], input=stdin_texto, capture_output=True,
                          text=True, encoding="utf-8", timeout=30)


@pytest.mark.parametrize("entrada", ['{"tool_input": "x"}', '{"tool_input": ["a"]}', '{"tool_input": 3}',
                                     '["x"]', "no es json", ""])
def test_gap10_el_hook_de_plantilla_calla_con_una_entrada_que_no_es_el_contrato(entrada):
    r = _correr_hook(entrada)
    assert r.returncode == 0 and "Traceback" not in r.stderr and r.stdout.strip() == "", (r.returncode, r.stderr)


def test_gap13_el_hook_de_plantilla_sanea_la_ruta_antes_del_mensaje():
    sucia = "a.py\x1b[31m\u202e\nSIMULADO: ok\u2028fin"
    r = _correr_hook(json.dumps({"tool_input": {"file_path": sucia}}))
    assert r.returncode == 0, r.stderr
    mensaje = json.loads(r.stdout)["systemMessage"]
    for malo in ("\x1b", "\u202e", "\n", "\u2028", "\r"):
        assert malo not in mensaje, repr(malo)
    assert "a.py" in mensaje


def test_gap12_las_plantillas_mcp_fijan_la_version_y_opencode_no_nace_activo():
    for archivo in ("mcp.claude.template.json", "mcp.codex.template.toml", "mcp.opencode.template.jsonc"):
        texto = _leer(os.path.join(TEMPLATES, archivo))
        assert "<paquete-del-servidor>@<versión>" in texto, archivo
        assert "<paquete-del-servidor>\"" not in texto, archivo          # nada de `npx -y <paquete>` sin versión
    assert '"enabled": false' in _leer(os.path.join(TEMPLATES, "mcp.opencode.template.jsonc"))
    skill = _leer(SKILL_MD)
    assert re.search(r"versi[oó]n fijada|fija la versi[oó]n", skill), "la skill debe exigir fijar la versión del servidor MCP"


def test_gap11_el_paso_3_dice_como_verificar_un_hook_que_el_inventario_no_lista():
    skill = _leer(SKILL_MD)
    paso3 = skill[skill.index("## Paso 3"):skill.index("## Referencias")]
    assert re.search(r"hook", paso3, re.I) and "no lista" in paso3, paso3
    assert re.search(r"hook", _leer(os.path.join(SKILL, "references", "verify-inventory.md")), re.I)


def test_fix2_la_skill_exige_la_descripcion_en_una_linea():
    """Gap 2 (intento 2): `>-` con varias lineas sin sangrar rompe el frontmatter; la skill lo prohibe."""
    texto = _leer(os.path.join(SKILL, "SKILL.md"))
    paso1 = texto.split("## Paso 1", 1)[1].split("## Paso 2", 1)[0]
    assert "una sola línea" in paso1 and "sangr" in paso1, paso1
