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

  OpenCode V2 (opencode.ai/v2/docs/build/plugins, 2026-10-08)
    interop/opencode/opencode.json     `plugins` con un paquete local; preserva permisos del consumidor.
    interop/opencode/agents/<n>.md     agentes (`mode`, `temperature`, `permission`).
    interop/opencode/commands/<n>.md   comandos (`$ARGUMENTS` funciona igual).
    interop/opencode/plugins/custom-agents/   paquete V2 de `hooks/opencode-plugin.js`.
    interop/opencode/custom-agents-index.md   snapshot consultable del índice de piezas.
                                       El hook nativo `session.context` inyecta el contexto actual.
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
> - **Delegar en otro agente:** usa `spawn_agent` con `agent_type` igual al ID nativo del rol
>   (por ejemplo `custom-agents-reviewer`) si la sesión ofrece esta herramienta.
>   {delegaciones}
> - **Guardrail:** {guardrail}
> - **Rutas:** los kits se resuelven con el `find` de la regla 5 de CONVENTIONS, que ya busca en
>   `$PWD/.codex` y `$HOME/.codex` (donde el instalador deja el plugin en Codex).
"""

PRE_AGENTE_OPENCODE = """> **Adaptación a OpenCode** (fichero generado; la fuente es `agents/{nombre}.md`).
> - **Skills:** donde el cuerpo diga «invoca la skill `X` con la herramienta Skill», en OpenCode se
>   usa la herramienta `skill` (`skill({{ name: "X" }})`). OpenCode las descubre en
>   `.opencode/skills/<nombre>/SKILL.md` (y también en `.claude/skills/`, por compatibilidad).
> - **Delegar en otro agente:** herramienta `subagent` con `agent: "custom-agents-reviewer"`.
>   {delegaciones}
> - **Guardrail:** {guardrail}
> - **Rutas:** los kits se resuelven con el `find` de la regla 5 de CONVENTIONS, que ya busca en
>   `$PWD/.opencode` y `$HOME/.config/opencode` (el global de OpenCode no es `~/.opencode`).
"""

PRE_COMANDO = """> **Adaptación a {runtime}** (fichero generado; la fuente es `commands/{nombre}.md`).
> Este comando ORQUESTA agentes. En {runtime} no hay herramienta Agent: {delegar}
> {delegaciones}
> Las skills se invocan {skills}. Todo lo demás (puertas, artefactos, ledger) no cambia.
"""

# El control declarado depende de carga/confianza y herramientas soportadas.
GUARDRAIL_CON_HOOK = {
    "implementer": ("la distribución registra control previo para el ID exacto "
                    "`{native_id}`: limita cambios en `docs/roadmap/` a `tasks.md`, "
                    "la rama de trabajo y operaciones Git destructivas reconocidas. Requiere "
                    "plugin cargado, hooks confiados y Python disponible. Solo cubre herramientas "
                    "y payloads soportados; entradas desconocidas o errores degradan con diagnóstico. "
                    "Conserva el opt-out de proyecto y no impone un sandbox universal. "
                    "La política canónica es `guardrail-check.py pre-tool --agent implementer`."),
    "architect": ("la distribución registra control previo para el ID exacto "
                  "`{native_id}`: restringe edición a `design.md`, `docs/knowledge/adr/**` "
                  "y enlaces `design:` en spec/plan. Requiere plugin cargado, hooks confiados y Python. "
                  "Solo cubre herramientas y payloads soportados; entradas desconocidas o errores "
                  "degradan con diagnóstico. Conserva el opt-out y no impone un sandbox universal. "
                  "La política canónica es `guardrail-check.py pre-tool --agent architect`."),
}
GUARDRAIL_SOLO_LECTURA = {
    "Codex": ("tu responsabilidad es revisar sin modificar archivos. El subagente usa los permisos "
              "heredados del padre: su TOML no impone un sandbox de solo lectura independiente. "
              "Una sesión padre con permisos de escritura también permite escribir al subagente. "
              "Si hace falta cambiar algo, devuelve el gap al implementador."),
    "OpenCode": ("tu responsabilidad es revisar sin modificar archivos; el agente declara "
                 "`permission.edit: deny`. Esto restringe las herramientas de edición sujetas a "
                 "ese permiso, no toda posible escritura desde una shell. Si hace falta cambiar "
                 "algo, devuelve el gap al implementador."),
}
GUARDRAIL_NINGUNO = "este agente no tiene hook de guardia propio; se aplican los guardrails del proyecto."

DELEGAR = {
    "Codex": "usa `spawn_agent` con `agent_type` igual al ID nativo del rol, si está disponible; "
             "las definiciones se copian a `.codex/agents/`.",
    "OpenCode": "usa `subagent` con el campo `agent` igual al ID nativo, definido en `.opencode/agents/`.",
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


def native_roles(root):
    """Mapa generado de los roles propios; nunca enumera agentes del consumidor."""
    roles = [n for n, _, _ in piezas(root, "agents")]
    return {"schema_version": 1, "runtimes": {
        runtime: {n: ("custom-agents:" if runtime == "claude" else "custom-agents-") + n
                  for n in roles} for runtime in ("claude", "codex", "opencode")}}


def delegaciones(runtime, mapping=None):
    roles = (mapping or native_roles(ROOT_DEFAULT))["runtimes"][runtime]
    return ("En el cuerpo, los roles propios se resuelven con este mapa: "
            + "; ".join(f"{role} → `{native}`" for role, native in roles.items())
            + ". Conserva nombres y rutas de agentes del consumidor.")


def guardrail_de(nombre, tools, runtime, mapping=None):
    if nombre in GUARDRAIL_CON_HOOK:
        mapping = mapping or native_roles(ROOT_DEFAULT)
        return GUARDRAIL_CON_HOOK[nombre].format(native_id=mapping["runtimes"][runtime.lower()][nombre])
    return GUARDRAIL_NINGUNO if (set(tools) & HERR_ESCRITURA) else GUARDRAIL_SOLO_LECTURA[runtime]


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
            # Codex (≥ 0.155, esquema serde) ya no admite `NONE` en `authentication`:
            # solo `ON_INSTALL` o `ON_USE` (lo que usa su marketplace oficial para plugins
            # locales sin auth real). Un `NONE` invalida el manifiesto ENTERO y rompe
            # `codex plugin marketplace list` para todos los marketplaces.
            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            "category": "Productivity",
            "keywords": src["keywords"],
        }],
    })


_ARG_SEGURO_RE = re.compile(r"^[A-Za-z0-9_${}/.\-]+$")
_COMANDOS_SHELL_TRADUCIBLES = ("bash", "sh")
_HOOK_RUNTIME_TARGETS = ("native-guardrail", "session-context.sh", "session-journal.sh",
                         "user-prompt-capture.sh", "subagent-progress.sh", "mark-docs-pending.sh",
                         "ledger-lint-warn.sh", "progress-line.sh")


def _hook_a_shell_form(h, evento="?"):
    """Codex no tiene el contrato de `args` (exec form) VERIFICADO como Claude Code (gap 16 de la
    revisión intento 1 de `session-end-durable-capture`, C5 · CWE-78): un hook en exec form
    (`command: bash`, `args: ["<ruta>"]`) se traduce a SHELL FORM (`command: 'bash "<ruta>"'`), más
    portable, y sin depender de que el runtime destino soporte `args` sueltos. También admite
    el launcher Node del plugin con el argumento literal session-journal.sh. El resto de campos
    se conserva aquí; codex_hooks_json aplica el máximo SessionEnd de 3 segundos.

    Un hook SIN `args` (ya en shell form: la mayoría) pasa TAL CUAL, sin tocar — no es de la
    incumbencia de esta función. Un hook CON `args` (exec form) traduce a shell form SOLO si
    `command` es literalmente `bash` o `sh` (gap 53 de la revisión intento 3, B-52 · CWE-78 latente:
    antes solo se interceptaba `command == "bash"` exacto — `/bin/bash`, `sh`, `python3 -c ...` en
    exec form se exportaban a Codex con `args` INTACTOS, exit 0, sin ningún aviso, pese a que el
    docstring prometía traducir todo exec form) Y tiene exactamente UN argumento que case el patrón
    seguro `^[A-Za-z0-9_${}/.\\-]+$`. En cualquier otro caso (≠ 1 arg, `command` que no sea
    `bash`/`sh`, o un argumento con metacaracteres) hace FALLAR el export (`ValueError`, nombrando
    el evento, el `command` y los `args`) en vez de exportar la exec form tal cual sin aviso (gap 36
    de la revisión intento 2).

    El `command` resultante se construye por INTERPOLACIÓN DIRECTA entre comillas DOBLES
    (`'%s "%s"' % (cmd, arg)`), IGUAL que el resto de hooks de `interop/codex/hooks.json` (gap 49 de
    la revisión intento 3, A-49: antes se usaba `shlex.quote`, que sobre un valor con `$`/`{`/`}`
    —como `${CLAUDE_PLUGIN_ROOT}/...`— produce comillas SIMPLES, distinto formato que los otros
    cuatro hooks del mismo fichero; no hay fuente que confirme si Codex, al expandir
    `${CLAUDE_PLUGIN_ROOT}` en `command`, lo hace igual dentro de comillas simples que dentro de
    dobles — ver `docs/INTEROP.md`, checklist M-01). La seguridad NO depende de las comillas: la da
    el patrón seguro, que EXCLUYE `(` `)` `` ` `` `"` `'` `;` `|` `&` `$(` `\\` y espacios — no hay
    nada que un atacante pueda inyectar en el argumento para romper las comillas dobles ni para que
    la shell interprete algo más que una ruta literal."""
    if not (isinstance(h, dict) and "args" in h):
        return dict(h)               # no es exec form: nada que traducir (la mayoría de los hooks)
    cmd = h.get("command")
    args = h.get("args")
    if (cmd == "node" and isinstance(args, list) and len(args) == 2
            and args[0] == "${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.mjs"
            and args[1] in ("session-journal.sh",)):
        nh = dict(h)
        nh["command"] = 'node "%s" "%s"' % tuple(args)
        if evento == "SessionEnd":
            nh["command"] += " --runtime=codex"
        nh.pop("args")
        return nh
    if not (cmd in _COMANDOS_SHELL_TRADUCIBLES and isinstance(args, list) and len(args) == 1
            and isinstance(args[0], str) and _ARG_SEGURO_RE.match(args[0])):
        raise ValueError(f"_hook_a_shell_form: el hook de {evento!r} (command={cmd!r}) tiene args "
                          f"que no se pueden traducir a shell form de forma segura ({args!r}); export abortado")
    nh = dict(h)
    nh["command"] = '%s "%s"' % (cmd, args[0])
    nh.pop("args", None)
    return nh


def codex_hooks_json(root):
    """`interop/codex/hooks.json` — los hooks del plugin filtrados y corregidos para Codex:

    - `SessionStart`: matcher `startup|resume|clear|compact`.
    - `SessionEnd`: exec form a shell form y timeout máximo 3 s (contrato Codex).
    - `UserPromptSubmit`: captura del turno con launcher compartido.
    - `SubagentStop`: existe en Codex; se mantiene.
    - `PostToolUse`: apply_patch; run-hook.mjs convierte tool_input.command a edits[].file_path.
    """
    src = json.loads(leer(os.path.join(root, "hooks", "hooks.json")))["hooks"]
    out = {}
    for evento in ("SessionStart", "UserPromptSubmit", "SubagentStop", "SessionEnd", "PreToolUse", "PostToolUse"):
        grupos = []
        for g in src.get(evento, []):
            ng = {}
            if evento == "SessionStart":
                ng["matcher"] = "startup|resume|clear|compact"
            elif evento == "PostToolUse":
                ng["matcher"] = "^apply_patch$"
            elif evento == "PreToolUse":
                ng["matcher"] = "^(Bash|apply_patch|PowerShell)$"
            elif "matcher" in g:
                ng["matcher"] = g["matcher"]
            ng["hooks"] = [_hook_a_shell_form(h, evento) for h in g.get("hooks", [])]
            launcher = 'node "${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.mjs" '
            for hook in ng["hooks"]:
                command = hook.get("command", "")
                if command.startswith(launcher):
                    # Solo los comandos conocidos del launcher propio; no mutar scripts arbitrarios.
                    suffix = command[len(launcher):]
                    for target in _HOOK_RUNTIME_TARGETS:
                        for quote in ("", '"'):
                            literal = quote + target + quote
                            if suffix in (literal, literal + " --runtime=claude"):
                                hook["command"] = launcher + literal + " --runtime=codex"
            if evento == "SessionEnd":
                for hook in ng["hooks"]:
                    if hook.get("timeout", 1) > 3:
                        hook["timeout"] = 3
            grupos.append(ng)
        if grupos:
            out[evento] = grupos
    return json_txt({"hooks": out})


def codex_agente(nombre, bloque, cuerpo, mapping=None):
    tools = tools_de(bloque)
    mapping = mapping or native_roles(ROOT_DEFAULT)
    pre = PRE_AGENTE_CODEX.format(nombre=nombre, guardrail=guardrail_de(nombre, tools, "Codex", mapping),
                                 delegaciones=delegaciones("codex", mapping))
    lineas = [cabecera("toml", "agents/%s.md" % nombre),
              "# Copia este fichero a `.codex/agents/` (proyecto) o `~/.codex/agents/` (usuario).\n",
              "name = %s" % toml_str(mapping["runtimes"]["codex"][nombre]),
              "description = %s" % toml_str(campo(bloque, "description"))]
    efecto = EFFORT_CODEX.get(campo(bloque, "effort"))
    if efecto:
        lineas.append("model_reasoning_effort = %s" % toml_str(efecto))
    # Codex 0.161.0 no proyecta sandbox_mode desde el TOML del rol; hereda permisos del padre.
    lineas.append("developer_instructions = %s" % toml_multi(pre + "\n" + cuerpo.lstrip("\n")))
    return "\n".join(lineas) + "\n"


def codex_prompt(nombre, bloque, cuerpo, mapping=None):
    pre = PRE_COMANDO.format(runtime="Codex", nombre=nombre,
                             delegar=DELEGAR["Codex"], skills=SKILLS_EN["Codex"],
                             delegaciones=delegaciones("codex", mapping))
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
    sin Write/Edit se declara `edit: deny`; la shell conserva su permiso independiente."""
    t = set(tools)
    return {
        "read": "allow", "grep": "allow", "glob": "allow", "list": "allow",
        "edit": "allow" if (t & HERR_ESCRITURA) else "deny",
        "shell": "allow" if "Bash" in t else "deny",
        "webfetch": "allow" if "WebFetch" in t else "deny",
        "websearch": "allow" if "WebSearch" in t else "deny",
        "subagent": "allow" if "Agent" in t else "deny",
        "skill": "allow",
    }


