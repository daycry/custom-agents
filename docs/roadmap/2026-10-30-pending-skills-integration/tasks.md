---
tasks: pending-skills-integration
estado: completado
creado: 2026-10-30
verificacion: obligatoria
changelog: Added
test-plan: n/a (sin UI)
generacion:
  fuente: estimado
  tokens_reales: null
  eur: null
  horas_ia: null
  tokens_procedencia: sin_medida
  coste_procedencia: sin_coste
---

# Integración pendiente de skills y diagnóstico de hooks

Ledger canónico. El usuario autoriza continuar la integración pendiente y mejorar las skills cuando aporte valor. Mantiene canceladas las tres optimizaciones de plugin-optimization. Añade el diagnóstico de `plugin contents changed; hook approval required` y de «Unnamed hook» al abrir `/hooks`.

Origen: los 47 destinos D-111..D-157 aparcados en catalog-capabilities. Cada destino se revalida contra el código actual; una propuesta histórica no demuestra que siga faltando. El usuario concreta después los stacks: CodeIgniter 4, Laravel, Symfony, Next.js, React, Python, .NET, C y C#; se aplican desde sus manifiestos al usarlos. Implementación por ROOT, sin delegarla; revisión independiente cuando corresponda. `.claude/settings.json` personal queda fuera de esta selección.

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase 1 — Integración | 6 | 6 | 100.0% |
| **TOTAL** | **6** | **6** | **100.0%** |

## Fase 1 — Integración y diagnóstico

### T-01 — Diagnosticar aprobación y dar nombres visibles a los hooks

- **Estado**: completado
- **Tipo**: hooks
- **Descripción**: Reproducir el inventario nativo, explicar las aprobaciones desfasadas y la interacción del navegador de hooks; añadir etiquetas al export propio de Codex sin cambiar comandos, alcance, plazos ni confianza.
- **Changelog**: Identificar los hooks de Codex con etiquetas descriptivas y documentar su revisión tras actualizar el plugin.
- **Archivos**: `scripts/export-interop.py`, `tests/test_export_interop.py`, `interop/codex/hooks.json`, `docs/INTEROP.md`, `docs/en/INTEROP.md`, `CHANGELOG.md`, `CHANGELOG.es.md`, `docs/roadmap/2026-10-30-pending-skills-integration/**`
- **Verificación**: `python -m pytest -q tests/test_export_interop.py; python scripts/export-interop.py --check` → exit 0; inventario nativo con etiquetas y mismo control de confianza.

**Criterios de aceptación**
- [x] Evidencia nativa distingue definición, huella del bundle y etiqueta; no atribuye la causa a bytecode ni a manipulación sin comprobarlo.
- [x] Los hooks propios exportados a Codex tienen etiqueta descriptiva; se conserva una etiqueta explícita y no se etiqueta una orden ajena por coincidencia parcial.
- [x] Comandos, matchers, async y timeouts conservados; no se modifica la confianza global ni la caché instalada.
- [x] Se documentan la tecla de revisión de la CLI y los límites de lo comprobado en Desktop.

**Diagnóstico inicial**: `hooks/list` nativo 0.166.0, sin crear hilo ni llamar a modelos: diez hooks propios activos, todos `modified`, todos `statusMessage: null`; cero avisos/errores de inventario. La huella calculada del bundle coincide exactamente con la devuelta por el servidor nativo y difiere de las aprobadas. Las diez huellas de definición activas conservan sus valores aprobados; hay una undécima aprobación histórica para una posición eliminada. El servidor de diagnóstico terminó con exit 0. El usuario confirma Terminal de Codex (CLI); la interacción descrita corresponde a esa interfaz. Desktop no se ha reproducido. Fuentes oficiales: https://learn.chatgpt.com/docs/hooks y fuente rust-v0.166.0, commit 6ff1e1ca3b30fc8b914720681fcf5fe62e95f856. Evidencia privada acotada en `.pytest_cache/hook-approval-20261030-*`; se publicará un resumen saneado.


RED: `tests/test_export_interop.py::test_codex_hook_browser_does_not_show_unnamed_own_hooks` falló con Native inventory and regression show ten own hooks without statusMessage; 1 failed, 1 passed before exporter change. · 2026-10-30.

**Verificación funcional**: 50 tests de exportación pasan. Antes del código, el caso de nombres falla para diez hooks (1 fail/1 pass); la suite completa intermedia conserva dos fallos por diccionarios de actividad que esperaban la metadata anterior, actualizados añadiendo el campo sin retirar sus otros checks. Inventario nativo aislado: diez nombres, todos `untrusted`, cero llamadas de inferencia/hilos creados, caché de fixture y config real intactas, cero procesos propios al terminar. Al retirar únicamente statusMessage, el export coincide exactamente con HEAD. Recibo `testing/hook-approval-and-labels-2026-10-30.json`. No se instala este cambio en la caché real ni se aprueban hooks globales. TDD observado antes del cambio; revisión/QA conjunta cerrada en T-05, con resultado en testing/validation.json.

