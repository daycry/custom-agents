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

## Bloque 9: entrega explícita de decisiones de guardia

Base `f3e594a`. Se retoma el trabajo autorizado con nuevas skills aplazadas.
El fallo bajo carga sigue abierto: el replay directo deniega, pero un arranque
que agota el presupuesto puede entregar stdout vacío. Ese vacío actualmente
es indistinguible de una evaluación que permite continuar en Claude/Codex.

El launcher pedirá el resultado estructurado existente al evaluador en los
tres runtimes, con lectura acotada y validación antes de convertir al formato
nativo. Un `continue` válido sin diagnóstico sigue silencioso; un `deny`
completo conserva su bloqueo incluso si luego vence el presupuesto. Falta de
Python, spawn fallido, supervisión inválida, resultado ausente/incorrecto o
timeout sin decisión completa producen un diagnóstico estable sin payload:
`systemMessage` sin decisión en Claude/Codex y `continue` con diagnóstico en
OpenCode. No se inventan permisos `allow` ni `deny` durante la degradación.

Los presupuestos y el aislamiento de procesos no cambian. Una entrega visible
no acredita eficacia bajo carga ni confianza de instalación. La comparación
privada acotada de venv/base conserva todos los resultados y no modifica la
selección de Python sin evidencia causal. Tests RED preceden al código; se
verifican salida parcial, bloqueo completo seguido de timeout, salida excesiva,
errores de arranque y controles de permiso normal. Revisión independiente y QA
Windows/Linux antes de commit y push del bloque.

## Bloque 10: aislamiento de latencia y cierre de hooks

Base `e7160f4`. El usuario autoriza continuar con el punto de hooks bajo carga;
las nuevas skills y las demás fases siguen aplazadas. Se reproduce el flujo
raíz + implementer + architect con todos los eventos, instalación y HOME propios,
modelo sintético loopback sin credenciales y presupuestos sin modificar.

Cada proceso/módulo escribe una traza separada. Se conservan los resultados
nativos, escrituras protegidas/permitidas y el envelope anterior a la salida
natural. La instrumentación no acredita latencia del bundle sin instrumentos.
El contraste inicial permite dos cohortes: primero la réplica instrumentada
en el workspace; después, si sus etapas lo justifican, un control cambiando
únicamente el destino de las trazas y del observador a un TEMP privado.
Proyecto, HOME, cache, fuente, intérprete y presupuestos mantienen su política.

Los relojes se distinguen: la duración nativa incluye creación del shell; el
timeout nativo empieza después de crearlo. La entrada de `SystemExit` en el
supervisor tampoco acredita la terminación del proceso. Una respuesta completa,
un estado `completed` y una captura durable son evidencias distintas.

No se incrementan timeouts ni se selecciona Python base sin un contraste causal.
Una optimización de handlers que no correspondan al archivo editado necesita
tests RED y preservar el tratamiento de entradas desconocidas. Sólo se presenta
como solución de la latencia que las pruebas demuestren que resuelve.

### Guardia de rama antes del primer commit

El repositorio sintético tiene HEAD simbólico válido pero todavía sin commit.
`rev-parse --abbrev-ref HEAD` falla en ese estado: el lector pierde una rama
existente y omite la protección de main/master. La corrección mantiene la
consulta actual y, cuando falla sin agotar el presupuesto, consulta el HEAD
simbólico con el tiempo restante. No cambia el resultado de HEAD detached,
ni duplica el presupuesto, ni confunde ausencia de Git con una rama permitida.
Se validan main y feature sin commits en el evaluador compartido de los tres
runtimes. El detector y sus tests amplían el alcance de este bloque.

### Aplicabilidad de PostToolUse antes de arrancar dependencias

El launcher reconocerá rutas canónicas de Write/Edit/MultiEdit y la normalización
existente de apply_patch antes de seleccionar Python. Para payloads reconocidos,
cada handler conserva los mismos patrones y exclusiones de su script shell:
documentación, ledger y progreso. Si no hay ninguna ruta aplicable, termina sin
arrancar supervisor/Bash/Python. Payloads incompletos o desconocidos conservan
la ejecución anterior; no se añade una decisión de guardia en PostToolUse.
No se agregan los handlers ni se copian sus responsabilidades de negocio.
La optimización elimina procesos sin trabajo útil; no se presenta como prueba
de una causa única del timeout histórico.

