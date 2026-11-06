---
tasks: audit-remediation
estado: completado
creado: 2026-11-05
verificacion: obligatoria
changelog: Fixed
---

# Corrección de la auditoría de v3.2.1

> Ledger canónico de progreso. Fuente única. Autorización: petición del usuario de implementar los fixes y revisar con Claude.

[Spec](spec.md) · [Plan](improvement-plan.md)

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase 1 | 10 | 10 | 100.0% |
| **TOTAL** | **10** | **10** | **100.0%** |

## Fase 1

**Estado**: completado

### T-01 — Instalador y propiedad

- **Changelog**: El instalador autentica la propiedad, separa las cachés compartidas y recupera copias interrumpidas mediante staging firmado.
- **Estado**: completado
- **Descripción**: Resolver R1, R2, R3; conservar las puertas y los datos ajenos.
- **Archivos**: `install/**`, `tests/installer.test.mjs`, `tests/install-auth.test.mjs`.
- **Verificación**: tests dirigidos del área y regresiones vecinas; evidencia en testing/validation.md.

**Criterios de aceptación**
- [x] R1, R2, R3: escenarios de auditoría cubiertos, corregidos y sin regresiones conocidas.

RED: `tests/installer.test.mjs` (R1/R2/R3, 7 casos) falló con 7 failed: comandos/borrados no rechazados, edición perdida y scope inválido aceptado · 2026-11-05.

GREEN inicial: R1/R2/R3 → 7 passed. Cierre: Node final Linux 470 passed/16 skipped/cero failed; cinco B12 Windows, upgrade/selección y presupuesto verificados; A7/B7/C7/D7 sin gaps pendientes.


RED: `tests/installer.test.mjs:B12` falló con RED determinista: SIGKILL antes de rename deja el temporal de entrega y conserva agents tras uninstall · 2026-11-05.

### T-02 — Hooks y briefs

- **Changelog**: Los hooks limitan los marcadores a docs y los briefs conservan criterios anidados y diseño relacionado.
- **Estado**: completado
- **Descripción**: Resolver R4, R5, R6; conservar las puertas y los datos ajenos.
- **Archivos**: `hooks/run-hook.mjs`, `agent-kits/shared/task-brief.py`, `tests/test_audit_briefs.py`.
- **Verificación**: tests dirigidos del área y regresiones vecinas; evidencia en testing/validation.md.

**Criterios de aceptación**
- [x] R4, R5, R6: escenarios de auditoría cubiertos, corregidos y sin regresiones conocidas.

RED: `tests/test_audit_briefs.py` falló con 6 failed / 3 passed: criterios omitidos, rutas de diseño no reconocidas y marcador fuera de docs · 2026-11-05.

GREEN: hooks/briefs → 101 passed con la suite vecina.

### T-03 — Ledger, alcance y retro

- **Changelog**: El ledger conserva rutas Unicode y permisos, detecta conflictos y admite continuidad acotada del histórico.
- **Estado**: completado
- **Descripción**: Resolver R7, R8, R16, R17; conservar las puertas y los datos ajenos.
- **Archivos**: `agent-kits/shared/scope-check.py`, `agent-kits/shared/retro-gate.py`, `agent-kits/shared/ledger-write.py`, `agent-kits/shared/ledger-archive.py`, `commands/retro.md`, `tests/test_audit_ledger.py`, `agent-kits/shared/test_retro_gate.py`, `agent-kits/shared/test_ledger_archive.py`.
- **Verificación**: tests dirigidos del área y regresiones vecinas; evidencia en testing/validation.md.

**Criterios de aceptación**
- [x] R7, R8, R16, R17: escenarios de auditoría cubiertos, corregidos y sin regresiones conocidas.

RED: `tests/test_audit_ledger.py` R7/R8/R16/R17 falló por rutas escapadas, calibración anterior aceptada, descripción alterada y archivado sin rechazar concurrencia/enlaces; POSIX mode no ejecutable en Windows · 2026-11-05.

GREEN: ledger/alcance/retro → 100 passed, 3 skipped (plataforma).

