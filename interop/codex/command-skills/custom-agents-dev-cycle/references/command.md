<!-- GENERADO por scripts/export-interop.py desde commands/dev-cycle.md — no lo edites a mano.
     Regenera con `python3 scripts/export-interop.py`; el porqué está en `docs/INTEROP.md`. -->

> **Adaptación a Codex** (fichero generado; la fuente es `commands/dev-cycle.md`).
> Este comando ORQUESTA agentes. En Codex no hay herramienta Agent: usa `spawn_agent` con `agent_type` igual al ID nativo del rol, si está disponible; las definiciones se copian a `.codex/agents/`.
> En el cuerpo, los roles propios se resuelven con este mapa: analyst → `custom-agents-analyst`; architect → `custom-agents-architect`; documenter → `custom-agents-documenter`; evaluator → `custom-agents-evaluator`; implementer → `custom-agents-implementer`; knowledge-curator → `custom-agents-knowledge-curator`; nemesis → `custom-agents-nemesis`; planner → `custom-agents-planner`; qa → `custom-agents-qa`; reviewer → `custom-agents-reviewer`. Conserva nombres y rutas de agentes del consumidor.
> Las skills se invocan mencionándolas con `$custom-agents:nombre` para las skills de este plugin; conserva el nombre nativo de las skills del consumidor. Todo lo demás (puertas, artefactos, ledger) no cambia.


# /dev-cycle — orquestador del ciclo de desarrollo

Ejecuta el ciclo de una iniciativa de forma explícita y fiable. Objetivo: **$ARGUMENTS**.

Mantén `docs/roadmap/<fecha>-<slug>/tasks.md` como **ledger canónico** de progreso en todo el
ciclo (ver regla 8 de `docs/CONVENTIONS.md`). Al escribirlo, lee
`agent-kits/shared/ledger-write.md`: writer preferente y obligatorio en lite;
conserva el fallback ordinario y las puertas del ciclo.

## Detalle por fase: lectura bajo demanda

Lee este núcleo completo. Las referencias privadas conservan el método de cada
fase; ábrelas **solo cuando** se cumpla la condición de la tabla. No cargues el kit
entero ni las fases que esta ejecución omite. Una referencia necesaria ilegible
se informa; no se improvisan puertas ni se sustituye por otra instalación.

Resuelve `DEVKIT` (Bash) o `$DevCycleKit` (PowerShell) en el **mismo bundle que el
núcleo**. Si ya conoces su origen, usa esa ruta observada. Sin ella, busca proyecto
antes que usuario en las seis raíces de la regla 5; el propio repo es el fallback
explícito de desarrollo. Contrasta la procedencia con el núcleo antes de leer.
No supongas que las variables sobreviven entre bloques de shell: conserva la
ruta observada y asígnala de nuevo en cada bloque que la necesite.

```bash
if [ -f "$PWD/agent-kits/dev-cycle/references/phase2-planning.md" ]; then
  DEVKIT="$PWD/agent-kits/dev-cycle"
else
  DEVKIT="$(find "$PWD/.claude" "$PWD/.codex" "$PWD/.opencode" "$HOME/.claude" "$HOME/.codex" "$HOME/.config/opencode" -type d -path '*agent-kits/dev-cycle' 2>/dev/null | head -1)"
fi
```

```powershell
$DevCycleKit = Join-Path (Get-Location) 'agent-kits/dev-cycle'
if (!(Test-Path -LiteralPath "$DevCycleKit/references/phase2-planning.md" -PathType Leaf)) {
  $DevCycleKit = $null
  foreach ($DevCycleRoot in @("$PWD/.claude", "$PWD/.codex", "$PWD/.opencode", "$HOME/.claude", "$HOME/.codex", "$HOME/.config/opencode")) {
    if (Test-Path -LiteralPath $DevCycleRoot -PathType Container) {
      $DevCycleOwner = Get-ChildItem -LiteralPath $DevCycleRoot -Filter phase2-planning.md -File -Recurse -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName.Replace('\', '/').EndsWith('/agent-kits/dev-cycle/references/phase2-planning.md') } | Select-Object -First 1
      if ($DevCycleOwner) { $DevCycleKit = $DevCycleOwner.Directory.Parent.FullName; break }
    }
  }
}
```

