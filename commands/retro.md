---
description: Retrospectiva de una iniciativa CERRADA — compara estimado vs real (horas, tokens, coste), captura causas de desviación y aprendizajes, y alimenta el histórico de calibración que el evaluator usa para estimar mejor las siguientes. Escribe retro.md en la carpeta de la iniciativa y una fila en docs/roadmap/CALIBRATION.md.
argument-hint: "<slug o carpeta de la iniciativa cerrada>"
---

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
2-bis. **Calcula el ratio real tokens→hora** de la iniciativa: `tokens facturables medidos ÷ horas-IA reales validadas` (facturables = entrada + creación de caché + salida; la lectura de caché no cuenta — misma convención que `usage-meter.py`). Solo si hay datos **medidos** (`fuente: medido`); si todo es estimado, deja la celda vacía en vez de calibrar con humo.
2-ter. **Journal de la iniciativa (si existe).** Si hay `docs/knowledge/journal/` con entradas cuyo `iniciativa:` sea este slug (`grep -l "^iniciativa: <slug>" docs/knowledge/journal/*.md`), léelas en orden: sus `decisiones`, `pendientes`, `tareas_cambiadas` y `ficheros_tocados` son una fuente **objetiva** de causas de desviación (sesiones cortas que no cerraron tarea, re-aperturas, ficheros fuera del plan) — úsalas para proponer causas en el paso 3, no para sustituir la respuesta del usuario. Sin journal, sigue sin él.
2-quater. **Candidatas a lección desde el journal (puerta de promoción, memory-retrieval T-14).** Localiza el kit compartido (`SHAREDKIT`, mismo comando que el paso 7) y ejecuta `python3 "$SHAREDKIT/journal.py" candidatas --root .` (añade `--iniciativa <slug>` si quieres solo las de esta iniciativa; las transversales suelen ser las buenas). El script es **determinista**: un mismo patrón de `decisiones`/`pendientes` repetido en **≥ 2 entradas de sesiones distintas** sale como candidata con `estado: propuesta` y su **evidencia** (fecha, fichero y `session_id` de cada entrada); un patrón en una sola entrada **no** se propone, y sin journal no imprime nada (exit 0). Muestra la lista al usuario tal cual. **Una candidata nunca nace `aceptada`**: aquí solo se *propone*; si el usuario la da por buena, entra en el paso 4-bis como un aprendizaje más (con su evidencia citando las entradas de journal como `Fuente`) y sigue el mismo umbral y la misma validación que el resto — no se escribe nada automáticamente. Sin python3 o sin el kit, sigue sin este paso.
3. **Pregunta al usuario las causas** (breve, 2-3 preguntas): ¿qué explicó la desviación principal? ¿qué incógnita de la spec resultó cara? ¿qué se haría distinto? Registra respuestas literales, sin adornar.
4. **Escribe `retro.md`** en la carpeta de la iniciativa: tabla est vs real con desviaciones, causas, aprendizajes, y una línea de "ajuste sugerido" (p. ej. "las tareas de integración salieron +40 %: estimarlas con margen extra").
4-bis. **Segunda salida: aprendizajes técnicos → `docs/knowledge/` (siempre activa, D3).** Localiza el kit compartido si no lo has hecho ya: `SHAREDKIT="$(find "$PWD/.claude" "$HOME/.claude" -type d -path '*agent-kits/shared' 2>/dev/null | head -1)"` (mismo comando que el paso 7; resuélvelo una vez y reutilízalo). De los aprendizajes que acabas de escribir en `retro.md` **más las candidatas del journal que el usuario haya dado por buenas en el paso 2-quater**, separa los **números** (paso 5, sin cambio) de lo **cualitativo técnico**: un aprendizaje sobre cómo falló o funcionó algo (no sobre cuánto costó). Para cada uno, aplica el umbral de `"$SHAREDKIT/knowledge-write.md"` — una **trampa concreta comprobada** (costó ≥1 ciclo de depuración o casi rompió algo) va a un fichero nuevo `docs/knowledge/gotchas/GOT-NNN-<slug>.md`; un **aprendizaje de proceso** transversal (no ligado a un fichero concreto) va a un fichero nuevo `docs/knowledge/lessons/LES-NNN-<agente>-<slug>.md`. Si un aprendizaje alimenta **las dos salidas** (un número Y una lección), usa un **enlace cruzado** entre `retro.md`/`CALIBRATION.md` y la entrada de `docs/knowledge/` — nunca dupliques el texto. Actualiza `docs/knowledge/README.md` en el mismo cambio y cierra con la marca `Estado: [actualizado|sin cambios]` (patrón `nemesis`: "sin cambios" si ningún aprendizaje de esta retro cruzó el umbral). Si `docs/knowledge/` no existe, créala en este primer registro; sin el fragmento, no bloquea: sigue sin esta segunda salida.

   **Validación del usuario (promotor 2, ver `knowledge-write.md` §Autoría).** `/retro` corre
   sobre iniciativas **ya cerradas**: el bucle de revisión de dos lentes (skill `adversarial-review`) de esa iniciativa ya pasó
   y ya promovió lo que tenía que promover, así que estas entradas nuevas nacen `propuesta` sin
   nadie más que las vaya a validar después. Si escribiste alguna entrada en este paso, ofrécele al
   usuario, en una línea, cerrar el ciclo ahora mismo: **"¿Doy por buenas estas N entradas? [Sí/luego]"**.
   Si responde que sí, promuévelas a `estado: aceptada (validada: usuario, AAAA-MM-DD)` (formato
   único de traza) en el mismo cambio. Si prefiere dejarlo para luego, quedan en `propuesta` —
   siguen siendo legibles vía `knowledge-check.md` (que las presenta como pendientes, no como
   doctrina), no es un bloqueo, solo una promoción diferida.
