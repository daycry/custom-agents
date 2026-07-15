# Changelog

Todos los cambios notables de este proyecto se documentan aquí.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el versionado sigue [SemVer](https://semver.org/lang/es/).

## [1.6.0] - 2026-07-15

### Añadido
- **Skill `jira-sync`**: vuelca un plan (`tasks.md`) a Jira vía el conector Atlassian (Rovo MCP). Se ofrece **al crear el plan** (opt-in en `.claude/jira.json`, como Confluence). Selector de destino **con doble modo**: artefacto interactivo en Cowork/escritorio (`assets/jira-picker.template.html` — busca proyecto, resuelve claves/URLs de issue, busca padre por clave/texto/JQL) y **conversacional** en CLI/VS Code. El **tipo de issue se deriva de la jerarquía del padre** (Épica/Iniciativa → Tarea/Historia; Tarea/Historia → Subtarea; sin padre → Tarea suelta), descubierto vía metadatos, no hardcodeado. Permite **crear una épica nueva** para la iniciativa. Idempotente vía `.claude/jira-state.json`.
- **Imputación automática de horas + cierre en Jira**: al completar cada tarea, `implementer` invoca `jira-sync` para imputar **Tiempo IA (ejec.) + Supervisión** (real→estimación) y transicionar el issue a *Done* (transición descubierta, no fija). **Tope de jornada diario** configurable (`horasJornada`, 8h/7h) con **banco de horas por issue**: al cubrir la jornada pregunta (parar / seguir / banco) y el excedente se imputa en jornadas posteriores, siempre con fecha del día en curso (nunca post-datado).
- **Plantilla `tasks.md` del `planner`** ampliada con **Tiempo IA (ejec.)** y **Supervisión** por tarea (además del tiempo humano), y columnas equivalentes en el resumen de progreso.

### Cambiado
- `planner` (ofrece el volcado al crear el plan) e `implementer` (refleja el progreso) declaran la skill `jira-sync`; `/dev-cycle` lo integra; `/pm-cycle` deja de duplicar el handoff conversacional a Jira.

## [1.5.1] - 2026-07-15

### Añadido
- **`scripts/release.py`**: sube la versión de forma **coherente** en los tres sitios (`plugin.json` y los dos campos de `marketplace.json`), valida que coinciden y crea commit + tag. Evita el fallo de olvidar `marketplace.json` (que deja al cliente sin ver la actualización).
- **Tests del dashboard** (`tests/` con fixtures) y **avisos** en `roadmap-dashboard`: el generador emite por `stderr` cuando no puede leer un campo esperado (posible cambio de etiquetas en las plantillas) o detecta incoherencias de estado, con `--strict` para CI.

### Cambiado
- `docs/INSTALL.md`: aviso de **no ubicar el repo git en carpeta sincronizada en la nube** (OneDrive/Dropbox…) por conflictos de locks/índice, y uso del script de release.

## [1.5.0] - 2026-07-15

### Añadido
- **Rol PM (producto) separado del desarrollo**: command **`/pm-cycle`** (spec → evaluación; cierra en la puerta go/no-go y ofrece handoff a `/dev-cycle`; salidas opt-in: brief PDF y épica en Jira) y **`/pm-backlog`** (prioriza la cartera leyendo todas las `evaluation.md` → `docs/roadmap/BACKLOG.md`).
- **Skill `roadmap-dashboard`** + command **`/roadmap-status`**: escanea `docs/roadmap/*/` y genera un dashboard **HTML** (vista local), **Markdown** (para Confluence) o **JSON** con estado, prioridad y presupuesto por iniciativa.
- **Skill `confluence-pull`** + command **`/confluence-pull`**: sentido **inverso** de la publicación (Confluence → `docs/` local) para PMs sin git; preserva el frontmatter local, avisa de conflictos y confirma antes de escribir. Reutiliza el mapa `.claude/confluence-state.json`.
- **Dashboard del roadmap publicable en Confluence**: `confluence-publish` regenera `dashboard.md` antes de publicar cuando cambia `docs/roadmap/`, para que un PM vea el estado real sin git.

### Cambiado
- Documentación e índices (`CLAUDE.md`, `docs/README.md`) con los nuevos comandos y skills; sincronización con Confluence descrita como **bidireccional**.

## [1.3.1] - 2026-07-10

### Añadido
- **Agente `documenter`**: genera y mantiene la documentación técnica y de producto del proyecto bajo `docs/`, con estructura **derivada del propio proyecto** (no impone nombres de carpeta; deriva del reparto y vocabulario del repo). Cubre índice, RAG-INDEX, arquitectura, stack, unidades del sistema, guías y producto; idempotente; propone estructura y confirma antes de redactar. Se ejecuta **al cerrar el ciclo de un plan** (implementación hecha + pruebas automáticas de `qa` en verde), como handoff de `qa`, **no tarea a tarea**. Incluye kit `agent-kits/documenter` (`taxonomy.md` + plantillas de formato genéricas). Sincroniza los docs en Confluence (opt-in).
- **Agente `implementer`**: implementa un plan aprobado fase a fase (escribe código real del proyecto, sobre rama), marcando `docs/roadmap/<…>/tasks.md` como **ledger canónico** de progreso por tarea; respeta guardrails y hace handoff a `qa`. Es el único agente que modifica código.
- **Command `/dev-cycle <objetivo>`** (`commands/dev-cycle.md`): orquestador que dirige la cadena invocando cada agente por nombre (sin depender de la auto-selección), con puertas de control (go/no-go, OK de plan, verde de qa). Tu `evaluator` y `planner` **siempre** generan los artefactos en `docs/roadmap/` (spec, evaluación, plan, tasks); no se delega la planificación. **Detecta superpowers**: si está, delega solo la **ejecución** (implementación/TDD/review) trabajando contra tu `tasks.md`; si no, usa la cadena nativa (`implementer` + `qa`). Sin dependencia dura de superpowers.
- **Regla de ledger canónico** (regla 8 de `CONVENTIONS.md` + banner en la plantilla `tasks.md`): el progreso de un plan se registra solo en `tasks.md`; cualquier implementador —incluidos orquestadores externos como *superpowers subagent-driven-development*— debe actualizarlo; los ledgers propios son espejo, no fuente.

### Cambiado
- **Transiciones de estado por fase**: los artefactos ya no se quedan en `borrador`. `/dev-cycle` (y los agentes al ejecutarse sueltos) mueven spec/evaluación/plan/tareas al estado que toca en cada puerta (go → spec `aprobada`/eval `completado`; arranque impl. → plan `en-progreso`; cierre en verde → plan `completado`/spec `implementada`; no-go/cancelación → `cancelado`/`obsoleta`). Mapa en regla 7 de `CONVENTIONS.md`.
- Cadena de trabajo ampliada a `evaluator → planner → implementer → qa → documenter`; `qa` hace handoff a `documenter` con las pruebas en verde.
- Documentación e índices actualizados (`README.md`, `docs/README.md`, `docs/CONVENTIONS.md`, `CLAUDE.md`) con los nuevos agentes, el command y los modos con/sin superpowers.

## [1.3.0] - 2026-07-10

### Añadido
- **Skill compartida `confluence-publish`**: publica/espeja `docs/` en Confluence usando el conector oficial de Atlassian (Rovo MCP), sin integración propia. Asistente guiado para personas no técnicas: conexión → elegir espacio (con búsqueda) → navegar el árbol → elegir destino (raíz del espacio o bajo una página existente) → nombrar la página del proyecto → subir. Idempotente (crea/actualiza, no duplica).
- **Sincronización opt-in** en `planner`, `evaluator` y `qa` (nuevo paso "P7. Sincronizar con Confluence"): al escribir en `docs/`, invocan la skill para reflejar los cambios. La primera vez se pregunta si se quiere sincronizar; la decisión se guarda en `.claude/confluence.json` (`enabled: true/false`) y no se vuelve a preguntar.
- **Navegador de árbol interactivo** (`skills/confluence-publish/assets/tree-browser.template.html`): en Cowork/escritorio expande páginas en vivo vía el conector; al elegir un destino pregunta si usar esa página o crear una hija (con nombre).
- **Fallback conversacional** del paso del árbol para Claude Code CLI y la extensión de VS Code (sin host de artefactos).
- **Detección de cambios sin git**: manifiesto de estado `.claude/confluence-state.json` (hash de contenido + `pageId` por documento); publica solo lo cambiado (crear/actualizar/obsoleto), idempotente e independiente de commits/fechas.
- **Hook `PostToolUse`** (`hooks/hooks.json` + `hooks/mark-docs-pending.sh`): disparador determinista que, al editar bajo `docs/`, deja una marca `.claude/.confluence-pending` (no publica; excluye `docs/security-scan/`). La publicación real la hace la skill.
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

[1.6.0]: https://github.com/daycry/custom-agents/releases/tag/v1.6.0
[1.5.1]: https://github.com/daycry/custom-agents/releases/tag/v1.5.1
[1.5.0]: https://github.com/daycry/custom-agents/releases/tag/v1.5.0
[1.3.1]: https://github.com/daycry/custom-agents/releases/tag/v1.3.1
[1.3.0]: https://github.com/daycry/custom-agents/releases/tag/v1.3.0
