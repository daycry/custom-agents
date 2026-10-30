# 1. Producto, módulos y responsabilidades

## El problema que resuelve

custom-agents organiza el trabajo asistido por IA desde una idea hasta una entrega
verificada. Separa definir el resultado, evaluar su coste, elegir el diseño, planificar,
implementar, revisar y comprobar. Las decisiones y evidencias quedan en el proyecto.
El equipo puede usar Jira, Redmine u otra herramienta para colaborar, sin convertir
esa herramienta en requisito del ciclo ni en autoridad sobre las pruebas.

Un ejemplo transversal del manual será **«Añadir aprobación de solicitudes»**.
El área solicita que un responsable pueda aprobar o rechazar una solicitud, con
registro de quién actuó y una explicación del rechazo. Producto define los criterios;
el equipo decide el diseño; la implementación se divide en permisos, API, interfaz
y pruebas. Los IDs remotos que aparecen en ejemplos son ficticios.

## Cinco conceptos que conviene distinguir

| Concepto | Qué es | Qué no demuestra |
|---|---|---|
| Comando | Entrada del usuario que coordina un workflow, como `/dev-cycle` | Que el entorno haya cargado ese comando |
| Agente | Rol con objetivo, herramientas y responsabilidad propia | Que esté autorizado a modificar otro artefacto |
| Skill | Método reutilizable activado cuando la tarea lo necesita | Que deba cargarse en todas las tareas |
| Tool o MCP | Operación que el runtime expone en la sesión | Que tenga permisos para cualquier destino |
| Persona | Criterios de dominio aplicados a una tarea | Que exista otro agente o una identidad humana real |

Los nombres cortos de los agentes se usan en la documentación. Su ID nativo puede
estar prefijado, por ejemplo `custom-agents-planner`; se consulta el mapa generado
del runtime. Invocar un nombre inexistente no se resuelve inventando un agente.

## Núcleo y módulos

El catálogo versionado está en `agent-kits/shared/modules.json`. El núcleo agrupa
las capacidades del ciclo de desarrollo y calidad. Jira, Confluence, auditoría
especializada, PDF, training, catálogo y capacidades de contenido/aplicación tienen
módulos propios. Las dependencias de módulos se resuelven de forma determinista.

| Perfil | Selección inicial | Uso orientativo |
|---|---|---|
| `core` | Núcleo | Ciclo de producto y desarrollo local |
| `developer` | Núcleo, seguridad especializada y aplicación/datos | Equipo que necesita esas especialidades |
| `research` | Núcleo, contenido y su dependencia de voz | Investigación y producción de contenido |
| `full` | Todos los módulos del bundle | Biblioteca completa bajo demanda |

Un perfil no identifica un proveedor externo. Se puede elegir `core` con el módulo
`jira`, o trabajar con `core` y un adaptador Redmine del proyecto. El catálogo del
plugin enumera lo que distribuye el propio plugin, no todos los sistemas permitidos.

La selección física depende del medio de entrega. El exportador portable filtra
skills y sus recursos; no entrega el ciclo completo de agentes/comandos/hooks. El
modo de copia de Claude admite perfiles de archivos. Los plugins nativos entregan
su bundle completo; no se edita su caché para simular una instalación parcial.
La disponibilidad real de una skill o tool se contrasta en la sesión.

## Dueños del trabajo

| Rol | Decide o produce | No sustituye a |
|---|---|---|
| Responsable/usuario | Objetivo, alcance aprobado, destino y autorizaciones | QA o herramientas de pruebas |
| `analyst` | Descubrimiento y especificación verificable | Planner o implementer |
| `evaluator` | Estimación, riesgos y evaluación | Aprobación de negocio |
| `architect` | Opciones técnicas y diseño elegido | Decisión humana cuando el flujo la pide |
| `planner` | Plan, fases, tareas y criterios | Ejecución y verificación |
| `implementer` | Código y verificaciones de implementación | Revisión independiente ni QA final |
| `reviewer` | Hallazgos de revisión con evidencia | Corrección del código revisado |
| `qa` | Ejecución de pruebas y veredicto de gate | Aprobación de negocio o cierre remoto |
| `documenter` | Documentación mantenible del producto | Publicación externa sin permiso |
| `knowledge-curator` | Juicio sobre conocimiento candidato | Aprobación automática por un productor |
| `nemesis` | Auditoría especializada, cuando está disponible y se solicita | Revisión ordinaria ni QA funcional |
| Orquestador | Orden de etapas, handoffs y cierre con todos los veredictos | Trabajo de los roles especialistas |

La skill `adversarial-review` coordina la revisión y sus lentes. El agente reviewer
emite hallazgos; la skill conserva la traza del intento y su proyección externa.
Este reparto evita que dos piezas publiquen el mismo comentario.

## Los registros de verdad

La carpeta de una iniciativa es `docs/roadmap/<fecha>-<slug>/`. `spec.md` explica
qué resultado se busca; `evaluation.md` estima y evalúa; `design.md` conserva el
diseño cuando procede; `improvement-plan.md` desarrolla el plan; `tasks.md` es el
ledger canónico de progreso. `testing/` conserva resultados y evidencias.

Una tarea completada en un tablero externo no acredita un test. Un informe verde
de QA no acredita que un comentario se publicara. Un recibo de publicación no
aprueba la especificación. Cada resultado conserva su autoridad y su evidencia.

## Integraciones por función

Los bindings de `.claude/integrations.json` declaran funciones como `task-tracking`
o `documentation`. Cada uno señala una skill o tool y las operaciones que espera.
`integration-route.py` valida y selecciona declaraciones; no ejecuta herramientas,
no conecta cuentas y no autoriza escrituras. La comprobación y ejecución pertenecen
al workflow y al adaptador elegido.

Una integración opcional puede faltar o fallar. El equipo continúa localmente y
deja pendiente la proyección externa. Los controles obligatorios del core mantienen
su exigencia: un QA rojo sigue siendo rojo aunque Jira no esté disponible.

## Criterio para ampliar el producto

Antes de añadir una pieza se comprueba si ya tiene dueño, si resuelve una necesidad
real, si aporta algo más que envolver otra herramienta, si se puede probar y quién
la mantendrá. Las particularidades de una organización pertenecen normalmente al
proyecto. Una capacidad reusable, estable y justificada puede optar al catálogo.

No se han incorporado en bloque las propuestas pendientes. Tampoco se exige que
el plugin conozca cada proveedor: un proyecto puede añadir su adaptador sin esperar
una nueva versión del core. Esta separación es modularidad con puertos y adaptadores;
no presupone que todo el producto deba modelarse mediante DDD.
