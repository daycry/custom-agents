# CONTINUE-HERE.md

Estado de trabajo en curso para retomar sin perder contexto (tras compactación o
un corte de sesión). Si estás leyendo esto al empezar una sesión: lee este
fichero ANTES de tocar nada. Bórralo (o vacíalo a "sin trabajo pendiente")
cuando la rama descrita aquí se publique y no quede nada abierto.

Última actualización: 2026-09-08.

## Dónde está el trabajo

- Rama: `feature/pendiente`, creada sobre `master` en `2d48980` (v1.17.1, ya
  publicada). Nada empujado todavía — Jordi no ha visto ni aplicado nada de
  este contenido.
- Sesión del 2026-09-08 (Windows 11, Git Bash, Claude Code en la máquina de
  Jordi): se trabajó DIRECTAMENTE sobre el repo, con commits locales por tarea.
  Para que las puertas corran en esta máquina hace falta el venv:
  `python -m venv .venv` (ya creado, ignorado por git) con
  `cp .venv/Scripts/python.exe .venv/Scripts/python3.exe` y `pip install pytest`;
  luego `export PATH="$PWD/.venv/Scripts:$PATH"` antes de cualquier `python3`
  (el `python3` del sistema es el alias de la Microsoft Store y los hooks
  callan). Fallos de suite que quedan en Windows son artefactos conocidos
  (separador `\` en asserts de `relpath`, bit `+x`, `os.symlink` en el helper
  `sin_python3`, rutas con espacios en `coverage-gate`, `WinError 5` en evals,
  CRLF en `test_knowledge_find --show`, los 6 `test_progress_line_*`); CI es
  Linux. Detalle en `CONTINUE-HERE.local.md` (fichero local de Jordi, sin
  seguimiento).
- Árbol: limpio salvo 3 ficheros sin seguimiento preexistentes y ajenos a la
  iniciativa (`.claude/.headroom_wrap_marker.json`, `CONTINUE-HERE.local.md`,
  `feature-pendiente.bundle`) — `scope-check` los marca «fuera de alcance» por
  eso; decisión de Jordi si van al `.gitignore`.

## Qué hay dentro de `feature/pendiente` (dos iniciativas)

### 1. `docs/roadmap/2026-09-04-sin-motor-externo/` — **completado**

Elimina toda referencia a "superpowers"/"Modo A" (delegación a un plugin
externo) de piezas vivas. 5 tareas, revisión de dos lentes intento 1: 10 gaps
→ todos corregidos. `estado: completado`.

### 2. `docs/roadmap/2026-09-04-memory-retrieval/` — **Fases 1-4 completadas y revisadas; Fases 5-6 pendientes**

Plan de 18 tareas / 6 fases (+ T-19 y T-20, cierres de gaps de revisión).

**Hecho (Fases 1-3, T-01..T-10 + T-19, 2026-09-07):** `knowledge-find.py` (3
capas, índice FTS5 reconstruible), lint de biyección del índice de
`docs/knowledge/`, memoria técnica en `task-brief.py` y en `session-context.sh`,
tabla de invocación por agente, `tests/test_memory_path.py`, evals, bloque
«Memoria técnica» de `/doctor`. Revisión intento 1: 12 gaps → 12 corregidos.

**Hecho (Fase 4, T-11..T-14 + T-20, 2026-09-08):**
- T-11 `hooks/user-prompt-capture.sh` → `journal.py capture`: hook
  `UserPromptSubmit` (contrato oficial verificado y fechado 2026-09-08 en el
  docstring) que acumula el turno del usuario en
  `.claude/session-prompts-<session_id>.log` (no versionado; `capture` siembra
  `.claude/.gitignore` para proyectos consumidores), opt-out `<private>` por
  turno y `dev.json` `sesion.journal|captura: false` por proyecto; secretos
  evidentes redactados antes de escribir; log `0600` + cerrojo `<log>.lock`;
  topes por turno/fichero y purga a 30 días; nunca stdout, siempre exit 0.
- T-12 `journal.py draft/write`: `decisiones`/`pendientes` extraídas SIN modelo
  del log (marcadores léxicos ES/EN; sin marcadores → `[]` honesto),
  `resumen` = primer turno capturado, campos `resumen_por`/`turnos`;
  `ADR-010` revisado con fecha (restricción conservada, conclusión revisada:
  «el hook no devuelve, escribe»); escritura atómica de la entrada.
- T-13 resumen por IA opt-in (`dev.json` `sesion.resumen: true`):
  `claude -p --bare --output-format json`, turnos por stdin como datos,
  timeout 25 s (`hooks.json` SessionEnd `timeout: 45`), entrada determinista
  primero y re-escritura de la misma; sin CLI/clave/timeout/JSON → determinista
  con el motivo en `avisos`. `--enrich` manda sobre la IA.
- T-14 `journal.py candidatas`: patrones de `decisiones`/`pendientes` repetidos
  en ≥ 2 sesiones (Jaccard ≥ 0,6 sobre raíces de `knowledge-find.py`) →
  candidatas `propuesta` con evidencia; `/retro` paso 2-quater las muestra;
  nunca nacen `aceptada`.
- T-20 cierra los 16 gaps de la revisión de dos lentes intento 1 (A+B+C; 1
  Critical: `<private>` resucitaba vía transcripción; 6 Important) — 15
  corregidos, 1 (deuda de doc) delegado a **T-18 con `Archivos` y criterio
  ampliados**. Traza: sección «Revisión de dos lentes — intento 1 (Fase 4)» al
  final del ledger.
- Puertas al cierre: `lint_plugin` 0 errores · `evals/check` 0 errores ·
  `ledger-lint` 0 incoherencias · `test_journal.py` 40 passed + 1 skipped
  (POSIX) · CA-08 (`task-brief` ≤ 10.000) verde tras recortar T-19.

**Pendiente (Fases 5-6, T-15..T-18 — NO empezado, solo especificado):**
- Fase 5 — Que la doctrina viaje: doctrina del plugin como assets separada de
  la memoria del proyecto (T-15); `evaluator` la usa sin engordar su prompt
  (T-16).
- Fase 6 — Cerrar el bucle: `/retro` se dispara al cerrar una iniciativa
  (T-17); doc ES/EN + entradas de `docs/knowledge/` de esta iniciativa (T-18).
  **T-18 arrastra la deuda de doc de F3 y F4** (ya listada en su criterio
  nuevo): `docs/observability.md` (ES/EN) dice «Sin resumen por IA» y
  `timeout: 20`; `docs/FLOWS.md` (ES/EN) sin nodo `UserPromptSubmit`;
  `docs/CONVENTIONS.md` regla 9 sin `sesion.captura`/`sesion.resumen`;
  `CLAUDE.md` tabla de hooks; `commands/doctor.md` + `docs/README.md` (seis
  bloques del doctor, con su eval); `docs/INSTALL.md`/`commands/setup.md` (qué
  se captura y cómo apagarlo); `agent-kits/shared/README.md` (fila de
  `journal.py`). Verificación: `grep -rn "Sin resumen por IA\|timeout: 20" docs/ CLAUDE.md` → 0.
- Cada fase que se implemente necesita su propia revisión de dos lentes
  (bucle acotado a 3) antes de darse por cerrada, como F1-3 y F4.
- Hallazgo de la revisión de F4 para tener en cuenta: la medida CA-08 del
  brief incluye la ruta ABSOLUTA de `knowledge-find.py`, así que varía con la
  máquina (~250 caracteres más en Windows con OneDrive). T-05/T-06/T-19 están
  cerca del tope; si un ledger crece, `test_ca08_*` avisa.

## Otros hilos (ya resueltos, sin nada pendiente)

- v1.16.0, v1.17.0, v1.17.1 publicadas. `v1.17.1` fue un hotfix de CI
  construido sobre la `master` publicada, no sobre esta rama.
- Los PRs de `daycry/custom-agents` con error en Actions eran solo 2 fallos
  antiguos de agosto. **Re-confirmar cuando se empuje `feature/pendiente`**
  (generará runs de CI nuevos).

## Cómo seguir desde aquí

1. Si quieres continuar la implementación: Fase 5 y Fase 6 de
   `memory-retrieval` (pueden ir en paralelo; F6 va después porque documenta
   todo lo anterior), cada una con su revisión de dos lentes.
2. Si quieres entregar ya lo que hay: `feature/pendiente` tiene
   sin-motor-externo + memory-retrieval F1-4 con sus revisiones cerradas.
   Puertas locales con el venv en PATH; `release.py --dry-run` antes de
   publicar. Nada empujado todavía.
3. Recordatorio permanente: el repo es público, nunca debe llevar datos
   corporativos de Atlassian ni nada específico de un cliente. Los tests de
   la Fase 4 usan secretos INVENTADOS (`ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123`,
   `AKIAIOSFODNN7EXAMPLE1`) para probar la redacción; no son reales.
