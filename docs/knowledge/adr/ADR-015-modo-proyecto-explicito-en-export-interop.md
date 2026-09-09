---
id: ADR-015
titulo: El modo proyecto de `export-interop.py` se activa con un flag explícito `--project`, nunca por inferencia de la ausencia de `.claude-plugin/`
estado: propuesta
fecha: 2026-09-09
iniciativa: project-specialization
---

# ADR-015: El modo proyecto de `export-interop.py` se pide, no se adivina

## Contexto

`C-11` de la iniciativa `project-specialization` traduce las **piezas de proyecto** (las que `/specialize` escribe en el `.claude/` del consumidor) a Codex y OpenCode, delegando en `scripts/export-interop.py` — el mismo mecanismo con el que el plugin se traduce a sí mismo. La spec daba por verificado que `--root` ya aceptaba «cualquier árbol con forma de plugin», y no es cierto: `--root` significa **la raíz del PLUGIN**. Contra un `.claude/` de consumidor sale con **exit 1** pidiendo `.claude-plugin/plugin.json`, y su plan de salida escribe en `interop/` y `.codex-plugin/`, no en `.codex/` y `.opencode/`. La evaluación lo midió y lo corrigió (§Ambigüedad 2), y dejó la forma de aprender el modo como **incógnita explícita del `planner`** y como **condición (d) del go de F2**: «no se abre `C-11` sin decidir cómo aprende `export-interop.py` el modo proyecto». Las dos candidatas eran un flag nuevo o inferirlo de la ausencia del manifiesto del plugin; la evaluación anotó que «inferirlo es más elegante y más frágil», y que ninguna de las dos cambia las 4,5 h.

## Decisión

El modo proyecto de `scripts/export-interop.py` se activa con un **flag explícito `--project`**. Sin ese flag, el comportamiento actual no cambia: `--root` sobre un árbol sin `.claude-plugin/plugin.json` sigue saliendo con **exit 1**. Con el flag, el plan de salida pasa a `.codex/…` + `.opencode/…` dentro del árbol del proyecto (cero escrituras en `interop/` o `.codex-plugin/`) y los manifiestos y hooks ausentes se toleran con aviso. `--check --project` compara contra el plan de salida del modo proyecto.

## Alternativas descartadas

- **Inferir el modo de la ausencia de `.claude-plugin/`** — convierte un **error en un cambio de modo silencioso**: una ruta mal escrita o un plugin a medio instalar dejarían de fallar y empezarían a **escribir en otro sitio**. Es la clase de fallo de `GOT-003` (un generador que escribe dentro del árbol que él mismo espeja), y aquí sin la red del registro, porque quien escribe las variantes es `export-interop.py`, que no consulta `dueno()`. Además elimina el caso de test que impide la regresión: con inferencia, «`--root` sin flag sobre árbol de proyecto → exit 1» desaparece y con él la garantía. Y deja `--check` ambiguo: su veredicto pasaría a depender de lo que haya en el disco en vez de lo que se le ha pedido, siendo puerta de CI y de `release.py`.
- **Un traductor aparte para piezas de proyecto** — dos implementaciones de la misma traducción divergiendo (`LES-013`), y rompería el invariante de que las variantes son **generadas y nunca editadas a mano** por un solo mecanismo.
- **Que `/specialize` traduzca él mismo** — rompe el invariante explícito de la spec: `/specialize` **no sabe de runtimes**. Un runtime nuevo sería un cambio en el comando en vez de una fila en la tabla `PROVIDERS` de `install/providers.mjs` (con `IDS` ya exportado) más su traductor.

## Consecuencias

`/specialize` sigue sin saber de runtimes y añadir un cuarto proveedor sigue sin tocar ni el comando ni el esquema del registro (`runtime` es un dato, `ADR-014`). Se gana un test de no-regresión —el exit 1 sin flag— que la inferencia habría hecho imposible, y `--check` mantiene dos veredictos explícitos en vez de uno dependiente del disco. Se renuncia a la ergonomía de no escribir el flag: quien traduzca las piezas de un proyecto tiene que pedirlo, y `/specialize` lo **ofrece** con el comando completo tras generar (nunca automáticamente). Queda condicionado el alcance de `C-11`: el modo proyecto es trabajo de `export-interop.py` (~2,0 h de sus 4,5 h), no una fila de documentación, tal como la evaluación ya presupuestó.

## Estado

`propuesta` — decidida por el `planner` en la puerta de planificación del 2026-09-09 (condición (d) del go de F2), antes de abrir `T-17`. Pasa a `aceptada` cuando la revisión de dos lentes valide la implementación de `C-11` contra esta decisión; a `obsoleta` si una decisión posterior la reemplaza. Fuente: [`docs/roadmap/2026-09-09-project-specialization/improvement-plan.md`](../../roadmap/2026-09-09-project-specialization/improvement-plan.md) §Cambios arquitectónicos, decisión 4, y [`evaluation.md`](../../roadmap/2026-09-09-project-specialization/evaluation.md) §Ambigüedad 2 y §Recomendación, condición (d).
