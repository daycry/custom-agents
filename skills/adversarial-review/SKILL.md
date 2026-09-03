---
name: adversarial-review
description: >
  Revisión ADVERSARIAL de un diff con lentes de contexto fresco en paralelo — A (conformidad con
  spec/plan/constitución, ✓/✗ por criterio), B (defectos de corrección), C (seguridad, CONDICIONAL)
  y D (rendimiento, CONDICIONAL — ambas por `review-lens-select.py` sobre ficheros/líneas sensibles
  o costosas) — con fusión, graduación Critical/Important/Minor, bucle acotado a 3 intentos, rebate
  con evidencia y traza en el ledger («Revisión de dos lentes — intento N»). Fuente única del
  método que usan /dev-cycle (Fase 3) y quick-implement; también a demanda sobre una rama o rango
  sin ledger. NO sustituye a `qa` (E2E + qa-gate) ni a `nemesis` (auditoría de seguridad completa),
  y NO revisa estilo ni propone refactors. Úsala cuando el usuario diga "revisa este diff",
  "revisión adversarial", "pasa las dos lentes", "revisión de dos lentes", "busca gaps en la rama",
  o cuando /dev-cycle o quick-implement lleguen a la puerta de revisión.
---

# adversarial-review — dos lentes (+ dos condicionales) contra el diff, con bucle acotado

Patrón que más críticos reales ha cazado en este repo (`docs/knowledge/lessons/LES-010-*`): revisores
de **contexto fresco** que NO han visto implementar, cada uno con una lente, sobre el **diff**. Fuente
única del método: `/dev-cycle` y `quick-implement` la invocan y conservan solo lo suyo (intentos, horas).

> **Regla dura.** Un revisor siempre encuentra algo: aquí solo cuentan gaps de **requisitos**,
> **corrección** o **seguridad introducida**, con `fichero:línea` y escenario. Estilo,
> preferencias y sobre-ingeniería se descartan sin discusión.

Resolución de rutas (regla 5 de CONVENTIONS — nunca rutas fijas):
```bash
SHAREDKIT="$(find "$PWD/.claude" "$HOME/.claude" -type d -path '*agent-kits/shared' 2>/dev/null | head -1)"
REVSKILL="$(find "$PWD/.claude" "$PWD/skills" "$HOME/.claude" -type d -path '*skills/adversarial-review' 2>/dev/null | head -1)"
```

## Cuándo NO usarla

- Para dar el verde de pruebas: eso es `qa` con `qa-gate.py` (la revisión va ANTES de qa).
- Para auditar la seguridad del proyecto (OWASP completo, deps, IaC, DAST): eso es `nemesis` con
  la skill `cybersecurity`. La Lente C mira SOLO lo que el diff introduce o reabre.
- Para comentar estilo, nombres o refactors: no es una code review de gustos.
- Sobre un cambio trivial de una línea si el usuario pidió explícitamente saltarse la revisión.

## Entradas — dos modos

| Modo | Qué recibes | Contra qué revisa la Lente A |
|---|---|---|
| **Con ledger** (desde `/dev-cycle`, `quick-implement`) | `docs/roadmap/<fecha>-<slug>/` (con `tasks.md`; `improvement-plan.md` si existe), nº de intento N, y si N > 1 la tabla de veredictos del intento anterior | `improvement-plan.md` + `tasks.md` (+ `docs/CONSTITUTION.md` si existe) |
| **Sin plan** (a demanda: «revísame este diff», «revisión de la rama») | rama o rango `<base>..HEAD` (si no lo dan, pregunta la base o usa merge-base con `main`/`master`), más el **objetivo declarado por el usuario** | el objetivo declarado + los mensajes de commit del rango; sin criterios formales, la Lente A emite ✓/✗ por **objetivo** (uno por commit o por el objetivo único) |

En ambos modos el diff es `git diff <base>...HEAD` ∪ cambios sin comitear. Sin git → revisa los
ficheros que el usuario indique y dilo (la puerta de alcance no aplica).

## Proceso

### 0. Puerta previa — alcance del diff (solo con ledger; determinista, sin gastar revisores)

