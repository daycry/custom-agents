# `docs/knowledge/` — memoria técnica del proyecto

Índice de **entrada** — un fichero por entrada (`adr/`, `gotchas/`, `lessons/`; decisión
[`adr/ADR-006`](adr/)). El índice generado + `knowledge-lint.py` siguen diferidos (ver
`docs/roadmap/2026-08-20-knowledge-capture/spec.md` D4: se retoma con >15 entradas o la primera
colisión de IDs de cualquiera de las tres familias — ADR/GOT/LES, ver `adr/ADR-006`) — mientras
tanto, **este es el único punto de entrada**: la lectura
SELECTIVA (`agent-kits/shared/knowledge-check.md`) empieza y termina aquí salvo que la tarea
requiera abrir una entrada concreta. **Quien añade una entrada actualiza esta tabla en el mismo
cambio.**

- **`adr/`** — decisiones de diseño (una por fichero, `ADR-NNN-<slug>.md`).
- **`gotchas/`** — trampas comprobadas (una por fichero, `GOT-NNN-<slug>.md`).
- **`lessons/`** — lecciones de proceso (una por fichero, `LES-NNN-<agente>-<slug>.md`).

Siempre activa, sin opt-in (D3): si esta carpeta no existiera, los agentes seguirían sin quejarse
y se crearía en el primer registro. Umbral de registro y quién escribe/lee: ver
`agent-kits/shared/knowledge-write.md` / `knowledge-check.md` y `docs/CONVENTIONS.md`.

## Índice

