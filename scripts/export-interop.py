#!/usr/bin/env python3
"""
export-interop.py — genera los ficheros de INTEROPERABILIDAD que hacen este plugin importable
en **Codex** (OpenAI) y **OpenCode** (SST), derivándolos de las piezas nativas del repo.

Principio: `agents/*.md`, `commands/*.md`, `skills/*/SKILL.md` y `hooks/` siguen siendo la ÚNICA
fuente de verdad. Este script no reescribe una pieza: la TRADUCE al formato que cada runtime
sabe leer, y `--check` falla si la traducción se ha quedado atrás (mismo patrón que las copias
`.MANUAL-COPY` que vigila `tests/test_ci_manual_copy.py`). Los ficheros generados llevan cabecera
«GENERADO» y no se editan a mano.

Qué se genera (y por qué ese formato, verificado en la doc oficial de cada herramienta):

  Codex — plugin nativo (developers.openai.com/codex, learn.chatgpt.com/docs, 2026-09-08)
    .codex-plugin/plugin.json          manifiesto del plugin (`skills`, `hooks`, `interface`).
                                       `codex plugin marketplace add <repo>` lo instala.
    .agents/plugins/marketplace.json   marketplace local/remoto que lista este plugin.
    interop/codex/hooks.json           hooks con los eventos y matchers que Codex SÍ dispara.
    interop/codex/agents/<n>.toml      agentes custom (`name`/`description`/`developer_instructions`).
    interop/codex/prompts/<n>.md       comandos como prompts (`/prompts:<n>`, `$ARGUMENTS`).
  Las `skills/` NO se copian: el manifiesto apunta a `./skills/` y Codex las lee tal cual
  (el `SKILL.md` del plugin ya cumple su frontmatter: `name` + `description`).

  OpenCode (opencode.ai/docs, 2026-09-08)
    interop/opencode/opencode.json     `instructions` + permisos de la herramienta `skill`.
    interop/opencode/agents/<n>.md     agentes (`mode`, `temperature`, `permission`).
    interop/opencode/commands/<n>.md   comandos (`$ARGUMENTS` funciona igual).
    interop/opencode/plugins/…js       copia de `hooks/opencode-plugin.js` (adaptador de hooks).
    interop/opencode/custom-agents-index.md   índice de piezas (`skill-index.py`) para `instructions`:
                                       OpenCode no tiene hook de SessionStart que inyecte contexto.
  Las `skills/` NO se traducen: su `SKILL.md` ya vale para los dos runtimes (`name` + `description`
  es exactamente lo que ambos exigen). Quien las pone en su sitio es el instalador
  (`install/install.mjs`: `.opencode/skills/` u `.codex/plugins/…/skills/`), no este script.

Traducción del prompt: a cada cuerpo se le antepone un PREÁMBULO corto que traduce las tres cosas
que cambian de runtime — cómo se invoca una skill, cómo se delega en otro agente y qué guardrail
NO está impuesto aquí. El cuerpo original no se toca (una sola fuente de verdad).

Determinista: misma entrada → mismo árbol (orden fijo, `\n`, sin fechas ni mtimes en el contenido).

Uso:
  python3 scripts/export-interop.py [--root DIR] [--quiet]      # escribe los ficheros
  python3 scripts/export-interop.py --check [--root DIR]        # ¿están al día? (CI / release)
  python3 scripts/export-interop.py --list                      # qué ficheros genera
Exit 0 si todo va bien; 1 si `--check` encuentra un fichero ausente o desincronizado.
Solo stdlib.
"""
import argparse
import json
import os
import re
import sys

# Consola Windows (cp1252) o tuberías: reconfigurar ANTES de leer o imprimir nada (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT_DEFAULT = os.path.dirname(HERE)

MARCA = "GENERADO por scripts/export-interop.py"
DOC = "docs/INTEROP.md"

