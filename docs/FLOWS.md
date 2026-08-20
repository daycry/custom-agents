# Flujos del plugin — diagramas

[English](en/FLOWS.md) · **Español**

Visión visual de cómo encajan agentes, comandos y skills. Los diagramas son Mermaid
(se renderizan en GitHub y editores compatibles).

**Leyenda:** flecha **continua** = flujo principal · flecha **punteada** = opcional, retorno o feedback · rombo = decisión/puerta · verde = camino de avance (*go*/verde) · rojo = rechazo o vuelta atrás (*no-go*/rojo).

## 0 · Mapa general — quién usa qué

```mermaid
flowchart TD
    PM(["👤 PM / producto"]) --> S0["/setup"]
    PM --> P1["/pm-cycle<br/>define y presupuesta"]
    PM --> P2["/pm-backlog<br/>prioriza cartera"]
    PM --> P3["/confluence-pull<br/>docs sin git"]
    DEV(["👩‍💻 Dev / equipo"]) --> D1["/dev-cycle<br/>construye"]
    DEV --> D2["/retro<br/>aprende"]
    DIR(["👔 Dirección"]) --> V1["/roadmap-brief<br/>one-pager PDF"]
    TODOS(["👀 Cualquiera"]) --> V2["/roadmap-status<br/>dashboard"]
    TODOS --> V3["/roadmap-metrics<br/>real vs estimado"]
    TODOS --> V4["/roadmap-live<br/>Jira en vivo"]
    P1 -->|go| D1
    D1 --> V3
    D2 -.->|CALIBRATION.md| P1
```

## 1 · La cadena completa de una iniciativa

Fase de **producto**: `analyst → evaluator`. Fase de **desarrollo**: `planner → implementer → qa`.

```mermaid
flowchart LR
    idea(["💡 Idea / petición"]) --> analyst["🗣️ analyst<br/>toma de requerimientos"]
    analyst -->|spec aprobada| evaluator["💶 evaluator<br/>presupuesta"]
    evaluator -->|go| planner["🗺️ planner<br/>plan + tasks"]
    evaluator -.->|no-go| fin1(["✋ se descarta"])
    planner --> implementer["⚙️ implementer<br/>código + ledger"]
    implementer --> review["🔍 revisión adversarial<br/>(2 lentes en paralelo,<br/>contexto fresco) diff vs plan"]
    review -->|sin gaps| qa["✅ qa<br/>E2E Playwright"]
    review -.->|gaps de corrección| implementer
    qa -->|verde| documenter["📚 documenter<br/>docs del proyecto"]
    qa -.->|rojo| implementer
    documenter --> retro["🔁 /retro<br/>calibración"]
    nemesis["🛡️ nemesis<br/>auditoría"] -.->|hallazgos críticos| analyst
    retro -.->|CALIBRATION.md| evaluator
    style fin1 fill:#fdecea,stroke:#ef9a9a
    style documenter fill:#e8f5e9,stroke:#81c784
```

Todo vive en **una carpeta por iniciativa**: `docs/roadmap/<fecha>-<slug>/`
(`spec.md → evaluation.md → improvement-plan.md + tasks.md → testing/ → retro.md`).

## 2 · `/pm-cycle` — rol producto (define y presupuesta, cierra en la puerta)

```mermaid
flowchart TD
    A["/pm-cycle objetivo"] --> B{"¿objetivo<br/>bien definido?"}
    B -->|no| C["skill discovery / @analyst<br/>entrevista → spec.md"]
    B -->|sí| D["evaluator<br/>spec + evaluation.md"]
    C --> D
    D --> E{"puerta<br/>go / no-go"}
    E -->|no-go| F["evaluación → cancelado<br/>spec → obsoleta"]
    E -->|a revisar| C
    E -->|go| G["spec → aprobada<br/>evaluación → completado"]
    G --> H["salidas opt-in:<br/>📄 brief PDF · 🎫 épica en Jira"]
    H --> I(["ofrece handoff a /dev-cycle<br/>sin ejecutarlo"])
    style F fill:#fdecea,stroke:#ef9a9a
    style G fill:#e8f5e9,stroke:#81c784
    style I fill:#e8f5e9,stroke:#81c784
```

## 3 · `/dev-cycle` — ciclo de desarrollo (con puertas)

