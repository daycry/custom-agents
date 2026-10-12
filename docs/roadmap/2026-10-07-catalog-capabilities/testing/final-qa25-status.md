# Validación del bloque operativo — estado parcial

El bloque comprende hooks, comandos, dashboard y memoria. La ampliación del catálogo de skills sigue aplazada. Las comprobaciones siguientes no cierran la iniciativa ni acreditan todo el plugin. La interacción visual en navegador continúa bloqueada y sin verificar. No hay promoción al proyecto, commit ni push de este cierre.

## Estado actual del cierre

La QA completa de la fuente working24 (1.082 archivos) terminó en exit 0
con las 7.020 pruebas previstas por plataforma, sin fallos ni errores.
Conserva las colecciones anteriores y añade once regresiones, sin exclusiones.

| Plataforma | Python aprobado / omitido | Media por propietario | Líneas cambiadas | Node aprobado / omitido |
|---|---|---|---|---|
| Windows | 6.921 / 99 | 91,78153326836936 % | 91,92277383766745 % | 328 / 0 |
| Linux | 6.962 / 58 | 91,88489064128503 % | 92,04097714736012 % | 312 / 16 |

Los dos gates Python superan el 90 % sin redondear, sobre los 22 archivos
Python de producción modificados y los 14 directorios de CI. Coverage.py
7.16.2 usa su CTracer oficial. La suite original del dashboard se ejecutó
además directamente en cada padre; ambas ejecuciones pasan. No se atribuye
cobertura de hijos al padre. Linux registró 82 subtests adicionales aprobados:
no se cuentan como nuevos casos de la colección.

La suite Node usa los ocho módulos y Node 22.23.3 con concurrencia predeterminada.
Las dieciséis omisiones Linux corresponden a casos exclusivos de Windows.
Se preservaron fuentes y dependencias. Los contenedores propios terminaron y
se retiraron con ausencia comprobada. La auditoría observó el terminal de
3.867 procesos lanzados en Windows y 3.919 en Linux; el job propio acabó sin
procesos activos ni fuga. Este wrapper no acredita todos los descendientes
del sistema fuera de su alcance.

La comprobación de referencias excluidas revisó los 1.082 archivos, incluido
el texto del PDF, sin coincidencias. La lectura estática dirigida registra 70 cuerpos completos, sin cuerpos
parciales ni dependencias declaradas sin leer. El cierre cubre este grafo
de comparación de hooks, guardias y aprendizaje; no acredita todo el catálogo
ni eficacia nativa. Los recursos de referencia no se ejecutaron.

Siguen pendientes los workflows nativos, la UI real, el cierre de dependencias
y la revisión independiente. No hay promoción al checkout, commit ni push de
este cierre. Las skills siguen aplazadas. Los resultados anteriores permanecen
sin cambios; esta QA no demuestra todas las causas de sus fallos históricos.
[Evidencia de QA actual](dual-platform-qa29-evidence.json).

## Pruebas nativas parciales — 2026-10-11

Claude 2.1.295 carga el plugin, expande `work-resume` con sus argumentos y
ejecuta el compositor real mediante su herramienta Bash. La salida conserva
las dos revisiones de la fixture: vigente y de otra versión. La decisión
registrada sigue pendiente, sin entregar, consumir ni conceder aprobación.
El inventario completo de archivos y directorios del proyecto permanece igual.

Codex 0.162.1 instala el marketplace local y el plugin en un CODEX_HOME
aislado; sus 1.083 archivos coinciden con la fuente. La invocación explícita
carga la skill adaptadora y conserva los argumentos. Este paso no lee por
sí mismo el cuerpo completo del comando. La prueba posterior de lectura y
consulta fue rechazada por la política nativa de ejecución de solo lectura;
se conserva el rechazo y el caso no está aceptado.

OpenCode 2.0.12 descubre los quince comandos Markdown generados en el
proyecto y la API V2 expande work-resume con sus argumentos. La consulta nativa
ejecuta el compositor real y conserva la revisión vigente y la de otra versión,
sin entregar, consumir o aprobar y sin modificar archivos ni directorios.
La disponibilidad se comprueba por los nombres esperados; un registro vacío
o sólo con los dos comandos internos no acredita fallo ni cierre.

La prueba nativa encontró que los ejemplos de carga de skills usaban `name`,
pero V2 requiere `id`. Se corrigieron los ejemplos de agentes y comandos en
el generador y se regeneraron los transportes. El test de contrato falla antes
del cambio y pasan las 38 pruebas del módulo tanto en Windows como en Linux.
La herramienta nativa carga por ID una skill existente y devuelve su cuerpo
completo. No se amplía el catálogo. Coverage.py/CTracer mide el 87,03703703703704 %
del propietario en esta suite focal; las dos líneas modificadas son texto de
constantes y no figuran como ejecutables. No se inventa un porcentaje para ese
delta ni se sustituye la medición conjunta de working24. La revisión independiente
de esta corrección sigue pendiente. [Evidencia del contrato](opencode-contract31-evidence.json).

Los proveedores de Claude y Codex son fixtures locales controladas, sin
inferencia externa ni tokens facturables medidos. Todos los procesos de estas
pruebas son terminales y su limpieza está confirmada. No acreditan juicio de
un modelo real, todos los hooks ni aprobación humana efectiva. Quedan pendientes
los demás flujos nativos, UI real y revisión independiente.
[Evidencia nativa](native-transport30-evidence.json).

## Consumidor nativo de decisiones versionadas — Claude

Claude 2.1.295 ejecutó por Bash nativo los cuatro pasos del dueño CLI:
receive devuelve entregada; ack confirma consumida con los mismos IDs;
la relectura view observa completa y vigente la misma versión y puerta plan-ok.
Tras cambiar el plan desde el controlador de la fixture, status devuelve
version_changed y la versión actual difiere de la ligada a la decisión.
El estado consumida no convierte la decisión antigua en vigente.

