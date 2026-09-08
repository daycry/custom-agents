# CONTINUE-HERE.md

Estado de trabajo en curso para retomar sin perder contexto (tras compactación o
un corte de sesión). Si estás leyendo esto al empezar una sesión: lee este
fichero ANTES de tocar nada. Bórralo (o vacíalo a "sin trabajo pendiente")
cuando la rama descrita aquí se publique y no quede nada abierto.

Última actualización: 2026-09-08 (fin de la sesión que implementó F4-F6).

## Dónde está el trabajo

- Rama: `feature/pendiente`, creada sobre `master` en `2d48980` (v1.17.1, ya
  publicada). Nada empujado todavía — Jordi no ha visto ni aplicado nada de
  este contenido.
- Sesión del 2026-09-08 (Windows 11, Git Bash, Claude Code en la máquina de
  Jordi): se trabajó DIRECTAMENTE sobre el repo, con commits locales por tarea
  y por fase. Para que las puertas corran en esta máquina hace falta el venv:
  `python -m venv .venv` (ya creado, ignorado por git) con
  `cp .venv/Scripts/python.exe .venv/Scripts/python3.exe` y `pip install pytest`;
  luego `export PATH="$PWD/.venv/Scripts:$PATH"` antes de cualquier `python3`
  (el `python3` del sistema es el alias de la Microsoft Store y los hooks
  callan). Fallos de suite que quedan en Windows son artefactos conocidos
  (separador `\` en asserts de `relpath`, bit `+x`, `os.symlink` en el helper
  `sin_python3`, rutas con espacios en `coverage-gate`, `WinError 5` en evals,
  CRLF en `test_knowledge_find --show`, los 6 `test_progress_line_*`); CI es
  Linux. Detalle en `CONTINUE-HERE.local.md` (fichero local de Jordi, sin
  seguimiento). **Ojo:** `tests/test_console_encoding.py` solo descubre scripts
  VERSIONADOS — córrela después de `git add` de cualquier script nuevo con el
  snippet GOT-005, no antes (nos pasó con `retro-gate.py`).
- Árbol: limpio salvo 3 ficheros sin seguimiento preexistentes y ajenos a la
  iniciativa (`.claude/.headroom_wrap_marker.json`, `CONTINUE-HERE.local.md`,
  `feature-pendiente.bundle`) — `scope-check` los marca «fuera de alcance» por
  eso; decisión de Jordi si van al `.gitignore`.

## Qué hay dentro de `feature/pendiente` (dos iniciativas)

### 1. `docs/roadmap/2026-09-04-sin-motor-externo/` — **completado**

Elimina toda referencia a "superpowers"/"Modo A" de piezas vivas. 5 tareas,
revisión de dos lentes intento 1: 10 gaps → todos corregidos.

### 2. `docs/roadmap/2026-09-04-memory-retrieval/` — **CERRADA del todo (2026-09-08)**

21 tareas cerradas (18 del plan + T-19/T-20/T-21, cierres de tres revisiones
de dos lentes: 38 gaps, todos corregidos, 0 rebatidos). Evaluación, plan y
ledger `completado`; **retro escrita** (`retro.md` + fila en `CALIBRATION.md`,
horas humanas en 0 por decisión de Jordi, `tokens/hora` vacío porque nada se
midió); **puerta de retro abierta** (`retro-gate.py` → exit 0) y **spec
`implementada`**. Fue la primera iniciativa a la que se le exigió el paso 8
del ritual que ella misma introdujo.

**Ojo con el plugin instalado vs. la rama:** la sesión corrió con el plugin de
la caché (`~/.claude/plugins/cache/daycry/custom-agents/1.17.1/`), así que
`/retro`, `changelog-sync` y los hooks que se dispararon eran los de 1.17.1
(por eso no hay journal de esta iniciativa). Los pasos deterministas se
ejecutaron desde el repo (`agent-kits/shared/*.py`, `skills/*/scripts/*.py`)
y la prosa se siguió de la versión del repo. Para probar en vivo las piezas de
la rama antes de publicar: `claude --plugin-dir "<ruta del repo>"` (la vía que
usa `evals/run.py`; contrato `headless.md` verificado 2026-09-03).

**Entradas de `docs/knowledge/` que nacen `propuesta` de esta iniciativa** (si
Jordi las da por buenas → `aceptada (validada: usuario, 2026-09-08)`):
`ADR-013` (tres capas de la memoria), `LES-015` (privacidad de punta a punta,
con dos evidencias), `GOT-007` (la suite de codificación solo ve scripts
versionados), `GOT-008` (el tope CA-08 del brief depende de la ruta y del
corpus).

**Qué se construyó (F4-F6, todo con su revisión de dos lentes cerrada):**
- F4 (T-11…T-14 + T-20): hook `UserPromptSubmit` → `journal.py capture` (log
  crudo no versionado, `<private>`, secretos redactados, `.claude/.gitignore`
  sembrado, 0600, cerrojo); `SessionEnd` extrae `decisiones`/`pendientes` sin
  modelo; resumen IA opt-in (`sesion.resumen`, `claude -p --bare`, stdin);
  `journal.py candidatas` → `/retro` 2-quater; ADR-010 revisado.
- F5 (T-15, T-16): doctrina del plugin (`agent-kits/evaluator/assets/doctrina/`,
  9 copias byte a byte con test) + `knowledge-find.py --doctrina` (JSON con
  `corpus`/`origen`); evaluator 15.513 → 15.024 bytes LF.
- F6 (T-17, T-18 + T-21): `retro-gate.py` (puerta con exit code; acepta el
  formato REAL de las retros; solo bajo `docs/roadmap/`), ritual 6→9 de
  `/dev-cycle`, `/retro` puerta; ADR-013 (tres capas) y LES-015 (privacidad de
  punta a punta) en `docs/knowledge/`, ambas `propuesta` (las promueve la
  revisión al no quedar gaps — si Jordi las da por buenas, `aceptada
  (validada: usuario, 2026-09-08)`); deuda de doc F3-F6 saldada en
  observability/FLOWS/CONVENTIONS ES+EN, CLAUDE.md, INSTALL ES+EN, /setup,
  /doctor, README del kit compartido.
- CHANGELOG `[Unreleased]`/`[Sin publicar]`: generado con `changelog-sync` al
  cerrar el ledger (ver el commit de cierre).

**Puertas al cierre** (Windows + venv): `lint_plugin` 0 errores · `evals/check`
0 errores · `ledger-lint` 0 incoherencias/0 avisos · CA-08 (briefs ≤ 10.000)
verde · suite completa: ver la última traza del ledger (los fallos que quedan
son las familias de Windows).

**Aviso de fragilidad conocido:** CA-08 mide el brief sobre el ledger REAL y
la sección de memoria del brief crece con `docs/knowledge/` hasta su tope
(2.400); T-19/T-20/T-21 están cerca del tope de 10.000 y `test_ca08_*` avisa.

## Otros hilos (ya resueltos, sin nada pendiente)

- v1.16.0, v1.17.0, v1.17.1 publicadas. `v1.17.1` fue un hotfix de CI sobre la
  `master` publicada, no sobre esta rama.
- Los PRs de `daycry/custom-agents` con error en Actions eran solo 2 fallos
  antiguos de agosto. **Re-confirmar cuando se empuje `feature/pendiente`**.

## Cómo seguir desde aquí

1. Nada pendiente en `memory-retrieval`. Opcional: promover a `aceptada` las
   cuatro entradas `propuesta` de arriba.
2. Entregar: `feature/pendiente` tiene sin-motor-externo + memory-retrieval
   completos. Puertas locales con el venv en PATH; `release.py --dry-run` antes
   de publicar (exige lint + evals + tests + copias `.MANUAL-COPY` al día).
3. Recordatorio permanente: el repo es público, nunca debe llevar datos
   corporativos de Atlassian ni nada específico de un cliente. Los tests de la
   Fase 4 usan secretos INVENTADOS (`ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123`,
   `AKIAIOSFODNN7EXAMPLE1`) para probar la redacción; no son reales.
