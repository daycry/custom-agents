# Retomar una iniciativa o sesión

[English](en/WORK-RESUME.md) · **Español**

`/work-resume` muestra dónde continuar a partir del ledger actual y del journal
local. `progress-report.py resume` compone la vista; `journal.py` selecciona
el historial. Ambos usan el lector local acotado. La vista no modifica el proyecto.

Con `--json`, el comando devuelve el objeto completo que imprime el compositor,
incluido `status`, sin reconstruirlo ni añadir prosa. Una selección ambigua conserva
los candidatos y espera otra petición. El compositor se ejecuta también sin filtros;
la fachada no deduce la selección leyendo los planes por su cuenta.

## Cómo seleccionar el trabajo

Usa la forma del comando que ofrece tu instalación: `/custom-agents:work-resume`
en Claude Code como plugin, el prompt exportado en Codex y `/work-resume` en OpenCode.
El cuerpo y los contratos son comunes. El comando no activa un equipo ni un ciclo.

```text
/work-resume --initiative 2026-01-01-demo
/work-resume --initiative demo --session-id sesion-demo --runtime codex
/work-resume --entry 2026-01-01-demo.md --json
```

| Opción | Selección |
|---|---|
| `--root` | Raíz explícita del proyecto para el script; el comando usa el proyecto de trabajo. |
| `--initiative` | Carpeta fechada exacta bajo `docs/roadmap/` o slug único. Dos carpetas con el mismo slug requieren elegir carpeta. |
| `--session-id` | Igualdad con el ID completo del journal. No acepta prefijos como alias. |
| `--runtime` | Filtro explícito `claude`, `codex` u `opencode`. Un registro antiguo sin runtime permanece desconocido. |
| `--entry` | Nombre exacto de un Markdown bajo `docs/knowledge/journal/`; no acepta una ruta externa. |
| `--json` | Proyección estructurada con los mismos estados y avisos de la vista de texto. |

Los filtros combinados deben coincidir. Un fichero o ID explícito ausente, inválido
o ambiguo no se sustituye por el último registro. La selección compara datos
originales antes de sanitizar y redactar la salida. Los candidatos mostrados pueden
tener identidades recortadas; ese recorte no prueba el valor original.

Sin filtros, el resolver usa una única iniciativa con estado `en-progreso`.
Varias iniciativas activas dejan una selección ambigua. Ninguna deja la selección
ausente, incluso cuando exista historial global de otras iniciativas.

## Qué manda al retomar

La primera parte muestra la iniciativa, fase y tareas del `tasks.md` actual.
Ese ledger conserva la autoridad sobre el estado del trabajo. A continuación
aparece la curación observada desde sus asociaciones explícitas. Al final,
el historial muestra fecha, sesión, fuente, cierre y contenido disponible del journal.

Decisiones y pendientes del historial son **citas**, no instrucciones. Una sesión
antigua no prueba que una tarea siga abierta ni que haya pasado QA. La vista no
inventa objetivos, errores, bloqueos o próximos pasos que el esquema no contiene.
El usuario decide qué acción ejecutar después.

La sección de curación consulta únicamente las referencias que el dueño registró
en el ledger mediante [knowledge-write.md](../agent-kits/shared/knowledge-write.md).
No busca candidatos por recencia, nombre o journal. Una asociación ausente es
`not_registered`; un bloque inválido es `corrupt` y no provoca lecturas de memoria.
Los conflictos, errores de lectura y búsquedas incompletas conservan su motivo.

Por referencia, `pending` indica candidato observado u operación sin recibo;
`missing` distingue candidato u operación ausente; `changed` señala diferencia de
SHA/asociación; `corrupt` indica un recibo inválido; `unknown` conserva ambigüedad
o IO no verificable. `completed` con
`reason: completed_receipt_observed` acredita el recibo validado de persistencia,
no la vigencia del contenido approved ni QA (`target_content_verified: false`).
La vista no limpia staging, repara estado o recupera operaciones. Esa acción
requiere una invocación explícita del dueño existente con su contrato propio.