| Entrada | ID | Tipo | Área | Estado | Fuente |
|---|---|---|---|---|---|
| [`lessons/LES-001-evaluator-coste-revision-no-escribir.md`](lessons/LES-001-evaluator-coste-revision-no-escribir.md) — "El coste real de una iniciativa se va en la revisión, no en escribir." | LES-001 | Lección | Estimación / calibración | aceptada (validada: revisión de dos lentes, 2026-08-20, intento 3) | `2026-08-12-sdd-hardening/retro.md#aprendizajes` |
| [`lessons/LES-002-evaluator-medir-cambia-diagnostico.md`](lessons/LES-002-evaluator-medir-cambia-diagnostico.md) — "Medir cambia el diagnóstico, no solo el número." | LES-002 | Lección | Estimación / calibración | aceptada (validada: revisión de dos lentes, 2026-08-20, intento 3) | `2026-08-12-sdd-hardening/retro.md#aprendizajes` |
| [`lessons/LES-003-evaluator-calibrar-datos-reales-cambia-cifras.md`](lessons/LES-003-evaluator-calibrar-datos-reales-cambia-cifras.md) — "Calibrar con datos reales cambia cifras ya publicadas, y eso es sano." | LES-003 | Lección | Estimación / calibración | aceptada (validada: revisión de dos lentes, 2026-08-20, intento 3) | `2026-08-12-sdd-hardening/retro.md#estimado-vs-real` |
| [`lessons/LES-004-evaluator-iniciativa-prosa-se-mide-en-minutos.md`](lessons/LES-004-evaluator-iniciativa-prosa-se-mide-en-minutos.md) — "Una iniciativa de solo prosa... se mide en minutos, no en horas." | LES-004 | Lección | Estimación / calibración | aceptada (validada: revisión de dos lentes, 2026-08-20, intento 3) | `2026-08-12-workflow-polish/retro.md#estimado-vs-real` |
| [`lessons/LES-005-evaluator-tdd-encarece-ejecucion-abarata-revision.md`](lessons/LES-005-evaluator-tdd-encarece-ejecucion-abarata-revision.md) — "El TDD encarece la ejecución y abarata la revisión." | LES-005 | Lección | Estimación / calibración | aceptada (validada: revisión de dos lentes, 2026-08-20, intento 3) | `2026-08-12-subagent-personas/retro.md` |
| [`lessons/LES-006-evaluator-escribir-spec-antes-reduce-coste.md`](lessons/LES-006-evaluator-escribir-spec-antes-reduce-coste.md) — "Escribir la spec antes... reduce el coste de implementarla después." | LES-006 | Lección | Estimación / calibración | aceptada (validada: revisión de dos lentes, 2026-08-20, intento 3) | `2026-08-13-quick-implement/retro.md` |
| [`lessons/LES-007-evaluator-separa-lo-que-mides-de-lo-que-vendes.md`](lessons/LES-007-evaluator-separa-lo-que-mides-de-lo-que-vendes.md) — "Separa lo que mides de lo que vendes." (1/3) | LES-007 | Lección | Estimación / calibración | aceptada (validada: revisión de dos lentes, 2026-08-20, intento 3) | `agents/evaluator.md` (histórico de git) |
| [`lessons/LES-008-evaluator-presupuesta-coste-proceso-aparte.md`](lessons/LES-008-evaluator-presupuesta-coste-proceso-aparte.md) — "Presupuesta el coste de PROCESO aparte." (2/3) | LES-008 | Lección | Estimación / calibración | aceptada (validada: revisión de dos lentes, 2026-08-20, intento 3) | `agents/evaluator.md` (histórico de git) |
| [`lessons/LES-009-evaluator-revision-es-partida-grande.md`](lessons/LES-009-evaluator-revision-es-partida-grande.md) — "La revisión es la partida grande, no escribir." (3/3) | LES-009 | Lección | Estimación / calibración | aceptada (validada: revisión de dos lentes, 2026-08-20, intento 3) | `agents/evaluator.md` (histórico de git) |
| [`gotchas/GOT-001-plantilla-sin-probar-esconde-defectos.md`](gotchas/GOT-001-plantilla-sin-probar-esconde-defectos.md) — plantilla sin probar rellenándola esconde defectos | GOT-001 | Gotcha | Plantillas / revisión | aceptada (validada: revisión de dos lentes, 2026-08-20, intento 3) | `2026-08-12-plugin-dev/retro.md` |
| [`adr/ADR-001-alcance-publicacion-curado.md`](adr/ADR-001-alcance-publicacion-curado.md) | ADR-001 | ADR | Confluence / publicación | aceptada (validada: revisión de dos lentes, 2026-08-20, intento 3) | `confluence-policy/spec.md` D1 |
| [`adr/ADR-002-sin-presets-audiencia.md`](adr/ADR-002-sin-presets-audiencia.md) | ADR-002 | ADR | Confluence / publicación | aceptada (validada: revisión de dos lentes, 2026-08-20, intento 3) | `confluence-policy/spec.md` D2 |
| [`adr/ADR-003-ledger-sincroniza-al-cerrar-fase.md`](adr/ADR-003-ledger-sincroniza-al-cerrar-fase.md) | ADR-003 | ADR | Confluence / implementer | aceptada (validada: revisión de dos lentes, 2026-08-20, intento 3) | `confluence-policy/spec.md` D3 |
| [`adr/ADR-004-testing-excluido-del-espejo.md`](adr/ADR-004-testing-excluido-del-espejo.md) | ADR-004 | ADR | Confluence / qa | aceptada (validada: revisión de dos lentes, 2026-08-20, intento 3) | `confluence-policy/spec.md` D4 |
| [`adr/ADR-005-verificador-y-staging-generado.md`](adr/ADR-005-verificador-y-staging-generado.md) | ADR-005 | ADR | Confluence / staging | aceptada (validada: revisión de dos lentes, 2026-08-20, intento 3) | `confluence-policy/spec.md` D5 |
| [`gotchas/GOT-002-fixture-gitignore-rompe-en-clon-limpio.md`](gotchas/GOT-002-fixture-gitignore-rompe-en-clon-limpio.md) — fixture bajo `.gitignore`, suite rota en clon limpio | GOT-002 | Gotcha | Tests / fixtures | aceptada (validada: usuario, 2026-08-20) | `2026-08-20-confluence-policy/tasks.md` (gap I1) vía `retro.md` |
| [`gotchas/GOT-003-generado-en-alcance-pisa-canonico.md`](gotchas/GOT-003-generado-en-alcance-pisa-canonico.md) — generado que pisa/borra canónico en el espejo | GOT-003 | Gotcha | Confluence / staging | aceptada (validada: usuario, 2026-08-20) | `2026-08-20-confluence-policy/tasks.md` (gaps C1/C2) vía `retro.md` |
| [`adr/ADR-006-un-fichero-por-entrada-gotchas-y-lecciones.md`](adr/ADR-006-un-fichero-por-entrada-gotchas-y-lecciones.md) | ADR-006 | ADR | Memoria técnica / lectura-escritura | aceptada (validada: usuario, 2026-08-20) | `2026-08-20-knowledge-split/tasks.md` |
| [`adr/ADR-007-deny-solo-con-alcance-de-agente.md`](adr/ADR-007-deny-solo-con-alcance-de-agente.md) — un hook de guardia (deny) solo en el frontmatter `hooks:` de un agente, nunca en `hooks/hooks.json` | ADR-007 | ADR | Hooks / implementer | aceptada (validada: revisión de dos lentes, 2026-09-02, intento 2) | `2026-09-02-deterministic-guardrails/tasks.md` |
| [`gotchas/GOT-004-conector-jira-transicion-por-nombre-y-assignee-default.md`](gotchas/GOT-004-conector-jira-transicion-por-nombre-y-assignee-default.md) — transición de cierre por nombre y asignado por defecto rompen contra Jira real | GOT-004 | Gotcha | Jira / conector | aceptada (validada: usuario, 2026-09-02) | `2026-08-10-jira-granularity/tasks.md` (T-08, dry-run PROJ-60) |
| [`lessons/LES-010-dev-cycle-revision-adversarial-a-skill.md`](lessons/LES-010-dev-cycle-revision-adversarial-a-skill.md) — "Un mecanismo que caza críticos de forma repetida pasa a ser skill reutilizable" (revisión de dos lentes → `adversarial-review`, 5 ledgers) | LES-010 | Lección | Proceso / revisión adversarial | aceptada (validada: revisión de dos lentes, 2026-09-02, intento 2) | `2026-09-02-adversarial-review/tasks.md` + tablas de revisión de 5 ledgers |
