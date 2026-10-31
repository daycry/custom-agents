---
tasks: control-center
estado: en-progreso
creado: 2026-10-31
verificacion: obligatoria
changelog: Changed
---

# Consola operativa de sesiones y planes

Ledger canónico. Alcance solicitado expresamente por el usuario durante la revisión
del manual: implementación robusta, UI moderna y útil, documentación detallada,
commits, push, PR y release v3.0.0. Se permiten cambios mayores sin retrocompatibilidad.
Las interfaces nativas se verifican; las limitaciones se presentan, no se simulan.
Petición adicional: un único servidor/puerto para todos los proyectos registrados,
espacios de trabajo aislados en servidor y navegador. Sin mezcla de sesiones,
planes, comentarios, memoria ni eventos al cambiar de proyecto. Ámbito local;
compartir por red requiere identidad y autorización, no un simple filtro visual.

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase 1 — Entrega | 5 | 6 | 83.3% |
| **TOTAL** | **5** | **6** | **83.3%** |

## Fase 1 — Entrega

### T-01 — Diseñar la consola y contrastar interfaces nativas

- **Estado**: completado
- **Tipo**: frontend
- **Descripción**: Diseño visual moderno e interactivo para sesiones/chat, cartera/kanban/detalle, actividad y memoria. Comparar interfaces oficiales, capacidades por versión y límites CLI/Desktop.
- **Changelog**: Diseñar la consola y contrastar interfaces nativas.
- **Archivos**: `skills/**`, `agent-kits/**`, `install/**`, `tests/**`, `docs/**`, `commands/**`, `agents/**`, `scripts/**`, `interop/**`, `output/pdf/**`, `README*`, `CHANGELOG*`, `package.json`
- **Verificación**: criterios del plan y evidencia en testing/report.md.

**Criterios de aceptación**
- [x] Comportamiento observado y límites contrastados; pruebas pertinentes y documentación coherentes. No confundir configuración, conexión, envío y confirmación.

### T-02 — Conectar sesiones y conversación por adaptadores

- **Estado**: completado
- **Tipo**: backend
- **Descripción**: Puente local explícito a Claude, Codex y OpenCode con límites, eventos, interrupción y solicitudes de aprobación. Nunca usar shell libre desde HTTP ni inventar acceso a Desktop.
- **Changelog**: Conectar sesiones y conversación por adaptadores.
- **Archivos**: `skills/**`, `agent-kits/**`, `install/**`, `tests/**`, `docs/**`, `commands/**`, `agents/**`, `scripts/**`, `interop/**`, `output/pdf/**`, `README*`, `CHANGELOG*`, `package.json`
- **Verificación**: criterios del plan y evidencia en testing/report.md.

**Criterios de aceptación**
- [x] Comportamiento observado y límites contrastados; pruebas pertinentes y documentación coherentes. No confundir configuración, conexión, envío y confirmación.

### T-03 — Operar planes y tareas desde la consola

- **Estado**: completado
- **Tipo**: frontend
- **Descripción**: Cartera, filtros, kanban, detalles y comentarios vinculados. Iniciar o retomar plan en una sesión elegida; el ledger sigue siendo canónico y el navegador no simula QA ni cierre.
- **Changelog**: Operar planes y tareas desde la consola.
- **Archivos**: `skills/**`, `agent-kits/**`, `install/**`, `tests/**`, `docs/**`, `commands/**`, `agents/**`, `scripts/**`, `interop/**`, `output/pdf/**`, `README*`, `CHANGELOG*`, `package.json`
- **Verificación**: criterios del plan y evidencia en testing/report.md.

**Criterios de aceptación**
- [x] Comportamiento observado y límites contrastados; pruebas pertinentes y documentación coherentes. No confundir configuración, conexión, envío y confirmación.

### T-04 — Mostrar actividad e integraciones con evidencia

- **Estado**: completado
- **Tipo**: backend
- **Descripción**: Estado observado de agentes, skills, tools y MCP con procedencia/frescura, sin inferir actividad del ledger ni guardar razonamiento o transcripciones crudas. Memoria e integraciones opcionales visibles.
- **Changelog**: Mostrar actividad e integraciones con evidencia.
- **Archivos**: `skills/**`, `agent-kits/**`, `install/**`, `tests/**`, `docs/**`, `commands/**`, `agents/**`, `scripts/**`, `interop/**`, `output/pdf/**`, `README*`, `CHANGELOG*`, `package.json`
- **Verificación**: criterios del plan y evidencia en testing/report.md.