5. **Añade una fila** a `docs/roadmap/CALIBRATION.md` (créalo si falta; una tabla: fecha · slug · desv. producción % · desv. tokens % · **tokens/hora (medido)** · causa principal · ajuste sugerido). Este fichero es el **histórico que lee `evaluator`** al estimar, y de la columna `tokens/hora` toma `usage-meter.py` la **mediana** como ratio calibrado (precedencia sobre el default de `estimation-defaults.md`). Reglas de formato: mantén el literal `tokens/hora` en el encabezado (lo busca el parser) y escribe el ratio como **número entero sin abreviar** (`300000`, no `300k` — las abreviaturas las tolera el parser, pero el entero es inequívoco). Tras la fila, actualiza la línea-resumen bajo la tabla: `> Ratio vigente: <mediana> tokens/hora (mediana de N muestras)` — así el nº de muestras queda visible sin contar filas. **Sin regresión: esta salida no cambia** respecto a lo que ya hacía `/retro` (solo los números).
6. Cierra con el titular: desviación global y el aprendizaje nº1.
7. **Sincronizar con Confluence (opcional).** Aplica el paso compartido `"$SHAREDKIT/confluence-optin.md"` (skill `confluence-publish` con opt-in) sobre `retro.md` y `CALIBRATION.md`. Localízalo con `SHAREDKIT="$(find "$PWD/.claude" "$HOME/.claude" -type d -path '*agent-kits/shared' 2>/dev/null | head -1)"`. Fallback si no está: invoca `confluence-publish` respetando su opt-in, sin bloquear el cierre; nunca sincronices `docs/security-scan/`.

## Reglas
- **Sin culpa, con datos.** Causas y aprendizajes, no reproches; cifras del ledger, no de memoria.
- Solo lectura del roadmap salvo `retro.md` y `CALIBRATION.md`. `docs/knowledge/` (paso 4-bis) es la excepción declarada: escritura habilitada ahí, fuera del roadmap.
- Si no hay horas reales registradas, dilo: sin datos no hay retro útil (y recuerda que `jira-sync`/`implementer` las registran al completar tareas).
