# Comparación de aprendizaje de sesión y reglas con evidencia

Fichas S053–S054 de la revisión
`ef648e01899ba3e8dc6371642deaaf64b4477775`. Dos cuerpos completos:
18.685 bytes/509 líneas. Se leyeron los **13 recursos locales completos**:
229.641 bytes/6.055 líneas, incluidos el CLI de 2.290 líneas y sus tests
de 1.420 líneas. [learning-reading-evidence.json](learning-reading-evidence.json)
registra 32 fuentes, 22 archivos propios, reutilizaciones comprobadas y
cuatro contrastes documentales oficiales. El progreso pertenece a
[tasks.md](../tasks.md); los comandos y callers leídos no se cuentan como
otras piezas evaluadas de T-04/T-05.

Son **decisiones de comparación y destinos propuestos para T-08**, no una
integración entregada. No se ejecutaron hooks, tests, imports, observadores,
modelos, migraciones, promociones, exportaciones o borrados del corpus.
Tampoco se modificó la memoria del proyecto ni la configuración del usuario.
Tokens y latencia son null. Leer código y comprobar hashes no demuestra
eficacia, seguridad completa o compatibilidad operativa.

## S053 — Extraer patrones al revisar una sesión

**Identidad y lectura.** SHA-256
`d494867b456999cad53c51c89fa2cf8da101f76ea875286987f52e5d45f72221`;
4.536 bytes/132 líneas. Sus dos recursos se leen completos.

**Contrato y valor.** Distingue resoluciones de errores, correcciones del
usuario, workarounds, técnicas de depuración y convenciones del proyecto.
Descarta typos y episodios sin evidencia de reutilización. El umbral de
mensajes pretende evitar extracción en sesiones demasiado pequeñas.
Lo útil es una petición de revisión que produzca una propuesta verificable,
con problema, causa, solución, trigger y fuente; no una skill por cada arreglo.

**Defecto comprobado.** El frontmatter declara la pieza retirada y ordena
redirigir a S054; la sección Status todavía permite escogerla. Su descripción
anuncia detección y escritura automáticas que sus scripts no implementan:

- R-09bf01be57cc crea la carpeta de destino, cuenta coincidencias en el
  transcript y emite dos avisos por stderr. No extrae ni escribe una skill.
  Su grep de `transcript_path` exige una serialización sin espacios y no
  resuelve escapes JSON. El contador busca también una forma literal; con
  cero coincidencias, `grep -c ... || echo 0` puede devolver dos ceros en
  líneas distintas y romper la comparación numérica.
- El caller de producción R-b18149810e30 usa JSON y admite espacios al contar
  mensajes, pero termina igualmente con avisos, sin extractor ni escritor.
  Acota el string de stdin; R-076e8356b72b lee íntegro el transcript para
  contar coincidencias. No comprueba el historial como registros válidos ni
  impone un presupuesto total de lectura.
- R-93b17f9535e7 declara categorías, exclusiones, threshold y `auto_approve`;
  los dos evaluadores solo consumen longitud mínima y ruta de destino.
  Declarar `auto_approve: false` no entrega una puerta de aprobación real.
- R-a48aec12c9dd conserva el evaluador Node en Stop, asíncrono, con timeout
  de 10 segundos. La retirada declarada de la skill no retiró ese caller.
  El manual presenta Stop como cierre único de sesión; ese supuesto es
  incorrecto. Los avisos con exit 0 tampoco entregan la petición al modelo.