### T-04 — Publicación y curación

- **Changelog**: La publicación revalida la cola y las proyecciones; protege exclusiones obligatorias y conserva el origen del conocimiento.
- **Estado**: completado
- **Descripción**: Resolver R9, R10, R11, R12, R21; conservar las puertas y los datos ajenos.
- **Archivos**: `skills/knowledge-services/**`, `skills/confluence-publish/scripts/confluence-scope.py`, `agent-kits/shared/knowledge-curation.py`, `tests/test_audit_knowledge.py`, `tests/test_knowledge_sync.py`.
- **Verificación**: tests dirigidos del área y regresiones vecinas; evidencia en testing/validation.md.

**Criterios de aceptación**
- [x] R9, R10, R11, R12, R21: escenarios de auditoría cubiertos, corregidos y sin regresiones conocidas.

RED: publicación/curación → 6 failed: replay envió cuerpo retirado; resumen filtró párrafo completo; cambio de proyección ignorado; staging incluyó seguridad; origen omitido; generación propia no reconocida.

### T-05 — Sesiones y consola

- **Changelog**: Las sesiones recuperan turnos fallidos y controlan envíos concurrentes, limpieza de procesos y buffers.
- **Estado**: completado
- **Descripción**: Resolver R13, R14, P1, P2; conservar las puertas y los datos ajenos.
- **Archivos**: `skills/plugin-panel/**`, `tests/test_console_*.py`, `tests/test_audit_console.py`.
- **Verificación**: tests dirigidos del área y regresiones vecinas; evidencia en testing/validation.md.

**Criterios de aceptación**
- [x] R13, R14, P1, P2: escenarios de auditoría cubiertos, corregidos y sin regresiones conocidas.

RED: consola → 6 failed: turno fallido bloqueó mensaje explícito, driver muerto retuvo slot, sondeo idle no recuperó, aprobación procesó 500k caracteres, pipe hizo 65.549 lecturas, ruta larga dio 404.

### T-06 — Exportación portable e interop

- **Changelog**: Las exportaciones portables incluyen el catálogo correcto y rechazan destinos enlazados antes de escribir.
- **Estado**: completado
- **Descripción**: Resolver R18, R19; conservar las puertas y los datos ajenos.
- **Archivos**: `scripts/export-skills.py`, `scripts/export-interop.py`, `tests/test_audit_exports.py`.
- **Verificación**: tests dirigidos del área y regresiones vecinas; evidencia en testing/validation.md.

**Criterios de aceptación**
- [x] R18, R19: escenarios de auditoría cubiertos, corregidos y sin regresiones conocidas.

RED: exportación → 3 failed: catálogo ausente en portable completo/core; hardlink sobrescrito sin preflight.

### T-07 — Jira y worklogs

- **Changelog**: Jira redacta comentarios y mantiene la raíz y la configuración del proyecto al generar worklogs.
- **Estado**: completado
- **Descripción**: Resolver R20, R22; conservar las puertas y los datos ajenos.
- **Archivos**: `skills/jira-sync/**`, `tests/test_audit_jira.py`.
- **Verificación**: tests dirigidos del área y regresiones vecinas; evidencia en testing/validation.md.

**Criterios de aceptación**
- [x] R20, R22: escenarios de auditoría cubiertos, corregidos y sin regresiones conocidas.

RED: Jira → 3 failed: secreto reconocido viajó en comentario, invocación anidada desactivó Jira y comando worklog usó jornada 99 del cwd ajeno.

GREEN: Jira → 76 passed; el test de posición de argumento verifica su significado (`--clave`). Regresión final pendiente.

### T-08 — Lecturas de capacidades y journal

- **Changelog**: El journal valida sus puntos de E/S y conserva reintentos ante bloqueos temporales de Windows.
- **Estado**: completado
- **Descripción**: Resolver R23, R24; conservar las puertas y los datos ajenos.
- **Archivos**: `agent-kits/shared/capabilities.py`, `agent-kits/shared/journal.py`, `agent-kits/shared/journal-io.py`, `agent-kits/shared/outbox.py`, `agent-kits/shared/local-state.py`, `agent-kits/shared/journal-capture.py`, `tests/test_audit_journal.py`, `agent-kits/shared/test_journal.py`.
- **Verificación**: tests dirigidos del área y regresiones vecinas; evidencia en testing/validation.md.

