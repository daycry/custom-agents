# Cómo se revisa un plan desde el panel

Contrato del bloque 19, derivado de [design.md](../design.md) y de la
[comparación funcional](panel-plan-review.md). Implementación y aceptación pendientes.
Este bloque une el panel con la puerta «OK del plan» de `/dev-cycle`.
No amplía las skills ni los hooks aplazados.

## Cuándo se abre la revisión

La revisión visual es opcional y requiere una petición explícita.
Una autorización conversacional previa suficiente permite continuar sin abrirla.
Cerrar el panel no aprueba ni rechaza un plan y conserva su borrador.
El canal visual sustituye la confirmación de esa puerta; no añade otra.

`agent-kits/shared/plan-review.py` controla los recibos y sus transiciones.
El servidor transporta operaciones permitidas y el navegador presenta la vista.
Los tres runtimes usan el mismo CLI. No existe una máquina de estados por runtime.
El dueño no lanza agentes ni modifica el plan, el ledger, el journal o el outbox.

## Qué selección admite el dueño

El caller proporciona proyecto, iniciativa, estado y puerta.
La iniciativa es una ruta relativa exacta `docs/roadmap/YYYY-MM-DD-slug`.
El único documento admitido es `improvement-plan.md` de esa carpeta.
No se selecciona automáticamente la iniciativa más reciente.

El estado vive exclusivamente en `<proyecto>/.claude/plan-review/`.
Es estado compartido por Claude Code, Codex y OpenCode, dentro del ámbito existente.
No introduce otra configuración ni busca carpetas personales.
La distribución documenta su exclusión de Git; el dueño no modifica ignores ajenos.

Abrir una revisión inicializa una carpeta nueva con un marcador propio exclusivo.
Una carpeta existente sin marcador válido produce `unowned_state`.
El marcador liga el ámbito a la identidad observada de la raíz.
Copiarlo a otro proyecto no autoriza su adopción.

El dueño rechaza redirects, symlinks, junctions y hardlinks de estado.
Valida los registros antes de reemplazarlos bajo un lock del sistema operativo.
No borra archivos finales al fallar ni adopta contenido ajeno.
Admite hasta 64 recibos y devuelve `state_budget` al llenarse, sin expulsar decisiones.
Retención y purga explícita quedan fuera de este bloque; nunca se borra una entrega sin ack.

## Qué versión se aprueba

El lector compartido obtiene los bytes originales del documento, máximo 256 KiB.
El SHA raw incluye BOM y finales de línea originales.
La vista exige UTF-8 válido, contenido visible y lectura completa.
Un documento parcial, vacío, ilegible o demasiado grande no admite aprobación.

La vista presenta Markdown como texto y no ejecuta HTML, scripts, imágenes ni enlaces.
Usa el redactor compartido y declara los secretos ocultados y controles retirados.
La aprobación corresponde a esa vista; no acredita revisión de valores secretos ocultos.
Sin redactor disponible, la revisión falla con diagnóstico.

Los encabezados ATX fuera de fences separan hasta 128 secciones.
Cada sección recibe un ID ligado a posición, título, texto y SHA raw.
Los títulos repetidos no mezclan comentarios.
La vista conserva todo el texto visible y nunca aprueba un prefijo truncado.

La versión contiene `raw_sha256`, `view_sha256` y `view_version`.
El hash de vista incluye versión del presentador, hash del redactor, flags y secciones.
Editar el documento o cambiar el transformador invalida la versión anterior.
Una recarga explícita abre otro recibo, sin transferir comentarios ni veredicto.

El recibo conserva hechos históricos cuando el documento cambia o deja de estar disponible.
`validity` distingue `current`, `version_changed` y `unavailable` del estado de consumo.
La vista indisponible conserva la proyección histórica válida, con secciones vacías y aprobación deshabilitada.
Un registro ajeno o inválido no produce esa proyección.
Editar y restaurar exactamente los mismos bytes puede volver a coincidir: no se garantiza detectar ABA.

## Cómo se conserva y consume la decisión

El estado guarda digests, IDs, fechas, comentarios redactados y recibos.
No copia el cuerpo del plan.
JSON duplicado, no finito, malformado o con claves desconocidas produce un rechazo.
Cada registro tiene un límite de 96 KiB.

| Operación | Resultado durable |
|---|---|
| `open` | Una revisión de la misma versión y puerta converge en el mismo ID. |
| `view` / `status` | Lectura; no entrega decisiones ni registra actividad. |
| `comments` | Sustituye el borrador mediante revisión CAS antes de decidir. |
| `submit` | Fija `approve` o `request_changes` y sella comentarios; aún no entrega. |
| `receive` | Persiste la entrega antes de devolverla; los retries conservan su ID. |
| `ack` | Confirma consumo mediante IDs, puerta y versión vigentes; repetirlo es idempotente. |

