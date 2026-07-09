<!--
  TEMPLATE: report.md  · informe de QA que genera el agente `qa`.
  Vive en docs/roadmap/<fecha>-<slug>/testing/report.md (+ report.pdf vía skill to-pdf).
  Sustituye {{PLACEHOLDER}} con los resultados de raw/results.json y borra estos comentarios.
-->
# Informe de QA — {{Título de la iniciativa}}

| | |
|---|---|
| **Fecha** | {{YYYY-MM-DD HH:MM}} |
| **Estado global** | {{VERDE (todo pasa) / ROJO (hay fallos)}} |
| **URL auditada** | {{http://localhost:PORT}} |
| **Plan** | [`../improvement-plan.md`](../improvement-plan.md) · [`../test-plan.md`](../test-plan.md) |

## Resumen

- **Automáticos (E2E):** {{X}}/{{Y}} pasan.
- **Manuales pendientes:** {{N}}.
- {{1 frase de veredicto}}.

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
