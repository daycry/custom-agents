# Actualizar un plan existente

Lee al actualizar, dividir, cancelar o reordenar tareas de un plan existente.

- **Replanificar un plan en marcha (otra sesión, hechos nuevos).** El ledger debe poder retomarse sin el historial de la conversación:
  - **IDs estables.** Una tarea conserva su `T-XX` aunque cambie de fase u orden. Lo nuevo toma el siguiente número libre; nunca se reutiliza el ID de una tarea cancelada o dividida (`ledger-lint` falla con duplicados). Al dividir, el ID original se queda con la parte que ya tiene progreso o evidencia.
  - **Razón del cambio.** Cada inserción, división, reordenación, omisión o cancelación lleva una fila en `Changelog del plan` (`improvement-plan.md`) con el motivo y su efecto en dependencias, y en la tarea afectada `**Notas**: replanificada <fecha> — <motivo>`.
  - **Dependencias revalidadas.** Revisa el campo `Dependencias` de toda tarea que apuntaba a la tocada: reescríbelo al ID nuevo o declara la dependencia rota; no dejes punteros a tareas canceladas.
  - **Tres cosas distintas, sin mezclarlas.** *Trabajo hecho*: una tarea `completado` no se reabre ni se reescribe; si el alcance cambia, va en una tarea nueva. *Cancelación autorizada*: `cancelado` solo con decisión del usuario o de una puerta, citada en `Notas`; la tarea se queda en el ledger y sigue contando en el total del resumen. *Nueva previsión*: se cambia el `est.` de las pendientes y se anota el anterior en `Notas`; el `real` no se toca.
  - **Sin borrar evidencia.** Secciones `Revisión de dos lentes`, `RED:`, salidas de `Verificación` ejecutadas y worklogs se conservan tal cual.
