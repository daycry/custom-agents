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
