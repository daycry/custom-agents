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
  `getJiraIssue`, y para la sincronización de progreso `addWorklogToJiraIssue`,
  `getTransitionsForJiraIssue`, `transitionJiraIssue`.
- Un plan existente: `docs/roadmap/<fecha>-<slug>/tasks.md` (tareas `T-XX`).

## Paso 0 — opt-in y conexión

1. Localiza la config y respeta el flag `enabled`:
   ```bash
   JCFG="$(find "$PWD/.claude" "$HOME/.claude" -type f -path '*jira.json' 2>/dev/null | head -1)"
   ```
   - `enabled: false` → no hagas nada. Sin config (primera vez) → pregunta **una vez**: "¿Quieres volcar los planes a Jira?"; guarda la decisión en `.claude/jira.json`.
2. Comprueba conexión con `getAccessibleAtlassianResources`; si no está, guía a conectarla y detente. Resuelve el `cloudId` (uno solo → úsalo; varios → pregunta por nombre) y persístelo.

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

## Paso 4 — previsualizar y CONFIRMAR (obligatorio)

Muestra un resumen humano y **espera "sí"** antes de crear nada:

> "Voy a crear en Jira, en **DM5985** › bajo **DM5985-59**:
> • **6 Subtareas** (una por tarea del plan): T-01 «…», T-02 «…», …
> ¿Las creo? [Sí / Cambiar destino / Cancelar]"

Indica claramente **cuántos** issues, de **qué tipo** y **dónde** cuelgan.

## Paso 5 — crear (idempotente)

Con el "sí", por cada tarea `T-XX` de `tasks.md`:
- `createJiraIssue(projectKey, issueTypeName, summary, description, parent?)`:
  - `summary` = `"T-XX · <título de la tarea>"`.
  - `description` = detalle/criterios de aceptación de la tarea (formato markdown).
  - `parent` = la clave del padre (si aplica).
- **Idempotencia — manifiesto `.claude/jira-state.json`:** mapea `carpeta+T-XX → issueKey`. Antes de crear, consulta el manifiesto:
  - Ya tiene issueKey y existe (`getJiraIssue`) → **no dupliques** (salta o, si cambió el título, ofrece actualizar con `editJiraIssue`).
  - No está → crea y registra `T-XX → issueKey`.
- Muestra progreso ligero si son muchas ("Creando… 3 de 6").

## Paso 6 — escribir de vuelta y cerrar

- En `tasks.md`, anota junto a cada `T-XX` su **clave Jira** (p. ej. una columna "Jira" o un sufijo `→ DM5985-123`). Si se usó un padre/épica, anótalo en `improvement-plan.md`.
- Actualiza `.claude/jira-state.json`.
- Cierra en llano con el recuento y **enlaces clicables**: "Creé 6 subtareas bajo DM5985-59. Aquí las tienes: <URLs>."

## Paso 7 — sincronizar progreso: imputar horas + marcar Done

Cuando una tarea `T-XX` pasa a **`completado`** en `tasks.md` (lo marca `implementer`, `qa` o el
chat), refleja ese avance en su issue de Jira. Se invoca **por tarea completada**, no al final.

1. **Localiza el issue** de la tarea en el manifiesto `.claude/jira-state.json` (`T-XX → issueKey`). Si no está mapeada (no se volcó a Jira), no hagas nada.
2. **Calcula el worklog (tiempo de producción):**
   - `horas = Tiempo IA (ejec.) + Supervisión`, tomando el valor **real** de cada uno; si un `real` falta, usa su **estimación**. Si además falta la supervisión, derívala como `Tiempo IA × ratioSupervision` (por defecto `0.25`).
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

## Config `.claude/jira.json` (gestión interna, editable)

La escribe/actualiza la skill; el usuario puede ajustarla. Campos:

- `enabled` (`true`/`false`) — opt-in del proyecto (como Confluence).
- `cloudId` — site Atlassian (se resuelve solo si falta).
- `horasJornada` (por defecto `8`) — **máximo de horas imputables por DÍA** (acumulado de todas las tareas), no por tarea; bájalo a `7` en periodos de jornada intensiva. Editable en cualquier momento; puedes pedir a la skill que lo confirme al arrancar.
- `alCubrirJornada` (por defecto `preguntar`) — qué hacer al llegar al tope diario: `preguntar` · `parar` · `seguir` · `banco`. Ver "Tope de jornada diario".
- `ratioSupervision` (por defecto `0.25`) — para derivar la supervisión cuando no viene como `real`.
- `defaults` (opcional) — `projectKey`, `parentKey`, `issueType`, `labels` para repetir de un clic.

Estado en `.claude/jira-state.json`: el **mapeo `T-XX → issueKey`** (clave Jira de cada tarea; el mismo valor se anota en `tasks.md`, Paso 6), `imputadoPorDia` (horas imputadas por fecha) y `bancoHoras` — una **lista de entradas por tarea/issue**, p. ej. `[{ "task":"T-08", "issueKey":"DM5985-123", "horas":1, "origen":"2026-07-15" }]` — para que cada excedente sepa a qué issue imputarse al drenarse.

## Reglas

- **Opt-in y confirmación:** nunca creas en Jira sin que el proyecto lo haya activado y sin un "sí" a la previsualización.
- **Doble modo:** artefacto en Cowork/escritorio; conversacional en CLI/VS Code. Mismo resultado (`{projectKey, parentKey}`); no dependas de que exista el host de artefactos.
- **No hardcodees tipos ni búsquedas:** descubre los tipos por jerarquía; construye la JQL acotada al proyecto; `searchResultMode:"issues"` siempre.
- **Idempotente:** el manifiesto evita duplicados al reejecutar. `tasks.md` sigue siendo el ledger canónico del progreso; Jira es un espejo para el equipo.
- **Errores en llano:** sin conexión / sin permiso / campo obligatorio inesperado / issue padre inválido → una frase clara y el siguiente paso, no un volcado técnico.
- **Solo el plan indicado:** trabaja sobre la carpeta `docs/roadmap/<fecha>-<slug>/` en curso; no toques otras iniciativas.
