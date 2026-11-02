---
tasks: session-visibility
estado: en-progreso
creado: 2026-11-02
verificacion: obligatoria
changelog: Fixed
---

# Visibilidad de sesiones externas y actividad

**Ledger canónico** de esta iniciativa. El orquestador conserva estados y evidencias.

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase 1 — Corrección | 2 | 2 | 100.0% |
| Fase 2 — Detalle de actividad | 1 | 1 | 100.0% |
| **TOTAL** | **3** | **3** | **100.0%** |

El usuario informa de que esta conversación y sus agentes no aparecen en la
consola. Diagnóstico reproducido: cero sesiones propias; runtimes detectados;
captura de actividad desactivada. Se activa únicamente el opt-in de este proyecto.
No se cambia la configuración personal de hooks ni la caché del plugin.

## Fase 1 — Corrección

### T-01 — Descubrir metadatos de sesiones nativas Codex del proyecto

- **Estado**: completado
- **Tipo**: backend
- **Capacidades**: backend-practices, unit-tests
- **Procedencia de capacidades**: selector del bundle para API, aislamiento y pruebas; no hay spec OpenAPI.
- **Cubre (tests)**: E2E-01, E2E-03, E2E-05, M-01
- **Descripción**: Reutilizar el transporte nativo y thread/list con cwd y useStateDbOnly. Vista de solo lectura, sin reanudar conversaciones externas ni inferir liveness de otro proceso. Presupuestos, paginación y degradación explícitos.
- **Archivos**: `skills/plugin-panel/**`, `tests/**`, `docs/roadmap/2026-11-02-session-visibility/**`
- **Verificación**: pytest de adaptador, servicio y HTTP; comprobación real de metadatos sin inferencia.

**Criterios de aceptación**
- [x] Sesiones Codex externas del proyecto visibles con origen, límites, fecha y estado no confirmado; ninguna conversación vecina o texto de turnos exportado.
- [x] Fallos y límites se muestran como lectura parcial; no equivalen a cero sesiones.

### T-02 — Mostrar sesiones externas y explicar la captura de actividad

- **Estado**: completado
- **Tipo**: frontend
- **Capacidades**: frontend-quality, unit-tests
- **Procedencia de capacidades**: selector del bundle para frontend y pruebas; reutiliza el sistema visual existente.
- **Cubre (tests)**: E2E-01, E2E-03, E2E-05
- **Descripción**: Inventario externo separado de conexiones controlables. Conservar chat nativo de sesiones propias. Explicar opt-in y antigüedad de señales. Claude/OpenCode quedan explícitamente sin descubrimiento externo en este arreglo.
- **Archivos**: `skills/plugin-panel/**`, `tests/**`, `docs/**`, `CHANGELOG*`
- **Verificación**: navegador real, regresiones dirigidas, lint, interop y revisión del diff.

**Criterios de aceptación**
- [x] Esta sesión puede encontrarse en el inventario Codex; su actividad real llega a la vista Actividad tras activar el opt-in.
- [x] No se prometen agentes vivos a partir de señales históricas ni descubrimiento no implementado para otros runtimes.

## Evidencia inicial

- RED: `tests/test_console_codex.py::test_discovery_lists_only_project_metadata_without_resuming_or_reading_turns` falló con `Native project session discovery is missing` · 2026-11-02, antes de implementar el lector.
- RED: servicio, ruta HTTP y cierre de procesos propios fallaron por método ausente / HTTP 404 en sus regresiones dedicadas · 2026-11-02, antes de implementar esas capas.
- RED: navegador real `external project sessions: metadata, honest status and workspace isolation` agotó la espera de `#native-session-inventory .native-session-card` (la vista no existía) · 2026-11-02, antes de implementar la UI.
- RED: navegador real `hook activity explains opt-in and distinguishes recent signals from completed agents` agotó la espera de la explicación `sesion.actividad` · 2026-11-02, antes de implementar el texto y los estados.
- RED adicional de QA: la suite de consola detectó un literal localizado en un adaptador que no es CLI ni emite salida. Se fija un título de reserva neutral `Codex / <id>`: el test de metadatos falló por el valor anterior antes del ajuste · 2026-11-02. No se modifican reglas de encoding ni se añaden exenciones a la suite.
- RED tras aclaración del usuario: navegador reprodujo `apply_patchRol no informado · Captura de hooks` en vez de `Herramienta: apply_patch` · 2026-11-02. La navegación y las etiquetas se ajustan para distinguir herramientas, sesiones y agentes.
- RED: el contador de Sesiones devolvió 0 ante una sesión externa conocida en la prueba de navegador; se cuenta el inventario observado, sin duplicar conversaciones propias · 2026-11-02.

## Fase 2 — Detalle de actividad

### T-03 — Ficha de ejecución comprensible con métricas y procedencia