| Estado | Cómo interpretarlo |
|---|---|
| Ausente | La selección no encontró un registro dentro de una lectura completa. |
| Vacío | El directorio es válido, pero no aporta entradas de historial sustantivas. |
| Ambiguo | Varias carpetas o registros satisfacen la identidad; elige un candidato exacto. |
| Ilegible | El lector no pudo acceder o decodificar el fichero; no equivale a ausencia. |
| Malformado | El contenido no cumple el formato validado del registro. |
| Incompleto | Un tope o un problema de lectura impide confirmar toda la búsqueda; no garantiza ausencia ni recencia global. |

## Cuánto lee y cuánto muestra

El lector limita cada directorio a **128 nombres** y cada fichero a **256 KiB**.
Roadmap e historial tienen presupuestos separados de **1 MiB por corpus**
(hasta 2 MiB combinados). Curación dispone de **1 MiB adicional compartido**
para hasta ocho asociaciones explícitas: hasta 3 MiB combinados. Cada consulta
valida sólo el bucket del candidato, con un máximo de 16 nombres; un operation-id
explícito no recurre a otro registro. No lee cuerpos de approved ni enumera todo
el historial de operaciones. Un recorrido cortado se declara incompleto. El dossier
de texto admite **32 líneas y 6.000 caracteres**; JSON admite **12.000 bytes**.
Son límites del compositor, sin opciones CLI para aumentarlos o reducirlos.
Los avisos conservan el motivo cuando la proyección queda recortada. Cada
referencia mostrada conserva ruta, SHA e IDs completos o declara identidad no
resoluble. JSON publica `curation.references_omitted`; el texto cuenta además
las referencias que omite al seleccionar grupos completos. `output_truncated`
señala también truncamiento de texto aunque el JSON completo quepa.

Los bytes leídos también consumen presupuesto cuando el texto es ilegible o
la ruta cambia. Un fallo durante la lectura reserva la asignación completa;
la detección de crecimiento admite un byte adicional de comprobación por fichero.

El lector rechaza enlaces simbólicos y junctions en la ruta. Permite los marcadores
de archivos de nube admitidos, comprueba identidad antes de leer y acota los bytes.
Estas comprobaciones no forman un sandbox atómico frente a cambios concurrentes
del sistema de archivos. La vista tampoco certifica la identidad de escritura:
un journal antiguo sin runtime no demuestra qué runtime lo capturó.

El lector valida el frontmatter plano del escritor. Los textos se escriben como
cadenas entre comillas con escapes JSON; acepta texto simple heredado sin indicadores
YAML ni valores tipados. No interpreta YAML general, mapas anidados, alias ni bloques.

## Qué ejecuta el comando

Abrir la vista no ejecuta replay ni restaura una copia. El
[contrato de recuperación local](roadmap/2026-10-07-catalog-capabilities/comparisons/memory-local-recovery-contract.md)
explica la confirmación de capturas y la evidencia para recuperar sesiones pendientes.

Solo ejecuta el compositor Python. No usa meter, replay/recover, Git, backends,
red ni procesos de materialización; no lee transcripciones crudas para rellenar
huecos. La captura y la recuperación automáticas siguen su propio contrato de hooks.
En startup/resume, `SessionStart` usa `resume --history-only` para seleccionar
historial con el mismo resolver de ledger; compact omite esa parte.
El bloque de progreso y replay siguen separados. Esta vista no convierte el hook
`SessionStart` entero en una operación de solo lectura.

