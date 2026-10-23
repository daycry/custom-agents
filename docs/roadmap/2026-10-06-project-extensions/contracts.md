# Contratos de descubrimiento — verificados 2026-10-06; MCP y alcance Claude 2026-10-07

Este inventario lee declaraciones locales. El runtime decide carga, permisos y
conexiones; esas decisiones no se deducen de un fichero ni se ejecutan al escanear.

| Runtime | Declaraciones de proyecto | Declaraciones de usuario | Fuente primaria |
|---|---|---|---|
| Claude Code | `.claude/agents/*.md`, `.claude/skills/*/SKILL.md`, `.claude/commands/*.md`, `.mcp.json` | `~/.claude/agents`, `~/.claude/skills`, `~/.claude/commands`; MCP en `~/.claude.json`, global y bajo `projects[<proyecto>].mcpServers` | [Agentes](https://code.claude.com/docs/en/sub-agents), [skills](https://code.claude.com/docs/en/skills), [MCP](https://code.claude.com/docs/en/mcp) |
| Codex | `.codex/agents/*.toml`, `.agents/skills/*/SKILL.md`, `.codex/config.toml` (`mcp_servers`) | `~/.codex/agents`, `~/.agents/skills`, `~/.codex/config.toml` | [Subagentes](https://learn.chatgpt.com/docs/agent-configuration/subagents), [skills](https://learn.chatgpt.com/docs/build-skills), [MCP](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) |
| OpenCode | `.opencode/agents/*.md`, `.opencode/skills/*/SKILL.md`, `.opencode/tools/*.{js,ts}`, `opencode.json`/`opencode.jsonc` (`agent`, `mcp`, `tools`) | `~/.config/opencode/agents`, `skills`, `tools`, `opencode.json`/`opencode.jsonc` | [Agentes](https://opencode.ai/docs/agents/), [skills](https://opencode.ai/docs/skills/), [tools](https://opencode.ai/docs/custom-tools/), [MCP](https://opencode.ai/docs/mcp-servers/) |

Codex busca skills desde el directorio de trabajo hasta la raíz del repositorio.
OpenCode también admite `.claude/skills` y `.agents/skills`, incluidas sus raíces
de usuario. Claude admite skills anidadas. Se recorre solo la cadena de directorios
seleccionada, sin escanear subárboles completos ni salir de la raíz de proyecto.

Los agentes Codex independientes declaran `name`, `description` y
`developer_instructions`. Estos últimos son cuerpo privado y no se exportan.
Claude permite frontmatter opcional en skills/comandos y deriva el nombre de
la carpeta/fichero. El lector no usa cuerpos privados como descripción pública.
Skills y comandos Claude comparten namespace de invocación; sus conflictos
se agrupan sin inventar precedencia. Codex/OpenCode mantienen sus contratos.
Los comandos Claude usan filename e ignoran name. Sus skills conservan name
y alias de directorio. OpenCode también deriva el nombre de agentes/comandos
Markdown del archivo: [comandos](https://opencode.ai/docs/commands/) y agentes
de la tabla. Estas identidades se verificaron el 2026-10-07.
La salida MCP conserva nombre, origen, transporte conocido y estado declarado;
omite comandos, argumentos, URLs, headers, credenciales y variables. JSONC se
parsea como datos, sin evaluar expresiones ni placeholders. Tools OpenCode se
inventarían como fuentes de definición; descubrir un archivo no acredita sus
exports ni ejecuta JavaScript/TypeScript. Los nombres reales se contrastan con la
sesión antes de invocar.

Claude admite `stdio`, `http`, `sse`, `ws` y el alias `streamable-http` de HTTP.
Una URL sin type, un transporte SDK local o un transporte sin endpoint conserva
identidad con definición inválida y aviso, sin inferir que pueda cargarse.
La desactivación de servidores normales se lee únicamente de
`projects[<proyecto>].disabledMcpServers` en `~/.claude.json`; no de un campo
enabled del servidor. Su ausencia no demuestra conexión ni habilitación.
`enabledMcpServers` afecta solo a servidores incorporados apagados por defecto;
las listas `*McpjsonServers` son aprobación, no estado de conexión. Codex y
OpenCode conservan su campo enabled declarado. No se calculan permisos efectivos.

Claude ignora hooks, mcpServers y permissionMode de agentes cargados desde un
plugin; los agentes nativos de proyecto/usuario admiten esos campos. El lector
inspecciona estos últimos, sin extender su contrato al bundle. La revisión del
guard del bundle para ese alcance permanece explícita en la fase de capacidades.
OpenCode admite permission con allow/ask/deny y reglas; el mapa tools booleano
anterior está deprecado. Se conserva su declaración, sin afirmar su efecto.

Personas: `.claude/personas/<tipo>.md` es contrato propio del plugin, con prioridad
de proyecto ya implementada en task-brief. La detección como pieza no convierte
la persona en un agente. La propiedad sigue el esquema O1 de
[project-specialization](../2026-09-09-project-specialization/design.md): pieza
con destinos anidados, hashes sha256-lf-1 y estado derivado, sin crear otro store.

El soporte de enlaces del runtime no obliga al inventario a seguirlos: la
constitución del plugin los excluye y avisa; CLOUD de OneDrive sigue el guard
compartido. Los formatos o raíces no inspeccionables declaran inventario parcial.
Configuraciones de organización, flags de sesión, cachés de otros plugins y
servidores remotos requieren evidencia explícita de la sesión; no se finge un
escaneo completo de esos entornos ni se altera su configuración.
