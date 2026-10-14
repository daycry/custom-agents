# Contratos de herramientas y observaciones

Léela solo cuando diseñes o cambies la interfaz de algo que un agente invoca y cuya salida vuelve a
su contexto: un script de kit o de skill, la salida de un hook (`systemMessage`/`additionalContext`)
o una tool de un servidor MCP propio. El agente no lee el código: decide con el nombre, las
entradas, la salida, el exit code y el mensaje de error. Eso es el contrato.

La regla de determinismo (Paso 2, regla 1) dice *dónde* va el cálculo; esta referencia dice *qué
forma* tiene lo que el agente ve. Servidores MCP (transporte, permisos, stdout reservado al
protocolo): `skills/delivery-practices/references/delivery-tools.md`.

## Granularidad

| Decisión | Regla | Señal de que está mal |
|---|---|---|
| Lectura frente a escritura | Operaciones separadas (subcomando o `--dry-run`/`--check` frente a la acción), porque el permiso y la revisión dependen del efecto | Para ver qué haría hay que ejecutarlo |
| Mismo objeto, mismo riesgo | Subcomandos de un mismo script (patrón `journal.py capture-end · replay · …`) en vez de un script por acción: menos selección ambigua | Dos scripts con nombres parecidos que el agente confunde |
| Riesgo distinto | Pieza o subcomando propio con su confirmación; un efecto externo se prepara aparte y se ejecuta con aprobación ligada al objeto | Un flag inocuo cambia de leer a publicar |
| Tool nueva | Solo si un riesgo o un coste observado lo justifica; si no, un flag de la existente | Una tool por cada verbo del dominio |

## Nombres y entradas

- **Nombre estable.** Renombrar un script, subcomando o flag rompe prompts, evals y exports: es un
  cambio de contrato (callers, `scripts/export-interop.py --check`, CHANGELOG), no un refactor.
- **Portabilidad del nombre.** MCP admite letras ASCII, dígitos, `_`, `-` y `.` (1-128); la API de
  Claude exige `^[a-zA-Z0-9_-]{1,128}$`, sin punto. Un nombre que deba valer en ambos evita el punto.
- **Entradas estrechas.** Valores cerrados (`choices`) antes que texto libre; nada de parámetro
  «comando» o «JSON arbitrario» si basta un enum; rutas resueltas y comprobadas dentro de su raíz.
- **Validación en la entrada.** Un uso inválido sale con exit 2 y un mensaje que nombra el flag y
  los valores válidos; nunca un traceback como única observación.
- **Identificadores semánticos y estables** en entrada y salida (slug, `T-XX`, ID de entrada), no
  índices posicionales ni rutas temporales que cambian entre llamadas.
- **Sin interacción.** Un agente no contesta a un `input()`: si falta un dato, error de uso.

## Forma de salida

- **Determinista:** misma entrada y mismo estado → mismos bytes. Orden estable, sin marcas de
  tiempo salvo en un campo explícito, sin ANSI cuando la salida no es una TTY.
- **Dos vistas:** texto corto para el modelo y `--json` para otras piezas. La vista JSON es la que
  se versiona (`schema_version`) si se persiste o la consume otro script.
- **stdout = resultado, stderr = diagnóstico.** Mezclarlos rompe a quien parsea stdout.
- **Presupuesto explícito:** salida acotada en líneas o bytes, con aviso de truncado y cómo pedir
  el resto (`--limit`, filtro, paginación). Truncar en silencio hace que el agente razone sobre
  un resultado parcial como si fuera completo. Topes de hooks: `references/claude-code-contracts.md`.
- **Codificación:** UTF-8 en ambos sentidos (Paso 2, regla 6).
- **Lo que la tool no devuelve** se dice en su ayuda o descripción, para que el agente no lo
  busque por inferencia.

## Observación legible

Cada salida responde a lo que el agente necesita para su siguiente paso:

| Elemento | Por qué |
|---|---|
| Estado en la primera línea (`ok` · `gap` · `error`, o ✅/⚠️/❌) | Es lo que se lee aunque el resto se trunque |
| Qué se comprobó y sobre qué (ruta, ID, revisión) | Evita aplicar el resultado a otro objeto |
| Evidencia mínima (`fichero:línea`, conteos) | Permite citar sin volver a leer |
| Siguiente paso o comando que lo arregla (patrón `agent-kits/shared/doctor.py`) | Convierte el error en acción |
| Lo no comprobado, como ausente (`null`, «no medido»), nunca como cero | Un cero inventado pasa por dato |
| Si el resultado es terminal o transitorio | Decide si tiene sentido repetir |

## Errores y recuperación

| Clase | Exit | Lo que dice el mensaje | Lo que hace el agente |
|---|---|---|---|
| Correcto (incluido «nada que hacer», dicho) | 0 | Resultado | Sigue |
| Veredicto negativo: la tool funcionó y el resultado es rojo | 1 | Qué falla y dónde | Corrige la causa; repetir igual da lo mismo |
| Uso o entorno: flag inválido, herramienta ausente, config ilegible | 2 | Qué falta y cómo arreglarlo | Corrige la llamada o degrada con aviso |
| Transitorio: cerrojo ocupado, timeout | documentado por la pieza | Que es transitorio y cuánto esperar | Reintento acotado, solo si la operación es idempotente |

- **Ausente, inválido, prohibido y no disponible** son estados distintos. Un JSON corrupto leído
  como «vacío» acaba sobrescrito por la siguiente escritura.
- **Resultado por paso.** Si una operación tiene varios pasos, informa de cada uno; un mensaje
  general de éxito con un paso fallido es una observación falsa.
- **MCP:** los errores de ejecución (validación de entrada, fallo de API, regla de negocio) van en
  el resultado con `isError: true` para que el modelo se corrija; los de protocolo (tool
  desconocida, petición mal formada) son errores JSON-RPC, con menos opciones de recuperación.
  Si la tool declara `outputSchema`, `structuredContent` debe cumplirlo, y por compatibilidad
  conviene repetir el JSON serializado en un bloque de texto.

## Estado entre llamadas

Si una tool necesita estado, devuelve un **handle explícito** que el agente pasa en las llamadas
siguientes: opaco (no codifica estructura que invite a adivinar), con caducidad declarada en la
descripción de la tool que lo crea, y autorización comprobada en cada llamada (un handle es un
nombre, no un permiso). Un handle desconocido o caducado devuelve un error de ejecución que lo dice,
para que el agente lo recree en vez de reintentar. Estado que sobrevive a la sesión:
`references/persistent-workflows.md`.

## Envolturas

Una envoltura tipada (estado, datos, errores, siguiente paso) es para las tools que se diseñan
aquí. No reescribas ni normalices en silencio la salida de una API o tool nativa ajena: si un
adaptador la recorta, declara qué quita.

## Verificación

- Un test por clase de salida (correcto, gap, uso, ausente, truncado) que compruebe el exit code y
  la primera línea; codificación en `tests/test_console_encoding.py`.
- Dos diseños de tool se comparan con el protocolo de `skills/outcome-evals/references/protocol.md`
  (mismos casos, mismas condiciones); sin medición no se afirma que uno mejore la tasa de éxito.

## Fuentes

- [MCP — Tools (especificación 2026-07-28)](https://modelcontextprotocol.io/specification/latest/server/tools): nombres, `inputSchema`/`outputSchema`, `structuredContent`, `isError`, handles de estado. Consultada el 2026-10-14.
- [Claude API — Define tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools): regex del nombre, descripciones, operaciones agrupadas, identificadores estables y respuestas de alta señal. Consultada el 2026-10-14.