Son decisiones sintéticas creadas mediante la API del dueño, sin interacción
humana real ni juicio del modelo. El cambio de plan fue una interferencia
controlada de ROOT después de la relectura. No se inició implementación ni
se publicó memoria. tasks.md permanece intacto y los cambios del proyecto se
limitan al plan de la fixture y al estado propio de revisiones.
Fuente, bundle y ejecutable mantienen sus hashes; el job terminó con cero
procesos activos y sin fuga. Se conserva el primer fallo de preparación por
runtime inválido, previo al lanzamiento del cliente.
[Evidencia del consumidor](native-plan-consumer34-evidence.json).

Esta prueba acepta el recorrido técnico de la fixture en Claude. No acredita
la aprobación mediante UI, atención del modelo, ejecución completa de dev-cycle,
feedback por comentario, los otros clientes o entrega a memoria. Esas puertas
y la revisión independiente permanecen pendientes; no se cierra la iniciativa.

## Propuesta nativa de memoria pendiente — Claude

Tras la autorización del usuario, Claude 2.1.295 ejecutó propose mediante Bash
nativo, creó un único candidato pendiente y devolvió su ruta y SHA. La consulta
resume inicial no infiere asociaciones: devuelve not_registered. El controlador
de la fixture registra explícitamente la referencia en el ledger y la segunda
consulta observa pending / candidate_observed con el mismo SHA.

El modo dontAsk se conserva con permisos para los dos comandos exactos y el
archivo de entrada, dentro del directorio temporal autorizado. No se modifican
configuraciones personales ni se emplea bypassPermissions. La memoria aprobada,
la entrada antigua, el plan, la taxonomía y la evidencia conservan sus bytes.
No se aprueba memoria ni se publica en backends. El productor declarado retro
no autentica la identidad de un agente. La asociación es del controlador de
la fixture, sin juicio de un modelo real ni aprobación humana mediante UI.

Claude y el proveedor local terminaron correctamente los tres tool calls en
cuatro turnos. El verificador original terminó en rojo: omitía el archivo vacío
persistente candidates/.curation-lock de su lista de cambios esperados. Una
auditoría posterior contrasta el contrato del dueño, comprueba que el bloqueo
está liberado y verifica el inventario completo, sin repetir el cliente nativo.
Se conserva el verificador fallido; no se transforma su exit 1 en verde.

También se conserva el primer intento rechazado por permisos, sin candidato
ni cambios en el proyecto; su controlador agotó el plazo y el cierre del job
retiró un hijo todavía activo. El segundo intento terminó sin procesos activos
ni fuga. Fuente, bundle y ejecutable mantienen sus hashes.
[Evidencia de memoria](native-memory-proposal35-evidence.json).

Esta comprobación acepta el recorrido técnico pendiente y su proyección de
reanudación en Claude. Los hooks no se ejecutaron en modo bare. Permanecen
pendientes la curación y publicación completas, feedback por comentario,
los demás clientes, UI real y revisión independiente. No se cierra la iniciativa,
no se promueve al checkout y no hay commit ni push.

## Feedback por comentario — recorrido nativo en Claude

Claude 2.1.295 carga el cuerpo completo de dev-cycle del bundle y ejecuta ocho
operaciones del dueño real en una fixture: result, verify-result, view, status
tras cambiar el plan, vista de la revisión nueva, reintento del resultado,
reintento incompatible y relectura histórica final. Nueve turnos del proveedor
local terminan sin errores; el cliente y el job son terminales, sin fuga.

La respuesta y la verificación conservan comentario, sección, versión y los
IDs de decisión/entrega/resultado. El segundo comentario no recibe respuesta
ni verificación inventadas. Los recibos de feedback tienen review null y
approval_granted false. La decisión de fixture pide cambios: registrar atención
o confirmed no la convierte en aprobación del plan.

Al cambiar el plan, la revisión consumida pasa a version_changed y conserva
sus filas. La revisión de la versión nueva tiene resultados/verificaciones y
decisión vacíos; muestra la revisión anterior sólo en su historial. Un reintento
con los mismos IDs y texto mantiene fecha y filas sin nueva escritura. Su
recibo refleja la revisión actual del registro, no el número del primer recibo.
Un texto distinto con el mismo ID devuelve operation_conflict sin sobrescribir.

El primer caso conserva exit 1: el oracle exigía igualdad también del número
de revisión del recibo tras registrar la verificación. Se contrasta la causa
con el contrato del dueño y se ejecuta una segunda fixture con ese criterio
corregido; el fallo original permanece sin aceptar. Sólo cambian el plan
controlado y el registro propio. tasks.md, fuentes, bundle y ejecutable se
conservan. La documentación ES/EN precisa la semántica del reintento.
[Evidencia de feedback](native-feedback36-evidence.json).

La decisión, la observación de verificación y el cambio de plan son sintéticos,
de ROOT: no acreditan intervención humana real ni juicio del modelo. La
identidad del productor es declarada. No se implementó una tarea ni se publicó
memoria. Los hooks no se ejecutaron en bare. Siguen pendientes los otros
clientes, UI humana y revisión independiente; esta comprobación no cierra
la iniciativa ni promueve el checkout o publica commits.

## Consumidor nativo de decisiones versionadas — OpenCode

OpenCode 2.0.12 descubre los quince comandos generados del proyecto aislado y
carga el cuerpo completo de dev-cycle con su argumento. La API V2 acepta el
comando con HTTP 204; wait termina con 204. El proveedor local controla cuatro
llamadas nativas shell: receive, ack, view y status después de cambiar el plan.

Receive observa entregada, ack confirma consumida con los mismos IDs y view
relee la vista completa, vigente y ligada a plan-ok. Un cambio posterior del
controlador produce version_changed: la decisión sigue consumida en su versión
histórica y no autoriza la nueva. Los vínculos de versión/decisión/entrega se
conservan. tasks.md y fuentes permanecen intactos; sólo cambian plan de fixture
y registro propio de la revisión. Bundle y ejecutable conservan sus hashes.

