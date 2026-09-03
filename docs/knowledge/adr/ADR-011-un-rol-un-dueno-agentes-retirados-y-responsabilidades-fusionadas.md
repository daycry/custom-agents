---
id: ADR-011
titulo: Un rol, un dueño — agentes retirados y responsabilidades fusionadas
estado: aceptada (validada: revisión de dos lentes, 2026-09-03, intento 2)
fecha: 2026-09-03
iniciativa: 2026-09-03-roles-and-jira-flow
---

# ADR-011: Un rol, un dueño — agentes retirados y responsabilidades fusionadas

## Contexto

`docs/agents/ROLES.md` (T-01 de esta iniciativa) mapea los 9 agentes + 3 orquestadores contra sus
responsabilidades (quién DECIDE, quién ESCRIBE, quién solo LEE) y encuentra cuatro solapes reales:

1. **`pdfy` vs skill `to-pdf`.** El agente `pdfy` no añadía ningún paso que la skill no hiciera ya
   por su cuenta: su "onboarding" (qué convertir, dónde guardar, qué tema), su flujo (preparar
   motor → convertir → verificar) y su DoD eran una paráfrasis del propio `SKILL.md` de `to-pdf`,
   que ya se auto-invoca por `description` ("convertir a PDF", "pasar a PDF"…) y ya lo usan
   directamente `qa` y `/roadmap-brief`. Dos piezas resolviendo el mismo disparador con el mismo
   resultado son dos sitios donde arreglar un bug o afinar una frase.
2. **`analyst` (agente) vs `discovery` (skill).** Ambos convierten una idea vaga en la MISMA
   `spec.md` con la MISMA plantilla, la MISMA lista de dimensiones (objetivo, alcance in/out,
   criterios, restricciones, datos, supuestos) y el MISMO handoff a `evaluator`. `analyst` ya
   declaraba `discovery` como su "checklist de dimensiones" (dependencia interna) y su propia
   `description` prometía activarse "cuando `/pm-cycle` reciba un objetivo poco definido" — pero
   `commands/pm-cycle.md` Fase 0 punto 3 invocaba la skill `discovery` DIRECTAMENTE, sin pasar por
   `analyst`. `discovery`, además, no la usaba ningún otro agente: no cumplía el criterio de
   "compartida por 2+" de la regla 3 de `docs/CONVENTIONS.md` — era contenido privado de `analyst`
   con rango de skill top-level.
3. **`qa` vs una futura skill de tests unitarios.** Ya resuelto en la práctica (skill `unit-tests`,
   iniciativa `superiority`): E2E es de `qa`; unitarios/integración son la skill compartida
   `unit-tests` que usan `implementer` (P5, gate opcional) y `qa` (cita el dato en el informe), sin
   agente "tester" nuevo. Faltaba dejarlo **escrito** en un mapa de roles para que nadie lo
   reinvente como agente.
4. **`reviewer` vs skill `adversarial-review`.** Ya resuelto en el diseño (la skill es el MÉTODO —
   qué lentes aplican, cómo se funden y gradúan los gaps —, el agente es el EJECUTOR de UNA lente,
   solo lectura por construcción), pero tampoco estaba en un mapa explícito.

## Decisión

**Un rol, un dueño**: para cada responsabilidad del ciclo hay EXACTAMENTE una pieza que decide y
escribe su artefacto; el resto, si la toca, solo la lee. Cuando dos piezas reclaman el MISMO
disparador y el MISMO resultado, se fusionan por **absorción**: la pieza con más forma de "rol"
(persona, puerta de aprobación, DoD propio — encaja mejor como **agente** según el árbol de
decisión de `skills/plugin-dev/SKILL.md` Paso 0) absorbe los disparadores de la otra en su
`description` y la otra se **retira**. Cuando el solape es en realidad una relación
método↔ejecutor o E2E↔unitarios, no se fusiona nada: se **documenta explícitamente** en
`docs/agents/ROLES.md` para que quede escrito lo que hoy solo se entendía leyendo el código.

Aplicado a los cuatro casos:

1. **`pdfy` se retira como agente.** `agents/pdfy.md`, `docs/agents/pdfy.md` y
   `evals/cases/agent-pdfy.json` desaparecen; la conversión a PDF la hace la skill `to-pdf`
   (auto-invocada por su propia `description`) para cualquier agente que la necesite (`qa`,
   `/roadmap-brief`). Badge de agentes 10 → 9; manifiestos (`plugin.json`/`marketplace.json`) y
   badge de skills sin cambio por este punto (la skill ya existía).
