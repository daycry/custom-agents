---
name: frontend-quality
description: >
  Criterios de UI para teclado, foco, formularios, estados remotos y rendimiento
  medido, compartidos por architect, implementer, reviewer y qa.
  Úsala cuando el usuario diga "calidad frontend", "revisa accesibilidad",
  "mejora rendimiento de la UI" o "prueba navegación con teclado".
---

# Calidad observable del frontend

Identifica usuarios, flujos y dispositivos de la tarea. Lee
[interacción y rendimiento](references/interaction-performance.md) **solo**
cuando haya UI afectada; fija escenarios en test-plan antes de validar.

qa conserva E2E y qa-gate; implementer conserva componentes/tests. Un scanner
sin incidencias no acredita teclado, foco ni legibilidad visual. No impongas
umbrales universales ni añadas dependencias de UI solo por invocar esta skill.
En React, combina con stack-practices para estado/efectos, sin repetir ese método.

| Referencia | Cuándo leerla |
|---|---|
| [Interacción y rendimiento](references/interaction-performance.md) | Diseño, implementación o QA de interfaces |