El servidor se detiene explícitamente al terminar el wait; su exit 1 corresponde
a esa terminación solicitada, no se presenta como un exit natural 0. El controlador
y cleanup terminan en exit 0, con cero procesos activos y sin fuga. El primer
caso conserva exit 1 por exigir status 200 al endpoint command, cuyo contrato
V2 es NoContent/204; se detuvo antes de esperar, sin llamadas al proveedor.
[Evidencia OpenCode](native-opencode-consumer37-evidence.json).

La decisión y el cambio de plan son de la fixture sintética de ROOT, sin UI humana
ni juicio de un modelo real. Esta instalación carga comandos y agentes de
proyecto; no carga hooks. No se inicia implementación ni se publica memoria.
La prueba acepta ese recorrido técnico en OpenCode, no todos sus workflows.
Feedback en este cliente, Codex, UI real, curación/publicación completas y
revisión independiente siguen pendientes. No se cierra ninguna macro ni se
promueve el checkout; no hay commit ni push.

## Graphiti real — errores tipados y creación de episodios

El servidor devuelve ErrorResponse bajo structuredContent.result con isError false.
El cliente sólo miraba isError y lo devolvía como éxito. La corrección decodifica
el resultado y rechaza su campo error con diagnóstico saneado, sin alterar éxitos.
RED: cinco fallos de seis casos; GREEN: 322 casos correctos, cero fallos/errores/omisiones
en Windows y Linux. CTracer oficial 7.16.2: cambios 100%, owner 92,48% en ambas.
El servidor real confirma el mismo rechazo con ErrorMCP antes de encolar.

El primer pase amplio conservó un fallo por una aserción que esperaba el mensaje
antiguo de publicación intacta. Se actualizó sólo ese diagnóstico y se conservaron
las comprobaciones de outbox, dead-letter, manifiesto y causa. El siguiente intento
tuvo un error de indentación del test; ambas ejecuciones fallidas se conservan.
La fuente corregida y compilada pasó después las suites completas en otro pase.
Jobs cerrados sin fuga; contenedores propios retirados y ausentes.
[Evidencia](graphiti-error44-evidence.json).

La publicación sintética real aún falla: el worker registra node-not-found para
el UUID enviado por el plugin. El código instalado de graphiti-core 0.30.1 recupera
un Episodic existente si recibe UUID; no crea ese identificador nuevo. La entrada
no llegó a confirmarse. Se limpió sólo el grupo propio tras observar fallo exacto,
sin reenvíos ni cambios a otros grupos/servicios; puede quedar su metadata vacía.
Este recorrido no acepta consulta, retirada, extracción ni handoff nativo.

Sigue pendiente adaptar creación, identidad y confirmación, además de respetar
la distinción Episodic/Entity al revisar sucesión y retirada. La candidata incorpora
el fix de ErrorResponse y el diagnóstico, sin cerrar macros/revisiones/global QA,
promover checkout o ejecutar commit/push. Las skills nuevas siguen aplazadas.

## Servicios reales — observación de conectividad

El 2026-10-11 a las 19:07:46 UTC, los adaptadores de la candidata observan sanos
los endpoints loopback de la documentación Docker del usuario. Kwipu responde
`status=ok, property_graph=ok, ollama=ok` en unos 451 ms. Graphiti responde
`get_status=ok` por MCP y health HTTP healthy en unos 513 ms. Se usan los métodos
health reales, con configuración explícita de esta prueba y entorno cerrado.
[Evidencia de conectividad](live-backend-health42-evidence.json).

La comprobación no publica ni consulta conocimiento, no ejecuta extracción de
episodios y no cambia contenedores o configuración del proyecto. Source y docs
externos conservan hashes; job cerrado sin fuga. Estos estados son observaciones
del instante indicado, sin promesa de disponibilidad posterior. No acreditan
calidad del LLM, recuperación semántica, persistencia, benchmark ni handoff nativo.
El siguiente paso sigue siendo una entrada controlada por el caller y su
recuperación/verificación, manteniendo opt-in y autoridad del canon local.

## Publicador de memoria — replay, finalización y recuperación parcial

Tres correcciones validadas en la candidata: el replay se drena antes de calcular
el plan fresco para reconciliar retiradas y versiones vigentes; la finalización
del manifiesto reintenta sólo errores Windows 5/32/33, hasta cuatro intentos y
con identidades observadas estables; el CLI y sus contratos informan posible
publicación parcial y recuperación, sin prometer rollback global. El mismo test
de recuperación bloquea el segundo reemplazo real, observa primer archivo nuevo,
segundo antiguo, manifiesto anterior y diario pendiente, y completa la publicación
en la siguiente sincronización. Canon local y vecino ajeno conservan sus bytes.

Windows y Linux: 109 casos por plataforma, 108 correctos, una omisión y cero fallos.
Cobertura parent CTracer oficial 7.16.2 sobre ambos owners y cambios ≥90%; no
acredita cobertura de hijos ni el gate global. El lector nativo Windows del pase
anterior reproduce el rechazo de rename sin compartir borrado. No identifica el
proceso que causó el WinError 5 histórico sin instrumentación. Fallos y recibos
anteriores se conservan. Contenedor propio retirado/ausente y jobs cerrados sin
fugas. [Evidencia acotada](publisher-recovery41-evidence.json).

El lote sigue publicándose por archivo; pueden verse cambios antes del manifiesto
final. Las firmas observadas bajo cerrojo cooperativo no son CAS contra terceros.
Estas pruebas usan corpus sintético y filesystem/outbox reales, no publican en
servicios del usuario ni acreditan todos los callers nativos, UI o juicio humano.
Se incorporan las correcciones y contratos a la candidata, sin promover el checkout,
cerrar macros, aceptar la revisión final ni ejecutar commit/push. Skills nuevas aplazadas.

