# Contratos iniciales verificados — 2026-10-07

Versiones locales, obtenidas con --version: Codex CLI 0.160.1, Claude Code
2.1.287, OpenCode 2.0.12. Son versiones observadas, no mínimos de soporte
definitivos. El plan todavía no acredita carga ni ejecución nativa de guardias.

| Runtime | Hecho contrastado | Implicación para la implementación |
|---|---|---|
| Claude | Agentes de plugin ignoran hooks, mcpServers y permissionMode de frontmatter; hooks del plugin también reciben eventos de subagentes con agent_id/agent_type | Verificar el despacho desde el plugin y filtrar identidad propia; no atribuir protección al frontmatter ignorado |
| Codex | PreToolUse cubre herramientas locales, Bash/apply_patch y MCP; su documentación advierte excepciones. Los hooks no gestionados requieren confianza de su definición actual | Contrastar esquema y datos de identidad por evento; probar bloqueo y carga confiada sin anunciar una frontera universal |
| OpenCode V2 | El API registra callbacks en setup mediante ctx.tool.hook; difiere del objeto V1 de hooks por string | El adaptador actual requiere comparación y prueba de carga V2; no basta su suite de fixtures V1 |

Fuentes abiertas y leídas: [Claude hooks](https://code.claude.com/docs/en/hooks),
[Claude subagents](https://code.claude.com/docs/en/sub-agents),
[Codex hooks](https://learn.chatgpt.com/docs/hooks),
[Codex packaging](https://developers.openai.com/plugins/build/plugins),
[OpenCode migration](https://opencode.ai/v2/docs/build/plugins/migrate-v1) y
[OpenCode V2 plugins](https://opencode.ai/v2/docs/build/plugins).

No se infiere agent_type en PreToolUse Codex porque lo documente otro evento o
Claude. No se usa una transcripción privada como interfaz estable de identidad.
Los esquemas/código del runtime instalado y una prueba nativa deben resolver
esas incógnitas antes de elegir el mecanismo de guardia.

## Corpus reconciliado

Los 455 hashes de piezas principales coinciden con la revisión fijada y el
registro de decisiones de fase 1: 293 skills, 68 agentes y 94 comandos. Helper
privado reconcile_catalog_corpus.py, resultado catalog-corpus-reconciled.json.
El inventario completo terminó: 4.212 archivos tracked, 455 bundles
estructurales, tres entradas de panel y 30 archivos relacionados con paneles.
[corpus.json](corpus.json) conserva hashes, medidas y categorías;
[corpus.md](corpus.md) delimita la evidencia y
[audit-contract.md](audit-contract.md) fija las fichas. La pertenencia a un
directorio no acredita dependencias ni callers; su lectura sigue pendiente.

Evaluadas semánticamente en esta fase: cero. No se ejecuta código de origen.

## Prueba nativa OpenCode 2.0.12

Fuente oficial fijada al tag de la versión instalada, commit
`2670273ff17da96f85c5826ced57aa1b368754fa`. Se leyeron los esquemas de config,
tool y permission, normalización V1/V2, loader de módulos, registro/despacho de
hooks, puente promise, supervisor de activación y fuentes de instrucciones.
[runtime-probes.json](runtime-probes.json) conserva el resultado público.

La prueba ejecutó el binario instalado con `serve --stdio` y peticiones locales
a su API. Proyecto, configuración, home de prueba y raíces XDG temporales
propios; entorno sin credenciales heredadas, discovery de proyecto desactivado,
actualización/fetch de modelos apagados, MCP de fixture desactivado y sin prompts
ni warming. El proceso terminó con exit 0. No se ejecutó código del corpus.

Resultados observados:

- Una copia byte a byte del adaptador actual, SHA-256
  `1092f3b894c5ee208d4eb9a46ed76361015180632207ec7edf630dcd4cb65bf9`,
  queda en estado failed: falta la definición default con id y setup/effect.
- El control positivo propio con id y setup carga como active, ejecuta setup y
  registra execute.before y evaluate mediante los dominios tool y permission.
  Es prueba de carga y registro; no acredita todavía bloqueo ni ejecución de tool.
- Agentes de fixture con agent V1 y agents V2 aparecen en el cargador nativo.
  command/commands se normalizan a commands; permission a reglas permissions;
  el MCP V1 a mcp.servers y enabled:false a disabled:true. La compatibilidad de
  configuración no traduce el export de hooks V1 a V2.
- La primera lectura del inventario puede estar vacía durante activación. La
  prueba espera la activación nativa mediante integration.list antes del veredicto;
  las observaciones tempranas vacías no se clasifican como fallos del plugin.

El esquema de tool leído incluye agent/sessionID/messageID/id en before/after;
before permite rechazo mediante Tool.Error. El de permission.evaluate incluye
agent opcional, action/resources y effect mutable. T-09 debe probar los caminos
reales y su alcance por rol; no basta registrar callbacks.

El lector propio de extensiones todavía usa las formas de configuración V1 de
OpenCode. Debe incorporar las formas V2 y su estado disabled con evidencia de
selección y briefs; ese ajuste forma parte del diseño e integración pendientes.
Las instrucciones configuradas se conservan en config.get, pero el código de
la fuente nativa de instrucciones lee AGENTS.md. Conservar un campo no acredita
cargar su contenido. La integración debe resolverlo y probarlo, sin confundir
normalización de configuración con aplicación efectiva.

Referencias: [configuración](https://opencode.ai/v2/docs/config/),
[API de plugins](https://opencode.ai/v2/docs/build/plugins/),
[normalización de la versión fijada](https://github.com/anomalyco/opencode/blob/2670273ff17da96f85c5826ced57aa1b368754fa/packages/core/src/config/normalize.ts),
[loader fijado](https://github.com/anomalyco/opencode/blob/2670273ff17da96f85c5826ced57aa1b368754fa/packages/core/src/plugin/module.ts),
[contrato de herramientas fijado](https://github.com/anomalyco/opencode/blob/2670273ff17da96f85c5826ced57aa1b368754fa/packages/plugin/src/promise/tool.ts).

## Identidad en el código de Codex 0.160.1

Se fijó la fuente oficial al tag rust-v0.160.1, commit
`d27764b82f7118f674371e6d6e76271d9d606edb`. El esquema generado de PreToolUse
sí contiene agent_id y agent_type opcionales, aunque la tabla de la página
de hooks no los enumere. schema.rs omite esos campos cuando no hay contexto
de subagente; events/pre_tool_use.rs los serializa desde ese contexto.

El constructor de core/src/hook_runtime.rs los proporciona para sesiones
SubAgent::ThreadSpawn: agent_id es el thread ID del hijo y agent_type el rol
solicitado, con fallback al rol por defecto. La sesión raíz y otras fuentes
no reciben ese contexto. tools/registry.rs consulta el resultado del hook
antes de ejecutar la herramienta y devuelve el bloqueo al modelo.

Esto resuelve la incógnita del contrato de identidad para esa versión; no
acredita todavía carga del plugin, confianza ni despacho en una sesión real.
T-09 debe probarlos, incluidos raíz sin campos, otros roles, colisiones con
agentes del consumidor y los caminos de tool que no emiten PreToolUse.
No se introduce un registro basado en transcripciones para suplir la identidad.

La [documentación oficial de hooks](https://learn.chatgpt.com/docs/hooks)
remite a los esquemas y advierte que main puede diferir de la release;
esta lectura usa la revisión de la versión instalada, no main.
