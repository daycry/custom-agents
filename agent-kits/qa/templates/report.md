<!--
  TEMPLATE: report.md  · informe de QA que genera el agente `qa`.
  Vive en docs/roadmap/<fecha>-<slug>/testing/report.md (+ report.pdf vía skill to-pdf).
  Sustituye {{PLACEHOLDER}} con los resultados de raw/results.json y borra estos comentarios.
-->
# Informe de QA — {{Título de la iniciativa}}

| | |
|---|---|
| **Fecha** | {{YYYY-MM-DD HH:MM}} |
| **Estado global** | {{VERDE / NO-VERDE — lo decide `qa-gate.py`, no una impresión}} |
| **URL auditada** | {{http://localhost:PORT}} |
| **Plan** | [`../improvement-plan.md`](../improvement-plan.md) · [`../test-plan.md`](../test-plan.md) |

## Veredicto (qa-gate)

<!-- Pega AQUÍ la salida JSON de qa-gate.py tal cual: es la evidencia del estado global. -->
```json
{{salida de: python3 "$QAKIT/qa-gate.py" raw/results.json [--justify raw/flaky-justify.json]}}
```

{{Si hay flaky justificados: 1 línea por test con su motivo.}}

## Resumen

- **Automáticos (E2E):** {{X}}/{{Y}} pasan.
- **Manuales pendientes:** {{N}}.
- {{1 frase de veredicto}}.

## Cobertura (coverage-check)

<!-- Resultado de coverage-check.py. Si hay criterios/tareas huérfanos, el estado global NO puede ser verde. -->

- **Referencias rotas:** {{0 / lista}}
- **Tareas sin cobertura declarada (triage):** {{— / T-0X: es de UI → huérfana / T-0Y: sin UI, no aplica}}
- **Tests sin referenciar desde ninguna tarea:** {{— / lista}}

## API y accesibilidad (si el test-plan los trae)

<!-- Fuera del umbral del gate en esta iteración: se reportan aparte. Borra la sección si no aplica. -->

| Bloque | Resultado | Detalle |
|--------|-----------|---------|
| API-01 | {{pasa / falla}} | {{status obtenido vs esperado; aserción del body}} |
| A11Y-01 | {{pasa / falla}} | {{violaciones serious/critical encontradas}} |

## Resultados automáticos (E2E)

### E2E-01 — {{nombre}} — {{PASA / FALLA}}
- **Cubre tareas**: {{T-0X}}
- **Aserciones**: {{resumen: N ok / M fallidas}}
- **Capturas**:
  - ![E2E-01](screenshots/E2E-01-home.png)
- **Error** (si falla): 
  ```
  {{traza/mensaje resumido; traza completa en raw/artifacts/}}
  ```

<!-- repite un bloque por escenario -->

## Checklist manual (para una persona)

> Ejecuta estos a mano y marca el resultado. No se automatizan por diseño (visual/UX, email real, captcha, etc.).

- [ ] **M-01 — {{nombre}}**: {{qué revisar}} · *(cubre {{T-0X}})*
- [ ] **M-02 — {{nombre}}**: {{…}}

## Trazabilidad (tarea → resultado)

| Tarea | Escenarios | Resultado |
|-------|------------|-----------|
| T-0X | E2E-01, M-01 | {{pasa / falla / manual pendiente}} |

## Evidencias

- Capturas: `screenshots/`
- Resultados crudos y trazas: `raw/results.json`, `raw/artifacts/`
