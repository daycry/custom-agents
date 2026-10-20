# Plugin capability panel

Hooks appear in one card per **runtime and event**. `PostToolUse` retains three
handlers in each runtime. HTML counts groups; JSON retains one entry per handler,
`counts.hooks` counts actions and `hook_group_count` counts groups. `--runtime`
selects hook and extension sources; `all` compares the three runtimes. The HTML
runtime filter affects hooks while retaining other bundle capabilities.

Each action has a stable ID, source and locator, native channel, public purpose,
activation and behavior. Claude reads `hooks/hooks.json`; Codex reads
`interop/codex/hooks.json`. OpenCode reads bounded strict JSON between markers in
`hooks/opencode-plugin.js`: the catalog governs the adapter and is never imported
as JavaScript. `hook_sources` reports each source as declared, missing or invalid;
a failed source is never replaced with another runtime's hooks.

The OpenCode catalog retains six bindings and eight actions. `ActivityObserved`
identifies the informative `agent-activity` capture, with declared supervision of
2500 ms; the reader requires its exact terminal events and idle inputs. This row
is an adapter declaration, not evidence of opt-in, loading or actual execution.

Claude/Codex timeouts use seconds with registration provenance. OpenCode shows
milliseconds of adapter supervision; its idle/execution stream capture is not a
native teardown hook. Declared, absent and invalid budgets remain distinct;
no default is invented. The guard obtains role identities from the central bundle
map; configuration, loading and execution are different evidence. `load_status`
and `execution_status` remain `unknown` in this static catalog.

Informational names and purposes come from recognized handlers' public
`panel-title` and `panel-description` headers. The panel excludes full commands
and never executes scripts, hooks or diagnostics. Action links restore filters
and focus; Sources stays reachable on mobile.

**English** · [Español](../PLUGIN-PANEL.md)

The plugin-catalog command uses plugin-panel to explore agents, skills, commands,
declared tools and global hooks. Search and filters run in a standalone
seven-page HTML panel. Served mode adds local progress, memory queries and opt-in recent activity signals. The
portfolio (evaluations and budgets) is presented on the Initiatives page; its data is computed by roadmap-dashboard.

From a checkout:

```powershell
python skills/plugin-panel/scripts/build_panel.py --export panel
python skills/plugin-panel/scripts/build_panel.py --json
python skills/plugin-panel/scripts/build_panel.py --project . --runtime codex --export panel
```

`--export <dir>` replaces the former `--html`: it writes seven pages (`index.html`,
`iniciativas.html`, `plan.html`, `agentes.html`, `memoria.html`, `catalogo.html`,
`diagnostico.html`) sharing one menu, `assets/`, `vendor/chart.js/` (with its license
and provenance) and an `export-manifest.json` listing each owned file with its SHA-256.
The folder opens from `file://` and makes no network requests. Only an HTML file with
the panel marker, or a manifest file whose hash is the one it wrote, is overwritten; a
foreign file with the same name aborts the export with exit code 2 before anything is
written. Project and home paths, the system user name and emails come out as `.`, `~`,
`<usuario>` and `<correo>`. If Chart.js does not match its fingerprint, pages show
tables only. `--json` is unchanged.

Installed bundles resolve the skill through their runtime roots. The generator
finds its own bundle; `--root <bundle>` inspects another catalog without importing
its code. Native Python supports Windows without WSL, Tkinter, extra Python
packages. Standalone export needs no server.

## Multi-page panel: seven pages, two modes

One command (`/plugin-catalog`; `/roadmap-status` invokes it for the portfolio) produces
the same seven-page panel with a shared menu, in two modes:

| Page | File | What it shows |
|---|---|---|
| Inicio (Home) | `index.html` | Summary and, in served mode, ledger progress |
| Iniciativas (Initiatives) | `iniciativas.html` | Portfolio from `docs/roadmap/` (state, budget); the landing page of `/roadmap-status` |
| Plan | `plan.html` (index) and `plan-<id16>.html` | Task kanban per initiative, charts and burndown; in served mode, plan review from the panel |
| Agentes en vivo (Live agents) | `agentes.html` | Runs, timeline and recent activity signals (served only; opt-in) |
| Memoria (Memory) | `memoria.html` | Entries, curator tray, timeline, relations, backends and journal; local queries (served; on demand) |
| Catálogo (Catalogue) | `catalogo.html` | Agents, skills, commands, tools and hooks |
| Diagnóstico (Diagnostics) | `diagnostico.html` | Imported doctor report, with date and scope |

- **Exported** (`--export <folder>`): static files opened from `file://`; no server and
  no network requests; pages that need live data say so instead of inventing it. CSP via
  `<meta>`: `default-src 'none'`, `script-src 'self' file:`, `style-src 'self'
  'unsafe-inline'`, `img-src data:`. Plan review is never opened from here.
- **Served** (`--serve`, 127.0.0.1 only): the same pages plus the live scripts
  (`panel-live.js`, `panel-memory.js`, `panel-activity.js`, `panel-review.js`). CSP via
  header with a nonce and `connect-src 'self'`; no CDN. The `api/*` routes keep their shape.

