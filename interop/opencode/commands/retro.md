---
description: "Retrospectiva de una iniciativa CERRADA — compara estimado vs real (horas, tokens, coste), captura causas de desviación y aprendizajes, y alimenta el histórico de calibración que el evaluator usa para estimar mejor las siguientes. Escribe retro.md en la carpeta de la iniciativa y una fila en docs/roadmap/CALIBRATION.md."
---
<!-- GENERADO por scripts/export-interop.py desde commands/retro.md — no lo edites a mano.
     Regenera con `python3 scripts/export-interop.py`; el porqué está en `docs/INTEROP.md`. -->

> **Adaptación a OpenCode** (fichero generado; la fuente es `commands/retro.md`).
> Este comando ORQUESTA agentes. En OpenCode no hay herramienta Agent: usa `subagent` con el campo `agent` igual al ID nativo, definido en `.opencode/agents/`.
> En el cuerpo, los roles propios se resuelven con este mapa: analyst → `custom-agents-analyst`; architect → `custom-agents-architect`; documenter → `custom-agents-documenter`; evaluator → `custom-agents-evaluator`; implementer → `custom-agents-implementer`; knowledge-curator → `custom-agents-knowledge-curator`; nemesis → `custom-agents-nemesis`; planner → `custom-agents-planner`; qa → `custom-agents-qa`; reviewer → `custom-agents-reviewer`. Conserva nombres y rutas de agentes del consumidor.
> Las skills se invocan con la herramienta `skill` (`skill({ id: "nombre" })`). Todo lo demás (puertas, artefactos, ledger) no cambia.

# /retro — cerrar el bucle de aprendizaje

Cuando una iniciativa termina (plan `completado`, spec `implementada`), esto convierte su
experiencia en **datos de calibración** para estimar mejor las próximas. Iniciativa: **$ARGUMENTS**.

> **Puerta de cierre (memory-retrieval T-17, spec CA-23).** `/dev-cycle` Fase 6 no declara una iniciativa cerrada sin esta
> retro: su paso 8 ejecuta `python3 "$SHAREDKIT/retro-gate.py" docs/roadmap/<fecha>-<slug>`, que exige `retro.md` con
> frontmatter y la fila de la iniciativa en `CALIBRATION.md` (exit 1 si falta algo, con el comando para arreglarlo).
> Aquí no se automatiza *escribir* la retro —las causas las escribe quien las conoce—, solo *exigirla*.

## Pasos
1. **Localiza y valida** la carpeta `docs/roadmap/<fecha>-<slug>/`. Si el plan no está `completado`, dilo y para (la retro es de iniciativas cerradas).
2. **Extrae los números** con la skill `roadmap-dashboard` (`--json`, campos `progreso` y `generacion` de esa iniciativa): horas humanas/IA/supervisión y tokens **real vs est**, el coste de `evaluation.md`, y los **tokens medidos** (bloques `generacion:` de los artefactos + mediciones por tarea si las hubo). Calcula desviaciones.
2-bis. **Calcula el ratio real tokens→hora** de la iniciativa: `tokens facturables medidos ÷ horas-IA reales validadas` (facturables = entrada + creación de caché + salida; la lectura de caché no cuenta — misma convención que `usage-meter.py`). Solo si hay datos **medidos** (`fuente: medido`); si todo es estimado, **no calibres con humo**: ver el paso 5 para cómo se escribe esa celda.
2-ter. **Journal de la iniciativa (si existe).** Si hay `docs/knowledge/journal/` con entradas cuyo `iniciativa:` sea este slug (`grep -l "^iniciativa: <slug>" docs/knowledge/journal/*.md`), léelas en orden: sus `decisiones`, `pendientes`, `tareas_cambiadas` y `ficheros_tocados` son una fuente **objetiva** de causas de desviación (sesiones cortas que no cerraron tarea, re-aperturas, ficheros fuera del plan) — úsalas para proponer causas en el paso 3, no para sustituir la respuesta del usuario. Sin journal, sigue sin él.
2-quater. **Candidatas a lección desde el journal (consulta episódica).** Localiza `$SHAREDKIT` como en el paso 7 y ejecuta `python3 "$SHAREDKIT/journal.py" candidatas --root .` (opcional `--iniciativa <slug>`). El patrón determinista repetido en **≥2 sesiones distintas** aparece con la etiqueta histórica `estado: propuesta` y evidencia de fecha, fichero y `session_id`; una sola sesión no se propone y sin journal sale vacío (exit 0). Es salida de consulta, no un candidato persistido ni verdad validada. Muestra la lista al usuario tal cual; los aprendizajes que elija pueden pasar al 4-bis con esas fuentes, sin copiar `estado` ni aprobación automática. Sin python3/kit, sigue sin este paso.
3. **Pregunta al usuario las causas** (breve, 2-3 preguntas): ¿qué explicó la desviación principal? ¿qué incógnita de la spec resultó cara? ¿qué se haría distinto? Registra respuestas literales, sin adornar.
4. **Escribe `retro.md`** en la carpeta de la iniciativa: tabla est vs real con desviaciones, causas, aprendizajes, y una línea de "ajuste sugerido" (p. ej. "las tareas de integración salieron +40 %: estimarlas con margen extra"). Empieza por un frontmatter mínimo (`---` · `retro: <slug>` · `fecha: AAAA-MM-DD` · `---`, cerrado con `---` exacto) y el título `# Retro — <slug>`; la puerta `retro-gate.py` acepta las retros antiguas sin frontmatter (título + cuerpo), pero no un fichero vacío, solo títulos o con el frontmatter sin cerrar.
4-bis. **Segunda salida: propuestas técnicas (siempre activa, D3).** Resuelve `$SHAREDKIT` una vez con el comando del paso 7. De `retro.md` y las candidatas del journal seleccionadas por el usuario, separa números (paso 5) de lo cualitativo técnico. Aplica `"$SHAREDKIT/knowledge-write.md"`: trampa comprobada (≥1 ciclo de depuración o garantía rota/casi rota) o aprendizaje de proceso transversal, con fuentes reales. Propón sin `estado` mediante `knowledge-curation.py propose`, productor `retro`; no crees GOT/LES legacy ni índice manual. Si alimenta números y lección, enlaza retro/CALIBRATION y la ruta pending devuelta, sin duplicar texto. Muestra `Estado: [actualizado|sin cambios|pendiente]`: actualizado sólo con salida real de propose, sin cambios si nada cruza el umbral, pendiente si falta fragmento/servicio o falla la persistencia; continúa sin fallback Write/Edit de memoria.

   **Handoff tardío.** Esta retro sucede después del Knowledge Gate principal. Si hay nuevas
   propuestas persistidas, entrega explícitamente a `knowledge-curator` sus rutas/SHA y fuentes;
   si la curación queda para después, deja ruta/ID de propuesta y estado pending visibles en
   retro y resumen. Sin servicio, muestra propuesta pendiente de persistir y motivo, sin ruta
   ficticia. La selección del usuario y cerrar retro no aprueban memoria: Curator juzga,
   consulta approved y legado aceptado pertinente, y aplica mediante el servicio con SHA,
   motivo e ID obligatorio al aprobar. Conflictos/alto impacto requieren resolución humana
   trazada; no se promueve ni reinterpreta el legado.
