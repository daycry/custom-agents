# CONTINUE-HERE.md

Estado de trabajo en curso para retomar sin perder contexto (tras compactación o
un corte de sesión). Si estás leyendo esto al empezar una sesión: lee este
fichero ANTES de tocar nada. Bórralo (o vacíalo a "sin trabajo pendiente")
cuando la rama descrita aquí se publique y no quede nada abierto.

Última actualización: 2026-09-09 (tarde).

## Trabajo EN CURSO — tres iniciativas abiertas el 2026-09-09 (rama `feature/project-specialization`)

Todo en la rama `feature/project-specialization`, **sin push ni merge**. Ocho commits: ciclo PM ·
diseño + `ADR-014` · plan + `ADR-015` · cifras re-medidas · `GOT-009` + análisis de `brief-budget` ·
análisis de `plugin-refactor` con línea base. **El diff de F1 (código + docs) está SIN comitear** en el
árbol de trabajo: se comitea por tarea (`T-01`/`T-02`/`T-03`) al cerrar la revisión.

### 1 · `docs/roadmap/2026-09-09-project-specialization/` — el tercer bucle (EN EJECUCIÓN, F1)

| Artefacto | Estado |
|---|---|
| `spec.md` **aprobada** · `evaluation.md` **completado** (56,4 h · 2.837 €) · `design.md` **aprobado** (`O1`, `ADR-014`) · `improvement-plan.md` + `tasks.md` **en-progreso** | 3 fases, 22 tareas; solo **F1 (T-01…T-03)** tiene puerta abierta («go por tramos») |
| Revisión de dos lentes | intento 1: 6 Important + 6 Minor · intento 2: 1 Critical + 4 Important + 3 Minor · intento 3: todo cerrado salvo **B-3** (tope de la persona), que no convergía porque su causa no está en F1 |
| Decisión del usuario tras el 3.er intento | **opción A** (suelo `PERSONA_SUELO_CHARS = 1300` + aviso en runtime con causa por sección) — implementada y verificada: 0 personas en muñón, 12/22 briefs sobre el tope **con aviso** |
| En vuelo al escribir esto | Lente B acotada al diff de A · después: `qa` → commits por tarea → decisión de merge (preguntar, no mergear por defecto) |

Verificado y contrario a supuestos previos: `export-interop.py --root` = raíz del PLUGIN (falla contra un
`.claude/` de consumidor) → `C-11` es un modo `--project` (`ADR-015`). El único test rojo
(`test_ca08…memory_retrieval`) **falla igual en `HEAD` limpio** en esta máquina (`GOT-008`, ruta OneDrive).

### 2 · `docs/roadmap/2026-09-09-brief-budget/` — el presupuesto del brief está roto (PM EN CURSO)

Solo una de las siete secciones del brief tiene tope; `## Diseño` entra entero en las 22 tareas (3.510, el
35 % de `BRIEF_TOPE_CHARS = 10000`), los gaps (4.396 en T-01) y la verificación (2.285) no tienen tope.
`project-specialization` es la ÚNICA iniciativa con `design.md`, y el test del CA-08 recorre solo
`memory-retrieval`, sin diseño: nunca lo vio. Documentado en **`GOT-009`** (`propuesta`). `analysis.md`
con 5 opciones; **`evaluator` en vuelo** (spec + evaluación). Después: puerta go/no-go.

### 3 · `docs/roadmap/2026-09-09-plugin-refactor/` — refactor de TODO el plugin (ANÁLISIS HECHO)

Petición del usuario. Línea base `code-health` en la carpeta (`code-health-baseline.json`): 36 ficheros ·
14.259 líneas · 7,6 % duplicado · **105 funciones > 30 líneas** · 8 TODO (6 falsos positivos del detector).
Hallazgo que ordena todo: la duplicación grande es **deliberada** (scripts standalone que viajan sueltos,
copias byte a byte guardadas por `test_knowledge_index`) o **generada** (`interop/`); la deuda real son
las funciones largas en hotspots (`task-brief.py` `main()` 155 líneas, `knowledge-find`, `doctor`,
`lint_plugin`). **Decisión previa para `architect`**: copias declaradas vs módulo vendorizado (el import
común se descarta: rompe el standalone y el requisito multi-runtime). Pendiente: `/pm-cycle`.

### Orden recomendado (decisión del usuario pendiente)

cerrar F1 → **refactor** (partir `main()` de `task-brief.py`) → **brief-budget** (presupuesto por secciones
sobre código limpio; al revés se refactoriza dos veces) → F2 de `project-specialization`.

### Lo aprendido hoy que aún no es doctrina (candidatas a lección, anotadas en el ledger de 1)

