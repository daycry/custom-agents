# Coste de contexto de las piezas

> Léela solo cuando haya que estimar cuánto contexto añade cargar o activar
> piezas (skills, agentes, referencias, instrucciones, MCP) — p. ej. antes de
> añadir guías a la selección habitual. El coste **facturado** de una sesión o
> de un artefacto no se estima aquí: lo mide `usage-meter.py`.

Un informe de coste de contexto separa lo medido de lo estimado y declara lo
que no sabe. No sustituye a `usage-meter.py` ni a la calibración de `/retro`.

## Unidades

| Unidad | Cómo se obtiene | Qué acredita |
|---|---|---|
| Bytes y líneas | Medidos sobre el fichero | Tamaño en disco; no que se cargue |
| Tokens estimados | Heurística declarada (p. ej. caracteres / 4) | Orden de magnitud; se marca `estimado` y se nombra el método |
| Observación nativa | Herramienta del runtime, si existe | Lo que ese runtime dice que carga, en esa sesión y versión |
| Tokens facturados | `usage-meter.py` sobre las transcripciones | Consumo real de una ventana de trabajo |

Sin observación compatible, el consumo y el margen libre son `null`, no cero.

## Modo de carga

El coste depende de **cuándo** entra cada pieza, no solo de su tamaño. En
Claude Code, según su documentación oficial:

| Pieza | Cuándo entra en el contexto |
|---|---|
| Descripción de una skill | En el listado de skills, en cada turno, la use o no |
| Cuerpo de `SKILL.md` | Al invocarla; se queda en los turnos siguientes |
| Referencias y recursos de una skill | Solo cuando se leen; los scripts se ejecutan, no se cargan |
| Skill precargada en un subagente | Entera, al arrancar ese subagente |
| Herramientas MCP con búsqueda de herramientas | Nombres e instrucciones del servidor al inicio; esquemas bajo demanda |
| Herramientas MCP sin búsqueda de herramientas | Todos los esquemas al inicio |

El listado de skills tiene un presupuesto (escala con la ventana del modelo):
si se desborda, el runtime quita descripciones y la skill deja de dispararse
aunque esté instalada. Para Codex y OpenCode no se traslada este modelo sin
un contrato comprobado: su modo de carga queda `desconocido`.

## Campos del informe

| Campo | Contenido |
|---|---|
| Pieza | ID y ruta real, con hash o revisión leída |
| Tamaño | Bytes y líneas, separando descripción y cuerpo |
| Modo de carga | Siempre, al invocar, bajo demanda o `desconocido` |
| Estimación | Tokens estimados con su método, o `null` |
| Observación | Valor nativo con su fuente y fecha, o `null` |
| Cobertura | Qué se midió y qué no (ámbitos, runtimes, piezas omitidas) |
| Desconocidos | Lista explícita; nunca se rellenan con supuestos |
| Propuesta | Carga bajo demanda, consolidar o recortar la descripción; con su dueño |

## Lo que no se deduce

- **Inventariado no es cargado.** Un fichero presente no prueba que su cuerpo
  entre en el contexto; un MCP configurado no prueba conexión ni herramientas.
- No se calcula el «contexto disponible» restando el inventario a una ventana
  fija, ni se anuncia un ahorro porcentual de sesión por retirar piezas.
- El mismo contenido en dos ámbitos puede activarse distinto según
  procedencia y precedencia. Deduplicar el almacenamiento y la carga son
  decisiones distintas.
- Una herramienta MCP no sobra porque exista un binario parecido: permisos y
  semántica pueden diferir.
- Los topes del plugin son **límites de diseño**, no mediciones: `SKILL.md`
  ≤ 200 líneas, índice de piezas ≤ 45 líneas, brief de `task-brief.py`
  ≤ 10.000 caracteres (≈ 2.500 tokens solo por la heurística de caracteres / 4).
  Tampoco se convierten en prohibiciones automáticas de uso.

## Recogida con topes

- Lee con tope por fichero y por registro; un JSONL grande o inválido se
  representa como parcial, con el error, sin abortar el informe.
- No busques transcripciones privadas por tu cuenta: solo las rutas que el
  usuario indica o las que ya mide `usage-meter.py`.
- Aplica `read-discipline.md`: ignora dependencias y generados.

## Comparar con una línea base

Una comparación solo vale entre configuraciones equivalentes: mismo runtime,
misma versión, mismos ámbitos y misma selección. Si algo cambia, se declara
junto a la diferencia.

## Observación nativa en Claude Code

| Comando | Qué observa |
|---|---|
| `/context` | Uso actual del contexto por categorías; la fila de skills refleja el listado ya recortado al presupuesto |
| `/skill-doctor` | Coste en contexto de cada skill y frecuencia de uso (requiere versión reciente) |
| `/usage` | Coste de la sesión y límites del plan; no desglosa piezas |

Sus categorías describen ese runtime; no prueban las de otro.

## Fuentes

- Claude Code — Skills (carga, presupuesto del listado, descripciones recortadas): https://code.claude.com/docs/en/skills · consultada 2026-10-14.
- Claude Code — MCP, «Scale with MCP tool search» y `ENABLE_TOOL_SEARCH`: https://code.claude.com/docs/en/mcp · consultada 2026-10-14.
- Claude Code — Commands (`/context`, `/skill-doctor`, `/usage`): https://code.claude.com/docs/en/commands · consultada 2026-10-14.