# --- Tablas de equivalencia -------------------------------------------------------------------
# `effort` del plugin → `model_reasoning_effort` de Codex: mismos nombres (Codex añade `ultra`,
# que no usamos). El `model` NO se traduce: los identificadores de OpenAI no tienen equivalente
# para haiku/sonnet/opus, así que el agente HEREDA el modelo de la sesión padre (comportamiento
# documentado) y el tiering se declara solo como esfuerzo de razonamiento.
EFFORT_CODEX = {"low": "low", "medium": "medium", "high": "high", "xhigh": "xhigh", "max": "max"}
# Capa de modelo → `temperature` de OpenCode. Toda pieza de este plugin es analítica (decidir,
# planificar, auditar), y la doc de OpenCode sitúa ese trabajo en 0.0-0.2.
TEMP_OPENCODE = {"opus": 0.1, "sonnet": 0.2, "haiku": 0.2, "inherit": 0.2}
HERR_ESCRITURA = {"Write", "Edit", "MultiEdit", "NotebookEdit"}

# --- Preámbulos de adaptación ------------------------------------------------------------------
# Lo ÚNICO que se añade al cuerpo de una pieza. Tres traducciones y una honestidad.
PRE_AGENTE_CODEX = """> **Adaptación a Codex** (fichero generado; la fuente es `agents/{nombre}.md`).
> - **Skills:** donde el cuerpo diga «invoca la skill `X` con la herramienta Skill», en Codex se
>   menciona `$X` (o se deja que Codex la active por su `description`). Las skills del plugin se
>   cargan desde el propio plugin.
> - **Delegar en otro agente:** no hay herramienta Agent; se pide en lenguaje natural nombrando al
>   agente («delega en `reviewer` la lente B»). Codex no auto-invoca agentes custom: hay que pedirlo.
> - **Guardrail:** {guardrail}
> - **Rutas:** los kits se resuelven con el `find` de la regla 5 de CONVENTIONS, que ya busca en
>   `$PWD/.codex` y `$HOME/.codex` (donde el instalador deja el plugin en Codex).
"""

PRE_AGENTE_OPENCODE = """> **Adaptación a OpenCode** (fichero generado; la fuente es `agents/{nombre}.md`).
> - **Skills:** donde el cuerpo diga «invoca la skill `X` con la herramienta Skill», en OpenCode se
>   usa la herramienta `skill` (`skill({{ name: "X" }})`). OpenCode las descubre en
>   `.opencode/skills/<nombre>/SKILL.md` (y también en `.claude/skills/`, por compatibilidad).
> - **Delegar en otro agente:** herramienta `task` con el nombre del subagente (o `@nombre`).
> - **Guardrail:** {guardrail}
> - **Rutas:** los kits se resuelven con el `find` de la regla 5 de CONVENTIONS, que ya busca en
>   `$PWD/.opencode` y `$HOME/.config/opencode` (el global de OpenCode no es `~/.opencode`).
"""

PRE_COMANDO = """> **Adaptación a {runtime}** (fichero generado; la fuente es `commands/{nombre}.md`).
> Este comando ORQUESTA agentes. En {runtime} no hay herramienta Agent: {delegar}
> Las skills se invocan {skills}. Todo lo demás (puertas, artefactos, ledger) no cambia.
"""

# Guardrail por agente: qué se pierde y qué se puede recuperar en cada runtime. Honestidad
# explícita — un hook `PreToolUse` con `deny` de alcance por-agente solo existe en Claude Code
# (ADR-007), así que aquí el agente lo aplica él mismo o el sandbox lo cubre en parte.
GUARDRAIL_CON_HOOK = {
    "implementer": ("el hook de guardia `implementer-guardrail.sh` (alcance en `docs/roadmap/`, rama de "
                    "trabajo, git no destructivo) **no está impuesto** en este runtime. Antes de un "
                    "`git push --force`, `git branch -D`, `rm -rf` o de escribir en `docs/roadmap/` "
                    "fuera de `tasks.md`, comprueba la regla tú mismo con "
                    "`agent-kits/shared/guardrail-check.py pre-tool --agent implementer` (lee el JSON "
                    "del evento por stdin) y respeta su veredicto."),
    "architect": ("el hook de guardia `architect-guardrail.sh` (escribes SOLO `design.md`, "
                  "`docs/knowledge/adr/**` y el enlace `design:` en spec/plan) **no está impuesto** en "
                  "este runtime: es tu responsabilidad no tocar nada más. Puedes verificarlo con "
                  "`agent-kits/shared/guardrail-check.py pre-tool --agent architect`."),
}
GUARDRAIL_SOLO_LECTURA = ("eres de SOLO LECTURA por construcción. Aquí se declara además en la "
                          "configuración del agente (`sandbox_mode`/`permission`), pero la regla es la "
                          "misma: si crees que hay que cambiar algo, es un gap para tu salida.")
