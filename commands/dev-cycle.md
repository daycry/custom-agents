---
description: >
  Orquesta el ciclo completo de una iniciativa (spec → evaluación → plan → implementación → pruebas →
  documentación) con la cadena nativa del plugin como único motor (autosuficiente: TDD, worktrees,
  subagentes frescos y debugging sistemático opt-in). Invoca los agentes por nombre y con puertas de
  control.
argument-hint: <objetivo de la iniciativa> [rapido | completo]
---

# /dev-cycle — orquestador del ciclo de desarrollo

Ejecuta el ciclo de una iniciativa de forma explícita y fiable. Objetivo: **$ARGUMENTS**.

Mantén `docs/roadmap/<fecha>-<slug>/tasks.md` como **ledger canónico** de progreso en todo el
ciclo (ver regla 8 de `docs/CONVENTIONS.md`).

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
4. Para cada cambio, identifica el comportamiento observable que probaría el resultado y los patrones pertinentes ya usados en el proyecto, con sus rutas. Si aún faltan, encarga su búsqueda al rol responsable y conserva ese pendiente. Este contexto acompaña al objetivo; no crea otro artefacto, aprobación ni etapa obligatoria de investigación.

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
Invoca **`evaluator`** con el objetivo y el encargo conservado en la Fase 0: crea/lee `spec.md` y produce `evaluation.md` (coste, esfuerzo, veredicto). Esto es valor propio: el presupuesto en €/tokens antes de construir.

**Puerta go/no-go:** muestra el veredicto y pregunta si continuar. Si no-go, para.

## Fase 2 — Planificar (solo en flujo completo: `architect` opcional → `planner`)

**Fase 2-a — Diseño (agente `architect`, opt-in).** Invoca **`architect`** ANTES de `planner` si (a) la
carpeta ya tiene `design.md` (lo creó `/pm-cycle` 2-bis) — si está `aprobado`, salta a 2-b; si está en
`borrador` (`opcion_elegida: pendiente`), retoma en el paso 2 de abajo — o (b) el usuario lo pide («explora
el diseño», «compara opciones antes de planificar»). Si no se da ninguna, **ofrécelo en una línea** cuando
la evaluación marque complejidad Alta o riesgo arquitectónico; si no, ve directo a 2-b. **Dos pasadas** (el
subagente devuelve UN mensaje; la validación por trozos es tuya, como la puerta go/no-go):
1. Invoca `architect` SIN `elegida:` → `design.md` en `borrador` + resumen estructurado (una línea por
   opción, recomendada, pregunta).
2. **Presenta al usuario por trozos**: AskUserQuestion en Cowork (una opción por entrada, recomendada
   marcada) / lista numerada + pregunta en CLI. Recoge la elección (o una variante).
3. Re-invoca `architect` con `elegida: O<n>` (o `variante: …` → repite 1-2). Fija la opción,
   enlaza `design:` en spec/plan y pasa `design.md` a `aprobado`. Si la decisión cruza el umbral,
   `architect` propone el candidato mediante `knowledge-curation.py propose`, según
   `agent-kits/shared/knowledge-write.md`; conserva ruta pending/SHA para Curator y `adr:` en
   `design.md`. Sin servicio, deja `adr: pendiente` y el motivo. Elegir diseño no aprueba memoria.
**Puerta:** `design.md` en `aprobado` (o el usuario decide seguir sin diseño).

**Fase 2-b — Plan (agente `planner`).** `planner` genera los artefactos del plan en `docs/roadmap/<…>/`:
`improvement-plan.md` + `tasks.md` (+ `test-plan.md` si hay UI), con las plantillas del kit — así
la estructura y el ledger canónico existen siempre. Si existe `design.md` aprobado, `planner` lo lee
y **respeta la opción elegida** (enlaza `design:` ↔ `plan:`). Puerta: OK del plan.

**Revisión visual del plan (opcional, en esta misma puerta).** Si ya existe una
autorización conversacional suficiente, continúa sin abrir revisión ni pedir otro
OK. Cuando el usuario pide revisar visualmente, selecciona la iniciativa exacta;
no busques la última. La revisión sustituye el OK pendiente de esta puerta.
La vía rápida sin `improvement-plan.md` conserva su autorización existente.

Usa la sintaxis del shell real, no la deduzcas del runtime. Fija proyecto autorizado,
iniciativa relativa exacta, runtime (`claude-code`, `codex` u `opencode`) y ejecutable
Python 3 comprobado. En Windows `python3` puede ser sólo un alias de WindowsApps:
elige un intérprete real por su ruta, sin ejecutar el alias como prueba de disponibilidad.
No cambies al worktree después de abrir la revisión.

Si el runtime identifica el bundle activo, fija `REVIEW_BUNDLE` (Bash) o
`$ReviewBundle` (PowerShell) a esa fuente. En otro caso, busca en las seis raíces,
proyecto antes que usuario. Exige dueño, validador de apertura y builder en el mismo bundle completo;
varias copias completas en una raíz son ambiguas: identifica la fuente activa
antes de abrir. No mezcles instalaciones parciales. La búsqueda no acredita carga
nativa ni autentica el bundle; conserva su procedencia junto al handle.

**Bash.** Fija `PROJECT_ROOT`, `REVIEW_INITIATIVE`, `REVIEW_RUNTIME` y
`REVIEW_PYTHON` como variables del shell (rutas entre comillas). La preparación es:

