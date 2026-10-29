# T-01: diagnóstico de estabilidad del 2026-10-29

**Estado: abierto. No se acepta una nueva línea base.**

Se reconstruye el código previo a F1 con `git archive bae4e46` y el benchmark/supervisor de `dc18d94`. Las ocho huellas de fuente registradas en la procedencia original coinciden al permitir LF/CRLF. Otros estados históricos del entorno no se pueden reconstruir. La preparación inicial de esta copia queda fuera de las medidas de hooks.

La primera repetición se interrumpió tras cuatro casos completos correctos (medianas 2.243,550; 3.922,425; 4.523,477; 6.434,319 ms). No completó ninguna de las tres pasadas previstas; solo sobreviven las medianas del progreso, sin muestras crudas. Se conserva como diagnóstico parcial, nunca como estabilidad o aceptación. Ctrl-C terminó los procesos propios; la consulta posterior por las rutas exclusivas de esta ejecución no encontró procesos Python/Node restantes.

Control de aislamiento posterior: cinco muestras medidas y un calentamiento descartado. No sustituye las diez muestras ni los 36 casos por pasada exigidos por el benchmark. Todas las invocaciones del guard de este control terminaron sin error.

| Operación | Mínimo ms | Mediana ms | Máximo ms |
|---|---:|---:|---:|
| Node, proceso completo | 547.574 | 925.304 | 1116.230 |
| Node, uptime al imprimir | 26.847 | 31.234 | 35.432 |
| Node, CPU acumulada al imprimir | 46.000 | 61.000 | 109.000 |
| Preparar fixture | 7.449 | 12.208 | 50.438 |
| Cerrar fixture | 5.996 | 9.460 | 16.914 |
| Guard original, proceso completo | 1016.063 | 1382.168 | 1642.403 |

La preparación y el cierre de la fixture se cronometran por separado y el benchmark ya los excluye del tiempo del hook. El control Node también varía sin ejecutar el plugin. Su uptime/CPU se declaran al imprimir y no cubren todo el lanzamiento/cierre observado desde el padre; no identifican por sí solos una causa única del retraso en Windows. No se atribuye el problema a OneDrive, antivirus, memoria o custom-agents sin aislarlo.

No hay una corrección de código justificada por este diagnóstico. Se conservan los umbrales y la subtarea original de tres pasadas estables de T-01. El ajuste aprobado de CA-01 no se extiende a esta condición. Para cerrarla falta una serie completa estable en las condiciones declaradas; estas muestras no la acreditan.

Fuentes: [procedencia](t01-baseline-replay-provenance-2026-10-29.json), [repetición interrumpida](t01-baseline-replay-interrupted-2026-10-29.json), [control crudo](t01-startup-isolation-2026-10-29.json).