**Criterios de aceptación**
- [x] Comportamiento observado y límites contrastados; pruebas pertinentes y documentación coherentes. No confundir configuración, conexión, envío y confirmación.

### T-05 — Verificar experiencia y recuperación

- **Estado**: completado
- **Tipo**: frontend
- **Descripción**: TDD, pruebas de contratos, fallos, reconexión, aislamiento de proyecto, teclado y visual en navegador; docs ES/EN y manual actualizados.
- **Changelog**: Verificar experiencia y recuperación.
- **Archivos**: `skills/**`, `agent-kits/**`, `install/**`, `tests/**`, `docs/**`, `commands/**`, `agents/**`, `scripts/**`, `interop/**`, `output/pdf/**`, `README*`, `CHANGELOG*`, `package.json`, `evals/cases/command-plugin-catalog.json`, `evals/cases/skill-plugin-panel.json`
- **Verificación**: criterios del plan y evidencia en testing/report.md.

**Criterios de aceptación**
- [x] Comportamiento observado y límites contrastados; pruebas pertinentes y documentación coherentes. No confundir configuración, conexión, envío y confirmación.

### T-06 — Publicar v3.0.0

- **Estado**: en-progreso
- **Tipo**: backend
- **Descripción**: Revisar literalmente, commits y push, PR con CI verde, fusión y release mediante scripts/release.py. Autorización expresa del usuario para v3.0.0; no omitir limitaciones de interfaces nativas.
- **Changelog**: Publicar v3.0.0.
- **Archivos**: `skills/**`, `agent-kits/**`, `install/**`, `tests/**`, `docs/**`, `commands/**`, `agents/**`, `scripts/**`, `interop/**`, `output/pdf/**`, `README*`, `CHANGELOG*`, `package.json`, `ci.yml.MANUAL-COPY`, `release.yml.MANUAL-COPY`, `.github/workflows/ci.yml`, `.github/workflows/release.yml`
- **Verificación**: criterios del plan y evidencia en testing/report.md.

**Criterios de aceptación**
- [ ] Comportamiento observado y límites contrastados; pruebas pertinentes y documentación coherentes. No confundir configuración, conexión, envío y confirmación.


RED: test_console_workspaces.py::test_one_registry_contains_independent_workspaces_without_exposing_paths falló por registro de workspaces no implementado · 2026-10-31.
TDD n/a: diseño y documentación.

RED: test_console_state.py: 9 failed; dueño de notas/versionado no implementado · 2026-10-31. Registro de workspaces: 9 passed, 1 skip Windows.

RED: test_console_sessions.py: 6 errores por SessionManager ausente; no existe aún ejecución/conversación con aislamiento · 2026-10-31. Notas y registro:18 passed/1skip.

RED: test_console_transport.py:4 failed por transporte acotado no implementado · 2026-10-31. Manager con fixtures:6 passed; no acredita todavía conexión nativa.

RED: test_console_codex.py:5 failed por adaptador no implementado · 2026-10-31. Transporte real con procesos de fixture:4 passed.

RED: test_console_claude.py:5 failed por adaptador no implementado · 2026-10-31. Codex con esquema/fixtures:5 passed, conexión real aún pendiente.

RED: test_native_extended_windows_path_resolves_to_the_same_project reprodujo native_scope_mismatch observado en Codex real. Se acepta únicamente prefijo extendido de unidad local y se contrasta identidad física; UNC/dispositivos rechazados · 2026-10-31.

RED: test_console_opencode.py:5 failed por adaptador V2 ausente · 2026-10-31. Claude inicialización nativa real correcta en16,85s; no hubo turno de inferencia.

RED: test_replacing_a_registered_root_cannot_reuse_its_authority falló antes del cambio: una carpeta reemplazada en la misma ruta mantenía autoridad. Ahora se contrasta identidad física original por petición · 2026-10-31.
RED: test_control_center_http.py:5 errores por servidor compartido ausente · 2026-10-31.
Inicialización nativa real adicional:Codex2,87s yOpenCode2 1,32s correctos; sesión de prueba OpenCode propia retirada.

RED navegador real: control-center.mjs agotó7000ms esperando selector con2workspaces; la conexión/JS de UI aún no existe (la dependencia y Chromium se corrigieron antes de este rojo válido) · 2026-10-31.
ServidorHTTPmultiproyecto:5 passed.

RED: test_activity_is_an_explicit_snapshot_when_capture_is_disabled detectó el tuple interno sin proyectar. Se reutiliza actividad_runs y el contrato indisponible del dueño, sin inferir agentes vivos · 2026-10-31.

