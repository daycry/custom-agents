# Sesiones, revisión de planes y reemplazo de estado

Checkpoint: 2026-10-11; revisión fijada del corpus y hashes en
[role-hook-reading-evidence.json](role-hook-reading-evidence.json).
Tres cuerpos leídos completos; recursos descargados se distinguen de recursos leídos.
Esta lectura estática no ejecuta el origen ni certifica su servidor o dispatch nativo.

| Recurso y secciones | Criterio útil y diferencia | Destino propio |
|---|---|---|
| R-115137fae3ce:55–129 | Un temporal único evita que otro escritor consuma su payload; los reemplazos tienen intentos y espera finitos. El comentario de plataforma no restringe la ejecución: el código decide por códigos de error, con fallback de espera activa | Medidor: temporal exclusivo por PID/UUID, cuatro intentos solo en Windows ante 5/32/33, esperas 20/40/80 ms. Sin espera activa ni retry de otros errores; fallo visible y limpieza solo del temporal propio |
| R-115137fae3ce:16–52,131–148 | Cache compartida por ID saneado/truncado en un directorio temporal global. El saneado puede colisionar y no vincula un proyecto ni autentica el estado | No usar esa caché como memoria ni autoridad. Mantener el estado local y la identidad explícita de nuestras mediciones; temporal único no implica fusión de updates concurrentes |
| R-5f85c39068f7:71–140,160–223 | Intención útil: entregar feedback cuando no hay await activo. El drain borra la cola antes de presentar el contexto; el texto muestra solo 20 items y puede perder detalles. Su fallback no opera si hay port pero falla el servidor, y Stop no es SessionEnd | Conservar decisiones versionadas y receipt/ack propios. No copiar vaciado destructivo ni un Stop genérico a todos los runtimes. La entrega a callers al retomar sigue por verificar |
| R-03b492bcef1e:28–55 | Recordar revisiones abiertas al iniciar. La lista es global, no filtra por proyecto y muestra solo cinco sin declarar cuántas quedan fuera | Destino: contexto y retoma existentes, selección exacta de iniciativa/proyecto, topes con omisiones visibles y lectura sin consumir/aprobar feedback. Diseño e integración del caller pendientes |

Nuestro servicio de revisión valida estados pendiente/entregada/consumida, IDs de decisión
y entrega, versión y ámbito; resultados por comentario y verificación declarada se conservan
por separado (`plan-review.py`:215–248,321–409). Escribir un ack no acredita que un modelo
haya atendido el comentario. El hook de contexto actual compone journal, índice, roadmap
y memoria técnica (`session-context.sh`:1–315); estos mecanismos no prueban retoma de una
revisión humana. No se añade una segunda cola ni se altera un gate de aprobación.

El cambio del medidor tiene RED real de interleaving (temporal consumido; WinError 2),
74 pruebas unitarias y la suite del dashboard aprobadas. Dos controles nativos Windows
comprobaron recuperación al liberar un bloqueo propio y conservación del snapshot cuando
persiste; 100 escrituras adicionales pasaron. Esto prueba esos casos y el error manejado,
sin identificar al causante de los rechazos históricos. Cobertura y límites en
[estado de validación](../testing/final-qa25-status.md). Revisión independiente y QA conjunta
siguen pendientes; no hay integración global ni catálogo de skills ampliado.

## Continuación: consulta integrada en candidata, sin aceptación global

El checkpoint anterior dejó el caller pendiente. La candidata posterior incorpora
`list_reminders` en el dueño común y su consulta en `/work-resume` y progreso de
sesión. Filtra por proyecto e iniciativa seleccionados, preserva versiones y
estados y declara omisiones. No drena una cola ni entrega/consume decisiones.
La consulta de sesión tiene un plazo cooperativo de 0,75 segundos; la manual, tres.
Su eficacia nativa y la atención del modelo siguen sin acreditarse. Las pruebas
y fallos preservados constan en el [estado de QA](../testing/final-qa25-status.md).
La integración es candidata; revisión independiente y QA conjunta siguen abiertas.

