# CONTINUE-HERE.md

Estado de trabajo en curso para retomar sin perder contexto (tras compactación o
un corte de sesión). Si estás leyendo esto al empezar una sesión: lee este
fichero ANTES de tocar nada. Bórralo (o vacíalo a "sin trabajo pendiente")
cuando la rama descrita aquí se publique y no quede nada abierto.

Última actualización: 2026-09-08.

## Trabajo EN CURSO — interoperabilidad con Codex y OpenCode (sin comitear)

Todo en el árbol de trabajo de `master`, **sin commit ni rama**: 16 ficheros nuevos
y 72 modificados. Puertas en verde (medido, 2026-09-08):

| Puerta | Resultado |
|---|---|
| `python scripts/lint_plugin.py` | ✅ `9 agentes · 0 errores · 3 avisos` (los 3 de siempre) |
| `python evals/check.py` | ✅ `38 ficheros · 135 casos · 0 errores` |
| `python scripts/export-interop.py --check` | ✅ `48 ficheros al día` |
| `python tests/test_export_interop.py` | ✅ `17 casos · 0 fallos` |
| `node --test "tests/*.test.mjs"` | ✅ `27/27` (instalador + adaptador de hooks) |
| `python scripts/release.py --check` | ✅ 5 manifiestos coherentes en 1.18.1 |
| Suite completa (pytest) | 37 fallos, **todos preexistentes de Windows** — el baseline de `HEAD` limpio da 49; el único «nuevo» (`test_doctor::…memoria_ya_no_pasa_en_silencio`) lo provoca el journal SIN SEGUIMIENTO `docs/knowledge/journal/2026-09-08-sesion.md`, que ya estaba antes (verificado apartándolo: pasa) |

**Además (2026-09-08, mismo árbol):** todo el frontmatter `.md` del repo es ya YAML válido
(187/187; había 64 ficheros que GitHub pintaba como «Error in user YAML»), con `lint_frontmatter_yaml`
en el linter como puerta (cruzado con PyYAML: mismo veredicto en los 187) y el arreglo de
`parse_frontmatter`, que no plegaba los bloques `>` y dejaba ciegos sus propios chequeos de
`description`. Detalle en los dos CHANGELOG.

**Qué se hizo:** `scripts/export-interop.py` traduce las piezas reales a los formatos de
Codex (plugin nativo + agentes `.toml` + prompts) y OpenCode (agentes/comandos +
adaptador de hooks en JS), `install/` es el instalador `npx` multi-proveedor, y
`docs/INTEROP.md` (+ espejo EN) documenta la **tabla de degradación**. El `find` de la
regla 5 pasó a **seis raíces** (88 ocurrencias en 56 ficheros).

**Qué falta (decisión de Jordi, no técnica):**

1. **Revisar y comitear.** Nada está comiteado. Sugerencia: revisión de dos lentes
   sobre el diff antes de integrar (es un cambio ancho: toca 56 piezas por el `find`).
2. **¿Publicar en npm?** El paquete es `@daycry/custom-agents` (719 kB, 260 ficheros,
   verificado con `npm pack` e instalado desde el tarball). Publicar exige `npm publish
   --access public` con la cuenta de daycry; **no se ha hecho**.
3. **Dos huecos documentados a propósito** (no son deuda oculta, están en la tabla):
   el guardrail por agente del `implementer` no se puede imponer fuera de Claude Code
   (el agente lo auto-comprueba) y los avisos de progreso no llegan a Codex (solo
   dispara Pre/PostToolUse para `Bash`).

## Sin trabajo en curso

**v1.18.0 publicada** (2026-09-08) y `master` con CI verde en `50932b4`. La rama
`feature/pendiente` se integró con merge (`--no-ff`) y se borró; no queda ningún
worktree ni rama abierta. Contenido de la release, ya cerrado del todo:

- `docs/roadmap/2026-09-04-sin-motor-externo/` — retira "superpowers"/"Modo A".
- `docs/roadmap/2026-09-04-memory-retrieval/` — memoria técnica recuperable en
  tres capas (`ADR-013`), captura episódica del turno con `<private>`, doctrina
  del plugin que viaja (`--doctrina`) y la **retro como puerta de cierre**
  (`retro-gate.py`, `/dev-cycle` pasos 6→9). 21 tareas, tres revisiones de dos
  lentes (38 gaps, todos corregidos), retro escrita y fila en `CALIBRATION.md`.

## Dos decisiones abiertas (de Jordi, no bloquean nada)

1. **¿`v1.18.1`?** El tag `v1.18.0` apunta a un commit cuya CI estaba **roja**:
   se arregló en los dos commits siguientes (`d2f93ef`, `50932b4`) y hoy master
   está verde, pero el árbol del tag no lo está. Si se quiere un tag sobre árbol
   verde: `python3 scripts/release.py 1.18.1` (no mover un tag publicado).
2. **¿Ampliar `GOT-007`?** Su lección era «corre la suite después de `git add`»,
   pero el patrón real que dejó la CI roja es más amplio: **toda cifra medida y
   todo test nuevo hay que re-verificarlos después del ÚLTIMO cambio**. Ese día
   se encadenaron tres fallos por lo mismo: recortar el campo `Changelog:` que
   ERA el bullet más largo sin re-medir (539 → 467, 11 marcas desfasadas), un
   comparador byte a byte del árbol de trabajo con `core.autocrlf=true` (decía
   «difiere» con los blobs del índice idénticos) y un `subprocess` sin
   `encoding=` en el propio arreglo (lo cazó `GOT-005`).

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
