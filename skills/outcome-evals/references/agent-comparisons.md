# Comparar agentes, workflows o runtimes

Léela solo cuando la comparación enfrenta **ejecuciones de agentes** (dos agentes, dos versiones de
un workflow, el mismo agente en dos runtimes) sobre las mismas tareas. Las reglas comunes (casos y
checks fijados antes, baseline/variante, pass@k, registro de runs) están en el
[protocolo](protocol.md); aquí solo lo que añade ejecutar agentes.

## Estado: preparación manual

El plugin no trae un runner de agentes con contrato verificado. `evals/run.py` mide **activación**
(qué pieza se dispara), no si la tarea quedó resuelta; `report_outcomes.py` **agrega** JUnit de
ejecuciones ya hechas, no lanza agentes ni crea copias. Por eso esta referencia entrega el diseño y
los checks de la comparación como **preparados**; cada ejecución no realizada queda `not-run` y su
coste `null`. No anuncies una mejora de agentes sin runs reales.

Antes de adoptar un runner externo: revisión fijada del runner, contrato documentado de sus
adaptadores por runtime, comandos comprobados contra esa versión (no contra su README) y
autorización vigente para sesiones con coste. Mencionarlo en una guía no concede esa autorización.

## Aislamiento por run

Cada run parte de una copia nueva de la misma revisión y fixture. Un worktree aísla **ficheros del
repositorio**, no:

| Fuga | Cómo se contamina la comparación | Qué fijar |
|---|---|---|
| Red y servicios | Un run deja datos en la base local o en una cola que el siguiente lee | Servicio por run o reset verificado entre runs |
| Credenciales | Un agente usa una cuenta con más permisos | La misma identidad y permisos en todas las variantes |
| Cachés personales | Paquetes, modelos o índices ya calientes en el segundo run | Caché fría declarada o calentada igual para todos |
| Configuración del anfitrión | Hooks, plugins, memoria o `CLAUDE.md` del usuario cargados en una variante y no en otra | Sesión sin configuración del anfitrión, o la misma en todas |
| Orden y hora | Cuotas, latencia o datos que cambian a lo largo del día | Alternar el orden de variantes; registrar inicio y fin |

## Condiciones por runtime

Al comparar runtimes (Claude Code, Codex, OpenCode) o versiones del mismo, registra por run:
runtime y versión, modelo, flags exactos, modo de permisos, herramientas permitidas, piezas cargadas
y presupuesto de turnos. Si una variante no puede reproducir una condición (otra herramienta, otro
modo de permisos), la diferencia se publica como condición distinta, no como resultado del agente.

Una herramienta ausente, un permiso denegado o un timeout del runtime son resultados `error`
distintos de un fallo funcional: se cuentan aparte y no se atribuyen al agente comparado.

## Repeticiones

Los agentes no son deterministas: el mismo caso puede pasar y fallar. Mínimo **k ≥ 3** runs por
caso y variante para **ver** la variación, no para concluir: tres repeticiones dicen si hay
dispersión, no cuánta en general. Publica por caso los k resultados, no solo la media, y deriva
pass@k / pass^k como indica el protocolo.

## Casos versionados

| Campo | Regla |
|---|---|
| Petición | Texto literal versionado; igual para todas las variantes |
| Revisión y fixture | SHA de 40 hex y hash del fixture; no cambian entre variantes |
| Criterio | Check ejecutable (test, contrato, script de puerta) escrito antes del primer run |
| Juez | Determinista primero; un modelo como juez solo auxiliar, con modelo y prompt registrados |
| Presión del prompt | Neutra, de apoyo o en contra, fijada como condición |

## Métricas

| Métrica | Fuente válida | Si falta |
|---|---|---|
| Resultado del check | El check del caso | `not-run` (no cuenta como pass) |
| Duración | Inicio y fin medidos por el runner | `null` |
| Tokens y coste | Medidor del runtime o `usage-meter.py` | `null`, con el motivo |
| Turnos y llamadas | Transcripción del run | `null` |

No estimes tokens ni coste a partir de la longitud de la salida. Una variante más barata que falla
más casos no «mejora»: publica éxito y coste por separado.
