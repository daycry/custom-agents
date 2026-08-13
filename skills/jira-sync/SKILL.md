---
name: jira-sync
description: >
  Vuelca un plan (tasks.md de docs/roadmap/<fecha>-<slug>/) a Jira creando issues,
  vía el conector oficial de Atlassian (Rovo MCP). Se ofrece al CREAR el plan
  (opt-in). Asistente guiado para elegir destino: en Cowork/escritorio abre un
  ARTEFACTO interactivo (buscar proyecto / buscar issue padre por clave, texto o
  JQL); en CLI o VS Code hace lo mismo de forma CONVERSACIONAL (por texto, eligiendo
  por número). Determina el tipo de issue según la jerarquía del padre (no lo
  hardcodea), comprueba campos obligatorios, PREVISUALIZA y pide confirmación antes
  de crear nada, es idempotente (no duplica) y escribe las claves Jira de vuelta en
  tasks.md. Úsala cuando el usuario diga "vuelca el plan a Jira", "crea las tareas
  en Jira", "sincroniza el plan con Jira", "pásame esto a Jira".
user-invokable: true
---

# jira-sync — volcar el plan a Jira (con artefacto o conversacional)

Convierte las tareas de un plan (`docs/roadmap/<fecha>-<slug>/tasks.md`) en **issues de Jira**,
usando el **conector oficial de Atlassian (Rovo MCP)** — sin integración propia. Se ofrece **al
crear el plan** y es **opt-in**: si el usuario no quiere, no se hace nada.

**Pensada para no técnicos.** Una pregunta a la vez, lenguaje llano, **previsualiza y confirma
antes de crear**. Nada se escribe en Jira sin un "sí" explícito.

## Requisitos

