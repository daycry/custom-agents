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
operación, Docker o MCP. Prepara artefactos/configuración y una comprobación
local reproducible antes de ejecutar cambios externos. Usa la autorización
vigente del usuario; preparar una entrega no autoriza publicarla o conectarla.

qa verifica resultados; nemesis conserva auditoría de seguridad. Los hooks
siguen sin red. Esta guía no instala servicios globales, no decide una release
ni sustituye el pipeline del proyecto. Usa herramientas disponibles y versiones
reales; una declaración MCP no demuestra conexión, salud ni permisos.

| Referencia | Cuándo leerla |
|---|---|
| [Entrega y herramientas](references/delivery-tools.md) | Contenedores, despliegue o servidores MCP |