<!-- plan-review:prepare:bash -->
```bash
: "${PROJECT_ROOT:?}" "${REVIEW_INITIATIVE:?}" "${REVIEW_PYTHON:?}"
case "$REVIEW_RUNTIME" in claude-code|codex|opencode) ;; *) exit 3 ;; esac
if [ ! -f "$REVIEW_PYTHON" ] || [ ! -s "$REVIEW_PYTHON" ] || [ ! -x "$REVIEW_PYTHON" ]; then
  printf '%s\n' 'Revisión visual: se requiere un ejecutable Python real por su ruta.' >&2
  exit 3
fi
if [ -z "${REVIEW_BUNDLE:-}" ]; then
  for root in "$PROJECT_ROOT/.claude" "$PROJECT_ROOT/.codex" "$PROJECT_ROOT/.opencode" \
              "$HOME/.claude" "$HOME/.codex" "$HOME/.config/opencode"; do
    candidates=()
    while IFS= read -r -d '' owner; do
      candidate="${owner%/agent-kits/shared/plan-review.py}"
      if [ -f "$candidate/skills/plugin-panel/scripts/build_panel.py" ] && \
         [ -f "$candidate/agent-kits/shared/plan-review-open.py" ]; then
        candidates+=("$candidate")
      fi
    done < <(find "$root" -type f -path '*/agent-kits/shared/plan-review.py' -print0 2>/dev/null)
    if [ "${#candidates[@]}" -gt 1 ]; then
      printf '%s\n' 'Revisión visual: bundle ambiguo; identifica la fuente activa.' >&2
      exit 3
    fi
    if [ "${#candidates[@]}" -eq 1 ]; then REVIEW_BUNDLE="${candidates[0]}"; break; fi
  done
fi
PLANREVIEW="${REVIEW_BUNDLE:-}/agent-kits/shared/plan-review.py"
REVIEW_OPEN_CHECK="${REVIEW_BUNDLE:-}/agent-kits/shared/plan-review-open.py"
PANELBUILDER="${REVIEW_BUNDLE:-}/skills/plugin-panel/scripts/build_panel.py"
if [ ! -f "$PLANREVIEW" ] || [ ! -f "$REVIEW_OPEN_CHECK" ] || [ ! -f "$PANELBUILDER" ]; then
  printf '%s\n' 'Revisión visual no disponible: falta un bundle completo.' >&2
  exit 3
fi
REVIEW_PYTHON_ARGS=(-I -X utf8 -B)
REVIEW_SCOPE=(--project "$PROJECT_ROOT" --state-root "$PROJECT_ROOT/.claude/plan-review")
```

<!-- plan-review:open:bash -->
```bash
REVIEW_OPEN_JSON="$("$REVIEW_PYTHON" "${REVIEW_PYTHON_ARGS[@]}" "$PLANREVIEW" open "${REVIEW_SCOPE[@]}" \
  --initiative "$REVIEW_INITIATIVE" --gate-key plan-ok \
  --caller-id dev-cycle --runtime "$REVIEW_RUNTIME" --json)" || exit $?
printf '%s' "$REVIEW_OPEN_JSON" | "$REVIEW_PYTHON" "${REVIEW_PYTHON_ARGS[@]}" \
  "$REVIEW_OPEN_CHECK" --initiative "$REVIEW_INITIATIVE" || exit $?
```

**PowerShell.** Fija `$ProjectRoot`, `$ReviewInitiative`, `$ReviewRuntime` y
`$ReviewPython` a los mismos datos, y `$ReviewHome` a la raíz personal del runtime.
No uses `$HOME` para guardar otra ruta. La preparación equivalente es:

<!-- plan-review:prepare:powershell -->
```powershell
$ErrorActionPreference = 'Stop'
if (!$ProjectRoot -or !$ReviewInitiative -or !$ReviewPython -or !$ReviewHome) {
  throw 'Revisión visual: faltan entradas explícitas.'
}
if ($ReviewRuntime -notin @('claude-code', 'codex', 'opencode')) { throw 'Runtime inválido.' }
if (!(Test-Path -LiteralPath $ReviewPython -PathType Leaf) -or
    (Get-Item -LiteralPath $ReviewPython).Length -eq 0) {
  throw 'Revisión visual: se requiere un ejecutable Python real por su ruta.'
}
if (!(Test-Path Variable:ReviewBundle)) { $ReviewBundle = $null }
if (!$ReviewBundle) {
  $ReviewRoots = @("$ProjectRoot/.claude", "$ProjectRoot/.codex", "$ProjectRoot/.opencode",
                   "$ReviewHome/.claude", "$ReviewHome/.codex", "$ReviewHome/.config/opencode")
  foreach ($root in $ReviewRoots) {
    $candidates = @()
    if (Test-Path -LiteralPath $root -PathType Container) {
      $owners = @(Get-ChildItem -LiteralPath $root -Filter plan-review.py -File -Recurse -ErrorAction SilentlyContinue)
      foreach ($owner in $owners) {
        if ($owner.FullName.Replace('\', '/').EndsWith('/agent-kits/shared/plan-review.py')) {
          $candidate = $owner.Directory.Parent.Parent.FullName.Replace('\', '/')
          if ((Test-Path -LiteralPath "$candidate/skills/plugin-panel/scripts/build_panel.py" -PathType Leaf) -and
              (Test-Path -LiteralPath "$candidate/agent-kits/shared/plan-review-open.py" -PathType Leaf)) {
            $candidates += $candidate
          }
        }
      }
    }
    if ($candidates.Count -gt 1) { throw 'Revisión visual: bundle ambiguo; identifica la fuente activa.' }
    if ($candidates.Count -eq 1) { $ReviewBundle = $candidates[0]; break }
  }
}
$PlanReview = "$ReviewBundle/agent-kits/shared/plan-review.py"
$ReviewOpenCheck = "$ReviewBundle/agent-kits/shared/plan-review-open.py"
$PanelBuilder = "$ReviewBundle/skills/plugin-panel/scripts/build_panel.py"
if (!(Test-Path -LiteralPath $PlanReview -PathType Leaf) -or
    !(Test-Path -LiteralPath $ReviewOpenCheck -PathType Leaf) -or
    !(Test-Path -LiteralPath $PanelBuilder -PathType Leaf)) {
  throw 'Revisión visual no disponible: falta un bundle completo.'
}
$ReviewPythonArgs = @('-I', '-X', 'utf8', '-B')
$ReviewScope = @('--project', $ProjectRoot, '--state-root', "$ProjectRoot/.claude/plan-review")
```

