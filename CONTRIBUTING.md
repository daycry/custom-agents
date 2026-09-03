# Contributing to custom-agents

**English** · [Español (resumen)](#en-español-resumen)

Thanks for considering a contribution. This plugin is a set of Markdown pieces (agents, commands,
skills) plus deterministic Python scripts, so contributing is mostly writing precise prose and
keeping a few mechanical guards green. Read [`CLAUDE.md`](CLAUDE.md) and
[`docs/CONVENTIONS.md`](docs/en/CONVENTIONS.md) first — they say where every piece lives and how it
is named.

## 1. Proposing a piece (agent, skill, command, kit, hook)

1. **Open an issue first** with the *New piece* form (`.github/ISSUE_TEMPLATE/pieza-nueva.yml`):
   what problem it solves, who invokes it, which existing pieces it touches. Small fixes do not
   need an issue — go straight to a PR.
2. **Use the `plugin-dev` skill** inside Claude Code (`skills/plugin-dev/`): it walks the decision
   tree (agent vs skill vs command vs shared fragment), fills the frontmatter (`name`, `model`,
   `tools`, `dependencies`, trigger phrase in the `description`) from the templates in
   `skills/plugin-dev/templates/`, and lists the validation steps below.
3. **Where things go** (rule of thumb from `CONVENTIONS.md`): used by 2+ agents → `skills/`;
   private to one agent → `agent-kits/<agent>/`; repeated prompt fragment → `agent-kits/shared/`;
   any calculation or verdict → a **script with tests and exit codes**, never agent prose.
4. **Skills stay short**: `SKILL.md` ≤ 200 lines (hard limit 250, `tests/test_skill_size.py`);
   detail goes to `skills/<skill>/references/<topic>.md` with "read X only when you reach step Y".
5. **Optional pieces degrade, never block** (Jira, Confluence, measurement, constitution).

## 2. Checklist before opening the PR

Run everything from the repo root (Python 3.11+, stdlib only):

```bash
python3 scripts/lint_plugin.py                 # 0 errors (warnings are listed; do not add new ones)
python3 -m pytest -q tests agent-kits/shared skills/adversarial-review/scripts skills/code-health/scripts skills/dependency-upgrade/scripts skills/changelog-sync/scripts skills/unit-tests/scripts skills/api-contract/scripts skills/jira-sync/scripts evals
python3 evals/check.py                         # every piece has ≥ 2 positive + 1 negative activation cases
python3 scripts/release.py --check             # versions consistent + CHANGELOG sections present
```

- [ ] **Activation evals**: a new or changed piece has its `evals/cases/<kind>-<name>.json` with at
      least one `literal` positive (a phrase from the REAL `description`), one paraphrase and one
      *neighbouring* negative with `redirect`. `evals/check.py` ties the literal to the description.
- [ ] **Docs, bilingual**: English is primary. `README.md` + `README.es.md`, `docs/<x>.md` +
      `docs/en/<x>.md` for the key docs (README, INSTALL, CONVENTIONS, FLOWS, observability); an
      agent gets `docs/agents/<name>.md` + a row in `docs/README.md` (+ EN). Machine-parsed tokens
      (states, `generacion:`, `- **Tipo**:`) stay in Spanish in both languages.
- [ ] **CHANGELOG**: add your entry under `## [Unreleased]` in `CHANGELOG.md` and under
      `## [Sin publicar]` in `CHANGELOG.es.md`. Do **not** create a version section — `release.py`
      does that at release time.
- [ ] **Manual copies in sync** (see §4): `cmp ci.yml.MANUAL-COPY .github/workflows/ci.yml` and the
      same for `release.yml`, `headless.yml` and `github-templates.MANUAL-COPY/` → `.github/`.
- [ ] **Executable bits**: new `.sh` files are `100755` (`git ls-files -s <file>`); on Windows run
      `git update-index --chmod=+x <file>`.
- [ ] Scripts: relative paths only (`dirname "$BASH_SOURCE"` / `os.path.dirname(__file__)`), tests
      next to them or in `tests/`, exit codes documented in the docstring.

## 3. Commit convention

One logical change per commit, imperative summary, body explains *why* when not obvious.

| Prefix | When |
|---|---|
| `T-XX: …` | a task of an initiative ledger (`docs/roadmap/<date>-<slug>/tasks.md`); the summary echoes the task title and the evidence (tests count, lint) |
| `feat: …` | a new piece or capability outside a ledger |
| `fix: …` | a bug fix |
| `docs: …` | documentation only (both languages in the same commit) |
| `chore: …` | maintenance; `chore: release vX.Y.Z` is created by `scripts/release.py` |

Do not push tags by hand: `python3 scripts/release.py X.Y.Z` moves the CHANGELOG, runs the checks,
bumps the version in the three places, fixes `.sh` modes and creates commit + tag.

## 4. `.MANUAL-COPY` files

`.github/` is a protected path for the remote tooling that develops this repo, so every file that
must live there has a **source of truth outside `.github/`** and is copied by hand:

| Source (edit this) | Copy (never edit directly) |
|---|---|
| `ci.yml.MANUAL-COPY`, `release.yml.MANUAL-COPY`, `headless.yml.MANUAL-COPY` | `.github/workflows/<name>.yml` |
| `github-templates.MANUAL-COPY/ISSUE_TEMPLATE/*.yml`, `github-templates.MANUAL-COPY/PULL_REQUEST_TEMPLATE.md` | `.github/ISSUE_TEMPLATE/*.yml`, `.github/PULL_REQUEST_TEMPLATE.md` |

Edit the source, then copy it (`cp <src> <dst>`). `tests/test_ci_manual_copy.py` fails when a copy
diverges (skips when the copy does not exist yet), `scripts/lint_plugin.py` warns, and
`scripts/release.py` refuses to release with a stale copy.

## 5. Review

Every PR runs the CI (`ci.yml`). Inside Claude Code you can run the same two-lens adversarial
review the plugin uses on itself: `skills/adversarial-review` ("review this diff"). Reviewers will
ask for evidence (test output, lint output) rather than descriptions — include it in the PR body.

---

## En español (resumen)

- **Antes de nada** lee [`CLAUDE.md`](CLAUDE.md) y [`docs/CONVENTIONS.md`](docs/CONVENTIONS.md).
- **Proponer una pieza**: abre un issue con el formulario *Pieza nueva* y usa la skill `plugin-dev`
  dentro de Claude Code para crearla con el frontmatter, el tiering y las dependencias correctas.
  Compartido → `skills/`; privado → `agent-kits/<agente>/`; fragmento repetido → `agent-kits/shared/`;
  cálculos y veredictos → script con tests y exit codes. `SKILL.md` ≤ 200 líneas, detalle en `references/`.
- **Checklist antes del PR**: `python3 scripts/lint_plugin.py` (0 errores) · `python3 -m pytest -q tests agent-kits/shared skills/adversarial-review/scripts skills/code-health/scripts skills/dependency-upgrade/scripts skills/changelog-sync/scripts skills/unit-tests/scripts skills/api-contract/scripts skills/jira-sync/scripts evals` · `python3 evals/check.py` · evals de activación (positivo literal + paráfrasis + negativo vecino) · doc ES+EN en el mismo cambio · entrada en `CHANGELOG.md` `[Unreleased]` y `CHANGELOG.es.md` `[Sin publicar]` (sin crear la sección de versión: la crea `release.py`) · copias `.MANUAL-COPY` sincronizadas · `.sh` en `100755`.
- **Commits**: `T-XX:` (tarea de un ledger), `feat:`, `fix:`, `docs:`, `chore:`; `chore: release vX.Y.Z` lo crea `scripts/release.py`.
- **Copias manuales**: `.github/` está protegida; edita `*.yml.MANUAL-COPY` y `github-templates.MANUAL-COPY/` y copia a mano. `tests/test_ci_manual_copy.py`, el linter y `release.py` vigilan que no diverjan.
