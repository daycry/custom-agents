#!/usr/bin/env python3
"""Suite de la INTEROP con Codex y OpenCode (`scripts/export-interop.py`).

Cubre las tres cosas que pueden romper la importación del plugin en otra herramienta:

1. **Sincronía** — el árbol generado refleja las piezas del repo (`--check` en verde). Es la
   misma puerta que corre CI y `release.py`: si alguien toca un agente y no regenera, falla aquí.
2. **Formato** — lo generado es válido y COMPLETO para cada runtime: TOML parseable con las tres
   claves obligatorias de Codex, frontmatter con `description` en OpenCode, manifiesto con los
   punteros que Codex lee, hooks solo con eventos que Codex dispara de verdad.
3. **Invariantes que no se pueden perder al traducir** — el `reviewer` sigue siendo de SOLO
   LECTURA en los dos runtimes, y ninguna `description` de skill pasa del tope de OpenCode
   (1.024 caracteres): pasarse no es un aviso, es una skill que NO carga.

Ejecutar: python3 -m pytest -q tests/test_export_interop.py   (o `python3 tests/test_export_interop.py`)
"""
import importlib.util
import json
import os
import re
import sys
import tomllib

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Tope de `description` de una skill en OpenCode (doc oficial: «1-1024 characters»).
OPENCODE_DESC_MAX = 1024
# Eventos que Codex dispara. `PostToolUse` NO entra: Codex solo lo emite para la herramienta
# Bash y los hooks del plugin reaccionan a Write/Edit (ver docs/INTEROP.md).
CODEX_EVENTOS_OK = {"SessionStart", "UserPromptSubmit", "SubagentStop", "SessionEnd",
                    "PreToolUse", "PostToolUse", "Stop", "PreCompact", "PostCompact",
                    "SubagentStart", "PermissionRequest"}