### T-02 — Revalidar los 47 destinos pendientes

- **Estado**: completado
- **Tipo**: docs
- **Descripción**: Comparar fuentes, destinos actuales y consumidores; distinguir ya cubierto, integración aplicable, contexto pendiente y dependencia externa pendiente. Conservar los cierres históricos.
- **Changelog**: Revalidar las propuestas aparcadas del catálogo contra los consumidores y contratos actuales.
- **Archivos**: `docs/roadmap/2026-10-30-pending-skills-integration/**`, `docs/roadmap/README.md`
- **Verificación**: `python agent-kits/shared/ledger-lint.py docs/roadmap/2026-10-30-pending-skills-integration/tasks.md` → exit 0; matriz de 47 IDs únicos, con fuente y disposición por destino.

**Criterios de aceptación**
- [x] Los 47 IDs tienen decisión individual, evidencia y dueño; no se cuentan como integrados por existir su propuesta.
- [x] Las especialidades esperan los stacks concretos del usuario; no se declara un consumidor inexistente.

**Notas**: TDD n/a: comparación documental. D-116 tiene contrato inspeccionado y tres regresiones existentes en verde. Verificación T-02: ledger-lint exit 0 (0 incoherencias/0 avisos); matriz con 47 IDs únicos. Los conteos iniciales se conservan y el avance posterior a la respuesta del usuario se distingue en los recibos.

**Resultado de revalidación**: 47 IDs únicos; 7 destinos transversales listos, D-116 ya cubierto con tres regresiones existentes en verde, D-146 necesita contrato de persistencia, 21 especialidades esperan consumidor y 17 destinos esperan contexto/dependencia. `integration-decisions.md` y `testing/destination-revalidation.json` conservan cada fuente, motivo y límite. No se declara ejecución de los stacks pendientes ni eficacia medida.

### T-03 — Integrar y mejorar los destinos transversales aplicables

