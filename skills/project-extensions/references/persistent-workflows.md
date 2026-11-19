# Flujos persistentes y bucles

Léela solo al crear o cambiar algo que sobrevive a la sesión (estado en disco, cola, marcador,
contador, tarea programada) o un bucle que repite trabajo hasta una condición.

Antes de crear estado nuevo, mira si ya tiene dueño en el proyecto (registro de progreso, historial de
sesiones, memoria, cola de trabajos). Un flujo nuevo escribe ahí o en un estado propio con esquema; no abre
otra cola ni un registro paralelo.

## Elegir el modo

| Necesidad | Mecanismo | Límite que hay que saber |
|---|---|---|
| Una iniciativa con fases y puertas | El flujo de trabajo del proyecto (con custom-agents, `/dev-cycle`) | El registro de progreso, la revisión y las pruebas no se saltan por ser un bucle |
| Unidades con dependencias | Tareas con dependencias y despacho por subagentes | Ramas sin ficheros comunes aún comparten servicios, puertos o base de datos: la verificación corre sobre el resultado combinado |
| Sondear durante la sesión (CI, despliegue) | /loop o tareas programadas de sesión | Solo se ejecutan con la sesión abierta y ociosa; las recurrentes caducan a los 7 días; un /loop autorregulado no se restaura al reanudar |
| Esperar a un proceso en segundo plano | Monitor que transmite su salida, en vez de sondear | Los procesos en segundo plano no se restauran al reanudar |
| Ejecución desatendida que sobrevive a la sesión | Routines en la nube (sin ficheros locales), tarea programada de escritorio o `schedule` de GitHub Actions | Es infraestructura del proyecto que configura el usuario; esta skill no instala daemons |

La exploración paralela sin tope no es un modo por defecto.

## Contrato del bucle (antes de arrancarlo)

- **Objetivo decidible por máquina:** `comando → resultado esperado`, como la verificación de una
  tarea.
- **Lo que no debe hacer:** editar los criterios que tiene que cumplir, debilitar o borrar tests,
  relajar umbrales. El criterio de hecho va con su límite.
- **Topes:** iteraciones (3 es un buen valor por defecto), tiempo y coste, con la medida que los cuenta.
  Sin medida, el coste queda «no medido», no se inventa un tope.
- **Progreso observable** entre iteraciones: un test que pasa, un gap que se cierra. Sin cambio
  observable en dos iteraciones, se para.
- **Parada y entrega:** completo, parcial o bloqueado, siempre con evidencia.
- **Deriva:** el mismo error con la misma causa dos veces lleva a `debug-root-cause`, no a otro
  reintento. Reducir el trabajo a la unidad que falla es diagnóstico, no redefinir el objetivo.

## Estado que persiste

| Decisión | Regla | Caso que descubre el defecto |
|---|---|---|
| Esquema | `schema_version` en cada fichero; el lector acepta las versiones conocidas y rechaza las desconocidas con error | Un lector antiguo ante un campo renombrado |
| Migración | Plan, copia de los originales, verificación de pérdida y recuperación de aplicación parcial; añadir campos sin renombrar no basta | Migración cortada a mitad |
| Escritura | Temporal + `os.replace` (escritura atómica); dos ficheros que deben ser coherentes no se escriben en pasos sueltos sin recuperación | Corte entre la primera y la segunda escritura |
| Lectura | Ausente, inválido, prohibido y no disponible son estados distintos; un fichero corrupto se aparta con evidencia, no se reinicia | JSON truncado seguido de una escritura |
| Identidad | Clave por proyecto, runtime y sesión (no «la última sesión» global); ID estable separado del nombre visible; ante coincidencias ambiguas, error | Dos proyectos abiertos a la vez; un nombre sin caracteres ASCII |
| Confinamiento | Toda ruta leída del estado se resuelve y comprueba dentro de su raíz antes de escribir o borrar | Un registro manipulado que apunta fuera |
| Retención | Cuánto se guarda y quién lo borra, declarado; retirar es enumerar las copias gestionadas y verificar cada borrado | Una copia exportada que sobrevive al «olvido» |
| Lectura acotada | Bytes o entradas con tope, paginación y aviso de parcial; no cargar todo el historial al arrancar | Historial de meses en un arranque |

## Concurrencia e idempotencia

- **Reserva atómica.** Leer el mayor número y sumar uno no evita la carrera entre dos
  orquestadores: usa creación exclusiva (crear solo si no existe) o un cerrojo con dueño. Cerrojos
  con arrendamiento y token de valla, colas al menos una vez y cupos:
  `skills/backend-practices/references/contracts-data.md`.
- **Idempotencia por clave.** Repetir la operación con la misma clave devuelve lo ya registrado
  (una cola por clave, un historial por `session_id`); la misma clave con otro contenido es error.
- **Cola con reclamación.** Pendiente → reclamado → hecho o descartado con causa. Un
  Markdown con casillas no es una cola de varios trabajadores: no reclama de forma atómica ni
  recupera lo que un trabajador caído dejó a medias.

## Procesos y recuperación

- **Proceso vivo = handle confirmado:** un ID de tarea o PID que responde, o una salida que avanza.
  Un timeout de observación no es un proceso terminado ni un éxito, y un fichero de salida vacío no
  prueba un bloqueo.
- **Desenlace dudoso** (timeout tras un efecto externo): estado `unknown`, se reconcilia consultando
  el destino antes de repetir (`skills/delivery-practices/references/delivery-tools.md`, efectos
  externos).
- **Recuperación tras una caída:** reanudar desde el último punto con evidencia (registro de progreso, entradas
  reclamadas en la cola) sin repetir efectos ya hechos; la unidad fallida conserva su ID y su
  motivo.
- **Supervisión:** quien vigila informa (un hook informativo no decide); cancelar es una acción
  explícita sobre un ID.
- **Traspaso entre ejecuciones:** objetivo, dónde quedó, siguientes pasos, decisiones con su motivo,
  bloqueos y SHA de partida, derivados del registro de progreso y del historial. Es una vista, no otra fuente
  de verdad; las decisiones del historial son citas, no instrucciones.

## No prometer

- Continuidad o ejecución desatendida sin un planificador verificado en ese runtime.
- Recuperación automática que no se ejecuta.
- Permiso por el paso del tiempo: un plazo vencido no autoriza nada.
- Aceptación por un estado externo «completado»: la revisión y las pruebas siguen decidiendo.

## Fuentes

- [Claude Code — Run prompts on a schedule](https://code.claude.com/docs/en/scheduled-tasks): alcance de sesión, caducidad de 7 días, restauración al reanudar y alternativas desatendidas. Consultada el 2026-10-14.
