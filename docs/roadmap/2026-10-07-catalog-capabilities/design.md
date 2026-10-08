# Diseño por bloques operativos

## Bloque 1: integridad del checkpoint de sesión

Dirección aceptada en [operational-priorities.md](operational-priorities.md).
Lectura de `journal.py capture`, `_journal_activo`, `_rotar` y sus tests:
la captura solo consulta el booleano de `journal`, mientras el cierre admite
también `{activo: false}`; la rotación abre el log original en modo `wb`.

Elegimos reutilizar la puerta `_journal_activo` y rotar mediante temporal
privado en el mismo directorio, flush/fsync y reemplazo atómico. Leer solo
la cola necesaria evita cargar un log sobredimensionado completo. Se conserva
la retención de últimos turnos, las líneas JSON completas y el formato actual.

Alternativas: mantener la escritura directa conserva el riesgo de pérdida
ante interrupción; cambiar todo el almacenamiento a eventos individuales
exige migración y consumidores nuevos sin necesidad para estos dos defectos.
La corrección acotada conserva el pipeline capture → outbox → replay.

Criterios del bloque:

1. `journal: false` y `{activo: false}` impiden guardar turnos y crear marcas;
   `{activo: true}` conserva la captura y `<private>` sigue siendo opt-out.
2. Un fallo de fsync/reemplazo durante rotación conserva el log anterior y
   elimina temporales de esta invocación; el hook mantiene exit 0.
3. Una rotación correcta conserva registros JSON recientes, permisos privados
   y tamaño acotado, leyendo solo la cola requerida.
4. Los consumidores capture-end/replay/recover conservan su formato y pasan
   regresiones. Las rutas relativas de salida CLI usan `/` también en Windows;
   no se anuncian carga/despacho nativos por esas pruebas.
5. Documentación ES/EN, ledger y exports coherentes; revisión independiente
   antes de publicar el bloque en la rama autorizada.

Un corte brusco antes del replace puede dejar un temporal privado ignorado;
el original permanece disponible. La atomicidad no constituye una garantía
de persistencia ante pérdida eléctrica en todos los filesystems.
Los contratos/dispatch pendientes de Claude, Codex y OpenCode V2 siguen en
T-02/T-09 y se entregan en bloques posteriores. Este bloque corrige el
servicio compartido que usan los launchers, sin activar grafos ni skills nuevas.

La regresión ampliada reprodujo una incompatibilidad de la CLI Windows:
`write` devuelve `docs\knowledge\journal\…` y los consumidores/tests esperan
`docs/knowledge/journal/…`. Se normalizan las salidas relativas de `write`
e `index`; las rutas internas de filesystem mantienen la forma nativa.

También se reprodujeron dos reclamaciones exitosas del mismo envelope en
Windows: `os.replace` concurrente no asegura un único consumidor. Se añade
un cerrojo de SO no bloqueante `.claim.lock` alrededor del barrido y todos
los pasos de reclamación (msvcrt en Windows, flock en POSIX). El proceso
libera el cerrojo al terminar o morir; la existencia del fichero no indica
propiedad. Sin cerrojo disponible no se mueve el item: sigue pendiente.
No se modifica la materialización ni el TTL de recuperación existentes.
La aceptación del bloque exige un único ganador bajo contención repetida.

## Bloque 2: transporte nativo OpenCode V2

El runtime rechaza el export V1 existente (contracts.md/runtime-probes.json).
El API oficial V2 requiere una definición default con id/setup. La lectura
dirigida del adaptador del corpus muestra un objeto V1, avisos post-tool/idle y
una búsqueda de CLAUDE.md que no acredita su carga. No se copia ni ejecuta.

Se reemplaza por tool execute.after (input/status), session prompt (checkpoint)
y session context (replay y fuentes locales), reutilizando el servicio compartido.
El prompt se captura antes de la admisión, como UserPromptSubmit: es una petición,
no evidencia de ejecución ni decisión aprobada. La prueba nativa revela que V2
emite session.execution.succeeded/failed/interrupted como transiciones terminales,
sin location en el stream local del plugin. Se captura el envelope con esos
eventos; status idle/session.idle se toleran si el runtime los entrega. La ubicación
real se obtiene siempre con session.get antes de actuar; una location explícita
incompatible se descarta antes de consultar la sesión.

La distribución usa index.js/package.json y registro de directorio en plugins.
El instalador preserva permisos/instrucciones del usuario y deja de añadir un
índice mediante instructions (V2 no lo carga). Se retiran solo el adaptador
anterior conocido y apuntes propios; una copia modificada se conserva y avisa.
Panel, exports y docs siguen el entrypoint nuevo. Se valida con 2.0.12, sin
prometer V1 ni versiones no probadas. Guardia por identidad y presupuesto
Claude/Codex siguen abiertos; estos callbacks informativos no imponen deny.

