# Verificación de memoria local y servicios opcionales

El catálogo Python/Node selecciona `memory-integrations` de forma explícita y
el perfil full lo incluye; core no entrega `knowledge-services`. El Curator,
journal y recuperación locales conservan su responsabilidad. Se retiran las
dependencias obligatorias de servicios externos de los agentes correspondientes.

El contrato común de bindings declara propósito knowledge y skill adaptadora;
el ID coincide con backend. No crea un segundo motor de curación, routing,
taxonomía ni outbox. Los ejemplos llegan desactivados y sin credenciales.
Declaración, conexión, publicación, indexación, consulta y verificación se
describen como hechos separados. Una proyección externa no adquiere autoridad.

TDD: rojo observado al comprobar que knowledge-services seguía en core. La
selección de módulos y exportación portable reales suman29pruebas verdes en la
última ejecución dirigida. El paquete core se materializa y valida con el
exportador real; Python/Node comparten selección. Las copias por perfil y sus
manifiestos conservan también las pruebas existentes de propiedad/recuperación.

W-19..W-22 ES/EN y PDF detallan memoria local, Kwipu, Graphify y Graphiti:
elección/configuración, autorización, shadow/read, fuentes, drift, outbox,
reconstrucción, revocación, fallos y retorno a memoria local. Graphify sigue
siendo contexto de código, separado de conocimiento aprobado. Los límites de
versiones/proveedores se indican; no se atribuye un despliegue real a un fixture.

Este cambio no prueba una nueva instalación de Kwipu, Graphify o Graphiti ni
ejecuta inferencia Ollama. La vista de memoria del navegador usa fuentes locales
de fixture y no llama a los servicios externos. La suite conjunta y publicación
se coordinan en [control-center](../../2026-10-31-control-center/testing/report.md).
Consumo total de tokens/coste/horas no medido; sin datos de aceptación inventados.

Publicación confirmada: [v3.0.0](https://github.com/daycry/custom-agents/releases/tag/v3.0.0), commit a3470f7, [CI41169576551](https://github.com/daycry/custom-agents/actions/runs/41169576551) success y cuatro assets verificados. No se ejecutó inferencia Ollama ni un despliegue nuevo de servicios externos.
