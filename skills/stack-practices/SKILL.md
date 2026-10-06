---
name: stack-practices
description: >
  Criterios de implementación, revisión y pruebas para PHP/CodeIgniter 4,
  Python y React, seleccionados por manifiestos y versión mínima del proyecto.
  Úsala cuando el usuario diga "guías de stack", "patrones CodeIgniter",
  "patrones Python", "patrones React" o "revisa cancelación asyncio".
---

# Guías por stack

Usa la selección de `agent-kits/shared/capability-check.md`. Comprueba versiones
en manifiestos y lockfiles; en un monorepo ejecuta el selector en el paquete de
la tarea. Lee **solo** la referencia del stack afectado. Los stacks explícitos
sin detección se registran como declarados, no como dependencias comprobadas.

| Referencia | Cuándo leerla |
|---|---|
| [PHP y CodeIgniter](references/php-codeigniter.md) | Rutas, validación, servicios, persistencia o tests PHP |
| [Python](references/python.md) | Tipos, E/S, concurrencia, empaquetado o fixtures Python |
| [React](references/react.md) | Estado, efectos, componentes, datos o tests React |

Architect decide fronteras; planner convierte riesgos en casos; implementer
aplica el criterio; reviewer comprueba el mismo contrato; qa ejecuta escenarios.
Las guías no eligen librerías ni fuerzan migraciones por sí mismas. TDD,
api-contract, adversarial-review y unit-tests mantienen sus métodos y puertas.
No precargues las tres referencias ni cambies versiones/configuración externa
por invocar esta skill. Una guía presente no acredita haberla aplicado.
