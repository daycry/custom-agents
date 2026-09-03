# jira-sync — destino, tipo de issue, campos obligatorios y previsualización (Pasos 0-bis a 4)

> Referencia de la skill `jira-sync`. Léela **solo** cuando llegues al Paso 0-bis (granularidad) y hasta completar el Paso 4 (previsualización): contiene la casuística completa de esos pasos, literal. El flujo resumido vive en `SKILL.md`.

## Paso 0-bis — granularidad del volcado (por TAREA o por FASE)

Antes de crear nada, decide la **granularidad** (campo `granularidad` en `.claude/jira.json`):

- **`tarea`** (por defecto): un issue de Jira **por cada `T-XX`** del plan. Es el comportamiento clásico; no rompe instalaciones existentes.
- **`fase`**: un issue **por cada Fase** del plan, con las `T-XX` de esa fase como **checklist** en la descripción del issue.

Si `granularidad` no está en `.claude/jira.json`, **pregunta una vez** ("¿Un issue por tarea, o uno por fase con sus tareas dentro?"; en Cowork puede ir en el mismo artefacto del Paso 1, en CLI conversacional) y **persiste** la decisión. A partir de aquí, cada paso indica su comportamiento **[modo tarea]** / **[modo fase]**.

> **Cambiar de granularidad con issues ya creados:** si el manifiesto ya tiene claves del otro modo (`T-XX → …` vs `fase-N → …`), **avisa** del choque y ofrece continuar en el modo ya volcado o empezar limpio (carpeta nueva o borrar el manifiesto). **Nunca** dupliques en silencio.

## Paso 0-ter — asignación de los issues creados (`assignee`)

Algunos proyectos de Jira tienen "asignado por defecto" activo: un `createJiraIssue` sin
`assignee` explícito puede terminar auto-asignado a otra persona del equipo (con notificación),
según ese default del proyecto (verificado en dry-run, ver `docs/atlassian-connector-notes.md`).
Para no depender de ese comportamiento: si `assignee` no está en `.claude/jira.json`, **pregunta
una vez** ("¿Los issues que cree se asignan a ti, o los dejo sin asignar?") y **persiste** la
respuesta como `assignee: "me" | "none"` (defecto `"me"` si el usuario no tiene preferencia). En
el Paso 5, al crear, fija siempre el campo `assignee` de forma explícita en `additional_fields`
según ese valor (`"me"` → el accountId propio, resuelto una vez con `atlassianUserInfo` y
cacheado; `"none"` → sin asignar) — nunca confíes en el default del proyecto.

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
2. **Padre:** ofrece: (a) **sin padre** (crear en la raíz del proyecto), o (b) indicar un **issue padre**. Para (b) acepta **clave** (`PROJ-59`), **texto** o **JQL**; construye la JQL **acotada al proyecto** (`project = "KEY" AND (…)`, salvo `key = X` que es global) — el conector **exige** `searchResultMode:"issues"` y **rechaza** JQL sin restricción. Lista los resultados numerados y el usuario elige.

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

> "Voy a crear en Jira, en **PROJ** › bajo **PROJ-59**:
> • **6 Subtareas** (una por tarea del plan): T-01 «…», T-02 «…», …
> ¿Las creo? [Sí / Cambiar destino / Cancelar]"

Indica claramente **cuántos** issues, de **qué tipo** y **dónde** cuelgan.