| Referencia en `agent-kits/dev-cycle/references/` | Cuándo leerla |
|---|---|
| `phase1-evaluation.md` | Fase 1 del flujo completo |
| `phase2-planning.md` | Fase 2 o revisión solicitada del plan; nunca por defecto en vía rápida |
| `phase3-subagents.md` | Fase 3 con `subagentes: true` |
| `phase3-jira.md` | Fase 3 con Jira habilitado para este proyecto |
| `phase4-knowledge-gate.md` | Gate tras QA/documentación, si hay candidatos o handoffs pendientes |

En referencias exportadas, estas rutas pertenecen al bundle canónico; no son
relativas a la carpeta `references/` del adaptador de Codex/OpenCode.

## Contexto técnico compartido

Antes de despachar roles, aplica `agent-kits/shared/capability-check.md` sobre
el paquete y áreas del objetivo. Comparte selección/procedencia con los roles;
planner registra los IDs y escenarios por tarea. Implementer, reviewer y qa
usan los mismos criterios técnicos. Repite selección solo ante hechos nuevos.
Sin selector, avisa y sigue con guías disponibles; conserva las puertas del ciclo.
Este paso no inicia servicios ni genera piezas de proyecto.

## Fase 0 — Preparación
1. Deriva un `<slug>` corto en kebab-case del objetivo y fija/crea la carpeta `docs/roadmap/<fecha>-<slug>/` (reutilízala si ya existe).
2. Ofrece añadir al `CLAUDE.md` del proyecto (si no está) la **regla de ledger canónico**: "El progreso de un plan se registra en `docs/roadmap/<…>/tasks.md`; cualquier implementador debe marcar ahí cada tarea; los ledgers propios son espejo, no fuente."
3. Conserva el encargo antes de despachar: resultado que busca el usuario, requisitos explícitos y su fuente (mensaje o sección concreta del documento), restricciones y cuestiones abiertas. Distingue los hechos de las hipótesis; no conviertas una recomendación o un patrón encontrado en requisito. Reutiliza lo ya aportado y pregunta sólo por información que impida decidir el siguiente paso.
4. Para cada cambio, identifica el comportamiento observable que probaría el resultado y los patrones pertinentes ya usados en el proyecto, con sus rutas. Si aún faltan, encarga su búsqueda al rol responsable y conserva ese pendiente. Clasifica cada cambio como capacidad nueva, cambio de un comportamiento que funciona, defecto o refactor, porque la clase fija su primer oráculo en la `Verificación` de la tarea: test nuevo en rojo, test existente modificado en rojo, reproducción mínima del fallo (fase 1 de `debug-root-cause`) o la misma suite en verde antes y después. Si el usuario describe un defecto como cambio (o al revés), pregúntalo antes de despachar. Este contexto acompaña al objetivo; no crea otro artefacto, aprobación ni etapa obligatoria de investigación.

## Fase 0-bis — PUERTA DE ENTRADA: flujo completo vs. vía rápida
Antes de arrancar, **pregunta al usuario** cómo quiere abordarlo (una sola pregunta, con recomendación según el tamaño aparente del cambio):

