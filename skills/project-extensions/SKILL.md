---
name: project-extensions
description: >
  Crea agentes, skills, comandos, hooks, tools y servidores MCP propios en el proyecto del usuario,
  en la carpeta y el formato de cada runtime (Claude Code, Codex, OpenCode), con plantillas y una
  verificación final contra el inventario de piezas del proyecto. Nunca escribe en la caché del
  plugin. Úsala cuando el usuario diga "crea un agente para este proyecto", "crea una skill",
  "añade un comando propio", "crea un hook", "añade un MCP al proyecto", "crea una tool para
  OpenCode" o "extiende este proyecto con una pieza nueva".
---

# project-extensions — crear piezas propias del proyecto, para cada runtime

## Alcance y activación

Crea piezas **del proyecto del usuario** (o, si lo pide, de su carpeta personal): agentes, skills,
comandos, hooks, tools y servidores MCP. Cada runtime guarda lo suyo en una carpeta y un formato
distintos; esta skill pregunta para cuáles, escribe en el sitio correcto con una plantilla y
comprueba al terminar que la pieza aparece en el inventario (`project-pieces.py`, lo que ven
`/work-context` y el panel). Si trabajas dentro del repositorio de custom-agents, lee además
`references/custom-agents-repo.md`: sus reglas propias (linter, regeneración, changelog) NO aplican
a un proyecto cualquiera.

> **No escribas en la caché del plugin** (`.../plugins/cache/...`, la raíz del plugin instalado ni
> `${CLAUDE_PLUGIN_ROOT}`): una actualización la sustituye. Tus piezas van al proyecto.

## Paso 0 — ¿Para qué runtimes, y qué tipo de pieza?

Pregunta: **¿Claude Code, Codex, OpenCode o varios?** y **¿del proyecto o personal?** Sin respuesta,
propón el runtime de la sesión actual y confírmalo. Después, el tipo:

| Si necesitas… | Es un… | Plantilla |
|---|---|---|
| Un rol con prompt propio que se invoca por nombre | **agente** | `agent.claude.template.md` · `agent.opencode.template.md` · `agent.codex.template.toml` |
| Una capacidad reutilizable que se activa por descripción | **skill** | `skill.template.md` |
| Un atajo que el usuario lanza con `/nombre` | **comando** | `command.claude.template.md` · `command.opencode.template.md` |
| Reaccionar a un evento para informar | **hook informativo** | `hook.claude.settings.template.json` + `hook-informativo.template.py` |
| Código que un agente invoca con argumentos tipados | **tool** (OpenCode) | `tool.opencode.template.ts` |
| Conectar un servicio externo por protocolo MCP | **servidor MCP** | `mcp.claude.template.json` · `mcp.codex.template.toml` · `mcp.opencode.template.jsonc` |

**Busca dueño antes de crear:** lista lo que ya existe (`project-pieces.py`, ver «Verificar») y, si una
pieza cubre la necesidad, propón cambiarla en vez de abrir otra. Dudas de tipo (agente frente a
skill, kit frente a skill): `references/piece-boundaries.md`.

## Dónde va cada cosa

| Componente | Claude Code | Codex | OpenCode |
|---|---|---|---|
| Agente | `.claude/agents/<nombre>.md` | `.codex/agents/<nombre>.toml` (o roles en `.codex/config.toml`) | `.opencode/agents/<nombre>.md` (o `agent`/`agents` en `opencode.json`) |
| Skill | `.claude/skills/<nombre>/SKILL.md` | `.agents/skills/<nombre>/SKILL.md` (Codex también lee `.codex/skills/`, que el inventario no lista: usa la primera) | `.opencode/skills/<nombre>/SKILL.md`, `.claude/skills/` o `.agents/skills/` |
| Comando | `.claude/commands/<nombre>.md` | No hay carpeta de comandos de proyecto: no se inventa; usa una skill | `.opencode/commands/<nombre>.md` (o `command`/`commands` en `opencode.json`) |
| Tool | Claude Code: tools sin ejecutor genérico (se crea el script y se declara en el agente con `tools:`) | Se declara en la sesión; los scripts no se deducen como tools | `.opencode/tools/<nombre>.ts` (o `.js`): una tool por fichero |
| Hook | `.claude/settings.json` → `hooks` | `hooks.json` del runtime (mismo esquema de eventos; compruébalo en tu versión) | Plugin JS en `.opencode/plugins/` |
| MCP | `.mcp.json` (clave `mcpServers`) | `.codex/config.toml` (clave `mcp_servers`) | `opencode.json` u `opencode.jsonc` con comentarios (clave `mcp`) |

Las carpetas personales equivalentes cuelgan de `~/.claude`, `~/.codex`, `~/.agents/skills` y
`~/.config/opencode`. Para Codex no hay comandos de proyecto ni, para Claude, un ejecutor de tools: dilo al
usuario y ofrece la alternativa, no inventes una carpeta.

## Paso 1 — Nombre y descripción

