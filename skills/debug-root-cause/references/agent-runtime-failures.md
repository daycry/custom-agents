# Fallos de ejecución de un agente: bucles y deriva

Léela solo cuando lo que falla no es el código del proyecto sino la **ejecución del agente**: repite
la misma herramienta o el mismo fix, no avanza, acumula contexto, pierde el objetivo o trabaja sobre
otra rama, carpeta o servicio. Es el mismo método de las 4 fases del `SKILL.md`, con los datos que
hay que capturar en este tipo de fallo; no es un segundo procedimiento.

## Fase 1 — Captura (en vez de reproducción mínima)

Antes de reintentar nada, deja por escrito:

| Dato | De dónde sale |
|---|---|
| Objetivo activo | La tarea `T-XX` del ledger y su criterio, con sus palabras; no la paráfrasis del agente |
| Último paso con éxito y primer fallo | Comando o herramienta, con su salida literal |
| Secuencia pertinente | Las 3-10 llamadas que se repiten, en orden, con sus argumentos |
| Entorno observado | `pwd`, `git rev-parse --abbrev-ref HEAD`, `git status --short`, servicio y puerto si los hay |
| Supuestos | Lo que el agente da por cierto (rama, fichero, que un servicio responde) y aún no comprobó |
| Presión de contexto | Si el mismo bloque grande (log, fichero, salida) se ha leído o pegado varias veces |

Lo que no se pueda observar (no hay trazas, el proceso ya terminó) se declara como no verificable;
no se rellena con lo que «debió de pasar».

## Fase 2 — Clasificación del patrón

| Patrón | Señal en la captura | Prueba discriminante (la más barata) |
|---|---|---|
| Herramienta sin salida o al límite | La misma llamada devuelve vacío, truncado o timeout | Repetirla UNA vez acotada (menos ficheros, `head`, timeout explícito) y comparar |
| Contexto duplicado | El mismo log o fichero entra varias veces; las respuestas se alargan sin progreso | Contar cuántas veces aparece; resumirlo una vez con `fichero:línea` y seguir desde ahí |
| Conexión o puerto | `ECONNREFUSED`, timeout, puerto ocupado | Comprobar si el proceso escucha (`curl` al host local, `ss`/`netstat`) antes de tocar código |
| Cuota o tormenta de reintentos | 429, `rate limit`, reintentos sin espera creciente | Leer la cabecera o el mensaje de cuota; contar reintentos por minuto |
| Carpeta, rama o carrera | Cambios que «desaparecen», tests que pasan y fallan sin diff | Comparar `pwd`/rama/`git status` con lo que el agente cree; buscar otro proceso escribiendo |
| Fix fallido repetido | El mismo cambio (o su inverso) aplicado 2+ veces | `git diff` entre intentos: si no cambia la hipótesis, es el mismo intento |

Un fallo puede encajar en dos patrones; se registran ambos y cada uno lleva su prueba.

## Fase 3 — Hipótesis probada

Enuncia la causa de la ejecución en una frase falsable («repite `pytest` porque corre en `src/` y
el `conftest.py` está en la raíz») y ejecuta la prueba discriminante de la tabla. Si cae, vuelve a
la Fase 2 con el descarte anotado. Sin hipótesis probada no hay recuperación, solo otro intento.

## Fase 4 — Recuperación acotada y reversible

- Un cambio por vez, el mínimo que la hipótesis justifica: volver a la carpeta o rama correcta,
  arrancar el servicio local, acotar la lectura, esperar lo que indica la cuota.
- Reversible: nada de `git reset --hard`, `git clean`, borrar ramas o matar procesos ajenos; si la
  recuperación necesita algo así, se pregunta.
- Se comprueba con el mismo paso que fallaba en la captura, y su salida se pega como evidencia.
- El resultado es **completo** (el paso que fallaba ya pasa), **parcial** (avanza pero queda un
  descarte abierto) o **bloqueado** (falta un permiso, una credencial o un servicio que el agente no
  puede ni debe crear). Las tres salidas son válidas; un «arreglado» sin evidencia no lo es.

## Prohibido

- **Reintento a ciegas**: repetir la misma llamada sin cambiar nada observable.
- **Reset ficticio**: afirmar «reinicio el contexto» o «empiezo de cero» sin que nada se haya
  reiniciado de verdad; la conversación sigue siendo la misma.
- **Rebajar la meta**: sustituir el criterio de la tarea por una suboperación que sí sale.
- **Esperar como respuesta**: el paso del tiempo no arregla ni autoriza nada salvo una cuota con
  espera declarada.

## A quién se deriva

| Hallazgo | Dueño |
|---|---|
| El fix toca código del proyecto | `implementer` con el ledger; el veredicto de pruebas sigue siendo de `qa` |
| La causa es un hueco o ambigüedad de la spec | `analyst` vía `/pm-cycle` |
| La causa merece memoria | Propuesta según `agent-kits/shared/knowledge-write.md`, solo con Fase 4 completa |

El gancho del 3.er rojo de `/dev-cycle` y su contador no cambian: esta referencia solo dice qué
capturar y probar dentro de la pasada.