Descartado: mantener el objeto V1 que falla nativamente, confundir normalización
de config con traducción de hooks o crear otro escritor de memoria.

Criterios: carga/ejecución nativas active de la distribución instalada; solo
post-tool exitoso informa; aislamiento por proyecto/workspace; captura con
redacción/opt-out y contexto efímero ≤10.000 caracteres que preserva instrucciones;
cleanup aborta suscripción/procesos; fallos informativos degradan; installer,
export, panel y docs ES/EN coherentes, migración/idempotencia probadas, diff ≥90%
y revisión independiente antes de push.

La revisión del transporte añade tres garantías: los avisos usan los targets
normalizados del resultado nativo; timeout/exceso de salida no resuelven antes
de cerrar el launcher; y las continuaciones sin cambios reutilizan el contexto.
La caché es efímera y tiene una sola entrada por instancia (sesión, texto de
10.000 caracteres y firma de metadatos), con TTL de 30 segundos. Se invalida
ante prompts propios, herramientas completadas que pueden modificar estado y
transiciones terminales. Las herramientas de lectura conocidas permiten reutilizar.
Antes de reutilizar se verifica session.get y una firma de configuración,
estado de uso, logs/cola locales, roadmap y conocimiento. No se leen cuerpos
de memoria para la firma. El recorrido tiene límites de 4.096 entradas,
ocho niveles y 250 ms; enlaces, errores o límites impiden cachear. Una cola
personalizada también desactiva la caché. La composición sigue siendo del
servicio compartido; los cambios concurrentes durante ella impiden guardar
su resultado. La caducidad cubre cambios del bundle instalado y recuperación
de huérfanas que dependen del tiempo, sin afirmar actualización instantánea.

En movimientos, applied[].target contiene solo el destino. Se incluye también
la cabecera de origen absoluto de FileDiff.Info.patch producido por el runtime,
para informar la eliminación del documento original cuando sale de docs/.
Los paths confirmados del resultado y los orígenes del diff nativo se deduplican;
el fallback de entrada se conserva para herramientas compatibles sin output nativo.

## Bloque 3: identidad y guardias nativas por rol

La captura/lifetime e instalación se verificaron en el bloque anterior. Ahora
se conecta el evaluador existente guardrail-check.py al evento previo de
herramienta de cada runtime. No se infiere el rol de instrucciones, historial,
transcripts ni campos del input controlados por el modelo.

Las fuentes fijadas exponen identidad nativa en los tres runtimes: agent_type
en Claude y Codex, y agent en OpenCode V2. En Claude un agente de plugin tiene
ID custom-agents:<rol>. Codex y OpenCode exponen el nombre sin procedencia de
la configuración seleccionada. Claude también admite overrides de un ID
completo mediante --agents: el namespace por sí solo no prueba el origen.

Decisión técnica dentro de la autorización del usuario: usar
custom-agents-<rol> como ID nativo en Codex/OpenCode, conservando el rol
canónico agents/<rol>.md. Es una convención del plugin para evitar colisiones,
no un namespace oficial adicional. Mapa generado único de IDs por runtime,
consumido por dispatcher y exports/contexto; no se crean roles duplicados.
Solo los IDs exactos de implementer y architect activan su política actual.
Planner, principal sin identidad y agentes con otros IDs mantienen el flujo
normal de permisos. Definir expresamente el mismo ID propio personaliza ese
rol y conserva su política; no se afirma que su prompt pertenezca al plugin.
Instalación y migración deben preservar o rechazar conflictos de archivos y
bindings del consumidor. Los exports bare anteriores se retiran solo si son
copias propias sin cambios; los personalizados se conservan con diagnóstico.

Alternativas descartadas: aplicar política al nombre bare puede restringir
un agente ajeno; sandbox_mode por agente Codex no prueba aislamiento frente
a overrides heredados; claimed role en la petición es controlado por el modelo.
Un segundo evaluador por runtime duplicaría política y produciría divergencias.

Claude necesita PreToolUse en hooks del plugin: el frontmatter de sus agentes
no impone hooks en ese modo. El dispatcher decide únicamente tras reconocer
un ID protegido exacto. Sigue prohibido aplicar deny indiscriminado a todos
los agentes. Codex usa su evento nativo previo y contrato JSON. OpenCode puede
rechazar execute.before: la prueba de Promise API bloquea antes de escribir
y la sesión continúa tras recibir el error. No se correlaciona decisión con
permission.evaluate mediante una tabla de toolcall IDs: CodeMode reutiliza
el ID externo en llamadas anidadas y esa tabla podría confundir decisiones.