5. **Añade una fila** a `docs/roadmap/CALIBRATION.md` (créalo si falta; una tabla: fecha · slug · desv. producción % · desv. tokens % · **tokens/hora (medido)** · causa principal · ajuste sugerido). Este fichero es el **histórico que lee `evaluator`** al estimar, y de la columna `tokens/hora` toma `usage-meter.py` la **mediana** como ratio calibrado (precedencia sobre el default de `estimation-defaults.md`). Reglas de formato: mantén el literal `tokens/hora` en el encabezado (lo busca el parser) y escribe el ratio como **número entero sin abreviar** (`300000`, no `300k` — las abreviaturas las tolera el parser, pero el entero es inequívoco). Tras la fila, actualiza la línea-resumen bajo la tabla: `> Ratio vigente: <mediana> tokens/hora (mediana de N muestras)` — así el nº de muestras queda visible sin contar filas. **Cuando NO hay ratio medido, la celda se marca `(estimado)`, no se deja vacía** (T-17, arista E7 de `docs/agents/CONTRACTS.md`): escribe en la celda `tokens/hora` el literal `**(estimado)**` seguido del motivo en una frase (p. ej. «heredó el ratio vigente, no lo midió» o «sin medida independiente de horas: derivarlo sería circular»). Dos razones para marcar en vez de vaciar: la celda vacía no distingue «no se midió» de «se olvidó rellenar», y una celda con un número heredado —que es lo que pasaba— **entraba en la mediana y la volvía circular**. `usage-meter.py` (`_ratio_calibrado`) descarta toda celda que contenga `(estimado)`, así que la marca es la que decide si la fila calibra o no. Deja la celda **vacía** solo si no hay ni estimación. Tras marcar, recalcula la línea-resumen: el `N` de «mediana de N muestras» cuenta solo las filas que SÍ calibran. **Sin regresión en el resto**: el literal `tokens/hora` del encabezado y el formato entero de los ratios medidos no cambian.
6. Cierra con el titular: desviación global y el aprendizaje nº1.
7. **Sincronizar con Confluence (opcional).** Aplica el paso compartido `"$SHAREDKIT/confluence-optin.md"` (skill `confluence-publish` con opt-in) sobre `retro.md` y `CALIBRATION.md`. Localízalo con `SHAREDKIT="$(find "$PWD/.claude" "$PWD/.codex" "$PWD/.opencode" "$HOME/.claude" "$HOME/.codex" "$HOME/.config/opencode" -type d -path '*agent-kits/shared' 2>/dev/null | head -1)"`. Fallback si no está: invoca `confluence-publish` respetando su opt-in, sin bloquear el cierre; nunca sincronices `docs/security-scan/`.

## Reglas
- **Sin culpa, con datos.** Causas y aprendizajes, no reproches; cifras del ledger, no de memoria.
- Solo lectura del roadmap salvo `retro.md` y `CALIBRATION.md`. El paso 4-bis sólo propone vía servicio compartido; no habilita escritura manual de memoria fuera del roadmap.
- Si no hay horas reales registradas, dilo: sin datos no hay retro útil (y recuerda que `jira-sync`/`implementer` las registran al completar tareas).