> **Puerta de entrada (Fase 0-bis):** `/dev-cycle` pregunta primero **flujo completo** vs **vía rápida**. La vía rápida salta evaluator+planner (crea un `tasks.md` ligero) y entra directa en implementación, pero mantiene revisión de dos lentes + qa.
>
> **Dos puertas de entrada al mismo gate:** el command `/dev-cycle` (explícito, con la barra) y la skill `quick-implement`, que se auto-invoca por lenguaje natural («implementa X rápido») y entra por la rama de vía rápida tras su filtro de idoneidad. La skill no define método propio: delega en esta misma Fase 0-bis.

```mermaid
flowchart TD
    NL(["petición en lenguaje natural<br/>«implementa X rápido»"]) -.->|"skill quick-implement<br/>(filtro de idoneidad)"| Z
    A["/dev-cycle objetivo"] --> Z{"flujo completo<br/>o vía rápida?"}
    Z -->|vía rápida| Q["tasks.md ligero<br/>(sin spec/eval/plan)"]
    Q --> H
    Z -->|completo| B{"¿carpeta con<br/>spec+evaluación<br/>de /pm-cycle?"}
    B -->|sí| D
    B -->|no| C["evaluator → puerta go/no-go"]
    C -->|go| D["planner<br/>improvement-plan + tasks.md"]
    C -->|no-go| X(["parar"])
    D --> E["opt-in: volcar plan a Jira<br/>jira-sync: 1 issue por tarea"]
    E --> F{"¿pidió el usuario<br/>un motor externo<br/>explícitamente?"}
    F -->|"sí (opt-in explícito)"| G["motor externo ejecuta<br/>contra TU tasks.md<br/>(review propio)"]
    F -->|"no (defecto):<br/>cadena NATIVA"| H["implementer<br/>tarea a tarea<br/>(dev.json opt-in: TDD ·<br/>worktree · subagentes frescos)"]
    H --> R["🔍 revisión adversarial<br/>DOS lentes en paralelo:<br/>spec-conformidad · calidad<br/>(fusión + dedupe)"]
    R -.->|gaps| H
    G --> I["qa · E2E local<br/>veredicto: qa-gate.py"]
    R --> I
    I -->|"rojo (máx. 3 intentos,<br/>luego preguntar)"| H
    I -->|verde| J["documenter<br/>una vez al final"]
    J --> K["opcional: nemesis<br/>auditoría"]
    K --> L(["cierre: plan completado<br/>spec implementada"])
    style X fill:#fdecea,stroke:#ef9a9a
    style L fill:#e8f5e9,stroke:#81c784
```

`tasks.md` es el **ledger canónico** de progreso en los dos modos.

## 4 · Jira (opt-in) — volcado del plan al crearlo

> **Granularidad** (`.claude/jira.json` → `granularidad`): **tarea** = un issue por `T-XX` (defecto); **fase** = un issue por Fase con sus tareas como checklist. En modo fase, comentarios/worklog/Done van al issue de la fase; el issue cierra cuando todas sus tareas están `completado`. Además, el **resultado del revisor** (Modo B) se publica como comentario (por criterio ✓/✗ + nº intentos) y su tiempo se imputa como worklog `[revisión]` aparte — con la granularidad elegida.

```mermaid
flowchart TD
    A["selector de destino<br/>+ granularidad tarea/fase<br/>artefacto o conversacional"] --> B{"¿padre?"}
    B -->|épica nueva| C["crear Épica<br/>+ Tareas debajo"]
    B -->|issue existente| D{"nivel del padre<br/>descubierto"}
    B -->|sin padre| E["Tareas sueltas<br/>en el proyecto"]
    D -->|épica / iniciativa| C2["Tareas"]
    D -->|tarea / historia| C3["Subtareas"]
    C --> F["dry-run + confirmación<br/>→ crear issues<br/>claves → tasks.md"]
    C2 --> F
    C3 --> F
    E --> F
    O["/roadmap-live<br/>estado en vivo por label"] -.->|lee| F
```

## 4b · Jira (opt-in) — imputación al completar cada tarea

