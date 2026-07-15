---
description: Rol PM de cartera. Lee todas las evaluaciones del roadmap (docs/roadmap/*/evaluation.md) y produce un backlog PRIORIZADO cross-iniciativa (quick wins vs. costosas) en docs/roadmap/BACKLOG.md, para decidir el orden de ejecución. No planifica ni implementa; solo lee y prioriza.
argument-hint: "(opcional) criterio de priorización, p. ej. 'maximizar valor por € este trimestre'"
---

# /pm-backlog — priorización de la cartera

Mientras `/pm-cycle` define y presupuesta **una** iniciativa, `/pm-backlog` mira **todas** a la vez
y propone **en qué orden abordarlas**. Es rol producto y de **solo lectura**: no crea specs, no
planifica, no implementa. Criterio de priorización (si se pasa): **$ARGUMENTS** (por defecto:
mejor relación valor/coste, favoreciendo quick wins).

## Pasos
1. Reúne los datos con la skill **`roadmap-dashboard`** (resumen JSON de todas las iniciativas):

   ```bash
   DASH="$(find "$PWD/.claude" "$HOME/.claude" -type f -path '*skills/roadmap-dashboard/scripts/build_dashboard.py' 2>/dev/null | head -1)"
   python3 "$DASH" --root docs/roadmap --json
   ```

   Si necesitas más detalle de alguna iniciativa (riesgos, características), abre su `evaluation.md`.
2. **Filtra**: considera iniciativas con evaluación (`has_eval`). Las que solo tienen spec o están en `borrador`/`en-revision` van en una sección aparte "aún sin presupuestar / a evaluar". Excluye las `cancelado`/`obsoleta` (lístalas al final como descartadas).
3. **Prioriza** aplicando el criterio pedido. Por defecto pondera: prioridad declarada (Crítica > Alta > Media > Baja), relación **valor/coste** (menor € y mayor multiplicador de productividad = mejor quick win), esfuerzo y riesgo. Explica el razonamiento; no inventes cifras que no estén en las evaluaciones.
4. **Escribe** `docs/roadmap/BACKLOG.md` con:
   - Fecha de generación y criterio aplicado.
   - **Tabla priorizada**: orden, iniciativa (enlace a su carpeta), estado spec/eval, prioridad, coste €, esfuerzo, multiplicador, fase, y una nota de "por qué aquí".
   - Bloque **Quick wins** (alto valor / bajo coste) y bloque **Apuestas grandes** (alto coste / alto impacto).
   - Sección **A evaluar** (solo spec) y **Descartadas** (canceladas/obsoletas).
   - Totales de la cartera **solo si** las cifras son homogéneas; si no, indícalo y no sumes.
5. Presenta `BACKLOG.md` y resume en 2-3 líneas el orden recomendado y el primer quick win.

## Reglas
- **Solo lectura del roadmap.** El único fichero que escribes es `docs/roadmap/BACKLOG.md`.
- **No planifiques ni implementes.** Para ejecutar una iniciativa concreta, remite a `/dev-cycle` sobre su carpeta.
- **Cifras honestas.** Usa lo que hay en las evaluaciones; marca lo que falte como "sin evaluar", no lo estimes aquí.
- **Confluence (opt-in):** si el proyecto sincroniza `docs/`, ofrece publicar `BACKLOG.md` vía `confluence-publish`; no lo fuerces.