- **Estado**: completado
- **Tipo**: frontend
- **Capacidades**: frontend-quality, backend-practices, unit-tests
- **Procedencia de capacidades**: ampliación del usuario sobre legibilidad, detalle por ejecución y métricas con ausencia explícita.
- **Cubre (tests)**: E2E-02, E2E-04
- **Descripción**: Agrupar por agente o sesión cuando no exista atribución; estados En curso/Terminado/Sin actualizar, ficha con duración, tokens y coste, y operaciones de la ejecución. Consumir el lector de detalle existente del almacén. No inventar consumo donde el runtime no lo proporciona.
- **Archivos**: `skills/plugin-panel/**`, `tests/**`, `docs/**`, `CHANGELOG*`
- **Verificación**: servicio y HTTP por proyecto, E2E de abrir ficha y leer tiempos/métricas/operaciones; probar respuesta tardía, ausencia de datos y cambio de proyecto.

**Criterios de aceptación**
- [x] Se distinguen agentes identificados y actividad sin atribución; cada ficha permite interpretar estado, fecha y operaciones.
- [x] Duración, tokens y coste muestran procedencia y ausencia explícita, sin sustituir valores desconocidos por cero ni calcular dinero desde el tiempo.

RED: `test_activity_execution_detail_uses_project_history_and_rejects_unknown_identity` falló por método inexistente antes de implementar el detalle · 2026-11-02.
RED de UI: la ficha/estado Terminado no existían; después, pruebas dedicadas reprodujeron falta de recuperación del detalle y contador cero ante inventario indisponible. Corregidos antes de la validación final, sin relajar tests.
RED de teclado: al llegar una nueva operación, el refresco perdía el foco del botón Ver ejecución; el test devolvió `undefined` en vez del ID enfocado. Se conserva el foco por identidad local de ejecución · 2026-11-02.

- Configuración local (no versionada): `sesion.actividad=true`, conservando el resto de opciones. Tras el siguiente evento real: history status=ok, un run y dos eventos. No se inyectaron eventos ficticios.
- Consulta nativa de solo metadatos: cinco resultados del cwd registrado, ninguno de otro proyecto; incluye el ID de la sesión actual (comparación en memoria, sin publicar IDs ni conversaciones).

## Revisión de dos lentes — intento 1: Inventario externo y captura de actividad (T-01, T-02)

Snapshot independiente `session-visibility-review1`, base fe232a9. Lentes por
subagentes genéricos con los prompts del rol reviewer: la herramienta disponible
no expone selección de tipo nativo. Perfil normal permite revisión paralela;
`subagentes=false` mantiene la implementación en el hilo principal.

| Lente | Resultado | Gaps Critical/Important |
|---|---|---|
| A — conformidad | Criterios T-01/T-02 contrastados con spec, plan y Constitución | 0 |
| B — corrección | Llamantes de transporte, servicio, HTTP y UI comprobados | 0 |
| C — seguridad | Auth, cwd, metadatos seleccionados y DOM seguro comprobados | 0 |
| D — rendimiento | No seleccionada por el selector determinista | No aplica |

El usuario amplió después la legibilidad, los contadores y el detalle de T-03;
se revisa el diff ampliado en el intento 2. QA final permanece pendiente.

## Revisión de dos lentes — intento 2: Contadores, estados y ficha de ejecución ampliada (T-01, T-02, T-03)

Snapshot independiente `session-visibility-review2`. A y C sin hallazgos; B
encuentra un único gap Minor, sin Critical/Important. D no seleccionada.

| Gap | Severidad | Veredicto | Evidencia |
|---|---|---|---|
| B-01: foco de Reintentar/Cerrar detalle perdido durante errores repetidos | Minor | Confirmado y corregido | RED del navegador: el foco pasa a body en vez de Reintentar tras dos refrescos fallidos; se restaura el botón por su nombre accesible |

La corrección mantiene las etiquetas, el rechazo de respuestas obsoletas y los
umbrales. Se revisa su delta en el intento 3 antes de QA final.

## Revisión de dos lentes — intento 3: Conservación de foco durante fallos repetidos (T-01, T-02, T-03)

Snapshot independiente `session-visibility-review3`, delta frente a la revisión 2.

| Lente | Resultado |
|---|---|
| A — conformidad | Sin gaps; requisito de foco y regresión dedicados verificados |
| B — corrección | Sin defectos; B-01 corregido sin mover el foco desde otros controles |
| C — seguridad | Sin hallazgos; sólo comparación de texto y botones locales |
| D — rendimiento | No seleccionada; no se cambia el criterio del selector |

Revisión cerrada sin gaps pendientes. La prueba de foco tras dos 503 vuelve a
verde. QA final conserva su propio gate e intentos; no se reutiliza la revisión
como veredicto de pruebas.

## Verificación final y entrega

- Gate QA: VERDE, 18 pasan/0 fallos/0 flaky; [informe](testing/report.md).
- Python cambiado: 92,58% con mínimo90; 123 pasan y una omitida. Regresiones:456 pasan y una omitida; [verificación](testing/verification.md).
- Documenter: guías ES/EN, tablas, pasos y Mermaid actualizados; 31 enlaces locales comprobados. PDF histórico íntegro.
- Knowledge Gate: sin candidatos nuevos de esta iniciativa; ninguna promoción automática.
- Tiempo/tokens de generación completos: no medidos; no se reconstruyen ni se inventan.
- Entrega técnica lista en rama `fix/native-session-visibility`; PR/CI pendientes de recibo. M-01 personalEdge permanece pendiente y se declara en QA.
