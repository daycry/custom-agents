---
description: Abre un dashboard VIVO del estado del roadmap leyendo Jira en tiempo real (issues + horas imputadas por label). En Cowork/escritorio como artefacto interactivo; en CLI/VS Code como resumen conversacional. Requiere el conector Atlassian y que el plan se haya volcado con jira-sync. Usa la skill roadmap-dashboard.
argument-hint: "(opcional) <slug> de una iniciativa; por defecto toda la cartera (label 'roadmap')"
---

# /roadmap-live — estado del roadmap en vivo desde Jira

A diferencia de `/roadmap-status` (que lee los ficheros locales), esto consulta **Jira en tiempo
real**: estado de cada issue y horas imputadas, por label. Requiere haber volcado el plan con
`jira-sync` (que etiqueta los issues con `roadmap` y el `<slug>`). Objetivo: **$ARGUMENTS**
(un `<slug>` concreto; si se omite, la cartera entera con label `roadmap`).

## Pasos
1. Comprueba el conector Atlassian (`getAccessibleAtlassianResources`); si no está, dilo y detente. Resuelve `cloudId`. Fija el `LABEL`: el `<slug>` de **$ARGUMENTS** o `roadmap`.
2. **Detecta el entorno:**
   - **Cowork / escritorio (con artefactos):** localiza la plantilla y publícala como artefacto en vivo.
     ```bash
     TPL="$(find "$PWD/.claude" "$HOME/.claude" -type f -path '*skills/roadmap-dashboard/assets/jira-live.template.html' 2>/dev/null | head -1)"
     ```
     Copia la plantilla, sustituye `{{SERVER_SEARCH}}` (nombre completo `mcp__<uuid>__searchJiraIssuesUsingJql`), `{{CLOUD_ID}}`, `{{LABEL}}` y `{{TITULO}}`, y publícala con `create_artifact` (`mcp_tools=[searchJiraIssuesUsingJql]`). El artefacto lee en vivo al abrirse; el host ya trae botón de recarga.
   - **CLI / VS Code (sin artefactos):** haz la misma consulta por texto — `searchJiraIssuesUsingJql` con `jql = 'labels = "<LABEL>" ORDER BY status'`, `searchResultMode:"issues"`, `fields:["summary","status","timetracking","aggregatetimespent"]` — y muestra un resumen: nº de issues, % done, horas imputadas totales y una lista `clave · estado · horas`.
3. Resume en una línea: completado (%), horas imputadas y cuántos issues en curso.

## Notas
- Es **solo lectura** de Jira; no crea ni modifica issues.
- Si no hay issues con ese label, indícalo y sugiere volcar el plan con `jira-sync` primero.
- El estado se agrupa por **categoría** de estado de Jira (Done / En curso / Pendiente), no por el nombre exacto, para ser robusto entre flujos de trabajo.
