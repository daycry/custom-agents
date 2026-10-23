# Arnés generador-evaluador y optimizador del arnés — A025–A027, A031

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cuatro definiciones completas: **24.138 bytes/535 líneas**. [agents-gan-harness-reading-evidence.json](agents-gan-harness-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08/T-11.

**Común a las cuatro.** Bloque «Prompt Defense Baseline» idéntico (líneas 9-16). **Sin destino.**

**Decisión previa.** La skill S111, el arnés generador-evaluador, ya se comparó en
`skills-fsharp-gan-gateguard.md:24-42`. Allí quedó **sin destino nuevo**: el plugin ya
separa producir de evaluar con contexto fresco y acota el bucle a tres intentos. Las tres
piezas A025–A027 son los agentes de esa misma skill, y aquí se comparan rol por rol, con
sus permisos. A031 es otra pieza: optimiza la configuración del arnés.

## A027 — gan-planner

`4.502 bytes/108 líneas` · tools: Read, Write, Grep, Glob · model: sonnet. Convierte un prompt
de una línea en una especificación de producto «deliberadamente ambiciosa», con 12-16
funciones, sprints, dirección de diseño y la rúbrica de evaluación (`gan-harness/spec.md` y
`eval-rubric.md`).

**Comparación.** Ocupa el sitio de `analyst`, que lleva la idea a una `spec.md` con alcance
in/out que **aprueba el usuario** (`agents/analyst.md:45`, `:59`), y de `evaluator`, que la
presupuesta antes de la puerta go/no-go. A027 amplía el alcance sin aprobación
(«push for 12-16 features», línea 26) y escribe directamente la spec que ejecutará el
generador. No hay puerta de usuario. Sus permisos son más estrechos que los de `analyst`
(sin Bash ni Edit), así que en eso no hay objeción. La sección de casos límite (estados
vacío, error, carga y responsive; línea 100) ya forma parte de `frontend-quality`.

**Destino:** **Sin destino.** Contradice la puerta de alcance del plugin.

## A026 — gan-generator

`5.891 bytes/140 líneas` · tools: Read, Write, Edit, Bash, Grep, Glob · model: sonnet.
Implementa la spec, mantiene el servidor de desarrollo, hace commit en cada iteración y
aplica **todo** el feedback del evaluador.

**Comparación.** Su rol lo cubre `implementer`, con rama, ledger y `Verificación` por tarea.
La diferencia de procedimiento importante está en las líneas 28 y 140: «los ítems del
Evaluator no son sugerencias» y «si una sugerencia parece equivocada, pruébala igual».
El plugin exige lo contrario: comprobar cada gap contra el código y la spec, y rebatirlo con
evidencia si es incorrecto (`skills/adversarial-review/SKILL.md:104-108`; racionalización
en `agents/implementer.md:132`, «El revisor lo señaló, así que lo corrijo tal cual»). Además
impone el stack («CSS-in-JS o Tailwind, nunca CSS plano», línea 89; SQLite como
persistencia, línea 96). En el plugin esa decisión es de `architect` y del proyecto.

**Destino:** **Sin destino.** La lista anti-«AI slop» de las líneas 106-124 coincide con la
dirección visual ya integrada en `frontend-quality/references/visual-system.md`.

## A025 — gan-evaluator

`8.822 bytes/232 líneas` · tools: Read, Write, Bash, Grep, Glob + 8 herramientas MCP de
Playwright · model: sonnet. Prueba la aplicación viva en el navegador, puntúa de 1 a 10
cuatro criterios ponderados (diseño, originalidad, oficio, funcionalidad; aprueba con 7,0)
y escribe el feedback.

**Comparación.** Une dos dueños del plugin. Las pruebas en navegador son de `qa`, y la
crítica del resultado son las lentes de `adversarial-review`. Diferencias:

| Aspecto | A025 | Plugin |
|---|---|---|
| Veredicto | Nota ponderada del modelo, umbral 7,0 (líneas 124-154) | `qa-gate.py` con exit code. Una nota de modelo es juicio auxiliar (`outcome-evals/references/agent-comparisons.md:57`) |
| Hosts | `browser_navigate` a cualquier URL; el puerto por defecto es solo un default (línea 57) | Guardrail local/privado antes de ejecutar nada (`agents/qa.md:44-49`) |
| Degradación | Registra el modo **conseguido** frente al pedido (líneas 38-42, 138-144) | Igual: «Playwright no está» se declara (`agents/qa.md:108`, `:127`) |
| Escritura | `Write` sin límite de ruta | `qa` escribe solo en `testing/` (`agents/qa.md:6`) |
| Tono | «Ruthlessly strict», penaliza la estética genérica | Severidad por definición, no por actitud |

El registro del modo conseguido (líneas 38-42) es la parte buena de la pieza, y el plugin
ya lo tiene.

**Destino:** **Sin destino.** Su veredicto por nota contradice la resolución de
`skills-destinations.md` («Puntuaciones del modelo como veredicto»).

## A031 — harness-optimizer

`4.923 bytes/55 líneas` · tools: Read, Grep, Glob, Bash, Edit · model: sonnet. Mejora la
configuración del arnés (hooks, evals, enrutado, contexto, seguridad) con evals pass@k/pass^k,
foto previa y restauración automática si falla la regresión.

**Comparación.** En el plugin no hay un agente para esto: cambiar una pieza del propio
plugin es una iniciativa más (`/dev-cycle` + `implementer`), con la skill `plugin-dev` como
método. Las evals las cubren `evals/check.py`, `evals/run.py` y `outcome-evals`. pass@k y
pass^k ya están definidos en `outcome-evals/references/protocol.md:62-63`, y k ≥ 3 en
`agent-comparisons.md:46-48` (D-044, integrado). Su regla «un cambio de seguridad queda
BLOCKED hasta aprobación humana» (línea 39) es buena. Defectos de la fuente:

| Línea | Dice | Problema |
|---|---|---|
| 51-55 | Ejemplo: pasa un hook `PreToolUse` lento a un `PostToolUse` asíncrono y reporta `SHIP IT` con pass@1 | Convierte una comprobación previa en un aviso posterior, es decir, debilita un control. Contradice su propia regla de BLOCKED (línea 39) y su exigencia de tres pruebas antes de reportar pass@3 |
| 39 | Grader «Model-Based (self-assessed diff quality)» | El agente califica su propio diff. El plugin separa producir de juzgar |
| 35, 39 | Foto con `git stash create` y restauración automática | `stash create` no guarda la referencia. Restaurar por ruta puede pisar cambios del usuario en esos ficheros |
| 24, 31 | `node scripts/harness-audit.js`, `node tests/run-all.js` | Scripts de su repositorio de origen: no son portables |

**Destino:** **Sin destino** como agente. El ejemplo de las líneas 51-55 justifica un
antipatrón en `plugin-dev` (propuesta P2 en el informe).