Stop corresponde al final de una respuesta; SessionEnd, al final de la
sesión. El stderr con exit 0 se conserva para depuración y no lo recibe
Claude. Esa diferencia explica por qué señalar «evalúa» no acredita una
extracción automática. [Contrato oficial de hooks](https://code.claude.com/docs/en/hooks#exit-code-0).

**Cobertura existente y delta.** `knowledge-write.md` ya fija umbrales de
ADR/gotcha/lección, procedencia y estado propuesta; `debug-root-cause`
aporta causa probada y regresión; `/retro` decide qué aprendizaje merece
memoria. `journal.py candidatas` agrupa decisiones y pendientes de sesiones
distintas y conserva sus fuentes. Ninguno equivale a extracción automática
de errores y correcciones a partir de cualquier transcript.

**Decisión: consolidar.** Conservar las categorías y la revisión manual en
una sola capacidad opcional `skills/session-learning/SKILL.md`, con método
en `references/candidate-pipeline.md`. Reutilizar journal/outbox y las puertas
de memoria; eliminar la segunda vía de extracción, sus callers reemplazados
y campos sin consumidor cuando se implemente T-10/T-12/T-15. Una compatibilidad
histórica solo se conserva si tiene usuarios y un contrato útil comprobados.

**Disparadores estáticos.** «Extrae una lección reutilizable de este fallo»
y «revisa qué aprendimos en la sesión» activan propuesta con evidencia.
«Retoma dónde estábamos» va a continuidad S035; «haz un dataset» a
training-data-services; «crea una skill aprobada» exige creación de pieza
y su validación, no aprobar memoria implícitamente. Estos casos no se ejecutaron.

## S054 — Observación, candidatos atómicos y evolución

**Identidad y lectura.** SHA-256
`ddad12451a0d582c6ef1b197b7be193bef613cbc74eba4117fcb74fc7a4ecd00`;
14.149 bytes/377 líneas. Once recursos locales completos:
226.859 bytes/5.968 líneas.

**Contrato y contenido único.** Propone una unidad pequeña: ID, trigger,
acción, dominio, evidencia, ámbito y estimación de confianza. Separa patrones
observados e importados; ofrece inventario, intercambio, promoción entre
ámbitos y agrupación para proponer skills/comandos/agentes. El pipeline
combina captura por tool, análisis opcional y escritura de reglas. Esto
añade granularidad y trazabilidad al journal; no sustituye la memoria curada,
el case store ni los backends de recuperación.

### Qué hace realmente la captura

R-3b02f94e1e1a registra fase, tool, sesión, proyecto, input y output. Recorta
los dos últimos campos a 5.000 caracteres y aplica una expresión de secretos.
No hay captura de prompts del usuario en ese recurso; los diagramas de
captura integral y correcciones directas no quedan respaldados por su payload.
La redacción tampoco cubre todo dato sensible: no procesa sesión/nombre del
proyecto, limita longitudes de secretos y guarda un fragmento del input
malformado. No contiene exclusión por la etiqueta privada que usa nuestro journal.

El contexto automatizado, `agent_id`, perfiles y marcas de desactivación
provocan skips deliberados. R-bf8034b7b095 también omite el trabajo si falta
shell, fase o recurso. Por tanto, la afirmación de observación completa no
está medida y contradice las rutas de omisión del propio código.

El grafo principal registra preobservación y el dispatcher post, no un
observador equivalente de PostToolUseFailure. El contrato distingue éxito y
fallo de tool. Las reglas basadas en resolución de errores necesitarán unir
intento, fallo, corrección y resultado; observar el preevento no prueba éxito.
Los hooks asíncronos tampoco pueden bloquear la acción original.
[Eventos y ejecución asíncrona](https://code.claude.com/docs/en/hooks#run-hooks-in-the-background).

La integración Node pasa la fase desde el ID del hook. El ejemplo manual
de S054 llama al shell sin fase y este busca una variable de entorno, en
lugar del `hook_event_name` del JSON: ese ejemplo no entrega un despacho
pre/post fiable por sí mismo. No se atribuye ese fallo al runner principal,
que sí pasa `pre` o `post` explícitamente.

El runner limita la invocación del shell a 9 segundos, pero sus probes de
shell no tienen timeout. El shell consume stdin antes de sus guardias y puede
arrancar un proceso cuyo bootstrap espera hasta 10 segundos. Sus límites de
subprocesos no constituyen un presupuesto agregado de hook. El wrapper
principal acota stdin; esa protección no se extiende al ejemplo manual
directo ni demuestra una latencia máxima en el recorrido completo.

### Identidad, ámbitos y escritura concurrente

R-bfbbc1c8e8e9 y el CLI normalizan remoto o raíz y usan 12 hex de SHA-256.
Es una clave práctica de agrupación, no una frontera de autorización. Remoto
y nombre pueden cambiar; repositorios distintos pueden compartir remoto;
la normalización convierte toda ruta remota a minúsculas. Se exige política
de identidad propia y detección de colisión, sin tratar un mismo hash como
evidencia de que dos almacenes deban compartir instrucciones.

Ambos detectores respetan una raíz explícita sin Git. Sin embargo, el hook
de observación la elimina si su cwd no pertenece a Git y fuerza el bucket
global. Por ello, el aislamiento prometido no se mantiene en ese recorrido.
La detección también crea carpetas, migra directorios y actualiza registro:
status y dry-run pueden tener efectos de escritura antes de su operación.

El escritor Python usa reemplazo atómico y flock donde existe; Windows no
obtiene ese lock. El escritor shell no comparte el cerrojo. Los comandos de
mantenimiento leen el registro antes de adquirir el lock de escritura, así
que bloquear solamente `_write_registry` no serializa toda la transacción.
Un registro corrupto se sustituye por uno vacío sin conservar el original.
Atomicidad de archivo y exclusión de transacción son requisitos diferentes.

El parser admite cualquier ID no vacío, claves duplicadas, confianza fuera
de rango y valores no finitos. Su formato se parece a YAML, pero no implementa
YAML completo: `---` dentro del cuerpo se interpreta como otro bloque.
La validación de ID protege las promociones; no entrega un esquema equivalente
en todas las entradas, imports, exports y generación.

### Modelo, finalización y observaciones no procesadas

R-b074e432e361 toma las últimas 500 líneas por defecto, crea un snapshot y
lanza `claude --print`, modelo configurable, máximo de turns y watchdog.
Protege el resultado mediante descriptores abiertos a un archivo temporal
desvinculado y exige un único marcador final. Retiene las observaciones si
el proceso falla o falta el marcador. Son mecanismos útiles de resultado
explícito y reintento; un marcador escrito por el modelo no valida por sí
solo la calidad ni el contenido de las reglas creadas.

El marcador de éxito permite archivar **el archivo vivo completo**, no solo
el snapshot analizado. Puede apartar el prefijo no leído y eventos llegados
durante el análisis. La rotación de captura también puede interferir con
esa ruta. El destino nativo deberá confirmar un lote estable por IDs/cursor,
retener cualquier evento nuevo y declarar muestra/omisiones, sin marcar como
procesado lo que no se leyó.

El prompt ordena escribir sin preguntar y trata las observaciones como datos
no confiables; ambas son instrucciones al modelo, no guardias de filesystem.
La invocación usa `--allowedTools Read,Write`: concede ejecución sin prompt,
no restringe por sí sola la lista de herramientas disponibles. No declara
`--tools`, aislamiento de settings/MCP ni confinamiento de destinos.
[Semántica oficial del CLI](https://code.claude.com/docs/en/cli-reference#cli-flags).

La captura queda en disco local, pero su análisis pasa por un CLI de modelo.
El export conserva cuerpos y metadata sin redacción propia; «solo patrones»
no demuestra ausencia de código, conversación o datos identificables. El
diseño debe distinguir persistencia local, inferencia y distribución.

En Windows nativo el cuerpo declara que el proceso no sobrevive al cierre del
hook; el código diagnostica reinicios repetidos y evita analizar salvo override.
No se ejecutó para validar esa declaración. El plugin necesita una operación
nativa comprobada en Windows y los tres runtimes; no vale habilitar una
configuración y anunciar aprendizaje funcionando. PID vivo tampoco verifica
identidad: el código puede señalizar o detener un PID reutilizado.

### Intercambio, promoción, generación y retirada

- **Import.** HTTPS, resolución pública inicial, tope remoto de 2 MiB,
  timeout y confirmación son buenos puntos de partida. La resolución y el
  fetch no están ligados a la misma conexión; no se valida cada redirect.
  urllib incorpora un redirect handler. La ausencia de validación del salto
  siguiente es una inferencia del recorrido leído, no una prueba de exploit.
  [Redirecciones oficiales](https://docs.python.org/3.13/library/urllib.request.html#httpredirecthandler-objects).
  El archivo local se lee sin ese tope. Los imports comparan confianza por ID,
  no contradicciones semánticas, y un update elimina el **archivo** anterior:
  si contiene otras reglas, estas se pierden. Las rutas de salida con timestamp
  pueden colisionar y las escrituras de reglas no son transacciones atómicas.
- **Export.** Filtra dominio/ámbito/confianza, pero por defecto mezcla proyecto
  y global, permite sobrescribir el destino y no redacciona el cuerpo. Omite
  campos falsy como confianza cero y no serializa todas las cadenas de forma
  homogénea. Intercambio debe conservar esquema, procedencia y decisión de
  difusión; no usar el número de confianza como sustituto de revisión.
- **Promote.** La selección automática une el mismo ID en dos proyectos con
  media ≥0,8 y toma el cuerpo con mayor confianza; requiere confirmación salvo
  force. No compara acciones contradictorias, no limita dominios universales
  como aconseja el prompt y retira las copias de proyecto. Conservar la
  previsualización y trazabilidad; la ampliación de ámbito necesita juicio
  explícito y conservación de excepciones, no votación por repetición.
- **Evolve.** Agrupa triggers por palabras inglesas, coincidencia mínima y
  coeficiente de solape; es una heurística dependiente del orden, no detección
  de equivalencia. Dos reglas forman candidato de skill; tres y suficiente
  confianza forman agente. El número de reglas no acredita responsabilidad
  nueva. El generador crea archivos, pero un agente generado solo enumera
  IDs y dominios: no entrega las acciones de las reglas. Las colisiones se
  resuelven dentro del lote, no frente a archivos ya existentes. No hay gate
  de propiedad, evaluación de utilidad ni export multi-runtime del resultado.
- **Retirada.** GC considera reglas parseadas y observaciones activas, pero
  ignora evolved, pendientes y archivos históricos antes de borrar el proyecto.
  Merge omite archivos con cualquier ID duplicado y después borra el origen,
  aunque contengan otros IDs; tampoco migra todos sus artefactos. Prune actúa
  sobre todos los proyectos y usa mtime si falta fecha; quiet todavía devuelve
  éxito cuando hay borrados fallidos. Edad o contador cero no prueban ausencia
  de contenido valioso. Hace falta plan, backup/revocación, verificación y
  exclusión de procesos activos; no copiar un borrado automático global.

Los lectores `is_file`/`is_dir` siguen enlaces por defecto. Su presencia no
acredita confinamiento, aunque la retirada recursiva concreta sí resuelve y
comprueba contención antes de borrar.
[Contrato Path de Python 3.13](https://docs.python.org/3.13/library/pathlib.html#pathlib.Path.is_file).

### Destino de los trece recursos locales

| Recurso | Valor/defecto comprobado | Destino propuesto |
|---|---|---|
| R-93b17f9535e7 · config de S053 | Umbral y taxonomía; varios campos no consumidos | Config opt-in de session-learning, validada por esquema y consumidor real |
| R-09bf01be57cc · evaluador shell | Señal de revisión; no entrega extracción | Sustituir por el único pipeline de propuestas y retirar su caller |
| R-b074e432e361 · observer loop | Snapshot, reintento, señal final y watchdog; archive de datos no leídos, permisos sin restricción de tools | `candidate-pipeline.md` y servicio compartido `learning.py`, lotes transaccionales y adaptadores T-09 |
| R-ac3c322987fa · método del observador | Triggers estrechos, categorías y evidencia; puntuación declarada en prompt | `candidate-pipeline.md`, score heurístico separado de aprobación |
| R-0fe5dcabdfb7 · guardian | Horario, cooldown y actividad opcionales; fallos de detección permiten continuar, lock persistente | Política opcional del scheduler propio con estado desconocido y lease verificable |
| R-95b5ae2a73e0 · start/stop/status | Diagnóstico y limpieza; status muta, PID sin identidad, carreras de arranque | Diagnóstico en doctor/panel y control nativo de jobs, sin alterar estado al consultar |
| R-30610fcbd0b0 · config de S054 | Observer deshabilitado y thresholds pequeños | Una config propia explícita, sin activar modelo por descubrir el plugin |
| R-3b02f94e1e1a · hook de captura | Eventos/redacción/rotación/throttle; privacidad incompleta, pérdida de ámbito y costes agregados | `observation-contract.md`, redactor/outbox compartidos y hooks nativos T-09/T-12 |
| R-bfbbc1c8e8e9 · detector | Agrupar checkout/worktree; migración y registro durante detección | Resolver de identidad propio de solo lectura; migración separada y validada |
| R-091ff88fa6e3 · CLI | Status/import/export/promote/evolve/maintenance; esquema débil y pérdidas por archivo/transacción | `candidate-exchange.md`, servicios de propuesta/curación y especialización; no segundo CLI canónico de memoria |
| R-5224873745a6 · resolver de directorio | Raíz explícita antes de defaults; diferencias de ruta Windows entre shell/Python | Resolver compartido por runtime, raíz privada declarada y confinada |
| R-78fa8e7a7d56 · migración | Rechaza destino no vacío; sin proceso verificable o transacción integral | Ciclo de instalación/mantenimiento S046/S047, plan/backup/undo sin migración implícita |
| R-9d24574fa402 · tests del CLI | Fixtures de parser, precedencia, promoción y mantenimiento | Casos propios en T-12/T-14, ampliados con fallos, concurrency, enlaces y conservación de todas las entradas |

Los tests del corpus se **leyeron, no se importaron ni ejecutaron**. Sus
fixtures de fsync/replace no comprueban una transacción de mantenimiento con
escritores concurrentes. Los tests de import y de fronteras HTTP que harían
falta no se acreditan por tres mocks de validación de URL. La lectura de
tests fuera de estos directorios y del grafo completo sigue en T-06.

### Comparación con nuestra memoria y decisión

| Necesidad | Cobertura propia comprobada | Delta a integrar |
|---|---|---|
| Retomar sesión | Journal episódico, outbox/replay y contexto acotado | Conservar S035 como dueño de retoma; el aprendizaje no crea otro registro de tareas |
| Detectar repetición | `journal.py candidatas`: decisiones/pendientes, sesiones distintas, evidencia y estado propuesta | Resultados de tools y correcciones observables, sin contar pre/post como dos éxitos independientes |
| Decidir conocimiento | Umbrales de knowledge-write, curator y gate de categoría/fuentes/tags/denylist | Candidatos atómicos; score no cambia estado aprobado ni resuelve contradicciones automáticamente |
| Recuperar | knowledge-find distingue propuesta/doctrina y consulta/related/show; fallback local | Trigger/ámbito/versiones pertinentes y cantidad limitada, sin inyectar toda la biblioteca |
| Conservar casos | training-data-services opt-in, Gold humano, bridge que propone | Mantener separados caso, observación y conocimiento; no entrenar ni marcar Gold por frecuencia |
| Especializar | Personas y lector de extensiones entregados; escritura de `/specialize` sigue planificada | Proponer la pieza mínima útil, comprobar colisiones/propiedad y validar por runtime antes de publicarla |
| Servicios externos | knowledge-services separa curación de publicación | Aprendizaje complementa el corpus aprobado; comparación completa de recuperación/grafos sigue en T-07 |

La memoria propia tiene dos contratos que T-07 debe reconciliar antes de
añadir otro productor: ADR/gotcha/lección con estado aceptada y el árbol
candidates/approved con estado aprobado. Además, la descripción de curator
se declara único escritor de candidatos, mientras el bridge de casos se
describe como productor de pending. Se debe precisar **quién propone, quién
persiste y quién aprueba**, con servicios compartidos y un contrato por
artefacto. Las instrucciones de roles no prueban enforcement del runtime;
esa frontera permanece en T-09. No se declara resuelto por esta comparación.

**Decisión: consolidar y ampliar.** Una sola skill opcional session-learning
para propuesta manual/automatizada; los tres documentos de referencia del
mapa contienen pipeline, captura e intercambio. `agent-kits/shared/learning.py`
es un destino propuesto de servicio compartido, todavía no implementado.
Curator conserva el juicio y el gate existente; la validación humana aplica
según sus políticas actuales de contradicción/alto impacto y las de
generación/difusión. No se añade aprobación automática por 0,7 ni se convierte
silencio del usuario en evidencia de acierto.

Preservar los umbrales como señales ajustables y medidas de evidencia, sin
presentarlos como probabilidad calibrada. La decadencia y aumentos por
corrección se describen en prompts; el CLI no entrega un motor determinista
equivalente. La promoción global compara contenido, contexto y excepciones,
mantiene procedencia, y requiere una política explícita de ámbito. Usar la
escalera de especialización existente en lugar de generar un agente por
tres reglas o incorporar una convención del framework como norma universal.

**Disparadores estáticos.** «Detecta patrones repetidos y proponlos para
memoria» y «importa estas reglas para revisarlas» entran en captura/propuesta
o intercambio. «Activa un grafo de memoria» va a knowledge-services y
comparación T-07; «reanuda la tarea» a journal/ledger; «aprueba todos los
patrones porque aparecen tres veces» conserva la puerta de curación. Sin
opt-in o proveedor compatible, se explica la degradación y sigue el ciclo.
No se ejecutaron estos escenarios ni una inferencia real del observador.

## Dependencias, carga y validación pendiente

Las 509 líneas de cuerpos son metadata/método; los 6.055 recursos locales
se cargan o ejecutan bajo demanda según su caller, no se suman como contexto
activo. El observer envía un prompt y un snapshot al CLI; no se midieron tokens
ni latencia. La frecuencia de invocación, tamaño de lote y turnos deben
presupuestarse separadamente de las escrituras y de la recuperación.

T-08 fija la arquitectura tras T-03/T-06/T-07. T-09 comprueba payloads,
presupuesto agregado, permisos, reentrancia y despacho nativo; T-10/T-12
implementan capacidad y servicios opt-in; T-13 muestra estado real y motivos,
no porcentajes de confianza como calidad; T-14 ejecuta regresiones y evals;
T-15 retira rutas reemplazadas y sincroniza docs/exports. Los comandos
C018/C035/C036/C037/C043/C065/C066/C072 necesitan ficha propia en T-05;
haber leído sus cuerpos como consumidores no cierra esa tarea.

Casos obligatorios para esa integración: proyecto sin Git, dos proyectos
con el mismo remoto, worktrees, raíz Windows, payload excesivo/truncado,
secretos y turno privado, intento sin resultado, fallo seguido de corrección,
repetición independiente entre sesiones, contradicción, NaN/confianza fuera
de rango, marcador falsificado/incompleto, timeout, PID reutilizado, lease
huérfano, eventos nuevos durante análisis/rotación, dos imports del mismo ID,
update de un archivo con otras entradas, redirect a destino no permitido,
enlaces, escritura parcial, generación sobre archivo modificado y limpieza
con datos históricos. Comparar precisión de propuestas, conservación y coste
con el journal actual. No declarar aprendizaje mejorado antes de medirlo.
