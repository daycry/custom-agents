# Tus agentes, skills, personas, tools y MCP

[English](en/PROJECT-EXTENSIONS.md) · **Español**

El plugin reconoce declaraciones locales del proyecto y del usuario mediante
`agent-kits/shared/project-pieces.py`. El lector del bundle se comparte entre
`/work-context`, los briefs y plugin-panel. Encontrar una declaración no prueba
que la sesión la haya cargado, conectado o autorizado; el runtime decide eso.

## Dónde añadirlas

Usa las carpetas y formatos del entorno en que trabajas. No copies tus piezas
al caché del plugin: una actualización sustituye ese bundle.

| Componente | Claude Code | Codex | OpenCode |
|---|---|---|---|
| Agentes del proyecto | `.claude/agents/<nombre>.md` | `.codex/agents/<nombre>.toml`; también roles en `.codex/config.toml` | `.opencode/agents/<nombre>.md`; también `agent` en `opencode.json`/`.jsonc` |
| Skills del proyecto | `.claude/skills/<nombre>/SKILL.md` | `.agents/skills/<nombre>/SKILL.md` | `.opencode/skills`, `.claude/skills` o `.agents/skills`, con `<nombre>/SKILL.md` |
| Comandos propios | `.claude/commands/<nombre>.md` | El lector no atribuye comandos a Codex por una carpeta de proyecto | `.opencode/commands/<nombre>.md`; también `command` en la configuración |
| Fuentes de tools | Nombres declarados por agentes; no hay ejecutor genérico del plugin | Nombres declarados en la sesión; no se deducen exports de scripts | `.opencode/tools/*.{js,ts}`; el lector lista fuentes y no ejecuta sus exports |
| MCP del proyecto | `.mcp.json`, clave `mcpServers`; también declaraciones por agente | `.codex/config.toml` y agentes TOML, clave `mcp_servers` | `opencode.json`/`.jsonc`, clave `mcp` |

Los agentes Markdown necesitan frontmatter de su runtime. Los agentes Codex
independientes usan `name`, `description` y `developer_instructions`. Las skills
Codex/OpenCode usan frontmatter `name`/`description`; Claude admite campos
opcionales y comandos Markdown sin frontmatter, con nombre derivado de la ruta.
Cuando no hay descripción declarada, el lector la deja vacía sin extraer el cuerpo.
El contenido se consulta bajo demanda. Este inventario
extrae metadata pública; no reemplaza la validación del cargador nativo.

Las raíces personales normales son `~/.claude`, `~/.codex`, `~/.agents/skills`
y `~/.config/opencode`. Claude guarda MCP personales y locales del proyecto en
`~/.claude.json`; el lector solo considera el proyecto seleccionado. Para otra
raíz usa `--user-root <runtime>=<ruta>` explícitamente. No se deduce una raíz
personalizada ni disponibilidad a partir de variables privadas del entorno.

Las skills anidadas se inspeccionan en la cadena desde `--cwd` hasta `--project`;
no se recorre todo el repositorio. El paquete debe estar dentro del proyecto.

## Cómo entran en una tarea

1. `/work-context` aplica `capability-check.md`: selecciona guías del bundle e
   inventaría las extensiones pertinentes del runtime actual.
2. Planner elige las necesarias por contrato y registra sus IDs y fuentes:

   ```markdown
   - **Extensiones**: ext-<identificador entregado por el lector>
   - **Procedencia de extensiones**: especialista de facturación del proyecto; revisar su referencia antes de usarlo.
   ```

3. Implementer, reviewer y qa comparten esa selección. El brief vuelve a leer
   las declaraciones y añade referencias acotadas, sin precargar prompts o
   manuales. Una pieza borrada o de otro runtime deja aviso y se omite.
4. El agente consulta el contenido pertinente y contrasta las capacidades reales
   de la sesión antes de invocar un agente, tool o MCP. La extensión complementa
   al rol del ciclo; no sustituye sus responsabilidades ni puertas de calidad.

