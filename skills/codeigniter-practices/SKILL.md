---
name: codeigniter-practices
description: >
  Guía específica de PHP con CodeIgniter 4: límites de Model y Query Builder,
  validación, mass assignment y fallos de transacción. Aporta contexto al
  implementer, reviewer y qa según la versión instalada. Úsala cuando el usuario
  diga "patrones de CodeIgniter 4", "revisa un modelo CodeIgniter" o
  "transacciones de CodeIgniter".
---

# CodeIgniter practices

Lee composer.json/lock para identificar PHP y CI4 reales antes de proponer APIs.
Usa [decisiones de persistencia](references/persistence.md) solo si la tarea toca
Model, Query Builder, validación o transacciones. Para APIs, conserva el contrato
del proyecto; no trasplantes convenciones de Laravel.

Implementer aplica el patrón pertinente; reviewer busca el fallo concreto; qa
prueba los efectos observables. El método TDD, la revisión y las puertas siguen
en sus piezas actuales. Esta skill no instala paquetes ni decide migraciones.

Inspiración: amplitud de especialización de ECC. Material específico original
para CodeIgniter 4, basado en documentación oficial consultada el 2026-10-06.
