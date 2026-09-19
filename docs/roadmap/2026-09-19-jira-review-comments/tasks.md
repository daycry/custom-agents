---
verificacion: obligatoria
estado: completado
changelog: Fixed
generacion:               # vía rápida — ventana única de este ledger (usage-meter no abierto: orquestador en modo autónomo)
  fuente: estimado
  horas_ia: 0.4
  duracion: ~25m
---

# Checklist de Tareas — jira-review-comments (vía rápida: los comentarios de revisión no llegaban a Jira)

| | |
|---|---|
| **Estado** | completado |
| **Fecha** | 2026-09-19 |
| **Plan** | n/a — **vía rápida** (ledger ligero + revisión de dos lentes), a petición del usuario: «los reviews no añaden comentarios en las tareas de Jira: hace todo el flujo pero no se puede saber el resultado de la verificación ni de las x verificaciones de esa tarea» |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del plan. **Cualquier** implementador —el agente `implementer`, el chat principal, o un orquestador SDD externo— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.

> **Diagnóstico (causa raíz, con evidencia).** El mecanismo funciona: `jira-flow.py plan --event gaps --actor reviewer --task T-01 --intento 1` sobre el ledger real de `knowledge-services`, con un `.claude/jira.json` habilitado y un `jira-state.json` de prueba, devolvió las 3 `ops` (etiqueta `ca-reviewer` → transición `reabrir` → comentario con la tabla completa de los 7 gaps del intento 1 y el pie «intento 2 de 3»). Lo que fallaba era la **propiedad**: `commands/dev-cycle.md` (tabla de eventos) decía que `revision`/`gaps` los dispara `adversarial-review`; `skills/adversarial-review/SKILL.md` §6 decía «el orquestador dispara»; `skills/jira-sync/references/review-publish.md` decía «el agente revisor» (que es solo lectura y no tiene tools de Jira); `docs/agents/ROLES.md` decía «lo publica el orquestador/implementer». Cuatro textos, cuatro dueños distintos → nadie lo ejecutaba y el ciclo terminaba sin rastro del veredicto de cada intento en Jira (violación de «un rol, un dueño», `ADR-011`). Además `dev-cycle.md` remitía a un «comentario FINAL (Paso 9 de `jira-sync`)» que no existe (es el Paso 7 y es por intento).

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase 1 — Dueño único del evento de revisión en Jira | 2 | 2 | 100% | 0 / 1,0h | 0,4 (estimado) / 0,3h | 0 / 0,1h | — / 80k |
| **TOTAL** | **2** | **2** | **100%** | **0 / 1,0h** | **0,4 (estimado) / 0,3h** | **0 / 0,1h** | **— / 80k** |

---

## Fase 1 — Dueño único del evento de revisión en Jira

**Estado**: completado · **Estimado**: 1,0h · **Real**: — · **Coste est.**: ~50 € · **Tokens est.**: 80k

### T-01 — La skill `adversarial-review` publica el evento `revision`/`gaps` de CADA intento