### Resultado verificado y frontera de esta entrega

El diff resuelve lectura de rama sin commits y evita dependencias en handlers
PostToolUse reconocidos sin trabajo. La comparación instrumentada cambia sólo
el destino de las escrituras de trazas/observador: mejora la guardia raíz,
pero conserva latencia residual y no demuestra una causa única del timeout.
No justifica cambiar intérprete, presupuestos o política de limpieza.

QA Windows/Linux y aceptación nativa sin instrumentar quedan identificadas en
[evidencia de QA](hook-reliability-qa-evidence.json),
[diagnóstico](hook-load-diagnosis-evidence.json) y
[aceptación nativa](hook-native-acceptance-evidence.json). Codex ejercita raíz y
dos hijos; Claude, cinco procesos separados; OpenCode, siete casos directos
y cuatro raíces con un hijo cada una. Son fixtures con dispatch real y modelo
loopback, sin extrapolación a latencia universal ni soak test de TUI.

Codex y Claude observan captura raíz válida de SessionEnd antes de salida
natural. OpenCode captura al quedar execution/idle con servidor vivo; una
captura sigue temporal al observarse. Ese contrato no acredita SessionEnd
nativo de teardown, publicación canónica ni replay completo de ese caso.
La iniciativa y tareas globales permanecen abiertas para las fases restantes.

## Bloque 11: aceptación de publicación canónica

El observador privado del bloque 10 aceptaba JSON visible en `.tmp-*`. La
publicación atómica exige nombre `<event_id>.json`; el observador corregido
excluye temporales antes de abrirlos y contempla outbox/processing/done para
no confundir materialización diferida con ausencia. Comprueba schema/secuencia,
ID raíz y servidor vivo; no infiere salida de hooks hijos por la del servidor.

La [evidencia canónica](hook-canonical-capture-evidence.json) acredita siete
publicaciones de una nueva matriz OpenCode, manteniendo el histórico anterior
de seis canónicas/una temporal. Los 94 archivos distribuidos conservan hashes
actuales y el escritor mantiene flush → fsync → close → rename. Dos mecanismos
sintéticos explican cómo puede quedar un temporal completo: hard stop previo
al rename o sharing violation por lector Windows. La reproducción de ambos
no atribuye ninguno al caso histórico y no justifica alterar fsync/timeouts.

La recuperación del checkpoint anterior, sólo en una copia aislada, verifica
la ruta existente `recuperado_sin_cierre`; no promociona JSON temporal ni
afirma cierre observado. La nueva cohorte verifica publicación canónica durante
execution/idle, no SessionEnd nativo de teardown, replay completo de todas
las sesiones o fiabilidad universal de carga/TUI. La corrección es del criterio
privado de validación; producción permanece idéntica al bloque entregado.

## Bloque 12: conservar la verificación de commits

`agent-kits/shared/guardrail-check.py` amplía la regla existente `git`.
El dispatcher conserva los IDs propios exactos de `implementer` y `architect`
en Claude, Codex y OpenCode. No cambia los permisos de agentes ajenos ni
añade registros, agentes, skills o servicios. Configurar
`{"guardrails": {"git": false}}` en el proyecto conserva el opt-out.

El evaluador deniega `git commit` cuando sus flags efectivos desactivan
pre-commit y commit-msg mediante `--no-verify`/`-n`. Reconoce abreviaturas
unívocas y clusters cortos. Un `--verify` o `--no-no-verify` posterior restaura
la verificación. Consume argumentos de opciones, incluidos prefijos largos
unívocos, y respeta `--` antes de las rutas, por lo
que mensajes y pathspecs no se convierten en comandos. `--amend` por sí solo
no desactiva la verificación.

