---
tasks: audit-remediation
estado: en-progreso
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
| Fase 1 | 0 | 10 | 0.0% |
| **TOTAL** | **0** | **10** | **0.0%** |

## Fase 1

**Estado**: en-progreso

### T-01 — Instalador y propiedad

- **Estado**: en-progreso
- **Descripción**: Resolver R1, R2, R3; conservar las puertas y los datos ajenos.
- **Archivos**: `install/**`, `tests/installer.test.mjs`, `tests/install-auth.test.mjs`.
- **Verificación**: tests dirigidos del área y regresiones vecinas; evidencia en testing/validation.md.

**Criterios de aceptación**
- [ ] R1, R2, R3: escenarios de auditoría cubiertos, corregidos y sin regresiones conocidas.

RED: `tests/installer.test.mjs` (R1/R2/R3, 7 casos) falló con 7 failed: comandos/borrados no rechazados, edición perdida y scope inválido aceptado · 2026-11-05.

GREEN: R1/R2/R3 → 7 passed. Regresión completa del instalador pendiente de la validación combinada.

### T-02 — Hooks y briefs

- **Estado**: en-progreso
- **Descripción**: Resolver R4, R5, R6; conservar las puertas y los datos ajenos.
- **Archivos**: `hooks/run-hook.mjs`, `agent-kits/shared/task-brief.py`, `tests/test_audit_briefs.py`.
- **Verificación**: tests dirigidos del área y regresiones vecinas; evidencia en testing/validation.md.

**Criterios de aceptación**
- [ ] R4, R5, R6: escenarios de auditoría cubiertos, corregidos y sin regresiones conocidas.

RED: `tests/test_audit_briefs.py` falló con 6 failed / 3 passed: criterios omitidos, rutas de diseño no reconocidas y marcador fuera de docs · 2026-11-05.

GREEN: hooks/briefs → 101 passed con la suite vecina.

### T-03 — Ledger, alcance y retro

- **Estado**: en-progreso
- **Descripción**: Resolver R7, R8, R16, R17; conservar las puertas y los datos ajenos.
- **Archivos**: `agent-kits/shared/scope-check.py`, `agent-kits/shared/retro-gate.py`, `agent-kits/shared/ledger-write.py`, `agent-kits/shared/ledger-archive.py`, `commands/retro.md`, `tests/test_audit_ledger.py`, `agent-kits/shared/test_retro_gate.py`, `agent-kits/shared/test_ledger_archive.py`.
- **Verificación**: tests dirigidos del área y regresiones vecinas; evidencia en testing/validation.md.

**Criterios de aceptación**
- [ ] R7, R8, R16, R17: escenarios de auditoría cubiertos, corregidos y sin regresiones conocidas.

RED: `tests/test_audit_ledger.py` R7/R8/R16/R17 falló por rutas escapadas, calibración anterior aceptada, descripción alterada y archivado sin rechazar concurrencia/enlaces; POSIX mode no ejecutable en Windows · 2026-11-05.

GREEN: ledger/alcance/retro → 100 passed, 3 skipped (plataforma).

### T-04 — Publicación y curación

- **Estado**: en-progreso
- **Descripción**: Resolver R9, R10, R11, R12, R21; conservar las puertas y los datos ajenos.
- **Archivos**: `skills/knowledge-services/**`, `skills/confluence-publish/scripts/confluence-scope.py`, `agent-kits/shared/knowledge-curation.py`, `tests/test_audit_knowledge.py`, `tests/test_knowledge_sync.py`.
- **Verificación**: tests dirigidos del área y regresiones vecinas; evidencia en testing/validation.md.

**Criterios de aceptación**
- [ ] R9, R10, R11, R12, R21: escenarios de auditoría cubiertos, corregidos y sin regresiones conocidas.

RED: publicación/curación → 6 failed: replay envió cuerpo retirado; resumen filtró párrafo completo; cambio de proyección ignorado; staging incluyó seguridad; origen omitido; generación propia no reconocida.

### T-05 — Sesiones y consola

- **Estado**: en-progreso
- **Descripción**: Resolver R13, R14, P1, P2; conservar las puertas y los datos ajenos.
- **Archivos**: `skills/plugin-panel/**`, `tests/test_console_*.py`, `tests/test_audit_console.py`.
- **Verificación**: tests dirigidos del área y regresiones vecinas; evidencia en testing/validation.md.

**Criterios de aceptación**
- [ ] R13, R14, P1, P2: escenarios de auditoría cubiertos, corregidos y sin regresiones conocidas.