## Curación y portabilidad — agente nativo OpenCode

OpenCode 2.0.12 delega al agente generado knowledge-curator, carga su prompt
completo y devuelve el resultado al padre. El hijo ejecuta diez herramientas
nativas en fixtures: gate de lectura; rechazo de apply con SHA antiguo; rechazo
de recover tras cambiar la fuente; recuperación de una intención preparada;
apply con SHA exacto; lectura del aprobado; exportación de un ID seleccionado;
import --check; import pendiente y reintento idempotente. Trece peticiones del
proveedor local completan el recorrido sin errores. Edit/Write no se exponen
al hijo; esto no acredita identidad autenticada ni confinamiento de shell.

Las fuentes cambiadas conservan candidato, intención y staging. La recuperación
válida completa la decisión de fixture ya preparada y retira únicamente su
staging y fuente exactos. La aprobación nueva crea otro aprobado con recibo;
la lectura nativa observa id/estado. Se crean dos aprobados sintéticos, ninguno
en memoria de producción. Vecinos approved, legado y taxonomías se conservan.

Export selecciona sólo el ID indicado y conserva bytes/hash originales en su
paquete. El controlador copia ese paquete al proyecto destino. Import --check
no crea ni modifica archivos/directorios. Import persiste un único candidato
pending, sin estado aprobado ni ID local final, con recibo y procedencia. El
reintento conserva el árbol exacto y declara written false. Los backends de
ambas fixtures están desactivados y no se publica en servicios externos.

El verificador original terminó en exit 1: omitía de sus cambios permitidos el
staging final, bajo approved, que recover retiró. La auditoría terminal contrasta
esa ruta y su hash con la intención original y el destino publicado, además
de todos los inventarios/recibos. No repite el cliente ni convierte el exit 1
original en verde. Servidor detenido explícitamente (exit 1); job cerrado sin
procesos activos ni fuga. Fuente, bundle y ejecutable conservan sus hashes.
[Evidencia de curación](native-memory-curation38-evidence.json).

Las propuestas, decisiones e interrupciones pertenecen a la fixture de ROOT;
el proveedor fija las llamadas. No se acepta juicio semántico real, aprobación
humana o revisión independiente. Los hooks no están cargados en esta instalación
de comandos/agentes de proyecto. Los otros clientes, publicación en backends,
UI real y cierre de comparación/revisión siguen pendientes. No se cierra una
macro ni se promueve el checkout; no hay commit ni push.

## Modelo y parámetros OpenCode — herencia nativa

La temperatura declarada por rol tampoco llegaba al proveedor con el formato
anterior. Esa observación descarta una regresión de la conversión, pero no prueba
la causa interna del cliente. Se retira la traducción propia de tiers de Claude
a temperaturas de OpenCode: no representa elección de modelo ni un contrato de
tiering nativo. Los agentes generados heredan modelo y parámetros y mantienen
sus responsabilidades, modo e identidad y las mismas reglas de permisos.
No se incorpora un hook para forzar parámetros ni se parchea el cliente.

RED: la nueva regresión falla antes de retirar el override. GREEN: módulo
completo, 40/40 en Windows y 40/40 en Linux, sin omisiones. CTracer oficial
confirma ejecución de la asignación de metadata. La prueba nativa configura
un modelo propio y temperatura 0.55 en el proveedor del llamador: reviewer
hereda ambos, lee la fixture, devuelve el resultado al padre y no expone edición.
El archivo leído y las fuentes permanecen intactos; los jobs son terminales
y el contenedor propio está eliminado. Es una prueba de herencia con proveedor
controlado, no de juicio real del modelo o de todos los parámetros/proveedores.

Los casos anteriores con el criterio de temperatura 0.1 siguen conservados
sin aprobar. Se retira la convención del producto por la decisión anterior;
no se convierten esos fallos en verdes ni se declara resuelto el comportamiento
genérico de overrides por agente en el cliente. La revisión independiente,
los demás workflows, UI real y cierre conjunto continúan pendientes.
[Evidencia de herencia](opencode-defaults33-evidence.json).

## Agentes OpenCode V2 — formato nativo y alcance verificado

Los diez agentes propios se exportan con `request.body.temperature` y un array
de reglas `permissions` (`action`, `resource`, `effect`). Sus archivos ya no
dependen de la conversión del frontmatter anterior. La comparación con la
normalización nativa original conserva los diez IDs, modos, descripciones,
requests y el orden completo de los permisos; sólo normaliza los prefijos de
las rutas de cada runtime aislado. Los cuerpos cargados coinciden con el Markdown.
No se cambian los archivos canónicos de los roles ni los permisos globales.

La regresión fue RED antes del cambio y el módulo final pasa 39/39 en Windows
y 39/39 en Linux. CTracer oficial mide las líneas cambiadas clasificadas
ejecutables, 100 %, y confirma ejecución de la asignación completa de metadata.
La cobertura focal del propietario completo es 86,24338624338624 %; esto no
es una nueva medición conjunta ni sustituye la QA de working24. Se conserva
el primer GREEN fallido por una comparación incorrecta de comillas escapadas
en el test; el oracle posterior decodifica la descripción JSON, sin cambiarla.

La delegación nativa a reviewer crea una sesión hija, carga su prompt, lee la
fixture y devuelve el resultado al padre, sin exponer herramientas de edición
ni cambiar el archivo leído. La temperatura declarada aparece en el registro
de agentes, pero no en las dos peticiones de la hija al proveedor de prueba.
Ese criterio no está aceptado y su causa sigue pendiente de comprobar; no se
atribuyen eficacia universal de parámetros, confinamiento de shell o juicio
real del modelo. La prueba controlada no sustituye la revisión independiente.
Los procesos son terminales y el contenedor propio está eliminado.
[Evidencia de agentes](opencode-agent32-evidence.json).

