# Vista opcional de Jira

Úsala sólo si la integración elegida es Jira y el host ofrece artefactos con tools de lectura. No modifica el ledger ni crea issues.

Resuelve el helper `agent-kits/shared/render-artifact.py` con las raíces proyecto/usuario de Claude, Codex u OpenCode. El modo `jira-live` requiere JSON con `SERVER_SEARCH`, `CLOUD_ID`, `LABEL` y `TITULO`, todos strings. El filtro debe pertenecer a la iniciativa/cartera consultada.

Guarda el JSON en un fichero y asigna su **ruta**, nunca el JSON inline, a `CONFIG_FILE`. `python3 "$RENDERER" --template jira-live --config "$CONFIG_FILE"` emite HTML por stdout. También admite `--config -` y JSON por stdin. Publica esa salida con el tool de lectura indicado en `mcp_tools`. Los títulos, errores y metadatos se muestran como texto; no sustituyas marcadores ni construyas JavaScript con strings del proveedor.

Sin helper o soporte de artefactos, presenta un snapshot conversacional usando el adaptador. No improvises HTML ni establezcas polling.

El valor de la etiqueta se serializa como un único literal JQL entre comillas, escapando comillas y barras para que no añada operadores. Referencia de sintaxis: [búsqueda avanzada de Atlassian](https://support.atlassian.com/jira-service-management-cloud/docs/what-is-advanced-search-in-jira-cloud/), consultada el 2026-11-06. Las pruebas son sintéticas; no consultan Jira real.