Charts use **Chart.js 4.5.1 (MIT), vendored** in `assets/vendor/chart.js/`, unmodified:
extracted once from the official npm tarball with its integrity verified;
`PROVENANCE.json` records version, SHA-256 and license, and nothing downloads it when
generating or opening. If the file does not match its fingerprint, pages show tables only.
`roadmap-dashboard` no longer generates HTML: it computes the portfolio data
(`dashboard.md`, `--json`, `--metrics-md`) and the panel presents it (relationship in
`agents/ROLES.md`). The installer copies the whole `skills/plugin-panel/assets/`,
`vendor/` included.

## Home, Initiatives and Plan (redesign phase 2)

The three pages read the roadmap through **read-only** projections and never recompute figures
that already have an owner: `roadmap-dashboard` (`scan` + `vista_json`) provides the portfolio,
`progress-report.py` the "N of M tasks", and `agent-kits/shared/ledger-view.py` what the ledger
says about each task. `skills/plugin-panel/scripts/panel_data.py` only projects them.
A missing value is `null` and is stated ("sin datos"); it is never drawn as 0.

| Page | What it shows | Served API |
|---|---|---|
| Inicio (Home) | Initiatives by spec state (chart + table), overall progress and actual vs estimated cost | `api/cartera` |
| Iniciativas (Initiatives) | Read-only kanban, one column per spec state (`borrador`, `aprobada`, `implementada`, `obsoleta`) and one card per initiative with its alerts as text; hours and cost charts with their table. A card with a plan links to `plan-<id16>.html` | `api/cartera` |
| Plan (`plan-<id16>.html`) | Kanban of the ledger tasks with the five vocabulary columns (`borrador`, `en-progreso`, `en-revision`, `completado`, `cancelado`) and an "unrecognised state" strip showing the literal; task detail; progress and hours per phase charts and a burndown | `api/plan-<id16>`, `api/plan-<id16>-<T-XX>` |

- **`api/cartera`**: initiatives of `docs/roadmap/` (at most 128 folders listed, 64 rows, response
  <= 64 KiB). Each initiative falls in ONE spec category: the four states, `ilegible`,
  `sin_spec` (fast path) or `no_reconocido` (with its literal). The estimated cost is shown as
  `evaluation.md` writes it; only the first euro amount is extracted for the sum.
- **Plan by id16**: `<id16>` is 16 hex characters from the plan inventory the server publishes;
  the browser never sends a path. A task carries actual and estimated AI hours with their source
  (`medido`/`estimado`), supervision and human hours, criteria with their checkbox, the
  `Verificación` and its output, dependencies, the latest review with its open gaps and the
  "archived" mark (only the link to `execution-history.md`; its content is never read). The detail
  opens with a click or Enter, is announced in an `aria-live` region and Escape closes it,
  returning focus.
- **Charts**: progress per phase = completed/total as the ledger counts them; hours per phase =
  sum of what is present, "sin datos" if no task has the figure, labelled "(medido)",
  "(estimado)" or "(medido y estimado)". The **burndown** starts from the non-cancelled tasks
  minus those closed up to each date, using only real closing dates; with no completed task it
  says "Sin datos: ninguna tarea completada todavía".
- **Live refresh** (served): the Plan is re-read every five seconds with the Progress polling
  rules (one active request, paused while the tab is hidden, four-second timeout); cards with the
  same row keep their node and focus. The read date sits in a non-live region so each cycle is
  not announced. A failure keeps the view with a warning.
- **Exported**: the same from the JSON embedded in `panel-data` (keys `plan` and `detalles`),
  with no requests; live data is declared absent.

### The `Cerrada` ledger field

`- **Cerrada**: YYYY-MM-DD` is an optional per-task field: the real closing date. The
implementer fills it when completing the task; `ledger-lint.py` requires a real date (empty,
malformed or impossible is an inconsistency) not earlier than `creado:` or the `| **Fecha** |`
row. `ledger-view.py` publishes `cerrada` (valid) and `cerrada_invalida` (the text), and the
burndown only uses the former. `task-brief.py` does not pass it to the subagent. Like
`Changelog`, it is ledger metadata, not an acceptance criterion.

### `ledger-view.py`

```powershell
python agent-kits/shared/ledger-view.py docs/roadmap/<date>-<slug> --json
```

Pure projection of a `tasks.md` (folder or file): phases, tasks, state (from the vocabulary or
`literal` if it does not match), hours, criteria, description, verification, dependencies,
`archivado`, `cerrada`, `revision` and `gaps`. It does not validate (that is `ledger-lint.py`),
does not summarise (that is `progress-report.py`) and reuses their parsers. `status`: `ok`,
`fuera_de_tope` (> 256 KiB, no figures), `ilegible`, `sin_ledger`, `sin_tareas` or `sin_lectura`.
Exit 0 for a usable path, 2 for incorrect usage.

## Memory, Catalogue and Diagnostics (redesign phase 4)

The three pages are **read-only** and do not recompute what already has an owner. A datum the source
does not provide is shown as «sin datos» (no data); it is never drawn as 0 nor inferred from `mtime`.

| Page | What it shows | Served API |
|---|---|---|
| Memoria (Memory) | Entries by type (ADR, gotcha, lesson) and state (`aceptada`, `propuesta`, `obsoleta`) with chart and table, filterable by area with the keyboard; curator tray; timeline with successors and «vigente»; relations of ONE entry; what was published per backend; recent journal sessions; and the usual explicit query | `api/memoria` (GET) and `api/memory` (POST, unchanged) |
| Catálogo (Catalogue) | Combinable filters by type, **origin** and runtime, with counts that follow them; keyboard operable | none (client only) |
| Diagnóstico (Diagnostics) | One row per check with its ✅/⚠️/❌ verdict also as text, the report's date and scope, and a summary with the count of each verdict | none (explicit report) |