- **Flujo completo** (Fases 1→6): `evaluator` (spec + presupuesto) → `architect` (opcional: opciones de diseño) → `planner` → implementación → revisión → qa → documentación. Para trabajo no trivial, con incógnitas, multi-fichero, o cuando quieras el presupuesto en €/tokens y la traza PM completa.
- **Vía rápida** (salta el papeleo PM, conserva la red de calidad): **omite Fases 1 y 2** (sin spec, sin evaluación, sin plan detallado). El orquestador crea directamente un **`tasks.md` ligero** en `docs/roadmap/<fecha>-<slug>/` (solo ese fichero: banner de ledger canónico + frontmatter con `verificacion: obligatoria` + una fase + las tareas mínimas con criterios de aceptación verificables y su campo `- **Verificación**: \`<comando>\` → <resultado esperado>` — `ledger-lint.py` exige el campo cuando el frontmatter lo declara —, más el campo `- **Changelog**: <una frase>` que se rellena al CERRAR cada tarea: qué cambia para quien USA el proyecto, sin jerga del ledger; es lo que `changelog-sync` copia tal cual a las notas de la Fase 6), va directo a **`implementer`**, y **mantiene las puertas de calidad**: la **revisión adversarial de dos lentes** (Fase 3) y **`qa`** con `qa-gate`. Cierra con `documenter` solo si el usuario lo pide. Para cambios pequeños/claros que se describen en una o dos frases. **Por qué la vía rápida NO salta la calidad.** El papeleo de PM (spec/evaluación/plan) es lo caro y prescindible en un cambio pequeño; la revisión de dos lentes y `qa-gate` son baratas y son la red que evita meter un bug "por ir rápido". Por eso la vía rápida ahorra ceremonia, no seguridad. El `tasks.md` ligero conserva el **ledger canónico**, así que el progreso, la imputación de horas y el volcado a Jira siguen funcionando igual. Si el usuario pide algo **trivial de verdad** (un typo, una línea), puede pedir explícitamente saltarse también la revisión/qa — pero no es el defecto.

**Si el usuario ya indica el modo, NO preguntes.** Respeta lo que pidió y arranca directo en ese modo:
- **Vía rápida explícita:** el objetivo trae "vía rápida", "rápido", "directo", "sin papeleo", "solo impleméntalo", o el argumento `rapido`/`--rapido`/`--quick`.
- **Flujo completo explícito:** "flujo completo", "con evaluación/presupuesto", "hazlo formal", o `--completo`/`--full`.

**Recomendación por defecto (solo si el usuario NO indicó modo):** si el objetivo se describe en una frase y toca pocos ficheros, propón **vía rápida**; si hay incógnitas, varias fases o el usuario quiere presupuesto, propón **flujo completo**. El usuario decide; respeta su elección.

> **Medición del coste (vía rápida).** El `tasks.md` ligero también se mide: al crearlo, `usage-meter.py start --artefacto "docs/roadmap/<fecha>-<slug>/tasks.md"` y, al dejarlo escrito, `close` → vuelca el JSON a su bloque `generacion:` (script en `agent-kits/shared/`; si degrada a `fuente: estimado`, anótalo y sigue — nunca bloquea).
>
> **Regla de no-solape (todo el ciclo).** Cada agente/fase mide su propio artefacto o tarea; como orquestador, asegúrate de que cada marcador se **cierra antes de abrir el siguiente** (evaluator cierra la evaluación antes de que planner abra el plan; una tarea cierra antes de lanzar la revisión): ventanas solapadas cuentan los mismos tokens dos veces y reparten mal el coste.

Si es **vía rápida**, salta a la Fase 3 (implementación) usando el `tasks.md` ligero; si es **flujo completo**, sigue en la Fase 1.

**Continuidad del encargo en ambas vías.** Al crear el ledger ligero o despachar
`planner`, pasa el encargo de la Fase 0 y pide que cada tarea conserve la relación
entre requisito y fuente, cambio esperado y primera comprobación observable.
Usa los campos existentes: `Descripción` para el resultado y requisito,
`Notas` para procedencia, patrones con rutas e hipótesis pendientes, criterios
de aceptación para el comportamiento y `Verificación` para su comprobación.
`task-brief.py` transfiere esos campos al implementer; no dependas de que recuerde
la conversación. Conserva los requisitos aprobados al retomar una iniciativa;
una contradicción nueva se comunica y resuelve antes del trabajo afectado.