Los IDs son estables para una fuente dentro del proyecto. Las raíces personales
se distinguen con un identificador opaco, sin exportar su ruta absoluta. Los
duplicados se conservan y el conflicto se muestra por nombre, runtime y tipo.
No hay una precedencia universal entre los tres runtimes.
Claude comparte el nombre de invocación entre comandos y skills; sus colisiones
se muestran también entre ambos tipos y frente a las piezas del bundle.
Los comandos Claude y los agentes/comandos Markdown de OpenCode usan el nombre
del archivo, aunque declaren otro name. Las skills Claude conservan el nombre
de frontmatter y el alias del directorio para detectar conflictos potenciales;
el runtime determina la invocación que prevalece.

## Personas de dominio

Es el contrato propio del plugin, compartido por los tres entornos. Crea un
perfil corto en `.claude/personas/facturacion.md` y etiqueta la tarea:

```markdown
- **Tipo**: facturacion
```

El brief prioriza esa persona de proyecto, después el catálogo del plugin y,
si no encuentra ninguna, continúa sin persona con aviso. Los tipos son libres.
Este perfil sí entra en el brief con sus límites existentes; no se convierte en
un agente. Las personas personales detectadas se pueden referenciar como
material; no añaden un cuarto escalón automático a esa cascada.

`personas/` es una convención de custom-agents. La documentación oficial
consultada no define un cargador de `.codex/personas/` o `.opencode/personas/`.
La especialización nativa se expresa en las instrucciones de los agentes;
las reglas generales del proyecto usan `AGENTS.md`. La opción `personality`
de Codex controla el estilo de comunicación, no el dominio de una tarea.
El contraste y el diseño pendiente están en
[contratos de personas](roadmap/2026-10-07-catalog-capabilities/contracts.md#personas-e-instrucciones-nativas).

## Panel e inventario directo

`/plugin-catalog` incluye el proyecto actual. El panel mantiene conteos separados
del bundle y las extensiones; permite buscar y filtrar por tipo, origen y runtime.
Cada pieza muestra fuente, ID, conflictos, propiedad y disponibilidad sin verificar.
Los MCP con una definición Claude inválida se señalan. Su desactivación se lee
de las preferencias del proyecto en `~/.claude.json`; los otros runtimes
conservan el campo enabled declarado. Ninguno de esos estados prueba conexión.

```powershell
python skills/plugin-panel/scripts/build_panel.py --project . --runtime codex --html panel.html
python agent-kits/shared/project-pieces.py --project . --runtime codex --project-only --json
```

Para revalidar una selección repite `--select <id>` en el lector. Admite como
máximo 20 IDs. En `task-brief.py` usa `--runtime` y, si se inspeccionaron otras
raíces o un paquete anidado, los mismos valores en `--extensions-home`,
`--extensions-cwd` y `--extensions-user-root`. `--extensions-project-only`
excluye fuentes personales. Las referencias de extensiones ocupan ≤1000
caracteres y comparten el presupuesto auxiliar del brief.

## Propiedad y límites

No necesitas registro para que se detecten tus piezas. Si existe
`.claude/pieces.json`, se valida el esquema O1 de [especialización](SPECIALIZATION.md)
y se comparan hashes completos con LF normalizado. Los estados son gestionada,
modificada, no gestionada o desconocida si el registro es inválido. Los destinos
ausentes se señalan. Este estado no concede permisos ni permite sobrescrituras.

El descubrimiento no crea el registro, adopta, genera, reconstruye o modifica
piezas; esas operaciones mantienen su plan de especialización independiente.
Tampoco ejecuta scripts/CLI del consumidor, conecta servidores ni resuelve
placeholders de entorno o archivos. Omite cuerpos privados, comandos MCP,
argumentos, URLs, headers, variables y credenciales; aplica la redacción central.

Se limita a 512 KiB por archivo, 8 MiB de presupuesto total de lectura,
1000 piezas y profundidad 32 en configuraciones. Los directorios con más de
1000 entradas se omiten completos con aviso; el resultado no depende del orden
del filesystem. Los errores y lecturas rechazadas consumen reserva; los formatos
YAML complejos fuera del extractor
acotado dejan un aviso. Los enlaces se excluyen con el guard compartido de
OneDrive. Un inventario parcial queda marcado y no bloquea el ciclo.

[Contratos nativos y fuentes verificadas](roadmap/2026-10-06-project-extensions/contracts.md)
· [Panel](PLUGIN-PANEL.md) · [Flujo compartido](FLOWS.md).
