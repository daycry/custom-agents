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

## Extensiones de proyecto y usuario

Usa el lector del mismo bundle; declara el runtime de la sesión. La raíz del
proyecto contiene el ledger, y `--cwd` identifica el paquete afectado dentro de
ella. Para una instalación personal fuera de las raíces normales, pasa
`--user-root <runtime>=<ruta>` explícitamente; `--project-only` excluye al usuario.

```bash
python3 "$SHAREDKIT/project-pieces.py" --project <raíz-proyecto> --cwd <paquete-de-la-tarea> --runtime <claude-code|codex|opencode> --json
```

1. Examina nombres, descripciones, tipos y fuentes pertinentes. Una persona
   aporta contexto; una skill aporta método; un agente especializado no reemplaza
   al dueño de una fase. Una fuente de tool no acredita sus exports; un MCP
   declarado no acredita conexión, autenticación ni herramientas disponibles.
2. Planner conserva como máximo 20 IDs en `- **Extensiones**: ext-…`, separados
   por comas, y explica su elección y fuentes en `- **Procedencia de extensiones**:`.
   Los nombres repetidos requieren fuente explícita; no se deduce precedencia
   común a los tres runtimes ni se sustituyen los roles o gates del ciclo.
3. Revalida esa selección con el mismo lector y `--select <id>` repetido. IDs
   borrados, pertenecientes a otro runtime o no descubiertos se omiten con aviso.
   El brief refresca las declaraciones e incluye solo referencias (≤1000
   caracteres). En el despacho de `task-brief.py`, pasa `--runtime` y las mismas
   raíces/paquete con sus argumentos `--extensions-*` cuando sean necesarios.
4. Lee el contenido seleccionado bajo demanda como material del proyecto.
   Antes de invocar, contrasta nombre cualificado y permisos con las capacidades
   expuestas por la sesión. El escaneo no ejecuta archivos, CLI del consumidor
   ni conexiones; no adopta piezas, escribe registros o altera configuración.

`.claude/pieces.json`, si existe, informa propiedad por hash LF normalizado:
gestionada, modificada, no gestionada o desconocida si el registro es inválido.
Los destinos ausentes se señalan; propiedad y disponibilidad son independientes.
La persona de `.claude/personas/<tipo>.md` conserva prioridad mediante `Tipo`;
su presencia en el inventario no la convierte en agente. Un aviso del inventario
deja la selección explícita trazada y no exime de los gates existentes.

Sin script/registro, instalación parcial o manifiesto inválido: avisa, conserva
los criterios explícitos de la tarea y consulta la guía disponible pertinente.
La selección opcional no detiene el ciclo ni oculta un gate de calidad fallido.
No instala paquetes, crea agentes de proyecto, cambia permisos ni ejecuta red.