> **Modelo del agente (tiering configurable, capa 2).** Antes de despachar CUALQUIER agente por nombre (`evaluator`, `architect`, `planner`, `implementer`, `qa`, `documenter`, `nemesis`), resuelve su tier efectivo y pasa `model` en el parámetro `model` del Agent tool (contrato oficial sub-agents.md, verificado 2026-09-03: el parámetro por invocación tiene prioridad sobre el frontmatter):
>
> ```bash
> SHAREDKIT="$(find "$PWD/.claude" "$PWD/.codex" "$PWD/.opencode" "$HOME/.claude" "$HOME/.codex" "$HOME/.config/opencode" -type d -path '*agent-kits/shared' 2>/dev/null | head -1)"
> python3 "$SHAREDKIT/model-tier.py" <agente> --json     # {"model": "...", "effort": "...", "fuente": {"model": "frontmatter|dev.json", ...}}
> ```
>
> Si `fuente.model` es `dev.json`, pasa ese `model`; si es `frontmatter`, no pases nada (el agente ya lo declara). El `effort` de `dev.json` es **informativo**: el Agent tool no documenta ese parámetro, así que el efectivo es el del frontmatter — anúncialo («effort configurado high; efectivo: el del frontmatter») sin fingir que lo aplicas. Sin el script (instalación parcial) → frontmatter y sigue. Las lentes de la revisión resuelven su propio tier dentro de la skill `adversarial-review` (agente `reviewer`).

## Fase 1 — Evaluar (siempre en flujo completo, agente `evaluator`)

Solo en flujo completo, lee `"$DEVKIT/references/phase1-evaluation.md"` al llegar
a esta fase, antes de invocar evaluator. Conserva su puerta go/no-go.

## Fase 2 — Planificar (solo en flujo completo: `architect` opcional → `planner`)

Solo cuando corresponda planificar o atender una revisión del plan, lee
`"$DEVKIT/references/phase2-planning.md"`. Contiene diseño, plan, las recetas
Bash/PowerShell de revisión visual, consumo y feedback, y el opt-in de Jira.
Omítela en vía rápida o al retomar Fase 3 si no hay una revisión del plan que atender.
La autorización conversacional suficiente conserva su alcance y evita otro OK.

## Fase 3 — Implementar y probar

> **Disciplina de desarrollo (`.claude/dev.json`, opt-in, defaults off — la crea `/setup`).** Antes de implementar, lee la config: `tdd: true` → el implementer sigue la skill **`tdd`** (fuente única de RED-GREEN-REFACTOR) por tarea con evidencia del rojo en el ledger; `worktree: true` → la iniciativa se trabaja en un worktree de git aislado (degradación a rama normal con aviso si no hay soporte); `subagentes: true` → el despacho por subagentes de contexto fresco (ver más abajo). Sin fichero o corrupto: defaults `false` + aviso — comportamiento clásico. Las tres opciones son combinables.

1. **`implementer`** → implementa fase a fase sobre rama (o worktree, si `worktree: true`), marcando `tasks.md` por tarea (con RED-GREEN-REFACTOR si `tdd: true`).

   **Subagentes (opt-in).** Solo cuando `subagentes: true`, lee
   `"$DEVKIT/references/phase3-subagents.md"` antes de preparar el brief o despachar.
   Sin ese opt-in, sigue el flujo clásico en el contexto principal. La revisión
   independiente conserva su propio método y no depende de este interruptor.

   **Medición por tarea (usage-meter).** Al ARRANCAR cada `T-XX`: `usage-meter.py start --artefacto "<slug>/T-XX"`; al COMPLETARLA: `close` con la misma clave (en el flujo clásico lo ejecuta el `implementer` — su P3 lo trae; con `subagentes: true` lo coordinas tú por despacho). Las **horas-IA medidas** del JSON (`horas_ia`, con `fuente: medido`) se escriben como tiempo IA **real** de la tarea en `tasks.md` — anota `(medido)` junto al valor — y son las que usa la imputación a Jira (`worklog.py plan` ya prefiere real sobre estimado; su aritmética de jornada/banco NO cambia). Reglas: (a) si el meter degrada, deja la estimación a juicio marcada `(estimado)` y sigue; (b) re-medir la MISMA ventana (re-close inmediato) sustituye; pero una **corrección posterior** (gaps de revisión) se mide con clave nueva `"<slug>/T-XX-fix<N>"` y sus horas se **SUMAN** al real de la tarea en el ledger — la implementación original no se pierde; (c) los tokens del bucle de revisión (los revisores) NO van a la tarea — la revisión tiene su propia imputación `[revisión]` por intento (ver más abajo); cierra el marcador de la tarea ANTES de lanzar la revisión. Duraciones presentadas en formato `XhYm` (`usage-meter.py fmt`).