<!-- plan-review:open:powershell -->
```powershell
$ReviewOpenJson = (& $ReviewPython @ReviewPythonArgs $PlanReview open @ReviewScope --initiative $ReviewInitiative --gate-key plan-ok --caller-id dev-cycle --runtime $ReviewRuntime --json | Out-String)
if ($LASTEXITCODE -ne 0) { throw 'No se pudo abrir la revisión visual.' }
$ReviewSavedOutputEncoding = $OutputEncoding
try {
  $OutputEncoding = New-Object System.Text.UTF8Encoding($false)
  $ReviewOpenJson | & $ReviewPython @ReviewPythonArgs $ReviewOpenCheck --initiative $ReviewInitiative
  if ($LASTEXITCODE -ne 0) { throw 'La apertura no corresponde a una vista completa y vigente.' }
} finally { $OutputEncoding = $ReviewSavedOutputEncoding }
```

`plan-review-open.py` comprueba la apertura antes de servir y devuelve sólo
`review_id`, la tupla de versión y `approval_granted: false`. No escribe estado
ni aprueba el plan. Conserva el JSON original en la variable privada del shell.
El comprobador exige
`schema_version: 1`, `status: ok`, iniciativa exacta, `artifact: improvement-plan.md`,
`gate_key: plan-ok`, `complete: true` y `validity: current`.
`consumer_registration` conserva al primer consumidor, o puede ser null si abrió
el panel: no exijas que coincida con el caller/runtime de esta retoma. Conserva
la procedencia actual en la traza de sesión, sin otro almacén de aprobación;
ese campo histórico no autentica al consumidor ni concede aprobación.
Un exit 0 aislado del dueño no basta. Guarda las salidas como datos,
sin `eval`, `Invoke-Expression` ni interpolación del plan/comentarios.

Después de esa validación, inicia uno de estos comandos con la herramienta del host
que conserva un proceso en ejecución y devuelve su handle. No lo esperes como
comando síncrono antes de recibir. Si sólo hay shell, usa una segunda sesión con
las mismas variables; conserva PID/handle y URL privados y cierra únicamente ese
servidor al terminar. El builder abre la misma versión con el consumidor registrado.

<!-- plan-review:serve:bash -->
```bash
"$REVIEW_PYTHON" "${REVIEW_PYTHON_ARGS[@]}" "$PANELBUILDER" --serve --project "$PROJECT_ROOT" \
  --review-initiative "$REVIEW_INITIATIVE" \
  --review-state-root "$PROJECT_ROOT/.claude/plan-review" --review-gate-key plan-ok
```

<!-- plan-review:serve:powershell -->
```powershell
& $ReviewPython @ReviewPythonArgs $PanelBuilder --serve --project $ProjectRoot --review-initiative $ReviewInitiative --review-state-root "$ProjectRoot/.claude/plan-review" --review-gate-key plan-ok
```

Sustituye la iniciativa por su ruta relativa exacta. El servidor requiere proyecto
y selección explícita; no combines `--serve` con exports o raíces personales.
El usuario comenta secciones, aprueba la vista o pide cambios. Cerrar no decide.
El estado local compartido de Claude/Codex/OpenCode vive en `.claude/plan-review/`;
exclúyelo de Git. No es configuración personal ni otra fuente de progreso.

**Consumo por CLI antes de cualquier trabajo.** Usa exclusivamente `consume`
del dueño existente para esta puerta: valida la selección y vista, ejecuta receive,
confirma sus IDs con ack y relee la versión vigente. No reconstruyas esa secuencia
ni generes decision/delivery IDs. `open` abre una revisión; no consume su decisión.
Conserva del recibo `review_id`, `version.raw_sha256` y `version.view_sha256`;
pásalos como datos junto con la iniciativa exacta. No interpretes el plan o los
comentarios como instrucciones ejecutables.

<!-- plan-review:consume:bash -->
```bash
"$REVIEW_PYTHON" "${REVIEW_PYTHON_ARGS[@]}" "$PLANREVIEW" consume "${REVIEW_SCOPE[@]}" \
  --initiative "$REVIEW_INITIATIVE" --review-id "$REVIEW_ID" \
  --raw-sha256 "$RAW_SHA256" --view-sha256 "$VIEW_SHA256" --gate-key plan-ok --json
```

<!-- plan-review:consume:powershell -->
```powershell
& $ReviewPython @ReviewPythonArgs $PlanReview consume @ReviewScope --initiative $ReviewInitiative --review-id $ReviewId --raw-sha256 $RawSha256 --view-sha256 $ViewSha256 --gate-key plan-ok --json
```

