# Conector Atlassian (Rovo MCP) — hechos verificados

Referencia **única** de los comportamientos del conector que las skills (`confluence-publish`,
`confluence-pull`, `jira-sync`, `roadmap-dashboard`/live) asumen. Verificado contra una instancia
real (2026-07). Si el conector cambia, actualiza AQUÍ y revisa las skills que lo citan.

## Generales
- Los nombres de herramienta llevan prefijo `mcp__<uuid>__…`; el uuid varía por instalación. Resuélvelos en runtime, no los persistas en plantillas (usa marcadores `{{SERVER_*}}`).
- `cloudId` se obtiene de `getAccessibleAtlassianResources` (acepta también el hostname del site).

## Jira
- **`searchJiraIssuesUsingJql`**: REQUIERE `searchResultMode: "issues"`. Rechaza JQL **sin restricción** ("consultas ilimitadas") → acota siempre (`project = "KEY"`, `labels = "..."`, `key = X`). Los issues vienen en **`issues.nodes`** (a veces `issues[]`); parsea tolerante. Cada issue trae `fields.issuetype.hierarchyLevel` y `fields.project`.
- **`getVisibleJiraProjects`**: usa `searchString` + `maxResults`; devuelve `{ values: [...] }`. Puede haber >1000 proyectos: nunca listes sin filtro.
- **Jerarquía de tipos** (por `hierarchyLevel`, NO por nombre — los nombres varían por instancia/idioma): 2=Iniciativa, 1=Épica, 0=Tarea/Historia, −1=Subtarea (`subtask:true`). Un nivel 0 **no** puede ser padre de otro nivel 0 → sus hijos son subtareas.
- **`createJiraIssue`**: `projectKey`, `issueTypeName`, `summary` obligatorios; `parent` para colgar de otro issue (obligatorio en subtareas); labels/prioridad/custom fields vía `additional_fields`. Verifica obligatorios con `getJiraIssueTypeMetaWithFields(requiredFieldsOnly:true)` antes de crear. Acepta `contentFormat: "markdown"` en la descripción (checklist `- [ ]` incluida) y se conserva; `editJiraIssue(fields.description, markdown)` marcando `- [x]` reescribe la descripción íntegra, sin pérdida.
- **Asignación por defecto:** si el proyecto tiene "asignado por defecto" activo, un `createJiraIssue` sin `assignee` explícito puede auto-asignarse a otra persona del equipo (con notificación) — fija siempre `assignee` de forma explícita al crear (accountId propio vía `atlassianUserInfo`, o sin asignar) en vez de confiar en el default del proyecto.
- Worklogs: `addWorklogToJiraIssue` — varias entradas sobre el mismo issue **conviven** (no se pisan): `timespent` acumula la suma en segundos y `timetracking.timeSpent` la refleja en formato legible. Comentarios: `addCommentToJiraIssue` acepta markdown (tablas y blockquotes incluidos) y se relee tal cual; dentro de una celda de tabla, escapa `|` como `\|` o rompe la fila. Transiciones: descubre con `getTransitionsForJiraIssue` y resuelve la de cierre por `to.statusCategory.key == "done"` — **nunca** por el nombre de la transición ni del estado destino (varían por workflow/idioma, p. ej. transición "Done" hacia un estado "HECHO" localizado) ni por id fijo.

## Confluence
- **`createConfluencePage`** acepta `contentFormat: "markdown"` (tablas incluidas) y renderiza nativo; `spaceId` numérico o clave; `parentId` debe ser una **página**. Sin `parentId` → raíz del espacio.
- **No existe borrado** de páginas por el conector: marcar obsoleto + borrado manual.
- El frontmatter YAML de los .md **no sobrevive fiel** al viaje ida/vuelta → `confluence-pull` preserva el frontmatter local y solo reemplaza cuerpo.
- Árbol: `getConfluencePageDescendants` (por niveles, `depth`/`limit`); espacios: `getConfluenceSpaces` (trae `homepageId`).

## Artefactos (Cowork)
- `window.cowork.callMcpTool(name, args)` devuelve `{content, structuredContent, isError}`; lee `structuredContent ?? JSON.parse(content[0].text)`.
- Solo en Cowork/escritorio hay host de artefactos; en CLI/VS Code las skills usan su modo conversacional.
