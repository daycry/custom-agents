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
Además se cuentan archivos tracked: contextos 3, hooks 6, MCP configs 1, reglas
122, scripts 320, src 20 y workflows 2. Son recuentos, no evaluación semántica
ni ejecución de recursos. El soporte del control panel y restantes directorios
todavía debe identificarse y reconciliarse en T-01.

Evaluadas semánticamente en esta fase: cero. No se ejecuta código de origen.
