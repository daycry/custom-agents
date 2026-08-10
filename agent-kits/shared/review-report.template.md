<!--
  PLANTILLA FIJA: comentario de revisión que se publica en Jira (jira-sync Paso 9)
  y/o se muestra al usuario. Formato IDÉNTICO siempre: el revisor emite su resultado
  ESTRUCTURADO por criterio y se renderiza contra esta plantilla.
  Sustituye los {{PLACEHOLDER}} y borra los comentarios guía.
  Modo tarea: una instancia por T-XX. Modo fase: una sola instancia por fase, con un
  bloque "### T-XX" por cada tarea de la fase.
-->
## 🔍 Revisión de la implementación — {{Fase N · título  |  T-XX · título}}

**Veredicto:** {{✅ APROBADA  |  ❌ CON GAPS}} · **Revisión superada en {{N}} intento(s)** · **Tiempo de revisión:** {{H}} h

<!-- Un bloque por tarea. En modo tarea hay uno solo; en modo fase, uno por cada T-XX de la fase. -->
### {{T-XX · título de la tarea}}

| Criterio de aceptación | Resultado |
|---|---|
| {{criterio 1}} | {{✓ / ✗}} |
| {{criterio 2}} | {{✓ / ✗}} |

{{**Gaps** (solo si los hubo, ya corregidos o pendientes): lista con fichero:línea y qué faltaba. Si el veredicto final es ✅, indica "corregidos en los N intentos". Si quedó algo aceptado como deuda, márcalo.}}

---
<!-- Pie fijo -->
> Revisión adversarial de dos lentes (conformidad con spec/plan · calidad/robustez), contexto fresco. Solo se reportan gaps de corrección o de requisitos, no preferencias de estilo. Generado por `/dev-cycle` (Modo B).