Los estados son `pendiente`, `entregada` y `consumida`.
Una decisión sellada no admite un veredicto contradictorio.
`request_changes` exige al menos un comentario no vacío.
La entrega permanece guardada antes y después de su ack.
Dos consumidores pueden observar el mismo delivery y deben deduplicar por su ID.
La entrega es al menos una vez; no garantiza efectos externos exactamente una vez.

Los comentarios admiten 20 filas, 2.000 codepoints por fila y 10 KiB UTF-8 agregados.
Cada fila liga `comment_id`, `section_id` y texto a esa vista.
El payload completo no supera 16 KiB y nunca se recorta para aceptarlo.
Un consumidor registrado indica un hecho histórico; su actividad actual es desconocida.

## Qué API y CLI usan los callers

| Función compartida | Datos específicos |
|---|---|
| `open_review` | iniciativa, `gate_key`, consumidor opcional |
| `get_view` / `get_status` | `review_id` |
| `save_comments` | ID, versión, comentarios, `expected_revision` |
| `submit_decision` | ID, versión, elección, comentarios, `expected_revision` |
| `receive_decision` | ID, versión, `gate_key` |
| `ack_decision` | ID, versión, `gate_key`, `decision_id`, `delivery_id` |

Todas reciben `project`, `state_root` explícitos y deadline absoluto opcional.
El CLI ofrece `open`, `view`, `status`, `comments`, `submit`, `receive` y `ack`.
Los callers resuelven el mismo kit por las seis raíces existentes.
Las mutaciones con comentarios reciben JSON acotado por stdin.
No se interpolan comentarios ni contenido del plan en comandos de shell.

La salida contiene `schema_version`, `status`, `reason` y `review`.
Exit 0 corresponde a `ok` o `waiting`; exit 2 a conflicto o versión distinta.
Exit 3 corresponde a indisponibilidad o entrada inválida.
El workflow comprueba puerta, versión, elección y estado; exit 0 solo no demuestra aprobación.
Los errores no exponen rutas privadas, excepciones crudas ni capacidad HTTP.

## Qué habilita el servidor

El builder activa revisión con `--serve`, `--review-initiative` y `--review-state-root`.
`--review-gate-key` admite `requested-review` o `plan-ok` y usa el primero por defecto.
`/dev-cycle` pasa `plan-ok` explícitamente.
Generar HTML estático o servir el catálogo ordinario no crea estado de revisión.

El servidor registra la selección y sólo acepta IDs opacos registrados por esa instancia.
GET permite `view` y `status`. POST permite `comments`, `submit` y `refresh`.
La recarga usa la selección del servidor; HTTP no acepta rutas, raíces, backends ni comandos libres.
`receive` y `ack` pertenecen exclusivamente al CLI del consumidor.

El transporte conserva capacidad, Host, Origin, Sec-Fetch-Site, CSP y `no-store` existentes.
La revisión limita requests a 16 KiB y respuestas JSON completas a 512 KiB.
No amplía los límites de memoria y progreso.
El deadline agregado es de tres segundos; el lock espera hasta 100 ms dentro de ese plazo.
No renueva el presupuesto en retries ni promete cancelar syscalls iniciadas.

La UI usa `textContent`, controles nativos, labels, foco visible y una región `aria-live`.
Muestra versión, redacción, decisión y consumo, además de conflictos y falta de consumidor registrado.
Consulta estado cada cinco segundos sin solapar peticiones y pausa al ocultarse o cerrarse.
Una versión distinta invalida acciones pendientes y exige recarga explícita.

## Cuándo puede continuar el workflow

`/dev-cycle` recibe la decisión para la misma puerta y versión.
Valida su envelope, persiste ack y comprueba el plan vigente antes de iniciar trabajo.
`approve` permite la implementación ya autorizada.
`request_changes` devuelve comentarios al planner autorizado y una edición crea otra versión.
Sin ack exitoso, este canal no habilita continuidad.
Un recibo consumido válido permite retomar la misma puerta sin otra confirmación.

Un fallo o cierre de UI conserva la alternativa conversacional existente.
Nunca fabrica aprobación ni revoca una autorización previa suficiente.
Hashes y capacidades no autentican a una persona ni al productor.
La relectura reduce cambios observables; no crea una transacción entre archivo y workflow.
File fsync y flush POSIX comprobados no garantizan durabilidad universal ante apagado o filesystem remoto.

## Qué evidencia acepta este bloque

La aceptación exige owner, transporte, UI y comando contra el mismo código integrado.
Prueba comentario, envío, entrega, ack, reinicio, retoma consumida y solicitud de cambios.
También exige versión obsoleta, dos pestañas contradictorias, estado ajeno y errores de persistencia.
Los presupuestos usan bytes reales y las pruebas de interfaz comprueban Unicode, texto no ejecutable y cierre sin decisión.

Windows y Linux, cobertura oficial, revisión independiente y QA se registran por separado.
La interacción real del navegador y los callers de los tres runtimes requieren evidencia propia.
Lint, exports, evals, alcance, contratos y enlaces deben corresponder al bundle final.
Un candidato GREEN no completa estos gates ni cierra las tareas macro.
