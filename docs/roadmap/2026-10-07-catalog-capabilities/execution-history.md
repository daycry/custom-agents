# Qué se ejecutó durante la integración

Este archivo conserva íntegro el historial de ejecuciones hasta el cierre de QA del bloque18.
Los estados, criterios y pendientes actuales tienen una única fuente: [tasks.md](tasks.md).
Las anotaciones históricas reflejan su fecha y snapshot; no acreditan el estado actual.
La separación mantiene el ledger dentro del límite de lectura del panel.

## Evidencia inicial

TDD n/a: planificación y documentación. Reconciliación de hashes mediante
helper privado y lectura de corpus fijado; ningún script externo ejecutado.
455 hashes verificados: 293 skills/68 agentes/94 comandos. Cero piezas
evaluadas semánticamente en esta fase; decisiones anteriores no se promueven
a revisión completa. Recursos auxiliares reconciliados en corpus.json; sus
dependencias y utilidad todavía requieren lectura semántica.

Versiones obtenidas con --version: Codex CLI 0.160.1, Claude Code 2.1.287,
OpenCode 2.0.12. Fuentes oficiales abiertas en contracts.md. La prueba aislada
reproduce el rechazo del export V1 actual en OpenCode V2; el control positivo
carga y registra hooks, y se observa normalización de configuración V1/V2.
No acredita despacho ni bloqueo. Guardias y formatos se resolverán en T-02/T-09.

Comprobaciones de apertura ejecutadas: scope-check contra 6187b12, nueve
ficheros en alcance/cero fuera/cero avisos, settings ajenos excluidos;
ledger-lint cero incoherencias/cero avisos; linter cero errores/tres avisos
históricos; test_roadmap_index 50 passed; scan de nombres/contenido público sin
hallazgos y diff --check limpio. Son gates del plan, no de la implementación.

Comprobaciones del cierre de T-01 ejecutadas: ledger-lint cero incoherencias y
cero avisos; test_roadmap_index 50 passed (0,09 s); linter cero errores y tres
avisos históricos; scope-check 13 ficheros en alcance y cero fuera/avisos,
settings ajenos excluidos; scan público sin hallazgos. TDD n/a: documentación
e inventario de investigación; ningún cambio de producción en este hito.

Al añadir la evidencia nativa de OpenCode, scope-check conserva 13 ficheros
propios en alcance/cero fuera/cero avisos (14 cambiados contando settings
excluidos). El scan público sigue sin hallazgos. Los digests y agregados del
manifiesto y el enlace al método se contrastaron con el mapa privado: exit 0.

## Revisión de dos lentes — intento 1: Fase 2 (T-08, T-09, T-14, T-15) — bloque de checkpoint

Lentes A+B mediante subagentes de contexto fresco; no se dispone de la herramienta
Agent del plugin en esta sesión. Selector contra 47e9ddc: C=false/D=false, sin
avisos. Alcance: diez archivos propios/cero fuera; settings ajenos excluidos.
No se ha revisado ni cerrado el resto de las tareas multi-runtime.

| Criterio | Veredicto inicial | Evidencia |
|---|---|---|
| T-08: diseño previo, alternativas, bloque acotado | ✓ | design.md, criterios del primer bloque y pendientes explícitos |
| T-09: opt-out booleano/objeto, privacidad, rotación acotada y atómica | ✓ | test_journal.py, casos capture/rotar y fallos fsync/replace |
| T-09: CLI portable y reclamación exclusiva | ✓ | aserciones de rutas y cien contenciones en test_outbox.py |
| Constitución: cerrojo sin seguir enlaces ajenos | ✗ | A-1, outbox.py reclamar abría .claim.lock sin validar |
| Corrección: errores de transacción visibles | ✗ | B-1, excepción de processing/ dañado absorbida como None |
| T-14: evidencia de pruebas y TDD | ✓ parcial | rojos registrados; Windows 198 passed/11 skipped y Linux 209 passed antes de estos fixes; cobertura final pendiente |
| T-15: docs ES/EN, sin marca nueva, alcance declarado | ✓ | observability y changelogs bilingües; scope-check |
| No cerrar tareas globales sin aceptación completa | ✓ | T-08/T-09/T-14/T-15 siguen en-progreso |

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A-1 | Important | .claim.lock seguía symlink externo | T-09 | Corregido: lstat previo, O_NOFOLLOW donde existe y contraste descriptor/ruta antes del cerrojo; pendiente revalidación independiente | RED Linux: test_reclamar_rechaza_cerrojo_enlace_sin_abrirlo falla al abrir enlace; test_reclamar_rechaza_cerrojo_sustituido_antes_de_abrir falla Windows/Linux. GREEN dirigido: Linux 5 passed; Windows 4 passed/1 skipped (symlinks sin privilegio), 2026-10-08 |
| B-1 | Important | except absorbía errores de _reclamar | T-09 | Corregido: captura solo errores de adquisición; transacción fuera del except y liberación en finally; pendiente revalidación independiente | RED test_reclamar_error_de_transaccion_no_parece_cola_vacia: DID NOT RAISE OSError en Windows/Linux; GREEN dirigido anterior incluye fallo observable y posterior recuperación, 2026-10-08 |

Rojo de revisión antes de modificar producción: Windows 2 failed/1 skipped;
Linux 3 failed, todos los casos dirigidos a los gaps. No hay deuda aceptada ni
gaps rebatidos. Segundo intento y QA final del bloque pendientes. No se promueve
conocimiento de otras tareas en progreso.

Jira: planner local de evento gaps/actor reviewer/intento 1 devuelve ops=[];
enabled no es true. No se publica nada externo.

## Revisión de dos lentes — intento 2: Fase 2 (T-08, T-09, T-14, T-15) — checkpoint sin gaps pendientes

A+B de contexto fresco revalidan solo las correcciones con la tabla completa del
intento anterior. C/D siguen false según selector, sin avisos. No se reabre lo
aprobado sin evidencia nueva. A-1/B-1 corregidos y verificados por ambas lentes;
cero Critical, Important o Minor pendientes en este bloque.

| Criterio corregido | Veredicto | Evidencia independiente |
|---|---|---|
| A-1: enlace rechazado e identidad contrastada antes de bloquear | ✓ | outbox.py:592–602; test_outbox.py:130,149. Lente A ejecuta Windows 4 passed/1 skipped y Linux 5 passed; el enlace sin privilegios de Windows se verifica en Linux |
| B-1: errores de la transacción llegan al llamador y el cerrojo se libera | ✓ | outbox.py:611–620; test_outbox.py:119 verifica excepción, pendiente y recuperación. Lente B ejecuta Windows 4 passed/1 skipped |
| Docs ES/EN y ámbito del bloque | ✓ | observability ES/EN explican enlaces, identidad y diagnóstico; tareas globales siguen en-progreso |

QA final después de esas correcciones, 2026-10-08:

- Python nativo Windows 3.13: journal/outbox completos, 200 passed/12 skipped,
  141,05 s. Los skips corresponden a POSIX/permisos/enlaces no disponibles allí;
  no acreditan ACL de NTFS. Python nativo Linux 3.14.4 en WSL Ubuntu: 212 passed,
  135,23 s, sin skips; mismos pytest 9.1.1 y coverage 7.16.2, dependencias de
  prueba aisladas en /tmp, sin instalación global.
- coverage.py oficial mide ambos módulos; unión de líneas ejecutadas en ambos
  sistemas intersectada con líneas añadidas ejecutables contra 47e9ddc:
  journal 16/19, outbox 34/34, total 50/53 = 94,34% (umbral ≥90%). Las dos
  líneas CLI ejecutadas en subprocess no se instrumentan y cuentan como ausentes;
  no se extrapola cobertura a runtime nativo ni al resto del proyecto.
- qa-gate VERDE: 412 passed, 0 failed/flaky/interrupted, 12 skipped. Entrada
  normalizada desde los casos JUnit reales de esas dos ejecuciones pytest;
  no se presenta como una ejecución de Playwright.
- node --test tests/hook-runtime.test.mjs: 12 passed/0 failed, 33,05 s. Prueba
  launchers/fixtures propios, incluida captura UTF-8 y cierre dentro de 3 s;
  el adaptador OpenCode V1 invocado por fixture no acredita carga nativa V2,
  ni este tiempo acredita el presupuesto de cierre por defecto de Claude.
- tests/test_console_encoding.py + tests/test_roadmap_index.py: 512 passed
  antes del registro final de revisión, 235,26 s.
- Linter: cero errores/tres avisos históricos; export-interop --check: 54
  archivos al día. Scope-check: diez propios/cero fuera/cero avisos; settings
  ajenos excluidos. No se ejecutan scripts del corpus ni se activan backends.

Evidencias brutas locales ignoradas: scratchpad/.venv/memory-{win,linux}.xml,
coverage-memory-{win,linux}.json, memory-diff-coverage.json y memory-qa-gate.json.
Son respaldos de este bloque, no distribución del plugin. La aceptación global
de T-08/T-09/T-14/T-15 permanece abierta por los criterios restantes.

Comprobación del registro final: test_roadmap_index 50 passed (0,97 s),
ledger-lint cero incoherencias/cero avisos, diff --check limpio y scan de
contenido/nombres de los diez archivos públicos sin marca de origen.
Jira evento revision/actor reviewer/intento 2: ops=[], disabled; sin envíos.
Este checkpoint se publica en feat/catalog-capabilities; el SHA final se
contrasta con origin después del push, sin merge ni release.

## Bloque de transporte OpenCode V2 — T-02, T-06, T-08, T-09, T-14, T-15

Implementación acotada al adaptador informativo y su distribución; las guardias
nativas y el resto del catálogo permanecen en-progreso. Diseño previo en design.md.
La comparación dirigida del adaptador del corpus descubre el mismo contrato V1
incompatible; no se ejecuta ni incorpora su código. Commands/dashboard siguen
pendientes de comparación detallada; las skills continúan aplazadas.

Evidencia RED anterior a producción, 2026-10-08:

- tests/opencode-plugin.test.mjs: seis fallos por ausencia de default id/setup.
- Instalador: dos fallos por registro sin plugins nativo y dos por ausencia de
  retirarArtefacto; export: un fallo por ausencia del paquete V2 generado.
- Doctor: tres fallos (estado info/aviso frente a registro V2 esperado) al cambiar
  únicamente las fixtures antes del lector.
- Diagnóstico stderr: falla la expectativa de aviso; el adaptador absorbía el error.
- Cierre nativo: el modelo local termina correctamente, pero no aparece envelope.
  Fixture session.execution.succeeded falla dos veces con «Adapter effect was not
  observed», con ubicación explícita y sin ella, antes de modificar producción.
  El stream local observado entrega eventos terminales sin location. La corrección
  usa session.get para verificar siempre la ubicación y mantiene rechazo de eventos
  explícitamente ajenos; no reutiliza el directorio de instancia a ciegas.

Verificación parcial antes de revisión: Python Windows 241 passed/2 skipped;
launchers/adaptador 20 passed; instalador dirigido 9 passed y casos de retirada
3 passed. La primera ejecución Node completa tuvo tres fallos por arrancar antes
de regenerar el nuevo paquete; los tres pasan después de generar. No se oculta
ese fallo ni se presenta como una suite completa verde. Linter: cero errores/tres
avisos históricos. Export-interop: 55 archivos generados. Alcance contra 057e26e:
cero fuera/cero avisos; settings ajenos excluidos y conservados.

Prueba nativa en OpenCode 2.0.12: paquete instalado active, prompt UTF-8 y exclusión
private observados, contexto y herramienta write despachados por el runtime,
cierre terminal con envelope. Dos respuestas SSE del modelo simulado propio en
loopback; cero solicitudes a proveedores externos, sin credenciales heredadas.
Replay nativo en una nueva sesión, cobertura final y revisión independiente en curso.

## Revisión de dos lentes — intento 1: transporte OpenCode V2

Scope-check contra 057e26e: cero fuera/cero avisos; configuración ajena excluida.
Selector: C=false, D=true por callbacks esperados en el camino del modelo.
A/B/D independientes; fallback de herramienta genérica porque Agent(reviewer)
no está disponible. No se ejecutó código del corpus ni se enviaron mensajes externos.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A-1 | Minor | Docstring del índice describe transporte V1 | T-15 | Corregido; pendiente revalidación | Docstring V2 actualizado; prosa/config, TDD n/a |
| B-1 | Important | Cleanup resuelve antes de close con stdout excesivo/timeout | T-09 | Corregido; pendiente revalidación | Se espera close y terminación del árbol propio; test verde Windows |
| B-2 | Important | Patches indentados válidos pierden post-hooks | T-09 | Corregido; pendiente revalidación | Targets del resultado nativo; fallback trim; patch indentado y write normalizado verdes |
| D-1 | Important | Composición completa en cada continuación | T-09 | Corregido; pendiente revalidación | Caché efímera acotada; 50 iniciativas: 7890/5915/64/38/32/31 ms, medianas calientes 7506 → 38 ms |

RED adicional antes de corregir: native applied falla para patch indentado;
unchanged context falla por devolver context 2 en la segunda llamada. La garantía
de cleanup ya tiene rojo reproducido. Diseño ampliado antes de producción;
correcciones y revalidación independientes pendientes, sin deuda aceptada.

GREEN dirigido tras las correcciones: adaptador Windows 11 passed/0 failed.
Prueba nativa 2.0.12 posterior: active, dos loops y cuatro requests al modelo
propio en loopback, replay en segunda sesión observado, cero proveedores externos,
servidor terminado exit 0. La prueba propia de caché se amplía con TTL, cambios
concurrentes y colas personalizadas antes de QA final. Segunda revisión y cobertura
siguen pendientes; ningún criterio global se marca completado.

## Revisión de dos lentes — intento 2: transporte OpenCode V2

A/B/D frescas revalidan las correcciones con la tabla completa del intento 1.
A: cero gaps. B: B-1/B-2 corregidos, un Important nuevo. D: D-1 corregido,
sin hallazgos nuevos; fixture independiente 50 iniciativas × 8 archivos produce
5986/5978/151/175/158/193 ms, mediana caliente 166,5 ms (~45× menos que 7506 ms).

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A-1 | Minor | Docstring V1 | T-15 | Verificado por A | export-interop --check 55 al día |
| B-1 | Important | Cleanup anterior a close | T-09 | Verificado por A/B | Windows cinco dirigidos verdes; Linux cinco dirigidos verdes |
| B-2 | Important | Patches indentados pierden avisos | T-09 | Verificado por A/B | Patch indentado y input write distinto de target nativo verdes |
| D-1 | Important | Contexto completo repetido | T-09 | Verificado por A/D | Caché/invalidez/TTL/concurrencia probados y benchmark independiente |
| B-3 | Important | Move desde docs pierde origen eliminado | T-09 | Pendiente | B contrasta native output=false frente a fallback=true; RED native move out falla antes de modificar producción |

Se conserva el destino normalizado y se añade el origen absoluto del diff
nativo FileDiff.Info.patch: el runtime lo compone con la ruta original incluso
cuando files[].file y applied[].target describen el destino. No se usa el cuerpo
de la herramienta como una decisión nueva ni se publica documentación. Diseño
ampliado antes de esta corrección; intento 3 será solo sobre B-3 y criterios afectados.

B-3 corregido con la ruta del origen desde el diff nativo; GREEN native move out.
El contraste de generación de caché se hace después de esperar su firma final,
manteniendo la garantía frente a invalidaciones durante esa espera; GREEN de
mutación concurrente. Suite Node completa previa a estas últimas líneas: 139
passed/0 failed; QA de adaptador final y nueva prueba nativa en curso. No se
reanuda el catálogo de skills ni se consideran comparados commands/dashboard.

## Revisión de dos lentes — intento 3: transporte OpenCode V2

A/B/D de contexto fresco, tabla anterior completa y solo B-3/criterios afectados.
C sigue false según selector; D conserva la revisión de las últimas líneas.
Cero Critical/Important/Minor pendientes en este bloque, sin deuda aceptada.

| Criterio corregido | Veredicto | Evidencia independiente |
|---|---|---|
| B-3: move conserva origen y destino | ✓ | A Windows 2 passed; B Linux 2 passed; fuente oficial patchFile/fileDiff compone header con absolute original; test dedicado verde |
| Invalidación durante la firma final | ✓ | A/B verifican contraste de generation posterior al await; mutación concurrente verde |
| Coste de extracción y caché | ✓ | D: tres dirigidos verdes; extracción en 400 diffs/26,3 MB mediana 1,010 ms; no se añade recorrido a la firma |
| Docs y fuente única | ✓ | A: ES/EN/diseño coherentes; export-interop --check, 55 al día |

QA final del bloque, 2026-10-08:

- Python Windows 3.13: doctor/export/panel, 241 passed/2 skipped, 166,59 s;
  skips por bit ejecutable y symlinks no disponibles en Windows. Node 23.8:
  suite completa de adaptador/launcher/instalador, 139 passed/0 failed antes
  de las últimas líneas del move y guardado de caché; adaptador/launcher
  completos después de ellas, 25 passed/0 failed/0 skipped. Los módulos del
  instalador no cambiaron entre esas dos ejecuciones.
- Python encoding/índice de roadmap: 512 passed/0 failed, 128,56 s, antes del
  registro final. qa-gate VERDE: 917 ejecuciones passed, cero failed/flaky/
  interrupted, dos skipped; normalización de casos JUnit reales, incluidas
  las repeticiones dirigidas del adaptador, no una ejecución de Playwright.
- Cobertura del diff contra 057e26e: 299/306 = 97,71% (umbral ≥90%). c8 10.1.3
  mide líneas V8 de JS; coverage.py, líneas ejecutables Python. Cinco módulos
  de fixture son copias byte a byte del adaptador: se unen sus rangos V8
  manteniendo offsets y contrastando el SHA, sin atribuir cobertura al probe
  nativo Bun. Export index.js idéntico a la fuente, comprobado, no contado
  por duplicado. Líneas ausentes se conservan, incluida terminación POSIX
  no instrumentada en Windows.
- Pruebas dirigidas propias Linux/WSL con Node 23.8.0 aislado, checksum de
  SHASUMS256 oficial: cuatro passed (cleanup de árbol, stdout excesivo,
  caché/concurrencia), más dos finales independientes de B para move y
  concurrencia. No instalación global ni ejecución del corpus.
- Native OpenCode 2.0.12 después de la última corrección: active, dos loops,
  cuatro requests al modelo propio en loopback y dos prompts retenidos;
  captura UTF-8/private, contexto, write, cierre y replay de segunda sesión
  observados. Cero proveedores externos, sin credenciales heredadas, servidor
  terminado exit 0. runtime-probes.json separa la evidencia nueva del baseline.
- Migración CLI real en proyecto temporal propio: copia V1 conocida retirada,
  entrada antigua del manifiesto eliminada, contenido/config/permissions ajenos
  preservados, paquete V2 idéntico, segunda instalación idempotente. La primera
  fixture usó «./.opencode» para instructions, distinto del valor histórico
  «.opencode»; su conservación fue correcta. Fixture corregida al registro real.
- Linter: cero errores/tres avisos históricos. Skills permanecen aplazadas.
  Guardias/presupuestos nativos Claude/Codex y comparación detallada de
  commands/dashboard siguen abiertos; ningún task global se cierra por este
  bloque. No se activan backends ni se publica conocimiento de tareas abiertas.

Evidencias brutas locales ignoradas: opencode-v2-{python,node,adapter-final,docs}.xml,
opencode-v2-{qa-input,test-summary,diff-coverage,coverage-identity}.json,
opencode-v2-transport-probe.json y opencode-v2-migration-probe.json en
scratchpad/.venv. La cobertura deriva de c8/coverage.py oficiales; las fichas
públicas no incluyen rutas/credenciales de consumidores. Publicación en la
rama autorizada después de los últimos checks; sin merge ni release.

Checks del registro final: ledger-lint cero incoherencias/cero avisos;
test_roadmap_index 50 passed; export-interop --check 55 al día; diff --check
limpio. Scope-check: 28 archivos propios/cero fuera/cero avisos, settings ajenos
excluidos y conservados. Scan de esos contenidos/nombres sin marca del corpus.
El SHA publicado se contrasta con origin después del push a feat/catalog-capabilities.

## Revisión de dos lentes — intento 1: Fase 1 (T-02, T-05, T-06, T-08, T-09, T-14, T-15) — evidencia operativa

Lentes A+B por subagentes genéricos de contexto fresco: reviewer no disponible
como herramienta nativa. Scope-check contra 90a41f8: diez archivos propios
en alcance, cero fuera/cero avisos; settings ajenos excluidos y sin cambios.
Selector C/D false: solo documentación/evidencia, sin producción modificada.

| Criterio | Veredicto | Evidencia |
|---|---|---|
| Estados y alcance | ✓ | T-02/T-05/T-06/T-08/T-09/T-14/T-15 abiertas; aceptación global sin marcar |
| Comparación semántica | ✗ inicial | C004 tenía destino de conversación incorrecto; gap deduplicado A/B-1 |
| Constitución y dueños | ✓ | Sin segundo ledger, dependencias nuevas, escrituras ajenas ni acciones externas |
| Evidencia y límites | ✓ | Fixtures Claude fijadas, recovery y 12 hashes Codex; versiones, bypass y ausencia de evento separados |
| Exports y OpenAPI | n/a | No cambian hooks/agents/commands de producción ni spec API |
| Prosa, privacidad y trazabilidad | ✓ | Enlaces válidos, sin nombres públicos prohibidos y dependencias pendientes explícitas |

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A/B-1 | Important | C004 se consolidaba como conversación y perdía su contrato de checkpoints Git | T-05/T-08 | Separar C001 y C004; conservar SHA, diferencias de archivos y artefactos tests/cobertura en ledger/QA, sin stash/commit automático ni confundir con checkpoint de prompts. Corregido, pendiente de revisión independiente | Fuente C004:13–53 y propuesta privada coinciden; fila pública corregida |

Comprobaciones documentales ejecutadas: pytest test_roadmap_index, 50 passed
(0,10 s); ledger-lint cero incoherencias/cero avisos. Helper privado
check_operational_evidence.py: 60 registros de origen y 18 propios con
hash/bytes/líneas LF/rangos comprobados, 12 hashes privados Codex, cuatro
fixtures Claude coincidentes, recovery positivo, 56 enlaces locales válidos,
JSON/nombres públicos válidos y fuente fijada sin cambios; exit 0.
Son pruebas de trazabilidad y estructura, no eficacia ni entrega funcional.
TDD n/a: prosa/evidencia; los rojos nativos se conservaron en T-09. Sin
producción modificada, la cobertura ejecutable del diff no aplica.

## Revisión de dos lentes — intento 2: Fase 1 (T-02, T-05, T-06, T-08, T-09, T-14, T-15) — evidencia operativa sin gaps pendientes

A+B por nuevos subagentes genéricos de contexto fresco, con tabla completa
del intento anterior. Re-evaluación de la corrección y su traza; criterios
aprobados conservados salvo evidencia nueva. C/D no aplican en este diff
documental. Sin defectos restantes: cero Critical, Important o Minor.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A/B-1 | Important | Destino incorrecto de C004 | T-05/T-08 | Corregido y verificado independientemente: C001 conversación; C004 anclas Git/evidencia en ledger/QA, límites y recursos pendientes | A2 y B2 contrastan fuente C004:13–53, propuesta privada y filas públicas 52–53 |

Ambas lentes validan conservación de SHA, diferencias y artefactos tests/
cobertura, ausencia de stash/commit automático, sin log duplicado y sin
confundir journal con Git. No se promueven entradas de knowledge porque
este bloque no crea ninguna. Jira-flow del intento 1: ops vacías, Jira
desactivado; nada publicado. El intento 2 conserva la misma degradación.

Los gates documentales del intento anterior siguen aplicando; la corrección
solo cambia una fila de prosa. Comprobación final de ledger, correspondencia,
JSON, enlaces, nombres y alcance antes del commit; no se atribuye a esta
revisión QA funcional del plugin. Las tareas globales y el objetivo continúan
en progreso. Próxima implementación: activar caché Codex conservando scope
y preferencias, corregir cierre por defecto y probar el lifecycle terminal
real antes de anunciar guardias o paridad entre runtimes.

## Implementación de cierre e instalación — T-02/T-09/T-14/T-15

Trabajo paralelo autorizado por el usuario: captura y lifetime de procesos,
instalación/caché Codex y revisión independiente. Doctor, documentación y
traza coordinados por el orquestador. Las skills siguen aplazadas; ninguna
tarea global se cierra por este bloque. Base del diff: b5a611a.

La captura terminal se extrae a `journal-capture.py`: un solo writer durable,
sin importar la materialización del journal, con snapshot físico compartido
por identidad y secuencia. El launcher recibe el runtime por argumento fijo,
no por texto del consumidor. El export de Codex declara tres segundos y
añade `--runtime=codex`; OpenCode declara `--runtime=opencode` al lanzarlo.
La instalación Codex valida la caché nativa antes de activar el scope local.
Doctor y status distinguen declaración, listado nativo, confianza y ejecución.

Rojos observados antes de implementar, 2026-10-08:

- RED: `SessionEnd capture is independent of slow materialization startup`
  falló: sin envelope con arranque de materializador de dos segundos.
- RED: `test_capture_end_hash_y_sequence_comparten_snapshot_fisico` falló:
  sequence 2 combinada con hash del snapshot anterior de una línea.
- RED: `SessionEnd timeout terminates its child tree before returning` falló:
  un descendiente escribió después de retornar el launcher.
- RED: `test_capture_version_uses_packaged_runtime_manifest` falló: manifests
  Codex y package-only devolvían 0.0.0.
- RED: `test_partial_journal_bundle_reports_missing_capture_without_blocking`
  falló: exit 1 y traceback al faltar el helper canónico.
- RED: `test_native_capture_rejects_oversized_payload_without_partial_envelope`
  falló: payload excesivo producía envelope.
- RED: export `test_codex_hooks_respetan_limite_session_end_y_runner_windows`
  falló: SessionEnd sin argumento literal de runtime.
- RED: `native adapter identifies its runtime independently of consumer
  payload` falló: argv sin runtime declarado por el adaptador.
- RED: cinco casos de doctor para estado nativo fallaron por ausencia del
  lector; después, el caso relativo de B-I4 falló porque se resolvía dos veces.
  GREEN de los quince casos actuales, sin CLI del consumidor.

## Revisiones parciales de corrección — cierre e instalación

B por revisores genéricos de contexto fresco, porque Agent(reviewer) no está
disponible. Estos pases parciales no constituyen la puerta completa A+B+D.
Scope-check: 34 archivos propios, cero fuera/cero avisos; únicamente settings
ajenos excluidos. Selector: C false; D true por espera del supervisor, lectura
de configuración y export. Falta cerrar QA y revisión completa del payload final.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B-T1 | Important | Padre Python termina pero nieto conserva pipes y evita deadline | T-09 | En corrección: ownership del árbol independiente de exitCode | Fixture Windows: nieto mantuvo pipes 3163 ms tras salida del padre |
| B-T2 | Important | Grupo Python separado sobrevive al cleanup del adaptador POSIX | T-09 | En corrección: lifecycle del grupo y ownership del adaptador | Contraste de código; reproducción Linux del revisor no ejecutada por falta de binario local |
| B-I1 | Important | Claves TOML quoted/bare duplicaban tabla equivalente | T-09 | Normalizar segmentos decodificados y rechazar cabeceras inválidas; revisión 2 en curso | RED previo y tests dedicados del instalador |
| B-I2 | Important | Ruta relativa nativa entrecomillada eludía validación | T-09 | Clasificar clave decodificada y scope nativo; revisión 2 en curso | RED previo y fixtures typed paths |
| B-I3 | Important | MCP env.config_file se trataba como ruta nativa | T-09 | Clasificar por scope, no solo nombre final; revisión 2 en curso | RED previo y fixture MCP preservada |
| B-I4 | Important | Doctor duplicaba raíz relativa en cwd y argv | T-09 | Absolutizar una sola vez | RED dedicado, GREEN quince casos de wrapper/estado |
| B-I5 | Important | CLI tests heredaban PATH real | T-14 | HOME/configdirs/PATH propios con stubs y credenciales filtradas; revisión 2 en curso | RED de aislamiento y pruebas propias |

Hipótesis de upsert de marketplace descartada con evidencia: el binario
oficial fijado 0.161.0 rechaza un origen diferente ya registrado. Esto no
recupera una preimagen inexistente de la configuración del consumidor.

Incidente de aislamiento: un test antiguo llegó al registro real de Codex y
dejó `marketplaces.daycry` apuntando a una carpeta temporal. La creación del
backup de caché falló con AccessDenied antes de activar el plugin. No se
dispone de preimagen de esa entrada; su reparación requiere el origen
anterior consultado al usuario. No se restaura el config completo, no se
ejecuta chmod ni se afirma que todos sus bytes permanecieron intactos.
Los probes posteriores usan solo homes, PATH, proyectos y proveedores propios.
El audit privado de este incidente queda fuera de Git y no publica rutas del usuario.

La revisión automática rechazó limpiar directorios auxiliares vacíos creados
fuera del workspace con el motivo `blocked by policy`. Esa limpieza no se
reintenta; no impide continuar las correcciones del plugin. Sigue pendiente.

QA previa a la corrección de lifetime: journal 150 passed/10 skipped;
export 28 passed; adaptador OpenCode 14 passed; doctor 184 passed/1 skipped.
La ejecución instrumentada conjunta dio 357 passed/11 skipped/14 deselected;
los catorce casos excluidos son capacidades ajenas a este diff. No se usa
esta medición como cobertura final de fuentes que cambiaron después.
Pruebas nativas previas conservadas por hash en las fichas: Claude headless,
Codex app-server con archive del hilo activo y OpenCode V2 con replay.
La nueva supervisión obliga a contrastar otra vez el payload final antes del push.

Segundo pase B parcial del instalador: B-I1–B-I4 verificados corregidos;
B-I5 corregido en tests del instalador, reabierto con evidencia nueva en
`test_doctor.py:_status`, cuyo subprocess heredaba PATH y credenciales.
Nuevo Important B-I6: `execFileSync` con SIGTERM espera una CLI no cooperativa;
fixture Linux propia con timeout 200 ms retornó a los 1292 ms. Sin una salida
posterior, el catch de cleanup no se alcanzaba. Cero Critical/Minor.

- RED: `test_status_subprocess_no_hereda_cli_ni_credenciales_del_host` falló
  porque el PATH del subprocess contenía el directorio host simulado y una
  credencial sentinel. Corregido con entorno permitido y stubs propios para
  los tres runtimes; el subprocess no depende del mock inprocess de doctor.
- B-I6 en corrección: worker Node con watchdog asíncrono y pipes internos,
  que limpia el árbol antes de retornar; outer wait también acotado. El rojo
  propio Windows dejó un descendiente vivo y bloqueo de cwd al limpiar.
- La ejecución Python instrumentada posterior se interrumpió deliberadamente
  al detectar B-I5 en doctor. No cuenta como QA verde ni cobertura final;
  mostró además un fallo sin resumen final que debe resolverse al repetir.

Rojos dedicados de lifetime preservados, 2026-10-08:

- RED: `SessionEnd cleans descendants after its direct child has already exited`
  falló: marker del nieto presente tras la salida del padre Windows.
- RED: `cleanup of the real launcher reaches its Python process` falló:
  marker posterior al cleanup en POSIX con grupo Python separado.
- RED: `test_group_cleanup_keeps_owner_running_and_kills_children` falló:
  SIGSTOP al grupo owner y ausencia de SIGSTOP individual del hijo.
  Los tres escenarios tienen GREEN dedicado en las fuentes congeladas.

A completa sin gaps confirmados; D sin hallazgos de rendimiento atribuibles.
B intento 3 verifica T1/T2/I1–I4/I6 corregidos y devuelve un Important I5:
PATHEXT `.EXE` omitía nuestros stubs `.cmd` y podía ejecutar un codex.exe
vecino al Node incluido en PATH. Fixture independiente propia reprodujo
`hostSiblingRuntimeExecuted: true`, sin CLI del consumidor.
El bucle automático de tres pases se detiene. El orquestador decide continuar
únicamente con esta corrección de aislamiento de tests y su verificación
dirigida independiente; no acepta deuda ni reinicia el contador de revisión.

- RED: `test_status_stubs_no_dependen_de_pathext_del_host` falló porque el
  subprocess conservaba PATHEXT `.EXE`. Se fija el selector Windows del
  entorno de tests para incluir los stubs propios; GREEN de los dos casos
  dedicados de aislamiento. No cambia producción.
- QA Python de fuentes finales: 357 passed/11 skipped/14 deselected, más dos
  fallos de export viejo detectados mientras se terminaba de regenerar la
  distribución. Corrección por exportador canónico: --check exit 0, 55 al día;
  suite export completa posterior: 28 passed. No son fallos intermitentes de
  la misma fuente; la distribución generada cambió entre ambas ejecuciones.

Verificación independiente dirigida de I5 sobre el intento 3: misma fixture
Windows con Node/codex.exe propios y PATHEXT `.EXE`, ahora
`hostSiblingRuntimeExecuted: false`. B confirma cero gaps pendientes de su
tabla, sin ampliar el pase. El cambio solo afecta el entorno de tests.

## Revisión de dos lentes — intento 3: Fase 1 (T-02, T-09, T-14, T-15) — cierre e instalación

Fusión final A+B+D por subagentes genéricos: Agent(reviewer) no está disponible.
Los pases B parciales y sus correcciones se conservan arriba; A revisa el diff
completo y los contratos, plan y constitución; D revisa el diff completo y
fixtures de rendimiento. C no aplica según selector automático; D sí por
esperas del supervisor y lecturas síncronas de instalación/exportación.
Esta sección cierra el bloque de captura/lifetime, instalación y diagnóstico,
sin dar por terminadas las guardias ni las tareas globales de la iniciativa.

| Criterio A | Veredicto | Evidencia y límite |
|---|---|---|
| Scope y contratos por runtime | ✓ | Diff propio contrastado con Archivos; settings ajenos preservados; instalación ≥0.161.0 y límites de cada runtime documentados |
| Captura canónica y ownership del cierre | ✓ | Writer único; Job Object Windows y grupo POSIX; pruebas de descendientes, pipes y muerte del padre; evidencia nativa final en tres runtimes |
| Scope Codex y preferencias del consumidor | ✓ | Config temporal privada, caché compartida, validación antes de activar; restauración de source por clave; colisión con origen ajeno explícita |
| Doctor/estado y límites de observabilidad | ✓ | Consulta nativa compartida, estado desconocido cuando no hay evidencia; no equipara enabled con confianza o ejecución |
| TDD, QA y distribución | ✓ | REDs trazados arriba; baseline nativo y cinco REDs del lector; cobertura oficial del diff y export canónico. El RED inicial del helper no se recupera de su consola y no se inventa |
| Documentación y tareas abiertas | ✓ | ES/EN, changelog, evidencia fechada y hashes; T-01 sigue siendo la única tarea global completada |

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B-T1 | Important | Padre terminado y nieto conservando pipes evitaban deadline | T-09 | Corregido: ownership del árbol independiente de exitCode | RED de nieto Windows; GREEN runtime 34/34 y supervisor; cierre nativo final |
| B-T2 | Important | Grupo Python separado sobrevivía al cleanup del adaptador | T-09 | Corregido: ownership del grupo POSIX y cleanup sin detener owner | Dos REDs POSIX dedicados; cuatro casos Linux GREEN |
| B-I1 | Important | Claves TOML quoted/bare duplicaban tabla equivalente | T-09 | Corregido: segmentos decodificados y cabeceras válidas | RED de tabla comentada: 2 !== 1; tests instalador GREEN |
| B-I2 | Important | Ruta relativa quoted eludía validación nativa | T-09 | Corregido: clasificación por scope y clave decodificada | RED skills.config sin excepción; fixture relativa GREEN |
| B-I3 | Important | MCP env.config_file se confundía con ruta nativa | T-09 | Corregido: scope exacto de rutas tipadas | Fixture conserva env ordinario; revisión B sin gap |
| B-I4 | Important | Doctor duplicaba raíz relativa | T-09 | Corregido: raíz absoluta una sola vez | RED relativo; suite doctor y 18 casos finales de status/aislamiento GREEN |
| B-I5 | Important | PATH/PATHEXT permitían CLI del host en tests | T-14 | Corregido: entorno permitido y stubs seleccionados por PATHEXT propio | REDs sentinel y PATHEXT; verificación independiente dirigida hostSiblingRuntimeExecuted false |
| B-I6 | Important | CLI no cooperativa bloqueaba execFileSync tras deadline | T-09 | Corregido: worker con watchdog y cleanup, outer wait acotado | Reproducción Linux 200 ms → 1292 ms anterior; helper final 5/5 y cobertura 6/6 GREEN |

Cero Critical/Important/Minor pendientes en el bloque. La continuación
dirigida de B-I5 fue decisión explícita del orquestador tras detener el bucle
de tres intentos; no se contabiliza como cuarto pase global ni deuda aceptada.
La hipótesis de upsert sigue descartada con evidencia del binario fijado.
No se promueven entradas de knowledge: este bloque no creó ninguna.

D: cero hallazgos atribuibles al diff. 36 fixtures finales de cierre y seis
pares baseline/final; arranque externo domina las medidas y el baseline ya
supera 1,5 s en cinco de seis pares. Dos avisos de cleanup en 42 fixtures
conservaron envelope y status 0. No se promete latencia universal por debajo
del presupuesto nativo en cualquier equipo.

QA final: `qa-gate.py` VERDE, 1091 ejecuciones passed, 11 skipped, cero failed,
flaky o interrupted en la selección final. Son ejecuciones con repeticiones
dirigidas, no 1091 tests únicos. La clase export anterior completa (28 casos,
dos fallos) se sustituye por sus 28 casos GREEN tras regenerar; su XML rojo
permanece privado. La ejecución interrumpida no participa. Los 14 casos de
capacidades ajenas se excluyeron expresamente de pytest. Cobertura oficial
coverage.py/c8 de líneas añadidas ejecutables: **869/946 = 91,86%**, mínimo
90%; se conservan líneas sin cubrir. Los probes nativos no se usan como
cobertura instrumentada. [Resumen verificable](terminal-qa-evidence.json).

Payload del bloque anterior (snapshot 18f58e3) verificado nativamente:

- Claude 2.1.287: cierre headless, envelope antes de salida, debug SessionEnd
  completed status 0; el stream no emite respuesta SessionEnd.
- Codex 0.161.0: un app-server y archive del hilo activo; SessionEnd 1745 ms
  con timeout 3 s sin modificar, envelope antes de salida natural.
- OpenCode 2.0.12: dos loops activos, UTF-8, write/post, cierre y replay;
  43,829 s es duración de fixture completa, no latencia individual del hook.

Fichas públicas: [Claude](claude-hook-evidence.json),
[Codex](codex-lifecycle-evidence.json), [OpenCode](opencode-lifecycle-evidence.json),
[supervisión](terminal-capture-evidence.json) e
[instalación](codex-installation-evidence.json). Conservan hashes y resultados
anteriores sin atribuirlos al payload final. Homes, proyectos, proveedores
y credenciales de pruebas son propios; no se prueba TUI, todas las formas
de salida, confianza persistida, guardias por rol ni activación del consumidor.

Resolución del incidente de registro: el usuario eligió el repositorio
oficial `daycry/custom-agents`. Se cambian únicamente source_type y source
de marketplaces.daycry a git y https://github.com/daycry/custom-agents.git.
Se comprueba igualdad de toda la configuración parseada salvo esas dos
claves y de los tres payloads de caché conocidos. No se recupera la preimagen
desconocida, no se refresca ni activa la caché real. Audit privado sin
credenciales, fuera de Git. La limpieza rechazada por política sigue pendiente.

T-02/T-09/T-14/T-15 permanecen en-progreso por su aceptación global pendiente.
Siguiente bloque: identidad efectiva y allow/deny por rol; después comandos,
dashboard y recuperación de memoria. Skills siguen aplazadas: 79/293 evaluadas,
214 pendientes, cero altas de esa comparación en este bloque.

Jira-flow de esta fusión: `plan --event revision --actor reviewer --batch
--task T-02,T-09,T-14,T-15 --intento 3 --json`, ops vacías porque Jira está
desactivado; no se publica nada. La primera llamada sin --batch devolvió
error de argumentos y ops vacías; se corrigió la invocación, sin mutación.

Cierre documental independiente A: cero gaps confirmados y condiciones
previas resueltas. Verifica hashes de las doce fuentes finales, los diez
registros de QA, siete XML, cobertura y fichas nativas de los tres runtimes.
No certifica TDD histórico completo del helper cuyo RED inicial no se recupera.
Repite export --check exit 0/55; no cambia producción ni amplía la revisión B.

Verificaciones finales del bloque: linter 0 errores/3 avisos históricos de
nombres genéricos, ledger-lint 0 incoherencias/0 avisos, roadmap index 50 passed,
export 55 al día, git diff --check sin errores. Scope: 41 archivos propios,
cero fuera/cero avisos; settings ajenos excluidos y preservados. Correspondencia
histórica: 60 registros de fuente, 18 propios y 12 hashes nativos privados,
corpus sin cambios ni ejecución. Correspondencia final: hashes de producción,
fichas públicas/privadas y 100 enlaces locales comprobados; nombres públicos
limpios. Los hashes de doctor/journal en la lectura operativa son históricos,
conservados y contrastados con sus snapshots, no con el payload final.

## Siguiente bloque operativo — identidad y guardias nativas

El turno anterior fue progreso: commit/push 18f58e3 verificado remoto, cierre
nativo en tres runtimes y configuración source reparada por elección del usuario.
Se retoma T-02/T-08/T-09/T-14/T-15 sobre HEAD 18f58e3, sin tocar settings ajenos.
Tres investigaciones independientes en paralelo contrastan metadata y bloqueo
nativo por rol en Claude, Codex y OpenCode; solo fixtures propias y proveedores
loopback, sin ejecutar código del corpus. Diseño y criterios en design.md,
«Bloque 3». La lectura y los controles nativos positivos y negativos confirman
identidad en los tres runtimes. Nombre e
ID scoped no acreditan procedencia del prompt: se decide usar IDs propios
con semántica de rol protegido y una migración que preserve personalizaciones.
Las pruebas de mecanismo no se declaran implementación entregada.

Resultados paralelos preservados en native-role-contract-evidence.json:
Claude 14 casos, Codex 12 comprobaciones y OpenCode tres experimentos, incluidos
dos hijos reales. Los controles nativos demuestran ID efectivo, bloqueo previo,
sesión principal sin rol, rol ajeno permitido y límites de procedencia. Claude
usa política simplificada de fixture; Codex/OpenCode llaman al evaluador actual.
No se certifica normalización de todas las herramientas, instalación de la
guardia ni confianza persistida por estas pruebas.

Hallazgo reproducido del export Codex: sandbox_mode="read-only" en dos TOMLs
se acepta, pero ambos subagentes escriben sentinels vía Set-Content cuando el
padre tiene permiso. La proyección nativa no aplica ese campo ni hooks por rol.
Se corrige el export y la documentación activa ES/EN sin cambiar permisos del
consumidor. Los nombres canónicos/bare actuales aún no migran: el namespace y
su retirada segura pertenecen al siguiente bloque de integración.

- RED: test_reviewer_no_declara_sandbox_independiente_inexistente falló el
  2026-10-08 porque reviewer.toml exportaba sandbox_mode. Se corrige el productor,
  se regenera interop y el mismo caso queda GREEN.
- QA del bloque: export + roadmap, 78 passed. La primera cobertura no recopiló
  datos por usar un fichero como --source; no se usa como medición. Se repite
  export con --source=scripts, 28 passed y datos oficiales coverage.py válidos.
  El XML y la colección vacía anteriores se conservan privados.

Las descripciones activas de reviewer ya no prometen solo lectura por
construcción: su responsabilidad de no modificar código y las restricciones
reales por runtime quedan explícitas. Bash conserva permisos del runtime;
Write/Edit ausentes o permission.edit deny no cubren toda escritura indirecta.
No se incorpora ninguna skill ni se cambia el writer/lifetime del bloque previo.

La comparación de política previa queda en
[hooks-role-policy.md](comparisons/hooks-role-policy.md): 19 cuerpos completos,
un helper parcial y lecturas pendientes explícitas. Se prioriza protección
frente a bypass de verificación Git después de conectar el dispatcher; la
protección de configuración de calidad es candidata opt-in. Se descartan
retries como autorización. Ninguna de estas políticas nuevas se distribuye
en este bloque; no hay ejecución del corpus ni alta de paquetes técnicos.

## Revisión de dos lentes — intento 1: Fase 1 (T-02, T-06, T-08, T-09, T-14, T-15) — identidad nativa y permisos de reviewer

Nuevo bloque sobre base 18f58e3; no reinicia el bucle de cierre/instalación
anterior. Lentes A+B+D independientes y paralelas, con prompts literales;
fallback por subagentes genéricos porque reviewer no está disponible en esta
sesión. Selector actual: C false, D true por rutas del exporter y su suite;
no código de guardia añadido. Todas las lentes leen el diff completo y las
fichas nuevas; A/B contrastan las fuentes privadas sin ejecutarlas.

| Criterio | Resultado | Evidencia |
|---|---|---|
| Identidad y bloqueo nativos, T-02 | ✓ | 14 casos Claude, 12 checks Codex, tres experimentos OpenCode; hashes privados/públicos coincidentes, dos hijos OpenCode contrastados |
| Comparación acotada, T-06 | ✓ | 19 cuerpos completos, uno parcial, 24 inmediatos y 16 descendientes pendientes; 44 hashes/rangos comprobados |
| Diseño y entrega separados, T-08/T-09 | ✓ | IDs y migración previstos; dispatcher privado; campo Codex ignorado retirado, sin promesa de integración |
| RED/GREEN, QA y cobertura, T-14 | ✓ | Test rojo previo al productor, mismo test verde; QA 78 passed; coverage.py y diff ejecutable 5/5 |
| Export canónico y formato | ✓ | A/B/D ejecutan --check, exit 0, 55 ficheros al día; B ejecuta 28 tests, todos passed |
| Límites activos de reviewer, T-15 | ✗ | A-E3: productor y método conservaban garantía por construcción, replicada en los cuerpos generados |
| Corrección y rendimiento del código añadido | ✓ | B y D sin hallazgos; dos callsites coherentes, selección O(1), sin E/S ni recorridos adicionales |
| Alcance y estados globales | ✓ | Solo T-01 completada; settings ajenos excluidos, integración y confianza real pendientes |

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A-E3 | Important | Instrucciones activas prometen solo lectura por construcción | T-15 | Pendiente en intento 1; corregido y revalidado en intento 2 | agents/reviewer.md y skills/adversarial-review/SKILL.md conservaban el claim, copiado a ambos exports; contradicción con el límite nativo medido |

Fusión: cero Critical, un Important, cero Minor en intento 1. No se rebaja
el gap ni se declara deuda. Se corrige el productor canónico, se regenera
interop y se actualiza el método; no se altera el estado del consumidor.
TDD n/a para estos deltas de prompt/documentación. El RED/GREEN del cambio
ejecutable del exporter queda preservado arriba y en sus XML privados.

## Revisión de dos lentes — intento 2: Fase 1 (T-02, T-06, T-08, T-09, T-14, T-15) — instrucciones y exports coherentes

A reevalúa solo A-E3 y sus deltas, sin reabrir lo aprobado. Verifica
agents/reviewer.md, la instrucción del método y ambos cuerpos regenerados;
responsabilidad de no modificar y permisos reales de Bash quedan explícitos.
Ejecuta --check: exit 0, 55 ficheros al día. Comprueba XML actual: 78 tests,
cero fallos/errores/skipped. B/D del intento 1 se conservan: no hay nuevo
cambio ejecutable desde sus dictámenes. A-E3: **corregido**. Cero gaps
Critical/Important/Minor pendientes; no hay entrada de memoria propuesta
nueva en este bloque para promover.

QA actual: [role-contract-qa-evidence.json](role-contract-qa-evidence.json),
qa-gate VERDE exit 0, **78 tests únicos passed**, cero failed, flaky,
skipped o interrupted. El input deriva de JUnit pytest, no de Playwright.
Cobertura oficial coverage.py 7.16.2: **5/5 líneas ejecutables añadidas,
100%**, mínimo 90%, solo el exporter; no se cuentan copias generadas como
código adicional. La primera colección sin datos no participa; XML/datos
anteriores permanecen privados. Los probes nativos no se suman al conteo.

La corrección y la evidencia del mecanismo quedan entregables. T-02/T-06/
T-08/T-09/T-14/T-15 permanecen abiertas por su aceptación global. Siguiente
paso concreto: conectar política central con metadata nativa, normalizar
todos los targets soportados y migrar IDs propios preservando agentes de
usuario. Después comandos, dashboard y recuperación de memoria; skills
siguen aplazadas en 79/293 evaluadas, 214 pendientes.

B contrasta por separado la derivación de la ficha QA final: 78 identidades
únicas, XML sin fallos, hashes oficiales coincidentes y diff recalculado
5/5, sin volver a ejecutar el publicador ni abrir otra revisión global.

Jira-flow de ambos intentos: gaps/revision, actor reviewer, batch, tareas
T-02/T-06/T-08/T-09/T-14/T-15; exit 0 y ops vacías porque Jira está desactivado.
No se publica ningún mensaje externo.

Gates finales: export --check 55 al día; linter 0 errores/3 avisos históricos
de nombres genéricos; ledger-lint 0 incoherencias/0 avisos; roadmap index
50 passed tras actualizar la traza. No se suman esas repeticiones a los
78 tests únicos de QA. Scope contra 18f58e3: 25 archivos propios en alcance,
cero fuera/cero avisos, settings ajenos excluidos. Checker final: 199 enlaces
locales, 22 hashes de procedencia nativa y 44 hashes/rangos del corpus
coincidentes, fuente fijada limpia, JSON y nombres públicos válidos, cero
referencias prohibidas. El exporter y las fuentes finales quedan fijados
en role-contract-qa-evidence.json; los hashes previos en terminal-qa-evidence.json
pertenecen al snapshot 18f58e3. Sin ejecución del corpus ni activación de la
caché real. La limpieza rechazada por política sigue pendiente.

## Bloque en progreso: guardias con identidad nativa y migración de agentes

Base: `8b51edd9ae1af020e0eb96bf92933e1f55edbaed`. T-02/T-08/T-09/T-14/T-15
siguen abiertas. Implementación local todavía sin revisión final, commit ni push.
Skills aplazadas: 79/293 evaluadas, 214 pendientes; sin ampliar el catálogo.

El dispatcher selecciona IDs propios de un mapa generado por runtime y consulta
la política central existente. No acepta el rol declarado dentro del input de la
herramienta. Codex y OpenCode exportan nombres con prefijo del plugin. La migración
usa manifiesto y hashes, conserva archivos ajenos/modificados y declara estado
incompleto ante conflictos. El contexto expone IDs del runtime. OpenCode evalúa
antes de ejecutar, sin reutilizar decisiones entre llamadas.

Evidencia TDD privada conservada, 2026-10-08:

- RED: entrada nativa del launcher falló por `unknown hook` antes del destino
  directo Python; mismo test GREEN para los tres runtimes.
- RED: entrada de contexto recibió `missing` antes de propagar el runtime fijo;
  mismo test GREEN.
- RED: timeout de branch y lectura limitada de config fallaron por `TypeError`
  antes de extender las APIs centrales; mismos tests GREEN, defaults conservados.
- RED: adapter OpenCode permitió escrituras protegidas antes de `execute.before`;
  mismos tests GREEN con política real. Diagnóstico de opt-out: RED y mismo GREEN.
- RED: MultiEdit incompleto perdió el diagnóstico; mismo test GREEN. El stand-in
  inicial descartado no cuenta como evidencia TDD.
- RED: installer sobrescribía un agente del consumidor; GREEN de conflictos,
  junction exterior, estado incompleto e ID propio desde otro nombre de archivo.
- RED: descripción del export no compartía el ID del mapa; mismo caso GREEN.

QA parcial: núcleo Python **140 passed**, normalizador **82 passed** y cobertura
oficial de su diff **202/206 = 98,06%**; installer dirigido **9/9**, V8 oficial del
diff **188/194 = 96,91%**. No se suman estos conjuntos como tests únicos ni se
presentan como QA final. Exporter: **56 archivos al día**. La suite amplia del
installer conserva un fallo de fixture: consultas a la CLI simulada rozan 3 s;
se reproduce `cli-timeout` sin cambio funcional en config/cache. Se corrige el
shim de prueba antes de dar por válida la suite; no se cambia producción.

La distribución real detectó un defecto pendiente: Claude recibe JSON `deny`,
pero el proceso no termina dentro de 5 s; el runtime descarta la decisión y
permite escribir. El control aislado sin suites concurrentes reproduce el fallo
(callback total 6.261 ms). Codex también registró un callback cancelado de 5.115 ms.
Se conservan protocolos y archivos fallidos y se investiga cierre/cleanup antes
de declarar eficaz la protección. OpenCode observa bloqueo anterior a escritura
en su primer caso real; matriz completa e hijos siguen en ejecución. No se afirma
paridad completa ni sandbox para herramientas arbitrarias.

El marketplace local Codex se reparó con autorización: origen Git oficial
`daycry/custom-agents`. Solo cambian dos campos; el resto de config y tres hashes
de payloads cacheados coinciden. No se refresca ni activa la caché real.

Registro posterior: PreToolUse Claude/Codex **10 s**, adapter OpenCode **10,5 s**,
presupuesto interno **4,5 s**, contención conservada. El diagnóstico privado de
una copia instrumentada midió 802 ms y no reprodujo hang; se conserva separado
de las pruebas de eficacia. La distribución final Codex 0.161.0 alcanza **14/14
checks de guardia** reales: deny de spec implementer, src architect y force Git;
allow de tasks/design/planner/agente bare/chat principal; metadata de los hijos
correlacionada y hashes de cache/fuente coincidentes. Los callbacks previos tardan
3.350–8.032 ms y no agotan los 10 s. La fixture usa catálogo de modelo compatible
del cliente y proveedor loopback propio, sin credenciales ni cambios del usuario.

El mismo experimento conserva **dos checks SessionEnd fallidos**: timeout nativo
de 3.041 ms y sin envelope en outbox antes del exit. Un experimento anterior sí
capturó envelope antes de un aviso de timeout. No se publica 16/16 verde, no se
amplían los 3 s ni se confunde captura con materialización. Se investiga el coste
de arranque/cierre y la recuperación del prompt retenido por separado. La matriz
Claude de 10 s ya acredita bloqueos y permisos, pero sigue en ejecución. OpenCode
verificó efectos correctos; una fixture anterior omitía cargar los prompts de
agente al desactivar discovery de proyecto, por lo que no cuenta como aceptación
de la distribución completa; la fixture final debe acreditar el prompt cargado.

Claude final: **13/13 casos nativos passed**, cinco deny aceptados antes de escribir
y ocho allow; todos con salida natural 0. Incluye cuatro hijos reales, controles
bare/principal y override explícito del mismo ID. Las fuentes ejecutables de
guardia coinciden en todos los casos; los primeros prompts preceden correcciones
de prosa, con hashes por caso preservados. La proyección pública en
[native-role-integration-evidence.json](native-role-integration-evidence.json)
excluye rutas privadas, prompts y payloads; no afirma todavía OpenCode completo.

Diagnóstico separado de memoria: dos copias instrumentadas, sin cambio de
producción, midieron escritura del envelope en 45/63 ms. El mínimo venv completó
SessionEnd en 2.704 ms; el mínimo base escribió antes de un timeout de 3.077 ms
durante cierre. El coste previo a Node fue 1.623/2.498 ms. No se confunden esos
diagnósticos con pruebas de eficacia de la distribución intacta. En el fixture
original cerrado sin envelope, `journal.py recover` recuperó **1 de 1 candidata**
desde el prompt UTF-8 retenido, sin avisos y con `recuperado_sin_cierre`. Es prueba
de recuperación a demanda; no acredita retoma automática por TTL. Se mantiene
el fallo de cierre original visible y la aceptación global de memoria abierta.

## Revisión de dos lentes — intento 1: guardias nativas y migración sobre 8b51edd

Scope previo: 101 archivos propios en alcance, cero fuera/cero avisos;
`.claude/settings.json` ajeno excluido. Selector: C true por ruta de sesión;
D true por lectura síncrona del instalador y exporter. Fallback de reviewer por
subagentes genéricos con prompts literales y contexto fresco. B/C independientes
ya finalizaron; A/D pendientes. No es todavía una revisión final aprobada.

| # | Grado | Gap | Tarea | Estado y evidencia |
|---|---|---|---|---|
| B-1 | Important | `splitlines()` divide caracteres Unicode/CR dentro de contenido patch válido y degrada a allow | T-09 | Corregido en productor, pendiente revalidación independiente. RED 24 fallos + 2 CRLF válidos; mismos 26 GREEN y suite 108 passed. Delta nativo Codex Unicode: deny de spec y tasks permitido con 29 bytes UTF-8 exactos, salida natural 0; snapshot conservado |
| B-2 | Important | Preflight ignora `agents` V2 y puede retirar un bare referenciado | T-09 | Corregido en productor, pendiente revalidación independiente. Test dedicado RED/GREEN; se inspeccionan ambos mapas `agent`/`agents`, con IDs y referencias `{file:…}` |
| C-1 | Important | Contexto válido ` *** Add File: …` se confunde con header, permitiendo Update protegido | T-09 | Corregido en productor; pendiente revalidación independiente. RED seis fallos y ocho controles válidos; mismos catorce GREEN, suite 122 passed. Deltas nativos Codex y OpenCode: Update protegido intacto y Update permitido con contenido UTF-8 exacto; snapshot 9827f5fd preservado |
| R-1 | Important | `Environment ID:own` válido sin espacio no se reconoce y degrada la guardia a allow | T-09 | Corregido en productor, pendiente revisión final y delta nativo. Se conserva RED contra gramática pinned OpenCode y GREEN en mismos casos; parser final 3347254b |
| R-2 | Important | Heredoc con delimitador válido distinto de EOF, con o sin `cat`, degrada la guardia a allow | T-09 | Corregido en productor según `stripHeredoc` nativo: delimitador ASCII, comillas emparejadas y whitespace ECMAScript. RED 17 fallos reales, 34 dirigidos GREEN y suite 156 passed; cobertura 211/215 = 98,14%. Revisión final y delta nativo pendientes |
| B-3 | Important | Una referencia `{file:…}` fuera de `agent`/`agents` puede perder su agente bare durante migración | T-09 | Corregido en productor; referencias en valores/claves de toda config, sin reclamar IDs desde comandos. `~/` y variables de entorno no resueltas conservan archivos con diagnóstico. RED/GREEN dedicados; tests actuales 16/16, cobertura 231/235 = 98,30%. Revisión final pendiente |

No se rebajan hallazgos ni se aceptan como deuda. Los tests dedicados y deltas
nativos deben conservarse con hashes de cada snapshot. La matriz ASCII previa
no se anuncia ejecutada contra el parser corregido; sirve como baseline junto
a las regresiones y los deltas posteriores. Los fallos SessionEnd no pasan a
verde por haber aprobado las guardias.

La lente A no encontró nuevos gaps de requisito o constitución en el bloque;
la aceptación de sus criterios de publicación y QA sigue pendiente. La lente D
no encontró regresiones de rendimiento medibles. OpenCode final acredita ocho
casos baseline (seis de matriz y dos hijos reales), más cuatro casos de regresión
Unicode/contexto sobre el parser 9827f5fd, con prompts de agente verificados y
salida natural cero. Los experimentos fallidos de modelo/seed de fixture se
conservan separados; no cuentan como pruebas verdes.

QA de raíz sobre ese snapshot: **180 tests Python passed**. Node: **36/37**
pasaron; SessionStart emitió `child cleanup confirmation timed out` en el primer
pase y pasó sin cambios de fuente en el reintento dirigido (**1/1**). La evidencia
mantiene ambos resultados y el test se registra como flaky, sin afirmar una
causa raíz demostrada. Cobertura oficial del diff del launcher, adapter y APIs
centrales: **69/71 = 97,18%**. Quedan las correcciones de gramática/referencias,
su revalidación independiente y la consolidación de QA del bloque.

Jira por intento 1: `jira-flow.py plan --event gaps --actor reviewer --task T-09
--intento 1 --json`, exit 0, `ops: []`; configuración desactivada, sin publicación.

## Revisión de dos lentes — intento 2: guardias nativas — límites de patches

La comprobación técnica dirigida B verificó las correcciones B-1/B-2/B-3/R-1/R-2
contra tests RED/GREEN y hashes actuales. La lente C de contexto fresco confirmó
de forma independiente un nuevo gap R-3; es la misma causa señalada por B, no dos
defectos distintos. No se declara revisión aprobada ni cierre de T-09. La tabla
completa del intento 1 se conserva arriba; no hay rebates ni deuda aceptada.

| # | Grado | Gap | Tarea | Corrección y evidencia |
|---|---|---|---|---|
| R-3 | Important | Los límites entre archivos después de Add/Delete requieren trim nativo, pero el normalizador preserva indentación como en Update y permite el patch protegido por degradación | T-09 | Corregido en parser 43f6c5ce: Add/Delete usan trim ECMAScript; Update conserva contexto con trimEnd estructural. RED/GREEN, C-1 retenido; revisión 3 y delta nativo pendientes |
| R-4 | Important | `strip()`/`rstrip()` Python no retiran BOM donde `trim()`/`trimEnd()` nativos sí lo hacen, y un patch protegido válido degrada a allow | T-09 | Corregido en parser 43f6c5ce: whitespace ECMAScript en headers/rutas/marcadores; EOF no convierte whitespace posterior en contenido. RED 40 fallos reales + tres controles, mismos 43 GREEN y suite 199 passed; cobertura oficial 227/231 = 98,27%. Revisión 3 y delta nativo pendientes |

El pase final usará revisores nuevos y revaluará las correcciones, con el estado
de esta tabla. La evidencia nativa iniciada antes de R-3 conserva su snapshot
3347254b; se añade un delta propio para la última corrección. No se reescriben
resultados previos como si hubieran ejecutado la fuente final.

Jira por intento 2: `jira-flow.py plan --event gaps --actor reviewer --task T-09
--intento 2 --json`, exit 0, `ops: []`; desactivado, sin publicación.

El normalizador extrae mutaciones de los esquemas soportados; no reimplementa
el validador ni la aplicación de patches del runtime. Conserva la tolerancia
previa para move-only y chunks vacíos, sin afirmar que el runtime los acepte.
Las decisiones por targets y la exención de enlaces de diseño siguen evaluadas
por el script central, con contenido/contexto UTF-8 original preservado.

## Revisión de dos lentes — intento 3: guardias nativas — validación de rutas

La lente C de contexto fresco finalizó sobre parser 43f6c5ce: **un Important
pendiente, cero Critical/Minor**. Su nueva evidencia impide aprobar el bloque.
El pase final conjunto A/B/D y el push no se completan: se alcanza el límite de
tres intentos y se devuelve la decisión de continuación. Las correcciones previas
no se promueven a aceptación global ni se marca completada ninguna tarea abierta.

| # | Grado | Gap | Tarea | Corrección y evidencia |
|---|---|---|---|---|
| R-5 | Important | Validar la ruta con `path.strip()` Python rechaza un nombre U+0085 válido y omite la guardia de otro archivo protegido del mismo patch | T-09 | Pendiente, CWE-863. Repro propio de C: primer Add con ruta NEL y segundo Delete de spec devuelve continue/input-unrecognized; primer Add src/a y mismo Delete devuelve deny. Fuente native-guardrail.py:58, hash 43f6c5ce. Contrato ECMAScript conserva NEL; resolución/aplicación pinned no elimina el carácter. Sin ejecutar upstream |

Propuesta de continuación: alinear la comprobación de ruta vacía con el conjunto
de whitespace ya definido, conservar NEL como parte del nombre y verificar todos
los targets. Exigir RED/GREEN del mismo payload, control permitido, prueba nativa
aislada e independiente revisión final antes del commit/push. No se ha aplicado
esta corrección tras alcanzar el límite; no se acepta el gap como deuda.

QA de raíz final del snapshot: **257 tests Python passed**, incluido el parser
199/199. OpenCode conserva 24 casos nativos entre baseline y deltas: ocho baseline,
cuatro Unicode/contexto, seis Environment/heredoc y seis sangría/BOM. Cada cohorte
conserva sus hashes; los seis últimos prueban R-3/R-4 con la fuente 43f6c5ce, no
R-5. Salidas naturales cero y controles permitidos con bytes exactos. La ficha
pública declara revisión no aprobada; unit tests verdes no resuelven este gap.

Las protecciones adicionales de migración conservan bindings de
`command`/`commands.*.agent` y las definiciones legacy `mode`, según contrato
pinned. La presencia de comandos Markdown en las capas conocidas impide retirar
exports bare, sin intentar interpretar YAML: las copias nuevas siguen su
preflight. Se conserva diagnóstico; el estado puede quedar incompleto aunque no
haya bare que retirar, porque cualquier aviso afecta al estado del instalador.
Esta limitación se registra, sin anunciar una migración plenamente verificada.

Consolidación QA del bloque (sin aprobar la revisión): **374 identidades únicas**,
373 passed y un flaky justificado; cero failed/skipped/interrupted. Los XML se
unen por identidad y se conservan el fallo inicial y reintento de SessionStart.
Installer final 19/19 y cobertura 272/276 = 98,55%; hash LF 2edeab74.
Cobertura oficial agregada del diff ejecutable: **663/677 = 97,93%**. Excluye
generados, JSON, prosa y tests. [native-role-qa-evidence.json](native-role-qa-evidence.json)
declara `review_approved: false` y R-5 pendiente; el verde de unit tests no
autoriza publicación. Jira por intento 3: exit 0, `ops: []`, desactivado.

Decisión de continuación solicitada al usuario el 2026-10-08: autorizar otro
ciclo acotado para corregir R-5 y completar revisión, o replanificar. El usuario
autorizó explícitamente corregir y completar la revisión. No se hace commit/push
de esta implementación sin resolver el gap.
La última entrega remota comprobada continúa en 8b51edd.

## Revisión de dos lentes — intento 4: ciclo adicional autorizado — R-5

Autorización expresa del usuario tras el límite de tres intentos; nuevo ciclo
acotado de hasta tres pases (intentos 4–6) para corregir y completar la revisión.
La plataforma rechaza crear revisores nuevos con
`agent thread limit reached`. Se revalidan las correcciones con los revisores
anteriores, independientes de quienes las implementaron. Se declara la pérdida
de contexto fresco; no se presenta esta degradación como un pase de agentes nuevos.

R-5 corregido en productor bbd3608c: validación de ruta vacía con whitespace
ECMAScript, conservando NEL. RED real de 17 regresiones, mismos 17 GREEN;
suite 216 passed y cobertura oficial 227/231 = 98,27%. Sin cambio de API/política.
La auditoría del normalizador no encuentra trims sin charset. La lente C verifica
la corrección de forma independiente. Delta OpenCode real: dos casos con parser
bbd3608c; el Delete protegido se bloquea antes de ambos efectos, el Delete
permitido y Add NEL conservan bytes exactos. Salida natural cero. Las cohortes
anteriores mantienen sus hashes originales.

La limitación de diagnóstico Markdown sin legacy se corrige en este ciclo:
se conserva el discovery acotado y el impedimento de retirar bare no verificable,
pero el aviso se emite solo cuando hay una copia antigua real. Test dedicado RED
por warnings inesperados; GREEN del mismo caso y dos controles de preservación
(3/3). Installer final LF cbcd7d50: 20 casos dirigidos, 19 pasan y el A/B falla
por consulta nativa de fixture no disponible. Primer reintento A/B vuelve a
fallar; una consulta mínima y una copia diagnóstica pasan, sin acreditar el test
canónico. Un posterior reintento del mismo test canónico pasa sin cambios en
fuente, límites ni assertions. Se conserva como flaky con los tres XML; no se
atribuye una causa demostrada. Cobertura oficial del diff installer: 276/280 =
98,57%. Fuentes y limitaciones históricas permanecen en los registros.

La lente D encuentra R-6 Important: un heredoc sin cierre con 16.000 LF y JSON
de 32.187 bytes excede 5.002 ms después de READY, por encima del presupuesto
interno de 4.500 ms. La expresión regular reintenta la apertura con coste
cuadrático. No se acepta como deuda ni se cambia el presupuesto para ocultarlo.
Jira por intento 4: exit 0, `ops: []`; desactivado, sin publicación.

## Revisión de dos lentes — intento 5: scanner lineal y evidencia final

R-6 corregido en normalizador 17fcd2ba: scanner lineal de heredoc, conservando
delimiter ASCII-word, quotes coincidentes, `cat` opcional, whitespace ECMAScript,
cierre literal y cuerpo exacto. TDD: dos fallos RED acotados tras READY y tres
controles preválidos; mismos cinco GREEN. Suite 221 passed, cobertura oficial
255/261 = 97,70%. No cambia la API, política central ni los permisos nativos.

La lente B independiente compara 20.000 casos pequeños con la gramática previa:
cero diferencias. La lente D compara 4.608 casos, 576 wrappers reconocidos y cero
discrepancias. Sus cinco evaluaciones por caso tras READY miden máximos de
2,565 ms para cierre ausente/mixto y 24,473 ms para casos válidos protegidos o
permitidos; todos por debajo de 4.500 ms y 64 KiB JSON. Corpus acotados, sin
afirmar equivalencia universal. Revisores reutilizados por límite de plataforma,
independientes de la implementación; no se declara contexto fresco.

Delta OpenCode real sobre el parser final: dos casos heredoc, deny protegido y
patch permitido con bytes exactos, prompts nativos cargados y salida natural
cero. La ficha [native-role-integration-evidence.json](native-role-integration-evidence.json)
conserva 28 casos OpenCode por cohortes, 13 Claude y 14 checks Codex baseline
más su delta; cada snapshot identifica su fuente. No anuncia toda la matriz
ejecutada contra el parser final ni transforma SessionEnd en verde.

QA final: 282 tests Python de raíz passed, 221 del parser incluidos. Se unen
reportes por identidad con exports, installer y Node: **397 identidades únicas**,
395 passed, dos flaky justificados, cero failed/skipped/interrupted; qa-gate
exit 0. Los fallos de SessionStart y A/B siguen visibles y sus reintentos no
suman pruebas únicas. Cobertura oficial agregada del diff: **695/711 = 97,75%**.
[native-role-qa-evidence.json](native-role-qa-evidence.json) recoge fuentes,
instrumentos y límites. La lente A acepta el bloque con todos los criterios
conformes: alcance, R-5/R-6, eficacia/trazabilidad de cohortes nativas, migración,
QA/flaky, cobertura, generado/documentación y constitución. Lentes A+B+C+D:
**0 Critical, 0 Important, 0 Minor pendientes**. Los hallazgos de los intentos
anteriores quedan corregidos y revalidados, sin rebates ni deuda aceptada.

| # | Grado original | Gap | Tarea | Corrección y evidencia |
|---|---|---|---|---|
| R-5 | Important | Ruta NEL omitía otro target protegido | T-09 | Corregido; RED/GREEN, delta OpenCode bbd3608c y revalidación C/A |
| R-6 | Important | Heredoc incompleto excedía presupuesto interno | T-09 | Corregido; scanner 17fcd2ba, dos RED/cinco GREEN, 221 tests, equivalencia B/C/D, medición D tras READY y delta nativo final |

Se acepta y autoriza publicar **este bloque**, con contexto reutilizado declarado.
Ninguna tarea global abierta ni la memoria se marca completada. ADR-023 se
promueve en memoria local; sustituye la ubicación exclusiva de ADR-007 y
mantiene su alcance por rol. Esos documentos locales están fuera de Git.
Jira por intento 5: `revision`, exit 0, `ops: []`; desactivado, sin publicación.
Puertas finales: lint_plugin cero errores/tres avisos históricos de nombres;
56 exports al día; ledger-lint cero incoherencias/cero avisos; scope-check
104 archivos propios en alcance/cero fuera y un settings ajeno excluido entre
105 cambios detectados. Scan de 881
archivos públicos: cero referencias o nombres prohibidos. Diff sin errores.
Publicación comprobada el 2026-10-08: commit
`54e8b3f8e117bfc1f9f4a83951f77631541b1549`, push de
`feat/catalog-capabilities` exit 0 y `git ls-remote --heads` coincide con HEAD.
Después del push, 56 exports siguen al día y el único archivo sin seguimiento
es `.claude/settings.json` ajeno, intacto y nunca incluido en el commit. La
memoria local ADR-023/ADR-007 también permanece fuera de Git. Este registro
documenta la entrega verificada del bloque; T-02/T-08/T-09/T-14/T-15 conservan
sus pendientes globales. Las skills siguen aplazadas en 79/293 evaluadas.

## Bloque operativo 5 — diagnóstico con acciones prioritarias

Base comprobada: `d3a2490a798485f5b0f982b6e04f2b55bd9c633b`. El turno anterior
fue progreso: corrigió y publicó guardias/IDs/migración con SHA remoto verificado.
Se continúa T-05/T-08/T-11, conservando skills aplazadas y aceptación global abierta.

Comparación pertinente completa: C030 (84 líneas), motor R-3d9f69328581
(1.085 líneas) y callers A031 (55) / S052 (46), contra revisión fijada y hashes
coincidentes. Lectura estática, sin ejecutar el corpus. No cierra globalmente
esos callers ni integra skills. El contraste propio cubre filas, registros,
ensamblado, rendering y CLI de doctor, ambos comandos doctor/setup y exportación
de sus cuerpos; no se afirma lectura de todos los checkers de doctor.

Diseño registrado en design.md antes de producir código. Dueño: doctor;
añadir acciones derivadas a JSON/Markdown y actualizar consumidores/docs.
Se conserva el contrato de filas y se descartan scores de inventario. El panel
se investiga en paralelo; su selector hoy no cambia la fuente de hooks y no
reconoce los handlers Codex con argumento runtime. Ese gap alimentará el siguiente
bloque, sin convertir la presencia de archivos en carga o ejecución probadas.

TDD/QA en progreso. Un test histórico diagnostica el repo real; se trasladará
a proyecto temporal con fuentes propias antes de correr la suite, para conservar
la comprobación del linter sin leer `.claude/settings.json` ajeno. No hay push
de este bloque hasta verificar implementación y revisión.

## Bloque operativo 6 — hooks por runtime en el panel

Investigación paralela completada: 29 lecturas propias/de origen con hashes y
rangos privados, diez hashes de origen coincidentes. Siete recursos releídos
completos y tres entrypoints parcialmente; se conservan sus lecturas completas
históricas sin cerrar dependencias globales. No se ejecuta código del corpus.

Repro propio del reader actual: los tres selectores presentan ocho handlers
Claude y SessionEnd 5 s; Codex declara 3 s. Regex de metadata no reconoce guardia
ni argumentos runtime. Footer conserva ubicación anterior de guardias y móvil
oculta Fuentes. Navegación y seis etapas ya tienen solución y tests históricos;
no se atribuye su bug antiguo al estado actual.

Diseño Bloque 6 registrado antes de producir código. Dueños: build_panel,
plantilla y contrato de bindings consumido por adapter OpenCode. T-06/T-08/T-13
y sus gates se aplican en paralelo al Bloque 5. Mantener estados de carga y
ejecución desconocidos, fuentes/runtime y presupuestos exactos; sin nuevo
servidor, escritor de memoria ni conexión de servicios. TDD, QA y delta nativo
propio pendientes; no se publica este bloque hasta su revisión independiente.

### Implementación y QA de los Bloques 5/6

Doctor incorpora `acciones_prioritarias` sin cambiar filas, conteos o exit:
errores antes de avisos, desempate canónico, total completo y hasta tres acciones
con bloque/ordinal. Markdown presenta esa selección antes de las tablas. El
test de linter utiliza consumidor temporal y la suite aísla homes/registro;
el settings ajeno no se lee. TDD: diez RED iniciales, diez GREEN; un RED de
orden Markdown y once GREEN finales. Suite Windows final **207 passed/1 skipped**
(chmod); Linux **207 passed/1 skipped** (PATHEXT). Cada caso omitido por plataforma
pasa en la otra. Cobertura oficial del diff **19/19 = 100%**. La primera
invocación de cobertura por filepath no produjo datos válidos; se conserva
como diagnóstico rechazado y se utiliza el informe final por módulo/directorio.

Panel incorpora fuentes independientes, 23 handlers y **17 grupos** declarados:
Claude 8/6, Codex 8/6, OpenCode 7/5. Muestra fuente/localizador, función, activación,
guardia por ID y procedencia/unidad del presupuesto. Booleanos, no finitos e
integer de 400 dígitos degradan a inválido; handlers no identificados permanecen
desconocidos. El JSON estricto consumido por OpenCode gobierna registros,
handlers, filtros y supervisión, sin importar JavaScript desde el catálogo.
No se modifica el normalizador, launcher, mapa de roles ni installer.

TDD panel: 17 RED iniciales → GREEN; dos RED de número/mapa booleano → nueve
GREEN; cinco RED de comportamiento/bindings incompatibles → cinco GREEN.
Adapter: tres RED de catálogo inexistente → GREEN; suite Windows **19/19**.
Cobertura oficial del diff Python **167/168 = 99,40%**, adapter **33/34 = 97,06%**.
Suite panel tras B1: Windows **84 passed/2 skipped** por symlinks; Linux final
**85 passed/1 skipped** por junction Windows. Las omisiones de plataforma quedan
cubiertas por los controles de la otra plataforma. La plantilla se ejercita
mediante DOM real y navegador, fuera de esos denominadores de statements.

Navegador Edge: nueve casos finales pasan, sin retries automáticos. Inventario,
filtro de los tres runtimes, presupuestos e identidades, enlaces, foco/historial,
destino ausente, seis etapas, Fuentes móvil, movimiento reducido, skip link y
extensiones independientes. Dos ejecuciones previas se conservan rechazadas:
arranque Edge con directorios de perfil falsos/largos, y selectors del runner
que incluían extensiones al contar catálogo. Se corrigen entorno y selectores,
conservando las assertions; no se presentan como passes ni como fallos del panel.
La generación inspecciona solo fixtures/homes propios; Edge usa perfil temporal
nuevo y conserva los known folders del sistema necesarios para arrancar.

El [delta nativo OpenCode](panel-native-delta-evidence.json) verifica dos casos
con el adapter modificado: deny previo al observer, patch permitido con bytes
exactos, cuerpos de agentes nativos cargados, notificación documental observada
y salida natural cero. Proveedor loopback y homes/config/proyecto propios; no
activa caché del consumidor. No acredita todos los handlers informativos ni
captura durable de memoria. Los snapshots anteriores permanecen inmutables.

QA adicional: export-interop regenera 56 archivos y `--check` confirma los 56
al día; tests del exportador **35 passed**. `evals/check`: 51 piezas, 182 casos,
cero errores. Linter cero errores y tres avisos históricos; ledger cero/ cero.
Gates finales, contraste de entorno Linux, revisión A y publicación aún pendientes.

## Revisión de dos lentes — intento 1: Bloques 5/6 (T-05/T-13) — filtro de extensiones

Nuevo ciclo acotado para este diff desde `d3a2490`, separado del bloque de
guardias aceptado en intento 5. Contexto fresco: lentes B y D genéricas porque
el tool `reviewer` no está disponible. Selector automático: C false; D true
por await en los bucles del adapter. D no encuentra degradación introducida:
tres handlers secuenciales y cuatro registros ya existían; doctor añade dos
pasadas lineales y panel tiene fuentes/inventario acotados. A queda para el
diff y evidencias finales; este pase no acepta ni publica el bloque.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B1 | Important | Excepción de runtime de catálogo aplicada también a extensiones | T-13 | Corregido tras el pase; condición limitada a `sectionId === 'catalog'` | Tres RED reales Node/DOM (agent/skill/mcp) → tres GREEN, suite 84/2, Linux 85/1, navegador H-09 |

Sin rebates ni deuda aceptada. Cero Critical/Minor; el único Important se
traspasa a intento 2 para revalidación independiente. Jira del pase: `gaps`,
exit 0 con `--batch`, `ops: []`, desactivado; sin publicación. La primera llamada
sin `--batch` fue rechazada antes de generar operaciones y se corrigió.

## Revisión de dos lentes — intento 2: Bloques 5/6 (T-05/T-13) — revalidación de B1

Lente B nueva, contexto fresco, recibe la tabla completa del intento 1:
reevalúa solo la corrección y no reabre áreas aprobadas sin evidencia nueva.
Confirma B1 corregido, hashes congelados y regresión 3/3; su control independiente
recorre 2.592 combinaciones de runtime/tipo/origen/búsqueda, sin discrepancias.
Cero Critical/Important/Minor en B. Se conserva el veredicto D sin cambio de
productores que altere su análisis; A y QA final todavía no autorizan entrega.

Jira del intento 2: `revision`, exit 0 con `--batch`, `ops: []`, desactivado;
sin publicación. Cuatro casos históricos de navegador de extensiones también
pasan después de actualizar su contador a grupos runtime/evento. La generación
y ejecución usan consumidores propios y conservan sin cambios sus fixtures.

### Puerta QA final de los Bloques 5/6

[panel-command-qa-evidence.json](panel-command-qa-evidence.json) une reportes
canónicos por módulo/título: **361 identidades únicas**, todas con ejecución
positiva, cero failed/flaky/interrupted y ninguna omisión sin cubrir. Los skips
por plataforma conservan identidad/motivo en cada reporter y su pass en el
otro sistema; no se convierten en tests nuevos. `qa-gate.py` exit 0, VERDE.
Cobertura oficial agregada del diff **219/221 = 99,10%**; cada script supera 90%.
No se suma dos veces la copia generada del adapter ni se incluye HTML en el
denominador de statements Python/Node.

Linux adapter final **19/19**, exit 0. Se conservan preparaciones rechazadas:
imagen sin `ps` y sin reaper, y snapshot crudo del checkout Windows con CRLF.
A/B con adapter/tests originales `d3a2490` reproduce las mismas tres identidades
de fallo; `/proc` comprueba hijos zombie con PPID 1. Imagen QA privada derivada
del pin existente incorpora procps de fuentes oficiales Debian; las pruebas
corren offline con `--init`, tar/runner propios readonly y salida propia,
sin montar workspace, home ni socket. Con procps pasan las dos limpiezas;
queda un fallo de contexto. `bash -n` reproduce `in\r` en el shell crudo y pasa
con LF. Las ocho normalizaciones en la copia QA obedecen `.gitattributes` y
coinciden byte/hash con los blobs canónicos de HEAD y `d3a2490`. La suite final
canónica pasa sin cambiar fuentes, tests, assertions ni plazos. No se borra ni
presenta como verde ninguna preparación rechazada.

Las rutas, hashes y conteos de XML RED/GREEN, oficiales de cobertura, reportes
de navegador y QA Linux figuran en la ficha pública. Evidencia privada de
doctor en `scratchpad/.venv/doctor-priorities-*`; panel/adapter Windows en
`scratchpad/.venv/dashboard-comparison/`; Linux doctor en
`scratchpad/.venv/doctor-linux-ba9b7f4a15f0/`; panel final en
`scratchpad/.venv/panel-adapter-linux-final-8fb8dc5c4423/`; adapter LF final y
prueba de checkout canónico en `scratchpad/.venv/panel-adapter-linux-procps-image/`.
Estos artefactos no se versionan; la ficha exporta exclusivamente datos propios
acotados y hashes, sin prompts, memoria privada ni credenciales.

### Aceptación acotada y parada solicitada

La lente A fresca contrasta fuentes, diff, tests, docs, las fichas y todos los
hashes/reporters privados del QA público; cuenta de forma independiente las
361 identidades. Conformidad por criterio: comparación C030/destinos, diseño
previo y alcance, prioridades/empates/límite/filas/exit/CLI, fuentes/grupos/
handlers/identidades/presupuestos/desconocidos, lectura acotada/catálogo consumido,
UI y delta nativo, TDD/ejecución/cobertura, documentación ES/EN/constitución.
Todos ✓. Su propio `export-interop.py --check`: exit 0, 56 archivos al día.
Lentes **A+B+D**, contexto fresco mediante subagentes genéricos; C no seleccionada
por el selector automático. **0 Critical, 0 Important, 0 Minor pendientes**.
B1 queda corregido y revalidado, sin rebates ni deuda. Los Bloques 5/6 se
aceptan para publicar; el intento 2 cierra este ciclo acotado.

No se crearon entradas nuevas de conocimiento que promocionar en estos bloques;
las anteriores aceptadas se conservan fuera de Git. Las fichas de lectura
históricas mantienen el estado anterior a entrega. Se consolida un concepto
de comando (C030) en doctor; no se suman nuevas skills ni se cierran los callers
globales. Tampoco se cierran T-02/T-05/T-06/T-08/T-09/T-11/T-13/T-14/T-15 globales
o la eficacia de memoria. El 2026-10-08 el usuario solicita explícitamente
hacer los commits, push de la rama y **parar al acabar este bloque**. No se
inicia la siguiente fase ni se reanudan las 214 skills pendientes.

### Publicación verificada de los Bloques 5/6

Implementación y documentación: commit
`363d0c95ca4069ec1a51af8c4dc6a944197b67cc`, 41 archivos propios.
Push a `feat/catalog-capabilities` exit 0; `git ls-remote --heads origin`
confirma exactamente ese SHA. Tras el push, `export-interop.py --check` sigue
en exit 0 con 56 archivos al día. Solo permanece sin seguimiento el
`.claude/settings.json` ajeno; no se leyó, modificó ni incluyó en el commit.
Scan de 869 archivos públicos: cero nombres/referencias prohibidos. Scope:
41 propios en alcance, settings ajeno excluido, cero fuera y cero avisos.
Linter cero errores/tres avisos históricos; ledger cero incoherencias/cero avisos.

Este registro se incorpora en un commit documental separado. Se conserva la
instrucción de detener el objetivo tras publicar, con pendientes globales
documentados, sin iniciar otra fase. El panel local actualizado está generado
fuera de Git; no contiene fixtures de extensiones ni configura el consumidor.

## Bloque operativo 7 — diagnóstico de cierre y contrato de memoria

El usuario pide continuar después de la parada anterior. Base `470e92e`,
T-02/T-07/T-09/T-14/T-15; nuevas skills todavía aplazadas. Se aplica
`debug-root-cause`: no modificar el cierre sin hipótesis probada. La evidencia
histórica de timeout nativo y falta de envelope se conserva, sin extrapolar
el tiempo del negocio a toda la ejecución. Contrato Codex reconsultado en
`https://learn.chatgpt.com/docs/hooks`: SessionEnd síncrono, default 1 s,
máximo 3 s; `async` no amplía el presupuesto. Fuente oficial local
`d27764b82f7118f674371e6d6e76271d9d606edb`,
`codex-rs/hooks/src/events/session_end.rs`, constantes 20–23.

La auditoría de T-07 confirma documentación obsoleta en la skill existente:
Graphiti presentado como futuro y toda consulta atribuida al stack externo,
pese a las funciones de lectura/router presentes. Se reconcilian mapa,
contrato y docs ES/EN; no se incorpora otra skill ni se activa un servicio.
Las referencias de proveedores son instrucciones al servidor, sin acreditar
modelo efectivo o coste. Se elimina la promesa genérica de captura <100 ms.
FLOWS distingue presupuestos/eventos por runtime y actualiza el claim antiguo
de guardias solo por frontmatter con el dispatcher ya entregado.

Archivos del bloque documental: skill y README del adaptador existentes,
README raíz ES/EN, docs/README ES/EN, FLOWS ES/EN, changelogs ES/EN y roadmap.
TDD n/a: prosa; producción del cierre intacta hasta prueba de causa. Se
validarán contratos existentes, lint/evals/exports/ledger y revisión A+B.
No se cierran tareas globales ni se atribuye utilidad medida a un backend.

### Diagnóstico y corrección del entorno de QA del Bloque 7

La primera tanda produjo 405 elementos JUnit: cuatro fallos; pytest declara
399 tests y dos subtests pasados. Se conserva íntegra, sin convertirla en verde.
El runner directo del exportador falla al recibir tests con fixtures; pytest
es la invocación compatible y pasa los 35 tests en base y cambio actual.

Contraste A/B con las mismas fuentes y memoria curada en copias privadas:
base `470e92e` y actual reproducen los tres fallos de knowledge-find; el
scanner de hooks pasa en ambas copias sin bytecode. No se modifica el scanner.
La caché `.pyc` local hizo fallar su lectura UTF-8 estricta en el workspace.

RED: `test_show_imprime_la_entrada_completa_tal_cual` y
`test_show_json_envuelve_el_contenido_con_su_ficha`: la fixture escribe CRLF
en Windows aunque los assertions requieren el contenido LF original.
Solo fijar `newline="\n"` en la escritura privada hace pasar ambos tests.
La corrección pública aplica esa misma escritura, sin alterar el lector.

RED: `test_ca03_related_adr010_grafo_curado_en_menos_de_1600_caracteres`
exige ADR-007 en una vista humana topada a seis entradas por grupo. Al
crecer el corpus puede quedar fuera de la vista. El test ahora exige
ADR-006/ADR-007 en la relación JSON completa, conserva el tope de 1600
caracteres y exige el marcador si ADR-007 no cabe en la vista compacta.
Fuentes/tests ejecutables de producción intactos; cobertura del diff n/a
porque el único código modificado es de prueba.

## Revisión de dos lentes — intento 1: Fase 2 (T-07, T-15) — contrato y diagnóstico parcial

Lentes A+B por subagentes genéricos frescos, sin agente reviewer nativo
disponible; tier declarado opus/high, sin override de proyecto. Scope exit 0;
selector C/D false, sin motivos. Ninguna lente implementó los cambios.

| Criterio | Veredicto | Evidencia |
|---|---|---|
| Contratos de memoria y proveedores vigentes | ✓ | A1/B1 contrastan router, `puede_leer`, adaptadores y proveedores |
| Diagnóstico sin promesa de fix ni cierre global | ✓ | Tres cohortes separadas; hashes instrumentados/originales; histórico abierto |
| Alcance, espejos y generación | ✓ | Scope cero fuera; A1 ejecuta export --check: 56 al día, exit 0 |
| No activar backends ni añadir skills | ✓ | Solo mapa/docs/evidencia; estados globales preservados |
| Verificación final no inventada | ✓ | QA aún pendiente al revisar; ninguna T global cerrada |

Gaps: cero Critical/Important/Minor. B1 verifica 12 hashes de evidencia y 15
snapshots de cohortes. La tanda QA posterior expone problemas de fixture/
invocación ya registrados arriba; los cambios de tests requieren el intento 2.

Jira del intento 1: `jira-flow.py plan --event revision --actor reviewer
--task T-07,T-15 --batch --intento 1 --json`, exit 0; desactivado, `ops: []`.

## Revisión de dos lentes — intento 2: Fase 2 (T-07, T-14, T-15) — fixtures de memoria

Lentes A+B por nuevos subagentes genéricos frescos; C/D false, sin motivos.
Traspaso íntegro de aprobación A1/B1, sin reabrirla al no existir evidencia nueva.
Scope exit 0: tests bajo T-14/T-15, resto del bloque bajo su alcance previo.

| Criterio | Veredicto | Evidencia |
|---|---|---|
| Fixture LF sin cambiar assertions ni lector | ✓ | A2/B2 leen línea 122; A/B y variante LF verificadas |
| Relaciones completas y salida humana acotada | ✓ | JSON exige ambos IDs; ≤1600 y aviso de truncado conservados |
| RED/GREEN con procedencia explícita | ✓ | A2/B2 verifican hashes XML/logs; GREEN privado equivalente, no byte idéntico al test público |
| Generados y contratos mantenidos | ✓ | A2 ejecuta --check: exit 0, 56 archivos al día |
| QA y aceptación global no inventadas | ✓ | Suite final aún en marcha al revisar; ninguna T global cerrada |

Gaps: cero Critical/Important/Minor. La QA final debe validar el test público
exacto en el snapshot con overlay, no atribuirle por identidad el GREEN privado.

Jira del intento 2: `jira-flow.py plan --event revision --actor reviewer
--task T-07,T-14,T-15 --batch --intento 2 --json`, exit 0; desactivado, `ops: []`.

### Resultado del diagnóstico nativo y QA final del Bloque 7

[SessionEnd reducido](session-closure-diagnosis-evidence.json): Codex 0.161.0,
dos cierres instrumentados completan captura antes de salir en 1251/1492 ms.
El segundo usa cero turnos y cero peticiones al proveedor; el primero una
petición a un stub local propio. Un override con shell anidado falla en 864 ms
por comillas y se rechaza. Hashes originales e instrumentados diferenciados.
El mínimo no reproduce el timeout histórico bajo carga de subagentes;
no hay causa probada ni cambio de producción. La fiabilidad sigue abierta.

La primera copia final produjo 402/403 pruebas de memoria verdes: el único
rojo hereda el Git del workspace y su exclusión de scratchpad en vez de un
`.gitignore` propio. Se conserva el resultado. Inicializar Git únicamente en
la copia de QA corrige esa fixture: el delta dedicado pasa 1/1. La repetición
completa posterior tiene artefactos separados, sin sobrescribir ningún rojo.

[QA final](memory-contract-qa-evidence.json): **403 pruebas de memoria + 35
de exportación = 438 identidades únicas**, cero fallos, errores, skips o flaky;
qa-gate VERDE. Memoria: 246,78 s; exportación: 1,74 s. Es una tanda dirigida,
no toda la suite del repositorio. Entorno Python 3.13.0/pytest 8.4.2, homes y
Git propios, sin `.pyc`; servicios simulados locales. El entorno inicial
reporta 403 casos padre y dos subtests separados; el final ejecuta los
subtests dentro de su caso padre. No se han eliminado pruebas por ese conteo.

[Contraste causal y procedencia](memory-contract-test-diagnosis-evidence.json):
917 hashes de la copia siguen intactos tras ejecutar (865 fuentes + 52 archivos
de memoria curada). El test público coincide exactamente con el snapshot:
SHA256 `9bbf23e962b92a4e15aadd98c740189f28a861b6d45bef5ed4fe26a94ed2864e`.
Los dos RED de `--show` y el RED de relación compacta quedan verdes con los
cambios registrados; no cambia el lector, el scanner ni código de producción.
Cobertura del diff n/a: solo prosa y código de fixtures de prueba.

Dos checks independientes adicionales verifican GOT-017, sus cuatro campos,
unicidad, fuente e índice. Detectan una frase Minor en la ficha causal que
atribuía LF explícito también al README: se corrige a entradas sintéticas;
ambos revalidan el delta y aprueban con cero gaps. GOT-017 se promociona con
traza `aceptada (validada: revisión de dos lentes, 2026-10-08, intento 2)` en
su entrada e índice locales, ignorados por Git. No se promociona ninguna
otra propuesta. Esta entrada nueva es posterior a la fixture congelada de
52 archivos de QA; no se atribuye su validación a esa tanda.

Aceptación acotada: documentación, diagnóstico parcial y fixtures corregidas.
Sin nuevas skills, activación de backend, configuración del consumidor ni
cierre global de T-02/T-07/T-09/T-14/T-15. La auditoría completa de memoria,
el benchmark de Graphiti y la reproducción causal del cierre siguen abiertos.

### Puertas finales y límite del verificador de revisión

Lint final: cero errores, tres avisos históricos de nombres. La promoción de
GOT-017 requería entrecomillar `estado` por sus dos puntos internos; se corrige
solo esa serialización YAML y el lint vuelve a verde. Evals: 51 piezas,
182 casos, cero errores. Export --check: 56 archivos al día. Ledger: cero
incoherencias/cero avisos. Diff --check: exit 0. Scope contra `470e92e`:
18 archivos propios en alcance, cero fuera, settings ajeno excluido, cero avisos.
Scan público: 872 archivos, cero nombres/referencias prohibidos; excluye el
settings ajeno antes de leer. No se publica memoria local ignorada por Git.

Incidente acotado del selector: su invocación `--base 470e92e` incluye todos
los archivos sin seguimiento y lee indirectamente `.claude/settings.json`.
No se mostró su contenido ni se modificó o añadió al índice. Se detecta al
inspeccionar el verificador y se registra la lectura; no se afirma aislamiento
de ese comando inicial. La repetición usa `--files` con los 18 archivos propios
explícitos: C/D false, sin motivos ni avisos, excluyendo settings antes de
cualquier lectura. El aislamiento de las copias de QA sigue acreditado por
sus manifiestos; no se extiende esa afirmación al primer selector del workspace.

### Publicación verificada del Bloque 7

Commit de cambios y evidencia:
`80689b79e166415e19ebcf88b4039e27eae44546`, 18 archivos propios.
Push a `feat/catalog-capabilities` exit 0; `git ls-remote --heads origin`
confirma exactamente ese SHA. Tras el push, export --check sigue en exit 0
con 56 archivos al día. Solo permanece sin seguimiento `.claude/settings.json`;
no se modificó ni incluyó en los commits. GOT-017 e índice de memoria local
siguen fuera de Git; el incidente de lectura del selector consta arriba.

Este registro de entrega se incorpora en un commit documental separado.
No se declara cerrada la iniciativa ni se inicia otra fase en esta entrega.

## Bloque operativo 8 — cierre bajo carga y recuperación canónica

El usuario reactiva el objetivo completo tras la entrega `b8e6192`. El turno
anterior produjo progreso verificable: dos commits publicados y 438 tests verdes.
Skills aplazadas; foco hooks/comandos/panel/memoria. Tres auditorías independientes
en paralelo: causalidad del cierre, continuidad por comandos y gobierno local.
No leen settings ajenos, conversaciones o journals ni ejecutan código del corpus.

El contraste de cierre fija dos fixtures frescas y hooks completos iguales,
variando solo actividad de dos hijos nativos frente a raíz. La instrumentación
no corta el despacho del stub. Producción y límite de 3 s intactos hasta prueba
causal. Es diagnóstico privado, TDD n/a; resultados y límites pendientes.

Auditoría local identifica dos huecos funcionales: el corpus recuperado omite
`approved/` y el router pierde `version`. Diseño de extracción y contrato
aprobado en design.md. RED antes de producción: ocho fallos en
`tests/test_knowledge_approved_retrieval.py` (1,45 s), approved-only ausente,
show/related exit 1, fallback vacío, caché sin entradas y `KeyError: version`.
Segundo RED: nueve fallos de corpus inválido, ambigüedad, independencia de
config de servicio y traversal. Logs propios separados bajo
`scratchpad/.venv/memory-approved-retrieval/audit-red-20261008-01/` y `-02/`.
El diseño preserva legacy, estados y políticas de promoción; no activa backend.

RED adicional `-03`: dos fallos demuestran que configuración/enabled de backend
inválidos eliminaban la lectura local. RED `-04`: nueve fallos cubren categoría
con carpeta propia, prioridad de aprobado, enlaces explícitos fuera del área,
versiones remotas bool/list/dict/controladas y junction hacia candidatos.
Estos casos preceden sus correcciones; los logs anteriores quedan intactos.

### Contraste nativo bajo carga: resultado parcial

[Evidencia de carga](session-closure-load-evidence.json): cuatro fixtures propias
con Codex 0.161.0 y hooks completos. Los cuatro manifiestos contienen 326 archivos
idénticos, comprobados en distribución y caché. SessionEnd del plugin informa
`completed` en 1308/2338/1807/3075 ms; todos capturan un envelope de raíz correcto
antes de salir naturalmente con código 0. Se conserva el 3075 tal como lo devuelve
el runtime: no se declara cumplimiento estricto de tres segundos.

La primera muestra con dos hijos permite crear `src/architect.txt` protegido:
su guardia termina con entradas vacías después de expirar el presupuesto hijo,
sin job header registrado. El mismo payload evaluado directamente devuelve
deny. Hay líneas de trace intercaladas inválidas, preservadas con línea/hash;
la ausencia de un stage no se trata como prueba absoluta. Los controles
posteriores bloquean, pero varían turnos/tiempos y no prueban que cambiar de
intérprete resuelva el fallo. No hay cambio de launcher, supervisor o guardia.
La eficacia de guardias y la fiabilidad de cierre permanecen abiertas.

### Comparación de continuidad sin otro almacén

[Ficha de continuidad](comparisons/commands-session-continuity.md) y su evidencia
registran lecturas de cuerpos, recursos y contratos propios. Proponen una
fachada de retoma de solo lectura sobre journal/progress/ledger, con selección
exacta y pruebas históricas distinguidas del estado vigente. No está implementada,
no aumenta el conteo global de fichas ni crea aliases, servicios o fases nuevas.
Las lecturas parciales y la cadena secundaria pendiente quedan explícitas.

### Validación inicial conservada, sin aceptación prematura

La primera cobertura Windows del snapshot de fuentes propio mide 460/499 líneas
ejecutables añadidas (92,18 %). Ejecuta 407 passed/1 skipped/4 failed: tres fallos
son dependencias ausentes de la copia (`evals/check.py` para copias declaradas),
y uno hereda el Git ancestral de scratchpad. Esos resultados se conservan;
el harness siguiente necesita dependencias completas y un Git propio antes
de atribuir verde. El skip es una fixture symlink de Windows, por justificar
con su identidad exacta en la evidencia final. Linux, sin memoria real, pasa
las pruebas sintéticas de symlinks; los skips de corpus real no cuentan como
validaciones ejecutadas de ese corpus.

Lint del workspace detecta un alias `_TAXONOMY_FALLBACK` de compatibilidad sin
fila de registro en schema. Evals: 51 piezas/182 casos, exit 0. Export interop
--check: 56 archivos al día, exit 0. Portable privado: 189 archivos, check 0.
Ledger: cero incoherencias/avisos. Estas comprobaciones no sustituyen la QA
ni cierran la revisión del código; el lint rojo requiere corrección validada.

## Revisión de dos lentes — intento 1: Fase 2 (T-07, T-08, T-14, T-15) — Bloque 8

Lentes A+B+C por subagentes genéricos frescos: reviewer nativo no disponible;
tier frontmatter opus/high, sin override. Scope contra `b8e6192`: exit 0,
cero fuera/avisos; settings ajeno excluido. Selector con ocho archivos propios
explícitos, excluyendo settings antes de leer: C true por SQL f-string con
columnas constantes; D false. C verifica parametrización y contención sin
hallazgos. A ejecuta export --check (56 archivos, exit 0). QA final pendiente.

| Criterio | Veredicto | Evidencia |
|---|---|---|
| Recuperación, ID/version, categorías, enlaces, caché y respaldo local | ✓ | A/B leen diff completo y tests sintéticos; B ejecuta 36 passed |
| TDD y límites de evidencia/estado global | ✓ | RED previos conservados; ningún T global cerrado |
| Documentación bilingüe y generados | ✓ | Contrato/índices/FLOWS/changelogs; export --check 0 |
| Registro de alias de compatibilidad | ✗ | A reproduce lint rojo en schema |
| Nuevas aristas con puerta declarada | ✗ | A cita CONTRACTS regla de alta |
| Datos opcionales incompatibles degradan sin perder legado | ✗ | B reproduce TypeError en query con/sin índice |
| Helpers ausentes degradan sin traceback | ✗ | B contrasta CLI nuevo y base en kits propios |
| Seguridad introducida | ✓ | C: SQL parametrizado, rutas contenidas, lector sin red; 11 tests propios passed |

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A1-01 | Important | Alias `_TAXONOMY_FALLBACK` sin registro, schema:188 | T-07/T-15 | pendiente: binding declarado y test de identidad, sin copiar literal | lint dirigido y lint workspace rojo |
| A1-02 | Important | find/index/schema → helpers no están en CONTRACTS | T-08/T-15 | pendiente: filas de contrato con puerta | CONTRACTS:11–12 y diff |
| B1 | Important | `area: [test]` admitida en approved aborta también legado | T-07/T-14 | pendiente: validar campos usados por recuperación y degradar con motivo | reproducciones propias query/--no-index, find:549–552 |
| B2 | Important | Kit parcial sin nuevos helpers aborta al importar | T-07/T-14 | pendiente: carga y API/CLI con diagnóstico | index:90/schema:54; contraste exacto con base |

Fusión: cero Critical, cuatro Important, cero Minor. No se rebate ni rebaja
ninguno. Producción congelada durante revisión; la siguiente corrección exige
RED dedicado y otro intento antes de QA/entrega. Detalles privados A1/B1/C1
preservados, sin publicar payloads ni contenido del consumidor.

Jira del intento 1: plan `--event gaps --actor reviewer --task T-07,T-08,T-14,T-15
--intento 1 --batch --json`, exit 0; desactivado, `ops: []`. Nada publicado.
Corrección A1-02: CONTRACTS declara E25–E28 con firmas/resultados y suites
ejecutables; incluye la arista interna local → taxonomy además de las tres
aristas de consumidor. TDD n/a: documentación, pendiente revalidación A2.

### Corrección del intento 1 con RED dedicado

RED `-05`: trece fallos reproducen metadatos opcionales incompatibles en caché/
recorrido plano y imports de helpers ausentes. RED `-06`: el test A1 demuestra
la definición adicional del respaldo en schema. RED `-07`: cinco fallos de
evidencia y tags incompatibles completan la frontera de metadatos consumidos.
Logs originales separados y conservados. GREEN `-06`: 55 passed, 13,64 s.

A1-01 se corrige mediante reexportación estándar `__getattr__`: el wrapper
devuelve el mismo objeto del helper y no define otro respaldo. No se debilita
el registro ni se fabrica una segunda copia; template/helper siguen siendo
los únicos cuerpos comparados. El test dedicado verifica identidad y lint.
B1 valida forma de etiquetas consumidas solo al recuperar; el índice completo
conserva su política anterior. B2 captura carga fallida y devuelve diagnóstico
en API/CLI; sin helper no finge validación ni copia el parser.

Fuentes finales congeladas en `frozen-20261008-03`, con Git/HOME propios,
dependencias de copias declaradas y sin memoria real/bytecode. QA Windows con
JUnit y cobertura, QA Linux equivalente y revisión 2 siguen pendientes al
escribir esta nota. No se altera la evidencia de snapshots rechazados.

## Revisión de dos lentes — intento 2: Fase 2 (T-07, T-08, T-14, T-15) — Bloque 8 corregido

Lentes A+B+C por subagentes genéricos frescos; traspaso completo del intento 1,
sin reabrir aprobados ni hallazgos rebatidos (no hubo rebates). Scope exit 0;
C aplica por el SQL de columnas constantes, D false. A ejecuta export --check:
56 archivos al día, exit 0. Revisión anterior a la aceptación final de QA.

| Criterio | Veredicto | Evidencia |
|---|---|---|
| A1-01: respaldo único y reexportación de compatibilidad | ✓ | A verifica identidad, ausencia de definición adicional y test de lint |
| A1-02: contratos nuevos declarados y vigilados | ✓ | E25–E28, nueve columnas, puertas y docs correspondientes |
| B1: metadatos inválidos conservan legado | ✓ | A/B: tipos solo include_source; B reproduce seis campos con/sin caché |
| B2: kit parcial sin traceback | ✓ | B: helpers ausentes, SyntaxError y RuntimeError, API/CLI con diagnóstico |
| TDD, docs bilingües, generados y límites globales | ✓ | A: RED -05/-06/-07, estados abiertos, --check 0 |
| Seguridad introducida | ✓ | C: rutas fijas, delegación limitada, schema completo intacto, SQL parametrizado |

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A1-01 | Important | Definición de respaldo adicional | T-07/T-15 | corregido | test A1; A2/B2 verifican forwarding al mismo objeto |
| A1-02 | Important | Nuevas aristas ausentes | T-08/T-15 | corregido | CONTRACTS E25–E28, A2 verifica formato/puertas |
| B1 | Important | Listas opcionales abortan recuperación | T-07/T-14 | corregido | tests B1; 21 escenarios B2, 19 tests dirigidos A2/B2 |
| B2 | Important | Imports parciales abortan CLI | T-07/T-14 | corregido | tests B2 y fixtures independientes ausente/roto |

Fusión: cero Critical/Important/Minor pendientes. C2 ejecuta 30 passed/25
deselected en HOME propio; no confunde esa selección con la QA completa.
No se promueve memoria ni se cierra ningún T global de esta iniciativa.

### QA final del Bloque 8

[Evidencia de recuperación](memory-approved-retrieval-evidence.json): Windows
**430 passed/1 skipped**, 431 casos parametrizados y 377 identidades padre;
Linux **405 passed/20 skipped**, 425 parametrizados y 384 identidades padre;
paquete portable **15 passed**, cero skips. Cada cohorte tiene qa-gate VERDE,
cero fallos/errores/flaky. Son suites dirigidas que se solapan entre plataformas;
no se suman como tests únicos ni se presentan como toda la CI.

Windows: Python 3.13.0/pytest 9.1.1/coverage 7.16.2, 220,73 s. Su único skip es
`test_gap6_symlink_fuera_de_la_carpeta_aprobada_falla`, por permisos de symlink;
las junctions propias y los symlinks Linux sí pasan. Los skips Linux requieren
memoria real deliberadamente ausente: no acreditan validación de ese corpus.
Linux: Python 3.11.16/pytest 9.1.1, 29,30 s, imagen propia fijada y red `none`.
Ambas copias contienen exactamente las mismas 477 fuentes del manifiesto final;
los ocho archivos implementados coinciden con sus fuentes actuales. Homes, TMP,
Git y datos de memoria son propios; no settings o servicios del consumidor.

Cobertura oficial del diff: **473/524 líneas ejecutables añadidas = 90,27 %**,
supera el gate global ≥90 %. Las métricas por módulo se conservan sin inflarlas:
los tests de wrappers parciales ejecutan copias byte idénticas fuera del filtro
de fuente canónica, por lo que sus ramas no se atribuyen a esos módulos. No se
afirma ≥90 % por archivo. Los rojos y resultados rechazados anteriores siguen
identificados con hashes; los nuevos artefactos no los sobrescriben.

Comprobaciones de entrega: lint workspace cero errores/tres avisos históricos,
evals 51 piezas/182 casos y cero errores, interop 56 archivos al día, ledger cero
incoherencias/avisos. Portable: 189 archivos/check 0 y ambos helpers byte idénticos.
La copia de entrega tiene un cuarto aviso de modo ejecutable de hooks.json
por metadatos de su Git vacío/NTFS; se conserva el log. El Git real declara su
modo correcto y el lint real da los tres avisos anteriores, sin cambiar modos.
Scan inicial de 874 fuentes públicas propias: cero referencias/nombres vetados;
settings y memoria local se excluyen antes de leer. Evidencia final añadida
después de esa copia; su scan y revisión de consistencia quedan para la entrega.

Aceptación acotada: recuperación aprobada corregida, distribución validada,
documentación y comparación/diagnóstico con límites explícitos. El fallo de
guardia bajo carga, la eficacia nativa de memoria, benchmark Graphiti, propuesta
de retoma y comparación general siguen abiertos. Nuevas skills aplazadas.
Publicación pendiente al escribir este bloque; no se inicia otra fase.

Jira del intento 2: `--event revision --actor reviewer --task T-07,T-08,T-14,T-15
--intento 2 --batch --json`, exit 0; desactivado, `ops: []`. Nada publicado.

### Consistencia y puertas antes de publicar

Dos controles independientes frescos de la evidencia final verifican hashes,
477 fuentes, mapas Windows/Linux, ocho fuentes actuales, XML/padres/skips,
gates derivados de resultados reales y portable. Recalculan cobertura desde
diff y JSON oficial: 473/524, 90,27 %, sin discrepancias ni gaps nuevos.
No repiten suites ni ejecutan builders que reescriban evidencia.

Scan final de 875 archivos públicos propios: cero referencias/nombres vetados;
settings ajeno y memoria local excluidos antes de cualquier lectura. Los ocho
hashes implementados siguen iguales al snapshot validado. Git declara
hooks.json `100644`. Scope final: 26 archivos propios en alcance, settings
excluido, cero fuera/avisos. Selector solo con ocho paths propios: C true por
SQL de columnas constantes, D false, cero avisos. Ledger y diff --check: exit 0.
La rama remota sigue en la base `b8e6192` antes de publicar; no hay cambios
ajenos staged. Tras entregar los commits y verificar el remoto, se detiene
este bloque conforme a la instrucción del usuario. El objetivo global no se
declara completado y esta entrega no inicia otra fase.

El check del índice al añadir helpers nuevos detecta dos líneas vacías al EOF,
sin espacios finales ni defecto funcional. Se conserva ese diagnóstico y se
comprueba con `git -c core.whitespace=-blank-at-eof diff --cached --check`:
exit 0. La excepción es solo para esa preferencia de estilo y solo por llamada;
no cambia configuración, fuentes validadas, gates del plugin ni sus hashes.

### Publicación verificada del Bloque 8

Commit de implementación/documentación/evidencia:
`e6fc5ff2a37a854ee0a2ccfcd5c7cb56abeb7640`, 26 archivos propios.
Push a `feat/catalog-capabilities` exit 0; `git ls-remote --heads origin`
confirma exactamente ese SHA. Solo queda sin seguimiento el settings ajeno;
no se modifica ni añade. Memoria local, fuentes de investigación, fixtures y
artefactos privados permanecen fuera de Git.

Este registro de entrega se incorpora en un segundo commit documental.
Al verificar su push, se detiene el trabajo a petición del usuario. No se
declara completa la iniciativa: quedan los pendientes y límites registrados
arriba, sin comenzar otra fase ni añadir skills nuevas.

## Bloque 9 — Entrega de guardia y diagnóstico acotado (2026-10-09)

El usuario reanudó el trabajo pendiente. Base `f3e594a`; T-02/T-09/T-14/T-15
siguen abiertas y nuevas skills aplazadas. El diseño de este bloque separa
entrega explícita de decisiones y eficacia bajo carga.

**RED real antes del código:**
`node --test --test-name-pattern='spawn failure|empty successful evaluator|evaluated denial' tests/hook-guard-delivery.test.mjs`
terminó con 8 failed/1 passed. Python ausente/spawn fallido y respuesta vacía
produjeron `Unexpected end of JSON input` en los tres runtimes; Claude/Codex
no convirtieron el resultado estructurado al deny nativo esperado. Los fixtures
solo contienen payloads propios. Primer verde de desarrollo: 39/39 casos de
entrega; ampliación de casos adversos y QA final en progreso.

El launcher pide `--output structured`, acota stdout a 16 KiB, valida un único
objeto y entrega como máximo una respuesta. Una decisión de bloqueo completa
se conserva incluso ante timeout o salida fallida posterior; una continuación
necesita terminar normalmente. Supervisión inválida invalida ambas. Errores,
ausencia o resultado incompleto degradan con aviso estable, sin revelar payload
ni diagnóstico libre del proceso y sin conceder permisos adicionales.

Scope-check inicial base f3e594a: 8 archivos propios en alcance, cero fuera/cero avisos;
settings ajenos excluidos por defecto. Selector con `--files` explícitos: A+B,
C/D false, cero avisos; no inspecciona settings ajenos. Exportador comprobado:
56 archivos al día. Tier reviewer frontmatter opus/high; el runtime ofrece
subagentes genéricos como fallback de revisión, sin override de modelo.

Comparación privada acotada: cuatro pares, dos de arranque Python y dos del
launcher real instrumentado. Venv 116,8/102,8 ms frente a base 83,1/66,2 ms;
launcher venv 854,2/819,6 frente a base 740,8/708,9 ms. Los cuatro guards
produjeron deny/exit 0. El snapshot de ascendencia sólo ocurrió en venv y
tardó aproximadamente 10–11 ms. No hubo carga impuesta ni despacho nativo
Codex, y no se reprodujo el fallo de 4.500 ms: no justifica cambiar intérprete
o presupuesto. `analysis-v2.json` sustituye un campo derivado incorrecto del
análisis inicial; se conservan ambos y no se usa el inicial como evidencia.

## Revisión de dos lentes — intento 1: bloque 9

A+B en paralelo, contexto fresco; C/D no activadas por selector explícito.
A: nueve criterios conformes, export --check exit 0/56 archivos al día.
B encontró un Important reproducible; no otros defectos.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | Razón deny válida con caracteres suplementarios rechazada por límite UTF-16 | T-09 | Contar puntos de código como el evaluador Python; pendiente segunda revisión | RED: 3 failed/0 passed en `supplementary Unicode` antes del fix; evaluador real del revisor deny con 1.189 puntos/2.189 unidades |

Jira deshabilitado: no se publican operaciones externas. Desarrollo ampliado
antes de este fix: 72 passed (69 nuevos + 3 adaptador), cero fallos, 115,86 s.
Estos resultados no constituyen QA de la corrección Unicode.

## Revisión de dos lentes — intento 2: bloque 9

A+B frescas revalidaron el delta Unicode y conservaron los criterios aprobados:
cero Critical/Important/Minor. Ambas ejecutaron independientemente seis casos
de frontera Unicode, todos verdes; A comprobó export --check exit 0/56 archivos.
El Important del intento 1 queda corregido. Jira `revision`, intento 2: exit 0,
`jira: desactivado`, `ops: []`. No se cierra ninguna tarea global.

### QA final del bloque 9

Fuentes congeladas: 876 archivos, manifest
`614ea558238b5131fe1f0f055b4786ccad124e9822d58363fcf3f8e780b614bf`.
Launcher `0b6b2f8a16721ef742e2c4bf3d6bb4bef9e4868e1e38f9f8b420c98b85bd0077`;
test de entrega `3454698bc9a0ea5051327362af94f80e775cc1f0e2f6ea6d454c28d8baffd49c`.
El gate de alcance antes de QA comprendía diez archivos propios, cero fuera,
sin avisos y settings ajenos excluidos. Evidencia y prioridades amplían sólo docs.

| Plataforma | Runner | Resultado final |
|---|---|---|
| Windows, Node 23.8.0 / Python 3.13 | Node, cuatro suites | 115 passed, cero fallos/skips |
| Windows | pytest, cinco suites | 276 passed, cero fallos/skips |
| Linux, imagen propia Python 3.11.16 / Node 22.23.3 | Node, cuatro suites | 103 passed, 12 skips de casos exclusivos de Windows |
| Linux | pytest, cinco suites | 276 passed, cero fallos/skips |

JUnit real convertido al formato del qa-gate: VERDE en las cuatro cohortes.
Las identidades de casos no se suman entre plataformas como casos únicos.
Cobertura V8: 51/55 líneas añadidas significativas, 92,73 %. Proyección de
rangos oficiales al primer offset UTF-16 de cada línea, no cobertura de
sentencias/ramas Istanbul; denominador/método/líneas descubiertas preservados.
No se repite para inflar el resultado tras superar el gate del diff ≥90 %.

La primera tanda Linux no ejecutó tests por el entrypoint heredado del helper.
La segunda conservó 92 passed/11 failed/12 skipped con checkout shell Windows;
la tercera, con LF canónico, 102 passed/1 failed/12 skipped. El único fallo
restante estaba en el oráculo de existencia de PID de limpieza, línea 271,
sin init en el contenedor. La cuarta usó init y pasó ambos runners, pero falló
la copia de symlinks de fixtures a Windows. La quinta conserva los informes
JUnit finales, exportando sólo artefactos necesarios. Todas permanecen privadas.
Los ocho shell normalizados coinciden exactamente con los blobs Git de la base
y con `.gitattributes`; los demás bytes, incluido launcher, coinciden con
Windows. Linux usa red none, HOME/Git propios y verifica los 876 hashes antes
de ejecutar. No se oculta un fallo del runner como test omitido.

Lint del snapshot: cero errores/cuatro avisos (tres nombres históricos y uno
por Git vacío/mode NTFS del JSON). Lint del árbol real: cero errores/tres avisos
históricos. Evals: 51 piezas, 182 casos, cero errores. Interop: 56 al día;
ledger-lint: cero incoherencias/cero avisos.

Prueba nativa Codex 0.161.0: una cohorte raíz propia con los seis eventos,
proveedor loopback sin Authorization y un guard privado retrasado ocho segundos.
PreToolUse plugin completed, 5.719 ms; entrada `warning` con el aviso exacto
del launcher; parche permitido bajo permisos normales. 328 archivos de
distribución/cache verificados, una sustitución explícita del negocio y ningún
instrumento en producción. Salida natural 0, sin cleanup forzado. Esta prueba
acredita entregar el aviso, no eficacia del evaluador/hijos ni cierre bajo carga.

Evidencia pública: [guard-delivery-evidence.json](guard-delivery-evidence.json)
y [guard-warning-native-evidence.json](guard-warning-native-evidence.json).
El gotcha Unicode GOT-018 y su fila del índice nacieron localmente como
propuesta. Dos auditorías independientes finales validaron los cuatro campos,
fuentes, RED/GREEN, casos finales y correspondencia del índice, sin hallazgos;
se acepta sólo esta entrada propia con la traza de revisión del intento 2.
`docs/knowledge/` sigue fuera de Git por la política del repositorio.
No se promociona memoria anterior ni se publica a un backend.

Auditorías documentales A/B finales: cero discrepancias. Verificados los cuatro
JUnit/gates, manifests, ocho excepciones LF, 146 muestras V8, denominador y
hashes públicos/privados de la prueba nativa y comparación de arranque. No
ejecutaron suites ni leyeron payloads/protocolos crudos, settings o memoria ajena.
Scan final: 878 archivos públicos, cero referencias/nombres prohibidos; fuentes
de launcher/test siguen idénticas al snapshot. Scope final: trece archivos
propios, cero fuera/cero avisos, settings excluidos antes de leer. Diff limpio.

Publicación: los dos JSON públicos se escriben con LF para que sus hashes
coincidan con los blobs Git. La proyección nativa privada conserva CRLF y
hash propio; su copia pública sólo normaliza finales de línea, con datos JSON
idénticos. La evidencia separa ambos hashes y no afirma igualdad de bytes.

### Checkpoint de entrega del bloque 9

Commit funcional/documental `e488f23f03eef1f3fc84bc0e5183a279310f4863`:
trece archivos, decisiones explícitas, 75 casos nuevos, evidencia de QA y
aviso nativo. Los JSON publicados conservan LF y sus hashes coinciden con
Git; código/tests siguen idénticos a las fuentes verificadas. Este segundo
commit registra el checkpoint antes de publicar ambos en la rama autorizada.
No PR, merge, release ni modificación de settings del consumidor.

Pendiente de la iniciativa: fiabilidad del arranque de guardia y cierre bajo
carga nativa, retoma de comandos, controles de panel y medición de memoria
opcional. Las nuevas skills permanecen aplazadas. El bloque de entrega de
decisiones queda validado; la iniciativa y T-02/T-09/T-14/T-15 siguen abiertas.

## Bloque 10 — Aislamiento causal de latencia de hooks (2026-10-09)

El usuario autoriza el punto 1: hooks bajo carga. Base `e7160f4`, alcance inicial
de investigación: fixtures privadas y este diseño/ledger. Nuevas skills y otras
fases aplazadas. No se tocan settings del consumidor, instalaciones reales,
credenciales ni memoria anterior. Durante el diagnóstico inicial, producción
conserva sus bytes y presupuestos; las correcciones posteriores se detallan abajo.

Dos comprobaciones independientes en paralelo: réplica nativa Codex completa y
auditoría de fuentes del launcher/supervisor/captura y contrato nativo pinned.
Las trazas se separan por proceso y módulo para eliminar corrupción por escrituras
concurrentes; el coste de escribir la propia traza permanece como hipótesis.
Límite de contraste inicial: dos cohortes, con los datos de la primera antes
de elegir la segunda. Los resultados y los errores del reducer se conservan;
una proyección corregida recibe versión nueva, sin sustituir la original.

La aceptación exige efecto de guardia por rol, control permitido y envelope
correcto antes de salida natural. `completed` no basta para acreditar captura;
la duración nativa y su timeout tienen instantes iniciales diferentes.
No se cierra T-02/T-09/T-14/T-15 ni la iniciativa por este diagnóstico.

**RED: antes de modificar el lector de rama**, `pytest` sobre
`test_guardrail_check.py` y `test_native_guardrail.py` con `-k unborn`:
8 failed, 254 deselected, 7,57 s, 2026-10-09. En main y feature sin commits,
`current_branch` devolvió None y los tres evaluadores entregaron
`branch-unavailable`. Esto omite protección de main aunque el HEAD simbólico
sea válido. Scope añadido: `agent-kits/shared/guardrail-check.py` y los dos
tests citados; consulta alternativa dentro del mismo presupuesto, sin cambiar
timeouts ni selección de Python.

GREEN de desarrollo del detector: 12 passed, 253 deselected, 8,58 s. Incluye
los ocho casos RED, timeout original, presupuesto restante/exhausto, HEAD
detached y ausencia de repositorio. No constituye todavía QA del bundle.

**RED antes del preflight:** `node --test tests/hook-post-preflight.test.mjs`
exit 1, 2026-10-09. Los casos de edición no aplicable fallaron al exigir stderr
vacío: el launcher intentó arrancar Python ausente y emitió `ENOENT`, por ejemplo
al editar `src/app.py` para `mark-docs-pending.sh`. Los controles aplicables y de
entrada desconocida conservaron el intento de ejecución. Scope añadido:
`hooks/run-hook.mjs`, `tests/hook-post-preflight.test.mjs`, documentación de
hooks ES/EN y changelogs; la forma exportada de registros no cambia.

Primer GREEN de desarrollo preflight: 42 passed, cero fallos, 38,35 s.
RED adicional de ruta multilínea: tres fallos reales en Claude/Codex/OpenCode,
`tasks.md\nsrc/app.py` se saltó como no aplicable pese a que el shell descompone
líneas. Esas rutas pasan a entrada desconocida y mantienen el camino anterior.

GREEN de ruta multilínea: tres passed, cero fallos, 2,47 s. Puerta previa a
revisión: scope-check base e7160f4 exit 0, once archivos propios en alcance,
cero fuera/cero avisos; settings ajenos excluidos por defecto antes de leer.
Selector con once `--files` propios explícitos: C/D false, cero avisos. Export
--check exit 0, 56 archivos al día. Registros generados sin delta: los scripts
compartidos se distribuyen directamente. T-09 declara `interop/**`.

## Revisión de dos lentes — intento 1: bloque 10

A+B en paralelo, contexto fresco, subagentes genéricos por disponibilidad del
runtime; reviewer frontmatter opus/high, sin override. A aprobó los ocho criterios
de conformidad y ejecutó export --check exit 0/56 archivos. C/D no activadas por
selector explícito. B encontró un Important reproducible, ningún otro defecto.
QA/cobertura/aceptación nativa del nuevo diff siguen pendientes.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B-1 | Important | Regex JS omite ledger/progreso en carpeta con U+2028/U+2029 que acepta el glob shell | T-09 | Corregido por comparación literal; pendiente segunda revisión | Reproducción B y RED seis failed/cero passed; mismos seis GREEN en los tres runtimes |

Jira gaps intento 1: exit 0, desactivado, `ops: []`. RED dedicado B-1:
`node --test --test-name-pattern='[\u2028\u2029]' tests/hook-post-preflight.test.mjs`
seis failed/cero passed, antes de cambiar producción. Una selección previa con
`.*` seleccionó otros nueve casos ASCII/multilínea verdes, sin seleccionar los
Unicode: no se usa como evidencia del gap. La fixture del test ahora deja PATH
propio sin Bash además de Python ausente para que el oráculo de intento de
dependencias sea portable a Linux, sin ejecutar negocio ni modificar su contrato.

GREEN B-1: seis passed/cero fallos, 3,53 s. Se conservan presupuestos, separación
de handlers y fuente shell de negocio. La segunda revisión fresca está en curso.

## Revisión de dos lentes — intento 2: bloque 10

A+B frescas conservaron los ocho criterios aprobados y verificaron B-1 corregido;
cero Critical/Important/Minor. A ejecutó export --check exit 0/56 al día y
selección Unicode exacta seis passed/cero fallos. Una selección inicial propia
de A ejecutó el archivo completo (51/0); no se presenta como selección Unicode
ni QA. B ejecutó 51/51 y nueve controles adicionales Unicode no aplicable/CR
desconocido en los tres runtimes, todos verdes. Sin reapertura de lo aprobado.
Se permite pasar a QA del snapshot y aceptación nativa; ninguna tarea global
se cierra en este pase. Jira por intento 2 se verifica antes de QA.

Jira revisión intento 2: exit 0, desactivado, `ops: []`. Snapshot inicial QA:
879 archivos, manifest `c5991285c0ca83e4e7d22f0fda45d77e06c0efb89edc0d50899614e741917d8d`.
Node Windows terminó exit 0 en 261.407 ms. Python conservó 286 passed/1 failed:
el test nuevo de ausencia de repo encontró el Git del workspace padre al usar
basetemp dentro de él. Es un defecto de aislamiento de fixture, no una regresión
del lector. La prueba acota descubrimiento con GIT_CEILING_DIRECTORIES propio;
la primera cohorte se conserva. Producción y tests Node no cambian. Se repite
Python y se valida Linux con esa fixture, sin repetir Node Windows ya verde.

### Resultado del diagnóstico y límites

La [proyección del diagnóstico](hook-load-diagnosis-evidence.json) conserva las
dos cohortes instrumentadas y sus límites. Al mover únicamente las escrituras
de trazas/observador a TEMP propio, la guardia raíz pasó de 9.221 ms con aviso a
2.936 ms sin aviso. El evaluador había entregado stdout completo a los 381 ms
en la primera cohorte; ese instante no acredita la salida del proceso. Los
PostToolUse que alcanzaron el deadline de limpieza bajaron de 8/9 a 4/9.
Persisten latencias y confusores: una observación por variante no demuestra
una causa única ni un arreglo universal. El probe aislado de limpieza no
reprodujo la hipótesis de proceso huérfano. No se aumenta ningún timeout ni
se cambia el intérprete por estas mediciones. SessionEnd dejó envelope raíz
válido antes de salida natural en ambas cohortes instrumentadas.

SHA-256 de la proyección del diagnóstico:
`0fb7cb439efb1aaefbc33e70a3c003672c09f6095ddc8fdc9193adeec48ae491`.
Las proyecciones privadas anteriores con colisión de etiquetas/asociación de
PID quedan conservadas y rechazadas; la aceptada delimita cada ciclo de proceso.

### QA del diff final

La [evidencia de QA](hook-reliability-qa-evidence.json) identifica el snapshot
final de 879 archivos, manifest
`d928d1af878e029832ec2595f9634a2972c3b2a03c8ad4c0e488564c7d5f7490`.
Windows: Node 166 passed/cero fallos/cero skips; Python 287 passed/cero fallos.
Linux: Node 154 passed/cero fallos/12 skips exclusivos de Windows; Python
287 passed/cero fallos. Cuatro JUnit reales dan qa-gate GREEN. Los casos no
se suman entre plataformas. Node Windows se reutiliza sólo tras comprobar
identidad de todos los bytes de producción y tests Node; el único delta del
segundo snapshot es la fixture Python y este ledger. Linux usa los ocho shell
con LF canónico de Git, sin otras diferencias respecto al snapshot Windows.

Cobertura de líneas añadidas: V8 37/37 (100 %, unión de 197 muestras), una
proyección de rangos nativos que no representa statements/branches de Istanbul;
Coverage.py 7/7 statements ejecutables añadidos (100 %). Ambos gates de diff
superan 90 %. Lint/evals/export/ledger exit 0; 51 piezas/182 casos de activación,
56 archivos interop al día. El snapshot congelado añade un aviso de modo JSON
por su Git vacío/NTFS a los tres nombres genéricos previos; no se cambia chmod.

SHA-256 de la proyección de QA:
`a2c03816127d74dd1871829f6af1884cabf1fbc14b9c1bb505b3c49c6b5a31f5`.

### Aceptación nativa del bundle sin instrumentar

La [evidencia nativa](hook-native-acceptance-evidence.json) usa ese snapshot,
binarios Windows pinned y proveedor sintético loopback sin Authorization.
Ocho ejecuciones seriales finalizaron exit 0, sin limpieza forzada, cambios
de fuentes ni hooks observadores adicionales. Las versiones son Codex 0.161.0,
Claude 2.1.287 y OpenCode 2.0.12; hashes de binarios/helpers/resultados en JSON.

- Codex: una raíz con implementer y architect reales, cuerpos TOML completos
  reconocidos e identidades nativas distintas. Cinco decisiones de guardia
  coinciden con el efecto esperado (dos bloqueos, tres permitidas). SessionEnd
  nativo al archivar deja envelope schema 1, secuencia entera positiva e ID raíz
  correcto, observado antes de la salida natural del app-server.
- Claude: cinco procesos propios separados (raíz y deny/allow de cada rol),
  cuerpos exportados completos y deny nativo en los dos casos protegidos.
  Cada caso deja captura raíz válida antes de la salida natural. Esta matriz
  no demuestra ejecución simultánea de ambos roles.
- OpenCode: siete casos directos y cuatro raíces con un hijo real cada una;
  parentID/agente/outcome correctos, cuerpos completos, escrituras protegidas
  impedidas y controles permitidos. La captura se observa durante execution/idle,
  con servidor vivo: no equivale a un evento nativo SessionEnd en teardown.
  Una captura aún tenía nombre temporal al observarse; no se acredita publicación
  canónica ni replay completado de ese caso.

La ausencia de Authorization del proveedor es una comprobación medida; no se
afirma captura global de tráfico saliente. Estos casos reproducibles acreditan
el contrato ejercitado, no un soak test de TUI en producción ni una garantía
de latencia bajo cualquier carga. T-02/T-09/T-14/T-15 y la iniciativa siguen
abiertas; las siguientes fases y skills permanecen aplazadas.

### Contraste factual final y estado de entrega

Dos auditorías independientes finales verificaron hashes, JUnit, reutilización
de Node, EOL Linux, método de cobertura y límites del diagnóstico/nativos;
cero hallazgos pendientes en el diff. El contraste OpenCode de sólo lectura
añade cuatro registros nativos de guardia `executed:false`/error con alcance
correcto. Diez capturas conservan nombre canónico y una, temporal completo;
el JSON explicita la frontera de publicación/replay. SHA-256 nativo final:
`3cdab6f57c4af3458ee52a796a94128640ca46996158f715d0af39f590b41e67`.
La corrección de aislamiento de fixture y la nota GOT-019 propia también
fueron contrastadas; sólo esa nueva nota/fila local pasa a aceptada, sin
publicación de memoria ni incorporación a Git.

El lint por defecto del workspace devolvió exit 1 por un escalar YAML con
`: ` en una nota local anterior GOT-018, ignorada por Git y ajena al diff;
no se modifica esa memoria. Esto no se presenta como lint local verde.
El bundle público congelado excluye memoria local/config/fixtures antes de
leer y conserva lint exit 0. El ledger actualizado da cero incoherencias/cero
avisos y export --check conserva 56 archivos al día.

Se entrega este diff acotado de hooks con sus evidencias. Quedan abiertas
la extrapolación de carga/TUI y publicación canónica del caso temporal de
OpenCode; no se atribuye cierre completo de fiabilidad ni de T-09. Comandos,
dashboard, memoria opcional y las nuevas skills no avanzan en este bloque.

Puerta final del código público: lint del snapshot con documentación actualizada
exit 0/cero errores/cuatro avisos descritos, scope-check base e7160f4 exit 0:
catorce archivos propios en alcance, cero fuera/cero avisos; settings ajenos
excluidos antes de leer. Escaneo de 882 archivos públicos: cero referencias o
nombres prohibidos. Producción y tests conservan los hashes del QA final.
Destino autorizado: commit y push a `feat/catalog-capabilities`, sin integración
en main ni publicación de versión. La nota local GOT-019 queda fuera de Git.

## Bloque 11 — Publicación canónica de la captura (2026-10-09)

Retoma del objetivo activo tras entregar `2a010a2`; prioridad de hooks y skills
aplazadas conservadas. El caso temporal de OpenCode se investiga antes de
cambiar producción. El bundle y sus presupuestos mantienen sus bytes.

La auditoría de sólo lectura confirma: el observador privado abría también
`.tmp-*` mediante `glob('*.json')`. La matriz anterior acredita seis capturas
canónicas y una temporal completa, no siete publicaciones atómicas. El JSON
anterior conserva ese límite; sus resultados históricos no se sobrescriben.

Hipótesis competidoras: terminación del hook durante flush/fsync/close/rename;
o fallo de rename y limpieza por un lector Windows sin permiso de borrado.
El observador incorrecto podría interferir con el escritor. El temporal por
sí solo no distingue estas causas; la salida natural del servidor tampoco
acredita salida natural de todos sus hooks hijos. Un OSError de fsync aislado
no explica falta de rename, porque el escritor degrada y sigue publicando.

Dos trabajos independientes en paralelo, sólo en fixtures privadas propias:
criterio canónico estricto con RED previo, y probes atómicos de las dos
hipótesis con controles. El criterio excluye temporales antes de abrirlos,
exige `<event_id>.json`, schema/secuencia/raíz correctos y observación con
servidor vivo; contempla outbox/processing/done. Una matriz nativa corregida
se permite sólo tras preparar y auditar ese criterio. No se incrementan
timeouts, se retira fsync ni se promocionan temporales arbitrarios por su JSON.

### Resultado medido

[Evidencia de publicación canónica](hook-canonical-capture-evidence.json),
SHA-256 `effb1eac12de8b778e0cd7259e3a979e0599189b3987cfb7e7628f0ce111840b`.
Caracterización del observador anterior: 16 controles, ocho fallos y un error;
incluye aceptación indebida de temporal completo y lectura de nombre no
publicado. Observador estricto: los mismos 16 controles pasan, sin lanzar
runtime; su función coincide por AST con la embebida en el helper nuevo.

Probe de lector Windows: un handle propio sin FILE_SHARE_DELETE provoca error
32 en rename y limpieza, dejando un temporal completo. Control de fallo de
rename con limpieza disponible: ningún temporal; control de OSError en fsync:
publicación canónica y marcador degradado. Probe independiente de hard stop:
worker propio bloqueado tras flush, terminado por su handle Popen y confirmado
terminal; temporal completo sin publicación. Liberar la barrera publica.
El worker usa el intérprete base fijado para evitar matar sólo el redirector
venv; no cambia la selección de producción ni mide el launcher. El probe de
launcher queda preparado, no ejecutado. Ambos mecanismos son reproducibles;
ninguno queda demostrado como causa histórica del caso anterior.

La única cohorte nativa nueva usa OpenCode 2.0.12 y la misma fuente congelada
de 879 archivos del QA previo. Siete casos exit 0 en 135.055 ms, siete nombres
canónicos en outbox observados con servidor vivo, schema 1, secuencia entera
positiva y sesión raíz correcta. Cuerpos exportados completos y 94 hashes de
fuente actual/congelada/instalada coinciden. Deny/allow por rol, control raíz,
planner y agente homónimo del consumidor conservan sus efectos. Salida natural
del servidor, sin limpieza forzada ni Authorization del proveedor; sin hooks
observadores adicionales. No se repiten Codex/Claude ni se cambian sus evidencias.

Una copia aislada del checkpoint sintético del planner anterior permite
`journal.py recover --session-id <id propio> --budget-ms 3000 --max 1`:
exit 0, una candidata/una recuperada en 511 ms. Entrada `fuente: recover`,
`cierre: recuperado_sin_cierre`, sesión coincidente; originales y checkpoint
de copia conservan su hash. No se renombra/promociona el temporal anterior ni
se convierte recuperación en cierre observado. Se usa recuperación explícita
de una sesión conocida como terminada, sin saltar la guarda de sesiones vivas
en la recuperación implícita.

No hay fix de producción en este bloque: el defecto probado era del criterio
de aceptación privado y queda corregido en una fixture nueva, conservando la
anterior. TDD de producción y alta de memoria técnica no aplican. Cambios
públicos: evidencia, diseño y estado verificable del ledger; ninguna skill,
agente, comando, backend, instalación del usuario o configuración ajena cambia.
La iniciativa permanece abierta. Siguiente integración de hooks: preservar
verificación de commit frente a bypass, bajo `guardrails.git` e IDs protegidos.

## Revisión de dos lentes — intento 1: bloque 11

A+B frescas en paralelo, fallback a reviewer genérico por disponibilidad;
tiering del frontmatter opus/high, sin override. A verifica conformidad y
evidencia por criterio; B contrasta hashes/AST, siete capturas físicas y dos
errores nativos de guardia en SQLite propio de sólo lectura. Ambas: cero
Critical/Important/Minor. C/D no activadas por selector de tres archivos
documentales explícitos, cero avisos. Jira revisión: exit 0, desactivado,
`ops: []`; no publicación externa.

Lint del bundle público con documentación actualizada: exit 0/cero errores,
los cuatro avisos ya descritos; no se afirma lint local por defecto verde.
Ledger: cero incoherencias/cero avisos. Export --check: 56 al día. Alcance
base 2a010a2: tres archivos propios, cero fuera/cero avisos; settings ajenos
excluidos antes de leer. Escaneo de 883 archivos públicos: cero referencias
o nombres prohibidos. No se repiten suites de producción para este diff
documental: los 94 archivos nativos y la fuente del QA conservan su hash,
con excepción esperada del propio diseño/ledger que describen este bloque.
Se permite commit/push acotado a la rama autorizada; la iniciativa queda abierta.

## Bloque 12 — Preservar la verificación de commit (2026-10-09)

Base publicada y contrastada con remoto `ddb06dc`; la retoma del objetivo
autoriza continuar integración de hooks. El contraste de política previo
identifica bypass de verificación Git como siguiente destino de T-09.
Se reutilizan `guardrail-check.py`, dispatcher e IDs exactos; ninguna skill,
registro de hooks, protocolo nativo ni permiso de agentes ajenos se añade.

Regla bajo `guardrails.git`: no omitir verificación de commit con flags
efectivos `--no-verify`/`-n`, también en amend; no sustituir core.hooksPath
por argumento/configuración de entorno explícita en la invocación de commit.
La ruta alternativa no acredita que preserve los hooks del proyecto. Mensajes,
valores de opciones, pathspec tras `--`, amend normal y otras operaciones Git
no disparan esta regla. `--verify` posterior restaura verificación. El opt-out
Git y la selección de identidades actuales se conservan.

El parser existente se amplía para asignaciones literales iniciales, `env`
con asignaciones, wrappers `command`/`exec` y recursión shell `-c` ya existente.
No evalúa variables, aliases ni scripts arbitrarios, ni lee configuración
externa para inferir intención. Consumir valores de opciones evita confundir
texto con flags. La misma normalización preserva guardias existentes al usar
esos wrappers. Archivos iniciales: shared lector/tests, docs del contrato y
este diseño/ledger; el alcance de T-09 incluye shared/tests/docs.

Tests contractuales nuevos en `test_git_verification.py` preceden a producción:
roles implementer/architect en Claude Bash/PowerShell, Codex Bash y OpenCode
shell; valores/pathspec/mensajes, opt-out, identidades ajenas y push previo.

**RED antes de modificar producción:** `pytest -q --tb=no
agent-kits/shared/test_git_verification.py`, 2026-10-09:
156 failed/66 passed, 2,41 s. Los 152 casos de commit protegidos y los cuatro
wrappers de push entregan permiso; controles, opt-out e identidades ajenas
conservan permiso. La suite no ejecuta comandos Git ni lee config del consumidor;
config/roles/rama están inyectados. Documentación oficial de
[git-commit](https://git-scm.com/docs/git-commit) y
[git](https://git-scm.com/docs/git), consultada 2026-10-09, confirma opciones
de verificación, valores de mensaje y overrides globales. No constituye QA.

Contraste preparatorio con Git 2.53.0.windows.2 en repositorio sintético propio,
config global/sistema vacía y hook local marcador/rechazo: baseline ejecuta
el hook; `--no-verify` lo omite. Commits sintéticos autorizados con
`--no-verify --mess --verify`, `--trail --verify` y `--pathspec-fr --verify`
también lo omiten: ese último token era un valor, no restauración.
No se ejecutan commits de prueba en el repo de trabajo. `--no-no-verify`
y su prefijo único restauran el hook; `--no-v`/`--no-ver` son ambiguos con
`--no-verbose`. El prefijo efectivo comienza en `--no-veri`.

**RED ampliación:** 33 failed/24 passed (222 deselected), 0,67 s, antes
de implementar wrappers/entorno ampliados. **RED semántica Git real:**
12 failed/1 passed (279 deselected), 0,12 s, opciones abreviadas con valor,
ambigüedad y ceros iniciales; 11 failed/1 passed (292 deselected), 0,14 s,
wrappers y ejecutables Windows; 2 failed (304 deselected), 0,09 s,
restauración por doble negación; 4 failed/20 passed (286 deselected),
0,20 s, prefijos mínimos de reuse/pathspec; 1 failed/11 passed
(317 deselected), 0,13 s, cleanup abreviado; 2 failed/3 passed
(329 deselected), 0,10 s, contador fuera del rango válido de Git.
Cada corrección de producción sigue a su rojo. El contraste corrige
también expectativas sobre abreviaturas inválidas de la fixture inicial.

**GREEN de desarrollo:** 316 casos puros pasan (18 de transporte
deseleccionados), 3,02 s. El launcher real había pasado sus 18 casos
en los tres runtimes y ambos roles, dentro de una suite de 329 en
28,87 s, antes de añadir los cinco controles de contador. Una fixture
inicial sin Git produjo diagnósticos `branch-unavailable`: se corrige la
fixture con repo sintético unborn y entorno Git aislado, sin cambiar
la producción ni ocultar el diagnóstico. No constituye aceptación CLI
de los hosts ni cierra T-09/T-14/T-15. Faltan revisión y QA del diff final.

Puerta previa del diff base `ddb06dc`: API canónica de scope-check con
15 archivos propios explícitos, cero fuera/cero excluidos/cero avisos.
Fuente pública congelada de 884 archivos; configuración del consumidor,
knowledge ignorado y fixtures privadas excluidos antes de leer. Selector
`--root <fuente pública> --files <15 propios> --json`: C/D false,
cero avisos. Tier reviewer: opus/high del frontmatter; el tool de sesión
requiere fallback genérico, modelo heredado sin override. Dos lentes frescas
en paralelo. `scripts/export-interop.py --check`: exit 0,
`export-interop --check: 56 ficheros al día`; `ledger-lint.py`: exit 0,
cero incoherencias/cero avisos. Registro/fuentes nativas no se editan a mano.

## Revisión de dos lentes — intento 1: bloque 12 (T-09)

Lentes A+B frescas en paralelo, fallback genérico. A: todos los criterios
aplican/pasan, sin gaps; verifica por sí misma export --check (56 al día).
B: dos Important reproducidos con commits en repo sintético aislado y
hook marcador/rechazo. No quedan rebatidos ni deuda aceptada.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B12-1 | Important | Un `--verify` de otra línea restauraba el primer commit; quoted `;`/`&&` perdían su condición de texto | T-09 | Scanner literal conserva límites, comillas, comentarios y continuación escapada; nunca mezcla estado entre órdenes | RED dedicado 7 failed/7 passed, 0,11 s antes del fix; pruebas de mensaje quoted y comandos separados |
| B12-2 | Important | `env -C.`, `exec -cl`, `env -iu X` abandonaban normalización | T-09 | Consumir clusters de flags soportados y valores cortos pegados | Mismo RED dedicado; reproducción B con omisión del hook sintético |

El contraste del fix añade RED 2 failed/14 passed, 0,15 s: backslash
escapado al final y primera orden completa seguida de comilla incompleta.
Se conserva la orden completa y no se analiza el fragmento incompleto.
RED 1 failed, 0,08 s para `env -` que limpia entorno como `env -i`.
El scanner no expande comandos/variables; mantiene el alcance literal
declarado y la recursión anterior. Próximo pase: re-evaluar estos cambios,
sin reabrir aprobados salvo evidencia nueva. QA final aún pendiente.

GREEN tras el fix del intento 1: `pytest -q --tb=short -p no:cacheprovider
-k 'not real_launcher' test_git_verification.py test_guardrail_check.py
test_native_guardrail.py` (rutas completas bajo `agent-kits/shared/`):
598 passed/18 deselected en 14,87 s, 2026-10-09. Segunda fuente congelada
pública conserva los 15 propios, scope API 0/cero fuera/cero avisos;
selector C/D false/cero avisos. Jira intento 1: exit 0, desactivado,
`ops: []`, sin publicación externa. El QA final ejecutará también transporte.

## Revisión de dos lentes — intento 2: bloque 12 (T-09)

A+B frescas en paralelo, fallback genérico, modelo heredado. A: tabla de
criterios del fix completa, todos ✓; export --check independiente sobre
fuente congelada y repo vivo, exit 0/56 al día. B: sin defectos, ejecuta
333 casos puros/18 deseleccionados sobre la fuente congelada y 15 controles
independientes de tokenizer/wrappers. C/D false por selector explícito.
Resultado: cero Critical/Important/Minor; B12-1/B12-2 corregidos y revalidados.
La fuente congelada no contiene el GREEN 598 pegado después en este ledger:
A lo señala como límite de snapshot; se conserva ese orden temporal y la
salida ejecutada, sin atribuirle evidencia que no leyó. Ninguna tarea global
se cierra ni se afirma aceptación CLI nueva. Siguiente puerta: QA final.

QA final del bloque 12, 2026-10-09, fuente pública congelada de 884 archivos:

| Entorno | Python | Node | qa-gate |
|---|---|---|---|
| Windows | 638 passed, cero skips | 166 passed, cero skips | Ambas suites exit 0/VERDE |
| Linux aislado | 638 passed, cero skips | 154 passed/12 skips exclusivos de Windows | Ambas suites exit 0/VERDE |

Cero unexpected/flaky en los cuatro reportes JUnit, sin reintentos.
Los 18 casos de launcher real pasan en cada entorno con ambos roles y los
tres runtimes. Ejecutan el evaluador y transportan deny/continue; los payloads
de commit no se ejecutan. No se repite aceptación CLI de hosts ni se extrapola
la anterior a la política nueva. Linux: imagen fija, red none, init y retirada
del único contenedor propio; shell LF igual a blobs base y permisos 0755 en
el tar, el resto idéntico al snapshot Windows.

Coverage.py oficial sobre statements añadidos frente a `ddb06dc`:
166/179, **92,74 %**, supera 90 %. Lint del bundle público: cero errores,
cuatro avisos previos (tres nombres genéricos y modo ejecutable del JSON en
snapshot Windows). No se afirma lint local por defecto verde: se mantiene
el límite de memoria ignorada descrito en el bloque 10. Evals: 51 piezas,
182 casos, cero errores. Export --check: 56 al día. Jira intento 2: exit 0,
desactivado, `ops: []`, sin publicación externa.

Evidencia pública: [hook-git-verification-evidence.json](hook-git-verification-evidence.json).
Los hashes fijan el lector, tests, launcher, dispatcher, mapa de IDs y prompts
generados. La documentación de límites del scanner se completa tras el pase
sin alterar código o tests medidos. Skills nuevas permanecen pausadas;
T-09/T-14/T-15 e iniciativa conservan sus estados abiertos.

Comprobación final de documentación pública actualizada: lint/ledger/export
exit 0; alcance 16 archivos propios, cero fuera/cero excluidos/cero avisos.
Escaneo de 885 archivos públicos: cero referencias y nombres prohibidos.
Código, tests y prompts generados mantienen los bytes medidos por QA.
Se autoriza la entrega acotada por commit/push a `feat/catalog-capabilities`;
no se publica release ni se integra la rama principal en este bloque.

## Bloque 13 — Retoma dirigida (2026-10-09)

Base publicada `03e520b`, remoto comprobado en el bloque anterior. Se retoma
la secuencia de comandos sobre la comparación semántica C079/C085/C087 y
sus recursos ya fijados. Las nuevas skills siguen aplazadas. Diseño y alcance
en el bloque 13 de design.md; T-08/T-11/T-14/T-15 permanecen abiertos.

Auditoría propia en paralelo, sólo fuentes públicas: journal parse/entradas/latest
no filtran ni acotan la lectura y confunden fallos con ausencia; el encabezado
de latest no sanea todos los escalares. Progress tiene dueño de cálculo vigente,
pero su modo session consulta usage-state mediante subprocess y no sirve como
compositor puramente de lectura. Runtime no figura en las entradas escritas,
y write usa solo session_id; el nuevo filtro no debe inventar procedencia ni
afirmar separación de captura. No se leyeron diarios/config del consumidor,
no se ejecutó código de origen ni se conectaron servicios.

Primero se prueba e implementa lectura local acotada común; después selección
y composición por sus dueños, fachada y consumidores/export. Sin fixtures
de selección ni QA todavía, no se declara integración ni cierre del bloque.

TDD del bloque 13, fuentes propias y fixtures sintéticas, 2026-10-09:

| Puerta | RED anterior a implementación | GREEN dirigido |
|---|---|---|
| Lector regular UTF-8 | 31 errores: módulo todavía ausente | 28 passed/3 skips Windows |
| Listado acotado y errores opacos | 25 failed/28 passed/6 skips | 53 passed/6 skips |
| Cambios observables durante lectura/listado | 2 failed/53 passed/6 skips | 55 passed/6 skips |
| Selección exacta de journal | 29 failed: API ausente | 29 passed |
| Presupuesto UTF-8 de salida | 1 failed/38 passed: 53.245 bytes frente a 12.000 | Proyección acotada por bytes escapados |
| Identidad transformada frente a detalle truncado | 2 failed/39 passed: metadato ausente | Identidad resoluble declarada por proyección |
| Compositor del ledger | 24 failed: API/CLI ausentes | 24 passed |
| Filtros/candidatos/formato de identidad | 4 failed/24 passed | 28 passed |
| CLI de historial, identidad y lectura real | 7 failed/34 passed | 41 passed |
| Sesión/entrada explícita ausente con ledger | 1 failed/41 passed | 42 passed |
| UTF-8 escapado inválido e instalación parcial | 2 failed/84 passed | 86 passed |
| Inyección automática por iniciativa | 2 failed/62 deselected | 4 passed/60 deselected incluyendo dos regresiones existentes |

Los seis skips del lector en Windows corresponden a creación de symlinks
nativos sin privilegio; los tags reparse y cloud se prueban con doubles.
La QA Linux comprobará esos enlaces nativos. Las dos pruebas existentes de
materialización incorporan una decisión sintética: un placeholder generado
sin contenido ya no cuenta como historial sustantivo implícito.

Verificación dirigida conjunta antes de revisión: 167 passed/6 skips
(lector, selector, compositor y progreso existente, 6,30 s). El pase posterior
del selector/compositor, con los dos controles nuevos de Unicode/bundle,
da 86 passed (2,17 s). Export --check: exit 0, 58 al día. Evals estáticos:
52 piezas/186 casos/cero errores. No se acredita aceptación CLI nativa ni
QA final del bloque mediante estos resultados parciales.

## Revisión de dos lentes — intento 1: bloque 13 (T-11/T-14/T-15)

Lentes frescas A+B+C en paralelo; D entra al quedar libre un slot (límite
de tres revisores simultáneos). Fallback genérico, modelo heredado; tier
de reviewer opus/high informativo. Scope API: 30 propios/cero fuera/cero
avisos, sin config del consumidor. Selector explícito activa C/D; su modo
`--files` también cita patrones previos fuera del diff, que no se atribuyen
al cambio. C no encuentra vulnerabilidades introducidas. A/B/D encuentran:

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A13-1 | Important | Dos exports omiten la última instrucción de selección sin filtros | T-15 | Regenerar desde comando definitivo | --check RED exit 1, dos DESINCRONIZADO; tras export GREEN 58 al día |
| A13-2 | Important | Segunda proyección pierde flags de recorte UTF-8/identidad | T-11 | Comparar valor proyectado y recalcular metadatos de cada historia | RED de proyección: 80 caracteres → 53 sin aviso; ID 150 →120 conservando identidad resoluble |
| B13-1/D13-1 | Important | Lecturas UTF-8 inválidas descuentan cero del presupuesto | T-11 | Contabilizar bytes también en fallo y reservar lectura fallida | D confirma 128×256 KiB =32 MiB por corpus frente a 1 MiB; no afirma 64 MiB en un único resume |
| B13-2 | Important | Nulos, números y sintaxis YAML ajena se aceptan como IDs | T-11 | Validar escalares del subconjunto antes de parse_entry | Reproducciones null/true/123/nested: value/\|; tests de tipo/sintaxis |
| A13-3 | Minor | README badges 15 pero párrafo anuncia 14 | T-15 | Corregir cantidades en ambos idiomas | Lectura factual A y recuento commands/ |

Todos los gaps se confirman contra código y fixtures propias; no hay rebates
ni deuda aceptada. RED conjunto antes del fix: 13 failed/141 passed/6 skips
(2,95 s). El primer GREEN detecta un fixture previo cuyo `bytes: 0` ya no
describe lectura descartada; se actualiza a los cinco bytes observados,
conservando `changed_path` y ausencia de texto. El lector reserva además la
asignación si read falla a mitad: nunca devuelve un consumo cero ficticio.
Las docs explican el byte adicional de detección de crecimiento.

Siguiente pase limitado al fix, sin reabrir aprobados salvo evidencia nueva.
La QA y publicación siguen pendientes; estados globales intactos.

GREEN tras el fix del intento 1: lector/selector/compositor/progreso existente,
183 passed/6 skips en 6,86 s. Export --check: exit 0, 58 al día. README anuncia
15 comandos tanto en badge como en párrafo, en ambos idiomas. Jira plan por
intento 1: primer uso sin --batch rechazado con exit 2; uso corregido con
--batch, exit 0/ops vacío sobre fixture propia desactivada, configuración y
estado explícitos aislados. No se consulta el Jira del consumidor ni se
publica externamente. La fuente del segundo pase se congela con esta traza.

## Revisión de dos lentes — intento 2: bloque 13 (T-11/T-14/T-15)

A+B+C frescas en paralelo, D al liberar slot, fallback genérico heredado.
A revalida export58 y flags de proyección. C: sin hallazgos, 39 passed/122
deselected de controles de corrección. D reproduce ambos corpus con lectura
real: 128 archivos UTF-8 inválidos de 256 KiB producen cuatro lecturas y
1.048.576 bytes descontados/leídos; ya no 32 MiB. Una excepción parcial
reserva la asignación y el cambio posterior también descuenta bytes.
B: 155 passed/6 skips, conserva un residual de la misma familia B13-2:

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B13-2 residual | Important | Comentario o indicadores YAML aceptados como ID | T-11 | Restringir texto plano heredado y rechazar tipos numéricos alternativos | RED 12 failed/56 passed (2,90 s), # comment/- item/? key y variantes de tipos; texto simple UUID/Unicode conservado |
| A13-3 residual | Minor | Cuatro recuentos del README aún dicen 14 | T-15 | Corregir tablas/resúmenes en ambos idiomas | README:109/209 de ambos; catálogo conserva las 15 filas |

No se reabren aprobados sin evidencia nueva: ambos residuales pertenecen a
correcciones incompletas del intento 1. Las docs fijan el subconjunto de
frontmatter admitido, sin anunciar un parser YAML general. GREEN del selector
tras el fix residual: 68 passed (1,81 s). Tercer pase acotado a estos fixes;
la QA sigue pendiente y la iniciativa abierta.

Jira plan del intento 2: exit 0/ops vacío con --batch, sobre configuración
y estado sintéticos explícitos; sin lectura del consumidor ni publicación.

## Revisión de dos lentes — intento 3: bloque 13 (T-11/T-14/T-15)

A+B+C en paralelo y D después por capacidad, todas frescas, fallback genérico
heredado. A: criterios del residual ✓, 68 passed independientes y export
--check exit 0/58 al día; cantidades 15 coherentes en los dos README.
B: sin defectos, 68 pruebas y ocho controles adicionales render→parse
con identidad, Unicode, comillas, saltos de línea y puntuación canónica.
C: sin hallazgos introducidos. D: sin hallazgos; escalares hasta 256 KiB,
128 nombres y tipos numéricos hostiles conservan el presupuesto de 1 MiB,
cuatro lecturas reales y estado incomplete. No infiere latencia sin medirla.

Los cuatro Important y el Minor del intento 1 quedan corregidos/revalidados,
incluidos los residuales del intento 2; cero gaps pendientes, ningún rebate
ni deuda. Se conserva cada alcance de revisión: el tercero solo reevalúa los
fixes y no reabre aprobados sin evidencia nueva. La QA corre después de esta
puerta sobre una copia pública, con código/tests/generados idénticos a la
fuente del intento 3. T-08/T-11/T-14/T-15 y objetivo global siguen abiertos.

Jira intento 3: exit 0/ops vacío con fixture sintética desactivada explícita;
sin configurar servicios ni publicar. La QA inicial Linux no se acepta:
34 failed/594 passed/8 skips en 53,94 s. Treinta y dos fallos de consola
proceden de un índice Git vacío en el harness; la suite descubre fuentes
por `git ls-files`. Dos fallos reales de distribución detectan /work-resume
ausente en descripciones canónicas. Se registra en plugin/marketplace y se
regeneran los manifiestos derivados: solo cambia la descripción, no permisos,
versión, rutas, hooks ni dependencias. Test_manifests dirigido: 4 passed.

El harness corregido crea un Git propio e indexa exclusivamente el snapshot
público en ambos entornos; no usa el índice del workspace como inventario.
Se conservan las ejecuciones rechazadas y se repiten las suites completas.
Las fuentes de comportamiento mantienen los hashes revisados del intento 3.
La doc de convenciones retira cantidades volátiles del exportador y conserva
el contrato de las seis raíces, en ambos idiomas.

QA Windows inicial rechazada: 36 failed/576 passed/24 skips; comparte los
32 fallos de inventario y dos de manifiestos de Linux. Los otros dos son del
harness: índice sin modos ejecutables y fixture sin Git que asciende al Git
del workspace (solo metadatos, sin leer configuración del consumidor). La
segunda ejecución Windows se interrumpe al detectar ese aislamiento pendiente.
El harness fija GIT_CEILING_DIRECTORIES y verifica que una fixture sin Git no
puede ascender, mientras el Git propio del snapshot sí ofrece su inventario.

Segundo Linux rechazado: 16 failed/1031 passed. Con el inventario completo
aparecen modos de consola ausentes para dos módulos puros y el adaptador de
guardrail nativo, añadidos en bloques previos. Se declaran imports sin CLI
para los módulos (sin exigirles una salida inexistente) y una denegación
nativa real con emoji para el adaptador, conservando la comprobación UTF-8.
Los cuatro fallos restantes de scope-check necesitan HEAD: el harness crea
un commit sintético en su Git propio, sin hooks ni configuración personal.
Estas correcciones solo afectan pruebas y harness; el comportamiento revisado
de la retoma dirigida permanece idéntico. Se conservan todos los informes
rechazados; no se clasifican como flaky ni como aceptación nativa.

Verificación independiente acotada de QA: sin gates debilitados ni cambios de
producción. Ambos módulos puros dan exit 0/salida vacía en cp1252 y ASCII;
el adaptador nativo deniega realmente la escritura sintética, conserva UTF-8
con emoji y no modifica el proyecto. El ceiling impide la búsqueda del Git
padre. No constituye un cuarto pase formal de comportamiento.

QA final aceptada sobre snapshot público de 895 archivos:

| Entorno/suite | Passed | Skipped | Unexpected/flaky | qa-gate |
|---|---:|---:|---:|---:|
| Windows Python | 1031 | 16 | 0/0 | 0 |
| Windows Node | 37 | 0 | 0/0 | 0 |
| Linux Python | 1047 | 0 | 0/0 | 0 |
| Linux Node | 34 | 3 | 0/0 | 0 |

Los skips de plataforma constan con motivo en la evidencia; los enlaces
nativos se ejecutan en Linux. Windows Python: 336,42 s; Linux Python: 72,30 s.
Cobertura oficial Coverage.py de sentencias ejecutables añadidas frente a
03e520b, incluyendo todo el lector nuevo: 473/523 =90,44 %, supera el 90 %.
Lint/ledger/evals/export: exit 0; 52 piezas/186 casos/cero errores y 58 exports
al día. El código, tests y prompts medidos mantienen sus hashes. Git, homes
y fixtures propios, config global/system desactivada, ceiling y Linux sin red.

Evidencia pública: [work-resume-evidence.json](work-resume-evidence.json).
Escenarios del bloque en test-plan.md; docs bilingües en WORK-RESUME.md.
La entrega completa este bloque de retoma local; no acredita aceptación nueva
de hosts nativos, cierre general bajo carga ni sandbox atómico. Runtime
heredado desconocido y contrato de captura permanecen explícitos.

T-08/T-11/T-14/T-15 y la iniciativa global siguen abiertos por sus otros
criterios. Nuevas skills permanecen aplazadas en 79/293. Próximas puertas:
controles del panel y medición del backend opcional. Se prepara commit/push
de esta entrega en feat/catalog-capabilities y se detiene el trabajo del bloque.

## Bloque 14 — Diagnóstico explícito en el panel (2026-10-09)

La continuación del objetivo retoma la siguiente puerta documentada, sin
reabrir la incorporación de skills. Base publicada `2610a27`, worktree sin
cambios públicos. Auditoría independiente confirma navegación, filtros y
etapas existentes, y detecta el gap de diagnóstico fechado con alcance y
remedio. Suite panel propia: 84 passed/2 skips; no aceptación de navegador
por esa auditoría. Comparación pertinente y contrato se completan antes del
código; diseño en el bloque 14 de design.md. T-08/T-13/T-14/T-15 permanecen
abiertas. No se leen configuraciones o memoria del consumidor ni se activan
servicios para esta investigación.

Se añade .gitignore al alcance T-15 para excluir únicamente /panel.html, la
instantánea local solicitada por el usuario; la plantilla empaquetada sigue
versionada. No se cambian exclusiones del consumidor ni se omite código.

TDD bloque 14: proyección nueva RED 25 fallos por módulo ausente → GREEN 25;
control de etiquetas públicas exactas añadido → 26. Fachada --panel-json RED
1 failed/1 passed/208 deselected (opción ausente; el segundo caso ya exigía
rechazo de modos simultáneos) → GREEN dirigido 28 passed/208 deselected.
Entrada del panel RED inicial 13 failed/2 errores: los errores son IDs de
parámetros demasiado largos para fixtures Windows. Con IDs explícitos y raíces
sintéticas correctas, RED 14 failed por API/lector ausentes → GREEN 14.
Se conserva la ausencia de efectos y no se confunde este GREEN dirigido con QA.

Comparación pertinente completada por rangos: cinco recursos revalidados, sin
ejecución externa. R-949360f20153 admite avisos por observaciones omitidas sin
impedir ready; no se traslada ese agregado. Dependencias fuera del contrato
seleccionado siguen pendientes, sin cerrar evaluación global. Registro en
comparisons/panel-diagnostics.md y su evidencia de lectura. Auditoría AST propia:
49 títulos literales únicos y 42 callsites dinámicos; etiquetas exactas públicas
permitidas, datos libres excluidos y referencia de remedio conservada en doctor.

GREEN dirigido de proyección/panel/regresiones actuales: 124 passed/2 skips
Windows en 12,19 s. No es QA final; faltan escenarios de límites adicionales,
revisión, exports/documentación finales y navegador Edge. La vista local pedida
por el usuario se genera sin informe, sin inspeccionar configuraciones privadas;
Diagnóstico muestra ausencia de informe y no inventa resultados.

La comprobación de distribución detecta package.json con conteos anteriores
(9 agentes/12 comandos/17 skills) y coste siempre medido. T-15 incluye ahora
package.json: su descripción pasa a capacidades estables, sin cifras o medición
no acreditadas; no cambia versión, dependencias, permisos ni ejecutables.

Regresión dirigida ampliada: 250 passed/1 skip en productor/doctor/lector,
antes de los seis controles adicionales de límites y helper ausente. Edge
H01–H09/D01–D07: RED 14/16; D07 reproduce fragmento repetido sin hashchange,
y D01 falla antes de ejecutar la página por arranque transitorio del navegador.
Se conserva ese rechazo. Corregido el click al mismo fragmento con navegación
nativa y clicks modificados intactos: GREEN 16/16, cero skips/reintentos/flaky.
Edge 154.0.4258.62 y Playwright 1.63.0, fixtures públicas y homes propias,
cero peticiones HTTP(S), hashes y capturas privados preservados. No es
aceptación de hooks nativos ni informe de diagnóstico real del consumidor.

El usuario amplía T-13 al seguimiento e interacción operativos. Comparación
en comparisons/panel-activity.md: 14 recursos con hashes/rangos revalidados,
sin ejecución externa. El panel de origen usa polling, procesos gestionados
y algunas acciones de memoria/tablero; no descubre todos los subagentes ni
expone control de pausa/arranque desde esos endpoints. T-13 pasa a en-progreso
por sus entregas parciales; no se marca completada. Servidor local,
observación por runtime y acciones canónicas quedan como siguientes bloques,
sin atribuir esas capacidades al HTML actual. Se investiga también la
aprobación visual de planes por petición posterior del usuario.

Esa comparación queda documentada en comparisons/panel-plan-review.md:
20 fuentes de comando, recurso, servidor, persistencia, consumidor y test de
integración leídas sin ejecución. La UI de origen sí tiene aprobar/pedir cambios,
comentarios y recarga; los otros comandos conversacionales no se cuentan como
otra UI. Se elige integrar experiencia sobre el servidor propio con versión
por contenido y consumo confirmado. Función propia aún pendiente; no se
añade ninguna skill ni se reclama evaluación completa de esas piezas.

Fachada portable y degradación dirigida: 3 passed/208 deselected. Exportación
actual comprobada con --check: exit 0, 58 ficheros al día. Diagramas ES/EN
actualizados para la importación explícita, sin diagnóstico automático.

## Revisión de dos lentes — intento 1: Bloque 14 (T-13/T-15) — diagnóstico y comparación operativa

Snapshot público de 36 archivos propios, base 2610a27, scope canónico 36/36
sin exclusiones. Lentes A+B+C+D por revisores genéricos de contexto fresco;
reviewer por nombre no disponible. Tier del bundle opus/high informativo,
sin override por invocación. Selector canónico sobre lista propia: C siempre
con fixture suministrada por privacidad de export; D auto por rutas y
concatenaciones. No se lee dev.json real. B/C sin defectos/hallazgos; D valida
carga máxima de 512 filas y ocho bloques sin degradación material. A confirma
alcance, pruebas y verificación parcial, pero requiere dos correcciones.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A1 | Important | La nueva exportación doctor omite redactor canónico | T-13 | Corregido; pendiente revalidación | Test dedicado RED 1 failed/211 deselected → GREEN 4 passed/208 deselected; redactor ausente añade rechazo opaco |
| A2 | Important | Nuevas aristas sin matriz de contratos | T-15 | Corregido; pendiente revalidación | E29–E32 añadidas con gates ejecutables; TDD n/a: tabla documental; no existe espejo EN de esa matriz |
| A3 | Minor | Hint del índice pierde flag y opcionalidad | T-15 | Corregido; pendiente revalidación | Test dedicado RED 1 failed/19 deselected → GREEN 1 passed/19 deselected; exports regenerados, 58 escritos |

Export --check independiente A: exit 0, 58 al día, antes del ajuste de hint.
Jira-flow gaps invocado sobre fixture propia explícitamente desactivada:
exit 0, ops vacío; nada publicado, sin consultar config ni cuenta reales.
Todos los rechazos y reportes de lentes se conservan privados. El diff corregido
se revisa como intento 2/3; la QA final sigue pendiente, no se declara cierre.

## Revisión de dos lentes — intento 2: Bloque 14 (T-13/T-15) — revalidación de correcciones

Snapshot público de 37 archivos propios, scope 37/37 sin exclusiones. Cuatro
lentes nuevas, fallback genérico y tier informativo, con tabla previa completa;
se reevalúan diez archivos corregidos y no se reabren aprobados sin evidencia.
A aprueba A1/A2/A3, B/C/D sin defectos/hallazgos. Export --check independiente
exit 0, 58 al día; cinco tests dirigidos y límite máximo de proyección comprobados.
Redacción del JSON máximo añade unos 8,6 ms por export CLI en probe aislado;
no es medida de latencia nativa ni medición de tokens. Sin gaps pendientes.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A1 | Important | Exportación sin redactor | T-13 | Corregido y aceptado | Invocación de redact.py y tests dedicados de uso/ausencia; JSON límite válido |
| A2 | Important | Aristas sin matriz | T-15 | Corregido y aceptado | E29–E32 con entradas, salidas, límites y gates ejecutables |
| A3 | Minor | Hint pierde flag y opcionalidad | T-15 | Corregido y aceptado | Test dedicado y export --check independiente, 58 al día |

Se corrige únicamente una línea vacía final en el documento EN antes de la
QA. Código, tests y generados aceptados se mantienen. Se prepara snapshot
final de QA, homes propios, Git sintético y contenedor Linux sin red; no se
declara QA verde antes de ejecutarla ni aceptación nativa de hooks por esta UI.

La primera QA Windows conserva 998 passed/9 skips/2 failures. Dos tests del
diagnóstico general pierden taxonomy.json/training.json por truncamiento de
ruta a 200 caracteres con basetemp largo. Comparación causal de cuatro cohortes:
base publicada y código actual fallan ambos con rutas largas y pasan ambos
con tempfile propio corto. AST de los tres métodos pertinentes coincide;
campo id_prefix se conserva. No es regresión de la proyección portable.
Se ajusta únicamente basetemp del harness Windows a una carpeta nueva propia
y se repite la misma suite completa, sin retirar casos. La limitación previa
del detalle general queda pendiente para el bloque de comandos; los rechazos
no se suman a QA verde ni se etiquetan flaky. Linux: 1007 passed/2 skips y
export --check 0; código/tests/generados idénticos al futuro rerun Windows.

### Entrega parcial del bloque 14 — QA aceptada

[Evidencia ejecutada](panel-diagnostics-evidence.json): Windows 1000 passed/
9 skips y Linux 1007 passed/2 skips; ambas puertas qa-gate exit 0, sin fallos
ni flaky. Windows conserva la misma selección de 1009 casos con basetemp
propio corto. Las cuatro cohortes causales y el primer rechazo quedan
separados de los resultados aceptados. Los hashes de código, tests y
generados coinciden entre las copias Windows/Linux; las diferencias posteriores
son trazas documentales. No se afirma que la limitación anterior esté resuelta.

Cobertura del diff oficial: 187/196 sentencias ejecutables, 95,41%, base
2610a27; gate mínimo 90%. Edge: 16/16, cero skips/reintentos/flaky; fixtures
propias y cero solicitudes HTTP(S). Lint: 10 agentes, cero errores y tres
avisos existentes de nombres; evals: 52 piezas y 186 casos, cero errores;
export --check: 58 al día; ledger: cero incoherencias/cero avisos. Los dos
pases de revisión quedan aceptados, sin gaps de este diff.

Entrega: exportación doctor --panel-json redactada e importación explícita
--diagnostics-report, diagnóstico histórico filtrable, prioridades navegables
y estados de ausencia/rechazo. El HTML no ejecuta doctor ni verifica hooks
nativos; carga/ejecución continúan desconocidas. Servidor local, observación
de agentes, acciones operativas y aprobación visual siguen pendientes.
T-08/T-11/T-13/T-14/T-15 globales permanecen abiertas; nuevas skills aplazadas.

## Bloque 15 — comandos, dashboard y contrato de consulta de memoria

Prioridad ratificada: revisión de comandos, dashboard y memoria. Diseño previo
en design.md, con responsabilidades y archivos acotados; no nuevas skills ni
ampliación de hooks. Trabajo paralelo: transporte/proyección, UI, corrección
de doctor y revisión de memoria pública, sin consultar configs o servicios reales.

RED: tests/test_panel_server.py, 34 errores por módulo serve_panel.py ausente,
antes de crearlo. Fixture propia y JUnit privado preservado. UI: 17 failed/
1 passed por render_html(live=True) ausente antes de modificar el renderer.
Estas pruebas no representan QA final ni aceptación nativa de agentes.

La revisión dirigida de memoria detecta lectura de corpus/caché al consultar,
fallback de journal que no debe presentarse como salud y ausencia de benchmark
de mejora con backend. No se ejecutan consultas, sincronizaciones o candidatas
durante polling. Consulta explícita local acotada será el siguiente contrato;
ningún servicio reemplaza la memoria canónica sin evidencia de utilidad.

Contrato dirigido de memoria en comparisons/memory-command-contract.md:
operaciones locales/externas, efectos de consulta, degradación y reconstrucción
separados. Se corrige la contradicción documental del Curator: los productores
proponen en pending; el curador decide y mueve candidatos y escribe approved.
No se añaden servicios, índices, consultas ni conexiones. T-07 sigue abierta.

Corrección de doctor: ocho regresiones RED fallan antes del cambio y GREEN
pasan; suite aislada 220 passed/1 skip, con config, homes y Git propios.
Saneador replicado idéntico, redacción antes de compactar la ruta y campo
independiente. UI: 29 tests finales GREEN en harness DOM/fetch/timers Node,
sin atribuir ese harness a Edge. Transporte: 34 RED por módulo ausente;
43 GREEN tras CLI y rechazo opaco de capacidad no ASCII. Regresión adicional
nonregular: RED 1 failed → GREEN dirigido 9 passed. Combinación actual
servidor/UI/diagnóstico/catálogo: 177 passed/2 skips. Snapshot final, revisión,
Edge y QA multiplataforma siguen pendientes antes de publicar este bloque.

## Revisión de dos lentes — intento 1: Bloque 15 (T-11/T-13/T-15) — parcialidad de la proyección

Snapshot público: 913 archivos, 30 propios, scope 30/30 sin exclusiones.
Lentes A+B+C+D de contexto fresco, fallback genérico y tier informativo;
C y D activadas mediante fixture propia explícita, sin leer dev.json real.
A y B reproducen los mismos dos gaps Important; C y D sin hallazgos.
Exports independientes de A: exit 0, 58 al día. Los hashes del snapshot
se conservan; ese snapshot anterior no incorpora las correcciones.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A1/B1 | Important | Recorte de título sin parcialidad | T-13 | Corregido; pendiente revalidación | Regresión dedicada RED antes del fix; clean añade text_budget tras redacción y antes del recorte |
| A2/B2 | Important | Estado desconocido de tarea omitido sin parcialidad | T-13 | Corregido; pendiente revalidación | Regresión dedicada RED antes del fix; parser canónico detecta unknown_task_state |

Dos regresiones nuevas: RED 2 failed/44 deselected → GREEN 2 passed/44
deselected. La revisión previa aprueba alcance, dueños, comando, transporte,
polling, docs y contratos; no concede QA final. Se revalidan las correcciones
y las nuevas evidencias documentales como intento 2/3 antes de publicar.

Jira-flow gaps por intento 1, actor reviewer, invocado sobre fixture propia
desactivada: exit 0, ops vacío. No se consultan cuentas ni configuración reales.

### Contraste de memoria y despliegue existente

El usuario confirma tres componentes distintos: Kwipu, Graphiti y Graphify;
autoriza revisar documentación del despliegue existente y pide comparar
también recuperación y aprendizaje de la referencia original. Las lecturas
previas no consultaron servicios reales; este contraste posterior realiza
únicamente inventario Docker y health/modelos acotados de loopback.

Lectura de cinco documentos de arquitectura, política, referencia y pruebas,
sin abrir env, secretos, corpus, almacenamiento, logs ni perfiles. El inventario
muestra ocho contenedores en ejecución. A 2026-10-09T13:39:21.512086+00:00,
Kwipu bridge y Graphiti health devuelven 200, y Ollama ofrece modelos cloud
y un modelo local pequeño. La documentación configura cloud por defecto;
esa configuración descrita y el inventario no prueban el modelo efectivo
de una consulta. Ninguna respuesta de recuperación o ingestión se ejecutó.

Los health no acreditan utilidad, aislamiento, durabilidad ni reconstrucción.
El benchmark posterior usará corpus sintético propio, comparará control local
con los componentes pertinentes y medirá citas, precisión, latencia, versiones
y recuperación tras fallos. No migra ni elimina datos existentes. La decisión
de conservar tres, dos, uno o ninguno requiere esa evidencia; T-07 permanece
abierta y la memoria Markdown canónica conserva su autoridad.

## Revisión de dos lentes — intento 2: Bloque 15 (T-11/T-13/T-15) — correcciones aceptadas

Snapshot de 917 archivos públicos, 34 propios, scope completo sin exclusiones.
A+B+C+D nuevas, fallback genérico y tier informativo, con tabla previa completa.
A/B aceptan ambos gaps; C/D sin hallazgos. A verifica independientemente export
--check exit 0, 58 al día, y 44 hashes de comparación de memoria. B ejecuta
dos regresiones y nueve escenarios adicionales propios, todos aprobados.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A1/B1 | Important | Recorte silencioso | T-13 | Corregido y aceptado | text_budget antes del recorte; límite, redacción y reducción de longitud comprobados |
| A2/B2 | Important | Estado desconocido silencioso | T-13 | Corregido y aceptado | Parser canónico del mismo texto; desconocido/ausente/normalizado comprobados |

D mide el coste de la segunda pasada del parser: mediana de 64 iniciativas
972 KiB pasa de 580 a 943 ms; cuatro ledgers/16.000 tareas, de 342 a 695 ms.
Máximo posterior medido 1,25 s, por debajo del plazo UI de cuatro segundos;
coste acotado y lineal, sin inferir latencia universal. Hashes intactos.

Primera QA completa: Windows 1112 passed/9 skips y Linux 1119 passed/2 skips;
qa-gate exit 0 en ambas. Cobertura del diff 212/236, 89,83%, **rechazada** por
umbral de 90%. Se añade prueba significativa del arranque/parada: carga helper
real, comunica URL al operador, captura interrupción y comprueba socket/puerto
cerrados. Prueba dirigida: 1 passed/46 deselected; no cambio de producción ni
RED inventado para comportamiento existente. Test-plan incorpora L-01–L-06.

Edge real: los seis callbacks públicos y sus assertions pasan mediante API
Playwright, sin bypass CSP/reintentos. Cuatro cohortes del runner CLI fallan
al arrancar el navegador antes de página, con cinco casos sin ejecutar cada
una; permanecen rechazadas y separadas, sin atribuir causa única a los probes.
Servidor propio cerrado. Ese resultado no acredita agentes vivos ni hooks.

Un lanzamiento posterior de QA se adelantó a terminar la copia pública y
rechazó ambas plataformas sin ejecutar tests. Se preserva como error del
harness, sin contarlo como fallo funcional. Nueva copia completada antes de
lanzar las plataformas; suite completa con prueba añadida en ejecución.
Se revisan únicamente test adicional, test-plan y trazas como intento 3/3.
Código de producción, UI, comando y exports aceptados permanecen idénticos.

Jira por intento 2: plan revision sobre fixture propia desactivada, actor
reviewer, exit 0 y ops vacío. Se comprueba con la traza del intento incluida;
no se accede a configuración ni cuentas reales.

## Revisión de dos lentes — intento 3: Bloque 15 (T-11/T-13/T-15) — verificación del ciclo de vida

Scope 35/35, snapshot de 917 archivos públicos. Cuatro lentes nuevas con
tabla previa completa, fallback genérico y tier informativo. Solo tres deltas
frente al intento 2: test añadido, test-plan y traza. Ninguna función previa
modificada; producción, assets, comando y exports conservan sus hashes.

| Criterio | Veredicto | Evidencia |
|---|---|---|
| Test adicional significativo y sin alterar pruebas previas | ✓ A/B | Helper real, servidor propio, interrupción y socket/puerto cerrados; AST previo idéntico |
| Plan y trazas conservan resultados rechazados y pendientes | ✓ A/B | L-01–L-06, cobertura 89,83% rechazada y harness sin casos diferenciados |
| Nuevos efectos/claims de seguridad | ✓ C | Sin hallazgos; no reabre aprobaciones sin evidencia nueva |
| Coste de prueba adicional | ✓ D | Un servidor/una sonda con timeout de 1 s; producción y benchmark D2 idénticos |
| Exportación independiente | ✓ A | Exit 0, 58 ficheros al día, homes/stubs/config propios |

Cero Critical/Important/Minor pendientes. Hashes antes/después 917/917 en
todas las lentes. No se afirma eficacia de memoria ni aceptación nativa.

### Entrega parcial del bloque 15 — QA aceptada

[Evidencia ejecutada](panel-live-evidence.json): Windows **1113 passed/9
skips**, Linux **1120 passed/2 skips**, cero fallos/flaky; qa-gate exit 0 en
ambas. Nueva copia terminó antes de ejecutar la suite completa; los rechazos
previos se conservan separados. Cobertura de diff oficial **225/236,
95,34%**, base ada60e2 y mínimo 90%; incluye todas las sentencias del transporte
nuevo. La cobertura Python no se atribuye al JavaScript.

Edge real: seis callbacks públicos mediante API Playwright, cero fallos,
reintentos o bypass CSP, qa-gate 0; cuatro fallos previos del runner CLI
conservados. No se declara CLI verde. Node DOM/fetch/timers queda como suite
unitaria distinta. Servidor de prueba propio cerrado, código/hash coincidentes.
Lint: diez agentes, cero errores/tres avisos existentes de nombres; evals:
52 piezas/188 casos, cero errores. Export --check: 58 al día. Ledger: cero
incoherencias/cero avisos. No se leen settings ajenos ni corpus real.

Entrega: modo --serve explícito y vista de progreso del ledger con polling,
frescura, parcialidad, filtros y fallos; corrección de errores largos doctor;
contrato de consulta y comparación de tres componentes de memoria. Son
declaraciones del ledger, no ejecución actual de agentes. La comparación
verifica 44 hashes/rangos y 26 enlaces, incluidos nueve documentos de
despliegue, sin consultas ni benchmark de backend. Health/modelos solo
acreditan disponibilidad observada y no configuración efectiva o utilidad.

Siguiente entrega: consulta local acotada y benchmark sintético para elegir
componentes; después observaciones por runtime y revisión visual de planes
consumible desde comandos. T-07/T-08/T-11/T-13/T-14/T-15 globales siguen
abiertas; nuevas skills y ampliación de hooks continúan aplazadas.

Jira por intento 3: plan revision, actor reviewer, sobre fixture propia
desactivada; exit 0 y ops vacío. Las tres trazas quedan registradas sin
publicación externa ni lectura de configuración real.

## Bloque 16 — Recuperación acotada y preparación del benchmark

Base publicada 21092c2. La entrega anterior es progreso: código, QA,
comparación y evidencia publicados; objetivo global sin completar. Se
revalida worktree: únicamente settings ajeno no seguido, sin leerlo.

Diseño previo en design.md: consulta CLI/panel sobre snapshot común, parsers
y autoridad existentes, límites acumulados y estados explícitos. Cerrar
lecturas HTTP sin tope del adaptador documental. Paralelo independiente:
lector/validación/ranking local, HTTP acotado y metadata/aislamiento del
benchmark; el servidor/UI integra el contrato común. No nuevas skills/hooks,
consulta al corpus real, credenciales, reconstrucción o migración de servicios.
T-07/T-11/T-13/T-14/T-15 globales permanecen abiertas. Las mediciones de
calidad y decisión final de componentes siguen exigidas después del lector.

### Implementación dirigida del bloque 16

El snapshot común reemplaza la lectura íntegra de la CLI ordinaria y sirve
`--view`/panel sin caché. Comparte parsers/ranking/relaciones y validación pura
de aprobados; declara corpus_read, límites y colisiones. Índice v5 reconstruye
IDs legados completos y metadata disponible. Módulos ausentes o approved
inválido conservan diagnóstico y legado, sin afirmar salud o aprobación humana.

La UI ofrece Buscar/Ver/Relaciones explícitos. El único POST aceptado es
api/memory con JSON 4 KiB, Host/Origin/capacidad y plazo de cuerpo acumulado.
No consulta memoria al cargar/pollear progreso; no invoca backends o journal.
La frescura se conserva por vista y los cuerpos solo viajan al pedir Ver.
IDs son selectores literales, incluso con caracteres usados en rutas, sin
usarlos para construir rutas o ejecutar código.

TDD y regresiones dirigidas en fixtures propias: lector **214 passed/2
skips**; bridge **96 passed/1 skip y seis subtests**; export **74 passed**;
UI RED35 y RED adicional de identidad literal, luego GREEN dirigido; transporte
RED36/3 controles, deadline RED separado y **156 passed** al integrar UI.
No son QA final ni medición de eficacia. Se conserva un fallo inicial de
invocación (ruta inexistente) y una ejecución con assets a medio editar como
errores de harness/estado incoherente, sin contarlos como verde.

HTTP del bridge acota health/error 64 KiB, snapshot 2 MiB y JSON de 64 niveles;
deadline compartido, IP privada fijada, proxies desactivados y TLS conservado.
Writer/routing y saneador replicado intactos. El cierre portable usa constantes
AST de Python, incluye helpers transitivos con ambas comillas y no los ejecuta.

La preparación del benchmark contrasta documentación/metadata existentes y
crea fuentes/preguntas propias. No hay ingesta, consultas o inferencia, ni
cambios Docker. Graphiti instalado declara otro commit y rutas de grupo con
límites estáticos; Kwipu no ofrece namespace HTTP. La selección final sigue
abierta y el experimento necesita almacenamiento/instancias propios.

Aristas E25 actualizada y E38–E42 declaradas con puertas. Diagramas, contrato,
comando, skill y docs ES/EN se actualizan en el mismo bloque. Las tareas globales
permanecen abiertas; revisión fresca, QA final y push siguen pendientes.

## Revisión de dos lentes — intento 1: Bloque 16 (T-11/T-13/T-14/T-15) — correcciones requeridas

Lentes A+B+C+D de contexto fresco por subagentes genéricos: reviewer no
callable. Tier frontmatter opus/high informativo, sin override. Snapshot
inmutable de 928 archivos públicos, 40 propios; alcance 40/40 sin exclusiones
o avisos. C/D siempre por fixture propia, sin leer dev/settings del consumidor.
Cada lente recorrió todo el diff y archivos nuevos, y confirmó 928 hashes
antes/después. Export independiente de A: exit 0, 58 ficheros al día.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A1 | Important | Helper aprobado ausente pierde legado válido | T-11/T-13 | Implementado, revisión pendiente: carga opcional tras legado, diagnóstico parcial | Fixture de helper ausente conserva ADR-001 y declara approved_helper_unavailable |
| A2 | Important | RED lector/HTTP/export no registrado en ledger | T-14/T-15 | Corregido: registrar rojos originales, sin recrearlos tras producción | Bloque RED siguiente y reportes originales conservados |
| A3 | Important | Dependencia descriptiva E25/E28 no actualizada | T-15 | Corregido: README de backends describe snapshot, corpus_read y caché parcial | skills/knowledge-services/backends/README.md, recuperación local compartida |
| B1 | Important | Sucesor prefijado se reduce y puede elegir otro ID corto | T-11/T-13 | Implementado, revisión pendiente: identidad literal íntegra y relaciones inversas | RED de namespaces, ID opaco, alias corto ajeno y selectores malformados |
| B2 | Important | TLS conserva timeout anterior a conexión TCP | T-11/T-14 | Corregido, revisión pendiente: recalcular antes de handshake | RED real 355,9 ms para 200 ms; GREEN dirigido y 97 pass/1 skip/seis subtests |
| B3 | Important | Versión int Python incompatible con UI segura | T-13/T-14 | Implementado, revisión pendiente: positiva exacta, decimal cuando supera entero JS seguro | Versiones -1 y 9007199254740993; RED UI2 → GREEN2 para representación exacta |
| D1 | Important | PEM incompleto provoca redacción cuadrática en show | T-13/T-14 | Implementado, revisión pendiente: barrido canónico lineal antes de recortar | RED3 de PEM/asignación/show; GREEN253/11 skips en regresión sintética con fixture corta |

Sin Critical/Minor ni hallazgos C. La observación D de 3.000 carpetas válidas
produjo 3.004 listados con solo una entrada contabilizada. Se acepta como
corrección adicional del presupuesto de metadata: máximo 256 listados,
contador scans y parcialidad; no se atribuye a D un grado que no emitió.
Reservar también el byte de sonda dentro del acumulado del lector.

No hay QA final, E2E o porcentaje del bloque todavía. Calidad de recuperación,
persistencia y elección de componentes siguen sin medir; tareas globales abiertas.

### RED original del bloque 16 — evidencia preservada

- **RED:** lector nuevo y validación pura: una aserción falló y 23 casos
  dieron error porque el módulo/API aún no existía; 2026-10-09. Después se
  implementaron snapshot y extracción de aprobación, con controles sintéticos.
- **RED:** bridge HTTP: 13 fallos de 18 controles por bytes, profundidad,
  cierre y plazo; forma inválida3/3 y DNS2/2 separados; 2026-10-09.
- **RED:** export portable: cinco fallos funcionales de cierre transitivo
  y ejecución mínima; 2026-10-09. El primer intento falló en setup por ruta
  larga y no constituye evidencia funcional; se conserva separado.
- **RED:** UI35 por ausencia de acciones/asset; literalID1 por vetos de
  caracteres incompatibles; transporte36/3 controles y deadline separado;
  2026-10-09. Los errores de conexión Windows por payload no leído se
  conservaron y la prueba de rechazo temprano pasó a enviar solo headers.

Los reportes originales se conservan privados; la evidencia pública final
registrará hashes y recuentos, excluyendo paths, cuerpos y capacidades de acceso.

Jira del intento 1: ejecutado sobre una copia propia del ledger y configuración
explícitamente desactivada; exit 0, `ops: []`. No se leyó configuración del
consumidor ni se publicó ningún mensaje externo.

RED adicional de revisión, 2026-10-09: UI2 para versión decimal exacta y
validación de versiones; UI1 para contador de listados fuera de presupuesto.
Sus reportes se preservaron antes de cambiar los respectivos controladores.
El rango descriptivo `imports_de_cabecera` del exportador se actualiza en
`agent-kits/shared/copias.json` tras el nuevo import AST; no añade una copia.

Corrección del redactor: RED válido con PEM/asignaciones/show acotados agotó
un plazo de tres segundos antes del cambio. GREEN dirigido27, fallback real1
y copia exacta1; regresión redactor/journal/view253 passed/11 skips. Un primer
run obtuvo ocho Git128 por longitud de ruta en la fixture; se conserva como
fallo del harness y se repitió con basetemp propio corto, sin alterar asserts.
JSON entrecomillado adverso ya pasaba y su regex permanece igual.

RED de corrección del lector, 2026-10-09: once fallos/dos controles por helper,
versiones, IDs y sonda; metadata1, ID opaco3, parser3, espacio literal1 y Unicode1.
Los reportes originales y hashes se registran en
`testing/memory-query-evidence.json`; conservar IDs literales también impide
seleccionar otra entrada al quitar espacios o usar mayúsculas ASCII únicamente.
La comparación de igualdad usa casefold Unicode compartido con la CLI.

RED del residual B1 en el segundo pase, 2026-10-09: nueve fallos y tres
controles por escalares entrecomillados, IDs con `#` o comilla interna,
referencias sin resolver y caché v4. La causa se verificó antes de corregir:
el parser quitaba las comillas y reinterpretaba el escalar como lista.
Las listas reales, la sucesión inversa y la caché son parte de la regresión.

## Revisión de dos lentes — intento 2: Bloque 16 (T-11/T-13/T-14/T-15) — residual de identidad

Lentes frescas A+B+C+D, fallback genérico sin override. Snapshot inmutable de
929 archivos públicos y 46 propios, alcance46/46 sin avisos/exclusiones;
las cuatro lentes confirmaron todos los hashes antes/después. A ejecutó
lint/evals/export/ledger con exit0; export58 ficheros al día. C sin hallazgos.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A1 | Important previo | Helper aprobado ausente pierde legado | T-11/T-13 | Corregido y verificado | A ejecutó dos bundles propios sin local/taxonomy: ADR-001 conservado y parcialidad |
| A2 | Important previo | RED original ausente del ledger | T-14/T-15 | Corregido y verificado | Ledger registra rojos originales y hashes de reportes |
| A3 | Important previo | README descriptivo de backends desactualizado | T-15 | Corregido y verificado | A confirma dependencia descriptiva actualizada en este bloque |
| B1 | Important | Escalar entrecomillado se interpreta como lista | T-11/T-13 | En corrección: preservar tipo de declaración e ID literal | `[ADR-002]` eligió ADR-002 ajeno como ok/completo; target ausente también se acortó |
| B2 | Important previo | Timeout TLS calculado antes de TCP | T-11/T-14 | Corregido y verificado | TCP130/200 ms deja70 ms para TLS en probe independiente |
| B3 | Important previo | Versiones Python/UI incompatibles | T-13/T-14 | Corregido y verificado | -1 parcial/null y entero grande decimal exacto; versión fuera de presupuesto diagnosticada |
| D1 | Important previo | Redactor cuadrático bloquea servidor | T-13/T-14 | Corregido y verificado | PEM261k ~32 ms; HTTP POST/GET ~233/240 ms; fallback real y scans256 probados |
| A4 | Minor | E25 conserva marcador índice v3 | T-15 | Corregido, revisión pendiente: E25 ahora v5 | La corrección de identidad invalida relaciones cacheadas y declara índice5 |

Fusión: cero Critical, un Important residual B1 y un Minor documental A4;
ningún rebate. Lo aprobado se conserva, salvo evidencia nueva. Las mediciones
de D son sintéticas y no acreditan eficacia de recuperación ni throughput real.
La corrección compartida del escalar cerró RED9/3 controles → GREEN12 y
regresión255 passed/2 skips; el tipo literal de cada item de lista recibe
comprobación adicional antes de congelar el tercer pase. QA final pendiente.

Jira del intento2 ejecutado en fixture propia con configuración explícitamente
desactivada: exit0, `ops: []`, ninguna publicación externa. RED adicional de
items entrecomillados, 2026-10-09: dos fallos y dos controles; GREEN combinado
22 passed conserva escalares/items/listas, inversas, caché y anotaciones
históricas. Cada item literal sin destino conserva su ID completo.

## Revisión de dos lentes — intento 3: Bloque 16 (T-11/T-13/T-14/T-15) — cierre de comilla pendiente

Lentes frescas A+B+C+D por fallback genérico, sin override. Snapshot inmutable
de 929 archivos públicos y 46 propios; alcance46/46 sin avisos/exclusiones.
Las cuatro lentes confirmaron todos los hashes antes/después. A comprobó
export58 con exit0 y delta22 passed. C no encontró defectos; D confirmó
comportamiento lineal del parser y mantiene D1 cerrado. No es QA final.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A1/A2/A3 | Important previos | Helper, RED y dependencia descriptiva | T-11/T-13/T-14/T-15 | Aprobaciones conservadas | Sin evidencia nueva que las reabra |
| B1 | Important previo | Identidad literal de escalares/items | T-11/T-13 | Corregido y verificado en escenarios previos | B ejecutó 40 controles de resolución, ausencia, inversas y caché5 |
| B2/B3 | Important previos | Deadline TLS y versión exacta | T-11/T-13/T-14 | Aprobaciones conservadas | Sin delta de comportamiento que las reabra |
| D1 | Important previo | Redactor cuadrático | T-13/T-14 | Aprobación conservada | Sin cambio del redactor; parser260 KiB ~23 ms y lista12.000items ~59 ms |
| A4 | Minor previo | Marcador de índice desactualizado | T-15 | Corregido y verificado | E25 y código declaran versión5 |
| B4 | Important nuevo | Barra literal impide cierre de comilla simple antes de comentario | T-11/T-13 | Pendiente de corrección acotada | `sucesor: 'ADR-002\\' # comentario` no resuelve el destino literal y pierde la inversa |

Fusión: cero Critical, un Important nuevo B4, cero Minor pendientes; sin
rebates. El orquestador verificó el scanner y la regla de escalares simples
de YAML1.2.2: la barra inversa no escapa la comilla simple. No se acepta como
deuda ni se declara aprobado el tercer intento.

Decisión explícita del orquestador tras alcanzar el máximo ordinario de tres
intentos: continuar con un único ciclo adicional acotado al cierre de comillas
del parser plano, sus controles y documentación. El usuario ya ha autorizado
corregir gaps y tomar decisiones técnicas; no se requiere otra autorización.
Se conserva toda la traza y las aprobaciones anteriores; una revisión fresca
validará el delta antes de QA. Las tareas globales permanecen abiertas.

Jira del intento3 ejecutado sobre fixture propia con configuración desactivada:
exit0, `ops: []`, sin lectura de configuración real ni publicación externa.

RED de B4 antes de producción, 2026-10-09: dos fallos de referencia presente
y ausente; 30 fallos y 24 controles para delimitadores escalares/listas.
Corrección mínima en ambos scanners con contador lineal de barras: las simples
delimitan con barra literal y las dobles respetan paridad. GREEN56 dirigido;
regresión view/local145 passed/1 skip, find66 passed y check-ignore original
aislado1 passed; caché/inversa y limitación previa3 passed. El primer fallo de
Git fue del stub del harness y se conserva, sin atribuirlo al código.
Los reportes RED y hashes se añaden a `testing/memory-query-evidence.json`.
Los comentarios exteriores de cada línea en listas de bloque siguen siendo
una limitación previa del parser plano; esta corrección no promete YAML completo.
Revisión adicional y QA final aún pendientes; no se declara aprobado B4.

## Revisión de dos lentes — intento 4: Bloque 16 (T-11/T-13/T-14/T-15) — ciclo adicional acotado aprobado

El ciclo adicional decidido por el orquestador conserva el tercer intento con
su gap. Lentes frescas A+B+C+D por fallback genérico, sin override. Snapshot
inmutable929 público/46 propio y alcance46/46 limpio; las cuatro lentes
confirmaron929 hashes antes/después. Todo el diff y los once nuevos se leyeron
íntegros. No se reabre ninguna aprobación sin evidencia nueva.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A1/A2/A3 | Important previos | Helper, RED y dependencia descriptiva | T-11/T-13/T-14/T-15 | Cierres conservados | A confirma continuidad completa y export independiente58/exit0 |
| B1 | Important previo | Identidad literal y listas | T-11/T-13 | Cierre conservado | Controles previos e inversas conservados; A78 dirigidos y B118 propios |
| B2/B3 | Important previos | Deadline TLS y versión exacta | T-11/T-13/T-14 | Cierres conservados | Sin nueva evidencia que reabra transporte/versiones |
| D1 | Important previo | Redactor cuadrático | T-13/T-14 | Cierre conservado | Sin delta del redactor; no se repite el benchmark anterior |
| A4 | Minor previo | Marcador de índice | T-15 | Cierre conservado | Documentación y código siguen en índice5 |
| B4 | Important previo | Cierre de comilla tras barra literal | T-11/T-13 | Corregido y verificado | B118/118 propios: presente/ausente, paridad, listas, inversas y caché; C283 controles del delta |

Fusión: cero Critical/Important/Minor pendientes, sin rebates ni deuda aceptada.
C no encuentra vulnerabilidades introducidas o reabiertas; D no encuentra
degradación material: scalar260 KiB ~53 ms, lista260 KiB ~79 ms y24.000items
~100 ms en sus fixtures. Esas mediciones no acreditan calidad de recuperación.
La revisión está aprobada; QA final, cobertura y browser son la siguiente puerta.
Las tareas globales, aceptación nativa y selección de componentes siguen abiertas.

Jira del intento4 sobre fixture desactivada: exit0, `ops: []`, sin publicación.

### Addendum de QA del ciclo4 — parser estándar sin capacidad de red

La primera QA Linux de este bloque obtuvo2089 passed/22 skips/seis subtests y
un fallo en el guard existente de imports. Su veto de todo `urllib` bloquea
el parser puro `urllib.parse` importado por `pathlib` en Python3.11; el camino
local degrada correctamente cuando el harness impide cargar su lector.
El informe y RED originales se conservan: no se convierte esa ejecución en verde.

B investigó de forma independiente en la misma imagen fijada, con contenedor
propio etiquetado y red desactivada: stack exacto desde `knowledge-view.py:10`
hasta `pathlib.py:14`; `urllib` padre vacío y `urllib.parse` sin socket/HTTP.
Permitir únicamente ese parser conserva los dos IDs aprobados esperados y
lectura completa, con cero eventos socket; un control separado confirma que
el auditor bloquea crear sockets. Se acepta como falso positivo del guard,
no como defecto del código de recuperación ni como relajación del acceso a red.

Ajuste únicamente de test: admitir `urllib.parse` y su paquete padre vacío,
seguir vetando socket/requests/HTTP y otros submódulos urllib, y añadir auditor
de operaciones de red. Las aserciones funcionales de IDs permanecen iguales.
Este addendum mantiene aprobado el código del ciclo4; requiere revisión A/B
del test y nueva QA sobre snapshot fresco, antes del cierre parcial y push.

### Addendum de cobertura del ciclo4 — journal sin helper compartido

QA completa: Windows4 obtuvo2070 passed/42 skips/seis subtests y Linux4q
obtuvo2090 passed/22 skips/seis subtests; las cohortes permanecen separadas.
La primera medición del diff frente a21092c2 obtuvo726/835 sentencias
ejecutables cubiertas, 86,95%, por debajo del mínimo90%. Se conserva ese
resultado y no se declara la puerta de cobertura aprobada.

El hueco principal son las funciones de redacción de respaldo del journal,
que no se ejecutan cuando viaja el helper canónico. Se añaden únicamente
tests funcionales en `agent-kits/shared/test_journal.py`: importan el archivo
real con ausencia simulada de ese helper, sin copiar el redactor ni cambiar
filenames de código. Comprueban captura persistida, redacción antes de
recorte, PEM/asignaciones y selección con identidad Unicode, sobre proyecto
y homes propios. Dirigido inicial20 passed; un fallo de fixture anterior
se conserva y no se presenta como RED de producción. El producto no cambia.

Siguiente puerta: revisión A/B de este addendum y dirigidos Windows/Linux.
Coverage.py combinará la batería Windows4 conservada y estos dirigidos con
aliases oficiales de rutas entre árboles de producto idénticos, verificados
por hash. No se suman los dirigidos dos veces a los conteos de suites ni se
atribuye cobertura del helper canónico al cuerpo de respaldo sin ejecutarlo.

### Cierre parcial del bloque16 — QA y consulta local

A/B aprobaron el addendum test-only, cero gaps nuevos; ambos snapshots
conservan929 hashes y el producto es idéntico. B ejecutó el test congelado
en Python3.11.16 propio y once controles del guard extraído: parser permitido,
seis imports de transporte y cuatro operaciones de red rechazados.

A/B aprobaron también los20 tests del fallback real del journal. Dirigidos
Windows/Linux20 passed cada uno, separados de las baterías completas.
Regresión del módulo Windows170 passed/10 skips con rutas propias cortas;
la primera ejecución con paths largos10 failed/161 passed/9 skips permanece
registrada. Solo se acortó el root/HOME del harness, sin modificar producto
ni tests entre ambas ejecuciones.

QA Windows del snapshot4:2070 passed/42 skips y seis subtests passed;
pytest, cobertura, lint, evals, export58 y ledger exit0. El test corregido
recibe un dirigido Windows separado1 passed; no se suma dos veces a la suite.
QA Linux del snapshot4q:2090 passed/22 skips y seis subtests passed, con
pytest/export58 exit0 en contenedor propio sin red, retirado. Lint/evals/ledger
se verifican aparte sobre snapshot4q y de nuevo tras la actualización documental.
El Linux4 original con un fallo permanece registrado, sin convertirlo en verde.

Cobertura de sentencias ejecutables añadidas frente a21092c2: 764/835 (91.5%), medida con Coverage.py Windows; scripts JavaScript tienen
controles propios y browser separado. qa-gate exit0 para ambas cohortes.

Browser real Chrome: siete callbacks públicos M-01–M-07 passed, cero fallos,
cero retries y CSP activa; API Playwright real, no runner CLI. Se revisaron
capturas escritorio/móvil sobre proyecto sintético y se cerró el servidor
propio sin cambios de fuentes. Dos arranques Edge fallaron antes de ejecutar
casos; Edge no queda validado. No se atribuye actividad viva de agentes.

Resultado: bloque16 entregado parcialmente; fuentes/evidencia/contratos
coherentes para búsqueda, entrada y relaciones locales explícitas. No activa
backends, no acredita eficacia comparada, UX de servicios ni hosts nativos.
Las pruebas funcionales separadas del bloque17 no se contabilizan como QA16.
T-07/T-08/T-11/T-13/T-14/T-15 y el objetivo global siguen abiertos; las
nuevas skills permanecen aplazadas en79/293 evaluadas y214 pendientes.

## Bloque17 — Resultados funcionales y contrato de integración

T-07/T-11/T-13/T-14/T-15 continúan abiertas. Esta entrega experimental publica
[fuentes/preguntas sintéticas](testing/fixtures/memory-benchmark/README.md),
[evidencia](testing/memory-benchmark-evidence.json),
[respuestas documentales](testing/memory-documental-answers.json),
[hechos temporales](testing/memory-temporal-facts.json) y
[conclusiones](comparisons/memory-functional-results.md). TDD n/a: documentación
y evidencia histórica propia; los cuatro Python de la fixture son fuentes de
prueba, no un nuevo ejecutor o código de producto. No se vuelve a contabilizar QA16.

Control local:12/12 preguntas con fuentes esperadas en top5,21 resultados
parciales/21 completos y cero generación. Kwipu:41/42 respuestas core y36/42
con hechos completos/atribuciones respaldadas,6/6 abstenciones, dos atribuciones
incorrectas;375 source_nodes con99 filenames nulos, sin enlace baseline completo.
Graphify:3/4 preguntas estructurales soportadas,9/9 repeticiones de esas tres;
93 ocurrencias/16 referencias distintas verificadas, sin PATH ni vigencia verificada.
Graphiti:4 episodios completos/12 búsquedas,0/9 valores numéricos esperados en
hechos y corte histórico violado3/3. Las tres repeticiones son recuperación sobre
una única ingesta; no se mide exactitud de respuestas generadas.

Revisiones independientes de control local, Kwipu, Graphify y Graphiti recalculan
métricas y hashes; la temporal contrastó doce búsquedas,83 hashes y trece fuentes.
Recursos Kwipu retirados, label actual
vacío; Graphiti registra cleanup exacto y ocho contenedores originales activos.
Los errores de harness antes de inferencia permanecen separados de fallos nativos.
El coste monetario, restauración, escritura interrumpida, UX y corpus real siguen
desconocidos. El LLM medido es cloud aunque embeddings y endpoints sean locales.

Decisión: base local y prioridad Kwipu/Graphify opcionales. Graphiti fuera de la
combinación recomendada por defecto, con capacidad existente opt-in y aceptación
temporal pendiente. No se cambia configuración del consumidor ni se elimina su
servicio. El [contrato siguiente](comparisons/memory-read-integration-contract.md)
define enlaces canónicos, respuesta sin autoridad, permisos antes de red,
selectores exactos y recibos de bytes ligados a artefactos. Todavía no implementado.

[Binding documental separado](testing/memory-documental-binding.json): dos
canónicos exportados por el adaptador real conservan ID/version/hash/project/scope
en2/2 chunks persistidos y GET nativo HTTP200;11 entidades excluidas. Snapshot
nativo/HTTP idénticos,7367 bytes. Ingesta adicional:2 LLM cloud+4 embeddings locales;
lectura posterior:0 inferencias/queries/constructores. Nueve fuentes y ocho archivos
del almacén conservaron hashes; recurso propio retirado. Fallos previos del harness
se conservan. Esta aceptación de metadata no valida routing, respuestas, el enlace
baseline de375 nodos o lectura integrada del producto.

Puertas de esta entrega: revisión A/B del alcance/documentación/evidencia sin
gaps y nueve checks readonly exit0 sobre snapshot propio. Ninguna tarea global
se cierra ni se inventan tokens/horas; skills79/293 y214 pendientes siguen aplazadas.

## Revisión de dos lentes — intento 1: Bloque17 (T-07/T-11/T-13/T-14/T-15) — evaluación y contrato de lectura

Lentes A+B por subagentes genéricos: la herramienta no permite seleccionar el
reviewer nativo. La revisión inicial recorrió34 piezas,42 respuestas documentales
y12 recuperaciones temporales; el addendum leyó todos los nuevos hunks y el
binding real. Resultado fusionado:0 Critical,0 Important,0 Minor. No se reabren
aprobaciones sin evidencia nueva. Esta revisión acepta documentación y evidencia
experimental, sin aceptar la lectura del bloque18 ni completar tareas globales.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| — | — | Sin gaps introducidos | T-07/T-11/T-13/T-14/T-15 | No requerida | Revisión A+B inicial y addendum contra artefactos reales |

C/D no aplican: selector automático sobre diff documental, ambas false, sin
motivos ni avisos. No se presenta como revisión de seguridad del futuro lector.
Alcance:36 archivos propios dentro del plan,0 fuera,0 avisos; una configuración
Jira sintética queda excluida por default, sin globs de usuario. Nunca se abre
configuración del consumidor ni memoria real para estos controles.

Checks exit0: scope, selección de lentes, lint, evals, export-interop --check,
ledger-lint,50 tests del índice del roadmap y dos ejemplos CLI reales sobre la
fixture propia. Export:58 archivos al día. Lint:0 errores y3 avisos genéricos
preexistentes. No se repite QA16 como evidencia nueva de producto; cobertura y
TDD de producto no aplican a esta entrega documental.

Publicación:958 hashes del snapshot intactos,117 enlaces locales válidos,
29 enlaces al consumidor excluidos antes de acceder,0 nombres/referencias
prohibidos. Los23 archivos de fixture conservaron exactamente sus bytes al
checkout con core.autocrlf=true. Se contrastaron doce documentos,42 textos
documentales,12 payloads temporales y2 bindings nativos completos.

Hashes SHA-256 de evidencia retenida:

- Manifest del alcance revisado: `4e636c5489158af283d9979a288e938ec737fd54571488a4dcfd3157625b40f8`.
- Addendum A: `b1cb769564896f2a348bb478fb26a8fae73f581cb08cfab8c9751ad3f341bdc3`.
- Addendum B: `ce3c769fbf67deaebad0876739c4c8dde05f7365f5978daa5815794acc7fea8b`.
- Checks readonly: `e73a44f93305a900869c23db3de4bded8cd403aea1133c84be8a380d4ffd969f`.
- Control de publicación: `ea455bf02c7d7db3f4f94599dace8c7f92f635cee97ad327079b5430089cd5bd`.

No se publican operaciones Jira ni se infiere su configuración real desde una
fixture desactivada. La traza final conserva abiertas continuidad nativa,
consulta documental autorizada, identidad/vigencia AST, UX, restore y el resto
del roadmap. La decisión de prioridad Kwipu/Graphify opcionales mantiene siempre
la fuente local y no cambia servicios/configuraciones del consumidor.

## Bloque18 — Implementación de lectura y contexto de código (en progreso)

T-07/T-11/T-13/T-14/T-15 siguen abiertas. La autorización documental, router por
intent, selectores/recibos AST y productor explícito ya están integrados en el
árbol de trabajo. Todavía no están revisados ni publicados. Este bloque no añade
skills, agentes o MCP y no configura servicios del consumidor.

Primer subpaso aplicado al árbol: selección pura compartida
`knowledge-taxonomy-local.entradas_enrutadas`, delegación del schema y del dueño
`knowledge-sync`. Conserva las entradas y el resumen explícito; routing falso o
ausente excluye entradas, y valores inválidos impiden construir cualquier envío.
No hace I/O, no carga adaptadores y no activa lectura. La aceptación nativa
documental y AST se registra abajo; revisión independiente y QA final siguen
pendientes. Los subpasos siguientes conservan sus checkpoints históricos.

RED: `agent-kits/shared/test_knowledge_routing.py::test_routing_selection_is_pure_preserves_summary_and_excludes_private`
falló con AttributeError por función pública ausente ·2026-10-09. Después pasó.
RED: `agent-kits/shared/test_knowledge_routing.py::test_invalid_routing_cannot_authorize_any_entry`
falló en cinco casos porque devolvía entradas con routing inválido ·2026-10-09.
Después de la comprobación estricta, los seis casos nuevos y las suites vecinas
de schema, lectura aprobada y sincronización dieron156 passed. La cohorte anterior
de37 tests de selección/sync es subconjunto; no se suman como193 casos distintos.

La [evidencia parcial](testing/memory-read-implementation-evidence.json) conserva
hashes y resultados observados. Son pruebas del subpaso, no QA completo del bloque18,
garantía de ausencia de regresiones globales ni autorización para declarar cierre.

Segundo subpaso: `local-read.read_text(include_digest=True)` devuelve SHA-256 de
bytes originales desde el mismo descriptor validado, sin segunda apertura. BOM y
CRLF se incluyen en ese hash, aunque el texto UTF-8 decodificado omita BOM. El modo
por defecto conserva su forma de salida. Un flag no booleano se rechaza antes de
abrir archivos; no se devuelven hashes de lecturas fallidas o inestables.

RED: `agent-kits/shared/test_local_read.py::test_optional_digest_uses_original_bom_and_crlf_bytes_on_same_read`
falló con TypeError por opción inexistente ·2026-10-09. Tras implementar la opción,
reader/view dieron202 passed y7 skipped Windows. RED:
`agent-kits/shared/test_local_read.py::test_invalid_digest_flag_is_rejected_before_file_access`
falló en tres casos al intentar abrir el archivo ·2026-10-09; tras validación estricta,
la suite reader dio61 passed y6 skipped. Cohortes solapadas, no se suman. La
autorización documental utilizará el digest de bytes, nunca el hash del texto
decodificado como si fuera el del canónico original.

### Integración aplicada y aceptación nativa parcial del bloque18

El núcleo prepara permiso sobre corpus completo y routing estricto. Lectura
documental exige opt-in e intent autorizado, filtros que cubran todo el corpus,
canon/export/manifest y todos los chunks ligados antes/después. El deadline es
común y una cita sin resolver suprime toda la respuesta. Esta conserva
`no_verificada`, autoridad `ninguna` y `citas_por_afirmacion: false`.
No se convierte `group_id` en supuesto filtro documental. Graphiti conserva
su contrato de grupo existente; consultas ordinarias, hooks y panel siguen locales.

AST añade identidad exacta, rechazo de duplicados y recibos ligados al SHA-256
del artefacto y todos sus inputs. Cambio, límite o lectura inestable retiran
contexto. El productor llama Graphify externo elegido explícitamente, sin
descarga/instalación. Publica recibo al final; no promete atomicidad del par,
cobertura global, autenticación ni semántica aprobada.

RED/GREEN adicionales observados el 2026-10-09, con salidas originales y hashes
en la evidencia parcial; los casos ya verdes no se presentan como RED:

- `test_knowledge_routing.py`: cuatro alias numéricos del routing y dieciséis
  opciones documentales fallaron antes de validar bool/int estrictos. Una prueba
  de schema completo demostró que ignoraba `read`; otra mostró nombres de límites
  distintos entre política y adaptador. Tras corregirlos, policy/schema/context
  dieron160 passed.
- `test_local_read.py`: ocho casos fallaron por API binaria ausente; el caso de
  descriptor abierto seguido de ausencia falló hasta devolver `changed_path`
  incluso con contenido vacío. Reader final:70 passed/6 skipped.
- `test_knowledge_view.py`: cuatro casos RED por digest ausente precedieron al
  snapshot opcional de bytes originales. `test_knowledge_read_context.py`: diez
  RED por módulo ausente, luego igualdad bool/int y versión cero fallaron; el
  bundle parcial lanzó RuntimeError hasta degradar. Context final:14 passed.
- `test_code_selectors.py` y `test_code_receipts.py`: ROOT observó API exacta
  ausente y frescura heredada no verificada antes de integrar la propuesta. Tres
  RED adicionales de lectura inicial exigieron salida parcial explícita. Consumer
  final:131 passed entre las cuatro suites.
- `test_backend_markdown_read.py`: API de lectura ausente dio RED en ROOT; dos
  casos de sonda acumulada probaron exceso de presupuesto antes de corregirlo.
  Adaptador final:55 passed.
- `test_code_context_build.py`: ROOT observó productor ausente antes de integrarlo.
  Producer final:24 passed y18 subtests, separados del ensayo nativo.
- `test_knowledge_router_read.py`: lectura documental sin grupo retornaba local
  antes de integrar el router; final49 passed/1 skipped, con dos casos de HTTP
  loopback real sobre fuentes sintéticas. No son queries al bridge nativo.

Cohorte intermedia local/schema/AST:533 passed/7 skipped y18 subtests antes del
ajuste `max_` y del router. Cohorte pública limpia adapter/publicación/sync:
202 passed/1 skipped y6 subtests antes del router. Son conjuntos solapados y
checkpoints distintos; no se suman ni se llaman QA final del bloque.

Se preservan los fallos de harness: comparación Windows de stat vs fstat,
mock de firma opcional, aserción antigua de tamaño, path temporal largo y
bytecode ajeno leído por un test histórico. El caso sync dejó de reproducirse
con temporal corto; el snapshot público excluyó bytecode antes de copiar.
Una lectura inestable de fixture no se reprodujo y su causa queda desconocida;
no se debilita el guard. Fallos reales de igualdad, versión, lectura y sonda
se corrigieron con sus regresiones.

Aceptación documental nativa: prepare y adaptador reales,2 POST query sobre dos
exports sintéticos persistidos; ambos chunks retornan en ambas preguntas. ID
nativo resolvió una cita con filename nulo. Fuente modificada y proyección vieja
se rechazaron antes de cualquier POST/inferencia nueva.2 LLM cloud y2 embeddings
locales, thinking false;1684 prompt/602 evaluation y50 embedding tokens observados,
coste € desconocido. Ocho stores originales/copias y cinco canónicos/proyecciones
quedaron byteexact; dos contenedores y una red propios retirados por ID verificado.
Primer startup falló RemoteDisconnected con cero queries/modelos y quedó preservado;
solo se corrigió readiness GET del harness. Este ensayo no incluyó el router.

Aceptación AST nativa: productor real Python generó8 nodos/7 arcos y cuatro inputs
de193 bytes; lector final comprobó4/4 en ID/par, retiró contexto tras cambio y
lo recuperó tras restauración byteexact. Cero inferencia/red/procesos observados.
La gramática JavaScript ausente dio unavailable sin instalarla; la fixture no
contiene definition_file positivo, cubierto por unit tests. Scope declarado
no demuestra cobertura global ni elimina ABA.

Documentación y matriz E43–E47 acompañan las aristas. Revisión independiente,
QA final Windows/Linux, cobertura changed-only y cierre local/push del bloque18
siguen pendientes. No se cierran tareas globales ni se integran nuevas skills.

## Revisión de dos lentes — intento 1: Bloque18 (T-07/T-11/T-13/T-14/T-15) — correcciones requeridas

Lentes A+B+C+D por subagentes genéricos de contexto fresco; la herramienta no
expone reviewer nativo. Scope previo exit0:41 archivos públicos en alcance,
0 fuera/avisos; una configuración Jira sintética propia desactivada se excluye.
Siete gates readonly exit0,970 hashes intactos,212 enlaces locales comprobados
y32 enlaces al consumidor excluidos antes de acceder. El primer check de enlaces
trataba dos directorios documentales válidos como ficheros; se conserva el fallo
y se corrige únicamente el harness. Esto no es QA final de producto.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A2 | Critical | Productor sobrescribe grafo/recibo preexistentes sin autoría | T-11/T-15 | Implementado; pendiente revalidación: destinos nuevos, creación exclusiva y ningún borrado/reemplazo final al fallar | Probe reemplazó dos sentinelas propios; CONSTITUTION línea36 |
| A1 | Important | Router devuelve generación tras vencer deadline en normalización | T-11/T-14 | Implementado; pendiente revalidación independiente | RED tres fases de normalización, seguido de GREEN |
| B1 | Important | Biblioteca sin helper privado lanza AttributeError fuera del envelope | T-11/T-14 | Implementado; pendiente revalidación: helper callable y supports protegidos antes de extracción | Probe compatible sin _get_extractor; sin outputs |
| D1 | Important | Snapshot inicia más E/S local tras vencer deadline | T-11/T-14 | Implementado: plazo opcional compartido en snapshot, guard antes de nuevas lecturas/listados | Probe100 inputs/100ms simulados:102 lecturas,92 tardías,10,2s virtuales para1s; no benchmark de disco |
| A3 | Minor | Contrato dice que los RED no se ejecutaron | T-15 | Prosa corregida; pendiente revalidación | Contrato ahora remite a evidencia/ledger observados |
| B2 | Minor | Router pierde score documental y publica puntuación cero | T-11 | Implementado; pendiente revalidación | Loopback real0,7→0 en review; regresión devuelve0,7 |

C no encontró vulnerabilidades introducidas. Los disparadores SQL/prompt resultaron
falsos positivos con evidencia: interpolación de CAMPOS constante y documentación
del productor explícito. No se cuentan como gaps rebatidos del producto.
Manifest revisado: `8f15b4f5d986272737edba1b9a8789e2023be48f3d5829f02bb560a0ac73041c`.
Los cuatro hashes de informe están en la evidencia parcial del bloque18.

Correcciones ROOT con RED del 2026-10-09: tres fases del router devolvían backend
tras deadline y score0,7 se volvía0 (4 failed/50 deselected). Después:53 passed/1
skipped. Snapshot carecía de argumento deadline en cinco casos y autorización
iniciaba E/S hasta108,8 con vencimiento101,2 (6 failed/163 deselected); después
view/context/router:221 passed/2 skipped. Cohortes solapadas; no se suman.
La normalización no concede autoridad y el snapshot por defecto conserva su API.
Un syscall ya iniciado puede bloquear; el guard detiene trabajo posterior y no
promete cancelación del kernel o atomicidad.

Los dos fixes del productor están integrados. No se publica el bloque hasta
revalidar los gaps, completar QA Windows/Linux/cobertura y cerrar las puertas. Jira real no se consulta ni modifica; el control de su fixture no prueba
la configuración del consumidor. Las tareas globales y nuevas skills aplazadas
conservan sus estados. La aceptación nativa publicada identifica su checkpoint,
sin atribuirla automáticamente al código corregido después.


Integración del productor corregido,2026-10-09: ROOT reprodujo los destinos
preexistentes y las dos incompatibilidades de API antes de copiar producción:
5 failed/1 passed contando los tres subcasos de sentinelas; el passed no se
considera RED. Después, productor/consumer/router/context/view:387 passed/2
skipped y21 subtests. No se suma a cohortes anteriores. Productor
`0534e0ae95f5585d14e2fd216eeebe10dc1e6bebd320290653e4360f10085d96`;
tests `bdb3b1c29108f067ba1bdc47c57bb15fcc70bfb2e7696434622f5d559d8d7f97`.
Se preservan11 RED del implementador, incluido el borrado de un reemplazo
concurrente justo antes de unlink;35 tests pasan en su copia propia.

Publicación: ambos destinos deben estar ausentes antes de importar/extraer;
creación exclusiva del grafo y, al final, del recibo. Un fallo no borra ni
reemplaza rutas finales, aunque quede un grafo parcial propio. Para repetir se
elige un destino nuevo. No se promete publicación atómica ni prevención ABA.
El ensayo nativo repetido con el productor corregido conserva94 hashes fuente
y104 archivos de checkpoints anteriores:4 fuentes/193 bytes,8 nodos/7 arcos AST,
cero red/inferencias/procesos. Cambio durante export impide ambos outputs;
gramática JS ausente degrada sin instalar. Resumen de QA del implementador
`99e2c104b9e63a603d20f0e0d1fd07a342f4754134ba129024f851638c40c41d`.
Revalidación independiente y QA final siguen pendientes.

Evento Jira del intento1 ejecutado en fixture propia desactivada: exit0,
`ops: []`, `jira: desactivado`. Salida
`d13f10ad80738cd9980a8d4249037a6029aacd20d205694b984028744e9d5d30`;
ledger de fixture
`580fc066b8b60eadd8c90590edb6003e6b10b91e3453dae6b75f9971634c1cfd`.
No se accedió a configuración ni se publicaron eventos de consumidores.


## Revisión de dos lentes — intento 2: Bloque18 (T-07/T-11/T-13/T-14/T-15) — sin gaps pendientes

Lentes A+B+C+D de contexto fresco por fallback genérico. Scope previo exit0:
41 archivos públicos en alcance,0 fuera/avisos; configuración Jira sintética
desactivada excluida, sin configuración real consultada. Los siete gates
readonly pasan;970 hashes verificados,212 enlaces locales válidos y32 destinos
del consumidor excluidos antes de acceder. Manifest revisado:
`c3425e58637128f9c262ca22cbdf07dd3ac03656c751786af328f93609c52710`.

Se traspasaron la tabla completa y los cuatro informes del intento1. El delta
de19 archivos se revisó completo, conservando aprobaciones previas; no se
declara una segunda auditoría completa del diff inicial. Ningún gap del producto
fue rebatido. Resultado fusionado:0 Critical,0 Important,0 Minor pendientes.

| # | Grado anterior | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A2 | Critical | Sobrescritura de outputs preexistentes | T-11/T-15 | Corregido y revalidado: destinos nuevos, links exclusivos, ningún borrado/reemplazo final al fallar | A: pruebas de sentinelas/concurrencia/no unlink; CONSTITUTION36 conforme |
| A1 | Important | Generación servida tras deadline durante normalización | T-11/T-14 | Corregido y revalidado: guard final tras normalización/filtro/redacción | A/B: tres fases cruzan plazo y devuelven local sin generación |
| B1 | Important | Helper opcional incompatible lanza fuera del envelope | T-11/T-14 | Corregido y revalidado: callable protegido/degradación antes de extract | B: tres paquetes sintéticos missing/noncallable/throws, sin outputs |
| D1 | Important | Nuevas lecturas locales tras vencer plazo | T-11/T-14 | Corregido y revalidado: deadline absoluto propagado a snapshot | D: misma carga100 archivos/100ms/1s,10 lecturas/0 tardías/1s virtual; antes102/92/10,2s |
| A3 | Minor | Contrato niega RED observados | T-15 | Corregido y revalidado: referencias a checkpoints observados y QA pendiente | A: contrato y evidencia coherentes |
| B2 | Minor | Score documental perdido | T-11 | Corregido y revalidado: alias score numérico finito | B: hits y source_nodes conservan0,7 |

A ejecutó24 pruebas y3 subtests propios; B14 pruebas seleccionadas más probes;
D siete probes de reloj virtual; C revisión estática sin hallazgos. Son
cohortes separadas y no se suman ni se confunden con QA final. D confirma
también deadline en listados/import/index/refresh y el límite explícito de un
syscall ya iniciado. Fuentes y manifiesto permanecen intactos. Hashes:

- A: `3e669ac16270aa2967967c496ac58b27d1e6d0a681a879828474e803273b898d`.
- B: `e8f0bdcb1e93640943c67126b219e47950add0bff1d35c9354facb5071ad9b09`.
- C: `a1eff49f80e2d92aa0d3ef309239648b04e7c077c76c8ab86ba80e115eb39db6`.
- D: `954c241c7e04000e5f857f532e92ef06414a781e7dbead3477b05fd8d94323ba`.

Aceptación de revisión, no verde QA: quedan Windows/Linux, las dos métricas
de cobertura>=90%, el recorrido nativo del router documental actual y el
cierre de publicación. Las tareas macro conservan sus estados. No se publica
el bloque ni se declara completada la integración por este veredicto.

Evento `revision`,intento2,actor reviewer ejecutado después del veredicto en
fixture propia con Jira desactivado: exit0,`ops: []`,sin publicación externa ni
inferencia de configuración del consumidor. Salida
`e6bbff98f69e08f2ec80dea3c5dcab7d70132a542ba495cd3af73eec62426b8a`;
ledger de fixture
`79cd18cdccf1eaa9d11ea6c86bcc384f3ecb7fb4b57e9e3dc08893287b09f146`.

### Bloque18 — aceptación funcional del router nativo y QA posterior

El recorrido nativo completo `consultar_intent` pasó dos consultas positivas
y dos negativas, sobre una copia sintética propia. Se ejecutaron la preparación
canónica, el adaptador, los snapshots y la normalización reales, sin reemplazar
sus guardias. Las fuentes se enlazaron a ID, versión, hash y ruta canónica;
el filename nulo de una fuente se resolvió por su UUID nativo exacto. Cambiar
el cuerpo canónico o su versión conservando la proyección anterior devolvió
el camino local, sin nuevos POST ni llamadas a modelos.

Resumen de aceptación:
`92c17357263dce154ce2397c3205dea73fa61c4777d0a6ac00c22c2f8f6f6326`;
manifest de91 archivos:
`263a64ae0f136242451c959e615f27c5921387a7e64cb8c40f5d33193c03e9a5`.
Las diez fuentes propias del recorrido coinciden con el checkpoint del intento2.
Los nueve módulos nativos seleccionados se verificaron antes y después; esto
no acredita toda la imagen. Los archivos protegidos y los fixtures restaurados
permanecieron intactos. Se retiraron tres recursos propios por identidad exacta,
con ausencia posterior comprobada y sin nuevos volúmenes.

Contadores:2 POST de consulta,2 LLM,2 embeddings,6 solicitudes de metadata,
0 reintentos POST y0 peticiones denegadas. Se usaron modelos ya instalados:
`gpt-oss:120b-cloud` con inferencia cloud aprobada y `nomic-embed-text` local.
Uso opaco observado:1684 tokens de entrada LLM,326 de salida y50 de embedding;
coste monetario desconocido. Ambas consultas recuperaron los dos documentos:
no se midió precisión de recuperación. Las respuestas siguen siendo
`no_verificada`, sin autoridad ni acreditación de cada afirmación. La estabilidad
observada no certifica atomicidad ni prevención de ABA. No se repiten llamadas
a modelos para corregir las suites de compatibilidad.

La QA Linux posterior del mismo checkpoint rechazó el bloque: cuatro fallos
en compatibilidad de receipt con colisión de mayúsculas, descripción de skill
mayor que1024 caracteres y dos escenarios de consola sin payload no ASCII.
La cobertura oficial dio media de diez archivos89,58859975135722% y líneas
ejecutables añadidas/cambiadas1198/1332=89,93993993993993%; ambos gates>=90%
fallaron, sin redondeo ni cambio de umbral. Se conservan las salidas originales
y se preparan correcciones y pruebas en copias propias. Windows sigue en QA;
ningún resultado parcial se declara verde. Esta aceptación nativa no sustituye
a la QA multiplataforma ni cierra tareas macro.

Windows terminó también NO-PASS:935 pruebas pasan/19 skips en lectura local;
1005 pasan/3 fallan/21 skips y21 subtests en router/código;
494 pasan/1 falla/3 skips y6 subtests en documental/panel. Linux conserva
953 pasan/1 skip,1004 pasan/4 fallan/21 skips y21 subtests, y497 pasan/1 skip
y6 subtests, respectivamente. No se suman cohortes ni plataformas.
Windows dio media89,34617550893297% y1198/1332 líneas cambiadas cubiertas;
ambos gates fallan. Lint/evals/export/ledger y los970 hashes de fuente pasan
en ambas plataformas. La configuración del usuario no se consultó.

El fallo documental Windows exige un POST en una fixture cuyo plazo total de
100ms empieza antes de preparar el bridge. La investigación posterior en copia
propia reprodujo0 POST: preparación, lecturas, redacción, health/snapshot y
refresh consumían ese plazo. Una segunda ejecución natural alcanzó el POST
con26,6ms restantes; retrasar120ms el setup produjo0 GET/POST. Se conserva
esa evidencia y se separará el test de transporte del gate del plazo total,
sin reiniciar deadlines del producto ni ampliar sus límites. Sigue pendiente
integrar las correcciones, revisión independiente del delta y nueva QA completa.

Integradas ocho correcciones exactas después de terminar ambas QA originales:
identidad portable de inputs y alias del artefacto/recibo en el lector,
regresión que exige rechazo antes de leer fuentes, fixture de consola con
etiqueta UTF-8 real y verificación del payload exacto, descripción de skill
reducida de1148 a960 caracteres conservando todos los disparadores, docs ES/EN
y changelogs. Patch
`8aa92d3559f799fd90a61556f44212baec24a0f14264b07f9740d897cbc0233c`;
suite OWN seleccionada Windows758 pasan/9 skips, Linux767 pasan. No son la
QA final ni cierran gaps por sí solas. El primer intento de integración rechazó
antes de cualquier escritura una comprobación de runtime que solo existe como
check Linux; se corrigió usando las attestaciones reales antes/después de970
archivos en ambas plataformas, conservando el check de runtime Linux.

La inspección del delta detectó una coherencia pendiente: el productor aún
aplica identidad sin distinguir mayúsculas solo en Windows, mientras el lector
corregido la exige portable. Se prepara regresión real Linux y corrección del
productor antes del tercer pase independiente. La aceptación nativa anterior
conserva sus hashes históricos; no se atribuye al consumidor corregido sin
validación de ese checkpoint. Continúan pendientes las pruebas adicionales,
la fixture de transporte corregida, revisión del delta y QA de cierre.

Integrados el productor portable y las tres suites coordinadas por hash exacto:
productor
`0534e0ae95f5585d14e2fd216eeebe10dc1e6bebd320290653e4360f10085d96`
→ `2d67c8f9cca9020927c0ad08b4e55103c7a9a8d6d5226ac8b029d252e1d0a12c`.
Solo cambian dos expresiones de identidad, que rechazan duplicados y alias de
destinos antes de leer inputs o cargar la biblioteca opcional. RED Linux real:
3 fallos,1 caso exterior pasado —no contado como RED— y43 deselectados;
GREEN productor Linux44 pasan/1 skip/39 subtests, Windows45 métodos OK.
Patch productor:
`bcf3d8e7fe791f42d8e461a90b11db88c90cc881f5bc9da5f4ba29aef973c248`.

Patch de pruebas:
`9963e8028feb1911f68402a814370b82e16a93e53d17f713d84e0722de0d9e23`;
180 pasan/39 subtests en la selección Windows contra ese candidato. Añade
rechazo de contratos y grafos nativos inválidos sin publicación, presupuesto
de staging, inputs ilegibles sin importar biblioteca, edición tardía de fuentes,
policy/filtros/deadlines inválidos antes de leer, autoridad canónica incompleta,
fuentes/chunks contradictorios, URLs prohibidas sin DNS, health degradada y
consulta íntegramente vacía cuando expira el plazo total. La prueba directa de
POST lento mantiene100ms absolutos y timeout<300ms, con1 POST; el caso de
consulta completa agotada conserva el deadline original y exige0 transporte.

La cobertura oficial del subconjunto de tres archivos da media85,6734% y
707/751 líneas ejecutables cambiadas=94,1411%. No se presenta como cobertura
global. La unión estática con trazas anteriores tampoco constituye QA y no
habilita publicación. Quedan la aceptación AST nativa del nuevo checkpoint,
el tercer pase independiente y nueva QA completa con ambos gates>=90%.

Aceptación AST nativa offline del checkpoint portable completada, driver exit0:
productor `2d67c8f9cca9020927c0ad08b4e55103c7a9a8d6d5226ac8b029d252e1d0a12c`
y consumidor `8e7286951ee86519869358154e6c355de90e7f05e8b7654a5376f085819d2b36`,
con clausura standalone de cinco archivos comprobada contra ROOT. Cuatro
fuentes sintéticas/193 bytes produjeron8 nodos/7 arcos; doce consultas —cuatro
fuentes por ID, archivo+label y símbolo— devolvieron contexto con todos los
inputs declarados verificados. Editar únicamente la fuente OWN no utilizada
por la consulta rechazó el artefacto entero y suprimió nodos/arcos; restaurarla
recuperó la verificación. Destinos nuevos exclusivos, sin sobrescribir prueba
previa. Artifact y receipt conservaron los hashes históricos por usar idéntica
fixture; la ejecución nueva acredita explícitamente el checkpoint portable.

Informe
`73fef7e212a6b890f6c2cade1344927187e5468eed3b730ede87c08ee8bb4300`;
resumen
`993060f734e9e3834e54e134952afa22880cdeca107922ae7e43b7f61e904113`;
manifest de26 archivos
`c1c8d5deb38c8fa0ea83d3c00fe53c35f26607aa7baae5eecc7edd168bf02e14`.
ROOT comprobó sus26 hashes, las doce respuestas, rechazo/restauración y
clausura actual. Biblioteca nativa fijada a
`5b74d7d74911cf435c8f1636b6f96ea202cc6246`:94 archivos de helper y104 previos
intactos respecto a la referencia antes/después. Cero sockets/procesos externos
y denegaciones; sin modelos, descargas, Docker, endpoints o cambios al consumidor.
No acredita cobertura del repositorio, semántica aprobada, autenticación,
atomicidad ni prevención de ABA. El caso JS sin gramática sigue histórico;
no se instaló ni repitió. La clausura documental de diez archivos es separada.

ROOT verificó también1266 filas de la traza E43–E47 contra los índices,
identidades, estados y hashes de los seis JUnit originales. Esos casos se
solapan y siguen acreditando NO-PASS en el checkpoint del intento2, no el
verde del delta. Las fuentes del siguiente pase deben congelarse de nuevo.


## Revisión de dos lentes — intento 3: Bloque18 (T-07/T-11/T-13/T-14/T-15) — sin gaps nuevos o reabiertos

Cuatro lentes A+B+C+D de contexto fresco revisaron íntegro el delta de14 archivos/2411 líneas. Se conservaron la tabla completa de20 criterios y las aprobaciones anteriores; ningún gap de producto fue rebatido. Resultado fusionado:0 Critical,0 Important,0 Minor pendientes. Fuente pública congelada:970 archivos,42 cambios; manifest `0ebbb8313c63897d549d015590c22e4047a74e2293946f104412a5ed3e61334e`. Los hashes de producción y pruebas actuales coinciden con esa fuente.

A:34 pruebas/18 subtests y dos payloads UTF-8 exactos; B:76 pruebas/18 subtests; C y D revisión estática. Son cohortes separadas y no se suman. D conserva D1 corregido porque seis módulos pertinentes siguen idénticos. Q1–Q4 conformes; las adiciones Q5 son pertinentes, pero la cobertura final sigue pendiente.

- A: `928b11c378de87c970b5222ba6cb0810bff4a091a2a547b60109b94cf592c973`.
- B: `0a282ae3c290c4862bb42d39247b791dfb75bf716861942b4676606a0c99737b`.
- C: `70ab48dee42d341117e239500890488d345dbb982bacccb671cb888354ac079e`.
- D: `0ab37da41c2702f1fde3133607bd1bdadc21f9206eea8c011b98671c96d56c03`.

Aceptación de revisión, no verde QA. Se preservan los fallos Windows/Linux y los dos gates originales inferiores al90%. Los checkpoints nativos actuales documental y AST siguen siendo pruebas funcionales separadas. Quedan QA completa en ambas plataformas, las dos métricas oficiales>=90% y publicación. Ninguna tarea macro se cierra por esta revisión.


Evento de revisión3 ejecutado sobre fixture propia Jira desactivada: exit0,0 operaciones; no se consultó configuración del consumidor ni se publicaron mensajes. Stdout SHA `637579da152352acacb582fde8ae1032ab614bf5ddec25a32b0133caeef6c50f`; ledger propio SHA `ffe1859b2444e8d8757703a76ad94b4337858ecd7288a5a86e56b0badd50ebfa`.


## Bloque18 — QA final aceptada y cierre de implementación

Tras el tercer pase independiente sin gaps nuevos o reabiertos, ambas ejecuciones finales terminaron con exit 0, conservando los mismos handles y sin reinicios. La raíz comprobó 172 artefactos sellados y 1.422 filas E43–E47 contra identidad, índice, estado y SHA de seis JUnit reales. Los 21 artefactos originales NO-PASS permanecen intactos.

| Plataforma/cohorte | Passed | Failed | Skipped | Subtests raw |
|---|---:|---:|---:|---:|
| windows/local-state | 956 | 0 | 19 | 0 |
| windows/router-code | 1023 | 0 | 21 | 39 |
| windows/documental-panel | 539 | 0 | 3 | 6 |
| linux/local-state | 974 | 0 | 1 | 0 |
| linux/router-code | 1023 | 0 | 21 | 39 |
| linux/documental-panel | 541 | 0 | 1 | 6 |

Totales JUnit: Windows 2.518 passed/0 failed/43 skipped; Linux 2.538/0/23. CLI auxiliares: 6 Windows y 8 Linux; los qa-gates incluyen esas CLI y son VERDE. Subtests, plataformas y cohortes históricas no se suman como casos únicos.

| Plataforma | Media de los diez archivos cambiados | Ejecutables añadidas/cambiadas | Gates |
|---|---:|---:|---|
| windows | 91.127209834166% | 1255/1333 = 94.14853713428357% | PASS ambos ≥90% |
| linux | 91.37956456318409% | 1255/1333 = 94.14853713428357% | PASS ambos ≥90% |

Coverage.py oficial y diff OWN del snapshot revisado; sin redondeo para aceptar, sin cambiar selección/umbrales ni asumir cobertura de hijos. Es media por archivo, no afirmación de que cada archivo individual supere el 90%. Lint/evals/export/ledger pasan. coverage-check auxilia solo: defined/referenced vacíos no acreditan cobertura del test-plan macro ni cierran tareas.

Las regresiones de servidor/controles del panel están incluidas. No hubo nueva navegación ni Playwright; Chrome7 anterior sigue siendo checkpoint histórico. Las aceptaciones nativas documental de diez módulos y AST portátil de cinco módulos son evidencia separada vinculada al código actual; no se repitieron modelos durante QA. Los 970 hashes de fuente y copias se conservaron. El contenedor propio Linux fue retirado por ID tras comprobar identidad, con ausencia final confirmada.

- Manifest de revisión y QA: `0ebbb8313c63897d549d015590c22e4047a74e2293946f104412a5ed3e61334e`.
- Informe final: `086a0ebda26896cdbdc6bbcdd61b076a8ab710efb285aee1b0603d0be7ccda5f`.
- Evidencia final: `a81d9c399df7f5f0209f974aebaa1ad61a156151775f4172d61974bd20f9541e`.
- Handoff sellado: `94f985dd8bfd661b4d5bc6503053d0c7829e3421732c118735f3dcfc6d133d46`.

Aceptada la implementación parcial del bloque: lectura documental explícita, selección pura, contexto canónico/deadline, selectores AST, recibos y productor sobre destinos nuevos. La memoria local conserva su disponibilidad sin servicios externos. Queda publicación de la rama; T-07/T-11/T-13/T-14/T-15 siguen abiertas por restore, corpus grandes, continuidad/aprendizaje y demás capacidades. No se declara superioridad experimental, autenticación del productor, atomicidad del par ni prevención de ABA.


## Continuación del historial operativo

Los siguientes registros mantienen los bytes originales del ledger antes de su
reorganización del 2026-10-11. Sus resultados pertenecen al snapshot indicado;
el estado actual sigue en [tasks.md](tasks.md). Las tablas y resúmenes de revisión
necesarios para los comandos se conservan también en el ledger.

## Revisión de dos lentes — intento 3: Bloque18 (T-07/T-11/T-13/T-14/T-15) — sin gaps nuevos o reabiertos

Cuatro lentes A+B+C+D de contexto fresco revisaron íntegro el delta de14 archivos/2411 líneas. Se conservaron la tabla completa de20 criterios y las aprobaciones anteriores; ningún gap de producto fue rebatido. Resultado fusionado:0 Critical,0 Important,0 Minor pendientes. Fuente pública congelada:970 archivos,42 cambios; manifest `0ebbb8313c63897d549d015590c22e4047a74e2293946f104412a5ed3e61334e`. Los hashes de producción y pruebas actuales coinciden con esa fuente.

A:34 pruebas/18 subtests y dos payloads UTF-8 exactos; B:76 pruebas/18 subtests; C y D revisión estática. Son cohortes separadas y no se suman. D conserva D1 corregido porque seis módulos pertinentes siguen idénticos. Q1–Q4 conformes; las adiciones Q5 son pertinentes, pero la cobertura final sigue pendiente.

- A: `928b11c378de87c970b5222ba6cb0810bff4a091a2a547b60109b94cf592c973`.
- B: `0a282ae3c290c4862bb42d39247b791dfb75bf716861942b4676606a0c99737b`.
- C: `70ab48dee42d341117e239500890488d345dbb982bacccb671cb888354ac079e`.
- D: `0ab37da41c2702f1fde3133607bd1bdadc21f9206eea8c011b98671c96d56c03`.

Aceptación de revisión, no verde QA. Se preservan los fallos Windows/Linux y los dos gates originales inferiores al90%. Los checkpoints nativos actuales documental y AST siguen siendo pruebas funcionales separadas. Quedan QA completa en ambas plataformas, las dos métricas oficiales>=90% y publicación. Ninguna tarea macro se cierra por esta revisión.


Evento de revisión3 ejecutado sobre fixture propia Jira desactivada: exit0,0 operaciones; no se consultó configuración del consumidor ni se publicaron mensajes. Stdout SHA `637579da152352acacb582fde8ae1032ab614bf5ddec25a32b0133caeef6c50f`; ledger propio SHA `ffe1859b2444e8d8757703a76ad94b4337858ecd7288a5a86e56b0badd50ebfa`.


## Bloque18 — QA final aceptada y cierre de implementación

Tras el tercer pase independiente sin gaps nuevos o reabiertos, ambas ejecuciones finales terminaron con exit 0, conservando los mismos handles y sin reinicios. La raíz comprobó 172 artefactos sellados y 1.422 filas E43–E47 contra identidad, índice, estado y SHA de seis JUnit reales. Los 21 artefactos originales NO-PASS permanecen intactos.

| Plataforma/cohorte | Passed | Failed | Skipped | Subtests raw |
|---|---:|---:|---:|---:|
| windows/local-state | 956 | 0 | 19 | 0 |
| windows/router-code | 1023 | 0 | 21 | 39 |
| windows/documental-panel | 539 | 0 | 3 | 6 |
| linux/local-state | 974 | 0 | 1 | 0 |
| linux/router-code | 1023 | 0 | 21 | 39 |
| linux/documental-panel | 541 | 0 | 1 | 6 |

Totales JUnit: Windows 2.518 passed/0 failed/43 skipped; Linux 2.538/0/23. CLI auxiliares: 6 Windows y 8 Linux; los qa-gates incluyen esas CLI y son VERDE. Subtests, plataformas y cohortes históricas no se suman como casos únicos.

| Plataforma | Media de los diez archivos cambiados | Ejecutables añadidas/cambiadas | Gates |
|---|---:|---:|---|
| windows | 91.127209834166% | 1255/1333 = 94.14853713428357% | PASS ambos ≥90% |
| linux | 91.37956456318409% | 1255/1333 = 94.14853713428357% | PASS ambos ≥90% |

Coverage.py oficial y diff OWN del snapshot revisado; sin redondeo para aceptar, sin cambiar selección/umbrales ni asumir cobertura de hijos. Es media por archivo, no afirmación de que cada archivo individual supere el 90%. Lint/evals/export/ledger pasan. coverage-check auxilia solo: defined/referenced vacíos no acreditan cobertura del test-plan macro ni cierran tareas.

Las regresiones de servidor/controles del panel están incluidas. No hubo nueva navegación ni Playwright; Chrome7 anterior sigue siendo checkpoint histórico. Las aceptaciones nativas documental de diez módulos y AST portátil de cinco módulos son evidencia separada vinculada al código actual; no se repitieron modelos durante QA. Los 970 hashes de fuente y copias se conservaron. El contenedor propio Linux fue retirado por ID tras comprobar identidad, con ausencia final confirmada.

- Manifest de revisión y QA: `0ebbb8313c63897d549d015590c22e4047a74e2293946f104412a5ed3e61334e`.
- Informe final: `086a0ebda26896cdbdc6bbcdd61b076a8ab710efb285aee1b0603d0be7ccda5f`.
- Evidencia final: `a81d9c399df7f5f0209f974aebaa1ad61a156151775f4172d61974bd20f9541e`.
- Handoff sellado: `94f985dd8bfd661b4d5bc6503053d0c7829e3421732c118735f3dcfc6d133d46`.

Aceptada la implementación parcial del bloque: lectura documental explícita, selección pura, contexto canónico/deadline, selectores AST, recibos y productor sobre destinos nuevos. La memoria local conserva su disponibilidad sin servicios externos. Publicada la entrega de implementación en la rama; T-07/T-11/T-13/T-14/T-15 siguen abiertas por restore, corpus grandes, continuidad/aprendizaje y demás capacidades. No se declara superioridad experimental, autenticación del productor, atomicidad del par ni prevención de ABA.

## Bloque18 — publicación comprobada

Entrega publicada en `feat/catalog-capabilities`, commit `ded934a70e56508601006a06d52550cbfb7da019`; el SHA remoto observado coincide. Se comprobaron los 43 blobs publicados. Git normalizó CRLF a LF en 13 archivos; los hashes de bytes de la fuente probada se conservan y la evidencia distingue los hashes de blobs publicados. La única diferencia de esos archivos es el fin de línea; los AST de Python y los valores JSON coinciden.

El cierre público conservó 971 archivos, 43 cambios, 214 enlaces locales válidos y 32 destinos del consumidor excluidos antes de leer. La revisión independiente de documentación no dejó gaps; informe SHA `2df7ed67848727ef8e278688f43772bae3e4f1f1a520e79888bfbc18500e5d20`. El historial archivado permanece intacto. El lector real del panel reconoce nuevamente la iniciativa y sus 16 tareas: muestra hasta ocho activas y declara `task_budget` cuando corresponde.

Esta publicación cierra el bloque de implementación, no las tareas macro ni la integración global. Restauración, corpus grandes, continuidad, aprendizaje y las capacidades restantes del panel y comandos siguen pendientes.

## Bloque19 — integración de revisión visual en curso

El [contrato](comparisons/plan-review-integration-contract.md) concreta el diseño elegido de revisión de planes. Alcance: dueño compartido, transporte/UI opt-in y consumo desde la puerta «OK del plan». Las skills y la ampliación de hooks permanecen aplazadas.

La implementación se prepara en fuentes propias aisladas. El candidato del dueño conserva 35 assertions RED previas a sus comportamientos y 46 pruebas GREEN en Windows. Coverage.py mide 384/398 líneas ejecutables, 96.48241206030151%, sin atribuir cobertura de subprocesos. Dos errores del harness por nombres de parámetros demasiado grandes no cuentan como RED. Los tres fallos intermedios de fsync en Windows permanecen en la evidencia y motivaron la corrección del descriptor.

El candidato del panel y la actualización de comandos/documentación avanzan en paralelo. Ningún resultado individual acepta todavía el bloque. Quedan unión real de UI/CLI/puerta, Linux, interacción en navegador, callers de los tres runtimes, revisión independiente y QA del código integrado. No se cierra ninguna tarea macro.

La consolidación aplica fuentes exactas del dueño, transporte/UI y doce archivos de comando/documentación. La comprobación previa a la integración detectó un envío POST en curso que podía acompañarse de un banner incorrecto; cinco RED reales preceden la corrección. La UI corregida pasa 40 casos, incluidos 29 escenarios Node, y conserva el handoff anterior. Estos checkpoints se solapan y no son QA del conjunto.

El comando obtiene ID/versión con `open` antes de iniciar el servidor y registra el runtime actual. Codex y OpenCode regeneran sus proyecciones comunes. La [evidencia de candidatos](testing/plan-review-implementation-evidence.json) conserva límites, fuentes y resultados por componente; revisión independiente, plataformas, navegador y publicación permanecen pendientes.

## Bloque19 — regresiones de normalización antes de corregir

RED: `agent-kits/shared/test_plan_review.py::test_gap_b1_c1_sanitized_plan_is_redacted_before_display` falló porque la vista mostraba un token sintético ensamblado al retirar controles; dos casos · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_gap_b1_c1_comment_roundtrip_keeps_receipts_readable` falló con `unavailable/invalid_state` después de guardar o sellar comentarios aceptados; cuatro casos · 2026-10-09.

RED: `tests/test_panel_review_server.py::test_gap_b1_c1_http_comments_do_not_reveal_tokens_or_poison_state` falló porque la respuesta HTTP contenía el token sintético saneado sin redactar; cuatro casos · 2026-10-09.

Los diez fallos son assertions de regresión en una copia propia, sin errores de colección ni skips. El dueño mantenía su SHA previo `536931b06e6ce0689d7434c0392e4f1517bdcf2ad7281d379d4f3d9ddbaefaff`; stdout RED SHA `731bfd7f9734ac7c475686ec013b03e061661ded001ab2aee20af4029ac27c06`. Esta evidencia precede la corrección y no acepta QA del conjunto.

## Revisión de dos lentes — intento 1: Bloque19 (T-11/T-13/T-14/T-15) — correcciones pendientes de validación

Lentes A+B+C+D sobre 28 archivos y 978 hashes de fuente. C usa el informe estático independiente de reemplazo; su primer informe fue interrumpido por un filtro automático. B conserva un addendum del error de serialización. Tres gaps Important tras fusionar la misma raíz B/C; no hay Critical ni Minor. Ningún resultado de revisión acepta QA.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A1 | Important | Faltaba traza RED canónica | T-11/T-13/T-14 | Registrar las observaciones previas existentes, con procedencia | RED por criterio abajo; 35 assertions del dueño, dos errores de harness excluidos; pendiente de validar |
| A2 | Important | Faltaba salida del check de interop | T-11/T-15 | Registrar exit y stdout del check real | `export-interop --check: 58 ficheros al día`, exit 0; pendiente de validar |
| BC1 | Important | El saneado posterior a redacción exponía texto y volvía inválido el recibo | T-11/T-13/T-14 | Sanear controles antes de redactar vista y comentarios | Diez RED/GREEN dedicados y 156 vecinos GREEN en Windows; pendiente de validar |

### Observaciones RED previas a la creación y endurecimiento del dueño

RED: `agent-kits/shared/test_plan_review.py::test_raw_view_and_sections_bind_exact_full_redacted_content` falló con unavailable/missing_owner antes de existir el dueño; 1 caso(s) · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_plan_failures_never_create_authorizing_state` falló con unavailable/missing_owner antes de existir el dueño; 3 caso(s) · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_selection_scope_rejected_before_state` falló con unavailable/missing_owner antes de existir el dueño; 4 caso(s) · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_comments_cas_and_sealed_decision` falló con unavailable/missing_owner antes de existir el dueño; 1 caso(s) · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_invalid_comments_never_freeze_decision` falló con unavailable/missing_owner antes de existir el dueño; 3 caso(s) · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_receive_keeps_delivery_until_revalidated_idempotent_ack_and_restart` falló con unavailable/missing_owner antes de existir el dueño; 1 caso(s) · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_changed_plan_blocks_each_decision_boundary_and_retains_old_record` falló con unavailable/missing_owner antes de existir el dueño; 3 caso(s) · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_gate_and_ack_identity_are_not_interchangeable` falló con unavailable/missing_owner antes de existir el dueño; 1 caso(s) · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_poll_is_read_only_and_unknown_id_has_no_state_effect` falló con unavailable/missing_owner antes de existir el dueño; 1 caso(s) · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_existing_unowned_state_and_foreign_record_are_preserved` falló con unavailable/missing_owner antes de existir el dueño; 1 caso(s) · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_state_scope_deadline_and_link_rejections` falló con unavailable/missing_owner antes de existir el dueño; 1 caso(s) · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_deadline_at_commit_and_fsync_failure_do_not_claim_success` falló con unavailable/missing_owner antes de existir el dueño; 1 caso(s) · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_record_and_response_budgets_do_not_truncate_or_drop_prior_receipt` falló con unavailable/missing_owner antes de existir el dueño; 1 caso(s) · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_common_cli_pipeline_and_registration_are_runtime_independent` falló con unavailable/missing_owner antes de existir el dueño; 3 caso(s) · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_corrupted_nested_state_cannot_be_served_or_consumed` falló con aceptó estado anidado inválido; 5 caso(s) · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_directory_creation_race_never_adopts_foreign_state` falló con creó marker en un directorio aparecido durante la carrera; 1 caso(s) · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_foreign_record_in_owned_namespace_is_not_adopted_by_new_open` falló con no rechazó el recibo ajeno del namespace; 1 caso(s) · 2026-10-09.

RED: `agent-kits/shared/test_plan_review.py::test_unavailable_plan_serves_history_readonly_and_never_consumes` falló con devolvió review nulo en lugar de conservar hechos históricos; 3 caso(s) · 2026-10-09.

### Observaciones RED del panel y cierre

Los ocho registros siguientes conservan el resumen del autor de sus salidas de herramientas; no se presentan como un stream stdout capturado.

RED: tests/test_panel_review_server.py::test_review_open_and_get_delegate_without_browser_paths failed TypeError create_server() unexpected keyword review_selection · 2026-10-09. Test expresses missing opt-in transport API, production still exact base.

RED: tests/test_panel_review_ui.py::test_review_is_explicit_live_only failed TypeError render_html() unexpected keyword review_enabled · 2026-10-09. Product unchanged before test.

RED: tests/test_panel_review_ui.py::test_review_controller[missing_canonical_history] failed generic unavailable discarded historic consumed receipt · 2026-10-09. Owner contract refinement notified before product adaptation.

RED: tests/test_panel_review_ui.py::test_cli_explicit_gate_selection (None/requested-review/plan-ok) failed missing gate_key and argparse unknownflag · 2026-10-09. Parent authorized minimal --review-gate-key extension.

RED: tests/test_panel_review_server.py::test_comment_budget_maps_to_413_without_owner 2 cases failed 400 != 413 · 2026-10-09. Budget HTTP mapping correction before product fix.

RED: tests/test_panel_review_ui.py::test_review_controller[multiple_comments_same_section_preserved] failed dropping existing-two on save · 2026-10-09. Sharedowner permits unique IDs on one section; transport/UI must preserve rows.

RED: tests/test_panel_review_ui.py::test_review_controller[poll_keeps_comment_editing] failed textarea.disabled true during GETstatus · 2026-10-09. Poll would blur focused editable comment every5s; keep editing while readpoll in-flight, mutatingbuttons disabled.

RED: tests/test_panel_review_ui.py::test_review_controller[unavailable_cannot_enable_current_view] failed enabling approval for contradictory unavailable/current envelope · 2026-10-09. UI must reject incoherent display projection, no receipt-state implementation.

RED: `tests/test_panel_review_ui.py::test_review_controller[close_blocked_during_submit]` falló con `close.disabled false != true` · 2026-10-09.

RED: `tests/test_panel_review_ui.py::test_review_controller[close_blocked_during_comments]` falló con `close.disabled false != true` · 2026-10-09.

RED: `tests/test_panel_review_ui.py::test_review_controller[close_blocked_during_refresh_post]` falló con `close.disabled false != true` · 2026-10-09.

RED: `tests/test_panel_review_ui.py::test_review_controller[close_preserves_sealed_changes_consumed]` falló porque el banner «cerrada sin decidir» descartaba hechos de la decisión sellada · 2026-10-09.

RED: `tests/test_panel_review_ui.py::test_review_controller[close_during_get_preserves_later_known_decision]` falló porque el banner «cerrada sin decidir» descartaba hechos de la decisión sellada · 2026-10-09.

El stdout capturado de estos cinco casos tiene SHA `6561d7793dfe264c9a11ff5e352194df75f82c3b0ddd02187b66c02d5dc886dd`. Los GREEN de componente se solapan y no se suman como QA final.

### Check real y siguiente puerta

`python3 scripts/export-interop.py --check` se ejecutó en la fuente integrada congelada del intento 1: exit 0, stdout `export-interop --check: 58 ficheros al día`, stderr vacío. ROOT y la lente A lo ejecutaron por separado; los 978 hashes permanecieron intactos. Los hashes y límites de los informes figuran en la [evidencia del bloque](testing/plan-review-implementation-evidence.json).

TDD n/a: incorporación de trazas/documentación de A1/A2. La corrección de BC1 tiene sus diez RED antes del cambio y diez GREEN después; la suite vecina pasa 156 casos sin fallos. Falta el segundo pase independiente y QA Windows/Linux, navegador, callers y paquete portable. Todas las tareas macro conservan su estado.

## Revisión de dos lentes — intento 2: Bloque19 (T-11/T-13/T-14/T-15) — implementación aceptada

2026-10-10. Lentes A/B/C/D independientes de contexto fresco, fallback genérico porque el revisor nativo no está disponible. Los informes conservan los criterios aprobados del primer pase y revisan los cinco archivos corregidos; no hay rebatidos. Fuente sellada: 978 archivos públicos, 28 en el diff; manifest SHA `1764fcaa55ddfd015419fa1a74a4c78a7cb8a10f1b48a35b725a3d286bbf84ce`, diff SHA `84d89fed1281c2f9d849a402f847d3d6be89a48a854d592e310109c3d4068ffc`. Los hashes antes/después coinciden. Los tres Important anteriores quedan corregidos y validados; 0 Critical, 0 Important y 0 Minor pendientes.

| Hallazgo anterior | Validación independiente |
|---|---|
| A1: trazas RED canónicas | A valida identidades, errores, fecha y procedencia individual; conserva la distinción entre capturas y resumen atribuido del autor. |
| A2: evidencia interop | A ejecuta un check propio: exit 0, stdout `export-interop --check: 58 ficheros al día`, stderr vacío; 978 hashes intactos. |
| BC1: saneado antes de redacción | B valida la corrección con 14 pruebas del dueño y 12 probes independientes; C la valida estáticamente con CWE-180/200. No se suma este checkpoint a QA. D conserva su aprobación de rendimiento sin repetir por rutina el benchmark. |

Los SHA de los cuatro informes están en la [evidencia del bloque](testing/plan-review-implementation-evidence.json). El evento de revisión se comprobó en configuración Jira OWN desactivada: exit 0, ops vacías y cero escrituras externas; el error anterior de harness sin `--batch` se conserva. No se leyó configuración consumidora.

QA Windows/Linux está en ejecución sobre la misma fuente revisada: 42 módulos en tres cohortes, dueño/servidor/builder completos, dos gates Coverage.py ≥90% sin redondear y qa-gate oficial desde JUnit real. Esto no declara su resultado. La prueba de navegador abrió la URL loopback sintética, pero Edge mostró «Microsoft Edge ha bloqueado esta página», `ERR_BLOCKED_BY_CLIENT`; cero escenarios UI ejecutados. Se cerraron la pestaña propia y el servidor registrado sin cambiar protecciones. La interacción real y los callers nativos siguen pendientes; todas las tareas macro conservan su estado.

TDD n/a: registro de revisión y resultados de infraestructura, sin cambio de código de producto.

### QA: registro de consola pendiente

La cohorte router/code de Linux terminó con 4 fallos, 1027 passes, 21 skips y 39 subtests reportados por separado. Los cuatro fallos detectan la ausencia del modo del nuevo CLI en la batería de codificación; no se eliminan ni excluyen. Stdout capturado SHA `3ae32f6fa41748d5d593d04cd691df559633342720d128f354c996692ffbd4aa`. La ejecución completa sigue en curso y no tiene aceptación QA.

RED: `tests/test_console_encoding.py::test_arranca_sin_reventar_en_consola_no_utf8[agent-kits/shared/plan-review.py-cp1252]` falló con AssertionError: el nuevo CLI no declara modo en MODOS · 2026-10-10.

RED: `tests/test_console_encoding.py::test_arranca_sin_reventar_en_consola_no_utf8[agent-kits/shared/plan-review.py-ascii]` falló con AssertionError: el nuevo CLI no declara modo en MODOS · 2026-10-10.

RED: `tests/test_console_encoding.py::test_la_salida_sigue_siendo_utf8_no_interrogantes[agent-kits/shared/plan-review.py-cp1252]` falló con KeyError: 'agent-kits/shared/plan-review.py' · 2026-10-10.

RED: `tests/test_console_encoding.py::test_la_salida_sigue_siendo_utf8_no_interrogantes[agent-kits/shared/plan-review.py-ascii]` falló con KeyError: 'agent-kits/shared/plan-review.py' · 2026-10-10.


### Corrección del registro de consola

Se integra únicamente `tests/test_console_encoding.py`: añade el modo operacional `open` sobre un plan sintético Unicode y su state-root propio. La ayuda del CLI es ASCII, por eso no sustituye la prueba. No se cambia el dueño ni se excluye ningún caso. Antes del cambio, el autor reproduce los cuatro RED sobre la misma fuente; después, los cuatro casos pasan y la batería completa de consola pasa 530 casos en Windows. Es un checkpoint del autor, sin aceptación QA global ni suma con los casos anteriores. Stdout de la batería SHA `cd221e07f1f1e4f7f2db47140105f122b9f91ac6c68d33d906279186eda29724`; informe SHA `83764b23d2dfb0384c3c7b62f843195e73484ffdb9827680607f0233170c7a68`.

La primera ejecución Linux conserva sus fallos y el cleanup del contenedor OWN confirmado. El auxiliar de comando falla por el alias privado `utf8-sig`; el recolector se detiene porque `test_mermaid_blocks.py` es una guarda CLI sin casos pytest. Se preparan correcciones privadas y una ejecución explícita de esa guarda, manteniendo las otras 41 selecciones pytest y los 29 escenarios Node obligatorios. No se borran ni convierten los resultados anteriores en verdes. Falta el tercer pase sobre este delta y QA reparada; navegador y callers siguen pendientes.

## Revisión de dos lentes — intento 3: Bloque19 (T-11/T-13/T-14/T-15) — sin gaps pendientes

2026-10-10. Lentes A+B+C+D de contexto fresco, fallback genérico por revisor nativo no disponible, sin override de modelo. Se conservan todos los criterios y aprobaciones anteriores; el delta revisado contiene registro de consola y dos archivos de evidencia. Los otros 975 archivos, incluida toda producción, conservan sus bytes. Fuente sellada: 978 archivos, 29 en el diff; manifest `834bb1e2050939a9ca6336cd9923e65fe58d0ced1209169e9b2ba2491b7d3d62`, diff `5259c025108e39b807fb3f8b3d90d682cc19d3efe18c97623258d759cfb011a7`. ROOT verifica informes, artefactos declarados y coincidencia de fuente con el árbol. Resultado: 0 Critical, 0 Important, 0 Minor pendientes; ningún gap rebatido o convertido en deuda.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A1 | Important histórico | Trazas RED canónicas | T-11/T-13/T-14 | Corregida en R2, conservada | A mantiene IDs, errores, fechas y procedencias individuales. |
| A2 | Important histórico | Prueba de exports en ledger | T-11/T-15 | Corregida en R2, conservada | A3 ejecuta check propio: exit 0, stdout `export-interop --check: 58 ficheros al día`, stderr vacío; 978 hashes intactos. |
| BC1 | Important histórico | Normalización después de redacción | T-11/T-13 | Corregida en R2, conservada | Dueño y regresiones mantienen bytes aprobados; B/C no encuentran evidencia de reapertura. |
| Consola | Fallo QA de registro | Cuatro casos cp1252/ascii sin modo para el dueño | T-11/T-14/T-15 | Registro operacional con fixture Unicode propia | A valida traza RED previa y límites; B verifica cuatro casos y dos probes de pipes, sin sustituir QA. C/D no encuentran vulnerabilidad o carga nueva. |

Los SHA de A/B/C/D están en la [evidencia del bloque](testing/plan-review-implementation-evidence.json). Los siete gates previos pasan; no son aceptación de QA, navegador ni callers nativos. Ninguna tarea macro cambia de estado. TDD n/a para este registro de resultados; el RED/GREEN del registro de consola permanece separado.

### QA original terminada — resultados conservados como NO-PASS

| Plataforma | Passed | Failed | Skipped | Subtests separados |
|---|---:|---:|---:|---:|
| Windows | 2678 | 4 | 43 | 45 |
| Linux | 2698 | 4 | 23 | 45 |

Las dos ejecuciones originales terminaron con exit 1. Los cuatro fallos de consola son reales y preceden la corrección revisada. Además, el checker privado usó un alias de codec inválido y la selección incluyó Mermaid, script standalone sin casos pytest: falta su ejecución CLI, no se omite su guard. Windows detectó seis consultas de registro de Codex que el stub OWN bloqueó con exit 97; Linux no tuvo intentos. No se ejecutó el CLI real ni se accedió al registro consumidor. La causa estática liga tres modos de doctor por dos codecs y diferente materialización del CODEX_HOME temporal; los logs originales no permiten atribución individual por PID.

Los runners se detuvieron antes de qa-gate, los gates finales de cobertura y los hashes posteriores. Existen CoverageJSON y JUnit reales, pero no se atribuye al primer intento verificación que no ejecutó. Los checks portable pasaron con seis casos por plataforma sobre CLI común y etiquetas de runtime; no prueban tres hosts nativos. El contenedor Linux propio fue retirado por ID con ausencia confirmada. Los seis XML, logs, fallos y pruebas auxiliares permanecen intactos.

La siguiente ejecución repara sólo consola y auxiliares defectuosos/faltantes, con agregación explícita de procedencias y conservación de resultados originales. La producción no ha cambiado. La aceptación de navegador y de callers nativos permanece pendiente; no se convierten Node/HTTP o etiquetas de runtime en evidencia equivalente.

Evento revisión3 sobre fixture Jira OWN desactivada: exit 0, ops vacías, cero escrituras externas. Stdout SHA `6a946c3fa6a690ce2f112293593f78e69ac1329c2078d0764af8ee13bc9f5f35`; ledger propio SHA `08cb5e81daebd124ddb58c5e8adfaa30b6c091ae51ec293eb9627f4207a2a8ad`.

### Bloque19 — referencia documental de los comandos

La comprobación independiente del puente documental detectó un Minor: el enlace relativo al panel era válido en el comando canónico, pero apuntaba a carpetas inexistentes en las dos proyecciones generadas. Se conserva el resultado original 70/72. La política de exports conserva el cuerpo canónico sin transformar rutas; por eso se sustituyó una única línea de documentación por la referencia explícita a `docs/PLUGIN-PANEL.md` en la documentación del plugin, y se regeneraron las dos copias. No se modificó el exporter ni ninguna instrucción del workflow.

La comparación de bytes verifica una única sustitución por archivo y el contrato funcional de revisión visual idéntico. Generación y check de exports: exit 0; enlaces restantes 69/69, más tres referencias explícitas al documento existente. El recuento baja en tres porque se retiraron el enlace canónico válido y las dos copias inválidas. El informe inicial y sus fallos permanecen intactos. Esta corrección de prosa no reabre la implementación aceptada ni acredita QA, navegador, callers nativos o cierre macro. TDD n/a: prosa y proyecciones generadas.

QA incremental iniciada Windows/Linux sobre fuente834 aceptada, en destinos OWN nuevos. Se ejecutan consola completa de 530 IDs y auxiliares defectuosos/faltantes; se retienen JUnit/coverage/portable válidos con cierre de dependencias y sustitución explícita por IDs. Stub de registro Codex cerrado y sintético, con manifest real/argv/cwd/hash/PID; no hay CLI nativo real. Runner SHA `d91d1ae2da7e250ce5e69d52e93bbfbff31c9eeaeb036fbfbc018ad7782924f1`; receta SHA `1225502c57d4d4cb9e1ce9ef7b856b19fee29daa9c2b76c84fcfbe71d4ac71e0`. La ejecución está en curso y todavía no se declara verde. El puente documental posterior de cinco archivos queda separado de la fuente QA sellada.

La primera repetición incremental terminó con exit 1 en ambas plataformas antes de tests o creación de contenedor: el PATH necesario de Node contiene también un CLI OpenCode real y el preflight estricto lo rechazó. Cero pruebas ejecutadas y cero CLI nativos lanzados. Se conservan los resultados terminales y las copias/hashes previos; al ocurrir antes del try/finally del runner, la traza se atribuye al tool y no a un log generado por el runner. Se prepara un OWN nuevo con Node existente copiado y ligado por hash a un bin aislado; no se amplía PATH ni se elimina el guard. No es un fallo nuevo del producto ni aceptación QA.

Nueva QA incremental iniciada Windows/Linux con copia OWN byte exacta del Node existente en directorio aislado; el rechazo previo del PATH y los fallos originales quedan conservados. Se mantiene la misma selección, fuente834, receta y guard estricto. Runner SHA `349014078051da28600152686c36022cb820aa242f5157d382940dec7a03dda8`; receta SHA `1225502c57d4d4cb9e1ce9ef7b856b19fee29daa9c2b76c84fcfbe71d4ac71e0`. Handles reales observados; ninguna aceptación QA se declara mientras están en curso. El puente documental posterior sigue separado.

La QA Node aislada termina Windows exit 0 (veredicto del runner, pendiente de comprobación ROOT) y Linux exit 1 tras consola completa exit 0 y auxiliares exit 0. El assert de fixture cerrada detecta cero llamadas: el stub Linux escrito desde Windows conserva shebang CRLF y no puede ejecutar `/bin/sh`; no se retira ese assert. Se conserva el fallo, los hashes y la retirada por identidad del contenedor propio. Se prepara únicamente corrección LF del harness para Linux, con candidata Windows retenida bajo puente explícito del cambio de rama; aún no hay aceptación QA global.

Corrección auxiliar LF adoptada en OWN nuevo y QA Linux iniciada con handle real1422. La comparación reversible demuestra que sólo cambian escritor/assert del stub Linux y nombre del contenedor propio; cuerpo Windows, fuente834, receta y proofs siguen exactos. Se retiene la candidata Windows terminal0 sin repetición rutinaria, pendiente de verificador completo por plataforma. Runner Linux SHA `b5dbcbedb5db0edc94d88d583806cd22c8904949133dd41c7ddba0d68f20d76e`; pointer SHA `51cdf42e13161bd3a159be9a2ab27d3e464bcb5b32952358f2dee81c408eedb7`. Se conserva el assert de llamadas CLOSED y toda evidencia NO-PASS previa.

QA de implementación del Bloque19 aceptada por ROOT tras comprobar íntegramente artefactos, procedencia y gate oficial de ambos OS sobre fuente834: Windows2682 passed/0 failed/43 skipped y Linux2702 passed/0 failed/23 skipped;2725 casos JUnit únicos por OS. Los530 casos de consola sustituyen sus mismos IDs anteriores;45 subtests crudos van aparte y29 casos Node ya están incluidos. El gate oficial incluye10/14 auxiliares adicionales y sale VERDE. Coverage oficial retenida bajo hashes/diff idénticos: media3 Windows96.31596814342258% y Linux96.62560154100005%;líneas ejecutables cambiadas515/532 y518/532, con umbral calculado sin redondeo. Seis llamadas mock cerradas por OS y cero CLI nativos reales. Windows se retiene con puente de harness que sólo modifica LF/nombre de contenedor en rama Linux; original NO-PASS, preflight y fallo shebang quedan intactos. Cleanup Linux por ID/imagen/label/network y ausencia verificados. Recibo QA SHA `8168de7023e9fc6685d61ca9a56e525a4c6b6966ac2f005e3ab572facd5489fc`; verificador SHA `020fd4370de91804c0cc81ee1905387f2a3ab8ad791de1a147f73635bac93c5c`. Navegador real, tres hosts nativos, cobertura macro y cierre global siguen pendientes; el puente final documental/metadatos se valida por separado antes de publicación.


## BLOQUE20 — conservación y recuperación de memoria local

Contrato propuesto: [memoria local y recuperación](comparisons/memory-local-recovery-contract.md). Define doce oráculos N01–N09: conservación canónica y colas, caché ausente/corrupta, cuatro fronteras de corte, reintento de manifiesto, restauración quiescente, autoridad, lectura offline y scope/redacción. Añade la regresión del parser para enlaces inline entrecomillados, sin sustituir la fixture por bloques.

Evidencia de aceptación: `UNKNOWN`. Preservar cada ejecución fallida y su clasificación, fuente/Gold/recipe/harness, JUnit y auditorías. El RED/GREEN del autor acredita la regresión específica; ROOT requiere ejecución congelada Windows/Linux y puertas pertinentes antes de aceptar el bloque. Ningún resultado anterior se reutiliza como PASS de recuperación.

| Macro existente | Trabajo del bloque |
|---|---|
| T-07 | Documentar límites de persistencia y recuperación frente a eficacia de consulta ya medida. |
| T-08 | Mantener corpus y colas locales como autoridad; caché reconstruible y contrato de publicación/idempotencia. |
| T-09 | Verificar captura confirmada, barreras y cleanup por identidad, sin añadir hooks o hosts. |
| T-11 | Conservar handoffs y aprobación actuales; legacy, propuesta y aprobado mantienen estados distintos. |
| T-13 | Vincular la guía de consulta a conservación/recuperación y estados parciales; consultar no restaura. |
| T-14 | Revisar regresión y doce casos obligatorios, cobertura oficial del diff y qa-gate; guardar fallos de infraestructura aparte. |
| T-15 | Integrar contrato y enlaces breves en guías propietarias; verificar enlaces y exportaciones afectadas. |
| T-16 | Incorporar evidencia sólo tras aceptación real del bloque; mantener pendiente el cierre de la iniciativa. |

Esta inserción no crea una tarea macro ni modifica los dieciséis campos `Estado`, dependencias o porcentajes. Mantener sólo T-01 completado y conservar todos los pendientes nativos, de escala y aprendizaje restantes.

### Corrección del lector y preparación reproducible

2026-10-10. Se integra la normalización compartida de listas YAML simples: retira una sola pareja de comillas coincidentes y conserva valores mal formados para su rechazo. No añade un parser YAML completo. La fixture entrecomillada original se conserva.

El autor observó 6 failed/7 passed antes del cambio y 13 passed después sobre los mismos IDs. El pase final de documentación volvió a ejecutar esos 13 IDs; no se suma como 26 pruebas distintas ni acepta QA global. JUnit RED SHA `bec970d45bab216aebe71e025ce9dd0f3430b587883a810f96987ed9c2fe9a78`; JUnit final GREEN SHA `eef0f24d7551ad3f9d58ac479c0ec31330b6acdf3ee0d21ed154aa295bd18d45`. ROOT verificó artefactos y adoptó los dos archivos exactos del autor.

RED: `tests/test_knowledge_approved_retrieval.py::test_quoted_links_regression_same_identity_related_and_readonly[double]` falló con AssertionError: show devolvió partial en lugar de ok · 2026-10-10 (ejecución del autor, JUnit conservado).

RED: `tests/test_knowledge_approved_retrieval.py::test_quoted_links_regression_same_identity_related_and_readonly[single]` falló con AssertionError: show devolvió partial en lugar de ok · 2026-10-10 (ejecución del autor, JUnit conservado).

RED: `tests/test_knowledge_approved_retrieval.py::test_quoted_links_regression_same_identity_related_and_readonly[mixed-whitespace]` falló con AssertionError: show devolvió partial en lugar de ok · 2026-10-10 (ejecución del autor, JUnit conservado).

RED: `tests/test_knowledge_approved_retrieval.py::test_quoted_links_regression_unknown_or_malformed_fail_closed[unmatched-block]` falló con AssertionError: show aceptó comillas mal formadas y devolvió ok en lugar de partial · 2026-10-10 (ejecución del autor, JUnit conservado).

RED: `tests/test_knowledge_approved_retrieval.py::test_quoted_links_regression_unknown_or_malformed_fail_closed[mismatched-block]` falló con AssertionError: show aceptó comillas mal formadas y devolvió ok en lugar de partial · 2026-10-10 (ejecución del autor, JUnit conservado).

RED: `tests/test_knowledge_approved_retrieval.py::test_quoted_links_regression_unknown_or_malformed_fail_closed[extra-quote-block]` falló con AssertionError: show aceptó comillas mal formadas y devolvió ok en lugar de partial · 2026-10-10 (ejecución del autor, JUnit conservado).

El primer drill Windows terminó 12 failed antes de ejecutar producto por identidad del launcher venv. La corrección usa el intérprete base y mantiene PID/ppid/nonce estrictos. El segundo terminó 2 passed/10 failed: siete por clasificación del argv Git auditado en Windows y tres por corpus aprobado parcial causado por enlaces entrecomillados. Ambos resultados NO-PASS permanecen conservados. El probe stdlib bloqueó las cuatro llamadas antes de crear procesos y distinguió las dos consultas Git exactas de las dos ajenas.

La batería pública copia sólo quince inputs de producto declarados a un directorio pytest propio, sin configuración o memoria del consumidor. Conserva doce IDs, nueve grupos, Gold, barreras y límites; registra el argv auditado y exige corpus completo al reconstruir la caché. Está preparada, todavía sin ejecución ni aceptación Windows/Linux. Revisión independiente, cobertura oficial, qa-gate y documentación humana final siguen pendientes. No se reabre QA19 ni cambia ningún estado macro.


## Revisión de dos lentes — intento 1: Bloque20 (T-08/T-09/T-14/T-15) — dos gaps pendientes

2026-10-10. Lentes A+B de contexto fresco, fallback genérico por revisor nativo no disponible, sin override. Selector sobre el diff real: C=false/D=false, sin avisos. Scope oficial exit0:16 archivos en alcance, cero fuera/exclusiones del usuario/avisos. Ledger-lint:0 incoherencias/0 avisos. Fuente983 y diff sellados; ambos revisores comprobaron983 hashes antes/después. No ejecutaron pruebas ni producto. Se conservan QA19 y todos los criterios aprobados anteriores; no se cierra ninguna macro.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A1 | Important | El contrato no distingue el plazo de admisión de420s de una duración total | T-09/T-14/T-15 | Se aclaran admisión, barrera25s, finalización30s y recogida5s; pendiente validación independiente | Contrato:50 y harness:257/290/312/419 en fuente revisada. |
| AB1 (A2/B1) | Important | Resolver antes de rechazar oculta raíces/ancestros enlazados y destinos colgantes dentro de OWN | T-08/T-09/T-14 | Corrección y regresión del soporte sintético en curso; no se afirma fallo de backup de producto | protocol.py:34/132/184; ningún caso nuevo ejecutado aún. |

Fusión ROOT tras leer ambos informes completos y verificar sus hashes:0 Critical,2 Important,0 Minor; no hay rebatidos ni deuda aceptada. Los informes y límites quedan en la [evidencia del bloque](testing/memory-local-recovery-review-evidence.json). El fallo del auxiliar ROOT que esperaba una lista de exclusiones, en lugar del objeto vacío oficial, se conserva: scope había salido0; no fue un gap del producto ni una prueba ejecutada. Su finalizador verificó nuevamente fuente, diff y salidas oficiales. El intento de registro del revisor A dejó un directorio vacío; se conserva y no se usó para evidencia ni producto.

La revisión sigue acotada a tres intentos para este bloque. La corrección del parser mantiene su GREEN de autor separado; las doce pruebas integradas y los gates de cobertura/QA continúan pendientes. TDD n/a: registro de revisión y precisión documental del plazo; la regresión del protocolo debe observar RED antes de corregirlo.

Evento `gaps`, intento1, actor reviewer, sobre copia de ledger y configuración Jira sintética desactivada: exit0, ops vacías y cero escrituras externas. Stdout SHA `4670c8e70e35284c0d4d764edd464ad73279c3f0d9f2885623a3e6e7976fcdae`. No se leyó configuración consumidora.

### Correcciones preparadas para revisión 2

2026-10-10. ROOT adoptó el rechazo léxico de enlaces/reparse points antes de resolver raíces, hojas y ancestros en el soporte de backup/restauración sintético. No se añade un CLI de backup de producto. Se conserva la contención posterior y todos los oráculos/budgets. La precisión documental distingue el plazo de admisión de420s de la duración total. Ambos gaps esperan revisión independiente; la tabla anterior conserva el estado observado en intento1.

RED: `tests/test_memory_local_recovery_protocol.py::test_reject_path_alias_before_mutation[source-leaf]` falló con AssertionError: alias operation changed source/backup/destination/staging/link evidence · 2026-10-10.

RED: `tests/test_memory_local_recovery_protocol.py::test_reject_path_alias_before_mutation[source-ancestor]` falló con AssertionError: alias operation changed source/backup/destination/staging/link evidence · 2026-10-10.

RED: `tests/test_memory_local_recovery_protocol.py::test_reject_path_alias_before_mutation[snapshot-leaf]` falló con AssertionError: alias operation changed source/backup/destination/staging/link evidence · 2026-10-10.

RED: `tests/test_memory_local_recovery_protocol.py::test_reject_path_alias_before_mutation[snapshot-ancestor]` falló con AssertionError: alias operation changed source/backup/destination/staging/link evidence · 2026-10-10.

RED: `tests/test_memory_local_recovery_protocol.py::test_reject_path_alias_before_mutation[target-dangling-leaf]` falló con AssertionError: alias operation changed source/backup/destination/staging/link evidence · 2026-10-10.

RED: `tests/test_memory_local_recovery_protocol.py::test_reject_path_alias_before_mutation[target-ancestor]` falló con AssertionError: alias operation changed source/backup/destination/staging/link evidence · 2026-10-10.

Autor:6 failed antes/6 passed después, mismos IDs y bytes; doce junctions nativas creadas con exit0. Cada GREEN rechaza antes de mutar y mantiene idéntico el árbol completo de fixture. ROOT verificó124 artefactos y fuente983 intacta, JUnit, registros/argv/PID y árboles de ambos pases. JUnit RED SHA `b30090d9c71dfdccf03989975a059a925d9f254bf7a5fb85e124cdd81836d68f`; GREEN SHA `03f7822f233c60e8b3ae61eb61d43a173d7ba82a2edd9be48b5f78462aee9c59`. Este checkpoint no acepta las doce pruebas de recuperación ni QA global. POSIX sigue sin ejecutar; macros y QA19 intactos.


## Revisión de dos lentes — intento 2: Bloque20 (T-08/T-09/T-14/T-15) — sin gaps pendientes

2026-10-10. A+B frescos, fallback genérico sin override. Ambos informes completos y sus verificaciones se contrastaron por ROOT; fuente985 idéntica antes/después, FULL18 diff, scope/selector/ledger oficiales exit0 y cero avisos/exclusiones. C=false/D=false. Se conserva el traspaso R1 íntegro, sin reabrir aprobados, sin rebatidos ni deuda.

| # | Grado previo | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A1 | Important | Plazo de admisión ambiguo | T-09/T-14/T-15 | Corregido: contrato precisa420s de admisión y25/30/5 propios; no promete duración total | A2 contrato:50–55, harness:257/290/312/377/405/419. |
| AB1 (A2/B1) | Important | Alias oculto por resolve anterior al rechazo | T-08/T-09/T-14 | Corregido: lstat léxico de hojas y ancestros antes de resolve; seis regresiones dedicadas preservan árbol completo | A2/B2 protocol:34–49; test_protocol:102–156; RED/GREEN de autor conservados. |

Fusión actual:0 Critical/0 Important/0 Minor. Recibo de revisión SHA `5138f50080b1692824607fb4cb3639b23d656820f2f590c8164728a71b428608`. La aceptación integrada sigue UNKNOWN: faltan Windows/Linux, cobertura oficial y qa-gate. No se ejecutaron pruebas de producto durante revisión. Los estados macro y QA19 permanecen intactos. TDD n/a: esta traza de revisión.

Evento revision/intento2/reviewer en ledger OWN y configuración Jira sintética desactivada: exit0, ops vacías, cero escrituras externas; stdout SHA `1fe31f91295d3d44feca55cd302ee205d555208176ae133ce7bfb0d1095568c2`. Ninguna configuración consumidora leída.

### QA Windows aceptada; diagnóstico Linux abierto

2026-10-10. ROOT verificó la cohorte Windows congelada R2:528 IDs únicos,514 passed/0 failed/14 skipped. Los doce casos de recuperación y seis guardias de rutas pasaron sin skips. Se contrastaron fuente985, receta, revisión, JUnit, colección, setenta hijos, cinco cortes observados, fallo de manifiesto y auditorías contra los artefactos reales. Cobertura oficial del lector cambiado:212/235 líneas ejecutables y7/7 cambiadas, ambas por encima del umbral90% sin redondeo. El qa-gate oficial salió VERDE, exit0. Recibo Windows SHA `1926ac57e71cb1a25e8a9927dfc1b37c8e5d2bc6469bea0204256fed6a30f6b7`; no acredita Linux ni aceptación integrada.

La ejecución Linux con captura FD terminó antes de recoger casos por ENOENT al truncar el temporal de pytest; sus tres cohortes vacías y cleanup verificado se conservan. Una nueva ejecución con captura sys mantiene fuente, Gold y oráculos intactos. Su cohorte de recuperación terminó4 passed/8 failed: los ocho fallos ocurrieron al verificar la copia, antes de restaurar; las otras cohortes aún estaban en curso al registrar este checkpoint.

Un probe ROOT de sólo lectura dentro del contenedor propio confirmó124 archivos con bytes/SHA256/modos iguales y fuentes estables durante la observación, pero fechas de copia truncadas a segundos enteros. Recibo diagnóstico SHA `76c59b8757a411a24d5c08c939f74a3dcfda3b8a9a10f9117ab7c9cf4739eb1b`. Es una observación posterior de fixtures, no el inventario histórico ni una reproducción sobre filesystem nativo. Se conserva cada fallo y se prepara esa reproducción mínima antes de otra batería Linux. No se redondean expectativas ni se cambia el producto para ocultar diferencias de infraestructura. La aceptación integrada sigue UNKNOWN; QA19 y los dieciséis estados macro permanecen intactos. TDD n/a: registro de evidencia observada.

La ejecución sys terminó con528 IDs:516 passed/12 failed/0 skipped. Los510 vecinos pasaron; fallaron ocho casos de recuperación y cuatro guardias al preparar su copia, todos en el mismo oráculo de metadatos. Cobertura212/235 y7/7 cambió correctamente, pero no convierte los fallos en aceptación. Fuente985/proofs permanecieron idénticos y el contenedor propio fue retirado por identidad con ausencia verificada. El índice final del harness host falló después de esos recibos al acceder a un symlink nativo desde Windows; se conservan XML, logs, fixtures y fallo original sin afirmar un índice completo.

La reproducción mínima ROOT conserva exactamente bytes y modos: cuatro copias con fecha natural pierden su fracción de segundo en el bind Windows; doce copias en tmpfs nativo conservan el inventario exacto, incluidas ocho solicitudes de fecha controlada y doce de modo. No ejecuta producto ni sustituye pruebas de recuperación. Recibo SHA `d896c198e8a09fe7fc420b07337db1c69b52efabbaecf02b80f387192e3a7ddd`; cleanup exacto y ausencia verificados. Un primer guard del auxiliar exigió tmpfs en `Mounts`, aunque Docker lo declara en `HostConfig.Tmpfs`; se conserva el fallo previo a start y se reanudó el mismo contenedor OWN registrado tras verificar ambas representaciones. No hubo ejecución previa del probe ni reinicio de pytest.

La nueva receta privada conserva los oráculos y separa runtime Linux nativo de outputs durables del host. Requiere revisión independiente, precondición de filesystem y archivo completo verificado antes del cleanup. Su preparación no acepta el bloque ni modifica producto, Gold, QA19 o estados macro.

La receta privada V5 fue aceptada estáticamente por A+B y ROOT selló su adopción y la precondición real de filesystem. La ejecución nativa terminó con528 passed/0 failed/0 skipped: doce de recuperación, seis guardias y510 vecinos. El gate original salió1 por el recolector privado: su glob contó tanto el directorio real `memory-local-recovery0` como el alias symlink `memory-local-recoverycurrent` de pytest. El manifiesto archivado confirma ambas rutas. Este resultado original permanece NO-PASS; no se corrigen retrospectivamente su gate ni su verdict.

Antes del cleanup se verificó independientemente el archivo completo:8820 entradas,3999 archivos regulares y12031578 bytes, sin extracción y con grafo de enlaces/framing validados. Archivo SHA `1e2b9fee3fbbc3bd6315af5e3ef5cc4188da45fead2234ec90e0c1bbbb47346b`; manifiesto SHA `e7320fc98c4239fb3f65465f7170e0d332b58cbdcef5ee36d7b287742d9ad833`. Cleanup por identidad y ausencia verificados; fuente985 y pruebas de cierre intactas. Se prepara una verificación ROOT correctiva sobre esos mismos artefactos, con selección del directorio real y comprobación completa de hijos, antes de aplicar un nuevo gate oficial. No se repiten tests, no se cambia producto/Gold y la aceptación integrada sigue UNKNOWN.

### QA correctiva Linux y aceptación ROOT únicamente del Bloque20

2026-10-10. La verificación ROOT correctiva terminó exit 0 sobre los mismos artefactos terminales archivados, sin repetir producto ni tests: 528 IDs únicos, 528 passed/0 failed/0 skipped; doce casos de recuperación, seis guardias y 510 vecinos. Comprueba 70 hijos, cinco cortes, un fallo de manifiesto, diez ACK y nueve snapshots (ocho íntegros y uno alterado de forma controlada), además de seis symlinks POSIX de las guardias. Fuente 985 y proofs antes/después siguen exactos. Coverage oficial conserva 212/235 líneas ejecutables y 7/7 cambiadas, con umbral 90% calculado sin redondeo y sin inferir cobertura de hijos aislados.

El NUEVO qa-gate oficial usa input SHA `11ea4c501210e41ad1504e72100c8cd433656afa253369f1810e022b9fb287d4` y termina VERDE/exit 0; stdout SHA `7f6a9b5cac5255a9481fd8d3cb72ce8801b7106339ea632406950dfde4be1acc`. Recibo correctivo SHA `924702a0e036de50387c78720f8a539d074268eaf8ac98fd6a5addbfab08b072`. No cambia el gate 1, el verdict NO-PASS ni los UNKNOWN históricos del recolector original; tampoco los dos primeros fallos Linux o sus probes.

ROOT acepta únicamente el Bloque20 mediante recibo de publicación SHA `2908cafc8e0cc6be599b0b0ffe01d304f514f8dc172d598358a3de9bfd545761`, ligado a la aceptación detallada SHA `3ddeb5bf89562e3fced0e7edd6e9f66761822d1a118883870d364f9508a07e95`, R2/fuente 985 y los receipts Windows/Linux reales. Windows se retiene514 passed/0 failed/14 skipped; los 18 casos obligatorios pasaron sin skips en ambos OS, sin sumar cohortes ni repetir Windows. Los dieciséis estados macro y QA19 permanecen intactos; cierre global, tres hosts nativos, escala y eficacia comparativa conservan sus pendientes. La validación documental/metadatos final y commit/push de la rama siguen pendientes. TDD n/a: puente documental de resultados y aceptación, sin algoritmo público nuevo.

### Puente documental de publicación: enlaces históricos

El primer preflight de publicación terminó exit 1 antes de ejecutar los cinco gates estáticos. Detectó 28 enlaces históricos del changelog a directorios de conocimiento no versionados en la distribución (14 por idioma). Se conservan el fallo y su informe; no se leyó configuración ni corpus. Los IDs ADR/LES/GOT permanecen como referencias textuales, con una nota de distribución. Esta corrección documental conserva los siete archivos de código/test/Gold de R2 y no reabre QA19/QA20. La siguiente validación usa un OWN nuevo y el mismo auxiliar sellado; no se convierte el primer resultado en verde.

El segundo preflight terminó exit 1 en la preparación Git aislada, antes de los cinco gates oficiales. El escritor privado de alternates generó CRLF y Git conservó el carriage return como parte de la ruta de objects: los bytes terminan en 0d0a; recortar sólo LF no encuentra la ruta, recortar CRLF sí. Se conserva la salida terminal y el OWN completo. La corrección privada escribe bytes UTF-8 con LF literal y ruta POSIX, sin cambiar checks, producto, tests, Gold o receipts de QA. El gate de publicación aún requiere una ejecución nueva real sobre la fuente actual.

El tercer preflight terminó exit 1 antes de los cinco gates: el índice Git nuevo del OWN comparó archivos CRLF sin la conversión de texto. Una comprobación de status en ese mismo OWN, con core.autocrlf=true y configuración global/system NUL, devuelve exactamente los 18 archivos esperados; no modifica la fuente pública. La corrección privada configura la conversión exclusivamente en el Git local del OWN, conservando hashes crudos, filtros, exact18 y ROOT intactos. Los tres preflights originales siguen como fallos históricos, distintos de la QA de recuperación ya aceptada.

### Publicación observada de la implementación del Bloque20

2026-10-10. El cuarto preflight termina exit 0: lint de plugin, interop, evals estáticas, scope exacto de 18 archivos y ledger pasan sus cinco gates. Conserva 985 fuentes antes/después, siete archivos de código/test/Gold iguales a R2, prefijo de las dieciséis macros intacto y cero referencias de origen en los 18 archivos examinados. Lint conserva cuatro avisos existentes; no se ocultan ni se convierten en errores. Recibo estático SHA `6487a748212e007e205d814e9e0b631df269135b098e7947bb88fbca0e7688d1`; manifiesto actual SHA `d828550347c7947f6ecbcf0c88a930b6767c0531d4c1b73949d884f28c11596d`.

Commit de implementación `1f47fbf61261f4bb62282d0e9a8252a80d7bb6c2` publicado en `feat/catalog-capabilities`: push real seguido de comprobación remota devuelve ese mismo HEAD. Este cierre documental registra la primera publicación ya observada; su propio push se verifica posteriormente. Bloque20 aceptado y entregado; no declara cierre global, cambia estados macro, reabre QA19 ni acredita los tres clientes nativos, escala o eficacia comparativa. Las skills siguen aplazadas. TDD n/a: documentación de evidencia observada.

### BLOQUE21 — Caller portable de revisión visual y aceptación nativa

2026-10-10. Publicación del cierre documental del Bloque20 verificada en el remoto mediante HEAD `bd0ffb0a59f117cca30e968da4ceb0e4411a3783`. Es la base de esta entrega T-05/T-11/T-13/T-14/T-15, sin modificar las dieciséis macros ni reabrir QA19/20. Sigue el [contrato de caller portable](comparisons/plan-review-portable-caller-contract.md), conservando owner, estado y puerta plan-ok existentes.

El caller anterior sólo mostraba Bash y buscaba dueño/builder por separado. Las recetas nuevas permiten Bash/PowerShell con Python explícito real, seis raíces con precedencia, bundle común y rechazo de ambigüedad. Open precede su validación; el servidor conserva un handle separado. Receive, ack y view mantienen las validaciones de puerta, versión y consumo anteriores; no se interpretan comentarios como shell ni se inicia trabajo porque un proceso sale0.

RED: los diez casos iniciales fallaron por falta de recetas ejecutables únicas en el comando canónico, exit1/JUnit SHA `221fb016ab393890ca996e1413de52b41d77f9db8cca3378516a5ea5f321efb0` · 2026-10-10. GREEN: esos diez pasan tras el cambio, exit0/JUnit SHA `d327a0b5df17f42ed83ff5b68b63ac998c1f44ca73c37453b76b8e30e34197f6`. La ampliación a seis raíces y fallo de open termina24 passed/0 failed/0 skipped en Windows: doce Bash real y doce PowerShell, sin hosts nativos, navegador o modelos. JUnit SHA `beff581c108f8a291b0a0d39d87898c85ec5e534a7317a0b9a4e3c1200560e11`; el auxiliar conservó metadata expected10 del piloto, pero colección/JUnit reales tienen24, declarado sin alterar el intent original.

La [evidencia del caller](testing/plan-review-portable-caller-evidence.json) separa esta prueba con recorder sintético de owner/servidor/UI reales, carga/expansión por cliente y continuidad de agentes. Faltan congelación/revisión independiente, checks integrados y escenarios reales pendientes; no se suman etiquetas runtime a pruebas de shell para declararlos hechos. Scope previsto: comando canónico y sus dos proyecciones, test de recetas, documentación del panel/flujo y changelogs EN/ES, contrato/evidencia y esta traza. Las skills siguen aplazadas; T-16 y aceptación global permanecen abiertos.

## Revisión de dos lentes — intento 1: Bloque21 (T-11/T-13/T-14/T-15) — corregir retoma entre runtimes

Lentes A+B de contexto fresco, fallback genérico sin override de modelo; selector C/D false por diff real de14 archivos, sin avisos. Scope0/interop0 (58 archivos al día)/ledger0 previos; fuente988 y diff completos estables. A:0 gaps; B:1 Important. Report A SHA `54d558e1581b6f415972b8d9e68bda1332089c179fc333e63de1a4559c94d12c`, receipt `d086b732df62d8260377f48b1189c5c76c6419571271401d0afa7f1d83dfd11c`; report B SHA `2f6aeb6e7428c409cc97d39e979e73f5afde5c1d087de5bf60a1f894577c2a01`, receipt `d8f1909453f47627da5c4b67635407d1c5e47f8d6ffc95ba72ec9807c0f0dc8a`.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B1 | Important | Caller exige consumidor actual al reabrir recibo histórico | T-11/T-13/T-14 | Validar selección/puerta/versión; tratar registro de consumidor como histórico, sin exigir coincidencia en retoma | Reproducción ROOT: codex→claude-code y panel sin registro→caller mantienen mismo ID, versión completa/current y consumidor anterior/null. SHA `d48e5f7f607b7af74ce1a1fb40a32f8e30e85aa1a2c8ca4d7692e2f4365730ae`; owner intacto. |

La corrección cambia sólo la regla de validación del caller y su contrato/proyecciones, no actualiza el consumidor guardado ni crea otro registro de estado. La siguiente revisión verificará esta corrección; máximo3 intentos. La aprobación de QA, UI y clientes nativos no se deduce de esta revisión.

### Comprobación real de navegador del Bloque21

El dueño real abre una revisión sintética propia con vista completa/current y el builder real inicia servidor loopback con PID/handle propio. Un primer launcher privado termina antes de navegar porque stdin era EOF en pipes; conserva ese fallo y cierre de su servidor por handle. La nueva ejecución con PTY conserva handle vivo. Edge rechaza la navegación a ese servidor con `net::ERR_BLOCKED_BY_CLIENT`; el árbol visible dice «Microsoft Edge ha bloqueado esta página». Cero escenarios UI ejecutados, ninguna decisión emitida. Se conserva el bloqueo sin cambiar Host/Origin/CSP/capacidad ni protecciones. El servidor propio se detuvo por su handle y se verificó ausencia del PID; su exit1 por terminación explícita no se presenta como salida natural0. La pestaña de prueba fue cerrada; no se tocaron pestañas del usuario, servicios Docker ni corpus/configuraciones consumidoras.


## Revisión de dos lentes — intento 2: Bloque21 (T-11/T-13/T-14/T-15) — prueba dedicada pendiente

2026-10-10. A+B frescos, fallback genérico sin override; scope0/exact14, selectorC/D false, interop0/58 y ledger0. Fuente988 y diff completos idénticos antes/después. A2:0 Critical/1 Important/0 Minor; B2:sin defectos. El comportamiento de B1 concuerda con el dueño, pero la constitución:13 exige una prueba dedicada que nombre y compruebe cada gap corregido. No hay rebatidos ni deuda; las aceptaciones anteriores y macros se conservan.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A2-1 | Important | B1 figura corregido sin regresión dedicada de la regla actual | T-11/T-13/T-14 | Validador de apertura ejecutable sin estado; pruebas B1 sobre dueño real y transporte shell | Informes A2/B2 y hashes completos en la evidencia; pendiente revisión3. |

Fusión ROOT tras leer informes completos y contrastar hashes:1 Important pendiente. Se mantiene máximo3 intentos. La fuente R2 no se modifica; no se aprueban QA, UI, clientes nativos ni publicación.

### Regresión dedicada y validación ejecutable preparadas

RED: `tests/test_plan_review_open.py::test_B1_resume_validates_real_owner_historical_consumer[codex]` y `[None]` fallaron con «B1 requires executable opening validation», dentro de23 failed/0 errors/exit1 · 2026-10-10. JUnit SHA `d0f2af3a476de23200c01d3241cb38ebc679df697f39412c616fe39f2ed1a155`. Un primer intento conservado produjo22 failed/2 errors por IDs pytest de tamaño excesivo para rutas Windows; se acotaron los IDs del test, sin cambiar producto ni oráculos.

El nuevo `agent-kits/shared/plan-review-open.py` valida JSON acotado, envelope, selección, puerta, hashes/vista/current y devuelve sólo IDs/versión con approval_granted=false. No escribe estado ni cambia el dueño. Las dos recetas lo ejecutan antes de servir; PowerShell conserva/restaura OutputEncoding al transportar Unicode por stdin. La búsqueda exige dueño/validador/builder co-locales; no completa una instalación parcial desde otra fuente.

GREEN de autor:49 passed/0 failed/0 skipped Windows,23 de validador y26 shell (13 Bash/13 PowerShell). Los dos B1 ejecutan cuatro aperturas reales en fixtures propias: Codex→Claude y panelnull→Claude; conservan ID/versión/primerconsumidor y bytes del estado durante validación. Dos negativos shell impiden serve ante exit0 del dueño con otra puerta. JUnit SHA `726a0359cde74df563e06cef932a4e20aa69f6b085c0cb05121cdccff09bc2a9`. Fuente/receta/IDs conservados antes/después; cero modelos/hosts/UI. No sustituye QA integrada ni prueba obediencia de agente.

El preflight Linux R2 no ejecutó pytest ni creó contenedores: se detuvo antes del arranque porque cambió la fuente para corregir A2-1. Imagen QA20 exacta disponible, diagnóstico retenido sin afirmar PASS/SKIP Linux. El siguiente ensayo debe corresponder al bundle nuevo. Contrato/evidencia/descriptores se actualizan juntos; exports, revisión3, checks integrados, UI/carga/continuidad nativa y push continúan pendientes.


## Revisión de dos lentes — intento 3: Bloque21 (T-11/T-13/T-14/T-15) — límites JSON pendientes

2026-10-10. A+B+D frescos, fallback genérico sin override; scope0/exact16, interop0/58, ledger0 y fuente990/diff íntegros. C=false; D=true por heurística regex-en-bucle, descartada por D con evidencia de compilaciones fuera del bucle. A3 acepta A2-1 y conserva B1; B3 introduce1 Important/1 Minor, D0. ROOT leyó los tres informes completos, verificó hashes y reprodujo ambos casos. No hay rebatidos ni deuda.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B3-1 | Important | 1e999 llega como infinito en metadata ignorada y valida ok | T-11/T-14 | parse_float comprueba finitud antes de aceptar el número | Probe real:782 bytes/exit0/statusok; pendiente validación correctiva. |
| B3-2 | Minor | JSON muy profundo termina sin envelope | T-11/T-14 | RecursionError devuelve unavailable/exit2, conservando rechazo | Probe real:12000 niveles/24001 bytes/exit1/RecursionError, sin aprobación ni serve. |

La reproducción ROOT sobre R3 intacto y los informes quedan ligados por SHA en la evidencia. El primer probe de2000 niveles devolvió unavailable; se conserva el fallo de su assert privado, sin convertir esa entrada en una reproducción positiva. La reserva siguiente falló por sintaxis del auxiliar antes de ejecutarse; un OWN nuevo conservó intenciones/terminales de los dos probes reales. No hubo mutación de estado, modelos, hosts ni UI.

### Decisión del orquestador tras el límite del ciclo inicial

El ciclo inicial concluye sus tres intentos con B3-1 pendiente y no se declara aprobado. Bajo la delegación del usuario para decisiones técnicas y revisión independiente, ROOT decide continuar con un ciclo correctivo acotado a un solo pase A+B+D sobre estos dos casos reproducidos. Será ciclo2/intento1, cuarto pase acumulado explícito; no reinicia ni oculta los tres resultados anteriores. No reabre criterios aprobados, QA19/20, macros ni catálogo de skills.

RED: `tests/test_plan_review_open.py::test_B3_json_boundaries_fail_closed[overflow_positive]`, `[overflow_negative]` y `[depth]` fallaron en la implementación R3,3 failed/23 deselected/exit1 · 2026-10-10. JUnit SHA `3b84c5758629a3a61f37149f3414dfee932fc4d72df8a7b8c33a7f11761bf77e`. GREEN de autor tras parse_float finito y captura RecursionError:52 passed/0 failed/0 skipped Windows (26 validador/26 shell), JUnit SHA `87f4f2f00852a1a37dc95fa6ba7bd14b64365c575efffa032b09c105e8ae23ab`; mismos IDs/fuente/fixtures y cero modelos/hosts/UI. La revisión correctiva y los checks finales siguen pendientes; no se publicará como aceptado con un Important abierto.


## Revisión de dos lentes — intento 1: Bloque21 · ciclo correctivo 2 (1 de 1; cuarto pase acumulado)

2026-10-10. Cuarto pase acumulado explícito después de los tres intentos iniciales, cuyo historial permanece intacto. A+B+D de contexto fresco, fallback genérico sin override; C=false y D=true por la misma señal heurística, descartada con evidencia estática. ROOT leyó los tres informes íntegros y verificó sus SHA, recibos y fuente990 antes/después:0 Critical/0 Important/0 Minor. B3-1 y B3-2 corregidos y aceptados; B1/A2-1 conservados. Sin rebatidos ni deuda.

Lente A: informe SHA `2d691b32cdfb5d0054d501cc8c10c947948f2866280dfb3f4f85f61222dce848`, recibo `f9c7a3f15055df87bcffb11895eab3eafafdca024ae961cfdfe8ec7153b0e5ca`.

Lente B: informe SHA `b5e2fab162dadb03f6a353f6cdc4b1903f04c00f180bfd1000584703ad85dde3`, recibo `9aec586ac7c1a472744cff67247823a8df2616127fb16fa232cf99ca5f031361`.

Lente D: informe SHA `7d518b2502adef0862adbc6472037640569174e7309c0434c7e751cf57f77f82`, recibo `3f99402314f52a9959e36450f7295d500acb87c6ab23aaabf98b8e7f08e46033`.

Fusión ROOT SHA `8ead037e75b9bc9e4ec74557a6e17d47c1fb0bd89415ccbc97379a83a4d58b4b`; fuente de revisión `edfef7a43df7d19115bd935e804455f9333964df7506c16b7f07391c49401bd9`. Esta aceptación corresponde a revisión del código congelado; no acredita QA visual, clientes nativos ni cierre global.

### Aceptación acotada de Windows

ROOT verificó los siete inputs del GREEN final contra la fuente revisada y los52 casos únicos de JUnit, más una colección independiente sin ejecutar de nuevo las pruebas. Resultado52 passed/0 failed/0 skipped;26 del validador,13 Bash y13 PowerShell. El qa-gate oficial aplicado a esos resultados reales convertidos terminó exit0/VERDE, SHA `a2b547b43ddf08c5879ee0361450fe77ad940fda64ba98e77a728a63a32d6c4e`. Recibo de aceptación SHA `f999c30eb5aa789a2df726b0740180e31caed6ed8ba82ea2dee7f9dc6166ffd2`. La conversión es de pruebas unitarias/shell y no se presenta como Playwright o aceptación de navegador.

El ensayo Linux del bundle final está en preparación; no se acredita todavía PASS ni SKIP. Los checks estáticos previos pasan con fuente990, exports58 y53 enlaces válidos; el lint de aquella copia aislada emitió5 avisos, uno por no resolver Git en PATH y recurrir a os.access para hooks/hooks.json. El índice ROOT confirma modo100644; los checks finales expondrán Git en el entorno propio para medir ese criterio correctamente. No cambia producto para ocultar el aviso. UI real de Edge, carga/continuidad nativa, comprobaciones finales y publicación permanecen pendientes. No cambia ninguna de las16 macros ni QA19/20, y el catálogo de skills permanece aplazado.


### Aceptación acotada de Linux y comprobaciones finales del Bloque21

Linux final:39 passed/13 skipped/0 failed/0 errors, pytest exit0. Los26 casos del validador y13 Bash pasan; los13 PowerShell se omiten por ejecutable ausente y no acreditan aceptación de ese shell en Linux. ROOT contrastó190 artefactos por bytes/SHA, los52 IDs de colección/JUnit, siete inputs ligados a GREEN/revisión y43 hijos registrados terminados. Sólo el contenedor propio fue retirado y su ausencia exacta se verificó. JUnit SHA `2520a688498ce712cb21ad6307905473b0cebefa9fe1039a564d0f9a814da38f`; recibo ROOT `108959646c1948a1ef1481392454555f1bd36d46d2f9748db725c65982537035`; qa-gate oficial exit0/VERDE, SHA `bb9859f3985b0465d212264c4d05bb2d2de3b8c1c77129a0b7bbd242a39cac62`. No se ejecutaron de nuevo las pruebas ni contenedores al verificar.

Se conservan dos fallos de auxiliares privados: el primer check estático intentó crear un directorio de entorno ya existente; el primer verificador Linux esperaba la frase Docker No such object y el artefacto real decía No such container para el CID exacto. Correcciones sólo del transporte/verificador, sin cambios en producto/oráculos ni repetición de pruebas. Los checks estáticos recuperados pasan:scope0/exact16, exports0/58, ledger0, evals0 y lint0 errores/4 avisos,53 enlaces válidos y16 estados macro sin cambios. La diferencia respecto a los5 avisos iniciales es la resolución real de Git para comprobar el modo100644 de hooks/hooks.json.

Checkpoint estático fuente SHA `1002b0c7c74b3ee83d636f65fffa1f5c4b8957a3e2717fef4ecd193fddd764bb`; recibo `f475a5c14b39222918b809afd818b5099c2aace4a1e495c0db23cce03a16b164`. Código, recetas, tests y proyecciones idénticos a la revisión correctiva; sólo tasks/evidence añaden resultados observados. Se acepta esta entrega portable, sin aceptar UI de Edge, carga/continuidad real en tres clientes, QA global o tareas macro. Se verificará el cierre documental y el push en la rama autorizada antes de registrarlos como observados.


### Publicación observada de la implementación portable del Bloque21

ROOT observó y verificó el push normal del commit `b5932849649db8294bdbe9053c64ae53d496dd2a` a feat/catalog-capabilities; HEAD remoto coincide. Recibo SHA `b7829dce6afb8f0f8d6a3bb99897da5aa177bbcebd1803fbb0bae3a034cb5c33`. Antes de publicar, los cinco gates estáticos pasaron sobre fuente990 y los16 archivos explícitos:scope, exports, ledger, lint y evals;53 enlaces válidos, código/proyecciones idénticos a revisión y estados macro conservados. Fuente final SHA `aa1826dc6a5ca833a405908b6037aa4aa5e9cc2367c4e568ed729aea2e7cd131`; recibo estático `37799fca2384e1b8dbcb4f19c1007cf549ef3e9a0a38514e65e51830cc137d9a`.

Esta publicación entrega la validación de apertura y las recetas portables aceptadas en Windows/Linux; no cierra UI real, carga/continuidad de agentes en tres clientes ni el objetivo global. El navegador Edge conserva su bloqueo sin escenarios aceptados. El cierre documental toca sólo tasks/evidence, pasa sus comprobaciones propias y se publica después de observar la implementación; su propio push se verificará tras ejecutarlo. QA19/20 y16 tareas macro permanecen iguales; skills aplazadas.

## Transporte nativo de comandos — Bloque22 en preparación

2026-10-10. T-08/T-09/T-11/T-14/T-15 conservan sus estados. El catálogo de nuevas skills permanece aplazado; los adaptadores generados sólo transportan los workflows de `commands/`. El [contrato](comparisons/codex-command-transport-contract.md) conserva dueño, puertas y argumentos del mensaje invocante.

RED: `tests/test_codex_command_transport.py` falló en sus cinco casos iniciales contra el exporter sin modificar: manifiesto con una sola raíz, adaptador ausente (dos variantes), generación de prompts personales y retirada ausente. Resultado5 failed/0 errors/exit1 · 2026-10-10. JUnit SHA `7b4e9b10233e4793c84416dc51be0d5d28e1369695d54f389af56bb7da8c6d5e`; fuente992 antes/después idéntica, SHA de manifiesto `3bc7de62bd95649c7e73bae0c1029c4dd876c0ab2de33cb94937c086a3fe2b35`. Cero modelos/clientes nativos en este RED. Se añaden negativos de nombres, colisión por nombre declarado y retirada precisa antes de implementar.

La prueba nativa aislada de Codex0.161.0 descubre ambas raíces del plugin desde su caché, con pluginId propio no nulo y SHA iguales a la fuente. El primer filtro privado esperaba nombres sin namespace y dio falso negativo; el reanálisis conserva los mismos frames sin repetir Codex. El nombre real incluye namespace del plugin. Esta observación no acredita inyección, lectura de la referencia ni ejecución del workflow; la verificación ROOT y evidencia pública completa siguen pendientes.

RED ampliado:12 failed/0 errors/1 skipped/exit1,13 casos totales · 2026-10-10. Los negativos de nombres, colisión por `name` declarado y retirada de adaptadores fallan en la fuente previa; el caso de symlink se omite por permiso Windows y no acredita ese guard. JUnit SHA `77df7b04df03eae9ccf99ee11fdc6fdb3867b5c5f8d5c488a36bbd935260c4ce`; fuente992 idéntica antes/después, SHA `0129c6235f5de849a3f60d05c15d2271de55035922d7cba3616d101dfe889165`. ROOT verifica por bytes los cinco pares fuente/caché y los tres frames de entrada/salida de discovery nativo. No ejecuta otro Codex para reanalizar. Implementación y GREEN pendientes.

GREEN inicial de exporter/transporte:47 passed/0 failed/1 skipped Windows; JUnit SHA `1c9290e6f4ad7c073006cd4f6d1687e7e29ea2d174805b78b87f6dfce99c3511`. Generación/check aislados exit0; se adoptan88 outputs,45 archivos de adaptador nuevos y15 prompts antiguos propios retirados con bytes/hash/cabecera verificados. La documentación ES/EN corrige invocación con namespace. Un ajuste posterior cualifica también las skills canónicas en los preámbulos; requiere GREEN final y regeneración antes de revisar.

RED del instalador:3 failed/0 passed/exit1, antes de modificar providers/install; JUnit SHA `898f9ec7a31293f0f65aaa6124646546d0ee6450687e480fce09699a212a13f1`. La primera GREEN falla porque faltaba el árbol generado aún no adoptado; se conserva sin cambiar el oráculo. Tras adoptarlo pasan3/3, más11 regresiones seleccionadas. La migración conserva bytes de prompts globales anteriores y retira sólo su propiedad del manifiesto, sin barrer el home; no existe hash antiguo fiable para eliminarlos. La verificación ROOT y revisión fresca siguen pendientes.

Inyección nativa de fixture observada y verificada por ROOT: una petición incorpora el cuerpo literal completo y Unicode/dólares, ausentes del stdin. Cinco frames enviados,14 recibidos, un POST al proveedor pasivo propio400, cero inferencias/toolcalls, turno failed y recursos propios terminados. El primer ensayo se detuvo por un warning de metadata de modelo sintético; el segundo admite sólo ese warning exacto en OWN nuevo. Se conservan además dos fallos del verificador privado ROOT (Unicode por stdin y ruta de instructionSources), corregidos sólo en el oráculo sin repetir Codex. [Evidencia acotada](testing/codex-command-transport-evidence.json): no acredita carga del adaptador real, lectura de referencias, obediencia, workflow, UI o QA global. Las16 macros y skills aplazadas se conservan.


## Revisión de dos lentes — intento 1: Bloque22 (T-09/T-11/T-14/T-15)

2026-10-10. A+B+D de contexto fresco, fallback genérico sin override; C=false/D=true. Fuente1023 y diff73 conservados por los revisores, exports88 idénticos. ROOT leyó los informes completos y verificó sus SHA y recibos:1 Critical/1 Important/0 Minor. No hay rebatidos ni aceptación.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Critical | B-01: cambio de CODEX_HOME conserva claims externos y uninstall borra bytes personales | T-09/T-15 | Corregido y aceptado en intento2: liberar claims externos con límite del bundle explícito | RED1/GREEN1 y regresiones12; conserva históricos editados y ownership interno |
| 2 | Important | A22-1: índices ES/EN muestran invocación antigua no instalada | T-11/T-15 | Corregido y aceptado en intento2: invocación nativa cualificada en ambos índices | RED6P2F/GREEN8P de los ocho documentos con nombres resolubles |

RED dedicado B-01: `Codex command adapters: B01 ...` falla en la implementación revisada:1 failed/exit1, JUnit SHA `ead5bbd5408e4d202550f1ec1b0a9223925f870268cc9593fc33386b7735d22a`. Prueba con upgrade/uninstall reales, homes propios A/B y CLI simulado; cero modelos/consumers reales. Producción permanece idéntica tras el RED.

Informes A/B/D SHA: `4f3754e2726240f7a37926cc11c531717a3f0b5beef4e7dc8336e216c841961b`, `f23389791daf6b4addfc93ccbf0068bb76a8db25214542afd48a70154c80340e`, `6ec6b19fef5283764adf1f4cd69f1f52970f6b6e49077695b19b03d7a805d8ec`. Fusión ROOT SHA `5980e7e457d6bece289fcf4f905568eeaf80ebac856e1d6d75c84dfd489daa7f`. La siguiente revisión será intento2 de3; no se publica con Critical/Important abiertos ni se cambian las16 macros.


RED dedicado A22-1: las ocho páginas se comprueban contra adaptadores realmente generados;6 passed/2 failed/exit1 en la fuente revisada. Fallan exclusivamente docs/README.md y docs/en/README.md antes de corregirlos. JUnit SHA `5fd16259ba62f92fb7a6ae26473fd1e141f07569ed37d29bf629d51fdb70b006`. Las correcciones ES/EN sustituyen los ejemplos antiguos por invocación con namespace nativo; GREEN y revisión correctiva pendientes.


GREEN dedicado A22-1:8 passed/0 failed/exit0, mismos ocho documentos/IDs y adaptadores generados; JUnit SHA `8204900710d109246c01c74da5a3101386b6c3880e07e42d36b2f7c00558c67d`. Ambos índices ES/EN corregidos. Esta prueba de documentación no sustituye la revisión fresca ni prueba ejecución nativa del comando.


GREEN dedicado B-01:1 passed/0 failed/exit0; JUnit SHA `7fac2f3687f93361b8c5fc0c1e8806a2d59e13c9efccba77437765fb97bd4da5`. Regresiones pertinentes del instalador:12 passed/0 skipped/exit0, JUnit SHA `14a4d2f6ce84435b80a58de7f5bcb85c1cd88f8f04401c8eb8c4c3def92b8288`. ROOT verifica todos los hashes de artefactos y los tres inputs contra producción, recibo SHA `c65876705608025786591df932737e41d3834eb1db3e7bba15d74acc341cb9a1`. El límite del bundle es explícito y los registros externos ambiguos se liberan sin leer ni borrar sus bytes; la prueba conserva prompts históricos editados y la desinstalación interna. La revisión2 y QA congelada siguen pendientes.


## Revisión de dos lentes — intento 2: Bloque22 (T-09/T-11/T-14/T-15)

2026-10-10. Segundo pase de un máximo de3; A+B+D frescos, fallback genérico sin override. C=false/D=true. ROOT lee tres informes completos y verifica hashes/recibos/fuente1023/diff75 y probe directo:1 Critical/1 Important/0 Minor. B-01/A22-1 corregidos y conservados; no hay rebatidos ni aceptación.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Critical | B22-2: uninstall directo legado elimina prompts externos editados | T-09/T-15 | Corregido y aceptado en intento3: liberar claims antes de contar/borrar/podar | Probe real exit0/legacy_exists=false y fuente intacta |
| 2 | Important | A22-2: cabecera y tabla nuevas no las leen brief/Jira | T-11/T-14/T-15 | Corregido y aceptado en intento3: cabecera canónica, seis columnas y # numérico | Header no casa; tabla4 columnas/ID no numérico omite ambas filas |

El borrado directo era previo al diff; B22-2 incumple la nueva garantía contractual sin precondición de upgrade. A22-2 se limita a la nueva sección Bloque22; aviso histórico Bloque21 conservado. Informes A/B/D SHA `9c905b549e4e7cbaa56462a3dc65ce5dd5e19591d6766daa22054dc46abd3a85`, `0eacf79739b78a83091e04168d1a0448fc2d62980aae469b96a4c4234a19f16e`, `8e48460ac420b2a653a68f0353c378ec96bc965814499513912e0d6b3ee3a809`; fusión ROOT SHA `4a53d226fef1b64e52aa5385c699c25a679e02a906f951d59e6bacdedaa4b0ca`. Se conservan dos fallos del verificador privado: ruta relativa de recibo y conteo del padre Node frente a hojas JUnit; corregidos sin repetir pruebas ni alterar producto.

RED dedicado B22-2: project y user fallan al conservar bytes externos tras uninstall directo. JUnit:2 hojas fallidas; Node:3 fallos contando padre+dos subtests; exit1, JUnit SHA `4afdeacbcb9c29dfea18fa8cdac6b8313906fe02b9795f5b8fcad8dfabc66800`. Dry-run previo conserva bytes/manifiesto. Producción intacta; GREEN y revisión3 pendientes. QA final no iniciada; publicación pendiente.


RED dedicado A22-2:2 failed/exit1, JUnit SHA `fe13d69cae6a8968b0bdcf7f784f91e54cbd274f030b63cc60c74ba38a6b6f4d`. Primer caso demuestra cabecera invisible; segundo corrige sólo la cabecera en memoria y demuestra las filas omitidas. Ambos usan el parser canónico real y la sección nueva del ledger, sin reabrir avisos históricos. Corrección: cabecera canónica, seis columnas y # numérico con tarea/evidencia; estados previos aceptados en intento2 conservados. GREEN pendiente.


GREEN dedicado A22-2:2 passed/exit0 sobre el mismo parser canónico, JUnit SHA `0ea9896810368729c7cd12070673a0ab4f4cab3a60d65eaa12afe62b2940ac1b`. La cabecera y las dos filas con tarea/grado/gap vuelven a ser consumibles; el contador máximo3 y veredictos previos permanecen. GREEN dedicado B22-2:2 hojas JUnit/3 contando padre Node,0 failed/exit0, SHA `47d6601824d49dc60e3bc271f9c0a6df09a693a834363ad0af4527cfb9b07b27`; regresiones seleccionadas:14 hojas JUnit/15 Node,0 failed/exit0, SHA `a7ea7ed816ec702ec66be1d0c19e0f1d96804c2afd0d16e62db6b0abe0e49954`. ROOT verifica hashes de todos los artefactos y tres inputs, recibo SHA `dc277409e329e459fac1a97bc10a1f3ee0bf364b671760d6cc36db106cb8f216`. El filtro se aplica antes de contar dry-run/borrar/podar y no lee ni borra bytes externos. Revisión3 y QA congelada pendientes.


## Revisión de dos lentes — intento 3: Bloque22 (T-09/T-11/T-14/T-15)

2026-10-10. Tercer pase de un máximo de3; A+B+D de contexto fresco, fallback genérico sin override; C=false/D=true. ROOT leyó íntegros los tres informes y verificó sus recibos, todos los hashes declarados y fuente1023 intacta:0 Critical/0 Important/0 Minor. B22-2/A22-2 corregidos y aceptados; B-01/A22-1 conservados. Sin rebatidos ni deuda. Se acepta exclusivamente el diff75 del código/documentos congelados, no la continuidad nativa, UI, integración global o tareas macro.

Informes A/B/D SHA `68105e3944d3d34489c522fd7da9852c807881d98299d770c1d1c23199a33e9f`, `89b2e64ebf9d39bc99d6c11a608c9302bf8127b365200465ac57df1abc502fe0`, `38f65fa8295b85368bff1fb958bd02cfcfe1c8854333608e0171e990f82897f5`; recibos `ffa913cf796507a6fb8a849f161ef1dc31c7f4a0aa0bcace3e8b78c79857f8eb`, `16bb8e8cae451b3ab2f906cf76b55fd0b423a7422efb6ad4788d75d7328eb3f8`, `433c9d1d12e7868c1646990708ed503d8d70b03e90dd0efc2d9dfe986dc1d620`. Fusión ROOT SHA `a74bd1c4543d815857f85e8d02d0ad36345b4e54f6f07a958c7ec24d709d050a`; fuente `d0b95ef1f9166a71e509db77ac95efdf63094af9e098b464782d257460d49539`, diff `b762855ccefdf09db2da0e337c1b6f9cff3c77f4aa532c8b70c1455761354914`. Export propio A exit0/88; probe independiente B project/user conserva bytes externos históricos/actuales/personales y limita dry-run/retiro al bundle. Los fallos privados de conteo rename/path, import aislado e inventario por cwd se conservan; se corrigieron sólo auxiliares propios, sin repetir probes ni cambiar producto.

### QA congelada acotada del Bloque22

Windows:57 passed/1 skipped Python y14 hojas passed/0 skipped Node;0 failed/errors, ambos procesos exit0. JUnit SHA `cc9dbcfb05d8ee3dbd4d783394c78c1708b659584d7df97403c8b8a8e5761338` y `d6fa184f329dbe00244a5da3e27b58e4e4ea62f158cf5eb41160064c11d906ba`. El skip de enlace simbólico por permisos no acredita ese guard en Windows. Linux:58 passed/0 skipped/failed/errors, exit0; JUnit SHA `c8463b73636961b92f17a13ac41408cb1d351b1c67ef53b5b1a73678c834993d`. Incluye el caso de symlink; no se ejecutó el instalador Node en Linux. ROOT verificó los58 IDs Python iguales entre plataformas, colección real y reportes por caso Linux, fuente1023 intacta y procesos registrados terminados. El contenedor exclusivamente propio, sin red, se retiró y su ausencia exacta se observó; no se tocaron servicios del usuario.

qa-gate oficial sobre resultados reales convertidos:Windows VERDE/exit0 con71 passed/1 skipped, SHA `b35b3e5ba6f4481dc0b240f53654c35e0db4e0bff599107a2614c5041c3d114d`; Linux VERDE/exit0 con58 passed/0 skipped, SHA `f56efab6c9168c38397da371da99ac516ae7461d77b701f2668fb7b9b743eac5`. La conversión JUnit es de pruebas unitarias/instalador y no se presenta como Playwright ni aceptación de navegador. Recibo de verificación ROOT SHA `4149b37ddbd52a921cb47ad50da5756683c1cce8b60f58d107fffc6c0c7a0259`. Se conserva el fallo inicial del verificador que exigía un log de subprocess opcional: no hubo eventos de subprocess en las dos pruebas Linux; se corrigió únicamente el lector, sin repetir QA.

Código, tests, recetas y proyecciones quedan ligados a revisión3. Se preparan comprobaciones documentales finales y push en la rama autorizada. Carga del adaptador real, lectura completa de referencia, workflow/plan UI y continuidad en tres clientes siguen pendientes; no se inventa cobertura ni aceptación global. Las16 macros, QA19/20/21 y catálogo de skills aplazado se conservan.


### Publicación observada del transporte de comandos del Bloque22

ROOT observó el commit `c03f5ff34aa65881998758546ccbabb46921f7b3` y su push normal a feat/catalog-capabilities; HEAD remoto coincide. Recibo SHA `de8363ac00e57aa01195b3f5247e04b595ae49696e9d1529424ed972d2344520`. El índice incluyó sólo las90 identidades de ruta del diff75 revisado; el índice quedó vacío y los1023 hashes públicos permanecieron iguales. Código/tests/proyecciones son idénticos a revisión3; sólo tres documentos registraron revisión/QA posteriores. Fuente final SHA `e34c9b5ee649c256374b90464eeefbc07a939950a63fda359754294f95610cde`, recibo estático `e49eacd9e43901e985afb7d1acfb70207e0f48251d34909e5e76d408b8dd7f40`:scope exact75 sin avisos/exclusiones, exports88, ledger0 incoherencias/1 aviso histórico, lint0 errores/8 avisos conocidos y evals0 (52 archivos/188 casos de validación).

Checkpoint documental independiente conforme:18 enlaces nuevos/cambiados válidos,16 estados y prefijo histórico QA19/20/21 intactos; recibo SHA `b6c5cd3f806b3a6739140dc0dc25079e2e675d13ffd9f0693bb35eb436210441`. Se conservan fallos privados de regex/reparación y comparación de modo: la copia de sólo archivos había perdido100755 de install.mjs, pero ROOT conserva el modo anterior verificado y todos los blobs coinciden. Dos pushes iniciales exit128 por autenticación no disponible en el entorno aislado permanecen registrados; el push normal final usó el helper de credenciales GitHub CLI ya configurado, sin leer/imprimir tokens ni cambiar configuración/iniciar sesión. No se cambió producto ni se repitió QA.

Esta publicación entrega los15 adaptadores generados de comandos Codex y preserva prompts externos durante actualización/desinstalación, incluidos homes históricos. No incorpora nuevas skills del catálogo. El cierre documental de tasks/evidence registra únicamente hechos ya observados y se publica con comprobaciones propias; su push se verifica después. Carga real del adaptador, lectura de referencia, workflow/UI y tres clientes siguen pendientes. No cambian las16 macros ni QA19/20/21 y no se concede aceptación global.

## Bloque23 — Curación única de memoria (T-07/T-08/T-11/T-14/T-15)

2026-10-10. Trabajo en progreso desde HEAD publicado `3be4821`. Tres auditorías
de contexto independiente sobre fuente pública congelada1023 identifican dos
contratos activos de promoción y una contradicción de ownership de candidates.
ROOT leyó informes completos: contratos24 archivos, productores deterministas y
callers181 inputs; integridad del snapshot sin diferencias. Son auditorías
estáticas, no pruebas nuevas ni aceptación del producto.

Informes SHA `5c64593e86eec597fc560c122d8ee755dcec6283515871030dca7e4b4c1d4f5f`,
`6ca340e64d6a29a64b69587d8a6b129bf069c33ffffd227a0d3f4b89ee32a18e` y
`5ae884143c56c9e902f269c508b7141e1ed83d1e9fcd0aed8da59be2a0579494`.
La [curación única](comparisons/memory-curation-contract.md) fija corte
prospectivo, proponentes/decisor/persistencia, SHA obligatorio, recuperación y
handoff tardío de retro. No migra ni borra memoria del consumidor ni añade skills.
Servicio, RED, actualización de todos los callers, revisión y QA pendientes.
Las16 macros y las aceptaciones anteriores permanecen; objetivo global activo.

RED: `test_memory_curation_scope.py` falló con siete AssertionError el
2026-10-10: candidates/journal entraban en el alcance y en staging aunque
no estuvieran curados. Fuente anterior congelada + test nuevo,7 failed/0
passed/exit1; JUnit SHA `50e4cf6daf12b3749c2f1edf16a2685c1af96571d7a8336fc6fccce3acbf8581`.
Se probaron también mayúsculas de Windows y conservación de approved/originales.
Corrección mecánica posterior al RED: exclusión incondicional de ambos árboles
en el resolvedor común y defaults; GREEN/regresiones en curso, sin publicación
real a Confluence ni datos del consumidor.

GREEN de alcance Confluence:32 passed/0 failed/exit0, incluidos los7 casos
nuevos y25 regresiones. Dos ejecuciones anteriores conservaron fallos de
infraestructura: faltaban Node y después Git Bash en PATH aislado. Se corrigió
sólo la receta, manteniendo fuente y oráculos; no se ocultó fallo del producto.

RED: `test_knowledge_curation.py` falla con78 errores de capacidad ausente
(loader lazy con assert, sin fake writer); los3 casos nuevos del puente fallan
porque todavía persiste directamente y no delega. Cohorte total:3 failed,
25 passed,78 errors/exit1 el2026-10-10, antes de crear el servicio o cambiar
el puente. El rojo incluye el requisito de representación corregida de
needs_changes ligada al SHA original. Implementación autorizada tras esta
evidencia; las pruebas de enlaces siguen sujetas a permisos OS y nunca
acreditan un sandbox nativo universal.

Primera ejecución de implementación:203 passed/2 failed/2 skipped/0 errors,
exit1. JUnit SHA `6b74e918ea9398037a8d331f281f2443928831e52c4bda7b3c47f5d3dfa42aa0`.
La recuperación en `prepared` detectó una representación distinta: el registro
JSON ordenaba metadata y el render inicial conservaba su orden de inserción.
La corrección ordena las claves de frontmatter antes de renderizar; no debilita
la verificación SHA. El puente conservaba la colisión, pero había perdido el
diagnóstico humano español; se traduce `name_already_reserved` sin cambiar su
test. Ambos fallos y la fuente congelada se conservan. Los dos skips corresponden
a enlaces simbólicos de archivo no permitidos en este Windows, no a guards
validados. Nueva ejecución sobre otra fuente congelada en curso; no hay
aceptación, commit o push del Bloque23 todavía.

GREEN posterior a ambas correcciones:205 passed/0 failed/0 errors/2 skipped,
exit0 en las mismas cinco suites, sobre fuente congelada nueva (manifiesto SHA
`d19748d7aac530a84ee28e851f16ae7219ef54caecd16523ff98f98a7429678d`).
JUnit SHA `97e5760ec4ac046c2972f8c077ce8b56608dd6f1d71d0ca38076581af09cc733`.
Proceso exacto observado terminado. Incluye recuperación prepared, diagnóstico
del puente, gate existente y alcance Confluence; conserva los dos skips de
enlaces de archivo. Esta evidencia unitaria acotada no sustituye revisión
fresca, QA final Windows/Linux, regeneración ni aceptación en tres clientes.

RED: `test_journal_curation_handoff.py` falló con tres AssertionError el
2026-10-10 sobre el journal anterior congelado: candidatos, entradas e índice
todavía dirigían a promoción legacy o revisión/retro como decisor.3 failed/0
passed/exit1; JUnit SHA `bfd69bfc9177e36432d6e9e663c3f2843c597018bfd8ebe641681a7aa032a4d5`.
Los oráculos conservan datos, estado propuesta, evidencia y ausencia de escritura
en candidates/approved. Corrección del texto generado posterior al rojo.

GREEN journal:173 passed/0 failed/10 skipped, exit0. Los tres casos nuevos
pasan junto a la suite anterior de journal; JUnit SHA
`721d01eb14b0e9b49f1d91c86d325eb82591be834a9059eb9b16746480a58eb6`.
Los skips no acreditan sus escenarios Windows. Sólo cambian orientación textual
y comentarios del journal; estados, extracción, fuentes y operaciones conservan
su contrato. Regeneración y revisión fresca del conjunto pendientes.

Preparación de revisión1:fuente1029 congelada,65 archivos cambiados, scope-check
oficial exit0 sin fuera/avisos/exclusiones. Exportador generó88 archivos de
Codex/OpenCode desde fuentes canónicas en copia propia; --check exit0 y copia
de proyecciones a ROOT por rutas explícitas verificadas. Diff SHA
`dec90289f1e8428d494ca2d5c0ad9bbf578bba7950b099ce0669cf1cacdc7cb6`,
manifiesto SHA `669cbcf220f38c6d3d93140e5ca7bd37166f0f6329d90aff8fdbad1e551c3410`.
Selector C=false/D=false sin avisos; lentes frescas A+B en paralelo, sin
aceptación concedida. ROOT mantiene HEAD3be4821, índice vacío y modo100755
de install.mjs; sólo tasks cambia después de congelar para registrar evidencia.

Checks sobre la fuente:portable200 archivos/0 problemas; las seis dependencias
directas reales del servicio viajan idénticas a la fuente. Se conserva el fallo
del auxiliar que exigía por error knowledge-services.py; el AST confirma
knowledge-schema.py, sin cambio de producto ni repetición de tests. Lint0
errores/9avisos (8históricos y uno nuevo de consola del módulo de reglas, bajo
revisión), evals52 archivos/188 casos/0errores, ledger0incoherencias/1aviso
histórico. Los1029 hashes congelados permanecen intactos; sin referencias
públicas prohibidas en la selección. No hay QA final, commit o push todavía.

Probe CLI portable propio:propose/apply/recover terminaron exit0 con stdout JSON
válido y stderr vacío. Corpus sintético UTF-8 con emoji, propuesta sin approved,
publicación ligada al SHA y recover idempotente byte a byte; configuración y
evidencia iniciales permanecieron idénticas. Recibo SHA
`b0ca07f09ca71870e60d0357547326c88629ceb2648b5ca979866756e6a5ad69`.
Sin clientes, inferencias, red o credenciales; no cuenta como aceptación nativa.
ROOT verificó los16 documentos/8 artefactos del primer autor y los12 prompts/5
artefactos del segundo contra baseline y ROOT; informe de seis docs adicionales
pendiente. Son verificaciones de autoría, no aceptación de revisión.

Revisión1 en curso: A señala integración de consola pendiente para ambos módulos
nuevos; B reproduce bloqueo de recover por nlink2 al interrumpir publicación de
intención/recibo, diagnóstico de categoría sin redacción y regresión de nombres
largos válidos del bridge. También señala contradicción de instrucciones del
Curator en las proyecciones. Informes completos, arbitraje, regresiones dedicadas
y corrección pendientes; ningún hallazgo se declara corregido ni se concede QA.

## Revisión de dos lentes — intento 1: Bloque23 (T-07/T-08/T-11/T-14/T-15) — corregir cinco Important

Lentes frescas A+B por subagentes genéricos; reviewer nativo no disponible.
Selector oficial C=false/D=false, sin avisos. ROOT leyó ambos informes completos,
contrastó los cinco hallazgos con fuente/reproducciones y los aceptó sin rebate.
0 Critical/5 Important/0 Minor. A aporta conformidad; sus ✓ no anulan los
defectos concretos reproducidos por B. Ninguna macro se cierra.

Tabla completa de criterios A sobre la fuente de revisión1:

| Criterio | Veredicto A | Evidencia / límite |
|---|---|---|
| Tareas hechas y criterios | ✓ | Sólo T-01 completada; no cambia su verificación. |
| Alcance del plan | ✓ | 65 rutas declaradas; scope sin exclusiones, avisos ni fuera. |
| Tests y oráculos reales | ✗ | IO real; falta consola obligatoria A23-1. |
| Constitución explícita | ✓ | Ownership/stdlib/redacción y límites declarados. |
| Verificaciones de tareas cerradas | ✓ | Ninguna macro nueva completada. |
| Generado / E2 | ✓ | Check propio A PID32344, exit0, 88 al día; sin cliente nativo. |
| Descriptores / E3 | ✓ | ROLES/CONTRACTS/E13/E14/E22/E53/E54 y espejos actualizados. |
| OpenAPI | n/a | No spec OpenAPI modificada. |
| Docs-style como gate de prosa | n/a | Bloque de persistencia con pruebas; no prosa exclusiva. |
| Corte prospectivo/legado | ✓ | Sin migración, reaprobación ni borrado. |
| Persistencia compartida/juicio Curator | ✓ | Productores proponen; Curator decide; servicio persiste. |
| Propuesta redactada/portable/exclusiva | ✓ | Límites, SHA y reserva; B3 detecta compatibilidad larga. |
| SHA/metadatos finales | ✓ | Índice/ID/versión/taxonomía; B4 detecta secreto en diagnóstico. |
| needs_changes/reject/replacement | ✓ | Original ligado a SHA y rechazado terminal. |
| Gate puro/reglas comunes | ✓ | Sin mutación; gate0 no es transición. |
| Intención/recibo/recover | ✓ | Cortes de checkpoint; B1 detecta corte interno de enlaces. |
| Concurrencia/IO/OS | ✓ | Cooperantes y límites; skips Windows no acreditan guards. |
| Productores/fallback/retro tardía | ✓ | Handoff o pendiente visible, sin autoaprobación. |
| Bridge Gold/store | ✓ | Gold/config/hash; B3 prueba ID válido máximo no cubierto. |
| Journal episódico | ✓ | Estado/fuentes y ausencia de promoción automática. |
| Confluence y staging | ✓ | Exclusión antes de include; sin publicación real. |
| Honestidad RED/GREEN/QA | ✓ | Fallos/skips preservados; aceptación final pendiente. |
| Consola de piezas nuevas | ✗ | Snippet y MODOS ausentes A23-1. |
| Rama/publicación/macros | ✓ | Sin PR/release/main ni cierre global declarado. |

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A23-1 | Important | Consola: snippet rules y MODOS ausentes | T-11/T-14/T-15 | Snippet literal, módulo puro medido y stdin/JSON/emoji reales cp1252/ascii; pendiente revisión2 | RED11 fallos; GREEN20 sin skips. |
| B23-1 | Important | recover bloqueado con nlink2 de intención/recibo tras enlace antes de limpieza | T-08/T-14 | Registro liga staging e identidad; sólo limpia el enlace exacto validado, rechaza ajenos; pendiente revisión2 | RED dos cortes internos; GREEN con recuperación doble y contraejemplos ajenos. |
| B23-2 | Important | Curator generado ordena no escribir y derivar al implementador | T-11/T-15 | Exportador declara persistencia por servicio/Bash y límites reales; edición directa denegada; pendiente revisión2 | RED Codex/OpenCode; GREEN y 88 exports al día. |
| B23-3 | Important | Gold válido de nombre histórico157 excede destino128 | T-08/T-14 | Slug acotado/hash completo, aliases sólo comparación en cuatro árboles; ruta/SHA real en handoff; pendiente revisión2 | RED seis bridge y contrato aliases; GREEN nombres ordinarios/Gold/store intactos. |
| B23-4 | Important | Categoría/ID inválidos muestran secreto en errores | T-08/T-14 | Redactor compartido en diagnóstico; sin él nunca emite bytes crudos; pendiente revisión2 | RED categoría/ID; GREEN mismos códigos y corpus intacto. |

Informes A SHA `783b6438705d714eb9f0ba690b7a9b596a68bf5b0f83107741410fef51e7b1f8`,
B SHA `923072cb0ae7bf37026b20285e801638d71c10eeb7c9bc6e8696206733d1cfe8`.
ROOT verificó recibos y sus 12/9 artefactos; los1029 hashes de la fuente siguen
idénticos al manifiesto congelado. Verificó además los seis docs adicionales
(baseline/ROOT y siete artefactos), puente corregido y dos fuentes de consola.
Esto acredita autoría/evidencia, no aceptación. Jira no se ejecuta: el fixture
de verificación no tiene integración activa ni issues volcados; no se consultan
configuraciones del consumidor.

RED consola:11 failed/5 passed/exit1, JUnit SHA
`537a39e6c2c770316a88f45026f85c4772364d4a7db200b066eacf5676b5c0fb`.
RED bridge:6 failed/exit1, JUnit SHA
`30088abf11e7afaa6a797756a379a14c2d5e26d3b03bc92c03699bfc37ef9f9d`.
RED core/export:16 failed/2 passed/exit1; procesos exactos terminados y logs
preservados antes de modificar producto. Los dos verdes de contraejemplo
comprueban que no se adopten enlaces ajenos; no son fallos ocultados.

GREEN corregido:264 passed/2 skipped/exit0 (servicio, gate anterior, bridge,
scope y exportador), JUnit SHA
`39514b187a5fbcf5ff6d2bda101d1388cef17d289cca1c9b1b1902dd119f0dda`.
Consola:20 passed/0 skipped/exit0, JUnit SHA
`1aa166a3c0a01230d4d25de30e1a4df5f22d95646a3e3dc71d08daf3c480c424`.
Los dos skips conservan los casos de symlink de archivo no disponibles en
Windows. Fuentes/oráculos congelados y ejecución OWN, sin corpus, red, modelos,
auth ni Docker del usuario. Exportador canónico escrito/check88 exit0 en esa
copia; trasladar proyecciones y preparar revisión2 todavía pendientes al
registrar esta evidencia. No hay QA final, commit ni push del bloque23.

## Revisión de dos lentes — intento 2: Bloque23 (T-07/T-08/T-11/T-14/T-15) — corregir un Important de rendimiento

Contexto fresco A+B+D, selector C=false/D=true. Revisor genérico; tier
opus/high comunicado desde frontmatter, sin override ni configuración consumidora.
Fuente inmutable1029, diff68/6577; ROOT leyó informes completos y verificó
23/88/119 artefactos, recibos, entradas y todos los hashes de la fuente.
El primer verificador auxiliar ROOT falló al tratar SHA null de archivos
nuevos como hashes de baseline; corregido a comprobar ausencia exacta. No
ejecutó producto ni altera dictámenes. A y B:0/0/0; D:0 Critical/1 Important/0 Minor.
ROOT acepta D23-1: el coste está reproducido y nace de recargar contenidos
históricos completos bajo el cerrojo. Los cinco Important previos quedan
corregidos; no se reabren conformidades aprobadas ni hay hallazgos rebatidos.
Ninguna macro se cierra y QA no comienza con un Important pendiente.

Tabla completa A del intento2 (referencias relativas a su fuente congelada,
sin convertir pruebas comunicadas en QA propia del revisor):

| Criterio | ✓/✗ | Evidencia y límite |
|---|---|---|
| T-XX hechas y criterios | ✓ | `docs/roadmap/2026-10-07-catalog-capabilities/tasks.md:46–56`: sólo T-01 completada, tres criterios y verificación corpus preservados. T-02…T-16 abiertas/borrador; no se reacepta comparación global. |
| Alcance del plan | ✓ | `tasks.md:204,248,281,292`: Archivos cubre servicio/kits/callers/docs/tests/interop. ROOT comunica scope oficial68/0fuera/0avisos/0excluidos. Las68 rutas verificadas implementan o describen curación; la aclaración F2 sólo retira falsa entrega de memoria/especialización. |
| Tests y oráculos reales | ✓ | `agent-kits/shared/test_knowledge_curation.py:106–194,195–702`: IO real, cortes/contraejemplos, redacción, aliases y estado legado. Bridge `skills/training-data-services/scripts/test_propose_from_case.py:603–701`; consola `tests/test_console_encoding.py:730–770`; export `tests/test_export_interop.py:51–62`. A23-1 subsanado sin fake writer ni exclusión genérica. |
| Constitución explícita | ✓ | `docs/CONSTITUTION.md:10–13,17–21,36–40`: scripts/tests/RED, regresiones dedicadas, fuente generada, stdlib, propietario del juicio, redactor compartido y no mutación ajena. `tasks.md:1024` en adelante preserva RED correctivo y GREEN; no exige PR/main/release excluidos por autorización vigente. |
| Verificación declarada de tareas cerradas | ✓ | `tasks.md:52` conserva ejecución T-01; no macro nueva completada. `tasks.md:846` en adelante conserva estado B23 en progreso, evidencias y pendientes; no ejecuté verificaciones faltantes para tapar cierre. |
| Generado al día / E2 | ✓ | Comprobación A propia en copia OWN exacta: PID30224, Python absoluto `-I -X utf8 -B scripts/export-interop.py --check`, exit0, stdout `export-interop --check: 88 ficheros al día`, stderr vacío. `interop/**` declarado en T-11/T-15; ROOT conserva evidencia previa. Falta traza final del intento2 por revisión en curso, sin macro cerrada. |
| Descriptores actualizados / E3 | ✓ | `docs/agents/CONTRACTS.md:76–77,85,118–119`: E13/E14/E22/E53/E54 describen servicio, juicio, SHA y fronteras. `docs/agents/ROLES.md:30–43,89`; docs de seis agentes, CONVENTIONS/FLOWS/SPECIALIZATION ES/EN, skills/kits y comando retro actualizados en el mismo diff. |
| API OpenAPI | ✓ (n/a) | Ninguna spec OpenAPI en las68 rutas. No se ejecutó openapi-lint. |
| Docs-style | ✓ (n/a como gate de prosa) | Bloque de servicio/persistencia con pruebas y descriptores, no iniciativa exclusivamente de prosa. Espejos preservan sentido y tokens; no se reporta estilo. |
| T-07 corte prospectivo / legacy | ✓ | `agent-kits/shared/knowledge-write.md:65–89`, `knowledge-check.md:59–71`, contrato `comparisons/memory-curation-contract.md:98–114` bajo roadmap. No migración/reaprobación/borrado ni accepted=approved. `test_knowledge_curation.py:597–610` conserva bytes/IDs/estados/journal/README. |
| T-08 persistencia compartida / juicio Curator | ✓ | `knowledge-curation.py:450,551,611`; `agents/knowledge-curator.md:37–46,79–141`: propose productores, Curator semántica, servicio bytes. Gate/design/QA/revisión/Gold/repetición no aprueban por sí solos. Sin agente/skill nuevo. |
| Propuesta redactada, portable y exclusiva | ✓ | `knowledge-curation.py:78–85,153–164,195–204,450–475`: 128 destino, aliases<=8/255 sólo comparación, cuatro estados/approved casefold y reserva bajo cerrojo. `test_knowledge_curation.py:170–194,195–266` reserva históricos sin escritura por alias y preserva redacción/SHA. |
| SHA original y metadata final | ✓ | `knowledge-curation.py:404–443,551–571`: ID/prefijo, categoría exacta, versión1, índice/colisión y SHA fuente. `_caught:66–76` redacta diagnóstico antes de devolución, fallback sin bytes crudos. Tests dedicados `test_knowledge_curation.py:157–167` cubren categoría e ID sensibles con mismo status/código y árbol intacto. |
| needs_changes/reject/replacement | ✓ | Servicio `:560–576,589–607`; tests `:364–429`: original/contenido/motivo y SHA conservados, rechazo terminal, sólo approve corrección final, nunca edición de approved. |
| Gate puro / reglas compartidas | ✓ | `agent-kits/knowledge-curator/curator-gate.py:152–172` delega mismas reglas usadas por servicio `:421–435`. `test_knowledge_curation.py:613–619` comprueba gate sin mutación; gate0 no significa transición. |
| Intención / recibo / recover | ✓ | Servicio `:299–340,477–496,499–548`: staging/identidad exactos ligados al registro, hash de intención, lectura links controlada y limpieza sólo verificable. Tests `:106–153` cortan el enlace real operations/receipts, recover doble y rechazo de hardlink ajeno sin mutación; `:456–524` conserva cortes/reintentos/cambios/ajenos. No garantiza corte eléctrico. |
| Concurrencia / IO / OS | ✓ | Servicio `:109–147,166–204,207–290`; tests `:526–595,633–702`: cerrojo cooperante de proceso, redirected/hardlinks/scan incompleto, fuente ajena conservada. Los dos skips Windows de symlink no prueban esos guards; POSIX/native pendientes. |
| T-11 productores / fallback / retro tardía | ✓ | Architect/planner/implementer/qa/documenter/debug-root-cause/retro/bridge delegan sin writer fallback. `commands/dev-cycle.md:400–428`; `commands/retro.md:24–34`: handoff tardío o pendiente/ruta/ID visible, cierre retro no aprueba memoria. |
| Bridge Gold / nombres / SHA / store | ✓ | `propose-from-case.py:172–187,210–267,307–309`: nombre histórico ordinario igual, sólo truncado slug largo conservando hash/ref íntegros; aliases reservan históricos157, sin ampliar destino128. API/CLI conserva SHA real; `test_propose_from_case.py:603–701` prueba dos Gold máximos, cuatro estados, duplicado/store/config intactos y handoff SHA. Hash ausente/cambiado conserva tratamiento `:239–243` y pruebas `:417–438`. |
| Journal episódico sin promoción | ✓ | `journal.py:1565–1574,1702–1711,2178–2184`; `test_journal_curation_handoff.py:18–52`: sólo cambia orientación generada, conserva fuentes/estado y no escribe candidates/approved. RED/GREEN histórico se conserva, no nueva aceptación QA. |
| Confluence excluye journal/candidates y staging | ✓ | `confluence-scope.py:83–85,268–275`; defaults/skill/policy y `test_memory_curation_scope.py:21–58`: exclusión antes de include, casing y staging, approved/originales intactos. Sin conexión/publicación externa. |
| T-14 honestidad RED/GREEN/QA | ✓ | `tasks.md:863` en adelante conserva fallos, REDs y GREEN205/2skips, journal173/10skips, nuevos RED11/6/16 y GREEN264/2symlinkskips + consola20sin skips. Evidencia comunicada/ledger, no tests propios A ni QA completa, eficacia/escala/UX/native/global. |
| T-15 consola obligatoria nueva | ✓ | A23-1 corregido: rules `:6–8` incorpora snippet literal al arrancar; service `:20–22` conserva suyo. `test_console_encoding.py:305–306,383–392` declara pureza nominal medible/MODOS para ambos; `:730–770` oráculos reales cp1252/ascii, error noASCII JSON y stdin UTF8/emoji/bytes/SHA éxito. El criterio canónico `:169–179,269–292,639–722` se conserva. |
| Rama / publicación / macros | ✓ | `tasks.md:14–24,1035–1046`: no PR/main/release ni B23 publicado/aceptado, sólo T-01 cerrada. Autorización normal commit/push rama no obliga PR/release. Comparación restante, skills aplazadas y objetivo global activos. |

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A23-1 | Important | Consola de nuevas piezas | T-11/T-14/T-15 | Corregido, confirmado A2; criterio conservado | Snippet/MODOS y oráculos reales, check88 propio. |
| B23-1 | Important | Corte entre enlace y limpieza de registros | T-08/T-14 | Corregido, confirmado B2 | Dos cortes reales y recover doble; enlaces ajenos rechazados. |
| B23-2 | Important | Curator generado incompatible con su persistencia | T-11/T-15 | Corregido, confirmado B2 | Dos proyecciones completas y otras14 equivalencias verificadas. |
| B23-3 | Important | Nombre Gold largo y SHA en handoff | T-08/T-14 | Corregido, confirmado B2 | Gold máximo real, aliases cuatro estados y store intacto. |
| B23-4 | Important | Secreto en diagnóstico de metadatos | T-08/T-14 | Corregido, confirmado B2 | Mismos códigos, secreto omitido y dependencia ausente segura. |
| D23-1 | Important | Cada apply recarga todos los payloads de intenciones cerradas | T-08/T-14/T-15 | Directorios ligados a la ruta del candidato; recover enumera nombres y valida único registro; pendiente GREEN y revisión3 | D:1/201/801 históricos,2/202/802 lecturas y0,139/0,703/2,031s. RED ROOT abajo. |

Informe A SHA `563f74c78e101812bb5185e55153d10d6e8f47d123c73c64a2b956e1c24c4b74`,
B SHA `32ce3dfd3d81cb4171965ea0fda00994ac0330556c8812a20db6cd3a6becb210`,
D SHA `d4f9684a7761c34b0305dbdc23a7e1b5b20c9e60709d8ba89727d4e0b4056e24`.
D conserva fixture sintético, cuatro procesos exactos exit0 y fallos auxiliares;
la extrapolación del lote20 no se presenta como medida. El cambio evita leer
payloads ajenos; no promete tiempo constante, historial ilimitado ni aceptación
nativa. Conserva recibos, hashes, redacción, recuperación y registros históricos.

RED: `test_review_d23_d1_apply_does_not_reload_unrelated_completed_history`
falló con cuatro lecturas ajenas; el contraejemplo de ID duplicado también
falló · 2026-10-10. PID11080 exit1,2 failed/5 passed/101 deselected; JUnit SHA
`884dd5e900eda5b2647aa268392eb753a89c727645eb21ae33f934823f1cfb87`.
Los cuatro tests B1 pasan antes del cambio con localización independiente del
layout, manteniendo la interrupción del enlace real y los enlaces ajenos.
Contrato actualizado antes de implementar; formato prospectivo no publicado,
sin migración del corpus legado. Fuentes y oráculos congelados en OWN, sin
consumer settings, red/modelos/auth ni Docker. GREEN, revisión3, QA,
commit y push pendientes al registrar esta fusión.

Dirección del usuario del2026-10-10: completar capacidades prioritarias
(comandos, dashboard, memoria y compatibilidad), continuar hasta terminar,
y retomar la ampliación de skills después. No se añaden skills en este bloque.

GREEN correctivo D23-1: PID32360 exit0,267 passed/2 skipped; JUnit SHA
`fa4f357e07ca5eca3bf16028b4e4aef8775486edc9870b05b074a7c2512f21c4`.
El oráculo dedicado observa cero lecturas de payloads históricos ajenos,
conserva sus bytes y recupera cada ID de manera idempotente. Los ID duplicados
y las intenciones fuera de directorio se rechazan sin mutación. Los cuatro
cortes/contraejemplos B1 se mantienen. Consola PID30188 exit0,20 passed sin
skips; JUnit SHA `ee4b7b465408ae5140905bd274e321132169c8fdd1d731bc0c738732a472945e`.
Dos skips de symlink de archivo Windows documentados; no se acreditan esos
guards. Exportador escrito/check88 exit0 sólo en copia OWN. Pendiente revisión3
independiente de la corrección, QA Windows/Linux y publicación de la rama.

## Revisión de dos lentes — intento 3: Bloque23 (T-07/T-08/T-11/T-14/T-15) — sin gaps pendientes

Lentes A+B+D, C=false/D=true; contexto fresco, fallback genérico reviewer
con tier opus/high frontmatter y sin override consumidor. Scope oficial68,
0 fuera/avisos/excluidos; fuente inmutable1029, diff68/6740 líneas. ROOT leyó
completos los tres informes, verificó recibos/90+362+112 artefactos, entradas
y hashes1029. Los seis Important están corregidos; 0 Critical/Important/Minor.
No rebatidos ni criterios reabiertos. B3 conserva23 sondas, sin sumar la
cohorte anterior de21; A ejecutó check88 propio PID17500 exit0.
Revisión aceptada como puerta previa de este bloque, no QA ni cierre macro.

Tabla completa A3 (referencias relativas a la fuente congelada revisión3):

| Criterio | ✓/✗ | Evidencia y límite |
|---|---|---|
| T-XX hechas y criterios | ✓ | `docs/roadmap/2026-10-07-catalog-capabilities/tasks.md:46–56`: T-01 conserva sus tres criterios y verificación; única macro completada. `tasks.md:33–40`:1/16; no acepta comparación global. |
| Alcance del plan | ✓ | `tasks.md:204,238,248,258` declara agentes/comandos/kits/scripts/tests/skills/docs/interop/changelogs. ROOT scope PID33736 exit0:68 en alcance,0 fuera/avisos/excluidos. `diff-audit.json` reconstruye esas68 rutas; corrección y contrato/oráculos permanecen en ese alcance. |
| Tests y oráculos reales | ✓ | `agent-kits/shared/test_knowledge_curation.py:105–205`: cuatro B1 siguen interrumpiendo `os.link` real y rechazando enlace ajeno; D23-1 observa `_read` real, conserva cada byte histórico y recupera cada ID; misplaced/duplicate compara árbol antes/después. `tests/test_console_encoding.py:730–770` conserva oráculos reales Unicode. No fake writer para verde. |
| Constitución explícita | ✓ | `docs/CONSTITUTION.md:10–13,17–21,36–40`: stdlib, dueño único, TDD/regresión dedicada, fuente generada, redactor/no mutación ajena. `tasks.md:1091–1100,1106–1115` conserva RED antes del cambio y GREEN posterior sin QA. `_load_operation:495–506` liga ruta antes de limpiar staging propio. |
| Verificación de tareas cerradas | ✓ | `tasks.md:52` conserva evidencia ejecutada T-01. Las demás tareas permanecen abiertas; `tasks.md:1106–1115` conserva verificación acotada y pendientes explícitos. No ejecuto una verificación faltante para tapar cierre. |
| Generado al día / E2 | ✓ | Check propio en copia OWN exacta1029: Python PID17500, `-I -X utf8 -B scripts/export-interop.py --check`, exit0, stdout `export-interop --check: 88 ficheros al día`, stderr vacío. `tasks.md:204,248` declara interop y `:1114` evidencia autor; revisión3 todavía en curso sin macro cerrada. |
| Descriptores actualizados / E3 | ✓ | `docs/agents/CONTRACTS.md:76–77,85,118–119` E13/E14/E22/E53/E54; `ROLES.md:30–43,89`; seis docs agentes y CONVENTIONS/FLOWS/SPECIALIZATION ES/EN, skills/kits/callers actualizados en el mismo diff. Nuevo layout descrito en contrato `:83–94`, sin nueva promesa global o nativa. |
| API OpenAPI | ✓ (n/a) | Ninguna spec OpenAPI en las68 rutas. No ejecutado openapi-lint. |
| Docs-style | ✓ (n/a como gate exclusivo de prosa) | Servicio/persistencia con pruebas y descriptores, criterio conservado del pase2. Fragmento `agent-kits/shared/docs-style.md:14–25` leído; no reabro estilo. |
| T-07 corte prospectivo / legado | ✓ | `agent-kits/shared/knowledge-write.md:65–89`, `knowledge-check.md:59–71`; contrato `memory-curation-contract.md:113–126` bajo comparisons. Sin migración/reaprobación/borrado ni accepted=approved; nuevo layout prospectivo `:93–94`. `test_knowledge_curation.py:648–661` preserva legado/journal/índice. |
| T-08 persistencia compartida / juicio Curator | ✓ | `knowledge-curation.py:450,562,623`; `agents/knowledge-curator.md:37–46,79–141`: productor propone, Curator semántica, servicio bytes. Revisión/design/QA/Gold/repetición no aprueban; sin nuevo rol/skill. |
| Propuesta redactada, portable y exclusiva | ✓ | Servicio `:78–85,153–164,195–204,450–475`: destino128, aliases<=8/255 sólo comparación, reserva en cuatro estados bajo cerrojo, SHA final. Tests `:220–307` conservan aliases/duplicado/redacción y nunca destino por alias. |
| SHA original / metadatos finales | ✓ | Servicio `:404–443,562–589`: ID/prefijo, categoría, versión1, índice/colisión y SHA fuente. `_caught:66–76` conserva redactor o fallback seguro. Test dedicado B4 `:207–217` mantiene código/status y árbol intacto sin secreto. |
| needs_changes/reject/replacement | ✓ | Servicio `:569–576,585–618`; tests `:415–480`: preserva original/motivo, rejected terminal, sólo approve admite replacement completo ligado al SHA original; nunca edición de approved. |
| Gate puro / reglas compartidas | ✓ | `agent-kits/knowledge-curator/curator-gate.py:152–172` delega los mismos validadores del servicio `:421–435`; `test_knowledge_curation.py:664–670` conserva gate0 sin mutación ni transición. |
| Intención / recibo / recover | ✓ | Servicio `:299–340,477–507,510–559,623–630`: SHA de ruta exacta, operación hash/verificación y binding antes de `_settle_record`; recover enumera nombres y exige única coincidencia. Tests `:105–205` conservan cortes B1 y añaden misplaced/duplicate sin mutación; `:507–575` preserva cortes/reintentos/cambios/ajenos. No corte eléctrico. |
| Concurrencia / IO / OS | ✓ | Servicio `:109–147,166–204,207–290`; tests `:577–646,684–753`: proceso cooperante, enlaces/scan incompleto y fuente ajena conservada. _walk de recover conserva límite4096 y rechaza escaneo no verificable. Dos skips Windows no prueban guards symlink; POSIX/nativo pendientes. |
| T-11 productores / fallback / retro tardía | ✓ | Seis agentes, debug-root-cause/retro/bridge siguen el mismo propose sin writer alternativo. `commands/dev-cycle.md:400–428`, `commands/retro.md:24–34`: handoff explícito o ruta/ID pendiente; cierre de retro no aprueba. |
| Bridge Gold / nombre / SHA / store | ✓ | `propose-from-case.py:151–164,210–243,274–277`: fórmula ordinaria preservada, acorta sólo slug largo y reserva alias histórico, SHA real servicio. `test_propose_from_case.py:603–701` verifica Gold máximos, cuatro estados, store/config y handoff; sin hash/cambiado conserva tratamientos históricos. |
| Journal episódico sin promoción | ✓ | `journal.py:1565–1574,1702–1711,2178–2184`; `test_journal_curation_handoff.py:18–52`: orientación de consulta explícita, fuentes/estado preservados y ausencia de creación de candidates/approved. No aceptación por repetición. |
| Confluence / staging | ✓ | `confluence-scope.py:83–85,268–275`, defaults/skill/policy; `test_memory_curation_scope.py:21–58`: exclusión forzada journal/candidates antes de include/casing/staging; approved y originales preservados. No conexión/publicación real. |
| T-14 honestidad RED/GREEN/QA | ✓ | `tasks.md:1091–1100`: RED2fallos/5pases, B1 pasaba misma frontera antes del cambio; `:1106–1115`: GREEN267/2skips y consola20sin skips, procesos exactos/SHAs y QA/publicación pendientes. Históricos conservados sin suma como cobertura única ni eficacia/escala/global. |
| T-15 consola obligatoria nueva | ✓ | A23-1 corregido confirmado2 y conservado: rules `:6–8` snippet, servicio `:20–22`; `test_console_encoding.py:305–306,383–392,730–770` MODOS/pureza medidos y UTF8/emoji/JSON/SHA reales cp1252/ascii. Criterio canónico no relajado. |
| Rama / publicación / macros | ✓ | `tasks.md:14–24,1102–1115`: sólo T-01 cerrada; sin PR/main/release ni B23 publicado/aceptado. Prioridades y skills aplazadas se mantienen; continúa objetivo global, QA/OS/clientes pendientes. |

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A23-1 | Important | Consola | T-11/T-14/T-15 | Corregido; aprobado2 y conservado3 | Snippet/MODOS, oráculos Unicode y criterios intactos. |
| B23-1 | Important | Corte enlace/limpieza de registros | T-08/T-14 | Corregido; confirmado B3 en layout actual | Cortes reales operations/receipts y staging vivo, recover doble y enlaces ajenos. |
| B23-2 | Important | Curator generado incompatible | T-11/T-15 | Corregido; aprobado2 y conservado3 |16 proyecciones individualmente verificadas; check88 propio A3. |
| B23-3 | Important | Gold largo y handoff SHA | T-08/T-14 | Corregido; aprobado2 y conservado3 | Nombre128/hash completo/aliases y store conservados. |
| B23-4 | Important | Secreto en diagnóstico | T-08/T-14 | Corregido; aprobado2 y conservado3 | Redactor/fallback y códigos sin datos crudos. |
| D23-1 | Important | Recarga global de payloads históricos bajo lock | T-08/T-14/T-15 | Corregido, confirmado D3 y sin defecto B3 |801 históricos:802→1 lecturas,62.627.193→78.137B,0 ajenas; cuatro transiciones reales conservadas. |

Informes SHA A `3ee6e8f4aa327a5df8774f0987fef2517b67768486d060985e977fb09e8c5d7c`,
B `a9edbd14df60b1100407e82b49236f04ad093fc0e9a26396fa2d442812acd30d`,
D `abef027d6f97f4dd11a0a5983b005f2c67460ae425a199eb84eab53a4969df4c`.
D mide muestras locales individuales: apply antiguo3,465s frente nuevo0,164s;
no SLA ni benchmark universal. Recover801 enumera803 directorios/1604 nombres,
lee un payload y tarda1,320s: coste explícito y acotado, no O(1).
La construcción de801 históricos modela registros sintéticos, no801 movimientos
reales; la sonda adicional sí completa cuatro transiciones reales y recover
doble con bytes intactos. Ambas fuentes/probes preservan sus límites.

Precisión de evidencia: B3 mantiene recibo original y suplemento SHA
`cfa8c8208a430894d9b9fd45ccfe4b912e9c69e88bbfadd5ae180a1e91e3017a`,
con16 hashes verificados. Su array argv original partió la ruta: no es captura
nativa; reconstrucción por receta diferenciada de sys.argv. Los logs del primer
finalizador son finalize-first, no los nombres reutilizados tras su fallo.
PID inicial ausente declarado; no se inventa. A/D conservan sus fallos auxiliares,
sin atribuirles verde de producto. No se repiten sondas para completar metadata.

Jira no publica: fixture público OWN sin integración activa ni issues volcados;
configuración privada del consumidor no consultada. Ninguna memoria se aprueba
por esta revisión. Se habilita QA de fuente exacta revisión3: Windows/Linux,
Coverage.py oficial y gates sin redondear, bundle portable/CLI/lint/evals/exports.
La preparación instala sólo dependencias QA OWN, no producto/Python global.
QA, commit y push todavía pendientes; las dieciséis macros conservan su estado.


## Validación Windows/Linux interrumpida y corrección posterior — Bloque23

La primera QA no se acepta: Windows JUnit995 passed/3 failed/1 error/2 skipped,
Linux952 passed/1 failed/1 error/1 skipped; pytest exit3 y procesos externos exit1.
JUnit SHA Windows `53172507423ee1e28b272cb8af1a9f17fd12671ef7b944130f21da2c41b4a092`,
Linux `8318e46f65e0aedae4f1980ffe35413c19e7809f2adfb2672b4c418f46870fa5`.
Se preservan resultados parciales, sin acreditar cobertura ni gate completo.
El contenedor QA OWN quedó detenido, eliminado por su ID exacto y ausente;
las1029 fuentes conservaron sus hashes. No se tocó ningún servicio del usuario.

La monitorización ROOT leía el log vivo mediante FileShare.Read: podía impedir
su append en Windows y en el bind mount Linux. Reproducción OWN con fixture
aislado: PowerShell PID31184 exit0; Python32520 obtiene PermissionError con
lector abierto y37536 exit0 después de cerrarlo. La primera sonda auxiliar
falló por quoting de PowerShell y se conserva; no prueba el bloqueo. Se corrige
el diagnóstico inicial atribuido a mocks. La repetición no leerá logs vivos
con ese modo; el registro QA usa referencias IO capturadas y progreso stdout.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| Q23-1 | Important | CI omite la suite Confluence nueva | T-14 | Incluida en workflow y copia manual | `test_toda_suite_de_skill_esta_en_la_linea_pytest_de_la_ci`: falla antes y pasa después. |
| Q23-2 | Important | Consola no declara el validador visual del bloque22 | T-14/T-15 | MODOS con envelope UTF8 válido; SIN_SIMBOLOS explícito medido | Oráculos existentes de arranque, snippet y Unicode:5 rojos antes; sin saltar el script ni aceptar invalid_open. |

RED correctivo PID25632 exit1:5 failed/4 passed/554 deselected. JUnit SHA
`6b7872de4732bc666c7666c2d2ec3d0b727143e6c4fdae9bc7bd3babde278be2`.
GREEN dirigido PID22916 exit0:570 passed/6 skipped. JUnit SHA
`9b824f2061b0dafc575ab9f959c7690aad7bf8a5870b4c6a9ed86a42969848a8`.
Tres skips: PyYAML ausente en esa receta; otros tres: Node ausente.
No se acreditan esos seis checks; QA completa llevará ambos runtimes QA OWN.
No cambia código de producto, decisiones de memoria ni proyecciones generadas.

El ciclo original revisión1–3 se conserva aceptado. Se abre un ciclo acotado
nuevo de remediación post-QA sobre seis rutas de CI/tests/changelogs/ledger,
con máximo tres intentos, sin reiniciar ni ocultar los tres pases anteriores.
Sus24 criterios y seis gaps corregidos se trasladan íntegros; se reevalúan
sólo Q23-1/Q23-2 y el delta, salvo evidencia nueva. No hay aprobación de memoria,
QA verde, cierre macro, commit ni push todavía. Skills aplazadas hasta completar
comandos, dashboard, memoria y compatibilidad, según instrucción del usuario.

## Revisión de dos lentes — intento 1: Remediación post-QA Bloque23 (T-14/T-15) — sin gaps pendientes

Ciclo nuevo acotado1 de3, separado de revisión original1–3 aceptada.
Lentes A+B+C independientes en paralelo, D=false. C=true sólo por workflow.
Scope PID35296 exit0:6 rutas,0 fuera/avisos/exclusiones. Export check88
PID10000 exit0. Ledger PID23512 exit0, aviso histórico de cabecera729.
ROOT leyó íntegros los tres informes y verificó recibos,26 hashes de A,
artefactos/hijos B y las1029 fuentes congeladas. Se conservan24 criterios
y seis gaps originales; Q23-1/Q23-2 corregidos,0 Critical/Important/Minor.
Sin rebatidos, reaperturas, nueva aprobación de memoria ni cierre macro.

| Criterio | ✓/✗ heredado | Evidencia aceptada del ciclo original3 (referencias históricas) | Revisión del delta remediación1 |
|---|---|---|---|
| T-XX hechas y criterios | ✓ | `docs/roadmap/2026-10-07-catalog-capabilities/tasks.md:46–56`: T-01 conserva sus tres criterios y verificación; única macro completada. `tasks.md:33–40`:1/16; no acepta comparación global. | ✓ Conservado; tasks.md:48 única macro completada. |
| Alcance del plan | ✓ | `tasks.md:204,238,248,258` declara agentes/comandos/kits/scripts/tests/skills/docs/interop/changelogs. ROOT scope PID33736 exit0:68 en alcance,0 fuera/avisos/excluidos. `diff-audit.json` reconstruye esas68 rutas; corrección y contrato/oráculos permanecen en ese alcance. | ✓ Revalidado: tasks.md:238–239 y259; scope PID35296 exit0 seis rutas, 0 fuera/avisos/excluidos. Changelogs pertenecen al alcance T-16, sin cerrar esa macro. |
| Tests y oráculos reales | ✓ | `agent-kits/shared/test_knowledge_curation.py:105–205`: cuatro B1 siguen interrumpiendo `os.link` real y rechazando enlace ajeno; D23-1 observa `_read` real, conserva cada byte histórico y recupera cada ID; misplaced/duplicate compara árbol antes/después. `tests/test_console_encoding.py:730–770` conserva oráculos reales Unicode. No fake writer para verde. | ✓ Revalidado: tests/test_ci_skill_suites.py:61–63; test_console_encoding.py:303–304,380–387,687–699,783–796. Ejecución real subprocess :632–634. RED5 y GREEN570/6skips comprobados; no acreditan QA global. |
| Constitución explícita | ✓ | `docs/CONSTITUTION.md:10–13,17–21,36–40`: stdlib, dueño único, TDD/regresión dedicada, fuente generada, redactor/no mutación ajena. `tasks.md:1091–1100,1106–1115` conserva RED antes del cambio y GREEN posterior sin QA. `_load_operation:495–506` liga ruta antes de limpiar staging propio. | ✓ Revalidado: CONSTITUTION.md:11–13,26. RED previo conserva tests que identifican el gap, stdlib json y espejo ES/EN en el delta. Sin cambios generados manuales ni cierre global. |
| Verificación de tareas cerradas | ✓ | `tasks.md:52` conserva evidencia ejecutada T-01. Las demás tareas permanecen abiertas; `tasks.md:1106–1115` conserva verificación acotada y pendientes explícitos. No ejecuto una verificación faltante para tapar cierre. | ✓ Conservado; ninguna nueva tarea completada. Tasks.md:1216–1222 registra evidencia correctiva limitada, no cierre. |
| Generado al día / E2 | ✓ | Check propio en copia OWN exacta1029: Python PID17500, `-I -X utf8 -B scripts/export-interop.py --check`, exit0, stdout `export-interop --check: 88 ficheros al día`, stderr vacío. `tasks.md:204,248` declara interop y `:1114` evidencia autor; revisión3 todavía en curso sin macro cerrada. | ✓ No aplica al delta6: no cambia commands/, agents/ ni hooks/. No ejecutado export por esta lente. Check88/PID17500 sigue como evidencia histórica aceptada3, sin atribuir ejecución nueva. |
| Descriptores actualizados / E3 | ✓ | `docs/agents/CONTRACTS.md:76–77,85,118–119` E13/E14/E22/E53/E54; `ROLES.md:30–43,89`; seis docs agentes y CONVENTIONS/FLOWS/SPECIALIZATION ES/EN, skills/kits/callers actualizados en el mismo diff. Nuevo layout descrito en contrato `:83–94`, sin nueva promesa global o nativa. | ✓ Revalidado para delta: tasks.md:239,1193–1230 y CHANGELOG.md:14–16/CHANGELOG.es.md:14–16 describen exactamente CI y consola. Contratos/callers del producto sin delta. |
| API OpenAPI | ✓ (n/a) | Ninguna spec OpenAPI en las68 rutas. No ejecutado openapi-lint. | ✓ n/a: sin spec OpenAPI en seis rutas; no ejecutado lint. |
| Docs-style | ✓ (n/a como gate exclusivo de prosa) | Servicio/persistencia con pruebas y descriptores, criterio conservado del pase2. Fragmento `agent-kits/shared/docs-style.md:14–25` leído; no reabro estilo. | ✓ Conservado n/a del ciclo anterior; no hallazgos de requisitos introducidos por la prosa acotada. |
| T-07 corte prospectivo / legado | ✓ | `agent-kits/shared/knowledge-write.md:65–89`, `knowledge-check.md:59–71`; contrato `memory-curation-contract.md:113–126` bajo comparisons. Sin migración/reaprobación/borrado ni accepted=approved; nuevo layout prospectivo `:93–94`. `test_knowledge_curation.py:648–661` preserva legado/journal/índice. | ✓ Conservado, sin cambio ni evidencia nueva en las seis rutas. No reabierto. |
| T-08 persistencia compartida / juicio Curator | ✓ | `knowledge-curation.py:450,562,623`; `agents/knowledge-curator.md:37–46,79–141`: productor propone, Curator semántica, servicio bytes. Revisión/design/QA/Gold/repetición no aprueban; sin nuevo rol/skill. | ✓ Conservado, sin cambio ni evidencia nueva en las seis rutas. No reabierto. |
| Propuesta redactada, portable y exclusiva | ✓ | Servicio `:78–85,153–164,195–204,450–475`: destino128, aliases<=8/255 sólo comparación, reserva en cuatro estados bajo cerrojo, SHA final. Tests `:220–307` conservan aliases/duplicado/redacción y nunca destino por alias. | ✓ Conservado, sin cambio ni evidencia nueva en las seis rutas. No reabierto. |
| SHA original / metadatos finales | ✓ | Servicio `:404–443,562–589`: ID/prefijo, categoría, versión1, índice/colisión y SHA fuente. `_caught:66–76` conserva redactor o fallback seguro. Test dedicado B4 `:207–217` mantiene código/status y árbol intacto sin secreto. | ✓ Conservado, sin cambio ni evidencia nueva en las seis rutas. No reabierto. |
| needs_changes/reject/replacement | ✓ | Servicio `:569–576,585–618`; tests `:415–480`: preserva original/motivo, rejected terminal, sólo approve admite replacement completo ligado al SHA original; nunca edición de approved. | ✓ Conservado, sin cambio ni evidencia nueva en las seis rutas. No reabierto. |
| Gate puro / reglas compartidas | ✓ | `agent-kits/knowledge-curator/curator-gate.py:152–172` delega los mismos validadores del servicio `:421–435`; `test_knowledge_curation.py:664–670` conserva gate0 sin mutación ni transición. | ✓ Conservado, sin cambio ni evidencia nueva en las seis rutas. No reabierto. |
| Intención / recibo / recover | ✓ | Servicio `:299–340,477–507,510–559,623–630`: SHA de ruta exacta, operación hash/verificación y binding antes de `_settle_record`; recover enumera nombres y exige única coincidencia. Tests `:105–205` conservan cortes B1 y añaden misplaced/duplicate sin mutación; `:507–575` preserva cortes/reintentos/cambios/ajenos. No corte eléctrico. | ✓ Conservado, sin cambio ni evidencia nueva en las seis rutas. No reabierto. |
| Concurrencia / IO / OS | ✓ | Servicio `:109–147,166–204,207–290`; tests `:577–646,684–753`: proceso cooperante, enlaces/scan incompleto y fuente ajena conservada. _walk de recover conserva límite4096 y rechaza escaneo no verificable. Dos skips Windows no prueban guards symlink; POSIX/nativo pendientes. | ✓ Conservado, sin cambio ni evidencia nueva en las seis rutas. No reabierto. |
| T-11 productores / fallback / retro tardía | ✓ | Seis agentes, debug-root-cause/retro/bridge siguen el mismo propose sin writer alternativo. `commands/dev-cycle.md:400–428`, `commands/retro.md:24–34`: handoff explícito o ruta/ID pendiente; cierre de retro no aprueba. | ✓ Conservado, sin cambio ni evidencia nueva en las seis rutas. No reabierto. |
| Bridge Gold / nombre / SHA / store | ✓ | `propose-from-case.py:151–164,210–243,274–277`: fórmula ordinaria preservada, acorta sólo slug largo y reserva alias histórico, SHA real servicio. `test_propose_from_case.py:603–701` verifica Gold máximos, cuatro estados, store/config y handoff; sin hash/cambiado conserva tratamientos históricos. | ✓ Conservado, sin cambio ni evidencia nueva en las seis rutas. No reabierto. |
| Journal episódico sin promoción | ✓ | `journal.py:1565–1574,1702–1711,2178–2184`; `test_journal_curation_handoff.py:18–52`: orientación de consulta explícita, fuentes/estado preservados y ausencia de creación de candidates/approved. No aceptación por repetición. | ✓ Conservado, sin cambio ni evidencia nueva en las seis rutas. No reabierto. |
| Confluence / staging | ✓ | `confluence-scope.py:83–85,268–275`, defaults/skill/policy; `test_memory_curation_scope.py:21–58`: exclusión forzada journal/candidates antes de include/casing/staging; approved y originales preservados. No conexión/publicación real. | ✓ Conservado producto; Q23-1 revalidado: workflow y copia :52 incluyen skills/confluence-publish/scripts y son byte-idénticos SHA d8378db84a799058564c69ad12f7e1331ad54c0f191f0bd91366bc3beb810844. No publicación real. |
| T-14 honestidad RED/GREEN/QA | ✓ | `tasks.md:1091–1100`: RED2fallos/5pases, B1 pasaba misma frontera antes del cambio; `:1106–1115`: GREEN267/2skips y consola20sin skips, procesos exactos/SHAs y QA/publicación pendientes. Históricos conservados sin suma como cobertura única ni eficacia/escala/global. | ✓ Revalidado: tasks.md:1195–1201 QA interrumpida no aceptada; :1216–1222 RED5/GREEN570/6skips exactos. XML y recibos coinciden. Sin suma de cohortes, cobertura/gate completo no acreditados. |
| T-15 consola obligatoria nueva | ✓ | A23-1 corregido confirmado2 y conservado: rules `:6–8` snippet, servicio `:20–22`; `test_console_encoding.py:305–306,383–392,730–770` MODOS/pureza medidos y UTF8/emoji/JSON/SHA reales cp1252/ascii. Criterio canónico no relajado. | ✓ Revalidado Q23-2: MODOS :380–387 exige exit0 para envelope UTF8 con emoji; excepción ASCII :303–304 medida :783–796 y no oculta arranque/snippet. Validador :69–79 usa bytes UTF8 y approval_granted=False :60–61. |
| Rama / publicación / macros | ✓ | `tasks.md:14–24,1102–1115`: sólo T-01 cerrada; sin PR/main/release ni B23 publicado/aceptado. Prioridades y skills aplazadas se mantienen; continúa objetivo global, QA/OS/clientes pendientes. | ✓ Revalidado: tasks.md:1224–1230 ciclo nuevo1/max3 separado, objetivo activo/skills aplazadas, sin QA verde/cierre macro/commit/push. |

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A23-1 | Important | Consola | T-11/T-14/T-15 | Corregido; aprobado2 y conservado3 | Snippet/MODOS, oráculos Unicode y criterios intactos. |
| B23-1 | Important | Corte enlace/limpieza de registros | T-08/T-14 | Corregido; confirmado B3 en layout actual | Cortes reales operations/receipts y staging vivo, recover doble y enlaces ajenos. |
| B23-2 | Important | Curator generado incompatible | T-11/T-15 | Corregido; aprobado2 y conservado3 |16 proyecciones individualmente verificadas; check88 propio A3. |
| B23-3 | Important | Gold largo y handoff SHA | T-08/T-14 | Corregido; aprobado2 y conservado3 | Nombre128/hash completo/aliases y store conservados. |
| B23-4 | Important | Secreto en diagnóstico | T-08/T-14 | Corregido; aprobado2 y conservado3 | Redactor/fallback y códigos sin datos crudos. |
| D23-1 | Important | Recarga global de payloads históricos bajo lock | T-08/T-14/T-15 | Corregido, confirmado D3 y sin defecto B3 |801 históricos:802→1 lecturas,62.627.193→78.137B,0 ajenas; cuatro transiciones reales conservadas. |

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| Q23-1 | Important | Suite Confluence omitida en CI | T-14 | Corregido; confirmado A/B/C | Ruta literal en copias idénticas, detector real sin carpetas omitidas; sin permisos/triggers/secrets nuevos. |
| Q23-2 | Important | Metadata consola de plan-review-open | T-14/T-15 | Corregido; confirmado A/B/C | Envelope UTF8 válido y exit0, exención ASCII individual medida; snippet/arranque/negativos preservados, approval_granted=false. |

Informes SHA A `6fd70f0afb0de172d3a33c201f479fe99baa413998a841a40252aa40272a248d`,
B `306d152b53775c9e489919be7419e9bad1353235bb703954897cf4ca4669a3dd`,
C `86ea0dbaf3abd7633069c70ac76d28056a99be5c04f3c1008d166d8954a57f00`.
B ejecutó8 hijos en copia OWN:2 positivos exit0 y6 negativos exit2,
supervisorPID3544 exit0. Wrapper declara cp1252/ascii antes del snippet;
no equivale a host nativo ni pytest/cobertura. A/C no ejecutaron producto.
Jira no publica: no integración/issue en fixture pública ni config consumidor
consultada. Fuente manifest `08d1c109802e46878f1287144529744c37ed04d1b2c9e0b5b1f7ef93cd9f59b4`,
diff `bd215e50f24ce4a8daf0a47f4aab16f62c0c368343e1b4efa96254f4e7742ce2`.
Se habilita segunda QA completa Windows/Linux sobre esa fuente exacta,
con selección CI íntegra, Node/PyYAML QA OWN y cobertura oficial sin redondeo.
El diff de cobertura es el bloque23 entero contra baseline publicado, no
el delta de seis rutas de remediación. Se preserva la primera QA fallida.
La preparación auxiliar intentó decodificar un asset binario inalterado;
falló antes de tests. La continuación verifica la copia exacta y sólo calcula
diff de archivos cambiados; no relaja la lectura ni cambia producto.
QA, commit y push siguen pendientes; skills aplazadas y objetivo activo.

## Continuación técnica — regresiones de hooks (2026-10-10)

Se mantiene el ciclo post-QA: intento1 aceptado, intento2 todavía pendiente.
La segunda QA completa sigue ejecutándose sobre su fuente congelada anterior;
sus fallos se conservan y no se atribuye aceptación a resultados parciales.
No se modifica su fuente, procesos ni registros durante la ejecución.

Corrección acotada a `tests/test_graphiti_security.py`,
`tests/test_knowledge_services.py` y nuevo `tests/hook_security_support.py`:
el recorrido declara las dependencias reales de captura y guardia nativa;
el analizador distingue enumeraciones de runtime usadas como datos de argv;
la excepción AST de `urllib.parse.urlparse` sólo admite el import exacto sin
ocultación de llamadas de red, alias o usos desconocidos. Se conserva la
excepción nominal y condicionada del resumen IA. El espía intercepta sólo
la carga del backend y deja funcionar el lector real de política local.
La huella del launcher se actualiza tras revisar su contenido íntegro;
no se deriva el esperado del fichero bajo prueba. No cambia el producto.

RED previo, conservado por cohortes independientes (sin sumarlas):

| Caso | PID / exit | Resultado | SHA256 JUnit |
|---|---|---|---|
| Enumeraciones, parseo local y dependencias | 10536 /1 |5 fallos,2 pases |3b74edf79c3e60c4fa488841b355f4f62d8bd5f9aee5461ce0a2b73a6d0bf464 |
| Lector real bajo espía |3040 /1 |1 fallo |a440e36fd1144d080d93d2abb0f559e7c9cc87edaec526a21a7effe6c7d8152c |
| Controles positivos/negativos ampliados |25476 /1 |6 fallos,5 pases |693abeca1f9e94128bb63a2f54cf04ff4cf80d00c8b3a3b4f2e6ed8e95e84765 |
| Segundo analizador y control de red |19628 /1 |2 fallos,1 pase |bc6a5fb418b3d18a6ab3555ccb46ed1097e99ed9ef161a463eceb92c18547ee3 |
| Reasignación de constructor argparse |36572 /1 |1 fallo |2e960b3195a9ceca5f97d963f82babc588302f00b3f2efab113f60a0fa8615e2 |

GREEN final dirigido Windows: PID24304 exit0,125 pases,0 fallos/errores/skips;
JUnit SHA256 `988ad2ce47c6b651903e9e921c7c1ece63a97c4561dbb07f5a8abfc23c0bc30b`.
GREEN dirigido Linux: Graphiti74, servicios51 y shell64:189 pases,
0 fallos/errores/skips,75,80s, Pythoncontenedor8/Docker19336/host20724 exit0.
JUnit SHA256 `8fc08fe7c837f58bcc27088175d5b99de25b0e4e42602f4982600265a8fe01c0`;
informe SHA256 `5c47b7f752fb6d5689b49851e74acfc999672bf38f59eea9b343b35a9d2c1eae`.
ROOT leyó informe y recibos finales; fuente1030 exacta y modos intactos,
134 hijos con terminal, contenedor OWN retirado por CID y ausencia comprobada.
Las cohortes Windows/Linux no se suman ni acreditan cobertura, QA completa,
clientes nativos, cierre macro o publicación.

La prueba Linux usa bytes LF conforme `.gitattributes` y modos publicados
100644/100755 en tmpfs nativo. Ocho shell de la copia Windows requieren
normalización CRLF→LF; la copia cruda conserva su SHA y no se modifica ROOT
para ocultar ese error de preparación. La segunda QA copió bytes/modes
inadecuados: esos fallos deben separarse de defectos del producto con evidencia.
La próxima receta preservará bytes canónicos, modos Git y registros JSONL
serializados, además de exigir CTracer oficial activo. No se inicia todavía.

ROOT promovió sólo los tres archivos de pruebas tras comprobar los SHA
originales de ambos tests y la ausencia del helper, conservando inmutable
la fuente dirigida. Quedan revisión2, análisis terminal de QA2, QA completa
corregida, gates y publicación. La ampliación de skills queda para después de
implementar y validar comandos, dashboard, hooks y memoria, según el usuario.

### Fixture de permisos Windows y diagnóstico de router

La segunda QA alcanza una prueba histórica de permisos POSIX que usa chmod
en Windows: `os.access(..., X_OK)` sigue dando true para archivos regulares.
RED aislado del caso original noexec: PID10460 exit1, stderr SHA256
`54b6277f62485658a5134f63fb05079ec6fb502e3035edc319661ac38069f9e7`.
Tras corregir ese caso, la suite completa expone la misma precondición en
hooks.json: PID19724 exit1, stderr SHA256
`cf25616d5aec08dcb0f8f69fa41ab2b9d84501f0bebf19b39da98ffa9abb4aa7`.
Ambos rojos se conservan. `tests/test_lint_plugin.py` simula en un hijo
aislado sólo la respuesta X_OK del path exacto para esos dos casos Windows;
delega el resto de accesos reales. Un control dedicado conserva permisos de
otro hook y el error de path inexistente. POSIX sigue usando chmod real y
el caso de modo Git conserva su índice real, sin simulación ni skip.
No cambia `scripts/lint_plugin.py` ni ningún hook de producto.

GREEN caso original: PID17348 exit0. GREEN suite-script completa final:
PID31000 exit0, stdout SHA256
`a5313733321974d91940bf113076ddecc913f2c34b726c3acedeac5b8644717a`,
stderr vacío. Es evidencia del comportamiento con entrada controlada en
Windows; no acredita permisos POSIX nativos ni la QA completa.
Promoción ROOT guardada por SHA original, nueva huella del test
`bb5bac7ca7a10ee7307e75bb01099faddb8bd8fbfd83ce4b043b6b3533e899a1`.

El fallo QA2 del router documental positivo no se ha reproducido en la
sonda acotada: dos casos (positivo y carrera) pasan con CTracer PID3152 y
con PyTracer PID17652, ambos exit0, con metadatos reales del router.
El positivo conserva origen backend y la carrera degrada a local por
manifest desfasado. No se atribuye el fallo a cobertura por inferencia:
faltan diagnóstico terminal de QA2 y revalidación completa. No hay fix de
producto, relajación de deadline ni aceptación global por estas sondas.
El assert del test de integración incluye ahora `info` para que una nueva
degradación exponga el motivo real en el informe de fallo; su condición y
el presupuesto permanecen intactos.

### Arranque de memoria y puerta de entrenamiento

RED original de SessionStart: PID3300 exit1, dos fallos, JUnit SHA256
`96d9718c3a37415ed6edde4e1807cd7e1dd082e240724bf2cebc4b5b9e22529d`.
La sonda bash-x prueba salida en línea69 por ausencia de python3, antes de
resolver SHARED; no se atribuye a línea81 ni a las barras Windows. `_env`
de `tests/test_memory_path.py` incorpora el shim, Python nativo, SystemRoot
y rutas normalizadas conforme al fixture de shell existente. POSIX y todas
las aserciones se conservan. La ejecución ampliada PID28228 produjo70 pases
y un fallo por ausencia de índice Git en la copia OWN; los siete tests de
memoria pasaron con contexto real, selección por área y topes originales.
JUnit SHA256 `52ce15713f32a9de1c1aad1ff8e39f0c5a436d0dba70621645fc23e3358b173f`.
Tras preparar todos los modos publicados en un índice Git OWN se repitió
sólo ese check: PID9552 exit0,1 pase, JUnit SHA256
`642caa52cf00fbec70e0ee5135b753f8f8c3cb647f0fd55f63bc05a41ee3259e`.
No se declara un intento único de71 pases. ROOT verificó385 hashes de
artefactos y promovió únicamente el fixture con guardia de SHA original.

Dos fallos de entrenamiento se reproducen antes de corregirlos: E22
carecía de ruta de pruebas y el lambda del resolver interpretaba el segundo
argumento timeout como la IP preparada. RED PID7652:2 fallos originales;
RED PID10320:4 variantes de la regresión dedicada. Se conservan ambos.
El spy en `tests/test_training_data_services.py` admite los dos argumentos
y mantiene la resolución privada/pública/None/no-IP preparada; sus asserts
originales y los controles del timeout permanecen activos. E22 en
`docs/agents/CONTRACTS.md` cita el bridge y el servicio compartido, conserva
QA pendiente y no convierte evidencia histórica en aprobación de memoria.
GREEN dirigido PID19468 exit0:6 pases. Suite principal y puerta E22,
PID3364 exit0:161 pases/2 skips de enlaces Windows. Scripts restantes,
PID21788 exit0:598 pases/12 skips OS. Cada skip tiene su razón en el informe;
ninguno acredita symlink/FIFO nativos ni se suma como pase.
ROOT comprobó los stdout/stderr/JUnit completos de las cinco cohortes y
promovió sólo el test y E22, tras comprobar sus SHA originales.
Informe SHA256 `e206377a5473ef91d74e064abd67de37e7ed24d6553a23afc38bd68ac36cc4bc`;
diff SHA256 `16e39bc66eb8aa088ca1feee1275e218427c46211bf7d6fcb8010a474ff1c341`.

La revisión2 del ciclo post-QA puede examinar ahora el delta congelado
mientras QA2 continúa sobre su fuente anterior, intacta. Se mantienen las
24 decisiones originales, seis gaps históricos y Q23-1/Q23-2; no se reabren
sin evidencia nueva. No se lanza QA3 ni se publica antes de analizar la QA2
terminal, completar revisión y verificar todas las puertas necesarias.

## Revisión de dos lentes — intento 2: Remediación post-QA Bloque23 (T-14/T-15) — un Important corregido pendiente de revisión3

Lentes A+B frescas por subagentes genéricos; reviewer nativo no disponible.
Selector PID23076 exit0: C=false/D=false. Scope real PID14652 exit0:
11 en alcance,0 fuera/avisos/excluidos. El despacho mencionaba PID13620;
se usa el terminal real y se conserva el artefacto original. Fuente congelada
1030 archivos, manifest SHA256
`a1fc147808cf757f0fcdb12b9748d73b9d80ebf534a57b146db6157f09e2b9bd`,
diff SHA256 `138fa204f56c565c61f335015cfa773a4a134ab2ed270c82afd70b9fb4db814d`.

A conserva los24 criterios y ocho gaps corregidos del intento1 post-QA.
B reproduce un Important nuevo: el cambio de método del parser desde una
función o mediante alias mantenía indebidamente la exención de datos runtime.
ROOT leyó ambos informes íntegros, comprobó sus hashes y17 artefactos B,
reprodujo el defecto con cinco regresiones dedicadas y lo acepta sin rebate.
Los ✓ de A no anulan el defecto de B; no hay aceptación global del intento2.
Informes A SHA256 `0e164b90a66fbe2258259654c62f8e497f4850a6bb26c330722f3f21e87745a1`,
B SHA256 `9b251e7739102295076489b1911f5870670121ab6bd410fe6221c431794aad95`.

Tabla de continuidad: las referencias al intento1 son evidencia canónica
heredada; no representan una nueva ejecución de esas cohortes.

| # | Criterio | A2 | Continuidad y delta |
|---|---|---|---|
| 1 | T-XX hechas y criterios | ✓ | Intento1 fila1; sólo T-01 completada, sin macro nueva. |
| 2 | Alcance del plan | ✓ | Intento1 fila2; scope11 sin fuera ni exclusiones. |
| 3 | Tests y oráculos reales | ✓ | Intento1 fila3; fixtures y spies reales; B23-QA2-1 acepta un defecto nuevo del scanner. |
| 4 | Constitución explícita | ✓ | Intento1 fila4; stdlib, RED previo, delegación y fuentes generadas conservadas. |
| 5 | Verificación de tareas cerradas | ✓ | Intento1 fila5; T-01 intacta, ninguna verificación faltante se inventa. |
| 6 | Generado al día / E2 | ✓ | Intento1 fila6; delta sin commands/agents/hooks; check autor PID5800 exit0,88 al día. |
| 7 | Descriptores / E3 | ✓ | Intento1 fila7; CONTRACTS E22 incorpora puertas reales manteniendo QA pendiente. |
| 8 | API OpenAPI | n/a | Intento1 fila8; no spec OpenAPI modificada. |
| 9 | Docs-style | n/a | Intento1 fila9; no gate exclusivo de prosa ni reapertura por estilo. |
| 10 | Corte prospectivo / legado | ✓ | Intento1 fila10; sin delta ni migración. |
| 11 | Persistencia compartida / juicio Curator | ✓ | Intento1 fila11; Gold sólo propone, QA no aprueba. |
| 12 | Propuesta redactada / portable / exclusiva | ✓ | Intento1 fila12; propose, aliases y reserva intactos. |
| 13 | SHA original / metadatos finales | ✓ | Intento1 fila13; binding y redactor intactos. |
| 14 | needs_changes / reject / replacement | ✓ | Intento1 fila14; transiciones y original ligado a SHA intactos. |
| 15 | Gate puro / reglas compartidas | ✓ | Intento1 fila15; E22 sólo enumera ejecución, sin transición nueva. |
| 16 | Intención / recibo / recover | ✓ | Intento1 fila16; operación y cortes internos intactos. |
| 17 | Concurrencia / IO / OS | ✓ | Intento1 fila17; fixtures Windows conservan assertions/POSIX; límites explícitos. |
| 18 | Productores / fallback / retro tardía | ✓ | Intento1 fila18; sin delta ni autoaprobación. |
| 19 | Bridge Gold / nombre / SHA / store | ✓ | Intento1 fila19; E22 gate real, store y juicio intactos. |
| 20 | Journal episódico sin promoción | ✓ | Intento1 fila20; nueva clasificación sólo en scanner de tests. |
| 21 | Confluence / staging | ✓ | Intento1 fila21 y Q23-1 conservados; ninguna publicación real. |
| 22 | Honestidad RED / GREEN / QA | ✓ | Intento1 fila22; cohortes separadas, fallos/skips preservados, sin cobertura nueva aceptada. |
| 23 | Consola obligatoria nueva | ✓ | Intento1 fila23 y A23-1/Q23-2 conservados; no CLI nueva del helper. |
| 24 | Rama / publicación / macros | ✓ | Intento1 fila24; QA/gates/push pendientes, skills aplazadas, objetivo activo. |

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B23-QA2-1 | Important | Mutación de parser entre scopes o aliases oculta argv claude | T-14/T-15 | Invalidación conservadora transitiva de aliases y nombres mutados; corregido, pendiente revisión3 | RED5, GREEN130/0skips; no producto modificado. |

A23-1, B23-1..4, D23-1, Q23-1 y Q23-2 permanecen corregidos, sin
reapertura, deuda aceptada ni cambio del ciclo original1–3. Este es el
intento2 del ciclo post-QA existente; el próximo será3/MAX3.

La primera recopilación del test nuevo falló por falta de import pytest,
PID1480 exit2; se conserva como error de preparación, no como RED válido.
Tras corregir sólo ese import, RED PID35640 exit1: cinco fallos del detector,
JUnit SHA256 `88986c4a3cd018be5757e0c9d1f00329971d0ed35d9ada6072ae6433016de0ef`.
GREEN PID25772 exit0:130 pases,0skips, ambas suites completas del scanner,
JUnit SHA256 `ef0427a038557fedff9a01bbb9cf4cb2ca564a7bf484ef50240da1848f8ca0f1`.
ROOT promovió sólo `tests/test_graphiti_security.py` con guardia del SHA
original; se conserva la fuente dirigida. No cambia el producto, el timeout,
los permisos nativos ni el backend. Revisión3 y QA completa siguen pendientes.

Linux dirigido2 aporta otra cohorte independiente:16 pases,0skips,14.36s,
JUnit SHA256 `b78f6ba6f94867b8be2d99b51ce259f445a520b8780cea813d4c0866c89555fb`.
ROOT verificó106 hashes y la identidad AST del helper final, cuyo único
cambio posterior fue whitespace EOF. Git privado mantiene1030 blobs/modos;
el contenedor OWN se retiró por su CID y se comprobó ausencia. No se suma
con189/125/130 ni acredita cobertura o clientes nativos.

La segunda QA Linux terminó:6209 pases,78 fallos,44 skips,6331 casos.
Conserva los75 fallos previamente diagnosticados y tres nuevos pendientes
de corrección/reproducción: fixture del recorte de memoria sin su lector
dependiente y dos verificaciones de snapshot documental. No se atribuyen
éstos a un timeout sin medir. La cobertura de esa ejecución no se acepta:
proveedor PyTracer, aviso trace-changed y gate sin datos agregados válidos.
Windows continúa sobre su snapshot antiguo; su terminal no se inventa.
La ampliación de skills sigue reservada para después de completar y validar
comandos, dashboard, hooks y memoria.

### Diagnóstico y corrección de la fixture final de memoria

El fallo del recorte tiene causa probada: el CLI trasladado a una ruta larga
no incluía `knowledge-view.py` ni sus dependencias locales. El hijo QA2
PID5119 exit0 devuelve total0/reader_unavailable; no alcanza el algoritmo
de recorte. La fixture copia ahora los cuatro siblings reales necesarios,
sin mocks ni cambio de assertions, orden, entradas o topes.
Las tres cohortes independientes sin cobertura/con CTracer/con PyTracer
reproducen6 pases/1 fallo, siempre ese caso. GREEN final CTracer:7 pases,
0skips, JUnit SHA256
`2758ffb2daab4749946f7a1416850196b69b2ab2aebf9cb780aa46f59c89c729`.
Son los mismos siete casos repetidos, no28 casos únicos. El CLI GREEN
devuelve41 entradas/12 candidatos, lectura completa y stderr vacío; la
aserción original comprueba que el render recorta de verdad.

Los dos verify históricos pasan en las cuatro cohortes sin cambiar100ms;
en las tres originales miden2.483–22.770ms. No usan resolver: loopback
IPv4 literal, cero llamadas DNS. No se ha reproducido su fallo ni probado
causa exacta; no hay fix de producto ni aumento de presupuesto.
El test muestra ahora `resultado` y exige explícitamente `comparacion`
antes del acceso ya obligatorio para que una recurrencia conserve el motivo.
Ese cambio diagnóstico se valida por AST/operandos sin repetir el GREEN;
su archivo final se ejecutará en QA completa. No se presenta como reparación
de un timeout ni elimina ninguno de los fallos históricos.

ROOT leyó el informe completo, verificó149 hashes y promovió únicamente
ambos tests con guardias de SHA original. Informe SHA256
`69da7cd4078c8a7b5b3062afbd39306b31ee3986dd2236fd05d6d2b36cba90ac`;
fixture SHA256 `c3afa13b17b1542fa670b762e501b4fe9b5d3699f1dc855a28346c95f687b35c`,
diagnóstico SHA256 `c3459e9538bfa5e8feba4f31d71165cf0b787ead763b2294d5ad485eec6f8840`.
El contenedor OWN fue retirado por su CID tras observar terminal y propietario;
fuentes QA2/final permanecen intactas. No se acredita cobertura por estas sondas.

El preparador OWN de QA3 conserva los14 directorios/6331 IDs anteriores,
siete archivos de producción y ambos umbrales90 sin redondear. Corrige
la auditoría concurrente JSONL y exige CTracer oficial activo; journal.py
sin ejecutables cambiados sigue en la media y aporta0 al denominador
agregado. Denominador global vacío/proveedor no medible no inventan ratios.
23 unidades propias del harness pasan en dos cohortes, sin tests de producto:
lock/shortwrite/IO capturado/dedup/pending/corrupción y binding/MAX3.
La aritmética corregida sobre los datos históricos Linux sigue FAIL:
media71.3220%, changed578/725=79.7241%; trace-changed impide atribuirlos
sólo a ejecución de hijos. No se asume que CTracer resolverá la cobertura.
QA3 aún no ha empezado: necesita revisión3 aceptada y terminal real de
ambas plataformas QA2, además de fuente/receta/pointer ligados por hashes.


## Revisión de dos lentes — intento 3: Fase QA (T-14/T-15) — residual verificado y decisión del orquestador

Lentes A+B+D sobre la fuente de1030 archivos, manifest
`0524e67de8eddac84d2d0a1777a366a1531b3bb9dd9bef2440a8904e7ac6bfee`.
A conserva sus24 criterios y los9 gaps de continuidad; D sin hallazgos.
B confirma el mismo Important B23-QA2-1: `alias = second = p` y
`alias: object = p` ocultan el argv tras mutar `alias.add_argument`.
ROOT verificó informes, recibos, artefactos y fuente; acepta el residual.
La sonda con mock PID9288 exit0 observa argv real y detectores vacíos;
no ejecuta comandos ni red. La corrección previa no cubre esas asignaciones.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B23-QA2-1 | Important | Alias encadenado/anotado no invalida el parser | T-14/T-15 | pendiente; no se acepta intento3 | test_graphiti_security.py:313–339; informe B SHA6727e60b351cc1d398ac1f6be1e9938f431aff50a2e163d6806c367ee447529a |

El ciclo3/MAX3 termina con ese gap. La skill adversarial-review §5 devuelve
la decisión al orquestador/usuario. ROOT decide continuar conforme a la
autorización de completar la implementación: una corrección y un único pase
independiente adicional, contador global4/MAX4. No reinicia ni oculta1–3,
no acepta deuda ni convierte esta fuente rechazada en revisión aceptada.
Los24 criterios y nueve gaps se trasladan íntegros al pase adicional.
Si ese pase conserva un Important, se devuelve una nueva decisión explícita.

QA2 Windows terminó PID21420 exit1:6215 pases,24 fallos,92 skips,
6331 casos y7821.37s. Linux mantiene6209/78/44 sobre6331 casos.
Los10 fallos Windows posteriores al inventario14 se diagnostican en OWN;
no se asumen corregidos ni se relanza QA3. Cobertura, aceptación nativa,
macros, commit/push y cierre global permanecen pendientes.
Sin Jira habilitado en esta ejecución aislada: no publicación externa.
Skills nuevas siguen aplazadas hasta completar comandos/dashboard/hooks/memoria.


### Corrección adicional acotada de B23-QA2-1 — revisión4/MAX4 pendiente

RED: seis regresiones de alias encadenado/anotado, dentro/fuera de función,
desempaquetado y expresión asignada fallaron con `argv claude` ausente:
Python PID18348 exit1 · 2026-10-10 · JUnit SHA256
`0ee68c6b9939f4c93d31463254660b798d33c0d690ce967b3ec460f8be155121`.
Se reproducen variantes del mismo falso negativo, antes de cambiar el detector.
El detector separa las relaciones de alias de las asignaciones que prueban
identidad argparse; recoge Assign, AnnAssign y NamedExpr, con pares
desempaquetados estructuralmente iguales. No concede una identidad nueva a
una asignación ambigua: sólo propaga la invalidez por mutación.

GREEN: Graphiti y knowledge-services completos, Python PID26368 exit0,
136 pases,0 skips,66.44s · JUnit SHA256
`b7fafeec21c576f9e46a7336fadee5395c1503c23c65a8282242ba3e1a95c8c9`.
ROOT verificó terminales, streams, XML y los1030 archivos OWN; sólo cambió
el test/scanner indicado, promovido con guardia SHA original. SHA final
`df76106ed8bdb1db25d7b97f6170aecbe34d3e9d0cb6871bcb64eed4d6c6e5d0`. Changelogs EN/ES actualizados.
No se modifica producto ni se acredita cobertura o QA completa.
La revisión adicional global4/MAX4 necesita fuente final que incluya las
correcciones de QA2 Windows; no se ha lanzado ni se acepta todavía el gap.
La fuente de revisión3 permanece intacta y rechazada, sin reiniciar ciclos.


### QA2 Windows — diagnóstico de los diez fallos nuevos y correcciones acotadas

Inventario: cinco coverage-gate, dos evals y tres lecturas HTTP. En OWN sobre
la fuente exacta de revisión3, PID9308 exit1 reproduce7 fallos y20 pases.
Coverage construía --runner con rutas Windows sin serializar para shlex:
el hijo buscaba un executable sin backslashes y no escribía coverage.json.
La fixture usa shlex.join para el script real y para el runner sin cobertura;
no cambia el parser ni el veredicto de producción.

RED: evals prueba desaparición real del cwd con objetos Git readonly y
visibilidad del fallo de limpieza: PID22904 exit1,2 fallos · 2026-10-10,
JUnit SHA256 `cacb795bd0a43e1b75ba24a4417532c0e08d605e913d543df08e92d51f7e97ff`.
El runner sustituye ignore_errors por limpieza del cwd recién creado y
reintenta sólo unlink de archivo regular readonly Windows dentro de esa ruta,
sin reparse. Un error restante falla el caso, conserva cwd y guarda clase/códigos
sin mensaje bruto. El prefijo eval- valida formato, no acredita propiedad.
El bloque standalone de tests queda al final; Git ausente sólo omite su
regresión específica. Docs EN/ES comparten evals/README.md y changelogs espejados.

GREEN: PID32648,2 regresiones; PID29048,45 casos; refinamientos PID33036,
45 casos; runner sin fichero serializado PID14428,1 caso. Todos exit0 sin
skips; las dos cohortes45 no se suman como90 únicos ni como cobertura.
JUnit final45 SHA256 `419b6bc6e1c2e8364daf93f30d1ff0f9655f4c1675680971e9d64ecc40711b4c`.

HTTP conserva100/1500ms. Tres casos dirigidos pasan sin cambiar producto,
con PyTracer PID13172 y CTracer activo PID33932; verify36.88/20.95ms y
17.52/15.32ms respectivamente, lectura306.52 y118.38ms. No reproducen
los fallos históricos ni demuestran su causa; deadline_read_agotado sólo
es el motivo histórico observado de uno. Se conserva la fuente/terminal
QA2 fallida, no se atribuye su resultado a cobertura válida ni al nuevo fix.

ROOT leyó informe completo y diff, verificó94 artefactos, terminales/XML y
1030 archivos OWN; promovió cuatro rutas con guardias de SHA original.
Informe SHA256 `ab48c88875b4c89256c8ca054ffc4f025757641b0183e49dde262cfc0f762521`;
recibo SHA256 `b9aa49d32042a383e81408b37cc711e4d2c11e08c895b2bdc66a161f64d1a41b`.
Revisión independiente adicional4/MAX4 y QA completa permanecen pendientes.
Sin modelos/hosts nativos, Docker, QA3, aprobación de memoria ni commit/push.
La ampliación de skills sigue aplazada después de comandos/dashboard/hooks/memoria.


## Revisión de dos lentes — intento 4: Fase QA (T-14/T-15) — dos Important verificados y replan acotado

ROOT fusiona A+B sobre el manifest de1030 archivos SHA256
`94aec1d3b603bc6185f33e5ee5726f8abd9f2de9320c31df8ae57b2d226dd45f`.
Selector autor C=false/D=false; reviewer nativo ausente, lentes genéricas con
modelo heredado sin override. Informes, recibos, artefactos y fuente cotejados
por SHA. A conserva24 criterios y tres criterios T-01; criterio4 ahora ✗.
B confirma el mismo B23-QA2-1 en `alias, *rest = p, None, None`: la mutación
no invalida p y los dos detectores omiten el argv observado por el mock.
La sonda PID10956 exit0 no ejecuta hosts, comandos de producto ni red.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B23-QA2-1 | Important | Desempaquetado con estrella conserva el falso negativo | T-14/T-15 | pendiente | tests/test_graphiti_security.py:335–339; informe B SHA d17c90225d71e9cd9aa35f20b137b522b73b900851c0bfa6d75c2518907a59c5 |
| A23-QA4-1 | Important | Nuevo diagnóstico persistido sin redactor compartido | T-14/T-15 | pendiente | evals/run.py:324–325,397; CONSTITUTION.md:34; informe A SHA 1f647b6ceec03f22553088033ca2a99f3a85928299aa6d0c59b6ea71cf1c3172 |

Los ocho gaps históricos A23-1, B23-1..4, D23-1 y Q23-1/Q23-2 siguen
corregidos y conservados con su evidencia original, sin nueva adjudicación.
El noveno B23-QA2-1 sigue pendiente; A23-QA4-1 es el décimo, nuevo Important
aceptado por ROOT contra el principio literal, sin afirmar fuga real.
Se conserva debajo la tabla completa A4 con las columnas de continuidad;
sus ✓ heredados no equivalen a aceptación universal o nueva ejecución.

| # | Tarea | Criterio | ✓/✗ | Evidencia heredada completa | Estado y evidencia delta2 heredados | Juicio y evidencia delta3 | Juicio y evidencia adicional 4/MAX4 |
|---|---|---|---|---|---|---|---|
| 1 | T-01 | T-XX hechas y criterios | ✓ | `docs/roadmap/2026-10-07-catalog-capabilities/tasks.md:46–56`: T-01 conserva sus tres criterios y verificación; única macro completada. `tasks.md:33–40`:1/16; no acepta comparación global. Referencia de traspaso: tasks.md:1246. | ✓ Conservado. tasks.md:48,54–56 y33–40 mantiene única macro T-01 completa, tres criterios y1/16; ninguna nueva macro se cierra. | ✓ Conservado. tasks.md:33–56 mantiene sólo T-01 completada,1/16. Sus tres criterios se desglosan abajo; ninguna macro se cierra en este delta. | ✓ Conservado. tasks.md:33–56 mantiene sólo T-01 completada, 1/16; se conservan sus tres criterios ejecutados. Ninguna macro se cierra. |
| 2 | T-14/T-15/T-16 | Alcance del plan | ✓ | `tasks.md:204,238,248,258` declara agentes/comandos/kits/scripts/tests/skills/docs/interop/changelogs. ROOT scope PID33736 exit0:68 en alcance,0 fuera/avisos/excluidos. `diff-audit.json` reconstruye esas68 rutas; corrección y contrato/oráculos permanecen en ese alcance. Referencia de traspaso: tasks.md:1247. | ✓ Revalidado. tasks.md:239 tests/** y ledger, :250 docs/** y tests/**, :260 ambos changelogs; corresponde QA/documentación del plan:19–21,45–48. Scope terminal PID14652 exit0:11 en alcance,0 fuera/avisos/excluidos. PID13620 del despacho no coincide con terminal y no se usa. | ✓ Revalidado. tasks.md:239,250,260 declara tests/kit/skills/docs y ambos changelogs; plan:19–21,45–48 requiere QA/documentación. Scope PID6176 exit0,6 en alcance,0 fuera/avisos/info/excluidos (terminal y hashes propios comprobados). | ✓ Revalidado. tasks.md:239,250,260 declara evals/**, tests/**, skills/**, ledger y ambos changelogs; plan:19–21,45–48 requiere QA/documentación. Scope PID 28776 exit 0: ocho rutas dentro, cero fuera/avisos/info/excluidos. Limpieza del fixture y serialización del runner son reparación de QA, no ampliación de skills. |
| 3 | T-14 | Tests y oráculos reales | ✓ | `agent-kits/shared/test_knowledge_curation.py:105–205`: cuatro B1 siguen interrumpiendo `os.link` real y rechazando enlace ajeno; D23-1 observa `_read` real, conserva cada byte histórico y recupera cada ID; misplaced/duplicate compara árbol antes/después. `tests/test_console_encoding.py:730–770` conserva oráculos reales Unicode. No fake writer para verde. Referencia de traspaso: tasks.md:1248. | ✓ Revalidado línea a línea: test_graphiti_security.py:2250–2348 prueba datos/argv, parseo/red, rutas y lector local real; test_knowledge_services.py:1379–1404 prueba ambos recorridos; test_lint_plugin.py:497–516 controla noexec/otro/missing. test_training_data_services.py:572–601 separa resolución/timeout y mantiene los asserts; test_memory_path.py:185–284 mantiene payload/contexto/área/topes. test_knowledge_router_read.py:366–371 sólo añade diagnóstico info. No existe % oficial nuevo del diff aceptado: pendiente, sin usar cohortes como cobertura. | ✓ Revalidado. tests/test_graphiti_security.py:308–339,2369–2385 conserva detector real y cinco negativos de mutación/alias/delete; RED5 y GREEN130/0skip ejecutados. test_task_brief.py:1802–1823 copia cuatro dependencias reales, preserves assertions/topes y GREEN7. test_backend_markdown_export.py:278,528–530 mantiene condiciones,100ms y añade sólo dict/presencia. Último archivo diagnóstico sin rerun todavía; tests existentes no equivalen a QA completa. Sin % oficial nuevo aceptado del diff. | ✓ Revalidado línea a línea. test_graphiti_security.py:332–347,2405–2422 recoge Assign/AnnAssign/NamedExpr y exige argv + ofensor real para seis variantes; RED 6/GREEN 136. evals/test_evals.py:402–458 comprueba Git readonly/ausencia real y denegación visible/conservación del sentinel; RED 2/GREEN 2 y cohorte 45. test_coverage_gate.py:160,262 cambia sólo shlex.join; conserva mínimos/diff/exit/asserts. No % oficial nuevo válido del diff. |
| 4 | T-14/T-15 | Constitución explícita | ✓ | `docs/CONSTITUTION.md:10–13,17–21,36–40`: stdlib, dueño único, TDD/regresión dedicada, fuente generada, redactor/no mutación ajena. `tasks.md:1091–1100,1106–1115` conserva RED antes del cambio y GREEN posterior sin QA. `_load_operation:495–506` liga ruta antes de limpiar staging propio. Referencia de traspaso: tasks.md:1249. | ✓ Revalidado contra CONSTITUTION.md:10–13,17–21,26,29,33–38. Tests/soporte stdlib, RED real conservado en tasks.md:1321–1330,1360–1366,1393–1394,1409–1412; controles dedicados y espejos CHANGELOG.md/CHANGELOG.es.md:17–18. No nueva llamada de red hook ni edición manual generada; no aprobación de memoria ni cierre/publicación. | ✓ Revalidado. CONSTITUTION.md:10–13,17–21,26,29,33–38: helper usa stdlib, RED válido precede corrección y cinco regresiones nombradas; mirrors EN/ES actualizados; fuente generada y juicio Curator conservados. Pytest es infraestructura de test existente, no dependencia nueva del producto. El error import PID1480 no cuenta como RED. | ✗ Nuevo A23-QA4-1 Important. CONSTITUTION.md:34 exige que todo texto persistido pase por redact.py. evals/run.py:324–325 crea detalle.cleanup como texto y :397 lo persiste por json.dump sin cargar/invocar ese redactor. El resto conserva stdlib, TDD (tasks.md:1598–1610,1629–1642), fuentes y espejos; no se reabren violaciones previas ajenas al delta. |
| 5 | T-01 | Verificación de tareas cerradas | ✓ | `tasks.md:52` conserva evidencia ejecutada T-01. Las demás tareas permanecen abiertas; `tasks.md:1106–1115` conserva verificación acotada y pendientes explícitos. No ejecuto una verificación faltante para tapar cierre. Referencia de traspaso: tasks.md:1250. | ✓ Conservado. Verificación ejecutada T-01 heredada tasks.md:52 y fila aceptada :1250. El delta no altera Estado ni sus tres criterios; otras15 macros abiertas. No ejecuté ninguna verificación para cubrir falta de evidencia. | ✓ Conservado. tasks.md:52 contiene verificación ejecutada T-01 y :54–56 sus tres checks. Ninguna otra macro cerrada; no ejecuté una verificación para ocultar ausencia. | ✓ Conservado. tasks.md:52 conserva la verificación ejecutada de la única macro cerrada; :54–56 sus tres checks. No ejecuto verificaciones para cubrir evidencia faltante. T-14/T-15 abiertas, T-16 borrador. |
| 6 | T-11/T-15 | Generado al día / E2 | ✓ | Check propio en copia OWN exacta1029: Python PID17500, `-I -X utf8 -B scripts/export-interop.py --check`, exit0, stdout `export-interop --check: 88 ficheros al día`, stderr vacío. `tasks.md:204,248` declara interop y `:1114` evidencia autor; revisión3 todavía en curso sin macro cerrada. Referencia de traspaso: tasks.md:1251. | ✓ n/a al delta11: sólo tests, CONTRACTS, changelogs y ledger; no commands/, agents/ ni hooks/. No ejecuté export. Evidencia autor adicional qa-rem-review2-final-exports/terminal.json PID5800 exit0 y stdout exacto export-interop --check: 88 ficheros al día; hashes stdout/stderr comprobados, separado del check heredado PID17500. | ✓ n/a al delta6: no commands/, agents/ ni hooks/. Prompt A no requiere ejecución propia de export aquí. Autor PID6488 exit0,88 ficheros al día, terminal/streams verificados; separar del check histórico17500. | ✓ n/a al delta ocho: no commands/, agents/ ni hooks/. No ejecuté export-interop; evidencia autor PID 30612 exit 0 y stdout «export-interop --check: 88 ficheros al día», streams cotejados. interop/** declarado en tasks.md:250. No se atribuye como ejecución propia nueva. |
| 7 | T-15 | Descriptores actualizados / E3 | ✓ | `docs/agents/CONTRACTS.md:76–77,85,118–119` E13/E14/E22/E53/E54; `ROLES.md:30–43,89`; seis docs agentes y CONVENTIONS/FLOWS/SPECIALIZATION ES/EN, skills/kits/callers actualizados en el mismo diff. Nuevo layout descrito en contrato `:83–94`, sin nueva promesa global o nativa. Referencia de traspaso: tasks.md:1252. | ✓ Revalidado E3. CONTRACTS.md:85 cambia sólo Puerta E22 por dos rutas existentes del bridge/servicio y conserva QA pendiente/Gold nunca aprueba. test_training_data_services.py:386–407 exige ruta real. CHANGELOG.md/CHANGELOG.es.md:17–18 y tasks.md:1303–1432 describen scanner/espía/fixtures, sin promesa global. Producto/callers sin delta. | ✓ Revalidado. CONTRACTS.md:85,118–119,140–142 conserva E22/E53/E54 y condición E3. Sólo tests/scanner/fixture cambian, sin arista/caller o flujo de producto nuevo; CHANGELOG.md/CHANGELOG.es.md:18,20 y tasks.md:1433–1561 describen exactamente esos cambios y límites en esta tarea. | ✓ Revalidado. CONTRACTS.md:66,140–142 exige E3/espejos. Ninguna arista de productor/caller cambia. evals/README.md:79–85,157–163 describe limpieza/cleanup_error en ES/EN en esta misma tarea; CHANGELOG.md/CHANGELOG.es.md:18,21 y tasks.md:1596–1657 describen scanner/fixtures/runner y límites. No obligación de modificar FLOWS por un flujo del ciclo inexistente en el delta. |
| 8 | T-08/T-11 | API OpenAPI | ✓ | Ninguna spec OpenAPI en las68 rutas. No ejecutado openapi-lint. Referencia de traspaso: tasks.md:1253. | ✓ n/a; las11 rutas no incluyen spec OpenAPI. No ejecutado lint. | ✓ n/a: seis rutas sin spec OpenAPI. No ejecutado openapi-lint. | ✓ n/a: ocho rutas sin spec OpenAPI. No ejecutado openapi-lint. |
| 9 | T-15 | Docs-style | ✓ | Servicio/persistencia con pruebas y descriptores, criterio conservado del pase2. Fragmento `agent-kits/shared/docs-style.md:14–25` leído; no reabro estilo. Referencia de traspaso: tasks.md:1254. | ✓ n/a conservado como gate exclusivo de prosa; sin hallazgo de requisitos ni reapertura por estilo. | ✓ Aplicado a este delta mayoritariamente prosa por líneas; docs-style.md:14–25. tasks.md:1433–1561 y changelogs:18,20 usan evidencia y comparaciones concretas, sin promesa global/nativa. Tabla única de gap :1482–1484 responde al formato obligatorio SKILL §6, no se elimina por preferencia; no hallazgo citable nuevo. | ✓ n/a al criterio adicional de iniciativa mayoritariamente prosa: semántica de código/tests y documentación de QA. docs-style.md:15–22 leído; no se reporta estilo. Tabla de una fila en ledger responde al formato obligatorio SKILL §6. |
| 10 | T-07 | T-07 corte prospectivo / legado | ✓ | `agent-kits/shared/knowledge-write.md:65–89`, `knowledge-check.md:59–71`; contrato `memory-curation-contract.md:113–126` bajo comparisons. Sin migración/reaprobación/borrado ni accepted=approved; nuevo layout prospectivo `:93–94`. `test_knowledge_curation.py:648–661` preserva legado/journal/índice. Referencia de traspaso: tasks.md:1255. | ✓ Conservado. Sin delta al servicio, knowledge-write/check ni contrato de corte prospectivo; evidencia heredada :1255 sigue vigente. | ✓ Conservado. tasks.md:1255,1466; ningún delta a knowledge-write/check/contrato o producto. Legado sin migración/reaprobación. | ✓ Conservado. tasks.md:1255,1466; sin delta a knowledge-write/check/contrato de corte prospectivo. No migración ni reaprobación del legado. |
| 11 | T-08 | T-08 persistencia compartida / juicio Curator | ✓ | `knowledge-curation.py:450,562,623`; `agents/knowledge-curator.md:37–46,79–141`: productor propone, Curator semántica, servicio bytes. Revisión/design/QA/Gold/repetición no aprueban; sin nuevo rol/skill. Referencia de traspaso: tasks.md:1256. | ✓ Conservado. Sin delta al servicio/Curator. CONTRACTS.md:85 conserva explícitamente Gold no aprueba, sólo pending; juicio no delegado a QA. | ✓ Conservado. tasks.md:1256,1467; persistencia/Curator sin delta. QA/Gold no aprueban memoria. | ✓ Conservado. tasks.md:1256,1467; servicio/Curator sin delta. QA/Gold/revisión no aprueban memoria. |
| 12 | T-08 | Propuesta redactada, portable y exclusiva | ✓ | Servicio `:78–85,153–164,195–204,450–475`: destino128, aliases<=8/255 sólo comparación, reserva en cuatro estados bajo cerrojo, SHA final. Tests `:220–307` conservan aliases/duplicado/redacción y nunca destino por alias. Referencia de traspaso: tasks.md:1257. | ✓ Conservado. Sin delta a propose/redactor/alias/reserva; evidencia heredada :1257 intacta. | ✓ Conservado. tasks.md:1257,1468; propose/aliases/reserva/redactor sin delta. | ✓ Conservado. tasks.md:1257,1468; propose/aliases de candidatos/reserva/redactor de memoria sin delta. Aliases del scanner son otro dominio. |
| 13 | T-08 | SHA original / metadatos finales | ✓ | Servicio `:404–443,562–589`: ID/prefijo, categoría, versión1, índice/colisión y SHA fuente. `_caught:66–76` conserva redactor o fallback seguro. Test dedicado B4 `:207–217` mantiene código/status y árbol intacto sin secreto. Referencia de traspaso: tasks.md:1258. | ✓ Conservado. Sin delta a SHA/metadatos/_caught ni test B4; evidencia heredada :1258 intacta. | ✓ Conservado. tasks.md:1258,1469; SHA original/metadatos y test B23-4 sin delta. | ✓ Conservado. tasks.md:1258,1469; SHA/metadatos/_caught y test B23-4 sin delta. |
| 14 | T-08 | needs_changes/reject/replacement | ✓ | Servicio `:569–576,585–618`; tests `:415–480`: preserva original/motivo, rejected terminal, sólo approve admite replacement completo ligado al SHA original; nunca edición de approved. Referencia de traspaso: tasks.md:1259. | ✓ Conservado. Sin delta a transiciones/replacement/terminal rejected; evidencia heredada :1259 intacta. | ✓ Conservado. tasks.md:1259,1470; transiciones y replacement ligados a SHA original sin delta. | ✓ Conservado. tasks.md:1259,1470; transiciones/replacement y rejected terminal sin delta. |
| 15 | T-08 | Gate puro / reglas compartidas | ✓ | `agent-kits/knowledge-curator/curator-gate.py:152–172` delega los mismos validadores del servicio `:421–435`; `test_knowledge_curation.py:664–670` conserva gate0 sin mutación ni transición. Referencia de traspaso: tasks.md:1260. | ✓ Conservado. Sin delta al gate/validadores; E22 sólo enumera su puerta de ejecución, no añade mutación ni transición. | ✓ Conservado. tasks.md:1260,1471 y CONTRACTS.md:85; gate puro y validadores compartidos sin delta. | ✓ Conservado. tasks.md:1260,1471 y CONTRACTS.md:85; gate y validadores compartidos sin delta. |
| 16 | T-08/T-14 | Intención / recibo / recover | ✓ | Servicio `:299–340,477–507,510–559,623–630`: SHA de ruta exacta, operación hash/verificación y binding antes de `_settle_record`; recover enumera nombres y exige única coincidencia. Tests `:105–205` conservan cortes B1 y añaden misplaced/duplicate sin mutación; `:507–575` preserva cortes/reintentos/cambios/ajenos. No corte eléctrico. Referencia de traspaso: tasks.md:1261. | ✓ Conservado. Sin delta a operaciones/recibos/recover ni oráculos de interrupción; evidencia heredada :1261 intacta. | ✓ Conservado. tasks.md:1261,1472; intención/recibo/recover y fronteras reales sin delta. | ✓ Conservado. tasks.md:1261,1472; intención/recibo/recover y cortes reales sin delta. |
| 17 | T-08/T-14 | Concurrencia / IO / OS | ✓ | Servicio `:109–147,166–204,207–290`; tests `:577–646,684–753`: proceso cooperante, enlaces/scan incompleto y fuente ajena conservada. _walk de recover conserva límite4096 y rechaza escaneo no verificable. Dos skips Windows no prueban guards symlink; POSIX/nativo pendientes. Referencia de traspaso: tasks.md:1262. | ✓ Conservado producto. Fixture Windows test_memory_path.py:151–169 ahora aporta shim/SYSTEMROOT/Python coherentes con shell, sin relajar aserciones. test_lint_plugin.py:41–60 simula X_OK sólo del path exacto y :497–516 comprueba delegado/missing. tasks.md:1375–1376,1400–1407,1418–1421 conserva límites, intento fallido y skips; no acredita POSIX/nativo. | ✓ Conservado. tasks.md:1262,1473; ningún cambio producto/OS/permisos. Fixture Linux lector real RED trescohortes6/1 y GREEN7/0skip son selección acotada, no aceptación Windows/POSIX completa ni nativa. | ✓ Conservado producto de curación. tasks.md:1262,1473; no cambio servicio/locks/guards. evals/run.py:134–164 limpia sólo cwd recibido de preparar_cwd, limita retry a unlink regular readonly Windows dentro del cwd y sin reparse; pruebas :402–458 verifican Windows, no aceptación POSIX/nativa completa. |
| 18 | T-11 | T-11 productores / fallback / retro tardía | ✓ | Seis agentes, debug-root-cause/retro/bridge siguen el mismo propose sin writer alternativo. `commands/dev-cycle.md:400–428`, `commands/retro.md:24–34`: handoff explícito o ruta/ID pendiente; cierre de retro no aprueba. Referencia de traspaso: tasks.md:1263. | ✓ Conservado. Sin delta a productores/commands/retro; evidencia heredada :1263 intacta. | ✓ Conservado. tasks.md:1263,1474; productores/retro/commands sin delta. No autoaprobación. | ✓ Conservado. tasks.md:1263,1474; productores, comandos y retro sin delta, sin autoaprobación. |
| 19 | T-08/T-11/T-14 | Bridge Gold / nombre / SHA / store | ✓ | `propose-from-case.py:151–164,210–243,274–277`: fórmula ordinaria preservada, acorta sólo slug largo y reserva alias histórico, SHA real servicio. `test_propose_from_case.py:603–701` verifica Gold máximos, cuatro estados, store/config y handoff; sin hash/cambiado conserva tratamientos históricos. Referencia de traspaso: tasks.md:1264. | ✓ Conservado implementación. E22 CONTRACTS.md:85 incorpora gate real y conserva pending/no aprobación; suites bridge/curation ejecutadas PID3364 exit0:161 pases y2 skips. No cambia nombre/SHA/Gold/store; evidencia heredada :1264. | ✓ Conservado. tasks.md:1264,1475,CONTRACTS.md:85; puente Gold/nombre/SHA/store sin delta. | ✓ Conservado. tasks.md:1264,1475; puente Gold/nombre/SHA/store sin delta. |
| 20 | T-07/T-11 | Journal episódico sin promoción | ✓ | `journal.py:1565–1574,1702–1711,2178–2184`; `test_journal_curation_handoff.py:18–52`: orientación de consulta explícita, fuentes/estado preservados y ausencia de creación de candidates/approved. No aceptación por repetición. Referencia de traspaso: tasks.md:1265. | ✓ Conservado. Sin delta journal/handoff y sin promoción por repetición. Nueva clasificación de runtime en test_graphiti_security.py:292–397 se limita al scanner de tests y no cambia autoridad. | ✓ Conservado. tasks.md:1265,1476; scanner de tests cambia clasificación conservadora, no journal ni autoridad. Journal sigue episódico. | ✓ Conservado. tasks.md:1265,1476; journal/handoff sin delta. Scanner AST sólo modifica una puerta de tests, no autoridad de memoria. |
| 21 | T-07/T-15 | Confluence / staging | ✓ | `confluence-scope.py:83–85,268–275`, defaults/skill/policy; `test_memory_curation_scope.py:21–58`: exclusión forzada journal/candidates antes de include/casing/staging; approved y originales preservados. No conexión/publicación real. Referencia de traspaso: tasks.md:1266. | ✓ Conservado Q23-1 y producto. No delta workflow/copia/confluence-scope ni tests Confluence; evidencia heredada :1266 y gap :1282. | ✓ Conservado. tasks.md:1266,1282,1477; sin cambios a Confluence/staging/CI en delta3. Q23-1 conservado; ninguna conexión o publicación real. | ✓ Conservado. tasks.md:1266,1282,1477; Confluence/staging/CI sin delta. Q23-1 conservado; no conexión/publicación real. |
| 22 | T-14 | T-14 honestidad RED/GREEN/QA | ✓ | `tasks.md:1091–1100`: RED2fallos/5pases, B1 pasaba misma frontera antes del cambio; `:1106–1115`: GREEN267/2skips y consola20sin skips, procesos exactos/SHAs y QA/publicación pendientes. Históricos conservados sin suma como cobertura única ni eficacia/escala/global. Referencia de traspaso: tasks.md:1267. | ✓ Revalidado. tasks.md:1321–1340,1360–1376,1393–1425 coincide con recibos terminal/JUnit por cohortes; se conservan70 pases/1 fallo y correctivo1 pase separado,161/2skips y598/12skips. QA2 anterior permanece pendiente/fallida; no % ni gate/QA completa nuevos aceptados. | ✓ Revalidado. tasks.md:1490–1548 conserva error preparación, RED5/GREEN130, tres RED6/1 y GREEN7; mismos7 repetidos. Dos verify históricos no reproducidos, causa pendiente y100ms intactos; diagnóstico final sin JUnit nuevo. QA2Linux6209/78/44,6331 no se transforma en verde; PyTracer/trace-changed y gates históricos insuficientes. tasks.md:1550–1561 distingue preparación QA3 de ejecución/aceptación. | ✓ Revalidado. tasks.md:1598–1610 conserva RED 6/GREEN 136; :1622–1642 conserva 20/7, RED 2 y verdes 2,45,45 + noop 1 separado. XML/terminales cotejados. :1644–1649 conserva HTTP no reproducido y deadlines, sin causa inventada. :1587–1591 mantiene QA2 Windows 6215/24/92 y Linux 6209/78/44, ambos 6331 FAIL. Sin QA3 ni cobertura válida. |
| 23 | T-15 | T-15 consola obligatoria nueva | ✓ | A23-1 corregido confirmado2 y conservado: rules `:6–8` snippet, servicio `:20–22`; `test_console_encoding.py:305–306,383–392,730–770` MODOS/pureza medidos y UTF8/emoji/JSON/SHA reales cp1252/ascii. Criterio canónico no relajado. Referencia de traspaso: tasks.md:1268. | ✓ Conservado A23-1/Q23-2. Sin delta a rules/MODOS/snippet/validador/oráculos Unicode; evidencia heredada :1268 y :1283. Helper de tests sin CLI nueva; no cambia promesa de consola. | ✓ Conservado. tasks.md:1268,1283,1479; A23-1/Q23-2 sin delta a snippet/MODOS/Unicode. Helper no añade CLI de producto. | ✓ Conservado. tasks.md:1268,1283,1479; snippet/MODOS/Unicode sin delta. evals/run.py:65–69 conserva consola UTF-8; no CLI de producto nueva. A23-1/Q23-2 no se reabren. |
| 24 | T-01..T-16 | Rama / publicación / macros | ✓ | `tasks.md:14–24,1102–1115`: sólo T-01 cerrada; sin PR/main/release ni B23 publicado/aceptado. Prioridades y skills aplazadas se mantienen; continúa objetivo global, QA/OS/clientes pendientes. Referencia de traspaso: tasks.md:1269. | ✓ Revalidado. tasks.md:192,1305–1308,1339–1340,1350–1354,1427–1432 conserva intento2 pendiente, QA2 intacta, macros/publicación/gates pendientes y skills aplazadas después de comandos/dashboard/hooks/memoria; objetivo no cancelado. | ✓ Conservado. tasks.md:14–24,192,1486–1488,1513–1515,1560–1561: ciclo post-QA3/MAX3 sin reset original1–3/post1–2; sólo1/16, skills aplazadas después comandos/dashboard/hooks/memoria; QA/gates/commit/push/cierre global pendientes. | ✓ Conservado. tasks.md:1564–1593 preserva rechazo de intento 3, decisión ROOT de una única revisión adicional global 4/MAX4 y original 1–3/post 1–3 sin reset. :1655–1657 mantiene QA completa/gates/macros/push/cierre pendientes y skills aplazadas después de comandos/dashboard/hooks/memoria. |

Los tres criterios T-01 conservan los455 hashes cotejados,4212 recursos/455
bundles reconciliados y alcance completo sin simular revisión semántica;
verificación ejecutada en tasks.md:52–56. Sólo1/16 macros completadas.

El pase4/MAX4 agota la extensión anterior con0 Critical/2 Important/0 Minor.
Conforme a adversarial-review §5, ROOT toma una decisión explícita de replan:
sustituir el seguimiento creciente de alias por una invalidación conservadora
ante mutaciones relevantes de métodos, y usar el redactor compartido real en
los nuevos diagnósticos de cleanup con fallback fijo seguro. Una sola revisión
independiente adicional, contador global5/MAX5. No se reinician1–3 ni4,
no se acepta deuda; si5 mantiene un Important devuelve otra decisión explícita.
El recibo ROOT4 enlaza el rechazo ROOT3 byte-identico por SHA.

QA2 sigue FAIL en ambas plataformas, QA3 no iniciada y cobertura no aceptada.
Sin Jira habilitado en esta ejecución aislada: ninguna publicación externa.
Commit/push y cierre permanecen pendientes. Skills nuevas aplazadas hasta
completar comandos, dashboard, hooks y memoria, conforme a la prioridad vigente.


### Replan5 — correcciones de B23-QA2-1 y A23-QA4-1, revisión independiente pendiente

RED: B23-QA2-1, siete casos de estrella (prefijo/sufijo/scope anidado),
contenedores list/dict y setattr literal/dinámico fallan antes del cambio:
Python PID21444 exit1,7 fallos · 2026-10-10 · JUnit SHA256
`06d2f7084ed9cf290a0707552a47c3c4ac5c0ea144d3bffa143c122c06547847`. Se exige argv y ofensor del detector real.
El scanner retira el cierre de alias y deja de eximir choices argparse
si encuentra escrituras/borrados de los métodos que prueban identidad o
setattr/delattr con un nombre relevante o no literal. La comprobación
es conservadora en todo el módulo; no demuestra un sandbox de Python.
Comparaciones y choices de argparse sin mutaciones conservan sus controles.
GREEN: Graphiti + knowledge-services completos, PID35096 exit0,
143 pases/0 skips,65.40s · JUnit SHA256 `cf71fc5c353eda142062412392aa25655b42d25830d2a5e5308d0d87a9c6369c`.
ROOT coteja1030 archivos OWN (sólo scanner/test cambia), terminales/streams/XML
y promueve con guardia SHA. SHA final `e442e30839a8d07c3ce8af77eab3bbef4f88c6b9f40c37af7506772585365b90`.

RED: A23-QA4-1, cinco regresiones con marcadores sintéticos en el JSON
fallan antes del cambio, PID22624 exit1 · 2026-10-10 · JUnit SHA256
`8a39a2b9da24f71342b60084f55ec53bba23bd4235a6bdf79ec35c941c67a334`.
run.py carga redact.py por ruta relativa a su propia raíz; diagnóstico y
cwd nuevos de cleanup_error pasan por el redactor real antes de persistir.
Si falta/falla/devuelve no-texto, aviso fijo sin texto del consumidor y
pass=false/checks.cleanup=false; el directorio real permanece retenido.
--keep y campos históricos sin delta. README ES/EN explica ruta redactada.
GREEN dedicado PID37120 exit0,5 pases; evals completo PID13396 exit0,
30 pases/0 skips/12.02s, JUnit SHA256
`3eb34a98b4c46129824fcccac7a45969c07391293b160d188b68228bb1046b95`.
ROOT leyó informe/diff y cotejó34 artefactos y1030 archivos de propuesta,
promoviendo tres rutas con guardias SHA. Los45 hijos reales observados
conservan un exit1 esperado del caso check_json_invalido; no fallo de suite.
No se suman5+30 ni143 como cobertura ni QA completa, ni se acepta revisión5.

ROOT cotejó también32 artefactos y3813 descriptores de la observación QA2.
Windows terminal FAIL6215/24/92 sobre6331, auditoría inutilizable por936
salidas que no coinciden al reutilizar PID/archivo; Linux FAIL6209/78/44,
audit corrupto con4 líneas no vacías y4 vacías inválidas. Counts de procesos
aceptados null en ambas; no reconstrucción, ni auditoría válida inventada.
El helper histórico del observador se conserva byte-idéntico antes de
adaptar la preparación de QA3. Observación root SHA256
`de60b8366148694e11ea038fe9170febd24f62edff5ca12d8d31d509b912f91c`.
QA3 necesita revisión5 aceptada y gates reales; no iniciada. Las dos fuentes
rechazadas3/MAX3 y4/MAX4 permanecen intactas, sin reset. Sin modelos/hosts
nativos, red, publicación de memoria, commit/push o cierre global.


## Revisión de dos lentes — intento 5: Fase QA (T-14/T-15) — redacción corregida y regresión de clase pendiente

ROOT fusiona A+B sobre 1030 rutas públicas, manifest SHA256
`f87527e0739ff7aa9bef32d657debdbfa4694119c676c17baa34ae7af4241300`.
Selector C=false/D=false, lentes genéricas con modelo heredado sin override.
Informes, recibos, artefactos y fuente cotejados; anexos A4/B4 byte-equivalentes
tras lectura de texto conservan íntegro el traspaso. A conserva 24 criterios
y tres de T-01, sin gaps nuevos. A23-QA4-1 corregido: redactor compartido real,
fallback fijo y cinco regresiones RED antes de la reparación, GREEN30 después.
B no identifica otro defecto en evals. ROOT acepta su corrección; QA no cerrada.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B23-QA2-1 | Important | alias.__class__ cambia add_argument sin invalidar p | T-14/T-15 | pendiente; regresión verificada | tests/test_graphiti_security.py:330–340,357–370; mock observa argv, detectores vacíos; PID14436 exit0 |
| A23-QA4-1 | Important | Diagnóstico nuevo persistido sin redactor | T-14/T-15 | corregido, aceptado por ROOT5 | evals/run.py:299–313,342–344; test_evals.py:462–561; RED5/GREEN30, A5/B5 |

La sonda reconstruye el scanner previo sólo revirtiendo hunks del diff,
SHA exacto df76106ed8bdb1db25d7b97f6170aecbe34d3e9d0cb6871bcb64eed4d6c6e5d0.
Ese scanner detecta el mismo caso; el actual no, y el control p.__class__ directo
sí se detecta. Es una regresión concreta del mismo noveno gap, no una exigencia
de sandbox universal ni reapertura de los ocho históricos corregidos. El décimo
A23-QA4-1 queda corregido. Todos los estados y evidencias previos se conservan.
La tabla completa A5 se traslada debajo; conformidad A no elimina el residual B.

| # | Tarea | Criterio | ✓/✗ histórico | Evidencia heredada completa | Estado y evidencia delta2 heredados | Juicio y evidencia delta3 | Juicio y evidencia adicional 4/MAX4 | Juicio y evidencia global5/MAX5 |
|---|---|---|---|---|---|---|---|---|
| 1 | T-01 | T-XX hechas y criterios | ✓ | `docs/roadmap/2026-10-07-catalog-capabilities/tasks.md:46–56`: T-01 conserva sus tres criterios y verificación; única macro completada. `tasks.md:33–40`:1/16; no acepta comparación global. Referencia de traspaso: tasks.md:1246. | ✓ Conservado. tasks.md:48,54–56 y33–40 mantiene única macro T-01 completa, tres criterios y1/16; ninguna nueva macro se cierra. | ✓ Conservado. tasks.md:33–56 mantiene sólo T-01 completada,1/16. Sus tres criterios se desglosan abajo; ninguna macro se cierra en este delta. | ✓ Conservado. tasks.md:33–56 mantiene sólo T-01 completada, 1/16; se conservan sus tres criterios ejecutados. Ninguna macro se cierra. | ✓ Conservado. tasks.md:33–56: sólo T-01 completada,1/16; tres criterios y evidencia ejecutada sin delta. |
| 2 | T-14/T-15/T-16 | Alcance del plan | ✓ | `tasks.md:204,238,248,258` declara agentes/comandos/kits/scripts/tests/skills/docs/interop/changelogs. ROOT scope PID33736 exit0:68 en alcance,0 fuera/avisos/excluidos. `diff-audit.json` reconstruye esas68 rutas; corrección y contrato/oráculos permanecen en ese alcance. Referencia de traspaso: tasks.md:1247. | ✓ Revalidado. tasks.md:239 tests/** y ledger, :250 docs/** y tests/**, :260 ambos changelogs; corresponde QA/documentación del plan:19–21,45–48. Scope terminal PID14652 exit0:11 en alcance,0 fuera/avisos/excluidos. PID13620 del despacho no coincide con terminal y no se usa. | ✓ Revalidado. tasks.md:239,250,260 declara tests/kit/skills/docs y ambos changelogs; plan:19–21,45–48 requiere QA/documentación. Scope PID6176 exit0,6 en alcance,0 fuera/avisos/info/excluidos (terminal y hashes propios comprobados). | ✓ Revalidado. tasks.md:239,250,260 declara evals/**, tests/**, skills/**, ledger y ambos changelogs; plan:19–21,45–48 requiere QA/documentación. Scope PID 28776 exit 0: ocho rutas dentro, cero fuera/avisos/info/excluidos. Limpieza del fixture y serialización del runner son reparación de QA, no ampliación de skills. | ✓ Revalidado. tasks.md:239,250,260 declara tests/**,evals/**,docs/** y ambos changelogs; plan:19–21,45–48 requiere QA/documentación. Scope autor PID9148 exit0,7 dentro,0 fuera/avisos/info/excluidos; reparación acotada QA y replan ROOT4:1714–1726. |
| 3 | T-14 | Tests y oráculos reales | ✓ | `agent-kits/shared/test_knowledge_curation.py:105–205`: cuatro B1 siguen interrumpiendo `os.link` real y rechazando enlace ajeno; D23-1 observa `_read` real, conserva cada byte histórico y recupera cada ID; misplaced/duplicate compara árbol antes/después. `tests/test_console_encoding.py:730–770` conserva oráculos reales Unicode. No fake writer para verde. Referencia de traspaso: tasks.md:1248. | ✓ Revalidado línea a línea: test_graphiti_security.py:2250–2348 prueba datos/argv, parseo/red, rutas y lector local real; test_knowledge_services.py:1379–1404 prueba ambos recorridos; test_lint_plugin.py:497–516 controla noexec/otro/missing. test_training_data_services.py:572–601 separa resolución/timeout y mantiene los asserts; test_memory_path.py:185–284 mantiene payload/contexto/área/topes. test_knowledge_router_read.py:366–371 sólo añade diagnóstico info. No existe % oficial nuevo del diff aceptado: pendiente, sin usar cohortes como cobertura. | ✓ Revalidado. tests/test_graphiti_security.py:308–339,2369–2385 conserva detector real y cinco negativos de mutación/alias/delete; RED5 y GREEN130/0skip ejecutados. test_task_brief.py:1802–1823 copia cuatro dependencias reales, preserves assertions/topes y GREEN7. test_backend_markdown_export.py:278,528–530 mantiene condiciones,100ms y añade sólo dict/presencia. Último archivo diagnóstico sin rerun todavía; tests existentes no equivalen a QA completa. Sin % oficial nuevo aceptado del diff. | ✓ Revalidado línea a línea. test_graphiti_security.py:332–347,2405–2422 recoge Assign/AnnAssign/NamedExpr y exige argv + ofensor real para seis variantes; RED 6/GREEN 136. evals/test_evals.py:402–458 comprueba Git readonly/ausencia real y denegación visible/conservación del sentinel; RED 2/GREEN 2 y cohorte 45. test_coverage_gate.py:160,262 cambia sólo shlex.join; conserva mínimos/diff/exit/asserts. No % oficial nuevo válido del diff. | ✓ Revalidado línea a línea. tests/test_graphiti_security.py:330–340,357–359,2413–2431: guardia conservadora de métodos y siete regresiones argv + detector real; RED7 PID21444/GREEN143 PID35096. evals/test_evals.py:462–561 persiste JSON, espía y delega redactor real, comprueba marcadores ausentes y cuatro fallbacks; RED5 PID22624/GREEN30 PID13396. Sin porcentaje oficial válido para este diff7; cohortes no son cobertura. |
| 4 | T-14/T-15 | Constitución explícita | ✓ | `docs/CONSTITUTION.md:10–13,17–21,36–40`: stdlib, dueño único, TDD/regresión dedicada, fuente generada, redactor/no mutación ajena. `tasks.md:1091–1100,1106–1115` conserva RED antes del cambio y GREEN posterior sin QA. `_load_operation:495–506` liga ruta antes de limpiar staging propio. Referencia de traspaso: tasks.md:1249. | ✓ Revalidado contra CONSTITUTION.md:10–13,17–21,26,29,33–38. Tests/soporte stdlib, RED real conservado en tasks.md:1321–1330,1360–1366,1393–1394,1409–1412; controles dedicados y espejos CHANGELOG.md/CHANGELOG.es.md:17–18. No nueva llamada de red hook ni edición manual generada; no aprobación de memoria ni cierre/publicación. | ✓ Revalidado. CONSTITUTION.md:10–13,17–21,26,29,33–38: helper usa stdlib, RED válido precede corrección y cinco regresiones nombradas; mirrors EN/ES actualizados; fuente generada y juicio Curator conservados. Pytest es infraestructura de test existente, no dependencia nueva del producto. El error import PID1480 no cuenta como RED. | ✗ Nuevo A23-QA4-1 Important. CONSTITUTION.md:34 exige que todo texto persistido pase por redact.py. evals/run.py:324–325 crea detalle.cleanup como texto y :397 lo persiste por json.dump sin cargar/invocar ese redactor. El resto conserva stdlib, TDD (tasks.md:1598–1610,1629–1642), fuentes y espejos; no se reabren violaciones previas ajenas al delta. | ✓ A23-QA4-1 corregido conforme en A5: evals/run.py:299–313,342–344 carga por ruta propia y llama module.redactar antes de json.dump:416; fallback fijo seguro para redactor ausente/fallido/no-texto. CONSTITUTION.md:34 satisfecho; :11–13 evidencia dedicada RED5/GREEN30 tasks.md:1745–1758, stdlib y espejos intactos. |
| 5 | T-01 | Verificación de tareas cerradas | ✓ | `tasks.md:52` conserva evidencia ejecutada T-01. Las demás tareas permanecen abiertas; `tasks.md:1106–1115` conserva verificación acotada y pendientes explícitos. No ejecuto una verificación faltante para tapar cierre. Referencia de traspaso: tasks.md:1250. | ✓ Conservado. Verificación ejecutada T-01 heredada tasks.md:52 y fila aceptada :1250. El delta no altera Estado ni sus tres criterios; otras15 macros abiertas. No ejecuté ninguna verificación para cubrir falta de evidencia. | ✓ Conservado. tasks.md:52 contiene verificación ejecutada T-01 y :54–56 sus tres checks. Ninguna otra macro cerrada; no ejecuté una verificación para ocultar ausencia. | ✓ Conservado. tasks.md:52 conserva la verificación ejecutada de la única macro cerrada; :54–56 sus tres checks. No ejecuto verificaciones para cubrir evidencia faltante. T-14/T-15 abiertas, T-16 borrador. | ✓ Conservado. tasks.md:48,52,54–56: única tarea cerrada y Verificación ejecutada. T-14/T-15 abiertas; T-16 borrador. No ejecuté una verificación faltante para cubrir evidencia. |
| 6 | T-11/T-15 | Generado al día / E2 | ✓ | Check propio en copia OWN exacta1029: Python PID17500, `-I -X utf8 -B scripts/export-interop.py --check`, exit0, stdout `export-interop --check: 88 ficheros al día`, stderr vacío. `tasks.md:204,248` declara interop y `:1114` evidencia autor; revisión3 todavía en curso sin macro cerrada. Referencia de traspaso: tasks.md:1251. | ✓ n/a al delta11: sólo tests, CONTRACTS, changelogs y ledger; no commands/, agents/ ni hooks/. No ejecuté export. Evidencia autor adicional qa-rem-review2-final-exports/terminal.json PID5800 exit0 y stdout exacto export-interop --check: 88 ficheros al día; hashes stdout/stderr comprobados, separado del check heredado PID17500. | ✓ n/a al delta6: no commands/, agents/ ni hooks/. Prompt A no requiere ejecución propia de export aquí. Autor PID6488 exit0,88 ficheros al día, terminal/streams verificados; separar del check histórico17500. | ✓ n/a al delta ocho: no commands/, agents/ ni hooks/. No ejecuté export-interop; evidencia autor PID 30612 exit 0 y stdout «export-interop --check: 88 ficheros al día», streams cotejados. interop/** declarado en tasks.md:250. No se atribuye como ejecución propia nueva. | ✓ n/a: diff7 no toca commands/,agents/ ni hooks/. No ejecuté exportador. Evidencia autor PID27252 exit0, stdout export-interop --check: 88 ficheros al día; hashes de terminal y streams cotejados. tasks.md:250 declara interop/**; separar de check propio históricoPID17500. |
| 7 | T-15 | Descriptores actualizados / E3 | ✓ | `docs/agents/CONTRACTS.md:76–77,85,118–119` E13/E14/E22/E53/E54; `ROLES.md:30–43,89`; seis docs agentes y CONVENTIONS/FLOWS/SPECIALIZATION ES/EN, skills/kits/callers actualizados en el mismo diff. Nuevo layout descrito en contrato `:83–94`, sin nueva promesa global o nativa. Referencia de traspaso: tasks.md:1252. | ✓ Revalidado E3. CONTRACTS.md:85 cambia sólo Puerta E22 por dos rutas existentes del bridge/servicio y conserva QA pendiente/Gold nunca aprueba. test_training_data_services.py:386–407 exige ruta real. CHANGELOG.md/CHANGELOG.es.md:17–18 y tasks.md:1303–1432 describen scanner/espía/fixtures, sin promesa global. Producto/callers sin delta. | ✓ Revalidado. CONTRACTS.md:85,118–119,140–142 conserva E22/E53/E54 y condición E3. Sólo tests/scanner/fixture cambian, sin arista/caller o flujo de producto nuevo; CHANGELOG.md/CHANGELOG.es.md:18,20 y tasks.md:1433–1561 describen exactamente esos cambios y límites en esta tarea. | ✓ Revalidado. CONTRACTS.md:66,140–142 exige E3/espejos. Ninguna arista de productor/caller cambia. evals/README.md:79–85,157–163 describe limpieza/cleanup_error en ES/EN en esta misma tarea; CHANGELOG.md/CHANGELOG.es.md:18,21 y tasks.md:1596–1657 describen scanner/fixtures/runner y límites. No obligación de modificar FLOWS por un flujo del ciclo inexistente en el delta. | ✓ E3 revalidado. CONTRACTS.md:140–142: sin cambio de cadena del ciclo; README evals:84–88,167–171 describe redactor/fallback/ruta retenida ES/EN en esta tarea. CHANGELOG.md/CHANGELOG.es.md:18,21 y tasks.md:1729–1771 describen scanner/redactor y límites; sin nueva autoridad/flujo de memoria. |
| 8 | T-08/T-11 | API OpenAPI | ✓ | Ninguna spec OpenAPI en las68 rutas. No ejecutado openapi-lint. Referencia de traspaso: tasks.md:1253. | ✓ n/a; las11 rutas no incluyen spec OpenAPI. No ejecutado lint. | ✓ n/a: seis rutas sin spec OpenAPI. No ejecutado openapi-lint. | ✓ n/a: ocho rutas sin spec OpenAPI. No ejecutado openapi-lint. | ✓ n/a: siete rutas sin spec OpenAPI; no ejecutado openapi-lint. |
| 9 | T-15 | Docs-style | ✓ | Servicio/persistencia con pruebas y descriptores, criterio conservado del pase2. Fragmento `agent-kits/shared/docs-style.md:14–25` leído; no reabro estilo. Referencia de traspaso: tasks.md:1254. | ✓ n/a conservado como gate exclusivo de prosa; sin hallazgo de requisitos ni reapertura por estilo. | ✓ Aplicado a este delta mayoritariamente prosa por líneas; docs-style.md:14–25. tasks.md:1433–1561 y changelogs:18,20 usan evidencia y comparaciones concretas, sin promesa global/nativa. Tabla única de gap :1482–1484 responde al formato obligatorio SKILL §6, no se elimina por preferencia; no hallazgo citable nuevo. | ✓ n/a al criterio adicional de iniciativa mayoritariamente prosa: semántica de código/tests y documentación de QA. docs-style.md:15–22 leído; no se reporta estilo. Tabla de una fila en ledger responde al formato obligatorio SKILL §6. | ✓ n/a: iniciativa de corrección de código/tests con evidencia documental; docs-style.md:15–22 leído. Sin nueva violación citable de requisitos ni hallazgo de estilo. |
| 10 | T-07 | T-07 corte prospectivo / legado | ✓ | `agent-kits/shared/knowledge-write.md:65–89`, `knowledge-check.md:59–71`; contrato `memory-curation-contract.md:113–126` bajo comparisons. Sin migración/reaprobación/borrado ni accepted=approved; nuevo layout prospectivo `:93–94`. `test_knowledge_curation.py:648–661` preserva legado/journal/índice. Referencia de traspaso: tasks.md:1255. | ✓ Conservado. Sin delta al servicio, knowledge-write/check ni contrato de corte prospectivo; evidencia heredada :1255 sigue vigente. | ✓ Conservado. tasks.md:1255,1466; ningún delta a knowledge-write/check/contrato o producto. Legado sin migración/reaprobación. | ✓ Conservado. tasks.md:1255,1466; sin delta a knowledge-write/check/contrato de corte prospectivo. No migración ni reaprobación del legado. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. |
| 11 | T-08 | T-08 persistencia compartida / juicio Curator | ✓ | `knowledge-curation.py:450,562,623`; `agents/knowledge-curator.md:37–46,79–141`: productor propone, Curator semántica, servicio bytes. Revisión/design/QA/Gold/repetición no aprueban; sin nuevo rol/skill. Referencia de traspaso: tasks.md:1256. | ✓ Conservado. Sin delta al servicio/Curator. CONTRACTS.md:85 conserva explícitamente Gold no aprueba, sólo pending; juicio no delegado a QA. | ✓ Conservado. tasks.md:1256,1467; persistencia/Curator sin delta. QA/Gold no aprueban memoria. | ✓ Conservado. tasks.md:1256,1467; servicio/Curator sin delta. QA/Gold/revisión no aprueban memoria. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. |
| 12 | T-08 | Propuesta redactada, portable y exclusiva | ✓ | Servicio `:78–85,153–164,195–204,450–475`: destino128, aliases<=8/255 sólo comparación, reserva en cuatro estados bajo cerrojo, SHA final. Tests `:220–307` conservan aliases/duplicado/redacción y nunca destino por alias. Referencia de traspaso: tasks.md:1257. | ✓ Conservado. Sin delta a propose/redactor/alias/reserva; evidencia heredada :1257 intacta. | ✓ Conservado. tasks.md:1257,1468; propose/aliases/reserva/redactor sin delta. | ✓ Conservado. tasks.md:1257,1468; propose/aliases de candidatos/reserva/redactor de memoria sin delta. Aliases del scanner son otro dominio. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. |
| 13 | T-08 | SHA original / metadatos finales | ✓ | Servicio `:404–443,562–589`: ID/prefijo, categoría, versión1, índice/colisión y SHA fuente. `_caught:66–76` conserva redactor o fallback seguro. Test dedicado B4 `:207–217` mantiene código/status y árbol intacto sin secreto. Referencia de traspaso: tasks.md:1258. | ✓ Conservado. Sin delta a SHA/metadatos/_caught ni test B4; evidencia heredada :1258 intacta. | ✓ Conservado. tasks.md:1258,1469; SHA original/metadatos y test B23-4 sin delta. | ✓ Conservado. tasks.md:1258,1469; SHA/metadatos/_caught y test B23-4 sin delta. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. |
| 14 | T-08 | needs_changes/reject/replacement | ✓ | Servicio `:569–576,585–618`; tests `:415–480`: preserva original/motivo, rejected terminal, sólo approve admite replacement completo ligado al SHA original; nunca edición de approved. Referencia de traspaso: tasks.md:1259. | ✓ Conservado. Sin delta a transiciones/replacement/terminal rejected; evidencia heredada :1259 intacta. | ✓ Conservado. tasks.md:1259,1470; transiciones y replacement ligados a SHA original sin delta. | ✓ Conservado. tasks.md:1259,1470; transiciones/replacement y rejected terminal sin delta. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. |
| 15 | T-08 | Gate puro / reglas compartidas | ✓ | `agent-kits/knowledge-curator/curator-gate.py:152–172` delega los mismos validadores del servicio `:421–435`; `test_knowledge_curation.py:664–670` conserva gate0 sin mutación ni transición. Referencia de traspaso: tasks.md:1260. | ✓ Conservado. Sin delta al gate/validadores; E22 sólo enumera su puerta de ejecución, no añade mutación ni transición. | ✓ Conservado. tasks.md:1260,1471 y CONTRACTS.md:85; gate puro y validadores compartidos sin delta. | ✓ Conservado. tasks.md:1260,1471 y CONTRACTS.md:85; gate y validadores compartidos sin delta. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. |
| 16 | T-08/T-14 | Intención / recibo / recover | ✓ | Servicio `:299–340,477–507,510–559,623–630`: SHA de ruta exacta, operación hash/verificación y binding antes de `_settle_record`; recover enumera nombres y exige única coincidencia. Tests `:105–205` conservan cortes B1 y añaden misplaced/duplicate sin mutación; `:507–575` preserva cortes/reintentos/cambios/ajenos. No corte eléctrico. Referencia de traspaso: tasks.md:1261. | ✓ Conservado. Sin delta a operaciones/recibos/recover ni oráculos de interrupción; evidencia heredada :1261 intacta. | ✓ Conservado. tasks.md:1261,1472; intención/recibo/recover y fronteras reales sin delta. | ✓ Conservado. tasks.md:1261,1472; intención/recibo/recover y cortes reales sin delta. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. |
| 17 | T-08/T-14 | Concurrencia / IO / OS | ✓ | Servicio `:109–147,166–204,207–290`; tests `:577–646,684–753`: proceso cooperante, enlaces/scan incompleto y fuente ajena conservada. _walk de recover conserva límite4096 y rechaza escaneo no verificable. Dos skips Windows no prueban guards symlink; POSIX/nativo pendientes. Referencia de traspaso: tasks.md:1262. | ✓ Conservado producto. Fixture Windows test_memory_path.py:151–169 ahora aporta shim/SYSTEMROOT/Python coherentes con shell, sin relajar aserciones. test_lint_plugin.py:41–60 simula X_OK sólo del path exacto y :497–516 comprueba delegado/missing. tasks.md:1375–1376,1400–1407,1418–1421 conserva límites, intento fallido y skips; no acredita POSIX/nativo. | ✓ Conservado. tasks.md:1262,1473; ningún cambio producto/OS/permisos. Fixture Linux lector real RED trescohortes6/1 y GREEN7/0skip son selección acotada, no aceptación Windows/POSIX completa ni nativa. | ✓ Conservado producto de curación. tasks.md:1262,1473; no cambio servicio/locks/guards. evals/run.py:134–164 limpia sólo cwd recibido de preparar_cwd, limita retry a unlink regular readonly Windows dentro del cwd y sin reparse; pruebas :402–458 verifican Windows, no aceptación POSIX/nativa completa. | ✓ Conservado producto curación. Scanner sólo cambia puerta de tests. evals/run.py:335–346 conserva limpieza/caso fallido/retención real; redacción no borra ni mueve ruta. test_evals.py:490,525–529,560–561 observa sentinel y JSON. Sin aceptación nueva POSIX/nativa. |
| 18 | T-11 | T-11 productores / fallback / retro tardía | ✓ | Seis agentes, debug-root-cause/retro/bridge siguen el mismo propose sin writer alternativo. `commands/dev-cycle.md:400–428`, `commands/retro.md:24–34`: handoff explícito o ruta/ID pendiente; cierre de retro no aprueba. Referencia de traspaso: tasks.md:1263. | ✓ Conservado. Sin delta a productores/commands/retro; evidencia heredada :1263 intacta. | ✓ Conservado. tasks.md:1263,1474; productores/retro/commands sin delta. No autoaprobación. | ✓ Conservado. tasks.md:1263,1474; productores, comandos y retro sin delta, sin autoaprobación. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. |
| 19 | T-08/T-11/T-14 | Bridge Gold / nombre / SHA / store | ✓ | `propose-from-case.py:151–164,210–243,274–277`: fórmula ordinaria preservada, acorta sólo slug largo y reserva alias histórico, SHA real servicio. `test_propose_from_case.py:603–701` verifica Gold máximos, cuatro estados, store/config y handoff; sin hash/cambiado conserva tratamientos históricos. Referencia de traspaso: tasks.md:1264. | ✓ Conservado implementación. E22 CONTRACTS.md:85 incorpora gate real y conserva pending/no aprobación; suites bridge/curation ejecutadas PID3364 exit0:161 pases y2 skips. No cambia nombre/SHA/Gold/store; evidencia heredada :1264. | ✓ Conservado. tasks.md:1264,1475,CONTRACTS.md:85; puente Gold/nombre/SHA/store sin delta. | ✓ Conservado. tasks.md:1264,1475; puente Gold/nombre/SHA/store sin delta. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. |
| 20 | T-07/T-11 | Journal episódico sin promoción | ✓ | `journal.py:1565–1574,1702–1711,2178–2184`; `test_journal_curation_handoff.py:18–52`: orientación de consulta explícita, fuentes/estado preservados y ausencia de creación de candidates/approved. No aceptación por repetición. Referencia de traspaso: tasks.md:1265. | ✓ Conservado. Sin delta journal/handoff y sin promoción por repetición. Nueva clasificación de runtime en test_graphiti_security.py:292–397 se limita al scanner de tests y no cambia autoridad. | ✓ Conservado. tasks.md:1265,1476; scanner de tests cambia clasificación conservadora, no journal ni autoridad. Journal sigue episódico. | ✓ Conservado. tasks.md:1265,1476; journal/handoff sin delta. Scanner AST sólo modifica una puerta de tests, no autoridad de memoria. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. |
| 21 | T-07/T-15 | Confluence / staging | ✓ | `confluence-scope.py:83–85,268–275`, defaults/skill/policy; `test_memory_curation_scope.py:21–58`: exclusión forzada journal/candidates antes de include/casing/staging; approved y originales preservados. No conexión/publicación real. Referencia de traspaso: tasks.md:1266. | ✓ Conservado Q23-1 y producto. No delta workflow/copia/confluence-scope ni tests Confluence; evidencia heredada :1266 y gap :1282. | ✓ Conservado. tasks.md:1266,1282,1477; sin cambios a Confluence/staging/CI en delta3. Q23-1 conservado; ninguna conexión o publicación real. | ✓ Conservado. tasks.md:1266,1282,1477; Confluence/staging/CI sin delta. Q23-1 conservado; no conexión/publicación real. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. |
| 22 | T-14 | T-14 honestidad RED/GREEN/QA | ✓ | `tasks.md:1091–1100`: RED2fallos/5pases, B1 pasaba misma frontera antes del cambio; `:1106–1115`: GREEN267/2skips y consola20sin skips, procesos exactos/SHAs y QA/publicación pendientes. Históricos conservados sin suma como cobertura única ni eficacia/escala/global. Referencia de traspaso: tasks.md:1267. | ✓ Revalidado. tasks.md:1321–1340,1360–1376,1393–1425 coincide con recibos terminal/JUnit por cohortes; se conservan70 pases/1 fallo y correctivo1 pase separado,161/2skips y598/12skips. QA2 anterior permanece pendiente/fallida; no % ni gate/QA completa nuevos aceptados. | ✓ Revalidado. tasks.md:1490–1548 conserva error preparación, RED5/GREEN130, tres RED6/1 y GREEN7; mismos7 repetidos. Dos verify históricos no reproducidos, causa pendiente y100ms intactos; diagnóstico final sin JUnit nuevo. QA2Linux6209/78/44,6331 no se transforma en verde; PyTracer/trace-changed y gates históricos insuficientes. tasks.md:1550–1561 distingue preparación QA3 de ejecución/aceptación. | ✓ Revalidado. tasks.md:1598–1610 conserva RED 6/GREEN 136; :1622–1642 conserva 20/7, RED 2 y verdes 2,45,45 + noop 1 separado. XML/terminales cotejados. :1644–1649 conserva HTTP no reproducido y deadlines, sin causa inventada. :1587–1591 mantiene QA2 Windows 6215/24/92 y Linux 6209/78/44, ambos 6331 FAIL. Sin QA3 ni cobertura válida. | ✓ Revalidado. tasks.md:1731–1759 conserva RED7/GREEN143 y RED5/GREEN dedicado5/GREEN30 separados, PIDs/XML cotejados; no suma como cobertura/suite única. :1761–1771 y recibo QA2 mantienen FAIL Windows6215/24/92 y Linux6209/78/44, auditorías inutilizable/corrupta, procesos aceptados null, sin QA3. |
| 23 | T-15 | T-15 consola obligatoria nueva | ✓ | A23-1 corregido confirmado2 y conservado: rules `:6–8` snippet, servicio `:20–22`; `test_console_encoding.py:305–306,383–392,730–770` MODOS/pureza medidos y UTF8/emoji/JSON/SHA reales cp1252/ascii. Criterio canónico no relajado. Referencia de traspaso: tasks.md:1268. | ✓ Conservado A23-1/Q23-2. Sin delta a rules/MODOS/snippet/validador/oráculos Unicode; evidencia heredada :1268 y :1283. Helper de tests sin CLI nueva; no cambia promesa de consola. | ✓ Conservado. tasks.md:1268,1283,1479; A23-1/Q23-2 sin delta a snippet/MODOS/Unicode. Helper no añade CLI de producto. | ✓ Conservado. tasks.md:1268,1283,1479; snippet/MODOS/Unicode sin delta. evals/run.py:65–69 conserva consola UTF-8; no CLI de producto nueva. A23-1/Q23-2 no se reabren. | ✓ Conservado A23-1/Q23-2. No delta a consola/MODOS/Unicode; importlib es stdlib y no añade CLI. Evidencia histórica intacta. |
| 24 | T-01..T-16 | Rama / publicación / macros | ✓ | `tasks.md:14–24,1102–1115`: sólo T-01 cerrada; sin PR/main/release ni B23 publicado/aceptado. Prioridades y skills aplazadas se mantienen; continúa objetivo global, QA/OS/clientes pendientes. Referencia de traspaso: tasks.md:1269. | ✓ Revalidado. tasks.md:192,1305–1308,1339–1340,1350–1354,1427–1432 conserva intento2 pendiente, QA2 intacta, macros/publicación/gates pendientes y skills aplazadas después de comandos/dashboard/hooks/memoria; objetivo no cancelado. | ✓ Conservado. tasks.md:14–24,192,1486–1488,1513–1515,1560–1561: ciclo post-QA3/MAX3 sin reset original1–3/post1–2; sólo1/16, skills aplazadas después comandos/dashboard/hooks/memoria; QA/gates/commit/push/cierre global pendientes. | ✓ Conservado. tasks.md:1564–1593 preserva rechazo de intento 3, decisión ROOT de una única revisión adicional global 4/MAX4 y original 1–3/post 1–3 sin reset. :1655–1657 mantiene QA completa/gates/macros/push/cierre pendientes y skills aplazadas después de comandos/dashboard/hooks/memoria. | ✓ Conservado. tasks.md:1714–1726 y ROOT4 preservan rechazo3/MAX3 y4/MAX4; global5/MAX5 único pase explícito replan, sin reset ni deuda. :1759,1769–1771 mantiene revisión5,QA3,gates,cobertura,publicación/macros pendientes; sólo1/16 y skills aplazadas. |

Global5/MAX5 termina con 0 Critical/1 Important/0 Minor. Conforme a la decisión
devuelta por adversarial-review §5, ROOT replantea la invalidación: cualquier
mutación de atributos o setter obliga a conservar la clasificación de argv,
sin enumerar sólo cuatro métodos ni afirmar un análisis universal de Python.
Regresión dedicada de cambio de clase y métodos internos, una revisión fresca
adicional global6/MAX6. Rechazos3/MAX3,4/MAX4 y5/MAX5 quedan intactos y enlazados,
sin reset ni deuda. Si6 retiene un Important vuelve a decisión explícita.

Preparación QA3 para5: 42 unidades OWN actuales pasan PID18112 exit0; las 11
runtime siguen históricas, no repetidas. ROOT cotejó 177 artefactos/copies;
no ejecución autorizada, freeze, pointer, atestación ni QA3. El primer cotejo
ROOT confundió path actual con archive en el índice y falló antes del recibo;
se corrigió sólo el lector de ese esquema y el cotejo final pasó. No RED producto.
La preparación5 no autoriza ni implementa la extensión6: requiere nueva adaptación
desde esta decisión real y revisión aceptada. Ambas QA2 siguen FAIL, sin cobertura
aceptada, clientes/modelos nativos, publicación de memoria, commit/push o cierre.
Skills nuevas permanecen aplazadas tras comandos, dashboard, hooks y memoria.


### Corrección B23-QA2-1 para revisión6/MAX6 — invalidación por cualquier mutación de atributos

La nueva prueba ejecuta sólo el script sintético con subprocess.run mockeado,
observa exactamente el argv de runtimes y después exige su clasificación en
los dos detectores AST reales. Tres variantes nombran el gap: alias.__class__,
setattr de clase y alias._add_action. Ningún hook, modelo, host o red ejecutado.
RED válido: PID38164 exit1, tres AssertionError con argv claude ausente,
sin error de preparación · 2026-10-10 · JUnit SHA256
`4d60cdc8308753b668d6a4787b45178e8a63086bd3a6f5b87c22d5ee3176b720`. La primera fixture omitía import subprocess:
PID39108/6996 fallaron por NameError, no cuentan como RED/GREEN. Se descartó
la guardia escrita tras ese error, restauró el scanner exacto de revisión5,
corrigió sólo el import del test y reescribió la guardia tras el RED válido.
Esos terminales/streams/XML anteriores se conservan sin sustituirlos.

El scanner conserva clasificación de argv cuando encuentra cualquier
Attribute Store/Del o llamada setattr/delattr en el módulo, sin enumerar
cuatro métodos ni volver al análisis de aliases. Esto cubre el cambio de clase
y métodos internos que ya protegía el scanner anterior; una mutación ajena
tampoco prueba identidad argparse. Comparaciones siguen como datos y argparse
sin mutaciones conserva sus controles. Static check conservador, no sandbox.
GREEN: Graphiti + knowledge-services completos, PID19260 exit0,
146 pases/0 skips/48.44s · JUnit SHA256 `3ab3875cb17fa22e2b34d1273a125e91b0f6a57249834ef020c9bb4e2975e618`.
ROOT cotejó terminales/streams/XML y 1030 archivos OWN, uno modificado,
promovido con guardia SHA original. Final `c15cc7c75746e5ac98776cb4f1f4829b912342aaede3a8cca9aecc0b60ec8584`.
Revisión6/MAX6 independiente pendiente, QA3 no iniciada y cobertura no aceptada;
no commit/push ni cierre global. Los rechazos3/4/5 permanecen intactos.


## Revisión de dos lentes — intento 6: Fase QA (T-14/T-15) — correcciones aceptadas; QA completa pendiente

ROOT fusiona A+B, genéricos con contexto fresco/modelo heredado. Selector C=false/D=false.
1030 hashes de fuente coinciden antes/después; informes, recibos e índices íntegros
cotejados: A6 21 artefactos y B6 62. Los anexos A5/B5 son byte exactos;
la tabla conserva las 24 filas y todas sus evidencias anteriores, añadiendo sólo6.
El primer cotejo ROOT falló antes de escribir recibos: el formatter A6 anexó el
juicio6 dentro de la última celda5. ROOT cotejó íntegros todos los campos previos
y el prefijo literal de esa celda; aquí separa el juicio añadido, sin modificar
el informe sellado ni sus veredictos. No fue fallo de producto o nuevo intento.
Tres criterios cerrados T-01 y diez warnings preservados. Rechazos3/4/5
siguen intactos; el pase6/MAX6 procede de la decisión ROOT5 explícita, sin reset.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B23-QA2-1 | Important | Mutación de identidad parser oculta argv | T-14/T-15 | corregido, aceptado ROOT6 | test_graphiti_security.py:326–336,353–355,2431–2454; RED3 PID38164/GREEN146 PID19260; B6 24 sondas OWN PID2396 exit0,14 cuerpos con subprocess mock y cinco controles limpios |
| A23-QA4-1 | Important | Diagnóstico nuevo persistido sin redactor | T-14/T-15 | aceptación ROOT5 conservada | evals/run.py:299–313,342–344; RED5/GREEN30, A5/B5; sin delta6 |

La guardia conservadora retira la exención argparse ante cualquier escritura/borrado
de atributo o setter en el módulo; se verificaron cambios de clase/métodos internos,
aliases, setters y controles limpios. Sin sandbox universal ni ejecución de hooks.
Las fallas propias de preparación de B6 quedan preservadas, no RED de producto.
Sólo la revisión de estas correcciones queda aceptada: 0 Critical/Important/Minor.

| # | Tarea | Criterio | ✓/✗ histórico | Evidencia heredada completa | Estado y evidencia delta2 heredados | Juicio y evidencia delta3 | Juicio y evidencia adicional 4/MAX4 | Juicio y evidencia global5/MAX5 | Juicio y evidencia global6/MAX6 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | T-01 | T-XX hechas y criterios | ✓ | `docs/roadmap/2026-10-07-catalog-capabilities/tasks.md:46–56`: T-01 conserva sus tres criterios y verificación; única macro completada. `tasks.md:33–40`:1/16; no acepta comparación global. Referencia de traspaso: tasks.md:1246. | ✓ Conservado. tasks.md:48,54–56 y33–40 mantiene única macro T-01 completa, tres criterios y1/16; ninguna nueva macro se cierra. | ✓ Conservado. tasks.md:33–56 mantiene sólo T-01 completada,1/16. Sus tres criterios se desglosan abajo; ninguna macro se cierra en este delta. | ✓ Conservado. tasks.md:33–56 mantiene sólo T-01 completada, 1/16; se conservan sus tres criterios ejecutados. Ninguna macro se cierra. | ✓ Conservado. tasks.md:33–56: sólo T-01 completada,1/16; tres criterios y evidencia ejecutada sin delta. | ✓ Conservado. tasks.md:33–56: sólo T-01 completada, 1/16; tres checks y Verificación ejecutada sin delta. |
| 2 | T-14/T-15/T-16 | Alcance del plan | ✓ | `tasks.md:204,238,248,258` declara agentes/comandos/kits/scripts/tests/skills/docs/interop/changelogs. ROOT scope PID33736 exit0:68 en alcance,0 fuera/avisos/excluidos. `diff-audit.json` reconstruye esas68 rutas; corrección y contrato/oráculos permanecen en ese alcance. Referencia de traspaso: tasks.md:1247. | ✓ Revalidado. tasks.md:239 tests/** y ledger, :250 docs/** y tests/**, :260 ambos changelogs; corresponde QA/documentación del plan:19–21,45–48. Scope terminal PID14652 exit0:11 en alcance,0 fuera/avisos/excluidos. PID13620 del despacho no coincide con terminal y no se usa. | ✓ Revalidado. tasks.md:239,250,260 declara tests/kit/skills/docs y ambos changelogs; plan:19–21,45–48 requiere QA/documentación. Scope PID6176 exit0,6 en alcance,0 fuera/avisos/info/excluidos (terminal y hashes propios comprobados). | ✓ Revalidado. tasks.md:239,250,260 declara evals/**, tests/**, skills/**, ledger y ambos changelogs; plan:19–21,45–48 requiere QA/documentación. Scope PID 28776 exit 0: ocho rutas dentro, cero fuera/avisos/info/excluidos. Limpieza del fixture y serialización del runner son reparación de QA, no ampliación de skills. | ✓ Revalidado. tasks.md:239,250,260 declara tests/**,evals/**,docs/** y ambos changelogs; plan:19–21,45–48 requiere QA/documentación. Scope autor PID9148 exit0,7 dentro,0 fuera/avisos/info/excluidos; reparación acotada QA y replan ROOT4:1714–1726. | ✓ Revalidado. tasks.md:239,250,260 declara tests/**, ledger y ambos changelogs; plan:19–21,45–48 y replan ROOT5/tasks.md:1826–1831 acotan esta reparación. Scope autor PID35272 exit0: cuatro dentro, cero fuera/avisos/info/excluidos. |
| 3 | T-14 | Tests y oráculos reales | ✓ | `agent-kits/shared/test_knowledge_curation.py:105–205`: cuatro B1 siguen interrumpiendo `os.link` real y rechazando enlace ajeno; D23-1 observa `_read` real, conserva cada byte histórico y recupera cada ID; misplaced/duplicate compara árbol antes/después. `tests/test_console_encoding.py:730–770` conserva oráculos reales Unicode. No fake writer para verde. Referencia de traspaso: tasks.md:1248. | ✓ Revalidado línea a línea: test_graphiti_security.py:2250–2348 prueba datos/argv, parseo/red, rutas y lector local real; test_knowledge_services.py:1379–1404 prueba ambos recorridos; test_lint_plugin.py:497–516 controla noexec/otro/missing. test_training_data_services.py:572–601 separa resolución/timeout y mantiene los asserts; test_memory_path.py:185–284 mantiene payload/contexto/área/topes. test_knowledge_router_read.py:366–371 sólo añade diagnóstico info. No existe % oficial nuevo del diff aceptado: pendiente, sin usar cohortes como cobertura. | ✓ Revalidado. tests/test_graphiti_security.py:308–339,2369–2385 conserva detector real y cinco negativos de mutación/alias/delete; RED5 y GREEN130/0skip ejecutados. test_task_brief.py:1802–1823 copia cuatro dependencias reales, preserves assertions/topes y GREEN7. test_backend_markdown_export.py:278,528–530 mantiene condiciones,100ms y añade sólo dict/presencia. Último archivo diagnóstico sin rerun todavía; tests existentes no equivalen a QA completa. Sin % oficial nuevo aceptado del diff. | ✓ Revalidado línea a línea. test_graphiti_security.py:332–347,2405–2422 recoge Assign/AnnAssign/NamedExpr y exige argv + ofensor real para seis variantes; RED 6/GREEN 136. evals/test_evals.py:402–458 comprueba Git readonly/ausencia real y denegación visible/conservación del sentinel; RED 2/GREEN 2 y cohorte 45. test_coverage_gate.py:160,262 cambia sólo shlex.join; conserva mínimos/diff/exit/asserts. No % oficial nuevo válido del diff. | ✓ Revalidado línea a línea. tests/test_graphiti_security.py:330–340,357–359,2413–2431: guardia conservadora de métodos y siete regresiones argv + detector real; RED7 PID21444/GREEN143 PID35096. evals/test_evals.py:462–561 persiste JSON, espía y delega redactor real, comprueba marcadores ausentes y cuatro fallbacks; RED5 PID22624/GREEN30 PID13396. Sin porcentaje oficial válido para este diff7; cohortes no son cobertura. | ✓ Revalidado línea a línea. tests/test_graphiti_security.py:2431–2454 nombra B23_QA2_1, observa argv bajo mock antes de exigir argv claude y ofensor en detectores reales. Tres variantes class-alias/class-setter/internal-method-alias. RED3 PID38164/GREEN146 PID19260 cotejados. No porcentaje oficial válido del diff actual; cobertura pendiente, cohortes no equivalen a cobertura. |
| 4 | T-14/T-15 | Constitución explícita | ✓ | `docs/CONSTITUTION.md:10–13,17–21,36–40`: stdlib, dueño único, TDD/regresión dedicada, fuente generada, redactor/no mutación ajena. `tasks.md:1091–1100,1106–1115` conserva RED antes del cambio y GREEN posterior sin QA. `_load_operation:495–506` liga ruta antes de limpiar staging propio. Referencia de traspaso: tasks.md:1249. | ✓ Revalidado contra CONSTITUTION.md:10–13,17–21,26,29,33–38. Tests/soporte stdlib, RED real conservado en tasks.md:1321–1330,1360–1366,1393–1394,1409–1412; controles dedicados y espejos CHANGELOG.md/CHANGELOG.es.md:17–18. No nueva llamada de red hook ni edición manual generada; no aprobación de memoria ni cierre/publicación. | ✓ Revalidado. CONSTITUTION.md:10–13,17–21,26,29,33–38: helper usa stdlib, RED válido precede corrección y cinco regresiones nombradas; mirrors EN/ES actualizados; fuente generada y juicio Curator conservados. Pytest es infraestructura de test existente, no dependencia nueva del producto. El error import PID1480 no cuenta como RED. | ✗ Nuevo A23-QA4-1 Important. CONSTITUTION.md:34 exige que todo texto persistido pase por redact.py. evals/run.py:324–325 crea detalle.cleanup como texto y :397 lo persiste por json.dump sin cargar/invocar ese redactor. El resto conserva stdlib, TDD (tasks.md:1598–1610,1629–1642), fuentes y espejos; no se reabren violaciones previas ajenas al delta. | ✓ A23-QA4-1 corregido conforme en A5: evals/run.py:299–313,342–344 carga por ruta propia y llama module.redactar antes de json.dump:416; fallback fijo seguro para redactor ausente/fallido/no-texto. CONSTITUTION.md:34 satisfecho; :11–13 evidencia dedicada RED5/GREEN30 tasks.md:1745–1758, stdlib y espejos intactos. | ✓ Revalidado. CONSTITUTION.md:11,13 satisfechos por RED válido y test dedicado B23_QA2_1; tasks.md:1850–1856 conserva NameError inválido y descarte/re-escritura. :17–21,26,34–37 sin violación nueva: fuente de pruebas, stdlib, espejos EN/ES, sin cambio de autoridad/red/persistencia de producto. A23-QA4-1 corregido/aceptado ROOT5:1783,1788. |
| 5 | T-01 | Verificación de tareas cerradas | ✓ | `tasks.md:52` conserva evidencia ejecutada T-01. Las demás tareas permanecen abiertas; `tasks.md:1106–1115` conserva verificación acotada y pendientes explícitos. No ejecuto una verificación faltante para tapar cierre. Referencia de traspaso: tasks.md:1250. | ✓ Conservado. Verificación ejecutada T-01 heredada tasks.md:52 y fila aceptada :1250. El delta no altera Estado ni sus tres criterios; otras15 macros abiertas. No ejecuté ninguna verificación para cubrir falta de evidencia. | ✓ Conservado. tasks.md:52 contiene verificación ejecutada T-01 y :54–56 sus tres checks. Ninguna otra macro cerrada; no ejecuté una verificación para ocultar ausencia. | ✓ Conservado. tasks.md:52 conserva la verificación ejecutada de la única macro cerrada; :54–56 sus tres checks. No ejecuto verificaciones para cubrir evidencia faltante. T-14/T-15 abiertas, T-16 borrador. | ✓ Conservado. tasks.md:48,52,54–56: única tarea cerrada y Verificación ejecutada. T-14/T-15 abiertas; T-16 borrador. No ejecuté una verificación faltante para cubrir evidencia. | ✓ Conservado. tasks.md:48,52,54–56 contiene ejecución de Verificación T-01; demás macros abiertas/borrador. Ninguna verificación faltante ejecutada por A6. |
| 6 | T-11/T-15 | Generado al día / E2 | ✓ | Check propio en copia OWN exacta1029: Python PID17500, `-I -X utf8 -B scripts/export-interop.py --check`, exit0, stdout `export-interop --check: 88 ficheros al día`, stderr vacío. `tasks.md:204,248` declara interop y `:1114` evidencia autor; revisión3 todavía en curso sin macro cerrada. Referencia de traspaso: tasks.md:1251. | ✓ n/a al delta11: sólo tests, CONTRACTS, changelogs y ledger; no commands/, agents/ ni hooks/. No ejecuté export. Evidencia autor adicional qa-rem-review2-final-exports/terminal.json PID5800 exit0 y stdout exacto export-interop --check: 88 ficheros al día; hashes stdout/stderr comprobados, separado del check heredado PID17500. | ✓ n/a al delta6: no commands/, agents/ ni hooks/. Prompt A no requiere ejecución propia de export aquí. Autor PID6488 exit0,88 ficheros al día, terminal/streams verificados; separar del check histórico17500. | ✓ n/a al delta ocho: no commands/, agents/ ni hooks/. No ejecuté export-interop; evidencia autor PID 30612 exit 0 y stdout «export-interop --check: 88 ficheros al día», streams cotejados. interop/** declarado en tasks.md:250. No se atribuye como ejecución propia nueva. | ✓ n/a: diff7 no toca commands/,agents/ ni hooks/. No ejecuté exportador. Evidencia autor PID27252 exit0, stdout export-interop --check: 88 ficheros al día; hashes de terminal y streams cotejados. tasks.md:250 declara interop/**; separar de check propio históricoPID17500. | ✓ n/a al delta4: no commands/, agents/ ni hooks/. No ejecuté exportador. Evidencia autor PID20444 exit0, stdout exacto export-interop --check: 88 ficheros al día; terminal/streams cotejados. interop/** declarado tasks.md:250; no nueva obligación de ledger --check de tarea cerrada. |
| 7 | T-15 | Descriptores actualizados / E3 | ✓ | `docs/agents/CONTRACTS.md:76–77,85,118–119` E13/E14/E22/E53/E54; `ROLES.md:30–43,89`; seis docs agentes y CONVENTIONS/FLOWS/SPECIALIZATION ES/EN, skills/kits/callers actualizados en el mismo diff. Nuevo layout descrito en contrato `:83–94`, sin nueva promesa global o nativa. Referencia de traspaso: tasks.md:1252. | ✓ Revalidado E3. CONTRACTS.md:85 cambia sólo Puerta E22 por dos rutas existentes del bridge/servicio y conserva QA pendiente/Gold nunca aprueba. test_training_data_services.py:386–407 exige ruta real. CHANGELOG.md/CHANGELOG.es.md:17–18 y tasks.md:1303–1432 describen scanner/espía/fixtures, sin promesa global. Producto/callers sin delta. | ✓ Revalidado. CONTRACTS.md:85,118–119,140–142 conserva E22/E53/E54 y condición E3. Sólo tests/scanner/fixture cambian, sin arista/caller o flujo de producto nuevo; CHANGELOG.md/CHANGELOG.es.md:18,20 y tasks.md:1433–1561 describen exactamente esos cambios y límites en esta tarea. | ✓ Revalidado. CONTRACTS.md:66,140–142 exige E3/espejos. Ninguna arista de productor/caller cambia. evals/README.md:79–85,157–163 describe limpieza/cleanup_error en ES/EN en esta misma tarea; CHANGELOG.md/CHANGELOG.es.md:18,21 y tasks.md:1596–1657 describen scanner/fixtures/runner y límites. No obligación de modificar FLOWS por un flujo del ciclo inexistente en el delta. | ✓ E3 revalidado. CONTRACTS.md:140–142: sin cambio de cadena del ciclo; README evals:84–88,167–171 describe redactor/fallback/ruta retenida ES/EN en esta tarea. CHANGELOG.md/CHANGELOG.es.md:18,21 y tasks.md:1729–1771 describen scanner/redactor y límites; sin nueva autoridad/flujo de memoria. | ✓ Revalidado. CONTRACTS.md:140–142 no introduce E2/flujo E3 nuevo. CHANGELOG.md/CHANGELOG.es.md:18 describen class/internal/setters en ESTA tarea; tasks.md:1844–1869 documenta guardia/pruebas/límites actuales. No cambio de productor/caller/autoridad de memoria. |
| 8 | T-08/T-11 | API OpenAPI | ✓ | Ninguna spec OpenAPI en las68 rutas. No ejecutado openapi-lint. Referencia de traspaso: tasks.md:1253. | ✓ n/a; las11 rutas no incluyen spec OpenAPI. No ejecutado lint. | ✓ n/a: seis rutas sin spec OpenAPI. No ejecutado openapi-lint. | ✓ n/a: ocho rutas sin spec OpenAPI. No ejecutado openapi-lint. | ✓ n/a: siete rutas sin spec OpenAPI; no ejecutado openapi-lint. | ✓ n/a: cuatro rutas sin spec OpenAPI; no ejecutado openapi-lint. |
| 9 | T-15 | Docs-style | ✓ | Servicio/persistencia con pruebas y descriptores, criterio conservado del pase2. Fragmento `agent-kits/shared/docs-style.md:14–25` leído; no reabro estilo. Referencia de traspaso: tasks.md:1254. | ✓ n/a conservado como gate exclusivo de prosa; sin hallazgo de requisitos ni reapertura por estilo. | ✓ Aplicado a este delta mayoritariamente prosa por líneas; docs-style.md:14–25. tasks.md:1433–1561 y changelogs:18,20 usan evidencia y comparaciones concretas, sin promesa global/nativa. Tabla única de gap :1482–1484 responde al formato obligatorio SKILL §6, no se elimina por preferencia; no hallazgo citable nuevo. | ✓ n/a al criterio adicional de iniciativa mayoritariamente prosa: semántica de código/tests y documentación de QA. docs-style.md:15–22 leído; no se reporta estilo. Tabla de una fila en ledger responde al formato obligatorio SKILL §6. | ✓ n/a: iniciativa de corrección de código/tests con evidencia documental; docs-style.md:15–22 leído. Sin nueva violación citable de requisitos ni hallazgo de estilo. | ✓ Conservado; docs-style.md:15–22 leído para la evidencia documental del delta. No gap de requisito/constitución ni reapertura por estilo. |
| 10 | T-07 | T-07 corte prospectivo / legado | ✓ | `agent-kits/shared/knowledge-write.md:65–89`, `knowledge-check.md:59–71`; contrato `memory-curation-contract.md:113–126` bajo comparisons. Sin migración/reaprobación/borrado ni accepted=approved; nuevo layout prospectivo `:93–94`. `test_knowledge_curation.py:648–661` preserva legado/journal/índice. Referencia de traspaso: tasks.md:1255. | ✓ Conservado. Sin delta al servicio, knowledge-write/check ni contrato de corte prospectivo; evidencia heredada :1255 sigue vigente. | ✓ Conservado. tasks.md:1255,1466; ningún delta a knowledge-write/check/contrato o producto. Legado sin migración/reaprobación. | ✓ Conservado. tasks.md:1255,1466; sin delta a knowledge-write/check/contrato de corte prospectivo. No migración ni reaprobación del legado. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. | ✓ Conservado íntegro. Sin delta semántico a fuente/test/contrato de este criterio en las cuatro rutas. Evidencia original y delta2/3/4/5 permanece en esta fila y anexos; sin nueva ejecución, aceptación global ni adjudicación. |
| 11 | T-08 | T-08 persistencia compartida / juicio Curator | ✓ | `knowledge-curation.py:450,562,623`; `agents/knowledge-curator.md:37–46,79–141`: productor propone, Curator semántica, servicio bytes. Revisión/design/QA/Gold/repetición no aprueban; sin nuevo rol/skill. Referencia de traspaso: tasks.md:1256. | ✓ Conservado. Sin delta al servicio/Curator. CONTRACTS.md:85 conserva explícitamente Gold no aprueba, sólo pending; juicio no delegado a QA. | ✓ Conservado. tasks.md:1256,1467; persistencia/Curator sin delta. QA/Gold no aprueban memoria. | ✓ Conservado. tasks.md:1256,1467; servicio/Curator sin delta. QA/Gold/revisión no aprueban memoria. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. | ✓ Conservado íntegro. Sin delta semántico a fuente/test/contrato de este criterio en las cuatro rutas. Evidencia original y delta2/3/4/5 permanece en esta fila y anexos; sin nueva ejecución, aceptación global ni adjudicación. |
| 12 | T-08 | Propuesta redactada, portable y exclusiva | ✓ | Servicio `:78–85,153–164,195–204,450–475`: destino128, aliases<=8/255 sólo comparación, reserva en cuatro estados bajo cerrojo, SHA final. Tests `:220–307` conservan aliases/duplicado/redacción y nunca destino por alias. Referencia de traspaso: tasks.md:1257. | ✓ Conservado. Sin delta a propose/redactor/alias/reserva; evidencia heredada :1257 intacta. | ✓ Conservado. tasks.md:1257,1468; propose/aliases/reserva/redactor sin delta. | ✓ Conservado. tasks.md:1257,1468; propose/aliases de candidatos/reserva/redactor de memoria sin delta. Aliases del scanner son otro dominio. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. | ✓ Conservado íntegro. Sin delta semántico a fuente/test/contrato de este criterio en las cuatro rutas. Evidencia original y delta2/3/4/5 permanece en esta fila y anexos; sin nueva ejecución, aceptación global ni adjudicación. |
| 13 | T-08 | SHA original / metadatos finales | ✓ | Servicio `:404–443,562–589`: ID/prefijo, categoría, versión1, índice/colisión y SHA fuente. `_caught:66–76` conserva redactor o fallback seguro. Test dedicado B4 `:207–217` mantiene código/status y árbol intacto sin secreto. Referencia de traspaso: tasks.md:1258. | ✓ Conservado. Sin delta a SHA/metadatos/_caught ni test B4; evidencia heredada :1258 intacta. | ✓ Conservado. tasks.md:1258,1469; SHA original/metadatos y test B23-4 sin delta. | ✓ Conservado. tasks.md:1258,1469; SHA/metadatos/_caught y test B23-4 sin delta. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. | ✓ Conservado íntegro. Sin delta semántico a fuente/test/contrato de este criterio en las cuatro rutas. Evidencia original y delta2/3/4/5 permanece en esta fila y anexos; sin nueva ejecución, aceptación global ni adjudicación. |
| 14 | T-08 | needs_changes/reject/replacement | ✓ | Servicio `:569–576,585–618`; tests `:415–480`: preserva original/motivo, rejected terminal, sólo approve admite replacement completo ligado al SHA original; nunca edición de approved. Referencia de traspaso: tasks.md:1259. | ✓ Conservado. Sin delta a transiciones/replacement/terminal rejected; evidencia heredada :1259 intacta. | ✓ Conservado. tasks.md:1259,1470; transiciones y replacement ligados a SHA original sin delta. | ✓ Conservado. tasks.md:1259,1470; transiciones/replacement y rejected terminal sin delta. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. | ✓ Conservado íntegro. Sin delta semántico a fuente/test/contrato de este criterio en las cuatro rutas. Evidencia original y delta2/3/4/5 permanece en esta fila y anexos; sin nueva ejecución, aceptación global ni adjudicación. |
| 15 | T-08 | Gate puro / reglas compartidas | ✓ | `agent-kits/knowledge-curator/curator-gate.py:152–172` delega los mismos validadores del servicio `:421–435`; `test_knowledge_curation.py:664–670` conserva gate0 sin mutación ni transición. Referencia de traspaso: tasks.md:1260. | ✓ Conservado. Sin delta al gate/validadores; E22 sólo enumera su puerta de ejecución, no añade mutación ni transición. | ✓ Conservado. tasks.md:1260,1471 y CONTRACTS.md:85; gate puro y validadores compartidos sin delta. | ✓ Conservado. tasks.md:1260,1471 y CONTRACTS.md:85; gate y validadores compartidos sin delta. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. | ✓ Conservado íntegro. Sin delta semántico a fuente/test/contrato de este criterio en las cuatro rutas. Evidencia original y delta2/3/4/5 permanece en esta fila y anexos; sin nueva ejecución, aceptación global ni adjudicación. |
| 16 | T-08/T-14 | Intención / recibo / recover | ✓ | Servicio `:299–340,477–507,510–559,623–630`: SHA de ruta exacta, operación hash/verificación y binding antes de `_settle_record`; recover enumera nombres y exige única coincidencia. Tests `:105–205` conservan cortes B1 y añaden misplaced/duplicate sin mutación; `:507–575` preserva cortes/reintentos/cambios/ajenos. No corte eléctrico. Referencia de traspaso: tasks.md:1261. | ✓ Conservado. Sin delta a operaciones/recibos/recover ni oráculos de interrupción; evidencia heredada :1261 intacta. | ✓ Conservado. tasks.md:1261,1472; intención/recibo/recover y fronteras reales sin delta. | ✓ Conservado. tasks.md:1261,1472; intención/recibo/recover y cortes reales sin delta. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. | ✓ Conservado íntegro. Sin delta semántico a fuente/test/contrato de este criterio en las cuatro rutas. Evidencia original y delta2/3/4/5 permanece en esta fila y anexos; sin nueva ejecución, aceptación global ni adjudicación. |
| 17 | T-08/T-14 | Concurrencia / IO / OS | ✓ | Servicio `:109–147,166–204,207–290`; tests `:577–646,684–753`: proceso cooperante, enlaces/scan incompleto y fuente ajena conservada. _walk de recover conserva límite4096 y rechaza escaneo no verificable. Dos skips Windows no prueban guards symlink; POSIX/nativo pendientes. Referencia de traspaso: tasks.md:1262. | ✓ Conservado producto. Fixture Windows test_memory_path.py:151–169 ahora aporta shim/SYSTEMROOT/Python coherentes con shell, sin relajar aserciones. test_lint_plugin.py:41–60 simula X_OK sólo del path exacto y :497–516 comprueba delegado/missing. tasks.md:1375–1376,1400–1407,1418–1421 conserva límites, intento fallido y skips; no acredita POSIX/nativo. | ✓ Conservado. tasks.md:1262,1473; ningún cambio producto/OS/permisos. Fixture Linux lector real RED trescohortes6/1 y GREEN7/0skip son selección acotada, no aceptación Windows/POSIX completa ni nativa. | ✓ Conservado producto de curación. tasks.md:1262,1473; no cambio servicio/locks/guards. evals/run.py:134–164 limpia sólo cwd recibido de preparar_cwd, limita retry a unlink regular readonly Windows dentro del cwd y sin reparse; pruebas :402–458 verifican Windows, no aceptación POSIX/nativa completa. | ✓ Conservado producto curación. Scanner sólo cambia puerta de tests. evals/run.py:335–346 conserva limpieza/caso fallido/retención real; redacción no borra ni mueve ruta. test_evals.py:490,525–529,560–561 observa sentinel y JSON. Sin aceptación nueva POSIX/nativa. | ✓ Conservado íntegro. Sin delta semántico a fuente/test/contrato de este criterio en las cuatro rutas. Evidencia original y delta2/3/4/5 permanece en esta fila y anexos; sin nueva ejecución, aceptación global ni adjudicación. |
| 18 | T-11 | T-11 productores / fallback / retro tardía | ✓ | Seis agentes, debug-root-cause/retro/bridge siguen el mismo propose sin writer alternativo. `commands/dev-cycle.md:400–428`, `commands/retro.md:24–34`: handoff explícito o ruta/ID pendiente; cierre de retro no aprueba. Referencia de traspaso: tasks.md:1263. | ✓ Conservado. Sin delta a productores/commands/retro; evidencia heredada :1263 intacta. | ✓ Conservado. tasks.md:1263,1474; productores/retro/commands sin delta. No autoaprobación. | ✓ Conservado. tasks.md:1263,1474; productores, comandos y retro sin delta, sin autoaprobación. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. | ✓ Conservado íntegro. Sin delta semántico a fuente/test/contrato de este criterio en las cuatro rutas. Evidencia original y delta2/3/4/5 permanece en esta fila y anexos; sin nueva ejecución, aceptación global ni adjudicación. |
| 19 | T-08/T-11/T-14 | Bridge Gold / nombre / SHA / store | ✓ | `propose-from-case.py:151–164,210–243,274–277`: fórmula ordinaria preservada, acorta sólo slug largo y reserva alias histórico, SHA real servicio. `test_propose_from_case.py:603–701` verifica Gold máximos, cuatro estados, store/config y handoff; sin hash/cambiado conserva tratamientos históricos. Referencia de traspaso: tasks.md:1264. | ✓ Conservado implementación. E22 CONTRACTS.md:85 incorpora gate real y conserva pending/no aprobación; suites bridge/curation ejecutadas PID3364 exit0:161 pases y2 skips. No cambia nombre/SHA/Gold/store; evidencia heredada :1264. | ✓ Conservado. tasks.md:1264,1475,CONTRACTS.md:85; puente Gold/nombre/SHA/store sin delta. | ✓ Conservado. tasks.md:1264,1475; puente Gold/nombre/SHA/store sin delta. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. | ✓ Conservado íntegro. Sin delta semántico a fuente/test/contrato de este criterio en las cuatro rutas. Evidencia original y delta2/3/4/5 permanece en esta fila y anexos; sin nueva ejecución, aceptación global ni adjudicación. |
| 20 | T-07/T-11 | Journal episódico sin promoción | ✓ | `journal.py:1565–1574,1702–1711,2178–2184`; `test_journal_curation_handoff.py:18–52`: orientación de consulta explícita, fuentes/estado preservados y ausencia de creación de candidates/approved. No aceptación por repetición. Referencia de traspaso: tasks.md:1265. | ✓ Conservado. Sin delta journal/handoff y sin promoción por repetición. Nueva clasificación de runtime en test_graphiti_security.py:292–397 se limita al scanner de tests y no cambia autoridad. | ✓ Conservado. tasks.md:1265,1476; scanner de tests cambia clasificación conservadora, no journal ni autoridad. Journal sigue episódico. | ✓ Conservado. tasks.md:1265,1476; journal/handoff sin delta. Scanner AST sólo modifica una puerta de tests, no autoridad de memoria. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. | ✓ Conservado íntegro. Sin delta semántico a fuente/test/contrato de este criterio en las cuatro rutas. Evidencia original y delta2/3/4/5 permanece en esta fila y anexos; sin nueva ejecución, aceptación global ni adjudicación. |
| 21 | T-07/T-15 | Confluence / staging | ✓ | `confluence-scope.py:83–85,268–275`, defaults/skill/policy; `test_memory_curation_scope.py:21–58`: exclusión forzada journal/candidates antes de include/casing/staging; approved y originales preservados. No conexión/publicación real. Referencia de traspaso: tasks.md:1266. | ✓ Conservado Q23-1 y producto. No delta workflow/copia/confluence-scope ni tests Confluence; evidencia heredada :1266 y gap :1282. | ✓ Conservado. tasks.md:1266,1282,1477; sin cambios a Confluence/staging/CI en delta3. Q23-1 conservado; ninguna conexión o publicación real. | ✓ Conservado. tasks.md:1266,1282,1477; Confluence/staging/CI sin delta. Q23-1 conservado; no conexión/publicación real. | ✓ Conservado íntegro: sin delta semántico a la fuente/test/contrato de este criterio en las siete rutas; todas sus evidencias y límites originales/delta2/delta3/A4 permanecen en esta fila y anexo. Sin nueva ejecución o adjudicación. | ✓ Conservado íntegro. Sin delta semántico a fuente/test/contrato de este criterio en las cuatro rutas. Evidencia original y delta2/3/4/5 permanece en esta fila y anexos; sin nueva ejecución, aceptación global ni adjudicación. |
| 22 | T-14 | T-14 honestidad RED/GREEN/QA | ✓ | `tasks.md:1091–1100`: RED2fallos/5pases, B1 pasaba misma frontera antes del cambio; `:1106–1115`: GREEN267/2skips y consola20sin skips, procesos exactos/SHAs y QA/publicación pendientes. Históricos conservados sin suma como cobertura única ni eficacia/escala/global. Referencia de traspaso: tasks.md:1267. | ✓ Revalidado. tasks.md:1321–1340,1360–1376,1393–1425 coincide con recibos terminal/JUnit por cohortes; se conservan70 pases/1 fallo y correctivo1 pase separado,161/2skips y598/12skips. QA2 anterior permanece pendiente/fallida; no % ni gate/QA completa nuevos aceptados. | ✓ Revalidado. tasks.md:1490–1548 conserva error preparación, RED5/GREEN130, tres RED6/1 y GREEN7; mismos7 repetidos. Dos verify históricos no reproducidos, causa pendiente y100ms intactos; diagnóstico final sin JUnit nuevo. QA2Linux6209/78/44,6331 no se transforma en verde; PyTracer/trace-changed y gates históricos insuficientes. tasks.md:1550–1561 distingue preparación QA3 de ejecución/aceptación. | ✓ Revalidado. tasks.md:1598–1610 conserva RED 6/GREEN 136; :1622–1642 conserva 20/7, RED 2 y verdes 2,45,45 + noop 1 separado. XML/terminales cotejados. :1644–1649 conserva HTTP no reproducido y deadlines, sin causa inventada. :1587–1591 mantiene QA2 Windows 6215/24/92 y Linux 6209/78/44, ambos 6331 FAIL. Sin QA3 ni cobertura válida. | ✓ Revalidado. tasks.md:1731–1759 conserva RED7/GREEN143 y RED5/GREEN dedicado5/GREEN30 separados, PIDs/XML cotejados; no suma como cobertura/suite única. :1761–1771 y recibo QA2 mantienen FAIL Windows6215/24/92 y Linux6209/78/44, auditorías inutilizable/corrupta, procesos aceptados null, sin QA3. | ✓ Revalidado. tasks.md:1850–1856 separa NameError PID39108/6996 de RED válido3 PID38164; :1864–1869 conserva GREEN146/0skip/48.44s, SHAs XML y revisión6/QA3/cobertura pendientes. Terminales, streams y casos JUnit cotejados; no suma como QA global. |
| 23 | T-15 | T-15 consola obligatoria nueva | ✓ | A23-1 corregido confirmado2 y conservado: rules `:6–8` snippet, servicio `:20–22`; `test_console_encoding.py:305–306,383–392,730–770` MODOS/pureza medidos y UTF8/emoji/JSON/SHA reales cp1252/ascii. Criterio canónico no relajado. Referencia de traspaso: tasks.md:1268. | ✓ Conservado A23-1/Q23-2. Sin delta a rules/MODOS/snippet/validador/oráculos Unicode; evidencia heredada :1268 y :1283. Helper de tests sin CLI nueva; no cambia promesa de consola. | ✓ Conservado. tasks.md:1268,1283,1479; A23-1/Q23-2 sin delta a snippet/MODOS/Unicode. Helper no añade CLI de producto. | ✓ Conservado. tasks.md:1268,1283,1479; snippet/MODOS/Unicode sin delta. evals/run.py:65–69 conserva consola UTF-8; no CLI de producto nueva. A23-1/Q23-2 no se reabren. | ✓ Conservado A23-1/Q23-2. No delta a consola/MODOS/Unicode; importlib es stdlib y no añade CLI. Evidencia histórica intacta. | ✓ Conservado. tasks.md:1268,1283 y tests/test_graphiti_security.py:2437 import subprocess local: no CLI nueva ni delta a consola/MODOS/oráculos Unicode; A23-1/Q23-2 intactos. |
| 24 | T-01..T-16 | Rama / publicación / macros | ✓ | `tasks.md:14–24,1102–1115`: sólo T-01 cerrada; sin PR/main/release ni B23 publicado/aceptado. Prioridades y skills aplazadas se mantienen; continúa objetivo global, QA/OS/clientes pendientes. Referencia de traspaso: tasks.md:1269. | ✓ Revalidado. tasks.md:192,1305–1308,1339–1340,1350–1354,1427–1432 conserva intento2 pendiente, QA2 intacta, macros/publicación/gates pendientes y skills aplazadas después de comandos/dashboard/hooks/memoria; objetivo no cancelado. | ✓ Conservado. tasks.md:14–24,192,1486–1488,1513–1515,1560–1561: ciclo post-QA3/MAX3 sin reset original1–3/post1–2; sólo1/16, skills aplazadas después comandos/dashboard/hooks/memoria; QA/gates/commit/push/cierre global pendientes. | ✓ Conservado. tasks.md:1564–1593 preserva rechazo de intento 3, decisión ROOT de una única revisión adicional global 4/MAX4 y original 1–3/post 1–3 sin reset. :1655–1657 mantiene QA completa/gates/macros/push/cierre pendientes y skills aplazadas después de comandos/dashboard/hooks/memoria. | ✓ Conservado. tasks.md:1714–1726 y ROOT4 preservan rechazo3/MAX3 y4/MAX4; global5/MAX5 único pase explícito replan, sin reset ni deuda. :1759,1769–1771 mantiene revisión5,QA3,gates,cobertura,publicación/macros pendientes; sólo1/16 y skills aplazadas. | ✓ Conservado. tasks.md:1830–1841,1868–1869 mantiene rechazos3/4/5 sin reset, una revisión6/MAX6 explícita y QA2 FAIL/QA3/cobertura/macros/push/cierre pendientes. :192 conserva skills aplazadas; T-01 sigue 1/16. |

Preparación6: 55 unidades OWN actuales pasan PID6212 exit0; 11 runtime históricas,
no repetidas. ROOT cotejó217 artefactos/copies, sin ejecución ni aceptación QA.
Una copia pública limpia conserva exactamente1030 hashes de la fuente revisada,
sin su Git privado; evita extras al verificar los inputs de QA3. No código cambiado.
Ambas QA2 siguen FAIL, auditorías inutilizable/corrupta y counts aceptados null.
QA3 completa Windows/Linux y cobertura90/90 siguen pendientes. Sin modelos/clientes
nativos, memoria promovida, cierre macro/global, commits o push por esta revisión.
Skills nuevas aplazadas hasta implementar y validar comandos, dashboard, hooks y memoria.

### QA3 iniciada tras revisión6 aceptada — Windows/Linux en paralelo

Revisión6 aceptada por ROOT, SHA256
`35e38f5a214f5c0a249a57d9002065b7d5d556d0dc01574d18e3b53922cd10ff`.
Ledger-lint posterior: PID23336 exit0, cero incoherencias y el aviso histórico730.
Freeze real PID33272 exit0; ROOT verificó los1030 hashes raw/canónicos, blobs Git,
todos los modos y los inputs/dependencias de ambas plataformas. Preflight SHA256
`9bc3f471fdb7ff5da9099e931f7b6a4fe7bfb16ed0bfd6515f50f498948e8854`.
Atestación ROOT SHA256
`dcfd73b5ac5e1e2259d63ff31102573cbf5fb56d94f8a617bd5a254a564706e6`;
pointer final SHA256
`49f5f5a8acdd8fe5b7e1c7b44559550f5527bacb0b12432c90e4cc7497700d5f`.

Runners reales iniciados: Windows PID34856 y Linux PID24544, cada uno con output
OWN exclusivo; conservan los14 directorios de CI y los6331 IDs históricos.
La colección y los terminales finales de esta ejecución siguen pendientes;
no se atribuye ningún pase ni porcentaje de cobertura antes de observarlos.
Coverage7.16.2 debe observar CTracer real; gates90/90, qa-gate y auditoría de hijos
siguen obligatorios. QA2 permanece FAIL. Sin aceptación completa/nativa/global,
promoción de memoria, commits, push ni nuevas skills por iniciar estos runners.

### Observación QA3 y reintento Linux aislado

Linux inicial terminó FAIL: runner PID24544 exit1 y Docker attach PID32360 exit1.
La colección de6378 se comparó por error contra los6331 IDs de Windows;27 IDs
paramétricos difieren entre plataformas. Se ejecutaron0 tests de producto. El
JUnit cerrado conserva1 testcase sintético `pytest/internal` con1 error, no0
testcases. El fallo posterior al construir coverage impidió escribir el terminal
del driver; no se reconstruye ese archivo ni se presenta pytest3 como un retorno
medido. CID OWN terminado removido y ausencia verificada; servicios del usuario
intactos. La ejecución Windows original continúa, sin alterar su harness/fuente.

Reparación exclusivamente OWN de Linux: RED PID24820 exit1 con4 fallos de
aserción; GREEN final PID38444 exit0,14 unidades de funciones AST, no QA completa.
Las dos cohortes observadas conservan6331 IDs exactos cada una,6304 comunes y27
propios de cada plataforma; no normalización ni omisiones. Coverage faltante
conserva los7 archivos como unsupported y bloquea aceptación; gates90/90 y
CTracer7.16.2 permanecen obligatorios. Revisión fresca de lectura sin defectos.
ROOT corrigió dos errores de lectura del índice de preparación antes de crear
bindings; ambos exit1 sin modificar los inputs originales ni iniciar QA.
El informe inicial confundía0 tests ejecutados con0 testcases JUnit: se corrigió
y se preservaron íntegros el informe y los recibos anteriores en OWN/history.

ROOT preflight PID29152 exit0, SHA256
`9986d5adc84c185fbf0994466d7f49a045d6ff17dc0be362a5d2b969247c49b8`:
91 artefactos OWN,1108 originales,78 OWN previos,6 artefactos Linux cerrados y10
archivados verificados. Fuente aceptada6 de1030 archivos y cadena de decisiones
3/4/5/6 intactas. Nuevo runner Linux PID39188 iniciado en OWN separado con los
mismos14 directorios de CI; terminal, colección y cobertura del reintento aún
pendientes. No se reinició Windows ni se atribuye aceptación al nuevo inicio.

Observación provisional Windows, mediante lectura compartida acotada de filas
JSONL completas:3371 call reports,3332 passed y7 failed. Seis fallos muestran
`COMSPEC` ausente en el entorno de pruebas; N09 muestra WinError5 al renombrar
el staging de restauración. La suite continúa: no son resultados finales ni
cobertura aceptada; causas/reproducciones y resolución siguen pendientes.

Comprobación visual OWN: servidor PID34544 cerrado voluntariamente exit0 tras
`ERR_BLOCKED_BY_CLIENT` de Edge. El HTML estático se generó, pero el navegador
rechazó file por su política de URLs. No se eludieron barreras ni se escribió
decisión alguna. Navegación visual y revisión interactiva/nativa siguen pendientes.

Lectura paralela identifica la siguiente aceptación de memoria: retoma tras
interrupción con candidato, operación y recibo exactos de la iniciativa. El lector
actual de work-resume compone ledger/journal sin consultar ese handoff; implementar
su vista readonly queda después de resolver la QA actual. No se convierte journal
en autoridad ni se infiere pertenencia por texto. Skills nuevas siguen aplazadas
hasta implementar y validar comandos, dashboard, hooks y memoria. Sin cierre
macro/global, promoción de memoria, commits o push por estas observaciones.

Reintento Linux observado: driver PID7 con CTracer7.16.2 real; colección6378
conserva los6331 previos Linux y añade47, sin omisiones. Ya supera la frontera
de colección que falló en el primer intento; no equivale a terminal verde.
Ledger-lint de esta observación: PID20732 exit0,0 incoherencias y1 aviso
histórico de cabecera en línea730. Gates y cierre completo siguen pendientes.

### QA3 terminal y bloque24 — coherencia de comandos y handoffs

Las observaciones provisionales anteriores quedan como historia. Windows terminó:
runner PID34856, driver PID24112, pytest y qa-gate exit1; JUnit6279 passed,
7 failed,0 errors,92 skipped,6378 casos. Los seis KeyError COMSPEC proceden
del entorno del harness, reparado en OWN separado con RED válido PID24368 exit1,
GREEN PID12176 exit0 y seis casos de aliases PID1492 exit0. No reemplazan la
suite completa fallida. N09 sigue con causa no probada: publicación por rename
tras inventario validado; tres hijos registrados exit0. Una reproducción aislada,
un módulo completo y dos fixtures de profundidad pasan, sin demostrar causa ni
autorizar la etiqueta flaky. Los128 artefactos de preparación,1378 de diagnóstico,
19 inputs originales y50 del análisis terminal fueron verificados por ROOT.

El reintento Linux terminó: runner PID39188, driver PID7, pytest/qa-gate exit0,
JUnit6334 passed,0 failed/errors,44 skipped,6378 casos. Conserva los6331 IDs
Linux previos y47 nuevos. El runner sale1 por cobertura, no por tests. Auditorías
del wrapper: Windows2910/2910 y Linux2917/2917 hijos registrados terminales,
sin pendientes; no cubren descendientes fuera del wrapper. CTracer7.16.2 real:
Windows media84.22456775892661%, cambiadas84.55172413793103%; Linux
media84.40309891746371%, cambiadas85.24137931034483%. Ambos incumplen90/90,
sin redondear ni sumar plataformas. No hay aceptación QA global. El contenedor
del reintento Linux fue retirado por el runner usando su CID propio ya terminal;
no se tocaron contenedores del usuario.

Recibos ROOT privados: `windows-preparations24-root-verified.json` y
`terminals-operations24-root-verified.json`, bajo el OWN de ejecución. JUnit Windows
SHA0056cc1ba76060eae41eb0fb5effa1724c91523c79696a704f1c7f53d1c7b161;
Linux SHA8215607ea66fbad80b60948af5ca4d291a65fe93ef3691b2fd5d640acfb3b1f2.
Un primer preflight del segundo recibo resolvió erróneamente una ruta pública
relativa contra OWN y falló antes de escribir; se corrigió contra ROOT explícito
con whitelist del manifest público. La evidencia terminal original se conserva.

Comparación de comandos en paralelo:55 cuerpos nuevos completos y2 relecturas,
en tres grupos de26,17 y14. Con los18 previos:73/94 cuerpos leídos;21 restantes
en el siguiente pase. ROOT verificó65,53 y56 registros de evidencia de estos
grupos y sus artefactos; los counterparts cambiados se cotejaron con el snapshot
raw histórico. Hay8 decisiones estáticas suficientes en el grupo de planificación,
sin aceptación de runtime; las otras fichas mantienen recursos/dependencias
pendientes. Cuerpo leído, comparación estática e integración son medidas distintas:
ningún comando de estos grupos se declara integrado por esta lectura.

Bloque24 aplica una corrección propia posterior a la fuente congelada6:
`agents/qa.md` sólo escribe testing y devuelve evidencia; el orquestador controla
reapertura y cierre después de retro. `commands/dev-cycle.md` reserva Done a
`aprobado`, propone diseño por servicio/ruta/SHA y reconcilia su tabla de estados.
La plantilla de architect, doc de QA, CONVENTIONS y FLOWS ES/EN conservan esos
dueños; rejected no se reenvía a curación y retro exit1 tiene nodo de cierre
pendiente separado. El formato de retro documentado coincide con el gate real.
Revisión fresca estática:8 ficheros,9 observaciones corregidas y releídas,
0 defectos scoped abiertos. Informe SHA
151d06cf93cf749b3365825408ce1d2c3ae9b7f869e790948089766e0fcea6f0.
Los límites Jira heredados —read-back antes de aprobado, evidencia de revisión,
agrupación fase y publicación de ops— permanecen pendientes distintos.

Validación aislada del bloque24: export PID13172 exit0, export-check PID26828
exit0, lint PID25812 exit0 (0 errores,9 avisos existentes). ROOT verificó los8
SHA actuales contra el snapshot revisado y promocionó exclusivamente4 exports
generados de QA/dev-cycle para Codex/OpenCode. Espejos CHANGELOG EN/ES reflejan
el cambio. Prosa: TDD n/a; no tests que imiten instrucciones. Esta revisión y
checks no amplían la aceptación de fuente6 ni prueban dispatch nativo.

Siguiente trabajo acotado: pruebas significativas de publicación/recuperación,
CLI en proceso y Gold sin fallback para cubrir contratos hoy no medidos; un
experimento OWN de sharing de rename comprueba un mecanismo, sin identificar
el holder original ni suprimir fallos; completar cuerpos y recursos de comandos.
Skills nuevas siguen aplazadas hasta implementar y validar comandos, dashboard,
hooks y memoria. Macros, V01–V08, memoria/handoffs nativos, cobertura, cierre,
commits y push permanecen pendientes; no se reinicia una suite completa antes
de atender estos resultados.

#### Continuación verificada del bloque24

El cuarto grupo leyó los21 cuerpos restantes:120954 bytes,4192 líneas. ROOT
verificó3 artefactos y68 registros, sus IDs y la unión exacta C001–C094 con los
18 previos y los tres grupos anteriores. Total94/94 cuerpos completos; seis
decisiones estáticas suficientes y quince fichas abiertas en este último grupo.
Recibo `remaining-commands24-root-verified.json`. Un primer lector ROOT incluyó
IDs de recursos como comandos y falló antes de escribir; se corrigió el filtro
exacto Cddd. Recursos transitivos, callers y aceptación nativa siguen pendientes;
esta lectura no integra comandos. El documento de comparación refleja esa
distinción y la ampliación de skills sigue aplazada.

Preparación de pruebas de memoria en OWN: tres archivos nuevos,54 casos nuevos
verdes. Cohorte final Windows PID35244 exit0:192 passed,0 failed/errors,2 skipped,
1 deselected; baseline PID13396 exit0:138 passed y los mismos2 skips. La prueba
original multiproceso se deselectó sólo en este experimento sin hijos y debe
incluirse en la próxima QA completa. El primer baseline falló en el harness antes
de pytest; el primer intento ampliado detectó ID de parámetro excesivo y lectura
del byte de lock Windows durante el bloqueo. Se conservaron sus recibos y se
corrigieron únicamente fixtures/observación, sin rebajar expectativas.

ROOT verificó54 artefactos,1030 fuentes canónicas,86 dependencias, JUnit, tracer
y las cohortes exactas: los140 casos previos se conservan y se añaden54. Preflight
PID17064 exit0, recibo `memory-tests24-root-verified.json`. CTracer7.16.2 real:
publicación260/268 líneas; curation493/544; Gold169/174 en la misma cohorte.
No son porcentajes de QA global, changed-lines ni Linux; no se atribuyen hijos.
Las pruebas siguen en OWN hasta completar la revisión A+B y promoverlas.

Experimento N09 de sharing de rename, en tres fixtures OWN con16 archivos y
un intento por caso: sin handle, handle de directorio con share READ|WRITE y
handle con READ|WRITE|DELETE; los tres restauran correctamente. Los dos handles
reales se cerraron. ROOT verificó169 artefactos y flags/resultados exactos;
recibo `rename-sharing24-root-verified.json`. Este mecanismo concreto no reproduce
el fallo original; causa y holder siguen desconocidos. No hay fix, retry de
producción, supresión ni etiqueta flaky.

Checks del bloque documental previo: export-check PID15000 exit0, lint PID33748
exit0 (0 errores,9 avisos existentes), ledger PID3652 exit0 (0 incoherencias,
1 aviso histórico). Diff-check explícito de16 archivos PID11084 exit0; stderr
sólo avisos CRLF. Las actualizaciones posteriores de ledger/comparación requieren
su check final; esta evidencia conserva los bytes que se comprobaron entonces.

## Revisión de dos lentes — intento 1: Bloque24 (T-14) — pruebas adicionales de memoria

Bloque nuevo de tres pruebas, separado de la revisión aceptada6 del producto:
intento1 de3, lentes A+B. Selector PID14604 exit0, C=false/D=false, sin avisos.
Contexto fresco por revisores genéricos con modelo heredado; API de reviewer por
nombre no disponible. Alcance sin Git: selección explícita de los tres archivos,
scope-gate saltado con aviso, sin simular exit0. No cambia el veredicto ni el
historial de intentos3/4/5/6 de la fuente anterior.

| Criterio del bloque | A | B | Evidencia |
|---|---|---|---|
| CLI y handoff reales | ✓ | ✓ | Confluence main, servicio propose/apply/recover y recorder Gold real |
| Errores e inputs corruptos observables | ✓ | ✓ | Códigos, snapshots y fronteras IO específicas |
| Bytes, identidades y estado preservados | ✓ | ✓ | SHA de bytes persistidos, fuente/store/policy conservados |
| Recuperación, idempotencia y lock cooperante | ✓ | ✓ | Servicio real, operación durable y hilo dueño liberado en finally |
| Gold exclusivamente candidato | ✓ | ✓ | Sin approved, trayectoria ni writer alternativo |
| Fixtures locales sin servicios externos | ✓ | ✓ | tmp_path, sin red ni subprocess en la cohorte acotada |
| Originales/umbrales intactos | ✓ | ✓ | Tres archivos nuevos; fuente1030 y dependencias86 verificadas |
| Evidencia y límites de54 casos | ✓ | ✓ | JUnit real, Windows acotado; Linux/global/multiproceso no aceptados |

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| — | — | Sin defectos ni gaps abiertos en este bloque | T-14 | No necesaria | A+B leyeron los tres tests completos y contratos/transitivos pertinentes |

ROOT leyó ambos informes y verificó sus artefactos, la preparación y los hashes
exactos de las tres pruebas. B detectó inicialmente una discrepancia al comparar
SHA raw con canonical: exit1 conservado, sin PID inventado. Las14 fuentes
contrastadas coinciden con sus campos de manifiesto; en seis sólo difiere CRLF/LF.
La revalidación B PID15724 exit0 mantiene ambos hashes separados. No se modificó
fuente ni consumió un intento de corrección del producto por ese error de lector.

Promoción ROOT PID22680 exit0 de sólo tres archivos nuevos en tests, con bytes
revisados intactos. Fusión privada SHA
d7ccf5f63f20fd5311bffb099b67ca2b2bc1a0a6f54a26fc9f7cb59de71483a9;
recibo de promoción SHA05f4366fde74120f90d9cd6867106f7830d38d516da57b70c9988949fc695b2c.
El preflight del índice B apuntó primero a un nombre inexistente y falló en
lectura; luego se usó sha256.json real. No hubo mutación ni aceptación por ese
fallo. No se consulta configuración Jira del consumidor en esta QA aislada,
por lo que no se publica fuera del ledger. Sin cierre de T-14, QA global/nativa,
promoción de conocimiento, commits ni push. Siguiente puerta: QA completa con
54 casos añadidos y todos los originales, sin deselect del lock multiproceso.

Comparación detallada del panel de revisión cerrada como lectura estática:
15 funciones,47 recursos (44 cuerpos completos y tres dirigidos). ROOT preflight
PID14452 exit0 verificó cinco artefactos y hashes de los47 recursos; recibo
`panel-comparison24-root-verified.json`. El documento panel-activity distingue
review UI de vista operativa/runner y conserva CAS, raw/view y receive/ack propios.
Se diseñan resultados por comentario y actividad con caducidad; polling actual
se conserva porque SSE bloquearía el HTTPServer serial. No hay implementación
ni prueba de atención individual, actividad nativa o interacción browser en este
pase. V01–V08 siguen pendientes. Un primer patch documental falló por contexto
de línea inexistente y no modificó el fichero; el patch con contexto real pasó.

#### Retoma explícita de curación — preparación del bloque24

El código de retoma quedó aprobado en la revisión acotada2 de3, lentes A+B+D,
sin gaps abiertos; C=false. Se conservan los dos Important del intento1 y
sus RED antes de corregir. Preparación Windows OWN-02:16 regresiones nuevas,
70 vecinos (25 añadidos previos y45 originales) y10 vecinos de curación pasan.
Estos resultados no constituyen QA global, Linux ni aceptación nativa.

El paquete integra referencias explícitas candidate/SHA en el ledger antes
de apply, con orquestador/planner como dueños; Curator sólo entrega IDs y recibos.
La vista usa validación readonly del servicio y presupuestos existentes,
sin limpieza, recuperación, aprobación ni búsqueda global de candidatos.
Callers, contratos ES/EN y proyecciones generadas se preparan en OWN; su
revisión independiente, QA y promoción a ROOT siguen pendientes. No cambia
el estado de T-14 ni de las otras quince tareas macro; skills nuevas aplazadas.

## Bloque24 — integración revisada y validación conjunta pendiente

La ampliación de skills sigue aplazada. Este bloque mantiene la prioridad de
comandos, panel, hooks y memoria; no cierra ninguna tarea macro adicional.

La retoma de curación y sus callers quedaron aceptados en sus revisiones
acotadas2. La lectura readonly conserva las identidades de candidato,
operación y recibo y sus omisiones; no recupera, aplica ni aprueba conocimiento.
La documentación y los exports se integraron en una copia de trabajo aislada.

Los resultados por comentario del panel quedaron aceptados en revisión de
producto2 y de documentación1. La revisión de sus pruebas terminó en intento3
de3: B-T01 (limpieza de procesos fallidos) corregido en2, A-T02 (lector aún
vivo después de publicar la señal) corregido en3. RED causal1 y GREEN1 del
último cambio, foco5/5 Windows y nueve hijos terminales; la colección72
observada entonces era Windows, no ejecución Linux. El consumo de una decisión
no equivale a atención ni una respuesta constituye otra autorización.

### Resultados de QA conservados

QA4 evaluó la fuente anterior congelada de1034 archivos, con6432 casos por
plataforma, sin deselects. Estos resultados no validan automáticamente las
ampliaciones posteriores de retoma, feedback o protocolo sintético.

| Plataforma | Pasan | Fallan | Saltos | Media de cobertura | Líneas cambiadas |
|---|---:|---:|---:|---:|---:|
| Windows |6338|2|92|93,6867%|92,2759%|
| Linux |6388|0|44|93,8652%|92,9655%|

Ambas mediciones usaron CTracer oficial7.16.2 en el proceso padre y superaron
90/90 con fracciones exactas, antes de redondear. Linux pasó sus gates;
Windows sigue NO-PASS por N03 y N04[claim_after_claiming]. La causa primaria
histórica permanece desconocida. Los dos casos pasaron en la ejecución
instrumentada aislada; ese resultado no demuestra reparación de su causa.

Un defecto secundario demostrado del soporte de prueba podía ocultar la primera
excepción de publicación con una segunda escritura desde finally. La corrección
acotada3 archivos quedó aceptada por A+B en intento1: clasifica InfrastructureError
con causa y etapa, conserva el temporal y repropaga la primera excepción sin
reintentar. Cinco RED antes del fix, cinco GREEN y cinco regresiones públicas
finales; focal original2/2 una vez. No se modificó ready ni producto ni se
presenta como reparación de los dos errores históricos. El nuevo test público
es `tests/test_memory_recovery_protocol.py`.

La ejecución Linux del panel72 terminó por timeout externo240s: salida parcial
sin JUnit ni aceptación. Fuente y contenedor propios verificados; el contenedor
se eliminó. La focal second_popen pasó1/1 en3,42s sin reproducir un atasco
intrínseco. La causa del coste total y la captura RAW POSIX del helper siguen
pendientes; no se reconstruyen streams antiguos ni se cambia el presupuesto
de producto para hacer pasar una prueba.

### Siguiente validación

La copia conjunta contiene1040 archivos públicos revisados, sin promoción a
ROOT ni QA integrada aceptada. Faltan corregir y verificar el registro de pruebas
Linux, ejecutar la QA de esta fuente, comprobar generados/documentación y
publicar el commit de alcance autorizado. V01–V08 de interacción real y la
aceptación nativa ampliada conservan su estado pendiente; las pruebas DOM y
los contratos aceptados no sustituyen esas observaciones. La memoria local
sigue siendo la base, con Kwipu/Graphify opcionales y Graphiti fuera del default.
### Addendum — Linux del panel y checks estáticos (2026-10-10)

La cohorte Linux del panel quedó aceptada con alcance limitado: colección y
JUnit reales 72/72, sin fallos, errores o skips, en 209,89 s según pytest;
29 hijos registrados terminales, sin pendientes, fuente antes/después igual y
contenedor propio eliminado con ausencia verificada. Bindings de código/tests,
imagen y versiones están en
`testing/panel-feedback-linux-evidence.json`.

Se conserva el intento histórico que agotó el guard externo de 240 s, sin JUnit
ni aceptación. Su causa primaria de coste total sigue desconocida. El defecto
de captura POSIX del helper se probó con 4 RAW rojos y 4 verdes; los tapes
antiguos no se reconstruyen. La nueva ejecución usó guardrail externo de 600 s y
traceback a 30 s por fase, sin cambiar deadline de 3 s, lock de 100 ms u oracles;
el resultado no demuestra una causa del tiempo anterior ni rendimiento garantizado.

Los checks estáticos de la copia conjunta de 1040 archivos fueron verificados:
88 exports al día, lint: 0 errores/9 avisos conservados y ledger: 0 incoherencias/
1 aviso histórico igual antes/después; todos con exit 0, sin ejecutar tests nuevos.
El aviso de ejecutabilidad usa fallback filesystem, no valida el índice Git.

Esto actualiza sólo la evidencia Linux y estática posterior. La QA integrada,
V01–V08 reales y aceptación nativa ampliada continúan pendientes; sin medición
de cobertura, aceptación global, promoción o nuevo cierre macro.

### Capturas nativas de la implementación actual (2026-10-10)

Claude 2.1.287 produjo dos capturas válidas de sesión, con schema1,
sequence1 y versión1.22.0. OpenCode2.0.12 también produjo dos tras corregir
el fixture para copiar el manifiesto que ya incluye el instalador. El fallo
anterior por versión0.0.0 se conserva; no requirió modificar producción.
OpenCode observa ejecución/idle y emite el envelope SessionEnd del plugin;
esta prueba no acredita un evento nativo de teardown.

Codex0.161.0 registró el marketplace, pero plugin add terminó en exit1 por
«Acceso denegado (os error5)» antes de iniciar sesiones. La causa sigue
sin determinar; el diagnóstico de instalación está preparado, sin ejecutar.
Todos los jobs de esas ejecuciones quedaron sin procesos activos y la fuente
y las distribuciones permanecieron intactas. Los bindings y los límites están
en `testing/native-capture-current-evidence.json`.

No se aceptan por esas capturas el solape de escritores, decisiones de modelos,
routing de agentes, workflows de comandos o interacción de navegador.
La suite integrada de Windows/Linux está en curso sobre1040 archivos,
11 productores Python y14 directorios CI; no tiene todavía veredicto final.
La colección real contiene6612 IDs por plataforma. Una prueba cuyo ID incluye
el número de líneas de una skill cambió79→82; código y límite250 son iguales.
Se conserva esa transición explícita y las6431 identidades restantes literales;
los recibos originales de colección no se reclasifican.

### QA completa de la fuente actual — resultado Linux (2026-10-10)

Linux terminó con 6.568 pruebas pasadas y 44 omitidas, de los 6.612 IDs
recogidos, sin fallos ni errores. Pytest y qa-gate terminaron con exit 0.
Coverage.py 7.16.2 usó CTracer oficial en el proceso padre: media de los
11 archivos de producción 93,140669 %, líneas cambiadas 355/383
(92,689295 %); ambos gates de 90 % pasaron antes de redondear.
Los 2.963 hijos registrados quedaron terminales, sin pendientes; los
1.060 bindings de fuente y soporte coincidieron tras la ejecución. El
contenedor propio se eliminó con ausencia verificada.

Las omisiones mantienen sus motivos: corpus privado ausente, PowerShell no
disponible en Linux y contratos específicos de Windows. No acreditan esos
recorridos en Linux. Los bindings y límites están en
`testing/core-qa-current-evidence.json`.

Windows sigue ejecutándose y conserva un fallo en
`test_f21_feedback_aggregate_boundaries[exact-verifications-40]`: el fixture
descartó la respuesta de preparación y después usó un review `None`. El
error original de esa operación no se registró y su causa permanece
desconocida. La regresión para conservar etapa/respuesta está preparada,
sin ejecución ni cambio de producto. Los dos casos N03/N04 que fallaron
históricamente pasaron sus tres fases en esta ejecución; no demuestra
reparación de sus causas históricas.

El resultado integrado aún no está aceptado; tampoco se cierran la interacción
real, la aceptación nativa ampliada o el objetivo completo. Sin promoción,
commit o push de este lote.

### Resultado terminal Windows y diagnóstico del setup de revisión

2026-10-10. Las dos suites completas han terminado con sus handles originales.
Windows: 6.519 passed, 1 failed, 92 skipped, 0 errors; pytest y qa-gate exit1.
Cobertura oficial CTracer 7.16.2 parent-only: media 93,248765 % y cambios
1.069/1.149 = 93,037424 %, ambos umbrales 90 % superados sin redondear.
Los 2.966 hijos registrados terminaron; 1.060 hashes posteriores sin diferencias.
La QA integrada permanece roja por F21 exact-verifications-40, conservado.

Diagnóstico en copia propia, sin cambiar producción: tres RED demuestran que
`typed_record` pierde la primera respuesta no-ok de submit/receive/ack.
La primera corrección conserva el texto pero pytest reescribe el assert;
la corrección definitiva lanza AssertionError con operación y envelope exactos.
Sus tres regresiones pasan. La primera invocación focal falló en setup por un
padre basetemp propio ausente; corregido el harness, el singleton original pasa.
Esto no reproduce ni explica el error operacional de la ejecución completa,
no cambia su resultado y no autoriza declarar aceptado el producto global.
Resultados y límites en [evidencia actual](testing/core-qa-current-evidence.json).
### Instalación Codex reducida y siguientes componentes

2026-10-10. Codex 0.161.0 instaló en un proyecto propio la distribución de
390 archivos (hooks, agent-kits, skills, manifiesto Codex y proyección Codex),
sin Git init, proveedor ni sesiones. Marketplace add y plugin add exit0;
versión instalada 1.22.0. ROOT comprobó 29 artefactos, los 390 hashes de caché
y los 1.040 hashes de fuente: cero diferencias. Cleanup exit0, ningún hijo
pendiente. El fallo del paquete completo permanece registrado. La comparación
exacta también encuentra diferencias de watcher/proveedor, tiempo y lectores;
el éxito reducido no atribuye a contenido la causa del os5. Se prepara una
instalación completa con el harness installation-only, aún sin ejecutarla.

En copia propia se implementa el cálculo puro de frescura de actividad:
27 casos GREEN tras RED por API ausente, caducidad exacta a los 60 segundos, reloj futuro
como desconocido, exclusión de contenido libre y separación respuesta/ejecución.
No acredita un proceso vivo ni destrucción de agente. Almacenamiento, opt-in,
productores nativos, HTTP y UI siguen pendientes; no se distribuye aún.
Portabilidad de memoria y selección de commits continúan con RED/GREEN reales
en copias propias separadas; no se incorporan a la fuente QA de 1.040 archivos
ni se declaran aceptadas por los resultados de esa fuente anterior.
### Actualización del 10 de octubre: instalación completa de Codex

La prueba aislada de instalación de la distribución completa terminó con exit 0: marketplace y plugin instalados, 1.040 archivos de caché verificados y 3.120 comparaciones SHA entre fuente, distribución y caché sin diferencias. El cierre terminó con exit 0 y cero procesos activos del job. No se lanzaron sesiones, modelos, proveedor, watcher ni Git. Se conserva el fallo anterior de acceso denegado; su causa sigue desconocida. Esta prueba acredita instalación y no ejecución nativa de hooks ni QA global. Evidencia portable: testing/native-capture-current-evidence.json.

### Actualización del 10 de octubre: almacenamiento compartido para actividad

Implementación aislada de local-state.py y extracción de seis funciones de plan-review.py; 41 funciones restantes idénticas. Revisión independiente C0/I0/M0. RED antes de código y regresiones de callback sync preservados. Pase vecino final: 211 aprobadas y una omitida por symlink OS, total 212, 51 hijos directos terminales y cierre del job sin fugas. El primer pase incompleto por límite de ejecutor 60 s se conserva; el siguiente usó 180 s sin aumentar deadlines del producto. Evidencia portable: testing/core-qa-current-evidence.json. Pendientes integración, store/productores de actividad, HTTP/UI, QA completo y publicación. El QA completo Windows previo sigue rojo y su causa no se declara resuelta.

## Bloque25 — traslado de memoria, commits y actividad integrada

2026-10-10. La candidata de trabajo incorpora el traslado local de memoria,
la selección revisada de commits y el almacenamiento/productores/HTTP/UI de
actividad. Su manifest de esta fusión tiene 1.068 archivos; no está congelada
para QA, no está promovida al checkout y no acredita aceptación global.
La ampliación de skills permanece aplazada; se cierran referencias de la
skill existente del panel para distribuir sus dependencias.

- Memoria: corrección de export a `.git` y efectos `written` con RED real;
  29 casos finales de corrección/persistencia pasan. La documentación ES/EN
  fue contrastada independientemente contra el CLI y codec sin defectos.
  Se conserva la QA anterior de 159 aprobadas/4 omisiones como evidencia de
  aquella fuente, no como ejecución completa de esta versión integrada.
- Commits: el CLI tiene 10 pruebas verdes, incluido el límite total de salida
  con newline. Las 28 pruebas públicas de selección/snapshot profundo terminan
  con 26 aprobadas y dos omisiones OS. Validan fixtures Git propias con 754
  hijos directos terminales, sin exigir rutas ni variables privadas OWN.
  Caller y documentación ES/EN tienen revisión independiente sin defectos;
  el workflow nativo conjunto aún requiere su evidencia.
- Actividad: el store conserva la QA focal anterior de 40 aprobadas/una omisión
  y dos barreras verdes. El rechazo de archivos locales por Git tiene RED y
  GREEN reales; el último caso focal pasa con un entorno Git cerrado, sin
  cambiar el producto. El fallo concurrente GREEN6 permanece de causa desconocida.
- Panel: la entrega inicial tuvo 185 aprobadas; ROOT encontró después dos
  etiquetas Unicode mal codificadas. RED dedicado y corrección conservados.
  El pase final de 11 casos sobre store actualizado pasa; no equivale a repetir
  los 185 sobre los bytes finales ni a comprobar un navegador real.
- Diagnóstico: RED de tres métodos y nueve subcasos confirma que `/doctor`
  desconoce `sesion.actividad`; tras añadirla al vocabulario booleano pasan los
  tres métodos. Su ejemplo conserva el opt-in desactivado. Corrección revisada
  y fusionada; documentación de dependencias fusionada en la candidata de trabajo.

La QA completa Windows anterior sigue roja en F21. Conservar etapa/envelope
mejora el diagnóstico y no demuestra una reparación causal. La instalación
Codex completa sin sesiones pasó; no acredita captura de actividad nativa.
Se preparan nuevas colecciones/QA Windows y Linux sobre una fuente congelada,
con los mismos 14 directorios CI y umbrales de cobertura 90/90, sin quitar casos.
Ejecución nativa ampliada, navegador Edge, retro y publicación permanecen
pendientes. No se cierra ninguna tarea macro ni se cambia su alcance por este
checkpoint. Sin commit ni push del lote.


### Validación operativa del bloque25 — resultados preservados

[Estado parcial de pruebas y actividad nativa](testing/final-qa25-status.md).
Linux full01 terminó con 6.842 pases/14 fallos/44 skips, cero errores y
ambas coberturas por encima del 90 %, con cierre del contenedor confirmado.
Windows full01 conserva un fallo de actividad y un error del diagnóstico;
no se declara QA completa. Correcciones de panel, fixtures y escáner pendientes
de pruebas focales, fusión y nueva QA. La actividad de sesión OpenCode V2 pasó
una prueba nativa con identidad HMAC y outcome HTTP correlacionados; Claude
valida límites de respuesta, pero no SessionEnd; Codex conserva el descubrimiento
y el diagnóstico del fixture LF/CRLF, sin captura aceptada todavía.
T-02/T-09/T-14 y las demás tareas macro conservan su estado. No hay push
de este cierre y la ampliación de skills sigue aplazada.


### Actividad nativa y revisiÃ³n del escÃ¡ner â€” checkpoint 2026-10-11

Codex 0.161.0 pasÃ³ la prueba aislada de actividad del subagente architect:
inicio y fin de respuesta correlacionados desde el protocolo RAW y el HMAC
del store, diez definiciones con confianza nativa verificada, cliente y probe
en exit 0, cierre exacto sin procesos activos y 1.070 archivos sin cambios.
El resultado no valida todos los eventos de hooks. Se conservan los intentos
fallidos y las causas probadas del fixture LF/CRLF y de la comparaciÃ³n de
ctime entre APIs en Python 3.13.0 para Windows.
La Ãºltima correcciÃ³n del escÃ¡ner tiene revisiÃ³n independiente sin defectos;
su selecciÃ³n focal prevista de 127 casos aÃºn debe recogerse y ejecutarse.
[Evidencia operativa actualizada](testing/final-qa25-status.md).
ContinÃºan pendientes SessionEnd de Claude, las pruebas focales y la QA final
Windows/Linux, la verificaciÃ³n visual bloqueada y la publicaciÃ³n de la rama.
No se cierran tareas macro ni se amplÃ­a el catÃ¡logo de skills.


### Coste de proceso — corrección candidata y persistencia pendiente, 2026-10-11

El contrato productor/consumidor conserva identidades de fuente y ventana con revisiones
persistidas. El dashboard selecciona el último snapshot completo, suma ventanas independientes
y avisa de datos parciales ante identidades inválidas o contradictorias. Planner, plantillas,
transportes y documentación bilingüe propagan los campos opcionales del JSON real.
RED: PID 36180/exit 1, identidad ausente y total 350 en lugar de 200.
Primer foco completo: PID 28516/exit 0, 65 tests del medidor y dashboard aprobado.
Segundo foco con productor/frontmatter/consumidor: dashboard aprobado (200/250 tokens);
medidor PID 15692/exit 1, 64 aprobados y un fallo de persistencia legacy. Se conservan
revisión 1 en state y revisión 2 en el temporal; el error exacto y su causa no se acreditan.
La observación aislada PID 19120/exit 0 pasó, sin aceptar la ejecución fallida.
No se añaden retries al producto ni se cambian permisos para obtener un verde.
[Detalle y límites de validación](testing/final-qa25-status.md).
Siguen pendientes la aceptación completa del delta, su cobertura, revisión independiente,
N05 Windows, verificación visual, promoción, commits y push. No se cierran tareas macro
ni se amplía el catálogo de skills.

### Persistencia de mediciones — corrección candidata verificada en foco, 2026-10-11

La carga aislada PID 12828 reprodujo WinError 5 en la escritura 63; la consulta posterior
no identificó usuarios del archivo. El control con bloqueo propio sí fue identificado.
Esto no demuestra la causa de los fallos históricos. No hubo retries ni cambios de permisos.
El productor informa `medicion_persistida`; el consumidor evita sumar cierres sin persistencia
y los muestra como parciales, sin una etiqueta de ventana compartida no acreditada.
RED PID 14700: campo ausente y subtotal 350 frente a 150 parcial. RED PID 4572: etiqueta incorrecta.
GREEN PID 18944 y comprobación final PID 35976: 65 tests del medidor y dashboard completos.
Coverage 7.16.2/CTracer: 76/79 líneas cambiadas (96,20253164556962 %) en los dos archivos de costes,
gate 90 % aprobado sin redondeo; alcance solo del padre. Plantillas y convenciones sincronizadas.
La observación anterior PID 19120 fue un único test, sin dashboard; scope corregido en recibo aparte.
[Evidencia actual y límites](testing/final-qa25-status.md). N05, causa Windows, revisión independiente,
UI real, QA global, promoción, commits y push siguen pendientes. No se cierran tareas macro.


### Temporales y sesiones — corrección y comparación, 2026-10-11

RED PID 15168: colisión real entre temporales de dos saves intercalados, WinError 2.
La candidata usa creación exclusiva por operación y reemplazo Windows acotado (5/32/33;
cuatro intentos; esperas 20/40/80 ms). Otros errores no se reintentan; no hay merge multiwriter.
GREEN PID 30120 y cobertura PID 3916: 74 tests del medidor y dashboard completos;
Coverage 7.16.2/CTracer 97/103 líneas cambiadas (94,1747572815534 %) en los dos archivos de costes.
Controles Windows PID 29904: bloqueo liberado, segundo intento aprobado; bloqueo persistente,
cuatro rechazos con bytes anteriores conservados. 100 escrituras adicionales aprobadas.
No se atribuye owner ni causa a los fallos históricos; N05 y QA conjunta siguen abiertos.
Tres cuerpos de sesiones/revisión añadidos: 22 completos y uno parcial; 22 inmediatos
y 15 descendientes pendientes. Dos descendientes tienen ahora hash comprobado, sin lectura completa.
[Contraste y límites](comparisons/hook-session-continuity.md). Retoma de decisiones UI pendiente
de integración del caller; no se consume feedback al mostrar contexto ni se equiparan eventos.
Revisión independiente, UI, promoción, commits y push pendientes; ninguna macro cerrada.

## Consulta de revisiones al retomar — candidata, verificación incompleta

El dueño `plan-review.py list_reminders` observa la carpeta exacta del ledger,
sin inicializar estado, adquirir bloqueos de escritura, entregar decisiones ni ack.
Dos inventarios y dos lecturas de versión rechazan cambios observados. Hasta ocho
referencias conservan ID, versión, puerta y estado; las actuales y pendientes tienen
prioridad y se cuentan las omisiones. Los contadores de respuestas/verificaciones
son registros, no evidencia de atención, aprobación vigente ni trabajo terminado.

`/work-resume` y el bloque de progreso de sesión usan ese dueño. El historial
`--history-only` mantiene su comportamiento. Exportaciones Codex/OpenCode
comprobadas: 88 ficheros; linter: cero errores y nueve avisos existentes.

RED: las 12 pruebas iniciales fallaron por ausencia de la función/proyección.
Primer conjunto ampliado: 294 correctas, tres fallidas y un error de preparación.
Final01: 298 correctas y dos fallidas; el oracle de omisiones requería tres
registros, pues dos más el encabezado caben en tres líneas. Se corrigió el fixture,
conservando ese rojo. El harness no produjo un recibo final de cobertura; no se
acepta su medición. Final02: 295 correctas, cinco fallidas; las 14 pruebas nuevas
pasaron, cobertura nueva 77/87 (88,51 %), insuficiente para el gate de 90 %.
Se añadieron casos de dependencias incompletas, acceso denegado y omisiones.
Final03: 90 correctas y una fallida; 17/18 nuevas correctas. La prueba de contadores
falló antes de su verificación con estado `unavailable`, sin motivo capturado.
Cobertura de líneas nuevas: 83/87 (95,40 %), CTracer del padre y sus threads,
sin descendientes. Cobertura verde no equivale a tests verdes.

Dos workloads positivos contra el dueño anterior, sin reintentos, se detuvieron
tras 71 y dos ciclos completos con `changed_path`. El segundo observó cambios en
`st_ctime_ns` del descriptor, con identidad, tamaño y mtime constantes. No hubo
OSError capturado ni escritor identificado. Esto reproduce sensibilidad de la
lectura previa; no demuestra la causa de cada fallo histórico ni de Final03.
Las diferencias de timestamps en Windows están documentadas en
[CPython](https://github.com/python/cpython/issues/157671) y la distinción entre
datos y metadatos en [Microsoft](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_basic_info).
Se mantienen las comprobaciones y los rojos, sin atribuirlos a un producto externo.

Evidencia y hashes en [review-resume25-evidence.json](testing/review-resume25-evidence.json).
Lectura estable, revisión independiente, aceptación nativa, UI real y QA conjunta
siguen pendientes. No se promueve ROOT, no se cierra ninguna macro y no hay commit
ni push de este cambio.

## Lectura estable — comprobación focal completada, cierre conjunto pendiente

Se reproduce en Windows el cambio de metadatos sin cambio de contenido y se
conservan los RED: seis fallos del contrato inicial, dos del control nativo y dos
por cachés reales creadas al consultar kits de proyecto sin `-B`.
La candidata incorpora una única relectura acotada del mismo descriptor y
desactiva bytecode en los dos CLIs, con los controles de identidad y rutas activos.

La regresión ampliada inicial dio 389 correctas, una fallida y seis omitidas;
el fallo ocurrió preparando un recibo antes del deadline inyectado, con motivo
`invalid_input`. No se identificó su causa exacta. Tras el arreglo de cachés,
la batería ampliada dio 392 correctas y seis omitidas. La medición posterior,
con controles nativos adicionales en los límites de buffer, dio 187 correctas y
seis omitidas: 23/23 líneas ejecutables nuevas cubiertas (100 %), CTracer del padre.
La cobertura no incluye procesos descendientes. El linter detectó dos avisos nuevos por situar la opción de bytecode antes del bloque UTF-8; se reordenó tras ese bloque y antes de cargar helpers, y se midió de nuevo la fuente corregida. Las seis omisiones corresponden
a la falta de privilegio de symlink nativo de Windows.

Dos workloads positivos independientes completaron 100 y 250 ciclos de
open/submit/receive/ack, sin reintentos de operaciones ni eventos de fallo.
No demuestran la causa de todos los fallos históricos ni aceptación global.
Los recibos terminales y cleanup terminaron sin timeout ni errores de captura.

Evidencia: [stable-read25-evidence.json](testing/stable-read25-evidence.json).
Siguen pendientes QA completa Windows/Linux, revisión independiente, workflows
nativos y UI real. El ledger actual supera el límite de lectura de 256 KiB;
hay que reorganizar su historial conservando trazas y revisiones vigentes.
No se cierra ninguna macro ni se promueve, commitea o publica este lote.