RED: consola → 6 failed: turno fallido bloqueó mensaje explícito, driver muerto retuvo slot, sondeo idle no recuperó, aprobación procesó 500k caracteres, pipe hizo 65.549 lecturas, ruta larga dio 404.

### T-06 — Exportación portable e interop

- **Estado**: en-progreso
- **Descripción**: Resolver R18, R19; conservar las puertas y los datos ajenos.
- **Archivos**: `scripts/export-skills.py`, `scripts/export-interop.py`, `tests/test_audit_exports.py`.
- **Verificación**: tests dirigidos del área y regresiones vecinas; evidencia en testing/validation.md.

**Criterios de aceptación**
- [ ] R18, R19: escenarios de auditoría cubiertos, corregidos y sin regresiones conocidas.

RED: exportación → 3 failed: catálogo ausente en portable completo/core; hardlink sobrescrito sin preflight.

### T-07 — Jira y worklogs

- **Estado**: en-progreso
- **Descripción**: Resolver R20, R22; conservar las puertas y los datos ajenos.
- **Archivos**: `skills/jira-sync/**`, `tests/test_audit_jira.py`.
- **Verificación**: tests dirigidos del área y regresiones vecinas; evidencia en testing/validation.md.

**Criterios de aceptación**
- [ ] R20, R22: escenarios de auditoría cubiertos, corregidos y sin regresiones conocidas.

RED: Jira → 3 failed: secreto reconocido viajó en comentario, invocación anidada desactivó Jira y comando worklog usó jornada 99 del cwd ajeno.

### T-08 — Lecturas de capacidades y journal

- **Estado**: en-progreso
- **Descripción**: Resolver R23, R24; conservar las puertas y los datos ajenos.
- **Archivos**: `agent-kits/shared/capabilities.py`, `agent-kits/shared/journal.py`, `agent-kits/shared/journal-io.py`, `agent-kits/shared/journal-capture.py`, `tests/test_audit_journal.py`, `agent-kits/shared/test_journal.py`.
- **Verificación**: tests dirigidos del área y regresiones vecinas; evidencia en testing/validation.md.

**Criterios de aceptación**
- [ ] R23, R24: escenarios de auditoría cubiertos, corregidos y sin regresiones conocidas.

GREEN: Jira ? 76 passed; un test de posici?n del argumento actualizado a su significado (`--clave`); repetici?n final pendiente.

RED: journal/capacidades → 6 failed: sondeo mutó bandera bytecode, cola siguió junction, gitignore hardlink modificado, materialización escapó, README ajeno sobrescrito y lectura aceptó hardlink.

### T-09 — Contratos y documentación

- **Estado**: en-progreso
- **Descripción**: Resolver R15, declaración npm de doble uso (R25) y contratos de las correcciones; conservar las puertas y los datos ajenos.
- **Archivos**: `agents/**`, `package.json`, `DISCLOSURE`, `commands/pm-cycle.md`, `CLAUDE.md`, `docs/agents/**`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `docs/INTEROP.md`, `docs/en/INTEROP.md`, `docs/INSTALL.md`, `docs/en/INSTALL.md`, `docs/guides/**`, `docs/en/guides/**`, `agent-kits/shared/ledger-write.md`, `skills/plugin-dev/SKILL.md`.
- **Verificación**: tests dirigidos del área y regresiones vecinas; evidencia en testing/validation.md.

**Criterios de aceptación**
- [ ] R15 y contratos de las correcciones: escenarios de auditoría cubiertos, corregidos y sin regresiones conocidas.

GREEN: journal/capacidades ? 269 passed, 10 skipped tras conservar los contratos de concurrencia e indexado.

RED: R25 → test_npm_payload security_tooling falló por ausencia de contentPolicy; luego 5 passed sobre el tgz. TDD no aplica a prosa; se valida mediante contratos, lint, interop y revisión.

### T-10 — Regresiones, revisión y entrega

- **Estado**: en-progreso
- **Descripción**: Resolver Todos los hallazgos, sin Critical/Important pendientes; conservar las puertas y los datos ajenos.
- **Archivos**: `docs/roadmap/README.md`, `docs/roadmap/2026-11-05-audit-remediation/**`, `CHANGELOG.md`, `CHANGELOG.es.md`, `interop/**`, `.codex-plugin/**`, `.agents/plugins/**`, `tests/**`.
- **Verificación**: tests dirigidos del área y regresiones vecinas; evidencia en testing/validation.md.

**Criterios de aceptación**
- [ ] Todos los hallazgos, sin Critical/Important pendientes: escenarios de auditoría cubiertos, corregidos y sin regresiones conocidas.
