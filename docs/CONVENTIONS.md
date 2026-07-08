# Convención de organización — agentes custom

Reglas para añadir agentes sin que se pisen entre sí, permitiendo que unos dependan de otros o de recursos compartidos. **Léela antes de crear o mover nada.**

## 1. Principio

Tres tipos de artefacto, tres ubicaciones fijas. Lo **compartido** vive en carpetas comunes por nombre único; lo **privado** de un agente vive en su propio namespace. La documentación va **siempre** en `docs/`, nunca junto al código.

```
custom-agents/               (raíz; se despliega como .claude/ del proyecto)
├── agents/<agente>.md       # definición del agente (uno por fichero, plano)
├── skills/<skill>/          # skills COMPARTIDAS (reutilizables por varios agentes)
├── agent-kits/<agente>/     # toolkit PRIVADO de un agente (scripts, plantillas)
└── docs/                    # TODA la documentación
    ├── README.md            # índice maestro (actualízalo al añadir un agente)
    ├── CONVENTIONS.md       # este documento
    ├── INSTALL.md           # despliegue del bundle
    └── agents/<agente>*.md  # documentación por agente
```

## 2. Nomenclatura (evita colisiones)

- **Un agente = un nombre en kebab-case** (`nemesis`, `code-reviewer`, `db-migrator`). Ese nombre es la clave única en todo el repo.
- El fichero del agente es `agents/<nombre>.md` y su `name:` en el frontmatter **debe** coincidir con `<nombre>`.
- El toolkit privado de un agente va en `agent-kits/<nombre>/` — mismo nombre. Así nunca chocan dos toolkits.
- Las skills se nombran por **función**, no por agente (`cybersecurity`, no `nemesis-sast`), porque están pensadas para reutilizarse.
- La documentación de un agente vive en `docs/agents/<nombre>.md` (+ ficheros auxiliares con prefijo `<nombre>-`, p. ej. `nemesis-presentacion.md`).

## 3. Compartido vs. privado — cómo decidir

| ¿Lo usará más de un agente? | Dónde va |
|-----------------------------|----------|
| Sí (o está pensado para reutilizar) | `skills/<skill>/` — compartido |
| No, es específico de un agente | `agent-kits/<agente>/` — privado |

Regla práctica: si dudas, empieza en el kit privado. Promociónalo a `skills/` el día que un segundo agente lo necesite (y actualiza las dependencias de ambos).

## 4. Dependencias — se declaran en el frontmatter del agente

Cada agente declara de qué depende en su propio `agents/<nombre>.md`. Fuente de verdad única, junto al agente.

```yaml
---
name: nemesis
description: ...
tools: Read, Grep, Glob, Bash, Write, Edit, WebFetch, Agent
dependencies:
  skills:            # skills de skills/ que necesita
    - cybersecurity
  kits:              # toolkits privados de agent-kits/ que usa
    - agent-kits/nemesis
  agents: []         # otros agentes de los que depende (por nombre)
---
```

Notas:

- Las claves `name`, `description`, `tools` (y `model`) son las que interpreta Claude Code. `dependencies` es **informativo**: Claude Code ignora claves extra, y nos sirve a nosotros (y a scripts) para ver el grafo de un vistazo.
- Un agente **puede** depender de otro (campo `agents`). Referéncialo por su nombre; el otro agente debe existir en `agents/`. Evita ciclos (A→B→A).
- Un kit privado (`agent-kits/<x>/`) es de su agente; si otro agente lo necesita, es señal de que ese código debería ser una skill compartida (ver §3).

## 5. Rutas dentro del código

- Los scripts de un kit se localizan entre sí con **rutas relativas** (`dirname "$BASH_SOURCE"`), nunca con rutas absolutas del repo. Así renombrar/mover el kit no rompe nada interno.
- **Cuando el agente (`.md`) invoca su toolkit o plantillas, NO uses rutas fijas** tipo `.claude/agent-kits/...`: solo funcionan a nivel proyecto y se rompen a nivel usuario o como plugin (además, `${CLAUDE_PLUGIN_ROOT}` no se expande en markdown de agentes/skills). Resuelve el kit en tiempo de ejecución con `find` sobre ambos scopes:

  ```bash
  MIKIT="$(find "$PWD/.claude" "$HOME/.claude" -type d -path '*agent-kits/<nombre>' 2>/dev/null | head -1)"
  # luego usa "$MIKIT/tools/..." , "$MIKIT/templates/..." , etc.
  ```

  `$PWD/.claude` cubre el scope proyecto; `$HOME/.claude` cubre tanto usuario (`~/.claude/`) como el caché de plugins (`~/.claude/plugins/…`). El proyecto va primero → gana si hay varias copias (misma precedencia que Claude Code).
- Skills compartidas: invócalas con la herramienta Skill (por nombre). Si necesitas leer un fichero suyo, resuélvelo igual: `find "$PWD/.claude" "$HOME/.claude" -type f -path '*skills/<skill>/...'`.

## 6. Checklist para añadir un agente nuevo

1. Elige un nombre único en kebab-case.
2. Crea `agents/<nombre>.md` con frontmatter (incluido el bloque `dependencies`).
3. Si necesita scripts propios → `agent-kits/<nombre>/`. Si es reutilizable → `skills/<skill>/`.
4. Escribe la doc en `docs/agents/<nombre>.md`.
5. Añade la fila correspondiente en `docs/README.md` (agentes y, si aplica, skills).
6. Verifica que no haya rutas absolutas rotas ni nombres duplicados.

## 7. Cadena de artefactos: spec → evaluación → plan

Los agentes `evaluator` y `planner` producen artefactos en el proyecto, enlazados en una cadena. **Comparten `<slug>`** para que sea trazable de punta a punta.

```
docs/specs/<slug>.md                          # QUÉ se quiere (especificación)
   └─ docs/evaluations/<fecha>-<slug>/evaluation.md   # CUÁNTO cuesta / si conviene
         └─ docs/plans/<fecha>-<slug>/improvement-plan.md (+ TASKS.md)  # CÓMO se ejecuta
```

Estados por artefacto (vocabularios distintos, a propósito):

- **spec:** `borrador` · `aprobada` · `implementada` · `obsoleta`.
- **evaluación / plan:** `borrador` 📝 · `en-progreso` 🚧 · `en-revision` 🔍 · `completado` ✅ · `cancelado` ❌.

Reglas de enlazado (**bidireccional** y **se informa según se crea**):

- La `spec` lleva en su frontmatter `evaluacion:` y `plan:` (o `pendiente`), más callouts al inicio.
- La `evaluation.md` lleva filas **Spec** y **Plan**; el `improvement-plan.md` lleva filas **Spec** y **Evaluación**.
- Al **crear la evaluación** desde una spec: rellena su fila **Spec** y **actualiza la spec** (`evaluacion:` + callout) para que apunte a la evaluación.
- Al **crear el plan** desde una evaluación/spec: rellena sus filas **Spec/Evaluación** y **actualiza hacia atrás** el `plan:` de la spec y la fila **Plan** de la evaluación.
- Rutas de enlace **relativas** entre carpetas de `docs/` (p. ej. desde `docs/evaluations/<f>-<slug>/` a la spec: `../../specs/<slug>.md`).