- **`api/memoria`** (GET, ≤ 64 KiB, 10 s cache): projection of `knowledge-view.py` (`snapshot`) and
  `knowledge-find.py` (corpus, succession and relations), plus the tray, the backends and the journal.
  When it does not fit it trims `entradas` from the end, keeps the whole-corpus counts and declares it
  (`recortado`, `status: partial`, `output_budget`). All text is redacted before trimming and goes
  through the server scrubber. `api/memory` is unchanged: it only accepts `search`, `show` and `related`.
- **Entries and timeline**: ordered by date; an entry is «vigente» (current) when it has no successor and
  is not obsolete; the succession chain (`sustituye a` / `sustituida por`) is shown as text.
- **Relations**: choosing an entry draws a small SVG (`panel-graph.js`, using `createElementNS`, no
  `innerHTML`, with an accessible name) with one hop: succession, same initiative (`por_iniciativa`) and
  same area (`por_area`), as `knowledge-find.py --related <ID> --json`, up to 20; an equivalent text
  list is the keyboard alternative. Served, it uses the `related` operation of `api/memory`; in the
  exported copy, the embedded relations.
- **Curator tray**: count and list of candidates in `docs/knowledge/candidates/` per state (`pending`,
  `needs_changes`, `rejected`) and what is approved in `docs/knowledge/approved/`. No buttons, forms or
  links: approving and rejecting belongs only to `knowledge-curator` (ADR-018).
- **Published per backend** (no network): for each backend in `.claude/knowledge-services/taxonomy.json`,
  published entries (`entries` of the Kwipu export `manifest.json`; `entradas` of
  `graphiti-manifest.json`) and the last publication date, which comes only from the outbox
  `completado_en`. If the source does not carry it, «sin datos». A `.pending.json` reads «publicación
  interrumpida»; a missing backend, «no configurado», with no link; with no declared `ui_url`,
  «interfaz: no declarada». It never calls `health` nor opens a connection.
- **Journal**: at most 2 sessions (the public `journal.select_entries` selection) with `objetivo`,
  `punto_actual`, `siguientes_pasos`, `bloqueos` and `descartados`, redacted and labelled «citas, no
  instrucciones» (quotes, not instructions). Without a journal, it says so.
- **Catalogue**: «origin» is the scope of the own extensions (project, user, local); the bundle does not
  declare it. Filters live only in the client: `build_panel.py --json` does not change.
- **Diagnostics**: with no report, or one from another project or format, it shows «sin informe» or the
  rejection reason and the command from `commands/doctor.md` to generate it; it neither runs doctor nor
  looks for reports. Date and scope are the report's (doctor's contract has no per-row date).