`python3 "$SHAREDKIT/scope-check.py" "docs/roadmap/<fecha>-<slug>"` — **exit 0 obligatorio** para
lanzar las lentes. Compara los ficheros cambiados (comiteados + sin comitear) con los campos `Archivos` de TODAS las
tareas del ledger (`tasks.md` propio y `docs/knowledge/**` siempre en alcance). **Exit 1** → los
ficheros fuera de alcance vuelven al `implementer` como **gap Important** ANTES de lanzar las
lentes: o revierte el cambio, o justifica que es necesario — entonces se añade al campo `Archivos`
de su tarea con una nota y se relanza el check. **Exit 2** (sin base clara: ni `main` ni `master`)
→ pásale `--base <ref>`. Sin git → salta la puerta con aviso (la Lente A conserva su comprobación
(2) como red).

### 1. ¿Aplican las Lentes C (seguridad) y D (rendimiento)? (determinista, un solo script)

```bash
python3 "$REVSKILL/scripts/review-lens-select.py" [--base <ref>] [--json]   # exit 0 siempre
```

Devuelve `lente_c`/`lente_d: true|false` + motivos (fichero + patrón), dos heurísticas
INDEPENDIENTES sobre el mismo diff. RUTA: C = stems auth/sesión/secretos/pagos/IaC · D =
repository/dao/query/cache/worker/batch/scheduler…; prosa y `docs/**` excluidas de ambas. CONTENIDO
de líneas añadidas: C = `eval(`, `shell=True`, `innerHTML`, SQL concatenado, claves… · D = `sleep`
bloqueante, `readFileSync`, N+1/`await`/regex-compile/concat **dentro de un bucle** (proximidad, no
parser). Config por separado en `.claude/dev.json`: `revision.lenteSeguridad`/`lenteRendimiento`
(`auto`|`siempre`|`nunca`) y `revision.excluir` (compartido, solo RUTA). Nunca bloquea (error →
aviso + ambas `false`). Contrato = constantes del script (`RUTA_RE`/`CONTENIDO`/`RUTA_RE_D`/
`CONTENIDO_D_INDEPENDIENTE`/`PATRONES_TRAS_BUCLE_D`), con tests; detalle en
`references/lens-c-heuristics.md`/`lens-d-heuristics.md` si un motivo sorprende.

### 2. Lanzar las lentes en PARALELO → agente `reviewer` (solo lectura, contexto fresco)

Cada lente recibe SOLO: el diff (o cómo obtenerlo), las rutas de los artefactos contra los que
revisa, y si N > 1 la tabla del intento anterior (ver §5). Despacho:

1. **Tier del revisor:** `python3 "$SHAREDKIT/model-tier.py" reviewer --json` → pasa `model` al Agent
   tool si `fuente.model` es `dev.json` (el `effort` de dev.json es informativo; sin script → frontmatter).
2. **Agente por nombre:** una llamada al Agent tool por lente con `subagent_type: reviewer`
   (`agents/reviewer.md`: `tools: Read, Grep, Glob, Bash` — NO puede escribir; Bash solo para ejecutar
   tests/scripts como evidencia) y el prompt literal de la lente. Las 2-4 llamadas van en paralelo.
3. **Fallback (degradación, no bloqueo):** si el agente `reviewer` no está disponible (instalación
   parcial, `Agent(reviewer)` rechazado), lanza un subagente genérico con el MISMO prompt y anótalo en la
   salida («lentes por subagente genérico: reviewer no disponible»).

**Prompts literales de A, B, C y D** (+ criterio docs-style en prosa): lee
`"$REVSKILL/references/lens-prompts.md"` **al llegar aquí**. C solo si `lente_c: true`; D solo si
`lente_d: true` (pueden ambas a la vez: hasta 4 lentes en paralelo).

### 3. Fusionar y graduar

**Fusiona** las 2-4 salidas: deduplica gaps que señalen lo mismo (mismo `fichero:línea` o mismo
escenario); A da el **veredicto por criterio** (✓/✗); B, C y D aportan defectos (los de C con su
CWE; los de D, el escenario de carga que lo justifica). Gradúa cada gap **`Critical / Important /
Minor`**: Critical (pérdida de datos, seguridad explotable, criterio incumplido que rompe el
objetivo) e Important (defecto reproducible, fuera de alcance, constitución violada) **obligan
corrección**; Minor se anota sin bloquear el cierre.

### 4. Disciplina al RECIBIR (nada de obediencia ciega)

