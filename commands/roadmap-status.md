---
description: Genera un dashboard HTML con el estado de todas las iniciativas del roadmap (spec, evaluación, plan, tasks, testing), sus estados, prioridad y presupuesto. Solo lee docs/roadmap/; no modifica nada. Usa la skill roadmap-dashboard.
argument-hint: "(opcional) ruta al roadmap; por defecto docs/roadmap"
---

# /roadmap-status — panel de estado del roadmap

Produce una vista de un vistazo de la cartera de iniciativas en `docs/roadmap/`. Es de **solo
lectura**: no toca spec/evaluación/plan/tasks. Complemento visual de `/pm-cycle` (que define una a
una) y de `/pm-backlog` (que prioriza).

## Pasos
1. Fija la raíz: `docs/roadmap` por defecto, o la que pase **$ARGUMENTS**.
2. Localiza el generador de la skill **`roadmap-dashboard`** sin depender del scope (regla 5 de `docs/CONVENTIONS.md`) y ejecútalo:

   ```bash
   DASH="$(find "$PWD/.claude" "$HOME/.claude" -type f -path '*skills/roadmap-dashboard/scripts/build_dashboard.py' 2>/dev/null | head -1)"
   python3 "$DASH" --root docs/roadmap --html docs/roadmap/dashboard.html --md docs/roadmap/dashboard.md
   ```

3. Si `docs/roadmap/` no existe todavía, dilo y sugiere crear la primera iniciativa con `/pm-cycle <objetivo>`. No crees carpetas vacías.
4. Presenta el fichero `docs/roadmap/dashboard.html` al usuario (en Cowork, con la tarjeta de fichero) y resume en una línea: nº de iniciativas y reparto por estado de spec.

## Notas
- Genera dos ficheros: `dashboard.html` (vista local, autocontenida) y `dashboard.md` (para Confluence). El `.md` lo espeja `confluence-publish` como una página, para que un **PM sin git** vea el estado real; el `.html` se queda local.
- No hay refresco automático: para actualizar el panel, vuelve a ejecutar `/roadmap-status`. En Confluence, la página se refresca cuando se sincroniza `docs/` (la skill regenera el `.md` antes de publicar).
- La sincronización a Confluence es la del proyecto (opt-in en `.claude/confluence.json`); este comando no fuerza publicación.
