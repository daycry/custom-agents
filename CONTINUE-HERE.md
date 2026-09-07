# CONTINUE-HERE.md

Estado de trabajo en curso para retomar sin perder contexto (tras compactación o
un corte de sesión). Si estás leyendo esto al empezar una sesión: lee este
fichero ANTES de tocar nada. Bórralo (o vacíalo a "sin trabajo pendiente")
cuando la rama descrita aquí se publique y no quede nada abierto.

Última actualización: 2026-09-07.

## Dónde está el trabajo

- Rama: `feature/pendiente`, creada sobre `master` en `2d48980` (v1.17.1, ya
  publicada). 24 commits por delante de `origin/master`, **nada empujado
  todavía** — Jordi no ha visto ni aplicado nada de este contenido.
- Árbol de trabajo limpio (`git status --porcelain` vacío) en el último punto
  verificado.
- El sandbox de Claude **no puede hacer `git push`** (403) ni debe ejecutar
  operaciones git destructivas sobre la carpeta del repo montada por OneDrive
  en la máquina de Jordi (el punto de montaje no permite `unlink`; un git
  interrumpido desde el sandbox deja `.git/index.lock` huérfano). Mecanismo de
  entrega usado en toda la sesión: construir en un worktree limpio → tar de los
  ficheros cambiados + `HASHES.txt` → `SendUserFile` → `device_commit_files` a
  `_to_delete/` en su máquina → `device_bash` descomprime y verifica hashes →
  correr las puertas (`lint_plugin.py`, `evals/check.py`, `pytest`,
  `scope-check.py`) en su máquina real → darle a Jordi los comandos exactos de
  git/release para que los ejecute él.

## Qué hay dentro de `feature/pendiente` (dos iniciativas, ambas con revisión de dos lentes cerrada)

### 1. `docs/roadmap/2026-09-04-sin-motor-externo/` — **completado**

Elimina toda referencia a "superpowers"/"Modo A" (delegación a un plugin
externo) de piezas vivas: `/dev-cycle` (flag `--superpowers`, bloque Modo A
completo, reglas de entrada/cierre), `README.md`/`README.es.md` (sección
"Compared with superpowers" retirada sin sustituto), fixture de
`skill-index`, cifras vivas del CHANGELOG. 5 tareas, revisión de dos lentes
intento 1: 10 gaps (3 Important, 7 Minor) → todos corregidos. `estado:
completado` en el frontmatter del ledger.

### 2. `docs/roadmap/2026-09-04-memory-retrieval/` — **Fases 1-3 completadas, Fases 4-6 pendientes**

Plan de 18 tareas / 6 fases para reforzar cómo `custom-agents` gestiona la
memoria técnica y recupera aprendizajes (motivado por el análisis de
`claude-mem`, ver `docs/roadmap/2026-09-04-ideas-externas/analysis.md` para
las ideas también extraídas de `WorldFlowAI/everything-claude-code`).

**Hecho (Fases 1-3, T-01..T-10 + T-19):**
- `agent-kits/shared/knowledge-find.py` (nuevo): búsqueda en 3 capas
  (consulta → `--related <ID>` por grafo curado → `--show <ID>`), índice
  SQLite FTS5 reconstruible en `.claude/knowledge-index.sqlite` (gitignored,
  degrada a escaneo plano si falla, nunca bloquea).
- `lint_plugin.py`: `lint_knowledge_index` (ERROR) verifica biyección
  README↔ficheros de `docs/knowledge/`.
- `task-brief.py`: sección "Memoria técnica del proyecto" enrutada por el
  campo `- **Tipo**:` de la tarea, con tope propio de caracteres.
- `hooks/session-context.sh`: inyecta memoria del área de la iniciativa
  activa al arrancar sesión, con tope propio y dedup por ID.
- `agent-kits/shared/knowledge-check.md` + `agents/*.md`: tabla explícita de
  invocación de `knowledge-find.py` por agente (7 agentes, `reviewer`
  incluido por primera vez).
- `tests/test_memory_path.py` (nuevo, gate + mutantes) y 2 casos nuevos en
  `evals/`.
- `agent-kits/shared/doctor.py`: bloque "Memoria técnica" (`/doctor`).
- Revisión de dos lentes intento 1: **12 gaps confirmados, los 12 corregidos**
  en una segunda ronda (9 commits, ledger T-19). Suite final: **1315 tests
  pasando**, `lint_plugin.py` exit 0, `evals/check.py` 135 casos/0 errores,
  `ledger-lint` 0 incoherencias, `scope-check --base 7ca3645` exit 0.

**Pendiente (Fases 4-6, T-11..T-18 — NO empezado, solo especificado):**
- Fase 4 — Captura episódica: hook `UserPromptSubmit` (T-11), `SessionEnd`
  escribe él mismo `decisiones`/`pendientes` revisando `ADR-010` (T-12),
  resumen episódico por IA opt-in (T-13), promoción journal→lección vía
  `/retro` (T-14).
- Fase 5 — Que la doctrina viaje: separar la doctrina que envía el plugin
  (especialmente LES-001..009 de estimación) de la memoria vacía-por-defecto
  del proyecto (T-15); que `evaluator` la use sin engordar su prompt (T-16).
- Fase 6 — Cerrar el bucle: `/retro` se dispara solo al cerrar una iniciativa
  (T-17); doc ES/EN + entradas propias de `docs/knowledge/` de esta iniciativa
  (T-18) — incluye deuda de doc ya identificada: `CONVENTIONS.md` regla 9,
  `/setup`, `commands/doctor.md`, `docs/README.md`, `docs/FLOWS.md`,
  `agent-kits/shared/README.md`.
- Cada fase que se implemente necesita su propia revisión de dos lentes
  (Lente A/B, bucle acotado a 3 intentos) antes de darse por cerrada, igual
  que se hizo con Fases 1-3 y con `sin-motor-externo`.

## Otros hilos de la sesión (ya resueltos, sin nada pendiente)

- v1.16.0, v1.17.0, v1.17.1 publicadas. `v1.17.1` fue un hotfix de CI
  (`tests/test_release.py` no fijaba la identidad git DENTRO del repo del
  fixture) construido sobre la `master` publicada, no sobre esta rama, a
  propósito, para no arrastrar contenido sin publicar.
- Los PRs de `daycry/custom-agents` con error en Actions eran solo 2 fallos
  antiguos de agosto — nada roto en ese momento. **Re-confirmar cuando se
  empuje `feature/pendiente`**, porque generará runs de CI nuevos.

## Cómo seguir desde aquí

1. Si quieres continuar la implementación: siguiente paso es lanzar Fase 4 y
   Fase 5 de `memory-retrieval` (pueden ir en paralelo; Fase 6 va después
   porque documenta todo lo anterior), luego su revisión de dos lentes.
2. Si quieres entregar ya lo que hay: empaquetar `feature/pendiente`
   (sin-motor-externo + memory-retrieval Fases 1-3) con el mecanismo de
   tarball+hashes+`device_commit_files` de siempre, verificar en la máquina de
   Jordi, y darle los comandos de push/release. Nada de esto se ha entregado
   todavía.
3. Recordatorio permanente: el repo es público, nunca debe llevar datos
   corporativos de Atlassian ni nada específico de un cliente.
