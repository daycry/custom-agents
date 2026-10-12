# Seguimiento operativo y acciones del panel

Petición del usuario del 2026-10-09: comparar el seguimiento de agentes y la
interacción del control panel para adaptar sus funciones útiles. La lectura
se fija en `ef648e01899ba3e8dc6371642deaaf64b4477775`, revalidada por HTTP.
[Evidencia por recurso](panel-activity-reading-evidence.json): hashes y rangos,
sin ejecutar origen, abrir bases de datos ni consultar datos del consumidor.
Los nombres y URLs de origen permanecen en el mapa privado.

## Qué está implementado

El catálogo y el panel operativo son superficies distintas. R-09d91020bb19
sirve snapshots, vista operativa, eventos y acciones; R-4d520fb19258 refresca
el panel principal cada 15 segundos. La vista operativa usa cinco segundos,
filtra y presenta sesiones, agrupaciones y avisos. Las peticiones tienen
plazo y control de solapamiento; la pestaña oculta suspende el refresco.
Un error conserva la fecha del dato anterior, en vez de hacerlo pasar por actual.

Las sesiones proceden de un almacén persistente alimentado por un runner.
El proceso gestionado aporta PID, stdout/stderr, heartbeat y resultado de
salida. Se ejecutan CLIs de Claude, Codex u OpenCode. Registrar ese proceso
no identifica automáticamente los subagentes internos ni descubre todos los
agentes de otras sesiones. La UI principal muestra tarea, estado y actualización,
sin publicar el stream completo de salida. R-87f94b578cce y R-1d2b20d8c957
delimitan esta diferencia entre una sesión gestionada y actividad nativa.

R-c01714e02ad5 define la vista operativa como observacional: no dirige, pausa
ni bloquea agentes. El servidor revisado no ofrece endpoints para iniciar,
pausar o detener agentes. Sí ejecuta acciones acotadas de sincronización,
recuperación y reconstrucción de memoria, y modifica la asignación y columna
de tareas. Mover o reclamar una tarea no demuestra que haya comenzado su ejecución.

El diseño de flotas permanece en borrador y no se cuenta como entrega. Los
normalizadores de métricas que rellenan valores ausentes con cero tampoco
demuestran consumo, salud ni eficacia. La comprobación de PID no Unix del
daemon requiere contraste de plataforma; no se ha reproducido ese comportamiento.

## Comparación y decisión propia

| Función | Estado propio | Destino |
|---|---|---|
| Catálogo, navegación, filtros, fuentes | Entregado; diagnóstico explícito en revisión | Conservar plugin-panel |
| Datos que cambian mientras está abierto | Modo local con polling y frescura en el código propio; aceptación visual pendiente | Conservar refresco acotado y pausa de pestaña oculta |
| Tareas y fases | Ledger canónico y parser existentes | Proyección de lectura; ninguna base nueva de tareas |
| Sesiones históricas | Journal y selector acotado existentes | Selección explícita; no confundir historial con proceso vivo |
| Agentes y herramientas observados | Sin productor operativo persistente | Contrato opt-in común y adaptadores de los tres runtimes |
| Cronología, búsqueda y detalle | Falta vista operativa | Presentar datos redactados, origen y última observación |
| Acciones sobre tareas y memoria | Dueños canónicos fuera del panel | Conectar acciones concretas mediante esos dueños, con conflicto y auditoría |
| Métricas de ejecución | Sin fuente operativa compatible | Mostrar sin medición; no fabricar ceros o tasas |

La secuencia elegida conserva una sola fuente por responsabilidad: servidor
local de lectura y progreso primero; observación por runtime después; acciones
mutables al tener un contrato que preserve las puertas del workflow. Interactivo
describe navegación y acciones disponibles; no se utilizará como sinónimo de
control total de agentes. Esta decisión amplía el alcance operativo de T-13,
sin declarar esas funciones implementadas ni cerrar la iniciativa.

