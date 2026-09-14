# agent-kits/planner — toolkit privado del agente `planner`

Plantillas para generar planes. Uso interno del agente `planner`.

- `templates/improvement-plan.md` — plantilla del plan (resumen, presupuesto tiempo/coste/tokens, impacto, riesgos, criterios).
- `templates/tasks.md` — plantilla del checklist de fases y tareas detalladas. Su comentario guía del campo `Archivos` lleva las **aristas E2 y E3** de [`docs/agents/CONTRACTS.md`](../../docs/agents/CONTRACTS.md): el patrón `interop/**` cuando la tarea toca `commands/`, `agents/` o `hooks/`, y las piezas que **describen** lo tocado, copiadas de la columna «Piezas que describen» de esa matriz.

Los planes generados se guardan en `docs/roadmap/<fecha>-<slug>/` del proyecto, **no** aquí.

**Documentación completa:** [`docs/agents/planner.md`](../../docs/agents/planner.md)
**Convención del repo:** [`docs/CONVENTIONS.md`](../../docs/CONVENTIONS.md)
