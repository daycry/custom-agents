---
name: roadmap-dashboard
description: Escanea docs/roadmap/<fecha>-<slug>/ y genera un dashboard HTML autocontenido con el estado de cada iniciativa (spec/evaluación/plan/tasks/testing), sus estados, prioridad y presupuesto (coste €, esfuerzo, tokens). También puede volcar un resumen JSON para que otros comandos prioricen. No modifica los ficheros del roadmap. Úsala cuando el usuario diga "estado del roadmap", "dashboard del roadmap", "cómo van las iniciativas", "panel del roadmap", o desde los comandos /roadmap-status y /pm-backlog.
---

# Skill: roadmap-dashboard

Convierte la carpeta de iniciativas `docs/roadmap/` en una vista de un vistazo. **Solo lee**;
nunca edita spec/evaluación/plan. Es la fuente del comando `/roadmap-status` (HTML) y una entrada
útil para `/pm-backlog` (JSON).

## Qué produce

- **HTML** (`--html RUTA`): tablero autocontenido (un solo fichero, sin dependencias), una tarjeta
  por iniciativa con: título, slug, descripción, estado de la spec y de la evaluación, prioridad,
  fase derivada (solo spec · evaluada · planificada · en pruebas), métricas del cuadro de mando
  (coste €, esfuerzo, tokens, multiplicador, nº de características) y qué artefactos existen.
  Es la **vista local**.
- **Markdown** (`--md RUTA`): el mismo estado en tablas Markdown, pensado para **publicarse como
  página de Confluence** (lo espeja `confluence-publish`). Lleva la marca `generado <fecha/hora>`.
- **JSON** (`--json`): lista de iniciativas con todos esos campos, para consumir desde otro comando.

## Cómo se ejecuta

Localiza el script sin depender del scope (proyecto/usuario/plugin) — regla 5 de `docs/CONVENTIONS.md`:

```bash
DASHKIT="$(find "$PWD/.claude" "$HOME/.claude" -type f -path '*skills/roadmap-dashboard/scripts/build_dashboard.py' 2>/dev/null | head -1)"

# Dashboard HTML (vista local) + Markdown (para Confluence) — lo usa /roadmap-status
python3 "$DASHKIT" --root docs/roadmap --html docs/roadmap/dashboard.html --md docs/roadmap/dashboard.md

# Resumen JSON (lo usa /pm-backlog)
python3 "$DASHKIT" --root docs/roadmap --json
```

## Publicación en Confluence (para PMs sin git)

El `dashboard.md` es la vía para que un PM vea el **estado real** sin git ni herramientas: la skill
`confluence-publish`, **antes de publicar**, regenera `docs/roadmap/dashboard.md` cuando el roadmap
ha cambiado y lo espeja como una página más del árbol. Solo el `.md` viaja a Confluence; el `.html`
(no es `.md`) se queda como vista local. No es tiempo real: la página se refresca en la misma
publicación que provocó el cambio, y su fecha de generación deja clara la frescura.

Requiere Python 3 (stdlib, sin paquetes). Si `docs/roadmap/` no existe, sale con código 2 y no
crea nada. Con cero iniciativas genera un HTML con un mensaje vacío y un enlace a `/pm-cycle`.

## Cómo lee cada iniciativa

- **spec.md** → frontmatter (`estado`, `descripcion`, `creado`, `actualizado`) + primer `# título`.
- **evaluation.md** → filas de la tabla de cabecera (`Estado`, `Prioridad global`, `Características`) y del **Cuadro de mando** (`Coste`, `Esfuerzo humano`, `Tokens IA`, `Multiplicador productividad`).
- Presencia de `improvement-plan.md`, `tasks.md` y `testing/` → artefactos y fase.

El esquema de estados es el del repo (regla 7 de `docs/CONVENTIONS.md`):
spec = `borrador · aprobada · implementada · obsoleta`;
evaluación/plan = `borrador · en-progreso · en-revision · completado · cancelado`.

## Regenerar

No hay refresco automático: vuelve a ejecutar `/roadmap-status` (o el comando de arriba) para
reflejar los cambios. El HTML lleva la marca de tiempo de generación.
