---
tasks: workflow-integration
estado: en-progreso
creado: 2026-10-06
actualizado: 2026-10-06
verificacion: obligatoria
changelog: Changed
---

# Workflow y capacidades — ledger de integración

> **Ledger canónico de progreso.** Fuente única de verdad de esta iniciativa.

El usuario autoriza la implementación y el push de la rama cuando esté lista.
El catálogo, los comentarios y los nombres públicos utilizan funciones propias.
La investigación privada mantiene las fuentes originales; los avisos legales
obligatorios se conservan. La autorización no incluye PR, merge ni release.

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase 1 | 11 | 12 | 92% |
| **TOTAL** | **11** | **12** | **92%** |

## Fase 1 — Integración

**Estado**: en-progreso

### T-01 — Decisiones trazables del catálogo y contrato del workflow

- **Estado**: completado
- **Descripción**: Decisiones trazables del catálogo y contrato del workflow.
- **Dependencias**: Primera entrega e inventario fijados.
- **Archivos**: `docs/roadmap/**`, `CHANGELOG.md`, `CHANGELOG.es.md`, `docs/agents/**`, `skills/**`, `docs/PLUGIN-PANEL.md`, `docs/en/PLUGIN-PANEL.md`
- **Verificación**: 455 decisiones trazables y 18 adaptaciones delimitadas; revisión A sin gaps; nombres públicos comprobados en el cierre.
- **Changelog**: Documenta decisiones y límites de las capacidades adaptadas; conserva fuentes legales y usa nombres públicos propios.
**Criterios de aceptación**:
  - [x] Resultado verificado contra spec.md; sin gaps introducidos pendientes.

### T-02 — Registro y selector común con contratos deterministas

- **Estado**: completado
- **Descripción**: Registro y selector común con contratos deterministas.
- **Dependencias**: T-01.
- **Archivos**: `agent-kits/shared/capability-catalog.json`, `agent-kits/shared/capability-route.py`, `tests/test_capability_route.py`, `tests/test_console_encoding.py`
- **Verificación**: Catálogo/selector y guards: suite Linux final verde; coverage-gate capability-route 98,25 %; revisión A+B sin gaps.
- **Changelog**: Selecciona guías por rol, stack y área desde manifiestos acotados sin ejecutar código del proyecto.
**Criterios de aceptación**:
  - [x] Resultado verificado contra spec.md; sin gaps introducidos pendientes.

### T-03 — Stack-practices completo y retirada de tres guías iniciales

- **Estado**: completado
- **Descripción**: Stack-practices completo y retirada de tres guías iniciales.
- **Dependencias**: T-01.
- **Archivos**: `skills/stack-practices/**`, `skills/codeigniter-practices/**`, `skills/python-practices/**`, `skills/react-practices/**`, `evals/cases/**`
- **Verificación**: Tres mapas iniciales retirados, referencias absorbidas y evals actualizadas; linter/evals y suites de manifests/tamaño verdes.
- **Changelog**: Consolida las guías iniciales en stack-practices y retira mapas y referencias sustituidos.
**Criterios de aceptación**:
  - [x] Resultado verificado contra spec.md; sin gaps introducidos pendientes.

### T-04 — Guías transversales backend, frontend y entrega

- **Estado**: completado
- **Descripción**: Guías transversales backend, frontend y entrega.
- **Dependencias**: T-01.
- **Archivos**: `skills/backend-practices/**`, `skills/frontend-quality/**`, `skills/delivery-practices/**`, `evals/cases/**`
- **Verificación**: Fuentes primarias y criterios propios comprobados por A; evals positivas/negativas y rationalization tables verdes.
- **Changelog**: Añade criterios de backend, frontend y entrega con referencias concretas y activación evaluada.
**Criterios de aceptación**:
  - [x] Resultado verificado contra spec.md; sin gaps introducidos pendientes.

### T-05 — Auditoría de capacidades y evaluación de resultados