## Historial: fuente congelada y QA full02

Fuente congelada de full02: **1.071 archivos**, manifiesto SHA256
`a13d803406646dafc6c40c9e10ff76aa728d5ef527c2b6fc48845713e5c74ec2`.

| Comprobación | Resultado observado | Alcance |
|---|---|---|
| Regresión focal de las correcciones | 127 aprobadas en Windows y 127 en Linux; cero fallos y cero omisiones | Aceptación focal del recibo ROOT SHA `767ef4f0894760b7371335162f26a86c98fd982d187267d6dfe13fb6ab911594`; no sustituye la QA completa |
| Distribución | Siete etapas en exit 0; lint sin errores y nueve avisos | El hijo Git de lint salió 128 y se usó fallback; lint no certifica los modos Git. La procedencia de los modos se conserva en el manifiesto |
| Referencias públicas | 1.071 archivos comprobados, incluido el PDF; cero coincidencias de referencias excluidas | Comprobación documental, no validación funcional |
| Colección para QA full02 | 6.951 casos en cada plataforma, ambas colecciones en exit 0 | Conserva los 6.612 IDs anteriores y 339 añadidos, sin exclusiones; una transición literal de plugin-panel de 82 a 102 líneas |
| Suite QA full02 | Windows: 6.848 aprobadas, cinco fallidas, 98 omitidas; Linux: 6.906 aprobadas, una fallida, 44 omitidas; cero errores | Ambas terminaron en exit 1 sin timeout ni fallo de captura; QA no aceptada |

En full02 se observó el mismo fallo en ambas plataformas en `test_hooks_no_nombran_el_case_store_ni_hacen_red`: el oracle textual encontró `https://` dentro de un comentario. ROOT incorporó una corrección exclusivamente de prosa en la candidata, conservando frozen02 intacta, y ejecutó la función original en RED/GREEN, PID 14572/exit 0, recibo SHA `2b70ab28a8b731b0e2b47af5bc764d4227d60279b73f35df727e946b366aa79b`. Los bytes ejecutables no cambian y la fuente de la suite viva permanece intacta. El foco no elimina el fallo observado ni convierte full02 en verde. También se corrige la explicación documental de que el timeout del plugin no eleva el presupuesto SessionEnd por defecto de 1,5 s.

También se observaron dos fallos Windows en el soporte sintético de recuperación: N05 falla en atomic_record al reemplazar audit.json, lo que contamina el replay instrumentado; N08 falla al renombrar el staging de restauración antes de ejecutar view/status. Ambos registran WinError 5. El informe de diagnóstico SHA 130fb81589e903223b3ace8f5abcf911b76ffe2491340ce684361c5a3fac0e29 identifica estas fases, pero no demuestra la causa del rechazo ni una regresión funcional del producto. Sus resultados originales permanecen en rojo y no se han suavizado los oracles. Otros dos casos Windows fallaron en las suites de training-data-services: uno al renombrar la fixture que simula un enlace dentro del store y otro con PermissionError durante la simulación de publicación del manifiesto de un dataset. Su causa y comprobación focal permanecen pendientes. Las reproducciones mínimas independientes de atomic_record y backup/restore pasaron una vez cada una, sin CLI ni retry; no reprodujeron WinError 5 ni aceptan los casos originales.

La colección conserva los 14 directorios de CI y los 19 propietarios del gate. Los gates de cobertura permanecen en 90 % por media de propietario y 90 % agregado sobre líneas cambiadas, con Coverage 7.16.2 y CTracer. Los terminales y JUnit de ambas plataformas están disponibles. Windows mide 92,05377666417307 % de media por propietario y 91,58031088082902 % sobre líneas cambiadas; Linux, 92,16161806542162 % y 91,79620034542314 %, respectivamente. Ambos gates superan el 90 % sin redondeo. La auditoría independiente de procesos y conservación de fuente sigue pendiente. No se atribuye cobertura de hijos a una medición del padre.

La comprobación focal posterior ejecutó una vez los cuatro casos Windows con fuente y soporte originales: tres pasaron y N05 volvió a fallar con WinError 5, esta vez al publicar la restauración sintética, antes del replay posterior. Recibo SHA d0833a0f787ed30cdf47255db581c22d95b37c84b2792a02635514de62883f25. Se verificaron antes y después los 1.071 inputs congelados y las 86 dependencias; el job propio terminó con cero procesos activos y sin fuga. Este foco no explica las causas históricas ni acepta full02.

## Coste de proceso — gap reproducido

El coste de proceso conserva un gap reproducido con fixtures sintéticas y los CLIs actuales: el primer cierre de una ventana informa 150 tokens y el segundo, acumulativo, 200; conservar ambos snapshots en plan y tasks hace que el dashboard sume 350. El resultado esperado para esa misma ventana es 200. RED PID 21648/exit 1, recibo SHA 6c78148e0d055566c1cbcffa8dc33cdb59cd6d4a6ede1ded60cbebb39b56a4c7. No se usaron transcripciones privadas, precios ni calibración medida. La candidata incorpora fuente/ventana/revisión persistidas y selecciona el último cierre completo por identidad, conservando ventanas independientes y copias legacy. Identidades inválidas o revisiones contradictorias se muestran como datos parciales. RED de los nuevos tests: PID 36180/exit 1 por identidad ausente y total 350. Primera comprobación: PID 28516/exit 0, 65 tests del medidor y suite completa del dashboard. Tras añadir el caso productor → frontmatter → consumidor, PID 15692/exit 1: dashboard aprobado (200 tokens compartidos, 250 con una ventana independiente), medidor 64 aprobados y un fallo en la segunda persistencia del marcador legacy. El fichero original conserva revisión 1 y su temporal contiene revisión 2; la identidad no se emitió tras fallar la persistencia. El error exacto y su causa no quedaron capturados en el assert original. Una observación focal con diagnóstico mejorado, PID 19120/exit 0, pasó el caso aislado; no explica ni sustituye la ejecución fallida. Los RAW originales y sus terminales se preservan. Planner, sus transportes Codex/OpenCode, cuatro plantillas y convenciones bilingües conservan los campos cuando existen, sin inventarlos al degradar. Cobertura del nuevo delta, revisión independiente y aceptación completa siguen pendientes; no hay calibración medida ni precios acreditados por estas fixtures.

