# Prioridad operativa y punto de reanudación

Dirección del usuario del 2026-10-08: aplazar la comparación e incorporación
de nuevas skills y centrar el trabajo en hooks, comandos, dashboard y memoria.
El [ledger](tasks.md) sigue siendo la fuente única de progreso; este documento
define secuencia y límites, sin cerrar la iniciativa ni reducir su alcance final.

## Skills aplazadas

Se conservan **79/293 evaluadas**, S001–S079; quedan **214**. S080–S082 tienen
cuerpos leídos y investigación privada parcial, pero no fichas completas ni
evaluación contabilizada. La reanudación comienza por completar ese bloque.
Las decisiones anteriores son destinos propuestos, no altas entregadas.
T-03 y T-10 quedan aplazadas por petición del usuario. Los cambios necesarios
en referencias de una capacidad existente para corregir hooks, comandos,
panel o memoria pertenecen al bloque operativo, sin abrir nuevas skills.

## Secuencia y dependencias por bloque

1. **Hooks (T-02/T-06/T-08/T-09).** Cerrar contrato, diseño, transporte e
   identidad efectivos por runtime; ejecutar pruebas de carga y despacho,
   allow/deny por rol, concurrencia y captura durable de sesión.
2. **Comandos (T-05/T-08/T-11).** Comparar los comandos pertinentes antes de
   modificarlos; consolidar operaciones útiles en el workflow existente,
   actualizar artefactos, consumidores y exports del mismo bloque.
3. **Dashboard (T-06/T-08/T-13).** Comparar las funciones pertinentes y
   presentar handlers, propósito, timeout, procedencia y estado comprobado.
   Diferenciar configuración declarada, carga observada y ejecución probada;
   verificar navegación, filtros, teclado y ausencia de datos sensibles.
4. **Memoria (T-07 y bloques anteriores).** Comparar captura, continuidad,
   curación y recuperación; corregir sus contratos y visibilidad. Medir
   candidatos de recuperación antes de recomendar una migración o ampliación.

Cada bloque exige la comparación pertinente y un diseño trazable antes de
producción. No depende de terminar las 214 skills, todos los agentes ni todos
los tools opcionales. T-14/T-15 se aplican a cada entrega; su aceptación global
y T-16 siguen pendientes mientras quede alcance requerido. Una entrega
operativa no acredita completar la comparación de 455 piezas.

Los [contratos](contracts.md) y [probes](runtime-probes.json) conservan gaps
observados: frontmatter de guardias ignorado en agentes de plugin Claude,
identidad opcional en PreToolUse Codex y carga V1 fallida en OpenCode V2.
El control positivo V2 inicial solo registra callbacks. La entrega posterior
ya valida transporte nativo de contexto, captura, write y cierre/replay;
sus límites siguen en transport_validation de runtime-probes.json.
El timeout declarado tampoco demuestra captura dentro del presupuesto de
teardown. El payload supervisado conserva pruebas históricas de cierre en
[Claude](claude-hook-evidence.json), [Codex](codex-lifecycle-evidence.json) y
[OpenCode](opencode-lifecycle-evidence.json). Claude conserva un envelope antes
de salir y confirma status 0 en debug; Codex completa SessionEnd en 1745 ms
dentro de los 3 s declarados; OpenCode valida dos loops y replay. Las fichas
conservan los resultados históricos anteriores a la supervisión y sus límites.
Codex necesita caché instalada además de enabled. La cohorte posterior de
[integración nativa](native-role-integration-evidence.json) conserva fallos
de SessionEnd Codex y una recuperación manual comprobada: la durabilidad y
eficacia de memoria dentro del teardown siguen pendientes. La medición
histórica de 1745 ms no acredita la cohorte final.