Antes de corregir, el implementador **verifica cada gap** contra el código y la spec: los revisores
también se equivocan, y "corregir" un señalamiento erróneo introduce bugs donde no los había. Si un
gap es incorrecto, se **rebate con evidencia concreta** (`fichero:línea` + por qué el comportamiento
actual es el correcto) — nunca con "yo creo que está bien". Arbitra el orquestador (o el usuario a
demanda): rebatido CON evidencia → `descartado (rebatido)` en la traza y no cuenta como gap
pendiente (rebatir **no consume intento**); rebatido sin evidencia → se corrige. La graduación se
aplica sobre los gaps que sobreviven al rebate.

### 5. Bucle ACOTADO y traspaso de estado entre intentos

Si quedan gaps Critical/Important: las tareas afectadas vuelven a `en-progreso`, el implementador
corrige (ese tiempo es **implementación**, medido con clave `"<slug>/T-XX-fix<N>"`) y se
**relanza la revisión sobre el nuevo diff** con contador explícito ("revisión, intento 2 de 3").
**Máximo 3 intentos**; al 3.º con gaps, PARA y devuelve la decisión al orquestador/usuario (seguir /
re-planificar / aceptar como deuda). Los subagentes son de un solo uso, así que la memoria del
revisor se consigue **por traspaso**: al lanzar las lentes del intento N+1, pásales la **tabla
completa de veredictos y gaps del intento N — incluidos los `descartado (rebatido)` con su
evidencia** — con la instrucción "esto ya lo juzgaste así; re-evalúa SOLO lo corregido; no reabras
ni lo aprobado ni lo rebatido salvo evidencia nueva".

### Racionalizaciones del REVISOR que NO valen

Formato y reglas: `"$SHAREDKIT/rationalization-table.md"`. Aplican a cada lente y a la fusión.

| Excusa que el modelo se da | Por qué no vale | Qué hacer en su lugar |
|---|---|---|
| «Parece correcto; el implementador sabe lo que hace» | Confianza no es evidencia; la revisión existe para lo que él no puede ver desde dentro. | Lee el diff completo y verifica cada criterio con `fichero:línea`. |
| «La suite está en verde, así que apruebo» | Los críticos de `LES-010` pasaban suites: el verde no cubre requisitos ni huecos de diseño. | Reproduce el escenario de cada criterio; ✓ solo con evidencia. |
| «Este nombre/estructura no me gusta; lo reporto como gap» | Estilo, preferencias y refactors están excluidos por la regla dura. | Descártalo sin discusión; solo requisitos, corrección o seguridad introducida. |
| «El diff es largo; reviso los ficheros importantes y extrapolo» | Los gaps aparecen donde nadie mira (BOM, rutas Windows, fixtures, evasiones). | Recorre TODO el diff; si no cabe, divídelo por ficheros y dilo en la salida. |
| «Aquel gap rebatido en el intento anterior sigue pareciéndome gap» | Reabrir sin evidencia nueva rompe el traspaso y el bucle acotado a 3. | Re-evalúa SOLO lo corregido; reabre únicamente con evidencia nueva citada. |
| «Es Critical, pero lo bajo a Minor para no bloquear el cierre» | La graduación sigue la definición, no el calendario; suavizarlo es deuda oculta. | Gradúa por definición; que el usuario decida si lo acepta como deuda. |
| «Lo señalo sin línea ni escenario; ya lo encontrará el implementador» | Sin `fichero:línea` + escenario no es verificable ni rebatible. | Cada gap con `fichero:línea` y escenario concreto de fallo. |
| «Encontré algo, con eso ya justifico la revisión» | Un revisor «siempre encuentra algo»; el objetivo es cobertura por criterio, no volumen. | Entrega la tabla ✓/✗ completa; «sin defectos» es una salida válida. |

### 6. Salida y traza

- **Siempre:** tabla por criterio (u objetivo) ✓/✗ + lista de gaps graduados con `fichero:línea`,
  escenario y veredicto (`corregido` · `descartado (rebatido)` · `deuda aceptada` · `pendiente`),
  y qué lentes corrieron (A+B, o A+B+C/D con sus motivos).