### Persistencia y coste parcial — checkpoint posterior, 2026-10-11

Una carga sintética independiente de pytest reprodujo WinError 5 en el reemplazo de state en la operación 63 (62 escrituras completadas), PID 12828/exit 1. Restart Manager devolvió cero usuarios de esos dos archivos en la consulta posterior; esto no excluye usuarios transitorios ni explica la causa histórica. El control positivo, que mantenía abierto otro archivo propio sin compartir borrado, produjo el mismo código y la consulta identificó el PID propio. No se detuvieron procesos externos ni se cambiaron permisos. Los originales de esta observación se conservan, con cero reintentos de la operación fallida y cierre del job sin fuga.

La candidata devuelve `medicion_persistida` como booleano y no emite identidades nuevas cuando falla la escritura. El dashboard excluye ese snapshot acumulado, muestra datos parciales y evita atribuirle una ventana compartida. RED PID 14700/exit 1: faltaba el indicador y el consumidor sumaba 350 en lugar del subtotal 150 con aviso. RED de etiqueta PID 4572/exit 1: una medición excluida se mostraba como compartida. GREEN PID 18944/exit 0: 65 tests del medidor y dashboard completo. La comprobación final instrumentada PID 35976/exit 0 repitió ambas suites con la fuente final: 65 tests aprobados y dashboard aprobado, incluidos productor/frontmatter/consumidor, fallo controlado de persistencia y ventanas independientes. Coverage 7.16.2/CTracer midió 76 de 79 líneas cambiadas (96,20253164556962 %) de los dos archivos de costes frente a frozen02, por encima del gate 90 % sin redondeo. Esta es cobertura del padre de esos dos archivos, no cobertura global ni de hijos. Las plantillas y convenciones conservan el indicador y los avisos.

La observación previa PID 19120 cubrió un único test de marcador legacy y no ejecutó el dashboard. Se conserva el recibo original con su etiqueta de scope imprecisa y una corrección separada ligada al JUnit real. La corrección actual del coste tiene pruebas focales y cobertura; la causa del rechazo Windows, N05, revisión independiente, UI real, QA global y publicación siguen pendientes.

### Temporales y reemplazo del medidor — checkpoint posterior

La prueba RED PID 15168/exit 1 reprodujo una colisión determinista: el segundo escritor consumía el temporal fijo y el primero fallaba con WinError 2. La candidata crea un temporal exclusivo por PID/UUID y reemplaza con hasta cuatro intentos en Windows solo para 5/32/33, con 140 ms de espera programada acumulada. Los demás errores y plataformas no se reintentan; al agotar, mantiene la degradación visible y limpia solo el temporal propio. No hay merge de snapshots ni lock multiwriter.

GREEN PID 30120/exit 0: 74 tests del medidor y dashboard completo. Controles nativos PID 29904/exit 0: liberar el bloqueo propio después del primer WinError 5 permitió guardar en el segundo intento (22,8766 ms); mantenerlo produjo cuatro rechazos y conservó los bytes anteriores (145,9726 ms), con aviso y sin temporales restantes. Una carga adicional completó 100 escrituras sin reintentos externos y sin errores observados; no acredita ausencia universal de fallos. La fuente se conservó y el job terminó sin procesos activos ni fuga. Cobertura final PID 3916/exit 0: 74 tests y dashboard, Coverage 7.16.2/CTracer; 97/103 líneas cambiadas (94,1747572815534 %) de los dos archivos de costes, gate 90 % aprobado sin redondeo. Alcance del padre, no global. La causa/owner de los rechazos históricos y N05 no quedan demostrados ni aceptados por estos controles.

Tres recursos adicionales de sesiones/revisión se leyeron completos, sin ejecutarlos. La comparación identifica continuidad de revisiones pendientes como caller por integrar, y conserva pendientes los recursos de costes descargados pero no leídos. Detalle en [hook-session-continuity.md](../comparisons/hook-session-continuity.md). Continúan pendientes revisión independiente, UI real, aceptación de workflows nativos, QA conjunta y publicación.

## Historia preservada: QA full01

La ejecución anterior usó 1.070 archivos, manifiesto
`a585d17b71f7eb358ed6bef021824204cba3b466c329519e815674951bb265a3`.

| Plataforma | Resultado original |
|---|---|
| Linux | 6.842 aprobadas, 14 fallidas, 44 omitidas, cero errores; 6.900 casos recogidos |
| Windows | 226 aprobadas, una fallida y dos omitidas; ejecución interrumpida al escribir el diagnóstico |

Linux superó ambos gates de cobertura, pero los tests fallidos impidieron aceptar esa QA. Sus 3.907 procesos registrados terminaron y el contenedor propio se eliminó con ausencia posterior comprobada; el wrapper no observó exhaustivamente todos los descendientes del sistema. Los rojos y el fallo del diagnóstico Windows conservan sus RAW, recibos y causas no demostradas. Las correcciones de consola, fixtures de reapertura, escáner y catálogo del panel están incorporadas a frozen02 y pasaron los focals anteriores; estos hechos no reescriben full01 como verde.

## Actividad nativa