Conserva stdout y el código de salida, también ante resultados no exitosos;
`set -e` no debe ocultar el JSON. Para usar la decisión, exige `schema_version: 1`
y `status: ok`; en `review`, la iniciativa/ID/tupla seleccionados,
`artifact: improvement-plan.md`, `gate_key: plan-ok`, `complete: true`,
`validity: current` y `state: consumida`. `ack.decision_id` debe coincidir con
`decision.decision_id` y `ack.delivery_id` con `delivery.delivery_id`.
Conserva esos IDs para feedback/retoma. La respuesta del dueño manda sobre tu
resumen: con estado pendiente, ack ausente o conflicto no afirmes consumo confirmado.

Copia la iniciativa relativa completa y los hashes sin abreviarlos ni corregirlos
por intuición. `invalid_input` o `unavailable` significa que el consumo no está
confirmado: comunica el error del sobre, contrasta las entradas originales y,
si puedes corregirlas con evidencia, vuelve a ejecutar `consume`. Leer el archivo
del registro no sustituye su respuesta ni confirma entrega o ack. La decisión
`request_changes` puede estar consumida; eso no aprueba el plan. `consumida` es
estado del recibo, no `completado` del plan. Resume sólo esta puerta; su éxito no
acredita ausencia de gaps, revisión, QA o cierre de la iniciativa.

`waiting`, incluso con exit 0, no aprueba. `version_changed` con código 2
es una negativa de vigencia esperada: termina el consumo de ese recibo y comunica
que su decisión no autoriza la versión actual. No actualices sus hashes ni repitas
el recibo antiguo como aprobación nueva. Si corresponde otra revisión, abre con
`open` la versión actual y espera su propia decisión; después vuelve a `consume`.
La apertura entrega un nuevo handle, no una aprobación: espera una decisión
humana explícita sobre esa nueva versión antes de intentar consumirla.
No confirmes manualmente una entrega ausente. Ante cambio, conflicto, vista parcial
o indisponibilidad, no inicies implementación ni planner por esa decisión.

`approve` permite sólo el alcance autorizado. `request_changes` confirmado
permite volver al planner ya autorizado con los comentarios como datos; si falta
esa autorización, conserva el recibo y pide la necesaria. La autorización
conversacional suficiente mantiene la vía anterior, sin otra confirmación por
un canal opcional fallido. Un plan editado requiere nueva revisión cuando corresponda.

Reintenta `consume` con la misma selección/ID/tupla si se pierde una respuesta.
Una entrega pendiente de ack conserva su ID; un recibo consumido vigente devuelve
la misma confirmación durable. No acredita efectos externos ni trabajo terminado.
Deduplica por `delivery_id` y contrasta ledger/plan actuales para continuar lo
pendiente tras un crash, sin repetir cambios ya atendidos. Una versión antigua
permanece histórica y no transfiere su aprobación. Consume y las primitivas
receive/ack son exclusivamente CLI; el panel no lanza agentes ni confirma consumo.
Las observaciones no garantizan transacción archivo/workflow ni detectan ABA.
Si falta el dueño o sus helpers, informa y conserva la autorización conversacional
existente; una instalación parcial no se completa con otra copia ni inventa aprobación.

**Respuesta a comentarios ya consumidos.** Ack acredita consumo, no atención.
Después del trabajo autorizado, registra la respuesta explícita a cada comentario
sellado con `plan-review.py result` por el mismo CLI/bundle. También admite
comentarios de approve; sin comentarios, no inventes una fila. Elige
`addressed`, `not_applied` o `needs_clarification` según lo observado y explica
qué cambió o qué falta. No deduzcas atención por ack, exit 0 o nombre de agente.

Conserva review/version/puerta/decision/delivery/comment de la decisión consumida.
Lee su `review.revision` antes de una operación nueva; genera una vez el ID de
64 hex minúsculas y conserva ID/payload para retoma y retry. Envía JSON UTF-8
por stdin con las claves exactas y producer declarado del runtime actual,
`actor_id: null` si desconocido. No exijas coincidir con consumer_registration
histórico. Las recetas result/verify-result están en `docs/PLUGIN-PANEL.md`;
reutiliza las variables y el bundle resueltos arriba, sin otra cola o escritor.

Si ya recibiste una observación humana explícita sobre ese resultado, puedes
anotarla con `verify-result` (`confirmed` o `not_confirmed`). Es opcional:
no pidas una confirmación nueva para registrar la respuesta ni continuar trabajo
autorizado. No infieras esa observación desde un test, cambio de archivo o ack.
La identidad declarada del caller no autentica al humano ni al agente.

Valida status ok y feedback_receipt ligado a la petición: `review: null` y
`approval_granted: false` son recibo de feedback, nunca permiso de implementación.
Un timeout o respuesta perdida conserva ID/payload; reintenta sin regenerarlos.
Ante revision_conflict, relee ese registro y reconcilia; operation_conflict no
se sobrescribe. Si corriges un resultado, usa otro result_id y supersedes del
último resultado del comentario. Un fallo opcional deja feedback pendiente visible
y mantiene la autorización anterior, sin fabricar una anotación.

Si atender el comentario editó el plan, la respuesta conserva la revisión antigua
consumida; no transfiere comentarios ni concede aprobación a la nueva versión.
El panel muestra respuestas/historial por versión. No modifica los pasos previos
receive/ack/relectura ni sustituye ledger, QA o curación de memoria.

Detalles de vista y persistencia: consulta `docs/PLUGIN-PANEL.md` en la documentación del plugin.

> **Jira (opcional, opt-in).** Recién creado el plan, `planner` **ofrece** volcar las tareas a Jira
> con la skill `jira-sync` (un issue por tarea bajo el proyecto/épica elegidos; selector visual en
> Cowork o conversacional en CLI/VS Code). Luego, durante la implementación, al completar cada tarea
> `implementer` imputa horas (Tiempo IA + Supervisión, tope jornada) con `implementado`; el issue
> sigue En curso. El orquestador dispara `aprobado` para pasar a *Done* sólo con revisión sin gaps
> y qa verde, según el ciclo de eventos de la Fase 3. Todo
> sujeto al opt-in de `.claude/jira.json`: aunque el conector esté conectado, si Jira no se activó
> para el proyecto, no se toca nada.