La siguiente investigación completa pruebas de identidad y bloqueo previo
con dispatchers privados en los tres runtimes:
[native-role-contract-evidence.json](native-role-contract-evidence.json).
Claude/Codex entregan agent_type; OpenCode entrega event.agent y confirma
delegación real. Esos nombres no acreditan origen del prompt. El diseño
elige IDs protegidos exactos y namespacing propio Codex/OpenCode, con migración
que preserve agentes y bindings del usuario. La conexión a la distribución,
su migración y las guardias quedaron entregadas en `54e8b3f8` y aceptadas en
el intento 5 del bloque acotado: [QA](native-role-qa-evidence.json) y
[cohortes nativas](native-role-integration-evidence.json). Cada cohorte conserva
sus hashes y límites; no se atribuye toda la matriz al último parser.
El export del reviewer deja de añadir sandbox_mode por rol
en Codex: dos hijos nativos escribieron con esa clave bajo permisos heredados
del padre. El diagnóstico futuro debe distinguir responsabilidad de revisión,
guardia por hook y sandbox efectivo; no convertir presencia de configuración
en protección acreditada.

Trabajo paralelo del 2026-10-08: contratos/pruebas nativas por runtime y
comparación estática de paneles/comandos. La
[comparación operativa](comparisons/operational-panel-commands.md) delimita
las tres entradas de dashboard, sus recursos y 18/94 cuerpos de comandos
leídos. Dependencias pendientes, cero fichas globales cerradas y cero nuevas
integraciones de aquel bloque de investigación. Las propuestas reutilizan
doctor, journal, ledger y medidor, con estados desconocidos y lectura como base.

El siguiente bloque operativo consolida [acciones prioritarias en doctor](comparisons/commands-diagnostics.md)
y [declaraciones de hooks por runtime en el panel](comparisons/panel-hook-contracts.md).
La ficha C030 se completa por su cuerpo, motor y callers pertinentes; la
lectura histórica de 18 cuerpos no se convierte en 18 fichas terminadas.
El panel distingue procedencia, timeout de registro y presupuesto del adapter;
la carga y ejecución permanecen desconocidas sin observación compatible.
Ambos bloques quedan aceptados por revisión A+B+D y [QA final](panel-command-qa-evidence.json),
con B1 corregido y sin gaps pendientes. No cierran T-05/T-13 globales ni la
investigación de memoria; las skills permanecen aplazadas. Por petición expresa
del usuario se publica este bloque y se detiene el trabajo antes de otra fase.

## Memoria: valoración inicial y comprobaciones pendientes

### Dirección de diseño aceptada por el usuario

El 2026-10-08 el usuario aceptó la recomendación de memoria:

1. Mantener la memoria local versionada como base canónica.
2. Mejorar primero la captura fiable y la recuperación local.
3. Incorporar propuestas de aprendizaje con evidencia y revisión, usando
   los servicios de memoria existentes.
4. Conservar Kwipu como proyección documental y evaluar Graphiti para
   relaciones e historial con consultas reales y métricas comparables.
5. Condicionar cualquier ampliación del backend a los resultados medidos.

Es una decisión de dirección, no evidencia de implementación ni de benchmark.
El siguiente bloque operativo sigue siendo hooks en los tres runtimes,
incluida la captura durable que sostiene la continuidad de memoria.

La [comparación S053–S054](comparisons/skills-session-learning-memory.md)
ya distingue captura por tool, propuestas pequeñas con trigger/evidencia y
evolución hacia piezas reutilizables. Parte de la automatización anunciada
no está implementada; el observador puede archivar eventos que no analizó.
Conservar lo útil exige lotes confirmados, procedencia y revisión; frecuencia
o confianza declarada no equivalen a aprobación ni calidad calibrada.

| Componente | Contrato observado | Valor y límite para el bloque |
|---|---|---|
| Journal/ledger | Continuidad y registro del trabajo | Capturar y retomar con fuentes; no convertir todo el historial en instrucciones |
| Markdown curado | Conocimiento versionado y estados explícitos | Mantener como base canónica; precisar propuesta, persistencia y aprobación |
| Kwipu | `markdown_export.py` publica y verifica; no expone `consultar`/`puede_leer` | Proyección documental; el plugin no obtiene recuperación enrutada mediante este adaptador |
| Graphiti | `consultar` y `puede_leer`, con modo `read`, salud y verificación | Candidato para relaciones y vigencia; requiere medir utilidad/coste en este proyecto |
| Aprendizaje de sesión | Captura y candidatos con trigger/acción/evidencia | Complementar la memoria curada; no activar otro escritor ni aprobación automática |

