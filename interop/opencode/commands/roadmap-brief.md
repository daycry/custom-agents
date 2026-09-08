---
description: "Genera un brief ejecutivo de la cartera (one-pager para dirección) combinando estado del roadmap, priorización y métricas real vs estimado, y lo exporta a PDF con aspecto moderno. Solo lee docs/roadmap/. Usa las skills roadmap-dashboard y to-pdf."
---
<!-- GENERADO por scripts/export-interop.py desde commands/roadmap-brief.md — no lo edites a mano.
     Regenera con `python3 scripts/export-interop.py`; el porqué está en `docs/INTEROP.md`. -->

> **Adaptación a OpenCode** (fichero generado; la fuente es `commands/roadmap-brief.md`).
> Este comando ORQUESTA agentes. En OpenCode no hay herramienta Agent: se delega con la herramienta `task` nombrando al subagente (o `@nombre`), definido en `.opencode/agents/`.
> Las skills se invocan con la herramienta `skill` (`skill({ name: "nombre" })`). Todo lo demás (puertas, artefactos, ledger) no cambia.

# /roadmap-brief — brief ejecutivo de la cartera (PDF)

Un **one-pager para dirección** que resume la cartera de iniciativas: qué hay, en qué estado, cuánto
se ha invertido/estimado y la eficiencia (real vs estimado). Combina lo que ya generan otros comandos
y lo deja en un PDF presentable. Solo lectura del roadmap. Foco opcional: **$ARGUMENTS**.

## Pasos
1. **Reúne los datos** (solo lectura) con la skill `roadmap-dashboard`:
   ```bash
   DASH="$(find "$PWD/.claude" "$PWD/.codex" "$PWD/.opencode" "$HOME/.claude" "$HOME/.codex" "$HOME/.config/opencode" -type f -path '*skills/roadmap-dashboard/scripts/build_dashboard.py' 2>/dev/null | head -1)"
   python3 "$DASH" --root docs/roadmap --json > /tmp/roadmap.json      # estado/presupuesto por iniciativa
   python3 "$DASH" --root docs/roadmap --metrics-md /tmp/metrics.md    # real vs estimado
   ```
   Si existe `docs/roadmap/BACKLOG.md` (de `/pm-backlog`), léelo para el orden recomendado.
2. **Compón el brief** en Markdown (`docs/roadmap/brief.md`), pensado para una página:
   - **Cabecera**: título, fecha, foco (`$ARGUMENTS` si viene).
   - **Resumen de cartera**: nº de iniciativas por estado (spec/eval), coste **estimado** total (€) y, si hay reales, **coste real** (horas × tarifa de `.claude/rates.json`) y **desviación**; multiplicador de productividad IA agregado si está disponible.
   - **Prioridades**: los primeros quick wins / apuestas del `BACKLOG.md`.
   - **Estado por iniciativa**: una línea cada una (título, estado, fase, coste, y real vs est si aplica).
   - **Salud del código** (opcional, una fila): si el usuario la pide o ya existe un `code-health.json` reciente en `docs/roadmap/`, pega la cabecera del informe de la skill `code-health` (`% duplicado · funciones largas · hotspots · TODO viejos`) — números del script, nunca estimados.
   - **Nota de método** al pie: cifras estimadas vs reales, y qué se imputa.
3. **Exporta a PDF** con la skill **`to-pdf`**: `docs/roadmap/brief.pdf`.
4. Presenta el PDF y resume en 2-3 líneas lo esencial (inversión, eficiencia, próximas apuestas).
5. **Sincronizar con Confluence (opcional).** Aplica el paso compartido `"$SHAREDKIT/confluence-optin.md"` (skill `confluence-publish` con opt-in) sobre `docs/roadmap/brief.md` (el `.pdf` no entra en el espejo, no es `.md`). Localízalo con `SHAREDKIT="$(find "$PWD/.claude" "$PWD/.codex" "$PWD/.opencode" "$HOME/.claude" "$HOME/.codex" "$HOME/.config/opencode" -type d -path '*agent-kits/shared' 2>/dev/null | head -1)"`. Fallback si no está: invoca `confluence-publish` respetando su opt-in, sin bloquear el cierre; nunca sincronices `docs/security-scan/`.

## Reglas
- **Solo lectura del roadmap**; los únicos ficheros que creas son `brief.md`/`brief.pdf` (y los temporales).
- **Cifras honestas**: usa estimado y real por separado; no mezcles ni inventes. Si no hay reales aún, dilo y muestra solo lo estimado.
- **Una página**: prioriza titulares y totales; el detalle ya está en el dashboard y las evaluaciones.
- Para audiencia no técnica: lenguaje llano, sin jerga de tickets ni rutas internas.