## Fase 3 — Implementar y probar

> **Disciplina de desarrollo (`.claude/dev.json`, opt-in, defaults off — la crea `/setup`).** Antes de implementar, lee la config: `tdd: true` → el implementer sigue la skill **`tdd`** (fuente única de RED-GREEN-REFACTOR) por tarea con evidencia del rojo en el ledger; `worktree: true` → la iniciativa se trabaja en un worktree de git aislado (degradación a rama normal con aviso si no hay soporte); `subagentes: true` → el despacho por subagentes de contexto fresco (ver más abajo). Sin fichero o corrupto: defaults `false` + aviso — comportamiento clásico. Las tres opciones son combinables.

1. **`implementer`** → implementa fase a fase sobre rama (o worktree, si `worktree: true`), marcando `tasks.md` por tarea (con RED-GREEN-REFACTOR si `tdd: true`).

   **Despacho por subagentes de contexto fresco (si `subagentes: true` en `.claude/dev.json`).** En vez de implementar todas las tareas en un mismo contexto, cada `T-XX` la ejecuta un **subagente fresco** (Task tool) que no arrastra el ruido de las tareas anteriores. El ciclo por tarea, que coordinas TÚ (el orquestador):
   1. **Brief determinista** — genera el brief con el script del kit shared (nunca lo redactes a mano):

      ```bash
      SHAREDKIT="$(find "$PWD/.claude" "$PWD/.codex" "$PWD/.opencode" "$HOME/.claude" "$HOME/.codex" "$HOME/.config/opencode" -type d -path '*agent-kits/shared' 2>/dev/null | head -1)"
      python3 "$SHAREDKIT/task-brief.py" "docs/roadmap/<fecha>-<slug>" T-XX --runtime <claude-code|codex|opencode>
      ```

      Sustituye el runtime por el de esta sesión. Si la selección usó otro home,
      raíz personal o paquete, conserva esos valores con `--extensions-*` del
      método común. El script valida el ledger (`ledger-lint`) y extrae SOLO lo que hace falta para esa tarea:

      - **Tarea + criterios + fase**, tal cual el ledger.
      - **Extensiones seleccionadas**, IDs revalidados en las fuentes actuales del runtime y referencias ≤1000 caracteres; sin precargar prompts o manuales. Contrasta disponibilidad y permisos con la sesión antes de invocar. Un aviso conserva el contrato y los gates del ciclo.
      - **Persona de dominio** (si la tarea lleva `- **Tipo**: <tipo>`), cascada de tres escalones desde `project-specialization` T-01: `.claude/personas/<tipo>.md` DEL PROYECTO primero, doctrina propia del equipo; **gana si existe y se puede leer** — un fichero vacío o un `OSError` al leerlo (p. ej. OneDrive «solo en la nube» sin red) cae al siguiente escalón sin bloquear. Si no hay perfil de proyecto (o cayó), el perfil corto de `agent-kits/shared/personas/<tipo>.md` del catálogo del plugin. Los tipos son **libres**, no hay lista cerrada. Sin etiqueta → subagente genérico; etiqueta sin persona en ningún escalón → aviso y genérico, nunca bloquea.
      - **Opción elegida de `design.md`** (si existe y está `aprobado`; solo esa sección).
      - **Arquitectura + constitución** (si existe) **+ el contrato de retorno**.

      Exit ≠ 0 → arregla la causa antes de despachar.
   2. **Despacho brief-only** — lanza el subagente con el brief como único contexto (con `tdd: true`, `task-brief.py` ya incluye la sección «TDD» que manda seguir la skill `tdd` y devolver la evidencia del rojo). El subagente NO explora el repo entero: el brief y los ficheros que referencia.
   3. **Estados de retorno** — el subagente termina en uno de: `DONE` (valida tú contra los criterios ANTES de marcar `completado` en el ledger) · `DONE_WITH_CONCERNS: <duda>` (valida y pasa la duda a la revisión de dos lentes) · `NEEDS_CONTEXT: <qué>` (re-despacha UNA vez añadiendo al brief exactamente lo pedido — el subagente tiene PROHIBIDO inventar) · `BLOCKED: <qué>` (resuélvelo tú o pregunta al usuario; no re-despaches a ciegas).
   4. **Re-despacho acotado** — máximo **1** re-despacho por tarea (por gap de validación o por `NEEDS_CONTEXT`); si el segundo intento tampoco cierra, la tarea pasa al **flujo normal** (`implementer` en contexto principal) con aviso en el ledger.
   5. **Las puertas no cambian**: la medición por tarea (usage-meter), la revisión de dos lentes y `qa-gate` se ejecutan exactamente igual — el despacho solo cambia QUIÉN implementa, no qué se valida.
   6. **Despacho PARALELO de tareas independientes (opcional dentro de `subagentes: true`).** Las tareas de una MISMA fase **sin dependencias entre sí** (campo `Dependencias` del ledger) pueden despacharse en un lote paralelo de **máximo 3** subagentes. Condición de aislamiento: con `worktree: true`, cada tarea del lote trabaja en su propio worktree **temporal de tarea** (`git worktree add ../<repo>-<slug>-TXX -b tmp/<slug>-TXX`, ramificado desde `feature/<slug>` — es la excepción al worktree único por iniciativa de P2 del implementer); sin worktrees, solo paraleliza tareas cuyos campos `Archivos` no se solapen (si tocan lo mismo, secuencial). En ambos casos, **ficheros disjuntos no son estado disjunto**: las tareas que migran esquema o escriben en el mismo almacén o servicio (misma base de datos, tabla, cola o despliegue) van en secuencia aunque sus `Archivos` no se solapen. Los retornos los validas **secuencialmente** (uno a uno contra sus criterios) y, al validar cada `DONE`, **reintegras su rama temporal en `feature/<slug>`** con `git merge --no-ff --no-commit` y, sobre ese árbol combinado, vuelves a ejecutar la `Verificación` de esa tarea y la de las tareas del lote ya integradas: solo con todo en verde haces el commit del merge; un rojo o un conflicto → `git merge --abort` y esa tarea vuelve al flujo secuencial. Después retiras su worktree — así, cuando lances la **revisión de dos lentes**, TODO el trabajo del lote está en `feature/<slug>` y el diff que ven los revisores es completo. Solo tú tocas el ledger. **Medición honesta del lote:** en paralelo las ventanas de usage-meter se solapan (contarían los mismos tokens varias veces), así que el lote se mide con UNA clave (`usage-meter.py start --artefacto "<slug>/lote-<n>"`) y las horas medidas se **reparten proporcionalmente a la estimación** de cada tarea, marcadas `(medido, lote)` en el ledger — jamás lo presentes como medición individual exacta. Con despacho secuencial (el default), nada de esto aplica.

   **TDD en modo subagentes:** con `tdd: true`, el subagente devuelve la evidencia del rojo junto a su estado; como el subagente tiene PROHIBIDO tocar el ledger, **eres tú (orquestador)** quien registra la línea `RED: <test> falló con <error> · <fecha>` en la tarea del ledger al validar el `DONE` — sin esa línea, el TDD de la tarea no cuenta.

   **Medición por tarea (usage-meter).** Al ARRANCAR cada `T-XX`: `usage-meter.py start --artefacto "<slug>/T-XX"`; al COMPLETARLA: `close` con la misma clave (en el flujo clásico lo ejecuta el `implementer` — su P3 lo trae; con `subagentes: true` lo coordinas tú por despacho). Las **horas-IA medidas** del JSON (`horas_ia`, con `fuente: medido`) se escriben como tiempo IA **real** de la tarea en `tasks.md` — anota `(medido)` junto al valor — y son las que usa la imputación a Jira (`worklog.py plan` ya prefiere real sobre estimado; su aritmética de jornada/banco NO cambia). Reglas: (a) si el meter degrada, deja la estimación a juicio marcada `(estimado)` y sigue; (b) re-medir la MISMA ventana (re-close inmediato) sustituye; pero una **corrección posterior** (gaps de revisión) se mide con clave nueva `"<slug>/T-XX-fix<N>"` y sus horas se **SUMAN** al real de la tarea en el ledger — la implementación original no se pierde; (c) los tokens del bucle de revisión (los revisores) NO van a la tarea — la revisión tiene su propia imputación `[revisión]` por intento (ver más abajo); cierra el marcador de la tarea ANTES de lanzar la revisión. Duraciones presentadas en formato `XhYm` (`usage-meter.py fmt`).