def opencode_agente(nombre, bloque, cuerpo, mapping=None):
    tools = tools_de(bloque)
    pre = PRE_AGENTE_OPENCODE.format(nombre=nombre, guardrail=guardrail_de(nombre, tools, "OpenCode", mapping),
                                    delegaciones=delegaciones("opencode", mapping))
    pares = [
        ("description", json.dumps(campo(bloque, "description"), ensure_ascii=False)),
        # Todas las piezas del plugin son subagentes: las despacha un orquestador por nombre.
        ("mode", "subagent"),
        ("temperature", TEMP_OPENCODE.get(campo(bloque, "model"), 0.2)),
        ("permission", permisos_opencode(tools)),
    ]
    return (fm_yaml(pares) + cabecera("html", "agents/%s.md" % nombre)
            + "\n" + pre + "\n" + cuerpo.lstrip("\n"))


def opencode_comando(nombre, bloque, cuerpo, mapping=None):
    pre = PRE_COMANDO.format(runtime="OpenCode", nombre=nombre,
                             delegar=DELEGAR["OpenCode"], skills=SKILLS_EN["OpenCode"],
                             delegaciones=delegaciones("opencode", mapping))
    pares = [("description", json.dumps(campo(bloque, "description"), ensure_ascii=False))]
    return (fm_yaml(pares) + cabecera("html", "commands/%s.md" % nombre)
            + "\n" + pre + "\n" + cuerpo.lstrip("\n"))