- **Estado**: completado
- **Descripción**: Auditoría de capacidades y evaluación de resultados.
- **Dependencias**: T-01.
- **Archivos**: `skills/capability-audit/**`, `skills/outcome-evals/**`, `evals/**`, `tests/test_outcome_evals.py`
- **Verificación**: JUnit observado y comparabilidad validada; RED secretos/colisión/magnitudes resueltos; cobertura 94,48 %; B+C sin gaps.
- **Changelog**: Audita capacidades y compara resultados JUnit observados con condiciones explícitas, sin métricas ficticias.
**Criterios de aceptación**:
  - [x] Resultado verificado contra spec.md; sin gaps introducidos pendientes.

### T-06 — Memoria/contexto: mejoras justificadas y piloto aislado

- **Estado**: completado
- **Descripción**: Memoria/contexto: mejoras justificadas y piloto aislado.
- **Dependencias**: T-01.
- **Archivos**: `agent-kits/shared/**`, `tests/test_code_context.py`, `docs/WORK-CONTEXT.md`, `docs/en/WORK-CONTEXT.md`
- **Verificación**: Piloto AST real 9 nodos/8 relaciones; tests de citas/hash/caché verdes; cobertura 97,83 %; D independiente sin gaps.
- **Changelog**: Añade consultas AST citadas y un piloto aislado; conserva la gobernanza de memoria existente.
**Criterios de aceptación**:
  - [x] Resultado verificado contra spec.md; sin gaps introducidos pendientes.

### T-07 — Integrar selección en roles, pm/dev-cycle y briefs

- **Estado**: completado
- **Descripción**: Integrar selección en roles, pm/dev-cycle y briefs.
- **Dependencias**: T-02…T-06.
- **Archivos**: `agents/**`, `commands/dev-cycle.md`, `commands/pm-cycle.md`, `agent-kits/shared/task-brief.py`, `agent-kits/shared/test_task_brief.py`, `agent-kits/shared/capability-check.md`
- **Verificación**: Diez roles y ciclos comparten selector; tests de brief/índice en Linux verdes; task-brief 96,83 %; límites protegidos.
- **Changelog**: Comparte capacidades entre roles, ciclos y briefs sin aumentar límites ni duplicar puertas de calidad.
**Criterios de aceptación**:
  - [x] Resultado verificado contra spec.md; sin gaps introducidos pendientes.

### T-08 — Panel y entrada de usuario para el workflow real

- **Estado**: completado
- **Descripción**: Panel y entrada de usuario para el workflow real.
- **Dependencias**: T-02/T-07.
- **Archivos**: `skills/plugin-panel/**`, `commands/work-context.md`, `tests/test_plugin_panel.py`, `evals/cases/**`, `hooks/**`
- **Verificación**: Edge P-01…P-07, 7 passed y qa-gate VERDE; capturas inspeccionadas; panel 26 passed/1 skipped, cobertura 94,05 %.
- **Changelog**: Moderniza el panel con hooks descriptivos, navegación accesible y seis etapas con contenido de sus roles.
**Criterios de aceptación**:
  - [x] Resultado verificado contra spec.md; sin gaps introducidos pendientes.

### T-09 — Retirar sustituciones y actualizar activos/generados

- **Estado**: completado
- **Descripción**: Retirar sustituciones y actualizar activos/generados.
- **Dependencias**: T-03…T-08.
- **Archivos**: `interop/**`, `.codex-plugin/**`, `.agents/plugins/**`, `.claude-plugin/**`, `CLAUDE.md`, `README.md`, `README.es.md`, `docs/README.md`, `docs/en/README.md`
- **Verificación**: 54 exports al día; plantillas incluidas en export y npm pack --dry-run; bajas, docs y modos comprobados en Linux.
- **Changelog**: Actualiza distribución y exports multi-runtime desde fuentes únicas y retira activos sustituidos.
**Criterios de aceptación**:
  - [x] Resultado verificado contra spec.md; sin gaps introducidos pendientes.

### T-10 — Revisión independiente, cobertura y QA Windows/Linux/navegador

- **Estado**: completado
- **Descripción**: Revisión independiente, cobertura y QA Windows/Linux/navegador.
- **Dependencias**: T-09.
- **Archivos**: `docs/roadmap/2026-10-06-workflow-integration/testing/**`, `tests/**`
- **Verificación**: Linux 3903 passed/29 skipped/8 subtests; Node Windows 134 passed, Linux 131/3 skips; cobertura 96,29 %; revisión A+B+C+D cero gaps.
- **Changelog**: Valida Windows, Linux, Edge y cobertura; cierra todos los gaps verificados de revisión.
**Criterios de aceptación**:
  - [x] Resultado verificado contra spec.md; sin gaps introducidos pendientes.

