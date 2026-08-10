---
spec: token-diet
descripcion: Reducir el consumo de tokens del plugin (disciplina de lectura en el recon, filtrado de payloads Atlassian, progressive disclosure de prompts largos, disciplina de salida en handoffs) y resolver el precio de tokens con una mini-skill rates-verify
estado: aprobada          # borrador | aprobada | implementada | obsoleta
creado: 2026-08-10
actualizado: 2026-08-10
evaluacion: evaluation.md
plan: improvement-plan.md
---

# Dieta de tokens del plugin

> **Evaluación:** [`evaluation.md`](evaluation.md) (2026-08-10 · 12,9 h · ~669 € · 5 características · go recomendado)
> **Plan de implementación:** [`improvement-plan.md`](improvement-plan.md) (2026-08-10 · 8 tareas · 3 fases · 12,9 h · ~669 €)

> **Terminología:** «recon» = fase de exploración del repo que hacen documenter/nemesis/evaluator. «progressive disclosure» = cargar el detalle procedimental solo cuando esa fase se ejecuta, no todo el prompt siempre. «disciplina de salida» = límite de longitud del mensaje final que un agente devuelve al orquestador.

## Contexto y objetivo

El model tiering (iniciativa `agent-best-practices`) ya atacó el **coste por token**. Esta iniciativa ataca el **número de tokens**, donde está el grueso real: no en los prompts, sino en (1) el **recon** — agentes que hacen `Read` de ficheros enteros y recorren repos completos cuando bastaría `grep` + leer un fragmento; (2) los **payloads de Atlassian** — búsquedas JQL y lecturas de Confluence que devuelven objetos enormes por defecto; (3) los **prompts largos** siempre cargados (documenter 148 líneas, nemesis 173) aunque solo se ejecute una sub-fase; y (4) la **acumulación en el orquestador** — cada agente de la cadena devuelve resúmenes generosos que se apilan en el contexto de `/dev-cycle`. Objetivo: recortar tokens sin perder calidad, con reglas verificables, reutilizando el patrón de fragmentos compartidos (`agent-kits/shared/`). Referencias: best practices oficiales (gestión de contexto, subagentes para investigación, `grep` antes de `Read`), superpowers (progressive disclosure).

## Decisiones de diseño

| Decisión | Elección | Motivo |
|---|---|---|
| Dónde vive la disciplina de lectura | **Fragmento compartido `agent-kits/shared/read-discipline.md`** | Lo comparten documenter, nemesis, evaluator, qa; una sola fuente (como estimation-defaults) |
| Recon | **grep/glob antes de `Read`; `Read` con límite de líneas; ignorar `node_modules/`, `vendor/`, lockfiles, `dist/`, binarios, `.min.*`** | El mayor ahorro está aquí; son reglas objetivas y verificables |
| Payloads Atlassian | **Pedir solo campos usados (`fields`), `maxResults` acotado, `searchResultMode:"issues"`** | Las respuestas por defecto son enormes; jira-sync/roadmap-live solo usan una fracción |
| Prompts largos | **Mover el detalle procedimental de fases a ficheros del kit, leídos on-demand** | documenter y nemesis cargan todo aunque se pida una sub-tarea |
| Disciplina de salida | **Fragmento compartido `output-discipline.md`: mensaje final del agente ≤ ~12 líneas, datos, sin prosa** | Cada handoff se apila en el contexto del orquestador; se multiplica por cada ciclo |
| Precio de tokens | **Mini-skill `rates-verify`: WebFetch a la doc de precios → actualiza `.claude/rates.json` con fecha** | Elimina el `⚠️ verificar` que arrastra toda evaluación; el coste IA deja de ser aproximado |

## Características (alcance detallado)

