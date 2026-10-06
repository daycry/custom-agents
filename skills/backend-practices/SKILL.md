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
| [Contratos y datos](references/contracts-data.md) | Cambios API, persistencia, retries o migraciones |