Fuentes propias contrastadas por lectura dirigida:
[exportador Kwipu](../../../skills/knowledge-services/backends/markdown_export.py),
[adaptador Graphiti](../../../skills/knowledge-services/backends/graphiti.py),
[router](../../../agent-kits/shared/knowledge-find.py) y
[reconciliación propuesta](../../knowledge/adr/ADR-020-graphiti-reconciliador-explicito-y-episodios-sin-uuid.md).
El router exige consulta/permiso de lectura, acota al grupo de proyecto y
degrada a local ante indisponibilidad. Esto describe código leído, no una
conexión actual ni una prueba de eficacia. La auditoría detectó que la
documentación de [knowledge-services](../../../skills/knowledge-services/SKILL.md)
presentaba Graphiti como futuro y toda consulta como externa. El Bloque 7
reconcilia ese texto con las funciones existentes, sin cerrar T-07/T-15 globales.

[Graphiti oficial](https://github.com/getzep/graphiti) documenta relaciones,
procedencia y vigencia temporal con recuperación híbrida; requiere operar
la infraestructura y comprobar el rendimiento de la instalación propia.
No se atribuyen al adaptador todas las capacidades del framework por nombre.

La medición de fase 4 debe comparar el mismo conjunto de consultas sobre
decisiones vigentes, cambios históricos, evidencias y retoma del trabajo:
aciertos con fuente, errores obsoletos o de otro proyecto, omisiones, latencia,
contexto y coste observado. Incluir revocación, reconstrucción, duplicados,
backend caído y respaldo local. La prueba de publicación no sustituye este
benchmark. No se activan servicios, conectan cuentas o cambian datos de memoria
por esta valoración; la selección del backend queda condicionada a resultados.

## Continuación: cierre y documentación de memoria

Tras publicar los Bloques 5/6 y detenerse, el usuario pide continuar. El Bloque 7
reconcilia el mapa de knowledge-services con las funciones ya existentes: Kwipu
proyecta/verifica; Graphiti permite lectura explícita `read` con sus puertas de
salud/verificación y respaldo local. Los proveedores orientan al servidor, sin
acreditar modelos efectivos o costes. No se añaden skills ni se activa un backend.

El [diagnóstico reducido de SessionEnd](session-closure-diagnosis-evidence.json)
conserva tres cohortes separadas. Dos cierres instrumentados completan captura
en 1251 y 1492 ms; el segundo no usa turnos ni solicita al proveedor. El intento
de override con shell anidado falla por comillas y se rechaza como mejora.
Las fuentes instrumentadas y originales conservan hashes distintos.

El mínimo no reproduce el timeout histórico bajo carga de subagentes. No hay
hipótesis causal probada: producción y presupuestos permanecen intactos. La
fiabilidad del cierre sigue abierta; esos éxitos no convierten en verde los
fallos anteriores ni prueban durabilidad general de memoria.

La [QA dirigida del contrato de memoria](memory-contract-qa-evidence.json)
valida 403 pruebas de memoria y 35 de exportación en una copia con Git y homes
propios, sin bytecode. Se corrigen únicamente fixtures LF en Windows y la
comprobación de relaciones completas; el lector y el scanner permanecen intactos.
El [contraste causal](memory-contract-test-diagnosis-evidence.json) conserva
los intentos rechazados y distingue cada entorno. No valida toda la suite
del repositorio ni mide eficacia de recuperación o cierre nativo bajo carga.

## Entregas posteriores y siguiente puerta

El bloque 8 incorporó memoria aprobada a la recuperación local, conservando
ID, versión, evidencia y autoridad tanto en caché como en lectura plana y
respaldo local. [Evidencia de recuperación](memory-approved-retrieval-evidence.json).
Los cuatro [cierres con carga](session-closure-load-evidence.json) conservan
una pérdida de guardia y un cierre de 3.075 ms registrado como completed:
no acreditan una latencia universal ni resolver la degradación bajo carga.

El bloque 9 hace explícita la entrega de decisiones y los fallos del evaluador
en los tres runtimes, preservando los bloqueos completos y corrigiendo el
límite Unicode. [QA y diagnóstico](guard-delivery-evidence.json) y
[aviso nativo Codex](guard-warning-native-evidence.json) separan tests del
launcher, comparación de arranque y fixture con demora deliberada. No cambia
intérprete, presupuestos, políticas de permisos ni conexiones de memoria.

Los bloques 10–12 entregaron ajustes de arranque, captura canónica y preservación
de verificación Git; sus evidencias y límites están en el ledger. La aceptación
global del despacho y cierre nativos sigue abierta. El bloque 13 aborda la retoma
dirigida como consulta local independiente: no añade captura, permisos ni backends
y no necesita atribuir fiabilidad nueva a los hooks. Sus puertas de lectura,
selección y composición se validan por separado antes de publicar.

La retoma dirigida ya tiene [QA y evidencia propia](work-resume-evidence.json):
Windows y Linux, selección exacta, ledger vigente, historial citado y lectura
acotada. `/work-resume` y sus exports comparten el compositor. No sustituye la
aceptación nativa pendiente ni cambia el contrato de captura.

Después quedan los controles del panel y la medición del backend opcional.
Una entrega parcial no completa una tarea global. Nuevas skills siguen
aplazadas en 79/293, con 214 pendientes.

## Panel operativo y revisión visual

Dirección del usuario del 2026-10-09: acercar el dashboard al seguimiento e
interacción operativos. La comparación [de actividad](comparisons/panel-activity.md)
confirma polling y sesiones del runner, con acciones de memoria y tablero;
no demuestra descubrimiento automático de todos los subagentes nativos.
La [revisión de planes](comparisons/panel-plan-review.md) confirma una UI real
con comentarios, aprobación y solicitud de cambios consumidos por el agente.

Tras cerrar diagnóstico explícito: servidor local y proyección del ledger;
observaciones opt-in por runtime y cronología; revisión visual con decisiones
versionadas; acciones de memoria/tablero por sus dueños existentes. Se puede
investigar cada contrato en paralelo, conservando esa dependencia de integración.
No se confunde actualización del ledger con ejecución actual ni se introduce
otra base de tareas/planes. T-08/T-11/T-13 siguen abiertas; ninguna de estas
ampliaciones operativas se declara entregada por documentar su diseño.

La QA del bloque 14 identifica además una limitación previa del diagnóstico
general: rutas largas se recortan antes del nombre de archivo en errores de
capacidad. Base y código actual reproducen el mismo resultado. El diagnóstico
portable no exporta esos detalles. Corregir la presentación de ese mensaje
pertenece al siguiente bloque de comandos, con test de ruta larga propio;
no se cierra ese criterio por usar fixtures cortas en la QA dirigida.

El bloque 14 entrega ya diagnóstico explícito en el panel, con informe
portable redactado y validación de proyecto, fecha y límites. La
[QA propia](panel-diagnostics-evidence.json) conserva Windows 1000 passed/
9 skips, Linux 1007 passed/2 skips, Edge 16/16 y cobertura del diff 95,41%;
también el rechazo previo y su contraste causal. Es una entrega parcial de
T-13/T-15: no activa servicios ni convierte el informe histórico en actividad
actual. La siguiente implementación integra servidor local y vistas canónicas;
después, observación por runtime y revisión visual consumible desde comandos.

Prioridad ratificada por el usuario: revisión de comandos, dashboard y memoria.
El bloque 15 implementa transporte de lectura y progreso local, y corrige el
nombre de archivo en errores largos de doctor; requiere QA y revisión antes
del push. La [consulta de memoria](comparisons/memory-command-contract.md)
queda acotada como siguiente entrega explícita: nada de búsquedas, generación
de candidatas o sincronización automática desde polling. Se conserva la
separación continuidad/conocimiento/contexto estructural. Benchmark local y
comparación opt-in de backend continúan pendientes; no se reclama utilidad
demostrada por los tests de contratos. Nuevas skills y ampliación de hooks
permanecen aplazadas conforme a la prioridad actual.

El contraste de memoria incluye explícitamente Kwipu, Graphiti y Graphify,
frente al control local y a la recuperación/aprendizaje de referencia. Hay
despliegue Docker existente: documentación autorizada y health acotados ya
comprobados, sin consultas o cambios de datos. La documentación describe
inferencia cloud por defecto; health y modelos disponibles no acreditan
recuperación ni la configuración efectiva. La selección final de componentes
depende de benchmark sintético aislado y pruebas de autoridad, persistencia
y reconstrucción; no se decide una sustitución por leer un README.