Criterios de entrega del bloque:

1. Mapa/exports, catálogo y delegación usan IDs propios coherentemente;
   la migración conserva agentes modificados y bindings del usuario.
2. Selección únicamente desde metadata nativa y argumento de runtime fijo;
   claimed role en tool_input/prompt no selecciona la política.
3. Deny/allow nativos para implementer y architect; controles planner,
   principal y agente personalizado acreditan ausencia de interferencia.
4. Normalización previa de targets originales/destinos y herramientas de
   escritura observadas. No se confunde guardrail con aprobación normal ni
   se anuncia una frontera universal de sandbox para cualquier herramienta.
5. Evaluador único, degradación visible, opt-out conservado; RED/GREEN,
   cobertura del diff >=90%, revisión independiente, docs ES/EN y exports
   coherentes antes del push de la implementación.

Las pruebas de mecanismo usan dispatchers privados y no acreditan todavía
que la distribución instalada los conecte. El bypass de confianza de una
fixture propia no prueba confianza persistida del consumidor. No se activa
ningún backend de memoria ni se incorpora una skill en este bloque.

## Bloque 4: conexión de guardias e instalación de IDs propios

El bloque local sobre 8b51edd conecta el mapa generado, normalizador y evaluador
central con PreToolUse Claude/Codex y `tool.execute.before` OpenCode V2. Usa solo
metadata de identidad del runtime. Sin ID propio reconocido no consulta la
configuración ni Git y continúa. No toma decisiones de guardia desde el input,
texto del prompt, nombre de sesión ni identidad del agente padre. Cada operación
se evalúa por separado, aun cuando un runtime reutilice el ID externo de llamada.

Los IDs con prefijo reducen colisiones; no prueban procedencia del prompt. Una
redefinición exacta continúa siendo ese rol para el runtime. El instalador
comprueba las capas conocidas, conserva agentes ajenos/modificados, referencias
ambiguas y enlaces, y declara estado incompleto ante conflictos. La retirada de
los exports anteriores exige manifiesto propio, hash publicado y un límite Git
regular sin bindings. Las copias globales y worktrees ambiguos se conservan.

El dispatcher traduce todas las mutaciones de los esquemas soportados, incluyendo
origen/destino de patch. La excepción de enlaces de diseño se evalúa por hunk;
move/delete se consideran mutaciones completas. No se pretende inspeccionar
toda escritura indirecta desde shell/MCP. Input incompleto, superior a 64 KiB,
herramientas desconocidas o fallos internos mantienen los permisos del runtime
con diagnóstico cuando corresponda. El opt-out explícito se conserva.

La decisión de ubicación aceptada en el intento 5 reemplaza la exclusividad de
frontmatter de ADR-007, manteniendo el alcance por rol (ADR-023 en memoria local).
Las copias locales Claude conservan sus wrappers; los agentes de plugin no
ejecutan ese campo. Las instrucciones expresan reglas del rol y requisitos
reales de carga, sin prometer una frontera universal de permisos.

Las primeras pruebas de la distribución de 5 s detectaron que el runtime
descarta `deny` si el proceso tarda en cerrar. Un control aislado reproduce
6.261 ms y un diagnóstico separado mide 802 ms: arranque/cleanup Windows
varían, sin evidencia de un cuelgue permanente. Se mantiene la contención y
el presupuesto interno de 4,5 s; el registro previo Claude/Codex pasa a 10 s y
OpenCode a 10,5 s incluyendo arranque/cierre. SessionEnd Codex sigue limitado a
3 s. La captura escrita antes del cierre y el aviso del runtime se comprueban
por separado. Se conservan los fallos como evidencia. Las fichas de
[ejecución nativa](native-role-integration-evidence.json) y
[QA](native-role-qa-evidence.json) registran cohortes con sus hashes, correcciones
de parser y reintentos intermitentes por identidad; no atribuyen la matriz
histórica completa a la fuente final. La aceptación de este bloque se registra
en el ledger; la eficacia SessionEnd y aceptación de memoria siguen abiertas.

## Bloque 5: acciones prioritarias del diagnóstico