2. **Revisión adversarial — skill `adversarial-review` (fuente única del método; aquí solo se invoca).** Invócala por nombre pasándole: la carpeta de la iniciativa (`docs/roadmap/<fecha>-<slug>/`), el **nº de intento N** y, si N > 1, la **tabla de veredictos del intento anterior** (incluidos los `descartado (rebatido)` con su evidencia). La skill hace el resto: puerta previa `scope-check.py` (exit 1 → gap Important al `implementer` sin gastar revisores), `review-lens-select.py` para decidir si añade la **Lente C** (seguridad, condicional), lentes A/B(/C) en paralelo con contexto fresco, fusión, graduación `Critical / Important / Minor`, arbitraje de los rebates con evidencia, sección «Revisión de dos lentes — intento N» en `tasks.md`, evidencia para Curator al cerrar sin gaps pendientes (sin promoción ni aprobación de memoria), y el **comentario firmado en Jira de CADA intento** (`jira-flow.py --event revision|gaps --intento N`, Paso 7 de `jira-sync`: lo ejecuta la propia skill en su paso 6, no tú) si hay opt-in y plan volcado. Espera de vuelta: veredicto por criterio ✓/✗, gaps graduados con su veredicto, qué lentes corrieron y el ledger actualizado (`ledger-lint` exit 0).
   - **Tuyo (orquestador) — bucle reviewer→implementer ACOTADO (regla dura).** Si quedan gaps Critical/Important: las tareas afectadas vuelven a `en-progreso`, `implementer` corrige (ese tiempo es **implementación**, clave `"<slug>/T-XX-fix<N>"`) y **relanzas la skill** sobre el nuevo diff con contador explícito ("revisión, intento 2 de 3"). **Máximo 3 intentos**; al 3.º con gaps, PARA y pregunta (seguir / re-planificar con `planner` / aceptar como deuda). Rebatir con evidencia **no consume intento**; lo Minor se anota sin bloquear.
   - **Tuyo (orquestador) — worklog `[revisión]` POR INTENTO (si `jira.json` `enabled` y se volcó el plan):** al cerrar cada pasada, `worklog.py plan --kind revision --attempt N` — cada intento queda como su propia entrada en Jira con duración y fecha, y `reviewAttempts` guarda la traza para `/retro`. El **comentario** del intento (`revision`/`gaps`) NO es tuyo: lo publica la skill en su paso 6; si al volver de la skill no hay comentario de ese intento en el issue, es un gap de proceso de la skill, no algo que rellenes tú a mano. Los tokens de los revisores NO van a la tarea: cierra el marcador de la tarea ANTES de invocar la skill.
