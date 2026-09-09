# CONTINUE-HERE.md

Estado de trabajo en curso para retomar sin perder contexto (tras compactación o
un corte de sesión). Si estás leyendo esto al empezar una sesión: lee este
fichero ANTES de tocar nada. Bórralo (o vacíalo a "sin trabajo pendiente")
cuando la rama descrita aquí se publique y no quede nada abierto.

Última actualización: 2026-09-09.

## Trabajo EN CURSO — iniciativa `project-specialization` (ciclo PM cerrado, sin comitear)

`docs/roadmap/2026-09-09-project-specialization/` — «el tercer bucle»: la capa de
especialización por proyecto (personas, skills y tools **de proyecto** derivadas de la
memoria del propio proyecto, comando `/specialize`, registro `.claude/pieces.json`
auditado por `/doctor`). El ciclo PM está **cerrado**.

| Artefacto | Estado |
|---|---|
| `analysis.md` | tres bucles · siete estadios · invariante de dirección · escalera de decisión · anti-alcance razonado |
| `spec.md` | **aprobada** — 9 características (C-01…C-07, C-10, C-11), 35 criterios de aceptación |
| `evaluation.md` | **completado** — 56,4 h · 2.837 € · 1,90 M tokens · veredicto «go por tramos» |

Puertas en verde (medido 2026-09-09, con `export PATH="$PWD/.venv/Scripts:$PATH"`):
`lint_plugin.py` ✅ 0 errores (los 3 avisos de siempre) · `pytest
tests/test_roadmap_index.py tests/test_dashboard.py tests/test_cifras_medidas.py`
✅ `286 passed`.

**Qué falta:**

1. **Diseño con `architect`** — el esquema de `pieces.json` (tres estados por hash,
   rutas por runtime, modo de adopción) es difícil de revertir en cuanto haya
   proyectos con registro escrito, y `C-05` está en complejidad **Muy alta**.
2. **`/dev-cycle`** sobre la carpeta → `planner`. Orden que fija la evaluación:
   `C-01 → C-02 ‖ C-10 → C-03 → C-04 → C-05 → C-07 → C-06 → C-11`.
3. **Las cuatro condiciones de F2**: `C-10` antes de `C-05` y `C-06` · `C-04` y `C-07`
   entran con `C-05` · las líneas de proceso (doc, evals, interop, changelog, retro)
   no se recortan · decidir el **modo proyecto** de `export-interop.py` antes de
   abrir `C-11`.

**Dos cosas verificadas que contradicen supuestos previos** (mandan estas):

- `export-interop.py --root` significa «la raíz del **plugin**», no «cualquier árbol».
  Contra un `.claude/` de consumidor falla pidiendo `.claude-plugin/plugin.json`, y
  escribe en `interop/` + `.codex-plugin/`, no en `.codex/`/`.opencode/`. Por eso
  `C-11` es un **modo proyecto** del traductor, no una fila de documentación.
- El requisito es **multi-runtime desde el diseño** (Codex, OpenCode y próximas
  integraciones), no solo Claude Code. Regla: **la pieza no sabe de runtimes** —
  escribe canónico y delega la traducción. Añadir un runtime = una fila en la tabla
  `PROVIDERS` de `install/providers.mjs` más su traductor, nunca un cambio en la pieza.
  Portabilidad por forma: persona y tool son neutrales (las inyecta Python nuestro por
  Bash), la skill viaja sin traducir pero con `description` ≤ 1.024 caracteres, y el
  agente exige traducción real.

**Diferido a propósito, no es deuda oculta:** `C-08` (deriva semántica) y `C-09` (campo
«Cuándo aplica» en la plantilla de `knowledge-write.md`), porque sin `C-08` ningún
código leería ese campo — y un campo que nadie consume es la pieza muerta que esta
iniciativa nació para evitar.

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