```mermaid
flowchart TD
    G["tarea completado<br/>en tasks.md"] --> H["worklog.py plan<br/>IA + supervisión, real→est"]
    H --> I{"¿cabe en la<br/>jornada de hoy?"}
    I -->|sí| J["imputar worklog<br/>+ issue → Done"]
    I -->|no| K{"política"}
    K -->|banco| L["imputar resto de hoy<br/>exceso → banco por issue<br/>se paga en días siguientes"]
    K -->|parar| M["imputar resto<br/>y DETENER implementación"]
    K -->|seguir| N["imputar todo<br/>aunque supere jornada"]
    P["read-back<br/>Jira → tasks.md con confirmación"] -.-> G
```

## 5 · Confluence — bidireccional (opt-in)

```mermaid
flowchart LR
    A["docs/ local: escriben los agentes<br/>evaluator · planner · qa · documenter"] -->|hook marca pendiente| C["confluence-publish<br/>manifiesto hash+pageId<br/>crear/actualizar sin duplicar"]
    B["dashboard.md<br/>regenerado si cambia el roadmap"] --> C
    C --> D[("🌐 Confluence<br/>árbol de páginas")]
    D -->|"confluence-pull · PM sin git"| E["docs/ local al día<br/>preserva frontmatter<br/>avisa de conflictos"]
    D -.->|no permite borrar| F["página obsoleta<br/>→ borrado manual"]
```

> **Política de publicación (2026-08-20-confluence-policy):** opt-out sobre `include: ["**/*.md"]`
> — un documento nuevo se publica salvo que caiga en una exclusión conocida. Detalle normativo y
> tabla completa de exclusiones: `skills/confluence-publish/SKILL.md`, sección "qué sube y qué no".

**Matriz disparador → artefacto → ¿se publica?** (los 10 disparadores conocidos que aplican, o
declaran que no aplican, el paso `agent-kits/shared/confluence-optin.md`):

| Disparador | Artefacto(s) que produce | ¿Se publica? |
|---|---|---|
| `analyst` | `spec.md` | ✅ Sí |
| `evaluator` | `evaluation.md` (+ `spec.md` si lo crea) | ✅ Sí |
| `planner` | `improvement-plan.md`, `tasks.md` | ❌ No — plan y ledger (D1): su sitio es el repo y Jira, no Confluence |
| `implementer` | actualiza `tasks.md` por tarea; dispara la sincronización **al cerrar cada fase** (D3) | ⚠️ El disparo sí ocurre, pero `tasks.md` en sí **no** sube (D1) — refresca lo demás que haya cambiado bajo `docs/` (típicamente `dashboard.md`) |
| `qa` | `testing/report.md` + `report.pdf`, `screenshots/`, `raw/` | ❌ No — `**/testing/**` (D4): el informe embebe capturas que el conector no puede adjuntar; queda solo-local |
| `documenter` | documentación de referencia bajo `docs/` (arquitectura, stack, guías, producto…) | ✅ Sí |
| `/pm-backlog` | `docs/roadmap/BACKLOG.md` | ✅ Sí |
| `/retro` | `retro.md` + `docs/roadmap/CALIBRATION.md` | ✅ Sí |
| `/spec-drift` | `docs/roadmap/DRIFT.md` | ✅ Sí |
| `/roadmap-brief` | `docs/roadmap/brief.md` + `brief.pdf` | ⚠️ El `.md` sí; el `.pdf` no entra en el espejo (no es `.md`) |

**"No" estructurales** (no dependen de un disparador concreto — son exclusiones de la política que
aplican siempre, escriba quien escriba): `docs/en/**` (árbol EN duplicado, para lectores de
GitHub), `docs/examples/**` y `docs/agents/**` (documentación interna del plugin, no del producto
del proyecto consumidor), `docs/**/atlassian-connector-notes.md` y, como siempre,
`docs/security-scan/**` (invariante no negociable de `nemesis`). Verificable con
`confluence-scope.py --status` / `--check` (`skills/confluence-publish/scripts/`).