Un override explícito de `core.hooksPath` durante el commit también produce
deny, mediante `-c`, `--config-env` o configuración literal por entorno.
La regla no afirma que cada ruta alternativa desactive los hooks: exige
revisión explícita para cambiar la cadena de verificación del proyecto.
`GIT_CONFIG_COUNT` se interpreta con sus claves suministradas;
`GIT_CONFIG_PARAMETERS` se analiza como pares literales. El parser no recorre
un rango proporcional al contador ni ejecuta los valores.

La gramática consume asignaciones iniciales y wrappers `env`, `command` y
`exec`. `env -i`/`--ignore-environment` elimina los bindings heredados;
`env -u NAME`, `-uNAME` o `--unset=NAME` elimina la variable indicada.
`env -C DIR` y `--chdir=DIR` consumen el directorio del wrapper. `command -p`
y `exec -a NAME` conservan la detección del comando efectivo; `exec -c`
elimina el entorno heredado y `-l` conserva el comando. La comparación del
nombre base ignora mayúsculas y contempla nombres Windows con `.exe`.
Esa normalización también alcanza las comprobaciones Git destructivas existentes.

El scanner literal conserva comillas, comentarios y continuaciones escapadas.
Separa cada orden por sus operadores y saltos de línea fuera de comillas:
un flag de una orden posterior no restaura la verificación de la anterior.
Los wrappers consumen clusters soportados y valores cortos pegados, como
`exec -cl`, `env -iu NAME` y `env -C.`. Un fragmento final incompleto no
elimina las órdenes completas ya reconocidas.

La recursión existente de shell `-c` y `eval` conserva profundidad máxima 3
y propaga los bindings literales. El evaluador no expande variables ni
resuelve aliases; tampoco abre scripts ni consulta configuración Git externa.
El dispatcher reconoce la tool PowerShell, pero sus asignaciones y scripts
quedan fuera de la gramática literal. No acredita un sandbox ni cobertura
universal de shell/PowerShell. Los tests
positivos y negativos están en `agent-kits/shared/test_git_verification.py`.
El ledger registra QA, revisión y aceptación propias de este bloque; la
evidencia nativa de bloques anteriores no valida automáticamente esta regla.

## Bloque 13: retoma dirigida sobre las fuentes canónicas

Base `03e520b`. Se integra el criterio de selección explícita, procedencia y
estado vigente de [commands-session-continuity.md](comparisons/commands-session-continuity.md).
Journal conserva lectura, selección y citas históricas; progress conserva
el cálculo de progreso desde `tasks.md` y compone la vista. La fachada
`work-resume` ofrece esa vista bajo demanda, sin otra cadena ni almacén.

Un lector local compartido acota bytes antes de parsear y valida la raíz,
ancestros y archivo. Rechaza symlinks/junctions y tipos no regulares; acepta
placeholders cloud que no redirigen. Comprueba identidad antes de leer el
descriptor, conserva códigos de ausencia, acceso, formato y límite, y no
escribe ni ejecuta código del proyecto. Cada consumidor aplica su esquema.

El selector admite nombre de entrada, iniciativa, session_id y runtime exactos.
Una elección explícita ausente, inválida o ambigua no se sustituye por otra
sesión. La exploración tiene tope de archivos y bytes; una búsqueda incompleta
no acredita ausencia ni recencia global. Las entradas antiguas sin runtime
conservan ese dato desconocido y no satisfacen un filtro runtime explícito.
No se infiere runtime por ID ni fuente. Separar captura por runtime y cambiar
la clave de escritura requieren otro contrato; este lector no acredita ese cambio.

La resolución de iniciativa admite carpeta exacta o slug inequívoco bajo el
roadmap de la raíz elegida; con varias coincidencias presenta candidatos.
El progreso y tareas vigentes proceden del ledger actual. Journal aporta
fecha, sesión, fuente, cierre y citas, con saneamiento/redacción y topes de
salida. Un test citado no equivale a ejecutarlo hoy. No inventa campos de
fallos, bloqueos o próximo paso que el esquema no haya capturado.

La composición no llama al modo session actual, usage-meter, replay/recover,
Git, inferencia o backends. El caller puede continuar el trabajo autorizado
tras contrastar las fuentes; consultar la vista no concede autorización nueva.
Los consumidores dirigidos usan el selector común; la inyección automática
se adapta cuando conserva estos límites, sin convertir el hook completo
(que tiene replay previo) en una operación de sólo lectura.