GUARDRAIL_NINGUNO = "este agente no tiene hook de guardia propio; se aplican los guardrails del proyecto."

DELEGAR = {
    "Codex": "se delega pidiéndolo en lenguaje natural y nombrando al agente (`reviewer`, `implementer`…), "
             "y los agentes custom se copian a `.codex/agents/`.",
    "OpenCode": "se delega con la herramienta `task` nombrando al subagente (o `@nombre`), definido en "
                "`.opencode/agents/`.",
}
SKILLS_EN = {
    "Codex": "mencionándolas con `$nombre`",
    "OpenCode": 'con la herramienta `skill` (`skill({ name: "nombre" })`)',
}


# --- Lectura de las piezas nativas -------------------------------------------------------------

def leer(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def partir_frontmatter(texto):
    """(bloque_frontmatter, cuerpo). Sin frontmatter → ("", texto)."""
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?", texto, re.S)
    return (m.group(1), texto[m.end():]) if m else ("", texto)


def campo(bloque, clave):
    """Escalar de PRIMER NIVEL del frontmatter (`clave: valor` en columna 0).

    Soporta los escalares de bloque de YAML (`>`, `>-`, `|`, `|-`), que es como escriben su
    `description` 12 de las 17 skills: las líneas indentadas siguientes se PLIEGAN en una sola
    (los saltos pasan a espacios), que es lo que consumen los dos runtimes de destino. Los
    bloques anidados (`dependencies:`, `hooks:`) no se traducen y por tanto no se leen.
    """
    m = re.search(r"^%s:[ \t]*(.*)$" % re.escape(clave), bloque, re.M)
    if not m:
        return ""
    v = m.group(1).strip()
    if v in (">", ">-", ">+", "|", "|-", "|+"):
        cont = []
        for linea in bloque[m.end():].splitlines():
            if linea.strip() and not linea[:1].isspace():
                break            # otra clave de primer nivel → fin del bloque
            cont.append(linea.strip())
        return re.sub(r"\s+", " ", " ".join(cont)).strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        v = v[1:-1]
    return v


def piezas(root, carpeta):
    """[(nombre, bloque_frontmatter, cuerpo)] de `carpeta/*.md`, en orden alfabético."""
    base = os.path.join(root, carpeta)
    out = []
    for fn in sorted(os.listdir(base)):
        if fn.endswith(".md"):
            bloque, cuerpo = partir_frontmatter(leer(os.path.join(base, fn)))
            out.append((fn[:-3], bloque, cuerpo))
    return out


def tools_de(bloque):
    return [t.strip() for t in campo(bloque, "tools").split(",") if t.strip()]


def guardrail_de(nombre, tools):
    if nombre in GUARDRAIL_CON_HOOK:
        return GUARDRAIL_CON_HOOK[nombre]
    return GUARDRAIL_NINGUNO if (set(tools) & HERR_ESCRITURA) else GUARDRAIL_SOLO_LECTURA


# --- Serialización ------------------------------------------------------------------------------

def json_txt(obj):
    """JSON estable: claves en el orden en que se construyen, 2 espacios, UTF-8 legible."""
    return json.dumps(obj, ensure_ascii=False, indent=2) + "\n"


def toml_str(s):
    """Cadena TOML básica de una línea."""
    return '"%s"' % s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


def toml_multi(s):
    """Cadena TOML multilínea. Literal (`'''`) salvo que el texto la contenga."""
    if "'''" not in s:
        return "'''\n%s'''" % (s if s.endswith("\n") else s + "\n")
    esc = s.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')
    return '"""\n%s"""' % (esc if esc.endswith("\n") else esc + "\n")


def cabecera(estilo, fuente):
    """Cabecera «GENERADO» en el comentario que admita el formato."""
    linea1 = "%s desde %s — no lo edites a mano." % (MARCA, fuente)
    linea2 = "Regenera con `python3 scripts/export-interop.py`; el porqué está en `%s`." % DOC
    if estilo == "toml":
        return "# %s\n# %s\n" % (linea1, linea2)
    if estilo == "html":
        return "<!-- %s\n     %s -->\n" % (linea1, linea2)
    return "// %s\n// %s\n" % (linea1, linea2)


def fm_yaml(pares):
    """Frontmatter YAML a partir de [(clave, valor)]; dict → bloque anidado de un nivel."""
    out = ["---"]
    for k, v in pares:
        if isinstance(v, dict):
            out.append("%s:" % k)
            out += ["  %s: %s" % (sk, sv) for sk, sv in v.items()]
        elif isinstance(v, float):
            out.append("%s: %s" % (k, v))
        else:
            out.append("%s: %s" % (k, v))
    out.append("---")
    return "\n".join(out) + "\n"


# --- Codex --------------------------------------------------------------------------------------

def codex_plugin_json(root):
    """`.codex-plugin/plugin.json` — mismos datos que el manifiesto de Claude Code (versión
    incluida: `release.py` los bumpea juntos) más el bloque `interface` propio de Codex y los
    punteros a los componentes que Codex sabe leer tal cual."""
    src = json.loads(leer(os.path.join(root, ".claude-plugin", "plugin.json")))
    return json_txt({
        "name": src["name"],
        "version": src["version"],
        "description": src["description"],
        "author": src["author"],
        "homepage": src["homepage"],
        "repository": src["repository"],
        "license": src["license"],
        "keywords": src["keywords"],
        # Punteros relativos a la raíz del plugin. `skills/` se lee TAL CUAL (el frontmatter
        # `name` + `description` del plugin ya es el que Codex exige). `hooks` apunta al fichero
        # adaptado, no al global: Codex no dispara los mismos eventos que Claude Code.
        "skills": "./skills/",
        "hooks": "./interop/codex/hooks.json",
        "interface": {
            "displayName": src["displayName"],
            "shortDescription": "Ciclo SDD presupuestado: requisitos → presupuesto → plan → "
                                "implementación → pruebas → documentación, con coste medido.",
            "developerName": src["author"]["name"],
            "category": "Productivity",
            "websiteURL": src["homepage"],
        },
    })


def codex_marketplace_json(root):
    """`.agents/plugins/marketplace.json` — ubicación que Codex reconoce en la raíz del repo, con
    los campos que su formato exige y el de Claude Code no tiene (`policy`, `category`)."""
    src = json.loads(leer(os.path.join(root, ".claude-plugin", "plugin.json")))
    mkt = json.loads(leer(os.path.join(root, ".claude-plugin", "marketplace.json")))
    return json_txt({
        "name": mkt["name"],
        "interface": {"displayName": "Agentes custom de daycry"},
        "plugins": [{
            "name": src["name"],
            "version": src["version"],
            "description": src["description"],
            "source": {"source": "local", "path": "./"},
            "policy": {"installation": "AVAILABLE", "authentication": "NONE"},
            "category": "Productivity",
            "keywords": src["keywords"],
        }],
    })


def codex_hooks_json(root):
    """`interop/codex/hooks.json` — los hooks del plugin filtrados y corregidos para Codex:

    - `SessionStart`: matcher `startup|resume|clear` (Codex NO tiene `compact`; la compactación
      son sus eventos `PreCompact`/`PostCompact`, que este plugin no usa).
    - `SessionEnd` y `UserPromptSubmit`: iguales (el journal y la captura del turno funcionan).
    - `SubagentStop`: existe en Codex; se mantiene.
    - `PostToolUse`: **se omite**. Codex solo dispara Pre/PostToolUse para la herramienta `Bash`,
      y los tres hooks del plugin reaccionan a `Write|Edit|MultiEdit`: registrarlos sería declarar
      un aviso que nunca llega. Lo cubre `docs/INTEROP.md` (tabla de degradación).
    """
    src = json.loads(leer(os.path.join(root, "hooks", "hooks.json")))["hooks"]
    out = {}
    for evento in ("SessionStart", "UserPromptSubmit", "SubagentStop", "SessionEnd"):
        grupos = []
        for g in src.get(evento, []):
            ng = {}
            if evento == "SessionStart":
                ng["matcher"] = "startup|resume|clear"
            elif "matcher" in g:
                ng["matcher"] = g["matcher"]
            ng["hooks"] = [dict(h) for h in g.get("hooks", [])]
            grupos.append(ng)
        if grupos:
            out[evento] = grupos
    return json_txt({"hooks": out})


def codex_agente(nombre, bloque, cuerpo):
    tools = tools_de(bloque)
    pre = PRE_AGENTE_CODEX.format(nombre=nombre, guardrail=guardrail_de(nombre, tools))
    lineas = [cabecera("toml", "agents/%s.md" % nombre),
              "# Copia este fichero a `.codex/agents/` (proyecto) o `~/.codex/agents/` (usuario).\n",
              "name = %s" % toml_str(nombre),
              "description = %s" % toml_str(campo(bloque, "description"))]
    efecto = EFFORT_CODEX.get(campo(bloque, "effort"))
    if efecto:
        lineas.append("model_reasoning_effort = %s" % toml_str(efecto))
    # Un agente sin herramienta de escritura es de solo lectura POR CONSTRUCCIÓN (reviewer): en
    # Codex eso se declara, no se recuerda.
    if not (set(tools) & HERR_ESCRITURA):
        lineas.append('sandbox_mode = "read-only"')
    lineas.append("developer_instructions = %s" % toml_multi(pre + "\n" + cuerpo.lstrip("\n")))
    return "\n".join(lineas) + "\n"


def codex_prompt(nombre, bloque, cuerpo):
    pre = PRE_COMANDO.format(runtime="Codex", nombre=nombre,
                             delegar=DELEGAR["Codex"], skills=SKILLS_EN["Codex"])
    # Description ENTRECOMILLADA (json.dumps): varias llevan `: ` dentro y un escalar plano de YAML
    # con `: ` es inválido — GitHub lo pinta como «Error in user YAML: mapping values not allowed in
    # this context» y el lector de frontmatter de Codex podría tropezar igual.
    pares = [("description", json.dumps(campo(bloque, "description"), ensure_ascii=False))]
    hint = campo(bloque, "argument-hint")
    if hint:
        pares.append(("argument-hint", json.dumps(hint, ensure_ascii=False)))
    return (fm_yaml(pares) + cabecera("html", "commands/%s.md" % nombre)
            + "\n" + pre + "\n" + cuerpo.lstrip("\n"))


# --- OpenCode -----------------------------------------------------------------------------------

def permisos_opencode(tools):
    """`tools` de Claude Code → `permission` de OpenCode. Traducción literal de lo DECLARADO:
    un agente sin Write/Edit sale con `edit: deny` (así el `reviewer` sigue sin poder escribir)."""
    t = set(tools)
    return {
        "read": "allow", "grep": "allow", "glob": "allow", "list": "allow",
        "edit": "allow" if (t & HERR_ESCRITURA) else "deny",
        "bash": "allow" if "Bash" in t else "deny",
        "webfetch": "allow" if "WebFetch" in t else "deny",
        "websearch": "allow" if "WebSearch" in t else "deny",
        "task": "allow" if "Agent" in t else "deny",
        "skill": "allow",
    }


def opencode_agente(nombre, bloque, cuerpo):
    tools = tools_de(bloque)
    pre = PRE_AGENTE_OPENCODE.format(nombre=nombre, guardrail=guardrail_de(nombre, tools))
    pares = [
        ("description", json.dumps(campo(bloque, "description"), ensure_ascii=False)),
        # Todas las piezas del plugin son subagentes: las despacha un orquestador por nombre.
        ("mode", "subagent"),
        ("temperature", TEMP_OPENCODE.get(campo(bloque, "model"), 0.2)),
        ("permission", permisos_opencode(tools)),
    ]
    return (fm_yaml(pares) + cabecera("html", "agents/%s.md" % nombre)
            + "\n" + pre + "\n" + cuerpo.lstrip("\n"))


def opencode_comando(nombre, bloque, cuerpo):
    pre = PRE_COMANDO.format(runtime="OpenCode", nombre=nombre,
                             delegar=DELEGAR["OpenCode"], skills=SKILLS_EN["OpenCode"])
    pares = [("description", json.dumps(campo(bloque, "description"), ensure_ascii=False))]
    return (fm_yaml(pares) + cabecera("html", "commands/%s.md" % nombre)
            + "\n" + pre + "\n" + cuerpo.lstrip("\n"))


def opencode_config():
    """`interop/opencode/opencode.json`. `instructions` es el sustituto del hook `SessionStart`
    que OpenCode no tiene: inyecta el índice de piezas (y el CLAUDE.md del proyecto) en cada
    sesión. `permission.skill` deja pasar las skills del plugin."""
    return json_txt({
        "$schema": "https://opencode.ai/config.json",
        "instructions": [
            ".opencode/custom-agents-index.md",
            "CLAUDE.md",
        ],
        "permission": {"skill": {"*": "allow"}},
    })


def opencode_indice(root):
    """Snapshot del índice de piezas (`skill-index.py`) como fichero de `instructions`.

    OpenCode no tiene un hook que inyecte contexto al arrancar, así que lo que en Claude Code
    hace `hooks/session-context.sh` (parte 1: el índice) aquí es un fichero estático que
    `--check` mantiene al día. Lo dinámico (roadmap, journal, memoria) no viaja: se pide a mano.
    """
    texto = ""
    try:
        mod = _cargar_skill_index(root)
        # `construir` devuelve el dict con métricas del índice; lo que viaja es su `texto`. Sin
        # caché: aquí el fichero ES el artefacto, y `--check` es quien detecta que ha caducado.
        texto = (mod.construir(mod.piezas(root)) or {}).get("texto") or ""
    except Exception:  # noqa: BLE001 — si `skill-index.py` cambia de API, índice propio (degrada)
        texto = ""
    if not texto.strip():
        texto = _indice_fallback(root)
    return ("<!-- %s desde las piezas del repo — no lo edites a mano. -->\n\n" % MARCA
            + "# custom-agents — índice de piezas\n\n"
            + "Este fichero lo lee OpenCode como `instructions` (sustituto del hook `SessionStart`\n"
              "de Claude Code). Antes de improvisar, comprueba si aplica una de estas piezas: las\n"
              "skills se invocan con la herramienta `skill`, los agentes con `task`.\n\n"
            + texto.rstrip("\n") + "\n")


def _cargar_skill_index(root):
    import importlib.util
    p = os.path.join(root, "agent-kits", "shared", "skill-index.py")
    spec = importlib.util.spec_from_file_location("skill_index_interop", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _indice_fallback(root):
    """Índice mínimo propio si `skill-index.py` cambia de API: una línea por pieza."""
    trozos = []
    for titulo, carpeta, sufijo in (("Comandos", "commands", ""), ("Agentes", "agents", "")):
        filas = ["- `%s%s` — %s" % (n, sufijo, campo(b, "description").split(".")[0])
                 for n, b, _ in piezas(root, carpeta)]
        trozos.append("**%s**\n%s" % (titulo, "\n".join(filas)))
    filas = []
    for d in sorted(os.listdir(os.path.join(root, "skills"))):
        sk = os.path.join(root, "skills", d, "SKILL.md")
        if os.path.isfile(sk):
            bloque, _ = partir_frontmatter(leer(sk))
            filas.append("- `%s` — %s" % (d, campo(bloque, "description").split(".")[0]))
    trozos.append("**Skills**\n%s" % "\n".join(filas))
    return "\n\n".join(trozos)


# --- Plan de generación --------------------------------------------------------------------------

def generar(root):
    """{ruta relativa: contenido} de TODO lo que este script produce. Orden fijo."""
    out = {}
    out[".codex-plugin/plugin.json"] = codex_plugin_json(root)
    out[".agents/plugins/marketplace.json"] = codex_marketplace_json(root)
    out["interop/codex/hooks.json"] = codex_hooks_json(root)
    for nombre, bloque, cuerpo in piezas(root, "agents"):
        out["interop/codex/agents/%s.toml" % nombre] = codex_agente(nombre, bloque, cuerpo)
        out["interop/opencode/agents/%s.md" % nombre] = opencode_agente(nombre, bloque, cuerpo)
    for nombre, bloque, cuerpo in piezas(root, "commands"):
        out["interop/codex/prompts/%s.md" % nombre] = codex_prompt(nombre, bloque, cuerpo)
        out["interop/opencode/commands/%s.md" % nombre] = opencode_comando(nombre, bloque, cuerpo)
    out["interop/opencode/opencode.json"] = opencode_config()
    out["interop/opencode/custom-agents-index.md"] = opencode_indice(root)
    # El adaptador de hooks de OpenCode es CÓDIGO fuente (vive en hooks/, con el resto de hooks);
    # aquí solo viaja su copia, para que el árbol de interop sea completo y copiable de una vez.
    out["interop/opencode/plugins/custom-agents-hooks.js"] = leer(
        os.path.join(root, "hooks", "opencode-plugin.js"))
    return dict(sorted(out.items()))


def escribir(root, plan, quiet=False):
    for rel, contenido in plan.items():
        p = os.path.join(root, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(contenido)
    if not quiet:
        print("export-interop: %d ficheros escritos (codex + opencode)" % len(plan))
    return 0


def comprobar(root, plan):
    faltan, distintos = [], []
    for rel, contenido in plan.items():
        p = os.path.join(root, rel.replace("/", os.sep))
        if not os.path.isfile(p):
            faltan.append(rel)
        elif leer(p) != contenido:
            distintos.append(rel)
    if not faltan and not distintos:
        print("export-interop --check: %d ficheros al día" % len(plan))
        return 0
    for rel in faltan:
        print("FALTA         %s" % rel)
    for rel in distintos:
        print("DESINCRONIZADO %s" % rel)
    print("\nERROR: la interop de Codex/OpenCode no refleja las piezas del repo.\n"
          "       Arréglalo con: python3 scripts/export-interop.py")
    return 1


def main():
    ap = argparse.ArgumentParser(description="Genera la interop de Codex y OpenCode desde las piezas del repo.")
    ap.add_argument("--root", default=ROOT_DEFAULT, help="raíz del plugin (por defecto, este repo)")
    ap.add_argument("--check", action="store_true", help="no escribe: falla si algo está desincronizado")
    ap.add_argument("--list", action="store_true", help="lista los ficheros que genera y sale")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    root = os.path.abspath(a.root)
    try:
        plan = generar(root)
    except (OSError, KeyError, ValueError) as e:
        print("ERROR: no pude leer las piezas del plugin en %s (%s)" % (root, e), file=sys.stderr)
        return 1
    if a.list:
        for rel in plan:
            print(rel)
        return 0
    return comprobar(root, plan) if a.check else escribir(root, plan, a.quiet)


if __name__ == "__main__":
    sys.exit(main())