3. **`qa`** → pruebas E2E (solo local), informe y evidencias. El veredicto verde/rojo lo da `qa-gate.py` (exit code), no una impresión. **Antes de despacharlo, lee el frontmatter de `improvement-plan.md`:** con `test-plan: n/a (sin UI)` la iniciativa no tiene interfaz por diseño, así que invoca `qa` en **modo sin UI** (corre `ledger-lint.py` y `coverage-check.py` —que reconoce el marcador—, sin Playwright ni URL) y anota en el ledger «qa: sin UI por diseño (`test-plan: n/a (sin UI)`)». Sin marcador **y** sin `test-plan.md`, `qa` avisa UNA vez con el comando que lo fija y termina: no lo relances por eso (era la contradicción E1, `ADR-017`).

**Bucle de corrección de qa ACOTADO (regla dura).** Si qa sale rojo: la(s) tarea(s) afectadas vuelven a `implementer`, se corrigen y qa **re-ejecuta**. Contador explícito ("intento 2 de 3"). **Máximo 3 intentos**; si el 3.º sigue rojo, ANTES de parar ejecuta **UNA pasada de la skill `debug-root-cause`** (4 fases con evidencia: reproducción mínima → aislamiento → hipótesis probada → fix propuesto). Luego PARA y pregunta al usuario qué hacer — seguir con el fix propuesto, re-planificar con `planner`, o cancelar — presentando el **diagnóstico** (causa probada, o lo descartado + hipótesis vivas si no concluyó) junto a la salida de qa-gate de cada intento. El tiempo del diagnóstico se imputa como implementación de la tarea afectada. No cierres estados en rojo y no degrades el umbral para "pasar".

### Ciclo Jira de la Fase 3 (opt-in, `.claude/jira.json` `enabled: true`) — la secuencia, UNA sola vez

El estado del issue, los comentarios y las horas los produce **`jira-flow.py`** (skill `jira-sync`,
Paso 7): tú no redactas comentarios ni compones llamadas — el script devuelve `ops` (etiqueta →
transición → comentario → worklog) **ya firmadas por el agente** y en orden; ejecútalas seguidas con
las tools del conector y, **solo si todas respondieron bien**, ejecuta el comando `confirmar` que trae
el plan (con `--comentario-id` del comentario creado): sin confirmar, el evento sigue pendiente y el
siguiente plan avisa de buscar su referencia en el issue antes de publicar. Una llamada por evento y tarea (con granularidad `fase`, `--batch` agrupa las
tareas de la fase en un comentario). El **ledger sigue siendo la fuente**; Jira es espejo.

| Evento | Cuándo | Quién lo dispara | Transición | Comentario (firma) | Worklog |
|---|---|---|---|---|---|
| `arrancar` | al abrir `T-XX` | `implementer` | → *En curso* | — | — |
| `implementado` | criterios cumplidos | `implementer` | *(sigue En curso)* | `ca-implementer`: qué hizo, evidencia, ficheros | implementación (horas medidas) |
| `revision` | cierre de intento sin gaps | `adversarial-review` (su paso 6, por intento; **no** el orquestador ni `reviewer`) | — | `ca-reviewer`: veredicto por criterio | `[revisión] --attempt N` |
| `gaps` | cierre de intento con gaps | `adversarial-review` (su paso 6, por intento; **no** el orquestador ni `reviewer`) | → *En curso* (reabre) | `ca-reviewer`: gaps graduados | `[revisión] --attempt N` |
| `qa-verde` / `qa-rojo` | veredicto de `qa-gate.py` | `qa` | — | `ca-qa`: X/Y del gate + evidencias | — |
| `aprobado` | revisión sin gaps **y** qa verde | **el orquestador (tú)**, `--actor orquestador --qa-verde` | → *Done* | `ca-orquestador`: cierre con la evidencia | — |

**`aprobado` es TUYO y con evidencia (no a ciegas).** `jira-flow.py` lo rechaza (exit 2, `ops: []`,
con la razón) si el ledger no tiene una última sección `## Revisión de dos lentes — intento N` sin
gaps pendientes para esas tareas, o si no le pasas `--qa-verde` — flag que pasas **solo tras leer el
exit 0 de `agent-kits/qa/qa-gate.py`**, nunca por el resumen de `qa`. Es el único evento que ve los
dos veredictos, y por eso el único que puede cerrar el issue.

**Cómo se entera el `implementer` de los gaps:** por su **brief** (`task-brief.py` inyecta los gaps
del último intento desde el ledger), no por Jira — el comentario `gaps` es el espejo para el equipo.
Sin Jira activado, el ciclo es idéntico salvo que no se publica nada: el script lee
`.claude/jira.json` y con `enabled` ≠ `true` devuelve `ops: []` y `jira: "desactivado"` (exit 0, sin
ruido). Reejecutar una fase tampoco duplica: cada plan con `ops` queda anotado en `jira-state.json`
(`flow[...]`) y repetir el mismo evento da `ops: []` + `yaRealizado: true` (`--force` para repetirlo
a propósito). En `revision`/`gaps`, `--intento N` es obligatorio.

Al salir debes tener: código implementado, revisión pasada, `qa-gate` en verde y `tasks.md` al día (validado con `ledger-lint.py`).

## Fase 4 — Documentar (siempre, agente `documenter`)
Con las pruebas en verde, invoca **`documenter`** para generar/actualizar la documentación del proyecto (una vez al final, no por tarea).

