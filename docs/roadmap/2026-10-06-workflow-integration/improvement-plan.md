---
plan: workflow-integration
estado: completado
creado: 2026-10-06
spec: spec.md
evaluacion: evaluation.md
design: design.md
test-plan: test-plan.md
---

# Plan de integración coherente

| Tarea | Resultado | Dependencia |
|---|---|---|
| T-01 | Decisiones trazables del catálogo y contrato del workflow | Primera entrega e inventario fijados |
| T-02 | Registro y selector común con contratos deterministas | T-01 |
| T-03 | Stack-practices completo y retirada de tres guías iniciales | T-01 |
| T-04 | Guías transversales backend, frontend y entrega | T-01 |
| T-05 | Auditoría de capacidades y evaluación de resultados | T-01 |
| T-06 | Memoria/contexto: mejoras justificadas y piloto aislado | T-01 |
| T-07 | Integrar selección en roles, pm/dev-cycle y briefs | T-02…T-06 |
| T-08 | Panel y entrada de usuario para el workflow real | T-02/T-07 |
| T-09 | Retirar sustituciones y actualizar activos/generados | T-03…T-08 |
| T-10 | Revisión independiente, cobertura y QA Windows/Linux/navegador | T-09 |
| T-11 | Documentación bilingüe, retro, estados y changelogs | T-10 |
| T-12 | Publicación de rama y comprobación remota | T-11 |

La autorización actual permite ejecutar el plan; no se pide de nuevo go para
decisiones técnicas ya delegadas. Los datos de consumo se registran sin ficción.
El cierre exige verificar las capacidades seleccionadas, sus bajas y el workflow;
no se marca cerrado por haber escrito este plan o por inventariar un catálogo.

## Continuidad acordada

Esta entrega corresponde al núcleo común de la
[integración por fases](../../INTEGRATION-ROADMAP.md). Después se priorizarán las
extensiones propias del usuario, las capacidades útiles ya existentes en el
catálogo de referencia y la medición de mejoras de memoria. No se crearán nuevos
paquetes técnicos para cubrir capacidades ausentes en dicho catálogo ni se
impondrán paquetes por stack. Las fases posteriores tienen planes y puertas
propios; no se contabilizan como completadas en este ledger.
