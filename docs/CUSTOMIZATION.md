# Manual de uso y personalización de custom-agents

[English](en/CUSTOMIZATION.md) · **Español**

Este manual acompaña la arquitectura modular de la próxima versión. Está dirigido
a responsables de área, producto, equipos técnicos y administradores de herramientas.
Describe el producto implementado y los puntos donde hace falta configurar un
adaptador del proyecto. Una receta de integración no equivale a una conexión ya probada.

## Recorrido de lectura

| Capítulo | Para qué sirve | Destinatario principal |
|---|---|---|
| [Producto y decisiones](guides/product.md) | Entender el núcleo, módulos y responsabilidades | Responsables de área |
| [Workflows del core](guides/core-workflows.md) | Seguir cada paso, comando, agente, skill y gate | Producto y equipos |
| [Atlassian](guides/atlassian.md) | Jira/Confluence: tareas, fases, comentarios, estados y documentos | Responsables y administradores |
| [Redmine y wiki](guides/redmine.md) | Añadir un proveedor de proyecto sin modificar el plugin | Equipos y administradores |
| [Personalización](guides/customization.md) | Personas, agentes, skills, comandos, tools, MCP y perfiles | Equipos técnicos |
| [Operación y adopción](guides/operations.md) | Permisos, incidencias, migración y puesta en marcha | Todos los responsables |

El PDF de entrega reúne estos capítulos, los ejemplos de configuración y los
workflows. Markdown es la fuente mantenible; el PDF es una edición para distribuir.
Los comandos de desarrollo y configuración se ejecutan desde la raíz del proyecto.
Cuando aparece `$SHAREDKIT`, significa el directorio shared del bundle instalado,
localizado según las instrucciones del runtime; no es una ruta fija del usuario.

## Qué se puede esperar

- Un ciclo local completo, con documentos, responsabilidades y pruebas trazables.
- Integraciones elegidas por proyecto, con destino y permisos comprobados.
- Módulos opcionales y extensiones propias sin editar la caché compartida del plugin.
- Fallos externos comunicados sin convertir un trabajo local válido en una entrega remota ficticia.

El plugin no crea cuentas, equipos humanos ni permisos de organización por instalarse.
Tampoco instala cualquier herramienta encontrada en una configuración. Esas acciones
pertenecen al administrador y al runtime, con autorización y comprobaciones específicas.

## Cómo invocar los workflows según el entorno

El manual abrevia los comandos. Con el plugin nativo de Claude Code se usa
`/custom-agents:setup`, `/custom-agents:dev-cycle`, etc. En Codex se invocan las
skills adaptadoras generadas, por ejemplo `$custom-agents:custom-agents-setup`,
explícitamente o desde `/skills`. OpenCode usa la forma corta `/setup`. Una copia
Claude no tiene namespace de plugin. Confirma la pieza realmente disponible antes
de seguir el workflow; los IDs de agentes siguen también el mapa de su runtime.
