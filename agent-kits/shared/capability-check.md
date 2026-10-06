# Selección común de capacidades

Aplica este paso antes de diseñar, planificar, implementar, revisar o probar.
Resuelve el kit shared del bundle desde las raíces del runtime; el proyecto
consumidor es solo dato y nunca selecciona qué script se importa o ejecuta.

```bash
SHAREDKIT="$(find "$PWD/.claude" "$PWD/.codex" "$PWD/.opencode" "$HOME/.claude" "$HOME/.codex" "$HOME/.config/opencode" -type d -path '*agent-kits/shared' 2>/dev/null | head -1)"
python3 "$SHAREDKIT/capability-route.py" --project <paquete-de-la-tarea> --role <agente> --area <area> --json
```

El registro `capability-catalog.json` es la fuente de criterios de selección.
Roles/fases/stacks/áreas son vocabularios cerrados del script; manifiestos se leen
con límites de bytes/profundidad y sin seguir enlaces. En un monorepo usa el
paquete afectado. Añade `--stack` solo si la tecnología está declarada para la
tarea; la salida distingue esa declaración de detección en manifiestos.

1. Escoge áreas pertinentes al contrato de la tarea: research, api, data,
   frontend, accessibility, performance, delivery, mcp, security, testing,
   memory, catalog, evaluation, dependencies o documentation. No actives todas.
2. Lee únicamente los mapas seleccionados y las referencias del cambio. La
   selección no acredita disponibilidad de tools, ejecución, calidad ni permisos.
3. Planner registra IDs separados por comas en `- **Capacidades**:` y motivo
   en `- **Procedencia de capacidades**:` de la tarea. Architect,
   implementer, reviewer y qa comparten esos criterios y escenarios; un cambio
   de selección por hechos nuevos se explica en ese mismo ledger.
4. Los métodos fijos del ciclo (TDD configurado, revisión independiente, qa-gate,
   Knowledge Gate y cierre) siguen aplicándose aunque no aparezcan en el selector.
   La memoria local se consulta con knowledge-check; no precargues su histórico.

Sin script/registro, instalación parcial o manifiesto inválido: avisa, conserva
los criterios explícitos de la tarea y consulta la guía disponible pertinente.
La selección opcional no detiene el ciclo ni oculta un gate de calidad fallido.
No instala paquetes, crea agentes de proyecto, cambia permisos ni ejecuta red.
