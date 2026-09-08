---
description: "Informe real vs estimado del roadmap — compara horas y tokens estimados (evaluación/plan) contra los reales imputados en tasks.md, con desviaciones y un total de cartera. Solo lee; no modifica nada. Usa la skill roadmap-dashboard."
---
<!-- GENERADO por scripts/export-interop.py desde commands/roadmap-metrics.md — no lo edites a mano.
     Regenera con `python3 scripts/export-interop.py`; el porqué está en `docs/INTEROP.md`. -->

> **Adaptación a OpenCode** (fichero generado; la fuente es `commands/roadmap-metrics.md`).
> Este comando ORQUESTA agentes. En OpenCode no hay herramienta Agent: se delega con la herramienta `task` nombrando al subagente (o `@nombre`), definido en `.opencode/agents/`.
> Las skills se invocan con la herramienta `skill` (`skill({ name: "nombre" })`). Todo lo demás (puertas, artefactos, ledger) no cambia.

# /roadmap-metrics — real vs estimado (cierre del presupuesto)

Cierra el bucle del presupuesto: mientras `/pm-cycle` y `planner` **estiman** (horas, coste €,
tokens), este comando muestra lo que **de verdad ha costado**, leyendo las horas `real` de cada
`tasks.md`. Es de **solo lectura**.

## Pasos
1. Fija la raíz (`docs/roadmap` por defecto, o **$ARGUMENTS**).
2. Localiza el generador de la skill **`roadmap-dashboard`** y ejecútalo en modo métricas:

   ```bash
   DASH="$(find "$PWD/.claude" "$PWD/.codex" "$PWD/.opencode" "$HOME/.claude" "$HOME/.codex" "$HOME/.config/opencode" -type f -path '*skills/roadmap-dashboard/scripts/build_dashboard.py' 2>/dev/null | head -1)"
   python3 "$DASH" --root docs/roadmap --metrics-md docs/roadmap/metrics.md
   ```

3. Presenta `docs/roadmap/metrics.md` y resume en 1-2 líneas: desviación total (real vs estimado) y qué iniciativas se desvían más.

## Notas
- **Producción = Tiempo IA (ejec.) + Supervisión** (lo que `jira-sync` imputa). Se compara real/est de la fila TOTAL de cada `tasks.md`; también muestra horas humanas y tokens.
- El informe incluye la sección **Coste de proceso**: lo que costó *producir* spec/evaluación/plan/tasks (bloque `generacion:` del frontmatter, medido con tokens reales por `usage-meter`), separado del coste de implementación. Duraciones en formato `XhYm`. Iniciativas sin bloque → "sin datos" (no se inventa 0).
- Desviación negativa = menos horas reales que estimadas (más eficiente); positiva = sobrecoste.
- El **coste €** sale de multiplicar horas por la tarifa de `.claude/rates.json` (config compartida de presupuesto).
- Si aún no hay horas `real` registradas, lo indica en vez de inventar cifras.
- Se apoya en los avisos del generador: si una `evaluation.md`/`tasks.md` cambió sus etiquetas y algo no se lee, sale por `stderr`.