## Bloque 14: diagnóstico explícito en el panel

Base publicada `2610a27`. La comparación de paneles identifica como criterio
útil conservar resultado, fuente, alcance y fecha; el agregado de readiness
externo permite avisos por comprobaciones omitidas y no acredita publicación.
No se traslada ese agregado ni el backend del control plane. El diagnóstico
propio sigue siendo responsabilidad de doctor, no del catálogo.

Doctor ofrecerá una proyección portable versionada bajo `--panel-json`, además
de sus salidas existentes. Un módulo puro compartido definirá la forma, la
identidad del alcance y sus límites. La proyección conserva fecha UTC de
comprobación, estados de filas por bloque público, referencias de hasta tres
acciones prioritarias y una recomendación de consultar doctor. No publica
rutas, detalles, arreglos libres, cuerpos ni valores de configuración. Los
resultados no se convierten en un score de salud o de readiness.
Las etiquetas son una allowlist exacta de 49 títulos públicos de doctor;
una etiqueta dinámica desconocida se muestra por su ordinal de fila. El panel
remite al bloque/fila de doctor para el detalle y arreglo concreto, conservando
ese dueño en vez de copiar datos privados o instrucciones de shell.

El panel consumirá únicamente un fichero indicado por `--diagnostics-report`;
no ejecutará doctor ni buscará informes automáticamente. Requiere proyecto
explícito y compara la clave derivada de su ruta absoluta normalizada, sin
afirmar identidad física del filesystem. No mostrará un informe de otro
alcance como diagnóstico local. Fuente SHA-256 y fecha identifican la
instantánea; no prueban autenticidad ni vigencia del estado actual.

Ausencia, lectura fallida, formato incompatible, alcance no ligado/diferente,
fecha futura y datos incompletos serán estados explícitos. Más de 24 horas
se etiquetará como antiguo, conservando la instantánea histórica; una fecha
reciente tampoco acredita estado vivo. JSON estricto, enums y números acotados,
topes de filas/bytes y lector local común preceden a la composición.

La sección Diagnóstico será accesible por menú, fragmento y teclado, con
filtro por severidad y acciones textuales; sin botones de ejecución. Fuentes
del inventario, hooks, carga y ejecución mantienen sus contratos independientes.
El catálogo sigue utilizable sin informe o con un informe rechazado.

Criterios antes de cerrar el bloque: productor portable y entrada opt-in
probados con fixtures propias; rechazo de metadatos/rutas hostiles y scope
incorrecto; límites y antigüedad explícitos; cero diagnóstico automático;
privacidad por allowlist; navegación/filtros/foco/móvil en Edge; revisión,
qa-gate, exports y documentación bilingüe. La iniciativa global sigue abierta.

## Siguiente bloque: panel operativo local

La petición del usuario amplía T-13 a seguimiento e interacción, comparados
en comparisons/panel-activity.md. El HTML autónomo sigue siendo el catálogo
portable; un modo operativo explícito servirá datos actualizados desde
127.0.0.1. No habrá servidor automático al cargar la skill ni red en hooks.

Se elige polling de cinco segundos, sin peticiones solapadas, suspendido en
pestañas ocultas, con refresh manual y fecha de la última respuesta aceptada.
Ante timeout o desconexión se conservará el dato anterior marcado como antiguo.
Se limitarán las rutas HTTP, métodos y tamaño de respuestas. Host/Origin y
acceso del navegador local requieren validación; no se servirá el árbol del
proyecto ni se aceptarán rutas o comandos libres de una petición.

La primera proyección reutilizará lectura acotada y parser canónico del ledger.
Estado, fase y asignación de tarea seguirán siendo declaraciones del ledger.
Historial de journal será opcional, explícito y redactado mediante el selector
existente. No se leerán logs de prompts, transcripciones ni envelopes completos.
Sin observaciones compatibles el estado de ejecución será desconocido.