| Cliente | Evidencia acotada preservada | Límite |
|---|---|---|
| Claude Code 2.1.287 | Inicio y fin de respuesta del mismo subagente, con identidad HMAC correlacionada y revisión creciente | El resultado original conserva el rojo del oracle de journal y su cancelación SessionEnd; no se atribuye a ese historial la causa de una prueba posterior |
| Codex 0.161.0 | Subagente nativo con inicio y fin de respuesta, rol architect e identidad HMAC comprobada desde el protocolo RAW; diez definiciones con confianza verificada antes y después | Instalación y confianza limitadas al entorno aislado; no acredita todos los eventos |
| OpenCode 2.0.12 | Sesión completada con outcome succeeded, proyecto exacto y execution_finished con identidad HMAC verificada | Sin rol independiente, evento idle independiente, teardown ni colección completa |

Los recibos de actividad y sus límites permanecen sin cambios. OpenCode V2 emite un terminal de ejecución; su proyector deriva idle/outcome. La captura no inventa un segundo session_idle. Los inputs legacy de idle/status conservan sus pruebas de compatibilidad. Estas señales no prueban liveness ni decisiones del modelo.

## SessionEnd aislado: opt-out y captura durable

**Opt-out:** native PID 28092 terminó en exit 0, con un resultado success, stderr vacío y callback SessionEnd completado en status 0. Node y sus dos hijos terminaron correctamente; el job propio quedó sin procesos activos ni fuga. El host PID 4572 conserva exit 1 por el oracle original de efectos: aparecieron los directorios -c y .exe, vacíos y ordinarios. ROOT aceptó una enmienda literal para ese caso aislado, recibo SHA `55f47801f6a9f9cd1228ead95922b72806e57e9a248e6acf3b3a1f6fcf963901`; no permite otros directorios, datos o efectos ni altera el recibo original. El escritor exacto de esos dos directorios y la causa de la cancelación histórica siguen desconocidos.

**Captura durable y replay:** ROOT aceptó una captura nativa sintética y su replay determinista, recibo SHA `85815ca1a539d2afb20844eea507bb5911de9af76ff704c27517afa8dc47c43c`, ligado a la aceptación de captura SHA `b0fe6628abf26ff55bad0ef47e8dc989e0faaf5379b632c396ba72d1c53e21d6`. El cliente original PID 3576/exit 0 y el host PID 37848/exit 1 conservan su resultado; la enmienda acepta sólo los dos directorios vacíos literales y mantiene desconocido su creador. El replay hijo PID 14360, host PID 28996 y cleanup PID 23696 terminaron en exit 0; el job propio registró tres procesos y quedó sin activos ni fuga. Se materializó una nota, con cero restantes, dead-letter y errores; su resumen procede del primer prompt sintético real. Nota SHA `9a605690105ef41592d4d6b297462069a17fb874e1e70dee5fd969d948202d78`. No hubo aprobación automática ni publicación externa. La aceptación cubre este caso aislado, no todas las sesiones ni todos los hooks.

Ambas pruebas usan un proveedor loopback simulado y explícito, sin modelo externo. No alteran el presupuesto nativo por defecto de 1,5 s ni acreditan eficacia de todos los hooks. La fuente y configuración exactas permanecen vinculadas a cada fixture y recibo. El cierre operativo sigue pendiente de resolver o verificar los fallos observados, revisar las últimas correcciones y promover la candidata validada. La captura/replay aceptados no sustituyen esos requisitos ni explican la cancelación histórica.

## Consulta de revisiones al retomar — candidata, verificación incompleta

El dueño `plan-review.py list_reminders` observa la carpeta exacta del ledger,
sin inicializar estado, adquirir bloqueos de escritura, entregar decisiones ni ack.
Dos inventarios y dos lecturas de versión rechazan cambios observados. Hasta ocho
referencias conservan ID, versión, puerta y estado; las actuales y pendientes tienen
prioridad y se cuentan las omisiones. Los contadores de respuestas/verificaciones
son registros, no evidencia de atención, aprobación vigente ni trabajo terminado.

`/work-resume` y el bloque de progreso de sesión usan ese dueño. El historial
`--history-only` mantiene su comportamiento. Exportaciones Codex/OpenCode
comprobadas: 88 ficheros; linter: cero errores y nueve avisos existentes.

RED: las 12 pruebas iniciales fallaron por ausencia de la función/proyección.
Primer conjunto ampliado: 294 correctas, tres fallidas y un error de preparación.
Final01: 298 correctas y dos fallidas; el oracle de omisiones requería tres
registros, pues dos más el encabezado caben en tres líneas. Se corrigió el fixture,
conservando ese rojo. El harness no produjo un recibo final de cobertura; no se
acepta su medición. Final02: 295 correctas, cinco fallidas; las 14 pruebas nuevas
pasaron, cobertura nueva 77/87 (88,51 %), insuficiente para el gate de 90 %.
Se añadieron casos de dependencias incompletas, acceso denegado y omisiones.
Final03: 90 correctas y una fallida; 17/18 nuevas correctas. La prueba de contadores
falló antes de su verificación con estado `unavailable`, sin motivo capturado.
Cobertura de líneas nuevas: 83/87 (95,40 %), CTracer del padre y sus threads,
sin descendientes. Cobertura verde no equivale a tests verdes.

