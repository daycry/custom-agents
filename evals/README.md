# `evals/` — evals de comportamiento del plugin (fiabilidad de activación)

**Español** · [English below](#english)

La `description` de una skill, comando o agente es una **promesa de activación**: «Claude me
invocará cuando el usuario diga X». Esta carpeta convierte esa promesa en algo que se **prueba**,
no que se asume (lección [`LES-011`](../docs/knowledge/lessons/LES-011-plugin-dev-activacion-se-prueba-con-evals.md)):
para cada pieza del plugin hay prompts reales de usuario que **deben** dispararla (positivos) y
prompts vecinos que **no** deben (negativos, los valiosos: comparten vocabulario pero piden otra
cosa — p. ej. una petición con incógnitas no debe ir a `quick-implement` sino a `/pm-cycle`).

## Qué hay

| Fichero | Qué es | Dónde corre |
|---|---|---|
| `cases/<kind>-<nombre>.json` | Un fichero por pieza evaluable (`skill-*`, `command-*`, `agent-*`; 12 + 11 + 8 = 31). Formato abajo. | — (datos) |
| `check.py` | Validación **estática**: esquema, cobertura (toda pieza tiene fichero con ≥ 2 positivos + 1 negativo), ids únicos, sin datos corporativos y, la clave, que el positivo `trigger: literal` **contenga una frase de la `description` real** → si cambias la description, el caso rompe y hay que actualizar ambas. Exit 0/1. | **CI** (`ci.yml`) |
| `run.py` | Runner **local**: lanza cada caso en una sesión headless (`claude -p … --plugin-dir`) sobre una copia de `fixtures/project/`, detecta en la transcripción si la pieza se activó y evalúa `expect`. Cuesta tokens reales. Exit 0/1, **2 si `claude` no está en PATH**. | tu máquina |
| `fixtures/project/` | Proyecto inventado con una iniciativa `demo` (spec aprobada, evaluación go, plan en borrador) para que los prompts tengan contexto realista. | copia por caso |
| `test_evals.py` | Tests de `check.py` y de `run.py` con el subprocess **mockeado** (aquí nunca se lanza `claude`). | CI (`pytest evals`) |
| `reports/` | Informes `AAAA-MM-DD.json` de `run.py` (ignorados por git). | local |
| `../headless.yml.MANUAL-COPY` → `.github/workflows/headless.yml` | Job **opcional** de CI (`workflow_dispatch` + lunes 06:00 UTC) que sí lanza `claude`: subconjunto barato de `run.py` (`--bare --max-turns 4 --target skill:quick-implement --target command:setup`) + comprobación de **hooks en sesión real** (abajo). Solo con el secret `ANTHROPIC_API_KEY`; sin él, verde con aviso. | GitHub Actions |

## Formato de un caso (propio — no hay formato oficial, ver abajo)

```json
{
  "target": "skill:quick-implement",
  "cases": [
    {
      "id": "quick-implement-literal",
      "prompt": "Hazme este cambio pequeño sin papeleo: …",
      "trigger": "literal",
      "expect": { "activates": true, "artifacts": ["docs/roadmap/*/tasks.md"], "mentions": ["ledger"], "must_not": [] },
      "notes": "Disparador literal de la description."
    },
    {
      "id": "quick-implement-neg-incognitas",
      "prompt": "Necesito un módulo de facturación multi-moneda; no sé qué normativa aplica y quiero presupuesto antes.",
      "expect": { "activates": false, "redirect": "command:pm-cycle" },
      "notes": "Vecino: incógnitas + presupuesto → /pm-cycle."
    }
  ]
}
```

- `target`: `skill:<n>` · `command:<n>` · `agent:<n>`; el fichero se llama igual con `:` → `-`.
- `trigger` (solo positivos): `literal` = el prompt contiene una frase de la description (entrecomillada o 4 palabras seguidas; comparación sin acentos ni mayúsculas) · `parafrasis` = misma intención con otras palabras. Cada pieza necesita ≥ 1 de cada.
- `expect.activates` (obligatorio) · `artifacts` (globs relativos al cwd temporal) · `mentions` / `must_not` (subcadenas en el texto del asistente) · `redirect` (pieza que debería activarse en su lugar; **informativo**, no decide).
- Prompts en español, naturales, con contexto (ficheros, rutas del fixture); **sin datos corporativos** (correos, hosts `atlassian.net`, URLs externas, claves Jira reales — `check.py` lo vigila; `PROJ-`, `localhost` y `example.com` están permitidos).

## Cómo se ejecuta

```bash
python3 evals/check.py                       # estático, CI (exit 0 = suite coherente)
python3 evals/run.py --dry-run               # imprime los comandos `claude -p …` sin ejecutar nada
python3 evals/run.py --target skill:quick-implement     # un target (repetible: --target A --target B)
python3 evals/run.py --only quick-implement-literal     # un caso
python3 evals/run.py --max-turns 6 --timeout 900 --bare # --bare: sin hooks/skills del host (exige ANTHROPIC_API_KEY)
python3 -m pytest -q evals                   # tests (subprocess mockeado)
```

Comando que lanza `run.py` por caso (contrato de la CLI verificado el 2026-09-03 en
`code.claude.com/docs/en/headless` y `cli-reference`):

```
claude -p "<prompt>" --output-format stream-json --verbose --plugin-dir <raíz del plugin> --max-turns 8 --permission-mode acceptEdits --allowedTools "Bash(python3:*),Bash(git:*),Bash(find:*)"
```

**Permisos en `-p`.** Nadie aprueba herramientas en una sesión headless y `acceptEdits` solo cubre
Write/Edit: una tool use de Bash (los scripts del plugin: `ledger-lint.py`, `usage-meter.py`, `git`,
`find`) quedaría **denegada** y el caso fallaría por permisos, no por activación. Por eso `run.py`
pasa `--allowed-tools` (default `Bash(python3:*),Bash(git:*),Bash(find:*)`; se entrega tal cual a
`--allowedTools`; cadena vacía → no se pasa) y, en el informe, cada caso fallido lleva una `causa`:
`no activó` / `activó sin deber` (lo que mide la suite), `permiso denegado` (la pieza se activó pero
un `tool_result` con `is_error` habla de permisos — amplía `--allowed-tools`), `expectativa`
(`mentions`/`must_not`/`artifacts`) o `timeout`.

**Cómo detecta la activación.** `--output-format json` solo devuelve el resultado final (sin tool
uses), así que se usa `stream-json` y se leen las tool uses de los mensajes `assistant`:
`Skill` (o `SlashCommand`) con `input.skill == <nombre>` para skills **y comandos** (los commands
se fusionaron con las skills: Claude los invoca por la herramienta Skill; se recorta el namespace
`custom-agents:` y los argumentos), y `Agent` (o `Task`) con `input.subagent_type == <nombre>`
para agentes. `--loose` añade como señal débil un `Read` del fichero de la pieza (depuración).
Un `claude` que acaba con error, `is_error` o timeout falla el caso.

**Coste.** 96 casos × una sesión corta ≈ decenas de dólares según el modelo; por eso `run.py` no
está en la CI y admite `--target`/`--only`. Ejecútalo antes de un release o tras tocar una
`description`; guarda el informe (o cita sus cifras en el ledger).

## Job headless opcional (`headless.yml`) — evals reales + hooks en sesión real

`ci.yml` nunca ejecuta `claude` (cuesta tokens). El workflow `headless.yml` sí, pero es **opt-in por
secret**: expone `secrets.ANTHROPIC_API_KEY` como `env` del job y cada paso lleva
`if: env.ANTHROPIC_API_KEY != ''` (los secrets no pueden usarse directamente en un `if:` —
docs.github.com «Using secrets in conditional statements», verificado 2026-09-03); sin secret el job
termina en verde con un `::warning::`. Con secret: instala Claude Code (`npm install -g
@anthropic-ai/claude-code`), repite la validación estática y ejecuta:

1. **Evals reales, subconjunto barato:** `python3 evals/run.py --bare --max-turns 4 --target
   skill:quick-implement --target command:setup` (`--target` es repetible; 7 casos). `--bare` salta
   hooks/skills/CLAUDE.md del runner y **exige `ANTHROPIC_API_KEY`** (no usa login OAuth) —
   `code.claude.com/docs/en/headless`, verificado 2026-09-03; `--plugin-dir` sí carga el plugin en bare mode.
2. **Hooks en sesión real** (cierra el paso 1 de la lista manual de `docs/observability.md`): sobre una
   copia de `fixtures/project/`, `claude -p --bare --plugin-dir . --output-format stream-json --verbose
   --permission-mode acceptEdits --max-turns 6 "Edita docs/roadmap/2026-01-01-demo/tasks.md marcando T-01
   completado…"`. Evidencia exigida: (a) el evento `system/init` del stream lista el plugin en `plugins`
   (campo documentado en «Fail CI when a plugin or MCP server doesn't load»); (b) el **fichero-testigo**
   `.claude/.progress-last` que escribe `hooks/progress-line.sh` al editar un `tasks.md`. **Por qué el
   fichero y no la salida:** la doc de stream-json solo documenta eventos `hook_started` /
   `hook_progress` / `hook_response` para hooks `SessionStart`/`Setup` (antes de `system/init`); no
   garantiza que el `systemMessage` de un `PostToolUse` aparezca en el stream, así que buscarlo sería
   frágil. **Duda documentada:** la doc dice que `--bare` «salta la auto-detección de hooks» y no aclara
   si los hooks de un plugin pasado con `--plugin-dir` corren; por eso, si con `--bare` el plugin cargó
   pero no hay testigo, el paso repite **sin** `--bare` y avisa (`::warning::`) de en qué modo hubo
   evidencia — si se repite, es dato para la doc.
3. Sube `evals/reports/*.json|*.jsonl|*.stderr` como artifact `headless-reports` (30 días).

La lista manual de `docs/observability.md` sigue valiendo para instalaciones locales (pasos 2 y 3:
contexto de sesión y hook de guardia son interactivos).

## Cómo añadir un caso (o una pieza nueva)

1. Pieza nueva → crea `cases/<kind>-<nombre>.json` con ≥ 2 positivos (uno `literal`, otro
   `parafrasis`, prompts distintos) + ≥ 1 negativo vecino (`redirect` a la pieza que sí toca).
   El linter (`scripts/lint_plugin.py`) avisa si una pieza no tiene fichero.
2. Caso nuevo en una pieza existente → añádelo al array `cases` con `id` único (`<nombre>-<qué>`).
3. `python3 evals/check.py` → 0 errores. Si cambias una `description`, revisa que el `literal`
   siga casando (el check te lo dirá).
4. Opcional: `python3 evals/run.py --only <id>` para verlo activarse de verdad.

## Relación con el formato oficial (verificado 2026-09-03)

- **No existe `claude plugin eval`** (`code.claude.com/docs/en/plugins-reference`: `init` ·
  `install` · `uninstall` · `prune` · `enable` · `disable` · `update` · `list` · `details` ·
  `validate`). El formato de esta carpeta es **propio**.
- La doc oficial de skills (`code.claude.com/docs/en/skills` § «Evaluate and iterate on a skill»)
  remite al plugin `skill-creator`, cuyo `evals/evals.json` por skill mide **calidad de la
  salida** (`{skill_name, evals:[{id, prompt, expected_output, files, assertions}]}`, formato de
  agentskills.io) y cuyo afinado de description usa una lista `[{query, should_trigger}]` **no
  documentada oficialmente**. Nuestro formato cubre la activación (lo que aquí falla) para skills,
  comandos **y agentes** a la vez, y es trivialmente convertible: `prompt`→`query`,
  `expect.activates`→`should_trigger`. Si Claude Code publica un formato oficial de evals de
  activación, migraremos `cases/` y este README.

---

## English

`evals/` turns each piece's `description` — a *promise* that Claude will invoke it when the user
says X — into something **tested**, not assumed. One JSON file per skill/command/agent
(`cases/<kind>-<name>.json`) holds ≥ 2 positive prompts (one containing a literal phrase of the
real description, one paraphrased) and ≥ 1 *neighbouring* negative (shares vocabulary, should route
elsewhere — `expect.redirect`). `check.py` is the **static, CI** half: schema, coverage of every
piece, unique ids, no corporate data, and the literal prompt must still match the current
description (so changing a description breaks the case until both are updated). `run.py` is the
**local** runner: it launches `claude -p "<prompt>" --output-format stream-json --verbose
--plugin-dir <plugin> --max-turns 8 --permission-mode acceptEdits --allowedTools "<--allowed-tools>"` (default
`Bash(python3:*),Bash(git:*),Bash(find:*)`: in `-p` nobody approves tools and `acceptEdits` does not cover Bash) per case on a copy of
`fixtures/project/`, detects activation from the `Skill`/`Agent` tool uses in the transcript
(`json` output has no tool uses; commands are invoked through the Skill tool), checks
`mentions`/`must_not`/`artifacts`, tags each failure with a `causa` (`no activó` · `activó sin deber` · `permiso denegado` — the
piece fired but a tool_result was denied for permissions — · `expectativa` · `timeout`), writes `reports/<date>.json`, and exits 0/1 (2 when `claude` is
not on PATH; `--dry-run` only prints the commands). There is no official `claude plugin eval`
(plugins-reference, 2026-09-03); the official `skill-creator` `evals/evals.json` measures output
quality, so this format is our own and maps 1:1 onto its trigger list (`prompt`→`query`,
`activates`→`should_trigger`).

**Optional headless CI job (`headless.yml.MANUAL-COPY` → `.github/workflows/headless.yml`,
`workflow_dispatch` + Mondays 06:00 UTC).** `ci.yml` never runs `claude`; this job does, gated by the
`ANTHROPIC_API_KEY` secret exposed as job `env` and checked per step with `if: env.ANTHROPIC_API_KEY !=
''` (secrets cannot be used directly in `if:` — docs.github.com, verified 2026-09-03); without it the
job ends green with a warning. With it: `npm install -g @anthropic-ai/claude-code`, then (1) a cheap
real-eval subset `python3 evals/run.py --bare --max-turns 4 --target skill:quick-implement --target
command:setup` (`--target` is repeatable; `--bare` requires `ANTHROPIC_API_KEY` and still loads
`--plugin-dir`), and (2) a **real-session hook check** that closes step 1 of the manual list in
`docs/observability.md`: `claude -p --bare --plugin-dir . --output-format stream-json …` edits the
`demo` ledger in a copy of `fixtures/project/`, and the evidence is (a) the plugin listed under
`plugins` in the `system/init` event and (b) the **witness file** `.claude/.progress-last` written by
`hooks/progress-line.sh` — not a `systemMessage` in the stream, which the docs only guarantee as
`hook_*` events for `SessionStart`/`Setup` hooks. Because the docs do not say whether `--bare` runs a
`--plugin-dir` plugin's hooks, a loaded plugin with no witness triggers a retry without `--bare` and a
`::warning::` naming the mode that produced evidence. Reports are uploaded as the `headless-reports`
artifact.