def _mod():
    p = os.path.join(ROOT, "scripts", "export-interop.py")
    spec = importlib.util.spec_from_file_location("export_interop", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


MOD = _mod()


def leer(rel):
    with open(os.path.join(ROOT, rel.replace("/", os.sep)), encoding="utf-8") as f:
        return f.read()


# --------------------------------------------------------------------- 1. sincronía

def test_arbol_generado_al_dia():
    """`--check` en verde: lo del disco == lo que produciría el generador ahora mismo."""
    plan = MOD.generar(ROOT)
    desincronizados = []
    for rel, contenido in plan.items():
        p = os.path.join(ROOT, rel.replace("/", os.sep))
        if not os.path.isfile(p):
            desincronizados.append("FALTA " + rel)
        elif leer(rel) != contenido:
            desincronizados.append("DISTINTO " + rel)
    assert not desincronizados, ("interop desincronizada; corre `python3 scripts/export-interop.py`:\n  "
                                 + "\n  ".join(desincronizados))


def test_generacion_determinista():
    """Dos generaciones seguidas dan exactamente el mismo árbol (ni fechas ni orden aleatorio)."""
    assert MOD.generar(ROOT) == MOD.generar(ROOT)


def test_cubre_todas_las_piezas():
    """Cada agente y cada comando del repo tiene su traducción en LOS DOS runtimes."""
    plan = MOD.generar(ROOT)
    agentes = [f[:-3] for f in sorted(os.listdir(os.path.join(ROOT, "agents"))) if f.endswith(".md")]
    comandos = [f[:-3] for f in sorted(os.listdir(os.path.join(ROOT, "commands"))) if f.endswith(".md")]
    faltan = [r for n in agentes for r in (f"interop/codex/agents/{n}.toml",
                                           f"interop/opencode/agents/{n}.md") if r not in plan]
    faltan += [r for n in comandos for r in (f"interop/codex/prompts/{n}.md",
                                             f"interop/opencode/commands/{n}.md") if r not in plan]
    assert not faltan, "piezas sin traducir: %s" % faltan


# --------------------------------------------------------------------- 2. formato

def test_codex_agentes_toml_valido():
    """TOML parseable con las tres claves que Codex exige, y `developer_instructions` con cuerpo."""
    base = os.path.join(ROOT, "interop", "codex", "agents")
    for fn in sorted(os.listdir(base)):
        with open(os.path.join(base, fn), "rb") as f:
            d = tomllib.load(f)
        for k in ("name", "description", "developer_instructions"):
            assert d.get(k), "%s: falta o está vacía la clave obligatoria `%s`" % (fn, k)
        assert d["name"] == fn[:-5], "%s: `name` debe coincidir con el fichero" % fn
        assert len(d["developer_instructions"]) > 500, "%s: cuerpo sospechosamente corto" % fn
        if "model_reasoning_effort" in d:
            assert d["model_reasoning_effort"] in ("low", "medium", "high", "xhigh", "max"), fn


def test_codex_manifiesto_apunta_a_lo_que_existe():
    m = json.loads(leer(".codex-plugin/plugin.json"))
    assert m["name"] == "custom-agents"
    for clave in ("skills", "hooks"):
        destino = m[clave].lstrip("./")
        assert os.path.exists(os.path.join(ROOT, destino.replace("/", os.sep))), \
            "plugin.json `%s` apunta a %s, que no existe" % (clave, m[clave])
    # La versión no puede divergir del manifiesto de Claude Code (los bumpea `release.py` juntos).
    assert m["version"] == json.loads(leer(".claude-plugin/plugin.json"))["version"]
    assert m["interface"]["displayName"]


def test_codex_marketplace_valido():
    mk = json.loads(leer(".agents/plugins/marketplace.json"))
    assert mk["plugins"], "marketplace sin plugins"
    p = mk["plugins"][0]
    assert p["policy"]["installation"] in ("AVAILABLE", "INSTALLED_BY_DEFAULT", "NOT_AVAILABLE")
    assert p["category"] and p["source"]["source"] == "local"
    assert p["version"] == json.loads(leer(".claude-plugin/plugin.json"))["version"]


def test_codex_hooks_solo_eventos_que_dispara():
    h = json.loads(leer("interop/codex/hooks.json"))["hooks"]
    assert h, "hooks.json de Codex vacío"
    desconocidos = set(h) - CODEX_EVENTOS_OK
    assert not desconocidos, "eventos que Codex no conoce: %s" % desconocidos
    # PostToolUse queda fuera A PROPÓSITO: solo dispara para Bash y los hooks miran Write/Edit.
    assert "PostToolUse" not in h, "PostToolUse no puede viajar a Codex (solo dispara para Bash)"
    # SessionStart sin `compact`: ese matcher es de Claude Code.
    for grupo in h.get("SessionStart", []):
        assert "compact" not in grupo.get("matcher", ""), "`compact` no es un source de Codex"


def test_opencode_agentes_frontmatter():
    """Frontmatter con `description`, `mode` y `permission`; el cuerpo conserva el prompt."""
    base = os.path.join(ROOT, "interop", "opencode", "agents")
    for fn in sorted(os.listdir(base)):
        t = leer("interop/opencode/agents/" + fn)
        bloque, cuerpo = MOD.partir_frontmatter(t)
        assert bloque, "%s: sin frontmatter" % fn
        assert MOD.campo(bloque, "description"), "%s: sin description" % fn
        assert re.search(r"^mode: (subagent|primary|all)$", bloque, re.M), "%s: `mode` inválido" % fn
        assert re.search(r"^permission:$", bloque, re.M), "%s: sin bloque `permission`" % fn
        assert len(cuerpo) > 500, "%s: cuerpo sospechosamente corto" % fn


def test_opencode_config_valida():
    cfg = json.loads(leer("interop/opencode/opencode.json"))
    assert cfg["$schema"] == "https://opencode.ai/config.json"
    # El índice de piezas es el sustituto del hook SessionStart: tiene que estar en instructions.
    assert any("custom-agents-index" in i for i in cfg["instructions"])


def test_opencode_adaptador_de_hooks_es_copia_fiel():
    """El .js de interop es copia EXACTA de su fuente en hooks/ (una sola fuente de verdad)."""
    assert leer("interop/opencode/plugins/custom-agents-hooks.js") == leer("hooks/opencode-plugin.js")


def test_generados_llevan_marca():
    """Todo fichero generado se identifica como tal (nadie lo edita a mano por error)."""
    sin_marca = [rel for rel, txt in MOD.generar(ROOT).items()
                 if MOD.MARCA not in txt and not rel.endswith((".json", ".js"))]
    assert not sin_marca, "generados sin cabecera «GENERADO»: %s" % sin_marca


# --------------------------------------------------------------------- 3. invariantes

def test_reviewer_sigue_siendo_solo_lectura():
    """El invariante «un revisor que puede escribir deja de ser revisor», en los dos runtimes."""
    with open(os.path.join(ROOT, "interop", "codex", "agents", "reviewer.toml"), "rb") as f:
        codex = tomllib.load(f)
    assert codex.get("sandbox_mode") == "read-only", "reviewer sin sandbox de solo lectura en Codex"
    bloque, _ = MOD.partir_frontmatter(leer("interop/opencode/agents/reviewer.md"))
    assert re.search(r"^\s+edit: deny$", bloque, re.M), "reviewer con `edit` permitido en OpenCode"


def test_agentes_con_escritura_la_conservan():
    """La traducción no puede DEJAR SIN herramientas a quien las declara (p. ej. implementer)."""
    bloque, _ = MOD.partir_frontmatter(leer("interop/opencode/agents/implementer.md"))
    assert re.search(r"^\s+edit: allow$", bloque, re.M)
    assert re.search(r"^\s+bash: allow$", bloque, re.M)


def test_descripciones_de_skill_caben_en_opencode():
    """OpenCode valida `description` en 1-1024 caracteres: pasarse = skill que no carga."""
    largas = []
    for d in sorted(os.listdir(os.path.join(ROOT, "skills"))):
        p = os.path.join(ROOT, "skills", d, "SKILL.md")
        if not os.path.isfile(p):
            continue
        with open(p, encoding="utf-8") as f:
            bloque, _ = MOD.partir_frontmatter(f.read())
        n = len(MOD.campo(bloque, "description"))
        assert n, "skill `%s`: sin description (OpenCode y Codex la exigen)" % d
        if n > OPENCODE_DESC_MAX:
            largas.append("%s (%d)" % (d, n))
    assert not largas, ("descriptions por encima de %d caracteres — OpenCode NO cargaría la skill: %s"
                        % (OPENCODE_DESC_MAX, ", ".join(largas)))


def test_skills_nombre_coincide_con_carpeta():
    """Requisito de los dos runtimes: `name` == carpeta, kebab-case."""
    for d in sorted(os.listdir(os.path.join(ROOT, "skills"))):
        p = os.path.join(ROOT, "skills", d, "SKILL.md")
        if not os.path.isfile(p):
            continue
        with open(p, encoding="utf-8") as f:
            bloque, _ = MOD.partir_frontmatter(f.read())
        assert MOD.campo(bloque, "name") == d, "skill `%s`: `name` no coincide con la carpeta" % d
        assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", d), "skill `%s`: no es kebab-case" % d


def test_campo_plieta_escalares_de_bloque():
    """`campo()` entiende `>` y `|` de YAML: 12 de las 17 skills escriben así su description."""
    bloque = "name: x\ndescription: >\n  linea uno\n  linea dos\nmodel: opus\n"
    assert MOD.campo(bloque, "description") == "linea uno linea dos"
    assert MOD.campo(bloque, "model") == "opus"
    assert MOD.campo("description: plano\n", "description") == "plano"
    assert MOD.campo("a: 1\n", "ausente") == ""


def test_toml_multi_escapa_cuerpo_con_triple_comilla():
    """Un cuerpo con `'''` no puede romper el TOML generado."""
    out = MOD.toml_multi("texto con ''' dentro")
    assert out.startswith('"""'), "debería caer al literal escapado"
    assert tomllib.loads("k = " + out)["k"].strip() == "texto con ''' dentro"


def _tests():
    return [(k, v) for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]


if __name__ == "__main__":
    fallos = 0
    for nombre, fn in _tests():
        try:
            fn()
            print("ok   %s" % nombre)
        except AssertionError as e:
            fallos += 1
            print("FAIL %s\n     %s" % (nombre, e))
    print("\ntest_export_interop: %d casos · %d fallo(s)" % (len(_tests()), fallos))
    sys.exit(1 if fallos else 0)
