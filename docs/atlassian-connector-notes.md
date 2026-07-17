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
- **`createJiraIssue`**: `projectKey`, `issueTypeName`, `summary` obligatorios; `parent` para colgar de otro issue (obligatorio en subtareas); labels/prioridad/custom fields vía `additional_fields`. Verifica obligatorios con `getJiraIssueTypeMetaWithFields(requiredFieldsOnly:true)` antes de crear.
- Worklogs: `addWorklogToJiraIssue`. Transiciones: descubre con `getTransitionsForJiraIssue` (por categoría de estado destino), aplica con `transitionJiraIssue`; no hardcodees ids.

## Confluence
- **`createConfluencePage`** acepta `contentFormat: "markdown"` (tablas incluidas) y renderiza nativo; `spaceId` numérico o clave; `parentId` debe ser una **página**. Sin `parentId` → raíz del espacio.
- **No existe borrado** de páginas por el conector: marcar obsoleto + borrado manual.
- El frontmatter YAML de los .md **no sobrevive fiel** al viaje ida/vuelta → `confluence-pull` preserva el frontmatter local y solo reemplaza cuerpo.
- Árbol: `getConfluencePageDescendants` (por niveles, `depth`/`limit`); espacios: `getConfluenceSpaces` (trae `homepageId`).

## Artefactos (Cowork)
- `window.cowork.callMcpTool(name, args)` devuelve `{content, structuredContent, isError}`; lee `structuredContent ?? JSON.parse(content[0].text)`.
- Solo en Cowork/escritorio hay host de artefactos; en CLI/VS Code las skills usan su modo conversacional.
