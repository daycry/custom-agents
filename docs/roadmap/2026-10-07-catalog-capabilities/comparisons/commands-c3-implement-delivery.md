# Ejecución de planes PRP, commit y pull request — C063, C067, C068, C070

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cuatro definiciones completas: **21.579 bytes/865 líneas**. [commands-c3-implement-delivery-reading-evidence.json](commands-c3-implement-delivery-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08/T-11.

## Decisión común

Las cuatro cubren el tramo implementar → commit → PR, que en el plugin es de
`implementer` (P3-P5) y del ritual de cierre de `/dev-cycle` Fase 6
(`commands/dev-cycle.md:491-503`). La selección de ficheros para el commit ya está
integrada (`agent-kits/shared/commit-selection.py`, `docs/COMMIT-SELECTION.md`). Del PR
falta lo que la fila «Entrega y onboarding» de
[commands-workflow-comparison.md](commands-workflow-comparison.md) dejó pendiente
(«plantilla real, base/head exactos»); C063 lo concreta.

Defecto común a C063 y C070, el más grave del bloque: ante un push rechazado por
divergencia hacen `git fetch`, `git rebase origin/<base>` y `git push -u origin HEAD`
(l.91-96). Rebasar sobre la base no trae los commits que otro dejó en la rama remota,
así que el push vuelve a fallar, y el caso límite (l.182) manda a
`--force-with-lease`, que los sobrescribe. En el plugin cualquier push forzado sobre
una rama empujada lo bloquea el guardarraíl del implementer (`agents/implementer.md:102`).

## C068 — prp-implement

`8.949 bytes/385 líneas` · frontmatter: `description` y `argument-hint`. Ejecuta un
plan PRP tarea a tarea con comprobación de tipos tras cada fichero, cinco niveles de
validación (estática, unitarias, build, integración contra el servidor local, casos
límite), informe en `.claude/PRPs/reports/`, actualización de la fase del PRD y
archivo del plan en `completed/`.

- **Artefactos y dueño propio:** código → `implementer`; progreso y desviaciones →
  `tasks.md` (`implementer`); estimado frente a real → `/retro` (`retro.md` y
  `CALIBRATION.md`, `commands/retro.md:17-34`); estado de la fase → transiciones de `/dev-cycle`.
- **Despacho:** ninguno; scripts del gestor de paquetes detectado y `curl` a localhost.
- **Escenario positivo:** «implementa el plan aprobado» → `implementer` (vía `/dev-cycle` Fase 3).
- **Escenario negativo:** «abre el PR» → no es `implementer`: Fase 6 de `/dev-cycle` (C063).

**Comparación.** La `Verificación` por tarea y la verificación de fase (P5) cubren
los niveles 1-3; la integración es de `qa` contra hosts locales. «Anota qué cambió y
por qué» (l.120-126) es la nota de alcance del implementer (`agents/implementer.md:97`)
y la replanificación con motivo de `planner` (D-096). Defectos:

| Defecto | Cita |
|---|---|
| `git pull --rebase origin <rama> 2>/dev/null \|\| true` | l.92: rebasa una rama que puede estar compartida y oculta el fallo; en el plugin `rebase` solo en rama propia no empujada (`agents/implementer.md:102`) |
| Mueve el plan a `completed/` con `mv` | l.283-284: rompe los enlaces desde el PRD y el informe; en el plugin la carpeta queda y cambia el estado (regla 7) |
| «Every function needs at least one test» | l.157: regla universal; aquí la cobertura es opt-in (`tests.coberturaMinima`) |

**Destino:** **Sin destino**: ya integrado en `implementer`, `qa` y `/retro`.

## C067 — prp-commit

`3.057 bytes/112 líneas` · frontmatter: `description` y `argument-hint`. Commit de una
línea con selección de ficheros en lenguaje natural («los cambios de auth», «menos los
tests», «solo los nuevos») y mensaje `tipo: descripción`.

- **Artefactos y dueño propio:** commit → `/dev-cycle` Fase 6 paso 2 (un commit por tarea, `T-XX:`) e `implementer` P4.
- **Despacho:** `git`.
- **Escenario positivo:** «haz el commit de la tarea T-03» → Fase 6 paso 2 con `commit-selection.py preview` y `validate` (`commands/dev-cycle.md:494`).
- **Escenario negativo:** «haz commit de todo» → ninguna pieza propia hace `git add -A`; se pide la lista explícita.

**Comparación.** Mostrar qué ficheros se eligen y por qué (l.40) es lo que hace la
vista previa propia, que además conserva el staging ajeno con `commit --only`.
Defectos: sin argumento hace `git add -A` (l.32), contra `agents/implementer.md:101`;
«except tests» (l.35) hace `git add -A && git reset -- …`, que también quita del índice
los tests que el usuario ya tenía preparados, y silencia errores con `|| true`; «staged»
(l.33) comitea cualquier staging previo sin revisarlo. **Destino:** **Sin destino**: ya
integrado en `commands/dev-cycle.md:494`.

## C063 — pr

`4.826 bytes/184 líneas` · frontmatter: `description` y `argument-hint`. Valida la rama
(no es la base, hay commits por delante, no existe ya un PR), busca la plantilla de PR
del repo, analiza commits y ficheros, enlaza PRD y planes, empuja, crea el PR con `gh`
y lee sus checks.

- **Artefactos y dueño propio:** rama remota y PR → `/dev-cycle` Fase 6 pasos 3-4
  (resumen derivado del ledger e integración según el flujo del repo, preguntando).
- **Despacho:** `git` y `gh`.
- **Escenario positivo:** «abre el PR de esta iniciativa» → Fase 6 pasos 3-4 de `/dev-cycle`.
- **Escenario negativo:** «mergéalo» → ninguna pieza mergea por defecto (`commands/dev-cycle.md:496`).

**Comparación.** El resumen propio sale del ledger (tareas, criterios, veredicto de
`qa-gate`, evidencias), más fiable que agrupar mensajes de commit. Le faltan tres
comprobaciones de la fuente: usar la plantilla de PR del repo conservando sus secciones
(l.42-49, l.106), fijar la base en vez de suponer `main` (l.13, que en este mismo
repo es `master`) y no crear un segundo PR si la rama ya tiene uno (l.32). Además del
defecto común, solo **avisa** con cambios sin comitear (l.30).

**Destino:** línea en `commands/dev-cycle.md:495` (Fase 6 paso 3): «Si el repo trae
plantilla de PR (`.github/PULL_REQUEST_TEMPLATE.md`, `.github/pull_request_template.md`,
`.github/PULL_REQUEST_TEMPLATE/` o `docs/pull_request_template.md`), rellena SUS
secciones con este resumen (N/A en las que no apliquen, sin borrarlas). Antes de crear
el PR fija base y head explícitos (la base no se supone) y comprueba que la rama no
tiene ya uno abierto.»

## C070 — prp-pr

`4.747 bytes/184 líneas` · frontmatter: `description` y `argument-hint`. Alias de C063
copiado: cambian la descripción, la línea de atribución, el aviso de cambios sin
comitear (sugiere `/prp-commit`) y la lista de artefactos, que solo mira `.claude/PRPs/`.

- **Artefactos, dueño, despacho y escenario positivo:** los de C063.
- **Escenario negativo:** PR de una iniciativa planificada con `/plan` → este alias no
  enlaza `.claude/prds/` ni `.claude/plans/` (l.76-79): la copia ya divergió del original.

**Comparación.** Un alias por copia duplica el disparador y deriva con el tiempo;
en el plugin cada intención tiene un dueño (ADR-011). **Destino:** **Sin destino**
(la línea de C063 cubre ambos).