Después se definirá observación opt-in compartida para los tres runtimes:
recibos de evento acotados, IDs opacos, fecha, rol reconocido, clase de herramienta
y resultado declarado. El registro operativo no será otra base de tareas o
memoria. Una respuesta terminada no implica muerte del agente y una observación
antigua no mantiene un agente marcado como vivo. Productores, concurrencia,
retención y degradación tendrán QA nativa propia antes de mostrar ejecución.

Las acciones mutables del panel delegarán en los dueños canónicos de tareas,
planes y memoria. Requerirán identidad del artefacto/versión, detección de
conflictos y evidencia del resultado, con pruebas de las puertas existentes.
La investigación de aprobación visual de planes precede a elegir ese contrato.
Este diseño fija secuencia; ninguna de estas capacidades se declara entregada.

La comparación posterior confirma revisión visual de planes implementada,
con anotaciones, aprobar/pedir cambios, recarga, SSE hacia navegador y long-poll
hacia el agente: comparisons/panel-plan-review.md. Se elige adaptar esa experiencia
al mismo servidor, manteniendo el plan/ledger canónicos y una decisión ligada
al hash de contenido. El consumidor común reconocerá pendiente, entregada y
consumida, confirmación idempotente y conflictos de versión. La UI solo sustituye
puertas de confirmación existentes o una revisión solicitada. No crea permisos
nativos ni invalidará autorizaciones previas válidas mediante preguntas repetidas.

El [contrato de integración visual](comparisons/plan-review-integration-contract.md)
concreta esta decisión en el bloque 19. El dueño compartido conserva el recibo;
el navegador no recibe ni confirma consumo en nombre del workflow.
El transporte usa consultas de estado acotadas, sin SSE ni long-poll adicionales.
La aceptación requiere unir UI, CLI y puerta de comando sobre la misma versión.

## Bloque 15 — comandos y transporte del dashboard

Prioridad confirmada por el usuario: comandos, dashboard y memoria; nuevas
skills y ampliación de hooks continúan aplazadas. Se compara servidor de
archivos, runner externo y transporte propio: se elige transporte propio
sin servir archivos arbitrarios ni introducir otra base de trabajo.

Modo `--serve` explícito de plugin-catalog, independiente de exportar HTML/JSON,
con proyecto obligatorio y bind fijo 127.0.0.1. Puerto efímero por defecto;
capacidad aleatoria por proceso en prefijo de URL, sin cookies, query, logs
de acceso o persistencia. Host exacto con puerto, Origin propio cuando exista,
rechazo de cross-site y métodos mutables. Solo página y api/progress; ninguna
ruta de proyecto elegida por HTTP. CSP HTTP con nonce, conexión al mismo origen,
sin marcos, formularios o base externa; respuestas no-store y no-referrer.

Catálogo y diagnóstico permanecen fijados al arranque. El progreso se lee con
local-read y progress-report.resumir(text=...), sin activas/session/resume,
meter o journal. Límites: 128 entradas, 256 KiB por ledger, 1 MiB acumulado,
64 iniciativas, ocho tareas visibles por iniciativa y 64 KiB de respuesta.
Texto redactado antes del recorte, solo campos admitidos; ninguna ruta absoluta,
cuerpo, verificación libre o métrica ausente convertida en cero. Fuente y hash
de contenido, fecha de lectura y parcialidad explícitas. Estado declarado
del ledger no prueba ejecución de agentes. Polling cinco segundos sin solapar,
plazo cuatro segundos, pausa en pestaña oculta y actualización manual.

La corrección de doctor conserva el nombre de archivo en errores largos
sin alterar el saneador replicado de 200 caracteres. Se prueba sobre las
ramas reales taxonomy/training, con redacción anterior al recorte.

Memoria: no llamar knowledge-find/journal.status/candidatas desde polling.
Sus lectores y degradaciones requieren contrato acotado antes de consumo web.
La siguiente entrega será consulta local explícita, con IDs/versiones/evidencia,
sin escritura de índice ni red; benchmark local antes de comparar backend.
El conocimiento aprobado, continuidad y contexto estructural conservan sus
dueños. Revisión visual y acciones mutables se integran después del transporte.

