# Flujos del plugin — diagramas

Visión visual de cómo encajan agentes, comandos y skills. Los diagramas son Mermaid
(se renderizan en GitHub y editores compatibles).

**Leyenda:** flecha **continua** = flujo principal · flecha **punteada** = opcional, retorno o feedback · rombo = decisión/puerta · verde = camino de avance (*go*/verde) · rojo = rechazo o vuelta atrás (*no-go*/rojo).

## 0 · Mapa general — quién usa qué

```mermaid
flowchart TD
    PM(["👤 PM / producto"]) --> S0["/setup"]
    PM --> P1["/pm-cycle\ndefine y presupuesta"]
    PM --> P2["/pm-backlog\nprioriza cartera"]
    PM --> P3["/confluence-pull\ndocs sin git"]
    DEV(["👩‍💻 Dev / equipo"]) --> D1["/dev-cycle\nconstruye"]
    DEV --> D2["/retro\naprende"]
    DIR(["👔 Dirección"]) --> V1["/roadmap-brief\none-pager PDF"]
    TODOS(["👀 Cualquiera"]) --> V2["/roadmap-status\ndashboard"]
    TODOS --> V3["/roadmap-metrics\nreal vs estimado"]
    TODOS --> V4["/roadmap-live\nJira en vivo"]
    P1 -->|go| D1
    D1 --> V3
    D2 -.->|CALIBRATION.md| P1
```

## 1 · La cadena completa de una iniciativa

Fase de **producto**: `analyst → evaluator`. Fase de **desarrollo**: `planner → implementer → qa`.

```mermaid
flowchart LR
    idea(["💡 Idea / petición"]) --> analyst["🗣️ analyst\ntoma de requerimientos"]
    analyst -->|spec aprobada| evaluator["💶 evaluator\npresupuesta"]
    evaluator -->|go| planner["🗺️ planner\nplan + tasks"]
    evaluator -.->|no-go| fin1(["✋ se descarta"])
    planner --> implementer["⚙️ implementer\ncódigo + ledger"]
    implementer --> qa["✅ qa\nE2E Playwright"]
    qa -->|verde| documenter["📚 documenter\ndocs del proyecto"]
    qa -.->|rojo| implementer
    documenter --> retro["🔁 /retro\ncalibración"]
    nemesis["🛡️ nemesis\nauditoría"] -.->|hallazgos críticos| analyst
    retro -.->|CALIBRATION.md| evaluator
    style fin1 fill:#fdecea,stroke:#ef9a9a
    style documenter fill:#e8f5e9,stroke:#81c784
```

Todo vive en **una carpeta por iniciativa**: `docs/roadmap/<fecha>-<slug>/`
(`spec.md → evaluation.md → improvement-plan.md + tasks.md → testing/ → retro.md`).

## 2 · `/pm-cycle` — rol producto (define y presupuesta, cierra en la puerta)

```mermaid
flowchart TD
    A["/pm-cycle objetivo"] --> B{"¿objetivo\nbien definido?"}
    B -->|no| C["skill discovery / @analyst\nentrevista → spec.md"]
    B -->|sí| D["evaluator\nspec + evaluation.md"]
    C --> D
    D --> E{"puerta\ngo / no-go"}
    E -->|no-go| F["evaluación → cancelado\nspec → obsoleta"]
    E -->|a revisar| C
    E -->|go| G["spec → aprobada\nevaluación → completado"]
    G --> H["salidas opt-in:\n📄 brief PDF · 🎫 épica en Jira"]
    H --> I(["ofrece handoff a /dev-cycle\nsin ejecutarlo"])
    style F fill:#fdecea,stroke:#ef9a9a
    style G fill:#e8f5e9,stroke:#81c784
    style I fill:#e8f5e9,stroke:#81c784
```

## 3 · `/dev-cycle` — ciclo de desarrollo (con puertas)

```mermaid
flowchart TD
    A["/dev-cycle objetivo"] --> B{"¿carpeta con\nspec+evaluación\nde /pm-cycle?"}
    B -->|sí| D
    B -->|no| C["evaluator → puerta go/no-go"]
    C -->|go| D["planner\nimprovement-plan + tasks.md"]
    C -->|no-go| X(["parar"])
    D --> E["opt-in: volcar plan a Jira\njira-sync: 1 issue por tarea"]
    E --> F{"¿superpowers\ninstalado?"}
    F -->|Modo A| G["superpowers ejecuta\ncontra TU tasks.md"]
    F -->|Modo B| H["implementer\ntarea a tarea"]
    G --> I["qa · E2E local"]
    H --> I
    I -->|rojo| H
    I -->|verde| J["documenter\nuna vez al final"]
    J --> K["opcional: nemesis\nauditoría"]
    K --> L(["cierre: plan completado\nspec implementada"])
    style X fill:#fdecea,stroke:#ef9a9a
    style L fill:#e8f5e9,stroke:#81c784
```

