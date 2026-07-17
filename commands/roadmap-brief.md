---
description: Genera un brief ejecutivo de la cartera (one-pager para dirección) combinando estado del roadmap, priorización y métricas real vs estimado, y lo exporta a PDF con aspecto moderno. Solo lee docs/roadmap/. Usa las skills roadmap-dashboard y to-pdf.
argument-hint: "(opcional) nota o foco para el brief (p. ej. 'cierre de trimestre')"
---

# /roadmap-brief — brief ejecutivo de la cartera (PDF)

Un **one-pager para dirección** que resume la cartera de iniciativas: qué hay, en qué estado, cuánto
se ha invertido/estimado y la eficiencia (real vs estimado). Combina lo que ya generan otros comandos
y lo deja en un PDF presentable. Solo lectura del roadmap. Foco opcional: **$ARGUMENTS**.

## Pasos
1. **Reúne los datos** (solo lectura) con la skill `roadmap-dashboard`:
   ```bash
   DASH="$(find "$PWD/.claude" "$HOME/.claude" -type f -path '*skills/roadmap-dashboard/scripts/build_dashboard.py' 2>/dev/null | head -1)"
   python3 "$DASH" --root docs/roadmap --json > /tmp/roadmap.json      # estado/presupuesto por iniciativa
   python3 "$DASH" --root docs/roadmap --metrics-md /tmp/metrics.md    # real vs estimado
   ```
   Si existe `docs/roadmap/BACKLOG.md` (de `/pm-backlog`), léelo para el orden recomendado.
2. **Compón el brief** en Markdown (`docs/roadmap/brief.md`), pensado para una página:
   - **Cabecera**: título, fecha, foco (`$ARGUMENTS` si viene).
   - **Resumen de cartera**: nº de iniciativas por estado (spec/eval), coste **estimado** total (€) y, si hay reales, **coste real** (horas × tarifa de `.claude/rates.json`) y **desviación**; multiplicador de productividad IA agregado si está disponible.
   - **Prioridades**: los primeros quick wins / apuestas del `BACKLOG.md`.
   - **Estado por iniciativa**: una línea cada una (título, estado, fase, coste, y real vs est si aplica).
   - **Nota de método** al pie: cifras estimadas vs reales, y qué se imputa.
3. **Exporta a PDF** con la skill **`to-pdf`** (o el agente `pdfy`): `docs/roadmap/brief.pdf`.
4. Presenta el PDF y resume en 2-3 líneas lo esencial (inversión, eficiencia, próximas apuestas).

## Reglas
- **Solo lectura del roadmap**; los únicos ficheros que creas son `brief.md`/`brief.pdf` (y los temporales).
- **Cifras honestas**: usa estimado y real por separado; no mezcles ni inventes. Si no hay reales aún, dilo y muestra solo lo estimado.
- **Una página**: prioriza titulares y totales; el detalle ya está en el dashboard y las evaluaciones.
- Para audiencia no técnica: lenguaje llano, sin jerga de tickets ni rutas internas.