Archivos de este bloque: scripts/plantilla/assets de plugin-panel; tests
panel_server/panel_live_ui; doctor/test_doctor; comando plugin-catalog y sus
exports; evals existentes; documentación ES/EN, contratos, changelogs y ledger.
Los primeros tests se escriben antes de producción. Servidor y productores
no se declaran entregados hasta revisión independiente y QA de transporte/UI.

### Evaluación de componentes de memoria existentes

Comparar las capacidades de memoria de la referencia original y del plugin
con Kwipu, Graphiti y Graphify sobre revisiones fijadas. Distinguir búsqueda,
continuidad, aprendizaje propuesto, conocimiento aprobado y contexto de código;
ningún score o grafo sustituye la autoridad del Knowledge Gate.

El despliegue Docker del usuario ya existe. Su documentación y health se
revisan sin abrir credenciales, corpus o almacenamiento ni reiniciar servicios.
Pruebas posteriores usan namespace/corpus sintético propio y límites de lectura,
sin cambiar los datos existentes. Cloud descrito por defecto requiere distinguir
modelo efectivo, ubicación de inferencia y privacidad del contenido evaluado.
Disponibilidad y documentación no equivalen a recuperación verificada.

Comparar control local, Kwipu para lectura humana/agentes, Graphiti para
relaciones temporales y Graphify para contexto estructural. Medir citas/ID,
versión, autoridad, calidad de recuperación, latencia, aislamiento, fallos,
persistencia y reconstrucción antes de decidir componentes retenidos. Una
comparación documental no declara consulta integrada ni eficacia de backend.

## Bloque 16 — Consulta común y acotada de memoria

La memoria de referencia ofrece un vault común para CLI/MCP y límites de
escaneo. Nuestro Knowledge Gate conserva una autoridad distinta. Consolidar
lectura/ranking/relaciones existentes antes de integrar recuperación externa;
no crear otra memoria, nueva skill o aprobación por score.

`knowledge-view.py` será el lector/proyector compartido de consulta local.
Usará `local-read.py`, parsers/ranking/relaciones de `knowledge-find.py` y
validación canónica de metadatos aprobados de `knowledge-local.py`. Extraer
validación de un snapshot de textos desde el índice existente, sin duplicar
sus reglas ni llamar a walk/build_index desde la web. La taxonomía local
se lee acotada y se valida sin importar adaptadores; ausencia usa el default
canónico. No se lee configuración nativa, journal, caché o corpus candidato.

Cerrar también la lectura íntegra de `ficheros_corpus`/aprobados en la consulta
ordinaria: reutilizar el mismo snapshot acotado, conservar degradación y
hacer visible `corpus_read` en salidas existentes. Un snapshot parcial no
se guarda ni se presenta como índice completo. La nueva vista explícita
de CLI omite toda caché; show/related no resuelven colisiones por primer ID.
Los estados/procedencia legados y aprobados permanecen diferenciados.

Presupuestos iniciales: 256 entradas de directorio acumuladas, 128 archivos,
256 KiB por archivo, 2 MiB de lectura acumulada, profundidad ocho para carpetas
aprobadas declaradas; máximo 20 aciertos, ID 256 caracteres, consulta 1.000,
cuerpo seleccionado 12.000 y respuesta 64 KiB. Cada omisión, enlace, corrupción,
fallo, estado/identidad no resoluble o presupuesto agotado es explícito. No se
recorta un ID para usarlo como selector. Identidad de fuente/hash es procedencia,
no autenticación ni prueba de aprobación humana.

Contrato público versión 1, source `canonical_knowledge`, `observed_at` UTC,
`operation: search|show|related`, `status: ok|partial|not_found|unavailable|
ambiguous|invalid_request`, `complete`, `issues` con códigos opacos. `entries`
contiene como máximo veinte resultados compactos: ID completo, tipo, estado,
titular/área, versión disponible, evidencia declarada, category, origen
`legacy|approved`, ruta relativa y hash del texto. `selected` es null o esa
entrada con cuerpo explícito acotado; `related` es null o grupos canónicos
sucesion/iniciativa/area/enlaces. `budget` declara archivos/bytes/entradas
leídos; no convierte corpus incompleto en ausencia sana. Redactor canónico
antes de truncar o enviar cualquier texto controlado por el consumidor.

