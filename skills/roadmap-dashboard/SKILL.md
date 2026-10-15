---
name: roadmap-dashboard
description: Escanea docs/roadmap/<fecha>-<slug>/ y calcula los datos de cartera de cada iniciativa (spec/evaluación/plan/tasks/testing) con estados, prioridad y presupuesto (coste €, esfuerzo, tokens), como dashboard.md para Confluence, informe real-vs-estimado y resumen JSON que consumen otros comandos. No genera HTML (la presentación es de plugin-panel) y no modifica los ficheros del roadmap. Úsala cuando el usuario diga "estado del roadmap", "cómo van las iniciativas", o desde los comandos /roadmap-status, /pm-backlog y /roadmap-metrics.
---

# Skill: roadmap-dashboard

Convierte la carpeta de iniciativas `docs/roadmap/` en una vista de un vistazo. **Solo lee**;
nunca edita spec/evaluación/plan. Es dueña de los **datos de cartera** (`ROLES.md`): `/roadmap-status` los pasa
a `dashboard.md` y exporta el panel (skill `plugin-panel`, dueña de la presentación HTML) y
`/pm-backlog` consume el JSON.

## Qué produce

- **Markdown** (`--md RUTA`): el mismo estado en tablas Markdown, pensado para **publicarse como
  página de Confluence** (lo espeja `confluence-publish`). Lleva la marca `generado <fecha/hora>`.
- **Métricas real vs estimado** (`--metrics-md RUTA`): informe que compara, por iniciativa y en total, la **producción** (Tiempo IA ejec. + Supervisión), horas humanas y tokens **reales vs estimados** (de la fila TOTAL de cada `tasks.md`), con desviaciones. Incluye además la sección **Coste de proceso**: lo que costó *producir* los artefactos del ciclo (spec/eval/plan/tasks) según el bloque `generacion:` de su frontmatter (medido por `usage-meter`, kit shared) — separado del coste de implementación; artefactos sin bloque salen como "sin datos", nunca como 0. Lo usa `/roadmap-metrics`.
- **JSON** (`--json`): lista de iniciativas con todos esos campos (incluye `progreso`: real/est parseado de `tasks.md`), para consumir desde otro comando.

## Cómo se ejecuta

Localiza el script sin depender del scope (proyecto/usuario/plugin) — regla 5 de `docs/CONVENTIONS.md`:

```bash
DASHKIT="$(find "$PWD/.claude" "$PWD/.codex" "$PWD/.opencode" "$HOME/.claude" "$HOME/.codex" "$HOME/.config/opencode" -type f -path '*skills/roadmap-dashboard/scripts/build_dashboard.py' 2>/dev/null | head -1)"

# Markdown (para Confluence) — lo usa /roadmap-status
python3 "$DASHKIT" --root docs/roadmap --md docs/roadmap/dashboard.md

# Informe real vs estimado (lo usa /roadmap-metrics)
python3 "$DASHKIT" --root docs/roadmap --metrics-md docs/roadmap/metrics.md

# Resumen JSON (lo usa /pm-backlog)
python3 "$DASHKIT" --root docs/roadmap --json
```

## Publicación en Confluence (para PMs sin git)

El `dashboard.md` es la vía para que un PM vea el **estado real** sin git ni herramientas: la skill
`confluence-publish`, **antes de publicar**, regenera `docs/roadmap/dashboard.md` cuando el roadmap
ha cambiado y lo espeja como una página más del árbol. Un `dashboard.html` antiguo ya no se genera ni se
publica (si existe, queda donde estaba: nada lo borra). No es tiempo real: la página se refresca en la misma
publicación que provocó el cambio, y su fecha de generación deja clara la frescura.

Requiere Python 3 (stdlib, sin paquetes). Si `docs/roadmap/` no existe, sale con código 2 y no
crea nada. Con cero iniciativas, el `.md` lo dice y enlaza `/pm-cycle`.

## Cómo lee cada iniciativa

- **spec.md** → frontmatter (`estado`, `descripcion`, `creado`, `actualizado`) + primer `# título`.
- **evaluation.md** → filas de la tabla de cabecera (`Estado`, `Prioridad global`, `Características`) y del **Cuadro de mando** (`Coste` o `Coste humano a N EUR/h` / `Coste humano (N EUR/h)`; `Esfuerzo humano` o `Tiempo humano`; `Tokens IA`; `Multiplicador productividad`). Sin fila `Estado`, lee `estado:` del frontmatter. Una evaluación sin tabla de coste (solo prosa) da coste y esfuerzo nulos y un aviso que nombra la evaluación; los valores se conservan como texto (la coma de «1,300 EUR» es de miles).
- Presencia de `improvement-plan.md`, `tasks.md` y `testing/` → artefactos y fase.

El esquema de estados es el del repo (regla 7 de `docs/CONVENTIONS.md`):
spec = `borrador · aprobada · implementada · obsoleta`;
evaluación/plan = `borrador · en-progreso · en-revision · completado · cancelado`.

## Regenerar

No hay refresco automático: vuelve a ejecutar `/roadmap-status` (o el comando de arriba) para
reflejar los cambios. El `.md` lleva la marca de tiempo de generación.

> **Cuántos números son una medida.** El informe de `--metrics-md` cierra la sección de coste de proceso con «N de M bloques `generacion:` con `fuente: estimado`» (`contar_fuentes`), y el `--json` trae `estimados`/`medidos`/`generacion_total` por iniciativa. Arista E7 de `docs/agents/CONTRACTS.md`. Las claves de procedencia/cobertura de `usage-meter.py close` (D-086) se agregan aparte (`procedencia_generacion`/`procedencia_cartera`): columna «Procedencia», línea «Procedencia (cartera)» y clave `procedencia` del `--json`; un bloque sin ellas es «procedencia desconocida», nunca medido (ver `docs/observability.md`).
