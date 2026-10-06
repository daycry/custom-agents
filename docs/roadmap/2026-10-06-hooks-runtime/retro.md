# Retro — hooks-runtime, 2026-10-06

La selección de intérprete en Windows priorizaba el lanzador WSL de System32 y los scripts requerían python3, aunque el Python nativo se llamaba python. Codex recortaba el timeout heredado de Claude5 a3. Durante la verificación se detectó que el exportador había quedado desactualizado respecto a PostToolUse y compact.

La solución comparte launcher entre clientes y usa Python nativo directamente para capturas. Se probaron escrituras efectivas, payload de parche y búsqueda de guardias en kit plano/caché anidada, con precedencia de proyecto. Las cachés activas Claude/Codex tienen hotfix con backup; no hay bundle local custom-agents en OpenCode. No se publicaron versiones ni se ejecutaron sesiones de modelo.

El consumo de tokens/horas no está medido en esta sesión; no se añade una muestra al ratio de calibración. Reiniciar clientes para cargar registros nuevos; la futura publicación deberá incorporar el hotfix para que sobreviva a reinstalaciones.
