# Revisión independiente — intento 2

Misma base y alcance que el intento1; se transfirió su tabla completa, sin
hallazgos descartados. Implementación ROOT y cuatro lentes frescas genéricas.

| Gap | Veredicto independiente |
|---|---|
| A-01 | Corregido: mapa Confluence200 líneas y siete reglas de interacción preservadas en referencia |
| A-02 | Corregido funcionalmente: documenter, ROLES y CONTRACTS seleccionan el puerto |
| A-03 | Corregido: Markdown obligatorio; PDF/panel solo disponibles y solicitados, sin relajar gates |
| B-01 | Corregido: edición concurrente preservada, guard antes de cada rename, sin fallback in-place |
| D-01 | Corregido: checkpoints por grupos, coste lineal; sin nuevos hallazgos de rendimiento |

Lente A ejecutó `export-interop --check`: exit0,88 archivos al día; scope-check
exit0, fuera de alcance vacío. Python desacoplamiento/propiedad23passed y Node
perfiles6passed. Señaló A-04Minor: dos espejos FLOWS todavía atribuían al core
el routing de la referencia Jira antigua. Se corrige la frase en ambos espejos.

Lente C: sin hallazgos confirmados. Ensayos aislados: modificación concurrente
preservada; hardlink y junction cambiada rechazados; tres EBUSY sin fallback;
guard repetido en reintentos. Symlink de archivo no disponible por permisos Windows.

| Benchmark posterior al arreglo D-01 | Archivos | Checkpoints | Bytes | Segundos |
|---|---|---|---|---|
| Sin perfil | 510 | 8 | 362434 | 3.416 |
| full | 510 | 8 | 1157745 | 8.373 |
| core | 353 | 8 | 775726 | 6.579 |
| Reinstalar full | 510 | 8 | 1308750 | 9.345 |
| full a core | 353 | 8 | 886206 | 6.369 |

No son SLA ni comparación de latencia limpia entre versiones: acreditan la
desaparición de la amplificación de escrituras anterior.

## B-02 — Important nuevo: recuperación de propiedad tras interrupción

La revalidación protegía la edición concurrente, pero el manifiesto incompleto
guardaba el hash final de archivos aún no copiados. En un upgrade interrumpido,
un archivo propio antiguo intacto ya no coincidía con el mapa. El revisor reprodujo
install0 → upgrade1 → retry1 → uninstall0 con archivo antiguo huérfano; también
SIGTERM143 seguido de retry1. No reabre B-01: la edición sí se conservaba.

Regresión dedicada observada roja: `gap B02: an aborted upgrade can retry without
adopting or orphaning unchanged old files`. Se reproduce después otra arista roja,
`SIGTERM during module retirement keeps ownership and resumes the selected profile`.

Corrección: un manifiesto incompleto conserva los hashes propios anteriores y
planificados, incluidos archivos de módulos aún no retirados. Solo se admiten
esos bytes verificados; una edición diferente sigue rechazándose. Se revalida la
retirada y se aborta si cambia. La instalación completa elimina el historial
provisional. Retry y uninstall pueden reconocer los archivos antiguos intactos.

Después: cuatro regresiones CLI B-01/D-01/B-02/retirada SIGTERM pasan. Se solicita
revisión final intento3; B-02 no se declara aceptado por el autor de la corrección.

Los TEMP propios de los ensayos se conservan; no se repitió la limpieza recursiva
rechazada por la revisión automática en el intento1. No hubo conexiones ni cuentas reales.