### T-11 — Documentación bilingüe, retro, estados y changelogs

- **Estado**: completado
- **Descripción**: Documentación bilingüe, retro, estados y changelogs.
- **Dependencias**: T-10.
- **Archivos**: `docs/**`, `CHANGELOG.md`, `CHANGELOG.es.md`
- **Verificación**: Docs ES/EN, informe final, retro y continuidad por fases escritos; notas Unreleased actuales y meter cerrado sin medición compatible; sincronización final tras push.
- **Changelog**: Sincroniza documentación bilingüe, evidencias, retro, changelogs y fases futuras con límites explícitos.
**Criterios de aceptación**:
  - [x] Resultado verificado contra spec.md; sin gaps introducidos pendientes.

### T-12 — Publicación de rama y comprobación remota

- **Estado**: en-progreso
- **Descripción**: Publicación de rama y comprobación remota.
- **Dependencias**: T-11.
- **Archivos**: `docs/roadmap/2026-10-06-workflow-integration/tasks.md`
- **Verificación**: Pendiente de ejecutar commit/push y comprobar git ls-remote frente a HEAD; no se anticipa publicación.
- **Changelog**: Publica la rama autorizada y comprueba que el commit remoto coincide con la entrega local.
**Criterios de aceptación**:
  - [ ] Resultado verificado contra spec.md; sin gaps introducidos pendientes.

## Evidencia durante la implementación

La evidencia consolidada y sus límites están en [testing/report.md](testing/report.md).
Resultado final: Linux 3903 passed/29 skipped/8 subtests, Node Windows
134 passed y Linux 131 passed/3 skipped. Consola 459 passed. Edge siete escenarios
y qa-gate VERDE. Cobertura del diff 96,29 %, cinco archivos, sin avisos. Export
54 al día; tres lentes iniciales y cuatro finales sin gaps pendientes. Las
comprobaciones documentales y la publicación se registran al concluirlas.

RED: T-08 responsabilidades nativas y HTML escapado (2 fallos); T-02 rendimiento
Python no activa frontend (1 fallo). GREEN: 61 passed, 2 skipped tras los fixes.
RED: T-06 hash de grafo con BOM no identifica bytes originales (1 fallo).
GREEN: contexto/selector 60 passed, 1 skipped; suite afectada final 276 passed,
2 skipped. La huella se calcula sobre el mismo buffer acotado que se parsea.

T-01: renombradas las iniciativas a capability-foundation y workflow-integration;
enlaces de roadmap, changelogs, calibración y pruebas actualizados. Comentarios
de inspiración retirados de las skills. Validación de nombres repetida en el cierre.

TDD n/a: renombrado y prosa. Los scripts nuevos tendrán evidencia RED antes del código.

RED: T-02 test_detects_three_stacks_from_manifests_without_executing_code falla con stacks=[] frente a los cuatro identificadores esperados (2026-10-06, scratchpad/capability-route-red.xml).

RED: T-02 test_deeply_nested_manifest_degrades_to_warning detecta ausencia de limite de profundidad (2026-10-06, scratchpad/capability-route-depth-red.xml).

GREEN: T-02 selector local: 42 passed / 1 skipped (Windows sin privilegio de symlink), 2026-10-06. La cobertura queda pendiente de la invocación final por directorio.

RED: T-07 test_selected_capabilities_reach_brief_without_loading_manuals falla por ausencia de referencias de capacidades (2026-10-06, scratchpad/capability-brief-red.xml).

RED: T-08 test_workflow_role_guides_use_inspected_sources_and_no_execution_claim falla por KeyError workflow (2026-10-06, scratchpad/workflow-panel-red.xml).

RED: T-05 test_result_is_derived_from_junit_and_metrics_are_not_invented falla con runs vacio (2026-10-06, scratchpad/outcomes-red.xml).

RED: T-06 test_symbol_context_contains_cited_ast_neighbors_without_promoting_memory falla con no-match-in-artifact (2026-10-06, scratchpad/code-context-red.xml).