- Nombre en kebab-case, único entre las piezas del proyecto; el `name:` coincide con el fichero o la
  carpeta. Por **función** (`revisor-sql`), no genérico (`helper`, `utils`).
- La `description` es la promesa de activación: qué hace, el **criterio** que aporta y los
  disparadores: termina con «Úsalo cuando el usuario diga "…", "…"». Las plantillas YAML aceptan comillas dobles dentro; en TOML o JSON no las pongas (o escápalas).

## Paso 2 — Escribir desde la plantilla

1. Copia la plantilla del runtime elegido, sustituye `{{nombre}}`, `{{descripcion}}` (y `{{servidor}}`,
   `{{comando_mcp}}`) y completa los huecos `<…>`. No dejes ningún `{{…}}` ni `<…>`.
2. **Agentes:** `tools` mínimos (los que usa de verdad); un agente de solo lectura no pide `Write`.
   `model`/`effort` según el runtime (`references/claude-code-contracts.md`).
3. **Skills:** el cuerpo es un MAPA de ≤ 200 líneas; el detalle va a `references/<tema>.md` con «lee X
   solo al llegar al paso Y».
4. **Hooks:** informan, no deciden — salida por `systemMessage`/`additionalContext`, exit 0 siempre y
   silencio si falta una dependencia. Impedir una acción (deny) es otra pieza, con pruebas propias.
5. **MCP y tools:** sin credenciales en el fichero (nombre de la variable de entorno, nunca el valor);
   si el servidor es de terceros, trátalo como código que ejecutas y **fija la versión** del paquete
   (`<paquete>@<versión>`, nunca `latest` ni sin versión). La plantilla de OpenCode nace `"enabled": false`:
   actívalo tras revisarlo. Contratos de salida y errores:
   `references/tool-observation-contracts.md`.
6. **Scripts deterministas:** los cálculos y veredictos van en un script con su prueba y exit codes;
   la prosa decide cuándo llamarlo. Lee y escribe UTF-8 explícito; degrada con aviso, no bloquees.
7. **No sobrescribas** una pieza existente sin preguntar; muestra la diferencia y espera.

## Paso 3 — Verificar con el inventario del proyecto

Ejecuta `project-pieces.py --project . --project-only --json` y comprueba que la pieza nueva aparece
para cada runtime elegido, con su nombre, y que `warnings` está vacío. El inventario no lista hooks: para un hook,
verifica que el JSON de `settings.json` parsea y prueba el script a mano con un evento de
ejemplo por stdin (exit 0 y, ante una entrada rara, silencio). Resolución de la ruta del script
y salida esperada: `references/verify-inventory.md`. El inventario **no ejecuta** nada ni prueba que la
sesión haya cargado la pieza: dilo, y pide reiniciar la sesión del runtime. Un aviso (frontmatter
inválido, campo desconocido, enlace inseguro) se corrige antes de dar la pieza por hecha.

## Referencias (lee cada una solo en su caso)

| Referencia | Cuándo leerla |
|---|---|
| [Tipo de pieza](references/piece-boundaries.md) | Paso 0, al dudar entre agente, skill, comando o kit, o al extraer algo compartido |
| [Contratos de Claude Code](references/claude-code-contracts.md) | Al escribir frontmatter, hooks, MCP o `settings.json` de Claude Code, antes de buscar en la web |
| [Contratos de herramientas](references/tool-observation-contracts.md) | Al diseñar lo que una tool, script o hook devuelve al agente: forma, exit codes, errores |
| [Flujos persistentes](references/persistent-workflows.md) | Al crear estado que sobrevive a la sesión (cola, marcador, contador) o un bucle con reintentos |
| [Diagnóstico de arquitectura](references/architecture-diagnostics.md) | Cuando un agente o hook propio falla y la causa puede estar en su contexto, memoria o herramientas |
| [Verificar el inventario](references/verify-inventory.md) | Paso 3 |
| [Reglas de custom-agents](references/custom-agents-repo.md) | Solo al trabajar en el repositorio de custom-agents |

## Anti-patrones

- **Escribir en la caché del plugin** o en una carpeta de otro runtime «porque ya existe».
- **Prosa que calcula** («suma y si supera X…») → script con prueba.
- **`tools` de más** o un hook que decide sin pruebas.
- **Skill sin disparadores** en la `description`: el runtime no sabrá cuándo activarla.
- **Credenciales en `.mcp.json`, `config.toml` u `opencode.json`.**
- **Inventar una carpeta** (comandos de Codex, tools de Claude) en vez de decir que no existe.
- **Duplicar una pieza** que ya cubre la necesidad.

## Qué NO hace

- No ejecuta tools, hooks ni servidores MCP, ni instala sus dependencias.
- No toca la caché del plugin ni la configuración global del runtime sin que el usuario lo pida.
- No sustituye la validación del cargador nativo de cada runtime.
- No publica ni versiona la pieza: eso es del flujo de trabajo del proyecto.
