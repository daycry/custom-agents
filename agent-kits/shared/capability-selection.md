# Selección de capacidades por evidencia del repositorio

> Léela solo cuando haya que decidir qué capacidades usa **habitualmente** un
> proyecto, o revisar una selección que se ha quedado vieja. La selección por
> tarea sigue en `capability-check.md` (`capability-route.py` y
> `project-pieces.py`); esto la justifica a nivel de proyecto.

Clasificar no es instalar ni retirar. Ninguna fila de esta selección adopta,
instala, borra ni desactiva una pieza: eso va al dueño de cada acción.

## Seis grupos

| Grupo | Qué entra | Inventario |
|---|---|---|
| Agentes | Roles del bundle y agentes del proyecto o del usuario | Bundle + `project-pieces.py` |
| Skills | Skills del bundle y del proyecto | `capability-route.py` + `project-pieces.py` |
| Comandos | Orquestadores y comandos propios | Bundle + `project-pieces.py` |
| Reglas | Constitución (`docs/CONSTITUTION.md`) e instrucciones del runtime | Lectura de esos ficheros |
| Hooks | Hooks del bundle y del proyecto | `/doctor` y configuración del runtime |
| Extras | Personas, fuentes de tools y MCP declarados | `project-pieces.py` |

## Evidencia que cuenta

Elige por lo que el repositorio **muestra**, nunca solo por el nombre de la
pieza:

- manifiestos y lockfiles del paquete afectado (stack y versiones);
- extensiones declaradas del proyecto y del usuario;
- CI y scripts (qué se construye, se prueba y se publica);
- configuración y documentación del proyecto;
- áreas que tocan las iniciativas del roadmap.

Cada capacidad elegida lleva su evidencia (`ruta` o comando). Sin evidencia,
la elección es provisional y se dice.

## Dos inventarios

| Clase | Significa | No significa |
|---|---|---|
| Habitual | Selección corta pertinente para la mayoría de tareas del proyecto | Cargarla entera en cada sesión |
| Biblioteca bajo demanda | Disponible y accesible cuando una tarea la pida | Baja, retirada o inútil |

Habitual es una lista corta: si crece hasta incluirlo casi todo, deja de
servir para elegir. El coste de cargar lo habitual se estima con
`context-cost.md`.

## Qué no se deduce

- Disponibilidad nativa, permisos, confianza o conexión: una pieza listada o
  un MCP declarado no acredita nada de eso. Se contrasta con la sesión.
- Uso medido: clasificar como habitual no dice cuánto se usa.
- Exclusión global: que el dominio del proyecto no use una capacidad no la
  saca del catálogo del bundle ni sobrescribe extensiones del proyecto.

## Revisar la vigencia

Revisa la selección cuando ocurra cualquiera de estos hechos:

| Hecho | Comprobación |
|---|---|
| Cambia un manifiesto (stack nuevo, salto de versión mayor) | `capability-route.py` con el paquete afectado |
| Una extensión desaparece o cambia de runtime | `project-pieces.py --select <id>`; los IDs no descubiertos salen con aviso |
| Aparece una pieza nueva en el bundle o en el proyecto | Lectura de su descripción y fuente |
| Un área nueva entra en el roadmap | Áreas de la tarea en `capability-check.md` |

Una selección revisada conserva la anterior y explica qué cambió y por qué,
en el mismo sitio donde se registró.

## Plan de instalación con dueño

Si falta una capacidad que la evidencia pide, se propone; no se instala. Cada
fila nombra su dueño y una acción explícita:

| Falta | Dueño | Acción |
|---|---|---|
| El bundle o una de sus piezas en un runtime | `install/` (método de `installation-lifecycle.md`) | `--dry-run`, autorización, `install`, `status` |
| Un opt-in del proyecto | `/setup` | Relanzarlo para esa decisión |
| Una pieza nueva del plugin | skill `plugin-dev` | Spec y ciclo normal |
| Una pieza propia del proyecto | Contrato de especialización del proyecto | Propuesta; la adopción la decide el usuario |
| Una herramienta externa (CLI, navegador) | Usuario | Comando de instalación y comprobación |

Cada fila cierra con su comprobación (`/doctor`, `status` o el listado nativo
del runtime). Sin dueño claro, queda pendiente visible.

## Salida

Se entrega como contexto (lo muestra `/work-context`); no crea otro registro.
Por tarea, los IDs y su motivo se anotan en el ledger con los campos
`Capacidades` y `Extensiones` de `capability-check.md`.

| Capacidad | Grupo | Clase | Evidencia | Pendiente |
|---|---|---|---|---|
| `<id>` | Skills | Habitual | `package.json` declara React | — |

## Degradación

Sin señal suficiente, sin selector o con una instalación parcial: selección
provisional con motivos y pendientes, aviso del límite y continuidad con los
criterios disponibles. Nunca bloquea el ciclo.