- `review-lens-select.py` no ve materia de seguridad en abrir un canal de texto controlado por el
  consumidor hacia el prompt de un subagente (`lente_c: false` en los tres intentos; la Lente B encontró la
  suplantación las tres veces).
- Cambiar una pieza no propaga a quien la documenta y el ciclo no lo comprueba (pasó dos veces DENTRO de
  la misma iniciativa: gaps 4, 13 y 14).
- `GOT-007` apareció **tres veces** en un día (dos del orquestador, una del implementer): toda cifra o
  evidencia se re-verifica tras el ÚLTIMO cambio, después del `git add`.
- Ruido del árbol: `.claude/.confluence-pending`, `.claude/.gitignore`, `.claude/.headroom_wrap_marker.json`,
  `CONTINUE-HERE.local.md`, `feature-pendiente.bundle` ensucian `scope-check` en CADA ciclo — borrar o ignorar,
  decisión del usuario.


## Sin trabajo en curso — lo ya cerrado

**v1.19.0 publicada** (2026-09-08, `8e9dec7`): interoperabilidad con Codex y OpenCode
+ instalador `npx` multi-proveedor, integrada con merge (`2095111`) y con la CI
arreglada en `ac1d1ef`. Las dos decisiones que este fichero dejaba abiertas el
2026-09-08 **están resueltas**: el tag `v1.18.1` existe, y el trabajo de interop ya
está comiteado y released (este fichero decía «sin commit ni rama»: era lo desfasado).

Antes de eso: `docs/roadmap/2026-09-04-sin-motor-externo/` (retira
"superpowers"/"Modo A") y `docs/roadmap/2026-09-04-memory-retrieval/` (memoria técnica
en tres capas — `ADR-013` —, captura episódica del turno con `<private>`, doctrina del
plugin que viaja con `--doctrina`, y la retro como puerta de cierre con
`retro-gate.py`).

## Dos decisiones abiertas (no bloquean nada)

1. **¿Publicar en npm?** El paquete es `@daycry/custom-agents`. **No verificado en la
   sesión del 2026-09-09** (hace falta red): si sigue sin publicar, exige
   `npm publish --access public` con la cuenta de daycry.
2. **¿Ampliar `GOT-007`?** Su lección era «corre la suite después de `git add`», pero
   el patrón real que dejó la CI roja es más amplio: **toda cifra medida y todo test
   nuevo hay que re-verificarlos después del ÚLTIMO cambio**.

## Entorno de esta máquina (Windows) — sigue aplicando

- El `python3` del PATH es el alias de la Microsoft Store: sin un intérprete real
  los hooks callan. Hay un venv en `.venv/` (ignorado por git) creado con
  `python -m venv .venv` + `cp .venv/Scripts/python.exe .venv/Scripts/python3.exe`
  + `pip install pytest`. **Antes de cualquier puerta:**
  `export PATH="$PWD/.venv/Scripts:$PATH"`.
- La suite completa deja ~36 fallos en Windows que **no** son defectos: `\` vs `/`
  en asserts de `relpath`, bit `+x` POSIX, `os.symlink` sin privilegio en el
  helper `sin_python3`, rutas con espacios en `coverage-gate`, `WinError 5` en
  evals, CRLF byte a byte en `test_knowledge_find --show`, los 6
  `test_progress_line_*`, `mark_docs_pending`/`ledger_lint_warn` y 3 de
  `test_release`. CI (Linux) los pasa. `release.py` **no** corre pytest, así que
  no bloquean el release; la puerta de verdad es CI.
- Checkout en CRLF (`core.autocrlf=true`, sin `.gitattributes`): toda comparación
  de bytes o conteo (CA-22 de `agents/evaluator.md`, copias de la doctrina) debe
  normalizar `\r\n` → `\n`, o comparar blobs del índice.
- El plugin que se carga en sesión es el de
  `~/.claude/plugins/cache/daycry/custom-agents/<versión>/`, **no** el árbol de
  trabajo: para probar piezas nuevas en vivo, `claude --plugin-dir "<ruta del repo>"`.
- Sin seguimiento y ajenos al repo: `.claude/.headroom_wrap_marker.json`,
  `CONTINUE-HERE.local.md`, `feature-pendiente.bundle` (bundle de entrega ya
  innecesario: todo está en `origin/master`). Ensucian `scope-check` y
  `release.py`; se pueden borrar o añadir al `.gitignore` — decisión de Jordi.

## Recordatorio permanente

El repo es **público**: nunca datos corporativos de Atlassian ni nada específico
de un cliente. Los tests de la captura episódica usan secretos **inventados**
(`ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123`, `AKIAIOSFODNN7EXAMPLE1`) para probar la
redacción; no son reales.
