---
description: "Muestra el estado de todas las iniciativas del roadmap (spec, evaluación, plan, tasks, testing), sus estados, prioridad y presupuesto. Lee docs/roadmap/ y ESCRIBE docs/roadmap/dashboard.md y la carpeta docs/roadmap/panel/ (panel multi-página exportado); no toca spec, evaluación, plan ni tasks, y no crea docs/roadmap/ si falta. Usa las skills roadmap-dashboard (datos) y plugin-panel (presentación)."
---
<!-- GENERADO por scripts/export-interop.py desde commands/roadmap-status.md — no lo edites a mano.
     Regenera con `python3 scripts/export-interop.py`; el porqué está en `docs/INTEROP.md`. -->

> **Adaptación a OpenCode** (fichero generado; la fuente es `commands/roadmap-status.md`).
> Este comando ORQUESTA agentes. En OpenCode no hay herramienta Agent: usa `subagent` con el campo `agent` igual al ID nativo, definido en `.opencode/agents/`.
> En el cuerpo, los roles propios se resuelven con este mapa: analyst → `custom-agents-analyst`; architect → `custom-agents-architect`; documenter → `custom-agents-documenter`; evaluator → `custom-agents-evaluator`; implementer → `custom-agents-implementer`; knowledge-curator → `custom-agents-knowledge-curator`; nemesis → `custom-agents-nemesis`; planner → `custom-agents-planner`; qa → `custom-agents-qa`; reviewer → `custom-agents-reviewer`. Conserva nombres y rutas de agentes del consumidor.
> Las skills se invocan con la herramienta `skill` (`skill({ id: "nombre" })`). Todo lo demás (puertas, artefactos, ledger) no cambia.

# /roadmap-status — panel de estado del roadmap

Produce una vista de un vistazo de la cartera de iniciativas en `docs/roadmap/`. **Lee** el roadmap y
**escribe solo** `docs/roadmap/dashboard.md` y la carpeta `docs/roadmap/panel/`: no toca
spec/evaluación/plan/tasks. Complemento visual de `/pm-cycle` (que define una a
una) y de `/pm-backlog` (que prioriza).

## Pasos
1. Fija la raíz: `docs/roadmap` por defecto, o la que pase **$ARGUMENTS**.
2. Localiza el generador de datos y el panel opcional sin depender del scope. Si el panel no está disponible, entrega `dashboard.md` y avisa sin bloquear el estado local:

   ```bash
   DASH="$(find "$PWD/.claude" "$PWD/.codex" "$PWD/.opencode" "$HOME/.claude" "$HOME/.codex" "$HOME/.config/opencode" -type f -path '*skills/roadmap-dashboard/scripts/build_dashboard.py' 2>/dev/null | head -1)"
   PANEL="$(find "$PWD/.claude" "$PWD/.codex" "$PWD/.opencode" "$HOME/.claude" "$HOME/.codex" "$HOME/.config/opencode" -type f -path '*skills/plugin-panel/scripts/build_panel.py' 2>/dev/null | head -1)"
   if [ -d docs/roadmap ] && [ -f "$DASH" ]; then
     python3 "$DASH" --root docs/roadmap --md docs/roadmap/dashboard.md
     if [ "$?" -eq 0 ] && [ -f "$PANEL" ]; then
       python3 "$PANEL" --export docs/roadmap/panel --project "$PWD"
     fi
   fi
   ```

3. Si `docs/roadmap/` no existe todavía, el bloque anterior no ejecuta nada: dilo y sugiere crear la primera iniciativa con `/pm-cycle <objetivo>`. No crees carpetas vacías. Si `build_dashboard.py` falla, tampoco se exporta el panel: informa del error en vez de dejar una exportación a medias.
4. Entrega el resultado generado en esta ejecución: `dashboard.md` y, solo si el módulo opcional pudo exportarlo, `panel/iniciativas.html`. Un HTML antiguo no acredita exportación actual. Resume nº de iniciativas y reparto por estado de spec.
5. Si existe un `docs/roadmap/dashboard.html` de una versión anterior, avisa **una vez** de que ya no se regenera y de que la vista nueva es `docs/roadmap/panel/`. Nunca lo borres.

## Notas
- Genera `dashboard.md` y, con el módulo de catálogo disponible, un panel HTML local. La documentación puede proyectarse mediante `project-integrations.md`, sin exigir un proveedor.
- La carpeta `panel/` es una exportación estática: para progreso en vivo usa `/plugin-catalog --serve`. No hay refresco automático: vuelve a ejecutar `/roadmap-status` para actualizarla. En Confluence, la página se refresca cuando se sincroniza `docs/` (la skill regenera el `.md` antes de publicar).
- Las integraciones se eligen en este proyecto; este comando no fuerza publicación ni conexión.