`tasks.md` es el **ledger canónico** de progreso en los dos modos.

## 4 · Jira (opt-in) — volcado del plan al crearlo

```mermaid
flowchart TD
    A["selector de destino\nartefacto en Cowork /\nconversacional en CLI"] --> B{"¿padre?"}
    B -->|épica nueva| C["crear Épica\n+ Tareas debajo"]
    B -->|issue existente| D{"nivel del padre\ndescubierto"}
    B -->|sin padre| E["Tareas sueltas\nen el proyecto"]
    D -->|épica / iniciativa| C2["Tareas"]
    D -->|tarea / historia| C3["Subtareas"]
    C --> F["dry-run + confirmación\n→ crear issues\nclaves → tasks.md"]
    C2 --> F
    C3 --> F
    E --> F
    O["/roadmap-live\nestado en vivo por label"] -.->|lee| F
```

## 4b · Jira (opt-in) — imputación al completar cada tarea

```mermaid
flowchart TD
    G["tarea completado\nen tasks.md"] --> H["worklog.py plan\nIA + supervisión, real→est"]
    H --> I{"¿cabe en la\njornada de hoy?"}
    I -->|sí| J["imputar worklog\n+ issue → Done"]
    I -->|no| K{"política"}
    K -->|banco| L["imputar resto de hoy\nexceso → banco por issue\nse paga en días siguientes"]
    K -->|parar| M["imputar resto\ny DETENER implementación"]
    K -->|seguir| N["imputar todo\naunque supere jornada"]
    P["read-back\nJira → tasks.md con confirmación"] -.-> G
```

## 5 · Confluence — bidireccional (opt-in)

```mermaid
flowchart LR
    A["docs/ local: escriben los agentes\nevaluator · planner · qa · documenter"] -->|hook marca pendiente| C["confluence-publish\nmanifiesto hash+pageId\ncrear/actualizar sin duplicar"]
    B["dashboard.md\nregenerado si cambia el roadmap"] --> C
    C --> D[("🌐 Confluence\nárbol de páginas")]
    D -->|"confluence-pull · PM sin git"| E["docs/ local al día\npreserva frontmatter\navisa de conflictos"]
    D -.->|no permite borrar| F["página obsoleta\n→ borrado manual"]
```

## 6 · Visibilidad y aprendizaje (todo solo-lectura)

```mermaid
flowchart TD
    R[("docs/roadmap/*/\nspec · evaluación · plan · tasks")] --> S["/roadmap-status\ndashboard HTML + md"]
    R --> T["/pm-backlog\nprioriza la cartera\nBACKLOG.md"]
    R --> U["/roadmap-metrics\nreal vs estimado\nmetrics.md"]
    S --> V["/roadmap-brief\none-pager PDF\npara dirección"]
    T --> V
    U --> V
    J[("Jira\nissues + worklogs")] --> W["/roadmap-live\nestado en tiempo real"]
    U --> X["/retro por iniciativa\ncausas de desviación"]
    X --> Y[("CALIBRATION.md")]
    Y -->|calibra estimaciones| Z["evaluator"]
```

## 7 · Configuración (una pasada con `/setup`)

```mermaid
flowchart LR
    A["/setup"] --> B[".claude/rates.json\ntarifa · tokens · jornada · ratios\nla leen evaluator, planner y jira-sync"]
    A --> C[".claude/confluence.json\nopt-in + destino"]
    A --> D[".claude/jira.json\nopt-in + política de jornada"]
    C -.->|estado| E[".claude/confluence-state.json"]
    D -.->|estado| F[".claude/jira-state.json\nmapeo · imputado/día · banco"]
```

Detalle de cada fichero: regla 9 de [`CONVENTIONS.md`](CONVENTIONS.md). Comportamientos del
conector Atlassian: [`atlassian-connector-notes.md`](atlassian-connector-notes.md).

> **Nota (Confluence):** si esta página se publica en Confluence vía `confluence-publish`, los
> diagramas Mermaid solo se dibujan si el espacio tiene una app/macro de Mermaid instalada; si no,
> se verá el código fuente del diagrama. En GitHub y editores compatibles se renderizan siempre.

> **Mantenimiento:** al añadir o cambiar un agente, comando o skill, actualiza el diagrama
> correspondiente de este documento (ver checklist de `CONVENTIONS.md`).