2. **Revisión adversarial — skill `adversarial-review` (fuente única del método; aquí solo se invoca).** Invócala por nombre pasándole: la carpeta de la iniciativa (`docs/roadmap/<fecha>-<slug>/`), el **nº de intento N** y, si N > 1, la **tabla de veredictos del intento anterior** (incluidos los `descartado (rebatido)` con su evidencia). La skill hace el resto: puerta previa `scope-check.py` (exit 1 → gap Important al `implementer` sin gastar revisores), `review-lens-select.py` para decidir si añade la **Lente C** (seguridad, condicional), lentes A/B(/C) en paralelo con contexto fresco, fusión, graduación `Critical / Important / Minor`, arbitraje de los rebates con evidencia, sección «Revisión de dos lentes — intento N» en `tasks.md`, evidencia para Curator al cerrar sin gaps pendientes (sin promoción ni aprobación de memoria), y el **comentario firmado en Jira de CADA intento** (`jira-flow.py --event revision|gaps --intento N`, Paso 7 de `jira-sync`: lo ejecuta la propia skill en su paso 6, no tú) si hay opt-in y plan volcado. Espera de vuelta: veredicto por criterio ✓/✗, gaps graduados con su veredicto, qué lentes corrieron y el ledger actualizado (`ledger-lint` exit 0).
   - **Tuyo (orquestador) — bucle reviewer→implementer ACOTADO (regla dura).** Si quedan gaps Critical/Important: las tareas afectadas vuelven a `en-progreso`, `implementer` corrige (ese tiempo es **implementación**, clave `"<slug>/T-XX-fix<N>"`) y **relanzas la skill** sobre el nuevo diff con contador explícito ("revisión, intento 2 de 3"). **Máximo 3 intentos**; al 3.º con gaps, PARA y pregunta (seguir / re-planificar con `planner` / aceptar como deuda). Rebatir con evidencia **no consume intento**; lo Minor se anota sin bloquear.
   - **Tuyo (orquestador) — worklog `[revisión]` POR INTENTO (si `jira.json` `enabled` y se volcó el plan):** al cerrar cada pasada, `worklog.py plan --kind revision --attempt N` — cada intento queda como su propia entrada en Jira con duración y fecha, y `reviewAttempts` guarda la traza para `/retro`. El **comentario** del intento (`revision`/`gaps`) NO es tuyo: lo publica la skill en su paso 6; si al volver de la skill no hay comentario de ese intento en el issue, es un gap de proceso de la skill, no algo que rellenes tú a mano. Los tokens de los revisores NO van a la tarea: cierra el marcador de la tarea ANTES de invocar la skill.
3. **`qa`** → pruebas E2E (solo local), informe y evidencias. El veredicto verde/rojo lo da `qa-gate.py` (exit code), no una impresión. **Antes de despacharlo, lee el frontmatter de `improvement-plan.md`:** con `test-plan: n/a (sin UI)` la iniciativa no tiene interfaz por diseño, así que invoca `qa` en **modo sin UI** (corre `ledger-lint.py` y `coverage-check.py` —que reconoce el marcador—, sin Playwright ni URL) y anota en el ledger «qa: sin UI por diseño (`test-plan: n/a (sin UI)`)». Sin marcador **y** sin `test-plan.md`, `qa` avisa UNA vez con el comando que lo fija y termina: no lo relances por eso (era la contradicción E1, `ADR-017`).