**Criterios de aceptación**
- [x] R23, R24: escenarios de auditoría cubiertos, corregidos y sin regresiones conocidas.

RED: journal/capacidades → 6 failed: sondeo mutó bandera bytecode, cola siguió junction, gitignore hardlink modificado, materialización escapó, README ajeno sobrescrito y lectura aceptó hardlink.

RED adicional R24/B1: la CLI directa devolvió exit 0 sin crear envelope (test_journal_capture_cli_materializes_a_durable_envelope); wrapper movido antes de main.

RED B2/R6: 3 failed adicionales: dos primeras capturas concurrentes perdieron un prompt; diseño omitido para tarea por directorio padre o raíz. Correcciones con CAS/reintento acotado e intersección de rutas en ambos sentidos.

GREEN: journal/capacidades → 269 passed, 10 skipped tras conservar los contratos de concurrencia e indexado; ampliaciones y revisión final en testing/validation.md.

### T-09 — Contratos y documentación

- **Changelog**: Los contratos de agentes y las guías ES/EN reflejan las correcciones; npm declara sus capacidades de doble uso.
- **Estado**: completado
- **Descripción**: Resolver R15, declaración npm de doble uso (R25) y contratos de las correcciones; conservar las puertas y los datos ajenos.
- **Archivos**: `agents/**`, `package.json`, `DISCLOSURE`, `commands/pm-cycle.md`, `CLAUDE.md`, `docs/agents/**`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `docs/INTEROP.md`, `docs/en/INTEROP.md`, `docs/INSTALL.md`, `docs/en/INSTALL.md`, `docs/guides/**`, `docs/en/guides/**`, `agent-kits/shared/ledger-write.md`, `skills/plugin-dev/SKILL.md`.
- **Verificación**: tests dirigidos del área y regresiones vecinas; evidencia en testing/validation.md.

**Criterios de aceptación**
- [x] R15 y contratos de las correcciones: escenarios de auditoría cubiertos, corregidos y sin regresiones conocidas.

RED: R25 → test_npm_payload security_tooling falló por ausencia de contentPolicy; luego 5 passed sobre el tgz. TDD no aplica a prosa; se valida mediante contratos, lint, interop y revisión.

### T-10 — Regresiones, revisión y entrega

- **Changelog**: Regresiones reproducidas, revisión con Claude y lentes independientes documentadas con sus límites de plataforma.
- **Estado**: completado
- **Descripción**: Resolver Todos los hallazgos, sin Critical/Important pendientes; conservar las puertas y los datos ajenos.
- **Archivos**: `docs/roadmap/README.md`, `docs/roadmap/2026-11-05-audit-remediation/**`, `CHANGELOG.md`, `CHANGELOG.es.md`, `interop/**`, `.codex-plugin/**`, `.agents/plugins/**`, `tests/**`, `skills/unit-tests/scripts/coverage-gate.py`, `agent-kits/shared/execution-profile.py`, `agent-kits/shared/local-read.py`, `agent-kits/shared/doctor.py`, `skills/training-data-services/scripts/case_schema.py`, `skills/training-data-services/scripts/test_case_schema.py`.
- **Verificación**: tests dirigidos del área y regresiones vecinas; evidencia en testing/validation.md.

**Criterios de aceptación**
- [x] Todos los hallazgos, sin Critical/Important pendientes: escenarios de auditoría cubiertos, corregidos y sin regresiones conocidas.

Regresión adicional T-10: rutas físicas de Git y cobertura unificadas para aliases 8.3 de Windows; 31 tests de coverage-gate pasan sin modificar umbrales. Fixtures de publicación y recuperación instrumentan ahora StateIO (link + retirada del temporal), preservan barreras, canarios, bytes y aserciones. La caché compartida tiene propiedad de usuario separada y se conserva tras desinstalar una instancia; contrato documentado ES/EN.