- **Estado**: completado
- **Tipo**: docs
- **Descripción**: Concretar el lote desde T-02, reutilizando dueños existentes y verificando recursos, activación y límites de acceso antes de crear piezas.
- **Changelog**: Integrar las mejoras transversales justificadas por la comparación del catálogo.
- **Archivos**: `skills/voice-profile/**`, `skills/content-production/**`, `skills/relationship-planning/**`, `skills/competitive-analysis/**`, `skills/llm-pipeline/**`, `skills/data-collection/**`, `agent-kits/shared/external-communication.md`, `agent-kits/shared/README.md`, `tests/test_rationalization_tables.py`, `evals/cases/skill-voice-profile.json`, `evals/cases/skill-content-production.json`, `evals/cases/skill-relationship-planning.json`, `evals/cases/skill-competitive-analysis.json`, `evals/cases/skill-llm-pipeline.json`, `evals/cases/skill-data-collection.json`, `docs/README.md`, `docs/en/README.md`, `CLAUDE.md`, `README.md`, `README.es.md`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.codex-plugin/**`, `.agents/plugins/**`, `interop/**`, `CHANGELOG.md`, `CHANGELOG.es.md`, `docs/roadmap/2026-10-30-pending-skills-integration/**`
- **Verificación**: `python scripts/lint_plugin.py; python evals/check.py; python -m pytest -q tests/test_rationalization_tables.py tests/test_skill_size.py tests/test_export_skills.py tests/test_manifests.py; python scripts/export-interop.py --check` → exit 0; inspección de enlaces y casos de fuente/conflicto/canal no disponible.

**Criterios de aceptación**
- [x] Cada incorporación tiene consumidor o función reutilizable explícita, recursos existentes, fuentes comprobadas y sin duplicar responsabilidades.
- [x] Las rutas y verificaciones se concretan antes de cambiar piezas; docs ES/EN y exports se actualizan junto con las fuentes.

**Lote concreto**: D-147/148/149/150/151/153/154. Seis skills opcionales de guía, sin runner de proveedor; D-151 se consolida como fragmento compartido para contenido y relaciones. Fuentes: S018/S029, S049/S063, S048, S024/S043/S044, S060, S056 y S069, desde fichas completas leídas. El contenido se redacta de nuevo a partir de contratos: no se copia código del corpus ni se incorporan sus dependencias. Se conservan datos desconocidos, procedencia, autorización existente, reservas y resultados inciertos; no se anuncian adaptadores instalados. TDD n/a para prosa/metadata; evals de activación estática y validaciones existentes son sus oráculos, sin atribuir calidad editorial o de modelos medida.

**Verificación del lote**: 119 passed/1 skipped en Windows para capability-route, tamaños, export portable, tablas, manifiestos; el skip existente es creación de symlinks sin privilegio. Evals: 58 piezas, 216 casos, 0 errores; export-interop --check: 88 ficheros al día. Linter: 0 errores y cinco avisos (tres nombres históricos, dos citas del comando nativo Codex /hooks). No se atribuye activación real a los casos estáticos.

### T-04 — Integrar las especialidades de stack solicitadas

- **Estado**: completado
- **Tipo**: docs
- **Descripción**: Incorporar los stacks que concrete el usuario, con selección por manifiesto/versión y carga bajo demanda. Concretar referencias, parsers o herramientas solo para los consumidores identificados.
- **Changelog**: Ampliar las guías de stack para los consumidores solicitados.
- **Archivos**: `agent-kits/shared/capability-route.py`, `agent-kits/shared/capability-catalog.json`, `agent-kits/shared/capability-check.md`, `tests/test_capability_route.py`, `skills/stack-practices/**`, `evals/cases/skill-stack-practices.json`, `docs/README.md`, `docs/en/README.md`, `CLAUDE.md`, `CHANGELOG.md`, `CHANGELOG.es.md`, `docs/roadmap/2026-10-30-pending-skills-integration/**`
- **Verificación**: `python scripts/lint_plugin.py; python evals/check.py; python scripts/export-interop.py --check; python -m pytest -q tests/test_skill_size.py tests/test_export_skills.py` → exit 0; enlaces oficiales y selección por manifiestos inspeccionados.

**Criterios de aceptación**
- [x] Los stacks y proyectos están declarados y las fuentes técnicas corresponden a sus versiones.
- [x] No se incorpora tooling no soportado como si estuviera instalado o verificado.

**Consumidores declarados por el usuario**: CodeIgniter 4, Laravel, Symfony, Next.js, React, Python, .NET, C y C#. Versiones/proyectos aún no indicados; la aplicación consulta los manifiestos del consumidor, sin fijar una major universal. Lote: cinco referencias Laravel/Symfony/Next.js/.NET-C#/C; revisar las tres existentes y ampliar selección/activación. C no se confunde con C++; .NET y C# comparten una referencia. No se instalan compiladores, SDK ni parsers de cobertura. TDD n/a: prosa, fuentes y casos de activación.

**Selección ejecutable**: ampliar vocabulario cerrado Laravel/Symfony/Next.js/.NET/C; detectar los tres frameworks por dependencias exactas JSON ya acotadas. C y .NET se declaran explícitamente para la tarea, sin fingir parser de CMake/MSBuild. TDD obligatorio para ese cambio del selector; primer rojo registrado antes del código.

RED: `tests/test_capability_route.py -k "requested_frameworks or framework_components or native_and_dotnet"` falló con Laravel/Symfony/Next.js no detectados y c/dotnet rechazados por argparse; 5 failed, 1 passed, 44 deselected antes del cambio · 2026-10-30.

### T-05 — Revisión, validación y entrega

- **Estado**: completado
- **Tipo**: devops
- **Descripción**: Revisar el alcance efectivamente implementado, ejecutar sus suites y validaciones, conservar limitaciones nativas y cerrar con evidencia.
- **Changelog**: Validar la integración y registrar el estado real de cada destino.
- **Archivos**: `docs/roadmap/2026-10-30-pending-skills-integration/**`, `docs/roadmap/README.md`, `docs/roadmap/CALIBRATION.md`, `CHANGELOG.md`, `CHANGELOG.es.md`
- **Verificación**: `python scripts/lint_plugin.py; python evals/check.py; python scripts/export-interop.py --check; python agent-kits/shared/ledger-lint.py docs/roadmap/2026-10-30-pending-skills-integration/tasks.md` → exit 0; suites dirigidas declaradas en cada lote.

**Criterios de aceptación**
- [x] Revisión independiente y QA del diff real, con cobertura donde exista código cambiado; sin fingir ejecución nativa ni activar integraciones externas.
- [x] Se conservan como pendientes los destinos sin contexto o dependencia; commits limitados a la selección revisada.

### T-06 — Conservar entradas centrales al crecer el índice

- **Estado**: completado
- **Tipo**: hooks
- **Changelog**: Conservar las entradas centrales del ciclo en el índice de inicio al crecer el catálogo.
- **Descripción**: La suite amplia detecta que la cuota alfabética del índice omite quick-implement con 33 skills. Mantener dev-cycle, quick-implement e implementer visibles cuando existan, sin elevar los presupuestos ni quitar avisos de piezas omitidas.
- **Archivos**: `interop/opencode/custom-agents-index.md`, `agent-kits/shared/skill-index.py`, `agent-kits/shared/test_skill_index.py`, `agent-kits/shared/README.md`, `docs/roadmap/2026-10-30-pending-skills-integration/**`, `CHANGELOG.md`, `CHANGELOG.es.md`
- **Verificación**: `python -m pytest -q agent-kits/shared/test_skill_index.py tests/test_hooks_shell.py` → exit 0; límites 45 líneas/3500 caracteres conservados y caché invalidada por formato.

**Criterios de aceptación**
- [x] El crecimiento del catálogo conserva las tres entradas del ciclo si existen, en cada runtime y con IDs nativos para agentes.
- [x] Cuotas, topes, mensajes de omisión y desactivación se conservan; no se debilita la regresión de SessionStart.

**Reproducción**: Linux sobre árbol 31e98d4cb64f51baa0e0bbaf9b1e8f6fdc3f48e1: test_session_context_startup_indice_mas_roadmap_bajo_el_tope falla en la presencia de quick-implement. La primera pasada amplia se conserva roja; no se cuenta como validación final. No es un fallo de confianza ni de ejecución atribuible a los hooks instalados.

RED: `agent-kits/shared/test_skill_index.py -k core_entrypoints` falló con /dev-cycle ausente en cuatro runtimes de un catálogo sintético sobredimensionado; 4 failed, 23 deselected antes del código · 2026-10-30.

Revisión intento 2: A detecta el índice OpenCode generado desfasado tras cambiar skill-index.py. Se añade el artefacto derivado a T-06 y se regenera, sin cambiar la fuente ni elevar presupuestos.

**Verificación T-06**: Windows, `python -m pytest -q agent-kits/shared/test_skill_index.py tests/test_hooks_shell.py --tb=short`: 106 passed. Revisión A/B/D intento 2 sin gaps pendientes; los tres módulos productivos de la QA Linux coinciden byte a byte en Git con HEAD. La pasada dirigida Linux tiene 215 passed/1 skipped (locale de coma decimal ausente), gate sobre ficheros cambiados 93,00 %, sin avisos; suite amplia y regresión documental descritas en QA final T-05.

**Confirmación del usuario**: usa la terminal de Codex; primero informa que sigue bloqueada y después confirma que la tecla t funciona. Persiste «Unnamed hook» en el bundle instalado 2.3.0, que carece de etiquetas. La corrección está en código/fixture aislado; no se ha instalado ni se han reescrito aprobaciones globales. El usuario no confirma el comportamiento de nombres en Claude/OpenCode.

**Cierre documental T-05**: retro local y fila de calibración sin ratio, sin transformar reloj en horas IA ni inventar tokens/costes. No se publica conocimiento aprobado ni se modifica la configuración instalada.

## Revisión de dos lentes — intento 1: Lentes A/B/D de contexto fresco sin gaps reportados. QA posterior detecta omisión de quick-implement al crecer el catálogo; se abre T-06 y no se cierra la entrega. (T-01, T-02, T-03, T-04)

Veredicto A/B/D: sin gaps reportados en el intento 1. La QA posterior detectó la omisión de quick-implement y abrió T-06; la corrección se acredita en el intento 2 y testing/reviews.json.

## Revisión de dos lentes — intento 2: A/B/D sin gaps pendientes tras conservar entradas centrales. A detectó índice OpenCode derivado desfasado, corregido por regeneración; check canónico exit 0. Se conserva el aprobado del intento 1; QA final documenta y verifica la tabla del roadmap. (T-06)

Veredicto A/B/D: conforme, sin gaps pendientes. El Important del índice OpenCode generado se corrigió y export-interop --check terminó con exit 0. Se conserva lo aprobado en el intento 1; resultados y límites en testing/reviews.json y testing/validation.json.

**QA final T-05**: pasada amplia Linux: 9888 passed, 2 failed, 57 skipped, 82 subtests passed. Ambos fallos eran la nueva fila fuera de la tabla del roadmap; corregida y suite completa del índice repetida: 55 passed en Linux y 55 passed en Windows. Resultado por composición: 9890 casos únicos pasados, 57 omitidos; no se finge una segunda pasada completa. Código y tests funcionales idénticos al árbol probado; Node 431 passed/16 skipped/0 failed; gate sobre tres ficheros productivos cambiados 93,00 %, mínimo 90, sin avisos. Recibo testing/validation.json y hashes de logs; revisión A/B/D cerrada sin gaps pendientes. Avisos acotados en el recibo.

**Entrega**: código en 68e0f51, bd89999 y 3333e0c; cierre documental y push de la rama preparados como selección literal revisada. Los nombres de Codex llegarán al instalar una versión que incorpore estos commits. Métricas compatibles ausentes: testing/metering.json, sin convertir reloj en horas IA.
