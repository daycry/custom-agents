# T-15: cierre del Job Object sin otro Python

Decisión **no-go** dentro del alcance aprobado, 2026-10-30. T-16 se cancela;
se conservan el supervisor y los presupuestos actuales. No se ha modificado
código de producción ni añadido dependencias nativas.

El experimento usa Windows 11, Node 23.8.0 y Python 3.13.0. Un Node desechable
invoca el supervisor real sin modificar en modo `run/python`. El negocio de
prueba crea un hijo y un nieto. Un observador externo abre handles de proceso
con permiso SYNCHRONIZE y verifica que los tres están vivos antes de liberar
una barrera. Después comprueba esos mismos handles, sin inferir vida de un PID
ni matar procesos por nombre. El recibo [t15-windows-experiment.json](t15-windows-experiment.json)
incluye fuentes del arnés, comandos reconstruibles, estados y hashes de producción.

| Alternativa | Muestras | Resultado observado |
|---|---:|---|
| Cierre actual, salida limpia | 3 | Helper confirma el job; los tres procesos están terminados al retornar Node |
| Cierre actual, timeout tras preparación | 3 | Igual; límite del helper de 500 ms conservado |
| Salir del propietario Node, limpio/timeout/cancelación externa | 9 | Todos terminan, pero en 6 muestras aún hay procesos propios vivos en la primera comprobación tras retornar Node |
| Cerrar desde el Python contenido | 3 | Marcador anterior al cierre presente; marcador posterior ausente: el propio llamante muere sin confirmar |
| `fs.closeSync` sobre el handle remoto | 3 | `EBADF`; el cierre posterior al salir Node termina el árbol, pero esa llamada no cierra el Job Object |

Las seis confirmaciones actuales tardan entre 141,270 y 166,982 ms desde el
spawn del helper. Las muestras de salida del propietario con procesos aún vivos
llegan a cero en la siguiente observación, aproximadamente 5,3–5,8 ms después.
Es resolución de muestreo, no latencia exacta de terminación. No quedan procesos
propios activos al finalizar ninguna de las 21 muestras. Esto no acredita el
criterio de 100 ejecuciones de T-16 ni garantiza esos tiempos bajo otra carga.

Un primer arnés carecía de la barrera del observador: podía abrir handles después
de la limpieza. Sus 21 resultados se conservan como `initial_diagnostic` y no
se cuentan como aceptación. Las 21 muestras finales exigen que los tres procesos
estén vivos y observados antes de iniciar el terminal correspondiente. La ejecución
final duró 33,4 segundos; la investigación se mantuvo dentro de las dos horas.
La suite sin cambios `python -m pytest -q tests/test_hook_supervisor.py` pasa
sus 15 casos en 0,60 s. TDD n/a: investigación sin implementación productiva.

Microsoft documenta que el último cierre con `KILL_ON_JOB_CLOSE` termina el árbol
y que un miembro no puede aplazar ni gestionar `TerminateJobObject`.
Eso concuerda con las observaciones; la garantía de confirmación antes de devolver
el resultado sigue necesitando un observador fuera del job.
Fuentes: [Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects),
[TerminateJobObject](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-terminatejobobject).

En las superficies públicas examinadas de Node (`process`, `fs`, `child_process`)
no aparece una función de Job Objects/CloseHandle, ni un módulo builtin `ffi`.
Esto es una comprobación acotada, no una prueba de imposibilidad universal.
`fs.closeSync` recibe un descriptor de fichero de Node, no un HANDLE Win32
arbitrario: [documentación de Node 23.8.0](https://nodejs.org/download/release/v23.8.0/docs/api/fs.html#fsclosesyncfd).
Un addon/FFI o un broker externo requeriría otro diseño y presupuesto; este spike
no los introduce. Salir sin confirmar o convertir la limpieza en una suposición
no cumple la garantía equivalente que exige el plan.

La evidencia nueva no convierte en válida la comparación inconcluyente de T-10:
sus siete diagnósticos históricos siguen declarados. No se amplían deadlines,
se ocultan fallos ni se presentan muestras de cierre eventual como confirmaciones.
