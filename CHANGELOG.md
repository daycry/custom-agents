# Changelog

Todos los cambios notables de este proyecto se documentan aquí.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el versionado sigue [SemVer](https://semver.org/lang/es/).

## [1.3.0] - 2026-07-10

### Añadido
- **Agente `documenter`**: genera y mantiene la documentación técnica y de producto del proyecto bajo `docs/`, con estructura **derivada del propio proyecto** (no impone nombres de carpeta; deriva del reparto y vocabulario del repo). Cubre índice, RAG-INDEX, arquitectura, stack, unidades del sistema, guías y producto; idempotente; propone estructura y confirma antes de redactar. Se ejecuta **al cerrar el ciclo de un plan** (implementación hecha + pruebas automáticas de `qa` en verde), como handoff de `qa`, **no tarea a tarea**. Incluye kit `agent-kits/documenter` (`taxonomy.md` + plantillas de formato genéricas). Sincroniza los docs en Confluence (opt-in).
- **Skill compartida `confluence-publish`**: publica/espeja `docs/` en Confluence usando el conector oficial de Atlassian (Rovo MCP), sin integración propia. Asistente guiado para personas no técnicas: conexión → elegir espacio (con búsqueda) → navegar el árbol → elegir destino (raíz del espacio o bajo una página existente) → nombrar la página del proyecto → subir. Idempotente (crea/actualiza, no duplica).
- **Sincronización opt-in** en `planner`, `evaluator` y `qa` (nuevo paso "P7. Sincronizar con Confluence"): al escribir en `docs/`, invocan la skill para reflejar los cambios. La primera vez se pregunta si se quiere sincronizar; la decisión se guarda en `.claude/confluence.json` (`enabled: true/false`) y no se vuelve a preguntar.
- **Navegador de árbol interactivo** (`skills/confluence-publish/assets/tree-browser.template.html`): en Cowork/escritorio expande páginas en vivo vía el conector; al elegir un destino pregunta si usar esa página o crear una hija (con nombre).
- **Fallback conversacional** del paso del árbol para Claude Code CLI y la extensión de VS Code (sin host de artefactos).
- Config de ejemplo `skills/confluence-publish/assets/confluence.example.json`.

### Cambiado
- Documentación actualizada (`README.md`, `docs/README.md`, `docs/INSTALL.md`, `CLAUDE.md`): nueva skill, alta del conector Atlassian por entorno (Cowork vs CLI/VS Code), comportamiento opt-in y matriz de compatibilidad.
- Dependencias declaradas de `planner`, `evaluator` y `qa`: añadida la skill `confluence-publish`.

### Seguridad
- `docs/security-scan/**` (datos sensibles del agente `nemesis`) queda **excluido** de la sincronización con Confluence de forma explícita.

### Notas / Limitaciones
- El borrado de un `.md` no elimina la página en Confluence: el conector Atlassian no expone borrado/archivado, así que la página se marca como obsoleta y se lista para borrado manual.
- La sincronización requiere dar de alta el conector de Atlassian una vez por entorno (ver `docs/INSTALL.md`).

## [1.2.0] - anterior

Versiones anteriores a la introducción de este changelog: bundle con los agentes `nemesis`, `evaluator`, `planner`, `pdfy` y `qa`, y las skills compartidas `cybersecurity` y `to-pdf`. Empaquetado como plugin + marketplace.

[1.3.0]: https://github.com/daycry/claude-agents/releases/tag/v1.3.0