La comparación completa de C030 y su motor confirma el valor de ordenar los
arreglos de un diagnóstico reproducible. Sus puntuaciones por cantidad de
piezas, cadenas presentes y supuesta latencia no acreditan calidad ni ejecución;
se descartan. El destino es `/doctor`, dueño actual de las comprobaciones, con
`doctor.py` como única fuente de filas, resumen y acciones. No se crea otro
comando, escritor de estado ni skill. Las decisiones técnicas ya están delegadas.

El JSON añade `acciones_prioritarias` con `{total, limite, acciones}`. `total`
cuenta filas `error`/`aviso` con arreglo no vacío; `limite` es tres. Cada acción
conserva bloque, ordinal de fila desde uno, estado, comprobación, detalle y
arreglo exactos. Prioridad: error antes de aviso; desempate por orden canónico
de bloque y fila. Dos problemas distintos con el mismo remedio siguen siendo
dos hallazgos. Las filas informativas o sin arreglo no originan recomendaciones.

Markdown muestra la misma selección y su total. Todas las tablas, filas de
cuatro campos, conteos y exit permanecen. No se ejecuta ningún arreglo ni se
deduce una ruta de la prosa. La ausencia de errores se expresa respecto a las
comprobaciones realizadas, sin anunciar salud global o ejecución de hooks.
`/setup` debe describir la excepción de red ya existente para capacidades
activadas, en vez de prometer un diagnóstico siempre sin red.

Aceptación del bloque: RED/GREEN de prioridad, empate, truncamiento, ausencia
de remedios, problemas distintos con el mismo remedio, texto con pipes/newlines,
identidad JSON/Markdown y preservación de filas/exit. Prueba de CLI en proyecto
y home propios, sin cambios en configuración; no diagnosticar el workspace real
porque contiene settings del usuario. QA de la suite propia en fixtures, diff
>=90%, docs ES/EN, exports, revisión independiente y push comprobado. T-05/T-11
globales y la comparación de otros comandos siguen abiertas.

## Bloque 6: hooks declarados por runtime en el panel

La comparación operativa verifica el valor de metadatos por componente, estados
desconocidos explícitos y navegación accesible. El lector actual ignora runtime
para hooks, pierde los launchers con argumento de runtime y muestra el presupuesto
Claude en la vista Codex. Se corrige sobre plugin-panel, conservando el HTML
autónomo, lectores canónicos y el registro de extensiones existente.

Claude se obtiene de `hooks/hooks.json`; Codex, de `interop/codex/hooks.json`.
OpenCode usa un catálogo JSON literal acotado dentro de su adapter, delimitado
por centinelas exactos. Ese mismo catálogo define bindings, handlers y presupuestos
que consume el adapter; los callbacks y transformaciones permanecen en JavaScript.
El panel valida y lee exclusivamente el JSON, sin importar ni ejecutar JavaScript
del bundle inspeccionado. No se crea un sidecar que duplique constantes sin uso.
El generador distribuye el adapter con su contrato integrado.

Cada handler declara runtime, evento/canal nativo, fuente/localizador, ID,
propósito, activación, comportamiento informativo/guardia, identidad del mapa
propio cuando corresponda y timeout con procedencia. Booleanos, valores no finitos
o no positivos no son timeouts válidos. Un timeout ausente se muestra como no
declarado; no se inventa el default del runtime. La guardia muestra el alcance
real y no acredita procedencia del prompt ni sandbox universal.

La vista `all` agrupa por runtime/evento y cuenta handlers y grupos explícitos;
un runtime concreto inspecciona solo su declaración. Fuente inválida/ausente se
presenta como desconocida o inventario parcial, sin sustituirla por Claude ni
confundir ausencia de evidencia con ausencia de hooks. Carga y ejecución siguen
sin verificar; no se invoca doctor, health/verify ni un servidor al generar HTML.

UI: filtro por runtime de hooks, funciones y presupuestos legibles, fuentes
accesibles también en móvil, foco/teclado, hashes/IDs inexistentes seguros,
historial y etapas existentes conservados. Probar metadatos hostiles, lectura
acotada, sources enlazadas, drift del contrato frente a callbacks, agrupación y
selección entre entornos. El refactor de bindings se valida con la suite del
adapter y un delta OpenCode nativo aislado, sin activar cachés del consumidor.
La proyección futura de doctor será opt-in; no se añade analítica sintética,
otro almacén de tareas ni nuevas skills en este bloque.

## Bloque 7: diagnóstico del cierre y contrato de memoria vigente

Se retoma desde `470e92e` tras la petición de continuar. El fallo SessionEnd
Codex se investiga con reproducción, aislamiento y una hipótesis probada antes
de cambiar producción. El límite nativo de tres segundos incluye el arranque
del comando; un negocio rápido no acredita un cierre completo. Las pruebas
usan proyectos, homes y cachés privados, sin modificar la instalación real.
No se aumenta el timeout por encima del contrato nativo.