## Fase 4-bis — Knowledge Gate (siempre tras QA verde y `documenter`, agente `knowledge-curator`)
Tras cerrar la Fase 4, comprueba los candidatos de la iniciativa bajo
`docs/knowledge/candidates/{pending,needs_changes}/`: pueden proceder de architect,
planner, implementer, qa, documenter, debug-root-cause, el usuario o el puente de casos,
siempre propuestos mediante `knowledge-curation.py`. `rejected/` es terminal y no dispara
esta fase. Si hay alguno pendiente, invoca **knowledge-curator** para juzgar categoría
exacta, evidencia, fuentes, tags, lista negra y contradicciones con approved y legado
aceptado pertinente; las de alto impacto o contradictorias requieren resolución humana.

- **Handoff y retoma.** Como dueño del ledger, registra las rutas candidate/SHA
  explícitas devueltas por propose en el único bloque de `knowledge-write.md`
  antes de entregar propuestas a apply. Conserva los handoffs de design al pasar
  por planner. Tras apply/recover, incorpora sólo el operation-id real devuelto
  por Curator; sin recibo mantiene pendiente. No infieras identidades ni cambies
  asociaciones conflictivas. Las propuestas tardías de retro usan el mismo
  handoff; productores, Curator y servicio no ganan permisos sobre roadmap.
- **Persistencia única.** `curator-gate.py` conserva evaluación readonly y códigos;
  Curator aplica por `knowledge-curation.py` con SHA esperado, motivo e ID final obligatorio
  al aprobar. El servicio persiste los bytes; el rol no escribe, mueve o borra memoria
  manualmente ni promueve ADR/GOT/LES legacy. Sin servicio o recibo completo, deja ruta/ID
  u operation-id y estado pendiente visibles, sin fallback Write/Edit.
- **Omisión honesta.** Sin candidatos, di una línea ("sin candidatos de conocimiento que curar")
  y continúa a Fase 5. No es un gap ni bloquea el cierre. Una propuesta que no pudo persistirse
  se informa como tal; no se presenta como ausencia de propuestas.
- **Kwipu/Graphiti nunca condicionan el cierre.** El servicio deja approved correcto y
  Curator muestra el recibo o una operación pendiente explícita. La exportación por
  `knowledge-sync.py` sigue asíncrona y reconstruible; su fallo se anota y no detiene el ciclo.
- **Handoff tardío de retro.** La retro de Fase 6 ocurre después de este Gate: sus propuestas
  entregan un handoff explícito al Curator o quedan con ruta/ID y pending visibles.
  QA, revisión y cierre de retro no aprueban memoria; accepted legacy no equivale a approved.
- Curator y el servicio no tocan roadmap ni código del proyecto; el orquestador
  conserva únicamente el handoff explícito en su ledger. El servicio sólo persiste memoria.

## Fase 5 — Seguridad (opcional, agente `nemesis`)
Si el usuario lo pide o la iniciativa lo amerita, invoca **`nemesis`** para auditar la seguridad de lo construido (solo entornos locales/privados).

## Fase 6 — Sincronizar y cerrar

**Ritual de cierre de rama (obligatorio, en orden):**

1. **Verificación final sobre la rama**: suites y lint del proyecto en verde (las mismas comprobaciones de P5 del implementer, una última vez sobre el estado final).
2. **Commits ordenados**: un commit lógico por tarea (`T-XX: …`), sin restos de instrumentación temporal (logs/asserts de diagnóstico fuera del diff — regla de `debug-root-cause`). Conserva la puerta de alcance del ledger y elige una lista de archivos relativos exactos. Usa `agent-kits/shared/commit-selection.py` desde el `$SHAREDKIT` ya resuelto: `preview --root <proyecto> --path <archivo>` (repite `--path`), muestra selección, patch, cambios no seleccionados y staging ajeno, y conserva el JSON fuera de Git. Para archivos nuevos, registra explícitamente sólo los elegidos con intent-to-add antes del preview. No atribuyas al ciclo el staging previo de un archivo seleccionado: un conflicto deja ese contenido intacto. Revalida el JSON por stdin con `validate --root <proyecto>` inmediatamente antes del commit; sólo exit 0 habilita `git --literal-pathspecs commit --only --pathspec-from-file=- --pathspec-file-nul -m <mensaje>` con la lista revisada UTF-8/NUL por stdin. Comprueba después árbol/blobs/modos y conservación del staging ajeno; una discrepancia se informa, sin reescritura automática. Sin helper o con error, queda pendiente el commit y continúa el trabajo permitido; no se sustituye por staging global. Detalle y límites: [selección de commits](../docs/COMMIT-SELECTION.md). Esto no autoriza push, merge, PR ni release por sí mismo.
3. **Resumen de merge/PR derivado del LEDGER** (no de memoria): título, qué se hizo tarea a tarea, criterios de aceptación cumplidos, veredicto de qa-gate y ruta de las evidencias. Es la descripción del PR o el mensaje del merge.
4. **Integración según el flujo del repo**: merge directo o PR — si no está claro cuál usa el equipo, **pregunta**; no mergees por defecto.
5. **Limpieza**: rama integrada eliminada; worktrees retirados (`git worktree remove` + `prune`); marcadores de usage-meter sin huérfanos (`usage-meter.py status` limpio).
6. **Estados del plan**: plan/tasks → `completado` (lo exigen `changelog-sync` y la retro) y fila del índice del roadmap al día con ese estado. La spec **todavía no**: pasa a `implementada` en el paso 9, solo con la puerta del paso 8 abierta.
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
