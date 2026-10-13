# Producto, revisión visual de planes, flujo de proyecto y prompts — S205, S212, S213, S216, S217

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cinco cuerpos completos: **35.707 bytes/932 líneas**, sin recursos locales.
[product-canvas-flow-prompts-reading-evidence.json](product-canvas-flow-prompts-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08.

## S205 — Lienzo de revisión de planes en el navegador

`8.676 bytes/198 líneas`. Abre un plan o un HTML local en un servidor de
loopback. La persona anota elementos, chatea y emite «aprobar» o «pedir cambios».
El agente espera con `await`, que devuelve JSON.

**Comparación.** La función ya se contrastó en
[panel-plan-review.md](panel-plan-review.md) y su destino está fijado para
T-08/T-11/T-13. `agent-kits/shared/plan-review.py` ya guarda recibos locales con
hash. El cuerpo leído confirma tres límites de esa ficha y añade dos:

| La pieza | Decisión propia |
|---|---|
| Sesiones identificadas por la ruta del artefacto, «sin IDs que seguir» | La decisión se liga al SHA-256 revisado (ya fijado) |
| `approve` significa «plan CONFIRMADO: empieza a implementar» | El recibo no concede permisos; solo sustituye una confirmación que el workflow ya exigía |
| El hook `stop:plan-canvas-pending` impide terminar el turno mientras haya feedback | Un bloqueo en un hook global contradice ADR-007; el pendiente se informa, no se impone |
| Mermaid se carga desde una CDN fijada | La vista no carga recursos externos; el bloque se muestra como fuente, que es lo que la propia pieza hace sin red |
| Puerto fijo `127.0.0.1:4517` y estado común en `~/.claude/plan-canvas/` | Puerto y estado por proyecto, con Host/Origin comprobados |

**Destino:** el de `panel-plan-review.md`, con estas dos restricciones
añadidas: sin hook que bloquee y sin recursos de CDN.

## S212 — Capacidad de producto (PRD → SRS)

`4.436 bytes/142 líneas`. Convierte una intención de producto en restricciones
de ingeniería: invariantes, fronteras de confianza, propiedad de los datos,
transiciones de ciclo de vida y preguntas abiertas antes de implementar.

**Comparación.** El dueño de la spec es `analyst`, que usa la plantilla
`agent-kits/evaluator/templates/spec.md`. Las restricciones de diseño son de
`architect`, en la sección 1 de `agent-kits/architect/templates/design.md`. Las
ocho dimensiones del analyst cubren alcance in/out, restricciones e incógnitas.
La pieza aporta una distinción que el plugin no pide: separar **política fija**,
**preferencia de arquitectura** y **decisión abierta**. También cita
invariantes, propiedad de datos y transiciones de estado cuando la iniciativa
cruza servicios. La plantilla de spec no tiene un lugar para ellos.

Defectos: remite a `docs/examples/product-capability-template.md`, que no viaja
con la skill, y deriva a seis «carriles» por nombre.

**Destino:** en `agents/analyst.md`, dimensión 6 (Restricciones), marcar cada
restricción como política fija, preferencia o abierta. En la sección 1 de
`design.md`, una línea para invariantes, propiedad de los datos y estados con
transiciones cuando el cambio cruza servicios.

## S213 — Lente de producto

`3.373 bytes/93 líneas`. Cuatro modos: diagnóstico de siete preguntas con
`PRODUCT-BRIEF.md` y go/no-go, revisión «de fundador» con puntuación de encaje
producto-mercado, auditoría del recorrido de un usuario nuevo y priorización ICE.

**Comparación.** El diagnóstico coincide con las dimensiones 1, 2, 4 y 5 del
`analyst`: por qué ahora, para quién, fuera de alcance y cómo se sabrá que
funciona. El go/no-go con coste es la puerta de `/pm-cycle` sobre la evaluación,
y la priorización entre iniciativas es `/pm-backlog`, con € y horas de cada
`evaluation.md`.

| La pieza | Problema |
|---|---|
| ICE = impacto × confianza ÷ esfuerzo, cada uno de 1 a 5 | ICE multiplica impacto, confianza y facilidad; dividir por esfuerzo es otra fórmula con el mismo nombre. Además, la nota la pone el modelo |
| Encaje producto-mercado de 0 a 10 a partir del README, CLAUDE.md y los commits | «Señales de ingresos» como la presencia de código de Stripe no miden encaje; es una puntuación del modelo, no un veredicto |
| Comparar el onboarding con el de la competencia | Exige fuentes externas que la pieza no fija |

**Sin destino.**

## S216 — Operación del flujo entre GitHub y Linear

`3.145 bytes/112 líneas`. Triaje de issues y PR, con cuatro clases (fusionar,
reconstruir dentro, cerrar, aparcar), y criterio para crear en Linear solo el
trabajo activo, delegado o planificado.

**Comparación.** El plugin no usa Linear. Su gestor opt-in es Jira, con
`jira-sync` como dueño. La operación de GitHub ya se trató en S115
([skills-git-github-workspace.md](skills-git-github-workspace.md)), con destino
`delivery-practices` y una nota en `CONTRIBUTING.md`. La pieza añade dos reglas
para esa nota:

- Nunca fusionar por el título, el resumen o la confianza: leer el diff completo.
  CI en rojo no es «listo para fusionar».
- Una aportación externa valiosa que no es autocontenida se **reconstruye
  dentro**, no se fusiona tal cual. Es lo que hace esta misma iniciativa con el
  catálogo comparado.

**Destino:** esas dos reglas y la clasificación en cuatro estados, en la nota de
`CONTRIBUTING.md` propuesta en S115. Lo de Linear queda sin destino.

## S217 — Optimizador de prompts

`16.077 bytes/387 líneas`. Analiza un borrador de prompt, detecta intención,
alcance y contexto que falta, lo empareja con comandos, skills y agentes del
otro catálogo y devuelve un prompt optimizado. No ejecuta la tarea.

**Comparación.** El índice de piezas al arrancar (`skill-index.py`) ya sirve
para que se dispare la skill correcta. `/work-context` selecciona guías por rol,
stack y área. La detección de contexto que falta es el trabajo del `analyst`, y
el filtro de tamaño es el de `quick-implement`.

| La pieza | Problema |
|---|---|
| Tabla de modelo por alcance («Sonnet 5», «Opus 5») | Aquí el modelo se resuelve por agente con `model-tier.py` y `dev.json` (ADR-009) |
| Catálogo de componentes por stack escrito a mano | Sus propias «piezas relacionadas» piden usar el inventario instalado en vez de un catálogo fijo |
| El ejemplo 2 usa `/go-review` | No figura en su tabla de componentes |
| «Advisory only»: no ejecutar comandos | La fase 0 detecta el stack leyendo ficheros del proyecto; leer es compatible, pero la regla debería decir «sin efectos», no «sin comandos» |

**Sin destino.**