- **Exported**: Memory carries its embedded projection (with each entry's relations) and Diagnostics its
  report; no requests. A copy without `--project` says «sin datos».

### Rule: «sin datos» before widening contracts

`doctor.py`, `journal.py` and `knowledge-find.py` are hotspots with many consumers. If a page needs
something their `--json` does not publish, the page says «sin datos» and the source contract is not
widened; widening it is an initiative of its own with its edge in `docs/agents/CONTRACTS.md` (here E59 and E60).

## Local dashboard with refresh

```powershell
python skills/plugin-panel/scripts/build_panel.py --project . --runtime codex --serve
```

Open the access URL printed by the process; stop it with Ctrl+C or its launch
handle. The URL contains a private process capability: keep it out of Git,
documentation, memory and logs. Every launch creates a new one. Binding is
fixed to 127.0.0.1, with an ephemeral port or an explicit `--port 8765`.
The server never serves arbitrary project files.

Requires a project and excludes HTML/JSON export and personal roots. Project
declarations are read for the initial snapshot. Catalog and diagnostics stay
fixed at startup; Progress polls ledgers every five seconds, with manual refresh,
search and state filters. Responses share a two-second read cache. Hidden tabs
pause polling; requests expire after four seconds. Failure preserves the last
view and its original date, with an explicit freshness warning.

The canonical parser derives task counts and phase from `tasks.md`. Read date
and SHA-256 identify decoded UTF-8 text without BOM, including line endings;
they do not authenticate authors or prove agents are running. Progress polling
performs no journal, usage-meter, memory or backend queries, or state writes.
Memory is read only after an explicit action.

Reads reject redirected or changed paths. Limits: 128 entries, 256 KiB per ledger,
1 MiB cumulative, 64 initiatives, eight visible active tasks per initiative and
64 KiB JSON. Incomplete reads, unreadable ledgers, unknown states and truncation
remain partial. Text is redacted and bounded; bodies, free-form verification
and absolute paths are excluded.

Page/API require the capability and exact Host; any Origin must match the server.
Cross-site requests, queries and arbitrary paths are rejected. POST is accepted
for local memory queries and a plan review (the fixed one of `--review-initiative` or that of
`--review-panel`). It is the only exception to read-only: review writes only its own local
receipts and comments, and the browser never opens the `plan-ok` gate.
No cookies or access logs; nonce CSP, same-origin connections, no-store,
no-referrer and no framing. The capability does not isolate other processes
owned by the same user. Consuming a plan decision requires the common CLI and
an authorized workflow. Memory publication/rebuild retain their consumers and tests.

## Live agents (redesign phase 3)

Served mode only, and only with `sesion.actividad: true` (see [`observability.md`](observability.md),
"Live agents"). The `agentes.html` page keeps the recent signals of the live snapshot at the top (next
section) and adds, with `assets/page-agentes.js`:

- **Runs de agentes** (agent runs): one row per run of the last 24 h, most recent first: runtime, role (or
  "sesión"; in Codex "sesión (Codex agrupa por sesión)"), start, duration, last tool and state. The states are
  `en curso` (signal less than 60 s old), `sin señal reciente` (over 60 s; the duration freezes at the last
  signal) and `respuesta terminada` (only when the subagent's end was observed). Never an inferred
  "finished" or "dead".
- **Timeline** of a run when opened: per event, time, tool, redacted summary of the argument,
  `tarea: <slug>/T-XX` or `tarea: sin atribuir`, duration (or "sin datos") and result (`ok`/`error`/"sin datos").
  These are the run's last 150 events; if there are more, "Historial recortado a los últimos N eventos".
- **Permanent statements**: what each runtime provides and what it does not (Codex does not identify the
  subagent in tool events; OpenCode has no duration; an adapter without the tool binding emits no events),
  "captura informativa: puede tener huecos" and "orden de recepción, no de ejecución".
- **Capture off**: "Actividad desactivada" and how to turn it on; without history, "Aún no hay actividad
  registrada"; a damaged history, "Historial no disponible (`<reason>`)", with nothing partial.

Home (Inicio) adds **Actividad reciente** (the last 10 events: who, runtime, tool, task and how long ago) with a
link to Live agents; in the exported copy it says activity only exists in the served panel.

APIs (GET, same capability and Host/Origin guards as the rest, no `?` in the route, ≤ 64 KiB, refreshed every
5 s from the page):

| Route | Returns |
|---|---|
| `api/actividad-runs` | `runs` (with `key16`, never the full key), `recientes`, `eventos`, `recortado`, `descartados_por_tamano`; with capture off, `status: unavailable`, `reason` and `activar` |
| `api/actividad-run-<key16>` | one run's timeline (`eventos`, `recortado`, `recortado_historial`); an unknown `key16`, or one that matches two runs → 404 |

Both read `agent-activity-store.history` (no lock, no initialization, no repair) and project with
`panel_data.actividad_runs`/`actividad_run`; displayed text goes through the panel's single scrubber. If the
content does not fit in 64 KiB the oldest events are dropped and counted in `recortado`. `api/activity` does
not change. The panel never deletes the history: to delete it, remove `.claude/agent-activity/` by hand.

## Recent activity signals

In `--serve` mode, Activity is separate from Progress. Reading it neither starts
agents nor turns ledger states into process presence. The common owner,
`agent-kits/shared/agent-activity-store.py`, persists only closed metadata; the
reader calls its `snapshot(project)` and the pure `agent-activity.py` projection.

Capture requires the boolean opt-in `sesion.actividad: true` in the project's
`.claude/dev.json`. Missing or `false` disables it. To enable it manually, merge
this key into the existing configuration without replacing other settings:

```json
{"sesion": {"actividad": true}}
```

Opening the panel or running setup neither creates nor enables this setting.
The producer owns `.claude/agent-activity/` and first creates its `.gitignore`
with `*` followed by a newline, excluding new local-state files from Git. The
reader never initializes, locks, purges, migrates or recovers state. Unowned,
partial or invalid directories remain unavailable without adoption. Ignore rules
do not remove files that Git already tracks.

There are at most 64 observations. The JSON snapshot and HTTP response each have
a 64 KiB limit. `complete` means that snapshot validated; visible
`collection_complete: false` does not represent every session or agent. Cards
show declared runtime/role, source, state and time; pseudonymous keys stay
internal. This state retains no prompts, transcripts, tool arguments or raw
consumer paths.

| State | Meaning |
|---|---|
| `recent_start` | Recent start signal |
| `recent_response_end` | Recent response boundary |
| `recent_execution_end` | Recent execution boundary |
| `recent_idle` | Recent session idle signal |
| `unknown` | Expired signal, future clock or unknown freshness |

A signal proves neither a live process nor agent destruction, authenticated
identity or complete collection. Freshness expires at 60 seconds. The UI combines
advertised age with monotonic time since reception; refreshing the same event
and revision does not renew its age. HTTP failure preserves the view and date,
but signals keep expiring. Future timestamps remain unknown.

`GET api/activity` uses the server's existing capability and Host/Origin guards.
It is read-only, bounded and accepts no arbitrary route. POST retains the
existing 405 rejection. There is one active request, a four-second timeout and
polling five seconds after settlement. Hiding the tab aborts and pauses requests;
resuming applies expiry before fetching. Static HTML explains that no service
supplies signals. Missing activity JS degrades only this section, preserving
other views.

Skills-only export requires explicit skill references to
`agent-kits/shared/agent-activity-store.py`, `agent-kits/shared/agent-activity.py`,
`agent-kits/shared/local-state.py` and `agent-kits/shared/local-read.py`.
The `capture` producer also reads the central mapping
`agent-kits/shared/native-roles.json`: declare it explicitly so the package
includes the JSON, even though the `snapshot` reader does not use it.
That package registers no native hooks; bundled helpers and mapping do not prove capture.
Projection/HTTP/DOM have focal tests. Real browser interaction, hook loading and
native acceptance require their own evidence.

Official references checked on **2026-10-10**:

- [Claude Code: SubagentStart/SubagentStop](https://code.claude.com/docs/en/hooks): subagent signals; a response boundary does not prove destruction.
- [Codex: hooks](https://developers.openai.com/codex/hooks/): native subagent events/payloads; documentation does not establish loading in this session.
- [OpenCode V2.0.12: execution settlement](https://github.com/anomalyco/opencode/blob/2670273ff17da96f85c5826ced57aa1b368754fa/packages/core/src/session/execution.ts#L118-L150): emits one `session.execution.succeeded/failed/interrupted` terminal; its [projector](https://github.com/anomalyco/opencode/blob/2670273ff17da96f85c5826ced57aa1b368754fa/packages/core/src/session/projector.ts#L403-L434) derives idle/outcome from that event.
  Capture preserves `execution_finished`, without turning it into an independent `session_idle` observation or teardown. `session.idle`/`session.status` remain compatibility inputs without claiming emission by this version.
  Native acceptance requires its own evidence and exact correlation; reading the contract does not establish complete capture.

## Review plans from the panel (`--review-panel`)

Besides the review of one fixed initiative (next section), the served panel can open the
review of the plan of **any** initiative from its Plan page:

```powershell
python skills/plugin-panel/scripts/build_panel.py --serve --project . --review-panel --review-state-root ./.claude/plan-review
```

`--review-panel` requires `--serve`, an explicit `--project` and `--review-state-root`; it
combines with `--review-initiative` (which keeps its legacy screen). Without `--review-panel`
the Plan page shows no button and explains in one sentence how to enable it; the exported HTML
never carries review controls or a write `fetch`.

| Route | Method | What it does |
|---|---|---|
| `api/review-summary` | GET | Review state of every initiative (the `plan-review.py summary` operation), keyed by id16 `initiative_id`, with no paths or `review_id`; 5 s cache |
| `api/review-current/<id16>` | GET | Registers for the browser the main review of ONE initiative; answers `review_id`, `estado`, `version_ordinal`, `gate_key` and `escritura` |
| `api/review-open/<id16>` | POST | Opens the review with the `requested-review` gate; compact answer (`review_id`, `escritura`); the view arrives through `api/review/<id64>/view` |

The id16 values come from listing `docs/roadmap` (a valid folder with `improvement-plan.md`; a
collision leaves the initiative out). An unknown id16 gets 404 before the body is read; the
browser never sends a path or a file name. One process registers at most 128 reviews: the
excess answers 429 with "demasiadas revisiones abiertas en este proceso". A review with another
gate (e.g. a `plan-ok` opened by `/dev-cycle`) is shown with `escritura: false`.

**`plan-review.py summary`** (read-only: no lock, no fsync, no writes). It takes a list of
initiatives on stdin and returns, for each, `estado` (`sin_revision`, `pendiente`,
`cambios_pedidos`, `aprobada`, `obsoleta` or `no_disponible`), `version_ordinal`, `gate_key` and
counters for comments, answered comments, those needing clarification and answers without
verification. A review whose version no longer matches the plan is `obsoleta`; the earlier
decision does not count as current. Double inventory that rejects observed changes (not an atomic
snapshot nor permission to continue a gate); `approval_granted` is always `false`. Without a state
folder every initiative is `sin_revision`. Exit 0 with `ok`/`partial`, 3 when unavailable; an
expired deadline mid-way leaves the rest as `no_disponible`.

The Plan page UI shows the "Revisar este plan" button and the state as text ("sin revisión ·
pendiente · cambios pedidos · aprobada vN · obsoleta por cambio de versión") on the Initiatives
card and in the Plan header, with identical wording; it lets you comment per section and decide
(approve or request changes); and under each comment it shows the agent's answer and its
disposition, or "sin respuesta del agente".

**Write exception.** The panel is read-only, with one bounded exception: `api/review-open` (and
the already existing comment/decision POSTs) write only the receipts and comments of
`.claude/plan-review/`, with the same protections (capability, Host/Origin, no cookies, nonce
CSP). **The browser never opens `plan-ok`**: `/dev-cycle` opens that gate; approving here with
`requested-review` does not authorise it. There is no receive/ack/consume/result over HTTP, and
the panel never modifies `improvement-plan.md` or `tasks.md`.

## Review a plan at the existing gate

Visual review is optional. When explicitly requested, it replaces the pending
plan approval in `/dev-cycle`. Sufficient approval already given in conversation
lets the workflow continue without opening this channel or asking again.

The [`/dev-cycle`](../../commands/dev-cycle.md) caller includes Bash and
PowerShell recipes. Use a real Python executable and owner/validator/builder from the same
bundle; multiple complete copies without active source provenance are ambiguous.
Validate `open` before starting a separately held server, and validate ack before
rereading the current view. These recipes alone do not establish native command
loading or real browser interaction.

```powershell
python skills/plugin-panel/scripts/build_panel.py --serve --project . --review-initiative docs/roadmap/<date>-<slug> --review-state-root ./.claude/plan-review --review-gate-key plan-ok
```

Select the exact initiative path; only `improvement-plan.md` is reviewed.
`--review-initiative` and `--review-state-root` are paired. The builder defaults
to `requested-review`; `/dev-cycle` must select `plan-ok`. A general review decision
cannot authorize that gate. Served mode excludes `--export`, `--json`, `--home` and
`--user-root`. Standalone HTML neither opens review nor writes its state.

The workflow first runs `plan-review.py open` to obtain the review ID and version,
using `gate-key: plan-ok` and its current runtime. It then starts the server,
which recovers that same receipt. Keep the server handle and private URL while
the user reviews; a waiting consumer must never interpret `waiting` as approval.

The view displays all Markdown as text, split into sections and bound to original
byte and view hashes. Repeated headings have separate IDs. Redacted secrets and
sanitized controls are indicated. Approval covers the displayed view, excluding
hidden values. Text, links, images and HTML cannot execute instructions or load
external resources. Unreadable, empty, partial or oversized plans disable decisions;
no clipped prefix can be approved.

| Action | Result |
|---|---|
| Save comments | Saves the redacted section drafts before a decision |
| Approve the view | Seals `approve` for that version; comments are optional |
| Request changes | Seals `request_changes`; needs at least one nonempty comment |
| Load current version | Explicitly opens the current version without transferring comments |
| Close without deciding | Closes the UI and preserves drafts/receipts without a decision |
| Return to review | Reopens the UI without submitting another decision |

The workflow uses `plan-review.py consume` with project, state-root, initiative,
review_id, gate and the raw/view tuple. The owner validates selection/view before
delivery, confirms actual IDs and rereads the version before returning consumed
state. It launches no roles and proves no external effects. Waiting preserves an
absent decision; an obsolete version is not consumed. A failed ack preserves the
delivery for retry; a post-ack change returns version_changed with historical
consumption. One three-second deadline covers the whole operation. The final view
is not a transaction with subsequent work and does not guarantee ABA detection.

An obsolete review preserves its historical decision but does not approve the
current plan. `receive` returns `version_changed` and exit code 2 without consuming
it. A new review opens with `open` against the current version and needs its own
decision; the old receipt hashes are not updated. Valid consumption remains
`receive → validation → ack → validation → view`, before effects. Sufficient
conversational authorization retains its existing route.

The common owner `agent-kits/shared/plan-review.py` maintains machine states
`pendiente` → `entregada` → `consumida`. Submission leaves the decision pending;
`receive` delivers it and `ack` records durable consumption. The panel never starts
agents, changes plan/tasks or performs receive/ack over HTTP. Consumer registration
is historical: the UI reports no registration or unknown activity.

GET view/status and POST comments/submit/refresh accept only IDs registered by
this server instance. No free-form roots, paths, artifacts or commands are accepted.
Project state under `.claude/plan-review/` is shared by all three runtimes; it is
not Claude-only personal configuration. Exclude it from Git. The owner neither
adopts an unrelated directory nor evicts decisions to make room.

Limits: 256 KiB plans, 128 sections, 64 receipts, 16 KiB requests and 512 KiB JSON
responses. Up to 20 comments, 2,000 characters each and 10 KiB cumulative UTF-8
text; excess is rejected without clipping. Operations share a three-second deadline
and a lock budget of up to 100 ms. Status polling runs every five seconds with
one active request, pauses on hide/close and aborts after four seconds.
Memory and Progress retain their separate limits.

Changed bytes or transformer produce `version_changed`, retain the old receipt
and disable decisions until the current version is explicitly selected.
The workflow validates gate, version and choice, acknowledges, then rereads before
starting work. A current consumed receipt permits resume without another confirmation.
Delivery may repeat; receipt consumption is idempotent, external effects have no such guarantee.
On resume the workflow checks the current ledger/plan: ack does not prove work
finished before a crash. Resume pending work without restarting planner for changes
already addressed. A stale receipt remains historical and cannot replay its decision on another plan.
Hashes and the capability do not authenticate a person. Rereads and locks provide
no workflow transaction, ABA detection or universal power-loss durability.
Fallback uses existing conversational authorization without inventing approval.

The common bundle needs `plan-review.py`, `local-state.py`, `local-read.py` and `redact.py`.
Skills-only review requires the export to include all four dependencies declared
from plugin-panel. Package verification belongs to QA; any missing dependency
leaves this channel unavailable.
The [command](../../commands/dev-cycle.md) describes receive/ack and the authorized return to planner.

### See what happened to a comment

Consumption confirmed means ack, not that the comment was addressed. Results show
the consumer's declaration: `addressed`, `not_applied` with a reason, or
`needs_clarification`. `confirmed`/`not_confirmed` records a human observation
already communicated; it authenticates nobody and grants no approval, QA or new
permission. Missing responses or verifications stay explicitly missing. This is
not chat and adds no confirmation before continuing authorized work.

The consumer records responses through the CLI after that decision's ack. The
browser reads results/history; result/verify-result/receive/ack have no HTTP write
endpoint. Comments on approve can also receive responses; no comments means no
invented row. Notes are inert text. Editing the plan leaves a response bound to
its old consumed review; the new view inherits neither attention nor approval.
Response history distinguishes versions and superseded results. Polling preserves
drafts and focus; failure retains the previous date with a warning.

### Record a response from the workflow

Reuse the `/dev-cycle` caller variables and owner from the same bundle. Retain
review_id, version, gate_key, decision_id and delivery_id from the consumed decision;
CommentId comes from decision.comments. ReviewRevision is that record's integer
`review.revision`, reread before a new operation. A historical version_changed or
unavailable view may expose this record; it cannot authorize work on a new plan.
Choose ResultId once (64 lowercase hex characters) and retain it and the payload
if a response is lost. ReviewRuntime is the current runtime.

```powershell
$OutputEncoding = [Text.UTF8Encoding]::new($false)
$ResultRequest = @{
  version = @{raw_sha256=$RawSha256; view_sha256=$ViewSha256; view_version='plan-text-v1'}
  gate_key = 'plan-ok'; decision_id = $DecisionId; delivery_id = $DeliveryId
  comment_id = $CommentId; result_id = $ResultId; expected_revision = $ReviewRevision
  disposition = 'addressed'; response_text = 'Separated consumption from comment attention.'
  supersedes_result_id = $null
  producer = @{caller_id='dev-cycle'; runtime=$ReviewRuntime; actor_id=$null}
}
$ResultRequest | ConvertTo-Json -Depth 4 -Compress | & $ReviewPython @ReviewPythonArgs $PlanReview result @ReviewScope --review-id $ReviewId --json
```

In Bash select a UTF-8 JSON file with the same eleven keys; RESULT_REQUEST is its
chosen path. Pass the note as data, never as executable shell text.

```bash
"$REVIEW_PYTHON" "${REVIEW_PYTHON_ARGS[@]}" "$PLANREVIEW" result "${REVIEW_SCOPE[@]}" --review-id "$REVIEW_ID" --json < "$RESULT_REQUEST"
```

`producer` has exactly caller_id (1–128 ASCII letters/digits/_/-), runtime
(`claude-code|codex|opencode`) and actor_id (null or an opaque 64 lowercase-hex ID).
Do not send identity_basis, human names, dates, flags, section_id or artifact
observations: the owner derives those. Matching the first consumer is not required.

If a human observation was already explicitly received, retain those bindings and
choose VerificationId once. Reread ReviewRevision for the new operation. Never
infer a verification from edits or tests.

```powershell
$VerifyRequest = @{
  version=$ResultRequest.version; gate_key=$ResultRequest.gate_key
  decision_id=$DecisionId; delivery_id=$DeliveryId; comment_id=$CommentId
  result_id=$ResultId; verification_id=$VerificationId; expected_revision=$ReviewRevision
  assessment='confirmed'; note='Human observation already communicated about this response.'
  producer=@{caller_id='dev-cycle'; runtime=$ReviewRuntime; actor_id=$null}
}
$VerifyRequest | ConvertTo-Json -Depth 4 -Compress | & $ReviewPython @ReviewPythonArgs $PlanReview verify-result @ReviewScope --review-id $ReviewId --json
```

The eleven verify-result keys replace disposition/response_text/supersedes_result_id
with verification_id/assessment/note. Assessment also accepts not_confirmed and
note may be empty. Bash uses the same verify-result CLI with its JSON on stdin.
This annotation is optional, never another gate or delivery requirement.

Exit 0/status ok confirms feedback persistence: review null, approval_granted false
and a feedback_receipt binding the operation, IDs and version. Never pass it to
the open validator or use it as authorization. Exit 2 means conflict; exit3 means
unavailable. Retry with identical IDs/content retains the date and observation,
even when the record revision has advanced. revision_conflict needs reread and
reconciliation; operation_conflict never permits overwrite. A correction uses a
new result_id and supersedes_result_id of the latest result (at most two per
comment). Each result allows one verification; superseded rows stay historical.

`feedback_receipt.revision` is the current record revision when the owner replies.
A retry after another operation may return a higher number than the first receipt;
the IDs, `recorded_at` and persisted row remain unchanged.


Requests 16 KiB; nonempty responses up to 1000 characters/2048 UTF-8 bytes; notes
up to 500/1024. Oversized input and row/record budgets fail without clipping.
History contains up to 8 complete reviews/64 KiB from the same scope, initiative
and gate. Incomplete is not empty. Older bundles without the extension report
unavailable results; an invalid extension is not treated as missing. The new owner
reads record schemas 1/2 without migration on reads; the first valid feedback write
may upgrade legacy to 2. Use owner/server/UI from one bundle; concurrent writes by
old and new binaries are not promised. The envelope remains 1. These instructions
do not establish V01–V08 browser interaction or native acceptance.

## Local memory queries

Queries preserve each entry's authority: proposals and legacy entries do not
become approved knowledge. The [local recovery contract](../roadmap/2026-10-07-catalog-capabilities/comparisons/memory-local-recovery-contract.md)
separates session preservation and restoration from query evaluation.

Served mode adds Memory with Search, Show entry and Relations. Each explicit
action uses `knowledge-view.py`; loading the page or refreshing Progress does
not trigger memory searches. Cards retain full ID, type, state, knowledge version,
evidence and source path. Proposed and obsolete entries retain their state.
Bodies are returned only on Show; an ID collision never selects an entry.

Reads share parsers, ranking, relations and approved validation with
`knowledge-find.py`. Cumulative limits: 256 directory entries, 128 files, 256 KiB
per file, 2 MiB read and depth eight. Queries allow 1,000 characters, IDs 256,
20 results/relations, bodies 12,000 characters and JSON responses 64 KiB.
Truncation, invalid corpus and incomplete reads remain partial; missing,
ambiguous and unavailable are distinct. Redaction precedes clipping;
paths and hashes do not prove approval.

Versions above JavaScript's safe integer range use exact decimal strings, up
to 4,300 digits. Invalid versions remain unknown with a partial result. Alongside
directory entries, enumeration calls are limited to 256; `scans` accounts for
this work even when directories are empty. The reader's probe byte is reserved
within the cumulative read budget.

Only UTF-8 JSON on the fixed private `api/memory` route is accepted, with a
4 KiB request limit and a cumulative three-second body deadline. Duplicate keys,
unknown selectors and other methods are rejected. The UI omits cookies, sets a
six-second query deadline and prevents overlapping requests. Failure preserves
the previous view/date with a warning; results, bodies and relations retain their
own freshness. No adapters, candidates, journal, cache or indexes are loaded.
Standalone HTML retains its inventory without these queries.

CLI usage: `knowledge-find.py --root <project> --view <query>`,
`--view --show <ID>` or `--view --related <ID>`. Output uses version 1 and source
`canonical_knowledge`. Ordinary CLI queries also use the bounded snapshot and
declare `corpus_read`; partial corpora are never cached as complete indexes.

## Standalone extension export

Include your components with `--project <root>` and the actual session runtime
in `--runtime claude-code|codex|opencode`. `--cwd <package>` inspects its skill
ancestor chain. Personal sources are included by default; `--project-only`
excludes them and `--user-root <runtime>=<path>` selects another root. `all`
compares declarations without claiming that one session loaded every runtime.

“Tus extensiones” has independent search and kind/origin/runtime filters. Its
declarations do not change bundle counts. Cards retain ID, source, ownership and
conflicts. Disabled MCP entries describe configuration; connection and permissions
remain unverified. OpenCode tools are definition sources, without inferred exports.
Personas retain the brief's `Tipo` contract and remain distinct from agents.

The generator imports `project-pieces.py` from its own bundle, never inspected
`--root` data. Reader failure preserves the bundle catalog with an explicit
partial inventory. JSON adds `extensions` only when a project is requested,
keeping `schema_version: 1` and existing counts. Task selection follows the
[shared extension method](PROJECT-EXTENSIONS.md).

The inventory extracts public frontmatter, runtime hook registries and metadata from
the first eight lines of scripts recognized by the bundled launcher. Executable
bodies, full commands, environment values and private memory are excluded from
the output. The central
redactor runs before export. Names, models and tools describe declarations,
not which tools are available in the current session.

The panel pages offer menu navigation, inventory cards, filters
and expandable role and capability details. It adapts to mobile, supports keyboard
controls and respects reduced motion. It needs no server or third-party assets (Chart.js is vendored).
If Chart.js or its provenance is missing, pages report it and show tables while JSON remains
available.

Runtime and memory indicators show **source presence in the inspected bundle**.
They do not establish service health, access, consumer configuration or hook
execution. The extension section separately inventories local project/user
declarations; it does not measure health or invoke servers.

Malformed/unreadable inputs produce warnings. Missing bundled redactor or invalid
root produces exit 2 with no metadata export; the user's main task continues.
Reads and inventory are bounded and symlinks rejected. HTML writes are atomic
and replace only output bearing this generator's marker. Rebuild to refresh.

See the [architecture and memory decisions](../roadmap/2026-10-06-capability-foundation/comparison.md)
for the design rationale. The panel is an original stdlib implementation.

“Guides by role” reads the inspected bundle's capability registry. These rows
are separate from catalog cards and do not prove that guides were applied.
An absent/invalid registry leaves the catalog usable with an explicit limitation.
`/work-context` selects from the same registry by role/phase/stack/area using the
task's package manifests.
## Imported diagnostics

The panel can consume an **explicitly selected** report. Request doctor
`--panel-json` for the project root and save its output to a chosen file, then
pass `--diagnostics-report <report.json>` and `--project <same-root>` to build_panel.
The panel never runs doctor, discovers reports or checks services. An explicitly
requested doctor run retains checks of active opt-in capabilities and may contact
their backends. Exit 1 can accompany a valid report containing findings; exit 2
means usage/projection failure. General doctor JSON contains private details and
is rejected by this input.

Doctor applies the shared redactor before exporting this projection. A missing
bundled contract or redactor yields an opaque warning and exit 2.

Version 1 declares doctor as producer and includes UTC time, a SHA-256 key of
the normalized absolute project path and rows by public block. This binds path
spelling according to the operating system; it does not prove physical identity,
anonymity or process provenance. A moved project needs another check. The visible
source hash covers decoded UTF-8 text without BOM, rather than original file bytes;
it identifies content without authenticating its producer.

The contract allows eight public blocks, at most **512 rows** and **64 KiB** of
input. Only severity, exact public labels and up to three priority references are
exported. Private or unknown labels fall back to row ordinals. Details, paths and
free-form remedies remain in doctor. Priority links point to checks and refer to
doctor's block/row for details and remedies; they never execute commands.

Every report is a historical snapshot. Reports older than 24 hours are labelled
old; future timestamps are rejected. Missing input, incompatible format, unbound
or mismatched scope, read failure and truncation are distinct. Partial reports
show partial counts and omit priorities. Missing evidence does not become zero,
readiness, execution rates or health.

Diagnostics provides severity filtering, search, fragments and keyboard focus.
Inventory filters remain independent. A successful check never upgrades hook
`load_status` or `execution_status`. Regenerate the panel to update it; the
exported panel is not a live service.
