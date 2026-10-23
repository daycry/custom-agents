---
name: backend-practices
description: >
  Diseño y revisión de límites backend: APIs, errores, autorización por recurso,
  idempotencia, consultas y migraciones compatibles durante despliegues.
  Úsala cuando el usuario diga "criterios backend", "diseña la API",
  "revisa una migración" o "evita escrituras duplicadas".
---

# Contratos backend y datos

Identifica contrato existente, clientes, unidad transaccional y orden de
despliegue. Lee [contratos y datos](references/contracts-data.md) **solo** al
diseñar o cambiar estos límites; convierte los riesgos pertinentes en casos
del ledger y comparte esos casos con reviewer y qa.

api-contract es dueño de OpenAPI y su gate; esta guía aporta criterios de
dominio. No impone envoltorios JSON, versionado de URL, porcentajes de cobertura
ni un ORM. Una consulta con parámetros no garantiza autorización por recurso.
Las credenciales y los detalles internos de errores no van a las respuestas.

| Referencia | Cuándo leerla |
|---|---|
| [Contratos y datos](references/contracts-data.md) | Cambios API, persistencia, retries, webhooks, subidas, cuotas, caché, cerrojos o migraciones |
| [Diseño de contratos HTTP](references/http-contract-design.md) | Solo al decidir métodos, estados, forma de respuesta, paginación, cuotas, versión o retirada visibles para el consumidor |
| [Límites de servicio](references/service-boundaries.md) | Solo al repartir un cambio entre transporte, servicio y repositorio, o al revisar código que cruza esas capas |
| [Caché y trabajos](references/cache-jobs.md) | Solo al construir una caché de resultados calculados o un worker en segundo plano |
| [Rendimiento de pipelines](references/pipeline-throughput.md) | Solo al acelerar o reestructurar una ingestión, exportación, ETL o backfill |
| [Migraciones de base de datos](references/database-migrations.md) | Solo al escribir o revisar DDL o un backfill sobre una base con tráfico (bloqueos por motor, estado a medias, runner) |
| [Regresiones por rama condicional](references/conditional-path-regressions.md) | Solo cuando el cambio depende de un flag, el entorno o el proveedor, o un verde no evitó un fallo por una rama no recorrida |