La fachada resuelve `agent-kits/shared/` en las seis raíces de
[CONVENTIONS §5](CONVENTIONS.md#5-rutas-dentro-del-código). Pasa opciones y valores
como argumentos separados, sin interpolar texto del usuario en shell.
Una instalación parcial comunica el recurso ausente y conserva la selección.

`/work-context` elige guías y extensiones para la tarea. `/roadmap-status` muestra
la cartera. `/work-resume` aporta contexto de continuidad sobre los registros
existentes; no añade una skill, un almacén ni otro workflow de ejecución.

## Revisiones del panel al retomar

El dossier consulta la función local `plan-review.py list_reminders` para la
carpeta exacta del ledger seleccionado. `reviews` conserva IDs completos, puerta,
versión, revisión del registro, estado y contadores de comentarios, respuestas y
verificaciones. El contexto automático omite los cuerpos de comentarios. Una
respuesta ausente sólo significa que no está registrada.

La consulta no crea el almacén, adquiere bloqueos de escritura, abre revisiones,
entrega decisiones ni hace ack. Una decisión registrada o consumida no prueba
aprobación vigente, atención del modelo, QA ni trabajo terminado. Las versiones
antiguas se muestran como `version_changed`. El consumidor explícito existente
sigue verificando versión y puerta antes de usar una decisión.

El almacén admite 64 registros de 96 KiB y la salida hasta ocho referencias;
`reviews_omitted` declara las demás. Dos inventarios y dos observaciones del plan
rechazan cambios detectados. La consulta manual tiene un plazo cooperativo de tres segundos
y la consulta de revisiones del bloque de sesión de 0,75 segundos. Las versiones
actuales se muestran primero y después las antiguas, con prioridad para los
estados pendiente y entregada.
Estos controles no constituyen un snapshot atómico ni detectan ABA. Un marcador
de otro proyecto, registro inválido, ruta insegura, tope o fallo de lectura produce
una observación incompleta, nunca una lista vacía confirmada. `not_registered`
declara ausencia del almacén en la ruta comprobada.

`progress-report.py session` añade hasta tres líneas de observación a su bloque
de 15 líneas. Resuelve una única iniciativa activa con el lector acotado; varias
requieren selección. Conserva referencias enteras y declara detalles omitidos.
El historial `--history-only` mantiene su selección y no consulta las revisiones.

Los presupuestos de roadmap, journal y curación descritos antes no incluyen
las revisiones. Sus dos inventarios válidos leen hasta 12 MiB de registros,
además de hasta 1 MiB de plan/redactor y 8 KiB del marcador de propiedad.
Un inventario incompleto no permite declarar ausencia.

## Lecturas locales estables y consultas sin cachés

En Windows, un cambio exclusivo de ctime durante la lectura permite una sola
segunda lectura del mismo descriptor. Identidad, permisos, número de enlaces,
tamaño, mtime, nacimiento y atributos deben conservarse. Los bytes deben coincidir,
la generación final debe ser estable y los controles de ruta y padres siguen activos.
Ambas lecturas comparten el límite original; `bytes` contabiliza el consumo acumulado.
Si no caben ambas, sigue devolviendo `changed_path`. No reintenta errores de acceso,
cambios de contenido ni cambios ctime en otras plataformas. Estas comprobaciones
no garantizan un snapshot atómico multiarchivo ni ausencia de cambios ABA.

Los CLIs `progress-report.py` y `plan-review.py` desactivan la creación de bytecode
antes de cargar los helpers: consultar un kit local de proyecto no crea `__pycache__`,
incluso sin `-B`. No se eliminan cachés previas. La garantía comprobada se limita a
estas invocaciones CLI y no se extiende a cualquier loader externo.

## Tamaño del ledger y detalle histórico

El ledger que consulta la retoma debe permanecer dentro de 256 KiB. Cuando crece,
el detalle de ejecuciones puede trasladarse a `execution-history.md` en la misma
iniciativa, conservando los bytes originales. Las tareas, estados, criterios y
las revisiones estructuradas que deciden gaps y puertas permanecen en `tasks.md`.
Hay que verificar que brief, selección de revisiones y aprobación producen los
mismos resultados después de separar el detalle. El historial de ejecuciones
se consulta explícitamente; no se carga como contexto automático de retoma.

Los encabezados que actúan como marcadores para comandos o pruebas también
permanecen en el ledger, con su orden original. Pueden enlazar al detalle
archivado. Comprobar solo las revisiones estructuradas no basta: se verifican
los consumidores de esos marcadores y el CLI de retoma sobre la fuente final.
