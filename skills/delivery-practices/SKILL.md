---
name: delivery-practices
description: >
  Preparación verificable de entrega: contenedores, configuración, readiness,
  migraciones, recuperación e integración MCP con límites de permisos.
  Úsala cuando el usuario diga "preparar entrega", "revisa Docker",
  "planifica el despliegue" o "integra un servidor MCP".
---

# Preparar una entrega verificable

Lee [entrega y herramientas](references/delivery-tools.md) **solo** al tocar
operación, Docker, CI, MCP o un efecto fuera del repo. Prepara artefactos/configuración y una comprobación
local reproducible antes de ejecutar cambios externos. Usa la autorización
vigente del usuario; preparar una entrega no autoriza publicarla o conectarla.

qa verifica resultados; nemesis conserva auditoría de seguridad. Los hooks
siguen sin red. Esta guía no instala servicios globales, no decide una release
ni sustituye el pipeline del proyecto. Usa herramientas disponibles y versiones
reales; una declaración MCP no demuestra conexión, salud ni permisos.

| Referencia | Cuándo leerla |
|---|---|
| [Entrega y herramientas](references/delivery-tools.md) | Contenedores, despliegue, CI, arnés aislado, servidores MCP, contenido externo o efectos externos (envío, publicación, transición) |
| [CI, artefacto, rollout y recuperación](references/rollout-recovery.md) | Solo al elegir estrategia de rollout, condición de parada o vuelta atrás, o al preparar el job que construye y publica el artefacto |
| [Observación tras desplegar](references/post-deploy-observation.md) | Solo al comprobar o vigilar un entorno propio tras un despliegue o un paso de rollout, o al comparar dos entornos |
| [Conectores del repositorio](references/repository-connectors.md) | Solo al añadir o ampliar un conector con un servicio externo (cliente, SDK, webhooks o polling) |
| [Entrega asistida por agentes](references/agent-assisted-delivery.md) | Solo al repartir trabajo entre agentes y personas, fijar qué evidencia pedir antes de delegar o decidir si escalar el modelo tras un fallo |