def opencode_config():
    """Registro V2 del paquete local; el contexto llega por hook sin grants globales."""
    return json_txt({
        "$schema": "https://opencode.ai/config.json",
        "plugins": ["./.opencode/plugins/custom-agents"],
    })


def opencode_indice(root):
    """Snapshot consultable del índice de piezas (`skill-index.py`).

    `--check` mantiene este fichero estático al día como referencia consultable.
    El adaptador V2 inyecta el índice y las fuentes dinámicas (roadmap, journal,
    memoria) mediante session.context, reutilizando hooks/session-context.sh.
    """
    texto = ""
    try:
        mod = _cargar_skill_index(root)
        # `construir` devuelve el dict con métricas del índice; lo que viaja es su `texto`. Sin
        # caché: aquí el fichero ES el artefacto, y `--check` es quien detecta que ha caducado.
        texto = (mod.construir(mod.piezas(root), runtime="opencode", mapping=native_roles(root)) or {}).get("texto") or ""
    except Exception:  # noqa: BLE001 — si `skill-index.py` cambia de API, índice propio (degrada)
        texto = ""
    if not texto.strip():
        texto = _indice_fallback(root)
    return ("<!-- %s desde las piezas del repo — no lo edites a mano. -->\n\n" % MARCA
            + "# custom-agents — índice de piezas\n\n"
            + "Snapshot consultable del catálogo. OpenCode V2 recibe el contexto mediante el hook\n"
              "nativo de sesión, no mediante `instructions`. Comprueba si aplica una de estas piezas: las\n"
              "skills se invocan con la herramienta `skill`, los agentes con `subagent` y su ID nativo.\n\n"
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
    roles = native_roles(root)["runtimes"]["opencode"]
    for titulo, carpeta, sufijo in (("Comandos", "commands", ""), ("Agentes", "agents", "")):
        filas = ["- `%s%s` — %s" % (roles[n] if carpeta == "agents" else n,
                                    sufijo, campo(b, "description").split(".")[0])
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
    mapping = native_roles(root)
    out["agent-kits/shared/native-roles.json"] = json_txt(mapping)
    out[".codex-plugin/plugin.json"] = codex_plugin_json(root)
    out[".agents/plugins/marketplace.json"] = codex_marketplace_json(root)
    out["interop/codex/hooks.json"] = codex_hooks_json(root)
    for nombre, bloque, cuerpo in piezas(root, "agents"):
        out["interop/codex/agents/%s.toml" % mapping["runtimes"]["codex"][nombre]] = codex_agente(nombre, bloque, cuerpo, mapping)
        out["interop/opencode/agents/%s.md" % mapping["runtimes"]["opencode"][nombre]] = opencode_agente(nombre, bloque, cuerpo, mapping)
    for nombre, bloque, cuerpo in piezas(root, "commands"):
        out["interop/codex/prompts/%s.md" % nombre] = codex_prompt(nombre, bloque, cuerpo, mapping)
        out["interop/opencode/commands/%s.md" % nombre] = opencode_comando(nombre, bloque, cuerpo, mapping)
    out["interop/opencode/opencode.json"] = opencode_config()
    out["interop/opencode/custom-agents-index.md"] = opencode_indice(root)
    # El adaptador de hooks de OpenCode es CÓDIGO fuente (vive en hooks/, con el resto de hooks);
    # aquí solo viaja su copia, para que el árbol de interop sea completo y copiable de una vez.
    out["interop/opencode/plugins/custom-agents/index.js"] = leer(
        os.path.join(root, "hooks", "opencode-plugin.js"))
    out["interop/opencode/plugins/custom-agents/package.json"] = json_txt({
        "name": "custom-agents-hooks", "type": "module", "main": "index.js",
    })
    return dict(sorted(out.items()))


def obsoletos(root, plan):
    """Exports propios retirados: nombre y cabecera exactos, sin barrer otros árboles."""
    out = []
    for runtime, extension, estilo in (("codex", ".toml", "toml"), ("opencode", ".md", "html")):
        folder = os.path.join(root, "interop", runtime, "agents")
        if not os.path.isdir(folder):
            continue
        for filename in sorted(os.listdir(folder)):
            relative = f"interop/{runtime}/agents/{filename}"
            if relative in plan or not filename.endswith(extension):
                continue
            path = os.path.join(folder, filename)
            if not os.path.isfile(path) or os.path.islink(path):
                continue
            text = leer(path)
            if estilo == "html":
                _, text = partir_frontmatter(text)
            pattern = (r"^# " if estilo == "toml" else r"^<!-- ") + re.escape(MARCA) + r" desde agents/([a-z0-9-]+)\.md — no lo edites a mano\."
            match = re.match(pattern, text)
            if not match:
                continue
            role = match.group(1)
            if filename in (role + extension, "custom-agents-" + role + extension):
                out.append(relative)
    return out


def escribir(root, plan, quiet=False):
    for rel, contenido in plan.items():
        p = os.path.join(root, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(contenido)
    for relative in obsoletos(root, plan):
        os.unlink(os.path.join(root, relative.replace("/", os.sep)))
    if not quiet:
        print("export-interop: %d ficheros escritos (codex + opencode)" % len(plan))
    return 0


def comprobar(root, plan):
    faltan, distintos = [], []
    retirados = obsoletos(root, plan)
    for rel, contenido in plan.items():
        p = os.path.join(root, rel.replace("/", os.sep))
        if not os.path.isfile(p):
            faltan.append(rel)
        elif leer(p) != contenido:
            distintos.append(rel)
    if not faltan and not distintos and not retirados:
        print("export-interop --check: %d ficheros al día" % len(plan))
        return 0
    for rel in faltan:
        print("FALTA         %s" % rel)
    for rel in distintos:
        print("DESINCRONIZADO %s" % rel)
    for rel in retirados:
        print("OBSOLETO      %s" % rel)
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
