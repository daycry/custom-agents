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
6. **Actualiza los diagramas de `docs/FLOWS.md`** si el agente/comando/skill cambia algún flujo.
7. Verifica que no haya rutas absolutas rotas ni nombres duplicados.

## 7. Cadena de artefactos: spec → evaluación → plan (carpeta única por iniciativa)

Los agentes `evaluator` y `planner` producen sus artefactos en **una sola carpeta por iniciativa**: `docs/roadmap/<fecha>-<slug>/`. Todo lo de una iniciativa vive junto.

```
docs/roadmap/<fecha>-<slug>/
├── spec.md              # QUÉ se quiere (especificación)
├── evaluation.md        # CUÁNTO cuesta / si conviene
├── improvement-plan.md  # CÓMO se ejecuta
├── tasks.md             # checklist de tareas del plan
└── testing/             # (opcional) salida del agente qa
```

Una evaluación **no-go** deja solo `spec.md` + `evaluation.md` (sin ficheros de plan). Índice único: `docs/roadmap/README.md`.

Estados por artefacto (vocabularios distintos, a propósito):

- **spec:** `borrador` · `aprobada` · `implementada` · `obsoleta`.
- **evaluación / plan:** `borrador` · `en-progreso` · `en-revision` · `completado` · `cancelado`.

**Transiciones a lo largo del ciclo (no dejar en `borrador`).** Todo artefacto nace en `borrador`,
pero cada fase que se supera **debe** moverlo al estado que toca (lo garantiza `/dev-cycle`, y los
agentes al ejecutarse sueltos):

- Tras **evaluar**: evaluación → `en-revision`. En la puerta **go**: spec → `aprobada`, evaluación → `completado`. En **no-go**: evaluación → `cancelado` (spec → `obsoleta` si se descarta).
- Al **crear el plan**: plan/tasks → `borrador`. Al **arrancar la implementación** (OK del plan): plan y fase activa → `en-progreso`.
- Durante la **implementación**: cada tarea `en-progreso` → `completado`; la fase → `completado` al cerrar sus tareas.
- En el **cierre** (qa en verde + documentado): plan → `completado` y spec → `implementada`.
- **Cancelación** en cualquier punto: plan/evaluación → `cancelado` (spec → `obsoleta` si aplica).

Reglas de enlazado (**bidireccional**, y como todo está en la misma carpeta, los enlaces son **nombres simples**):

- La `spec` lleva en su frontmatter `evaluacion: evaluation.md` y `plan: improvement-plan.md` (o `pendiente`), más callouts al inicio.
- La `evaluation.md` lleva filas **Spec** (`spec.md`) y **Plan** (`improvement-plan.md`); el `improvement-plan.md` lleva filas **Spec** (`spec.md`) y **Evaluación** (`evaluation.md`).
- Al **crear la evaluación**: rellena su fila **Spec** y **actualiza la spec** (`evaluacion:` + callout) para que apunte a la evaluación.
- Al **crear el plan**: rellena sus filas **Spec/Evaluación** y **actualiza hacia atrás** el `plan:` de la spec y la fila **Plan** de la evaluación.

## 8. Progreso de un plan: `tasks.md` es el ledger canónico

El avance de un plan se registra en **un único sitio**: `docs/roadmap/<fecha>-<slug>/tasks.md`
(checkbox + estado por tarea T-XX + tabla de resumen). Es la **fuente única de verdad**.

- **Cualquier implementador** debe actualizar `tasks.md` al completar cada tarea: el agente `implementer`, el chat principal, o un **orquestador externo** (p. ej. *superpowers subagent-driven-development*).
- Si una herramienta lleva su propio registro (todo-list interna, `.superpowers/sdd/progress.md`, etc.), ese registro es **espejo**, no fuente: `tasks.md` manda. Ante discrepancia, gana `tasks.md`.
- El orquestador `/dev-cycle` y el agente `implementer` aplican esta regla de serie. Para que la respeten orquestadores externos, `/dev-cycle` ofrece añadir esta regla al `CLAUDE.md` del proyecto consumidor.
- **Estados con motor externo (p. ej. superpowers):** cuando la implementación se delega a un orquestador externo, ese motor **no** actualiza tus artefactos. Por tanto, `/dev-cycle` (o tú) aplica las **transiciones de estado** de la regla 7 y mantiene `tasks.md` al día en su nombre. Las transiciones valen igual haya o no motor externo.
- El cierre del ciclo (documentación con `documenter`) se hace **una vez** tras implementar y con `qa` en verde, no tarea a tarea.

## 9. Ficheros de config/estado en `.claude/` del proyecto consumidor

Cada skill guarda su config (decisiones del usuario) y su estado (memoria de máquina) en
`.claude/` del proyecto. Mapa único — quién escribe qué y cómo se recupera si se pierde:

| Fichero | Qué es | Lo escribe | Si se corrompe/pierde |
|---|---|---|---|
| `rates.json` | Config compartida de presupuesto (tarifa, tokens, jornada, ratios) | `/setup` o a mano | Recrear desde `agent-kits/evaluator/templates/rates.example.json` |
| `confluence.json` | Opt-in + destino de publicación (espacio/anclaje) | skill `confluence-publish` | Relanzar el alta guiada (elige espacio de nuevo) |
| `confluence-state.json` | Manifiesto página↔fichero (hash + pageId) | `confluence-publish`/`pull` | Se reconstruye: publish busca por título bajo el anclaje antes de crear |
| `jira.json` | Opt-in + política de jornada (`alCubrirJornada`) | skill `jira-sync` o `/setup` | Recrear con `/setup`; defaults seguros |
| `jira-state.json` | Mapeo T-XX↔issue, imputado por día, banco de horas | `jira-sync` (vía `worklog.py`) | Mapeo: re-derivable de las claves anotadas en `tasks.md`; imputado/banco: revisar worklogs en Jira |
| `.confluence-pending` | Marca efímera del hook (hay docs sin sincronizar) | hook `PostToolUse` | Borrarla es inocuo; la skill re-detecta por manifiesto |

Reglas: **config ≠ estado** (la config la decide el usuario; el estado lo mantiene la máquina y
nunca se edita a mano); toda skill nueva que necesite memoria sigue este patrón (`<skill>.json` +
`<skill>-state.json`) y añade su fila aquí.