| ID | Característica | Detalle |
|----|---------------|---------|
| C-01 | Fragmento `read-discipline.md` + adopción | Nuevo en `agent-kits/shared/`: reglas de recon (grep/glob antes de Read; `Read` con `limit`; lista de rutas/globs a ignorar; "lee fragmentos, no ficheros completos, salvo que el fichero sea el objeto de trabajo"). Lo referencian documenter (P2 recon), nemesis (SAST), evaluator (P2), qa (P1) vía `$SHAREDKIT`, con fallback de una línea |
| C-02 | Filtrado de payloads Atlassian | En `jira-sync` (búsquedas/creación) y en la skill `roadmap-dashboard`/comando `roadmap-live`: pedir siempre `fields` explícitos (solo los que se usan), `maxResults` acotado, `searchResultMode:"issues"`. Documentar el patrón como regla en el SKILL de jira-sync |
| C-03 | Progressive disclosure de documenter y nemesis | Mover el detalle paso-a-paso de las fases largas a ficheros de su kit (`agent-kits/documenter/`, `agent-kits/nemesis/`) que el agente lee **cuando entra en esa fase**, dejando en el `.md` el flujo de alto nivel + punteros. Sin cambiar comportamiento, solo cuándo se carga el detalle |
| C-04 | Fragmento `output-discipline.md` + adopción | Nuevo en `agent-kits/shared/`: "tu mensaje final al orquestador es datos, no informe: ≤ ~12 líneas, rutas + cifras + estado, sin recap de pasos". Lo referencian los agentes de cadena (evaluator, planner, implementer, qa, documenter). El detalle para el usuario ya vive en los artefactos |
| C-05 | Mini-skill `rates-verify` | Skill que hace WebFetch a la doc de precios de la API de Claude, extrae input/output del modelo asumido y **escribe `.claude/rates.json`** (`precioTokensInput/Output`, `verificadoEl: YYYY-MM-DD`). evaluator/planner dejan de marcar `⚠️ verificar` si la fecha es reciente. Se ofrece en `/setup` y cuando una evaluación detecte el precio sin verificar |

## Alcance

- **Dentro (esta iteración):** C-01 … C-05.
- **Fuera (siguientes specs):**
  - Cachés de prompt propias / memoization entre ejecuciones — complejidad alta, ahorro dudoso; Claude Code ya gestiona el caché de contexto.
  - Versiones "lite" de los agentes — duplicaría mantenimiento; el tiering + progressive disclosure cubren el caso.
  - Telemetría de tokens propia — `/cost` y `/context` de Claude Code ya lo dan; ver [[preferencias-jordi]] sobre no reinventar.
  - Medición automatizada del ahorro (A/B) — se valora tras rodar; el real por token entra en CALIBRATION vía `/retro`.

## Manejo de errores

| Caso | Comportamiento |
|---|---|
| `rates-verify` no puede leer la doc (red/bloqueo) | No inventa precio: deja el `⚠️ verificar` y avisa; la evaluación sigue con cálculo parametrizado |
| Un agente necesita leer un fichero entero de verdad (p. ej. es el objeto a documentar) | La disciplina lo permite explícitamente: la regla es "no leas de más", no "no leas" |
| Fragmento compartido ausente (instalación parcial) | Fallback de una línea en cada agente; el comportamiento no se rompe, solo pierde la optimización |
| Filtro de `fields` deja fuera un campo que sí se necesita | Se añade a la lista explícita; nunca se vuelve al "todos los campos" por defecto |

## Pruebas

- Revisión de que documenter/nemesis/evaluator/qa referencian `read-discipline.md` y que su recon usa grep/glob + `Read` con límite (inspección de los prompts).
- `rates-verify`: prueba con la doc real → `.claude/rates.json` queda con precios y fecha; prueba con red caída → mantiene `⚠️ verificar` sin inventar.
- jira-sync/roadmap-live: las llamadas declaran `fields` explícitos y `maxResults` (inspección).
- `lint_plugin.py` sigue verde; los fragmentos nuevos aparecen en `agent-kits/shared/README.md`.
- Comprobación cualitativa: una ejecución de documenter sobre un repo mediano lee menos (se puede contrastar con `/context` antes/después, manualmente).

## Referencias

- Best practices oficiales — gestión de contexto y subagentes: https://code.claude.com/docs/en/best-practices
- Iniciativa previa `agent-best-practices` (model tiering, agent-kits/shared).
- [[preferencias-jordi]] — no hardcodear, no reinventar lo que trae Claude Code.

## Decisiones confirmadas (revisión del usuario · 2026-08-10)

1. Atacar el consumo de tokens vía iniciativa propia. **Confirmado.**
2. Alcance = recon + Atlassian + progressive disclosure + salida + rates-verify. **Confirmado.**

## Supuestos

- La doc de precios de la API es accesible por WebFetch; si cambia de formato, `rates-verify` se adapta al parseo real.
- Reducir el detalle inline de documenter/nemesis y cargarlo on-demand no degrada la calidad — a verificar en el rodaje; si degrada, se revierte esa característica sin afectar al resto.
- No hay `.claude/rates.json` con precios verificados hoy; C-05 lo resuelve.
