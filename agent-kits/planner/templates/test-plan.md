<!--
  TEMPLATE: test-plan.md  · plan de pruebas de la iniciativa.
  Lo genera `planner` (a partir de los criterios de aceptación) cuando el plan implica UI.
  Lo ejecuta el agente `qa`: corre los E2E-xx con Playwright y guía los M-xx (manuales).
  Vive junto al resto en docs/roadmap/<fecha>-<slug>/. Sustituye {{PLACEHOLDER}} y borra estos comentarios.
-->
# Plan de pruebas — {{Título de la iniciativa}}

| | |
|---|---|
| **Estado** | borrador |
| **Plan** | [`improvement-plan.md`](improvement-plan.md) |
| **URL local** | {{https://<proyecto>.test | http://localhost:PORT}} |

## Automáticos (E2E — los ejecuta `qa` con Playwright)

<!-- Un bloque por escenario. Son FLUJOS (pueden cruzar varias tareas). -->

### E2E-01 — {{nombre del flujo}}
- **Objetivo**: {{qué comportamiento valida}}
- **Precondiciones**: {{app levantada en la URL local; datos/seed necesarios}}
- **Pasos**:
  1. {{acción del usuario}}
  2. {{…}}
- **Aserciones**:
  - [ ] {{resultado observable esperado}}
- **Capturas esperadas**: {{momentos clave: p. ej. formulario relleno, mensaje de éxito}}
- **Cubre tareas**: {{T-0X, T-0X}}

## Manuales (M — los realiza una persona)

<!-- Lo que NO conviene automatizar: juicio visual/UX, email real, captcha, pagos, accesibilidad, multidispositivo. -->

### M-01 — {{nombre}}
- **Qué revisar**: {{…}}
- **Por qué no se automatiza**: {{motivo}}
- **Criterio de aceptación**:
  - [ ] {{…}}
- **Cubre tareas**: {{T-0X}}

## Cobertura (tarea → escenarios)

| Tarea | Cubierta por |
|-------|--------------|
| T-0X | E2E-01, M-01 |
| T-0X | E2E-02 |