Regresión de compatibilidad T-10: presupuestos explícitos de anidamiento JSON para perfil, snapshots de commit y respuestas del diagnóstico; no depender de RecursionError implícito del intérprete. El diagnóstico de arguments JSON textual conserva el campo de origen y el límite CoT de 50 niveles. Casos existentes rojos en Python 3.14 y nuevos límites 31/32/33; 68 + 82 casos dirigidos pasan en Windows.

## Revisión de dos lentes — intento 1: Fase 1; dictamen y continuaciones en testing/validation.md (T-01, T-02, T-03, T-04, T-05, T-06, T-07, T-08, T-09, T-10)

Lentes: A+B+C+D. Dictamen inicial: correcciones necesarias. El detalle y escenarios están en [validation.md](testing/validation.md).

| # | Grado | Gap | Tarea | Corrección / estado de ese intento | Evidencia |
|---|---|---|---|---|---|
| A1 | Important | Permisos antiguos descritos | T-09 | Pendiente de corregir | revisión A1 |
| B1 | Critical | Wrapper de captura después de main | T-08 | RED subprocess; corregido después | test_audit_journal |
| B2 | Important | Inicialización concurrente pierde prompt | T-08 | RED barrera real; corrección posterior | test_audit_journal |
| B3 | Important | Marcador de recuperación rechazado | T-08 | Corrección posterior | test_outbox |
| B4 | Important | Resumen legado idéntico bloqueado | T-04 | Corrección posterior | test_audit_knowledge |
| B5 | Important | Caché común no reutilizable en proyecto B | T-01 | Recibo de usuario posterior | installer.test |
| B6 | Important | Aliases de sistema macOS rechazados | T-01 | Contrato de alias posterior | install-auth.test |
| B7 | Important | Fixtures sin propiedad autenticada | T-01 | Fixtures sintéticas posteriores | installer.test |
| B8 | Important | Idle admite envío concurrente | T-05 | Corrección posterior | test_audit_console |
| B9 | Minor | Continuidad del histórico no declarada | T-03 | Presupuesto explícito posterior | test_audit_ledger |
| D1 | Important | Listado de roadmap por fila | T-03 | Escaneo lazy posterior | test_retro_gate |
| D2 | Important | Recorrido completo del histórico de cola | T-08 | IO guardada posterior | test_outbox |
| D3 | Minor | Rotación lee log completo | T-08 | Lectura de cola posterior | test_journal |
| R6 | Important | Tarea por directorio omite diseño | T-02 | Intersección inversa posterior | test_audit_briefs |

C: sin hallazgos introducidos confirmados; no equivale a auditoría completa.

## Revisión de dos lentes — intento 2: Fase 1; dictamen y continuaciones en testing/validation.md (T-01, T-02, T-03, T-04, T-05, T-06, T-07, T-08, T-09, T-10)

Lentes: A+B+C+D. A/C/D sin nuevos gaps; B exige corregir dos residuales. [Detalle](testing/validation.md).

| # | Grado | Gap | Tarea | Corrección / estado de ese intento | Evidencia |
|---|---|---|---|---|---|
| A1/B1/B3/B4/B5/B7/B8/R6 | — | Hallazgos previos | T-01,T-02,T-04,T-05,T-08,T-09 | Corregidos | tablas S2 de validation.md |
| B6 | — | Aliases macOS | T-01 | Contrato corregido; macOS real no ejecutado | install-auth.test |
| B9/D1/D2/D3 | — | Histórico/listados/rotación | T-03,T-08 | Corregidos | revisión D2 |
| B2 | Important | Ventana transitoria link-unlink | T-08 | Corrección posterior con relectura acotada | test_audit_journal |
| B10 | Important | fsync previo aparenta publicación | T-08 | Corrección posterior; ACK sólo tras publicar | test_audit_journal |
| HTTP422/inflight | Descartado | Entrega incierta interpretada como bloqueo permanente | T-05 | Rebatido: disconnect/resume admite mensaje explícito | driver real + cliente sintético |