El panel ofrece búsqueda, selección y relaciones mediante acción explícita.
No busca al cargar, al filtrar catálogo o por polling de progreso. Única
ruta POST `api/memory`, mismo prefijo privado/Host/Origin/CSP/no-cookies que
el transporte actual, body JSON acotado a 4 KiB, sin campos de rutas, root,
backend, comando o configuración. Rechazo de campos duplicados/desconocidos,
UTF-8/JSON inválidos y tipos ajenos. Lectura de body con plazo acumulado;
plazo de petición UI, exclusión de solapamientos y estados de error visibles.
Ningún cuerpo viaja antes de seleccionar show. Solo texto en DOM, con teclado
y móvil; catálogo offline mantiene cero consultas/red. POST sirve una consulta
y no autoriza escrituras, sincronizaciones, índices o ejecución de adaptadores.

El adaptador documental acota health, snapshot y cuerpos de error antes de
parsear. Mantener contratos de estado/verificación, routing y writer propios;
agotamiento de bytes/plazo o JSON excesivo no acredita salud/completitud.
Cerrar sockets en todos los caminos; saneador replicado permanece idéntico.

Preparar en paralelo benchmark sintético y verificar metadata/protocolo del
despliegue actual, sin consultar datos existentes. No habilitar una consulta
en web por descubrir un backend. Namespace/almacén aislado, modelo efectivo,
compatibilidad, citas/versiones/vigencia y recuperación tras fallos preceden
a decidir Kwipu/Graphiti/Graphify. Si un servicio no permite aislamiento,
usar instancia temporal propia con componentes existentes; nunca reconstruir
su índice general para medir. Lecturas de metadata no son resultados de calidad.

Archivos: knowledge-view/test_knowledge_view nuevos; knowledge-find y pruebas,
knowledge-local y pruebas para parser de snapshot; markdown_export y pruebas;
servidor/renderer/assets/tests del panel; comando existente y exports/evals
si cambia su contrato; matriz/flujo/docs ES/EN/changelogs y roadmap. TDD antes
de nuevos scripts y regresiones de límites antes de cambiar producción.

### Ajustes tras revisión independiente del bloque 16

Las fixtures de revisión exigen conservar legado ante ausencia del helper
aprobado, IDs de relaciones íntegros y versiones interoperables. Mantener
enteros positivos seguros; versiones mayores se proyectan como decimal exacto
de hasta 4.300 dígitos, sin convertirlas a Number. Metadatos inválidos quedan
desconocidos con parcialidad, sin inutilizar los demás aciertos.

Además de entradas/bytes, acotar a 256 llamadas de listado acumuladas: una
carpeta vacía/inexistente consume trabajo aunque no devuelva nombres. Reservar
el byte de sonda del lector dentro del presupuesto acumulado y detener acceso
al agotarlo. La proyección declara scans para distinguir llamadas y entradas.

Recalcular el timeout de socket inmediatamente antes del handshake TLS, tras
conectar TCP, con el mismo deadline. La redacción completa sigue precediendo
el recorte; cerrar el coste cuadrático de PEM incompletos en el redactor
canónico mediante barrido lineal de marcadores. Actualizar su copia declarada
de journal y probar compatibilidad de secretos completos/incompletos y fallbacks.
No crear un redactor alternativo para el panel ni afirmar cancelación de I/O.

### Ajuste de identidad tras el segundo pase

Conservar el tipo de declaración de una relación antes de perder las comillas
del frontmatter: un escalar entrecomillado como `[ADR-002]` o `- ADR-002`
es un ID literal; una lista inline/de bloque expresa varios IDs. No interpretar
el escalar como lista, exista o no su destino. La conservación de identidad
se aplica a referencias resueltas, no resueltas, inversas y a la caché ordinaria.
Añadir casos RED contra la selección del ID corto ajeno y contra referencias
sin resolver, manteniendo las listas reales y las anotaciones históricas.
Al leer el escalar plano, reconocer el delimitador antes de los comentarios:
un `#` dentro de comillas pertenece al ID y se elimina solo la pareja exterior
de comillas. Conservar el tipo literal también evita reinterpretarlo como
anotación histórica. Este ajuste no introduce un parser YAML completo.
Los items entrecomillados de una lista conservan también su tipo literal;
la lista no convierte su contenido en anotación histórica.