## Continuación: memoria de sesión, costes y checkpoints

Lectura estática de los cuerpos y hashes de la revisión fijada. El siguiente
checkpoint de lectura conserva los registros anteriores y alcanza 41 cuerpos
completos y uno parcial; quedan nueve recursos inmediatos y diez descendientes
por revisar. El cierre transitivo global sigue abierto. Descargar un fichero no
cuenta como leerlo; leerlo no acredita su ejecución ni eficacia en un host.

| Recursos | Comportamiento comprobado | Decisión nativa |
|---|---|---|
| R-aa073f6b406b, R-7d9940f71285, R-d8dbc333fffb | Costes por sesión, checkpoint incremental y publicación mediante temporal exclusivo. El checkpoint muestrea tres ventanas del prefijo; el renombrado no coordina escritores. Precios fijos y coste de caché no prueban facturación real | Conservar ventanas/fuentes/revisiones explícitas, persistencia fallida visible y deduplicación propias. No importar precios fijos, logs globales ni una garantía de concurrencia que el helper no proporciona |
| R-076e8356b72b, R-e004ae305ac0, R-4f8126d33200 | Directorios de datos globales, IDs abreviados y comprobación de contención por ancestro real existente. Varias operaciones de lectura/recorrido no tienen topes de bytes o elementos | Conservar memoria canónica por proyecto, IDs completos, lectura local acotada y los adaptadores actuales. No crear otra raíz de memoria por proveedor |
| R-2a754bdba132, R-30aa29857c62, R-f33c48fbb392 | Stop actualiza un resumen tras cada respuesta. Cada 50 mensajes o por presión de contexto puede ejecutar Claude hasta 90 segundos. Lee el transcript completo antes de recortar turnos; no redacta secretos en ese helper | Conservar captura rápida, outbox y replay. Publicar primero la entrada determinista; el resumen por IA sigue opt-in, con redacción, datos delimitados y aislamiento contra recursión. Ningún modelo se ejecuta en la captura de cierre |
| R-b18149810e30 | Cuenta mensajes y sugiere evaluar patrones; no extrae patrones ni crea skills automáticamente | Mantener propuesta de conocimiento y aprobación humana. No presentar una sugerencia como aprendizaje ejecutado |
| R-053f74dadb4a, R-b9a585599001 | Checkpoint antes de compactar y recordatorio por tokens/llamadas. El resumen vuelve a usar el helper de 90 segundos; los contadores temporales no coordinan concurrencia y su limpieza no tiene tope de elementos | Mantener /work-save y /work-resume en los límites del flujo. No registrar eventos de compactación de otros hosts sin contrato nativo verificado ni introducir contadores globales |
| R-115c4c2bd99f, R-c340af711e18, R-68dc6b78fcc7 | Avisos de build/PR y logs de comandos. El aviso de build no comprueba éxito ni inicia el análisis anunciado; el logger conserva texto de comandos con redacción parcial | Mantener evidencia de QA y entrega del workflow, actividad tipada sin comandos completos y medidor propio. No duplicar hooks que atribuyen trabajo o éxito sin ejecución |
| R-591e0ebb2a34, R-13dd1e32403b, R-07b6abd1ac04, R-261622b88023 | Aviso de nombres de documentos, limpieza de observador y bootstraps de ciclo de vida. Algunos descendientes aún están pendientes | Mantener convenciones documentales, cierre durable sin observador y presupuestos por host. No afirmar cierre de estas cadenas hasta terminar los descendientes |

La revisión del helper atómico y de la cadena de resumen está cerrada para esos
recursos concretos; la comparación de todos los hooks sigue abierta. Las skills
continúan aplazadas. Esta decisión conserva la memoria local como autoridad:
los servicios externos añaden recuperación documental o estructural según su
configuración, sin convertir sus resultados en aprobación ni reemplazar el
journal del proyecto. No se ha ejecutado código del origen en estas lecturas.