**Bucle de corrección de qa ACOTADO (regla dura).** Si qa sale rojo: la(s) tarea(s) afectadas vuelven a `implementer`, se corrigen y qa **re-ejecuta**. Contador explícito ("intento 2 de 3"). **Máximo 3 intentos**; si el 3.º sigue rojo, ANTES de parar ejecuta **UNA pasada de la skill `debug-root-cause`** (4 fases con evidencia: reproducción mínima → aislamiento → hipótesis probada → fix propuesto). Luego PARA y pregunta al usuario qué hacer — seguir con el fix propuesto, re-planificar con `planner`, o cancelar — presentando el **diagnóstico** (causa probada, o lo descartado + hipótesis vivas si no concluyó) junto a la salida de qa-gate de cada intento. El tiempo del diagnóstico se imputa como implementación de la tarea afectada. No cierres estados en rojo y no degrades el umbral para "pasar".

### Ciclo Jira de la Fase 3 (opt-in)

Solo cuando `.claude/jira.json` tiene `enabled: true`, lee
`"$DEVKIT/references/phase3-jira.md"` antes de ejecutar el primer evento y aplica
su tabla completa de dueños, firmas, confirmaciones y estados. Sin opt-in no
publiques operaciones. `adversarial-review` conserva el evento de cada intento;
el orquestador conserva `aprobado`, sólo con revisión sin gaps y QA verde.

Al salir debes tener: código implementado, revisión pasada, `qa-gate` en verde y `tasks.md` al día (validado con `ledger-lint.py`).

**Ledger grande (al cerrar cada fase).** Si `ledger-lint.py` avisa del tamaño del ledger (70 % del tope de lectura de 256 KiB) o de una `Verificación` larga, ejecuta TÚ `python3 "$SHAREDKIT/ledger-archive.py" docs/roadmap/<fecha>-<slug> --apply` (sin `--apply` enseña el plan): traslada la historia cerrada a `execution-history.md` con su SHA sin cambiar lo que deciden `jira-flow`/`task-brief`. El `implementer` no puede: su guardia solo le deja escribir `tasks.md` en `docs/roadmap/`.

## Fase 4 — Documentar (siempre, agente `documenter`)
Con las pruebas en verde, invoca **`documenter`** para generar/actualizar la documentación del proyecto (una vez al final, no por tarea).

## Fase 4-bis — Knowledge Gate (siempre, agente `knowledge-curator`)

Después de QA verde y documenter (o de QA si la vía rápida no requiere documenter),
comprueba sus candidatos en `docs/knowledge/candidates/{pending,needs_changes}/`.
Si hay candidatos, handoffs que atender o propuestas que no pudieron persistirse,
lee `"$DEVKIT/references/phase4-knowledge-gate.md"` antes de entregarlos a Curator.
Curator juzga y el servicio persiste; el orquestador sólo conserva el handoff en
su ledger. Revisión/QA no aprueban memoria. Sin candidatos, informa una línea y
continúa; una propuesta fallida se declara pendiente, no ausencia de propuestas.

## Fase 5 — Seguridad (opcional, agente `nemesis`)
Si el usuario lo pide o la iniciativa lo amerita, invoca **`nemesis`** para auditar la seguridad de lo construido (solo entornos locales/privados).

## Fase 6 — Sincronizar y cerrar

**Ritual de cierre de rama (obligatorio, en orden):**

