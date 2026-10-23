# Pruebas F#, bucle generador-evaluador y puerta de hechos antes de editar — S110–S112

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Tres cuerpos completos: **29.700 bytes/766 líneas**, sin recursos locales.
El hook y el script que citan S111/S112 (`scripts/gan-harness.sh`,
`scripts/hooks/gateguard-fact-force.js`) no se leyeron.
[fsharp-gan-gateguard-reading-evidence.json](fsharp-gan-gateguard-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08.

## S110 — Pruebas en F#

`7.941 bytes/281 líneas`. xUnit, FsUnit, Unquote, FsCheck, NSubstitute, Testcontainers
y WebApplicationFactory; organización y antipatrones.

**Comparación.** Encaja en la especialidad opcional `dotnet-practices` (S064, S086).
Correcciones: `UseInMemoryDatabase` en la prueba de integración no reproduce el
motor relacional (mismo defecto que SQLite en S081/S101; Testcontainers, que la
propia pieza lista, es la opción adecuada); el generador de emails con tres
nombres y dos dominios no es una propiedad, es una tabla de casos; el test de
«serialización de ida y vuelta» con igualdad estructural puede pasar ocultando
pérdida de precisión de `decimal` según el serializador. **Destino:** sección F#
en `dotnet-practices/references/testing.md`.

## S111 — Arnés generador-evaluador

`12.431 bytes/279 líneas`. Planificador, generador y evaluador separados que iteran
contra la aplicación en ejecución hasta superar una puntuación ponderada.

**Comparación.** El plugin ya separa producir de evaluar con contexto fresco
(`implementer` frente a las lentes de `adversarial-review` y `qa`) y acota el bucle
a 3 intentos con trazas en el ledger. Diferencias que no se adoptan:

| Afirmación | Motivo |
|---|---|
| Planificador «deliberadamente ambicioso» que convierte una línea en 16 funciones | El plugin presupuesta y fija alcance con el usuario (analyst, evaluator); ampliar alcance sin aprobación contradice la puerta go/no-go |
| Aprobado por puntuación ponderada de diseño y originalidad (umbral 7) | Los veredictos del plugin son deterministas (`qa-gate`, criterios por tarea); una nota de modelo no es criterio verificable (outcome-evals) |
| Hasta 15 iteraciones, 125-200 $ por ejecución | Coste sin medición propia; el plugin acota a 3 y mide con `usage-meter` |
| Cifras de resultados atribuidas a una publicación externa | No contrastadas en esta lectura |

**Conservar** dos reglas que ya rigen: el evaluador no propone y evalúa sus propios
arreglos (las lentes son de solo lectura), y la retroalimentación viaja en fichero
(sección de revisión en el ledger). **Sin destino nuevo.**

## S112 — Puerta de hechos antes de la primera edición

`9.328 bytes/206 líneas`. Hook PreToolUse que deniega la primera edición, escritura
o comando de cada fichero hasta que el agente aporta hechos (quién importa el
fichero, esquema de datos, instrucción literal del usuario) y luego permite reintentar.

**Comparación.** El plugin tiene guardias por rol (`guardrail-check.py`,
ADR-007) que **deniegan acciones prohibidas**, no acciones legítimas para forzar
investigación. Una denegación genérica en la primera edición cambiaría el
contrato de los hooks globales («informan, no deciden»). La pieza documenta
bien sus límites (lotes paralelos con aplicación parcial, condensar mensajes
repetidos, desactivación explícita).

| Afirmación | Valoración |
|---|---|
| A/B con +2,25 puntos sobre dos tareas | Muestra mínima y calificación subjetiva; no acredita el efecto |
| Denegar la primera edición en un lote paralelo deja aplicadas las demás | Riesgo real que la propia pieza declara; incompatible con las ediciones en paralelo de los agentes |
| Desactivar con variables de entorno en la sesión | Una puerta que el propio agente puede desactivar no es un control |
| Las preguntas de hechos (importadores, esquema real, instrucción literal) | **Útiles** como contenido: ya pedidos por `task-brief.py` (contexto) y por `debug-root-cause` (evidencia) |

**Decisión.** No adoptar el hook. Valorar añadir «quién importa este fichero» y
«formato real de los datos» a la checklist previa del implementer.
