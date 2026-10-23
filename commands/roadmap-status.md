---
description: Muestra el estado de todas las iniciativas del roadmap (spec, evaluación, plan, tasks, testing), sus estados, prioridad y presupuesto. Lee docs/roadmap/ y ESCRIBE docs/roadmap/dashboard.md y la carpeta docs/roadmap/panel/ (panel multi-página exportado); no toca spec, evaluación, plan ni tasks, y no crea docs/roadmap/ si falta. Usa las skills roadmap-dashboard (datos) y plugin-panel (presentación).
argument-hint: "(opcional) ruta al roadmap; por defecto docs/roadmap"
---

# /roadmap-status — panel de estado del roadmap

Produce una vista de un vistazo de la cartera de iniciativas en `docs/roadmap/`. **Lee** el roadmap y
**escribe solo** `docs/roadmap/dashboard.md` y la carpeta `docs/roadmap/panel/`: no toca
spec/evaluación/plan/tasks. Complemento visual de `/pm-cycle` (que define una a
una) y de `/pm-backlog` (que prioriza).

## Pasos
1. Fija la raíz: `docs/roadmap` por defecto, o la que pase **$ARGUMENTS**.
2. Localiza los dos generadores sin depender del scope (regla 5 de `docs/CONVENTIONS.md`) y ejecútalos:

   ```bash
   DASH="$(find "$PWD/.claude" "$PWD/.codex" "$PWD/.opencode" "$HOME/.claude" "$HOME/.codex" "$HOME/.config/opencode" -type f -path '*skills/roadmap-dashboard/scripts/build_dashboard.py' 2>/dev/null | head -1)"
   PANEL="$(find "$PWD/.claude" "$PWD/.codex" "$PWD/.opencode" "$HOME/.claude" "$HOME/.codex" "$HOME/.config/opencode" -type f -path '*skills/plugin-panel/scripts/build_panel.py' 2>/dev/null | head -1)"
   [ -d docs/roadmap ] && python3 "$DASH" --root docs/roadmap --md docs/roadmap/dashboard.md &&      python3 "$PANEL" --export docs/roadmap/panel --project "$PWD"
   ```

3. Si `docs/roadmap/` no existe todavía, el bloque anterior no ejecuta nada: dilo y sugiere crear la primera iniciativa con `/pm-cycle <objetivo>`. No crees carpetas vacías. Si `build_dashboard.py` falla, tampoco se exporta el panel: informa del error en vez de dejar una exportación a medias.
4. Entrega `docs/roadmap/panel/iniciativas.html` al usuario (en Cowork, con la tarjeta de fichero; el panel exportado aterriza en la página Iniciativas y se abre desde `index.html`) y resume en una línea: nº de iniciativas y reparto por estado de spec.
5. Si existe un `docs/roadmap/dashboard.html` de una versión anterior, avisa **una vez** de que ya no se regenera y de que la vista nueva es `docs/roadmap/panel/`. Nunca lo borres.

## Notas
- Genera `dashboard.md` (para Confluence) y la carpeta `docs/roadmap/panel/` (HTML local, sin servidor, siete páginas). El `.md` lo espeja `confluence-publish` como una página, para que un **PM sin git** vea el estado real; el panel se queda local.
- La carpeta `panel/` es una exportación estática: para progreso en vivo usa `/plugin-catalog --serve`. No hay refresco automático: vuelve a ejecutar `/roadmap-status` para actualizarla. En Confluence, la página se refresca cuando se sincroniza `docs/` (la skill regenera el `.md` antes de publicar).
- La sincronización a Confluence es la del proyecto (opt-in en `.claude/confluence.json`); este comando no fuerza publicación.
