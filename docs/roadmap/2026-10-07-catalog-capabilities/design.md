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