- **Descripción**: `skills/adversarial-review/SKILL.md` §6 «Salida y traza» pasa de «el orquestador dispara» a un paso EJECUTABLE propio: nada más escribir la sección `## Revisión de dos lentes — intento N` corre `jira-flow.py plan --ledger <tasks.md> --event revision|gaps --actor reviewer --task T-XX --intento N --json` y aplica las `ops` con el conector; sin `jira.json`/issue degrada con aviso. `commands/dev-cycle.md`: la invocación de la skill (punto 2 de la Fase 3) deja de hablar de «comentario FINAL (Paso 9)» y dice «comentario firmado de CADA intento (Paso 7), lo ejecuta la propia skill»; la tabla de eventos fija el dueño («su paso 6, por intento; no el orquestador ni `reviewer`»); el bullet del worklog aclara que el comentario no es del orquestador. `skills/jira-sync/references/review-publish.md`: la cabecera del bloque `revision`/`gaps` nombra a la skill como ejecutor único (no al agente `reviewer`). `docs/agents/ROLES.md`: filas `reviewer` y `adversarial-review` coherentes con lo anterior. Interop regenerado.
- **Estado**: completado
- **Tipo**: docs (prosa de piezas: skill, comando, referencia, matriz de roles)
- **Tiempo humano**: est. 0,6h · real —
- **Tiempo IA (ejec.)**: est. 0,2h · real 0,3h (estimado; ventana compartida con T-02)
- **Supervisión**: est. 0,06h · real —
- **Archivos**: `skills/adversarial-review/SKILL.md`, `commands/dev-cycle.md`, `skills/jira-sync/references/review-publish.md`, `docs/agents/ROLES.md`, `interop/codex/prompts/dev-cycle.md`, `interop/opencode/commands/dev-cycle.md`
- **Verificación**: `grep -n "lo publica ESTA skill" skills/adversarial-review/SKILL.md && grep -c "Paso 9" commands/dev-cycle.md` → una coincidencia en la skill y `0` en el comando · `python scripts/export-interop.py --check` → «al día» · `python scripts/lint_plugin.py` → 0 errores
- **Changelog**: The adversarial review now posts its verdict to Jira after every attempt (the `revision`/`gaps` comment with the graded gap table), so each task's issue shows the result of each verification; before, four pieces each assumed another one would post it and nothing reached Jira.

**Criterios de aceptación**
- [x] Un solo dueño declarado en las cuatro piezas (skill §6, tabla de `dev-cycle`, `review-publish.md`, `ROLES.md`) y es el mismo: la skill `adversarial-review`
- [x] El paso de la skill es ejecutable tal cual (comando completo con `--actor reviewer --intento N`) y degrada con aviso sin Jira
- [x] Ninguna pieza remite ya a un «Paso 9» inexistente ni a un comentario «final» en lugar de «por intento»
- [x] `SKILL.md` ≤ 200 líneas; interop regenerado y `--check` limpio

### T-02 — Guardarraíl: test de propiedad única sobre los ficheros reales

- **Descripción**: `tests/test_review_jira_owner.py` lee los ficheros REALES (no fixtures) y falla si vuelve a abrirse el hueco: la skill contiene el comando `jira-flow.py … --event revision|gaps … --actor reviewer … --intento N`; la skill no dice que «el orquestador dispara» esos eventos; la tabla de `dev-cycle.md` nombra a `adversarial-review` en las filas `revision`/`gaps` y no cita «Paso 9» ni «comentario FINAL»; `review-publish.md` nombra a la skill como ejecutor; `ROLES.md` no atribuye la publicación al orquestador/implementer/reviewer. Además ejecuta `jira-flow.py` sobre un ledger de prueba con Jira habilitado y comprueba que el evento `gaps` del intento 1 produce el comentario con la tabla de gaps y el pie «intento 2 de 3» (así el test documenta también que el mecanismo funciona y que lo que faltaba era el dueño).
- **Estado**: completado
- **Tipo**: test
- **Tiempo humano**: est. 0,4h · real —
- **Tiempo IA (ejec.)**: est. 0,1h · real 0,1h (estimado)
- **Supervisión**: est. 0,04h · real —
- **Archivos**: `tests/test_review_jira_owner.py`
- **Verificación**: `python -m pytest -q tests/test_review_jira_owner.py` → todos en verde; revertir a mano la frase «el orquestador dispara» en la skill → el test falla nombrando la pieza
- **Changelog**: A regression test now guards that exactly one piece owns posting the review verdict to Jira.

**Criterios de aceptación**
- [x] El test corre contra los ficheros reales del repo y contra un ledger de prueba con Jira habilitado (mecanismo + propiedad)
- [x] Falla con mensaje que nombra la pieza y la frase ofensiva si se reintroduce un segundo dueño o el «Paso 9»