La reconciliación documental distingue dos adaptadores ya existentes: Kwipu
proyecta documentos y verifica su publicación; Graphiti también permite lectura
enrutada explícita en modo `read`, condicionada por salud, verificación completa
y permisos del proyecto. `off`/`shadow` no conceden lectura. La memoria local
sigue siendo canónica y ofrece respaldo. Los proveedores declarados orientan
al servidor: no acreditan su configuración ni el coste de extracción.

Alcance: T-02/T-07/T-09/T-14/T-15, diagnóstico privado con evidencia pública
sin datos del consumidor, mapa de la skill existente, contrato del adaptador,
índice bilingüe y changelogs. No se añaden skills, backends ni conexiones. Si la
hipótesis de cierre no queda demostrada, se conserva el fallo y sus límites;
no se transforma una investigación parcial en un fix. Prosa: TDD n/a. Las
pruebas de contratos existentes, lint, exports y revisión independiente deben
validar la reconciliación antes de publicarla.

Los diagramas también distinguen los presupuestos de cada runtime y corrigen
la referencia antigua a guardias solo por frontmatter: la distribución ya usa
identidades propias exactas y dispatcher global. No cambia la política.

La primera tanda dirigida expone fixtures de consulta incompatibles con Windows
y un miembro del grafo esperado fuera de la vista compacta. El contraste con
la base reproduce esos tres fallos; una fixture LF corrige los dos `--show`.
Se fija LF explícito y se verifica la relación completa en JSON, conservando
el tope humano y su marcador de truncamiento. No cambia el lector de memoria.
La QA final usa una copia de fuentes sin bytecode generado; el scanner de
seguridad mantiene su política estricta sobre todos los archivos inspeccionados.

## Bloque 8: cierre bajo carga y autoridad de recuperación local

Base `b8e6192`. El objetivo vuelve a activo; nuevas skills siguen aplazadas.
Se mantienen dos investigaciones independientes antes de modificar producción:
diagnóstico causal de SessionEnd y auditoría de recuperación/governance local.

El contraste de cierre usa dos fixtures frescas propias con idénticos hooks
completos, observers, intérprete, instrumentación y presupuesto nativo de 3 s.
Una completa un turno raíz; otra añade dos hijos nativos con una mutación
protegida y una permitida por rol. La instrumentación se separa del atajo del
stub que antes respondía directamente sin crear hijos. Se miden arranque del
Node, bootstrap, captura, cleanup, observer y envelope antes de salida natural.
Un éxito no acredita resolver el fallo histórico. Un par ambiguo admite solo
un par adicional en orden inverso; se conservan todos los resultados.

La revisión de memoria contrasta autoridad de `approved/`, documentos curados
ADR/GOT/LES, recuperación local y proyecciones, con fuentes/tests exactos.
No activa backend ni publica o promociona propuestas. Cualquier corrección
necesita diseño de autoridad y tests RED antes de tocar el lector. La auditoría
de comandos en paralelo delimita selección/retoma sin añadir otro almacén.

### Recuperación aprobada: decisión de implementación

La recuperación local incorporará `approved/` mediante un lector compartido
sin capacidad de red. Se extraen las reglas locales de taxonomía y el lector
aprobado de sus validadores actuales; no se copian parsers ni se importa el
validador de servicios desde hooks. Schema/index/sync conservan validación
completa de backends. Una configuración de servicio inválida no invalida la
lectura Markdown local; una taxonomía local o corpus aprobado inválido sí
degrada ese corpus con motivo explícito, conservando lectura legada válida.

Las entradas approved conservan ID completo, versión, estado, evidencia y
ruta canónica en query/show/related y fallback. Aciertos/related llevan versión
de conocimiento; --show mantiene `version: 1` del envelope y añade
`knowledge_version`. Caché y lectura plana tienen los mismos resultados;
cambios de taxonomía o contenido invalidan la caché. No se leen candidatos ni
rutas que escapen a las carpetas aprobadas declaradas. Colisiones de ID no
eligen el primer archivo: se diagnostican, y show/related rechazan ambigüedad.

No se migra memoria existente ni se cambia la política de promoción. Indexar
forma/carpeta/estado no demuestra que una aprobación humana o semántica ocurrió.
El límite entre propuestas, validación legada y escritura del Curator sigue
como auditoría de gobierno pendiente. La extracción incluye distribución y
registro de copias; tests RED preceden a producción y gate de diff ≥90 %.
