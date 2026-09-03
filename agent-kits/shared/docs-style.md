<!--
  FRAGMENTO COMPARTIDO: guía de redacción técnica del plugin. La cargan (una línea + fallback)
  documenter, analyst, planner y architect al redactar, y la Lente A de adversarial-review SOLO
  cuando la iniciativa es de prosa. Espejo EN: docs-style.en.md (misma sustancia, no traducción
  literal — regla 8 aplicada a sí misma). Si cambias una regla aquí, cámbiala allí.
-->

# Redacción técnica — paso compartido (`docs-style`)

Ocho reglas. Cada una con la señal que la delata y un antes/después tomado de este repo. Son criterio
de revisión solo cuando son **citables** (regla + línea): lo que no viola una regla es estilo y no es gap.

| # | Regla | Señal de que se incumple |
|---|---|---|
| 1 | **Frases cortas.** Una idea por frase; ≤ ~25 palabras. Si hace falta un «que… que… y que», corta. | Frases de 3+ líneas; más de dos subordinadas. |
| 2 | **Voz activa.** Quién hace qué: «`ledger-lint` valida el ledger», no «el ledger es validado». | «se debe», «es validado por», «será generado». |
| 3 | **Un concepto por párrafo.** El párrafo empieza con la afirmación y sigue con su porqué. | Párrafos que cambian de tema a mitad; «además» que abre un asunto nuevo. |
| 4 | **Tablas para comparar, prosa para explicar.** Opciones, campos, estados → tabla. Por qué se decidió → prosa. | Una tabla de una fila; una lista de 6 viñetas con el mismo esquema (es una tabla). |
| 5 | **Ejemplos reales del código.** Rutas, comandos y salidas que existen (`agent-kits/shared/scope-check.py`, `exit 1`), no «el script de validación». | «p. ej. un módulo», «algún test», rutas inventadas o genéricas. |
| 6 | **Sin adjetivos vacíos.** Sustituye «robusto», «potente», «sencillo», «completo» por el hecho que lo prueba. | Adjetivo que, quitado, no cambia el significado. |
| 7 | **Títulos que responden preguntas.** El lector busca «¿cuándo se publica?» → título «Qué sube y qué no». | «Introducción», «Consideraciones», «Varios», «Notas». |
| 8 | **Bilingüe sin traducción literal.** El espejo EN dice lo mismo con redacción nativa; los tokens de máquina (`borrador`, `generacion:`, `- **Tipo**:`) quedan en español en ambos. | Calcos («realizar la publicación» ↔ «realize the publication»); un token de estado traducido. |

## Antes / después (del propio repo)

| Regla | Antes | Después |
|---|---|---|
| 1, 2 | «La validación del ledger debe ser realizada por el script en cada edición para que las incoherencias puedan ser detectadas antes de que el orquestador las lea.» | «`ledger-lint.py` valida el ledger en cada edición. Así el orquestador nunca lee incoherencias.» |
| 3 | Un párrafo que explica la puerta `scope-check`, luego la Lente C y luego el worklog de Jira. | Tres párrafos: puerta · lente · worklog. Cada uno abre con su afirmación. |
| 4 | Seis viñetas «Lente A: … · Lente B: … · Lente C: …» con los mismos tres atributos. | Tabla `Lente · Qué mira · Contra qué · Salida`. |
| 5 | «El agente ejecuta el script de comprobación y, si falla, lo devuelve.» | «`python3 "$SHAREDKIT/scope-check.py" docs/roadmap/<fecha>-<slug>` → exit 1 devuelve los ficheros fuera de alcance como gap Important.» |
| 6 | «Un sistema robusto y completo de hooks informativos.» | «Tres hooks (`PostToolUse`, `SubagentStop`, `SessionStart`) que informan y siempre salen con exit 0.» |
| 7 | «## Consideraciones sobre Confluence» | «## Qué sube y qué no» |
| 8 | ES: «política curada» → EN: «curated politics». | EN: «curated publish scope». Los estados `borrador/aprobada` siguen en español en el texto EN. |

## Cómo aplicarlo

- **Al redactar** (`documenter`, `analyst`, `planner`, `architect`): repasa el texto contra la tabla antes de
  cerrar; prioriza 1, 2 y 5 — son las que más cuesta corregir después.
- **Al revisar** (Lente A de `adversarial-review`, solo en iniciativas de prosa): un gap de redacción cita
  **regla + línea**; sin cita no es gap, es gusto. Grado `Minor` salvo que la regla 5 o la 8 rompan
  algo verificable (ruta inexistente, token de máquina traducido) → `Important`.
- **Fallback** si este fragmento no está (instalación parcial): frases cortas, voz activa, ejemplos reales,
  tablas para comparar. Nunca bloquea.