1. **Verificación final sobre la rama**: suites y lint del proyecto en verde (las mismas comprobaciones de P5 del implementer, una última vez sobre el estado final).
2. **Commits ordenados**: un commit lógico por tarea (`T-XX: …`), sin restos de instrumentación temporal (logs/asserts de diagnóstico fuera del diff — regla de `debug-root-cause`). Conserva la puerta de alcance del ledger y elige una lista de archivos relativos exactos. Usa `agent-kits/shared/commit-selection.py` desde el `$SHAREDKIT` ya resuelto: `preview --root <proyecto> --path <archivo>` (repite `--path`), muestra selección, patch, cambios no seleccionados y staging ajeno, y conserva el JSON fuera de Git. Para archivos nuevos, registra explícitamente sólo los elegidos con intent-to-add antes del preview. No atribuyas al ciclo el staging previo de un archivo seleccionado: un conflicto deja ese contenido intacto. Revalida el JSON por stdin con `validate --root <proyecto>` inmediatamente antes del commit; sólo exit 0 habilita `git --literal-pathspecs commit --only --pathspec-from-file=- --pathspec-file-nul -m <mensaje>` con la lista revisada UTF-8/NUL por stdin. Comprueba después árbol/blobs/modos y conservación del staging ajeno; una discrepancia se informa, sin reescritura automática. Sin helper o con error, queda pendiente el commit y continúa el trabajo permitido; no se sustituye por staging global. Detalle y límites: [selección de commits](../docs/COMMIT-SELECTION.md). Esto no autoriza push, merge, PR ni release por sí mismo.
3. **Resumen de merge/PR derivado del LEDGER** (no de memoria): título, qué se hizo tarea a tarea, criterios de aceptación cumplidos, veredicto de qa-gate y ruta de las evidencias. Es la descripción del PR o el mensaje del merge. Si el repo trae plantilla de PR (`pull_request_template.md`, en mayúsculas o minúsculas, en `.github/` o `docs/`, o la carpeta `.github/PULL_REQUEST_TEMPLATE/`), rellena SUS secciones con este resumen (N/A en las que no apliquen, sin borrarlas). Antes de crear el PR fija base y head explícitos (la base no se supone: `main` no siempre es la principal) y comprueba que la rama no tiene ya uno abierto (`gh pr list --head <rama> --state open`; sin `gh`, pregunta); si lo tiene, dilo y propón actualizar su descripción en vez de abrir otro.
4. **Integración según el flujo del repo**: merge directo o PR — si no está claro cuál usa el equipo, **pregunta**; no mergees por defecto.
5. **Limpieza**: rama integrada eliminada; worktrees retirados (`git worktree remove` + `prune`); marcadores de usage-meter sin huérfanos (`usage-meter.py status` limpio).
6. **Estados del plan**: plan/tasks → `completado` (lo exigen `changelog-sync` y la retro) y fila del índice del roadmap al día con ese estado. Si `ledger-lint.py` avisa del tamaño, `ledger-archive.py … --apply` antes de cerrar (ver «Ledger grande» en la Fase 3). La spec **todavía no**: pasa a `implementada` en el paso 9, solo con la puerta del paso 8 abierta.
7. **Notas de cambios**: con el ledger ya en `completado`, invoca la skill **`changelog-sync`** (determinista, idempotente) para generar las entradas `[Unreleased]`/`[Sin publicar]` de esta iniciativa en ambos CHANGELOG, y afina la redacción sin ampliar alcance. El bullet sale del campo `- **Changelog**:` de cada tarea, así que **antes de invocarla comprueba que las tareas cerradas lo traen** (`changelog-sync.py --check` te lista las que no; sin campo el bullet degrada al título). No crea la sección de versión: eso es del release.
8. **Retro — PUERTA, no aviso (memory-retrieval T-17, spec CA-23).** Con el ledger ya en `completado`, ejecuta `/retro docs/roadmap/<fecha>-<slug>` (las causas de desviación las escribe quien las conoce: el usuario responde, tú registras; ahí también se muestran las candidatas a lección del journal) y después la puerta determinista `python3 "$SHAREDKIT/retro-gate.py" docs/roadmap/<fecha>-<slug>` (mismo `$SHAREDKIT` que el resto del ciclo) → **exit 0 obligatorio**: `retro.md` con título y cuerpo, o frontmatter cerrado y cuerpo, más la fila de la iniciativa en `docs/roadmap/CALIBRATION.md`. Con exit 1 la iniciativa **no se declara cerrada** ni la spec pasa a `implementada`: el resumen final dice «cierre pendiente de retro» y qué falta (el script lo lista con el comando exacto). Sin `python3`, comprueba a mano los dos ficheros y dilo. Es el patrón de `qa-gate`/`ledger-lint`: un aviso que se puede ignorar se ignorará (`LES-012`).
9. **Cierre declarado**: solo con la puerta abierta, spec → `implementada` (tabla de abajo) y el resumen final. Con la puerta cerrada la spec se queda `aprobada` aunque el plan esté `completado` — es la señal visible (en `/roadmap-status`, en el índice) de que falta la retro.