RED: T-05 JUnit contradictorio daba pass y metrica extrema lanzaba OverflowError (2026-10-06, scratchpad/outcome-limits-red.xml).

- T-09/T-10 · RED: `tests/test_cloud_paths.py` rechazó las 16 variantes CLOUD en selector, panel y reporte (48 fallos, 18 aciertos). Causa real: directorios OneDrive con etiqueta `0x9000e01a` y atributo de solo lectura; no son junctions. GREEN: 184 passed, 2 skipped en guards, selector, panel, resultados, contexto y copias declaradas. Solo CLOUD permite lectura; reparse desconocido, junction y symlink siguen excluidos. Referencia: [Microsoft reparse tags](https://learn.microsoft.com/en-us/windows/win32/fileio/reparse-point-tags). Se retiraron las tres carpetas vacías con `rmdir` no recursivo tras verificar ruta, etiqueta y ausencia de contenido; antes se quitó únicamente su atributo de solo lectura.

## Revisión de dos lentes — intento 1: Fase 1 (T-01…T-10) — cinco gaps verificados

Lentes A+B+D en contexto fresco, fallback genérico porque el rol tipado de Claude
no está disponible. C no activada; D activada por la ruta del reporte de resultados.
Scope exit 0 sin avisos/info/fuera de alcance; settings privados del usuario excluidos.
Los criterios de T-01…T-08 y generados/documentación de T-09 fueron aprobados por A.
Linux, QA final, retro y push se reconocen pendientes, sin darles verde anticipado.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A-01 | Important | Anonimización inventa comando de push y rutas XML históricas inexistentes | T-09 | Se describe el push real sin inventar una referencia; rutas neutras contienen copias byte a byte de los XML originales | Referencia inválida reproducida exit 128; hashes de ambas copias iguales; XML RED 917 casos/4 fallos, GREEN 917/0 |
| B-01 | Important | tomllib obligatorio rompe Python 3.9/3.10 y sus consumidores | T-02/T-07/T-08 | Parser TOML opcional; JSON y filtros funcionan, TOML sin parser avisa; briefs/panel/lector continúan | RED 4 fallos en test_native_python_compat.py antes del fix; casos verdes después |
| B-02 | Important | Redacción después de JSON expone secreto entrecomillado en result | T-05 | Redacción central de valores y claves antes de serializar; si colisionan identificadores redactados, no exporta | RED test_b02_cli_redacts_quoted_secret_before_json_serialization; colisión roja antes de guard; ambos verdes |
| B-03 | Important | Entero negativo enorme provoca OverflowError fuera del diagnóstico | T-05 | Validación de magnitud y signo antes de convertir para isfinite | RED test_b03_cli_rejects_extreme_negative_metric_without_traceback; GREEN sin traceback, exit 2 |
| D-01 | Important | E/S repetida por cada cita de un mismo archivo del grafo | T-06 | Disponibilidad de ruta reutilizada solo durante una consulta; sintaxis y localización se validan siempre; errores también se reutilizan | Revisor: 10k nodos/20k relaciones/100 archivos/4,28 MiB, 10,982 s vs 1,460 s; RED test_d01_* antes de fixes; una comprobación por archivo y nueva comprobación en siguiente consulta |

Estado: corregidos y aprobados en el intento 2 independiente.
No se aceptan gaps como deuda ni se promueve conocimiento por esta revisión.

La primera validación Linux completa sobre filesystem nativo terminó con 3881
passed, 29 skipped y cinco fallos. Se corrigieron prompt evaluator (15.498 bytes
frente a tope 15.513), fila fuera de la tabla del roadmap, badges/prosa antiguos y
referencia histórica ADR abreviada. GREEN específicos: 143 passed y suite-script
de badges con diez conteos verificados. Esa ejecución precede los fixes de revisión;
se exige repetir la puerta final sobre el árbol actualizado.

## Revisión de dos lentes — intento 2: Fase 1 (T-01…T-10) — aprobado

Contexto fresco A+B+D, solo lectura, con el veredicto íntegro anterior. Scope
previo: exit 0, 155 archivos, sin avisos/info/fuera de alcance; settings privados
excluidos. Los cinco gaps aceptados quedan resueltos; 0 Critical, 0 Important,
0 Minor. No se reabren criterios aprobados sin evidencia nueva.

A conserva o reevalúa todos los criterios y verifica los XML históricos, sus
hashes y los 54 exports. B ejecuta 190 passed/2 skipped y prueba degradación sin
TOML, redacción antes de serializar, colisiones y magnitudes extremas. D ejecuta
46 passed: en su corpus independiente, reutilizar disponibilidad mantiene la
salida y baja de 30.000 a 100 comprobaciones (12,080 s frente a 1,117 s).

La tabla completa está en [testing/review-attempt2.md](testing/review-attempt2.md).
Los grupos se solapan; no se suman. Python 3.9/3.10 se verifica mediante ausencia
simulada del parser y compatibilidad sintáctica, no intérpretes ejecutados.
La revisión no sustituye a QA final ni acredita por sí sola cierre o push.

## Refinamiento del panel solicitado por el usuario (T-08/T-10)

Se agrupan handlers por evento sin cambiar el inventario JSON por handler.
Los siete scripts registrados declaran nombre y función en su cabecera pública;
el panel muestra activación, función, origen y solo timeouts explícitos. Se lee
cada cabecera una vez por inventario, sin ejecutar código ni mostrar comandos.
La UI usa una plantilla local con navegación, búsqueda, detalles y vista móvil.
Las etapas permiten seleccionar contenido y abrir responsabilidades del rol.

RED: dos casos de agrupación, uno de metadatos públicos y uno de plantilla ausente
fallaron antes de implementar. GREEN inicial: 94 passed/1 skipped en panel, CLOUD
y compatibilidad. Edge: cinco escenarios verdes antes de añadir navegación.
RED P-06: Catálogo carecía de aria-current; RED P-07: no había botones de etapas.
Los nuevos escenarios exigen navegación por teclado e historial y contenido real.

La suite Linux previa al refinamiento pasó: 3895 passed, 29 skipped, ocho subtests;
Node 131 passed/3 skipped y release --check verde. Se repetirá sobre lo actualizado.

Windows Node: 133 passed/1 failed. Aislamiento B-12: fallo reproducido solo por
marca a los 3 s. Una copia instrumentada mostró marca escrita y nieto ya terminado
al retornar; otra no llegó a escribir. El oráculo se cambia por existencia del PID
real, con fixture iniciada y cleanup propio incluso al fallar. El instalador de
producción permanece idéntico. RED de la variante privada sin matarArbol: proceso
vivo, exit 1; GREEN aislado de producción: 1 passed. Causa en GOT-016, propuesta local ignorada por Git; evidencia pública en testing/timeout-oracle.md.


## Revisión de dos lentes — intento 3: refinamiento final — aprobado

A+B+C+D en contexto fresco, solo lectura, con veredictos previos íntegros.
C y D activadas por selector; hooks solo cambian cabeceras públicas. Scope previo
165 archivos, exit 0 sin avisos/info/fuera de alcance; settings privados excluidos.
Veredicto: 0 Critical, 0 Important, 0 Minor. Los cinco gaps anteriores siguen
resueltos. Tabla completa en testing/review-attempt3.md. La revisión no sustituye
las puertas ejecutables; el ejecutor terminó Linux, Windows, cobertura y Edge
sobre la implementación final como consta en testing/report.md.

## Continuidad autorizada

El usuario acuerda integración por fases y descarta crear nuevos paquetes
técnicos que no existan en el catálogo de referencia. Se prioriza después de
publicar el núcleo común el reconocimiento de agentes, skills, tools y MCP
propios en los tres runtimes. Plan y límites actuales en
../../INTEGRATION-ROADMAP.md; las fases futuras no se declaran implementadas.


## Puertas finales antes de publicar

Comprobación documental actualizada: 502 passed, un aviso histórico preexistente.
Scope: 169 archivos, exit 0, sin avisos/info/fuera de alcance; settings del usuario
excluidos. Linter final: cero errores, tres avisos previos; evals 51/179 y export
54 al día. git diff --cached --check limpio y barrido de nombres/contenido
públicos sin referencias prohibidas. Se corrigió la posición de la fila propia
GOT-016 en su índice privado; ambos permanecen ignorados y no se distribuyen.
Meter cerrado: fuente estimado, tokens/horas IA/€ nulos; mediana sin cambios.