- **Conector Atlassian (Rovo MCP) conectado** con permiso de escritura (`write:jira-work`). Si no
  lo está, dilo en llano ("Necesito conectarme a vuestro Jira; actívalo en los conectores y
  volvemos") y **detente**.
- Herramientas del conector (por su función; el prefijo `mcp__…__` puede variar):
  `getAccessibleAtlassianResources`, `getVisibleJiraProjects`, `searchJiraIssuesUsingJql`,
  `getJiraProjectIssueTypesMetadata`, `getJiraIssueTypeMetaWithFields`, `createJiraIssue`,
  `getJiraIssue`, `editJiraIssue` (checklist de la descripción en modo fase), y para la
  sincronización de progreso `addWorklogToJiraIssue`, `addCommentToJiraIssue` (comentarios de
  progreso y de revisión), `getTransitionsForJiraIssue`, `transitionJiraIssue`.
- Un plan existente: `docs/roadmap/<fecha>-<slug>/tasks.md` (tareas `T-XX`).

## Paso 0 — opt-in y conexión

1. Localiza la config y respeta el flag `enabled`:
   ```bash
   JCFG="$(find "$PWD/.claude" "$HOME/.claude" -type f -path '*jira.json' 2>/dev/null | head -1)"
   ```
   - `enabled: false` → no hagas nada. Sin config (primera vez) → pregunta **una vez**: "¿Quieres volcar los planes a Jira?"; guarda la decisión en `.claude/jira.json`.
2. Comprueba conexión con `getAccessibleAtlassianResources`; si no está, guía a conectarla y detente. Resuelve el `cloudId` (uno solo → úsalo; varios → pregunta por nombre) y persístelo.

## Paso 0-bis — granularidad del volcado (por TAREA o por FASE)

Antes de crear nada, decide la **granularidad** (campo `granularidad` en `.claude/jira.json`):

- **`tarea`** (por defecto): un issue de Jira **por cada `T-XX`** del plan. Es el comportamiento clásico; no rompe instalaciones existentes.
- **`fase`**: un issue **por cada Fase** del plan, con las `T-XX` de esa fase como **checklist** en la descripción del issue.

Si `granularidad` no está en `.claude/jira.json`, **pregunta una vez** ("¿Un issue por tarea, o uno por fase con sus tareas dentro?"; en Cowork puede ir en el mismo artefacto del Paso 1, en CLI conversacional) y **persiste** la decisión. A partir de aquí, cada paso indica su comportamiento **[modo tarea]** / **[modo fase]**.

> **Cambiar de granularidad con issues ya creados:** si el manifiesto ya tiene claves del otro modo (`T-XX → …` vs `fase-N → …`), **avisa** del choque y ofrece continuar en el modo ya volcado o empezar limpio (carpeta nueva o borrar el manifiesto). **Nunca** dupliques en silencio.

## Paso 1 — elegir destino (proyecto + padre opcional)

Resultado buscado, sea cual sea el modo: **`{ projectKey, parentKey|null }`**.

**Detecta el entorno primero:**

### Paso 1-A — artefacto (Cowork / escritorio)
Si la herramienta de crear artefactos está disponible:
1. Localiza la plantilla sin depender del scope:
   ```bash
   TPL="$(find "$PWD/.claude" "$HOME/.claude" -type f -path '*skills/jira-sync/assets/jira-picker.template.html' 2>/dev/null | head -1)"
   ```
2. Copia la plantilla y sustituye `{{SERVER_PROJECTS}}` (nombre completo `mcp__<uuid>__getVisibleJiraProjects`), `{{SERVER_SEARCH}}` (`mcp__<uuid>__searchJiraIssuesUsingJql`) y `{{CLOUD_ID}}`.
3. Publícala con `create_artifact` (con `mcp_tools=[getVisibleJiraProjects, searchJiraIssuesUsingJql]`). El artefacto busca proyectos, resuelve claves/URLs de issue directas y busca padre por clave/texto/JQL en vivo.
4. Cuando el usuario elija, lee `window.__dest = {projectKey, projectName, parentKey, parentSummary}` y continúa.

### Paso 1-B — conversacional (CLI / VS Code, sin artefactos)
Mismo resultado, en texto (no intentes `create_artifact`):
1. **Proyecto:** pide un término y llama `getVisibleJiraProjects` (`action:"create"`, `searchString`, `maxResults` pequeño). Muestra los resultados **numerados por clave y nombre**; el usuario elige uno. (Si el usuario ya da una clave/URL de issue, ve directo al padre.)
2. **Padre:** ofrece: (a) **sin padre** (crear en la raíz del proyecto), o (b) indicar un **issue padre**. Para (b) acepta **clave** (`DM5985-59`), **texto** o **JQL**; construye la JQL **acotada al proyecto** (`project = "KEY" AND (…)`, salvo `key = X` que es global) — el conector **exige** `searchResultMode:"issues"` y **rechaza** JQL sin restricción. Lista los resultados numerados y el usuario elige.

En ambos modos, **no hardcodees la forma de buscar el padre**: clave exacta → `key = X`; texto → `summary ~ "…"`; expresión JQL → tal cual (acotada al proyecto).

## Paso 2 — decidir el TIPO de issue (según la jerarquía del padre, descubierto)

Los nombres de tipo varían por instancia/idioma (Tarea/Historia/Subtarea/Epic/Iniciativa, o
Task/Story/Sub-task…). **No los hardcodees**: descúbrelos con
`getJiraProjectIssueTypesMetadata(projectKey)` y decide por `hierarchyLevel` + `subtask`:

- **Sin padre** → un tipo **nivel 0** no-subtarea (preferir `untranslatedName` `Task`, luego `Story`; si no, el primer nivel 0 no-subtarea). Se crea en la raíz del proyecto.
- **Padre nivel ≥ 1** (Epic/Iniciativa) → tipo **nivel 0** no-subtarea, con `parent` = la clave del padre.
- **Padre nivel 0** (Tarea/Historia) → tipo **subtarea** (`subtask:true`, nivel −1), con `parent` = la clave del padre. Una Tarea **no** puede ser padre de otra Tarea; por eso los hijos son subtareas.

Para saber el nivel del padre, léelo con `getJiraIssue(parentKey)` (campo `issuetype.hierarchyLevel`)
o a partir de los metadatos del proyecto.

## Paso 3 — comprobar campos obligatorios (evitar fallos al crear)

Antes de crear, llama `getJiraIssueTypeMetaWithFields(projectKey, issueTypeId, requiredFieldsOnly:true)`
para el tipo elegido. Los normales que siempre pondrás son `project`, `issuetype`, `summary` y, si
hay padre, `parent`. **Si hay algún campo obligatorio adicional sin valor por defecto** (p. ej. un
custom field), **pregúntalo al usuario** una vez y pásalo en `additional_fields`; no lo inventes ni
falles en silencio.

> **Comportamientos del conector**: los hechos verificados (searchResultMode, `issues.nodes`, JQL
> acotada, jerarquía por `hierarchyLevel`, campos obligatorios) están centralizados en
> `docs/atlassian-connector-notes.md` del plugin. Ante cualquier duda o error del conector, consulta ahí.

## Paso 4 — previsualizar y CONFIRMAR (obligatorio) — la previsualización ES un dry-run

La previsualización se construye con **verificaciones reales de solo lectura** (no de memoria):
tipos del proyecto (`getJiraProjectIssueTypesMetadata`), nivel del padre (`getJiraIssue`) y campos
obligatorios (`getJiraIssueTypeMetaWithFields`). Si el usuario pide "simúlalo" / "sin crear nada",
detente tras este paso y entrega el informe de lo que se crearía (n.º de issues, tipo, dónde,
campos) — ese es el modo **dry-run** de primera clase.

Muestra un resumen humano y **espera "sí"** antes de crear nada:

> "Voy a crear en Jira, en **DM5985** › bajo **DM5985-59**:
> • **6 Subtareas** (una por tarea del plan): T-01 «…», T-02 «…», …
> ¿Las creo? [Sí / Cambiar destino / Cancelar]"

Indica claramente **cuántos** issues, de **qué tipo** y **dónde** cuelgan.

## Paso 5 — crear (idempotente)

**[modo tarea]** Con el "sí", por cada tarea `T-XX` de `tasks.md`:
- `createJiraIssue(projectKey, issueTypeName, summary, description, parent?)`:
  - `summary` = `"T-XX · <título de la tarea>"`.
  - `description` = detalle/criterios de aceptación de la tarea (formato markdown) **+ enlace de vuelta** a la iniciativa (`docs/roadmap/<fecha>-<slug>/`) para no perder el contexto.
  - `parent` = la clave del padre (si aplica).
  - **Labels** (via `additional_fields`): `roadmap` y `<slug>` de la iniciativa, para poder filtrarla luego por JQL (`labels = "<slug>"`) — lo aprovecha el dashboard vivo desde Jira.
- **Idempotencia — manifiesto `.claude/jira-state.json`:** mapea `carpeta+T-XX → issueKey`. Antes de crear, consulta el manifiesto:
  - Ya tiene issueKey y existe (`getJiraIssue`) → **no dupliques** (salta o, si cambió el título, ofrece actualizar con `editJiraIssue`).
  - No está → crea y registra `T-XX → issueKey`.
- Muestra progreso ligero si son muchas ("Creando… 3 de 6").

**[modo fase]** Antes de agrupar, **valida el ledger** con el script compartido — un `tasks.md` mal formado (una `T-XX` fuera de fase, resumen descuadrado) crearía issues incorrectos:
```bash
LL="$(find "$PWD/.claude" "$HOME/.claude" -type f -path '*agent-kits/shared/ledger-lint.py' 2>/dev/null | head -1)"
python3 "$LL" "docs/roadmap/<fecha>-<slug>/tasks.md"   # exit 0 obligatorio para volcar en modo fase
```
Si da incoherencias duras, repórtalas y no vuelques hasta que el ledger esté limpio. Con el ledger en verde y el "sí", por cada **Fase** del plan (agrupa las `T-XX` por su fase leyendo `tasks.md`):
- `createJiraIssue(...)`:
  - `summary` = `"Fase N · <título de la fase>"`.
  - `description` = objetivo de la fase + **checklist de sus tareas** en markdown (`- [ ] T-XX · <título>` una por tarea) + enlace de vuelta a la iniciativa.
  - `parent`, tipo y labels igual que en modo tarea (el tipo se descubre por jerarquía, Paso 2).
- **Fase sin tareas → no se crea issue** (avísalo).
- **Idempotencia:** el manifiesto mapea `fase-N → issueKey`. Mismo criterio: si ya existe, no dupliques; si no, crea y registra `fase-N → issueKey`.
- Escribe la clave Jira en la **cabecera de cada fase** de `tasks.md` (Paso 6).

## Paso 6 — escribir de vuelta y cerrar

- En `tasks.md`, anota junto a cada `T-XX` su **clave Jira** (p. ej. una columna "Jira" o un sufijo `→ DM5985-123`). Si se usó un padre/épica, anótalo en `improvement-plan.md`.
- Actualiza `.claude/jira-state.json`.
- Cierra en llano con el recuento y **enlaces clicables**: "Creé 6 subtareas bajo DM5985-59. Aquí las tienes: <URLs>."

## Paso 7 — sincronizar progreso: imputar horas + marcar Done

Cuando una tarea `T-XX` pasa a **`completado`** en `tasks.md` (lo marca `implementer`, `qa` o el
chat), refleja ese avance en su issue de Jira. Se invoca **por tarea completada**, no al final.

> **El cálculo NO se hace a mano: usa el script probado del kit.** Toda la aritmética (real→est,
> ratio de supervisión, tope diario, banco por issue, re-banco) vive en
> `scripts/worklog.py` y devuelve JSON. Tú orquestas: llamas al script, aplicas su salida en Jira
> y confirmas con `--apply`. Localízalo:
> ```bash
> WL="$(find "$PWD/.claude" "$HOME/.claude" -type f -path '*skills/jira-sync/scripts/worklog.py' 2>/dev/null | head -1)"
> # cuánto imputar hoy (y qué banca):   python3 "$WL" plan --task T-08 --issue KEY --ia-real 4 --sup-real 1
> # entrada de revisión (C-07, acumulativa): añade --kind revision  (por defecto: implementacion)
> # si sale requiereDecision: pregunta al usuario y reejecuta con --policy <parar|seguir|banco>
> # tras registrar el worklog en Jira:  el MISMO comando con --apply (persiste el estado)
> # al empezar el día / retomar:        python3 "$WL" drain            (banco → pagos de hoy por issue) y --apply tras imputarlos
> # vista rápida:                       python3 "$WL" status
> ```

> **[modo fase] Dónde va cada cosa.** El issue objetivo de una tarea `T-XX` es el de **su fase** (`fase-N → issueKey` en el manifiesto), no uno propio. Al completar cada `T-XX`: (a) añade un **comentario** en el issue de la fase (tarea, evidencia, horas); (b) marca `- [x]` esa tarea en la **checklist de la descripción** del issue (`editJiraIssue`); (c) imputa su worklog al issue de la fase (abajo). El issue de la fase pasa a **Done** solo cuando **todas** sus tareas están `completado` en `tasks.md`. El resto del cálculo (worklog, tope, banco) es idéntico; solo cambia el `issueKey` destino.

1. **Localiza el issue**: **[modo tarea]** `T-XX → issueKey`; **[modo fase]** el de su fase (`fase-N → issueKey`). Si no está mapeado (no se volcó), no hagas nada.
2. **Calcula el worklog (tiempo de producción)** — con `worklog.py plan` (regla que implementa):
   - `horas = Tiempo IA (ejec.) + Supervisión`, tomando el valor **real** de cada uno; si un `real` falta, usa su **estimación**. Si además falta la supervisión, derívala como `Tiempo IA × ratioSupervision` (por defecto `0.25`).
   - **De dónde sale el "real" del tiempo IA:** si la tarea se ejecutó en `/dev-cycle` Modo B con medición por tarea (iniciativa coste-generacion), el real viene **medido** (`usage-meter.py`: tokens reales × ratio calibrado; marcado `(medido)` en `tasks.md`) — es el valor preferente. Si no hay medición, el real es el que anote el implementador a juicio, y si tampoco, cae a la estimación (regla anterior). La aritmética de jornada/banco no cambia en ningún caso.
   - **Fallback**: si la tarea no tiene tiempo IA (tarea puramente humana), usa el **tiempo humano** (real→est).
   - El **+20 % de contingencia no se imputa** (es margen de presupuesto, no tiempo real).
   - El **tope de jornada es DIARIO** (acumulado de todas las tareas del día), no por tarea. Antes de imputar, aplica el "Tope de jornada diario" de abajo.
3. **Imputa** con `addWorklogToJiraIssue` (issueKey, `timeSpent` en horas/minutos, con un comentario tipo "Imputado automáticamente al completar T-XX"). Opcional: anota el **tiempo IA** por separado en un comentario/label para reporting.
4. **Marca Done (descubierto, no hardcodeado):** `getTransitionsForJiraIssue(issueKey)` → localiza la transición cuyo estado destino es de categoría *Done* (o el nombre configurado) y aplícala con `transitionJiraIssue`. Si hay varias o ninguna clara, pregunta/omite con aviso; no fuerces un id fijo.
5. **Actualiza** el manifiesto (`T-XX → {issueKey, worklogImputado, done:true}`) para no re-imputar en reejecuciones (idempotente).

### Tope de jornada diario (banco de horas)

El **acumulado de horas imputadas por día** no debe pasar de `horasJornada` (por defecto 8; 7 en
periodos intensivos). Lleva ese acumulado por fecha en `.claude/jira-state.json`
(`imputadoPorDia: { "YYYY-MM-DD": 6.5 }`). Antes de imputar el worklog de una tarea:

- Calcula `restante = horasJornada − imputado_hoy`.
- **Si cabe** (`horas ≤ restante`): imputa normal y suma al acumulado del día.
- **Si NO cabe** (superaría la jornada): aplica la preferencia `alCubrirJornada` de `.claude/jira.json`:
  - **`preguntar`** (por defecto): para y ofrece las **tres** opciones; actúa según la respuesta y ofrece **recordarla** (guardarla en `alCubrirJornada` para no volver a preguntar):
    1. **Parar** — imputa solo `restante` (hasta cubrir la jornada) y **detén la implementación**; informa de cuántas horas y tareas quedan pendientes. (El `implementer` debe respetar esta parada.)
    2. **Seguir imputando** — imputa las `horas` completas aunque el día supere la jornada.
    3. **Banco (día siguiente)** — imputa `restante` hoy (hasta cubrir la jornada) y **guarda el exceso** en `bancoHoras` como una **entrada con su tarea e issue** (`{ task:"T-XX", issueKey:"…", horas, origen }`); sigue implementando. El excedente **no** se imputa hoy: queda pendiente para una jornada posterior, y sabe **a qué issue** imputarse.
  - Si `alCubrirJornada` ya tiene un valor (`parar`/`seguir`/`banco`), aplícalo sin preguntar.

> **Ejemplo (banco).** Llevas 6 h imputadas hoy y una tarea consume 3 h (tope 8 h): imputa **2 h hoy** (llegas a 8 h) y guarda **1 h** en el banco. Esa 1 h **no** se registra hoy con fecha de mañana.

- **Solo se imputan horas del día en curso.** Todo worklog se registra con la **fecha de hoy** (la real); **nunca** se post-datan horas a días futuros. Por eso el banco no se imputa por adelantado: cada entrada del banco se imputa **a su `issueKey`** cuando ese día posterior sea realmente *hoy* (en una ejecución de ese día), consumiendo el presupuesto de esa jornada. Si una entrada no cabe entera, imputa lo que quepa a su issue y **re-banca el resto de esa misma entrada**. Así, en Jira, cada día solo lleva horas registradas ese mismo día y nunca más de `horasJornada`, y cada hora va a la tarea que le corresponde.

> Igual que el volcado, esto es **opt-in**: solo ocurre si `.claude/jira.json` tiene `enabled: true`. Aunque el conector esté conectado, si no se ha activado Jira para el proyecto, no se imputa ni se transiciona nada.

## Paso 8 — traer estado desde Jira (read-back, opcional)

Sentido inverso del volcado, para no perder de vista lo que el equipo mueve en Jira. Se invoca a
demanda ("trae el estado de Jira", "sincroniza el estado desde Jira") o al **retomar** un plan.
`tasks.md` es el **ledger canónico**: Jira es espejo, así que el read-back **informa** y solo
actualiza `tasks.md` con confirmación.

1. **[modo tarea]** Para cada `T-XX → issueKey`, lee el issue con `getJiraIssue` (`status` y categoría). **[modo fase]** Para cada `fase-N → issueKey`, lee el issue de la fase y compáralo con el **agregado** de sus tareas en `tasks.md` (la fase está *Done* ⟺ todas sus `T-XX` `completado`).
2. Compara el estado del issue con el de la tarea/fase en `tasks.md` (mapa aproximado: categoría *Done* ↔ `completado`; *In Progress* ↔ `en-progreso`; *To Do* ↔ `borrador`/`en-progreso`).
3. **Clasifica y muestra** las divergencias, sin tocar nada aún:
   - Issue *Done* en Jira pero tarea no `completado` en `tasks.md` (alguien la cerró en Jira).
   - Tarea `completado` en `tasks.md` pero issue abierto en Jira (no se sincronizó el cierre; ver Paso 7).
   - Coinciden → nada que hacer.
4. **Con confirmación**, aplica los cambios acordados en `tasks.md` (y su resumen de progreso). Nunca sobreescribas el ledger en silencio; ante duda, deja la divergencia listada para que el usuario decida.
5. No imputa horas en el read-back (eso es del Paso 7, al completar la tarea desde la implementación).

> Es **opt-in** como el resto: solo si `.claude/jira.json` `enabled: true`. Útil al reabrir una iniciativa (`/dev-cycle` sobre una carpeta existente) para alinear `tasks.md` con lo que haya pasado en Jira entretanto.

## Paso 9 — publicar el resultado del revisor (comentario + worklog `[revisión]`)

El agente **revisor** (revisión adversarial de dos lentes de `/dev-cycle` Modo B, iniciativa `qa-strict`) produce, tras su **bucle acotado a 3 intentos** con `implementer`, un resultado **estructurado por criterio** (`T-XX` → criterio → ✓/✗ + gaps + nº de intentos + tiempo de revisión). Este paso lo lleva a Jira. Lo invoca el orquestador `/dev-cycle` (o `implementer` al cerrar), **solo en Modo B** (en Modo A el motor externo revisa con otro formato → no aplica).

1. **Localiza la plantilla fija** del comentario y renderiza el resultado del revisor contra ella (formato idéntico siempre):
   ```bash
   RT="$(find "$PWD/.claude" "$HOME/.claude" -type f -path '*agent-kits/shared/review-report.template.md' 2>/dev/null | head -1)"
   ```
   Si el revisor devolvió prosa sin la estructura por criterio, **no inventes ✓/✗**: publica solo el resumen + gaps y deja constancia del aviso.
2. **Publica el comentario** con `addCommentToJiraIssue`, con la **granularidad del volcado**:
   - **[modo tarea]** un comentario en el issue de cada `T-XX` revisada.
   - **[modo fase]** un **único** comentario en el issue de la fase, al cerrarla, agregando el pasa/falla por criterio de **todas** sus tareas.
   - El comentario refleja el **resultado FINAL** (tras el bucle) e incluye la línea *"revisión superada en N intento(s)"*. **No** publiques un comentario por intento.
3. **Imputa el worklog de revisión POR INTENTO** con `worklog.py plan --kind revision --attempt N`: **cada pasada del bucle es su propia entrada de worklog** (con su duración y su fecha en Jira, comentario tipo `"[revisión] intento N de 3 — T-XX"`), de modo que quede la traza de cuánto costó cada vuelta. El script acumula el total en `worklogRevision` (aparte de `worklogImpl`) y registra `reviewAttempts: [{intento, fecha, horas}]` para `/retro`; todo suma al total del issue y respeta el tope de jornada y el banco:
   ```bash
   # [modo tarea] la revisión de cada tarea se registra bajo su propia T-XX (una llamada POR intento):
   python3 "$WL" plan --task T-XX      --issue <issueKey_tarea> --kind revision --attempt 1 --ia-real <h_intento1> --apply
   python3 "$WL" plan --task T-XX      --issue <issueKey_tarea> --kind revision --attempt 2 --ia-real <h_intento2> --apply
   # [modo fase] revisión agregada de la fase → clave sintética rev-fase-N (issue destino = el de la fase):
   python3 "$WL" plan --task rev-fase-N --issue <issueKey_fase>  --kind revision --attempt N --ia-real <h> --apply
   ```
   La clave sintética `rev-fase-N` evita pisar el registro de una `T-XX` real; el issue destino sigue siendo el de la fase. Las horas por intento son las estimadas/reales del bloque de trabajo (como el resto de imputaciones del plugin), no un cronómetro; el "cuándo" de cada intento lo da la fecha de su entrada de worklog.
4. **Idempotencia:** marca en `.claude/jira-state.json` `reviewComentado` por `T-XX`/`fase-N` para no re-comentar ni re-imputar la revisión en reejecuciones.

> Las **correcciones** que hace el `implementer` durante el bucle son tiempo de **implementación**: van a la entrada normal (`--kind implementacion`, la de por defecto), no a `[revisión]`. Así el total del issue = implementación + revisión, con el desglose intacto para `/retro`.

## Config `.claude/jira.json` (gestión interna, editable)

La escribe/actualiza la skill; el usuario puede ajustarla. Campos:

- `enabled` (`true`/`false`) — opt-in del proyecto (como Confluence).
- `granularidad` (`"tarea"` por defecto · `"fase"`) — un issue por tarea, o uno por fase con sus tareas como checklist (Paso 0-bis). Si falta, se pregunta una vez y se persiste.
- `cloudId` — site Atlassian (se resuelve solo si falta).
- `horasJornada` — **máximo de horas imputables por DÍA** (acumulado de todas las tareas), no por tarea; `8` por defecto, `7` en jornada intensiva. **Se lee de `.claude/rates.json`** (config compartida); `jira.json` solo lo sobreescribe si quieres un valor distinto para Jira.
- `alCubrirJornada` (por defecto `preguntar`) — qué hacer al llegar al tope diario: `preguntar` · `parar` · `seguir` · `banco`. Ver "Tope de jornada diario". (Específico de Jira → vive en `jira.json`.)
- `ratioSupervision` — para derivar la supervisión cuando no viene como `real`; también **de `.claude/rates.json`** (`0.25` por defecto).
- `defaults` (opcional) — `projectKey`, `parentKey`, `issueType`, `labels` para repetir de un clic.

Estado en `.claude/jira-state.json`: el **mapeo `T-XX → issueKey`** (modo tarea) o **`fase-N → issueKey`** (modo fase; el valor se anota en la cabecera de la fase de `tasks.md`, Paso 6), `imputadoPorDia` (horas imputadas por fecha), `bancoHoras` — lista de entradas por tarea/issue con su `kind` (`implementacion`/`revision`), p. ej. `[{ "task":"T-08", "issueKey":"DM5985-123", "horas":1, "origen":"2026-07-15", "kind":"implementacion" }]` — y, por tarea, el **desglose** `worklogImpl` / `worklogRevision` y el flag `reviewComentado` (para no re-publicar la revisión).

## Reglas

- **Opt-in y confirmación:** nunca creas en Jira sin que el proyecto lo haya activado y sin un "sí" a la previsualización.
- **Doble modo:** artefacto en Cowork/escritorio; conversacional en CLI/VS Code. Mismo resultado (`{projectKey, parentKey}`); no dependas de que exista el host de artefactos.
- **No hardcodees tipos ni búsquedas:** descubre los tipos por jerarquía; construye la JQL acotada al proyecto; `searchResultMode:"issues"` siempre.
- **Payloads mínimos (ahorro de tokens):** en toda llamada al conector (`searchJiraIssuesUsingJql`, `getJiraIssue`…) pide **solo los campos que vas a usar** con `fields:[…]` (p. ej. `["summary","status","issuetype","parent"]` al buscar padre; `["summary","status","timetracking","aggregatetimespent"]` al leer progreso) y acota `maxResults` (p. ej. 25-50) en vez de traer la respuesta completa por defecto, que es enorme. Nunca pidas "todos los campos" salvo que de verdad los necesites; si falta uno, añádelo a la lista explícita.
- **Idempotente:** el manifiesto evita duplicados al reejecutar. `tasks.md` sigue siendo el ledger canónico del progreso; Jira es un espejo para el equipo.
- **Errores en llano:** sin conexión / sin permiso / campo obligatorio inesperado / issue padre inválido → una frase clara y el siguiente paso, no un volcado técnico.
- **Solo el plan indicado:** trabaja sobre la carpeta `docs/roadmap/<fecha>-<slug>/` en curso; no toques otras iniciativas.