- **Con ledger, además:** sección **`## Revisión de dos lentes — intento N: …`** al final de
  `tasks.md` (tabla `# · Grado · Gap · Tarea · Corrección · Evidencia`; ver
  `docs/roadmap/2026-09-02-deterministic-guardrails/tasks.md` como referencia de formato) y, al
  cerrar el bucle **sin gaps de corrección pendientes** (0 gaps, todos rebatidos con evidencia, o
  aceptados como deuda por el usuario), **promoción** de las entradas `docs/knowledge/` que la
  iniciativa escribió con `estado: propuesta` → `estado: aceptada (validada: revisión de dos
  lentes, AAAA-MM-DD, intento N)` (formato único de `"$SHAREDKIT/knowledge-write.md"` §Autoría).
  Si el 3.º intento sigue con gaps sin resolver, quedan en `propuesta`. `ledger-lint.py` exit 0
  tras escribir.
- **Jira (solo si `.claude/jira.json` `enabled` Y el plan se volcó):** el orquestador dispara, POR
  CADA intento (no solo al cerrar), el evento `revision` (sin gaps) o `gaps` (con la tabla) de
  `jira-flow.py` — Paso 7 de `jira-sync`, `--intento N` obligatorio —, que comenta YA FIRMADO por el
  `reviewer` (`ca-reviewer`) leyendo la sección `## Revisión de dos lentes` recién escrita; con gaps
  el issue **se reabre** a *En curso* y el aviso al `implementer` va por el ledger (`task-brief.py`),
  no por Jira. El **worklog** `[revisión]` por intento lo imputa el orquestador (contabilidad del
  ciclo, no del método) con las horas medidas. Done es el evento `aprobado` aparte, del
  **orquestador** (`--actor orquestador` + evidencia en el ledger + `--qa-verde`): nunca aquí, nunca `qa`.
- **Mensaje final al orquestador:** disciplina de `"$SHAREDKIT/output-discipline.md"` (≤ ~12
  líneas: veredicto, nº de gaps por grado, lentes que corrieron, ruta del ledger actualizado,
  siguiente paso). El detalle vive en el ledger.

> **Compatibilidad de la etiqueta.** La sección en los ledgers y el promotor de `docs/knowledge/`
> siguen llamándose **«Revisión de dos lentes»** aunque hayan corrido C y/o D (`/retro` y
> `knowledge-write.md` lo buscan literal); anota en el texto qué corrió de verdad (p. ej. "lentes:
> A+B+C", "A+B+D" o "A+B+C+D").

## Scripts propios

- `scripts/review-lens-select.py` — decide si aplican las Lentes C y D (ruta+contenido de las líneas
  añadidas; `dev.json` `revision.lenteSeguridad`/`lenteRendimiento`); determinista, con tests junto
  al script, **exit 0 siempre** (error → ambas `false`).
- Reutiliza sin duplicar, de `agent-kits/shared/`: `scope-check.py` (puerta), `ledger-lint.py`,
  `personas/`, `knowledge-write.md`, `review-report.template.md`, `output-discipline.md`,
  `model-tier.py` (tier del `reviewer`) y `docs-style.md` (Lente A en prosa).
- Referencias propias (bajo demanda): `references/lens-prompts.md` (prompts literales + criterio
  docs-style) · `references/lens-c-heuristics.md` · `references/lens-d-heuristics.md`.

## Qué NO hace

- No implementa ni corrige: devuelve gaps; corrige el `implementer` (o quien pidió la revisión).
- No da el verde de pruebas (`qa`/`qa-gate.py`) ni audita seguridad completa (`nemesis`).
- No toca `docs/roadmap/` salvo la sección de revisión del `tasks.md`, ni `docs/knowledge/` salvo el `estado` de lo que promueve.
- No imputa horas: el worklog `[revisión]` por intento es del orquestador (`/dev-cycle`).
- No decide qué hacer al 3.º intento con gaps: lo devuelve al orquestador/usuario.

## Degradación

Sin `scope-check.py` o sin git → puerta saltada con aviso. Sin `review-lens-select.py` → solo A+B
(dilo). Sin `skills/cybersecurity/references/` → la Lente C corre con criterio propio y lo anota.
Sin `personas/` → Lente B genérica. Sin agente `reviewer` → subagente genérico con el mismo prompt
(dilo). Sin `model-tier.py` → frontmatter. Sin Jira activo → nada se publica. Nada de esto bloquea
la revisión; lo obligatorio es el bucle acotado y la traza en el ledger cuando hay ledger.
