---
id: ADR-003
titulo: El ledger sincroniza con Confluence al cerrar cada fase, no por tarea ni solo al final
estado: aceptada
fecha: 2026-08-20
iniciativa: confluence-policy
---

# ADR-003: El ledger sincroniza con Confluence al cerrar cada fase, no por tarea ni solo al final

## Contexto

`implementer` es de los pocos disparadores de la cadena que **no** aplicaba el paso opt-in de
Confluence, pese a escribir en `tasks.md` (el ledger canónico) en cada tarea. Había que decidir
con qué frecuencia disparar la publicación: por tarea (ruido alto, decenas de publicaciones por
iniciativa), solo al final (el resto del espejo queda congelado durante toda la implementación) o
en un punto intermedio.

## Decisión

`implementer` aplica el paso opt-in de Confluence **al cerrar cada fase** (no tarea a tarea, no
solo al final).

## Alternativas descartadas

- **Publicar en cada tarea** — demasiado ruido: una iniciativa de 16 tareas dispararía 16
  publicaciones.
- **Publicar solo al final del plan** — el resto del espejo (p. ej. `dashboard.md`) queda
  congelado durante toda la ejecución, que puede ser larga.

## Consecuencias

Punto medio entre ruido y congelación: una publicación por fase. **Interacción con ADR-001
(D1↔D3, documentada explícitamente en la spec fuente):** D1 deja `tasks.md` fuera del espejo por
defecto y D3 hace que `implementer` dispare al cerrar fase — no son contradictorios porque D1
manda sobre el **contenido** (qué páginas existen) y D3 sobre el **momento** (cuándo se refresca
el espejo). Efecto real: al cerrar fase, el ledger en sí **no** sube; lo que se refresca es el
resto de lo que haya cambiado dentro del alcance (típicamente `dashboard.md`, y `spec.md`/
`evaluation.md` si se tocaron). Esto se documenta para que nadie espere ver el ledger en
Confluence sin haberlo añadido antes al `include` a mano.

## Estado

`aceptada (validada: revisión de dos lentes, 2026-08-20, intento 3)` — implementada y mergeada en
`feature/confluence-policy` → `master`. Fuente:
[`docs/roadmap/2026-08-20-confluence-policy/spec.md`](../../roadmap/2026-08-20-confluence-policy/spec.md#decisiones-de-diseño)
(fila "Ledger (`tasks.md`) durante la implementación", D3, la nota "Interacción D1 ↔ D3" bajo la
tabla, y "Decisiones confirmadas" punto 3).
