<!--
  FRAGMENTO COMPARTIDO: paso "Sincronizar con Confluence (opt-in)".
  Lo referencian `evaluator`, `planner`, `qa` y `documenter` como último paso de su flujo.
  Si cambia la política de opt-in, se cambia SOLO aquí.
-->

# Sincronizar con Confluence (opcional, opt-in)

Tras escribir/actualizar cualquier fichero en `docs/`, invoca la skill **`confluence-publish`** pasándole las rutas afectadas. La skill aplica el **opt-in**: si el proyecto aún no lo ha decidido, preguntará **una vez** si se quiere sincronizar con Confluence (si sí → conecta y publica; si no → lo recuerda en `.claude/confluence.json` y no vuelve a preguntar); si ya está en `enabled: false`, no hace nada. No bloquees el trabajo por esto. **Nunca** sincroniza `docs/security-scan/`.
