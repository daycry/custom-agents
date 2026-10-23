---
plan: project-extensions
estado: completado
creado: 2026-10-06
spec: spec.md
evaluacion: evaluation.md
test-plan: test-plan.md
---

# Plan de reconocimiento e integración

Cada tarea verifica un contrato completo antes de ampliar consumidores.
La fuente canónica será project-pieces.py (lectura y resultados derivados);
la propiedad sigue el registro O1, sin otra base persistente. Las extensiones se
usan por selección explícita y disponibilidad real de la sesión, nunca por asumir
que una declaración concede permisos. La configuración del consumidor se conserva.

| Tarea | Resultado | Dependencia |
|---|---|---|
| T-01 | Contratos y arquitectura de extensiones | Primera fase publicada |
| T-02 | Descubrimiento multi-runtime acotado | T-01 |
| T-03 | Propiedad, identidad y colisiones verificables | T-02 |
| T-04 | Selección explícita compartida de extensiones | T-03 |
| T-05 | Briefs y personas de proyecto | T-04 |
| T-06 | Extensiones en panel con fuentes y conflictos | T-03/T-04 |
| T-07 | Workflow, distribución y documentos bilingües | T-05/T-06 |
| T-08 | Revisión, cobertura y QA multi-runtime | T-07 |
| T-09 | Retro, estados y changelogs | T-08 |
| T-10 | Push y comprobación remota | T-08 y entrega documental de T-09 |

El cierre documental se confirma después de contrastar el primer push: así el
ledger y los changelogs finales pueden citar una publicación observada. Se
publica después ese commit de cierre, sin PR, merge ni release. La dependencia
es de entrega técnica y documental, no de una afirmación anticipada del remoto.