**Puntos de nacimiento de `docs/knowledge/`** (memoria técnica, `2026-08-20-knowledge-capture`) —
**sí entra en el espejo por defecto**, no está en el `exclude` (a diferencia del plan/ledger de la
fila `planner` de arriba): `planner`/`implementer` escriben un ADR en `docs/knowledge/adr/` cuando
una decisión de diseño cruza el umbral (ver regla 10 de `CONVENTIONS.md`); `debug-root-cause`
escribe un gotcha en `docs/knowledge/gotchas/GOT-NNN-<slug>.md` (fichero nuevo) al cerrar su Fase 4
(causa raíz confirmada); `qa` escribe un gotcha cuando un flaky justificado resulta ser un patrón,
no un accidente; `/retro` produce una segunda salida con lecciones de proceso en
`docs/knowledge/lessons/LES-NNN-<agente>-<slug>.md` (fichero nuevo), además de su
fila numérica en `CALIBRATION.md`. Los cinco agentes lectores (`evaluator`, `planner`,
`implementer`, `qa`, `documenter`) aplican `agent-kits/shared/knowledge-check.md` antes de
trabajar (progressive disclosure: solo el índice + su área). Detalle completo: regla 10 de
[`CONVENTIONS.md`](CONVENTIONS.md).

## 6 · Visibilidad y aprendizaje (todo solo-lectura)

> **Coste de generación (usage-meter):** cada artefacto del ciclo (y cada tarea en Modo B) se **mide** con tokens reales de la transcripción (`agent-kits/shared/usage-meter.py`); el bloque `generacion:` de su frontmatter alimenta la sección **coste de proceso** de `/roadmap-metrics`, y `/retro` calibra con ello el **ratio tokens→hora** que usan el evaluator y el propio meter. Fechas = contexto · tokens = medida · horas = derivadas.

```mermaid
flowchart TD
    M["usage-meter.py<br/>start/close por artefacto y tarea<br/>(tokens reales de la transcripción)"] -->|bloque generacion:| R
    R[("docs/roadmap/*/<br/>spec · evaluación · plan · tasks")] --> S["/roadmap-status<br/>dashboard HTML + md"]
    R --> T["/pm-backlog<br/>prioriza la cartera<br/>BACKLOG.md"]
    R --> U["/roadmap-metrics<br/>real vs estimado<br/>+ coste de proceso<br/>metrics.md"]
    S --> V["/roadmap-brief<br/>one-pager PDF<br/>para dirección"]
    T --> V
    U --> V
    J[("Jira<br/>issues + worklogs")] --> W["/roadmap-live<br/>estado en tiempo real"]
    U --> X["/retro por iniciativa<br/>causas de desviación<br/>+ ratio tokens/hora medido"]
    R --> DR["/spec-drift<br/>deriva spec↔código<br/>vigente ✓ · derivado ✗ · no verificable<br/>→ DRIFT.md"]
    DR -.->|"deriva → /pm-cycle"| R
    X --> Y[("CALIBRATION.md")]
    Y -->|calibra estimaciones<br/>y ratio tokens→hora| Z["evaluator"]
    Y -.->|ratio| M
```

## 7 · Configuración (una pasada con `/setup`)

```mermaid
flowchart LR
    A["/setup"] --> B[".claude/rates.json<br/>tarifa · tokens · jornada · ratios<br/>la leen evaluator, planner y jira-sync"]
    A --> C[".claude/confluence.json<br/>opt-in + destino"]
    A --> D[".claude/jira.json<br/>opt-in + política de jornada"]
    A --> G[".claude/dev.json<br/>tdd · worktree · subagentes<br/>(+ decisión constitución)"]
    A --> H["docs/CONSTITUTION.md<br/>principios permanentes (opt-in)<br/>los leen TODOS los agentes;<br/>la lente A los hace cumplir"]
    C -.->|estado| E[".claude/confluence-state.json"]
    D -.->|estado| F[".claude/jira-state.json<br/>mapeo · imputado/día · banco"]
```

Detalle de cada fichero: regla 9 de [`CONVENTIONS.md`](CONVENTIONS.md). Comportamientos del
conector Atlassian: [`atlassian-connector-notes.md`](atlassian-connector-notes.md).

> **Nota (Confluence):** si esta página se publica en Confluence vía `confluence-publish`, los
> diagramas Mermaid solo se dibujan si el espacio tiene una app/macro de Mermaid instalada; si no,
> se verá el código fuente del diagrama. En GitHub y editores compatibles se renderizan siempre.

> **Mantenimiento:** al añadir o cambiar un agente, comando o skill, actualiza el diagrama
> correspondiente de este documento (ver checklist de `CONVENTIONS.md`).
