---
description: Genera un brief ejecutivo de la cartera (one-pager para dirección) combinando estado del roadmap, priorización y métricas real vs estimado, y permite exportarlo a PDF si el módulo está disponible. Lee docs/roadmap/ y escribe docs/roadmap/brief.md (y brief.pdf si se pide). Usa las skills roadmap-dashboard y to-pdf.
argument-hint: "(opcional) nota o foco para el brief (p. ej. 'cierre de trimestre')"
---

# /roadmap-brief — brief ejecutivo de la cartera (PDF)

Un **one-pager para dirección** que resume la cartera de iniciativas: qué hay, en qué estado, cuánto
se ha invertido/estimado y la eficiencia (real vs estimado). Combina lo que ya generan otros comandos
y lo deja en un PDF presentable. Lee el roadmap sin modificarlo y escribe solo `brief.md`/`brief.pdf`. Foco opcional: **$ARGUMENTS**.

## Pasos
1. **Reúne los datos** (solo lectura; los temporales van a un directorio que pide al sistema, no a una ruta fija de Unix) con la skill `roadmap-dashboard`:
   ```bash
   R="${CLAUDE_PLUGIN_ROOT}"; M=agent-kits/shared/ledger-lint.py; [ -f "$R/$M" ] || R="$(for r in "$PWD"/.{claude,codex,opencode} ~/.{claude,codex}/plugins/cache/daycry ~/.{claude,codex,config/opencode}; do find "$r" -maxdepth 5 -path "*/$M" ! -path "$r/jobs/*" ! -path "$r/worktrees/*" 2>/dev/null | sort -V | tail -1 | grep . && break; done)"; R="${R%/$M}"; DASH="${R:+$R/skills/roadmap-dashboard/scripts/build_dashboard.py}"
   TMPD="$(python3 -c 'import tempfile; print(tempfile.mkdtemp(prefix="roadmap-brief-"))')"   # temporal portable (Windows incluido)
   python3 "$DASH" --root docs/roadmap --json > "$TMPD/roadmap.json"      # estado/presupuesto por iniciativa
   python3 "$DASH" --root docs/roadmap --metrics-md "$TMPD/metrics.md"    # real vs estimado
   ```
   Si existe `docs/roadmap/BACKLOG.md` (de `/pm-backlog`), léelo para el orden recomendado.
2. **Compón el brief** en Markdown (`docs/roadmap/brief.md`), pensado para una página:
   - **Cabecera**: título, fecha, foco (`$ARGUMENTS` si viene).
   - **Resumen de cartera**: nº de iniciativas por estado (spec/eval), coste **estimado** total (€) y, si hay reales, **coste real** (horas × tarifa de `.claude/rates.json`) y **desviación**; multiplicador de productividad IA agregado si está disponible.
   - **Prioridades**: los primeros quick wins / apuestas del `BACKLOG.md`.
   - **Estado por iniciativa**: una línea cada una (título, estado, fase, coste, y real vs est si aplica).
   - **Salud del código** (opcional, una fila): si el usuario la pide o ya existe un `code-health.json` reciente en `docs/roadmap/`, pega la cabecera del informe de la skill `code-health` (`% duplicado · funciones largas · hotspots · TODO viejos`) — números del script, nunca estimados.
   - **Nota de método** al pie: cifras estimadas vs reales, y qué se imputa.
3. **PDF opcional:** si `to-pdf` está disponible y se solicita, exporta `docs/roadmap/brief.pdf`. Sin módulo o motor, entrega `brief.md` y avisa sin bloquear el brief; no inventes el PDF.
4. Presenta el PDF y resume en 2-3 líneas lo esencial (inversión, eficiencia, próximas apuestas).
5. **Documentación externa opcional.** Aplica `agent-kits/shared/project-integrations.md` con `docs.changed` para los documentos generados. Sin binding o permiso, conserva el resultado local. No publiques evidencias sensibles ni PDFs automáticamente.

## Reglas
- **El roadmap no se modifica**; los únicos ficheros que creas son `brief.md`/`brief.pdf` (y los temporales).
- **Cifras honestas**: usa estimado y real por separado; no mezcles ni inventes. Si no hay reales aún, dilo y muestra solo lo estimado.
- **Una página**: prioriza titulares y totales; el detalle ya está en el dashboard y las evaluaciones.
- Para audiencia no técnica: lenguaje llano, sin jerga de tickets ni rutas internas.