Dos workloads positivos contra el dueño anterior, sin reintentos, se detuvieron
tras 71 y dos ciclos completos con `changed_path`. El segundo observó cambios en
`st_ctime_ns` del descriptor, con identidad, tamaño y mtime constantes. No hubo
OSError capturado ni escritor identificado. Esto reproduce sensibilidad de la
lectura previa; no demuestra la causa de cada fallo histórico ni de Final03.
Las diferencias de timestamps en Windows están documentadas en
[CPython](https://github.com/python/cpython/issues/157671) y la distinción entre
datos y metadatos en [Microsoft](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_basic_info).
Se mantienen las comprobaciones y los rojos, sin atribuirlos a un producto externo.

Evidencia y hashes en [review-resume25-evidence.json](review-resume25-evidence.json).
Lectura estable, revisión independiente, aceptación nativa, UI real y QA conjunta
siguen pendientes. No se promueve ROOT, no se cierra ninguna macro y no hay commit
ni push de este cambio.

## Lectura estable — comprobación focal completada, cierre conjunto pendiente

Se reproduce en Windows el cambio de metadatos sin cambio de contenido y se
conservan los RED: seis fallos del contrato inicial, dos del control nativo y dos
por cachés reales creadas al consultar kits de proyecto sin `-B`.
La candidata incorpora una única relectura acotada del mismo descriptor y
desactiva bytecode en los dos CLIs, con los controles de identidad y rutas activos.

La regresión ampliada inicial dio 389 correctas, una fallida y seis omitidas;
el fallo ocurrió preparando un recibo antes del deadline inyectado, con motivo
`invalid_input`. No se identificó su causa exacta. Tras el arreglo de cachés,
la batería ampliada dio 392 correctas y seis omitidas. La medición posterior,
con controles nativos adicionales en los límites de buffer, dio 187 correctas y
seis omitidas: 23/23 líneas ejecutables nuevas cubiertas (100 %), CTracer del padre.
La cobertura no incluye procesos descendientes. El linter detectó dos avisos nuevos por situar la opción de bytecode antes del bloque UTF-8; se reordenó tras ese bloque y antes de cargar helpers, y se midió de nuevo la fuente corregida. Las seis omisiones corresponden
a la falta de privilegio de symlink nativo de Windows.

Dos workloads positivos independientes completaron 100 y 250 ciclos de
open/submit/receive/ack, sin reintentos de operaciones ni eventos de fallo.
No demuestran la causa de todos los fallos históricos ni aceptación global.
Los recibos terminales y cleanup terminaron sin timeout ni errores de captura.

Evidencia: [stable-read25-evidence.json](stable-read25-evidence.json).
Siguen pendientes QA completa Windows/Linux, revisión independiente, workflows
nativos y UI real. El ledger actual supera el límite de lectura de 256 KiB;
hay que reorganizar su historial conservando trazas y revisiones vigentes.
No se cierra ninguna macro ni se promueve, commitea o publica este lote.

## Ledger legible de nuevo — verificación de comandos acotada

El CLI común reproducía `too_large` con el ledger de 367.539 bytes. Se trasladó
el detalle histórico a `execution-history.md`, conservando el sufijo original
sin cambiar sus bytes y los bloques canónicos de las dieciséis tareas intactos.
Las 23 revisiones conservan encabezados, intentos, resúmenes y filas; también se
mantienen las fronteras que controlan la herencia de cierres anónimos.

Los intentos 1–6 y veinte selecciones (tareas individuales, fases y conjunto)
conservan los mismos resultados. Los gaps del brief y la puerta de aprobación
Jira coinciden, tanto con QA declarada verde como sin ella; no se publica en Jira.
El CLI sin `-B` leyó la copia de 220.880 bytes con estado `ok` y las 16 tareas;
no cambió archivos ni añadió directorios. La evidencia y los hashes están en
[ledger-readability25-evidence.json](ledger-readability25-evidence.json).

No se cambia el límite de lectura, no se borra evidencia ni se cierra una tarea
por compactar documentación. QA conjunta, hosts nativos, UI real y revisión
independiente siguen pendientes. No hay commit ni push de este lote.

## QA completa tercera ejecución y conservación de encabezados

Windows: 6.905 correctas, seis fallos y 98 omisiones. Linux: 6.955 correctas,
dos fallos y 52 omisiones. Cada plataforma ejecutó la colección conservada de
7.009 casos. Se revalidaron fuentes/dependencias y auditorías de hijos; el
contenedor Linux propio quedó eliminado. La QA y cobertura siguen en rojo.

Los dos fallos comunes procedían de encabezados históricos suprimidos al
compactar. Se restauraron trece encabezados y su orden como enlaces al detalle
archivado: 23 pruebas correctas y una omisión, retoma nativa sin escritura,
23 revisiones y veinte selecciones preservadas. No se modificaron las pruebas.

Windows añade un fallo de publicación del audit de la infraestructura de memoria,
dos resultados genéricos al registrar feedback y una sustitución de directorio
de fixture que no llegó a completarse. El original de esta última conserva
validation pendiente; falta capturar el error de la sustitución. Sesenta ciclos
aislados de feedback pasan, con instrumentación que altera tiempos; no prueban
la causa de los fallos históricos ni sustituyen el resultado completo.

La cobertura excluye subprocesos: el dashboard se ejecutaba allí y solo cubría
69/566 líneas en el padre. La suite original medida directamente con CTracer
cubre 443/566; todavía hay que incorporarla a la medición final por plataforma.
La suite Node quedó incompleta por plazo del controlador secuencial; cinco
checks estáticos y el benchmark pasan. Se conservan los fallos y tres cachés
generadas en su copia aislada; los 1.078 ficheros canónicos mantienen sus hashes.

[Evidencia](full03-and-ledger-boundaries25-evidence.json). No hay cierre global,
promoción al checkout, commit ni push. Las skills continúan aplazadas.

## Publicación de estado propio — causa controlada y regresión

Un lector nativo Windows sin compartir borrado provoca WinError 5 al reemplazar
el estado, incluso si se libera justo después del rechazo. La candidata recupera
ese caso con intentos acotados, comprobando la generación y el plazo. Windows:
221 correctas y dos omisiones en las suites de estado, planes, feedback y actividad.
Linux: 18 correctas y seis omisiones Windows en las suites de estado y publicación.
Los dos fallos previos del controlador Linux ocurrieron antes de ejecutar casos;
sus RAW y la eliminación de sus contenedores propios se conservan.

La causa controlada está probada; la de los resultados genéricos históricos no.
Esta regresión no convierte full03 en verde ni mide su cobertura. Continúan
pendientes infraestructura Windows, medición conjunta de dashboard, Node,
workflows nativos, UI real, recursos comparados y revisión independiente.
[Evidencia](state-publication26-evidence.json). Sin promoción al checkout o push.
