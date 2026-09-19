---
category: PATTERN
evidencia: multiple_validated_cases
fuentes:
  - docs/roadmap/2026-09-15-knowledge-services/spec.md (CA-16)
  - docs/roadmap/2026-09-15-knowledge-services/tasks.md (T-08, validación en vivo contra el bridge real)
  - skills/knowledge-services/backends/markdown_export.py (health/verify)
tags:
  - agente:knowledge-services
  - area:integracion-externa
  - riesgo:acoplamiento
---

## Un adaptador a un sistema externo opcional degrada con un estado explícito y nunca ejecuta operaciones del propio stack

- **Contexto:** `knowledge-services` publica `docs/knowledge/approved/` a un backend externo
  declarado por proyecto (Kwipu, vía el adaptador `markdown-export`), pero Kwipu **indexa una
  vista**, no ingiere: el export del plugin va a un directorio (`generated_knowledge`) y el
  reindexado real (`build_view` + reinicio de `kwipu`/`kwipu-bridge`/`kwipu-mcp`) es una operación
  del stack externo, ajena al plugin (CA-16, `docs/roadmap/2026-09-15-knowledge-services/spec.md:54`).
- **Patrón aplicado:** el contrato de 6 funciones del adaptador (`health/plan/apply/verify/rebuild/revoke`,
  `skills/knowledge-services/backends/README.md`) resuelve `health` a uno de cuatro estados
  explícitos (`off · sano · degradado · error`, nunca una excepción no controlada) y `verify`
  compara el manifiesto publicado contra `GET /graph/snapshot` del bridge real: si detecta desfase,
  **nombra** el remedio exacto («reindexar: `build_view` + reiniciar `kwipu`, `kwipu-bridge`,
  `kwipu-mcp`») en vez de ejecutarlo. La validación en vivo del orquestador contra
  `127.0.0.1:8765` (T-08, `docs/roadmap/2026-09-15-knowledge-services/tasks.md`) confirmó el ciclo
  completo (`health` → `sano`, `apply` publica, `--check` reporta el desfase con el remedio) sin
  que el plugin tocara `docker compose` ni `projects.yaml`.
- **Por qué importa:** acoplar el plugin a acciones del stack externo (reiniciar contenedores,
  activar clases de `projects.yaml`) le daría permisos y superficie de fallo que no le
  corresponden y que varían por despliegue; degradar con un estado nombrado + un remedio explícito
  mantiene el adaptador reemplazable y el fallo diagnosticable sin privilegios adicionales.
- **Cuándo aplica:** cualquier integración con un sistema externo cuya operación de
  "aplicar los cambios de verdad" (rebuild de índice, reinicio de servicio, migración) no es
  responsabilidad del plugin — el patrón es health explícito + verify que detecta y nombra, nunca
  ejecuta.