2. **`discovery` se retira como skill top-level y se funde dentro de `analyst`.** El checklist de
   8 dimensiones pasa a vivir literal en el cuerpo de `agents/analyst.md` (ya no como una
   dependencia externa); la `description` de `analyst` absorbe los disparadores literales de
   `discovery` ("afinar la idea", "discovery", "define bien esto antes de presupuestar", "prepara
   la spec"); `commands/pm-cycle.md` Fase 0 punto 3 pasa a ofrecer el agente `analyst` (no la skill
   retirada) cuando el objetivo llega poco definido — cierra la promesa que la propia
   `description` de `analyst` ya hacía y que la orquestación real no cumplía. Badge de skills
   18 → 17.
3. **`qa`/`unit-tests`**: fila explícita en `docs/agents/ROLES.md` — "E2E, agente `qa`" y
   "unit/integración, skill compartida `unit-tests`, sin agente propio" — para que una futura
   iniciativa no reabra la pregunta.
4. **`reviewer`/`adversarial-review`**: fila explícita con la relación método (skill) / ejecutor de
   una lente (agente), solo lectura por construcción.

**Guardarraíl mecánico (heurístico).** `scripts/lint_plugin.py` gana un aviso — `lint_duplicate_triggers` —
que compara los disparadores literales entrecomillados de las `description` de agentes/skills/comandos y
avisa si DOS piezas distintas declaran el MISMO literal exacto (normalizado en minúsculas y espacios). No
sustituye el criterio humano (los cuatro solapes de este ADR usaban frases DISTINTAS pero semánticamente
iguales, que un match literal no habría cazado), pero atrapa la colisión más barata: copiar-pegar un
disparador de una pieza a otra sin darse cuenta.

## Alternativas descartadas

- **Mantener `pdfy` como "envoltorio documentado"** (con una nota de qué aporta) — se descartó
  porque, tras revisar su cuerpo entero, no aporta NADA que la skill no haga ya sola: mismo
  onboarding, mismo flujo, mismo DoD, mismo disparador. Un envoltorio sin valor añadido es un
  sitio más donde arreglar el mismo bug dos veces, no una capa de orquestación real.
- **Mantener `discovery` como skill independiente, invocada directamente por `/pm-cycle`** (el
  status quo) — se descartó porque deja DOS puertas de entrada al mismo resultado (`analyst` y
  `discovery`) con la orquestación real usando solo una, y porque `discovery` no cumplía el
  criterio de "compartida por 2+ agentes" que justifica que algo viva en `skills/` (regla 3 de
  CONVENTIONS) — era contenido privado de un único agente disfrazado de skill top-level.
- **Fusionar al revés: `analyst` desaparece y `discovery` se convierte en el agente único** — se
  descartó porque el trabajo de `analyst` es una conversación multi-turno con selección de
  TÉCNICA según el caso (entrevista dirigida / ejemplos / user stories / contraejemplos), puerta
  de aprobación explícita y DoD propio: encaja en el molde "agente" del árbol de decisión de
  `plugin-dev` mejor que en el de "capacidad reutilizable corta". Además ya tenía toda esa
  maquinaria escrita; reescribirla como skill habría sido puro churn sin beneficio.
- **No tocar nada y limitarse a documentar el solape en prosa** — se descartó porque una promesa de
  activación que la orquestación real no cumple (punto 2) es un defecto de comportamiento, no solo
  de claridad; documentarlo sin arreglarlo habría dejado el bug.

## Consecuencias

Agentes: 10 → 9 (`analyst`, `architect`, `documenter`, `evaluator`, `implementer`, `nemesis`,
`planner`, `qa`, `reviewer`). Skills compartidas: 18 → 17. Toda referencia a `pdfy`/`discovery`
en docs, manifiestos y badges se actualiza en el mismo cambio (T-01); `evals/cases/agent-pdfy.json`
y `evals/cases/skill-discovery.json` se retiran y sus disparadores positivos se re-comprueban desde
`evals/cases/agent-analyst.json` (que ahora cubre también los de `discovery`). El único coste real
es de migración (referencias, manifiestos, evals); ningún flujo pierde capacidad — `analyst` cubre
el 100% de lo que hacían las dos piezas por separado, y `to-pdf` sigue disponible exactamente igual
para quien la necesite. Queda condicionado a que el detector heurístico de `lint_plugin.py` es
literal (no semántico): los solapes semánticos futuros los sigue cazando la revisión humana, no el
linter.

## Estado

`propuesta` — a validar por la revisión de dos lentes o el usuario en la puerta. Pasa a `aceptada`
cuando se valida; a `obsoleta` si una decisión posterior la reemplaza (enlaza aquí a la que la
sustituye, nunca se borra el rastro).