RED: test_direct_workspace_constructor_canonicalizes_the_registered_root reprodujo project_changed de la prueba en navegador con ruta temporal Windows8.3. El constructor ahora fija ruta canónica antes de capturar identidad; la sustitución física sigue rechazada · 2026-10-31.

RED observados antes de corregir:ack de permiso sobrescribía final nativo; descubrimiento elegía codex.exe del proyecto; desconexión ausente; historial parcial oculto; envío por pipe marcado running en lugar de queued. Se añaden identidad de generación, cierre propio, PATH explícito fuera del proyecto y estados diferenciados · 2026-10-31.

RED: test_cookie_from_another_local_port_cannot_authenticate_without_the_header_capability detectó credencial en cookie. Se separa nonce de cookie y credencial de cabecera; cookie sola nunca autoriza · 2026-10-31.

Navegador real: recorrido principal verde (sesión/chat/XSS como texto/permisos/kanban/notas/aislamiento/tema/móvil),19510ms. Capturas privadas generadas para revisión visual. RED adicionales observados: binario de usuario al arrancar desde HOME rechazado por exceso de alcance; modo inválido de backend exponía objeto de configuración. Ajuste acotado del descubrimiento y proyección por enum · 2026-10-31.

RED observados: ocho conexiones todavía arrancando no reservaban capacidad; una pregunta recortada podía enviarse por API; ocho formularios grandes superaban el límite del snapshot; Codex inventaba decisiones cuando la lista nativa era explícitamente vacía (4 failed,16 passed). Se reservan conexiones desde connecting, se validan decisiones en servidor y adaptador, y los formularios incompletos/grandes permiten únicamente cancelar cuando el entorno lo ofrece. RED de navegador: cierre móvil visible en escritorio; corregido ocultando según viewport. El enlace profundo y la respuesta tardía entre proyectos se verifican por separado · 2026-10-31.

GREEN de contratos de sesiones/Codex:20 passed. Segundo RED de navegador: recargar un enlace de plan volvía a otra vista (timeout de tarjetas tras reload). El arranque ahora conserva plan/vista únicamente cuando el enlace identifica un proyecto registrado; una selección ordinaria de otro proyecto vuelve a su cartera, sin reutilizar el plan anterior · 2026-10-31.

GREEN de navegador común:2 recorridos,30447ms total; incluye reload y respuesta tardía forzada sin mezclar proyectos. Export portable/check y selección de módulos:24 passed. RED de transporte: EOF notificaba desconexión sin cerrar el proceso propio y POSIX omitía el grupo si el padre ya había salido (2 failed,6 passed). Se cierra al perder el canal y se termina el grupo propio aunque el líder haya finalizado; Windows conserva su Job privado · 2026-10-31.

RED de snapshots:3 failed por lector asíncrono ausente. La cartera, memoria e inventario se calculan fuera de los handlers HTTP, con4 lecturas globales,96 claves máximas ligadas a proyecto/tipo y sin cola ilimitada; una lectura fallida conserva el dato anterior con fecha original y estado de refresco fallido explícito. No hay caché de autoridad para ejecutar planes: prepare/run releen las fuentes · 2026-10-31.

GREEN de snapshots/transporte/HTTP:19 passed; transporte aislado:8 passed. RED en navegador: el catálogo no reconsultaba tras la respuesta inicial calculating y omitía piezas propias; además un GET tardío de comentarios guardados de T-02 sobrescribía las notas visibles de T-03. El catálogo reconsulta y presenta orígenes/tipos; las notas validan también la identidad de tarea tras la lectura final. Guardar queda deshabilitado hasta recibir la revisión inicial · 2026-10-31.

GREEN de4 recorridos del navegador:51500ms total; notas entre tareas, memoria real de fixture, extensión propia, deep link y respuesta tardía. RED adicional reproducido: el borrador de Nueva idea de Portal aparecía al abrir Facturación. Los borradores de idea ahora se guardan por proyecto en memoria de la pestaña y se restauran únicamente al volver a su proyecto; filtros y fecha de observación se limpian al cambiar. HTTP adicional:9 passed, incluyendo un proyecto lento que no bloquea al otro · 2026-10-31.

GREEN adicional: enlace/borradores aislados en navegador; contratos completos de consola70 passed,1 skip de symlink Windows. RED adicional de sesiones: una respuesta lenta de permisos mantenía el bloqueo global y un envío antiguo fallido sobrescribía la conexión retomada (2 failed,13 passed). El I/O de aprobación sale del bloqueo y cada operación conserva driver/generación; sólo puede actualizar su propia conexión. Mermaid español:31 diagramas compilados con Mermaid CLI12.0.0 y Chromium146, sin errores · 2026-10-31.

