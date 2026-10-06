---
name: react-practices
description: >
  Guía específica de React para estado derivado, efectos, peticiones y fronteras
  de componentes; evita sincronizaciones redundantes y respuestas obsoletas.
  Úsala cuando el usuario diga "patrones React", "revisa efectos React" o
  "arquitectura de estado React".
---

# React practices

Determina React, framework y gestor de datos desde package.json/lockfile. Lee
[estado y efectos](references/state-effects.md) solo al tocar esos contratos.
Respeta las fronteras servidor/cliente del framework existente; no impongas
otro framework, librería de estado o fetching por aplicar esta guía.

Implementer diseña el cambio; reviewer verifica transiciones y respuestas
obsoletas; qa prueba interacciones visibles. Accesibilidad, TDD y E2E siguen
dentro de los roles y puertas actuales. No sustituye una revisión visual de UI.

Inspiración: especialización frontend de ECC. Guía original acotada, con fuente
oficial consultada el 2026-10-06.