Claude CLI: success/end_turn; revisión parcial completada por el revisor B con reproducción. No se reenvían entregas inciertas automáticamente.

## Revisión de dos lentes — intento 3: Fase 1; dictamen y continuaciones en testing/validation.md (T-01, T-02, T-03, T-04, T-05, T-06, T-07, T-08, T-09, T-10)

Lentes: A+B+C+D. A/C/D sin gaps nuevos; B descubre B11. [Detalle y decisión](testing/validation.md).

| # | Grado | Gap | Tarea | Corrección / estado de ese intento | Evidencia |
|---|---|---|---|---|---|
| B2/B10 | — | Residuales anteriores | T-08 | Corregidos | revisión B3 |
| B11 | Important | Bloqueo exclusivo se clasifica permanente | T-08 | Impide cierre; corrección y continuación explícitas | handles CreateFileW reales |
| A/C/D | — | Sin nuevos gaps | T-01–T-10 | Dictamen limitado a S3 | revisión S3 |

### Continuaciones explícitas 4 y 5

Agotado el bucle ordinario de tres intentos, el orquestador decidió continuar y después replanificar según la orden vigente de corregir todos los hallazgos. No se oculta ni se reinicia el contador y no se acepta deuda.

| Iteración | Lentes | Dictamen | Evidencia |
|---|---|---|---|
| 4 | A+B+C; D no despachada | A/C sin nuevos gaps; B11 residual en publicación impide cierre | S4, validation.md |
| 5 | A+B+C+D | B11 corregido en read/write/update; sin nuevos defectos o vulnerabilidades; D cubre delta acumulado desde S3 | A:sin gaps, interop92; B:221 passed/3 skipped; C:196/8; D:10 passed |

Conformidad final A5 sin gaps. T-10 conserva su estado abierto hasta CI de referencia. No hay publicación npm ni efectos sobre servicios reales.

### Continuación explícita 6 — B12 de CI

Run 42078982134: Python 10.469 passed/41 skipped; Node 464 passed/16 skipped/1 failed. T-01 reabierta por temporal atómico fuera del inventario. RED con barrera real antes de rename; cinco variantes Windows verdes tras staging con identidad firmada. Revisión y regresión completas del delta pendientes; T-10 sigue abierta. [Diagnóstico y decisión](testing/validation.md#ci-de-referencia-y-b12--continuación-6).

### Continuación explícita 7 — presupuesto de checkpoints

B12 recupera correctamente, pero S6 excedió la cota existente (9 frente a 8), reproducido en Linux y Windows. Corrección sin relajar el test: registro único de rutas preflightadas y snapshots iniciales/final. Test de presupuesto y recuperación de upgrade verdes en Windows. T-01/T-10 abiertas hasta revisión y validación final. [Evidencia](testing/validation.md#continuación-7--presupuesto-de-checkpoints).

### Dictamen de la continuación 7

| Lente | Resultado | Evidencia |
|---|---|---|
| A | Sin gaps nuevos; A6-1 corregido | Test de presupuesto correcto; interop 92 al día |
| B | Sin defectos nuevos | 12 passed, cero fallos/omisiones |
| C | Sin vulnerabilidades nuevas | 29 passed; preflight, autenticidad y recuperación preservados |
| D | Sin nuevos hallazgos | Tres checkpoints en cargas de 100/1.000/5.000 archivos; umbral inalterado |

Regresión final Linux: Node 470 passed/16 skipped/cero failed; tgz 5 passed. T-01 verificada, T-10 conserva CI de referencia pendiente. [Detalle](testing/validation.md#dictamen-final-del-código--s7--aa25dda).

## Cierre verificado

CI de referencia [42085116173](https://github.com/daycry/custom-agents/actions/runs/42085116173), código aa25dda: success en todas las puertas. Python 10.469 passed/41 skipped/82 subtests; Node 470 passed/16 skipped/cero failed. Benchmark p95 2,65 ms/p99 2,94 ms frente a 100/300 ms. A7+B7+C7+D7 sin Critical/Important pendientes, sin relajar puertas. T-10 cumplida. No se publica versión ni paquete npm.