GREEN de sesiones tras esas correcciones:15 passed. Chat nativo real en carpeta temporal aislada:Codex/OpenAI28,75s y Claude/firstParty21,86s; recibieron marcador visible y terminal idle,0 operaciones de herramientas, conexiones propias cerradas. No se guardaron mensajes ni datos de cuenta en evidencias; sólo metadatos de resultado. OpenCode mantiene inicialización real validada y no se ejecuta inferencia por el aplazamiento de Ollama · 2026-10-31.

## Revisión de dos lentes — intento 1: Fase 1 (T-01 a T-05) — correcciones en curso

Lentes A+B+C+D genéricas de contexto fresco, como respaldo al rol reviewer;
selección C/D determinista (9/12 motivos). Scope exit0,112 archivos propios,
sin avisos ni exclusiones de usuario. El archivo personal ajeno queda excluido
sin leer su contenido. Snapshot privado inmutable y huellas contrastadas.
La lectura adicional de B completa CSS y toda la prosa ES/EN; C/D revisan sus
dimensiones, sin atribuirse revisión editorial ni visual del PDF.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | A1: estados fallidos de actividad/integraciones ocultos como vacío normal | T-04 | Corregido, pendiente re-revisión | RED de navegador observado; aviso distingue configuración inválida, captura no disponible y lecturas parciales; GREEN |
| 2 | Important | A2: firma de Vista general omite degradación con datos conservados | T-04 | Corregido, pendiente re-revisión | RED de navegador observado; firma incluye degradación y conserva cifras con aviso; GREEN |
| 3 | Important | B1: ack turn/start de Codex sobrescribe finalización rápida | T-02 | Corregido, pendiente re-revisión | RED observado; `test_fast_native_completion_is_not_overwritten_by_turn_start_ack`, GREEN |
| 4 | Important | B2: envío admitido durante cierre de conexión | T-02 | Corregido, pendiente UI/re-revisión | RED observado; `test_disconnect_reserves_its_slot_and_cannot_admit_a_turn_while_closing`, GREEN |
| 5 | Important | B3: permiso queda deshabilitado tras error anterior al consumo | T-02 | Corregido, pendiente re-revisión | RED de navegador observado; reconcilia la solicitud pendiente antes de habilitar un nuevo intento humano; GREEN |
| 6 | Important | C1/CWE-451: la redacción alarga y recorta una vista todavía aprobable | T-02 | Corregido, pendiente re-revisión | RED observado; `test_redaction_expansion_cannot_leave_an_incomplete_preview_approvable`, GREEN |
| 7 | Important | D1: recorte reserializa90,6MB y bloquea otras sesiones por GET máximo | T-02 | Corregido, pendiente re-revisión | RED de bloqueo entre proyectos; medición intercalada con fixture idéntico:85,45→0,85 MB serializados y mediana0,891→0,282s |
| 8 | Important | D2: mutex de catálogo ocupa lectores comunes esperando otro proyecto | T-04 | Corregido, pendiente re-revisión | RED de bloqueo observado; builders con namespaces propios; GREEN2 pruebas de justicia y aislamiento concurrente real |
| 9 | Minor | B4: contratos avanzados enlazados no viajan en npm | T-05 | Corregido, pendiente re-revisión | RED dedicado Node; GREEN y npm pack dry-run incluye Markdown público y roles, sin añadir journals/roadmap |

RED de regresiones de3,4,6,7:4 failed/22passed antes del cambio; GREEN26passed
después. Se conserva el resultado nativo con revisión de eventos, cierre explícito,
decisión sobre texto completo saneado y serialización fuera del bloqueo común.
Faltan las restantes correcciones, medición, re-revisión y QA. Interop readonly
confirmado por A:exit0,88 archivos al día. Compilación ES/EN:64 diagramas válidos;
edición PDF de QA actual126 páginas,32 gráficos,77 marcadores,184 enlaces y0
desbordamientos de texto (inspección visual final aún en curso).

Linux aislado/offline con Python3.11.18/Node22.23.3: lint/evals/procedenciaPDF
verdes; primera suite se detuvo con3fallos de registro de modos en
`test_console_encoding.py`,1455passed/3skipped/39subtests. Se corregirá el registro
explícito de módulo sin CLI y la prueba del servidor de fixture; sin bajar reglas.
La ejecución amplia nativa Windows se interrumpió tras fallos, sin afirmar su causa.
La suite dirigida Windows de consola estaba en70passed/1skip antes de estas
regresiones; no se declara una suite completa verde ni se reutiliza el%de Go.

