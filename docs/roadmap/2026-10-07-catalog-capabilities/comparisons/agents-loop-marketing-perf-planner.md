# Bucles, planificación, rendimiento y marketing — A038–A039, A047, A049

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cuatro definiciones completas: **30.687 bytes/880 líneas**. [agents-loop-marketing-perf-planner-reading-evidence.json](agents-loop-marketing-perf-planner-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08/T-11.

Tres de los cuatro duplican una fase o un método que ya tiene dueño y destino
integrado; el cuarto es de un dominio fuera del ciclo.

## A038 — loop-operator

`1.903 bytes/45 líneas` · tools: Read, Grep, Glob, Bash, Edit · model: sonnet.
Opera bucles autónomos: puntos de control, detección de atascos y tormentas de
reintentos, y escalado si no hay progreso en dos puntos de control, si se
repiten las trazas o si el coste se desvía.

**Comparación.** Ya integrado en `skills/plugin-dev/references/persistent-workflows.md`
(D-110), «Contrato del bucle» (l.23-35): objetivo decidible por máquina, lo que
no debe hacer, topes medidos con `usage-meter.py`, parada si no hay cambio
observable en dos iteraciones y deriva a `debug-root-cause`. Los bucles de
`/dev-cycle` están acotados a 3 (`commands/dev-cycle.md:409,413`). **Defectos:**
tiene Edit sin decir qué edita, siendo un operador que observa; «Start loop
from explicit pattern and mode» (l.26) no define ni patrón ni modo; los
chequeos obligatorios (*eval baseline*, *rollback path*, l.34-37) no dicen cómo
se comprueban; no hay tope de iteraciones ni de coste, solo escalado; y «cost
drift» no tiene medida.

**Destino:** **Sin destino**: ya integrado en `persistent-workflows.md` (D-110).

## A049 — planner

`8.055 bytes/221 líneas` · tools: Read, Grep, Glob · model: opus.
Plan de implementación por fases y pasos con fichero, dependencias, riesgo,
estrategia de pruebas y criterios de éxito, con un ejemplo completo (Stripe).

**Comparación.** El dueño es `agents/planner.md`: fases y `T-XX` con criterios y
`Verificación` obligatoria (P3, l.88), presupuesto por fase (P4), rebanadas
verticales (l.88, D-095 integrada), replanificación con IDs estables (§3
«Replanificar un plan en marcha», D-096 integrada) y `tasks.md` como ledger
canónico. Las preguntas de requisitos son de `analyst`, la revisión de
arquitectura de `architect` y las «red flags» del código (funciones largas,
anidamiento, duplicados) de `code-health`. La fuente no escribe (no tiene
Write): el plan se queda en el chat, sin ledger, sin `Verificación` y sin
estimación con método. **Defectos:** usa **el mismo `name: planner`** que el
agente propio, así que instalados juntos chocan de nombre, y su «Use
PROACTIVELY… Automatically activated for planning tasks» (l.3) compite con el
disparador propio. Además, «All tests pass with 80%+ coverage» como criterio de
éxito (l.186) es un umbral universal; en el plugin, `tests.coberturaMinima` es
opt-in. «Estimated complexity» no tiene método.

**Destino:** **Sin destino**: ya integrado en `agents/planner.md` (D-095, D-096).

## A047 — performance-optimizer

`13.454 bytes/455 líneas` · tools: Read, Write, Edit, Bash, Grep, Glob · model: sonnet.
Perfilado, bundle, algoritmos, renders de React, consultas, red y fugas de
memoria, con umbrales de Web Vitals, plantilla de informe y la orden de
optimizar.

**Comparación.** El rendimiento del diff es la Lente D (`lens-prompts.md:29`;
N+1, `await` y regex en bucle, concatenación: `lens-d-heuristics.md`). Medir el
antes y el después es `outcome-evals/references/performance-baselines.md`
(D-050 integrada) con `measured-optimization.md`. La interfaz es
`frontend-quality/references/interaction-performance.md:34-36` y
`stack-practices/references/react.md:5,66`. El código lo cambia `implementer`.
Con Write y Edit, la pieza es un **segundo implementador** fuera del ledger:
duplica una fase (ADR-011).

| Punto | Problema |
|---|---|
| FCP < 1,8 s, TTI < 3,8 s, bundle < 200 KB como objetivos (l.60-67) | Umbrales universales sin percentil, muestra ni dispositivo; `frontend-quality` no los admite (`SKILL.md:18`) y `performance-baselines.md` fija el p75 de campo por dispositivo. TTI ya no forma parte de la puntuación de Lighthouse (verificar con la doc oficial) |
| `npx lighthouse https://your-app.com` (l.38, 339-345) | Medición contra la app publicada; `performance-baselines.md:79-83` la limita a hosts locales o de prueba autorizados |
| `useCallback`/`useMemo` por defecto, incluso para un objeto literal (l.103-115, 135-138) | Contra `react.md:5,66`: memoizar solo si hay trabajo medido |
| `npx bundle-analyzer`, `npx duplicate-package-checker-analyzer` (l.34, 152) | `npx` descarga y ejecuta lo que esté publicado con ese nombre; nombres sin comprobar |
| Informe con «Overall Score X/100» y «Estimated Impact» (l.381, 422-425) | Cifras antes de medir |

**Destino:** **Sin destino**: ya integrado en la Lente D, `performance-baselines.md` (D-050) y `frontend-quality`.

## A039 — marketing-agent

`7.275 bytes/159 líneas` · tools: Read, Grep, Glob, WebSearch, WebFetch · model: sonnet.
Estratega y redactor de campañas: investigación, posicionamiento, landing,
correos, redes, guiones, anuncios, calendario y revisión de copy.

**Comparación.** Es la skill S171 (`skills-leads-logistics-research-agreements.md`)
en forma de agente, y el dominio ya se decidió **fuera del bundle**
(`skills-seo-social-graph-publisher.md`, «Decisión común»). No tiene escritura
(entrega en el chat) y sí red. Arrastra los defectos de S171: prohíbe la
urgencia falsa (l.146), pero toda secuencia termina en
«agitation → … → urgency» (l.61); fija cantidades sin relación con la campaña
(3 posts de LinkedIn, 5-6 en X más un hilo, l.67-68); y depende de
`brand-voice`, `content-engine`, `crosspost` y `market-research`, que no viajan
con él.

**Destino:** **Fuera del bundle**; persona de proyecto si un consumidor lo declara.