La documentación/artefactos se sincronizan con Confluence vía `confluence-publish` (opt-in; la invocan los agentes al escribir en `docs/`). Cierra con un resumen: iniciativa, tareas completadas, estado de pruebas, coste medido (usage-meter), ruta de la doc y enlaces. La retro ya no es «siguiente paso natural»: es el paso 8 del ritual, y sin ella no hay paso 9 (la spec no pasa a `implementada`).

## Transiciones de estado (OBLIGATORIAS en cada fase)
Los artefactos nacen en `borrador`. En **cada fase/puerta** que se supera, actualiza su estado
(frontmatter + cabecera) al que toque; **no dejes nada en `borrador`** al avanzar. Vocabularios:
spec = `borrador · aprobada · implementada · obsoleta`; evaluación/plan/tareas = `borrador ·
en-progreso · en-revision · completado · cancelado`; design = `borrador · aprobado · obsoleto`.

> **Vía rápida:** no hay spec/evaluación/plan que transicionar — solo el `tasks.md` ligero, que sigue el vocabulario de tareas (`borrador → en-progreso → completado`). Todo lo demás de esta tabla se salta.
>
> **`design.md` (opcional, agente `architect`):** vocabulario propio `borrador · aprobado · obsoleto`. Solo existe si se hizo el paso de diseño; la columna queda `—` si no.

| Momento | spec | evaluación | design (opcional) | plan / tasks |
|---|---|---|---|---|
| Tras evaluar (Fase 1) | borrador | `en-revision` | — | — |
| Puerta **go** | `aprobada` | `completado` | — | — |
| Puerta **no-go** | (obsoleta si se descarta) | `cancelado` | — | — |
| Diseño presentado (Fase 2-a) | aprobada | completado | `borrador` (opciones abiertas) | — |
| Opción validada por el usuario | aprobada | completado | `aprobado` | — |
| Plan creado (Fase 2-b) | aprobada | completado | aprobado (`plan:` relleno) | `borrador` |
| Puerta OK del plan → arranca impl. | aprobada | completado | aprobado | `en-progreso` (plan y fase activa) |
| Durante impl. (Fase 3) | aprobada | completado | aprobado | tareas `en-progreso`→`completado`; fase `completado` al cerrar |
| qa en rojo | aprobada | completado | aprobado | tarea/plan → `en-progreso` (reabrir) |
| Re-diseño (se descarta la opción) | aprobada | completado | `obsoleto` → nuevo `design.md` `borrador` | plan `en-revision` |
| Cierre (revisión sin gaps + qa verde + documentado + retro-gate exit 0) | `implementada` | completado | aprobado | plan `completado` |
| Cancelación en cualquier punto | (obsoleta) | `cancelado` | `obsoleto` | `cancelado` |

Aplica la transición **en el mismo paso** en que se cruza la puerta, y mantén coherente la tabla
de resumen de `tasks.md`.

**Estas transiciones son responsabilidad del orquestador.** En el flujo normal,
`implementer` registra el progreso de sus tareas según sus instrucciones; con subagentes frescos,
lo registras tú después de validar sus retornos. QA entrega veredicto y evidencia: tú reabres las
tareas afectadas con rojo y aplicas las transiciones de las puertas (go/no-go, OK del plan,
cierre), garantizando que `tasks.md` refleje el progreso.

## Reglas del orquestador
- **Invoca a los agentes por nombre**; no dependas de la auto-delegación.
- **Autosuficiente:** el ciclo completo lo hacen los agentes del plugin; no hay motor de implementación externo ni dependencia de otros plugins.
- **`tasks.md` es la fuente única de progreso.**
- **Respeta las puertas** (go/no-go, OK de plan, verde de pruebas).
- Si el usuario pide solo una parte (p. ej. "solo planifica"), ejecuta hasta esa fase y detente.
