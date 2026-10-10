<!-- GENERADO por scripts/export-interop.py desde commands/roadmap-status.md — no lo edites a mano.
     Regenera con `python3 scripts/export-interop.py`; el porqué está en `docs/INTEROP.md`. -->

> **Adaptación a Codex** (fichero generado; la fuente es `commands/roadmap-status.md`).
> Este comando ORQUESTA agentes. En Codex no hay herramienta Agent: usa `spawn_agent` con `agent_type` igual al ID nativo del rol, si está disponible; las definiciones se copian a `.codex/agents/`.
> En el cuerpo, los roles propios se resuelven con este mapa: analyst → `custom-agents-analyst`; architect → `custom-agents-architect`; documenter → `custom-agents-documenter`; evaluator → `custom-agents-evaluator`; implementer → `custom-agents-implementer`; knowledge-curator → `custom-agents-knowledge-curator`; nemesis → `custom-agents-nemesis`; planner → `custom-agents-planner`; qa → `custom-agents-qa`; reviewer → `custom-agents-reviewer`. Conserva nombres y rutas de agentes del consumidor.
> Las skills se invocan mencionándolas con `$custom-agents:nombre` para las skills de este plugin; conserva el nombre nativo de las skills del consumidor. Todo lo demás (puertas, artefactos, ledger) no cambia.


# /roadmap-status — panel de estado del roadmap

Produce una vista de un vistazo de la cartera de iniciativas en `docs/roadmap/`. Es de **solo
lectura**: no toca spec/evaluación/plan/tasks. Complemento visual de `/pm-cycle` (que define una a
una) y de `/pm-backlog` (que prioriza).

## Pasos
1. Fija la raíz: `docs/roadmap` por defecto, o la que pase **$ARGUMENTS**.
2. Localiza el generador de la skill **`roadmap-dashboard`** sin depender del scope (regla 5 de `docs/CONVENTIONS.md`) y ejecútalo:

   ```bash
   DASH="$(find "$PWD/.claude" "$PWD/.codex" "$PWD/.opencode" "$HOME/.claude" "$HOME/.codex" "$HOME/.config/opencode" -type f -path '*skills/roadmap-dashboard/scripts/build_dashboard.py' 2>/dev/null | head -1)"
   python3 "$DASH" --root docs/roadmap --html docs/roadmap/dashboard.html --md docs/roadmap/dashboard.md
   ```

3. Si `docs/roadmap/` no existe todavía, dilo y sugiere crear la primera iniciativa con `/pm-cycle <objetivo>`. No crees carpetas vacías.
4. Presenta el fichero `docs/roadmap/dashboard.html` al usuario (en Cowork, con la tarjeta de fichero) y resume en una línea: nº de iniciativas y reparto por estado de spec.

## Notas
- Genera dos ficheros: `dashboard.html` (vista local, autocontenida) y `dashboard.md` (para Confluence). El `.md` lo espeja `confluence-publish` como una página, para que un **PM sin git** vea el estado real; el `.html` se queda local.
- No hay refresco automático: para actualizar el panel, vuelve a ejecutar `/roadmap-status`. En Confluence, la página se refresca cuando se sincroniza `docs/` (la skill regenera el `.md` antes de publicar).
- La sincronización a Confluence es la del proyecto (opt-in en `.claude/confluence.json`); este comando no fuerza publicación.
