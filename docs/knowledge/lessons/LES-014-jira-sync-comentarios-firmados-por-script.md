---
id: LES-014
tipo: leccion
area: jira-sync / integración de gestión
estado: aceptada (validada: revisión de dos lentes, 2026-09-03, intento 2)
fuente: 2026-09-03-roles-and-jira-flow (T-02, T-03, T-04)
---

## jira-sync

- **Los comentarios de Jira los FIRMA el agente y los REDACTA un script.** El ciclo (transición →
  comentario → worklog) es determinista: `jira-flow.py` devuelve las `ops` en orden con el
  comentario ya renderizado desde `assets/comment-<evento>.md`, con la firma
  `> 🤖 **[custom-agents · <agente>]**` en la primera línea y una etiqueta por agente
  (`ca-implementer`, `ca-reviewer`, `ca-qa`, `ca-orquestador` para el cierre) para poder filtrar
  en Jira **quién comentó qué**.
  El modelo no redacta ni compone llamadas: ejecuta.
  *Por qué importa:* antes el formato del comentario, las reglas de transición y el worklog vivían
  como prosa repetida en `implementer`, `qa` y la skill de revisión — tres copias que el modelo
  releía en cada evento. Ahora hay una tabla en `/dev-cycle` Fase 3 y una línea por agente; las 6
  plantillas pesan 1000 bytes (`wc -c`, ≈ 245 tokens) y solo se carga la del evento en curso.
  *Trampa evitada:* un comentario por paso interno (por criterio, por fichero) inunda el issue y
  multiplica llamadas — las `ops` se agrupan por tarea, y por fase con `--batch`.
  *Frontera:* el ledger (`tasks.md`) sigue siendo la fuente de verdad y la vía por la que el
  `implementer` recibe los gaps (su brief los inyecta); el comentario de Jira es el espejo para el
  equipo, nunca el canal de trabajo entre agentes.

  *Fuente*: [`2026-09-03-roles-and-jira-flow/tasks.md`](../../roadmap/2026-09-03-roles-and-jira-flow/tasks.md) ·
  [`skills/jira-sync/scripts/jira-flow.py`](../../../skills/jira-sync/scripts/jira-flow.py)