## Fuentes propias y límites nativos

`progress-report.py` permite resumir texto del ledger sin volver a abrirlo;
`local-read.py` aporta límites y rechazo de redirecciones. El selector de
journal ofrece historial seleccionado y redactado. Ninguno prueba que un
agente esté ejecutándose. `subagent-progress.sh` descarta el payload y vuelve
a consultar el ledger; el launcher actual no persiste observaciones.

Los contratos nativos permiten ampliar captura: inicio/fin de respuesta de
subagente, identidad de llamada y límites de turno en Claude/Codex; callbacks
y stream con verificación de ubicación en OpenCode V2. Un fin de respuesta
no garantiza destrucción del agente. Un inicio antiguo sin cierre deja estado
desconocido, nunca una etiqueta indefinida de «trabajando».

No se publica el envelope del journal: contiene rutas privadas. La observación
operativa requiere un opt-in propio, sin reutilizar como permiso la captura
de memoria. El contrato mínimo excluye prompts, argumentos, comandos, respuestas,
errores libres, transcripciones y razonamiento. Probar nativamente productores,
concurrencia, retención, degradación y lectura del panel sigue pendiente.

## Revisión visual de planes: contraste ampliado del 2026-10-10

La revisión de planes es un circuito distinto de la vista operativa y su runner.
Se contrastaron 15 funciones y 47 recursos: 44 cuerpos completos y tres lecturas
dirigidas declaradas. ROOT verificó los cinco artefactos del informe, hashes de
los 47 recursos y mapas previos. Esta lectura no ejecuta el panel, código de
referencia ni agentes; V01–V08 conservan su aceptación pendiente.

El dueño propio `plan-review.py` liga comentarios y decisiones a raw/view,
puerta y revisión, controla conflictos con CAS y reentrega el mismo delivery
hasta ack. Se conserva ese contrato. Drenar feedback al responder una petición
puede perder su reentrega si el consumidor se desconecta; una respuesta libre
posterior tampoco demuestra que cada comentario haya sido atendido.

| Función | Decisión propia | Aceptación que falta |
|---|---|---|
| Guardar comentario y sellar decisión | Conservar borrador versionado y el dueño durable | Interacción real, reinicio y conflicto sin perder el borrador |
| Entregar y consumir | Conservar receive/ack y sus IDs; consumo no equivale a atención | Callers reales de Claude, Codex y OpenCode |
| Responder a un comentario | Añadir resultado ligado a comentario, decisión, delivery y versión en el mismo dueño | Schema cerrado, CAS, retry, corrupción y respuesta tardía sin mezclar versiones |
| Mostrar actividad | Metadatos explícitos con procedencia y caducidad; sin señal vigente mostrar desconocido | Opt-in propio, identidad/lease y productores reales de los tres runtimes |
| Actualizar contenido | Mantener invalidación por hash y recarga explícita | Preservar foco y feedback ante cambios del plan |
| Transporte vivo | Conservar polling de 5 s, timeout de 4 s y pausa oculta | Errores y recuperación visibles; no mostrar datos antiguos como actuales |
| Presentación | Texto seguro, foco, controles accesibles y detalle legible | Navegador escritorio/móvil/teclado; captura no acredita interacción |

El servidor HTTP propio atiende solicitudes en serie. Mantener SSE o long-poll
abierto en ese handler bloquearía las otras solicitudes. Una futura adopción de
push exige concurrencia acotada, cierre, lectores lentos, replay y presupuesto
agregado; no justifica otro daemon para evitar ese contrato.

La respuesta por comentario tendrá un vocabulario que distinga respuesta/acción
declarada de resultado verificado. Ack no producirá automáticamente un estado
«atendido». La observación de actividad tendrá otro dueño por responsabilidad,
sin almacenar prompts, transcripciones o comandos ni dirigir agentes desde el
panel. Es diseño por implementar; no incorpora skills ni otra base de tareas.