## Bloque 17 — Experimento funcional de memoria

El usuario autoriza probar el uso real aprovechando el despliegue existente,
priorizando la combinación documental/estructura de código. La memoria local
sigue siendo el control y la fuente canónica. No activar tres backends en
cada tarea ni escoger por health o número de funciones.

Ejecutar con las fuentes sintéticas ya preparadas y almacenes físicos propios:
Kwipu no tiene namespace de consulta; su indexer/bridge experimental usarán
directorios exclusivos, nunca el índice existente. Reutilizar imágenes fijadas
y el endpoint de modelos ya disponible sin reiniciar servicios, descargar
modelos, leer secretos o cambiar configuración del despliegue. Graphify usará
un productor AST fijado y revisado, en entorno privado, sin instalar skills o
hooks en los hosts del usuario ni ejecutar una pasada semántica implícita.

Medir aciertos citados, abstenciones, aislamiento, vigente/obsoleto, latencia,
tokens/contexto, recursos y persistencia/actualización. Conservar preguntas y
fuentes comunes con el control local; separar tareas documentales de las de
código. Los errores de ingesta, cuotas o producer se registran como resultado,
sin convertir salud/fixtures de esquema en calidad. El coste monetario será
desconocido si el proveedor no entrega una medición verificable.

Los contenedores/puertos/almacenes de prueba serán propios, etiquetados y
registrados antes de usarlos; solo se detendrán o retirarán esos recursos.
No copiar datos del usuario, leer logs de los servicios existentes, usar clear
sobre grafos compartidos o modificar el Source Manager. Las conclusiones pueden
descartar componentes: la selección final se apoya en utilidad adicional y coste
de operación, con la memoria local disponible sin Docker.

### Corrección acotada de delimitadores del lector local

Respetar el cierre de comillas del frontmatter plano: una barra inversa dentro
de comillas simples es contenido literal; no impide cerrar el escalar antes
de un comentario externo. En comillas dobles, distinguir barra escapada y
comilla escapada por paridad, sin un escaneo retrospectivo cuadrático. Mantener
el contenido de IDs opacos y la distinción entre escalar literal y lista real;
no añadir un parser YAML completo ni reinterpretar IDs existentes.

Primero reproducir B4 con destino presente/ausente, inversa y comentario,
y controles de comillas simples/dobles, listas reales y `#` literal. Después
corregir el scanner compartido y comprobar la regresión del lector/cache.
El cuarto ciclo autorizado por el orquestador es adicional y acotado: no
reabre criterios aprobados sin evidencia nueva ni sustituye QA o benchmark.

### Resultado del bloque17 y diseño de la siguiente lectura

Los [resultados funcionales](comparisons/memory-functional-results.md) miden
separadamente recuperación local, respuestas documentales, contexto AST y
hechos temporales con fuentes sintéticas propias. No se mezclan sus denominadores
ni se comparan latencias de búsqueda con generación. La memoria local queda
canónica; se priorizan Kwipu y Graphify opcionales. La prueba Graphiti no
demuestra utilidad temporal adicional y su corte superior falla; mantener su
capacidad opt-in no acredita ese contrato ni modifica consumidores.

El [contrato del bloque18](comparisons/memory-read-integration-contract.md)
amplía los dueños existentes: lectura opcional en markdown-export/router y
selectores/recibos de inputs en code-context. Respuesta generada y contexto
estructural no heredan aprobación. Routing/manifest/canon preceden a red;
snapshot previo/posterior detecta cambios sin certificar atomicidad. Los recibos
solo verifican bytes del conjunto declarado, ligados al artefacto por su productor.
El lector no extrae ni fabrica recibos para grafos antiguos.

Primero verificar propagación del export real a snapshot, después RED/implementación
de lectura y de selectores/vigencia. La aceptación nativa, QA y revisión de esos
cambios siguen pendientes. No se crean skills, agentes ni servicios obligatorios;
las tareas globales conservan sus estados y todos sus criterios restantes.