GREEN navegador completo tras las correcciones:7/7 recorridos,64,64s.
RED adicional: las capacidades con Unicode podían ocupar todo el snapshot e
impedir ver una decisión humana pendiente (`response_budget`). Se limita cada
grupo a8192bytes y se marca el recorte; GREEN sesiones+fronteras nativas31passed.
El registro de modos UTF-8 se corrige sin relajar la prueba. La primera medición
de cobertura dirigida no alcanza todavía el90%; se amplían pruebas de protocolos,
errores y recuperación antes de ejecutar el gate final.

## Revisión de dos lentes — intento 2: correcciones verificadas y dos residuos

Lentes frescas A+B+C+D, respaldo genérico; scope exit0 sin avisos. A conserva los
criterios aprobados y verifica interop readonly:88 archivos al día. El gate oficial
del diff Python mide93,2% sobre12 archivos, mínimo90, exit0 y sin avisos; no es la
cobertura global del repositorio. C confirma C1 y presupuestos Unicode (8 pruebas);
D confirma D1/D2 (24 pruebas y medición propia≈101 veces menos bytes serializados).
B confirma B1/B2 (27 pruebas), B3 y B4. Ningún gap fue rebatido ni descartado.

| # | Grado | Resultado | Corrección para intento3 |
|---|---|---|---|
| 1 | Important, A+B | A1 residual: backends falsy inválidos se convierten en ausencia normal | RED5failed/2passed con valores array/false/0/string vacío/null; sustituir el fallback por default sólo para clave ausente; GREEN7passed |
| 2 | Important, B | Avisos A1/A2 desaparecen al volver a una vista con firma idéntica | RED de navegador al volver a Integraciones; avisos fuera del guard de render, también Vista general y Actividad; pendiente GREEN |

Los ocho Important y el Minor del intento1 quedan corregidos salvo los dos residuos
anteriores; los criterios aprobados no se reabren sin evidencia nueva. La suite
amplia Linux detectó además un assert de hint antiguo: la consola cambia los
argumentos aprobados y debe conservar visible `--diagnostics-report` del inventario.
Se actualiza el hint y su expectativa exacta para el contrato nuevo; no se elimina
el test ni el argumento. GREEN44 pruebas de diagnóstico; interop regenerado.
Otra prueba temporal del redactor falló bajo carga concurrente; falta aislarla y
no se modifica su límite. QA completa, cierre y publicación continúan pendientes.

## Revisión de dos lentes — intento 3: superada

Las cuatro lentes nuevas A+B+C+D revisaron el delta del snapshot inmutable contra
el intento2 y conservaron la tabla completa de veredictos anteriores. **0Critical,
0Important y0Minor pendientes; ningún rebate.** A ejecutó interop readonly:exit0,
88archivos al día. B reprodujo independientemente los7valores de configuración y
el regreso a las3vistas con la misma firma; todos verdes. C/D confirman que los
fixes no añaden ejecución externa ni consultas y no reabren C1/D1/D2 sin cambios.
Se usó respaldo genérico readonly porque el tool no ofrece el tipo reviewer.

GREEN final de navegador:7/7,0omitidas,68,96s. Cobertura final oficial del diff:
**93,26%**,12Python, mínimo90,exit0,sin avisos. Check de procedenciaPDF exit0;
linter0errores/7avisos explicados y evals221casos/0errores. Dos mapas nuevos de
FLOWS ES/EN compilados además de los64diagramas del manual. Los30archivos del
manual/referencias no tienen enlaces locales inexistentes ni destinos omitidos
del packlist npm. Chat real repetido tras fixes:Codex/OpenAI23,22s y
Claude/firstParty19,48s,marcador recibido,idle,0tools y cierre propio correcto.

Primera suite Linux amplia finalizada:2failed/10095passed/58skipped/82subtests,
1480,90s. Fallos:hintantiguo corregido y redactor1MB2,17s frente a1,5s. El redactor
no fue modificado por esta iniciativa; se ejecuta aislado con el mismo umbral,
seguido de suites afectadas y Node. Se exige después CI completa del commit
publicado; no se presenta la pasada amplia roja como una suite verde.

Entrega de rama: commits653a139/281664d/c4016cf publicados. CI41168370837 success
sobre c4016cf:10140passed/39skipped/82subtests,577,28s en la batería principal.
PR22 fusionada en dc9e98c el2026-10-31. Los16casos Windows omitidos en Linux
se contrastaron por nombre contra ejecuciones Windows verdes. Publicación
v3.0.0 en curso desde checkout limpio; T-06 permanece abierta hasta confirmarla.
