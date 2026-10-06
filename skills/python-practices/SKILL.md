---
name: python-practices
description: >
  Guía de diseño y revisión Python para cancelación, concurrencia asyncio,
  límites de E/S y contratos de scripts portables. Selecciona según la versión
  Python del consumidor. Úsala cuando el usuario diga "patrones Python",
  "revisa cancelación asyncio" o "diseña concurrencia Python".
---

# Python practices

Determina versión mínima y dependencias desde pyproject, lockfile y CI. Lee
[concurrencia y scripts](references/concurrency.md) solo si la tarea toca esas
áreas. No fuerces asyncio donde un flujo síncrono es suficiente.

Implementer aplica decisiones; reviewer comprueba escenarios de cancelación y
límites; qa reproduce efectos con recursos externos controlados. TDD y cobertura
siguen en sus skills actuales. No sustituye una auditoría de seguridad ni una
actualización de dependencias.

Inspiración: especialización técnica de ECC. Guía original acotada, con fuentes
oficiales consultadas el 2026-10-06.
